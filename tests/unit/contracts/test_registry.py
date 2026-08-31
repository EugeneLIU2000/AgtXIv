from __future__ import annotations

import builtins
import itertools
import json
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker


def _add_local_src_package() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    source_root = repository_root / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    return repository_root


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
    raw_asset_sha256,
)
import agtxiv_v2.contracts.registry as registry_module  # noqa: E402


DIALECT = "https://json-schema.org/draft/2020-12/schema"
BASE = "https://agtxiv.org/schema/v2/contract-kernel/example"


def _raw(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _parsed(value: object) -> ParsedCanonicalValue:
    result = build_canonical_value(value)
    assert isinstance(result, ParsedCanonicalValue), result
    return result


def _schema(
    family: str = "family-a",
    *,
    body: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "$schema": DIALECT,
        "$id": f"{BASE}/{family}/1.0.0",
        "type": "object",
        **({} if body is None else body),
    }


def _binding(
    schema: object,
    *,
    asset_id: str = "schema:family-a:1.0.0",
    schema_uri: str | None = None,
    raw: bytes | None = None,
    ref_changes: dict[str, object] | None = None,
    asset_changes: dict[str, object] | None = None,
) -> SchemaAssetBinding:
    raw_bytes = _raw(schema) if raw is None else raw
    if schema_uri is None and type(schema) is dict and type(schema.get("$id")) is str:
        schema_uri = schema["$id"]  # type: ignore[assignment]
    schema_uri = schema_uri or f"{BASE}/family-a/1.0.0"
    ref: dict[str, object] = {
        "asset_id": asset_id,
        "media_type": "application/schema+json",
        "byte_size": len(raw_bytes),
        "sha256": raw_asset_sha256(raw_bytes),
        "schema_uri": schema_uri,
    }
    ref.update(ref_changes or {})
    asset_fields: dict[str, object] = {
        "asset_id": asset_id,
        "media_type": "application/schema+json",
        "raw_bytes": raw_bytes,
        "schema_uri": schema_uri,
    }
    asset_fields.update(asset_changes or {})
    return SchemaAssetBinding(
        exact_ref=_parsed(ref),
        supplied_asset=SuppliedAsset(**asset_fields),  # type: ignore[arg-type]
    )


def _codes(result: object) -> tuple[DiagnosticCode, ...]:
    assert type(result) is tuple
    assert result
    assert all(type(item) is Diagnostic for item in result)
    return tuple(item.code for item in result)


def _serialized(result: tuple[Diagnostic, ...]) -> bytes:
    return _raw([diagnostic.to_dict() for diagnostic in result])


def test_registry_diagnostic_codes_are_locked() -> None:
    expected = {
        DiagnosticCode.SCHEMA_EMPTY_REGISTRY: "AGTXIV.SCHEMA.EMPTY_REGISTRY",
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH: "AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH",
        DiagnosticCode.SCHEMA_INVALID_DOCUMENT: "AGTXIV.SCHEMA.INVALID_DOCUMENT",
        DiagnosticCode.SCHEMA_DIALECT_MISMATCH: "AGTXIV.SCHEMA.DIALECT_MISMATCH",
        DiagnosticCode.SCHEMA_ID_MISMATCH: "AGTXIV.SCHEMA.ID_MISMATCH",
        DiagnosticCode.SCHEMA_DUPLICATE_ID: "AGTXIV.SCHEMA.DUPLICATE_ID",
        DiagnosticCode.SCHEMA_META_INVALID: "AGTXIV.SCHEMA.META_INVALID",
        DiagnosticCode.SCHEMA_UNRESOLVED_REF: "AGTXIV.SCHEMA.UNRESOLVED_REF",
        DiagnosticCode.SCHEMA_REFERENCE_CYCLE: "AGTXIV.SCHEMA.REFERENCE_CYCLE",
        DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN: "AGTXIV.SCHEMA.REMOTE_REF_FORBIDDEN",
    }
    assert {code: str(code) for code in expected} == expected


def test_success_is_one_nonconstructible_frozen_registry() -> None:
    result = build_schema_registry((_binding(_schema()),))
    assert type(result) is ContractSchemaRegistry
    assert result.schema_ids == (f"{BASE}/family-a/1.0.0",)
    assert "sealed" not in dir(result)
    assert "released" not in dir(result)
    assert "admitted" not in dir(result)
    with pytest.raises(TypeError):
        ContractSchemaRegistry()  # type: ignore[call-arg]
    with pytest.raises(AttributeError):
        result.schema_ids = ()  # type: ignore[misc]


@pytest.mark.parametrize(
    "bindings",
    [
        [],
        object(),
        (object(),),
    ],
    ids=["list", "object", "wrong-member"],
)
def test_wrong_public_input_types_are_diagnostic_only(bindings: object) -> None:
    result = build_schema_registry(bindings)  # type: ignore[arg-type]
    assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


def test_empty_registry_is_a_distinct_failure() -> None:
    assert _codes(build_schema_registry(())) == (DiagnosticCode.SCHEMA_EMPTY_REGISTRY,)


def test_subclasses_incomplete_members_and_forged_opaque_values_fail_closed() -> None:
    class BindingSubclass(SchemaAssetBinding):
        __slots__ = ()

    valid = _binding(_schema())
    subclass = BindingSubclass(valid.exact_ref, valid.supplied_asset)
    assert _codes(build_schema_registry((subclass,))) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )

    incomplete = object.__new__(SchemaAssetBinding)
    assert _codes(build_schema_registry((incomplete,))) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )

    forged_ref = _parsed({})
    object.__setattr__(forged_ref, "_ParsedCanonicalValue__node", {"host": "dict"})
    forged = SchemaAssetBinding(forged_ref, valid.supplied_asset)
    assert _codes(build_schema_registry((forged,))) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )


def test_phase_one_failure_aggregation_is_permutation_stable_without_indices() -> None:
    valid = _binding(_schema())
    incomplete = object.__new__(SchemaAssetBinding)
    wrong_fields = SchemaAssetBinding(  # type: ignore[arg-type]
        object(),
        valid.supplied_asset,
    )
    malformed = (object(), incomplete, wrong_fields)
    observations = {
        _serialized(build_schema_registry(permutation))  # type: ignore[arg-type]
        for permutation in itertools.permutations(malformed)
    }
    assert len(observations) == 1
    result = build_schema_registry(malformed)  # type: ignore[arg-type]
    assert _codes(result) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )

    forged_asset = object.__new__(SuppliedAsset)
    forged = SchemaAssetBinding(valid.exact_ref, forged_asset)
    assert _codes(build_schema_registry((forged,))) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )


def test_phase_one_failure_stops_before_raw_hash_or_identity_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = _binding(_schema())
    ref = valid.exact_ref.to_python()
    ref.pop("asset_id")
    semantic_failure = SchemaAssetBinding(
        _parsed(ref),
        SuppliedAsset(
            "\ud800",
            valid.supplied_asset.media_type,
            valid.supplied_asset.raw_bytes,
            "\ud800",
        ),
    )

    def forbidden(_: bytes) -> str:
        raise AssertionError("phase one inspected raw schema bytes")

    monkeypatch.setattr(registry_module, "raw_asset_sha256", forbidden)
    assert _codes(
        build_schema_registry((object(), semantic_failure))  # type: ignore[arg-type]
    ) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


@pytest.mark.parametrize(
    ("ref_changes", "asset_changes", "expected"),
    [
        ({"byte_size": 999}, {}, DiagnosticCode.REF_HASH_MISMATCH),
        ({"sha256": "sha256:" + ("0" * 64)}, {}, DiagnosticCode.REF_HASH_MISMATCH),
        ({"media_type": "application/json"}, {}, DiagnosticCode.REF_TYPE_MISMATCH),
        ({}, {"media_type": "application/json"}, DiagnosticCode.REF_TYPE_MISMATCH),
        ({"asset_id": "schema:other:1.0.0"}, {}, DiagnosticCode.REF_UNRESOLVED),
        (
            {"schema_uri": f"{BASE}/other/1.0.0"},
            {},
            DiagnosticCode.SCHEMA_ID_MISMATCH,
        ),
        (
            {},
            {"schema_uri": f"{BASE}/other/1.0.0"},
            DiagnosticCode.SCHEMA_ID_MISMATCH,
        ),
    ],
)
def test_exact_raw_binding_is_checked_before_parsing(
    ref_changes: dict[str, object],
    asset_changes: dict[str, object],
    expected: DiagnosticCode,
) -> None:
    result = build_schema_registry(
        (
            _binding(
                _schema(),
                ref_changes=ref_changes,
                asset_changes=asset_changes,
            ),
        )
    )
    assert expected in _codes(result)
    assert all(diagnostic.phase == "REGISTRY_EXACT_BINDING" for diagnostic in result)


def test_phase_two_aggregates_independent_field_failures_in_stable_order() -> None:
    valid = _binding(_schema())
    fields = valid.exact_ref.to_python()
    fields.update(
        {
            "media_type": "application/json",
            "byte_size": -1,
            "sha256": "not-a-digest",
        }
    )
    observations: set[bytes] = set()
    for permutation in itertools.permutations(fields.items()):
        binding = SchemaAssetBinding(
            _parsed(dict(permutation)),
            valid.supplied_asset,
        )
        observations.add(_serialized(build_schema_registry((binding,))))
    assert len(observations) == 1
    result = build_schema_registry((SchemaAssetBinding(_parsed(fields), valid.supplied_asset),))
    assert {diagnostic.json_pointer for diagnostic in result} == {
        "/byte_size",
        "/media_type",
        "/sha256",
    }
    assert set(_codes(result)) == {
        DiagnosticCode.CONTRACT_MUTABLE_REF,
        DiagnosticCode.REF_TYPE_MISMATCH,
    }


def test_phase_two_key_set_failure_does_not_hide_safe_present_field_failures() -> None:
    valid = _binding(_schema())
    fields = valid.exact_ref.to_python()
    fields.pop("asset_id")
    fields.update(
        {
            "unexpected": True,
            "media_type": "application/json",
            "byte_size": -1,
            "sha256": "not-a-digest",
        }
    )
    observations = {
        _serialized(
            build_schema_registry(
                (
                    SchemaAssetBinding(
                        _parsed(dict(items)),
                        valid.supplied_asset,
                    ),
                )
            )
        )
        for items in (tuple(fields.items()), tuple(reversed(tuple(fields.items()))))
    }
    assert len(observations) == 1
    result = build_schema_registry(
        (SchemaAssetBinding(_parsed(fields), valid.supplied_asset),)
    )
    assert {diagnostic.json_pointer for diagnostic in result} == {
        "",
        "/byte_size",
        "/media_type",
        "/sha256",
    }
    assert all(
        diagnostic.phase == "REGISTRY_EXACT_BINDING" for diagnostic in result
    )


def test_supplied_string_semantics_are_phase_two_and_hostile_unicode_is_total() -> None:
    valid = _binding(_schema())
    ref = valid.exact_ref.to_python()
    ref.pop("asset_id")
    supplied = SuppliedAsset(
        "\ud800",
        "INVALID",
        valid.supplied_asset.raw_bytes,
        "\ud800",
    )
    result = build_schema_registry((SchemaAssetBinding(_parsed(ref), supplied),))
    assert result
    assert all(
        diagnostic.phase == "REGISTRY_EXACT_BINDING" for diagnostic in result
    )
    assert DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH not in _codes(result)
    assert {diagnostic.json_pointer for diagnostic in result} >= {
        "",
        "/supplied_asset/asset_id",
        "/supplied_asset/media_type",
        "/supplied_asset/schema_uri",
    }
    assert all(
        diagnostic.subject_identity
        == raw_asset_sha256(valid.supplied_asset.raw_bytes)
        for diagnostic in result
    )


def test_phase_two_binding_observation_never_adopts_path_hint() -> None:
    result = build_schema_registry(
        (
            _binding(
                _schema(),
                ref_changes={
                    "byte_size": 0,
                    "path_hint": "/private/mutable/location.schema.json",
                },
            ),
        )
    )
    assert _codes(result) == (DiagnosticCode.REF_HASH_MISMATCH,)
    details = result[0].to_dict()["details"]
    assert "path_hint" not in json.dumps(details, sort_keys=True)
    assert set(details["binding_observation"]) >= {
        "raw_byte_size",
        "raw_sha256",
        "exact_ref_byte_size",
    }


def test_both_schema_uri_assertions_are_mandatory() -> None:
    valid = _binding(_schema())
    ref = valid.exact_ref.to_python()
    ref.pop("schema_uri")
    missing_ref = SchemaAssetBinding(_parsed(ref), valid.supplied_asset)
    assert _codes(build_schema_registry((missing_ref,))) == (
        DiagnosticCode.SCHEMA_ID_MISMATCH,
    )

    without_asset_uri = SuppliedAsset(
        valid.supplied_asset.asset_id,
        valid.supplied_asset.media_type,
        valid.supplied_asset.raw_bytes,
    )
    missing_asset = SchemaAssetBinding(valid.exact_ref, without_asset_uri)
    assert _codes(build_schema_registry((missing_asset,))) == (
        DiagnosticCode.SCHEMA_ID_MISMATCH,
    )


def test_distinct_valid_schema_uri_mismatches_remain_distinct_and_ordered() -> None:
    first = _binding(
        _schema(),
        asset_changes={"schema_uri": f"{BASE}/other-a/1.0.0"},
    )
    second = _binding(
        _schema(),
        asset_changes={"schema_uri": f"{BASE}/other-b/1.0.0"},
    )
    observations = {
        _serialized(build_schema_registry(order))
        for order in ((first, second), (second, first))
    }
    assert len(observations) == 1
    result = build_schema_registry((first, second))
    assert _codes(result) == (
        DiagnosticCode.SCHEMA_ID_MISMATCH,
        DiagnosticCode.SCHEMA_ID_MISMATCH,
    )
    assert {
        diagnostic.to_dict()["details"]["supplied_schema_uri"]
        for diagnostic in result
    } == {
        f"{BASE}/other-a/1.0.0",
        f"{BASE}/other-b/1.0.0",
    }
    assert all(
        diagnostic.to_dict()["details"]["exact_ref_schema_uri"]
        == f"{BASE}/family-a/1.0.0"
        for diagnostic in result
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (b"[]", DiagnosticCode.SCHEMA_INVALID_DOCUMENT),
        (b'{"$schema":"x","$schema":"y"}', DiagnosticCode.DUPLICATE_KEY),
        (b'\xff', DiagnosticCode.INVALID_UTF8),
        (b'{"value":1.0}', DiagnosticCode.UNSUPPORTED_NUMBER),
        (b'{} trailing', DiagnosticCode.INVALID_JSON),
    ],
)
def test_strict_schema_parsing_and_top_level_shape(raw: bytes, expected: DiagnosticCode) -> None:
    result = build_schema_registry((_binding({}, raw=raw),))
    assert _codes(result) == (expected,)
    assert result[0].phase == "REGISTRY_PARSE"


def test_distinct_raw_bindings_with_same_parse_failure_are_not_deduplicated() -> None:
    bindings = (
        _binding({}, raw=b"?a"),
        _binding({}, raw=b"?b"),
    )
    observations = {
        _serialized(build_schema_registry(order))
        for order in (bindings, tuple(reversed(bindings)))
    }
    assert len(observations) == 1
    result = build_schema_registry(bindings)
    assert _codes(result) == (
        DiagnosticCode.INVALID_JSON,
        DiagnosticCode.INVALID_JSON,
    )
    binding_observations = [
        diagnostic.to_dict()["details"]["binding_observation"]
        for diagnostic in result
    ]
    assert len({item["raw_sha256"] for item in binding_observations}) == 2
    assert {item["raw_byte_size"] for item in binding_observations} == {2}


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ({"$schema": "https://json-schema.org/draft/2019-09/schema"}, DiagnosticCode.SCHEMA_DIALECT_MISMATCH),
        ({"$id": f"{BASE}/latest"}, DiagnosticCode.SCHEMA_ID_MISMATCH),
        ({"$id": "https://example.invalid/schema/1.0.0"}, DiagnosticCode.SCHEMA_ID_MISMATCH),
        ({"unknownKeyword": True}, DiagnosticCode.SCHEMA_META_INVALID),
        ({"$anchor": "x"}, DiagnosticCode.SCHEMA_META_INVALID),
        ({"$dynamicRef": "#x"}, DiagnosticCode.SCHEMA_META_INVALID),
        ({"format": "email"}, DiagnosticCode.SCHEMA_META_INVALID),
        ({"format": 1}, DiagnosticCode.SCHEMA_META_INVALID),
        ({"pattern": "["}, DiagnosticCode.SCHEMA_META_INVALID),
        (
            {"pattern": "a{999999999999999999999999999999999}"},
            DiagnosticCode.SCHEMA_META_INVALID,
        ),
        ({"patternProperties": {"[": {"type": "string"}}}, DiagnosticCode.SCHEMA_META_INVALID),
        (
            {
                "patternProperties": {
                    "a{999999999999999999999999999999999}": {"type": "string"}
                }
            },
            DiagnosticCode.SCHEMA_META_INVALID,
        ),
        ({"type": "not-a-json-schema-type"}, DiagnosticCode.SCHEMA_META_INVALID),
    ],
)
def test_dialect_identity_closed_language_format_regex_and_meta_schema(
    mutation: dict[str, object],
    expected: DiagnosticCode,
) -> None:
    schema = _schema()
    schema.update(mutation)
    result = build_schema_registry(
        (_binding(schema, schema_uri=f"{BASE}/family-a/1.0.0"),)
    )
    assert expected in _codes(result)
    assert all(diagnostic.phase == "REGISTRY_SCHEMA_META" for diagnostic in result)


def test_distinct_raw_bindings_with_same_meta_failure_are_not_deduplicated() -> None:
    schemas = (
        _schema(body={"$comment": "first", "unknownKeyword": True}),
        _schema(body={"$comment": "second", "unknownKeyword": True}),
    )
    bindings = tuple(_binding(schema) for schema in schemas)
    observations = {
        _serialized(build_schema_registry(order))
        for order in (bindings, tuple(reversed(bindings)))
    }
    assert len(observations) == 1
    result = build_schema_registry(bindings)
    assert _codes(result) == (
        DiagnosticCode.SCHEMA_META_INVALID,
        DiagnosticCode.SCHEMA_META_INVALID,
    )
    binding_observations = [
        diagnostic.to_dict()["details"]["binding_observation"]
        for diagnostic in result
    ]
    assert len({item["raw_sha256"] for item in binding_observations}) == 2
    assert {
        item["declared_schema_id"] for item in binding_observations
    } == {f"{BASE}/family-a/1.0.0"}


def test_nested_id_is_specific_but_keywords_inside_instance_data_are_not_walked() -> None:
    nested = _schema(body={"properties": {"x": {"$id": f"{BASE}/nested/1.0.0"}}})
    assert _codes(build_schema_registry((_binding(nested),))) == (
        DiagnosticCode.SCHEMA_ID_MISMATCH,
    )

    ordinary_data = _schema(
        body={
            "const": {"$id": "latest", "$ref": "https://example.invalid", "format": "email"},
            "default": {"unknownKeyword": True},
            "examples": [{"$dynamicRef": "#x"}],
            "enum": [{"$recursiveRef": "#"}],
        }
    )
    assert type(build_schema_registry((_binding(ordinary_data),))) is ContractSchemaRegistry


@pytest.mark.parametrize(
    "body",
    [
        {"$defs": {"x": {"unknown": True}}},
        {"properties": {"x": {"unknown": True}}},
        {"patternProperties": {"^x$": {"unknown": True}}},
        {"dependentSchemas": {"x": {"unknown": True}}},
        {"allOf": [{"unknown": True}]},
        {"anyOf": [{"unknown": True}]},
        {"oneOf": [{"unknown": True}]},
        {"prefixItems": [{"unknown": True}]},
        {"not": {"unknown": True}},
        {"if": {"unknown": True}},
        {"then": {"unknown": True}},
        {"else": {"unknown": True}},
        {"items": {"unknown": True}},
        {"contains": {"unknown": True}},
        {"additionalProperties": {"unknown": True}},
        {"propertyNames": {"unknown": True}},
        {"unevaluatedItems": {"unknown": True}},
        {"unevaluatedProperties": {"unknown": True}},
    ],
)
def test_every_typed_schema_container_is_walked(body: dict[str, object]) -> None:
    assert _codes(build_schema_registry((_binding(_schema(body=body)),))) == (
        DiagnosticCode.SCHEMA_META_INVALID,
    )


@pytest.mark.parametrize(
    "target",
    [
        "#/const",
        "#/$defs/x/const",
    ],
)
def test_refs_cannot_target_object_looking_ordinary_data(target: str) -> None:
    schema = _schema(
        body={
            "$defs": {"x": {"const": {"type": "string"}}},
            "const": {"type": "string"},
            "$ref": target,
        }
    )
    assert _codes(build_schema_registry((_binding(schema),))) == (
        DiagnosticCode.SCHEMA_UNRESOLVED_REF,
    )


@pytest.mark.parametrize("ordinary", [False, True, 1, "value", [True]])
def test_refs_cannot_target_scalar_boolean_or_array_ordinary_data(ordinary: object) -> None:
    schema = _schema(body={"const": ordinary, "$ref": "#/const"})
    assert _codes(build_schema_registry((_binding(schema),))) == (
        DiagnosticCode.SCHEMA_UNRESOLVED_REF,
    )


@pytest.mark.parametrize("leaf", [{"type": "string"}, True, False])
def test_refs_to_genuine_object_or_boolean_schema_locations_succeed(leaf: object) -> None:
    schema = _schema(body={"$defs": {"leaf": leaf}, "$ref": "#/$defs/leaf"})
    assert type(build_schema_registry((_binding(schema),))) is ContractSchemaRegistry


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        ("#", DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN),
        ("relative.json", DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN),
        ("../other", DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN),
        ("https://example.invalid/schema/1.0.0", DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN),
        (f"{BASE}/missing/1.0.0", DiagnosticCode.SCHEMA_UNRESOLVED_REF),
        ("#/$defs/~2bad", DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN),
        ("#/$defs/missing", DiagnosticCode.SCHEMA_UNRESOLVED_REF),
        (f"{BASE}/family-a/1.0.0?x=1", DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN),
        (f"{BASE}/family-a/1.0.0#/$defs/x#again", DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN),
        (f"{BASE}/family-a/1.0.0#/%78", DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN),
    ],
)
def test_ref_literals_fail_closed_without_aliases(reference: str, expected: DiagnosticCode) -> None:
    result = build_schema_registry((_binding(_schema(body={"$ref": reference})),))
    assert _codes(result) == (expected,)


def test_percent_fragment_is_forbidden_even_when_a_literal_property_exists() -> None:
    schema = _schema(
        body={"$defs": {"%78": {"type": "string"}}, "$ref": "#/$defs/%78"}
    )
    assert _codes(build_schema_registry((_binding(schema),))) == (
        DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN,
    )


def test_latest_path_segment_is_forbidden_in_schema_ids_and_refs() -> None:
    latest_id = f"{BASE}/latest/family-a/1.0.0"
    schema = _schema()
    schema["$id"] = latest_id
    assert _codes(build_schema_registry((_binding(schema, schema_uri=latest_id),))) == (
        DiagnosticCode.SCHEMA_ID_MISMATCH,
    )

    referencing = _schema(body={"$ref": latest_id})
    assert _codes(build_schema_registry((_binding(referencing),))) == (
        DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN,
    )


def test_external_exact_reference_and_very_large_pointer_are_offline_and_total() -> None:
    common = _schema("common", body={"$defs": {"leaf": {"type": "string"}}})
    family = _schema(
        "family-a",
        body={"$ref": f"{BASE}/common/1.0.0#/$defs/leaf"},
    )
    bindings = (
        _binding(common, asset_id="schema:common:1.0.0"),
        _binding(family),
    )
    assert type(build_schema_registry(bindings)) is ContractSchemaRegistry

    huge = _schema(body={"$ref": "#/$defs/" + ("9" * 4000)})
    assert _codes(build_schema_registry((_binding(huge),))) == (
        DiagnosticCode.SCHEMA_UNRESOLVED_REF,
    )


def test_containment_plus_reference_cycles_are_rejected_but_one_way_refs_pass() -> None:
    schema_id = f"{BASE}/family-a/1.0.0"
    cycle_all_of = _schema(body={"allOf": [{"$ref": schema_id}]})
    assert _codes(build_schema_registry((_binding(cycle_all_of),))) == (
        DiagnosticCode.SCHEMA_REFERENCE_CYCLE,
    )

    cycle_property = _schema(body={"properties": {"x": {"$ref": schema_id}}})
    assert _codes(build_schema_registry((_binding(cycle_property),))) == (
        DiagnosticCode.SCHEMA_REFERENCE_CYCLE,
    )

    one_way = _schema(
        body={
            "$defs": {"leaf": {"type": "string"}},
            "properties": {"x": {"$ref": "#/$defs/leaf"}},
        }
    )
    assert type(build_schema_registry((_binding(one_way),))) is ContractSchemaRegistry


def test_cross_resource_cycle_is_rejected() -> None:
    first = _schema("first", body={"$ref": f"{BASE}/second/1.0.0"})
    second = _schema("second", body={"$ref": f"{BASE}/first/1.0.0"})
    result = build_schema_registry(
        (
            _binding(first, asset_id="schema:first:1.0.0"),
            _binding(second, asset_id="schema:second:1.0.0"),
        )
    )
    assert _codes(result) == (DiagnosticCode.SCHEMA_REFERENCE_CYCLE,)


def test_disjoint_cycles_are_all_reported_without_downstream_nodes() -> None:
    ids = {name: f"{BASE}/{name}/1.0.0" for name in ("a", "b", "c", "d", "tail")}
    schemas = {
        "a": _schema("a", body={"$ref": ids["b"]}),
        "b": _schema(
            "b",
            body={
                "allOf": [{"$ref": ids["a"]}],
                "properties": {"tail": {"$ref": ids["tail"]}},
            },
        ),
        "c": _schema("c", body={"$ref": ids["d"]}),
        "d": _schema("d", body={"allOf": [{"$ref": ids["c"]}]}),
        "tail": _schema("tail", body={"type": "string"}),
    }
    bindings = tuple(
        _binding(schema, asset_id=f"schema:{name}:1.0.0")
        for name, schema in sorted(schemas.items())
    )
    observations = {
        _serialized(build_schema_registry(permutation))  # type: ignore[arg-type]
        for permutation in itertools.permutations(bindings)
    }
    assert len(observations) == 1
    result = build_schema_registry(bindings)
    assert _codes(result) == (
        DiagnosticCode.SCHEMA_REFERENCE_CYCLE,
        DiagnosticCode.SCHEMA_REFERENCE_CYCLE,
    )
    cycle_node_groups = [
        diagnostic.to_dict()["details"]["cycle_nodes"] for diagnostic in result
    ]
    assert all(
        ids["tail"] not in node
        and "/properties/tail" not in node
        for group in cycle_node_groups
        for node in group
    )
    assert any(ids["a"] in " ".join(group) and ids["b"] in " ".join(group) for group in cycle_node_groups)
    assert any(ids["c"] in " ".join(group) and ids["d"] in " ".join(group) for group in cycle_node_groups)


def test_duplicate_asset_and_schema_ids_are_order_independent() -> None:
    same_asset_a = _binding(_schema("first"), asset_id="schema:duplicate:1.0.0")
    same_asset_b = _binding(_schema("second"), asset_id="schema:duplicate:1.0.0")
    same_schema_a = _binding(_schema("shared"), asset_id="schema:shared-a:1.0.0")
    same_schema_b = _binding(_schema("shared"), asset_id="schema:shared-b:1.0.0")
    bindings = (same_asset_a, same_asset_b, same_schema_a, same_schema_b)
    observations = {
        _serialized(build_schema_registry(permutation))  # type: ignore[arg-type]
        for permutation in itertools.permutations(bindings)
    }
    assert len(observations) == 1
    result = build_schema_registry(bindings)
    assert _codes(result) == (
        DiagnosticCode.SCHEMA_DUPLICATE_ID,
        DiagnosticCode.SCHEMA_DUPLICATE_ID,
    )


def test_three_conflicting_bindings_have_complete_permutation_stable_details() -> None:
    bindings = tuple(
        _binding(
            _schema(body={"title": title}),
            asset_id="schema:triple:1.0.0",
        )
        for title in ("a", "longer-title", "the-longest-title-of-three")
    )
    observations = {
        _serialized(build_schema_registry(permutation))  # type: ignore[arg-type]
        for permutation in itertools.permutations(bindings)
    }
    assert len(observations) == 1
    result = build_schema_registry(bindings)
    assert _codes(result) == (
        DiagnosticCode.SCHEMA_DUPLICATE_ID,
        DiagnosticCode.SCHEMA_DUPLICATE_ID,
    )
    for diagnostic in result:
        details = diagnostic.to_dict()["details"]
        assert details["binding_count"] == 3
        assert len(details["observations"]) == 3
        assert all(
            set(observation) == {"asset_id", "byte_size", "schema_id", "sha256"}
            for observation in details["observations"]
        )


def test_asset_preflight_failures_suppress_global_duplicate_and_closure_checks() -> None:
    first = _binding(
        _schema(body={"$ref": f"{BASE}/missing/1.0.0"}),
        asset_id="schema:duplicate:1.0.0",
        ref_changes={"byte_size": 0},
    )
    second = _binding(
        _schema(body={"unknown": True}),
        asset_id="schema:duplicate:1.0.0",
    )
    result = build_schema_registry((first, second))
    assert _codes(result) == (
        DiagnosticCode.REF_HASH_MISMATCH,
        DiagnosticCode.SCHEMA_META_INVALID,
    )
    assert DiagnosticCode.SCHEMA_DUPLICATE_ID not in _codes(result)
    assert DiagnosticCode.SCHEMA_UNRESOLVED_REF not in _codes(result)


def test_meta_validation_ignores_process_global_regex_checker_pollution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    polluted = dict(FormatChecker.checkers)
    polluted["regex"] = (lambda value: False, ())
    monkeypatch.setattr(FormatChecker, "checkers", polluted)
    valid = _schema(body={"pattern": "^x$"})
    assert type(build_schema_registry((_binding(valid),))) is ContractSchemaRegistry

    FormatChecker.checkers["regex"] = (lambda value: True, ())
    invalid = _schema(body={"pattern": "["})
    assert _codes(build_schema_registry((_binding(invalid),))) == (
        DiagnosticCode.SCHEMA_META_INVALID,
    )


def test_meta_phase_aggregates_multiple_structural_errors_deterministically() -> None:
    bodies = (
        {"type": "bogus", "required": [1]},
        {"required": [1], "type": "bogus"},
    )
    observations = {
        _serialized(build_schema_registry((_binding(_schema(body=body)),)))
        for body in bodies
    }
    assert len(observations) == 1
    result = build_schema_registry((_binding(_schema(body=bodies[0])),))
    assert len(result) >= 2
    assert all(
        diagnostic.code is DiagnosticCode.SCHEMA_META_INVALID
        and diagnostic.phase == "REGISTRY_SCHEMA_META"
        for diagnostic in result
    )
    assert {diagnostic.json_pointer for diagnostic in result} >= {
        "/type",
        "/required/0",
    }


@pytest.mark.parametrize("exception", [RuntimeError("runtime"), OverflowError("overflow")])
def test_meta_validator_iterator_exceptions_are_diagnostic_only(
    monkeypatch: pytest.MonkeyPatch,
    exception: Exception,
) -> None:
    def fail(*args: object, **kwargs: object) -> object:
        raise exception

    monkeypatch.setattr(Draft202012Validator, "iter_errors", fail)
    result = build_schema_registry((_binding(_schema()),))
    assert _codes(result) == (DiagnosticCode.SCHEMA_META_INVALID,)
    assert result[0].message == (
        "schema cannot be safely checked by the locked Draft 2020-12 implementation"
    )


def test_registry_build_never_uses_path_network_git_or_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = _binding(_schema())

    def forbidden(*args: object, **kwargs: object) -> Any:
        raise AssertionError("pure registry attempted external I/O")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert type(build_schema_registry((binding,))) is ContractSchemaRegistry


def test_all_committed_common_schemas_form_one_offline_graph() -> None:
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
        bindings.append(
            _binding(
                document,
                asset_id=f"schema:common:{path.parent.name}:1.0.0",
                raw=raw,
            )
        )
    result = build_schema_registry(tuple(reversed(bindings)))
    assert type(result) is ContractSchemaRegistry
    assert len(result.schema_ids) == 8


def test_registry_snapshots_survive_caller_mutation() -> None:
    binding = _binding(_schema())
    registry = build_schema_registry((binding,))
    assert type(registry) is ContractSchemaRegistry
    object.__setattr__(binding.supplied_asset, "raw_bytes", b"tampered")
    object.__setattr__(binding.exact_ref, "_ParsedCanonicalValue__node", {"host": "dict"})
    assert registry.schema_ids == (f"{BASE}/family-a/1.0.0",)


def test_phase_gate_suppresses_parse_and_closure_noise_after_binding_failure() -> None:
    invalid = _schema(body={"$ref": f"{BASE}/missing/1.0.0"})
    binding = _binding(invalid, ref_changes={"byte_size": 0})
    result = build_schema_registry((binding,))
    assert _codes(result) == (DiagnosticCode.REF_HASH_MISMATCH,)
    assert result[0].phase == "REGISTRY_EXACT_BINDING"


def test_diagnostic_details_are_frozen_and_serialize_as_json() -> None:
    diagnostic = Diagnostic(
        DiagnosticCode.SCHEMA_DUPLICATE_ID,
        "duplicate",
        details={"observations": [{"id": "a"}]},
    )
    details = diagnostic.to_dict()["details"]
    assert details == {"observations": [{"id": "a"}]}
    details["observations"][0]["id"] = "changed"
    assert diagnostic.to_dict()["details"] == {"observations": [{"id": "a"}]}

    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(TypeError, match="cycle"):
        Diagnostic(DiagnosticCode.SCHEMA_DUPLICATE_ID, "cycle", details=cyclic)

    with pytest.raises(TypeError, match="I-JSON"):
        Diagnostic(
            DiagnosticCode.SCHEMA_DUPLICATE_ID,
            "integer",
            details={"value": 9_007_199_254_740_992},
        )

    normalized = Diagnostic(
        DiagnosticCode.SCHEMA_DUPLICATE_ID,
        "normalized",
        details={"e\u0301": "a\r\nb\rc"},
    )
    assert normalized.to_dict()["details"] == {"é": "a\nb\nc"}
    with pytest.raises(TypeError, match="collide"):
        Diagnostic(
            DiagnosticCode.SCHEMA_DUPLICATE_ID,
            "collision",
            details={"é": 1, "e\u0301": 2},
        )
