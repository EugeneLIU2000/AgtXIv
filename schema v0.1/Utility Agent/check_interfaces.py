#!/usr/bin/env python3
"""Read-only Utility request/receipt checks. Exit 0: checked layers pass; 1: fail; 2: input error.

Reads JSON only. No command runs, no bytes are read, no transaction occurs, no Result is produced.
The checker compares declared operations, input families and output types. A receipt is treated as
a claim: execution facts, exit codes and timestamps are never verified here.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("utility_contracts", DIRECTORY.parent / "validate.py")
contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contracts)

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Resource
from referencing.exceptions import Unresolvable
from agtxiv_v3.contracts import ContractError, REF_KEYS

AGENT = "utility"
KINDS = ("request", "capture", "register-plan", "assemble-packet", "formal-check",
         "persist", "export", "project", "certify")
SCHEMAS = {"request": "utility-request"}
SCHEMAS.update({kind: f"{kind}-receipt" for kind in KINDS if kind != "request"})
OPERATIONS = {kind: f"utility.{kind}" for kind in KINDS if kind != "request"}
UNCHECKED = {
    "record_set": "No RecordSet, stored envelopes/hashes, root record constraints or reference closure checked.",
    "source_bytes": "Artifact bytes and hashes are not read or verified.",
    "execution_facts": (
        "Receipt execution is self-reported. Commands, exit codes, timestamps, tool versions and host mode"
        " are not verified against any real process; a shape-valid receipt is not evidence that anything ran."),
    "request_binding": (
        "request_hash is not recomputed from any canonical request bytes, and the request is not compared"
        " against a real Task here. Host adapters own that binding."),
    "outputs": (
        "Outputs are not assembled into business records and their payload semantics are not reviewed."
        " This checker only verifies declared types against the pinned operation whitelist."),
    "authority": "Permissions, allowed_commands enforcement and the host execution boundary are not checked.",
    "meaning": "Scientific correctness, source meaning and approval are not checked.",
    "result": "No Result, delivery outcome, persistence or approval is produced.",
}


def report_for(kind):
    return {"kind": kind, "checks_passed": False, "checked": [], "unchecked": dict(UNCHECKED),
            "warnings": [], "errors": []}


def walk(value, path=""):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + "/" + key.replace("~", "~0").replace("/", "~1"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}/{index}")


class InterfaceChecker:
    def __init__(self):
        self.contracts = contracts.Contracts()

    def validator(self, kind):
        schema = contracts.read_json(DIRECTORY / (SCHEMAS[kind] + ".schema.json"))
        Draft202012Validator.check_schema(schema)
        if kind != "request":
            outputs = schema["properties"]["outputs"]
            items = outputs.get("items")
            expected = self.contracts.operation(AGENT, OPERATIONS[kind])["output_record_types"]
            if items is False:
                contracts.require(outputs.get("type") == "array" and outputs.get("maxItems") == 0,
                                  "Receipt schema whitelist mismatch: this program returns no business records")
            else:
                branches = items.get("oneOf") or [items]
                types = [branch["properties"]["record_type"]["const"] for branch in branches]
                contracts.require(len(types) == len(expected) and set(types) == {
                    f"agtxiv.v3.{name}/0.0.0" for name in expected}, "Receipt schema whitelist mismatch")
                for branch, record_type in zip(branches, types):
                    business = self.contracts.base.by_type[record_type]
                    contracts.require(branch["properties"]["payload"] == {
                        "$ref": business["$id"] + "#/properties/payload"},
                        "Receipt payload must directly reference its pinned business type")
        registry = self.contracts.registry.with_resource(schema["$id"], Resource.from_contents(schema))
        resolver = registry.resolver(base_uri=schema["$id"])
        for _, node in walk(schema):
            if "$ref" in node:
                resolver.lookup(node["$ref"])
        return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())

    def check(self, kind, value):
        report = report_for(kind)

        def require(ok, code, path, message):
            if not ok:
                report["errors"].append({"code": code, "path": path, "message": message})

        report["checked"].append("schema")
        for error in self.validator(kind).iter_errors(value):
            require(False, "SCHEMA", "/" + "/".join(map(str, error.absolute_path)),
                    "Record must match its type/payload branch." if error.validator == "oneOf" else error.message)
        if report["errors"]:
            report["unchecked"]["interface_rules_and_task"] = "Input schema failed; dependent checks were skipped."
            return report

        if kind == "request":
            report["checked"].append("request_operation_and_inputs")
            try:
                operation = self.contracts.operation(AGENT, value["operation"])
            except contracts.InterfaceError as error:
                require(False, "REQUEST_OPERATION", "/operation", str(error))
            else:
                try:
                    contracts.check_ref_set(value["input_refs"])
                except contracts.InterfaceError as error:
                    require(False, "REQUEST_REFS", "/input_refs", str(error))
                allowed = set(operation["input_record_types"]) | contracts.CONTEXT_TYPES
                require({contracts.short_type(r) for r in value["input_refs"]} <= allowed,
                        "REQUEST_INPUT", "/input_refs",
                        "The request names an input family this operation is not allowed to read.")
                outputs = set(operation["output_record_types"])
                declared = {name.removeprefix("agtxiv.v3.").removesuffix("/0.0.0")
                            for name in value["expected_record_types"]}
                require(declared <= outputs,
                        "REQUEST_OUTPUT", "/expected_record_types",
                        "The request expects a record type this operation cannot produce.")
        else:
            report["checked"].append("receipt_outputs_and_diagnostics")
            operation = self.contracts.operation(AGENT, OPERATIONS[kind])
            declared = {contracts.short_type(record) for record in value["outputs"]}
            require(declared <= set(operation["output_record_types"]), "RECEIPT_OUTPUT", "/outputs",
                    "A receipt returns a record type outside this operation's output whitelist.")
            execution = value["execution"]
            host_mode = execution.get("host_mode") if isinstance(execution, dict) else None
            require(host_mode == "EXECUTED" or not value["outputs"], "DIAGNOSTIC_OUTPUT", "/outputs",
                    "A receipt without EXECUTED host_mode must not claim business outputs; diagnostics are not delivery.")
            if (not value["outputs"] and not value["artifacts"]
                    and not any(text.strip() for text in value["open_items"])):
                require(False, "EMPTY_RECEIPT", "/",
                        "A receipt with no outputs, no artifacts and no open item states nothing.")
            report["checked"].extend(["follow_up_agent_operation_pairs", "follow_up_input_refs_and_families"])
            for i, request in enumerate(value["follow_up_requests"]):
                try:
                    target = self.contracts.operation(request["agent"], request["operation"])
                except contracts.InterfaceError as error:
                    require(False, "FOLLOW_UP_OPERATION", f"/follow_up_requests/{i}", str(error))
                    continue
                try:
                    contracts.check_ref_set(request["input_refs"])
                    allowed = set(target["input_record_types"]) | contracts.CONTEXT_TYPES
                    if request["operation"] == "review.backtranslate":
                        allowed = {"formal-environment"}
                    contracts.require({contracts.short_type(r) for r in request["input_refs"]} <= allowed,
                                      "Disallowed follow-up input family")
                except contracts.InterfaceError as error:
                    require(False, "FOLLOW_UP_INPUT", f"/follow_up_requests/{i}/input_refs", str(error))
        report["checks_passed"] = not report["errors"]
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=sorted(SCHEMAS))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args(argv)
    try:
        value = contracts.read_json(args.input)
        report = InterfaceChecker().check(args.kind, value)
        status = 0 if report["checks_passed"] else 1
        if status == 0 and args.fail_on_warning and report["warnings"]:
            status = 1
    except (OSError, ValueError, KeyError, TypeError, RecursionError, ContractError, SchemaError, Unresolvable) as error:
        report = report_for(args.kind)
        report["unchecked"]["interface"] = "Input or checker setup failed; checks were not completed."
        report["errors"].append({"code": "INPUT_ERROR", "path": "", "message": str(error)})
        status = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
