import AgtXIvRootMath.StabilizerAffineComplete
import AgtXIvRootMath.DensityStabilizerRoM

/-!
# Unconditional all-qubit full stabilizer robustness

This module discharges the affine-completeness argument that earlier modules
kept visible.  The resulting optimization is over the finite type of distinct
frame-presented pure stabilizer projectors.  Feasibility, attainment,
faithfulness, and the stochastic coefficient kernel used for deterministic
monotonicity are all derived upstream rather than supplied as assumptions.

The map theorem below is scoped to `StabilizerAtomMap`: a real-linear map with
an exact convex decomposition of every input stabilizer atom.  Identifying a
particular physical protocol or channel with that interface remains a separate
exact-semantics obligation; this theorem does not silently assert it for every
operation informally called a stabilizer operation.
-/

namespace AgtXIv.Stabilizer

noncomputable section

/-- Every trace-one Hermitian target has a normalized signed decomposition
over complete frame-presented pure stabilizer projectors. -/
theorem traceOne_exists_normalized_stabilizer_signedDecomp
    {n : ℕ} (A : TraceOneHermitianMatrix (2 ^ n)) :
    ∃ x : IndependentSignedPauliFrame n n → ℝ,
      (∑ F, x F = 1) ∧
      AgtXIv.RoM.SignedDecomp (completeFrameHermitianAtom n) A.1 x := by
  exact traceOne_exists_normalized_stabilizer_signedDecomp_of_complete
    (traceOneHermitianAffine_le_completeFrame_affineSpan n) A

/-- The same unconditional feasibility over the canonical finite type of
distinct pure stabilizer projectors. -/
theorem traceOne_canonicalStabilizer_feasible
    {n : ℕ} (A : TraceOneHermitianMatrix (2 ^ n)) :
    ∃ x, AgtXIv.RoM.SignedDecomp
      (canonicalStabilizerHermitianAtom n) A.1 x := by
  exact traceOne_canonicalStabilizer_feasible_of_complete
    (traceOneHermitianAffine_le_completeFrame_affineSpan n) A

/-- Howard--Campbell full robustness on the distinct pure stabilizer
projectors, now total and unconditional for every `n`-qubit trace-one
Hermitian target. -/
noncomputable def fullStabilizerRoM {n : ℕ}
    (A : TraceOneHermitianMatrix (2 ^ n)) : ℝ :=
  fullStabilizerRoMCanonicalOfComplete
    (traceOneHermitianAffine_le_completeFrame_affineSpan n) A

/-- The canonical distinct-projector definition agrees with the redundant
complete-frame implementation. -/
theorem fullStabilizerRoM_eq_frames {n : ℕ}
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    fullStabilizerRoM A =
      fullStabilizerRoMOfComplete
        (traceOneHermitianAffine_le_completeFrame_affineSpan n) A := by
  exact fullStabilizerRoMCanonicalOfComplete_eq_frames
    (traceOneHermitianAffine_le_completeFrame_affineSpan n) A

/-- Exact faithfulness: full robustness is one exactly on the convex hull of
the actual frame-presented pure stabilizer projectors. -/
theorem fullStabilizerRoM_eq_one_iff_free {n : ℕ}
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    fullStabilizerRoM A = 1 ↔
      StabilizerFreeByFrames n (A.1 : CMatrix (2 ^ n) (2 ^ n)) := by
  exact fullStabilizerRoMCanonicalOfComplete_eq_one_iff_free
    (traceOneHermitianAffine_le_completeFrame_affineSpan n) A

/-- Strict full robustness is equivalent to lying outside the stabilizer
convex hull. -/
theorem one_lt_fullStabilizerRoM_iff_not_free {n : ℕ}
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    1 < fullStabilizerRoM A ↔
      ¬ StabilizerFreeByFrames n (A.1 : CMatrix (2 ^ n) (2 ^ n)) := by
  exact one_lt_fullStabilizerRoMCanonicalOfComplete_iff_not_free
    (traceOneHermitianAffine_le_completeFrame_affineSpan n) A

/-- An exact atom-preserving map sends trace-one Hermitian inputs to
trace-one Hermitian outputs.  This property is derived from all-qubit affine
completeness, not added to the map interface. -/
noncomputable def StabilizerAtomMap.mapTraceOne
    {nIn nOut : ℕ} (E : StabilizerAtomMap nOut nIn)
    (A : TraceOneHermitianMatrix (2 ^ nIn)) :
    TraceOneHermitianMatrix (2 ^ nOut) :=
  E.mapTraceOneOfComplete
    (traceOneHermitianAffine_le_completeFrame_affineSpan nIn) A

/-- Unconditional deterministic monotonicity for the exact atom-preserving
linear-map interface.  The stochastic kernel is constructed from the atom
image witnesses and is not a premise. -/
theorem StabilizerAtomMap.fullStabilizerRoM_mono
    {nIn nOut : ℕ} (E : StabilizerAtomMap nOut nIn)
    (A : TraceOneHermitianMatrix (2 ^ nIn)) :
    fullStabilizerRoM (E.mapTraceOne A) ≤ fullStabilizerRoM A := by
  exact E.fullStabilizerRoMCanonicalOfComplete_mono
    (traceOneHermitianAffine_le_completeFrame_affineSpan nIn)
    (traceOneHermitianAffine_le_completeFrame_affineSpan nOut) A

/-- Density-matrix specialization of unconditional full robustness. -/
noncomputable def densityFullStabilizerRoM {n : ℕ}
    (rho : DensityMatrix (2 ^ n)) : ℝ :=
  fullStabilizerRoM rho.toTraceOneHermitian

/-- Density-matrix faithfulness against the stabilizer convex hull. -/
theorem densityFullStabilizerRoM_eq_one_iff_free {n : ℕ}
    (rho : DensityMatrix (2 ^ n)) :
    densityFullStabilizerRoM rho = 1 ↔
      StabilizerFreeByFrames n rho.val := by
  exact fullStabilizerRoM_eq_one_iff_free rho.toTraceOneHermitian

/-- A density matrix has strict full robustness exactly when it is magic in
the free-set sense used here. -/
theorem one_lt_densityFullStabilizerRoM_iff_magic {n : ℕ}
    (rho : DensityMatrix (2 ^ n)) :
    1 < densityFullStabilizerRoM rho ↔ IsMagicDensityByFrames rho := by
  exact one_lt_fullStabilizerRoM_iff_not_free rho.toTraceOneHermitian

/-- Unconditional deterministic density-level monotonicity for maps that
implement the exact `DensityStabilizerAtomMap` contract. -/
theorem DensityStabilizerAtomMap.densityFullStabilizerRoM_mono
    {nIn nOut : ℕ} (E : DensityStabilizerAtomMap nOut nIn)
    (rho : DensityMatrix (2 ^ nIn)) :
    densityFullStabilizerRoM (E.mapDensity rho) ≤
      densityFullStabilizerRoM rho := by
  exact E.densityFullStabilizerRoMOfComplete_mono
    (traceOneHermitianAffine_le_completeFrame_affineSpan nIn)
    (traceOneHermitianAffine_le_completeFrame_affineSpan nOut) rho

end

end AgtXIv.Stabilizer
