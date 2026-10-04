import AgtXIvVarela.ExternalPerfectGraphFoundation
import Mathlib

/-!
The color-class deletion step of the true-twin replication argument.
A k-coloring meets every k-clique in every color. If x is in no k-clique,
removing x's color class except x therefore lowers the clique number below k.
Perfection then supplies a (k-1)-coloring of the retained induced graph.
An independent removed block can be restored with one additional color.

This proves a genuine combinatorial foundation, not replication itself or
weighted perfect-graph duality. The local 1972 characterization cites Berge
1961 Theorem 1; that earlier proof's source alignment remains unresolved.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation

noncomputable section

variable {V : Type*} [Fintype V] [DecidableEq V] {G : SimpleGraph V} {k : ℕ}

/-- A full-size clique uses each color of the given k-coloring. -/
theorem clique_meets_each_color (C : G.Coloring (Fin k)) (Q : Finset V)
    (hQ : G.IsClique (Q : Set V)) (hCard : Q.card = k) (c : Fin k) :
    ∃ v ∈ Q, C v = c := by
  exact C.surjOn_of_card_le_isClique hQ (by simpa [hCard]) (Set.mem_univ c)

/-- Delete the color class of x except x itself. -/
def retainedVertices (C : G.Coloring (Fin k)) (x : V) : Set V :=
  {v | v = x ∨ C v ≠ C x}

theorem mem_retainedVertices (C : G.Coloring (Fin k)) (x v : V) :
    v ∈ retainedVertices C x ↔ v = x ∨ C v ≠ C x := Iff.rfl

/-- The removed vertices form an independent set and none is x. -/
theorem removed_color_class_independent (C : G.Coloring (Fin k)) (x : V) :
    G.IsIndepSet (retainedVertices C x)ᶜ := by
  intro v hv w hw hvw hAdj
  have hvC : C v = C x := by
    have h : ¬(v = x ∨ C v ≠ C x) := hv
    exact Classical.not_not.mp (not_or.mp h).2
  have hwC : C w = C x := by
    have h : ¬(w = x ∨ C w ≠ C x) := hw
    exact Classical.not_not.mp (not_or.mp h).2
  exact C.valid hAdj (hvC.trans hwC.symm)

/-- This is the substantive rank-drop step in replication's hard case. -/
theorem retained_clique_card_lt (C : G.Coloring (Fin k)) (x : V)
    (hNoMax : ∀ Q : Finset V, G.IsClique (Q : Set V) → Q.card = k → x ∉ Q)
    (Q : Finset V) (hQ : G.IsClique (Q : Set V))
    (hRetained : (Q : Set V) ⊆ retainedVertices C x) : Q.card < k := by
  have hLe : Q.card ≤ k := by simpa using hQ.card_le_of_coloring C
  by_contra hLt
  have hCard : Q.card = k := by omega
  obtain ⟨v, hv, hvC⟩ := clique_meets_each_color C Q hQ hCard (C x)
  have hvRetained := hRetained hv
  rcases hvRetained with hvx | hvNe
  · exact hNoMax Q hQ hCard (hvx ▸ hv)
  · exact hvNe hvC

/-- Lift a clique of an induced graph while retaining its cardinality. -/
theorem induced_clique_lift (S : Set V) (Q : Finset S)
    (hQ : (G.induce S).IsClique (Q : Set S)) :
    G.IsClique ((Q.map ⟨Subtype.val, Subtype.val_injective⟩ : Finset V) : Set V) := by
  intro v hv w hw hvw
  obtain ⟨a, ha, rfl⟩ := Finset.mem_map.mp hv
  obtain ⟨b, hb, rfl⟩ := Finset.mem_map.mp hw
  exact hQ ha hb (fun hab => hvw (congrArg Subtype.val hab))

theorem retained_cliqueNum_lt (C : G.Coloring (Fin k)) (x : V)
    (hNoMax : ∀ Q : Finset V, G.IsClique (Q : Set V) → Q.card = k → x ∉ Q) :
    (G.induce (retainedVertices C x)).cliqueNum < k := by
  classical
  obtain ⟨Q, hQ⟩ := (G.induce (retainedVertices C x)).exists_isNClique_cliqueNum
  let T : Finset V := Q.map ⟨Subtype.val, Subtype.val_injective⟩
  have hT : G.IsClique (T : Set V) := induced_clique_lift _ Q hQ.isClique
  have hSub : (T : Set V) ⊆ retainedVertices C x := by
    intro v hv
    obtain ⟨a, ha, rfl⟩ := Finset.mem_map.mp hv
    exact a.property
  have hLt := retained_clique_card_lt C x hNoMax T hT hSub
  simpa only [T, Finset.card_map, hQ.card_eq] using hLt

/-- The original IsPerfect definition discharges the smaller coloring. No
replication or weighted-duality certificate is supplied as a hypothesis. -/
theorem perfect_retained_colorable (hPerfect : IsPerfect G)
    (C : G.Coloring (Fin k)) (x : V)
    (hNoMax : ∀ Q : Finset V, G.IsClique (Q : Set V) → Q.card = k → x ∉ Q) :
    (G.induce (retainedVertices C x)).Colorable (k - 1) := by
  classical
  apply SimpleGraph.chromaticNumber_le_iff_colorable.mp
  rw [hPerfect (retainedVertices C x)]
  have hLt := retained_cliqueNum_lt C x hNoMax
  have hLe : (G.induce (retainedVertices C x)).cliqueNum ≤ k - 1 := by omega
  exact_mod_cast hLe

/-- Restore an independent block using a fresh last color. This is a concrete
coloring constructor, available to the next replication module. -/
def coloringWithIndependentBlock (S : Set V) (hS : G.IsIndepSet S)
    (C : (G.induce Sᶜ).Coloring (Fin k)) : G.Coloring (Fin (k + 1)) := by
  classical
  refine SimpleGraph.Coloring.mk
    (fun v => if hv : v ∈ S then Fin.last k else (C ⟨v, hv⟩).castSucc) ?_
  intro v w hvw
  by_cases hv : v ∈ S <;> by_cases hw : w ∈ S
  · exact False.elim (hS hv hw (G.ne_of_adj hvw) hvw)
  · simp only [dif_pos hv, dif_neg hw]
    exact (Fin.castSucc_ne_last _).symm
  · simp only [dif_neg hv, dif_pos hw]
    exact Fin.castSucc_ne_last _
  · simp only [dif_neg hv, dif_neg hw, ne_eq, Fin.castSucc_inj]
    exact C.valid hvw

theorem colorable_with_independent_block (S : Set V) (hS : G.IsIndepSet S)
    (hColor : (G.induce Sᶜ).Colorable k) : G.Colorable (k + 1) := by
  obtain ⟨C⟩ := hColor
  exact ⟨coloringWithIndependentBlock S hS C⟩

end
end AgtXIv.PerfectGraph
