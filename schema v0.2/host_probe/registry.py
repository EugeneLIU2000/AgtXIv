"""v0.2 offline schema registry + validator.  HOST.md section 6, item 1."""
import json, pathlib, sys
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR = pathlib.Path(__file__).resolve().parent.parent / "schemas"
FILES = ["common.schema.json","task.schema.json","items.schema.json",
         "output.schema.json","run.schema.json"]

def build():
    registry = Registry()
    ids = {}
    for name in FILES:
        doc = json.loads((SCHEMA_DIR/name).read_text())
        uri = doc["$id"]
        ids[name] = uri
        registry = registry.with_resource(uri, Resource.from_contents(doc))
        # also register by bare filename so relative $refs resolve
        registry = registry.with_resource(name, Resource.from_contents(doc))
    return registry, ids

def validator_for(name):
    registry, ids = build()
    doc = json.loads((SCHEMA_DIR/name).read_text())
    return Draft202012Validator(doc, registry=registry)

def walk_refs():
    """Prove every $ref in every schema resolves offline."""
    registry, ids = build()
    unresolved, total = [], 0
    for name in FILES:
        doc = json.loads((SCHEMA_DIR/name).read_text())
        base = doc["$id"]
        resolver = registry.resolver(base)
        def rec(node):
            nonlocal total
            if isinstance(node, dict):
                if "$ref" in node and isinstance(node["$ref"], str):
                    total += 1
                    try: resolver.lookup(node["$ref"])
                    except Exception as e: unresolved.append((name, node["$ref"], type(e).__name__))
                for v in node.values(): rec(v)
            elif isinstance(node, list):
                for v in node: rec(v)
        rec(doc)
    return total, unresolved

if __name__ == "__main__":
    total, bad = walk_refs()
    print(f"$refs walked: {total}   unresolved: {len(bad)}")
    for b in bad: print("   ", b)
    sys.exit(1 if bad else 0)
