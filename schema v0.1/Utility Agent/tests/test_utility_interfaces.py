"""Synthetic Utility request/receipt fixtures only: no command runs, no writes, no external execution.

Every rule check_interfaces.py actually enforces gets one positive and one negative case, and every
gap CONFORMANCE.md marks "未接入" gets a test that asserts the gap is still open. Those gap tests are
expected to FAIL LOUDLY once coverage is added, so that check_interfaces.py's `unchecked` map and
validation-report.json's not_implemented_or_not_established are updated in the same change.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

sys.dont_write_bytecode = True

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parents[1]
CONFORMANCE = MODULE_DIR / "conformance"

_spec = importlib.util.spec_from_file_location("utility_interfaces", MODULE_DIR / "check_interfaces.py")
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


# --- constructors (plain functions, not fixtures) -------------------------------------------------

def ref(name, suffix="one", fill="a"):
    return {"record_type": f"agtxiv.v3.{name}/0.0.0", "record_id": f"{name}:{suffix}",
            "revision": 1, "content_hash": "sha256:" + fill * 64}


def artifact_ref(suffix="one", fill="b"):
    return {"artifact_id": f"artifact:{suffix}", "sha256": "sha256:" + fill * 64,
            "byte_size": 1, "media_type": "text/plain"}


def execution(**overrides):
    value = {"command": ["fetch-source", "--exact"], "exit_code": 0,
             "started_at": "2026-09-16T00:00:00Z", "finished_at": "2026-09-16T00:00:01Z",
             "tool_versions": {"fetch-source": "0.0.0"}, "host_mode": "EXECUTED"}
    value.update(overrides)
    return value


def receipt(outputs=(), artifacts=(), open_items=(), follow_ups=(), exec_value="default"):
    return {"receipt_version": "1.0", "request_hash": "sha256:" + "f" * 64,
            "execution": execution() if exec_value == "default" else exec_value,
            "outputs": list(outputs), "artifacts": list(artifacts),
            "open_items": list(open_items), "follow_up_requests": list(follow_ups)}


def follow_up(agent, operation, input_refs=()):
    return {"agent": agent, "operation": operation, "input_refs": list(input_refs),
            "reason": "target=packet:one; need=an exact environment; purpose=fix the import gap"}


def review_context():
    return {"reviewed_refs": [ref("formalization-attempt")],
            "producer_principal_ids": ["agent:formalization"], "independence": "UNESTABLISHED",
            "conflicts": [], "method": "synthetic fixture", "evidence_refs": []}


def declaration(is_axiom=False):
    return {"name": "Synthetic.target", "statement": "forall n, P n",
            "source_artifact": artifact_ref("source", "c"), "is_axiom": is_axiom,
            "axioms": ["propext"], "dependencies": []}


def formal_check(outcome="KERNEL_CHECKED", declarations=None, placeholders=(), exit_code=0):
    return {"record_type": "agtxiv.v3.formal-check/0.0.0", "payload": {
        "packet_ref": ref("formalization-packet"), "attempt_ref": ref("formalization-attempt"),
        "environment_ref": ref("formal-environment"), "review": review_context(),
        "outcome": outcome,
        "built_declarations": [declaration()] if declarations is None else declarations,
        "placeholder_findings": list(placeholders),
        "logs": [artifact_ref("log", "d")], "exit_code": exit_code}}


def fixture_json(name):
    return json.loads((CONFORMANCE / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def checker():
    return m.InterfaceChecker()


def accepted(checker, kind, value):
    report = checker.check(kind, value)
    assert report["checks_passed"], report
    assert not report["errors"], report
    return report


def rejected(checker, kind, value, code):
    report = checker.check(kind, value)
    assert not report["checks_passed"], report
    assert code in {error["code"] for error in report["errors"]}, report
    return report


# --- positive path and read-only behaviour --------------------------------------------------------

@pytest.mark.parametrize("kind,name", [
    ("request", "request-capture.json"),
    ("capture", "capture-receipt-diagnostic.json"),
])
def test_committed_fixtures_are_accepted(checker, kind, name):
    accepted(checker, kind, fixture_json(name))


@pytest.mark.parametrize("kind,name,code", [
    ("request", "request-capture-rejected.json", "REQUEST_INPUT"),
    ("project", "project-receipt-diagnostic-output.json", "DIAGNOSTIC_OUTPUT"),
])
def test_committed_negative_fixtures_are_rejected(checker, kind, name, code):
    rejected(checker, kind, fixture_json(name), code)


def test_check_does_not_mutate_its_input(checker):
    value = fixture_json("capture-receipt-diagnostic.json")
    before = copy.deepcopy(value)
    checker.check("capture", value)
    assert value == before


def test_every_report_carries_the_full_blind_spot_map(checker):
    report = checker.check("capture", fixture_json("capture-receipt-diagnostic.json"))
    assert set(m.UNCHECKED) <= set(report["unchecked"])
    assert report["unchecked"] is not m.UNCHECKED
    assert report["checked"] == ["schema", "receipt_outputs_and_diagnostics",
                                 "follow_up_agent_operation_pairs", "follow_up_input_refs_and_families"]


def test_request_report_lists_only_the_request_layers(checker):
    report = checker.check("request", fixture_json("request-capture.json"))
    assert report["checked"] == ["schema", "request_operation_and_inputs"]


def test_schema_failure_stops_dependent_layers(checker):
    report = checker.check("capture", {"receipt_version": "1.0"})
    assert not report["checks_passed"]
    assert {error["code"] for error in report["errors"]} == {"SCHEMA"}
    assert "interface_rules_and_task" in report["unchecked"]


# --- request layer --------------------------------------------------------------------------------

def test_request_rejects_an_input_family_outside_the_operation_whitelist(checker):
    value = fixture_json("request-capture.json")
    value["input_refs"] = [ref("math-claim")]
    rejected(checker, "request", value, "REQUEST_INPUT")


def test_request_accepts_the_three_general_context_families(checker):
    value = fixture_json("request-capture.json")
    value["operation"] = "utility.register-plan"
    value["expected_record_types"] = ["agentization-plan"]
    value["input_refs"] = [ref("source-snapshot"), ref("processing-profile"), ref("authority-policy")]
    accepted(checker, "request", value)


def test_request_rejects_an_output_type_the_operation_cannot_produce(checker):
    value = fixture_json("request-capture.json")
    value["operation"] = "utility.persist"
    value["input_refs"] = [ref("source-snapshot")]
    value["expected_record_types"] = ["source-snapshot"]
    rejected(checker, "request", value, "REQUEST_OUTPUT")


def test_persist_request_must_expect_nothing(checker):
    value = fixture_json("request-capture.json")
    value["operation"] = "utility.persist"
    value["input_refs"] = [ref("source-snapshot")]
    value["expected_record_types"] = []
    accepted(checker, "request", value)


def test_request_rejects_same_identity_with_a_different_hash(checker):
    value = fixture_json("request-capture.json")
    value["input_refs"] = [ref("source-request", fill="a"), ref("source-request", fill="b")]
    rejected(checker, "request", value, "REQUEST_REFS")


def test_expected_record_types_must_be_short_names(checker):
    value = fixture_json("request-capture.json")
    value["expected_record_types"] = ["agtxiv.v3.source-acquisition/0.0.0"]
    rejected(checker, "request", value, "SCHEMA")


def test_request_rejects_an_unregistered_operation_name(checker):
    value = fixture_json("request-capture.json")
    value["operation"] = "utility.run"
    rejected(checker, "request", value, "SCHEMA")


def test_request_rejects_an_environment_ref_of_the_wrong_family(checker):
    value = fixture_json("request-capture.json")
    value["parameters"] = dict(value["parameters"], environment_ref=ref("source-snapshot"))
    rejected(checker, "request", value, "SCHEMA")


def test_request_rejects_an_unknown_top_level_field(checker):
    value = fixture_json("request-capture.json")
    value["approved"] = True
    rejected(checker, "request", value, "SCHEMA")


# --- receipt layer --------------------------------------------------------------------------------

def test_diagnostic_receipt_may_not_claim_business_outputs(checker):
    value = receipt(outputs=[formal_check()], exec_value=None)
    rejected(checker, "formal-check", value, "DIAGNOSTIC_OUTPUT")


def test_offline_diagnostic_host_mode_may_not_claim_business_outputs(checker):
    value = receipt(outputs=[formal_check()], exec_value=execution(host_mode="OFFLINE_DIAGNOSTIC"))
    rejected(checker, "formal-check", value, "DIAGNOSTIC_OUTPUT")


def test_executed_receipt_may_carry_its_whitelisted_output(checker):
    accepted(checker, "formal-check", receipt(outputs=[formal_check()]))


def test_receipt_stating_nothing_is_rejected(checker):
    rejected(checker, "persist", receipt(), "EMPTY_RECEIPT")


def test_blank_open_items_do_not_rescue_an_empty_receipt(checker):
    value = receipt(exec_value=None)
    value["open_items"] = ["   "]
    rejected(checker, "persist", value, "EMPTY_RECEIPT")


def test_persist_receipt_delivering_an_artifact_is_accepted(checker):
    accepted(checker, "persist", receipt(artifacts=[{"path": "txn.json", "sha256": "sha256:" + "e" * 64,
                                                     "byte_size": 12, "media_type": "application/json"}]))


def test_persist_receipt_may_not_carry_business_outputs(checker):
    value = receipt(outputs=[{"record_type": "agtxiv.v3.status-view/0.0.0", "payload": {}}])
    rejected(checker, "persist", value, "SCHEMA")


def test_receipt_may_not_carry_a_type_outside_its_operation_whitelist(checker):
    value = receipt(outputs=[{"record_type": "agtxiv.v3.release-manifest/0.0.0", "payload": {}}])
    rejected(checker, "project", value, "SCHEMA")


def test_receipt_may_not_carry_host_envelope_fields(checker):
    value = receipt(artifacts=[], open_items=["target=x; missing=y; checked=z; next=w"])
    value["producer"] = {"principal_id": "agent:utility"}
    rejected(checker, "capture", value, "SCHEMA")


# --- follow-up layer ------------------------------------------------------------------------------

def test_follow_up_rejects_an_unregistered_agent_operation_pair(checker):
    value = receipt(open_items=["target=x; missing=y; checked=z; next=w"],
                    follow_ups=[follow_up("utility", "proof.expand")])
    rejected(checker, "capture", value, "FOLLOW_UP_OPERATION")


def test_follow_up_accepts_a_registered_pair_with_allowed_inputs(checker):
    value = receipt(open_items=["target=x; missing=y; checked=z; next=w"],
                    follow_ups=[follow_up("review", "review.scope", [ref("inventory-discovery")])])
    accepted(checker, "capture", value)


def test_follow_up_rejects_an_input_family_the_target_cannot_read(checker):
    value = receipt(open_items=["target=x; missing=y; checked=z; next=w"],
                    follow_ups=[follow_up("review", "review.scope", [ref("release-certificate")])])
    rejected(checker, "capture", value, "FOLLOW_UP_INPUT")


def test_follow_up_to_blind_backtranslation_allows_only_formal_environment(checker):
    allowed = receipt(open_items=["target=x; missing=y; checked=z; next=w"],
                      follow_ups=[follow_up("review", "review.backtranslate", [ref("formal-environment")])])
    accepted(checker, "capture", allowed)
    leaked = receipt(open_items=["target=x; missing=y; checked=z; next=w"],
                     follow_ups=[follow_up("review", "review.backtranslate", [ref("math-claim")])])
    rejected(checker, "capture", leaked, "FOLLOW_UP_INPUT")


def test_blind_backtranslation_does_not_get_the_general_context_permission(checker):
    value = receipt(open_items=["target=x; missing=y; checked=z; next=w"],
                    follow_ups=[follow_up("review", "review.backtranslate", [ref("processing-profile")])])
    rejected(checker, "capture", value, "FOLLOW_UP_INPUT")


def test_follow_up_rejects_same_identity_with_a_different_hash(checker):
    value = receipt(open_items=["target=x; missing=y; checked=z; next=w"],
                    follow_ups=[follow_up("review", "review.scope",
                                          [ref("inventory-discovery", fill="a"),
                                           ref("inventory-discovery", fill="b")])])
    rejected(checker, "capture", value, "FOLLOW_UP_INPUT")


# --- schema-versus-agents.json drift guard (exit 2 class) -----------------------------------------

def test_output_whitelist_drift_raises_instead_of_reporting_an_error():
    fresh = m.InterfaceChecker()
    real = fresh.contracts.operation

    def widened(agent, operation):
        value = dict(real(agent, operation))
        if operation == "utility.project":
            value["output_record_types"] = ["status-view", "impact-analysis"]
        return value

    fresh.contracts.operation = widened
    with pytest.raises(m.contracts.InterfaceError, match="whitelist mismatch"):
        fresh.validator("project")


def test_payload_ref_must_be_verbatim():
    fresh = m.InterfaceChecker()
    real_schema = m.contracts.read_json(MODULE_DIR / "project-receipt.schema.json")
    mutated = copy.deepcopy(real_schema)
    mutated["properties"]["outputs"]["items"]["properties"]["payload"] = {
        "allOf": [mutated["properties"]["outputs"]["items"]["properties"]["payload"]]}
    original = m.contracts.read_json
    try:
        m.contracts.read_json = lambda path: copy.deepcopy(mutated)
        with pytest.raises(m.contracts.InterfaceError, match="directly reference"):
            fresh.validator("project")
    finally:
        m.contracts.read_json = original


def test_every_receipt_schema_matches_its_agents_json_whitelist(checker):
    for kind, operation in m.OPERATIONS.items():
        checker.validator(kind)  # raises InterfaceError on any drift
        expected = checker.contracts.operation(m.AGENT, operation)["output_record_types"]
        schema = m.contracts.read_json(MODULE_DIR / (m.SCHEMAS[kind] + ".schema.json"))
        items = schema["properties"]["outputs"].get("items")
        if items is False:
            assert expected == []
        else:
            branches = items.get("oneOf") or [items]
            assert {branch["properties"]["record_type"]["const"] for branch in branches} == {
                f"agtxiv.v3.{name}/0.0.0" for name in expected}


# --- CLI: three exit codes, and no files written ---------------------------------------------------

def run_cli(*args):
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run([sys.executable, "-B", str(MODULE_DIR / "check_interfaces.py"), *args],
                          cwd=REPO_ROOT, env=environment, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, check=False)


def directory_state():
    return {str(path.relative_to(MODULE_DIR)): path.stat().st_mtime_ns
            for path in sorted(MODULE_DIR.rglob("*")) if path.is_file()}


def test_cli_exit_codes_and_no_writes():
    before = directory_state()
    assert run_cli("--kind", "request", "--input",
                   str(CONFORMANCE / "request-capture.json")).returncode == 0
    assert run_cli("--kind", "request", "--input",
                   str(CONFORMANCE / "request-capture-rejected.json")).returncode == 1
    assert run_cli("--kind", "capture", "--input",
                   str(MODULE_DIR / "AGENT.md")).returncode == 2
    assert directory_state() == before
    assert not list(MODULE_DIR.rglob("__pycache__"))


def test_cli_input_error_report_declares_its_blind_spot():
    completed = run_cli("--kind", "capture", "--input", str(MODULE_DIR / "AGENT.md"))
    report = json.loads(completed.stdout)
    assert report["errors"][0]["code"] == "INPUT_ERROR"
    assert "interface" in report["unchecked"]
    assert report["checks_passed"] is False


# --- blind-spot fixation: these assert the gaps CONFORMANCE.md records as 未接入 -------------------

def test_gap_execution_facts_are_never_verified(checker):
    """CONFORMANCE E01: an EXECUTED receipt with no command and no exit code still passes."""
    value = receipt(outputs=[formal_check()], exec_value=execution(command=[], exit_code=None))
    accepted(checker, "formal-check", value)


def test_gap_timestamps_may_run_backwards(checker):
    """CONFORMANCE E01: finished_at before started_at is not checked."""
    value = receipt(outputs=[formal_check()],
                    exec_value=execution(started_at="2026-09-16T00:00:09Z",
                                         finished_at="2026-09-16T00:00:01Z"))
    accepted(checker, "formal-check", value)


def test_gap_kernel_checked_success_gate_does_not_reach_a_receipt(checker):
    """CONFORMANCE E09: the v0.0 root-level allOf is not pulled in by #/properties/payload."""
    value = receipt(outputs=[formal_check(declarations=[declaration(is_axiom=True)],
                                          placeholders=["sorry at line 3"], exit_code=7)])
    accepted(checker, "formal-check", value)


def test_gap_kernel_checked_gate_does_fire_on_a_fully_assembled_record(checker):
    """The same payload is rejected once the host validates it against the whole business schema."""
    payload = formal_check(declarations=[declaration(is_axiom=True)],
                           placeholders=["sorry at line 3"], exit_code=7)["payload"]
    validator = checker.contracts.base.validators["agtxiv.v3.formal-check/0.0.0"]
    messages = [error.message for error in validator.iter_errors({"payload": payload})]
    assert "False was expected" in messages
    assert "0 was expected" in messages


def test_gap_acquired_without_bytes_passes_at_the_receipt_layer(checker):
    """CONFORMANCE E10: source-acquisition ACQUIRED requires artifacts only at record level."""
    value = receipt(outputs=[{"record_type": "agtxiv.v3.source-acquisition/0.0.0", "payload": {
        "request_ref": ref("source-request"), "outcome": "ACQUIRED",
        "started_at": "2026-09-16T00:00:00Z", "finished_at": "2026-09-16T00:00:01Z",
        "artifacts": [], "final_uri": None, "transport_evidence": [],
        "reason": "nothing was actually downloaded"}}])
    accepted(checker, "capture", value)


def test_gap_certified_with_failed_checks_passes_at_the_receipt_layer(checker):
    """CONFORMANCE E10: release-certificate CERTIFIED requires empty failed_checks only at record level."""
    value = receipt(outputs=[{"record_type": "agtxiv.v3.release-certificate/0.0.0", "payload": {
        "manifest_ref": ref("release-manifest"), "audit_ref": ref("release-audit"),
        "checks": ["json schema"], "outcome": "CERTIFIED",
        "failed_checks": ["independence was never established"]}}])
    accepted(checker, "certify", value)


def test_gap_release_order_and_prerequisites_are_not_checked(checker):
    """CONFORMANCE E11: a paper-release naming three arbitrary refs is accepted."""
    value = receipt(outputs=[{"record_type": "agtxiv.v3.paper-release/0.0.0", "payload": {
        "manifest_ref": ref("release-manifest"), "audit_ref": ref("release-audit"),
        "certificate_ref": ref("release-certificate"), "release_name": "synthetic-v1",
        "publication_uri": None}}])
    accepted(checker, "export", value)


def test_gap_allowed_commands_are_not_parsed(checker):
    """CONFORMANCE E14: the checker only bounds string length and uniqueness."""
    value = fixture_json("request-capture.json")
    value["allowed_commands"] = ["fetch-source; rm -rf /"]
    accepted(checker, "request", value)


def test_gap_request_is_never_bound_to_a_task(checker):
    """CONFORMANCE E13: there is no --task mode, so no INVISIBLE_REF or UNDECLARED_OUTPUT layer."""
    completed = run_cli("--kind", "request", "--input", str(CONFORMANCE / "request-capture.json"),
                        "--task", str(CONFORMANCE / "request-capture.json"))
    assert completed.returncode == 2
    assert "unrecognized arguments: --task" in completed.stdout
    value = fixture_json("request-capture.json")
    value["task_id"] = "a-task-that-does-not-exist"
    accepted(checker, "request", value)


def test_gap_receipt_output_code_is_unreachable_through_check(checker):
    """CONFORMANCE E08: the schema branch consts already equal the whitelist, and schema errors return early."""
    for kind, operation in m.OPERATIONS.items():
        expected = set(checker.contracts.operation(m.AGENT, operation)["output_record_types"])
        schema = m.contracts.read_json(MODULE_DIR / (m.SCHEMAS[kind] + ".schema.json"))
        items = schema["properties"]["outputs"].get("items")
        branches = [] if items is False else (items.get("oneOf") or [items])
        declared = {branch["properties"]["record_type"]["const"].removeprefix(
            "agtxiv.v3.").removesuffix("/0.0.0") for branch in branches}
        assert declared == expected
    value = receipt(outputs=[{"record_type": "agtxiv.v3.release-manifest/0.0.0", "payload": {}}])
    report = checker.check("project", value)
    assert "RECEIPT_OUTPUT" not in {error["code"] for error in report["errors"]}


def test_gap_request_operation_code_is_unreachable_through_check(checker):
    """CONFORMANCE E05: the request enum equals the registered operation set."""
    schema = m.contracts.read_json(MODULE_DIR / "utility-request.schema.json")
    assert set(schema["properties"]["operation"]["enum"]) == set(m.OPERATIONS.values())
    value = fixture_json("request-capture.json")
    value["operation"] = "utility.run"
    report = checker.check("request", value)
    assert "REQUEST_OPERATION" not in {error["code"] for error in report["errors"]}
