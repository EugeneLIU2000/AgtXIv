"""Build a new candidate dependency graph from frozen extraction and model data.

This does not import the historical DAG. A bibliographic reference or a missing
occurrence becomes a typed unresolved request, not an invented upstream theorem.
Every judgement remains unreviewed; exact text binding proves only location.
"""
from __future__ import annotations

from collections import defaultdict
import json
import pathlib

from core import VERSION, canonical, digest, reject_model_state
from graph import _tarjan, prune_graph
from model import CLAIM_REFERENCE_FIELDS, CLAIM_RESPONSE_COMPAT_SCHEMA, _candidate_reference_issues, bind_source_locators

CLAIM_REFERENCE_POLICY = "CLAIM_REFERENCE_V1"


def _id(prefix, value):
    return prefix + digest(canonical(value))[7:31]


def assemble_candidates(paper, candidate, full_sources, *, response_reference, claim_reference_policy=None):
    """Return new graph inputs and requests with no acceptance/state promotion.

    CLAIM_REFERENCE_V1 (explicit, or implied by CLAIM_REFERENCE_FIELDS in the
    response) drops bare self-occurrence references, expands an occurrence
    carrying several claims into all of them except any that would close a
    support cycle, and records mere mentions apart.
    """
    from jsonschema import Draft202012Validator
    reject_model_state(candidate)
    Draft202012Validator(CLAIM_RESPONSE_COMPAT_SCHEMA).validate(candidate)
    if any(field in claim for claim in candidate["claims"] for field in CLAIM_REFERENCE_FIELDS):
        claim_reference_policy = claim_reference_policy or CLAIM_REFERENCE_POLICY
    if claim_reference_policy not in (None, CLAIM_REFERENCE_POLICY):
        raise ValueError("Unknown claim reference policy")
    v1 = claim_reference_policy is not None
    problems = _candidate_reference_issues(candidate, paper["claims"], paper["bibliography"], full_sources)
    if problems:
        raise ValueError({"code": "INVALID_EXTRACTION_CANDIDATE", "issues": problems})
    if not isinstance(response_reference, dict) or not isinstance(response_reference.get("path"), str):
        raise ValueError("An immutable response reference is required")
    response_path = pathlib.Path(response_reference["path"])
    if not response_path.is_file() or response_path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Response evidence is missing or exceeds the 10 MiB ceiling")
    raw_response = response_path.read_bytes()
    if response_reference.get("sha256") != digest(raw_response) or response_reference.get("byte_size") != len(raw_response):
        raise ValueError("Response reference does not match the actual response bytes")
    response_data = json.loads(raw_response)
    if response_data.get("candidate", response_data) != candidate:
        raise ValueError("Candidate data differs from the referenced response")
    paper_id = paper["paper"]["id"]
    occurrences = {row["id"]: row for row in paper["claims"]}
    bibliography = defaultdict(list)
    for row in paper["bibliography"]:
        bibliography[row["key"]].append(row)
    locators = defaultdict(list)
    for row in bind_source_locators(candidate, full_sources)["bindings"]:
        locators[row["claim_index"]].append(row)
    nodes, groups, requests, issues, mentions, by_occurrence = {}, [], [], [], [], defaultdict(list)
    claim_ids = []
    for index, claim in enumerate(candidate["claims"]):
        sources = [occurrences[oid]["source"] for oid in claim["source_occurrence_ids"]]
        sources += [row["source"] for row in locators[index]]
        node_id = _id("claim:candidate:", [paper_id, sources, claim["statement"], claim["conditions"]])
        if node_id in nodes:
            raise ValueError("Repeated identical candidate claim; reconcile it before graph assembly")
        claim_ids.append(node_id)
        nodes[node_id] = {"id": node_id, "kind": claim["kind"], "paper_id": paper_id,
                          "text": claim["statement"], "conditions": claim["conditions"],
                          "source_spans": sources, "source_occurrence_ids": claim["source_occurrence_ids"],
                          "disposition": "AGENT_NORMALIZED_UNREVIEWED", "blocked_by": [],
                          "confidence": {"source": "SELF_REPORTED", "value": claim["confidence"], "calibration_ref": None},
                          "candidate_response": response_reference, "response_claim_index": index,
                          "upstream_search": "FRONTIER", "cost_microusd": None}
        for occurrence_id in claim["source_occurrence_ids"]:
            by_occurrence[occurrence_id].append(node_id)

    def split(target, oid):
        rows = by_occurrence.get(oid, [])
        return [node_id for node_id in rows if node_id != target], target in rows

    cyclic = {}
    if v1:
        # All reverts are decided at once from the SCCs of the fully expanded claim graph:
        # an expanded member in its target's support cycle reverts; direct references stay.
        direct, expansions = set(), []
        for index, claim in enumerate(candidate["claims"]):
            target = claim_ids[index]
            direct.update((claim_ids[i], target) for i in claim.get("internal_support_claim_indexes", []))
            for oid in claim["internal_support_occurrence_ids"]:
                matches, own = split(target, oid)
                if len(matches) == 1 and not own:
                    direct.add((matches[0], target))
                elif matches and not own:
                    expansions.append((target, oid, matches))
        downstream = {node_id: set() for node_id in claim_ids}
        for member, target in direct | {(match, target) for target, _, matches in expansions for match in matches}:
            downstream[member].add(target)
        scc = {node_id: members[0] for members in _tarjan(downstream) if len(members) > 1 for node_id in members}
        cyclic = {(target, oid): [match for match in matches if (match, target) not in direct
                                  and target in scc and scc.get(match) == scc[target]]
                  for target, oid, matches in expansions}

    def request(kind, identity, text, source_spans, **details):
        node_id = _id("request:", [paper_id, kind, identity])
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "kind": kind, "paper_id": None, "text": text,
                              "source_spans": source_spans, "disposition": "UNREVIEWED",
                              "blocked_by": [kind.upper() + ":" + node_id],
                              "upstream_search": "FRONTIER", "cost_microusd": None}
            requests.append({"id": node_id, "request_kind": kind, "from_paper_id": paper_id,
                             "candidate_response": response_reference, **details})
        return node_id

    for index, claim in enumerate(candidate["claims"]):
        target, members, expanded = claim_ids[index], set(), False
        members.update(claim_ids[i] for i in claim.get("internal_support_claim_indexes", []))
        for oid in claim["internal_support_occurrence_ids"]:
            matches, own = split(target, oid)
            reason = None
            # A shared occurrence can state several distinct claims. A match is
            # not selected by array order, nor does a self-reference prove itself.
            if len(matches) == 1 and not own:
                members.add(matches[0])
            elif v1 and own and not matches:
                issues.append({"code": "SELF_OCCURRENCE_REFERENCE", "subject": target, "occurrence_id": oid,
                               "detail": "A claim's own occurrence is not a dependency; reference dropped"})
            elif v1 and matches and not own:
                # Conservative over-approximation of "by Theorem X": all its claims jointly, less
                # any that would close a support cycle, which revert to the placeholder below.
                kept = [node_id for node_id in matches if node_id not in cyclic[(target, oid)]]
                if kept:
                    expanded = True
                    members.update(kept)
                    issues.append({"code": "MULTI_CLAIM_OCCURRENCE_EXPANDED", "subject": target, "occurrence_id": oid,
                                   "member_ids": sorted(kept), "mathematical_dependency_asserted": False})
                if cyclic[(target, oid)]:
                    matches, reason = cyclic[(target, oid)], "SHARED_OCCURRENCE_EXPANSION_CYCLIC"
            else:
                reason = "AMBIGUOUS_OR_SELF_CLAIM" if by_occurrence.get(oid) else "NOT_YET_EXTRACTED"
            if reason:
                member = request("unresolved_claim_occurrence", [oid, target],
                                 "Locate the supporting mathematical claim in the cited occurrence.",
                                 [occurrences[oid]["source"]], occurrence_id=oid,
                                 downstream_node_id=target, candidate_claim_ids=matches, reason=reason)
                if reason == "SHARED_OCCURRENCE_EXPANSION_CYCLIC":
                    issues.append({"code": reason, "subject": target, "occurrence_id": oid, "member_ids": sorted(matches),
                                   "placeholder_id": member, "mathematical_dependency_asserted": False})
                members.add(member)
        for key in claim["external_citation_keys"]:
            entries = bibliography[key]
            # Conflicting bibliography units remain distinct pieces of evidence.
            # Neither a base arXiv ID nor a title is silently pinned to a version.
            member = request("external_claim_request", [key, target],
                             "Find the exact external statement used to support this claim.",
                             [row["source"] for row in entries], citation_key=key,
                             downstream_node_id=target,
                             bibliography=[{field: row.get(field) for field in
                                            ("id", "bibliography_unit", "title", "identifiers", "local_match_evidence")}
                                           for row in entries],
                             cited_statement_alignment="NOT_ESTABLISHED")
            members.add(member)
        mentions.extend({"claim_id": target, "citation_key": key, "relation": "MENTION_NOT_SUPPORT",
                         "bibliography_ids": [row.get("id") for row in bibliography[key]]}
                        for key in claim.get("external_mention_citation_keys", []))
        for unresolved in claim["unresolved_dependencies"]:
            # Free prose may describe missing Lean implementation, uncertainty,
            # or a mathematical gap. It cannot become an AND premise without a
            # typed mathematical statement and a support-role judgement.
            issue_id = _id("unresolved:", [target, unresolved])
            nodes[target]["blocked_by"].append(issue_id)
            issues.append({"id": issue_id, "code": "UNTYPED_EXTRACTION_UNCERTAINTY",
                           "subject": target, "detail": unresolved,
                           "mathematical_dependency_asserted": False})
        if members:
            groups.append({"id": _id("support-group:candidate:", [target, sorted(members)]),
                           "target": target, "members": sorted(members),
                           "relation": "PROOF_DEPENDENCY", "disposition": "UNREVIEWED",
                           "grouping_basis": "ONE_JOINT_CANDIDATE_SUPPORT_SET_NOT_CHECKED_SUFFICIENCY" +
                                             ("; MULTI_CLAIM_OCCURRENCES_EXPANDED_JOINTLY" if expanded else ""),
                           "confidence": {"source": "SELF_REPORTED", "value": claim["confidence"], "calibration_ref": None}})
        else:
            issues.append({"code": "NO_EXPLICIT_SUPPORT_IS_NOT_ORIGIN", "subject": target,
                           "detail": "No support was proposed in this scope; root status remains FRONTIER"})
    covered = set(by_occurrence)
    policy = {"claim_reference_policy": claim_reference_policy, "graph_format": "COMPACT_V1",
              "mentions": mentions} if v1 else {}
    return {"kind": "CandidateGraphAssembly", "contract_version": VERSION, **policy,
            "paper_id": paper_id, "nodes": list(nodes.values()), "support_groups": groups,
            "query_ids": claim_ids, "dependency_requests": requests, "issues": issues,
            "coverage": {"scope": "SUPPLIED_HEURISTIC_OCCURRENCE_IDS_NOT_ALL_MATHEMATICS",
                         "supplied_occurrences": len(occurrences), "candidate_covered_occurrences": len(covered),
                         "uncovered_occurrence_ids": sorted(set(occurrences) - covered),
                         "new_exact_locator_count": sum(map(len, locators.values()))},
            "unread_or_uncertain_scope": candidate["unread_or_uncertain_scope"],
            "source_completeness_asserted": False, "all_judgements_unreviewed": True,
            "response_reference": response_reference}


def select_candidate_graph(assembly, query_ids=None):
    queries = assembly["query_ids"] if query_ids is None else query_ids
    if not queries:
        raise ValueError("No extracted mathematical claim is available as a query")
    return prune_graph(assembly["nodes"], assembly["support_groups"], queries,
                       graph_format=assembly.get("graph_format"))


def main():
    import argparse
    import json
    import pathlib
    import uuid
    from core import PlanLedger, utcnow, write_json
    from model import _frozen_source_payload
    parser = argparse.ArgumentParser(description="Assemble an unreviewed graph from a real extraction candidate, without legacy DAG input")
    parser.add_argument("--extraction", type=pathlib.Path, required=True)
    parser.add_argument("--candidate", type=pathlib.Path, required=True)
    parser.add_argument("--source-directory", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("Use a fresh output directory; previous evidence is immutable")
    paper = json.loads(args.extraction.read_bytes())
    raw = args.candidate.read_bytes()
    response = json.loads(raw)
    candidate = response.get("candidate", response)
    if candidate is None:
        parser.error("The supplied model result contains no successful candidate")
    reference = {"path": str(args.candidate.resolve()), "sha256": digest(raw), "byte_size": len(raw)}
    sources = _frozen_source_payload(paper, args.source_directory, source_directory=args.source_directory)
    assembly = assemble_candidates(paper, candidate, sources, response_reference=reference)
    plan = {"contract_version": VERSION, "plan_id": "plan:" + uuid.uuid4().hex,
            "paper_id": paper["paper"]["id"], "query_ids": assembly["query_ids"], "created_at": utcnow(),
            "cost_mode": "ACCOUNT_QUOTA", "decision_policy": "CANDIDATE_EXPLORATION",
            "limits": {"max_model_calls": 0, "max_cost_microusd": 0, "max_papers": 1,
                       "max_call_seconds": 1, "max_node_attempts": 1, "no_progress_limit": 1},
            "environment": {"mode": "CANDIDATE_ASSEMBLY_ONLY", "response_reference": reference,
                            "host_sources": {p.name: digest(p.read_bytes()) for p in pathlib.Path(__file__).parent.glob("*.py")}},
            "source_sha256": paper["paper"]["source_sha256"]}
    ledger = PlanLedger(out, plan)
    write_json(out / "plan.json", plan)
    write_json(out / "candidate-input.json", candidate)
    with ledger.stage("candidate.source_binding_and_graph", {"extraction": digest(args.extraction.read_bytes()),
                                                            "candidate": reference}) as receipt:
        graph = select_candidate_graph(assembly)
        receipt["assembly"] = write_json(out / "assembly.json", assembly)
        receipt["graph"] = write_json(out / "graph.json", graph)
        receipt["source_locator_bindings"] = write_json(out / "source-locator-bindings.json",
                                                       bind_source_locators(candidate, sources))
    write_json(out / "ledger.json", ledger.snapshot())
    summary = {"status": "CANDIDATE_GRAPH_RECORDED", "mathematical_status": "CHAIN_INCOMPLETE",
               "query_candidates": len(assembly["query_ids"]), "nodes": len(graph["nodes"]),
               "support_groups": len(graph["support_groups"]), "dependency_requests": len(assembly["dependency_requests"]),
               "all_judgements_unreviewed": True, "legacy_dag_used": False,
               "coverage": assembly["coverage"]}
    write_json(out / "summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key != "coverage"}))


if __name__ == "__main__":
    main()
