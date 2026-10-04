import AnticommutingMatrixBound
import ReducedRoMGraphDual

/-! Uncompiled bridge from actual measurement-window Pauli observables to the
general matrix-unit bound. This is a separate route from PauliCliqueGramFactor;
no equality of source provenance or kernel verification is asserted.
-/

namespace AgtXIv.PauliCliqueMatrixBound

open AgtXIv.Stabilizer AgtXIv.Varela

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

theorem observable_matrix_mul_self (i : Fin m) :
    (W.observable i).toCMatrix * (W.observable i).toCMatrix = 1 := by
  rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
  have hs : W.observable i * W.observable i = 1 := by
    simpa only [pow_two] using W.involutive i
  rw [hs, Pauli.one_toCMatrix]

def observableUnit (i : Fin m) : (Matrix (Fin (2 ^ n)) (Fin (2 ^ n)) ℂ)ˣ where
  val := (W.observable i).toCMatrix
  inv := (W.observable i).toCMatrix
  val_inv := observable_matrix_mul_self W i
  inv_val := observable_matrix_mul_self W i

theorem observable_matrix_anticommute (i j : Fin m)
    (h : ¬(W.observable i).commutesWith (W.observable j)) :
    (observableUnit W i : Matrix (Fin (2 ^ n)) (Fin (2 ^ n)) ℂ) *
        (observableUnit W j : Matrix (Fin (2 ^ n)) (Fin (2 ^ n)) ℂ) =
      -((observableUnit W j : Matrix (Fin (2 ^ n)) (Fin (2 ^ n)) ℂ) *
        (observableUnit W i : Matrix (Fin (2 ^ n)) (Fin (2 ^ n)) ℂ)) := by
  have hp := congrArg (fun P : Pauli n => P.toCMatrix)
    (Pauli.mul_anticomm_of_not_commutesWith (W.observable i) (W.observable j) h)
  simp only [Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix, Pauli.toCMatrix_neg] at hp
  exact hp

theorem indexed_noncommuting_family_bound {r : ℕ} (f : Fin r → Fin m)
    (h : ∀ i j, i ≠ j → ¬(W.observable (f i)).commutesWith (W.observable (f j))) :
    r ≤ 2 * n + 1 := by
  apply AgtXIv.AnticommutingMatrixBound.family_card_le_two_mul_add_one
    (K := ℂ) (by norm_num) (fun i => observableUnit W (f i))
  intro i j hij
  exact observable_matrix_anticommute W (f i) (f j) (h i j hij)

theorem clique_card_le_two_mul_add_one (Q : Finset (Fin m))
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) :
    Q.card ≤ 2 * n + 1 := by
  classical
  let e := Fintype.equivFin Q
  have h := indexed_noncommuting_family_bound W (fun i => (e.symm i).val) (by
    intro i j hij
    have hv : (e.symm i).val ≠ (e.symm j).val := by
      intro heq
      exact hij (e.symm.injective (Subtype.ext heq))
    exact hQ (e.symm i).property (e.symm j).property hv)
  simpa using h

end

end AgtXIv.PauliCliqueMatrixBound
