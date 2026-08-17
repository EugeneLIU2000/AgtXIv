module

public import AgtXIvRootMath.FiniteAtomRoM

/-!
# Contraction of signed coefficients under a finite stochastic kernel

This is the coefficient-level triangle-inequality step in the deterministic,
trace-preserving monotonicity proof for full robustness of magic.  The bridge
from a physical free channel to such a kernel remains outside this file.
-/

@[expose] public section

namespace AgtXIv.RoM

open scoped BigOperators

variable {ι κ : Type*} [Fintype ι] [Fintype κ]

/-- A finite real row-stochastic kernel.  Each input atom is sent to an ordinary
probability mixture of output atoms. -/
structure FiniteStochasticKernel (ι κ : Type*) [Fintype κ] where
  prob : ι → κ → ℝ
  nonneg : ∀ i j, 0 ≤ prob i j
  row_sum : ∀ i, ∑ j, prob i j = 1

namespace FiniteStochasticKernel

/-- Push signed input coefficients through a stochastic kernel. -/
def push (K : FiniteStochasticKernel ι κ) (x : ι → ℝ) (j : κ) : ℝ :=
  ∑ i, x i * K.prob i j

/-- A stochastic kernel preserves the total signed coefficient sum. -/
theorem sum_push (K : FiniteStochasticKernel ι κ) (x : ι → ℝ) :
    ∑ j, K.push x j = ∑ i, x i := by
  calc
    ∑ j, K.push x j = ∑ j, ∑ i, x i * K.prob i j := by rfl
    _ = ∑ i, ∑ j, x i * K.prob i j := by rw [Finset.sum_comm]
    _ = ∑ i, x i * ∑ j, K.prob i j := by
      apply Finset.sum_congr rfl
      intro i _
      rw [Finset.mul_sum]
    _ = ∑ i, x i := by simp [K.row_sum]

/-- The `l1` norm of signed coefficients cannot increase under a row-stochastic
kernel.  This is not, by itself, a theorem about quantum channels. -/
theorem l1_push_le (K : FiniteStochasticKernel ι κ) (x : ι → ℝ) :
    l1Cost (K.push x) ≤ l1Cost x := by
  calc
    l1Cost (K.push x) = ∑ j, |∑ i, x i * K.prob i j| := by rfl
    _ ≤ ∑ j, ∑ i, |x i * K.prob i j| := by
      apply Finset.sum_le_sum
      intro j _
      simpa using Finset.abs_sum_le_sum_abs
        (fun i => x i * K.prob i j) Finset.univ
    _ = ∑ j, ∑ i, |x i| * K.prob i j := by
      apply Finset.sum_congr rfl
      intro j _
      apply Finset.sum_congr rfl
      intro i _
      rw [abs_mul, abs_of_nonneg (K.nonneg i j)]
    _ = ∑ i, ∑ j, |x i| * K.prob i j := by rw [Finset.sum_comm]
    _ = ∑ i, |x i| * ∑ j, K.prob i j := by
      apply Finset.sum_congr rfl
      intro i _
      rw [Finset.mul_sum]
    _ = ∑ i, |x i| := by simp [K.row_sum]
    _ = l1Cost x := by rfl

end FiniteStochasticKernel

end AgtXIv.RoM
