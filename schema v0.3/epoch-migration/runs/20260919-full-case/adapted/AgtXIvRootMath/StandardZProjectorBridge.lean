import AgtXIvRootMath.StandardZIndependentFrame
import AgtXIvRootMath.StabilizerFrameProjector
import AgtXIvRootMath.GottesmanRankNProjector

/-!
# Identifying the two standard stabilizer projectors

The Gottesman branch constructs a pure state as the normalized average of the
binary signed-`Z` group.  The Veitch branch starts from the computational
projector `|0...0><0...0|`.  This file proves that these are the same matrix;
the identification is not made by definition.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix
noncomputable section

/-- Split a binary word into its most-significant coordinate and the remaining
initial word.  The order matches `BitVec.cons` and LeanQuantum's recursive
matrix evaluator. -/
def binaryWordSnocEquiv (n : ℕ) :
    StandardF2 × BinaryWord n ≃ BinaryWord (n + 1) where
  toFun p := Multiplicative.ofAdd (Fin.snoc p.2.toAdd p.1)
  invFun a :=
    (a.toAdd (Fin.last n), Multiplicative.ofAdd (Fin.init a.toAdd))
  left_inv p := by
    rcases p with ⟨b, a⟩
    apply Prod.ext
    · simp
    · apply Multiplicative.toAdd.injective
      simp
  right_inv a := by
    apply Multiplicative.toAdd.injective
    exact Fin.snoc_init_self a.toAdd

@[simp] theorem binaryWordSnocEquiv_apply (n : ℕ)
    (b : StandardF2) (a : BinaryWord n) :
    binaryWordSnocEquiv n (b, a) =
      Multiplicative.ofAdd (Fin.snoc a.toAdd b) := rfl

theorem bitVecOfF2Fun_snoc {n : ℕ} (a : Fin n → StandardF2)
    (b : StandardF2) :
    bitVecOfF2Fun (Fin.snoc a b) =
      BitVec.cons (boolOfStandardF2 b) (bitVecOfF2Fun a) := by
  apply BitVec.eq_of_getLsbD_eq
  intro i
  intro hiWidth
  rw [getLsbD_bitVecOfF2Fun, BitVec.getLsbD_cons]
  rw [getLsbD_bitVecOfF2Fun]
  by_cases hi : i < n
  · have hine : i ≠ n := by omega
    simp [hi, hiWidth, hine, Fin.snoc]
  · have hilast : i = n := by omega
    subst i
    simp [Fin.snoc]

theorem standardZEval_snoc {n : ℕ} (b : StandardF2)
    (a : BinaryWord n) :
    standardZEval (binaryWordSnocEquiv n (b, a)) =
      Pauli.cons (boolOfStandardF2 b) false (standardZEval a) := by
  apply Pauli.ext
  · simp [standardZEval, Pauli.cons]
  · simp [standardZEval, Pauli.cons, bitVecOfF2Fun_snoc]
  · simp [standardZEval, Pauli.cons]

/-- Summation over the two-element field in its canonical order. -/
theorem sum_standardF2 {M : Type*} [AddCommMonoid M]
    (f : StandardF2 → M) :
    ∑ b : StandardF2, f b = f 0 + f 1 := by
  have hUniv : (Finset.univ : Finset StandardF2) = {0, 1} := by decide
  rw [show Finset.univ = ({0, 1} : Finset StandardF2) from hUniv]
  rw [Finset.sum_insert]
  · simp
  · decide

/-- The unnormalized standard signed-`Z` group sum obeys the same tensor
recursion as the product of its spectral filters. -/
theorem sum_standardZEval_succ (n : ℕ) :
    (∑ a : BinaryWord (n + 1), (standardZEval a).toCMatrix) =
      StandardFrame.prependTensor
        ((1 : CMatrix 2 2) + Pauli.Z.toCMatrix)
        (∑ a : BinaryWord n, (standardZEval a).toCMatrix) := by
  rw [Fintype.sum_equiv (binaryWordSnocEquiv n).symm
    (fun a : BinaryWord (n + 1) => (standardZEval a).toCMatrix)
    (fun p : StandardF2 × BinaryWord n =>
      (standardZEval (binaryWordSnocEquiv n p)).toCMatrix)]
  · rw [Fintype.sum_prod_type]
    rw [sum_standardF2]
    simp only [standardZEval_snoc]
    simp only [boolOfStandardF2]
    norm_num
    simp_rw [StandardFrame.toCMatrix_cons]
    simp only [Pauli.toCMatrix.bitsToMat]
    ext i j
    simp only [StandardFrame.prependTensor, Matrix.reindexAlgEquiv_apply,
      Matrix.reindex_apply, Matrix.submatrix_apply, Matrix.kron_apply,
      Matrix.add_apply, Matrix.one_apply, Matrix.sum_apply]
    rw [← Finset.mul_sum, ← Finset.mul_sum]
    simp [Pauli.toCMatrix.bitsToMat]
    simp only [Matrix.one_apply]
    split_ifs <;> ring
  · intro a
    simp

theorem complex_inv_two_pow_succ (n : ℕ) :
    (((2 ^ (n + 1) : ℕ) : ℂ))⁻¹ =
      (2 : ℂ)⁻¹ * (((2 ^ n : ℕ) : ℂ))⁻¹ := by
  push_cast
  rw [pow_succ]
  field_simp

/-- The normalized standard group average satisfies the same tensor recursion
as the independently defined standard filter product. -/
theorem stabilizerProjectorMatrix_standard_succ (n : ℕ) :
    stabilizerProjectorMatrix (standardIndependentZFrame (n + 1)) =
      StandardFrame.prependTensor (pauliFilter Pauli.Z)
        (stabilizerProjectorMatrix (standardIndependentZFrame n)) := by
  unfold stabilizerProjectorMatrix
  rw [invOf_eq_inv, invOf_eq_inv]
  rw [AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card,
    AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card]
  simp only [standardIndependentZFrame_eval]
  rw [sum_standardZEval_succ, complex_inv_two_pow_succ]
  ext i j
  simp only [StandardFrame.prependTensor, Matrix.reindexAlgEquiv_apply,
    Matrix.reindex_apply, Matrix.submatrix_apply, Matrix.kron_apply,
    Matrix.smul_apply, pauliFilter]
  simp only [Matrix.add_apply, smul_eq_mul]
  ring

/-- The standard Gottesman group average and the raw standard filter product
are extensionally equal for every qubit count. -/
theorem stabilizerProjectorMatrix_standard_eq_standardZProjector (n : ℕ) :
    stabilizerProjectorMatrix (standardIndependentZFrame n) =
      standardZProjector n := by
  induction n with
  | zero =>
      have hEval : ∀ a : BinaryWord 0, standardZEval a = 1 := by
        intro a
        rw [Subsingleton.elim a 1]
        exact standardZEval_one
      unfold stabilizerProjectorMatrix
      rw [invOf_eq_inv]
      simp_rw [standardIndependentZFrame_eval, hEval]
      norm_num [AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card,
        standardZProjector, standardZFrame, standardZGenerators, frameProjector]
  | succ n ih =>
      rw [stabilizerProjectorMatrix_standard_succ,
        StandardFrame.standardZProjector_succ, ih]

/-- The common source object: the normalized binary signed-`Z` group average
is exactly the computational-basis pure state projector. -/
theorem stabilizerProjectorMatrix_standard_eq_computationalZeroProjector
    (n : ℕ) :
    stabilizerProjectorMatrix (standardIndependentZFrame n) =
      computationalZeroProjector n := by
  rw [stabilizerProjectorMatrix_standard_eq_standardZProjector,
    StandardFrame.standardZProjector_eq_computationalZeroProjector]

end

end AgtXIv.Stabilizer
