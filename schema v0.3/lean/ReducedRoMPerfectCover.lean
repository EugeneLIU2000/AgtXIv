import ReducedRoMGraphDual
import PerfectGraphWeightedDuality

/-!
Uncompiled candidate composition: replace the perfect-graph dual constraint by
an actual fractional clique cover of |y|, with the normalization budget |mu|.
The statement retains both no-active-dependency and perfectness hypotheses.
It neither assumes the final RoM closed form nor identifies a source theorem.
-/

open scoped BigOperators

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation

noncomputable section

theorem weightedIndependent_le_iff_cover_budget
    {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V)
    (hG : IsPerfect G) (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) (b : ℝ) :
    maxWeightIndependent G w ≤ b ↔
      ∃ lam : Finset V → ℝ, IsFractionalCliqueCover G w lam ∧
        (∑ Q ∈ cliqueFinsets G, lam Q) ≤ b := by
  constructor
  · intro h
    obtain ⟨lam, hLam, hCost⟩ := exists_real_optimal_fractionalCliqueCover G hG w hw
    exact ⟨lam, hLam, hCost.le.trans h⟩
  · rintro ⟨lam, hLam, hCost⟩
    exact (maxWeightIndependent_le_cover_cost G w lam hLam).trans hCost

end
end AgtXIv.PerfectGraph

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation AgtXIv.PerfectGraph

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n))

/-- Clique-cover certificates carry the normalization budget explicitly. -/
def perfectCoverDualValues : Set ℝ :=
  {z : ℝ | ∃ (y : Fin m → ℝ) (μ : ℝ) (lam : Finset (Fin m) → ℝ),
    IsFractionalCliqueCover W.contextFrustrationGraph (fun i => |y i|) lam ∧
    (∑ Q ∈ cliqueFinsets W.contextFrustrationGraph, lam Q) + |μ| ≤ 1 ∧
    z = μ + ∑ i, W.expectationProjection ρ.toTraceOneHermitian.1 i * y i}

theorem graphDualValues_eq_perfectCoverDualValues
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    graphDualValues W ρ = perfectCoverDualValues W ρ := by
  ext z
  constructor
  · rintro ⟨y, μ, hBudget, hValue⟩
    have hAlpha : maxWeightIndependent W.contextFrustrationGraph (fun i => |y i|) ≤
        1 - |μ| := by linarith
    obtain ⟨lam, hLam, hCost⟩ :=
      (weightedIndependent_le_iff_cover_budget W.contextFrustrationGraph hPerfect
        (fun i => |y i|) (fun i => abs_nonneg (y i)) (1 - |μ|)).mp hAlpha
    exact ⟨y, μ, lam, hLam, by linarith, hValue⟩
  · rintro ⟨y, μ, lam, hLam, hBudget, hValue⟩
    have hWeak := maxWeightIndependent_le_cover_cost W.contextFrustrationGraph
      (fun i => |y i|) lam hLam
    exact ⟨y, μ, by linarith, hValue⟩

/-- The certificate formulation has the actual reduced RoM as attained maximum. -/
theorem reducedRoM_isGreatest_perfect_cover_dual
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    IsGreatest (perfectCoverDualValues W ρ) (reducedRoM W ρ) := by
  rw [← graphDualValues_eq_perfectCoverDualValues W ρ hPerfect]
  exact reducedRoM_isGreatest_graph_dual W ρ hNoActive

end
end AgtXIv.ReducedRoM
