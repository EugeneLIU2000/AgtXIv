import AgtXIvRootMath.PauliAdjoint

/-!
# Faithfulness of the concrete signed-Pauli matrix representation

LeanQuantum provides exact multiplication for the phase-aware Pauli matrices.
Here we prove that the representation loses no signed-Pauli information.  This
is needed when a matrix conjugation identity must be reflected back to an exact
group identity, including the sign of `-I`.
-/

namespace AgtXIv.Stabilizer

/-- The locked concrete matrix representation of the full signed Pauli group
is injective. -/
theorem pauli_toCMatrix_injective {n : ℕ} :
    Function.Injective (fun P : Pauli n => P.toCMatrix) := by
  intro P Q hPQ
  change P.toCMatrix = Q.toCMatrix at hPQ
  let R : Pauli n := P⁻¹ * Q
  have hRMatrix : R.toCMatrix = 1 := by
    dsimp [R]
    rw [Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
    rw [← pauli_toCMatrix_conjTranspose]
    rw [← hPQ]
    have hU := Matrix.mem_unitaryGroup_iff'.mp (pauli_toCMatrix_isUnitary P)
    simpa only [star] using hU
  have hTrace : Matrix.trace R.toCMatrix = ((2 ^ n : ℕ) : ℂ) := by
    rw [hRMatrix, Matrix.trace_one]
    norm_num
  have hSupport : R.z = 0 ∧ R.x = 0 := by
    by_contra h
    have hZero : Matrix.trace R.toCMatrix = 0 := by
      rw [pauli_trace_formula, if_neg h]
    rw [hZero] at hTrace
    have hDim : (((2 ^ n : ℕ) : ℂ)) ≠ 0 := by
      exact_mod_cast (pow_ne_zero n (by norm_num : (2 : ℕ) ≠ 0))
    exact hDim hTrace.symm
  have hPhaseEq : (-Complex.I) ^ R.m.val = 1 := by
    rw [pauli_trace_formula, if_pos hSupport] at hTrace
    have hDim : (((2 ^ n : ℕ) : ℂ)) ≠ 0 := by
      exact_mod_cast (pow_ne_zero n (by norm_num : (2 : ℕ) ≠ 0))
    exact mul_left_cancel₀ hDim (by simpa using hTrace)
  have hm : R.m = 0 := by
    have hv := R.m.val_lt
    interval_cases hval : R.m.val
    · exact (ZMod.val_eq_zero R.m).mp hval
    · exfalso
      have hRe := congrArg Complex.re hPhaseEq
      norm_num [hval] at hRe
    · exfalso
      have hRe := congrArg Complex.re hPhaseEq
      norm_num [hval, pow_two] at hRe
    · exfalso
      have hRe := congrArg Complex.re hPhaseEq
      norm_num [hval, pow_succ] at hRe
  have hR : R = 1 := by
    apply Pauli.ext
    · simpa [hm]
    · simpa [hSupport.1]
    · simpa [hSupport.2]
  have hMul := congrArg (fun S : Pauli n => P * S) hR
  simpa [R, mul_assoc] using hMul.symm

end AgtXIv.Stabilizer
