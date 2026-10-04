import Lean

/- Model text is parsed as one term per field, never as a command sequence.
   This is a syntactic boundary; resource isolation remains the host's job. -/
open Lean Elab Command

namespace AgtXIv.GeneratedProofDriver

private partial def termUsesFVar (e : Expr) (id : FVarId) : Bool :=
  match e with
  | .fvar other => id == other
  | .app f a => termUsesFVar f id || termUsesFVar a id
  | .lam _ _ b _ => termUsesFVar b id
  | .letE _ _ v b _ => termUsesFVar v id || termUsesFVar b id
  | .mdata _ b => termUsesFVar b id
  | .proj _ _ b => termUsesFVar b id
  | _ => false

elab "#agtxiv_used_premises " name:ident : command => do
  let result ← liftTermElabM do
    let info ← getConstInfo name.getId
    let some value := info.value? (allowOpaque := true)
      | throwError "candidate declaration has no value"
    Meta.lambdaTelescope value fun xs body => do
      let mut rows : Array Json := #[]
      for x in xs do
        let localDecl ← x.fvarId!.getDecl
        if (← Meta.isProp localDecl.type) && termUsesFVar body x.fvarId! then
          rows := rows.push (Json.mkObj [
            ("binder", toJson localDecl.userName.toString),
            ("type_constants", toJson (localDecl.type.getUsedConstants.map Name.toString)),
            ("proof_body_uses_binder", toJson true)])
      pure (Json.mkObj [("declaration", toJson name.getId.toString), ("used_prop_binders", toJson rows)])
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

end AgtXIv.GeneratedProofDriver
