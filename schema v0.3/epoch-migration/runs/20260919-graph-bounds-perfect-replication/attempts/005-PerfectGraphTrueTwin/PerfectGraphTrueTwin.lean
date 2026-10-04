import PerfectGraphTransport

/-!
True-twin replication on Option V: none is adjacent to the distinguished old
vertex and all its neighbors. The old graph is retained exactly on some V.
This module proves chi = omega for the entire replicated graph from actual
IsPerfect G. The hereditary induced-subgraph step is kept separate.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation

noncomputable section

variable {V : Type*} (G : SimpleGraph V) (x : V)

/-- Adjacent replication, distinct from independent false-twin multiplication. -/
def trueTwin : SimpleGraph (Option V) where
  Adj a b := match a, b with
    | none, none => False
    | none, some v => v = x ∨ G.Adj x v
    | some v, none => v = x ∨ G.Adj x v
    | some v, some w => G.Adj v w
  symm := by
    intro a b h
    cases a <;> cases b
    · exact h
    · exact h
    · exact h
    · exact G.symm h
  loopless := by
    constructor
    intro a h
    cases a with
    | none => exact h
    | some v => exact G.ne_of_adj h rfl

@[simp] theorem trueTwin_adj_some (v w : V) :
    (trueTwin G x).Adj (some v) (some w) ↔ G.Adj v w := Iff.rfl

@[simp] theorem trueTwin_adj_none (v : V) :
    (trueTwin G x).Adj none (some v) ↔ v = x ∨ G.Adj x v := Iff.rfl

def oldEmbedding : G ↪g trueTwin G x where
  toFun := Option.some
  inj' := Option.some_injective V
  map_rel_iff' := by intro v w; rfl

def oldSubsetEmbedding (S : Set V) : G.induce S ↪g trueTwin G x where
  toFun v := some v.val
  inj' := by intro v w h; exact Subtype.ext (Option.some.inj h)
  map_rel_iff' := by intro v w; rfl

theorem none_not_mem_oldSubset_range (S : Set V) :
    none ∉ Set.range (oldSubsetEmbedding G x S) := by
  rintro ⟨v, h⟩
  change some v.val = none at h
  cases h

theorem some_mem_oldSubset_range (S : Set V) (v : V) :
    some v ∈ Set.range (oldSubsetEmbedding G x S) ↔ v ∈ S := by
  constructor
  · rintro ⟨w, hw⟩
    have h : w.val = v := Option.some.inj hw
    simpa only [h] using w.property
  · exact fun h => ⟨⟨v, h⟩, rfl⟩

/-- Always available: assign the new vertex a fresh color. -/
def coloringWithFreshTwin {k : ℕ} (C : G.Coloring (Fin k)) :
    (trueTwin G x).Coloring (Fin (k + 1)) := by
  refine SimpleGraph.Coloring.mk
    (fun v => match v with | none => Fin.last k | some w => (C w).castSucc) ?_
  intro v w hvw
  cases v <;> cases w
  · exact False.elim hvw
  · exact (Fin.castSucc_ne_last _).symm
  · exact Fin.castSucc_ne_last _
  · exact fun h => C.valid hvw (Fin.castSucc_inj.mp h)

theorem old_clique_lift (Q : Finset V) (hQ : G.IsClique (Q : Set V)) :
    (trueTwin G x).IsClique
      ((Q.map (oldEmbedding G x).toEmbedding : Finset (Option V)) : Set (Option V)) := by
  intro v hv w hw hvw
  obtain ⟨a, ha, rfl⟩ := Finset.mem_map.mp hv
  obtain ⟨b, hb, rfl⟩ := Finset.mem_map.mp hw
  exact hQ ha hb (fun hab => hvw (congrArg (oldEmbedding G x) hab))

theorem clique_with_twin [DecidableEq V] (Q : Finset V)
    (hQ : G.IsClique (Q : Set V)) (hx : x ∈ Q) :
    (trueTwin G x).IsClique
      ((insert none (Q.map (oldEmbedding G x).toEmbedding) : Finset (Option V)) : Set (Option V)) := by
  rw [Finset.coe_insert]
  apply (old_clique_lift G x Q hQ).insert
  intro v hv _
  obtain ⟨w, hw, rfl⟩ := Finset.mem_map.mp hv
  by_cases h : w = x
  · exact Or.inl h
  · exact Or.inr (hQ hx hw (fun hxw => h hxw.symm))

variable [Fintype V] [DecidableEq V]

theorem cliqueNum_succ_le_trueTwin_of_mem_maximum
    (Q : Finset V) (hQ : G.IsClique (Q : Set V))
    (hCard : Q.card = G.cliqueNum) (hx : x ∈ Q) :
    G.cliqueNum + 1 ≤ (trueTwin G x).cliqueNum := by
  have hClique := clique_with_twin G x Q hQ hx
  have hNone : (none : Option V) ∉ Q.map (oldEmbedding G x).toEmbedding := by
    simp [oldEmbedding]
  have hLe := hClique.card_le_cliqueNum
  rwa [Finset.card_insert_of_notMem hNone, Finset.card_map, hCard] at hLe

/-- In the hard case, the new twin together with the removed old color class
is a genuine independent block. -/
theorem removed_with_twin_independent {k : ℕ} (C : G.Coloring (Fin k)) :
    (trueTwin G x).IsIndepSet
      (Set.range (oldSubsetEmbedding G x (retainedVertices C x)))ᶜ := by
  intro v hv w hw _ hvw
  have outside (u : V)
      (h : some u ∉ Set.range (oldSubsetEmbedding G x (retainedVertices C x))) :
      u ≠ x ∧ C u = C x := by
    have hn : u ∉ retainedVertices C x := fun hu =>
      h ((some_mem_oldSubset_range G x _ u).mpr hu)
    change ¬(u = x ∨ C u ≠ C x) at hn
    exact ⟨(not_or.mp hn).1, Classical.not_not.mp (not_or.mp hn).2⟩
  cases v with
  | none =>
    cases w with
    | none => exact hvw
    | some w =>
      obtain ⟨hne, hc⟩ := outside w hw
      rcases hvw with hEq | hAdj
      · exact hne hEq
      · exact C.valid hAdj hc.symm
  | some v =>
    cases w with
    | none =>
      obtain ⟨hne, hc⟩ := outside v hv
      rcases hvw with hEq | hAdj
      · exact hne hEq
      · exact C.valid hAdj hc.symm
    | some w =>
      exact C.valid hvw ((outside v hv).2.trans (outside w hw).2.symm)

theorem trueTwin_colorable_of_no_maximum_clique {k : ℕ}
    (hPerfect : IsPerfect G) (C : G.Coloring (Fin k))
    (hNoMax : ∀ Q : Finset V, G.IsClique (Q : Set V) → Q.card = k → x ∉ Q) :
    (trueTwin G x).Colorable k := by
  classical
  let T := retainedVertices C x
  let e := oldSubsetEmbedding G x T
  have hOld : (G.induce T).Colorable (k - 1) := perfect_retained_colorable hPerfect C x hNoMax
  have hImage : ((trueTwin G x).induce (Set.range e)).Colorable (k - 1) :=
    SimpleGraph.Colorable.of_hom (embeddingRangeIso e).symm.toHom hOld
  have hImage' : ((trueTwin G x).induce ((Set.range e)ᶜ)ᶜ).Colorable (k - 1) := by
    have hDouble : ((Set.range e)ᶜ)ᶜ = Set.range e := by ext v; simp
    rw [hDouble]
    exact hImage
  have hColor := colorable_with_independent_block (Set.range e)ᶜ
    (removed_with_twin_independent G x C) hImage'
  have hk : 1 ≤ k := by have := (C x).isLt; omega
  simpa only [Nat.sub_add_cancel hk] using hColor

/-- Chi equals omega for the whole replicated graph, with both cases proved.
Hereditary perfection requires the subsequent induced-subgraph transport. -/
theorem trueTwin_chromatic_eq_cliqueNum (hPerfect : IsPerfect G) :
    (trueTwin G x).chromaticNumber = (trueTwin G x).cliqueNum := by
  classical
  obtain ⟨C⟩ := colorable_cliqueNum_of_perfect hPerfect
  apply le_antisymm _ SimpleGraph.cliqueNum_le_chromaticNumber
  by_cases h : ∃ Q : Finset V, G.IsClique (Q : Set V) ∧ Q.card = G.cliqueNum ∧ x ∈ Q
  · obtain ⟨Q, hQ, hCard, hx⟩ := h
    have hColor : (trueTwin G x).Colorable (G.cliqueNum + 1) := ⟨coloringWithFreshTwin G x C⟩
    apply hColor.chromaticNumber_le.trans
    exact_mod_cast cliqueNum_succ_le_trueTwin_of_mem_maximum G x Q hQ hCard hx
  · have hNoMax : ∀ Q : Finset V, G.IsClique (Q : Set V) → Q.card = G.cliqueNum → x ∉ Q := by
      intro Q hQ hCard hx
      exact h ⟨Q, hQ, hCard, hx⟩
    have hColor := trueTwin_colorable_of_no_maximum_clique G x hPerfect C hNoMax
    apply hColor.chromaticNumber_le.trans
    exact_mod_cast cliqueNum_le_of_embedding (oldEmbedding G x)

end
end AgtXIv.PerfectGraph
