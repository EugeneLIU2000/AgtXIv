import PerfectGraphIntegralCover

/-!
Natural weights represented by actual independent copies. The weighted maximum
is the existing real-valued maxWeightIndependent, not a replacement definition.
The independence number of the replicated graph equals that existing quantity.
The graph is perfect by two proved complement steps and clique replication.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation
open scoped BigOperators

noncomputable section

variable {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V) (w : V → ℕ)

/-- Independent copies of each original vertex, with multiplicity its weight. -/
def independentBlowup : SimpleGraph (Σ v : V, Fin (w v)) := (cliqueBlowup Gᶜ w)ᶜ

/-- Distinct copies are adjacent exactly when their original vertices are adjacent. -/
@[simp] theorem independentBlowup_adj (a b : Σ v : V, Fin (w v)) :
    (independentBlowup G w).Adj a b ↔ G.Adj a.1 b.1 := by
  change (a ≠ b ∧ ¬(a ≠ b ∧ (a.1 = b.1 ∨ (a.1 ≠ b.1 ∧ ¬G.Adj a.1 b.1)))) ↔ _
  constructor
  · rintro ⟨hne, hnot⟩
    by_contra hadj
    apply hnot ⟨hne, ?_⟩
    by_cases heq : a.1 = b.1
    · exact Or.inl heq
    · exact Or.inr ⟨heq, hadj⟩
  · intro hadj
    refine ⟨fun heq => hadj.ne (congrArg Sigma.fst heq), ?_⟩
    rintro ⟨_, heq | hnot⟩
    · exact hadj.ne heq
    · exact hnot.2 hadj

/-- Independent replication is perfect by proved complement perfection. -/
theorem independentBlowup_isPerfect (hG : IsPerfect G) : IsPerfect (independentBlowup G w) := by
  classical
  exact complement_isPerfect (cliqueBlowup Gᶜ w)
    (cliqueBlowup_isPerfect Gᶜ w (complement_isPerfect G hG))

/-- Keep every copy above an independent set. -/
theorem independentBlowup_lift_independent (S : Finset V) (hS : G.IsIndepSet (S : Set V)) :
    (independentBlowup G w).IsIndepSet
      ((S.sigma (fun v => (Finset.univ : Finset (Fin (w v))))) : Set (Σ v, Fin (w v))) := by
  intro a ha b hb _ hadj
  have hAdj := (independentBlowup_adj G w a b).mp hadj
  exact hS (Finset.mem_sigma.mp ha).1 (Finset.mem_sigma.mp hb).1 hAdj.ne hAdj

/-- Forgetting copy indices preserves independence. -/
theorem independentBlowup_image_independent (S : Finset (Σ v, Fin (w v)))
    (hS : (independentBlowup G w).IsIndepSet (S : Set (Σ v, Fin (w v)))) :
    G.IsIndepSet (S.image Sigma.fst : Set V) := by
  intro a ha b hb hne hadj
  obtain ⟨x, hx, rfl⟩ := Finset.mem_image.mp ha
  obtain ⟨y, hy, rfl⟩ := Finset.mem_image.mp hb
  exact hS hx hy (fun heq => hne (congrArg Sigma.fst heq))
    ((independentBlowup_adj G w x y).mpr hadj)

/-- A set of copies cannot exceed the total multiplicity of its projection. -/
theorem copies_card_le_sum_weights (S : Finset (Σ v, Fin (w v))) :
    S.card ≤ ∑ v ∈ S.image Sigma.fst, w v := by
  classical
  have hSub : S ⊆ (S.image Sigma.fst).sigma (fun v => (Finset.univ : Finset (Fin (w v)))) := by
    intro a ha
    exact Finset.mem_sigma.mpr ⟨Finset.mem_image.mpr ⟨a, ha, rfl⟩, Finset.mem_univ _⟩
  simpa only [Finset.card_sigma, Finset.card_univ, Fintype.card_fin] using Finset.card_le_card hSub

/-- The copied independence number equals the actual existing weighted maximum. -/
theorem independentBlowup_indepNum_eq_weightedMax :
    ((independentBlowup G w).indepNum : ℝ) = maxWeightIndependent G (fun v => (w v : ℝ)) := by
  classical
  apply le_antisymm
  · obtain ⟨S, hS⟩ := (independentBlowup G w).exists_isNIndepSet_indepNum
    let T := S.image Sigma.fst
    have hT : G.IsIndepSet (T : Set V) := independentBlowup_image_independent G w S hS.isIndepSet
    have hCard : (S.card : ℝ) ≤ ∑ v ∈ T, (w v : ℝ) := by
      exact_mod_cast copies_card_le_sum_weights w S
    have hMax : (∑ v ∈ T, (w v : ℝ)) ≤ maxWeightIndependent G (fun v => (w v : ℝ)) :=
      Finset.le_sup' (fun U => ∑ v ∈ U, (w v : ℝ)) (show T ∈ independentFinsets G by simp [independentFinsets, hT])
    simpa only [hS.card_eq] using hCard.trans hMax
  · unfold maxWeightIndependent
    apply Finset.sup'_le
    intro S hS
    have hInd : G.IsIndepSet (S : Set V) := by
      simpa only [independentFinsets, Finset.mem_filter, Finset.mem_powerset,
        Finset.subset_univ, true_and] using hS
    have hBound := (independentBlowup_lift_independent G w S hInd).card_le_indepNum
    have hNat : (∑ v ∈ S, w v) ≤ (independentBlowup G w).indepNum := by
      simpa only [Finset.card_sigma, Finset.card_univ, Fintype.card_fin] using hBound
    change (∑ v ∈ S, (w v : ℝ)) ≤ ((independentBlowup G w).indepNum : ℝ)
    exact_mod_cast hNat

/-- Every integer weight sum of an independent set is bounded by this integer. -/
theorem integer_weight_independent_le (S : Finset V) (hS : G.IsIndepSet (S : Set V)) :
    (∑ v ∈ S, w v) ≤ (independentBlowup G w).indepNum := by
  classical
  have h := (independentBlowup_lift_independent G w S hS).card_le_indepNum
  simpa only [Finset.card_sigma, Finset.card_univ, Fintype.card_fin] using h

end
end AgtXIv.PerfectGraph
