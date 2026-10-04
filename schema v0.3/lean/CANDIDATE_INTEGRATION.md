# Query perfect-graph branch: integration boundary

Status (2026-09-24): the 60-module closure compiles in one common environment,
and 54 selected declarations are audited. Evidence:
`runs/candidate-compile-20260923/` (`SUMMARY.json`). Source alignment is unreviewed.

`QueryPerfectBranchCandidates.lean` imports `ReducedRoMPerfectCover`,
`SolvableWindowCapacityMaximum` (which imports `JordanWignerCapacity`), and
`CapacityAnticommutingCriterion`. The JW endpoint alone does not import the
cover-dual reformulation. The old concatenation modules
`RoMGraphDualFoundation.lean` and `GraphDualCoverFoundation.lean` (copied or
re-exported source bodies) are deleted; `ReducedRoMGraphDual` and
`GraphDualBounds` now import the original modules directly, so no declaration
is defined twice. Historical run snapshots keep the old files.

The capacity root joins two chains:

- Actual JW Pauli family → coordinate pairing → anticommutation → no active
  dependencies → complete frustration graph.
- Perfect-graph weighted duality → reduced RoM closed form → square-root bound
  → positive clique state → attained witness capacity, together with the binary
  Gram factorization giving the dimension ceiling.

These arrows describe the current source imports and intended proof use;
they are not accepted paper-dependency edges.

## Compilation path and evidence

`host/extension_migration.py:freeze_extension` still cannot admit these modules:
it requires a successful original-epoch receipt per module, which new candidates
do not have. Do not disable that requirement or manufacture receipts. The separate
candidate path was used instead, all in `runs/candidate-compile-20260923/`:

- `candidate_sources.freeze_candidate_sources(W, run, roots, context_repo=<main checkout>)`
  froze the import closure of four roots (`QueryPerfectBranchCandidates`,
  `ReducedRoMMatrixDimensionCeiling`, `Hurwitz1898Bilinear`,
  `MeasurementWindowDimensionDomain`): 60 modules. `AnticommutingWitness` is
  context-provided (frozen Alpha object, source and olean hashes checked), not recompiled.
- `candidate_compile.compile_next_candidate(..., library=<physlib>)` ran 60 times in
  dependency order: 60 `SUCCEEDED` receipts, logs kept (linter/deprecation warnings
  only). Environment: physlib at Lean v4.33.0 with its pinned mathlib (db584cd6)
  plus the migrated AgtXIv/Quantumlib base, bridge and frozen-Alpha layers.
- `candidate_audit.audit_candidate_plan` audited 54 targets (union of
  `profiles/query-perfect-branch-audit.json` and
  `profiles/query-capacity-matrix-route-audit.json`, plus two terminal theorems):
  44 theorems and 10 definitions, no kind mismatch, axioms only `propext`,
  `Classical.choice`, `Quot.sound`; 65 composition witnesses.

To compile, 21 modules received proof-level repairs for this Mathlib (for example
`SimpleGraph.symm` now being `Std.Symm`), plus a few helper lemmas and one
`open scoped ComplexOrder`; a signature diff shows no existing statement changed
beyond one explicit implicit argument `(K := K)`. Adaptations already
recorded by the earlier epoch migration were ported into 8 modules
(`ContextCodeState`, `ContextSignIndependence`, `FiniteCliqueCoverAttainment`,
`GraphDualBounds`, `MaximalContextPhysical`, `PerfectGraphTrueTwin`,
`ReducedRoMGraphDual`, `SignedGeneratorCompletion`). These repairs were written
by agents, not by the automated proof worker.

The terminal theorem
`AgtXIv.ReducedRoM.perfect_window_closed_form_bound_and_attainment` is
kernel-checked with explicit hypotheses `hNoActive : W.NoActiveDependencies` and
`hPerfect : IsPerfect W.contextFrustrationGraph`, plus the `MeasurementWindow`
structure fields (`nonempty : 0 < m`, `involutive`, `nonidentitySupport`,
`distinctPhaseClass`). Every audit record keeps `source_alignment_accepted=false`.

This build establishes only this candidate branch's kernel acceptance of the
stated implications. Source-premise alignment, recursive citation joins,
earliest-source obligations and the remaining query claims require separate
evidence before the end-to-end goal is complete.
