#!/usr/bin/env python3
"""Run the AgtXIv repository validation profiles.

The runner selects checks intended to consume local, preloaded inputs and checks
declared protected artifacts for mutation.  It does not enforce operating-system
network or filesystem isolation.  Known historical exceptions remain narrow,
explicit, and machine-readable.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import selectors
import signal
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any


REPO = Path(__file__).resolve().parents[1]
MINIMUM_PYTHON = (3, 12)
REPORT_SCHEMA = "agtxiv.repository-validation-report/0.2.0"
NETWORK_MODE = "OFFLINE_INTENDED_PRELOADED_ONLY"
MAX_CAPTURE_BYTES = 2 * 1024 * 1024
PROCESS_GROUP_GRACE_SECONDS = 5
POST_EXIT_DRAIN_SECONDS = 1
TIMEOUT_EXIT_CODE = 124
OUTPUT_LIMIT_EXIT_CODE = 125
BACKGROUND_PROCESS_EXIT_CODE = 126
MAX_PROTECTED_FILE_BYTES = 64 * 1024 * 1024
STABILIZERNESS_BLOCKER_CODE = "UNVERIFIED_FUTURE_LEAN_CACHE_CLOSURE"
STABILIZERNESS_EVIDENCE_ID = (
    "lean-verification:stabilizerness-local-delta:2026-08-16"
)
STABILIZERNESS_HISTORICAL_STATUS = "TARGET_LOCAL_DELTA_KERNEL_CHECKED"
STABILIZERNESS_BLOCKER_REASON = (
    "consumed_cache_closure=NOT_VERIFIED: a future Lean run would consume preloaded "
    ".lake artifacts without an external exact type/mode/content manifest; clean "
    "scratch execution, OS-level no-egress, and executable byte locks are also "
    "not implemented"
)
STABILIZERNESS_SCIENTIFIC_EFFECT = (
    "NONE; this static run only confirms that the anchored source and historical "
    "record bytes associated with four target-local and three imported declaration "
    "names remain unchanged. It does not type-check or build those declarations, "
    "audit their axioms, reassess mapping correctness or source alignment, modify "
    "the registry, establish scientific acceptance, or prove the closed-form theorem."
)
STABILIZERNESS_NETWORK_NOTE = (
    "No dynamic command ran. This validator does not enforce operating-system "
    "outbound network blocking."
)
STABILIZERNESS_SIDE_EFFECT_KEYS = frozenset(
    {
        "method",
        "observed_paths",
        "reused_unmeasured_cache_roots",
        "paths_outside_observed_formal_and_evidence_closure",
        "future_dynamic_note",
        "filesystem_isolation_enforced",
    }
)
STABILIZERNESS_SIDE_EFFECT_METHOD = (
    "two pure-Python lstat/O_NOFOLLOW raw-byte snapshots of the exact "
    "anchored evidence, artifact, and three-project formal inventories"
)
STABILIZERNESS_REUSED_UNMEASURED_CACHE_ROOTS = (
    "formal/AgtXIvStabilizerness/.lake/**",
    "formal/AgtXIvRootMath/.lake/**",
    "formal/AgtXIvVarela/.lake/**",
    "Reference/LeanQuantum/.lake/**",
)
STABILIZERNESS_OUTSIDE_OBSERVED_CLOSURE = "NOT_MEASURED"
STABILIZERNESS_FUTURE_DYNAMIC_NOTE = (
    "A future Lean run would consume these unverified cache roots; this "
    "static diagnostic did not consume or validate them."
)
STABILIZERNESS_OBSERVED_PATHS_SHA256 = (
    "529247c6326e749370207bb84dff73c98a25b873ae1c697b1f5822d402c71ed3"
)
STABILIZERNESS_ADMISSION_NOTE = (
    "An EXPECTED_BLOCKED diagnostic must not be used for database admission, "
    "merge approval, or a threat-model security gate."
)
STABILIZERNESS_REMAINING_M0_SECURITY_BLOCKERS = (
    "externally anchored consumed .lake cache closure or clean scratch rebuild",
    "clean scratch workspace",
    "operating-system enforced no-egress execution",
    "cryptographic lock for Lean, Lake, and Git executable bytes",
)
STABILIZERNESS_SCOPE_LIMITATIONS = (
    "The affine-span declaration is only a generic reduction from vector span "
    "and does not prove claim:relaxed-affine-span.",
    "The sign-maximization declaration does not by itself prove "
    "claim:relaxed-mwis-dual; the LP-to-MWIS bridge remains open.",
    "Weighted perfect-graph duality remains an explicit external foundation and "
    "is not proved by this project.",
)
STABILIZERNESS_ENVIRONMENT_POLICY_KEYS = frozenset(
    {"network_mode", "credential_minimized"}
)
STABILIZERNESS_TOOLCHAIN_BIN_RELATIVE = Path(
    ".tools/elan/toolchains/leanprover--lean4---v4.30.0-rc2/bin"
)
STABILIZERNESS_TOOL_PATHS = {
    "lake": str(REPO / STABILIZERNESS_TOOLCHAIN_BIN_RELATIVE / "lake"),
    "lean": str(REPO / STABILIZERNESS_TOOLCHAIN_BIN_RELATIVE / "lean"),
}
IJSON_MAX_INTEGER = (1 << 53) - 1
PYTEST_IDENTITY_BASELINE_PATH = (
    "baselines/repository-validation/pytest/test-identity-v1.json"
)
PYTEST_IDENTITY_TOOL_PATH = "tools/validate_pytest_inventory.py"
PYTEST_IDENTITY_SCHEMA_PATH = (
    "schemas/repository-validation/pytest-test-identity.schema.json"
)
PYTEST_IDENTITY_EVALUATION_SCHEMA = "agtxiv.pytest-inventory-evaluation/2.0.0"
PYTEST_IDENTITY_SCHEMA = "agtxiv.pytest-test-identity/1.0.0"
PYTEST_IDENTITY_EVIDENCE_SCOPE = (
    "COLLECTION_IDENTITY_ONLY_NOT_TEST_EXECUTION_RESULT"
)
PYTEST_IDENTITY_BLOCKER_CODE = (
    "UNSANDBOXED_PYTEST_COLLECTION_NOT_BRANCH_EVIDENCE"
)
PYTEST_IDENTITY_ENVIRONMENT_STATUS = "LOCKED_RUNTIME_MATCHED"
PYTEST_IDENTITY_ENVIRONMENT_SECURITY_ROLE = (
    "REQUIRED_LOCK_QUALIFICATION_EXCLUDED_ONLY_FROM_CROSS_ENVIRONMENT_IDENTITY"
)
PYTEST_IDENTITY_ENVIRONMENT_SCOPE = (
    "VERSION_LOCK_AND_INSTALLED_DISTRIBUTION_MATCH_NOT_OS_OR_NETWORK_ISOLATION"
)
PYTEST_IDENTITY_VALIDATOR_BINDING_STATUS = (
    "PARENT_BYTES_MATCHED_SOURCE_COMMIT"
)
PYTEST_IDENTITY_BASELINE_BINDING_STATUS = (
    "FROZEN_BASELINE_BYTES_MATCHED_SOURCE_COMMIT"
)
PYTEST_IDENTITY_HEAD_BINDING_STATUS = "HEAD_UNCHANGED_DURING_EVALUATION"
PYTEST_IDENTITY_VERSION_RE = re.compile(
    r"^[0-9]+(?:\.[0-9]+)+(?:[-+._a-zA-Z0-9]*)?$"
)
PYTEST_IDENTITY_COLLECTION_CONTRACT = {
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
STABILIZERNESS_LOCAL_DECLARATIONS = {
    "AgtXIv.Stabilizerness.abs_signed_sum_add_le",
    "AgtXIv.Stabilizerness.exists_sign_attaining_abs_sum",
    "AgtXIv.Stabilizerness.max_abs_signed_sum",
    "AgtXIv.Stabilizerness.affineSpan_eq_top_of_vectorSpan_eq_top",
}
STABILIZERNESS_IMPORTED_DECLARATIONS = {
    "AgtXIv.GraphFoundation.independentFinsets",
    "AgtXIv.GraphFoundation.maxWeightIndependent",
    "AgtXIv.GraphFoundation.IsPerfect",
}
STABILIZERNESS_REPORT_TOP_LEVEL_KEYS = frozenset(
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
STABILIZERNESS_DECLARATION_ENTRY_KEYS = frozenset(
    {"scope", "audit_status", "axioms"}
)
STABILIZERNESS_TOOL_IDENTITY_KEYS = frozenset(
    {
        "validation",
        "static_path_validation",
        "dynamic_identity",
        "paths",
        "resolved_git_executable",
    }
)
STABILIZERNESS_TOOL_PATH_KEYS = frozenset({"lake", "lean"})
STABILIZERNESS_DEPENDENCY_IDENTITY_KEYS = frozenset(
    {"validation", "source_tree_closure", "consumed_cache_closure"}
)

SHELLWORLD_MANIFEST = Path(
    "agents/bouncing-shellworld-charged-ads/queries/query-001/run-manifest.json"
)
SHELLWORLD_MUTABLE_SPEC = Path("docs/specifications/v1-bridge.md")
SHELLWORLD_EXPECTED_SPEC_SHA256 = (
    "c9c7b46732d56c862f77b64304b5a24f312b36386e643f0c204949c426cd6b54"
)
SHELLWORLD_REVIEWED_CURRENT_SPEC_SHA256 = (
    "0c8fcd49dca17c0f6f547182cc6143c466d90a343b9703bd0aaec67690233d13"
)
SHELLWORLD_EXACT_ERROR = (
    "manifest hash mismatch: docs/specifications/v1-bridge.md"
)

FORMAL_VERIFICATION_RECORDS = (
    "formal/AgtXIvRootMath/verification-result.json",
    "formal/AgtXIvStabilizerness/verification-result.json",
    "formal/AgtXIvVarela/verification-result.json",
)

class ResultStatus(StrEnum):
    PASS = "PASS"
    KNOWN_STALE = "KNOWN_STALE"
    EXPECTED_BLOCKED = "EXPECTED_BLOCKED"
    FAIL = "FAIL"
    MISSING_TOOL = "MISSING_TOOL"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True)
class ToolRequirement:
    kind: str
    value: str
    label: str


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    description: str
    profiles: tuple[str, ...]
    command: tuple[str, ...] | None = None
    requirements: tuple[ToolRequirement, ...] = ()
    classifier: str = "normal"
    timeout_seconds: int = 300
    protected_paths: tuple[str, ...] = ()
    expected_blocker: str | None = None
    site_build: bool = False
    required_repository_paths: tuple[str, ...] = ()
    missing_repository_status: ResultStatus = ResultStatus.FAIL


@dataclass(frozen=True)
class Invocation:
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float


@dataclass
class CheckResult:
    check_id: str
    description: str
    status: ResultStatus
    command: list[str] = field(default_factory=list)
    exit_code: int | None = None
    duration_seconds: float = 0.0
    stdout: str = ""
    stderr: str = ""
    details: dict[str, Any] = field(default_factory=dict)


CommandRunner = Callable[[Sequence[str], Path, Mapping[str, str], int], Invocation]
RequirementProbe = Callable[[ToolRequirement, Path], tuple[bool, str | None]]


def _python(path: str, *arguments: str) -> tuple[str, ...]:
    return ("{python}", path, *arguments)


def validation_catalog() -> tuple[CheckSpec, ...]:
    """Return the ordered, immutable repository validation inventory."""
    full = ("full", "nightly")
    every = ("fast", "full", "nightly")
    nightly = ("nightly",)
    executable = lambda name: ToolRequirement("executable", name, name)
    module = lambda name: ToolRequirement("python-module", name, f"Python module {name}")
    repository_lake = ToolRequirement(
        "repository-executable", ".tools/elan/bin/lake", "repository-local lake"
    )
    direct_lake = ToolRequirement(
        "repository-executable",
        (
            ".tools/elan/toolchains/leanprover--lean4---v4.30.0-rc2/"
            "bin/lake"
        ),
        "direct pinned lake",
    )
    direct_lean = ToolRequirement(
        "repository-executable",
        (
            ".tools/elan/toolchains/leanprover--lean4---v4.30.0-rc2/"
            "bin/lean"
        ),
        "direct pinned lean",
    )
    return (
        CheckSpec(
            "preflight-node",
            "Node.js is available for JavaScript-facing tests.",
            full,
            requirements=(executable("node"),),
        ),
        CheckSpec(
            "preflight-rsync",
            "rsync is available for the static-site assembly.",
            full,
            requirements=(executable("rsync"),),
        ),
        CheckSpec(
            "preflight-lake",
            "The direct pinned Lean and Lake executables are available.",
            full,
            requirements=(direct_lake, direct_lean),
        ),
        CheckSpec(
            "v2-paper-agentization",
            "Validate the current V2 schema and cross-record contract fixture.",
            every,
            _python("tools/validate_v2_paper_agentization.py"),
            requirements=(module("jsonschema"),),
            required_repository_paths=("tools/validate_v2_paper_agentization.py",),
        ),
        CheckSpec(
            "scientific-claims",
            "Validate ScientificClaim, bridge, assessment, and dependency records.",
            every,
            _python("tools/validate_scientific_claims.py", "--check"),
            requirements=(module("jsonschema"), module("referencing")),
        ),
        CheckSpec(
            "claim-interface-study",
            "Validate the source-faithful claim-interface study fixtures.",
            every,
            _python("tools/validate_claim_interface_study.py"),
        ),
        CheckSpec(
            "semantic-contribution-study",
            "Validate semantic contribution fixtures without regenerating them.",
            every,
            _python("tools/validate_semantic_contribution_study.py"),
            requirements=(module("jsonschema"),),
        ),
        CheckSpec(
            "demo-claimir-migration",
            "Validate the legacy-to-MathClaimIR demo migration inventory.",
            every,
            _python("tools/migration/validate_demo_claimir.py"),
        ),
        CheckSpec(
            "claim-dag",
            "Validate the current claim dependency DAG.",
            every,
            _python("tools/validate_claim_dag.py", "--json"),
        ),
        CheckSpec(
            "root-partitions",
            "Validate Root PaperAgent verification partitions and evidence bindings.",
            every,
            _python("tools/validate_root_partitions.py"),
            protected_paths=FORMAL_VERIFICATION_RECORDS,
        ),
        CheckSpec(
            "pilot-structure",
            "Validate the V1 pilot structure without promoting scientific status.",
            every,
            _python("tools/validate_pilot.py"),
        ),
        CheckSpec(
            "shellworld-v1-run",
            "Validate the immutable Shellworld V1 query run and its historical hashes.",
            every,
            _python(
                "agents/bouncing-shellworld-charged-ads/queries/query-001/validate_run.py"
            ),
            requirements=(
                module("jsonschema"),
                module("referencing"),
                module("sympy"),
            ),
            classifier="shellworld-known-stale",
            protected_paths=(
                (
                    "agents/bouncing-shellworld-charged-ads/queries/query-001/"
                    "verification/check-result.json"
                ),
            ),
        ),
        CheckSpec(
            "pytest-test-identity",
            "Compare the reviewed portable pytest identity without promoting it to branch evidence.",
            every,
            _python(
                PYTEST_IDENTITY_TOOL_PATH,
                "--check",
                PYTEST_IDENTITY_BASELINE_PATH,
                "--source-head",
            ),
            requirements=(
                module("pytest"),
                executable("git"),
                executable("uv"),
            ),
            classifier="pytest-test-identity-expected-blocked",
            timeout_seconds=300,
            protected_paths=(
                PYTEST_IDENTITY_BASELINE_PATH,
                PYTEST_IDENTITY_TOOL_PATH,
                PYTEST_IDENTITY_SCHEMA_PATH,
                "tools/validate_repo.py",
            ),
            required_repository_paths=(
                PYTEST_IDENTITY_TOOL_PATH,
                PYTEST_IDENTITY_SCHEMA_PATH,
                PYTEST_IDENTITY_BASELINE_PATH,
            ),
            missing_repository_status=ResultStatus.EXPECTED_BLOCKED,
        ),
        CheckSpec(
            "test-suite",
            "Run the repository unit and contract test suite.",
            every,
            ("{python}", "-m", "pytest", "-q"),
            requirements=(module("pytest"), executable("node")),
            timeout_seconds=600,
        ),
        CheckSpec(
            "pages-site",
            "Assemble and validate the Pages site in an ignored temporary directory.",
            full,
            ("bash", "tools/build_pages_site.sh", "{site_dir}"),
            requirements=(executable("bash"), executable("rsync")),
            timeout_seconds=300,
            protected_paths=FORMAL_VERIFICATION_RECORDS,
            site_build=True,
        ),
        CheckSpec(
            "lean-root-math",
            "Rebuild and axiom-audit the RootMath Lean project.",
            full,
            _python("tools/validate_lean_formalization.py"),
            requirements=(repository_lake,),
            timeout_seconds=900,
            protected_paths=FORMAL_VERIFICATION_RECORDS,
        ),
        CheckSpec(
            "lean-varela",
            "Rebuild and axiom-audit the Varela Lean project.",
            full,
            _python("tools/validate_varela_formalization.py"),
            requirements=(repository_lake,),
            timeout_seconds=900,
            protected_paths=FORMAL_VERIFICATION_RECORDS,
        ),
        CheckSpec(
            "lean-stabilizerness-dynamic",
            "Audit the pinned Stabilizerness inputs and report the unverified-cache blocker.",
            full,
            _python("tools/validate_stabilizerness_formalization.py"),
            classifier="stabilizerness-expected-blocked",
            timeout_seconds=120,
            protected_paths=FORMAL_VERIFICATION_RECORDS,
        ),
        CheckSpec(
            "claim-interface-final-readiness",
            "Run the stronger final-readiness checks for the claim-interface study.",
            nightly,
            _python("tools/validate_claim_interface_study.py", "--final-readiness"),
        ),
        CheckSpec(
            "pilot-scientific-gate",
            "Exercise the intentionally blocked V1 scientific-release gate.",
            nightly,
            _python("tools/validate_pilot.py", "--strict-science"),
            classifier="pilot-expected-blocked",
        ),
        CheckSpec(
            "arxiv-intake-adversarial-corpus",
            "Run the grammar-complete preloaded arXiv intake and archive-security corpus.",
            nightly,
            expected_blocker=(
                "M3 intake grammar, safe acquisition, and adversarial archive corpus are "
                "not implemented yet."
            ),
        ),
        CheckSpec(
            "database-review-admission",
            "Exercise append-only storage and independent review-before-admission gates.",
            nightly,
            expected_blocker=(
                "M6 production persistence, independent review, and atomic admission are "
                "not implemented yet."
            ),
        ),
        CheckSpec(
            "browser-v2-e2e",
            "Run the API-backed V2 browser and downloadable-bundle workflow.",
            nightly,
            expected_blocker=(
                "M7 API-backed V2 demo and browser end-to-end suite are not implemented yet."
            ),
        ),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ProtectedHashError(RuntimeError):
    pass


def _stat_signature(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _directory_identity(value: os.stat_result) -> tuple[int, int, int]:
    """Identify a directory without rejecting unrelated changes to its children."""
    return (value.st_dev, value.st_ino, value.st_mode)


def _guarded_protected_bytes(
    root: Path, relative: str, max_bytes: int = MAX_PROTECTED_FILE_BYTES
) -> bytes | None:
    """Read a protected regular file through a revalidated dirfd/openat chain."""
    pure = PurePosixPath(relative)
    if (
        not relative
        or pure.is_absolute()
        or "\\" in relative
        or "\x00" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        raise ProtectedHashError(f"unsafe protected path: {relative!r}")
    root = root.absolute()
    if root.anchor != os.sep:
        raise ProtectedHashError(f"protected root is not an absolute POSIX path: {root}")
    if any(
        not hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    ):
        raise ProtectedHashError("required dirfd/openat safety flags are unavailable")
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
    directory_fds: list[int] = []
    chain: list[tuple[int, str, int, tuple[int, int, int]]] = []
    file_fd: int | None = None
    final_observed = False
    try:
        current_fd = os.open(Path(root.anchor), directory_flags)
        directory_fds.append(current_fd)
        for part in [*root.parts[1:], *pure.parts[:-1]]:
            before = os.stat(part, dir_fd=current_fd, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
                raise ProtectedHashError(
                    f"protected path component is not a real directory: {relative!r}/{part}"
                )
            child_fd = os.open(part, directory_flags, dir_fd=current_fd)
            opened = os.fstat(child_fd)
            if _directory_identity(before) != _directory_identity(opened):
                os.close(child_fd)
                raise ProtectedHashError(
                    f"protected path component changed during open: {relative!r}/{part}"
                )
            chain.append((current_fd, part, child_fd, _directory_identity(before)))
            directory_fds.append(child_fd)
            current_fd = child_fd
        final_name = pure.parts[-1]
        before_file = os.stat(final_name, dir_fd=current_fd, follow_symlinks=False)
        final_observed = True
        if not stat.S_ISREG(before_file.st_mode) or stat.S_ISLNK(before_file.st_mode):
            raise ProtectedHashError(
                f"protected artifact is not a regular non-symlink file: {relative}"
            )
        if before_file.st_size > max_bytes:
            raise ProtectedHashError(
                f"protected artifact exceeds {max_bytes} bytes: {relative}"
            )
        file_fd = os.open(final_name, file_flags, dir_fd=current_fd)
        opened_file = os.fstat(file_fd)
        if (
            not stat.S_ISREG(opened_file.st_mode)
            or _stat_signature(before_file) != _stat_signature(opened_file)
        ):
            raise ProtectedHashError(
                f"protected artifact changed before safe open: {relative}"
            )
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
            raise ProtectedHashError(
                f"protected artifact grew beyond {max_bytes} bytes: {relative}"
            )
        after_fd = os.fstat(file_fd)
        after_path = os.stat(final_name, dir_fd=current_fd, follow_symlinks=False)
        if (
            _stat_signature(before_file) != _stat_signature(after_fd)
            or _stat_signature(before_file) != _stat_signature(after_path)
            or len(payload) != before_file.st_size
        ):
            raise ProtectedHashError(
                f"protected artifact changed while being read: {relative}"
            )
        for parent_fd, part, child_fd, expected in chain:
            path_state = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
            fd_state = os.fstat(child_fd)
            if (
                _directory_identity(path_state) != expected
                or _directory_identity(fd_state) != expected
            ):
                raise ProtectedHashError(
                    f"protected directory chain changed while reading: {relative!r}/{part}"
                )
        return payload
    except FileNotFoundError as exc:
        if final_observed:
            raise ProtectedHashError(
                f"protected artifact disappeared during guarded read: {relative}: {exc}"
            ) from exc
        return None
    except ProtectedHashError:
        raise
    except OSError as exc:
        raise ProtectedHashError(
            f"protected artifact guarded read failed: {relative}: {exc}"
        ) from exc
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


def _protected_hashes(root: Path, paths: Sequence[str]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for relative in paths:
        payload = _guarded_protected_bytes(root, relative)
        result[relative] = (
            hashlib.sha256(payload).hexdigest() if payload is not None else None
        )
    return result


def _default_requirement_probe(
    requirement: ToolRequirement, root: Path
) -> tuple[bool, str | None]:
    if requirement.kind == "executable":
        resolved = shutil.which(requirement.value)
        return resolved is not None, resolved
    if requirement.kind == "repository-executable":
        candidate = root / requirement.value
        available = (
            not candidate.is_symlink()
            and candidate.is_file()
            and os.access(candidate, os.X_OK)
        )
        return available, str(candidate) if available else None
    if requirement.kind == "python-module":
        available = importlib.util.find_spec(requirement.value) is not None
        return available, requirement.value if available else None
    raise ValueError(f"unknown tool requirement kind: {requirement.kind}")


def _preloaded_validation_environment() -> dict[str, str]:
    """Pass a credential-minimized environment; this is not an egress sandbox."""
    passthrough = {
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "SYSTEMROOT",
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
    environment.update(
        {
            "AGTXIV_NETWORK_MODE": NETWORK_MODE,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
        }
    )
    return environment


def _subprocess_runner(
    command: Sequence[str], cwd: Path, environment: Mapping[str, str], timeout: int
) -> Invocation:
    started = time.monotonic()
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
        return Invocation(127, "", str(exc), time.monotonic() - started)
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    streams = {process.stdout.fileno(): "stdout", process.stderr.fileno(): "stderr"}
    open_fds = set(streams)
    for descriptor in open_fds:
        os.set_blocking(descriptor, False)
        selector.register(descriptor, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout
    leader_exit_seen: float | None = None
    forced_code: int | None = None
    forced_message = ""
    captured = 0
    try:
        while open_fds:
            now = time.monotonic()
            if now >= deadline:
                forced_code = TIMEOUT_EXIT_CODE
                forced_message = f"command timed out after {timeout} seconds"
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
                    "command leader exited while descendants or inherited pipes remained active"
                )
                break
            for key, _ in selector.select(min(0.1, max(0.0, deadline - now))):
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
                        forced_message = f"command output exceeded {MAX_CAPTURE_BYTES} bytes"
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
    return Invocation(
        forced_code if forced_code is not None else int(process.returncode or 0),
        stdout,
        stderr,
        time.monotonic() - started,
    )


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


def _resolve_command(
    spec: CheckSpec, root: Path, site_directory: Path | None = None
) -> list[str]:
    if spec.command is None:
        return []
    replacements = {
        "{python}": sys.executable,
        "{repo}": str(root),
        "{site_dir}": str(site_directory) if site_directory is not None else "<temporary-site>",
    }
    return [replacements.get(part, part) for part in spec.command]


def _prepare_shellworld_validation_tree(root: Path, destination: Path) -> Path:
    """Copy run inputs so the legacy determinism check cannot write in place."""
    root_resolved = root.resolve(strict=True)
    destination_resolved = destination.resolve(strict=True)

    def checked_paths(relative: object) -> tuple[Path, Path]:
        if not isinstance(relative, str):
            raise ValueError("Shellworld manifest path must be a string")
        raw_parts = relative.split("/")
        pure = PurePosixPath(relative)
        if (
            not relative
            or pure.is_absolute()
            or any(part in {"", ".", ".."} for part in raw_parts)
            or "\\" in relative
            or "\x00" in relative
        ):
            raise ValueError(f"unsafe Shellworld manifest path: {relative!r}")
        source = root / Path(*pure.parts)
        if source.is_symlink() or not source.is_file():
            raise ValueError(
                f"Shellworld manifest source must be a regular non-symlink file: {relative}"
            )
        source_resolved = source.resolve(strict=True)
        if not source_resolved.is_relative_to(root_resolved):
            raise ValueError(f"Shellworld manifest source escapes repository: {relative}")
        target = destination / Path(*pure.parts)
        target_resolved = target.resolve(strict=False)
        if not target_resolved.is_relative_to(destination_resolved):
            raise ValueError(f"Shellworld manifest target escapes isolation: {relative}")
        return source_resolved, target_resolved

    manifest_source, _ = checked_paths(SHELLWORLD_MANIFEST.as_posix())
    manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Shellworld manifest must be a JSON object")
    relative_paths: set[str] = set()
    for section in ("consumed_artifacts", "produced_artifacts"):
        items = manifest.get(section)
        if not isinstance(items, list):
            raise ValueError(f"Shellworld manifest {section} must be an array")
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                raise ValueError(
                    f"Shellworld manifest {section} contains an invalid artifact path"
                )
            relative_paths.add(item["path"])
    self_artifact = manifest.get("self_artifact")
    if (
        not isinstance(self_artifact, dict)
        or self_artifact.get("path") != SHELLWORLD_MANIFEST.as_posix()
    ):
        raise ValueError("Shellworld manifest self_artifact path is not exact")
    relative_paths.add(self_artifact["path"])
    for relative in sorted(relative_paths):
        source, target = checked_paths(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return (
        destination
        / "agents/bouncing-shellworld-charged-ads/queries/query-001/validate_run.py"
    )


class DuplicateJSONKeyError(ValueError):
    pass


class StrictJSONValueError(ValueError):
    pass


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKeyError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _parse_ijson_integer(token: str) -> int:
    digits = token[1:] if token.startswith("-") else token
    if not digits or len(digits) > len(str(IJSON_MAX_INTEGER)):
        raise StrictJSONValueError("JSON integer is outside the I-JSON exact range")
    value = int(token)
    if not -IJSON_MAX_INTEGER <= value <= IJSON_MAX_INTEGER:
        raise StrictJSONValueError("JSON integer is outside the I-JSON exact range")
    return value


def _parse_finite_json_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise StrictJSONValueError("JSON floating-point value is not finite")
    return value


def _reject_json_constant(token: str) -> None:
    raise StrictJSONValueError(f"non-standard JSON constant is forbidden: {token}")


def _stable_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_json_output(invocation: Invocation) -> dict[str, Any] | None:
    if not isinstance(invocation.stdout, str):
        return None
    try:
        encoded = invocation.stdout.encode("utf-8", errors="strict")
        if len(encoded) > MAX_CAPTURE_BYTES:
            return None
        payload = json.loads(
            invocation.stdout,
            object_pairs_hook=_strict_json_object,
            parse_int=_parse_ijson_integer,
            parse_float=_parse_finite_json_float,
            parse_constant=_reject_json_constant,
        )
    except (
        ValueError,
        TypeError,
        UnicodeError,
        OverflowError,
        RecursionError,
    ):
        return None
    return payload if isinstance(payload, dict) else None


def _normal_result(spec: CheckSpec, invocation: Invocation, command: list[str]) -> CheckResult:
    return CheckResult(
        check_id=spec.check_id,
        description=spec.description,
        status=ResultStatus.PASS if invocation.returncode == 0 else ResultStatus.FAIL,
        command=command,
        exit_code=invocation.returncode,
        duration_seconds=invocation.duration_seconds,
        stdout=invocation.stdout,
        stderr=invocation.stderr,
    )


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _is_git_object_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _length_prefixed_sha256(domain: bytes, values: Sequence[str]) -> str:
    digest = hashlib.sha256(domain)
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(struct.pack(">Q", len(encoded)))
        digest.update(encoded)
    return digest.hexdigest()


def _pytest_identity_digest(identity: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        identity,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(
        b"agtxiv.pytest-test-identity/1.0.0\0" + encoded
    ).hexdigest()


def _is_exact_node_id(value: object) -> bool:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or any(character in value for character in ("\x00", "\r", "\n"))
        or unicodedata.normalize("NFC", value) != value
    ):
        return False
    components = value.split("::")
    path_text = components[0]
    parts = path_text.split("/")
    return bool(
        len(parts) >= 2
        and parts[0] == "tests"
        and ":" not in path_text
        and "\\" not in path_text
        and "//" not in path_text
        and all(part not in {"", ".", ".."} for part in parts)
        and all(component != "" for component in components[1:])
    )


def _is_stable_marker_value(value: Any) -> bool:
    if value is None or type(value) is bool or isinstance(value, str):
        return True
    if type(value) is int:
        return -IJSON_MAX_INTEGER <= value <= IJSON_MAX_INTEGER
    if isinstance(value, list):
        return all(_is_stable_marker_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_stable_marker_value(item)
            for key, item in value.items()
        )
    return False


def _is_exact_input_bindings(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {
        ".python-version",
        "pyproject.toml",
        "uv.lock",
    }:
        return False
    for binding in value.values():
        if not isinstance(binding, dict) or set(binding) != {"byte_size", "sha256"}:
            return False
        byte_size = binding.get("byte_size")
        if (
            type(byte_size) is not int
            or not 1 <= byte_size <= IJSON_MAX_INTEGER
            or not _is_sha256(binding.get("sha256"))
        ):
            return False
    return True


def _is_exact_pytest_collection_contract(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != set(
        PYTEST_IDENTITY_COLLECTION_CONTRACT
    ):
        return False
    for field, expected in PYTEST_IDENTITY_COLLECTION_CONTRACT.items():
        actual = value.get(field)
        if type(actual) is not type(expected):
            return False
        if isinstance(expected, list):
            if (
                len(actual) != len(expected)
                or any(type(item) is not str for item in actual)
                or any(
                    type(item) is not type(expected_item) or item != expected_item
                    for item, expected_item in zip(actual, expected, strict=True)
                )
            ):
                return False
        elif actual != expected:
            return False
    return True


def _is_exact_marker_declarations(
    value: object, node_ids: Sequence[str]
) -> bool:
    if not isinstance(value, list):
        return False
    node_order = {node_id: index for index, node_id in enumerate(node_ids)}
    seen: set[str] = set()
    last_index = -1
    for declaration in value:
        if not isinstance(declaration, dict) or set(declaration) != {
            "node_id",
            "markers",
        }:
            return False
        node_id = declaration.get("node_id")
        markers = declaration.get("markers")
        if (
            not isinstance(node_id, str)
            or node_id not in node_order
            or node_id in seen
            or node_order[node_id] <= last_index
            or not isinstance(markers, list)
            or not markers
        ):
            return False
        canonical_markers: list[bytes] = []
        for marker in markers:
            if not isinstance(marker, dict) or set(marker) != {"name", "args", "kwargs"}:
                return False
            if marker.get("name") not in {"skip", "skipif", "xfail"}:
                return False
            if not isinstance(marker.get("args"), list) or not isinstance(
                marker.get("kwargs"), dict
            ):
                return False
            if not _is_stable_marker_value(marker["args"]) or not _is_stable_marker_value(
                marker["kwargs"]
            ):
                return False
            try:
                canonical_markers.append(
                    json.dumps(
                        marker,
                        ensure_ascii=False,
                        allow_nan=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
            except (TypeError, ValueError, UnicodeError):
                return False
        if canonical_markers != sorted(canonical_markers):
            return False
        seen.add(node_id)
        last_index = node_order[node_id]
    return True


def _is_exact_collection_skips(value: object) -> bool:
    if not isinstance(value, list):
        return False
    seen: set[str] = set()
    node_ids: list[str] = []
    for record in value:
        if not isinstance(record, dict) or set(record) != {"node_id", "reason"}:
            return False
        node_id = record.get("node_id")
        reason = record.get("reason")
        if (
            not _is_exact_node_id(node_id)
            or node_id in seen
            or not isinstance(reason, str)
            or not reason
            or "\x00" in reason
        ):
            return False
        seen.add(node_id)
        node_ids.append(node_id)
    return node_ids == sorted(node_ids, key=lambda item: item.encode("utf-8"))


def _is_exact_test_identity(value: object, digest: object) -> bool:
    expected_keys = {
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
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        return False
    if (
        value.get("schema") != PYTEST_IDENTITY_SCHEMA
        or value.get("evidence_scope") != PYTEST_IDENTITY_EVIDENCE_SCOPE
        or not _is_exact_pytest_collection_contract(
            value.get("collection_contract")
        )
        or not _is_exact_input_bindings(value.get("input_bindings"))
    ):
        return False
    node_ids = value.get("node_ids")
    selected = value.get("selected_node_ids")
    deselected = value.get("deselected_node_ids")
    if not all(isinstance(items, list) for items in (node_ids, selected, deselected)):
        return False
    assert isinstance(node_ids, list)
    assert isinstance(selected, list)
    assert isinstance(deselected, list)
    if (
        not node_ids
        or not selected
        or not all(_is_exact_node_id(item) for item in (*node_ids, *selected, *deselected))
        or len(node_ids) != len(set(node_ids))
        or len(selected) != len(set(selected))
        or len(deselected) != len(set(deselected))
        or set(selected) & set(deselected)
        or set(node_ids) != set(selected) | set(deselected)
    ):
        return False
    skips = value.get("collection_skips")
    markers = value.get("marker_declarations")
    if not _is_exact_collection_skips(skips) or not _is_exact_marker_declarations(
        markers, node_ids
    ):
        return False
    assert isinstance(skips, list)
    assert isinstance(markers, list)
    counts = value.get("counts")
    expected_counts = {
        "collected": len(node_ids),
        "selected": len(selected),
        "deselected": len(deselected),
        "collection_skipped": len(skips),
        "marker_declarations": len(markers),
    }
    if (
        not isinstance(counts, dict)
        or set(counts) != set(expected_counts)
        or any(type(item) is not int for item in counts.values())
        or counts != expected_counts
    ):
        return False
    expected_set_digest = _length_prefixed_sha256(
        b"agtxiv.pytest-node-set/1.0.0\0",
        sorted(node_ids, key=lambda item: item.encode("utf-8")),
    )
    expected_order_digest = _length_prefixed_sha256(
        b"agtxiv.pytest-node-order/1.0.0\0", selected
    )
    try:
        expected_identity_digest = _pytest_identity_digest(value)
    except (TypeError, ValueError, UnicodeError):
        return False
    return bool(
        value.get("node_set_sha256") == expected_set_digest
        and value.get("node_order_sha256") == expected_order_digest
        and digest == expected_identity_digest
    )


def _is_exact_runtime(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "python_implementation",
        "python_version",
        "pytest_version",
        "pluggy_version",
        "uv_version",
        "platform",
        "installed_distributions",
    }:
        return False
    if not isinstance(value.get("python_implementation"), str) or not value[
        "python_implementation"
    ]:
        return False
    if any(
        not isinstance(value.get(field), str)
        or PYTEST_IDENTITY_VERSION_RE.fullmatch(value[field]) is None
        for field in ("python_version", "pytest_version", "pluggy_version", "uv_version")
    ):
        return False
    platform_record = value.get("platform")
    if not isinstance(platform_record, dict) or set(platform_record) != {
        "os_name",
        "sys_platform",
        "system",
        "release",
        "machine",
        "python_platform",
        "cache_tag",
    } or any(not isinstance(item, str) or not item for item in platform_record.values()):
        return False
    distributions = value.get("installed_distributions")
    if not isinstance(distributions, list) or not distributions:
        return False
    names: list[str] = []
    versions: dict[str, str] = {}
    for record in distributions:
        if not isinstance(record, dict) or set(record) != {"name", "version"}:
            return False
        name = record.get("name")
        version = record.get("version")
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is None
            or not isinstance(version, str)
            or not version
            or name in versions
        ):
            return False
        names.append(name)
        versions[name] = version
    return bool(
        names == sorted(names, key=lambda item: item.encode("utf-8"))
        and versions.get("pytest") == value.get("pytest_version")
        and versions.get("pluggy") == value.get("pluggy_version")
    )


def _is_exact_environment_qualification(value: object) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value) == {"status", "security_role", "qualification_scope", "runtime"}
        and value.get("status") == PYTEST_IDENTITY_ENVIRONMENT_STATUS
        and value.get("security_role") == PYTEST_IDENTITY_ENVIRONMENT_SECURITY_ROLE
        and value.get("qualification_scope") == PYTEST_IDENTITY_ENVIRONMENT_SCOPE
        and _is_exact_runtime(value.get("runtime"))
    )


def _is_exact_pytest_source(value: object, baseline_sha256: object) -> bool:
    expected_keys = {
        "mode",
        "assurance_tier",
        "requested_ref",
        "evaluated_commit",
        "content_may_differ_from_evaluated_commit",
        "baseline_commit_binding",
        "git_manifest_sha256",
        "validator_binding",
        "baseline_binding",
        "branch_evidence_eligible",
        "filesystem_isolation_enforced",
        "network_isolation_enforced",
        "collection_snapshot_manifest_sha256",
        "head_binding",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        return False
    validator_binding = value.get("validator_binding")
    baseline_binding = value.get("baseline_binding")
    head_binding = value.get("head_binding")
    if (
        not isinstance(validator_binding, dict)
        or set(validator_binding) != {"path", "status", "git_blob_oid", "sha256"}
        or validator_binding.get("path") != PYTEST_IDENTITY_TOOL_PATH
        or validator_binding.get("status")
        != PYTEST_IDENTITY_VALIDATOR_BINDING_STATUS
        or not _is_git_object_id(validator_binding.get("git_blob_oid"))
        or not _is_sha256(validator_binding.get("sha256"))
        or not isinstance(baseline_binding, dict)
        or set(baseline_binding) != {"path", "status", "git_blob_oid", "sha256"}
        or baseline_binding.get("path") != PYTEST_IDENTITY_BASELINE_PATH
        or baseline_binding.get("status")
        != PYTEST_IDENTITY_BASELINE_BINDING_STATUS
        or not _is_git_object_id(baseline_binding.get("git_blob_oid"))
        or not _is_sha256(baseline_binding.get("sha256"))
        or baseline_binding.get("sha256") != baseline_sha256
        or not isinstance(head_binding, dict)
        or set(head_binding) != {"status", "start_commit", "end_commit"}
        or head_binding.get("status") != PYTEST_IDENTITY_HEAD_BINDING_STATUS
    ):
        return False
    requested = value.get("requested_ref")
    evaluated = value.get("evaluated_commit")
    start_commit = head_binding.get("start_commit")
    end_commit = head_binding.get("end_commit")
    return bool(
        value.get("mode") == "GIT_BLOB_SNAPSHOT"
        and value.get("assurance_tier")
        == "COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC"
        and _is_git_object_id(requested)
        and requested == evaluated == start_commit == end_commit
        and value.get("content_may_differ_from_evaluated_commit") is False
        and value.get("baseline_commit_binding")
        == "EXCLUDED_TO_AVOID_SELF_REFERENCE"
        and _is_sha256(value.get("git_manifest_sha256"))
        and _is_sha256(value.get("collection_snapshot_manifest_sha256"))
        and value.get("branch_evidence_eligible") is False
        and value.get("filesystem_isolation_enforced") is False
        and value.get("network_isolation_enforced") is False
    )


def _pytest_test_identity_result(
    spec: CheckSpec,
    invocation: Invocation,
    command: list[str],
    protected_hashes: Mapping[str, str | None],
) -> CheckResult:
    result = _normal_result(spec, invocation, command)
    payload = _parse_json_output(invocation)
    exact_top_level = bool(
        isinstance(payload, dict)
        and set(payload)
        == {
            "schema",
            "operation",
            "outcome",
            "source",
            "test_identity_sha256",
            "test_identity",
            "environment_qualification",
            "errors",
            "baseline_sha256",
        }
    )
    try:
        exact_report = bool(
            invocation.returncode == 0
            and invocation.stderr == ""
            and exact_top_level
            and payload is not None
            and payload.get("schema") == PYTEST_IDENTITY_EVALUATION_SCHEMA
            and payload.get("operation") == "CHECK"
            and payload.get("outcome") == "PASS"
            and payload.get("errors") == []
            and _is_sha256(payload.get("baseline_sha256"))
            and _is_exact_test_identity(
                payload.get("test_identity"), payload.get("test_identity_sha256")
            )
            and _is_exact_environment_qualification(
                payload.get("environment_qualification")
            )
            and _is_exact_pytest_source(
                payload.get("source"), payload.get("baseline_sha256")
            )
            and payload.get("baseline_sha256")
            == protected_hashes.get(PYTEST_IDENTITY_BASELINE_PATH)
            and isinstance(payload.get("source"), dict)
            and isinstance(payload["source"].get("validator_binding"), dict)
            and payload["source"]["validator_binding"].get("sha256")
            == protected_hashes.get(PYTEST_IDENTITY_TOOL_PATH)
        )
    except Exception:
        exact_report = False
    result.status = (
        ResultStatus.EXPECTED_BLOCKED if exact_report else ResultStatus.FAIL
    )
    result.details.update(
        {
            "exact_diagnostic_report": exact_report,
            "diagnostic_comparison": "PASSED" if exact_report else "REJECTED",
            "admission_eligible": False,
            "security_gate_eligible": False,
            "branch_evidence_eligible": False,
            "m0_completion_effect": "NONE",
        }
    )
    if exact_report:
        result.details.update(
            {
                "blocker_code": PYTEST_IDENTITY_BLOCKER_CODE,
                "reason": (
                    "The reviewed pytest identity matched, but collection was not "
                    "executed with operating-system filesystem or network isolation."
                ),
            }
        )
    return result


def _shellworld_result(
    spec: CheckSpec, invocation: Invocation, command: list[str], root: Path
) -> CheckResult:
    result = _normal_result(spec, invocation, command)
    if invocation.returncode == 0:
        return result

    payload = _parse_json_output(invocation)
    manifest_path = root / SHELLWORLD_MANIFEST
    current_path = root / SHELLWORLD_MUTABLE_SPEC
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        matching_entries = [
            item
            for item in manifest.get("consumed_artifacts", [])
            if item.get("path") == SHELLWORLD_MUTABLE_SPEC.as_posix()
        ]
        manifest_expected = (
            matching_entries[0].get("sha256")
            if len(matching_entries) == 1
            else None
        )
        current = _sha256(current_path) if current_path.is_file() else None
    except (OSError, ValueError, json.JSONDecodeError):
        manifest_expected = None
        current = None

    checks = payload.get("checks", {}) if payload else {}
    exact_failed_check = (
        isinstance(checks, dict)
        and checks.get("run_manifest_hashes_and_self_hash") == "FAILED"
        and all(
            value == "PASSED"
            for key, value in checks.items()
            if key != "run_manifest_hashes_and_self_hash"
        )
    )
    exact_output = bool(
        payload
        and payload.get("outcome") == "FAILED"
        and payload.get("errors") == [SHELLWORLD_EXACT_ERROR]
        and payload.get("counts", {}).get("errors") == 1
        and exact_failed_check
    )
    exact_hashes = (
        manifest_expected == SHELLWORLD_EXPECTED_SPEC_SHA256
        and current == SHELLWORLD_REVIEWED_CURRENT_SPEC_SHA256
        and manifest_expected != current
    )
    result.details.update(
        {
            "stale_path": SHELLWORLD_MUTABLE_SPEC.as_posix(),
            "manifest_expected_sha256": manifest_expected,
            "reviewed_current_sha256": current,
            "exact_validator_output": exact_output,
            "exact_reviewed_hash_pair": exact_hashes,
        }
    )
    if invocation.returncode == 1 and exact_output and exact_hashes:
        result.status = ResultStatus.KNOWN_STALE
        result.details["policy"] = (
            "Retain the immutable V1 run; supersede it with a V2 contract-bound run "
            "instead of rewriting the historical manifest."
        )
    return result


def _pilot_blocked_result(
    spec: CheckSpec, invocation: Invocation, command: list[str]
) -> CheckResult:
    result = _normal_result(spec, invocation, command)
    if invocation.returncode == 0:
        return result
    payload = _parse_json_output(invocation)
    exact_blocker = bool(
        invocation.returncode == 1
        and payload
        and payload.get("structural_validation") == "PASSED"
        and payload.get("scientific_release_gate") == "BLOCKED"
        and payload.get("strict_science_requested") is True
        and payload.get("errors") == []
        and payload.get("counts", {}).get("open_blockers") == 7
    )
    result.details["exact_reviewed_blocker_state"] = exact_blocker
    if exact_blocker:
        result.status = ResultStatus.EXPECTED_BLOCKED
        result.details["reason"] = (
            "The pilot is structurally valid, but seven explicit scientific blockers "
            "prevent release."
        )
    return result


def _stabilizerness_blocked_result(
    spec: CheckSpec, invocation: Invocation, command: list[str]
) -> CheckResult:
    result = _normal_result(spec, invocation, command)
    payload = _parse_json_output(invocation)
    tool_identity = payload.get("tool_identity") if isinstance(payload, dict) else None
    dependency_identity = (
        payload.get("dependency_git_identity") if isinstance(payload, dict) else None
    )
    declaration_audit = (
        payload.get("declaration_audit") if isinstance(payload, dict) else None
    )
    side_effect_scope = (
        payload.get("side_effect_observation_scope")
        if isinstance(payload, dict)
        else None
    )
    environment_policy = (
        payload.get("environment_policy") if isinstance(payload, dict) else None
    )
    top_level_exact = bool(
        isinstance(payload, dict)
        and set(payload) == STABILIZERNESS_REPORT_TOP_LEVEL_KEYS
    )
    declaration_entries_exact = bool(
        isinstance(declaration_audit, dict)
        and set(declaration_audit)
        == STABILIZERNESS_LOCAL_DECLARATIONS | STABILIZERNESS_IMPORTED_DECLARATIONS
        and all(
            isinstance(declaration_audit.get(name), dict)
            and set(declaration_audit[name]) == STABILIZERNESS_DECLARATION_ENTRY_KEYS
            and declaration_audit[name].get("scope") == "target-local"
            and declaration_audit[name].get("audit_status") == "NOT_RUN"
            and declaration_audit[name].get("axioms") == []
            for name in STABILIZERNESS_LOCAL_DECLARATIONS
        )
        and all(
            isinstance(declaration_audit.get(name), dict)
            and set(declaration_audit[name]) == STABILIZERNESS_DECLARATION_ENTRY_KEYS
            and declaration_audit[name].get("scope") == "imported"
            and declaration_audit[name].get("audit_status") == "NOT_RUN"
            and declaration_audit[name].get("axioms") == []
            for name in STABILIZERNESS_IMPORTED_DECLARATIONS
        )
    )
    observed_paths = (
        side_effect_scope.get("observed_paths")
        if isinstance(side_effect_scope, dict)
        else None
    )
    side_effect_scope_exact = bool(
        isinstance(side_effect_scope, dict)
        and set(side_effect_scope) == STABILIZERNESS_SIDE_EFFECT_KEYS
        and side_effect_scope.get("method") == STABILIZERNESS_SIDE_EFFECT_METHOD
        and isinstance(observed_paths, list)
        and all(isinstance(path, str) and bool(path) for path in observed_paths)
        and observed_paths == sorted(observed_paths)
        and len(observed_paths) == len(set(observed_paths))
        and _stable_json_sha256(observed_paths)
        == STABILIZERNESS_OBSERVED_PATHS_SHA256
        and side_effect_scope.get("reused_unmeasured_cache_roots")
        == list(STABILIZERNESS_REUSED_UNMEASURED_CACHE_ROOTS)
        and side_effect_scope.get(
            "paths_outside_observed_formal_and_evidence_closure"
        )
        == STABILIZERNESS_OUTSIDE_OBSERVED_CLOSURE
        and side_effect_scope.get("future_dynamic_note")
        == STABILIZERNESS_FUTURE_DYNAMIC_NOTE
        and side_effect_scope.get("filesystem_isolation_enforced") is False
    )
    environment_policy_exact = bool(
        isinstance(environment_policy, dict)
        and set(environment_policy) == STABILIZERNESS_ENVIRONMENT_POLICY_KEYS
        and environment_policy.get("network_mode") == NETWORK_MODE
        and environment_policy.get("credential_minimized") is True
    )
    exact_blocker = bool(
        invocation.returncode == 2
        and invocation.stderr == ""
        and top_level_exact
        and payload.get("schema")
        == "agtxiv.stabilizerness-dynamic-validation-report/0.1.0"
        and payload.get("historical_evidence_schema_version") == "0.1.0-prototype"
        and payload.get("project") == "formal/AgtXIvStabilizerness"
        and payload.get("evidence_id") == STABILIZERNESS_EVIDENCE_ID
        and payload.get("declared_historical_status")
        == STABILIZERNESS_HISTORICAL_STATUS
        and payload.get("effective_validation_status") == "EXPECTED_BLOCKED"
        and payload.get("formalization_validation") == "EXPECTED_BLOCKED"
        and payload.get("dynamic_execution") == "EXPECTED_BLOCKED"
        and payload.get("dynamic_blocker_code") == STABILIZERNESS_BLOCKER_CODE
        and payload.get("dynamic_blocker_reason") == STABILIZERNESS_BLOCKER_REASON
        and payload.get("assurance_tier") == "LOCAL_PRELOADED_DIAGNOSTIC"
        and payload.get("cache_mode")
        == "DYNAMIC_NOT_RUN_FUTURE_PRELOADED_CACHE_UNVERIFIED"
        and payload.get("consumed_cache_closure") == "NOT_VERIFIED"
        and payload.get("source_clean_rebuild") is False
        and payload.get("network_mode") == NETWORK_MODE
        and payload.get("network_isolation_enforced") is False
        and payload.get("filesystem_isolation_enforced") is False
        and payload.get("network_note") == STABILIZERNESS_NETWORK_NOTE
        and payload.get("evidence_anchors") == "PASSED"
        and payload.get("artifact_hashes") == "PASSED"
        and payload.get("formal_input_inventory") == "PASSED"
        and payload.get("environment_binding") == "PASSED"
        and payload.get("placeholder_scan") == "PASSED"
        and payload.get("protected_input_integrity") == "PASSED"
        and isinstance(tool_identity, dict)
        and set(tool_identity) == STABILIZERNESS_TOOL_IDENTITY_KEYS
        and tool_identity.get("validation") == "NOT_RUN"
        and tool_identity.get("static_path_validation") == "PASSED"
        and tool_identity.get("dynamic_identity") == "NOT_RUN"
        and tool_identity.get("resolved_git_executable") is None
        and isinstance(tool_identity.get("paths"), dict)
        and set(tool_identity["paths"]) == STABILIZERNESS_TOOL_PATH_KEYS
        and tool_identity["paths"] == STABILIZERNESS_TOOL_PATHS
        and isinstance(dependency_identity, dict)
        and set(dependency_identity) == STABILIZERNESS_DEPENDENCY_IDENTITY_KEYS
        and dependency_identity.get("validation") == "NOT_RUN"
        and dependency_identity.get("source_tree_closure") == "NOT_RUN"
        and dependency_identity.get("consumed_cache_closure") == "NOT_VERIFIED"
        and payload.get("kernel_build") == "NOT_RUN"
        and payload.get("kernel_build_failure_excerpt") == []
        and payload.get("axiom_audit") == "NOT_RUN"
        and type(payload.get("declarations_audited")) is int
        and payload["declarations_audited"] == 0
        and type(payload.get("target_local_declarations_audited")) is int
        and payload["target_local_declarations_audited"] == 0
        and type(payload.get("imported_declarations_audited")) is int
        and payload["imported_declarations_audited"] == 0
        and payload.get("expected_target_local_declarations")
        == sorted(STABILIZERNESS_LOCAL_DECLARATIONS)
        and payload.get("expected_imported_declarations")
        == sorted(STABILIZERNESS_IMPORTED_DECLARATIONS)
        and payload.get("reported_axioms") == []
        and declaration_entries_exact
        and side_effect_scope_exact
        and environment_policy_exact
        and payload.get("external_commands") == []
        and payload.get("admission_eligible") is False
        and payload.get("security_gate_eligible") is False
        and payload.get("m0_completion_effect") == "NONE"
        and payload.get("admission_note") == STABILIZERNESS_ADMISSION_NOTE
        and payload.get("remaining_m0_security_blockers")
        == list(STABILIZERNESS_REMAINING_M0_SECURITY_BLOCKERS)
        and payload.get("scientific_acceptance_effect")
        == STABILIZERNESS_SCIENTIFIC_EFFECT
        and payload.get("scope_limitations")
        == list(STABILIZERNESS_SCOPE_LIMITATIONS)
        and payload.get("errors") == []
    )
    result.details["exact_reviewed_blocker_state"] = exact_blocker
    if exact_blocker:
        result.status = ResultStatus.EXPECTED_BLOCKED
        result.details["blocker_code"] = STABILIZERNESS_BLOCKER_CODE
        result.details["reason"] = STABILIZERNESS_BLOCKER_REASON
        result.details["policy"] = (
            "This local static diagnostic cannot authorize admission or merge; add "
            "an externally anchored cache closure or a clean isolated rebuild first."
        )
    return result


def execute_check(
    spec: CheckSpec,
    *,
    root: Path = REPO,
    command_runner: CommandRunner = _subprocess_runner,
    requirement_probe: RequirementProbe = _default_requirement_probe,
) -> CheckResult:
    missing_paths = [
        relative
        for relative in spec.required_repository_paths
        if not (root / relative).exists()
    ]
    if missing_paths:
        missing_status = spec.missing_repository_status
        missing_reason = (
            "This declared validation slice is not present in the checkout; "
            "no untracked working-tree artifact was assumed."
        )
        if (
            spec.classifier == "pytest-test-identity-expected-blocked"
            and missing_paths != [PYTEST_IDENTITY_BASELINE_PATH]
        ):
            missing_status = ResultStatus.FAIL
            missing_reason = (
                "A required normative pytest identity tool or schema is missing; "
                "the dormant exception applies only to the unreviewed baseline."
            )
        return CheckResult(
            spec.check_id,
            spec.description,
            missing_status,
            command=_resolve_command(spec, root),
            details={
                "missing_repository_paths": missing_paths,
                "reason": missing_reason,
            },
        )
    missing: list[str] = []
    resolved_tools: dict[str, str] = {}
    for requirement in spec.requirements:
        available, resolved = requirement_probe(requirement, root)
        if not available:
            missing.append(requirement.label)
        elif resolved is not None:
            resolved_tools[requirement.label] = resolved
    if missing:
        return CheckResult(
            spec.check_id,
            spec.description,
            ResultStatus.MISSING_TOOL,
            command=_resolve_command(spec, root),
            details={"missing_tools": missing, "resolved_tools": resolved_tools},
        )
    if spec.expected_blocker is not None:
        return CheckResult(
            spec.check_id,
            spec.description,
            ResultStatus.EXPECTED_BLOCKED,
            details={"reason": spec.expected_blocker},
        )
    if spec.command is None:
        return CheckResult(
            spec.check_id,
            spec.description,
            ResultStatus.PASS,
            details={"resolved_tools": resolved_tools},
        )

    try:
        before = _protected_hashes(root, spec.protected_paths)
    except ProtectedHashError as exc:
        return CheckResult(
            spec.check_id,
            spec.description,
            ResultStatus.FAIL,
            command=_resolve_command(spec, root),
            stderr=f"protected artifact pre-check failed: {exc}",
            details={
                "protected_hash_phase": "before",
                "protected_hash_error": str(exc),
                "resolved_tools": resolved_tools,
            },
        )
    environment = _preloaded_validation_environment()
    if spec.site_build:
        temporary_parent = root / "tmp"
        temporary_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="validate-repo-site-", dir=temporary_parent
        ) as temporary:
            temporary_path = Path(temporary)
            site_directory = temporary_path / "site"
            shim_directory = temporary_path / "bin"
            shim_directory.mkdir()
            (shim_directory / "python3").symlink_to(sys.executable)
            environment["PATH"] = str(shim_directory) + os.pathsep + environment.get("PATH", "")
            command = _resolve_command(spec, root, site_directory)
            invocation = command_runner(
                command, root, environment, spec.timeout_seconds
            )
    elif spec.classifier == "shellworld-known-stale":
        command = _resolve_command(spec, root)
        try:
            with tempfile.TemporaryDirectory(
                prefix="agtxiv-shellworld-validation-"
            ) as temporary:
                isolated_root = Path(temporary)
                isolated_validator = _prepare_shellworld_validation_tree(
                    root, isolated_root
                )
                invocation = command_runner(
                    [sys.executable, str(isolated_validator)],
                    isolated_root,
                    environment,
                    spec.timeout_seconds,
                )
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            return CheckResult(
                spec.check_id,
                spec.description,
                ResultStatus.FAIL,
                command=command,
                stderr=f"could not prepare isolated Shellworld validation: {exc}",
                details={"isolation_setup_failed": True},
            )
    else:
        command = _resolve_command(spec, root)
        invocation = command_runner(command, root, environment, spec.timeout_seconds)

    if spec.classifier == "shellworld-known-stale":
        result = _shellworld_result(spec, invocation, command, root)
    elif spec.classifier == "pilot-expected-blocked":
        result = _pilot_blocked_result(spec, invocation, command)
    elif spec.classifier == "stabilizerness-expected-blocked":
        result = _stabilizerness_blocked_result(spec, invocation, command)
    elif spec.classifier == "pytest-test-identity-expected-blocked":
        result = _pytest_test_identity_result(spec, invocation, command, before)
    elif spec.classifier == "normal":
        result = _normal_result(spec, invocation, command)
    else:
        raise ValueError(f"unknown classifier: {spec.classifier}")

    result.details.setdefault("resolved_tools", resolved_tools)
    if spec.classifier == "shellworld-known-stale":
        result.details["filesystem_execution_isolation"] = (
            "manifest-declared inputs copied to a temporary tree; tracked history "
            "was read-only"
        )
    try:
        after = _protected_hashes(root, spec.protected_paths)
    except ProtectedHashError as exc:
        result.status = ResultStatus.FAIL
        result.details["protected_hash_phase"] = "after"
        result.details["protected_hash_error"] = str(exc)
        result.stderr = (
            f"{result.stderr}\nprotected artifact post-check failed: {exc}"
        ).strip()
        return result
    changed = sorted(path for path in before if before[path] != after[path])
    if changed:
        result.status = ResultStatus.FAIL
        result.details["protected_artifacts_changed"] = changed
        result.details["protected_hashes_before"] = before
        result.details["protected_hashes_after"] = after
    return result


def select_checks(
    catalog: Sequence[CheckSpec], profile: str, only: Sequence[str] | None = None
) -> list[CheckSpec]:
    by_id = {spec.check_id: spec for spec in catalog}
    if len(by_id) != len(catalog):
        raise ValueError("validation catalog contains duplicate check IDs")
    if only:
        requested: list[str] = []
        for group in only:
            for identifier in group.split(","):
                identifier = identifier.strip()
                if identifier and identifier not in requested:
                    requested.append(identifier)
        unknown = [identifier for identifier in requested if identifier not in by_id]
        if unknown:
            raise ValueError(f"unknown check IDs: {', '.join(unknown)}")
        return [by_id[identifier] for identifier in requested]
    return [spec for spec in catalog if profile in spec.profiles]


def run_checks(
    checks: Sequence[CheckSpec],
    *,
    root: Path = REPO,
    keep_going: bool = False,
    command_runner: CommandRunner = _subprocess_runner,
    requirement_probe: RequirementProbe = _default_requirement_probe,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    stopped = False
    for spec in checks:
        if stopped:
            results.append(
                CheckResult(
                    spec.check_id,
                    spec.description,
                    ResultStatus.SKIPPED,
                    command=_resolve_command(spec, root),
                    details={"reason": "fail-fast after an earlier unexpected result"},
                )
            )
            continue
        result = execute_check(
            spec,
            root=root,
            command_runner=command_runner,
            requirement_probe=requirement_probe,
        )
        results.append(result)
        if result.status in {ResultStatus.FAIL, ResultStatus.MISSING_TOOL}:
            stopped = not keep_going
    return results


def build_report(
    profile: str, selected: Sequence[CheckSpec], results: Sequence[CheckResult]
) -> dict[str, Any]:
    counts = Counter(result.status.value for result in results)
    summary = {status.value: counts.get(status.value, 0) for status in ResultStatus}
    failed = summary[ResultStatus.FAIL] + summary[ResultStatus.MISSING_TOOL]
    return {
        "schema": REPORT_SCHEMA,
        "profile": profile,
        "network_mode": NETWORK_MODE,
        "network_isolation_enforced": False,
        "filesystem_isolation_enforced": False,
        "assurance_tier": "LOCAL_REPOSITORY_DIAGNOSTIC",
        "network_note": (
            "Checks are selected for local, preloaded inputs; this runner does not "
            "enforce operating-system outbound network blocking."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_root": str(REPO),
        "python": {
            "executable": sys.executable,
            "version": ".".join(str(part) for part in sys.version_info[:3]),
            "minimum_supported": ".".join(str(part) for part in MINIMUM_PYTHON),
        },
        "selected_checks": [spec.check_id for spec in selected],
        "results": [
            {
                **asdict(result),
                "status": result.status.value,
                "duration_seconds": round(result.duration_seconds, 6),
            }
            for result in results
        ],
        "summary": summary,
        "outcome": "FAIL" if failed else "PASS",
    }


def _print_list(catalog: Sequence[CheckSpec]) -> None:
    for spec in catalog:
        profiles = ",".join(spec.profiles)
        if spec.expected_blocker:
            command = "<expected blocker>"
        else:
            command = " ".join(_resolve_command(spec, REPO)) or "<preflight>"
        print(f"{spec.check_id:34} [{profiles}]\n  {spec.description}\n  {command}")


def _print_human_report(report: Mapping[str, Any]) -> None:
    print(
        f"AgtXIv repository validation: profile={report['profile']} "
        "network=offline-intended/preloaded OS-network-blocking=not-enforced "
        f"outcome={report['outcome']}"
    )
    for result in report["results"]:
        print(
            f"[{result['status']:16}] {result['check_id']} "
            f"({result['duration_seconds']:.3f}s)"
        )
        if result["status"] in {
            ResultStatus.FAIL.value,
            ResultStatus.MISSING_TOOL.value,
        }:
            output = (result.get("stderr") or result.get("stdout") or "").strip()
            if output:
                for line in output.splitlines()[-8:]:
                    print(f"  {line}")
            missing = result.get("details", {}).get("missing_tools", [])
            if missing:
                print(f"  missing: {', '.join(missing)}")
        if result["status"] in {
            ResultStatus.KNOWN_STALE.value,
            ResultStatus.EXPECTED_BLOCKED.value,
        }:
            details = result.get("details", {})
            explanation = details.get("reason") or details.get("policy")
            if explanation:
                print(f"  {explanation}")
    print("summary: " + " ".join(f"{key}={value}" for key, value in report["summary"].items()))


def _supported_python() -> bool:
    return sys.version_info[:2] >= MINIMUM_PYTHON


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile", choices=("fast", "full", "nightly"), default="fast"
    )
    parser.add_argument(
        "--list", action="store_true", help="list checks, profiles, and commands"
    )
    parser.add_argument(
        "--only",
        action="append",
        metavar="CHECK[,CHECK...]",
        help="run only named checks; may be repeated",
    )
    parser.add_argument(
        "--json-report",
        metavar="PATH|-",
        help="write the complete machine-readable report, or use '-' for stdout",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="continue after FAIL or MISSING_TOOL results",
    )
    args = parser.parse_args(argv)

    if not _supported_python():
        print(
            "AgtXIv validation requires Python "
            f"{MINIMUM_PYTHON[0]}.{MINIMUM_PYTHON[1]} or newer; "
            f"running {sys.version_info.major}.{sys.version_info.minor}.",
            file=sys.stderr,
        )
        return 2

    catalog = validation_catalog()
    if args.list:
        _print_list(catalog)
        return 0
    try:
        selected = select_checks(catalog, args.profile, args.only)
    except ValueError as exc:
        print(f"validation selection error: {exc}", file=sys.stderr)
        return 2
    if not selected:
        print("validation selection is empty", file=sys.stderr)
        return 2

    results = run_checks(selected, keep_going=args.keep_going)
    report = build_report(args.profile, selected, results)
    serialized = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.json_report == "-":
        sys.stdout.write(serialized)
    else:
        _print_human_report(report)
        if args.json_report:
            try:
                Path(args.json_report).write_text(serialized, encoding="utf-8")
            except OSError as exc:
                print(f"could not write JSON report: {exc}", file=sys.stderr)
                return 2
    return 0 if report["outcome"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
