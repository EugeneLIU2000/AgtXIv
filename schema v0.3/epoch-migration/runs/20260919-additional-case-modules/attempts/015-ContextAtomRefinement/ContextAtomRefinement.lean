import ProjectedFrameCoordinates
import AgtXIvVarela.ContextReconstruction

/-!
Constructive refinement of each projected complete stabilizer-frame atom
into two maximal-context candidates on the no-active-dependency branch.
The candidates keep the original nonzero coordinates and have opposite signs
on added coordinates. Their coefficients are exactly 1/2 each (combined if
the two labels coincide). This proves both repaired V-representation fields
and the resulting convex-hull equality, rather than assuming either field.

Source: arXiv:2607.26154v1 draft.tex:134--155, 223--231, 498--509.
No claim is made that every projected atom itself has maximal support.
-/

open scoped BigOperators

namespace AgtXIv.RoM

/-- Explicit nonnegative midpoint coefficients; coincident labels accumulate
their weights and still have total mass one. -/
theorem midpoint_freeByAtoms {ι V : Type*} [Fintype ι]
    [AddCommGroup V] [Module ℝ V] (atom : ι → V) (a b : ι) :
    FreeByAtoms atom ((2 : ℝ)⁻¹ • atom a + (2 : ℝ)⁻¹ • atom b) := by
  classical
  refine ⟨fun i => (if i = a then (2 : ℝ)⁻¹ else 0) +
    (if i = b then (2 : ℝ)⁻¹ else 0), ?_, ?_, ?_⟩
  · intro i
    positivity
  · norm_num [Finset.sum_add_distrib]
  · simp [SignedDecomp, reconstruct, add_smul, Finset.sum_add_distrib, ite_smul]

end AgtXIv.RoM

namespace AgtXIv.Varela.MeasurementWindow

open AgtXIv.Stabilizer

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

/-- Finite cardinal maximization constructs an inclusion-maximal commuting
context containing the given commuting subset. -/
theorem exists_maximal_context_containing (T : Finset (Fin m))
    (hT : W.IsCommutingContext T) :
    ∃ S : Finset (Fin m), T ⊆ S ∧ W.IsMaximalCommutingContext S := by
  classical
  let candidates : Finset (Finset (Fin m)) :=
    Finset.univ.filter (fun S => T ⊆ S ∧ W.IsCommutingContext S)
  have hnonempty : candidates.Nonempty := ⟨T, by simp [candidates, hT]⟩
  obtain ⟨S, hS, hMax⟩ := candidates.exists_max_image Finset.card hnonempty
  have hSprops : T ⊆ S ∧ W.IsCommutingContext S := (Finset.mem_filter.mp hS).2
  refine ⟨S, hSprops.1, hSprops.2, ?_⟩
  intro U hU hSU
  have hUc : U ∈ candidates := by
    simp [candidates, hSprops.1.trans hSU, hU]
  exact (Finset.eq_of_subset_of_card_le hSU (hMax U hUc)).symm

/-- Retain all nonzero signs of b; choose one common sign on its zero
coordinates inside S; use the required false encoding outside S. -/
def completionSign (S : Finset (Fin m)) (b : Fin m → ℝ) (t : Bool) : Fin m → Bool := by
  classical
  exact fun i => if i ∈ S then if b i = 0 then t else decide (b i = -1) else false

def completionCandidate (hNoActive : W.NoActiveDependencies)
    (S : Finset (Fin m)) (hMax : W.IsMaximalCommutingContext S)
    (b : Fin m → ℝ) (t : Bool) : W.MaximalSignedContext where
  support := S
  sign := completionSign S b t
  offSupportFalse i hi := by simp [completionSign, hi]
  maximal := hMax
  admissible := W.isAdmissibleSign_of_noActiveDependencies hNoActive S hMax.1 _

theorem midpoint_completionCandidates (hNoActive : W.NoActiveDependencies)
    (S : Finset (Fin m)) (hMax : W.IsMaximalCommutingContext S) (b : Fin m → ℝ)
    (hTernary : ∀ i, b i = 0 ∨ b i = 1 ∨ b i = -1)
    (hOutside : ∀ i, i ∉ S → b i = 0) :
    (2 : ℝ)⁻¹ • MaximalSignedContext.vector W (W.completionCandidate hNoActive S hMax b false) +
      (2 : ℝ)⁻¹ • MaximalSignedContext.vector W (W.completionCandidate hNoActive S hMax b true) = b := by
  classical
  funext i
  by_cases hi : i ∈ S
  · rcases hTernary i with h0 | hPos | hNeg
    · norm_num [Pi.add_apply, Pi.smul_apply, smul_eq_mul, MaximalSignedContext.vector,
        completionCandidate, completionSign, hi, h0]
    · norm_num [Pi.add_apply, Pi.smul_apply, smul_eq_mul, MaximalSignedContext.vector,
        completionCandidate, completionSign, hi, hPos]
    · norm_num [Pi.add_apply, Pi.smul_apply, smul_eq_mul, MaximalSignedContext.vector,
        completionCandidate, completionSign, hi, hNeg]
  · simp [Pi.add_apply, Pi.smul_apply, MaximalSignedContext.vector,
      completionCandidate, hi, hOutside i hi]

/-- Actual atom refinement. A pure frame's nonzero measured support need not
be maximal; the extra context coordinates cancel in a proved midpoint. -/
theorem atomRefinement_of_noActiveDependencies
    (hNoActive : W.NoActiveDependencies) (F : IndependentSignedPauliFrame n n) :
    AgtXIv.RoM.FreeByAtoms (MaximalSignedContext.vector W) (W.projectedFrameAtom F) := by
  obtain ⟨S, hTS, hMax⟩ := W.exists_maximal_context_containing
    (W.frameNonzeroSupport F) (W.frameNonzeroSupport_commuting F)
  have hOutside : ∀ i, i ∉ S → W.projectedFrameAtom F i = 0 := by
    intro i hi
    by_contra hne
    exact hi (hTS ((W.mem_frameNonzeroSupport F i).mpr hne))
  have hMid := W.midpoint_completionCandidates hNoActive S hMax (W.projectedFrameAtom F)
    (W.projectedFrameAtom_ternary F) hOutside
  rw [← hMid]
  exact AgtXIv.RoM.midpoint_freeByAtoms (MaximalSignedContext.vector W)
    (W.completionCandidate hNoActive S hMax (W.projectedFrameAtom F) false)
    (W.completionCandidate hNoActive S hMax (W.projectedFrameAtom F) true)

/-- Both repaired V-representation fields are now proved on the actual
no-active-dependency branch; neither field is supplied by the caller. -/
def vRepRepair_of_noActiveDependencies
    (hNoActive : W.NoActiveDependencies) : VRepRepairObligations W where
  candidatePhysical := W.candidatePhysical_of_noActiveDependencies hNoActive
  atomRefinement := W.atomRefinement_of_noActiveDependencies hNoActive

theorem projected_eq_contextPolytope_of_noActiveDependencies
    (hNoActive : W.NoActiveDependencies) :
    W.ProjectedStabilizerPolytope = VRepRepairObligations.contextPolytope W := by
  exact VRepRepairObligations.projected_eq_contextPolytope W
    (W.vRepRepair_of_noActiveDependencies hNoActive)

end

end AgtXIv.Varela.MeasurementWindow
