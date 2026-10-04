# Feasibility of the unchanged closed-form query

**Update 2026-09-24.** A conditional theorem now exists and is kernel-checked in the common physlib environment: `AgtXIv.ReducedRoM.perfect_window_closed_form_bound_and_attainment` (`PositiveCliqueState.lean`) gives, under explicit `hNoActive` and `hPerfect` plus the `MeasurementWindow` fields (`nonempty : 0 < m`, `involutive`, `nonidentitySupport`, `distinctPhaseClass`), the closed form and square-root bound for every density matrix and a state attaining the bound. Evidence: `runs/candidate-compile-20260923/` ([CANDIDATE_INTEGRATION.md](CANDIDATE_INTEGRATION.md)). The chain was written and repaired by agents, not by the automated proof worker, and its alignment with the source below is unreviewed. The analysis that follows is the original feasibility plan; items it lists as missing are now candidates in that build, but every source-alignment question it raises remains open.

An honest **conditional** proof of the closed-form equality was judged mathematically feasible, not a direct application of the compiled sign/clique bridges. The complete query also includes the upper bound and saturation statement; proving only the equality would not complete it.

The target is `Stabilizerness/arXiv-2607.26154v1/draft.tex:270–282` (`thm:solvable`), including
`RoM_M(rho) = max(1, max_Q sum_{P in Q} |tr(P rho)|) <= sqrt(cliqueNum G)` and attainment on the specified positive eigenspace. Nothing below defines RoM by that formula or assumes that equality.

## Required reduced-RoM semantics

The primal at `draft.tex:122–130` explicitly requires both `sum x_v v = b` and `sum x_v = 1`. `AgtXIv.RoM.finiteRoM` in `formal/AgtXIvRootMath/AgtXIvRootMath/FiniteAtomTotalRoM.lean:39` minimizes `l1Cost` subject only to `SignedDecomp`. Applying it directly to `W.projectedFrameAtom` would discard normalization: at `b = 0`, the zero coefficient vector has cost zero, unlike the paper's normalized minimum.

Use augmented atoms and target instead:

```text
a_W(F) := (1, W.projectedFrameAtom F)
t_W(rho) := (1, W.expectationProjection rho.toTraceOneHermitian.1)
reducedRoM(W,rho) := finiteRoM a_W t_W(rho) hFeasible
SignedDecomp a_W (1,b) x ↔ (sum F, x F = 1) ∧ SignedDecomp W.projectedFrameAtom b x
```

Feasibility follows from `traceOne_exists_normalized_stabilizer_signedDecomp` (`UnconditionalStabilizerRoM.lean:26`) and `expectationProjection_reconstruct` (`MeasurementProjection.lean:90`). The finite-atom attainment theorem then supplies an actual minimum. These facts do not require perfectness, sign collapse, V-representation, or the final equality.

This optimization uses all frame-presented projected stabilizer atoms. The source uses the vertices of their convex hull. Their normalized minima agree by convex-generator invariance, but that equivalence must be proved explicitly; merely naming the wrapper “reduced RoM” does not discharge source alignment.

## Independent premises for a conditional equality

The following are proposed mathematical contracts, not currently implemented declarations except where named. Type notation below is schematic; it has not been elaborated as a final theorem.

1. **Repaired stabilizer/context correspondence.** Existing `H : AgtXIv.Varela.VRepRepairObligations W` has exactly these fields (`ContextReconstruction.lean:27–35`):

   ```text
   candidatePhysical : ∀ c : W.MaximalSignedContext,
     FreeByAtoms W.projectedFrameAtom (MaximalSignedContext.vector W c)
   atomRefinement : ∀ F : IndependentSignedPauliFrame n n,
     FreeByAtoms (MaximalSignedContext.vector W) (W.projectedFrameAtom F)
   ```

   These imply the convex-hull equality at `draft.tex:142–146` through `reducedStabilizerPolytope_vrep_conditional`. They are independent Pauli/stabilizer proof obligations, not proven by the conditional theorem.

2. **Phase-aware forward sign collapse — now proved.** Use the graph defined by anticommutation of `W.observable`, together with its independent-set/commuting-context equivalence (`draft.tex:134–140`). Under the source's no-active-dependency hypothesis, the established consequence is:

   ```text
   ∀ (S : Finset (Fin m)) (f : Fin m → Bool),
     W.IsCommutingContext S → W.IsAdmissibleSign S f
   ```

   Here admissibility is absence of `-I` from the generated signed Pauli subgroup (`MaximalContext.lean:45`). `NoActiveDependencies.lean` defines the source-style minimal nonempty scalar Pauli product, proves its F₂ zero-sum characterization and order independence of scalarity, and derives context support independence. `ContextSignIndependence.lean` then constructs arbitrary admissible signs and the exact real-sign domain restricted to the context. The actual endpoint `max_abs_context_signed_sum_of_noActiveDependencies` has only `hNoActive` and `hContext` as explicit proposition premises. Evidence is in `runs/no-active-dependencies-20260919`. The full reverse/parity-code characterization and the converse from arbitrary complex-matrix scalarity remain separate source-alignment work; the forward Pauli phase-scalar implication is proved.

3. **General finite normalized l1 strong duality — now proved.** `FiniteRoMDuality.lean` implements the following general contract for every finite atom family `a : ι → (Fin m → ℝ)` and feasible `b`:

   ```text
   IsGreatest
     {z | ∃ y μ, (∀ j, |μ + sum i, a j i * y i| ≤ 1) ∧
                    z = μ + sum i, b i * y i}
     (finiteRoM (fun j => (1, a j)) (1,b) hFeasible)
   ```

   `normalized_finiteRoM_isGreatest_dual` proves this attained maximum from the original finite-atom minimum and mathlib Hahn–Banach. `reducedRoM_isGreatest_dual W ρ` derives feasibility and applies it to actual projected-frame atoms. Strong duality and the final clique formula are not assumed. The isolated original-epoch success is recorded in `runs/finite-rom-duality-20260919/evidence.json`; particular context/vertex substitution remains separate.

4. **Perfect-graph foundation.** Existing `WeightedPerfectGraphFoundation` and `hPerfect : IsPerfect G` yield

   ```text
   ∀ w, (∀ v, 0 ≤ w v) →
     maxWeightIndependent G w = fractionalCliqueCoverValue G w
   ```

   See `ExternalPerfectGraphFoundation.lean:55–77` and `draft.tex:664–684`. The cover value is an `sInf`; this interface does not directly produce minimizing cover coefficients. Finite cover attainment or approximation reasoning and the antiblocker/support-function argument must still be supplied. The sign-maximization bridge plus this graph argument can derive the dual optimum `max(1,K(b))` by the upper bound and explicit dual witnesses in `draft.tex:700–723`.

## Upper bound, saturation, and source alignment

The compiled `graph_clique_expectation_bound` in `schema v0.3/lean/AnticommutingNonvacuity.lean` supplies the clique bound for actual Physlib `MState` values and Hermitian involutions, with graph-to-anticommutation hypotheses. Using it for the query requires a checked realization of `MeasurementWindow` and `DensityMatrix` in those APIs, preserving matrices and trace expectations. A shared Lean epoch alone is not that mathematical bridge.

Saturation additionally needs the square expansion, traceless-involution positive-eigenspace existence, and trace anticommutator argument at `draft.tex:765–793`. The existing clique inequality does not supply these. An explicit hypothesis `A_Q rho = rho` describes the original support condition; assuming the final RoM value would be tautological and is excluded.

`MeasurementWindow` includes `nonempty : 0 < m`. This is genuinely used by the source proof at `draft.tex:763`, while the theorem header at line 272 omits it. With an empty measurement set the normalized optimum is 1 and the stated ceiling is `sqrt(0)`, so the unrestricted printed bound is false. The extra domain restriction must remain visible as a source-statement discrepancy.

**Source alignment still needed:** projected generators versus convex-hull vertices; the full reverse/parity-code statement; the actual frustration graph; matrix/state representation and real trace; provenance of each external foundation; nonempty measurement domain. The theorem work listed here at the time (generator maps, graph optimization composition, saturation) now has the kernel-checked candidate named at the top. A conditional result remains conditional and unreviewed until its premises (`hNoActive`, `hPerfect`, the window fields) and source alignment are discharged. No completed-query claim is made here.

## Bounded semantic wrapper execution

`ReducedRoMSemantics.lean` now proves the augmented constraint equivalence, density-input feasibility, existence of a normalized minimizing decomposition, and the floor `1 ≤ reducedRoM W ρ`. The wrapper is the actual finite-l1 minimum over projected frame atoms, independent of any desired formula.

The isolated `schema v0.3/runs/reduced-rom-semantics-20260919/attempt-02` compile succeeded in the observed original Lean `4.30.0-rc2` environment. `evidence.json` records seven new declarations, six supporting declarations, axiom audit results, direct proof-term composition, source anchors, the compiled object, and environment hashes. The earlier failed compile is preserved and its error-recovery declarations are excluded from successful evidence. Imported dependencies were read from cache and not rebuilt. This is a separate epoch from Physlib and no final-query declaration or source acceptance is asserted.
