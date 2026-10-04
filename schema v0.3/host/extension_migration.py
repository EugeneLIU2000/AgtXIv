"""Freeze and migrate additional audited case modules without changing baseline epochs."""
from __future__ import annotations

import json
import difflib
from pathlib import Path
import re

from epoch_migration import _artifact_inventory
from lean import ALLOWED_AXIOMS, _execute, _sha, _write, composition_witness


INITIAL_MODULES = [
    "ReducedRoMSemantics", "ConvexGeneratorInvariance", "FiniteRoMDuality",
    "ContextSignIndependence", "NoActiveDependencies", "ContextCodeState",
    "PartialFrameExtension", "SignedGeneratorCompletion", "MaximalContextPhysical",
    "ProjectedFrameCoordinates", "ContextAtomRefinement", "FiniteCliqueCoverAttainment",
]


def _predecessor(repo: Path, name: str, source_sha: str) -> dict:
    matches = []
    for receipt_path in (repo / "schema v0.3/runs").glob("*/attempt-*/receipt.json"):
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("status") != "SUCCEEDED":
            continue
        declared = receipt.get("source", {})
        source_name = Path(declared.get("path", receipt.get("command", [""])[-1])).stem
        recorded_sha = declared.get("sha256", receipt.get("source_sha256", "")).removeprefix("sha256:")
        if source_name == name and recorded_sha == source_sha:
            matches.append((receipt.get("finished_at", ""), receipt_path, receipt))
    if not matches:
        raise ValueError("No successful original-epoch receipt matches current source: " + name)
    _, receipt_path, receipt = max(matches, key=lambda item: item[0])
    records_path = receipt_path.parent / "audits.json"
    if not records_path.exists():
        records_path = receipt_path.parent / "declarations.json"
    records = json.loads(records_path.read_text())
    if not isinstance(records, list) or any(set(row["axioms"]) - ALLOWED_AXIOMS for row in records):
        raise ValueError("Predecessor declaration evidence is not usable: " + name)
    targets_path = receipt_path.parent / "audit-targets.json"
    targets = (json.loads(targets_path.read_text()) if targets_path.exists() else
               {"audited": [row["declaration"] for row in records]})
    if set(n for group in targets.values() for n in group) != {row["declaration"] for row in records}:
        raise ValueError("Predecessor targets and results disagree: " + name)
    return {"receipt": str(receipt_path), "receipt_sha256": _sha(receipt_path.read_bytes()),
            "source_sha256": source_sha, "records": str(records_path),
            "records_sha256": _sha(records_path.read_bytes()), "targets": targets,
            "original_epoch_cwd": receipt["cwd"], "original_epoch_status": receipt["status"]}


def _context(repo: Path, predecessor_extension_dirs: list[Path] | None = None) -> dict:
    base = repo / "schema v0.3/epoch-migration/runs/20260919-full-case"
    bridge = repo / "schema v0.3/epoch-migration/runs/20260919-concrete-physlib-bridge"
    frozen = repo / "schema v0.3/runs/physlib-anticommuting-20260919"
    migration = json.loads((base / "migration-completed.json").read_text())
    audit = json.loads((base / "full-case-audit.json").read_text())
    concrete = json.loads((bridge / "bridge-evidence.json").read_text())
    if audit["status"] != "FULL_COMMON_EPOCH_AUDITED" or concrete["status"] != "CONCRETE_PHYSLIB_BRIDGE_AUDITED":
        raise ValueError("Common-epoch predecessors are incomplete")
    context = {"base": str(base), "bridge": str(bridge), "frozen_alpha": str(frozen),
            "original_module_count": len(migration["compiled_modules"]),
            "base_modules": migration["compiled_modules"],
            "base_artifacts": audit["local_artifact_inventory"],
            "bridge_artifacts": concrete["environment"]["extension_objects"],
            "bridge_targets": concrete["requested_targets"],
            "frozen_alpha_olean_sha256": concrete["environment"]["frozen_local_alpha_olean_sha256"],
            "toolchain": migration["toolchain"], "manifest": migration["resolved_manifest"],
            "baseline_audit_sha256": _sha((base / "full-case-audit.json").read_bytes()),
            "bridge_audit_sha256": _sha((bridge / "bridge-evidence.json").read_bytes()),
            "additional_layers": []}
    seen = set()
    for directory in predecessor_extension_dirs or []:
        directory = Path(directory).resolve()
        prior_state = json.loads((directory / "migration-completed.json").read_text())
        prior_audit = json.loads((directory / "extension-audit.json").read_text())
        if prior_audit["status"] != "ADDITIONAL_COMMON_EPOCH_AUDITED":
            raise ValueError("Additional predecessor layer is not audited")
        prior_context = prior_state["context"]
        if (prior_context["baseline_audit_sha256"] != context["baseline_audit_sha256"] or
                prior_context["bridge_audit_sha256"] != context["bridge_audit_sha256"] or
                prior_context.get("additional_layers", []) != context["additional_layers"]):
            raise ValueError("Additional predecessor layers are not a consistent ordered chain")
        if seen & set(prior_state["modules"]):
            raise ValueError("Additional predecessor layers shadow module names")
        seen.update(prior_state["modules"])
        context["additional_layers"].append({
            "directory": str(directory), "modules": prior_state["modules"],
            "compile_order": prior_state["compile_order"],
            "compiled_modules": prior_state["compiled_modules"],
            "artifacts": prior_state["extension_artifacts"],
            "audit_sha256": _sha((directory / "extension-audit.json").read_bytes()),
            "targets": prior_audit["requested_targets"],
        })
    return context


def _check_context(context: dict, library: Path) -> None:
    if ((library / "lean-toolchain").read_text().strip() != context["toolchain"] or
            json.loads((library / "lake-manifest.json").read_text()) != context["manifest"]):
        raise ValueError("Common library epoch changed")
    if _artifact_inventory(Path(context["base"]) / "lib", context["base_modules"]) != context["base_artifacts"]:
        raise ValueError("Read-only original baseline changed")
    rows = [{"module": row["module"], "olean_sha256": row["artifacts"][".olean"]}
            for row in context["bridge_artifacts"]]
    if _artifact_inventory(Path(context["bridge"]) / "lib", rows) != context["bridge_artifacts"]:
        raise ValueError("Read-only concrete bridge changed")
    if _sha((Path(context["frozen_alpha"]) / "AnticommutingWitness.olean").read_bytes()) != context["frozen_alpha_olean_sha256"]:
        raise ValueError("Frozen Alpha object changed")
    for layer in context.get("additional_layers", []):
        directory = Path(layer["directory"])
        if (_sha((directory / "extension-audit.json").read_bytes()) != layer["audit_sha256"] or
                _artifact_inventory(directory / "lib", layer["compiled_modules"]) != layer["artifacts"]):
            raise ValueError("Read-only additional predecessor changed")


def _lean_path(context: dict, objects: Path) -> str:
    return ":".join(map(str, [objects,
        *(Path(layer["directory"]) / "lib" for layer in reversed(context.get("additional_layers", []))),
        Path(context["base"]) / "lib", Path(context["bridge"]) / "lib", context["frozen_alpha"]]))


def freeze_extension(repo: Path, output_dir: Path, module_names: list[str] | None = None, *,
                     predecessor_extension_dirs: list[Path] | None = None,
                     import_replacements: dict[str, dict[str, list[str]]] | None = None) -> dict:
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Freeze requires a fresh extension directory")
    context = _context(repo, predecessor_extension_dirs)
    _check_context(context, repo.parent / "physlib")
    available = {p.stem: p for p in (repo / "schema v0.3/lean").glob("*.lean")}
    reused = {name: row for layer in context.get("additional_layers", [])
              for name, row in layer["modules"].items()}
    modules, active, order, initial_adaptations = {}, set(), [], []

    def visit(name: str) -> None:
        if name in reused:
            if name not in available or _sha(available[name].read_bytes()) != reused[name]["source_sha256"]:
                raise ValueError("Live source differs from reused frozen predecessor: " + name)
            return
        if name in modules:
            return
        if name in active:
            raise ValueError("Cycle in additional case imports: " + name)
        if name not in available:
            raise ValueError("Missing requested extension source: " + name)
        active.add(name)
        source = available[name]
        raw = source.read_bytes()
        original = raw.decode()
        adapted = original
        for old_import, new_imports in (import_replacements or {}).get(name, {}).items():
            pattern = r"^import " + re.escape(old_import) + r"$"
            if len(re.findall(pattern, adapted, re.M)) != 1:
                raise ValueError("Import replacement must match exactly one import")
            adapted = re.sub(pattern, "\n".join("import " + module for module in new_imports), adapted, flags=re.M)
        original_body = [line for line in original.splitlines() if not re.match(r"^(?:public )?import\s+", line)]
        adapted_body = [line for line in adapted.splitlines() if not re.match(r"^(?:public )?import\s+", line)]
        if original_body != adapted_body:
            raise ValueError("Initial import adaptation changed a mathematical source line")
        imports = re.findall(r"^(?:public )?import\s+(\S+)", adapted, re.M)
        for dependency in imports:
            if dependency in available:
                visit(dependency)
        sha = _sha(raw)
        modules[name] = {"source": str(source), "source_sha256": sha, "imports": imports,
                         "original_imports": re.findall(r"^(?:public )?import\s+(\S+)", original, re.M),
                         "predecessor": _predecessor(repo, name, sha)}
        for category in ("originals", "adapted"):
            target = output_dir / category / (name + ".lean")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw if category == "originals" else adapted.encode())
        if adapted != original:
            patch = output_dir / "adaptations" / ("initial-" + name + "-imports.diff")
            patch.parent.mkdir(exist_ok=True)
            patch.write_text("".join(difflib.unified_diff(original.splitlines(True), adapted.splitlines(True),
                                                        fromfile="originals/" + name + ".lean",
                                                        tofile="adapted/" + name + ".lean")))
            change = {"module": name, "before_sha256": sha, "after_sha256": _sha(adapted.encode()),
                      "change_kind": "EXPLICIT_IMPORT_ONLY_FOUNDATION_DEDUPLICATION",
                      "mathematical_body_unchanged": True, "statement_changed": False,
                      "new_assumptions": [], "patch": str(patch),
                      "replacement_imports": (import_replacements or {})[name],
                      "review": "AGENT_NORMALIZED_UNREVIEWED", "accepted": False}
            _write(patch.with_suffix(".json"), change)
            initial_adaptations.append(change)
        active.remove(name)
        order.append(name)

    for name in module_names or INITIAL_MODULES:
        if name in reused:
            raise ValueError("Explicit extension target is already in a predecessor: " + name)
        visit(name)
    state = {"scope": "ADDITIONAL_ORIGINAL_EPOCH_MODULES_COMMON_EPOCH_MIGRATION",
             "status": "FROZEN", "query_chain_complete": False, "accepted": False,
             "source_alignment": "AGENT_NORMALIZED_UNREVIEWED", "context": context,
             "modules": modules, "compile_order": order, "compiled_modules": [],
             "receipts": [], "compatibility_adaptations": initial_adaptations}
    _write(output_dir / "frozen-extension.json", state)
    _write(output_dir / "progress.json", state)
    return state


def compile_extension(repo: Path, output_dir: Path, adaptation_files: list[Path] | None = None) -> dict:
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    library = repo.parent / "physlib"
    state = json.loads((output_dir / "progress.json").read_text())
    if state["status"] not in {"FROZEN", "COMPATIBILITY_BLOCKED"}:
        raise ValueError("Extension is not at a resumable checkpoint")
    _check_context(state["context"], library)
    for path in adaptation_files or []:
        change = json.loads(Path(path).read_text())
        if change["module"] != state.get("failed_module"):
            raise ValueError("Adapt only the currently failed extension module")
        state["compatibility_adaptations"].append(change)
    expected = {name: row["source_sha256"] for name, row in state["modules"].items()}
    for change in state["compatibility_adaptations"]:
        if change["before_sha256"] != expected[change["module"]]:
            raise ValueError("Broken extension adaptation chain")
        expected[change["module"]] = change["after_sha256"]
    for name, original in state["modules"].items():
        if _sha((output_dir / "originals" / (name + ".lean")).read_bytes()) != original["source_sha256"]:
            raise ValueError("Frozen original changed: " + name)
        if _sha((output_dir / "adapted" / (name + ".lean")).read_bytes()) != expected[name]:
            raise ValueError("Unrecorded adapted source change: " + name)
    objects = output_dir / "lib"
    objects.mkdir(exist_ok=True)
    _artifact_inventory(objects, state["compiled_modules"])
    context = state["context"]
    lean_path = _lean_path(context, objects)
    state["status"] = "IN_PROGRESS"
    state.pop("failed_module", None)
    state.pop("failure_log", None)
    for name in state["compile_order"][len(state["compiled_modules"]):]:
        state["active_module"] = name
        _write(output_dir / "progress.json", state)
        index = len(state["receipts"]) + 1
        attempt = output_dir / "attempts" / (str(index).zfill(3) + "-" + name)
        attempt.mkdir(parents=True)
        source = attempt / (name + ".lean")
        source.write_bytes((output_dir / "adapted" / (name + ".lean")).read_bytes())
        receipt = _execute(["env", "LEAN_PATH=" + lean_path, "lake", "env", "lean", "-R", str(attempt),
                            "-DautoImplicit=false", "-o", str(objects / (name + ".olean")), str(source)],
                           library, attempt / "compile.log", "lean.additional_case_module_migration", _sha(source.read_bytes()))
        _write(attempt / "receipt.json", receipt)
        state["receipts"].append(receipt)
        if receipt["status"] != "SUCCEEDED":
            state.pop("active_module", None)
            state.update(status="COMPATIBILITY_BLOCKED", failed_module=name, failure_log=receipt["log"])
            _write(output_dir / "progress.json", state)
            _write(output_dir / ("checkpoint-" + str(index).zfill(3) + ".json"), state)
            return state
        state["compiled_modules"].append({"module": name, "olean_sha256": _sha((objects / (name + ".olean")).read_bytes())})
        _write(output_dir / "progress.json", state)
    _check_context(context, library)
    state.pop("active_module", None)
    state["status"] = "ADDITIONAL_MODULES_COMPILED_AUDIT_PENDING"
    state["extension_artifacts"] = _artifact_inventory(objects, state["compiled_modules"])
    _write(output_dir / "progress.json", state)
    _write(output_dir / "migration-completed.json", state)
    return state


def audit_extension(repo: Path, output_dir: Path) -> dict:
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    library = repo.parent / "physlib"
    if (output_dir / "extension-audit.json").exists():
        raise ValueError("Preserve completed extension audit")
    state = json.loads((output_dir / "migration-completed.json").read_text())
    if state["status"] != "ADDITIONAL_MODULES_COMPILED_AUDIT_PENDING":
        raise ValueError("Additional modules have not all compiled")
    context = state["context"]
    _check_context(context, library)
    objects = output_dir / "lib"
    if _artifact_inventory(objects, state["compiled_modules"]) != state["extension_artifacts"]:
        raise ValueError("Extension objects changed")
    original_targets = {name for row in state["modules"].values()
                        for group in row["predecessor"]["targets"].values() for name in group}
    previous_targets = {name for layer in context.get("additional_layers", []) for name in layer["targets"]}
    targets = sorted(original_targets | previous_targets | set(context["bridge_targets"]))
    imported_modules = [name for layer in context.get("additional_layers", []) for name in layer["compile_order"]]
    imported_modules += state["compile_order"]
    imports = "\n".join("import " + name for name in imported_modules)
    source = (imports + "\nimport ConcretePhyslibBridge\n" +
              (repo / "schema v0.3/lean/EnvironmentAudit.lean").read_text() + "\n" +
              "\n".join("#agtxiv_audit " + name for name in targets) + "\n")
    attempt = 1
    while (output_dir / "audits" / str(attempt)).exists():
        attempt += 1
    audit_dir = output_dir / "audits" / str(attempt)
    audit_dir.mkdir(parents=True)
    script = audit_dir / "ExtensionAudit.lean"
    script.write_text(source)
    lean_path = _lean_path(context, objects)
    receipt = _execute(["env", "LEAN_PATH=" + lean_path, "lake", "env", "lean", str(script)],
                       library, audit_dir / "audit.log", "lean.additional_case_common_epoch_audit", _sha(source.encode()))
    _write(audit_dir / "receipt.json", receipt)
    environment = {"context": context, "extension_artifacts": state["extension_artifacts"],
                   "audit_source_sha256": _sha(source.encode())}
    environment_sha = _sha(json.dumps(environment, sort_keys=True).encode())
    result = {"scope": "ADDITIONAL_CASE_MODULES_PLUS_CONCRETE_PHYSLIB_COMMON_EPOCH_AUDIT",
              "status": "AUDIT_FAILED", "query_chain_complete": False, "accepted": False,
              "original_module_count": 82, "additional_migrated_module_count": len(state["compiled_modules"]),
              "prior_additional_module_count": sum(len(layer["compiled_modules"])
                                                   for layer in context.get("additional_layers", [])),
              "concrete_bridge_module_count": 2, "requested_targets": targets,
              "extension_predecessor_targets": sorted(original_targets), "environment": environment,
              "environment_sha256": environment_sha, "receipt": receipt,
              "records": [], "composition_witnesses": []}
    _check_context(context, library)
    if _artifact_inventory(objects, state["compiled_modules"]) != state["extension_artifacts"]:
        result["status"] = "EXTENSION_ARTIFACTS_CHANGED"
    elif receipt["status"] == "SUCCEEDED":
        for line in Path(receipt["log"]).read_text().splitlines():
            if line.startswith("AGTXIV_AUDIT_JSON "):
                row = json.loads(line[len("AGTXIV_AUDIT_JSON "):])
                forbidden = sorted(set(row["axioms"]) - ALLOWED_AXIOMS)
                row.update(forbidden_axioms=forbidden, kernel_checked=not forbidden,
                           environment_sha256=environment_sha, receipt=receipt["log"],
                           statement_alignment="AGENT_NORMALIZED_UNREVIEWED", accepted=False)
                result["records"].append(row)
        records = {row["declaration"]: row for row in result["records"]}
        result["status"] = ("AUDIT_TARGET_MISMATCH" if set(records) != set(targets) else
                            "AUDIT_AXIOMS_REJECTED" if any(not row["kernel_checked"] for row in records.values()) else
                            "ADDITIONAL_COMMON_EPOCH_AUDITED")
        for row in result["records"]:
            for dependency in row["term_constants"]:
                if dependency in records and dependency != row["declaration"]:
                    witness = composition_witness(result["records"], dependency, row["declaration"])
                    if witness["status"] == "COMPOSED":
                        result["composition_witnesses"].append(witness)
    result["declaration_kind_counts"] = {
        kind: sum(row["kind"] == kind for row in result["records"])
        for kind in sorted({row["kind"] for row in result["records"]})}
    _write(audit_dir / "extension-audit.json", result)
    if result["status"] == "ADDITIONAL_COMMON_EPOCH_AUDITED":
        _write(output_dir / "extension-audit.json", result)
    return result
