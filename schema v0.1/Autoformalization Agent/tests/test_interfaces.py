"""Synthetic interface fixtures only: no historical cases, writes or Lean execution."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("auto_interfaces", Path(__file__).resolve().parents[1] / "check_interfaces.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def ref(name, suffix="one"):
    return dict(record_type=f"agtxiv.v3.{name}/0.0.0", record_id=f"{name}:{suffix}",
                revision=1, content_hash="sha256:" + "a" * 64)


def record(name, **payload):
    return {"record_type": ref(name)["record_type"], "payload": payload}


def proof():
    return dict(draft_version="1.0", open_items=[], follow_up_requests=[], records=[
        record("argument-node", statement="P", kind="CLAIM", origin="SOURCE", claim_refs=[],
               context_ref=None, definition_refs=[], source_span_refs=[ref("source-span")]),
        record("inference-step", premise_refs=[ref("argument-node", "premise")],
               conclusion_ref=ref("argument-node"), rule="DIRECT", justification="Synthetic step",
               context_ref=None, discharged_context_refs=[], rule_evidence_refs=[])])


def entry(label, parent, role):
    return dict(label=label, parent_label=parent, role=role, node_ref=ref("argument-node"), inference_ref=None)


def view():
    return dict(view_version="1.0", argument_ref=ref("argument-snapshot"), proof_plan_ref=ref("proof-plan"),
                entries=[entry("1", None, "GOAL"), entry("1.10", "1", "QED"), entry("1.9", "1", "STEP")])


def lean():
    return dict(draft_version="1.0", packet_ref=ref("formalization-packet"),
                files=[dict(path="Proof/Main.lean", content="theorem target : True := by sorry")],
                declaration_map=[dict(declaration="target", role="TARGET", code_path="Proof/Main.lean",
                                      local_name=None, node_ref=ref("argument-node"), inference_ref=None)],
                records=[], open_items=[], follow_up_requests=[])


def task(value, operation="proof.expand"):
    required = [ref(n) for n in ({"proof.expand": ["math-claim", "frozen-scope"],
                                "formalization.generate": ["formalization-packet"]}[operation])]
    refs = {m.contracts.ref_key(r): r for r in required}
    refs.update({m.contracts.ref_key(r): r for _, r in m.walk(value) if set(r) == m.REF_KEYS})
    return dict(contract_version="0.1.0", task_id="synthetic", agent=operation.split(".")[0],
                operation=operation, brief="Synthetic interface check", target_refs=[required[0]],
                input_refs=deepcopy(list(refs.values())), input_artifacts=[], depends_on=[],
                expected_record_types=sorted({m.contracts.short_type(r) for r in value.get("records", [])}),
                limits=dict(max_attempts=1, max_seconds=1, max_cost_units=0, no_progress_limit=1),
                acceptance="DELIVERY", exclusions=[], capabilities=[])


@pytest.fixture(scope="module")
def checker():
    return m.InterfaceChecker()


def rejected(checker, kind, value, code, supplied_task=None):
    report = checker.check(kind, value, supplied_task)
    assert not report["checks_passed"]
    assert code in {e["code"] for e in report["errors"]}, report


def test_proof_positive_and_read_only(checker):
    value = proof()
    supplied_task = task(value)
    before = deepcopy((value, supplied_task))
    assert checker.check("proof", value, supplied_task)["checks_passed"]
    assert (value, supplied_task) == before


def test_source_requires_span(checker):
    value = proof()
    value["records"][0]["payload"]["source_span_refs"] = []
    rejected(checker, "proof", value, "SOURCE_SPANS")


def test_conclusion_not_own_premise(checker):
    value = proof()
    p = value["records"][1]["payload"]
    p["premise_refs"] = [p["conclusion_ref"]]
    rejected(checker, "proof", value, "SELF_PREMISE")


def test_discharge_requires_context_and_evidence(checker):
    value = proof()
    p = value["records"][1]["payload"]
    p["rule"] = "ASSUMPTION_DISCHARGE"
    rejected(checker, "proof", value, "DISCHARGE_CONTEXT")
    p["discharged_context_refs"] = [ref("assumption-context")]
    rejected(checker, "proof", value, "RULE_EVIDENCE")
    p["rule_evidence_refs"] = [ref("argument-node", "witness")]
    assert checker.check("proof", value)["checks_passed"]
    p.update(rule="CONTRADICTION", rule_evidence_refs=[])
    rejected(checker, "proof", value, "RULE_EVIDENCE")


@pytest.mark.parametrize("rule", ["CASE_SPLIT", "INDUCTION"])
def test_special_rule_evidence(checker, rule):
    value = proof()
    p = value["records"][1]["payload"]
    p["rule"] = rule
    rejected(checker, "proof", value, "RULE_EVIDENCE")
    p["rule_evidence_refs"] = [ref("argument-node", "witness")]
    assert checker.check("proof", value)["checks_passed"]


@pytest.mark.parametrize("rule,allowed", [
    ("ASSUMPTION_DISCHARGE", True), ("CONTRADICTION", True), ("CASE_SPLIT", True), ("INDUCTION", True),
    ("DIRECT", False), ("MODUS_PONENS", False), ("DEFINITIONAL", False), ("EXTERNAL_RESULT", False),
])
def test_discharge_rule_whitelist(checker, rule, allowed):
    value = proof()
    p = value["records"][1]["payload"]
    p.update(rule=rule, discharged_context_refs=[ref("assumption-context")],
             rule_evidence_refs=[ref("argument-node", "witness")])
    if allowed:
        assert checker.check("proof", value)["checks_passed"]
    else:
        rejected(checker, "proof", value, "INVALID_DISCHARGE_RULE")
        p["discharged_context_refs"] = []
        assert checker.check("proof", value)["checks_passed"]


def test_follow_up_pair(checker):
    value = proof()
    request = dict(agent="proof", operation="proof.expand", input_refs=[], reason="Next step")
    value["follow_up_requests"] = [request]
    assert checker.check("proof", value)["checks_passed"]
    for operation in ("formalization.generate", "proof.invented"):
        request["operation"] = operation
        rejected(checker, "proof", value, "FOLLOW_UP_OPERATION")


@pytest.mark.parametrize("operation,family,allowed", [
    ("review.backtranslate", "formal-environment", True), ("review.backtranslate", "math-claim", False),
    ("review.backtranslate", "processing-profile", False), ("formalization.generate", "argument-node", True),
    ("formalization.generate", "inference-step", True), ("formalization.generate", "source-span", False),
    ("proof.expand", "processing-profile", True),
])
def test_follow_up_input_families(checker, operation, family, allowed):
    value = proof()
    value["follow_up_requests"] = [dict(agent=operation.split(".")[0], operation=operation,
                                      input_refs=[ref(family)], reason="Synthetic follow-up")]
    if allowed:
        assert checker.check("proof", value)["checks_passed"]
    else:
        rejected(checker, "proof", value, "FOLLOW_UP_INPUT")


def test_follow_up_rejects_same_identity_revision_with_conflicting_hash(checker):
    value = lean()
    value["follow_up_requests"] = [dict(agent="proof", operation="proof.expand", reason="Continue",
        input_refs=[ref("math-claim"), dict(ref("math-claim"), content_hash="sha256:" + "b" * 64)])]
    rejected(checker, "lean", value, "FOLLOW_UP_INPUT")


def test_all_nested_refs_are_exact_visible_inputs(checker):
    value = proof()
    value["follow_up_requests"] = [dict(agent="proof", operation="proof.expand",
                                      input_refs=[ref("math-claim")], reason="Continue")]
    supplied_task = task(value)
    for _, reference in m.walk(value):
        if set(reference) == m.REF_KEYS:
            for field, replacement in (("content_hash", "sha256:" + "b" * 64), ("revision", 2)):
                old = reference[field]
                reference[field] = replacement
                # Task fixtures are detached so mutation cannot expand visibility.
                rejected(checker, "proof", value, "INVISIBLE_REF", supplied_task)
                reference[field] = old


def test_outputs_must_be_predeclared(checker):
    value = proof()
    supplied_task = task(value)
    supplied_task["expected_record_types"] = []
    rejected(checker, "proof", value, "UNDECLARED_OUTPUT", supplied_task)


def test_operation_must_match_kind(checker):
    value = dict(draft_version="1.0", records=[], open_items=["Blocked"], follow_up_requests=[])
    rejected(checker, "proof", value, "TASK_CONTRACT", task(value, "formalization.generate"))
    value = lean()
    supplied_task = task({}, "proof.expand")
    rejected(checker, "lean", value, "TASK_CONTRACT", supplied_task)


def test_task_shape_and_contract(checker):
    value = proof()
    for patch in ({"extra": True}, {"capabilities": ["invented"]}, {"agent": "reader"},
                  {"input_refs": [], "target_refs": []}):
        supplied_task = task(value)
        supplied_task.update(patch)
        rejected(checker, "proof", value, "TASK_CONTRACT", supplied_task)


def test_closed_schema_and_business_payload(checker):
    for location in ("top", "wrapper", "payload", "version", "type"):
        value = proof()
        if location == "version":
            value["draft_version"] = "2.0"
        elif location == "type":
            value["records"][0]["record_type"] = ref("formal-check")["record_type"]
        else:
            {"top": value, "wrapper": value["records"][0], "payload": value["records"][0]["payload"]}[location]["extra"] = True
        rejected(checker, "proof", value, "SCHEMA")


def test_schema_mapping_checked_on_load(checker, monkeypatch):
    read = m.contracts.read_json
    for change in ("duplicate", "wrong_ref", "inline"):
        schema = read(m.DIRECTORY / "proof-draft.schema.json")
        branches = schema["properties"]["records"]["items"]["oneOf"]
        if change == "duplicate":
            branches[1] = deepcopy(branches[0])
        else:
            branches[0]["properties"]["payload"] = ({"type": "object"} if change == "inline"
                                                    else branches[1]["properties"]["payload"])
        monkeypatch.setattr(m.contracts, "read_json", lambda path: schema)
        with pytest.raises(m.contracts.InterfaceError):
            checker.validator("proof")


def test_view_numeric_order_and_existing_task_operation(checker):
    value = view()
    assert checker.check("view", value, task(value, "formalization.generate"))["checks_passed"]
    supplied_task = task(value)
    value["entries"][1]["node_ref"] = ref("argument-node", "unregistered")
    rejected(checker, "view", value, "INVISIBLE_REF", supplied_task)


def test_view_labels_parents_and_root(checker):
    for patch, code in [({"label": "1"}, "DUPLICATE_LABEL"), ({"parent_label": "2"}, "MISSING_PARENT"),
                        ({"parent_label": "1.10"}, "PARENT_PATH"), ({"label": "0"}, "SCHEMA"),
                        ({"label": "2", "parent_label": None}, "ROOT_GOAL"), ({"label": "1.9\n"}, "LABEL_PATH")]:
        value = view()
        value["entries"][2].update(patch)
        rejected(checker, "view", value, code)
    value = view()
    value["entries"][0]["role"] = "STEP"
    rejected(checker, "view", value, "ROOT_GOAL")


def test_view_goal_endings_and_non_goal_children(checker):
    value = view()
    value["entries"] += [entry("1.9.1", "1.9", "QED")]
    rejected(checker, "view", value, "NON_GOAL_CHILDREN")
    value["entries"][2]["role"] = "GOAL"
    assert checker.check("view", value)["checks_passed"]
    for index, patch in [(1, {"role": "STEP"}), (3, {"role": "STEP"}),
                         (1, {"node_ref": ref("argument-node", "other")})]:
        changed = deepcopy(value)
        changed["entries"][index].update(patch)
        rejected(checker, "view", changed, "GOAL_QED")


def test_lean_draft_does_not_claim_proof_or_mapping_correct(checker):
    value = lean()
    report = checker.check("lean", value, task(value, "formalization.generate"))
    assert report["checks_passed"]  # A source containing sorry is still only a proposal.
    assert set(m.UNCHECKED) <= report["unchecked"].keys()
    assert "not checked" in report["unchecked"]["context_resolution_and_mapping"]


def test_lean_empty_files_need_reason(checker):
    value = lean()
    value.update(files=[], declaration_map=[], open_items=["Missing dependency"])
    assert checker.check("lean", value)["checks_passed"]
    for reasons in ([], [" \t"]):
        value["open_items"] = reasons
        rejected(checker, "lean", value, "TARGET_REQUIRED")


@pytest.mark.parametrize("role", ["HELPER", "STEP"])
def test_partial_lean_without_target_requires_reason(checker, role):
    value = lean()
    value["files"] = [dict(path="Helpers.lean", content="def helper : Nat := 0\n")]
    value["declaration_map"][0].update(role=role, declaration="helper", code_path="Helpers.lean")
    value["open_items"] = ["Only a helper is available; the target proof remains open."]
    supplied_task = task(value, "formalization.generate")
    report = checker.check("lean", value, supplied_task)
    assert report["checks_passed"]
    assert "expected-declaration coverage" in report["unchecked"]["context_resolution_and_mapping"]
    for reasons in ([], [" \t"]):
        value["open_items"] = reasons
        rejected(checker, "lean", value, "TARGET_REQUIRED", supplied_task)


def test_lean_safe_paths(checker):
    for path in ("../A.lean", "A/../B.lean", "/A.lean", "A\\B.lean", "C:/A.lean", "C:A.lean",
                 "A//B.lean", "./A.lean", "A\0.lean", "A.txt", "lakefile.lean", "LakeFile.Lean",
                 "lean-toolchain", "lakefile.toml", "sub/lakefile.lean", "A.lean/"):
        value = lean()
        value["files"][0]["path"] = value["declaration_map"][0]["code_path"] = path
        rejected(checker, "lean", value, "UNSAFE_PATH")


def test_lean_casefold_collision(checker):
    value = lean()
    for path in ("Proof/Main.lean", "proof/main.lean"):
        value["files"] = [lean()["files"][0], dict(path=path, content="-- synthetic")]
        rejected(checker, "lean", value, "PATH_COLLISION")


def test_lean_target_uniqueness_and_required(checker):
    value = lean()
    value["declaration_map"] *= 2
    rejected(checker, "lean", value, "DUPLICATE_TARGET")
    value["declaration_map"] = []
    rejected(checker, "lean", value, "TARGET_REQUIRED")


def test_lean_code_path_must_exist(checker):
    value = lean()
    value["declaration_map"][0]["code_path"] = "Other.lean"
    rejected(checker, "lean", value, "MISSING_CODE_PATH")


def test_target_local_name_must_be_null(checker):
    value = lean()
    value["declaration_map"][0]["local_name"] = "h"
    rejected(checker, "lean", value, "TARGET_LOCAL_NAME")
    value["declaration_map"][0]["local_name"] = None
    assert checker.check("lean", value)["checks_passed"]
    for role in ("STEP", "HELPER"):
        value["declaration_map"] = [lean()["declaration_map"][0],
                                    dict(lean()["declaration_map"][0], declaration="aux", role=role, local_name="h")]
        assert checker.check("lean", value)["checks_passed"]


@pytest.mark.parametrize("family", ["argument-node", "inference-step", "source-span"])
def test_formalization_input_families(checker, family):
    value = lean()
    if family == "inference-step":
        value["declaration_map"][0]["inference_ref"] = ref(family)
    supplied_task = task(value, "formalization.generate")
    if family == "source-span":
        supplied_task["input_refs"].append(ref(family))
        report = checker.check("lean", value, supplied_task)
        assert not report["checks_passed"]
        assert any(e["code"] == "TASK_CONTRACT" and "Disallowed input family" in e["message"] for e in report["errors"])
    else:
        assert ref(family) in supplied_task["input_refs"]
        assert checker.check("lean", value, supplied_task)["checks_passed"]


def test_lean_packet_must_be_direct_exact_input(checker):
    value = lean()
    supplied_task = task(value, "formalization.generate")
    value["packet_ref"] = ref("formalization-packet", "new")
    rejected(checker, "lean", value, "INVISIBLE_REF", supplied_task)


@pytest.mark.parametrize("other", [ref("formalization-packet", "other"), dict(ref("formalization-packet"), revision=2)])
def test_lean_cannot_replace_target_with_another_visible_packet(checker, other):
    value = lean()
    supplied_task = task(value, "formalization.generate")
    supplied_task["input_refs"].append(other)
    value["packet_ref"] = other
    report = checker.check("lean", value, supplied_task)
    assert not report["checks_passed"]
    assert {e["code"] for e in report["errors"]} == {"TARGET_PACKET"}


def test_lean_requires_one_target_packet_but_allows_other_target_types(checker):
    value = lean()
    supplied_task = task(value, "formalization.generate")
    a, b, node = value["packet_ref"], ref("formalization-packet", "other"), ref("argument-node")
    supplied_task["input_refs"].append(b)
    for targets in ([node], [a, b, node]):
        supplied_task["target_refs"] = targets
        rejected(checker, "lean", value, "TARGET_PACKET", supplied_task)
    supplied_task["target_refs"] = [a, node]
    assert checker.check("lean", value, supplied_task)["checks_passed"]


def test_lean_only_frontier_records(checker):
    value = lean()
    value["records"] = [record("frontier-item", target_refs=[ref("argument-node")], kind="UNPROVED_LEMMA",
                               axes=["mathematical_correctness"], statement="Unproved", next_evidence="Proof",
                               attempt_refs=[], state="OPEN", resolution_refs=[])]
    assert checker.check("lean", value, task(value, "formalization.generate"))["checks_passed"]
    value["records"][0]["record_type"] = ref("formalization-attempt")["record_type"]
    rejected(checker, "lean", value, "SCHEMA")


@pytest.mark.parametrize("kind,filename", [
    ("proof", "proof-context.draft.json"), ("proof", "proof-nodes.draft.json"), ("proof", "proof-draft.json"),
    ("view", "lamport-view.json"), ("lean", "lean-draft.json"),
])
def test_synthetic_and_swap_example_interfaces(checker, kind, filename):
    value = m.contracts.read_json(m.DIRECTORY / "example" / "and-swap" / filename)
    report = checker.check(kind, value)
    assert report["checks_passed"], report["errors"]
    assert "task" in report["unchecked"]  # Fixture refs are not registered Task inputs.
    assert set(m.UNCHECKED) <= report["unchecked"].keys()


def test_synthetic_and_swap_lean_bytes_match():
    directory = m.DIRECTORY / "example" / "and-swap"
    value = m.contracts.read_json(directory / "lean-draft.json")
    assert [file["path"] for file in value["files"]] == ["AndSwap.lean"]
    assert value["files"][0]["content"].encode("utf-8") == m.contracts.read_bytes(directory / "AndSwap.lean")


def test_cli_exit_codes_and_json_without_file_writes(checker, monkeypatch, capsys):
    read = m.contracts.read_bytes
    for raw, status in [(json.dumps(proof()).encode(), 0), (b"{}", 1), (b'{"x":1,"x":2}', 2)]:
        monkeypatch.setattr(m.contracts, "read_bytes", lambda path: raw if path == Path("synthetic.json") else read(path))
        assert m.main(["--kind", "proof", "--input", "synthetic.json"]) == status
        report = json.loads(capsys.readouterr().out)
        assert report["checks_passed"] == (status == 0)
        assert report["unchecked"]
        if status == 0:
            assert "task" in report["unchecked"]
    for supplied, status in [(task(proof()), 0), ({}, 1), (None, 2)]:
        sources = {Path("synthetic.json"): json.dumps(proof()).encode(), Path("task.json"): json.dumps(supplied).encode()}
        monkeypatch.setattr(m.contracts, "read_bytes", lambda path: sources[path] if path in sources else read(path))
        assert m.main(["--kind", "proof", "--input", "synthetic.json", "--task", "task.json"]) == status
        assert json.loads(capsys.readouterr().out)["checks_passed"] == (status == 0)


def test_lean_forbidden_constructs_are_warnings(checker):
    value = lean()
    report = checker.check("lean", value, task(value, "formalization.generate"))
    assert report["checks_passed"]  # An incomplete draft is still only a proposal.
    assert {warning["code"] for warning in report["warnings"]} == {"FORBIDDEN_CONSTRUCT"}
    value["files"][0]["content"] = "theorem target : True := by native_decide\n"
    report = checker.check("lean", value, task(value, "formalization.generate"))
    assert report["checks_passed"]
    assert "native_decide" in report["warnings"][0]["message"]


def test_lean_declaration_digests_are_emitted(checker):
    report = checker.check("lean", lean())
    digest = report["declaration_digests"][0]
    assert digest["declaration"] == "target" and digest["role"] == "TARGET"
    assert digest["sha256"] == "sha256:" + hashlib.sha256(b"target").hexdigest()


def test_statement_baseline_freeze(checker):
    value = lean()
    digest = "sha256:" + hashlib.sha256(b"target").hexdigest()
    assert checker.check("lean", value, statement_baseline={"statements": {"target": digest}})["checks_passed"]
    drift = checker.check("lean", value, statement_baseline={"statements": {"target": "sha256:" + "b" * 64}})
    assert {error["code"] for error in drift["errors"]} == {"STATEMENT_DRIFT"}
    missing = checker.check("lean", value, statement_baseline={"statements": {"other": digest}})
    assert {error["code"] for error in missing["errors"]} == {"STATEMENT_BASELINE"}


def test_require_task_flag(checker):
    value = proof()
    report = checker.check("proof", value, require_task=True)
    assert not report["checks_passed"]
    assert "TASK_REQUIRED" in {error["code"] for error in report["errors"]}
    assert checker.check("proof", value, task(value), require_task=True)["checks_passed"]


def test_axioms_audit_accepts_standard_and_rejects_sorry():
    text = ("'A' depends on axioms: [propext, Classical.choice, Quot.sound]\n"
            "'B' does not depend on any axioms\n")
    report = m.check_axioms(text)
    assert report["checks_passed"]
    assert [entry["declaration"] for entry in report["declarations"]] == ["A", "B"]
    bad = m.check_axioms("'C' depends on axioms: [sorryAx]\n")
    assert not bad["checks_passed"] and {error["code"] for error in bad["errors"]} == {"SORRY_AXIOM"}
    custom = m.check_axioms("'D' depends on axioms: [propext, MyAxiom]\n")
    assert not custom["checks_passed"] and {error["code"] for error in custom["errors"]} == {"UNEXPECTED_AXIOM"}
    empty = m.check_axioms("no audit output here")
    assert not empty["checks_passed"] and {error["code"] for error in empty["errors"]} == {"EMPTY_AUDIT"}
    allowed = m.check_axioms("'E' depends on axioms: [MyAxiom]\n", allowed=["MyAxiom"])
    assert allowed["checks_passed"]


def test_cli_audit_and_fail_on_warning(monkeypatch, capsys):
    read = m.contracts.read_bytes
    sources = {
        Path("audit.txt"): b"'A' does not depend on any axioms\n",
        Path("bad-audit.txt"): b"'A' depends on axioms: [sorryAx]\n",
        Path("draft.json"): json.dumps(lean()).encode(),
    }
    monkeypatch.setattr(m.contracts, "read_bytes", lambda path: sources[path] if path in sources else read(path))
    assert m.main(["--kind", "audit", "--input", "audit.txt"]) == 0
    assert json.loads(capsys.readouterr().out)["checks_passed"]
    assert m.main(["--kind", "audit", "--input", "bad-audit.txt", "--allowed-axioms", "propext"]) == 1
    assert json.loads(capsys.readouterr().out)["checks_passed"] is False
    assert m.main(["--kind", "lean", "--input", "draft.json", "--fail-on-warning"]) == 1
    assert json.loads(capsys.readouterr().out)["warnings"]
    assert m.main(["--kind", "lean", "--input", "draft.json"]) == 0
