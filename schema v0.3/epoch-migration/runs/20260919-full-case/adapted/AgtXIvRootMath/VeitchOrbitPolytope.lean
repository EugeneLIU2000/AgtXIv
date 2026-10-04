import AgtXIvRootMath.VeitchConvexHull
import AgtXIvRootMath.VeitchOrbitEquivalence

/-!
# The stabilizer polytope in the Clifford-orbit presentation

The preceding modules prove, rather than assume, that complete signed-Pauli
frame projectors are exactly the semantic Clifford orbit of the computational
zero projector.  This file transfers that pointwise theorem to equality of
the corresponding atom sets and convex hulls.
-/

namespace AgtXIv.Stabilizer

noncomputable section

/-- The range of complete-frame projectors is exactly the set of pure
Clifford-orbit stabilizer projectors. -/
theorem range_frameAtom_eq_cliffordOrbitAtoms (n : ℕ) :
    Set.range (frameAtom n) =
      {rho : CMatrix (2 ^ n) (2 ^ n) |
        PureStabilizerByCliffordOrbit n rho} := by
  ext rho
  constructor
  · rintro ⟨F, rfl⟩
    exact pureStabilizerByFrame_implies_byCliffordOrbit n _ ⟨F, rfl⟩
  · intro hOrbit
    obtain ⟨F, hF⟩ :=
      (pureStabilizerByFrame_iff_byCliffordOrbit n rho).2 hOrbit
    exact ⟨F, hF.symm⟩

/-- Veitch's qubit stabilizer polytope, presented directly as the convex hull
of the semantic Clifford orbit. -/
def StabilizerPolytopeByCliffordOrbit (n : ℕ) :
    Set (CMatrix (2 ^ n) (2 ^ n)) :=
  convexHull ℝ
    {rho : CMatrix (2 ^ n) (2 ^ n) |
      PureStabilizerByCliffordOrbit n rho}

/-- The common-eigenspace/frame and Clifford-orbit presentations generate
the same stabilizer polytope. -/
theorem stabilizerPolytopeByFrames_eq_byCliffordOrbit (n : ℕ) :
    StabilizerPolytopeByFrames n = StabilizerPolytopeByCliffordOrbit n := by
  unfold StabilizerPolytopeByFrames StabilizerPolytopeByCliffordOrbit
  rw [range_frameAtom_eq_cliffordOrbitAtoms]

/-- A state is a nonnegative classical mixture of frame atoms exactly when it
lies in the convex hull of pure Clifford-orbit atoms. -/
theorem stabilizerFreeByFrames_iff_mem_cliffordOrbitPolytope
    (n : ℕ) (rho : CMatrix (2 ^ n) (2 ^ n)) :
    StabilizerFreeByFrames n rho ↔
      rho ∈ StabilizerPolytopeByCliffordOrbit n := by
  rw [stabilizerFreeByFrames_iff_mem_polytope]
  rw [stabilizerPolytopeByFrames_eq_byCliffordOrbit]

end

end AgtXIv.Stabilizer
