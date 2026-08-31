from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from tools import validate_stabilizerness_formalization as validator


def make_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "repository"
    for project_name in (
        "AgtXIvRootMath",
        "AgtXIvVarela",
        "AgtXIvStabilizerness",
    ):
        source = validator.REPO / "formal" / project_name
        destination = repo / "formal" / project_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns(".lake", "__pycache__"),
        )
    tool_artifact = repo / "tools/validate_varela_formalization.py"
    tool_artifact.parent.mkdir(parents=True)
    shutil.copy2(
        validator.REPO / "tools/validate_varela_formalization.py", tool_artifact
    )
    for relative in (validator.LAKE_RELATIVE, validator.LEAN_RELATIVE):
        executable = repo / relative
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
    return repo


def must_not_spawn(*args):
    raise AssertionError("static Stabilizerness validation must not spawn")


def update_evidence_artifact(repo: Path, evidence_relative: str, artifact: str) -> None:
    evidence_path = repo / evidence_relative
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["artifact_hashes"][artifact] = f"sha256:{validator.sha256(repo / artifact)}"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def test_static_fixture_is_explicitly_blocked_without_spawning(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    report, build_output, audit_output = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "EXPECTED_BLOCKED", report["errors"]
    assert report["formalization_validation"] == "EXPECTED_BLOCKED"
    assert report["dynamic_execution"] == "EXPECTED_BLOCKED"
    assert report["dynamic_blocker_code"] == validator.BLOCKER_CODE
    assert report["dynamic_blocker_reason"] == validator.BLOCKER_REASON
    assert report["kernel_build"] == "NOT_RUN"
    assert report["axiom_audit"] == "NOT_RUN"
    assert report["consumed_cache_closure"] == "NOT_VERIFIED"
    assert report["cache_mode"] == "DYNAMIC_NOT_RUN_FUTURE_PRELOADED_CACHE_UNVERIFIED"
    assert report["admission_eligible"] is False
    assert report["security_gate_eligible"] is False
    assert report["m0_completion_effect"] == "NONE"
    assert report["external_commands"] == []
    assert report["evidence_anchors"] == "PASSED"
    assert report["artifact_hashes"] == "PASSED"
    assert report["formal_input_inventory"] == "PASSED"
    assert report["placeholder_scan"] == "PASSED"
    assert report["declared_historical_status"] == validator.EXPECTED_STATUS
    assert report["schema"] == validator.REPORT_SCHEMA
    assert set(report) == validator.REPORT_TOP_LEVEL_KEYS
    assert set(report["tool_identity"]) == validator.REPORT_TOOL_IDENTITY_KEYS
    assert set(report["tool_identity"]["paths"]) == validator.REPORT_TOOL_PATH_KEYS
    assert report["network_note"] == validator.NETWORK_NOTE
    side_effect_scope = report["side_effect_observation_scope"]
    assert set(side_effect_scope) == validator.SIDE_EFFECT_OBSERVATION_SCOPE_KEYS
    assert side_effect_scope["method"] == validator.SIDE_EFFECT_OBSERVATION_METHOD
    observed_paths = side_effect_scope["observed_paths"]
    assert observed_paths == sorted(set(observed_paths))
    assert hashlib.sha256(
        json.dumps(
            observed_paths, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest() == validator.OBSERVED_PATHS_SHA256
    assert side_effect_scope["reused_unmeasured_cache_roots"] == list(
        validator.SIDE_EFFECT_REUSED_UNMEASURED_CACHE_ROOTS
    )
    assert (
        side_effect_scope["paths_outside_observed_formal_and_evidence_closure"]
        == validator.SIDE_EFFECT_OUTSIDE_OBSERVED_CLOSURE
    )
    assert (
        side_effect_scope["future_dynamic_note"]
        == validator.SIDE_EFFECT_FUTURE_DYNAMIC_NOTE
    )
    assert side_effect_scope["filesystem_isolation_enforced"] is False
    assert report["admission_note"] == validator.ADMISSION_NOTE
    assert report["remaining_m0_security_blockers"] == list(
        validator.REMAINING_M0_SECURITY_BLOCKERS
    )
    assert report["scope_limitations"] == validator.EXPECTED_SCOPE_LIMITATIONS
    assert set(report["environment_policy"]) == validator.ENVIRONMENT_POLICY_KEYS
    assert report["environment_policy"] == {
        "network_mode": validator.NETWORK_MODE,
        "credential_minimized": True,
    }
    assert (
        set(report["dependency_git_identity"])
        == validator.REPORT_DEPENDENCY_IDENTITY_KEYS
    )
    assert all(
        set(entry) == validator.REPORT_DECLARATION_ENTRY_KEYS
        for entry in report["declaration_audit"].values()
    )
    assert build_output == audit_output == ""


def test_guarded_read_allows_unrelated_directory_child_churn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "trusted"
    root.mkdir()
    protected = root / "evidence.json"
    protected.write_bytes(b"{}\n")
    original_read = validator.os.read
    changed = False

    def changing_read(descriptor: int, size: int) -> bytes:
        nonlocal changed
        if not changed:
            changed = True
            (root / "unrelated").mkdir()
        return original_read(descriptor, size)

    monkeypatch.setattr(validator.os, "read", changing_read)
    errors: list[str] = []
    assert validator._read_regular_bytes(
        root,
        protected,
        label="fixture",
        max_bytes=16,
        errors=errors,
    ) == b"{}\n"
    assert errors == []


def test_environment_strips_credentials_and_identity_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid")
    monkeypatch.setenv("HTTP_PROXY", "http://user:secret@proxy.invalid")
    monkeypatch.setenv("NO_PROXY", "localhost")
    unsafe = (
        "ELAN_TOOLCHAIN",
        "LEAN_PATH",
        "LAKE_HOME",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_AUTHOR_NAME",
        "LD_PRELOAD",
        "DYLD_INSERT_LIBRARIES",
        "AWS_SECRET_ACCESS_KEY",
        "GITHUB_TOKEN",
    )
    for key in unsafe:
        monkeypatch.setenv(key, "must-not-pass")
    environment = validator.preloaded_validation_environment(tmp_path)
    assert environment["HTTPS_PROXY"] == "http://proxy.invalid"
    assert environment["HTTP_PROXY"] == "http://127.0.0.1:9"
    assert environment["NO_PROXY"] == "localhost"
    assert environment["AGTXIV_NETWORK_MODE"] == validator.NETWORK_MODE
    assert all(key not in environment for key in unsafe)


def test_git_resolution_ignores_ambient_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_git = tmp_path / "git"
    fake_git.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    errors: list[str] = []
    resolved = validator.resolve_git_executable(errors)
    assert errors == []
    assert resolved is not None
    assert resolved != fake_git


def test_modified_expected_lean_fails_before_any_command(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    source = repo / "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/LocalDelta.lean"
    source.write_text(
        source.read_text(encoding="utf-8") + "\naxiom injected : Prop\n",
        encoding="utf-8",
    )
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert report["artifact_hashes"] == "FAILED"
    assert report["placeholder_scan"] == "FAILED"
    assert report["kernel_build"] == "NOT_RUN"
    assert report["external_commands"] == []


def test_observed_path_contract_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = make_fixture(tmp_path)
    monkeypatch.setattr(validator, "OBSERVED_PATHS_SHA256", "0" * 64)
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert any(
        "observed-path coverage does not match" in error
        for error in report["errors"]
    )
    assert report["external_commands"] == []


def test_unexpected_unhashed_formal_file_is_not_placeholder_scanned(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    extra = repo / "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/Unproved.lean"
    extra.write_text("constant unprovedFact : False\n", encoding="utf-8")
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert report["formal_input_inventory"] == "FAILED"
    assert report["placeholder_scan"] == "PASSED"
    assert any("unexpected files" in error for error in report["errors"])


def test_nested_dot_lake_is_not_excluded(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    nested = repo / "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/.lake"
    nested.mkdir()
    (nested / "Injected.lean").write_text("def injected := true\n", encoding="utf-8")
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["formal_input_inventory"] == "FAILED"
    assert any("Injected.lean" in error for error in report["errors"])


def test_only_project_root_dot_lake_real_directory_is_excluded(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    cache = repo / "formal/AgtXIvStabilizerness/.lake"
    cache.mkdir()
    (cache / "Unanchored.olean").write_bytes(b"cache")
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "EXPECTED_BLOCKED"
    assert report["consumed_cache_closure"] == "NOT_VERIFIED"


def test_formal_source_symlink_is_rejected(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    external = tmp_path / "external.lean"
    external.write_text("def external : True := True.intro\n", encoding="utf-8")
    link = repo / "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/External.lean"
    try:
        link.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert any("must not be a symlink" in error for error in report["errors"])


def test_root_dot_lake_symlink_is_rejected(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    external = tmp_path / "cache"
    external.mkdir()
    link = repo / "formal/AgtXIvStabilizerness/.lake"
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert any("approved root .lake cache" in error for error in report["errors"])


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_fifo_evidence_is_rejected_without_blocking_or_parsing(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    evidence_path = repo / validator.RESULT_RELATIVE
    evidence_path.unlink()
    os.mkfifo(evidence_path)
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert any("not a regular file" in error for error in report["errors"])
    assert any("was not parsed" in error for error in report["errors"])
    assert report["external_commands"] == []


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_fifo_formal_input_is_rejected_without_opening(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    fifo = repo / "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/Injected.lean"
    os.mkfifo(fifo)
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert any("forbidden special file" in error for error in report["errors"])


def test_missing_and_symlinked_direct_tools_fail_statically(tmp_path: Path) -> None:
    missing_repo = make_fixture(tmp_path / "missing")
    (missing_repo / validator.LAKE_RELATIVE).unlink()
    missing, _, _ = validator.validate(missing_repo, must_not_spawn)
    assert missing["effective_validation_status"] == "FAILED"
    assert missing["tool_identity"]["validation"] == "NOT_RUN"
    assert missing["tool_identity"]["static_path_validation"] == "FAILED"

    linked_repo = make_fixture(tmp_path / "linked")
    lake = linked_repo / validator.LAKE_RELATIVE
    external = tmp_path / "fake-lake"
    external.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    external.chmod(0o755)
    lake.unlink()
    try:
        lake.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")
    linked, _, _ = validator.validate(linked_repo, must_not_spawn)
    assert linked["effective_validation_status"] == "FAILED"
    assert linked["tool_identity"]["validation"] == "NOT_RUN"
    assert linked["tool_identity"]["static_path_validation"] == "FAILED"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_fifo_direct_lean_is_rejected_without_opening(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    lean = repo / validator.LEAN_RELATIVE
    lean.unlink()
    os.mkfifo(lean)
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert report["tool_identity"]["validation"] == "NOT_RUN"
    assert report["tool_identity"]["static_path_validation"] == "FAILED"


def test_source_and_evidence_cannot_be_retagged_together(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    relative = "formal/AgtXIvStabilizerness/AgtXIvStabilizerness/LocalDelta.lean"
    source = repo / relative
    source.write_text(source.read_text(encoding="utf-8") + "\n-- retagged\n", encoding="utf-8")
    update_evidence_artifact(repo, validator.RESULT_RELATIVE.as_posix(), relative)
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert report["evidence_anchors"] == "FAILED"
    assert any("was not parsed" in error for error in report["errors"])


def test_bad_anchor_prevents_untrusted_json_path_derivation(tmp_path: Path) -> None:
    repo = make_fixture(tmp_path)
    evidence_path = repo / validator.RESULT_RELATIVE
    evidence_path.write_text(
        '{"artifact_hashes":{"formal/AgtXIvStabilizerness/../../outside":1}}',
        encoding="utf-8",
    )
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert any("inventory was not derived" in error for error in report["errors"])
    assert not any("unsafe" in error and "outside" in error for error in report["errors"])


def test_strict_json_parser_rejects_duplicate_keys() -> None:
    errors: list[str] = []
    value = validator._parse_json_bytes(b'{"a": 1, "a": 2}', "fixture", errors)
    assert value == {}
    assert any("duplicate JSON object key" in error for error in errors)


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "unexpected"])
def test_declaration_semantics_reject_non_exact_arrays(mutation: str) -> None:
    evidence = json.loads((validator.REPO / validator.RESULT_RELATIVE).read_text(encoding="utf-8"))
    declarations = evidence["target_local_declarations"]
    if mutation == "duplicate":
        declarations.append(declarations[0])
    elif mutation == "missing":
        declarations.pop()
    else:
        declarations[-1] = "AgtXIv.Stabilizerness.unexpected"
    errors: list[str] = []
    validator.validate_evidence_semantics(evidence, errors)
    assert any("target_local_declarations" in error for error in errors)


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "unexpected"])
def test_mapping_semantics_reject_non_exact_arrays(mutation: str) -> None:
    evidence = json.loads((validator.REPO / validator.RESULT_RELATIVE).read_text(encoding="utf-8"))
    declarations = evidence["registry_claim_effects"][1]["declarations"]
    if mutation == "duplicate":
        declarations.append(declarations[0])
    elif mutation == "missing":
        declarations.pop()
    else:
        declarations[-1] = "AgtXIv.GraphFoundation.unexpected"
    errors: list[str] = []
    validator.validate_evidence_semantics(evidence, errors)
    assert any("registry effect" in error for error in errors)


def test_axiom_parser_rejects_duplicate_axiom_in_one_entry() -> None:
    declaration = sorted(validator.ALL_DECLARATIONS)[0]
    errors: list[str] = []
    validator.parse_axiom_audit(
        f"'{declaration}' depends on axioms: [propext, propext]\n", errors
    )
    assert any("repeated axioms" in error for error in errors)


def test_final_snapshot_detects_change_after_initial_snapshot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = make_fixture(tmp_path)
    source = repo / "formal/AgtXIvVarela/AgtXIvVarela/MeasurementProjection.lean"
    original = validator._formal_snapshot_guarded
    calls = 0

    def mutating_snapshot(repository, expected, errors, phase):
        nonlocal calls
        result = original(repository, expected, errors, phase)
        calls += 1
        if calls == 1:
            source.write_text(
                source.read_text(encoding="utf-8") + "\n-- changed after snapshot\n",
                encoding="utf-8",
            )
        return result

    monkeypatch.setattr(validator, "_formal_snapshot_guarded", mutating_snapshot)
    report, _, _ = validator.validate(repo, must_not_spawn)
    assert report["effective_validation_status"] == "FAILED"
    assert report["protected_input_integrity"] == "FAILED"
    assert report["external_commands"] == []


def test_guarded_reader_detects_same_size_change_during_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"AAAA")
    original_read = validator.os.read
    changed = False

    def changing_read(descriptor: int, size: int) -> bytes:
        nonlocal changed
        if not changed:
            changed = True
            path.write_bytes(b"BBBB")
        return original_read(descriptor, size)

    monkeypatch.setattr(validator.os, "read", changing_read)
    errors: list[str] = []
    payload = validator._read_regular_bytes(
        tmp_path, path, label="changing fixture", max_bytes=16, errors=errors
    )
    assert payload is None
    assert any("changed while being read" in error for error in errors)


def test_guarded_reader_detects_growth_beyond_cap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"AAAA")
    original_read = validator.os.read
    changed = False

    def growing_read(descriptor: int, size: int) -> bytes:
        nonlocal changed
        if not changed:
            changed = True
            with path.open("ab") as stream:
                stream.write(b"BBBBBBBB")
        return original_read(descriptor, size)

    monkeypatch.setattr(validator.os, "read", growing_read)
    errors: list[str] = []
    payload = validator._read_regular_bytes(
        tmp_path, path, label="growing fixture", max_bytes=4, errors=errors
    )
    assert payload is None
    assert any("safety limit" in error for error in errors)


def test_run_command_has_hard_total_output_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(validator, "MAX_CAPTURE_BYTES", 4096)
    command = [sys.executable, "-c", "import os; os.write(1, b'x' * 65536)"]
    result = validator.run_command(command, tmp_path, os.environ, 10)
    assert result.returncode == validator.OUTPUT_LIMIT_EXIT_CODE
    assert len(result.stdout.encode("utf-8", errors="surrogateescape")) <= 4096
    assert "output exceeded" in result.stderr


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_run_command_reports_and_kills_background_descendant(tmp_path: Path) -> None:
    command = [
        sys.executable,
        "-c",
        (
            "import subprocess,sys; "
            "subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
            "print('leader done')"
        ),
    ]
    result = validator.run_command(command, tmp_path, os.environ, 10)
    assert result.returncode == validator.BACKGROUND_PROCESS_EXIT_CODE
    assert "descendants" in result.stderr


@pytest.mark.skipif(os.name != "posix", reason="process groups require POSIX")
def test_run_command_detects_background_descendant_with_devnull_pipes(
    tmp_path: Path,
) -> None:
    command = [
        sys.executable,
        "-c",
        (
            "import subprocess,sys; "
            "subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'], "
            "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, "
            "stderr=subprocess.DEVNULL); print('leader done')"
        ),
    ]
    result = validator.run_command(command, tmp_path, os.environ, 10)
    assert result.returncode == validator.BACKGROUND_PROCESS_EXIT_CODE
    assert "original POSIX process group" in result.stderr
