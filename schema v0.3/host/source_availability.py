"""Retained DOI/PDF availability is evidence, not a mathematical support edge."""
from recursive_graph import _verified_json


def apply_dependency_gaps(assembly, references):
    """Expose attributed missing obligations without converting them to supports."""
    if not references:
        return assembly
    requests = {row["id"]: row for row in assembly["dependency_requests"]}
    nodes = {row["id"]: row for row in assembly["nodes"]}
    gaps = assembly.setdefault("dependency_gaps", {})
    for reference in references:
        review = _verified_json(reference)
        if review.get("kind") != "RetainedPDFDependencyGapReview":
            raise ValueError("UNSUPPORTED_DEPENDENCY_GAP_REVIEW")
        seen = set()
        for row in review["rows"]:
            ident = row["request_id"]
            if ident in seen:
                raise ValueError("DUPLICATE_DEPENDENCY_GAP_REQUEST")
            seen.add(ident)
            if (row.get("relation") != "BRIDGE_REQUIRED_NOT_DIRECT_SUPPORT"
                    or row.get("source_alignment_accepted") is not False
                    or not row.get("missing_obligations")
                    or any(not item.get("kind") or not item.get("description")
                           for item in row["missing_obligations"])):
                raise ValueError("INVALID_DEPENDENCY_GAP_OBLIGATIONS")
            request = requests.get(ident)
            if request is None:
                continue
            available = assembly.get("source_availability", {}).get(ident)
            downstream = nodes.get(row["downstream_node_id"])
            if (available is None or available["binding"] != review["source_availability"]
                    or request["from_paper_id"] != row["from_paper_id"]
                    or request["downstream_node_id"] != row["downstream_node_id"]
                    or downstream is None or downstream.get("text") != row["downstream_statement"]):
                raise ValueError("DEPENDENCY_GAP_SOURCE_OR_STATEMENT_MISMATCH")
            record = {"review": reference, "source_availability": review["source_availability"],
                      "relation": row["relation"], "missing_obligations": row["missing_obligations"],
                      "source_alignment_accepted": False, "mathematically_resolved": False}
            if ident in gaps and gaps[ident] != record:
                raise ValueError("CONFLICTING_DEPENDENCY_GAP_REVIEWS")
            gaps[ident] = record
            if ident in nodes:
                nodes[ident]["blocked_by"] = sorted(set(nodes[ident].get("blocked_by", [])) |
                    {"SOURCE_BRIDGE_REQUIRED:" + reference["sha256"]})
    return assembly


def apply_source_availability(assembly, references):
    if not references:
        return assembly
    availability = assembly.setdefault("source_availability", {})
    requests = {row["id"]: row for row in assembly["dependency_requests"]}
    nodes = {row["id"]: row for row in assembly["nodes"]}
    for reference in references:
        binding = _verified_json(reference)
        paper_id = binding.get("paper_id", "")
        if binding.get("kind") != "DOISourceAvailabilityBinding" or not paper_id.startswith("doi:"):
            raise ValueError("UNSUPPORTED_SOURCE_AVAILABILITY_BINDING")
        source = _verified_json(binding["source_assembly"])
        summary = _verified_json(binding["source_summary"])
        if source["paper_id"] != paper_id or summary["paper_id"] != paper_id:
            raise ValueError("AVAILABLE_SOURCE_IDENTITY_MISMATCH")
        if summary["assembly"] != binding["source_assembly"] or summary["document"] != binding["source_document"]:
            raise ValueError("AVAILABLE_SOURCE_REFERENCES_MISMATCH")
        _verified_json(binding["source_document"])
        _verified_json(binding["historical_alignment"])
        for target in binding["requests"]:
            request = requests.get(target["request_id"])
            if request is None:
                continue  # It can appear after a later upstream join.
            dois = {doi for entry in request.get("bibliography", [])
                    for doi in entry.get("identifiers", {}).get("doi", [])}
            if (paper_id[4:] not in dois or request["from_paper_id"] != target["from_paper_id"]
                    or request["downstream_node_id"] != target["downstream_node_id"]):
                raise ValueError("AVAILABLE_SOURCE_REQUEST_MISMATCH")
            record = {"paper_id": paper_id, "binding": reference,
                      "status": "PDF_SOURCE_AVAILABLE_SUPPORT_JOIN_REQUIRED",
                      "source_alignment_accepted": False}
            prior = availability.get(request["id"])
            if prior is not None and prior != record:
                raise ValueError("CONFLICTING_AVAILABLE_SOURCE_BINDINGS")
            availability[request["id"]] = record
            node = nodes.get(request["id"])
            if node is not None:
                node["blocked_by"] = sorted(set(node.get("blocked_by", [])) |
                    {"PDF_SUPPORT_JOIN_REQUIRED:" + reference["sha256"]})
    return assembly
