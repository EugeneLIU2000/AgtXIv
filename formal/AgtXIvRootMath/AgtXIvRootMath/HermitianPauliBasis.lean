import AgtXIvRootMath.HermitianAffineFeasibility
import AgtXIvRootMath.PauliAdjoint
import Mathlib.LinearAlgebra.FiniteDimensional.Lemmas
import Mathlib.LinearAlgebra.Basis.VectorSpace
import Mathlib.LinearAlgebra.Matrix.StdBasis
import Init.Data.BitVec.Lemmas

/-!
# A phase-clean Hermitian Pauli basis

This module constructs one involutive signed representative for each binary
`Z/X` support and proves that their concrete matrices form a complex basis of
the full matrix algebra.  It then derives the real spanning statement for the
self-adjoint carrier; real completeness is a conclusion, not a field.
-/

namespace AgtXIv.Stabilizer

noncomputable section

open scoped BigOperators
open Module

/-- The `4^n` binary Pauli supports. -/
abbrev PauliSupportIndex (n : ℕ) := BitVec n × BitVec n

/-- The phase-zero Pauli with the requested support. -/
def supportZeroPauli {n : ℕ} (u : PauliSupportIndex n) : Pauli n where
  m := 0
  z := u.1
  x := u.2

/-- Choose the unique representative with phase `0` or `1` that squares to
the identity.  When `Z·X` parity is odd, adding phase one converts the
anti-Hermitian phase-zero string into a Hermitian involution. -/
def hermitianSupportPauli {n : ℕ} (u : PauliSupportIndex n) : Pauli n :=
  let P := supportZeroPauli u
  bif P.phaseFlipsWith P then P.addPhase 1 else P

@[simp]
theorem hermitianSupportPauli_z {n : ℕ} (u : PauliSupportIndex n) :
    (hermitianSupportPauli u).z = u.1 := by
  change (bif (supportZeroPauli u).phaseFlipsWith (supportZeroPauli u)
    then (supportZeroPauli u).addPhase 1 else supportZeroPauli u).z = u.1
  cases h : (supportZeroPauli u).phaseFlipsWith (supportZeroPauli u) <;>
    simp [h, supportZeroPauli]

@[simp]
theorem hermitianSupportPauli_x {n : ℕ} (u : PauliSupportIndex n) :
    (hermitianSupportPauli u).x = u.2 := by
  change (bif (supportZeroPauli u).phaseFlipsWith (supportZeroPauli u)
    then (supportZeroPauli u).addPhase 1 else supportZeroPauli u).x = u.2
  cases h : (supportZeroPauli u).phaseFlipsWith (supportZeroPauli u) <;>
    simp [h, supportZeroPauli]

/-- Every chosen support representative is an exact involution. -/
@[simp]
theorem hermitianSupportPauli_sq {n : ℕ} (u : PauliSupportIndex n) :
    hermitianSupportPauli u ^ 2 = 1 := by
  unfold hermitianSupportPauli
  generalize hP : supportZeroPauli u = P
  have hm : P.m = 0 := by simp [← hP, supportZeroPauli]
  cases h : P.phaseFlipsWith P
  · simp only [h, Bool.false_eq_true, cond_false]
    rw [Pauli.pow_two]
    apply Pauli.ext <;> simp [h, hm, Pauli.one_def, Pauli.addPhase]
  · simp only [h, cond_true]
    have hdot : P.x.dotZ₂ P.z = true := by
      simpa [Pauli.phaseFlipsWith] using h
    rw [Pauli.pow_two]
    apply Pauli.ext
    · simp [Pauli.addPhase, Pauli.one_def, Pauli.phaseFlipsWith, hdot, hm]
      exact (by decide : (2 : ZMod 4) + 2 = 0)
    · simp [Pauli.one_def, Pauli.addPhase]
    · simp [Pauli.one_def, Pauli.addPhase]

/-- Distinct binary supports give distinct signed Paulis. -/
theorem hermitianSupportPauli_injective {n : ℕ} :
    Function.Injective (hermitianSupportPauli (n := n)) := by
  intro u v h
  apply Prod.ext
  · simpa using congrArg Pauli.z h
  · simpa using congrArg Pauli.x h

/-- The concrete matrix of every chosen representative is Hermitian. -/
theorem hermitianSupportPauli_matrix_isHermitian {n : ℕ}
    (u : PauliSupportIndex n) :
    (hermitianSupportPauli u).toCMatrix.IsHermitian :=
  pauli_toCMatrix_isHermitian_of_sq_eq_one _ (hermitianSupportPauli_sq u)

/-- Hilbert--Schmidt orthogonality of distinct binary-support representatives.
The inverse is used so the diagonal product is exactly the identity even
before Hermiticity is invoked. -/
theorem trace_inv_mul_hermitianSupportPauli {n : ℕ}
    (u v : PauliSupportIndex n) :
    Matrix.trace
        ((hermitianSupportPauli u)⁻¹.toCMatrix *
          (hermitianSupportPauli v).toCMatrix) =
      if u = v then ((2 ^ n : ℕ) : ℂ) else 0 := by
  rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
  by_cases huv : u = v
  · subst v
    simp [pauli_trace_formula]
  · rw [if_neg huv]
    apply trace_eval_eq_zero_of_support_ne_zero
    by_contra hzero
    push_neg at hzero
    apply huv
    apply Prod.ext
    · have hz : u.1 ^^^ v.1 = 0 := by
        simpa using hzero.1
      exact BitVec.xor_eq_zero_iff.mp hz
    · have hx : u.2 ^^^ v.2 = 0 := by
        simpa using hzero.2
      exact BitVec.xor_eq_zero_iff.mp hx

/-- The `4^n` Hermitian Pauli matrices are complex-linearly independent. -/
theorem hermitianSupportPauli_matrix_linearIndependent (n : ℕ) :
    LinearIndependent ℂ
      (fun u : PauliSupportIndex n => (hermitianSupportPauli u).toCMatrix) := by
  rw [Fintype.linearIndependent_iff]
  intro c hc u
  have htrace := congrArg
    (fun A : CMatrix (2 ^ n) (2 ^ n) =>
      Matrix.trace ((hermitianSupportPauli u)⁻¹.toCMatrix * A)) hc
  simp only [Matrix.mul_zero, Matrix.trace_zero] at htrace
  rw [Matrix.mul_sum] at htrace
  simp only [Matrix.mul_smul, Matrix.trace_sum, Matrix.trace_smul,
    trace_inv_mul_hermitianSupportPauli] at htrace
  have hcu : c u * ((2 ^ n : ℕ) : ℂ) = 0 := by
    simpa using htrace
  exact (mul_eq_zero.mp hcu).resolve_right (by norm_num)

/-- The support index has exactly the dimension of the `2^n × 2^n`
complex matrix algebra. -/
theorem card_pauliSupportIndex_eq_finrank_matrix (n : ℕ) :
    Fintype.card (PauliSupportIndex n) =
      Module.finrank ℂ (CMatrix (2 ^ n) (2 ^ n)) := by
  have hcard : Fintype.card (BitVec n) = 2 ^ n := by
    rw [← FinEnum.card_eq_fintypeCard]
    exact FinEnum.card_bitVec n
  rw [Fintype.card_prod, hcard]
  simp [Module.finrank_matrix, pow_two, pow_add, Nat.mul_comm]

/-- The phase-clean Hermitian Pauli matrices, now packaged as an actual
complex basis of all matrices. -/
noncomputable def hermitianPauliMatrixBasis (n : ℕ) :
    Basis (PauliSupportIndex n) ℂ (CMatrix (2 ^ n) (2 ^ n)) :=
  basisOfLinearIndependentOfCardEqFinrank
    (hermitianSupportPauli_matrix_linearIndependent n)
    (card_pauliSupportIndex_eq_finrank_matrix n)

@[simp]
theorem hermitianPauliMatrixBasis_apply (n : ℕ) (u : PauliSupportIndex n) :
    hermitianPauliMatrixBasis n u = (hermitianSupportPauli u).toCMatrix := by
  exact congrFun
    (coe_basisOfLinearIndependentOfCardEqFinrank
      (hermitianSupportPauli_matrix_linearIndependent n)
      (card_pauliSupportIndex_eq_finrank_matrix n)) u

/-- The same basis vectors viewed in the real self-adjoint carrier. -/
def hermitianPauliHermitianAtom {n : ℕ} (u : PauliSupportIndex n) :
    HermitianMatrixReal (2 ^ n) :=
  ⟨(hermitianSupportPauli u).toCMatrix,
    (hermitianSupportPauli_matrix_isHermitian u).eq⟩

@[simp]
theorem coe_hermitianPauliHermitianAtom {n : ℕ} (u : PauliSupportIndex n) :
    (hermitianPauliHermitianAtom u : CMatrix (2 ^ n) (2 ^ n)) =
      (hermitianSupportPauli u).toCMatrix := rfl

/-- Taking real parts of the complex Pauli-basis coordinates reconstructs a
self-adjoint matrix with real coefficients.  This is the load-bearing bridge
from the complex matrix basis to the real Hermitian carrier. -/
theorem sum_re_hermitianPauliMatrixBasis_repr (n : ℕ)
    (A : HermitianMatrixReal (2 ^ n)) :
    ∑ u : PauliSupportIndex n,
        ((hermitianPauliMatrixBasis n).repr
          (A : CMatrix (2 ^ n) (2 ^ n)) u).re •
          hermitianPauliHermitianAtom u = A := by
  have hreal (u : PauliSupportIndex n) :
      realPart (hermitianSupportPauli u).toCMatrix =
        hermitianPauliHermitianAtom u := by
    apply Subtype.ext
    exact IsSelfAdjoint.coe_realPart
      (hermitianSupportPauli_matrix_isHermitian u)
  have himag (u : PauliSupportIndex n) :
      imaginaryPart (hermitianSupportPauli u).toCMatrix = 0 :=
    IsSelfAdjoint.imaginaryPart
      (hermitianSupportPauli_matrix_isHermitian u)
  have h := congrArg
    (fun M : CMatrix (2 ^ n) (2 ^ n) =>
      (realPart M : HermitianMatrixReal (2 ^ n)))
    ((hermitianPauliMatrixBasis n).sum_repr
      (A : CMatrix (2 ^ n) (2 ^ n)))
  simpa [map_sum, realPart_smul, hreal, himag] using h

/-- The phase-clean Hermitian Pauli matrices span the entire self-adjoint
matrix carrier over the reals. -/
theorem hermitianPauliHermitianAtom_real_span_eq_top (n : ℕ) :
    Submodule.span ℝ
        (Set.range (hermitianPauliHermitianAtom (n := n))) = ⊤ := by
  apply top_unique
  intro A _
  refine (Submodule.mem_span_range_iff_exists_fun ℝ).2 ?_
  refine ⟨fun u => ((hermitianPauliMatrixBasis n).repr
    (A : CMatrix (2 ^ n) (2 ^ n)) u).re, ?_⟩
  exact sum_re_hermitianPauliMatrixBasis_repr n A

end

end AgtXIv.Stabilizer
