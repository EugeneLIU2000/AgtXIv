import AgtXIvRootMath.GottesmanGeneralRankDimension
import AgtXIvRootMath.PauliAdjoint
import Mathlib.Analysis.Matrix.PosDef
import Mathlib.LinearAlgebra.Matrix.Rank

/-!
# The projector of a general-rank stabilizer code

For `r ≤ n` independent commuting phase-clean signed Pauli generators, the
normalized group sum is the orthogonal positive-semidefinite projector onto
their common fixed space.  Its trace and range dimension are `2 ^ (n-r)`.
No dimension, character, or projector property is stored in the frame.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators ComplexOrder

noncomputable section

variable {n r : ℕ}

/-- The normalized group average of a rank-`r` signed Pauli frame on `n`
qubits. -/
noncomputable def stabilizerCodeProjectorMatrix
    (F : IndependentSignedPauliFrame n r) : CMatrix (2 ^ n) (2 ^ n) :=
  ⅟(Fintype.card (BinaryWord r) : ℂ) •
    ∑ a : BinaryWord r, (F.eval a).toCMatrix

/-- The concrete matrix is the abstract group-average linear map. -/
theorem toLin_stabilizerCodeProjectorMatrix
    (F : IndependentSignedPauliFrame n r) :
    Matrix.toLin' (stabilizerCodeProjectorMatrix F) =
      AgtXIv.Gottesman.groupAverageMap F.generalRankFDRep.ρ := by
  ext v
  simp [stabilizerCodeProjectorMatrix,
    AgtXIv.Gottesman.groupAverageMap, Representation.averageMap,
    GroupAlgebra.average, IndependentSignedPauliFrame.generalRankFDRep,
    pauliMatrixRepresentation]

/-- The general stabilizer-code group average is Hermitian. -/
theorem stabilizerCodeProjectorMatrix_isHermitian
    (F : IndependentSignedPauliFrame n r) :
    (stabilizerCodeProjectorMatrix F).IsHermitian := by
  rw [Matrix.IsHermitian]
  simp only [stabilizerCodeProjectorMatrix, Matrix.conjTranspose_smul,
    Matrix.conjTranspose_sum]
  congr 1
  · simp
  · apply Finset.sum_congr rfl
    intro a _
    exact (pauli_toCMatrix_isHermitian_of_sq_eq_one
      (F.eval a) (F.eval_sq a)).eq

/-- The general stabilizer-code group average is idempotent. -/
theorem stabilizerCodeProjectorMatrix_idempotent
    (F : IndependentSignedPauliFrame n r) :
    stabilizerCodeProjectorMatrix F * stabilizerCodeProjectorMatrix F =
      stabilizerCodeProjectorMatrix F := by
  letI : Invertible (Fintype.card (BinaryWord r) : ℂ) :=
    invertibleOfNonzero (Nat.cast_ne_zero.mpr Fintype.card_ne_zero)
  apply Matrix.toLin'.injective
  rw [Matrix.toLin'_mul]
  simp only [toLin_stabilizerCodeProjectorMatrix]
  apply LinearMap.ext
  intro v
  exact AgtXIv.Gottesman.groupAverage_idempotent F.generalRankFDRep.ρ v

/-- Hermitian idempotence makes the code projector positive semidefinite. -/
theorem stabilizerCodeProjectorMatrix_posSemidef
    (F : IndependentSignedPauliFrame n r) :
    (stabilizerCodeProjectorMatrix F).PosSemidef := by
  have hPSD :=
    Matrix.posSemidef_conjTranspose_mul_self
      (stabilizerCodeProjectorMatrix F)
  rw [(stabilizerCodeProjectorMatrix_isHermitian F).eq,
    stabilizerCodeProjectorMatrix_idempotent] at hPSD
  exact hPSD

/-- The trace of the code projector is the encoded-space dimension. -/
theorem stabilizerCodeProjectorMatrix_trace
    (F : IndependentSignedPauliFrame n r) (hr : r ≤ n) :
    Matrix.trace (stabilizerCodeProjectorMatrix F) =
      (2 ^ (n - r) : ℂ) := by
  letI : Invertible (Fintype.card (BinaryWord r) : ℂ) :=
    invertibleOfNonzero (Nat.cast_ne_zero.mpr Fintype.card_ne_zero)
  rw [← Matrix.trace_toLin'_eq, toLin_stabilizerCodeProjectorMatrix]
  rw [(AgtXIv.Gottesman.groupAverage_isProjection
    F.generalRankFDRep.ρ).trace]
  rw [F.finrank_commonFixed_eq_two_pow_sub hr]
  norm_num

/-- The range of the code projector has dimension `2 ^ (n-r)`. -/
theorem stabilizerCodeProjectorMatrix_range_finrank
    (F : IndependentSignedPauliFrame n r) (hr : r ≤ n) :
    Module.finrank ℂ
      (LinearMap.range (Matrix.toLin' (stabilizerCodeProjectorMatrix F))) =
        2 ^ (n - r) := by
  letI : Invertible (Fintype.card (BinaryWord r) : ℂ) :=
    invertibleOfNonzero (Nat.cast_ne_zero.mpr Fintype.card_ne_zero)
  rw [toLin_stabilizerCodeProjectorMatrix]
  rw [AgtXIv.Gottesman.range_groupAverageMap]
  exact F.finrank_commonFixed_eq_two_pow_sub hr

end

end AgtXIv.Stabilizer
