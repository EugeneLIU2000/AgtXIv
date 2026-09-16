"""Bounded, offline inspection of explicitly supplied local source directories.

Inspection observes bytes and limited TeX syntax. It does not authenticate a
paper version, infer redistribution rights, execute source, or certify fidelity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from types import MappingProxyType
from typing import Mapping
import unicodedata

from .source import SourceError, TexStructure, analyze_tex_structure, fingerprint


@dataclass(frozen=True)
class IntakeLimits:
    max_entries: int = 10_000
    max_files: int = 5_000
    max_file_bytes: int = 16 * 1024 * 1024
    max_total_bytes: int = 32 * 1024 * 1024
    max_depth: int = 32
    max_path_bytes: int = 1024
    max_commands: int = 100_000
    max_includes: int = 10_000
    max_conditional_depth: int = 256

    def __post_init__(self):
        if any(type(value) is not int or value < 1 for value in vars(self).values()):
            raise SourceError("Intake limits must be positive integers")


LIMITATIONS = (
    "This is a local byte inventory and bounded static syntax inspection, not source-fidelity certification.",
    "No TeX, source code, PDF renderer, macro interpreter, network request, or scientific check was executed.",
    "Static include activity is not proof that a passage participated in a published rendering or is an author assertion.",
    "Non-TeX materials are inventoried and hashed, but their content and participation are unassessed.",
    "The source directory is caller-selected; external completeness, exact publication version, and redistribution rights are unverified.",
    "Retained bytes identify the inspected inputs; filesystem checks do not establish a globally atomic filesystem snapshot.",
)


def _relative(value: str, max_bytes: int) -> str:
    if not isinstance(value, str) or not value or "\\" in value or re.search(r"[\x00-\x1f\x7f]", value):
        raise SourceError("Source paths must be nonempty relative POSIX paths without controls")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError as error:
        raise SourceError("Source paths must be valid UTF-8") from error
    path = PurePosixPath(value)
    if size > max_bytes or path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", value) or path.as_posix() == ".":
        raise SourceError("Source path is unsafe or exceeds the path-byte limit")
    return path.as_posix()


def _open_directory_no_symlinks(path: Path) -> tuple[Path, int]:
    """Open every component through directory descriptors, rejecting symlinks."""
    if not hasattr(os, "O_NOFOLLOW") or os.name != "posix":
        raise SourceError("Safe directory inspection requires POSIX no-follow directory descriptors")
    absolute = Path(os.path.abspath(path))
    if ".." in path.parts:
        raise SourceError("Directory path must not contain parent traversal")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in absolute.parts[1:]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
    except BaseException:
        os.close(descriptor)
        raise
    return absolute, descriptor


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _kind(path: str) -> tuple[str, str]:
    suffix = PurePosixPath(path).suffix.lower()
    if suffix == ".tex":
        return "TEX", "text/x-tex"
    if suffix == ".pdf":
        return "PDF", "application/pdf"
    if suffix in {".bib", ".bbl"}:
        return "BIBLIOGRAPHY", "text/plain"
    if suffix in {".png", ".jpg", ".jpeg", ".svg", ".eps", ".tif", ".tiff"}:
        return "FIGURE", "application/octet-stream"
    if suffix in {".py", ".r", ".jl", ".m", ".c", ".cpp", ".sh", ".lean"}:
        return "CODE", "text/plain"
    if suffix in {".csv", ".tsv", ".json", ".h5", ".hdf5", ".npy", ".npz"}:
        return "DATA", "application/octet-stream"
    return "OTHER", "application/octet-stream"


@dataclass(frozen=True)
class LocalInspection:
    root: Path
    observed_at: str
    sources: Mapping[str, bytes]
    structure: TexStructure
    limits: IntakeLimits

    def __post_init__(self):
        object.__setattr__(self, "sources", MappingProxyType(dict(self.sources)))

    def report(self) -> dict:
        """Return a fresh English report without modifying or embedding sources."""
        files = []
        for path, data in sorted(self.sources.items(), key=lambda pair: pair[0].encode("utf-8")):
            item = fingerprint(path, data)
            role, media_type = _kind(path)
            is_tex = role == "TEX" or path == self.structure.main
            files.append({
                "path": path, "byte_size": item.size_bytes, "sha256": "sha256:" + item.sha256,
                "kind": role, "media_type_hint": media_type, "kind_basis": "FILENAME_EXTENSION_ONLY",
                "static_include_activity": self.structure.file_activity[path] if is_tex else None,
                "analysis": "BOUNDED_TEX_SYNTAX" if is_tex else "BYTES_ONLY_UNSUPPORTED_CONTENT",
                "published_rendering_activity": "UNASSESSED",
            })
        return {
            "report_type": "agtxiv.v3.local-source-inspection/0.0.0",
            "data_class": "OBSERVED", "observation": "LOCAL_FILESYSTEM_BYTES",
            "source_root": str(self.root), "observed_at": self.observed_at,
            "main": self.structure.main, "working_directory": self.structure.working_directory,
            "limits": asdict(self.limits), "file_count": len(files),
            "total_bytes": sum(item["byte_size"] for item in files), "files": files,
            "includes": [asdict(edge) for edge in self.structure.includes],
            "issues": [asdict(issue) for issue in self.structure.issues],
            "syntax_requires_review": self.structure.requires_review,
            "unsupported_content_paths": [item["path"] for item in files if item["analysis"] == "BYTES_ONLY_UNSUPPORTED_CONTENT"],
            "unclassified_publication_participation_paths": [item["path"] for item in files],
            "source_fidelity_assessment": "NOT_PERFORMED",
            "scientific_assessment": "NOT_PERFORMED",
            "limitations": list(LIMITATIONS),
        }

    def json_bytes(self) -> bytes:
        return (json.dumps(self.report(), ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def inspect_source_directory(
    root: str | Path,
    main: str,
    *,
    working_directory: str = ".",
    limits: IntakeLimits = IntakeLimits(),
) -> LocalInspection:
    """Read a complete bounded local inventory without following any symlink.

    Files, directories and path components are opened relative to already-open
    directory descriptors. Links, special files, cross-device mounts, and
    detectable concurrent modifications fail closed. No partial report escapes.
    All original bytes, including non-TeX and dormant files, are retained.
    """
    main = _relative(main, limits.max_path_bytes)
    if working_directory != ".":
        working_directory = _relative(working_directory, limits.max_path_bytes)
    directory, root_fd = _open_directory_no_symlinks(Path(root))
    sources: dict[str, bytes] = {}
    entries = 0
    total = 0
    device = os.fstat(root_fd).st_dev

    def visit(descriptor: int, prefix: str, depth: int):
        nonlocal entries, total
        if depth > limits.max_depth:
            raise SourceError("Source directory exceeds the depth limit")
        before = os.fstat(descriptor)
        # scandir is lazy, so a directory with millions of entries cannot force
        # an unbounded list allocation before the entry budget is checked.
        with os.scandir(descriptor) as iterator:
            for entry in iterator:
                entries += 1
                if entries > limits.max_entries:
                    raise SourceError("Source directory exceeds the entry limit")
                relative = _relative(prefix + entry.name, limits.max_path_bytes)
                info = os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    raise SourceError("Symbolic links are forbidden in a source directory: " + relative)
                if info.st_dev != device:
                    raise SourceError("Cross-device source entries are forbidden: " + relative)
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
                    try:
                        if _stamp(os.fstat(child)) != _stamp(info):
                            raise SourceError("Source directory changed during inspection: " + relative)
                        visit(child, relative + "/", depth + 1)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode):
                    if info.st_nlink != 1:
                        raise SourceError("Hard-linked source files are forbidden: " + relative)
                    if len(sources) >= limits.max_files:
                        raise SourceError("Source directory exceeds the file count limit")
                    if info.st_size > limits.max_file_bytes:
                        raise SourceError("Source file exceeds the per-file byte limit: " + relative)
                    if total + info.st_size > limits.max_total_bytes:
                        raise SourceError("Source directory exceeds the total byte limit")
                    file_fd = os.open(entry.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor)
                    with os.fdopen(file_fd, "rb") as stream:
                        opened = os.fstat(stream.fileno())
                        if not stat.S_ISREG(opened.st_mode) or _stamp(opened) != _stamp(info):
                            raise SourceError("Source file changed before reading: " + relative)
                        # One byte beyond the smallest remaining budget detects
                        # growth without reading an arbitrarily large file.
                        budget = min(limits.max_file_bytes, limits.max_total_bytes - total)
                        data = stream.read(budget + 1)
                        if len(data) > budget or len(data) != opened.st_size or _stamp(os.fstat(stream.fileno())) != _stamp(opened):
                            raise SourceError("Source file changed or exceeded its byte limit while reading: " + relative)
                    if _stamp(os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)) != _stamp(opened):
                        raise SourceError("Source file was replaced during inspection: " + relative)
                    total += len(data)
                    sources[relative] = data
                else:
                    raise SourceError("Only regular files and directories are supported: " + relative)
        if _stamp(os.fstat(descriptor)) != _stamp(before):
            raise SourceError("Source directory entries changed during inspection")

    try:
        visit(root_fd, "", 0)
    finally:
        os.close(root_fd)
    if main not in sources:
        raise SourceError("Explicit TeX main is absent from the source directory")
    if working_directory != "." and not any(path.startswith(working_directory + "/") for path in sources):
        raise SourceError("Explicit TeX working directory contains no supplied files")
    structure = analyze_tex_structure(
        main, sources, working_directory=working_directory,
        max_files=limits.max_files, max_total_bytes=limits.max_total_bytes,
        max_commands=limits.max_commands, max_includes=limits.max_includes,
        max_conditional_depth=limits.max_conditional_depth,
    )
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return LocalInspection(directory, observed_at, sources, structure, limits)


@dataclass(frozen=True)
class SourceCandidates:
    source_snapshot: dict
    paper_structure: dict
    artifacts: tuple
    limitations: tuple[str, ...] = LIMITATIONS


def build_source_candidates(
    inspection: LocalInspection,
    *,
    bundle,
    producer: dict,
    policy_ref: dict,
    source_record_id: str,
    structure_record_id: str,
    paper_id: str,
    paper_version: str,
    created_at: str,
    rights_status: str,
    rights_note: str,
) -> SourceCandidates:
    """Build shape-checked candidates from actual retained bytes and caller data.

    Caller supplies every identity, policy and bibliographic/rights declaration.
    No policy is invented, reviewer is impersonated, or assessment is emitted.
    Actual publication participation stays UNKNOWN on every source unit. Exact
    include syntax is projected into PaperStructure and retained in a raw report
    artifact. The candidates do not prove their external policy reference exists.
    """
    from .contracts import SuppliedArtifact, exact_ref

    if not policy_ref:
        raise SourceError("An explicit caller-supplied authority policy reference is required")
    if paper_version.strip().lower() in {"latest", "current", "head", "main"}:
        raise SourceError("Caller must provide an exact paper version, not a floating selector")
    if any(unicodedata.normalize("NFC", path) != path for path in inspection.sources):
        raise SourceError("Candidate records require an explicit mapping for non-NFC source paths; raw inspection remains available")
    artifacts = {}
    units = []
    unit_ids = {}
    for path, data in sorted(inspection.sources.items()):
        unit_id = "unit:path-" + hashlib.sha256(path.encode("utf-8")).hexdigest()
        unit_ids[path] = unit_id
        role, media_type = _kind(path)
        artifact = SuppliedArtifact("artifact:sha256-" + hashlib.sha256(data).hexdigest(), media_type, data)
        # Equal bytes with different extension-derived media types need distinct
        # artifact declarations even when their content digest is identical.
        artifact = SuppliedArtifact(artifact.artifact_id + "-" + hashlib.sha256(media_type.encode()).hexdigest()[:12], media_type, data)
        artifacts[artifact.artifact_id] = artifact
        units.append({"unit_id": unit_id, "relative_path": path, "artifact": artifact.reference(path), "activity": "UNKNOWN", "kind": role})
    source = bundle.make_record(
        "source-snapshot", source_record_id,
        {"paper_id": paper_id, "paper_version": paper_version, "source_uri": inspection.root.as_uri(),
         "acquired_at": inspection.observed_at, "acquisition_ref": None, "acquisition_method": "LOCAL_IMPORT",
         "units": units, "archive": None, "missing_material": [], "rights_status": rights_status, "rights_note": rights_note},
        producer=producer, policy_ref=policy_ref, created_at=created_at, data_class="OBSERVED",
    )
    report = inspection.json_bytes()
    report_artifact = SuppliedArtifact("artifact:inspection-" + hashlib.sha256(report).hexdigest(), "application/json", report)
    artifacts[report_artifact.artifact_id] = report_artifact
    edges = [{"source_unit_id": unit_ids[edge.source], "target_unit_id": unit_ids[edge.target],
              "relation": "INCLUDES", "activity": {"ACTIVE": "ACTIVE", "INACTIVE": "DORMANT", "UNKNOWN": "UNKNOWN"}[edge.activity],
              "locator": f"{edge.source}: original bytes [{edge.start_byte}, {edge.end_byte})"}
             for edge in inspection.structure.includes if edge.target is not None]
    blockers = list(LIMITATIONS) + [f"{issue.code} at {issue.path}:{issue.byte_offset}: {issue.detail}" for issue in inspection.structure.issues]
    blockers.append("Full raw inspection report: " + report_artifact.artifact_id + " (" + report_artifact.reference()["sha256"] + ")")
    structure = bundle.make_record(
        "paper-structure", structure_record_id,
        {"source_ref": exact_ref(source), "main_unit_id": unit_ids[inspection.structure.main], "edges": edges,
         "unclassified_unit_ids": list(unit_ids.values()), "blockers": blockers},
        producer=producer, policy_ref=policy_ref, input_refs=(exact_ref(source),), created_at=created_at, data_class="OBSERVED",
    )
    return SourceCandidates(source, structure, tuple(artifacts.values()))
