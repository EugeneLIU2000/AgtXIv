import AgtXIvRootMath.GottesmanConcretePauliFrame
import Mathlib.Analysis.Matrix.PosDef
import Mathlib.LinearAlgebra.Matrix.Rank

/-!
# The rank-one density projector of a complete stabilizer frame

For a rank-`n` independent signed Pauli frame, the normalized group sum is the
common-`+1` projector.  This file proves, rather than assumes, that it is
Hermitian, idempotent, positive semidefinite, trace one, and has
one-dimensional range.

Complex positive semidefiniteness uses Mathlib's exact Hermitian quadratic-form
definition under its scoped complex order.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators ComplexOrder

variable {n : ℕ}

noncomputable instance binaryWordCardInvertible (n : ℕ) :
    Invertible (Fintype.card (BinaryWord n) : ℂ) :=
  invertibleOfNonzero (Nat.cast_ne_zero.mpr Fintype.card_ne_zero)

/-- An exact finite-dimensional density-matrix carrier. -/
structure DensityMatrix (d : ℕ) where
  val : CMatrix d d
  posSemidef : val.PosSemidef
  trace_one : Matrix.trace val = 1

/-- A pure density matrix, characterized by one-dimensional operator range. -/
structure PureDensityMatrix (d : ℕ) extends DensityMatrix d where
  range_finrank_one :
    Module.finrank ℂ (LinearMap.range (Matrix.toLin' val)) = 1

/-- The normalized group average of a complete signed Pauli frame. -/
noncomputable def stabilizerProjectorMatrix
    (F : IndependentSignedPauliFrame n n) : CMatrix (2 ^ n) (2 ^ n) :=
  ⅟(Fintype.card (BinaryWord n) : ℂ) •
    ∑ a : BinaryWord n, (F.eval a).toCMatrix

/-- The concrete matrix average is exactly the abstract finite-group averaging
linear map. -/
theorem toLin_stabilizerProjectorMatrix
    (F : IndependentSignedPauliFrame n n) :
    Matrix.toLin' (stabilizerProjectorMatrix F) =
      AgtXIv.Gottesman.groupAverageMap F.rankPauliFrame.fdRep.ρ := by
  ext v
  simp [stabilizerProjectorMatrix, AgtXIv.Gottesman.groupAverageMap,
    Representation.averageMap, GroupAlgebra.average,
    AgtXIv.Gottesman.RankPauliFrame.fdRep,
    IndependentSignedPauliFrame.rankPauliFrame,
    pauliMatrixRepresentation]

/-- Every element of the binary frame is an involutive, hence Hermitian,
Pauli.  Their real normalized average is Hermitian. -/
theorem stabilizerProjectorMatrix_isHermitian
    (F : IndependentSignedPauliFrame n n) :
    (stabilizerProjectorMatrix F).IsHermitian := by
  rw [Matrix.IsHermitian]
  simp only [stabilizerProjectorMatrix, Matrix.conjTranspose_smul,
    Matrix.conjTranspose_sum]
  congr 1
  · simp
  · apply Finset.sum_congr rfl
    intro a _
    exact (pauli_toCMatrix_isHermitian_of_sq_eq_one (F.eval a) (F.eval_sq a)).eq

/-- The stabilizer group average is idempotent. -/
theorem stabilizerProjectorMatrix_idempotent
    (F : IndependentSignedPauliFrame n n) :
    stabilizerProjectorMatrix F * stabilizerProjectorMatrix F =
      stabilizerProjectorMatrix F := by
  apply Matrix.toLin'.injective
  rw [Matrix.toLin'_mul]
  simp only [toLin_stabilizerProjectorMatrix]
  apply LinearMap.ext
  intro v
  exact AgtXIv.Gottesman.groupAverage_idempotent F.rankPauliFrame.fdRep.ρ v

/-- A Hermitian idempotent is its own Gram square, hence positive
semidefinite. -/
theorem stabilizerProjectorMatrix_posSemidef
    (F : IndependentSignedPauliFrame n n) :
    (stabilizerProjectorMatrix F).PosSemidef := by
  have hPSD := Matrix.posSemidef_conjTranspose_mul_self (stabilizerProjectorMatrix F)
  rw [(stabilizerProjectorMatrix_isHermitian F).eq,
    stabilizerProjectorMatrix_idempotent] at hPSD
  exact hPSD

/-- The rank-`n` projector has trace one.  This follows from the abstract
projection trace theorem and the independently derived one-dimensional fixed
space. -/
theorem stabilizerProjectorMatrix_trace_one
    (F : IndependentSignedPauliFrame n n) :
    Matrix.trace (stabilizerProjectorMatrix F) = 1 := by
  rw [← Matrix.trace_toLin'_eq, toLin_stabilizerProjectorMatrix]
  rw [(AgtXIv.Gottesman.groupAverage_isProjection F.rankPauliFrame.fdRep.ρ).trace]
  rw [F.finrank_commonFixed_eq_one]
  norm_num

/-- The operator range of the projector is one-dimensional. -/
theorem stabilizerProjectorMatrix_range_finrank_one
    (F : IndependentSignedPauliFrame n n) :
    Module.finrank ℂ
      (LinearMap.range (Matrix.toLin' (stabilizerProjectorMatrix F))) = 1 := by
  rw [toLin_stabilizerProjectorMatrix]
  rw [AgtXIv.Gottesman.range_groupAverageMap]
  exact F.finrank_commonFixed_eq_one

/-- The normalized group average is therefore an actual pure density matrix. -/
noncomputable def pureStabilizerDensity
    (F : IndependentSignedPauliFrame n n) : PureDensityMatrix (2 ^ n) where
  val := stabilizerProjectorMatrix F
  posSemidef := stabilizerProjectorMatrix_posSemidef F
  trace_one := stabilizerProjectorMatrix_trace_one F
  range_finrank_one := stabilizerProjectorMatrix_range_finrank_one F

end AgtXIv.Stabilizer
