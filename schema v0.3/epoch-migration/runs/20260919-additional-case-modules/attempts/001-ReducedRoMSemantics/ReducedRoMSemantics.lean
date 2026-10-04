import AgtXIvVarela.MeasurementProjection

/-!
The normalized reduced primal from arXiv:2607.26154v1,
Stabilizerness/arXiv-2607.26154v1/draft.tex:122–130.

Appending the constant coordinate preserves the source's sum x = 1 constraint.
The finite atom family consists of projections of complete stabilizer frames;
equality with optimization over the reduced polytope's vertices remains a
separate convex-generator-invariance obligation. This file proves no closed
form, perfect-graph theorem, sign collapse, or final-query result.

This isolated module uses the cached original Lean 4.30.0-rc2 epoch. It does not
claim composition with the separate Physlib epoch.
-/

namespace AgtXIv.ReducedRoM

open scoped BigOperators
open AgtXIv.RoM AgtXIv.Stabilizer AgtXIv.Varela

noncomputable section

variable {ι E : Type*} [Fintype ι] [AddCommGroup E] [Module ℝ E]

/-- The added coordinate records affine normalization, independently of the
measured expectations. -/
def augmentedAtom (atom : ι → E) (i : ι) : ℝ × E := (1, atom i)

theorem reconstruct_augmentedAtom (atom : ι → E) (x : ι → ℝ) :
    reconstruct (augmentedAtom atom) x = (∑ i, x i, reconstruct atom x) := by
  apply Prod.ext <;> simp [reconstruct, augmentedAtom, Prod.fst_sum, Prod.snd_sum]

/-- Exact equivalence with both constraints in the paper's reduced primal. -/
theorem signedDecomp_augmentedAtom_iff (atom : ι → E) (b : E) (x : ι → ℝ) :
    SignedDecomp (augmentedAtom atom) (1, b) x ↔
      (∑ i, x i = 1) ∧ SignedDecomp atom b x := by
  unfold SignedDecomp
  rw [reconstruct_augmentedAtom]
  simp only [Prod.mk.injEq]

variable {n m : ℕ}

/-- Every density input has an augmented projected-frame decomposition. The
normalization and reconstruction are obtained from actual full stabilizer
decomposition, rather than assumed for the reduced optimization. -/
theorem augmented_projected_feasible
    (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n)) :
    ∃ x : IndependentSignedPauliFrame n n → ℝ,
      SignedDecomp (augmentedAtom W.projectedFrameAtom)
        (1, W.expectationProjection ρ.toTraceOneHermitian.1) x := by
  obtain ⟨x, hNorm, hx⟩ :=
    traceOne_exists_normalized_stabilizer_signedDecomp ρ.toTraceOneHermitian
  refine ⟨x, (signedDecomp_augmentedAtom_iff _ _ _).2 ⟨hNorm, ?_⟩⟩
  change reconstruct W.projectedFrameAtom x =
    W.expectationProjection ρ.toTraceOneHermitian.1
  rw [← W.expectationProjection_reconstruct]
  exact congrArg W.expectationProjection hx

/-- The attained normalized reduced optimization over actual projected frame
atoms. The definition contains no desired clique formula. -/
def reducedRoM (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n)) : ℝ :=
  finiteRoM (augmentedAtom W.projectedFrameAtom)
    (1, W.expectationProjection ρ.toTraceOneHermitian.1)
    (augmented_projected_feasible W ρ)

/-- This optimization has an actual minimum satisfying both source constraints. -/
theorem reducedRoM_attained
    (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n)) :
    ∃ x : IndependentSignedPauliFrame n n → ℝ,
      (∑ F, x F = 1) ∧
      SignedDecomp W.projectedFrameAtom (W.expectationProjection ρ.toTraceOneHermitian.1) x ∧
      reducedRoM W ρ = l1Cost x ∧
      ∀ y : IndependentSignedPauliFrame n n → ℝ,
        (∑ F, y F = 1) →
        SignedDecomp W.projectedFrameAtom (W.expectationProjection ρ.toTraceOneHermitian.1) y →
        l1Cost x ≤ l1Cost y := by
  let x := optimalCoeffs (augmentedAtom W.projectedFrameAtom)
    (1, W.expectationProjection ρ.toTraceOneHermitian.1)
    (augmented_projected_feasible W ρ)
  have hx : IsL1Minimizer (augmentedAtom W.projectedFrameAtom)
      (1, W.expectationProjection ρ.toTraceOneHermitian.1) x :=
    optimalCoeffs_isL1Minimizer _ _ _
  obtain ⟨hNorm, hDecomp⟩ := (signedDecomp_augmentedAtom_iff _ _ _).1 hx.1
  refine ⟨x, hNorm, hDecomp, rfl, ?_⟩
  intro y hyNorm hyDecomp
  exact hx.2 y ((signedDecomp_augmentedAtom_iff _ _ _).2 ⟨hyNorm, hyDecomp⟩)

/-- The constant-coordinate constraint enforces the paper's universal floor. -/
theorem one_le_reducedRoM
    (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n)) :
    1 ≤ reducedRoM W ρ := by
  obtain ⟨x, hNorm, _, hValue, _⟩ := reducedRoM_attained W ρ
  rw [hValue]
  exact (normalized_l1 x hNorm).1

end

end AgtXIv.ReducedRoM
