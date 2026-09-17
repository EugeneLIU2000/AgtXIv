"""Validate a v0.2 model output against output.schema.json, then run the
cross-object checks CONTRACT section 3 requires (schema alone cannot do them)."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from registry import validator_for

ALLOWED = {
 "paper.extract": {"source_locator","definition","scientific_claim","math_claim"},
 "dependency.search": {"source_locator","dependency_candidate","search_request"},
 "autoformalization.lamport": {"lamport_proof"},
 "autoformalization.lean": {"lean_source"},
}

def check(path, task_input_aliases):
    doc = json.loads(pathlib.Path(path).read_text())
    errs = []
    # layer SHAPE
    v = validator_for("output.schema.json")
    for e in sorted(v.iter_errors(doc), key=lambda e: e.path):
        errs.append(("SHAPE", list(e.path), e.message))
    if errs: return doc, errs
    op = doc["operation"]
    items = doc["items"]
    ids = [i["id"] for i in items]
    # unique ids
    if len(ids) != len(set(ids)): errs.append(("REFERENCES","items","duplicate item.id"))
    # operation / kind allow-list
    for i in items:
        if i["kind"] not in ALLOWED.get(op, set()):
            errs.append(("SHAPE", i["id"], f"kind {i['kind']} not allowed for {op}"))
    # reference resolution: {"input": alias} must exist; {"local": id} must be unique in batch
    idset = set(ids)
    def refs(node, where):
        if isinstance(node, dict):
            if set(node) == {"input"}:
                if node["input"] not in task_input_aliases:
                    errs.append(("REFERENCES", where, f"invisible input alias {node['input']!r}"))
            elif set(node) == {"local"}:
                if node["local"] not in idset:
                    errs.append(("REFERENCES", where, f"dangling local ref {node['local']!r}"))
            else:
                for k,val in node.items(): refs(val, f"{where}.{k}")
        elif isinstance(node, list):
            for n,val in enumerate(node): refs(val, f"{where}[{n}]")
    for i in items: refs(i, i["id"])
    # reference TYPE agreement (CONTRACT section 3)
    kind = {i["id"]: i["kind"] for i in items}
    for i in items:
        for s in i.get("sources", []) or []:
            if "local" in s and kind.get(s["local"]) != "source_locator":
                errs.append(("REFERENCES", i["id"], f"sources -> {s['local']} is {kind.get(s['local'])}, not source_locator"))
        if i["kind"] == "math_claim":
            n = i.get("normalization") or {}
            rel = n.get("relation_to_source")
            src_s, norm_s = n.get("source_statement"), n.get("normalized_statement")
            # VERBATIM means exactly that: no notation was unified, so the two agree.
            if rel == "VERBATIM" and src_s is not None and src_s != norm_s:
                errs.append(("REFERENCES", i["id"],
                             "relation_to_source VERBATIM but source_statement and "
                             "normalized_statement differ"))
            # Conversely, a declared departure that changed nothing is a mislabel.
            if rel and rel != "VERBATIM" and src_s is not None and src_s == norm_s:
                errs.append(("REFERENCES", i["id"],
                             f"relation_to_source {rel} but the two statements are identical"))
            sc = i.get("source_claim") or {}
            if "local" in sc and kind.get(sc["local"]) != "scientific_claim":
                errs.append(("REFERENCES", i["id"], "source_claim must point at a scientific_claim"))
        if i["kind"] == "scientific_claim":
            cids = [c["id"] for c in i.get("components", [])]
            if len(cids) != len(set(cids)):
                errs.append(("REFERENCES", i["id"], "duplicate component id"))
            for c in i.get("components", []):
                # every conclusion component needs a math target OR a nonempty residual
                if not c.get("math_refs") and not c.get("residual"):
                    errs.append(("REFERENCES", f"{i['id']}.{c['id']}",
                                 "component has neither math_refs nor residual"))
    # reverse ownership: math_claim.component_id must name a real component of its source_claim
    by_id = {i["id"]: i for i in items}
    for i in items:
        if i["kind"] == "math_claim":
            sc = (i.get("source_claim") or {}).get("local")
            if sc and sc in by_id:
                comps = {c["id"] for c in by_id[sc].get("components", [])}
                if i.get("component_id") not in comps:
                    errs.append(("REFERENCES", i["id"], f"component_id {i.get('component_id')!r} not in {sc}"))
                else:
                    comp = next(c for c in by_id[sc]["components"] if c["id"] == i["component_id"])
                    if not any(r.get("local") == i["id"] for r in comp.get("math_refs", [])):
                        errs.append(("REFERENCES", i["id"], "reverse ownership: component does not point back"))
    return doc, errs

if __name__ == "__main__":
    doc, errs = check(sys.argv[1], set(sys.argv[2].split(",")) if len(sys.argv)>2 else set())
    print(f"operation={doc.get('operation')} items={len(doc.get('items',[]))} issues={len(doc.get('issues',[]))}")
    if not errs: print("PASS  SHAPE + REFERENCES")
    else:
        print(f"FAIL  {len(errs)} error(s)")
        for layer, where, msg in errs: print(f"   [{layer}] {where}: {msg}")
    sys.exit(1 if errs else 0)
