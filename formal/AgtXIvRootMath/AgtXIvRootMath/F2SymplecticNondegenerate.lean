import AgtXIvRootMath.PauliF2Support
import Mathlib.LinearAlgebra.BilinearForm.Properties

/-!
# Nondegeneracy of the binary Pauli pairing

This file closes the concrete hypothesis needed to apply the constructive
completion theorem to phase-free Pauli supports.  It first proves directly
that every nonzero bit vector has dot product one with a suitable bit vector.
It then uses this witness in one half of the `Z/X` pair to prove that the
standard Pauli symplectic form is nondegenerate.

The result concerns only the binary commutation ledger.  It does not recover
Pauli phases or signs, construct a unitary Clifford, or identify a common
`+1` eigenspace.
-/

namespace AgtXIv.Stabilizer

namespace F2Bits

/-- A nonzero binary vector can be detected by the parity dot product. -/
theorem exists_dot_eq_one_of_ne_zero {n : Nat} (a : F2Bits n) (ha : a ≠ 0) :
    ∃ b : F2Bits n, dot a b = 1 := by
  induction n with
  | zero =>
      exfalso
      apply ha
      apply F2Bits.ext
      exact BitVec.of_length_zero
  | succ n ih =>
      by_cases hmsb : a.bits.msb = true
      · let b : F2Bits (n + 1) := ⟨BitVec.cons true (0 : BitVec n)⟩
        refine ⟨b, ?_⟩
        change ofBool (a.bits.dotZ₂ b.bits) = 1
        rw [show a.bits = BitVec.cons a.bits.msb a.bits.lsbs from
          (BitVec.cons_msb_lsbs a.bits).symm]
        change ofBool ((BitVec.cons a.bits.msb a.bits.lsbs).dotZ₂
          (BitVec.cons true (0 : BitVec n))) = 1
        rw [BitVec.cons_dotZ₂_cons]
        simp [hmsb]
      · have hmsbFalse : a.bits.msb = false := by
          cases h : a.bits.msb
          · rfl
          · exact (hmsb h).elim
        let tail : F2Bits n := ⟨a.bits.lsbs⟩
        have htail : tail ≠ 0 := by
          intro hzero
          apply ha
          apply F2Bits.ext
          rw [← BitVec.cons_msb_lsbs a.bits, hmsbFalse]
          have hbits : tail.bits = 0 := congrArg F2Bits.bits hzero
          simp [tail] at hbits
          rw [hbits]
          simp
        obtain ⟨btail, hbtail⟩ := ih tail htail
        let b : F2Bits (n + 1) := ⟨BitVec.cons false btail.bits⟩
        refine ⟨b, ?_⟩
        change ofBool (a.bits.dotZ₂ b.bits) = 1
        rw [show a.bits = BitVec.cons a.bits.msb a.bits.lsbs from
          (BitVec.cons_msb_lsbs a.bits).symm]
        change ofBool ((BitVec.cons a.bits.msb a.bits.lsbs).dotZ₂
          (BitVec.cons false btail.bits)) = 1
        rw [BitVec.cons_dotZ₂_cons]
        simp only [hmsbFalse, Bool.false_and, Bool.false_xor]
        exact hbtail

/-- The parity dot-product form on length-`n` binary vectors is nondegenerate. -/
theorem dotForm_nondegenerate (n : Nat) : (dotForm (n := n)).Nondegenerate := by
  constructor
  · intro a h
    by_contra ha
    obtain ⟨b, hb⟩ := exists_dot_eq_one_of_ne_zero a ha
    have hz := h b
    rw [dotForm_apply, hb] at hz
    exact one_ne_zero hz
  · intro a h
    by_contra ha
    obtain ⟨b, hb⟩ := exists_dot_eq_one_of_ne_zero a ha
    have hz := h b
    rw [dotForm_apply, dot_comm, hb] at hz
    exact one_ne_zero hz

end F2Bits

namespace F2Support

/-- A nonzero Pauli support has symplectic pairing one with some support. -/
theorem exists_symplectic_eq_one_of_ne_zero {n : Nat} (u : F2Support n)
    (hu : u ≠ 0) :
    ∃ v : F2Support n, symplecticForm u v = 1 := by
  by_cases hx : u.2 = 0
  · have hz : u.1 ≠ 0 := by
      intro hz
      apply hu
      exact Prod.ext hz hx
    obtain ⟨b, hb⟩ := F2Bits.exists_dot_eq_one_of_ne_zero u.1 hz
    refine ⟨(0, b), ?_⟩
    simp [symplecticForm_apply, symplecticValue, hb]
  · obtain ⟨b, hb⟩ := F2Bits.exists_dot_eq_one_of_ne_zero u.2 hx
    refine ⟨(b, 0), ?_⟩
    simp [symplecticForm_apply, symplecticValue, hb]

/-- The standard binary Pauli symplectic form is nondegenerate in every
finite qubit dimension, including dimension zero. -/
theorem symplecticForm_nondegenerate (n : Nat) :
    (symplecticForm (n := n)).Nondegenerate := by
  constructor
  · intro u h
    by_contra hu
    obtain ⟨v, hv⟩ := exists_symplectic_eq_one_of_ne_zero u hu
    have hz := h v
    rw [hv] at hz
    exact one_ne_zero hz
  · intro u h
    by_contra hu
    obtain ⟨v, hv⟩ := exists_symplectic_eq_one_of_ne_zero u hu
    have hz := h v
    rw [symplectic_symm, hv] at hz
    exact one_ne_zero hz

end F2Support

end AgtXIv.Stabilizer
