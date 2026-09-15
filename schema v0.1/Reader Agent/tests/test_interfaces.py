"""Synthetic interface fixtures only: no historical cases, writes, model calls or external execution."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location(
    "reader_interfaces", Path(__file__).resolve().parents[1] / "check_interfaces.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

HASH = "sha256:" + "a" * 64
OTHER_HASH = "sha256:" + "b" * 64


def ref(name, suffix="one", content_hash=HASH):
    return dict(record_type=f"agtxiv.v3.{name}/0.0.0", record_id=f"{name}:{suffix}",
                revision=1, content_hash=content_hash)


_DEFAULT_TARGET = object()


def explanation(target=_DEFAULT_TARGET, **overrides):
    target = ref("math-claim") if target is _DEFAULT_TARGET else target
    item = dict(target_ref=target, audience="Reader with undergraduate linear algebra",
                text="The claim fixes one exact statement; its abbreviation is expanded here.",
                basis_refs=[target, ref("definition")],
                gaps=["target=math-claim:one; missing=regime; checked=payload; next=semantic-context"])
    item.update(overrides)
    return item


def draft(**overrides):
    value = dict(draft_version="1.0", attribution="UNESTABLISHED", explanations=[explanation()],
                 records=[], open_items=[], follow_up_requests=[])
    value.update(overrides)
    return value


def task(value, operation="reader.explain", **overrides):
    refs = {m.contracts.ref_key(r): r for _, r in m.walk(value) if set(r) == m.REF_KEYS}
    targets = [item["target_ref"] for item in value.get("explanations", []) if item["target_ref"] is not None]
    supplied = dict(contract_version="0.1.0", task_id="synthetic", agent=operation.split(".")[0],
                    operation=operation, brief="Explain this claim to a first-year graduate reader",
                    target_refs=list({m.contracts.ref_key(r): r for r in targets}.values()),
                    input_refs=deepcopy(list(refs.values())), input_artifacts=[], depends_on=[],
                    expected_record_types=[],
                    limits=dict(max_attempts=1, max_seconds=1, max_cost_units=0, no_progress_limit=1),
                    acceptance="DELIVERY", exclusions=[], capabilities=["records.read", "reader.explain"])
    supplied.update(overrides)
    return supplied


@pytest.fixture(scope="module")
def checker():
    return m.InterfaceChecker()


def rejected(checker, value, code, supplied_task=None):
    report = checker.check("explanation", value, supplied_task)
    assert not report["checks_passed"]
    assert code in {e["code"] for e in report["errors"]}, report
    return report


def test_positive_without_task_and_read_only(checker):
    value = draft()
    before = deepcopy(value)
    report = checker.check("explanation", value)
    assert report["checks_passed"], report
    assert value == before
    assert "task" in report["unchecked"]
    assert report["checked"][0] == "no_business_records"


def test_positive_with_task_and_read_only(checker):
    value = draft()
    supplied = task(value)
    before = deepcopy((value, supplied))
    report = checker.check("explanation", value, supplied)
    assert report["checks_passed"], report
    assert (value, supplied) == before
    assert "task" not in report["unchecked"]
    assert "task_exact_refs_and_target_coverage" in report["checked"]


def test_unchecked_map_is_copied_per_report(checker):
    first = checker.check("explanation", draft())
    first["unchecked"]["injected"] = "must not leak"
    assert "injected" not in checker.check("explanation", draft())["unchecked"]


# --- no business records --------------------------------------------------------------------

def test_records_array_with_a_business_record_is_smuggling(checker):
    value = draft(records=[{"record_type": "agtxiv.v3.scientific-claim/0.0.0", "payload": {"statement": "x"}}])
    report = rejected(checker, value, "SMUGGLED_RECORD")
    assert "SCHEMA" in {e["code"] for e in report["errors"]}


def test_payload_anywhere_is_smuggling(checker):
    value = draft()
    value["explanations"][0]["basis_refs"][0] = dict(ref("math-claim"), payload={"statement": "x"})
    rejected(checker, value, "SMUGGLED_RECORD")


def test_record_type_outside_an_exact_ref_is_smuggling(checker):
    value = draft()
    value["explanations"][0]["basis_refs"][0] = {"record_type": "agtxiv.v3.math-claim/0.0.0", "statement": "x"}
    rejected(checker, value, "SMUGGLED_RECORD")


def test_empty_records_array_is_the_only_accepted_value(checker):
    assert checker.check("explanation", draft(records=[]))["checks_passed"]


# --- schema closure -------------------------------------------------------------------------

@pytest.mark.parametrize("location", ["top", "explanation"])
def test_unknown_field_rejected(checker, location):
    value = draft()
    if location == "top":
        value["verdict"] = "SUPPORTED"
    else:
        value["explanations"][0]["confidence"] = 0.9
    rejected(checker, value, "SCHEMA")


@pytest.mark.parametrize("field", ["record_id", "revision", "created_at", "producer", "content_hash"])
def test_model_cannot_add_envelope_fields(checker, field):
    rejected(checker, draft(**{field: "whatever"}), "SCHEMA")


def test_draft_cannot_declare_independence(checker):
    # The enum has no independent value at all: only the host can establish independence (I1, I2).
    rejected(checker, draft(attribution="INDEPENDENTLY_ATTESTED"), "SCHEMA")
    assert checker.check("explanation", draft(attribution="SELF_CHECK"))["checks_passed"]


# --- explanation interface rules ------------------------------------------------------------

def test_empty_delivery_rejected(checker):
    rejected(checker, draft(explanations=[]), "EMPTY_EXPLANATION")
    rejected(checker, draft(explanations=[], open_items=["   "]), "EMPTY_EXPLANATION")
    assert checker.check("explanation", draft(
        explanations=[], open_items=["target=math-claim:one; missing=record; checked=inputs; next=capture"]
    ))["checks_passed"]


@pytest.mark.parametrize("field", ["text", "audience"])
def test_blank_text_rejected(checker, field):
    value = draft()
    value["explanations"][0][field] = "   "
    rejected(checker, value, "BLANK_TEXT")


def test_ungrounded_explanation_must_declare_its_gap(checker):
    value = draft(explanations=[explanation(target=None, basis_refs=[], gaps=[])])
    rejected(checker, value, "UNGROUNDED_EXPLANATION")
    value = draft(explanations=[explanation(target=None, basis_refs=[], gaps=["  "])])
    rejected(checker, value, "UNGROUNDED_EXPLANATION")
    value = draft(explanations=[explanation(
        target=None, basis_refs=[], gaps=["target=brief; missing=any record; checked=inputs; next=capture"])])
    assert checker.check("explanation", value)["checks_passed"]


def test_same_identity_under_two_hashes_rejected(checker):
    value = draft()
    value["explanations"][0]["basis_refs"] = [ref("math-claim"), ref("math-claim", content_hash=OTHER_HASH)]
    rejected(checker, value, "INCONSISTENT_REF")


def test_citing_the_explained_record_as_its_own_basis_is_allowed(checker):
    value = draft(explanations=[explanation(basis_refs=[ref("math-claim")])])
    assert checker.check("explanation", value)["checks_passed"]


# --- whitelist and schema drift -------------------------------------------------------------

def test_empty_output_whitelist_drift_refuses_to_run(checker, monkeypatch):
    agent, operation = checker.contracts.operations["reader.explain"]
    widened = deepcopy(operation)
    widened["output_record_types"] = ["frontier-item"]
    monkeypatch.setitem(checker.contracts.operations, "reader.explain", (agent, widened))
    with pytest.raises(m.contracts.InterfaceError):
        checker.validator("explanation")


@pytest.mark.parametrize("change", ["max_items", "items"])
def test_records_shape_drift_refuses_to_run(checker, monkeypatch, change):
    schema = m.contracts.read_json(m.DIRECTORY / "explanation-draft.schema.json")
    if change == "max_items":
        schema["properties"]["records"]["maxItems"] = 10000
    else:
        schema["properties"]["records"]["items"] = {"type": "object"}
    monkeypatch.setattr(m.contracts, "read_json", lambda path: schema)
    with pytest.raises(m.contracts.InterfaceError):
        checker.validator("explanation")


# --- follow-up requests ---------------------------------------------------------------------

def follow_up(**overrides):
    request = dict(agent="review", operation="review.argument", input_refs=[ref("argument-snapshot")],
                   reason="target=math-claim:one; need=argument review; purpose=close the open obligation")
    request.update(overrides)
    return request


def test_follow_up_positive(checker):
    assert checker.check("explanation", draft(follow_up_requests=[follow_up()]))["checks_passed"]


def test_follow_up_agent_operation_pair_must_exist(checker):
    rejected(checker, draft(follow_up_requests=[follow_up(agent="reader", operation="review.argument")]),
             "FOLLOW_UP_OPERATION")
    rejected(checker, draft(follow_up_requests=[follow_up(operation="reader.approve")]), "FOLLOW_UP_OPERATION")


def test_follow_up_input_family_is_bounded(checker):
    rejected(checker, draft(follow_up_requests=[follow_up(
        agent="delta", operation="delta.compare", input_refs=[ref("source-span")])]), "FOLLOW_UP_INPUT")


def test_follow_up_backtranslate_only_sees_formal_environment(checker):
    rejected(checker, draft(follow_up_requests=[follow_up(
        operation="review.backtranslate", input_refs=[ref("math-claim")])]), "FOLLOW_UP_INPUT")
    assert checker.check("explanation", draft(follow_up_requests=[follow_up(
        operation="review.backtranslate", input_refs=[ref("formal-environment")])]))["checks_passed"]


def test_follow_up_refs_must_be_consistent(checker):
    rejected(checker, draft(follow_up_requests=[follow_up(input_refs=[
        ref("argument-snapshot"), ref("argument-snapshot", content_hash=OTHER_HASH)])]), "FOLLOW_UP_INPUT")


# --- Task layer -----------------------------------------------------------------------------

def test_task_required_mode(checker):
    report = checker.check("explanation", draft(), None, require_task=True)
    assert not report["checks_passed"]
    assert "TASK_REQUIRED" in {e["code"] for e in report["errors"]}


def test_blank_brief_rejected(checker):
    value = draft()
    rejected(checker, value, "BLANK_BRIEF", task(value, brief="   "))


def test_task_cannot_predeclare_business_output(checker):
    value = draft()
    rejected(checker, value, "NONEMPTY_EXPECTED_TYPES", task(value, expected_record_types=["frontier-item"]))


def test_reader_task_cannot_carry_an_evidence_gate(checker):
    value = draft()
    report = rejected(checker, value, "EVIDENCE_GATE_ON_READER", task(value, acceptance="EVIDENCE"))
    # contracts.task() independently refuses it, because an EVIDENCE task must name business outputs.
    assert "TASK_CONTRACT" in {e["code"] for e in report["errors"]}


def test_task_operation_must_be_reader_explain(checker):
    value = draft()
    rejected(checker, value, "TASK_CONTRACT", task(value, agent="planner", operation="planner.propose"))


def test_task_capability_escalation_rejected(checker):
    value = draft()
    rejected(checker, value, "TASK_CONTRACT", task(value, capabilities=["records.read", "candidates.propose"]))


def test_invisible_ref_rejected(checker):
    value = draft()
    supplied = task(value)
    value["explanations"][0]["basis_refs"].append(ref("definition", "unseen"))
    rejected(checker, value, "INVISIBLE_REF", supplied)


def test_every_task_target_must_be_explained(checker):
    value = draft()
    supplied = task(value)
    supplied["input_refs"].append(ref("argument-snapshot"))
    supplied["target_refs"].append(ref("argument-snapshot"))
    rejected(checker, value, "UNEXPLAINED_TARGET", supplied)


def test_task_contract_failure_skips_bindings(checker):
    value = draft()
    report = checker.check("explanation", value, {})
    assert "TASK_CONTRACT" in {e["code"] for e in report["errors"]}
    assert "task_bindings" in report["unchecked"]
    assert "task_exact_refs_and_target_coverage" not in report["checked"]


def test_empty_task_inputs_are_allowed_for_reader(checker):
    value = draft(explanations=[explanation(
        target=None, basis_refs=[], gaps=["target=brief; missing=any record; checked=inputs; next=capture"])])
    supplied = task(value)
    assert supplied["input_refs"] == [] and supplied["target_refs"] == []
    assert checker.check("explanation", value, supplied)["checks_passed"]


# --- declared blind spot --------------------------------------------------------------------

def test_known_gap_opinion_text_passes(checker):
    """KNOWN GAP, asserted so it fails loudly when covered.

    Nothing in this checker reads explanation prose, so an opinion written as if it were support
    passes every layer. This is declared in UNCHECKED['opinion_as_support'] and in
    validation-report.json; CONFORMANCE E07 names the human layer that is the actual defence.
    When a future check catches this, update both of those and this test together.
    """
    value = draft(explanations=[explanation(
        text="I checked the argument and it looks correct, so the result can be treated as verified.",
        gaps=[])])
    report = checker.check("explanation", value, task(value))
    assert report["checks_passed"]
    assert "opinion_as_support" in report["unchecked"]


# --- CLI ------------------------------------------------------------------------------------

def listing():
    return {path: path.stat().st_mtime_ns for path in sorted(m.DIRECTORY.rglob("*")) if path.is_file()}


def test_cli_exit_codes_and_no_file_writes(monkeypatch, capsys):
    read = m.contracts.read_bytes
    before = listing()
    for raw, status in [(json.dumps(draft()).encode(), 0), (b"{}", 1), (b'{"x":1,"x":2}', 2)]:
        monkeypatch.setattr(m.contracts, "read_bytes",
                            lambda path, raw=raw: raw if path == Path("synthetic.json") else read(path))
        assert m.main(["--kind", "explanation", "--input", "synthetic.json"]) == status
        report = json.loads(capsys.readouterr().out)
        assert report["kind"] == "explanation"
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
        assert m.main(["--kind", "explanation", "--input", "synthetic.json", "--task", "task.json"]) == status
        assert json.loads(capsys.readouterr().out)["checks_passed"] == (status == 0)
