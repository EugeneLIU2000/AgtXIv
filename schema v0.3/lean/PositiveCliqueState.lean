import NormalizedCliqueInvolution

/-! Uncompiled candidate: explicit positive-eigenspace state (I+A_Q)/2^n.
Positivity follows from a Gram matrix identity, without an existence premise.
-/

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela
open scoped ComplexOrder

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

def positiveCliqueStateMatrix (Q : Finset (Fin m)) : CMatrix (2 ^ n) (2 ^ n) :=
  ((2 : ℂ) ^ n)⁻¹ • (1 + normalizedCliqueOperator W Q)

theorem one_add_cliqueOperator_posSemidef (Q : Finset (Fin m))
    (hNonempty : Q.Nonempty)
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) :
    (1 + normalizedCliqueOperator W Q).PosSemidef := by
  let A := normalizedCliqueOperator W Q
  have hHerm : A.conjTranspose = A := (normalizedCliqueOperator_isHermitian W Q).eq
  have hSq : A * A = 1 := by
    simpa only [pow_two] using normalizedCliqueOperator_sq W Q hNonempty hQ
  have hGram : (1 + A).conjTranspose * (1 + A) = (2 : ℂ) • (1 + A) := by
    rw [Matrix.conjTranspose_add, Matrix.conjTranspose_one, hHerm]
    simp only [add_mul, mul_add, one_mul, mul_one, hSq, two_smul]
    abel
  have hPSD := Matrix.posSemidef_conjTranspose_mul_self (1 + A)
  rw [hGram] at hPSD
  have hHalf : (0 : ℂ) ≤ (2 : ℂ)⁻¹ := by
    have hCast : (2 : ℂ)⁻¹ = (((2 : ℝ)⁻¹ : ℝ) : ℂ) := by push_cast; rfl
    rw [hCast]
    exact Complex.zero_le_real.mpr (by norm_num)
  have hScaled := hPSD.smul hHalf
  simpa only [smul_smul, inv_mul_cancel₀ (by norm_num : (2 : ℂ) ≠ 0), one_smul] using hScaled

theorem positiveCliqueStateMatrix_posSemidef (Q : Finset (Fin m))
    (hNonempty : Q.Nonempty)
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) :
    (positiveCliqueStateMatrix W Q).PosSemidef := by
  have hReal : (0 : ℝ) ≤ ((2 : ℝ) ^ n)⁻¹ := by positivity
  have hComplex : (0 : ℂ) ≤ ((2 : ℂ) ^ n)⁻¹ := by
    have hCast : ((2 : ℂ) ^ n)⁻¹ = ((((2 : ℝ) ^ n)⁻¹ : ℝ) : ℂ) := by push_cast; rfl
    rw [hCast]
    exact Complex.zero_le_real.mpr hReal
  exact (one_add_cliqueOperator_posSemidef W Q hNonempty hQ).smul hComplex

theorem positiveCliqueStateMatrix_trace_one (Q : Finset (Fin m)) :
    Matrix.trace (positiveCliqueStateMatrix W Q) = 1 := by
  simp [positiveCliqueStateMatrix, Matrix.trace_smul, Matrix.trace_add,
    normalizedCliqueOperator_trace_zero W, Matrix.trace_one]

theorem positiveCliqueStateMatrix_supported (Q : Finset (Fin m))
    (hNonempty : Q.Nonempty)
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) :
    normalizedCliqueOperator W Q * positiveCliqueStateMatrix W Q =
      positiveCliqueStateMatrix W Q := by
  have hSq : normalizedCliqueOperator W Q * normalizedCliqueOperator W Q = 1 := by
    simpa only [pow_two] using normalizedCliqueOperator_sq W Q hNonempty hQ
  simp only [positiveCliqueStateMatrix, mul_smul_comm, mul_add, mul_one, hSq, add_comm]

/-- A concrete density matrix, rather than a hypothetical supported state. -/
def positiveCliqueState (Q : Finset (Fin m)) (hNonempty : Q.Nonempty)
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) : DensityMatrix (2 ^ n) where
  val := positiveCliqueStateMatrix W Q
  posSemidef := positiveCliqueStateMatrix_posSemidef W Q hNonempty hQ
  trace_one := positiveCliqueStateMatrix_trace_one W Q

theorem positiveCliqueState_attains
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : AgtXIv.GraphFoundation.IsPerfect W.contextFrustrationGraph)
    (Q : Finset (Fin m)) (hNonempty : Q.Nonempty)
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = W.contextFrustrationGraph.cliqueNum) :
    reducedRoM W (positiveCliqueState W Q hNonempty hQ) =
      Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ) := by
  apply reducedRoM_eq_sqrt_of_maximum_clique_support W
    (positiveCliqueState W Q hNonempty hQ) hNoActive hPerfect Q hQ hCard
  exact positiveCliqueStateMatrix_supported W Q hNonempty hQ

/-- A maximum clique and its supported state are constructed, not assumed. -/
theorem exists_reducedRoM_sqrt_attainer
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : AgtXIv.GraphFoundation.IsPerfect W.contextFrustrationGraph) :
    ∃ ρ : DensityMatrix (2 ^ n),
      reducedRoM W ρ = Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ) := by
  classical
  obtain ⟨Q, hQ⟩ := W.contextFrustrationGraph.exists_isNClique_cliqueNum
  have hNonempty : Q.Nonempty := by
    by_contra hEmpty
    have hZero : Q.card = 0 := by simp [Finset.not_nonempty_iff_eq_empty.mp hEmpty]
    have hBaseline := one_le_sqrt_window_cliqueNum W
    rw [← hQ.card_eq, hZero] at hBaseline
    norm_num at hBaseline
  exact ⟨positiveCliqueState W Q hNonempty hQ.isClique,
    positiveCliqueState_attains W hNoActive hPerfect Q hNonempty hQ.isClique hQ.card_eq⟩

/-- Combined query-branch candidate; source alignment and kernel validation
remain external obligations, not claims made by the existence of this file. -/
theorem perfect_window_closed_form_bound_and_attainment
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : AgtXIv.GraphFoundation.IsPerfect W.contextFrustrationGraph) :
    (∀ ρ : DensityMatrix (2 ^ n),
      reducedRoM W ρ = max 1 (AgtXIv.GraphDual.maxWeightClique W.contextFrustrationGraph
        (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|)) ∧
      reducedRoM W ρ ≤ Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ)) ∧
    (∃ ρ : DensityMatrix (2 ^ n),
      reducedRoM W ρ = Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ)) := by
  refine ⟨?_, exists_reducedRoM_sqrt_attainer W hNoActive hPerfect⟩
  intro ρ
  exact ⟨reducedRoM_eq_max_one_clique_weight W ρ hNoActive hPerfect,
    reducedRoM_le_sqrt_cliqueNum W ρ hNoActive hPerfect⟩

end
end AgtXIv.ReducedRoM
