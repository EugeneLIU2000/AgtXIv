"""Local intake boundaries with temporary inputs; no actual paper or demo runs."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agtxiv_v3.contracts import SchemaBundle  # noqa: E402
from agtxiv_v3.intake import IntakeLimits, build_source_candidates, inspect_source_directory  # noqa: E402
from agtxiv_v3.source import SourceError  # noqa: E402


def source_tree(tmp_path, files=None):
    root = tmp_path / "source"
    root.mkdir()
    for name, data in (files or {"main.tex": b"Local source"}).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


def run_cli(root, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools/inspect_v3_source.py"), str(root), "--main", "main.tex", *args],
        capture_output=True, timeout=10, check=False,
    )


def test_complete_inventory_preserves_original_bytes_and_distinguishes_non_tex(tmp_path):
    raw = "α\r\n\\input{sections/body}\n".encode()
    files = {"main.tex": raw, "sections/body.tex": br"\input{appendix}", "appendix.tex": b"Appendix", "unused.tex": b"Unused", "figure.png": b"\x89PNG\r\n\x1a\n", "data.csv": b"x,y\r\n1,2\r\n", "notes.custom": b"\xff\x00"}
    root = source_tree(tmp_path, files)
    inspection = inspect_source_directory(root, "main.tex")
    report = inspection.report()
    rows = {row["path"]: row for row in report["files"]}
    assert set(rows) == set(files) == set(inspection.sources)
    assert report["file_count"] == len(files)
    assert report["total_bytes"] == sum(map(len, files.values()))
    assert rows["main.tex"]["sha256"] == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert rows["main.tex"]["byte_size"] == len(raw)
    assert all(inspection.sources[name] == data for name, data in files.items())
    assert rows["sections/body.tex"]["static_include_activity"] == "ACTIVE"
    assert rows["appendix.tex"]["static_include_activity"] == "ACTIVE"
    assert rows["unused.tex"]["static_include_activity"] == "INACTIVE"
    assert rows["figure.png"]["static_include_activity"] is None
    assert rows["figure.png"]["analysis"] == "BYTES_ONLY_UNSUPPORTED_CONTENT"
    assert set(report["unsupported_content_paths"]) == {"figure.png", "data.csv", "notes.custom"}
    assert report["source_fidelity_assessment"] == report["scientific_assessment"] == "NOT_PERFORMED"
    assert all(row["published_rendering_activity"] == "UNASSESSED" for row in rows.values())
    assert set(report["unclassified_publication_participation_paths"]) == set(files)
    assert json.loads(inspection.json_bytes()) == report
    with pytest.raises(TypeError):
        inspection.sources["main.tex"] = b"replacement"
    assert (root / "main.tex").read_bytes() == raw


def test_missing_include_is_a_visible_parse_blocker_not_a_successful_source_assessment(tmp_path):
    root = source_tree(tmp_path, {"main.tex": br"\input{missing}"})
    report = inspect_source_directory(root, "main.tex").report()
    assert report["syntax_requires_review"] is True
    assert "MISSING_INCLUDE" in {issue["code"] for issue in report["issues"]}
    assert report["includes"][0]["target"] is None
    assert report["includes"][0]["activity"] == "UNKNOWN"


def test_conditions_comments_and_opaque_macros_preserve_uncertainty(tmp_path):
    root = source_tree(tmp_path, {"main.tex": b"% \\input{off}\n\\newcommand{\\load}{\\input{maybe}}", "off.tex": b"Off", "maybe.tex": b"Uncertain"})
    report = inspect_source_directory(root, "main.tex").report()
    assert report["syntax_requires_review"]
    assert all(edge["target"] != "off.tex" for edge in report["includes"])
    assert report["includes"][0]["activity"] == "UNKNOWN"


@pytest.mark.parametrize("is_directory", [False, True])
def test_symlink_entries_are_rejected_without_reading_targets(tmp_path, is_directory):
    root = source_tree(tmp_path)
    outside = tmp_path / "outside"
    if is_directory:
        outside.mkdir()
        (outside / "secret").write_bytes(b"must not read")
    else:
        outside.write_bytes(b"must not read")
    (root / "linked").symlink_to(outside, target_is_directory=is_directory)
    with pytest.raises(SourceError, match="Symbolic links"):
        inspect_source_directory(root, "main.tex")


def test_root_and_ancestor_symlinks_are_rejected(tmp_path):
    root = source_tree(tmp_path)
    link = tmp_path / "link"
    link.symlink_to(root, target_is_directory=True)
    with pytest.raises((SourceError, OSError)):
        inspect_source_directory(link, "main.tex")
    (root / "subdir").mkdir()
    (root / "subdir" / "main.tex").write_bytes(b"source")
    with pytest.raises((SourceError, OSError)):
        inspect_source_directory(link / "subdir", "main.tex")


def test_hard_links_and_special_files_are_rejected(tmp_path):
    root = source_tree(tmp_path)
    os.link(root / "main.tex", root / "alias.tex")
    with pytest.raises(SourceError, match="Hard-linked"):
        inspect_source_directory(root, "main.tex")
    (root / "alias.tex").unlink()
    os.mkfifo(root / "pipe")
    with pytest.raises(SourceError, match="Only regular"):
        inspect_source_directory(root, "main.tex")


@pytest.mark.parametrize("limits", [
    IntakeLimits(max_files=1), IntakeLimits(max_entries=1), IntakeLimits(max_file_bytes=2),
    IntakeLimits(max_total_bytes=7), IntakeLimits(max_depth=1), IntakeLimits(max_path_bytes=5),
])
def test_each_filesystem_budget_fails_closed(tmp_path, limits):
    root = source_tree(tmp_path, {"main.tex": b"source", "a/b/other.tex": b"source"})
    with pytest.raises(SourceError):
        inspect_source_directory(root, "main.tex", limits=limits)


def test_scan_does_not_follow_a_file_replaced_by_symlink_between_stat_and_open(tmp_path, monkeypatch):
    root = source_tree(tmp_path)
    secret = tmp_path / "secret"
    secret.write_bytes(b"outside data")
    original_open = os.open
    def raced_open(path, flags, *args, **kwargs):
        if path == "main.tex" and kwargs.get("dir_fd") is not None:
            (root / "main.tex").unlink()
            (root / "main.tex").symlink_to(secret)
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(os, "open", raced_open)
    with pytest.raises((SourceError, OSError)):
        inspect_source_directory(root, "main.tex")


@pytest.mark.parametrize("main", ["../main.tex", "/main.tex", "missing.tex", "a\\main.tex"])
def test_unsafe_or_missing_main_is_rejected(tmp_path, main):
    root = source_tree(tmp_path)
    with pytest.raises(SourceError):
        inspect_source_directory(root, main)


def test_explicit_working_directory_controls_nested_resolution(tmp_path):
    root = source_tree(tmp_path, {"paper/main.tex": br"\input{body}", "paper/body.tex": b"Correct", "body.tex": b"Other"})
    report = inspect_source_directory(root, "paper/main.tex", working_directory="paper").report()
    assert report["includes"][0]["target"] == "paper/body.tex"


def test_cli_emits_valid_json_to_stdout_and_keeps_diagnostics_separate(tmp_path):
    root = source_tree(tmp_path)
    result = run_cli(root)
    assert result.returncode == 0
    assert result.stderr == b""
    assert json.loads(result.stdout)["source_fidelity_assessment"] == "NOT_PERFORMED"
    failed = run_cli(root, "--max-files", "0")
    assert failed.returncode != 0
    assert failed.stdout == b""
    assert b"failed" in failed.stderr.lower()


def test_cli_writes_new_output_atomically_and_refuses_existing_or_symlink_output(tmp_path):
    root = source_tree(tmp_path)
    output = tmp_path / "inspection.json"
    result = run_cli(root, "--output", str(output))
    assert result.returncode == 0 and not result.stdout
    original = output.read_bytes()
    assert json.loads(original)["file_count"] == 1
    repeated = run_cli(root, "--output", str(output))
    assert repeated.returncode != 0
    assert output.read_bytes() == original
    link = tmp_path / "output-link.json"
    link.symlink_to(output)
    assert run_cli(root, "--output", str(link)).returncode != 0
    assert output.read_bytes() == original
    assert not list(tmp_path.glob(".agtxiv-inspection-*"))


def test_cli_invalid_source_never_creates_output(tmp_path):
    root = source_tree(tmp_path)
    (root / "bad").symlink_to(tmp_path / "absent")
    output = tmp_path / "inspection.json"
    assert run_cli(root, "--output", str(output)).returncode != 0
    assert not output.exists()


def test_cli_refuses_symlinked_output_parent(tmp_path):
    root = source_tree(tmp_path)
    output_directory = tmp_path / "outputs"
    output_directory.mkdir()
    link = tmp_path / "output-directory-link"
    link.symlink_to(output_directory, target_is_directory=True)
    result = run_cli(root, "--output", str(link / "report.json"))
    assert result.returncode != 0
    assert not (output_directory / "report.json").exists()


def test_output_publication_does_not_overwrite_a_concurrently_created_file(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("inspect_v3_source_cli", ROOT / "tools/inspect_v3_source.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_link = os.link
    output = tmp_path / "report.json"
    def raced_link(source, target, **kwargs):
        output.write_bytes(b"other writer's content")
        return original_link(source, target, **kwargs)
    monkeypatch.setattr(os, "link", raced_link)
    with pytest.raises(FileExistsError):
        module._write_new_file(output, b"complete report")
    assert output.read_bytes() == b"other writer's content"
    assert not list(tmp_path.glob(".agtxiv-inspection-*"))


def caller_metadata(bundle):
    return {
        "bundle": bundle,
        "producer": {"principal_id": "synthetic:declared-caller", "role": "SOURCE_PRODUCER", "actor_kind": "HUMAN", "identity_assurance": "DECLARED", "execution_id": "synthetic:inspection-test", "visible_input_refs": [], "identity_evidence": []},
        "policy_ref": {"record_type": "agtxiv.v3.authority-policy/0.0.0", "record_id": "synthetic:caller-policy", "revision": 1, "content_hash": "sha256:" + "0" * 64},
        "source_record_id": "synthetic:local-source", "structure_record_id": "synthetic:local-structure",
        "paper_id": "synthetic:paper", "paper_version": "fixture-v1", "created_at": "2026-09-07T00:00:00Z",
        "rights_status": "UNRESOLVED", "rights_note": "Caller declares this temporary test fixture; no publication rights inferred.",
    }


def test_candidate_records_bind_retained_bytes_without_inventing_identity_or_approval(tmp_path):
    root = source_tree(tmp_path, {"main.tex": br"\input{body}\input{missing}", "body.tex": b"Body", "data.csv": b"1,2"})
    inspection = inspect_source_directory(root, "main.tex")
    bundle = SchemaBundle()
    metadata = caller_metadata(bundle)
    candidates = build_source_candidates(inspection, **metadata)
    for record in [candidates.source_snapshot, candidates.paper_structure]:
        assert bundle.validate_record(record) == ()
        assert record["producer"] == metadata["producer"]
        assert record["policy_ref"] == metadata["policy_ref"]
        assert record["data_class"] == "OBSERVED"  # Actual temporary filesystem observation.
    source = candidates.source_snapshot["payload"]
    structure = candidates.paper_structure["payload"]
    assert source["acquisition_method"] == "LOCAL_IMPORT"
    assert source["source_uri"] == root.as_uri()
    assert all(unit["activity"] == "UNKNOWN" for unit in source["units"])
    assert set(structure["unclassified_unit_ids"]) == {unit["unit_id"] for unit in source["units"]}
    assert any("MISSING_INCLUDE" in blocker for blocker in structure["blockers"])
    artifacts = {artifact.artifact_id: artifact for artifact in candidates.artifacts}
    for unit in source["units"]:
        artifact = artifacts[unit["artifact"]["artifact_id"]]
        assert artifact.data == inspection.sources[unit["relative_path"]]
        assert artifact.reference(unit["relative_path"]) == unit["artifact"]
    assert not any(record["record_type"].endswith("assessment/0.0.0") for record in [candidates.source_snapshot, candidates.paper_structure])


def test_candidate_builder_requires_policy_and_exact_version(tmp_path):
    inspection = inspect_source_directory(source_tree(tmp_path), "main.tex")
    metadata = caller_metadata(SchemaBundle())
    for update in [{"policy_ref": None}, {"paper_version": "latest"}]:
        with pytest.raises(SourceError):
            build_source_candidates(inspection, **(metadata | update))


def test_inspection_keeps_retained_bytes_if_disk_changes_afterward(tmp_path):
    root = source_tree(tmp_path, {"main.tex": b"Original"})
    inspection = inspect_source_directory(root, "main.tex")
    (root / "main.tex").write_bytes(b"Later change")
    assert inspection.sources["main.tex"] == b"Original"
    assert inspection.report()["files"][0]["sha256"] == "sha256:" + hashlib.sha256(b"Original").hexdigest()
