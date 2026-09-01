from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


def _add_local_src_package() -> Path:
    root = Path(__file__).resolve().parents[3]
    source = root / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    return root


ROOT = _add_local_src_package()

from agtxiv_v2.contracts import (  # noqa: E402
    ContractSchemaRegistry,
    Diagnostic,
    DiagnosticCode,
    ParsedCanonicalValue,
    SchemaAssetBinding,
    SuppliedAsset,
    build_canonical_value,
    build_schema_registry,
    canonical_bytes,
    parse_canonical_json,
    raw_asset_sha256,
    record_content_hash,
    validate_immutable_record_payload,
)

FIXTURE = ROOT / "fixtures/v2-contract-kernel/catalog-profile/1.0.0"
OFFICIAL = {
    "requirements": (
        ROOT / "schemas/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0.schema.json",
        "schema:m1-contract-requirement-set:1.0.0",
        "https://agtxiv.org/schema/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0",
    ),
    "catalog": (
        ROOT / "schemas/v2/contract-kernel/contract/artifact-family-catalog/1.0.0.schema.json",
        "schema:artifact-family-catalog:1.0.0",
        "https://agtxiv.org/schema/v2/contract-kernel/contract/artifact-family-catalog/1.0.0",
    ),
    "profile": (
        ROOT / "schemas/v2/contract-kernel/contract/agentization-profile-release/1.0.0.schema.json",
        "schema:agentization-profile-release:1.0.0",
        "https://agtxiv.org/schema/v2/contract-kernel/contract/agentization-profile-release/1.0.0",
    ),
    "synthetic": (
        FIXTURE / "synthetic-immutable-record/1.0.0.schema.json",
        "schema:fixture:checkpoint-c-synthetic-record:1.0.0",
        "https://agtxiv.org/schema/v2/contract-kernel/fixture/checkpoint-c-synthetic-record/1.0.0",
    ),
}


def _parsed(value: object) -> ParsedCanonicalValue:
    result = build_canonical_value(value)
    assert type(result) is ParsedCanonicalValue
    return result


def _binding(path: Path, asset_id: str) -> SchemaAssetBinding:
    raw = path.read_bytes()
    uri = json.loads(raw)["$id"]
    ref = {
        "asset_id": asset_id,
        "media_type": "application/schema+json",
        "byte_size": len(raw),
        "sha256": raw_asset_sha256(raw),
        "schema_uri": uri,
    }
    return SchemaAssetBinding(
        _parsed(ref), SuppliedAsset(asset_id, "application/schema+json", raw, uri)
    )


def _registry() -> ContractSchemaRegistry:
    bindings = []
    for path in sorted((ROOT / "schemas/v2/contract-kernel/common").glob("*/1.0.0.schema.json")):
        bindings.append(_binding(path, f"schema:common:{path.parent.name}:1.0.0"))
    for path, asset_id, _ in OFFICIAL.values():
        bindings.append(_binding(path, asset_id))
    result = build_schema_registry(tuple(reversed(bindings)))
    assert type(result) is ContractSchemaRegistry, result
    return result


def _asset_ref(asset_id: str, marker: str) -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "media_type": "application/json",
        "byte_size": 1,
        "sha256": "sha256:" + marker * 64,
    }


def _record_ref(record_type: str, record_id: str, marker: str) -> dict[str, object]:
    return {
        "record_type": record_type,
        "record_id": record_id,
        "record_revision": 1,
        "schema_ref": {
            **_asset_ref(f"schema:{record_id}", marker),
            "media_type": "application/schema+json",
            "schema_uri": "https://agtxiv.org/schema/v2/contract-kernel/example/placeholder/1.0.0",
        },
        "content_hash": "sha256:" + marker * 64,
    }


def _synthetic_record(registry: ContractSchemaRegistry) -> ParsedCanonicalValue:
    path, asset_id, uri = OFFICIAL["synthetic"]
    raw = path.read_bytes()
    envelope = {
        "record_type": "agtxiv.checkpoint-c-synthetic-record/1.0.0",
        "schema_ref": {
            "asset_id": asset_id,
            "media_type": "application/schema+json",
            "byte_size": len(raw),
            "sha256": raw_asset_sha256(raw),
            "schema_uri": uri,
        },
        "record_id": "checkpoint-c-synthetic-record:test-1",
        "record_revision": 1,
        "contract_bundle_ref": _record_ref(
            "agtxiv.contract-bundle-release/1.0.0",
            "contract-bundle-release:test-1",
            "1",
        ),
        "created_at": "2026-08-31T12:34:56Z",
        "producer_context": {
            "producer": {"actor_kind": "AGENT", "actor_id": "agent:test-1"},
            "role": "SYNTHETIC_RECORD_PRODUCER",
            "attempt_id": "attempt:test-1",
            "implementation_ref": _asset_ref("implementation:test-1", "2"),
            "environment_ref": _asset_ref("environment:test-1", "3"),
        },
    }
    document = {
        "envelope": envelope,
        "payload": {
            "fixture_purpose": "STRUCTURAL_INTEGRATION_ONLY",
            "synthetic_artifact_id": "synthetic:test-1",
            "synthetic_value": "deterministic fixture value",
        },
    }
    digest = record_content_hash(_parsed(document))
    assert type(digest) is str
    document["content_hash"] = digest
    return _parsed(document)


def _rehash(document: dict[str, object]) -> ParsedCanonicalValue:
    value = deepcopy(document)
    value.pop("content_hash", None)
    digest = record_content_hash(_parsed(value))
    assert type(digest) is str
    value["content_hash"] = digest
    return _parsed(value)


def test_four_checkpoint_c_schemas_are_exact_meta_valid_offline_registry_members() -> None:
    registry = _registry()
    for path, asset_id, uri in OFFICIAL.values():
        raw = path.read_bytes()
        document = json.loads(raw)
        assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert document["$id"] == uri
        assert asset_id in {entry.supplied_asset.asset_id for entry in [_binding(path, asset_id)]}
        assert uri in registry.schema_ids
        assert raw_asset_sha256(raw) == "sha256:" + hashlib.sha256(raw).hexdigest()


def test_same_id_substituted_schema_bytes_are_not_the_pinned_asset() -> None:
    path, asset_id, uri = OFFICIAL["catalog"]
    changed = json.loads(path.read_bytes())
    changed["description"] += " substituted"
    raw = json.dumps(changed, sort_keys=True, separators=(",", ":")).encode()
    binding = SchemaAssetBinding(
        _parsed({
            "asset_id": asset_id,
            "media_type": "application/schema+json",
            "byte_size": len(raw),
            "sha256": raw_asset_sha256(raw),
            "schema_uri": uri,
        }),
        SuppliedAsset(asset_id, "application/schema+json", raw, uri),
    )
    common = [
        _binding(item, f"schema:common:{item.parent.name}:1.0.0")
        for item in sorted(
            (ROOT / "schemas/v2/contract-kernel/common").glob("*/1.0.0.schema.json")
        )
    ]
    result = build_schema_registry(tuple(common + [binding]))
    assert type(result) is ContractSchemaRegistry
    assert raw_asset_sha256(raw) != raw_asset_sha256(path.read_bytes())


@pytest.mark.parametrize("name", ["requirements", "catalog", "profile"])
@pytest.mark.parametrize(
    "forbidden",
    [
        "coverage", "coverage_status", "runtime_authority", "authority",
        "production_authority", "maturity", "completion", "completion_status",
        "release", "released", "release_effect", "admission",
        "admission_status", "admitted",
    ],
)
def test_official_document_schemas_are_closed_against_authority_claims(name: str, forbidden: str) -> None:
    fixture_path = {
        "requirements": ROOT / "contracts/v2/contract-kernel/requirements/m1-contract-requirement-set/1.0.0.json",
        "catalog": FIXTURE / "catalog.synthetic.json",
        "profile": FIXTURE / "profile.synthetic.json",
    }[name]
    document = json.loads(fixture_path.read_bytes())
    document[forbidden] = "NONE"
    resources = []
    for path in sorted((ROOT / "schemas/v2/contract-kernel/common").glob("*/1.0.0.schema.json")):
        schema = json.loads(path.read_bytes())
        resources.append((schema["$id"], Resource.from_contents(schema)))
    for path, _, uri in OFFICIAL.values():
        resources.append((uri, Resource.from_contents(json.loads(path.read_bytes()))))
    validator = Draft202012Validator(
        {"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": OFFICIAL[name][2]},
        registry=Registry().with_resources(resources),
    )
    errors = list(validator.iter_errors(document))
    assert errors and any(error.validator == "additionalProperties" for error in errors)


def test_all_raw_contract_fixture_documents_are_canonical_bytes() -> None:
    paths = [
        ROOT / "contracts/v2/contract-kernel/requirements/m1-contract-requirement-set/1.0.0.json",
        FIXTURE / "family-conformance-vectors.json",
        FIXTURE / "catalog.synthetic.json",
        FIXTURE / "profile.synthetic.json",
        FIXTURE / "linkage.integration-fixture.json",
    ]
    for path in paths:
        parsed = parse_canonical_json(path.read_bytes())
        assert type(parsed) is ParsedCanonicalValue, (path, parsed)
        assert canonical_bytes(parsed) == path.read_bytes()


def test_synthetic_immutable_record_validates_with_generic_checkpoint_a_validator() -> None:
    registry = _registry()
    assert validate_immutable_record_payload(_synthetic_record(registry), registry) == ()


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda d: d["envelope"].pop("contract_bundle_ref"), DiagnosticCode.RECORD_INVALID_ENVELOPE),
        (lambda d: d["payload"].pop("synthetic_value"), DiagnosticCode.RECORD_PAYLOAD_INVALID),
        (lambda d: d["payload"].update(synthetic_value="   "), DiagnosticCode.RECORD_PAYLOAD_INVALID),
        (lambda d: d["envelope"].update(record_type="agtxiv.other/1.0.0"), DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH),
        (lambda d: d["envelope"].update(producer_context=[]), DiagnosticCode.RECORD_INVALID_ENVELOPE),
    ],
)
def test_synthetic_record_closed_root_payload_type_and_context_negatives(mutation, expected: DiagnosticCode) -> None:
    registry = _registry()
    document = _synthetic_record(registry).to_python()
    mutation(document)
    result = validate_immutable_record_payload(_rehash(document), registry)
    assert expected in {diagnostic.code for diagnostic in result}


def test_synthetic_record_hash_replacement_is_rejected() -> None:
    registry = _registry()
    document = _synthetic_record(registry).to_python()
    document["content_hash"] = "sha256:" + "0" * 64
    result = validate_immutable_record_payload(_parsed(document), registry)
    assert DiagnosticCode.RECORD_HASH_MISMATCH in {diagnostic.code for diagnostic in result}


def test_linkage_manifest_is_closed_non_normative_metadata() -> None:
    document = json.loads((FIXTURE / "linkage.integration-fixture.json").read_bytes())
    assert set(document) == {
        "fixture_purpose", "normative_status", "runtime_authority", "coverage_claim",
        "requirements_ref", "catalog_ref", "profile_ref",
    }
    assert document["fixture_purpose"] == "STRUCTURAL_INTEGRATION_ONLY"
    assert document["normative_status"] == "NON_NORMATIVE"
    assert document["runtime_authority"] == document["coverage_claim"] == "NONE"
