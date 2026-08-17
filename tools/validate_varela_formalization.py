#!/usr/bin/env python3
"""Rebuild and audit the conditional Varela projected-polytope formalization."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PROJECT = REPO / "formal" / "AgtXIvVarela"
RESULT = PROJECT / "verification-result.json"
ELAN_HOME = REPO / ".tools" / "elan"
LAKE = ELAN_HOME / "bin" / "lake"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
REQUIRED = {
    "AgtXIv.Varela.MeasurementWindow.expectationProjection_reconstruct",
    "AgtXIv.Varela.MeasurementWindow.mem_projectedStabilizerPolytope_iff",
    "AgtXIv.Varela.MeasurementWindow.MaximalSignedContext.abs_vector_le_one",
    "AgtXIv.Varela.VRepRepairObligations.projected_eq_contextPolytope",
    "AgtXIv.Varela.reducedStabilizerPolytope_vrep_conditional",
    "AgtXIv.GraphFoundation.weighted_duality_of_foundation",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["ELAN_HOME"] = str(ELAN_HOME)
    return subprocess.run(
        command,
        cwd=PROJECT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def main() -> int:
    errors: list[str] = []
    evidence = json.loads(RESULT.read_text(encoding="utf-8"))

    for relative, tagged_expected in evidence["artifact_hashes"].items():
        path = REPO / relative
        if not path.is_file():
            errors.append(f"hashed formal artifact missing: {relative}")
            continue
        if sha256(path) != tagged_expected.removeprefix("sha256:"):
            errors.append(f"formal artifact hash mismatch: {relative}")

    placeholder_pattern = re.compile(
        r"(?m)^\s*(?:sorry|admit|axiom)\b|:=\s*(?:sorry|by\s+sorry)\b"
    )
    for path in sorted(PROJECT.rglob("*.lean")):
        if path.name == "Audit.lean" or ".lake" in path.parts:
            continue
        if placeholder_pattern.search(path.read_text(encoding="utf-8")):
            errors.append(f"placeholder or project axiom found: {path.relative_to(REPO)}")

    build = run([str(LAKE), "build"])
    if build.returncode != 0:
        errors.append("lake build failed")

    audit = run([str(LAKE), "env", "lean", "Audit.lean"])
    audit_output = audit.stdout
    if audit.returncode != 0:
        errors.append("Lean axiom audit failed to run")
    if "sorryAx" in audit_output:
        errors.append("Lean axiom audit found sorryAx")

    found_declarations = set(
        re.findall(r"^'([^']+)' depends on axioms:", audit_output, re.MULTILINE)
    )
    expected_declarations = set(evidence["declarations"])
    if expected_declarations != REQUIRED:
        errors.append("verification evidence does not list the required conditional surface")
    missing = expected_declarations - found_declarations
    if missing:
        errors.append(f"axiom report missing declarations: {sorted(missing)}")

    found_axioms: set[str] = set()
    for payload in re.findall(r"depends on axioms: \[([^]]*)\]", audit_output):
        found_axioms.update(item.strip() for item in payload.split(",") if item.strip())
    unexpected = found_axioms - ALLOWED_AXIOMS
    if unexpected:
        errors.append(f"unexpected axioms: {sorted(unexpected)}")

    if evidence.get("vrep_status") != "PARTIALLY_FORMALIZED_EXPLICIT_OBLIGATIONS":
        errors.append("aggregate V-representation status is overstated or missing")

    report = {
        "schema_version": "0.1.0-prototype",
        "project": str(PROJECT.relative_to(REPO)),
        "kernel_build": "PASSED" if build.returncode == 0 else "FAILED",
        "declarations_audited": len(found_declarations),
        "reported_axioms": sorted(found_axioms),
        "artifact_hashes": "PASSED" if not any("hash" in e for e in errors) else "FAILED",
        "placeholder_scan": "PASSED" if not any("placeholder" in e for e in errors) else "FAILED",
        "vrep_status": evidence.get("vrep_status"),
        "errors": errors,
        "formalization_validation": "PASSED" if not errors else "FAILED",
        "scientific_acceptance_effect": "NONE; Varela export remains accepted=false",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors and build.stdout:
        print(build.stdout)
    if errors and audit_output:
        print(audit_output)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
