import ReducedRoMPerfectClosedForm
import ConcretePhyslibBridge

/-!
Uncompiled candidate connecting the existing concrete Physlib expectation bound
to the RoM closed form. Operator realization and trace preservation are proved
in ConcretePhyslibBridge, rather than supplied as certificate hypotheses here.
All imports must be rebuilt in one compatible Lean/mathlib/Physlib environment.
-/

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation AgtXIv.GraphDual

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n))

/-- Both existing graph constructions use precisely Pauli noncommutation. -/
theorem contextFrustrationGraph_eq_concrete :
    W.contextFrustrationGraph = AgtXIv.ConcretePhyslib.frustrationGraph W := by
  ext i j
  rfl

theorem max_clique_expectation_le_sqrt :
    maxWeightClique W.contextFrustrationGraph
      (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|) ≤
      Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ) := by
  apply (maxWeightClique_le_iff _ _ _).2
  intro Q hQ
  have hConcrete : (AgtXIv.ConcretePhyslib.frustrationGraph W).IsClique
      (Q : Set (Fin m)) := by
    rwa [← contextFrustrationGraph_eq_concrete W]
  have hBound := AgtXIv.ConcretePhyslib.window_cliqueNumber_bound W ρ Q hConcrete
  rw [← contextFrustrationGraph_eq_concrete W] at hBound
  exact hBound

/-- The original window is nonempty, so the normalization baseline also fits
under sqrt(cliqueNum). This does not impose a new nonempty-clique premise. -/
theorem one_le_sqrt_window_cliqueNum :
    (1 : ℝ) ≤ Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ) := by
  let i : Fin m := ⟨0, W.nonempty⟩
  have hClique : W.contextFrustrationGraph.IsClique
      (({i} : Finset (Fin m)) : Set (Fin m)) := by
    simpa using W.contextFrustrationGraph.isClique_singleton i
  have hNat : 1 ≤ W.contextFrustrationGraph.cliqueNum := by
    simpa using hClique.card_le_cliqueNum
  have hReal : (1 : ℝ) ≤ (W.contextFrustrationGraph.cliqueNum : ℝ) := by
    exact_mod_cast hNat
  simpa only [Real.sqrt_one] using Real.sqrt_le_sqrt hReal

/-- The query's square-root upper bound on actual reduced robustness. -/
theorem reducedRoM_le_sqrt_cliqueNum
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    reducedRoM W ρ ≤ Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ) := by
  rw [reducedRoM_eq_max_one_clique_weight W ρ hNoActive hPerfect]
  exact max_le (one_le_sqrt_window_cliqueNum W) (max_clique_expectation_le_sqrt W ρ)

end
end AgtXIv.ReducedRoM
