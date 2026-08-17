import AgtXIvRootMath.StandardZProjectorBridge
import AgtXIvRootMath.SemanticCliffordFrames
import AgtXIvRootMath.VeitchStabilizerPolytope

/-!
# Common-eigenspace stabilizers and the Clifford orbit

The standard computational projector has already been identified with the
standard signed-`Z` group average.  Exact Clifford covariance therefore gives
one unconditional direction of the Gottesman-to-Veitch bridge: every state in
the semantic Clifford orbit is the group-average projector of a complete
signed Pauli frame.

The reverse direction requires the separate all-`n` Clifford-transitivity
theorem.  It is not encoded here as a premise or typeclass.
-/

namespace AgtXIv.Stabilizer

noncomputable section

/-- Veitch's pure-state presentation using the exact phase-aware semantic
Clifford orbit of the computational zero projector. -/
def PureStabilizerByCliffordOrbit (n : ℕ)
    (rho : CMatrix (2 ^ n) (2 ^ n)) : Prop :=
  SemanticClifford.InOrbit (computationalZeroProjector n) rho

/-- Every exact Clifford-orbit atom is a complete-frame common-eigenspace
atom.  This direction uses covariance only and has no transitivity premise. -/
theorem pureStabilizerByCliffordOrbit_implies_byFrame (n : ℕ)
    (rho : CMatrix (2 ^ n) (2 ^ n))
    (hOrbit : PureStabilizerByCliffordOrbit n rho) :
    PureStabilizerByFrame n rho := by
  obtain ⟨C, rfl⟩ := hOrbit
  refine ⟨C.mapFrame (standardIndependentZFrame n), ?_⟩
  unfold frameAtom
  rw [← C.conjugate_stabilizerProjectorMatrix]
  rw [stabilizerProjectorMatrix_standard_eq_computationalZeroProjector]

end

end AgtXIv.Stabilizer
