#!/usr/bin/env python3
"""Read-only interface checks for reader.explain. Exit 0: checked layers pass; 1: fail; 2: input error.

Reads JSON only. No model call, no assembly, no record, no Result, no approval. This agent has an
empty output_record_types whitelist, so the strongest check here is negative: nothing record-shaped
may leave in a reader draft. Nothing in this file reads the explanation text itself.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("reader_contracts", DIRECTORY.parent / "validate.py")
contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contracts)

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Resource
from referencing.exceptions import Unresolvable
from agtxiv_v3.contracts import ContractError, REF_KEYS

AGENT = "reader"
SCHEMAS = {"explanation": "explanation-draft"}
OPERATIONS = {"explanation": "reader.explain"}
UNCHECKED = {
    "record_set": "No RecordSet, stored envelopes/hashes, root record constraints or reference closure checked.",
    "source_bytes": "Source bytes and provenance are not checked.",
    "execution_identity": "Actual producer identity, visibility and independence are not checked.",
    "meaning": "Scientific correctness and source meaning are not checked.",
    "result": "No Result, delivery outcome or approval is produced.",
    "explanation_quality": "Explanation text is never read: whether it is correct, readable, matched to the stated"
                           " audience, or an answer to the brief at all is NOT checked here.",
    "opinion_as_support": "Text asserting that something 'looks right', 'is fine' or 'is verified' passes this"
                          " checker unchanged. The draft carries no verdict field, but nothing stops an opinion"
                          " from being written in prose and later quoted as if it were support.",
    "attribution": "The declared attribution value is taken as given; whether the same principal produced the"
                   " explained material is not checked.",
    "gap_fidelity": "Declared gaps are counted, never compared with the open items of the explained records: an"
                    " explanation that silently drops a known gap passes this checker.",
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


def blank(text):
    return not isinstance(text, str) or not text.strip()


class InterfaceChecker:
    def __init__(self):
        self.contracts = contracts.Contracts()

    def validator(self, kind):
        """Load the draft schema and refuse to run if it ever drifts away from agents.json.

        For a no-record agent the drift guard is the mirror image of the usual one: the operation's
        output whitelist must still be empty, and the draft's `records` must still be shaped so that
        no item can be placed in it. Either drifting is a checker/registry failure (exit 2), not a
        finding about the input being checked.
        """
        schema = contracts.read_json(DIRECTORY / (SCHEMAS[kind] + ".schema.json"))
        Draft202012Validator.check_schema(schema)
        expected = self.contracts.operation(AGENT, OPERATIONS[kind])["output_record_types"]
        contracts.require(expected == [], f"Draft schema whitelist mismatch: {OPERATIONS[kind]} must keep an empty "
                                          f"output_record_types, found {expected}")
        records = schema["properties"]["records"]
        contracts.require(records.get("type") == "array" and records.get("maxItems") == 0
                          and records.get("items") is False,
                          "Draft schema must keep business records structurally impossible")
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

        # Runs before the schema gate on purpose: a draft carrying records must be named as smuggling,
        # not merely reported as a shape error, and the scan needs no valid shape to be meaningful.
        report["checked"].append("no_business_records")
        for path, node in walk(value):
            require("payload" not in node, "SMUGGLED_RECORD", path,
                    "This agent has no business outputs; a payload object cannot be delivered here.")
            require("record_type" not in node or set(node) == REF_KEYS, "SMUGGLED_RECORD", path,
                    "Only exact RecordRefs may carry record_type in this draft.")

        report["checked"].append("schema")
        for error in self.validator(kind).iter_errors(value):
            require(False, "SCHEMA", "/" + "/".join(map(str, error.absolute_path)), error.message)
        if report["errors"]:
            report["unchecked"]["interface_rules_and_task"] = "Input schema failed; dependent checks were skipped."
            return report

        report["checked"].append(kind + "_interface_rules")
        require(bool(value["explanations"]) or any(not blank(item) for item in value["open_items"]),
                "EMPTY_EXPLANATION", "/explanations",
                "An empty delivery is not an explanation: give an explanation or a nonblank open item.")
        for i, item in enumerate(value["explanations"]):
            path = f"/explanations/{i}"
            require(not blank(item["text"]), "BLANK_TEXT", path + "/text", "Explanation text cannot be blank.")
            require(not blank(item["audience"]), "BLANK_TEXT", path + "/audience",
                    "The audience this was written for cannot be blank.")
            require(item["target_ref"] is not None or item["basis_refs"]
                    or any(not blank(gap) for gap in item["gaps"]), "UNGROUNDED_EXPLANATION", path,
                    "An explanation with no target and no basis record must declare what it could not ground.")
        # Citing the explained record as its own basis is normal, so identical refs are folded first;
        # what stays forbidden is one identity and revision appearing under two different content hashes.
        refs = [item["target_ref"] for item in value["explanations"] if item["target_ref"] is not None]
        refs += [ref for item in value["explanations"] for ref in item["basis_refs"]]
        try:
            contracts.check_ref_set(list({contracts.ref_key(ref): ref for ref in refs}.values()))
        except contracts.InterfaceError as error:
            require(False, "INCONSISTENT_REF", "/explanations",
                    "One record identity and revision is cited under two different content hashes: " + str(error))

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
            report["unchecked"]["task"] = ("No Task supplied: operation, brief, acceptance gate, declared output "
                                           "types, target coverage and exact input visibility are not checked.")
        else:
            if isinstance(task, dict):
                report["checked"].append("task_reader_preconditions")
                require(not blank(task.get("brief")), "BLANK_BRIEF", "/task/brief",
                        "reader.explain carries real user intent in a nonblank brief; whitespace is not intent.")
                require(not task.get("expected_record_types"), "NONEMPTY_EXPECTED_TYPES",
                        "/task/expected_record_types",
                        "reader.explain has an empty output whitelist; no business output may be predeclared.")
                require(task.get("acceptance") != "EVIDENCE", "EVIDENCE_GATE_ON_READER", "/task/acceptance",
                        "A readability pass cannot satisfy an evidence gate; reader Tasks deliver attachments.")
            report["checked"].append("task_contract")
            try:
                self.contracts.task(task)
                contracts.require(task["operation"] == OPERATIONS[kind],
                                  f"{kind} requires Task operation {OPERATIONS[kind]}")
            except contracts.InterfaceError as error:
                require(False, "TASK_CONTRACT", "/task", str(error))
                report["unchecked"]["task_bindings"] = "Task contract failed; bindings were skipped."
            else:
                report["checked"].append("task_exact_refs_and_target_coverage")
                visible = {contracts.ref_key(ref) for ref in task["input_refs"]}
                for path, node in walk(value):
                    if set(node) == REF_KEYS:
                        require(contracts.ref_key(node) in visible, "INVISIBLE_REF", path,
                                "RecordRef must be an exact Task.input_refs member.")
                explained = {contracts.ref_key(item["target_ref"]) for item in value["explanations"]
                             if item["target_ref"] is not None}
                for i, target in enumerate(task["target_refs"]):
                    require(contracts.ref_key(target) in explained, "UNEXPLAINED_TARGET", f"/task/target_refs/{i}",
                            "Every exact Task target must be the target_ref of an explanation.")
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
