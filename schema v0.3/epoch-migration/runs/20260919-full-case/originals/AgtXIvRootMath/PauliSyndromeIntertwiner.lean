import AgtXIvRootMath.PauliSyndromeData

/-!
# Unitary intertwiners between complete signed Pauli frames

The normalized syndrome bases constructed for two complete signed Pauli
frames have the same binary labels.  Their change-of-basis matrix is unitary
and maps each source syndrome vector to the identically labelled target
vector.  Consequently it conjugates every exact signed read word and every
constructed exact signed flip word.

This is the unitary core of frame transitivity.  It derives the unitary from
the syndrome bases and does not assume a Clifford-normalizer witness.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix
noncomputable section
set_option maxHeartbeats 800000

namespace SyndromeBasisData

variable {iota : Type*} [Fintype iota] {d : ℕ}

/-- A syndrome state is the corresponding column of its basis matrix. -/
theorem state_eq_matrix_mulVec_single
    (D : SyndromeBasisData iota d) (b : iota) :
    D.state b = D.matrix *ᵥ Pi.single (D.basisIndex b) 1 := by
  rw [Matrix.mulVec_single_one]
  funext row
  exact (D.matrix_column b row).symm

/-- Equality on every syndrome state determines a matrix, because the
syndrome-state matrix is unitary. -/
theorem matrix_eq_of_mulVec_state_eq
    (D : SyndromeBasisData iota d) (M N : CMatrix d d)
    (h : ∀ b, M *ᵥ D.state b = N *ᵥ D.state b) : M = N := by
  have hprod : M * D.matrix = N * D.matrix := by
    ext row col
    let b := D.basisIndex.symm col
    have hb := congrFun (h b) row
    simpa [Matrix.mul_apply, SyndromeBasisData.matrix, b] using hb
  have hright : D.matrix * D.matrixᴴ = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff] using D.matrix_unitary
  calc
    M = M * (D.matrix * D.matrixᴴ) := by rw [hright]; simp
    _ = (M * D.matrix) * D.matrixᴴ := by rw [Matrix.mul_assoc]
    _ = (N * D.matrix) * D.matrixᴴ := by rw [hprod]
    _ = N * (D.matrix * D.matrixᴴ) := by rw [Matrix.mul_assoc]
    _ = N := by rw [hright]; simp

end SyndromeBasisData

namespace IndependentSignedPauliFrame

variable {n : ℕ}

/-- Change of syndrome basis from frame `A` to frame `F`. -/
def frameChangeMatrix (A F : IndependentSignedPauliFrame n n) :
    CMatrix (2 ^ n) (2 ^ n) :=
  F.syndromeBasisData.matrix * A.syndromeBasisData.matrixᴴ

theorem frameChangeMatrix_unitary (A F : IndependentSignedPauliFrame n n) :
    (frameChangeMatrix A F).IsUnitary :=
  Matrix.mul_of_isUnitary _ _ F.syndromeBasisData.matrix_unitary
    (Matrix.conjTranspose_of_isUnitary _ A.syndromeBasisData.matrix_unitary)

/-- The change-of-basis unitary preserves the complete binary syndrome
label, including the coherent phases fixed by the common vacuum and dual
words. -/
theorem frameChangeMatrix_state (A F : IndependentSignedPauliFrame n n)
    (b : BinaryWord n) :
    frameChangeMatrix A F *ᵥ A.syndromeBasisData.state b =
      F.syndromeBasisData.state b := by
  let e : Fin (2 ^ n) → ℂ := Pi.single (binaryWordIndexEquiv n b) 1
  have hA : A.syndromeBasisData.state b =
      A.syndromeBasisData.matrix *ᵥ e := by
    exact A.syndromeBasisData.state_eq_matrix_mulVec_single b
  have hF : F.syndromeBasisData.state b =
      F.syndromeBasisData.matrix *ᵥ e := by
    exact F.syndromeBasisData.state_eq_matrix_mulVec_single b
  have hleft : A.syndromeBasisData.matrixᴴ * A.syndromeBasisData.matrix = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff'] using
      A.syndromeBasisData.matrix_unitary
  rw [hA, hF, frameChangeMatrix, Matrix.mulVec_mulVec]
  congr 1
  rw [Matrix.mul_assoc, hleft, Matrix.mul_one]

theorem frameChangeMatrix_read_intertwines
    (A F : IndependentSignedPauliFrame n n) (a : BinaryWord n) :
    frameChangeMatrix A F * (A.eval a).toCMatrix =
      (F.eval a).toCMatrix * frameChangeMatrix A F := by
  apply A.syndromeBasisData.matrix_eq_of_mulVec_state_eq
  intro b
  calc
    (frameChangeMatrix A F * (A.eval a).toCMatrix) *ᵥ
        A.syndromeBasisData.state b =
      frameChangeMatrix A F *ᵥ
        ((A.eval a).toCMatrix *ᵥ A.syndromeBasisData.state b) := by
          rw [Matrix.mulVec_mulVec]
    _ = frameChangeMatrix A F *ᵥ
        (binaryPhase a b • A.syndromeBasisData.state b) := by
          have hread := A.syndromeBasisData.read_state a b
          simpa [syndromeBasisData] using
            congrArg (fun v => frameChangeMatrix A F *ᵥ v) hread
    _ = binaryPhase a b • F.syndromeBasisData.state b := by
          rw [Matrix.mulVec_smul, frameChangeMatrix_state]
    _ = (F.eval a).toCMatrix *ᵥ F.syndromeBasisData.state b := by
          simpa [syndromeBasisData] using
            (F.syndromeBasisData.read_state a b).symm
    _ = (F.eval a).toCMatrix *ᵥ
        (frameChangeMatrix A F *ᵥ A.syndromeBasisData.state b) := by
          rw [frameChangeMatrix_state]
    _ = ((F.eval a).toCMatrix * frameChangeMatrix A F) *ᵥ
        A.syndromeBasisData.state b := Matrix.mulVec_mulVec _ _ _

/-- Exact signed read-word conjugation. -/
theorem frameChangeMatrix_read_conjugates
    (A F : IndependentSignedPauliFrame n n) (a : BinaryWord n) :
    frameChangeMatrix A F * (A.eval a).toCMatrix *
        (frameChangeMatrix A F)ᴴ =
      (F.eval a).toCMatrix := by
  have hright : frameChangeMatrix A F * (frameChangeMatrix A F)ᴴ = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff] using
      frameChangeMatrix_unitary A F
  rw [frameChangeMatrix_read_intertwines]
  calc
    (F.eval a).toCMatrix * frameChangeMatrix A F *
        (frameChangeMatrix A F)ᴴ =
      (F.eval a).toCMatrix *
        (frameChangeMatrix A F * (frameChangeMatrix A F)ᴴ) := by
          rw [Matrix.mul_assoc]
    _ = (F.eval a).toCMatrix := by rw [hright]; simp

/-- A dual word shifts the binary syndrome label by group multiplication. -/
theorem syndrome_flip_state (F : IndependentSignedPauliFrame n n)
    (a b : BinaryWord n) :
    (F.dualFrame.eval a).toCMatrix *ᵥ F.syndromeBasisData.state b =
      F.syndromeBasisData.state (a * b) := by
  unfold SyndromeBasisData.state syndromeBasisData
  rw [Matrix.mulVec_mulVec]
  rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
  rw [← F.dualFrame.eval.map_mul]

theorem frameChangeMatrix_flip_intertwines
    (A F : IndependentSignedPauliFrame n n) (a : BinaryWord n) :
    frameChangeMatrix A F * (A.dualFrame.eval a).toCMatrix =
      (F.dualFrame.eval a).toCMatrix * frameChangeMatrix A F := by
  apply A.syndromeBasisData.matrix_eq_of_mulVec_state_eq
  intro b
  calc
    (frameChangeMatrix A F * (A.dualFrame.eval a).toCMatrix) *ᵥ
        A.syndromeBasisData.state b =
      frameChangeMatrix A F *ᵥ
        ((A.dualFrame.eval a).toCMatrix *ᵥ
          A.syndromeBasisData.state b) := by
            rw [Matrix.mulVec_mulVec]
    _ = frameChangeMatrix A F *ᵥ A.syndromeBasisData.state (a * b) := by
          rw [A.syndrome_flip_state]
    _ = F.syndromeBasisData.state (a * b) := frameChangeMatrix_state A F _
    _ = (F.dualFrame.eval a).toCMatrix *ᵥ
        F.syndromeBasisData.state b := (F.syndrome_flip_state a b).symm
    _ = (F.dualFrame.eval a).toCMatrix *ᵥ
        (frameChangeMatrix A F *ᵥ A.syndromeBasisData.state b) := by
          rw [frameChangeMatrix_state]
    _ = ((F.dualFrame.eval a).toCMatrix * frameChangeMatrix A F) *ᵥ
        A.syndromeBasisData.state b := Matrix.mulVec_mulVec _ _ _

/-- Exact signed flip-word conjugation. -/
theorem frameChangeMatrix_flip_conjugates
    (A F : IndependentSignedPauliFrame n n) (a : BinaryWord n) :
    frameChangeMatrix A F * (A.dualFrame.eval a).toCMatrix *
        (frameChangeMatrix A F)ᴴ =
      (F.dualFrame.eval a).toCMatrix := by
  have hright : frameChangeMatrix A F * (frameChangeMatrix A F)ᴴ = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff] using
      frameChangeMatrix_unitary A F
  rw [frameChangeMatrix_flip_intertwines]
  calc
    (F.dualFrame.eval a).toCMatrix * frameChangeMatrix A F *
        (frameChangeMatrix A F)ᴴ =
      (F.dualFrame.eval a).toCMatrix *
        (frameChangeMatrix A F * (frameChangeMatrix A F)ᴴ) := by
          rw [Matrix.mul_assoc]
    _ = (F.dualFrame.eval a).toCMatrix := by rw [hright]; simp

end IndependentSignedPauliFrame

end
end AgtXIv.Stabilizer
