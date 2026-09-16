"""Synthetic interface fixtures only: no historical cases, writes, model calls or external execution.

Covers every rule Review Agent/check_interfaces.py actually enforces, plus characterization
tests pinning the gaps CONFORMANCE.md marks as 未接入 (E03, E04, E06 partial, E08, E13, E14).
Those gap tests assert that the checker PASSES today; if coverage is ever added they fail loudly
so that check_interfaces.py's `unchecked` map, CONFORMANCE.md and validation-report.json get
updated in the same change.
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
spec = importlib.util.spec_from_file_location("review_interfaces", MODULE / "check_interfaces.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

CONFORMANCE = MODULE / "conformance"
HASH = "sha256:" + "a" * 64
OTHER_HASH = "sha256:" + "b" * 64
ARTIFACT = dict(artifact_id="artifact:formal-bytes", sha256="sha256:" + "c" * 64,
                byte_size=128, media_type="text/x-lean")

# Minimum inputs enforced by ../validate.py for each review operation.
REQUIRED_INPUTS = {
    "review.scope": ["inventory-discovery", "source-snapshot", "paper-structure",
                     "agentization-plan", "processing-profile"],
    "review.argument": ["argument-snapshot", "frozen-scope"],
    "review.reuse": ["math-claim", "processing-profile"],
    "review.backtranslate": ["formal-environment"],
    "review.alignment": ["math-claim", "argument-snapshot"],
    "review.scientific": ["math-claim"],
    "review.audit": ["release-manifest", "processing-profile"],
    "review.admission": ["paper-release", "knowledge-snapshot", "authority-policy",
                         "processing-profile"],
}
# A target the challenge fixture may legally point at, per each operation's input whitelist.
CHALLENGE_TARGET = {
    "scope": "inventory-discovery", "argument": "argument-snapshot", "reuse": "math-claim",
    "alignment": "math-claim", "scientific": "math-claim", "audit": "release-manifest",
}


def ref(name, suffix="one", content_hash=HASH):
    return dict(record_type=f"agtxiv.v3.{name}/0.0.0", record_id=f"{name}:{suffix}",
                revision=1, content_hash=content_hash)


def record(name, **payload):
    return dict(record_type=f"agtxiv.v3.{name}/0.0.0", payload=payload)


def review_context(independence="UNESTABLISHED", reviewed="math-claim"):
    return dict(reviewed_refs=[ref(reviewed)], producer_principal_ids=["agent:synthetic-producer"],
                independence=independence, conflicts=[],
                method="Read the exact fixed target and its declared evidence.", evidence_refs=[])


def challenge(kind="scope", **overrides):
    payload = dict(target_ref=ref(CHALLENGE_TARGET[kind]), category="SCOPE", severity="MAJOR",
                   statement="target=inventory-discovery:one; violated=scope closure; "
                             "basis=span 3.1; affects=math-claim:one; needs=paper.extract",
                   evidence_refs=[])
    payload.update(overrides)
    return record("challenge", **payload)


def frontier(**overrides):
    payload = dict(target_refs=[ref("math-claim")], kind="ALIGNMENT_GAP", axes=["formal_alignment"],
                   statement="The formal target has no frozen backtranslation yet.",
                   next_evidence="Run review.backtranslate on the fixed environment.",
                   attempt_refs=[], state="OPEN", resolution_refs=[])
    payload.update(overrides)
    return record("frontier-item", **payload)


def axis(**overrides):
    payload = dict(target_refs=[ref("math-claim")], axis="mathematical_correctness",
                   applicability="APPLICABLE", result="INCONCLUSIVE", execution="COMPLETED",
                   method="ARGUMENT_REVIEW", review=review_context(), support_refs=[],
                   counterevidence_refs=[], conditions=[], frontier_refs=[],
                   rationale="The discharge rule for step 3 was not supplied.")
    payload.update(overrides)
    return record("axis-assessment", **payload)


def comparison(dimension="OBJECT"):
    return dict(dimension=dimension, source_value="A_k over n terms",
                target_value="A_k over n terms", relation="EQUIVALENT", witness_refs=[])


def relation(**overrides):
    payload = dict(source_ref=ref("math-claim"), target_ref=ref("math-claim", "two"),
                   relation="EQUIVALENT", review=review_context(), comparisons=[comparison()],
                   outcome="PROPOSED", witness_refs=[])
    payload.update(overrides)
    return record("relation-assessment", **payload)


def alignment(**overrides):
    payload = dict(comparison_kind="MATH_TO_FORMAL", source_refs=[ref("math-claim")],
                   target_refs=[ref("formalization-attempt")], review=review_context(),
                   comparisons=[comparison("CONCLUSION")], outcome="ALIGNED",
                   backtranslation_refs=[])
    payload.update(overrides)
    return record("alignment-assessment", **payload)


def draft(kind="scope", **overrides):
    if kind == "backtranslate":
        value = dict(draft_version="1.0",
                     interpretation="For every pair of propositions P and Q, a proof of P and Q "
                                    "yields a proof of Q and P; no further assumption is used.",
                     conditions=[], records=[], open_items=[], follow_up_requests=[])
    elif kind in CHALLENGE_TARGET:
        value = dict(draft_version="1.0", records=[challenge(kind)], open_items=[],
                     follow_up_requests=[])
    else:
        # review.admission may output only admission-decision, so its minimal draft is an
        # explicit gap rather than a challenge.
        value = dict(draft_version="1.0", records=[],
                     open_items=["blocked: no authority-policy grant for this domain"],
                     follow_up_requests=[])
    value.update(overrides)
    return value


def task(value, operation="review.scope", **overrides):
    seen = {m.contracts.ref_key(r): r for _, r in m.walk(value) if set(r) == m.REF_KEYS}
    for name in REQUIRED_INPUTS[operation]:
        seen.setdefault(m.contracts.ref_key(ref(name)), ref(name))
    inputs = list(seen.values())
    supplied = dict(contract_version="0.1.0", task_id="synthetic-review", agent="review",
                    operation=operation,
                    brief="Assess the exact fixed target under the standard named by this task.",
                    target_refs=[deepcopy(inputs[0])], input_refs=deepcopy(inputs),
                    input_artifacts=[], depends_on=[], expected_record_types=["challenge"],
                    limits=dict(max_attempts=1, max_seconds=60, max_cost_units=0,
                                no_progress_limit=1),
                    acceptance="DELIVERY", exclusions=["agent:synthetic-producer"],
                    capabilities=["records.read", operation])
    supplied.update(overrides)
    return supplied


@pytest.fixture(scope="module")
def checker():
    return m.InterfaceChecker()


def accepted(checker, kind, value, supplied_task=None, **kw):
    report = checker.check(kind, value, supplied_task, **kw)
    assert report["checks_passed"], report
    return report


def rejected(checker, kind, value, code, supplied_task=None, **kw):
    report = checker.check(kind, value, supplied_task, **kw)
    assert not report["checks_passed"], report
    assert code in {e["code"] for e in report["errors"]}, report
    return report


# --- positives, read-only behaviour, and the eight kinds -------------------------------------

def test_all_eight_kinds_are_registered():
    assert set(m.SCHEMAS) == set(m.KINDS) == {
        "scope", "argument", "reuse", "backtranslate", "alignment", "scientific", "audit",
        "admission"}
    assert m.OPERATIONS == {k: f"review.{k}" for k in m.KINDS}


@pytest.mark.parametrize("kind", sorted(CHALLENGE_TARGET))
def test_minimal_draft_passes_without_task(checker, kind):
    report = accepted(checker, kind, draft(kind))
    assert "task" in report["unchecked"]
    assert kind + "_interface_rules" in report["checked"]


def test_checker_does_not_mutate_its_inputs(checker):
    value = draft("scope")
    supplied = task(value)
    before = deepcopy((value, supplied))
    accepted(checker, "scope", value, supplied)
    assert (value, supplied) == before


def test_admission_draft_delivers_only_an_open_item(checker):
    accepted(checker, "admission", draft("admission"))


def test_every_kind_declares_its_unchecked_blind_spots(checker):
    for kind in m.KINDS:
        report = checker.check(kind, draft(kind))
        assert set(report["unchecked"]) >= {
            "record_set", "independence", "assessment_meaning", "blind_isolation",
            "record_conditionals", "result"}


# --- conformance fixtures shared with tests/run_agent_tests.py -------------------------------

def test_conformance_backtranslate_fixture_passes(checker):
    value = json.loads((CONFORMANCE / "backtranslate-draft.json").read_text())
    supplied = json.loads((CONFORMANCE / "task-backtranslate.json").read_text())
    accepted(checker, "backtranslate", value, supplied, require_task=True)


def test_conformance_backtranslate_leak_fixture_is_rejected(checker):
    """CONFORMANCE E01: a first-round blind task that can see the expected answer."""
    value = json.loads((CONFORMANCE / "backtranslate-draft.json").read_text())
    supplied = json.loads((CONFORMANCE / "task-backtranslate-leak.json").read_text())
    report = rejected(checker, "backtranslate", value, "TASK_CONTRACT", supplied)
    assert "Disallowed input family" in report["errors"][0]["message"]
    assert "task_bindings" in report["unchecked"]


# --- draft-layer rules ------------------------------------------------------------------------

def test_e02_backtranslate_draft_may_not_carry_a_business_record(checker):
    rejected(checker, "backtranslate", draft("backtranslate", records=[frontier()]), "SCHEMA")


def test_e02_backtranslate_draft_may_not_invent_identity_fields(checker):
    rejected(checker, "backtranslate",
             draft("backtranslate", source_blind=True, packet_ref=ref("formalization-packet")),
             "SCHEMA")


def test_unknown_top_level_field_is_rejected(checker):
    rejected(checker, "scope", draft("scope", verdict="PASS"), "SCHEMA")


def test_record_type_and_payload_branch_must_match(checker):
    bad = draft("scope")
    bad["records"][0]["record_type"] = "agtxiv.v3.frontier-item/0.0.0"
    rejected(checker, "scope", bad, "SCHEMA")


def test_record_outside_the_operation_whitelist_is_rejected(checker):
    """review.admission outputs only admission-decision (CONFORMANCE E10)."""
    rejected(checker, "admission", draft("admission", records=[frontier()]), "SCHEMA")


def test_model_may_not_add_an_envelope_field(checker):
    bad = draft("scope")
    bad["records"][0]["record_id"] = "challenge:one"
    rejected(checker, "scope", bad, "SCHEMA")


def test_e12_empty_delivery_is_rejected(checker):
    rejected(checker, "scope", draft("scope", records=[], open_items=["   "]), "EMPTY_DELIVERY")


def test_e12_open_item_alone_is_a_valid_delivery(checker):
    accepted(checker, "scope",
             draft("scope", records=[], open_items=["blocked: paper-structure not supplied"]))


def test_e09_resolved_frontier_item_needs_resolution_refs(checker):
    rejected(checker, "scope", draft("scope", records=[frontier(state="RESOLVED")]),
             "FRONTIER_RESOLUTION")


def test_e09_superseded_frontier_item_needs_resolution_refs(checker):
    rejected(checker, "scope", draft("scope", records=[frontier(state="SUPERSEDED")]),
             "FRONTIER_RESOLUTION")


def test_e09_resolved_frontier_item_with_evidence_passes(checker):
    accepted(checker, "scope", draft("scope", records=[
        frontier(state="RESOLVED", resolution_refs=[ref("alignment-assessment")])]))


# --- follow-up requests ------------------------------------------------------------------------

def test_follow_up_unknown_operation_is_rejected(checker):
    value = draft("scope", follow_up_requests=[dict(
        agent="review", operation="review.everything", input_refs=[], reason="need more")])
    rejected(checker, "scope", value, "FOLLOW_UP_OPERATION")


def test_follow_up_agent_operation_mismatch_is_rejected(checker):
    value = draft("scope", follow_up_requests=[dict(
        agent="paper", operation="review.scope", input_refs=[], reason="need more")])
    rejected(checker, "scope", value, "FOLLOW_UP_OPERATION")


def test_e01_follow_up_backtranslate_allows_only_formal_environment(checker):
    value = draft("scope", follow_up_requests=[dict(
        agent="review", operation="review.backtranslate",
        input_refs=[ref("formal-environment"), ref("math-claim")],
        reason="interpret the fixed declarations")])
    rejected(checker, "scope", value, "FOLLOW_UP_INPUT")


def test_follow_up_backtranslate_with_only_formal_environment_passes(checker):
    value = draft("scope", follow_up_requests=[dict(
        agent="review", operation="review.backtranslate",
        input_refs=[ref("formal-environment")], reason="interpret the fixed declarations")])
    accepted(checker, "scope", value)


def test_follow_up_input_outside_the_target_whitelist_is_rejected(checker):
    value = draft("scope", follow_up_requests=[dict(
        agent="proof", operation="proof.expand", input_refs=[ref("release-certificate")],
        reason="expand the missing step")])
    rejected(checker, "scope", value, "FOLLOW_UP_INPUT")


def test_e11_follow_up_same_identity_different_hash_is_rejected(checker):
    value = draft("scope", follow_up_requests=[dict(
        agent="review", operation="review.backtranslate",
        input_refs=[ref("formal-environment"), ref("formal-environment", content_hash=OTHER_HASH)],
        reason="interpret the fixed declarations")])
    rejected(checker, "scope", value, "FOLLOW_UP_INPUT")


# --- Task layer ---------------------------------------------------------------------------------

def test_task_required_mode(checker):
    rejected(checker, "scope", draft("scope"), "TASK_REQUIRED", None, require_task=True)


def test_task_operation_must_match_the_kind(checker):
    value = draft("argument")
    rejected(checker, "argument", value, "TASK_CONTRACT", task(value, "review.scope"))


def test_e04_review_task_must_declare_producer_exclusions(checker):
    value = draft("scope")
    report = rejected(checker, "scope", value, "TASK_CONTRACT", task(value, exclusions=[]))
    assert "Independent work requires declared producer exclusions" in report["errors"][0]["message"]


def test_missing_required_operation_input_is_rejected(checker):
    value = draft("scope")
    supplied = task(value)
    supplied["input_refs"] = [r for r in supplied["input_refs"]
                              if "paper-structure" not in r["record_id"]]
    report = rejected(checker, "scope", value, "TASK_CONTRACT", supplied)
    assert "paper-structure" in report["errors"][0]["message"]


def test_e05_comparison_operations_need_two_exact_targets(checker):
    value = draft("reuse")
    supplied = task(value, "review.reuse")
    report = rejected(checker, "reuse", value, "TASK_CONTRACT", supplied)
    assert "Comparison requires both exact target endpoints" in report["errors"][0]["message"]


def test_e05_two_targets_satisfy_the_comparison_rule(checker):
    value = draft("reuse", records=[relation()])
    supplied = task(value, "review.reuse", expected_record_types=["relation-assessment"])
    supplied["target_refs"] = [ref("math-claim"), ref("math-claim", "two")]
    accepted(checker, "reuse", value, supplied)


def test_e07_reuse_decision_requires_a_processing_profile(checker):
    value = draft("reuse", records=[relation()])
    supplied = task(value, "review.reuse", expected_record_types=["reuse-decision"])
    supplied["target_refs"] = [ref("math-claim"), ref("math-claim", "two")]
    supplied["input_refs"] = [r for r in supplied["input_refs"]
                              if "processing-profile" not in r["record_id"]]
    report = rejected(checker, "reuse", value, "TASK_CONTRACT", supplied)
    assert "Reuse decision requires a processing profile" in report["errors"][0]["message"]


def test_e06_formal_alignment_requires_a_frozen_backtranslation(checker):
    value = draft("alignment", records=[alignment()])
    supplied = task(value, "review.alignment", expected_record_types=["alignment-assessment"])
    supplied["target_refs"] = [ref("math-claim"), ref("formalization-attempt")]
    report = rejected(checker, "alignment", value, "TASK_CONTRACT", supplied)
    assert "Formal alignment requires frozen backtranslation" in report["errors"][0]["message"]


def test_e06_formal_alignment_with_a_backtranslation_passes(checker):
    value = draft("alignment", records=[alignment(backtranslation_refs=[ref("backtranslation")])])
    supplied = task(value, "review.alignment", expected_record_types=["alignment-assessment"])
    supplied["target_refs"] = [ref("math-claim"), ref("formalization-attempt")]
    accepted(checker, "alignment", value, supplied)


def test_e10_undeclared_output_type_is_rejected(checker):
    value = draft("scope", records=[frontier()])
    rejected(checker, "scope", value, "UNDECLARED_OUTPUT", task(value))


def test_e10_output_outside_the_operation_whitelist_is_rejected_at_task_level(checker):
    value = draft("admission")
    supplied = task(value, "review.admission", expected_record_types=["challenge"])
    report = rejected(checker, "admission", value, "TASK_CONTRACT", supplied)
    assert "Disallowed output family" in report["errors"][0]["message"]


def test_e11_reference_outside_task_inputs_is_rejected(checker):
    value = draft("scope")
    supplied = task(value)
    value["records"][0]["payload"]["target_ref"] = ref("inventory-discovery", "unseen")
    rejected(checker, "scope", value, "INVISIBLE_REF", supplied)


def test_capability_escalation_is_rejected(checker):
    value = draft("scope")
    supplied = task(value, capabilities=["records.read", "review.scope", "records.write"])
    report = rejected(checker, "scope", value, "TASK_CONTRACT", supplied)
    assert "Capability escalation" in report["errors"][0]["message"]


def test_evidence_acceptance_requires_policy_and_profile(checker):
    value = draft("argument")
    supplied = task(value, "review.argument", acceptance="EVIDENCE")
    report = rejected(checker, "argument", value, "TASK_CONTRACT", supplied)
    assert "Evidence gate requires exact policy and profile" in report["errors"][0]["message"]


def test_blind_task_must_be_delivery_with_nonempty_artifacts(checker):
    value = draft("backtranslate")
    supplied = task(value, "review.backtranslate", input_artifacts=[ARTIFACT],
                    expected_record_types=[])
    accepted(checker, "backtranslate", value, supplied)
    report = rejected(checker, "backtranslate", value, "TASK_CONTRACT",
                      task(value, "review.backtranslate", input_artifacts=[],
                           expected_record_types=[]))
    assert "Source-blind work requires explicit formal artifacts" in report["errors"][0]["message"]


def test_blind_task_may_not_ask_for_an_evidence_gate(checker):
    value = draft("backtranslate")
    supplied = task(value, "review.backtranslate", input_artifacts=[ARTIFACT],
                    expected_record_types=[], acceptance="EVIDENCE")
    rejected(checker, "backtranslate", value, "TASK_CONTRACT", supplied)


# --- whitelist drift guards ---------------------------------------------------------------------

def test_schema_whitelist_drift_raises(checker, monkeypatch):
    original = checker.contracts.operation

    def shrunken(agent, name):
        result = dict(original(agent, name))
        result["output_record_types"] = result["output_record_types"][:1]
        return result

    monkeypatch.setattr(checker.contracts, "operation", shrunken)
    with pytest.raises(m.contracts.InterfaceError):
        checker.validator("scope")


def test_backtranslate_draft_must_stay_record_free(checker, monkeypatch):
    original = checker.contracts.operation

    def widened(agent, name):
        result = dict(original(agent, name))
        if name == "review.backtranslate":
            result["output_record_types"] = ["backtranslation"]
        return result

    monkeypatch.setattr(checker.contracts, "operation", widened)
    schema = m.contracts.read_json(MODULE / "backtranslate-draft.schema.json")
    assert schema["properties"]["records"] == {"type": "array", "maxItems": 0, "items": False}
    checker.validator("backtranslate")  # the maxItems-0 branch accepts an empty whitelist


# --- characterization tests: gaps CONFORMANCE.md marks 未接入 ------------------------------------

def test_gap_e04_overclaimed_independence_is_not_caught(checker):
    """KNOWN GAP (CONFORMANCE E04). AGENT.md §2 says a draft may only declare UNESTABLISHED,
    but nothing enforces it: the draft $refs the full v0.0 payload, whose enum allows all three
    values. If this ever fails, add the rule, drop `unchecked.independence` accordingly and
    update CONFORMANCE E04 plus validation-report.json in the same change."""
    value = draft("argument", records=[
        axis(review=review_context("INDEPENDENTLY_ATTESTED"), result="SUPPORTED",
             support_refs=[ref("argument-snapshot")])])
    accepted(checker, "argument", value)


def test_gap_e08_business_root_conditionals_are_not_inherited(checker):
    """KNOWN GAP (CONFORMANCE E08). axis-assessment's root allOf requires support_refs when
    result is SUPPORTED, and relation-assessment's requires witness_refs when ACCEPTED. The
    draft only $refs '#/properties/payload', so neither gate applies; only frontier-item's is
    re-implemented in the checker."""
    accepted(checker, "argument", draft("argument", records=[
        axis(result="SUPPORTED", support_refs=[])]))
    accepted(checker, "reuse", draft("reuse", records=[
        relation(outcome="ACCEPTED", witness_refs=[])]))


def test_gap_e06_math_to_formal_without_any_backtranslation_ref(checker):
    """KNOWN GAP (CONFORMANCE E06). The Task-level rule fires only when target_refs name a
    formal family; a MATH_TO_FORMAL assessment whose task targets are not formal passes with
    an empty backtranslation_refs."""
    value = draft("alignment", records=[alignment(target_refs=[ref("math-claim", "two")])])
    supplied = task(value, "review.alignment", expected_record_types=["alignment-assessment"])
    supplied["target_refs"] = [ref("math-claim"), ref("math-claim", "two")]
    accepted(checker, "alignment", value, supplied)


def test_gap_e13_producer_closing_its_own_challenge_is_not_caught(checker):
    """KNOWN GAP (CONFORMANCE E13). The draft layer cannot see principals at all; the Result-level
    comparison lives in ../validate.py and this checker never inspects a Result."""
    disposition = record("challenge-disposition", challenge_ref=ref("challenge"),
                         response="The producer rewrote step 3.",
                         response_refs=[ref("argument-snapshot")],
                         review=review_context(reviewed="challenge"), outcome="RESOLVED",
                         replacement_ref=None, reason="Producer states the objection is addressed.")
    accepted(checker, "argument", draft("argument", records=[disposition]))
    assert "result" in checker.check("argument", draft("argument"))["unchecked"]


# --- CLI: three exit codes, and no writes --------------------------------------------------------

def run_cli(*args):
    return subprocess.run([sys.executable, "-B", str(MODULE / "check_interfaces.py"), *args],
                          capture_output=True, text=True)


def snapshot(directory):
    return {p: p.stat().st_mtime_ns for p in sorted(directory.rglob("*")) if p.is_file()}


def test_cli_exit_zero_on_the_positive_fixture():
    before = snapshot(MODULE)
    done = run_cli("--kind", "backtranslate", "--input", str(CONFORMANCE / "backtranslate-draft.json"),
                   "--task", str(CONFORMANCE / "task-backtranslate.json"), "--require-task")
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)["checks_passed"] is True
    assert snapshot(MODULE) == before


def test_cli_exit_one_on_the_leak_fixture():
    done = run_cli("--kind", "backtranslate", "--input", str(CONFORMANCE / "backtranslate-draft.json"),
                   "--task", str(CONFORMANCE / "task-backtranslate-leak.json"))
    assert done.returncode == 1, done.stderr
    report = json.loads(done.stdout)
    assert report["checks_passed"] is False
    assert {e["code"] for e in report["errors"]} == {"TASK_CONTRACT"}


def test_cli_exit_two_on_unreadable_input(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("not json")
    done = run_cli("--kind", "scope", "--input", str(broken))
    assert done.returncode == 2, done.stderr
    report = json.loads(done.stdout)
    assert report["errors"][0]["code"] == "INPUT_ERROR"
    assert "interface" in report["unchecked"]
