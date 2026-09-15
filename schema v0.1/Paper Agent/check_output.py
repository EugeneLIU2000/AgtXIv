#!/usr/bin/env python3
"""Read-only Paper draft/record checks, never assembly, delivery or approval.

Exit 0: the checks actually performed passed (inspect unchecked layers).
Exit 1: a mechanical schema, binding or Paper filling check failed.
Exit 2: invalid invocation, unreadable/invalid JSON, or unusable checker inputs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

# Importing this read-only command must not create caches in the repository.
sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
OVERLAY = DIRECTORY.parent
_spec = importlib.util.spec_from_file_location("paper_output_contracts", OVERLAY / "validate.py")
contracts_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contracts_module)

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Resource
from referencing.exceptions import Unresolvable
from agtxiv_v3.contracts import MAX_RECORDS, REF_KEYS


ARTIFACT_KEYS = frozenset({"artifact_id", "sha256", "byte_size", "media_type"})
MAX_REPORTED_ERRORS = 200


class InputError(ValueError):
    """The supplied input cannot be checked in the requested mode."""


def pointer(parts):
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def walk(value, path=""):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + pointer([key]))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + f"/{index}")


def new_report(mode):
    reasons = {
        "draft_schema": "Not checked in this mode or input shape is unavailable.",
        "follow_up_operations": "Requires a structurally valid draft.",
        "task_contract": "No Task supplied; task scope is not checked.",
        "task_output_types": "No valid Task and draft; output scope is not checked.",
        "task_record_refs": "No valid Task and draft; reference membership is not checked.",
        "task_artifact_refs": "No valid Task and draft; artifact membership is not checked.",
        "record_shape_and_hash": "Drafts have no business envelope or record hash.",
        "paper_lint": "Requires structurally valid Paper payloads.",
        "record_set": "No RecordSet validation, reference closure or cross-record checks.",
        "source_bytes": "No source bytes are opened or verified; catalog membership is not provenance proof.",
        "execution_identity": "Actual visibility, producer identity and independent review require the host.",
        "delivery": "A draft is not a Result; missing output families and open items do not determine outcome.",
        "scientific_correctness": "No semantic inference, claim merging or scientific assessment.",
    }
    return {
        "mode": mode,
        "record_count": 0,
        "paper_record_count": 0,
        "paper_lint_record_count": 0,
        "layers": {name: {"checked": False, "passed": None, "reason": reason}
                   for name, reason in reasons.items()},
        "missing_expected_record_types": None,
        "error_count": 0,
        "errors": [],
        "errors_truncated": False,
        "warnings": [],
    }


def issue(report, layer, code, path, message, record_id=None):
    report["error_count"] += 1
    if len(report["errors"]) < MAX_REPORTED_ERRORS:
        item = {"layer": layer, "code": code, "path": path, "message": str(message)[:600]}
        if record_id is not None:
            item["record_id"] = record_id
        report["errors"].append(item)
    else:
        report["errors_truncated"] = True


def checked(report, layer, before, reason):
    report["layers"][layer] = {
        "checked": True, "passed": report["error_count"] == before, "reason": reason,
    }


class OutputChecker:
    def __init__(self):
        # Reuse the pinned bundle, operation registry and offline schema resolver.
        self.contracts = contracts_module.Contracts()
        self.base = self.contracts.base
        self.paper_types = {
            f"agtxiv.v3.{name}/0.0.0" for name in
            self.contracts.operation("paper", "paper.extract")["output_record_types"]
        }

    def draft_validator(self):
        schema = contracts_module.read_json(DIRECTORY / "extraction-draft.schema.json")
        Draft202012Validator.check_schema(schema)
        branches = schema["properties"]["records"]["items"]["oneOf"]
        types = [branch["properties"]["record_type"]["const"] for branch in branches]
        if len(types) != len(self.paper_types) or set(types) != self.paper_types:
            raise InputError("Draft branches differ from the Paper operation output whitelist")
        for branch in branches:
            properties = branch["properties"]
            business = self.base.by_type[properties["record_type"]["const"]]
            if properties["payload"] != {"$ref": business["$id"] + "#/properties/payload"}:
                raise InputError("Draft payload must directly reference its existing business payload")
        registry = self.contracts.registry.with_resource(schema["$id"], Resource.from_contents(schema))
        resolver = registry.resolver(base_uri=schema["$id"])
        for _, node in walk(schema):
            if "$ref" in node:
                resolver.lookup(node["$ref"])
        return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())

    def lint(self, records, report, *, draft):
        before = report["error_count"]
        for index, record in records:
            if record["record_type"] not in self.paper_types:
                continue
            report["paper_lint_record_count"] += 1
            name = contracts_module.short_type(record)
            payload = record["payload"]
            path = f"/records/{index}/payload"
            def fail(code, location, message):
                issue(report, "paper_lint", code, location, message, record.get("record_id"))
            field = {"scientific-claim": "conditions", "math-claim": "assumptions",
                     "semantic-context": "assumptions"}.get(name)
            if field:
                for i, condition in enumerate(payload[field]):
                    cpath = path + f"/{field}/{i}"
                    if condition["origin"] in {"SOURCE_EXPLICIT", "SOURCE_RECONSTRUCTED"}:
                        if not condition["source_span_refs"]:
                            fail("CONDITION_SOURCE_REQUIRED", cpath + "/source_span_refs",
                                 "Source conditions need direct source-span references.")
                    elif condition["origin"] in {"AGENT_ADDED", "IMPORTED"}:
                        fail("ADDED_SOURCE_CONDITION", cpath + "/origin",
                             "Source extraction cannot add or import a premise; report the proposed repair separately.")
            if name == "scientific-claim" and not any(c["role"] == "CONCLUSION" for c in payload["components"]):
                fail("CONCLUSION_REQUIRED", path + "/components",
                     "A source claim needs a CONCLUSION component, including interpretive claims.")
            if name == "math-claim":
                if not payload["component_ids"]:
                    fail("MATH_COMPONENT_REQUIRED", path + "/component_ids",
                         "A mathematical target must identify its source components.")
                if payload["exactness"] in {"APPROXIMATE", "ASYMPTOTIC"} and not payload["approximation_error"].strip():
                    fail("APPROXIMATION_REQUIRED", path + "/approximation_error",
                         "An approximate/asymptotic target needs explicit error/regime information or an explicit gap.")
            if draft and name == "claim-component-map" and payload["review"]["independence"] != "UNESTABLISHED":
                fail("DRAFT_REVIEW_UNESTABLISHED", path + "/review/independence",
                     "A draft may only declare UNESTABLISHED; actual identity and SELF_REVIEW are checked by the host.")
        checked(report, "paper_lint", before,
                "Only the listed Paper filling rules; structurally invalid records are skipped. No semantic judgment.")

    def check_draft(self, draft, task=None):
        if not isinstance(draft, dict):
            raise InputError("--draft requires a JSON object")
        report = new_report("draft")
        before = report["error_count"]
        for error in self.draft_validator().iter_errors(draft):
            message = ("Record must match exactly one corresponding type/payload branch."
                       if error.validator == "oneOf" else error.message)
            issue(report, "draft_schema", "DRAFT_SCHEMA", pointer(error.absolute_path), message)
        checked(report, "draft_schema", before,
                "Draft wrapper and referenced payload schemas only; full-record root constraints are not checked.")
        shape_ok = report["layers"]["draft_schema"]["passed"]
        if isinstance(draft.get("records"), list):
            report["record_count"] = len(draft["records"])
        if shape_ok:
            report["paper_record_count"] = len(draft["records"])
            self.lint(enumerate(draft["records"]), report, draft=True)
            before = report["error_count"]
            for index, request in enumerate(draft["follow_up_requests"]):
                try:
                    self.contracts.operation(request["agent"], request["operation"])
                except contracts_module.InterfaceError as error:
                    issue(report, "follow_up_operations", "FOLLOW_UP_OPERATION",
                          f"/follow_up_requests/{index}/operation", error)
            checked(report, "follow_up_operations", before,
                    "Registered agent/operation pairing only; required operation inputs remain scheduler work.")
            if not any(draft[field] for field in ("records", "open_items", "follow_up_requests")):
                report["warnings"].append({
                    "code": "UNEXPLAINED_EMPTY_DRAFT", "path": "",
                    "message": "No records, gaps or follow-up requests; the empty draft does not establish completed extraction.",
                })
        if task is not None:
            before = report["error_count"]
            try:
                self.contracts.task(task)
                if task["agent"] != "paper" or task["operation"] != "paper.extract":
                    raise contracts_module.InterfaceError("Draft Task must use paper.extract")
            except contracts_module.InterfaceError as error:
                issue(report, "task_contract", "TASK_CONTRACT", "/task", error)
            checked(report, "task_contract", before, "Existing Contracts.task checks, restricted to paper.extract.")
            if shape_ok and report["layers"]["task_contract"]["passed"]:
                self.check_task_bindings(draft, task, report)
        return report

    def check_task_bindings(self, draft, task, report):
        before = report["error_count"]
        expected = set(task["expected_record_types"])
        actual = set()
        for index, record in enumerate(draft["records"]):
            name = contracts_module.short_type(record)
            actual.add(name)
            if name not in expected:
                issue(report, "task_output_types", "UNDECLARED_OUTPUT_TYPE", f"/records/{index}/record_type",
                      "Output family is not declared in Task.expected_record_types: " + name)
        report["missing_expected_record_types"] = sorted(expected - actual)
        checked(report, "task_output_types", before,
                "Every output family must be declared. Missing families are reported, not treated as a Result outcome.")
        record_refs = {contracts_module.ref_key(ref) for ref in task["input_refs"]}
        artifacts = {contracts_module.artifact_key(ref) for ref in task["input_artifacts"]}
        for layer, keys, catalog, key_fn, code in (
            ("task_record_refs", REF_KEYS, record_refs, contracts_module.ref_key, "UNPROVIDED_RECORD_REF"),
            ("task_artifact_refs", ARTIFACT_KEYS, artifacts, contracts_module.artifact_key, "UNPROVIDED_ARTIFACT_REF"),
        ):
            before = report["error_count"]
            for path, node in walk(draft):
                if keys <= node.keys() and key_fn(node) not in catalog:
                    issue(report, layer, code, path, "Exact reference was not provided in this Task's input catalog.")
            checked(report, layer, before,
                    "All nested references, including follow-up requests; artifact path_hint is not identity. Actual visibility is not checked.")

    def check_records(self, records):
        if not isinstance(records, list) or len(records) > MAX_RECORDS:
            raise InputError(f"--records requires a JSON array of at most {MAX_RECORDS} full records")
        report = new_report("records")
        report["record_count"] = len(records)
        before = report["error_count"]
        lintable = []
        for index, record in enumerate(records):
            # Guard the bundle's discriminator lookup against unhashable input.
            if not isinstance(record, dict) or not isinstance(record.get("record_type"), str):
                issue(report, "record_shape_and_hash", "RECORD_SCHEMA", f"/records/{index}",
                      "A full record needs an object with a string record_type.")
                continue
            if record["record_type"] in self.paper_types:
                report["paper_record_count"] += 1
            errors = self.base.validate_record(record)
            for error in errors:
                issue(report, "record_shape_and_hash", error.code,
                      f"/records/{index}" + error.path, error.message, record.get("record_id"))
            if not any(error.code not in {"RECORD_HASH_MISMATCH", "SCHEMA_BUNDLE_MISMATCH"} for error in errors):
                lintable.append((index, record))
        checked(report, "record_shape_and_hash", before,
                "SchemaBundle.validate_record on each record, including host context; no RecordSet validation.")
        if lintable or not records:
            self.lint(lintable, report, draft=False)
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--draft", type=Path, help="Paper model draft JSON")
    modes.add_argument("--records", type=Path, help="Array of full v0.0 records (may include host context)")
    parser.add_argument("--task", type=Path, help="Fixed Task used only with --draft")
    args = parser.parse_args(argv)
    if args.task is not None and args.draft is None:
        parser.error("--task may only be used with --draft")
    try:
        # read_json reuses bounded read_bytes and canonical parse: duplicate
        # keys, NaN, unsupported numbers and excessive nesting are rejected.
        value = contracts_module.read_json(args.draft or args.records)
        task = contracts_module.read_json(args.task) if args.task is not None else None
        if args.task is not None and not isinstance(task, dict):
            raise InputError("--task requires a JSON object")
        checker = OutputChecker()
        report = checker.check_draft(value, task) if args.draft else checker.check_records(value)
    except (OSError, InputError, contracts_module.ContractError, contracts_module.InterfaceError,
            SchemaError, Unresolvable, RecursionError) as error:
        report = new_report("draft" if args.draft else "records")
        report["input_error"] = str(error)[:1200]
        report["checks_completed"] = False
        issue(report, "input", "INVALID_INPUT", "", error)
        report["layers"]["input"] = {"checked": True, "passed": False,
                                       "reason": "Requested input could not be read or checked."}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
