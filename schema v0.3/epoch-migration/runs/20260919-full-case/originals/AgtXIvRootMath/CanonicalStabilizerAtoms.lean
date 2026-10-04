import AgtXIvRootMath.StabilizerRoMInstantiation

/-!
# Distinct pure stabilizer atoms

Complete signed Pauli frames are a convenient finite index, but several
frames may define the same rank-one projector.  Howard and Campbell minimize
over pure stabilizer states themselves.  This module forms the finite range
type of distinct projectors and proves that removing duplicate frame indices
does not change either the free convex hull or the attained `l1` optimum.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix.Norms.L2Operator
noncomputable section

set_option maxHeartbeats 1200000

/-- The finite type of distinct frame-presented pure stabilizer projectors. -/
def PureStabilizerAtom (n : ℕ) :=
  {A : HermitianMatrixReal (2 ^ n) //
    A ∈ Set.range (completeFrameHermitianAtom n)}

/-- Send a complete frame to the distinct projector that it presents. -/
def frameToPureStabilizerAtom (n : ℕ)
    (F : IndependentSignedPauliFrame n n) : PureStabilizerAtom n :=
  ⟨completeFrameHermitianAtom n F, ⟨F, rfl⟩⟩

theorem frameToPureStabilizerAtom_surjective (n : ℕ) :
    Function.Surjective (frameToPureStabilizerAtom n) := by
  rintro ⟨A, F, rfl⟩
  exact ⟨F, rfl⟩

noncomputable instance pureStabilizerAtomFinite (n : ℕ) :
    Finite (PureStabilizerAtom n) :=
  Finite.of_surjective (frameToPureStabilizerAtom n)
    (frameToPureStabilizerAtom_surjective n)

noncomputable instance pureStabilizerAtomFintype (n : ℕ) :
    Fintype (PureStabilizerAtom n) := Fintype.ofFinite _

/-- The canonical atom family has no duplicate matrix values. -/
def canonicalStabilizerHermitianAtom (n : ℕ) :
    PureStabilizerAtom n → HermitianMatrixReal (2 ^ n) :=
  fun A => A.1

theorem canonicalStabilizerHermitianAtom_injective (n : ℕ) :
    Function.Injective (canonicalStabilizerHermitianAtom n) :=
  Subtype.val_injective

@[simp]
theorem canonicalStabilizerHermitianAtom_frameTo (n : ℕ)
    (F : IndependentSignedPauliFrame n n) :
    canonicalStabilizerHermitianAtom n (frameToPureStabilizerAtom n F) =
      completeFrameHermitianAtom n F := rfl

/-- Every canonical atom has a chosen complete-frame representative. -/
noncomputable def PureStabilizerAtom.representativeFrame {n : ℕ}
    (A : PureStabilizerAtom n) : IndependentSignedPauliFrame n n :=
  Classical.choose A.2

@[simp]
theorem PureStabilizerAtom.representativeFrame_atom {n : ℕ}
    (A : PureStabilizerAtom n) :
    completeFrameHermitianAtom n A.representativeFrame =
      canonicalStabilizerHermitianAtom n A :=
  Classical.choose_spec A.2

namespace CanonicalAtomAux

variable {V : Type*} [NormedAddCommGroup V] [NormedSpace ℝ V]

/-- Every member of a finite atom family is trivially a free point. -/
theorem atom_mem_freeByAtoms {iota : Type*} [Fintype iota]
    (atom : iota → V) (i : iota) :
    AgtXIv.RoM.FreeByAtoms atom (atom i) := by
  classical
  refine ⟨fun j => if j = i then 1 else 0, ?_, ?_, ?_⟩
  · intro j
    positivity
  · simp
  · unfold AgtXIv.RoM.SignedDecomp AgtXIv.RoM.reconstruct
    rw [Finset.sum_eq_single i]
    · simp
    · intro j _hj hji
      simp [hji]
    · intro hi
      simp at hi

/-- Atom-wise convex preservation maps the entire input convex hull into the
output convex hull.  The row-stochastic kernel is constructed, not assumed. -/
theorem freeByAtoms_map_of_atomImages
    {iota kappa : Type*} [Fintype iota] [Fintype kappa]
    {W : Type*} [NormedAddCommGroup W] [NormedSpace ℝ W]
    (atomIn : iota → V) (atomOut : kappa → W)
    (E : V →ₗ[ℝ] W)
    (hAtomImage : ∀ i, AgtXIv.RoM.FreeByAtoms atomOut (E (atomIn i)))
    {rho : V} (hFree : AgtXIv.RoM.FreeByAtoms atomIn rho) :
    AgtXIv.RoM.FreeByAtoms atomOut (E rho) := by
  obtain ⟨p, hp, hsum, hrec⟩ := hFree
  let K := AgtXIv.RoM.kernelOfAtomImages atomIn atomOut E hAtomImage
  refine ⟨K.push p, ?_, K.sum_push p |>.trans hsum, ?_⟩
  · intro j
    unfold AgtXIv.RoM.FiniteStochasticKernel.push
    exact Finset.sum_nonneg fun i _ => mul_nonneg (hp i) (K.nonneg i j)
  · unfold AgtXIv.RoM.SignedDecomp
    rw [AgtXIv.RoM.reconstruct_push_kernelOfAtomImages
      atomIn atomOut E hAtomImage p,
      hrec]

end CanonicalAtomAux

/-- Each frame-indexed atom is an ordinary point of the canonical atom set. -/
theorem frameAtom_freeByCanonical (n : ℕ)
    (F : IndependentSignedPauliFrame n n) :
    AgtXIv.RoM.FreeByAtoms (canonicalStabilizerHermitianAtom n)
      (completeFrameHermitianAtom n F) := by
  simpa using CanonicalAtomAux.atom_mem_freeByAtoms
    (canonicalStabilizerHermitianAtom n) (frameToPureStabilizerAtom n F)

/-- Each canonical atom has a complete-frame representative. -/
theorem canonicalAtom_freeByFrames (n : ℕ)
    (A : PureStabilizerAtom n) :
    AgtXIv.RoM.FreeByAtoms (completeFrameHermitianAtom n)
      (canonicalStabilizerHermitianAtom n A) := by
  rw [← A.representativeFrame_atom]
  exact CanonicalAtomAux.atom_mem_freeByAtoms
    (completeFrameHermitianAtom n) A.representativeFrame

/-- Removing duplicate frame labels leaves the convex hull unchanged. -/
theorem freeByCanonical_iff_freeByFrames (n : ℕ)
    (A : HermitianMatrixReal (2 ^ n)) :
    AgtXIv.RoM.FreeByAtoms (canonicalStabilizerHermitianAtom n) A ↔
      AgtXIv.RoM.FreeByAtoms (completeFrameHermitianAtom n) A := by
  constructor
  · intro h
    simpa using CanonicalAtomAux.freeByAtoms_map_of_atomImages
      (canonicalStabilizerHermitianAtom n) (completeFrameHermitianAtom n)
      (LinearMap.id) (canonicalAtom_freeByFrames n) h
  · intro h
    simpa using CanonicalAtomAux.freeByAtoms_map_of_atomImages
      (completeFrameHermitianAtom n) (canonicalStabilizerHermitianAtom n)
      (LinearMap.id) (frameAtom_freeByCanonical n) h

/-- The range of the distinct atom family is exactly the range of the
possibly redundant complete-frame family. -/
theorem range_canonicalStabilizerHermitianAtom (n : ℕ) :
    Set.range (canonicalStabilizerHermitianAtom n) =
      Set.range (completeFrameHermitianAtom n) := by
  ext A
  constructor
  · rintro ⟨B, rfl⟩
    exact B.2
  · rintro ⟨F, rfl⟩
    exact ⟨frameToPureStabilizerAtom n F, rfl⟩

/-- Feasibility over complete frames and over distinct projectors are
equivalent. -/
theorem canonical_feasible_iff_frame_feasible (n : ℕ)
    (A : HermitianMatrixReal (2 ^ n)) :
    (∃ x, AgtXIv.RoM.SignedDecomp
      (canonicalStabilizerHermitianAtom n) A x) ↔
    (∃ x, AgtXIv.RoM.SignedDecomp
      (completeFrameHermitianAtom n) A x) := by
  constructor
  · intro h
    exact AgtXIv.RoM.output_feasible_of_atomImages
      (canonicalStabilizerHermitianAtom n) (completeFrameHermitianAtom n)
      LinearMap.id A (canonicalAtom_freeByFrames n) h
  · intro h
    exact AgtXIv.RoM.output_feasible_of_atomImages
      (completeFrameHermitianAtom n) (canonicalStabilizerHermitianAtom n)
      LinearMap.id A (frameAtom_freeByCanonical n) h

/-- Duplicating or removing frame labels does not change the attained
robustness value. -/
theorem finiteRoM_canonical_eq_frames (n : ℕ)
    (A : HermitianMatrixReal (2 ^ n))
    (hCanonical : ∃ x, AgtXIv.RoM.SignedDecomp
      (canonicalStabilizerHermitianAtom n) A x)
    (hFrames : ∃ x, AgtXIv.RoM.SignedDecomp
      (completeFrameHermitianAtom n) A x) :
    AgtXIv.RoM.finiteRoM (canonicalStabilizerHermitianAtom n) A hCanonical =
      AgtXIv.RoM.finiteRoM (completeFrameHermitianAtom n) A hFrames := by
  apply le_antisymm
  · have h := AgtXIv.RoM.finiteRoM_mono_of_atomImages
      (completeFrameHermitianAtom n) (canonicalStabilizerHermitianAtom n)
      LinearMap.id A (frameAtom_freeByCanonical n) hFrames
    simpa using h
  · have h := AgtXIv.RoM.finiteRoM_mono_of_atomImages
      (canonicalStabilizerHermitianAtom n) (completeFrameHermitianAtom n)
      LinearMap.id A (canonicalAtom_freeByFrames n) hCanonical
    simpa using h

/-- Affine completeness of the frame family gives feasibility over the
source-aligned type of distinct pure stabilizer projectors. -/
theorem traceOne_canonicalStabilizer_feasible_of_complete
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    ∃ x, AgtXIv.RoM.SignedDecomp
      (canonicalStabilizerHermitianAtom n) A.1 x := by
  apply (canonical_feasible_iff_frame_feasible n A.1).2
  exact traceOne_stabilizer_feasible_of_complete hcomplete A

/-- Source-aligned full robustness: the minimum is indexed by distinct pure
stabilizer projectors rather than by a redundant list of frames. -/
noncomputable def fullStabilizerRoMCanonicalOfComplete
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) : ℝ :=
  AgtXIv.RoM.finiteRoM (canonicalStabilizerHermitianAtom n) A.1
    (traceOne_canonicalStabilizer_feasible_of_complete hcomplete A)

/-- The distinct-projector definition and the redundant-frame implementation
have exactly the same value. -/
theorem fullStabilizerRoMCanonicalOfComplete_eq_frames
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    fullStabilizerRoMCanonicalOfComplete hcomplete A =
      fullStabilizerRoMOfComplete hcomplete A := by
  exact finiteRoM_canonical_eq_frames n A.1
    (traceOne_canonicalStabilizer_feasible_of_complete hcomplete A)
    (traceOne_stabilizer_feasible_of_complete hcomplete A)

/-- Source-aligned exact faithfulness. -/
theorem fullStabilizerRoMCanonicalOfComplete_eq_one_iff_free
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    fullStabilizerRoMCanonicalOfComplete hcomplete A = 1 ↔
      StabilizerFreeByFrames n (A.1 : CMatrix (2 ^ n) (2 ^ n)) := by
  rw [fullStabilizerRoMCanonicalOfComplete_eq_frames]
  exact fullStabilizerRoMOfComplete_eq_one_iff_free hcomplete A

/-- Source-aligned strict witness form. -/
theorem one_lt_fullStabilizerRoMCanonicalOfComplete_iff_not_free
    {n : ℕ}
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom n)))
    (A : TraceOneHermitianMatrix (2 ^ n)) :
    1 < fullStabilizerRoMCanonicalOfComplete hcomplete A ↔
      ¬ StabilizerFreeByFrames n (A.1 : CMatrix (2 ^ n) (2 ^ n)) := by
  rw [fullStabilizerRoMCanonicalOfComplete_eq_frames]
  exact one_lt_fullStabilizerRoMOfComplete_iff_not_free hcomplete A

/-- Deterministic monotonicity for the source-aligned distinct-projector
definition. -/
theorem StabilizerAtomMap.fullStabilizerRoMCanonicalOfComplete_mono
    {nIn nOut : ℕ} (E : StabilizerAtomMap nOut nIn)
    (hcompleteIn : traceOneHermitianAffine (2 ^ nIn) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom nIn)))
    (hcompleteOut : traceOneHermitianAffine (2 ^ nOut) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom nOut)))
    (A : TraceOneHermitianMatrix (2 ^ nIn)) :
    fullStabilizerRoMCanonicalOfComplete hcompleteOut
        (E.mapTraceOneOfComplete hcompleteIn A) ≤
      fullStabilizerRoMCanonicalOfComplete hcompleteIn A := by
  rw [fullStabilizerRoMCanonicalOfComplete_eq_frames,
    fullStabilizerRoMCanonicalOfComplete_eq_frames]
  exact E.fullStabilizerRoMOfComplete_mono
    hcompleteIn hcompleteOut A

end

end AgtXIv.Stabilizer
