"""Current Lean-environment evidence, separately from source-alignment judgements.

Historical verification-result.json files are never read as successful builds and
never rewritten. A build exit code is necessary, but cannot discharge premises,
establish source faithfulness, or turn imported modules into composition edges.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any


PROJECTS = ("AgtXIvRootMath", "AgtXIvVarela", "AgtXIvStabilizerness")
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})
EXTRA_DECLARATIONS = {
    "AgtXIvVarela": [
        "AgtXIv.GraphFoundation.IsPerfect",
        "AgtXIv.GraphFoundation.maxWeightIndependent",
        "AgtXIv.GraphFoundation.independentFinsets",
        "AgtXIv.GraphFoundation.fractionalCliqueCoverValue",
        "AgtXIv.GraphFoundation.WeightedPerfectGraphFoundation",
        "AgtXIv.GraphFoundation.WeightedPerfectDualityCertificate",
        "AgtXIv.Varela.VRepRepairObligations",
    ],
    "AgtXIvStabilizerness": [
        "AgtXIv.Stabilizerness.admissibleSignedValues",
        "AgtXIv.Stabilizerness.admissible_signed_sum_le",
        "AgtXIv.Stabilizerness.max_abs_admissible_signed_sum_of_sign_set_eq",
        "AgtXIv.Stabilizerness.full_sign_cube_collapse_instance",
    ],
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _snapshot(repo: Path) -> dict:
    paths: list[Path] = []
    for project in PROJECTS:
        root = repo / "formal" / project
        paths.extend(root.glob("*.lean"))
        paths.extend((root / project).glob("*.lean"))
        paths.extend(root / name for name in ("lean-toolchain", "lakefile.toml", "lake-manifest.json"))
    files = {str(path.relative_to(repo)): _sha(path.read_bytes()) for path in sorted(set(paths))}
    return {
        "sha256": _sha(json.dumps(files, sort_keys=True).encode()),
        "files": files,
        "toolchains": {
            project: (repo / "formal" / project / "lean-toolchain").read_text().strip()
            for project in PROJECTS
        },
        "resolved_manifests": {
            project: json.loads((repo / "formal" / project / "lake-manifest.json").read_text())
            for project in PROJECTS
        },
    }


def _execute(command: list[str], cwd: Path, output: Path, operation: str,
             input_sha256: str, timeout: int = 1800) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    tick = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                              timeout=timeout, check=False)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        status = "SUCCEEDED" if code == 0 else "FAILED"
    except subprocess.TimeoutExpired as exc:
        code, status = None, "TIMEOUT"
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
    except OSError as exc:
        code, status, stdout, stderr = None, "UNAVAILABLE", "", str(exc)
    log = stdout + ("\nSTDERR:\n" + stderr if stderr else "")
    output.write_text(log)
    return {
        "kind": "ProgramReceipt", "contract_version": "0.3.0",
        "program": "agtxiv.lean-audit/0.3.0", "engine_class": "HOST", "call": None,
        "operation": operation,
        "command": command, "cwd": str(cwd), "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.monotonic() - tick, 3),
        "elapsed_seconds": round(time.monotonic() - tick, 3),
        "outcome": "RECORDED" if status == "SUCCEEDED" else "FAILED",
        "exit_code": code, "status": status, "input_sha256": input_sha256,
        "output_sha256": _sha(log.encode()), "log": str(output),
    }


def _targets(repo: Path, project: str) -> list[str]:
    audit = (repo / "formal" / project / "Audit.lean").read_text()
    return sorted(set(re.findall(r"^#print axioms\s+(\S+)", audit, re.M)) |
                  set(EXTRA_DECLARATIONS.get(project, [])))


def composition_witness(records: list[dict], upstream: str, downstream: str) -> dict:
    """Direct elaborated value dependency, never inferred from an import line.

    A negative result only says this direct witness is absent; the caller may
    obtain a transitive witness by auditing intermediate declarations.
    """
    indexed = {item["declaration"]: item for item in records}
    source, target = indexed.get(upstream), indexed.get(downstream)
    source_epoch = source.get("environment_sha256", source.get("environment")) if source else None
    target_epoch = target.get("environment_sha256", target.get("environment")) if target else None
    same_epoch = source_epoch is not None and source_epoch == target_epoch
    present = bool(source and target and source.get("kernel_checked") and
                   target.get("kernel_checked") and same_epoch and upstream in target["term_constants"])
    return {
        "upstream_declaration": upstream, "downstream_declaration": downstream,
        "status": "COMPOSED" if present else "NOT_COMPOSED",
        "basis": "LEAN_ELABORATED_TERM_CONSTANT" if present else "NO_DIRECT_TERM_WITNESS",
        "receipt": target.get("receipt") if target else None,
        "same_environment": same_epoch,
        "mathematical_necessity_established": False,
    }


def audit_physlib(repo: Path, output_dir: Path, physlib_root: Path | None = None) -> dict:
    """Audit a local Physlib cache in its own epoch; do not alter that checkout.

    This does not add Physlib to the incompatible 4.30 package. Only tracked
    Physlib core is imported, never local or upstream PhyslibAlpha. The cache
    freshness limitation is explicit; actual imported types/proofs are audited.
    """
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    root = Path(physlib_root or repo.parent / "physlib").resolve()
    result: dict = {
        "library": "physlib", "requested": True, "root": str(root),
        "status": "LOCAL_CHECKOUT_UNAVAILABLE", "records": [], "receipts": [],
        "same_epoch_as_query": False, "cross_epoch_composition": "NOT_COMPOSED",
        "import_policy": "PHYSLIB_CORE_ONLY",
        "upstream_source_url": "https://github.com/leanprover-community/physlib",
    }
    if not (root / "lean-toolchain").is_file():
        _write(output_dir / "physlib-audit.json", result)
        return result
    toolchain = (root / "lean-toolchain").read_text().strip()
    manifest = json.loads((root / "lake-manifest.json").read_text())
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              text=True, capture_output=True, check=False).stdout.strip()
    core_path = root / "Physlib/Relativity/PauliMatrices/Basic.lean"
    olean = root / ".lake/build/lib/lean/Physlib/Relativity/PauliMatrices/Basic.olean"
    environment = {
        "revision": revision, "toolchain": toolchain, "resolved_manifest": manifest,
        "source_sha256": _sha(core_path.read_bytes()),
        "imported_olean_sha256": _sha(olean.read_bytes()) if olean.is_file() else None,
        "cache_source_freshness": "NOT_REBUILT_IN_THIS_RUN",
        "module": "Physlib.Relativity.PauliMatrices.Basic",
    }
    query_manifest = json.loads((repo / "formal/AgtXIvRootMath/lake-manifest.json").read_text())
    mathlib_rev = lambda data: next((p["rev"] for p in data["packages"] if p["name"] == "mathlib"), None)
    result.update(environment=environment,
                  same_epoch_as_query=(toolchain == (repo / "formal/AgtXIvRootMath/lean-toolchain").read_text().strip()
                                       and mathlib_rev(manifest) == mathlib_rev(query_manifest)),
                  status="AUDIT_NOT_RUN")
    if not olean.is_file():
        result["status"] = "COMPILED_LIBRARY_UNAVAILABLE"
        _write(output_dir / "physlib-audit.json", result)
        return result
    declarations = [
        "PauliMatrix.pauliMatrix", "PauliMatrix.pauliMatrix_selfAdjoint",
        "PauliMatrix.pauliMatrix_mul_self", "PauliMatrix.pauliMatrix_anticommutator",
        "PauliMatrix.vectorMatrix", "PauliMatrix.vectorMatrix_sq",
        "AgtXIv.PhyslibFoundation.normalized_pauli_combination_square",
    ]
    template = (repo / "schema v0.3/lean/EnvironmentAudit.lean").read_text()
    foundation = (repo / "schema v0.3/lean/PhyslibPauliFoundation.lean").read_text()
    foundation = "\n".join(line for line in foundation.splitlines() if not line.startswith("import "))
    source = "import Physlib.Relativity.PauliMatrices.Basic\n" + template + "\n" + foundation
    source += "\n" + "\n".join("#agtxiv_audit " + name for name in declarations) + "\n"
    script = output_dir / "Physlib-EnvironmentAudit.lean"
    script.write_text(source)
    receipt = _execute(["lake", "env", "lean", str(script)], root,
                       output_dir / "physlib-audit.log", "lean.physlib_environment_audit",
                       _sha(source.encode()))
    result["receipts"].append(receipt)
    if receipt["status"] == "SUCCEEDED":
        for line in Path(receipt["log"]).read_text().splitlines():
            if line.startswith("AGTXIV_AUDIT_JSON "):
                record = json.loads(line[len("AGTXIV_AUDIT_JSON "):])
                record.update(receipt=receipt["log"], environment=environment,
                              forbidden_axioms=sorted(set(record["axioms"]) - ALLOWED_AXIOMS),
                              statement_alignment="AGENT_NORMALIZED_UNREVIEWED")
                record["kernel_checked"] = not record["forbidden_axioms"]
                result["records"].append(record)
        complete = {r["declaration"] for r in result["records"]} == set(declarations)
        result["status"] = "ENVIRONMENT_AUDITED" if complete else "AUDIT_TARGET_MISMATCH"
        result["composition_witness"] = composition_witness(result["records"],
            "PauliMatrix.vectorMatrix_sq", "AgtXIv.PhyslibFoundation.normalized_pauli_combination_square")
    else:
        result["status"] = "AUDIT_FAILED"
    _write(output_dir / "physlib-audit.json", result)
    return result


def audit_projects(repo: Path, output_dir: Path, run_builds: bool = True) -> dict:
    """Build and audit only the three packages used for arXiv:2607.26154.

    The final package depends on the first two, so one `lake build` refreshes
    the complete chain without simultaneous writes to the shared cache. When
    run_builds=False, nothing is executed and no cached result is promoted.
    """
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    if (output_dir / "lean-audit.json").exists():
        raise ValueError("Use a fresh audit directory; preserve earlier run evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    environment = _snapshot(repo)
    targets = {project: _targets(repo, project) for project in PROJECTS}
    summary: dict = {
        "scope": "CURRENT_SELECTED_LEAN_DECLARATIONS",
        "environment": environment, "requested_targets": targets,
        "records": [], "receipts": [], "composition_witnesses": [],
        "execution_status": "NOT_RUN", "query_declaration": None,
        "query_chain_status": "CHAIN_INCOMPLETE",
        "limitations": [
            "Bindings are candidates; Lean does not judge faithfulness to paper text.",
            "Non-instance Prop hypotheses are read from the environment; no inhabitation is inferred.",
            "Term dependencies establish syntactic composition, not logical necessity.",
            "The graph/RoM query has no composed Lean declaration in these projects.",
        ],
    }
    if not run_builds:
        _write(output_dir / "lean-audit.json", summary)
        return summary

    build = _execute(["lake", "build"], repo / "formal" / PROJECTS[-1],
                     output_dir / "chain-build.log", "lean.build_dependency_chain",
                     environment["sha256"])
    summary["receipts"].append(build)
    if build["status"] != "SUCCEEDED":
        summary["execution_status"] = "BUILD_FAILED"
        _write(output_dir / "lean-audit.json", summary)
        return summary

    template = (repo / "schema v0.3" / "lean" / "EnvironmentAudit.lean").read_text()
    audit_failed = False
    for project in PROJECTS:
        source = "import " + project + "\n" + template + "\n"
        source += "\n".join("#agtxiv_audit " + name for name in targets[project]) + "\n"
        script = output_dir / (project + "-EnvironmentAudit.lean")
        script.write_text(source)
        receipt = _execute(["lake", "env", "lean", str(script)],
                           repo / "formal" / project, output_dir / (project + "-audit.log"),
                           "lean.environment_audit", _sha(source.encode()))
        summary["receipts"].append(receipt)
        # A partial stdout from a failed auditor is retained as a log only.
        if receipt["status"] != "SUCCEEDED":
            audit_failed = True
            continue
        project_records = []
        for line in Path(receipt["log"]).read_text().splitlines():
            if not line.startswith("AGTXIV_AUDIT_JSON "):
                continue
            item = json.loads(line[len("AGTXIV_AUDIT_JSON "):])
            forbidden = sorted(set(item["axioms"]) - ALLOWED_AXIOMS)
            item.update({
                "project": project, "receipt": receipt["log"],
                "environment_sha256": environment["sha256"],
                "kernel_checked": not forbidden, "forbidden_axioms": forbidden,
                "statement_discharged": item["kind"] == "DEFINITION" and not forbidden,
                "proof_discharged": item["kind"] == "THEOREM" and not forbidden,
                "nonvacuity_witness": "NONE",
                "statement_alignment": "AGENT_NORMALIZED_UNREVIEWED",
                "accepted": False,
                "definition_promotion": "NOT_PROMOTED" if item["kind"] == "DEFINITION" else None,
                "total_on": None,
                "nondegeneracy_witness": "NONE",
            })
            if forbidden:
                item["evidence_status"] = "AXIOM_AUDIT_FAILED"
                item["derived_state"] = "AWAITING_REVIEW"
            elif item["kind"] == "DEFINITION":
                item["derived_state"] = "DEFINITION_ELABORATED"
            elif item["kind"] == "THEOREM":
                item["derived_state"] = ("KERNEL_CHECKED_VACUITY_UNKNOWN"
                                         if (item["non_instance_prop_hypotheses"] or
                                             item["structure_prop_hypotheses"])
                                         else "KERNEL_CHECKED_CANDIDATE")
            else:
                item["derived_state"] = "CANDIDATE"
            project_records.append(item)
        if {x["declaration"] for x in project_records} != set(targets[project]):
            audit_failed = True
            summary.setdefault("issues", []).append({
                "kind": "AUDIT_TARGET_MISMATCH", "project": project,
            })
            continue
        summary["records"].extend(project_records)

    current = _snapshot(repo)
    if current["sha256"] != environment["sha256"]:
        summary["execution_status"] = "SOURCE_CHANGED_DURING_AUDIT"
        for record in summary["records"]:
            record.update(kernel_checked=False, statement_discharged=False, proof_discharged=False)
            record.update(derived_state="AWAITING_REVIEW", evidence_status="SOURCE_CHANGED_DURING_AUDIT")
    else:
        summary["execution_status"] = "AUDIT_PARTIAL" if audit_failed else "AUDIT_COMPLETE"
    # Repeated imports do not inflate counts; retain the latest successful view.
    records = {item["declaration"]: item for item in summary["records"]}
    summary["records"] = list(records.values())
    for target in summary["records"]:
        for dependency in target["term_constants"]:
            if dependency in records and dependency != target["declaration"]:
                witness = composition_witness(summary["records"], dependency, target["declaration"])
                if witness["status"] == "COMPOSED":
                    summary["composition_witnesses"].append(witness)
    summary["coverage"] = [
        {"scope": "CURRENT_SELECTED_LEAN_THEOREMS", "metric": "PROOF_TERM_ACCEPTED",
         "count": sum(x["proof_discharged"] for x in records.values()),
         "denominator": sum(x["kind"] == "THEOREM" for x in records.values())},
        {"scope": "CURRENT_SELECTED_LEAN_DEFINITIONS", "metric": "DEFINITION_ELABORATED",
         "count": sum(x["statement_discharged"] for x in records.values()),
         "denominator": sum(x["kind"] == "DEFINITION" for x in records.values())},
        {"scope": "CURRENT_SELECTED_LEAN_THEOREMS", "metric": "PREMISE_NONVACUITY_UNKNOWN",
         "count": sum(x["kind"] == "THEOREM" and bool(x["non_instance_prop_hypotheses"] or
                                                     x["structure_prop_hypotheses"])
                      for x in records.values()),
         "denominator": sum(x["kind"] == "THEOREM" for x in records.values())},
    ]
    summary["requested_library_audits"] = [audit_physlib(repo, output_dir / "physlib")]
    _write(output_dir / "lean-audit.json", summary)
    return summary
