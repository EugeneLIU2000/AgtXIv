module

public import AgtXIvRootMath.FiniteAtomRoM
public import Mathlib.Topology.MetricSpace.Bounded

/-!
# Attainment of the finite-atom `l1` minimum

For a finite atom family in a real normed vector space, every feasible target
has an actual global minimum of the signed-coefficient `l1` cost.  This closes
the compactness step that was previously assumed by the conditional
faithfulness theorem.
-/

@[expose] public section

namespace AgtXIv.RoM

open Set
open scoped BigOperators

variable {ι V : Type*} [Fintype ι]
variable [NormedAddCommGroup V] [NormedSpace ℝ V]

theorem continuous_reconstruct (atom : ι → V) :
    Continuous (fun x : ι → ℝ => reconstruct atom x) := by
  unfold reconstruct
  fun_prop

theorem continuous_l1Cost : Continuous (l1Cost : (ι → ℝ) → ℝ) := by
  unfold l1Cost
  fun_prop

/-- Every feasible finite-atom signed decomposition admits a global `l1`
minimizer.  No minimum-attainment hypothesis is needed. -/
theorem exists_l1Minimizer
    (atom : ι → V) (ρ : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom ρ x) :
    ∃ x : ι → ℝ, IsL1Minimizer atom ρ x := by
  classical
  obtain ⟨x₀, hx₀⟩ := hFeasible
  let candidates : Set (ι → ℝ) :=
    {x | SignedDecomp atom ρ x ∧ l1Cost x ≤ l1Cost x₀}
  have hCandidatesNonempty : candidates.Nonempty := by
    exact ⟨x₀, hx₀, le_rfl⟩
  have hCandidatesClosed : IsClosed candidates := by
    apply IsClosed.inter
    · exact isClosed_eq (continuous_reconstruct atom) continuous_const
    · exact isClosed_le continuous_l1Cost continuous_const
  have hCostNonneg : 0 ≤ l1Cost x₀ := by
    exact Finset.sum_nonneg fun i _ => abs_nonneg (x₀ i)
  have hCandidatesBounded : Bornology.IsBounded candidates := by
    apply Metric.isBounded_closedBall.subset
    intro x hx
    rw [Metric.mem_closedBall, dist_zero_right]
    apply (pi_norm_le_iff_of_nonneg hCostNonneg).2
    intro i
    rw [Real.norm_eq_abs]
    exact (Finset.single_le_sum (fun j _ => abs_nonneg (x j))
      (Finset.mem_univ i)).trans hx.2
  have hCandidatesCompact : IsCompact candidates :=
    Metric.isCompact_iff_isClosed_bounded.mpr ⟨hCandidatesClosed, hCandidatesBounded⟩
  obtain ⟨x, hxCandidates, hxMin⟩ :=
    hCandidatesCompact.exists_isMinOn hCandidatesNonempty continuous_l1Cost.continuousOn
  refine ⟨x, hxCandidates.1, ?_⟩
  intro y hy
  by_cases hyCost : l1Cost y ≤ l1Cost x₀
  · exact hxMin ⟨hy, hyCost⟩
  · exact hxCandidates.2.trans (le_of_not_ge hyCost)

/-- Unconditional finite-atom faithfulness for every feasible normalized target. -/
theorem feasible_faithful
    (atom : ι → V) (ρ : V) (τ : V →ₗ[ℝ] ℝ)
    (hAtom : ∀ i, τ (atom i) = 1) (hTarget : τ ρ = 1)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom ρ x) :
    ∃ x : ι → ℝ,
      IsL1Minimizer atom ρ x ∧
      (l1Cost x = 1 ↔ FreeByAtoms atom ρ) ∧
      (1 < l1Cost x ↔ ¬ FreeByAtoms atom ρ) := by
  obtain ⟨x, hx⟩ := exists_l1Minimizer atom ρ hFeasible
  exact ⟨x, hx,
    minimizer_faithful atom ρ x τ hAtom hTarget hx,
    minimizer_cost_gt_one_iff_not_free atom ρ x τ hAtom hTarget hx⟩

end AgtXIv.RoM
