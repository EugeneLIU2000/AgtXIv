#!/usr/bin/env python3
"""Read-only Delta interface checks. Exit 0: checked layers pass; 1: fail; 2: input error.

Reads JSON only. No model call, no retrieval, no assembly, no Result, no approval.
The checker compares reference identities; it never resolves a referenced record, so it
cannot see what a baseline covers, when it was fixed, or whether prior work exists.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("delta_contracts", DIRECTORY.parent / "validate.py")
contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contracts)

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Resource
from referencing.exceptions import Unresolvable
from agtxiv_v3.contracts import ContractError, REF_KEYS

AGENT = "delta"
SCHEMAS = {"delta": "delta-draft"}
OPERATIONS = {"delta": "delta.compare"}
UNCHECKED = {
    "record_set": "No RecordSet, stored envelopes/hashes, root record constraints or reference closure checked.",
    "source_bytes": "Source bytes and provenance are not checked.",
    "execution_identity": "Actual producer identity, visibility and independence are not checked.",
    "meaning": "Scientific correctness and source meaning are not checked.",
    "result": "No Result, delivery outcome or approval is produced.",
    "baseline_fixation_time": (
        "WHEN the baseline was pinned is not checked. A draft carries no time, and the checker sees only"
        " reference identities, so a baseline chosen after the result was known passes this check exactly"
        " like a baseline fixed at the start of the work."),
    "baseline_content": (
        "The baseline-snapshot record is not resolved: its domain, selection_method, search_coverage and"
        " limitations are never read. Only the identity of the reference is compared."),
    "prior_art": (
        "Whether relevant prior work exists outside the pinned baseline is not checked. An empty prior_refs"
        " means nothing was compared here; it is not evidence that nothing exists."),
    "relation_evidence": (
        "relation-assessment records are not resolved: whether they were independently produced, and whether"
        " they witness the relation claimed here, is not checked."),
    "qualification_meaning": (
        "qualifications and author_declaration are checked for being nonblank strings only. Whether a"
        " qualification actually states the baseline's coverage gap, and whether the author's own novelty"
        " statement was copied into it, are not checked."),
    "record_conditionals": (
        "The draft references only the v0.0 '#/properties/payload' subschema, so the business schemas'"
        " root-level if/then gates are not inherited. They are re-implemented here for contribution-delta"
        " (SUPPORTED needs relation_refs) and frontier-item (RESOLVED/SUPERSEDED needs resolution_refs);"
        " a record assembled outside this checker is not covered by these two rules."),
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
        baseline = contracts.ref_key(value["baseline_ref"])
        for i, record in enumerate(value["records"]):
            name, p = contracts.short_type(record), record["payload"]
            path = f"/records/{i}/payload"
            if name == "contribution-delta":
                self.check_contribution_delta(p, path, baseline, require)
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
                        "A Task is required in this mode; a comparison without a fixed Task is not acceptable.")
            report["unchecked"]["task"] = ("No Task supplied: operation, the pinned baseline, the assigned current"
                                           " object, declared output types and exact input visibility are not checked.")
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
                report["checked"].append("task_pinned_baseline_and_assigned_current")
                baselines = [r for r in task["input_refs"] if contracts.short_type(r) == "baseline-snapshot"]
                require(len(baselines) == 1 and value["baseline_ref"] == baselines[0], "TARGET_BASELINE",
                        "/baseline_ref",
                        "baseline_ref must exactly match the unique baseline-snapshot in Task.input_refs.")
                assigned = {contracts.ref_key(r) for r in task["target_refs"]
                            if contracts.short_type(r) != "baseline-snapshot"}
                deltas = [record for record in value["records"]
                          if contracts.short_type(record) == "contribution-delta"]
                compared = {contracts.ref_key(r) for record in deltas for r in record["payload"]["current_refs"]}
                declared = {contracts.ref_key(r) for record in value["records"]
                            if contracts.short_type(record) == "frontier-item"
                            for r in record["payload"]["target_refs"]}
                missing = sorted(assigned - compared - declared)
                missing_ids = ", ".join(str(reference[1]) for reference in missing)
                require(not deltas or not missing, "UNCOVERED_TARGET", "/records",
                        "Every assigned non-baseline Task target must be compared by a contribution-delta or "
                        "declared as a frontier-item target; missing: " + missing_ids)
        report["checks_passed"] = not report["errors"]
        return report

    @staticmethod
    def check_contribution_delta(p, path, baseline, require):
        """Draft-layer rules for one contribution-delta payload.

        Stricter than the v0.0 business schema on purpose, and only here: SUPPORTED_WITHOUT_PRIOR and
        DRAFT_REVIEW_UNESTABLISHED have no counterpart in schema v0.0, so a record that this function
        rejects may still be schema-valid once assembled. Recorded as such in validation-report.json.
        """
        current = [contracts.ref_key(r) for r in p["current_refs"]]
        prior = [contracts.ref_key(r) for r in p["prior_refs"]]
        require(p["review"]["independence"] == "UNESTABLISHED", "DRAFT_REVIEW_UNESTABLISHED",
                path + "/review/independence",
                "A draft may only declare UNESTABLISHED; real identity and separation are the host's.")
        require(contracts.ref_key(p["baseline_ref"]) == baseline, "BASELINE_MISMATCH", path + "/baseline_ref",
                "Every delta in one draft is measured against the draft's single pinned baseline_ref.")
        require(baseline not in current, "BASELINE_AS_CURRENT", path + "/current_refs",
                "The baseline cannot also be this paper's result; a comparison needs two distinct endpoints.")
        require(baseline not in prior, "BASELINE_AS_PRIOR", path + "/prior_refs",
                "The baseline is the pinned frame, not one of the prior objects compared inside it.")
        require(not (set(current) & set(prior)), "CURRENT_PRIOR_OVERLAP", path + "/prior_refs",
                "The same exact record cannot be both the current object and the prior object compared.")
        require(len(set(current)) == len(current), "DUPLICATE_CURRENT", path + "/current_refs",
                "current_refs must list each exact record once.")
        require(p["outcome"] != "SUPPORTED" or bool(p["relation_refs"]), "SUPPORTED_WITHOUT_RELATION",
                path + "/relation_refs",
                "SUPPORTED requires at least one independently assessed relation-assessment.")
        require(p["outcome"] != "SUPPORTED" or bool(prior), "SUPPORTED_WITHOUT_PRIOR", path + "/prior_refs",
                "SUPPORTED requires a prior object that was actually compared; finding nothing in a bounded"
                " search is not a supported contribution.")
        require(all(text.strip() for text in p["qualifications"]), "BLANK_QUALIFICATION",
                path + "/qualifications",
                "Each qualification must state a real baseline-coverage or unresolved limitation.")
        reviewed = {contracts.ref_key(r) for r in p["review"]["reviewed_refs"]}
        require(set(current) <= reviewed, "REVIEWED_REFS_COVERAGE", path + "/review/reviewed_refs",
                "Every current object assessed by this delta must appear in review.reviewed_refs.")


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
