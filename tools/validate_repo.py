#!/usr/bin/env python3
"""Run the AgtXIv repository validation profiles.

The runner is deliberately offline and read-only with respect to tracked source
artifacts.  It provides one inventory for the existing validators while keeping
known historical exceptions narrow, explicit, and machine-readable.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any


REPO = Path(__file__).resolve().parents[1]
MINIMUM_PYTHON = (3, 12)
REPORT_SCHEMA = "agtxiv.repository-validation-report/0.1.0"

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
            "The pinned repository-local Lean lake executable is available.",
            full,
            requirements=(repository_lake,),
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
            "lean-stabilizerness-dynamic",
            "Dynamically rebuild the Stabilizerness Lean example.",
            nightly,
            expected_blocker=(
                "M5 has not yet supplied a dynamic Stabilizerness validator; the current "
                "record is checked only as a frozen artifact."
            ),
        ),
        CheckSpec(
            "arxiv-intake-adversarial-corpus",
            "Run the grammar-complete offline arXiv intake and archive-security corpus.",
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


def _protected_hashes(root: Path, paths: Sequence[str]) -> dict[str, str | None]:
    return {
        relative: _sha256(root / relative) if (root / relative).is_file() else None
        for relative in paths
    }


def _default_requirement_probe(
    requirement: ToolRequirement, root: Path
) -> tuple[bool, str | None]:
    if requirement.kind == "executable":
        resolved = shutil.which(requirement.value)
        return resolved is not None, resolved
    if requirement.kind == "repository-executable":
        candidate = root / requirement.value
        available = candidate.is_file() and os.access(candidate, os.X_OK)
        return available, str(candidate) if available else None
    if requirement.kind == "python-module":
        available = importlib.util.find_spec(requirement.value) is not None
        return available, requirement.value if available else None
    raise ValueError(f"unknown tool requirement kind: {requirement.kind}")


def _offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in (
        "ALL_PROXY",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "all_proxy",
        "https_proxy",
        "http_proxy",
    ):
        environment.pop(key, None)
    environment.update(
        {
            "AGTXIV_OFFLINE": "1",
            "NO_PROXY": "*",
            "no_proxy": "*",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
        }
    )
    return environment


def _subprocess_runner(
    command: Sequence[str], cwd: Path, environment: Mapping[str, str], timeout: int
) -> Invocation:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=dict(environment),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
        return Invocation(
            completed.returncode,
            completed.stdout,
            completed.stderr,
            time.monotonic() - started,
        )
    except FileNotFoundError as exc:
        return Invocation(127, "", str(exc), time.monotonic() - started)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        message = f"command timed out after {timeout} seconds"
        return Invocation(124, stdout, f"{stderr}\n{message}".strip(), time.monotonic() - started)


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


def _parse_json_output(invocation: Invocation) -> dict[str, Any] | None:
    try:
        payload = json.loads(invocation.stdout)
    except (json.JSONDecodeError, TypeError):
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
        return CheckResult(
            spec.check_id,
            spec.description,
            spec.missing_repository_status,
            command=_resolve_command(spec, root),
            details={
                "missing_repository_paths": missing_paths,
                "reason": (
                    "This declared validation slice is not present in the checkout; "
                    "no untracked working-tree artifact was assumed."
                ),
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

    before = _protected_hashes(root, spec.protected_paths)
    environment = _offline_environment()
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
    elif spec.classifier == "normal":
        result = _normal_result(spec, invocation, command)
    else:
        raise ValueError(f"unknown classifier: {spec.classifier}")

    result.details.setdefault("resolved_tools", resolved_tools)
    if spec.classifier == "shellworld-known-stale":
        result.details["execution_isolation"] = (
            "manifest-declared inputs copied to a temporary tree; tracked history "
            "was read-only"
        )
    after = _protected_hashes(root, spec.protected_paths)
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
        "offline": True,
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
        f"offline=yes outcome={report['outcome']}"
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
