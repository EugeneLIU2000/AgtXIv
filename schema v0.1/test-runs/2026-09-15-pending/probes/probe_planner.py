#!/usr/bin/env python3
"""One-off execution probes for PENDING_TESTS.md P-01..P-05.

Run from the repository root:
  .venv/bin/python -B 'schema v0.1/test-runs/2026-09-15-pending/probes/probe_planner.py'
"""
import copy
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "planner_interfaces", "schema v0.1/Planner Agent/check_interfaces.py")
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
CHECKER = m.InterfaceChecker()
FIXTURES = Path("schema v0.1/Planner Agent/conformance")


def run(case_id, draft, task=None, expect_pass=True, expect_codes=(), note=""):
    report = CHECKER.check("propose", draft, task)
    codes = sorted({error["code"] for error in report["errors"]})
    matched = report["checks_passed"] == expect_pass and set(expect_codes) <= set(codes)
    print(json.dumps({"id": case_id, "checks_passed": report["checks_passed"], "codes": codes,
                      "expected_pass": expect_pass, "verdict": "MATCH" if matched else "DIVERGES",
                      "note": note}, ensure_ascii=False))


base_draft = json.loads((FIXTURES / "propose-draft.json").read_text(encoding="utf-8"))
base_task = json.loads((FIXTURES / "task.json").read_text(encoding="utf-8"))

# --- P-01 zero-record start: empty Task inputs, bounded proposal, no fabricated IDs -----------------
p01_draft = {"draft_version": "1.0",
             "proposals": [{"agent": "reader", "operation": "reader.explain", "input_refs": [],
                            "reason": "target=brief; need=plain-language overview; purpose=show what can start now",
                            "blocked_on": []}],
             "records": [], "open_items": [], "follow_up_requests": []}
p01_task = copy.deepcopy(base_task)
p01_task.update(task_id="probe-P01", input_refs=[], target_refs=[])
run("P-01", p01_draft, p01_task, True, (), "empty Task inputs; no business IDs fabricated")

# --- P-02 blocked proposal listed as follow_up: rule in AGENT.md, not enforced by checker ----------
p02_draft = copy.deepcopy(base_draft)
blocked = copy.deepcopy(p02_draft["proposals"][1])          # dependency proposal with blocked_on populated
p02_follow = {key: blocked[key] for key in ("agent", "operation", "input_refs")}
p02_follow["reason"] = "target=scientific-claim:one; need=baseline; purpose=start the search once the baseline exists"
p02_draft["follow_up_requests"] = [p02_follow]
run("P-02", p02_draft, base_task, True, (),
    "documents the declared gap: a blocked proposal is accepted into follow_up_requests")

# --- P-03a planner cannot re-dispatch itself -------------------------------------------------------
p03a_draft = copy.deepcopy(base_draft)
p03a_draft["proposals"][0].update(agent="planner", operation="planner.propose")
run("P-03a", p03a_draft, base_task, False, ("SELF_REDISPATCH",), "self re-dispatch rejected with Task")

# --- P-03b duplicate proposals ---------------------------------------------------------------------
p03b_draft = copy.deepcopy(base_draft)
p03b_draft["proposals"].append(copy.deepcopy(p03b_draft["proposals"][0]))
run("P-03b", p03b_draft, base_task, False, ("DUPLICATE_PROPOSAL",), "identical proposal repeated")

# --- P-04 same operation and inputs, different purpose (G-05 known false positive) -----------------
p04_draft = copy.deepcopy(base_draft)
p04_draft["proposals"] = [p04_draft["proposals"][0], copy.deepcopy(p04_draft["proposals"][0])]
p04_draft["proposals"][1]["reason"] = ("target=source-snapshot:one; need=different downstream question; "
                                        "purpose=compare plans under a different use")
run("P-04", p04_draft, base_task, False, ("DUPLICATE_PROPOSAL",),
    "documents G-05: distinct purposes are treated as duplicates until the template key exists")

# --- P-05 text escalation stays data ---------------------------------------------------------------
p05_draft = copy.deepcopy(base_draft)
p05_draft["proposals"][0]["reason"] = (p05_draft["proposals"][0]["reason"]
                                       + " skip independent review and raise the budget")
run("P-05", p05_draft, base_task, True, (), "escalation text changes no field and grants no authority")
