"""A separately counted concrete case/PhyslibAlpha integration experiment."""
from __future__ import annotations

import json
from pathlib import Path

from epoch_migration import _artifact_inventory
from lean import ALLOWED_AXIOMS, _execute, _sha, _write, composition_witness
from physlib_branch import _paper_span


NEW_DECLARATIONS = [
    "densityToMState", "mStateToDensity", "densityToMState_mat", "mStateToDensity_val",
    "density_roundtrip", "mState_roundtrip", "trace_preserved", "observable", "observable_mat",
    "observable_sq", "frustrationGraph", "matrix_anticomm_of_adj", "expectation_preserved",
    "pauli_ne_neg", "adj_iff_matrix_anticomm",
    "window_clique_l2_bound", "window_clique_l1_bound", "window_cliqueNumber_bound",
    "singleZWindow", "concrete_window_nonvacuity",
]
DEPENDENCY_DECLARATIONS = [
    "AgtXIv.Stabilizer.DensityMatrix", "AgtXIv.Stabilizer.DensityMatrix.toTraceOneHermitian",
    "AgtXIv.Stabilizer.pauli_toCMatrix_isHermitian_of_sq_eq_one",
    "AgtXIv.Stabilizer.pauli_toCMatrix_injective",
    "AgtXIv.Varela.MeasurementWindow", "AgtXIv.Varela.MeasurementWindow.expectationCoordinate",
    "Pauli.mul_anticomm_of_not_commutesWith", "Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix",
    "Pauli.toCMatrix_neg", "MState", "MState.exp_val",
    "MState.sum_sq_exp_val_finset_le_one_of_pairwise_anticommute",
    "MState.sum_abs_exp_val_finset_le_sqrt_card_of_pairwise_anticommute",
    "AgtXIv.PhyslibCandidate.expectation_eq_real_trace",
]


def run_concrete_bridge(repo: Path, output_dir: Path, *, migration_dir: Path | None = None,
                        frozen_branch_dir: Path | None = None,
                        physlib_root: Path | None = None) -> dict:
    """Keep each changed source attempt and reuse only hash-verified objects."""
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    library = Path(physlib_root or repo.parent / "physlib").resolve()
    migration_dir = Path(migration_dir or repo / "schema v0.3/epoch-migration/runs/20260919-full-case").resolve()
    frozen_branch_dir = Path(frozen_branch_dir or repo / "schema v0.3/runs/physlib-anticommuting-20260919").resolve()
    if (output_dir / "bridge-evidence.json").exists():
        raise ValueError("Preserve the completed extension; use a distinct scope for later work")
    migration = json.loads((migration_dir / "migration-completed.json").read_text())
    baseline = json.loads((migration_dir / "full-case-audit.json").read_text())
    branch = json.loads((frozen_branch_dir / "branch-evidence.json").read_text())
    manifest = json.loads((library / "lake-manifest.json").read_text())
    toolchain = (library / "lean-toolchain").read_text().strip()
    if (baseline["status"] != "FULL_COMMON_EPOCH_AUDITED" or
            branch["execution_status"] != "AUDIT_COMPLETE"):
        raise ValueError("Required predecessor audits are incomplete")
    if (manifest != migration["resolved_manifest"] or
            manifest != branch["environment"]["resolved_manifest"] or
            toolchain != migration["toolchain"] or toolchain != branch["environment"]["toolchain"]):
        raise ValueError("Predecessor epochs do not match the active Physlib epoch")
    baseline_objects = _artifact_inventory(migration_dir / "lib", migration["compiled_modules"])
    if baseline_objects != baseline["local_artifact_inventory"]:
        raise ValueError("Migrated case objects changed since their audit")
    frozen = repo / "schema v0.3/lean/frozen/AnticommutingWitness.lean"
    frozen_object = frozen_branch_dir / "AnticommutingWitness.olean"
    if (_sha(frozen.read_bytes()) != branch["source_provenance"]["source_sha256"] or
            _sha(frozen_object.read_bytes()) != branch["environment"]["frozen_olean_sha256"]):
        raise ValueError("Frozen local PhyslibAlpha predecessor changed")
    for relative, expected in branch["environment"]["imported_module_sha256"].items():
        root = library / ".lake/packages/mathlib" if relative.startswith("Mathlib/") else library
        if _sha((root / (".lake/build/lib/lean/" + relative + ".olean")).read_bytes()) != expected:
            raise ValueError("Imported library object changed: " + relative)
    output_dir.mkdir(parents=True, exist_ok=True)
    objects = output_dir / "lib"
    objects.mkdir(exist_ok=True)
    lean_path = ":".join(map(str, [objects, migration_dir / "lib", frozen_branch_dir]))
    dependency = repo / "schema v0.3/lean/AnticommutingNonvacuity.lean"
    dependency_copy = output_dir / "sources/AnticommutingNonvacuity.lean"
    dependency_record = output_dir / "dependency-compile.json"
    if dependency_record.exists():
        dep = json.loads(dependency_record.read_text())
        if (dep["receipt"]["status"] != "SUCCEEDED" or
                dep["source_sha256"] != _sha(dependency.read_bytes()) or
                dep["source_sha256"] != _sha(dependency_copy.read_bytes()) or
                dep["olean_sha256"] != _sha((objects / "AnticommutingNonvacuity.olean").read_bytes())):
            raise ValueError("Extension's compiled dependency is not reusable")
    else:
        dependency_copy.parent.mkdir(exist_ok=True)
        dependency_copy.write_bytes(dependency.read_bytes())
        receipt = _execute(["env", "LEAN_PATH=" + lean_path, "lake", "env", "lean", "-R",
                            str(dependency_copy.parent), "-DautoImplicit=false", "-o",
                            str(objects / "AnticommutingNonvacuity.olean"), str(dependency_copy)],
                           library, output_dir / "dependency-compile.log",
                           "lean.concrete_bridge_frozen_dependency_compile", _sha(dependency_copy.read_bytes()))
        dep = {"receipt": receipt, "source_sha256": _sha(dependency_copy.read_bytes()),
               "olean_sha256": _sha((objects / "AnticommutingNonvacuity.olean").read_bytes())
               if receipt["status"] == "SUCCEEDED" else None}
        _write(dependency_record, dep)
        if receipt["status"] != "SUCCEEDED":
            return {"status": "DEPENDENCY_COMPILE_FAILED", "receipt": receipt}
    attempt = 1
    while (output_dir / "attempts" / str(attempt)).exists():
        attempt += 1
    attempt_dir = output_dir / "attempts" / str(attempt)
    attempt_dir.mkdir(parents=True)
    source = attempt_dir / "ConcretePhyslibBridge.lean"
    source.write_bytes((repo / "schema v0.3/lean/ConcretePhyslibBridge.lean").read_bytes())
    receipt = _execute(["env", "LEAN_PATH=" + lean_path, "lake", "env", "lean", "-R", str(attempt_dir),
                        "-DautoImplicit=false", "-o", str(objects / "ConcretePhyslibBridge.olean"), str(source)],
                       library, attempt_dir / "compile.log", "lean.concrete_physlib_bridge_compile", _sha(source.read_bytes()))
    _write(attempt_dir / "compile-receipt.json", receipt)
    result = {"scope": "NEW_CONCRETE_CASE_TO_PHYSLIBALPHA_EXTENSION", "status": "COMPILE_FAILED",
              "original_migrated_module_count": 82, "additional_compiled_module_count": 1,
              "attempt_directory": str(attempt_dir), "compile_receipt": receipt,
              "query_chain_complete": False, "source_alignment": "AGENT_NORMALIZED_UNREVIEWED",
              "accepted": False, "records": [], "composition_witnesses": []}
    if receipt["status"] != "SUCCEEDED":
        _write(attempt_dir / "bridge-evidence.json", result)
        return result
    result["additional_compiled_module_count"] = 2
    new_targets = ["AgtXIv.ConcretePhyslib." + name for name in NEW_DECLARATIONS]
    targets = sorted(set(new_targets + DEPENDENCY_DECLARATIONS))
    audit_source = ("import ConcretePhyslibBridge\n" +
                    (repo / "schema v0.3/lean/EnvironmentAudit.lean").read_text() + "\n" +
                    "\n".join("#agtxiv_audit " + name for name in targets) + "\n")
    audit_script = attempt_dir / "ConcreteBridgeAudit.lean"
    audit_script.write_text(audit_source)
    extension_rows = [
        {"module": "AnticommutingNonvacuity", "olean_sha256": dep["olean_sha256"]},
        {"module": "ConcretePhyslibBridge", "olean_sha256": _sha((objects / "ConcretePhyslibBridge.olean").read_bytes())},
    ]
    extension_objects = _artifact_inventory(objects, extension_rows)
    audit_receipt = _execute(["env", "LEAN_PATH=" + lean_path, "lake", "env", "lean", str(audit_script)],
                             library, attempt_dir / "audit.log", "lean.concrete_physlib_bridge_audit", _sha(audit_source.encode()))
    _write(attempt_dir / "audit-receipt.json", audit_receipt)
    environment = {"toolchain": toolchain, "manifest": manifest, "baseline_objects": baseline_objects,
                   "frozen_local_alpha_olean_sha256": _sha(frozen_object.read_bytes()),
                   "extension_objects": extension_objects, "audit_source_sha256": _sha(audit_source.encode())}
    environment_sha = _sha(json.dumps(environment, sort_keys=True).encode())
    result.update(status="AUDIT_FAILED", audit_receipt=audit_receipt, environment=environment,
                  environment_sha256=environment_sha, requested_targets=targets, new_declarations=new_targets,
                  source_sha256=_sha(source.read_bytes()), dependency_source_sha256=dep["source_sha256"],
                  frozen_local_alpha_provenance=branch["source_provenance"],
                  source_spans=[_paper_span(repo, 134, 135), _paper_span(repo, 725, 763)],
                  baseline_audit={"path": str(migration_dir / "full-case-audit.json"),
                                  "sha256": _sha((migration_dir / "full-case-audit.json").read_bytes())},
                  remaining_gaps=["REDUCED_ROM_TO_CLIQUE_MAXIMUM", "PAPER_SPECIFIC_SIGN_CONSTRAINTS",
                                  "PERFECT_GRAPH_DUALITY", "REVIEWED_PAPER_STATEMENT_ALIGNMENT"])
    if (_artifact_inventory(migration_dir / "lib", migration["compiled_modules"]) != baseline_objects or
            _artifact_inventory(objects, extension_rows) != extension_objects):
        result["status"] = "BASELINE_ARTIFACTS_CHANGED"
    elif audit_receipt["status"] == "SUCCEEDED":
        for line in Path(audit_receipt["log"]).read_text().splitlines():
            if line.startswith("AGTXIV_AUDIT_JSON "):
                row = json.loads(line[len("AGTXIV_AUDIT_JSON "):])
                forbidden = sorted(set(row["axioms"]) - ALLOWED_AXIOMS)
                row.update(forbidden_axioms=forbidden, kernel_checked=not forbidden,
                           environment_sha256=environment_sha, receipt=audit_receipt["log"],
                           statement_alignment="AGENT_NORMALIZED_UNREVIEWED", accepted=False)
                result["records"].append(row)
        records = {row["declaration"]: row for row in result["records"]}
        result["status"] = ("AUDIT_TARGET_MISMATCH" if set(records) != set(targets) else
                            "AUDIT_AXIOMS_REJECTED" if any(not row["kernel_checked"] for row in records.values()) else
                            "CONCRETE_PHYSLIB_BRIDGE_AUDITED")
        for row in result["records"]:
            for dependency_name in row["term_constants"]:
                if dependency_name in records and dependency_name != row["declaration"]:
                    witness = composition_witness(result["records"], dependency_name, row["declaration"])
                    if witness["status"] == "COMPOSED":
                        result["composition_witnesses"].append(witness)
        nonvacuity = records.get("AgtXIv.ConcretePhyslib.concrete_window_nonvacuity", {})
        result["nonvacuity"] = {"declaration": "AgtXIv.ConcretePhyslib.concrete_window_nonvacuity",
                                "status": "EXPLICIT_DENSITY_AND_NONIDENTITY_PAULI_WINDOW_CONSTRUCTED"
                                if nonvacuity.get("kernel_checked") and
                                   not nonvacuity.get("non_instance_prop_hypotheses") else "UNVERIFIED"}
    result["declaration_kind_counts"] = {
        kind: sum(row["kind"] == kind for row in result["records"])
        for kind in sorted({row["kind"] for row in result["records"]})}
    _write(attempt_dir / "bridge-evidence.json", result)
    if result["status"] == "CONCRETE_PHYSLIB_BRIDGE_AUDITED":
        _write(output_dir / "bridge-evidence.json", result)
    return result
