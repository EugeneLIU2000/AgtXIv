from __future__ import annotations

import builtins
import dataclasses
import importlib
import itertools
import json
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import FormatChecker


def _add_local_src_package() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    source_root = repository_root / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    return repository_root


_add_local_src_package()

import agtxiv_v2.contracts.schema_validation as schema_validation_module  # noqa: E402
import agtxiv_v2.contracts.registry as registry_module  # noqa: E402
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
    record_content_hash,
    validate_immutable_record_payload,
)


DIALECT = "https://json-schema.org/draft/2020-12/schema"
BASE = "https://agtxiv.org/schema/v2/contract-kernel/example"
FAMILY_ID = f"{BASE}/family-a/1.0.0"
RECORD_TYPE = "agtxiv.example-family/1.0.0"


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


def _family_schema(
    *,
    schema_id: str = FAMILY_ID,
    record_type: object = RECORD_TYPE,
    payload_schema: object | None = None,
    extra_defs: dict[str, object] | None = None,
) -> dict[str, object]:
    definitions: dict[str, object] = {
        "recordType": {"const": record_type},
        "payload": (
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["value"],
                "properties": {"value": {"type": "integer"}},
            }
            if payload_schema is None
            else payload_schema
        ),
    }
    definitions.update(extra_defs or {})
    return {
        "$schema": DIALECT,
        "$id": schema_id,
        "$defs": definitions,
    }


def _binding(
    schema: dict[str, object],
    *,
    asset_id: str = "schema:family-a:1.0.0",
) -> SchemaAssetBinding:
    raw = _raw(schema)
    schema_id = schema["$id"]
    assert type(schema_id) is str
    ref = {
        "asset_id": asset_id,
        "media_type": "application/schema+json",
        "byte_size": len(raw),
        "sha256": raw_asset_sha256(raw),
        "schema_uri": schema_id,
    }
    return SchemaAssetBinding(
        _parsed(ref),
        SuppliedAsset(
            asset_id,
            "application/schema+json",
            raw,
            schema_id,
        ),
    )


def _registry(
    schema: dict[str, object] | None = None,
    *extra_bindings: SchemaAssetBinding,
) -> tuple[ContractSchemaRegistry, SchemaAssetBinding]:
    binding = _binding(_family_schema() if schema is None else schema)
    result = build_schema_registry((binding, *extra_bindings))
    assert type(result) is ContractSchemaRegistry, result
    return result, binding


def _dummy_schema_ref() -> dict[str, object]:
    return {
        "asset_id": "schema:contract-bundle-release:1.0.0",
        "media_type": "application/schema+json",
        "byte_size": 1,
        "sha256": "sha256:" + ("1" * 64),
        "schema_uri": (
            "https://agtxiv.org/schema/v2/contract-kernel/contract/"
            "contract-bundle-release/1.0.0"
        ),
    }


def _bundle_ref() -> dict[str, object]:
    return {
        "record_type": "agtxiv.contract-bundle-release/1.0.0",
        "record_id": "contract-bundle-release:test-1",
        "record_revision": 1,
        "schema_ref": _dummy_schema_ref(),
        "content_hash": "sha256:" + ("2" * 64),
    }


def _record(
    binding: SchemaAssetBinding,
    *,
    payload: object = None,
    record_type: str = RECORD_TYPE,
    envelope_changes: dict[str, object] | None = None,
    content_hash: str | None = None,
    outer_changes: dict[str, object] | None = None,
) -> ParsedCanonicalValue:
    envelope: dict[str, object] = {
        "record_type": record_type,
        "schema_ref": binding.exact_ref.to_python(),
        "record_id": "example-family:test-1",
        "record_revision": 1,
        "contract_bundle_ref": _bundle_ref(),
        "created_at": "2026-08-31T12:34:56Z",
    }
    envelope.update(envelope_changes or {})
    document: dict[str, object] = {
        "envelope": envelope,
        "payload": {"value": 1} if payload is None else payload,
    }
    document.update(outer_changes or {})
    without_hash = _parsed(document)
    computed = record_content_hash(without_hash)
    if not isinstance(computed, str):
        assert outer_changes
        computed = "sha256:" + ("0" * 64)
    document["content_hash"] = computed if content_hash is None else content_hash
    return _parsed(document)


def _codes(result: tuple[Diagnostic, ...]) -> tuple[DiagnosticCode, ...]:
    assert type(result) is tuple
    assert all(type(item) is Diagnostic for item in result)
    return tuple(item.code for item in result)


def _serialized(result: tuple[Diagnostic, ...]) -> bytes:
    return _raw([diagnostic.to_dict() for diagnostic in result])


def test_record_diagnostic_codes_are_locked() -> None:
    assert str(DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH) == (
        "AGTXIV.RECORD.TYPE_SCHEMA_MISMATCH"
    )
    assert str(DiagnosticCode.RECORD_PAYLOAD_INVALID) == "AGTXIV.RECORD.PAYLOAD_INVALID"


def test_valid_generic_record_checks_envelope_schema_type_payload_and_hash() -> None:
    registry, binding = _registry()
    assert validate_immutable_record_payload(_record(binding), registry) == ()


@pytest.mark.parametrize("record", [{}, object(), None])
def test_wrong_record_runtime_type_returns_one_input_diagnostic(record: object) -> None:
    registry, _ = _registry()
    result = validate_immutable_record_payload(record, registry)  # type: ignore[arg-type]
    assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


@pytest.mark.parametrize("registry", [{}, object(), None])
def test_wrong_registry_runtime_type_returns_one_input_diagnostic(registry: object) -> None:
    _, binding = _registry()
    result = validate_immutable_record_payload(
        _record(binding),
        registry,  # type: ignore[arg-type]
    )
    assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


def test_forged_record_and_registry_are_diagnostic_only() -> None:
    registry, binding = _registry()
    record = _record(binding)
    object.__setattr__(record, "_ParsedCanonicalValue__node", {"host": "dict"})
    assert _codes(validate_immutable_record_payload(record, registry)) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )

    forged_registry = object.__new__(ContractSchemaRegistry)
    assert _codes(
        validate_immutable_record_payload(_record(binding), forged_registry)
    ) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


def test_top_level_and_envelope_failures_gate_schema_type_and_payload() -> None:
    registry, binding = _registry()

    outer = _record(binding, outer_changes={"extra": True})
    assert _codes(validate_immutable_record_payload(outer, registry)) == (
        DiagnosticCode.RECORD_INVALID_ENVELOPE,
    )

    invalid_envelope = _record(
        binding,
        envelope_changes={"record_revision": 0},
        content_hash="sha256:" + ("0" * 64),
    )
    result = validate_immutable_record_payload(invalid_envelope, registry)
    assert _codes(result) == (
        DiagnosticCode.RECORD_INVALID_ENVELOPE,
        DiagnosticCode.RECORD_HASH_MISMATCH,
    )
    assert all(code is not DiagnosticCode.RECORD_PAYLOAD_INVALID for code in _codes(result))
    assert result[0].json_pointer == "/envelope/record_revision"


def test_non_object_envelope_still_allows_independent_hash_validation() -> None:
    registry, _ = _registry()
    record = _parsed(
        {
            "envelope": [],
            "payload": {},
            "content_hash": "sha256:" + ("0" * 64),
        }
    )
    result = validate_immutable_record_payload(record, registry)
    assert _codes(result) == (
        DiagnosticCode.RECORD_INVALID_ENVELOPE,
        DiagnosticCode.RECORD_HASH_MISMATCH,
    )
    assert [diagnostic.phase for diagnostic in result] == [
        "RECORD_ENVELOPE",
        "RECORD_HASH",
    ]
    assert [diagnostic.json_pointer for diagnostic in result] == [
        "/envelope",
        "/content_hash",
    ]


@pytest.mark.parametrize(
    ("schema_ref_change", "expected"),
    [
        ({"asset_id": "schema:missing:1.0.0"}, DiagnosticCode.REF_UNRESOLVED),
        ({"media_type": "application/json"}, DiagnosticCode.RECORD_INVALID_ENVELOPE),
        ({"byte_size": 0}, DiagnosticCode.REF_HASH_MISMATCH),
        ({"sha256": "sha256:" + ("0" * 64)}, DiagnosticCode.REF_HASH_MISMATCH),
        (
            {"schema_uri": f"{BASE}/other/1.0.0"},
            DiagnosticCode.REF_TYPE_MISMATCH,
        ),
    ],
)
def test_exact_schema_binding_failure_gates_type_and_payload(
    schema_ref_change: dict[str, object],
    expected: DiagnosticCode,
) -> None:
    registry, binding = _registry()
    schema_ref = binding.exact_ref.to_python()
    schema_ref.update(schema_ref_change)
    record = _record(binding, envelope_changes={"schema_ref": schema_ref})
    result = validate_immutable_record_payload(record, registry)
    assert _codes(result) == (expected,)


def test_type_binding_failure_gates_payload() -> None:
    registry, binding = _registry()
    record = _record(binding, record_type="agtxiv.other-family/1.0.0", payload={})
    assert _codes(validate_immutable_record_payload(record, registry)) == (
        DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH,
    )


def test_component_schema_cannot_validate_a_record() -> None:
    component = {
        "$schema": DIALECT,
        "$id": FAMILY_ID,
        "$defs": {"leaf": {"type": "string"}},
    }
    registry, binding = _registry(component)
    assert _codes(validate_immutable_record_payload(_record(binding), registry)) == (
        DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH,
    )


def test_missing_payload_entry_is_payload_invalid_after_type_binding() -> None:
    schema = {
        "$schema": DIALECT,
        "$id": FAMILY_ID,
        "$defs": {"recordType": {"const": RECORD_TYPE}},
    }
    registry, binding = _registry(schema)
    assert _codes(validate_immutable_record_payload(_record(binding), registry)) == (
        DiagnosticCode.RECORD_PAYLOAD_INVALID,
    )


def test_payload_and_hash_failures_are_independent_and_phase_sorted() -> None:
    registry, binding = _registry()
    record = _record(
        binding,
        payload={"value": "wrong", "extra": True},
        content_hash="sha256:" + ("0" * 64),
    )
    result = validate_immutable_record_payload(record, registry)
    assert _codes(result) == (
        DiagnosticCode.RECORD_PAYLOAD_INVALID,
        DiagnosticCode.RECORD_PAYLOAD_INVALID,
        DiagnosticCode.RECORD_HASH_MISMATCH,
    )
    assert [diagnostic.phase for diagnostic in result] == [
        "RECORD_PAYLOAD",
        "RECORD_PAYLOAD",
        "RECORD_HASH",
    ]


@pytest.mark.parametrize("required", [["a", "b"], ["b", "a"]])
def test_each_missing_required_property_has_a_distinct_stable_diagnostic(
    required: list[str],
) -> None:
    schema = _family_schema(
        payload_schema={
            "type": "object",
            "required": required,
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        }
    )
    registry, binding = _registry(schema)
    record = _record(binding, payload={})
    observations = {
        _serialized(validate_immutable_record_payload(record, registry))
        for _ in range(10)
    }
    assert len(observations) == 1
    result = validate_immutable_record_payload(record, registry)
    assert len(result) == 2
    assert {diagnostic.json_pointer for diagnostic in result} == {
        "/payload/a",
        "/payload/b",
    }
    assert {
        diagnostic.to_dict()["details"]["required_property"]
        for diagnostic in result
    } == {"a", "b"}
    expected_schema_pointers = {
        f"/$defs/payload/required/{required.index(name)}" for name in ("a", "b")
    }
    assert {diagnostic.schema_pointer for diagnostic in result} == expected_schema_pointers


def test_each_missing_dependent_property_has_a_distinct_stable_diagnostic() -> None:
    schema = _family_schema(
        payload_schema={
            "type": "object",
            "dependentRequired": {"trigger": ["a", "b"]},
        }
    )
    registry, binding = _registry(schema)
    result = validate_immutable_record_payload(
        _record(binding, payload={"trigger": True}),
        registry,
    )
    assert len(result) == 2
    assert {diagnostic.json_pointer for diagnostic in result} == {
        "/payload/a",
        "/payload/b",
    }
    assert {diagnostic.schema_pointer for diagnostic in result} == {
        "/$defs/payload/dependentRequired/trigger/0",
        "/$defs/payload/dependentRequired/trigger/1",
    }
    assert {
        (
            diagnostic.to_dict()["details"]["trigger_property"],
            diagnostic.to_dict()["details"]["required_property"],
        )
        for diagnostic in result
    } == {("trigger", "a"), ("trigger", "b")}


def test_required_diagnostic_expansion_is_linear_not_quadratic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_count = 40
    names = [f"field_{index:02d}" for index in range(property_count)]
    schema = _family_schema(
        payload_schema={
            "type": "object",
            "required": names,
            "properties": {name: {"type": "integer"} for name in names},
        }
    )
    registry, binding = _registry(schema)
    original = schema_validation_module._diagnostic
    calls = 0

    def counted(*args: object, **kwargs: object) -> Diagnostic:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(schema_validation_module, "_diagnostic", counted)
    result = validate_immutable_record_payload(_record(binding, payload={}), registry)
    assert len(result) == property_count
    assert calls == property_count


def test_payload_local_ref_keeps_family_resource_base() -> None:
    schema = _family_schema(
        payload_schema={"$ref": "#/$defs/payloadBody"},
        extra_defs={
            "payloadBody": {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
                "additionalProperties": False,
            }
        },
    )
    registry, binding = _registry(schema)
    assert validate_immutable_record_payload(
        _record(binding, payload={"name": "Ada"}),
        registry,
    ) == ()
    assert _codes(
        (invalid := validate_immutable_record_payload(
            _record(binding, payload={"name": 1}),
            registry,
        ))
    ) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)
    assert invalid[0].schema_pointer == "/$defs/payloadBody/properties/name/type"
    assert invalid[0].to_dict()["details"]["schema_id"] == FAMILY_ID


def test_two_payload_families_can_share_an_exact_component_schema() -> None:
    shared_id = f"{BASE}/shared/1.0.0"
    shared_schema = {
        "$schema": DIALECT,
        "$id": shared_id,
        "$defs": {"name": {"type": "string", "minLength": 1}},
    }
    shared_binding = _binding(shared_schema, asset_id="schema:shared:1.0.0")
    family = _family_schema(
        payload_schema={
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"$ref": f"{shared_id}#/$defs/name"}},
        }
    )
    registry, binding = _registry(family, shared_binding)
    assert validate_immutable_record_payload(
        _record(binding, payload={"name": "Ada"}),
        registry,
    ) == ()
    invalid = validate_immutable_record_payload(
        _record(binding, payload={"name": 1}),
        registry,
    )
    assert _codes(invalid) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)
    assert invalid[0].schema_pointer == "/$defs/name/type"
    assert invalid[0].to_dict()["details"]["schema_id"] == shared_id


def test_false_boolean_payload_schema_has_one_exact_original_location() -> None:
    registry, binding = _registry(_family_schema(payload_schema=False))
    result = validate_immutable_record_payload(_record(binding, payload={}), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)
    assert result[0].schema_pointer == "/$defs/payload"
    assert result[0].to_dict()["details"] == {
        "location_status": "EXACT_BOOLEAN_SCHEMA_NODE",
        "schema_id": FAMILY_ID,
        "validator": "false-schema",
    }


@pytest.mark.parametrize(
    ("format_name", "accepted", "rejected"),
    [
        (
            "uri",
            ["https://example.org/a?b=c#d", "urn:example:paper", "https://[::1]/"],
            ["relative/path", "https://exa mple.org", "https://example.org/%ZZ", "https://example.org\n"],
        ),
        (
            "date-time",
            [
                "2026-08-31T12:34:56Z",
                "2026-08-31T12:34:56.123+02:30",
                "2026-08-31t12:34:56z",
            ],
            ["2026-02-30T00:00:00Z", "2026-08-31T23:59:60Z", "2026-08-31 00:00:00Z", "2026-08-31T00:00:00Z\n"],
        ),
    ],
)
def test_fixed_uri_and_date_time_vectors(
    format_name: str,
    accepted: list[str],
    rejected: list[str],
) -> None:
    schema = _family_schema(
        payload_schema={"type": "string", "format": format_name}
    )
    registry, binding = _registry(schema)
    for value in accepted:
        assert validate_immutable_record_payload(
            _record(binding, payload=value), registry
        ) == (), value
    for value in rejected:
        assert _codes(
            validate_immutable_record_payload(
                _record(binding, payload=value), registry
            )
        ) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,), value


def test_process_global_format_checker_mutation_before_reload_and_validation_is_irrelevant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    polluted = dict(FormatChecker.checkers)
    polluted["uri"] = (lambda value: True, ())
    polluted["date-time"] = (lambda value: True, ())
    polluted["regex"] = (lambda value: False, ())
    monkeypatch.setattr(FormatChecker, "checkers", polluted)
    module = importlib.reload(schema_validation_module)

    schema = _family_schema(payload_schema={"type": "string", "format": "uri"})
    registry, binding = _registry(schema)
    invalid = _record(binding, payload="relative/path")
    first = module.validate_immutable_record_payload(invalid, registry)

    FormatChecker.checkers["uri"] = (lambda value: True, ())
    FormatChecker.checkers["date-time"] = (lambda value: True, ())
    FormatChecker.checkers["regex"] = (lambda value: True, ())
    second = module.validate_immutable_record_payload(invalid, registry)
    assert _serialized(first) == _serialized(second)
    assert _codes(first) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize(
    ("format_name", "dependency_name", "exception"),
    [
        ("uri", "validate_rfc3986", OverflowError("overflow")),
        ("date-time", "validate_rfc3339", IndexError("index")),
    ],
)
def test_format_dependency_exceptions_become_payload_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    format_name: str,
    dependency_name: str,
    exception: Exception,
) -> None:
    schema = _family_schema(payload_schema={"type": "string", "format": format_name})
    registry, binding = _registry(schema)

    def fail(*args: object, **kwargs: object) -> bool:
        raise exception

    monkeypatch.setattr(schema_validation_module, dependency_name, fail)
    result = validate_immutable_record_payload(
        _record(binding, payload="https://example.org"),
        registry,
    )
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize(
    "value",
    [
        "https://example.org/\x00",
        "https://example.org/\x85",
        "https://example.org/é",
    ],
    ids=["c0", "c1", "non-ascii"],
)
def test_uri_format_rejects_non_ascii_and_control_characters(value: str) -> None:
    schema = _family_schema(payload_schema={"type": "string", "format": "uri"})
    registry, binding = _registry(schema)
    assert _codes(
        validate_immutable_record_payload(_record(binding, payload=value), registry)
    ) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


def test_uri_format_handles_a_very_long_ascii_value_without_exception() -> None:
    schema = _family_schema(payload_schema={"type": "string", "format": "uri"})
    registry, binding = _registry(schema)
    value = "https://example.org/" + ("a" * 100_000)
    assert validate_immutable_record_payload(_record(binding, payload=value), registry) == ()


def test_validation_never_uses_path_network_git_or_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, binding = _registry()
    record = _record(binding)

    def forbidden(*args: object, **kwargs: object) -> Any:
        raise AssertionError("pure record validation attempted external I/O")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert validate_immutable_record_payload(record, registry) == ()


def test_record_and_schema_insertion_order_do_not_change_diagnostics() -> None:
    schema = _family_schema(
        payload_schema={
            "type": "object",
            "required": ["a", "b"],
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        }
    )
    registry, binding = _registry(schema)
    payload_items = (("b", "wrong"), ("a", "wrong"))
    observations: set[bytes] = set()
    for permutation in itertools.permutations(payload_items):
        record = _record(binding, payload=dict(permutation))
        for _ in range(5):
            observations.add(
                _serialized(validate_immutable_record_payload(record, registry))
            )
    assert len(observations) == 1


def test_registry_snapshot_is_not_changed_by_original_asset_mutation() -> None:
    registry, binding = _registry()
    record = _record(binding)
    object.__setattr__(binding.supplied_asset, "raw_bytes", b"tampered")
    object.__setattr__(binding.supplied_asset, "schema_uri", f"{BASE}/other/1.0.0")
    assert validate_immutable_record_payload(record, registry) == ()


def test_mutated_registry_internals_fail_closed() -> None:
    registry, binding = _registry()
    object.__setattr__(registry, "_ContractSchemaRegistry__entries", ())
    assert _codes(validate_immutable_record_payload(_record(binding), registry)) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )


@pytest.mark.parametrize("corruption", ["cycle", "deep"])
def test_cyclic_or_deep_frozen_registry_snapshot_fails_closed(corruption: str) -> None:
    registry, binding = _registry()
    entries = object.__getattribute__(
        registry,
        "_ContractSchemaRegistry__entries",
    )
    entry = entries[0]
    if corruption == "cycle":
        frozen = object.__new__(registry_module._FrozenObject)
        object.__setattr__(frozen, "pairs", (("x", frozen),))
    else:
        frozen = 0
        for _ in range(258):
            frozen = registry_module._FrozenObject((("x", frozen),))
    corrupted_entry = dataclasses.replace(entry, document=frozen)
    object.__setattr__(
        registry,
        "_ContractSchemaRegistry__entries",
        (corrupted_entry,),
    )
    result = validate_immutable_record_payload(_record(binding), registry)
    assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


@pytest.mark.parametrize(
    "field",
    ["asset_id", "media_type", "byte_size", "sha256", "schema_id", "raw_bytes", "document"],
)
def test_hostile_registry_field_is_rejected_before_any_protocol_call(field: str) -> None:
    registry, binding = _registry()
    record = _record(binding)
    entries = object.__getattribute__(registry, "_ContractSchemaRegistry__entries")

    class Hostile:
        def __str__(self) -> str:
            raise RuntimeError("str must not run")

        def __len__(self) -> int:
            raise RuntimeError("len must not run")

        def __iter__(self) -> object:
            raise RuntimeError("iter must not run")

        def __eq__(self, other: object) -> bool:
            raise RuntimeError("eq must not run")

        def encode(self, *args: object, **kwargs: object) -> bytes:
            raise RuntimeError("encode must not run")

    corrupted_entry = dataclasses.replace(entries[0], **{field: Hostile()})
    object.__setattr__(
        registry,
        "_ContractSchemaRegistry__entries",
        (corrupted_entry,),
    )
    result = validate_immutable_record_payload(record, registry)
    assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)
