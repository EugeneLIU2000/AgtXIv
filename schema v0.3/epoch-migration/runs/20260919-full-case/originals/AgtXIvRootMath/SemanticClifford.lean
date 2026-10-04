import Quantumlib.Data.Gate.Pauli.Lemmas
import Quantumlib.ForMathlib.Data.Matrix.Unitary

/-!
# Witness-carrying semantic Clifford operators

A semantic Clifford operator is packaged as a unitary matrix together with the
*signed* Pauli-group automorphism that it implements by conjugation.  Keeping
the automorphism as data avoids erasing `ZMod 4` phases and makes composition
and inversion exact before a separate normalizer-to-automorphism existence
theorem is available.

This file proves that these witnesses are closed under identity, composition,
and inverse, and that their action on matrices defines an equivalence relation.
It deliberately does **not** identify this orbit relation with the predicate
"is the unique common `+1` eigenstate of a rank-`n` Pauli frame".  That
fixed-space-to-orbit equivalence remains a later theorem, not a definition.
-/

namespace AgtXIv.Stabilizer

open scoped Matrix
noncomputable section

/-- A unitary Pauli normalizer carrying the exact signed Pauli automorphism it
implements. -/
structure SemanticClifford (n : Nat) where
  matrix : CMatrix (2 ^ n) (2 ^ n)
  isUnitary : matrix.IsUnitary
  action : Pauli n ≃* Pauli n
  conjugates : ∀ P : Pauli n,
    matrix * P.toCMatrix * matrixᴴ = (action P).toCMatrix

namespace SemanticClifford

variable {n : Nat}

/-- The identity unitary implements the identity signed-Pauli automorphism. -/
def id (n : Nat) : SemanticClifford n where
  matrix := 1
  isUnitary := by simp [Matrix.IsUnitary]
  action := MulEquiv.refl (Pauli n)
  conjugates := by intro P; simp

/-- Composition follows physical operator order: `comp C D` first applies `D`
and then `C`. -/
def comp (C D : SemanticClifford n) : SemanticClifford n where
  matrix := C.matrix * D.matrix
  isUnitary := Matrix.mul_of_isUnitary C.matrix D.matrix C.isUnitary D.isUnitary
  action := D.action.trans C.action
  conjugates := by
    intro P
    rw [Matrix.conjTranspose_mul]
    calc
      (C.matrix * D.matrix) * P.toCMatrix * (D.matrixᴴ * C.matrixᴴ) =
          C.matrix * (D.matrix * P.toCMatrix * D.matrixᴴ) * C.matrixᴴ := by
            noncomm_ring
      _ = C.matrix * (D.action P).toCMatrix * C.matrixᴴ := by
            rw [D.conjugates]
      _ = (C.action (D.action P)).toCMatrix := C.conjugates _
      _ = ((D.action.trans C.action) P).toCMatrix := rfl

/-- The conjugate transpose implements the inverse signed-Pauli automorphism. -/
def inv (C : SemanticClifford n) : SemanticClifford n where
  matrix := C.matrixᴴ
  isUnitary := Matrix.conjTranspose_of_isUnitary C.matrix C.isUnitary
  action := C.action.symm
  conjugates := by
    intro P
    rw [Matrix.conjTranspose_conjTranspose]
    have hConj := C.conjugates (C.action.symm P)
    rw [C.action.apply_symm_apply] at hConj
    have hLeft : C.matrixᴴ * C.matrix = 1 := by
      simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff'] using C.isUnitary
    calc
      C.matrixᴴ * P.toCMatrix * C.matrix =
          C.matrixᴴ * (C.matrix * (C.action.symm P).toCMatrix * C.matrixᴴ) * C.matrix := by
            rw [hConj]
      _ = (C.matrixᴴ * C.matrix) * (C.action.symm P).toCMatrix *
          (C.matrixᴴ * C.matrix) := by noncomm_ring
      _ = (C.action.symm P).toCMatrix := by rw [hLeft]; simp

/-- Conjugation action on an arbitrary square matrix. -/
def conjugate (C : SemanticClifford n) (ρ : CMatrix (2 ^ n) (2 ^ n)) :
    CMatrix (2 ^ n) (2 ^ n) := C.matrix * ρ * C.matrixᴴ

@[simp] theorem conjugate_id (ρ : CMatrix (2 ^ n) (2 ^ n)) :
    conjugate (id n) ρ = ρ := by simp [conjugate, id]

theorem conjugate_comp (C D : SemanticClifford n) (ρ : CMatrix (2 ^ n) (2 ^ n)) :
    conjugate (comp C D) ρ = conjugate C (conjugate D ρ) := by
  simp only [conjugate, comp, Matrix.conjTranspose_mul]
  noncomm_ring

/-- Unitary conjugation preserves the multiplicative identity. -/
@[simp] theorem conjugate_one (C : SemanticClifford n) : C.conjugate 1 = 1 := by
  have hRight : C.matrix * C.matrixᴴ = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff] using C.isUnitary
  simpa [conjugate] using hRight

/-- Unitary conjugation preserves matrix multiplication. -/
theorem conjugate_mul (C : SemanticClifford n)
    (A B : CMatrix (2 ^ n) (2 ^ n)) :
    C.conjugate (A * B) = C.conjugate A * C.conjugate B := by
  have hLeft : C.matrixᴴ * C.matrix = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff'] using C.isUnitary
  simp only [conjugate]
  symm
  calc
    (C.matrix * A * C.matrixᴴ) * (C.matrix * B * C.matrixᴴ) =
        C.matrix * A * (C.matrixᴴ * C.matrix) * B * C.matrixᴴ := by
          noncomm_ring
    _ = C.matrix * (A * B) * C.matrixᴴ := by
          rw [hLeft]
          simp
          noncomm_ring

/-- Unitary conjugation preserves matrix addition. -/
theorem conjugate_add (C : SemanticClifford n)
    (A B : CMatrix (2 ^ n) (2 ^ n)) :
    C.conjugate (A + B) = C.conjugate A + C.conjugate B := by
  simp [conjugate, Matrix.mul_add, Matrix.add_mul]

/-- Unitary conjugation is complex-linear on matrices. -/
theorem conjugate_smul (C : SemanticClifford n) (a : ℂ)
    (A : CMatrix (2 ^ n) (2 ^ n)) :
    C.conjugate (a • A) = a • C.conjugate A := by
  simp [conjugate]

/-- The arbitrary-matrix conjugation action agrees with the exact signed
Pauli action carried by the certificate. -/
theorem conjugate_pauli (C : SemanticClifford n) (P : Pauli n) :
    C.conjugate P.toCMatrix = (C.action P).toCMatrix :=
  C.conjugates P

/-- Orbit relation generated by witness-carrying semantic Clifford conjugation. -/
def InOrbit (ρ σ : CMatrix (2 ^ n) (2 ^ n)) : Prop :=
  ∃ C : SemanticClifford n, σ = conjugate C ρ

theorem inOrbit_refl (ρ : CMatrix (2 ^ n) (2 ^ n)) : InOrbit ρ ρ := by
  exact ⟨id n, (conjugate_id ρ).symm⟩

theorem inOrbit_trans {ρ σ τ : CMatrix (2 ^ n) (2 ^ n)} :
    InOrbit ρ σ → InOrbit σ τ → InOrbit ρ τ := by
  rintro ⟨D, rfl⟩ ⟨C, rfl⟩
  exact ⟨comp C D, (conjugate_comp C D ρ).symm⟩

theorem conjugate_inv_cancel (C : SemanticClifford n)
    (ρ : CMatrix (2 ^ n) (2 ^ n)) :
    conjugate (inv C) (conjugate C ρ) = ρ := by
  have hLeft : C.matrixᴴ * C.matrix = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff'] using C.isUnitary
  simp only [conjugate, inv, Matrix.conjTranspose_conjTranspose]
  calc
    C.matrixᴴ * (C.matrix * ρ * C.matrixᴴ) * C.matrix =
        (C.matrixᴴ * C.matrix) * ρ * (C.matrixᴴ * C.matrix) := by noncomm_ring
    _ = ρ := by rw [hLeft]; simp

theorem inOrbit_symm {ρ σ : CMatrix (2 ^ n) (2 ^ n)} :
    InOrbit ρ σ → InOrbit σ ρ := by
  rintro ⟨C, rfl⟩
  exact ⟨inv C, (conjugate_inv_cancel C ρ).symm⟩

end SemanticClifford
end

end AgtXIv.Stabilizer
