"""Synthetic interface fixtures only: no retrieval, no historical cases, no writes, no model calls.

Unique basename on purpose: `test_interfaces.py` already exists in two sibling modules and the
tests directories carry no `__init__.py`, so that basename collides under pytest's default
import mode. The three files under `conformance/` are reused here rather than re-created.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location(
    "dependency_interfaces", Path(__file__).resolve().parents[1] / "check_interfaces.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

CONFORMANCE = m.DIRECTORY / "conformance"
HASH = "sha256:" + "a" * 64
OTHER_HASH = "sha256:" + "b" * 64
THIRD_HASH = "sha256:" + "c" * 64


def ref(name, suffix="one", content_hash=HASH, revision=1):
    return dict(record_type=f"agtxiv.v3.{name}/0.0.0", record_id=f"{name}:{suffix}",
                revision=revision, content_hash=content_hash)


def search_request(**overrides):
    request = dict(target_ref=ref("math-claim"), query="Leone/Stab_Renyi/2022",
                   sources=["Citing-paper bibliography; fetch in a separately budgeted task."])
    request.update(overrides)
    return request


def baseline(**payload_overrides):
    payload = dict(knowledge_ref=None, entry_refs=[], domain="stabilizer Renyi entropy of pure states",
                   selection_method="Only the bibliography entries in the supplied source spans.",
                   search_coverage="Two queries over the supplied spans; no external index was reached.",
                   limitations=["No knowledge-snapshot was supplied, so prior coverage is unknown."])
    payload.update(payload_overrides)
    return {"record_type": "agtxiv.v3.baseline-snapshot/0.0.0", "payload": payload}


def binding(**payload_overrides):
    payload = dict(dependent_ref=ref("math-claim"), prerequisite_ref=ref("math-claim", "upstream", OTHER_HASH),
                   kind="MATHEMATICAL", affected_axes=["mathematical_correctness"], proof_plan_ref=None,
                   comparison=[dict(dimension="ASSUMPTION", source_value="pure states only",
                                    target_value="all states", relation="SOURCE_STRONGER", witness_refs=[])],
                   reuse_decision_ref=None)
    payload.update(payload_overrides)
    return {"record_type": "agtxiv.v3.dependency-binding/0.0.0", "payload": payload}


def frontier(**payload_overrides):
    payload = dict(target_refs=[ref("math-claim")], kind="MISSING_SOURCE",
                   axes=["mathematical_correctness"],
                   statement="The cited upstream theorem is not available as a record.",
                   next_evidence="Fetch the cited work and extract its exact statement.",
                   attempt_refs=[], state="OPEN", resolution_refs=[])
    payload.update(payload_overrides)
    return {"record_type": "agtxiv.v3.frontier-item/0.0.0", "payload": payload}


def draft(**overrides):
    value = dict(draft_version="1.0", search_requests=[search_request()], records=[],
                 open_items=["target=math-claim:one; missing=upstream statement; checked=supplied spans;"
                             " next=fetch before any binding"],
                 follow_up_requests=[])
    value.update(overrides)
    return value


def task(value, operation="dependency.search", **overrides):
    refs = {m.contracts.ref_key(r): r for _, r in m.walk(value) if set(r) == m.REF_KEYS}
    claim = ref("math-claim")
    refs.setdefault(m.contracts.ref_key(claim), claim)
    supplied = dict(contract_version="0.1.0", task_id="dependency-synthetic", agent=operation.split(".")[0],
                    operation=operation,
                    brief="Bounded search for the cited upstream result; propose candidates only.",
                    target_refs=[claim], input_refs=deepcopy(list(refs.values())), input_artifacts=[],
                    depends_on=[],
                    expected_record_types=["baseline-snapshot", "dependency-binding", "frontier-item"],
                    limits=dict(max_attempts=1, max_seconds=60, max_cost_units=0, no_progress_limit=1),
                    acceptance="DELIVERY", exclusions=[],
                    capabilities=["records.read", "dependency.search", "candidates.propose"])
    supplied.update(overrides)
    return supplied


@pytest.fixture(scope="module")
def checker():
    return m.InterfaceChecker()


def rejected(checker, value, code, supplied_task=None):
    report = checker.check("search", value, supplied_task)
    assert not report["checks_passed"]
    assert code in {e["code"] for e in report["errors"]}, report
    return report


# --- the committed conformance fixtures -------------------------------------------------------

def fixture(name):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


def test_conformance_positive_fixture_passes(checker):
    report = checker.check("search", fixture("search-draft.json"))
    assert report["checks_passed"], report
    assert report["checked"] == ["schema", "search_interface_rules",
                                 "follow_up_agent_operation_pairs", "follow_up_input_refs_and_families"]


def test_conformance_duplicate_fixture_is_rejected(checker):
    report = rejected(checker, fixture("search-draft-duplicate.json"), "DUPLICATE_SEARCH")
    assert report["errors"][0]["path"] == "/search_requests/1"


def test_conformance_self_binding_fixture_is_rejected(checker):
    report = rejected(checker, fixture("search-draft-self-binding.json"), "DEPENDENT_IS_PREREQUISITE")
    assert report["errors"][0]["path"] == "/records/0/payload"


# --- positive and read-only -------------------------------------------------------------------

def test_positive_without_task_and_read_only(checker):
    value = draft(records=[baseline(), binding(), frontier()])
    before = deepcopy(value)
    report = checker.check("search", value)
    assert report["checks_passed"], report
    assert value == before
    assert "task" in report["unchecked"]


def test_positive_with_task_and_read_only(checker):
    value = draft(records=[baseline(), binding(), frontier()])
    supplied = task(value)
    before = deepcopy((value, supplied))
    report = checker.check("search", value, supplied)
    assert report["checks_passed"], report
    assert (value, supplied) == before
    assert "task" not in report["unchecked"]
    assert "task_exact_refs_and_declared_outputs" in report["checked"]


def test_unchecked_map_is_copied_per_report(checker):
    first = checker.check("search", draft())
    first["unchecked"]["injected"] = "must not leak"
    assert "injected" not in checker.check("search", draft())["unchecked"]


def test_every_declared_blind_spot_is_reported(checker):
    report = checker.check("search", draft())
    for key in ("retrieval_not_run", "baseline_content", "absence", "binding_semantics",
                "authorization", "record_conditionals"):
        assert key in report["unchecked"]


# --- search_requests rules --------------------------------------------------------------------

def test_empty_delivery_rejected(checker):
    rejected(checker, draft(search_requests=[], open_items=[]), "EMPTY_DELIVERY")
    rejected(checker, draft(search_requests=[], open_items=["   "]), "EMPTY_DELIVERY")
    assert checker.check("search", draft(search_requests=[], open_items=[
        "target=math-claim:one; missing=source bytes; checked=supplied inputs; next=utility.capture"
    ]))["checks_passed"]


def test_only_a_frontier_item_is_also_a_delivery(checker):
    assert checker.check("search", draft(search_requests=[], records=[frontier()],
                                         open_items=[]))["checks_passed"]


def test_duplicate_target_and_query_rejected(checker):
    value = draft(search_requests=[search_request(), search_request(sources=["another source list"])])
    rejected(checker, value, "DUPLICATE_SEARCH")


def test_duplicate_detection_ignores_surrounding_whitespace(checker):
    value = draft(search_requests=[search_request(), search_request(query="  Leone/Stab_Renyi/2022  ")])
    rejected(checker, value, "DUPLICATE_SEARCH")


def test_same_query_against_two_targets_is_not_a_duplicate(checker):
    value = draft(search_requests=[search_request(),
                                   search_request(target_ref=ref("math-claim", "two", OTHER_HASH))])
    assert checker.check("search", value)["checks_passed"]


def test_two_null_target_requests_with_the_same_query_are_duplicates(checker):
    value = draft(search_requests=[search_request(target_ref=None), search_request(target_ref=None)])
    rejected(checker, value, "DUPLICATE_SEARCH")


def test_source_level_request_may_omit_the_target(checker):
    value = draft(search_requests=[search_request(target_ref=None, query="stabilizer Renyi entropy zero")])
    assert checker.check("search", value)["checks_passed"]


# --- record rules -------------------------------------------------------------------------------

def test_self_binding_rejected(checker):
    value = draft(records=[binding(prerequisite_ref=ref("math-claim"))])
    rejected(checker, value, "DEPENDENT_IS_PREREQUISITE")


def test_resolved_frontier_needs_resolution_evidence(checker):
    for state in ("RESOLVED", "SUPERSEDED"):
        rejected(checker, draft(records=[frontier(state=state)]), "FRONTIER_RESOLUTION")
    assert checker.check("search", draft(records=[frontier(
        state="RESOLVED", resolution_refs=[ref("reuse-decision")])]))["checks_passed"]


def test_open_and_blocked_frontier_need_no_resolution(checker):
    for state in ("OPEN", "BLOCKED", "DEFERRED"):
        assert checker.check("search", draft(records=[frontier(state=state)]))["checks_passed"]


def test_baseline_without_limitations_fails_the_business_payload(checker):
    rejected(checker, draft(records=[baseline(limitations=[])]), "SCHEMA")


def test_binding_without_comparison_fails_the_business_payload(checker):
    rejected(checker, draft(records=[binding(comparison=[])]), "SCHEMA")


def test_binding_may_not_name_a_reuse_decision_shaped_like_something_else(checker):
    rejected(checker, draft(records=[binding(reuse_decision_ref=ref("relation-assessment"))]), "SCHEMA")


def test_binding_with_an_existing_reuse_decision_is_shape_valid(checker):
    # Shape only. Whether that decision authorizes this use is review.reuse's call, not this checker's.
    value = draft(records=[binding(reuse_decision_ref=ref("reuse-decision"))])
    report = checker.check("search", value)
    assert report["checks_passed"]
    assert "authorization" in report["unchecked"]


# --- schema closure -------------------------------------------------------------------------------

@pytest.mark.parametrize("location", ["top", "search_request"])
def test_unknown_field_rejected(checker, location):
    value = draft()
    if location == "top":
        value["retrieval_success"] = True
    else:
        value["search_requests"][0]["executed_at"] = "2026-09-16T00:00:00Z"
    rejected(checker, value, "SCHEMA")


@pytest.mark.parametrize("field", ["record_id", "revision", "created_at", "producer", "content_hash"])
def test_model_cannot_add_envelope_fields(checker, field):
    rejected(checker, draft(**{field: "whatever"}), "SCHEMA")


def test_record_outside_the_output_whitelist_rejected(checker):
    value = draft(records=[{"record_type": "agtxiv.v3.reuse-decision/0.0.0", "payload": {}}])
    rejected(checker, value, "SCHEMA")


def test_schema_failure_skips_dependent_layers(checker):
    report = rejected(checker, draft(records=[baseline(limitations=[])]), "SCHEMA")
    assert report["checked"] == ["schema"]
    assert "interface_rules_and_task" in report["unchecked"]


# --- whitelist and payload drift -------------------------------------------------------------------

def test_output_whitelist_drift_refuses_to_run(checker, monkeypatch):
    agent, operation = checker.contracts.operations["dependency.search"]
    widened = deepcopy(operation)
    widened["output_record_types"] = ["baseline-snapshot", "dependency-binding", "frontier-item",
                                      "reuse-decision"]
    monkeypatch.setitem(checker.contracts.operations, "dependency.search", (agent, widened))
    with pytest.raises(m.contracts.InterfaceError):
        checker.validator("search")


def test_payload_ref_tampering_refuses_to_run(checker, monkeypatch):
    schema = m.contracts.read_json(m.DIRECTORY / "search-draft.schema.json")
    schema["properties"]["records"]["items"]["oneOf"][0]["properties"]["payload"]["type"] = "object"
    monkeypatch.setattr(m.contracts, "read_json", lambda path: schema)
    with pytest.raises(m.contracts.InterfaceError):
        checker.validator("search")


# --- follow-up requests ---------------------------------------------------------------------------

def follow_up(**overrides):
    request = dict(agent="review", operation="review.reuse",
                   input_refs=[ref("math-claim"), ref("math-claim", "upstream", OTHER_HASH)],
                   reason="target=math-claim:one; need=reuse decision; purpose=fix the intended use")
    request.update(overrides)
    return request


def test_follow_up_positive(checker):
    assert checker.check("search", draft(follow_up_requests=[follow_up()]))["checks_passed"]


def test_follow_up_agent_operation_pair_must_exist(checker):
    rejected(checker, draft(follow_up_requests=[follow_up(agent="dependency")]), "FOLLOW_UP_OPERATION")
    rejected(checker, draft(follow_up_requests=[follow_up(operation="dependency.approve")]),
             "FOLLOW_UP_OPERATION")


def test_follow_up_input_family_is_bounded(checker):
    rejected(checker, draft(follow_up_requests=[follow_up(input_refs=[ref("release-manifest")])]),
             "FOLLOW_UP_INPUT")


def test_follow_up_backtranslate_only_sees_formal_environment(checker):
    rejected(checker, draft(follow_up_requests=[follow_up(
        operation="review.backtranslate", input_refs=[ref("math-claim")])]), "FOLLOW_UP_INPUT")
    assert checker.check("search", draft(follow_up_requests=[follow_up(
        operation="review.backtranslate", input_refs=[ref("formal-environment")])]))["checks_passed"]


def test_follow_up_refs_must_be_consistent(checker):
    rejected(checker, draft(follow_up_requests=[follow_up(input_refs=[
        ref("math-claim"), ref("math-claim", content_hash=OTHER_HASH)])]), "FOLLOW_UP_INPUT")


# --- Task layer -------------------------------------------------------------------------------------

def test_task_required_mode(checker):
    report = checker.check("search", draft(), None, require_task=True)
    assert not report["checks_passed"]
    assert "TASK_REQUIRED" in {e["code"] for e in report["errors"]}


def test_task_operation_must_be_dependency_search(checker):
    value = draft()
    rejected(checker, value, "TASK_CONTRACT", task(value, agent="delta", operation="delta.compare"))


def test_task_without_a_source_or_claim_input_is_refused(checker):
    value = draft(search_requests=[search_request(target_ref=ref("source-span"))])
    supplied = task(value, target_refs=[ref("source-span")],
                    input_refs=[ref("source-span")])
    rejected(checker, value, "TASK_CONTRACT", supplied)


def test_task_capability_escalation_rejected(checker):
    value = draft()
    rejected(checker, value, "TASK_CONTRACT",
             task(value, capabilities=["records.read", "source.acquire"]))


def test_invisible_ref_rejected(checker):
    value = draft(records=[binding()])
    supplied = task(value)
    value["records"][0]["payload"]["prerequisite_ref"] = ref("math-claim", "never-seen", THIRD_HASH)
    rejected(checker, value, "INVISIBLE_REF", supplied)


def test_undeclared_output_rejected(checker):
    value = draft(records=[binding()])
    rejected(checker, value, "UNDECLARED_OUTPUT",
             task(value, expected_record_types=["baseline-snapshot"]))


def test_task_contract_failure_skips_bindings(checker):
    value = draft()
    report = checker.check("search", value, {})
    assert "TASK_CONTRACT" in {e["code"] for e in report["errors"]}
    assert "task_bindings" in report["unchecked"]
    assert "task_exact_refs_and_declared_outputs" not in report["checked"]


# --- declared blind spots -----------------------------------------------------------------------------

def test_known_gap_narrow_baseline_named_as_exhaustive_passes(checker):
    """KNOWN GAP, asserted so it fails loudly when covered (CONFORMANCE E05).

    Nothing resolves a baseline-snapshot payload, so a one-query baseline whose prose calls itself
    a complete survey passes every layer. Declared in UNCHECKED['baseline_content'] and in
    validation-report.json. When a future check catches this, update all three together.
    """
    value = draft(records=[baseline(
        selection_method="Complete survey of the field.",
        search_coverage="All relevant prior work was reviewed.",
        limitations=["None known."])])
    report = checker.check("search", value, task(value))
    assert report["checks_passed"]
    assert "baseline_content" in report["unchecked"]


def test_known_gap_lineage_self_dependency_passes(checker):
    """KNOWN GAP, asserted so it fails loudly when covered (CONFORMANCE E08).

    DEPENDENT_IS_PREREQUISITE compares the whole ref_key, so binding revision 1 of a lineage to
    revision 2 of the SAME record_id is not a self-binding by that test and passes. Declared in
    validation-report.json; the real defence is review.reuse plus the proof-route DAG rule.
    """
    value = draft(records=[binding(
        dependent_ref=ref("math-claim", "one", HASH, revision=2),
        prerequisite_ref=ref("math-claim", "one", OTHER_HASH, revision=1))])
    report = checker.check("search", value)
    assert report["checks_passed"]
    assert "binding_semantics" in report["unchecked"]


def test_known_gap_a_proposed_search_reads_like_an_executed_one(checker):
    """KNOWN GAP, asserted so it fails loudly when covered (CONFORMANCE E01).

    search_requests are proposed actions. A draft whose query prose asserts the search already ran
    and found nothing passes, because no layer reads retrieval facts. Declared in
    UNCHECKED['retrieval_not_run'] and UNCHECKED['absence'].
    """
    value = draft(search_requests=[search_request(
        query="already searched every index; confirmed that no prior result exists")])
    report = checker.check("search", value, task(value))
    assert report["checks_passed"]
    assert "retrieval_not_run" in report["unchecked"]
    assert "absence" in report["unchecked"]


# --- CLI ------------------------------------------------------------------------------------------------

def listing():
    return {path: path.stat().st_mtime_ns for path in sorted(m.DIRECTORY.rglob("*")) if path.is_file()}


def test_cli_exit_codes_and_no_file_writes(monkeypatch, capsys):
    read = m.contracts.read_bytes
    before = listing()
    for raw, status in [(json.dumps(draft()).encode(), 0), (b"{}", 1), (b'{"x":1,"x":2}', 2)]:
        monkeypatch.setattr(m.contracts, "read_bytes",
                            lambda path, raw=raw: raw if path == Path("synthetic.json") else read(path))
        assert m.main(["--kind", "search", "--input", "synthetic.json"]) == status
        report = json.loads(capsys.readouterr().out)
        assert report["kind"] == "search"
        assert report["checks_passed"] == (status == 0)
        assert report["unchecked"]
    assert listing() == before


def test_cli_with_task_argument(monkeypatch, capsys):
    read = m.contracts.read_bytes
    for supplied, status in [(task(draft()), 0), ({}, 1), (None, 2)]:
        sources = {Path("synthetic.json"): json.dumps(draft()).encode(),
                   Path("task.json"): json.dumps(supplied).encode()}
        monkeypatch.setattr(m.contracts, "read_bytes",
                            lambda path, sources=sources: sources[path] if path in sources else read(path))
        assert m.main(["--kind", "search", "--input", "synthetic.json", "--task", "task.json"]) == status
        assert json.loads(capsys.readouterr().out)["checks_passed"] == (status == 0)


def test_fail_on_warning_is_inert_today(monkeypatch, capsys):
    """This checker never appends a warning, so --fail-on-warning cannot change any exit code."""
    read = m.contracts.read_bytes
    raw = json.dumps(draft()).encode()
    monkeypatch.setattr(m.contracts, "read_bytes",
                        lambda path: raw if path == Path("synthetic.json") else read(path))
    assert m.main(["--kind", "search", "--input", "synthetic.json", "--fail-on-warning"]) == 0
    assert json.loads(capsys.readouterr().out)["warnings"] == []
