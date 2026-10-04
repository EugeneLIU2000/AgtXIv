"""Reconstruct a completed PDF match attempt without a model call or Lean execution.

This is a local integrity audit using shared adapters, not semantic acceptance.
Failed/interrupted attempts and recursive ledger publication remain separate gates.
"""
import argparse
import json
from pathlib import Path

from core import canonical, digest, reject_model_state, utcnow, write_json
from image_evidence import image_evidence_issues
from model import SOURCE_ONLY_INSTRUCTION, MAX_MODEL_INPUT_BYTES, MAX_MODEL_INPUT_CHARACTERS
from model_routing import routing_evidence_issues
from pdf_extract_recover import reference
from pdf_match import PDF_MATCH_SCHEMA, prepare_pdf_match, proposal_from_response
from pdf_proof_context import _asset
from pdf_support_join import join_pdf_candidate_paper
from recursive_graph import _verified_graph_json, _verified_json


def reconstruct_pdf_match(summary_ref):
    from jsonschema import Draft202012Validator

    summary = _verified_json(summary_ref)
    if (summary.get("kind") != "PDFMatchAttempt" or summary.get("status") not in
            {"CANDIDATE_JOIN_RECORDED", "JUDGEMENTS_RECORDED_NO_SUPPORT_PROPOSAL"}):
        raise ValueError("PDF_MATCH_AUDIT_REQUIRES_COMPLETED_ATTEMPT; failures remain unaudited")
    if (summary.get("mathematical_status") != "CHAIN_INCOMPLETE"
            or summary.get("source_alignment_accepted") is not False
            or summary.get("source_completeness_asserted") is not False
            or summary.get("automatic_retry") is not False):
        raise ValueError("PDF_MATCH_AUDIT_SCOPE_PROMOTED")
    root = Path(summary_ref["path"]).resolve().parent
    inputs = _verified_json(summary["inputs"])
    plan = _verified_json(summary["plan"])
    result = _verified_json(summary["model_result"])
    if result.get("pdf_match_inputs") != inputs:
        raise ValueError("PDF_MATCH_AUDIT_INPUTS_CHANGED")
    prepared = prepare_pdf_match(inputs["base_assembly"], inputs["request_ids"], inputs["downstream_source"],
                                 inputs["upstream_paper_id"], inputs["upstream_pdf_run"])
    receipt = result["receipt"]
    call = Path(receipt["directory"]).resolve()
    if call.parent != root / "model":
        raise ValueError("PDF_MATCH_AUDIT_CALL_OUTSIDE_ATTEMPT")
    refs = {name: reference(call / name) for name in
            ("task.json", "receipt.json", "prompt.txt", "response.schema.json", "response.json", "events.jsonl")}
    task = _verified_json(refs["task.json"])
    response = _verified_json(refs["response.json"])
    schema = _verified_json(refs["response.schema.json"])
    if (_verified_json(refs["receipt.json"]) != receipt or task.get("kind") != "Task"
            or receipt.get("kind") != "ModelReceipt" or task.get("task_id") != receipt.get("call_id")
            or task.get("plan_id") != plan["plan_id"] or task.get("operation") != "dependency.match"
            or task.get("engine_class") != "DECISION" or receipt.get("outcome") != "CANDIDATE_RECORDED"
            or task.get("max_seconds") != plan["limits"]["max_call_seconds"]
            or receipt.get("model_identity_attested_by_provider") is not False
            or receipt.get("returncode") != 0 or receipt.get("error") is not None
            or receipt.get("validation_issues") != [] or receipt.get("unexpected_tool_events") != []
            or not plan.get("environment", {}).get("model_routing")
            or routing_evidence_issues(plan, task, receipt)):
        raise ValueError("PDF_MATCH_AUDIT_MODEL_RECEIPT_MISMATCH")
    prompt = (SOURCE_ONLY_INSTRUCTION + prepared["prompt"]).encode("utf-8")
    if (_asset(refs["prompt.txt"], MAX_MODEL_INPUT_BYTES) != prompt
            or digest(prompt) != task.get("prompt_sha256")
            or digest(prompt) != receipt.get("request_sha256")
            or schema != PDF_MATCH_SCHEMA or digest(canonical(schema)) != task.get("schema_sha256")
            or refs["response.json"]["sha256"] != receipt.get("response_sha256")
            or response != result.get("candidate")):
        raise ValueError("PDF_MATCH_AUDIT_PROMPT_SCHEMA_RESPONSE_CHANGED")
    if (task.get("input_character_count") != len(prompt.decode("utf-8"))
            or task.get("input_byte_size") != len(prompt) + len(canonical(schema))
            or task["input_character_count"] > MAX_MODEL_INPUT_CHARACTERS
            or task["input_byte_size"] > MAX_MODEL_INPUT_BYTES):
        raise ValueError("PDF_MATCH_AUDIT_INPUT_ACCOUNTING_CHANGED")
    if ([image["original"] for image in task.get("image_inputs", [])] != prepared["images"]
            or image_evidence_issues(task, receipt, call)):
        raise ValueError("PDF_MATCH_AUDIT_IMAGE_CONTEXT_CHANGED")
    events = _asset(refs["events.jsonl"], 10 * 1024 * 1024)
    if digest(events) != receipt.get("events_sha256"):
        raise ValueError("PDF_MATCH_AUDIT_EVENTS_CHANGED")
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if event.get("item", {}).get("type") in {"command_execution", "mcp_tool_call", "web_search", "file_change"}:
            raise ValueError("PDF_MATCH_AUDIT_SOURCE_ONLY_VIOLATION")
    reject_model_state(response)
    json.dumps(response, allow_nan=False)  # Match the source worker's non-finite JSON rejection.
    Draft202012Validator(schema).validate(response)
    if prepared["validate"](response):
        raise ValueError("PDF_MATCH_AUDIT_RESPONSE_SCOPE_INVALID")
    proposal = proposal_from_response(response, prepared["requests"], prepared["upstream"], inputs["upstream_pdf_run"])
    if proposal != result.get("pdf_support_proposal"):
        raise ValueError("PDF_MATCH_AUDIT_PROPOSAL_PROJECTION_CHANGED")
    join_schema = _verified_json(summary["join_schema"])
    current = json.loads((Path(__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
    if join_schema != current:
        raise ValueError("PDF_MATCH_AUDIT_JOIN_CONTRACT_CHANGED")
    joined = None
    if proposal is None:
        if summary["status"] != "JUDGEMENTS_RECORDED_NO_SUPPORT_PROPOSAL" or any(
                key in summary for key in ("proposal", "assembly", "graph")):
            raise ValueError("PDF_MATCH_AUDIT_NON_SUPPORT_PROMOTED")
    else:
        if summary["status"] != "CANDIDATE_JOIN_RECORDED" or _verified_json(summary["proposal"]) != proposal:
            raise ValueError("PDF_MATCH_AUDIT_SAVED_PROPOSAL_CHANGED")
        base = _verified_graph_json(inputs["base_assembly"])
        joined = join_pdf_candidate_paper(base, summary["proposal"])
        if any(_verified_graph_json(summary[key]) != joined[key] for key in ("assembly", "graph")):
            raise ValueError("PDF_MATCH_AUDIT_JOIN_RECONSTRUCTION_MISMATCH")
    judgements = {row["target_request_id"]: row for row in response["matches"]}
    outcomes = []
    for ident in inputs["request_ids"]:
        row = judgements[ident]
        outcome = {"request_id": ident, "upstream_paper_id": inputs["upstream_paper_id"],
            "status": "JUDGEMENT_RECORDED_UNREVIEWED", "mathematically_resolved": False,
            "model_result": summary["model_result"], "relation": row["relation"],
            "candidate_route_count": len(row["support_routes"]), "join_status": "NOT_APPLICABLE"}
        if row["relation"] == "CANDIDATE_SUPPORT":
            outcome.update(join_status="CANDIDATE_EDGE_RECORDED_BOUNDARY_STILL_BLOCKED",
                           assembly=summary["assembly"], graph=summary["graph"])
        outcomes.append(outcome)
    if _verified_json(summary["outcomes"]) != outcomes:
        raise ValueError("PDF_MATCH_AUDIT_OUTCOMES_CHANGED")
    snapshots = summary.get("runtime_sources", [])
    names = [Path(ref["path"]).name for ref in snapshots]
    if len(names) != len(set(names)) or not {
            "pdf_match.py", "pdf_match_run.py", "pdf_support_join.py", "pdf_proof_context.py",
            "pdf_extract_recover.py", "model.py", "model_routing.py", "core.py", "graph.py"
            }.issubset(names):
        raise ValueError("PDF_MATCH_AUDIT_RUNTIME_SNAPSHOTS_MISSING")
    for ref in snapshots:
        _asset(ref, 2 * 1024 * 1024)
    return {"summary": summary, "inputs": inputs, "plan": plan, "receipt": receipt,
            "outcomes": outcomes, "joined": joined}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Preserve earlier audit reports; choose a fresh output file")
    report = {"kind": "PDFMatchIntegrityAudit", "created_at": utcnow(),
              "source_alignment_accepted": False, "mathematical_status": "CHAIN_INCOMPLETE",
              "scope": "ONE_COMPLETED_ATTEMPT_SHARED_ADAPTER_RECONSTRUCTION",
              "recursive_ledger_and_publication_checked": False}
    try:
        report["attempt"] = reference(args.summary)
        reconstruct_pdf_match(report["attempt"])
        report["integrity_status"] = "PASS"
    except Exception as error:
        report.update(integrity_status="FAIL", error=type(error).__name__ + ": " + str(error))
    write_json(args.output.resolve(), report)
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report["integrity_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
