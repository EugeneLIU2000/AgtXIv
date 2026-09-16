"""Bounded local source handling for V3; never executes TeX or downloads content.

This is not a source-acquisition pipeline or a full TeX interpreter. TeX activity
is a *static syntactic* projection under ordinary TeX tokenization. Unsupported
constructs remain explicit blockers. Callers must not turn this result into a
preprocessing READY decision, author assertion, or source-fidelity assessment.
"""

from __future__ import annotations

import ctypes
import gzip
import hashlib
import hmac
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping


class SourceError(ValueError):
    """An invalid, unsafe, unsupported, or over-budget source input."""


@dataclass(frozen=True)
class ArchiveLimits:
    max_archive_bytes: int = 64 * 1024 * 1024
    max_expanded_archive_bytes: int = 320 * 1024 * 1024
    max_entries: int = 10_000
    max_files: int = 5_000
    max_file_bytes: int = 32 * 1024 * 1024
    max_total_bytes: int = 256 * 1024 * 1024
    max_path_bytes: int = 1024

    def __post_init__(self) -> None:
        if any(type(value) is not int or value < 1 for value in vars(self).values()):
            raise SourceError("Archive limits must be positive integers")


@dataclass(frozen=True)
class SourceFile:
    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class SourceTree:
    destination: Path
    archive_sha256: str
    source_tree_sha256: str
    files: tuple[SourceFile, ...]


def _relative_path(value: str, *, max_bytes: int = 1024) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise SourceError("Expected a nonempty relative POSIX path")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise SourceError("Path is not valid UTF-8") from error
    if len(encoded) > max_bytes:
        raise SourceError("Path exceeds its byte limit")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", value):
        raise SourceError("Absolute and traversing paths are forbidden")
    canonical = path.as_posix()
    if canonical == ".":
        raise SourceError("Path must name an entry below the source root")
    return canonical


def fingerprint(path: str, data: bytes) -> SourceFile:
    """Fingerprint exact original bytes; do not normalize Unicode or newlines."""
    if not isinstance(data, bytes):
        raise SourceError("Source data must be bytes")
    return SourceFile(_relative_path(path), len(data), hashlib.sha256(data).hexdigest())


def verify_byte_span(
    data: bytes,
    start: int,
    end: int,
    *,
    expected_sha256: str,
    expected_bytes: bytes | None = None,
) -> bytes:
    """Verify a nonempty half-open original-byte span [start, end).

    Character offsets, inferred text, and silently normalized line endings are
    not substitutes for a byte span. Caller separately binds the original file
    hash (e.g. via ``fingerprint``) to the source snapshot.
    """
    if not isinstance(data, bytes) or type(start) is not int or type(end) is not int:
        raise SourceError("Span requires bytes and integer offsets")
    if not 0 <= start < end <= len(data):
        raise SourceError("Span must be nonempty and inside the original bytes")
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise SourceError("Expected a lowercase SHA-256 digest")
    span = data[start:end]
    if not hmac.compare_digest(hashlib.sha256(span).hexdigest(), expected_sha256):
        raise SourceError("Span SHA-256 does not match")
    if expected_bytes is not None and (
        not isinstance(expected_bytes, bytes) or not hmac.compare_digest(span, expected_bytes)
    ):
        raise SourceError("Span bytes do not match")
    return span


def _rename_without_replacement(source: Path, destination: Path) -> None:
    """Publish atomically without the check/rename directory-overwrite race."""
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        operation = libc.renamex_np
        operation.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        result = operation(os.fsencode(source), os.fsencode(destination), 4)  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        operation = libc.renameat2
        operation.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        result = operation(-100, os.fsencode(source), -100, os.fsencode(destination), 1)  # NOREPLACE
    else:
        raise SourceError("Atomic no-replace directory publication is unsupported on this platform")
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def extract_tar_atomic(
    archive: bytes | Path,
    destination: Path,
    *,
    limits: ArchiveLimits = ArchiveLimits(),
) -> SourceTree:
    """Safely extract a tar/tar.gz input into a previously absent destination.

    The existing parent must be a caller-controlled directory. All staging is
    private and on the same filesystem; failed extraction leaves no destination
    or temporary tree. Existing destinations (including symlinks) are preserved.
    Regular files/directories only; no extractall, external commands, permissions,
    owner metadata, links, sparse files, or archive paths are trusted.
    """
    destination = Path(destination)
    parent = destination.parent.resolve(strict=True)
    target = parent / destination.name
    if destination.name in ("", ".", "..") or os.path.lexists(target):
        raise SourceError("Destination must be a previously absent named directory")
    if isinstance(archive, Path):
        with archive.open("rb") as stream:
            payload = stream.read(limits.max_archive_bytes + 1)
    elif isinstance(archive, bytes):
        payload = archive
    else:
        raise SourceError("Archive must be bytes or a Path")
    if len(payload) > limits.max_archive_bytes:
        raise SourceError("Archive exceeds its byte limit")
    # Bound decompression *before* tarfile sees headers. Otherwise a compressed
    # PAX/longname header can allocate unbounded memory before member limits run.
    expanded = payload
    if payload.startswith((b"BZh", b"\xfd7zXZ\x00")):
        raise SourceError("This bounded extractor supports only plain tar and gzip-compressed tar")
    decompressor = gzip.open if payload.startswith(b"\x1f\x8b") else None
    if decompressor is not None:
        try:
            with decompressor(io.BytesIO(payload), "rb") as stream:
                expanded = stream.read(limits.max_expanded_archive_bytes + 1)
        except (OSError, EOFError) as error:
            raise SourceError("Invalid compressed archive") from error
    if len(expanded) > limits.max_expanded_archive_bytes:
        raise SourceError("Archive exceeds its expanded container byte limit")
    temporary = Path(tempfile.mkdtemp(prefix=".agtxiv-source-", dir=parent))
    files: list[SourceFile] = []
    seen: set[str] = set()
    total = 0
    try:
        with tarfile.open(fileobj=io.BytesIO(expanded), mode="r|") as tar:
            for count, member in enumerate(tar, start=1):
                if count > limits.max_entries:
                    raise SourceError("Archive exceeds its entry limit")
                name = _relative_path(member.name, max_bytes=limits.max_path_bytes)
                if name in seen:
                    raise SourceError("Duplicate normalized archive path")
                seen.add(name)
                if not (member.isdir() or member.isfile()) or member.issparse():
                    raise SourceError("Only nonsparse regular files and directories are permitted")
                path = temporary / name
                if member.isdir():
                    path.mkdir(parents=True, exist_ok=True)
                    continue
                if len(files) >= limits.max_files:
                    raise SourceError("Archive exceeds its file count limit")
                if member.size < 0 or member.size > limits.max_file_bytes:
                    raise SourceError("Archive member exceeds its byte limit")
                total += member.size
                if total > limits.max_total_bytes:
                    raise SourceError("Archive exceeds its total extracted byte limit")
                path.parent.mkdir(parents=True, exist_ok=True)
                reader = tar.extractfile(member)
                if reader is None:
                    raise SourceError("Cannot read archive member")
                digest = hashlib.sha256()
                written = 0
                with reader, path.open("xb") as writer:
                    while chunk := reader.read(min(65536, member.size - written + 1)):
                        written += len(chunk)
                        if written > member.size:
                            raise SourceError("Archive member exceeds its declared size")
                        digest.update(chunk)
                        writer.write(chunk)
                if written != member.size:
                    raise SourceError("Truncated archive member")
                files.append(SourceFile(name, written, digest.hexdigest()))
        if not files or total == 0:
            raise SourceError("Archive contains no nonempty regular-file payload")
        ordered = tuple(sorted(files, key=lambda entry: entry.path.encode("utf-8")))
        # This string-only, fixed-key shape has the same encoding as RFC 8785.
        manifest = [{"path": entry.path, "type": "file", "sha256": entry.sha256} for entry in ordered]
        canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        result = SourceTree(target, hashlib.sha256(payload).hexdigest(), hashlib.sha256(canonical).hexdigest(), ordered)
        _rename_without_replacement(temporary, target)
        return result
    except (tarfile.TarError, EOFError, UnicodeError) as error:
        raise SourceError("Invalid or truncated tar archive") from error
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


@dataclass(frozen=True)
class TexIssue:
    path: str
    byte_offset: int
    code: str
    detail: str


@dataclass(frozen=True)
class TexInclude:
    source: str
    command: str
    start_byte: int
    end_byte: int
    raw_argument: str
    target: str | None
    activity: str  # ACTIVE, INACTIVE, UNKNOWN under the stated static profile


@dataclass(frozen=True)
class TexStructure:
    main: str
    working_directory: str
    files: tuple[SourceFile, ...]
    includes: tuple[TexInclude, ...]
    file_activity: Mapping[str, str]
    issues: tuple[TexIssue, ...]
    semantics: str = "BOUNDED_STATIC_SYNTAX_NOT_TEX_EXECUTION"

    @property
    def requires_review(self) -> bool:
        return bool(self.issues)


_COMMAND = re.compile(rb"\\([A-Za-z@]+|[^\r\n])")
_VERBATIM_BEGIN = re.compile(rb"\\begin\s*\{(verbatim\*?)\}")
_DEFINITIONS = {"newcommand", "renewcommand", "providecommand", "DeclareRobustCommand", "def", "gdef", "edef", "xdef", "newenvironment", "renewenvironment"}
_OPAQUE = {"catcode", "csname", "expandafter", "let", "futurelet", "includeonly", "usepackage", "RequirePackage", "documentclass", "IfFileExists", "InputIfFileExists", "scantokens", "directlua"}
_SAFE_SYNTAX = {"begin", "end", "section", "subsection", "subsubsection", "paragraph", "subparagraph", "chapter", "part", "appendix", "label", "ref", "eqref", "cite", "title", "author", "date", "maketitle"}


def _blank_comments_and_verbatim(data: bytes) -> tuple[bytes, list[tuple[int, str, str]]]:
    """Mask comments and lexical verbatim while keeping exact byte coordinates."""
    result = bytearray(data)
    issues: list[tuple[int, str, str]] = []
    index = 0
    while index < len(data):
        if data[index] == 37:  # Unescaped percent; backslash tokens are skipped below.
            end = data.find(b"\n", index)
            if end < 0:
                end = len(data)
            result[index:end] = b" " * (end - index)
            index = end
        elif data[index] == 92:
            token = _COMMAND.match(data, index)
            if token is None:
                index += 1
                continue
            if token.group(1) in (b"verb", b"Verb"):
                cursor = token.end()
                if data[cursor:cursor + 1] == b"*":
                    cursor += 1
                if cursor < len(data) and data[cursor] not in b" \t\r\n":
                    end = data.find(data[cursor:cursor + 1], cursor + 1)
                    newline = data.find(b"\n", cursor)
                    if end < 0 or (newline >= 0 and newline < end):
                        issues.append((index, "MALFORMED_VERBATIM", "Inline verbatim delimiter is not closed on this line"))
                        end = newline if newline >= 0 else len(data)
                    else:
                        end += 1
                    result[index:end] = b" " * (end - index)
                    index = end
                    continue
                issues.append((index, "MALFORMED_VERBATIM", "Inline verbatim has no valid delimiter"))
            begin = _VERBATIM_BEGIN.match(data, index)
            if begin:
                ending = b"\\end{" + begin.group(1) + b"}"
                end = data.find(ending, begin.end())
                if end < 0:
                    issues.append((index, "MALFORMED_VERBATIM", "Verbatim environment has no closing marker"))
                end = len(data) if end < 0 else end + len(ending)
                result[index:end] = b" " * (end - index)
                index = end
            else:
                index = token.end()
        else:
            index += 1
    return bytes(result), issues


def _argument(data: bytes, start: int, command: str) -> tuple[bytes, int, bool]:
    cursor = start
    while cursor < len(data) and data[cursor] in b" \t\r\n":
        cursor += 1
    if cursor == len(data):
        return b"", cursor, False
    if data[cursor] == 123:
        depth, end = 1, cursor + 1
        while end < len(data) and depth:
            if data[end] == 92:
                match = _COMMAND.match(data, end)
                end = match.end() if match else end + 1
                continue
            depth += (data[end] == 123) - (data[end] == 125)
            end += 1
        return data[cursor + 1:end - 1 if depth == 0 else end], end, depth == 0
    if command == "input":
        end = cursor
        while end < len(data) and data[end] not in b" \t\r\n{}":
            end += 1
        return data[cursor:end], end, end > cursor
    return b"", cursor, False


def analyze_tex_structure(
    main: str,
    sources: Mapping[str, bytes],
    *,
    working_directory: str = ".",
    max_files: int = 5000,
    max_total_bytes: int = 32 * 1024 * 1024,
    max_commands: int = 100_000,
    max_includes: int = 10_000,
    max_conditional_depth: int = 256,
) -> TexStructure:
    """Inspect supplied bytes under an explicit main and TeX working directory.

    Resolves literal input/include paths against working_directory (TeX does not
    automatically chdir into included files). Handles ordinary percent comments,
    lexical verbatim, nested literal iftrue/iffalse, else/fi and endinput. Macros,
    packages, includeonly and nonliteral conditions are review blockers. Includes
    after opaque constructs are UNKNOWN. Missing files/cycles are retained.
    Unreferenced files are INACTIVE only in this limited syntactic graph; any
    reachable opaque construct makes unobserved files UNKNOWN instead.

    No macro expansion, claim extraction, head.tex, PDF mapping, or full semantic
    activity is produced. In particular, ACTIVE never means published assertion.
    """
    if any(type(limit) is not int or limit < 1 for limit in (max_files, max_total_bytes, max_commands, max_includes, max_conditional_depth)):
        raise SourceError("Static-analysis limits must be positive integers")
    if len(sources) > max_files:
        raise SourceError("Static analysis exceeds its file count limit")
    canonical: dict[str, bytes] = {}
    total = 0
    for name, data in sources.items():
        name = _relative_path(name)
        if name in canonical:
            raise SourceError("Duplicate normalized source path")
        if not isinstance(data, bytes):
            raise SourceError("Supplied sources must contain bytes")
        total += len(data)
        if total > max_total_bytes:
            raise SourceError("Static analysis exceeds its total byte limit")
        canonical[name] = data
    main = _relative_path(main)
    if main not in canonical:
        raise SourceError("Explicit TeX main is missing")
    working_directory = "." if working_directory == "." else _relative_path(working_directory)
    includes: list[TexInclude] = []
    issues: list[TexIssue] = []
    local_edges: dict[str, list[TexInclude]] = {}
    opaque_files: set[str] = set()
    command_count = 0
    include_count = 0
    for name, original in sorted(canonical.items()):
        if not name.endswith(".tex") and name != main:
            continue
        try:
            original.decode("utf-8", errors="strict")
        except UnicodeError:
            issues.append(TexIssue(name, 0, "UNSUPPORTED_ENCODING", "TeX source is not UTF-8; no syntax is inferred"))
            opaque_files.add(name)
            continue
        data, lexical_issues = _blank_comments_and_verbatim(original)
        if lexical_issues:
            opaque_files.add(name)
            issues.extend(TexIssue(name, *issue) for issue in lexical_issues)
        # Verbatim masking itself assumes standard package definitions. Never
        # treat arbitrary custom environments as executed or expanded.
        frames: list[tuple[str, bool]] = []
        ended = False
        opaque = False
        edges: list[TexInclude] = []
        cursor = 0
        while match := _COMMAND.search(data, cursor):
            command_count += 1
            if command_count > max_commands:
                raise SourceError("Static analysis exceeds its command count limit")
            cursor = match.end()
            command = match.group(1).decode("ascii", errors="replace")
            def activity() -> str:
                if ended:
                    return "INACTIVE"
                if opaque:
                    return "UNKNOWN"
                if any(state == "INACTIVE" for state, _ in frames):
                    return "INACTIVE"
                if any(state == "UNKNOWN" for state, _ in frames):
                    return "UNKNOWN"
                return "ACTIVE"
            if command.startswith("if") and command not in {"ifthenelse"}:
                if len(frames) >= max_conditional_depth:
                    raise SourceError("Static analysis exceeds its conditional nesting limit")
                state = "ACTIVE" if command == "iftrue" else "INACTIVE" if command == "iffalse" else "UNKNOWN"
                if state == "UNKNOWN":
                    issues.append(TexIssue(name, match.start(), "CONDITIONAL_UNKNOWN", f"Cannot evaluate \\{command}"))
                    opaque_files.add(name)
                frames.append((state, False))
                continue
            if command == "else":
                if not frames or frames[-1][1]:
                    issues.append(TexIssue(name, match.start(), "UNBALANCED_CONDITIONAL", "Unmatched or repeated else"))
                    opaque = True
                    opaque_files.add(name)
                else:
                    state, _ = frames[-1]
                    frames[-1] = ({"ACTIVE": "INACTIVE", "INACTIVE": "ACTIVE", "UNKNOWN": "UNKNOWN"}[state], True)
                continue
            if command == "fi":
                if frames:
                    frames.pop()
                else:
                    issues.append(TexIssue(name, match.start(), "UNBALANCED_CONDITIONAL", "Unmatched fi"))
                    opaque = True
                    opaque_files.add(name)
                continue
            if command in _DEFINITIONS | _OPAQUE or command == "ifthenelse":
                if activity() != "INACTIVE":
                    issues.append(TexIssue(name, match.start(), "OPAQUE_TEX", f"\\{command} requires semantics outside this static profile"))
                    opaque = True
                    opaque_files.add(name)
                continue
            if command == "endinput":
                if activity() == "ACTIVE":
                    ended = True
                elif activity() == "UNKNOWN":
                    opaque = True
                continue
            if command not in {"input", "include"}:
                if command == "begin":
                    arg, _, valid = _argument(data, cursor, command)
                    if not valid or arg != b"document":
                        if activity() != "INACTIVE":
                            issues.append(TexIssue(name, match.start(), "OPAQUE_ENVIRONMENT", "Only document and lexical verbatim environments are interpreted"))
                            opaque = True
                            opaque_files.add(name)
                if command == "end":
                    arg, _, valid = _argument(data, cursor, command)
                    if valid and arg == b"document" and activity() == "ACTIVE":
                        ended = True
                if command not in _SAFE_SYNTAX and command.isalpha() and activity() != "INACTIVE":
                    issues.append(TexIssue(name, match.start(), "UNKNOWN_COMMAND", f"\\{command} is outside the static syntax profile"))
                    opaque = True
                    opaque_files.add(name)
                continue
            include_count += 1
            if include_count > max_includes:
                raise SourceError("Static analysis exceeds its include count limit")
            argument, end, balanced = _argument(data, cursor, command)
            cursor = max(cursor, end)
            current = activity()
            raw = original[match.end():end].decode("utf-8")
            target = None
            literal = balanced and bool(argument) and not any(char in argument for char in b"\\#{}\r\n\x00")
            if literal:
                try:
                    path = _relative_path(argument.decode("utf-8").strip())
                    candidate = _relative_path(str(PurePosixPath(working_directory) / path))
                    candidates = [candidate] if PurePosixPath(candidate).suffix else [candidate, candidate + ".tex"]
                    found = [item for item in candidates if item in canonical]
                    if len(found) == 1:
                        target = found[0]
                    elif len(found) > 1:
                        issues.append(TexIssue(name, match.start(), "AMBIGUOUS_INCLUDE", "Multiple supplied paths match the literal input"))
                    elif current != "INACTIVE":
                        issues.append(TexIssue(name, match.start(), "MISSING_INCLUDE", f"No supplied file for {candidate}"))
                except SourceError:
                    if current != "INACTIVE":
                        issues.append(TexIssue(name, match.start(), "UNSAFE_INCLUDE_PATH", "Literal include is not a safe relative path"))
            elif current != "INACTIVE":
                issues.append(TexIssue(name, match.start(), "UNRESOLVED_INCLUDE", "Include argument is missing, unbalanced, or contains macros"))
                opaque_files.add(name)
            if target is None and current != "INACTIVE":
                current = "UNKNOWN"
                opaque_files.add(name)
            edge = TexInclude(name, command, match.start(), end, raw, target, current)
            edges.append(edge)
        if frames:
            issues.append(TexIssue(name, len(original), "UNBALANCED_CONDITIONAL", "Conditional crosses EOF; cross-file conditionals are unsupported"))
            opaque_files.add(name)
            edges = [TexInclude(e.source, e.command, e.start_byte, e.end_byte, e.raw_argument, e.target, "UNKNOWN") for e in edges]
        local_edges[name] = edges

    # Fixed-point propagation handles repeated inclusions without recursion.
    levels = {name: 0 for name in canonical}  # INACTIVE < UNKNOWN < ACTIVE
    levels[main] = 2
    changed = True
    while changed:
        changed = False
        for name, edges in local_edges.items():
            for edge in edges:
                if edge.target and edge.activity != "INACTIVE":
                    level = min(levels[name], 2 if edge.activity == "ACTIVE" else 1)
                    if level > levels[edge.target]:
                        levels[edge.target] = level
                        changed = True
    reachable_opaque = any(levels[name] > 0 for name in opaque_files)
    for name, level in levels.items():
        if level and name not in local_edges:
            issues.append(TexIssue(name, 0, "UNPARSED_INCLUDED_FILE", "Included file is not a supported UTF-8 TeX source"))
            reachable_opaque = True
    if reachable_opaque:
        # An included file can change execution of later commands in its caller.
        # Without interpretation, no non-root file receives a semantic upgrade.
        levels = {name: 2 if name == main else 1 for name in levels}
    for name, edges in local_edges.items():
        for edge in edges:
            state = "INACTIVE" if levels[name] == 0 or edge.activity == "INACTIVE" else "UNKNOWN" if levels[name] == 1 or reachable_opaque else edge.activity
            includes.append(TexInclude(edge.source, edge.command, edge.start_byte, edge.end_byte, edge.raw_argument, edge.target, state))
    # Iterative DFS catches cycles in the reachable include graph, including
    # uncertain branches, without risking Python recursion on hostile sources.
    graph = {name: [edge.target for edge in edges if edge.target and edge.activity != "INACTIVE"] for name, edges in local_edges.items()}
    visited: set[str] = set()
    active: set[str] = set()
    stack = [(main, False)]
    while stack:
        name, leaving = stack.pop()
        if leaving:
            active.discard(name)
            continue
        if name in active:
            issues.append(TexIssue(name, 0, "INCLUDE_CYCLE", "Reachable include graph contains a cycle"))
            continue
        if name in visited:
            continue
        visited.add(name)
        active.add(name)
        stack.append((name, True))
        stack.extend((target, False) for target in reversed(graph.get(name, [])))
    return TexStructure(
        main, working_directory,
        tuple(fingerprint(name, data) for name, data in sorted(canonical.items())),
        tuple(includes), {name: ("INACTIVE", "UNKNOWN", "ACTIVE")[level] for name, level in levels.items()},
        tuple(issues),
    )
