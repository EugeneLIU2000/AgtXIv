import ReducedRoMWitnessCapacity
import PauliCliqueGramFactor

/-! Uncompiled candidates for the n-qubit ceiling and its clique criterion.
These do not construct a Jordan–Wigner window attaining the ceiling.
-/

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

theorem window_cliqueNum_le_two_mul_add_one :
    W.contextFrustrationGraph.cliqueNum ≤ 2 * n + 1 := by
  classical
  obtain ⟨Q, hQ⟩ := W.contextFrustrationGraph.exists_isNClique_cliqueNum
  have h := AgtXIv.PauliCliqueGram.clique_card_le_two_mul_add_one W Q hQ.isClique
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

theorem witnessCapacity_eq_ceiling_iff_cliqueNum
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    witnessCapacity W = Real.sqrt (2 * (n : ℝ) + 1) ↔
      W.contextFrustrationGraph.cliqueNum = 2 * n + 1 := by
  rw [witnessCapacity_eq_sqrt_cliqueNum W hNoActive hPerfect]
  constructor
  · intro h
    have hSquare := congrArg (fun x : ℝ => x ^ 2) h
    rw [Real.sq_sqrt (by positivity), Real.sq_sqrt (by positivity)] at hSquare
    exact_mod_cast hSquare
  · intro h
    have hReal : (W.contextFrustrationGraph.cliqueNum : ℝ) = 2 * (n : ℝ) + 1 := by
      exact_mod_cast h
    rw [hReal]

end
end AgtXIv.ReducedRoM
