#!/usr/bin/env python3
"""Run the schema v0.1 orchestration and agent contract test suites.

Read-only: no repository files are written. Subprocesses run with bytecode and
pytest cache writing disabled so `git diff --exit-code` stays clean.

Run from anywhere:
  .venv/bin/python -B 'schema v0.1/tests/run_agent_tests.py'
Exit 0: every suite and conformance probe matched its expected exit code.
"""
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PLANNER = "schema v0.1/Planner Agent"
DELTA = "schema v0.1/Delta Agent"
DEPENDENCY = "schema v0.1/Dependency Agent"
REVIEW = "schema v0.1/Review Agent"
UTILITY = "schema v0.1/Utility Agent"

STEPS = (
    ("validate-check", [sys.executable, "-B", "schema v0.1/validate.py", "--check"], 0),
    ("repo-unit", [sys.executable, "-B", "-m", "unittest",
                   "discover", "-s", "schema v0.1/tests", "-q"], 0),
    ("handoff-unit", [sys.executable, "-B", "-m", "unittest",
                      "discover", "-s", "schema v0.1/handoff/tests", "-q"], 0),
    ("paper-autoformalization-pytest",
     [sys.executable, "-B", "-m", "pytest", "schema v0.1/Paper Agent/tests",
      "schema v0.1/Autoformalization Agent/tests", "-q", "-p", "no:cacheprovider"], 0),
    ("reader-pytest",
     [sys.executable, "-B", "-m", "pytest", "schema v0.1/Reader Agent/tests",
      "-q", "-p", "no:cacheprovider"], 0),
    ("planner-conformance-positive",
     [sys.executable, "-B", f"{PLANNER}/check_interfaces.py", "--kind", "propose",
      "--input", f"{PLANNER}/conformance/propose-draft.json"], 0),
    ("planner-conformance-rejected",
     [sys.executable, "-B", f"{PLANNER}/check_interfaces.py", "--kind", "propose",
      "--input", f"{PLANNER}/conformance/propose-draft-rejected.json"], 1),
    ("planner-conformance-blocked-follow-up",
     [sys.executable, "-B", f"{PLANNER}/check_interfaces.py", "--kind", "propose",
      "--input", f"{PLANNER}/conformance/propose-draft-blocked-follow-up.json"], 1),
    ("delta-conformance-positive",
     [sys.executable, "-B", f"{DELTA}/check_interfaces.py", "--kind", "delta",
      "--input", f"{DELTA}/conformance/delta-draft.json"], 0),
    ("delta-conformance-invalid",
     [sys.executable, "-B", f"{DELTA}/check_interfaces.py", "--kind", "delta",
      "--input", f"{DELTA}/conformance/delta-draft-invalid.json"], 1),
    ("delta-conformance-multi-target-uncovered",
     [sys.executable, "-B", f"{DELTA}/check_interfaces.py", "--kind", "delta",
      "--input", f"{DELTA}/conformance/delta-draft.json",
      "--task", f"{DELTA}/conformance/task-multi-target.json"], 1),
    ("delta-conformance-multi-target-covered",
     [sys.executable, "-B", f"{DELTA}/check_interfaces.py", "--kind", "delta",
      "--input", f"{DELTA}/conformance/delta-draft-multi-target-covered.json",
      "--task", f"{DELTA}/conformance/task-multi-target.json"], 0),
    ("dependency-conformance-positive",
     [sys.executable, "-B", f"{DEPENDENCY}/check_interfaces.py", "--kind", "search",
      "--input", f"{DEPENDENCY}/conformance/search-draft.json"], 0),
    ("dependency-conformance-duplicate-search",
     [sys.executable, "-B", f"{DEPENDENCY}/check_interfaces.py", "--kind", "search",
      "--input", f"{DEPENDENCY}/conformance/search-draft-duplicate.json"], 1),
    ("dependency-conformance-self-binding",
     [sys.executable, "-B", f"{DEPENDENCY}/check_interfaces.py", "--kind", "search",
      "--input", f"{DEPENDENCY}/conformance/search-draft-self-binding.json"], 1),
    ("review-conformance-backtranslate",
     [sys.executable, "-B", f"{REVIEW}/check_interfaces.py", "--kind", "backtranslate",
      "--input", f"{REVIEW}/conformance/backtranslate-draft.json",
      "--task", f"{REVIEW}/conformance/task-backtranslate.json"], 0),
    ("review-conformance-backtranslate-leak",
     [sys.executable, "-B", f"{REVIEW}/check_interfaces.py", "--kind", "backtranslate",
      "--input", f"{REVIEW}/conformance/backtranslate-draft.json",
      "--task", f"{REVIEW}/conformance/task-backtranslate-leak.json"], 1),
    ("utility-conformance-request-positive",
     [sys.executable, "-B", f"{UTILITY}/check_interfaces.py", "--kind", "request",
      "--input", f"{UTILITY}/conformance/request-capture.json"], 0),
    ("utility-conformance-request-rejected",
     [sys.executable, "-B", f"{UTILITY}/check_interfaces.py", "--kind", "request",
      "--input", f"{UTILITY}/conformance/request-capture-rejected.json"], 1),
    ("utility-conformance-receipt-diagnostic",
     [sys.executable, "-B", f"{UTILITY}/check_interfaces.py", "--kind", "capture",
      "--input", f"{UTILITY}/conformance/capture-receipt-diagnostic.json"], 0),
    ("utility-conformance-receipt-diagnostic-output",
     [sys.executable, "-B", f"{UTILITY}/check_interfaces.py", "--kind", "project",
      "--input", f"{UTILITY}/conformance/project-receipt-diagnostic-output.json"], 1),
)

environment = os.environ.copy()
environment["PYTHONDONTWRITEBYTECODE"] = "1"

failures = []
for name, command, expected in STEPS:
    started = time.monotonic()
    completed = subprocess.run(command, cwd=ROOT, env=environment,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, check=False)
    elapsed = time.monotonic() - started
    status = "PASS" if completed.returncode == expected else "FAIL"
    print(f"[{status}] {name} (exit={completed.returncode}, expected={expected}, {elapsed:.1f}s)")
    if status == "FAIL":
        failures.append(name)
        tail = "\n".join(completed.stdout.strip().splitlines()[-40:])
        print(f"---- {name} output ----\n{tail}\n---- end {name} ----")

if failures:
    print(f"FAILED steps: {', '.join(failures)}")
    raise SystemExit(1)
print(f"All {len(STEPS)} schema v0.1 checks passed.")
