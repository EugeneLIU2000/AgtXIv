"""Bind retained PDF model output and recover missing-jsonschema host failures.

The recovery command executes validation. It requires explicit execution
authorization. Original runs and receipts remain immutable; output must be new.
The read-only binding functions also admit normally successful model runs, using
their own success gate. Neither path dispatches a model or accepts mathematics.
"""
import argparse
import json
from pathlib import Path
import re

from core import canonical, digest, reject_model_state, write_json
from graph import prune_graph
from model_routing import routing_evidence_issues
from pdf_candidates import assemble
from pdf_extract import PDF_EXTRACTION_SCHEMA, _candidate
from pdf_proof_context import _asset
from recursive_graph import _verified_graph_json, _verified_json


def reference(path):
    """Freeze small local recovery inputs without an unbounded allocation."""
    path = Path(path).resolve()
    with path.open("rb") as stream:
        raw = stream.read(10 * 1024 * 1024 + 1)
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("RECOVERY_INPUT_EXCEEDS_BYTE_CEILING")
    return {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}


def _document_inventory(old, document, source):
    """Check the retained inventory receipt, without rerunning pdfinfo/rendering."""
    reading = _verified_json(old["reading"])
    receipt = _verified_json(document["page_count_receipt"])
    with (source / "pdfinfo.log").open("rb") as stream:
        log = stream.read(1024 * 1024 + 1)
    match = re.search(rb"(?m)^Pages:\s+(\d+)\s*$", log)
    if (len(log) > 1024 * 1024 or match is None
            or receipt.get("input_sha256") != document["pdf"]["sha256"]
            or receipt.get("output_sha256") != digest(log)
            or receipt.get("exit_code") != 0 or receipt.get("status") != "SUCCEEDED"
            or receipt.get("command", [])[1:] != [document["pdf"]["path"]]
            or int(match[1]) != document["page_count"]
            or len(reading["page_images"]) != document["page_count"]
            or document["original_pdf"] != reading["pdf"]
            or document.get("reported_visually_read_pages") != reading.get("pages_visually_read", [])
            or document.get("source_completeness_asserted") is not False
            or document.get("ocr_is_authoritative_math") is not False
            or document.get("reading_report_is_attributed_not_independently_observed") is not True):
        raise ValueError("RECOVERY_DOCUMENT_INVENTORY_MISMATCH")
    if _asset(document["derived_text"], 8 * 1024 * 1024) != _asset(reading["derived_text"], 8 * 1024 * 1024):
        raise ValueError("RECOVERY_DERIVED_TEXT_CHANGED")
    for page, original in zip(document["pages"], reading["page_images"]):
        raw = _asset(page["image"], 32 * 1024 * 1024)
        if (raw != _asset(original, 32 * 1024 * 1024) or len(raw) < 24
                or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR"
                or page["width"] != int.from_bytes(raw[16:20], "big")
                or page["height"] != int.from_bytes(raw[20:24], "big")):
            raise ValueError("RECOVERY_PAGE_IMAGE_INVENTORY_MISMATCH")


def _reconstruct_run(summary_ref, *, recover_failure):
    """Reconstruct retained model evidence; success and recovery have distinct gates."""
    from jsonschema import Draft202012Validator

    source = Path(summary_ref["path"]).resolve().parent
    old = _verified_json(summary_ref)
    allowed = {"MODEL_EXTRACTION_FAILED"} if recover_failure else {
        "CANDIDATE_GRAPH_RECORDED", "NO_ASSERTED_QUERY_CANDIDATES"}
    if old.get("kind") != "PDFModelExtractionRun" or old.get("status") not in allowed:
        raise ValueError("PDF_MODEL_RUN_STATUS_NOT_ADMISSIBLE")
    plan = _verified_json(old["plan"])
    result = _verified_json(old["result"])
    document = _verified_json(old["document"])
    receipt = result["receipt"]
    error = "ModuleNotFoundError: No module named 'jsonschema'"
    if receipt.get("returncode") != 0 or receipt.get("unexpected_tool_events") != []:
        raise ValueError("PDF_MODEL_PROCESS_NOT_ADMISSIBLE")
    if recover_failure:
        if (result.get("candidate") is not None or receipt.get("outcome") != "FAILED"
                or receipt.get("error") != error or receipt.get("validation_issues") != [
                    {"code": "MODEL_RESPONSE_PROCESSING_FAILED", "detail": error}]):
            raise ValueError("RECOVERY_FAILURE_NOT_SUPPORTED")
    elif (receipt.get("outcome") != "CANDIDATE_RECORDED" or receipt.get("error") is not None
            or receipt.get("validation_issues") != []):
        raise ValueError("PDF_MODEL_SUCCESS_RECEIPT_REQUIRED")
    call = Path(receipt["directory"]).resolve()
    if call.parent != source / "model":
        raise ValueError("RECOVERY_CALL_OUTSIDE_SOURCE_RUN")
    inputs = {name: reference(call / name) for name in
              ("task.json", "receipt.json", "response.json", "response.schema.json", "prompt.txt", "events.jsonl")}
    task = _verified_json(inputs["task.json"])
    schema = _verified_json(inputs["response.schema.json"])
    response = _verified_json(inputs["response.json"])
    if _verified_json(inputs["receipt.json"]) != receipt:
        raise ValueError("RECOVERY_RECEIPT_MISMATCH")
    events = _asset(inputs["events.jsonl"], 10 * 1024 * 1024)
    if digest(events) != receipt.get("events_sha256"):
        raise ValueError("RECOVERY_EVENTS_CHANGED")
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if event.get("item", {}).get("type") in {"command_execution", "mcp_tool_call", "web_search", "file_change"}:
            raise ValueError("RECOVERY_SOURCE_ONLY_TASK_USED_TOOLS")
    if (task.get("operation") != "paper.extract" or receipt.get("operation") != "paper.extract"
            or task.get("kind") != "Task" or receipt.get("kind") != "ModelReceipt"
            or task.get("task_id") != receipt.get("call_id")
            or task.get("plan_id") != plan.get("plan_id")
            or plan.get("paper_id") != old.get("paper_id")
            or result.get("pdf_document") != old["document"]
            or plan["environment"].get("document") != old["document"]):
        raise ValueError("RECOVERY_TASK_PLAN_DOCUMENT_MISMATCH")
    if (not plan.get("environment", {}).get("model_routing")
            or routing_evidence_issues(plan, task, receipt)):
        raise ValueError("RECOVERY_MODEL_ROUTING_MISMATCH")
    if (inputs["response.json"]["sha256"] != receipt.get("response_sha256")
            or inputs["prompt.txt"]["sha256"] != task.get("prompt_sha256")
            or task.get("prompt_sha256") != receipt.get("request_sha256")
            or digest(canonical(schema)) != task.get("schema_sha256")
            or schema != PDF_EXTRACTION_SCHEMA):
        raise ValueError("RECOVERY_RESPONSE_OR_SCHEMA_BINDING_MISMATCH")
    prompt = _asset(inputs["prompt.txt"], 2 * 1024 * 1024).decode("utf-8")
    inventory = json.loads(prompt.split("\nSOURCE INVENTORY:\n", 1)[1])
    pages = document["pages"]
    count = document["page_count"]
    if (document.get("kind") != "FrozenPDFRegionDocument" or type(count) is not int
            or not 1 <= count <= 32 or len(pages) != count
            or [row["page"] for row in pages] != list(range(1, count + 1))
            or inventory.get("document") != old["document"]
            or inventory.get("paper_id") != old["paper_id"]
            or inventory.get("render_correspondence") != document.get("image_render_correspondence")
            or inventory.get("ordered_pages") != [
                {"image_index": i, "page": row["page"]} for i, row in enumerate(pages)]):
        raise ValueError("RECOVERY_SOURCE_INVENTORY_MISMATCH")
    _asset(document["pdf"], 64 * 1024 * 1024)
    if any(document["pdf"][key] != document["original_pdf"][key]
           for key in ("sha256", "byte_size")):
        raise ValueError("RECOVERY_ORIGINAL_PDF_MISMATCH")
    _document_inventory(old, document, source)
    images = task.get("image_inputs", [])
    if images != receipt.get("image_inputs") or len(images) != count:
        raise ValueError("RECOVERY_IMAGE_COUNT_MISMATCH")
    multimodal_digest = digest(canonical({"prompt_sha256": task["prompt_sha256"],
        "ordered_image_sha256": [row["snapshot"]["sha256"] for row in images]}))
    if any(item.get("multimodal_input_sha256") != multimodal_digest for item in (task, receipt)):
        raise ValueError("RECOVERY_MULTIMODAL_DIGEST_MISMATCH")
    total_image_bytes = 0
    for i, (image, page) in enumerate(zip(images, pages)):
        if image["index"] != i or image["original"] != page["image"]:
            raise ValueError("RECOVERY_IMAGE_ORDER_MISMATCH")
        if _asset(image["snapshot"], 32 * 1024 * 1024) != _asset(page["image"], 32 * 1024 * 1024):
            raise ValueError("RECOVERY_IMAGE_BYTES_MISMATCH")
        total_image_bytes += image["snapshot"]["byte_size"]
    if total_image_bytes > 32 * 1024 * 1024 or task.get("image_input_bytes") != total_image_bytes:
        raise ValueError("RECOVERY_IMAGE_TOTAL_MISMATCH")
    reject_model_state(response)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(response)
    report = _candidate(response, document, old["paper_id"])
    assembly = assemble(document, report)
    if not recover_failure and (result.get("candidate") != response or result.get("pdf_candidate_report") != report):
        raise ValueError("PDF_MODEL_RESULT_RESPONSE_MISMATCH")
    return old, report, assembly, inputs


def reconstruct_failed_run(summary_ref):
    """The recovery writer may process only the explicitly supported host failure."""
    return _reconstruct_run(summary_ref, recover_failure=True)


def _graph_binding(summary, report, assembly):
    if (summary.get("candidate_count") != len(report["claims"])
            or summary.get("source_alignment_accepted") is not False
            or summary.get("source_completeness_asserted") is not False
            or summary.get("mathematical_status") != "CHAIN_INCOMPLETE"):
        raise ValueError("PDF_MODEL_SUMMARY_SCOPE_CHANGED")
    if (_verified_json(summary["candidate_report"]) != report
            or _verified_graph_json(summary["assembly"]) != assembly):
        raise ValueError("RECOVERY_CANDIDATES_OR_ASSEMBLY_CHANGED")
    if assembly["query_ids"]:
        graph = prune_graph(assembly["nodes"], assembly["support_groups"], assembly["query_ids"])
        if (summary.get("status") != "CANDIDATE_GRAPH_RECORDED"
                or _verified_graph_json(summary["graph"]) != graph):
            raise ValueError("RECOVERY_GRAPH_CHANGED")
    elif summary.get("status") != "NO_ASSERTED_QUERY_CANDIDATES" or "graph" in summary:
        raise ValueError("RECOVERY_EMPTY_QUERY_STATUS_CHANGED")


def model_run_binding(summary_ref):
    """Admit a normally successful model run by reconstructing its saved output."""
    summary, report, assembly, _ = _reconstruct_run(summary_ref, recover_failure=False)
    _graph_binding(summary, report, assembly)
    plan = _verified_json(summary["plan"])
    snapshots = summary.get("runtime_sources", [])
    if snapshots != plan["environment"].get("runtime_sources"):
        raise ValueError("PDF_MODEL_RUNTIME_PLAN_MISMATCH")
    names = [Path(item["snapshot"]["path"]).name for item in snapshots]
    required = {"pdf_extract_run.py", "pdf_extract.py", "pdf_candidates.py", "graph.py",
                "core.py", "model.py", "model_routing.py", "pdf_proof_context.py", "recursive_graph.py"}
    if len(names) != len(set(names)) or not required.issubset(names):
        raise ValueError("PDF_MODEL_RUNTIME_SNAPSHOTS_MISSING")
    for item in snapshots:
        _asset(item["snapshot"], 2 * 1024 * 1024)
    return summary, assembly


def recovery_binding(summary_ref):
    """Recompute a recovery artifact before allowing it into proof source context.

    Uses the shared adapter; this is integrity reconstruction, not an independent
    semantic review or a replay of the model. No historical Python is executed.
    """
    recovered = _verified_json(summary_ref)
    if recovered.get("kind") != "PDFModelExtractionRecoveryRun":
        raise ValueError("RECOVERY_SUMMARY_KIND_INVALID")
    old, report, assembly, inputs = reconstruct_failed_run(recovered["source_run"])
    if (recovered.get("inputs") != inputs or recovered.get("document") != old["document"]
            or recovered.get("paper_id") != old["paper_id"]
            or recovered.get("candidate_count") != len(report["claims"])
            or recovered.get("new_model_calls") != 0
            or recovered.get("original_outcome") != "FAILED"
            or recovered.get("source_alignment_accepted") is not False
            or recovered.get("source_completeness_asserted") is not False
            or recovered.get("mathematical_status") != "CHAIN_INCOMPLETE"):
        raise ValueError("RECOVERY_SUMMARY_BINDING_MISMATCH")
    _graph_binding(recovered, report, assembly)
    snapshots = recovered.get("runtime_sources", [])
    names = [Path(ref["path"]).name for ref in snapshots]
    required = {"pdf_extract_recover.py", "pdf_extract.py", "pdf_candidates.py", "graph.py",
                "core.py", "chunks.py", "model_routing.py", "pdf_proof_context.py", "recursive_graph.py"}
    if len(names) != len(set(names)) or not required.issubset(names):
        raise ValueError("RECOVERY_RUNTIME_SNAPSHOTS_MISSING")
    for ref in snapshots:
        _asset(ref, 2 * 1024 * 1024)
    return recovered, assembly


def recover(source, output):
    source = Path(source).resolve()
    output = Path(output).resolve()
    # A recovery may not add files inside the original run or overwrite an old one.
    if output == source or source in output.parents or output.exists():
        raise FileExistsError("RECOVERY_REQUIRES_NEW_SEPARATE_OUTPUT_DIRECTORY")
    summary_ref = reference(source / "summary.json")
    old, report, assembly, inputs = reconstruct_failed_run(summary_ref)
    output.mkdir(parents=True, exist_ok=False)
    runtime = output / "runtime"
    runtime.mkdir()
    snapshots = []
    for path in sorted(Path(__file__).parent.glob("*.py")):
        dest = runtime / path.name
        dest.write_bytes(path.read_bytes())
        snapshots.append(reference(dest))
    recovered = {"kind": "PDFModelExtractionRecoveryRun", "paper_id": old["paper_id"],
                 "source_run": summary_ref, "inputs": inputs, "document": old["document"],
                 "runtime_sources": snapshots, "new_model_calls": 0,
                 "original_outcome": "FAILED", "source_alignment_accepted": False,
                 "source_completeness_asserted": False, "mathematical_status": "CHAIN_INCOMPLETE",
                 "candidate_count": len(report["claims"]),
                 "candidate_report": write_json(output / "candidates.json", report),
                 "assembly": write_json(output / "assembly.json", assembly),
                 "status": "NO_ASSERTED_QUERY_CANDIDATES"}
    if assembly["query_ids"]:
        graph = prune_graph(assembly["nodes"], assembly["support_groups"], assembly["query_ids"])
        recovered["graph"] = write_json(output / "graph.json", graph)
        recovered["status"] = "CANDIDATE_GRAPH_RECORDED"
    write_json(output / "summary.json", recovered)
    return recovered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = recover(args.source, args.output)
    print(json.dumps({key: result[key] for key in
                      ("kind", "status", "candidate_count", "new_model_calls", "mathematical_status")}))
    raise SystemExit(2)  # Candidate graph is not a mathematical completion certificate.
