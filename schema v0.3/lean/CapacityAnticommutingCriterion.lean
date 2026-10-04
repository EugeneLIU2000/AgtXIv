import ReducedRoMDimensionCeiling

/-! Uncompiled candidate: the equality criterion stated with actual Pauli
multiplication, not only graph terminology. Source alignment remains pending. -/

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

def HasCeilingAnticommutingSet : Prop :=
  ∃ Q : Finset (Fin m), Q.card = 2 * n + 1 ∧
    ∀ i ∈ Q, ∀ j ∈ Q, i ≠ j →
      W.observable i * W.observable j = -(W.observable j * W.observable i)

theorem cliqueNum_eq_ceiling_iff_anticommutingSet :
    W.contextFrustrationGraph.cliqueNum = 2 * n + 1 ↔
      HasCeilingAnticommutingSet W := by
  classical
  constructor
  · intro h
    obtain ⟨Q, hQ⟩ := W.contextFrustrationGraph.exists_isNClique_cliqueNum
    refine ⟨Q, hQ.card_eq.trans h, ?_⟩
    intro i hi j hj hne
    exact Pauli.mul_anticomm_of_not_commutesWith _ _ (hQ.isClique hi hj hne)
  · rintro ⟨Q, hCard, hAnti⟩
    have hClique : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)) := by
      intro i hi j hj hne
      change ¬(W.observable i).commutesWith (W.observable j)
      intro hComm
      have hp := hAnti i hi j hj hne
      have hc := ((Pauli.commutesWith_iff _ _).mp hComm).eq
      rw [hc] at hp
      exact AgtXIv.ConcretePhyslib.pauli_ne_neg _ hp
    apply Nat.le_antisymm (window_cliqueNum_le_two_mul_add_one W)
    rw [← hCard]
    exact hClique.card_le_cliqueNum

theorem witnessCapacity_eq_ceiling_iff_anticommutingSet
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    witnessCapacity W = Real.sqrt (2 * (n : ℝ) + 1) ↔
      HasCeilingAnticommutingSet W :=
  (witnessCapacity_eq_ceiling_iff_cliqueNum W hNoActive hPerfect).trans
    (cliqueNum_eq_ceiling_iff_anticommutingSet W)

end
end AgtXIv.ReducedRoM
