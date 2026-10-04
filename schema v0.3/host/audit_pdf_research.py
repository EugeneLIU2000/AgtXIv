"""Bind completed PDF attempts to one recursive ledger and checkpoint history.

Failed or interrupted attempts are deliberately rejected until their failure
reconstruction exists. No attempt, judgement or model call may be omitted to PASS.
"""
import json
from datetime import datetime
from pathlib import Path

from audit_pdf_match import reconstruct_pdf_match
from candidates import select_candidate_graph
from core import canonical, digest
from recursive_graph import _verified_graph_json, _verified_json
from scheduler import Frontier


def reconstruct_pdf_research(run, plan, state, events, calls, call_start_times, admissions, decorated):
    run = Path(run).resolve()
    refs = state.get("pdf_match_attempts", [])
    sources = state.get("pdf_sources", {})
    paths = [Path(ref["path"]).resolve() for ref in refs]
    dirs = {path.resolve() for path in (run / "pdf-matches").glob("*") if path.is_dir()}
    if len(paths) != len(set(paths)) or {path.parent for path in paths} != dirs or any(
            path.name != "summary.json" or path.parent.parent != run / "pdf-matches" for path in paths):
        raise ValueError("PDF_RESEARCH_ATTEMPT_INVENTORY_MISMATCH")
    catalog, targets = {}, {}
    for ref in plan["environment"]["evidence_imports"].get("pdf_sources", []):
        binding = _verified_json(ref)
        if binding.get("kind") != "RetainedPDFSourceBinding":
            raise ValueError("PDF_RESEARCH_SOURCE_BINDING_KIND_INVALID")
        entry = {"pdf_run": binding["pdf_run"]}
        pid = binding["paper_id"]
        if pid in catalog and catalog[pid] != entry:
            raise ValueError("PDF_RESEARCH_SOURCE_BINDING_CONFLICT")
        catalog[pid] = entry
        for request in binding["requests"]:
            if request["id"] in targets:
                raise ValueError("PDF_RESEARCH_REQUEST_BINDING_DUPLICATE")
            targets[request["id"]] = (pid, request)
    admitted_events = [event["payload"] for event in events if event["kind"] == "RetainedPDFAdmitted"]
    by_paper = {item["paper_id"]: item for item in admitted_events}
    pdf_admissions = {pid: value for pid, value in admissions.items()
                      if (value.get("evidence") or {}).get("admission_kind") == "RETAINED_PDF_SOURCE"}
    if (len(by_paper) != len(admitted_events) or set(by_paper) != set(sources)
            or set(pdf_admissions) != set(sources)):
        raise ValueError("PDF_RESEARCH_ADMISSION_INVENTORY_MISMATCH")
    for pid, entry in sources.items():
        event, admission = by_paper[pid], pdf_admissions[pid]
        evidence = admission["evidence"]
        if (entry != catalog.get(pid) or evidence.get("pdf_run") != entry["pdf_run"]
                or event.get("admission_evidence") != evidence or event.get("admitted") is not True
                or event.get("reused") is not False or admission["admitted"] != 1
                or admission["state"] != "RECORDED" or admission["claim_token"] is not None
                or plan["decision_policy"] != "CANDIDATE_EXPLORATION"):
            raise ValueError("PDF_RESEARCH_SOURCE_NOT_BOUND_TO_ADMISSION")
    checkpoints = [json.loads(path.read_bytes()) for path in sorted((run / "checkpoints").glob("*.json"))]
    call_rows = {row[0]: (row[1], json.loads(row[2]) if row[2] else None) for row in calls}
    owned_calls = {cid for cid, (_, receipt) in call_rows.items() if receipt and
                   run / "pdf-matches" in Path(receipt["directory"]).resolve().parents}
    used_calls, visited_papers, all_outcomes, transitions, attempted = set(), set(), [], [], []
    for ref, path in zip(refs, paths):
        checked = reconstruct_pdf_match(ref)
        inputs, receipt = checked["inputs"], checked["receipt"]
        cid, upstream = receipt["call_id"], inputs["upstream_paper_id"]
        if (checked["plan"] != plan or cid in used_calls
                or call_rows.get(cid) != ("RECORDED", receipt)
                or receipt.get("operation") != "dependency.match"):
            raise ValueError("PDF_RESEARCH_CALL_NOT_UNIQUELY_OWNED_BY_PLAN")
        used_calls.add(cid)
        if sources.get(upstream) != {"pdf_run": inputs["upstream_pdf_run"]}:
            raise ValueError("PDF_RESEARCH_UPSTREAM_NOT_ADMITTED")
        busy = [(i, checkpoint) for i, checkpoint in enumerate(checkpoints)
                if checkpoint.get("phase") == "BUSY" and
                checkpoint.get("inflight", {}).get("operation") == "dependency.match.pdf" and
                checkpoint["inflight"].get("directory") == str(path.parent)]
        if len(busy) != 1 or busy[0][0] + 1 >= len(checkpoints):
            raise ValueError("PDF_RESEARCH_ATTEMPT_CHECKPOINT_PAIR_MISSING")
        index, before = busy[0]
        after = checkpoints[index + 1]
        work = before["inflight"]
        down = work["downstream_paper_id"]
        if (work["upstream_paper_id"] != upstream or work["request_ids"] != inputs["request_ids"]
                or before["assembly"] != inputs["base_assembly"] or after["phase"] != "READY"
                or after.get("inflight") is not None
                or after.get("pdf_match_attempts") != before.get("pdf_match_attempts", []) + [ref]
                or before.get("pdf_sources", {}).get(upstream) != sources[upstream]):
            raise ValueError("PDF_RESEARCH_ATTEMPT_CHECKPOINT_BINDING_MISMATCH")
        for paper in {upstream, down} & sources.keys():
            if datetime.fromisoformat(admissions[paper]["updated"]) > datetime.fromisoformat(call_start_times[cid]):
                raise ValueError("PDF_RESEARCH_CALL_PRECEDES_PAPER_ADMISSION")
        pairs = [[ident, upstream] for ident in inputs["request_ids"]]
        if any(pair in before["attempted_matches"] or pair in attempted for pair in pairs):
            raise ValueError("PDF_RESEARCH_COMPLETED_SCOPE_REPEATED")
        attempted.extend(pairs)
        down_source = sources.get(down)
        if down_source is None:
            entry = before["papers"].get(down)
            down_source = {key: entry[key] for key in ("extraction", "directory")} if entry else None
        if down_source != inputs["downstream_source"]:
            raise ValueError("PDF_RESEARCH_DOWNSTREAM_CONTEXT_MISMATCH")
        base = _verified_graph_json(inputs["base_assembly"])
        graph = select_candidate_graph(base)
        request_map = {row["id"]: row for row in base["dependency_requests"]}
        for ident in inputs["request_ids"]:
            request = request_map[ident]
            lead = {"upstream_node_id": ident, "downstream_node_id": request["downstream_node_id"]}
            if targets.get(ident) != (upstream, request) or not Frontier._load_bearing(lead, graph):
                raise ValueError("PDF_RESEARCH_REQUEST_NOT_FROZEN_OR_LOAD_BEARING")
        if upstream not in visited_papers:
            evidence = pdf_admissions[upstream]["evidence"]
            if not Frontier._load_bearing(evidence, graph):
                raise ValueError("PDF_RESEARCH_ADMISSION_GRAPH_BINDING_CHANGED")
            visited_papers.add(upstream)
        joined = checked["joined"]
        published = after["assembly"] != before["assembly"]
        key, assembly = None, None
        if published:
            if joined is None:
                raise ValueError("PDF_RESEARCH_NON_SUPPORT_PUBLISHED_GRAPH")
            assembly = decorated(joined["assembly"])
            key = digest(canonical(assembly))
            if (_verified_graph_json(after["assembly"]) != assembly
                    or _verified_graph_json(after["graph"]) != select_candidate_graph(assembly)):
                raise ValueError("PDF_RESEARCH_PUBLISHED_GRAPH_NOT_RECONSTRUCTED")
        elif after["graph"] != before["graph"]:
            raise ValueError("PDF_RESEARCH_GRAPH_CHANGED_WITHOUT_ASSEMBLY")
        outcomes = [{**row, "pdf_attempt": ref,
                     "research_graph_published": published and row.get("relation") == "CANDIDATE_SUPPORT"}
                    for row in checked["outcomes"]]
        if (after["match_outcomes"] != before["match_outcomes"] + outcomes
                or after["attempted_matches"] != before["attempted_matches"] +
                [[ident, upstream] for ident in inputs["request_ids"]]):
            raise ValueError("PDF_RESEARCH_ATTEMPT_OUTCOMES_CHANGED")
        all_outcomes.extend(outcomes)
        transitions.append({"base": inputs["base_assembly"]["sha256"], "output": key,
                            "assembly": assembly})
    if used_calls != owned_calls or visited_papers != set(sources):
        raise ValueError("PDF_RESEARCH_CALL_OR_SOURCE_OMITTED")
    if [row for row in state["match_outcomes"] if "pdf_attempt" in row] != all_outcomes:
        raise ValueError("PDF_RESEARCH_FINAL_OUTCOMES_OMITTED_OR_CHANGED")
    if [pair for pair in state["attempted_matches"] if pair[1] in sources] != attempted:
        raise ValueError("PDF_RESEARCH_FINAL_ATTEMPTED_SCOPE_CHANGED")
    if any(row.get("status") == "PDF_DISPATCH_FAILED_BEFORE_SUMMARY" for row in state["match_outcomes"]):
        raise ValueError("PDF_RESEARCH_UNRECONSTRUCTED_DISPATCH_FAILURE")
    return transitions
