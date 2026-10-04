import Lean

/- The original driver is retained for immutable historical environments.
   This version compares the types of actual used proof-value binders in Lean. -/
open Lean Elab Command

namespace AgtXIv.GeneratedProofDriverV2

private partial def termUsesFVar (e : Expr) (id : FVarId) : Bool :=
  match e with
  | .fvar other => id == other
  | .app f a => termUsesFVar f id || termUsesFVar a id
  | .lam _ _ b _ => termUsesFVar b id
  | .letE _ _ v b _ => termUsesFVar v id || termUsesFVar b id
  | .mdata _ b => termUsesFVar b id
  | .proj _ _ b => termUsesFVar b id
  | _ => false

elab "#agtxiv_used_premises " name:ident " against " "[" targets:ident,* "]" : command => do
  let targetNames := targets.getElems.map (·.getId)
  let result ← liftTermElabM do
    let info ← getConstInfo name.getId
    let some value := info.value? (allowOpaque := true)
      | throwError "candidate declaration has no value"
    Meta.lambdaTelescope value fun xs body => do
      let mut rows : Array Json := #[]
      for index in [:xs.size] do
        let x := xs[index]!
        let localDecl ← x.fvarId!.getDecl
        if (← Meta.isProp localDecl.type) && termUsesFVar body x.fvarId! then
          let mut equal : Array String := #[]
          for target in targetNames do
            let typeMatches ← withoutModifyingState do
              let proposition ← Meta.mkConstWithFreshMVarLevels target
              unless ← Meta.isProp proposition do
                throwError "explicit prerequisite is not a proposition"
              Meta.isDefEq localDecl.type proposition
            if typeMatches then
              equal := equal.push target.toString
          rows := rows.push (Json.mkObj [
            ("binder_index", toJson index),
            ("binder", toJson localDecl.userName.toString),
            ("type", toJson (← Meta.ppExpr localDecl.type).pretty),
            ("type_constants", toJson (localDecl.type.getUsedConstants.map Name.toString)),
            ("definitionally_equal_propositions", toJson equal),
            ("type_equality_method", toJson "LEAN_META_ISDEFEQ_ACTUAL_PROOF_VALUE_BINDER"),
            ("proof_body_uses_binder", toJson true)])
      pure (Json.mkObj [("declaration", toJson name.getId.toString),
        ("checked_propositions", toJson (targetNames.map Name.toString)),
        ("protocol", toJson "ACTUAL_VALUE_BINDER_ISDEFEQ_V2"),
        ("used_prop_binders", toJson rows)])
  liftIO <| IO.println ("AGTXIV_USED_PREMISES_JSON " ++ result.compress)

private def parseTerm (text : String) : CommandElabM (TSyntax `term) := do
  match Parser.runParserCategory (← getEnv) `term text with
  | .ok parsed => pure ⟨parsed⟩
  | .error message => throwError "candidate term parse failed: {message}"

elab "#agtxiv_candidate " name:ident kind:str statement:str value:str : command => do
  let type ← parseTerm statement.getString
  let term ← parseTerm value.getString
  if kind.getString == "THEOREM" then
    elabCommand (← `(theorem $name : $type := $term))
  else if kind.getString == "DEFINITION" then
    elabCommand (← `(noncomputable def $name : $type := $term))
  else
    throwError "unsupported candidate declaration kind"

end AgtXIv.GeneratedProofDriverV2
