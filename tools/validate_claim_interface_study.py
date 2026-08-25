#!/usr/bin/env python3
"""Validate ScientificClaim interface study data, cases, and source anchors."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STUDY_ROOT = ROOT / "docs/specifications/scientific-claim-interface"
REQUIRED_FINAL_SECTIONS = (
    "sections/01-literature.tex",
    "sections/02-method.tex",
    "sections/03-initial-principles.tex",
    "sections/04-cross-case-analysis.tex",
    "sections/05-iteration-log.tex",
    "sections/06-normative-specification.tex",
    "sections/07-migration.tex",
    "sections/08-references.tex",
)
FINAL_REVIEW_STATUSES = frozenset(("SOURCE_CHECKED", "REVISED"))


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    claims: list[dict[str, Any]] = field(default_factory=list)
    source_verification: str = "skipped"
    summary: dict[str, Any] = field(default_factory=dict)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        errors.append(f"{path}: cannot read file: {exc}")
    except json.JSONDecodeError as exc:
        errors.append(f"{path}:{exc.lineno}: invalid JSON: {exc.msg}")
    return None


def read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append(f"{path}: cannot read file: {exc}")
        return rows
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(row, dict):
            errors.append(f"{path}:{number}: record must be a JSON object")
            continue
        row["__location__"] = f"{path}:{number}"
        rows.append(row)
    return rows


def selected_papers(manifest: Any, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("selected"), list):
        errors.append("sample manifest must contain a selected array")
        return {}
    selected: dict[str, dict[str, Any]] = {}
    sample_indices: set[int] = set()
    for index, paper in enumerate(manifest["selected"], 1):
        if not isinstance(paper, dict):
            errors.append(f"manifest selected item {index} is not an object")
            continue
        arxiv_id = paper.get("arxiv_id")
        if not isinstance(arxiv_id, str):
            errors.append(f"manifest selected item {index} has no arxiv_id")
            continue
        if arxiv_id in selected:
            errors.append(f"duplicate selected paper ID: {arxiv_id}")
        selected[arxiv_id] = paper
        sample_index = paper.get("sample_index")
        if not isinstance(sample_index, int) or sample_index in sample_indices:
            errors.append(f"selected paper {arxiv_id} has an invalid or duplicate sample_index")
        sample_indices.add(sample_index)
        if paper.get("versioned_id") != f"{arxiv_id}v1":
            errors.append(f"selected paper {arxiv_id} must be pinned to v1")
    return selected


def load_schema_validator(schema_path: Path, errors: list[str]) -> Any:
    try:
        import jsonschema
    except ImportError:
        errors.append("jsonschema is required to validate claim records; install the 'jsonschema' package")
        return None
    schema = read_json(schema_path, errors)
    if schema is None:
        return None
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        return jsonschema.Draft202012Validator(schema)
    except jsonschema.SchemaError as exc:
        errors.append(f"{schema_path}: invalid JSON Schema: {exc.message}")
        return None


def validate_source_span(span: Any, location: str, paper_id: str, source_root: Path | None, errors: list[str]) -> None:
    if not isinstance(span, dict):
        errors.append(f"{location}: source span must be an object")
        return
    start, end = span.get("line_start"), span.get("line_end")
    if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < 1 or start > end:
        errors.append(f"{location}: malformed 1-indexed source span {start!r}-{end!r}")
        return
    if source_root is None:
        return
    relative = Path(str(span.get("source_file", "")))
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"{location}: source_file must be a safe relative path")
        return
    resolved_root = source_root.resolve()
    candidates = (source_root / paper_id / relative, source_root / relative, ROOT / relative)
    source_path = next(
        (
            candidate
            for candidate in candidates
            if candidate.is_file() and candidate.resolve().is_relative_to(resolved_root)
        ),
        candidates[0],
    )
    try:
        with source_path.open("r", encoding="utf-8", newline="") as source:
            lines = source.readlines()
    except OSError as exc:
        errors.append(f"{location}: cannot read source file {source_path}: {exc}")
        return
    if end > len(lines):
        errors.append(f"{location}: source span {start}-{end} exceeds {source_path} ({len(lines)} lines)")
        return
    actual = "".join(lines[start - 1:end])
    if span.get("exact_text") != actual:
        errors.append(f"{location}: exact_text mismatch for {source_path}:{start}-{end}")


def count_summary(claims: list[dict[str, Any]]) -> dict[str, Any]:
    def count(key: str) -> dict[str, int]:
        return dict(sorted(Counter(str(row.get(key, "<missing>")) for row in claims).items()))

    pressures: Counter[str] = Counter()
    suitability: Counter[str] = Counter()
    per_paper: Counter[str] = Counter()
    for row in claims:
        per_paper[str(row.get("paper_id", "<missing>"))] += 1
        normalization = row.get("math_normalization")
        suitability[str(normalization.get("suitability", "<missing>")) if isinstance(normalization, dict) else "<missing>"] += 1
        values = row.get("interface_pressure")
        if isinstance(values, list):
            pressures.update(str(value) for value in values)
    return {
        "total_claims": len(claims),
        "by_paper": dict(sorted(per_paper.items())),
        "by_modality": count("modality"),
        "by_attribution": count("knowledge_attribution"),
        "by_mathclaimir_suitability": dict(sorted(suitability.items())),
        "by_interface_pressure": dict(sorted(pressures.items())),
    }


def validate_study(study_root: Path = STUDY_ROOT, source_root: Path | None = None, final_readiness: bool = False) -> ValidationResult:
    result = ValidationResult(source_verification="performed" if source_root is not None else "skipped")
    errors = result.errors
    data_root = study_root / "data"
    manifest_path = data_root / "sample_manifest.json"
    pool_path = data_root / "candidate_pool.jsonl"
    manifest = read_json(manifest_path, errors)
    selected = selected_papers(manifest, errors)

    pool_rows = read_jsonl(pool_path, errors) if pool_path.is_file() else []
    if not pool_path.is_file():
        errors.append(f"missing candidate pool: {pool_path}")
    pool_ids = [row.get("id") for row in pool_rows]
    if len(pool_ids) != len(set(pool_ids)):
        errors.append("candidate pool contains duplicate IDs")
    if isinstance(manifest, dict):
        if manifest.get("pool_size") != len(pool_rows):
            errors.append(f"candidate pool count {len(pool_rows)} does not match manifest pool_size {manifest.get('pool_size')}")
        if pool_path.is_file() and manifest.get("candidate_pool_sha256") != sha256_file(pool_path):
            errors.append("candidate pool digest does not match manifest candidate_pool_sha256")
    missing_pool_ids = sorted(set(selected) - set(pool_ids))
    if missing_pool_ids:
        errors.append(f"selected IDs absent from candidate pool: {', '.join(missing_pool_ids)}")

    validator = load_schema_validator(data_root / "claim-record-schema.json", errors)
    claims: list[dict[str, Any]] = []
    claim_files = sorted(data_root.glob("claims-*.jsonl"))
    expected_claim_files = {data_root / f"claims-{paper_id}.jsonl": paper_id for paper_id in selected}
    for path in claim_files:
        expected_paper = expected_claim_files.get(path)
        if expected_paper is None:
            errors.append(f"unknown claim file: {path.name}")
        for row in read_jsonl(path, errors):
            location = row.pop("__location__")
            claims.append(row)
            if validator is not None:
                for schema_error in sorted(validator.iter_errors(row), key=lambda error: list(error.absolute_path)):
                    field_path = ".".join(str(part) for part in schema_error.absolute_path)
                    errors.append(f"{location}{'.' + field_path if field_path else ''}: schema validation failed: {schema_error.message}")
            raw_paper_id = row.get("paper_id")
            paper_version = selected.get(expected_paper, {}).get("versioned_id") if expected_paper else None
            if expected_paper is not None and raw_paper_id != f"arxiv:{paper_version}":
                errors.append(f"{location}: paper_id does not match claim file paper {expected_paper}v1")
            if not isinstance(raw_paper_id, str) or not raw_paper_id.startswith("arxiv:"):
                paper_id = ""
            else:
                versioned = raw_paper_id.removeprefix("arxiv:")
                paper_id = versioned.rsplit("v", 1)[0]
                if paper_id not in selected:
                    errors.append(f"{location}: unknown paper {raw_paper_id}")
                elif versioned != f"{paper_id}v1":
                    errors.append(f"{location}: selected paper ID must use v1: {raw_paper_id}")
            spans = row.get("source_spans")
            if isinstance(spans, list):
                for span_index, span in enumerate(spans, 1):
                    validate_source_span(span, f"{location}.source_spans[{span_index}]", paper_id, source_root, errors)

    candidate_ids: dict[str, str] = {}
    for path in claim_files:
        for row in read_jsonl(path, []):
            location = row.pop("__location__")
            candidate_id = row.get("candidate_id")
            if isinstance(candidate_id, str):
                if candidate_id in candidate_ids:
                    errors.append(f"duplicate candidate_id {candidate_id}: {candidate_ids[candidate_id]} and {location}")
                else:
                    candidate_ids[candidate_id] = location

    cases_root = study_root / "cases"
    all_cases = sorted(cases_root.glob("case-*.tex")) if cases_root.is_dir() else []
    expected_cases = {cases_root / f"case-{paper_id}.tex": paper_id for paper_id in selected}
    for path in all_cases:
        if path not in expected_cases:
            errors.append(f"unknown case file: {path.name}")
        try:
            line_count = len(path.read_text(encoding="utf-8").splitlines())
        except OSError as exc:
            errors.append(f"{path}: cannot read case file: {exc}")
        else:
            if line_count >= 1000:
                errors.append(f"{path}: case file has {line_count} lines; must be below 1000")

    for path, paper_id in expected_claim_files.items():
        if not path.is_file():
            errors.append(f"selected paper {paper_id} is missing claim JSONL {path.name}")
    for path, paper_id in expected_cases.items():
        if not path.is_file():
            errors.append(f"selected paper {paper_id} is missing case file {path.name}")

    if final_readiness:
        for row in claims:
            if row.get("review_status") not in FINAL_REVIEW_STATUSES:
                errors.append(f"claim {row.get('candidate_id', '<missing>')} is not SOURCE_CHECKED/REVISED")
        for relative in REQUIRED_FINAL_SECTIONS:
            if not (study_root / relative).is_file():
                errors.append(f"required final specification section is missing: {relative}")

    result.claims = claims
    result.summary = count_summary(claims)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", type=Path, default=STUDY_ROOT)
    parser.add_argument("--source-root", type=Path, help="root containing one extracted-source directory per unversioned arXiv ID")
    parser.add_argument("--final-readiness", action="store_true", help="also require complete cases, reviewed claims, and final sections")
    args = parser.parse_args()
    result = validate_study(args.study_root, args.source_root, args.final_readiness)
    for error in result.errors:
        print(f"ERROR: {error}")
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    if result.source_verification == "skipped":
        print("source verification: skipped (supply --source-root to verify exact source spans)")
    else:
        print("source verification: performed")
    print(f"claim-interface study validation: errors={len(result.errors)} final_readiness={'yes' if args.final_readiness else 'no'}")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
