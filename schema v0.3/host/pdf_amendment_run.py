"""Persist and reconstruct one local PDF reading amendment.

No model dispatch, recursive publication or mathematical acceptance occurs here.
Execution performs integrity checks and therefore requires execution authorization.
"""
from pathlib import Path

from core import utcnow, write_json
from pdf_amendments import prepare_amendment
from pdf_candidates import assemble
from pdf_extract_recover import reference
from pdf_proof_context import pdf_source_binding, _asset
from recursive_graph import _verified_json


def _prepare(source_reference, proposal_reference):
    source = _verified_json(source_reference)
    # A bounded first implementation: amendments cannot yet chain themselves.
    if source.get("kind") not in {"PDFModelExtractionRun", "PDFModelExtractionRecoveryRun"}:
        raise ValueError("PDF_AMENDMENT_REQUIRES_MODEL_OR_RECOVERY_SOURCE")
    source, original_assembly = pdf_source_binding(
        source["paper_id"], {"pdf_run": source_reference})
    proposal = _verified_json(proposal_reference)
    if proposal.get("original") != source["candidate_report"]:
        raise ValueError("PDF_AMENDMENT_REPORT_NOT_BOUND_TO_SOURCE_RUN")
    document = _verified_json(source["document"])
    original = _verified_json(source["candidate_report"])
    if assemble(document, original) != original_assembly:
        raise ValueError("PDF_AMENDMENT_ORIGINAL_ASSEMBLY_MISMATCH")
    prepared = prepare_amendment(document, source["candidate_report"], proposal)
    candidate = prepared["candidate"]
    assembly = assemble(document, candidate)
    return source, prepared, assembly


def run_amendment(source_reference, proposal_reference, output):
    """Write a fresh, independent candidate revision; never edit source runs."""
    output = Path(output).resolve()
    protected = [Path(ref["path"]).resolve().parent
                 for ref in (source_reference, proposal_reference)]
    if any(output == root or root in output.parents for root in protected):
        raise ValueError("PDF_AMENDMENT_OUTPUT_MUST_BE_SEPARATE_FROM_INPUTS")
    output.mkdir(parents=True, exist_ok=False)
    summary = {"kind": "PDFReadingAmendmentRun", "status": "PREPARING",
               "created_at": utcnow(), "source_run": source_reference,
               "proposal": proposal_reference, "new_model_calls": 0,
               "source_alignment_accepted": False, "source_completeness_asserted": False,
               "proof_discharge_verified": False, "graph_publication_supported": False,
               "mathematical_status": "CHAIN_INCOMPLETE"}
    try:
        runtime = []
        runtime_root = output / "runtime"
        runtime_root.mkdir()
        for path in sorted(Path(__file__).resolve().parent.glob("*.py")):
            target = runtime_root / path.name
            target.write_bytes(path.read_bytes())
            runtime.append({"name": path.name, "snapshot": reference(target)})
        summary["runtime_sources"] = runtime
        source, prepared, assembly = _prepare(source_reference, proposal_reference)
        summary.update({"paper_id": source["paper_id"], "document": source["document"],
                        "candidate_report": write_json(output / "candidates.json", prepared["candidate"]),
                        "preparation": write_json(output / "preparation.json", prepared["preparation"]),
                        "assembly": write_json(output / "assembly.json", assembly),
                        "status": "CANDIDATE_REVISION_RECORDED"})
    except Exception as error:
        summary.update(status="AMENDMENT_PREPARATION_FAILED",
                       error={"type": type(error).__name__, "detail": str(error)})
        raise
    finally:
        summary["updated_at"] = utcnow()
        write_json(output / "summary.json", summary)
    return summary


def reconstruct_amendment(summary_reference):
    """Rebuild a normally completed revision; this is not semantic validation."""
    summary = _verified_json(summary_reference)
    if (summary.get("kind") != "PDFReadingAmendmentRun"
            or summary.get("status") != "CANDIDATE_REVISION_RECORDED"
            or type(summary.get("new_model_calls")) is not int
            or summary["new_model_calls"] != 0
            or summary.get("mathematical_status") != "CHAIN_INCOMPLETE"
            or any(summary.get(key) is not False for key in (
                "source_alignment_accepted", "source_completeness_asserted",
                "proof_discharge_verified", "graph_publication_supported"))
            or "error" in summary):
        raise ValueError("PDF_AMENDMENT_AUDIT_REQUIRES_UNREVIEWED_COMPLETED_REVISION")
    root = Path(summary_reference["path"]).resolve().parent
    host = Path(__file__).resolve().parent
    snapshots = summary.get("runtime_sources", [])
    names = [item["name"] for item in snapshots]
    if len(names) != len(set(names)) or set(names) != {path.name for path in host.glob("*.py")}:
        raise ValueError("PDF_AMENDMENT_AUDIT_RUNTIME_INVENTORY_CHANGED")
    for item in snapshots:
        path = Path(item["snapshot"]["path"]).resolve()
        if path != root / "runtime" / item["name"]:
            raise ValueError("PDF_AMENDMENT_AUDIT_SNAPSHOT_OUTSIDE_RUN")
        # Do not execute retained code. Current-code drift requires a deliberate
        # migration instead of claiming equivalent reconstruction automatically.
        if _asset(item["snapshot"], 10 * 1024 * 1024) != (host / item["name"]).read_bytes():
            raise ValueError("PDF_AMENDMENT_AUDIT_RUNTIME_CHANGED")
    source, prepared, assembly = _prepare(summary["source_run"], summary["proposal"])
    if summary.get("paper_id") != source["paper_id"] or summary.get("document") != source["document"]:
        raise ValueError("PDF_AMENDMENT_AUDIT_SOURCE_CHANGED")
    for key, filename, expected in (
        ("candidate_report", "candidates.json", prepared["candidate"]),
        ("preparation", "preparation.json", prepared["preparation"]),
        ("assembly", "assembly.json", assembly),
    ):
        if (Path(summary[key]["path"]).resolve() != root / filename
                or _verified_json(summary[key]) != expected):
            raise ValueError("PDF_AMENDMENT_AUDIT_OUTPUT_CHANGED:" + key)
    return summary, assembly
