#!/usr/bin/env python3
"""One-off execution probes for PENDING_TESTS.md DL-01..DL-04.

Run from the repository root:
  .venv/bin/python -B 'schema v0.1/test-runs/2026-09-15-pending/probes/probe_delta.py'
"""
import copy
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "delta_interfaces", "schema v0.1/Delta Agent/check_interfaces.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
CHECKER = m.InterfaceChecker()
FIXTURES = Path("schema v0.1/Delta Agent/conformance")


def run(case_id, draft, task=None, expect_pass=True, expect_codes=(), note=""):
    report = CHECKER.check("delta", draft, task)
    codes = sorted({error["code"] for error in report["errors"]})
    matched = report["checks_passed"] == expect_pass and set(expect_codes) <= set(codes)
    print(json.dumps({"id": case_id, "checks_passed": report["checks_passed"], "codes": codes,
                      "expected_pass": expect_pass, "verdict": "MATCH" if matched else "DIVERGES",
                      "note": note}, ensure_ascii=False))


def refs_in(value):
    found = {}
    def walk(node):
        if isinstance(node, dict):
            if set(node) == {"record_type", "record_id", "revision", "content_hash"}:
                found[m.contracts.ref_key(node)] = node
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
    walk(value)
    return found


base_draft = json.loads((FIXTURES / "delta-draft.json").read_text(encoding="utf-8"))

# --- DL-01 unique pinned baseline ------------------------------------------------------------------
d = copy.deepcopy(base_draft)
d["baseline_ref"] = None
run("DL-01a", d, None, False, ("SCHEMA",), "null baseline is schema-rejected")

d = copy.deepcopy(base_draft)
delta = d["records"][0]["payload"]
delta["baseline_ref"] = dict(delta["baseline_ref"], record_id="baseline-snapshot:other")
run("DL-01b", d, None, False, ("BASELINE_MISMATCH",), "delta cannot use a second baseline")

d = copy.deepcopy(base_draft)
delta = d["records"][0]["payload"]
delta["current_refs"].append(copy.deepcopy(d["baseline_ref"]))
run("DL-01c", d, None, False, ("BASELINE_AS_CURRENT",), "baseline cannot double as the current object")

# --- DL-03 supported needs prior and relation -------------------------------------------------------
d = copy.deepcopy(base_draft)
delta = d["records"][0]["payload"]
delta.update(outcome="SUPPORTED", prior_refs=[], relation_refs=[])
run("DL-03", d, None, False, ("SUPPORTED_WITHOUT_RELATION", "SUPPORTED_WITHOUT_PRIOR"),
    "SUPPORTED without prior or relation witness is rejected")

# --- DL-04 author declaration is not evidence (semantic layer, not machine-checked) -----------------
d = copy.deepcopy(base_draft)
delta = d["records"][0]["payload"]
delta["author_declaration"] = "The paper states that this is the first result to drop the commuting assumption."
run("DL-04", d, None, True, (),
    "declaration passes; the checker does not compare claims of first-ness with evidence (human layer)")

# --- DL-02 multi-target coverage (G-07 known gap) ---------------------------------------------------
d = copy.deepcopy(base_draft)
compared = d["records"][0]["payload"]["current_refs"][0]
extra = [dict(compared, record_id="math-claim:current-2"), dict(compared, record_id="math-claim:current-3")]
task = {"contract_version": "0.1.0", "task_id": "probe-DL02", "agent": "delta", "operation": "delta.compare",
        "brief": "Compare the current results against the pinned baseline.",
        "target_refs": [compared] + extra,
        "input_refs": list(refs_in(d).values()) + extra,
        "input_artifacts": [], "depends_on": [],
        "expected_record_types": sorted({m.contracts.short_type(r) for r in d["records"]}),
        "limits": {"max_attempts": 1, "max_seconds": 60, "max_cost_units": 0, "no_progress_limit": 1},
        "acceptance": "DELIVERY", "exclusions": ["agent:synthetic-claim-producer"],
        "capabilities": ["records.read", "delta.compare"]}
run("DL-02", d, task, True, (),
    "documents G-07: one compared target satisfies the intersection rule, so two assigned targets stay unreported")
