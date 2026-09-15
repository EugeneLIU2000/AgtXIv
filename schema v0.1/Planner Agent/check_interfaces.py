#!/usr/bin/env python3
"""Read-only interface checks for planner.propose. Exit 0: checked layers pass; 1: fail; 2: input error.

Reads JSON only. No model call, no Task creation, no scheduling, no budget accounting,
no assembly, no Result, no approval. A proposal that passes here is a suggestion, not
accepted work: the host scheduler and utility.register-plan decide what becomes real.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("planner_contracts", DIRECTORY.parent / "validate.py")
contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contracts)

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Resource
from referencing.exceptions import Unresolvable
from agtxiv_v3.contracts import ContractError, REF_KEYS

AGENT = "planner"
SCHEMAS = {"propose": "propose-draft"}
OPERATIONS = {"propose": "planner.propose"}
SELF_OPERATION = "planner.propose"
REASON_ORDER = ("target=", "; need=", "; purpose=")
OPEN_ITEM_ORDER = ("target=", "; missing=", "; checked=", "; next=")
UNCHECKED = {
    "record_set": "No RecordSet, stored envelopes/hashes, root record constraints or reference closure checked.",
    "source_bytes": "Source bytes and provenance are not checked.",
    "execution_identity": "Actual producer identity, visibility and independence are not checked.",
    "meaning": "Scientific correctness and source meaning are not checked.",
    "result": "No Result, delivery outcome or approval is produced.",
    "plan_quality": ("Whether a proposal is well founded, bounded, non-redundant, decomposed to a useful depth or "
                     "an answer to the user's actual goal is not checked; only its agent/operation pair, input "
                     "families and reference visibility are."),
    "required_inputs_of_proposed_operation": ("Whether the proposed operation's required inputs are complete, whether "
                                              "the referenced records exist, and whether the scheduler would accept "
                                              "the proposal are not checked; that is the host's decision."),
    "budget_and_no_progress": ("Parent budget reservation, cost, attempt, time and no-progress accounting live in the "
                               "host. This checker cannot see the parent plan's remaining allowance, so it cannot tell "
                               "a bounded fan-out from one that exhausts the tree budget."),
    "escalation_in_prose": ("The draft has no key for capabilities, exclusions, limits, acceptance or "
                            "expected_record_types, so a structured escalation fails the schema. The same request "
                            "written as prose inside reason, blocked_on or open_items PASSES this checker."),
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


def ordered_text(text, order):
    """True when text uses the fixed field order verbatim. Format only, never a claim about content."""
    position = -1
    for marker in order:
        found = text.find(marker, position + 1)
        if found <= position:
            return False
        position = found
    return True


def proposal_key(request):
    return (request["agent"], request["operation"],
            frozenset(contracts.ref_key(ref) for ref in request["input_refs"]))


class InterfaceChecker:
    def __init__(self):
        self.contracts = contracts.Contracts()

    def validator(self, kind):
        schema = contracts.read_json(DIRECTORY / (SCHEMAS[kind] + ".schema.json"))
        Draft202012Validator.check_schema(schema)
        expected = self.contracts.operation(AGENT, OPERATIONS[kind])["output_record_types"]
        contracts.require(expected == [], (
            f"Draft schema whitelist mismatch: {OPERATIONS[kind]} no longer has an empty output_record_types; "
            "this module's shape is only valid for an agent that produces no business records"))
        records = schema["properties"]["records"]
        contracts.require(records.get("type") == "array" and records.get("maxItems") == 0
                          and records.get("items") is False,
                          "Draft schema whitelist mismatch: an empty output whitelist requires "
                          '"records": {"type": "array", "maxItems": 0, "items": false}')
        registry = self.contracts.registry.with_resource(schema["$id"], Resource.from_contents(schema))
        resolver = registry.resolver(base_uri=schema["$id"])
        for _, node in walk(schema):
            if "$ref" in node:
                resolver.lookup(node["$ref"])
        return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())

    def check_requests(self, requests, field, codes, report, require, warn, task_supplied):
        """Shared gate for proposals and follow_up_requests: the only channel this agent has."""
        operation_code, input_code = codes
        seen = {}
        for i, request in enumerate(requests):
            path = f"/{field}/{i}"
            try:
                operation = self.contracts.operation(request["agent"], request["operation"])
            except contracts.InterfaceError as error:
                require(False, operation_code, path, str(error))
                continue
            try:
                contracts.check_ref_set(request["input_refs"])
                allowed = set(operation["input_record_types"]) | contracts.CONTEXT_TYPES
                if request["operation"] == "review.backtranslate":
                    allowed = {"formal-environment"}
                contracts.require({contracts.short_type(r) for r in request["input_refs"]} <= allowed,
                                  "Disallowed proposed input family")
            except contracts.InterfaceError as error:
                require(False, input_code, path + "/input_refs", str(error))
            key = proposal_key(request)
            require(key not in seen, "DUPLICATE_PROPOSAL", path,
                    f"Same agent, operation and input_refs already proposed at index {seen.get(key)}; "
                    "the scheduler cannot tell two identical work orders apart.")
            seen.setdefault(key, i)
            if not ordered_text(request["reason"], REASON_ORDER):
                warn("REASON_FORMAT", path + "/reason",
                     "reason must use the fixed order target=...; need=...; purpose=... . "
                     "Correct format is not a valid justification.")
            if request["operation"] == SELF_OPERATION:
                message = ("A planner cannot schedule itself. Every proposed ref must already be an exact Task input, "
                           "so a further planner.propose adds no source, evidence or gap reduction; re-planning is "
                           "started by the scheduler after new records land.")
                if task_supplied:
                    require(False, "SELF_REDISPATCH", path, message)
                else:
                    warn("SELF_REDISPATCH", path, message + " Without a Task, visibility cannot be checked here.")
        return seen

    def check(self, kind, value, task=None, require_task=False):
        report = report_for(kind)

        def require(ok, code, path, message):
            if not ok:
                report["errors"].append({"code": code, "path": path, "message": message})

        def warn(code, path, message):
            report["warnings"].append({"code": code, "path": path, "message": message})

        report["checked"].append("schema")
        for error in self.validator(kind).iter_errors(value):
            require(False, "SCHEMA", "/" + "/".join(map(str, error.absolute_path)), error.message)
        if report["errors"]:
            report["unchecked"]["interface_rules_and_task"] = "Input schema failed; dependent checks were skipped."
            return report

        report["checked"].append("no_business_records")
        for path, node in walk(value):
            require("payload" not in node, "SMUGGLED_RECORD", path,
                    "This agent has no business outputs; a payload object cannot be delivered here.")
            require("record_type" not in node or set(node) == REF_KEYS, "SMUGGLED_RECORD", path,
                    "Only exact RecordRefs may carry record_type in this draft.")

        report["checked"].extend(["proposal_agent_operation_pairs", "proposal_input_refs_and_families",
                                  "follow_up_agent_operation_pairs", "follow_up_input_refs_and_families"])
        proposed = self.check_requests(value["proposals"], "proposals",
                                       ("PROPOSAL_OPERATION", "PROPOSAL_INPUT"),
                                       report, require, warn, task is not None)
        self.check_requests(value["follow_up_requests"], "follow_up_requests",
                            ("FOLLOW_UP_OPERATION", "FOLLOW_UP_INPUT"),
                            report, require, warn, task is not None)
        report["checked"].append("follow_up_subset_of_proposals")
        for i, request in enumerate(value["follow_up_requests"]):
            require(proposal_key(request) in proposed, "FOLLOW_UP_NOT_PROPOSED", f"/follow_up_requests/{i}",
                    "Every handover request must also appear in proposals; the proposal list is the complete "
                    "attachment the host reviews.")
        report["checked"].append("follow_up_requires_unblocked_proposal")
        proposals_by_key = {proposal_key(request): request for request in value["proposals"]}
        for i, request in enumerate(value["follow_up_requests"]):
            proposal = proposals_by_key.get(proposal_key(request))
            require(proposal is None or not proposal["blocked_on"], "FOLLOW_UP_BLOCKED", f"/follow_up_requests/{i}",
                    "A proposal with declared blocked_on preconditions is not ready work; the scheduler must not "
                    "receive it as a follow-up until those preconditions are resolved.")
        for i, text in enumerate(value["open_items"]):
            if not ordered_text(text, OPEN_ITEM_ORDER):
                warn("OPEN_ITEM_FORMAT", f"/open_items/{i}",
                     "open_items must use the fixed order target=...; missing=...; checked=...; next=... .")
        for i, request in enumerate(value["proposals"]):
            for j, text in enumerate(request["blocked_on"]):
                if not ordered_text(text, OPEN_ITEM_ORDER):
                    warn("OPEN_ITEM_FORMAT", f"/proposals/{i}/blocked_on/{j}",
                         "blocked_on uses the same fixed order as open_items.")

        if task is None:
            if require_task:
                require(False, "TASK_REQUIRED", "/task",
                        "A Task is required in this mode; a draft without a fixed Task is not acceptable.")
            report["unchecked"]["task"] = ("No Task supplied: operation, empty expected_record_types, exact input "
                                           "visibility and self-redispatch are not checked.")
        else:
            report["checked"].append("task_declared_outputs")
            require(not (isinstance(task, dict) and task.get("expected_record_types")),
                    "NONEMPTY_EXPECTED_TYPES", "/task/expected_record_types",
                    "planner.propose has an empty output whitelist; a declared business output is not schedulable. "
                    "This is also rejected by the shared Task contract, with a less specific message.")
            report["checked"].append("task_contract")
            try:
                self.contracts.task(task)
                contracts.require(task["operation"] == OPERATIONS[kind],
                                  f"{kind} requires Task operation {OPERATIONS[kind]}")
            except contracts.InterfaceError as error:
                require(False, "TASK_CONTRACT", "/task", str(error))
                report["unchecked"]["task_bindings"] = "Task contract failed; bindings were skipped."
            else:
                report["checked"].append("task_exact_refs")
                visible = {contracts.ref_key(ref) for ref in task["input_refs"]}
                for path, node in walk(value):
                    if set(node) == REF_KEYS:
                        require(contracts.ref_key(node) in visible, "INVISIBLE_REF", path,
                                "RecordRef must be an exact Task.input_refs member; a proposal cannot name a record "
                                "the planner was not given, nor a future identity.")
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
