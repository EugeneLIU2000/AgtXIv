#!/usr/bin/env python3
"""Collect and compare a portable deterministic pytest test identity.

The committed baseline is deliberately only the ``test_identity`` object emitted
by this tool.  Host runtime qualification and source commit information live in
the evaluation envelope instead.  Including the commit that contains a baseline
inside that same baseline would create an impossible self-reference.

This tool never writes or updates a baseline.  ``--candidate`` emits a candidate
and ``--check`` compares a read-only baseline with a fresh collection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import signal
import stat
import struct
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import tomllib
import unicodedata
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


REPO = Path(__file__).resolve().parents[1]
TEST_IDENTITY_SCHEMA = "agtxiv.pytest-test-identity/1.0.0"
EVALUATION_SCHEMA = "agtxiv.pytest-inventory-evaluation/2.0.0"
NODE_SET_DOMAIN = b"agtxiv.pytest-node-set/1.0.0\0"
NODE_ORDER_DOMAIN = b"agtxiv.pytest-node-order/1.0.0\0"
TEST_IDENTITY_DOMAIN = b"agtxiv.pytest-test-identity/1.0.0\0"
VALIDATOR_RELATIVE_PATH = "tools/validate_pytest_inventory.py"
ENVIRONMENT_QUALIFICATION_STATUS = "LOCKED_RUNTIME_MATCHED"
ENVIRONMENT_SECURITY_ROLE = (
    "REQUIRED_LOCK_QUALIFICATION_EXCLUDED_ONLY_FROM_CROSS_ENVIRONMENT_IDENTITY"
)
ENVIRONMENT_QUALIFICATION_SCOPE = (
    "VERSION_LOCK_AND_INSTALLED_DISTRIBUTION_MATCH_NOT_OS_OR_NETWORK_ISOLATION"
)
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)+(?:[-+._a-zA-Z0-9]*)?$")
DISTRIBUTION_NAME_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*(?![\s\S])"
DISTRIBUTION_NAME_RE = re.compile(DISTRIBUTION_NAME_PATTERN)
I_JSON_EXACT_INTEGER_MAX = (2**53) - 1
I_JSON_EXACT_INTEGER_MIN = -I_JSON_EXACT_INTEGER_MAX
I_JSON_EXACT_INTEGER_DIGITS = str(I_JSON_EXACT_INTEGER_MAX)
MAX_GIT_BLOB_BYTES = 512 * 1024 * 1024
MAX_SOURCE_MATERIALIZED_BYTES = 1024 * 1024 * 1024
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_MANIFEST_FILE_BYTES = 512 * 1024 * 1024
COLLECTION_TIMEOUT_SECONDS = 180
GIT_TIMEOUT_SECONDS = 60
MAX_PROCESS_STDOUT_BYTES = 8 * 1024 * 1024
MAX_PROCESS_STDERR_BYTES = 2 * 1024 * 1024
MAX_BASELINE_BYTES = 16 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_MANIFEST_ENTRIES = 200_000
PROCESS_OUTPUT_LIMIT_EXIT = 125
PROCESS_TIMEOUT_EXIT = 124
PROCESS_GROUP_LEAK_EXIT = 126
PROCESS_TERMINATION_GRACE_SECONDS = 3
WORKTREE_MANIFEST_EXCLUDED_DIRECTORY_NAMES = frozenset(
    {".git", ".venv", ".uv-cache", ".tools", ".lake"}
)

CONTROL_MARKERS = frozenset({"skip", "skipif", "xfail"})
EVIDENCE_SCOPE = "COLLECTION_IDENTITY_ONLY_NOT_TEST_EXECUTION_RESULT"
COLLECTION_CONTRACT: dict[str, Any] = {
    "config": "pyproject.toml",
    "rootdir": ".",
    "test_paths": ["tests"],
    "import_mode": "prepend",
    "plugin_autoload": False,
    "cacheprovider": False,
    "config_addopts_enabled": False,
    "keyword_selection": None,
    "marker_selection": None,
    "deselection_policy": "RECORDED_EXACT",
    "collection_skip_policy": "RECORDED_EXACT",
    "double_collection_required": True,
    "set_digest_scope": "FULL_COLLECTED_NODE_SET",
    "order_digest_scope": "SELECTED_EXECUTION_ORDER",
}


class InventoryError(Exception):
    """A stable, machine-classified inventory failure."""

    def __init__(
        self, code: str, message: str, *, details: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def record(self) -> dict[str, Any]:
        return _error_record(self.code, self.message, details=self.details)


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: bytes = b""
    stderr: bytes = b""
    output_limited: bool = False
    timed_out: bool = False
    process_group_leaked: bool = False
    cleanup_unconfirmed: bool = False


@dataclass(frozen=True)
class FileMetadata:
    device: int
    inode: int
    mode: int
    link_count: int
    user_id: int
    group_id: int
    byte_size: int
    modified_ns: int
    changed_ns: int


@dataclass(frozen=True)
class DirectoryIdentity:
    device: int
    inode: int
    mode: int
    user_id: int
    group_id: int


@dataclass(frozen=True)
class SafeFileSnapshot:
    absolute_path: str
    payload: bytes
    metadata: FileMetadata
    ancestor_metadata: tuple[DirectoryIdentity, ...]


@dataclass(frozen=True)
class FrozenBaseline:
    document: dict[str, Any]
    sha256: str
    file_snapshot: SafeFileSnapshot


@dataclass(frozen=True)
class GitTreeEntry:
    path: str
    mode: str
    object_type: str
    object_id: str
    byte_size: int


@dataclass(frozen=True)
class GitBlob:
    object_id: str
    payload: bytes


@dataclass(frozen=True)
class PreparedGitSource:
    commit: str
    entries: tuple[GitTreeEntry, ...]
    blobs: tuple[GitBlob, ...]


@dataclass(frozen=True)
class GuardedCollection:
    collection: dict[str, Any]
    input_bindings: dict[str, dict[str, Any]]
    runtime: dict[str, Any]
    manifest_sha256: str


@dataclass(frozen=True)
class EvaluationOptions:
    operation: str
    baseline: Path | None = None
    source_ref: str | None = None


ProcessRunner = Callable[
    [Sequence[str], Path, Mapping[str, str], int], ProcessResult
]
CollectionRunner = Callable[[Path], dict[str, Any]]
RuntimeProvider = Callable[[Path, ProcessRunner], dict[str, Any]]
GitBlobRunner = Callable[[Path, str, Mapping[str, str], int, int], ProcessResult]


def _default_process_runner(
    command: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    timeout: int,
) -> ProcessResult:
    return _run_streaming_process(
        command,
        cwd,
        environment,
        timeout,
        max_stdout_bytes=MAX_PROCESS_STDOUT_BYTES,
        max_stderr_bytes=MAX_PROCESS_STDERR_BYTES,
    )


def _default_git_blob_runner(
    repo: Path,
    object_id: str,
    environment: Mapping[str, str],
    timeout: int,
    max_bytes: int,
) -> ProcessResult:
    return _run_streaming_process(
        ("git", *_git_command_prefix(), "cat-file", "blob", object_id),
        repo,
        environment,
        timeout,
        max_stdout_bytes=max_bytes,
        max_stderr_bytes=MAX_PROCESS_STDERR_BYTES,
    )


def _original_process_group_exists(process_group_id: int) -> bool:
    if os.name != "posix":
        return False
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _signal_original_process_group(
    process_group_id: int, signal_number: int
) -> bool:
    """Signal only the process group created for this one subprocess invocation."""
    try:
        os.killpg(process_group_id, signal_number)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return True


def _wait_for_original_process_group_exit(
    process_group_id: int, timeout: float
) -> bool:
    deadline = time.monotonic() + max(0.0, timeout)
    while _original_process_group_exists(process_group_id):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(0.01, remaining))
    return True


def _clean_leaked_process_group(process_group_id: int) -> bool:
    _signal_original_process_group(process_group_id, signal.SIGTERM)
    if _wait_for_original_process_group_exit(
        process_group_id, PROCESS_TERMINATION_GRACE_SECONDS
    ):
        return True
    _signal_original_process_group(process_group_id, signal.SIGKILL)
    return _wait_for_original_process_group_exit(
        process_group_id, PROCESS_TERMINATION_GRACE_SECONDS
    )


def _wait_for_process_exit(
    process: subprocess.Popen[bytes], timeout: float
) -> bool:
    try:
        process.wait(timeout=max(0.0, timeout))
    except (OSError, subprocess.TimeoutExpired):
        return False
    return True


def _terminate_process(
    process: subprocess.Popen[bytes], process_group_id: int | None
) -> bool:
    if os.name == "posix":
        assert process_group_id is not None
        _signal_original_process_group(process_group_id, signal.SIGTERM)
    elif process.poll() is None:
        try:
            process.terminate()
        except OSError:
            pass
    if _wait_for_process_exit(process, PROCESS_TERMINATION_GRACE_SECONDS):
        return True
    try:
        if os.name == "posix":
            assert process_group_id is not None
            _signal_original_process_group(process_group_id, signal.SIGKILL)
        else:
            process.kill()
    except OSError:
        pass
    return _wait_for_process_exit(process, PROCESS_TERMINATION_GRACE_SECONDS)


def _run_streaming_process(
    command: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    timeout: int,
    *,
    max_stdout_bytes: int,
    max_stderr_bytes: int,
) -> ProcessResult:
    try:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=dict(environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name == "posix",
        )
    except OSError as exc:
        return ProcessResult(127, b"", str(exc).encode("utf-8", errors="replace"))
    process_group_id = process.pid if os.name == "posix" else None

    stdout = bytearray()
    stderr = bytearray()
    output_limited = threading.Event()

    def drain(stream: Any, destination: bytearray, limit: int) -> None:
        while chunk := stream.read(64 * 1024):
            remaining = max(0, limit - len(destination))
            destination.extend(chunk[:remaining])
            if len(chunk) > remaining:
                output_limited.set()

    assert process.stdout is not None
    assert process.stderr is not None
    stdout_thread = threading.Thread(
        target=drain, args=(process.stdout, stdout, max_stdout_bytes), daemon=True
    )
    stderr_thread = threading.Thread(
        target=drain, args=(process.stderr, stderr, max_stderr_bytes), daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    termination_confirmed = True
    while process.poll() is None:
        if output_limited.is_set():
            termination_confirmed = _terminate_process(process, process_group_id)
            break
        if time.monotonic() >= deadline:
            timed_out = True
            termination_confirmed = _terminate_process(process, process_group_id)
            break
        time.sleep(0.01)
    process_group_leaked = False
    process_group_cleanup_confirmed = True
    if (
        process_group_id is not None
        and _original_process_group_exists(process_group_id)
    ):
        process_group_leaked = True
        process_group_cleanup_confirmed = _clean_leaked_process_group(
            process_group_id
        )
    cleanup_unconfirmed = (
        not termination_confirmed or not process_group_cleanup_confirmed
    )
    stdout_thread.join(timeout=PROCESS_TERMINATION_GRACE_SECONDS)
    stderr_thread.join(timeout=PROCESS_TERMINATION_GRACE_SECONDS)
    if cleanup_unconfirmed:
        return ProcessResult(
            PROCESS_GROUP_LEAK_EXIT,
            bytes(stdout),
            bytes(stderr),
            timed_out=timed_out,
            output_limited=output_limited.is_set(),
            process_group_leaked=process_group_leaked,
            cleanup_unconfirmed=True,
        )
    if timed_out:
        return ProcessResult(
            PROCESS_TIMEOUT_EXIT,
            bytes(stdout),
            bytes(stderr),
            output_limited=output_limited.is_set(),
            timed_out=True,
            process_group_leaked=process_group_leaked,
            cleanup_unconfirmed=False,
        )
    if output_limited.is_set():
        return ProcessResult(
            PROCESS_OUTPUT_LIMIT_EXIT,
            bytes(stdout),
            bytes(stderr),
            output_limited=True,
            process_group_leaked=process_group_leaked,
            cleanup_unconfirmed=False,
        )
    if process_group_leaked:
        return ProcessResult(
            PROCESS_GROUP_LEAK_EXIT,
            bytes(stdout),
            bytes(stderr),
            process_group_leaked=True,
            cleanup_unconfirmed=False,
        )
    return ProcessResult(process.returncode, bytes(stdout), bytes(stderr))


def _has_lone_surrogate(value: str) -> bool:
    return any(0xD800 <= ord(character) <= 0xDFFF for character in value)


def _validate_unicode_scalars(value: Any, *, label: str) -> None:
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            if _has_lone_surrogate(current):
                raise InventoryError(
                    "INVALID_JSON", f"{label} contains a non-Unicode scalar"
                )
        elif isinstance(current, dict):
            stack.extend(current.keys())
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)


def _machine_safe_text(value: str) -> str:
    """Return ASCII text while preserving non-ASCII input only as an escape."""
    try:
        value.encode("ascii")
    except UnicodeEncodeError:
        return json.dumps(value, ensure_ascii=True)[1:-1]
    return value


def _machine_safe_mapping_key(value: str) -> str:
    # Escaping every key keeps a literal ``\\u1234`` distinct from U+1234.
    return json.dumps(value, ensure_ascii=True)[1:-1]


def _machine_safe_error_value(
    value: Any, *, depth: int = 0, ancestors: frozenset[int] = frozenset()
) -> Any:
    if depth > MAX_JSON_DEPTH:
        return "<redacted-depth-limit>"
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "<redacted-non-finite-number>"
    if isinstance(value, str):
        return _machine_safe_text(value)
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in ancestors:
            return "<redacted-cycle>"
        nested_ancestors = ancestors | {identity}
        safe: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if isinstance(key, str):
                safe_key = _machine_safe_mapping_key(key)
            else:
                type_name = (
                    f"{type(key).__module__}.{type(key).__qualname__}"
                )
                safe_key = f"<non-string-key-{index}:{_machine_safe_text(type_name)}>"
            if safe_key in safe:
                safe_key = f"{safe_key}<collision-{index}>"
            safe[safe_key] = _machine_safe_error_value(
                item, depth=depth + 1, ancestors=nested_ancestors
            )
        return safe
    if isinstance(value, (list, tuple)):
        identity = id(value)
        if identity in ancestors:
            return "<redacted-cycle>"
        nested_ancestors = ancestors | {identity}
        return [
            _machine_safe_error_value(
                item, depth=depth + 1, ancestors=nested_ancestors
            )
            for item in value
        ]
    type_name = f"{type(value).__module__}.{type(value).__qualname__}"
    return {"redacted_non_json_type": _machine_safe_text(type_name)}


def _error_record(
    code: str, message: str, *, details: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "code": _machine_safe_text(str(code)),
        "message": _machine_safe_text(str(message)),
    }
    if details:
        record["details"] = _machine_safe_error_value(details)
    return record


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return encoded.encode("utf-8")
    except (TypeError, UnicodeEncodeError, ValueError) as exc:
        raise InventoryError(
            "NON_CANONICAL_JSON", "value cannot be encoded as canonical JSON"
        ) from exc


def _machine_json_bytes(
    value: Any, *, fallback: Mapping[str, Any]
) -> tuple[bytes, bool]:
    """Encode once, replacing any malformed result with one fixed-safe record."""
    try:
        return _canonical_json_bytes(value), False
    except Exception:
        # The caller supplies only static ASCII JSON primitives here.  Keeping this
        # fallback independent of the failed value prevents repr()/Unicode leakage.
        return _canonical_json_bytes(dict(fallback)), True


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InventoryError(
                "DUPLICATE_JSON_KEY", "JSON object contains a duplicate key"
            )
        result[key] = value
    return result


def _reject_non_json_constant(_: str) -> Any:
    raise InventoryError(
        "INVALID_JSON", "JSON contains a non-standard numeric constant"
    )


def _parse_finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise InventoryError(
            "INVALID_JSON", "JSON number exceeds the finite numeric range"
        )
    return parsed


def _parse_i_json_integer(value: str) -> int:
    digits = value[1:] if value.startswith("-") else value
    if len(digits) > len(I_JSON_EXACT_INTEGER_DIGITS) or (
        len(digits) == len(I_JSON_EXACT_INTEGER_DIGITS)
        and digits > I_JSON_EXACT_INTEGER_DIGITS
    ):
        raise InventoryError(
            "INVALID_JSON", "JSON integer is outside the I-JSON exact range"
        )
    # Conversion happens only after the lexical length/value bound, so behavior
    # never depends on CPython's process-global integer digit limit.
    parsed = int(value)
    if not I_JSON_EXACT_INTEGER_MIN <= parsed <= I_JSON_EXACT_INTEGER_MAX:
        raise InventoryError(
            "INVALID_JSON", "JSON integer is outside the I-JSON exact range"
        )
    return parsed


def _strict_json_loads(payload: str, *, label: str) -> Any:
    try:
        result = json.loads(
            payload,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_non_json_constant,
            parse_float=_parse_finite_json_float,
            parse_int=_parse_i_json_integer,
        )
        _validate_unicode_scalars(result, label=label)
        return result
    except InventoryError:
        raise
    except json.JSONDecodeError as exc:
        raise InventoryError(
            "INVALID_JSON", f"{label} is not valid JSON"
        ) from exc
    except ValueError as exc:
        raise InventoryError(
            "INVALID_JSON", f"{label} contains an unsupported JSON number"
        ) from exc
    except RecursionError as exc:
        raise InventoryError(
            "JSON_TOO_DEEP", f"{label} exceeds the JSON nesting limit"
        ) from exc


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_metadata(value: os.stat_result) -> FileMetadata:
    return FileMetadata(
        device=value.st_dev,
        inode=value.st_ino,
        mode=value.st_mode,
        link_count=value.st_nlink,
        user_id=value.st_uid,
        group_id=value.st_gid,
        byte_size=value.st_size,
        modified_ns=value.st_mtime_ns,
        changed_ns=value.st_ctime_ns,
    )


def _directory_identity(value: os.stat_result) -> DirectoryIdentity:
    return DirectoryIdentity(
        device=value.st_dev,
        inode=value.st_ino,
        mode=value.st_mode,
        user_id=value.st_uid,
        group_id=value.st_gid,
    )


def _safe_absolute_path(path: Path, *, unsafe_code: str, label: str) -> Path:
    if os.name != "posix" or not all(
        hasattr(os, name)
        for name in ("O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    ):
        raise InventoryError(
            "SAFE_FILE_READER_UNAVAILABLE",
            "dirfd/openat file safety is unavailable on this platform",
        )
    try:
        absolute = Path(os.path.abspath(os.fspath(path)))
    except (OSError, TypeError, ValueError) as exc:
        raise InventoryError(unsafe_code, f"{label} path is invalid") from exc
    if not absolute.is_absolute() or len(absolute.parts) < 2:
        raise InventoryError(unsafe_code, f"{label} path has no file component")
    return absolute


def _open_ancestor_chain(
    absolute: Path, *, unsafe_code: str, label: str
) -> tuple[list[int], tuple[DirectoryIdentity, ...]]:
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | os.O_NONBLOCK
        | os.O_CLOEXEC
    )
    descriptors: list[int] = []
    metadata_records: list[DirectoryIdentity] = []
    try:
        root_fd = os.open(os.sep, directory_flags)
        descriptors.append(root_fd)
        metadata_records.append(_directory_identity(os.fstat(root_fd)))
        for component in absolute.parts[1:-1]:
            if component in {"", ".", ".."}:
                raise InventoryError(
                    unsafe_code, f"{label} path has an unsafe component"
                )
            descriptor = os.open(component, directory_flags, dir_fd=descriptors[-1])
            descriptors.append(descriptor)
            metadata_records.append(_directory_identity(os.fstat(descriptor)))
    except InventoryError:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise
    except OSError as exc:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise InventoryError(
            unsafe_code,
            f"{label} ancestor cannot be opened without following links",
            details={"errno": exc.errno},
        ) from exc
    return descriptors, tuple(metadata_records)


def _safe_read_regular_file(
    path: Path,
    *,
    max_bytes: int,
    unsafe_code: str,
    too_large_code: str,
    label: str,
) -> SafeFileSnapshot:
    absolute = _safe_absolute_path(path, unsafe_code=unsafe_code, label=label)
    descriptors, ancestor_metadata = _open_ancestor_chain(
        absolute, unsafe_code=unsafe_code, label=label
    )
    file_descriptor: int | None = None
    try:
        parent_fd = descriptors[-1]
        file_name = absolute.parts[-1]
        try:
            path_before = os.stat(file_name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as exc:
            raise InventoryError(
                unsafe_code,
                f"{label} cannot be inspected safely",
                details={"errno": exc.errno},
            ) from exc
        before_metadata = _file_metadata(path_before)
        if not stat.S_ISREG(path_before.st_mode):
            raise InventoryError(unsafe_code, f"{label} must be a regular file")
        if path_before.st_size < 0 or path_before.st_size > max_bytes:
            raise InventoryError(too_large_code, f"{label} exceeds the byte limit")
        file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        try:
            file_descriptor = os.open(file_name, file_flags, dir_fd=parent_fd)
        except OSError as exc:
            raise InventoryError(
                unsafe_code,
                f"{label} cannot be opened safely",
                details={"errno": exc.errno},
            ) from exc
        opened_metadata = _file_metadata(os.fstat(file_descriptor))
        if opened_metadata != before_metadata or not stat.S_ISREG(opened_metadata.mode):
            raise InventoryError(
                unsafe_code, f"{label} changed between inspection and open"
            )
        payload = bytearray()
        while True:
            remaining = max_bytes + 1 - len(payload)
            if remaining <= 0:
                raise InventoryError(too_large_code, f"{label} exceeds the byte limit")
            try:
                chunk = os.read(file_descriptor, min(1024 * 1024, remaining))
            except BlockingIOError as exc:
                raise InventoryError(
                    unsafe_code, f"{label} did not behave as a regular file"
                ) from exc
            if not chunk:
                break
            payload.extend(chunk)
        after_fd_metadata = _file_metadata(os.fstat(file_descriptor))
        try:
            path_after = os.stat(file_name, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as exc:
            raise InventoryError(
                unsafe_code, f"{label} disappeared during the stable read"
            ) from exc
        after_path_metadata = _file_metadata(path_after)
        current_ancestors = tuple(
            _directory_identity(os.fstat(fd)) for fd in descriptors
        )
        if not (
            before_metadata
            == opened_metadata
            == after_fd_metadata
            == after_path_metadata
            and ancestor_metadata == current_ancestors
            and len(payload) == opened_metadata.byte_size
        ):
            raise InventoryError(unsafe_code, f"{label} changed during the stable read")
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        for descriptor in reversed(descriptors):
            os.close(descriptor)
    reopened_descriptors, reopened_ancestors = _open_ancestor_chain(
        absolute, unsafe_code=unsafe_code, label=label
    )
    try:
        try:
            reopened_file_metadata = _file_metadata(
                os.stat(
                    absolute.parts[-1],
                    dir_fd=reopened_descriptors[-1],
                    follow_symlinks=False,
                )
            )
        except OSError as exc:
            raise InventoryError(
                unsafe_code, f"{label} changed after the stable read"
            ) from exc
    finally:
        for descriptor in reversed(reopened_descriptors):
            os.close(descriptor)
    if (
        reopened_ancestors != ancestor_metadata
        or reopened_file_metadata != opened_metadata
    ):
        raise InventoryError(unsafe_code, f"{label} path changed during the stable read")
    return SafeFileSnapshot(
        absolute_path=os.fspath(absolute),
        payload=bytes(payload),
        metadata=opened_metadata,
        ancestor_metadata=ancestor_metadata,
    )


def _sha256_file(path: Path) -> str:
    snapshot = _safe_read_regular_file(
        path,
        max_bytes=MAX_MANIFEST_FILE_BYTES,
        unsafe_code="UNSAFE_FILE_READ",
        too_large_code="FILE_TOO_LARGE",
        label="file",
    )
    return _sha256_bytes(snapshot.payload)


def _length_prefixed_digest(domain: bytes, values: Sequence[str]) -> str:
    digest = hashlib.sha256(domain)
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(struct.pack(">Q", len(encoded)))
        digest.update(encoded)
    return digest.hexdigest()


def _test_identity_digest(test_identity: Mapping[str, Any]) -> str:
    return _sha256_bytes(
        TEST_IDENTITY_DOMAIN + _canonical_json_bytes(test_identity)
    )


def normalize_node_id(raw: object) -> str:
    """Validate a pytest node ID without silently changing its identity."""
    if not isinstance(raw, str) or not raw:
        raise InventoryError("INVALID_NODE_ID", "pytest node ID must be a non-empty string")
    if any(character in raw for character in ("\x00", "\n", "\r")):
        raise InventoryError(
            "INVALID_NODE_ID", "pytest node ID contains a forbidden character"
        )
    if unicodedata.normalize("NFC", raw) != raw:
        raise InventoryError(
            "NON_NFC_NODE_ID", "pytest node ID must already use Unicode NFC"
        )
    components = raw.split("::")
    path_text = components[0]
    if (
        not path_text
        or path_text.startswith("/")
        or "//" in path_text
        or "\\" in path_text
        or ":" in path_text
    ):
        raise InventoryError(
            "INVALID_NODE_PATH", "pytest node path must be repository-relative POSIX"
        )
    path = PurePosixPath(path_text)
    if (
        path.is_absolute()
        or len(path.parts) < 2
        or path.parts[0] != "tests"
        or any(part in {"", ".", ".."} for part in path_text.split("/"))
    ):
        raise InventoryError(
            "INVALID_NODE_PATH", "pytest node path must be below tests/"
        )
    if any(component == "" for component in components[1:]):
        raise InventoryError(
            "INVALID_NODE_ID", "pytest node ID contains an empty hierarchy component"
        )
    return raw


def _validated_unique_node_ids(values: object, *, label: str) -> list[str]:
    if not isinstance(values, list):
        raise InventoryError("INVALID_COLLECTION_PAYLOAD", f"{label} must be an array")
    normalized = [normalize_node_id(value) for value in values]
    counts = Counter(normalized)
    duplicates = sorted(
        {value for value, count in counts.items() if count > 1},
        key=lambda value: value.encode("utf-8"),
    )
    if duplicates:
        raise InventoryError(
            "DUPLICATE_NODE_ID",
            f"{label} contains duplicate pytest node IDs",
            details={"node_ids": duplicates},
        )
    return normalized


def _stable_marker_value(value: Any) -> Any:
    if value is None or type(value) is bool or isinstance(value, str):
        return value
    if type(value) is int:
        if I_JSON_EXACT_INTEGER_MIN <= value <= I_JSON_EXACT_INTEGER_MAX:
            return value
        raise InventoryError(
            "UNSTABLE_MARKER_VALUE",
            "marker integer is outside the I-JSON exact range",
        )
    if isinstance(value, (list, tuple)):
        return [_stable_marker_value(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise InventoryError(
                "UNSTABLE_MARKER_VALUE", "marker mappings require string keys"
            )
        return {
            key: _stable_marker_value(value[key])
            for key in sorted(value, key=lambda item: item.encode("utf-8"))
        }
    raise InventoryError(
        "UNSTABLE_MARKER_VALUE",
        "skip/skipif/xfail marker values must be stable JSON values",
        details={"type": f"{type(value).__module__}.{type(value).__qualname__}"},
    )


def _collection_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONINSPECT",
    ):
        environment.pop(key, None)
    environment.update(
        {
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTHONSAFEPATH": "1",
            "PYTHONUTF8": "1",
            "TZ": "UTC",
            "LC_ALL": "C",
            "LANG": "C",
        }
    )
    return environment


def _git_environment() -> dict[str, str]:
    environment = _collection_environment()
    for key in tuple(environment):
        if key.startswith("GIT_") and key not in {"GIT_CONFIG_NOSYSTEM"}:
            environment.pop(key, None)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _git_command_prefix() -> tuple[str, ...]:
    return (
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "core.fsmonitor=false",
    )


def _normalize_report_reason(value: Any, root: Path) -> str:
    if isinstance(value, tuple) and len(value) >= 3:
        text = str(value[2])
    else:
        text = str(value)
    return text.replace(str(root), "<repo>").replace("\r\n", "\n")


def _collect_worker(root: Path) -> dict[str, Any]:
    """Run inside a fresh isolated interpreter; import pytest only after env setup."""
    os.environ.clear()
    os.environ.update(_collection_environment())
    worker_runtime = {
        "dont_write_bytecode": bool(sys.flags.dont_write_bytecode),
        "hash_seed": os.environ.get("PYTHONHASHSEED"),
        "no_user_site": os.environ.get("PYTHONNOUSERSITE"),
        "safe_path": bool(sys.flags.safe_path),
        "utf8_mode": bool(sys.flags.utf8_mode),
    }
    expected_worker_runtime = {
        "dont_write_bytecode": True,
        "hash_seed": "0",
        "no_user_site": "1",
        "safe_path": True,
        "utf8_mode": True,
    }
    if worker_runtime != expected_worker_runtime:
        return {
            "worker_error": {
                "code": "WORKER_RUNTIME_MISMATCH",
                "message": "pytest worker flags do not match the collection contract",
            },
            "worker_runtime": worker_runtime,
        }
    try:
        import pytest
    except Exception as exc:  # pragma: no cover - exercised through parent errors
        return {
            "worker_error": {
                "code": "PYTEST_IMPORT_FAILED",
                "message": f"pytest import failed: {type(exc).__name__}",
            }
        }

    class CollectionPlugin:
        def __init__(self) -> None:
            self.node_ids: list[str] = []
            self.selected_node_ids: list[str] = []
            self.marker_declarations: list[dict[str, Any]] = []
            self.collection_skips: list[dict[str, str]] = []
            self.deselected_node_ids: list[str] = []
            self.collection_errors: list[dict[str, str]] = []
            self.serialization_error: InventoryError | None = None

        def pytest_deselected(self, items: Sequence[Any]) -> None:
            self.deselected_node_ids.extend(item.nodeid for item in items)

        @pytest.hookimpl(hookwrapper=True, tryfirst=True)
        def pytest_collection_modifyitems(
            self, session: Any, config: Any, items: list[Any]
        ) -> Any:
            original_items = list(items)
            yield
            self.node_ids = [item.nodeid for item in original_items]
            self._record_marker_declarations(original_items)

        def pytest_collectreport(self, report: Any) -> None:
            if report.failed:
                self.collection_errors.append(
                    {
                        "node_id": report.nodeid or "<collection-root>",
                        "reason": _normalize_report_reason(report.longrepr, root),
                    }
                )
            elif report.skipped:
                self.collection_skips.append(
                    {
                        "node_id": report.nodeid,
                        "reason": _normalize_report_reason(report.longrepr, root),
                    }
                )

        def pytest_collection_finish(self, session: Any) -> None:
            self.selected_node_ids = [item.nodeid for item in session.items]
            if not self.node_ids:
                self.node_ids = list(self.selected_node_ids)
                self._record_marker_declarations(list(session.items))

        def _record_marker_declarations(self, items: Sequence[Any]) -> None:
            declarations: list[dict[str, Any]] = []
            try:
                for item in items:
                    markers: list[dict[str, Any]] = []
                    for mark in item.iter_markers():
                        if mark.name not in CONTROL_MARKERS:
                            continue
                        marker = {
                            "name": mark.name,
                            "args": [_stable_marker_value(value) for value in mark.args],
                            "kwargs": {
                                key: _stable_marker_value(mark.kwargs[key])
                                for key in sorted(
                                    mark.kwargs, key=lambda value: value.encode("utf-8")
                                )
                            },
                        }
                        markers.append(marker)
                    if markers:
                        markers.sort(key=_canonical_json_bytes)
                        declarations.append({"node_id": item.nodeid, "markers": markers})
            except InventoryError as exc:
                self.serialization_error = exc
            self.marker_declarations = declarations

    plugin = CollectionPlugin()
    arguments = [
        "-c",
        str(root / "pyproject.toml"),
        f"--rootdir={root}",
        f"--confcutdir={root}",
        "--import-mode=prepend",
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
        "-p",
        "no:terminal",
        "--collect-only",
        str(root / "tests"),
    ]
    try:
        exit_code = int(pytest.main(arguments, plugins=[plugin]))
    except Exception as exc:  # pragma: no cover - defensive subprocess boundary
        return {
            "worker_error": {
                "code": "PYTEST_COLLECTION_CRASH",
                "message": f"pytest collection crashed: {type(exc).__name__}",
            }
        }
    payload: dict[str, Any] = {
        "pytest_exit_code": exit_code,
        "worker_runtime": worker_runtime,
        "node_ids": plugin.node_ids,
        "selected_node_ids": plugin.selected_node_ids,
        "marker_declarations": plugin.marker_declarations,
        "collection_skips": plugin.collection_skips,
        "deselected_node_ids": plugin.deselected_node_ids,
        "collection_errors": plugin.collection_errors,
    }
    if plugin.serialization_error is not None:
        payload["worker_error"] = plugin.serialization_error.record()
    return payload


def _collect_worker_cli(root_text: str) -> int:
    root = Path(root_text).resolve()
    payload = _collect_worker(root)
    fallback = {
        "worker_error": {
            "code": "COLLECTION_WORKER_ENCODING_FAILED",
            "message": "pytest collection worker produced non-canonical JSON",
        }
    }
    encoded, used_fallback = _machine_json_bytes(payload, fallback=fallback)
    sys.stdout.buffer.write(encoded + b"\n")
    return 1 if used_fallback else 0


def _default_collection_runner(
    root: Path, process_runner: ProcessRunner = _default_process_runner
) -> dict[str, Any]:
    worker_validator = root / VALIDATOR_RELATIVE_PATH
    command = (
        sys.executable,
        "-B",
        "-P",
        "-X",
        "utf8",
        str(worker_validator),
        "--_collect-worker",
        str(root),
    )
    result = process_runner(
        command,
        root,
        _collection_environment(),
        COLLECTION_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise InventoryError(
            "COLLECTION_WORKER_FAILED",
            "pytest collection worker did not complete",
            details={"exit_code": result.returncode},
        )
    try:
        worker_output = result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InventoryError(
            "INVALID_COLLECTION_PAYLOAD", "collection worker output is not UTF-8"
        ) from exc
    payload = _strict_json_loads(worker_output, label="collection worker output")
    if not isinstance(payload, dict):
        raise InventoryError(
            "INVALID_COLLECTION_PAYLOAD", "collection worker output must be an object"
        )
    return payload


def _collect_twice(root: Path, collection_runner: CollectionRunner) -> dict[str, Any]:
    first = collection_runner(root)
    second = collection_runner(root)
    if _canonical_json_bytes(first) != _canonical_json_bytes(second):
        raise InventoryError(
            "NONDETERMINISTIC_COLLECTION",
            "two fresh pytest collections produced different results",
        )
    return first


def _required_input_snapshot(root: Path, relative: str) -> SafeFileSnapshot:
    root_absolute = root.resolve(strict=True)
    path_absolute = root_absolute / relative
    if not path_absolute.is_relative_to(root_absolute):
        raise InventoryError(
            "UNSAFE_INPUT_BINDING", f"input binding escapes source root: {relative}"
        )
    return _safe_read_regular_file(
        path_absolute,
        max_bytes=MAX_INPUT_BYTES,
        unsafe_code="UNSAFE_INPUT_BINDING",
        too_large_code="INPUT_BINDING_TOO_LARGE",
        label=f"input binding {relative}",
    )


def _input_bindings(root: Path) -> dict[str, dict[str, Any]]:
    bindings: dict[str, dict[str, Any]] = {}
    for relative in (".python-version", "pyproject.toml", "uv.lock"):
        snapshot = _required_input_snapshot(root, relative)
        bindings[relative] = {
            "byte_size": len(snapshot.payload),
            "sha256": _sha256_bytes(snapshot.payload),
        }
    return bindings


def _filesystem_manifest(
    root: Path, *, excluded_directory_names: frozenset[str] = frozenset()
) -> tuple[dict[str, Any], ...]:
    root_resolved = root.resolve(strict=True)
    records: list[dict[str, Any]] = []
    paths: list[str] = []
    total_file_bytes = 0

    def visit(directory: Path, relative_parent: PurePosixPath) -> None:
        nonlocal total_file_bytes
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name.encode())
        except OSError as exc:
            raise InventoryError(
                "SOURCE_MANIFEST_UNREADABLE", "source tree cannot be enumerated"
            ) from exc
        for entry in entries:
            if (
                not relative_parent.parts
                and entry.name in excluded_directory_names
                and entry.is_dir(follow_symlinks=False)
            ):
                continue
            relative = relative_parent / entry.name
            relative_text = _validated_repository_path(
                relative.as_posix(), label="filesystem manifest"
            )
            target = Path(entry.path)
            target_resolved = target.resolve(strict=False)
            if not target_resolved.is_relative_to(root_resolved):
                raise InventoryError(
                    "SOURCE_MANIFEST_ESCAPE", "source tree entry escapes the source root"
                )
            entry_stat = target.lstat()
            mode = f"{stat.S_IMODE(entry_stat.st_mode):04o}"
            if stat.S_ISDIR(entry_stat.st_mode):
                record = {"path": relative_text, "kind": "directory", "mode": mode}
                records.append(record)
                paths.append(relative_text)
                visit(target, relative)
            elif stat.S_ISREG(entry_stat.st_mode):
                snapshot = _safe_read_regular_file(
                    target,
                    max_bytes=MAX_MANIFEST_FILE_BYTES,
                    unsafe_code="SOURCE_MANIFEST_UNREADABLE",
                    too_large_code="SOURCE_MANIFEST_TOO_LARGE",
                    label=f"source manifest file {relative_text}",
                )
                if snapshot.metadata != _file_metadata(entry_stat):
                    raise InventoryError(
                        "SOURCE_TREE_MUTATED_DURING_MANIFEST",
                        "source file changed while its manifest was read",
                        details={"path": relative_text},
                    )
                total_file_bytes += len(snapshot.payload)
                if total_file_bytes > MAX_SOURCE_MATERIALIZED_BYTES:
                    raise InventoryError(
                        "SOURCE_MANIFEST_TOO_LARGE",
                        "source manifest file bytes exceed the total limit",
                    )
                record = {
                    "path": relative_text,
                    "kind": "file",
                    "mode": f"{stat.S_IMODE(snapshot.metadata.mode):04o}",
                    "byte_size": len(snapshot.payload),
                    "sha256": _sha256_bytes(snapshot.payload),
                }
                records.append(record)
                paths.append(relative_text)
            elif stat.S_ISLNK(entry_stat.st_mode):
                record = {
                    "path": relative_text,
                    "kind": "symlink",
                    "mode": mode,
                    "target": os.readlink(target),
                }
                records.append(record)
                paths.append(relative_text)
            else:
                raise InventoryError(
                    "UNSUPPORTED_SOURCE_ENTRY",
                    "source manifest supports only files, directories, and symlinks",
                    details={"path": relative_text},
                )
            if len(records) > MAX_MANIFEST_ENTRIES:
                raise InventoryError(
                    "SOURCE_MANIFEST_TOO_LARGE", "source manifest has too many entries"
                )

    visit(root_resolved, PurePosixPath())
    _reject_component_collisions(paths, code="SOURCE_PATH_COLLISION")
    return tuple(records)


def _filesystem_manifest_digest(records: Sequence[Mapping[str, Any]]) -> str:
    return _sha256_bytes(
        b"agtxiv.source-tree-manifest/1.0.0\0" + _canonical_json_bytes(list(records))
    )


def _manifest_difference(
    before: Sequence[Mapping[str, Any]], after: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    before_by_path = {record["path"]: record for record in before}
    after_by_path = {record["path"]: record for record in after}
    changed = sorted(
        path
        for path in set(before_by_path) & set(after_by_path)
        if before_by_path[path] != after_by_path[path]
    )
    return {
        "added": sorted(set(after_by_path) - set(before_by_path))[:100],
        "removed": sorted(set(before_by_path) - set(after_by_path))[:100],
        "changed": changed[:100],
    }


def _guarded_collection(
    root: Path,
    *,
    collection_runner: CollectionRunner | None,
    process_runner: ProcessRunner,
    runtime_provider: RuntimeProvider,
    excluded_directory_names: frozenset[str] = frozenset(),
) -> GuardedCollection:
    input_bindings = _input_bindings(root)
    before = _filesystem_manifest(
        root, excluded_directory_names=excluded_directory_names
    )
    guarded_error: Exception | None = None
    runtime: dict[str, Any] | None = None
    collection: dict[str, Any] | None = None
    try:
        runtime = runtime_provider(root, process_runner)
        collection = (
            _default_collection_runner(root, process_runner)
            if collection_runner is None
            else collection_runner(root)
        )
    except Exception as exc:  # mutation evidence must survive guarded-operation failure
        guarded_error = exc
    after = _filesystem_manifest(root, excluded_directory_names=excluded_directory_names)
    if before != after:
        raise InventoryError(
            "SOURCE_TREE_MUTATED_DURING_COLLECTION",
            "pytest collection changed the source snapshot",
            details=_manifest_difference(before, after),
        ) from guarded_error
    if guarded_error is not None:
        raise guarded_error
    assert runtime is not None
    assert collection is not None
    return GuardedCollection(
        collection=collection,
        input_bindings=input_bindings,
        runtime=runtime,
        manifest_sha256=_filesystem_manifest_digest(before),
    )


def _normalized_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _locked_distribution_versions(lock: Mapping[str, Any]) -> dict[str, str]:
    packages = lock.get("package")
    if not isinstance(packages, list):
        raise InventoryError("INVALID_UV_LOCK", "uv.lock package inventory is missing")
    versions: dict[str, str] = {}
    for package in packages:
        if not isinstance(package, dict):
            raise InventoryError("INVALID_UV_LOCK", "uv.lock package entry is invalid")
        name = package.get("name")
        version = package.get("version")
        if not isinstance(name, str) or not name or not isinstance(version, str):
            raise InventoryError("INVALID_UV_LOCK", "uv.lock package pin is invalid")
        normalized = _normalized_distribution_name(name)
        if DISTRIBUTION_NAME_RE.fullmatch(normalized) is None:
            raise InventoryError(
                "INVALID_UV_LOCK", "uv.lock package name is not canonical"
            )
        previous = versions.get(normalized)
        if previous is not None and previous != version:
            raise InventoryError(
                "INVALID_UV_LOCK",
                "uv.lock contains multiple versions for one normalized package name",
                details={"name": normalized},
            )
        versions[normalized] = version
    return versions


def _locked_package_version(lock: Mapping[str, Any], package_name: str) -> str:
    versions = _locked_distribution_versions(lock)
    normalized = _normalized_distribution_name(package_name)
    if normalized not in versions:
        raise InventoryError(
            "INVALID_UV_LOCK", f"uv.lock does not pin {package_name}"
        )
    return versions[normalized]


def _decode_utf8(result: ProcessResult, *, code: str, label: str) -> str:
    if result.returncode != 0:
        raise InventoryError(
            code,
            f"{label} command failed",
            details={"exit_code": result.returncode},
        )
    try:
        return result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise InventoryError(code, f"{label} output is not UTF-8") from exc


def _default_runtime_provider(
    root: Path, process_runner: ProcessRunner
) -> dict[str, Any]:
    try:
        expected_python = _required_input_snapshot(
            root, ".python-version"
        ).payload.decode("utf-8").strip()
        project = tomllib.loads(
            _required_input_snapshot(root, "pyproject.toml").payload.decode("utf-8")
        )
        lock = tomllib.loads(
            _required_input_snapshot(root, "uv.lock").payload.decode("utf-8")
        )
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise InventoryError(
            "INVALID_RUNTIME_BINDING", "runtime binding files are not valid UTF-8 TOML"
        ) from exc
    if not VERSION_RE.fullmatch(expected_python):
        raise InventoryError(
            "INVALID_RUNTIME_BINDING", ".python-version is not an exact version"
        )
    actual_python = platform.python_version()
    locked_distributions = _locked_distribution_versions(lock)
    try:
        expected_pytest = locked_distributions["pytest"]
        expected_pluggy = locked_distributions["pluggy"]
    except KeyError as exc:
        raise InventoryError(
            "INVALID_UV_LOCK", "uv.lock must pin pytest and pluggy"
        ) from exc
    try:
        expected_uv_spec = project["tool"]["uv"]["required-version"]
    except (KeyError, TypeError) as exc:
        raise InventoryError(
            "INVALID_RUNTIME_BINDING", "pyproject.toml lacks tool.uv.required-version"
        ) from exc
    if (
        not isinstance(expected_uv_spec, str)
        or not expected_uv_spec.startswith("==")
        or VERSION_RE.fullmatch(expected_uv_spec[2:]) is None
    ):
        raise InventoryError(
            "INVALID_RUNTIME_BINDING", "uv required-version must be an exact == pin"
        )
    expected_uv = expected_uv_spec[2:]
    try:
        actual_pytest = metadata.version("pytest")
        actual_pluggy = metadata.version("pluggy")
    except metadata.PackageNotFoundError as exc:
        raise InventoryError(
            "RUNTIME_UNAVAILABLE", "pytest or pluggy is not installed"
        ) from exc
    uv_result = process_runner(
        ("uv", "--version"), root, _collection_environment(), GIT_TIMEOUT_SECONDS
    )
    uv_output = _decode_utf8(
        uv_result, code="UV_UNAVAILABLE", label="uv version probe"
    )
    match = re.fullmatch(r"uv ([^ ]+)(?: .*)?", uv_output)
    if match is None:
        raise InventoryError("UV_UNAVAILABLE", "uv version output is not recognized")
    actual_uv = match.group(1)
    comparisons = {
        "python": (expected_python, actual_python),
        "pytest": (expected_pytest, actual_pytest),
        "pluggy": (expected_pluggy, actual_pluggy),
        "uv": (expected_uv, actual_uv),
    }
    mismatches = {
        name: {"expected": expected, "actual": actual}
        for name, (expected, actual) in comparisons.items()
        if expected != actual
    }
    if mismatches:
        raise InventoryError(
            "RUNTIME_LOCK_MISMATCH",
            "active collection runtime does not match committed pins",
            details={"mismatches": mismatches},
        )
    installed_by_name: dict[str, str] = {}
    try:
        installed_distributions = list(metadata.distributions())
    except Exception as exc:  # pragma: no cover - defensive metadata boundary
        raise InventoryError(
            "RUNTIME_UNAVAILABLE", "installed distribution metadata is unavailable"
        ) from exc
    for distribution in installed_distributions:
        raw_name = distribution.metadata.get("Name")
        if not isinstance(raw_name, str) or not raw_name:
            raise InventoryError(
                "RUNTIME_DISTRIBUTION_INVALID",
                "an installed distribution has no canonical metadata name",
            )
        name = _normalized_distribution_name(raw_name)
        if DISTRIBUTION_NAME_RE.fullmatch(name) is None:
            raise InventoryError(
                "RUNTIME_DISTRIBUTION_INVALID",
                "an installed distribution name is not canonical",
            )
        version = distribution.version
        if not isinstance(version, str) or not version:
            raise InventoryError(
                "RUNTIME_DISTRIBUTION_INVALID",
                "an installed distribution has no version",
                details={"name": name},
            )
        previous = installed_by_name.get(name)
        if previous is not None:
            raise InventoryError(
                "RUNTIME_DISTRIBUTION_INVALID",
                "multiple installed distributions share one normalized package name",
                details={"name": name},
            )
        installed_by_name[name] = version
    unlocked_or_mismatched = {
        name: {"installed": version, "locked": locked_distributions.get(name)}
        for name, version in installed_by_name.items()
        if locked_distributions.get(name) != version
    }
    if unlocked_or_mismatched:
        raise InventoryError(
            "RUNTIME_LOCK_MISMATCH",
            "installed distributions are not an exact-version subset of uv.lock",
            details={"distributions": unlocked_or_mismatched},
        )
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": actual_python,
        "pytest_version": actual_pytest,
        "pluggy_version": actual_pluggy,
        "uv_version": actual_uv,
        "platform": {
            "os_name": os.name,
            "sys_platform": sys.platform,
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_platform": sysconfig.get_platform(),
            "cache_tag": sys.implementation.cache_tag,
        },
        "installed_distributions": [
            {"name": name, "version": installed_by_name[name]}
            for name in sorted(installed_by_name, key=lambda value: value.encode("utf-8"))
        ],
    }


def _validate_collection_payload(payload: Mapping[str, Any]) -> None:
    worker_error = payload.get("worker_error")
    if worker_error is not None:
        if isinstance(worker_error, dict):
            code = worker_error.get("code", "COLLECTION_WORKER_ERROR")
            message = worker_error.get("message", "pytest collection worker failed")
        else:
            code = "COLLECTION_WORKER_ERROR"
            message = "pytest collection worker failed"
        raise InventoryError(str(code), str(message))
    expected_worker_runtime = {
        "dont_write_bytecode": True,
        "hash_seed": "0",
        "no_user_site": "1",
        "safe_path": True,
        "utf8_mode": True,
    }
    if payload.get("worker_runtime") != expected_worker_runtime:
        raise InventoryError(
            "WORKER_RUNTIME_MISMATCH",
            "pytest worker flags do not match the collection contract",
        )
    exit_code = payload.get("pytest_exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise InventoryError(
            "INVALID_COLLECTION_PAYLOAD", "pytest_exit_code must be an integer"
        )
    errors = payload.get("collection_errors")
    if not isinstance(errors, list):
        raise InventoryError(
            "INVALID_COLLECTION_PAYLOAD", "collection_errors must be an array"
        )
    if exit_code != 0 or errors:
        raise InventoryError(
            "PYTEST_COLLECTION_FAILED",
            "pytest did not complete a clean collection",
            details={"exit_code": exit_code, "collection_errors": errors},
        )


def _validated_marker_declarations(
    value: object, *, selected_node_ids: Sequence[str]
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise InventoryError(
            "INVALID_COLLECTION_PAYLOAD", "marker_declarations must be an array"
        )
    selected = set(selected_node_ids)
    declarations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in value:
        if not isinstance(record, dict) or set(record) != {"node_id", "markers"}:
            raise InventoryError(
                "INVALID_COLLECTION_PAYLOAD",
                "marker declaration must have exact fields",
            )
        node_id = normalize_node_id(record.get("node_id"))
        if node_id not in selected or node_id in seen:
            raise InventoryError(
                "INVALID_MARKER_DECLARATION",
                "marker declaration must identify one selected node exactly once",
            )
        markers = record.get("markers")
        if not isinstance(markers, list) or not markers:
            raise InventoryError(
                "INVALID_MARKER_DECLARATION", "marker declaration list must be non-empty"
            )
        canonical_markers: list[dict[str, Any]] = []
        for marker in markers:
            if not isinstance(marker, dict) or set(marker) != {"name", "args", "kwargs"}:
                raise InventoryError(
                    "INVALID_MARKER_DECLARATION", "marker declaration has invalid fields"
                )
            name = marker["name"]
            if name not in CONTROL_MARKERS:
                raise InventoryError(
                    "INVALID_MARKER_DECLARATION", "only skip/skipif/xfail are recorded"
                )
            args = _stable_marker_value(marker["args"])
            kwargs = _stable_marker_value(marker["kwargs"])
            if not isinstance(args, list) or not isinstance(kwargs, dict):
                raise InventoryError(
                    "INVALID_MARKER_DECLARATION", "marker args or kwargs have invalid shape"
                )
            canonical_markers.append({"name": name, "args": args, "kwargs": kwargs})
        canonical_markers.sort(key=_canonical_json_bytes)
        declarations.append({"node_id": node_id, "markers": canonical_markers})
        seen.add(node_id)
    node_order = {node_id: index for index, node_id in enumerate(selected_node_ids)}
    declarations.sort(key=lambda item: node_order[item["node_id"]])
    return declarations


def _validated_collection_skips(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise InventoryError(
            "INVALID_COLLECTION_PAYLOAD", "collection_skips must be an array"
        )
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for record in value:
        if not isinstance(record, dict) or set(record) != {"node_id", "reason"}:
            raise InventoryError(
                "INVALID_COLLECTION_PAYLOAD", "collection skip has invalid fields"
            )
        node_id = normalize_node_id(record["node_id"])
        reason = record["reason"]
        if not isinstance(reason, str) or not reason or "\x00" in reason:
            raise InventoryError(
                "INVALID_COLLECTION_PAYLOAD", "collection skip reason is invalid"
            )
        if node_id in seen:
            raise InventoryError(
                "INVALID_COLLECTION_PAYLOAD", "collection skip node IDs must be unique"
            )
        records.append({"node_id": node_id, "reason": reason})
        seen.add(node_id)
    records.sort(key=lambda item: item["node_id"].encode("utf-8"))
    return records


def build_test_identity(
    root: Path,
    collection: Mapping[str, Any],
    *,
    input_bindings: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    _validate_collection_payload(collection)
    node_ids = _validated_unique_node_ids(collection.get("node_ids"), label="node_ids")
    if not node_ids:
        raise InventoryError("EMPTY_TEST_INVENTORY", "pytest collected no selected tests")
    selected = _validated_unique_node_ids(
        collection.get("selected_node_ids"), label="selected_node_ids"
    )
    if not selected:
        raise InventoryError("EMPTY_TEST_SELECTION", "pytest selected no tests")
    deselected = _validated_unique_node_ids(
        collection.get("deselected_node_ids"), label="deselected_node_ids"
    )
    overlap = sorted(set(selected) & set(deselected), key=lambda item: item.encode("utf-8"))
    if overlap:
        raise InventoryError(
            "INVALID_COLLECTION_PAYLOAD",
            "selected and deselected node IDs overlap",
            details={"node_ids": overlap},
        )
    if set(node_ids) != set(selected) | set(deselected):
        raise InventoryError(
            "INVALID_COLLECTION_PAYLOAD",
            "full node inventory must equal selected plus deselected node IDs",
        )
    markers = _validated_marker_declarations(
        collection.get("marker_declarations"), selected_node_ids=node_ids
    )
    collection_skips = _validated_collection_skips(collection.get("collection_skips"))
    bound_inputs = (
        _input_bindings(root) if input_bindings is None else dict(input_bindings)
    )
    sorted_nodes = sorted(node_ids, key=lambda item: item.encode("utf-8"))
    test_identity = {
        "schema": TEST_IDENTITY_SCHEMA,
        "evidence_scope": EVIDENCE_SCOPE,
        "collection_contract": dict(COLLECTION_CONTRACT),
        "input_bindings": bound_inputs,
        "counts": {
            "collected": len(node_ids),
            "selected": len(selected),
            "deselected": len(deselected),
            "collection_skipped": len(collection_skips),
            "marker_declarations": len(markers),
        },
        "node_ids": node_ids,
        "selected_node_ids": selected,
        "deselected_node_ids": deselected,
        "collection_skips": collection_skips,
        "marker_declarations": markers,
        "node_set_sha256": _length_prefixed_digest(NODE_SET_DOMAIN, sorted_nodes),
        "node_order_sha256": _length_prefixed_digest(NODE_ORDER_DOMAIN, selected),
    }
    _validate_test_identity_document(
        test_identity, error_code="INVALID_TEST_IDENTITY"
    )
    return test_identity


def _run_git(
    process_runner: ProcessRunner,
    repo: Path,
    arguments: Sequence[str],
    *,
    label: str,
) -> bytes:
    result = process_runner(
        ("git", *_git_command_prefix(), *arguments),
        repo,
        _git_environment(),
        GIT_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise InventoryError(
            "GIT_COMMAND_FAILED",
            f"git {label} failed",
            details={"exit_code": result.returncode},
        )
    return result.stdout


def _resolve_head(repo: Path, process_runner: ProcessRunner) -> str:
    output = _run_git(
        process_runner, repo, ("rev-parse", "--verify", "HEAD^{commit}"), label="rev-parse"
    )
    try:
        commit = output.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise InventoryError("INVALID_GIT_COMMIT", "git returned a non-ASCII commit") from exc
    if not FULL_COMMIT_RE.fullmatch(commit):
        raise InventoryError("INVALID_GIT_COMMIT", "git did not return a full commit hash")
    return commit


def _validated_repository_path(raw: str, *, label: str) -> str:
    if (
        not raw
        or raw.startswith("/")
        or "\\" in raw
        or "\x00" in raw
        or any(ord(character) < 32 or ord(character) == 127 for character in raw)
        or "//" in raw
        or unicodedata.normalize("NFC", raw) != raw
    ):
        raise InventoryError("INVALID_GIT_MANIFEST", f"{label} path is not canonical")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw.split("/")):
        raise InventoryError("INVALID_GIT_MANIFEST", f"{label} path is unsafe")
    return raw


def _reject_component_collisions(paths: Sequence[str], *, code: str) -> None:
    components: dict[tuple[tuple[str, ...], str], str] = {}
    for raw in paths:
        parent: tuple[str, ...] = ()
        for component in PurePosixPath(raw).parts:
            key = (tuple(part.casefold() for part in parent), component.casefold())
            previous = components.get(key)
            if previous is not None and previous != component:
                raise InventoryError(
                    code,
                    "repository paths collide after per-component case folding",
                    details={"first": previous, "second": component},
                )
            components[key] = component
            parent = (*parent, component)


def _parse_git_tree_manifest(payload: bytes) -> tuple[GitTreeEntry, ...]:
    entries: list[GitTreeEntry] = []
    seen: set[str] = set()
    records = payload.split(b"\0")
    if records and records[-1] == b"":
        records.pop()
    for record in records:
        try:
            metadata_bytes, path_bytes = record.split(b"\t", 1)
            mode_bytes, type_bytes, oid_bytes, size_bytes = metadata_bytes.split()
            mode = mode_bytes.decode("ascii")
            object_type = type_bytes.decode("ascii")
            object_id = oid_bytes.decode("ascii")
            byte_size = int(size_bytes.decode("ascii"), 10)
            path = path_bytes.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise InventoryError(
                "INVALID_GIT_MANIFEST", "git ls-tree output is malformed"
            ) from exc
        _validated_repository_path(path, label="git manifest")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise InventoryError(
                "UNSUPPORTED_GIT_ENTRY",
                "commit snapshots support only regular non-symlink blobs",
                details={"path": path, "mode": mode, "type": object_type},
            )
        if not re.fullmatch(r"[0-9a-f]{40}", object_id):
            raise InventoryError(
                "INVALID_GIT_MANIFEST", "git object ID must be a full SHA-1 blob ID"
            )
        if byte_size < 0 or byte_size > MAX_GIT_BLOB_BYTES:
            raise InventoryError(
                "GIT_BLOB_TOO_LARGE",
                "git blob size is outside the bounded source policy",
                details={"path": path, "byte_size": byte_size},
            )
        if path in seen:
            raise InventoryError(
                "INVALID_GIT_MANIFEST", "git manifest paths must be unique"
            )
        seen.add(path)
        entries.append(GitTreeEntry(path, mode, object_type, object_id, byte_size))
    if not entries:
        raise InventoryError("INVALID_GIT_MANIFEST", "git manifest is empty")
    manifest_paths = {PurePosixPath(entry.path) for entry in entries}
    if any(
        parent in manifest_paths
        for path in manifest_paths
        for parent in path.parents
        if parent.as_posix() != "."
    ):
        raise InventoryError(
            "INVALID_GIT_MANIFEST", "git manifest nests an entry below a regular blob"
        )
    _reject_component_collisions([entry.path for entry in entries], code="GIT_PATH_COLLISION")
    entries.sort(key=lambda entry: entry.path.encode("utf-8"))
    if sum(entry.byte_size for entry in entries) > MAX_SOURCE_MATERIALIZED_BYTES:
        raise InventoryError(
            "GIT_SOURCE_TOO_LARGE", "git source tree exceeds the materialized byte limit"
        )
    return tuple(entries)


def _git_manifest_digest(entries: Sequence[GitTreeEntry]) -> str:
    records = [
        (
            f"{entry.mode} {entry.object_type} {entry.object_id} "
            f"{entry.byte_size}\t{entry.path}"
        )
        for entry in entries
    ]
    return _length_prefixed_digest(b"agtxiv.git-tree-manifest/1.0.0\0", records)


def _resolve_source_ref(
    repo: Path,
    source_ref: str,
    process_runner: ProcessRunner,
    git_blob_runner: GitBlobRunner = _default_git_blob_runner,
) -> PreparedGitSource:
    if not FULL_COMMIT_RE.fullmatch(source_ref):
        raise InventoryError(
            "INVALID_SOURCE_REF",
            "--source-ref accepts only a lowercase full 40-hex commit",
        )
    _run_git(
        process_runner,
        repo,
        ("cat-file", "-e", f"{source_ref}^{{commit}}"),
        label="cat-file",
    )
    resolved = _resolve_commit(repo, source_ref, process_runner)
    if resolved != source_ref:
        raise InventoryError(
            "INVALID_SOURCE_REF", "source ref does not resolve to the exact requested commit"
        )
    manifest_payload = _run_git(
        process_runner,
        repo,
        ("ls-tree", "-rzl", "--full-tree", source_ref),
        label="ls-tree",
    )
    entries = _parse_git_tree_manifest(manifest_payload)
    expected_sizes: dict[str, int] = {}
    for entry in entries:
        previous_size = expected_sizes.get(entry.object_id)
        if previous_size is not None and previous_size != entry.byte_size:
            raise InventoryError(
                "INVALID_GIT_MANIFEST",
                "one Git blob object has inconsistent declared sizes",
            )
        expected_sizes[entry.object_id] = entry.byte_size
    blobs: list[GitBlob] = []
    for object_id in sorted(expected_sizes):
        expected_size = expected_sizes[object_id]
        result = git_blob_runner(
            repo,
            object_id,
            _git_environment(),
            GIT_TIMEOUT_SECONDS,
            expected_size,
        )
        if result.returncode != 0 or result.output_limited:
            raise InventoryError(
                "GIT_BLOB_READ_FAILED",
                "bounded raw git cat-file blob read failed",
                details={
                    "object_id": object_id,
                    "exit_code": result.returncode,
                    "output_limited": result.output_limited,
                    "timed_out": result.timed_out,
                    "process_group_leaked": result.process_group_leaked,
                    "cleanup_unconfirmed": result.cleanup_unconfirmed,
                },
            )
        payload = result.stdout
        if len(payload) != expected_size:
            raise InventoryError(
                "GIT_BLOB_SIZE_MISMATCH",
                "raw git blob size differs from replacement-disabled ls-tree",
                details={"object_id": object_id},
            )
        digest = hashlib.sha1(usedforsecurity=False)
        digest.update(f"blob {len(payload)}\0".encode("ascii"))
        digest.update(payload)
        if digest.hexdigest() != object_id:
            raise InventoryError(
                "GIT_BLOB_OID_MISMATCH",
                "raw git blob bytes do not match their replacement-disabled object ID",
                details={"object_id": object_id},
            )
        blobs.append(GitBlob(object_id, payload))
    return PreparedGitSource(resolved, entries, tuple(blobs))


def _source_validator_entry(prepared: PreparedGitSource) -> GitTreeEntry:
    matching_entries = [
        entry
        for entry in prepared.entries
        if entry.path == VALIDATOR_RELATIVE_PATH
    ]
    if len(matching_entries) != 1:
        raise InventoryError(
            "VALIDATOR_SOURCE_BINDING_MISMATCH",
            "source commit must contain exactly one validator measuring instrument",
        )
    return matching_entries[0]


def _source_validator_payload(prepared: PreparedGitSource) -> bytes:
    entry = _source_validator_entry(prepared)
    blob_by_id = {blob.object_id: blob.payload for blob in prepared.blobs}
    payload = blob_by_id.get(entry.object_id)
    if payload is None or len(payload) != entry.byte_size:
        raise InventoryError(
            "VALIDATOR_SOURCE_BINDING_MISMATCH",
            "source validator blob is missing from the verified object set",
        )
    return payload


def _freeze_parent_validator() -> SafeFileSnapshot:
    return _safe_read_regular_file(
        Path(__file__).resolve(strict=True),
        max_bytes=MAX_INPUT_BYTES,
        unsafe_code="VALIDATOR_SOURCE_BINDING_MISMATCH",
        too_large_code="VALIDATOR_SOURCE_BINDING_MISMATCH",
        label="parent validator measuring instrument",
    )


def _bind_frozen_parent_to_source(
    frozen_parent: SafeFileSnapshot, prepared: PreparedGitSource
) -> bytes:
    source_payload = _source_validator_payload(prepared)
    if frozen_parent.payload != source_payload:
        raise InventoryError(
            "VALIDATOR_SOURCE_BINDING_MISMATCH",
            "parent validator bytes do not match the exact source commit",
        )
    return source_payload


def _verify_source_validator_binding(
    frozen_parent: SafeFileSnapshot, source_payload: bytes
) -> None:
    current = _safe_read_regular_file(
        Path(frozen_parent.absolute_path),
        max_bytes=MAX_INPUT_BYTES,
        unsafe_code="SOURCE_VALIDATOR_CHANGED_DURING_EVALUATION",
        too_large_code="SOURCE_VALIDATOR_CHANGED_DURING_EVALUATION",
        label="parent validator post-evaluation verification",
    )
    if current != frozen_parent or current.payload != source_payload:
        raise InventoryError(
            "SOURCE_VALIDATOR_CHANGED_DURING_EVALUATION",
            "parent validator bytes or identity changed during evaluation",
        )


def _resolve_commit(repo: Path, commit: str, process_runner: ProcessRunner) -> str:
    output = _run_git(
        process_runner,
        repo,
        ("rev-parse", "--verify", f"{commit}^{{commit}}"),
        label="rev-parse",
    )
    try:
        resolved = output.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise InventoryError("INVALID_GIT_COMMIT", "git returned a non-ASCII commit") from exc
    if not FULL_COMMIT_RE.fullmatch(resolved):
        raise InventoryError("INVALID_GIT_COMMIT", "git did not return a full commit hash")
    return resolved


def _materialize_git_source(prepared: PreparedGitSource, destination: Path) -> None:
    destination_resolved = destination.resolve(strict=True)
    if any(destination.iterdir()):
        raise InventoryError(
            "GIT_SNAPSHOT_NOT_EMPTY", "git snapshot destination must start empty"
        )
    blob_by_id = {blob.object_id: blob.payload for blob in prepared.blobs}
    if len(blob_by_id) != len(prepared.blobs):
        raise InventoryError("INVALID_GIT_BLOB_SET", "git blob objects must be unique")
    expected_object_ids = {entry.object_id for entry in prepared.entries}
    if set(blob_by_id) != expected_object_ids:
        raise InventoryError(
            "INVALID_GIT_BLOB_SET", "git blob objects do not match the tree manifest"
        )
    directory_paths = sorted(
        {
            parent
            for entry in prepared.entries
            for parent in PurePosixPath(entry.path).parents
            if parent.as_posix() != "."
        },
        key=lambda value: (len(value.parts), value.as_posix().encode("utf-8")),
    )
    for relative_directory in directory_paths:
        directory = destination_resolved.joinpath(*relative_directory.parts)
        if not directory.resolve(strict=False).is_relative_to(destination_resolved):
            raise InventoryError(
                "UNSAFE_GIT_MATERIALIZATION",
                "git directory would escape the fresh snapshot",
            )
        directory.mkdir(exist_ok=False)
        directory.chmod(0o755)
    for entry in prepared.entries:
        relative = PurePosixPath(entry.path)
        target = destination_resolved.joinpath(*relative.parts)
        if not target.resolve(strict=False).is_relative_to(destination_resolved):
            raise InventoryError(
                "UNSAFE_GIT_MATERIALIZATION",
                "git file would escape the fresh snapshot",
            )
        payload = blob_by_id[entry.object_id]
        if len(payload) != entry.byte_size:
            raise InventoryError(
                "GIT_BLOB_SIZE_MISMATCH",
                "materialized git blob size differs from the tree manifest",
            )
        file_descriptor: int | None = None
        try:
            file_descriptor = os.open(
                target,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                int(entry.mode[-3:], 8),
            )
            view = memoryview(payload)
            written = 0
            while written < len(view):
                count = os.write(file_descriptor, view[written:])
                if count <= 0:
                    raise InventoryError(
                        "GIT_MATERIALIZATION_FAILED",
                        "git snapshot write made no progress",
                    )
                written += count
            os.fchmod(file_descriptor, int(entry.mode[-3:], 8))
            materialized = os.fstat(file_descriptor)
            if (
                not stat.S_ISREG(materialized.st_mode)
                or materialized.st_size != entry.byte_size
                or stat.S_IMODE(materialized.st_mode) != int(entry.mode[-3:], 8)
            ):
                raise InventoryError(
                    "GIT_MATERIALIZATION_FAILED",
                    "materialized git file metadata is inconsistent",
                    details={"path": entry.path},
                )
        except OSError as exc:
            raise InventoryError(
                "GIT_MATERIALIZATION_FAILED",
                "git snapshot could not be materialized safely",
                details={"path": entry.path, "errno": exc.errno},
            ) from exc
        finally:
            if file_descriptor is not None:
                os.close(file_descriptor)
        verified = _safe_read_regular_file(
            target,
            max_bytes=entry.byte_size,
            unsafe_code="GIT_MATERIALIZATION_FAILED",
            too_large_code="GIT_MATERIALIZATION_FAILED",
            label=f"materialized git file {entry.path}",
        )
        verified_digest = hashlib.sha1(usedforsecurity=False)
        verified_digest.update(f"blob {len(verified.payload)}\0".encode("ascii"))
        verified_digest.update(verified.payload)
        if (
            verified_digest.hexdigest() != entry.object_id
            or stat.S_IMODE(verified.metadata.mode) != int(entry.mode[-3:], 8)
        ):
            raise InventoryError(
                "GIT_MATERIALIZATION_FAILED",
                "materialized git file differs from its verified raw blob",
                details={"path": entry.path},
            )


@contextmanager
def source_tree(
    repo: Path,
    source_ref: str | None,
    process_runner: ProcessRunner = _default_process_runner,
    git_blob_runner: GitBlobRunner = _default_git_blob_runner,
) -> Iterator[tuple[Path, dict[str, Any]]]:
    if source_ref is None:
        commit = _resolve_head(repo, process_runner)
        yield repo.resolve(), {
            "mode": "WORKTREE",
            "assurance_tier": "WORKTREE_DIAGNOSTIC",
            "requested_ref": None,
            "evaluated_commit": commit,
            "content_may_differ_from_evaluated_commit": True,
            "baseline_commit_binding": "EXCLUDED_TO_AVOID_SELF_REFERENCE",
            "branch_evidence_eligible": False,
            "filesystem_isolation_enforced": False,
            "network_isolation_enforced": False,
        }
        return
    frozen_parent = _freeze_parent_validator()
    source_payload = frozen_parent.payload
    try:
        prepared = _resolve_source_ref(
            repo, source_ref, process_runner, git_blob_runner=git_blob_runner
        )
        source_payload = _bind_frozen_parent_to_source(frozen_parent, prepared)
        with tempfile.TemporaryDirectory(
            prefix="agtxiv-pytest-inventory-"
        ) as temporary:
            snapshot = Path(temporary) / "snapshot"
            snapshot.mkdir()
            _materialize_git_source(prepared, snapshot)
            yield snapshot, {
                "mode": "GIT_BLOB_SNAPSHOT",
                "assurance_tier": "COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC",
                "requested_ref": source_ref,
                "evaluated_commit": prepared.commit,
                "content_may_differ_from_evaluated_commit": False,
                "baseline_commit_binding": "EXCLUDED_TO_AVOID_SELF_REFERENCE",
                "git_manifest_sha256": _git_manifest_digest(prepared.entries),
                "validator_binding": {
                    "path": VALIDATOR_RELATIVE_PATH,
                    "status": "PARENT_BYTES_MATCHED_SOURCE_COMMIT",
                    "git_blob_oid": _source_validator_entry(prepared).object_id,
                    "sha256": _sha256_bytes(source_payload),
                },
                "branch_evidence_eligible": False,
                "filesystem_isolation_enforced": False,
                "network_isolation_enforced": False,
            }
    finally:
        _verify_source_validator_binding(frozen_parent, source_payload)


def _require_exact_keys(
    value: object,
    expected: set[str],
    *,
    label: str,
    error_code: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise InventoryError(error_code, f"{label} must have exact fields")
    return value


def _validate_json_depth(value: Any, *, error_code: str) -> None:
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > MAX_JSON_DEPTH:
            raise InventoryError(error_code, "inventory exceeds the JSON nesting limit")
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)


def _validate_input_binding_document(value: object, *, error_code: str) -> None:
    bindings = _require_exact_keys(
        value,
        {".python-version", "pyproject.toml", "uv.lock"},
        label="input_bindings",
        error_code=error_code,
    )
    for relative, record_value in bindings.items():
        record = _require_exact_keys(
            record_value,
            {"byte_size", "sha256"},
            label=f"input binding {relative}",
            error_code=error_code,
        )
        byte_size = record["byte_size"]
        if (
            type(byte_size) is not int
            or byte_size < 1
            or byte_size > I_JSON_EXACT_INTEGER_MAX
        ):
            raise InventoryError(error_code, "input binding byte_size is invalid")
        if not isinstance(record["sha256"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", record["sha256"]
        ):
            raise InventoryError(error_code, "input binding sha256 is invalid")


def _validate_runtime_document(value: object, *, error_code: str) -> None:
    runtime = _require_exact_keys(
        value,
        {
            "python_implementation",
            "python_version",
            "pytest_version",
            "pluggy_version",
            "uv_version",
            "platform",
            "installed_distributions",
        },
        label="runtime",
        error_code=error_code,
    )
    if not isinstance(runtime["python_implementation"], str) or not runtime[
        "python_implementation"
    ]:
        raise InventoryError(error_code, "runtime implementation is invalid")
    for field in ("python_version", "pytest_version", "pluggy_version", "uv_version"):
        value_text = runtime[field]
        if not isinstance(value_text, str) or VERSION_RE.fullmatch(value_text) is None:
            raise InventoryError(error_code, f"runtime {field} is invalid")
    platform_record = _require_exact_keys(
        runtime["platform"],
        {
            "os_name",
            "sys_platform",
            "system",
            "release",
            "machine",
            "python_platform",
            "cache_tag",
        },
        label="runtime platform",
        error_code=error_code,
    )
    if any(not isinstance(item, str) or not item for item in platform_record.values()):
        raise InventoryError(error_code, "runtime platform value is invalid")
    distributions = runtime["installed_distributions"]
    if not isinstance(distributions, list) or not distributions:
        raise InventoryError(error_code, "installed_distributions must be non-empty")
    canonical: list[dict[str, str]] = []
    seen: set[str] = set()
    for record_value in distributions:
        record = _require_exact_keys(
            record_value,
            {"name", "version"},
            label="installed distribution",
            error_code=error_code,
        )
        name = record["name"]
        version = record["version"]
        if (
            not isinstance(name, str)
            or DISTRIBUTION_NAME_RE.fullmatch(name) is None
            or name in seen
        ):
            raise InventoryError(error_code, "installed distribution name is invalid")
        if not isinstance(version, str) or not version:
            raise InventoryError(error_code, "installed distribution version is invalid")
        canonical.append({"name": name, "version": version})
        seen.add(name)
    expected_order = sorted(canonical, key=lambda item: item["name"].encode("utf-8"))
    if canonical != expected_order:
        raise InventoryError(error_code, "installed distributions are not sorted")
    versions = {record["name"]: record["version"] for record in canonical}
    if versions.get("pytest") != runtime["pytest_version"] or versions.get(
        "pluggy"
    ) != runtime["pluggy_version"]:
        raise InventoryError(
            error_code, "pytest/pluggy runtime versions disagree with distribution metadata"
        )


def _environment_qualification(runtime: Mapping[str, Any]) -> dict[str, Any]:
    runtime_record = dict(runtime)
    _validate_runtime_document(
        runtime_record, error_code="INVALID_ENVIRONMENT_QUALIFICATION"
    )
    return {
        "status": ENVIRONMENT_QUALIFICATION_STATUS,
        "security_role": ENVIRONMENT_SECURITY_ROLE,
        "qualification_scope": ENVIRONMENT_QUALIFICATION_SCOPE,
        "runtime": runtime_record,
    }


def _validate_collection_contract_document(
    value: object, *, error_code: str
) -> None:
    contract = _require_exact_keys(
        value,
        set(COLLECTION_CONTRACT),
        label="collection contract",
        error_code=error_code,
    )
    for field, expected in COLLECTION_CONTRACT.items():
        actual = contract[field]
        if type(actual) is not type(expected):
            raise InventoryError(
                error_code, "collection contract field type is not pinned"
            )
        if isinstance(expected, list):
            if (
                len(actual) != len(expected)
                or any(type(item) is not str for item in actual)
                or any(
                    type(item) is not type(expected_item) or item != expected_item
                    for item, expected_item in zip(actual, expected, strict=True)
                )
            ):
                raise InventoryError(
                    error_code, "collection contract array value is not pinned"
                )
        elif actual != expected:
            raise InventoryError(
                error_code, "collection contract field value is not pinned"
            )


def _validate_test_identity_document(
    value: object, *, error_code: str = "INVALID_BASELINE"
) -> None:
    _validate_json_depth(value, error_code=error_code)
    test_identity = _require_exact_keys(
        value,
        {
            "schema",
            "evidence_scope",
            "collection_contract",
            "input_bindings",
            "counts",
            "node_ids",
            "selected_node_ids",
            "deselected_node_ids",
            "collection_skips",
            "marker_declarations",
            "node_set_sha256",
            "node_order_sha256",
        },
        label="test identity",
        error_code=error_code,
    )
    if test_identity["schema"] != TEST_IDENTITY_SCHEMA:
        raise InventoryError(error_code, "test identity schema identifier is invalid")
    if test_identity["evidence_scope"] != EVIDENCE_SCOPE:
        raise InventoryError(error_code, "test identity evidence scope is invalid")
    _validate_collection_contract_document(
        test_identity["collection_contract"], error_code=error_code
    )
    _validate_input_binding_document(
        test_identity["input_bindings"], error_code=error_code
    )

    counts = _require_exact_keys(
        test_identity["counts"],
        {
            "collected",
            "selected",
            "deselected",
            "collection_skipped",
            "marker_declarations",
        },
        label="counts",
        error_code=error_code,
    )
    if any(
        type(count) is not int
        or count < 0
        or count > I_JSON_EXACT_INTEGER_MAX
        for count in counts.values()
    ):
        raise InventoryError(error_code, "test identity count is invalid")

    try:
        node_ids = _validated_unique_node_ids(
            test_identity["node_ids"], label="node_ids"
        )
        selected = _validated_unique_node_ids(
            test_identity["selected_node_ids"], label="selected_node_ids"
        )
        deselected = _validated_unique_node_ids(
            test_identity["deselected_node_ids"], label="deselected_node_ids"
        )
        skips = _validated_collection_skips(test_identity["collection_skips"])
        markers = _validated_marker_declarations(
            test_identity["marker_declarations"], selected_node_ids=node_ids
        )
    except InventoryError as exc:
        raise InventoryError(
            error_code, f"test identity semantics are invalid: {exc.code}"
        ) from exc
    if not node_ids or not selected:
        raise InventoryError(
            error_code, "test identity must contain collected and selected nodes"
        )
    if set(selected) & set(deselected):
        raise InventoryError(error_code, "selected and deselected node IDs overlap")
    if set(node_ids) != set(selected) | set(deselected):
        raise InventoryError(
            error_code, "collected nodes do not equal selected plus deselected nodes"
        )
    if skips != test_identity["collection_skips"]:
        raise InventoryError(error_code, "collection skips are not canonically ordered")
    if markers != test_identity["marker_declarations"]:
        raise InventoryError(error_code, "marker declarations are not canonical")
    expected_counts = {
        "collected": len(node_ids),
        "selected": len(selected),
        "deselected": len(deselected),
        "collection_skipped": len(skips),
        "marker_declarations": len(markers),
    }
    if counts != expected_counts:
        raise InventoryError(
            error_code, "test identity counts disagree with identity arrays"
        )
    expected_set_digest = _length_prefixed_digest(
        NODE_SET_DOMAIN, sorted(node_ids, key=lambda item: item.encode("utf-8"))
    )
    expected_order_digest = _length_prefixed_digest(NODE_ORDER_DOMAIN, selected)
    if test_identity["node_set_sha256"] != expected_set_digest:
        raise InventoryError(error_code, "node_set_sha256 is not derived from node_ids")
    if test_identity["node_order_sha256"] != expected_order_digest:
        raise InventoryError(
            error_code, "node_order_sha256 is not derived from selected_node_ids"
        )


def _load_baseline(path: Path) -> FrozenBaseline:
    snapshot = _safe_read_regular_file(
        path,
        max_bytes=MAX_BASELINE_BYTES,
        unsafe_code="BASELINE_UNSAFE",
        too_large_code="BASELINE_TOO_LARGE",
        label="baseline",
    )
    try:
        baseline_text = snapshot.payload.decode("utf-8")
        payload = _strict_json_loads(baseline_text, label="baseline")
    except UnicodeDecodeError as exc:
        raise InventoryError("INVALID_JSON", "baseline is not UTF-8") from exc
    _validate_test_identity_document(payload)
    assert isinstance(payload, dict)
    return FrozenBaseline(payload, _sha256_bytes(snapshot.payload), snapshot)


def _verify_frozen_baseline(frozen: FrozenBaseline) -> None:
    current = _safe_read_regular_file(
        Path(frozen.file_snapshot.absolute_path),
        max_bytes=MAX_BASELINE_BYTES,
        unsafe_code="BASELINE_CHANGED_DURING_EVALUATION",
        too_large_code="BASELINE_CHANGED_DURING_EVALUATION",
        label="baseline post-evaluation verification",
    )
    if current != frozen.file_snapshot:
        raise InventoryError(
            "BASELINE_CHANGED_DURING_EVALUATION",
            "baseline bytes, metadata, or ancestor identity changed during evaluation",
        )


def _baseline_difference(
    expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> dict[str, Any]:
    expected_nodes = expected.get("node_ids")
    actual_nodes = actual.get("node_ids")
    expected_set = set(expected_nodes) if isinstance(expected_nodes, list) else set()
    actual_set = set(actual_nodes) if isinstance(actual_nodes, list) else set()
    expected_selected = expected.get("selected_node_ids")
    actual_selected = actual.get("selected_node_ids")
    return {
        "expected_test_identity_sha256": _test_identity_digest(expected),
        "actual_test_identity_sha256": _test_identity_digest(actual),
        "added_node_ids": sorted(
            actual_set - expected_set, key=lambda item: str(item).encode("utf-8")
        ),
        "removed_node_ids": sorted(
            expected_set - actual_set, key=lambda item: str(item).encode("utf-8")
        ),
        "node_order_changed": expected_nodes != actual_nodes,
        "selected_order_changed": expected_selected != actual_selected,
    }


def _assert_guarded_collections_equal(
    first: GuardedCollection, second: GuardedCollection
) -> None:
    differences = {
        "collection": _canonical_json_bytes(first.collection)
        != _canonical_json_bytes(second.collection),
        "input_bindings": _canonical_json_bytes(first.input_bindings)
        != _canonical_json_bytes(second.input_bindings),
        "runtime": _canonical_json_bytes(first.runtime)
        != _canonical_json_bytes(second.runtime),
        "source_manifest": first.manifest_sha256 != second.manifest_sha256,
    }
    if any(differences.values()):
        raise InventoryError(
            "NONDETERMINISTIC_COLLECTION",
            "two guarded pytest collections produced different evidence",
            details={
                "differing_components": [
                    name for name, differs in differences.items() if differs
                ]
            },
        )


def _worktree_source_record(commit: str) -> dict[str, Any]:
    return {
        "mode": "WORKTREE",
        "assurance_tier": "WORKTREE_DIAGNOSTIC",
        "requested_ref": None,
        "evaluated_commit": commit,
        "content_may_differ_from_evaluated_commit": True,
        "baseline_commit_binding": "EXCLUDED_TO_AVOID_SELF_REFERENCE",
        "branch_evidence_eligible": False,
        "filesystem_isolation_enforced": False,
        "network_isolation_enforced": False,
    }


def _commit_source_record(
    source_ref: str, prepared: PreparedGitSource
) -> dict[str, Any]:
    return {
        "mode": "GIT_BLOB_SNAPSHOT",
        "assurance_tier": "COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC",
        "requested_ref": source_ref,
        "evaluated_commit": prepared.commit,
        "content_may_differ_from_evaluated_commit": False,
        "baseline_commit_binding": "EXCLUDED_TO_AVOID_SELF_REFERENCE",
        "git_manifest_sha256": _git_manifest_digest(prepared.entries),
        "branch_evidence_eligible": False,
        "filesystem_isolation_enforced": False,
        "network_isolation_enforced": False,
    }


def _collect_current_test_identity(
    options: EvaluationOptions,
    *,
    repo: Path,
    process_runner: ProcessRunner,
    collection_runner: CollectionRunner | None,
    runtime_provider: RuntimeProvider,
    git_blob_runner: GitBlobRunner,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if options.source_ref is None:
        commit = _resolve_head(repo, process_runner)
        source = _worktree_source_record(commit)
        root = repo.resolve(strict=True)
        first = _guarded_collection(
            root,
            collection_runner=collection_runner,
            process_runner=process_runner,
            runtime_provider=runtime_provider,
            excluded_directory_names=WORKTREE_MANIFEST_EXCLUDED_DIRECTORY_NAMES,
        )
        second = _guarded_collection(
            root,
            collection_runner=collection_runner,
            process_runner=process_runner,
            runtime_provider=runtime_provider,
            excluded_directory_names=WORKTREE_MANIFEST_EXCLUDED_DIRECTORY_NAMES,
        )
    else:
        frozen_parent = _freeze_parent_validator()
        source_payload: bytes | None = None
        source_operation_error: Exception | None = None
        try:
            prepared = _resolve_source_ref(
                repo,
                options.source_ref,
                process_runner,
                git_blob_runner=git_blob_runner,
            )
            source_payload = _bind_frozen_parent_to_source(
                frozen_parent, prepared
            )
            source = _commit_source_record(options.source_ref, prepared)
            source["validator_binding"] = {
                "path": VALIDATOR_RELATIVE_PATH,
                "status": "PARENT_BYTES_MATCHED_SOURCE_COMMIT",
                "git_blob_oid": _source_validator_entry(prepared).object_id,
                "sha256": _sha256_bytes(source_payload),
            }
            with tempfile.TemporaryDirectory(
                prefix="agtxiv-pytest-inventory-first-"
            ) as first_temporary, tempfile.TemporaryDirectory(
                prefix="agtxiv-pytest-inventory-second-"
            ) as second_temporary:
                first_root = Path(first_temporary) / "snapshot"
                second_root = Path(second_temporary) / "snapshot"
                first_root.mkdir()
                second_root.mkdir()
                _materialize_git_source(prepared, first_root)
                first = _guarded_collection(
                    first_root,
                    collection_runner=collection_runner,
                    process_runner=process_runner,
                    runtime_provider=runtime_provider,
                )
                _materialize_git_source(prepared, second_root)
                second = _guarded_collection(
                    second_root,
                    collection_runner=collection_runner,
                    process_runner=process_runner,
                    runtime_provider=runtime_provider,
                )
        except Exception as exc:
            source_operation_error = exc
        try:
            _verify_source_validator_binding(
                frozen_parent,
                frozen_parent.payload if source_payload is None else source_payload,
            )
        except InventoryError as verification_error:
            raise verification_error from source_operation_error
        if source_operation_error is not None:
            raise source_operation_error
    _assert_guarded_collections_equal(first, second)
    source["collection_snapshot_manifest_sha256"] = first.manifest_sha256
    test_identity = build_test_identity(
        repo,
        first.collection,
        input_bindings=first.input_bindings,
    )
    environment_qualification = _environment_qualification(first.runtime)
    return source, test_identity, environment_qualification


def evaluate(
    options: EvaluationOptions,
    *,
    repo: Path = REPO,
    process_runner: ProcessRunner = _default_process_runner,
    collection_runner: CollectionRunner | None = None,
    runtime_provider: RuntimeProvider = _default_runtime_provider,
    git_blob_runner: GitBlobRunner = _default_git_blob_runner,
) -> tuple[int, dict[str, Any]]:
    source: dict[str, Any] | None = None
    try:
        frozen_baseline: FrozenBaseline | None = None
        if options.operation == "CHECK":
            if options.baseline is None:
                raise InventoryError(
                    "BASELINE_UNAVAILABLE", "check operation requires a baseline path"
                )
            # This is deliberately the first operation that can touch external state.
            # It runs before every Git, uv/runtime, or pytest subprocess.
            frozen_baseline = _load_baseline(options.baseline)

        operation_error: Exception | None = None
        test_identity: dict[str, Any] | None = None
        environment_qualification: dict[str, Any] | None = None
        try:
            (
                source,
                test_identity,
                environment_qualification,
            ) = _collect_current_test_identity(
                options,
                repo=repo,
                process_runner=process_runner,
                collection_runner=collection_runner,
                runtime_provider=runtime_provider,
                git_blob_runner=git_blob_runner,
            )
        except Exception as exc:
            operation_error = exc

        if frozen_baseline is not None:
            try:
                _verify_frozen_baseline(frozen_baseline)
            except InventoryError as verification_error:
                raise verification_error from operation_error
        if operation_error is not None:
            raise operation_error
        assert test_identity is not None
        assert environment_qualification is not None

        result: dict[str, Any] = {
            "schema": EVALUATION_SCHEMA,
            "operation": options.operation,
            "outcome": "PASS",
            "source": source,
            "test_identity_sha256": _test_identity_digest(test_identity),
            "test_identity": test_identity,
            "environment_qualification": environment_qualification,
            "errors": [],
        }
        if frozen_baseline is not None:
            result["baseline_sha256"] = frozen_baseline.sha256
            baseline = frozen_baseline.document
            if _canonical_json_bytes(baseline) != _canonical_json_bytes(
                test_identity
            ):
                result["outcome"] = "FAIL"
                result["errors"] = [
                    _error_record(
                        "BASELINE_MISMATCH",
                        "actual pytest test identity differs from the baseline",
                        details=_baseline_difference(baseline, test_identity),
                    )
                ]
                return 1, result
        return 0, result
    except InventoryError as exc:
        return 1, {
            "schema": EVALUATION_SCHEMA,
            "operation": options.operation,
            "outcome": "ERROR",
            "source": source,
            "test_identity": None,
            "test_identity_sha256": None,
            "environment_qualification": None,
            "errors": [exc.record()],
        }
    except OSError as exc:
        return 1, {
            "schema": EVALUATION_SCHEMA,
            "operation": options.operation,
            "outcome": "ERROR",
            "source": source,
            "test_identity": None,
            "test_identity_sha256": None,
            "environment_qualification": None,
            "errors": [
                _error_record(
                    "FILESYSTEM_ERROR",
                    f"filesystem operation failed: {type(exc).__name__}",
                )
            ],
        }
    except Exception as exc:  # pragma: no cover - last-resort machine boundary
        return 1, {
            "schema": EVALUATION_SCHEMA,
            "operation": options.operation,
            "outcome": "ERROR",
            "source": source,
            "test_identity": None,
            "test_identity_sha256": None,
            "environment_qualification": None,
            "errors": [
                _error_record(
                    "INTERNAL_INVENTORY_ERROR",
                    (
                        "unexpected inventory failure: "
                        f"{type(exc).__module__}.{type(exc).__qualname__}"
                    ),
                )
            ],
        }


def _parse_options(argv: Sequence[str] | None) -> EvaluationOptions:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument(
        "--candidate", action="store_true", help="emit a candidate test identity as JSON"
    )
    operation.add_argument(
        "--check", metavar="BASELINE", type=Path, help="compare with a read-only baseline"
    )
    parser.add_argument(
        "--source-ref",
        metavar="FULL_COMMIT",
        help="collect from raw verified Git blobs of one exact lowercase 40-hex commit",
    )
    args = parser.parse_args(argv)
    if args.candidate:
        return EvaluationOptions("CANDIDATE", source_ref=args.source_ref)
    return EvaluationOptions("CHECK", baseline=args.check, source_ref=args.source_ref)


def main(argv: Sequence[str] | None = None) -> int:
    options = _parse_options(argv)
    try:
        exit_code, result = evaluate(options)
    except Exception:
        exit_code = 1
        result = {
            "schema": EVALUATION_SCHEMA,
            "operation": options.operation,
            "outcome": "ERROR",
            "source": None,
            "test_identity": None,
            "test_identity_sha256": None,
            "environment_qualification": None,
            "errors": [
                _error_record(
                    "INTERNAL_INVENTORY_ERROR",
                    "unexpected inventory failure at the machine-output boundary",
                )
            ],
        }
    fallback = {
        "schema": EVALUATION_SCHEMA,
        "operation": options.operation,
        "outcome": "ERROR",
        "source": None,
        "test_identity": None,
        "test_identity_sha256": None,
        "environment_qualification": None,
        "errors": [
            {
                "code": "MACHINE_OUTPUT_ENCODING_FAILED",
                "message": "inventory result could not be encoded as UTF-8 JSON",
            }
        ],
    }
    encoded, used_fallback = _machine_json_bytes(result, fallback=fallback)
    if used_fallback:
        exit_code = 1
    sys.stdout.buffer.write(encoded + b"\n")
    return exit_code


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--_collect-worker":
        raise SystemExit(_collect_worker_cli(sys.argv[2]))
    raise SystemExit(main())
