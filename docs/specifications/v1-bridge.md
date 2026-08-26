# AgtXIv V1 claim–mathematics bridge

**Status:** normative for V1.
**Scope:** bidirectional alignment and conservative status projection for one bounded claim at a time.

## 1. Purpose

V1 connects a source-faithful `ScientificClaim` to the mathematical objects used to inspect it. It answers two narrow questions:

1. Which source components map to which exact `MathClaimIR` or `MathematicalPropositionIR` components, and which physical semantics remain outside that mapping?
2. Given separately registered evidence, blockers, and classifications, what conclusion may a Root Agent project back to the literal source claim without broadening it?

The bridge does not make a mapping true merely by recording it. Mapping-generation provenance, evidence completeness, and scientific acceptance are independent axes. `ORACLE_PROPOSED` / `UNVERIFIED` is input provenance, not acceptance.

## 2. Minimal path

```text
source anchors
  -> source-faithful ScientificClaim
  -> ClaimMathBridge (proposed alignment, mapped + residual semantics)
  -> existing MathClaimIR / MathematicalPropositionIR
  -> existing evidence, blocker, and classification records
  -> BridgeAssessment (bounded Root Agent projection)
  -> separate physicist review / scientific acceptance
```

This is bidirectional alignment: mathematical outcomes may be projected back only through the same pinned bridge components and source scope. No graph property is required for this path.

## 3. V1 scope

| In V1 | Out of V1 / post-V1 |
|---|---|
| One source-faithful claim and its exact anchors | Research-direction discovery |
| Exact mathematical-record references and component roles | Novelty, priority, or contribution scoring |
| `EQUIVALENT`, `CONSERVATIVE`, or `PARTIAL` alignment | Semantic pruning or claim deletion |
| Explicit mapped and residual physical semantics | Graph optimization, root minimization, or global closure |
| Existing evidence/blocker/classification references | Treating navigation coverage as truth |
| Conservative `VERIFIED` / `REFUTED` / `BLOCKED` / `UNKNOWN` / `NOT_CHECKED` outcomes | Automatic scientific acceptance |
| One bounded Root Agent assessment as the V1 gate | General-LLM output as gold |

## 4. Record contracts

### 4.1 `ClaimMathBridge`

A `ClaimMathBridge` is an immutable alignment record. V1 uses record revision 1 and a canonical content hash; corrections create a new identity rather than mutating the record.

It MUST contain:

- an exact immutable reference to one `ScientificClaim` revision;
- the exact source anchors from that claim;
- a complete list of source components;
- for every component, either:
  - one or more exact `MathClaimIR` or `MathematicalPropositionIR` references with role `CONCLUSION`, `ASSUMPTION`, `DEFINITION`, or `DEPENDENCY`; or
  - explicit residual physical semantics;
- overall alignment `EQUIVALENT`, `CONSERVATIVE`, or `PARTIAL`;
- mapping-generation provenance, including `ORACLE_PROPOSED` and `UNVERIFIED` when the preliminary oracle produced the mapping;
- a canonical content hash.

Every mapped `target_ref.component_path` MUST be a nonempty RFC 6901 JSON Pointer that resolves against the exact pinned mathematical record. V1 applies only minimal role compatibility: `CONCLUSION` resolves at `/structured_statement/conclusion` or below; `ASSUMPTION` resolves to an exact item or value under assumptions, quantifiers, or mathematical mode; `DEFINITION` resolves to the conclusion of a record whose statement kind or conclusion relation is `definition`; and `DEPENDENCY`, when present, resolves to an existing mathematical component. These checks prevent a conclusion from being relabeled as an assumption or definition without imposing graph semantics.

It MUST NOT contain verification, truth, acceptance, novelty, contribution, evidence, blocker, aggregate coverage, or navigation-coverage fields. In particular, `UNVERIFIED` describes the mapping proposal's epistemic provenance; it is not a verification result.

### 4.2 `BridgeAssessment`

A `BridgeAssessment` is separate from the bridge and references exactly one immutable bridge. It MUST contain:

- references to existing evidence, blocker, and source-classification records, without copying their bodies;
- exactly one assessment for every bridge component, with a required `assessment_kind` and kind-specific `status`:
  - `MATHEMATICAL_DISPOSITION`: `VERIFIED`, `REFUTED`, `BLOCKED`, `UNKNOWN`, or `NOT_CHECKED`, only for conclusions or proposition components;
  - `APPLICABILITY_MATCH`: `MATCHED`, `PARTIAL`, `MISMATCH`, `UNKNOWN`, or `BLOCKED`, for mapped assumption and definition components;
  - `RESIDUAL_REVIEW`: `PRESERVED`, `INCOMPLETE`, `UNKNOWN`, or `BLOCKED`, for residual components;
- an explicit assumption-and-object match review with its own `status`: `MATCHED`, `PARTIAL`, `MISMATCH`, `UNKNOWN`, or `BLOCKED`;
- an explicit residual-semantics review with its own `status`: `PRESERVED`, `INCOMPLETE`, `UNKNOWN`, or `BLOCKED`;
- a bounded Root Agent conclusion and explicit non-implications;
- unresolved questions;
- `evidence_completeness` and `scientific_acceptance` as separate fields, each preserving `UNKNOWN` and `BLOCKED` when applicable;
- a canonical content hash.

Every `VERIFIED` or `REFUTED` mathematical disposition requires a resolvable evidence or classification basis, and `REFUTED` specifically requires evidence. `MATCHED` is an applicability judgment, not mathematical verification; in the counterexample fixture it also requires the exact counterexample evidence. Residual preservation records that semantics were retained, not that their truth or applicability was established. Navigation or facet coverage is not evidence and is never a mathematical outcome. `COMPLETE_FOR_BOUNDED_CONCLUSION` does not imply `ACCEPTED`; acceptance remains `NOT_REVIEWED` until a separate scientific reviewer acts.

## 5. Conservative projection rules

1. **Pin identities and revisions.** Projection uses the exact source claim, exact anchors, exact mathematical revisions, and exact bridge hash.
2. **Match assumptions and objects first.** Physical system, state space, measurement window, operation class, deterministic/selective regime, and ideal/statistical regime must match.
3. **Project component-wise.** A conclusion outcome cannot silently replace unknown or residual components.
4. **Preserve uncertainty.** Missing evidence remains `UNKNOWN`, `BLOCKED`, or `NOT_CHECKED`; absence of coverage is not refutation and presence of coverage is not verification.
5. **Preserve residual semantics.** A mathematical encoding that omits a physical distinction does not erase that distinction.
6. **Do not repair the source silently.** A literal source proposition and an Agent-repaired proposition are different targets.
7. **Bound non-implications.** A counterexample refutes only the proposition whose assumptions and objects it satisfies. It does not automatically reach a stronger, weaker, covariant, selective, noisy, or full-resource statement.
8. **Keep three axes separate.** Mapping provenance, evidence completeness, and scientific acceptance MUST be reported independently.

## 6. Fixed-window reduced-RoM example

The V1 fixture pins:

- `claim:2602.18939v1:fixed-window-monotonicity-claimed`;
- `math-claim-ir:2602.18939v1:fixed-window-monotonicity-claimed`, revision 2;
- `anchor:2602.18939v1:fixed-window-monotonicity-claim` and `anchor:2602.18939v1:fixed-window-monotonicity-proof`;
- `evidence:2602.18939v1:fixed-window-monotonicity-counterexample`;
- `source-claim-classification:2602.18939v1:fixed-window-monotonicity`.

The mapped scope is finite-dimensional $n$-qubit states, a fixed Pauli measurement window, deterministic trace-preserving stabilizer operations, and the exact/noiseless regime. The quantity is reduced RoM computed from selected measurement coordinates, not full RoM.

The exact one-qubit fixture uses the fixed window $\mathcal M=\{X,Z\}$ and a deterministic Clifford rotation. Reduced RoM changes from $1$ to $\sqrt 2$. Therefore the literal source assertion is `REFUTED` in its exact fixed-window scope. The registered direct one-qubit counterexample proposition and evidence evaluate the projected diamond geometry independently. The disputed general V-representation is not imported, so no `DEPENDENCY` mapping is required for this bounded refutation.

The conservative projection is limited:

- it does **not** refute full-RoM monotonicity;
- it does **not** refute a proposition that transforms the measurement window covariantly with the operation;
- it does **not** assess selective or postselected operation branches;
- it does **not** establish finite-shot performance, noise robustness, confidence bounds, or an experimental acceptance threshold.

Residual physical semantics are explicit: this fixed-window quantity is a measurement-dependent witness, not thereby a general resource monotone. The assumption/object summary is `MATCHED`, and the residual-semantics summary is `PRESERVED`. Component-wise, mapped assumptions and the definition are `APPLICABILITY_MATCH / MATCHED`; all three residuals are `RESIDUAL_REVIEW / PRESERVED`. Preservation does not settle their truth or applicability: measurement-window covariance, finite-shot/noise behavior, and physics acceptance remain explicit unresolved questions. The fixture's evidence is `COMPLETE_FOR_BOUNDED_CONCLUSION`; scientific acceptance is `NOT_REVIEWED`.

## 7. Physics acceptance questions and gates

A physicist reviewing a bridge or assessment MUST ask:

1. What is the physical system and finite/infinite-dimensional domain?
2. Which measurement windows are admissible, and must the window remain fixed or transform covariantly?
3. Is the quantity reduced RoM or full RoM?
4. Are operations deterministic trace-preserving maps or selective/postselected branches?
5. Is the claim ideal and noiseless, or about finite-shot data and an explicit noise model?
6. Is the quantity only a measurement-dependent witness, or is resource-monotone status actually established?
7. Is the assessed proposition the literal source assertion or a repaired proposition?
8. Which semantics are mathematically mapped and which remain residual?
9. What are the independent mapping-provenance, evidence-completeness, and scientific-acceptance states?

The V1 acceptance gate is one bounded claim assessment that passes schema/reference validation, preserves all source and residual components, has evidence for every dispositive projection, states non-implications, and receives separate physics review. Repository validation is not physics acceptance.

## 8. Status of existing artifacts

The following may be useful inputs, but none is a V1 authority for bridge truth or scientific acceptance:

| Existing artifact | V1 status |
|---|---|
| Contribution-profile `ScientificClaim` 1.1 records | Experimental narrative/profile records; not substitutes for the pinned source-occurrence claim in this fixture |
| `ClaimSupportAssociation` | Navigation/migration input; facet coverage is not truth status |
| `mathclaim-semantic-contribution` study | Experimental post-V1 contribution-analysis input |
| Preliminary Oracle DAG | `ORACLE_PROPOSED` / `UNVERIFIED` navigation input |
| Root partitions and root-minimization outputs | Experimental graph/navigation inputs; post-V1 optimization |
| Legacy query outputs | Legacy navigation/migration outputs; not V1 assessment authorities |

`tools/query_agent.py` remains on the legacy path in this V1 slice. It is not partially migrated to infer bridge conclusions.
