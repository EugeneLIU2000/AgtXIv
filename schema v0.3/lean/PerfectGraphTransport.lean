import PerfectGraphColorClass

/-!
Explicit finite graph transport for the hereditary perfectness definition.
No perfect-graph theorem or weighted certificate is assumed. An induced
embedding is identified with the induced graph on its image, and both clique
and chromatic numbers are transported by constructed graph isomorphisms.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation

noncomputable section

variable {V W : Type*} [Fintype V] [Fintype W]
variable {G : SimpleGraph V} {H : SimpleGraph W}

theorem cliqueNum_le_of_embedding (e : G ↪g H) : G.cliqueNum ≤ H.cliqueNum := by
  classical
  obtain ⟨Q, hQ⟩ := G.exists_isNClique_cliqueNum
  have hMap : H.IsClique ((Q.map e.toEmbedding : Finset W) : Set W) := by
    intro v hv w hw hvw
    obtain ⟨a, ha, rfl⟩ := Finset.mem_map.mp hv
    obtain ⟨b, hb, rfl⟩ := Finset.mem_map.mp hw
    exact e.map_adj_iff.mpr (hQ.isClique ha hb (fun hab => hvw (congrArg e hab)))
  simpa only [Finset.card_map, hQ.card_eq] using hMap.card_le_cliqueNum

theorem cliqueNum_eq_of_iso (e : G ≃g H) : G.cliqueNum = H.cliqueNum :=
  le_antisymm (cliqueNum_le_of_embedding e.toEmbedding)
    (cliqueNum_le_of_embedding e.symm.toEmbedding)

theorem chromaticNumber_eq_of_iso (e : G ≃g H) : G.chromaticNumber = H.chromaticNumber := by
  apply le_antisymm
  · exact SimpleGraph.chromaticNumber_mono_of_hom e.toHom
  · exact SimpleGraph.chromaticNumber_mono_of_hom e.symm.toHom

/-- An induced embedding is a graph isomorphism onto the induced image. -/
def embeddingRangeIso (e : G ↪g H) : G ≃g H.induce (Set.range e) where
  toEquiv := Equiv.ofInjective e e.injective
  map_rel_iff' := by
    intro a b
    change H.Adj (e a) (e b) ↔ G.Adj a b
    exact e.map_adj_iff

/-- Perfection passes to every induced embedding, by its actual induced image. -/
theorem perfect_of_embedding (e : G ↪g H) (hPerfect : IsPerfect H) : IsPerfect G := by
  classical
  intro S
  let f : G.induce S ↪g H := e.comp (SimpleGraph.Embedding.induce S)
  let i := embeddingRangeIso f
  rw [chromaticNumber_eq_of_iso i, cliqueNum_eq_of_iso i]
  exact hPerfect (Set.range f)

theorem perfect_induce (hPerfect : IsPerfect G) (S : Set V) [Fintype S] : IsPerfect (G.induce S) := by
  classical
  exact perfect_of_embedding (SimpleGraph.Embedding.induce S) hPerfect

theorem perfect_iff_of_iso (e : G ≃g H) : IsPerfect G ↔ IsPerfect H :=
  ⟨fun h => perfect_of_embedding e.symm.toEmbedding h,
    fun h => perfect_of_embedding e.toEmbedding h⟩

theorem chromaticNumber_eq_cliqueNum_of_perfect (hPerfect : IsPerfect G) :
    G.chromaticNumber = G.cliqueNum := by
  classical
  have h := hPerfect Set.univ
  rwa [chromaticNumber_eq_of_iso (SimpleGraph.induceUnivIso G),
    cliqueNum_eq_of_iso (SimpleGraph.induceUnivIso G)] at h

theorem colorable_cliqueNum_of_perfect (hPerfect : IsPerfect G) : G.Colorable G.cliqueNum := by
  exact SimpleGraph.chromaticNumber_le_iff_colorable.mp
    (le_of_eq (chromaticNumber_eq_cliqueNum_of_perfect hPerfect))

end
end AgtXIv.PerfectGraph
