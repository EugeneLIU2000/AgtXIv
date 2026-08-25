from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.sample_claim_interface_arxiv as sampler
import tools.validate_claim_interface_study as validator


class SamplingTests(unittest.TestCase):
    def test_deterministic_per_stratum_shuffle_is_order_independent(self) -> None:
        rows = [
            {"id": "2608.00003", "primary_category": "hep-ph"},
            {"id": "2608.00001", "primary_category": "hep-th"},
            {"id": "2608.00002", "primary_category": "nucl-th"},
            {"id": "2608.00004", "primary_category": "gr-qc"},
        ]
        first = [row["id"] for row in sampler.deterministic_shuffle(rows, "qft-particle-nuclear")]
        second = [row["id"] for row in sampler.deterministic_shuffle(reversed(rows), "qft-particle-nuclear")]
        self.assertEqual(first, second)
        self.assertEqual(set(first), {"2608.00001", "2608.00002", "2608.00003"})

    def test_frozen_pool_and_manifest_pass_offline_check(self) -> None:
        self.assertEqual(sampler.validate_frozen(), [])


class ClaimInterfaceStudyValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "study"
        self.source_root = Path(self.temporary.name) / "sources"
        (self.root / "data").mkdir(parents=True)
        (self.root / "cases").mkdir()
        (self.root / "sections").mkdir()
        schema_source = validator.STUDY_ROOT / "data/claim-record-schema.json"
        (self.root / "data/claim-record-schema.json").write_bytes(schema_source.read_bytes())
        self.paper_ids = ("2608.00001", "2608.00002")
        self.pool = [
            {
                "authors": ["Author One"],
                "categories": ["hep-th"],
                "id": "2608.00001",
                "primary_category": "hep-th",
                "published": "2026-08-01T01:00:00Z",
                "title": "One",
                "updated": "2026-08-01T01:00:00Z",
                "versioned_id": "2608.00001v1",
            },
            {
                "authors": ["Author Two"],
                "categories": ["gr-qc"],
                "id": "2608.00002",
                "primary_category": "gr-qc",
                "published": "2026-08-01T02:00:00Z",
                "title": "Two",
                "updated": "2026-08-01T02:00:00Z",
                "versioned_id": "2608.00002v1",
            },
        ]
        self.write_pool_and_manifest()
        for index, paper_id in enumerate(self.paper_ids, 1):
            (self.root / "cases" / f"case-{paper_id}.tex").write_text("Case\n", encoding="utf-8")
            source_dir = self.source_root / paper_id
            source_dir.mkdir(parents=True)
            (source_dir / "main.tex").write_text("first line\nClaim source text.\nthird line\n", encoding="utf-8")
            self.write_claims(paper_id, [self.claim(paper_id, index)])

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_pool_and_manifest(self, digest: str | None = None) -> None:
        pool_path = self.root / "data/candidate_pool.jsonl"
        pool_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in self.pool),
            encoding="utf-8",
        )
        actual_digest = "sha256:" + hashlib.sha256(pool_path.read_bytes()).hexdigest()
        selected = [
            {
                "arxiv_id": paper_id,
                "sample_index": index,
                "versioned_id": f"{paper_id}v1",
            }
            for index, paper_id in enumerate(self.paper_ids, 1)
        ]
        manifest = {
            "candidate_pool_sha256": digest or actual_digest,
            "pool_size": len(self.pool),
            "selected": selected,
        }
        (self.root / "data/sample_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    @staticmethod
    def claim(paper_id: str, index: int, status: str = "EXTRACTED") -> dict:
        return {
            "candidate_id": f"candidate:arxiv:{paper_id}:claim-{index}",
            "paper_id": f"arxiv:{paper_id}v1",
            "statement": "A source-grounded statement.",
            "source_spans": [
                {
                    "source_file": "main.tex",
                    "line_start": 2,
                    "line_end": 2,
                    "exact_text": "Claim source text.\n",
                }
            ],
            "atomicity": {"single_primary_predication": True, "split_note": ""},
            "scope": {"conditions": [], "quantifiers": [], "population_or_system": "test system"},
            "modality": "ASSERTED",
            "knowledge_attribution": "CURRENT_WORK",
            "math_normalization": {"suitability": "PARTIAL", "reason": "Mixed prose and mathematics."},
            "interface_pressure": ["source-context"],
            "review_status": status,
        }

    def write_claims(self, paper_id: str, claims: list[dict]) -> None:
        path = self.root / "data" / f"claims-{paper_id}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in claims), encoding="utf-8")

    def validate(self, *, source: bool = False, final: bool = False) -> validator.ValidationResult:
        return validator.validate_study(self.root, self.source_root if source else None, final)

    def test_valid_fixture_reports_summary_and_explicit_source_skip(self) -> None:
        result = self.validate()
        self.assertEqual(result.errors, [])
        self.assertEqual(result.source_verification, "skipped")
        self.assertEqual(result.summary["total_claims"], 2)
        self.assertEqual(result.summary["by_modality"], {"ASSERTED": 2})
        self.assertEqual(result.summary["by_mathclaimir_suitability"], {"PARTIAL": 2})

    def test_manifest_digest_mismatch_is_rejected(self) -> None:
        self.write_pool_and_manifest("sha256:" + "0" * 64)
        self.assertTrue(any("digest does not match" in error for error in self.validate().errors))

    def test_duplicate_candidate_ids_are_rejected_globally(self) -> None:
        duplicate = self.claim(self.paper_ids[1], 2)
        duplicate["candidate_id"] = self.claim(self.paper_ids[0], 1)["candidate_id"]
        self.write_claims(self.paper_ids[1], [duplicate])
        self.assertTrue(any("duplicate candidate_id" in error for error in self.validate().errors))

    def test_duplicate_candidate_pool_ids_are_rejected(self) -> None:
        self.pool.append(copy.deepcopy(self.pool[0]))
        self.write_pool_and_manifest()
        self.assertTrue(any("candidate pool contains duplicate IDs" in error for error in self.validate().errors))

    def test_malformed_source_span_is_rejected_without_source_tree(self) -> None:
        claim = self.claim(self.paper_ids[0], 1)
        claim["source_spans"][0]["line_start"] = 3
        claim["source_spans"][0]["line_end"] = 2
        self.write_claims(self.paper_ids[0], [claim])
        errors = self.validate().errors
        self.assertTrue(any("malformed 1-indexed source span" in error for error in errors))

    def test_exact_text_mismatch_is_rejected_with_source_tree(self) -> None:
        claim = self.claim(self.paper_ids[0], 1)
        claim["source_spans"][0]["exact_text"] = "Drifted text."
        self.write_claims(self.paper_ids[0], [claim])
        result = self.validate(source=True)
        self.assertEqual(result.source_verification, "performed")
        self.assertTrue(any("exact_text mismatch" in error for error in result.errors))

    def test_source_verification_preserves_crlf_bytes(self) -> None:
        paper_id = self.paper_ids[0]
        (self.source_root / paper_id / "main.tex").write_bytes(
            b"first line\r\nClaim source text.\r\nthird line\r\n"
        )
        claim = self.claim(paper_id, 1)
        claim["source_spans"][0]["exact_text"] = "Claim source text.\r\n"
        self.write_claims(paper_id, [claim])
        self.assertEqual(self.validate(source=True).errors, [])

    def test_unknown_paper_is_rejected(self) -> None:
        unknown = self.claim("2608.99999", 3)
        (self.root / "data/claims-2608.99999.jsonl").write_text(json.dumps(unknown) + "\n", encoding="utf-8")
        errors = self.validate().errors
        self.assertTrue(any("unknown claim file" in error for error in errors))
        self.assertTrue(any("unknown paper" in error for error in errors))

    def test_missing_case_is_rejected(self) -> None:
        (self.root / "cases/case-2608.00002.tex").unlink()
        self.assertTrue(any("missing case file" in error for error in self.validate().errors))

    def test_final_readiness_requires_reviewed_claims_and_sections(self) -> None:
        errors = self.validate(final=True).errors
        self.assertTrue(any("not SOURCE_CHECKED/REVISED" in error for error in errors))
        self.assertTrue(any("required final specification section is missing" in error for error in errors))

        for relative in validator.REQUIRED_FINAL_SECTIONS:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("final\n", encoding="utf-8")
        for index, paper_id in enumerate(self.paper_ids, 1):
            self.write_claims(paper_id, [self.claim(paper_id, index, "SOURCE_CHECKED")])
        self.assertEqual(self.validate(source=True, final=True).errors, [])


if __name__ == "__main__":
    unittest.main()
