#!/usr/bin/env python3
"""Build auditable research fixtures for the semantic-contribution study.

The generated MathClaim records are deliberately marked ASSUMED_VERIFIED_FOR_STUDY.
They are inspectable design fixtures, not Lean or production verification artifacts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/specifications/mathclaim-semantic-contribution/data"
UPSTREAM = ROOT / "docs/specifications/scientific-claim-interface/data"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def candidate_ref(paper: str, suffix: str) -> str:
    return f"candidate:arxiv:{paper}:{suffix}"


def math_ref(paper: str, suffix: str) -> str:
    return f"math:assumed:{paper}:{suffix}"


def load_upstream() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for path in UPSTREAM.glob("claims-*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            index[row["candidate_id"]] = row
    return index


MANUAL_MATH: dict[str, dict[str, Any]] = {
    math_ref("2608.14798", "uniform-random-function-formulas"): {
        "proposition": "For a uniformly random Boolean phase function, the stated subset-phase-state partition-function moments and density formulas hold under the finite-dimensional ensemble assumptions.",
        "assumptions": ["The phase function is uniformly random, not merely pseudorandom."],
        "quantifiers": ["For the finite n-qubit ensemble used by the formula."],
    },
    math_ref("2608.05845", "scalar-comparison"): {
        "proposition": "Scalar viscosity estimates expressed in the same units may be placed in one comparison tuple without identifying their provenance or uncertainty.",
        "assumptions": ["Units, temperature, and material identity are aligned."],
        "quantifiers": [],
    },
    math_ref("2608.15963", "support-membership-probability"): {
        "proposition": "The sample support-membership fraction is the empirical mean of support indicators.",
        "assumptions": ["Samples and hidden support are specified."],
        "quantifiers": ["For N samples."],
    },
    math_ref("2608.15963", "iid-bernoulli-premise"): {
        "proposition": "The support indicators for the N samples are independent and identically distributed Bernoulli variables with common success probability p.",
        "assumptions": ["Each indicator records membership in the same fixed support."],
        "quantifiers": ["For every sample index from 1 through N."],
    },
    math_ref("2608.15963", "bernoulli-sample-moments"): {
        "proposition": "The empirical mean of N Bernoulli variables with common success probability p has expectation p and variance p(1-p)/N.",
        "assumptions": ["The iid Bernoulli premise is supplied as an explicit dependency."],
        "quantifiers": ["For every p in [0,1] and positive integer N."],
    },
    math_ref("2608.20180", "target-geodesic-lift"): {
        "proposition": "A scalar-map composition along an affinely parametrized target geodesic lifts the stated one-scalar solution when the speed and source conditions align.",
        "assumptions": ["The one-scalar source, target metric, affine geodesic, and speed constraint are aligned."],
        "quantifiers": [],
    },
    math_ref("2608.22867", "h-monotonicity"): {
        "proposition": "Under equal bidirectional transition rates, dH/dt is nonpositive and dS/dt is nonnegative.",
        "assumptions": ["Equal-rate detailed-balance assumption."],
        "quantifiers": [],
    },
    math_ref("2608.22867", "free-energy-entropy"): {
        "proposition": "With F=-k_B T ln Z and canonical probabilities, F=E-TS.",
        "assumptions": ["Canonical equilibrium and normalized probabilities."],
        "quantifiers": [],
    },
    math_ref("2608.22867", "gibbs-entropy"): {
        "proposition": "For normalized canonical probabilities, S=-k_B sum_i p_i ln p_i.",
        "assumptions": ["Canonical probabilities are normalized."],
        "quantifiers": ["For all accessible states in the finite sum."],
    },
    math_ref("2608.22867", "copying-terminal-invariant"): {
        "proposition": "Under the specified copying update, a terminal common probability equals one of the initial probability values.",
        "assumptions": ["The copying process reaches a common terminal value."],
        "quantifiers": ["For every realized terminal state under the stated update."],
    },
    math_ref("2608.02862", "local-entropy-maximality"): {
        "proposition": "Under the cited selection hypotheses, the selected limit satisfies the stated local entropy-maximality property.",
        "assumptions": ["The imported theorem's selection hypotheses and parameter range hold."],
        "quantifiers": ["For every parameter value covered by the cited result."],
    },
    math_ref("2608.02862", "selection-observables"): {
        "proposition": "The stated entropy-production, energy, mean-energy, and defect quantities are functions of the Cesaro-averaged numerical fields.",
        "assumptions": ["The numerical fields and averaging procedure are defined."],
        "quantifiers": [],
    },
    math_ref("2608.02862", "selection-functionals"): {
        "proposition": "The stated weighted and unweighted selection functionals aggregate the defined observables over the declared time and state domains.",
        "assumptions": ["The observables and weighting parameters are defined."],
        "quantifiers": [],
    },
    math_ref("2608.02862", "cesaro-average"): {
        "proposition": "The Cesaro average is the arithmetic average of the stated numerical approximations.",
        "assumptions": ["The approximation sequence is defined."],
        "quantifiers": [],
    },
}

DIMENSIONS_BY_DECISION: dict[str, list[str]] = {
    "gold:2608.20180:01": ["CONDITIONS", "PROOF_METHOD"],
    "gold:2608.20180:02": ["ATTRIBUTION", "PROOF_METHOD"],
    "gold:2608.20180:03": ["CONDITIONS", "INTERPRETATION"],
    "gold:2608.20180:04": ["CONDITIONS"],
    "gold:2608.20180:05": ["CONDITIONS", "QUANTIFIERS"],
    "gold:2608.14798:01": [],
    "gold:2608.14798:02": ["CONDITIONS", "ACTOR_ACCESS_MODEL", "EVIDENCE_STATUS"],
    "gold:2608.14798:03": ["CONDITIONS", "LIMITATION"],
    "gold:2608.14798:04": ["APPROXIMATION", "CONDITIONS"],
    "gold:2608.05845:01": ["EMPIRICAL_SCOPE", "COMPARISON_BASELINE"],
    "gold:2608.05845:02": ["EMPIRICAL_SCOPE", "PROOF_METHOD"],
    "gold:2608.05845:03": ["ATTRIBUTION", "UNCERTAINTY", "EVIDENCE_STATUS", "COMPARISON_BASELINE"],
    "gold:2608.05845:04": ["CONDITIONS", "UNCERTAINTY"],
    "gold:2608.05845:05": ["EMPIRICAL_SCOPE", "MODALITY"],
    "gold:2608.15963:01": ["CONDITIONS", "QUANTIFIERS", "INTERPRETATION"],
    "gold:2608.15963:02": ["INTERPRETATION"],
    "gold:2608.15963:03": ["ACTOR_ACCESS_MODEL", "CONDITIONS", "EVIDENCE_STATUS"],
    "gold:2608.15963:04": ["CONDITIONS"],
    "gold:2608.22867:01": ["ATTRIBUTION", "CONDITIONS", "PROOF_METHOD"],
    "gold:2608.22867:02": ["CONDITIONS"],
    "gold:2608.22867:03": ["EMPIRICAL_SCOPE", "EVIDENCE_STATUS", "INTERPRETATION"],
    "gold:2608.22867:04": ["EMPIRICAL_SCOPE", "INTERPRETATION", "EVIDENCE_STATUS"],
    "gold:2608.02862:01": ["ATTRIBUTION", "EMPIRICAL_SCOPE", "EVIDENCE_STATUS"],
    "gold:2608.02862:02": ["EMPIRICAL_SCOPE", "COMPARISON_BASELINE", "INTERPRETATION"],
    "gold:2608.02862:03": ["CONDITIONS"],
    "gold:2608.02862:04": ["EMPIRICAL_SCOPE", "COMPARISON_BASELINE", "EVIDENCE_STATUS"],
}

# Relation orientation is always ``source relation_type target``.  In particular,
# ``DEPENDS_ON`` points from the dependent claim to the prerequisite claim.
DIRECTIONS: dict[str, tuple[list[str], list[str]]] = {
    "gold:2608.20180:02": ([candidate_ref("2608.20180", "geodesic-sufficiency")], [candidate_ref("2608.20180", "geodesic-lift")]),
    "gold:2608.20180:03": ([candidate_ref("2608.20180", "tangherlini-family")], [candidate_ref("2608.20180", "solution-theorem")]),
    "gold:2608.20180:04": ([candidate_ref("2608.20180", "buchdahl-coefficient")], [candidate_ref("2608.20180", "off-shell-density")]),
    "gold:2608.20180:05": ([candidate_ref("2608.20180", "solution-theorem")], [candidate_ref("2608.20180", "ricci-system")]),
    "gold:2608.14798:03": ([candidate_ref("2608.14798", "stabilizer-work-properties")], [candidate_ref("2608.14798", "stabilizer-work-subadditivity")]),
    "gold:2608.14798:04": ([candidate_ref("2608.14798", "haar-asymptotic-spf")], [candidate_ref("2608.14798", "haar-average-spf")]),
    "gold:2608.15963:01": ([candidate_ref("2608.15963", "general-ssb-mass")], [candidate_ref("2608.15963", "ssb-definition")]),
    "gold:2608.15963:02": ([candidate_ref("2608.15963", "general-ssb-mass")], [candidate_ref("2608.15963", "ssb-definition")]),
    "gold:2608.15963:04": ([candidate_ref("2608.15963", "uniform-random-ssb")], [candidate_ref("2608.15963", "depolarizing-ssb")]),
    "gold:2608.22867:02": ([candidate_ref("2608.22867", "free-energy-entropy-identification")], [candidate_ref("2608.22867", "gibbs-entropy-formula")]),
    "gold:2608.02862:03": ([candidate_ref("2608.02862", "selection-functionals-definition")], [candidate_ref("2608.02862", "selection-observables-definition")]),
}

RELATION_OVERRIDES = {
    "gold:2608.20180:04": "DEPENDS_ON",
    "gold:2608.20180:05": "DEPENDS_ON",
    "gold:2608.14798:04": "DEPENDS_ON",
    "gold:2608.15963:01": "DEPENDS_ON",
    "gold:2608.15963:02": "DEPENDS_ON",
    "gold:2608.22867:02": "DEPENDS_ON",
    "gold:2608.02862:03": "DEPENDS_ON",
}

MATH_ENDPOINTS: dict[str, tuple[list[str], list[str]]] = {
    "gold:2608.20180:03": ([math_ref("2608.20180", "tangherlini-family")], [math_ref("2608.20180", "solution-theorem")]),
    "gold:2608.20180:04": ([math_ref("2608.20180", "buchdahl-coefficient")], [math_ref("2608.20180", "off-shell-density")]),
    "gold:2608.20180:05": ([math_ref("2608.20180", "solution-theorem")], [math_ref("2608.20180", "ricci-system")]),
    "gold:2608.14798:01": ([math_ref("2608.14798", "spf-definition")], [math_ref("2608.14798", "cspf-definition")]),
    "gold:2608.14798:04": ([math_ref("2608.14798", "haar-asymptotic-spf")], [math_ref("2608.14798", "haar-average-spf")]),
    "gold:2608.05845:04": ([math_ref("2608.05845", "absolute-standard-error")], [math_ref("2608.05845", "relative-standard-error")]),
    "gold:2608.15963:01": ([math_ref("2608.15963", "bernoulli-sample-moments")], [math_ref("2608.15963", "ssb-definition")]),
    "gold:2608.15963:02": ([math_ref("2608.15963", "general-ssb-mass")], [math_ref("2608.15963", "ssb-definition")]),
    "gold:2608.15963:04": ([math_ref("2608.15963", "uniform-random-ssb")], [math_ref("2608.15963", "depolarizing-ssb")]),
    "gold:2608.22867:02": ([math_ref("2608.22867", "free-energy-entropy")], [math_ref("2608.22867", "gibbs-entropy")]),
    "gold:2608.02862:03": ([math_ref("2608.02862", "selection-functionals")], [math_ref("2608.02862", "selection-observables")]),
}

MATH_DEPENDENCIES = {
    math_ref("2608.15963", "bernoulli-sample-moments"): [math_ref("2608.15963", "iid-bernoulli-premise")],
    math_ref("2608.15963", "general-ssb-mass"): [math_ref("2608.15963", "ssb-definition"), math_ref("2608.15963", "bernoulli-sample-moments")],
}


def dimension_value(row: dict[str, Any], dimension: str) -> str:
    scope = row.get("scope", {})
    if dimension == "CONDITIONS":
        values = scope.get("conditions", [])
        return canonical(values) if values else "No separate structured value; condition-bearing statement: " + row["statement"]
    if dimension == "QUANTIFIERS":
        values = scope.get("quantifiers", [])
        return canonical(values) if values else "No separate structured value; quantifier-bearing statement: " + row["statement"]
    if dimension == "MODALITY":
        return str(row.get("modality"))
    if dimension == "ATTRIBUTION":
        return str(row.get("knowledge_attribution"))
    if dimension in {"EMPIRICAL_SCOPE", "ACTOR_ACCESS_MODEL"}:
        return str(scope.get("population_or_system")) + " | " + canonical(scope.get("conditions", []))
    if dimension == "EVIDENCE_STATUS":
        return str(row.get("review_status")) + " | " + row["statement"]
    return row["statement"]


def component_mappings(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Map only the mathematical clauses actually covered by each contract."""
    refs = set(row["assumed_math_claim_refs"])
    mappings: list[dict[str, Any]] = []
    for candidate in row["candidate_refs"]:
        _, _, paper, suffix = candidate.split(":", 3)
        exact = math_ref(paper, suffix)
        if exact in refs:
            mappings.append({"candidate_ref": candidate, "component_path": "statement.mathematical_content", "coverage": row["grounding_coverage"], "math_claim_refs": [exact]})

    shared: dict[str, dict[str, tuple[str, list[str]]]] = {
        "gold:2608.20180:02": {
            "geodesic-lift": ("statement.lifting_principle", [math_ref("2608.20180", "target-geodesic-lift")]),
            "geodesic-sufficiency": ("statement.sufficiency_conditions", [math_ref("2608.20180", "target-geodesic-lift")]),
        },
        "gold:2608.14798:02": {
            "sps-average-spf": ("statement.random_function_formula", [math_ref("2608.14798", "uniform-random-function-formulas")]),
            "sps-density-corollary": ("statement.random_function_density_formula", [math_ref("2608.14798", "uniform-random-function-formulas")]),
        },
        "gold:2608.14798:03": {
            "stabilizer-work-properties": ("statement.properties.subadditivity", [math_ref("2608.14798", "stabilizer-work-subadditivity")]),
        },
        "gold:2608.05845:02": {
            "implemented-orthoboxy-estimator": ("statement.implemented_formula", [math_ref("2608.05845", "orthoboxy-viscosity-equation")]),
        },
        "gold:2608.05845:03": {
            suffix: ("statement.scalar_value", [math_ref("2608.05845", "scalar-comparison")])
            for suffix in ["acetone-orthoboxy-viscosity", "acetone-green-kubo-viscosity", "acetone-experimental-viscosity"]
        },
        "gold:2608.15963:01": {
            "ssb-definition": ("statement.statistic_definition", [math_ref("2608.15963", "ssb-definition")]),
            "general-ssb-mass": ("statement.moment_formula", [math_ref("2608.15963", "bernoulli-sample-moments")]),
        },
        "gold:2608.15963:03": {
            "ssb-noiseless-completeness": ("statement.support_membership_probability", [math_ref("2608.15963", "support-membership-probability")]),
        },
        "gold:2608.22867:01": {
            "h-theorem-statement": ("statement.monotonicity_conclusion", [math_ref("2608.22867", "h-monotonicity")]),
            "h-monotonicity-derivation": ("statement.monotonicity_formula", [math_ref("2608.22867", "h-monotonicity")]),
        },
        "gold:2608.22867:02": {
            "free-energy-entropy-identification": ("statement.free_energy_identity", [math_ref("2608.22867", "free-energy-entropy")]),
            "gibbs-entropy-formula": ("statement.gibbs_entropy_formula", [math_ref("2608.22867", "gibbs-entropy")]),
        },
        "gold:2608.22867:03": {
            "terminal-value-is-initial-value": ("statement.terminal_value_invariant", [math_ref("2608.22867", "copying-terminal-invariant")]),
        },
        "gold:2608.22867:04": {
            "h-monotonicity-derivation": ("statement.monotonicity_formula", [math_ref("2608.22867", "h-monotonicity")]),
        },
        "gold:2608.02862:01": {
            "local-maximality-mismatch": ("statement.imported_local_maximality_theorem", [math_ref("2608.02862", "local-entropy-maximality")]),
        },
        "gold:2608.02862:03": {
            "selection-observables-definition": ("statement.observables_definition", [math_ref("2608.02862", "selection-observables")]),
            "selection-functionals-definition": ("statement.functionals_definition", [math_ref("2608.02862", "selection-functionals")]),
        },
        "gold:2608.02862:04": {
            "cesaro-density-converges": ("statement.cesaro_average_definition", [math_ref("2608.02862", "cesaro-average")]),
        },
    }
    existing = {(item["candidate_ref"], ref) for item in mappings for ref in item["math_claim_refs"]}
    for candidate in row["candidate_refs"]:
        suffix = candidate.rsplit(":", 1)[1]
        override = shared.get(row["decision_id"], {}).get(suffix)
        if override:
            path, math_refs = override
            missing = [ref for ref in math_refs if (candidate, ref) not in existing]
            if missing:
                mappings.append({"candidate_ref": candidate, "component_path": path, "coverage": row["grounding_coverage"], "math_claim_refs": missing})
    return mappings


def build() -> None:
    upstream = load_upstream()
    rows = [json.loads(line) for line in (DATA / "gold-slices.jsonl").read_text(encoding="utf-8").splitlines()]

    for row in rows:
        row["relation_type"] = RELATION_OVERRIDES.get(row["decision_id"], row["relation_type"])
        if row["decision_id"] == "gold:2608.15963:01":
            row.update(
                decision="KEEP_VISIBLE",
                representative_refs=row["candidate_refs"],
                semantic_envelope=["CONDITIONS", "QUANTIFIERS", "INTERPRETATION"],
                assumed_math_claim_refs=[math_ref("2608.15963", "ssb-definition"), math_ref("2608.15963", "bernoulli-sample-moments")],
                rationale="The moment theorem depends on the statistic definition and carries the iid Bernoulli premise as an internal MathClaim dependency; the definition alone does not entail it. Both scientific claims remain visible.",
            )
            row["review"] = {"pass_one": "REVISED", "pass_two": "REVISED", "independent_audit": "REVISED", "adjudicator_marked_high_severity_false_prune": False}
        if row["decision_id"] == "gold:2608.22867:03":
            row["relation_type"] = "INCOMPARABLE"
            row["rationale"] = "Selecting a terminal value from the initial values motivates but does not entail preservation of the distribution across repeated simulations; the structural and empirical claims remain separate."
            row["review"] = {"pass_one": "REVISED", "pass_two": "REVISED", "independent_audit": "REVISED", "adjudicator_marked_high_severity_false_prune": False}

    all_math_refs = sorted({ref for row in rows for ref in row["assumed_math_claim_refs"]} | set(MATH_DEPENDENCIES) | {ref for refs in MATH_DEPENDENCIES.values() for ref in refs})
    fixtures: list[dict[str, Any]] = []
    for ref in all_math_refs:
        _, _, paper, suffix = ref.split(":", 3)
        candidate = candidate_ref(paper, suffix)
        if ref in MANUAL_MATH:
            content = MANUAL_MATH[ref]
            sources = [candidate] if candidate in upstream else []
            if ref == math_ref("2608.15963", "iid-bernoulli-premise"):
                sources = [candidate_ref("2608.15963", "general-ssb-mass")]
        elif candidate in upstream:
            source = upstream[candidate]
            content = {
                "proposition": source["statement"],
                "assumptions": source.get("scope", {}).get("conditions", []),
                "quantifiers": source.get("scope", {}).get("quantifiers", []),
            }
            sources = [candidate]
        else:
            raise ValueError(f"no assumed MathClaim fixture for {ref}")
        fixture = {
            "math_claim_id": ref,
            "revision": 1,
            "status": "ASSUMED_VERIFIED_FOR_STUDY",
            **content,
            "dependencies": MATH_DEPENDENCIES.get(ref, []),
            "source_candidate_refs": sources,
            "fixture_scope": "Research-only assumed contract; not a Lean or production verification record.",
        }
        fixture["contract_hash"] = digest(fixture)
        fixtures.append(fixture)
    (DATA / "assumed-mathclaims.jsonl").write_text("".join(canonical(row) + "\n" for row in fixtures), encoding="utf-8")

    relations: list[dict[str, Any]] = []
    enriched: list[dict[str, Any]] = []
    for row in rows:
        refs = row["candidate_refs"]
        sources, targets = DIRECTIONS.get(row["decision_id"], ([refs[0]], refs[1:] or [refs[0]]))
        dimensions = DIMENSIONS_BY_DECISION[row["decision_id"]]
        row.pop("semantic_envelope", None)
        old_review = row.pop("review")
        residual = [
            {"dimension": dimension, "candidate_ref": ref, "value": dimension_value(upstream[ref], dimension)}
            for dimension in dimensions
            for ref in refs
        ]
        comparisons = []
        for dimension in dimensions:
            source_values = [dimension_value(upstream[ref], dimension) for ref in sources]
            target_values = [dimension_value(upstream[ref], dimension) for ref in targets]
            result = "ALIGNED" if source_values == target_values else "DISTINCT"
            if row["relation_type"] in {"BLOCKED", "UNKNOWN"}:
                result = "UNRESOLVED"
            comparisons.append({"dimension": dimension, "result": result, "source_values": source_values, "target_values": target_values})
        hidden_claims = [ref for ref in refs if ref not in row["representative_refs"]] if row["decision"] == "HIDE_IN_VIEW" else []
        hidden_occurrences = []
        if row["decision"] == "CONSOLIDATE_OCCURRENCES":
            for ref in refs:
                for number, span in enumerate(upstream[ref]["source_spans"][1:], 2):
                    hidden_occurrences.append({"candidate_ref": ref, "occurrence_index": number, "source_file": span["source_file"], "line_start": span["line_start"], "line_end": span["line_end"]})
        components = [] if row["grounding_coverage"] == "NONE" else component_mappings(row)
        policy_payload = {
            "policy_revision": "claim-view-policy:2",
            "query_profile": row["query_profile"],
            "claim_hiding_relations": ["SAME_OCCURRENCE_LINEAGE", "SEMANTIC_EQUIVALENT", "DERIVABLE_EXPOSITION"],
            "preserve_residual_envelope": True,
        }
        receipt = {
            "hidden_claim_refs": hidden_claims,
            "hidden_occurrences": hidden_occurrences,
            "representative_refs": row["representative_refs"],
            "preserved_envelope": residual,
            "candidate_snapshot_hashes": {ref: digest(upstream[ref]) for ref in refs},
            "source_span_digests": {ref: digest(upstream[ref].get("source_spans", [])) for ref in refs},
            "reconstructible": True,
            "policy_revision": "claim-view-policy:2",
            "policy_fixture": {"payload": policy_payload, "sha256": digest(policy_payload)},
        }
        receipt["receipt_hash"] = digest(receipt)
        enriched_row = {
            "decision_id": row["decision_id"],
            "paper_id": row["paper_id"],
            "candidate_refs": refs,
            "candidate_snapshots": [{"candidate_ref": ref, "record_sha256": digest(upstream[ref])} for ref in refs],
            "source_claim_refs": sources,
            "target_claim_refs": targets,
            "relation_orientation": "source_claim_refs relation_type target_claim_refs; DEPENDS_ON points from dependent to prerequisite",
            "query_profile": row["query_profile"],
            "grounding_coverage": row["grounding_coverage"],
            "assumed_math_claim_refs": row["assumed_math_claim_refs"],
            "covered_components": components,
            "residual_envelope": residual,
            "envelope_comparison": comparisons,
            "relation_type": row["relation_type"],
            "decision": row["decision"],
            "representative_refs": row["representative_refs"],
            "reconstruction_receipt": receipt,
            "contribution_operations": row["contribution_operations"],
            "contribution_unit_refs": [],
            "iteration_evidence_refs": ["iteration:loop1:semantic-envelope", "iteration:loop2:contribution-sensitivity", "iteration:audit1:independent", "iteration:audit2:release-blockers"],
            "rationale": row["rationale"],
            "review": {
                "pass_one": old_review.get("pass_one", "ACCEPTED"),
                "pass_two": old_review.get("pass_two", "ACCEPTED"),
                "independent_audit": old_review.get("independent_audit", "ACCEPTED"),
                "adjudicator_marked_high_severity_false_prune": False,
            },
        }
        enriched.append(enriched_row)
        if row["decision_id"] in MATH_ENDPOINTS:
            source_math, target_math = MATH_ENDPOINTS[row["decision_id"]]

            def endpoint_groundings(math_refs: list[str], preferred: list[str]) -> list[dict[str, str]]:
                result = []
                for math_claim in math_refs:
                    matches = [item for item in components if math_claim in item["math_claim_refs"]]
                    selected = [item for item in matches if item["candidate_ref"] in preferred] or matches
                    for item in selected:
                        result.append({"math_claim_ref": math_claim, "candidate_ref": item["candidate_ref"], "component_path": item["component_path"]})
                return result

            source_groundings = endpoint_groundings(source_math, sources)
            target_groundings = endpoint_groundings(target_math, targets)
            relation = {
                "relation_id": "mathrel:" + row["decision_id"].removeprefix("gold:"),
                "source_math_claim_refs": source_math,
                "target_math_claim_refs": target_math,
                "relation_type": row["relation_type"],
                "orientation": "source_math_claim_refs relation_type target_math_claim_refs; DEPENDS_ON means each source requires the jointly listed targets",
                "assumption_context": "Only assumptions, quantifiers, and explicit dependencies in the referenced assumed contracts; semantic envelopes are excluded.",
                "status": "ASSUMED_VERIFIED_FOR_STUDY",
                "source_candidate_refs": sorted({item["candidate_ref"] for item in source_groundings}),
                "target_candidate_refs": sorted({item["candidate_ref"] for item in target_groundings}),
                "source_groundings": source_groundings,
                "target_groundings": target_groundings,
            }
            relation["relation_hash"] = digest(relation)
            relations.append(relation)
    contribution_specs = [
        ("contrib:2608.20180:geodesic-sufficiency", "2608.20180", ["geodesic-sufficiency"], ["geodesic-lift"], ["PROVES", "SPECIALIZES"], "NEW", "A current-work sufficiency proof is distinguished from the imported lifting principle."),
        ("contrib:2608.20180:solution-theorem", "2608.20180", ["solution-theorem"], ["geodesic-lift"], ["PROVES", "GENERALIZES"], "NEW", "The general theorem combines the source geometry with target-geodesic conditions beyond the lifting baseline."),
        ("contrib:2608.14798:haar-asymptotic", "2608.14798", ["haar-asymptotic-spf"], ["haar-average-spf"], ["COMPUTES", "SPECIALIZES"], "SPECIALIZED", "The asymptotic formula is a regime-qualified consequence of the exact ensemble average."),
        ("contrib:2608.05845:implemented-estimator", "2608.05845", ["implemented-orthoboxy-estimator"], ["orthoboxy-viscosity-equation"], ["IMPLEMENTS"], "EQUIVALENT", "The implementation adds an averaging procedure without claiming a new underlying formula."),
        ("contrib:2608.05845:method-benchmark", "2608.05845", ["methods-agree-three-decades"], ["green-kubo-estimator"], ["BENCHMARKS", "OBSERVES"], "NONE", "The contribution is empirical agreement over the tested liquids, not a new mathematical proposition."),
        ("contrib:2608.15963:ssb-moments", "2608.15963", ["general-ssb-mass"], ["ssb-definition"], ["PROVES", "INTERPRETS"], "NEW", "The arbitrary-distribution moment statement adds an independently sampled Bernoulli theorem and interpretation beyond the definition."),
        ("contrib:2608.22867:h-reproof", "2608.22867", ["h-monotonicity-derivation"], ["h-theorem-statement"], ["REPROVES"], "EQUIVALENT", "The conclusion is background mathematics; the paper contributes a derivation under its equal-rate assumption."),
        ("contrib:2608.02862:combined-ranking", "2608.02862", ["combined-functional-ranking"], ["selection-functionals-definition", "energy-functionals-no-single-winner"], ["BENCHMARKS", "OBSERVES"], "NONE", "The ranking is relative to a declared combined functional and reported numerical data."),
    ]
    units = []
    decision_for_output = {ref: row["decision_id"] for row in enriched for ref in row["candidate_refs"]}
    unit_by_decision: dict[str, list[str]] = {}
    for unit_id, paper, outputs, baselines, operations, math_relation, note in contribution_specs:
        output_refs = [candidate_ref(paper, suffix) for suffix in outputs]
        baseline_refs = [candidate_ref(paper, suffix) for suffix in baselines]
        unit = {
            "unit_id": unit_id,
            "paper_revision": f"arxiv:{paper}v1",
            "output_claim_refs": output_refs,
            "baseline_claim_refs": baseline_refs,
            "baseline_declarations": [
                {"baseline_ref": ref, "role": "COMPARISON_BASELINE", "record_sha256": digest(upstream[ref])}
                for ref in baseline_refs
            ],
            "allows_no_external_baseline": True,
            "operation_types": operations,
            "math_delta": {"relation": math_relation, "new_equivalence_classes": output_refs if math_relation == "NEW" else [], "witness_relations": []},
            "dimension_witnesses": {
                "new_math_classes": output_refs if math_relation == "NEW" else [],
                "proofs_or_methods": output_refs if any(op in operations for op in ["PROVES", "REPROVES", "IMPLEMENTS"]) else [],
                "empirical": output_refs if any(op in operations for op in ["OBSERVES", "BENCHMARKS"]) else [],
                "interpretive": output_refs if "INTERPRETS" in operations else [],
            },
            "assumption_delta": ["See the source candidate scope and the assumed MathClaim contracts."],
            "conclusion_delta": [note],
            "proof_or_method_delta": [note] if any(op in operations for op in ["PROVES", "REPROVES", "IMPLEMENTS"]) else [],
            "semantic_envelope_delta": [note] if any(op in operations for op in ["OBSERVES", "BENCHMARKS", "INTERPRETS"]) else [],
            "verification_and_evidence": ["Math relations are ASSUMED_VERIFIED_FOR_STUDY; empirical and novelty assessments remain source-scoped."],
            "attribution": "CURRENT_WORK",
            "uncertainty": "Baseline-relative design adjudication; not a population or importance estimate.",
            "status": "ACCEPTED_FOR_STUDY",
            "assessor_or_method": "project adjudication revised by independent audit 08f98377bb91",
            "revision": 1,
            "provenance": sorted({decision_for_output.get(ref, "manual:contribution-adjudication") for ref in output_refs}),
        }
        unit["record_hash"] = digest(unit)
        units.append(unit)
        for ref in output_refs:
            if ref in decision_for_output:
                unit_by_decision.setdefault(decision_for_output[ref], []).append(unit_id)
    for row in enriched:
        row["contribution_unit_refs"] = sorted(unit_by_decision.get(row["decision_id"], []))

    profile_specs = [
        ("profile:2608.20180:geodesic:fine", "arxiv:2608.20180v1", [candidate_ref("2608.20180", "geodesic-lift")], "FINE_CLAIM", {"claim:geodesic-sufficiency": ["contrib:2608.20180:geodesic-sufficiency"], "claim:solution-theorem": ["contrib:2608.20180:solution-theorem"]}, "Both accepted units are separate granularity groups."),
        ("profile:2608.20180:geodesic:coarse", "arxiv:2608.20180v1", [candidate_ref("2608.20180", "geodesic-lift")], "COARSE_THEOREM_PACKAGE", {"package:solution-and-proof": ["contrib:2608.20180:geodesic-sufficiency", "contrib:2608.20180:solution-theorem"]}, "The proof mechanism and theorem form one declared package."),
        ("profile:2608.20180:prior-scope:fine", "arxiv:2608.20180v1", [candidate_ref("2608.20180", "geodesic-lift"), candidate_ref("2608.20180", "buchdahl-prior-scope")], "FINE_CLAIM", {"claim:solution-theorem": ["contrib:2608.20180:solution-theorem"]}, "The broader profile scope excludes the separate sufficiency unit."),
        ("profile:2608.22867:h-theorem:fine", "arxiv:2608.22867v1", [candidate_ref("2608.22867", "h-theorem-statement")], "FINE_CLAIM", {"claim:h-reproof": ["contrib:2608.22867:h-reproof"]}, "The accepted witness is a reproof, not a new theorem."),
        ("profile:2608.22867:no-external-baseline:fine", "arxiv:2608.22867v1", ["NO_EXTERNAL_BASELINE"], "FINE_CLAIM", {"claim:h-reproof": ["contrib:2608.22867:h-reproof"]}, "Mathematical novelty remains unknown without an external baseline."),
    ]
    unit_index = {unit["unit_id"]: unit for unit in units}
    profiles = []
    for profile_id, paper_revision, baseline_set, granularity, grouping_map, note in profile_specs:
        unit_refs = sorted({ref for group in grouping_map.values() for ref in group})
        no_external = baseline_set == ["NO_EXTERNAL_BASELINE"]
        groups = list(grouping_map.values())
        aggregate = {
            "new_math_classes": None if no_external else sum(any(unit_index[ref]["dimension_witnesses"]["new_math_classes"] for ref in group) for group in groups),
            "new_proofs_or_methods": sum(any(unit_index[ref]["dimension_witnesses"]["proofs_or_methods"] for ref in group) for group in groups),
            "empirical_units": sum(any(unit_index[ref]["dimension_witnesses"]["empirical"] for ref in group) for group in groups),
            "interpretive_units": sum(any(unit_index[ref]["dimension_witnesses"]["interpretive"] for ref in group) for group in groups),
            "unknown_or_blocked": len(groups) if no_external else sum(any(unit_index[ref]["math_delta"]["relation"] in {"UNKNOWN", "BLOCKED"} for ref in group) for group in groups),
        }
        profile = {
            "profile_id": profile_id,
            "paper_revision": paper_revision,
            "baseline_set": baseline_set,
            "granularity_profile": granularity,
            "granularity_grouping_map": grouping_map,
            "contribution_unit_refs": unit_refs,
            "aggregate_vector": aggregate,
            "aggregate_derivation": "Count witness-bearing granularity groups by dimension; preserve null mathematical novelty when no external baseline is declared.",
            "sensitivity_note": note,
            "comparison_domain": "Only profiles with the same baseline and granularity are component-wise comparable.",
            "assessor_or_method": "study sensitivity analysis; no quality, importance, or impact dimension is derived",
            "revision": 1,
            "provenance": ["iteration:loop2:contribution-sensitivity"],
        }
        profile["record_hash"] = digest(profile)
        profiles.append(profile)

    def snapshot(snapshot_id: str, version: int, payload: dict[str, Any]) -> dict[str, Any]:
        return {"snapshot_id": snapshot_id, "version": version, "payload": payload, "sha256": digest(payload)}

    iterations = [
        {"iteration_id": "iteration:loop1:semantic-envelope", "round": 1, "assessor": "project adjudication", "decided_at": "2026-08-25", "input_snapshot": snapshot("snapshot:loop1:input", 1, {"model": "mathematical equivalence could suggest semantic merging", "grounding": "claim-level"}), "trigger_refs": ["gold:2608.20180:02", "gold:2608.14798:02", "gold:2608.05845:03"], "change": "Split mathematical from semantic equivalence, add clause coverage, residual envelope, and query-relative receipts.", "output_snapshot": snapshot("snapshot:loop1:output", 1, {"interfaces": ["ClaimMathGrounding", "SemanticClaimRelation", "ClaimView"], "destructive_deletion": False})},
        {"iteration_id": "iteration:loop2:contribution-sensitivity", "round": 2, "assessor": "project adjudication", "decided_at": "2026-08-25", "input_snapshot": snapshot("snapshot:loop2:input", 1, {"aggregation": "operation tags and raw new-node counts", "baseline_required": False}), "trigger_refs": ["profile:2608.20180:geodesic:fine", "profile:2608.20180:geodesic:coarse", "profile:2608.22867:h-theorem:fine", "profile:2608.22867:no-external-baseline:fine"], "change": "Make baseline and granularity mandatory, separate new theorem from new proof, and replace scalar scoring with vectors and incomparability.", "output_snapshot": snapshot("snapshot:loop2:output", 1, {"aggregation": "witness-bearing granularity groups", "baseline_required": True, "unknown_novelty": None})},
        {"iteration_id": "iteration:audit1:independent", "round": 3, "assessor": "independent review execution 08f98377bb91", "decided_at": "2026-08-25", "input_snapshot": snapshot("snapshot:audit1:input", 1, {"decision_count": 26, "ssb_hidden": True, "relations_directed": False}), "trigger_refs": ["gold:2608.15963:01", "gold:2608.22867:03"], "change": "Keep the SSB moment claim visible and change the terminal-distribution relation to incomparable.", "output_snapshot": snapshot("snapshot:audit1:output", 1, {"decision_count": 26, "ssb_hidden": False, "claim_level_hides": 0})},
        {"iteration_id": "iteration:audit2:release-blockers", "round": 4, "assessor": "independent audit execution 71aa6f5586f4", "decided_at": "2026-08-25", "input_snapshot": snapshot("snapshot:audit2:input", 1, {"ssb_relation": "DERIVABLE_EXPOSITION", "depolarizing_edge": "depolarizing SPECIALIZES uniform", "observables_edge": "observables STRICTLY_ENTAILS functionals", "component_paths": ["statement"], "profile_vectors": "hard-coded", "iteration_snapshots": "mutable prose"}), "trigger_refs": ["gold:2608.15963:01", "mathrel:2608.15963:04", "mathrel:2608.02862:03", "profile:2608.20180:geodesic:coarse"], "change": "Correct relation semantics and endpoint orientation, make clause grounding specific, derive aggregates from witnesses and grouping maps, and hash immutable iteration and reconstruction evidence.", "output_snapshot": snapshot("snapshot:audit2:output", 1, {"ssb_relation": "DEPENDS_ON", "depolarizing_edge": "uniform SPECIALIZES depolarizing", "observables_edge": "functionals DEPENDS_ON observables", "component_paths": "clause-addressable", "profile_vectors": "derived", "iteration_snapshots": "canonical sha256"})},
    ]
    for iteration in iterations:
        iteration["record_hash"] = digest(iteration)

    (DATA / "gold-slices.jsonl").write_text("".join(canonical(row) + "\n" for row in enriched), encoding="utf-8")
    (DATA / "assumed-math-relations.jsonl").write_text("".join(canonical(row) + "\n" for row in relations), encoding="utf-8")
    (DATA / "contribution-units.jsonl").write_text("".join(canonical(row) + "\n" for row in units), encoding="utf-8")
    (DATA / "contribution-profiles.jsonl").write_text("".join(canonical(row) + "\n" for row in profiles), encoding="utf-8")
    (DATA / "iteration-log.jsonl").write_text("".join(canonical(row) + "\n" for row in iterations), encoding="utf-8")


if __name__ == "__main__":
    build()
