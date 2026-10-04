import Quantumlib.Data.Gate.Pauli.Lemmas

/-!
Compatibility identities for the new MonoidAlgebra wrapper. These compare the
ported operations with the old finite-coefficient formulas; they are not paper
claim bindings and do not assert completion of the query proof.
-/

namespace AgtXIv.EpochCompatibility

noncomputable section

theorem normalized_coeff_formula {n : ℕ} (p : PauliMap n) :
    (PauliMap.normalized p).coeff =
      p.coeff.sum (fun P c => Finsupp.single P.zeroed (P.evalPhase * c)) := by
  classical
  simp only [PauliMap.normalized, PauliMap.normalized.f, Finsupp.sum,
    MonoidAlgebra.coeff_sum, MonoidAlgebra.coeff_single]

theorem ofPauli_coeff_formula {n : ℕ} (P : Pauli n) :
    (PauliMap.ofPauli P).coeff = Finsupp.single P.zeroed P.evalPhase := by
  simp only [PauliMap.ofPauli, PauliMap.normalized_single, mul_one,
    MonoidAlgebra.coeff_single]

theorem toCMatrix_coeff_formula {n : ℕ} (p : PauliMap n) :
    PauliMap.toCMatrix p = p.coeff.sum (fun P c => c • P.toCMatrix) := rfl

end

end AgtXIv.EpochCompatibility
