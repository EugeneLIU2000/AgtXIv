# AgtXIv V1 implementation checklist

**Document type:** implementation and release checklist

**Target release:** AgtXIv V1 bounded bridge prototype

**Primary domain:** Stabilizerness

**Normative contract:** [V1 claim--mathematics bridge](../specifications/v1-bridge.md)

**System specification:** [AgtXIv](../../AgtXIv.md)

## 1. V1 objective

V1 demonstrates one source-faithful, bidirectional path:

```text
exact frozen source and anchors
→ ScientificClaim
→ ClaimMathBridge
→ exact RFC 6901-addressed MathClaimIR components
→ registered evidence, blockers, and classifications
→ BridgeAssessment
→ bounded Root Agent conclusion
→ separate physics review
```

The bridge records alignment and mapping-generation provenance. It does not contain truth, verification, acceptance, novelty, contribution, or aggregate coverage. The assessment references evidence and keeps mathematical disposition, assumption/object matching, residual-semantics preservation, evidence completeness, and scientific acceptance separate.

## 2. Frozen V1 case

The primary case is:

```text
claim:2602.18939v1:fixed-window-monotonicity-claimed
```

Question:

> Does reduced robustness of magic for one fixed Pauli measurement window remain non-increasing under every deterministic trace-preserving stabilizer operation?

Required conclusion:

- the literal fixed-window assertion is `REFUTED` by the registered exact one-qubit counterexample;
- the conclusion is limited to finite-dimensional $n$-qubit states, reduced RoM, a fixed Pauli window, deterministic trace-preserving stabilizer operations, and the exact/noiseless regime;
- it does not refute full-RoM monotonicity;
- it does not refute a covariantly transformed-window proposition;
- it does not assess selective or postselected branches;
- it does not establish finite-shot performance, noise robustness, confidence bounds, or an experimental acceptance threshold.

This negative case is preferable for V1 because it tests whether the bridge can prevent a mathematically precise result from being broadened into a false physical statement.

## 3. Required artifacts

### 3.1 Source and claim

- [ ] Pin one exact source version.
- [ ] Pin every source anchor used by the claim and bridge.
- [ ] Preserve the literal source wording in one immutable `ScientificClaim`.
- [ ] Keep source fidelity separate from truth.

### 3.2 `ClaimMathBridge`

- [ ] Reference one exact `ScientificClaim` revision.
- [ ] Account for every relevant source component as `MAPPED` or `RESIDUAL`.
- [ ] Reference exact `MathClaimIR` or `MathematicalPropositionIR` revisions and resolve every nonempty RFC 6901 component pointer.
- [ ] Mark each target role as `CONCLUSION`, `ASSUMPTION`, `DEFINITION`, or `DEPENDENCY`, and enforce minimal role compatibility.
- [ ] Preserve physical system, state domain, measurement window, operation class, exactness, and data regime.
- [ ] Retain all uncovered physical or empirical semantics explicitly.
- [ ] Record mapping provenance as `ORACLE_PROPOSED / UNVERIFIED` when the preliminary Oracle supplied it.
- [ ] Store no verification, acceptance, novelty, contribution, or coverage field.

### 3.3 Mathematical evidence

- [ ] Keep verification evidence external to the bridge.
- [ ] Resolve every evidence, blocker, and classification reference.
- [ ] Require evidence for every `VERIFIED` or `REFUTED` mathematical disposition; do not call applicability matching mathematical verification.
- [ ] Preserve `UNKNOWN`, `BLOCKED`, and `NOT_CHECKED` rather than filling gaps from prose or graph reachability.
- [ ] Keep literal source propositions distinct from Agent-repaired propositions.

### 3.4 `BridgeAssessment`

- [ ] Produce exactly one kind-specific component assessment: `MATHEMATICAL_DISPOSITION`, `APPLICABILITY_MATCH`, or `RESIDUAL_REVIEW`.
- [ ] Record assumption/object matching as `MATCHED`, `PARTIAL`, `MISMATCH`, `UNKNOWN`, or `BLOCKED`.
- [ ] Record residual-semantics preservation as `PRESERVED`, `INCOMPLETE`, `UNKNOWN`, or `BLOCKED`.
- [ ] State a bounded Root Agent conclusion and explicit non-implications.
- [ ] Keep `evidence_completeness` independent of `scientific_acceptance`.
- [ ] Do not infer acceptance from source provenance, Oracle output, navigation coverage, a producer edge, or Lean compilation alone.

## 4. Physics review gate

The reviewer must answer:

1. What physical system and dimensional domain are quantified over?
2. What is an admissible measurement window, and is it fixed or transformed?
3. Is the quantity reduced RoM or full RoM?
4. Are operations deterministic trace-preserving maps or selective branches?
5. Is the result exact/noiseless or statistical/noisy?
6. Is the quantity a measurement-dependent witness or a proved resource monotone?
7. Is the target the literal source assertion or a repaired proposition?
8. Which source semantics are mapped and which remain residual?
9. Are mapping provenance, evidence completeness, and scientific acceptance reported separately?

A schema-valid record is not physics acceptance. Any unanswered truth-relevant question remains `UNKNOWN` or `BLOCKED`.

## 5. Required regression tests

The test suite must reject:

- an unknown claim, mathematical target, evidence, blocker, or classification reference;
- a source component that is neither mapped nor residual;
- erased residual physical semantics;
- verification or acceptance fields embedded in `ClaimMathBridge`;
- Oracle provenance promoted to accepted mapping or scientific truth;
- navigation coverage used as mathematical status;
- `VERIFIED` or `REFUTED` without resolvable evidence;
- full-RoM, selective-operation, transformed-window, finite-shot, or noisy overreach;
- replacement of the fixed-window `REFUTED` result by `VERIFIED` or `UNKNOWN`;
- conflation of evidence completeness with scientific acceptance.

Before release, run:

```bash
python3 tools/validate_scientific_claims.py
python3 -m pytest -q
git diff --check
```

## 6. Release gate

V1 is releasable as a bridge prototype only when:

- [ ] the source, claim, bridge, mathematical records, evidence, assessment, and Root Agent conclusion form one reconstructible path;
- [ ] all hashes and exact references validate;
- [ ] every relevant component is mapped or preserved as residual;
- [ ] the bounded refutation and all non-implications are explicit;
- [ ] an independent physics review finds no unresolved high-severity projection error;
- [ ] tests and validators pass;
- [ ] unrelated working-tree material is excluded from the release commit.

Scientific acceptance of the target paper is not a V1 stopping condition. The fixture may retain `scientific_acceptance: NOT_REVIEWED` while still demonstrating a correct bounded assessment.

## 7. Explicitly post-V1

The following are not V1 gates:

- discovery or ranking of new research directions;
- novelty, priority, importance, impact, or contribution scoring;
- semantic claim pruning, hiding, or compression;
- broad contribution-role claim extraction;
- proof-guided DAG optimization, transitive reduction, or root minimization;
- replacement or training of the preliminary general-LLM Oracle;
- complete PaperBuildDAG construction;
- cross-target reuse telemetry;
- global `MATH_CLOSED` or `VERIFICATION_CLOSED` status;
- formalization of the complete target paper;
- finite-shot or numerical-reproduction claims not required by the bounded fixture.

The exact graph-dual and closed-form Stabilizerness queries remain useful post-V1 migration cases. Their literal V-representation failure, conditional repair, and unresolved perfect-graph foundation must remain visible and must not block release of the bounded bridge prototype.
