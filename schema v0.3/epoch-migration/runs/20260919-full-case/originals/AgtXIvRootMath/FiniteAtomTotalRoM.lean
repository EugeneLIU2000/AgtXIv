module

public import AgtXIvRootMath.AtomPreservingMonotonicity

/-!
# The attained finite-atom robustness value

This file packages the minimum whose existence was proved in
`FiniteAtomAttainment`.  Feasibility remains an explicit argument: the later
stabilizer-state specialization must prove that every trace-one Hermitian
target has a signed decomposition by the complete finite stabilizer atom set.
-/

@[expose] public section

namespace AgtXIv.RoM

variable {ι κ V W : Type*}
variable [Fintype ι] [Fintype κ]
variable [NormedAddCommGroup V] [NormedSpace ℝ V]
variable [NormedAddCommGroup W] [NormedSpace ℝ W]

/-- A chosen global minimizer for a feasible finite signed-decomposition
problem.  The numerical value below is independent of this choice. -/
noncomputable def optimalCoeffs
    (atom : ι → V) (ρ : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom ρ x) : ι → ℝ :=
  Classical.choose (exists_l1Minimizer atom ρ hFeasible)

theorem optimalCoeffs_isL1Minimizer
    (atom : ι → V) (ρ : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom ρ x) :
    IsL1Minimizer atom ρ (optimalCoeffs atom ρ hFeasible) :=
  Classical.choose_spec (exists_l1Minimizer atom ρ hFeasible)

/-- The finite-atom robustness is the attained minimum absolute coefficient
weight.  The explicit feasibility proof prevents an infeasible linear program
from being silently assigned a value. -/
noncomputable def finiteRoM
    (atom : ι → V) (ρ : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom ρ x) : ℝ :=
  l1Cost (optimalCoeffs atom ρ hFeasible)

/-- Every global minimizer has cost equal to the packaged finite robustness
value, so the value does not depend on the chosen minimizer. -/
theorem finiteRoM_eq_cost_of_isL1Minimizer
    (atom : ι → V) (ρ : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom ρ x)
    (x : ι → ℝ) (hx : IsL1Minimizer atom ρ x) :
    finiteRoM atom ρ hFeasible = l1Cost x := by
  apply le_antisymm
  · exact (optimalCoeffs_isL1Minimizer atom ρ hFeasible).2 x hx.1
  · exact hx.2 (optimalCoeffs atom ρ hFeasible)
      (optimalCoeffs_isL1Minimizer atom ρ hFeasible).1

/-- Faithfulness of the actual attained finite-atom robustness value. -/
theorem finiteRoM_eq_one_iff_free
    (atom : ι → V) (ρ : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom ρ x)
    (τ : V →ₗ[ℝ] ℝ)
    (hAtom : ∀ i, τ (atom i) = 1) (hTarget : τ ρ = 1) :
    finiteRoM atom ρ hFeasible = 1 ↔ FreeByAtoms atom ρ := by
  exact minimizer_faithful atom ρ (optimalCoeffs atom ρ hFeasible) τ hAtom hTarget
    (optimalCoeffs_isL1Minimizer atom ρ hFeasible)

/-- Strict form of faithfulness for the packaged value. -/
theorem one_lt_finiteRoM_iff_not_free
    (atom : ι → V) (ρ : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom ρ x)
    (τ : V →ₗ[ℝ] ℝ)
    (hAtom : ∀ i, τ (atom i) = 1) (hTarget : τ ρ = 1) :
    1 < finiteRoM atom ρ hFeasible ↔ ¬ FreeByAtoms atom ρ := by
  exact minimizer_cost_gt_one_iff_not_free atom ρ
    (optimalCoeffs atom ρ hFeasible) τ hAtom hTarget
    (optimalCoeffs_isL1Minimizer atom ρ hFeasible)

/-- Atom-wise preservation gives a concrete feasible signed decomposition of
the output whenever the input is feasible. -/
theorem output_feasible_of_atomImages
    (atomIn : ι → V) (atomOut : κ → W) (E : V →ₗ[ℝ] W) (ρ : V)
    (hAtomImage : ∀ i, FreeByAtoms atomOut (E (atomIn i)))
    (hInputFeasible : ∃ x : ι → ℝ, SignedDecomp atomIn ρ x) :
    ∃ y : κ → ℝ, SignedDecomp atomOut (E ρ) y := by
  obtain ⟨x, hx⟩ := hInputFeasible
  refine ⟨(kernelOfAtomImages atomIn atomOut E hAtomImage).push x, ?_⟩
  unfold SignedDecomp
  rw [reconstruct_push_kernelOfAtomImages atomIn atomOut E hAtomImage x, hx]

/-- Deterministic monotonicity of the packaged finite-atom robustness value.
No stochastic kernel is assumed: it is constructed from atom-wise free-set
preservation. -/
theorem finiteRoM_mono_of_atomImages
    (atomIn : ι → V) (atomOut : κ → W) (E : V →ₗ[ℝ] W) (ρ : V)
    (hAtomImage : ∀ i, FreeByAtoms atomOut (E (atomIn i)))
    (hInputFeasible : ∃ x : ι → ℝ, SignedDecomp atomIn ρ x) :
    finiteRoM atomOut (E ρ)
        (output_feasible_of_atomImages atomIn atomOut E ρ hAtomImage hInputFeasible) ≤
      finiteRoM atomIn ρ hInputFeasible := by
  obtain ⟨x, y, hx, hy, hCost⟩ :=
    exists_output_minimizer_cost_le atomIn atomOut E ρ hAtomImage hInputFeasible
  rw [finiteRoM_eq_cost_of_isL1Minimizer atomOut (E ρ) _ y hy]
  rw [finiteRoM_eq_cost_of_isL1Minimizer atomIn ρ hInputFeasible x hx]
  exact hCost

end AgtXIv.RoM
