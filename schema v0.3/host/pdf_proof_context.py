"""Prepare complete retained page context without claiming visual correctness."""
import math
from pathlib import Path

from core import digest
from recursive_graph import _verified_json


def pdf_source_binding(paper_id, entry):
    """Bind attributed paper identity to one immutable PDF candidate run."""
    if set(entry) != {"pdf_run"}:
        raise ValueError("PDF_SOURCE_ENTRY_REQUIRES_ONLY_PDF_RUN")
    summary = _verified_json(entry["pdf_run"])
    if summary.get("kind") in {"PDFModelExtractionRun", "PDFModelExtractionRecoveryRun"}:
        # Explicitly reconstruct the saved response and candidate graph. Changing
        # the summary's kind is never sufficient to admit model recovery output.
        from pdf_extract_recover import model_run_binding, recovery_binding
        binding = recovery_binding if summary["kind"] == "PDFModelExtractionRecoveryRun" else model_run_binding
        summary, assembly = binding(entry["pdf_run"])
        if summary["paper_id"] != paper_id or assembly["paper_id"] != paper_id:
            raise ValueError("PDF_SOURCE_PAPER_BINDING_MISMATCH")
        return summary, assembly
    assembly = _verified_json(summary["assembly"])
    if (summary.get("kind") != "PDFRegionCandidateRun"
            or assembly.get("kind") != "PDFCandidateGraphAssembly"
            or summary.get("paper_id") != paper_id or assembly.get("paper_id") != paper_id):
        raise ValueError("PDF_SOURCE_PAPER_BINDING_MISMATCH")
    return summary, assembly


def bound_pdf_proof_context(node, entry):
    summary, assembly = pdf_source_binding(node["paper_id"], entry)
    matches = [row for row in assembly["nodes"] if row["id"] == node["id"]]
    if len(matches) != 1:
        raise ValueError("PDF_SOURCE_NODE_BINDING_AMBIGUOUS_OR_MISSING")
    # Scheduler annotations may change; the source statement and its scope may not.
    for key in ("paper_id", "kind", "text", "conditions", "source_spans", "source_reading_id",
                "unresolved_dependencies"):
        if matches[0].get(key) != node.get(key):
            raise ValueError("PDF_SOURCE_NODE_CONTENT_CHANGED:" + key)
    context, images = pdf_proof_context(node, summary["document"])
    context["source_run"] = entry["pdf_run"]
    context["source_assembly"] = summary["assembly"]
    return context, images


def amendment_proof_context(node, entry):
    """Read a reconstructed amendment for review, without admitting it to research.

    Kept separate from pdf_source_binding until recursive amendment publication
    and its ledger audit exist. Merely obtaining context does not accept a node.
    """
    if set(entry) != {"pdf_run"}:
        raise ValueError("PDF_AMENDMENT_CONTEXT_REQUIRES_ONLY_PDF_RUN")
    from pdf_amendment_run import reconstruct_amendment
    summary, assembly = reconstruct_amendment(entry["pdf_run"])
    matches = [row for row in assembly["nodes"] if row["id"] == node["id"]]
    if len(matches) != 1:
        raise ValueError("PDF_AMENDMENT_CONTEXT_NODE_MISSING_OR_AMBIGUOUS")
    bound = matches[0]
    for key in ("paper_id", "kind", "text", "conditions", "source_spans",
                "source_reading_id", "unresolved_dependencies"):
        if bound.get(key) != node.get(key):
            raise ValueError("PDF_AMENDMENT_CONTEXT_NODE_CHANGED:" + key)
    context, images = pdf_proof_context(bound, summary["document"])
    preparation = _verified_json(summary["preparation"])
    original = _verified_json(preparation["original"])
    replaced_ids = {change["old_id"] for change in preparation["proposal"]["replacements"]}
    by_reading_id = {row["source_reading_id"]: row for row in assembly["nodes"]
                     if "source_reading_id" in row}
    associations = []
    for association in preparation["proof_context_associations"]:
        # Include every recorded scope, so local steps can also be reviewed in
        # the context of their conclusion. None becomes an incoming support edge.
        associations.append({
            "conclusion": by_reading_id[association["conclusion_id"]],
            "local_context": [by_reading_id[ident] for ident in association["context_ids"]],
            "reason": association["reason"],
            "assumption_discharge_verified": False,
        })
    context.update({"source_run": entry["pdf_run"], "source_assembly": summary["assembly"],
                    "source_amendment": summary["preparation"],
                    "original_source_run": summary["source_run"],
                    "reading_revision_proposal": preparation["proposal"],
                    "replaced_original_readings": [row for row in original["claims"]
                                                   if row["id"] in replaced_ids],
                    "proof_context_associations": associations,
                    "usage_boundary": "READING_REVIEW_ONLY_NOT_RECURSIVE_SOURCE_ADMISSION",
                    "source_alignment_accepted": False, "proof_discharge_verified": False})
    return context, images


def _asset(ref, limit):
    with Path(ref["path"]).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit or len(raw) != ref["byte_size"] or digest(raw) != ref["sha256"]:
        raise ValueError("PDF_CONTEXT_ASSET_CHANGED_OR_TOO_LARGE")
    return raw


def pdf_proof_context(node, document_reference):
    document = _verified_json(document_reference)
    if document.get("kind") != "FrozenPDFRegionDocument":
        raise ValueError("PDF_CONTEXT_DOCUMENT_KIND_INVALID")
    pages = document["pages"]
    count = document["page_count"]
    if type(count) is not int or not 1 <= count <= 32 or len(pages) != count:
        raise ValueError("PDF_CONTEXT_PAGE_COUNT_UNSUPPORTED")
    if [row["page"] for row in pages] != list(range(1, count + 1)):
        raise ValueError("PDF_CONTEXT_PAGE_ORDER_INVALID")
    _asset(document["pdf"], 64 * 1024 * 1024)
    images, total = [], 0
    for page in pages:
        raw = _asset(page["image"], 32 * 1024 * 1024)
        total += len(raw)
        if total > 32 * 1024 * 1024:
            raise ValueError("PDF_CONTEXT_IMAGES_TOO_LARGE")
        images.append(page["image"])
    spans = node.get("source_spans", [])
    if not spans:
        raise ValueError("PDF_CONTEXT_REGION_MISSING")
    for span in spans:
        page = span.get("page")
        if (span.get("kind") != "PDF_PAGE_REGION" or type(page) is not int or not 1 <= page <= count
                or span.get("pdf") != document["pdf"] or span.get("page_image") != images[page - 1]):
            raise ValueError("PDF_CONTEXT_REGION_ASSET_MISMATCH")
        rectangle = span.get("normalized_rectangle")
        if (span.get("coordinate_system") != "TOP_LEFT_UNIT_SQUARE" or not isinstance(rectangle, list)
                or len(rectangle) != 4 or any(type(x) not in (int, float) or not math.isfinite(x) for x in rectangle)
                or not (0 <= rectangle[0] < rectangle[2] <= 1 and 0 <= rectangle[1] < rectangle[3] <= 1)):
            raise ValueError("PDF_CONTEXT_RECTANGLE_INVALID")
    context = {"kind": "RetainedPDFProofContext", "document": document_reference,
               "paper_id": node["paper_id"], "page_regions": spans,
               "ordered_pages": [{"image_input_index": i, "page": page["page"], "image": page["image"]}
                                 for i, page in enumerate(pages)],
               "scope": "ALL_RETAINED_DOCUMENT_PAGES_IN_ORDER",
               "image_render_correspondence": document["image_render_correspondence"],
               "reading_report_is_attributed_not_independently_observed": True,
               "source_completeness_asserted": False, "source_alignment_accepted": False,
               "instruction": "Read the attached full pages. Regions locate the claim, not a verified quotation. "
                              "Do not infer missing proofs or external citations; preserve every premise and ambiguity."}
    if document.get("derived_text"):
        context["non_authoritative_derived_text"] = _asset(document["derived_text"], 4 * 1024 * 1024).decode("utf-8")
        context["derived_text_reference"] = document["derived_text"]
    return context, images
