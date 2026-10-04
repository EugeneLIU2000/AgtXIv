"""Persist one budgeted PDF matching attempt and its candidate join.

The recursive controller supplies an existing PlanLedger; this function does not
create a second budget, retry a failed call, or register a paper outside the
controller's paper limit. Callers must admit both papers before invoking it.
"""
from pathlib import Path

from core import canonical, utcnow, write_json
from pdf_extract_recover import reference
from pdf_match import match_pdf_candidates
from pdf_support_join import join_pdf_candidate_paper
from recursive_graph import MAX_GRAPH_BYTES, _verified_graph_json


def run_pdf_match(ledger, base_reference, request_ids, downstream_source,
                  upstream_paper_id, upstream_pdf_run, output):
    """Retain all outcomes before attempting graph assembly; never overwrite a run."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    inputs = {"base_assembly": base_reference, "request_ids": list(request_ids),
              "downstream_source": downstream_source, "upstream_paper_id": upstream_paper_id,
              "upstream_pdf_run": upstream_pdf_run}
    summary = {"kind": "PDFMatchAttempt", "created_at": utcnow(), "status": "PREPARING",
               "inputs": write_json(output / "inputs.json", inputs),
               "mathematical_status": "CHAIN_INCOMPLETE", "source_alignment_accepted": False,
               "source_completeness_asserted": False, "automatic_retry": False}
    outcomes = [{"request_id": ident, "upstream_paper_id": upstream_paper_id,
                 "status": "DISPATCH_NOT_COMPLETED", "mathematically_resolved": False}
                for ident in request_ids]
    try:
        # Plan and runtime snapshots make the attempt reviewable even if dispatch
        # fails before creating a model receipt. They do not allocate new quota.
        summary["plan"] = write_json(output / "plan.json", ledger._frozen_plan())
        runtime = output / "runtime"
        runtime.mkdir()
        summary["runtime_sources"] = []
        for path in sorted(Path(__file__).parent.glob("*.py")):
            dest = runtime / path.name
            dest.write_bytes(path.read_bytes())
            summary["runtime_sources"].append(reference(dest))
        schema = Path(__file__).resolve().parents[1] / "schemas/research.schema.json"
        dest = output / "research.schema.json"
        dest.write_bytes(schema.read_bytes())
        summary["join_schema"] = reference(dest)
        base = _verified_graph_json(base_reference)
        summary["status"] = "MATCH_DISPATCH_PENDING"
        result = match_pdf_candidates(ledger, base_reference, request_ids, downstream_source,
                                      upstream_paper_id, upstream_pdf_run, output / "model")
        # Persist the complete result first, including non-support judgements.
        summary["model_result"] = write_json(output / "model-result.json", result)
        for outcome in outcomes:
            outcome.update(status="MODEL_RESPONSE_UNAVAILABLE", model_result=summary["model_result"])
        if result["candidate"] is None:
            summary["status"] = "MODEL_MATCH_FAILED"
        else:
            judgements = {row["target_request_id"]: row for row in result["candidate"]["matches"]}
            for outcome in outcomes:
                row = judgements[outcome["request_id"]]
                outcome.update(status="JUDGEMENT_RECORDED_UNREVIEWED", relation=row["relation"],
                               candidate_route_count=len(row["support_routes"]),
                               join_status="NOT_APPLICABLE" if row["relation"] != "CANDIDATE_SUPPORT"
                               else "NOT_PUBLISHED")
            # A later join failure must not erase these retained judgements.
            summary["outcomes"] = write_json(output / "outcomes.json", outcomes)
            proposal = result.get("pdf_support_proposal")
            if proposal is None:
                summary["status"] = "JUDGEMENTS_RECORDED_NO_SUPPORT_PROPOSAL"
            else:
                summary["proposal"] = write_json(output / "proposal.json", proposal)
                summary["status"] = "JOIN_PENDING"
                joined = join_pdf_candidate_paper(base, summary["proposal"])
                if max(len(canonical(joined[key])) for key in ("assembly", "graph")) > MAX_GRAPH_BYTES:
                    raise ValueError("PDF_MATCH_GRAPH_ARTIFACT_LIMIT_EXCEEDED")
                summary["assembly"] = write_json(output / "assembly.json", joined["assembly"])
                summary["graph"] = write_json(output / "graph.json", joined["graph"])
                summary["status"] = "CANDIDATE_JOIN_RECORDED"
                for outcome in outcomes:
                    if outcome.get("relation") == "CANDIDATE_SUPPORT":
                        outcome.update(join_status="CANDIDATE_EDGE_RECORDED_BOUNDARY_STILL_BLOCKED",
                                       assembly=summary["assembly"], graph=summary["graph"])
    except BaseException as error:
        summary["failure_phase"] = summary["status"]
        summary["status"] = ("ATTEMPT_INTERRUPTED" if isinstance(error, (KeyboardInterrupt, SystemExit))
                             else "ATTEMPT_FAILED")
        summary["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        summary["finished_at"] = utcnow()
        # Status may change inside this unique attempt directory; historical
        # model receipts and prior attempt directories are never overwritten.
        summary["outcomes"] = write_json(output / "outcomes.json", outcomes)
        write_json(output / "summary.json", summary)
    return summary
