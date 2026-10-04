"""Audit one real recursive-research run without upgrading scientific judgements."""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
from image_evidence import image_evidence_issues
from review_blocks import apply_review_blocks
from source_availability import apply_source_availability, apply_dependency_gaps
from source_corrections import apply_source_corrections
import sqlite3

from candidates import assemble_candidates, select_candidate_graph
from core import canonical, digest, utcnow, write_json
from model import _frozen_source_payload
from recursive_graph import _verified_graph_json, _verified_json, join_candidate_paper
from arxiv_metadata import parse_version
from extract_batches import audit_batch_dispatch
from model_routing import routing_evidence_issues, validate_policy
from research import accepted_support_edges, bind_query


def audit(run):
    from jsonschema import Draft202012Validator
    run = pathlib.Path(run).resolve()
    plan = json.loads((run / "plan.json").read_bytes())
    ledger = json.loads((run / "ledger.json").read_bytes())
    state = json.loads((run / "checkpoint.json").read_bytes())
    frontier = json.loads((run / "frontier.json").read_bytes())
    issues = []
    def reference(path):
        raw = path.read_bytes()
        return {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}
    projection_refs = {name: reference(run / name) for name in
                       ("plan.json", "ledger.json", "checkpoint.json", "frontier.json")}
    def require(condition, code):
        if not condition:
            issues.append({"code": code})
    db = sqlite3.connect((run / "ledger.sqlite").as_uri() + "?mode=ro", uri=True)
    pid = plan["plan_id"]
    try:
        frozen = db.execute("SELECT spec FROM plans WHERE id=?", (pid,)).fetchone()
        require(frozen is not None and json.loads(frozen[0]) == plan == ledger["plan"], "FROZEN_PLAN_MISMATCH")
        events = [{"sequence": row[0], "kind": row[1], "payload": json.loads(row[2])}
                  for row in db.execute("SELECT seq,kind,payload FROM events WHERE plan_id=? ORDER BY seq", (pid,))]
        require(events == ledger["events"], "LEDGER_EVENT_PROJECTION_MISMATCH")
        rows = list(db.execute("SELECT paper_id,state,admitted,claim_token FROM frontier WHERE plan_id=?", (pid,)))
        admissions = {row[0]: {"state": row[1], "admitted": row[2], "claim_token": row[3],
                               "evidence": json.loads(row[4]) if row[4] else None, "updated": row[5]}
                      for row in db.execute("SELECT paper_id,state,admitted,claim_token,admission_json,updated FROM frontier WHERE plan_id=?", (pid,))}
        admitted = sum(row[2] for row in rows)
        require(admitted == frontier["admitted_papers"] and admitted <= plan["limits"]["max_papers"], "PAPER_QUOTA_MISMATCH")
        require(any(row[0] == plan["paper_id"] and row[2] == 1 for row in rows), "QUERY_PAPER_NOT_COUNTED")
        require(not any(row[3] for row in rows), "LIVE_FRONTIER_WORK_REMAINS")
        require({row[0]: row[1] for row in rows} == {row["paper_id"]: row["state"] for row in frontier["papers"]}, "FRONTIER_STATE_PROJECTION_MISMATCH")
        require({pid: row["evidence"] for pid, row in admissions.items()} ==
                {row["paper_id"]: row.get("admission_evidence") for row in frontier["papers"]},
                "FRONTIER_ADMISSION_PROJECTION_MISMATCH")
        calls = list(db.execute("SELECT id,state,receipt FROM calls WHERE plan_id=?", (pid,)))
        call_start_times = dict(db.execute("SELECT id,started FROM calls WHERE plan_id=?", (pid,)))
        call_operations = dict(db.execute("SELECT id,operation FROM calls WHERE plan_id=?", (pid,)))
        require(len(calls) == len(ledger["calls"]) <= plan["limits"]["max_model_calls"], "MODEL_CALL_QUOTA_MISMATCH")
        require({row[0]: [row[1], json.loads(row[2]) if row[2] else None] for row in calls} ==
                {row["id"]: [row["state"], row["receipt"]] for row in ledger["calls"]}, "CALL_RECEIPT_PROJECTION_MISMATCH")
        require(not any(row[1] == "RESERVED" for row in calls), "LIVE_MODEL_CALL_REMAINS")
    finally:
        db.close()
    schema = json.loads((pathlib.Path(__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
    for value, kind in ((plan, "Plan"), (ledger, "PlanLedger")):
        validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/" + kind})
        issues.extend({"code": "SCHEMA_MISMATCH", "subject": kind, "path": list(error.absolute_path), "detail": error.message}
                      for error in validator.iter_errors(value))
    for entry in plan["environment"]["runtime_sources"]:
        require(digest(pathlib.Path(entry["snapshot"]).read_bytes()) == entry["sha256"], "RUNTIME_SNAPSHOT_MISMATCH")
    if "model_routing" in plan["environment"]:
        try:
            validate_policy(plan["environment"]["model_routing"])
        except (ValueError, TypeError, KeyError) as error:
            issues.append({"code": "MODEL_ROUTING_INVALID", "detail": str(error)})
        for call_id, _, encoded in calls:
            if not encoded:
                continue
            receipt = json.loads(encoded)
            directory = pathlib.Path(receipt["directory"])
            task = json.loads((directory / "task.json").read_bytes())
            issues.extend(image_evidence_issues(task, receipt, directory))
            if "input_character_count" in task:
                prompt = (directory / "prompt.txt").read_bytes().decode("utf-8")
                require(task["input_character_count"] == len(prompt)
                        and task["input_character_count"] <= task["max_input_characters"] == 1048576,
                        "MODEL_PROMPT_CHARACTER_LIMIT_MISMATCH")
            validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/Task"})
            issues.extend({"code": "SCHEMA_MISMATCH", "subject": call_id, "detail": error.message}
                          for error in validator.iter_errors(task))
            require(json.loads((directory / "receipt.json").read_bytes()) == receipt, "MODEL_RECEIPT_FILE_MISMATCH")
            require(task.get("task_id") == call_id and task.get("plan_id") == pid, "MODEL_ROUTING_TASK_IDENTITY_MISMATCH")
            require(task.get("operation") == receipt.get("operation") == call_operations[call_id],
                    "MODEL_OPERATION_DIFFERS_FROM_RESERVED_CALL")
            issues.extend(routing_evidence_issues(plan, task, receipt))
    _verified_json(plan["environment"]["source_catalog"])
    requests = {event["payload"]["id"]: event["payload"] for event in events if event["kind"] == "ArxivVersionResolutionRequested"}
    finished = [event["payload"] for event in events if event["kind"] == "ArxivVersionResolutionFinished"]
    require(len(requests) == sum(event["kind"] == "ArxivVersionResolutionRequested" for event in events), "DUPLICATE_VERSION_REQUEST_ID")
    require(len(finished) == len(requests) and {row["id"] for row in finished} == set(requests), "VERSION_REQUEST_COMPLETION_MISMATCH")
    version_refs = {}
    for row in finished:
        require(requests.get(row["id"], {}).get("requested_id") == row["requested_id"], "VERSION_REQUEST_IDENTITY_MISMATCH")
        require(row["requested_id"] not in version_refs, "VERSION_REQUEST_REPEATED")
        version_refs[row["requested_id"]] = row["receipt"]
    require(version_refs == state.get("version_resolutions", {}), "VERSION_RECEIPT_CHECKPOINT_MISMATCH")
    initial = plan["environment"].get("initial_version_resolution")
    require(len(requests) + int(initial is not None) <= plan["environment"].get("max_identity_requests", 0), "VERSION_REQUEST_QUOTA_EXCEEDED")
    version_inputs = [(requested, ref, False) for requested, ref in version_refs.items()]
    if initial:
        version_inputs.append((_verified_json(initial)["requested_id"], initial, True))
    for requested, ref, is_query in version_inputs:
        value = _verified_json(ref)
        require(value["requested_id"] == requested, "VERSION_RECEIPT_REQUEST_MISMATCH")
        if value.get("response"):
            response = value["response"]
            raw = pathlib.Path(response["path"]).read_bytes()
            require(digest(raw) == response["sha256"] and len(raw) == response["byte_size"], "VERSION_RESPONSE_BYTES_MISMATCH")
            if value.get("resolved"):
                require(parse_version(raw, requested) == value["resolved"], "VERSION_METADATA_PARSE_MISMATCH")
        if value.get("resolved"):
            require(value.get("response") is not None and value["status"] == "VERSION_PINNED_FROM_METADATA", "VERSION_METADATA_EVIDENCE_ABSENT")
        if is_query:
            require((value.get("resolved") or {}).get("paper_id") == plan["paper_id"], "QUERY_VERSION_METADATA_MISMATCH")
    for entry in plan["environment"]["evidence_imports"]["candidates"].values():
        for ref in entry.values():
            _verified_json(ref)
    for entry in plan["environment"]["evidence_imports"]["matches"]:
        _verified_json(entry["response"])
    for ref in plan["environment"]["evidence_imports"].get("extraction_batches", {}).values():
        _verified_json(ref)
    bindings = [event["payload"] for event in events if event["kind"] == "QuerySelectorBound"]
    if state["query_binding"] is None:
        # A failed seed extraction still has auditable source bytes, quota and
        # receipts. No query/graph exists, so do not fabricate a successful walk.
        require(not bindings and not state["papers"] and not state.get("pdf_sources")
                and not state.get("pdf_match_attempts") and not (run / "pdf-matches").exists()
                and state["assembly"] is None and state["graph"] is None,
                "FAILED_QUERY_HAS_GRAPH_OR_BOUND_CANDIDATES")
        require(state["controller_status"] in {"QUERY_EXTRACTION_FAILED", "MODEL_PROVIDER_CIRCUIT_OPEN"} and state["phase"] == "READY",
                "UNBOUND_QUERY_FAILURE_STATE_MISMATCH")
        source_directory = run / "papers" / plan["paper_id"].replace(":", "-").replace("/", "-")
        paper = json.loads((source_directory / "extraction.json").read_bytes())
        _frozen_source_payload(paper, source_directory, source_directory=source_directory)
        require(paper["paper"]["id"] == plan["paper_id"] and
                paper["paper"]["source_sha256"] == plan["source_sha256"], "FAILED_QUERY_SOURCE_IDENTITY_MISMATCH")
        for _, _, encoded in calls:
            receipt = json.loads(encoded) if encoded else {}
            directory = pathlib.Path(receipt.get("directory", ""))
            require(json.loads((directory / "receipt.json").read_bytes()) == receipt, "FAILED_QUERY_CALL_RECEIPT_MISMATCH")
            require(digest((directory / "prompt.txt").read_bytes()) == receipt["request_sha256"] and
                    digest((directory / "events.jsonl").read_bytes()) == receipt["events_sha256"],
                    "FAILED_QUERY_CALL_BYTES_MISMATCH")
        snapshots = sorted((run / "checkpoints").glob("*.json"))
        require(bool(snapshots) and json.loads(snapshots[-1].read_bytes()) == state, "LATEST_CHECKPOINT_MISMATCH")
        return {"kind": "RecursiveResearchArtifactAudit", "created_at": utcnow(), "run": str(run),
                "status": "PASS" if not issues else "FAILED", "issues": issues,
                "input_projection_references": projection_refs,
                "immutable_checkpoint_reference": reference(snapshots[-1]) if snapshots else None,
                "scope": "FAILED_QUERY_SOURCE_BYTES_SQLITE_QUOTA_AND_MODEL_RECEIPTS_NO_QUERY_GRAPH",
                "controller_result": state["controller_status"], "paper_assemblies": 0,
                "graph_snapshots": 0, "model_calls": len(calls), "accepted_support_edges": 0,
                "mathematical_status": "CHAIN_INCOMPLETE", "semantic_completeness_checked": False}
    require(bindings == [state["query_binding"]], "QUERY_BINDING_EVENT_MISMATCH")
    selector = plan["environment"]["query_selector"]
    require(state["query_binding"]["selector"] == selector and selector["paper_id"] == plan["paper_id"],
            "FROZEN_QUERY_SELECTOR_MISMATCH")
    sources, originals = {}, {}
    for paper_id, entry in state["papers"].items():
        paper = _verified_json(entry["extraction"])
        recorded = _verified_graph_json(entry["assembly"])
        provenance = _verified_json(entry["provenance"])
        full = _frozen_source_payload(paper, pathlib.Path(entry["directory"]), source_directory=pathlib.Path(entry["directory"]))
        if provenance.get("kind") == "LIVE_MODEL_OUTPUT_BATCHES":
            dispatch = _verified_json(provenance["dispatch"])
            require(dispatch.get("reuse_dispatch") == plan["environment"]["evidence_imports"].get("extraction_batches", {}).get(paper_id),
                    "BATCH_REUSE_DIFFERS_FROM_FROZEN_PLAN")
            issues.extend(audit_batch_dispatch(provenance, paper, full, {row[0] for row in calls}))
        response = _verified_json(recorded["response_reference"])
        rebuilt = assemble_candidates(paper, response.get("candidate", response), full, response_reference=recorded["response_reference"],
                                      claim_reference_policy=plan["environment"].get("claim_reference_policy"))
        require(rebuilt == recorded and rebuilt["paper_id"] == paper_id, "PAPER_ASSEMBLY_RECONSTRUCTION_MISMATCH")
        sources[paper_id], originals[paper_id] = full, rebuilt
        if paper_id == plan["paper_id"]:
            require(paper["paper"]["source_sha256"] == plan["source_sha256"], "QUERY_SOURCE_HASH_MISMATCH")
            require(state["query_binding"]["source_assembly"] == entry["assembly"] and
                    state["query_binding"]["query_ids"] == bind_query(selector, paper, rebuilt), "QUERY_ASSEMBLY_BINDING_MISMATCH")
    def decorated(assembly):
        assembly = copy.deepcopy(assembly)
        if plan["decision_policy"] == "CANDIDATE_EXPLORATION":
            for node in assembly["nodes"]:
                node["blocked_by"] = sorted(set(node.get("blocked_by", [])) | {"CANDIDATE_EXPLORATION_REVIEW_REQUIRED"})
        apply_review_blocks(assembly, plan["environment"]["evidence_imports"].get("review_blocks", []))
        apply_source_availability(assembly, plan["environment"]["evidence_imports"].get("source_availability", []))
        apply_dependency_gaps(assembly, plan["environment"]["evidence_imports"].get("dependency_gaps", []))
        return apply_source_corrections(assembly, plan["environment"]["evidence_imports"].get("source_corrections", []))
    seed = decorated({**originals[plan["paper_id"]], "query_ids": state["query_binding"]["query_ids"]})
    expected = {digest(canonical(seed)): seed}
    joins = []
    for path in sorted((run / "matches").glob("*/provenance.json")):
        provenance = json.loads(path.read_bytes())
        refs = provenance["inputs"]
        inputs = {key: (_verified_graph_json(ref) if key in {"base", "upstream"} else _verified_json(ref))
                  for key, ref in refs.items()}
        for origin in provenance["origins"]:
            if origin.get("reference"):
                _verified_json(origin["reference"])
            if origin.get("kind") == "PARTIAL_MODEL_MATCH_ROWS":
                selection = _verified_json(origin["reference"])
                receipt = selection["original_receipt"]
                require(receipt == origin["receipt"] and receipt["error"] == "MODEL_CANDIDATE_VALIDATION_FAILED",
                        "PARTIAL_MATCH_RECEIPT_MISMATCH")
                raw = pathlib.Path(receipt["directory"]) / "response.json"
                require(digest(raw.read_bytes()) == receipt["response_sha256"], "PARTIAL_MATCH_RESPONSE_CHANGED")
                original = json.loads(raw.read_bytes())["matches"]
                bad = {issue["row"] for issue in receipt["validation_issues"]}
                require(all(issue["code"] in {"MODEL_SOURCE_LOCATOR_INVALID", "MODEL_SOURCE_LOCATOR_NOT_UNIQUE",
                            "MATCH_SUPPORT_QUOTATION_ABSENT"} for issue in receipt["validation_issues"]),
                        "PARTIAL_MATCH_NONLOCAL_FAILURE")
                selected = [i for i in range(len(original)) if i not in bad]
                require(selection["selected_row_indices"] == selected and selection["rejected_row_indices"] == sorted(bad)
                        and selection["matches"] == [original[i] for i in selected], "PARTIAL_MATCH_SELECTION_CHANGED")
                require(all(row in inputs["matches"]["matches"] for row in selection["matches"]),
                        "PARTIAL_MATCH_ROWS_NOT_JOINED")
        upstream = inputs["upstream"]["paper_id"]
        require(inputs["upstream"] == originals[upstream], "JOIN_UPSTREAM_ASSEMBLY_MISMATCH")
        output = join_candidate_paper(inputs["base"], inputs["upstream"], inputs["matches"], sources[upstream],
            matches_reference=refs["matches"], resolve_explicit_occurrences=plan["environment"].get("source_join_policy") ==
            "EXPLICIT_CLAIM_IDS_DISAMBIGUATE_OCCURRENCES_V1")
        assembly = decorated(output["assembly"])
        key = digest(canonical(assembly))
        expected[key] = assembly
        joins.append({"base": refs["base"]["sha256"], "output": key})
    pdf_transitions = []
    if (state.get("pdf_sources") or state.get("pdf_match_attempts") or (run / "pdf-matches").exists()
            or any(event["kind"] == "RetainedPDFAdmitted" for event in events)):
        from audit_pdf_research import reconstruct_pdf_research
        pdf_transitions = reconstruct_pdf_research(run, plan, state, events, calls, call_start_times, admissions, decorated)
        for transition in pdf_transitions:
            if transition["output"] is not None:
                expected[transition["output"]] = transition["assembly"]
                joins.append({key: transition[key] for key in ("base", "output")})
    reachable = {digest(canonical(seed))}
    while True:
        enlarged = reachable | {row["output"] for row in joins if row["base"] in reachable}
        if enlarged == reachable:
            break
        reachable = enlarged
    require(set(expected) == reachable, "JOIN_HISTORY_HAS_UNRECONSTRUCTED_BASE")
    require(all(row["base"] in reachable for row in pdf_transitions), "PDF_ATTEMPT_BASE_NOT_RECONSTRUCTED")
    graph_hashes = set()
    snapshots = sorted((run / "checkpoints").glob("*.json"))
    require(bool(snapshots) and json.loads(snapshots[-1].read_bytes()) == state, "LATEST_CHECKPOINT_MISMATCH")
    for path in snapshots:
        checkpoint = json.loads(path.read_bytes())
        require(checkpoint["plan_id"] == pid, "CHECKPOINT_PLAN_MISMATCH")
        if not checkpoint["assembly"]:
            continue
        assembly, graph = _verified_graph_json(checkpoint["assembly"]), _verified_graph_json(checkpoint["graph"])
        require(checkpoint["assembly"]["sha256"] in reachable and expected.get(checkpoint["assembly"]["sha256"]) == assembly,
                "CHECKPOINT_ASSEMBLY_NOT_RECONSTRUCTED")
        require(select_candidate_graph(assembly) == graph, "GRAPH_RECONSTRUCTION_MISMATCH")
        require(assembly["query_ids"] == state["query_binding"]["query_ids"], "QUERY_IDS_CHANGED_DURING_RECURSION")
        graph_hashes.add(checkpoint["graph"]["sha256"])
    require(state["phase"] == "READY", "CONTROLLER_NOT_QUIESCENT")
    return {"kind": "RecursiveResearchArtifactAudit", "created_at": utcnow(), "run": str(run),
            "status": "PASS" if not issues else "FAILED", "issues": issues,
            "input_projection_references": projection_refs,
            "immutable_checkpoint_reference": reference(snapshots[-1]) if snapshots else None,
            "scope": "FROZEN_PLAN_SQLITE_PROJECTIONS_SOURCE_BYTES_CANDIDATES_QUERY_BINDING_JOIN_AND_GRAPH_RECONSTRUCTION",
            "paper_assemblies": len(originals), "recursive_joins": len(joins), "graph_snapshots": len(graph_hashes),
            **({"pdf_attempts_reconstructed": len(pdf_transitions),
                "pdf_failure_or_interruption_reconstruction_supported": False} if pdf_transitions else {}),
            "admitted_papers_including_query": admitted, "model_calls": len(calls),
            "version_metadata_requests": len(requests) + int(initial is not None),
            "accepted_support_edges": accepted_support_edges(_verified_graph_json(state["graph"]) if state["graph"] else None),
            "mathematical_status": "CHAIN_INCOMPLETE",
            "semantic_completeness_checked": False, "concurrency_or_crash_recovery_exercised": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a fresh audit output")
    try:
        report = audit(args.run)
    except Exception as error:
        report = {"kind": "RecursiveResearchArtifactAudit", "status": "FAILED", "error": str(error),
                  "mathematical_status": "CHAIN_INCOMPLETE", "run": str(args.run.resolve())}
    write_json(args.output, report)
    print(json.dumps({key: value for key, value in report.items() if key not in {"issues", "scope", "run"}}))
    raise SystemExit(0 if report["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
