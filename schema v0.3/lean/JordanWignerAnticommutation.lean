import JordanWignerCoordinatePairing
import JordanWignerWindow
import F2CoordinateDot
import AnticommutingWindowDependencies

/-! Uncompiled connection to the original Pauli Boolean commutation relation.
All conclusions depend on the uncompiled coordinate-dot bridge; no runtime
or source-alignment acceptance is claimed here.
-/

namespace AgtXIv.JordanWigner

open AgtXIv.Stabilizer AgtXIv.Varela
open scoped BigOperators

noncomputable section

theorem symplectic_support_eq_coordinatePairing {n : ℕ} (a b : Index n) :
    F2Support.symplecticForm (support a) (support b) = coordinatePairing a b := by
  have ha := support_coordinates a
  have hb := support_coordinates b
  change (F2Bits.coordinate (support a).1, F2Bits.coordinate (support a).2) = coordinates a at ha
  change (F2Bits.coordinate (support b).1, F2Bits.coordinate (support b).2) = coordinates b at hb
  obtain ⟨haz, hax⟩ := Prod.mk.inj ha
  obtain ⟨hbz, hbx⟩ := Prod.mk.inj hb
  simp only [F2Support.symplecticForm_apply, F2Support.symplecticValue,
    F2Bits.dot_eq_sum_coordinates, coordinatePairing]
  rw [hax, haz, hbx, hbz]
  rfl

theorem observable_not_commutes {n : ℕ} (a b : Index n) (hne : a ≠ b) :
    ¬(observable a).commutesWith (observable b) := by
  intro hComm
  have hZero := (F2Support.pauli_commutes_iff_symplectic_eq_zero
    (observable a) (observable b)).mp hComm
  rw [observable_support, observable_support, symplectic_support_eq_coordinatePairing,
    coordinatePairing_eq_one_of_ne a b hne] at hZero
  exact one_ne_zero hZero

theorem observable_anticommutes {n : ℕ} (a b : Index n) (hne : a ≠ b) :
    observable a * observable b = -(observable b * observable a) :=
  Pauli.mul_anticomm_of_not_commutesWith _ _ (observable_not_commutes a b hne)

theorem window_pairwise_noncommuting (n : ℕ) (hn : 0 < n)
    (i j : Fin (2 * n + 1)) (hne : i ≠ j) :
    ¬((window n hn).observable i).commutesWith ((window n hn).observable j) := by
  apply observable_not_commutes
  exact fun h => hne ((indexEquiv n).symm.injective h)

theorem window_noActiveDependencies (n : ℕ) (hn : 0 < n) :
    (window n hn).NoActiveDependencies :=
  (window n hn).noActiveDependencies_of_pairwise_noncommuting
    (window_pairwise_noncommuting n hn)

end
end AgtXIv.JordanWigner
