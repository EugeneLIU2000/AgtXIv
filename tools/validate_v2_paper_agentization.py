#!/usr/bin/env python3
"""Validate the additive AgtXIv V2 paper-agentization contract family."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = ROOT / "fixtures" / "v2-paper-agentization"
SCHEMA_DIR = ROOT / "schemas" / "v2"

SCHEMA_BY_DISCRIMINATOR = {
    "agtxiv.agentization-profile/2.0.0": "agentization-profile.schema.json",
    "agtxiv.inventory-scope/2.0.0": "inventory-scope.schema.json",
    "agtxiv.math-claim-ir/2.0.0": "math-claim-ir.schema.json",
    "agtxiv.assessment-record/2.0.0": "assessment-record.schema.json",
    "agtxiv.paper-agent-release-manifest/2.0.0": "paper-agent-release-manifest.schema.json",
    "agtxiv.release-audit-record/2.0.0": "release-audit-record.schema.json",
    "agtxiv.release-certification-record/2.0.0": "release-certification-record.schema.json",
    "agtxiv.formalization-request/2.0.0": "formalization-request.schema.json",
    "agtxiv.formalization-record/2.0.0": "formalization-record.schema.json",
    "agtxiv.knowledge-index-snapshot/2.0.0": "knowledge-index-snapshot.schema.json",
    "agtxiv.knowledge-ingestion-receipt/2.0.0": "knowledge-ingestion-receipt.schema.json",
    "agtxiv.query-resolution/2.0.0": "query-resolution.schema.json",
}

EXPECTED_REF_TYPES: dict[str, set[str]] = {
    "profile_ref": {"agtxiv.agentization-profile/2.0.0"},
    "scope_ref": {"agtxiv.inventory-scope/2.0.0"},
    "target_ref": {"agtxiv.math-claim-ir/2.0.0"},
    "request_ref": {"agtxiv.formalization-request/2.0.0"},
    "manifest_ref": {"agtxiv.paper-agent-release-manifest/2.0.0"},
    "source_release_ref": {"agtxiv.paper-agent-release-manifest/2.0.0"},
    "release_manifest_ref": {"agtxiv.paper-agent-release-manifest/2.0.0"},
    "audit_ref": {"agtxiv.release-audit-record/2.0.0"},
    "root_agent_audit_ref": {"agtxiv.release-audit-record/2.0.0"},
    "certificate_ref": {"agtxiv.release-certification-record/2.0.0"},
    "inventory_scope_ref": {"agtxiv.inventory-scope/2.0.0"},
    "inventory_scope_refs": {"agtxiv.inventory-scope/2.0.0"},
    "before_snapshot_ref": {"agtxiv.knowledge-index-snapshot/2.0.0"},
    "after_snapshot_ref": {"agtxiv.knowledge-index-snapshot/2.0.0"},
    "target_refs": {"agtxiv.inventory-scope/2.0.0", "agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0", "agtxiv.paper-agent-release-manifest/2.0.0"},
    "selected_assessment_refs": {"agtxiv.assessment-record/2.0.0"},
    "evidence_refs": {"agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0"},
    "assessment_refs": {"agtxiv.assessment-record/2.0.0"},
    "alignment_refs": {"agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0"},
    "relation_assessment_ref": {"agtxiv.assessment-record/2.0.0"},
    "release_certificate_ref": {"agtxiv.release-certification-record/2.0.0"},
    "knowledge_index_snapshot": {"agtxiv.knowledge-index-snapshot/2.0.0"},
    "record_ref": {"agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0", "agtxiv.assessment-record/2.0.0"},
    "returned_record_refs": {"agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0", "agtxiv.assessment-record/2.0.0"},
    "basis_refs": {"agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0", "agtxiv.assessment-record/2.0.0"},
}

MANDATORY_AUDIT_CHECKS = {
    "EXACT_INPUTS",
    "TOTAL_DISPOSITION_ACCOUNTING",
    "ARTIFACT_INTEGRITY",
    "PROFILE_CONFORMANCE",
    "ROLE_SEPARATION",
}

ENTRY_ADMISSION_BY_SCHEMA = {
    "agtxiv.math-claim-ir/2.0.0": {
        "artifact_class": "MATH_CLAIM_IR",
        "binding_field": "source_inventory_entry_id",
        "inventory_kind": "MATH_CLAIM",
        "entry_families": {"CONTRACT"},
    },
    "agtxiv.formalization-record/2.0.0": {
        "artifact_class": "FORMALIZATION_RECORD",
        "binding_field": "inventory_entry_id",
        "inventory_kind": "FORMALIZATION_TARGET",
        "entry_families": {"FORMAL_ARTIFACT"},
    },
    "agtxiv.assessment-record/2.0.0": {
        "artifact_class": "ASSESSMENT_RECORD",
        "binding_field": "source_inventory_entry_id",
        "inventory_kind": "MATH_CLAIM",
        "entry_families": {"ASSESSMENT"},
    },
}


def _normalized_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw_key, value in pairs:
        key = unicodedata.normalize("NFC", raw_key.replace("\r\n", "\n").replace("\r", "\n"))
        if key in result:
            raise ValueError(f"duplicate normalized JSON key: {key!r}")
        result[key] = value
    return result


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle, object_pairs_hook=_normalized_pairs)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def load_bundle(fixture_dir: Path = DEFAULT_FIXTURES) -> dict[str, dict[str, Any]]:
    return {path.name: _load_json(path) for path in sorted(fixture_dir.glob("*.json"))}


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for raw_key, child in value.items():
            key = _normalize(raw_key)
            if key in normalized:
                raise ValueError(f"duplicate normalized JSON key: {key!r}")
            normalized[key] = _normalize(child)
        return normalized
    if value is None or isinstance(value, (bool, int)):
        return value
    raise ValueError(f"unsupported canonical JSON value: {value!r}")


def canonical_json_bytes(value: Any) -> bytes:
    """Canonical UTF-8 JSON for the V2 integer-only subset of the V1 profile."""
    return json.dumps(_normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _projection(record: dict[str, Any], excluded: set[str]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in excluded}


def canonical_content_hash(record: dict[str, Any]) -> str:
    projection = _projection(record, {"content_hash"})
    return "sha256:" + hashlib.sha256(canonical_json_bytes(projection)).hexdigest()


def canonical_release_hash(manifest: dict[str, Any]) -> str:
    projection = _projection(manifest, {"content_hash", "release_hash"})
    return "sha256:" + hashlib.sha256(canonical_json_bytes(projection)).hexdigest()


def file_content_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def exact_ref(record: dict[str, Any]) -> dict[str, Any]:
    return {"id": record["id"], "record_revision": record["record_revision"], "content_hash": record["content_hash"]}


def _walk_keys(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, f"{path}.{key}"
            yield from _walk_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_keys(child, f"{path}[{index}]")


def _is_exact_ref(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    keys = set(value)
    return keys in ({"id", "record_revision", "content_hash"}, {"id", "record_revision", "content_hash", "component_path"})


def _walk_refs(value: Any, path: str = "$", parent_key: str | None = None) -> Iterable[tuple[dict[str, Any], str, str | None]]:
    if _is_exact_ref(value):
        yield value, path, parent_key
        return
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_refs(child, f"{path}.{key}", key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_refs(child, f"{path}[{index}]", parent_key)


def validate_bundle(bundle: dict[str, dict[str, Any]], fixture_dir: Path = DEFAULT_FIXTURES) -> list[str]:
    errors: list[str] = []
    schemas = {name: _load_json(SCHEMA_DIR / name) for name in SCHEMA_BY_DISCRIMINATOR.values()}
    schema_id_by_discriminator = {
        discriminator: schemas[name]["$id"] for discriminator, name in SCHEMA_BY_DISCRIMINATOR.items()
    }

    for name, schema in schemas.items():
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
        except jsonschema.SchemaError as exc:
            errors.append(f"schema {name}: {exc.message}")

    identity_index: dict[tuple[Any, Any], tuple[str, dict[str, Any]]] = {}
    for name, record in bundle.items():
        discriminator = record.get("schema")
        schema_name = SCHEMA_BY_DISCRIMINATOR.get(discriminator)
        if schema_name is None:
            errors.append(f"{name}: unknown V2 schema discriminator: {discriminator!r}")
        else:
            validator = jsonschema.Draft202012Validator(schemas[schema_name], format_checker=jsonschema.FormatChecker())
            for error in sorted(validator.iter_errors(record), key=lambda item: list(item.absolute_path)):
                location = "/".join(str(part) for part in error.absolute_path) or "$"
                errors.append(f"{name}:{location}: {error.message}")
        for key, location in _walk_keys(record):
            if key.lower() == "verified":
                errors.append(f"{name}:{location}: aggregate verified fields are forbidden")
        if "content_hash" in record:
            expected_hash = canonical_content_hash(record)
            if record.get("content_hash") != expected_hash:
                errors.append(f"{name}: stale content_hash; expected {expected_hash}")
        identity = (record.get("id"), record.get("record_revision"))
        if all(item is not None for item in identity):
            if identity in identity_index:
                errors.append(f"{name}: duplicate (id, revision) identity also used by {identity_index[identity][0]}: {identity!r}")
            else:
                identity_index[identity] = (name, record)

    def resolve(ref: dict[str, Any], context: str, parent_key: str | None) -> dict[str, Any] | None:
        identity = (ref.get("id"), ref.get("record_revision"))
        found = identity_index.get(identity)
        if found is None:
            errors.append(f"{context}: exact reference identity does not resolve: {identity!r}")
            return None
        _, target = found
        if ref.get("content_hash") != target.get("content_hash"):
            errors.append(f"{context}: exact reference has stale content_hash for {identity!r}")
        expected_types = EXPECTED_REF_TYPES.get(parent_key or "")
        if expected_types is None:
            errors.append(f"{context}: exact reference appears in an untyped field {parent_key!r}")
        elif target.get("schema") not in expected_types:
            errors.append(f"{context}: expected {sorted(expected_types)}, got {target.get('schema')!r}")
        return target

    for name, record in bundle.items():
        for ref, context, parent_key in _walk_refs(record, name):
            resolve(ref, context, parent_key)

    required_files = {
        "agentization-profile.json", "inventory-scope.json", "math-claim-ir.json",
        "paper-agent-release-manifest.json", "release-audit-record.json",
        "release-certification-record.json", "formalization-request.json",
        "formalization-record.json", "knowledge-index-snapshot-genesis.json",
        "knowledge-index-snapshot.json", "knowledge-ingestion-receipt.json",
        "query-resolution-package-backed.json", "query-resolution-provisional.json",
    }
    missing_files = sorted(required_files - bundle.keys())
    if missing_files:
        errors.append(f"fixture family missing required records: {', '.join(missing_files)}")
        return errors

    profile = bundle["agentization-profile.json"]
    scope = bundle["inventory-scope.json"]
    math_ir = bundle["math-claim-ir.json"]
    request = bundle["formalization-request.json"]
    result = bundle["formalization-record.json"]
    manifest = bundle["paper-agent-release-manifest.json"]
    audit = bundle["release-audit-record.json"]
    certificate = bundle["release-certification-record.json"]
    knowledge_genesis = bundle["knowledge-index-snapshot-genesis.json"]
    knowledge = bundle["knowledge-index-snapshot.json"]
    ingestion = bundle["knowledge-ingestion-receipt.json"]

    if scope.get("profile_ref") != exact_ref(profile):
        errors.append("scope does not bind the exact profile")
    if profile.get("paper_release") != scope.get("paper_release"):
        errors.append("profile and scope paper releases differ")
    paper_release = profile.get("paper_release", {})
    source_path = fixture_dir / str(paper_release.get("source_path", ""))
    if not source_path.is_file():
        errors.append(f"exact paper source path does not resolve: {paper_release.get('source_path')}")
    elif paper_release.get("source_hash") != file_content_hash(source_path):
        errors.append("exact paper source has stale byte hash")
    if manifest.get("profile_ref") != exact_ref(profile) or manifest.get("scope_ref") != exact_ref(scope):
        errors.append("manifest does not bind the exact profile and scope")

    scope_entries = scope.get("entries", [])
    scope_ids = [entry.get("entry_id") for entry in scope_entries]
    if len(scope_ids) != len(set(scope_ids)):
        errors.append("inventory scope contains duplicate entry IDs")
    allowed_kinds = set(profile.get("inventory_classes", []))
    invalid_kinds = sorted({entry.get("entry_kind") for entry in scope_entries if entry.get("entry_kind") not in allowed_kinds})
    if invalid_kinds:
        errors.append(f"inventory scope uses entry kinds not allowed by the profile: {invalid_kinds}")
    scope_by_id = {entry.get("entry_id"): entry for entry in scope_entries}
    for entry in scope_entries:
        component_path = fixture_dir / str(entry.get("source_component_path", ""))
        if not component_path.is_file():
            errors.append(f"scoped source component path does not resolve: {entry.get('source_component_path')}")
        elif entry.get("source_hash") != file_content_hash(component_path):
            errors.append(f"scoped source component has stale byte hash: {entry.get('entry_id')}")
    if math_ir.get("scope_ref") != exact_ref(scope) or math_ir.get("source_inventory_entry_id") not in scope_ids:
        errors.append("MathClaimIR does not bind an in-scope inventory entry and exact scope")

    target = request.get("target_ref", {})
    component_paths = {component.get("component_path") for component in math_ir.get("components", [])}
    if target.get("id") != math_ir.get("id") or target.get("record_revision") != math_ir.get("record_revision") or target.get("content_hash") != math_ir.get("content_hash") or target.get("component_path") not in component_paths:
        errors.append("formalization target/component does not resolve in the exact MathClaimIR")

    formal_forbidden = ("verification", "alignment", "acceptance", "admission", "promotion")
    for key, location in _walk_keys(result):
        if any(term in key.lower() for term in formal_forbidden):
            errors.append(f"formalization-record.json:{location}: FormalizationRecord cannot own {key}")
    for field in ("mode", "target_ref", "boundary", "environment"):
        if request.get(field) != result.get(field):
            errors.append(f"formalization request/result {field} mismatch")
    if result.get("request_ref") != exact_ref(request):
        errors.append("FormalizationRecord does not bind the exact request")
    boundary = request.get("boundary", {})
    boundary_entry = scope_by_id.get(boundary.get("inventory_entry_id"))
    if boundary_entry is None or boundary_entry.get("entry_kind") != "FORMALIZATION_TARGET":
        errors.append("formalization boundary does not bind an in-scope FORMALIZATION_TARGET entry")
    elif boundary.get("source_component_hash") != boundary_entry.get("source_hash"):
        errors.append("formalization boundary hash does not match its exact scoped source component")
    if result.get("inventory_entry_id") != boundary.get("inventory_entry_id"):
        errors.append("FormalizationRecord inventory entry does not match its request boundary")
    environment = request.get("environment", {})
    environment_path = fixture_dir / str(environment.get("descriptor_path", ""))
    if not environment_path.is_file():
        errors.append(f"formal environment descriptor path does not resolve: {environment.get('descriptor_path')}")
    else:
        if environment.get("descriptor_hash") != file_content_hash(environment_path):
            errors.append("formal environment descriptor has stale byte hash")
        try:
            environment_descriptor = tomllib.loads(environment_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"formal environment descriptor is not valid UTF-8 TOML: {exc}")
        else:
            required_environment_fields = {
                "environment_id", "lean_toolchain", "lean_commit", "mathlib_repository",
                "mathlib_revision", "project_path", "project_manifest_path",
                "project_manifest_hash", "build_command",
            }
            missing_environment_fields = sorted(required_environment_fields - environment_descriptor.keys())
            if missing_environment_fields:
                errors.append(f"formal environment descriptor is missing required fields: {missing_environment_fields}")
            if environment_descriptor.get("environment_id") != environment.get("environment_id"):
                errors.append("formal environment descriptor ID does not match the formalization request")
            project_manifest_path = ROOT / str(environment_descriptor.get("project_manifest_path", ""))
            if not project_manifest_path.is_file():
                errors.append("formal environment project manifest path does not resolve")
            elif environment_descriptor.get("project_manifest_hash") != file_content_hash(project_manifest_path):
                errors.append("formal environment project manifest has stale byte hash")

    requested_kinds = set(request.get("requested_artifacts", []))
    generated = result.get("generated_artifacts", [])
    generated_kinds = [artifact.get("artifact_kind") for artifact in generated]
    if len(generated_kinds) != len(set(generated_kinds)):
        errors.append("FormalizationRecord contains duplicate generated artifact kinds")
    for artifact in generated:
        path = fixture_dir / str(artifact.get("path", ""))
        if not path.is_file():
            errors.append(f"generated artifact path does not resolve: {artifact.get('path')}")
        elif artifact.get("content_hash") != file_content_hash(path):
            errors.append(f"generated artifact has stale byte hash: {artifact.get('path')}")
    outcome = result.get("generation_outcome")
    generated_set = set(generated_kinds)
    diagnostics = result.get("diagnostics", [])
    if outcome == "SUCCEEDED" and generated_set != requested_kinds:
        errors.append("successful FormalizationRecord must contain exactly every requested artifact kind")
    elif outcome == "PARTIAL" and not (generated_set and generated_set < requested_kinds and diagnostics):
        errors.append("partial FormalizationRecord requires a nonempty proper subset of requested artifacts and diagnostics")
    elif outcome == "FAILED" and (generated or not diagnostics):
        errors.append("failed FormalizationRecord requires no generated artifacts and nonempty diagnostics")

    ledger = manifest.get("disposition_ledger", [])
    ledger_ids = [row.get("inventory_entry_id") for row in ledger]
    if len(ledger_ids) != len(set(ledger_ids)):
        errors.append("disposition ledger contains duplicate entries")
    missing = sorted(set(scope_ids) - set(ledger_ids))
    outside = sorted(set(ledger_ids) - set(scope_ids))
    if missing:
        errors.append(f"disposition ledger is missing in-scope entries: {missing}")
    if outside:
        errors.append(f"disposition ledger contains out-of-scope entries: {outside}")
    if any(row.get("disposition") not in set(profile.get("allowed_dispositions", [])) for row in ledger):
        errors.append("disposition ledger uses a status not allowed by the profile")
    record_bound_entry: dict[tuple[Any, Any, Any], Any] = {}
    for candidate in bundle.values():
        admission = ENTRY_ADMISSION_BY_SCHEMA.get(candidate.get("schema"))
        if admission is not None:
            identity = (candidate.get("id"), candidate.get("record_revision"), candidate.get("content_hash"))
            record_bound_entry[identity] = candidate.get(admission["binding_field"])
    for row in ledger:
        for basis_ref in row.get("basis_refs", []):
            identity = (basis_ref.get("id"), basis_ref.get("record_revision"), basis_ref.get("content_hash"))
            bound_entry = record_bound_entry.get(identity)
            if bound_entry is not None and bound_entry != row.get("inventory_entry_id"):
                errors.append("disposition basis record is bound to a different inventory entry")

    required_classes = set(profile.get("required_artifact_classes", []))
    artifacts = manifest.get("artifacts", [])
    actual_classes = {artifact.get("artifact_class") for artifact in artifacts}
    if not required_classes <= actual_classes:
        errors.append(f"manifest is missing required artifact classes: {sorted(required_classes - actual_classes)}")
    manifest_records: dict[tuple[Any, Any, Any], dict[str, Any]] = {}
    byte_class_bindings = {
        "SOURCE_BYTES": {
            "artifact_id": f"source-release:{paper_release.get('paper_id')}:{paper_release.get('release_id')}",
            "path": paper_release.get("source_path"),
            "content_hash": paper_release.get("source_hash"),
            "media_type": "text/plain",
        },
        "FORMAL_ENVIRONMENT_DESCRIPTOR": {
            "artifact_id": environment.get("environment_id"),
            "path": environment.get("descriptor_path"),
            "content_hash": environment.get("descriptor_hash"),
            "media_type": "application/toml",
        },
    }
    for artifact in artifacts:
        path = fixture_dir / str(artifact.get("path", ""))
        if not path.is_file():
            errors.append(f"manifest artifact path does not resolve locally: {artifact.get('path')}")
            continue
        category = artifact.get("artifact_category")
        if category == "RECORD":
            identity = (artifact.get("artifact_id"), artifact.get("record_revision"))
            indexed = identity_index.get(identity)
            if indexed is None:
                errors.append(f"manifest record artifact identity does not resolve: {identity!r}")
                continue
            _, target_record = indexed
            try:
                path_record = _load_json(path)
            except (OSError, ValueError, json.JSONDecodeError):
                errors.append(f"manifest RECORD artifact is not a typed JSON record: {artifact.get('path')}")
                continue
            discriminator = target_record.get("schema")
            if path_record != target_record:
                errors.append(f"manifest RECORD path does not contain the exact indexed record: {artifact.get('path')}")
            if artifact.get("schema_uri") != schema_id_by_discriminator.get(discriminator):
                errors.append(f"manifest schema_uri mismatch for {artifact.get('path')}")
            if artifact.get("content_hash") != target_record.get("content_hash"):
                errors.append(f"manifest artifact content_hash mismatch for {artifact.get('path')}")
            admission = ENTRY_ADMISSION_BY_SCHEMA.get(discriminator)
            if admission is None or artifact.get("artifact_class") != admission["artifact_class"]:
                errors.append(f"manifest artifact_class mismatch for {artifact.get('path')}")
            record_identity = (target_record.get("id"), target_record.get("record_revision"), target_record.get("content_hash"))
            bound_entry = record_bound_entry.get(record_identity)
            scoped_entry = scope_by_id.get(bound_entry)
            if scoped_entry is None:
                errors.append(f"manifest record artifact is not bound to an exact in-scope inventory entry: {artifact.get('path')}")
            elif admission is None or scoped_entry.get("entry_kind") != admission["inventory_kind"]:
                errors.append(f"manifest record artifact has the wrong inventory entry kind: {artifact.get('path')}")
            if record_identity in manifest_records:
                errors.append(f"manifest contains a duplicate record artifact identity: {record_identity!r}")
            manifest_records[record_identity] = target_record
        elif category == "BYTE":
            expected_binding = byte_class_bindings.get(artifact.get("artifact_class"))
            if expected_binding is None:
                errors.append(f"manifest BYTE artifact uses an unsupported class: {artifact.get('artifact_class')}")
            elif any(artifact.get(field) != value for field, value in expected_binding.items()):
                errors.append(f"manifest byte artifact binding mismatch for {artifact.get('artifact_class')}")
            if artifact.get("content_hash") != file_content_hash(path):
                errors.append(f"manifest byte artifact has stale hash: {artifact.get('path')}")
        else:
            errors.append(f"manifest artifact has unknown category: {category!r}")

    expected_release_hash = canonical_release_hash(manifest)
    if manifest.get("release_hash") != expected_release_hash:
        errors.append(f"manifest has stale release_hash; expected {expected_release_hash}")

    coordinator = manifest.get("coordinator", {})
    root_agent = audit.get("auditor", {})
    certifier = certificate.get("certifier", {})
    if root_agent.get("role") != "V2_ROOT_AGENT":
        errors.append("ReleaseAuditRecord auditor must be the V2 Root Agent")
    if audit.get("coordinator") != coordinator or certificate.get("coordinator") != coordinator:
        errors.append("coordinator identity is not stable across manifest, audit, and certificate")
    if certificate.get("root_agent") != root_agent:
        errors.append("certificate Root Agent does not match the release audit")
    actor_ids = [coordinator.get("actor_id"), root_agent.get("actor_id"), certifier.get("actor_id")]
    if len(actor_ids) != len(set(actor_ids)):
        errors.append("coordinator, V2 Root Agent, and certifier identities must be pairwise distinct")

    mandatory_stages = [
        "SOURCE_INVENTORY", "PAPER_STRUCTURE", "CLAIM_INVENTORY_DECOMPOSITION",
        "MATHCLAIM_EXTRACTION_IR", "DEPENDENCY_INFERENCE_GRAPH",
        "FORMALIZATION_DISPOSITION", "FORMAL_VERIFICATION",
        "SOURCE_IR_FORMAL_ALIGNMENT", "RESIDUAL_NON_MATHEMATICAL_SEMANTICS",
        "ASSESSMENT_SELECTION",
    ]
    steps = audit.get("verification_steps", [])
    stage_order = [step.get("stage") for step in steps]
    sequences = [step.get("sequence") for step in steps]
    if stage_order != mandatory_stages or sequences != list(range(1, len(mandatory_stages) + 1)):
        errors.append("ReleaseAuditRecord has out-of-order, duplicate, or missing required audit stages")
    frontier = audit.get("unresolved_frontier", [])
    frontier_ids = [item.get("frontier_id") for item in frontier]
    if len(frontier_ids) != len(set(frontier_ids)):
        errors.append("ReleaseAuditRecord unresolved frontier contains duplicate IDs")
    frontier_by_id = {item.get("frontier_id"): item for item in frontier}
    required_frontier = set()
    for step in steps:
        ids = step.get("frontier_ids", [])
        if step.get("outcome") in {"UNKNOWN", "BLOCKED", "REFUTED"} and not ids:
            errors.append(f"audit stage {step.get('stage')} drops its unresolved outcome")
        required_frontier.update(ids)
        step_targets = {(ref.get("id"), ref.get("record_revision"), ref.get("content_hash")) for ref in step.get("target_refs", [])}
        for frontier_id in ids:
            item = frontier_by_id.get(frontier_id)
            frontier_targets = {(ref.get("id"), ref.get("record_revision"), ref.get("content_hash")) for ref in (item or {}).get("target_refs", [])}
            if (item is None or item.get("stage") != step.get("stage") or item.get("disposition") != step.get("outcome")
                    or frontier_targets != step_targets):
                errors.append(f"audit stage {step.get('stage')} does not bind an exact matching frontier entry and target set")
        for assessment_ref in step.get("selected_assessment_refs", []):
            found = identity_index.get((assessment_ref.get("id"), assessment_ref.get("record_revision")))
            assessment = found[1] if found else {}
            assessment_targets = {(ref.get("id"), ref.get("record_revision"), ref.get("content_hash")) for ref in assessment.get("target_refs", [])}
            if (assessment.get("assessment_kind") != "ROOT_STAGE_ASSESSMENT" or assessment_targets != step_targets or assessment.get("outcome") != step.get("outcome")):
                errors.append(f"audit stage {step.get('stage')} selects an incompatible AssessmentRecord")
    if required_frontier != set(frontier_ids):
        errors.append("ReleaseAuditRecord frontier is not exactly accounted by verification steps")
    recommendation = audit.get("release_recommendation", {})
    if set(recommendation.get("retained_frontier_ids", [])) != set(frontier_ids):
        errors.append("release recommendation drops UNKNOWN/BLOCKED/REFUTED frontier")
    if audit.get("manifest_ref") != exact_ref(manifest) or audit.get("profile_ref") != exact_ref(profile) or audit.get("scope_ref") != exact_ref(scope):
        errors.append("ReleaseAuditRecord exact input references mismatch")
    if certificate.get("manifest_ref") != exact_ref(manifest) or certificate.get("root_agent_audit_ref") != exact_ref(audit):
        errors.append("ReleaseCertificationRecord does not bind the exact Root Agent audit")
    expected_certifier_checks = ["ROOT_AGENT_AUDIT_RECOMMENDATION", "HASH_INTEGRITY", "POLICY_CONFORMANCE", "RELEASE_BINDING"]
    checks = certificate.get("mechanical_checks", [])
    if [row.get("check") for row in checks] != expected_certifier_checks:
        errors.append("ReleaseCertificationRecord mechanical checks are incomplete or out of order")
    release_hash = manifest.get("release_hash")
    if audit.get("audited_release_hash") != release_hash:
        errors.append("manifest and Root Agent audit release hashes differ")
    if certificate.get("decision") == "CERTIFIED":
        if recommendation.get("decision") != "RECOMMEND_PROFILE_RELEASE":
            errors.append("CERTIFIED requires the exact Root Agent recommendation RECOMMEND_PROFILE_RELEASE")
        if any(row.get("status") != "PASSED" for row in checks):
            errors.append("CERTIFIED requires every mechanical check to pass")
        if certificate.get("certified_release_hash") != release_hash or certificate.get("rejection_reasons") != []:
            errors.append("CERTIFIED release hash/rejection fields are inconsistent")
    elif certificate.get("decision") == "REJECTED":
        if not any(row.get("status") == "FAILED" for row in checks):
            errors.append("REJECTED requires at least one failed mechanical check")
        if certificate.get("certified_release_hash") is not None or not certificate.get("rejection_reasons"):
            errors.append("REJECTED certification fields are inconsistent")
    else:
        errors.append("ReleaseCertificationRecord has an unknown decision")

    expected_package_binding = {"manifest_ref": exact_ref(manifest), "certificate_ref": exact_ref(certificate), "root_agent_audit_ref": exact_ref(audit)}

    def resolve_exact_record(ref: Any, expected_schema: str, context: str) -> dict[str, Any] | None:
        if not isinstance(ref, dict):
            errors.append(f"{context}: exact package reference is missing")
            return None
        found = identity_index.get((ref.get("id"), ref.get("record_revision")))
        target = found[1] if found else None
        if target is None or ref != exact_ref(target) or target.get("schema") != expected_schema:
            errors.append(f"{context}: exact package reference does not resolve to {expected_schema}")
            return None
        return target

    def component_paths_for(record: dict[str, Any], inventory_entry_id: Any) -> set[Any]:
        schema = record.get("schema")
        if schema == "agtxiv.math-claim-ir/2.0.0":
            if record.get("source_inventory_entry_id") != inventory_entry_id:
                return set()
            return {component.get("component_path") for component in record.get("components", [])}
        if schema == "agtxiv.formalization-record/2.0.0":
            request_ref = record.get("request_ref", {})
            request_found = identity_index.get((request_ref.get("id"), request_ref.get("record_revision")))
            request_record = request_found[1] if request_found and request_ref == exact_ref(request_found[1]) else None
            if (record.get("inventory_entry_id") != inventory_entry_id
                    or record.get("boundary", {}).get("inventory_entry_id") != inventory_entry_id
                    or request_record is None
                    or request_record.get("schema") != "agtxiv.formalization-request/2.0.0"
                    or request_record.get("target_ref") != record.get("target_ref")
                    or request_record.get("boundary") != record.get("boundary")):
                return set()
            target_ref = record.get("target_ref", {})
            found = identity_index.get((target_ref.get("id"), target_ref.get("record_revision")))
            target = found[1] if found else None
            if (target is None or target.get("schema") != "agtxiv.math-claim-ir/2.0.0"
                    or {key: target_ref.get(key) for key in exact_ref(target)} != exact_ref(target)
                    or target_ref.get("component_path") not in {
                        component.get("component_path") for component in target.get("components", [])}):
                return set()
            return {target_ref.get("component_path")}
        if schema == "agtxiv.assessment-record/2.0.0":
            if record.get("source_inventory_entry_id") != inventory_entry_id:
                return set()
            paths: set[Any] = set()
            for target_ref in record.get("target_refs", []):
                found = identity_index.get((target_ref.get("id"), target_ref.get("record_revision")))
                target = found[1] if found and target_ref == exact_ref(found[1]) else None
                if target is not None:
                    paths.update(component_paths_for(target, inventory_entry_id))
            return paths
        return set()

    def validate_entry_package(
        entry: dict[str, Any], snapshot: dict[str, Any], context: str
    ) -> tuple[Any, Any] | None:
        provenance = entry.get("provenance", {})
        manifest_record = resolve_exact_record(
            provenance.get("manifest_ref"), "agtxiv.paper-agent-release-manifest/2.0.0", context
        )
        certificate_record = resolve_exact_record(
            provenance.get("certificate_ref"), "agtxiv.release-certification-record/2.0.0", context
        )
        audit_record = resolve_exact_record(
            provenance.get("root_agent_audit_ref"), "agtxiv.release-audit-record/2.0.0", context
        )
        scope_record = resolve_exact_record(
            provenance.get("inventory_scope_ref"), "agtxiv.inventory-scope/2.0.0", context
        )
        if None in (manifest_record, certificate_record, audit_record, scope_record):
            return None
        package_binding = {
            "manifest_ref": exact_ref(manifest_record),
            "certificate_ref": exact_ref(certificate_record),
            "root_agent_audit_ref": exact_ref(audit_record),
        }
        if package_binding not in snapshot.get("package_bindings", []):
            errors.append(f"{context}: exact package binding is absent from its knowledge snapshot")
        if exact_ref(scope_record) not in snapshot.get("inventory_scope_refs", []):
            errors.append(f"{context}: exact inventory scope binding is absent from its knowledge snapshot")
        profile_record = resolve_exact_record(
            manifest_record.get("profile_ref"), "agtxiv.agentization-profile/2.0.0", context
        )
        chain_ok = (
            manifest_record.get("scope_ref") == exact_ref(scope_record)
            and audit_record.get("manifest_ref") == exact_ref(manifest_record)
            and audit_record.get("profile_ref") == (exact_ref(profile_record) if profile_record else None)
            and audit_record.get("scope_ref") == exact_ref(scope_record)
            and manifest_record.get("release_hash") == canonical_release_hash(manifest_record)
            and audit_record.get("audited_release_hash") == manifest_record.get("release_hash")
            and certificate_record.get("manifest_ref") == exact_ref(manifest_record)
            and certificate_record.get("root_agent_audit_ref") == exact_ref(audit_record)
            and certificate_record.get("decision") == "CERTIFIED"
            and certificate_record.get("certified_release_hash") == manifest_record.get("release_hash")
            and profile_record is not None
            and scope_record.get("profile_ref") == exact_ref(profile_record)
            and scope_record.get("paper_release") == profile_record.get("paper_release")
        )
        if not chain_ok:
            errors.append(f"{context}: manifest/certificate/audit/scope refs do not form one exact certified package chain")
            return None
        release = scope_record.get("paper_release", {})
        package_source_path = fixture_dir / str(release.get("source_path", ""))
        if (not package_source_path.is_file()
                or release.get("source_hash") != file_content_hash(package_source_path)):
            errors.append(f"{context}: resolved package source bytes/path do not match the exact scope")
        inventory_entry_id = entry.get("component", {}).get("inventory_entry_id")
        scoped_entry = next(
            (item for item in scope_record.get("entries", []) if item.get("entry_id") == inventory_entry_id), None
        )
        scoped_source_path = fixture_dir / str((scoped_entry or {}).get("source_component_path", ""))
        if (scoped_entry is None or not scoped_source_path.is_file()
                or scoped_entry.get("source_hash") != file_content_hash(scoped_source_path)):
            errors.append(f"{context}: resolved inventory source component bytes/path are not exact")
        ref = entry.get("record_ref", {})
        found = identity_index.get((ref.get("id"), ref.get("record_revision")))
        record = found[1] if found and ref == exact_ref(found[1]) else None
        if record is None or record.get("schema") not in EXPECTED_REF_TYPES["record_ref"]:
            errors.append(f"{context}: exact knowledge record reference does not resolve")
            record = None
        admission = ENTRY_ADMISSION_BY_SCHEMA.get((record or {}).get("schema"))
        record_artifact = next((artifact for artifact in manifest_record.get("artifacts", [])
            if artifact.get("artifact_category") == "RECORD"
            and artifact.get("artifact_id") == ref.get("id")
            and artifact.get("record_revision") == ref.get("record_revision")
            and artifact.get("content_hash") == ref.get("content_hash")), None)
        if (record is None or admission is None or scoped_entry is None
                or scoped_entry.get("entry_kind") != admission["inventory_kind"]
                or record.get(admission["binding_field"]) != inventory_entry_id
                or record_artifact is None
                or record_artifact.get("artifact_class") != admission["artifact_class"]
                or record_artifact.get("schema_uri") != schema_id_by_discriminator.get(record.get("schema"))):
            errors.append(f"{context}: record/inventory binding is not an exact artifact of its resolved package")
        component_path = entry.get("component", {}).get("component_path")
        if record is None or component_path not in component_paths_for(record, inventory_entry_id):
            errors.append(f"{context}: component_path does not resolve to the record-family-specific exact component boundary")
        source = provenance.get("source", {})
        expected_source = {
            "paper_id": release.get("paper_id"),
            "release_id": release.get("release_id"),
            "source_uri": release.get("source_uri"),
            "source_hash": release.get("source_hash"),
            "source_locator": (scoped_entry or {}).get("source_locator"),
            "source_component_path": (scoped_entry or {}).get("source_component_path"),
            "source_component_hash": (scoped_entry or {}).get("source_hash"),
        }
        if source != expected_source:
            errors.append(f"{context}: source provenance does not match its resolved exact manifest/scope chain")
        return release.get("paper_id"), release.get("release_id")

    before_entries_by_id = {entry.get("entry_id"): entry for entry in knowledge_genesis.get("entries", [])}
    expected_packages = {canonical_json_bytes(value) for value in knowledge_genesis.get("package_bindings", [])}
    expected_scopes = {canonical_json_bytes(value) for value in knowledge_genesis.get("inventory_scope_refs", [])}
    if any(entry.get("entry_id") not in before_entries_by_id for entry in knowledge.get("entries", [])):
        expected_packages.add(canonical_json_bytes(expected_package_binding))
        expected_scopes.add(canonical_json_bytes(exact_ref(scope)))
    if ({canonical_json_bytes(value) for value in knowledge.get("package_bindings", [])} != expected_packages
            or {canonical_json_bytes(value) for value in knowledge.get("inventory_scope_refs", [])} != expected_scopes):
        errors.append("knowledge index does not preserve prior bindings plus the exact manifest/certificate/Root Agent audit/inventory")
    if certificate.get("decision") != "CERTIFIED":
        errors.append("knowledge index cannot bind a rejected release certification")
    ledger_by_id = {row.get("inventory_entry_id"): row for row in ledger}
    for index, entry in enumerate(knowledge_genesis.get("entries", [])):
        validate_entry_package(entry, knowledge_genesis, f"genesis knowledge index entry {index}")

    admitted_refs: set[tuple[Any, Any, Any]] = set()
    admitted_pairs: set[tuple[Any, tuple[Any, Any, Any]]] = set()
    knowledge_entry_ids: set[Any] = set()
    derived_release_by_entry_id: dict[Any, tuple[Any, Any] | None] = {}
    entry_ids = [entry.get("entry_id") for entry in knowledge.get("entries", [])]
    if len(entry_ids) != len(set(entry_ids)):
        errors.append("knowledge index contains duplicate entry IDs")
    for index, entry in enumerate(knowledge.get("entries", [])):
        ref = entry.get("record_ref", {})
        identity = (ref.get("id"), ref.get("record_revision"), ref.get("content_hash"))
        component = entry.get("component", {})
        inventory_entry_id = component.get("inventory_entry_id")
        pair = (inventory_entry_id, identity)
        if not entry.get("domain_id") or entry.get("domain_id") != knowledge.get("domain_id"):
            errors.append(f"knowledge index entry {index} lacks the exact domain binding")
        if identity in admitted_refs:
            errors.append(f"knowledge index contains a duplicate record admission: {identity!r}")
        if pair in admitted_pairs:
            errors.append(f"knowledge index contains a duplicate inventory-entry/record pair: {pair!r}")
        found = identity_index.get((ref.get("id"), ref.get("record_revision")))
        record = found[1] if found else {}
        admission = ENTRY_ADMISSION_BY_SCHEMA.get(record.get("schema"))
        if admission is None or entry.get("entry_family") not in admission["entry_families"]:
            errors.append(f"knowledge index entry {index} has an incompatible record schema/artifact class/component/entry_family")
        is_preserved = before_entries_by_id.get(entry.get("entry_id")) == entry
        derived_release_by_entry_id[entry.get("entry_id")] = validate_entry_package(
            entry, knowledge, f"knowledge index entry {index}"
        )
        if not is_preserved:
            if identity not in manifest_records:
                errors.append(f"knowledge index entry {index} is not an exact manifest artifact")
            bound_entry = record_bound_entry.get(identity)
            if bound_entry != inventory_entry_id:
                errors.append(f"knowledge index entry {index} inventory entry does not match the admitted record binding")
            row = ledger_by_id.get(inventory_entry_id)
            if row is None or row.get("disposition") != entry.get("admission_status") or entry.get("admission_status") not in {"ADMITTED", "CONDITIONAL"}:
                errors.append(f"knowledge index entry {index} does not match an admissible ledger disposition")
        provenance = entry.get("provenance", {})
        axes = entry.get("axes", {})
        if set(axes) != {"source_assertion", "formal_verification", "scientific_acceptance"}:
            errors.append(f"knowledge index entry {index} lacks independent status axes")
        else:
            axis_contracts = {
                "source_assertion": {
                    "SOURCE_ALIGNMENT_ASSESSED": ("SOURCE_ALIGNMENT", "SOURCE_ASSERTION", "ALIGNED"),
                    "SOURCE_ALIGNMENT_REJECTED": ("SOURCE_ALIGNMENT", "SOURCE_ASSERTION", "MISALIGNED"),
                },
                "formal_verification": {
                    "KERNEL_CHECKED": ("FORMAL_VERIFICATION", "FORMAL_VERIFICATION", "KERNEL_CHECKED"),
                    "KERNEL_REJECTED": ("FORMAL_VERIFICATION", "FORMAL_VERIFICATION", "KERNEL_REJECTED"),
                },
                "scientific_acceptance": {
                    "ACCEPTED": ("SCIENTIFIC_ACCEPTANCE", "SCIENTIFIC_ACCEPTANCE", "ACCEPTED"),
                    "REJECTED": ("SCIENTIFIC_ACCEPTANCE", "SCIENTIFIC_ACCEPTANCE", "REJECTED"),
                },
            }
            expected_target = {(ref.get("id"), ref.get("record_revision"), ref.get("content_hash"))}
            for axis_name, axis in axes.items():
                status = axis.get("status")
                assessment_refs = axis.get("assessment_refs", [])
                contract = axis_contracts[axis_name].get(status)
                if contract is None:
                    if assessment_refs:
                        errors.append(f"knowledge index entry {index} {axis_name} unassessed status carries assessment refs")
                    continue
                if not assessment_refs:
                    errors.append(f"knowledge index entry {index} assessed {axis_name} status lacks typed AssessmentRecord")
                for assessment_ref in assessment_refs:
                    found = identity_index.get((assessment_ref.get("id"), assessment_ref.get("record_revision")))
                    assessment = found[1] if found else {}
                    targets = {(target.get("id"), target.get("record_revision"), target.get("content_hash")) for target in assessment.get("target_refs", [])}
                    if ((assessment.get("assessment_kind"), assessment.get("axis"), assessment.get("outcome")) != contract
                            or targets != expected_target):
                        errors.append(f"knowledge index entry {index} {axis_name} uses an incompatible AssessmentRecord")
        if entry.get("entry_family") == "FORMAL_ARTIFACT" and entry.get("formal_environment") != manifest_records.get(identity, {}).get("environment"):
            errors.append(f"knowledge index entry {index} lacks its exact formal environment")
        if not entry.get("scope_assumptions") or not provenance or not entry.get("entry_family"):
            errors.append(f"knowledge index entry {index} lacks family/provenance/scope")
        admitted_refs.add(identity); admitted_pairs.add(pair); knowledge_entry_ids.add(entry.get("entry_id"))
    entries_by_id = {entry.get("entry_id"): entry for entry in knowledge.get("entries", [])}
    relations = knowledge.get("cross_paper_relations", [])
    relation_ids = [relation.get("relation_id") for relation in relations]
    if len(relation_ids) != len(set(relation_ids)):
        errors.append("cross-paper relations contain duplicate relation IDs")
    for relation in relations:
        left_id = relation.get("left_entry_id")
        right_id = relation.get("right_entry_id")
        left = entries_by_id.get(left_id)
        right = entries_by_id.get(right_id)
        if left_id == right_id:
            errors.append("cross-paper relation endpoints must be distinct")
        if left is None or right is None:
            errors.append("cross-paper relation endpoints are absent from the exact snapshot")
            continue
        left_release = derived_release_by_entry_id.get(left_id)
        right_release = derived_release_by_entry_id.get(right_id)
        if left_release is None or right_release is None:
            errors.append("cross-paper relation endpoints must have resolvable exact package provenance")
        elif left_release == right_release:
            errors.append("cross-paper relation endpoints must identify different paper releases derived from exact package provenance")
        assessment_ref = relation.get("relation_assessment_ref", {})
        found = identity_index.get((assessment_ref.get("id"), assessment_ref.get("record_revision")))
        assessment = found[1] if found else {}
        expected_targets = {
            (left.get("record_ref", {}).get("id"), left.get("record_ref", {}).get("record_revision"), left.get("record_ref", {}).get("content_hash")),
            (right.get("record_ref", {}).get("id"), right.get("record_ref", {}).get("record_revision"), right.get("record_ref", {}).get("content_hash")),
        }
        assessment_targets = {(target.get("id"), target.get("record_revision"), target.get("content_hash")) for target in assessment.get("target_refs", [])}
        if (assessment.get("assessment_kind") != "CROSS_PAPER_RELATION" or assessment.get("relation") != relation.get("relation")
                or assessment.get("left_entry_id") != relation.get("left_entry_id") or assessment.get("right_entry_id") != relation.get("right_entry_id")
                or assessment.get("outcome") != "RELATION_CONFIRMED" or assessment_targets != expected_targets):
            errors.append("cross-paper relation lacks a compatible exact AssessmentRecord")
    view_policy = knowledge.get("view_policy", {})
    if view_policy.get("conflict_behavior") != "PRESERVE_ALL_ASSESSED_CONFLICTS":
        errors.append("knowledge query policy suppresses conflicts")

    if (ingestion.get("profile_ref") != exact_ref(profile) or ingestion.get("manifest_ref") != exact_ref(manifest)
            or ingestion.get("certificate_ref") != exact_ref(certificate) or ingestion.get("root_agent_audit_ref") != exact_ref(audit)):
        errors.append("knowledge ingestion is not bound to the exact profile/manifest/certificate/audit transaction")
    before_found = identity_index.get((ingestion.get("before_snapshot_ref", {}).get("id"), ingestion.get("before_snapshot_ref", {}).get("record_revision")))
    after_found = identity_index.get((ingestion.get("after_snapshot_ref", {}).get("id"), ingestion.get("after_snapshot_ref", {}).get("record_revision")))
    before_snapshot = before_found[1] if before_found and before_found[1].get("schema") == "agtxiv.knowledge-index-snapshot/2.0.0" else None
    after_snapshot = after_found[1] if after_found and after_found[1].get("schema") == "agtxiv.knowledge-index-snapshot/2.0.0" else None
    if before_snapshot is None or after_snapshot is None:
        errors.append("knowledge ingestion before/after snapshots do not resolve exactly")
    elif (ingestion.get("before_snapshot_ref") != exact_ref(before_snapshot) or ingestion.get("after_snapshot_ref") != exact_ref(after_snapshot)):
        errors.append("knowledge ingestion before/after snapshot hashes are not exact")
    if ingestion.get("domain_id") != (after_snapshot or {}).get("domain_id") or ingestion.get("policy", {}).get("atomicity") != "REQUIRED" or ingestion.get("policy", {}).get("partial_mutation") != "FORBIDDEN":
        errors.append("knowledge ingestion weakens domain or atomicity policy")

    candidate_set = ingestion.get("candidate_set", [])
    candidate_groups = [ingestion.get("accepted_candidates", []), ingestion.get("rejected_candidates", []), ingestion.get("blocked_candidates", [])]
    universe_ids = [candidate.get("candidate_id") for candidate in candidate_set]
    candidate_ids = [candidate.get("candidate_id") for group in candidate_groups for candidate in group]
    if len(universe_ids) != len(set(universe_ids)):
        errors.append("knowledge ingestion candidate_set contains duplicate candidate IDs")
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("knowledge ingestion candidate IDs must be globally unique and disjoint")

    def candidate_base(candidate):
        return {key: candidate.get(key) for key in ("candidate_id", "entry_family", "record_ref", "inventory_entry_id")}

    universe = {candidate.get("candidate_id"): candidate for candidate in candidate_set}
    dispositions = {candidate.get("candidate_id"): candidate_base(candidate) for group in candidate_groups for candidate in group}
    if set(dispositions) != set(universe) or any(dispositions[candidate_id] != universe[candidate_id] for candidate_id in set(dispositions) & set(universe)):
        errors.append("knowledge ingestion dispositions are not a disjoint exhaustive partition of the exact candidate_set")
    for candidate in candidate_set:
        ref = candidate.get("record_ref", {})
        found = identity_index.get((ref.get("id"), ref.get("record_revision")))
        record = found[1] if found else {}
        admission = ENTRY_ADMISSION_BY_SCHEMA.get(record.get("schema"))
        identity = (ref.get("id"), ref.get("record_revision"), ref.get("content_hash"))
        if (admission is None or candidate.get("entry_family") not in admission["entry_families"]
                or candidate.get("inventory_entry_id") != record_bound_entry.get(identity)
                or identity not in manifest_records):
            errors.append(f"knowledge ingestion candidate {candidate.get('candidate_id')} has an incompatible exact record/inventory/family binding")
    accepted = ingestion.get("accepted_candidates", [])
    if ingestion.get("outcome") == "ABORTED":
        if accepted:
            errors.append("ABORTED knowledge ingestion cannot contain accepted additions")
        if ingestion.get("after_snapshot_ref") != ingestion.get("before_snapshot_ref"):
            errors.append("ABORTED knowledge ingestion must bind the identical before/after snapshot")
    elif ingestion.get("outcome") == "COMMITTED" and before_snapshot is not None and after_snapshot is not None:
        if before_snapshot.get("domain_id") != after_snapshot.get("domain_id") or before_snapshot.get("view_policy") != after_snapshot.get("view_policy"):
            errors.append("knowledge ingestion changed the immutable domain/view policy")
        before_entries = {entry.get("entry_id"): entry for entry in before_snapshot.get("entries", [])}
        after_entries = {entry.get("entry_id"): entry for entry in after_snapshot.get("entries", [])}
        if any(after_entries.get(entry_id) != entry for entry_id, entry in before_entries.items()):
            errors.append("knowledge ingestion removed or changed a pre-existing entry")
        added_ids = set(after_entries) - set(before_entries)
        accepted_ids = {candidate.get("knowledge_entry_id") for candidate in accepted}
        if added_ids != accepted_ids:
            errors.append("knowledge ingestion performed non-atomic/partial entry mutation under atomic policy")
        for candidate in accepted:
            entry = after_entries.get(candidate.get("knowledge_entry_id"))
            if (entry is None or candidate.get("record_ref") != entry.get("record_ref")
                    or candidate.get("inventory_entry_id") != entry.get("component", {}).get("inventory_entry_id")
                    or candidate.get("entry_family") != entry.get("entry_family")):
                errors.append("accepted ingestion candidate does not bind its exact admitted addition")
        def canonical_inventory(values):
            return {canonical_json_bytes(value) for value in values}
        before_packages = canonical_inventory(before_snapshot.get("package_bindings", []))
        before_scopes = canonical_inventory(before_snapshot.get("inventory_scope_refs", []))
        expected_packages = set(before_packages)
        expected_scopes = set(before_scopes)
        if accepted:
            expected_packages.add(canonical_json_bytes(expected_package_binding))
            expected_scopes.add(canonical_json_bytes(exact_ref(scope)))
        if canonical_inventory(after_snapshot.get("package_bindings", [])) != expected_packages:
            errors.append("knowledge ingestion did not preserve package bindings plus the exact accepted package")
        if canonical_inventory(after_snapshot.get("inventory_scope_refs", [])) != expected_scopes:
            errors.append("knowledge ingestion did not preserve scope refs plus the exact accepted scope")
        if after_snapshot.get("cross_paper_relations") != before_snapshot.get("cross_paper_relations"):
            errors.append("knowledge ingestion changed pre-existing relations outside accepted entry additions")
        if after_snapshot.get("environment_compatibility_receipts") != before_snapshot.get("environment_compatibility_receipts"):
            errors.append("knowledge ingestion changed pre-existing environment receipts outside accepted entry additions")

    for name, query in bundle.items():
        if query.get("schema") != "agtxiv.query-resolution/2.0.0":
            continue
        if query.get("mode") == "PACKAGE_BACKED":
            forbidden_query_fields = {"mutation", "publication"} & query.keys()
            if forbidden_query_fields:
                errors.append(f"{name}: mutation/publication fields are not allowed: {sorted(forbidden_query_fields)}")
            if query.get("release_manifest_ref") != exact_ref(manifest) or query.get("release_certificate_ref") != exact_ref(certificate) or query.get("knowledge_index_snapshot") != exact_ref(knowledge):
                errors.append(f"{name}: package-backed query does not bind the exact certified release and index")
            returned_identities = {(ref.get("id"), ref.get("record_revision"), ref.get("content_hash")) for ref in query.get("returned_record_refs", [])}
            for identity in returned_identities:
                if identity not in admitted_refs:
                    errors.append(f"{name}: returned record is not admitted by the exact knowledge index")
            relation_ids = [relation.get("relation_id") for relation in knowledge.get("cross_paper_relations", [])]
            if Counter(query.get("returned_relation_ids", [])) != Counter(relation_ids):
                errors.append(f"{name}: relation/conflict closure omits, duplicates, or invents snapshot relations")
            closure_relations = {"CONFLICTING", "INCOMPARABLE", "CORRECTS", "QUALIFIES", "REFUTES"}
            entries_by_id = {entry.get("entry_id"): entry for entry in knowledge.get("entries", [])}
            for relation in knowledge.get("cross_paper_relations", []):
                if relation.get("relation") not in closure_relations:
                    continue
                endpoint_identities = set()
                for endpoint in (relation.get("left_entry_id"), relation.get("right_entry_id")):
                    endpoint_ref = entries_by_id.get(endpoint, {}).get("record_ref", {})
                    endpoint_identities.add((endpoint_ref.get("id"), endpoint_ref.get("record_revision"), endpoint_ref.get("content_hash")))
                if not endpoint_identities <= returned_identities:
                    errors.append(f"{name}: conflict-preserving closure drops a relation endpoint record")
        elif query.get("mode") == "PROVISIONAL_FAST_PATH":
            trigger = query.get("agentization_trigger")
            if not isinstance(trigger, dict):
                errors.append(f"{name}: provisional query is missing its agentization trigger")
            else:
                if trigger.get("profile_ref") != exact_ref(profile) or trigger.get("scope_ref") != exact_ref(scope):
                    errors.append(f"{name}: agentization trigger does not bind the exact profile and scope")
                if trigger.get("scope_control") != "QUERY_INDEPENDENT":
                    errors.append(f"{name}: agentization trigger permits query-controlled scope")
            effects = query.get("canonical_effects", {})
            if any(value != "FORBIDDEN" for value in effects.values()):
                errors.append(f"{name}: provisional query attempts a canonical effect")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_dir", nargs="?", type=Path, default=DEFAULT_FIXTURES)
    args = parser.parse_args(argv)
    try:
        bundle = load_bundle(args.fixture_dir)
        errors = validate_bundle(bundle, args.fixture_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"V2 paper-agentization validation failed: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("V2 paper-agentization validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"V2 paper-agentization validation passed ({len(bundle)} JSON records, {len(SCHEMA_BY_DISCRIMINATOR)} schemas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
