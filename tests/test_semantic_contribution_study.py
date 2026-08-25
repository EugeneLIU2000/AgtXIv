import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/validate_semantic_contribution_study.py"
SPEC = importlib.util.spec_from_file_location("validate_semantic_contribution_study", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SemanticContributionStudyTests(unittest.TestCase):
    def test_repository_study_validates(self) -> None:
        summary, errors = MODULE.validate(MODULE.DEFAULT_STUDY, MODULE.UPSTREAM_DATA)
        self.assertEqual(errors, [])
        self.assertEqual(summary["decision_count"], 26)
        self.assertEqual(summary["paper_count"], 6)
        self.assertEqual(summary["hidden_claim_units_in_declared_views"], 0)
        self.assertEqual(summary["adjudicator_marked_high_severity_false_prunes"], 0)
        self.assertEqual(summary["independent_audit_blocked_rows"], 0)
        self.assertGreater(summary["occurrence_consolidation"]["reduction"], 0)

    def copied_study(self, directory: str) -> Path:
        target = Path(directory) / "study"
        shutil.copytree(MODULE.DEFAULT_STUDY, target)
        return target

    def read_jsonl(self, root: Path, name: str) -> list[dict]:
        return [json.loads(line) for line in (root / f"data/{name}").read_text(encoding="utf-8").splitlines()]

    def rewrite_jsonl(self, root: Path, name: str, rows: list[dict]) -> None:
        (root / f"data/{name}").write_text(
            "\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n",
            encoding="utf-8",
        )

    def rewrite_rows(self, root: Path, rows: list[dict]) -> None:
        self.rewrite_jsonl(root, "gold-slices.jsonl", rows)

    def rehash(self, row: dict, field: str) -> None:
        row[field] = MODULE.digest({key: value for key, value in row.items() if key != field})

    def test_none_grounding_rejects_math_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = [json.loads(line) for line in (root / "data/gold-slices.jsonl").read_text(encoding="utf-8").splitlines()]
            rows[0]["grounding_coverage"] = "NONE"
            self.rewrite_rows(root, rows)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("NONE grounding" in error for error in errors))

    def test_hide_requires_safe_relation_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = [json.loads(line) for line in (root / "data/gold-slices.jsonl").read_text(encoding="utf-8").splitlines()]
            rows[0]["decision"] = "HIDE_IN_VIEW"
            rows[0]["relation_type"] = "STRICTLY_ENTAILS"
            rows[0]["representative_refs"] = rows[0]["candidate_refs"][:1]
            self.rewrite_rows(root, rows)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("unsafe relation" in error or "incorrect hidden claims" in error for error in errors))

    def test_candidate_snapshot_detects_upstream_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = self.read_jsonl(root, "gold-slices.jsonl")
            rows[0]["candidate_snapshots"][0]["record_sha256"] = "0" * 64
            self.rewrite_rows(root, rows)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("snapshot hash mismatch" in error for error in errors))

    def test_bogus_candidate_relation_endpoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = self.read_jsonl(root, "gold-slices.jsonl")
            rows[1]["source_claim_refs"] = ["candidate:arxiv:2608.20180:does-not-exist"]
            self.rewrite_rows(root, rows)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("source_claim_refs must be candidate_refs" in error for error in errors))

    def test_removed_preserved_envelope_value_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = self.read_jsonl(root, "gold-slices.jsonl")
            receipt = rows[0]["reconstruction_receipt"]
            receipt["preserved_envelope"].pop()
            self.rehash(receipt, "receipt_hash")
            self.rewrite_rows(root, rows)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("preserve the exact residual envelope" in error for error in errors))

    def test_incorrect_profile_aggregate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            profiles = self.read_jsonl(root, "contribution-profiles.jsonl")
            profiles[0]["aggregate_vector"]["new_proofs_or_methods"] += 1
            self.rehash(profiles[0], "record_hash")
            self.rewrite_jsonl(root, "contribution-profiles.jsonl", profiles)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("aggregate vector is not derived" in error for error in errors))

    def test_incompatible_profile_unit_baseline_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            profiles = self.read_jsonl(root, "contribution-profiles.jsonl")
            profiles[0]["baseline_set"] = ["candidate:arxiv:2608.22867:h-theorem-statement"]
            self.rehash(profiles[0], "record_hash")
            self.rewrite_jsonl(root, "contribution-profiles.jsonl", profiles)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("profile baseline is incompatible" in error for error in errors))

    def test_nonexistent_iteration_trigger_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            iterations = self.read_jsonl(root, "iteration-log.jsonl")
            iterations[0]["trigger_refs"].append("gold:does-not-exist")
            self.rehash(iterations[0], "record_hash")
            self.rewrite_jsonl(root, "iteration-log.jsonl", iterations)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("unresolved iteration trigger" in error for error in errors))

    def test_math_endpoint_must_align_with_candidate_component(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            relations = self.read_jsonl(root, "assumed-math-relations.jsonl")
            relation = relations[0]
            relation["source_groundings"][0]["candidate_ref"] = relation["target_candidate_refs"][0]
            relation["source_candidate_refs"] = relation["target_candidate_refs"]
            self.rehash(relation, "relation_hash")
            self.rewrite_jsonl(root, "assumed-math-relations.jsonl", relations)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("materialized source candidate endpoints" in error for error in errors))
            self.assertTrue(any("MathClaim endpoint is not aligned" in error for error in errors))

    def test_moment_contract_requires_internal_iid_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            claims = self.read_jsonl(root, "assumed-mathclaims.jsonl")
            moment = next(row for row in claims if row["math_claim_id"].endswith(":bernoulli-sample-moments"))
            moment["dependencies"] = []
            self.rehash(moment, "contract_hash")
            self.rewrite_jsonl(root, "assumed-mathclaims.jsonl", claims)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("must retain" in error and "iid-bernoulli-premise" in error for error in errors))

    def test_coherent_relation_side_swap_is_rejected_by_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = self.read_jsonl(root, "gold-slices.jsonl")
            gold = next(row for row in rows if row["decision_id"] == "gold:2608.15963:04")
            gold["source_claim_refs"], gold["target_claim_refs"] = gold["target_claim_refs"], gold["source_claim_refs"]
            for comparison in gold["envelope_comparison"]:
                comparison["source_values"], comparison["target_values"] = comparison["target_values"], comparison["source_values"]
            self.rewrite_rows(root, rows)

            relations = self.read_jsonl(root, "assumed-math-relations.jsonl")
            relation = next(row for row in relations if row["relation_id"] == "mathrel:2608.15963:04")
            for suffix in ("math_claim_refs", "candidate_refs", "groundings"):
                source_key, target_key = f"source_{suffix}", f"target_{suffix}"
                relation[source_key], relation[target_key] = relation[target_key], relation[source_key]
            self.rehash(relation, "relation_hash")
            self.rewrite_jsonl(root, "assumed-math-relations.jsonl", relations)

            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("independent adjudication anchor" in error for error in errors))

    def test_coherent_observables_entailment_restoration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = self.read_jsonl(root, "gold-slices.jsonl")
            gold = next(row for row in rows if row["decision_id"] == "gold:2608.02862:03")
            gold["relation_type"] = "STRICTLY_ENTAILS"
            gold["source_claim_refs"], gold["target_claim_refs"] = gold["target_claim_refs"], gold["source_claim_refs"]
            self.rewrite_rows(root, rows)

            relations = self.read_jsonl(root, "assumed-math-relations.jsonl")
            relation = next(row for row in relations if row["relation_id"] == "mathrel:2608.02862:03")
            relation["relation_type"] = "STRICTLY_ENTAILS"
            for suffix in ("math_claim_refs", "candidate_refs", "groundings"):
                source_key, target_key = f"source_{suffix}", f"target_{suffix}"
                relation[source_key], relation[target_key] = relation[target_key], relation[source_key]
            self.rehash(relation, "relation_hash")
            self.rewrite_jsonl(root, "assumed-math-relations.jsonl", relations)

            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("independent adjudication anchor" in error for error in errors))

    def test_coherent_ssb_derivable_exposition_restoration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = self.read_jsonl(root, "gold-slices.jsonl")
            gold = next(row for row in rows if row["decision_id"] == "gold:2608.15963:01")
            gold["relation_type"] = "DERIVABLE_EXPOSITION"
            self.rewrite_rows(root, rows)

            relations = self.read_jsonl(root, "assumed-math-relations.jsonl")
            relation = next(row for row in relations if row["relation_id"] == "mathrel:2608.15963:01")
            relation["relation_type"] = "DERIVABLE_EXPOSITION"
            self.rehash(relation, "relation_hash")
            self.rewrite_jsonl(root, "assumed-math-relations.jsonl", relations)

            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("independent adjudication anchor" in error for error in errors))

    def test_coherent_envelope_deletion_is_rejected_by_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = self.read_jsonl(root, "gold-slices.jsonl")
            gold = rows[0]
            removed = gold["residual_envelope"].pop()
            gold["envelope_comparison"] = [
                item for item in gold["envelope_comparison"] if item["dimension"] != removed["dimension"]
            ]
            receipt = gold["reconstruction_receipt"]
            receipt["preserved_envelope"] = gold["residual_envelope"]
            self.rehash(receipt, "receipt_hash")
            self.rewrite_rows(root, rows)

            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("independent adjudication inventory" in error for error in errors))

    def test_complete_grounding_requires_each_candidate_component(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_study(directory)
            rows = self.read_jsonl(root, "gold-slices.jsonl")
            rows[1]["covered_components"] = rows[1]["covered_components"][:1]
            self.rewrite_rows(root, rows)
            _, errors = MODULE.validate(root, MODULE.UPSTREAM_DATA)
            self.assertTrue(any("COMPLETE means every candidate" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
