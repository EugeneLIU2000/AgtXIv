"""Bind model-reported source clauses without asserting inventory completeness."""
from premise_evidence import bind_premise_report
from copy import deepcopy


def _within_node(span, node):
    for original in node.get("source_spans", []):
        if span.get("kind") == "PDF_PAGE_REGION":
            if span == original:
                return True
        elif (span.get("path") == original.get("path") and
              span.get("sha256") == original.get("sha256") and
              original.get("offset_unit") == "BYTE" and original.get("interval") == "HALF_OPEN" and
              type(original.get("byte_start")) is int and type(original.get("byte_end")) is int and
              original["byte_start"] <= span["byte_start"] < span["byte_end"] <= original["byte_end"]):
            return True
    return False


def bind_clause_report(report, sources, node=None):
    seen, coverage, unbound = set(), [], []
    pdf_contexts = [row for row in sources if row.get("kind") == "RetainedPDFProofContext"]
    if len(pdf_contexts) > 1:
        raise ValueError("CLAUSE_PDF_CONTEXT_AMBIGUOUS")
    for item in report:
        clause_id = item["clause_id"]
        if not clause_id.strip() or clause_id in seen:
            raise ValueError("CLAUSE_ID_EMPTY_OR_DUPLICATED")
        seen.add(clause_id)
        evidence = bind_premise_report([{
            "source_role": item["source_role"],
            "source_evidence_description": item["source_evidence_description"],
            "source_path": item["source_path"], "source_quote": item["source_quote"]}], sources)["rows"][0]
        indices = item.get("pdf_region_indices", [])
        if (not isinstance(indices, list) or any(type(i) is not int or i < 0 for i in indices)
                or len(indices) != len(set(indices))):
            raise ValueError("CLAUSE_PDF_REGION_INDICES_INVALID")
        if indices:
            if not pdf_contexts or item["source_role"] == "NOT_LOCATED":
                raise ValueError("CLAUSE_PDF_REGION_WITHOUT_LOCATED_CONTEXT")
            regions = pdf_contexts[0]["page_regions"]
            if any(i >= len(regions) for i in indices):
                raise ValueError("CLAUSE_PDF_REGION_INDEX_OUT_OF_RANGE")
            # Context regions were bound to the frozen PDF and ordered images
            # by bound_pdf_proof_context. Model input cannot replace their refs.
            evidence["source_spans"] = [deepcopy(regions[i]) for i in indices]
            evidence["status"] = "PDF_REGIONS_BOUND_SEMANTICS_UNREVIEWED"
        if not evidence["source_spans"]:
            unbound.append({"clause_id": clause_id, "status": evidence["status"]})
            continue
        if node is not None and not all(_within_node(span, node) for span in evidence["source_spans"]):
            unbound.append({"clause_id": clause_id, "status": "OUTSIDE_TARGET_NODE_SOURCE_SCOPE",
                            "located_source_spans": evidence["source_spans"]})
            continue
        coverage.append({"clause_id": clause_id, "statement": item["statement"],
                         "source_spans": evidence["source_spans"], "relation": item["relation"],
                         "remaining_obligations": item["remaining_obligations"]})
    result = {"kind": "ClauseSourceEvidence", "coverage": coverage, "unbound": unbound,
            "inventory_complete": False, "source_alignment_accepted": False}
    if node is not None:
        result.update(scope_protocol="NODE_SOURCE_SPANS_V1", source_node_id=node["id"])
    return result


def clause_binding_coverage(evidence):
    # Do not expose a seemingly complete subset when another reported clause
    # lacks a text or retained-region binding.
    return [] if evidence["unbound"] else evidence["coverage"]
