import AgtXIvVarela
import AnticommutingNonvacuity

/-!
The concrete finite Pauli measurement model and the frozen local PhyslibAlpha
uncertainty theorem share the same density matrices and expectation values.
This module is an extension of the migrated case, not one of its original 82
modules. It proves the operator/graph specialization, not the RoM closed form.
-/

namespace AgtXIv.ConcretePhyslib

open scoped BigOperators
open AgtXIv.Stabilizer AgtXIv.Varela

noncomputable section

def densityToMState {d : ℕ} (ρ : DensityMatrix d) : MState (Fin d) where
  M := ⟨ρ.val, ρ.posSemidef.1⟩
  nonneg := HermitianMat.zero_le_iff.mpr ρ.posSemidef
  tr := by
    rw [HermitianMat.trace_eq_re_trace]
    change (Matrix.trace ρ.val).re = 1
    rw [ρ.trace_one]
    rfl

def mStateToDensity {d : ℕ} (ρ : MState (Fin d)) : DensityMatrix d where
  val := ρ.m
  posSemidef := ρ.psd
  trace_one := ρ.tr'

@[simp] theorem densityToMState_mat {d : ℕ} (ρ : DensityMatrix d) :
    (densityToMState ρ).m = ρ.val := rfl

@[simp] theorem mStateToDensity_val {d : ℕ} (ρ : MState (Fin d)) :
    (mStateToDensity ρ).val = ρ.m := rfl

@[simp] theorem density_roundtrip {d : ℕ} (ρ : DensityMatrix d) :
    mStateToDensity (densityToMState ρ) = ρ := by
  cases ρ
  rfl

@[simp] theorem mState_roundtrip {d : ℕ} (ρ : MState (Fin d)) :
    densityToMState (mStateToDensity ρ) = ρ := by
  apply MState.ext_m
  rfl

theorem trace_preserved {d : ℕ} (ρ : DensityMatrix d) :
    (densityToMState ρ).m.trace = ρ.val.trace := rfl

def observable {n m : ℕ} (W : MeasurementWindow n m) (i : Fin m) :
    HermitianMat (Fin (2 ^ n)) ℂ :=
  ⟨(W.observable i).toCMatrix,
    pauli_toCMatrix_isHermitian_of_sq_eq_one _ (W.involutive i)⟩

@[simp] theorem observable_mat {n m : ℕ} (W : MeasurementWindow n m) (i : Fin m) :
    (observable W i).mat = (W.observable i).toCMatrix := rfl

theorem observable_sq {n m : ℕ} (W : MeasurementWindow n m) (i : Fin m) :
    observable W i ^ 2 = 1 := by
  apply HermitianMat.ext
  rw [HermitianMat.mat_pow, HermitianMat.mat_one, pow_two]
  change (W.observable i).toCMatrix * (W.observable i).toCMatrix = 1
  rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix, ← pow_two,
    W.involutive, Pauli.one_toCMatrix]

/-- The actual frustration graph: adjacency is failure of Pauli commutation. -/
def frustrationGraph {n m : ℕ} (W : MeasurementWindow n m) : SimpleGraph (Fin m) where
  Adj i j := ¬(W.observable i).commutesWith (W.observable j)
  symm := by
    constructor
    intro i j hij hji
    apply hij
    exact (Pauli.commutesWith_iff _ _).mpr ((Pauli.commutesWith_iff _ _).mp hji).symm
  loopless := by
    constructor
    intro i hii
    apply hii
    exact (Pauli.commutesWith_iff _ _).mpr (Commute.refl _)

theorem matrix_anticomm_of_adj {n m : ℕ} (W : MeasurementWindow n m)
    (i j : Fin m) (h : (frustrationGraph W).Adj i j) :
    (observable W i).mat * (observable W j).mat =
      -((observable W j).mat * (observable W i).mat) := by
  have hp := Pauli.mul_anticomm_of_not_commutesWith (W.observable i) (W.observable j) h
  have hm := congrArg Pauli.toCMatrix hp
  simpa only [Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix, Pauli.toCMatrix_neg] using hm

theorem expectation_preserved {n m : ℕ} (W : MeasurementWindow n m)
    (ρ : DensityMatrix (2 ^ n)) (i : Fin m) :
    W.expectationCoordinate i ρ.toTraceOneHermitian.1 =
      (densityToMState ρ).exp_val (observable W i) := by
  rw [AgtXIv.PhyslibCandidate.expectation_eq_real_trace]
  rfl

/-- No separate Hermiticity, involution or graph/operator premise is assumed:
all three are discharged from the concrete window and its frustration graph. -/
theorem window_clique_l2_bound {n m : ℕ} (W : MeasurementWindow n m)
    (ρ : DensityMatrix (2 ^ n)) (s : Finset (Fin m))
    (hs : (frustrationGraph W).IsClique (s : Set (Fin m))) :
    ∑ i ∈ s, (W.expectationCoordinate i ρ.toTraceOneHermitian.1) ^ 2 ≤ 1 := by
  simp_rw [expectation_preserved]
  exact (densityToMState ρ).sum_sq_exp_val_finset_le_one_of_pairwise_anticommute
    s (observable W) (fun i _ => observable_sq W i)
    (fun i hi j hj hij => matrix_anticomm_of_adj W i j (hs hi hj hij))

theorem window_clique_l1_bound {n m : ℕ} (W : MeasurementWindow n m)
    (ρ : DensityMatrix (2 ^ n)) (s : Finset (Fin m))
    (hs : (frustrationGraph W).IsClique (s : Set (Fin m))) :
    ∑ i ∈ s, |W.expectationCoordinate i ρ.toTraceOneHermitian.1| ≤
      Real.sqrt (s.card : ℝ) := by
  simp_rw [expectation_preserved]
  exact (densityToMState ρ).sum_abs_exp_val_finset_le_sqrt_card_of_pairwise_anticommute
    s (observable W) (fun i _ => observable_sq W i)
    (fun i hi j hj hij => matrix_anticomm_of_adj W i j (hs hi hj hij))

theorem window_cliqueNumber_bound {n m : ℕ} (W : MeasurementWindow n m)
    (ρ : DensityMatrix (2 ^ n)) (s : Finset (Fin m))
    (hs : (frustrationGraph W).IsClique (s : Set (Fin m))) :
    ∑ i ∈ s, |W.expectationCoordinate i ρ.toTraceOneHermitian.1| ≤
      Real.sqrt ((frustrationGraph W).cliqueNum : ℝ) := by
  exact (window_clique_l1_bound W ρ s hs).trans
    (Real.sqrt_le_sqrt (Nat.cast_le.mpr hs.card_le_cliqueNum))

def singleZWindow : MeasurementWindow 1 1 where
  nonempty := by decide
  observable := fun _ => Pauli.Z
  involutive := by intro i; decide
  nonidentitySupport := by intro i; decide
  distinctPhaseClass := by intro i j _; exact Subsingleton.elim i j

theorem concrete_window_nonvacuity :
    ∃ (W : MeasurementWindow 1 1) (ρ : DensityMatrix 2),
      W.observable 0 = Pauli.Z ∧
      (∀ i, W.observable i ≠ 1) ∧
      ∑ i ∈ ({0} : Finset (Fin 1)), (W.expectationCoordinate i ρ.toTraceOneHermitian.1) ^ 2 ≤ 1 := by
  refine ⟨singleZWindow, mStateToDensity MState.uniform, rfl, ?_, ?_⟩
  · intro i
    decide
  · apply window_clique_l2_bound
    exact (frustrationGraph singleZWindow).isClique_singleton 0

end
end AgtXIv.ConcretePhyslib
