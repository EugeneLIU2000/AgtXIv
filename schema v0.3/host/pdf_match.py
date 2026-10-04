"""Source-to-source dependency.match with a retained PDF upstream.

The frozen DECISION route selects Terra by default. Both sources are supplied in
full within host limits; this worker neither truncates them nor upgrades models.
Output is an unreviewed proposal, never a proof or a source-identity acceptance.
"""
from pathlib import Path

from core import canonical, digest
from model import _frozen_source_payload, call_model
from pdf_proof_context import bound_pdf_proof_context, pdf_proof_context, pdf_source_binding
from recursive_graph import _verified_graph_json, _verified_json


def _object(fields):
    return {"type": "object", "additionalProperties": False,
            "properties": fields, "required": list(fields)}


TEXT = {"type": "string", "minLength": 1}
STRINGS = {"type": "array", "items": TEXT}
PDF_MATCH_SCHEMA = _object({"matches": {"type": "array", "items": _object({
    "target_request_id": TEXT,
    "relation": {"enum": ["CANDIDATE_SUPPORT", "MISMATCH", "UNCERTAIN"]},
    "support_routes": {"type": "array", "items": _object({
        "upstream_claim_ids": {"type": "array", "minItems": 1, "items": TEXT},
        "combination": {"enum": ["SINGLE_CLAIM", "JOINT_SUPPORT"]},
        "route_semantics": {"enum": ["SINGLE_PROPOSED_ROUTE", "EXPLICIT_CANDIDATE_ALTERNATIVE"]},
        "extra_conditions": STRINGS, "proof_issues": STRINGS, "reason": TEXT,
    })},
    "extra_conditions": STRINGS, "proof_issues": STRINGS, "reason": TEXT,
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
})}})


def _downstream_context(nodes, entry, paper_id):
    if "pdf_run" in entry:
        context, images = bound_pdf_proof_context(nodes[0], entry)
        # Every request's claim must belong to the same retained PDF assembly.
        _, assembly = pdf_source_binding(paper_id, entry)
        originals = {row["id"]: row for row in assembly["nodes"]}
        for node in nodes:
            original = originals.get(node["id"])
            if original is None or any(original.get(key) != node.get(key) for key in
                    ("paper_id", "kind", "text", "conditions", "source_spans",
                     "source_reading_id", "unresolved_dependencies")):
                raise ValueError("PDF_MATCH_DOWNSTREAM_PDF_CLAIM_CHANGED")
        return context, images
    if set(entry) != {"extraction", "directory"}:
        raise ValueError("PDF_MATCH_DOWNSTREAM_SOURCE_ENTRY_INVALID")
    paper = _verified_json(entry["extraction"])
    if paper["paper"]["id"] != paper_id:
        raise ValueError("PDF_MATCH_DOWNSTREAM_PAPER_MISMATCH")
    directory = Path(entry["directory"])
    sources = _frozen_source_payload(paper, directory, source_directory=directory)
    by_path = {source["path"]: source for source in sources}
    for node in nodes:
        if not node.get("source_spans"):
            raise ValueError("PDF_MATCH_DOWNSTREAM_SPANS_REQUIRED")
        for span in node["source_spans"]:
            source = by_path[span["path"]]
            raw = source["text"].encode("utf-8")
            start, end = span["byte_start"], span["byte_end"]
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw)
                    or span["sha256"] != source["sha256"] or digest(raw[start:end]) != span["span_sha256"]):
                raise ValueError("PDF_MATCH_DOWNSTREAM_SPAN_CHANGED")
    return {"kind": "RetainedTeXMatchContext", "extraction": entry["extraction"],
            "paper_id": paper_id, "full_sources": sources}, []


def proposal_from_response(response, requests, upstream, pdf_run):
    """Host supplies immutable target requests and regions; models select IDs only."""
    requests = {row["id"]: row for row in requests}
    claims = {node["id"]: node for node in upstream["nodes"]}
    rows = []
    for judgement in response["matches"]:
        if judgement["relation"] != "CANDIDATE_SUPPORT":
            continue
        for route in judgement["support_routes"]:
            rows.append({**route, "target_request_id": judgement["target_request_id"],
                "target_request": requests[judgement["target_request_id"]],
                "relation": "CANDIDATE_SUPPORT",
                "source_regions": [{"claim_id": cid, "source_spans": claims[cid]["source_spans"]}
                                   for cid in route["upstream_claim_ids"]],
                "extra_conditions": judgement["extra_conditions"] + route["extra_conditions"],
                "proof_issues": judgement["proof_issues"] + route["proof_issues"],
                "reason": judgement["reason"] + "\n" + route["reason"]})
    return ({"kind": "PDFSupportMatchProposal", "upstream_paper_id": upstream["paper_id"],
             "pdf_run": pdf_run, "matches": rows} if rows else None)


def prepare_pdf_match(base_reference, request_ids, downstream_source,
                      upstream_paper_id, upstream_pdf_run):
    """Reconstruct the complete prompt, page order and response checks without dispatch."""
    base = _verified_graph_json(base_reference)
    if base.get("all_judgements_unreviewed") is not True:
        raise ValueError("PDF_MATCH_UNREVIEWED_BASE_REQUIRED")
    if not request_ids or len(request_ids) != len(set(request_ids)):
        raise ValueError("PDF_MATCH_DISTINCT_REQUESTS_REQUIRED")
    requests_by_id = {row["id"]: row for row in base["dependency_requests"]}
    nodes = {node["id"]: node for node in base["nodes"]}
    requests, downstream_nodes, papers = [], [], set()
    for ident in request_ids:
        request = requests_by_id[ident]
        if request.get("request_kind", request.get("kind")) != "external_claim_request":
            raise ValueError("PDF_MATCH_EXTERNAL_REQUEST_REQUIRED")
        node = nodes[request["downstream_node_id"]]
        paper_id = request.get("from_paper_id", base["paper_id"])
        if node.get("paper_id") != paper_id:
            raise ValueError("PDF_MATCH_DOWNSTREAM_REQUEST_PAPER_MISMATCH")
        requests.append(request)
        downstream_nodes.append(node)
        papers.add(paper_id)
    if len(papers) != 1:
        raise ValueError("PDF_MATCH_ONE_DOWNSTREAM_PAPER_PER_CALL")
    downstream, down_images = _downstream_context(downstream_nodes, downstream_source, papers.pop())
    summary, upstream = pdf_source_binding(upstream_paper_id, {"pdf_run": upstream_pdf_run})
    claims = {node["id"]: node for node in upstream["nodes"] if node.get("paper_id") == upstream_paper_id
              and node.get("kind") in {"definition", "claim", "theorem", "lemma", "corollary", "proof_local_claim"}}
    if not claims:
        raise ValueError("PDF_MATCH_UPSTREAM_ASSERTED_CANDIDATES_REQUIRED")
    upstream_context, up_images = pdf_proof_context(next(iter(claims.values())), summary["document"])
    # Context page indices are local; the offset makes the combined image order explicit.
    upstream_context["image_input_offset"] = len(down_images)
    downstream["image_input_offset"] = 0
    images = down_images + up_images
    if len(images) > 32:
        raise ValueError("PDF_MATCH_FULL_SOURCE_IMAGE_LIMIT_EXCEEDED")
    existing_routes = {target: [group["id"] for group in base["support_groups"] if group["target"] == target]
                       for target in request_ids}
    explicit_alternatives = {row.get("candidate_group_id") for row in base.get("match_records", [])
                             if row.get("route_semantics") == "EXPLICIT_CANDIDATE_ALTERNATIVE"}
    payload = {"base_assembly": base_reference, "upstream_pdf_run": upstream_pdf_run,
        "requests": [{**request, "downstream_candidate": {key: node.get(key) for key in
                      ("id", "kind", "text", "conditions", "source_spans", "unresolved_dependencies")}}
                     for request, node in zip(requests, downstream_nodes)],
        "downstream_full_context": downstream, "upstream_full_context": upstream_context,
        "upstream_candidates": list(claims.values()), "upstream_reading_scope": upstream.get("supplied_scope"),
        "existing_support_group_ids": existing_routes,
        "existing_explicit_alternative_group_ids": sorted(explicit_alternatives)}

    def validate(response):
        seen, issues = set(), []
        for row in response["matches"]:
            target, routes = row["target_request_id"], row["support_routes"]
            if target not in request_ids or target in seen:
                issues.append({"code": "PDF_MATCH_REQUEST_UNKNOWN_OR_DUPLICATE", "detail": target})
            seen.add(target)
            if bool(routes) != (row["relation"] == "CANDIDATE_SUPPORT"):
                issues.append({"code": "PDF_MATCH_RELATION_ROUTE_MISMATCH", "detail": target})
            route_ids = set()
            for route in routes:
                ids = route["upstream_claim_ids"]
                key = tuple(sorted(ids))
                if len(ids) != len(set(ids)) or set(ids) - claims.keys() or key in route_ids:
                    issues.append({"code": "PDF_MATCH_UPSTREAM_IDS_INVALID", "detail": target})
                route_ids.add(key)
                if route["combination"] != ("SINGLE_CLAIM" if len(ids) == 1 else "JOINT_SUPPORT"):
                    issues.append({"code": "PDF_MATCH_COMBINATION_INVALID", "detail": target})
                old = existing_routes.get(target, [])
                if ((len(routes) > 1 or old) and route["route_semantics"] != "EXPLICIT_CANDIDATE_ALTERNATIVE"
                        or old and not set(old).issubset(explicit_alternatives)):
                    issues.append({"code": "PDF_MATCH_ROUTE_SEMANTICS_UNSPECIFIED", "detail": target})
        if seen != set(request_ids):
            issues.append({"code": "PDF_MATCH_REQUEST_SCOPE_INCOMPLETE", "detail": "Every request needs a judgement"})
        return issues

    prompt = (
        "Operation dependency.match. Read both complete retained sources. Attached images are ordered: "
        "downstream pages first, then upstream pages, with explicit offsets in the source contexts. "
        "Compare the exact needed premise with upstream statements and proofs, including domains, "
        "transpose versus adjoint, normalization, invertibility and hidden assumptions. Citation or "
        "similar formula alone is insufficient. Return exactly one judgement per request. "
        "CANDIDATE_SUPPORT needs one or more support_routes. Each route is a sufficient proposed "
        "alternative; several jointly needed claims belong in one JOINT_SUPPORT route. "
        "Select only supplied asserted claim IDs. Do not invent source regions or quotations. "
        "MISMATCH and UNCERTAIN must have empty support_routes; they do not close the request. "
        "Retain missing bridges, reading limitations, stronger assumptions and errors. Do not "
        "silently repair the source. Every judgement and confidence remains unreviewed and uncalibrated.\n"
        "SOURCE DATA:\n" + canonical(payload).decode())
    return {"prompt": prompt, "images": images, "validate": validate,
            "requests": requests, "upstream": upstream}


def match_pdf_candidates(ledger, base_reference, request_ids, downstream_source,
                         upstream_paper_id, upstream_pdf_run, directory):
    """Dispatch once using the existing ledger; caller persists the complete result.

    downstream_source is {pdf_run: reference} or {extraction: reference, directory:
    path}. Preserve non-support outcomes and the receipt, not just the proposal.
    """
    prepared = prepare_pdf_match(base_reference, request_ids, downstream_source,
                                 upstream_paper_id, upstream_pdf_run)
    result = call_model(ledger, "dependency.match", "DECISION", prepared["prompt"], PDF_MATCH_SCHEMA, directory,
                        timeout=ledger.plan["limits"]["max_call_seconds"], candidate_validator=prepared["validate"],
                        image_references=prepared["images"])
    result["pdf_match_inputs"] = {"base_assembly": base_reference, "request_ids": request_ids,
        "downstream_source": downstream_source, "upstream_paper_id": upstream_paper_id,
        "upstream_pdf_run": upstream_pdf_run}
    if result["candidate"] is not None:
        result["pdf_support_proposal"] = proposal_from_response(
            result["candidate"], prepared["requests"], prepared["upstream"], upstream_pdf_run)
    return result
