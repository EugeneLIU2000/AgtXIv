import ReducedRoMPerfectSqrtBound

/-!
Uncompiled candidate for the source's supported-state saturation implication.
The support hypothesis is the operator equation A_Q * rho = rho, not a RoM
value or expectation certificate. Existence of such a density matrix remains
a separate obligation; this file does not establish nonvacuous saturation.
-/

open scoped BigOperators

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation AgtXIv.GraphDual

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n))

/-- The normalized sum appearing in the paper's positive eigenspace condition. -/
def normalizedCliqueOperator (Q : Finset (Fin m)) :
    CMatrix (2 ^ n) (2 ^ n) :=
  (Real.sqrt (Q.card : ℝ))⁻¹ • ∑ i ∈ Q, (W.observable i).toCMatrix

/-- Taking the trace of the actual support equation fixes the signed sum of
expectations; no coordinate-wise saturation hypothesis is required. -/
theorem expectation_sum_of_positive_support (Q : Finset (Fin m))
    (hQ : Q.Nonempty)
    (hSupport : normalizedCliqueOperator W Q * ρ.val = ρ.val) :
    (∑ i ∈ Q, W.expectationProjection ρ.toTraceOneHermitian.1 i) =
      Real.sqrt (Q.card : ℝ) := by
  have hPos : 0 < Real.sqrt (Q.card : ℝ) :=
    Real.sqrt_pos.2 (by exact_mod_cast hQ.card_pos)
  have hTrace := congrArg (fun A => (Matrix.trace A).re) hSupport
  have hCoord : ∀ i, W.expectationProjection ρ.toTraceOneHermitian.1 i =
      (Matrix.trace ((W.observable i).toCMatrix * ρ.val)).re := fun _ => rfl
  have hLeft : (Matrix.trace (normalizedCliqueOperator W Q * ρ.val)).re =
      (Real.sqrt (Q.card : ℝ))⁻¹ *
        (∑ i ∈ Q, W.expectationProjection ρ.toTraceOneHermitian.1 i) := by
    rw [normalizedCliqueOperator, smul_mul_assoc, Matrix.trace_smul, Complex.smul_re,
      Finset.sum_mul, Matrix.trace_sum, Complex.re_sum, smul_eq_mul]
    simp only [hCoord]
  have hEq : (Real.sqrt (Q.card : ℝ))⁻¹ *
      (∑ i ∈ Q, W.expectationProjection ρ.toTraceOneHermitian.1 i) = 1 := by
    have hTrace' : (Matrix.trace (normalizedCliqueOperator W Q * ρ.val)).re =
        (Matrix.trace ρ.val).re := hTrace
    rw [hLeft, ρ.trace_one, Complex.one_re] at hTrace'
    exact hTrace'
  have hScaled := congrArg (fun x : ℝ => Real.sqrt (Q.card : ℝ) * x) hEq
  simpa only [← mul_assoc, mul_inv_cancel₀ hPos.ne', one_mul, mul_one] using hScaled

/-- Any supported state for a maximum clique attains the square-root bound.
Existence of supported states is deliberately not inferred from this implication. -/
theorem reducedRoM_eq_sqrt_of_maximum_clique_support
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph)
    (Q : Finset (Fin m)) (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = W.contextFrustrationGraph.cliqueNum)
    (hSupport : normalizedCliqueOperator W Q * ρ.val = ρ.val) :
    reducedRoM W ρ = Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ) := by
  have hNonempty : Q.Nonempty := by
    by_contra hEmpty
    have hZero : Q.card = 0 := by simp [Finset.not_nonempty_iff_eq_empty.mp hEmpty]
    have hBaseline := one_le_sqrt_window_cliqueNum W
    rw [← hCard, hZero] at hBaseline
    norm_num at hBaseline
  have hSum := expectation_sum_of_positive_support W ρ Q hNonempty hSupport
  have hAbs : (∑ i ∈ Q, W.expectationProjection ρ.toTraceOneHermitian.1 i) ≤
      ∑ i ∈ Q, |W.expectationProjection ρ.toTraceOneHermitian.1 i| :=
    Finset.sum_le_sum fun i _ => le_abs_self _
  have hClique : (∑ i ∈ Q, |W.expectationProjection ρ.toTraceOneHermitian.1 i|) ≤
      maxWeightClique W.contextFrustrationGraph
        (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|) :=
    (maxWeightClique_le_iff _ _ _).mp le_rfl Q hQ
  apply le_antisymm (reducedRoM_le_sqrt_cliqueNum W ρ hNoActive hPerfect)
  rw [hSum, hCard] at hAbs
  exact hAbs.trans (hClique.trans (maxWeightClique_le_reducedRoM W ρ hNoActive))

end
end AgtXIv.ReducedRoM
