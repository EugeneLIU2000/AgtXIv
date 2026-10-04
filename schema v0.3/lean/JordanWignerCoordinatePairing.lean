import JordanWignerPauliFamily

/-! Uncompiled coordinate calculation. The equality with F2Support.symplecticForm
must still be proved from the bit-vector dot product; this file alone does not
establish actual Pauli anticommutation.
-/

open scoped BigOperators

namespace AgtXIv.JordanWigner

open AgtXIv.Stabilizer

noncomputable section

def coordinatePairing {n : ℕ} (a b : Index n) : F2 :=
  (∑ j, (coordinates a).2 j * (coordinates b).1 j) +
  (∑ j, (coordinates a).1 j * (coordinates b).2 j)

theorem coordinatePairing_symm {n : ℕ} (a b : Index n) :
    coordinatePairing a b = coordinatePairing b a := by
  simp only [coordinatePairing, mul_comm]
  exact add_comm _ _

theorem coordinatePairing_none_some {n : ℕ} (k : Fin n) (y : Bool) :
    coordinatePairing none (some (k, y)) = 1 := by
  classical
  simp [coordinatePairing, coordinates]

private theorem sum_indicator_mul {n : ℕ} (k : Fin n) (f : Fin n → F2) :
    (∑ j, (if j = k then (1 : F2) else 0) * f j) = f k := by
  classical
  simp [ite_mul]

private theorem sum_mul_indicator {n : ℕ} (k : Fin n) (f : Fin n → F2) :
    (∑ j, f j * (if j = k then (1 : F2) else 0)) = f k := by
  classical
  simp [mul_ite]

theorem coordinatePairing_some_some {n : ℕ} (k l : Fin n) (y z : Bool) :
    coordinatePairing (some (k, y)) (some (l, z)) =
      (if k < l ∨ (k = l ∧ z = true) then 1 else 0) +
      (if l < k ∨ (l = k ∧ y = true) then 1 else 0) := by
  classical
  simp only [coordinatePairing, coordinates]
  rw [sum_indicator_mul k (fun j => if j < l ∨ (j = l ∧ z = true) then 1 else 0),
    sum_mul_indicator l (fun j => if j < k ∨ (j = k ∧ y = true) then 1 else 0)]

theorem coordinatePairing_eq_one_of_ne {n : ℕ} (a b : Index n) (hne : a ≠ b) :
    coordinatePairing a b = 1 := by
  classical
  cases a with
  | none =>
    cases b with
    | none => exact False.elim (hne rfl)
    | some b => exact coordinatePairing_none_some b.1 b.2
  | some a =>
    obtain ⟨k, y⟩ := a
    cases b with
    | none => rw [coordinatePairing_symm]; exact coordinatePairing_none_some k y
    | some b =>
      obtain ⟨l, z⟩ := b
      rw [coordinatePairing_some_some]
      rcases lt_trichotomy k l with hlt | heq | hgt
      · simp [hlt, ne_of_lt hlt, ne_of_gt hlt, not_lt_of_ge hlt.le]
      · subst l
        cases y <;> cases z <;> simp_all
      · simp [hgt, ne_of_lt hgt, ne_of_gt hgt, not_lt_of_ge hgt.le]

end
end AgtXIv.JordanWigner
