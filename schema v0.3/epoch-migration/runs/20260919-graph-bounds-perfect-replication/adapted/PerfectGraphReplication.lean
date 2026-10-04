import PerfectGraphTrueTwin

/-!
Hereditary true-twin replication from the existing IsPerfect definition.
An induced subgraph with at most one copy embeds in the original graph.
If it contains both copies, a concrete graph isomorphism identifies it with
replication of the corresponding original induced graph. The previously
proved whole-graph coloring theorem then completes every induced case.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation

noncomputable section

variable {V : Type*} (G : SimpleGraph V) (x : V)

def collapseVertex : Option V → V
  | none => x
  | some v => v

/-- With at most one copy present, collapsing the copy is an induced embedding. -/
def singleCopyEmbedding (U : Set (Option V))
    (hNotBoth : ¬(none ∈ U ∧ some x ∈ U)) :
    (trueTwin G x).induce U ↪g G where
  toFun u := collapseVertex x u.val
  inj' := by
    rintro ⟨u, hu⟩ ⟨v, hv⟩ h
    apply Subtype.ext
    cases u with
    | none =>
      cases v with
      | none => rfl
      | some v =>
        change x = v at h
        exact False.elim (hNotBoth ⟨hu, by simpa only [← h] using hv⟩)
    | some u =>
      cases v with
      | none =>
        change u = x at h
        exact False.elim (hNotBoth ⟨hv, by simpa only [h] using hu⟩)
      | some v =>
        change u = v at h
        exact congrArg Option.some h
  map_rel_iff' := by
    rintro ⟨u, hu⟩ ⟨v, hv⟩
    cases u with
    | none =>
      cases v with
      | none =>
        change G.Adj x x ↔ False
        simp
      | some v =>
        have hne : v ≠ x := by
          intro h
          exact hNotBoth ⟨hu, by simpa only [h] using hv⟩
        change G.Adj x v ↔ v = x ∨ G.Adj x v
        simp only [hne, false_or]
    | some u =>
      cases v with
      | none =>
        have hne : u ≠ x := by
          intro h
          exact hNotBoth ⟨hv, by simpa only [h] using hu⟩
        change G.Adj u x ↔ u = x ∨ G.Adj x u
        simp only [hne, false_or, G.adj_comm]
      | some v => rfl

/-- Both copies present: an actual equivalence of the entire vertex and edge sets. -/
def bothCopiesIso (U : Set (Option V)) (hNone : none ∈ U) (hX : some x ∈ U) :
    trueTwin (G.induce {v : V | some v ∈ U}) ⟨x, hX⟩ ≃g (trueTwin G x).induce U where
  toEquiv :=
    { toFun := fun u => match u with
        | none => ⟨none, hNone⟩
        | some v => ⟨some v.val, v.property⟩
      invFun := fun u => match h : u.val with
        | none => none
        | some v => some ⟨v, by change some v ∈ U; rw [← h]; exact u.property⟩
      left_inv := by intro u; cases u <;> rfl
      right_inv := by rintro ⟨u, hu⟩; cases u <;> rfl }
  map_rel_iff' := by
    intro u v
    cases u with
    | none =>
      cases v with
      | none => rfl
      | some v =>
        change (v.val = x ∨ G.Adj x v.val) ↔
          (v = (⟨x, hX⟩ : {v : V | some v ∈ U}) ∨ G.Adj x v.val)
        simp only [Subtype.ext_iff]
    | some u =>
      cases v with
      | none =>
        change (u.val = x ∨ G.Adj x u.val) ↔
          (u = (⟨x, hX⟩ : {v : V | some v ∈ U}) ∨ G.Adj x u.val)
        simp only [Subtype.ext_iff]
      | some v => rfl

/-- The complete replication lemma: all induced subgraphs satisfy chi=omega.
No replication certificate or weighted perfect-graph foundation is a premise. -/
theorem trueTwin_isPerfect [Fintype V] [DecidableEq V] (hPerfect : IsPerfect G) :
    IsPerfect (trueTwin G x) := by
  classical
  intro U
  by_cases hBoth : none ∈ U ∧ some x ∈ U
  · let S : Set V := {v | some v ∈ U}
    have hOld : IsPerfect (G.induce S) := perfect_induce hPerfect S
    have hRep := trueTwin_chromatic_eq_cliqueNum (G.induce S) ⟨x, hBoth.2⟩ hOld
    let e := bothCopiesIso G x U hBoth.1 hBoth.2
    rw [← chromaticNumber_eq_of_iso e, ← cliqueNum_eq_of_iso e]
    exact hRep
  · have hOld := perfect_of_embedding (singleCopyEmbedding G x U hBoth) hPerfect
    exact chromaticNumber_eq_cliqueNum_of_perfect hOld

end
end AgtXIv.PerfectGraph
