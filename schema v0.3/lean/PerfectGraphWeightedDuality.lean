import PerfectGraphWeightedApproximation
import WeightedCliqueCoverWeakDuality

/-!
Candidate, not yet compiled: close the real-weight bridge using the existing
finite-cover minimizer and quantitative integer-cover approximation. No weighted
duality, replication certificate, or continuity assertion is an extra premise.
This does not establish theta equality, an algorithm, or source alignment.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation
open scoped BigOperators

noncomputable section

variable {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V)

/-- A nonnegative real demand has a cover whose cost is its weighted independence
number. The empty graph and zero demands are included in the stated domain. -/
theorem exists_real_optimal_fractionalCliqueCover (hG : IsPerfect G)
    (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) :
    ∃ lam : Finset V → ℝ, IsFractionalCliqueCover G w lam ∧
      (∑ Q ∈ cliqueFinsets G, lam Q) = maxWeightIndependent G w := by
  classical
  obtain ⟨lam, hLam, hMin⟩ := exists_minimizing_fractionalCliqueCover G w hw
  refine ⟨lam, hLam, le_antisymm ?_ (maxWeightIndependent_le_cover_cost G w lam hLam)⟩
  by_contra hNot
  have hGap : maxWeightIndependent G w < ∑ Q ∈ cliqueFinsets G, lam Q :=
    lt_of_not_ge hNot
  let ε : ℝ := ((∑ Q ∈ cliqueFinsets G, lam Q) - maxWeightIndependent G w) / 2
  have hε : 0 < ε := by dsimp [ε]; linarith
  obtain ⟨mu, hMu, hNear⟩ := exists_real_cover_within G hG w hw ε hε
  have hCompare := hMin mu hMu
  dsimp [ε] at hNear
  linarith

/-- Equality uses the original infimum definition of the fractional cover value. -/
theorem fractionalCliqueCoverValue_eq_maxWeightIndependent (hG : IsPerfect G)
    (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) :
    fractionalCliqueCoverValue G w = maxWeightIndependent G w := by
  obtain ⟨lam, hLam, hCost⟩ := exists_real_optimal_fractionalCliqueCover G hG w hw
  have hLeast : IsLeast {c : ℝ | ∃ mu, IsFractionalCliqueCover G w mu ∧
      c = ∑ Q ∈ cliqueFinsets G, mu Q} (maxWeightIndependent G w) := by
    refine ⟨⟨lam, hLam, hCost.symm⟩, ?_⟩
    rintro c ⟨mu, hMu, rfl⟩
    exact maxWeightIndependent_le_cover_cost G w mu hMu
  exact hLeast.csInf_eq

end
end AgtXIv.PerfectGraph
