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
#agtxiv_audit AgtXIv.PhyslibCandidate.expectation_eq_real_trace
#agtxiv_audit AgtXIv.Stabilizer.DensityMatrix
#agtxiv_audit AgtXIv.Stabilizer.DensityMatrix.toTraceOneHermitian
#agtxiv_audit AgtXIv.Stabilizer.pauli_toCMatrix_injective
#agtxiv_audit AgtXIv.Stabilizer.pauli_toCMatrix_isHermitian_of_sq_eq_one
#agtxiv_audit AgtXIv.Varela.MeasurementWindow
#agtxiv_audit AgtXIv.Varela.MeasurementWindow.expectationCoordinate
#agtxiv_audit MState
#agtxiv_audit MState.exp_val
#agtxiv_audit MState.sum_abs_exp_val_finset_le_sqrt_card_of_pairwise_anticommute
#agtxiv_audit MState.sum_sq_exp_val_finset_le_one_of_pairwise_anticommute
#agtxiv_audit Pauli.mul_anticomm_of_not_commutesWith
#agtxiv_audit Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix
#agtxiv_audit Pauli.toCMatrix_neg
