import Mathlib

/-! Uncompiled combinatorial part of the even-generator argument.
A support vector x records subset membership in ZMod 2. Conjugation exponents
are encoded by total parity plus the membership bit. This file does not yet
identify that encoding with eigenvalues in an arbitrary characteristic-not-two
field or with the ordered products of actual generators.
-/

namespace AgtXIv.AnticommutingParityPatterns

open scoped BigOperators

def code {m : ℕ} (x : Fin m → ZMod 2) : Fin m → ZMod 2 :=
  fun i => (∑ j, x j) + x i

theorem double_eq_zero (a : ZMod 2) : a + a = 0 := by
  rw [← two_mul]
  have htwo : (2 : ZMod 2) = 0 := by decide
  rw [htwo, zero_mul]

theorem even_cast_eq_zero {m : ℕ} (hm : Even m) : (m : ZMod 2) = 0 := by
  obtain ⟨k, hk⟩ := hm
  rw [hk, Nat.cast_add]
  exact double_eq_zero (k : ZMod 2)

theorem sum_code {m : ℕ} (hm : Even m) (x : Fin m → ZMod 2) :
    (∑ i, code x i) = ∑ i, x i := by
  simp [code, Finset.sum_add_distrib, Finset.sum_const, nsmul_eq_mul,
    even_cast_eq_zero hm]

theorem code_involutive {m : ℕ} (hm : Even m) :
    Function.Involutive (code (m := m)) := by
  intro x
  funext i
  change (∑ j, code x j) + ((∑ j, x j) + x i) = x i
  rw [sum_code hm, ← add_assoc, double_eq_zero, zero_add]

theorem code_injective {m : ℕ} (hm : Even m) :
    Function.Injective (code (m := m)) :=
  (code_involutive hm).injective

theorem distinct_supports_have_distinct_exponent {m : ℕ} (hm : Even m)
    (x y : Fin m → ZMod 2) (hxy : x ≠ y) :
    ∃ i, code x i ≠ code y i := by
  classical
  by_contra h
  apply hxy
  apply code_injective hm
  funext i
  by_contra hi
  exact h ⟨i, hi⟩

end AgtXIv.AnticommutingParityPatterns
