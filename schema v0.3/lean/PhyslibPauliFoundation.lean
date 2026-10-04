import Physlib.Relativity.PauliMatrices.Basic

/-!
An actual Physlib-based foundation in its own Lean/mathlib epoch.
The Pauli-vector identity is relevant to the paper's anticommuting-observable
argument. It is not the arbitrary-n clique bound or the reduced-RoM theorem.
No cross-epoch composition with the existing RootMath packages is claimed.
-/

namespace AgtXIv.PhyslibFoundation

open scoped BigOperators

/-- A normalized real combination of the three Pauli matrices is involutive. -/
theorem normalized_pauli_combination_square
    (a : Fin 3 → ℝ) (hNorm : ∑ i : Fin 3, a i ^ 2 = 1) :
    PauliMatrix.vectorMatrix a * PauliMatrix.vectorMatrix a = 1 := by
  rw [PauliMatrix.vectorMatrix_sq, hNorm]
  simp

end AgtXIv.PhyslibFoundation
