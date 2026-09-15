#!/usr/bin/env python3
"""Read-only interface checks. Exit 0: checked layers pass; 1: fail; 2: input error.

Only JSON is read; Lean source is neither written, scanned for proof claims, nor run.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
DIRECTORY = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("autoformalization_contracts", DIRECTORY.parent / "validate.py")
contracts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(contracts)

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError
from referencing import Resource
from referencing.exceptions import Unresolvable
from agtxiv_v3.contracts import ContractError, REF_KEYS

SCHEMAS = {"proof": "proof-draft", "view": "lamport-view", "lean": "lean-draft"}
UNCHECKED = {
    "record_set": "No RecordSet, stored envelopes/hashes, root record constraints or reference closure checked.",
    "source_bytes": "Source bytes and provenance are not checked.",
    "execution_identity": "Actual producer identity, visibility and independence are not checked.",
    "context_resolution_and_mapping": "Context records are not resolved: scope, packet payload/expected-declaration coverage and node/inference/declaration correspondence are not checked; mapping correctness is not established.",
    "lean": "Lean is not run; compilation, absence of sorry/axioms and declaration existence are not checked.",
    "meaning": "Mathematical correctness, source meaning and formal alignment are not checked.",
    "result": "No Result, delivery outcome, formal-check or approval is produced.",
}


def report_for(kind):
    return {"kind": kind, "checks_passed": False, "checked": [], "unchecked": dict(UNCHECKED), "errors": []}


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
        if kind in {"proof", "lean"}:
            items = schema["properties"]["records"]["items"]
            branches = items["oneOf"] if kind == "proof" else [items]
            expected = (self.contracts.operation("proof", "proof.expand")["output_record_types"]
                        if kind == "proof" else ["frontier-item"])
            types = [b["properties"]["record_type"]["const"] for b in branches]
            contracts.require(len(types) == len(expected) and set(types) == {
                f"agtxiv.v3.{name}/0.0.0" for name in expected}, "Draft schema whitelist mismatch")
            for branch, record_type in zip(branches, types):
                business = self.contracts.base.by_type[record_type]
                contracts.require(branch["properties"]["payload"] == {
                    "$ref": business["$id"] + "#/properties/payload"}, "Draft payload must directly reference its pinned business type")
        registry = self.contracts.registry.with_resource(schema["$id"], Resource.from_contents(schema))
        resolver = registry.resolver(base_uri=schema["$id"])
        for _, node in walk(schema):
            if "$ref" in node:
                resolver.lookup(node["$ref"])
        return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())

    def check(self, kind, value, task=None):
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
        for i, record in enumerate(value.get("records", [])):
            name, p = contracts.short_type(record), record["payload"]
            path = f"/records/{i}/payload"
            if name == "argument-node":
                require(p["origin"] != "SOURCE" or bool(p["source_span_refs"]), "SOURCE_SPANS", path,
                        "SOURCE nodes require source_span_refs.")
            if name == "inference-step":
                require(p["conclusion_ref"] not in p["premise_refs"], "SELF_PREMISE", path,
                        "The conclusion cannot be its own premise.")
                require(p["rule"] != "ASSUMPTION_DISCHARGE" or bool(p["discharged_context_refs"]),
                        "DISCHARGE_CONTEXT", path, "Discharge requires discharged_context_refs.")
                require(not p["discharged_context_refs"] or p["rule"] in {
                    "ASSUMPTION_DISCHARGE", "CONTRADICTION", "CASE_SPLIT", "INDUCTION"},
                    "INVALID_DISCHARGE_RULE", path + "/rule", "This rule cannot discharge a local assumption context.")
                require(not (p["discharged_context_refs"] or p["rule"] in {
                    "ASSUMPTION_DISCHARGE", "CASE_SPLIT", "INDUCTION"}) or bool(p["rule_evidence_refs"]),
                    "RULE_EVIDENCE", path, "Discharge, CASE_SPLIT and INDUCTION require rule_evidence_refs.")
        if kind == "view":
            self.check_view(value, require)
        if kind == "lean":
            self.check_lean(value, require)
        report["checked"].extend(["follow_up_agent_operation_pairs", "follow_up_input_refs_and_families"])
        for i, request in enumerate(value.get("follow_up_requests", [])):
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
            report["unchecked"]["task"] = "No Task supplied: operation, target packet, draft output types and exact input visibility are not checked."
        else:
            report["checked"].append("task_contract")
            try:
                self.contracts.task(task)
                expected_op = {"proof": "proof.expand", "lean": "formalization.generate"}.get(kind)
                contracts.require(expected_op is None or task["operation"] == expected_op,
                                  f"{kind} requires Task operation {expected_op}")
            except contracts.InterfaceError as error:
                require(False, "TASK_CONTRACT", "/task", str(error))
                report["unchecked"]["task_bindings"] = "Task contract failed; bindings were skipped."
            else:
                report["checked"].append("task_exact_refs_and_declared_outputs")
                visible = {contracts.ref_key(ref) for ref in task["input_refs"]}
                for path, node in walk(value):
                    if set(node) == REF_KEYS:
                        require(contracts.ref_key(node) in visible, "INVISIBLE_REF", path,
                                "RecordRef must be an exact Task.input_refs member; draft outputs do not supply new refs.")
                for i, record in enumerate(value.get("records", [])):
                    require(contracts.short_type(record) in task["expected_record_types"], "UNDECLARED_OUTPUT",
                            f"/records/{i}", "Draft record type was not predeclared by the Task.")
                if kind == "lean":
                    packets = [r for r in task["target_refs"] if contracts.short_type(r) == "formalization-packet"]
                    require(len(packets) == 1 and value["packet_ref"] == packets[0], "TARGET_PACKET", "/packet_ref",
                            "packet_ref must exactly match the unique formalization-packet in Task.target_refs.")
        report["checks_passed"] = not report["errors"]
        return report

    @staticmethod
    def check_view(value, require):
        entries = value["entries"]
        index = {e["label"]: e for e in entries}
        require(len(index) == len(entries), "DUPLICATE_LABEL", "/entries", "Labels must be unique.")
        roots = [e for e in entries if e["parent_label"] is None]
        require(len(roots) == 1 and roots[0]["role"] == "GOAL", "ROOT_GOAL", "/entries", "Exactly one root GOAL is required.")
        children = {}
        for i, entry in enumerate(entries):
            label, parent = entry["label"], entry["parent_label"]
            path = f"/entries/{i}"
            require(re.fullmatch(r"[1-9][0-9]*(\.[1-9][0-9]*)*", label) is not None,
                    "LABEL_PATH", path, "Labels must be positive integers separated by dots.")
            require(parent is None or parent in index, "MISSING_PARENT", path, "Parent label must exist.")
            require(parent == (label.rsplit(".", 1)[0] if "." in label else None),
                    "PARENT_PATH", path, "Parent must match the numeric path prefix.")
            children.setdefault(parent, []).append(entry)
        for label, entry in index.items():
            descendants = children.get(label, [])
            if descendants:
                require(entry["role"] == "GOAL", "NON_GOAL_CHILDREN", "/entries", "Only GOAL entries may have children.")
                # Numeric sibling order, including 1.9 before 1.10; input order is immaterial.
                last = max(descendants, key=lambda e: tuple(map(int, e["label"].split("."))))
                require(last["role"] == "QED" and last["node_ref"] == entry["node_ref"],
                        "GOAL_QED", "/entries", f"Goal {label} must end with a QED referencing the same exact node.")

    @staticmethod
    def check_lean(value, require):
        paths = [file["path"] for file in value["files"]]
        for i, path in enumerate(paths):
            parts = path.split("/")
            safe = (path.endswith(".lean") and not any(c in path for c in "\\:")
                    and all(ord(c) >= 32 and ord(c) != 127 for c in path)
                    and all(p not in {"", ".", ".."} for p in parts)
                    and not any(p.casefold() in {"lakefile.lean", "lakefile.toml", "lean-toolchain"} for p in parts))
            require(safe, "UNSAFE_PATH", f"/files/{i}/path", "Use safe relative .lean paths; project configuration files are forbidden.")
        require(len(paths) == len({p.casefold() for p in paths}), "PATH_COLLISION", "/files", "File paths must be unique under casefold.")
        targets = [e["declaration"] for e in value["declaration_map"] if e["role"] == "TARGET"]
        require(len(targets) == len(set(targets)), "DUPLICATE_TARGET", "/declaration_map", "TARGET declarations must be unique.")
        require(bool(targets) or any(s.strip() for s in value["open_items"]),
                "TARGET_REQUIRED", "/declaration_map", "A draft without a TARGET requires a nonblank open_items reason, including partial helper-only code.")
        for i, entry in enumerate(value["declaration_map"]):
            require(entry["role"] != "TARGET" or entry["local_name"] is None, "TARGET_LOCAL_NAME",
                    f"/declaration_map/{i}/local_name", "TARGET maps a complete declaration; local_name must be null.")
            require(entry["code_path"] in paths, "MISSING_CODE_PATH", f"/declaration_map/{i}/code_path", "code_path must name a supplied file.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=SCHEMAS)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--task", type=Path)
    args = parser.parse_args(argv)
    try:
        value = contracts.read_json(args.input)
        task = contracts.read_json(args.task) if args.task else None
        contracts.require(not args.task or task is not None, "--task must contain a Task object, not JSON null")
        report = InterfaceChecker().check(args.kind, value, task)
        status = 0 if report["checks_passed"] else 1
    except (OSError, ValueError, KeyError, TypeError, RecursionError, ContractError, SchemaError, Unresolvable) as error:
        report = report_for(args.kind)
        report["unchecked"]["interface"] = "Input or checker setup failed; checks were not completed."
        report["errors"].append({"code": "INPUT_ERROR", "path": "", "message": str(error)})
        status = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
