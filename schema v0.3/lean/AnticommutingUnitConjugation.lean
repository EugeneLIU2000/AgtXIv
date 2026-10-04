import Mathlib

/-!
Uncompiled bridge candidates for the general-unit argument suggested by the
Robert/Shapiro source trail. These statements use actual unit inverses, not -B,
and impose no matrix order, square=-1 or skew-transpose hypothesis.

They do NOT yet prove even-generator square-free-product independence, the
dimension bound, or source alignment with a historical theorem.
-/

namespace AgtXIv.AnticommutingUnits

open scoped BigOperators

variable {A : Type*} [Ring A]

def conjugate (u : Aˣ) (a : A) : A := (u : A) * a * (↑u⁻¹ : A)

@[simp] theorem conjugate_one (u : Aˣ) : conjugate u 1 = 1 := by
  simp [conjugate]

theorem conjugate_mul (u : Aˣ) (a b : A) :
    conjugate u (a * b) = conjugate u a * conjugate u b := by
  simp [conjugate, mul_assoc]

@[simp] theorem conjugate_self (u : Aˣ) : conjugate u (u : A) = (u : A) := by
  simp [conjugate, mul_assoc]

theorem conjugate_of_anticommute (u : Aˣ) (a : A)
    (h : (u : A) * a = -(a * (u : A))) : conjugate u a = -a := by
  rw [conjugate, h]
  simp [neg_mul, mul_assoc]

theorem conjugate_list_prod (u : Aˣ) (xs : List A) :
    conjugate u xs.prod = (xs.map (conjugate u)).prod := by
  induction xs with
  | nil => simp
  | cons a xs ih =>
      simp only [List.prod_cons, List.map_cons]
      rw [conjugate_mul, ih]

-- This is the product-level rule before any parity counting: the factor equal
-- to the conjugating generator stays fixed, every distinct generator changes
-- sign. It does not assume distinctness or any size of the ambient matrices.
theorem conjugate_generator_product {ι : Type*} [DecidableEq ι]
    (b : ι → Aˣ)
    (hanti : ∀ i j, i ≠ j → (b i : A) * (b j : A) = -((b j : A) * (b i : A)))
    (i : ι) (indices : List ι) :
    conjugate (b i) (indices.map (fun j => (b j : A))).prod =
      (indices.map (fun j => if j = i then (b j : A) else -(b j : A))).prod := by
  induction indices with
  | nil => simp
  | cons j indices ih =>
      simp only [List.map_cons, List.prod_cons]
      rw [conjugate_mul, ih]
      by_cases hji : j = i
      · subst j
        simp
      · rw [if_neg hji]
        rw [conjugate_of_anticommute (b i) (b j) (hanti i j (Ne.symm hji))]

section LinearRelations

variable {K : Type*} [CommSemiring K] [Algebra K A]

def conjugateLinear (u : Aˣ) : A →ₗ[K] A where
  toFun := conjugate u
  map_add' := by
    intro a b
    simp [conjugate, mul_add, add_mul]
  map_smul' := by
    intro c a
    simp [conjugate, mul_smul_comm, smul_mul_assoc]

@[simp] theorem conjugateLinear_apply (u : Aˣ) (a : A) :
    conjugateLinear (K := K) u a = conjugate u a := rfl

theorem conjugate_preserves_relation {ι : Type*} [Fintype ι]
    (u : Aˣ) (c : ι → K) (a : ι → A)
    (h : ∑ i, c i • a i = 0) : ∑ i, c i • conjugate u (a i) = 0 := by
  have transformed := congrArg (conjugateLinear (K := K) u) h
  simpa only [map_sum, map_smul, map_zero, conjugateLinear_apply] using transformed

end LinearRelations

end AgtXIv.AnticommutingUnits
