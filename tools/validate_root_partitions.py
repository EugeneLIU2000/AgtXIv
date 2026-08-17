#!/usr/bin/env python3
"""Validate five-route verification partitions for the three conceptual roots.

The validator enforces the central separation rule:

* missing Lean work is not a physical approximation;
* every claim/assumption/reasoning step is covered exactly once;
* a KERNEL_CHECKED badge must point to declarations and fresh pinned evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
ROOTS = (
    "stabilizer-codes-and-quantum-error-correction",
    "resource-theory-of-stabilizer-computation",
    "robustness-of-magic",
)
ROUTES = {
    "SOURCE_ALIGNMENT",
    "LEAN_KERNEL",
    "EXACT_PHYSICAL_SEMANTICS",
    "PHYSICAL_APPROXIMATION",
    "EMPIRICAL",
}
APPROXIMATION_FIELDS = {
    "exact_parent",
    "approximation_map",
    "control_parameters",
    "error_model",
    "validity_regime",
    "propagates_to",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    partition_count = 0
    object_count = 0
    kernel_checked_objects = 0
    approximation_objects = 0

    lean_evidence_path = REPO / "formal/AgtXIvRootMath/verification-result.json"
    lean_evidence = load_json(lean_evidence_path)
    verified_declarations = set(lean_evidence.get("declarations", []))
    stale_artifacts: list[str] = []
    for relative, tagged_expected in lean_evidence.get("artifact_hashes", {}).items():
        artifact = REPO / relative
        if not artifact.is_file() or sha256(artifact) != tagged_expected.removeprefix("sha256:"):
            stale_artifacts.append(relative)
    if stale_artifacts:
        errors.append(f"Lean evidence has stale or missing artifacts: {sorted(stale_artifacts)}")

    formal_contracts: dict[str, dict[str, Any]] = {}
    for path in REPO.glob("agents/*/formal/*.json"):
        document = load_json(path)
        if document.get("id"):
            formal_contracts[document["id"]] = document

    for root in ROOTS:
        base = REPO / "agents" / root
        manifest = load_json(base / "agent.json")
        partition_relative = manifest.get("verification", {}).get("verification_partition")
        if not partition_relative:
            errors.append(f"{root}: manifest lacks verification.verification_partition")
            continue
        partition_path = REPO / partition_relative
        if not partition_path.is_file():
            errors.append(f"{root}: partition missing: {partition_relative}")
            continue
        partition = load_json(partition_path)
        partition_count += 1

        if set(partition.get("route_catalog", [])) != ROUTES:
            errors.append(f"{root}: route_catalog must contain exactly the five canonical routes")
        if partition.get("agent") != manifest.get("agent", {}).get("id"):
            errors.append(f"{root}: partition agent does not match manifest")

        statements = load_jsonl(base / "knowledge/statements.jsonl")
        steps = load_jsonl(base / "reasoning/chains.jsonl")
        records = {record["id"]: record for record in statements + steps}
        expected_ids = set(records)
        objects = partition.get("objects", [])
        object_ids = [obj.get("object_id") for obj in objects]
        duplicates = sorted({object_id for object_id in object_ids if object_ids.count(object_id) > 1})
        if duplicates:
            errors.append(f"{root}: duplicate partition objects: {duplicates}")
        missing = sorted(expected_ids - set(object_ids))
        extra = sorted(set(object_ids) - expected_ids)
        if missing:
            errors.append(f"{root}: unpartitioned statements/steps: {missing}")
        if extra:
            errors.append(f"{root}: partition references unknown objects: {extra}")

        for obj in objects:
            object_count += 1
            object_id = obj.get("object_id", "<missing>")
            obligations = obj.get("verification_obligations", [])
            not_applicable = obj.get("not_applicable", [])
            obligation_routes = [item.get("route") for item in obligations]
            na_routes = [item.get("route") for item in not_applicable]
            covered = obligation_routes + na_routes
            if set(covered) != ROUTES or len(covered) != len(ROUTES):
                errors.append(f"{object_id}: each canonical route must occur exactly once")
            if set(obligation_routes) & set(na_routes):
                errors.append(f"{object_id}: a route cannot be both required and not applicable")
            if any(not item.get("reason") for item in not_applicable):
                errors.append(f"{object_id}: every not-applicable route needs a reason")
            if any(not item.get("status") or not item.get("evidence") for item in obligations):
                errors.append(f"{object_id}: every obligation needs nonempty status and evidence")

            approximation = next(
                (item for item in obligations if item.get("route") == "PHYSICAL_APPROXIMATION"),
                None,
            )
            if obj.get("approximation_introduced") is False:
                if approximation is not None or "PHYSICAL_APPROXIMATION" not in na_routes:
                    errors.append(f"{object_id}: exact object must mark PHYSICAL_APPROXIMATION not applicable")
            elif obj.get("approximation_introduced") is True:
                approximation_objects += 1
                if approximation is None:
                    errors.append(f"{object_id}: approximation introduced but no approximation obligation exists")
                else:
                    absent = sorted(field for field in APPROXIMATION_FIELDS if field not in approximation)
                    if absent:
                        errors.append(f"{object_id}: approximation obligation lacks {absent}")
            else:
                errors.append(f"{object_id}: approximation_introduced must be boolean")

            record = records.get(object_id, {})
            origin = record.get("origin")
            source = next((item for item in obligations if item.get("route") == "SOURCE_ALIGNMENT"), None)
            if origin in {"SOURCE_EXPLICIT", "AGENT_NORMALIZED", "AGENT_INFERRED"} and source is None:
                errors.append(f"{object_id}: {origin} object lacks SOURCE_ALIGNMENT obligation")
            if origin == "SOURCE_EXPLICIT" and not record.get("source_anchors"):
                errors.append(f"{object_id}: SOURCE_EXPLICIT object lacks source anchors")
            if origin in {"AGENT_NORMALIZED", "AGENT_INFERRED"}:
                relation = record.get("scope_relation") or (source or {}).get("scope_relation")
                if not relation:
                    errors.append(f"{object_id}: {origin} object lacks scope/alignment relation")

            lean = next((item for item in obligations if item.get("route") == "LEAN_KERNEL"), None)
            if lean and lean.get("status") == "KERNEL_CHECKED":
                kernel_checked_objects += 1
                declarations = set(lean.get("declarations", []))
                contracts = lean.get("formalization_contracts", [])
                if not declarations or not contracts:
                    errors.append(f"{object_id}: KERNEL_CHECKED lacks declarations or formalization contract")
                missing_declarations = sorted(declarations - verified_declarations)
                if missing_declarations:
                    errors.append(f"{object_id}: declarations absent from pinned Lean evidence: {missing_declarations}")
                for contract_id in contracts:
                    contract = formal_contracts.get(contract_id)
                    if contract is None:
                        errors.append(f"{object_id}: unknown formalization contract {contract_id}")
                    elif contract.get("status") != "KERNEL_CHECKED":
                        errors.append(f"{object_id}: formalization contract is not KERNEL_CHECKED: {contract_id}")
                    elif not declarations <= set(contract.get("declarations", [])):
                        errors.append(f"{object_id}: declaration not covered by {contract_id}")
            elif lean and "STALE_EVIDENCE" in str(lean.get("status")):
                warnings.append(f"{object_id}: Lean evidence is stale and cannot carry a kernel badge")

        exports = [load_json(path) for path in base.glob("exports/*.json")]
        if any(export.get("accepted") is True for export in exports):
            unresolved = [
                obj.get("object_id")
                for obj in objects
                for obligation in obj.get("verification_obligations", [])
                if obligation.get("status") not in {"PASSED", "KERNEL_CHECKED", "HUMAN_REVIEWED", "REPRODUCED"}
            ]
            if unresolved:
                errors.append(f"{root}: accepted export exists while partition obligations remain open: {sorted(set(unresolved))}")

    report = {
        "schema_version": "0.1.0-prototype",
        "root_partition_validation": "PASSED" if not errors else "FAILED",
        "partitions": partition_count,
        "objects_partitioned": object_count,
        "kernel_checked_objects": kernel_checked_objects,
        "approximation_objects": approximation_objects,
        "errors": errors,
        "warnings": warnings,
        "scientific_acceptance_effect": "NONE; all three Root PaperAgents remain accepted=false",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
