import JordanWignerAnticommutation
import ReducedRoMDimensionCeiling

/-! Uncompiled endpoint for the explicit JW window. The existing window and
Pauli operations are retained; complete-graph and perfectness statements are
derived rather than installed as certificate assumptions.
-/

namespace AgtXIv.JordanWigner

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation AgtXIv.ReducedRoM

noncomputable section

theorem window_graph_eq_top (n : ℕ) (hn : 0 < n) :
    (window n hn).contextFrustrationGraph = ⊤ := by
  ext i j
  change (¬((window n hn).observable i).commutesWith ((window n hn).observable j)) ↔ i ≠ j
  constructor
  · intro h heq
    subst j
    exact h ((Pauli.commutesWith_iff _ _).mpr (Commute.refl _))
  · exact window_pairwise_noncommuting n hn i j

private theorem cliqueNum_top_eq_card (V : Type*) [Fintype V] :
    (⊤ : SimpleGraph V).cliqueNum = Fintype.card V := by
  classical
  apply le_antisymm
  · obtain ⟨s, hs⟩ := (⊤ : SimpleGraph V).exists_isNClique_cliqueNum
    rw [← hs.card_eq]
    exact Finset.card_le_univ s
  · have hClique : (⊤ : SimpleGraph V).IsClique ((Finset.univ : Finset V) : Set V) := by
      intro i _ j _ hij
      exact hij
    have h := SimpleGraph.IsClique.card_le_cliqueNum (tc := hClique)
    simpa using h

theorem window_graph_isPerfect (n : ℕ) (hn : 0 < n) :
    IsPerfect (window n hn).contextFrustrationGraph := by
  classical
  rw [window_graph_eq_top]
  intro S
  have hInduce : (⊤ : SimpleGraph (Fin (2 * n + 1))).induce S = ⊤ := by
    ext i j
    simp [Subtype.ext_iff]
  rw [hInduce, SimpleGraph.chromaticNumber_top, cliqueNum_top_eq_card]

theorem window_cliqueNum (n : ℕ) (hn : 0 < n) :
    (window n hn).contextFrustrationGraph.cliqueNum = 2 * n + 1 := by
  rw [window_graph_eq_top, cliqueNum_top_eq_card, Fintype.card_fin]

theorem window_witnessCapacity (n : ℕ) (hn : 0 < n) :
    witnessCapacity (window n hn) = Real.sqrt (2 * (n : ℝ) + 1) := by
  rw [witnessCapacity_eq_sqrt_cliqueNum (window n hn)
    (window_noActiveDependencies n hn) (window_graph_isPerfect n hn), window_cliqueNum]
  norm_cast

theorem window_exists_attainer (n : ℕ) (hn : 0 < n) :
    ∃ ρ : DensityMatrix (2 ^ n),
      reducedRoM (window n hn) ρ = Real.sqrt (2 * (n : ℝ) + 1) := by
  obtain ⟨ρ, hρ⟩ := exists_reducedRoM_sqrt_attainer (window n hn)
    (window_noActiveDependencies n hn) (window_graph_isPerfect n hn)
  refine ⟨ρ, ?_⟩
  simpa [window_cliqueNum] using hρ

/-- The complete, explicitly constructed JW window has exactly its full-set
minimal dependency, and this dependency is inactive. Uncompiled candidate. -/
theorem window_unique_inactive_dependency (n : ℕ) (hn : 0 < n) :
    (window n hn).IsPauliDependency Finset.univ ∧
    ¬ (window n hn).IsActiveDependency Finset.univ ∧
    ∀ U : Finset (Fin (2 * n + 1)),
      (window n hn).IsPauliDependency U → U = Finset.univ := by
  classical
  have hClique : (window n hn).contextFrustrationGraph.IsClique
      ((Finset.univ : Finset (Fin (2 * n + 1))) : Set (Fin (2 * n + 1))) := by
    intro i hi j hj hne
    exact window_pairwise_noncommuting n hn i j hne
  have hCard : (Finset.univ : Finset (Fin (2 * n + 1))).card = 2 * n + 1 := by simp
  obtain ⟨hDependency, hInactive, hUnique⟩ :=
    AgtXIv.PauliCliqueGram.maximum_clique_unique_inactive_dependency
      (window n hn) Finset.univ hn hClique hCard
  exact ⟨hDependency, hInactive, fun U hU => hUnique U (Finset.subset_univ U) hU⟩

end
end AgtXIv.JordanWigner
