#!/usr/bin/env python3
"""Rebuild and audit the first pinned AgtXIv Lean 4 formalization slice."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PROJECT = REPO / "formal" / "AgtXIvRootMath"
RESULT = PROJECT / "verification-result.json"
ELAN_HOME = REPO / ".tools" / "elan"
LAKE = ELAN_HOME / "bin" / "lake"
QUANTUMLIB = REPO / "Reference" / "LeanQuantum"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
ROOT_MATH_REQUIRED = {
    "AgtXIv.Stabilizer.IndependentSignedPauliFrame.finrank_commonFixed_eq_two_pow_sub",
    "AgtXIv.Stabilizer.IndependentSignedPauliGenerators.generatorsFix_iff_mem_generalRankCommonFixed",
    "AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_posSemidef",
    "AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_trace",
    "AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_range_finrank",
    "AgtXIv.Stabilizer.IndependentSignedPauliGenerators.pureStabilizerDensity",
    "AgtXIv.Stabilizer.IndependentSignedPauliFrame.exists_semanticClifford_map_standardIndependentZFrame",
    "AgtXIv.Stabilizer.pureStabilizerByFrame_iff_byCliffordOrbit",
    "AgtXIv.Stabilizer.stabilizerPolytopeByFrames_eq_byCliffordOrbit",
    "AgtXIv.Stabilizer.traceOneHermitianAffine_le_completeFrame_affineSpan",
    "AgtXIv.Stabilizer.traceOne_canonicalStabilizer_feasible",
    "AgtXIv.Stabilizer.densityFullStabilizerRoM_eq_one_iff_mem_cliffordOrbitPolytope",
    "AgtXIv.Stabilizer.DensityStabilizerAtomMap.densityFullStabilizerRoM_mono",
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

    if not LAKE.is_file():
        errors.append(f"repository-local lake missing: {LAKE}")

    expected_quantumlib = evidence.get("environment", {}).get("quantumlib_commit")
    if expected_quantumlib:
        if not (QUANTUMLIB / ".git").exists():
            errors.append(f"pinned LeanQuantum checkout missing: {QUANTUMLIB}")
        else:
            head = subprocess.run(
                ["git", "-C", str(QUANTUMLIB), "rev-parse", "HEAD"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if head.returncode != 0 or head.stdout.strip() != expected_quantumlib:
                errors.append("LeanQuantum dependency commit mismatch")
            dirty = subprocess.run(
                ["git", "-C", str(QUANTUMLIB), "status", "--porcelain"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if dirty.returncode != 0 or dirty.stdout.strip():
                errors.append("LeanQuantum dependency checkout is not clean")

    for relative, tagged_expected in evidence["artifact_hashes"].items():
        path = REPO / relative
        if not path.is_file():
            errors.append(f"hashed formal artifact missing: {relative}")
            continue
        expected = tagged_expected.removeprefix("sha256:")
        actual = sha256(path)
        if actual != expected:
            errors.append(f"formal artifact hash mismatch: {relative}")

    placeholder_pattern = re.compile(
        r"(?m)^\s*(?:sorry|admit|axiom)\b|:=\s*(?:sorry|by\s+sorry)\b"
    )
    for path in sorted(PROJECT.rglob("*.lean")):
        if path.name == "Audit.lean" or ".lake" in path.parts:
            continue
        if placeholder_pattern.search(path.read_text(encoding="utf-8")):
            errors.append(f"placeholder or project axiom found: {path.relative_to(REPO)}")
        if "Quantumlib.Data.Error.Operator" in path.read_text(encoding="utf-8"):
            errors.append(f"forbidden LeanQuantum import found: {path.relative_to(REPO)}")

    build = run([str(LAKE), "build"]) if LAKE.is_file() else None
    if build is None or build.returncode != 0:
        errors.append("lake build failed")

    audit = run([str(LAKE), "env", "lean", "Audit.lean"]) if LAKE.is_file() else None
    audit_output = audit.stdout if audit is not None else ""
    if audit is None or audit.returncode != 0:
        errors.append("Lean axiom audit failed to run")
    if "sorryAx" in audit_output:
        errors.append("Lean axiom audit found sorryAx")

    found_declarations = set(re.findall(r"^'([^']+)' depends on axioms:", audit_output, re.MULTILINE))
    expected_declarations = set(evidence["declarations"])
    missing_declarations = expected_declarations - found_declarations
    if missing_declarations:
        errors.append(f"axiom report missing declarations: {sorted(missing_declarations)}")
    if evidence.get("root_math_status") == "ROOT_MATH_KERNEL_COMPLETE":
        missing_root_surface = ROOT_MATH_REQUIRED - expected_declarations
        if missing_root_surface:
            errors.append(
                "ROOT_MATH_KERNEL_COMPLETE lacks required declarations: "
                f"{sorted(missing_root_surface)}"
            )
    else:
        errors.append("root_math_status is not ROOT_MATH_KERNEL_COMPLETE")

    found_axioms: set[str] = set()
    for payload in re.findall(r"depends on axioms: \[([^]]*)\]", audit_output):
        found_axioms.update(item.strip() for item in payload.split(",") if item.strip())
    unexpected_axioms = found_axioms - ALLOWED_AXIOMS
    if unexpected_axioms:
        errors.append(f"unexpected axioms: {sorted(unexpected_axioms)}")

    report = {
        "schema_version": "0.1.0-prototype",
        "project": str(PROJECT.relative_to(REPO)),
        "kernel_build": "PASSED" if build is not None and build.returncode == 0 else "FAILED",
        "declarations_audited": len(found_declarations),
        "reported_axioms": sorted(found_axioms),
        "artifact_hashes": "PASSED" if not any("hash" in error for error in errors) else "FAILED",
        "placeholder_scan": "PASSED" if not any("placeholder" in error for error in errors) else "FAILED",
        "errors": errors,
        "formalization_validation": "PASSED" if not errors else "FAILED",
        "scientific_acceptance_effect": "NONE; parent Root PaperAgents remain accepted=false",
        "root_math_status": evidence.get("root_math_status", "UNDECLARED"),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors and build is not None and build.stdout:
        print(build.stdout)
    if errors and audit_output:
        print(audit_output)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
