"""One new PDF extraction call with retained inputs, routing and candidate graph.

Execution consumes model quota. This is not a validator or a Lean proof runner.
Existing output directories are never resumed or overwritten by this command.
"""
import argparse
import json
from pathlib import Path
import uuid

from chunks import reference
from core import VERSION, PlanLedger, utcnow, write_json
from graph import prune_graph
from model_routing import freeze_model_routing
from pdf_candidates import frozen_document, assemble
from pdf_extract import extract_pdf_candidates


def run(reading_path, paper_id, output, *, profile="LIGHT", timeout=300):
    if not isinstance(paper_id, str) or not paper_id.strip():
        raise ValueError("PDF_PAPER_ID_REQUIRED")
    if type(timeout) is not int or not 1 <= timeout <= 1800:
        raise ValueError("PDF_CALL_TIMEOUT_OUT_OF_RANGE")
    # Resolve routing before making any output or model reservation.
    routing = freeze_model_routing(profile)
    raw = Path(reading_path).read_bytes()
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("PDF_READING_INPUT_TOO_LARGE")
    reading = json.loads(raw)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "reading-input.json").write_bytes(raw)
    runtime = output / "runtime"
    runtime.mkdir()
    sources = []
    for path in sorted(Path(__file__).parent.glob("*.py")):
        dest = runtime / path.name
        dest.write_bytes(path.read_bytes())
        sources.append({"repository_path": str(path.resolve()), "snapshot": reference(dest)})
    summary = {"kind": "PDFModelExtractionRun", "paper_id": paper_id,
               "reading": reference(output / "reading-input.json"),
               "mathematical_status": "CHAIN_INCOMPLETE", "source_alignment_accepted": False,
               "source_completeness_asserted": False, "runtime_sources": sources}
    ledger = None
    try:
        document = frozen_document(reading, output)
        summary["document"] = write_json(output / "document.json", document)
        plan = {"contract_version": VERSION, "plan_id": "plan:" + uuid.uuid4().hex,
                "paper_id": paper_id, "query_ids": [], "created_at": utcnow(),
                "cost_mode": "ACCOUNT_QUOTA", "decision_policy": "CANDIDATE_EXPLORATION",
                "source_sha256": document["pdf"]["sha256"],
                "limits": {"max_papers": 1, "max_model_calls": 1,
                           "max_call_seconds": timeout, "max_cost_microusd": 0,
                           "no_progress_limit": 1, "max_node_attempts": 1},
                "environment": {"mode": "PDF_MODEL_EXTRACTION", "model_routing": routing,
                                "document": summary["document"], "runtime_sources": sources,
                                "proof_backend": "NOT_CONNECTED"}}
        summary["plan"] = write_json(output / "plan.json", plan)
        ledger = PlanLedger(output, plan)
        result = extract_pdf_candidates(ledger, summary["document"], paper_id, output / "model")
        summary["result"] = write_json(output / "result.json", result)
        if result["candidate"] is None:
            summary["status"] = "MODEL_EXTRACTION_FAILED"
        else:
            report = result["pdf_candidate_report"]
            summary["candidate_report"] = write_json(output / "candidates.json", report)
            assembly = assemble(document, report)
            summary["assembly"] = write_json(output / "assembly.json", assembly)
            summary["candidate_count"] = len(report["claims"])
            if assembly["query_ids"]:
                graph = prune_graph(assembly["nodes"], assembly["support_groups"], assembly["query_ids"])
                summary["graph"] = write_json(output / "graph.json", graph)
                summary["status"] = "CANDIDATE_GRAPH_RECORDED"
            else:
                summary["status"] = "NO_ASSERTED_QUERY_CANDIDATES"
    except BaseException as error:
        summary.update(status="RUN_INTERRUPTED" if isinstance(error, (KeyboardInterrupt, SystemExit))
                       else "RUN_FAILED", error=type(error).__name__ + ": " + str(error))
        raise
    finally:
        try:
            if ledger is not None:
                try:
                    summary["ledger"] = write_json(output / "ledger.json", ledger.snapshot())
                finally:
                    ledger.db.close()
        finally:
            write_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reading", required=True, type=Path)
    parser.add_argument("--paper-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--extraction-profile", choices=["LIGHT", "LIGHT_TERRA"], default="LIGHT")
    parser.add_argument("--max-call-seconds", type=int, default=300)
    args = parser.parse_args()
    result = run(args.reading, args.paper_id, args.output,
                 profile=args.extraction_profile, timeout=args.max_call_seconds)
    print(json.dumps({key: result.get(key) for key in
                      ("kind", "paper_id", "status", "mathematical_status", "candidate_count",
                       "document", "result", "assembly", "graph", "error")}, ensure_ascii=False))
    raise SystemExit(2)  # Candidate evidence never means the mathematical goal is closed.


if __name__ == "__main__":
    main()
