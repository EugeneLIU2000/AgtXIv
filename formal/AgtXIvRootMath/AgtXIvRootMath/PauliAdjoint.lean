import AgtXIvRootMath.PauliTrace
import Quantumlib.ForMathlib.Data.Matrix.Unitary

/-!
# Unitary and Hermitian semantics of the locked Pauli matrices

LeanQuantum supplies the phase-aware Pauli group and its concrete matrix
multiplication theorem, but does not expose the unitary/adjoint facts required
by the stabilizer projector proof.  This file reconstructs those facts without
assuming that a Pauli matrix is Hermitian: scalar phases `±i` are unitary but
not Hermitian.  Hermiticity is derived only for involutions.
-/

namespace AgtXIv.Stabilizer

open Kron

/-- Every phase-free one-qubit tensor factor used by `Pauli.toCMatrix` is
unitary. -/
theorem bitsToMat_isUnitary (a b : Bool) :
    (Pauli.toCMatrix.bitsToMat (a, b)).IsUnitary := by
  cases a <;> cases b <;>
    change Pauli.toCMatrix.bitsToMat (_, _) ∈ Matrix.unitaryGroup (Fin 2) ℂ <;>
    rw [Matrix.mem_unitaryGroup_iff'] <;>
    simp only [star] <;>
    ext i j <;> fin_cases i <;> fin_cases j <;>
    simp [Pauli.toCMatrix.bitsToMat, σx, σy, σz, Matrix.mul_apply]

/-- The concrete matrix of every phase-aware Pauli is unitary. -/
theorem pauli_toCMatrix_isUnitary {n : ℕ} (P : Pauli n) :
    P.toCMatrix.IsUnitary := by
  induction n with
  | zero =>
      obtain ⟨m, rfl⟩ := Pauli.of_length_zero P
      fin_cases m <;>
        change _ ∈ Matrix.unitaryGroup (Fin 1) ℂ <;>
        rw [Matrix.mem_unitaryGroup_iff'] <;>
        simp only [star] <;>
        ext i j <;> fin_cases i <;> fin_cases j <;>
        norm_num [Pauli.toCMatrix, Matrix.mul_apply, ZMod.val, pow_succ]
  | succ n ih =>
      rw [Pauli.cons_msb_tail P, Pauli.toCMatrix_cons]
      change
        (Matrix.reindex (finCongr _) (finCongr _)
          (Pauli.toCMatrix.bitsToMat (P.z.msb, P.x.msb) ⊗ P.tail.toCMatrix)) ∈
          Matrix.unitaryGroup (Fin (2 ^ (n + 1))) ℂ
      rw [Matrix.mem_unitaryGroup_iff']
      simp only [star]
      rw [Matrix.conjTranspose_reindex]
      have hLocal := bitsToMat_isUnitary P.z.msb P.x.msb
      have hTail := ih P.tail
      have hLocal' := Matrix.mem_unitaryGroup_iff'.mp hLocal
      have hTail' := Matrix.mem_unitaryGroup_iff'.mp hTail
      simp only [star] at hLocal' hTail'
      let e : Fin (2 * 2 ^ n) ≃ Fin (2 ^ (n + 1)) := finCongr (by ring)
      change
        Matrix.reindexLinearEquiv ℂ ℂ e e
            (Matrix.conjTranspose
              (Pauli.toCMatrix.bitsToMat (P.z.msb, P.x.msb) ⊗ P.tail.toCMatrix)) *
          Matrix.reindexLinearEquiv ℂ ℂ e e
            (Pauli.toCMatrix.bitsToMat (P.z.msb, P.x.msb) ⊗ P.tail.toCMatrix) = 1
      rw [Matrix.reindexLinearEquiv_mul]
      rw [Matrix.conjTranspose_kron, ← Matrix.mul_kron_mul]
      rw [hLocal', hTail', Matrix.one_kron_one]
      exact Matrix.reindexLinearEquiv_one (R := ℂ) (A := ℂ) e

/-- For the locked matrix realization, conjugate transpose agrees with the
group inverse. -/
theorem pauli_toCMatrix_conjTranspose {n : ℕ} (P : Pauli n) :
    Matrix.conjTranspose P.toCMatrix = P⁻¹.toCMatrix := by
  have hMul : Matrix.conjTranspose P.toCMatrix * P.toCMatrix = 1 := by
    have h := Matrix.mem_unitaryGroup_iff'.mp (pauli_toCMatrix_isUnitary P)
    simpa only [star] using h
  calc
    Matrix.conjTranspose P.toCMatrix = Matrix.conjTranspose P.toCMatrix * 1 := by simp
    _ = Matrix.conjTranspose P.toCMatrix * (P.toCMatrix * P⁻¹.toCMatrix) := by
      rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
      simp
    _ = (Matrix.conjTranspose P.toCMatrix * P.toCMatrix) * P⁻¹.toCMatrix := by
      rw [Matrix.mul_assoc]
    _ = P⁻¹.toCMatrix := by rw [hMul, one_mul]

/-- An involutive Pauli is Hermitian.  The order-two premise is essential: a
generic phase-aware Pauli may carry a `±i` scalar phase. -/
theorem pauli_toCMatrix_isHermitian_of_sq_eq_one {n : ℕ} (P : Pauli n)
    (hP : P ^ 2 = 1) : P.toCMatrix.IsHermitian := by
  rw [Matrix.IsHermitian, pauli_toCMatrix_conjTranspose]
  have hInv : P⁻¹ = P := by
    calc
      P⁻¹ = P⁻¹ * 1 := by simp
      _ = P⁻¹ * (P * P) := by
        simpa [pow_two] using congrArg (fun Q => P⁻¹ * Q) hP.symm
      _ = P := by simp
  rw [hInv]

end AgtXIv.Stabilizer
