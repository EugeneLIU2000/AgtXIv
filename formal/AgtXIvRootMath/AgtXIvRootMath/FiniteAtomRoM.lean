module

public import Mathlib

/-!
# The finite-atom coefficient core of robustness of magic

This file deliberately proves an abstract convex-geometric kernel.  It does not
define density matrices, Pauli operators, stabilizer states, Clifford operations,
or a fixed measurement window.

The key identity behind the proofs is that normalized signed coefficients obey

`sum |x i| = 1 + sum (|x i| - x i)`.

Every summand on the right is nonnegative, and it vanishes exactly when the
corresponding coefficient is nonnegative.
-/

@[expose] public section

namespace AgtXIv.RoM

open scoped BigOperators

variable {ι V : Type*} [Fintype ι]
variable [AddCommGroup V] [Module ℝ V]

/-- Reconstruct an ambient vector from a finite family of atoms and real coefficients. -/
def reconstruct (atom : ι → V) (x : ι → ℝ) : V :=
  ∑ i, x i • atom i

/-- The finite `l1` cost used by the Howard--Campbell pseudomixture definition. -/
def l1Cost (x : ι → ℝ) : ℝ :=
  ∑ i, |x i|

/-- A signed decomposition is feasible when it reconstructs the target. -/
def SignedDecomp (atom : ι → V) (ρ : V) (x : ι → ℝ) : Prop :=
  reconstruct atom x = ρ

/-- Membership in the classical convex hull of a finite atom family. -/
def FreeByAtoms (atom : ι → V) (ρ : V) : Prop :=
  ∃ p : ι → ℝ,
    (∀ i, 0 ≤ p i) ∧
    (∑ i, p i = 1) ∧
    SignedDecomp atom ρ p

/-- A feasible coefficient vector that attains the global finite-atom `l1` minimum. -/
def IsL1Minimizer (atom : ι → V) (ρ : V) (x : ι → ℝ) : Prop :=
  SignedDecomp atom ρ x ∧
    ∀ y : ι → ℝ, SignedDecomp atom ρ y → l1Cost x ≤ l1Cost y

/-- A trace-like normalization functional forces every feasible signed decomposition
to have coefficient sum one. -/
theorem coeff_sum_eq_one
    (atom : ι → V) (ρ : V) (x : ι → ℝ) (τ : V →ₗ[ℝ] ℝ)
    (hAtom : ∀ i, τ (atom i) = 1) (hTarget : τ ρ = 1)
    (hx : SignedDecomp atom ρ x) :
    ∑ i, x i = 1 := by
  calc
    ∑ i, x i = ∑ i, x i * τ (atom i) := by
      apply Finset.sum_congr rfl
      intro i _
      rw [hAtom i, mul_one]
    _ = ∑ i, τ (x i • atom i) := by
      apply Finset.sum_congr rfl
      intro i _
      rw [τ.map_smul]
      rfl
    _ = τ (reconstruct atom x) := by
      simp [reconstruct]
    _ = τ ρ := by rw [hx]
    _ = 1 := hTarget

/-- For normalized real coefficients, the `l1` cost is at least one, and it is
exactly one precisely for an ordinary probability vector. -/
theorem normalized_l1 (x : ι → ℝ) (hNorm : ∑ i, x i = 1) :
    1 ≤ l1Cost x ∧ (l1Cost x = 1 ↔ ∀ i, 0 ≤ x i) := by
  have hTermNonneg : ∀ i, 0 ≤ |x i| - x i := fun i => sub_nonneg.mpr (le_abs_self (x i))
  have hGap : l1Cost x - 1 = ∑ i, (|x i| - x i) := by
    simp only [l1Cost, Finset.sum_sub_distrib, hNorm]
  constructor
  · rw [← sub_nonneg]
    rw [hGap]
    exact Finset.sum_nonneg fun i _ => hTermNonneg i
  · constructor
    · intro hCost i
      have hGapZero : ∑ j, (|x j| - x j) = 0 := by
        rw [← hGap, hCost]
        norm_num
      have hOneZero : |x i| - x i = 0 := by
        exact (Finset.sum_eq_zero_iff_of_nonneg
          (fun j (_hj : j ∈ Finset.univ) => hTermNonneg j)).mp hGapZero i (Finset.mem_univ i)
      exact abs_eq_self.mp (sub_eq_zero.mp hOneZero)
    · intro hNonneg
      simp only [l1Cost, abs_of_nonneg (hNonneg _), hNorm]

/-- Conditional finite-atom faithfulness.  The theorem assumes an actual global
minimizer; existence/attainment and the identification of the atoms with all pure
stabilizer states are separate contracts. -/
theorem minimizer_faithful
    (atom : ι → V) (ρ : V) (x : ι → ℝ) (τ : V →ₗ[ℝ] ℝ)
    (hAtom : ∀ i, τ (atom i) = 1) (hTarget : τ ρ = 1)
    (hMin : IsL1Minimizer atom ρ x) :
    l1Cost x = 1 ↔ FreeByAtoms atom ρ := by
  have hNorm : ∑ i, x i = 1 :=
    coeff_sum_eq_one atom ρ x τ hAtom hTarget hMin.1
  constructor
  · intro hCost
    exact ⟨x, (normalized_l1 x hNorm).2.mp hCost, hNorm, hMin.1⟩
  · rintro ⟨p, hpNonneg, hpNorm, hpDecomp⟩
    have hpCost : l1Cost p = 1 := (normalized_l1 p hpNorm).2.mpr hpNonneg
    have hUpper : l1Cost x ≤ 1 := by
      simpa [hpCost] using hMin.2 p hpDecomp
    exact le_antisymm hUpper (normalized_l1 x hNorm).1

/-- The strict form of finite-atom faithfulness, under the same attained-minimum
and normalization hypotheses. -/
theorem minimizer_cost_gt_one_iff_not_free
    (atom : ι → V) (ρ : V) (x : ι → ℝ) (τ : V →ₗ[ℝ] ℝ)
    (hAtom : ∀ i, τ (atom i) = 1) (hTarget : τ ρ = 1)
    (hMin : IsL1Minimizer atom ρ x) :
    1 < l1Cost x ↔ ¬ FreeByAtoms atom ρ := by
  have hNorm : ∑ i, x i = 1 :=
    coeff_sum_eq_one atom ρ x τ hAtom hTarget hMin.1
  have hLower : 1 ≤ l1Cost x := (normalized_l1 x hNorm).1
  constructor
  · intro hStrict hFree
    have hEq : l1Cost x = 1 :=
      (minimizer_faithful atom ρ x τ hAtom hTarget hMin).mpr hFree
    linarith
  · intro hNotFree
    have hNe : l1Cost x ≠ 1 := fun hEq =>
      hNotFree ((minimizer_faithful atom ρ x τ hAtom hTarget hMin).mp hEq)
    exact lt_of_le_of_ne hLower hNe.symm

end AgtXIv.RoM
