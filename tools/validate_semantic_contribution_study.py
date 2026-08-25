#!/usr/bin/env python3
"""Validate the MathClaim-grounded semantic-contribution design study."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STUDY = ROOT / "docs/specifications/mathclaim-semantic-contribution"
UPSTREAM_DATA = ROOT / "docs/specifications/scientific-claim-interface/data"

# Independent adjudication anchors.  These are intentionally not imported from the
# fixture builder, so coordinated edits to generated layers cannot redefine safety.
EXPECTED_RELATION_ADJUDICATIONS = {
    "gold:2608.15963:01": {
        "relation_type": "DEPENDS_ON",
        "source_claim_refs": ["candidate:arxiv:2608.15963:general-ssb-mass"],
        "target_claim_refs": ["candidate:arxiv:2608.15963:ssb-definition"],
    },
    "gold:2608.15963:04": {
        "relation_type": "SPECIALIZES",
        "source_claim_refs": ["candidate:arxiv:2608.15963:uniform-random-ssb"],
        "target_claim_refs": ["candidate:arxiv:2608.15963:depolarizing-ssb"],
    },
    "gold:2608.02862:03": {
        "relation_type": "DEPENDS_ON",
        "source_claim_refs": ["candidate:arxiv:2608.02862:selection-functionals-definition"],
        "target_claim_refs": ["candidate:arxiv:2608.02862:selection-observables-definition"],
    },
}

EXPECTED_RESIDUAL_ENVELOPE_DIGESTS = {
    "gold:2608.20180:01": "083533639d62734f9929a730070b731f451dce6a0759f8d3f5a2beb7c9574048",
    "gold:2608.20180:02": "450e926d99f052bbf755260607141acf623def64f049c1629942ecaa850c5368",
    "gold:2608.20180:03": "2945e0e9f1fbf4589bea0f596b5cdf2a73ac2570e1aed5fcee59a0a46312048b",
    "gold:2608.20180:04": "1bb3b814068c609633b8109ff0ebec08e5ecb94d72084fff3e1352908695d7b9",
    "gold:2608.20180:05": "e3c5a2348fe6f61e50e602cf20f16c7afa0b67e5fcece93f4f5c383374361a71",
    "gold:2608.14798:01": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "gold:2608.14798:02": "bdc7c5e6da0117455a834400b51d804d26e9f846cfe6a9f037d74ed6e3262682",
    "gold:2608.14798:03": "2c7a34b01f4bced9612e0faef8e616626ad7d3ef4289caf7e86267b0663a291f",
    "gold:2608.14798:04": "2fe0dc3803f5115446103c0070de4bbb5492482a5ba785283431823b50d6118d",
    "gold:2608.05845:01": "c8cb8d81057acddcd852208372ca1c4bb92056f077c153cdc4fa30263fc76f05",
    "gold:2608.05845:02": "aea620debb26c439ac42b85677b60e145ecd79fd175c57095efacbb185521f3d",
    "gold:2608.05845:03": "14c895ca77c73a793a76e84a33999f477036e098c3014f934f9449e522e1774a",
    "gold:2608.05845:04": "877dc76013d5e5f8094edf621a82936322ed3ce67a1230e4d7668a7a0ac320d8",
    "gold:2608.05845:05": "f3828f82d655ed32f13bc686df0ae657c816d898373ed613c90f5ee623a63010",
    "gold:2608.15963:01": "7a4be0e13be9273c75180eb0abc1db524d9a9457c396832f9e4bf1ed9ed9bfed",
    "gold:2608.15963:02": "9cfbff39de073ad90fdd2edf5aab825a815e6f9e5820e881523585b97d9dfaad",
    "gold:2608.15963:03": "6bd12a4c2fcca047ad17b84f58599f7461e676278cfbdec959e92505eedd4130",
    "gold:2608.15963:04": "59c52e5229eb877f62c06beff2ae357c19eb279eb60201398b73df5647d3cab8",
    "gold:2608.22867:01": "b9a543330de033778898cc651de8f616d5861c9b8860140d6d729a887f392ad6",
    "gold:2608.22867:02": "87b22dc63c5e917a04a4949235002bd2036742f6a5c38d5ee201a08c7d8e022a",
    "gold:2608.22867:03": "04f2400702f9dc4432531343bd333f97795085625419f8588c4190f5bd2c5048",
    "gold:2608.22867:04": "39f0a78be9ead4f27bc9fcf30dc6bde5c57667ce4c9d35e0c12ce66ab7ce70c6",
    "gold:2608.02862:01": "d3aeec642e21e40fb54170f7199484e0663287da59e653600abf014b2978ed69",
    "gold:2608.02862:02": "f11f3603d8c032b3fc0e46617eb5f6059f1c37fb19d47b3f8c056abf1c8355b8",
    "gold:2608.02862:03": "83b09cda7cdcc7f88c75596a708cdce61e4695e63fc2549951de80f09a973162",
    "gold:2608.02862:04": "5c387c20ba65e145e9a31392977e3798d87b87cd1e8fec5c1e68878b85a37498",
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number}: expected an object")
            rows.append(value)
    return rows


def keyed(rows: list[dict[str, Any]], key: str, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for number, row in enumerate(rows, 1):
        value = row.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{label}:{number}: missing string {key}")
        elif value in result:
            errors.append(f"{label}:{number}: duplicate {key} {value}")
        else:
            result[value] = row
    return result


def candidate_index(data_root: Path, errors: list[str]) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(data_root.glob("claims-*.jsonl")):
        rows.extend(load_jsonl(path))
    return keyed(rows, "candidate_id", "upstream candidates", errors)


def validate(study_root: Path, upstream_data: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    candidates = candidate_index(upstream_data, errors)
    gold_rows = load_jsonl(study_root / "data/gold-slices.jsonl")
    math_rows = load_jsonl(study_root / "data/assumed-mathclaims.jsonl")
    math_relation_rows = load_jsonl(study_root / "data/assumed-math-relations.jsonl")
    unit_rows = load_jsonl(study_root / "data/contribution-units.jsonl")
    profile_rows = load_jsonl(study_root / "data/contribution-profiles.jsonl")
    iteration_rows = load_jsonl(study_root / "data/iteration-log.jsonl")

    schema = json.loads((study_root / "data/gold-slice-schema.json").read_text(encoding="utf-8"))
    schema_validator = jsonschema.Draft202012Validator(schema)
    for number, row in enumerate(gold_rows, 1):
        for error in sorted(schema_validator.iter_errors(row), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path)
            errors.append(f"gold-slices.jsonl:{number}:{location}: {error.message}")

    gold_decisions = keyed(gold_rows, "decision_id", "gold decisions", errors)
    math_claims = keyed(math_rows, "math_claim_id", "assumed MathClaims", errors)
    math_relations = keyed(math_relation_rows, "relation_id", "assumed math relations", errors)
    units = keyed(unit_rows, "unit_id", "contribution units", errors)
    profiles = keyed(profile_rows, "profile_id", "contribution profiles", errors)
    iterations = keyed(iteration_rows, "iteration_id", "iteration log", errors)
    if set(gold_decisions) != set(EXPECTED_RESIDUAL_ENVELOPE_DIGESTS):
        errors.append("gold decisions do not match the independent residual-envelope inventory")

    for ref, row in math_claims.items():
        stored = row.get("contract_hash")
        payload = {key: value for key, value in row.items() if key != "contract_hash"}
        if stored != digest(payload):
            errors.append(f"{ref}: contract_hash does not match canonical fixture")
        if row.get("status") != "ASSUMED_VERIFIED_FOR_STUDY":
            errors.append(f"{ref}: invalid research-only status")
        if not row.get("proposition"):
            errors.append(f"{ref}: empty proposition")
        for candidate_ref in row.get("source_candidate_refs", []):
            if candidate_ref not in candidates:
                errors.append(f"{ref}: unresolved source candidate {candidate_ref}")
        for dependency_ref in row.get("dependencies", []):
            if dependency_ref not in math_claims:
                errors.append(f"{ref}: unresolved MathClaim dependency {dependency_ref}")

    moment_ref = "math:assumed:2608.15963:bernoulli-sample-moments"
    iid_ref = "math:assumed:2608.15963:iid-bernoulli-premise"
    if moment_ref not in math_claims or iid_ref not in math_claims.get(moment_ref, {}).get("dependencies", []):
        errors.append(f"{moment_ref}: must retain {iid_ref} as an internal dependency")

    relation_by_decision: dict[str, dict[str, Any]] = {}
    for ref, row in math_relations.items():
        stored = row.get("relation_hash")
        payload = {key: value for key, value in row.items() if key != "relation_hash"}
        if stored != digest(payload):
            errors.append(f"{ref}: relation_hash does not match canonical fixture")
        for claim_ref in row.get("source_math_claim_refs", []) + row.get("target_math_claim_refs", []):
            if claim_ref not in math_claims:
                errors.append(f"{ref}: unresolved assumed MathClaim {claim_ref}")
        if not row.get("source_math_claim_refs") or not row.get("target_math_claim_refs"):
            errors.append(f"{ref}: directed relation requires source and target MathClaims")
        if not row.get("orientation"):
            errors.append(f"{ref}: relation orientation is not explicit")
        for side in ("source", "target"):
            claim_refs = row.get(f"{side}_math_claim_refs", [])
            candidate_refs = row.get(f"{side}_candidate_refs", [])
            groundings = row.get(f"{side}_groundings", [])
            if {item.get("math_claim_ref") for item in groundings} != set(claim_refs):
                errors.append(f"{ref}: {side} groundings do not cover MathClaim endpoints exactly")
            if {item.get("candidate_ref") for item in groundings} != set(candidate_refs):
                errors.append(f"{ref}: {side} candidate endpoints do not match groundings")
            for candidate_ref in candidate_refs:
                if candidate_ref not in candidates:
                    errors.append(f"{ref}: unresolved {side} candidate {candidate_ref}")
            for item in groundings:
                if item.get("component_path") == "statement" or not item.get("component_path"):
                    errors.append(f"{ref}: {side} endpoint lacks clause-addressable grounding")
        decision_ref = "gold:" + ref.removeprefix("mathrel:")
        relation_by_decision[decision_ref] = row

    by_decision: Counter[str] = Counter()
    by_relation: Counter[str] = Counter()
    by_query: Counter[str] = Counter()
    by_paper: Counter[str] = Counter()
    envelope: Counter[str] = Counter()
    decision_tags: Counter[str] = Counter()
    occurrence_before = 0
    occurrence_after = 0
    hidden_claim_units = 0
    adjudicator_false_prunes = 0
    audit_blocked = 0

    for number, row in enumerate(gold_rows, 1):
        prefix = f"gold-slices.jsonl:{number}"
        refs = row.get("candidate_refs", [])
        snapshots = {item.get("candidate_ref"): item.get("record_sha256") for item in row.get("candidate_snapshots", [])}
        if set(snapshots) != set(refs):
            errors.append(f"{prefix}: candidate snapshots do not cover candidate_refs exactly")
        for ref in refs:
            if ref not in candidates:
                errors.append(f"{prefix}: unresolved candidate {ref}")
                continue
            if candidates[ref].get("paper_id") != row.get("paper_id"):
                errors.append(f"{prefix}: candidate {ref} belongs to another paper")
            if snapshots.get(ref) != digest(candidates[ref]):
                errors.append(f"{prefix}: snapshot hash mismatch for {ref}")
        if not set(row.get("source_claim_refs", [])).issubset(set(refs)):
            errors.append(f"{prefix}: source_claim_refs must be candidate_refs")
        if not set(row.get("target_claim_refs", [])).issubset(set(refs)):
            errors.append(f"{prefix}: target_claim_refs must be candidate_refs")
        if not row.get("source_claim_refs") or not row.get("target_claim_refs"):
            errors.append(f"{prefix}: relation direction requires source and target refs")
        if not row.get("relation_orientation"):
            errors.append(f"{prefix}: relation orientation is not explicit")
        if len(refs) > 1 and set(row.get("source_claim_refs", [])) & set(row.get("target_claim_refs", [])):
            errors.append(f"{prefix}: directed multi-claim relation endpoints overlap")
        if not set(row.get("representative_refs", [])).issubset(set(refs)):
            errors.append(f"{prefix}: representative_refs must be candidate_refs")

        coverage = row.get("grounding_coverage")
        math_refs = row.get("assumed_math_claim_refs", [])
        components = row.get("covered_components", [])
        if coverage == "NONE" and (math_refs or components):
            errors.append(f"{prefix}: NONE grounding cannot cite mathematics or covered components")
        if coverage in {"COMPLETE", "PARTIAL"} and (not math_refs or not components):
            errors.append(f"{prefix}: grounded decision requires contracts and component mappings")
        for ref in math_refs:
            if ref not in math_claims:
                errors.append(f"{prefix}: unresolved assumed MathClaim {ref}")
        covered_math_refs: set[str] = set()
        component_keys: set[tuple[Any, Any]] = set()
        covered_candidates: set[str] = set()
        for component in components:
            candidate_ref = component.get("candidate_ref")
            component_math_refs = component.get("math_claim_refs", [])
            key = (candidate_ref, component.get("component_path"))
            if candidate_ref not in refs:
                errors.append(f"{prefix}: component points outside candidate_refs")
            if key in component_keys:
                errors.append(f"{prefix}: duplicate candidate component grounding")
            component_keys.add(key)
            covered_candidates.add(candidate_ref)
            if component.get("component_path") == "statement" or not component.get("component_path"):
                errors.append(f"{prefix}: grounding must identify a component narrower than statement")
            if not component_math_refs:
                errors.append(f"{prefix}: component grounding has no MathClaim")
            if not set(component_math_refs).issubset(set(math_refs)):
                errors.append(f"{prefix}: component cites undeclared MathClaim")
            covered_math_refs.update(component_math_refs)
        if coverage in {"COMPLETE", "PARTIAL"} and covered_math_refs != set(math_refs):
            errors.append(f"{prefix}: component mappings do not cover declared MathClaims exactly")
        if coverage == "COMPLETE":
            if covered_candidates != set(refs) or any(item.get("coverage") != "COMPLETE" for item in components):
                errors.append(f"{prefix}: COMPLETE means every candidate mathematical component is completely grounded")
        if coverage == "PARTIAL":
            if not row.get("residual_envelope"):
                errors.append(f"{prefix}: PARTIAL grounding requires a nonempty residual semantic envelope")
            if any(item.get("coverage") != "PARTIAL" for item in components):
                errors.append(f"{prefix}: PARTIAL component mappings must remain partial")

        decision_id = row.get("decision_id")
        adjudication = EXPECTED_RELATION_ADJUDICATIONS.get(decision_id)
        if adjudication and any(row.get(field) != expected for field, expected in adjudication.items()):
            errors.append(f"{prefix}: relation conflicts with independent adjudication anchor")
        expected_envelope_digest = EXPECTED_RESIDUAL_ENVELOPE_DIGESTS.get(decision_id)
        if expected_envelope_digest != digest(row.get("residual_envelope", [])):
            errors.append(f"{prefix}: residual envelope conflicts with independent adjudication inventory")

        relation_fixture = relation_by_decision.get(decision_id)
        if relation_fixture:
            if relation_fixture.get("relation_type") != row.get("relation_type"):
                errors.append(f"{prefix}: gold and MathClaim relation types differ")
            for side in ("source", "target"):
                if set(relation_fixture.get(f"{side}_candidate_refs", [])) != set(row.get(f"{side}_claim_refs", [])):
                    errors.append(f"{prefix}: materialized {side} candidate endpoints differ from gold relation")
                for grounding in relation_fixture.get(f"{side}_groundings", []):
                    if not any(
                        component.get("candidate_ref") == grounding.get("candidate_ref")
                        and component.get("component_path") == grounding.get("component_path")
                        and grounding.get("math_claim_ref") in component.get("math_claim_refs", [])
                        for component in components
                    ):
                        errors.append(f"{prefix}: {side} MathClaim endpoint is not aligned to its candidate component")

        dimensions = {item.get("dimension") for item in row.get("residual_envelope", [])}
        compared = {item.get("dimension") for item in row.get("envelope_comparison", [])}
        if dimensions != compared:
            errors.append(f"{prefix}: residual envelope and comparison dimensions differ")
        for item in row.get("residual_envelope", []):
            if item.get("candidate_ref") not in refs:
                errors.append(f"{prefix}: residual envelope points outside candidate_refs")
            if not item.get("value"):
                errors.append(f"{prefix}: empty residual envelope value")

        decision = row.get("decision")
        relation = row.get("relation_type")
        receipt = row.get("reconstruction_receipt", {})
        receipt_payload = {key: value for key, value in receipt.items() if key != "receipt_hash"}
        if receipt.get("receipt_hash") != digest(receipt_payload):
            errors.append(f"{prefix}: reconstruction receipt hash mismatch")
        if receipt.get("preserved_envelope") != row.get("residual_envelope"):
            errors.append(f"{prefix}: reconstruction receipt does not preserve the exact residual envelope")
        expected_snapshots = {ref: digest(candidates[ref]) for ref in refs if ref in candidates}
        if receipt.get("candidate_snapshot_hashes") != expected_snapshots:
            errors.append(f"{prefix}: reconstruction receipt candidate hashes mismatch")
        expected_spans = {ref: digest(candidates[ref].get("source_spans", [])) for ref in refs if ref in candidates}
        if receipt.get("source_span_digests") != expected_spans:
            errors.append(f"{prefix}: reconstruction receipt source-span digests mismatch")
        policy = receipt.get("policy_fixture", {})
        if policy.get("sha256") != digest(policy.get("payload")):
            errors.append(f"{prefix}: reconstruction policy fixture hash mismatch")
        if policy.get("payload", {}).get("query_profile") != row.get("query_profile"):
            errors.append(f"{prefix}: reconstruction policy query does not match decision")
        hidden = receipt.get("hidden_claim_refs", [])
        expected_hidden = [ref for ref in refs if ref not in row.get("representative_refs", [])] if decision == "HIDE_IN_VIEW" else []
        if hidden != expected_hidden:
            errors.append(f"{prefix}: reconstruction receipt has incorrect hidden claims")
        if hidden:
            hidden_claim_units += len(hidden)
            if not receipt.get("reconstructible"):
                errors.append(f"{prefix}: hidden claim is not reconstructible")
            residual_refs = {item.get("candidate_ref") for item in row.get("residual_envelope", [])}
            if not set(hidden).issubset(residual_refs):
                errors.append(f"{prefix}: hidden claim lacks explicit residual-envelope values")
        if decision == "HIDE_IN_VIEW" and relation not in {"SAME_OCCURRENCE_LINEAGE", "SEMANTIC_EQUIVALENT", "DERIVABLE_EXPOSITION"}:
            errors.append(f"{prefix}: unsafe relation for HIDE_IN_VIEW")
        if decision == "BLOCK_REDUCTION" and relation not in {"BLOCKED", "CONTRADICTS", "UNKNOWN"}:
            errors.append(f"{prefix}: block decision lacks a blocking relation")
        if decision == "CONSOLIDATE_OCCURRENCES":
            spans = sum(len(candidates[ref].get("source_spans", [])) for ref in refs if ref in candidates)
            expected_occurrences = spans - len(refs)
            if len(receipt.get("hidden_occurrences", [])) != expected_occurrences:
                errors.append(f"{prefix}: incomplete occurrence reconstruction receipt")
            occurrence_before += spans
            occurrence_after += len(refs)

        for ref in row.get("contribution_unit_refs", []):
            if ref not in units:
                errors.append(f"{prefix}: unresolved contribution unit {ref}")
        for ref in row.get("iteration_evidence_refs", []):
            if ref not in iterations:
                errors.append(f"{prefix}: unresolved iteration evidence {ref}")
        review = row.get("review", {})
        adjudicator_false_prunes += bool(review.get("adjudicator_marked_high_severity_false_prune"))
        audit_blocked += review.get("independent_audit") == "BLOCKED"

        by_decision[str(decision)] += 1
        by_relation[str(relation)] += 1
        by_query[str(row.get("query_profile"))] += 1
        by_paper[str(row.get("paper_id"))] += 1
        envelope.update(dimensions)
        decision_tags.update(row.get("contribution_operations", []))

    for ref, unit in units.items():
        stored = unit.get("record_hash")
        payload = {key: value for key, value in unit.items() if key != "record_hash"}
        if stored != digest(payload):
            errors.append(f"{ref}: record_hash mismatch")
        if unit.get("status") != "ACCEPTED_FOR_STUDY":
            errors.append(f"{ref}: contribution unit is not accepted for study")
        for claim_ref in unit.get("output_claim_refs", []) + unit.get("baseline_claim_refs", []):
            if claim_ref not in candidates:
                errors.append(f"{ref}: unresolved output or baseline candidate {claim_ref}")
        if not unit.get("output_claim_refs") or not unit.get("baseline_claim_refs"):
            errors.append(f"{ref}: output and baseline references are mandatory")
        declarations = unit.get("baseline_declarations", [])
        if {item.get("baseline_ref") for item in declarations} != set(unit.get("baseline_claim_refs", [])):
            errors.append(f"{ref}: baseline declarations do not match baseline_claim_refs")
        for declaration in declarations:
            baseline_ref = declaration.get("baseline_ref")
            if baseline_ref in candidates and declaration.get("record_sha256") != digest(candidates[baseline_ref]):
                errors.append(f"{ref}: baseline declaration hash mismatch for {baseline_ref}")
        witnesses = unit.get("dimension_witnesses", {})
        if set(witnesses) != {"new_math_classes", "proofs_or_methods", "empirical", "interpretive"}:
            errors.append(f"{ref}: contribution unit lacks the required dimension witnesses")
        for dimension, witness_refs in witnesses.items():
            if not set(witness_refs).issubset(set(unit.get("output_claim_refs", []))):
                errors.append(f"{ref}: {dimension} witness is not an output claim")

    accepted_operations: Counter[str] = Counter(op for unit in units.values() for op in unit.get("operation_types", []))
    for ref, profile in profiles.items():
        stored = profile.get("record_hash")
        payload = {key: value for key, value in profile.items() if key != "record_hash"}
        if stored != digest(payload):
            errors.append(f"{ref}: record_hash mismatch")
        unit_refs = profile.get("contribution_unit_refs", [])
        for unit_ref in unit_refs:
            if unit_ref not in units:
                errors.append(f"{ref}: unresolved contribution unit {unit_ref}")
        baseline_set = profile.get("baseline_set", [])
        no_external = baseline_set == ["NO_EXTERNAL_BASELINE"]
        if "NO_EXTERNAL_BASELINE" in baseline_set and not no_external:
            errors.append(f"{ref}: NO_EXTERNAL_BASELINE cannot be combined with candidate baselines")
        for baseline_ref in baseline_set:
            if baseline_ref != "NO_EXTERNAL_BASELINE" and baseline_ref not in candidates:
                errors.append(f"{ref}: unresolved profile baseline {baseline_ref}")
        grouping = profile.get("granularity_grouping_map", {})
        grouped_refs = [unit_ref for group in grouping.values() for unit_ref in group]
        if not grouping or any(not group for group in grouping.values()):
            errors.append(f"{ref}: granularity grouping map must contain nonempty groups")
        if len(grouped_refs) != len(set(grouped_refs)) or set(grouped_refs) != set(unit_refs):
            errors.append(f"{ref}: granularity grouping map must partition contribution_unit_refs")
        for unit_ref in unit_refs:
            if unit_ref not in units:
                continue
            unit = units[unit_ref]
            if unit.get("paper_revision") != profile.get("paper_revision"):
                errors.append(f"{ref}: contribution unit belongs to another paper revision")
            if no_external:
                if not unit.get("allows_no_external_baseline"):
                    errors.append(f"{ref}: contribution unit does not allow an unassessed baseline")
            elif not set(unit.get("baseline_claim_refs", [])).issubset(set(baseline_set)):
                errors.append(f"{ref}: profile baseline is incompatible with contribution unit {unit_ref}")
        groups = [group for group in grouping.values() if all(unit_ref in units for unit_ref in group)]
        expected_vector = {
            "new_math_classes": None if no_external else sum(any(units[unit_ref].get("dimension_witnesses", {}).get("new_math_classes") for unit_ref in group) for group in groups),
            "new_proofs_or_methods": sum(any(units[unit_ref].get("dimension_witnesses", {}).get("proofs_or_methods") for unit_ref in group) for group in groups),
            "empirical_units": sum(any(units[unit_ref].get("dimension_witnesses", {}).get("empirical") for unit_ref in group) for group in groups),
            "interpretive_units": sum(any(units[unit_ref].get("dimension_witnesses", {}).get("interpretive") for unit_ref in group) for group in groups),
            "unknown_or_blocked": len(groups) if no_external else sum(any(units[unit_ref].get("math_delta", {}).get("relation") in {"UNKNOWN", "BLOCKED"} for unit_ref in group) for group in groups),
        }
        if profile.get("aggregate_vector") != expected_vector:
            errors.append(f"{ref}: aggregate vector is not derived from unit witnesses and granularity groups")
        if any(term in canonical(profile).lower() for term in ['"quality":', '"importance":', '"impact":']):
            errors.append(f"{ref}: quality, importance, and impact must not be derived")

    resolvable_triggers = set(gold_row.get("decision_id") for gold_row in gold_rows) | set(math_relations) | set(units) | set(profiles) | set(math_claims)
    for ref, iteration in iterations.items():
        stored = iteration.get("record_hash")
        payload = {key: value for key, value in iteration.items() if key != "record_hash"}
        if stored != digest(payload):
            errors.append(f"{ref}: iteration record_hash mismatch")
        for side in ("input_snapshot", "output_snapshot"):
            snapshot = iteration.get(side, {})
            if not isinstance(snapshot.get("version"), int) or snapshot.get("version", 0) < 1:
                errors.append(f"{ref}: {side} lacks an immutable positive version")
            if snapshot.get("sha256") != digest(snapshot.get("payload")):
                errors.append(f"{ref}: {side} payload digest mismatch")
        for trigger_ref in iteration.get("trigger_refs", []):
            if trigger_ref not in resolvable_triggers:
                errors.append(f"{ref}: unresolved iteration trigger {trigger_ref}")

    required_iterations = {"iteration:loop1:semantic-envelope", "iteration:loop2:contribution-sensitivity", "iteration:audit1:independent", "iteration:audit2:release-blockers"}
    if set(iterations) != required_iterations:
        errors.append("iteration log does not contain both loops and both independent audit corrections")

    required_papers = {f"arxiv:{paper}v1" for paper in ["2608.20180", "2608.14798", "2608.05845", "2608.15963", "2608.22867", "2608.02862"]}
    if set(by_paper) != required_papers:
        errors.append("gold slices do not cover the six declared papers")

    required_files = [
        "main.tex", "preamble.tex", "sections/01-literature.tex", "sections/02-method.tex",
        "sections/03-initial-model.tex", "sections/04-gold-slice-analysis.tex",
        "sections/05-iteration-log.tex", "sections/06-normative-proposal.tex",
        "sections/07-evaluation-and-migration.tex", "sections/08-references.tex",
    ]
    for relative in required_files:
        path = study_root / relative
        if not path.exists():
            errors.append(f"missing study file: {relative}")
        elif path.suffix == ".tex" and len(path.read_text(encoding="utf-8").splitlines()) > 1000:
            errors.append(f"LaTeX module exceeds 1000 lines: {relative}")

    occurrence_reduction = 1.0 - occurrence_after / occurrence_before if occurrence_before else None
    summary = {
        "decision_count": len(gold_rows),
        "paper_count": len(by_paper),
        "assumed_mathclaim_count": len(math_claims),
        "assumed_math_relation_count": len(math_relations),
        "accepted_contribution_unit_count": len(units),
        "contribution_profile_count": len(profiles),
        "iteration_evidence_count": len(iterations),
        "by_decision": dict(sorted(by_decision.items())),
        "by_relation": dict(sorted(by_relation.items())),
        "by_query": dict(sorted(by_query.items())),
        "by_paper": dict(sorted(by_paper.items())),
        "semantic_envelope_counts": dict(sorted(envelope.items())),
        "decision_tag_counts": dict(sorted(decision_tags.items())),
        "accepted_contribution_operation_counts": dict(sorted(accepted_operations.items())),
        "occurrence_consolidation": {"before": occurrence_before, "after": occurrence_after, "reduction": occurrence_reduction},
        "hidden_claim_units_in_declared_views": hidden_claim_units,
        "adjudicator_marked_high_severity_false_prunes": adjudicator_false_prunes,
        "independent_audit_blocked_rows": audit_blocked,
        "assumption_note": "All MathClaim fixtures are ASSUMED_VERIFIED_FOR_STUDY and are not repository proof artifacts.",
    }
    return summary, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", type=Path, default=DEFAULT_STUDY)
    parser.add_argument("--upstream-data", type=Path, default=UPSTREAM_DATA)
    parser.add_argument("--write-summary", action="store_true")
    args = parser.parse_args()
    summary, errors = validate(args.study_root, args.upstream_data)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"semantic-contribution study validation: errors={len(errors)}")
        return 1
    if args.write_summary:
        path = args.study_root / "data/evaluation-summary.json"
        path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("semantic-contribution study validation: errors=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
