import AgtXIvVarela.MaximalContext

/-!
# Abstract repaired V-representation step

The source proof incorrectly identified every pure-stabilizer projection with
a maximal measured context.  The repaired route needs two different facts:

1. every maximal-context candidate is physically in the projected stabilizer
   polytope;
2. every projected pure stabilizer atom is a classical mixture of maximal-
   context candidates.

This file proves that these obligations are sufficient.  They remain visible
premises and therefore cannot be mistaken for already formalized Pauli facts.
-/

namespace AgtXIv.Varela

noncomputable section

open AgtXIv.Stabilizer

variable {n m : ℕ}

/-- The two load-bearing obligations of the repaired Varela proof. -/
structure VRepRepairObligations (W : MeasurementWindow n m) where
  candidatePhysical : ∀ c : W.MaximalSignedContext,
    AgtXIv.RoM.FreeByAtoms W.projectedFrameAtom
      (MeasurementWindow.MaximalSignedContext.vector W c)
  atomRefinement : ∀ F : IndependentSignedPauliFrame n n,
    AgtXIv.RoM.FreeByAtoms
      (fun c : W.MaximalSignedContext =>
        MeasurementWindow.MaximalSignedContext.vector W c)
      (W.projectedFrameAtom F)

namespace VRepRepairObligations

/-- The context-generated candidate polytope. -/
def contextPolytope (W : MeasurementWindow n m) : Set (Fin m → ℝ) :=
  {b | AgtXIv.RoM.FreeByAtoms
    (fun c : W.MaximalSignedContext =>
      MeasurementWindow.MaximalSignedContext.vector W c) b}

/-- Conditional repaired V-representation.  No graph theorem or Pauli
extension lemma is hidden: the exact physicality and refinement statements are
the fields of `VRepRepairObligations`. -/
theorem projected_eq_contextPolytope
    (W : MeasurementWindow n m) (H : VRepRepairObligations W) :
    W.ProjectedStabilizerPolytope = contextPolytope W := by
  ext b
  constructor
  · intro hb
    exact AgtXIv.Stabilizer.CanonicalAtomAux.freeByAtoms_map_of_atomImages
      W.projectedFrameAtom
      (fun c : W.MaximalSignedContext =>
        MeasurementWindow.MaximalSignedContext.vector W c)
      LinearMap.id H.atomRefinement hb
  · intro hb
    exact AgtXIv.Stabilizer.CanonicalAtomAux.freeByAtoms_map_of_atomImages
      (fun c : W.MaximalSignedContext =>
        MeasurementWindow.MaximalSignedContext.vector W c)
      W.projectedFrameAtom
      LinearMap.id H.candidatePhysical hb

end VRepRepairObligations

end

end AgtXIv.Varela
