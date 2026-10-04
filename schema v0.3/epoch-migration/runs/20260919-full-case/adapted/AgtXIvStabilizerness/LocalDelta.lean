import AgtXIvVarela
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.LinearAlgebra.AffineSpace.AffineSubspace.Defs

/-!
# Target-local mathematical delta for Stabilizerness

This module deliberately imports the Root and Varela packages and contains only
generic target-local interfaces. It reuses Mathlib's finite-sum triangle
inequality and affine-span API rather than reproving those foundations.

The graph-theoretic perfect-graph duality and the stabilizer-specific relaxed
vertex spanning construction are not asserted here.
-/

namespace AgtXIv.Stabilizerness

open scoped BigOperators
open Set

/-- A real coefficient is a deterministic sign. -/
def IsSign (x : ℝ) : Prop := x = 1 ∨ x = -1

/-- Every deterministic signed sum is bounded by the sum of absolute
coefficients. This is the reusable upper-bound half of free-sign maximization. -/
theorem abs_signed_sum_add_le
    {ι : Type*} [Fintype ι]
    (y f : ι → ℝ) (μ : ℝ) (hf : ∀ i, IsSign (f i)) :
    |(∑ i, f i * y i) + μ| ≤ (∑ i, |y i|) + |μ| := by
  calc
    |(∑ i, f i * y i) + μ| ≤ |∑ i, f i * y i| + |μ| := abs_add_le _ _
    _ ≤ (∑ i, |f i * y i|) + |μ| := by
      simpa [add_comm] using
        add_le_add_right (Finset.abs_sum_le_sum_abs (fun i => f i * y i) Finset.univ) |μ|
    _ = (∑ i, |y i|) + |μ| := by
      congr 1
      apply Finset.sum_congr rfl
      intro i _
      rcases hf i with hi | hi
      · simp [hi]
      · simp [hi]

/-- There is a deterministic sign choice attaining the universal absolute-sum
bound, including the affine constant `μ`. -/
theorem exists_sign_attaining_abs_sum
    {ι : Type*} [Fintype ι] (y : ι → ℝ) (μ : ℝ) :
    ∃ f : ι → ℝ,
      (∀ i, IsSign (f i)) ∧
      |(∑ i, f i * y i) + μ| = (∑ i, |y i|) + |μ| := by
  classical
  by_cases hμ : 0 ≤ μ
  · let f : ι → ℝ := fun i => if 0 ≤ y i then 1 else -1
    have hf : ∀ i, IsSign (f i) := by
      intro i
      by_cases hi : 0 ≤ y i <;> simp [f, hi, IsSign]
    have hterm : ∀ i, f i * y i = |y i| := by
      intro i
      by_cases hi : 0 ≤ y i
      · simp [f, hi, abs_of_nonneg hi]
      · have hneg : y i < 0 := lt_of_not_ge hi
        simp [f, hi, abs_of_neg hneg]
    refine ⟨f, hf, ?_⟩
    simp_rw [hterm]
    rw [abs_of_nonneg (add_nonneg (Finset.sum_nonneg fun i _ => abs_nonneg (y i)) hμ)]
    rw [abs_of_nonneg hμ]
  · have hμneg : μ < 0 := lt_of_not_ge hμ
    let f : ι → ℝ := fun i => if 0 ≤ y i then -1 else 1
    have hf : ∀ i, IsSign (f i) := by
      intro i
      by_cases hi : 0 ≤ y i <;> simp [f, hi, IsSign]
    have hterm : ∀ i, f i * y i = -|y i| := by
      intro i
      by_cases hi : 0 ≤ y i
      · simp [f, hi, abs_of_nonneg hi]
      · have hneg : y i < 0 := lt_of_not_ge hi
        simp [f, hi, abs_of_neg hneg]
    refine ⟨f, hf, ?_⟩
    simp_rw [hterm]
    rw [Finset.sum_neg_distrib, abs_of_neg hμneg]
    have hnonneg : 0 ≤ (∑ i, |y i|) + -μ :=
      add_nonneg (Finset.sum_nonneg fun i _ => abs_nonneg (y i)) (neg_nonneg.mpr hμneg.le)
    rw [show -(∑ i, |y i|) + μ = -((∑ i, |y i|) + -μ) by ring]
    rw [abs_neg, abs_of_nonneg hnonneg]

/-- The attainable value is greatest among all deterministic sign choices. -/
theorem max_abs_signed_sum
    {ι : Type*} [Fintype ι] (y : ι → ℝ) (μ : ℝ) :
    IsGreatest
      {z : ℝ | ∃ f : ι → ℝ,
        (∀ i, IsSign (f i)) ∧ z = |(∑ i, f i * y i) + μ|}
      ((∑ i, |y i|) + |μ|) := by
  obtain ⟨f, hf, hattain⟩ := exists_sign_attaining_abs_sum y μ
  constructor
  · exact ⟨f, hf, hattain.symm⟩
  · rintro z ⟨g, hg, rfl⟩
    exact abs_signed_sum_add_le y g μ hg

/-- Reusable reduction of a full affine-span goal to a vector-span goal.
The Stabilizerness-specific construction of coordinate differences remains the
local premise `hspan`. -/
theorem affineSpan_eq_top_of_vectorSpan_eq_top
    {E : Type*} [AddCommGroup E] [Module ℝ E]
    {s : Set E} (hs : s.Nonempty) (hspan : vectorSpan ℝ s = ⊤) :
    affineSpan ℝ s = ⊤ :=
  (AffineSubspace.affineSpan_eq_top_iff_vectorSpan_eq_top_of_nonempty ℝ E E hs).2 hspan

end AgtXIv.Stabilizerness
