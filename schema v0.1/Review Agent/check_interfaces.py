#!/usr/bin/env python3
"""Read-only Review interface checks. Exit 0: checked layers pass; 1: fail; 2: input error.

Reads JSON only. No model call, no identity assembly, no Result, no approval.
The checker verifies the shared draft boundaries (declared record whitelist, task binding,
follow-up families, blind-input rules from the shared Task contract) and the two draft-layer
rules that can be decided from identities alone. It never resolves an assessment record, so it
cannot see whether a review is independent, correct or scientifically meaningful.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("review_contracts", DIRECTORY.parent / "validate.py")
contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contracts)

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Resource
from referencing.exceptions import Unresolvable
from agtxiv_v3.contracts import ContractError, REF_KEYS

AGENT = "review"
KINDS = ("scope", "argument", "reuse", "backtranslate", "alignment", "scientific", "audit", "admission")
SCHEMAS = {kind: f"{kind}-draft" for kind in KINDS}
OPERATIONS = {kind: f"review.{kind}" for kind in KINDS}
UNCHECKED = {
    "record_set": "No RecordSet, stored envelopes/hashes, root record constraints or reference closure checked.",
    "source_bytes": "Source bytes and provenance are not checked.",
    "independence": (
        "Producer identity, separation and visibility are not established here. A draft may only declare"
        " UNESTABLISHED identity; real independence is assembled by the host from execution facts."),
    "assessment_meaning": (
        "Assessment records are not resolved: whether a review actually examined the claimed object, and"
        " what it concluded, is not checked. Only record identity and the declared record type are compared."),
    "blind_isolation": (
        "Source-blind isolation is enforced only through the shared Task contract; the checker verifies the"
        " fixed input families, not what any interpreter actually read at run time."),
    "record_conditionals": (
        "The draft references only the v0.0 '#/properties/payload' subschema, so business root-level if/then"
        " gates are not inherited. frontier-item (RESOLVED/SUPERSEDED needs resolution_refs) is re-implemented"
        " here; other business conditionals are not."),
    "result": "No Result, delivery outcome or approval is produced.",
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
        records = schema["properties"]["records"]
        items = records.get("items")
        expected = self.contracts.operation(AGENT, OPERATIONS[kind])["output_record_types"]
        if items is False:
            contracts.require(records.get("type") == "array" and records.get("maxItems") == 0,
                              "Draft schema whitelist mismatch: this draft must carry no business records")
        else:
            branches = items.get("oneOf") or [items]
            types = [branch["properties"]["record_type"]["const"] for branch in branches]
            contracts.require(len(types) == len(expected) and set(types) == {
                f"agtxiv.v3.{name}/0.0.0" for name in expected}, "Draft schema whitelist mismatch")
            for branch, record_type in zip(branches, types):
                business = self.contracts.base.by_type[record_type]
                contracts.require(branch["properties"]["payload"] == {
                    "$ref": business["$id"] + "#/properties/payload"},
                    "Draft payload must directly reference its pinned business type")
        registry = self.contracts.registry.with_resource(schema["$id"], Resource.from_contents(schema))
        resolver = registry.resolver(base_uri=schema["$id"])
        for _, node in walk(schema):
            if "$ref" in node:
                resolver.lookup(node["$ref"])
        return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())

    def check(self, kind, value, task=None, require_task=False):
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

        report["checked"].append(kind + "_interface_rules")
        if (kind != "backtranslate" and not value["records"]
                and not any(text.strip() for text in value["open_items"])):
            require(False, "EMPTY_DELIVERY", "/",
                    "A review draft must deliver an assessment record or declare a nonblank open item.")
        for i, record in enumerate(value["records"]):
            name, p = contracts.short_type(record), record["payload"]
            if name == "frontier-item":
                require(p["state"] not in {"RESOLVED", "SUPERSEDED"} or bool(p["resolution_refs"]),
                        "FRONTIER_RESOLUTION", f"/records/{i}/payload/resolution_refs",
                        "RESOLVED or SUPERSEDED requires exact resolution evidence.")

        report["checked"].extend(["follow_up_agent_operation_pairs", "follow_up_input_refs_and_families"])
        for i, request in enumerate(value["follow_up_requests"]):
            try:
                operation = self.contracts.operation(request["agent"], request["operation"])
            except contracts.InterfaceError as error:
                require(False, "FOLLOW_UP_OPERATION", f"/follow_up_requests/{i}", str(error))
                continue
            try:
                contracts.check_ref_set(request["input_refs"])
                allowed = set(operation["input_record_types"]) | contracts.CONTEXT_TYPES
                if request["operation"] == "review.backtranslate":
                    allowed = {"formal-environment"}
                contracts.require({contracts.short_type(r) for r in request["input_refs"]} <= allowed,
                                  "Disallowed follow-up input family")
            except contracts.InterfaceError as error:
                require(False, "FOLLOW_UP_INPUT", f"/follow_up_requests/{i}/input_refs", str(error))

        if task is None:
            if require_task:
                require(False, "TASK_REQUIRED", "/task",
                        "A Task is required in this mode; a review without a fixed Task is not acceptable.")
            report["unchecked"]["task"] = ("No Task supplied: operation, declared output types, blind-input"
                                           " constraints and exact input visibility are not checked.")
        else:
            report["checked"].append("task_contract")
            try:
                self.contracts.task(task)
                contracts.require(task["operation"] == OPERATIONS[kind],
                                  f"{kind} requires Task operation {OPERATIONS[kind]}")
            except contracts.InterfaceError as error:
                require(False, "TASK_CONTRACT", "/task", str(error))
                report["unchecked"]["task_bindings"] = "Task contract failed; bindings were skipped."
            else:
                report["checked"].append("task_exact_refs_and_declared_outputs")
                visible = {contracts.ref_key(ref) for ref in task["input_refs"]}
                for path, node in walk(value):
                    if set(node) == REF_KEYS:
                        require(contracts.ref_key(node) in visible, "INVISIBLE_REF", path,
                                "RecordRef must be an exact Task.input_refs member.")
                for i, record in enumerate(value["records"]):
                    require(contracts.short_type(record) in task["expected_record_types"], "UNDECLARED_OUTPUT",
                            f"/records/{i}", "Draft record type was not predeclared by the Task.")
        report["checks_passed"] = not report["errors"]
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=sorted(SCHEMAS))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--task", type=Path)
    parser.add_argument("--require-task", action="store_true")
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args(argv)
    try:
        value = contracts.read_json(args.input)
        task = contracts.read_json(args.task) if args.task else None
        contracts.require(not args.task or task is not None, "--task must contain a Task object, not JSON null")
        report = InterfaceChecker().check(args.kind, value, task, require_task=args.require_task)
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
