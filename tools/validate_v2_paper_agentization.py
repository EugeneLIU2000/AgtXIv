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
    "agtxiv.paper-agent-release-manifest/2.0.0": "paper-agent-release-manifest.schema.json",
    "agtxiv.release-audit-record/2.0.0": "release-audit-record.schema.json",
    "agtxiv.release-certification-record/2.0.0": "release-certification-record.schema.json",
    "agtxiv.formalization-request/2.0.0": "formalization-request.schema.json",
    "agtxiv.formalization-record/2.0.0": "formalization-record.schema.json",
    "agtxiv.knowledge-index-snapshot/2.0.0": "knowledge-index-snapshot.schema.json",
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
    "release_certificate_ref": {"agtxiv.release-certification-record/2.0.0"},
    "knowledge_index_snapshot": {"agtxiv.knowledge-index-snapshot/2.0.0"},
    "record_ref": {"agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0"},
    "returned_record_refs": {"agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0"},
    "basis_refs": {"agtxiv.math-claim-ir/2.0.0", "agtxiv.formalization-record/2.0.0"},
}

MANDATORY_AUDIT_CHECKS = {
    "EXACT_INPUTS",
    "TOTAL_DISPOSITION_ACCOUNTING",
    "ARTIFACT_INTEGRITY",
    "PROFILE_CONFORMANCE",
    "ROLE_SEPARATION",
}

ARTIFACT_CLASS_BY_SCHEMA = {
    "agtxiv.math-claim-ir/2.0.0": "MATH_CLAIM_IR",
    "agtxiv.formalization-record/2.0.0": "FORMALIZATION_RECORD",
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
        if all(identity):
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
        "formalization-record.json", "knowledge-index-snapshot.json",
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
    knowledge = bundle["knowledge-index-snapshot.json"]

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
    inventory_binding_field = {
        "agtxiv.math-claim-ir/2.0.0": "source_inventory_entry_id",
        "agtxiv.formalization-record/2.0.0": "inventory_entry_id",
    }
    expected_entry_kind = {
        "agtxiv.math-claim-ir/2.0.0": "MATH_CLAIM",
        "agtxiv.formalization-record/2.0.0": "FORMALIZATION_TARGET",
    }
    record_bound_entry: dict[tuple[Any, Any, Any], Any] = {}
    for candidate in bundle.values():
        binding_field = inventory_binding_field.get(candidate.get("schema"))
        if binding_field is not None:
            identity = (candidate.get("id"), candidate.get("record_revision"), candidate.get("content_hash"))
            record_bound_entry[identity] = candidate.get(binding_field)
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
            if artifact.get("artifact_class") != ARTIFACT_CLASS_BY_SCHEMA.get(discriminator):
                errors.append(f"manifest artifact_class mismatch for {artifact.get('path')}")
            record_identity = (target_record.get("id"), target_record.get("record_revision"), target_record.get("content_hash"))
            bound_entry = record_bound_entry.get(record_identity)
            scoped_entry = scope_by_id.get(bound_entry)
            if scoped_entry is None:
                errors.append(f"manifest record artifact is not bound to an exact in-scope inventory entry: {artifact.get('path')}")
            elif scoped_entry.get("entry_kind") != expected_entry_kind.get(discriminator):
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
    auditor = audit.get("auditor", {})
    certifier = certificate.get("certifier", {})
    if audit.get("coordinator") != coordinator or certificate.get("coordinator") != coordinator:
        errors.append("coordinator identity is not stable across manifest, audit, and certificate")
    if certificate.get("auditor") != auditor:
        errors.append("certificate auditor does not match the release audit")
    actor_ids = [coordinator.get("actor_id"), auditor.get("actor_id"), certifier.get("actor_id")]
    if len(actor_ids) != len(set(actor_ids)):
        errors.append("coordinator, auditor, and certifier identities must be pairwise distinct")

    audit_checks = [check.get("check") for check in audit.get("checks", []) if check.get("status") == "PASSED"]
    counts = Counter(audit_checks)
    if set(counts) != MANDATORY_AUDIT_CHECKS or any(count != 1 for count in counts.values()):
        errors.append("passing ReleaseAuditRecord must contain exactly one passing instance of every mandatory check")
    if audit.get("manifest_ref") != exact_ref(manifest) or audit.get("profile_ref") != exact_ref(profile) or audit.get("scope_ref") != exact_ref(scope):
        errors.append("ReleaseAuditRecord exact input references mismatch")
    if certificate.get("manifest_ref") != exact_ref(manifest) or certificate.get("audit_ref") != exact_ref(audit):
        errors.append("ReleaseCertificationRecord exact references mismatch")
    release_hash = manifest.get("release_hash")
    if audit.get("audited_release_hash") != release_hash or certificate.get("certified_release_hash") != release_hash:
        errors.append("manifest, audit, and certificate release hashes differ")

    if knowledge.get("source_release_ref") != exact_ref(manifest) or knowledge.get("release_certificate_ref") != exact_ref(certificate):
        errors.append("knowledge index does not bind the exact certified release")
    ledger_by_id = {row.get("inventory_entry_id"): row for row in ledger}
    admitted_refs: set[tuple[Any, Any, Any]] = set()
    admitted_pairs: set[tuple[Any, tuple[Any, Any, Any]]] = set()
    for index, entry in enumerate(knowledge.get("entries", [])):
        ref = entry.get("record_ref", {})
        identity = (ref.get("id"), ref.get("record_revision"), ref.get("content_hash"))
        pair = (entry.get("inventory_entry_id"), identity)
        if identity in admitted_refs:
            errors.append(f"knowledge index contains a duplicate record admission: {identity!r}")
        if pair in admitted_pairs:
            errors.append(f"knowledge index contains a duplicate inventory-entry/record pair: {pair!r}")
        if identity not in manifest_records:
            errors.append(f"knowledge index entry {index} is not an exact manifest artifact")
        bound_entry = record_bound_entry.get(identity)
        if bound_entry != entry.get("inventory_entry_id"):
            errors.append(f"knowledge index entry {index} inventory entry does not match the admitted record binding")
        row = ledger_by_id.get(entry.get("inventory_entry_id"))
        if row is None or row.get("disposition") != entry.get("admission_status") or entry.get("admission_status") not in {"ADMITTED", "CONDITIONAL"}:
            errors.append(f"knowledge index entry {index} does not match an admissible ledger disposition")
        admitted_refs.add(identity)
        admitted_pairs.add(pair)

    for name, query in bundle.items():
        if query.get("schema") != "agtxiv.query-resolution/2.0.0":
            continue
        if query.get("mode") == "PACKAGE_BACKED":
            forbidden_query_fields = {"mutation", "publication"} & query.keys()
            if forbidden_query_fields:
                errors.append(f"{name}: mutation/publication fields are not allowed: {sorted(forbidden_query_fields)}")
            if query.get("release_manifest_ref") != exact_ref(manifest) or query.get("release_certificate_ref") != exact_ref(certificate) or query.get("knowledge_index_snapshot") != exact_ref(knowledge):
                errors.append(f"{name}: package-backed query does not bind the exact certified release and index")
            for ref in query.get("returned_record_refs", []):
                identity = (ref.get("id"), ref.get("record_revision"), ref.get("content_hash"))
                if identity not in admitted_refs:
                    errors.append(f"{name}: returned record is not admitted by the exact knowledge index")
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
