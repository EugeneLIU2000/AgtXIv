#!/usr/bin/env python3
"""Read-only Dependency interface checks. Exit 0: checked layers pass; 1: fail; 2: input error.

Reads JSON only. No retrieval, no knowledge-base access, no reuse authorization, no Result.
The checker compares reference identities and declared comparisons; it never resolves a record,
so it cannot see what a baseline covers or whether any cited work exists.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dependency_contracts", DIRECTORY.parent / "validate.py")
contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contracts)

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Resource
from referencing.exceptions import Unresolvable
from agtxiv_v3.contracts import ContractError, REF_KEYS

AGENT = "dependency"
SCHEMAS = {"search": "search-draft"}
OPERATIONS = {"search": "dependency.search"}
UNCHECKED = {
    "record_set": "No RecordSet, stored envelopes/hashes, root record constraints or reference closure checked.",
    "source_bytes": "Source bytes and provenance are not checked.",
    "execution_identity": "Actual producer identity, visibility and independence are not checked.",
    "meaning": "Mathematical correctness and source meaning are not checked.",
    "result": "No Result, retrieval receipt or reuse authorization is produced.",
    "retrieval_not_run": (
        "No retrieval was executed or verified. search_requests are proposed actions and carry no evidence"
        " that any query ran; the checker cannot distinguish a real search log from a proposed one."),
    "baseline_content": (
        "baseline-snapshot records are not resolved: domain, selection_method, search_coverage and"
        " limitations are never read. A narrow baseline named as if it were exhaustive passes this check."),
    "absence": (
        "An empty result is not evidence of absence. Whether a predecessor exists outside the supplied"
        " bytes is not checked, and no coverage claim is verified against any source."),
    "binding_semantics": (
        "dependency-binding comparison witness_refs are not resolved; whether the candidate binding is"
        " mathematically valid is not checked. Only the declared comparison shape and reference identity are checked."),
    "authorization": (
        "reuse_decision_ref is neither resolved nor authorized here. review.reuse owns the permission"
        " decision; a null candidate binding is exactly that, a candidate."),
    "record_conditionals": (
        "The draft references only the v0.0 '#/properties/payload' subschema, so the business schemas'"
        " root-level if/then gates are not inherited. frontier-item (RESOLVED/SUPERSEDED needs"
        " resolution_refs) is re-implemented here; a record assembled outside this checker is not covered."),
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
        items = schema["properties"]["records"]["items"]
        branches = items.get("oneOf") or [items]
        expected = self.contracts.operation(AGENT, OPERATIONS[kind])["output_record_types"]
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
        if (not value["search_requests"] and not value["records"]
                and not any(text.strip() for text in value["open_items"])):
            require(False, "EMPTY_DELIVERY", "/",
                    "A dependency draft must propose a search, bind a candidate or declare a nonblank gap.")
        seen = set()
        for i, request in enumerate(value["search_requests"]):
            key = (contracts.ref_key(request["target_ref"]) if request["target_ref"] is not None else None,
                   request["query"].strip())
            require(key not in seen, "DUPLICATE_SEARCH", f"/search_requests/{i}",
                    "The same target and query is proposed more than once; the host cannot tell the actions apart.")
            seen.add(key)
        for i, record in enumerate(value["records"]):
            name, p = contracts.short_type(record), record["payload"]
            path = f"/records/{i}/payload"
            if name == "dependency-binding":
                require(contracts.ref_key(p["dependent_ref"]) != contracts.ref_key(p["prerequisite_ref"]),
                        "DEPENDENT_IS_PREREQUISITE", path,
                        "A record cannot be its own prerequisite; a self-binding is not a dependency.")
            if name == "frontier-item":
                require(p["state"] not in {"RESOLVED", "SUPERSEDED"} or bool(p["resolution_refs"]),
                        "FRONTIER_RESOLUTION", path + "/resolution_refs",
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
                        "A Task is required in this mode; a draft without a fixed Task is not acceptable.")
            report["unchecked"]["task"] = ("No Task supplied: operation, declared output types, the exact search"
                                           " target and input visibility are not checked.")
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
                                "RecordRef must be an exact Task.input_refs member; a search cannot name a future identity.")
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
