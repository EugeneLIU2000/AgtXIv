import JordanWignerPauliFamily
import AgtXIvVarela.MeasurementProjection

/-! Uncompiled concrete measurement window. Numbering is a finite equivalence,
not a claim about conventional gamma index order or ordered-product phase.
Pairwise anticommutation and perfectness are not fields assumed here.
-/

namespace AgtXIv.JordanWigner

open AgtXIv.Stabilizer AgtXIv.Varela

noncomputable section

def indexEquiv (n : ℕ) : Index n ≃ Fin (2 * n + 1) :=
  (Fintype.equivFin (Index n)).trans (finCongr (index_card n))

def window (n : ℕ) (hn : 0 < n) : MeasurementWindow n (2 * n + 1) where
  nonempty := by omega
  observable i := observable ((indexEquiv n).symm i)
  involutive i := observable_sq _
  nonidentitySupport i := observable_nonidentitySupport hn _
  distinctPhaseClass := (observable_distinctPhaseClass n).comp (indexEquiv n).symm.injective

theorem window_observable_index (n : ℕ) (hn : 0 < n) (i : Index n) :
    (window n hn).observable (indexEquiv n i) = observable i := by
  simp [window]

theorem window_observable_surjective (n : ℕ) (hn : 0 < n) (i : Index n) :
    ∃ j : Fin (2 * n + 1), (window n hn).observable j = observable i :=
  ⟨indexEquiv n i, window_observable_index n hn i⟩

end
end AgtXIv.JordanWigner
