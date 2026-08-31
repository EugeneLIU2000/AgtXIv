from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource


def _add_local_src_package() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    source_root = repository_root / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    return repository_root


ROOT = _add_local_src_package()
COMMON_SCHEMA_ROOT = ROOT / "schemas" / "v2" / "contract-kernel" / "common"

import agtxiv_v2.contracts.references as references_module  # noqa: E402
from agtxiv_v2.contracts import (  # noqa: E402
    Diagnostic,
    ParsedCanonicalValue,
    build_canonical_value,
    validate_immutable_envelope,
)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError(f"duplicate schema key: {key}")
        result[key] = value
    return result


def _load_schemas() -> dict[str, dict[str, Any]]:
    paths = sorted(COMMON_SCHEMA_ROOT.glob("*/1.0.0.schema.json"))
    assert len(paths) == 8
    schemas: dict[str, dict[str, Any]] = {}
    for path in paths:
        schema = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
        Draft202012Validator.check_schema(schema)
        schema_id = schema["$id"]
        assert schema_id not in schemas
        assert path.parent.name in schema_id
        assert schema_id.endswith("/1.0.0")
        schemas[schema_id] = schema
    return schemas


SCHEMAS = _load_schemas()
REGISTRY = Registry().with_resources(
    (schema_id, Resource.from_contents(schema))
    for schema_id, schema in SCHEMAS.items()
)
BASE = "https://agtxiv.org/schema/v2/contract-kernel/common"


def _validator(family: str, fragment: str = "") -> Draft202012Validator:
    schema_id = f"{BASE}/{family}/1.0.0"
    if not fragment:
        schema = SCHEMAS[schema_id]
    else:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": f"{schema_id}{fragment}",
        }
    return Draft202012Validator(
        schema,
        registry=REGISTRY,
        format_checker=FormatChecker(),
    )


def _assert_valid(family: str, instance: object, fragment: str = "") -> None:
    errors = sorted(_validator(family, fragment).iter_errors(instance), key=str)
    assert not errors, [error.message for error in errors]


def _assert_invalid(family: str, instance: object, fragment: str = "") -> None:
    assert list(_validator(family, fragment).iter_errors(instance))


def _digest(raw: bytes = b"schema") -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _asset_ref(
    asset_id: str = "schema:agentization-plan:1.0.0",
    *,
    media_type: str = "application/schema+json",
    schema_uri: str | None = (
        "https://agtxiv.org/schema/v2/contract-kernel/planning/agentization-plan/1.0.0"
    ),
) -> dict[str, object]:
    result: dict[str, object] = {
        "asset_id": asset_id,
        "media_type": media_type,
        "byte_size": len(b"schema"),
        "sha256": _digest(),
    }
    if schema_uri is not None:
        result["schema_uri"] = schema_uri
    return result


def _record_ref(
    *,
    record_type: str = "agtxiv.agentization-plan/1.0.0",
    record_id: str = "agentization-plan:fixture-1",
    record_revision: int = 1,
    schema_ref: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "record_type": record_type,
        "record_id": record_id,
        "record_revision": record_revision,
        "schema_ref": schema_ref or _asset_ref(),
        "content_hash": _digest(b"record"),
    }


def _bundle_ref() -> dict[str, object]:
    return _record_ref(
        record_type="agtxiv.contract-bundle-release/1.0.0",
        record_id="contract-bundle-release:fixture-1",
        schema_ref=_asset_ref(
            "schema:contract-bundle-release:1.0.0",
            schema_uri=(
                "https://agtxiv.org/schema/v2/contract-kernel/contract/"
                "contract-bundle-release/1.0.0"
            ),
        ),
    )


def _producer_context() -> dict[str, object]:
    implementation = _asset_ref(
        "implementation:discovery-agent:1.0.0",
        media_type="application/octet-stream",
        schema_uri=None,
    )
    environment = _asset_ref(
        "environment:python-lock:1.0.0",
        media_type="application/json",
        schema_uri=None,
    )
    return {
        "producer": {"actor_kind": "AGENT", "actor_id": "agent:discovery-A"},
        "role": "DISCOVERY_PRODUCER",
        "attempt_id": "attempt:walking-1",
        "implementation_ref": implementation,
        "environment_ref": environment,
    }


def _base_envelope() -> dict[str, object]:
    return {
        "record_type": "agtxiv.contract-bundle-release/1.0.0",
        "schema_ref": _asset_ref(
            "schema:contract-bundle-release:1.0.0",
            schema_uri=(
                "https://agtxiv.org/schema/v2/contract-kernel/contract/"
                "contract-bundle-release/1.0.0"
            ),
        ),
        "record_id": "contract-bundle-release:fixture-1",
        "record_revision": 1,
        "created_at": "2026-08-31T00:00:00Z",
    }


def _contract_envelope() -> dict[str, object]:
    return {
        "record_type": "agtxiv.agentization-plan/1.0.0",
        "schema_ref": _asset_ref(),
        "record_id": "agentization-plan:fixture-1",
        "record_revision": 1,
        "contract_bundle_ref": _bundle_ref(),
        "created_at": "2026-08-31T00:00:00.123Z",
        "producer_context": _producer_context(),
    }


def _collect_external_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if type(value) is dict:
        for key, child in value.items():
            if key == "$ref" and type(child) is str and not child.startswith("#"):
                refs.add(child.split("#", 1)[0])
            refs.update(_collect_external_refs(child))
    elif type(value) is list:
        for child in value:
            refs.update(_collect_external_refs(child))
    return refs


def _collect_patterns(value: object) -> list[str]:
    patterns: list[str] = []
    if type(value) is dict:
        for key, child in value.items():
            if key == "pattern" and type(child) is str:
                patterns.append(child)
            patterns.extend(_collect_patterns(child))
    elif type(value) is list:
        for child in value:
            patterns.extend(_collect_patterns(child))
    return patterns


def _parsed(value: object) -> ParsedCanonicalValue:
    built = build_canonical_value(value)
    assert isinstance(built, ParsedCanonicalValue), built
    return built


def _pattern_instance(case: str, value: str) -> tuple[str, object]:
    if case == "digest":
        return "digest", value
    if case in {"asset_id", "media_type", "schema_uri"}:
        instance = _asset_ref()
        instance[case] = value
        return "exact-asset-ref", instance
    if case in {"record_type", "record_id"}:
        instance = _record_ref()
        instance[case] = value
        return "exact-record-ref", instance
    if case in {"envelope_record_type", "envelope_record_id", "created_at"}:
        instance = _contract_envelope()
        field = case.removeprefix("envelope_")
        instance[field] = value
        return "immutable-record-envelope", instance
    if case in {"component_id", "json_pointer"}:
        instance = {
            **_record_ref(),
            "component_id": "component:theorem-1",
            "json_pointer": "/payload/components/0",
        }
        instance[case] = value
        return "exact-component-ref", instance
    if case == "actor_id":
        return "actor-identity", {"actor_kind": "AGENT", "actor_id": value}
    if case in {"role", "attempt_id"}:
        instance = _producer_context()
        instance[case] = value
        return "producer-context", instance
    raise AssertionError(f"unknown pattern case {case}")


PATTERN_CASES = [
    ("digest", _digest(), "g", "_DIGEST_PATTERN"),
    ("asset_id", "schema:agentization-plan:1.0.0", "?", "_NAMESPACED_ID_PATTERN"),
    ("media_type", "application/schema+json", ";", "_MEDIA_TYPE_PATTERN"),
    (
        "schema_uri",
        "https://agtxiv.org/schema/v2/contract-kernel/planning/agentization-plan/1.0.0",
        "?",
        "_SCHEMA_URI_PATTERN",
    ),
    ("record_type", "agtxiv.agentization-plan/1.0.0", "x", "_RECORD_TYPE_PATTERN"),
    ("record_id", "agentization-plan:fixture-1", "?", "_NAMESPACED_ID_PATTERN"),
    (
        "envelope_record_type",
        "agtxiv.agentization-plan/1.0.0",
        "x",
        "_RECORD_TYPE_PATTERN",
    ),
    (
        "envelope_record_id",
        "agentization-plan:fixture-1",
        "?",
        "_NAMESPACED_ID_PATTERN",
    ),
    ("component_id", "component:theorem-1", "?", "_NAMESPACED_ID_PATTERN"),
    ("json_pointer", "/payload/components/0", "~", "_JSON_POINTER_PATTERN"),
    ("actor_id", "agent:discovery-A", "?", "_NAMESPACED_ID_PATTERN"),
    ("role", "DISCOVERY_PRODUCER", "!", "_ROLE_PATTERN"),
    ("attempt_id", "attempt:walking-1", "?", "_NAMESPACED_ID_PATTERN"),
    ("created_at", "2026-08-31T00:00:00Z", "X", "_UTC_TIMESTAMP_PATTERN"),
]


def test_all_common_schemas_are_meta_valid_versioned_and_offline_closed() -> None:
    assert len(SCHEMAS) == 8
    for schema in SCHEMAS.values():
        assert _collect_external_refs(schema) <= set(SCHEMAS)
    with pytest.raises(NoSuchResource):
        REGISTRY.get_or_retrieve("https://example.invalid/not-supplied")


def test_every_schema_and_code_pattern_uses_absolute_end_assertion() -> None:
    schema_patterns = [
        pattern
        for schema in SCHEMAS.values()
        for pattern in _collect_patterns(schema)
    ]
    assert len(schema_patterns) == 14
    assert all(pattern.endswith(r"(?![\s\S])") for pattern in schema_patterns)
    assert all(not pattern.endswith("$") and r"\Z" not in pattern for pattern in schema_patterns)
    for _, _, _, code_pattern_name in PATTERN_CASES:
        code_pattern = getattr(references_module, code_pattern_name).pattern
        assert code_pattern.endswith(r"(?![\s\S])")
        assert not code_pattern.endswith("$") and r"\Z" not in code_pattern


@pytest.mark.parametrize(
    ("case", "base_value", "extra_character", "code_pattern_name"),
    PATTERN_CASES,
    ids=[case[0] for case in PATTERN_CASES],
)
@pytest.mark.parametrize(
    ("suffix_name", "suffix"),
    [("lf", "\n"), ("cr", "\r"), ("extra", None)],
)
def test_schema_and_code_patterns_both_reject_all_trailing_data(
    case: str,
    base_value: str,
    extra_character: str,
    code_pattern_name: str,
    suffix_name: str,
    suffix: str | None,
) -> None:
    actual_suffix = extra_character if suffix_name == "extra" else suffix
    assert actual_suffix is not None
    mutated = base_value + actual_suffix
    family, instance = _pattern_instance(case, mutated)
    _assert_invalid(family, instance)
    code_pattern = getattr(references_module, code_pattern_name)
    assert code_pattern.fullmatch(mutated) is None


def test_standalone_positive_instances_cover_every_common_family() -> None:
    _assert_valid("digest", _digest())
    _assert_valid("exact-asset-ref", _asset_ref())
    _assert_valid("exact-record-ref", _record_ref())
    _assert_valid(
        "exact-component-ref",
        {
            **_record_ref(),
            "component_id": "component:theorem-1",
            "json_pointer": "/payload/components/0",
        },
    )
    _assert_valid("actor-identity", {"actor_kind": "HUMAN", "actor_id": "human:reviewer-B"})
    _assert_valid("producer-context", _producer_context())
    _assert_valid("resource-budget", {"max_wall_time_ms": 60_000, "max_network_requests": 0})
    _assert_valid("immutable-record-envelope", _base_envelope())
    _assert_valid("immutable-record-envelope", _contract_envelope())


@pytest.mark.parametrize(
    "digest",
    [
        "0" * 64,
        "sha256:" + ("A" * 64),
        "sha256:" + ("0" * 63),
        "sha256:" + ("0" * 64) + "\n",
    ],
)
def test_digest_rejects_non_exact_spellings(digest: str) -> None:
    _assert_invalid("digest", digest)


@pytest.mark.parametrize("forbidden_field", ["path", "url", "git_branch", "latest"])
def test_asset_ref_rejects_authoritative_locator_or_floating_fields(
    forbidden_field: str,
) -> None:
    ref = {**_asset_ref(), forbidden_field: "main"}
    _assert_invalid("exact-asset-ref", ref)


def test_asset_ref_rejects_digest_free_and_mutable_schema_uri() -> None:
    digest_free = _asset_ref()
    digest_free.pop("sha256")
    _assert_invalid("exact-asset-ref", digest_free)

    mutable_uri = _asset_ref()
    mutable_uri["schema_uri"] = "https://agtxiv.org/schema/v2/contract-kernel/planning/latest"
    _assert_invalid("exact-asset-ref", mutable_uri)


def test_record_and_component_ref_are_disjoint_exact_shapes() -> None:
    component = {
        **_record_ref(),
        "component_id": "component:theorem-1",
        "json_pointer": "/payload/components/0",
    }
    _assert_invalid("exact-record-ref", component)

    missing_pointer = dict(component)
    missing_pointer.pop("json_pointer")
    _assert_invalid("exact-component-ref", missing_pointer)

    malformed_pointer = {**component, "json_pointer": "/payload/~2bad"}
    _assert_invalid("exact-component-ref", malformed_pointer)


def test_record_ref_rejects_revisionless_schema_less_and_wrong_schema_media() -> None:
    for field in ("record_revision", "schema_ref", "content_hash"):
        incomplete = _record_ref()
        incomplete.pop(field)
        _assert_invalid("exact-record-ref", incomplete)

    wrong_media = _record_ref()
    wrong_media["schema_ref"] = _asset_ref(media_type="application/json", schema_uri=None)
    _assert_invalid("exact-record-ref", wrong_media)

    noncanonical_version = _record_ref()
    noncanonical_version["record_type"] = "agtxiv.agentization-plan/01.0.0"
    _assert_invalid("exact-record-ref", noncanonical_version)


def test_actor_and_producer_context_do_not_accept_authority_claims_or_implicit_tools() -> None:
    _assert_invalid(
        "actor-identity",
        {"actor_kind": "AGENT", "actor_id": "agent:A", "production_authorized": True},
    )
    implicit_tool = _producer_context()
    implicit_tool["implementation_ref"] = {"url": "https://example.invalid/latest"}
    _assert_invalid("producer-context", implicit_tool)


def test_envelope_modes_and_revision_rules_are_disjoint() -> None:
    base_validator_fragment = "#/$defs/baseEnvelope"
    contract_validator_fragment = "#/$defs/contractBoundEnvelope"
    _assert_valid("immutable-record-envelope", _base_envelope(), base_validator_fragment)
    _assert_valid("immutable-record-envelope", _contract_envelope(), contract_validator_fragment)
    _assert_invalid("immutable-record-envelope", _contract_envelope(), base_validator_fragment)
    _assert_invalid("immutable-record-envelope", _base_envelope(), contract_validator_fragment)

    runtime_without_contract = _contract_envelope()
    runtime_without_contract.pop("contract_bundle_ref")
    _assert_invalid("immutable-record-envelope", runtime_without_contract)

    bundle_with_contract = _base_envelope()
    bundle_with_contract["contract_bundle_ref"] = _bundle_ref()
    _assert_invalid("immutable-record-envelope", bundle_with_contract)

    revision_two = _contract_envelope()
    revision_two["record_revision"] = 2
    _assert_invalid("immutable-record-envelope", revision_two, contract_validator_fragment)
    revision_two["supersedes_ref"] = _record_ref()
    _assert_valid("immutable-record-envelope", revision_two, contract_validator_fragment)

    first_with_predecessor = _contract_envelope()
    first_with_predecessor["supersedes_ref"] = _record_ref()
    _assert_invalid("immutable-record-envelope", first_with_predecessor, contract_validator_fragment)


def test_envelope_rejects_wrong_contract_type_and_unrecognized_provenance() -> None:
    wrong_contract = _contract_envelope()
    wrong_contract["contract_bundle_ref"] = _record_ref()
    _assert_invalid(
        "immutable-record-envelope",
        wrong_contract,
        "#/$defs/contractBoundEnvelope",
    )
    unknown = {**_contract_envelope(), "source_path": "/tmp/current.json"}
    _assert_invalid("immutable-record-envelope", unknown)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-02-30T00:00:00Z",
        "2026-08-31T24:00:00Z",
        "2026-08-31T23:59:60Z",
    ],
    ids=["invalid-date", "hour-24", "leap-second"],
)
def test_timestamp_schema_and_code_reject_invalid_calendar_values(
    timestamp: str,
) -> None:
    envelope = _contract_envelope()
    envelope["created_at"] = timestamp
    _assert_invalid("immutable-record-envelope", envelope)
    result = validate_immutable_envelope(_parsed(envelope), contract_bound=True)
    assert isinstance(result, Diagnostic)


def test_timestamp_schema_and_code_accept_exactly_nine_fractional_digits() -> None:
    envelope = _contract_envelope()
    envelope["created_at"] = "2026-08-31T23:59:59.123456789Z"
    _assert_valid("immutable-record-envelope", envelope)
    assert validate_immutable_envelope(_parsed(envelope), contract_bound=True) is None


@pytest.mark.parametrize(
    "budget",
    [
        {},
        {"max_wall_time_ms": -1},
        {"max_wall_time_ms": 1.5},
        {"max_wall_time_ms": 9007199254740992},
        {"unbounded": True},
    ],
)
def test_resource_budget_rejects_empty_unsafe_or_implicit_limits(
    budget: dict[str, object],
) -> None:
    _assert_invalid("resource-budget", budget)


def test_negative_mutations_do_not_modify_positive_templates() -> None:
    original = _contract_envelope()
    mutated = copy.deepcopy(original)
    mutated["contract_bundle_ref"]["record_revision"] = 0  # type: ignore[index]
    _assert_invalid("immutable-record-envelope", mutated)
    _assert_valid("immutable-record-envelope", original)
