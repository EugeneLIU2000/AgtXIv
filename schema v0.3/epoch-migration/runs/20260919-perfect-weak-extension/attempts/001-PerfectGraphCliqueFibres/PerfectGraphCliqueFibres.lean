import PerfectGraphReplication

/-!
Finite clique substitution from actual one-vertex replication. A projection
whose fibres are cliques and whose cross-fibre edges are exactly the original
edges preserves hereditary perfectness. Empty and singleton fibres are allowed.
This proves integer replication without assuming complement perfection or
weighted perfect-graph duality.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation

noncomputable section

universe u v

variable {V : Type u} {W : Type v}
variable (G : SimpleGraph V) (H : SimpleGraph W) (f : W → V)

/-- Precise adjacency condition for finite clique fibres over a graph. -/
def HasCliqueFibres : Prop :=
  ∀ a b, H.Adj a b ↔ a ≠ b ∧ (f a = f b ∨ G.Adj (f a) (f b))

/-- If all fibres contain at most one vertex, the projection is induced. -/
def cliqueFibresEmbedding (hf : HasCliqueFibres G H f) (hinj : Function.Injective f) :
    H ↪g G where
  toFun := f
  inj' := hinj
  map_rel_iff' := by
    intro a b
    rw [hf a b]
    constructor
    · intro h
      exact ⟨fun hab => G.loopless.irrefl _ (hab ▸ h), Or.inr h⟩
    · rintro ⟨hne, heq | hadj⟩
      · exact False.elim (hne (hinj heq))
      · exact hadj

/-- Deleting one member of a repeated fibre identifies the graph with an
actual true-twin extension of the smaller induced graph. -/
def cliqueFibresDeleteIso [DecidableEq W]
    (hf : HasCliqueFibres G H f) (a b : W) (hab : a ≠ b) (hfib : f a = f b) :
    trueTwin (H.induce {w : W | w ≠ b}) ⟨a, hab⟩ ≃g H where
  toEquiv :=
    { toFun := fun u => match u with
        | none => b
        | some w => w.val
      invFun := fun w => if hw : w = b then none else some ⟨w, hw⟩
      left_inv := by
        intro u
        cases u with
        | none => simp
        | some w =>
          have hw : w.val ≠ b := w.property
          simp [hw]
      right_inv := by intro w; by_cases hw : w = b <;> simp [hw] }
  map_rel_iff' := by
    intro u v
    have hNeighbour (w : {w : W | w ≠ b}) :
        H.Adj b w.val ↔ w = (⟨a, hab⟩ : {w : W | w ≠ b}) ∨ H.Adj a w.val := by
      rw [hf b w.val, hf a w.val]
      simp only [Subtype.ext_iff]
      by_cases hwa : w.val = a
      · simp [hwa, Ne.symm hab, hfib]
      · simp [hwa, Ne.symm hwa, Ne.symm w.property, hfib]
    cases u with
    | none =>
      cases v with
      | none => change H.Adj b b ↔ False; simp
      | some w => exact hNeighbour w
    | some w =>
      cases v with
      | none =>
        change H.Adj w.val b ↔ w = (⟨a, hab⟩ : {w : W | w ≠ b}) ∨ H.Adj a w.val
        rw [H.adj_comm]
        exact hNeighbour w
      | some z => rfl

/-- The exact clique-fibre condition survives deletion of a vertex. -/
theorem hasCliqueFibres_induce (hf : HasCliqueFibres G H f) (S : Set W) :
    HasCliqueFibres G (H.induce S) (fun w => f w.val) := by
  intro a b
  change H.Adj a.val b.val ↔ _
  rw [hf a.val b.val]
  constructor
  · rintro ⟨hne, h⟩
    exact ⟨fun hab => hne (congrArg Subtype.val hab), h⟩
  · rintro ⟨hne, h⟩
    exact ⟨fun hab => hne (Subtype.ext hab), h⟩

/-- Arbitrarily many finite true twins preserve perfectness. The proof removes
one duplicate at each induction step; an injective projection is the base case. -/
theorem perfect_of_cliqueFibres [Fintype V] (hG : IsPerfect G)
    [Fintype W] (hf : HasCliqueFibres G H f) : IsPerfect H := by
  classical
  have aux : ∀ n : ℕ, ∀ (W : Type v) [Fintype W], ∀ (H : SimpleGraph W) (f : W → V),
      Fintype.card W ≤ n → HasCliqueFibres G H f → IsPerfect H := by
    intro n
    induction n using Nat.strong_induction_on with
    | h n ih =>
      intro W inst H f hCard hf
      by_cases hinj : Function.Injective f
      · exact perfect_of_embedding (cliqueFibresEmbedding G H f hf hinj) hG
      · obtain ⟨a, b, hfib, hab⟩ := Function.not_injective_iff.mp hinj
        let S : Set W := {w | w ≠ b}
        have hlt : Fintype.card S < n := lt_of_lt_of_le
          (Fintype.card_subtype_lt (x := b) (by simp [S])) hCard
        have hSmall : IsPerfect (H.induce S) :=
          ih (Fintype.card S) hlt S (H.induce S) (fun w => f w.val) le_rfl
            (hasCliqueFibres_induce G H f hf S)
        have hTwin : IsPerfect (trueTwin (H.induce S) ⟨a, hab⟩) :=
          trueTwin_isPerfect (H.induce S) ⟨a, hab⟩ hSmall
        exact (perfect_iff_of_iso (cliqueFibresDeleteIso G H f hf a b hab hfib)).mp hTwin
  exact aux (Fintype.card W) W H f le_rfl hf

/-- Integer multiplicity as a genuine finite vertex set, allowing zero copies. -/
def cliqueBlowup (w : V → ℕ) : SimpleGraph (Σ a : V, Fin (w a)) where
  Adj a b := a ≠ b ∧ (a.1 = b.1 ∨ G.Adj a.1 b.1)
  symm := by
    intro a b h
    exact ⟨Ne.symm h.1, h.2.elim (fun e => Or.inl e.symm) (fun e => Or.inr e.symm)⟩
  loopless := by constructor; intro a h; exact h.1 rfl

@[simp] theorem cliqueBlowup_adj (w : V → ℕ) (a b : Σ v : V, Fin (w v)) :
    (cliqueBlowup G w).Adj a b ↔ a ≠ b ∧ (a.1 = b.1 ∨ G.Adj a.1 b.1) := Iff.rfl

/-- A concrete arbitrary integer replication of a perfect graph is perfect. -/
theorem cliqueBlowup_isPerfect [Fintype V] (w : V → ℕ) (hG : IsPerfect G) :
    IsPerfect (cliqueBlowup G w) := by
  classical
  exact perfect_of_cliqueFibres G (cliqueBlowup G w) Sigma.fst hG (fun _ _ => Iff.rfl)

end
end AgtXIv.PerfectGraph
