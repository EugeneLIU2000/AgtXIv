import AgtXIvRootMath.StabilizerAtomMaps

/-!
# Full robustness on the stabilizer atom family

This module connects the abstract finite-atom robustness development to the
actual rank-one stabilizer projectors.  It keeps affine completeness visible
as a theorem argument for now; the all-qubit Pauli-basis module will discharge
that argument once and for all.  In particular, no minimizer and no stochastic
kernel is assumed here.

The two convex-hull predicates below live in different ambient types only for
technical reasons: one uses the real vector space of Hermitian matrices and
the other uses concrete complex matrices.  Their coefficients and physical
projectors are identical.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix.Norms.L2Operator
noncomputable section

set_option maxHeartbeats 1200000

/-- Convex-hull membership in the Hermitian carrier is exactly the matrix-level
frame-presented stabilizer free-set predicate. -/
theorem freeByCompleteFrameHermitian_iff_stabilizerFreeByFrames
    (n : ℕ) (A : HermitianMatrixReal (2 ^ n)) :
    AgtXIv.RoM.FreeByAtoms (completeFrameHermitianAtom n) A ↔
      StabilizerFreeByFrames n (A : CMatrix (2 ^ n) (2 ^ n)) := by
  constructor
  · rintro ⟨p, hp, hsum, hrec⟩
    refine ⟨p, hp, hsum, ?_⟩
    unfold AgtXIv.RoM.SignedDecomp AgtXIv.RoM.reconstruct at hrec ⊢
    have h := congrArg
      (fun B : HermitianMatrixReal (2 ^ n) =>
        (B : CMatrix (2 ^ n) (2 ^ n))) hrec
    simpa [completeFrameHermitianAtom, pureStabilizerHermitianAtom,
      frameAtom] using h
  · rintro ⟨p, hp, hsum, hrec⟩
    refine ⟨p, hp, hsum, ?_⟩
    unfold AgtXIv.RoM.SignedDecomp AgtXIv.RoM.reconstruct at hrec ⊢
    apply Subtype.ext
    simpa [completeFrameHermitianAtom, pureStabilizerHermitianAtom,
      frameAtom] using hrec

/-- Density-matrix specialization of the exact free-set identification. -/
theorem density_freeByCompleteFrameHermitian_iff_stabilizerFreeByFrames
    {n : ℕ} (ρ : DensityMatrix (2 ^ n)) :
    AgtXIv.RoM.FreeByAtoms (completeFrameHermitianAtom n)
        ρ.toTraceOneHermitian.1 ↔
      StabilizerFreeByFrames n ρ.val := by
  simpa using
    freeByCompleteFrameHermitian_iff_stabilizerFreeByFrames n
      ρ.toTraceOneHermitian.1

/-- Affine completeness gives a normalized signed stabilizer decomposition of
every point of the Hermitian trace-one slice, not merely of positive density
matrices. -/
theorem traceOne_exists_normalized_stabilizer_signedDecomp_of_complete
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    ∃ x : IndependentSignedPauliFrame n n → ℝ,
      (∑ F, x F = 1) ∧
      AgtXIv.RoM.SignedDecomp (completeFrameHermitianAtom n) A.1 x := by
  exact AgtXIv.RoM.exists_normalized_signedDecomp_of_mem_affineSpan
    (completeFrameHermitianAtom n) A.1 (hcomplete A.2)

/-- Feasibility in precisely the shape consumed by `finiteRoM`. -/
theorem traceOne_stabilizer_feasible_of_complete
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    ∃ x : IndependentSignedPauliFrame n n → ℝ,
      AgtXIv.RoM.SignedDecomp (completeFrameHermitianAtom n) A.1 x := by
  obtain ⟨x, _hxSum, hx⟩ :=
    traceOne_exists_normalized_stabilizer_signedDecomp_of_complete hcomplete A
  exact ⟨x, hx⟩

/-- The attained full stabilizer robustness, parameterized only by a proof of
the substantive all-atom affine-completeness theorem.  A later wrapper removes
this parameter by applying the proved all-qubit completeness result. -/
noncomputable def fullStabilizerRoMOfComplete
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) : ℝ := by
  let hFeasible : ∃ x : IndependentSignedPauliFrame n n → ℝ,
      AgtXIv.RoM.SignedDecomp (completeFrameHermitianAtom n) A.1 x :=
    traceOne_stabilizer_feasible_of_complete hcomplete A
  exact @AgtXIv.RoM.finiteRoM
    (IndependentSignedPauliFrame n n) (HermitianMatrixReal (2 ^ n))
    (frameFintype n n) inferInstance inferInstance
    (completeFrameHermitianAtom n) A.1 hFeasible

/-- The trace functional is normalized on every point of the trace-one
Hermitian affine slice. -/
@[simp]
theorem hermitianTraceReal_traceOne {d : ℕ}
    (A : TraceOneHermitianMatrix d) :
    hermitianTraceReal d A.1 = 1 := by
  change (Matrix.trace (A.1 : CMatrix d d)).re = 1
  rw [A.2]
  norm_num

/-- Exact Howard--Campbell faithfulness after affine completeness is supplied:
robustness one is equivalent to ordinary convex membership in the actual
stabilizer projector family. -/
theorem fullStabilizerRoMOfComplete_eq_one_iff_free
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    fullStabilizerRoMOfComplete hcomplete A = 1 ↔
      StabilizerFreeByFrames n (A.1 : CMatrix (2 ^ n) (2 ^ n)) := by
  unfold fullStabilizerRoMOfComplete
  rw [AgtXIv.RoM.finiteRoM_eq_one_iff_free
    (completeFrameHermitianAtom n) A.1
    (traceOne_stabilizer_feasible_of_complete hcomplete A)
    (hermitianTraceReal (2 ^ n))
    (hermitianTraceReal_completeFrameHermitianAtom n)
    (hermitianTraceReal_traceOne A)]
  exact freeByCompleteFrameHermitian_iff_stabilizerFreeByFrames n A.1

/-- Strict witness form of faithfulness. -/
theorem one_lt_fullStabilizerRoMOfComplete_iff_not_free
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    1 < fullStabilizerRoMOfComplete hcomplete A ↔
      ¬ StabilizerFreeByFrames n (A.1 : CMatrix (2 ^ n) (2 ^ n)) := by
  unfold fullStabilizerRoMOfComplete
  rw [AgtXIv.RoM.one_lt_finiteRoM_iff_not_free
    (completeFrameHermitianAtom n) A.1
    (traceOne_stabilizer_feasible_of_complete hcomplete A)
    (hermitianTraceReal (2 ^ n))
    (hermitianTraceReal_completeFrameHermitianAtom n)
    (hermitianTraceReal_traceOne A)]
  exact not_congr
    (freeByCompleteFrameHermitian_iff_stabilizerFreeByFrames n A.1)

/-- An atom-preserving map sends the trace-one affine slice into the trace-one
affine slice once input atoms are affine-complete. -/
noncomputable def StabilizerAtomMap.mapTraceOneOfComplete
    {nIn nOut : ℕ} (E : StabilizerAtomMap nOut nIn)
    (hcompleteIn : traceOneHermitianAffine (2 ^ nIn) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom nIn)))
    (A : TraceOneHermitianMatrix (2 ^ nIn)) :
    TraceOneHermitianMatrix (2 ^ nOut) :=
  ⟨E A.1, E.trace_one_of_affine_complete hcompleteIn A.1 A.2⟩

/-- Deterministic full-RoM monotonicity.  Neither the stochastic kernel nor
input/output feasibility is assumed: the former comes from atom images and
the latter from affine completeness. -/
theorem StabilizerAtomMap.fullStabilizerRoMOfComplete_mono
    {nIn nOut : ℕ} (E : StabilizerAtomMap nOut nIn)
    (hcompleteIn : traceOneHermitianAffine (2 ^ nIn) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom nIn)))
    (hcompleteOut : traceOneHermitianAffine (2 ^ nOut) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom nOut)))
    (A : TraceOneHermitianMatrix (2 ^ nIn)) :
    fullStabilizerRoMOfComplete hcompleteOut
        (E.mapTraceOneOfComplete hcompleteIn A) ≤
      fullStabilizerRoMOfComplete hcompleteIn A := by
  let hIn := traceOne_stabilizer_feasible_of_complete hcompleteIn A
  have hMono := E.finiteRoM_mono A.1 hIn
  unfold fullStabilizerRoMOfComplete
  change AgtXIv.RoM.finiteRoM (completeFrameHermitianAtom nOut) (E A.1)
      (traceOne_stabilizer_feasible_of_complete hcompleteOut
        (E.mapTraceOneOfComplete hcompleteIn A)) ≤
    AgtXIv.RoM.finiteRoM (completeFrameHermitianAtom nIn) A.1
      (traceOne_stabilizer_feasible_of_complete hcompleteIn A)
  simpa only [hIn] using hMono

end

end AgtXIv.Stabilizer
