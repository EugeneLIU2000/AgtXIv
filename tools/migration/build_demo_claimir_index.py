#!/usr/bin/env python3
"""Build demo-wide ClaimIR migration indexes, manifests, and a readable comparison."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-08-22T00:00:00Z"


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest_value(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def digest_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def file_ref(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(ROOT)), "artifact_hash": digest_file(path)}


def main() -> int:
    slugs = sorted(path.stem for path in (ROOT / "Stabilizerness/MathClaimIRRegistry/migrations").glob("*.jsonl"))
    disposition_totals: collections.Counter[str] = collections.Counter()
    new_totals: collections.Counter[str] = collections.Counter()
    papers = []
    high_risk = []

    paper_registry = ROOT / "Stabilizerness/PaperAgentRegistry"
    (paper_registry / "manifests").mkdir(parents=True, exist_ok=True)

    for slug in slugs:
        legacy_agent_path = ROOT / f"agents/{slug}/agent.json"
        legacy = json.loads(legacy_agent_path.read_text())
        paper_id = legacy["agent"]["paper_id"]
        source_path = ROOT / legacy["source"]["canonical_artifact"]
        claim_path = ROOT / f"Stabilizerness/ScientificClaimRegistry/claims/{slug}.jsonl"
        ir_path = ROOT / f"Stabilizerness/MathClaimIRRegistry/claims/{slug}.jsonl"
        prop_path = ROOT / f"Stabilizerness/ExternalRecordRegistry/propositions/{slug}.jsonl"
        evidence_path = ROOT / f"Stabilizerness/ExternalRecordRegistry/evidence/{slug}.jsonl"
        migration_path = ROOT / f"Stabilizerness/MathClaimIRRegistry/migrations/{slug}.jsonl"
        summary_path = ROOT / f"Stabilizerness/MathClaimIRRegistry/migrations/{slug}-summary.json"
        preprocessing_path = ROOT / f"Stabilizerness/MathClaimIRRegistry/preprocessing/{slug}.json"
        source_anchor_path = ROOT / f"Stabilizerness/MathClaimIRRegistry/source-anchors/{slug}.jsonl"
        classification_path = ROOT / f"Stabilizerness/ExternalRecordRegistry/claim-classifications/{slug}.jsonl"

        migrations = load_jsonl(migration_path)
        dispositions = collections.Counter(row["disposition"] for row in migrations)
        disposition_totals.update(dispositions)
        counts = {
            "ScientificClaim": len(load_jsonl(claim_path)),
            "MathClaimIR": len(load_jsonl(ir_path)),
            "MathematicalPropositionIR": len(load_jsonl(prop_path)),
            "EvidenceRecord": len(load_jsonl(evidence_path)),
            "SourceClaimClassification": len(load_jsonl(classification_path)) if classification_path.exists() else 0,
        }
        new_totals.update(counts)
        unresolved = sorted(row["legacy_record"]["id"] for row in migrations if row["disposition"] in {"SOURCE_UNSUPPORTED", "BLOCKED"})
        semantic_count = sum(1 for row in migrations if any(d["significance"] in {"SEMANTIC", "SAFETY"} for d in row["differences"]))
        for row in migrations:
            if row["review_priority"] in {"HIGH", "BLOCKING"} or any(d["significance"] in {"SEMANTIC", "SAFETY"} for d in row["differences"]):
                high_risk.append({
                    "paper_id": paper_id,
                    "legacy_id": row["legacy_record"]["id"],
                    "disposition": row["disposition"],
                    "review_priority": row["review_priority"],
                    "differences": [d for d in row["differences"] if d["significance"] in {"SEMANTIC", "SAFETY"}],
                    "source_support": row["source_audit"]["support"],
                })

        papers.append({
            "slug": slug,
            "paper_id": paper_id,
            "legacy_records": len(migrations),
            "dispositions": dict(sorted(dispositions.items())),
            "new_records": counts,
            "semantic_or_safety_changes": semantic_count,
            "unresolved_legacy_ids": unresolved,
        })

        manifest = {
            "schema": "agtxiv.paper-agent-manifest/1.0.0",
            "id": f"paper-agent-manifest:{slug}",
            "record_revision": 1,
            "supersedes": None,
            "produced_at": STAMP,
            "paper_id": paper_id,
            "legacy_agent": file_ref(legacy_agent_path),
            "source": {
                "canonical_artifact": str(source_path.relative_to(ROOT)),
                "artifact_hash": digest_file(source_path),
                "preprocessing_record": file_ref(preprocessing_path),
                **({"source_anchor_records": file_ref(source_anchor_path)} if source_anchor_path.exists() else {}),
            },
            "registries": {
                "scientific_claims": file_ref(claim_path),
                "math_claim_ir": file_ref(ir_path),
                "mathematical_propositions": file_ref(prop_path),
                "evidence": file_ref(evidence_path),
                **({"source_claim_classifications": file_ref(classification_path)} if classification_path.exists() else {}),
            },
            "migration": {
                "dispositions": file_ref(migration_path),
                "summary": file_ref(summary_path),
                "legacy_record_count": len(migrations),
                "unresolved_legacy_ids": unresolved,
            },
            "content_hash": "sha256:" + "0" * 64,
        }
        manifest["content_hash"] = digest_value({k: v for k, v in manifest.items() if k != "content_hash"})
        (paper_registry / f"manifests/{slug}.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")

    aggregate = {
        "schema": "agtxiv.demo-claim-migration-summary/1.0.0",
        "produced_at": STAMP,
        "legacy_record_count": sum(p["legacy_records"] for p in papers),
        "migration_disposition_count": sum(disposition_totals.values()),
        "disposition_totals": dict(sorted(disposition_totals.items())),
        "new_record_totals": dict(sorted(new_totals.items())),
        "papers": papers,
        "high_risk_differences": high_risk,
        "validation": {
            "expected_legacy_records": 50,
            "all_legacy_records_disposed": sum(disposition_totals.values()) == 50,
            "claimir_contains_verification_status": False,
        },
    }
    aggregate_path = ROOT / "Stabilizerness/MathClaimIRRegistry/migrations/demo-comparison.json"
    aggregate_path.write_text(json.dumps(aggregate, ensure_ascii=False, sort_keys=True, indent=2) + "\n")

    lines = [
        "# Demo MathClaimIR migration comparison", "",
        "This report compares the 50 legacy `knowledge/statements.jsonl` records with records reconstructed from frozen canonical LaTeX. Legacy files remain unchanged.", "",
        "## Coverage", "",
        f"- Legacy records: **{aggregate['legacy_record_count']}**",
        f"- Migration dispositions: **{aggregate['migration_disposition_count']}**",
        f"- Source-grounded MathClaimIR records: **{new_totals['MathClaimIR']}**",
        f"- External mathematical propositions: **{new_totals['MathematicalPropositionIR']}**",
        f"- External evidence records: **{new_totals['EvidenceRecord']}**",
        f"- External source-claim classifications: **{new_totals['SourceClaimClassification']}**", "",
        "## Per-paper result", "",
        "| PaperAgent | Legacy | ClaimIR | Proposition | Evidence | Main dispositions |", "|---|---:|---:|---:|---:|---|",
    ]
    for p in papers:
        disp = ", ".join(f"{k}={v}" for k, v in p["dispositions"].items())
        lines.append(f"| `{p['slug']}` | {p['legacy_records']} | {p['new_records']['MathClaimIR']} | {p['new_records']['MathematicalPropositionIR']} | {p['new_records']['EvidenceRecord']} | {disp} |")
    lines += ["", "## Interpretation", "",
        "- `MathClaimIR` records source mathematical meaning only; truth judgments, Lean results, blockers, and attribution are external.",
        "- `RECLASSIFIED_EXTERNAL` marks legacy material that was an agent reconstruction, counterexample, numerical check, or verification observation rather than a source claim.",
        "- `SPLIT` marks compound legacy statements decomposed into atomic conclusions or into source and derived layers.",
        "- `SEMANTIC_CORRECTION` marks a source-fidelity correction, not a claim that the paper is mathematically false.",
        "- `SOURCE_UNSUPPORTED` preserves a legacy statement whose asserted detail could not be located in the frozen LaTeX.", "",
        "## High-priority differences", "",
    ]
    for item in high_risk:
        details = "; ".join(f"{d['field']}: {d['change_type']}" for d in item["differences"]) or "high-priority source boundary"
        lines.append(f"- `{item['legacy_id']}` ({item['disposition']}, source={item['source_support']}): {details}.")
    (ROOT / "Stabilizerness/MathClaimIRRegistry/migrations/demo-comparison.md").write_text("\n".join(lines) + "\n")

    registry_specs = [
        (ROOT / "Stabilizerness/ScientificClaimRegistry/manifest.json", "claim_files", "Stabilizerness/ScientificClaimRegistry/claims/*.jsonl"),
        (ROOT / "Stabilizerness/MathClaimIRRegistry/manifest.json", "claim_files", "Stabilizerness/MathClaimIRRegistry/claims/*.jsonl"),
        (ROOT / "Stabilizerness/ExternalRecordRegistry/manifest.json", "proposition_files", "Stabilizerness/ExternalRecordRegistry/propositions/*.jsonl"),
    ]
    for manifest_path, key, pattern in registry_specs:
        manifest = json.loads(manifest_path.read_text())
        manifest[key] = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
        if manifest_path.name == "manifest.json" and "MathClaimIRRegistry" in str(manifest_path):
            manifest["preprocessing_files"] = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("Stabilizerness/MathClaimIRRegistry/preprocessing/*.json"))
            manifest["source_anchor_files"] = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("Stabilizerness/MathClaimIRRegistry/source-anchors/*.jsonl"))
            manifest["migration_files"] = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("Stabilizerness/MathClaimIRRegistry/migrations/*.jsonl"))
        if "ExternalRecordRegistry" in str(manifest_path):
            manifest["evidence_files"] = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("Stabilizerness/ExternalRecordRegistry/evidence/*.jsonl"))
            manifest["source_claim_classification_files"] = sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("Stabilizerness/ExternalRecordRegistry/claim-classifications/*.jsonl"))
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")

    paper_manifest = {
        "schema": "agtxiv.registry-manifest/1.0.0",
        "registry": "PaperAgentRegistry",
        "scope": "Stabilizerness demo",
        "manifest_files": sorted(str(p.relative_to(ROOT)) for p in (paper_registry / "manifests").glob("*.json")),
        "authority": "Immutable v1 PaperAgent manifests for the ClaimIR-reconstructed demo; legacy agents remain migration inputs."
    }
    (paper_registry / "manifest.json").write_text(json.dumps(paper_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print(f"papers={len(papers)} legacy={aggregate['legacy_record_count']} high_risk={len(high_risk)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
