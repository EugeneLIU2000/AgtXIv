from __future__ import annotations

import copy
from functools import cache
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from tools import validate_repo as validator
from tools import validate_stabilizerness_formalization as standalone_validator


def invocation(returncode: int = 0, stdout: str = "", stderr: str = "") -> validator.Invocation:
    return validator.Invocation(returncode, stdout, stderr, 0.01)


def pytest_identity_report() -> dict:
    node_ids = ["tests/test_alpha.py::test_alpha"]
    selected_node_ids = list(node_ids)
    identity = {
        "schema": validator.PYTEST_IDENTITY_SCHEMA,
        "evidence_scope": validator.PYTEST_IDENTITY_EVIDENCE_SCOPE,
        "collection_contract": copy.deepcopy(
            validator.PYTEST_IDENTITY_COLLECTION_CONTRACT
        ),
        "input_bindings": {
            relative: {"byte_size": 1, "sha256": character * 64}
            for relative, character in (
                (".python-version", "1"),
                ("pyproject.toml", "2"),
                ("uv.lock", "3"),
            )
        },
        "counts": {
            "collected": 1,
            "selected": 1,
            "deselected": 0,
            "collection_skipped": 0,
            "marker_declarations": 0,
        },
        "node_ids": node_ids,
        "selected_node_ids": selected_node_ids,
        "deselected_node_ids": [],
        "collection_skips": [],
        "marker_declarations": [],
        "node_set_sha256": validator._length_prefixed_sha256(
            b"agtxiv.pytest-node-set/1.0.0\0", node_ids
        ),
        "node_order_sha256": validator._length_prefixed_sha256(
            b"agtxiv.pytest-node-order/1.0.0\0", selected_node_ids
        ),
    }
    commit = "a" * 40
    baseline_sha256 = "b" * 64
    return {
        "schema": validator.PYTEST_IDENTITY_EVALUATION_SCHEMA,
        "operation": "CHECK",
        "outcome": "PASS",
        "source": {
            "mode": "GIT_BLOB_SNAPSHOT",
            "assurance_tier": "COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC",
            "requested_ref": commit,
            "evaluated_commit": commit,
            "content_may_differ_from_evaluated_commit": False,
            "baseline_commit_binding": "EXCLUDED_TO_AVOID_SELF_REFERENCE",
            "git_manifest_sha256": "c" * 64,
            "validator_binding": {
                "path": validator.PYTEST_IDENTITY_TOOL_PATH,
                "status": validator.PYTEST_IDENTITY_VALIDATOR_BINDING_STATUS,
                "git_blob_oid": "d" * 40,
                "sha256": "e" * 64,
            },
            "baseline_binding": {
                "path": validator.PYTEST_IDENTITY_BASELINE_PATH,
                "status": validator.PYTEST_IDENTITY_BASELINE_BINDING_STATUS,
                "git_blob_oid": "f" * 40,
                "sha256": baseline_sha256,
            },
            "branch_evidence_eligible": False,
            "filesystem_isolation_enforced": False,
            "network_isolation_enforced": False,
            "collection_snapshot_manifest_sha256": "4" * 64,
            "head_binding": {
                "status": validator.PYTEST_IDENTITY_HEAD_BINDING_STATUS,
                "start_commit": commit,
                "end_commit": commit,
            },
        },
        "test_identity_sha256": validator._pytest_identity_digest(identity),
        "test_identity": identity,
        "environment_qualification": {
            "status": validator.PYTEST_IDENTITY_ENVIRONMENT_STATUS,
            "security_role": validator.PYTEST_IDENTITY_ENVIRONMENT_SECURITY_ROLE,
            "qualification_scope": validator.PYTEST_IDENTITY_ENVIRONMENT_SCOPE,
            "runtime": {
                "python_implementation": "CPython",
                "python_version": "3.12.11",
                "pytest_version": "7.4.4",
                "pluggy_version": "1.6.0",
                "uv_version": "0.10.0",
                "platform": {
                    "os_name": "posix",
                    "sys_platform": "linux",
                    "system": "Linux",
                    "release": "fixture",
                    "machine": "x86_64",
                    "python_platform": "linux-x86_64",
                    "cache_tag": "cpython-312",
                },
                "installed_distributions": [
                    {"name": "pluggy", "version": "1.6.0"},
                    {"name": "pytest", "version": "7.4.4"},
                ],
            },
        },
        "errors": [],
        "baseline_sha256": baseline_sha256,
    }


def test_catalog_has_three_profiles_and_all_python_commands_use_current_interpreter() -> None:
    catalog = validator.validation_catalog()
    assert {profile for spec in catalog for profile in spec.profiles} == {
        "fast",
        "full",
        "nightly",
    }
    ids = [spec.check_id for spec in catalog]
    assert len(ids) == len(set(ids))
    by_id = {spec.check_id: spec for spec in catalog}
    pytest_identity = by_id["pytest-test-identity"]
    assert ids.index("pytest-test-identity") + 1 == ids.index("test-suite")
    assert pytest_identity.profiles == ("fast", "full", "nightly")
    assert pytest_identity.command == (
        "{python}",
        validator.PYTEST_IDENTITY_TOOL_PATH,
        "--check",
        validator.PYTEST_IDENTITY_BASELINE_PATH,
        "--source-head",
    )
    assert pytest_identity.classifier == "pytest-test-identity-expected-blocked"
    assert pytest_identity.timeout_seconds == 300
    assert pytest_identity.missing_repository_status == (
        validator.ResultStatus.EXPECTED_BLOCKED
    )
    assert pytest_identity.required_repository_paths == (
        validator.PYTEST_IDENTITY_TOOL_PATH,
        validator.PYTEST_IDENTITY_SCHEMA_PATH,
        validator.PYTEST_IDENTITY_BASELINE_PATH,
    )
    assert pytest_identity.protected_paths == (
        validator.PYTEST_IDENTITY_BASELINE_PATH,
        validator.PYTEST_IDENTITY_TOOL_PATH,
        validator.PYTEST_IDENTITY_SCHEMA_PATH,
        "tools/validate_repo.py",
    )
    assert [(item.kind, item.value) for item in pytest_identity.requirements] == [
        ("python-module", "pytest"),
        ("executable", "git"),
        ("executable", "uv"),
    ]
    assert by_id["test-suite"].profiles == ("fast", "full", "nightly")
    assert by_id["lean-stabilizerness-dynamic"].profiles == ("full", "nightly")
    assert by_id["lean-stabilizerness-dynamic"].expected_blocker is None
    assert by_id["lean-stabilizerness-dynamic"].command == (
        "{python}",
        "tools/validate_stabilizerness_formalization.py",
    )
    assert by_id["lean-stabilizerness-dynamic"].timeout_seconds == 120
    assert by_id["lean-stabilizerness-dynamic"].requirements == ()
    assert (
        by_id["lean-stabilizerness-dynamic"].classifier
        == "stabilizerness-expected-blocked"
    )
    assert by_id["v2-paper-agentization"].required_repository_paths == (
        "tools/validate_v2_paper_agentization.py",
    )
    for spec in catalog:
        resolved = validator._resolve_command(spec, validator.REPO)
        if spec.command and spec.command[0] == "{python}":
            assert resolved[0] == sys.executable


def test_profile_selection_and_only_are_stable() -> None:
    catalog = validator.validation_catalog()
    fast = validator.select_checks(catalog, "fast")
    assert fast
    assert all("fast" in spec.profiles for spec in fast)
    fast_ids = {spec.check_id for spec in fast}
    assert "shellworld-v1-run" in fast_ids
    assert "pytest-test-identity" in fast_ids
    assert "test-suite" in fast_ids

    selected = validator.select_checks(
        catalog, "fast", ["lean-root-math,v2-paper-agentization", "lean-root-math"]
    )
    assert [spec.check_id for spec in selected] == [
        "lean-root-math",
        "v2-paper-agentization",
    ]


def test_normal_pass_fail_and_keep_going_without_running_repository() -> None:
    checks = [
        validator.CheckSpec("one", "first", ("fast",), ("{python}", "one.py")),
        validator.CheckSpec("two", "second", ("fast",), ("{python}", "two.py")),
    ]
    calls: list[list[str]] = []

    def fake_runner(command, cwd, environment, timeout):
        calls.append(list(command))
        assert cwd == validator.REPO
        assert environment["AGTXIV_NETWORK_MODE"] == validator.NETWORK_MODE
        assert command[0] == sys.executable
        return invocation(1 if command[-1] == "one.py" else 0, stderr="boom")

    fail_fast = validator.run_checks(checks, command_runner=fake_runner)
    assert [result.status for result in fail_fast] == [
        validator.ResultStatus.FAIL,
        validator.ResultStatus.SKIPPED,
    ]
    assert len(calls) == 1

    calls.clear()
    continued = validator.run_checks(
        checks, command_runner=fake_runner, keep_going=True
    )
    assert [result.status for result in continued] == [
        validator.ResultStatus.FAIL,
        validator.ResultStatus.PASS,
    ]
    assert len(calls) == 2


def test_missing_tool_is_distinct_and_does_not_spawn() -> None:
    check = validator.CheckSpec(
        "needs-tool",
        "requires a tool",
        ("full",),
        ("{python}", "check.py"),
        requirements=(
            validator.ToolRequirement("executable", "absent", "absent tool"),
        ),
    )

    def must_not_run(*args):
        raise AssertionError("a check with a missing tool must not spawn")

    result = validator.execute_check(
        check,
        command_runner=must_not_run,
        requirement_probe=lambda requirement, root: (False, None),
    )
    assert result.status == validator.ResultStatus.MISSING_TOOL
    assert result.details["missing_tools"] == ["absent tool"]


def test_pytest_identity_missing_baseline_is_expected_blocked_without_spawn(
    tmp_path: Path,
) -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "pytest-test-identity"
    )
    for relative in (
        validator.PYTEST_IDENTITY_TOOL_PATH,
        validator.PYTEST_IDENTITY_SCHEMA_PATH,
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    def must_not_run(*args):
        raise AssertionError("missing baseline must stop before probes or subprocesses")

    result = validator.execute_check(
        spec,
        root=tmp_path,
        command_runner=must_not_run,
        requirement_probe=must_not_run,
    )
    assert result.status == validator.ResultStatus.EXPECTED_BLOCKED
    assert result.details["missing_repository_paths"] == [
        validator.PYTEST_IDENTITY_BASELINE_PATH
    ]


@pytest.mark.parametrize(
    "missing_path",
    [
        validator.PYTEST_IDENTITY_TOOL_PATH,
        validator.PYTEST_IDENTITY_SCHEMA_PATH,
    ],
)
def test_pytest_identity_missing_tool_or_schema_fails_without_spawn(
    tmp_path: Path, missing_path: str
) -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "pytest-test-identity"
    )
    for relative in spec.required_repository_paths:
        if relative == missing_path:
            continue
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    def must_not_run(*args):
        raise AssertionError("missing normative tool/schema must fail before spawning")

    result = validator.execute_check(
        spec,
        root=tmp_path,
        command_runner=must_not_run,
        requirement_probe=must_not_run,
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.details["missing_repository_paths"] == [missing_path]
    assert "normative pytest identity tool or schema" in result.details["reason"]


def test_pytest_identity_combined_missing_paths_cannot_use_dormant_exception(
    tmp_path: Path,
) -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "pytest-test-identity"
    )

    def must_not_run(*args):
        raise AssertionError("combined missing paths must fail before spawning")

    result = validator.execute_check(
        spec,
        root=tmp_path,
        command_runner=must_not_run,
        requirement_probe=must_not_run,
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.details["missing_repository_paths"] == list(
        spec.required_repository_paths
    )
    assert "dormant exception" in result.details["reason"]


def test_exact_pytest_identity_diagnostic_is_expected_blocked() -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "pytest-test-identity"
    )
    payload = pytest_identity_report()
    result = validator._pytest_test_identity_result(
        spec,
        invocation(0, json.dumps(payload, sort_keys=True), ""),
        [sys.executable, validator.PYTEST_IDENTITY_TOOL_PATH],
        {
            validator.PYTEST_IDENTITY_BASELINE_PATH: payload["baseline_sha256"],
            validator.PYTEST_IDENTITY_TOOL_PATH: payload["source"][
                "validator_binding"
            ]["sha256"],
        },
    )
    assert result.status == validator.ResultStatus.EXPECTED_BLOCKED
    assert result.details == {
        "exact_diagnostic_report": True,
        "diagnostic_comparison": "PASSED",
        "admission_eligible": False,
        "security_gate_eligible": False,
        "branch_evidence_eligible": False,
        "m0_completion_effect": "NONE",
        "blocker_code": validator.PYTEST_IDENTITY_BLOCKER_CODE,
        "reason": (
            "The reviewed pytest identity matched, but collection was not "
            "executed with operating-system filesystem or network isolation."
        ),
    }


def test_execute_check_routes_exact_pytest_identity_report_through_classifier(
    tmp_path: Path,
) -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "pytest-test-identity"
    )
    for index, relative in enumerate(spec.protected_paths, start=1):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"protected-{index}\n".encode())
    protected = validator._protected_hashes(tmp_path, spec.protected_paths)
    payload = pytest_identity_report()
    payload["baseline_sha256"] = protected[
        validator.PYTEST_IDENTITY_BASELINE_PATH
    ]
    payload["source"]["baseline_binding"]["sha256"] = payload[
        "baseline_sha256"
    ]
    payload["source"]["validator_binding"]["sha256"] = protected[
        validator.PYTEST_IDENTITY_TOOL_PATH
    ]

    def runner(command, cwd, environment, timeout):
        assert command[-1] == "--source-head"
        assert timeout == 300
        return invocation(0, json.dumps(payload, sort_keys=True), "")

    result = validator.execute_check(
        spec,
        root=tmp_path,
        command_runner=runner,
        requirement_probe=lambda requirement, root: (True, requirement.value),
    )
    assert result.status == validator.ResultStatus.EXPECTED_BLOCKED
    assert result.details["diagnostic_comparison"] == "PASSED"
    assert result.details["resolved_tools"] == {
        "Python module pytest": "pytest",
        "git": "git",
        "uv": "uv",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "returncode",
        "stderr",
        "top-extra",
        "source-extra",
        "identity-extra",
        "environment-extra",
        "validator-extra",
        "baseline-binding-extra",
        "head-extra",
        "runtime-extra",
        "platform-extra",
        "distribution-extra",
        "contract-extra",
        "input-binding-extra",
        "counts-extra",
        "assurance-promotion",
        "branch-promotion",
        "filesystem-promotion",
        "network-promotion",
        "head-changed",
        "baseline-status",
        "validator-status",
        "baseline-digest",
        "protected-baseline-digest",
        "protected-validator-digest",
        "environment-status",
        "environment-security-role",
        "malformed-python-version",
        "pytest-version-trailing-lf",
        "identity-digest",
        "contract-bool-impostor",
        "count-bool",
        "input-byte-size-bool",
        "malformed-marker-node",
        "errors",
        "outcome",
    ],
)
def test_pytest_identity_classifier_rejects_every_contradiction_and_unknown_field(
    mutation: str,
) -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "pytest-test-identity"
    )
    payload = pytest_identity_report()
    returncode = 0
    stderr = ""
    protected = {
        validator.PYTEST_IDENTITY_BASELINE_PATH: payload["baseline_sha256"],
        validator.PYTEST_IDENTITY_TOOL_PATH: payload["source"]["validator_binding"][
            "sha256"
        ],
    }
    if mutation == "returncode":
        returncode = 1
    elif mutation == "stderr":
        stderr = "unexpected diagnostics"
    elif mutation == "top-extra":
        payload["unexpected"] = True
    elif mutation == "source-extra":
        payload["source"]["unexpected"] = True
    elif mutation == "identity-extra":
        payload["test_identity"]["unexpected"] = True
    elif mutation == "environment-extra":
        payload["environment_qualification"]["unexpected"] = True
    elif mutation == "validator-extra":
        payload["source"]["validator_binding"]["unexpected"] = True
    elif mutation == "baseline-binding-extra":
        payload["source"]["baseline_binding"]["unexpected"] = True
    elif mutation == "head-extra":
        payload["source"]["head_binding"]["unexpected"] = True
    elif mutation == "runtime-extra":
        payload["environment_qualification"]["runtime"]["unexpected"] = True
    elif mutation == "platform-extra":
        payload["environment_qualification"]["runtime"]["platform"][
            "unexpected"
        ] = True
    elif mutation == "distribution-extra":
        payload["environment_qualification"]["runtime"][
            "installed_distributions"
        ][0]["unexpected"] = True
    elif mutation == "contract-extra":
        payload["test_identity"]["collection_contract"]["unexpected"] = True
    elif mutation == "input-binding-extra":
        payload["test_identity"]["input_bindings"]["uv.lock"][
            "unexpected"
        ] = True
    elif mutation == "counts-extra":
        payload["test_identity"]["counts"]["unexpected"] = 0
    elif mutation == "assurance-promotion":
        payload["source"]["assurance_tier"] = "BRANCH_EVIDENCE"
    elif mutation == "branch-promotion":
        payload["source"]["branch_evidence_eligible"] = True
    elif mutation == "filesystem-promotion":
        payload["source"]["filesystem_isolation_enforced"] = True
    elif mutation == "network-promotion":
        payload["source"]["network_isolation_enforced"] = True
    elif mutation == "head-changed":
        payload["source"]["head_binding"]["end_commit"] = "9" * 40
    elif mutation == "baseline-status":
        payload["source"]["baseline_binding"]["status"] = "UNREVIEWED"
    elif mutation == "validator-status":
        payload["source"]["validator_binding"]["status"] = "UNBOUND"
    elif mutation == "baseline-digest":
        payload["source"]["baseline_binding"]["sha256"] = "9" * 64
    elif mutation == "protected-baseline-digest":
        protected[validator.PYTEST_IDENTITY_BASELINE_PATH] = "9" * 64
    elif mutation == "protected-validator-digest":
        protected[validator.PYTEST_IDENTITY_TOOL_PATH] = "9" * 64
    elif mutation == "environment-status":
        payload["environment_qualification"]["status"] = "UNLOCKED"
    elif mutation == "environment-security-role":
        payload["environment_qualification"]["security_role"] = "IGNORED"
    elif mutation == "malformed-python-version":
        payload["environment_qualification"]["runtime"][
            "python_version"
        ] = "not-a-version"
    elif mutation == "pytest-version-trailing-lf":
        payload["environment_qualification"]["runtime"][
            "pytest_version"
        ] += "\n"
    elif mutation == "identity-digest":
        payload["test_identity_sha256"] = "9" * 64
    elif mutation == "contract-bool-impostor":
        payload["test_identity"]["collection_contract"]["plugin_autoload"] = 0
    elif mutation == "count-bool":
        payload["test_identity"]["counts"]["selected"] = True
    elif mutation == "input-byte-size-bool":
        payload["test_identity"]["input_bindings"]["uv.lock"][
            "byte_size"
        ] = True
    elif mutation == "malformed-marker-node":
        payload["test_identity"]["marker_declarations"] = [
            {"node_id": [], "markers": []}
        ]
        payload["test_identity"]["counts"]["marker_declarations"] = 1
    elif mutation == "errors":
        payload["errors"] = [{"code": "CONTRADICTION", "message": "not a pass"}]
    elif mutation == "outcome":
        payload["outcome"] = "FAIL"
    else:  # pragma: no cover - parameter list and implementation are one contract
        raise AssertionError(mutation)

    result = validator._pytest_test_identity_result(
        spec,
        invocation(returncode, json.dumps(payload, sort_keys=True), stderr),
        [sys.executable, validator.PYTEST_IDENTITY_TOOL_PATH],
        protected,
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.status != validator.ResultStatus.KNOWN_STALE
    assert result.details["exact_diagnostic_report"] is False
    assert result.details["diagnostic_comparison"] == "REJECTED"
    assert result.details["admission_eligible"] is False
    assert result.details["security_gate_eligible"] is False
    assert result.details["m0_completion_effect"] == "NONE"
    assert "blocker_code" not in result.details


def protected_check() -> validator.CheckSpec:
    return validator.CheckSpec(
        "protected",
        "protected artifact fixture",
        ("full",),
        ("{python}", "check.py"),
        protected_paths=("verification-result.json",),
    )


def test_protected_hash_symlink_is_structured_failure_without_spawn(tmp_path: Path) -> None:
    target = tmp_path / "real.json"
    target.write_text("{}\n", encoding="utf-8")
    try:
        (tmp_path / "verification-result.json").symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")

    def must_not_run(*args):
        raise AssertionError("unsafe protected artifact must fail before spawn")

    result = validator.execute_check(
        protected_check(), root=tmp_path, command_runner=must_not_run
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.details["protected_hash_phase"] == "before"
    assert "regular non-symlink" in result.stderr


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_protected_hash_fifo_is_structured_failure_without_blocking(tmp_path: Path) -> None:
    os.mkfifo(tmp_path / "verification-result.json")

    def must_not_run(*args):
        raise AssertionError("FIFO protected artifact must fail before spawn")

    result = validator.execute_check(
        protected_check(), root=tmp_path, command_runner=must_not_run
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.details["protected_hash_phase"] == "before"
    assert "regular non-symlink" in result.stderr


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_protected_hash_postcheck_fifo_is_structured_failure(tmp_path: Path) -> None:
    protected = tmp_path / "verification-result.json"
    protected.write_text("{}\n", encoding="utf-8")

    def mutating_runner(command, cwd, environment, timeout):
        protected.unlink()
        os.mkfifo(protected)
        return invocation()

    result = validator.execute_check(
        protected_check(), root=tmp_path, command_runner=mutating_runner
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.details["protected_hash_phase"] == "after"
    assert "post-check failed" in result.stderr


def test_guarded_protected_reader_detects_change_during_read(
    monkeypatch, tmp_path: Path
) -> None:
    protected = tmp_path / "verification-result.json"
    protected.write_bytes(b"AAAA")
    original_read = validator.os.read
    changed = False

    def changing_read(descriptor: int, size: int) -> bytes:
        nonlocal changed
        if not changed:
            changed = True
            protected.write_bytes(b"BBBB")
        return original_read(descriptor, size)

    monkeypatch.setattr(validator.os, "read", changing_read)
    with pytest.raises(validator.ProtectedHashError, match="changed while being read"):
        validator._guarded_protected_bytes(
            tmp_path, "verification-result.json", max_bytes=16
        )


def test_guarded_protected_reader_detects_growth_beyond_cap(
    monkeypatch, tmp_path: Path
) -> None:
    protected = tmp_path / "verification-result.json"
    protected.write_bytes(b"AAAA")
    original_read = validator.os.read
    changed = False

    def growing_read(descriptor: int, size: int) -> bytes:
        nonlocal changed
        if not changed:
            changed = True
            with protected.open("ab") as stream:
                stream.write(b"BBBBBBBB")
        return original_read(descriptor, size)

    monkeypatch.setattr(validator.os, "read", growing_read)
    with pytest.raises(validator.ProtectedHashError, match="grew beyond"):
        validator._guarded_protected_bytes(
            tmp_path, "verification-result.json", max_bytes=4
        )


def test_guarded_protected_reader_allows_unrelated_directory_child_churn(
    monkeypatch, tmp_path: Path
) -> None:
    protected = tmp_path / "verification-result.json"
    protected.write_bytes(b"{}\n")
    original_read = validator.os.read
    changed = False

    def changing_read(descriptor: int, size: int) -> bytes:
        nonlocal changed
        if not changed:
            changed = True
            (tmp_path / "unrelated").mkdir()
        return original_read(descriptor, size)

    monkeypatch.setattr(validator.os, "read", changing_read)
    assert validator._guarded_protected_bytes(
        tmp_path, "verification-result.json", max_bytes=16
    ) == b"{}\n"


def shellworld_payload(error: str = validator.SHELLWORLD_EXACT_ERROR) -> str:
    return json.dumps(
        {
            "outcome": "FAILED",
            "errors": [error],
            "counts": {"errors": 1},
            "checks": {
                "component_completeness_and_bridge_purity": "PASSED",
                "evidence_blocker_refs_and_one_to_one_assessment": "PASSED",
                "exact_refs_anchors_and_rfc6901_targets": "PASSED",
                "non_promotion_and_status_separation": "PASSED",
                "normative_and_target_schema_validation": "PASSED",
                "normative_schema_fixture_consistency": "PASSED",
                "rerun_result_determinism": "PASSED",
                "run_manifest_hashes_and_self_hash": "FAILED",
            },
        }
    )


def test_shellworld_known_stale_requires_exact_output_and_reviewed_hash_pair() -> None:
    spec = next(
        spec
        for spec in validator.validation_catalog()
        if spec.check_id == "shellworld-v1-run"
    )
    command = validator._resolve_command(spec, validator.REPO)
    exact = validator._shellworld_result(
        spec, invocation(1, shellworld_payload()), command, validator.REPO
    )
    assert exact.status == validator.ResultStatus.KNOWN_STALE
    assert exact.details["manifest_expected_sha256"] == (
        validator.SHELLWORLD_EXPECTED_SPEC_SHA256
    )
    assert exact.details["reviewed_current_sha256"] == (
        validator.SHELLWORLD_REVIEWED_CURRENT_SPEC_SHA256
    )

    another_hash_error = validator._shellworld_result(
        spec,
        invocation(1, shellworld_payload("manifest hash mismatch: another-file")),
        command,
        validator.REPO,
    )
    assert another_hash_error.status == validator.ResultStatus.FAIL


def write_shellworld_manifest(root: Path, artifact_path: str) -> None:
    manifest = root / validator.SHELLWORLD_MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "consumed_artifacts": [{"path": artifact_path}],
                "produced_artifacts": [],
                "self_artifact": {"path": validator.SHELLWORLD_MANIFEST.as_posix()},
            }
        ),
        encoding="utf-8",
    )


def test_shellworld_isolation_rejects_traversal_as_structured_failure(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    (tmp_path / "outside.txt").write_text("outside", encoding="utf-8")
    write_shellworld_manifest(root, "../outside.txt")
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "shellworld-v1-run"
    )

    def must_not_run(*args):
        raise AssertionError("unsafe manifest paths must fail before spawning")

    result = validator.execute_check(
        spec,
        root=root,
        command_runner=must_not_run,
        requirement_probe=lambda requirement, repository: (True, requirement.value),
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.details["isolation_setup_failed"] is True
    assert "unsafe Shellworld manifest path" in result.stderr


def test_shellworld_isolation_rejects_symlink_source(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    data = root / "data"
    data.mkdir()
    (data / "real.txt").write_text("content", encoding="utf-8")
    try:
        (data / "link.txt").symlink_to(data / "real.txt")
    except (NotImplementedError, OSError):
        pytest.skip("symbolic links are unavailable on this platform")
    write_shellworld_manifest(root, "data/link.txt")
    destination = tmp_path / "isolated"
    destination.mkdir()
    with pytest.raises(ValueError, match="regular non-symlink"):
        validator._prepare_shellworld_validation_tree(root, destination)


def test_expected_blocker_is_explicit_and_does_not_spawn() -> None:
    spec = validator.CheckSpec(
        "future",
        "future check",
        ("nightly",),
        expected_blocker="not implemented in this milestone",
    )

    def must_not_run(*args):
        raise AssertionError("an expected blocker must not spawn")

    result = validator.execute_check(spec, command_runner=must_not_run)
    assert result.status == validator.ResultStatus.EXPECTED_BLOCKED
    assert result.details["reason"] == "not implemented in this milestone"


@cache
def stabilizerness_observed_paths() -> tuple[str, ...]:
    observed = set(validator.FORMAL_VERIFICATION_RECORDS)
    for relative in validator.FORMAL_VERIFICATION_RECORDS:
        evidence = json.loads((validator.REPO / relative).read_text(encoding="utf-8"))
        observed.update(evidence["artifact_hashes"])
    return tuple(sorted(observed))


def stabilizerness_blocked_payload() -> dict:
    declaration_audit = {
        **{
            name: {
                "scope": "target-local",
                "audit_status": "NOT_RUN",
                "axioms": [],
            }
            for name in validator.STABILIZERNESS_LOCAL_DECLARATIONS
        },
        **{
            name: {
                "scope": "imported",
                "audit_status": "NOT_RUN",
                "axioms": [],
            }
            for name in validator.STABILIZERNESS_IMPORTED_DECLARATIONS
        },
    }
    return {
        "schema": "agtxiv.stabilizerness-dynamic-validation-report/0.1.0",
        "historical_evidence_schema_version": "0.1.0-prototype",
        "project": "formal/AgtXIvStabilizerness",
        "evidence_id": validator.STABILIZERNESS_EVIDENCE_ID,
        "declared_historical_status": validator.STABILIZERNESS_HISTORICAL_STATUS,
        "assurance_tier": "LOCAL_PRELOADED_DIAGNOSTIC",
        "effective_validation_status": "EXPECTED_BLOCKED",
        "formalization_validation": "EXPECTED_BLOCKED",
        "dynamic_execution": "EXPECTED_BLOCKED",
        "dynamic_blocker_code": validator.STABILIZERNESS_BLOCKER_CODE,
        "dynamic_blocker_reason": validator.STABILIZERNESS_BLOCKER_REASON,
        "cache_mode": "DYNAMIC_NOT_RUN_FUTURE_PRELOADED_CACHE_UNVERIFIED",
        "consumed_cache_closure": "NOT_VERIFIED",
        "source_clean_rebuild": False,
        "network_mode": validator.NETWORK_MODE,
        "network_isolation_enforced": False,
        "filesystem_isolation_enforced": False,
        "network_note": validator.STABILIZERNESS_NETWORK_NOTE,
        "evidence_anchors": "PASSED",
        "artifact_hashes": "PASSED",
        "formal_input_inventory": "PASSED",
        "environment_binding": "PASSED",
        "placeholder_scan": "PASSED",
        "protected_input_integrity": "PASSED",
        "side_effect_observation_scope": {
            "method": validator.STABILIZERNESS_SIDE_EFFECT_METHOD,
            "observed_paths": list(stabilizerness_observed_paths()),
            "reused_unmeasured_cache_roots": list(
                validator.STABILIZERNESS_REUSED_UNMEASURED_CACHE_ROOTS
            ),
            "paths_outside_observed_formal_and_evidence_closure": (
                validator.STABILIZERNESS_OUTSIDE_OBSERVED_CLOSURE
            ),
            "future_dynamic_note": validator.STABILIZERNESS_FUTURE_DYNAMIC_NOTE,
            "filesystem_isolation_enforced": False,
        },
        "tool_identity": {
            "validation": "NOT_RUN",
            "static_path_validation": "PASSED",
            "dynamic_identity": "NOT_RUN",
            "paths": dict(validator.STABILIZERNESS_TOOL_PATHS),
            "resolved_git_executable": None,
        },
        "dependency_git_identity": {
            "validation": "NOT_RUN",
            "source_tree_closure": "NOT_RUN",
            "consumed_cache_closure": "NOT_VERIFIED",
        },
        "kernel_build": "NOT_RUN",
        "kernel_build_failure_excerpt": [],
        "axiom_audit": "NOT_RUN",
        "declarations_audited": 0,
        "target_local_declarations_audited": 0,
        "imported_declarations_audited": 0,
        "expected_target_local_declarations": sorted(
            validator.STABILIZERNESS_LOCAL_DECLARATIONS
        ),
        "expected_imported_declarations": sorted(
            validator.STABILIZERNESS_IMPORTED_DECLARATIONS
        ),
        "declaration_audit": declaration_audit,
        "reported_axioms": [],
        "external_commands": [],
        "admission_eligible": False,
        "security_gate_eligible": False,
        "m0_completion_effect": "NONE",
        "admission_note": validator.STABILIZERNESS_ADMISSION_NOTE,
        "remaining_m0_security_blockers": list(
            validator.STABILIZERNESS_REMAINING_M0_SECURITY_BLOCKERS
        ),
        "scientific_acceptance_effect": validator.STABILIZERNESS_SCIENTIFIC_EFFECT,
        "scope_limitations": list(validator.STABILIZERNESS_SCOPE_LIMITATIONS),
        "environment_policy": {
            "network_mode": validator.NETWORK_MODE,
            "credential_minimized": True,
        },
        "errors": [],
    }


def test_stabilizerness_classifier_constants_mirror_standalone_contract() -> None:
    assert validator.STABILIZERNESS_NETWORK_NOTE == standalone_validator.NETWORK_NOTE
    assert (
        validator.STABILIZERNESS_SIDE_EFFECT_KEYS
        == standalone_validator.SIDE_EFFECT_OBSERVATION_SCOPE_KEYS
    )
    assert (
        validator.STABILIZERNESS_SIDE_EFFECT_METHOD
        == standalone_validator.SIDE_EFFECT_OBSERVATION_METHOD
    )
    assert (
        validator.STABILIZERNESS_REUSED_UNMEASURED_CACHE_ROOTS
        == standalone_validator.SIDE_EFFECT_REUSED_UNMEASURED_CACHE_ROOTS
    )
    assert (
        validator.STABILIZERNESS_OUTSIDE_OBSERVED_CLOSURE
        == standalone_validator.SIDE_EFFECT_OUTSIDE_OBSERVED_CLOSURE
    )
    assert (
        validator.STABILIZERNESS_FUTURE_DYNAMIC_NOTE
        == standalone_validator.SIDE_EFFECT_FUTURE_DYNAMIC_NOTE
    )
    assert (
        validator.STABILIZERNESS_OBSERVED_PATHS_SHA256
        == standalone_validator.OBSERVED_PATHS_SHA256
    )
    assert (
        validator.STABILIZERNESS_ADMISSION_NOTE
        == standalone_validator.ADMISSION_NOTE
    )
    assert (
        validator.STABILIZERNESS_REMAINING_M0_SECURITY_BLOCKERS
        == standalone_validator.REMAINING_M0_SECURITY_BLOCKERS
    )
    assert list(validator.STABILIZERNESS_SCOPE_LIMITATIONS) == (
        standalone_validator.EXPECTED_SCOPE_LIMITATIONS
    )
    assert (
        validator.STABILIZERNESS_ENVIRONMENT_POLICY_KEYS
        == standalone_validator.ENVIRONMENT_POLICY_KEYS
    )
    assert validator.STABILIZERNESS_TOOL_PATHS == {
        "lake": str(standalone_validator.REPO / standalone_validator.LAKE_RELATIVE),
        "lean": str(standalone_validator.REPO / standalone_validator.LEAN_RELATIVE),
    }


def test_stabilizerness_exact_static_blocker_is_classified() -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "lean-stabilizerness-dynamic"
    )
    payload = stabilizerness_blocked_payload()
    assert set(payload) == validator.STABILIZERNESS_REPORT_TOP_LEVEL_KEYS
    result = validator._stabilizerness_blocked_result(
        spec,
        invocation(2, json.dumps(payload)),
        [sys.executable, "tools/validate_stabilizerness_formalization.py"],
    )
    assert result.status == validator.ResultStatus.EXPECTED_BLOCKED
    assert result.details["exact_reviewed_blocker_state"] is True

    payload["external_commands"] = [["lake", "build"]]
    rejected = validator._stabilizerness_blocked_result(
        spec,
        invocation(2, json.dumps(payload)),
        [sys.executable, "tools/validate_stabilizerness_formalization.py"],
    )
    assert rejected.status == validator.ResultStatus.FAIL


@pytest.mark.parametrize("non_integer_zero", [False, 0.0])
@pytest.mark.parametrize(
    "field",
    [
        "declarations_audited",
        "target_local_declarations_audited",
        "imported_declarations_audited",
    ],
)
def test_stabilizerness_blocker_requires_exact_integer_zero_counts(
    field: str, non_integer_zero: object
) -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "lean-stabilizerness-dynamic"
    )
    payload = stabilizerness_blocked_payload()
    payload[field] = non_integer_zero
    result = validator._stabilizerness_blocked_result(
        spec,
        invocation(2, json.dumps(payload)),
        [sys.executable, "tools/validate_stabilizerness_formalization.py"],
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.details["exact_reviewed_blocker_state"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_top_level",
        "missing_reason",
        "wrong_code",
        "wrong_evidence_id",
        "formalization_pass",
        "effective_pass",
        "dynamic_pass",
        "cache_mode",
        "clean_rebuild",
        "network_isolation",
        "filesystem_isolation",
        "network_note",
        "evidence_failed",
        "artifact_failed",
        "inventory_failed",
        "environment_failed",
        "placeholder_failed",
        "protected_failed",
        "missing_tool_identity",
        "unknown_tool_identity",
        "unknown_tool_path",
        "tool_identity_passed",
        "tool_static_failed",
        "tool_dynamic_passed",
        "tool_path_empty",
        "tool_path_wrong_lake",
        "tool_path_wrong_lean",
        "missing_dependency_identity",
        "unknown_dependency_identity",
        "dependency_passed",
        "cache_verified",
        "build_passed",
        "audit_passed",
        "count_nonzero",
        "missing_declaration_audit",
        "unknown_declaration_entry",
        "declaration_audited",
        "declaration_names",
        "expected_declarations",
        "side_effect_nonobject",
        "side_effect_missing_key",
        "side_effect_unknown_key",
        "side_effect_method",
        "side_effect_observed_paths",
        "side_effect_reused_cache",
        "side_effect_outside_scope",
        "side_effect_future_note",
        "side_effect_filesystem_isolation",
        "environment_nonobject",
        "environment_missing_key",
        "environment_unknown_key",
        "environment_network_mode",
        "environment_credentials",
        "external_command",
        "admission_true",
        "security_true",
        "m0_complete",
        "admission_note",
        "remaining_blockers",
        "scientific_effect",
        "scope_limitations",
        "reported_error",
        "stderr",
    ],
)
def test_stabilizerness_blocker_rejects_missing_or_contradictory_fields(
    mutation: str,
) -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "lean-stabilizerness-dynamic"
    )
    payload = copy.deepcopy(stabilizerness_blocked_payload())
    stderr = ""
    if mutation == "unknown_top_level":
        payload["admission_authorized"] = True
    elif mutation == "missing_reason":
        payload.pop("dynamic_blocker_reason")
    elif mutation == "wrong_code":
        payload["dynamic_blocker_code"] = "OTHER"
    elif mutation == "wrong_evidence_id":
        payload["evidence_id"] = "other"
    elif mutation == "formalization_pass":
        payload["formalization_validation"] = "PASSED"
    elif mutation == "effective_pass":
        payload["effective_validation_status"] = "PASSED"
    elif mutation == "dynamic_pass":
        payload["dynamic_execution"] = "PASSED"
    elif mutation == "cache_mode":
        payload["cache_mode"] = "CACHE_ASSISTED_REVALIDATION"
    elif mutation == "clean_rebuild":
        payload["source_clean_rebuild"] = True
    elif mutation == "network_isolation":
        payload["network_isolation_enforced"] = True
    elif mutation == "filesystem_isolation":
        payload["filesystem_isolation_enforced"] = True
    elif mutation == "network_note":
        payload["network_note"] = "operating-system no-egress was enforced"
    elif mutation == "evidence_failed":
        payload["evidence_anchors"] = "FAILED"
    elif mutation == "artifact_failed":
        payload["artifact_hashes"] = "FAILED"
    elif mutation == "inventory_failed":
        payload["formal_input_inventory"] = "FAILED"
    elif mutation == "environment_failed":
        payload["environment_binding"] = "FAILED"
    elif mutation == "placeholder_failed":
        payload["placeholder_scan"] = "FAILED"
    elif mutation == "protected_failed":
        payload["protected_input_integrity"] = "FAILED"
    elif mutation == "missing_tool_identity":
        payload.pop("tool_identity")
    elif mutation == "unknown_tool_identity":
        payload["tool_identity"]["admission_authorized"] = True
    elif mutation == "unknown_tool_path":
        payload["tool_identity"]["paths"]["git"] = "/fixed/git"
    elif mutation == "tool_identity_passed":
        payload["tool_identity"]["validation"] = "PASSED"
    elif mutation == "tool_static_failed":
        payload["tool_identity"]["static_path_validation"] = "FAILED"
    elif mutation == "tool_dynamic_passed":
        payload["tool_identity"]["dynamic_identity"] = "PASSED"
    elif mutation == "tool_path_empty":
        payload["tool_identity"]["paths"]["lean"] = ""
    elif mutation == "tool_path_wrong_lake":
        payload["tool_identity"]["paths"]["lake"] = "/bin/true"
    elif mutation == "tool_path_wrong_lean":
        payload["tool_identity"]["paths"]["lean"] = "/bin/false"
    elif mutation == "missing_dependency_identity":
        payload.pop("dependency_git_identity")
    elif mutation == "unknown_dependency_identity":
        payload["dependency_git_identity"]["admission_authorized"] = True
    elif mutation == "dependency_passed":
        payload["dependency_git_identity"]["validation"] = "PASSED"
    elif mutation == "cache_verified":
        payload["consumed_cache_closure"] = "VERIFIED"
    elif mutation == "build_passed":
        payload["kernel_build"] = "PASSED"
    elif mutation == "audit_passed":
        payload["axiom_audit"] = "PASSED"
    elif mutation == "count_nonzero":
        payload["declarations_audited"] = 1
    elif mutation == "missing_declaration_audit":
        payload.pop("declaration_audit")
    elif mutation == "unknown_declaration_entry":
        next(iter(payload["declaration_audit"].values()))[
            "admission_authorized"
        ] = True
    elif mutation == "declaration_audited":
        next(iter(payload["declaration_audit"].values()))["audit_status"] = "PASSED"
    elif mutation == "declaration_names":
        value = payload["declaration_audit"].pop(
            next(iter(payload["declaration_audit"]))
        )
        payload["declaration_audit"]["unexpected"] = value
    elif mutation == "expected_declarations":
        payload["expected_target_local_declarations"] = []
    elif mutation == "side_effect_nonobject":
        payload["side_effect_observation_scope"] = "ALL_FILES_PROTECTED"
    elif mutation == "side_effect_missing_key":
        payload["side_effect_observation_scope"].pop("future_dynamic_note")
    elif mutation == "side_effect_unknown_key":
        payload["side_effect_observation_scope"]["admission_authorized"] = True
    elif mutation == "side_effect_method":
        payload["side_effect_observation_scope"]["method"] = "full sandbox"
    elif mutation == "side_effect_observed_paths":
        payload["side_effect_observation_scope"]["observed_paths"].pop()
    elif mutation == "side_effect_reused_cache":
        payload["side_effect_observation_scope"][
            "reused_unmeasured_cache_roots"
        ] = []
    elif mutation == "side_effect_outside_scope":
        payload["side_effect_observation_scope"][
            "paths_outside_observed_formal_and_evidence_closure"
        ] = "MEASURED"
    elif mutation == "side_effect_future_note":
        payload["side_effect_observation_scope"]["future_dynamic_note"] = (
            "future dynamic cache is verified"
        )
    elif mutation == "side_effect_filesystem_isolation":
        payload["side_effect_observation_scope"][
            "filesystem_isolation_enforced"
        ] = True
    elif mutation == "environment_nonobject":
        payload["environment_policy"] = "FULLY_ISOLATED"
    elif mutation == "environment_missing_key":
        payload["environment_policy"].pop("credential_minimized")
    elif mutation == "environment_unknown_key":
        payload["environment_policy"]["admission_authorized"] = True
    elif mutation == "environment_network_mode":
        payload["environment_policy"]["network_mode"] = "ONLINE_ALLOWED"
    elif mutation == "environment_credentials":
        payload["environment_policy"]["credential_minimized"] = False
    elif mutation == "external_command":
        payload["external_commands"] = [["lake", "build"]]
    elif mutation == "admission_true":
        payload["admission_eligible"] = True
    elif mutation == "security_true":
        payload["security_gate_eligible"] = True
    elif mutation == "m0_complete":
        payload["m0_completion_effect"] = "COMPLETE"
    elif mutation == "admission_note":
        payload["admission_note"] = "approved for database admission and merge"
    elif mutation == "remaining_blockers":
        payload["remaining_m0_security_blockers"] = []
    elif mutation == "scientific_effect":
        payload["scientific_acceptance_effect"] = "PROMOTED"
    elif mutation == "scope_limitations":
        payload["scope_limitations"] = []
    elif mutation == "reported_error":
        payload["errors"] = ["error"]
    elif mutation == "stderr":
        stderr = "warning"
    result = validator._stabilizerness_blocked_result(
        spec,
        invocation(2, json.dumps(payload), stderr),
        [sys.executable, "tools/validate_stabilizerness_formalization.py"],
    )
    assert result.status == validator.ResultStatus.FAIL
    assert result.details["exact_reviewed_blocker_state"] is False


def test_stabilizerness_blocker_rejects_duplicate_json_keys() -> None:
    spec = next(
        item
        for item in validator.validation_catalog()
        if item.check_id == "lean-stabilizerness-dynamic"
    )
    encoded = json.dumps(stabilizerness_blocked_payload())
    encoded = encoded.replace(
        '"schema":', '"schema": "duplicate", "schema":', 1
    )
    result = validator._stabilizerness_blocked_result(
        spec,
        invocation(2, encoded),
        [sys.executable, "tools/validate_stabilizerness_formalization.py"],
    )
    assert result.status == validator.ResultStatus.FAIL


@pytest.mark.parametrize(
    ("case", "encoded"),
    [
        ("oversized_integer", '{"value":' + ("9" * 5000) + "}"),
        ("nan", '{"value":NaN}'),
        ("positive_infinity", '{"value":Infinity}'),
        ("negative_infinity", '{"value":-Infinity}'),
        ("invalid_utf8_surrogate", '{"value":"\udcff"}'),
    ],
)
def test_strict_json_output_rejects_hostile_scalars_without_raising(
    case: str, encoded: str
) -> None:
    del case
    parsed = validator._parse_json_output(invocation(2, encoded))
    assert parsed is None


def test_strict_json_output_rejects_deep_nesting_without_raising() -> None:
    depth = 2000
    encoded = '{"value":' + ("[" * depth) + "0" + ("]" * depth) + "}"
    assert validator._parse_json_output(invocation(2, encoded)) is None


def test_strict_json_output_enforces_ijson_integer_range() -> None:
    maximum = validator.IJSON_MAX_INTEGER
    assert validator._parse_json_output(
        invocation(stdout=json.dumps({"value": maximum}))
    ) == {"value": maximum}
    assert validator._parse_json_output(
        invocation(stdout=json.dumps({"value": -maximum}))
    ) == {"value": -maximum}
    assert validator._parse_json_output(
        invocation(stdout=json.dumps({"value": maximum + 1}))
    ) is None
    assert validator._parse_json_output(
        invocation(stdout=json.dumps({"value": -maximum - 1}))
    ) is None


def test_report_contains_all_stable_statuses() -> None:
    specs = [validator.CheckSpec("one", "one", ("fast",))]
    results = [
        validator.CheckResult(
            "one", "one", validator.ResultStatus.KNOWN_STALE
        )
    ]
    report = validator.build_report("fast", specs, results)
    assert report["outcome"] == "PASS"
    assert report["schema"] == "agtxiv.repository-validation-report/0.2.0"
    assert set(report["summary"]) == {status.value for status in validator.ResultStatus}
    assert report["summary"]["KNOWN_STALE"] == 1
    assert report["network_mode"] == validator.NETWORK_MODE
    assert report["network_isolation_enforced"] is False
    assert report["filesystem_isolation_enforced"] is False
    json.dumps(report)


def test_preloaded_environment_preserves_proxy_policy_without_claiming_isolation(
    monkeypatch,
) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid")
    monkeypatch.setenv("NO_PROXY", "localhost")
    monkeypatch.setenv("ELAN_TOOLCHAIN", "must-not-pass")
    monkeypatch.setenv("GIT_DIR", "must-not-pass")
    monkeypatch.setenv("LD_PRELOAD", "must-not-pass")
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-pass")
    environment = validator._preloaded_validation_environment()
    assert environment["HTTP_PROXY"] == "http://proxy.invalid"
    assert environment["NO_PROXY"] == "localhost"
    assert environment["AGTXIV_NETWORK_MODE"] == validator.NETWORK_MODE
    assert "AGTXIV_OFFLINE" not in environment
    assert "ELAN_TOOLCHAIN" not in environment
    assert "GIT_DIR" not in environment
    assert "LD_PRELOAD" not in environment
    assert "GITHUB_TOKEN" not in environment


@pytest.mark.skipif(os.name != "posix", reason="process-group signal is POSIX-only")
def test_subprocess_timeout_terminates_the_process_group(tmp_path: Path) -> None:
    result = validator._subprocess_runner(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        tmp_path,
        os.environ,
        1,
    )
    assert result.returncode == validator.TIMEOUT_EXIT_CODE
    assert "process group terminated" in result.stderr


def test_subprocess_output_is_hard_bounded(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(validator, "MAX_CAPTURE_BYTES", 4096)
    result = validator._subprocess_runner(
        [sys.executable, "-c", "import os; os.write(1, b'x' * 65536)"],
        tmp_path,
        os.environ,
        10,
    )
    assert result.returncode == validator.OUTPUT_LIMIT_EXIT_CODE
    assert len(result.stdout.encode("utf-8", errors="surrogateescape")) <= 4096
    assert "output exceeded" in result.stderr


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_subprocess_reports_and_kills_background_descendant(tmp_path: Path) -> None:
    result = validator._subprocess_runner(
        [
            sys.executable,
            "-c",
            (
                "import subprocess,sys; "
                "subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                "print('leader done')"
            ),
        ],
        tmp_path,
        os.environ,
        10,
    )
    assert result.returncode == validator.BACKGROUND_PROCESS_EXIT_CODE
    assert "descendants" in result.stderr


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_subprocess_detects_background_descendant_with_devnull_pipes(
    tmp_path: Path,
) -> None:
    result = validator._subprocess_runner(
        [
            sys.executable,
            "-c",
            (
                "import subprocess,sys; "
                "subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'], "
                "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, "
                "stderr=subprocess.DEVNULL); print('leader done')"
            ),
        ],
        tmp_path,
        os.environ,
        10,
    )
    assert result.returncode == validator.BACKGROUND_PROCESS_EXIT_CODE
    assert "original POSIX process group" in result.stderr


def test_main_list_and_json_report_use_injected_execution(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    assert validator.main(["--list"]) == 0
    assert "shellworld-v1-run" in capsys.readouterr().out

    def fake_run(checks, **kwargs):
        return [
            validator.CheckResult(
                checks[0].check_id,
                checks[0].description,
                validator.ResultStatus.PASS,
            )
        ]

    monkeypatch.setattr(validator, "run_checks", fake_run)
    report_path = tmp_path / "report.json"
    exit_code = validator.main(
        [
            "--only",
            "v2-paper-agentization",
            "--json-report",
            str(report_path),
        ]
    )
    assert exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["selected_checks"] == ["v2-paper-agentization"]
    assert report["results"][0]["status"] == "PASS"
