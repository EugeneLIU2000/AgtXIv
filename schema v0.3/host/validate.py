"""Validate v0.3 artifact integrity without claiming mathematical completion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core import canonical, digest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent


def validator(name):
    schemas = [json.loads(p.read_bytes()) for p in sorted((ROOT / "schemas").glob("*.schema.json"))]
    registry = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    schema = next(s for s in schemas if s["$id"].endswith("/" + name))
    return Draft202012Validator(schema, registry=registry)


def validate_run(directory):
    directory = Path(directory).resolve()
    errors, checks = [], []
    for filename, schema in (("plan.json", "plan.schema.json"), ("chain-certificate.json", "chain-certificate.schema.json")):
        path = directory / filename
        if not path.is_file():
            errors.append("missing artifact: " + filename)
            continue
        value = json.loads(path.read_bytes())
        for error in validator(schema).iter_errors(value):
            errors.append(f"{filename}:{list(error.path)}:{error.message}")
        checks.append(filename)
    graph = json.loads((directory / "graph.json").read_bytes())
    certificate = json.loads((directory / "chain-certificate.json").read_bytes())
    ledger = json.loads((directory / "ledger.json").read_bytes())
    if certificate["plan_id"] != ledger["plan"]["plan_id"]:
        errors.append("certificate/ledger plan mismatch")
    if sorted(certificate["query_ids"]) != sorted(graph["query_ids"]):
        errors.append("certificate/graph query mismatch")
    if certificate["state"] == "CHAIN_CERTIFICATE_EMITTED" and not certificate["query_declarations"]:
        errors.append("chain cannot be emitted without a composed query declaration")
    if not certificate["query_declarations"] and certificate["premises_from_lean_environment"]:
        errors.append("unbound premise list without actual query declaration")
    node_ids = {n["id"] for n in graph["nodes"]}
    if set(graph["query_ids"]) - node_ids:
        errors.append("query missing from selected graph")
    for group in graph["support_groups"]:
        for error in validator("support-group.schema.json").iter_errors(group):
            errors.append(f"support_group:{group.get('id')}:{error.message}")
        if {group["target"], *group["members"]} - node_ids:
            errors.append("dangling support group: " + group["id"])
    for node in graph["nodes"]:
        if set(node.get("bridging_claims", [])) - node_ids:
            errors.append("missing bridge: " + node["id"])
        if node["kind"] == "definition" and node.get("proof_discharged"):
            errors.append("definition reported as theorem proof: " + node["id"])
    for event in ledger["events"]:
        if event["kind"] == "ProgramReceipt":
            for error in validator("program-receipt.schema.json").iter_errors(event["payload"]):
                errors.append(f"receipt:{event['sequence']}:{error.message}")
    source_count = 0
    for path in sorted((directory / "papers").glob("*/extraction.json")):
        paper = json.loads(path.read_bytes())
        for claim in paper["claims"]:
            source = claim["source"]
            original = REPO / source["path"]
            if not original.resolve().is_relative_to(REPO.resolve()):
                errors.append("source escapes repository")
                continue
            raw = original.read_bytes()
            expected = source.get("source_sha256", source.get("sha256"))
            if expected and digest(raw) != expected:
                errors.append("changed frozen source: " + str(original))
            start, end = source["byte_start"], source["byte_end"]
            if not 0 <= start < end <= len(raw):
                errors.append("invalid source span: " + claim["id"])
            elif raw[start:end].decode("utf-8") != claim["text"]:
                errors.append("claim text differs from source bytes: " + claim["id"])
            source_count += 1
    return {"kind": "ArtifactIntegrityReport", "scope": "ONE_FROZEN_SCHEMA_V03_CASE_RUN",
            "directory": str(directory), "integrity": "PASS" if not errors else "FAIL",
            "errors": errors, "source_occurrences_checked": source_count,
            "mathematical_chain_state": certificate["state"],
            "note": "Integrity PASS does not assert complete extraction, reviewed dependencies, source faithfulness or a query proof."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    directory = args.run
    if directory is None:
        latest = ROOT / "runs/latest.json"
        if not latest.is_file():
            print("No frozen v0.3 run registered", file=sys.stderr)
            return 1
        directory = REPO / json.loads(latest.read_bytes())["path"]
    try:
        report = validate_run(directory)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"integrity": "FAIL", "error": str(exc)}))
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["integrity"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
