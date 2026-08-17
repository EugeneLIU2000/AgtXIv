import AgtXIvRootMath.GottesmanGeneralRankDimension
import AgtXIvRootMath.GottesmanGeneralRankProjector
import AgtXIvRootMath.GottesmanGeneratorFixedSpace
import AgtXIvRootMath.UnconditionalStabilizerRoM
import AgtXIvRootMath.VeitchOrbitPolytope

/-!
# Kernel-checked surface for the three conceptual root agents

This module exposes the final cross-root mathematical statements.  Gottesman's
complete signed-Pauli common-eigenspace atoms have already been proved equal to
Veitch's semantic Clifford-orbit atoms.  Howard--Campbell's finite signed
decomposition therefore has the source-aligned stabilizer polytope as its
free set.

The operation theorem remains deliberately scoped to the exact
atom-preserving linear/density-map interface.  Connecting a concrete
stabilizer protocol syntax, including selective branches, to that interface
is a separate source-and-physical-semantics obligation rather than an
approximation.
-/

namespace AgtXIv.Stabilizer

noncomputable section

/-- Magic membership using Veitch's Clifford-orbit stabilizer polytope. -/
def IsMagicDensityByCliffordOrbit {n : ℕ}
    (rho : DensityMatrix (2 ^ n)) : Prop :=
  rho.val ∉ StabilizerPolytopeByCliffordOrbit n

/-- Howard--Campbell faithfulness, now stated against Veitch's
Clifford-orbit stabilizer polytope rather than the intermediate frame
presentation. -/
theorem densityFullStabilizerRoM_eq_one_iff_mem_cliffordOrbitPolytope
    {n : ℕ} (rho : DensityMatrix (2 ^ n)) :
    densityFullStabilizerRoM rho = 1 ↔
      rho.val ∈ StabilizerPolytopeByCliffordOrbit n := by
  rw [densityFullStabilizerRoM_eq_one_iff_free]
  exact stabilizerFreeByFrames_iff_mem_cliffordOrbitPolytope n rho.val

/-- Strict full robustness is exactly membership outside Veitch's
Clifford-orbit stabilizer polytope. -/
theorem one_lt_densityFullStabilizerRoM_iff_magicByCliffordOrbit
    {n : ℕ} (rho : DensityMatrix (2 ^ n)) :
    1 < densityFullStabilizerRoM rho ↔
      IsMagicDensityByCliffordOrbit rho := by
  rw [one_lt_densityFullStabilizerRoM_iff_magic]
  unfold IsMagicDensityByFrames IsMagicDensityByCliffordOrbit
  exact not_congr
    (stabilizerFreeByFrames_iff_mem_cliffordOrbitPolytope n rho.val)

end

end AgtXIv.Stabilizer
