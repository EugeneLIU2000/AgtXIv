#!/usr/bin/env python3
"""Finalize and validate AgtXIv demo migration JSONL records.

The command fills deterministic hashes for ScientificClaim, MathClaimIR, and
MathematicalPropositionIR records. It never rewrites legacy Agent files.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROFILE_ID = "agtxiv.canonical-json/1.0.0"
PROFILE_HASH = "sha256:" + hashlib.sha256(PROFILE_ID.encode()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def finalize_scientific_claim(record: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["content_hash"] = digest({k: v for k, v in result.items() if k != "content_hash"})
    return result


def semantic_claimir_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "revision": record["revision"],
        "claim_id": record["claim"]["id"],
        "source": record["source"],
        "statement_kind": record["statement_kind"],
        "normalized_statement_expanded_latex": record["normalized_statement_expanded_latex"],
        "structured_statement": record["structured_statement"],
        "normalization": record["normalization"],
    }


def finalize_ir(record: dict[str, Any], proposition: bool = False) -> dict[str, Any]:
    result = copy.deepcopy(record)
    if proposition:
        semantic = {
            "id": result["id"], "revision": result["revision"], "origin": result["origin"],
            "derivation_provenance": result["derivation_provenance"],
            "normalized_statement_expanded_latex": result["normalized_statement_expanded_latex"],
            "structured_statement": result["structured_statement"],
        }
        schema_uri = "https://agtxiv.org/schema/mathematical-proposition-ir/1.0.0"
    else:
        semantic = semantic_claimir_payload(result)
        schema_uri = "https://agtxiv.org/schema/math-claimir/1.0.0"
    result["semantic_content_hash"] = digest(semantic)
    result["artifact"] = {
        "schema_uri": schema_uri,
        "schema_version": "1.0.0",
        "serialization_profile": {"id": PROFILE_ID, "content_hash": PROFILE_HASH},
        "artifact_hash": "sha256:" + "0" * 64,
    }
    artifact_payload = copy.deepcopy(result)
    artifact_payload["artifact"]["artifact_hash"] = None
    result["artifact"]["artifact_hash"] = digest(artifact_payload)
    return result


def validate(rows: list[dict[str, Any]], schema_path: Path, label: str) -> list[str]:
    errors: list[str] = []
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is unavailable; structural validation skipped"]
    schema = json.loads(schema_path.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for i, row in enumerate(rows, 1):
        for error in sorted(validator.iter_errors(row), key=lambda e: list(e.path)):
            location = ".".join(str(x) for x in error.path)
            errors.append(f"{label}:{i}:{location}: {error.message}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate without rewriting")
    args = parser.parse_args()

    claim_files = sorted((ROOT / "Stabilizerness/ScientificClaimRegistry/claims").glob("*.jsonl"))
    ir_files = sorted((ROOT / "Stabilizerness/MathClaimIRRegistry/claims").glob("*.jsonl"))
    proposition_files = sorted((ROOT / "Stabilizerness/ExternalRecordRegistry/propositions").glob("*.jsonl"))
    evidence_files = sorted((ROOT / "Stabilizerness/ExternalRecordRegistry/evidence").glob("*.jsonl"))
    preprocessing_files = sorted((ROOT / "Stabilizerness/MathClaimIRRegistry/preprocessing").glob("*.json"))
    migration_files = sorted((ROOT / "Stabilizerness/MathClaimIRRegistry/migrations").glob("*.jsonl"))
    all_errors: list[str] = []

    claim_hashes: dict[str, tuple[int, str]] = {}
    for path in claim_files:
        rows = read_jsonl(path)
        finalized = [finalize_scientific_claim(r) for r in rows]
        for row in finalized:
            claim_hashes[row["id"]] = (row["record_revision"], row["content_hash"])
        if args.check and finalized != rows:
            all_errors.append(f"{path}: hashes are not finalized")
        elif not args.check:
            write_jsonl(path, finalized)
        all_errors.extend(validate(finalized if not args.check else rows, ROOT / "Stabilizerness/ScientificClaimRegistry/schema/scientific-claim.schema.json", str(path)))

    for path in ir_files:
        rows = read_jsonl(path)
        for row in rows:
            claim_id = row.get("claim", {}).get("id")
            if claim_id in claim_hashes:
                revision, content_hash = claim_hashes[claim_id]
                row["claim"] = {"id": claim_id, "record_revision": revision, "content_hash": content_hash}
        finalized = [finalize_ir(r) for r in rows]
        if args.check and finalized != rows:
            all_errors.append(f"{path}: hashes are not finalized")
        elif not args.check:
            write_jsonl(path, finalized)
        all_errors.extend(validate(finalized if not args.check else rows, ROOT / "Stabilizerness/MathClaimIRRegistry/schema/math-claim-ir.schema.json", str(path)))

    for path in proposition_files:
        rows = read_jsonl(path)
        finalized = [finalize_ir(r, proposition=True) for r in rows]
        if args.check and finalized != rows:
            all_errors.append(f"{path}: hashes are not finalized")
        elif not args.check:
            write_jsonl(path, finalized)
        all_errors.extend(validate(finalized if not args.check else rows, ROOT / "Stabilizerness/ExternalRecordRegistry/schema/mathematical-proposition-ir.schema.json", str(path)))

    for path in evidence_files:
        rows = read_jsonl(path)
        finalized = []
        for row in rows:
            item = copy.deepcopy(row)
            item["content_hash"] = digest({k: v for k, v in item.items() if k != "content_hash"})
            finalized.append(item)
        if args.check and finalized != rows:
            all_errors.append(f"{path}: hashes are not finalized")
        elif not args.check:
            write_jsonl(path, finalized)
        all_errors.extend(validate(finalized if not args.check else rows, ROOT / "Stabilizerness/ExternalRecordRegistry/schema/migration-evidence.schema.json", str(path)))

    for path in preprocessing_files:
        row = json.loads(path.read_text())
        finalized = copy.deepcopy(row)
        finalized["content_hash"] = digest({k: v for k, v in finalized.items() if k != "content_hash"})
        if args.check and finalized != row:
            all_errors.append(f"{path}: hash is not finalized")
        elif not args.check:
            path.write_text(json.dumps(finalized, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        all_errors.extend(validate([finalized if not args.check else row], ROOT / "Stabilizerness/MathClaimIRRegistry/schema/source-preprocessing.schema.json", str(path)))

    for path in migration_files:
        rows = read_jsonl(path)
        finalized = []
        for row in rows:
            item = copy.deepcopy(row)
            legacy = item.get("legacy_record", {})
            legacy_path = ROOT / legacy.get("path", "")
            line_number = legacy.get("line", 0)
            if legacy_path.exists() and isinstance(line_number, int) and line_number > 0:
                source_lines = [line for line in legacy_path.read_text().splitlines() if line.strip()]
                if line_number <= len(source_lines):
                    legacy_obj = json.loads(source_lines[line_number - 1])
                    legacy["content_hash"] = digest(legacy_obj)
            finalized.append(item)
        if args.check and finalized != rows:
            all_errors.append(f"{path}: legacy hashes are not finalized")
        elif not args.check:
            write_jsonl(path, finalized)
        all_errors.extend(validate(finalized if not args.check else rows, ROOT / "Stabilizerness/MathClaimIRRegistry/schema/claim-migration.schema.json", str(path)))

    for error in all_errors:
        print(error)
    print(f"scientific_claim_files={len(claim_files)} claimir_files={len(ir_files)} proposition_files={len(proposition_files)} evidence_files={len(evidence_files)} preprocessing_files={len(preprocessing_files)} migration_files={len(migration_files)} errors={len(all_errors)}")
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
