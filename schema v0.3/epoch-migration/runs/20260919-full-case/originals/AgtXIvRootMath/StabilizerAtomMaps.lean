import AgtXIvRootMath.HermitianAffineFeasibility
import AgtXIvRootMath.VeitchStabilizerPolytope
import Mathlib.Analysis.CStarAlgebra.Matrix

/-!
# Exact atom-preserving maps on the stabilizer polytope

Howard and Campbell's deterministic monotonicity proof factors through the
following mathematical interface: every pure input stabilizer atom is sent to an ordinary
convex mixture of pure output stabilizer atoms.  This file records that
interface explicitly and derives, rather than assumes, the stochastic
coefficient kernel used in the proof.

This is an exact ideal-theory interface.  It is not definitionally identified
with the full Veitch stabilizer-protocol syntax (ancillas, measurements,
discarding, and feed-forward); proving that each such protocol induces this
interface remains a separate source-semantics theorem.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix.Norms.L2Operator
noncomputable section

set_option maxHeartbeats 1200000

/-- The complete finite family of frame-presented pure stabilizer projectors,
viewed in the real vector space of Hermitian matrices. -/
def completeFrameHermitianAtom (n : ℕ) :
    IndependentSignedPauliFrame n n → HermitianMatrixReal (2 ^ n) :=
  pureStabilizerHermitianAtom id

@[simp]
theorem completeFrameHermitianAtom_apply (n : ℕ)
    (F : IndependentSignedPauliFrame n n) :
    completeFrameHermitianAtom n F = (pureStabilizerTraceOneHermitian F).1 := rfl

@[simp]
theorem hermitianTraceReal_completeFrameHermitianAtom (n : ℕ)
    (F : IndependentSignedPauliFrame n n) :
    hermitianTraceReal (2 ^ n) (completeFrameHermitianAtom n F) = 1 := by
  exact hermitianTraceReal_pureStabilizerHermitianAtom id F

/-- Exact atom-preservation contract.  The map is real-linear
on Hermitian matrices, and each pure stabilizer atom has a witnessed convex
decomposition over output atoms.  No stochastic kernel is stored as data. -/
structure StabilizerAtomMap (nOut nIn : ℕ) where
  toLinearMap :
    HermitianMatrixReal (2 ^ nIn) →ₗ[ℝ] HermitianMatrixReal (2 ^ nOut)
  atom_image : ∀ F : IndependentSignedPauliFrame nIn nIn,
    AgtXIv.RoM.FreeByAtoms (completeFrameHermitianAtom nOut)
      (toLinearMap (completeFrameHermitianAtom nIn F))

namespace StabilizerAtomMap

variable {nIn nMid nOut : ℕ}

instance : CoeFun (StabilizerAtomMap nOut nIn) (fun _ =>
    HermitianMatrixReal (2 ^ nIn) → HermitianMatrixReal (2 ^ nOut)) :=
  ⟨fun E => E.toLinearMap⟩

/-- The identity is atom preserving. -/
def id (n : ℕ) : StabilizerAtomMap n n where
  toLinearMap := LinearMap.id
  atom_image := by
    classical
    intro F
    refine ⟨fun G => if G = F then 1 else 0, ?_, ?_, ?_⟩
    · intro G
      positivity
    · simp
    · unfold AgtXIv.RoM.SignedDecomp AgtXIv.RoM.reconstruct
      rw [Finset.sum_eq_single F]
      · simp
      · intro G _hG hGF
        simp [hGF]
      · intro hF
        simp at hF

/-- An atom-preserving map sends every free convex mixture to another free
convex mixture.  The coefficient kernel is constructed from `atom_image`. -/
theorem maps_free_to_free (E : StabilizerAtomMap nOut nIn)
    (rho : HermitianMatrixReal (2 ^ nIn))
    (hFree : AgtXIv.RoM.FreeByAtoms (completeFrameHermitianAtom nIn) rho) :
    AgtXIv.RoM.FreeByAtoms (completeFrameHermitianAtom nOut) (E rho) := by
  classical
  obtain ⟨p, hp, hsum, hrec⟩ := hFree
  let K := AgtXIv.RoM.kernelOfAtomImages
    (completeFrameHermitianAtom nIn) (completeFrameHermitianAtom nOut)
    E.toLinearMap E.atom_image
  refine ⟨K.push p, ?_, ?_, ?_⟩
  · intro j
    unfold AgtXIv.RoM.FiniteStochasticKernel.push
    exact Finset.sum_nonneg fun i _ => mul_nonneg (hp i) (K.nonneg i j)
  · exact (K.sum_push p).trans hsum
  · unfold AgtXIv.RoM.SignedDecomp
    change AgtXIv.RoM.reconstruct (completeFrameHermitianAtom nOut)
      ((AgtXIv.RoM.kernelOfAtomImages
        (completeFrameHermitianAtom nIn) (completeFrameHermitianAtom nOut)
        E.toLinearMap E.atom_image).push p) = E rho
    rw [AgtXIv.RoM.reconstruct_push_kernelOfAtomImages
      (completeFrameHermitianAtom nIn) (completeFrameHermitianAtom nOut)
      E.toLinearMap E.atom_image p, hrec]

/-- Exact atom-preserving maps compose. -/
def comp (E : StabilizerAtomMap nOut nMid)
    (D : StabilizerAtomMap nMid nIn) : StabilizerAtomMap nOut nIn where
  toLinearMap := E.toLinearMap.comp D.toLinearMap
  atom_image := by
    intro F
    exact E.maps_free_to_free _ (D.atom_image F)

/-- Atom preservation forces trace-one outputs on every trace-one input once
the input atoms have been proved affine-complete.  Thus trace preservation on
the state affine slice is derived from, not added to, the atom contract. -/
theorem trace_one_of_affine_complete (E : StabilizerAtomMap nOut nIn)
    (hcomplete : traceOneHermitianAffine (2 ^ nIn) ≤
      affineSpan ℝ (Set.range (completeFrameHermitianAtom nIn)))
    (rho : HermitianMatrixReal (2 ^ nIn))
    (hrho : rho ∈ traceOneHermitianSet (2 ^ nIn)) :
    Matrix.trace (E rho : CMatrix (2 ^ nOut) (2 ^ nOut)) = 1 := by
  classical
  obtain ⟨x, hxSum, hx⟩ :=
    AgtXIv.RoM.exists_normalized_signedDecomp_of_mem_affineSpan
      (completeFrameHermitianAtom nIn) rho (hcomplete hrho)
  let K := AgtXIv.RoM.kernelOfAtomImages
    (completeFrameHermitianAtom nIn) (completeFrameHermitianAtom nOut)
    E.toLinearMap E.atom_image
  have hOutput : AgtXIv.RoM.SignedDecomp (completeFrameHermitianAtom nOut)
      (E rho) (K.push x) := by
    unfold AgtXIv.RoM.SignedDecomp
    rw [AgtXIv.RoM.reconstruct_push_kernelOfAtomImages
      (completeFrameHermitianAtom nIn) (completeFrameHermitianAtom nOut)
      E.toLinearMap E.atom_image x, hx]
  have hCoeffSum : ∑ j, K.push x j = 1 := (K.sum_push x).trans hxSum
  have hTraceReal : hermitianTraceReal (2 ^ nOut) (E rho) = 1 := by
    calc
      hermitianTraceReal (2 ^ nOut) (E rho) =
          hermitianTraceReal (2 ^ nOut)
            (AgtXIv.RoM.reconstruct (completeFrameHermitianAtom nOut) (K.push x)) := by
              rw [hOutput]
      _ = ∑ j, K.push x j := by
            unfold AgtXIv.RoM.reconstruct
            rw [map_sum]
            simp only [map_smul]
            apply Finset.sum_congr rfl
            intro j _
            rw [hermitianTraceReal_completeFrameHermitianAtom]
            simp
      _ = 1 := hCoeffSum
  change (Matrix.trace (E rho : CMatrix (2 ^ nOut) (2 ^ nOut))).re = 1 at hTraceReal
  have hTraceSelfAdjoint :
      star (Matrix.trace (E rho : CMatrix (2 ^ nOut) (2 ^ nOut))) =
        Matrix.trace (E rho : CMatrix (2 ^ nOut) (2 ^ nOut)) := by
    rw [← Matrix.trace_conjTranspose]
    exact congrArg Matrix.trace (E rho).property
  have hRealTrace :
      ((Matrix.trace (E rho : CMatrix (2 ^ nOut) (2 ^ nOut))).re : ℂ) =
        Matrix.trace (E rho : CMatrix (2 ^ nOut) (2 ^ nOut)) :=
    Complex.conj_eq_iff_re.mp hTraceSelfAdjoint
  rw [← hRealTrace, hTraceReal]
  norm_num

/-- Exact full-RoM monotonicity for the atom-preserving linear interface after actual atom feasibility is
supplied for the input target.  The output feasibility and the stochastic
kernel are both derived. -/
theorem finiteRoM_mono (E : StabilizerAtomMap nOut nIn)
    (rho : HermitianMatrixReal (2 ^ nIn))
    (hFeasible : ∃ x, AgtXIv.RoM.SignedDecomp
      (completeFrameHermitianAtom nIn) rho x) :
    AgtXIv.RoM.finiteRoM (completeFrameHermitianAtom nOut) (E rho)
        (AgtXIv.RoM.output_feasible_of_atomImages
          (completeFrameHermitianAtom nIn) (completeFrameHermitianAtom nOut)
          E.toLinearMap rho E.atom_image hFeasible) ≤
      AgtXIv.RoM.finiteRoM (completeFrameHermitianAtom nIn) rho hFeasible := by
  classical
  exact AgtXIv.RoM.finiteRoM_mono_of_atomImages
    (completeFrameHermitianAtom nIn) (completeFrameHermitianAtom nOut)
    E.toLinearMap rho E.atom_image hFeasible

end StabilizerAtomMap

end
end AgtXIv.Stabilizer
