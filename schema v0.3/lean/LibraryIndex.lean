import Lean

/-!
The host prepends the frozen proof environment's imports and appends one
`#agtxiv_library_index "rows.jsonl" ["Prefix", ...]` command. A constant is
indexed when its module or its own name starts with a prefix and it is not an
internal, matcher, no-confusion, auxiliary-recursor (or helper) or
compiler-generated structural declaration. Rows carry Lean's own name, kind,
pretty-printed type and module. Retrieval over them is a candidate search,
never a library binding or a source alignment.
-/

open Lean Meta Elab Command in
elab "#agtxiv_library_index " path:str " [" prefixes:str,* "]" : command => do
  let prefixes := prefixes.getElems.map (·.getString)
  let env ← getEnv
  let generated := ["noConfusionType", "ctorIdx", "ctorElimType", "ctorElim", "sizeOf_spec", "injEq", "inj"]
  let handle ← IO.FS.Handle.mk path.getString .write
  let count ← liftTermElabM <| withTheReader Core.Context ({ · with maxHeartbeats := 0 }) <|
      withOptions (fun opts => opts.set `pp.width (140 : Nat)) do
    let mut count := 0
    for moduleName in env.header.moduleNames, data in env.header.moduleData do
      let moduleText := moduleName.toString
      for info in data.constants do
        let name := info.name
        let kind? : Option String := match info with
          | .thmInfo _ => some "THEOREM" | .defnInfo _ => some "DEFINITION"
          | .axiomInfo _ => some "AXIOM" | .opaqueInfo _ => some "OPAQUE"
          | .inductInfo _ => some "INDUCTIVE" | .ctorInfo _ => some "CONSTRUCTOR"
          | _ => none
        let some kind := kind? | continue
        unless prefixes.any (fun p => p.isPrefixOf moduleText || p.isPrefixOf name.toString) do continue
        if name.isInternalDetail || isAuxRecursor env name || isAuxRecursor env name.getPrefix ||
            isNoConfusion env name || isMatcherCore env name ||
            (match name with | .str _ last => generated.contains last | _ => false) then
          continue
        let type ← ppExpr info.type
        handle.putStrLn (Json.mkObj [("name", toJson name.toString), ("kind", toJson kind),
          ("type", toJson type.pretty), ("module", toJson moduleText)]).compress
        count := count + 1
    pure count
  handle.flush
  liftIO <| IO.println s!"AGTXIV_LIBRARY_INDEX_ROWS {count}"
