import FiniteCliqueCoverAttainment

/-! Actual finite independent-set/clique-cover weak duality, for arbitrary graphs.
No perfectness or weighted-duality equality is assumed. -/

open scoped BigOperators

namespace AgtXIv.GraphFoundation

theorem indep_clique_inter_card_le_one {V : Type*} [DecidableEq V]
    (G : SimpleGraph V) (S Q : Finset V)
    (hS : G.IsIndepSet (S : Set V)) (hQ : G.IsClique (Q : Set V)) :
    (S ∩ Q).card ≤ 1 := by
  apply Finset.card_le_one.mpr
  intro u hu v hv
  by_contra h
  exact hS (Finset.mem_inter.mp hu).1 (Finset.mem_inter.mp hv).1 h
    (hQ (Finset.mem_inter.mp hu).2 (Finset.mem_inter.mp hv).2 h)

theorem clique_weight_on_independent_le {V : Type*} [DecidableEq V]
    (G : SimpleGraph V) (S Q : Finset V) (a : ℝ)
    (hS : G.IsIndepSet (S : Set V)) (hQ : G.IsClique (Q : Set V))
    (ha : 0 ≤ a) : (∑ v ∈ S, if v ∈ Q then a else 0) ≤ a := by
  classical
  have hfilter : S.filter (fun v => v ∈ Q) = S ∩ Q := by ext v; simp
  rw [← Finset.sum_filter, hfilter, Finset.sum_const, nsmul_eq_mul]
  have hc : ((S ∩ Q).card : ℝ) ≤ 1 := by
    exact_mod_cast indep_clique_inter_card_le_one G S Q hS hQ
  simpa using mul_le_mul_of_nonneg_right hc ha

theorem independent_weight_le_cover_cost {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (lam : Finset V → ℝ)
    (hcover : IsFractionalCliqueCover G w lam) (S : Finset V)
    (hS : G.IsIndepSet (S : Set V)) :
    (∑ v ∈ S, w v) ≤ ∑ Q ∈ cliqueFinsets G, lam Q := by
  classical
  calc
    (∑ v ∈ S, w v) ≤ ∑ v ∈ S, ∑ Q ∈ cliqueFinsets G,
        if v ∈ Q then lam Q else 0 := Finset.sum_le_sum fun v _ => hcover.2 v
    _ = ∑ Q ∈ cliqueFinsets G, ∑ v ∈ S,
        if v ∈ Q then lam Q else 0 := Finset.sum_comm
    _ ≤ ∑ Q ∈ cliqueFinsets G, lam Q := by
      apply Finset.sum_le_sum
      intro Q hQ
      exact clique_weight_on_independent_le G S Q (lam Q) hS
        (Finset.mem_filter.mp hQ).2 (hcover.1 Q hQ)

theorem maxWeightIndependent_le_cover_cost {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (lam : Finset V → ℝ)
    (hcover : IsFractionalCliqueCover G w lam) :
    maxWeightIndependent G w ≤ ∑ Q ∈ cliqueFinsets G, lam Q := by
  classical
  unfold maxWeightIndependent
  apply Finset.sup'_le
  intro S hS
  exact independent_weight_le_cover_cost G w lam hcover S (Finset.mem_filter.mp hS).2

theorem maxWeightIndependent_le_fractionalCliqueCoverValue
    {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) :
    maxWeightIndependent G w ≤ fractionalCliqueCoverValue G w := by
  obtain ⟨lam, hcover, heq⟩ := fractionalCliqueCoverValue_attained G w hw
  rw [heq]
  exact maxWeightIndependent_le_cover_cost G w lam hcover

end AgtXIv.GraphFoundation
