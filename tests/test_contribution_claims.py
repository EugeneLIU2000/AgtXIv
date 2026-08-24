from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.validate_contribution_claims as validator


class ContributionClaimValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.claims = validator.load_jsonl(validator.CLAIMS)
        cls.calibrations = validator.load_jsonl(validator.CALIBRATIONS)
        cls.support = validator.load_jsonl(validator.SUPPORT)

    def validate(self, claims=None, calibrations=None, support=None) -> list[str]:
        return validator.validate_records(
            copy.deepcopy(self.claims if claims is None else claims),
            copy.deepcopy(self.calibrations if calibrations is None else calibrations),
            copy.deepcopy(self.support if support is None else support),
        )

    @staticmethod
    def rehash_claim(claim: dict) -> None:
        claim["semantic_content_hash"] = validator.semantic_hash(claim)
        claim["artifact"]["artifact_hash"] = validator.artifact_hash(claim)
        claim["content_hash"] = validator.record_content_hash(claim)

    @staticmethod
    def rehash_external(record: dict) -> None:
        record["content_hash"] = validator.external_content_hash(record)

    def test_all_fixtures_sources_hashes_references_manifests_and_dag_inputs_validate(self) -> None:
        self.assertEqual(self.validate(), [])

    def test_unicode_equivalent_strings_have_identical_hashes(self) -> None:
        self.assertEqual(validator.hash_value({"text": "é"}), validator.hash_value({"text": "e\u0301"}))
        self.assertEqual(validator.hash_value({"text": "a\r\nb\rc"}), validator.hash_value({"text": "a\nb\nc"}))

    def test_set_order_does_not_change_semantic_hash(self) -> None:
        claim = copy.deepcopy(self.claims[0])
        expected = validator.semantic_hash(claim)
        claim["scope_hints"].reverse()
        claim["contribution_tags"].reverse()
        self.assertEqual(validator.semantic_hash(claim), expected)

    def test_canonical_duplicate_set_member_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "canonical duplicate"):
            validator.canonicalize(["é", "e\u0301"], "scope_hints")

    def test_semantic_hash_excludes_occurrences_revision_and_artifact_metadata(self) -> None:
        claim = copy.deepcopy(self.claims[0])
        old_semantic = validator.semantic_hash(claim)
        old_artifact = validator.artifact_hash(claim)
        claim["record_revision"] += 1
        claim["occurrences"][0]["source_text"] += " changed provenance"
        self.assertEqual(validator.semantic_hash(claim), old_semantic)
        self.assertNotEqual(validator.artifact_hash(claim), old_artifact)

    def test_artifact_and_record_content_hashes_detect_metadata_changes(self) -> None:
        claim = copy.deepcopy(self.claims[0])
        old_artifact = validator.artifact_hash(claim)
        old_content = validator.record_content_hash(claim)
        claim["produced_at"] = "2026-08-25T00:00:00Z"
        self.assertNotEqual(validator.artifact_hash(claim), old_artifact)
        claim["artifact"]["artifact_hash"] = validator.artifact_hash(claim)
        self.assertNotEqual(validator.record_content_hash(claim), old_content)

    def test_revision_chain_requires_exact_immutable_supersedes_targetref(self) -> None:
        first = copy.deepcopy(self.claims[0])
        second = copy.deepcopy(first)
        second["record_revision"] = 2
        second["supersedes"] = validator.immutable_record_ref(first, "org.agtxiv.scientific_claim.contribution")
        self.rehash_claim(second)
        self.assertEqual(validator.validate_supersedes([first, second], "org.agtxiv.scientific_claim.contribution"), [])
        second["supersedes"]["target_artifact"]["artifact_hash"] = "sha256:" + "0" * 64
        self.assertTrue(any("exact previous immutable TargetRef" in error for error in validator.validate_supersedes([first, second], "org.agtxiv.scientific_claim.contribution")))

    def test_full_validator_accepts_two_append_only_generations(self) -> None:
        claims = copy.deepcopy(self.claims)
        first_claim = claims[0]
        second_claim = copy.deepcopy(first_claim)
        second_claim["record_revision"] = 2
        second_claim["supersedes"] = validator.immutable_record_ref(first_claim, "org.agtxiv.scientific_claim.contribution")
        second_claim["scope_hints"].append("append-only revision test scope")
        second_claim["scope_hints"] = validator.canonicalize(second_claim["scope_hints"], "scope_hints")
        for occurrence in second_claim["occurrences"]:
            occurrence["id"] += ":revision-2"
        self.rehash_claim(second_claim)
        claims.append(second_claim)

        calibrations = copy.deepcopy(self.calibrations)
        first_calibration = calibrations[0]
        second_calibration = copy.deepcopy(first_calibration)
        second_calibration["record_revision"] = 2
        second_calibration["supersedes"] = validator.immutable_record_ref(first_calibration, "org.agtxiv.contribution_calibration")
        second_calibration["contribution_ref"] = validator.contribution_target_ref(second_claim)
        self.rehash_external(second_calibration)
        calibrations.append(second_calibration)

        support = copy.deepcopy(self.support)
        first_support = support[0]
        second_support = copy.deepcopy(first_support)
        second_support["record_revision"] = 2
        second_support["supersedes"] = validator.immutable_record_ref(first_support, "org.agtxiv.claim_support_association")
        second_support["contribution_ref"] = validator.contribution_target_ref(second_claim)
        second_support["navigation_basis_ref"] = validator.contribution_target_ref(second_claim, "/facets", artifact=False)
        self.rehash_external(second_support)
        support.append(second_support)

        self.assertEqual(validator.validate_registry_records(claims, calibrations, support), [])

    def test_exactly_one_primary_and_registry_global_occurrence_ids_are_required(self) -> None:
        claims = copy.deepcopy(self.claims)
        claims[0]["occurrences"][1]["occurrence_role"] = "PRIMARY"
        claims[1]["occurrences"][0] = copy.deepcopy(claims[0]["occurrences"][0])
        self.rehash_claim(claims[0])
        self.rehash_claim(claims[1])
        errors = self.validate(claims=claims)
        self.assertTrue(any("exactly one PRIMARY" in error for error in errors))
        self.assertTrue(any("duplicate occurrence ID" in error for error in errors))

    def test_association_revision_must_match_the_claim_revision(self) -> None:
        calibrations = copy.deepcopy(self.calibrations)
        calibrations[0]["record_revision"] = 2
        self.rehash_external(calibrations[0])
        errors = validator.validate_registry_records(self.claims, calibrations, self.support)
        self.assertTrue(any("record revision must equal its ContributionClaim target revision" in error for error in errors))

    def test_association_revision_cannot_switch_claim_identity(self) -> None:
        cases = (
            (self.calibrations, "org.agtxiv.contribution_calibration", "calibration"),
            (self.support, "org.agtxiv.claim_support_association", "support"),
        )
        for fixtures, target_kind, label in cases:
            with self.subTest(label=label):
                first = copy.deepcopy(fixtures[0])
                switched = copy.deepcopy(first)
                switched["record_revision"] = 2
                switched["supersedes"] = validator.immutable_record_ref(first, target_kind)
                switched["contribution_ref"] = copy.deepcopy(fixtures[1]["contribution_ref"])
                switched["contribution_ref"]["target_revision"] = 2
                self.rehash_external(switched)
                self.assertEqual(validator.validate_supersedes([first, switched], target_kind), [])
                errors = validator.validate_association_identity([first, switched], label)
                self.assertTrue(any("cannot switch ContributionClaim identity" in error for error in errors))

    def test_embedded_verification_or_support_is_rejected(self) -> None:
        claims = copy.deepcopy(self.claims)
        claims[0]["verification_status"] = "VERIFIED"
        self.assertTrue(any("embedded lifecycle/evidence/support" in error for error in self.validate(claims=claims)))

    def test_missing_perfect_graph_hypothesis_is_rejected(self) -> None:
        claims = copy.deepcopy(self.claims)
        claim = next(row for row in claims if row["id"].endswith("2607-perfect-graph-closed-form"))
        claim["scope_hints"] = [hint for hint in claim["scope_hints"] if "perfect frustration graph" not in hint]
        self.rehash_claim(claim)
        self.assertTrue(any("both no-active-dependency and perfect-graph hypotheses" in error for error in self.validate(claims=claims)))

    def test_np_complete_overstatement_is_rejected(self) -> None:
        claims = copy.deepcopy(self.claims)
        claim = next(row for row in claims if row["id"].endswith("2602-rsmp-np-hardness"))
        claim["normalized_statement"] = claim["normalized_statement"].replace("NP-hard", "NP-complete")
        self.rehash_claim(claim)
        self.assertTrue(any("must state NP-hard, not NP-complete" in error for error in self.validate(claims=claims)))

    def test_facet_coverage_cannot_be_promoted_without_complete_facets(self) -> None:
        support = copy.deepcopy(self.support)
        record = next(row for row in support if row["id"].endswith("2602-vrep-algorithm-runtime"))
        record["provisional_facet_coverage"] = "COMPLETE"
        self.rehash_external(record)
        self.assertTrue(any("does not aggregate from all facets" in error or "does not permit COMPLETE" in error for error in self.validate(support=support)))

    def test_combined_rom_claim_maps_definition_monotonicity_estimator_and_bound_facets(self) -> None:
        claim = next(row for row in self.claims if row["id"].endswith("1609-rom-monotone-estimator"))
        self.assertEqual(
            {facet["facet_id"] for facet in claim["facets"]},
            {"facet:rom-definition", "facet:rom-monotonicity", "facet:gk-estimator", "facet:quadratic-sample-bound"},
        )
        support = next(row for row in self.support if row["id"].endswith("1609-rom-monotone-estimator"))
        outcomes = {item["facet_id"]: item["coverage"] for item in support["facet_outcomes"]}
        self.assertEqual(outcomes["facet:rom-definition"], "COMPLETE")
        self.assertEqual(outcomes["facet:rom-monotonicity"], "COMPLETE")
        self.assertEqual(outcomes["facet:gk-estimator"], "NONE")
        self.assertEqual(outcomes["facet:quadratic-sample-bound"], "NONE")

    def test_body_enriched_primary_calibrations_use_partial_overlap(self) -> None:
        expected = {
            "contribution-calibration:2602-vrep-algorithm-runtime",
            "contribution-calibration:2602-rsmp-np-hardness",
            "contribution-calibration:1307-wigner-sum-negativity",
            "contribution-calibration:1609-rom-monotone-estimator",
        }
        actual = {
            record["id"]
            for record in self.calibrations
            if record["primary_to_normalized_relation"] == "PARTIAL_OVERLAP"
        }
        self.assertTrue(expected <= actual)
        self.assertTrue(all(record["relation_direction"] == "SOURCE_RELATIVE_TO_NORMALIZED_CLAIM" for record in self.calibrations))
        by_id = {record["id"]: record for record in self.calibrations}
        self.assertEqual(by_id["contribution-calibration:2607-sign-relaxation-exactness"]["primary_to_normalized_relation"], "BROADER_THAN")
        for calibration_id in (
            "contribution-calibration:1307-wigner-sum-negativity",
            "contribution-calibration:1609-rom-monotone-estimator",
        ):
            self.assertEqual(by_id[calibration_id]["body_to_normalized_relation"], "PARTIAL_OVERLAP")

    def test_thesis_mathclaimir_links_are_topical_and_coverage_none(self) -> None:
        record = next(row for row in self.support if row["id"].endswith("9705052-thesis-overview"))
        self.assertEqual(record["provisional_facet_coverage"], "NONE")
        self.assertTrue(all(link["relationship"] == "TOPICAL_NAVIGATION_ONLY" and link["facet_coverage"] == "NONE" for link in record["links"]))

    def test_mathclaimir_coexistence_does_not_create_or_promote_contribution(self) -> None:
        math_claim = validator.load_jsonl(validator.ROOT / "Stabilizerness/MathClaimIRRegistry/claims/stabilizer-codes-and-quantum-error-correction.jsonl")[0]
        self.assertFalse(validator.is_contribution_record(math_claim))
        self.assertNotEqual(math_claim["id"], "claim:contribution:9705052-thesis-overview")

    def test_contribution_claim_is_recursively_rejected_from_math_dependency_dag(self) -> None:
        target_ref = {
            "target_kind": "org.agtxiv.scientific_claim.contribution",
            "target_id": "claim:contribution:test",
        }
        payloads = (
            {"nodes": ["math-claim-ir:test:ok", "claim:contribution:test"]},
            {"nodes": [{"id": "claim:contribution:test"}]},
            {"nodes": {"contribution": {"claim": {"id": "claim:contribution:test"}}}},
            {"nodes": [target_ref]},
            {"nodes": [{"id": "statement:test:valid", "target_ref": target_ref}]},
            {"nodes": [{"target_kind": "org.agtxiv.claim_ir", "target_id": "math-claim-ir:test:valid", "claim": target_ref}]},
            {"edges": [{"source": {"claim": target_ref}, "target": {"id": "math-claim-ir:test:ok"}}]},
            {"edges": [{"from": {"claim": {"id": "claim:contribution:test"}}, "to": "math-claim-ir:test:ok"}]},
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                errors = validator.validate_dependency_payload(payload)
                self.assertTrue(any("cannot be a MathClaimDependencyDAG node" in error for error in errors))

    def test_math_dependency_dag_accepts_only_permitted_target_kinds_and_id_families(self) -> None:
        claim_ir_ref = {"target_kind": "org.agtxiv.claim_ir", "target_id": "math-claim-ir:test:one"}
        proposition_ref = {
            "target_kind": "org.agtxiv.mathematical_proposition_ir",
            "target_id": "math-proposition-ir:test:two",
        }
        permitted = {
            "nodes": {
                "legacy": ["assumption:test:legacy", {"id": "statement:test:legacy", "label": "Lemma", "color": "blue"}],
                "canonical": [claim_ir_ref, proposition_ref],
            },
            "edges": [{"source": {"claim": claim_ir_ref, "label": "premise"}, "target": proposition_ref}],
        }
        self.assertEqual(validator.validate_dependency_payload(permitted), [])

        invalid = (
            {"nodes": ["claim:scientific:not-a-mathematical-node"]},
            {"nodes": [{"target_kind": "org.agtxiv.claim_ir", "target_id": "math-proposition-ir:wrong-family"}]},
            {"edges": [{"from": {"target_kind": "org.example.unknown", "target_id": "math-claim-ir:test"}, "to": "statement:test"}]},
        )
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assertTrue(validator.validate_dependency_payload(payload))

    def test_thesis_cannot_be_promoted_to_result_or_proof_speech_act(self) -> None:
        claims = copy.deepcopy(self.claims)
        claim = next(row for row in claims if row["id"].endswith("9705052-thesis-overview"))
        claim["contribution_kind"] = "org.agtxiv.contribution.result"
        claim["source_characterization"]["speech_act"] = "org.agtxiv.speech_act.proves"
        self.rehash_claim(claim)
        self.assertTrue(any("cannot be promoted to a theorem contribution" in error for error in self.validate(claims=claims)))

    def test_source_fidelity_detects_text_drift(self) -> None:
        claims = copy.deepcopy(self.claims)
        claims[0]["occurrences"][0]["source_text"] += " drift"
        self.rehash_claim(claims[0])
        self.assertTrue(any("source text mismatch" in error for error in self.validate(claims=claims)))


if __name__ == "__main__":
    unittest.main()
