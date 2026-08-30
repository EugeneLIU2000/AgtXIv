from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tools import validate_repo as validator


def invocation(returncode: int = 0, stdout: str = "", stderr: str = "") -> validator.Invocation:
    return validator.Invocation(returncode, stdout, stderr, 0.01)


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
    assert by_id["test-suite"].profiles == ("fast", "full", "nightly")
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
        assert environment["AGTXIV_OFFLINE"] == "1"
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


def test_report_contains_all_stable_statuses() -> None:
    specs = [validator.CheckSpec("one", "one", ("fast",))]
    results = [
        validator.CheckResult(
            "one", "one", validator.ResultStatus.KNOWN_STALE
        )
    ]
    report = validator.build_report("fast", specs, results)
    assert report["outcome"] == "PASS"
    assert set(report["summary"]) == {status.value for status in validator.ResultStatus}
    assert report["summary"]["KNOWN_STALE"] == 1
    json.dumps(report)


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
