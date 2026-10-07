"""Offline registry for the v0.4 contracts; v0.3 defs resolve by $id from the frozen v0.3 files."""
from __future__ import annotations

import functools
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
V03_SCHEMAS = ROOT.parent / "schema v0.3" / "schemas"
SCHEMA_FILES = (*sorted((ROOT / "schemas").glob("*.schema.json")),
                V03_SCHEMAS / "research.schema.json", V03_SCHEMAS / "human-review.schema.json")
SCHEMAS = {s["$id"]: s for s in (json.loads(p.read_bytes()) for p in SCHEMA_FILES)}
CORPUS_ID = "https://agtxiv.org/schema/research/0.4.0/corpus.schema.json"
DEFS = tuple(SCHEMAS[CORPUS_ID]["$defs"])
REGISTRY = Registry().with_resources((i, Resource.from_contents(s)) for i, s in SCHEMAS.items())


@functools.cache
def validator(def_name):
    if def_name not in DEFS:
        raise KeyError("unknown v0.4 def: " + def_name)
    return Draft202012Validator({"$ref": f"{CORPUS_ID}#/$defs/{def_name}"}, registry=REGISTRY)


def validate(def_name, instance):
    """Raise jsonschema.ValidationError (the most relevant error) if instance violates def_name."""
    error = best_match(validator(def_name).iter_errors(instance))
    if error is not None:
        raise error
