"""Join source-matched candidate papers without erasing unresolved boundaries.

The external-request node remains in the graph. A proposed upstream statement
gets a candidate edge into it; this cannot turn source matching into a theorem
or remove any proof, alignment, identity, or review blocker.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import json
import pathlib
import re

from core import canonical, digest, reject_model_state
from graph import prune_graph
from ingest import normalize_paper_id
from model import bind_source_locators

MAX_GRAPH_BYTES = 64 * 1024 * 1024


def _verified_json(reference):
    if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
        raise ValueError("Missing host evidence reference")
    path = pathlib.Path(reference["path"])
    if not path.is_file():
        raise ValueError("Evidence is absent or exceeds the 10 MiB ceiling")
    with path.open("rb") as stream:
        raw = stream.read(10 * 1024 * 1024 + 1)
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("Evidence is absent or exceeds the 10 MiB ceiling")
    if digest(raw) != reference.get("sha256") or len(raw) != reference.get("byte_size"):
        raise ValueError("Evidence bytes differ from the host reference")
    return json.loads(raw)


def _verified_graph_json(reference):
    """Read a pinned graph/assembly artifact with a bounded allocation."""
    if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
        raise ValueError("Missing graph artifact reference")
    path = pathlib.Path(reference["path"])
    if not path.is_file():
        raise ValueError("Graph artifact is absent")
    with path.open("rb") as stream:
        raw = stream.read(MAX_GRAPH_BYTES + 1)
    if len(raw) > MAX_GRAPH_BYTES:
        raise ValueError("Graph artifact exceeds the 64 MiB ceiling")
    if digest(raw) != reference.get("sha256") or len(raw) != reference.get("byte_size"):
        raise ValueError("Graph artifact bytes differ from the host reference")
    value = json.loads(raw)
    if (not isinstance(value, dict) or not isinstance(value.get("nodes"), list)
            or not isinstance(value.get("support_groups"), list)):
        raise ValueError("Graph artifact must contain nodes and support_groups arrays")
    return value


def join_candidate_paper(base, upstream, matches, full_upstream_sources, *, matches_reference,
                         resolve_explicit_occurrences=False):
    if base.get("all_judgements_unreviewed") is not True or upstream.get("all_judgements_unreviewed") is not True:
        raise ValueError("This join accepts only explicitly unreviewed candidate assemblies")
    if _verified_json(matches_reference) != matches:
        raise ValueError("Matches differ from their actual response file")
    rows = matches.get("matches")
    if not isinstance(rows, list):
        raise ValueError("Source matches require a matches array")
    # Check only model match content; assemblies are host-owned derived data.
    reject_model_state(rows)
    nodes = {node["id"]: copy.deepcopy(node) for node in base["nodes"]}
    groups = {group["id"]: copy.deepcopy(group) for group in base["support_groups"]}
    for node in upstream["nodes"]:
        existing = nodes.get(node["id"])
        if existing is not None:
            # A cached paper can support a new boundary after an earlier join.
            # Host review blockers only accumulate; all other identity-bearing
            # content must still be exactly the same.
            core = lambda value: {key: item for key, item in value.items() if key != "blocked_by"}
            if core(existing) != core(node):
                raise ValueError("Conflicting node identity across papers")
            existing["blocked_by"] = sorted(set(existing.get("blocked_by", [])) | set(node.get("blocked_by", [])))
        else:
            nodes[node["id"]] = copy.deepcopy(node)
    for group in upstream["support_groups"]:
        if group["id"] in groups and groups[group["id"]] != group:
            raise ValueError("Conflicting support-group identity across papers")
        groups[group["id"]] = copy.deepcopy(group)
    requests = {row["id"]: row for row in base["dependency_requests"]}
    occurrence_claims = defaultdict(list)
    occurrence_sources = {}
    for node in upstream["nodes"]:
        for position, oid in enumerate(node.get("source_occurrence_ids", [])):
            occurrence_claims[oid].append(node["id"])
            occurrence_sources[oid] = node["source_spans"][position]
    records, issues = [], []
    upstream_id = upstream.get("paper_id")
    support_counts = Counter(row.get("target_request_id") for row in rows if row.get("relation") == "CANDIDATE_SUPPORT")
    ambiguous_routes = {target for target, count in support_counts.items() if count > 1 and
                        any(row.get("route_semantics") != "EXPLICIT_CANDIDATE_ALTERNATIVE" for row in rows
                            if row.get("target_request_id") == target and row.get("relation") == "CANDIDATE_SUPPORT")}
    for index, row in enumerate(rows):
        target = row.get("target_request_id")
        request = requests.get(target)
        result = {"row": index, "target_request_id": target, "status": "UNRESOLVED",
                  "candidate_group_id": None, "source_alignment_accepted": False,
                  "matches_reference": matches_reference}
        records.append(result)
        if not request or request["request_kind"] != "external_claim_request":
            issues.append({"row": index, "code": "MATCH_TARGET_IS_NOT_EXTERNAL_REQUEST"})
            continue
        if row.get("relation") != "CANDIDATE_SUPPORT":
            result["status"] = "UNREVIEWED_" + str(row.get("relation", "UNKNOWN"))
            continue
        if target in ambiguous_routes:
            issues.append({"row": index, "code": "CROSS_ROW_AND_OR_SEMANTICS_UNSPECIFIED"})
            continue
        ids = row.get("upstream_occurrence_ids")
        explicit_claims = row.get("upstream_claim_ids", [])
        if (not isinstance(ids, list) or not isinstance(explicit_claims, list) or not (ids or explicit_claims) or
                any(not isinstance(oid, str) for oid in ids + explicit_claims)):
            issues.append({"row": index, "code": "MATCH_HAS_NO_UPSTREAM_OCCURRENCE"})
            continue
        upstream_nodes = {node["id"]: node for node in upstream["nodes"]}
        if any(cid not in upstream_nodes or upstream_nodes[cid].get("paper_id") != upstream_id or
               upstream_nodes[cid].get("kind") not in {"definition", "theorem", "lemma", "proposition", "equation", "claim"}
               for cid in explicit_claims):
            issues.append({"row": index, "code": "UPSTREAM_CLAIM_ID_UNKNOWN"})
            continue
        occurrence_members = set()
        resolution = {}
        for oid in ids:
            owners = set(occurrence_claims.get(oid, []))
            selected = owners
            if len(owners) > 1 and resolve_explicit_occurrences:
                selected = owners & set(explicit_claims)
            if (not selected or (len(selected) > 1 and
                    (not resolve_explicit_occurrences or row.get("combination") != "JOINT_SUPPORT"))):
                break
            occurrence_members.update(selected)
            resolution[oid] = sorted(selected)
        if len(resolution) != len(set(ids)):
            issues.append({"row": index, "code": "UPSTREAM_CLAIM_IDENTITY_AMBIGUOUS_OR_MISSING"})
            continue
        quotes = row.get("source_quotes")
        if not isinstance(quotes, list) or not quotes:
            issues.append({"row": index, "code": "MATCH_HAS_NO_EXACT_SOURCE_EVIDENCE"})
            continue
        located = bind_source_locators({"claims": [{"source_locators": quotes}]}, full_upstream_sources)
        if located["issues"]:
            issues.append({"row": index, "code": "MATCH_SOURCE_QUOTATION_UNBOUND", "detail": located["issues"]})
            continue
        source_sets = [[occurrence_sources[oid]] for oid in ids] + [upstream_nodes[cid]["source_spans"] for cid in explicit_claims]
        if any(not any(bound["source"]["path"] == source["path"] and
                           bound["source"]["sha256"] == source["sha256"] and
                           bound["source"]["byte_start"] < source["byte_end"] and
                           source["byte_start"] < bound["source"]["byte_end"]
                           for bound in located["bindings"] for source in sources)
                   for sources in source_sets):
            issues.append({"row": index, "code": "MATCH_QUOTATION_DOES_NOT_LOCATE_CLAIM"})
            continue
        # Identity remains a candidate even for an exact base identifier; a
        # pinned source snapshot is recorded separately by upstream extraction.
        proposed = []
        for entry in request.get("bibliography", []):
            proposed += (entry.get("identifiers") or {}).get("arxiv", [])
        identity = "UNREVIEWED_NON_ARXIV_IDENTITY"
        if proposed:
            pinned = normalize_paper_id(upstream_id)
            proposed_ids = {normalize_paper_id(value) for value in proposed}
            proposed_bases = {re.sub(r"v[1-9]\d*$", "", value) for value in proposed_ids}
            base_id = re.sub(r"v[1-9]\d*$", "", pinned)
            if len(proposed_bases) != 1:
                issues.append({"row": index, "code": "CONFLICTING_BIBLIOGRAPHY_PAPER_IDENTITIES"})
                continue
            if base_id not in proposed_bases:
                issues.append({"row": index, "code": "EXPLICIT_PAPER_ID_MISMATCH"})
                continue
            if not re.search(r"v[1-9]\d*$", pinned):
                issues.append({"row": index, "code": "UPSTREAM_VERSION_NOT_PINNED"})
                continue
            if any(re.search(r"v[1-9]\d*$", value) and value != pinned for value in proposed_ids):
                issues.append({"row": index, "code": "EXPLICIT_CITED_VERSION_MISMATCH"})
                continue
            identity = "EXPLICIT_BASE_ARXIV_MATCH_VERSION_PINNED_BY_EXTRACTION"
        members = sorted(occurrence_members | set(explicit_claims))
        if resolve_explicit_occurrences:
            result["occurrence_claim_resolution"] = resolution
        if len(members) > 1 and row.get("combination") != "JOINT_SUPPORT":
            issues.append({"row": index, "code": "MULTIPLE_UPSTREAM_CLAIMS_WITHOUT_JOINT_SUPPORT_JUDGEMENT"})
            continue
        group_id = "source-match:" + digest(canonical([target, members, matches_reference, index]))[7:31]
        groups[group_id] = {"id": group_id, "target": target, "members": members,
                            "relation": "SCIENTIFIC_CLAIM_DEPENDENCY", "disposition": "UNREVIEWED",
                            "judgement_ref": matches_reference["sha256"] + ":" + str(index),
                            "grouping_basis": "CANDIDATE_SOURCE_MATCH_THROUGH_UNRESOLVED_BOUNDARY"}
        nodes[target]["blocked_by"] = sorted(set(nodes[target].get("blocked_by", [])) |
                                              {"SOURCE_SUPPORT_ALIGNMENT_UNREVIEWED:" + group_id})
        result.update(status="CANDIDATE_EDGE_RECORDED_BOUNDARY_STILL_BLOCKED", candidate_group_id=group_id,
                      upstream_node_ids=members, identity_basis=identity,
                      source_bindings=located["bindings"], extra_conditions=row.get("extra_conditions", []),
                      proof_issues=row.get("proof_issues", []))
    combined_requests = {}
    for item in base["dependency_requests"] + upstream["dependency_requests"]:
        if item["id"] in combined_requests and combined_requests[item["id"]] != item:
            raise ValueError("Conflicting dependency request identity")
        combined_requests[item["id"]] = item
    combined = {"kind": "RecursiveCandidateGraphAssembly", "paper_id": base["paper_id"],
                "nodes": list(nodes.values()), "support_groups": list(groups.values()),
                "query_ids": base["query_ids"],
                "dependency_requests": list(combined_requests.values()),
                "match_records": base.get("match_records", []) + upstream.get("match_records", []) + records,
                "match_issues": base.get("match_issues", []) + upstream.get("match_issues", []) +
                                [{**issue, "matches_reference": matches_reference} for issue in issues],
                "join_history": base.get("join_history", []) + upstream.get("join_history", []) +
                                [{"upstream_paper_id": upstream_id, "matches_reference": matches_reference,
                                  "record_count": len(records), "issue_count": len(issues)}],
                "all_judgements_unreviewed": True, "source_completeness_asserted": False,
                "upstream_paper_id": upstream_id,
                "matches_reference": matches_reference}
    if "pdf_support_imports" in base or "pdf_support_imports" in upstream:
        retained = {}
        for record in base.get("pdf_support_imports", []) + upstream.get("pdf_support_imports", []):
            key = record["matches"]["sha256"]
            if key in retained and retained[key] != record:
                raise ValueError("Conflicting retained PDF support provenance")
            retained[key] = copy.deepcopy(record)
        combined["pdf_support_imports"] = list(retained.values())
    if "graph_format" in base:
        combined["graph_format"] = base["graph_format"]
    graph = prune_graph(combined["nodes"], combined["support_groups"], combined["query_ids"],
                        graph_format=combined.get("graph_format"))
    return {"assembly": combined, "graph": graph,
            "mathematical_status": "CHAIN_INCOMPLETE", "matched_source_is_not_proof": True}


def main():
    import argparse
    import uuid
    from core import PlanLedger, VERSION, utcnow, write_json
    from model import _frozen_source_payload
    from candidates import assemble_candidates
    parser = argparse.ArgumentParser(description="Join a newly extracted upstream paper through unreviewed source-match boundaries")
    for name in ("base", "upstream", "matches", "upstream-extraction", "source-directory", "output"):
        parser.add_argument("--" + name, required=True, type=pathlib.Path)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("Use a fresh output directory")
    refs, values = {}, {}
    for name in ("base", "upstream", "matches", "upstream_extraction"):
        path = getattr(args, name).resolve()
        if name in {"base", "upstream"}:
            with path.open("rb") as stream:
                raw = stream.read(MAX_GRAPH_BYTES + 1)
            if len(raw) > MAX_GRAPH_BYTES:
                raise ValueError("Graph artifact exceeds the 64 MiB ceiling")
        else:
            with path.open("rb") as stream:
                raw = stream.read(10 * 1024 * 1024 + 1)
            if len(raw) > 10 * 1024 * 1024:
                raise ValueError("Evidence exceeds the 10 MiB ceiling")
        refs[name] = {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}
        values[name] = (_verified_graph_json(refs[name]) if name in {"base", "upstream"}
                        else _verified_json(refs[name]))
    paper = values["upstream_extraction"]
    sources = _frozen_source_payload(paper, args.source_directory, source_directory=args.source_directory)
    response = _verified_json(values["upstream"]["response_reference"])
    reconstructed = assemble_candidates(paper, response.get("candidate", response), sources,
                                         response_reference=values["upstream"]["response_reference"],
                                         claim_reference_policy=values["upstream"].get("claim_reference_policy"))
    if canonical(reconstructed) != canonical(values["upstream"]):
        raise ValueError("Upstream assembly differs from its source-bound reconstruction")
    plan = {"contract_version": VERSION, "plan_id": "plan:" + uuid.uuid4().hex,
            "paper_id": values["base"]["paper_id"], "query_ids": values["base"]["query_ids"],
            "created_at": utcnow(), "cost_mode": "ACCOUNT_QUOTA", "decision_policy": "CANDIDATE_EXPLORATION",
            "limits": {"max_model_calls": 0, "max_cost_microusd": 0, "max_papers": 2,
                       "max_call_seconds": 1, "max_node_attempts": 1, "no_progress_limit": 1},
            "environment": {"mode": "ONE_RECURSIVE_CANDIDATE_JOIN", "input_references": refs,
                            "source_sha256_scope": "CANONICAL_INPUT_REFERENCE_BUNDLE"},
            "source_sha256": digest(canonical(refs))}
    ledger = PlanLedger(out, plan)
    write_json(out / "plan.json", plan)
    with ledger.stage("recursive.source_match_and_re_prune", refs) as receipt:
        result = join_candidate_paper(values["base"], values["upstream"], values["matches"], sources,
                                      matches_reference=refs["matches"])
        receipt["assembly"] = write_json(out / "assembly.json", result["assembly"])
        receipt["graph"] = write_json(out / "graph.json", result["graph"])
        current = [row for row in result["assembly"]["match_records"] if row["matches_reference"] == refs["matches"]]
        summary = {"status": "RECURSIVE_CANDIDATES_RECORDED", "mathematical_status": "CHAIN_INCOMPLETE",
                   "query_candidates": len(result["graph"]["query_ids"]), "selected_nodes": len(result["graph"]["nodes"]),
                   "selected_support_groups": len(result["graph"]["support_groups"]),
                   "joined_matches": sum(row["candidate_group_id"] is not None for row in current),
                   "match_rows": len(current), "match_issues": result["assembly"]["match_issues"],
                   "all_source_boundaries_still_unreviewed": True, "legacy_dag_used": False}
        receipt["summary"] = write_json(out / "summary.json", summary)
    write_json(out / "ledger.json", ledger.snapshot())
    print(json.dumps({key: value for key, value in summary.items() if key != "match_issues"}))


if __name__ == "__main__":
    main()
