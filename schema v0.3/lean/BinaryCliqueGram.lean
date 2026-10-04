import Mathlib

/-! Uncompiled candidate for the binary Gram argument in draft.tex:834–857.
The kernel of I+J embeds in the scalar field by coordinate sum. Relating this
map to the concrete Pauli symplectic Gram matrix remains a separate step.
-/

open scoped BigOperators

namespace AgtXIv.BinaryCliqueGram

variable (ι : Type*) [Fintype ι]

def coordinateSum : (ι → ZMod 2) →ₗ[ZMod 2] ZMod 2 where
  toFun x := ∑ i, x i
  map_add' x y := Finset.sum_add_distrib
  map_smul' c x := by simp [Finset.mul_sum]

/-- Coordinate expression for the all-ones matrix plus the identity. -/
def gramMap : (ι → ZMod 2) →ₗ[ZMod 2] (ι → ZMod 2) where
  toFun x i := x i + coordinateSum ι x
  map_add' x y := by
    funext i
    change (x i + y i) + (∑ j, (x j + y j)) =
      (x i + ∑ j, x j) + (y i + ∑ j, y j)
    rw [Finset.sum_add_distrib]
    ring
  map_smul' c x := by
    funext i
    simp [coordinateSum, Finset.mul_sum, mul_add]

theorem kernel_coordinate_eq_neg_sum (x : LinearMap.ker (gramMap ι)) (i : ι) :
    x.val i = -coordinateSum ι x.val := by
  have h := congrFun x.property i
  change x.val i + coordinateSum ι x.val = 0 at h
  exact eq_neg_of_add_eq_zero_left h

def kernelSum : LinearMap.ker (gramMap ι) →ₗ[ZMod 2] ZMod 2 :=
  (coordinateSum ι).comp (LinearMap.ker (gramMap ι)).subtype

theorem kernelSum_injective : Function.Injective (kernelSum ι) := by
  intro x y h
  change coordinateSum ι x.val = coordinateSum ι y.val at h
  apply Subtype.ext
  funext i
  rw [kernel_coordinate_eq_neg_sum ι x i, kernel_coordinate_eq_neg_sum ι y i, h]

/-- Every binary Gram-kernel vector is zero or the full-support all-ones vector.
This is a containment statement; it does not assert that the latter lies in
the kernel for every cardinality. -/
theorem eq_zero_or_one_of_gram_eq_zero (x : ι → ZMod 2)
    (hx : gramMap ι x = 0) : x = 0 ∨ x = fun _ => 1 := by
  have hScalar : coordinateSum ι x = 0 ∨ coordinateSum ι x = 1 := by
    have hAll : ∀ c : ZMod 2, c = 0 ∨ c = 1 := by decide
    exact hAll _
  have hCoordinate (i : ι) : x i = -coordinateSum ι x :=
    kernel_coordinate_eq_neg_sum ι ⟨x, hx⟩ i
  rcases hScalar with hZero | hOne
  · left
    funext i
    simpa [hZero] using hCoordinate i
  · right
    funext i
    have hi := hCoordinate i
    rw [hOne] at hi
    simpa only [show -(1 : ZMod 2) = 1 by decide] using hi

/-- Any dependency of the first Gram factor has full support unless trivial.
Existence of a nonzero dependency needs an additional dimension argument. -/
theorem factor_kernel_eq_zero_or_one
    {E : Type*} [AddCommGroup E] [Module (ZMod 2) E]
    (f : (ι → ZMod 2) →ₗ[ZMod 2] E)
    (g : E →ₗ[ZMod 2] (ι → ZMod 2))
    (hFactor : g.comp f = gramMap ι)
    (x : ι → ZMod 2) (hx : f x = 0) : x = 0 ∨ x = fun _ => 1 := by
  apply eq_zero_or_one_of_gram_eq_zero ι x
  rw [← hFactor]
  change g (f x) = 0
  rw [hx, map_zero]

/-- If the clique Gram map factors through E, retaining the coordinate sum
makes the first factor injective into E × F₂. This avoids assuming a rank bound. -/
theorem factor_with_sum_injective
    {E : Type*} [AddCommGroup E] [Module (ZMod 2) E]
    (f : (ι → ZMod 2) →ₗ[ZMod 2] E)
    (g : E →ₗ[ZMod 2] (ι → ZMod 2))
    (hFactor : g.comp f = gramMap ι) :
    Function.Injective (f.prod (coordinateSum ι)) := by
  intro x y h
  have hF : f x = f y := congrArg Prod.fst h
  have hSum : coordinateSum ι x = coordinateSum ι y := congrArg Prod.snd h
  have hGram : gramMap ι x = gramMap ι y := by
    rw [← hFactor]
    exact congrArg g hF
  funext i
  have hCoordinate := congrFun hGram i
  change x i + coordinateSum ι x = y i + coordinateSum ι y at hCoordinate
  rw [hSum] at hCoordinate
  exact add_right_cancel hCoordinate

/-- The factor space contributes its dimension, and the scalar sum contributes
at most one. A concrete Pauli factor of dimension 2n will yield the desired bound. -/
theorem card_le_factor_finrank_add_one
    {E : Type*} [AddCommGroup E] [Module (ZMod 2) E] [FiniteDimensional (ZMod 2) E]
    (f : (ι → ZMod 2) →ₗ[ZMod 2] E)
    (g : E →ₗ[ZMod 2] (ι → ZMod 2))
    (hFactor : g.comp f = gramMap ι) :
    Fintype.card ι ≤ Module.finrank (ZMod 2) E + 1 := by
  have hDim := LinearMap.finrank_le_finrank_of_injective
    (factor_with_sum_injective ι f g hFactor)
  simpa [Module.finrank_prod] using hDim

/-- More input coordinates than output dimensions force a nonzero dependency. -/
theorem exists_nonzero_kernel_of_finrank_lt
    {E : Type*} [AddCommGroup E] [Module (ZMod 2) E] [FiniteDimensional (ZMod 2) E]
    (f : (ι → ZMod 2) →ₗ[ZMod 2] E)
    (hDim : Module.finrank (ZMod 2) E < Fintype.card ι) :
    ∃ x : ι → ZMod 2, f x = 0 ∧ x ≠ 0 := by
  classical
  by_contra h
  push Not at h
  have hInjective : Function.Injective f := by
    intro x y hxy
    apply sub_eq_zero.mp
    apply h (x - y)
    simp [map_sub, hxy]
  have hBound : Fintype.card ι ≤ Module.finrank (ZMod 2) E := by
    simpa using LinearMap.finrank_le_finrank_of_injective hInjective
  omega

/-- Under the dimension excess, the unique possible nonzero kernel vector
actually is a dependency. This does not yet state a Pauli product identity. -/
theorem factor_one_eq_zero_of_finrank_lt
    {E : Type*} [AddCommGroup E] [Module (ZMod 2) E] [FiniteDimensional (ZMod 2) E]
    (f : (ι → ZMod 2) →ₗ[ZMod 2] E)
    (g : E →ₗ[ZMod 2] (ι → ZMod 2))
    (hFactor : g.comp f = gramMap ι)
    (hDim : Module.finrank (ZMod 2) E < Fintype.card ι) :
    f (fun _ => 1) = 0 := by
  obtain ⟨x, hx, hne⟩ := exists_nonzero_kernel_of_finrank_lt ι f hDim
  rcases factor_kernel_eq_zero_or_one ι f g hFactor x hx with hZero | hOne
  · exact False.elim (hne hZero)
  · simpa only [hOne] using hx

theorem factor_kernel_iff_zero_or_one_of_finrank_lt
    {E : Type*} [AddCommGroup E] [Module (ZMod 2) E] [FiniteDimensional (ZMod 2) E]
    (f : (ι → ZMod 2) →ₗ[ZMod 2] E)
    (g : E →ₗ[ZMod 2] (ι → ZMod 2))
    (hFactor : g.comp f = gramMap ι)
    (hDim : Module.finrank (ZMod 2) E < Fintype.card ι)
    (x : ι → ZMod 2) : f x = 0 ↔ x = 0 ∨ x = fun _ => 1 := by
  constructor
  · exact factor_kernel_eq_zero_or_one ι f g hFactor x
  · rintro (rfl | rfl)
    · exact map_zero f
    · exact factor_one_eq_zero_of_finrank_lt ι f g hFactor hDim

end AgtXIv.BinaryCliqueGram
