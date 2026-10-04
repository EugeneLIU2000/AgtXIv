module

public import AgtXIvRootMath.FiniteAtomAttainment
public import AgtXIvRootMath.StochasticContraction

/-!
# From atom preservation to a stochastic kernel and RoM monotonicity

This file does not assume that a stochastic kernel has already been supplied.
It constructs one from the exact free-operation hypothesis that every input
atom is mapped to an ordinary convex mixture of output atoms.  It then proves
that the reconstructed output decomposition commutes with the linear map and
derives the finite-atom `l1` monotonicity theorem.
-/

@[expose] public section

namespace AgtXIv.RoM

open scoped BigOperators

variable {ι κ V W : Type*}
variable [NormedAddCommGroup V] [NormedSpace ℝ V]
variable [NormedAddCommGroup W] [NormedSpace ℝ W]

/-- Construct the row-stochastic coefficient kernel promised by atom-wise
free-set preservation. -/
noncomputable def kernelOfAtomImages
    [Fintype κ]
    (atomIn : ι → V) (atomOut : κ → W) (E : V →ₗ[ℝ] W)
    (hAtomImage : ∀ i, FreeByAtoms atomOut (E (atomIn i))) :
    FiniteStochasticKernel ι κ where
  prob i := Classical.choose (hAtomImage i)
  nonneg i := (Classical.choose_spec (hAtomImage i)).1
  row_sum i := (Classical.choose_spec (hAtomImage i)).2.1

/-- The chosen row of `kernelOfAtomImages` reconstructs the image of its input
atom. -/
theorem kernelOfAtomImages_row_reconstruct
    [Fintype κ]
    (atomIn : ι → V) (atomOut : κ → W) (E : V →ₗ[ℝ] W)
    (hAtomImage : ∀ i, FreeByAtoms atomOut (E (atomIn i))) (i : ι) :
    reconstruct atomOut ((kernelOfAtomImages atomIn atomOut E hAtomImage).prob i) =
      E (atomIn i) := by
  exact (Classical.choose_spec (hAtomImage i)).2.2

/-- Pushing signed coefficients through the constructed stochastic kernel and
then reconstructing gives exactly the linear image of the input
reconstruction. -/
theorem reconstruct_push_kernelOfAtomImages
    [Fintype ι] [Fintype κ]
    (atomIn : ι → V) (atomOut : κ → W) (E : V →ₗ[ℝ] W)
    (hAtomImage : ∀ i, FreeByAtoms atomOut (E (atomIn i)))
    (x : ι → ℝ) :
    reconstruct atomOut ((kernelOfAtomImages atomIn atomOut E hAtomImage).push x) =
      E (reconstruct atomIn x) := by
  classical
  calc
    reconstruct atomOut ((kernelOfAtomImages atomIn atomOut E hAtomImage).push x) =
        ∑ j, ∑ i, (x i * (kernelOfAtomImages atomIn atomOut E hAtomImage).prob i j) •
          atomOut j := by
            simp only [reconstruct, FiniteStochasticKernel.push]
            apply Finset.sum_congr rfl
            intro j _
            rw [Finset.sum_smul]
    _ = ∑ i, ∑ j, (x i * (kernelOfAtomImages atomIn atomOut E hAtomImage).prob i j) •
          atomOut j := by rw [Finset.sum_comm]
    _ = ∑ i, x i • reconstruct atomOut
          ((kernelOfAtomImages atomIn atomOut E hAtomImage).prob i) := by
            apply Finset.sum_congr rfl
            intro i _
            simp only [reconstruct, Finset.smul_sum, mul_smul]
    _ = ∑ i, x i • E (atomIn i) := by
            apply Finset.sum_congr rfl
            intro i _
            rw [kernelOfAtomImages_row_reconstruct]
    _ = E (reconstruct atomIn x) := by simp [reconstruct]

/-- Exact deterministic monotonicity for the attained finite-atom optimum.
The output optimum is derived, not assumed, and its cost cannot exceed the
input optimum. -/
theorem exists_output_minimizer_cost_le
    [Fintype ι] [Fintype κ]
    (atomIn : ι → V) (atomOut : κ → W) (E : V →ₗ[ℝ] W) (ρ : V)
    (hAtomImage : ∀ i, FreeByAtoms atomOut (E (atomIn i)))
    (hInputFeasible : ∃ x : ι → ℝ, SignedDecomp atomIn ρ x) :
    ∃ x : ι → ℝ, ∃ y : κ → ℝ,
      IsL1Minimizer atomIn ρ x ∧
      IsL1Minimizer atomOut (E ρ) y ∧
      l1Cost y ≤ l1Cost x := by
  let K := kernelOfAtomImages atomIn atomOut E hAtomImage
  obtain ⟨x, hxMin⟩ := exists_l1Minimizer atomIn ρ hInputFeasible
  have hPushFeasible : SignedDecomp atomOut (E ρ) (K.push x) := by
    unfold SignedDecomp
    rw [reconstruct_push_kernelOfAtomImages atomIn atomOut E hAtomImage x, hxMin.1]
  obtain ⟨y, hyMin⟩ := exists_l1Minimizer atomOut (E ρ) ⟨K.push x, hPushFeasible⟩
  exact ⟨x, y, hxMin, hyMin,
    (hyMin.2 (K.push x) hPushFeasible).trans (K.l1_push_le x)⟩

end AgtXIv.RoM
