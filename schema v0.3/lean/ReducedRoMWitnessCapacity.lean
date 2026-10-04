import PositiveCliqueState

/-! Uncompiled candidate for draft.tex's witness-capacity identity.
The value set uses actual density matrices and reducedRoM, not a graph-defined
replacement. The dimension bound 2n+1 and its extremal characterization remain
separate mathematical obligations.
-/

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

def witnessValues : Set ℝ :=
  Set.range (fun ρ : DensityMatrix (2 ^ n) => reducedRoM W ρ)

def witnessCapacity : ℝ := sSup (witnessValues W)

theorem sqrt_cliqueNum_isGreatest_witnessValues
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    IsGreatest (witnessValues W) (Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ)) := by
  obtain ⟨ρ, hρ⟩ := exists_reducedRoM_sqrt_attainer W hNoActive hPerfect
  refine ⟨⟨ρ, hρ⟩, ?_⟩
  rintro z ⟨σ, rfl⟩
  exact reducedRoM_le_sqrt_cliqueNum W σ hNoActive hPerfect

theorem witnessCapacity_eq_sqrt_cliqueNum
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    witnessCapacity W = Real.sqrt (W.contextFrustrationGraph.cliqueNum : ℝ) :=
  (sqrt_cliqueNum_isGreatest_witnessValues W hNoActive hPerfect).csSup_eq

end
end AgtXIv.ReducedRoM
