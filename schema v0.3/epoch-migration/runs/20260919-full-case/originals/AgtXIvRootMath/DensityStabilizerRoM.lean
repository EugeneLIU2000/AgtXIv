import AgtXIvRootMath.CanonicalStabilizerAtoms

/-!
# Density-matrix form of full stabilizer robustness

Howard and Campbell state robustness for density operators.  The optimization
itself takes place in the surrounding Hermitian trace-one affine space; this
module supplies the exact density wrapper and a minimal deterministic channel
interface whose linear action preserves stabilizer atoms and whose state action
really returns density matrices.

Complete positivity and a concrete protocol syntax are not smuggled into the
proof: showing that a chosen physical stabilizer protocol implements this exact
interface is a separate source-semantics obligation.
-/

namespace AgtXIv.Stabilizer

open scoped Matrix.Norms.L2Operator
noncomputable section

set_option maxHeartbeats 1200000

/-- Full robustness of a density matrix, still parameterized by the single
all-qubit affine-completeness theorem that the Pauli-basis development will
discharge globally. -/
noncomputable def densityFullStabilizerRoMOfComplete
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (rho : DensityMatrix (2 ^ n)) : ℝ :=
  fullStabilizerRoMCanonicalOfComplete hcomplete rho.toTraceOneHermitian

/-- Density-matrix faithfulness against the actual stabilizer-state convex
hull. -/
theorem densityFullStabilizerRoMOfComplete_eq_one_iff_free
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (rho : DensityMatrix (2 ^ n)) :
    densityFullStabilizerRoMOfComplete hcomplete rho = 1 ↔
      StabilizerFreeByFrames n rho.val := by
  exact fullStabilizerRoMCanonicalOfComplete_eq_one_iff_free
    hcomplete rho.toTraceOneHermitian

/-- Magic membership is the complement of the ordinary stabilizer convex hull,
not the complement of the set of pure stabilizer vertices. -/
def IsMagicDensityByFrames {n : ℕ} (rho : DensityMatrix (2 ^ n)) : Prop :=
  ¬ StabilizerFreeByFrames n rho.val

/-- Strict robustness is exactly magic membership. -/
theorem one_lt_densityFullStabilizerRoMOfComplete_iff_magic
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (rho : DensityMatrix (2 ^ n)) :
    1 < densityFullStabilizerRoMOfComplete hcomplete rho ↔
      IsMagicDensityByFrames rho := by
  exact one_lt_fullStabilizerRoMCanonicalOfComplete_iff_not_free
    hcomplete rho.toTraceOneHermitian

/-- Minimal exact deterministic state-map interface used by the full-RoM
proof.  The Hermitian action is real-linear and atom preserving; the state
action certifies that exact density inputs have exact density outputs and is
required to agree with that linear action. -/
structure DensityStabilizerAtomMap (nOut nIn : ℕ) where
  atomMap : StabilizerAtomMap nOut nIn
  mapDensity : DensityMatrix (2 ^ nIn) → DensityMatrix (2 ^ nOut)
  mapDensity_eq : ∀ rho,
    atomMap rho.toTraceOneHermitian.1 =
      (mapDensity rho).toTraceOneHermitian.1

namespace DensityStabilizerAtomMap

variable {nIn nOut : ℕ}

/-- Deterministic density-matrix monotonicity.  Feasibility, optimum
attainment, and the stochastic kernel are all derived in upstream modules. -/
theorem densityFullStabilizerRoMOfComplete_mono
    (E : DensityStabilizerAtomMap nOut nIn)
    (hcompleteIn : traceOneHermitianAffine (2 ^ nIn) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom nIn)))
    (hcompleteOut : traceOneHermitianAffine (2 ^ nOut) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom nOut)))
    (rho : DensityMatrix (2 ^ nIn)) :
    densityFullStabilizerRoMOfComplete hcompleteOut (E.mapDensity rho) ≤
      densityFullStabilizerRoMOfComplete hcompleteIn rho := by
  have hMono := E.atomMap.fullStabilizerRoMCanonicalOfComplete_mono
    hcompleteIn hcompleteOut rho.toTraceOneHermitian
  unfold densityFullStabilizerRoMOfComplete
  have hPoint : E.atomMap.mapTraceOneOfComplete hcompleteIn
      rho.toTraceOneHermitian = (E.mapDensity rho).toTraceOneHermitian := by
    apply Subtype.ext
    exact E.mapDensity_eq rho
  rwa [hPoint] at hMono

end DensityStabilizerAtomMap

end

end AgtXIv.Stabilizer
