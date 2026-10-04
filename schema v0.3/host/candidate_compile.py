"""Explicit, one-module-at-a-time compilation of source-only candidate bundles.

Calling this module's function executes Lean and requires execution authorization.
No result produced here is a declaration audit or an accepted chain certificate.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

from extension_migration import _check_context, _lean_path
from lean import _execute, _sha, _write


ARTIFACT_SUFFIXES = (".olean", ".ilean", ".olean.private", ".olean.server", ".ir", ".ir.sig")


def check_candidate_receipts(bundle_dir: Path, bundle: dict, state: dict, library: Path) -> None:
    """Bind the successful prefix to retained commands, source bytes and logs."""
    completed, receipts = state["compiled_modules"], state["receipts"]
    if len(receipts) != len(completed):
        raise ValueError("Successful prefix and receipt count disagree")
    for row, receipt in zip(completed, receipts):
        name = row["module"]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
            raise ValueError("Unsafe receipt module name")
        attempt = bundle_dir / "compile-attempts" / name
        source = attempt / (name + ".lean")
        log = attempt / "compile.log"
        expected_command = ["env", "LEAN_PATH=" + _lean_path(bundle["intended_context"], bundle_dir / "candidate-lib"),
                            "lake", "env", "lean", "-R", str(attempt), "-DautoImplicit=false", "-o",
                            str(bundle_dir / "candidate-lib" / (name + ".olean")), str(source)]
        if (json.loads((attempt / "receipt.json").read_bytes()) != receipt or
                receipt.get("status") != "SUCCEEDED" or receipt.get("exit_code") != 0 or
                receipt.get("operation") != "lean.source_only_candidate_compile" or
                receipt.get("command") != expected_command or receipt.get("cwd") != str(library) or
                receipt.get("input_sha256") != bundle["modules"][name]["source_sha256"] or
                _sha(source.read_bytes()) != receipt["input_sha256"] or
                receipt.get("log") != str(log) or _sha(log.read_bytes()) != receipt.get("output_sha256")):
            raise ValueError("Candidate compilation receipt binding changed: " + name)


def check_candidate_objects(objects: Path, completed: list[dict]) -> None:
    """Reject unrecorded search-path contents as well as changed known objects."""
    expected = {}
    for row in completed:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", row["module"]):
            raise ValueError("Unsafe compiled module name")
        if ".olean" not in row["artifacts"]:
            raise ValueError("Missing compiled object binding")
        for suffix, digest in row["artifacts"].items():
            if suffix not in ARTIFACT_SUFFIXES:
                raise ValueError("Unknown compiled artifact suffix")
            name = row["module"] + suffix
            if name in expected:
                raise ValueError("Duplicate compiled artifact binding")
            expected[name] = digest
    if objects.is_symlink():
        raise ValueError("Candidate object directory cannot be a symlink")
    paths = list(objects.iterdir()) if objects.exists() else []
    if any(path.is_symlink() or not path.is_file() for path in paths):
        raise ValueError("Unexpected candidate object directory entry")
    if {path.name for path in paths} != set(expected):
        raise ValueError("Unrecorded or missing candidate search-path artifact")
    if any(_sha(path.read_bytes()) != expected[path.name] for path in paths):
        raise ValueError("Compiled candidate artifact changed")


def compile_next_candidate(repo: Path, bundle_dir: Path, *,
                           library: Path | None = None) -> dict:
    """Compile the next frozen module; ``library`` defaults to ``repo.parent/"physlib"``."""
    repo, bundle_dir = Path(repo).resolve(), Path(bundle_dir).resolve()
    manifest = bundle_dir / "candidate-sources.json"
    raw = manifest.read_bytes()
    bundle = json.loads(raw)
    if bundle.get("kind") != "UncompiledCandidateSourceBundle":
        raise ValueError("Expected a source-only candidate bundle")
    order, modules = bundle["source_dependency_order"], bundle["modules"]
    if len(order) != len(set(order)) or set(order) != set(modules):
        raise ValueError("Invalid candidate dependency order")
    prior = set()
    for name in order:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
            raise ValueError("Unsafe local module name")
        row = modules[name]
        if row["snapshot"] != "sources/" + name + ".lean":
            raise ValueError("Unexpected source snapshot path")
        if _sha((bundle_dir / row["snapshot"]).read_bytes()) != row["source_sha256"]:
            raise ValueError("Frozen source changed: " + name)
        if any(dep in modules and dep not in prior for dep in row["imports"]):
            raise ValueError("Candidate imports are not dependency ordered")
        prior.add(name)
    context = bundle["intended_context"]
    library = repo.parent / "physlib" if library is None else Path(library).resolve()
    _check_context(context, library)
    progress = bundle_dir / "compile-progress.json"
    state = (json.loads(progress.read_text()) if progress.exists() else {
        "kind": "CandidateCompilationProgress", "status": "READY",
        "bundle_sha256": _sha(raw), "compiled_modules": [], "receipts": [],
        "accepted": False, "query_chain_complete": False,
        "declaration_audit_complete": False, "source_alignment_accepted": False})
    if state["bundle_sha256"] != _sha(raw):
        raise ValueError("Candidate manifest changed")
    if state["status"] != "READY":
        raise ValueError("Candidate is terminal or requires interrupted-attempt review")
    completed = state["compiled_modules"]
    if [row["module"] for row in completed] != order[:len(completed)]:
        raise ValueError("Completed modules are not an ordered prefix")
    objects = bundle_dir / "candidate-lib"
    check_candidate_objects(objects, completed)
    check_candidate_receipts(bundle_dir, bundle, state, library)
    if len(completed) >= len(order):
        raise ValueError("No remaining candidate module")
    name = order[len(completed)]
    attempt = bundle_dir / "compile-attempts" / name
    attempt.mkdir(parents=True, exist_ok=False)
    objects.mkdir(exist_ok=True)
    source = attempt / (name + ".lean")
    source.write_bytes((bundle_dir / modules[name]["snapshot"]).read_bytes())
    state.update(status="IN_PROGRESS", active_module=name)
    _write(progress, state)
    receipt = _execute([
        "env", "LEAN_PATH=" + _lean_path(context, objects), "lake", "env", "lean",
        "-R", str(attempt), "-DautoImplicit=false", "-o",
        str(objects / (name + ".olean")), str(source)], library,
        attempt / "compile.log", "lean.source_only_candidate_compile", modules[name]["source_sha256"])
    _write(attempt / "receipt.json", receipt)
    state["receipts"].append(receipt)
    state.pop("active_module")
    state["status"] = "COMPILE_FAILED"
    if receipt["status"] == "SUCCEEDED":
        try:
            _check_context(context, library)
            if manifest.read_bytes() != raw:
                raise ValueError("Manifest changed during compilation")
            for module, row in modules.items():
                if _sha((bundle_dir / row["snapshot"]).read_bytes()) != row["source_sha256"]:
                    raise ValueError("Source changed during compilation: " + module)
            if _sha(source.read_bytes()) != modules[name]["source_sha256"]:
                raise ValueError("Attempt source changed during compilation")
            artifacts = {suffix: _sha((objects / (name + suffix)).read_bytes())
                         for suffix in ARTIFACT_SUFFIXES if (objects / (name + suffix)).exists()}
            next_completed = completed + [{"module": name, "artifacts": artifacts}]
            check_candidate_objects(objects, next_completed)
            state["compiled_modules"] = next_completed
            state["status"] = ("COMPILED_AUDIT_PENDING" if len(next_completed) == len(order) else "READY")
        except (ValueError, OSError, KeyError) as exc:
            state.update(status="COMPILE_EVIDENCE_REJECTED", error=str(exc))
    _write(progress, state)
    return state
