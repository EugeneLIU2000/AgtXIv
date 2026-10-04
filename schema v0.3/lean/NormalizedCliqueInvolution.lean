import ReducedRoMPerfectAttainment

/-! Uncompiled candidate: the concrete normalized clique operator squares to 1.
This is a construction step toward a positive-eigenspace density matrix, not
an existence proof for that state. -/

open scoped BigOperators

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

/-- The window excludes all scalar Pauli phase classes, so every observable
is traceless, including possible negative representatives. -/
theorem window_observable_trace_zero (i : Fin m) :
    Matrix.trace (W.observable i).toCMatrix = 0 := by
  apply trace_eval_eq_zero_of_support_ne_zero
  by_contra hZero
  push Not at hZero
  apply W.nonidentitySupport i
  simp [F2Support.pauli, hZero.1, hZero.2]
  rfl

theorem normalizedCliqueOperator_trace_zero (Q : Finset (Fin m)) :
    Matrix.trace (normalizedCliqueOperator W Q) = 0 := by
  simp [normalizedCliqueOperator, Matrix.trace_smul, Matrix.trace_sum,
    window_observable_trace_zero W]

theorem normalizedCliqueOperator_isHermitian (Q : Finset (Fin m)) :
    (normalizedCliqueOperator W Q).IsHermitian := by
  have hHerm (i : Fin m) : ((W.observable i).toCMatrix).IsHermitian :=
    pauli_toCMatrix_isHermitian_of_sq_eq_one _ (W.involutive i)
  change (normalizedCliqueOperator W Q).conjTranspose = normalizedCliqueOperator W Q
  simp [normalizedCliqueOperator, Matrix.conjTranspose_smul, Matrix.conjTranspose_sum,
    fun i => (hHerm i).eq]

theorem clique_operator_sum_sq (Q : Finset (Fin m))
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) :
    (∑ i ∈ Q, (W.observable i).toCMatrix) ^ 2 =
      (Q.card : ℝ) • (1 : CMatrix (2 ^ n) (2 ^ n)) := by
  have hConcrete : (AgtXIv.ConcretePhyslib.frustrationGraph W).IsClique
      (Q : Set (Fin m)) := by
    rwa [← contextFrustrationGraph_eq_concrete W]
  have hInv (i : Fin m) (_ : i ∈ Q) :
      (W.observable i).toCMatrix * (W.observable i).toCMatrix = 1 := by
    rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix, ← pow_two,
      W.involutive, Pauli.one_toCMatrix]
  have hAnti (i : Fin m) (hi : i ∈ Q) (j : Fin m) (hj : j ∈ Q) (hne : i ≠ j) :
      (W.observable i).toCMatrix * (W.observable j).toCMatrix =
        -((W.observable j).toCMatrix * (W.observable i).toCMatrix) :=
    AgtXIv.ConcretePhyslib.matrix_anticomm_of_adj W i j (hConcrete hi hj hne)
  simpa using Matrix.weighted_sum_sq_of_pairwise_anticommute Q
    (fun i => (W.observable i).toCMatrix) (fun _ => (1 : ℝ)) hInv hAnti

theorem normalizedCliqueOperator_sq (Q : Finset (Fin m)) (hNonempty : Q.Nonempty)
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) :
    normalizedCliqueOperator W Q ^ 2 = 1 := by
  have hCard : (0 : ℝ) < Q.card := by exact_mod_cast hNonempty.card_pos
  have hSqrt : Real.sqrt (Q.card : ℝ) ≠ 0 := (Real.sqrt_pos.2 hCard).ne'
  have hScale : (Real.sqrt (Q.card : ℝ))⁻¹ *
      (Real.sqrt (Q.card : ℝ))⁻¹ * (Q.card : ℝ) = 1 := by
    have hSquare := Real.sq_sqrt hCard.le
    field_simp [hSqrt]
    nlinarith
  unfold normalizedCliqueOperator
  rw [pow_two, smul_mul_assoc, mul_smul_comm, smul_smul,
    ← pow_two (∑ i ∈ Q, (W.observable i).toCMatrix),
    clique_operator_sum_sq W Q hQ, smul_smul, hScale, one_smul]

end
end AgtXIv.ReducedRoM
