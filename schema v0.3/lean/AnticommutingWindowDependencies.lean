import ReducedRoMGraphDual

/-! Uncompiled candidate prerequisite for the Jordan–Wigner construction.
A pairwise anticommuting window has no active dependencies because a commuting
subset has at most one member, and singleton scalar observables are excluded.
This does not construct a window with 2n+1 observables.
-/

namespace AgtXIv.Varela.MeasurementWindow

open AgtXIv.Stabilizer

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

theorem noActiveDependencies_of_pairwise_noncommuting
    (hAnti : ∀ i j : Fin m, i ≠ j → ¬(W.observable i).commutesWith (W.observable j)) :
    W.NoActiveDependencies := by
  classical
  intro T hActive
  obtain ⟨i, hi⟩ := hActive.1.1
  have hOnly : ∀ j ∈ T, j = i := by
    intro j hj
    by_contra hji
    exact hAnti j i hji (hActive.2 hj hi hji)
  have hSingleton : T = {i} := Finset.eq_singleton_iff_unique_mem.mpr ⟨hi, hOnly⟩
  have hZero := (W.scalar_subsetProduct_iff_zero_sum T).mp hActive.1.2.1
  rw [hSingleton] at hZero
  exact W.nonidentitySupport i (by simpa using hZero)

end
end AgtXIv.Varela.MeasurementWindow
