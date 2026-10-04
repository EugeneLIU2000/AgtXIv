"""Isolated, provenance-preserving experiment against Physlib's cached epoch."""
from __future__ import annotations

import json
from pathlib import Path
import re

from lean import ALLOWED_AXIOMS, PROJECTS, _execute, _sha, _targets, _write, composition_witness


SOURCES = [
    ("EpochGraphFoundation", "formal/AgtXIvVarela/AgtXIvVarela/ExternalPerfectGraphFoundation.lean"),
    ("EpochLocalDelta", "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/LocalDelta.lean"),
    ("EpochAdmissibleSigns", "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/AdmissibleSigns.lean"),
]
TARGETS = [
    "AgtXIv.GraphFoundation.IsPerfect", "AgtXIv.GraphFoundation.maxWeightIndependent",
    "AgtXIv.GraphFoundation.fractionalCliqueCoverValue",
    "AgtXIv.GraphFoundation.weighted_duality_of_foundation",
    "AgtXIv.Stabilizerness.abs_signed_sum_add_le",
    "AgtXIv.Stabilizerness.exists_sign_attaining_abs_sum",
    "AgtXIv.Stabilizerness.max_abs_signed_sum",
    "AgtXIv.Stabilizerness.affineSpan_eq_top_of_vectorSpan_eq_top",
    "AgtXIv.Stabilizerness.admissibleSignedValues",
    "AgtXIv.Stabilizerness.max_abs_admissible_signed_sum_of_sign_set_eq",
    "MState.exp_val", "AgtXIv.CommonEpoch.quantum_admissible_sign_maximum",
]


def _artifact_inventory(objects: Path, compiled_modules: list[dict]) -> list[dict]:
    """Capture current Lean module companions, including executable macro IR."""
    inventory = []
    for row in compiled_modules:
        stem = objects / Path(*row["module"].split("."))
        artifacts = {}
        for suffix in (".olean", ".olean.private", ".olean.server", ".ir", ".ir.sig"):
            path = Path(str(stem) + suffix)
            if path.is_file():
                artifacts[suffix] = _sha(path.read_bytes())
        if artifacts.get(".olean") != row["olean_sha256"]:
            raise ValueError("Compiled object changed: " + row["module"])
        inventory.append({"module": row["module"], "artifacts": artifacts})
    return inventory


def source_catalog(repo: Path) -> dict:
    """Static closure size estimate, not a successful migration claim."""
    modules = {}
    for project in ("AgtXIvRootMath", "AgtXIvVarela", "AgtXIvStabilizerness"):
        root = repo / "formal" / project
        for file in [root / (project + ".lean"), *(root / project).glob("*.lean")]:
            name = str(file.relative_to(root).with_suffix("")).replace("/", ".")
            modules[name] = {"path": str(file), "sha256": _sha(file.read_bytes()),
                             "imports": re.findall(r"^(?:public )?import\s+(\S+)", file.read_text(), re.M)}
    quantum = repo / "Reference/LeanQuantum"
    for file in (quantum / "Quantumlib").rglob("*.lean"):
        name = str(file.relative_to(quantum).with_suffix("")).replace("/", ".")
        modules[name] = {"path": str(file), "sha256": _sha(file.read_bytes()),
                         "imports": re.findall(r"^(?:public )?import\s+(\S+)", file.read_text(), re.M)}
    needed = set()
    frontier = ["AgtXIvStabilizerness"]
    while frontier:
        name = frontier.pop()
        if name in needed or name not in modules:
            continue
        needed.add(name)
        frontier.extend(modules[name]["imports"])
    return {"scope": "STATIC_ORIGINAL_CASE_MODULE_CLOSURE", "modules": {n: modules[n] for n in sorted(needed)},
            "count": len(needed), "status": "NOT_MIGRATED_AS_A_WHOLE",
            "quantumlib_count": sum(n.startswith("Quantumlib.") for n in needed)}


def run_migration_probe(repo: Path, output_dir: Path, physlib_root: Path | None = None) -> dict:
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    library = Path(physlib_root or repo.parent / "physlib").resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Migration evidence requires a fresh output directory")
    (output_dir / "originals").mkdir(parents=True)
    (output_dir / "adapted").mkdir()
    manifest = json.loads((library / "lake-manifest.json").read_text())
    result = {"scope": "SELECTED_MODULES_PHYSLIB_COMMON_EPOCH_PROBE",
              "status": "IN_PROGRESS", "full_case_migrated": False, "query_chain_complete": False,
              "toolchain": (library / "lean-toolchain").read_text().strip(),
              "resolved_manifest": manifest, "sources": [], "receipts": [], "records": [],
              "composition_witnesses": [], "full_case_catalog": source_catalog(repo)}
    modules = []
    for name, source_path in SOURCES:
        raw = (repo / source_path).read_bytes()
        (output_dir / "originals" / (name + ".lean")).write_bytes(raw)
        original = raw.decode()
        adapted = original
        adaptations = []
        if name == "EpochLocalDelta":
            adapted = adapted.replace("import AgtXIvVarela\n", "import EpochGraphFoundation\nimport Mathlib.Tactic.Ring\n", 1)
            adaptations.append("Replace unused whole Varela-package import with the graph foundation; import Ring explicitly")
        elif name == "EpochAdmissibleSigns":
            adapted = adapted.replace("import AgtXIvStabilizerness.LocalDelta\n", "import EpochLocalDelta\n", 1)
            adaptations.append("Point at the isolated LocalDelta copy")
        if [x for x in original.splitlines() if not x.startswith("import ")] != [x for x in adapted.splitlines() if not x.startswith("import ")]:
            raise ValueError("Unexpected non-import compatibility edit")
        target = output_dir / "adapted" / (name + ".lean")
        target.write_text(adapted)
        result["sources"].append({"module": name, "original_path": source_path,
                                  "original_sha256": _sha(raw), "adapted_sha256": _sha(adapted.encode()),
                                  "adaptations": adaptations, "mathematical_body_unchanged": True})
        modules.append((name, target))
    bridge = repo / "schema v0.3/epoch-migration/CommonEpochBridge.lean"
    bridge_copy = output_dir / "adapted/CommonEpochBridge.lean"
    bridge_copy.write_bytes(bridge.read_bytes())
    modules.append(("CommonEpochBridge", bridge_copy))
    result["sources"].append({"module": "CommonEpochBridge", "kind": "NEW_PARTIAL_QUANTUM_BRIDGE",
                              "sha256": _sha(bridge.read_bytes()), "source_alignment": "AGENT_NORMALIZED_UNREVIEWED"})
    environment_sha256 = _sha(json.dumps({"sources": result["sources"], "toolchain": result["toolchain"],
                                         "manifest": manifest}, sort_keys=True).encode())
    result["environment_sha256"] = environment_sha256
    for name, source in modules:
        receipt = _execute(["env", "LEAN_PATH=" + str(output_dir), "lake", "env", "lean", "-R",
                            str(source.parent), "-o", str(output_dir / (name + ".olean")), str(source)],
                           library, output_dir / (name + ".log"), "lean.isolated_epoch_module_compile", _sha(source.read_bytes()))
        result["receipts"].append(receipt)
        _write(output_dir / (name + "-receipt.json"), receipt)
        if receipt["status"] != "SUCCEEDED":
            result.update(status="COMPATIBILITY_BLOCKED", failed_module=name)
            _write(output_dir / "migration-evidence.json", result)
            return result
    template = (repo / "schema v0.3/lean/EnvironmentAudit.lean").read_text()
    source = "import CommonEpochBridge\n" + template + "\n"
    source += "\n".join("#agtxiv_audit " + name for name in TARGETS) + "\n"
    audit = output_dir / "CommonEpochAudit.lean"
    audit.write_text(source)
    receipt = _execute(["env", "LEAN_PATH=" + str(output_dir), "lake", "env", "lean", str(audit)],
                       library, output_dir / "common-epoch-audit.log", "lean.common_epoch_environment_audit", _sha(source.encode()))
    result["receipts"].append(receipt)
    if receipt["status"] == "SUCCEEDED":
        for line in Path(receipt["log"]).read_text().splitlines():
            if line.startswith("AGTXIV_AUDIT_JSON "):
                item = json.loads(line[len("AGTXIV_AUDIT_JSON "):])
                forbidden = sorted(set(item["axioms"]) - ALLOWED_AXIOMS)
                item.update(kernel_checked=not forbidden, forbidden_axioms=forbidden,
                            environment_sha256=environment_sha256, receipt=receipt["log"],
                            statement_alignment="AGENT_NORMALIZED_UNREVIEWED", accepted=False)
                result["records"].append(item)
        records = {x["declaration"]: x for x in result["records"]}
        result["status"] = "SELECTED_MODULES_COMMON_EPOCH_AUDITED" if set(records) == set(TARGETS) else "AUDIT_TARGET_MISMATCH"
        for target in result["records"]:
            for dependency in target["term_constants"]:
                if dependency in records and dependency != target["declaration"]:
                    witness = composition_witness(result["records"], dependency, target["declaration"])
                    if witness["status"] == "COMPOSED":
                        result["composition_witnesses"].append(witness)
    else:
        result["status"] = "AUDIT_FAILED"
    result["remaining_migration_blockers"] = [
        "Quantumlib and the complete RootMath/Varela module closure have not been compiled at this epoch.",
        "No entire-package compatibility conclusion follows from the selected source modules.",
        "The paper-specific Pauli sign-collapse and reduced-RoM proof still need mathematical formalization.",
    ]
    _write(output_dir / "migration-evidence.json", result)
    return result


def run_full_case_migration(repo: Path, output_dir: Path, physlib_root: Path | None = None) -> dict:
    """Freshly compile the exact local import closure; stop at first failure.

    No source edits are automated. A compatibility change must be recorded as
    a subsequent explicit adaptation, with failed attempts retained.
    """
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    library = Path(physlib_root or repo.parent / "physlib").resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Full migration evidence requires a fresh output directory")
    originals, adapted, objects = (output_dir / n for n in ("originals", "adapted", "lib"))
    for directory in (originals, adapted, objects, output_dir / "logs", output_dir / "receipts"):
        directory.mkdir(parents=True, exist_ok=True)
    catalog = source_catalog(repo)
    modules = catalog["modules"]
    visited, active, order = set(), set(), []

    def visit(name):
        if name in visited:
            return
        if name in active:
            raise ValueError("Cycle in original local-module imports: " + name)
        active.add(name)
        for dependency in modules[name]["imports"]:
            if dependency in modules:
                visit(dependency)
        active.remove(name)
        visited.add(name)
        order.append(name)

    for name in sorted(modules):
        visit(name)
    for name, metadata in modules.items():
        raw = Path(metadata["path"]).read_bytes()
        if _sha(raw) != metadata["sha256"]:
            raise ValueError("Source changed during freeze: " + name)
        relative = Path(*name.split(".")).with_suffix(".lean")
        for directory in (originals, adapted):
            target = directory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    manifest = json.loads((library / "lake-manifest.json").read_text())
    result = {"scope": "FULL_ORIGINAL_CASE_LOCAL_MODULE_MIGRATION", "status": "IN_PROGRESS",
              "query_chain_complete": False, "full_case_migrated": False,
              "toolchain": (library / "lean-toolchain").read_text().strip(),
              "resolved_manifest": manifest, "catalog": catalog, "compile_order": order,
              "compiled_modules": [], "receipts": [], "compatibility_adaptations": [],
              "mathematical_statements_changed": False}
    _write(output_dir / "frozen-source-catalog.json", catalog)
    _write(output_dir / "frozen-audit-targets.json", {
        "scope": "FROZEN_ORIGINAL_CASE_DECLARATION_TARGETS",
        "targets_by_project": {project: _targets(repo, project) for project in PROJECTS},
        "provenance": "Captured from the project audit declarations when freezing the source closure",
    })
    _write(output_dir / "progress.json", result)
    for index, name in enumerate(order):
        source = adapted / Path(*name.split(".")).with_suffix(".lean")
        olean = objects / Path(*name.split(".")).with_suffix(".olean")
        olean.parent.mkdir(parents=True, exist_ok=True)
        command = ["env", "LEAN_PATH=" + str(objects), "lake", "env", "lean", "-R", str(adapted)]
        if not name.startswith("Quantumlib."):
            command.append("-DautoImplicit=false")
        command += ["-o", str(olean), str(source)]
        receipt = _execute(command, library, output_dir / "logs" / (name + ".log"),
                           "lean.frozen_full_case_module_compile", _sha(source.read_bytes()))
        result["receipts"].append(receipt)
        _write(output_dir / "receipts" / (str(index).zfill(3) + "-" + name + ".json"), receipt)
        if receipt["status"] != "SUCCEEDED":
            result.update(status="COMPATIBILITY_BLOCKED", failed_module=name,
                          failure_log=receipt["log"], remaining_modules=order[index:])
            _write(output_dir / "progress.json", result)
            _write(output_dir / "migration-evidence.json", result)
            return result
        result["compiled_modules"].append({"module": name, "olean_sha256": _sha(olean.read_bytes())})
        _write(output_dir / "progress.json", result)
    result.update(status="FULL_LOCAL_CLOSURE_COMPILED_AUDIT_PENDING", full_case_migrated=True,
                  remaining_modules=[])
    _write(output_dir / "progress.json", result)
    _write(output_dir / "migration-evidence.json", result)
    return result


def audit_full_case_migration(repo: Path, output_dir: Path, physlib_root: Path | None = None) -> dict:
    """Audit the freshly compiled full local closure plus a Physlib bridge."""
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    library = Path(physlib_root or repo.parent / "physlib").resolve()
    if (output_dir / "full-case-audit.json").exists():
        raise ValueError("A completed common-epoch audit already exists; preserve that evidence")
    # Resumed runs preserve the first failed evidence and publish completion
    # separately. Never mistake that immutable predecessor for the final state.
    completed = output_dir / "migration-completed.json"
    migration_path = completed if completed.exists() else output_dir / "migration-evidence.json"
    migration = json.loads(migration_path.read_text())
    if migration["status"] != "FULL_LOCAL_CLOSURE_COMPILED_AUDIT_PENDING":
        raise ValueError("The whole local closure has not compiled")
    manifest = json.loads((library / "lake-manifest.json").read_text())
    if manifest != migration["resolved_manifest"]:
        raise ValueError("Library environment changed since compilation")
    if (library / "lean-toolchain").read_text().strip() != migration["toolchain"]:
        raise ValueError("Lean toolchain changed since compilation")
    expected_sources = {name: item["sha256"] for name, item in migration["catalog"]["modules"].items()}
    for change in migration["compatibility_adaptations"]:
        if expected_sources[change["module"]] != change["before_sha256"]:
            raise ValueError("Broken source-adaptation chain: " + change["module"])
        expected_sources[change["module"]] = change["after_sha256"]
    for name, item in migration["catalog"]["modules"].items():
        relative = Path(*name.split(".")).with_suffix(".lean")
        if _sha((output_dir / "originals" / relative).read_bytes()) != item["sha256"]:
            raise ValueError("Frozen original source changed: " + name)
        if _sha((output_dir / "adapted" / relative).read_bytes()) != expected_sources[name]:
            raise ValueError("Unrecorded adapted source change: " + name)
    objects = output_dir / "lib"
    for compiled in migration["compiled_modules"]:
        olean = objects / Path(*compiled["module"].split(".")).with_suffix(".olean")
        if _sha(olean.read_bytes()) != compiled["olean_sha256"]:
            raise ValueError("Compiled object changed: " + compiled["module"])
    artifact_inventory = _artifact_inventory(objects, migration["compiled_modules"])
    # Do not read live project audit targets here: independently added original
    # modules can belong to a later migration scope than this frozen closure.
    inventory_path = output_dir / "frozen-audit-targets.json"
    target_inventory = json.loads(inventory_path.read_text())
    extra_targets = {
        "MState.exp_val", "AgtXIv.CommonEpoch.quantum_admissible_sign_maximum",
        "PauliMatrix.pauliMatrix_anticommutator", "PauliMatrix.vectorMatrix_sq",
        "AgtXIv.Stabilizer.pauli_toCMatrix_isHermitian_of_sq_eq_one",
        "Pauli.mul_anticomm_of_not_commutesWith", "Pauli.toCMatrix_neg",
        "Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix",
        "AgtXIv.Varela.MeasurementWindow",
        "AgtXIv.Varela.MeasurementWindow.expectationCoordinate",
    }
    targets = sorted(set(name for names in target_inventory["targets_by_project"].values()
                         for name in names) | extra_targets)
    template = (repo / "schema v0.3/lean/EnvironmentAudit.lean").read_text()
    bridge = (repo / "schema v0.3/epoch-migration/CommonEpochBridge.lean").read_text()
    bridge = "\n".join(line for line in bridge.splitlines() if not line.startswith("import "))
    source = ("import AgtXIvStabilizerness\nimport QuantumInfo.States.Mixed.MState\n"
              "import Physlib.Relativity.PauliMatrices.Basic\n" + template + "\n" + bridge + "\n")
    source += "\n".join("#agtxiv_audit " + name for name in targets) + "\n"
    audit_root = output_dir / "audits"
    attempt = 1
    while (audit_root / ("full-case-" + str(attempt))).exists():
        attempt += 1
    audit_dir = audit_root / ("full-case-" + str(attempt))
    audit_dir.mkdir(parents=True)
    script = audit_dir / "FullCaseAudit.lean"
    script.write_text(source)
    receipt = _execute(["env", "LEAN_PATH=" + str(objects), "lake", "env", "lean", str(script)],
                       library, audit_dir / "full-case-audit.log", "lean.full_common_epoch_audit", _sha(source.encode()))
    _write(audit_dir / "full-case-audit-receipt.json", receipt)
    environment_sha = _sha(json.dumps({"objects": artifact_inventory, "manifest": manifest,
                                      "audit_source_sha256": _sha(source.encode())}, sort_keys=True).encode())
    result = {"scope": "FULL_CASE_COMMON_EPOCH_SELECTED_DECLARATIONS", "status": "AUDIT_FAILED",
              "environment_sha256": environment_sha, "toolchain": migration["toolchain"],
              "local_artifact_inventory": artifact_inventory,
              "migration_checkpoint": {"path": str(migration_path),
                                       "sha256": _sha(migration_path.read_bytes())},
              "adapted_source_sha256": expected_sources,
              "artifact_capture_scope": "CURRENT_LOCAL_MODULE_COMPANIONS_BEFORE_AND_AFTER_AUDIT",
              "audit_directory": str(audit_dir),
              "frozen_audit_targets": {"path": str(inventory_path),
                                       "sha256": _sha(inventory_path.read_bytes())},
              "requested_targets": targets, "additional_bridge_targets": sorted(extra_targets),
              "receipt": receipt, "records": [], "composition_witnesses": [],
              "query_chain_complete": False, "query_declaration": None}
    if _artifact_inventory(objects, migration["compiled_modules"]) != artifact_inventory:
        result["status"] = "ARTIFACT_SNAPSHOT_CHANGED"
    elif receipt["status"] == "SUCCEEDED":
        for line in Path(receipt["log"]).read_text().splitlines():
            if line.startswith("AGTXIV_AUDIT_JSON "):
                item = json.loads(line[len("AGTXIV_AUDIT_JSON "):])
                forbidden = sorted(set(item["axioms"]) - ALLOWED_AXIOMS)
                item.update(kernel_checked=not forbidden, forbidden_axioms=forbidden,
                            environment_sha256=environment_sha, receipt=receipt["log"],
                            statement_alignment="AGENT_NORMALIZED_UNREVIEWED", accepted=False)
                result["records"].append(item)
        records = {r["declaration"]: r for r in result["records"]}
        result["status"] = ("AUDIT_TARGET_MISMATCH" if set(records) != set(targets) else
                            "AUDIT_AXIOMS_REJECTED" if any(not r["kernel_checked"] for r in records.values()) else
                            "FULL_COMMON_EPOCH_AUDITED")
        for target in result["records"]:
            for dependency in target["term_constants"]:
                if dependency in records and dependency != target["declaration"]:
                    witness = composition_witness(result["records"], dependency, target["declaration"])
                    if witness["status"] == "COMPOSED":
                        result["composition_witnesses"].append(witness)
    result["declaration_kind_counts"] = {
        kind: sum(row["kind"] == kind for row in result["records"])
        for kind in sorted({row["kind"] for row in result["records"]})
    }
    result["coverage_scope"] = "ACTUALLY_AUDITED_SELECTED_DECLARATIONS_NOT_PAPER_CLAIM_COVERAGE"
    _write(audit_dir / "full-case-audit.json", result)
    if result["status"] == "FULL_COMMON_EPOCH_AUDITED":
        _write(output_dir / "full-case-audit.json", result)
    return result


def resume_full_case_migration(repo: Path, output_dir: Path, adaptation_files: list[Path],
                               physlib_root: Path | None = None, *,
                               allow_compiled_representation_adaptations: bool = False) -> dict:
    """Resume a stopped run after explicit, hash-bound compatibility patches.

    Existing compiled modules must be unchanged unless the narrowly scoped
    representation-adaptation option is enabled. In that case earlier objects
    are archived and their suffix is recompiled. Failed receipts and summaries
    are always preserved; each retry has a new file.
    """
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    library = Path(physlib_root or repo.parent / "physlib").resolve()
    result = json.loads((output_dir / "progress.json").read_text())
    if result["status"] != "COMPATIBILITY_BLOCKED":
        raise ValueError("Can only resume a failed compatibility checkpoint")
    if json.loads((library / "lake-manifest.json").read_text()) != result["resolved_manifest"]:
        raise ValueError("Library environment changed")
    adaptations = list(result["compatibility_adaptations"])
    changed_modules = []
    representation_modules = {
        "Quantumlib.Data.Gate.Pauli.Defs", "Quantumlib.Data.Gate.Pauli.Notation",
        "Quantumlib.Data.Gate.Pauli.Lemmas",
    }
    for path in adaptation_files:
        change = json.loads(Path(path).read_text())
        if (change["module"] != result["failed_module"] and
                not (allow_compiled_representation_adaptations and
                     change["module"] in representation_modules)):
            raise ValueError("Patch may only change the currently failed module")
        adaptations.append(change)
        changed_modules.append(change["module"])
    expected = {name: item["sha256"] for name, item in result["catalog"]["modules"].items()}
    for change in adaptations:
        if change["before_sha256"] != expected[change["module"]]:
            raise ValueError("Adaptation input hash does not match predecessor")
        expected[change["module"]] = change["after_sha256"]
    adapted, objects = output_dir / "adapted", output_dir / "lib"
    for name, source_hash in expected.items():
        source = adapted / Path(*name.split(".")).with_suffix(".lean")
        if _sha(source.read_bytes()) != source_hash:
            raise ValueError("Unrecorded compatibility change: " + name)
    for compiled in result["compiled_modules"]:
        path = objects / Path(*compiled["module"].split(".")).with_suffix(".olean")
        if _sha(path.read_bytes()) != compiled["olean_sha256"]:
            raise ValueError("Previously compiled object changed: " + compiled["module"])
    # An explicitly authorized representation patch can touch a previously
    # compiled module. Preserve the old objects and restart the whole suffix,
    # conservatively invalidating every possible downstream artifact.
    start = min([len(result["compiled_modules"])] +
                [result["compile_order"].index(name) for name in changed_modules])
    superseded = result["compiled_modules"][start:]
    if superseded:
        archive = output_dir / "superseded-objects" / ("checkpoint-" + str(len(result["receipts"])))
        destinations = [archive / Path(*item["module"].split(".")).with_suffix(".olean")
                        for item in superseded]
        if any(path.exists() for path in destinations):
            raise ValueError("Superseded-object archive already exists")
        archive.mkdir(parents=True, exist_ok=True)
        _write(archive / "invalidation-manifest.json", {
            "patched_modules": changed_modules, "compiled_modules": superseded,
            "predecessor_checkpoint": str(output_dir / ("migration-checkpoint-" + str(len(result["receipts"])) + ".json")),
        })
        for compiled in superseded:
            relative = Path(*compiled["module"].split(".")).with_suffix(".olean")
            destination = archive / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            (objects / relative).rename(destination)
        result.setdefault("invalidated_compilations", []).append({
            "reason": "EXPLICIT_REPRESENTATION_PATCH_REQUIRES_DOWNSTREAM_RECOMPILE",
            "patched_modules": changed_modules, "archive": str(archive),
            "compiled_modules": superseded,
        })
        result["compiled_modules"] = result["compiled_modules"][:start]
    result["compatibility_adaptations"] = adaptations
    result["status"] = "IN_PROGRESS"
    result.pop("failed_module", None)
    result.pop("failure_log", None)
    _write(output_dir / "progress.json", result)
    for index in range(start, len(result["compile_order"])):
        name = result["compile_order"][index]
        result["active_module"] = name
        _write(output_dir / "progress.json", result)
        source = adapted / Path(*name.split(".")).with_suffix(".lean")
        olean = objects / Path(*name.split(".")).with_suffix(".olean")
        olean.parent.mkdir(parents=True, exist_ok=True)
        attempt = len(list((output_dir / "receipts").glob("*" + name + "*.json"))) + 1
        suffix = name + "-attempt" + str(attempt)
        command = ["env", "LEAN_PATH=" + str(objects), "lake", "env", "lean", "-R", str(adapted)]
        if not name.startswith("Quantumlib."):
            command.append("-DautoImplicit=false")
        command += ["-o", str(olean), str(source)]
        receipt = _execute(command, library, output_dir / "logs" / (suffix + ".log"),
                           "lean.frozen_full_case_module_compile", _sha(source.read_bytes()))
        result["receipts"].append(receipt)
        _write(output_dir / "receipts" / (str(index).zfill(3) + "-" + suffix + ".json"), receipt)
        if receipt["status"] != "SUCCEEDED":
            result.pop("active_module", None)
            result.update(status="COMPATIBILITY_BLOCKED", failed_module=name,
                          failure_log=receipt["log"], remaining_modules=result["compile_order"][index:])
            _write(output_dir / "progress.json", result)
            _write(output_dir / ("migration-checkpoint-" + str(len(result["receipts"])) + ".json"), result)
            return result
        result["compiled_modules"].append({"module": name, "olean_sha256": _sha(olean.read_bytes())})
        _write(output_dir / "progress.json", result)
    result.update(status="FULL_LOCAL_CLOSURE_COMPILED_AUDIT_PENDING", full_case_migrated=True,
                  remaining_modules=[])
    result.pop("failed_module", None)
    result.pop("failure_log", None)
    result.pop("active_module", None)
    _write(output_dir / "progress.json", result)
    _write(output_dir / "migration-completed.json", result)
    return result


def audit_representation_port(repo: Path, migration_dir: Path, output_dir: Path,
                              physlib_root: Path | None = None) -> dict:
    """Check ported operations against their original coefficient formulas."""
    repo, migration_dir, output_dir = map(lambda p: Path(p).resolve(),
                                          (repo, migration_dir, output_dir))
    library = Path(physlib_root or repo.parent / "physlib").resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Representation audit requires a fresh output directory")
    migration = json.loads((migration_dir / "progress.json").read_text())
    if "Quantumlib.Data.Gate.Pauli.Lemmas" not in {row["module"] for row in migration["compiled_modules"]}:
        raise ValueError("Ported Pauli lemmas have not compiled")
    manifest = json.loads((library / "lake-manifest.json").read_text())
    if manifest != migration["resolved_manifest"]:
        raise ValueError("Library manifest changed")
    objects = migration_dir / "lib"
    for row in migration["compiled_modules"]:
        path = objects / Path(*row["module"].split(".")).with_suffix(".olean")
        if _sha(path.read_bytes()) != row["olean_sha256"]:
            raise ValueError("Compiled object changed: " + row["module"])
    output_dir.mkdir(parents=True, exist_ok=True)
    compatibility = (repo / "schema v0.3/epoch-migration/RepresentationCompatibility.lean").read_text()
    template = (repo / "schema v0.3/lean/EnvironmentAudit.lean").read_text()
    targets = ["PauliMap." + name for name in (
        "normalized.f_zero", "normalized_neg", "normalized_zero", "normalized_single",
        "normalized_add", "m_eq_0_of_in_normalized_support")]
    targets += ["AgtXIv.EpochCompatibility." + name for name in (
        "normalized_coeff_formula", "ofPauli_coeff_formula", "toCMatrix_coeff_formula")]
    compatibility_imports = "\n".join(line for line in compatibility.splitlines() if line.startswith("import "))
    compatibility_body = "\n".join(line for line in compatibility.splitlines() if not line.startswith("import "))
    source = compatibility_imports + "\n" + template + "\n" + compatibility_body + "\n" + "\n".join(
        "#agtxiv_audit " + name for name in targets) + "\n"
    script = output_dir / "RepresentationAudit.lean"
    script.write_text(source)
    receipt = _execute(["env", "LEAN_PATH=" + str(objects), "lake", "env", "lean", str(script)],
                       library, output_dir / "audit.log", "lean.coefficient_representation_compatibility",
                       _sha(source.encode()))
    _write(output_dir / "receipt.json", receipt)
    fingerprint = _sha(json.dumps({"compiled_modules": migration["compiled_modules"],
                                   "manifest": manifest, "script_sha256": _sha(source.encode())},
                                  sort_keys=True).encode())
    result = {"status": "AUDIT_FAILED", "scope": "PAULI_MAP_REPRESENTATION_COMPATIBILITY_ONLY",
              "receipt": receipt, "records": [], "environment_sha256": fingerprint,
              "migration_directory": str(migration_dir),
              "compatibility_adaptations": migration["compatibility_adaptations"],
              "notation_macro_expansion": "NOT_ELABORATED_NO_CASE_USAGE", "query_chain_complete": False}
    if receipt["status"] == "SUCCEEDED":
        for line in Path(receipt["log"]).read_text().splitlines():
            if line.startswith("AGTXIV_AUDIT_JSON "):
                row = json.loads(line[len("AGTXIV_AUDIT_JSON "):])
                forbidden = sorted(set(row["axioms"]) - ALLOWED_AXIOMS)
                row.update(kernel_checked=not forbidden, forbidden_axioms=forbidden,
                           environment_sha256=fingerprint, accepted=False,
                           receipt=receipt["log"],
                           statement_alignment="AGENT_NORMALIZED_UNREVIEWED")
                result["records"].append(row)
        found = {row["declaration"] for row in result["records"]}
        if found == set(targets) and all(row["kernel_checked"] for row in result["records"]):
            result["status"] = "COEFFICIENT_FORMULAS_KERNEL_CHECKED"
        else:
            result["status"] = "AUDIT_TARGET_OR_AXIOM_MISMATCH"
    _write(output_dir / "representation-evidence.json", result)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--physlib", type=Path)
    parser.add_argument("--full-case", action="store_true")
    args = parser.parse_args()
    runner = run_full_case_migration if args.full_case else run_migration_probe
    result = runner(args.repo, args.output, args.physlib)
    print(json.dumps({"status": result["status"], "audited_declarations": len(result.get("records", [])),
                      "compiled_modules": len(result.get("compiled_modules", [])),
                      "full_case_migrated": result["full_case_migrated"]}))
