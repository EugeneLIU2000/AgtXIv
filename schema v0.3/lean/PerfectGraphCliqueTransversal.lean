import PerfectGraphCliqueFibres

/-!
Counting proof of a clique meeting every maximum independent set. Vertices of
the auxiliary graph are actual occurrences (S,v) of vertices in independent
sets. Projection to v has clique fibres, whereas projection to S is injective
on each clique. No complement-perfectness theorem is an assumption.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation
open scoped BigOperators

noncomputable section

variable {V W : Type*} [Fintype V] [Fintype W]
variable (G : SimpleGraph V) (H : SimpleGraph W) (f : W → V)

/-- An independent set contains at most one vertex in each clique fibre. -/
theorem cliqueFibres_injOn_independent (hf : HasCliqueFibres G H f)
    (S : Finset W) (hS : H.IsIndepSet (S : Set W)) : Set.InjOn f (S : Set W) := by
  intro a ha b hb heq
  by_contra hne
  exact hS ha hb hne ((hf a b).mpr ⟨hne, Or.inl heq⟩)

/-- Projection of an independent set is independent in the original graph. -/
theorem cliqueFibres_image_independent [DecidableEq V] (hf : HasCliqueFibres G H f)
    (S : Finset W) (hS : H.IsIndepSet (S : Set W)) :
    G.IsIndepSet (S.image f : Set V) := by
  intro a ha b hb hne hab
  obtain ⟨x, hx, rfl⟩ := Finset.mem_image.mp ha
  obtain ⟨y, hy, rfl⟩ := Finset.mem_image.mp hb
  have hxy : x ≠ y := fun heq => hne (congrArg f heq)
  exact hS hx hy hxy ((hf x y).mpr ⟨hxy, Or.inr hab⟩)

/-- Independent colour classes in any clique replication have size at most
that of a maximum independent set of the original graph. -/
theorem cliqueFibres_independent_card_le (hf : HasCliqueFibres G H f)
    (S : Finset W) (hS : H.IsIndepSet (S : Set W)) : S.card ≤ G.indepNum := by
  classical
  have hImage := cliqueFibres_image_independent G H f hf S hS
  rw [← Finset.card_image_of_injOn (cliqueFibres_injOn_independent G H f hf S hS)]
  exact hImage.card_le_indepNum

/-- A colouring and the maximum independent-set bound bound the whole size. -/
theorem card_le_colors_mul_indepNum {k : ℕ} (C : H.Coloring (Fin k))
    (hf : HasCliqueFibres G H f) : Fintype.card W ≤ k * G.indepNum := by
  classical
  have hCount : (Finset.univ : Finset W).card =
      ∑ c : Fin k, (Finset.univ.filter fun w => C w = c).card :=
    Finset.card_eq_sum_card_fiberwise (fun _ _ => Finset.mem_univ _)
  calc
    Fintype.card W = ∑ c : Fin k, (Finset.univ.filter fun w => C w = c).card := hCount
    _ ≤ ∑ _c : Fin k, G.indepNum := by
      apply Finset.sum_le_sum
      intro c _
      apply cliqueFibres_independent_card_le G H f hf
      intro a ha b hb hab
      exact C.not_adj_of_mem_colorClass (Finset.mem_filter.mp ha).2
        (Finset.mem_filter.mp hb).2
    _ = k * G.indepNum := by simp

variable (F : Finset (Finset V))

/-- A vertex together with a specific independent set in which it occurs. -/
abbrev IndependentOccurrence := Σ S : F, (S.val : Set V)

/-- Actual edges on occurrences: true twins over the same original vertex. -/
def occurrenceGraph : SimpleGraph (IndependentOccurrence F) where
  Adj a b := a ≠ b ∧ (a.2.val = b.2.val ∨ G.Adj a.2.val b.2.val)
  symm := by
    constructor
    intro a b h
    exact ⟨Ne.symm h.1, h.2.elim (fun e => Or.inl e.symm) (fun e => Or.inr e.symm)⟩
  loopless := by constructor; intro a h; exact h.1 rfl

theorem occurrenceGraph_isPerfect (hG : IsPerfect G) : IsPerfect (occurrenceGraph G F) := by
  classical
  exact perfect_of_cliqueFibres G (occurrenceGraph G F) (fun a => a.2.val) hG
    (fun _ _ => Iff.rfl)

/-- Each occurrence carries one member of a maximum independent set. -/
theorem occurrence_card (hF : ∀ S ∈ F, G.IsNIndepSet G.indepNum S) :
    Fintype.card (IndependentOccurrence F) = F.card * G.indepNum := by
  classical
  rw [Fintype.card_sigma]
  calc
    (∑ S : F, Fintype.card (S.val : Set V)) = ∑ _S : F, G.indepNum := by
      apply Finset.sum_congr rfl
      intro S _
      simpa using (hF S.val S.property).card_eq
    _ = F.card * G.indepNum := by simp

/-- In a clique, distinct occurrences must come from distinct independent sets. -/
theorem occurrence_family_injective (hF : ∀ S ∈ F, G.IsIndepSet (S : Set V))
    (Q : Finset (IndependentOccurrence F))
    (hQ : (occurrenceGraph G F).IsClique (Q : Set (IndependentOccurrence F))) :
    Function.Injective (fun q : Q => q.val.1) := by
  intro a b heq
  change a.val.1 = b.val.1 at heq
  apply Subtype.ext
  by_contra hne
  have hadj := hQ a.property b.property hne
  rcases hadj.2 with hsame | hadj
  · exact hne (Sigma.subtype_ext heq hsame)
  · have hA : a.val.2.val ∈ a.val.1.val := a.val.2.property
    have hB : b.val.2.val ∈ a.val.1.val := by
      exact (congrArg (fun T : F => b.val.2.val ∈ T.val) heq).mpr b.val.2.property
    exact (hF a.val.1.val a.val.1.property) hA hB hadj.ne hadj

/-- Projecting an occurrence clique gives an actual clique of the original graph. -/
theorem occurrence_clique_image [DecidableEq V]
    (Q : Finset (IndependentOccurrence F))
    (hQ : (occurrenceGraph G F).IsClique (Q : Set (IndependentOccurrence F))) :
    G.IsClique (Q.image (fun q => q.2.val) : Set V) := by
  intro a ha b hb hne
  obtain ⟨x, hx, rfl⟩ := Finset.mem_image.mp ha
  obtain ⟨y, hy, rfl⟩ := Finset.mem_image.mp hb
  have hxy : x ≠ y := fun heq => hne (congrArg (fun q : IndependentOccurrence F => q.2.val) heq)
  exact (hQ hx hy hxy).2.resolve_left hne

/-- A finite perfect graph with positive independence number has a clique
meeting every member of any family of maximum independent sets. -/
theorem exists_clique_meeting_maximum_family [DecidableEq V]
    (hG : IsPerfect G) (hAlpha : 0 < G.indepNum)
    (hF : ∀ S ∈ F, G.IsNIndepSet G.indepNum S) :
    ∃ Q : Finset V, G.IsClique (Q : Set V) ∧ ∀ S ∈ F, ∃ v ∈ Q, v ∈ S := by
  classical
  let K := occurrenceGraph G F
  have hKP : IsPerfect K := occurrenceGraph_isPerfect G F hG
  obtain ⟨C⟩ := colorable_cliqueNum_of_perfect hKP
  have hCard := card_le_colors_mul_indepNum G K (fun q => q.2.val) C
    (fun _ _ => Iff.rfl)
  rw [occurrence_card G F hF] at hCard
  have hLower : F.card ≤ K.cliqueNum := Nat.le_of_mul_le_mul_right hCard hAlpha
  obtain ⟨R, hR⟩ := K.exists_isNClique_cliqueNum
  have hInj := occurrence_family_injective G F (fun S hS => (hF S hS).isIndepSet) R hR.isClique
  have hUpper : R.card ≤ F.card := by
    simpa using Fintype.card_le_of_injective _ hInj
  have hEq : Fintype.card R = Fintype.card F := by
    simp only [Fintype.card_coe]
    exact le_antisymm hUpper (by simpa only [hR.card_eq] using hLower)
  have hSurj := ((Fintype.bijective_iff_injective_and_card (fun q : R => q.val.1)).mpr
    ⟨hInj, hEq⟩).2
  refine ⟨R.image (fun q => q.2.val), occurrence_clique_image G F R hR.isClique, ?_⟩
  intro S hS
  obtain ⟨q, hq⟩ := hSurj ⟨S, hS⟩
  refine ⟨q.val.2.val, Finset.mem_image.mpr ⟨q.val, q.property, rfl⟩, ?_⟩
  have hm := q.val.2.property
  have hv : q.val.1.val = S := congrArg Subtype.val hq
  exact (congrArg (fun T : Finset V => q.val.2.val ∈ T) hv).mp hm

/-- The full collection of maximum independent sets, represented finitely. -/
def maximumIndependentFamily [DecidableEq V] : Finset (Finset V) := by
  classical
  exact Finset.univ.filter (G.IsNIndepSet G.indepNum)

@[simp] theorem mem_maximumIndependentFamily [DecidableEq V] (S : Finset V) :
    S ∈ maximumIndependentFamily G ↔ G.IsNIndepSet G.indepNum S := by
  classical
  simp [maximumIndependentFamily]

/-- The transversal needed for deletion induction in the weak perfect theorem. -/
theorem exists_clique_meeting_all_maximum [DecidableEq V]
    (hG : IsPerfect G) (hAlpha : 0 < G.indepNum) :
    ∃ Q : Finset V, G.IsClique (Q : Set V) ∧
      ∀ S : Finset V, G.IsNIndepSet G.indepNum S → ∃ v ∈ Q, v ∈ S := by
  classical
  obtain ⟨Q, hQ, hMeet⟩ := exists_clique_meeting_maximum_family G
    (maximumIndependentFamily G) hG hAlpha (fun S hS => (mem_maximumIndependentFamily G S).mp hS)
  exact ⟨Q, hQ, fun S hS => hMeet S ((mem_maximumIndependentFamily G S).mpr hS)⟩

end
end AgtXIv.PerfectGraph
