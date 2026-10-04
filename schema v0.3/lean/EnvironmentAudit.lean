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
