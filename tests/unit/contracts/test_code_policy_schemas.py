from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from agtxiv_v2.contracts import (  # noqa: E402
    Diagnostic,
    ParsedCanonicalValue,
    SchemaAssetBinding,
    SuppliedAsset,
    build_canonical_value,
    build_schema_registry,
    canonical_bytes,
    parse_canonical_json,
    raw_asset_sha256,
)

SCHEMAS = {
    "catalog": ROOT / "schemas/v2/contract-kernel/contract/stable-code-catalog/1.0.0.schema.json",
    "policy": ROOT / "schemas/v2/contract-kernel/contract/kernel-validation-policy/1.0.0.schema.json",
}
ROOTS = {
    "catalog": ROOT / "contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.0.0.json",
    "policy": ROOT / "contracts/v2/contract-kernel/code-policy/kernel-validation-policy/1.0.0.json",
}
EXPECTED_IDS = {
    "catalog": "https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.0.0",
    "policy": "https://agtxiv.org/schema/v2/contract-kernel/contract/kernel-validation-policy/1.0.0",
}


def _parsed(value: object) -> ParsedCanonicalValue:
    result = build_canonical_value(value)
    assert type(result) is ParsedCanonicalValue
    return result


def _binding(kind: str) -> SchemaAssetBinding:
    raw = SCHEMAS[kind].read_bytes()
    asset = SuppliedAsset(f"schema:{'stable-code-catalog' if kind == 'catalog' else 'kernel-validation-policy'}:1.0.0", "application/schema+json", raw, EXPECTED_IDS[kind])
    ref = {"asset_id": asset.asset_id, "media_type": asset.media_type, "byte_size": len(raw), "sha256": raw_asset_sha256(raw), "schema_uri": asset.schema_uri}
    return SchemaAssetBinding(_parsed(ref), asset)


@pytest.mark.parametrize("kind", tuple(SCHEMAS))
def test_official_schemas_are_standalone_closed_and_meta_valid(kind: str) -> None:
    schema = json.loads(SCHEMAS[kind].read_bytes())
    Draft202012Validator.check_schema(schema)
    assert schema["$id"] == EXPECTED_IDS[kind]
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert all(ref.startswith("#/$defs/") for ref in _refs(schema))
    registry = build_schema_registry((_binding(kind),))
    assert not isinstance(registry, tuple)


def _refs(value: object):
    if type(value) is dict:
        for key, child in value.items():
            if key == "$ref":
                yield child
            yield from _refs(child)
    elif type(value) is list:
        for child in value:
            yield from _refs(child)


@pytest.mark.parametrize("kind", tuple(ROOTS))
def test_canonical_roots_validate_and_pin_exact_schema_bytes(kind: str) -> None:
    raw = ROOTS[kind].read_bytes()
    parsed = parse_canonical_json(raw)
    assert type(parsed) is ParsedCanonicalValue
    assert canonical_bytes(parsed) == raw
    document = parsed.to_python()
    schema_raw = SCHEMAS[kind].read_bytes()
    assert document["document_schema_ref"] == {
        "asset_id": f"schema:{'stable-code-catalog' if kind == 'catalog' else 'kernel-validation-policy'}:1.0.0",
        "media_type": "application/schema+json",
        "byte_size": len(schema_raw),
        "sha256": raw_asset_sha256(schema_raw),
        "schema_uri": EXPECTED_IDS[kind],
    }
    assert not list(Draft202012Validator(json.loads(schema_raw)).iter_errors(document))


@pytest.mark.parametrize("kind", tuple(ROOTS))
@pytest.mark.parametrize("field", ["predecessor_ref", "successor_ref", "parent", "supersedes_ref", "inherited_catalog_ref", "deprecation", "replacement", "version_range", "path_hint"])
def test_genesis_roots_reject_revision_and_locator_fields(kind: str, field: str) -> None:
    document = json.loads(ROOTS[kind].read_bytes())
    document[field] = "forbidden"
    errors = list(Draft202012Validator(json.loads(SCHEMAS[kind].read_bytes())).iter_errors(document))
    assert errors


@pytest.mark.parametrize("kind,field", [("catalog", "catalog_version"), ("policy", "policy_version")])
def test_only_version_1_0_0_is_admitted(kind: str, field: str) -> None:
    document = json.loads(ROOTS[kind].read_bytes())
    document[field] = "1.0.1"
    assert list(Draft202012Validator(json.loads(SCHEMAS[kind].read_bytes())).iter_errors(document))
    document = json.loads(ROOTS[kind].read_bytes())
    document["revision_kind"] = "SUCCESSOR"
    assert list(Draft202012Validator(json.loads(SCHEMAS[kind].read_bytes())).iter_errors(document))


def test_every_policy_exact_ref_is_closed_and_forbids_path_hint() -> None:
    schema = json.loads(SCHEMAS["policy"].read_bytes())
    original = json.loads(ROOTS["policy"].read_bytes())
    paths = [
        ("document_schema_ref",), ("code_catalog_ref",), ("terminal_schema_ref",),
        ("validator_ref",), ("conformance_vector_ref",),
        ("structural_constraints_ref", "requirements_ref"),
        ("structural_constraints_ref", "catalog_ref"),
        ("structural_constraints_ref", "profile_ref"),
    ]
    for path in paths:
        document = deepcopy(original)
        target = document
        for token in path:
            target = target[token]
        target["path_hint"] = "not-a-locator.json"
        assert list(Draft202012Validator(schema).iter_errors(document)), path


def test_policy_schema_freezes_complete_resource_map_and_registration_shape() -> None:
    document = json.loads(ROOTS["policy"].read_bytes())
    assert len(document["resource_limits"]) == 17
    assert document["resource_limits"]["maximum_total_d_input_bytes"] == 2_542_512
    assert len(document["terminal_reason_registrations"]) == 1
    registration = document["terminal_reason_registrations"][0]
    assert set(registration) == {"reason_code", "registration_kind", "allowed_outcomes", "allowed_retry_dispositions", "allowed_context_modes", "targets"}
    assert len(registration["targets"]) == 1
