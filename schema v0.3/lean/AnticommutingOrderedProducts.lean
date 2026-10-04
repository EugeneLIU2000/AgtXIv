import AnticommutingUnitConjugation
import AnticommutingSignCharacters

/-! Uncompiled ordered unit products indexed by binary support vectors.
No commutative product of algebra elements is used: factors retain list order.
The finRange exponent is identified with the parity code below. All declarations
remain uncompiled candidates, including the assembled independence theorem.
-/

namespace AgtXIv.AnticommutingOrderedProducts

open AgtXIv.AnticommutingUnits AgtXIv.AnticommutingSignCharacters
open AgtXIv.AnticommutingParityPatterns
open scoped BigOperators

variable {K A ι : Type*} [Field K] [Ring A] [Algebra K A]

def factor (b : ι → Aˣ) (x : ι → ZMod 2) (j : ι) : Aˣ :=
  if x j = 0 then 1 else b j

def unitWord (b : ι → Aˣ) (x : ι → ZMod 2) : List ι → Aˣ
  | [] => 1
  | j :: rest => factor b x j * unitWord b x rest

def orderedProduct {m : ℕ} (b : Fin m → Aˣ) (x : Fin m → ZMod 2) : A :=
  (unitWord b x (List.finRange m) : A)

theorem orderedProduct_ne_zero [Nontrivial A] {m : ℕ}
    (b : Fin m → Aˣ) (x : Fin m → ZMod 2) : orderedProduct b x ≠ 0 :=
  Units.ne_zero (unitWord b x (List.finRange m))

theorem conjugate_factor [DecidableEq ι] (b : ι → Aˣ) (x : ι → ZMod 2)
    (hanti : ∀ i j, i ≠ j → (b i : A) * (b j : A) = -((b j : A) * (b i : A)))
    (i j : ι) :
    conjugate (b i) (factor b x j : A) =
      sign (K := K) (if j = i then 0 else x j) • (factor b x j : A) := by
  by_cases hx : x j = 0
  · simp [factor, hx, sign]
  · by_cases hji : j = i
    · subst j
      simp [factor, hx, sign]
    · simp only [factor, if_neg hx, if_neg hji]
      rw [conjugate_of_anticommute (b i) (b j) (hanti i j (Ne.symm hji))]
      simp [sign, hx]

theorem conjugate_unitWord [DecidableEq ι] (b : ι → Aˣ) (x : ι → ZMod 2)
    (hanti : ∀ i j, i ≠ j → (b i : A) * (b j : A) = -((b j : A) * (b i : A)))
    (i : ι) (indices : List ι) :
    conjugate (b i) (unitWord b x indices : A) =
      (indices.map (fun j => sign (K := K) (if j = i then 0 else x j))).prod •
        (unitWord b x indices : A) := by
  induction indices with
  | nil => simp [unitWord]
  | cons j rest ih =>
      simp only [unitWord, Units.val_mul, List.map_cons, List.prod_cons]
      rw [conjugate_mul, conjugate_factor (K := K) b x hanti, ih]
      rw [smul_mul_assoc, mul_smul_comm, smul_smul]

theorem sign_list_sum (xs : List (ZMod 2)) :
    sign (K := K) xs.sum = (xs.map (sign (K := K))).prod := by
  induction xs with
  | nil => simp [sign]
  | cons a rest ih =>
      simp only [List.sum_cons, List.map_cons, List.prod_cons]
      rw [sign_add, ih]

theorem conjugate_unitWord_exponent [DecidableEq ι]
    (b : ι → Aˣ) (x : ι → ZMod 2)
    (hanti : ∀ i j, i ≠ j → (b i : A) * (b j : A) = -((b j : A) * (b i : A)))
    (i : ι) (indices : List ι) :
    conjugate (b i) (unitWord b x indices : A) =
      sign (K := K) (indices.map (fun j => if j = i then 0 else x j)).sum •
        (unitWord b x indices : A) := by
  rw [conjugate_unitWord (K := K) b x hanti, sign_list_sum]
  simp only [List.map_map, Function.comp_def]

theorem full_exponent_eq_code {m : ℕ} (x : Fin m → ZMod 2) (i : Fin m) :
    ((List.finRange m).map (fun j => if j = i then 0 else x j)).sum = code x i := by
  rw [← List.ofFn_eq_map, Fin.sum_ofFn]
  calc
    (∑ j, if j = i then 0 else x j) =
        ∑ j, (x j + if j = i then x i else 0) := by
      apply Finset.sum_congr rfl
      intro j hj
      by_cases hji : j = i
      · subst j
        simp [double_eq_zero]
      · simp [hji]
    _ = code x i := by simp [Finset.sum_add_distrib, code]

theorem conjugate_orderedProduct {m : ℕ} (b : Fin m → Aˣ)
    (hanti : ∀ i j, i ≠ j → (b i : A) * (b j : A) = -((b j : A) * (b i : A)))
    (x : Fin m → ZMod 2) (i : Fin m) :
    conjugate (b i) (orderedProduct b x) =
      sign (K := K) (code x i) • orderedProduct b x := by
  unfold orderedProduct
  rw [conjugate_unitWord_exponent (K := K) b x hanti, full_exponent_eq_code]

theorem orderedProducts_linearIndependent [Nontrivial A] {m : ℕ}
    (hm : Even m) (htwo : (2 : K) ≠ 0) (b : Fin m → Aˣ)
    (hanti : ∀ i j, i ≠ j → (b i : A) * (b j : A) = -((b j : A) * (b i : A))) :
    LinearIndependent K (orderedProduct b) := by
  apply linearIndependent_of_code_eigenvectors hm htwo
    (fun i => conjugateLinear (K := K) (b i)) (orderedProduct b)
    (orderedProduct_ne_zero b)
  intro i x
  exact conjugate_orderedProduct (K := K) b hanti x i

theorem two_pow_le_finrank [Nontrivial A] [FiniteDimensional K A] {m : ℕ}
    (hm : Even m) (htwo : (2 : K) ≠ 0) (b : Fin m → Aˣ)
    (hanti : ∀ i j, i ≠ j → (b i : A) * (b j : A) = -((b j : A) * (b i : A))) :
    2 ^ m ≤ Module.finrank K A := by
  have h := (orderedProducts_linearIndependent (K := K) hm htwo b hanti).fintype_card_le_finrank
  simpa using h

end AgtXIv.AnticommutingOrderedProducts
