import PerfectGraphWeakPerfect

/-!
Optimality of the constructed integral clique cover. A maximum independent set
can contribute at most one vertex to each covering clique, so every cover uses
at least alpha(G) cliques. This lower bound holds for any finite graph. Perfection
supplies an actual cover attaining it through the preceding constructive proof.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation

noncomputable section

variable {V : Type*} [Fintype V] (G : SimpleGraph V)

/-- Every integral clique cover, including overlapping or empty listed cliques,
has at least as many members as a maximum independent set has vertices. -/
theorem indepNum_le_clique_cover_size {k : ℕ} (Q : Fin k → Finset V)
    (hQ : ∀ i, G.IsClique (Q i : Set V)) (hCover : ∀ v, ∃ i, v ∈ Q i) :
    G.indepNum ≤ k := by
  classical
  obtain ⟨S, hS⟩ := G.exists_isNIndepSet_indepNum
  let c : S → Fin k := fun v => Classical.choose (hCover v.val)
  have hc (v : S) : v.val ∈ Q (c v) := Classical.choose_spec (hCover v.val)
  have hinj : Function.Injective c := by
    intro a b hab
    apply Subtype.ext
    by_contra hne
    have hb : b.val ∈ Q (c a) := by rw [hab]; exact hc b
    exact hS.isIndepSet a.property b.property hne (hQ (c a) (hc a) hb hne)
  have hBound := Fintype.card_le_of_injective c hinj
  simpa only [Fintype.card_coe, Fintype.card_fin, hS.card_eq] using hBound

/-- Both existence and optimality of an integral alpha(G)-clique cover. -/
theorem exists_optimal_integral_clique_cover [DecidableEq V] (hG : IsPerfect G) :
    ∃ Q : Fin G.indepNum → Finset V,
      (∀ i, G.IsClique (Q i : Set V)) ∧ (∀ v, ∃! i, v ∈ Q i) ∧
      ∀ (k : ℕ) (R : Fin k → Finset V),
        (∀ i, G.IsClique (R i : Set V)) → (∀ v, ∃ i, v ∈ R i) → G.indepNum ≤ k := by
  obtain ⟨Q, hQ, hCover⟩ := exists_integral_clique_partition G hG
  exact ⟨Q, hQ, hCover, fun _ R hR hRCover => indepNum_le_clique_cover_size G R hR hRCover⟩

end
end AgtXIv.PerfectGraph
