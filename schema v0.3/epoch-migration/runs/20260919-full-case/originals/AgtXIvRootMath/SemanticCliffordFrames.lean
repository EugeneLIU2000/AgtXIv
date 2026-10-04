import AgtXIvRootMath.PauliFaithful
import AgtXIvRootMath.SemanticClifford
import AgtXIvRootMath.GottesmanRankNProjector

/-!
# Exact Clifford action on complete signed Pauli frames

This file proves the easy, but phase-sensitive, half of the
Gottesman-to-Veitch bridge: an already certified semantic Clifford maps every
valid complete signed Pauli frame to another valid frame, preserves `-I`, and
conjugates the associated rank-one density projector exactly.

It does not assert that a suitable Clifford exists between arbitrary frames;
that transitivity theorem is a separate obligation.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix
noncomputable section

namespace SemanticClifford

variable {n : ℕ}

/-- Exact matrix conjugation as a complex-linear map. -/
def conjugateLinear (C : SemanticClifford n) :
    CMatrix (2 ^ n) (2 ^ n) →ₗ[ℂ] CMatrix (2 ^ n) (2 ^ n) where
  toFun := C.conjugate
  map_add' := C.conjugate_add
  map_smul' := C.conjugate_smul

@[simp]
theorem conjugateLinear_apply (C : SemanticClifford n)
    (A : CMatrix (2 ^ n) (2 ^ n)) :
    C.conjugateLinear A = C.conjugate A := rfl

/-- A physical conjugation certificate cannot send the distinguished scalar
`-I` to a different Pauli element. -/
theorem action_neg_one (C : SemanticClifford n) :
    C.action (-(1 : Pauli n)) = -(1 : Pauli n) := by
  apply pauli_toCMatrix_injective
  have hUnitary : C.matrix * C.matrixᴴ = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff] using C.isUnitary
  calc
    (C.action (-(1 : Pauli n))).toCMatrix =
        C.matrix * (-(1 : Pauli n)).toCMatrix * C.matrixᴴ :=
      (C.conjugates _).symm
    _ = C.matrix * (-(1 : CMatrix (2 ^ n) (2 ^ n))) * C.matrixᴴ := by
      rw [Pauli.toCMatrix_neg, Pauli.one_toCMatrix]
    _ = -(C.matrix * C.matrixᴴ) := by noncomm_ring
    _ = -(1 : CMatrix (2 ^ n) (2 ^ n)) := by rw [hUnitary]
    _ = (-(1 : Pauli n)).toCMatrix := by
      rw [Pauli.toCMatrix_neg, Pauli.one_toCMatrix]

/-- Apply a semantic Clifford to every word of an independent signed Pauli
frame.  Independence and exclusion of `-I` are conclusions. -/
def mapFrame (C : SemanticClifford n)
    (F : IndependentSignedPauliFrame n n) :
    IndependentSignedPauliFrame n n where
  eval := C.action.toMonoidHom.comp F.eval
  independent := C.action.injective.comp F.independent
  minusOneExcluded := by
    intro a h
    change C.action (F.eval a) = -(1 : Pauli n) at h
    have hNegInv : C.action.symm (-(1 : Pauli n)) = -(1 : Pauli n) := by
      calc
        C.action.symm (-(1 : Pauli n)) =
            C.action.symm (C.action (-(1 : Pauli n))) :=
          congrArg C.action.symm C.action_neg_one.symm
        _ = -(1 : Pauli n) := C.action.symm_apply_apply _
    have h' := congrArg C.action.symm h
    rw [C.action.symm_apply_apply, hNegInv] at h'
    exact F.minusOneExcluded a h'

@[simp]
theorem mapFrame_eval (C : SemanticClifford n)
    (F : IndependentSignedPauliFrame n n) (a : BinaryWord n) :
    (C.mapFrame F).eval a = C.action (F.eval a) := rfl

/-- Conjugation transports the exact group-average stabilizer projector. -/
theorem conjugate_stabilizerProjectorMatrix (C : SemanticClifford n)
    (F : IndependentSignedPauliFrame n n) :
    C.conjugate (stabilizerProjectorMatrix F) =
      stabilizerProjectorMatrix (C.mapFrame F) := by
  unfold stabilizerProjectorMatrix
  change C.conjugateLinear
      (((Fintype.card (BinaryWord n) : ℂ))⁻¹ •
        ∑ a, (F.eval a).toCMatrix) = _
  rw [map_smul, map_sum]
  apply congrArg
  apply Finset.sum_congr rfl
  intro a _
  exact C.conjugates (F.eval a)

end SemanticClifford

end
end AgtXIv.Stabilizer
