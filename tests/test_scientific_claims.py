from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools.validate_scientific_claims as validator


class ScientificClaimValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.claims = validator.load_jsonl(validator.CLAIMS)
        cls.calibrations = validator.load_jsonl(validator.CALIBRATIONS)
        cls.support = validator.load_jsonl(validator.SUPPORT)
        cls.bridges = validator.load_jsonl(validator.BRIDGES)
        cls.bridge_assessments = validator.load_jsonl(validator.BRIDGE_ASSESSMENTS)

    def validate(self, claims=None, calibrations=None, support=None) -> list[str]:
        return validator.validate_records(
            copy.deepcopy(self.claims if claims is None else claims),
            copy.deepcopy(self.calibrations if calibrations is None else calibrations),
            copy.deepcopy(self.support if support is None else support),
        )

    def validate_bridge(self, bridges=None, assessments=None) -> list[str]:
        return validator.validate_bridge_records(
            copy.deepcopy(self.bridges if bridges is None else bridges),
            copy.deepcopy(self.bridge_assessments if assessments is None else assessments),
        )

    @staticmethod
    def rehash_bridge_pair(bridge: dict, assessment: dict) -> None:
        bridge["content_hash"] = validator.external_content_hash(bridge)
        assessment["bridge_ref"]["target_content_hash"] = bridge["content_hash"]
        assessment["content_hash"] = validator.external_content_hash(assessment)

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

    def test_unified_schema_validates_formal_v1_and_contribution_role_records(self) -> None:
        manifest = json.loads((validator.ROOT / "Stabilizerness/ScientificClaimRegistry/manifest.json").read_text())
        records = [
            row
            for relative in manifest["claim_files"]
            for row in validator.load_jsonl(validator.ROOT / relative)
        ]
        formal = [row for row in records if row["schema"] == "agtxiv.scientific-claim/1.0.0"]
        narrative = [row for row in records if row["schema"] == "agtxiv.scientific-claim/1.1.0"]
        self.assertEqual(len(formal), 43)
        self.assertEqual(len(narrative), 7)
        self.assertTrue(all(row.get("claim_role") == "CONTRIBUTION" for row in narrative))
        self.assertEqual(validator.validate_all_scientific_claims(validator.ROOT), [])

    def test_generic_manifest_discovers_role_records_without_parallel_claim_type(self) -> None:
        registry = validator.ROOT / "Stabilizerness/ScientificClaimRegistry"
        manifest = json.loads((registry / "manifest.json").read_text())
        relative = str(validator.CLAIMS.relative_to(validator.ROOT))
        self.assertIn(relative, manifest["claim_files"])
        self.assertIn(relative, manifest["object_files"])
        self.assertNotIn("contribution_claim_files", manifest)
        self.assertEqual(manifest["schema_files"], ["Stabilizerness/ScientificClaimRegistry/schema/scientific-claim.schema.json"])
        obsolete_schema = registry / "schema" / ("contribution" + "-claim.schema.json")
        self.assertFalse(obsolete_schema.exists())
        self.assertFalse((registry / "contributions").exists())
        self.assertTrue(all(row["id"].startswith("claim:") and not row["id"].startswith("claim:" + "contribution:") for row in self.claims))
        self.assertTrue(all(row["scientific_claim_ref"]["target_kind"] == "org.agtxiv.scientific_claim" for row in self.calibrations + self.support))

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
        second["supersedes"] = validator.immutable_record_ref(first, "org.agtxiv.scientific_claim")
        self.rehash_claim(second)
        self.assertEqual(validator.validate_supersedes([first, second], "org.agtxiv.scientific_claim"), [])
        second["supersedes"]["target_artifact"]["artifact_hash"] = "sha256:" + "0" * 64
        self.assertTrue(any("exact previous immutable TargetRef" in error for error in validator.validate_supersedes([first, second], "org.agtxiv.scientific_claim")))

    def test_full_validator_accepts_two_append_only_generations(self) -> None:
        claims = copy.deepcopy(self.claims)
        first_claim = claims[0]
        second_claim = copy.deepcopy(first_claim)
        second_claim["record_revision"] = 2
        second_claim["supersedes"] = validator.immutable_record_ref(first_claim, "org.agtxiv.scientific_claim")
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
        second_calibration["supersedes"] = validator.immutable_record_ref(first_calibration, "org.agtxiv.scientific_claim_calibration")
        second_calibration["scientific_claim_ref"] = validator.scientific_claim_target_ref(second_claim)
        self.rehash_external(second_calibration)
        calibrations.append(second_calibration)

        support = copy.deepcopy(self.support)
        first_support = support[0]
        second_support = copy.deepcopy(first_support)
        second_support["record_revision"] = 2
        second_support["supersedes"] = validator.immutable_record_ref(first_support, "org.agtxiv.claim_support_association")
        second_support["scientific_claim_ref"] = validator.scientific_claim_target_ref(second_claim)
        second_support["navigation_basis_ref"] = validator.scientific_claim_target_ref(second_claim, "/facets", artifact=False)
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
        self.assertTrue(any("record revision must equal its contribution-role ScientificClaim target revision" in error for error in errors))

    def test_association_revision_cannot_switch_claim_identity(self) -> None:
        cases = (
            (self.calibrations, "org.agtxiv.scientific_claim_calibration", "calibration"),
            (self.support, "org.agtxiv.claim_support_association", "support"),
        )
        for fixtures, target_kind, label in cases:
            with self.subTest(label=label):
                first = copy.deepcopy(fixtures[0])
                switched = copy.deepcopy(first)
                switched["record_revision"] = 2
                switched["supersedes"] = validator.immutable_record_ref(first, target_kind)
                switched["scientific_claim_ref"] = copy.deepcopy(fixtures[1]["scientific_claim_ref"])
                switched["scientific_claim_ref"]["target_revision"] = 2
                self.rehash_external(switched)
                self.assertEqual(validator.validate_supersedes([first, switched], target_kind), [])
                errors = validator.validate_association_identity([first, switched], label)
                self.assertTrue(any("cannot switch contribution-role ScientificClaim identity" in error for error in errors))

    def test_embedded_verification_or_support_is_rejected(self) -> None:
        claims = copy.deepcopy(self.claims)
        claims[0]["verification_status"] = "VERIFIED"
        self.assertTrue(any("embedded lifecycle/evidence/support" in error for error in self.validate(claims=claims)))

    def test_missing_perfect_graph_hypothesis_is_rejected(self) -> None:
        claims = copy.deepcopy(self.claims)
        claim = next(row for row in claims if row["id"].endswith(":perfect-graph-closed-form"))
        claim["scope_hints"] = [hint for hint in claim["scope_hints"] if "perfect frustration graph" not in hint]
        self.rehash_claim(claim)
        self.assertTrue(any("both no-active-dependency and perfect-graph hypotheses" in error for error in self.validate(claims=claims)))

    def test_np_complete_overstatement_is_rejected(self) -> None:
        claims = copy.deepcopy(self.claims)
        claim = next(row for row in claims if row["id"].endswith(":reduced-stabilizer-membership-np-hardness"))
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
        claim = next(row for row in self.claims if row["id"].endswith(":rom-monotone-estimator"))
        self.assertEqual(
            {facet["facet_id"] for facet in claim["facets"]},
            {"facet:rom-definition", "facet:rom-monotonicity", "facet:gk-estimator", "facet:quadratic-sample-bound"},
        )
        support = next(row for row in self.support if row["scientific_claim_ref"]["target_id"].endswith(":rom-monotone-estimator"))
        outcomes = {item["facet_id"]: item["coverage"] for item in support["facet_outcomes"]}
        self.assertEqual(outcomes["facet:rom-definition"], "COMPLETE")
        self.assertEqual(outcomes["facet:rom-monotonicity"], "COMPLETE")
        self.assertEqual(outcomes["facet:gk-estimator"], "NONE")
        self.assertEqual(outcomes["facet:quadratic-sample-bound"], "NONE")

    def test_body_enriched_primary_calibrations_use_partial_overlap(self) -> None:
        expected = {
            "scientific-claim-calibration:2602-vrep-algorithm-runtime",
            "scientific-claim-calibration:2602-rsmp-np-hardness",
            "scientific-claim-calibration:1307-wigner-sum-negativity",
            "scientific-claim-calibration:1609-rom-monotone-estimator",
        }
        actual = {
            record["id"]
            for record in self.calibrations
            if record["primary_to_normalized_relation"] == "PARTIAL_OVERLAP"
        }
        self.assertTrue(expected <= actual)
        self.assertTrue(all(record["relation_direction"] == "SOURCE_RELATIVE_TO_NORMALIZED_CLAIM" for record in self.calibrations))
        by_id = {record["id"]: record for record in self.calibrations}
        self.assertEqual(by_id["scientific-claim-calibration:2607-sign-relaxation-exactness"]["primary_to_normalized_relation"], "BROADER_THAN")
        for calibration_id in (
            "scientific-claim-calibration:1307-wigner-sum-negativity",
            "scientific-claim-calibration:1609-rom-monotone-estimator",
        ):
            self.assertEqual(by_id[calibration_id]["body_to_normalized_relation"], "PARTIAL_OVERLAP")

    def test_thesis_mathclaimir_links_are_topical_and_coverage_none(self) -> None:
        record = next(row for row in self.support if row["scientific_claim_ref"]["target_id"].endswith(":thesis-overview"))
        self.assertEqual(record["provisional_facet_coverage"], "NONE")
        self.assertTrue(all(link["relationship"] == "TOPICAL_NAVIGATION_ONLY" and link["facet_coverage"] == "NONE" for link in record["links"]))

    def test_mathclaimir_coexistence_does_not_create_or_promote_contribution(self) -> None:
        math_claim = validator.load_jsonl(validator.ROOT / "Stabilizerness/MathClaimIRRegistry/claims/stabilizer-codes-and-quantum-error-correction.jsonl")[0]
        self.assertFalse(validator.is_contribution_role_record(math_claim))
        self.assertNotEqual(math_claim["id"], "claim:stabilizer-codes-and-quantum-error-correction:thesis-overview")

    def test_scientific_claim_is_recursively_rejected_from_math_dependency_dag(self) -> None:
        target_ref = {
            "target_kind": "org.agtxiv.scientific_claim",
            "target_id": "claim:test-paper:narrative-claim",
        }
        payloads = (
            {"nodes": ["math-claim-ir:test:ok", "claim:test-paper:narrative-claim"]},
            {"nodes": [{"id": "claim:test-paper:narrative-claim"}]},
            {"nodes": {"contribution": {"claim": {"id": "claim:test-paper:narrative-claim"}}}},
            {"nodes": [target_ref]},
            {"nodes": [{"id": "statement:test:valid", "target_ref": target_ref}]},
            {"nodes": [{"target_kind": "org.agtxiv.claim_ir", "target_id": "math-claim-ir:test:valid", "claim": target_ref}]},
            {"edges": [{"source": {"claim": target_ref}, "target": {"id": "math-claim-ir:test:ok"}}]},
            {"edges": [{"from": {"claim": {"id": "claim:test-paper:narrative-claim"}}, "to": "math-claim-ir:test:ok"}]},
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
        claim = next(row for row in claims if row["id"].endswith(":thesis-overview"))
        claim["contribution_kind"] = "org.agtxiv.contribution.result"
        claim["source_characterization"]["speech_act"] = "org.agtxiv.speech_act.proves"
        self.rehash_claim(claim)
        self.assertTrue(any("cannot be promoted to a theorem contribution" in error for error in self.validate(claims=claims)))

    def test_v1_bridge_fixture_pins_bounded_fixed_window_counterexample(self) -> None:
        self.assertEqual(self.validate_bridge(), [])
        bridge = self.bridges[0]
        assessment = self.bridge_assessments[0]
        self.assertEqual(bridge["scientific_claim_ref"]["target_id"], "claim:2602.18939v1:fixed-window-monotonicity-claimed")
        self.assertEqual(bridge["source_anchors"], [
            "anchor:2602.18939v1:fixed-window-monotonicity-claim",
            "anchor:2602.18939v1:fixed-window-monotonicity-proof",
        ])
        self.assertEqual(assessment["root_agent_conclusion"]["outcome"], "REFUTED")
        self.assertEqual(assessment["assumption_object_match"]["status"], "MATCHED")
        self.assertEqual(assessment["residual_semantics_review"]["status"], "PRESERVED")
        outcomes = {row["source_component_id"]: row for row in assessment["component_outcomes"]}
        self.assertEqual(outcomes["component:fixed-window-conclusion"]["assessment_kind"], "MATHEMATICAL_DISPOSITION")
        self.assertEqual(outcomes["component:fixed-window-conclusion"]["status"], "REFUTED")
        self.assertEqual(outcomes["component:fixed-measurement-window"]["assessment_kind"], "APPLICABILITY_MATCH")
        self.assertEqual(outcomes["component:fixed-measurement-window"]["status"], "MATCHED")
        self.assertEqual(outcomes["component:finite-shot-and-noise"]["assessment_kind"], "RESIDUAL_REVIEW")
        self.assertEqual(outcomes["component:finite-shot-and-noise"]["status"], "PRESERVED")
        self.assertEqual(outcomes["component:measurement-window-covariance"]["status"], "PRESERVED")
        components = {row["component_id"]: row for row in bridge["source_components"]}
        self.assertEqual(
            {row["target_ref"]["component_path"] for row in components["component:deterministic-stabilizer-operation"]["mapped_targets"]},
            {"/structured_statement/assumptions/explicit/0", "/structured_statement/assumptions/explicit/1"},
        )
        self.assertFalse(any(row["role"] == "DEPENDENCY" for component in components.values() for row in component["mapped_targets"]))
        non_implications = " ".join(assessment["root_agent_conclusion"]["non_implications"])
        self.assertIn("finite-shot performance", non_implications)
        self.assertIn("noise robustness", non_implications)
        self.assertIn("confidence bounds", non_implications)
        self.assertIn("experimental acceptance threshold", non_implications)
        self.assertEqual(assessment["scientific_acceptance"], "NOT_REVIEWED")

    def test_bridge_assessment_axes_preserve_unknown_and_blocked(self) -> None:
        schema = json.loads((validator.ROOT / "Stabilizerness/ExternalRecordRegistry/schema/bridge-assessment.schema.json").read_text())
        self.assertTrue({"UNKNOWN", "BLOCKED"} <= set(schema["properties"]["evidence_completeness"]["enum"]))
        self.assertTrue({"UNKNOWN", "BLOCKED"} <= set(schema["properties"]["scientific_acceptance"]["enum"]))

    def test_bridge_rejects_embedded_acceptance_verification_and_coverage_status(self) -> None:
        for field, value in (("verification_status", "VERIFIED"), ("scientific_acceptance", "ACCEPTED"), ("coverage", "VERIFIED")):
            with self.subTest(field=field):
                bridges = copy.deepcopy(self.bridges)
                bridges[0][field] = value
                self.rehash_external(bridges[0])
                errors = self.validate_bridge(bridges=bridges)
                self.assertTrue(any("embeds acceptance/verification/contribution/coverage" in error for error in errors))

    def test_assessment_rejects_navigation_coverage_as_mathematical_status(self) -> None:
        assessments = copy.deepcopy(self.bridge_assessments)
        assessments[0]["coverage"] = "VERIFIED"
        self.rehash_external(assessments[0])
        self.assertTrue(any("navigation coverage cannot be used as mathematical status" in error for error in self.validate_bridge(assessments=assessments)))

    def test_bridge_requires_every_source_component_to_be_mapped_or_residual(self) -> None:
        bridges = copy.deepcopy(self.bridges)
        component = bridges[0]["source_components"][0]
        component["mapped_targets"] = []
        self.rehash_external(bridges[0])
        self.assertTrue(any("neither mapped nor residual" in error for error in self.validate_bridge(bridges=bridges)))

    def test_bridge_rejects_unknown_and_inexact_references(self) -> None:
        bridges = copy.deepcopy(self.bridges)
        bridges[0]["source_components"][0]["mapped_targets"][0]["target_ref"]["target_id"] = "math-claim-ir:unknown"
        self.rehash_external(bridges[0])
        self.assertTrue(any("unknown mapped mathematical reference" in error for error in self.validate_bridge(bridges=bridges)))

        assessments = copy.deepcopy(self.bridge_assessments)
        assessments[0]["evidence_refs"][0]["id"] = "evidence:unknown"
        self.rehash_external(assessments[0])
        self.assertTrue(any("unknown or inexact evidence reference" in error for error in self.validate_bridge(assessments=assessments)))

    def test_mapped_component_paths_must_resolve_after_rehashing(self) -> None:
        cases = (
            ("/structured_statement/not-present", "component_path does not exist"),
            ("/structured_statement/assumptions/explicit/99", "invalid array index"),
        )
        for pointer, expected_error in cases:
            with self.subTest(pointer=pointer):
                bridges = copy.deepcopy(self.bridges)
                assessments = copy.deepcopy(self.bridge_assessments)
                mapped = bridges[0]["source_components"][0]["mapped_targets"][0]
                mapped["target_ref"]["component_path"] = pointer
                self.rehash_bridge_pair(bridges[0], assessments[0])
                errors = self.validate_bridge(bridges=bridges, assessments=assessments)
                self.assertTrue(any(expected_error in error for error in errors))

    def test_mapped_roles_must_match_resolved_components(self) -> None:
        cases = (
            ("component:fixed-window-conclusion", "ASSUMPTION", "ASSUMPTION must resolve"),
            ("component:fixed-measurement-window", "CONCLUSION", "CONCLUSION must resolve"),
            ("component:reduced-rom-definition", "ASSUMPTION", "ASSUMPTION must resolve"),
        )
        for component_id, role, expected_error in cases:
            with self.subTest(component_id=component_id, role=role):
                bridges = copy.deepcopy(self.bridges)
                assessments = copy.deepcopy(self.bridge_assessments)
                component = next(row for row in bridges[0]["source_components"] if row["component_id"] == component_id)
                component["mapped_targets"][0]["role"] = role
                self.rehash_bridge_pair(bridges[0], assessments[0])
                errors = self.validate_bridge(bridges=bridges, assessments=assessments)
                self.assertTrue(any("mapped role mismatch" in error and expected_error in error for error in errors))

    def test_oracle_bridge_cannot_be_marked_scientifically_accepted(self) -> None:
        assessments = copy.deepcopy(self.bridge_assessments)
        assessments[0]["scientific_acceptance"] = "ACCEPTED"
        self.rehash_external(assessments[0])
        self.assertTrue(any("Oracle-generated bridge cannot be treated as scientifically accepted" in error for error in self.validate_bridge(assessments=assessments)))

    def test_bridge_rejects_erased_residual_physical_semantics(self) -> None:
        bridges = copy.deepcopy(self.bridges)
        residual = next(row for row in bridges[0]["source_components"] if row["disposition"] == "RESIDUAL")
        residual["residual_physical_semantics"] = ""
        self.rehash_external(bridges[0])
        self.assertTrue(any("erased residual semantics" in error for error in self.validate_bridge(bridges=bridges)))

    def test_verified_and_refuted_mathematical_dispositions_require_resolvable_bases(self) -> None:
        assessments = copy.deepcopy(self.bridge_assessments)
        disposition = next(row for row in assessments[0]["component_outcomes"] if row["assessment_kind"] == "MATHEMATICAL_DISPOSITION")
        disposition["status"] = "VERIFIED"
        disposition["basis_refs"] = []
        self.rehash_external(assessments[0])
        self.assertTrue(any("VERIFIED/REFUTED mathematical disposition requires an evidence or classification basis" in error for error in self.validate_bridge(assessments=assessments)))

        assessments = copy.deepcopy(self.bridge_assessments)
        refuted = next(row for row in assessments[0]["component_outcomes"] if row["status"] == "REFUTED")
        refuted["basis_refs"] = ["source-claim-classification:2602.18939v1:fixed-window-monotonicity"]
        self.rehash_external(assessments[0])
        self.assertTrue(any("REFUTED mathematical disposition requires evidence" in error for error in self.validate_bridge(assessments=assessments)))

    def test_assessment_rejects_status_projection_without_evidence(self) -> None:
        assessments = copy.deepcopy(self.bridge_assessments)
        assessments[0]["evidence_refs"] = []
        self.rehash_external(assessments[0])
        self.assertTrue(any("status projection has no evidence" in error for error in self.validate_bridge(assessments=assessments)))

    def test_assessment_rejects_full_rom_covariant_or_selective_overreach(self) -> None:
        assessments = copy.deepcopy(self.bridge_assessments)
        assessments[0]["root_agent_conclusion"]["bounded_scope"] = "All robustness of magic monotonicity is false."
        assessments[0]["root_agent_conclusion"]["non_implications"] = ["No exceptions remain."]
        self.rehash_external(assessments[0])
        self.assertTrue(any("full-RoM, covariant-window, selective-operation, or finite-shot/noise overreach" in error for error in self.validate_bridge(assessments=assessments)))

    def test_assessment_requires_finite_shot_noise_non_implication(self) -> None:
        assessments = copy.deepcopy(self.bridge_assessments)
        assessments[0]["root_agent_conclusion"]["non_implications"] = [
            statement for statement in assessments[0]["root_agent_conclusion"]["non_implications"]
            if "finite-shot performance" not in statement
        ]
        self.rehash_external(assessments[0])
        errors = self.validate_bridge(assessments=assessments)
        self.assertTrue(any("finite-shot/noise overreach" in error for error in errors))

    def test_assessment_cannot_replace_refuted_with_verified_or_unknown(self) -> None:
        for replacement in ("VERIFIED", "UNKNOWN"):
            with self.subTest(replacement=replacement):
                assessments = copy.deepcopy(self.bridge_assessments)
                assessments[0]["root_agent_conclusion"]["outcome"] = replacement
                conclusion = next(row for row in assessments[0]["component_outcomes"] if row["source_component_id"] == "component:fixed-window-conclusion")
                conclusion["status"] = replacement
                self.rehash_external(assessments[0])
                self.assertTrue(any("REFUTED mathematical disposition cannot be replaced" in error for error in self.validate_bridge(assessments=assessments)))

    def test_assessment_keeps_evidence_completeness_separate_from_acceptance(self) -> None:
        assessments = copy.deepcopy(self.bridge_assessments)
        assessments[0]["scientific_acceptance"] = assessments[0]["evidence_completeness"]
        self.rehash_external(assessments[0])
        errors = self.validate_bridge(assessments=assessments)
        self.assertTrue(any("evidence completeness is conflated with scientific acceptance" in error for error in errors))

    def test_source_fidelity_detects_text_drift(self) -> None:
        claims = copy.deepcopy(self.claims)
        claims[0]["occurrences"][0]["source_text"] += " drift"
        self.rehash_claim(claims[0])
        self.assertTrue(any("source text mismatch" in error for error in self.validate(claims=claims)))


if __name__ == "__main__":
    unittest.main()
