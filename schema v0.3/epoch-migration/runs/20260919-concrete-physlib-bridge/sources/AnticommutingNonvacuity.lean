import AnticommutingWitness
import Physlib.Relativity.PauliMatrices.Basic
import Mathlib.Combinatorics.SimpleGraph.Clique

namespace AgtXIv.PhyslibCandidate

open scoped BigOperators

/-- Bridge the library's real expectation API to the paper's trace notation. -/
theorem expectation_eq_real_trace
    {d : Type*} [Fintype d] [DecidableEq d]
    (ρ : MState d) (A : HermitianMat d ℂ) :
    ρ.exp_val A = ((A.mat * ρ.m).trace).re := by
  rw [MState.exp_val, HermitianMat.inner_eq_re_trace, Matrix.trace_mul_comm]
  rfl

/-- Trace-form version of the paper's finite anticommuting-family l2 bound.
Pauli-specific involution and anticommutation remain explicit hypotheses. -/
theorem anticommuting_real_trace_l2_bound
    {d V : Type*} [Fintype d] [DecidableEq d] [DecidableEq V]
    (ρ : MState d) (s : Finset V) (A : V → HermitianMat d ℂ)
    (hInv : ∀ i ∈ s, A i ^ 2 = 1)
    (hAnti : ∀ i ∈ s, ∀ j ∈ s, i ≠ j →
      (A i).mat * (A j).mat = -((A j).mat * (A i).mat)) :
    ∑ i ∈ s, (((A i).mat * ρ.m).trace).re ^ 2 ≤ 1 := by
  simp_rw [← expectation_eq_real_trace]
  exact ρ.sum_sq_exp_val_finset_le_one_of_pairwise_anticommute s A hInv hAnti

/-- The paper's clique uncertainty argument, with the graph-to-operator
correspondence retained as explicit hypotheses. This does not define RoM. -/
theorem graph_clique_expectation_bound
    {d V : Type*} [Fintype d] [DecidableEq d] [Fintype V] [DecidableEq V]
    (ρ : MState d) (G : SimpleGraph V) (A : V → HermitianMat d ℂ)
    (hInv : ∀ i, A i ^ 2 = 1)
    (hAdj : ∀ i j, G.Adj i j → (A i).mat * (A j).mat = -((A j).mat * (A i).mat))
    (s : Finset V) (hs : G.IsClique (s : Set V)) :
    ∑ i ∈ s, |ρ.exp_val (A i)| ≤ Real.sqrt (G.cliqueNum : ℝ) := by
  have hfamily := ρ.sum_abs_exp_val_finset_le_sqrt_card_of_pairwise_anticommute
    s A (fun i _ => hInv i) (fun i hi j hj hij => hAdj i j (hs hi hj hij))
  exact hfamily.trans (Real.sqrt_le_sqrt (Nat.cast_le.mpr hs.card_le_cliqueNum))

noncomputable def pauliZ : HermitianMat (Fin 2) ℂ :=
  ⟨PauliMatrix.pauliMatrix (Sum.inr 2), PauliMatrix.pauliMatrix_selfAdjoint _⟩

theorem pauliZ_sq : pauliZ ^ 2 = 1 := by
  apply HermitianMat.ext
  rw [HermitianMat.mat_pow, HermitianMat.mat_one, pow_two]
  exact PauliMatrix.pauliMatrix_mul_self (Sum.inr 2)

theorem pauliZ_ne_one : pauliZ ≠ 1 := by
  intro h
  have hentry : (-1 : ℂ) = 1 :=
    congrArg (fun A : HermitianMat (Fin 2) ℂ => A.mat 1 1) h
  norm_num at hentry

/-- A concrete trace-one state and nonidentity Pauli observable inhabit the
bound's domain. This does not close the arbitrary-n graph specialization. -/
theorem anticommuting_bound_nonvacuity :
    ∃ (_ρ : MState (Fin 2)) (A : Fin 1 → HermitianMat (Fin 2) ℂ),
      (∀ i, A i ^ 2 = 1) ∧
      (∀ i j, i ≠ j → (A i).mat * (A j).mat = -((A j).mat * (A i).mat)) ∧
      (∀ i, A i ≠ 1) := by
  refine ⟨MState.uniform, fun _ => pauliZ, ?_, ?_, ?_⟩
  · intro i
    exact pauliZ_sq
  · intro i j hij
    exact False.elim (hij (Subsingleton.elim i j))
  · intro i
    exact pauliZ_ne_one

end AgtXIv.PhyslibCandidate
