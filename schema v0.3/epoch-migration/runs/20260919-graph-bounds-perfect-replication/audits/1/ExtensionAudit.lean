import ReducedRoMSemantics
import ConvexGeneratorInvariance
import FiniteRoMDuality
import ContextSignIndependence
import NoActiveDependencies
import ContextCodeState
import PartialFrameExtension
import SignedGeneratorCompletion
import MaximalContextPhysical
import ProjectedFrameCoordinates
import ContextAtomRefinement
import FiniteCliqueCoverAttainment
import WeightedCliqueCoverWeakDuality
import ReducedRoMGraphDual
import GraphDualBounds
import PerfectGraphColorClass
import PerfectGraphTransport
import PerfectGraphTrueTwin
import PerfectGraphReplication
import ConcretePhyslibBridge
import Lean

/-!
The host prepends an import of the project being audited and appends
`#agtxiv_audit Declaration.name` commands. Evidence is obtained from Lean's
environment, never from declaration-name matching or a historical JSON file.

`value_constants` are syntactic dependencies of the elaborated value. This
does not establish that a hypothesis is mathematically necessary. Importing a
module without using a declaration does not create such a dependency.
-/

open Lean Meta Elab Command

namespace AgtXIv.EnvironmentAudit

private def namesJson (names : Array Name) : Json :=
  toJson (names.map Name.toString)

private def kind (info : ConstantInfo) : String :=
  match info with
  | .thmInfo _ => "THEOREM"
  | .defnInfo _ => "DEFINITION"
  | .axiomInfo _ => "AXIOM"
  | .opaqueInfo _ => "OPAQUE"
  | .inductInfo _ => "INDUCTIVE"
  | .ctorInfo _ => "CONSTRUCTOR"
  | .recInfo _ => "RECURSOR"
  | .quotInfo _ => "QUOTIENT"

private def binderKind (bi : BinderInfo) : String :=
  match bi with
  | .default => "EXPLICIT"
  | .implicit => "IMPLICIT"
  | .strictImplicit => "STRICT_IMPLICIT"
  | .instImplicit => "INSTANCE"

/-- Binder annotations alone are not composition witnesses. -/
private partial def termConstants (e : Expr) (acc : NameSet := {}) : NameSet :=
  match e with
  | .const n _ => acc.insert n
  | .app f a => termConstants a (termConstants f acc)
  | .lam _ _ b _ => termConstants b acc
  | .letE _ _ v b _ => termConstants b (termConstants v acc)
  | .mdata _ b => termConstants b acc
  | .proj _ _ b => termConstants b acc
  | _ => acc

def audit (name : Name) : MetaM Json := do
  let info ← getConstInfo name
  let statement ← ppExpr info.type
  let axioms ← collectAxioms name
  let value := info.value? (allowOpaque := true)
  let dependencies := value.map Expr.getUsedConstants |>.getD #[]
  let termDependencies := value.map (fun e => (termConstants e).toArray) |>.getD #[]
  let (binders, premises, packedPremises, result) ← forallTelescope info.type fun xs body => do
    let mut binders : Array Json := #[]
    let mut premises : Array Json := #[]
    let mut packedPremises : Array Json := #[]
    for x in xs do
      let decl ← x.fvarId!.getDecl
      let proposition ← isProp decl.type
      let ty ← ppExpr decl.type
      let item := Json.mkObj [
        ("name", toJson decl.userName.toString),
        ("type", toJson ty.pretty),
        ("binder_kind", toJson (binderKind decl.binderInfo)),
        ("is_prop", toJson proposition),
        ("type_constants", namesJson decl.type.getUsedConstants)]
      binders := binders.push item
      if proposition && decl.binderInfo != .instImplicit then
        premises := premises.push item
      -- A proof-carrying structure can live in Type. Its proof fields are
      -- still obligations (notably VRepRepairObligations).
      if !proposition && decl.binderInfo != .instImplicit then
        let reduced ← whnf decl.type
        if let .const structName _ := reduced.getAppFn then
          if (getStructureInfo? (← getEnv) structName).isSome then
            for field in getStructureFields (← getEnv) structName do
              let projection ← mkProjection x field
              let fieldType ← inferType projection
              if ← isProp fieldType then
                packedPremises := packedPremises.push (Json.mkObj [
                  ("name", toJson (decl.userName.toString ++ "." ++ field.toString)),
                  ("parent_binder", toJson decl.userName.toString),
                  ("structure", toJson structName.toString),
                  ("type", toJson (← ppExpr fieldType).pretty),
                  ("type_constants", namesJson fieldType.getUsedConstants)])
    let conclusion ← ppExpr body
    pure (binders, premises, packedPremises, conclusion.pretty)
  return Json.mkObj [
    ("declaration", toJson name.toString),
    ("kind", toJson (kind info)),
    ("type", toJson statement.pretty),
    ("conclusion", toJson result),
    ("parameters", toJson binders),
    ("non_instance_prop_hypotheses", toJson premises),
    ("structure_prop_hypotheses", toJson packedPremises),
    ("type_constants", namesJson info.type.getUsedConstants),
    ("value_constants", namesJson dependencies),
    ("term_constants", namesJson termDependencies),
    ("axioms", namesJson axioms),
    ("has_value", toJson value.isSome)]

end AgtXIv.EnvironmentAudit

elab "#agtxiv_audit " name:ident : command => do
  let result ← liftTermElabM do
    withOptions (fun opts => opts.set `pp.width (140 : Nat) |>.setBool `pp.universes true) do
      AgtXIv.EnvironmentAudit.audit name.getId
  liftIO <| IO.println ("AGTXIV_AUDIT_JSON " ++ result.compress)

#agtxiv_audit AgtXIv.ConcretePhyslib.adj_iff_matrix_anticomm
#agtxiv_audit AgtXIv.ConcretePhyslib.concrete_window_nonvacuity
#agtxiv_audit AgtXIv.ConcretePhyslib.densityToMState
#agtxiv_audit AgtXIv.ConcretePhyslib.densityToMState_mat
#agtxiv_audit AgtXIv.ConcretePhyslib.density_roundtrip
#agtxiv_audit AgtXIv.ConcretePhyslib.expectation_preserved
#agtxiv_audit AgtXIv.ConcretePhyslib.frustrationGraph
#agtxiv_audit AgtXIv.ConcretePhyslib.mStateToDensity
#agtxiv_audit AgtXIv.ConcretePhyslib.mStateToDensity_val
#agtxiv_audit AgtXIv.ConcretePhyslib.mState_roundtrip
#agtxiv_audit AgtXIv.ConcretePhyslib.matrix_anticomm_of_adj
#agtxiv_audit AgtXIv.ConcretePhyslib.observable
#agtxiv_audit AgtXIv.ConcretePhyslib.observable_mat
#agtxiv_audit AgtXIv.ConcretePhyslib.observable_sq
#agtxiv_audit AgtXIv.ConcretePhyslib.pauli_ne_neg
#agtxiv_audit AgtXIv.ConcretePhyslib.singleZWindow
#agtxiv_audit AgtXIv.ConcretePhyslib.trace_preserved
#agtxiv_audit AgtXIv.ConcretePhyslib.window_cliqueNumber_bound
#agtxiv_audit AgtXIv.ConcretePhyslib.window_clique_l1_bound
#agtxiv_audit AgtXIv.ConcretePhyslib.window_clique_l2_bound
#agtxiv_audit AgtXIv.GraphDual.abs_signedCliqueVector
#agtxiv_audit AgtXIv.GraphDual.clique_weight_mem_objectiveValues
#agtxiv_audit AgtXIv.GraphDual.independentFinsets_complement
#agtxiv_audit AgtXIv.GraphDual.independent_max_le_iff
#agtxiv_audit AgtXIv.GraphDual.independent_max_nonneg
#agtxiv_audit AgtXIv.GraphDual.independent_max_zero
#agtxiv_audit AgtXIv.GraphDual.independent_weight_le_max
#agtxiv_audit AgtXIv.GraphDual.maxWeightClique
#agtxiv_audit AgtXIv.GraphDual.maxWeightClique_eq_complement_independent
#agtxiv_audit AgtXIv.GraphDual.maxWeightClique_le_iff
#agtxiv_audit AgtXIv.GraphDual.mem_cliqueFinsets_iff
#agtxiv_audit AgtXIv.GraphDual.objectiveValues
#agtxiv_audit AgtXIv.GraphDual.objective_le_complement_cover
#agtxiv_audit AgtXIv.GraphDual.objective_le_fractional_complement_cover
#agtxiv_audit AgtXIv.GraphDual.one_mem_objectiveValues
#agtxiv_audit AgtXIv.GraphDual.pairing_le_clique_max_mul_cover_cost
#agtxiv_audit AgtXIv.GraphDual.pairing_le_complement_cover_cost_mul
#agtxiv_audit AgtXIv.GraphDual.signedCliqueVector
#agtxiv_audit AgtXIv.GraphDual.signedCliqueVector_pairing
#agtxiv_audit AgtXIv.GraphFoundation.IsFractionalCliqueCover
#agtxiv_audit AgtXIv.GraphFoundation.IsNonnegativeFiniteCover
#agtxiv_audit AgtXIv.GraphFoundation.IsPerfect
#agtxiv_audit AgtXIv.GraphFoundation.cliqueFinsets
#agtxiv_audit AgtXIv.GraphFoundation.clique_weight_on_independent_le
#agtxiv_audit AgtXIv.GraphFoundation.exists_minimizing_fractionalCliqueCover
#agtxiv_audit AgtXIv.GraphFoundation.exists_nonnegative_finite_cover_minimizer
#agtxiv_audit AgtXIv.GraphFoundation.fractionalCliqueCoverValue
#agtxiv_audit AgtXIv.GraphFoundation.fractionalCliqueCoverValue_attained
#agtxiv_audit AgtXIv.GraphFoundation.fractionalCliqueCoverValue_nonneg
#agtxiv_audit AgtXIv.GraphFoundation.fractionalCliqueCover_cost_nonneg
#agtxiv_audit AgtXIv.GraphFoundation.fractionalCliqueCover_feasible
#agtxiv_audit AgtXIv.GraphFoundation.indep_clique_inter_card_le_one
#agtxiv_audit AgtXIv.GraphFoundation.independent_weight_le_cover_cost
#agtxiv_audit AgtXIv.GraphFoundation.maxWeightIndependent
#agtxiv_audit AgtXIv.GraphFoundation.maxWeightIndependent_le_cover_cost
#agtxiv_audit AgtXIv.GraphFoundation.maxWeightIndependent_le_fractionalCliqueCoverValue
#agtxiv_audit AgtXIv.GraphFoundation.singleton_mem_cliqueFinsets
#agtxiv_audit AgtXIv.PerfectGraph.bothCopiesIso
#agtxiv_audit AgtXIv.PerfectGraph.chromaticNumber_eq_cliqueNum_of_perfect
#agtxiv_audit AgtXIv.PerfectGraph.chromaticNumber_eq_of_iso
#agtxiv_audit AgtXIv.PerfectGraph.cliqueNum_eq_of_iso
#agtxiv_audit AgtXIv.PerfectGraph.cliqueNum_le_of_embedding
#agtxiv_audit AgtXIv.PerfectGraph.cliqueNum_succ_le_trueTwin_of_mem_maximum
#agtxiv_audit AgtXIv.PerfectGraph.clique_meets_each_color
#agtxiv_audit AgtXIv.PerfectGraph.clique_with_twin
#agtxiv_audit AgtXIv.PerfectGraph.collapseVertex
#agtxiv_audit AgtXIv.PerfectGraph.colorable_cliqueNum_of_perfect
#agtxiv_audit AgtXIv.PerfectGraph.colorable_with_independent_block
#agtxiv_audit AgtXIv.PerfectGraph.coloringWithFreshTwin
#agtxiv_audit AgtXIv.PerfectGraph.coloringWithIndependentBlock
#agtxiv_audit AgtXIv.PerfectGraph.embeddingRangeIso
#agtxiv_audit AgtXIv.PerfectGraph.induced_clique_lift
#agtxiv_audit AgtXIv.PerfectGraph.mem_retainedVertices
#agtxiv_audit AgtXIv.PerfectGraph.none_not_mem_oldSubset_range
#agtxiv_audit AgtXIv.PerfectGraph.oldEmbedding
#agtxiv_audit AgtXIv.PerfectGraph.oldSubsetEmbedding
#agtxiv_audit AgtXIv.PerfectGraph.old_clique_lift
#agtxiv_audit AgtXIv.PerfectGraph.perfect_iff_of_iso
#agtxiv_audit AgtXIv.PerfectGraph.perfect_induce
#agtxiv_audit AgtXIv.PerfectGraph.perfect_of_embedding
#agtxiv_audit AgtXIv.PerfectGraph.perfect_retained_colorable
#agtxiv_audit AgtXIv.PerfectGraph.removed_color_class_independent
#agtxiv_audit AgtXIv.PerfectGraph.removed_with_twin_independent
#agtxiv_audit AgtXIv.PerfectGraph.retainedVertices
#agtxiv_audit AgtXIv.PerfectGraph.retained_cliqueNum_lt
#agtxiv_audit AgtXIv.PerfectGraph.retained_clique_card_lt
#agtxiv_audit AgtXIv.PerfectGraph.singleCopyEmbedding
#agtxiv_audit AgtXIv.PerfectGraph.some_mem_oldSubset_range
#agtxiv_audit AgtXIv.PerfectGraph.trueTwin
#agtxiv_audit AgtXIv.PerfectGraph.trueTwin_adj_none
#agtxiv_audit AgtXIv.PerfectGraph.trueTwin_adj_some
#agtxiv_audit AgtXIv.PerfectGraph.trueTwin_chromatic_eq_cliqueNum
#agtxiv_audit AgtXIv.PerfectGraph.trueTwin_colorable_of_no_maximum_clique
#agtxiv_audit AgtXIv.PerfectGraph.trueTwin_isPerfect
#agtxiv_audit AgtXIv.PhyslibCandidate.expectation_eq_real_trace
#agtxiv_audit AgtXIv.ReducedRoM.augmentedAtom
#agtxiv_audit AgtXIv.ReducedRoM.augmented_context_feasible
#agtxiv_audit AgtXIv.ReducedRoM.augmented_dualCoordinates
#agtxiv_audit AgtXIv.ReducedRoM.augmented_dualCoordinates_apply
#agtxiv_audit AgtXIv.ReducedRoM.augmented_feasible_of_convex_atoms
#agtxiv_audit AgtXIv.ReducedRoM.augmented_projected_feasible
#agtxiv_audit AgtXIv.ReducedRoM.convexPush
#agtxiv_audit AgtXIv.ReducedRoM.exists_graph_dual_optimizer
#agtxiv_audit AgtXIv.ReducedRoM.graphDualValues
#agtxiv_audit AgtXIv.ReducedRoM.graphDualValues_eq_objectiveValues
#agtxiv_audit AgtXIv.ReducedRoM.linearFunctional_eq_augmented_dualCoordinates
#agtxiv_audit AgtXIv.ReducedRoM.maxWeightClique_le_reducedRoM
#agtxiv_audit AgtXIv.ReducedRoM.normalized_decomposition_transport
#agtxiv_audit AgtXIv.ReducedRoM.normalized_finiteRoM_isGreatest_dual
#agtxiv_audit AgtXIv.ReducedRoM.normalized_minimum_eq_of_mutual_convex_atoms
#agtxiv_audit AgtXIv.ReducedRoM.normalized_minimum_le_of_convex_atoms
#agtxiv_audit AgtXIv.ReducedRoM.one_le_reducedRoM
#agtxiv_audit AgtXIv.ReducedRoM.reconstruct_augmentedAtom
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_attained
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_clique_cover_sandwich
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_eq_context_minimum
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_eq_graph_dual_sup
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_eq_of_mutual_convex_generators
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_isGreatest_context_dual
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_isGreatest_dual
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_isGreatest_graph_dual
#agtxiv_audit AgtXIv.ReducedRoM.reducedRoM_le_fractional_complement_cover
#agtxiv_audit AgtXIv.ReducedRoM.signedDecomp_augmentedAtom_iff
#agtxiv_audit AgtXIv.RoM.FiniteStochasticKernel.l1_push_le
#agtxiv_audit AgtXIv.RoM.FiniteStochasticKernel.sum_push
#agtxiv_audit AgtXIv.RoM.dual_le_l1Cost
#agtxiv_audit AgtXIv.RoM.exists_finiteRoM_dual_optimizer
#agtxiv_audit AgtXIv.RoM.finiteRoM
#agtxiv_audit AgtXIv.RoM.finiteRoM_isGreatest_dual
#agtxiv_audit AgtXIv.RoM.kernelOfAtomImages
#agtxiv_audit AgtXIv.RoM.midpoint_freeByAtoms
#agtxiv_audit AgtXIv.RoM.norm_toLp_eq_l1Cost
#agtxiv_audit AgtXIv.RoM.normalized_l1
#agtxiv_audit AgtXIv.RoM.optimalCoeffs_isL1Minimizer
#agtxiv_audit AgtXIv.RoM.quotient_eq_iff_reconstructL1
#agtxiv_audit AgtXIv.RoM.quotient_norm_eq_finiteRoM
#agtxiv_audit AgtXIv.RoM.reconstructL1
#agtxiv_audit AgtXIv.RoM.reconstructL1_single
#agtxiv_audit AgtXIv.RoM.reconstructL1_toLp
#agtxiv_audit AgtXIv.RoM.reconstruct_push_kernelOfAtomImages
#agtxiv_audit AgtXIv.Stabilizer.CanonicalAtomAux.atom_mem_freeByAtoms
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.closure_generators_le_wordProduct_range
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.exists_complete_frame
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.exists_complete_generators
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.exists_new_generator
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.frameOfSupportIndependent
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.generator_range_subset_prepend
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.minus_one_not_mem_closure_of_support_independent
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.prepend
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.prepend_support_independent
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.rank_le_of_support_independent
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.support_isotropic
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.support_wordProduct
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.wordProductHom
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.wordProduct_basisWord
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.wordProduct_injective_of_support_independent
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.wordProduct_ne_minus_one_of_support_independent
#agtxiv_audit AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators.wordProduct_one
#agtxiv_audit AgtXIv.Stabilizer.DensityMatrix
#agtxiv_audit AgtXIv.Stabilizer.DensityMatrix.toTraceOneHermitian
#agtxiv_audit AgtXIv.Stabilizer.F2Bits.f2_eq_zero_or_one
#agtxiv_audit AgtXIv.Stabilizer.F2Support.coordinateEquiv
#agtxiv_audit AgtXIv.Stabilizer.F2Support.exists_orthogonal_outside_span
#agtxiv_audit AgtXIv.Stabilizer.F2Support.finrank_eq_twice
#agtxiv_audit AgtXIv.Stabilizer.F2Support.hermitianRepresentative
#agtxiv_audit AgtXIv.Stabilizer.F2Support.hermitianRepresentative_sq
#agtxiv_audit AgtXIv.Stabilizer.F2Support.isotropic_independent_card_le
#agtxiv_audit AgtXIv.Stabilizer.F2Support.pauli_addPhase
#agtxiv_audit AgtXIv.Stabilizer.F2Support.pauli_mul
#agtxiv_audit AgtXIv.Stabilizer.F2Support.span_le_orthogonal_of_isotropic
#agtxiv_audit AgtXIv.Stabilizer.F2Support.support_hermitianRepresentative
#agtxiv_audit AgtXIv.Stabilizer.F2Support.symplecticForm_nondegenerate
#agtxiv_audit AgtXIv.Stabilizer.F2Support.symplectic_alternating
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.basisGenerators
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.basisGenerators_support_independent
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.codeState
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.codeStateMatrix
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.codeStateMatrix_eq_scaled_projector
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.codeStateMatrix_eq_stabilizerProjectorMatrix
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.codeStateMatrix_posSemidef
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.codeStateMatrix_trace_one
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.codeState_eq_completeFrameAtom_of_rank_eq
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.eval_mul_codeStateMatrix
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.exists_complete_signed_extension
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.generatorSupport_linearIndependent
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.trace_eval_eq_zero_of_label_ne_one
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.trace_mul_codeStateMatrix_zero_of_not_commutes
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.trace_mul_codeStateMatrix_zero_of_support_outside
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.trace_mul_eval_zero_of_not_commutes
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.trace_mul_eval_zero_of_support_ne
#agtxiv_audit AgtXIv.Stabilizer.IsScalarPauli
#agtxiv_audit AgtXIv.Stabilizer.completeFrameHermitianAtom
#agtxiv_audit AgtXIv.Stabilizer.exists_minimal_nonempty_zero_sum
#agtxiv_audit AgtXIv.Stabilizer.exists_nonempty_zero_sum_of_not_linearIndependent
#agtxiv_audit AgtXIv.Stabilizer.hermitianSupportPauli_sq
#agtxiv_audit AgtXIv.Stabilizer.pauli_eq_or_eq_neg_of_same_support_of_sq_one
#agtxiv_audit AgtXIv.Stabilizer.pauli_toCMatrix_injective
#agtxiv_audit AgtXIv.Stabilizer.pauli_toCMatrix_isHermitian_of_sq_eq_one
#agtxiv_audit AgtXIv.Stabilizer.scalarPauli_toCMatrix
#agtxiv_audit AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_posSemidef
#agtxiv_audit AgtXIv.Stabilizer.support_eq_zero_iff_scalar
#agtxiv_audit AgtXIv.Stabilizer.support_list_product
#agtxiv_audit AgtXIv.Stabilizer.traceOne_exists_normalized_stabilizer_signedDecomp
#agtxiv_audit AgtXIv.Stabilizer.trace_eval_eq_zero_of_support_ne_zero
#agtxiv_audit AgtXIv.Stabilizerness.max_abs_admissible_signed_sum_of_sign_set_eq
#agtxiv_audit AgtXIv.Stabilizerness.max_abs_signed_sum
#agtxiv_audit AgtXIv.Varela.MeasurementWindow
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.IsActiveDependency
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.IsAdmissibleSign
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.IsBinaryDependency
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.IsCommutingContext
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.IsPauliDependency
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.MaximalSignedContext.vector
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.NoActiveDependencies
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.atomRefinement_of_noActiveDependencies
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.candidatePhysical_of_full_rank_context
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.candidatePhysical_of_noActiveDependencies
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.codeState_projection_eq_maximalContext
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.commute_signedObservable_of_context
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.completionCandidate
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.completionSign
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.contextCodeState_expectation
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.contextEnumeration
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.contextFrustrationGraph
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.context_dual_constraint_iff_graph
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.context_dual_constraint_iff_maximal_weights
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.context_support_independent_of_noActiveDependencies
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.context_vector_dot
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.exists_binaryDependency_subset_of_not_independent
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.exists_completeFrame_realizing_maximalContext
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.exists_density_projecting_to_maximalContext
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.exists_frame_support_of_coordinate_ne_zero
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.exists_maximal_context_containing
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.exists_not_commutes_of_not_mem_maximal
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.exists_projectedFrameAtom_eq_maximalContext
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.expectationCoordinate
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.expectationProjection
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.expectationProjection_reconstruct
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.frameNonzeroSupport
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.frameNonzeroSupport_commuting
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.independent_iff_commutingContext
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.isAdmissibleSign_of_noActiveDependencies
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.isAdmissibleSign_of_support_independent
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.maxWeightIndependent_le_iff_contexts
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.max_abs_context_signed_sum_of_noActiveDependencies
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.max_abs_context_signed_sum_of_support_independent
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.maximalContextFrame
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.maximal_weights_iff_all_context_weights
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.mem_frameNonzeroSupport
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.midpoint_completionCandidates
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.pauliDependency_iff_binaryDependency
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.projectedFrameAtom
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.projectedFrameAtom_coordinate
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.projectedFrameAtom_coordinate_cases
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.projectedFrameAtom_ternary
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.projected_eq_contextPolytope_of_noActiveDependencies
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.realAdmissibleSigns
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.realAdmissibleSigns_eq_full_of_noActiveDependencies
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.realAdmissibleSigns_eq_full_of_support_independent
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.scalar_product_iff_for_any_order
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.scalar_subsetProduct_iff_zero_sum
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedContextGenerators
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedContextGenerators_support_independent
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedContextSet_eq_generator_range
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedMaximalCandidate
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedMaximalCandidate_dot
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedObservable
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedObservable_commutesWith
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedObservable_involutive
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.signedObservable_mem_contextFrame
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.subsetProduct
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.support_signedObservable
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.support_subsetProduct
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.vRepRepair_of_noActiveDependencies
#agtxiv_audit AgtXIv.Varela.VRepRepairObligations.projected_eq_contextPolytope
#agtxiv_audit Equiv.ofInjective
#agtxiv_audit Fintype.not_linearIndependent_iff
#agtxiv_audit IsCompact.exists_isMinOn
#agtxiv_audit LinearMap.BilinForm.finrank_orthogonal
#agtxiv_audit LinearMap.exists_extend
#agtxiv_audit LinearMap.quotKerEquivRange
#agtxiv_audit MState
#agtxiv_audit MState.exp_val
#agtxiv_audit MState.sum_abs_exp_val_finset_le_sqrt_card_of_pairwise_anticommute
#agtxiv_audit MState.sum_sq_exp_val_finset_le_one_of_pairwise_anticommute
#agtxiv_audit Pauli.addPhase_toCMatrix
#agtxiv_audit Pauli.mul_anticomm_of_not_commutesWith
#agtxiv_audit Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix
#agtxiv_audit Pauli.toCMatrix_neg
#agtxiv_audit PiLp.norm_single
#agtxiv_audit SimpleGraph.Coloring.surjOn_of_card_le_isClique
#agtxiv_audit SimpleGraph.IsClique.card_le_cliqueNum
#agtxiv_audit SimpleGraph.IsClique.card_le_of_coloring
#agtxiv_audit SimpleGraph.chromaticNumber_le_iff_colorable
#agtxiv_audit SimpleGraph.chromaticNumber_mono_of_hom
#agtxiv_audit SimpleGraph.cliqueNum_le_chromaticNumber
#agtxiv_audit SimpleGraph.exists_isNClique_cliqueNum
#agtxiv_audit SimpleGraph.induceUnivIso
#agtxiv_audit Submodule.Quotient.norm_mk_le
#agtxiv_audit Submodule.Quotient.norm_mk_lt
#agtxiv_audit exists_dual_vector''
