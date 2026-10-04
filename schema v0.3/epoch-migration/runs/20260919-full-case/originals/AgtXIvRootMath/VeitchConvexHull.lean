import AgtXIvRootMath.FiniteAtomConvexHull
import AgtXIvRootMath.VeitchStabilizerPolytope

/-!
# The stabilizer free set as an actual convex hull

The coefficient-level predicate used by the robustness development is here
identified with Mathlib's ordinary convex hull of the exact pure stabilizer
projectors.  This is the mathematical content behind Veitch et al.'s
stabilizer polytope definition; classical convex mixing is not coherent state
superposition.
-/

namespace AgtXIv.Stabilizer

open scoped Matrix.Norms.L2Operator
noncomputable section

/-- Frame presentation of the finite stabilizer polytope. -/
def StabilizerPolytopeByFrames (n : ℕ) :
    Set (CMatrix (2 ^ n) (2 ^ n)) :=
  convexHull ℝ (Set.range (frameAtom n))

/-- The explicit nonnegative normalized mixture and geometric convex-hull
presentations coincide exactly. -/
theorem stabilizerFreeByFrames_iff_mem_polytope
    (n : ℕ) (rho : CMatrix (2 ^ n) (2 ^ n)) :
    StabilizerFreeByFrames n rho ↔ rho ∈ StabilizerPolytopeByFrames n := by
  exact AgtXIv.RoM.freeByAtoms_iff_mem_convexHull_range (frameAtom n) rho

end

end AgtXIv.Stabilizer
