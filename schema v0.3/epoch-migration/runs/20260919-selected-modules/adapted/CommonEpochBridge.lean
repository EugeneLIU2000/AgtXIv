import EpochAdmissibleSigns
import QuantumInfo.States.Mixed.MState

/-!
Both inputs now live in the same Physlib/mathlib epoch. The admissible-domain
equality remains explicit: this is not the paper's sign-collapse theorem.
-/

namespace AgtXIv.CommonEpoch

open scoped BigOperators

theorem quantum_admissible_sign_maximum
    {d ι : Type*} [Fintype d] [DecidableEq d] [Fintype ι]
    (ρ : MState d) (A : ι → HermitianMat d ℂ)
    (admissible : Set (ι → ℝ)) (μ : ℝ)
    (hCollapse : admissible = {f | ∀ i, AgtXIv.Stabilizerness.IsSign (f i)}) :
    IsGreatest
      (AgtXIv.Stabilizerness.admissibleSignedValues admissible (fun i => ρ.exp_val (A i)) μ)
      ((∑ i, |ρ.exp_val (A i)|) + |μ|) :=
  AgtXIv.Stabilizerness.max_abs_admissible_signed_sum_of_sign_set_eq
    admissible (fun i => ρ.exp_val (A i)) μ hCollapse

end AgtXIv.CommonEpoch
