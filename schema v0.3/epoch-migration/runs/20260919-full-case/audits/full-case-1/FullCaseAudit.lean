import AgtXIvStabilizerness
import QuantumInfo.States.Mixed.MState
import Physlib.Relativity.PauliMatrices.Basic
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


/-!
Both inputs now live in the same Physlib/mathlib epoch. The admissible-domain
equality remains explicit: this is not the paper's sign-collapse theorem.
-/

namespace AgtXIv.CommonEpoch

open scoped BigOperators

theorem quantum_admissible_sign_maximum
    {d ι : Type*} [Fintype d] [DecidableEq d] [Fintype ι]
    (ρ : MState d) (A : ι → HermitianMat d ℂ)
    (admissible : Set (ι → ℝ)) (μ : ℝ)
    (hCollapse : admissible = {f | ∀ i, AgtXIv.Stabilizerness.IsSign (f i)}) :
    IsGreatest
      (AgtXIv.Stabilizerness.admissibleSignedValues admissible (fun i => ρ.exp_val (A i)) μ)
      ((∑ i, |ρ.exp_val (A i)|) + |μ|) :=
  AgtXIv.Stabilizerness.max_abs_admissible_signed_sum_of_sign_set_eq
    admissible (fun i => ρ.exp_val (A i)) μ hCollapse

end AgtXIv.CommonEpoch
#agtxiv_audit AgtXIv.CommonEpoch.quantum_admissible_sign_maximum
#agtxiv_audit AgtXIv.Gottesman.groupAverage_eq_self_iff
#agtxiv_audit AgtXIv.Gottesman.groupAverage_idempotent
#agtxiv_audit AgtXIv.Gottesman.groupAverage_isProjection
#agtxiv_audit AgtXIv.Gottesman.groupAverage_mem_commonFixed
#agtxiv_audit AgtXIv.Gottesman.range_groupAverageMap
#agtxiv_audit AgtXIv.GraphFoundation.IsPerfect
#agtxiv_audit AgtXIv.GraphFoundation.WeightedPerfectDualityCertificate
#agtxiv_audit AgtXIv.GraphFoundation.WeightedPerfectGraphFoundation
#agtxiv_audit AgtXIv.GraphFoundation.fractionalCliqueCoverValue
#agtxiv_audit AgtXIv.GraphFoundation.independentFinsets
#agtxiv_audit AgtXIv.GraphFoundation.maxWeightIndependent
#agtxiv_audit AgtXIv.GraphFoundation.weighted_duality_of_foundation
#agtxiv_audit AgtXIv.RoM.coeff_sum_eq_one
#agtxiv_audit AgtXIv.RoM.exists_l1Minimizer
#agtxiv_audit AgtXIv.RoM.feasible_faithful
#agtxiv_audit AgtXIv.RoM.finiteRoM_mono_of_atomImages
#agtxiv_audit AgtXIv.RoM.kernelOfAtomImages
#agtxiv_audit AgtXIv.RoM.normalized_l1
#agtxiv_audit AgtXIv.RoM.reconstruct_push_kernelOfAtomImages
#agtxiv_audit AgtXIv.Stabilizer.DensityStabilizerAtomMap.densityFullStabilizerRoM_mono
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.exists_semanticClifford_map_standardIndependentZFrame
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliFrame.finrank_commonFixed_eq_two_pow_sub
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliGenerators.exists_normalized_generator_fixed_vector
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliGenerators.finrank_commonFixed_eq_two_pow_codeDimension
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliGenerators.generatorsFix_iff_mem_commonFixed
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliGenerators.generatorsFix_iff_mem_generalRankCommonFixed
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliGenerators.normalized_fixed_vectors_differ_by_phase
#agtxiv_audit AgtXIv.Stabilizer.IndependentSignedPauliGenerators.pureStabilizerDensity
#agtxiv_audit AgtXIv.Stabilizer.StabilizerAtomMap.fullStabilizerRoM_mono
#agtxiv_audit AgtXIv.Stabilizer.densityFullStabilizerRoM_eq_one_iff_mem_cliffordOrbitPolytope
#agtxiv_audit AgtXIv.Stabilizer.fullStabilizerRoM_eq_one_iff_free
#agtxiv_audit AgtXIv.Stabilizer.one_lt_densityFullStabilizerRoM_iff_magicByCliffordOrbit
#agtxiv_audit AgtXIv.Stabilizer.pauli_toCMatrix_isHermitian_of_sq_eq_one
#agtxiv_audit AgtXIv.Stabilizer.pureStabilizerByFrame_iff_byCliffordOrbit
#agtxiv_audit AgtXIv.Stabilizer.range_frameAtom_eq_cliffordOrbitAtoms
#agtxiv_audit AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_idempotent
#agtxiv_audit AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_isHermitian
#agtxiv_audit AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_posSemidef
#agtxiv_audit AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_range_finrank
#agtxiv_audit AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_trace
#agtxiv_audit AgtXIv.Stabilizer.stabilizerFreeByFrames_iff_mem_cliffordOrbitPolytope
#agtxiv_audit AgtXIv.Stabilizer.stabilizerPolytopeByFrames_eq_byCliffordOrbit
#agtxiv_audit AgtXIv.Stabilizer.stabilizerProjectorMatrix_idempotent
#agtxiv_audit AgtXIv.Stabilizer.stabilizerProjectorMatrix_isHermitian
#agtxiv_audit AgtXIv.Stabilizer.stabilizerProjectorMatrix_posSemidef
#agtxiv_audit AgtXIv.Stabilizer.stabilizerProjectorMatrix_range_finrank_one
#agtxiv_audit AgtXIv.Stabilizer.stabilizerProjectorMatrix_trace_one
#agtxiv_audit AgtXIv.Stabilizer.toLin_stabilizerCodeProjectorMatrix
#agtxiv_audit AgtXIv.Stabilizer.traceOneHermitianAffine_le_completeFrame_affineSpan
#agtxiv_audit AgtXIv.Stabilizer.traceOne_canonicalStabilizer_feasible
#agtxiv_audit AgtXIv.Stabilizer.trace_eval_eq_zero_of_support_ne_zero
#agtxiv_audit AgtXIv.Stabilizerness.abs_signed_sum_add_le
#agtxiv_audit AgtXIv.Stabilizerness.admissibleSignedValues
#agtxiv_audit AgtXIv.Stabilizerness.admissible_signed_sum_le
#agtxiv_audit AgtXIv.Stabilizerness.affineSpan_eq_top_of_vectorSpan_eq_top
#agtxiv_audit AgtXIv.Stabilizerness.exists_sign_attaining_abs_sum
#agtxiv_audit AgtXIv.Stabilizerness.full_sign_cube_collapse_instance
#agtxiv_audit AgtXIv.Stabilizerness.max_abs_admissible_signed_sum_of_sign_set_eq
#agtxiv_audit AgtXIv.Stabilizerness.max_abs_signed_sum
#agtxiv_audit AgtXIv.Varela.MeasurementWindow
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.MaximalSignedContext.abs_vector_le_one
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.expectationCoordinate
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.expectationProjection_reconstruct
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.mem_projectedStabilizerPolytope_iff
#agtxiv_audit AgtXIv.Varela.VRepRepairObligations
#agtxiv_audit AgtXIv.Varela.VRepRepairObligations.projected_eq_contextPolytope
#agtxiv_audit AgtXIv.Varela.reducedStabilizerPolytope_vrep_conditional
#agtxiv_audit MState.exp_val
#agtxiv_audit Pauli.mul_anticomm_of_not_commutesWith
#agtxiv_audit Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix
#agtxiv_audit Pauli.toCMatrix_neg
#agtxiv_audit PauliMatrix.pauliMatrix_anticommutator
#agtxiv_audit PauliMatrix.vectorMatrix_sq
