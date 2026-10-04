import GraphDualBounds
import PerfectGraphWeightedDuality

/-!
Uncompiled candidate: the existing RoM sandwich closes on a perfect graph.
Complement perfection is proved by the replication chain, not an extra premise.
No theta identity, quantum square-root bound or attainment claim is made here.
-/

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation
open AgtXIv.GraphDual AgtXIv.PerfectGraph

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n))

/-- The source's normalized maximum-clique-weight formula, with both original
branch hypotheses retained and no weighted integrality certificate assumed. -/
theorem reducedRoM_eq_max_one_clique_weight
    (hNoActive : W.NoActiveDependencies)
    (hPerfect : IsPerfect W.contextFrustrationGraph) :
    reducedRoM W ρ = max 1 (maxWeightClique W.contextFrustrationGraph
      (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|)) := by
  have hSandwich := reducedRoM_clique_cover_sandwich W ρ hNoActive
  have hComplement : IsPerfect W.contextFrustrationGraphᶜ :=
    complement_isPerfect W.contextFrustrationGraph hPerfect
  have hValue := fractionalCliqueCoverValue_eq_maxWeightIndependent
    W.contextFrustrationGraphᶜ hComplement
    (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|)
    (fun i => abs_nonneg _)
  rw [hValue, ← maxWeightClique_eq_complement_independent] at hSandwich
  exact le_antisymm hSandwich.2 hSandwich.1

end
end AgtXIv.ReducedRoM
