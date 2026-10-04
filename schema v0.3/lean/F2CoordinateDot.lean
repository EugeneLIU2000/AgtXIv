import AgtXIvRootMath.F2Coordinates

/-! Uncompiled bridge from the actual parity bit-vector dot product to coordinate
sum. The induction follows cons_dotZ₂_cons and the most-significant-bit split.
-/

open scoped BigOperators

namespace AgtXIv.Stabilizer.F2Bits

theorem ofBool_and (a b : Bool) : ofBool (a && b) = ofBool a * ofBool b := by
  cases a <;> cases b <;> decide

theorem dot_cons {n : ℕ} (a b : BitVec n) (p q : Bool) :
    dot (⟨BitVec.cons p a⟩ : F2Bits (n + 1)) ⟨BitVec.cons q b⟩ =
      ofBool p * ofBool q + dot (⟨a⟩ : F2Bits n) ⟨b⟩ := by
  simp only [dot, BitVec.cons_dotZ₂_cons, ofBool_xor, ofBool_and]

theorem dot_eq_sum_coordinates {n : ℕ} (a b : F2Bits n) :
    dot a b = ∑ i, coordinate a i * coordinate b i := by
  induction n with
  | zero =>
    have ha : a = 0 := by apply F2Bits.ext; exact BitVec.of_length_zero
    subst a
    simp [coordinate]
  | succ n ih =>
    have ha : a.bits = BitVec.cons a.bits.msb a.bits.lsbs :=
      (BitVec.cons_msb_lsbs a.bits).symm
    have hb : b.bits = BitVec.cons b.bits.msb b.bits.lsbs :=
      (BitVec.cons_msb_lsbs b.bits).symm
    have hDot : dot a b = ofBool a.bits.msb * ofBool b.bits.msb +
        dot (⟨a.bits.lsbs⟩ : F2Bits n) ⟨b.bits.lsbs⟩ := by
      change ofBool (a.bits.dotZ₂ b.bits) = ofBool a.bits.msb * ofBool b.bits.msb +
        ofBool (a.bits.lsbs.dotZ₂ b.bits.lsbs)
      conv_lhs => rw [ha, hb]
      rw [BitVec.cons_dotZ₂_cons, ofBool_xor, ofBool_and]
    rw [hDot, ih, Fin.sum_univ_castSucc]
    have hTail : (∑ i : Fin n, coordinate (⟨a.bits.lsbs⟩ : F2Bits n) i *
        coordinate (⟨b.bits.lsbs⟩ : F2Bits n) i) =
        ∑ i : Fin n, coordinate a i.castSucc * coordinate b i.castSucc := by
      apply Finset.sum_congr rfl
      intro i _
      simp [coordinate, BitVec.lsbs]
    rw [hTail]
    simpa [coordinate, BitVec.msb_eq_getLsbD_last] using add_comm
      (ofBool a.bits.msb * ofBool b.bits.msb)
      (∑ i : Fin n, coordinate a i.castSucc * coordinate b i.castSucc)

end AgtXIv.Stabilizer.F2Bits
