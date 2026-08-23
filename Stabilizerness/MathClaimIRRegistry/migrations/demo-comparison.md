# Demo MathClaimIR migration comparison

This report compares the 50 legacy `knowledge/statements.jsonl` records with records reconstructed from frozen canonical LaTeX. Legacy files remain unchanged.

## Coverage

- Legacy records: **50**
- Migration dispositions: **50**
- Source-grounded MathClaimIR records: **39**
- External mathematical propositions: **18**
- External evidence records: **14**

## Per-paper result

| PaperAgent | Legacy | ClaimIR | Proposition | Evidence | Main dispositions |
|---|---:|---:|---:|---:|---|
| `graph-theoretic-nonstabilizerness` | 21 | 21 | 0 | 5 | NOTATION_ONLY=10, RECLASSIFIED_EXTERNAL=5, SOURCE_UNSUPPORTED=1, SPLIT=5 |
| `predicting-magic-from-very-few-measurements` | 10 | 4 | 7 | 2 | NOTATION_ONLY=3, RECLASSIFIED_EXTERNAL=6, SPLIT=1 |
| `resource-theory-of-stabilizer-computation` | 7 | 5 | 3 | 2 | NOTATION_ONLY=4, RECLASSIFIED_EXTERNAL=1, SEMANTIC_CORRECTION=1, SPLIT=1 |
| `robustness-of-magic` | 5 | 4 | 2 | 3 | NOTATION_ONLY=2, RECLASSIFIED_EXTERNAL=1, SEMANTIC_CORRECTION=1, SPLIT=1 |
| `stabilizer-codes-and-quantum-error-correction` | 7 | 5 | 6 | 2 | NOTATION_ONLY=1, RECLASSIFIED_EXTERNAL=2, SEMANTIC_CORRECTION=1, SPLIT=3 |

## Interpretation

- `MathClaimIR` records source mathematical meaning only; truth judgments, Lean results, blockers, and attribution are external.
- `RECLASSIFIED_EXTERNAL` marks legacy material that was an agent reconstruction, counterexample, numerical check, or verification observation rather than a source claim.
- `SPLIT` marks compound legacy statements decomposed into atomic conclusions or into source and derived layers.
- `SEMANTIC_CORRECTION` marks a source-fidelity correction, not a claim that the paper is mathematically false.
- `SOURCE_UNSUPPORTED` preserves a legacy statement whose asserted detail could not be located in the frozen LaTeX.

## High-priority differences

- `assumption:2607.26154v1:measurement-set-normalized` (SPLIT, source=IMPLICIT_CONTEXT): high-priority source boundary.
- `statement:2607.26154v1:relaxation-exactness` (SPLIT, source=EXPLICIT): high-priority source boundary.
- `statement:2607.26154v1:relaxed-affine-span` (SOURCE_UNSUPPORTED, source=PARTIAL): proof_detail: REMOVED; conclusion: REMOVED.
- `statement:2607.26154v1:dual-mwis` (SPLIT, source=EXPLICIT): high-priority source boundary.
- `statement:2607.26154v1:exact-graph-dual` (NOTATION_ONLY, source=EXPLICIT): hypothesis: ADDED.
- `statement:2607.26154v1:clifford-covariance` (SPLIT, source=EXPLICIT): high-priority source boundary.
- `statement:2607.26154v1:figure2-detection` (RECLASSIFIED_EXTERNAL, source=EXPLICIT): record_kind: RECLASSIFIED.
- `statement:prototype:k3-finite-check` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): record_kind: RECLASSIFIED.
- `statement:prototype:ising-path-finite-check` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): record_kind: RECLASSIFIED.
- `statement:prototype:active-dependency-negative-control` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): record_kind: RECLASSIFIED.
- `statement:prototype:active-dependency-physical-counterexample` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): record_kind: RECLASSIFIED.
- `statement:2602.18939v1:fixed-window-monotonicity-claimed` (RECLASSIFIED_EXTERNAL, source=EXPLICIT): truth_status: RECLASSIFIED; fixed_window: ADDED.
- `statement:2602.18939v1:fixed-window-counterexample` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED.
- `statement:2602.18939v1:reduced-polytope-vrep` (NOTATION_ONLY, source=EXPLICIT): normalization_assumptions: ADDED; proof_status: RECLASSIFIED.
- `assumption:2602.18939v1:normalized-pauli-window` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED; source_support: CHANGED.
- `statement:2602.18939v1:admissible-sign-bijection` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED.
- `statement:2602.18939v1:maximal-context-physical` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED.
- `statement:2602.18939v1:projection-maximal-mixture` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED.
- `statement:2602.18939v1:reduced-polytope-vrep-normalized` (SPLIT, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED; assumptions: ADDED.
- `statement:1307.7171v1:fixed-space-clifford-orbit-equivalence` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED.
- `statement:1307.7171v1:stabilizer-convex-hull` (NOTATION_ONLY, source=EXPLICIT): state_representation: ADDED.
- `statement:1307.7171v1:magic-membership` (SEMANTIC_CORRECTION, source=EXPLICIT): definition_basis: CHANGED; source_anchor: ADDED.
- `statement:1307.7171v1:n-qubit-stabilizer-polytope` (SPLIT, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED; scope: CHANGED.
- `statement:1609.07488v2:rom-definition-normalized` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED; affine_constraint: CHANGED; free_set_bridge: RECLASSIFIED.
- `statement:1609.07488v2:rom-faithfulness` (SEMANTIC_CORRECTION, source=EXPLICIT): hypotheses: REMOVED; strict_outside_clause: ADDED.
- `statement:1609.07488v2:rom-monotonicity` (SPLIT, source=PARTIAL): claim_scope: SPLIT; channel_premise: ADDED; quantified_interface: CHANGED; status_and_blocker: REMOVED.
- `assumption:9705052v1:rank-n-phase-normalized-stabilizer` (RECLASSIFIED_EXTERNAL, source=PARTIAL): origin: RECLASSIFIED; assumptions: CHANGED.
- `assumption:9705052v1:finite-group-representation-core` (RECLASSIFIED_EXTERNAL, source=NOT_SOURCE_CLAIM): record_layer: RECLASSIFIED; physical_scope: REMOVED.
- `statement:9705052v1:stabilizer-code-fixed-space` (SPLIT, source=EXPLICIT): phase_notation: CHANGED; dimension_assumptions: ADDED.
- `statement:9705052v1:n-generator-unique-eigenvector` (SEMANTIC_CORRECTION, source=EXPLICIT): scope: CHANGED; conclusion: CHANGED.
- `statement:9705052v1:group-average-projector` (SPLIT, source=NOT_SOURCE_CLAIM): origin: RECLASSIFIED; source_support: CHANGED.
- `statement:9705052v1:pure-stabilizer-state` (SPLIT, source=PARTIAL): source_scope: CHANGED; terminology: RECLASSIFIED.
