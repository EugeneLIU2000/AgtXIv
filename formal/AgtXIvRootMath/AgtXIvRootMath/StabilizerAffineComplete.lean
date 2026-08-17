import AgtXIvRootMath.HermitianPauliBasis
import AgtXIvRootMath.ProductStabilizerFrames
import AgtXIvRootMath.StabilizerAtomMaps

/-!
# All-qubit affine completeness of stabilizer atoms

The proof uses only the explicit product-state subfamily of complete signed
Pauli frames.  It first proves that the six one-qubit projectors linearly span
the Hermitian carrier, then propagates their tensor products through the
phase-clean Hermitian Pauli basis.  Affine feasibility is a conclusion.
-/

namespace AgtXIv.Stabilizer

noncomputable section

open scoped BigOperators

/-- A Hermitian matrix has real trace, stated in the coercion form needed for
real affine coefficients. -/
theorem hermitian_trace_eq_coe_re {d : ℕ} (A : HermitianMatrixReal d) :
    (((Matrix.trace (A : CMatrix d d)).re : ℝ) : ℂ) =
      Matrix.trace (A : CMatrix d d) := by
  rw [← Complex.conj_eq_iff_re]
  simp only [starRingEnd_apply]
  rw [← Matrix.trace_conjTranspose]
  exact congrArg Matrix.trace A.property

/-- The six exact one-qubit stabilizer projectors linearly span every
Hermitian `2 × 2` matrix.  This is derived from their already proved affine
completeness on the trace-one slice. -/
theorem qubitStabilizerHermitianAtom_real_span_eq_top :
    Submodule.span ℝ (Set.range qubitStabilizerHermitianAtom) = ⊤ := by
  apply top_unique
  intro A _
  let a0 : HermitianMatrixReal 2 :=
    qubitStabilizerHermitianAtom .zPlus
  let r : ℝ := hermitianTraceReal 2 A
  let B : HermitianMatrixReal 2 := A + (1 - r) • a0
  have ha0Trace : Matrix.trace (a0 : CMatrix 2 2) = 1 := by
    exact pureStabilizerHermitianAtom_mem_traceOne
      qubitStabilizerFrame QubitStabilizerAtom.zPlus
  have hATrace : Matrix.trace (A : CMatrix 2 2) = (r : ℂ) := by
    exact (hermitian_trace_eq_coe_re A).symm
  have hBTrace : Matrix.trace (B : CMatrix 2 2) = 1 := by
    change Matrix.trace
      ((A : CMatrix 2 2) + ((1 - r : ℝ) : ℂ) • (a0 : CMatrix 2 2)) = 1
    rw [Matrix.trace_add, Matrix.trace_smul, hATrace, ha0Trace]
    push_cast
    ring
  have hBaff : B ∈ affineSpan ℝ (Set.range qubitStabilizerHermitianAtom) := by
    rw [qubit_stabilizerAffineSpan_eq_traceOne]
    exact hBTrace
  have hBspan : B ∈ Submodule.span ℝ
      (Set.range qubitStabilizerHermitianAtom) :=
    affineSpan_subset_span hBaff
  have ha0span : a0 ∈ Submodule.span ℝ
      (Set.range qubitStabilizerHermitianAtom) := by
    apply Submodule.subset_span
    exact ⟨QubitStabilizerAtom.zPlus, rfl⟩
  have hAeq : A = B - (1 - r) • a0 := by
    simp [B]
  rw [hAeq]
  exact Submodule.sub_mem _ hBspan (Submodule.smul_mem _ _ ha0span)

/-- Tensor a one-qubit Hermitian matrix onto an `n`-qubit Hermitian matrix,
using the same index convention as the Pauli evaluator. -/
def hermitianPrependTensor {n : ℕ} (A : HermitianMatrixReal 2)
    (B : HermitianMatrixReal (2 ^ n)) :
    HermitianMatrixReal (2 ^ (n + 1)) :=
  ⟨StandardFrame.prependTensor (A : CMatrix 2 2)
      (B : CMatrix (2 ^ n) (2 ^ n)), by
    change Matrix.conjTranspose
        (StandardFrame.prependTensor (A : CMatrix 2 2)
          (B : CMatrix (2 ^ n) (2 ^ n))) =
      StandardFrame.prependTensor (A : CMatrix 2 2)
        (B : CMatrix (2 ^ n) (2 ^ n))
    unfold StandardFrame.prependTensor
    simp only [Matrix.reindexAlgEquiv_apply]
    rw [Matrix.conjTranspose_reindex, Matrix.conjTranspose_kron]
    have hA : Matrix.conjTranspose (A : CMatrix 2 2) =
        (A : CMatrix 2 2) := A.property
    have hB : Matrix.conjTranspose (B : CMatrix (2 ^ n) (2 ^ n)) =
        (B : CMatrix (2 ^ n) (2 ^ n)) := B.property
    rw [hA, hB]⟩

@[simp]
theorem coe_hermitianPrependTensor {n : ℕ} (A : HermitianMatrixReal 2)
    (B : HermitianMatrixReal (2 ^ n)) :
    (hermitianPrependTensor A B : CMatrix (2 ^ (n + 1)) (2 ^ (n + 1))) =
      StandardFrame.prependTensor (A : CMatrix 2 2)
        (B : CMatrix (2 ^ n) (2 ^ n)) := rfl

theorem hermitianPrependTensor_zero_left {n : ℕ}
    (B : HermitianMatrixReal (2 ^ n)) :
    hermitianPrependTensor 0 B = 0 := by
  apply Subtype.ext
  simp [hermitianPrependTensor, StandardFrame.prependTensor]

theorem hermitianPrependTensor_zero_right {n : ℕ}
    (A : HermitianMatrixReal 2) :
    hermitianPrependTensor A (0 : HermitianMatrixReal (2 ^ n)) =
      (0 : HermitianMatrixReal (2 ^ (n + 1))) := by
  apply Subtype.ext
  simp [hermitianPrependTensor, StandardFrame.prependTensor]

theorem hermitianPrependTensor_add_left {n : ℕ}
    (A B : HermitianMatrixReal 2) (C : HermitianMatrixReal (2 ^ n)) :
    hermitianPrependTensor (A + B) C =
      hermitianPrependTensor A C + hermitianPrependTensor B C := by
  apply Subtype.ext
  exact prependTensor_add_left _ _ _

theorem hermitianPrependTensor_add_right {n : ℕ}
    (A : HermitianMatrixReal 2) (B C : HermitianMatrixReal (2 ^ n)) :
    hermitianPrependTensor A (B + C) =
      hermitianPrependTensor A B + hermitianPrependTensor A C := by
  apply Subtype.ext
  exact prependTensor_add_right _ _ _

theorem hermitianPrependTensor_smul_left {n : ℕ} (r : ℝ)
    (A : HermitianMatrixReal 2) (B : HermitianMatrixReal (2 ^ n)) :
    hermitianPrependTensor (r • A) B = r • hermitianPrependTensor A B := by
  apply Subtype.ext
  change StandardFrame.prependTensor
      ((r : ℂ) • (A : CMatrix 2 2)) (B : CMatrix (2 ^ n) (2 ^ n)) =
    (r : ℂ) • StandardFrame.prependTensor
      (A : CMatrix 2 2) (B : CMatrix (2 ^ n) (2 ^ n))
  unfold StandardFrame.prependTensor
  rw [Matrix.smul_kron, map_smul]

theorem hermitianPrependTensor_smul_right {n : ℕ} (r : ℝ)
    (A : HermitianMatrixReal 2) (B : HermitianMatrixReal (2 ^ n)) :
    hermitianPrependTensor A (r • B) = r • hermitianPrependTensor A B := by
  apply Subtype.ext
  change StandardFrame.prependTensor
      (A : CMatrix 2 2) ((r : ℂ) • (B : CMatrix (2 ^ n) (2 ^ n))) =
    (r : ℂ) • StandardFrame.prependTensor
      (A : CMatrix 2 2) (B : CMatrix (2 ^ n) (2 ^ n))
  unfold StandardFrame.prependTensor
  rw [Matrix.kron_smul, map_smul]

/-- Bilinearity plus the explicit product-frame recursion sends the local and
tail stabilizer spans into the next product-stabilizer span. -/
theorem hermitianPrependTensor_mem_productStabilizer_span {n : ℕ}
    {A : HermitianMatrixReal 2} {B : HermitianMatrixReal (2 ^ n)}
    (hA : A ∈ Submodule.span ℝ (Set.range qubitStabilizerHermitianAtom))
    (hB : B ∈ Submodule.span ℝ
      (Set.range (productStabilizerHermitianAtom n))) :
    hermitianPrependTensor A B ∈ Submodule.span ℝ
      (Set.range (productStabilizerHermitianAtom (n + 1))) := by
  induction hA, hB using Submodule.span_induction₂ with
  | mem_mem A B hA hB =>
      rcases hA with ⟨a, rfl⟩
      rcases hB with ⟨b, rfl⟩
      apply Submodule.subset_span
      refine ⟨(a, b), ?_⟩
      apply Subtype.ext
      exact productStabilizerHermitianAtom_succ n (a, b)
  | zero_left B _ =>
      rw [hermitianPrependTensor_zero_left]
      exact Submodule.zero_mem _
  | zero_right A _ =>
      rw [hermitianPrependTensor_zero_right]
      exact Submodule.zero_mem _
  | add_left A B C _ _ _ hAC hBC =>
      rw [hermitianPrependTensor_add_left]
      exact Submodule.add_mem _ hAC hBC
  | add_right A B C _ _ _ hAB hAC =>
      rw [hermitianPrependTensor_add_right]
      exact Submodule.add_mem _ hAB hAC
  | smul_left r A B _ _ hAB =>
      have heq : hermitianPrependTensor (r • A) B =
          r • hermitianPrependTensor A B :=
        hermitianPrependTensor_smul_left (n := n) r A B
      exact heq.symm ▸ Submodule.smul_mem _ r hAB
  | smul_right r A B _ _ hAB =>
      have heq : hermitianPrependTensor A (r • B) =
          r • hermitianPrependTensor A B :=
        hermitianPrependTensor_smul_right (n := n) r A B
      exact heq.symm ▸ Submodule.smul_mem _ r hAB

theorem zmod4_eq_or_eq_add_two_of_two_mul_eq (a b : ZMod 4)
    (h : 2 * a = 2 * b) : a = b ∨ a = b + 2 := by
  exact (by decide : ∀ a b : ZMod 4,
    2 * a = 2 * b → a = b ∨ a = b + 2) a b h

/-- Two involutive signed Paulis with identical binary support differ by at
most a real sign.  The involutivity hypothesis excludes the `±i` ambiguity. -/
theorem pauli_eq_or_eq_neg_of_same_support_of_sq_one {n : ℕ}
    (P Q : Pauli n) (hz : P.z = Q.z) (hx : P.x = Q.x)
    (hP : P ^ 2 = 1) (hQ : Q ^ 2 = 1) : P = Q ∨ P = -Q := by
  have hflip : P.phaseFlipsWith P = Q.phaseFlipsWith Q := by
    simp only [Pauli.phaseFlipsWith]
    rw [hz, hx]
  have hPm : 2 * P.m + (P.phaseFlipsWith P).toNat * 2 = 0 := by
    have h := congrArg Pauli.m hP
    simpa [Pauli.pow_two] using h
  have hQm : 2 * Q.m + (P.phaseFlipsWith P).toNat * 2 = 0 := by
    have h := congrArg Pauli.m hQ
    simpa [Pauli.pow_two, ← hflip] using h
  have htwo : 2 * P.m = 2 * Q.m := by
    apply add_right_cancel
    exact hPm.trans hQm.symm
  rcases zmod4_eq_or_eq_add_two_of_two_mul_eq P.m Q.m htwo with hm | hm
  · left
    apply Pauli.ext <;> simp [hm, hz, hx]
  · right
    apply Pauli.ext <;> simp [hm, hz, hx, add_comm]

/-- The leading one-qubit support of an all-qubit Pauli support. -/
def pauliSupportHead {n : ℕ} (u : PauliSupportIndex (n + 1)) :
    PauliSupportIndex 1 :=
  (BitVec.cons u.1.msb (0 : BitVec 0),
    BitVec.cons u.2.msb (0 : BitVec 0))

/-- The remaining support after removing the leading qubit. -/
def pauliSupportTail {n : ℕ} (u : PauliSupportIndex (n + 1)) :
    PauliSupportIndex n :=
  (u.1.lsbs, u.2.lsbs)

@[simp]
theorem pauliSupportHead_z_msb {n : ℕ}
    (u : PauliSupportIndex (n + 1)) :
    (pauliSupportHead u).1.msb = u.1.msb := by
  simp [pauliSupportHead]

@[simp]
theorem pauliSupportHead_x_msb {n : ℕ}
    (u : PauliSupportIndex (n + 1)) :
    (pauliSupportHead u).2.msb = u.2.msb := by
  simp [pauliSupportHead]

/-- The support selected by the global Hermitian Pauli basis is the
head/tail concatenation of the corresponding local support selections. -/
theorem hermitianSupportPauli_prepend_same_support {n : ℕ}
    (u : PauliSupportIndex (n + 1)) :
    (hermitianSupportPauli u).z =
        (prependPauli (hermitianSupportPauli (pauliSupportHead u))
          (hermitianSupportPauli (pauliSupportTail u))).z ∧
      (hermitianSupportPauli u).x =
        (prependPauli (hermitianSupportPauli (pauliSupportHead u))
          (hermitianSupportPauli (pauliSupportTail u))).x := by
  constructor
  · simp only [hermitianSupportPauli_z, prependPauli_z,
      pauliSupportHead_z_msb]
    exact (BitVec.cons_msb_lsbs u.1).symm
  · simp only [hermitianSupportPauli_x, prependPauli_x,
      pauliSupportHead_x_msb]
    exact (BitVec.cons_msb_lsbs u.2).symm

/-- Concatenating two involutive signed Paulis on disjoint tensor factors is
again involutive. -/
theorem prependPauli_sq_of_sq_one {n : ℕ} (P : Pauli 1) (Q : Pauli n)
    (hP : P ^ 2 = 1) (hQ : Q ^ 2 = 1) :
    prependPauli P Q ^ 2 = 1 := by
  rw [pow_two, ← prependPauli_mul, ← pow_two, hP, ← pow_two, hQ,
    prependPauli_one]

/-- Every Hermitian Pauli basis element belongs to the real span of the
explicit product stabilizer projectors.  No classification of arbitrary
maximal frames is required: the product-state subfamily already spans. -/
theorem hermitianPauliHermitianAtom_mem_productStabilizer_span :
    ∀ (n : ℕ) (u : PauliSupportIndex n),
      hermitianPauliHermitianAtom u ∈
        Submodule.span ℝ (Set.range (productStabilizerHermitianAtom n))
  | 0, u => by
      have hu : u = ((0 : BitVec 0), (0 : BitVec 0)) :=
        Subsingleton.elim _ _
      subst u
      apply Submodule.subset_span
      refine ⟨PUnit.unit, ?_⟩
      apply Subtype.ext
      change stabilizerProjectorMatrix (standardIndependentZFrame 0) =
        (hermitianSupportPauli ((0 : BitVec 0), (0 : BitVec 0))).toCMatrix
      rw [stabilizerProjectorMatrix_standard_eq_computationalZeroProjector]
      have hPauli :
          hermitianSupportPauli ((0 : BitVec 0), (0 : BitVec 0)) =
            (1 : Pauli 0) := by
        apply Pauli.ext <;>
          simp [hermitianSupportPauli, supportZeroPauli,
            Pauli.phaseFlipsWith, Pauli.one_def]
      rw [hPauli, Pauli.one_toCMatrix]
      ext i j
      fin_cases i
      fin_cases j
      norm_num [computationalZeroProjector, computationalZeroKet]
  | n + 1, u => by
      let uh : PauliSupportIndex 1 := pauliSupportHead u
      let ut : PauliSupportIndex n := pauliSupportTail u
      have hLocal : hermitianPauliHermitianAtom uh ∈
          Submodule.span ℝ (Set.range qubitStabilizerHermitianAtom) := by
        rw [qubitStabilizerHermitianAtom_real_span_eq_top]
        trivial
      have hTail : hermitianPauliHermitianAtom ut ∈
          Submodule.span ℝ
            (Set.range (productStabilizerHermitianAtom n)) :=
        hermitianPauliHermitianAtom_mem_productStabilizer_span n ut
      have hTensor :
          hermitianPrependTensor
              (hermitianPauliHermitianAtom uh)
              (hermitianPauliHermitianAtom ut) ∈
            Submodule.span ℝ
              (Set.range (productStabilizerHermitianAtom (n + 1))) :=
        hermitianPrependTensor_mem_productStabilizer_span hLocal hTail
      let P : Pauli (n + 1) := hermitianSupportPauli u
      let Q : Pauli (n + 1) :=
        prependPauli (hermitianSupportPauli uh) (hermitianSupportPauli ut)
      have hsupport : P.z = Q.z ∧ P.x = Q.x := by
        simpa [P, Q, uh, ut] using
          hermitianSupportPauli_prepend_same_support u
      have hPsq : P ^ 2 = 1 := by
        simpa [P] using hermitianSupportPauli_sq u
      have hQsq : Q ^ 2 = 1 := by
        exact prependPauli_sq_of_sq_one _ _
          (hermitianSupportPauli_sq uh) (hermitianSupportPauli_sq ut)
      rcases pauli_eq_or_eq_neg_of_same_support_of_sq_one
          P Q hsupport.1 hsupport.2 hPsq hQsq with hPQ | hPQ
      · have heq : hermitianPauliHermitianAtom u =
            hermitianPrependTensor
              (hermitianPauliHermitianAtom uh)
              (hermitianPauliHermitianAtom ut) := by
          apply Subtype.ext
          change P.toCMatrix =
            StandardFrame.prependTensor
              (hermitianSupportPauli uh).toCMatrix
              (hermitianSupportPauli ut).toCMatrix
          rw [← prependPauli_toCMatrix, hPQ]
        rw [heq]
        exact hTensor
      · have heq : hermitianPauliHermitianAtom u =
            -hermitianPrependTensor
              (hermitianPauliHermitianAtom uh)
              (hermitianPauliHermitianAtom ut) := by
          apply Subtype.ext
          change P.toCMatrix =
            -StandardFrame.prependTensor
              (hermitianSupportPauli uh).toCMatrix
              (hermitianSupportPauli ut).toCMatrix
          rw [← prependPauli_toCMatrix, hPQ, Pauli.toCMatrix_neg]
        rw [heq]
        exact Submodule.neg_mem _ hTensor

/-- The explicit `6^n` product stabilizer projectors span the full real vector
space of `n`-qubit Hermitian matrices.  The proof factors through the proved
Hermitian Pauli basis; no spanning hypothesis is stored in an atom type. -/
theorem productStabilizerHermitianAtom_real_span_eq_top (n : ℕ) :
    Submodule.span ℝ (Set.range (productStabilizerHermitianAtom n)) = ⊤ := by
  have hle :
      Submodule.span ℝ
          (Set.range (hermitianPauliHermitianAtom (n := n))) ≤
        Submodule.span ℝ
          (Set.range (productStabilizerHermitianAtom n)) := by
    apply Submodule.span_le.mpr
    rintro A ⟨u, rfl⟩
    exact hermitianPauliHermitianAtom_mem_productStabilizer_span n u
  rw [hermitianPauliHermitianAtom_real_span_eq_top n] at hle
  exact top_unique hle

@[simp]
theorem hermitianTraceReal_productStabilizerHermitianAtom (n : ℕ)
    (a : ProductStabilizerAtom n) :
    hermitianTraceReal (2 ^ n) (productStabilizerHermitianAtom n a) = 1 := by
  exact hermitianTraceReal_pureStabilizerHermitianAtom
    (productStabilizerFrame n) a

/-- Every trace-one Hermitian matrix is an affine combination of actual
product stabilizer projectors.  Coefficients are real and sum to one, but may
be negative; this is signed feasibility, not convex/free membership. -/
theorem traceOneHermitianAffine_le_productStabilizer_affineSpan (n : ℕ) :
    traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (productStabilizerHermitianAtom n)) := by
  intro A hA
  have hSpan : A ∈
      Submodule.span ℝ
        (Set.range (productStabilizerHermitianAtom n)) := by
    rw [productStabilizerHermitianAtom_real_span_eq_top n]
    trivial
  obtain ⟨c, hrec⟩ :=
    (Submodule.mem_span_range_iff_exists_fun ℝ).mp hSpan
  have hATraceReal : hermitianTraceReal (2 ^ n) A = 1 := by
    change (Matrix.trace (A : CMatrix (2 ^ n) (2 ^ n))).re = 1
    change Matrix.trace (A : CMatrix (2 ^ n) (2 ^ n)) = 1 at hA
    rw [hA]
    norm_num
  have hsum : ∑ a, c a = 1 := by
    have htrace := congrArg (hermitianTraceReal (2 ^ n)) hrec
    change hermitianTraceReal (2 ^ n)
        (∑ a, c a • productStabilizerHermitianAtom n a) =
      hermitianTraceReal (2 ^ n) A at htrace
    rw [map_sum, hATraceReal] at htrace
    simp only [map_smul,
      hermitianTraceReal_productStabilizerHermitianAtom,
      smul_eq_mul, mul_one] at htrace
    exact htrace
  have hmem : Finset.univ.affineCombination ℝ
      (productStabilizerHermitianAtom n) c ∈
        affineSpan ℝ (Set.range (productStabilizerHermitianAtom n)) := by
    apply affineCombination_mem_affineSpan
    simpa using hsum
  have hcomb : Finset.univ.affineCombination ℝ
      (productStabilizerHermitianAtom n) c = A := by
    rw [Finset.affineCombination_eq_linear_combination]
    · exact hrec
    · simpa using hsum
  rwa [hcomb] at hmem

/-- **Unconditional all-qubit affine completeness.**  The complete family of
phase-clean rank-`n` signed Pauli frame projectors affinely spans the entire
trace-one Hermitian slice.  The proof uses only its explicit product-state
subfamily, so no arbitrary-frame classification premise is hidden here. -/
theorem traceOneHermitianAffine_le_completeFrame_affineSpan (n : ℕ) :
    traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)) := by
  intro A hA
  have hProduct :=
    traceOneHermitianAffine_le_productStabilizer_affineSpan n hA
  apply (affineSpan_mono ℝ ?_) hProduct
  rintro B ⟨a, rfl⟩
  exact ⟨productStabilizerFrame n a, rfl⟩

end

end AgtXIv.Stabilizer
