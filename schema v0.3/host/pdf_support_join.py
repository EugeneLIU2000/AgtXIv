"""Join PDF claim candidates through retained, explicitly unreviewed match proposals.

This adapter does not discover identities, call a model or accept support. PDF
regions locate existing candidates; they are never fabricated text quotations.
The research controller must still schedule and budget PDF papers explicitly.
"""
from copy import deepcopy
import json
from pathlib import Path

from core import canonical, digest, reject_model_state
from graph import prune_graph
from pdf_proof_context import pdf_source_binding
from recursive_graph import _verified_json


def _request(row, paper_id):
    """Expose PDF requests in the research shape, preserving the original fields."""
    result = deepcopy(row)
    if "request_kind" not in result:
        if result.get("kind") != "external_claim_request":
            raise ValueError("PDF_JOIN_REQUEST_KIND_INVALID")
        result.update(request_kind="external_claim_request", from_paper_id=paper_id,
                      bibliography=[])
    return result


def join_pdf_candidate_paper(base, matches_reference):
    """Read a PDFSupportMatchProposal and return a new assembly and pruned graph.

    Each row carries the exact downstream request, selected upstream claim IDs
    and their existing source spans. This binds a proposed semantic judgement;
    it does not establish that the cited paper or theorem is the right one.
    """
    if base.get("all_judgements_unreviewed") is not True:
        raise ValueError("PDF_JOIN_REQUIRES_UNREVIEWED_BASE")
    proposal = _verified_json(matches_reference)
    from jsonschema import Draft202012Validator
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
    Draft202012Validator({"$defs": schema["$defs"],
                         "$ref": "#/$defs/PDFSupportMatchProposal"}).validate(proposal)
    if proposal.get("kind") != "PDFSupportMatchProposal":
        raise ValueError("PDF_JOIN_PROPOSAL_KIND_INVALID")
    upstream_id = proposal["upstream_paper_id"]
    summary, upstream = pdf_source_binding(upstream_id, {"pdf_run": proposal["pdf_run"]})
    if upstream.get("all_judgements_unreviewed") is not True:
        raise ValueError("PDF_JOIN_REQUIRES_UNREVIEWED_UPSTREAM")
    rows = proposal.get("matches")
    if not isinstance(rows, list) or not rows:
        raise ValueError("PDF_JOIN_MATCH_ROWS_REQUIRED")
    reject_model_state(rows)
    requests = {row["id"]: row for row in base["dependency_requests"]}
    selected = {node["id"]: node for node in upstream["nodes"]}
    prepared, targets = [], {}
    for index, row in enumerate(rows):
        target = row["target_request_id"]
        request = requests.get(target)
        if (request is None or request.get("request_kind", request.get("kind")) != "external_claim_request"
                or row.get("target_request") != request):
            raise ValueError("PDF_JOIN_TARGET_REQUEST_MISMATCH")
        if row.get("relation") != "CANDIDATE_SUPPORT":
            raise ValueError("PDF_JOIN_REQUIRES_CANDIDATE_SUPPORT_PROPOSAL")
        ids = row.get("upstream_claim_ids")
        if (not isinstance(ids, list) or not ids or any(not isinstance(cid, str) for cid in ids)
                or len(ids) != len(set(ids))):
            raise ValueError("PDF_JOIN_UPSTREAM_IDS_INVALID")
        for cid in ids:
            node = selected.get(cid)
            if (node is None or node.get("paper_id") != upstream_id or node.get("kind") not in
                    {"definition", "claim", "theorem", "lemma", "corollary", "proof_local_claim"}):
                raise ValueError("PDF_JOIN_UPSTREAM_CLAIM_UNKNOWN_OR_NONASSERTED")
        expected_spans = [{"claim_id": cid, "source_spans": selected[cid]["source_spans"]} for cid in ids]
        if row.get("source_regions") != expected_spans:
            raise ValueError("PDF_JOIN_SOURCE_REGIONS_MISMATCH")
        if row.get("combination") != ("SINGLE_CLAIM" if len(ids) == 1 else "JOINT_SUPPORT"):
            raise ValueError("PDF_JOIN_COMBINATION_UNSPECIFIED")
        if row.get("route_semantics") not in {"SINGLE_PROPOSED_ROUTE", "EXPLICIT_CANDIDATE_ALTERNATIVE"}:
            raise ValueError("PDF_JOIN_ROUTE_SEMANTICS_UNSPECIFIED")
        for key in ("extra_conditions", "proof_issues"):
            if not isinstance(row.get(key), list) or any(not isinstance(value, str) for value in row[key]):
                raise ValueError("PDF_JOIN_SCOPE_REPORT_REQUIRED")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            raise ValueError("PDF_JOIN_SEMANTIC_REASON_REQUIRED")
        targets.setdefault(target, []).append(row)
        prepared.append((index, target, sorted(ids), row))
    for alternatives in targets.values():
        if len(alternatives) > 1 and any(row["route_semantics"] != "EXPLICIT_CANDIDATE_ALTERNATIVE"
                                       for row in alternatives):
            raise ValueError("PDF_JOIN_CROSS_ROW_AND_OR_UNSPECIFIED")
    for target, alternatives in targets.items():
        existing = {group["id"] for group in base["support_groups"] if group["target"] == target}
        declared = {record.get("candidate_group_id") for record in base.get("match_records", [])
                    if record.get("route_semantics") == "EXPLICIT_CANDIDATE_ALTERNATIVE"}
        if existing and (not existing.issubset(declared) or any(
                row["route_semantics"] != "EXPLICIT_CANDIDATE_ALTERNATIVE" for row in alternatives)):
            raise ValueError("PDF_JOIN_EXISTING_ROUTE_SEMANTICS_UNSPECIFIED")

    combined = deepcopy(base)
    nodes = {node["id"]: node for node in combined["nodes"]}
    groups = {group["id"]: group for group in combined["support_groups"]}
    # This marker makes repeated application explicit instead of duplicating rows.
    prior = combined.setdefault("pdf_support_imports", [])
    import_record = {"matches": matches_reference, "pdf_run": proposal["pdf_run"],
                     "paper_id": upstream_id, "source_assembly": summary["assembly"],
                     "source_scope": deepcopy(upstream.get("supplied_scope")),
                     "source_completeness_asserted": False}
    if import_record in prior:
        raise ValueError("PDF_JOIN_ALREADY_IMPORTED")
    for node in upstream["nodes"]:
        old = nodes.get(node["id"])
        if old is not None:
            identity = lambda value: {key: item for key, item in value.items() if key != "blocked_by"}
            if identity(old) != identity(node):
                raise ValueError("PDF_JOIN_NODE_IDENTITY_CONFLICT")
            old["blocked_by"] = sorted(set(old.get("blocked_by", [])) | set(node.get("blocked_by", [])))
        else:
            nodes[node["id"]] = deepcopy(node)
    for group in upstream["support_groups"]:
        if group["id"] in groups and groups[group["id"]] != group:
            raise ValueError("PDF_JOIN_GROUP_IDENTITY_CONFLICT")
        groups[group["id"]] = deepcopy(group)
    for index, target, ids, row in prepared:
        if target not in nodes or nodes[target].get("kind") != "external_claim_request":
            raise ValueError("PDF_JOIN_TARGET_NODE_MISSING")
        group_id = "pdf-source-match:" + digest(canonical([target, ids, matches_reference, index]))[7:31]
        groups[group_id] = {"id": group_id, "target": target, "members": ids,
            "relation": "SCIENTIFIC_CLAIM_DEPENDENCY", "disposition": "UNREVIEWED",
            "judgement_ref": matches_reference["sha256"] + ":" + str(index),
            "grouping_basis": "CANDIDATE_PDF_SOURCE_MATCH_THROUGH_UNRESOLVED_BOUNDARY"}
        nodes[target]["blocked_by"] = sorted(set(nodes[target].get("blocked_by", [])) |
            {"SOURCE_SUPPORT_ALIGNMENT_UNREVIEWED:" + group_id,
             "PDF_SOURCE_IDENTITY_REQUIRES_REVIEW:" + upstream_id})
        combined.setdefault("match_records", []).append({"row": index,
            "target_request_id": target, "matches_reference": matches_reference,
            "status": "CANDIDATE_EDGE_RECORDED_BOUNDARY_STILL_BLOCKED",
            "candidate_group_id": group_id, "upstream_node_ids": ids,
            "source_alignment_accepted": False, "identity_basis": "UNREVIEWED_PDF_PAPER_IDENTITY",
            "source_bindings": row["source_regions"], "extra_conditions": row["extra_conditions"],
            "proof_issues": row["proof_issues"], "reason": row["reason"],
            "route_semantics": row["route_semantics"]})
    combined_requests = {item["id"]: item for item in combined["dependency_requests"]}
    for item in upstream["dependency_requests"]:
        item = _request(item, upstream_id)
        if item["id"] in combined_requests and combined_requests[item["id"]] != item:
            raise ValueError("PDF_JOIN_REQUEST_IDENTITY_CONFLICT")
        combined_requests[item["id"]] = item
    prior.append(import_record)
    combined.update(kind="RecursiveCandidateGraphAssembly", nodes=list(nodes.values()),
                    support_groups=list(groups.values()), dependency_requests=list(combined_requests.values()),
                    source_completeness_asserted=False, all_judgements_unreviewed=True)
    graph = prune_graph(combined["nodes"], combined["support_groups"], combined["query_ids"],
                        graph_format=combined.get("graph_format"))
    return {"assembly": combined, "graph": graph, "mathematical_status": "CHAIN_INCOMPLETE",
            "matched_source_is_not_proof": True, "new_model_calls": 0}
