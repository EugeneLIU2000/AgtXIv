"""Synthetic read-only Paper checks; no historical example is read or changed.

Run: .venv/bin/python -B -m unittest discover -s 'schema v0.1/Paper Agent/tests' -v
"""
import copy
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parents[1]
CHECKER_PATH = DIRECTORY / "check_output.py"
SPEC = importlib.util.spec_from_file_location("paper_output_checker", CHECKER_PATH)
output = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(output)


def ref(name, suffix="one"):
    return {"record_type": f"agtxiv.v3.{name}/0.0.0", "record_id": f"fixture:{name}-{suffix}",
            "revision": 1, "content_hash": "sha256:" + "1" * 64}


def condition(origin="SOURCE_EXPLICIT"):
    return {"condition_id": "condition:one", "statement": "The source defines a real scalar.",
            "origin": origin, "source_span_refs": [ref("source-span")]}


def math_object():
    return {"symbol": "1", "object_type": "Real scalar", "definition_refs": [],
            "unit": "", "convention": "Usual real arithmetic"}


def payload(name):
    if name == "scientific-claim":
        return {"statement": "The real number one equals itself.", "source_span_refs": [ref("source-span")],
                "components": [{"component_id": "component:one", "text": "1 = 1", "role": "CONCLUSION",
                                "source_span_refs": [ref("source-span")]}],
                "conditions": [condition()], "modality": "ASSERTED", "attribution": "Synthetic author",
                "system": "Real arithmetic", "comparison_baseline": ""}
    if name == "math-claim":
        return {"claim_ref": ref("scientific-claim"), "component_ids": ["component:one"],
                "objects": [math_object()], "quantifiers": [], "assumptions": [condition()],
                "conclusion": "1 = 1", "exactness": "EXACT", "approximation_error": "",
                "definition_refs": [], "semantic_refs": [], "normalization": "Source notation retained."}
    if name == "semantic-context":
        return {"claim_ref": ref("scientific-claim"), "physical_system": "Synthetic scalar model",
                "object_mapping": [{"dimension": "OBJECT", "source_value": "scalar", "target_value": "scalar",
                                    "relation": "UNKNOWN", "witness_refs": []}],
                "assumptions": [condition()], "approximation_regime": "Exact arithmetic",
                "error_bound": "", "observables": [], "limitations": []}
    if name == "claim-component-map":
        return {"claim_ref": ref("scientific-claim"), "coverage": "PARTIAL",
                "mappings": [{"component_id": "component:one", "math_refs": [ref("math-claim")],
                              "semantic_refs": [], "evidence_refs": [], "disposition": "MAPPED", "residual": ""}],
                "review": {"reviewed_refs": [ref("scientific-claim")],
                           "producer_principal_ids": ["principal:fixture"], "independence": "UNESTABLISHED",
                           "conflicts": [], "method": "Synthetic draft, not an independent review.", "evidence_refs": []}}
    if name == "source-span":
        return {"source_ref": ref("source-snapshot"), "artifact": artifact(), "locator_kind": "RAW_TEXT_BYTES",
                "byte_start": 0, "byte_end": 1, "span_sha256": "sha256:" + "2" * 64,
                "pdf_region": None, "transformation_ref": None, "locator": "Synthetic byte 0", "activity": "ACTIVE"}
    if name == "agentization-plan":
        return {"source_ref": ref("source-snapshot"), "profile_ref": ref("processing-profile"), "baseline_ref": None,
                "source_unit_ids": ["unit:one"], "max_steps": 2, "max_seconds": 60, "max_cost_units": 1,
                "no_progress_limit": 1, "trigger_note": "Synthetic test only"}
    raise AssertionError(name)


def artifact():
    return {"artifact_id": "artifact:one", "sha256": "sha256:" + "2" * 64,
            "byte_size": 1, "media_type": "text/plain", "path_hint": "does-not-exist.txt"}


def draft(*names):
    return {"draft_version": "1.1",
            "records": [{"record_type": f"agtxiv.v3.{name}/0.0.0", "payload": payload(name)} for name in names],
            "open_items": [], "follow_up_requests": []}


def task_for(value):
    refs = {output.contracts_module.ref_key(r): r for r in
            [ref("source-snapshot"), ref("agentization-plan"), ref("processing-profile")]}
    artifacts = {}
    for _, node in output.walk(value):
        if output.REF_KEYS <= node.keys():
            refs[output.contracts_module.ref_key(node)] = copy.deepcopy(node)
        if output.ARTIFACT_KEYS <= node.keys():
            artifacts[output.contracts_module.artifact_key(node)] = copy.deepcopy(node)
    return {"contract_version": "0.1.0", "task_id": "task-fixture", "agent": "paper", "operation": "paper.extract",
            "brief": "Extract the fixed synthetic statement without changing its meaning.",
            "input_refs": list(refs.values()), "target_refs": [ref("source-snapshot")],
            "input_artifacts": list(artifacts.values()), "depends_on": [],
            "expected_record_types": sorted({output.contracts_module.short_type(r) for r in value["records"]}),
            "limits": {"max_attempts": 2, "max_seconds": 60, "max_cost_units": 1, "no_progress_limit": 1},
            "acceptance": "DELIVERY", "exclusions": [], "capabilities": []}


def full_record(checker, name):
    return checker.base.make_record(
        name, f"fixture:record-{name}", payload(name), policy_ref=ref("authority-policy"),
        producer={"principal_id": "principal:fixture", "role": "CLAIM_PRODUCER", "actor_kind": "AGENT",
                  "identity_assurance": "DECLARED", "execution_id": "execution:fixture",
                  "visible_input_refs": [], "identity_evidence": []},
        created_at="2026-09-13T00:00:00Z", data_class="SYNTHETIC")


class OutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = output.OutputChecker()

    def assert_passes(self, report):
        self.assertEqual(report["error_count"], 0, report["errors"])

    def assert_code(self, report, code):
        self.assertIn(code, {error["code"] for error in report["errors"]}, report)

    def record(self, name):
        return full_record(self.checker, name)

    def test_valid_draft_does_not_claim_unchecked_scope(self):
        result = self.checker.check_draft(draft("scientific-claim", "math-claim", "semantic-context"))
        self.assert_passes(result)
        for layer in ("task_contract", "task_output_types", "task_record_refs", "task_artifact_refs",
                      "record_shape_and_hash", "record_set", "execution_identity", "delivery", "scientific_correctness"):
            with self.subTest(layer=layer):
                self.assertFalse(result["layers"][layer]["checked"])
                self.assertIsNone(result["layers"][layer]["passed"])
        self.assertIsNone(result["missing_expected_record_types"])

    def test_type_payload_mismatch_and_unknown_type(self):
        for wrong in ("math-claim", "agentization-plan", "invented"):
            with self.subTest(wrong=wrong):
                value = draft("scientific-claim")
                value["records"][0]["record_type"] = f"agtxiv.v3.{wrong}/0.0.0"
                self.assert_code(self.checker.check_draft(value), "DRAFT_SCHEMA")

    def test_unknown_fields_and_model_envelope_are_rejected(self):
        for path, key in (((), "scientific_pass"), (("records", 0), "producer"),
                          (("records", 0), "content_hash"), (("records", 0, "payload"), "seed")):
            with self.subTest(path=path, key=key):
                value = draft("scientific-claim")
                node = value
                for part in path:
                    node = node[part]
                node[key] = "forbidden"
                self.assert_code(self.checker.check_draft(value), "DRAFT_SCHEMA")

    def test_direct_condition_sources_and_added_premises(self):
        for name, field in (("scientific-claim", "conditions"), ("math-claim", "assumptions"),
                            ("semantic-context", "assumptions")):
            for origin in ("SOURCE_EXPLICIT", "SOURCE_RECONSTRUCTED", "AGENT_ADDED", "IMPORTED"):
                with self.subTest(name=name, origin=origin):
                    value = draft(name)
                    value["records"][0]["payload"][field] = [condition(origin)]
                    if origin.startswith("SOURCE_"):
                        self.assert_passes(self.checker.check_draft(value))
                        value["records"][0]["payload"][field][0]["source_span_refs"] = []
                        code = "CONDITION_SOURCE_REQUIRED"
                    else:
                        code = "ADDED_SOURCE_CONDITION"
                    self.assert_code(self.checker.check_draft(value), code)

    def test_empty_quantifiers_are_legal_without_semantic_guessing(self):
        value = draft("math-claim")
        self.assertEqual(value["records"][0]["payload"]["quantifiers"], [])
        self.assert_passes(self.checker.check_draft(value))
        value["records"][0]["payload"]["conclusion"] = "A and B; assumed words alone are not an origin tag."
        self.assert_passes(self.checker.check_draft(value))

    def test_math_component_and_approximation_requirements(self):
        value = draft("math-claim")
        value["records"][0]["payload"]["component_ids"] = []
        self.assert_code(self.checker.check_draft(value), "MATH_COMPONENT_REQUIRED")
        for exactness in ("APPROXIMATE", "ASYMPTOTIC"):
            for missing in ("", "   "):
                with self.subTest(exactness=exactness, missing=missing):
                    value = draft("math-claim")
                    value["records"][0]["payload"].update(exactness=exactness, approximation_error=missing)
                    self.assert_code(self.checker.check_draft(value), "APPROXIMATION_REQUIRED")
                    value["records"][0]["payload"]["approximation_error"] = "Source does not specify an error bound."
                    self.assert_passes(self.checker.check_draft(value))

    def test_scientific_claim_needs_conclusion_including_interpretation(self):
        value = draft("scientific-claim")
        value["records"][0]["payload"]["modality"] = "INTERPRETIVE"
        self.assert_passes(self.checker.check_draft(value))
        value["records"][0]["payload"]["components"][0]["role"] = "EVIDENCE"
        self.assert_code(self.checker.check_draft(value), "CONCLUSION_REQUIRED")

    def test_map_draft_does_not_establish_independent_review(self):
        value = draft("claim-component-map")
        self.assert_passes(self.checker.check_draft(value))
        for state in ("ROLE_SEPARATED", "INDEPENDENTLY_ATTESTED"):
            value["records"][0]["payload"]["review"]["independence"] = state
            self.assert_code(self.checker.check_draft(value), "DRAFT_REVIEW_UNESTABLISHED")
        record = self.record("claim-component-map")
        record["payload"]["review"]["independence"] = "ROLE_SEPARATED"
        from agtxiv_v3.contracts import content_hash
        record["content_hash"] = content_hash(record)
        result = self.checker.check_records([record])
        self.assert_passes(result)
        self.assertFalse(result["layers"]["execution_identity"]["checked"])

    def test_task_whitelist_and_missing_expected_are_distinct(self):
        value = draft("scientific-claim")
        task = task_for(value)
        self.assert_passes(self.checker.check_draft(value, task))
        task["expected_record_types"] = ["math-claim"]
        self.assert_code(self.checker.check_draft(value, task), "UNDECLARED_OUTPUT_TYPE")
        task["expected_record_types"] = ["scientific-claim", "math-claim"]
        result = self.checker.check_draft(value, task)
        self.assert_passes(result)
        self.assertEqual(result["missing_expected_record_types"], ["math-claim"])
        self.assertFalse(result["layers"]["delivery"]["checked"])

    def test_existing_task_validation_is_used(self):
        value = draft("scientific-claim")
        for field, replacement in (("brief", ""), ("expected_record_types", ["release-certificate"]),
                                   ("input_refs", []), ("capabilities", ["release.certify"])):
            with self.subTest(field=field):
                task = task_for(value)
                task[field] = replacement
                self.assert_code(self.checker.check_draft(value, task), "TASK_CONTRACT")

    def test_all_nested_refs_and_followup_refs_must_be_provided(self):
        value = draft("semantic-context")
        value["records"][0]["payload"]["object_mapping"][0]["witness_refs"] = [ref("definition", "nested")]
        value["follow_up_requests"] = [{"agent": "dependency", "operation": "dependency.search",
                                         "input_refs": [ref("scientific-claim", "followup")], "reason": "Find a source."}]
        task = task_for(value)
        self.assert_passes(self.checker.check_draft(value, task))
        for missing in (ref("definition", "nested"), ref("scientific-claim", "followup"), ref("source-span")):
            with self.subTest(missing=missing):
                bad = copy.deepcopy(task)
                bad["input_refs"].remove(missing)
                self.assert_code(self.checker.check_draft(value, bad), "UNPROVIDED_RECORD_REF")
        value["records"][0]["payload"]["claim_ref"]["content_hash"] = "sha256:" + "f" * 64
        self.assert_code(self.checker.check_draft(value, task), "UNPROVIDED_RECORD_REF")

    def test_followup_operation_pairing_without_requiring_future_inputs(self):
        value = draft()
        value["follow_up_requests"] = [{"agent": "dependency", "operation": "dependency.search",
                                         "input_refs": [], "reason": "Find the missing source after registration."}]
        self.assert_passes(self.checker.check_draft(value))
        for wrong in ("proof.expand", "dependency.unknown"):
            with self.subTest(operation=wrong):
                value["follow_up_requests"][0]["operation"] = wrong
                report = self.checker.check_draft(value)
                self.assert_code(report, "FOLLOW_UP_OPERATION")
                self.assertEqual(report["errors"][0]["path"], "/follow_up_requests/0/operation")

    def test_artifact_identity_uses_four_fields_not_path_hint(self):
        value = draft("source-span")
        task = task_for(value)
        task["input_artifacts"][0]["path_hint"] = "never-open-this-path.txt"
        self.assert_passes(self.checker.check_draft(value, task))
        for field, replacement in (("sha256", "sha256:" + "3" * 64), ("byte_size", 2),
                                   ("media_type", "application/pdf"), ("artifact_id", "artifact:other")):
            with self.subTest(field=field):
                bad = copy.deepcopy(task)
                bad["input_artifacts"][0][field] = replacement
                self.assert_code(self.checker.check_draft(value, bad), "UNPROVIDED_ARTIFACT_REF")
        task["input_artifacts"] = []
        self.assert_code(self.checker.check_draft(value, task), "UNPROVIDED_ARTIFACT_REF")

    def test_open_items_can_coexist_with_shape_success(self):
        value = draft("scientific-claim")
        value["open_items"] = ["Independent mapping review remains unavailable."]
        original = copy.deepcopy(value)
        self.assert_passes(self.checker.check_draft(value, task_for(value)))
        self.assertEqual(value, original)

    def test_empty_draft_warns_without_inventing_result_outcome(self):
        result = self.checker.check_draft(draft())
        self.assert_passes(result)
        self.assertEqual(result["warnings"][0]["code"], "UNEXPLAINED_EMPTY_DRAFT")
        self.assertFalse(result["layers"]["delivery"]["checked"])
        value = draft()
        value["open_items"] = ["Required source material is missing."]
        result = self.checker.check_draft(value)
        self.assert_passes(result)
        self.assertEqual(result["warnings"], [])
        self.assertNotIn("outcome", result)

    def test_records_accept_host_context_without_claiming_recordset(self):
        records = [self.record("agentization-plan"), self.record("scientific-claim"), self.record("math-claim")]
        original = copy.deepcopy(records)
        result = self.checker.check_records(records)
        self.assert_passes(result)
        self.assertEqual(result["paper_record_count"], 2)
        self.assertEqual(result["record_count"], 3)
        self.assertFalse(result["layers"]["record_set"]["checked"])
        self.assertIsNone(result["layers"]["record_set"]["passed"])
        self.assertEqual(records, original)

    def test_full_record_tampering_and_paper_lint(self):
        record = self.record("scientific-claim")
        record["payload"]["conditions"][0]["source_span_refs"] = []
        result = self.checker.check_records([record])
        self.assert_code(result, "RECORD_HASH_MISMATCH")
        self.assert_code(result, "CONDITION_SOURCE_REQUIRED")
        error = next(e for e in result["errors"] if e["code"] == "CONDITION_SOURCE_REQUIRED")
        self.assertEqual(error["path"], "/records/0/payload/conditions/0/source_span_refs")
        self.assertEqual(error["record_id"], record["record_id"])
        record = self.record("agentization-plan")
        record["content_hash"] = "sha256:" + "0" * 64
        self.assert_code(self.checker.check_records([record]), "RECORD_HASH_MISMATCH")
        record = self.record("scientific-claim")
        record["unexpected"] = True
        self.assert_code(self.checker.check_records([record]), "SCHEMA")

    def test_bad_record_discriminators_do_not_crash(self):
        for value in (None, [], {}, {"record_type": []}, {"record_type": "unknown"}):
            with self.subTest(value=value):
                self.assertGreater(self.checker.check_records([value])["error_count"], 0)

    def test_record_array_is_bounded(self):
        with self.assertRaises(output.InputError):
            self.checker.check_records([{}] * (output.MAX_RECORDS + 1))


class CommandTests(unittest.TestCase):
    def run_cli(self, raw, *extra, mode="--draft", task=None):
        with tempfile.TemporaryDirectory(prefix="paper-output-test-") as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(raw if isinstance(raw, bytes) else json.dumps(raw).encode())
            before = path.read_bytes()
            args = [sys.executable, "-B", str(CHECKER_PATH), mode, str(path), *extra]
            task_path = Path(directory) / "task.json"
            if task is not None:
                task_path.write_text(json.dumps(task), encoding="utf-8")
                args += ["--task", str(task_path)]
            files_before = {p.name: p.read_bytes() for p in Path(directory).iterdir()}
            result = subprocess.run(args, text=True, capture_output=True, timeout=30, cwd=directory)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual({p.name: p.read_bytes() for p in Path(directory).iterdir()}, files_before)
            return result

    def test_exit_zero_and_unchecked_layers_without_task(self):
        value = draft("math-claim")
        value["open_items"] = ["Unresolved interpretation."]
        result = self.run_cli(value)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["layers"]["task_record_refs"]["checked"])
        self.assertIsNone(report["layers"]["task_record_refs"]["passed"])

    def test_exit_one_for_schema_and_task_failures(self):
        value = draft("scientific-claim")
        value["extra"] = "not allowed"
        result = self.run_cli(value)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertGreater(json.loads(result.stdout)["error_count"], 0)
        value = draft("scientific-claim")
        task = task_for(value)
        task["expected_record_types"] = []
        result = self.run_cli(value, task=task)
        self.assertEqual(result.returncode, 1, result.stderr)

    def test_invalid_json_and_unusable_input_exit_two(self):
        for raw in (b'{"records": [], "records": []}', b'{"x": NaN}', b'{"x": Infinity}',
                    b'{"x": -Infinity}', b'{"x": 0.5}', b'{"x":', b'\xff', b'null'):
            with self.subTest(raw=raw):
                result = self.run_cli(raw)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("input_error", json.loads(result.stdout))

    def test_mode_and_task_argument_restrictions(self):
        self.assertEqual(self.run_cli([], "--task", "absent.json", mode="--records").returncode, 2)
        self.assertEqual(self.run_cli({}, mode="--records").returncode, 2)
        self.assertEqual(self.run_cli(draft(), "--records", "absent.json").returncode, 2)
        self.assertEqual(self.run_cli(draft(), "--task", "absent.json").returncode, 2)

    def test_records_cli_hash_failure_and_no_recordset_claim(self):
        checker = output.OutputChecker()
        record = full_record(checker, "scientific-claim")
        result = self.run_cli([record], mode="--records")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["layers"]["record_set"]["checked"])
        record["content_hash"] = "sha256:" + "f" * 64
        self.assertEqual(self.run_cli([record], mode="--records").returncode, 1)

    def test_read_helper_bounds_and_symlinks_exit_two(self):
        with tempfile.TemporaryDirectory(prefix="paper-output-bounds-") as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(b'{}' * 8)
            with mock.patch.object(output.contracts_module, "MAX_FILE", 8), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(output.main(["--draft", str(path)]), 2)
            link = Path(directory) / "link.json"
            link.symlink_to(path)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(output.main(["--draft", str(link)]), 2)


if __name__ == "__main__":
    unittest.main()
