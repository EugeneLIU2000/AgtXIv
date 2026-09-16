"""Adversarial local-source checks; no network, demos, TeX, or Lean execution."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from agtxiv_v3.source import (  # noqa: E402
    ArchiveLimits, SourceError, analyze_tex_structure, extract_tar_atomic,
    fingerprint, verify_byte_span,
)


def bundle(entries: list[tuple[str, bytes, bytes]], *, mtime: int = 0) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as tar:
        for name, data, kind in entries:
            member = tarfile.TarInfo(name)
            member.type = kind
            member.mtime = mtime
            member.size = len(data) if kind == tarfile.REGTYPE else 0
            if kind in {tarfile.SYMTYPE, tarfile.LNKTYPE}:
                member.linkname = "../outside"
            tar.addfile(member, io.BytesIO(data) if kind == tarfile.REGTYPE else None)
    return output.getvalue()


def regular(name: str, data: bytes = b"source") -> tuple[str, bytes, bytes]:
    return name, data, tarfile.REGTYPE


def assert_atomic_rejection(tmp_path: Path, payload: bytes, **kwargs) -> None:
    target = tmp_path / "extracted"
    before = set(tmp_path.iterdir())
    with pytest.raises((SourceError, OSError)):
        extract_tar_atomic(payload, target, **kwargs)
    assert not target.exists()
    assert set(tmp_path.iterdir()) == before


def test_archive_hash_and_tree_hash_preserve_original_bytes_and_ignore_container(tmp_path):
    entries = [regular("z/main.tex", "é\r\n".encode()), regular("α.tex", b"other")]
    first = bundle(entries)
    second = gzip.compress(bundle(list(reversed(entries)), mtime=42))
    tree1 = extract_tar_atomic(first, tmp_path / "first")
    archive_path = tmp_path / "download.tar.gz"
    archive_path.write_bytes(second)
    tree2 = extract_tar_atomic(archive_path, tmp_path / "second")
    assert tree1.source_tree_sha256 == tree2.source_tree_sha256
    assert tree1.archive_sha256 != tree2.archive_sha256
    assert tree1.archive_sha256 == hashlib.sha256(first).hexdigest()
    assert (tree1.destination / "z/main.tex").read_bytes() == entries[0][1]
    assert tree1.files[0].size_bytes == len(entries[0][1])
    records = [{"path": entry.path, "type": "file", "sha256": entry.sha256} for entry in tree1.files]
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert tree1.source_tree_sha256 == hashlib.sha256(canonical).hexdigest()


@pytest.mark.parametrize("name", ["../escape", "/escape", "a/../../escape", "C:/escape", r"a\escape", "a/../b"])
def test_path_attacks_leave_no_partial_output(tmp_path, name):
    assert_atomic_rejection(tmp_path, bundle([regular("valid.tex"), regular(name)]))


@pytest.mark.parametrize("kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.FIFOTYPE])
def test_links_and_special_members_are_rejected(tmp_path, kind):
    assert_atomic_rejection(tmp_path, bundle([regular("valid.tex"), ("attack", b"", kind)]))


@pytest.mark.parametrize("names", [("a.tex", "./a.tex"), ("a/b.tex", "a//b.tex"), ("a", "a/b")])
def test_duplicate_or_incompatible_normalized_paths_rejected(tmp_path, names):
    assert_atomic_rejection(tmp_path, bundle([regular(name) for name in names]))


@pytest.mark.parametrize("limits,entries", [
    (ArchiveLimits(max_files=1), [regular("a"), regular("b")]),
    (ArchiveLimits(max_entries=1), [("dir", b"", tarfile.DIRTYPE), regular("a")]),
    (ArchiveLimits(max_file_bytes=1), [regular("a")]),
    (ArchiveLimits(max_total_bytes=7), [regular("a"), regular("b")]),
    (ArchiveLimits(max_archive_bytes=10), [regular("a")]),
    (ArchiveLimits(max_path_bytes=2), [regular("long.tex")]),
])
def test_each_resource_budget_is_enforced_atomically(tmp_path, limits, entries):
    assert_atomic_rejection(tmp_path, bundle(entries), limits=limits)


def test_compressed_header_bomb_is_bounded_before_tar_parsing(tmp_path):
    compressed = gzip.compress(b" " * 500_000)
    assert_atomic_rejection(tmp_path, compressed, limits=ArchiveLimits(max_expanded_archive_bytes=1000))


@pytest.mark.parametrize("payload", [b"not tar", b"", bundle([regular("empty", b"")]), gzip.compress(b"broken", mtime=0)[:-5]])
def test_invalid_or_empty_archives_leave_no_partial_output(tmp_path, payload):
    assert_atomic_rejection(tmp_path, payload)


def test_existing_destination_and_symlink_are_never_replaced(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    original = target / "keep.txt"
    original.write_bytes(b"keep")
    with pytest.raises(SourceError):
        extract_tar_atomic(bundle([regular("new")]), target)
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(SourceError):
        extract_tar_atomic(bundle([regular("new")]), link)
    assert original.read_bytes() == b"keep"
    assert list(target.iterdir()) == [original]


def test_concurrent_destination_creation_cannot_be_overwritten(tmp_path, monkeypatch):
    import agtxiv_v3.source as source
    real_rename = source._rename_without_replacement
    def racing_rename(staged, target):
        target.mkdir()
        real_rename(staged, target)
    monkeypatch.setattr(source, "_rename_without_replacement", racing_rename)
    with pytest.raises(OSError):
        extract_tar_atomic(bundle([regular("source")]), tmp_path / "result")
    assert list((tmp_path / "result").iterdir()) == []
    assert not list(tmp_path.glob(".agtxiv-source-*"))


def test_span_coordinates_are_original_bytes_not_unicode_characters():
    data = "α\r\nClaim: β".encode()
    span = "β".encode()
    start = data.index(span)
    expected = hashlib.sha256(span).hexdigest()
    assert verify_byte_span(data, start, start + len(span), expected_sha256=expected, expected_bytes=span) == span
    assert fingerprint("main.tex", data).size_bytes == len(data)
    for begin, end in [(start - 1, start + 1), (start, len(data) + 1), (0, 0), (-1, 2), (True, 2)]:
        with pytest.raises(SourceError):
            verify_byte_span(data, begin, end, expected_sha256=expected)
    with pytest.raises(SourceError):
        verify_byte_span(data, start, len(data), expected_sha256=expected, expected_bytes=b"different")


def test_static_include_graph_uses_main_and_ignores_comments_and_unused_files():
    sources = {
        "main.tex": b"% \\input{comment}\n\\input{body}\n\\include{appendix}\n",
        "body.tex": b"Body \\input{figures/caption}",
        "appendix.tex": b"Appendix",
        "figures/caption.tex": b"Caption",
        "comment.tex": b"Never published",
        "unused.tex": b"Unused",
    }
    result = analyze_tex_structure("main.tex", sources)
    assert not result.requires_review
    assert result.file_activity == {"main.tex": "ACTIVE", "body.tex": "ACTIVE", "appendix.tex": "ACTIVE", "figures/caption.tex": "ACTIVE", "comment.tex": "INACTIVE", "unused.tex": "INACTIVE"}
    for edge in result.includes:
        exact = sources[edge.source][edge.start_byte:edge.end_byte]
        assert exact.startswith((b"\\input", b"\\include"))
        assert b"comment" not in exact


def test_includes_resolve_against_explicit_tex_working_directory():
    result = analyze_tex_structure("paper/main.tex", {
        "paper/main.tex": b"\\input{chapters/body}",
        "paper/chapters/body.tex": b"\\input{appendix}",
        "paper/appendix.tex": b"Root relative",
        "paper/chapters/appendix.tex": b"Not implicitly file relative",
    }, working_directory="paper")
    assert result.file_activity["paper/appendix.tex"] == "ACTIVE"
    assert result.file_activity["paper/chapters/appendix.tex"] == "INACTIVE"


def test_literal_nested_conditionals_and_endinput_are_not_claimed_active():
    result = analyze_tex_structure("main.tex", {
        "main.tex": b"\\iffalse\\input{off}\\iftrue\\input{nested}\\fi\\else\\input{on}\\fi\\endinput\n\\input{after}",
        "off.tex": b"Off", "nested.tex": b"Off", "on.tex": b"On", "after.tex": b"Off",
    })
    assert not result.requires_review
    assert result.file_activity["on.tex"] == "ACTIVE"
    assert all(result.file_activity[name] == "INACTIVE" for name in ("off.tex", "nested.tex", "after.tex"))


def test_escaped_percent_and_verbatim_do_not_create_false_includes():
    result = analyze_tex_structure("main.tex", {
        "main.tex": br"\% literal \input{yes}" + b"\n" + br"\verb|\input{no}| \begin{verbatim}\include{no}\end{verbatim}",
        "yes.tex": b"Yes", "no.tex": b"No",
    })
    assert result.file_activity["yes.tex"] == "ACTIVE"
    assert result.file_activity["no.tex"] == "INACTIVE"


@pytest.mark.parametrize("prefix,code", [
    (br"\newcommand{\load}{\input{body}}", "OPAQUE_TEX"),
    (br"\usepackage{custom}", "OPAQUE_TEX"),
    (br"\includeonly{body}", "OPAQUE_TEX"),
    (br"\ifdefined\choice", "CONDITIONAL_UNKNOWN"),
    (br"\load", "UNKNOWN_COMMAND"),
])
def test_opaque_tex_prevents_false_activity_certainty(prefix, code):
    result = analyze_tex_structure("main.tex", {"main.tex": prefix + br"\input{body}", "body.tex": b"Body", "unseen.tex": b"Could be loaded by macro"})
    assert code in {issue.code for issue in result.issues}
    assert result.file_activity["body.tex"] == "UNKNOWN"
    assert result.file_activity["unseen.tex"] == "UNKNOWN"
    assert all(edge.activity == "UNKNOWN" for edge in result.includes)


def test_included_macro_context_can_affect_later_parent_input():
    result = analyze_tex_structure("main.tex", {
        "main.tex": br"\input{defs}\input{body}",
        "defs.tex": br"\def\input#1{}", "body.tex": b"Maybe ignored",
    })
    assert result.requires_review
    assert result.file_activity["body.tex"] == "UNKNOWN"


def test_definition_body_conditionals_never_create_false_inactive_labels():
    result = analyze_tex_structure("main.tex", {
        "main.tex": br"\def\skip{\iffalse}\input{body}\fi",
        "body.tex": b"Execution cannot be inferred from a definition body",
    })
    assert result.includes[0].activity == "UNKNOWN"


def test_custom_verbatim_or_comment_environments_require_review():
    result = analyze_tex_structure("main.tex", {
        "main.tex": br"\begin{comment}\input{body}\end{comment}",
        "body.tex": b"Requires external environment semantics",
    })
    assert "OPAQUE_ENVIRONMENT" in {issue.code for issue in result.issues}
    assert result.includes[0].activity == "UNKNOWN"


@pytest.mark.parametrize("text", [br"\verb|unfinished", br"\begin{verbatim}unfinished", b"\\verb\n"])
def test_unclosed_verbatim_preserves_parse_blockers(text):
    result = analyze_tex_structure("main.tex", {"main.tex": text})
    assert "MALFORMED_VERBATIM" in {issue.code for issue in result.issues}


def test_included_non_tex_extension_cannot_be_silently_treated_as_parsed():
    result = analyze_tex_structure("main.tex", {"main.tex": br"\input{defs.sty}", "defs.sty": br"\def\input#1{}"})
    assert "UNPARSED_INCLUDED_FILE" in {issue.code for issue in result.issues}
    assert result.file_activity["defs.sty"] == "UNKNOWN"


@pytest.mark.parametrize("source,code", [
    (br"\input{missing}", "MISSING_INCLUDE"),
    (br"\input{\filename}", "UNRESOLVED_INCLUDE"),
    (br"\input{body", "UNRESOLVED_INCLUDE"),
    (br"\input{../outside}", "UNSAFE_INCLUDE_PATH"),
    (br"\else\input{body}", "UNBALANCED_CONDITIONAL"),
    (b"\xff\\input{body}", "UNSUPPORTED_ENCODING"),
])
def test_unresolvable_sources_preserve_explicit_blockers(source, code):
    result = analyze_tex_structure("main.tex", {"main.tex": source, "body.tex": b"Body"})
    assert result.requires_review
    assert code in {issue.code for issue in result.issues}


def test_cycles_are_reported_without_recursive_execution():
    result = analyze_tex_structure("main.tex", {"main.tex": br"\input{other}", "other.tex": br"\input{main}"})
    assert "INCLUDE_CYCLE" in {issue.code for issue in result.issues}


def test_source_map_validation_and_limits_fail_closed():
    for sources in [{"other.tex": b"x"}, {"main.tex": b"x", "./main.tex": b"y"}, {"../main.tex": b"x"}, {"main.tex": "not bytes"}]:
        with pytest.raises(SourceError):
            analyze_tex_structure("main.tex", sources)
    with pytest.raises(SourceError):
        analyze_tex_structure("main.tex", {"main.tex": b"a", "body.tex": b"b"}, max_files=1)
    with pytest.raises(SourceError):
        analyze_tex_structure("main.tex", {"main.tex": b"long"}, max_total_bytes=1)
    with pytest.raises(SourceError):
        analyze_tex_structure("main.tex", {"main.tex": br"\section{A}\section{B}"}, max_commands=1)
    with pytest.raises(SourceError):
        analyze_tex_structure("main.tex", {"main.tex": br"\input{a}\input{b}"}, max_includes=1)
    with pytest.raises(SourceError):
        analyze_tex_structure("main.tex", {"main.tex": br"\iftrue\iftrue\fi\fi"}, max_conditional_depth=1)
