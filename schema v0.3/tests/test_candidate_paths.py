"""Path plumbing for the candidate freeze/compile/audit path (no Lean is run)."""
import hashlib
import json

import pytest

import candidate_audit
import candidate_compile
import candidate_sources


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_repo(tmp_path):
    repo = tmp_path / "worktree"
    lean = repo / "schema v0.3/lean"
    (lean / "frozen").mkdir(parents=True)
    (lean / "A.lean").write_text("import B\nimport AnticommutingWitness\nimport Mathlib\n")
    (lean / "B.lean").write_text("import Mathlib\n")
    witness = b"-- frozen witness\n"
    (lean / "frozen/AnticommutingWitness.lean").write_bytes(witness)
    return repo, _sha(witness)


def _fake_context(tmp_path, witness_sha, olean_sha="olean"):
    alpha = tmp_path / "alpha"
    alpha.mkdir()
    (alpha / "frozen-build-observation.json").write_text(json.dumps(
        {"source_sha256": witness_sha, "olean_sha256": olean_sha}))
    return {"frozen_alpha": str(alpha), "frozen_alpha_olean_sha256": "olean"}


def test_freeze_reads_sources_from_repo_and_context_from_context_repo(tmp_path, monkeypatch):
    repo, witness_sha = _source_repo(tmp_path)
    main = tmp_path / "main"
    seen = []
    context = _fake_context(tmp_path, witness_sha)
    monkeypatch.setattr(candidate_sources, "_context", lambda r: seen.append(r) or context)
    state = candidate_sources.freeze_candidate_sources(repo, tmp_path / "out", ["A"],
                                                       context_repo=main)
    assert seen == [main.resolve()]
    assert state["source_dependency_order"] == ["B", "A"]
    assert state["modules"]["A"]["original_path"].startswith(str(repo.resolve()))
    # The frozen witness is provided by the context's Alpha object, never recompiled.
    assert "AnticommutingWitness" not in state["modules"]
    assert state["context_provided_imports"]["AnticommutingWitness"]["source_sha256"] == witness_sha
    assert state["external_imports_unresolved"] == ["Mathlib"]
    assert not (tmp_path / "out/sources/AnticommutingWitness.lean").exists()


def test_freeze_default_context_repo_is_repo(tmp_path, monkeypatch):
    repo, witness_sha = _source_repo(tmp_path)
    seen = []
    context = _fake_context(tmp_path, witness_sha)
    monkeypatch.setattr(candidate_sources, "_context", lambda r: seen.append(r) or context)
    candidate_sources.freeze_candidate_sources(repo, tmp_path / "out", ["B"])
    assert seen == [repo.resolve()]


def test_freeze_rejects_witness_source_not_matching_alpha_object(tmp_path, monkeypatch):
    repo, _ = _source_repo(tmp_path)
    context = _fake_context(tmp_path, "different-source")
    monkeypatch.setattr(candidate_sources, "_context", lambda r: context)
    with pytest.raises(ValueError, match="frozen Alpha"):
        candidate_sources.freeze_candidate_sources(repo, tmp_path / "out", ["A"])
    assert not (tmp_path / "out").exists()


class _Stop(Exception):
    pass


def _bundle(tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "sources").mkdir(parents=True)
    source = b"import Mathlib\n"
    (bundle / "sources/B.lean").write_bytes(source)
    (bundle / "candidate-sources.json").write_text(json.dumps({
        "kind": "UncompiledCandidateSourceBundle", "roots": ["B"],
        "source_dependency_order": ["B"], "intended_context": {"marker": 1},
        "modules": {"B": {"snapshot": "sources/B.lean", "source_sha256": _sha(source),
                          "imports": ["Mathlib"]}}}))
    return bundle


@pytest.mark.parametrize("explicit", [False, True])
def test_compile_library_parameter(tmp_path, monkeypatch, explicit):
    bundle = _bundle(tmp_path)
    repo, library = tmp_path / "worktree", tmp_path / "physlib-elsewhere"
    seen = []

    def fake_check(context, lib):
        seen.append(lib)
        raise _Stop

    monkeypatch.setattr(candidate_compile, "_check_context", fake_check)
    with pytest.raises(_Stop):
        if explicit:
            candidate_compile.compile_next_candidate(repo, bundle, library=library)
        else:
            candidate_compile.compile_next_candidate(repo, bundle)
    assert seen == [library.resolve() if explicit else repo.resolve().parent / "physlib"]


@pytest.mark.parametrize("explicit", [False, True])
def test_audit_library_parameter(tmp_path, monkeypatch, explicit):
    bundle = _bundle(tmp_path)
    raw = (bundle / "candidate-sources.json").read_bytes()
    (bundle / "compile-progress.json").write_text(json.dumps({
        "kind": "CandidateCompilationProgress", "status": "COMPILED_AUDIT_PENDING",
        "bundle_sha256": _sha(raw), "compiled_modules": [{"module": "B", "artifacts": {}}],
        "receipts": []}))
    repo, library = tmp_path / "worktree", tmp_path / "physlib-elsewhere"
    seen = []

    def fake_check(context, lib):
        seen.append(lib)
        raise _Stop

    monkeypatch.setattr(candidate_audit, "_check_context", fake_check)
    with pytest.raises(_Stop):
        if explicit:
            candidate_audit.audit_candidates(repo, bundle, ["X.y"], library=library)
        else:
            candidate_audit.audit_candidates(repo, bundle, ["X.y"])
    assert seen == [library.resolve() if explicit else repo.resolve().parent / "physlib"]
    assert not (bundle / "declaration-audit").exists()
