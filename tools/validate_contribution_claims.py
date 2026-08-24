#!/usr/bin/env python3
"""Validate ContributionClaim registries and the seven source-audit fixtures."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import unicodedata
from pathlib import Path
from typing import Any

import jsonschema
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "Stabilizerness/ScientificClaimRegistry/contributions/contribution-claims.jsonl"
CALIBRATIONS = ROOT / "Stabilizerness/ExternalRecordRegistry/contribution-calibrations/contribution-calibrations.jsonl"
SUPPORT = ROOT / "Stabilizerness/ExternalRecordRegistry/claim-support-associations/contribution-support.jsonl"
TARGET_REF_SCHEMA = ROOT / "schemas/target-ref.schema.json"
PROFILE = ROOT / "schemas/record-canonical-json-v1.profile.json"
SCHEMAS = {
    "agtxiv.contribution-claim/1.1.0": ROOT / "Stabilizerness/ScientificClaimRegistry/schema/contribution-claim.schema.json",
    "agtxiv.contribution-calibration-record/1.1.0": ROOT / "Stabilizerness/ExternalRecordRegistry/schema/contribution-calibration-record.schema.json",
    "agtxiv.claim-support-association/1.1.0": ROOT / "Stabilizerness/ExternalRecordRegistry/schema/claim-support-association.schema.json",
}
SET_VALUED_KEYS = {"claim_ir_members", "contribution_tags", "links", "reason_codes", "scope_hints"}
FORBIDDEN_CONTRIBUTION_KEYS = {
    "status", "truth_status", "verification", "verification_status", "verified",
    "contribution_verified", "novelty", "priority", "evidence", "evidence_ids",
    "blocker", "blockers", "support", "supports", "support_links",
}
SUPPORTED_TARGET_KINDS = {
    "org.agtxiv.claim_ir": "math-claim-ir:",
    "org.agtxiv.mathematical_proposition_ir": "math-proposition-ir:",
}
MATHEMATICAL_DAG_ID_PREFIXES = (*SUPPORTED_TARGET_KINDS.values(), "assumption:", "statement:")
COVERAGE_RANK = {"NONE": 0, "PARTIAL": 1, "COMPLETE": 2}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def normalize_string(value: str) -> str:
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def canonicalize(value: Any, parent_key: str | None = None) -> Any:
    """Canonicalize the primitive/string/integer JSON subset declared by PROFILE."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("NaN and infinities are forbidden")
        raise ValueError("non-integral numbers are outside the implemented canonical profile")
    if isinstance(value, str):
        return normalize_string(value)
    if isinstance(value, list):
        members = [canonicalize(item) for item in value]
        if parent_key in SET_VALUED_KEYS:
            encoded = [(canonical_bytes(item), item) for item in members]
            encoded.sort(key=lambda pair: pair[0])
            if any(left[0] == right[0] for left, right in zip(encoded, encoded[1:])):
                raise ValueError(f"canonical duplicate in set-valued array {parent_key}")
            return [item for _, item in encoded]
        return members
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            normalized_key = normalize_string(key)
            if normalized_key in normalized:
                raise ValueError(f"canonical duplicate object key {normalized_key}")
            normalized[normalized_key] = canonicalize(child, normalized_key)
        return {key: normalized[key] for key in sorted(normalized)}
    raise ValueError(f"unsupported JSON value {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    normalized = canonicalize(value)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def hash_value(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def profile_ref() -> dict[str, str]:
    return {"id": "agtxiv.record-canonical-json/1.0.0", "content_hash": hash_value(json.loads(PROFILE.read_text()))}


def semantic_payload(claim: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "paper_id", "role", "granularity", "contribution_kind", "contribution_tags",
        "source_characterization", "normalized_statement", "scope_hints", "facets",
    )
    return {key: claim[key] for key in keys}


def semantic_hash(claim: dict[str, Any]) -> str:
    return hash_value(semantic_payload(claim))


def artifact_hash(claim: dict[str, Any]) -> str:
    payload = copy.deepcopy(claim)
    payload.get("artifact", {}).pop("artifact_hash", None)
    payload.pop("content_hash", None)
    return hash_value(payload)


def record_content_hash(record: dict[str, Any]) -> str:
    return hash_value({key: value for key, value in record.items() if key != "content_hash"})


def external_content_hash(record: dict[str, Any]) -> str:
    return record_content_hash(record)


def nested_forbidden(value: Any, path: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key.lower() in FORBIDDEN_CONTRIBUTION_KEYS:
                errors.append(child_path)
            errors.extend(nested_forbidden(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(nested_forbidden(child, f"{path}[{index}]"))
    return errors


def is_contribution_record(record: dict[str, Any]) -> bool:
    return record.get("schema") == "agtxiv.contribution-claim/1.1.0" and record.get("role") == "CONTRIBUTION" and record.get("granularity") == "NARRATIVE_ATOMIC"


def contribution_target_ref(claim: dict[str, Any], component_path: str | None = None, artifact: bool = True) -> dict[str, Any]:
    return {
        "target_kind": "org.agtxiv.scientific_claim.contribution",
        "type_schema": {"uri": "https://agtxiv.org/schema/contribution-claim/1.1.0", "content_hash": file_hash(SCHEMAS["agtxiv.contribution-claim/1.1.0"])},
        "target_id": claim["id"], "target_revision": claim["record_revision"], "target_content_hash": claim["content_hash"],
        "target_artifact": copy.deepcopy(claim["artifact"]) if artifact else None,
        "component_path": component_path, "claim_ir": None, "claim_ir_members": [],
    }


def existing_support_targets(root: Path) -> tuple[dict[tuple[str, int], dict[str, Any]], list[str]]:
    targets: dict[tuple[str, int], dict[str, Any]] = {}
    errors: list[str] = []
    for pattern in ("Stabilizerness/MathClaimIRRegistry/claims/*.jsonl", "Stabilizerness/ExternalRecordRegistry/propositions/*.jsonl"):
        for path in root.glob(pattern):
            for row in load_jsonl(path):
                identifier = row.get("id", "")
                if not identifier.startswith(("math-claim-ir:", "math-proposition-ir:")):
                    continue
                key = (identifier, row.get("revision"))
                if key in targets:
                    errors.append(f"support target does not resolve uniquely: {key}")
                targets[key] = row
    return targets, errors


def target_ref_for_existing(target: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    is_claim_ir = target["id"].startswith("math-claim-ir:")
    if is_claim_ir:
        kind = "org.agtxiv.claim_ir"
        schema_path = root / "Stabilizerness/MathClaimIRRegistry/schema/math-claim-ir.schema.json"
        claim_ir = {"id": target["id"], "revision": target["revision"], "semantic_content_hash": target["semantic_content_hash"]}
    else:
        kind = "org.agtxiv.mathematical_proposition_ir"
        schema_path = root / "Stabilizerness/ExternalRecordRegistry/schema/mathematical-proposition-ir.schema.json"
        claim_ir = None
    return {
        "target_kind": kind,
        "type_schema": {"uri": target["artifact"]["schema_uri"], "content_hash": file_hash(schema_path)},
        "target_id": target["id"], "target_revision": target["revision"], "target_content_hash": target["semantic_content_hash"],
        "target_artifact": copy.deepcopy(target["artifact"]), "component_path": None,
        "claim_ir": claim_ir, "claim_ir_members": [],
    }


def validate_dependency_payload(payload: Any, label: str = "dependency payload") -> list[str]:
    """Validate mathematical references in legacy and structured dependency DAG shapes."""
    errors: list[str] = []
    reference_slots = {"nodes", "source", "target", "from", "to", "claim", "claim_id", "target_ref"}

    def validate_identifier(identifier: Any, target_kind: Any = None) -> None:
        if not isinstance(identifier, str):
            errors.append(f"{label}: mathematical DAG node reference has no string ID")
            return
        if identifier.startswith("claim:contribution:") or target_kind == "org.agtxiv.scientific_claim.contribution":
            errors.append(f"{label}: ContributionClaim cannot be a MathClaimDependencyDAG node: {identifier}")
            return
        if target_kind is not None:
            prefix = SUPPORTED_TARGET_KINDS.get(target_kind)
            if prefix is None:
                errors.append(f"{label}: unsupported mathematical DAG target kind: {target_kind}")
            elif not identifier.startswith(prefix):
                errors.append(f"{label}: mathematical DAG target kind {target_kind} does not match ID {identifier}")
            return
        if not identifier.startswith(MATHEMATICAL_DAG_ID_PREFIXES):
            errors.append(f"{label}: unsupported mathematical DAG node ID family: {identifier}")

    def validate_reference(value: Any) -> None:
        if isinstance(value, str):
            validate_identifier(value)
            return
        if isinstance(value, list):
            for child in value:
                validate_reference(child)
            return
        if not isinstance(value, dict):
            errors.append(f"{label}: mathematical DAG node reference must be a string or object")
            return
        has_identity = False
        if "target_id" in value or "target_kind" in value:
            validate_identifier(value.get("target_id"), value.get("target_kind"))
            has_identity = True
        elif "id" in value:
            validate_identifier(value.get("id"))
            has_identity = True

        nested_slots = [(key, child) for key, child in value.items() if key in reference_slots]
        for _, child in nested_slots:
            validate_reference(child)
        if has_identity or nested_slots:
            return

        # Object-valued node collections and wrappers may use arbitrary map keys.
        # Descend only into structured children; scalar metadata such as labels and
        # colors is not a node reference unless it occupies a recognized slot.
        for key, child in value.items():
            if isinstance(key, str) and key.startswith(MATHEMATICAL_DAG_ID_PREFIXES + ("claim:",)):
                validate_identifier(key)
            elif isinstance(child, (dict, list)):
                validate_reference(child)

    def walk(value: Any) -> None:
        if isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            for key, child in value.items():
                if key in reference_slots:
                    validate_reference(child)
                else:
                    walk(child)

    walk(payload)
    return errors


def validate_manifest_discovery(root: Path) -> list[str]:
    errors: list[str] = []
    scientific = json.loads((root / "Stabilizerness/ScientificClaimRegistry/manifest.json").read_text())
    external = json.loads((root / "Stabilizerness/ExternalRecordRegistry/manifest.json").read_text())
    expected = (
        (scientific, "object_files", str(CLAIMS.relative_to(ROOT))),
        (scientific, "schema_files", str(SCHEMAS["agtxiv.contribution-claim/1.1.0"].relative_to(ROOT))),
        (scientific, "shared_schema_files", str(TARGET_REF_SCHEMA.relative_to(ROOT))),
        (scientific, "serialization_profile_files", str(PROFILE.relative_to(ROOT))),
        (external, "contribution_calibration_files", str(CALIBRATIONS.relative_to(ROOT))),
        (external, "claim_support_association_files", str(SUPPORT.relative_to(ROOT))),
        (external, "schema_files", str(SCHEMAS["agtxiv.contribution-calibration-record/1.1.0"].relative_to(ROOT))),
        (external, "schema_files", str(SCHEMAS["agtxiv.claim-support-association/1.1.0"].relative_to(ROOT))),
        (external, "shared_schema_files", str(TARGET_REF_SCHEMA.relative_to(ROOT))),
    )
    for manifest, field, path in expected:
        if path not in manifest.get(field, []):
            errors.append(f"registry manifest does not discover {path} through {field}")
    for manifest in (scientific, external):
        for field, paths in manifest.items():
            if field.endswith("_files") or field in {"object_files", "schema_files"}:
                for relative in paths:
                    if not (root / relative).is_file():
                        errors.append(f"manifest-listed path does not exist: {relative}")
    return errors


def immutable_record_ref(record: dict[str, Any], target_kind: str) -> dict[str, Any]:
    if target_kind == "org.agtxiv.scientific_claim.contribution":
        return contribution_target_ref(record)
    schema_name = record["schema"]
    schema_path = SCHEMAS[schema_name]
    schema = json.loads(schema_path.read_text())
    return {
        "target_kind": target_kind,
        "type_schema": {"uri": schema["$id"], "content_hash": file_hash(schema_path)},
        "target_id": record["id"], "target_revision": record["record_revision"],
        "target_content_hash": record["content_hash"], "target_artifact": None,
        "component_path": None, "claim_ir": None, "claim_ir_members": [],
    }


def validate_supersedes(records: list[dict[str, Any]], target_kind: str) -> list[str]:
    errors: list[str] = []
    by_key = {(row.get("id"), row.get("record_revision")): row for row in records}
    for row in records:
        revision, supersedes = row.get("record_revision"), row.get("supersedes")
        if revision == 1 and supersedes is not None:
            errors.append(f"{row.get('id')}: revision 1 must not supersede another record")
        if isinstance(revision, int) and revision > 1:
            previous = by_key.get((row.get("id"), revision - 1))
            if previous is None:
                errors.append(f"{row.get('id')} revision {revision}: missing previous revision")
            elif supersedes != immutable_record_ref(previous, target_kind):
                errors.append(f"{row.get('id')} revision {revision}: supersedes is not the exact previous immutable TargetRef")
    return errors


def validate_association_identity(records: list[dict[str, Any]], label: str) -> list[str]:
    """Keep an append-only association identity attached to one claim identity."""
    errors: list[str] = []
    by_key = {(row.get("id"), row.get("record_revision")): row for row in records}
    for row in records:
        revision = row.get("record_revision")
        if not isinstance(revision, int) or revision <= 1:
            continue
        previous = by_key.get((row.get("id"), revision - 1))
        if previous is None:
            continue
        current_target = row.get("contribution_ref", {}).get("target_id")
        previous_target = previous.get("contribution_ref", {}).get("target_id")
        if current_target != previous_target:
            errors.append(f"{row.get('id')} revision {revision}: {label} association cannot switch ContributionClaim identity from {previous_target} to {current_target}")
    return errors


def validate_registry_records(claims: list[dict[str, Any]], calibrations: list[dict[str, Any]], support_records: list[dict[str, Any]], root: Path = ROOT) -> list[str]:
    """General cross-record validator; it does not assume the seven audit fixtures."""
    errors: list[str] = []
    target_schema = json.loads(TARGET_REF_SCHEMA.read_text())
    registry = Registry().with_resource(target_schema["$id"], Resource.from_contents(target_schema))
    schemas = {name: json.loads(path.read_text()) for name, path in SCHEMAS.items()}
    for label, rows in (("claim", claims), ("calibration", calibrations), ("support", support_records)):
        for index, row in enumerate(rows, 1):
            schema = schemas.get(row.get("schema"))
            if schema is None:
                errors.append(f"{label} {index}: unknown schema {row.get('schema')}")
                continue
            try:
                jsonschema.Draft202012Validator(schema, registry=registry, format_checker=jsonschema.FormatChecker()).validate(row)
            except jsonschema.ValidationError as exc:
                errors.append(f"{label} {index}: schema validation failed: {exc.message}")
    errors.extend(validate_manifest_discovery(root))
    all_records = claims + calibrations + support_records
    keys = [(row.get("id"), row.get("record_revision")) for row in all_records]
    if len(set(keys)) != len(keys):
        errors.append("duplicate record ID/revision in ContributionClaim vertical slice")
    global_ids: dict[tuple[str, Any], str] = {}
    for path in root.glob("Stabilizerness/**/*.jsonl"):
        for row in load_jsonl(path):
            identifier = row.get("id")
            if not identifier:
                continue
            revision = row.get("record_revision", row.get("revision"))
            key = (identifier, revision)
            relative = str(path.relative_to(root))
            if key in global_ids:
                errors.append(f"duplicate global record ID/revision {key}: {global_ids[key]} and {relative}")
            else:
                global_ids[key] = relative
    errors.extend(validate_supersedes(claims, "org.agtxiv.scientific_claim.contribution"))
    errors.extend(validate_supersedes(calibrations, "org.agtxiv.contribution_calibration"))
    errors.extend(validate_supersedes(support_records, "org.agtxiv.claim_support_association"))
    errors.extend(validate_association_identity(calibrations, "calibration"))
    errors.extend(validate_association_identity(support_records, "support"))

    claim_by_key = {(row.get("id"), row.get("record_revision")): row for row in claims}
    occurrence_ids: set[str] = set()
    source_paper: dict[str, str] = {}
    for claim in claims:
        identifier = claim.get("id", "<missing-id>")
        if not is_contribution_record(claim):
            errors.append(f"{identifier}: only explicit ContributionClaim profile records enter this registry collection")
        forbidden = nested_forbidden(claim)
        if forbidden:
            errors.append(f"{identifier}: embedded lifecycle/evidence/support fields: {forbidden}")
        try:
            if claim.get("semantic_content_hash") != semantic_hash(claim): errors.append(f"{identifier}: semantic_content_hash mismatch")
            if claim.get("artifact", {}).get("artifact_hash") != artifact_hash(claim): errors.append(f"{identifier}: artifact_hash mismatch")
            if claim.get("content_hash") != record_content_hash(claim): errors.append(f"{identifier}: content_hash mismatch")
            if claim.get("artifact", {}).get("serialization_profile") != profile_ref(): errors.append(f"{identifier}: serialization profile reference is not schema-pinned")
            for key in SET_VALUED_KEYS & claim.keys():
                if claim[key] != canonicalize(claim[key], key): errors.append(f"{identifier}: set-valued {key} is not in canonical order")
        except ValueError as exc:
            errors.append(f"{identifier}: canonicalization failed: {exc}")
        occurrences = claim.get("occurrences", [])
        if sum(item.get("occurrence_role") == "PRIMARY" for item in occurrences) != 1: errors.append(f"{identifier}: exactly one PRIMARY occurrence is required")
        if not any(item.get("occurrence_role") == "BODY_SUPPORT" for item in occurrences): errors.append(f"{identifier}: an explicit BODY_SUPPORT occurrence is required")
        facet_ids = [facet.get("facet_id") for facet in claim.get("facets", [])]
        if len(set(facet_ids)) != len(facet_ids): errors.append(f"{identifier}: facet IDs are not unique")
        for occurrence in occurrences:
            occurrence_id = occurrence.get("id")
            if occurrence_id in occurrence_ids:
                errors.append(f"duplicate occurrence ID across registry: {occurrence_id}")
            occurrence_ids.add(occurrence_id)
            source = occurrence.get("source_artifact", {})
            relative = Path(source.get("path", ""))
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(f"{identifier}: source artifact path must be workspace-relative"); continue
            previous_paper = source_paper.setdefault(str(relative), claim.get("paper_id"))
            if previous_paper != claim.get("paper_id"): errors.append(f"{identifier}: source artifact is associated with inconsistent paper IDs")
            path = root / relative
            if not path.is_file(): errors.append(f"{identifier}: missing source artifact {relative}"); continue
            if source.get("sha256") != file_hash(path): errors.append(f"{identifier}: source hash mismatch for {relative}")
            lines = path.read_text().splitlines(); start, end = occurrence.get("line_start", 0), occurrence.get("line_end", 0)
            if not (1 <= start <= end <= len(lines)): errors.append(f"{identifier}: invalid 1-based inclusive source range {start}-{end}")
            elif occurrence.get("source_text") != "\n".join(lines[start - 1:end]): errors.append(f"{identifier}: source text mismatch for {relative}:{start}-{end}")

    calibration_refs: set[tuple[str, int]] = set(); support_refs: set[tuple[str, int]] = set()
    for label, records, refs in (("calibration", calibrations, calibration_refs), ("support", support_records, support_refs)):
        for record in records:
            identifier = record.get("id", "<missing-id>")
            try:
                if record.get("content_hash") != external_content_hash(record): errors.append(f"{identifier}: content_hash mismatch")
                for key in SET_VALUED_KEYS & record.keys():
                    if record[key] != canonicalize(record[key], key): errors.append(f"{identifier}: set-valued {key} is not in canonical order")
            except ValueError as exc: errors.append(f"{identifier}: canonicalization failed: {exc}")
            ref = record.get("contribution_ref", {}); key = (ref.get("target_id"), ref.get("target_revision"))
            if record.get("record_revision") != ref.get("target_revision"):
                errors.append(f"{identifier}: {label} record revision must equal its ContributionClaim target revision")
            if key in refs: errors.append(f"duplicate {label} for ContributionClaim revision {key}")
            refs.add(key); claim = claim_by_key.get(key)
            if claim is None: errors.append(f"{identifier}: unresolved ContributionClaim TargetRef {key}")
            elif ref != contribution_target_ref(claim): errors.append(f"{identifier}: ContributionClaim TargetRef is not exact and canonical")
    claim_keys = set(claim_by_key)
    if calibration_refs != claim_keys: errors.append("every ContributionClaim revision must have exactly one calibration record")
    if support_refs != claim_keys: errors.append("every ContributionClaim revision must have exactly one support association")

    targets, target_errors = existing_support_targets(root); errors.extend(target_errors)
    calibration_by_ref = {(row["contribution_ref"]["target_id"], row["contribution_ref"]["target_revision"]): row for row in calibrations}
    for record in support_records:
        identifier = record.get("id", "<missing-id>"); cref = record.get("contribution_ref", {})
        claim = claim_by_key.get((cref.get("target_id"), cref.get("target_revision")))
        if claim is None: continue
        if record.get("navigation_basis_ref") != contribution_target_ref(claim, "/facets", artifact=False): errors.append(f"{identifier}: navigation basis must pin the immutable /facets decomposition")
        facets = [facet["facet_id"] for facet in claim.get("facets", [])]; outcomes = record.get("facet_outcomes", [])
        if [item.get("facet_id") for item in outcomes] != facets: errors.append(f"{identifier}: facet outcomes must cover every facet once in declared order")
        positive = {facet: 0 for facet in facets}
        for link in record.get("links", []):
            facet_id = link.get("facet_id")
            if facet_id not in positive: errors.append(f"{identifier}: link references unknown facet {facet_id}"); continue
            target_ref = link.get("target_ref", {}); kind = target_ref.get("target_kind")
            if kind not in SUPPORTED_TARGET_KINDS: errors.append(f"{identifier}: unsupported target kind in this slice: {kind}"); continue
            target = targets.get((target_ref.get("target_id"), target_ref.get("target_revision")))
            if target is None: errors.append(f"{identifier}: unresolved support target {target_ref.get('target_id')}"); continue
            if not target["id"].startswith(SUPPORTED_TARGET_KINDS[kind]): errors.append(f"{identifier}: target kind does not match target ID")
            elif target_ref != target_ref_for_existing(target, root): errors.append(f"{identifier}: support TargetRef is not exact and canonical for {target['id']}")
            relationship, coverage = link.get("relationship"), link.get("facet_coverage")
            if relationship == "TOPICAL_NAVIGATION_ONLY" and coverage != "NONE": errors.append(f"{identifier}: topical navigation links must have NONE facet coverage")
            elif relationship != "TOPICAL_NAVIGATION_ONLY": positive[facet_id] = max(positive[facet_id], COVERAGE_RANK.get(coverage, 0))
        expected_outcomes = [{"facet_id": facet, "coverage": next(name for name, rank in COVERAGE_RANK.items() if rank == positive[facet])} for facet in facets]
        if outcomes != expected_outcomes: errors.append(f"{identifier}: facet coverage outcomes do not aggregate from links")
        ranks = list(positive.values()); expected_total = "COMPLETE" if ranks and all(rank == 2 for rank in ranks) else "PARTIAL" if any(rank > 0 for rank in ranks) else "NONE"
        if record.get("provisional_facet_coverage") != expected_total: errors.append(f"{identifier}: provisional facet coverage does not aggregate from all facets")
        calibration = calibration_by_ref.get((cref.get("target_id"), cref.get("target_revision")))
        if calibration and calibration.get("calibration_stage") != "ATOMIC_AUDIT_COMPLETED": errors.append(f"{identifier}: publishing facet outcomes requires ATOMIC_AUDIT_COMPLETED")

    graph_paths = [root / "graph/claim-dependencies.json", *root.glob("Stabilizerness/GraphRegistry/**/*.json")]
    for path in graph_paths:
        if path.is_file(): errors.extend(validate_dependency_payload(json.loads(path.read_text()), str(path.relative_to(root))))
    return errors


def validate_fixture_audit(claims: list[dict[str, Any]], calibrations: list[dict[str, Any]], support_records: list[dict[str, Any]]) -> list[str]:
    """Seven-fixture source-strength guardrails, separate from registry validation."""
    errors: list[str] = []
    if len(claims) != 7 or len(calibrations) != 7 or len(support_records) != 7: errors.append("source audit requires exactly seven ContributionClaim fixtures and paired records")
    claim_by_id = {row.get("id"): row for row in claims}; support_by_id = {row.get("contribution_ref", {}).get("target_id"): row for row in support_records}; calibration_by_id = {row.get("contribution_ref", {}).get("target_id"): row for row in calibrations}
    expected_sources = {
        "arxiv:2607.26154v1": "Stabilizerness/arXiv-2607.26154v1/draft.tex",
        "arxiv:2602.18939v1": "Reference/Predicting magic from very few measurements/pra_version.tex",
        "arxiv:1307.7171v1": "Reference/The Resource Theory of Stabilizer Computation/stab_resource_theory_021.tex",
        "arxiv:1609.07488v2": "Reference/Application of a resource theory for magic states to fault-tolerant quantum computing/Robustness_main_appendix.tex",
        "arxiv:quant-ph/9705052v1": "Reference/Stabilizer Codes and Quantum Error Correction/Thesis.tex",
    }
    for claim in claims:
        expected_path = expected_sources.get(claim.get("paper_id"))
        if expected_path is None or any(occurrence.get("source_artifact", {}).get("path") != expected_path for occurrence in claim.get("occurrences", [])):
            errors.append(f"{claim.get('id')}: fixture paper/source artifact mapping is inconsistent")
    def require(claim_id: str, condition: bool, message: str) -> None:
        if claim_id in claim_by_id and not condition: errors.append(f"{claim_id}: {message}")
    perfect_id = "claim:contribution:2607-perfect-graph-closed-form"; perfect = claim_by_id.get(perfect_id, {}); perfect_scope = " ".join(perfect.get("scope_hints", [])).lower()
    require(perfect_id, "no active dependencies" in perfect_scope and "perfect frustration graph" in perfect_scope, "both no-active-dependency and perfect-graph hypotheses are mandatory")
    hard_id = "claim:contribution:2602-rsmp-np-hardness"; hard = claim_by_id.get(hard_id, {}); hard_text = (hard.get("normalized_statement", "") + " " + " ".join(hard.get("scope_hints", []))).lower()
    require(hard_id, "np-hard" in hard_text and "np-complete" not in hard.get("normalized_statement", "").lower(), "must state NP-hard, not NP-complete"); require(hard_id, "p != np" in hard_text, "the no-polynomial-time consequence must retain P != NP")
    wigner_id = "claim:contribution:1307-wigner-sum-negativity"; wigner = claim_by_id.get(wigner_id, {}); require(wigner_id, "odd prime" in " ".join(wigner.get("scope_hints", [])).lower(), "odd-prime-dimensional scope is mandatory")
    rom_id = "claim:contribution:1609-rom-monotone-estimator"; rom = claim_by_id.get(rom_id, {}); rom_text = (rom.get("normalized_statement", "") + " " + " ".join(rom.get("scope_hints", []))).lower()
    require(rom_id, "estimator" in rom_text and "quadratic" in rom_text, "must identify the specified estimator and quadratic sample bound"); require(rom_id, "equals classical simulation runtime" not in rom_text, "must not assert generic runtime equality")
    body_enriched_ids = (
        "claim:contribution:2602-vrep-algorithm-runtime",
        hard_id,
        wigner_id,
        rom_id,
    )
    for claim_id in body_enriched_ids:
        require(claim_id, calibration_by_id.get(claim_id, {}).get("primary_to_normalized_relation") == "PARTIAL_OVERLAP", "body-enriched facets require conservative PARTIAL_OVERLAP calibration")
    sign_id = "claim:contribution:2607-sign-relaxation-exactness"
    require(sign_id, calibration_by_id.get(sign_id, {}).get("primary_to_normalized_relation") == "BROADER_THAN", "the full primary source is BROADER_THAN the selected sign-relaxation claim facets")
    for claim_id in (wigner_id, rom_id):
        require(claim_id, calibration_by_id.get(claim_id, {}).get("body_to_normalized_relation") == "PARTIAL_OVERLAP", "grouped body spans omit normalized facets and require PARTIAL_OVERLAP calibration")
    thesis_id = "claim:contribution:9705052-thesis-overview"; thesis = claim_by_id.get(thesis_id, {}); thesis_support = support_by_id.get(thesis_id, {}); thesis_calibration = calibration_by_id.get(thesis_id, {})
    require(thesis_id, thesis.get("contribution_kind") == "org.agtxiv.contribution.synthesis" and thesis.get("source_characterization", {}).get("speech_act") == "org.agtxiv.speech_act.reviews", "thesis negative control cannot be promoted to a theorem contribution")
    require(thesis_id, thesis_support.get("provisional_facet_coverage") == "NONE" and all(link.get("relationship") == "TOPICAL_NAVIGATION_ONLY" and link.get("facet_coverage") == "NONE" for link in thesis_support.get("links", [])), "thesis MathClaimIR coexistence must remain non-dispositive topical navigation")
    require(thesis_id, thesis_calibration.get("body_to_normalized_relation") == "PARTIAL_OVERLAP", "thesis body span only partially overlaps the overview narrative")
    for claim_id in ("claim:contribution:2602-vrep-algorithm-runtime", wigner_id, rom_id, thesis_id): require(claim_id, support_by_id.get(claim_id, {}).get("provisional_facet_coverage") != "COMPLETE", "audit does not permit COMPLETE existing atomic support")
    return errors


def validate_records(claims: list[dict[str, Any]], calibrations: list[dict[str, Any]], support_records: list[dict[str, Any]], root: Path = ROOT) -> list[str]:
    return validate_registry_records(claims, calibrations, support_records, root) + validate_fixture_audit(claims, calibrations, support_records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--check", action="store_true", help="validate without modifying files (the default behavior)"); parser.parse_args()
    claims = load_jsonl(CLAIMS); calibrations = load_jsonl(CALIBRATIONS); support_records = load_jsonl(SUPPORT); errors = validate_records(claims, calibrations, support_records)
    for error in errors: print(error)
    print(f"contribution_claims={len(claims)} calibrations={len(calibrations)} support_associations={len(support_records)} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
