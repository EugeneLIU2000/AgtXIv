"""Source-only PDF extraction through the frozen LIGHT paper.extract route.

This entry point does not acquire/render PDFs or claim extraction completeness.
It consumes a retained document produced by pdf_candidates.frozen_document.
"""
from core import canonical
from model import call_model
from pdf_candidates import assemble
from pdf_proof_context import _asset
from recursive_graph import _verified_json


def _object(properties):
    return {"type": "object", "additionalProperties": False,
            "properties": properties, "required": list(properties)}


_TEXT = {"type": "string", "minLength": 1}
_STRINGS = {"type": "array", "items": _TEXT}
PDF_EXTRACTION_SCHEMA = _object({
    "claims": {"type": "array", "items": _object({
        "id": _TEXT,
        "role": {"enum": ["DEFINITION", "CLAIM", "THEOREM", "LEMMA",
                           "COROLLARY", "PROOF_LOCAL_CLAIM", "CONTRADICTION_CONTEXT"]},
        "statement": _TEXT, "conditions": _STRINGS,
        "page": {"type": "integer", "minimum": 1},
        "region": {"type": "array", "items": {"type": "number", "minimum": 0,
                    "maximum": 1}, "minItems": 4, "maxItems": 4},
        "printed_page": {"type": ["string", "null"]},
        "internal": _STRINGS, "external": _STRINGS,
        "unresolved_dependencies": _STRINGS,
    })},
    "reading_limitations": _STRINGS,
})


def _candidate(response, document, paper_id):
    rows = []
    for claim in response["claims"]:
        rows.append({key: claim[key] for key in
                     ("id", "role", "statement", "conditions", "internal", "external",
                      "unresolved_dependencies")})
        rows[-1]["source"] = {"pdf": document["original_pdf"], "page": claim["page"],
                              "region": claim["region"], "printed_page": claim["printed_page"]}
    return {"source_identity": paper_id, "claims": rows,
            "coverage": {"scope": "ALL_RETAINED_DOCUMENT_PAGES",
                         "reading_limitations": response["reading_limitations"],
                         "all_math_claims_extracted": False}}


def extract_pdf_candidates(ledger, document_reference, paper_id, directory):
    if not isinstance(paper_id, str) or not paper_id.strip():
        raise ValueError("PDF_EXTRACTION_PAPER_ID_REQUIRED")
    document = _verified_json(document_reference)
    if document.get("kind") != "FrozenPDFRegionDocument":
        raise ValueError("PDF_EXTRACTION_DOCUMENT_KIND_INVALID")
    pages, count = document["pages"], document["page_count"]
    if (type(count) is not int or not 1 <= count <= 32 or len(pages) != count
            or [page["page"] for page in pages] != list(range(1, count + 1))):
        raise ValueError("PDF_EXTRACTION_REQUIRES_ORDERED_COMPLETE_DOCUMENT_AT_MOST_32_PAGES")
    _asset(document["pdf"], 64 * 1024 * 1024)
    if any(document["original_pdf"][key] != document["pdf"][key]
           for key in ("sha256", "byte_size")):
        raise ValueError("PDF_EXTRACTION_ORIGINAL_SOURCE_MISMATCH")
    images = [page["image"] for page in pages]
    payload = {"paper_id": paper_id, "document": document_reference,
               "ordered_pages": [{"image_index": i, "page": page["page"]}
                                 for i, page in enumerate(pages)],
               "render_correspondence": document["image_render_correspondence"]}
    prompt = (
        "Operation paper.extract. Read all attached PDF page images in order. Extract mathematical "
        "claims including definitions, proof-local steps, quantifier domains and conditions. "
        "A library cover or bibliography is not the article body. Use stable unique local IDs. "
        "Keep contradiction assumptions separate from asserted conclusions. "
        "When a proof by contradiction excludes a case, emit the local assumption and the asserted "
        "exclusion as separate rows; do not label the whole argument CONTRADICTION_CONTEXT. "
        "Keep matrix order, generator count, and vector-space dimension distinct; scalar matrix "
        "identities require the identity matrix. Preserve transpose versus adjoint and index exclusions. "
        "Record unresolved trivial cases or missing field restrictions instead of silently repairing scope. "
        "Anchor each statement "
        "at its actual page with a nonempty top-left normalized [x0,y0,x1,y1] rectangle; record "
        "the printed page separately. A region is an approximate locator, not a verified quotation. "
        "Use internal IDs only for claims in this response; external lists contain only citations "
        "used as mathematical premises, with the needed statement and citation detail. Historical "
        "mentions and criticized arguments are not automatically supports. Record ambiguous or "
        "implicit dependencies in unresolved_dependencies, never fill them from outside knowledge. "
        "Record illegible pages, split-page statements and omitted scopes in reading_limitations. "
        "Do not claim completeness, acceptance or verification.\nSOURCE INVENTORY:\n"
        + canonical(payload).decode("utf-8"))

    def check(response):
        try:
            assemble(document, _candidate(response, document, paper_id))
        except (ValueError, KeyError, TypeError) as error:
            return [{"code": "PDF_CANDIDATE_BINDING_FAILED", "detail": str(error)}]
        return []

    result = call_model(ledger, "paper.extract", "LIGHT", prompt, PDF_EXTRACTION_SCHEMA,
                        directory, timeout=ledger.plan["limits"]["max_call_seconds"],
                        candidate_validator=check, image_references=images)
    result["pdf_document"] = document_reference
    if result["candidate"] is not None:
        result["pdf_candidate_report"] = _candidate(result["candidate"], document, paper_id)
    return result
