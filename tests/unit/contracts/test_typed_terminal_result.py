from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


def _add_local_src_package() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    source_root = repository_root / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    return repository_root


ROOT = _add_local_src_package()

import agtxiv_v2.contracts.schema_validation as schema_validation_module  # noqa: E402
import agtxiv_v2.contracts.terminal_validation as terminal_validation_module  # noqa: E402
from agtxiv_v2.contracts import (  # noqa: E402
    ContractSchemaRegistry,
    ParsedCanonicalValue,
    SchemaAssetBinding,
    SuppliedAsset,
    build_canonical_value,
    build_schema_registry,
    raw_asset_sha256,
    record_content_hash,
    validate_immutable_record_payload,
)


TERMINAL_SCHEMA_PATH = (
    ROOT
    / "schemas"
    / "v2"
    / "contract-kernel"
    / "terminal"
    / "typed-terminal-result"
    / "1.0.0.schema.json"
)
TERMINAL_SCHEMA_ID = (
    "https://agtxiv.org/schema/v2/contract-kernel/terminal/"
    "typed-terminal-result/1.0.0"
)
TERMINAL_RECORD_TYPE = "agtxiv.typed-terminal-result/1.0.0"


def _parsed(value: object) -> ParsedCanonicalValue:
    result = build_canonical_value(value)
    assert isinstance(result, ParsedCanonicalValue), result
    return result


def _asset_ref(asset_id: str, marker: str = "1") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "media_type": "application/json",
        "byte_size": 1,
        "sha256": "sha256:" + (marker * 64),
    }


def _schema_ref(asset_id: str, marker: str = "2") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "media_type": "application/schema+json",
        "byte_size": 1,
        "sha256": "sha256:" + (marker * 64),
        "schema_uri": (
            "https://agtxiv.org/schema/v2/contract-kernel/example/"
            "placeholder/1.0.0"
        ),
    }


def _record_ref(record_type: str, record_id: str, marker: str) -> dict[str, object]:
    return {
        "record_type": record_type,
        "record_id": record_id,
        "record_revision": 1,
        "schema_ref": _schema_ref(f"schema:{record_id}", marker),
        "content_hash": "sha256:" + (marker * 64),
    }


def _terminal_schema_binding() -> SchemaAssetBinding:
    raw = TERMINAL_SCHEMA_PATH.read_bytes()
    exact_ref = {
        "asset_id": "schema:typed-terminal-result:1.0.0",
        "media_type": "application/schema+json",
        "byte_size": len(raw),
        "sha256": raw_asset_sha256(raw),
        "schema_uri": TERMINAL_SCHEMA_ID,
    }
    return SchemaAssetBinding(
        _parsed(exact_ref),
        SuppliedAsset(
            exact_ref["asset_id"],
            exact_ref["media_type"],
            raw,
            TERMINAL_SCHEMA_ID,
        ),
    )


def _all_bindings() -> tuple[SchemaAssetBinding, ...]:
    bindings: list[SchemaAssetBinding] = []
    paths = sorted(
        (ROOT / "schemas" / "v2" / "contract-kernel" / "common").glob(
            "*/1.0.0.schema.json"
        )
    )
    assert len(paths) == 8
    for path in paths:
        raw = path.read_bytes()
        document = json.loads(raw)
        schema_id = document["$id"]
        asset_id = f"schema:common:{path.parent.name}:1.0.0"
        exact_ref = {
            "asset_id": asset_id,
            "media_type": "application/schema+json",
            "byte_size": len(raw),
            "sha256": raw_asset_sha256(raw),
            "schema_uri": schema_id,
        }
        bindings.append(
            SchemaAssetBinding(
                _parsed(exact_ref),
                SuppliedAsset(asset_id, "application/schema+json", raw, schema_id),
            )
        )
    bindings.append(_terminal_schema_binding())
    return tuple(bindings)


def _payload() -> dict[str, object]:
    return {
        "terminal_for_attempt": True,
        "terminal_scope": "ATTEMPT_ONLY",
        "successful_artifact_produced": False,
        "satisfaction_claim": "NONE",
        "attempt_id": "attempt:test-1",
        "binding_context": {
            "context_mode": "PROFILE_BOUND",
            "profile_ref": _asset_ref("profile:test-1", "3"),
            "catalog_ref": _asset_ref("catalog:test-1", "4"),
        },
        "target_obligation": {
            "obligation_key": "obligation:test-1",
            "stage_id": "EXAMPLE_STAGE",
            "family_id": "EXAMPLE_FAMILY",
            "basis": {
                "basis_kind": "ASSET",
                "asset_ref": _asset_ref("source:test-1", "5"),
            },
        },
        "outcome": "RETRY_REQUIRED",
        "declared_reason": {
            "declared_reason_code": "AGTXIV.TERMINAL.EXAMPLE",
            "summary": "The dependency is not ready.",
        },
        "evidence": [
            {
                "evidence_id": "evidence:test-1",
                "evidence_role": "TOOL_DIAGNOSTIC",
                "evidence_kind": "ASSET",
                "asset_ref": _asset_ref("diagnostic:test-1", "6"),
            }
        ],
        "retry": {
            "retry_disposition": "RETRY_AFTER_CONDITION",
            "retry_condition": "The dependency becomes ready.",
        },
        "next_action": {
            "action_code": "RETRY",
            "description": "Start a new attempt after the dependency is ready.",
            "responsible_actor": {
                "actor_kind": "AGENT",
                "actor_id": "agent:test-1",
            },
            "responsible_role": "TERMINAL_ACTION_OWNER",
            "deadline": {
                "deadline_kind": "NO_DEADLINE",
                "no_deadline_reason": "The dependency controls readiness.",
            },
        },
        "resources": {
            "limit": {"max_wall_time_ms": 100},
            "observed": {"wall_time_ms": 100},
            "unobserved_metrics": [],
            "relation": "WITHIN_OBSERVED_LIMITS",
        },
    }


def _record(binding: SchemaAssetBinding) -> ParsedCanonicalValue:
    envelope = {
        "record_type": TERMINAL_RECORD_TYPE,
        "schema_ref": binding.exact_ref.to_python(),
        "record_id": "typed-terminal-result:test-1",
        "record_revision": 1,
        "contract_bundle_ref": _record_ref(
            "agtxiv.contract-bundle-release/1.0.0",
            "contract-bundle-release:test-1",
            "7",
        ),
        "created_at": "2026-08-31T12:34:56Z",
        "producer_context": {
            "producer": {"actor_kind": "AGENT", "actor_id": "agent:test-1"},
            "role": "TERMINAL_PRODUCER",
            "attempt_id": "attempt:test-1",
            "implementation_ref": _asset_ref("implementation:test-1", "8"),
            "environment_ref": _asset_ref("environment:test-1", "9"),
        },
    }
    document: dict[str, object] = {"envelope": envelope, "payload": _payload()}
    computed = record_content_hash(_parsed(document))
    assert isinstance(computed, str)
    document["content_hash"] = computed
    return _parsed(document)


def _direct_validator() -> Draft202012Validator:
    resources: list[tuple[str, Resource[Any]]] = []
    for binding in _all_bindings():
        raw = binding.supplied_asset.raw_bytes
        document = json.loads(raw)
        resources.append((document["$id"], Resource.from_contents(document)))
    registry = Registry().with_resources(resources)
    terminal_document = json.loads(TERMINAL_SCHEMA_PATH.read_bytes())
    return Draft202012Validator(
        terminal_document,
        registry=registry,
        format_checker=schema_validation_module._FIXED_FORMAT_CHECKER,
    )


def test_terminal_schema_exact_bytes_and_offline_registry_are_locked() -> None:
    raw = TERMINAL_SCHEMA_PATH.read_bytes()
    assert len(raw) == terminal_validation_module._TERMINAL_SCHEMA_BYTE_SIZE
    assert raw_asset_sha256(raw) == terminal_validation_module._TERMINAL_SCHEMA_SHA256
    assert dict(terminal_validation_module._TERMINAL_SCHEMA_EXACT_REF) == {
        "asset_id": "schema:typed-terminal-result:1.0.0",
        "media_type": "application/schema+json",
        "byte_size": len(raw),
        "sha256": raw_asset_sha256(raw),
        "schema_uri": TERMINAL_SCHEMA_ID,
    }
    result = build_schema_registry(_all_bindings())
    assert type(result) is ContractSchemaRegistry
    assert len(result.schema_ids) == 9
    assert TERMINAL_SCHEMA_ID in result.schema_ids


def test_standalone_root_and_generic_payload_entrypoint_agree() -> None:
    registry = build_schema_registry(_all_bindings())
    assert type(registry) is ContractSchemaRegistry
    binding = _terminal_schema_binding()
    record = _record(binding)
    assert list(_direct_validator().iter_errors(record.to_python())) == []
    assert validate_immutable_record_payload(record, registry) == ()


def test_standalone_root_requires_producer_context_and_exact_outer_fields() -> None:
    binding = _terminal_schema_binding()
    document = _record(binding).to_python()
    missing_producer = deepcopy(document)
    del missing_producer["envelope"]["producer_context"]
    extra_root = deepcopy(document)
    extra_root["authority"] = "ADMITTED"
    validator = _direct_validator()
    assert list(validator.iter_errors(missing_producer))
    assert list(validator.iter_errors(extra_root))


def test_standalone_root_rejects_wrong_type_and_matches_payload_failure() -> None:
    registry = build_schema_registry(_all_bindings())
    assert type(registry) is ContractSchemaRegistry
    binding = _terminal_schema_binding()
    document = _record(binding).to_python()
    wrong_type = deepcopy(document)
    wrong_type["envelope"]["record_type"] = "agtxiv.example-other/1.0.0"
    invalid_payload = deepcopy(document)
    invalid_payload["payload"]["outcome"] = "REFUTED"
    computed = record_content_hash(
        _parsed(
            {
                "envelope": invalid_payload["envelope"],
                "payload": invalid_payload["payload"],
            }
        )
    )
    assert isinstance(computed, str)
    invalid_payload["content_hash"] = computed
    validator = _direct_validator()
    assert list(validator.iter_errors(wrong_type))
    assert list(validator.iter_errors(invalid_payload))
    assert validate_immutable_record_payload(_parsed(invalid_payload), registry)
