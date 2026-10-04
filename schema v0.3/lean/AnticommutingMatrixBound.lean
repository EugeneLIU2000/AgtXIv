import AnticommutingOrderedProducts

/-! Uncompiled matrix-dimension consequences of the general-unit argument.
The final theorem accepts actual matrix units, not merely nonzero matrices.
No Hermitian or ordinary skew-transpose hypothesis is imposed. Connecting the
query's Pauli objects and graph relation to these hypotheses remains separate.
-/

namespace AgtXIv.AnticommutingMatrixBound

variable {K : Type*} [Field K]

theorem even_family_dimension_bound {N m : ℕ} [NeZero N]
    (hm : Even m) (htwo : (2 : K) ≠ 0)
    (b : Fin m → (Matrix (Fin N) (Fin N) K)ˣ)
    (hanti : ∀ i j, i ≠ j →
      (b i : Matrix (Fin N) (Fin N) K) * (b j : Matrix (Fin N) (Fin N) K) =
        -((b j : Matrix (Fin N) (Fin N) K) * (b i : Matrix (Fin N) (Fin N) K))) :
    2 ^ m ≤ N ^ 2 := by
  have h := AgtXIv.AnticommutingOrderedProducts.two_pow_le_finrank
    (K := K) hm htwo b hanti
  simpa [Module.finrank_matrix, pow_two] using h

theorem family_card_le_two_mul_add_one {q r : ℕ}
    (htwo : (2 : K) ≠ 0)
    (b : Fin r → (Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K)ˣ)
    (hanti : ∀ i j, i ≠ j →
      (b i : Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K) *
          (b j : Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K) =
        -((b j : Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K) *
          (b i : Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K))) :
    r ≤ 2 * q + 1 := by
  classical
  by_contra hlarge
  have hle : 2 * q + 2 ≤ r := by omega
  let e : Fin (2 * q + 2) → Fin r := Fin.castLE hle
  have he : Function.Injective e := Fin.castLE_injective hle
  let subfamily := fun i : Fin (2 * q + 2) => b (e i)
  have hsub : ∀ i j, i ≠ j →
      (subfamily i : Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K) *
          (subfamily j : Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K) =
        -((subfamily j : Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K) *
          (subfamily i : Matrix (Fin (2 ^ q)) (Fin (2 ^ q)) K)) := by
    intro i j hij
    exact hanti (e i) (e j) (fun h => hij (he h))
  have heven : Even (2 * q + 2) := ⟨q + 1, by omega⟩
  letI : NeZero (2 ^ q) := ⟨pow_ne_zero q (by decide)⟩
  have hdim := even_family_dimension_bound heven htwo subfamily hsub
  have hsquare : (2 ^ q : ℕ) ^ 2 = 2 ^ (2 * q) := by
    rw [← pow_mul, Nat.mul_comm q 2]
  rw [hsquare, pow_add] at hdim
  norm_num at hdim

end AgtXIv.AnticommutingMatrixBound
