import JordanWignerCapacity

/-! Uncompiled candidate for the outer maximum in Proposition Universal ceiling.
The domain includes all finite indexed MeasurementWindows in the solvable
regime, with arbitrary window cardinality. Source alignment is unreviewed.
-/

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation

noncomputable section

def solvableWindowCapacities (n : ℕ) : Set ℝ :=
  {c | ∃ (m : ℕ) (W : MeasurementWindow n m),
    W.NoActiveDependencies ∧ IsPerfect W.contextFrustrationGraph ∧
      c = witnessCapacity W}

theorem sqrt_dimension_isGreatest_solvableWindowCapacities
    (n : ℕ) (hn : 0 < n) :
    IsGreatest (solvableWindowCapacities n) (Real.sqrt (2 * (n : ℝ) + 1)) := by
  constructor
  · refine ⟨2 * n + 1, AgtXIv.JordanWigner.window n hn,
      AgtXIv.JordanWigner.window_noActiveDependencies n hn,
      AgtXIv.JordanWigner.window_graph_isPerfect n hn, ?_⟩
    exact (AgtXIv.JordanWigner.window_witnessCapacity n hn).symm
  · rintro c ⟨m, W, hNoActive, hPerfect, rfl⟩
    exact witnessCapacity_le_sqrt_dimension_ceiling W hNoActive hPerfect

end
end AgtXIv.ReducedRoM
