"""Query selection, frozen policies, honest summary and failure classification in research.py."""
import copy
import json
import pathlib
import types

import pytest
from jsonschema import Draft202012Validator

import research
from candidates import CLAIM_REFERENCE_POLICY
from core import VERSION, PlanLedger, write_json
from model import SourcePayloadError

PID = "arxiv:2101.00002v1"
SCHEMA = json.loads((pathlib.Path(research.__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
LABELS = {"thm:a": [{"source": {"path": "main.tex", "byte_start": 10, "byte_end": 20}, "claim_ids": ["occ:A"]}],
          "thm:b": [{"source": {"path": "main.tex", "byte_start": 105, "byte_end": 115}, "claim_ids": []}],
          "eq:none": [{"source": {"path": "main.tex", "byte_start": 900, "byte_end": 910}, "claim_ids": []}]}
BIBLIOGRAPHY = [{"id": "bib:arxiv", "identifiers": {"arxiv": ["2001.00001"], "doi": ["10.1/a"]}},
                {"id": "bib:doi", "entry_type": "article", "identifiers": {"arxiv": [], "doi": ["10.1/b"]}},
                {"id": "bib:book", "entry_type": "book", "identifiers": {"arxiv": [], "doi": ["10.1/c"]}},
                {"id": "bib:text", "identifiers": {"arxiv": [], "doi": []}}]
PAPER = {"paper": {"id": PID, "source_sha256": "sha256:src"}, "source_files": [{"path": "main.tex"}],
         "claims": [], "labels": LABELS, "bibliography": BIBLIOGRAPHY}


def claim(name, occurrences, start):
    return {"id": "claim:" + name, "kind": "theorem", "paper_id": PID, "source_occurrence_ids": occurrences,
            "source_spans": [{"path": "main.tex", "byte_start": start, "byte_end": start + 100}],
            "disposition": "AGENT_NORMALIZED_UNREVIEWED", "blocked_by": [], "upstream_search": "FRONTIER"}


def request(name, target, bib):
    node = {"id": "request:" + name, "kind": "external_claim_request", "paper_id": None, "source_spans": [],
            "disposition": "UNREVIEWED", "blocked_by": ["EXTERNAL:" + name], "upstream_search": "FRONTIER"}
    row = {"id": node["id"], "request_kind": "external_claim_request", "from_paper_id": PID,
           "downstream_node_id": "claim:" + target, "citation_key": name,
           "bibliography": [{"id": bib, "identifiers": next(r["identifiers"] for r in BIBLIOGRAPHY if r["id"] == bib)}]}
    return node, row


REQUESTS = [request("r1", "A", "bib:arxiv"), request("r2", "A", "bib:doi"),
            request("r3", "B", "bib:book"), request("r4", "C", "bib:text")]
# r1 is matched by a signed group (resolved); r2 only by an unreviewed candidate match (still open).
ASSEMBLY = {"kind": "CandidateGraphAssembly", "paper_id": PID,
            "nodes": [claim("A", ["occ:A"], 0), claim("B", [], 100), claim("C", ["occ:C"], 300), claim("U", [], 0),
                      claim("W", ["occ:bundle"], 0)]  # W's larger occurrence also contains thm:a's byte
                     + [n for n, _ in REQUESTS],
            "support_groups": [{"id": "g:" + t, "target": t, "members": m, "relation": "PROOF_DEPENDENCY",
                                "disposition": d} for t, m, d in
                               (("claim:A", ["request:r1", "request:r2"], "UNREVIEWED"), ("claim:B", ["request:r3"], "UNREVIEWED"),
                                ("claim:C", ["request:r4"], "UNREVIEWED"), ("request:r1", ["claim:U"], "SOURCE_FROZEN_HUMAN_SIGNED"),
                                ("request:r2", ["claim:U"], "UNREVIEWED"))],
            "query_ids": ["claim:A", "claim:B", "claim:C", "claim:W"], "dependency_requests": [r for _, r in REQUESTS],
            "coverage": {"candidate_covered_occurrences": 2, "new_exact_locator_count": 0},
            "all_judgements_unreviewed": True}


def labels(*names):
    return {"kind": "SOURCE_LABELS", "paper_id": PID, "labels": list(names)}


def test_bind_query_selectors():
    assert research.bind_query({"kind": "ALL_EXTRACTED_MATH_CLAIMS", "paper_id": PID}, PAPER, ASSEMBLY) == ASSEMBLY["query_ids"]
    assert research.bind_query(labels("thm:a"), PAPER, ASSEMBLY) == ["claim:A"]  # recorded occurrence; W not by byte
    assert research.bind_query(labels("thm:b"), PAPER, ASSEMBLY) == ["claim:B"]  # no occurrence: label byte in span
    assert research.bind_query(labels("thm:b", "thm:a"), PAPER, ASSEMBLY) == ["claim:A", "claim:B"]
    with pytest.raises(ValueError, match="QUERY_LABEL_UNMATCHED: eq:none, absent$"):
        research.bind_query(labels("thm:a", "eq:none", "absent"), PAPER, ASSEMBLY)


def test_terminal_kind_and_accepted_edges():
    bibliography = {row["id"]: row for row in BIBLIOGRAPHY}
    assert [research.terminal_kind(row, bibliography) for _, row in REQUESTS] == [
        "ARXIV_SOURCE_AVAILABLE", "PREARXIV_DOI_NO_SOURCE", "MONOGRAPH", "FREE_TEXT_UNRESOLVED"]
    assert research.terminal_kind({"bibliography": []}, {}) == "FREE_TEXT_UNRESOLVED"
    groups = [{"disposition": "SOURCE_FROZEN_HUMAN_SIGNED"}, {"disposition": "UNREVIEWED"}]
    assert research.accepted_support_edges({"support_groups": groups}) == 1
    assert research.accepted_support_edges(None) == 0


def controller(tmp_path, monkeypatch, selector, read_error=None, extract_result=None, batch_receipts=None, no_progress_limit=2):
    run = tmp_path / "run"
    plan = {"contract_version": VERSION, "plan_id": "plan:test", "paper_id": PID, "query_ids": [], "created_at": "t",
            "cost_mode": "ACCOUNT_QUOTA", "decision_policy": "CANDIDATE_EXPLORATION",
            "limits": {"max_papers": 2, "max_model_calls": 1, "max_call_seconds": 1, "max_cost_microusd": 0,
                       "no_progress_limit": no_progress_limit, "max_node_attempts": 1},  # no_progress_limit=1 replaces the reason
            "source_sha256": "sha256:src",
            "environment": {"mode": "RECURSIVE_RESEARCH", "query_selector": selector,
                            "claim_reference_policy": CLAIM_REFERENCE_POLICY, "network_sources": False,
                            "extract_focus_bytes": 8192 if batch_receipts else 0, "max_extract_batches": 4, "runtime_sources": [],
                            "evidence_imports": {"candidates": {}, "matches": [], "extraction_batches": {}},
                            "source_catalog": write_json(tmp_path / "catalog.json", {})}}
    policies = []

    def assemble(paper, candidate, sources, *, response_reference, claim_reference_policy=None):
        policies.append(claim_reference_policy)
        return copy.deepcopy(ASSEMBLY)

    def extract(ledger, paper, output, source_directory):
        if isinstance(extract_result, Exception):
            raise extract_result
        return extract_result or {"candidate": {"claims": []}, "receipt": {"directory": str(output)}}

    def batches(ledger, paper, directory, **kwargs):
        rows = [{"id": str(n), "status": "FAILED", "result": write_json(directory / f"{n}.json", {"candidate": None, "receipt": r})}
                for n, r in enumerate(batch_receipts)] + [{"id": "rest", "status": "NOT_DISPATCHED"}]
        return {"candidate": None, "dispatch": write_json(directory / "dispatch.json", {"scopes": rows}),
                "error": "NO_SUCCESSFUL_BATCH_RESPONSE"}

    monkeypatch.setattr(research, "assemble_candidates", assemble)
    monkeypatch.setattr(research, "extract_candidate_batches", batches)
    monkeypatch.setattr(research, "extract_candidates", extract)
    result = research.ResearchController(tmp_path, run, PlanLedger(run, plan))
    directory = result.paper_directory(PID)
    write_json(directory / "extraction.json", PAPER)
    write_json(directory / "model/response.json", {"candidate": {"claims": []}})

    def read_paper(pid):
        if read_error:
            raise read_error
        return PAPER, {}, directory
    result.read_paper = read_paper
    return result, policies


def test_label_query_prunes_graph_and_summary_is_computed(tmp_path, monkeypatch):
    ctl, policies = controller(tmp_path, monkeypatch, labels("thm:a"))
    summary = ctl.run()
    assert policies == [CLAIM_REFERENCE_POLICY]
    assert ctl.state["query_binding"]["query_ids"] == ["claim:A"]
    graph = research._verified_graph_json(ctl.state["graph"])
    assert sorted(graph["selected_node_ids"]) == ["claim:A", "claim:U", "request:r1", "request:r2"]
    assert research._verified_graph_json(ctl.state["papers"][PID]["assembly"])["query_ids"] == ASSEMBLY["query_ids"]
    ctl.validate_query_binding()
    assert summary["query_candidates"] == 1 and summary["accepted_support_edges"] == 1
    assert summary["proof_backend"] == "SEPARATE_STAGE_PROOF_WALK"
    assert summary["frontier_terminal_kinds"] == {"PREARXIV_DOI_NO_SOURCE": 1}  # r2's unreviewed match resolves nothing


def test_all_claims_selector_keeps_legacy_scope(tmp_path, monkeypatch):
    ctl, _ = controller(tmp_path, monkeypatch, {"kind": "ALL_EXTRACTED_MATH_CLAIMS", "paper_id": PID})
    summary = ctl.run()
    assert ctl.state["query_binding"]["query_ids"] == ASSEMBLY["query_ids"]
    assert summary["frontier_terminal_kinds"] == {"FREE_TEXT_UNRESOLVED": 1, "MONOGRAPH": 1, "PREARXIV_DOI_NO_SOURCE": 1}


def frontier_reason(ctl):
    return next(row for row in ctl.frontier.snapshot()["papers"] if row["paper_id"] == PID)["reason"]


def test_unmatched_label_is_a_hard_query_failure(tmp_path, monkeypatch):
    ctl, _ = controller(tmp_path, monkeypatch, labels("thm:a", "eq:none"))
    assert ctl.run()["controller_status"] == "QUERY_EXTRACTION_FAILED"
    assert ctl.state["query_binding"] is None and ctl.state["graph"] is None and not ctl.state["papers"]
    issue = next(row for row in ctl.ledger.snapshot()["issues"] if row["code"] == "RESEARCH_PAPER_FAILED")
    assert issue["detail"] == "QUERY_LABEL_UNMATCHED: eq:none"
    assert frontier_reason(ctl) == "HOST_PROCESSING_FAILED"


@pytest.mark.parametrize("read_error, extract_result, reason, exception", [
    (SourcePayloadError("MODEL_SOURCE_HASH_MISMATCH", "changed"), None, "SOURCE_READ_DEFECTIVE", "SourcePayloadError"),
    (ValueError("SOURCE_READ_DEFECTIVE: absent frozen versioned source"), None, "SOURCE_READ_DEFECTIVE", "ValueError"),
    (ValueError("SOURCE_UNREACHABLE: no registered source"), None, "SOURCE_UNREACHABLE", "ValueError"),
    (KeyError("paper"), None, "HOST_PROCESSING_FAILED", "KeyError"),
    (None, TypeError("bad host call"), "HOST_PROCESSING_FAILED", "TypeError"),
    (None, {"candidate": None, "receipt": {"operation": "paper.extract.preflight", "error": "MODEL_INPUT_LIMIT_EXCEEDED"}},
     "SOURCE_READ_DEFECTIVE", "SourcePayloadError"),  # model.extract_candidates' real preflight return
    (None, {"candidate": None, "receipt": {"operation": "paper.extract", "error": "MODEL_TIMEOUT"}},
     "HOST_PROCESSING_FAILED", "ValueError"),
])
def test_failure_classification(tmp_path, monkeypatch, read_error, extract_result, reason, exception):
    ctl, _ = controller(tmp_path, monkeypatch, labels("thm:a"), read_error, extract_result)
    assert ctl.run()["controller_status"] == "QUERY_EXTRACTION_FAILED"
    assert frontier_reason(ctl) == reason
    issue = next(row for row in ctl.ledger.snapshot()["issues"] if row["code"] == "RESEARCH_PAPER_FAILED")
    assert issue["evidence"] == {"failure_reason": reason, "exception_type": exception}


def test_no_progress_limit_keeps_the_failure_classification(tmp_path, monkeypatch):
    ctl, _ = controller(tmp_path, monkeypatch, labels("thm:a"), KeyError("paper"), no_progress_limit=1)
    ctl.run()
    assert frontier_reason(ctl) == "NO_PROGRESS_LIMIT"
    [event] = [row["payload"] for row in ctl.ledger.snapshot()["events"] if row["kind"] == "FrontierRecorded"]
    assert (event["reason"], event["failure_reason"]) == ("NO_PROGRESS_LIMIT", "HOST_PROCESSING_FAILED")


@pytest.mark.parametrize("operations, reason", [
    (["paper.extract.preflight", "paper.extract.preflight"], "SOURCE_READ_DEFECTIVE"),
    (["paper.extract.preflight", "paper.extract"], "HOST_PROCESSING_FAILED"),
])
def test_batch_failure_classification(tmp_path, monkeypatch, operations, reason):
    receipts = [{"operation": operation, "error": "MODEL_INPUT_CHARACTER_LIMIT_EXCEEDED"} for operation in operations]
    ctl, _ = controller(tmp_path, monkeypatch, labels("thm:a"), batch_receipts=receipts)
    assert ctl.run()["controller_status"] == "QUERY_EXTRACTION_FAILED"
    assert frontier_reason(ctl) == reason


def new_plan(tmp_path, monkeypatch, query_labels):
    host = tmp_path / "schema v0.3/host"
    host.mkdir(parents=True)
    (host / "stub.py").write_text("")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/extract_provisional_claims.py").write_text("")
    monkeypatch.setattr(research, "__file__", str(host / "research.py"))
    monkeypatch.setattr(research, "discover_sources", lambda repo: {PID: {"artifact": "main.tex"}})
    monkeypatch.setattr(research, "extract_paper", lambda *args, **kwargs: PAPER)
    monkeypatch.setattr(research, "_frozen_source_payload", lambda *args, **kwargs: {})
    monkeypatch.setattr(research, "ResearchController", lambda *args: types.SimpleNamespace(run=lambda: {}))
    args = types.SimpleNamespace(paper=PID, output=tmp_path / "run", imports=None, extraction_profile=None,
        max_papers=2, max_model_calls=0, max_match_requests=4, max_call_seconds=10, extract_focus_bytes=0,
        max_extract_batches=1, network_sources=False, max_identity_requests=0, candidate_exploration=True,
        resume=False, query_labels=query_labels)
    parser = types.SimpleNamespace(error=lambda message: (_ for _ in ()).throw(SystemExit(message)))
    with pytest.raises(SystemExit) as raised:
        research.execute(args, parser)
    return raised.value.code, tmp_path / "run/plan.json"


def test_new_plan_freezes_selector_and_policies(tmp_path, monkeypatch):
    code, path = new_plan(tmp_path, monkeypatch, ["thm:b", "thm:a", "thm:b"])
    plan = json.loads(path.read_bytes())
    assert code == 2
    assert plan["environment"]["query_selector"] == labels("thm:a", "thm:b")
    assert plan["environment"]["claim_reference_policy"] == CLAIM_REFERENCE_POLICY
    assert plan["environment"]["proof_backend"] == "SEPARATE_STAGE_PROOF_WALK"
    validator = Draft202012Validator({"$defs": SCHEMA["$defs"], "$ref": "#/$defs/Plan"})
    assert not list(validator.iter_errors(plan))
    legacy = copy.deepcopy(plan)
    legacy["environment"]["query_selector"] = {"kind": "ALL_EXTRACTED_MATH_CLAIMS", "paper_id": PID}
    del legacy["environment"]["claim_reference_policy"]
    assert not list(validator.iter_errors(legacy))
    legacy["environment"]["query_selector"]["labels"] = ["thm:a"]
    assert list(validator.iter_errors(legacy))


def test_new_plan_rejects_label_absent_from_source(tmp_path, monkeypatch):
    code, path = new_plan(tmp_path, monkeypatch, ["thm:missing"])
    assert "thm:missing" in code and not path.exists()
