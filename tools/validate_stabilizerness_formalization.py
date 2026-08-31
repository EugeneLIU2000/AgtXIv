#!/usr/bin/env python3
"""Run a static byte-integrity diagnostic for the pinned Stabilizerness inputs.

This diagnostic does not type-check, build, or axiom-audit Lean declarations.
"""

from __future__ import annotations

import configparser
import hashlib
import json
import os
import re
import selectors
import shutil
import signal
import stat
import subprocess
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PROJECT_RELATIVE = Path("formal/AgtXIvStabilizerness")
RESULT_RELATIVE = PROJECT_RELATIVE / "verification-result.json"
TOOLCHAIN_RELATIVE = Path(
    ".tools/elan/toolchains/leanprover--lean4---v4.30.0-rc2"
)
TOOLCHAIN_BIN_RELATIVE = TOOLCHAIN_RELATIVE / "bin"
LAKE_RELATIVE = TOOLCHAIN_BIN_RELATIVE / "lake"
LEAN_RELATIVE = TOOLCHAIN_BIN_RELATIVE / "lean"

REPORT_SCHEMA = "agtxiv.stabilizerness-dynamic-validation-report/0.1.0"
REPORT_TOP_LEVEL_KEYS = frozenset(
    {
        "schema",
        "historical_evidence_schema_version",
        "project",
        "assurance_tier",
        "cache_mode",
        "consumed_cache_closure",
        "source_clean_rebuild",
        "network_mode",
        "network_isolation_enforced",
        "filesystem_isolation_enforced",
        "network_note",
        "evidence_id",
        "declared_historical_status",
        "effective_validation_status",
        "dynamic_execution",
        "dynamic_blocker_code",
        "dynamic_blocker_reason",
        "kernel_build",
        "kernel_build_failure_excerpt",
        "axiom_audit",
        "declarations_audited",
        "target_local_declarations_audited",
        "imported_declarations_audited",
        "expected_target_local_declarations",
        "expected_imported_declarations",
        "declaration_audit",
        "reported_axioms",
        "evidence_anchors",
        "artifact_hashes",
        "formal_input_inventory",
        "environment_binding",
        "tool_identity",
        "dependency_git_identity",
        "placeholder_scan",
        "protected_input_integrity",
        "side_effect_observation_scope",
        "external_commands",
        "admission_eligible",
        "security_gate_eligible",
        "m0_completion_effect",
        "admission_note",
        "remaining_m0_security_blockers",
        "errors",
        "formalization_validation",
        "scientific_acceptance_effect",
        "scope_limitations",
        "environment_policy",
    }
)
REPORT_DECLARATION_ENTRY_KEYS = frozenset({"scope", "audit_status", "axioms"})
REPORT_TOOL_IDENTITY_KEYS = frozenset(
    {
        "validation",
        "static_path_validation",
        "dynamic_identity",
        "paths",
        "resolved_git_executable",
    }
)
REPORT_TOOL_PATH_KEYS = frozenset({"lake", "lean"})
REPORT_DEPENDENCY_IDENTITY_KEYS = frozenset(
    {"validation", "source_tree_closure", "consumed_cache_closure"}
)
EXPECTED_HISTORICAL_SCHEMA_VERSION = "0.1.0-prototype"
EXPECTED_EVIDENCE_ID = "lean-verification:stabilizerness-local-delta:2026-08-16"
EXPECTED_STATUS = "TARGET_LOCAL_DELTA_KERNEL_CHECKED"
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
EXPECTED_LEAN_VERSION = "4.30.0-rc2"
EXPECTED_LAKE_VERSION = "5.0.0-src+3dc1a08"
EXPECTED_LEAN_GITHASH = "3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc"
EXPECTED_MATHLIB_COMMIT = "c1e30e172c8fda21e6776bf1f10351e882ee31b9"
EXPECTED_QUANTUMLIB_COMMIT = "44fc4eb1f4ba512e659deacd3468fda0a764d162"
EXPECTED_QUANTUMLIB_ORIGIN = "https://github.com/inQWIRE/LeanQuantum"
EXPECTED_QUANTUMLIB_TREE = "98dec098800b988c5cb805e1614c68fbd8537229"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
NETWORK_MODE = "OFFLINE_INTENDED_PRELOADED_ONLY"
ASSURANCE_TIER = "LOCAL_PRELOADED_DIAGNOSTIC"
BLOCKER_CODE = "UNVERIFIED_FUTURE_LEAN_CACHE_CLOSURE"
BLOCKER_REASON = (
    "consumed_cache_closure=NOT_VERIFIED: a future Lean run would consume preloaded "
    ".lake artifacts without an external exact type/mode/content manifest; clean "
    "scratch execution, OS-level no-egress, and executable byte locks are also "
    "not implemented"
)
NETWORK_NOTE = (
    "No dynamic command ran. This validator does not enforce operating-system "
    "outbound network blocking."
)
SIDE_EFFECT_OBSERVATION_SCOPE_KEYS = frozenset(
    {
        "method",
        "observed_paths",
        "reused_unmeasured_cache_roots",
        "paths_outside_observed_formal_and_evidence_closure",
        "future_dynamic_note",
        "filesystem_isolation_enforced",
    }
)
SIDE_EFFECT_OBSERVATION_METHOD = (
    "two pure-Python lstat/O_NOFOLLOW raw-byte snapshots of the exact "
    "anchored evidence, artifact, and three-project formal inventories"
)
SIDE_EFFECT_REUSED_UNMEASURED_CACHE_ROOTS = (
    "formal/AgtXIvStabilizerness/.lake/**",
    "formal/AgtXIvRootMath/.lake/**",
    "formal/AgtXIvVarela/.lake/**",
    "Reference/LeanQuantum/.lake/**",
)
SIDE_EFFECT_OUTSIDE_OBSERVED_CLOSURE = "NOT_MEASURED"
SIDE_EFFECT_FUTURE_DYNAMIC_NOTE = (
    "A future Lean run would consume these unverified cache roots; this "
    "static diagnostic did not consume or validate them."
)
OBSERVED_PATHS_SHA256 = (
    "529247c6326e749370207bb84dff73c98a25b873ae1c697b1f5822d402c71ed3"
)
ADMISSION_NOTE = (
    "An EXPECTED_BLOCKED diagnostic must not be used for database admission, "
    "merge approval, or a threat-model security gate."
)
REMAINING_M0_SECURITY_BLOCKERS = (
    "externally anchored consumed .lake cache closure or clean scratch rebuild",
    "clean scratch workspace",
    "operating-system enforced no-egress execution",
    "cryptographic lock for Lean, Lake, and Git executable bytes",
)
ENVIRONMENT_POLICY_KEYS = frozenset({"network_mode", "credential_minimized"})

GIT_TIMEOUT_SECONDS = 15
VERSION_TIMEOUT_SECONDS = 15
AUDIT_TIMEOUT_SECONDS = 300
BUILD_TIMEOUT_SECONDS = 900
PROCESS_GROUP_GRACE_SECONDS = 5
POST_EXIT_DRAIN_SECONDS = 1
MAX_CAPTURE_BYTES = 8 * 1024 * 1024
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_FORMAL_FILE_BYTES = 64 * 1024 * 1024
MAX_DEPENDENCY_FILE_BYTES = 128 * 1024 * 1024
MAX_DEPENDENCY_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
TIMEOUT_EXIT_CODE = 124
OUTPUT_LIMIT_EXIT_CODE = 125
BACKGROUND_PROCESS_EXIT_CODE = 126

EXPECTED_EVIDENCE_SHA256 = {
    "formal/AgtXIvStabilizerness/verification-result.json": (
        "02d6aaaa3d86c91a017f912459896b290f3a630cde9bba54a215f84762496d14"
    ),
    "formal/AgtXIvRootMath/verification-result.json": (
        "94111e224d0cb934aa98c164665859828955549e9fa1452797efe55188fb4e50"
    ),
    "formal/AgtXIvVarela/verification-result.json": (
        "9d532854f826afe453ac350527070d74650cbb1e0a519c3e3da1df0bd79a9a6c"
    ),
}

DEPENDENCY_EVIDENCE_PATHS = {
    "formal/AgtXIvRootMath/verification-result.json",
    "formal/AgtXIvVarela/verification-result.json",
}
EXPECTED_GIT_PACKAGES = {
    "Cli": {
        "origin": "https://github.com/leanprover/lean4-cli",
        "revision": "13567aed1ac4f12aea9484178e07e51f8c9f7658",
        "input_revision": "v4.30.0-rc2",
        "tree": "15b725754ebcf01202bb28e404ed0e42246efc54",
    },
    "LeanSearchClient": {
        "origin": "https://github.com/leanprover-community/LeanSearchClient",
        "revision": "c5d5b8fe6e5158def25cd28eb94e4141ad97c843",
        "input_revision": "main",
        "tree": "d0224b6df6c90cc0b4ed2db6218037d31bfd6f52",
    },
    "Qq": {
        "origin": "https://github.com/leanprover-community/quote4",
        "revision": "1cc7e819b9b9bc1e87c9edcccb62e0269e00a809",
        "input_revision": "v4.30.0-rc2",
        "tree": "a515231cbf007e41a84bc2bb65ec91cc27684c70",
    },
    "aesop": {
        "origin": "https://github.com/leanprover-community/aesop",
        "revision": "f0c6e183ea26531e82773feb4b73ab6595ca17a5",
        "input_revision": "v4.30.0-rc2",
        "tree": "4a1006c9183cf1e70a207a14653d28405d49e3c5",
    },
    "batteries": {
        "origin": "https://github.com/leanprover-community/batteries",
        "revision": "5c57f3857ba81924a88b2cdf4f062e34ec04ff11",
        "input_revision": "v4.30.0-rc2",
        "tree": "1c86760fadbe6bf15d8e281431dbc92f93afda45",
    },
    "importGraph": {
        "origin": "https://github.com/leanprover-community/import-graph",
        "revision": "cdab3938ccabbdb044be6896e251b5814bec932e",
        "input_revision": "main",
        "tree": "f02b64d855db070eb5e2f1f01a65286f1462448e",
    },
    "mathlib": {
        "origin": "https://github.com/leanprover-community/mathlib4.git",
        "revision": EXPECTED_MATHLIB_COMMIT,
        "input_revision": EXPECTED_MATHLIB_COMMIT,
        "tree": "426094735539fc51969f67ac28a5de0bf55348c8",
    },
    "plausible": {
        "origin": "https://github.com/leanprover-community/plausible",
        "revision": "86210d4ad1b08b086d0bd638637a75246523dbb8",
        "input_revision": "main",
        "tree": "bfbaf990f50b6c1428ede79ab945741d5a3cdd16",
    },
    "proofwidgets": {
        "origin": "https://github.com/leanprover-community/ProofWidgets4",
        "revision": "2db6054a44326f8c0230ee0570e2ddb894816511",
        "input_revision": "v0.0.98",
        "tree": "d1674b8cf337e1e5fd2bc43a58ae2f7e16ddd9f3",
    },
}
EXPECTED_PATH_PACKAGES = {
    "AgtXIvRootMath",
    "AgtXIvVarela",
    "quantumlib",
}
EXPECTED_PACKAGE_NAMES = set(EXPECTED_GIT_PACKAGES) | EXPECTED_PATH_PACKAGES

LOCAL_DECLARATIONS = {
    "AgtXIv.Stabilizerness.abs_signed_sum_add_le",
    "AgtXIv.Stabilizerness.exists_sign_attaining_abs_sum",
    "AgtXIv.Stabilizerness.max_abs_signed_sum",
    "AgtXIv.Stabilizerness.affineSpan_eq_top_of_vectorSpan_eq_top",
}
IMPORTED_DECLARATIONS = {
    "AgtXIv.GraphFoundation.independentFinsets",
    "AgtXIv.GraphFoundation.maxWeightIndependent",
    "AgtXIv.GraphFoundation.IsPerfect",
}
ALL_DECLARATIONS = LOCAL_DECLARATIONS | IMPORTED_DECLARATIONS

REQUIRED_ARTIFACTS = {
    "formal/AgtXIvStabilizerness/AgtXIvStabilizerness.lean",
    "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/LocalDelta.lean",
    "formal/AgtXIvStabilizerness/Audit.lean",
    "formal/AgtXIvStabilizerness/lakefile.toml",
    "formal/AgtXIvStabilizerness/lake-manifest.json",
    "formal/AgtXIvStabilizerness/lean-toolchain",
}

EXPECTED_COMMANDS = [
    "lake build",
    "lake env lean Audit.lean",
    "project-source placeholder scan",
]
EXPECTED_SCOPE_LIMITATIONS = [
    (
        "The affine-span declaration is only a generic reduction from vector span "
        "and does not prove claim:relaxed-affine-span."
    ),
    (
        "The sign-maximization declaration does not by itself prove "
        "claim:relaxed-mwis-dual; the LP-to-MWIS bridge remains open."
    ),
    (
        "Weighted perfect-graph duality remains an explicit external foundation and "
        "is not proved by this project."
    ),
]
EXPECTED_HISTORICAL_SCIENTIFIC_EFFECT = (
    "NONE; only the three claim-to-declaration mappings listed above are promoted. "
    "The closed-form theorem remains unproved."
)
CURRENT_SCIENTIFIC_EFFECT = (
    "NONE; this static run only confirms that the anchored source and historical "
    "record bytes associated with four target-local and three imported declaration "
    "names remain unchanged. It does not type-check or build those declarations, "
    "audit their axioms, reassess mapping correctness or source alignment, modify "
    "the registry, establish scientific acceptance, or prove the closed-form theorem."
)
EXPECTED_REGISTRY_EFFECTS = {
    "claim:sign-alignment-identity": {
        "AgtXIv.Stabilizerness.max_abs_signed_sum"
    },
    "claim:mwis-definition": {
        "AgtXIv.GraphFoundation.independentFinsets",
        "AgtXIv.GraphFoundation.maxWeightIndependent",
    },
    "claim:perfect-graph-definition": {"AgtXIv.GraphFoundation.IsPerfect"},
}

PLACEHOLDER_PATTERN = re.compile(
    r"(?m)^\s*(?:sorry|admit|axiom|constant)\b|"
    r":=\s*(?:sorry|by\s+sorry)\b|"
    r"\bnative_decide\b"
)
AUDIT_ENTRY_PATTERN = re.compile(
    r"(?ms)^'([^']+)' depends on axioms: \[(.*?)\]"
)
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
LEAN_VERSION_PATTERN = re.compile(
    rf"^Lean \(version {re.escape(EXPECTED_LEAN_VERSION)}, .+, "
    rf"commit {EXPECTED_LEAN_GITHASH}, Release\)$"
)
LAKE_VERSION_PATTERN = re.compile(
    rf"^Lake version {re.escape(EXPECTED_LAKE_VERSION)} "
    rf"\(Lean version {re.escape(EXPECTED_LEAN_VERSION)}\)$"
)


CommandRunner = Callable[
    [Sequence[str], Path, Mapping[str, str], int], subprocess.CompletedProcess[str]
]


def sha256(path: Path) -> str:
    """Compatibility helper; security-sensitive reads use `_read_regular_bytes`."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metadata(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _directory_identity(value: os.stat_result) -> tuple[int, int, int]:
    """Identify an opened directory without treating unrelated child churn as replacement."""
    return (value.st_dev, value.st_ino, value.st_mode)


def _lexically_contained(root: Path, path: Path) -> bool:
    try:
        path.absolute().relative_to(root.absolute())
    except ValueError:
        return False
    return True


def _safe_lstat_chain(
    root: Path, path: Path, label: str, errors: list[str]
) -> os.stat_result | None:
    """Inspect every component without following links."""
    root = root.absolute()
    path = path.absolute()
    if not _lexically_contained(root, path):
        errors.append(f"{label} escapes its trusted root: {path}")
        return None
    try:
        root_stat = os.lstat(root)
    except OSError as exc:
        errors.append(f"{label} trusted root cannot be inspected: {exc}")
        return None
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        errors.append(f"{label} trusted root is not a real directory: {root}")
        return None
    current = root
    parts = path.relative_to(root).parts
    if not parts:
        return root_stat
    for index, part in enumerate(parts):
        current /= part
        try:
            value = os.lstat(current)
        except OSError as exc:
            errors.append(f"{label} is missing or inaccessible: {current}: {exc}")
            return None
        if stat.S_ISLNK(value.st_mode):
            errors.append(f"{label} must not contain a symlink: {current}")
            return None
        if index < len(parts) - 1 and not stat.S_ISDIR(value.st_mode):
            errors.append(f"{label} has a non-directory ancestor: {current}")
            return None
    return value


def has_symlink_component(root: Path, path: Path) -> bool:
    errors: list[str] = []
    value = _safe_lstat_chain(root, path, "path", errors)
    return value is None and any("symlink" in error for error in errors)


def _read_regular_bytes(
    root: Path,
    path: Path,
    *,
    label: str,
    max_bytes: int,
    errors: list[str],
) -> bytes | None:
    """Read through a fully revalidated dirfd/openat chain without following links."""
    root = root.absolute()
    path = path.absolute()
    if not _lexically_contained(root, path):
        errors.append(f"{label} escapes its trusted root: {path}")
        return None
    try:
        relative = path.relative_to(root)
    except ValueError:
        errors.append(f"{label} escapes its trusted root: {path}")
        return None
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        errors.append(f"{label} has an unsafe relative path: {relative}")
        return None
    required_flags = ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    if any(not hasattr(os, name) for name in required_flags):
        errors.append(f"{label} cannot be read safely: required openat flags unavailable")
        return None
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    file_flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | os.O_NONBLOCK
        | getattr(os, "O_CLOEXEC", 0)
    )
    anchor = Path(root.anchor)
    if root.anchor != os.sep:
        errors.append(f"{label} requires an absolute POSIX trusted root: {root}")
        return None
    directory_fds: list[int] = []
    chain: list[tuple[int, str, int, tuple[int, int, int]]] = []
    file_fd: int | None = None
    try:
        current_fd = os.open(anchor, directory_flags)
        directory_fds.append(current_fd)
        directory_parts = [*root.parts[1:], *relative.parts[:-1]]
        for part in directory_parts:
            before = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
                errors.append(f"{label} directory component is not a real directory: {part}")
                return None
            child_fd = os.open(part, directory_flags, dir_fd=current_fd)
            opened = os.fstat(child_fd)
            if _directory_identity(before) != _directory_identity(opened):
                errors.append(f"{label} directory component changed during open: {part}")
                os.close(child_fd)
                return None
            chain.append((current_fd, part, child_fd, _directory_identity(before)))
            directory_fds.append(child_fd)
            current_fd = child_fd

        final_name = relative.parts[-1]
        before_file = os.stat(final_name, dir_fd=current_fd, follow_symlinks=False)
        if not stat.S_ISREG(before_file.st_mode) or stat.S_ISLNK(before_file.st_mode):
            errors.append(f"{label} is not a regular file: {path}")
            return None
        if before_file.st_size > max_bytes:
            errors.append(f"{label} exceeds the {max_bytes}-byte safety limit: {path}")
            return None
        file_fd = os.open(final_name, file_flags, dir_fd=current_fd)
        opened_file = os.fstat(file_fd)
        if (
            not stat.S_ISREG(opened_file.st_mode)
            or _metadata(before_file) != _metadata(opened_file)
        ):
            errors.append(f"{label} changed before safe open: {path}")
            return None
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(file_fd, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > max_bytes:
            errors.append(f"{label} exceeded its safety limit while reading: {path}")
            return None
        after_fd = os.fstat(file_fd)
        after_path = os.stat(final_name, dir_fd=current_fd, follow_symlinks=False)
        if (
            _metadata(before_file) != _metadata(after_fd)
            or _metadata(before_file) != _metadata(after_path)
            or len(payload) != before_file.st_size
        ):
            errors.append(f"{label} changed while being read: {path}")
            return None
        for parent_fd, part, child_fd, expected in chain:
            path_state = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            fd_state = os.fstat(child_fd)
            if (
                _directory_identity(path_state) != expected
                or _directory_identity(fd_state) != expected
            ):
                errors.append(f"{label} directory chain changed while reading: {part}")
                return None
        return payload
    except FileNotFoundError as exc:
        errors.append(f"{label} is missing or changed during guarded read: {exc}")
        return None
    except OSError as exc:
        errors.append(f"{label} could not be read through guarded openat: {exc}")
        return None
    finally:
        if file_fd is not None:
            try:
                os.close(file_fd)
            except OSError:
                pass
        for descriptor in reversed(directory_fds):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _process_group_alive(process: subprocess.Popen[bytes]) -> bool:
    if os.name != "posix":
        return process.poll() is None
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    """Best-effort bounded termination, including descendants after leader exit."""
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        elif process.poll() is None:
            process.terminate()
    except OSError:
        pass
    deadline = time.monotonic() + PROCESS_GROUP_GRACE_SECONDS
    while time.monotonic() < deadline and _process_group_alive(process):
        try:
            process.wait(timeout=min(0.1, max(0.0, deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            pass
        if os.name != "posix" and process.poll() is not None:
            break
    if _process_group_alive(process):
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=PROCESS_GROUP_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass


def run_command(
    command: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    """Continuously drain bounded pipes and contain the process group."""
    command_list = list(command)
    try:
        process = subprocess.Popen(
            command_list,
            cwd=cwd,
            env=dict(environment),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name == "posix",
        )
    except OSError as exc:
        return subprocess.CompletedProcess(command_list, 127, "", str(exc))
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    streams = {process.stdout.fileno(): "stdout", process.stderr.fileno(): "stderr"}
    open_fds = set(streams)
    for descriptor in open_fds:
        os.set_blocking(descriptor, False)
        selector.register(descriptor, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout_seconds
    leader_exit_seen: float | None = None
    forced_code: int | None = None
    forced_message = ""
    captured = 0
    try:
        while open_fds:
            now = time.monotonic()
            if now >= deadline:
                forced_code = TIMEOUT_EXIT_CODE
                forced_message = f"command timed out after {timeout_seconds} seconds"
                break
            if process.poll() is not None and leader_exit_seen is None:
                leader_exit_seen = now
            if (
                leader_exit_seen is not None
                and now - leader_exit_seen >= POST_EXIT_DRAIN_SECONDS
                and (_process_group_alive(process) or open_fds)
            ):
                forced_code = BACKGROUND_PROCESS_EXIT_CODE
                forced_message = (
                    "command leader exited while descendants or inherited pipes "
                    "remained active"
                )
                break
            for key, _ in selector.select(
                min(0.1, max(0.0, deadline - now))
            ):
                descriptor = key.fd
                while True:
                    try:
                        chunk = os.read(descriptor, 65536)
                    except BlockingIOError:
                        break
                    if not chunk:
                        selector.unregister(descriptor)
                        open_fds.discard(descriptor)
                        break
                    available = MAX_CAPTURE_BYTES - captured
                    if available > 0:
                        buffers[streams[descriptor]].extend(chunk[:available])
                    captured += len(chunk)
                    if captured > MAX_CAPTURE_BYTES:
                        forced_code = OUTPUT_LIMIT_EXIT_CODE
                        forced_message = (
                            f"command output exceeded {MAX_CAPTURE_BYTES} bytes"
                        )
                        break
                if forced_code is not None:
                    break
            if forced_code is not None:
                break
            if process.poll() is not None and not open_fds:
                if _process_group_alive(process):
                    if leader_exit_seen is None:
                        leader_exit_seen = time.monotonic()
                    continue
                break
    finally:
        selector.close()
    if forced_code is not None:
        _terminate_process_group(process)
    else:
        try:
            process.wait(timeout=PROCESS_GROUP_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            forced_code = BACKGROUND_PROCESS_EXIT_CODE
            forced_message = "command leader did not finish after pipe closure"
            _terminate_process_group(process)
        if (
            forced_code is None
            and os.name == "posix"
            and _process_group_alive(process)
        ):
            forced_code = BACKGROUND_PROCESS_EXIT_CODE
            forced_message = (
                "command leader exited but its original POSIX process group remained active"
            )
            _terminate_process_group(process)
    process.stdout.close()
    process.stderr.close()
    stdout = bytes(buffers["stdout"]).decode("utf-8", errors="surrogateescape")
    stderr = bytes(buffers["stderr"]).decode("utf-8", errors="surrogateescape")
    if forced_message:
        stderr = f"{stderr}\n{forced_message}; process group terminated".strip()
    return subprocess.CompletedProcess(
        command_list,
        forced_code if forced_code is not None else int(process.returncode or 0),
        stdout,
        stderr,
    )


def preloaded_validation_environment(repo: Path) -> dict[str, str]:
    """Build a credential-minimized environment; this is not an egress sandbox."""
    passthrough = {
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TERM",
        "TMPDIR",
        "TZ",
    }
    proxy_policy = {
        "ALL_PROXY",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
        "all_proxy",
        "https_proxy",
        "http_proxy",
        "no_proxy",
    }
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in passthrough or key in proxy_policy
    }
    for key in proxy_policy:
        value = environment.get(key)
        if value and "@" in value:
            environment[key] = "http://127.0.0.1:9"
    git = shutil.which("git", path=os.defpath)
    path_entries = [str(repo / TOOLCHAIN_BIN_RELATIVE), "/usr/bin", "/bin"]
    if git:
        path_entries.insert(1, str(Path(git).resolve().parent))
    environment["PATH"] = os.pathsep.join(dict.fromkeys(path_entries))
    environment["AGTXIV_NETWORK_MODE"] = NETWORK_MODE
    return environment


class DuplicateJSONKeyError(ValueError):
    pass


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJSONKeyError(f"duplicate JSON object key: {key}")
        value[key] = item
    return value


def load_json_object(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_strict_json_object
        )
    except (OSError, json.JSONDecodeError, DuplicateJSONKeyError) as exc:
        errors.append(f"could not read {label}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def validate_evidence_anchor(
    relative: str, repo: Path, errors: list[str], phase: str
) -> bool:
    before = len(errors)
    path = repo / relative
    expected = EXPECTED_EVIDENCE_SHA256[relative]
    if has_symlink_component(repo, path) or not path.is_file():
        errors.append(f"{phase} evidence anchor is missing or not a regular file: {relative}")
    elif sha256(path) != expected:
        errors.append(f"{phase} evidence SHA256 anchor mismatch: {relative}")
    return len(errors) == before


def _safe_artifact_path(relative: object, repo: Path) -> Path | None:
    if not isinstance(relative, str) or not relative:
        return None
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or "\\" in relative
        or "\x00" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        return None
    path = repo.joinpath(*pure.parts)
    try:
        resolved = path.resolve(strict=False)
        root = repo.resolve(strict=True)
    except OSError:
        return None
    return path if resolved.is_relative_to(root) else None


def validate_artifact_hashes(
    evidence: dict[str, Any],
    repo: Path,
    errors: list[str],
    label: str,
    expected_inventory: set[str] | None = None,
) -> bool:
    before = len(errors)
    hashes = evidence.get("artifact_hashes")
    if not isinstance(hashes, dict):
        errors.append(f"{label} artifact_hashes must be an object")
        return False
    if expected_inventory is not None and set(hashes) != expected_inventory:
        missing = sorted(expected_inventory - set(hashes))
        extra = sorted(set(hashes) - expected_inventory)
        errors.append(
            f"{label} artifact inventory mismatch: missing={missing} extra={extra}"
        )
    for relative, expected in sorted(hashes.items(), key=lambda item: str(item[0])):
        path = _safe_artifact_path(relative, repo)
        if path is None:
            errors.append(f"{label} contains an unsafe artifact path: {relative!r}")
            continue
        if not isinstance(expected, str) or not HASH_PATTERN.fullmatch(expected):
            errors.append(f"{label} has an invalid artifact hash: {relative}")
        elif has_symlink_component(repo, path) or not path.is_file():
            errors.append(f"{label} artifact is missing, non-regular, or a symlink: {relative}")
        elif sha256(path) != expected.removeprefix("sha256:"):
            errors.append(f"{label} artifact hash mismatch: {relative}")
    return len(errors) == before


FORMAL_PROJECT_RELATIVES = (
    Path("formal/AgtXIvRootMath"),
    Path("formal/AgtXIvVarela"),
    PROJECT_RELATIVE,
)


def expected_formal_inventory(
    evidences: Mapping[str, dict[str, Any]], repo: Path, errors: list[str]
) -> set[str]:
    inventory = set(EXPECTED_EVIDENCE_SHA256)
    roots = tuple(PurePosixPath(relative.as_posix()) for relative in FORMAL_PROJECT_RELATIVES)
    for label, evidence in evidences.items():
        hashes = evidence.get("artifact_hashes")
        if not isinstance(hashes, dict):
            errors.append(f"{label} cannot define the formal input inventory")
            continue
        for relative in hashes:
            if not isinstance(relative, str):
                errors.append(f"{label} contains a non-string artifact path")
                continue
            pure = PurePosixPath(relative)
            inside_formal_project = any(
                pure != root and pure.is_relative_to(root) for root in roots
            )
            if inside_formal_project:
                if _safe_artifact_path(relative, repo) is None:
                    errors.append(
                        f"{label} cannot define an unsafe formal inventory path: {relative}"
                    )
                    continue
                inventory.add(relative)
            elif relative.startswith("formal/"):
                errors.append(
                    f"{label} artifact is outside the exact formal projects: {relative}"
                )
    return inventory


def formal_input_snapshot(
    repo: Path, expected: set[str], errors: list[str], phase: str
) -> dict[str, str]:
    actual: set[str] = set()
    root_resolved = repo.resolve(strict=True)
    for relative_root in FORMAL_PROJECT_RELATIVES:
        project = repo / relative_root
        if has_symlink_component(repo, project) or not project.is_dir():
            errors.append(f"{phase} formal project root is missing or a symlink: {relative_root}")
            continue
        if not project.resolve(strict=True).is_relative_to(root_resolved):
            errors.append(f"{phase} formal project root escapes repository: {relative_root}")
            continue
        for path in project.rglob("*"):
            relative_to_project = path.relative_to(project)
            if ".lake" in relative_to_project.parts:
                continue
            if path.is_symlink() or path.is_file():
                actual.add(path.relative_to(repo).as_posix())

    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"{phase} formal input inventory is missing files: {missing}")
    if unexpected:
        errors.append(f"{phase} formal input inventory has unexpected files: {unexpected}")

    snapshot: dict[str, str] = {}
    for relative in sorted(actual | expected):
        path = repo / relative
        if has_symlink_component(repo, path):
            errors.append(f"{phase} formal input must not be a symlink: {relative}")
        elif path.is_file() and stat.S_ISREG(path.stat(follow_symlinks=False).st_mode):
            snapshot[relative] = sha256(path)
        elif relative in expected:
            errors.append(f"{phase} formal input is not a regular file: {relative}")
    return snapshot


def scan_placeholders(project: Path, repo: Path, errors: list[str]) -> bool:
    before = len(errors)
    lean_files = sorted(
        path
        for path in project.rglob("*.lean")
        if ".lake" not in path.parts
    )
    if not lean_files:
        errors.append("Stabilizerness project contains no Lean source files")
        return False
    for path in lean_files:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"could not scan Lean source {path}: {exc}")
            continue
        match = PLACEHOLDER_PATTERN.search(source)
        if match:
            line = source.count("\n", 0, match.start()) + 1
            errors.append(
                "placeholder, project axiom, or native_decide found: "
                f"{path.relative_to(repo)}:{line}"
            )
    return len(errors) == before


def package_index(manifest: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    packages = manifest.get("packages")
    if not isinstance(packages, list):
        errors.append("Stabilizerness lake manifest packages must be an array")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for package in packages:
        if not isinstance(package, dict) or not isinstance(package.get("name"), str):
            errors.append("Stabilizerness lake manifest contains an invalid package")
            continue
        name = package["name"]
        if name in result:
            errors.append(f"duplicate package in Stabilizerness lake manifest: {name}")
        result[name] = package
    return result


def resolve_git_executable(errors: list[str]) -> Path | None:
    resolved = next(
        (
            str(candidate)
            for candidate in (Path("/usr/bin/git"), Path("/bin/git"))
            if candidate.is_file() and os.access(candidate, os.X_OK)
        ),
        shutil.which("git", path=os.defpath),
    )
    if not resolved:
        errors.append("Git executable could not be resolved")
        return None
    try:
        path = Path(resolved).resolve(strict=True)
    except OSError as exc:
        errors.append(f"Git executable could not be resolved to a regular file: {exc}")
        return None
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        errors.append(f"resolved Git executable is not executable: {path}")
        return None
    return path


def validate_direct_tool_paths(repo: Path, errors: list[str]) -> dict[str, Path]:
    tools = {"lake": repo / LAKE_RELATIVE, "lean": repo / LEAN_RELATIVE}
    valid: dict[str, Path] = {}
    expected_bin = repo / TOOLCHAIN_BIN_RELATIVE
    for component in (repo / TOOLCHAIN_RELATIVE, expected_bin):
        if has_symlink_component(repo, component) or not component.is_dir():
            errors.append(f"direct toolchain directory is missing or a symlink: {component}")
            return {}
    try:
        expected_bin_resolved = expected_bin.resolve(strict=True)
    except OSError as exc:
        errors.append(f"direct toolchain bin directory cannot be resolved: {exc}")
        return {}
    for name, path in tools.items():
        try:
            mode = path.stat(follow_symlinks=False).st_mode
        except OSError as exc:
            errors.append(f"direct {name} binary is missing: {path}: {exc}")
            continue
        if (
            has_symlink_component(repo, path)
            or not stat.S_ISREG(mode)
            or not os.access(path, os.X_OK)
        ):
            errors.append(
                f"direct {name} binary must be a regular executable, not a symlink: {path}"
            )
            continue
        resolved = path.resolve(strict=True)
        if resolved.parent != expected_bin_resolved or resolved.name != name:
            errors.append(f"direct {name} binary escapes exact toolchain bin: {resolved}")
            continue
        valid[name] = path
    return valid


def validate_tool_identity(
    tools: Mapping[str, Path],
    repo: Path,
    environment: Mapping[str, str],
    command_runner: CommandRunner,
    errors: list[str],
    phase: str,
) -> dict[str, str]:
    if set(tools) != {"lean", "lake"}:
        return {}
    commands = {
        "lean_githash": [str(tools["lean"]), "--githash"],
        "lean_version": [str(tools["lean"]), "--version"],
        "lake_version": [str(tools["lake"]), "--version"],
    }
    outputs: dict[str, str] = {}
    for name, command in commands.items():
        try:
            completed = command_runner(
                command, repo, environment, VERSION_TIMEOUT_SECONDS
            )
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(f"{phase} tool identity command failed for {name}: {exc}")
            continue
        outputs[name] = (completed.stdout or "").strip()
        if completed.returncode != 0:
            errors.append(
                f"{phase} tool identity command returned {completed.returncode}: {name}"
            )
    if outputs.get("lean_githash") != EXPECTED_LEAN_GITHASH:
        errors.append(f"{phase} Lean githash is not the pinned commit")
    if not LEAN_VERSION_PATTERN.fullmatch(outputs.get("lean_version", "")):
        errors.append(f"{phase} Lean version identity is not exact")
    if not LAKE_VERSION_PATTERN.fullmatch(outputs.get("lake_version", "")):
        errors.append(f"{phase} Lake version identity is not exact")
    return outputs


def validate_git_checkout(
    path: Path,
    *,
    expected_origin: str,
    expected_commit: str,
    expected_tree: str,
    label: str,
    git_executable: Path,
    repo: Path,
    environment: Mapping[str, str],
    command_runner: CommandRunner,
    errors: list[str],
    phase: str,
) -> dict[str, str]:
    if (
        has_symlink_component(repo, path)
        or not path.is_dir()
        or has_symlink_component(repo, path / ".git")
        or not (path / ".git").is_dir()
    ):
        errors.append(f"{phase} pinned Git checkout missing or a symlink: {label}")
        return {}
    commands = {
        "origin": [
            str(git_executable),
            "-C",
            str(path),
            "config",
            "--get",
            "remote.origin.url",
        ],
        "head": [str(git_executable), "-C", str(path), "rev-parse", "HEAD"],
        "tree": [
            str(git_executable),
            "-C",
            str(path),
            "rev-parse",
            "HEAD^{tree}",
        ],
        "status": [
            str(git_executable),
            "-C",
            str(path),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
    }
    outputs: dict[str, str] = {}
    for name, command in commands.items():
        try:
            completed = command_runner(
                command, repo, environment, GIT_TIMEOUT_SECONDS
            )
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(f"{phase} Git inspection failed for {label}/{name}: {exc}")
            continue
        outputs[name] = (completed.stdout or "").strip()
        if completed.returncode != 0:
            errors.append(
                f"{phase} Git inspection returned {completed.returncode}: {label}/{name}"
            )
    if outputs.get("origin") != expected_origin:
        errors.append(f"{phase} pinned Git origin mismatch: {label}")
    if outputs.get("head") != expected_commit:
        errors.append(f"{phase} pinned Git commit mismatch: {label}")
    if outputs.get("tree") != expected_tree:
        errors.append(f"{phase} pinned Git tree mismatch: {label}")
    if outputs.get("status"):
        errors.append(f"{phase} pinned Git checkout is not clean: {label}")
    return outputs


def validate_git_dependencies(
    repo: Path,
    git_executable: Path | None,
    environment: Mapping[str, str],
    command_runner: CommandRunner,
    errors: list[str],
    phase: str,
) -> dict[str, dict[str, str]]:
    if git_executable is None:
        return {}
    identities: dict[str, dict[str, str]] = {}
    packages_root = repo / "formal/AgtXIvRootMath/.lake/packages"
    for name, expected in sorted(EXPECTED_GIT_PACKAGES.items()):
        identities[name] = validate_git_checkout(
            packages_root / name,
            expected_origin=expected["origin"],
            expected_commit=expected["revision"],
            expected_tree=expected["tree"],
            label=f"lake package {name}",
            git_executable=git_executable,
            repo=repo,
            environment=environment,
            command_runner=command_runner,
            errors=errors,
            phase=phase,
        )
    identities["LeanQuantum"] = validate_git_checkout(
        repo / "Reference/LeanQuantum",
        expected_origin=EXPECTED_QUANTUMLIB_ORIGIN,
        expected_commit=EXPECTED_QUANTUMLIB_COMMIT,
        expected_tree=EXPECTED_QUANTUMLIB_TREE,
        label="LeanQuantum",
        git_executable=git_executable,
        repo=repo,
        environment=environment,
        command_runner=command_runner,
        errors=errors,
        phase=phase,
    )
    return identities


def validate_environment(
    evidence: dict[str, Any],
    root_evidence: dict[str, Any],
    varela_evidence: dict[str, Any],
    repo: Path,
    errors: list[str],
) -> bool:
    before = len(errors)
    project = repo / PROJECT_RELATIVE
    environment = evidence.get("environment")
    if not isinstance(environment, dict):
        errors.append("verification evidence environment must be an object")
        environment = {}
    expected_environment = {
        "lean_toolchain": EXPECTED_TOOLCHAIN,
        "mathlib_commit": EXPECTED_MATHLIB_COMMIT,
        "root_math_project": "formal/AgtXIvRootMath",
        "varela_project": "formal/AgtXIvVarela",
    }
    if environment != expected_environment:
        errors.append("verification evidence environment binding is not exact")

    toolchain_path = project / "lean-toolchain"
    try:
        toolchain = toolchain_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        errors.append(f"could not read Stabilizerness lean-toolchain: {exc}")
        toolchain = None
    if toolchain != EXPECTED_TOOLCHAIN:
        errors.append("Stabilizerness lean-toolchain does not match pinned evidence")

    manifest = load_json_object(
        project / "lake-manifest.json", "Stabilizerness lake manifest", errors
    )
    if manifest.get("name") != "AgtXIvStabilizerness":
        errors.append("Stabilizerness lake manifest has the wrong project name")
    if manifest.get("packagesDir") != "../AgtXIvRootMath/.lake/packages":
        errors.append("Stabilizerness lake manifest has an unpinned packagesDir")
    packages = package_index(manifest, errors)
    if set(packages) != EXPECTED_PACKAGE_NAMES:
        errors.append("Stabilizerness lake package inventory is not exact")
    expected_path_packages = {
        "AgtXIvRootMath": "../AgtXIvRootMath",
        "AgtXIvVarela": "../AgtXIvVarela",
    }
    for name, expected_dir in expected_path_packages.items():
        package = packages.get(name, {})
        if package.get("type") != "path" or package.get("dir") != expected_dir:
            errors.append(f"Stabilizerness lake dependency is not exact: {name}")
    quantumlib = packages.get("quantumlib", {})
    if (
        quantumlib.get("type") != "path"
        or quantumlib.get("dir")
        != "../AgtXIvVarela/../AgtXIvRootMath/../../Reference/LeanQuantum"
    ):
        errors.append("Stabilizerness Quantumlib path dependency is not exact")
    for name, expected in EXPECTED_GIT_PACKAGES.items():
        package = packages.get(name, {})
        if (
            package.get("type") != "git"
            or package.get("url") != expected["origin"]
            or package.get("rev") != expected["revision"]
            or package.get("inputRev") != expected["input_revision"]
        ):
            errors.append(f"Stabilizerness Git manifest binding is not exact: {name}")

    for relative in ("formal/AgtXIvRootMath", "formal/AgtXIvVarela"):
        dependency = repo / relative
        if not dependency.is_dir():
            errors.append(f"local Lean dependency project missing: {relative}")
            continue
        dependency_toolchain = dependency / "lean-toolchain"
        try:
            value = dependency_toolchain.read_text(encoding="utf-8").strip()
        except OSError as exc:
            errors.append(f"could not read {relative}/lean-toolchain: {exc}")
            continue
        if value != EXPECTED_TOOLCHAIN:
            errors.append(f"local Lean dependency toolchain mismatch: {relative}")

    root_environment = root_evidence.get("environment", {})
    if (
        root_evidence.get("id") != "lean-verification:root-math:2026-08-16"
        or root_evidence.get("root_math_status") != "ROOT_MATH_KERNEL_COMPLETE"
        or not isinstance(root_environment, dict)
        or root_environment.get("lean_toolchain") != EXPECTED_TOOLCHAIN
        or root_environment.get("mathlib_commit") != EXPECTED_MATHLIB_COMMIT
        or root_environment.get("quantumlib_commit") != EXPECTED_QUANTUMLIB_COMMIT
    ):
        errors.append("RootMath dependency evidence binding is not exact")

    varela_environment = varela_evidence.get("environment", {})
    if (
        varela_evidence.get("id") != "lean-verification:varela-vrep:2026-08-16"
        or varela_evidence.get("vrep_status")
        != "PARTIALLY_FORMALIZED_EXPLICIT_OBLIGATIONS"
        or not isinstance(varela_environment, dict)
        or varela_environment.get("lean_toolchain") != EXPECTED_TOOLCHAIN
        or varela_environment.get("mathlib_commit") != EXPECTED_MATHLIB_COMMIT
        or varela_environment.get("quantumlib_commit") != EXPECTED_QUANTUMLIB_COMMIT
    ):
        errors.append("Varela dependency evidence binding is not exact")

    return len(errors) == before


def validate_evidence_semantics(
    evidence: dict[str, Any], errors: list[str]
) -> bool:
    before = len(errors)
    expected_scalars = {
        "schema_version": EXPECTED_HISTORICAL_SCHEMA_VERSION,
        "id": EXPECTED_EVIDENCE_ID,
        "project": PROJECT_RELATIVE.as_posix(),
        "status": EXPECTED_STATUS,
        "scientific_acceptance_effect": EXPECTED_HISTORICAL_SCIENTIFIC_EFFECT,
    }
    for key, expected in expected_scalars.items():
        if evidence.get(key) != expected:
            errors.append(f"verification evidence has unexpected {key}")
    if evidence.get("commands") != EXPECTED_COMMANDS:
        errors.append("verification evidence command inventory is not exact")

    def declared_exact_array(key: str, expected: set[str]) -> None:
        value = evidence.get(key)
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            errors.append(f"verification evidence {key} must be a string array")
            return
        duplicates = sorted(item for item, count in Counter(value).items() if count > 1)
        if duplicates:
            errors.append(f"verification evidence {key} contains duplicates: {duplicates}")
        missing = sorted(expected - set(value))
        unexpected = sorted(set(value) - expected)
        if len(value) != len(expected) or missing or unexpected:
            errors.append(
                f"verification evidence {key} is not exact: expected_count={len(expected)} "
                f"actual_count={len(value)} missing={missing} unexpected={unexpected}"
            )

    declared_exact_array("target_local_declarations", LOCAL_DECLARATIONS)
    declared_exact_array(
        "reused_imported_declarations_audited_here", IMPORTED_DECLARATIONS
    )
    if evidence.get("scope_limitations") != EXPECTED_SCOPE_LIMITATIONS:
        errors.append("verification evidence scope limitations are not exact")

    effects = evidence.get("registry_claim_effects")
    found_effects: dict[str, set[str]] = {}
    if not isinstance(effects, list):
        errors.append("verification evidence registry_claim_effects must be an array")
    else:
        if len(effects) != len(EXPECTED_REGISTRY_EFFECTS):
            errors.append(
                "verification evidence registry_claim_effects cardinality is not exact"
            )
        for effect in effects:
            if not isinstance(effect, dict):
                errors.append("verification evidence contains an invalid registry effect")
                continue
            node = effect.get("dag_node_id")
            if not isinstance(node, str) or node in found_effects:
                errors.append(f"invalid or duplicate registry effect: {node!r}")
                continue
            if effect.get("effect") != "PROMOTE_TO_EXISTING_PROJECT_DECLARATIONS":
                errors.append(f"registry effect has an invalid promotion kind: {node}")
            declarations = effect.get("declarations")
            if declarations is None:
                declarations = [effect.get("declaration")]
            if not isinstance(declarations, list) or not all(
                isinstance(item, str) for item in declarations
            ):
                errors.append(f"registry effect has invalid declarations: {node}")
                continue
            duplicates = sorted(
                item for item, count in Counter(declarations).items() if count > 1
            )
            if duplicates:
                errors.append(
                    f"registry effect contains duplicate declarations: {node}: {duplicates}"
                )
            expected_declarations = EXPECTED_REGISTRY_EFFECTS.get(node, set())
            if len(declarations) != len(expected_declarations):
                errors.append(
                    f"registry effect declaration cardinality is not exact: {node}"
                )
            if set(declarations) != expected_declarations:
                errors.append(f"registry effect declarations are not exact: {node}")
            found_effects[node] = set(declarations)
    if found_effects != EXPECTED_REGISTRY_EFFECTS:
        errors.append("verification evidence registry claim effects are not exact")

    results = evidence.get("results")
    if not isinstance(results, dict):
        errors.append("verification evidence results must be an object")
        results = {}
    if results.get("kernel_build") != "PASSED (8408 jobs)":
        errors.append("historical verification record kernel build result is not exact")
    if results.get("placeholder_scan") != (
        "PASSED (no sorry, admit, project axiom, or native_decide in target "
        "project declarations)"
    ):
        errors.append("historical verification record placeholder result is not exact")
    axiom_audit = results.get("axiom_audit")
    if not isinstance(axiom_audit, dict):
        errors.append("historical verification record lacks axiom_audit")
    else:
        if axiom_audit.get("result") != "PASSED":
            errors.append("historical verification record axiom audit did not pass")
        dependencies = axiom_audit.get("reported_standard_dependencies")
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) for item in dependencies
        ):
            errors.append(
                "historical verification record standard axiom set must be a string array"
            )
            dependencies = []
        if len(dependencies) != len(ALLOWED_AXIOMS) or set(dependencies) != ALLOWED_AXIOMS:
            errors.append("historical verification record standard axiom set is not exact")
        if len(dependencies) != len(set(dependencies)):
            errors.append("historical verification record standard axiom set has duplicates")
        if axiom_audit.get("forbidden_dependencies") != []:
            errors.append("historical verification record contains forbidden axioms")
    return len(errors) == before


def parse_axiom_audit(output: str, errors: list[str]) -> dict[str, set[str]]:
    entries = AUDIT_ENTRY_PATTERN.findall(output)
    counts = Counter(declaration for declaration, _ in entries)
    duplicates = sorted(declaration for declaration, count in counts.items() if count > 1)
    if duplicates:
        errors.append(f"Lean axiom audit repeated declarations: {duplicates}")
    parsed: dict[str, set[str]] = {}
    for declaration, payload in entries:
        axioms = {
            item.strip()
            for item in payload.replace("\n", " ").split(",")
            if item.strip()
        }
        parsed[declaration] = axioms
    found = set(parsed)
    missing = sorted(ALL_DECLARATIONS - found)
    unexpected = sorted(found - ALL_DECLARATIONS)
    if missing:
        errors.append(f"Lean axiom audit missing declarations: {missing}")
    if unexpected:
        errors.append(f"Lean axiom audit reported unexpected declarations: {unexpected}")
    for declaration, axioms in sorted(parsed.items()):
        unexpected_axioms = sorted(axioms - ALLOWED_AXIOMS)
        if unexpected_axioms:
            errors.append(
                f"unexpected axioms for {declaration}: {unexpected_axioms}"
            )
    if "sorryAx" in output:
        errors.append("Lean axiom audit found sorryAx")
    return parsed


def failure_excerpt(output: str, limit: int = 40) -> list[str]:
    pattern = re.compile(
        r"(?:✖|\berror\b|\bfail(?:ed|ure)?\b|killed|signal|resource|cannot)",
        re.IGNORECASE,
    )
    return [line[:1000] for line in output.splitlines() if pattern.search(line)][:limit]


# Hardened implementation below intentionally supersedes the prototype helpers above.
# Keeping the historical pure semantic checks local makes the diff reviewable while all
# filesystem and process operations used by `validate` go through the guarded helpers.


def _parse_json_bytes(payload: bytes, label: str, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_strict_json_object
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJSONKeyError) as exc:
        errors.append(f"could not parse {label}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def _read_evidence_anchors(
    repo: Path, errors: list[str], phase: str
) -> tuple[dict[str, bytes], dict[str, dict[str, Any]]]:
    payloads: dict[str, bytes] = {}
    valid = True
    for relative, expected in EXPECTED_EVIDENCE_SHA256.items():
        payload = _read_regular_bytes(
            repo,
            repo / relative,
            label=f"{phase} evidence anchor {relative}",
            max_bytes=MAX_JSON_BYTES,
            errors=errors,
        )
        if payload is None:
            valid = False
            continue
        if hashlib.sha256(payload).hexdigest() != expected:
            errors.append(f"{phase} evidence SHA256 anchor mismatch: {relative}")
            valid = False
            continue
        payloads[relative] = payload
    if not valid or set(payloads) != set(EXPECTED_EVIDENCE_SHA256):
        errors.append(
            f"{phase} evidence JSON was not parsed because every exact anchor did not pass"
        )
        return payloads, {}
    evidences = {
        relative: _parse_json_bytes(payloads[relative], relative, errors)
        for relative in EXPECTED_EVIDENCE_SHA256
    }
    return payloads, evidences


def _validated_relative_path(
    relative: object,
    repo: Path,
    *,
    label: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{label} is not a non-empty string path: {relative!r}")
        return None
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or "\\" in relative
        or "\x00" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        errors.append(f"{label} is unsafe: {relative!r}")
        return None
    path = repo.joinpath(*pure.parts)
    if not _lexically_contained(repo, path):
        errors.append(f"{label} escapes repository: {relative!r}")
        return None
    return path


def _formal_project_for(relative: str) -> Path | None:
    pure = PurePosixPath(relative)
    for project in FORMAL_PROJECT_RELATIVES:
        root = PurePosixPath(project.as_posix())
        if pure == root or pure.is_relative_to(root):
            return project
    return None


def _validate_artifacts_guarded(
    evidences: Mapping[str, dict[str, Any]],
    repo: Path,
    errors: list[str],
    phase: str,
) -> tuple[dict[str, bytes], set[str]]:
    payloads: dict[str, bytes] = {}
    formal_inventory = set(EXPECTED_EVIDENCE_SHA256)
    labels = {
        RESULT_RELATIVE.as_posix(): "Stabilizerness verification evidence",
        "formal/AgtXIvRootMath/verification-result.json": "RootMath verification evidence",
        "formal/AgtXIvVarela/verification-result.json": "Varela verification evidence",
    }
    for evidence_relative, label in labels.items():
        evidence = evidences.get(evidence_relative, {})
        hashes = evidence.get("artifact_hashes")
        if not isinstance(hashes, dict):
            errors.append(f"{phase} {label} artifact_hashes must be an object")
            continue
        if evidence_relative == RESULT_RELATIVE.as_posix() and set(hashes) != REQUIRED_ARTIFACTS:
            errors.append(
                f"{phase} Stabilizerness artifact inventory mismatch: "
                f"missing={sorted(REQUIRED_ARTIFACTS - set(hashes))} "
                f"extra={sorted(set(hashes) - REQUIRED_ARTIFACTS)}"
            )
        for relative, expected in sorted(hashes.items(), key=lambda item: str(item[0])):
            path = _validated_relative_path(
                relative,
                repo,
                label=f"{phase} {label} artifact path",
                errors=errors,
            )
            if path is None:
                continue
            project = _formal_project_for(relative)
            if project is not None:
                project_pure = PurePosixPath(project.as_posix())
                if PurePosixPath(relative) == project_pure:
                    errors.append(f"{phase} artifact names a project directory: {relative}")
                else:
                    formal_inventory.add(relative)
            elif relative.startswith("formal/"):
                errors.append(
                    f"{phase} artifact is outside the exact formal projects: {relative}"
                )
            if not isinstance(expected, str) or not HASH_PATTERN.fullmatch(expected):
                errors.append(f"{phase} {label} has invalid artifact hash: {relative}")
                continue
            payload = _read_regular_bytes(
                repo,
                path,
                label=f"{phase} artifact {relative}",
                max_bytes=MAX_FORMAL_FILE_BYTES,
                errors=errors,
            )
            if payload is None:
                continue
            if hashlib.sha256(payload).hexdigest() != expected.removeprefix("sha256:"):
                errors.append(f"{phase} {label} artifact hash mismatch: {relative}")
                continue
            payloads[relative] = payload
    return payloads, formal_inventory


def _walk_formal_project(
    repo: Path,
    project_relative: Path,
    errors: list[str],
    phase: str,
) -> dict[str, bytes]:
    project = repo / project_relative
    root_stat = _safe_lstat_chain(
        repo, project, f"{phase} formal project root {project_relative}", errors
    )
    if root_stat is None or not stat.S_ISDIR(root_stat.st_mode):
        if root_stat is not None:
            errors.append(f"{phase} formal project root is not a directory: {project_relative}")
        return {}
    found: dict[str, bytes] = {}

    def visit(directory: Path, at_project_root: bool = False) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            errors.append(f"{phase} could not enumerate formal directory {directory}: {exc}")
            return
        for entry in entries:
            path = Path(entry.path)
            try:
                value = entry.stat(follow_symlinks=False)
            except OSError as exc:
                errors.append(f"{phase} could not lstat formal input {path}: {exc}")
                continue
            relative = path.relative_to(repo).as_posix()
            if at_project_root and entry.name == ".lake":
                if stat.S_ISDIR(value.st_mode) and not stat.S_ISLNK(value.st_mode):
                    continue
                errors.append(
                    f"{phase} approved root .lake cache must be a real directory: {relative}"
                )
                continue
            if stat.S_ISLNK(value.st_mode):
                errors.append(f"{phase} formal input must not be a symlink: {relative}")
            elif stat.S_ISDIR(value.st_mode):
                visit(path)
            elif stat.S_ISREG(value.st_mode):
                payload = _read_regular_bytes(
                    repo,
                    path,
                    label=f"{phase} formal input {relative}",
                    max_bytes=MAX_FORMAL_FILE_BYTES,
                    errors=errors,
                )
                if payload is not None:
                    found[relative] = payload
            else:
                errors.append(
                    f"{phase} formal input is a forbidden special file: {relative}"
                )

    visit(project, True)
    return found


def _formal_snapshot_guarded(
    repo: Path, expected: set[str], errors: list[str], phase: str
) -> tuple[dict[str, str], dict[str, bytes]]:
    payloads: dict[str, bytes] = {}
    for project in FORMAL_PROJECT_RELATIVES:
        payloads.update(_walk_formal_project(repo, project, errors, phase))
    actual = set(payloads)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"{phase} formal input inventory is missing files: {missing}")
    if unexpected:
        errors.append(f"{phase} formal input inventory has unexpected files: {unexpected}")
    return (
        {relative: hashlib.sha256(payload).hexdigest() for relative, payload in payloads.items()},
        payloads,
    )


def _scan_expected_placeholders(
    expected_inventory: set[str], payloads: Mapping[str, bytes], errors: list[str]
) -> bool:
    before = len(errors)
    expected_lean = sorted(relative for relative in expected_inventory if relative.endswith(".lean"))
    if not expected_lean:
        errors.append("formal evidence inventory contains no expected Lean source files")
        return False
    for relative in expected_lean:
        payload = payloads.get(relative)
        if payload is None:
            errors.append(f"expected Lean source was not safely read: {relative}")
            continue
        try:
            source = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"expected Lean source is not UTF-8: {relative}: {exc}")
            continue
        match = PLACEHOLDER_PATTERN.search(source)
        if match:
            line = source.count("\n", 0, match.start()) + 1
            errors.append(
                f"placeholder, project axiom, constant, or native_decide found: {relative}:{line}"
            )
    return len(errors) == before


def _text_artifact(
    payloads: Mapping[str, bytes], relative: str, label: str, errors: list[str]
) -> str:
    payload = payloads.get(relative)
    if payload is None:
        errors.append(f"validated artifact payload unavailable: {label}")
        return ""
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{label} is not UTF-8: {exc}")
        return ""


def _validate_environment_guarded(
    evidence: dict[str, Any],
    root_evidence: dict[str, Any],
    varela_evidence: dict[str, Any],
    artifact_payloads: Mapping[str, bytes],
    errors: list[str],
) -> tuple[bool, dict[str, Any]]:
    before = len(errors)
    expected_environment = {
        "lean_toolchain": EXPECTED_TOOLCHAIN,
        "mathlib_commit": EXPECTED_MATHLIB_COMMIT,
        "root_math_project": "formal/AgtXIvRootMath",
        "varela_project": "formal/AgtXIvVarela",
    }
    if evidence.get("environment") != expected_environment:
        errors.append("verification evidence environment binding is not exact")
    for relative in (
        "formal/AgtXIvStabilizerness/lean-toolchain",
        "formal/AgtXIvRootMath/lean-toolchain",
        "formal/AgtXIvVarela/lean-toolchain",
    ):
        if _text_artifact(artifact_payloads, relative, relative, errors).strip() != EXPECTED_TOOLCHAIN:
            errors.append(f"local Lean dependency toolchain mismatch: {relative}")
    manifest_relative = "formal/AgtXIvStabilizerness/lake-manifest.json"
    manifest_payload = artifact_payloads.get(manifest_relative)
    manifest = (
        _parse_json_bytes(manifest_payload, "Stabilizerness lake manifest", errors)
        if manifest_payload is not None
        else {}
    )
    if manifest.get("name") != "AgtXIvStabilizerness":
        errors.append("Stabilizerness lake manifest has the wrong project name")
    if manifest.get("packagesDir") != "../AgtXIvRootMath/.lake/packages":
        errors.append("Stabilizerness lake manifest has an unpinned packagesDir")
    packages = package_index(manifest, errors)
    if set(packages) != EXPECTED_PACKAGE_NAMES:
        errors.append("Stabilizerness lake package inventory is not exact")
    for name, expected_dir in {
        "AgtXIvRootMath": "../AgtXIvRootMath",
        "AgtXIvVarela": "../AgtXIvVarela",
    }.items():
        package = packages.get(name, {})
        if package.get("type") != "path" or package.get("dir") != expected_dir:
            errors.append(f"Stabilizerness lake dependency is not exact: {name}")
    quantumlib = packages.get("quantumlib", {})
    if (
        quantumlib.get("type") != "path"
        or quantumlib.get("dir")
        != "../AgtXIvVarela/../AgtXIvRootMath/../../Reference/LeanQuantum"
    ):
        errors.append("Stabilizerness Quantumlib path dependency is not exact")
    for name, expected in EXPECTED_GIT_PACKAGES.items():
        package = packages.get(name, {})
        if (
            package.get("type") != "git"
            or package.get("url") != expected["origin"]
            or package.get("rev") != expected["revision"]
            or package.get("inputRev") != expected["input_revision"]
        ):
            errors.append(f"Stabilizerness Git manifest binding is not exact: {name}")
    root_environment = root_evidence.get("environment")
    if (
        root_evidence.get("id") != "lean-verification:root-math:2026-08-16"
        or root_evidence.get("root_math_status") != "ROOT_MATH_KERNEL_COMPLETE"
        or not isinstance(root_environment, dict)
        or root_environment.get("lean_toolchain") != EXPECTED_TOOLCHAIN
        or root_environment.get("mathlib_commit") != EXPECTED_MATHLIB_COMMIT
        or root_environment.get("quantumlib_commit") != EXPECTED_QUANTUMLIB_COMMIT
    ):
        errors.append("RootMath dependency evidence binding is not exact")
    varela_environment = varela_evidence.get("environment")
    if (
        varela_evidence.get("id") != "lean-verification:varela-vrep:2026-08-16"
        or varela_evidence.get("vrep_status")
        != "PARTIALLY_FORMALIZED_EXPLICIT_OBLIGATIONS"
        or not isinstance(varela_environment, dict)
        or varela_environment.get("lean_toolchain") != EXPECTED_TOOLCHAIN
        or varela_environment.get("mathlib_commit") != EXPECTED_MATHLIB_COMMIT
        or varela_environment.get("quantumlib_commit") != EXPECTED_QUANTUMLIB_COMMIT
    ):
        errors.append("Varela dependency evidence binding is not exact")
    return len(errors) == before, manifest


def resolve_git_executable(errors: list[str]) -> Path | None:
    """Resolve Git only from fixed system candidates, never ambient PATH."""
    for candidate in (Path("/usr/bin/git"), Path("/bin/git")):
        try:
            value = os.lstat(candidate)
        except OSError:
            continue
        if stat.S_ISREG(value.st_mode) and not stat.S_ISLNK(value.st_mode) and os.access(
            candidate, os.X_OK
        ):
            return candidate
    errors.append("trusted fixed Git executable /usr/bin/git or /bin/git is unavailable")
    return None


def validate_direct_tool_paths(repo: Path, errors: list[str]) -> dict[str, Path]:
    tools = {"lake": repo / LAKE_RELATIVE, "lean": repo / LEAN_RELATIVE}
    valid: dict[str, Path] = {}
    bin_path = repo / TOOLCHAIN_BIN_RELATIVE
    bin_stat = _safe_lstat_chain(repo, bin_path, "direct toolchain bin", errors)
    if bin_stat is None or not stat.S_ISDIR(bin_stat.st_mode):
        if bin_stat is not None:
            errors.append("direct toolchain bin is not a real directory")
        return {}
    for name, path in tools.items():
        value = _safe_lstat_chain(repo, path, f"direct {name} binary", errors)
        if value is None:
            continue
        if not stat.S_ISREG(value.st_mode) or not os.access(path, os.X_OK):
            errors.append(
                f"direct {name} binary must be a regular executable, not a symlink: {path}"
            )
            continue
        if path.parent != bin_path or path.name != name:
            errors.append(f"direct {name} binary is outside the exact toolchain bin")
            continue
        valid[name] = path
    return valid


def _git_environment(environment: Mapping[str, str]) -> dict[str, str]:
    value = dict(environment)
    value.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_PAGER": "cat",
        }
    )
    return value


def _read_git_origin_config(
    repo: Path,
    checkout: Path,
    expected_origin: str,
    label: str,
    errors: list[str],
) -> str | None:
    checkout_stat = _safe_lstat_chain(repo, checkout, f"Git checkout {label}", errors)
    if checkout_stat is None or not stat.S_ISDIR(checkout_stat.st_mode):
        if checkout_stat is not None:
            errors.append(f"Git checkout is not a real directory: {label}")
        return None
    dot_git = checkout / ".git"
    dot_git_stat = _safe_lstat_chain(repo, dot_git, f"Git metadata {label}", errors)
    if dot_git_stat is None or not stat.S_ISDIR(dot_git_stat.st_mode):
        if dot_git_stat is not None:
            errors.append(f"Git metadata must be a real directory: {label}")
        return None
    config_path = dot_git / "config"
    payload = _read_regular_bytes(
        repo,
        config_path,
        label=f"Git config {label}",
        max_bytes=MAX_JSON_BYTES,
        errors=errors,
    )
    if payload is None:
        return None
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"Git config is not UTF-8 for {label}: {exc}")
        return None
    parser = configparser.RawConfigParser(interpolation=None, strict=True)
    parser.optionxform = str.lower
    try:
        parser.read_string(text)
    except configparser.Error as exc:
        errors.append(f"Git config could not be parsed safely for {label}: {exc}")
        return None
    dangerous_sections = ("include", "includeif", "filter ", "diff ", "merge ", "credential")
    dangerous_core = {
        "fsmonitor",
        "hookspath",
        "attributesfile",
        "sshcommand",
        "askpass",
    }
    for section in parser.sections():
        lowered = section.lower()
        if lowered.startswith(dangerous_sections):
            errors.append(f"Git config contains forbidden executable/include section: {label}/{section}")
        if lowered == "core":
            present = dangerous_core & set(parser[section])
            if present:
                errors.append(
                    f"Git config contains forbidden core options for {label}: {sorted(present)}"
                )
    origin_section = next(
        (section for section in parser.sections() if section.lower() == 'remote "origin"'),
        None,
    )
    origin = parser.get(origin_section, "url", fallback=None) if origin_section else None
    if origin != expected_origin:
        errors.append(f"pinned Git origin mismatch: {label}")
    for forbidden in (dot_git / "info/grafts",):
        try:
            forbidden_stat = os.lstat(forbidden)
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"could not inspect forbidden Git override {forbidden}: {exc}")
            continue
        if forbidden_stat:
            errors.append(f"forbidden Git graft override exists: {label}")
    return origin


def _prepare_git_checkouts(repo: Path, errors: list[str]) -> dict[str, dict[str, Any]]:
    prepared: dict[str, dict[str, Any]] = {}
    packages_root = repo / "formal/AgtXIvRootMath/.lake/packages"
    for name, expected in sorted(EXPECTED_GIT_PACKAGES.items()):
        label = f"lake package {name}"
        checkout = packages_root / name
        origin = _read_git_origin_config(
            repo, checkout, expected["origin"], label, errors
        )
        prepared[label] = {
            "path": checkout,
            "origin": origin,
            "expected_origin": expected["origin"],
            "expected_commit": expected["revision"],
            "expected_tree": expected["tree"],
        }
    checkout = repo / "Reference/LeanQuantum"
    origin = _read_git_origin_config(
        repo, checkout, EXPECTED_QUANTUMLIB_ORIGIN, "LeanQuantum", errors
    )
    prepared["LeanQuantum"] = {
        "path": checkout,
        "origin": origin,
        "expected_origin": EXPECTED_QUANTUMLIB_ORIGIN,
        "expected_commit": EXPECTED_QUANTUMLIB_COMMIT,
        "expected_tree": EXPECTED_QUANTUMLIB_TREE,
    }
    return prepared


def _git_command(git: Path, checkout: Path, arguments: Sequence[str]) -> list[str]:
    return [
        str(git),
        "--no-replace-objects",
        "--no-pager",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.attributesFile=/dev/null",
        "-c",
        "protocol.file.allow=never",
        "-C",
        str(checkout),
        *arguments,
    ]


def _parse_ls_tree(
    output: str, label: str, errors: list[str], phase: str
) -> dict[str, tuple[str, str]]:
    manifest: dict[str, tuple[str, str]] = {}
    for record in output.split("\x00"):
        if not record:
            continue
        try:
            header, relative = record.split("\t", 1)
            mode, object_type, object_id = header.split(" ", 2)
        except ValueError:
            errors.append(f"{phase} malformed git ls-tree record for {label}")
            continue
        if object_type != "blob" or mode not in {"100644", "100755"}:
            errors.append(
                f"{phase} unsupported tracked Git entry for {label}: {mode} {object_type} {relative!r}"
            )
            continue
        if not re.fullmatch(r"[0-9a-f]{40}", object_id):
            errors.append(f"{phase} invalid Git blob id for {label}: {relative!r}")
            continue
        if any(0xDC80 <= ord(character) <= 0xDCFF for character in relative):
            errors.append(f"{phase} non-UTF-8 Git path rejected for {label}")
            continue
        pure = PurePosixPath(relative)
        if (
            pure.is_absolute()
            or "\\" in relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))
            or pure.parts[0] in {".git", ".lake"}
        ):
            errors.append(f"{phase} unsafe Git tree path for {label}: {relative!r}")
            continue
        if relative in manifest:
            errors.append(f"{phase} duplicate Git tree path for {label}: {relative!r}")
            continue
        manifest[relative] = (mode, object_id)
    return manifest


def _inspect_git_external(
    prepared: Mapping[str, dict[str, Any]],
    git: Path,
    repo: Path,
    environment: Mapping[str, str],
    runner: CommandRunner,
    errors: list[str],
    phase: str,
) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, tuple[str, str]]]]:
    identities: dict[str, dict[str, str]] = {}
    manifests: dict[str, dict[str, tuple[str, str]]] = {}
    git_environment = _git_environment(environment)
    for label, checkout in prepared.items():
        expected_commit = checkout["expected_commit"]
        commands = {
            "head": ["rev-parse", "--verify", "HEAD"],
            "tree": ["rev-parse", "--verify", f"{expected_commit}^{{tree}}"],
            "object_format": ["rev-parse", "--show-object-format"],
            "ls_tree": ["ls-tree", "-rz", "--full-tree", "-r", expected_commit],
        }
        outputs: dict[str, str] = {}
        for name, arguments in commands.items():
            command = _git_command(git, checkout["path"], arguments)
            try:
                completed = runner(command, repo, git_environment, GIT_TIMEOUT_SECONDS)
            except (OSError, subprocess.SubprocessError) as exc:
                errors.append(f"{phase} Git inspection failed for {label}/{name}: {exc}")
                continue
            outputs[name] = completed.stdout or ""
            if completed.returncode != 0:
                errors.append(
                    f"{phase} Git inspection returned {completed.returncode}: {label}/{name}"
                )
        identity = {
            "origin": str(checkout.get("origin") or ""),
            "head": outputs.get("head", "").strip(),
            "tree": outputs.get("tree", "").strip(),
            "object_format": outputs.get("object_format", "").strip(),
        }
        identities[label] = identity
        if identity["head"] != expected_commit:
            errors.append(f"{phase} pinned Git commit mismatch: {label}")
        if identity["tree"] != checkout["expected_tree"]:
            errors.append(f"{phase} pinned Git tree mismatch: {label}")
        if identity["object_format"] != "sha1":
            errors.append(f"{phase} Git object format must be sha1: {label}")
        manifests[label] = _parse_ls_tree(outputs.get("ls_tree", ""), label, errors, phase)
    return identities, manifests


def _git_blob_id(payload: bytes) -> str:
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(f"blob {len(payload)}\0".encode("ascii"))
    digest.update(payload)
    return digest.hexdigest()


def _checkout_closure(
    repo: Path,
    prepared: Mapping[str, dict[str, Any]],
    manifests: Mapping[str, dict[str, tuple[str, str]]],
    errors: list[str],
    phase: str,
) -> dict[str, dict[str, str]]:
    snapshots: dict[str, dict[str, str]] = {}
    for label, checkout in prepared.items():
        root = checkout["path"]
        actual_payloads: dict[str, bytes] = {}
        actual_modes: dict[str, str] = {}
        directories: set[str] = set()
        total = 0

        def visit(directory: Path, at_root: bool = False) -> None:
            nonlocal total
            try:
                entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
            except OSError as exc:
                errors.append(f"{phase} could not enumerate checkout {label}: {exc}")
                return
            for entry in entries:
                path = Path(entry.path)
                try:
                    value = entry.stat(follow_symlinks=False)
                except OSError as exc:
                    errors.append(f"{phase} could not lstat checkout entry {label}/{entry.name}: {exc}")
                    continue
                relative = path.relative_to(root).as_posix()
                if at_root and entry.name in {".git", ".lake"}:
                    if stat.S_ISDIR(value.st_mode) and not stat.S_ISLNK(value.st_mode):
                        continue
                    errors.append(
                        f"{phase} approved checkout cache/metadata must be a real directory: {label}/{relative}"
                    )
                    continue
                if stat.S_ISLNK(value.st_mode):
                    errors.append(f"{phase} checkout symlink rejected: {label}/{relative}")
                elif stat.S_ISDIR(value.st_mode):
                    directories.add(relative)
                    visit(path)
                elif stat.S_ISREG(value.st_mode):
                    payload = _read_regular_bytes(
                        root,
                        path,
                        label=f"{phase} checkout file {label}/{relative}",
                        max_bytes=MAX_DEPENDENCY_FILE_BYTES,
                        errors=errors,
                    )
                    if payload is None:
                        continue
                    total += len(payload)
                    if total > MAX_DEPENDENCY_TOTAL_BYTES:
                        errors.append(f"{phase} checkout exceeds total byte limit: {label}")
                        continue
                    actual_payloads[relative] = payload
                    actual_modes[relative] = "100755" if value.st_mode & 0o111 else "100644"
                else:
                    errors.append(f"{phase} checkout special file rejected: {label}/{relative}")

        visit(root, True)
        expected = manifests.get(label, {})
        actual = set(actual_payloads)
        expected_paths = set(expected)
        missing = sorted(expected_paths - actual)
        extra = sorted(actual - expected_paths)
        if missing or extra:
            errors.append(
                f"{phase} Git checkout inventory mismatch for {label}: missing={missing} extra={extra}"
            )
        allowed_directories = {
            PurePosixPath(path).parents[index].as_posix()
            for path in expected_paths
            for index in range(len(PurePosixPath(path).parents) - 1)
            if PurePosixPath(path).parents[index].as_posix() != "."
        }
        unexpected_directories = sorted(directories - allowed_directories)
        if unexpected_directories:
            errors.append(
                f"{phase} untracked checkout directories for {label}: {unexpected_directories}"
            )
        snapshot: dict[str, str] = {}
        for relative in sorted(actual & expected_paths):
            expected_mode, expected_blob = expected[relative]
            actual_blob = _git_blob_id(actual_payloads[relative])
            snapshot[relative] = actual_blob
            if actual_modes[relative] != expected_mode:
                errors.append(f"{phase} Git executable mode mismatch: {label}/{relative}")
            if actual_blob != expected_blob:
                errors.append(f"{phase} Git blob mismatch: {label}/{relative}")
        snapshots[label] = snapshot
    return snapshots


def parse_axiom_audit(output: str, errors: list[str]) -> dict[str, set[str]]:
    entries = AUDIT_ENTRY_PATTERN.findall(output)
    counts = Counter(declaration for declaration, _ in entries)
    duplicates = sorted(declaration for declaration, count in counts.items() if count > 1)
    if duplicates:
        errors.append(f"Lean axiom audit repeated declarations: {duplicates}")
    parsed: dict[str, set[str]] = {}
    for declaration, payload in entries:
        values = [item.strip() for item in payload.replace("\n", " ").split(",") if item.strip()]
        repeated_axioms = sorted(item for item, count in Counter(values).items() if count > 1)
        if repeated_axioms:
            errors.append(
                f"Lean axiom audit repeated axioms for {declaration}: {repeated_axioms}"
            )
        parsed[declaration] = set(values)
    found = set(parsed)
    missing = sorted(ALL_DECLARATIONS - found)
    unexpected = sorted(found - ALL_DECLARATIONS)
    if missing:
        errors.append(f"Lean axiom audit missing declarations: {missing}")
    if unexpected:
        errors.append(f"Lean axiom audit reported unexpected declarations: {unexpected}")
    for declaration, axioms in sorted(parsed.items()):
        unexpected_axioms = sorted(axioms - ALLOWED_AXIOMS)
        if unexpected_axioms:
            errors.append(f"unexpected axioms for {declaration}: {unexpected_axioms}")
    if "sorryAx" in output:
        errors.append("Lean axiom audit found sorryAx")
    return parsed


def validate(
    repo: Path = REPO, command_runner: CommandRunner = run_command
) -> tuple[dict[str, Any], str, str]:
    """Run the static diagnostic and fail closed before any dynamic subprocess.

    The injected runner is retained for API compatibility and deliberately unused.
    A future Lean run would consume an unanchored preloaded `.lake` closure, so this
    static result cannot be promoted to an admission or security gate.
    """
    del command_runner
    errors: list[str] = []
    environment = preloaded_validation_environment(repo)
    external_commands: list[dict[str, Any]] = []

    anchor_start = len(errors)
    _, evidences = _read_evidence_anchors(repo, errors, "pre-validation")
    anchors_ok = len(errors) == anchor_start and set(evidences) == set(
        EXPECTED_EVIDENCE_SHA256
    )
    evidence: dict[str, Any] = {}
    root_evidence: dict[str, Any] = {}
    varela_evidence: dict[str, Any] = {}
    evidence_ok = False
    artifacts_ok = False
    inventory_ok = False
    environment_ok = False
    placeholders_ok = False
    expected_inventory: set[str] = set()
    artifact_payloads: dict[str, bytes] = {}
    before_snapshot: dict[str, str] = {}
    before_formal_payloads: dict[str, bytes] = {}

    if anchors_ok:
        evidence = evidences[RESULT_RELATIVE.as_posix()]
        root_evidence = evidences["formal/AgtXIvRootMath/verification-result.json"]
        varela_evidence = evidences["formal/AgtXIvVarela/verification-result.json"]
        start = len(errors)
        validate_evidence_semantics(evidence, errors)
        evidence_ok = len(errors) == start

        start = len(errors)
        artifact_payloads, expected_inventory = _validate_artifacts_guarded(
            evidences, repo, errors, "pre-validation"
        )
        artifacts_ok = len(errors) == start

        start = len(errors)
        before_snapshot, before_formal_payloads = _formal_snapshot_guarded(
            repo, expected_inventory, errors, "pre-validation"
        )
        inventory_ok = len(errors) == start

        start = len(errors)
        environment_ok, _ = _validate_environment_guarded(
            evidence,
            root_evidence,
            varela_evidence,
            artifact_payloads,
            errors,
        )
        environment_ok = environment_ok and len(errors) == start

        placeholders_ok = _scan_expected_placeholders(
            expected_inventory, before_formal_payloads, errors
        )
    else:
        errors.append(
            "formal input inventory was not derived because exact evidence anchors failed"
        )

    tools_start = len(errors)
    tools = validate_direct_tool_paths(repo, errors)
    direct_tool_paths_ok = len(errors) == tools_start and set(tools) == {"lean", "lake"}

    static_ready = all(
        (
            anchors_ok,
            evidence_ok,
            artifacts_ok,
            inventory_ok,
            environment_ok,
            placeholders_ok,
            direct_tool_paths_ok,
        )
    )

    # Absolute final filesystem observation. Nothing below this block reads files or
    # starts a process; report construction consumes only the bytes retained here.
    final_start = len(errors)
    _, final_evidences = _read_evidence_anchors(repo, errors, "final")
    final_anchors_ok = len(errors) == final_start and set(final_evidences) == set(
        EXPECTED_EVIDENCE_SHA256
    )
    final_artifacts_ok = False
    final_inventory_ok = False
    after_snapshot: dict[str, str] = {}
    if final_anchors_ok and anchors_ok:
        artifact_start = len(errors)
        _, final_expected_inventory = _validate_artifacts_guarded(
            final_evidences, repo, errors, "final"
        )
        final_artifacts_ok = (
            len(errors) == artifact_start
            and final_expected_inventory == expected_inventory
        )
        inventory_start = len(errors)
        after_snapshot, _ = _formal_snapshot_guarded(
            repo, expected_inventory, errors, "final"
        )
        added = sorted(set(after_snapshot) - set(before_snapshot))
        removed = sorted(set(before_snapshot) - set(after_snapshot))
        changed = sorted(
            relative
            for relative in set(before_snapshot) & set(after_snapshot)
            if before_snapshot[relative] != after_snapshot[relative]
        )
        if added or removed or changed:
            errors.append(
                "formal input closure changed during static validation: "
                f"added={added} removed={removed} changed={changed}"
            )
        final_inventory_ok = len(errors) == inventory_start
    final_integrity_ok = all(
        (final_anchors_ok, final_artifacts_ok, final_inventory_ok)
    )

    artifact_paths = sorted(
        set(EXPECTED_EVIDENCE_SHA256)
        | {
            relative
            for item in evidences.values()
            for relative in (
                item.get("artifact_hashes", {})
                if isinstance(item.get("artifact_hashes"), dict)
                else {}
            )
            if isinstance(relative, str)
        }
    )
    observed_paths_digest = hashlib.sha256(
        json.dumps(
            artifact_paths, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    if observed_paths_digest != OBSERVED_PATHS_SHA256:
        errors.append(
            "side-effect observed-path coverage does not match the stable contract"
        )

    static_passed = static_ready and final_integrity_ok and not errors
    effective_status = "EXPECTED_BLOCKED" if static_passed else "FAILED"
    dynamic_status = "EXPECTED_BLOCKED" if static_passed else "NOT_RUN"
    blocker_reason = BLOCKER_REASON
    declaration_audit = {
        declaration: {
            "scope": "target-local" if declaration in LOCAL_DECLARATIONS else "imported",
            "audit_status": "NOT_RUN",
            "axioms": [],
        }
        for declaration in sorted(ALL_DECLARATIONS)
    }
    report = {
        "schema": REPORT_SCHEMA,
        "historical_evidence_schema_version": evidence.get("schema_version"),
        "project": PROJECT_RELATIVE.as_posix(),
        "assurance_tier": ASSURANCE_TIER,
        "cache_mode": "DYNAMIC_NOT_RUN_FUTURE_PRELOADED_CACHE_UNVERIFIED",
        "consumed_cache_closure": "NOT_VERIFIED",
        "source_clean_rebuild": False,
        "network_mode": NETWORK_MODE,
        "network_isolation_enforced": False,
        "filesystem_isolation_enforced": False,
        "network_note": NETWORK_NOTE,
        "evidence_id": evidence.get("id"),
        "declared_historical_status": evidence.get("status", "UNDECLARED"),
        "effective_validation_status": effective_status,
        "dynamic_execution": dynamic_status,
        "dynamic_blocker_code": BLOCKER_CODE if static_passed else None,
        "dynamic_blocker_reason": blocker_reason if static_passed else None,
        "kernel_build": "NOT_RUN",
        "kernel_build_failure_excerpt": [],
        "axiom_audit": "NOT_RUN",
        "declarations_audited": 0,
        "target_local_declarations_audited": 0,
        "imported_declarations_audited": 0,
        "expected_target_local_declarations": sorted(LOCAL_DECLARATIONS),
        "expected_imported_declarations": sorted(IMPORTED_DECLARATIONS),
        "declaration_audit": declaration_audit,
        "reported_axioms": [],
        "evidence_anchors": "PASSED" if anchors_ok and final_anchors_ok else "FAILED",
        "artifact_hashes": "PASSED" if artifacts_ok and final_artifacts_ok else "FAILED",
        "formal_input_inventory": "PASSED" if inventory_ok and final_inventory_ok else "FAILED",
        "environment_binding": "PASSED" if environment_ok else "FAILED",
        "tool_identity": {
            "validation": "NOT_RUN",
            "static_path_validation": "PASSED" if direct_tool_paths_ok else "FAILED",
            "dynamic_identity": "NOT_RUN",
            "paths": {name: str(path) for name, path in sorted(tools.items())},
            "resolved_git_executable": None,
        },
        "dependency_git_identity": {
            "validation": "NOT_RUN",
            "source_tree_closure": "NOT_RUN",
            "consumed_cache_closure": "NOT_VERIFIED",
        },
        "placeholder_scan": "PASSED" if placeholders_ok else "FAILED",
        "protected_input_integrity": "PASSED" if final_integrity_ok else "FAILED",
        "side_effect_observation_scope": {
            "method": SIDE_EFFECT_OBSERVATION_METHOD,
            "observed_paths": artifact_paths,
            "reused_unmeasured_cache_roots": list(
                SIDE_EFFECT_REUSED_UNMEASURED_CACHE_ROOTS
            ),
            "paths_outside_observed_formal_and_evidence_closure": (
                SIDE_EFFECT_OUTSIDE_OBSERVED_CLOSURE
            ),
            "future_dynamic_note": SIDE_EFFECT_FUTURE_DYNAMIC_NOTE,
            "filesystem_isolation_enforced": False,
        },
        "external_commands": external_commands,
        "admission_eligible": False,
        "security_gate_eligible": False,
        "m0_completion_effect": "NONE",
        "admission_note": ADMISSION_NOTE,
        "remaining_m0_security_blockers": list(REMAINING_M0_SECURITY_BLOCKERS),
        "errors": errors,
        "formalization_validation": effective_status,
        "scientific_acceptance_effect": CURRENT_SCIENTIFIC_EFFECT,
        "scope_limitations": list(EXPECTED_SCOPE_LIMITATIONS),
        "environment_policy": {
            "network_mode": environment.get("AGTXIV_NETWORK_MODE"),
            "credential_minimized": True,
        },
    }
    return report, "", ""


def main() -> int:
    report, build_output, audit_output = validate()
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["errors"] and build_output:
        print(build_output)
    if report["errors"] and audit_output:
        print(audit_output)
    if report["formalization_validation"] == "EXPECTED_BLOCKED":
        return 2
    return 0 if report["formalization_validation"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
