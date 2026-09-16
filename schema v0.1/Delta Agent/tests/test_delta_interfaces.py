"""Synthetic Delta interface fixtures only: no real records, no writes, no external execution.

Every case is built by copying a file from ../conformance/ and mutating the copy, so the
document, the fixtures and these tests describe one checker. Cases marked GAP assert that a
draft PASSES; they characterize a known blind spot recorded in CONFORMANCE.md and in
validation-report.json, and are meant to fail loudly if coverage is ever added.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

sys.dont_write_bytecode = True
MODULE = Path(__file__).resolve().parents[1]
CONFORMANCE = MODULE / "conformance"

spec = importlib.util.spec_from_file_location("delta_interfaces", MODULE / "check_interfaces.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture(name):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


def draft():
    return fixture("delta-draft.json")


def covered_draft():
    return fixture("delta-draft-multi-target-covered.json")


def invalid_draft():
    return fixture("delta-draft-invalid.json")


def multi_task():
    return fixture("task-multi-target.json")


def single_task():
    """The same fixture Task narrowed to its first assigned target."""
    task = multi_task()
    task["target_refs"] = task["target_refs"][:1]
    return task


def input_ref(short_name):
    for ref in multi_task()["input_refs"]:
        if m.contracts.short_type(ref) == short_name:
            return copy.deepcopy(ref)
    raise AssertionError(short_name)


def delta_payload(value):
    for record in value["records"]:
        if m.contracts.short_type(record) == "contribution-delta":
            return record["payload"]
    raise AssertionError("no contribution-delta in fixture")


def frontier_payload(value):
    for record in value["records"]:
        if m.contracts.short_type(record) == "frontier-item":
            return record["payload"]
    raise AssertionError("no frontier-item in fixture")


@pytest.fixture(scope="module")
def checker():
    return m.InterfaceChecker()


def codes(checker, value, task=None, require_task=False):
    report = checker.check("delta", value, task, require_task=require_task)
    return report, {error["code"] for error in report["errors"]}


def rejected(checker, value, code, task=None, require_task=False):
    report, found = codes(checker, value, task, require_task)
    assert not report["checks_passed"], report
    assert code in found, report
    return report


def accepted(checker, value, task=None):
    report, _ = codes(checker, value, task)
    assert report["checks_passed"], report
    return report


# --- positive cases and read-only behaviour -------------------------------------------------

def test_conformance_draft_passes_without_task(checker):
    report = accepted(checker, draft())
    assert report["checked"] == ["schema", "delta_interface_rules",
                                 "follow_up_agent_operation_pairs",
                                 "follow_up_input_refs_and_families"]
    assert "task" in report["unchecked"]


def test_conformance_draft_passes_with_its_single_target_task(checker):
    report = accepted(checker, draft(), single_task())
    assert "task_pinned_baseline_and_assigned_current" in report["checked"]
    assert "task" not in report["unchecked"]


def test_multi_target_covered_fixture_passes_with_multi_target_task(checker):
    accepted(checker, covered_draft(), multi_task())


def test_check_does_not_mutate_its_inputs(checker):
    value, task = draft(), single_task()
    before_value, before_task = copy.deepcopy(value), copy.deepcopy(task)
    checker.check("delta", value, task)
    assert value == before_value
    assert task == before_task


def test_report_always_carries_its_own_unchecked_copy(checker):
    first = checker.check("delta", draft())
    first["unchecked"]["injected"] = "x"
    second = checker.check("delta", draft())
    assert "injected" not in second["unchecked"]


def test_unchecked_names_the_blind_spots_the_documents_rely_on(checker):
    report = checker.check("delta", draft())
    for key in ("baseline_fixation_time", "baseline_content", "prior_art",
                "relation_evidence", "qualification_meaning", "record_conditionals"):
        assert key in report["unchecked"]


# --- schema layer ---------------------------------------------------------------------------

def test_unknown_top_level_field_is_rejected(checker):
    value = draft()
    value["confidence"] = 0.9
    rejected(checker, value, "SCHEMA")


def test_model_supplied_envelope_field_is_rejected(checker):
    value = draft()
    value["records"][0]["record_id"] = "contribution-delta:one"
    rejected(checker, value, "SCHEMA")


def test_record_type_outside_the_output_whitelist_is_rejected(checker):
    value = draft()
    value["records"][0]["record_type"] = "agtxiv.v3.relation-assessment/0.0.0"
    rejected(checker, value, "SCHEMA")


def test_schema_failure_skips_the_dependent_layers(checker):
    value = draft()
    del value["baseline_ref"]
    report = rejected(checker, value, "SCHEMA")
    assert report["checked"] == ["schema"]
    assert "interface_rules_and_task" in report["unchecked"]


# --- contribution-delta draft rules ---------------------------------------------------------

def test_draft_may_not_declare_established_independence(checker):
    # Exactly what conformance/delta-draft-invalid.json encodes.
    rejected(checker, invalid_draft(), "DRAFT_REVIEW_UNESTABLISHED")


def test_supported_without_prior_is_rejected(checker):
    rejected(checker, invalid_draft(), "SUPPORTED_WITHOUT_PRIOR")


def test_supported_without_relation_is_rejected(checker):
    rejected(checker, invalid_draft(), "SUPPORTED_WITHOUT_RELATION")


def test_blank_qualification_is_rejected(checker):
    rejected(checker, invalid_draft(), "BLANK_QUALIFICATION")


def test_supported_with_prior_and_relation_is_accepted(checker):
    value = draft()
    delta_payload(value)["outcome"] = "SUPPORTED"
    accepted(checker, value)


def test_delta_measured_against_another_baseline_is_rejected(checker):
    value = draft()
    other = copy.deepcopy(value["baseline_ref"])
    other["record_id"] = "baseline-snapshot:two"
    delta_payload(value)["baseline_ref"] = other
    rejected(checker, value, "BASELINE_MISMATCH")


def test_baseline_as_current_endpoint_is_rejected(checker):
    value = draft()
    payload = delta_payload(value)
    payload["current_refs"].append(copy.deepcopy(value["baseline_ref"]))
    payload["review"]["reviewed_refs"].append(copy.deepcopy(value["baseline_ref"]))
    rejected(checker, value, "BASELINE_AS_CURRENT")


def test_baseline_as_prior_endpoint_is_rejected(checker):
    value = draft()
    delta_payload(value)["prior_refs"].append(copy.deepcopy(value["baseline_ref"]))
    rejected(checker, value, "BASELINE_AS_PRIOR")


def test_same_exact_record_on_both_sides_is_rejected(checker):
    value = draft()
    payload = delta_payload(value)
    payload["prior_refs"].append(copy.deepcopy(payload["current_refs"][0]))
    rejected(checker, value, "CURRENT_PRIOR_OVERLAP")


def test_duplicate_current_ref_is_rejected(checker):
    value = draft()
    payload = delta_payload(value)
    payload["current_refs"].append(copy.deepcopy(payload["current_refs"][0]))
    rejected(checker, value, "DUPLICATE_CURRENT")


def test_current_object_missing_from_reviewed_refs_is_rejected(checker):
    value = draft()
    payload = delta_payload(value)
    payload["review"]["reviewed_refs"] = copy.deepcopy(payload["prior_refs"])
    rejected(checker, value, "REVIEWED_REFS_COVERAGE")


def test_resolved_frontier_item_without_resolution_evidence_is_rejected(checker):
    value = draft()
    frontier_payload(value)["state"] = "RESOLVED"
    rejected(checker, value, "FRONTIER_RESOLUTION")


def test_superseded_frontier_item_without_resolution_evidence_is_rejected(checker):
    value = draft()
    frontier_payload(value)["state"] = "SUPERSEDED"
    rejected(checker, value, "FRONTIER_RESOLUTION")


# --- follow-up requests ---------------------------------------------------------------------

def test_follow_up_with_unregistered_agent_operation_pair_is_rejected(checker):
    value = draft()
    value["follow_up_requests"][0]["agent"] = "delta"
    rejected(checker, value, "FOLLOW_UP_OPERATION")


def test_follow_up_input_outside_the_target_operation_family_is_rejected(checker):
    value = draft()
    value["follow_up_requests"][0]["input_refs"].append({
        "record_type": "agtxiv.v3.paper-release/0.0.0",
        "record_id": "paper-release:one",
        "revision": 1,
        "content_hash": "sha256:" + "d" * 64})
    rejected(checker, value, "FOLLOW_UP_INPUT")


def test_follow_up_with_same_identity_and_different_hash_is_rejected(checker):
    value = draft()
    clash = copy.deepcopy(value["follow_up_requests"][0]["input_refs"][0])
    clash["content_hash"] = "sha256:" + "e" * 64
    value["follow_up_requests"][0]["input_refs"].append(clash)
    rejected(checker, value, "FOLLOW_UP_INPUT")


def test_backtranslate_follow_up_accepts_only_a_formal_environment(checker):
    value = draft()
    value["follow_up_requests"][0] = {
        "agent": "review",
        "operation": "review.backtranslate",
        "input_refs": [copy.deepcopy(delta_payload(value)["current_refs"][0])],
        "reason": "target=math-claim:current; need=a blind reading; purpose=check the formal statement"}
    rejected(checker, value, "FOLLOW_UP_INPUT")


# --- Task layer -----------------------------------------------------------------------------

def test_require_task_mode_refuses_a_draft_without_a_task(checker):
    rejected(checker, draft(), "TASK_REQUIRED", require_task=True)


def test_task_for_another_operation_is_rejected(checker):
    task = single_task()
    task["operation"] = "review.reuse"
    report = rejected(checker, draft(), "TASK_CONTRACT", task)
    assert "task_bindings" in report["unchecked"]


def test_reference_outside_task_input_refs_is_rejected(checker):
    value = draft()
    delta_payload(value)["current_refs"][0]["record_id"] = "math-claim:not-supplied"
    rejected(checker, value, "INVISIBLE_REF", single_task())


def test_record_type_not_predeclared_by_the_task_is_rejected(checker):
    task = single_task()
    task["expected_record_types"] = ["frontier-item"]
    rejected(checker, draft(), "UNDECLARED_OUTPUT", task)


def test_baseline_ref_must_be_the_unique_task_baseline(checker):
    value = draft()
    value["baseline_ref"]["record_id"] = "baseline-snapshot:two"
    rejected(checker, value, "TARGET_BASELINE", single_task())


def test_assigned_target_neither_compared_nor_declared_is_rejected(checker):
    # conformance/delta-draft.json against conformance/task-multi-target.json:
    # two of three assigned targets are silently absent.
    report = rejected(checker, draft(), "UNCOVERED_TARGET", multi_task())
    message = next(e["message"] for e in report["errors"] if e["code"] == "UNCOVERED_TARGET")
    assert "math-claim:current-2" in message and "math-claim:current-3" in message


def test_uncovered_target_accepts_a_frontier_item_declaration(checker):
    accepted(checker, covered_draft(), multi_task())


# --- checker self-guards --------------------------------------------------------------------

def test_output_whitelist_drift_raises_instead_of_reporting_a_data_error(checker, monkeypatch):
    original = checker.contracts.operation

    def narrowed(agent, name):
        operation = copy.deepcopy(original(agent, name))
        operation["output_record_types"] = ["contribution-delta"]
        return operation

    monkeypatch.setattr(checker.contracts, "operation", narrowed)
    with pytest.raises(m.contracts.InterfaceError):
        checker.check("delta", draft())


def test_cli_exit_codes_and_no_writes(tmp_path, capsys):
    before = sorted(path.name for path in CONFORMANCE.iterdir())

    def run(*argv):
        status = m.main(list(argv))
        return status, json.loads(capsys.readouterr().out)

    status, report = run("--kind", "delta", "--input", str(CONFORMANCE / "delta-draft.json"))
    assert (status, report["checks_passed"]) == (0, True)
    status, report = run("--kind", "delta",
                         "--input", str(CONFORMANCE / "delta-draft-invalid.json"))
    assert (status, report["checks_passed"]) == (1, False)
    broken = tmp_path / "broken.json"
    broken.write_text("not json", encoding="utf-8")
    status, report = run("--kind", "delta", "--input", str(broken))
    assert status == 2
    assert [error["code"] for error in report["errors"]] == ["INPUT_ERROR"]
    assert "interface" in report["unchecked"]
    assert sorted(path.name for path in CONFORMANCE.iterdir()) == before
    assert not (MODULE / "__pycache__").exists()


# --- characterized gaps: these assert that the checker PASSES ---------------------------------

def test_gap_a_draft_with_no_contribution_delta_skips_target_coverage(checker):
    # GAP (CONFORMANCE E06, PENDING_TESTS G-07/DL-02): the UNCOVERED_TARGET rule is guarded by
    # `not deltas`, so a draft that compares nothing at all satisfies it vacuously.
    value = covered_draft()
    value["records"] = [r for r in value["records"]
                        if m.contracts.short_type(r) == "frontier-item"]
    frontier_payload(value)["target_refs"] = [input_ref("relation-assessment")]
    accepted(checker, value, multi_task())


def test_gap_a_baseline_swapped_after_the_fact_is_indistinguishable(checker):
    # GAP (CONFORMANCE E08): the draft carries no time and the checker compares only reference
    # identities, so a baseline pinned after the result was known passes like any other.
    accepted(checker, draft(), single_task())
    assert "baseline_fixation_time" in checker.check("delta", draft())["unchecked"]


def test_gap_the_change_type_enum_value_is_never_judged(checker):
    # GAP (CONFORMANCE E09): a notation-only change recorded as GENERALIZES, or as INTRODUCES,
    # passes; the checker reads the enum but never the mathematics.
    for operation in ("GENERALIZES", "INTRODUCES", "CORRECTS", "REFUTES"):
        value = draft()
        delta_payload(value)["operation"] = operation
        accepted(checker, value)


def test_gap_the_author_declaration_may_be_copied_into_a_qualification(checker):
    # GAP (CONFORMANCE E10): qualifications are checked for being nonblank strings only.
    value = draft()
    payload = delta_payload(value)
    payload["qualifications"] = [payload["author_declaration"]]
    accepted(checker, value)


def test_gap_relation_refs_are_never_resolved(checker):
    # GAP (CONFORMANCE E03): SUPPORTED needs a nonempty relation_refs, and nothing more. Whether
    # the relation witnesses this comparison, or was independently produced, is not checked.
    value = draft()
    payload = delta_payload(value)
    payload["outcome"] = "SUPPORTED"
    payload["relation_refs"] = [input_ref("relation-assessment")]
    accepted(checker, value)
