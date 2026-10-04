import PerfectGraphCliqueTransversal

/-!
The weak perfect-graph theorem from the actual replication and transversal
proofs. Deleting a clique meeting all maximum independent sets strictly lowers
the independence number. Induction constructs a complement colouring using
exactly that many available colours, hence an integral clique partition.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation

noncomputable section

universe u

variable {V : Type u} [Fintype V] (G : SimpleGraph V)

/-- Complement commutes with induced subgraphs, including the subtype inequality. -/
theorem complement_induce (S : Set V) : (G.induce S)ᶜ = Gᶜ.induce S := by
  ext a b
  change (a ≠ b ∧ ¬G.Adj a.val b.val) ↔ (a.val ≠ b.val ∧ ¬G.Adj a.val b.val)
  constructor
  · rintro ⟨hne, h⟩
    exact ⟨fun heq => hne (Subtype.ext heq), h⟩
  · rintro ⟨hne, h⟩
    exact ⟨fun heq => hne (congrArg Subtype.val heq), h⟩

/-- Lift an independent set of an induced graph without changing its size. -/
theorem induced_independent_lift (S : Set V) (T : Finset S)
    (hT : (G.induce S).IsIndepSet (T : Set S)) :
    G.IsIndepSet ((T.map ⟨Subtype.val, Subtype.val_injective⟩ : Finset V) : Set V) := by
  intro a ha b hb hne hadj
  obtain ⟨x, hx, rfl⟩ := Finset.mem_map.mp ha
  obtain ⟨y, hy, rfl⟩ := Finset.mem_map.mp hb
  exact hT hx hy (fun heq => hne (congrArg Subtype.val heq)) hadj

/-- A transversal to all maximum independent sets forces a strict drop on deletion. -/
theorem indepNum_delete_transversal_lt [DecidableEq V] (Q : Finset V)
    (hMeet : ∀ T : Finset V, G.IsNIndepSet G.indepNum T → ∃ v ∈ Q, v ∈ T) :
    (G.induce (Q : Set V)ᶜ).indepNum < G.indepNum := by
  classical
  let S : Set V := (Q : Set V)ᶜ
  obtain ⟨T, hT⟩ := (G.induce S).exists_isNIndepSet_indepNum
  let U : Finset V := T.map ⟨Subtype.val, Subtype.val_injective⟩
  have hU : G.IsIndepSet (U : Set V) := induced_independent_lift G S T hT.isIndepSet
  have hLe : U.card ≤ G.indepNum := hU.card_le_indepNum
  have hLt : U.card < G.indepNum := by
    by_contra hnot
    have hEq : U.card = G.indepNum := by omega
    obtain ⟨v, hvQ, hvU⟩ := hMeet U ⟨hU, hEq⟩
    obtain ⟨w, hw, rfl⟩ := Finset.mem_map.mp hvU
    exact w.property hvQ
  simpa only [U, Finset.card_map, hT.card_eq] using hLt

/-- The constructive integral clique-cover conclusion: a complement colouring
with alpha(G) colours, derived solely from hereditary perfection of G. -/
theorem complement_colorable_indepNum (hG : IsPerfect G) : Gᶜ.Colorable G.indepNum := by
  classical
  have aux : ∀ n : ℕ, ∀ (V : Type u) [Fintype V], ∀ G : SimpleGraph V,
      Fintype.card V ≤ n → IsPerfect G → Gᶜ.Colorable G.indepNum := by
    intro n
    induction n using Nat.strong_induction_on with
    | h n ih =>
      intro V inst G hCard hG
      by_cases hV : Nonempty V
      · obtain ⟨v⟩ := hV
        have hSingle : G.IsIndepSet ({v} : Finset V) := by simp
        have hAlpha : 0 < G.indepNum := by
          have := hSingle.card_le_indepNum
          simpa using this
        obtain ⟨Q, hQ, hMeet⟩ := exists_clique_meeting_all_maximum G hG hAlpha
        obtain ⟨T, hT⟩ := G.exists_isNIndepSet_indepNum
        obtain ⟨q, hq, _⟩ := hMeet T hT
        let S : Set V := (Q : Set V)ᶜ
        have hlt : Fintype.card S < n := lt_of_lt_of_le
          (Fintype.card_subtype_lt (x := q) (by exact fun h => h hq)) hCard
        have hSmall := ih (Fintype.card S) hlt S (G.induce S) le_rfl (perfect_induce hG S)
        have hSmall' : (Gᶜ.induce S).Colorable (G.induce S).indepNum := by
          rwa [complement_induce] at hSmall
        have hIndependent : Gᶜ.IsIndepSet (Q : Set V) := by simpa using hQ
        have hRestored := colorable_with_independent_block (G := Gᶜ) (Q : Set V) hIndependent hSmall'
        have hDrop := indepNum_delete_transversal_lt G Q hMeet
        exact hRestored.mono (by dsimp [S]; omega)
      · letI : IsEmpty V := not_nonempty_iff.mp hV
        exact ⟨SimpleGraph.Coloring.mk (fun v => isEmptyElim v) (by intro v; exact isEmptyElim v)⟩
  exact aux (Fintype.card V) V G le_rfl hG

/-- The complement satisfies chi=omega on its entire vertex set. -/
theorem complement_chromatic_eq_cliqueNum (hG : IsPerfect G) :
    Gᶜ.chromaticNumber = Gᶜ.cliqueNum := by
  apply le_antisymm
  · rw [SimpleGraph.cliqueNum_compl]
    exact SimpleGraph.chromaticNumber_le_iff_colorable.mpr (complement_colorable_indepNum G hG)
  · exact Gᶜ.cliqueNum_le_chromaticNumber

/-- Weak perfect-graph theorem, with no complement or duality certificate premise. -/
theorem complement_isPerfect (hG : IsPerfect G) : IsPerfect Gᶜ := by
  classical
  intro S
  have h := complement_chromatic_eq_cliqueNum (G.induce S) (perfect_induce hG S)
  rwa [complement_induce] at h

/-- The original graph and its complement are perfect simultaneously. -/
theorem isPerfect_complement_iff : IsPerfect Gᶜ ↔ IsPerfect G := by
  constructor
  · intro h
    simpa using complement_isPerfect Gᶜ h
  · exact complement_isPerfect G

/-- An explicit family of alpha(G) cliques partitions every vertex exactly once. -/
theorem exists_integral_clique_partition [DecidableEq V] (hG : IsPerfect G) :
    ∃ Q : Fin G.indepNum → Finset V,
      (∀ i, G.IsClique (Q i : Set V)) ∧ ∀ v, ∃! i, v ∈ Q i := by
  classical
  obtain ⟨C⟩ := complement_colorable_indepNum G hG
  refine ⟨fun i => Finset.univ.filter (fun v => C v = i), ?_, ?_⟩
  · intro i
    have h := C.isIndepSet_colorClass i
    rw [SimpleGraph.isIndepSet_compl] at h
    simpa [SimpleGraph.Coloring.colorClass] using h
  · intro v
    refine ⟨C v, by simp, ?_⟩
    intro i hi
    exact (Finset.mem_filter.mp hi).2.symm

end
end AgtXIv.PerfectGraph
