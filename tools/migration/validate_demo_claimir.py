#!/usr/bin/env python3
"""Validate complete legacy-to-MathClaimIR coverage for the five demo PaperAgents."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AGENTS = sorted((ROOT / "agents").glob("*/knowledge/statements.jsonl"))
ZERO_HASH = "sha256:" + "0" * 64
FORBIDDEN_CORE_KEYS = {
    "status", "truth_status", "verification", "verification_status", "lifecycle_status",
    "blockers", "formalization", "alignment", "confidence", "attribution",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["__line__"] = line_number
        rows.append(row)
    return rows


def without_meta(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k != "__line__"}


def canonical_hash(row: dict[str, Any]) -> str:
    raw = json.dumps(without_meta(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def recurse_forbidden(value: Any, path: str = "") -> list[str]:
    errors = []
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else key
            if key in FORBIDDEN_CORE_KEYS:
                errors.append(here)
            errors.extend(recurse_forbidden(child, here))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            errors.extend(recurse_forbidden(child, f"{path}[{i}]"))
    return errors


def main() -> int:
    errors: list[str] = []
    legacy_total = migration_total = 0
    all_new_ids: set[str] = set()
    ids_by_kind: dict[str, set[str]] = {
        "ScientificClaim": set(),
        "MathClaimIR": set(),
        "MathematicalPropositionIR": set(),
        "EvidenceRecord": set(),
    }

    registry_patterns = [
        ("ScientificClaim", "Stabilizerness/ScientificClaimRegistry/claims/*.jsonl"),
        ("MathClaimIR", "Stabilizerness/MathClaimIRRegistry/claims/*.jsonl"),
        ("MathematicalPropositionIR", "Stabilizerness/ExternalRecordRegistry/propositions/*.jsonl"),
        ("EvidenceRecord", "Stabilizerness/ExternalRecordRegistry/evidence/*.jsonl"),
    ]
    for kind, pattern in registry_patterns:
        for path in ROOT.glob(pattern):
            for row in load_jsonl(path):
                identifier = row.get("id")
                if not identifier:
                    errors.append(f"{path}:{row['__line__']}: missing id")
                elif identifier in all_new_ids:
                    errors.append(f"duplicate new record id: {identifier}")
                else:
                    all_new_ids.add(identifier)
                    ids_by_kind[kind].add(identifier)
                if row.get("schema") == "agtxiv.math-claimir/1.0.0":
                    forbidden = recurse_forbidden(without_meta(row))
                    if forbidden:
                        errors.append(f"{path}:{row['__line__']}: forbidden ClaimIR keys {forbidden}")

    for legacy_path in AGENTS:
        slug = legacy_path.parents[1].name
        legacy_rows = load_jsonl(legacy_path)
        legacy_total += len(legacy_rows)
        migration_path = ROOT / f"Stabilizerness/MathClaimIRRegistry/migrations/{slug}.jsonl"
        if not migration_path.exists():
            errors.append(f"missing migration file for {slug}")
            continue
        migrations = load_jsonl(migration_path)
        migration_total += len(migrations)
        by_id = {m.get("legacy_record", {}).get("id"): m for m in migrations}
        if len(by_id) != len(migrations):
            errors.append(f"{migration_path}: duplicate legacy ids")
        for legacy in legacy_rows:
            legacy_id = legacy.get("id")
            migration = by_id.get(legacy_id)
            if not migration:
                errors.append(f"{slug}: no migration for {legacy_id}")
                continue
            ref = migration["legacy_record"]
            expected_path = str(legacy_path.relative_to(ROOT))
            if ref.get("path") != expected_path:
                errors.append(f"{slug}:{legacy_id}: legacy path mismatch")
            if ref.get("line") != legacy["__line__"]:
                errors.append(f"{slug}:{legacy_id}: legacy line mismatch")
            if ref.get("content_hash") != canonical_hash(legacy):
                errors.append(f"{slug}:{legacy_id}: legacy content hash mismatch")
            for new_ref in migration.get("new_records", []):
                identifier = new_ref.get("id")
                if identifier and identifier not in all_new_ids:
                    errors.append(f"{slug}:{legacy_id}: missing new record {identifier}")
        extras = set(by_id) - {row.get("id") for row in legacy_rows}
        if extras:
            errors.append(f"{slug}: migration entries for unknown legacy ids {sorted(extras)}")

        summary_path = migration_path.with_name(f"{slug}-summary.json")
        if not summary_path.exists():
            errors.append(f"missing summary for {slug}")

        preprocessing_path = ROOT / f"Stabilizerness/MathClaimIRRegistry/preprocessing/{slug}.json"
        if not preprocessing_path.exists():
            errors.append(f"missing preprocessing receipt for {slug}")

    preprocessing_ids: set[str] = set()
    for path in ROOT.glob("Stabilizerness/MathClaimIRRegistry/preprocessing/*.json"):
        record = json.loads(path.read_text())
        identifier = record.get("id")
        if not identifier:
            errors.append(f"{path}: missing preprocessing id")
        elif identifier in preprocessing_ids:
            errors.append(f"duplicate preprocessing id: {identifier}")
        else:
            preprocessing_ids.add(identifier)

    anchors: set[str] = set()
    anchor_paths = list(ROOT.glob("agents/*/source/anchors.jsonl"))
    anchor_paths += list(ROOT.glob("Stabilizerness/MathClaimIRRegistry/source-anchors/*.jsonl"))
    for path in anchor_paths:
        for anchor in load_jsonl(path):
            identifier = anchor.get("id")
            if identifier in anchors:
                errors.append(f"{path}:{anchor['__line__']}: duplicate source anchor {identifier}")
            anchors.add(identifier)
            artifact = ROOT / anchor.get("artifact", "")
            if not artifact.exists():
                errors.append(f"{path}:{anchor['__line__']}: missing source artifact {artifact}")

    for path in ROOT.glob("Stabilizerness/MathClaimIRRegistry/claims/*.jsonl"):
        for row in load_jsonl(path):
            for anchor in row.get("source", {}).get("statement_anchors", []) + row.get("source", {}).get("proof_anchors", []):
                if anchor not in anchors:
                    errors.append(f"{path}:{row['__line__']}: unknown source anchor {anchor}")
            preprocessing_ref = row.get("normalization", {}).get("preprocessing_record_ref")
            if preprocessing_ref not in preprocessing_ids:
                errors.append(f"{path}:{row['__line__']}: unknown preprocessing record {preprocessing_ref}")
            if ZERO_HASH in json.dumps(row):
                errors.append(f"{path}:{row['__line__']}: unfinalized zero hash")

    classification_count = 0
    for path in ROOT.glob("Stabilizerness/ExternalRecordRegistry/claim-classifications/*.jsonl"):
        for row in load_jsonl(path):
            classification_count += 1
            if row.get("classification") != "REFUTED":
                errors.append(f"{path}:{row['__line__']}: unsupported source-claim classification")
            if row.get("downstream_policy") != "EXCLUDE_AS_THEOREM_DEPENDENCY":
                errors.append(f"{path}:{row['__line__']}: unsafe downstream policy")
            if row.get("scientific_claim_id") not in ids_by_kind["ScientificClaim"]:
                errors.append(f"{path}:{row['__line__']}: unknown ScientificClaim target")
            if row.get("math_claim_ir_id") not in ids_by_kind["MathClaimIR"]:
                errors.append(f"{path}:{row['__line__']}: unknown MathClaimIR target")
            for evidence_id in row.get("evidence_ids", []):
                if evidence_id not in ids_by_kind["EvidenceRecord"]:
                    errors.append(f"{path}:{row['__line__']}: unknown evidence {evidence_id}")

    required_refuted_claims = {
        "math-claim-ir:2602.18939v1:fixed-window-monotonicity-claimed",
        "math-claim-ir:2602.18939v1:reduced-polytope-vrep",
    }
    classified_claims = {
        row.get("math_claim_ir_id")
        for path in ROOT.glob("Stabilizerness/ExternalRecordRegistry/claim-classifications/*.jsonl")
        for row in load_jsonl(path)
    }
    missing_classifications = required_refuted_claims - classified_claims
    if missing_classifications:
        errors.append(f"missing downstream exclusion classifications: {sorted(missing_classifications)}")

    if legacy_total != 50:
        errors.append(f"expected 50 legacy statements, found {legacy_total}")
    if migration_total != legacy_total:
        errors.append(f"migration count {migration_total} != legacy count {legacy_total}")

    for error in errors:
        print(error)
    print(f"legacy={legacy_total} migrations={migration_total} new_records={len(all_new_ids)} classifications={classification_count} preprocessing_ids={len(preprocessing_ids)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
