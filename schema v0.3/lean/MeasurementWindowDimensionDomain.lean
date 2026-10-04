import AgtXIvVarela.MeasurementProjection
import AgtXIvRootMath.F2Coordinates

/-! Uncompiled domain facts for the existing normalized MeasurementWindow.
They explain why a nonempty nonidentity window already entails n > 0. They do
not decide whether the paper intends to permit an empty measurement set.
-/

namespace AgtXIv.Varela.MeasurementWindow

open AgtXIv.Stabilizer

theorem qubit_count_pos {n m : ℕ} (W : MeasurementWindow n m) : 0 < n := by
  classical
  by_contra hn
  have hn0 : n = 0 := Nat.eq_zero_of_not_pos hn
  subst n
  let i : Fin m := ⟨0, W.nonempty⟩
  apply W.nonidentitySupport i
  apply (F2Support.coordinateEquiv 0).injective
  exact Subsingleton.elim _ _

theorem no_zero_qubit_window (m : ℕ) : ¬Nonempty (MeasurementWindow 0 m) := by
  rintro ⟨W⟩
  exact (Nat.lt_irrefl 0) (qubit_count_pos W)

end AgtXIv.Varela.MeasurementWindow
