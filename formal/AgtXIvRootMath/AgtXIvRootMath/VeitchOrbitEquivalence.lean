import AgtXIvRootMath.PauliCliffordTransitivity
import AgtXIvRootMath.VeitchOrbitBridge

/-!
# Exact equivalence of the two pure stabilizer presentations

Clifford transitivity now supplies the reverse direction missing from
`VeitchOrbitBridge`: every complete-frame common-eigenspace projector lies in
the semantic Clifford orbit of the computational zero projector.  Together
with the previously proved covariance direction this identifies the two atom
predicates by theorem, not by definition.
-/

namespace AgtXIv.Stabilizer

noncomputable section

/-- Every complete-frame atom is an exact semantic Clifford-orbit atom. -/
theorem pureStabilizerByFrame_implies_byCliffordOrbit (n : ℕ)
    (rho : CMatrix (2 ^ n) (2 ^ n))
    (hFrame : PureStabilizerByFrame n rho) :
    PureStabilizerByCliffordOrbit n rho := by
  obtain ⟨F, rfl⟩ := hFrame
  obtain ⟨C, hC⟩ :=
    F.exists_semanticClifford_map_standardIndependentZFrame
  refine ⟨C, ?_⟩
  unfold frameAtom
  rw [← stabilizerProjectorMatrix_standard_eq_computationalZeroProjector]
  rw [C.conjugate_stabilizerProjectorMatrix]
  rw [hC]

/-- Common-`+1` complete-frame pure stabilizers are exactly the pure states
in the semantic Clifford orbit of the computational zero projector. -/
theorem pureStabilizerByFrame_iff_byCliffordOrbit (n : ℕ)
    (rho : CMatrix (2 ^ n) (2 ^ n)) :
    PureStabilizerByFrame n rho ↔ PureStabilizerByCliffordOrbit n rho := by
  constructor
  · exact pureStabilizerByFrame_implies_byCliffordOrbit n rho
  · exact pureStabilizerByCliffordOrbit_implies_byFrame n rho

end

end AgtXIv.Stabilizer
