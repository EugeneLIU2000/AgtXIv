"""Freeze uncompiled case sources without manufacturing migration predecessors.

This is source preparation only. The output cannot be consumed as an audited
extension layer or as a compilation receipt.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extension_migration import _context
from lean import _sha, _write


def _header_imports(source: str) -> list[str]:
    """Read the supported Lean header subset, skipping nested comments.

    Stop at the first body command so strings and documentation examples in
    declarations cannot create dependencies. Unsupported import forms fail
    explicitly; Lean remains responsible for parsing the complete source.
    """
    position, imports = 0, []

    def skip() -> None:
        nonlocal position
        while position < len(source):
            if source[position].isspace():
                position += 1
            elif source.startswith("--", position):
                end = source.find("\n", position)
                position = len(source) if end < 0 else end + 1
            elif source.startswith("/-", position):
                position += 2
                depth = 1
                while depth:
                    if position >= len(source):
                        raise ValueError("Unterminated Lean header comment")
                    if source.startswith("/-", position):
                        depth += 1
                        position += 2
                    elif source.startswith("-/", position):
                        depth -= 1
                        position += 2
                    else:
                        position += 1
            else:
                return

    while True:
        skip()
        keyword = re.match(r"(?:public\s+)?import\b", source[position:])
        if keyword is None:
            # These optional header directives carry no imports themselves.
            directive = re.match(r"(?:module|prelude)\b", source[position:])
            if directive:
                position += directive.end()
                continue
            return imports
        position += keyword.end()
        skip()
        name = re.match(r"[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*", source[position:])
        if name is None:
            raise ValueError("Unsupported Lean import name")
        position += name.end()
        if position < len(source) and not (source[position].isspace() or
                source.startswith("--", position) or source.startswith("/-", position)):
            raise ValueError("Unsupported Lean import suffix")
        imports.append(name[0])


def freeze_candidate_sources(repo: Path, output_dir: Path,
                             roots: list[str] | None = None, *,
                             context_repo: Path | None = None) -> dict:
    """Retain the local import closure and references to the intended epoch.

    Environment artifacts are not validated or executed here. A subsequent
    authorized compiler must verify them before using the intended context.
    Imports are conservatively read from a comment-aware header subset;
    unresolved names remain explicit external requirements, not proven imports.

    Sources are read from ``repo``; the compiled epoch layers are described by
    ``context_repo`` (default: ``repo``), e.g. a worktree's sources against the
    main checkout's ignored compiled objects. ``AnticommutingWitness`` is not
    recompiled: the frozen Alpha object of the context provides it, and its
    frozen source must be the one that object was built from.
    """
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    context_repo = repo if context_repo is None else Path(context_repo).resolve()
    if output_dir.exists():
        raise ValueError("Candidate preparation requires a new directory")
    root_names = list(roots if roots is not None else ["QueryPerfectBranchCandidates"])
    if not root_names or len(root_names) != len(set(root_names)):
        raise ValueError("Require distinct nonempty candidate roots")
    directory = repo / "schema v0.3/lean"
    available = {path.stem: path for path in directory.glob("*.lean")}
    # This module lives below the flat source directory but is imported by name.
    # Its compiled object is the context's frozen Alpha layer, not a candidate.
    provided = {"AnticommutingWitness": directory / "frozen/AnticommutingWitness.lean"}
    if set(provided) & set(available):
        raise ValueError("Context-provided module shadowed by a flat source")
    modules, contents, active, order = {}, {}, set(), []
    external, used_provided = set(), set()

    def visit(name: str) -> None:
        if name in active:
            raise ValueError("Local candidate import cycle: " + name)
        if name in modules:
            return
        if name not in available:
            raise ValueError("Unknown local candidate root: " + name)
        active.add(name)
        path = available[name]
        raw = path.read_bytes()
        imports = _header_imports(raw.decode("utf-8"))
        for dependency in imports:
            if dependency in provided:
                used_provided.add(dependency)
            elif dependency in available:
                visit(dependency)
            else:
                external.add(dependency)
        modules[name] = {"original_path": str(path), "source_sha256": _sha(raw),
                         "snapshot": "sources/" + name + ".lean", "imports": imports,
                         "kernel_checked": False}
        contents[name] = raw
        active.remove(name)
        order.append(name)

    for root in root_names:
        visit(root)
    # Read existing epoch metadata, but deliberately do not run _check_context.
    context = _context(context_repo)
    context_provided = {}
    for name in sorted(used_provided):
        observation = json.loads((Path(context["frozen_alpha"]) /
                                  "frozen-build-observation.json").read_text())
        digest = _sha(provided[name].read_bytes())
        if (observation.get("source_sha256") != digest or
                observation.get("olean_sha256") != context["frozen_alpha_olean_sha256"]):
            raise ValueError("Frozen source is not the one the frozen Alpha object was built from")
        context_provided[name] = {"provider": "frozen_alpha", "source_path": str(provided[name]),
                                  "source_sha256": digest,
                                  "olean_sha256": context["frozen_alpha_olean_sha256"]}
    state = {"kind": "UncompiledCandidateSourceBundle", "status": "SOURCE_ONLY",
             "roots": root_names, "modules": modules, "source_dependency_order": order,
             "external_imports_unresolved": sorted(external),
             "context_provided_imports": context_provided,
             "import_discovery": "COMMENT_AWARE_HEADER_SUBSET_NOT_LEAN_PARSER",
             "intended_context": context, "context_verified": False,
             "compiled_modules": [], "receipts": [], "accepted": False,
             "source_alignment_accepted": False, "query_chain_complete": False}
    # All source reads and dependency discovery precede directory creation.
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "sources").mkdir()
    for name in order:
        (output_dir / modules[name]["snapshot"]).write_bytes(contents[name])
    _write(output_dir / "candidate-sources.json", state)
    return state
