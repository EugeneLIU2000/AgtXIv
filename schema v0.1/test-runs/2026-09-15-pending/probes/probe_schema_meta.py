#!/usr/bin/env python3
"""Schema meta-validation for the six new agent modules (and Autoformalization as control).

Checks each draft/receipt schema against JSON Schema 2020-12 and resolves every $ref
through the pinned contract registry. This is the maximum coverage available for the
modules that have no semantic checker (Dependency, Review, Utility).

Run from the repository root:
  .venv/bin/python -B 'schema v0.1/test-runs/2026-09-15-pending/probes/probe_schema_meta.py'
"""
import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Resource

SPEC = importlib.util.spec_from_file_location("contracts_module", "schema v0.1/validate.py")
contracts_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contracts_module)
CONTRACTS = contracts_module.Contracts()

MODULES = ["Dependency Agent", "Review Agent", "Utility Agent",
           "Planner Agent", "Delta Agent", "Reader Agent", "Autoformalization Agent"]


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


rows = []
for module in MODULES:
    for schema_path in sorted(Path("schema v0.1", module).glob("*.schema.json")):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            Draft202012Validator.check_schema(schema)
            registry = CONTRACTS.registry.with_resource(schema["$id"], Resource.from_contents(schema))
            resolver = registry.resolver(base_uri=schema["$id"])
            for node in walk(schema):
                if "$ref" in node:
                    resolver.lookup(node["$ref"])
            rows.append({"module": module, "schema": schema_path.name, "status": "OK"})
        except Exception as error:  # noqa: BLE001 - report, do not raise
            rows.append({"module": module, "schema": schema_path.name,
                         "status": "FAIL", "error": str(error)[:200]})

for row in rows:
    print(json.dumps(row, ensure_ascii=False))
print(json.dumps({"total": len(rows), "failed": sum(1 for row in rows if row["status"] == "FAIL")}))
