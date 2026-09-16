"""Synthetic interface fixtures only: no historical cases, writes, model calls or external execution.

Every rule asserted here is a rule check_interfaces.py actually enforces today. Tests whose
name ends in _is_a_known_gap assert that something PASSES; they fix a documented blind spot so
that adding coverage later fails loudly and forces CONFORMANCE.md, the checker's `unchecked`
map and validation-report.json to be updated together.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.dont_write_bytecode = True
MODULE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
CONFORMANCE = MODULE / "conformance"
CHECKER = MODULE / "check_interfaces.py"

spec = importlib.util.spec_from_file_location("planner_interfaces", CHECKER)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

HASH = "sha256:" + "a" * 64
OTHER_HASH = "sha256:" + "b" * 64


def ref(name, suffix="one", content_hash=HASH):
    return dict(record_type=f"agtxiv.v3.{name}/0.0.0", record_id=f"{name}:{suffix}",
                revision=1, content_hash=content_hash)


def fixture(name):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


def draft():
    return fixture("propose-draft.json")


def task():
    return fixture("task.json")


def proposal(agent, operation, input_refs, reason=None, blocked_on=None):
    return dict(agent=agent, operation=operation, input_refs=input_refs,
                reason=reason or f"target={agent}; need=a fixed prerequisite; purpose=move the main line",
                blocked_on=list(blocked_on or []))


def follow_up(request):
    return {key: deepcopy(request[key]) for key in ("agent", "operation", "input_refs", "reason")}


@pytest.fixture(scope="module")
def checker():
    return m.InterfaceChecker()


def codes(report):
    return {error["code"] for error in report["errors"]}


def warning_codes(report):
    return {warning["code"] for warning in report["warnings"]}


def rejected(checker, value, code, supplied_task=None, require_task=False):
    report = checker.check("propose", value, supplied_task, require_task=require_task)
    assert not report["checks_passed"], report
    assert code in codes(report), report
    return report


def accepted(checker, value, supplied_task=None):
    report = checker.check("propose", value, supplied_task)
    assert report["checks_passed"], report
    return report


# --- positive and read-only -------------------------------------------------

def test_conformance_draft_passes_without_task(checker):
    report = accepted(checker, draft())
    assert report["checked"] == [
        "schema", "no_business_records",
        "proposal_agent_operation_pairs", "proposal_input_refs_and_families",
        "follow_up_agent_operation_pairs", "follow_up_input_refs_and_families",
        "follow_up_subset_of_proposals", "follow_up_requires_unblocked_proposal"]
    assert "task" in report["unchecked"]


def test_conformance_draft_passes_with_task_and_adds_three_layers(checker):
    report = accepted(checker, draft(), task())
    assert report["checked"][-3:] == ["task_declared_outputs", "task_contract", "task_exact_refs"]
    assert "task" not in report["unchecked"]


def test_checker_does_not_mutate_its_inputs(checker):
    value, supplied = draft(), task()
    before_value, before_task = deepcopy(value), deepcopy(supplied)
    checker.check("propose", value, supplied)
    assert value == before_value
    assert supplied == before_task


def test_every_report_gets_its_own_unchecked_copy(checker):
    first = checker.check("propose", draft())
    first["unchecked"]["injected"] = "x"
    assert "injected" not in checker.check("propose", draft())["unchecked"]


def test_constant_blind_spots_are_always_reported(checker):
    report = accepted(checker, draft(), task())
    for key in ("record_set", "source_bytes", "execution_identity", "meaning", "result",
                "plan_quality", "required_inputs_of_proposed_operation",
                "budget_and_no_progress", "escalation_in_prose"):
        assert key in report["unchecked"], key


# --- E01 self redispatch ----------------------------------------------------

def test_self_redispatch_is_only_a_warning_without_a_task(checker):
    report = checker.check("propose", fixture("propose-draft-rejected.json"))
    assert "SELF_REDISPATCH" in warning_codes(report)
    assert "SELF_REDISPATCH" not in codes(report)


def test_self_redispatch_is_an_error_with_a_task(checker):
    value = draft()
    value["proposals"].append(proposal("planner", "planner.propose", []))
    rejected(checker, value, "SELF_REDISPATCH", task())


# --- E02 blocked follow-up --------------------------------------------------

def test_blocked_proposal_cannot_be_a_follow_up(checker):
    rejected(checker, fixture("propose-draft-blocked-follow-up.json"), "FOLLOW_UP_BLOCKED")


def test_same_request_is_accepted_once_its_block_is_cleared(checker):
    value = fixture("propose-draft-blocked-follow-up.json")
    value["proposals"][1]["blocked_on"] = []
    accepted(checker, value)


# --- E03 / E04 agent and operation pairing ----------------------------------

def test_unknown_operation_is_rejected(checker):
    value = draft()
    value["proposals"][0]["operation"] = "planner.run"
    report = rejected(checker, value, "PROPOSAL_OPERATION")
    assert "Unknown operation" in report["errors"][0]["message"]


def test_agent_operation_mismatch_is_rejected(checker):
    value = draft()
    value["proposals"][1]["agent"] = "review"
    report = rejected(checker, value, "PROPOSAL_OPERATION")
    assert any("mismatch" in error["message"] for error in report["errors"])


def test_follow_up_operation_is_checked_separately(checker):
    value = draft()
    value["follow_up_requests"][0]["operation"] = "utility.register-plans"
    rejected(checker, value, "FOLLOW_UP_OPERATION")


# --- E05 input families -----------------------------------------------------

def test_disallowed_proposed_input_family_is_rejected(checker):
    report = rejected(checker, fixture("propose-draft-rejected.json"), "PROPOSAL_INPUT")
    assert any(error["path"] == "/proposals/2/input_refs" for error in report["errors"])


def test_backtranslate_accepts_only_formal_environment(checker):
    allowed = proposal("review", "review.backtranslate", [ref("formal-environment")])
    value = draft()
    value["proposals"].append(allowed)
    accepted(checker, value)
    value = draft()
    value["proposals"].append(proposal("review", "review.backtranslate", [ref("frozen-scope")]))
    rejected(checker, value, "PROPOSAL_INPUT")


def test_context_types_are_allowed_beyond_the_operation_whitelist(checker):
    value = draft()
    value["proposals"].append(proposal("delta", "delta.compare",
                                       [ref("baseline-snapshot"), ref("processing-profile")]))
    accepted(checker, value)


def test_follow_up_input_family_is_checked_separately(checker):
    request = proposal("review", "review.backtranslate", [ref("scientific-claim")])
    value = draft()
    value["proposals"].append(request)
    value["follow_up_requests"].append(follow_up(request))
    report = rejected(checker, value, "FOLLOW_UP_INPUT")
    assert "PROPOSAL_INPUT" in codes(report)


# --- E06 reference identity -------------------------------------------------

def test_same_identity_with_a_different_hash_is_rejected(checker):
    value = draft()
    value["proposals"][1]["input_refs"].append(ref("scientific-claim", content_hash=OTHER_HASH))
    report = rejected(checker, value, "PROPOSAL_INPUT")
    assert any("Duplicate identity" in error["message"] for error in report["errors"])


# --- E07 visibility ---------------------------------------------------------

def test_reference_outside_task_inputs_is_rejected(checker):
    value = draft()
    value["proposals"][1]["input_refs"] = [ref("scientific-claim", suffix="two")]
    rejected(checker, value, "INVISIBLE_REF", task())


def test_reference_outside_task_inputs_is_unchecked_without_a_task(checker):
    value = draft()
    value["proposals"][1]["input_refs"] = [ref("scientific-claim", suffix="two")]
    report = accepted(checker, value)
    assert "task" in report["unchecked"]


# --- E08 escalation ---------------------------------------------------------

@pytest.mark.parametrize("key, value", [
    ("capabilities", ["records.write"]),
    ("limits", {"max_attempts": 100}),
    ("exclusions", []),
    ("acceptance", "EVIDENCE"),
    ("expected_record_types", ["agentization-plan"]),
    ("priority", 1),
])
def test_structured_escalation_keys_fail_the_schema(checker, key, value):
    draft_value = draft()
    draft_value["proposals"][0][key] = value
    report = rejected(checker, draft_value, "SCHEMA")
    assert report["unchecked"]["interface_rules_and_task"]


def test_top_level_unknown_key_fails_the_schema(checker):
    value = draft()
    value["capabilities"] = ["records.write"]
    rejected(checker, value, "SCHEMA")


def test_escalation_written_as_prose_is_a_known_gap(checker):
    # No machine layer catches this today; see CONFORMANCE E08 and unchecked.escalation_in_prose.
    value = draft()
    value["proposals"][0]["reason"] = ("target=source-snapshot:one; need=records.write and a larger "
                                       "budget; purpose=let the host drop the exclusion list")
    report = accepted(checker, value)
    assert "escalation_in_prose" in report["unchecked"]


# --- E09 business records ---------------------------------------------------

def test_records_cannot_hold_a_business_record(checker):
    value = draft()
    value["records"] = [{"record_type": "agtxiv.v3.agentization-plan/0.0.0", "payload": {}}]
    rejected(checker, value, "SCHEMA")


def test_smuggled_record_code_is_unreachable_today_is_a_known_gap(checker):
    # The draft schema is closed and RecordRef carries exactly the four reference keys, so the
    # anti-smuggling scan cannot fire: the schema layer rejects first and check() returns early.
    value = draft()
    value["proposals"][0]["input_refs"][0]["payload"] = {"anything": 1}
    report = rejected(checker, value, "SCHEMA")
    assert "SMUGGLED_RECORD" not in codes(report)
    assert "no_business_records" not in report["checked"]


# --- E10 duplicates ---------------------------------------------------------

def test_duplicate_proposal_is_rejected(checker):
    value = draft()
    value["proposals"].append(deepcopy(value["proposals"][0]))
    rejected(checker, value, "DUPLICATE_PROPOSAL")


def test_different_purpose_same_inputs_is_judged_duplicate_is_a_known_gap(checker):
    # G-05: the draft has no field for purpose or route, so two genuinely different jobs with the
    # same inputs collapse into one key. Recorded in CONFORMANCE E10 and validation-report.json.
    value = draft()
    other = deepcopy(value["proposals"][1])
    other["reason"] = "target=scientific-claim:one; need=a comparison baseline; purpose=a different job"
    value["proposals"].append(other)
    rejected(checker, value, "DUPLICATE_PROPOSAL")


def test_follow_up_must_appear_in_proposals(checker):
    value = draft()
    value["follow_up_requests"][0]["input_refs"] = value["follow_up_requests"][0]["input_refs"][:1]
    rejected(checker, value, "FOLLOW_UP_NOT_PROPOSED")


# --- E11 / E13 host-owned judgements ---------------------------------------

def test_budget_and_plan_quality_are_reported_as_unchecked(checker):
    report = accepted(checker, draft(), task())
    assert "parent plan's remaining allowance" in report["unchecked"]["budget_and_no_progress"]
    assert "user's actual goal" in report["unchecked"]["plan_quality"]


# --- E14 declared outputs and the Task layer --------------------------------

def test_nonempty_expected_record_types_is_rejected(checker):
    supplied = task()
    supplied["expected_record_types"] = ["agentization-plan"]
    report = rejected(checker, draft(), "NONEMPTY_EXPECTED_TYPES", supplied)
    assert "TASK_CONTRACT" in codes(report)


def test_task_for_another_operation_is_rejected(checker):
    supplied = task()
    supplied["agent"], supplied["operation"] = "reader", "reader.explain"
    report = rejected(checker, draft(), "TASK_CONTRACT", supplied)
    assert report["unchecked"]["task_bindings"]


def test_require_task_without_a_task_is_rejected(checker):
    rejected(checker, draft(), "TASK_REQUIRED", None, require_task=True)


# --- fixed text order (warnings only) --------------------------------------

def test_free_form_reason_is_a_warning_not_an_error(checker):
    value = draft()
    value["proposals"][0]["reason"] = "register the plan"
    report = accepted(checker, value)
    assert "REASON_FORMAT" in warning_codes(report)


def test_free_form_open_item_and_blocked_on_are_warnings(checker):
    value = draft()
    value["open_items"] = ["budget unknown"]
    value["proposals"][1]["blocked_on"] = ["needs a baseline"]
    report = accepted(checker, value)
    assert warning_codes(report) == {"OPEN_ITEM_FORMAT"}
    assert {warning["path"] for warning in report["warnings"]} == {
        "/open_items/0", "/proposals/1/blocked_on/0"}


def test_ordered_text_checks_order_not_content():
    assert m.ordered_text("target=x; need=y; purpose=z", m.REASON_ORDER)
    assert not m.ordered_text("need=y; target=x; purpose=z", m.REASON_ORDER)


# --- whitelist drift guards (exit 2 class) ----------------------------------

def test_nonempty_output_whitelist_raises_interface_error(checker, monkeypatch):
    real = checker.contracts.operation

    def drifted(agent, name):
        operation = dict(real(agent, name))
        if name == "planner.propose":
            operation["output_record_types"] = ["agentization-plan"]
        return operation

    monkeypatch.setattr(checker.contracts, "operation", drifted)
    with pytest.raises(m.contracts.InterfaceError, match="empty output_record_types"):
        checker.validator("propose")


def test_relaxed_records_shape_raises_interface_error(checker, monkeypatch):
    real = m.contracts.read_json

    def drifted(path):
        value = real(path)
        if str(path).endswith("propose-draft.schema.json"):
            value["properties"]["records"] = {"type": "array", "maxItems": 10}
        return value

    monkeypatch.setattr(m.contracts, "read_json", drifted)
    with pytest.raises(m.contracts.InterfaceError, match="empty output whitelist"):
        checker.validator("propose")


# --- CLI --------------------------------------------------------------------

def run(*arguments):
    return subprocess.run([sys.executable, "-B", str(CHECKER), *arguments],
                          cwd=REPO, capture_output=True, text=True, check=False)


def test_cli_exit_codes_and_no_writes(tmp_path):
    before = sorted(path.relative_to(MODULE).as_posix() for path in MODULE.rglob("*"))
    assert run("--kind", "propose", "--input",
               str(CONFORMANCE / "propose-draft.json")).returncode == 0
    assert run("--kind", "propose", "--input",
               str(CONFORMANCE / "propose-draft-rejected.json")).returncode == 1
    not_json = tmp_path / "draft.json"
    not_json.write_text("{not json", encoding="utf-8")
    failed = run("--kind", "propose", "--input", str(not_json))
    assert failed.returncode == 2
    assert "INPUT_ERROR" in failed.stdout
    assert sorted(path.relative_to(MODULE).as_posix() for path in MODULE.rglob("*")) == before


def test_cli_fail_on_warning_promotes_a_warning(tmp_path):
    value = draft()
    value["open_items"] = ["budget unknown"]
    path = tmp_path / "warned.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert run("--kind", "propose", "--input", str(path)).returncode == 0
    assert run("--kind", "propose", "--input", str(path), "--fail-on-warning").returncode == 1


def test_cli_rejects_a_null_task_and_an_unknown_kind(tmp_path):
    null_task = tmp_path / "task.json"
    null_task.write_text("null", encoding="utf-8")
    assert run("--kind", "propose", "--input", str(CONFORMANCE / "propose-draft.json"),
               "--task", str(null_task)).returncode == 2
    assert run("--kind", "plan", "--input", str(CONFORMANCE / "propose-draft.json")).returncode == 2
