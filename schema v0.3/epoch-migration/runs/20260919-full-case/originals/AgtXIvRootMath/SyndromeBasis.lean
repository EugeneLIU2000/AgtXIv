import AgtXIvRootMath.SemanticClifford
import Mathlib.LinearAlgebra.Matrix.ConjTranspose

/-!
# A unitary basis from read and flip operators

This module contains the generic linear-algebra core of the stabilizer-to-
Clifford bridge.  A commuting family of Hermitian "read" operators diagnoses a
binary syndrome, while unitary "flip" operators generate all syndrome vectors
from one normalized common `+1` vector.  Distinct characters force
orthogonality, and the resulting columns form a unitary matrix.

The file is intentionally independent of Pauli support and phase arithmetic.
The phase-aware Pauli module must construct the data below and prove its Weyl
relations; none of those obligations is assumed to be a Clifford theorem.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix
noncomputable section

/-- Coordinate formula for the physical complex inner product. -/
def ketInner {d : ℕ} (v w : Fin d → ℂ) : ℂ :=
  star v ⬝ᵥ w

@[simp]
theorem ketInner_zero_left {d : ℕ} (w : Fin d → ℂ) :
    ketInner 0 w = 0 := by
  simp [ketInner]

@[simp]
theorem ketInner_zero_right {d : ℕ} (v : Fin d → ℂ) :
    ketInner v 0 = 0 := by
  simp [ketInner]

theorem ketInner_smul_left {d : ℕ} (c : ℂ) (v w : Fin d → ℂ) :
    ketInner (c • v) w = star c * ketInner v w := by
  simp [ketInner]

theorem ketInner_smul_right {d : ℕ} (c : ℂ) (v w : Fin d → ℂ) :
    ketInner v (c • w) = c * ketInner v w := by
  simp [ketInner]

/-- Moving a matrix from the first slot to the second slot takes its conjugate
transpose. -/
theorem ketInner_mulVec_left {d : ℕ} (M : CMatrix d d)
    (v w : Fin d → ℂ) :
    ketInner (M *ᵥ v) w = ketInner v (Mᴴ *ᵥ w) := by
  unfold ketInner
  rw [Matrix.star_mulVec]
  exact (Matrix.dotProduct_mulVec (star v) Mᴴ w).symm

/-- A unitary matrix preserves the physical inner product. -/
theorem ketInner_unitary_mulVec {d : ℕ} (U : CMatrix d d)
    (hU : U.IsUnitary) (v w : Fin d → ℂ) :
    ketInner (U *ᵥ v) (U *ᵥ w) = ketInner v w := by
  rw [ketInner_mulVec_left]
  rw [Matrix.mulVec_mulVec]
  have hLeft : Uᴴ * U = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff'] using hU
  rw [hLeft, Matrix.one_mulVec]

/-- Exact input required to generate an orthonormal syndrome basis.  Character
separation is a finite-label fact; the Pauli specialization proves it from the
nondegenerate binary dot product. -/
structure SyndromeBasisData (iota : Type*) [Fintype iota] (d : ℕ) where
  basisIndex : iota ≃ Fin d
  read : iota → CMatrix d d
  flip : iota → CMatrix d d
  vacuum : Fin d → ℂ
  phase : iota → iota → ℂ
  read_hermitian : ∀ a, (read a).IsHermitian
  flip_unitary : ∀ b, (flip b).IsUnitary
  vacuum_normalized : ketInner vacuum vacuum = 1
  read_vacuum : ∀ a, read a *ᵥ vacuum = vacuum
  weyl : ∀ a b, read a * flip b = phase a b • (flip b * read a)
  phase_star : ∀ a b, star (phase a b) = phase a b
  phase_separates : ∀ {b c}, b ≠ c → ∃ a, phase a b ≠ phase a c

namespace SyndromeBasisData

variable {iota : Type*} [Fintype iota] {d : ℕ}

/-- Generate the vector with syndrome `b` by flipping the common `+1`
vacuum. -/
def state (D : SyndromeBasisData iota d) (b : iota) : Fin d → ℂ :=
  D.flip b *ᵥ D.vacuum

/-- The Weyl relation makes each generated state a simultaneous read
eigenvector with the prescribed character. -/
theorem read_state (D : SyndromeBasisData iota d) (a b : iota) :
    D.read a *ᵥ D.state b = D.phase a b • D.state b := by
  unfold state
  rw [Matrix.mulVec_mulVec, D.weyl]
  rw [Matrix.smul_mulVec, ← Matrix.mulVec_mulVec, D.read_vacuum]

/-- Unitary flips preserve normalization. -/
theorem state_normalized (D : SyndromeBasisData iota d) (b : iota) :
    ketInner (D.state b) (D.state b) = 1 := by
  unfold state
  rw [ketInner_unitary_mulVec (D.flip b) (D.flip_unitary b)]
  exact D.vacuum_normalized

/-- Eigenvectors carrying distinct real characters of a Hermitian read
operator are orthogonal. -/
theorem state_orthogonal (D : SyndromeBasisData iota d)
    {b c : iota} (hbc : b ≠ c) :
    ketInner (D.state b) (D.state c) = 0 := by
  obtain ⟨a, hphase⟩ := D.phase_separates hbc
  have hMove := ketInner_mulVec_left (D.read a) (D.state b) (D.state c)
  rw [(D.read_hermitian a).eq, D.read_state, D.read_state] at hMove
  rw [ketInner_smul_left, ketInner_smul_right, D.phase_star] at hMove
  have hFactor :
      (D.phase a b - D.phase a c) * ketInner (D.state b) (D.state c) = 0 := by
    calc
      (D.phase a b - D.phase a c) * ketInner (D.state b) (D.state c) =
          D.phase a b * ketInner (D.state b) (D.state c) -
            D.phase a c * ketInner (D.state b) (D.state c) := by ring
      _ = 0 := sub_eq_zero.mpr hMove
  exact (mul_eq_zero.mp hFactor).resolve_left (sub_ne_zero.mpr hphase)

/-- Square matrix whose column `basisIndex b` is the syndrome state `b`. -/
def matrix (D : SyndromeBasisData iota d) : CMatrix d d :=
  fun row col => D.state (D.basisIndex.symm col) row

@[simp]
theorem matrix_column (D : SyndromeBasisData iota d) (b : iota) (row : Fin d) :
    D.matrix row (D.basisIndex b) = D.state b row := by
  simp [matrix]

/-- The syndrome-state matrix is unitary. -/
theorem matrix_unitary (D : SyndromeBasisData iota d) : D.matrix.IsUnitary := by
  classical
  rw [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff']
  ext j k
  change ketInner (D.state (D.basisIndex.symm j))
      (D.state (D.basisIndex.symm k)) = (1 : CMatrix d d) j k
  by_cases h : j = k
  · subst k
    rw [D.state_normalized]
    simp
  · have h' : D.basisIndex.symm j ≠ D.basisIndex.symm k := by
      exact fun heq => h (D.basisIndex.symm.injective heq)
    rw [D.state_orthogonal h']
    simp [h]

end SyndromeBasisData

end

end AgtXIv.Stabilizer
