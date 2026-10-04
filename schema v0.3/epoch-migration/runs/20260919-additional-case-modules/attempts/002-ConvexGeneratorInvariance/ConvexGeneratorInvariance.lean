import ReducedRoMSemantics

/-!
Constructive convex-generator invariance for the normalized finite-l1 primal.
Target source: arXiv:2607.26154v1 draft.tex:122–130, where coefficients sum to 1
and the sum ranges over vertices of the projected stabilizer polytope.

Each input atom is given as a probability mixture of output atoms. The existing
kernel construction transports any particular signed input decomposition to a
particular output decomposition with no larger cost. Bidirectional mixtures
therefore imply equality of the two minima. No inequality between independently
chosen arbitrary representations is asserted. In particular this is not the
overstated all-representations claim of Varela's Proposition 1norminequality.

The actual maps between projected frame atoms and a chosen vertex enumeration
remain explicit hypotheses in the application theorem. No final closed form,
LP duality, sign collapse, or perfect-graph theorem is assumed or proved.
-/

namespace AgtXIv.ReducedRoM

open scoped BigOperators
open AgtXIv.RoM AgtXIv.Stabilizer AgtXIv.Varela

noncomputable section

variable {ι κ E : Type*} [Fintype ι] [Fintype κ]
variable [NormedAddCommGroup E] [NormedSpace ℝ E]

/-- Explicit coefficient transport through probability rows witnessing that
every input atom belongs to the output convex hull. -/
def convexPush (atomIn : ι → E) (atomOut : κ → E)
    (hAtoms : ∀ i, FreeByAtoms atomOut (atomIn i)) (x : ι → ℝ) : κ → ℝ :=
  (kernelOfAtomImages atomIn atomOut LinearMap.id hAtoms).push x

/-- The transported decomposition preserves normalization and reconstruction,
with cost no greater than that of the given input decomposition. -/
theorem normalized_decomposition_transport
    (atomIn : ι → E) (atomOut : κ → E)
    (hAtoms : ∀ i, FreeByAtoms atomOut (atomIn i))
    (b : E) (x : ι → ℝ) (hNorm : ∑ i, x i = 1)
    (hDecomp : SignedDecomp atomIn b x) :
    (∑ j, convexPush atomIn atomOut hAtoms x j = 1) ∧
      SignedDecomp atomOut b (convexPush atomIn atomOut hAtoms x) ∧
      l1Cost (convexPush atomIn atomOut hAtoms x) ≤ l1Cost x := by
  let K := kernelOfAtomImages atomIn atomOut LinearMap.id hAtoms
  refine ⟨?_, ?_, K.l1_push_le x⟩
  · change ∑ j, K.push x j = 1
    rw [K.sum_push x, hNorm]
  · change reconstruct atomOut (K.push x) = b
    rw [reconstruct_push_kernelOfAtomImages]
    exact hDecomp

/-- A probability-row map transfers augmented feasibility; it does not assume
that either optimum has a particular numerical value. -/
theorem augmented_feasible_of_convex_atoms
    (atomIn : ι → E) (atomOut : κ → E)
    (hAtoms : ∀ i, FreeByAtoms atomOut (atomIn i)) (b : E)
    (hFeasible : ∃ x, SignedDecomp (augmentedAtom atomIn) (1, b) x) :
    ∃ y, SignedDecomp (augmentedAtom atomOut) (1, b) y := by
  obtain ⟨x, hx⟩ := hFeasible
  obtain ⟨hNorm, hDecomp⟩ := (signedDecomp_augmentedAtom_iff _ _ _).1 hx
  obtain ⟨hyNorm, hyDecomp, _⟩ :=
    normalized_decomposition_transport atomIn atomOut hAtoms b x hNorm hDecomp
  exact ⟨convexPush atomIn atomOut hAtoms x,
    (signedDecomp_augmentedAtom_iff _ _ _).2 ⟨hyNorm, hyDecomp⟩⟩

/-- One convex-generator inclusion gives the correctly directed minimum
inequality, by transporting a minimizing input decomposition. -/
theorem normalized_minimum_le_of_convex_atoms
    (atomIn : ι → E) (atomOut : κ → E)
    (hAtoms : ∀ i, FreeByAtoms atomOut (atomIn i)) (b : E)
    (hIn : ∃ x, SignedDecomp (augmentedAtom atomIn) (1, b) x)
    (hOut : ∃ y, SignedDecomp (augmentedAtom atomOut) (1, b) y) :
    finiteRoM (augmentedAtom atomOut) (1, b) hOut ≤
      finiteRoM (augmentedAtom atomIn) (1, b) hIn := by
  let x := optimalCoeffs (augmentedAtom atomIn) (1, b) hIn
  have hx : IsL1Minimizer (augmentedAtom atomIn) (1, b) x :=
    optimalCoeffs_isL1Minimizer _ _ _
  obtain ⟨hNorm, hDecomp⟩ := (signedDecomp_augmentedAtom_iff _ _ _).1 hx.1
  obtain ⟨hyNorm, hyDecomp, hCost⟩ :=
    normalized_decomposition_transport atomIn atomOut hAtoms b x hNorm hDecomp
  have hy := (signedDecomp_augmentedAtom_iff atomOut b
    (convexPush atomIn atomOut hAtoms x)).2 ⟨hyNorm, hyDecomp⟩
  exact ((optimalCoeffs_isL1Minimizer (augmentedAtom atomOut) (1, b) hOut).2 _ hy).trans hCost

/-- Mutual probability decompositions of the atoms imply equality of the
normalized minima, not equality of costs of arbitrary representations. -/
theorem normalized_minimum_eq_of_mutual_convex_atoms
    (atomA : ι → E) (atomB : κ → E)
    (hAB : ∀ i, FreeByAtoms atomB (atomA i))
    (hBA : ∀ j, FreeByAtoms atomA (atomB j)) (b : E)
    (hA : ∃ x, SignedDecomp (augmentedAtom atomA) (1, b) x)
    (hB : ∃ y, SignedDecomp (augmentedAtom atomB) (1, b) y) :
    finiteRoM (augmentedAtom atomA) (1, b) hA =
      finiteRoM (augmentedAtom atomB) (1, b) hB := by
  exact le_antisymm
    (normalized_minimum_le_of_convex_atoms atomB atomA hBA b hB hA)
    (normalized_minimum_le_of_convex_atoms atomA atomB hAB b hA hB)

/-- Projected-frame semantics can be replaced by any finite family with the
same bidirectional convex atom maps. Proving that a supplied family is exactly
the source's vertex family, and furnishing these maps, remain separate tasks. -/
theorem reducedRoM_eq_of_mutual_convex_generators
    {n m : ℕ} (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n))
    (atom : κ → (Fin m → ℝ))
    (hFrame : ∀ F, FreeByAtoms atom (W.projectedFrameAtom F))
    (hAtom : ∀ j, FreeByAtoms W.projectedFrameAtom (atom j)) :
    reducedRoM W ρ =
      finiteRoM (augmentedAtom atom)
        (1, W.expectationProjection ρ.toTraceOneHermitian.1)
        (augmented_feasible_of_convex_atoms W.projectedFrameAtom atom hFrame
          (W.expectationProjection ρ.toTraceOneHermitian.1) (augmented_projected_feasible W ρ)) := by
  exact normalized_minimum_eq_of_mutual_convex_atoms W.projectedFrameAtom atom
    hFrame hAtom (W.expectationProjection ρ.toTraceOneHermitian.1)
    (augmented_projected_feasible W ρ) _

end

end AgtXIv.ReducedRoM
