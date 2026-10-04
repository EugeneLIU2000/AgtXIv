import PerfectGraphIntegerCover

/-!
Finite quantitative extension from natural to nonnegative real weights.
Scale actual integer clique covers, round each coordinate upward in increments
c, and bound the total maximum-independent-weight error by |V|*c. This gives
arbitrarily close feasible covers without assuming a duality equality or
continuity certificate. It is also valid when the graph has no vertices.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation
open scoped BigOperators

noncomputable section

variable {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V)

 theorem weightedIndependent_weight_le (w : V → ℝ) (S : Finset V)
    (hS : G.IsIndepSet (S : Set V)) : (∑ v ∈ S, w v) ≤ maxWeightIndependent G w := by
  classical
  exact Finset.le_sup' (fun T => ∑ v ∈ T, w v)
    (show S ∈ independentFinsets G by simp [independentFinsets, hS])

theorem weightedIndependent_le_iff (w : V → ℝ) (a : ℝ) :
    maxWeightIndependent G w ≤ a ↔
      ∀ S : Finset V, G.IsIndepSet (S : Set V) → (∑ v ∈ S, w v) ≤ a := by
  classical
  constructor
  · intro h S hS
    exact (weightedIndependent_weight_le G w S hS).trans h
  · intro h
    have hFamily : (independentFinsets G).Nonempty := ⟨∅, by simp [independentFinsets]⟩
    obtain ⟨S, hS, hMax⟩ := Finset.exists_mem_eq_sup' hFamily (fun T => ∑ v ∈ T, w v)
    have hInd : G.IsIndepSet (S : Set V) := by simpa [independentFinsets] using hS
    have hEq : maxWeightIndependent G w = ∑ v ∈ S, w v := hMax
    rw [hEq]
    exact h S hInd

/-- Homogeneity is proved from the actual finite maximum. -/
theorem weightedIndependent_scale (w : V → ℝ) (c : ℝ) (hc : 0 ≤ c) :
    maxWeightIndependent G (fun v => c * w v) = c * maxWeightIndependent G w := by
  classical
  apply le_antisymm
  · apply (weightedIndependent_le_iff G _ _).mpr
    intro S hS
    rw [← Finset.mul_sum]
    exact mul_le_mul_of_nonneg_left (weightedIndependent_weight_le G w S hS) hc
  · have hFamily : (independentFinsets G).Nonempty := ⟨∅, by simp [independentFinsets]⟩
    obtain ⟨S, hS, hMax⟩ := Finset.exists_mem_eq_sup' hFamily (fun T => ∑ v ∈ T, w v)
    have hInd : G.IsIndepSet (S : Set V) := by simpa [independentFinsets] using hS
    have hEq : maxWeightIndependent G w = ∑ v ∈ S, w v := hMax
    rw [hEq, Finset.mul_sum]
    exact weightedIndependent_weight_le G (fun v => c * w v) S hInd

/-- A uniform coordinate error c increases the maximum by at most |V|*c. -/
theorem weightedIndependent_error_bound (w z : V → ℝ) (c : ℝ) (hc : 0 ≤ c)
    (hError : ∀ v, z v ≤ w v + c) :
    maxWeightIndependent G z ≤ maxWeightIndependent G w + Fintype.card V * c := by
  classical
  apply (weightedIndependent_le_iff G z _).mpr
  intro S hS
  calc
    (∑ v ∈ S, z v) ≤ ∑ v ∈ S, (w v + c) := Finset.sum_le_sum fun v _ => hError v
    _ = (∑ v ∈ S, w v) + S.card * c := by simp [Finset.sum_add_distrib]
    _ ≤ maxWeightIndependent G w + Fintype.card V * c := by
      apply add_le_add (weightedIndependent_weight_le G w S hS)
      exact mul_le_mul_of_nonneg_right (by exact_mod_cast Finset.card_le_univ S) hc

/-- Scaling a feasible cover scales the demanded weights. -/
theorem fractionalCliqueCover_scale (w : V → ℝ) (lam : Finset V → ℝ)
    (hLam : IsFractionalCliqueCover G w lam) (c : ℝ) (hc : 0 ≤ c) :
    IsFractionalCliqueCover G (fun v => c * w v) (fun Q => c * lam Q) := by
  classical
  refine ⟨fun Q hQ => mul_nonneg hc (hLam.1 Q hQ), ?_⟩
  intro v
  have h := mul_le_mul_of_nonneg_left (hLam.2 v) hc
  simpa only [Finset.mul_sum, mul_ite, mul_zero] using h

/-- Exact covers for any scaled natural weights, including common-denominator
nonnegative rational weights; the scale may be any nonnegative real. -/
theorem exists_scaled_integer_optimal_cover (hG : IsPerfect G) (w : V → ℕ)
    (c : ℝ) (hc : 0 ≤ c) :
    ∃ lam : Finset V → ℝ, IsFractionalCliqueCover G (fun v => c * (w v : ℝ)) lam ∧
      (∑ Q ∈ cliqueFinsets G, lam Q) = maxWeightIndependent G (fun v => c * (w v : ℝ)) := by
  obtain ⟨lam, hLam, hCost, _⟩ := exists_integer_optimal_fractionalCliqueCover G w hG
  refine ⟨fun Q => c * lam Q, fractionalCliqueCover_scale G _ _ hLam c hc, ?_⟩
  rw [← Finset.mul_sum, hCost, weightedIndependent_scale G _ c hc]

/-- Arbitrarily close feasible covers of the actual nonnegative real weights. -/
theorem exists_real_cover_within (hG : IsPerfect G) (w : V → ℝ) (hw : ∀ v, 0 ≤ w v)
    (ε : ℝ) (hε : 0 < ε) :
    ∃ lam : Finset V → ℝ, IsFractionalCliqueCover G w lam ∧
      (∑ Q ∈ cliqueFinsets G, lam Q) ≤ maxWeightIndependent G w + ε := by
  classical
  let c : ℝ := ε / (Fintype.card V + 1)
  have hDen : (0 : ℝ) < Fintype.card V + 1 := by positivity
  have hc : 0 < c := div_pos hε hDen
  let p : V → ℕ := fun v => Nat.ceil (w v / c)
  let z : V → ℝ := fun v => c * (p v : ℝ)
  have hLower (v : V) : w v ≤ z v := by
    have h := Nat.le_ceil (w v / c)
    have hm := (div_le_iff₀ hc).mp h
    simpa only [z, p, mul_comm] using hm
  have hUpper (v : V) : z v ≤ w v + c := by
    have h := Nat.ceil_lt_add_one (div_nonneg (hw v) hc.le)
    have hm := mul_lt_mul_of_pos_left h hc
    have hCancel : c * (w v / c + 1) = w v + c := by field_simp
    rw [hCancel] at hm
    exact hm.le
  obtain ⟨lam, hLam, hCost⟩ := exists_scaled_integer_optimal_cover G hG p c hc.le
  have hCover : IsFractionalCliqueCover G w lam :=
    ⟨hLam.1, fun v => (hLower v).trans (hLam.2 v)⟩
  refine ⟨lam, hCover, ?_⟩
  rw [hCost]
  have hError := weightedIndependent_error_bound G w z c hc.le hUpper
  have hTotal : (Fintype.card V : ℝ) * c ≤ ε := by
    dsimp [c]
    rw [← mul_div_assoc]
    apply (div_le_iff₀ hDen).mpr
    nlinarith
  exact hError.trans (by linarith)

end
end AgtXIv.PerfectGraph
