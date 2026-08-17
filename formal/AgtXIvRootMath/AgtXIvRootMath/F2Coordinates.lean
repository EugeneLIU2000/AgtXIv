import AgtXIvRootMath.PauliF2Support
import Mathlib.LinearAlgebra.BilinearForm.Properties

/-!
# Coordinate model of bit-vector support over `ZMod 2`

`F2Bits n` was introduced as a thin vector-space wrapper around `BitVec n`.
This file proves, rather than postulates, that reading all least-significant-bit
coordinates is a linear equivalence with `Fin n → ZMod 2`.  It supplies the
finite-coordinate interface needed for constructive symplectic completion.
-/

namespace AgtXIv.Stabilizer

namespace F2Bits

variable {n : Nat}

/-- Read one bit as an element of the two-element field. -/
def coordinate (a : F2Bits n) (i : Fin n) : F2 :=
  ofBool (a.bits.getLsb i)

theorem coordinate_add (a b : F2Bits n) :
    coordinate (a + b) = coordinate a + coordinate b := by
  funext i
  simp [coordinate, ofBool_xor]

theorem coordinate_smul (r : F2) (a : F2Bits n) :
    coordinate (r • a) = r • coordinate a := by
  rcases f2_eq_zero_or_one r with rfl | rfl
  · funext i
    simp [coordinate]
  · simp

/-- Reading every bit is a linear map. -/
def coordinateLinear : F2Bits n →ₗ[F2] (Fin n → F2) where
  toFun := coordinate
  map_add' := coordinate_add
  map_smul' := coordinate_smul

theorem ofBool_injective : Function.Injective ofBool := by
  intro a b h
  cases a <;> cases b <;> simp_all

theorem coordinateLinear_injective :
    Function.Injective (coordinateLinear : F2Bits n → Fin n → F2) := by
  intro a b h
  apply F2Bits.ext
  apply BitVec.eq_of_getLsbD_eq
  intro i
  by_cases hi : i < n
  · intro _
    have hc := congrFun h ⟨i, hi⟩
    apply ofBool_injective
    simpa [coordinateLinear, coordinate, BitVec.getLsbD_eq_getElem hi] using hc
  · intro hlt
    exact (hi hlt).elim

theorem coordinateLinear_bijective : Function.Bijective
    (coordinateLinear : F2Bits n → Fin n → F2) := by
  apply (Fintype.bijective_iff_injective_and_card _).2
  constructor
  · exact coordinateLinear_injective
  · rw [Fintype.card_congr {
      toFun := F2Bits.bits
      invFun := F2Bits.mk
      left_inv := fun _ => rfl
      right_inv := fun _ => rfl }]
    simpa using Fintype.card_congr (BitVec.equivFin (m := n)).toEquiv

/-- Exact linear coordinate equivalence; its inverse is obtained from the
proved finite bijection, not supplied as an axiom. -/
noncomputable def coordinateEquiv : F2Bits n ≃ₗ[F2] (Fin n → F2) :=
  LinearEquiv.ofBijective coordinateLinear coordinateLinear_bijective

@[simp] theorem coordinateEquiv_apply (a : F2Bits n) :
    coordinateEquiv a = coordinate a := rfl

end F2Bits

/-- Coordinate both the `Z` and `X` halves of phase-free Pauli support. -/
noncomputable def F2Support.coordinateEquiv (n : Nat) :
    F2Support n ≃ₗ[F2] ((Fin n → F2) × (Fin n → F2)) :=
  LinearEquiv.prodCongr F2Bits.coordinateEquiv F2Bits.coordinateEquiv

end AgtXIv.Stabilizer
