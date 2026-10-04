import ReducedRoMWitnessCapacity
import PauliCliqueMatrixBound

/-! Uncompiled capacity ceiling through the general matrix-unit route.
This deliberately does not import ReducedRoMDimensionCeiling or its F₂ clique
bound. The graph/capacity bridge is shared, with all its hypotheses retained.
No attainment theorem or claim about arbitrary measurement windows is added.
-/

namespace AgtXIv.ReducedRoM.MatrixRoute

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

theorem window_cliqueNum_le_two_mul_add_one :
    W.contextFrustrationGraph.cliqueNum ≤ 2 * n + 1 := by
  classical
  obtain ⟨Q, hQ⟩ := W.contextFrustrationGraph.exists_isNClique_cliqueNum
  have h := AgtXIv.PauliCliqueMatrixBound.clique_card_le_two_mul_add_one W Q hQ.isClique
  simpa only [hQ.card_eq] using h

theorem reducedRoM_le_sqrt_dimension_ceiling (ρ : DensityMatrix (2 ^ n))
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    reducedRoM W ρ ≤ Real.sqrt (2 * (n : ℝ) + 1) := by
  apply (reducedRoM_le_sqrt_cliqueNum W ρ hNoActive hPerfect).trans
  apply Real.sqrt_le_sqrt
  exact_mod_cast window_cliqueNum_le_two_mul_add_one W

theorem witnessCapacity_le_sqrt_dimension_ceiling
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    witnessCapacity W ≤ Real.sqrt (2 * (n : ℝ) + 1) := by
  rw [witnessCapacity_eq_sqrt_cliqueNum W hNoActive hPerfect]
  apply Real.sqrt_le_sqrt
  exact_mod_cast window_cliqueNum_le_two_mul_add_one W

end

end AgtXIv.ReducedRoM.MatrixRoute
