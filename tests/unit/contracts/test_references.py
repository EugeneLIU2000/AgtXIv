from __future__ import annotations

import builtins
import copy
import sys
from pathlib import Path

import pytest


def _add_local_src_package() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    source_root = repository_root / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    return repository_root


_add_local_src_package()

from agtxiv_v2.contracts import (  # noqa: E402
    MAX_NESTING,
    Diagnostic,
    DiagnosticCode,
    ParsedCanonicalValue,
    SuppliedAsset,
    build_canonical_value,
    raw_asset_sha256,
    record_content_hash,
    resolve_exact_asset_ref,
    resolve_exact_component_ref,
    resolve_exact_record_ref,
    validate_immutable_envelope,
    validate_immutable_record,
)


SCHEMA_BYTES = b'{"type":"object"}'
SCHEMA_URI = (
    "https://agtxiv.org/schema/v2/contract-kernel/planning/agentization-plan/1.0.0"
)
BUNDLE_SCHEMA_URI = (
    "https://agtxiv.org/schema/v2/contract-kernel/contract/"
    "contract-bundle-release/1.0.0"
)


def _parsed(value: object) -> ParsedCanonicalValue:
    built = build_canonical_value(value)
    assert isinstance(built, ParsedCanonicalValue), built
    return built


def _schema_asset_ref(
    *,
    asset_id: str = "schema:agentization-plan:1.0.0",
    schema_uri: str = SCHEMA_URI,
    path_hint: str | None = None,
) -> dict[str, object]:
    ref: dict[str, object] = {
        "asset_id": asset_id,
        "media_type": "application/schema+json",
        "byte_size": len(SCHEMA_BYTES),
        "sha256": raw_asset_sha256(SCHEMA_BYTES),
        "schema_uri": schema_uri,
    }
    if path_hint is not None:
        ref["path_hint"] = path_hint
    return ref


def _schema_asset() -> SuppliedAsset:
    return SuppliedAsset(
        asset_id="schema:agentization-plan:1.0.0",
        media_type="application/schema+json",
        raw_bytes=SCHEMA_BYTES,
        schema_uri=SCHEMA_URI,
    )


def _bundle_ref() -> dict[str, object]:
    return {
        "record_type": "agtxiv.contract-bundle-release/1.0.0",
        "record_id": "contract-bundle-release:fixture-1",
        "record_revision": 1,
        "schema_ref": _schema_asset_ref(
            asset_id="schema:contract-bundle-release:1.0.0",
            schema_uri=BUNDLE_SCHEMA_URI,
        ),
        "content_hash": "sha256:" + ("1" * 64),
    }


def _envelope(
    *,
    revision: int = 1,
    schema_ref: dict[str, object] | None = None,
) -> dict[str, object]:
    envelope: dict[str, object] = {
        "record_type": "agtxiv.agentization-plan/1.0.0",
        "schema_ref": schema_ref or _schema_asset_ref(),
        "record_id": "agentization-plan:fixture-1",
        "record_revision": revision,
        "contract_bundle_ref": _bundle_ref(),
        "created_at": "2026-08-31T00:00:00Z",
    }
    if revision > 1:
        envelope["supersedes_ref"] = {
            "record_type": envelope["record_type"],
            "record_id": envelope["record_id"],
            "record_revision": revision - 1,
            "schema_ref": envelope["schema_ref"],
            "content_hash": "sha256:" + ("2" * 64),
        }
    return envelope


def _record(
    *,
    payload: object | None = None,
    revision: int = 1,
    schema_ref: dict[str, object] | None = None,
) -> ParsedCanonicalValue:
    without_hash = _parsed(
        {
            "envelope": _envelope(revision=revision, schema_ref=schema_ref),
            "payload": {} if payload is None else payload,
        }
    )
    content_hash = record_content_hash(without_hash)
    assert isinstance(content_hash, str)
    return _parsed(
        {
            "envelope": _envelope(revision=revision, schema_ref=schema_ref),
            "payload": {} if payload is None else payload,
            "content_hash": content_hash,
        }
    )


def _record_ref(
    record: ParsedCanonicalValue,
    *,
    schema_ref: dict[str, object] | None = None,
) -> ParsedCanonicalValue:
    document = record.to_python()
    envelope = document["envelope"]
    return _parsed(
        {
            "record_type": envelope["record_type"],
            "record_id": envelope["record_id"],
            "record_revision": envelope["record_revision"],
            "schema_ref": schema_ref or envelope["schema_ref"],
            "content_hash": document["content_hash"],
        }
    )


def _assert_diagnostic(result: object, code: DiagnosticCode) -> Diagnostic:
    assert isinstance(result, Diagnostic)
    assert result.code is code
    return result


def test_stable_reference_and_envelope_diagnostic_codes_are_locked() -> None:
    assert str(DiagnosticCode.REF_UNRESOLVED) == "AGTXIV.REF.UNRESOLVED"
    assert str(DiagnosticCode.REF_HASH_MISMATCH) == "AGTXIV.REF.HASH_MISMATCH"
    assert str(DiagnosticCode.REF_TYPE_MISMATCH) == "AGTXIV.REF.TYPE_MISMATCH"
    assert str(DiagnosticCode.CONTRACT_MUTABLE_REF) == "AGTXIV.CONTRACT.MUTABLE_REF"
    assert str(DiagnosticCode.RECORD_INVALID_ENVELOPE) == "AGTXIV.RECORD.INVALID_ENVELOPE"
    assert str(DiagnosticCode.RECORD_SUPERSESSION_MISMATCH) == (
        "AGTXIV.RECORD.SUPERSESSION_MISMATCH"
    )
    assert str(DiagnosticCode.RECORD_HASH_MISMATCH) == "AGTXIV.RECORD.HASH_MISMATCH"


def test_raw_asset_hash_is_over_original_bytes_not_canonical_json() -> None:
    pretty = b'{\n  "a": 1\n}\n'
    compact = b'{"a":1}'
    assert raw_asset_sha256(pretty) != raw_asset_sha256(compact)
    with pytest.raises(TypeError, match="requires bytes"):
        raw_asset_sha256("bytes")  # type: ignore[arg-type]


def test_exact_asset_ref_resolves_only_one_supplied_raw_byte_target() -> None:
    target = SuppliedAsset(
        asset_id="schema:agentization-plan:1.0.0",
        media_type="application/schema+json",
        raw_bytes=SCHEMA_BYTES,
        schema_uri=SCHEMA_URI,
    )
    ref = _parsed(_schema_asset_ref(path_hint="does/not/need/to/exist.json"))
    assert resolve_exact_asset_ref(ref, (target,)) is target

    _assert_diagnostic(
        resolve_exact_asset_ref(ref, (target, target)),
        DiagnosticCode.REF_UNRESOLVED,
    )
    _assert_diagnostic(resolve_exact_asset_ref(ref, ()), DiagnosticCode.REF_UNRESOLVED)


def test_supplied_asset_index_is_fully_validated_before_matching() -> None:
    ref = _parsed(_schema_asset_ref())
    target = _schema_asset()

    _assert_diagnostic(
        resolve_exact_asset_ref(ref, [target]),  # type: ignore[arg-type]
        DiagnosticCode.REF_TYPE_MISMATCH,
    )
    _assert_diagnostic(
        resolve_exact_asset_ref(ref, (object(),)),  # type: ignore[arg-type]
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    class SuppliedAssetSubclass(SuppliedAsset):
        __slots__ = ()

    subclass = SuppliedAssetSubclass(
        target.asset_id,
        target.media_type,
        target.raw_bytes,
        target.schema_uri,
    )
    _assert_diagnostic(
        resolve_exact_asset_ref(ref, (subclass,)),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    incomplete = object.__new__(SuppliedAsset)
    _assert_diagnostic(
        resolve_exact_asset_ref(ref, (incomplete,)),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    for field, invalid_value in (
        ("asset_id", []),
        ("media_type", object()),
        ("raw_bytes", "not-bytes"),
        ("schema_uri", "https://example.invalid/latest"),
    ):
        malformed = _schema_asset()
        object.__setattr__(malformed, field, invalid_value)
        _assert_diagnostic(
            resolve_exact_asset_ref(ref, (malformed,)),
            DiagnosticCode.REF_TYPE_MISMATCH,
        )


def test_supplied_asset_ids_are_globally_unique_before_target_matching() -> None:
    ref = _parsed(_schema_asset_ref())
    unrelated_first = SuppliedAsset(
        "asset:unrelated:1.0.0",
        "application/octet-stream",
        b"first",
    )
    unrelated_second = SuppliedAsset(
        "asset:unrelated:1.0.0",
        "application/octet-stream",
        b"second",
    )
    result = resolve_exact_asset_ref(
        ref,
        (_schema_asset(), unrelated_first, unrelated_second),
    )
    diagnostic = _assert_diagnostic(result, DiagnosticCode.REF_UNRESOLVED)
    assert diagnostic.json_pointer == "/supplied_assets/2/asset_id"


def test_schema_uri_is_a_one_way_assertion_and_never_a_locator() -> None:
    ref_without_uri = _schema_asset_ref()
    ref_without_uri.pop("schema_uri")
    target_with_uri = _schema_asset()
    assert resolve_exact_asset_ref(_parsed(ref_without_uri), (target_with_uri,)) is target_with_uri

    target_without_uri = SuppliedAsset(
        target_with_uri.asset_id,
        target_with_uri.media_type,
        target_with_uri.raw_bytes,
    )
    _assert_diagnostic(
        resolve_exact_asset_ref(_parsed(_schema_asset_ref()), (target_without_uri,)),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    different_uri_target = SuppliedAsset(
        target_with_uri.asset_id,
        target_with_uri.media_type,
        target_with_uri.raw_bytes,
        "https://agtxiv.org/schema/v2/contract-kernel/planning/other/1.0.0",
    )
    _assert_diagnostic(
        resolve_exact_asset_ref(_parsed(_schema_asset_ref()), (different_uri_target,)),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )


@pytest.mark.parametrize(
    ("field", "replacement", "expected_code"),
    [
        ("sha256", "sha256:" + ("0" * 64), DiagnosticCode.REF_HASH_MISMATCH),
        ("byte_size", len(SCHEMA_BYTES) + 1, DiagnosticCode.REF_HASH_MISMATCH),
        ("media_type", "application/json", DiagnosticCode.REF_TYPE_MISMATCH),
    ],
)
def test_exact_asset_ref_rejects_stale_hash_size_or_type(
    field: str,
    replacement: object,
    expected_code: DiagnosticCode,
) -> None:
    target = SuppliedAsset(
        "schema:agentization-plan:1.0.0",
        "application/schema+json",
        SCHEMA_BYTES,
        SCHEMA_URI,
    )
    ref_value = _schema_asset_ref()
    ref_value[field] = replacement
    _assert_diagnostic(resolve_exact_asset_ref(_parsed(ref_value), (target,)), expected_code)


def test_digest_free_or_locator_augmented_asset_ref_fails_as_mutable() -> None:
    for mutation in (
        {"remove": "sha256"},
        {"add": ("url", "https://example.invalid/latest")},
        {"add": ("git_branch", "main")},
        {"add": ("latest", True)},
    ):
        ref_value = _schema_asset_ref()
        if "remove" in mutation:
            ref_value.pop(str(mutation["remove"]))
        else:
            field, value = mutation["add"]  # type: ignore[misc]
            ref_value[field] = value
        _assert_diagnostic(
            resolve_exact_asset_ref(_parsed(ref_value), ()),
            DiagnosticCode.CONTRACT_MUTABLE_REF,
        )


def test_path_and_schema_uri_never_trigger_file_or_network_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("reference resolution attempted filesystem access")

    monkeypatch.setattr(builtins, "open", forbidden_open)
    ref_value = _schema_asset_ref(path_hint="/etc/passwd")
    result = resolve_exact_asset_ref(_parsed(ref_value), ())
    _assert_diagnostic(result, DiagnosticCode.REF_UNRESOLVED)


def test_host_dictionary_cannot_bypass_the_parsed_reference_boundary() -> None:
    _assert_diagnostic(
        resolve_exact_asset_ref(_schema_asset_ref(), ()),  # type: ignore[arg-type]
        DiagnosticCode.REF_TYPE_MISMATCH,
    )


def test_malformed_canonical_values_fail_closed_without_host_exceptions() -> None:
    malformed_asset = _schema_asset_ref()
    malformed_asset["asset_id"] = []
    _assert_diagnostic(
        resolve_exact_asset_ref(_parsed(malformed_asset), ()),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    record = _record()
    malformed_record_ref = _record_ref(record).to_python()
    malformed_record_ref["schema_ref"] = []
    _assert_diagnostic(
        resolve_exact_record_ref(
            _parsed(malformed_record_ref),
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    malformed_envelope = _envelope()
    malformed_envelope["producer_context"] = {
        "producer": {"actor_kind": [], "actor_id": "agent:discovery-A"},
        "role": "DISCOVERY_PRODUCER",
        "attempt_id": "attempt:walking-1",
        "implementation_ref": _schema_asset_ref(),
        "environment_ref": _schema_asset_ref(),
    }
    _assert_diagnostic(
        validate_immutable_envelope(_parsed(malformed_envelope), contract_bound=True),
        DiagnosticCode.RECORD_INVALID_ENVELOPE,
    )
    _assert_diagnostic(
        resolve_exact_record_ref({}, (), ()),  # type: ignore[arg-type]
        DiagnosticCode.REF_TYPE_MISMATCH,
    )


@pytest.mark.parametrize("corruption_kind", ["invalid-type", "excessive-depth"])
def test_every_reference_consumer_revalidates_opaque_values_fail_closed(
    corruption_kind: str,
) -> None:
    if corruption_kind == "invalid-type":
        invalid_node: object = {"host": "dictionary"}
    else:
        invalid_node = 0
        for _ in range(MAX_NESTING + 1):
            invalid_node = (invalid_node,)

    consumers = (
        (
            lambda value: resolve_exact_asset_ref(value, ()),
            DiagnosticCode.REF_TYPE_MISMATCH,
        ),
        (
            lambda value: resolve_exact_record_ref(value, (), ()),
            DiagnosticCode.REF_TYPE_MISMATCH,
        ),
        (
            lambda value: resolve_exact_component_ref(value, (), ()),
            DiagnosticCode.REF_TYPE_MISMATCH,
        ),
        (
            lambda value: validate_immutable_envelope(value, contract_bound=True),
            DiagnosticCode.RECORD_INVALID_ENVELOPE,
        ),
        (
            lambda value: validate_immutable_record(value, contract_bound=True),
            DiagnosticCode.RECORD_INVALID_ENVELOPE,
        ),
    )
    for consume, expected_code in consumers:
        opaque = _parsed({})
        object.__setattr__(
            opaque,
            "_ParsedCanonicalValue__node",
            invalid_node,
        )
        _assert_diagnostic(consume(opaque), expected_code)


def test_exact_record_ref_checks_type_schema_revision_and_canonical_hash() -> None:
    record = _record(payload={"value": 1})
    ref = _record_ref(record)
    assert resolve_exact_record_ref(ref, (record,), (_schema_asset(),)) is record

    stale_hash_value = ref.to_python()
    stale_hash_value["content_hash"] = "sha256:" + ("0" * 64)
    _assert_diagnostic(
        resolve_exact_record_ref(
            _parsed(stale_hash_value),
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_HASH_MISMATCH,
    )

    wrong_type_value = ref.to_python()
    wrong_type_value["record_type"] = "agtxiv.inventory-discovery-result/1.0.0"
    _assert_diagnostic(
        resolve_exact_record_ref(
            _parsed(wrong_type_value),
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    wrong_schema_value = ref.to_python()
    wrong_schema_value["schema_ref"]["asset_id"] = "schema:other:1.0.0"
    _assert_diagnostic(
        resolve_exact_record_ref(
            _parsed(wrong_schema_value),
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    wrong_revision_value = ref.to_python()
    wrong_revision_value["record_revision"] = 2
    _assert_diagnostic(
        resolve_exact_record_ref(
            _parsed(wrong_revision_value),
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_UNRESOLVED,
    )


def test_record_resolution_requires_exact_supplied_schema_bytes() -> None:
    record = _record(payload={"value": 1})
    ref = _record_ref(record)
    _assert_diagnostic(
        resolve_exact_record_ref(ref, (record,), ()),
        DiagnosticCode.REF_UNRESOLVED,
    )
    changed_schema = SuppliedAsset(
        asset_id="schema:agentization-plan:1.0.0",
        media_type="application/schema+json",
        raw_bytes=b'{"type":"array"}',
        schema_uri=SCHEMA_URI,
    )
    _assert_diagnostic(
        resolve_exact_record_ref(ref, (record,), (changed_schema,)),
        DiagnosticCode.REF_HASH_MISMATCH,
    )


def test_record_resolution_is_direct_not_schema_or_transitive_validation() -> None:
    schema_bytes = (
        b'{"$id":"https://example.invalid/wrong-id","type":"array"}'
    )
    schema_ref = {
        "asset_id": "schema:agentization-plan:1.0.0",
        "media_type": "application/schema+json",
        "byte_size": len(schema_bytes),
        "sha256": raw_asset_sha256(schema_bytes),
        "schema_uri": SCHEMA_URI,
    }
    payload_that_does_not_match_schema = {
        "unresolved_embedded_ref": {
            "url": "https://example.invalid/latest",
            "record_id": "missing:record",
        }
    }
    record = _record(
        payload=payload_that_does_not_match_schema,
        schema_ref=schema_ref,
    )
    ref = _record_ref(record)
    schema_asset = SuppliedAsset(
        "schema:agentization-plan:1.0.0",
        "application/schema+json",
        schema_bytes,
        SCHEMA_URI,
    )

    # Direct resolution verifies the exact schema bytes but intentionally does
    # not parse their $id, validate this payload, resolve its embedded locator,
    # or follow the unresolved contract_bundle_ref transitively.
    assert resolve_exact_record_ref(ref, (record,), (schema_asset,)) is record


def test_record_resolution_rejects_duplicate_identity_and_tampered_target_hash() -> None:
    record = _record(payload={"value": 1})
    ref = _record_ref(record)
    _assert_diagnostic(
        resolve_exact_record_ref(ref, (record, record), (_schema_asset(),)),
        DiagnosticCode.REF_UNRESOLVED,
    )

    tampered_document = record.to_python()
    tampered_document["payload"] = {"value": 2}
    tampered = _parsed(tampered_document)
    _assert_diagnostic(
        resolve_exact_record_ref(ref, (tampered,), (_schema_asset(),)),
        DiagnosticCode.REF_HASH_MISMATCH,
    )


def test_schema_path_hint_is_non_authoritative_during_record_resolution() -> None:
    target_schema_ref = _schema_asset_ref(path_hint="original/location.json")
    record = _record(schema_ref=target_schema_ref)
    referring_schema_ref = _schema_asset_ref(path_hint="different/display/location.json")
    ref = _record_ref(record, schema_ref=referring_schema_ref)
    assert resolve_exact_record_ref(ref, (record,), (_schema_asset(),)) is record


def test_record_ref_rejects_ad_hoc_component_or_locator_fields() -> None:
    record = _record()
    ref_value = _record_ref(record).to_python()
    for field, value in (
        ("component_id", "component:x"),
        ("path", "records/current.json"),
        ("url", "https://example.invalid/latest"),
        ("git_branch", "main"),
    ):
        mutated = {**ref_value, field: value}
        _assert_diagnostic(
            resolve_exact_record_ref(
                _parsed(mutated),
                (record,),
                (_schema_asset(),),
            ),
            DiagnosticCode.CONTRACT_MUTABLE_REF,
        )

    noncanonical_version = ref_value | {
        "record_type": "agtxiv.agentization-plan/01.0.0"
    }
    _assert_diagnostic(
        resolve_exact_record_ref(
            _parsed(noncanonical_version),
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )


def test_exact_component_ref_resolves_pointer_and_rechecks_component_identity() -> None:
    payload = {
        "components": [
            {"component_id": "component:theorem-1", "value": "T"},
        ],
        "by_key": {
            "a/b~c": {"component_id": "component:escaped-1", "value": "E"},
        },
    }
    record = _record(payload=payload)
    base_ref = _record_ref(record).to_python()
    component_ref = _parsed(
        {
            **base_ref,
            "component_id": "component:theorem-1",
            "json_pointer": "/payload/components/0",
        }
    )
    component = resolve_exact_component_ref(
        component_ref,
        (record,),
        (_schema_asset(),),
    )
    assert isinstance(component, ParsedCanonicalValue)
    assert component.to_python()["value"] == "T"

    escaped_ref = _parsed(
        {
            **base_ref,
            "component_id": "component:escaped-1",
            "json_pointer": "/payload/by_key/a~1b~0c",
        }
    )
    escaped = resolve_exact_component_ref(
        escaped_ref,
        (record,),
        (_schema_asset(),),
    )
    assert isinstance(escaped, ParsedCanonicalValue)
    assert escaped.to_python()["value"] == "E"

    wrong_id = component_ref.to_python()
    wrong_id["component_id"] = "component:other"
    _assert_diagnostic(
        resolve_exact_component_ref(
            _parsed(wrong_id),
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_TYPE_MISMATCH,
    )

    missing_pointer = component_ref.to_python()
    missing_pointer["json_pointer"] = "/payload/components/9"
    _assert_diagnostic(
        resolve_exact_component_ref(
            _parsed(missing_pointer),
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_UNRESOLVED,
    )


def test_json_pointer_empty_and_tilde_tokens_are_exactly_decoded() -> None:
    record = _record(
        payload={
            "by_key": {
                "": {"component_id": "component:empty-token", "value": "empty"},
                "~1": {"component_id": "component:tilde-one", "value": "tilde"},
            }
        }
    )
    base_ref = _record_ref(record).to_python()
    cases = (
        ("/payload/by_key/", "component:empty-token", "empty"),
        ("/payload/by_key/~01", "component:tilde-one", "tilde"),
    )
    for pointer, component_id, expected_value in cases:
        ref = _parsed(
            {
                **base_ref,
                "component_id": component_id,
                "json_pointer": pointer,
            }
        )
        result = resolve_exact_component_ref(
            ref,
            (record,),
            (_schema_asset(),),
        )
        assert isinstance(result, ParsedCanonicalValue)
        assert result.to_python()["value"] == expected_value


@pytest.mark.parametrize(
    "array_token",
    [
        "00",
        "-",
        "٠",
        "9" * 4000,
    ],
    ids=["leading-zero", "append-token", "unicode-digit", "large-index"],
)
def test_json_pointer_array_aliases_and_non_indices_fail_without_integer_conversion_leaks(
    array_token: str,
) -> None:
    record = _record(
        payload={
            "components": [
                {"component_id": "component:theorem-1", "value": "T"},
            ]
        }
    )
    ref = _parsed(
        {
            **_record_ref(record).to_python(),
            "component_id": "component:theorem-1",
            "json_pointer": f"/payload/components/{array_token}",
        }
    )
    diagnostic = _assert_diagnostic(
        resolve_exact_component_ref(
            ref,
            (record,),
            (_schema_asset(),),
        ),
        DiagnosticCode.REF_UNRESOLVED,
    )
    assert diagnostic.json_pointer == "/json_pointer"


def test_envelope_validator_enforces_base_contract_and_immediate_predecessor() -> None:
    contract_envelope = _parsed(_envelope())
    assert validate_immutable_envelope(contract_envelope, contract_bound=True) is None
    _assert_diagnostic(
        validate_immutable_envelope(contract_envelope, contract_bound=False),
        DiagnosticCode.RECORD_INVALID_ENVELOPE,
    )

    base_value = _envelope()
    base_value["record_type"] = "agtxiv.contract-bundle-release/1.0.0"
    base_value["record_id"] = "contract-bundle-release:fixture-1"
    base_value["schema_ref"] = _schema_asset_ref(
        asset_id="schema:contract-bundle-release:1.0.0",
        schema_uri=BUNDLE_SCHEMA_URI,
    )
    base_value.pop("contract_bundle_ref")
    assert validate_immutable_envelope(_parsed(base_value), contract_bound=False) is None

    revision_two = _envelope(revision=2)
    assert validate_immutable_envelope(_parsed(revision_two), contract_bound=True) is None
    for field, wrong_value in (
        ("record_id", "agentization-plan:other"),
        ("record_type", "agtxiv.inventory-discovery-result/1.0.0"),
        ("record_revision", 2),
    ):
        invalid = copy.deepcopy(revision_two)
        invalid["supersedes_ref"][field] = wrong_value  # type: ignore[index]
        _assert_diagnostic(
            validate_immutable_envelope(_parsed(invalid), contract_bound=True),
            DiagnosticCode.RECORD_SUPERSESSION_MISMATCH,
        )


def test_envelope_validator_rejects_first_revision_supersession_and_later_gap() -> None:
    first = _envelope()
    first["supersedes_ref"] = _record_ref(_record()).to_python()
    _assert_diagnostic(
        validate_immutable_envelope(_parsed(first), contract_bound=True),
        DiagnosticCode.RECORD_SUPERSESSION_MISMATCH,
    )

    later = _envelope(revision=2)
    later.pop("supersedes_ref")
    _assert_diagnostic(
        validate_immutable_envelope(_parsed(later), contract_bound=True),
        DiagnosticCode.RECORD_SUPERSESSION_MISMATCH,
    )


def test_immutable_record_recomputes_hash_and_rejects_outer_metadata() -> None:
    record = _record(payload={"value": 1})
    assert validate_immutable_record(record, contract_bound=True) is None

    tampered = record.to_python()
    tampered["payload"] = {"value": 2}
    _assert_diagnostic(
        validate_immutable_record(_parsed(tampered), contract_bound=True),
        DiagnosticCode.RECORD_HASH_MISMATCH,
    )

    with_extra = record.to_python()
    with_extra["path"] = "records/current.json"
    _assert_diagnostic(
        validate_immutable_record(_parsed(with_extra), contract_bound=True),
        DiagnosticCode.RECORD_INVALID_ENVELOPE,
    )


def test_repeated_resolution_is_deterministic() -> None:
    record = _record(payload={"value": 1})
    ref = _record_ref(record)
    observations: list[tuple[str, str]] = []
    for _ in range(20):
        result = resolve_exact_record_ref(ref, (record,), (_schema_asset(),))
        assert isinstance(result, ParsedCanonicalValue)
        observations.append(
            (result.to_python()["content_hash"], str(validate_immutable_record(result, contract_bound=True)))
        )
    assert len(set(observations)) == 1
