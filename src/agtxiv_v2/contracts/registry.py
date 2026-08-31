"""Pure offline construction of immutable V2 contract-schema registries.

An ``https://`` schema identity is a literal key in this module, never a
retrieval instruction.  Registry construction receives every byte string
explicitly, validates the exact raw-byte bindings before interpreting JSON,
checks a deliberately closed Draft 2020-12 language, and admits only an
acyclic graph of typed schema locations.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
from dataclasses import dataclass
from typing import Any, Never

from jsonschema import Draft202012Validator, FormatChecker

from .canonical import (
    IJSON_MAX_INTEGER,
    MAX_NESTING,
    CanonicalValueIntegrityError,
    ParsedCanonicalValue,
    canonical_bytes,
    parse_canonical_json,
)
from .diagnostics import Diagnostic, DiagnosticCode
from .references import (
    SuppliedAsset,
    raw_asset_sha256,
)

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_MEDIA_TYPE = "application/schema+json"

_SCHEMA_ID_PATTERN = re.compile(
    r"^https://agtxiv\.org/schema/v2/contract-kernel/"
    r"[a-z0-9-]+(?:/[a-z0-9-]+)+/"
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)(?![\s\S])"
)
_NAMESPACED_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._:/-]*(?![\s\S])"
)
_MEDIA_TYPE_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/"
    r"[a-z0-9][a-z0-9!#$&^_.+-]*(?![\s\S])"
)
_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}(?![\s\S])")
_JSON_POINTER_PATTERN = re.compile(r"^(?:/(?:[^~/\r\n]|~[01])*)+(?![\s\S])")
_ASSET_REQUIRED = frozenset({"asset_id", "media_type", "byte_size", "sha256"})
_ASSET_ALLOWED = _ASSET_REQUIRED | {"path_hint", "schema_uri"}

_ROOT_ONLY_KEYWORDS = frozenset({"$schema", "$id"})
_ALLOWED_SCHEMA_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "$ref",
        "$defs",
        "$comment",
        "title",
        "description",
        "default",
        "examples",
        "deprecated",
        "readOnly",
        "writeOnly",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "if",
        "then",
        "else",
        "dependentSchemas",
        "prefixItems",
        "items",
        "contains",
        "properties",
        "patternProperties",
        "additionalProperties",
        "propertyNames",
        "unevaluatedItems",
        "unevaluatedProperties",
        "type",
        "enum",
        "const",
        "multipleOf",
        "maximum",
        "exclusiveMaximum",
        "minimum",
        "exclusiveMinimum",
        "maxLength",
        "minLength",
        "pattern",
        "maxItems",
        "minItems",
        "uniqueItems",
        "maxContains",
        "minContains",
        "maxProperties",
        "minProperties",
        "required",
        "dependentRequired",
        "format",
    }
)
_SCHEMA_MAP_KEYWORDS = frozenset(
    {"$defs", "properties", "patternProperties", "dependentSchemas"}
)
_SCHEMA_ARRAY_KEYWORDS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})
_SINGLE_SCHEMA_KEYWORDS = frozenset(
    {
        "not",
        "if",
        "then",
        "else",
        "items",
        "contains",
        "additionalProperties",
        "propertyNames",
        "unevaluatedItems",
        "unevaluatedProperties",
    }
)
_ALLOWED_FORMATS = frozenset({"uri", "date-time"})

_PHASE_RANK = {
    "REGISTRY_INPUT": 1,
    "REGISTRY_EXACT_BINDING": 2,
    "REGISTRY_PARSE": 3,
    "REGISTRY_SCHEMA_META": 4,
    "REGISTRY_UNIQUENESS": 5,
    "REGISTRY_REFERENCE_CLOSURE": 6,
    "RECORD_INPUT": 10,
    "RECORD_ENVELOPE": 11,
    "RECORD_SCHEMA_BINDING": 12,
    "RECORD_TYPE_BINDING": 13,
    "RECORD_PAYLOAD": 14,
    "RECORD_HASH": 15,
}
_REGISTRY_CONSTRUCTION_TOKEN = object()


def _valid_schema_id(value: object) -> bool:
    if type(value) is not str or _SCHEMA_ID_PATTERN.fullmatch(value) is None:
        return False
    path = value.removeprefix("https://agtxiv.org/schema/v2/contract-kernel/")
    return "latest" not in path.split("/")[:-1]


def _valid_pointer_literal(value: str) -> bool:
    return _JSON_POINTER_PATTERN.fullmatch(value) is not None and "%" not in value


@dataclass(frozen=True, slots=True)
class SchemaAssetBinding:
    """One exact schema reference paired with its explicitly supplied bytes."""

    exact_ref: ParsedCanonicalValue
    supplied_asset: SuppliedAsset


@dataclass(frozen=True, slots=True)
class _FrozenObject:
    pairs: tuple[tuple[str, Any], ...]


@dataclass(frozen=True, slots=True)
class _InputSnapshot:
    ref_document: Any
    asset_id: str
    media_type: str
    raw_bytes: bytes
    schema_uri: str | None
    subject_identity: str | None
    binding_observation: tuple[tuple[str, Any], ...]


@dataclass(frozen=True, slots=True)
class _SchemaAnalysis:
    locations: tuple[tuple[str, Any], ...]
    references: tuple[tuple[str, str, str], ...]
    containment_edges: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class _PreparedSchema:
    snapshot: _InputSnapshot
    ref_document: dict[str, Any]
    document: dict[str, Any]
    schema_id: str
    analysis: _SchemaAnalysis


@dataclass(frozen=True, slots=True)
class _RegisteredSchema:
    asset_id: str
    media_type: str
    byte_size: int
    sha256: str
    schema_id: str
    raw_bytes: bytes
    document: _FrozenObject


class ContractSchemaRegistry:
    """A complete recursively frozen snapshot of verified schema assets.

    The constructor token is intentionally package-private.  Public callers
    obtain instances only from :func:`build_schema_registry`.  The internal
    seal detects accidental or simple post-build mutation; it is not a
    cryptographic authenticator, signature, authorization decision, or defense
    against arbitrary malicious code running in the same Python interpreter.
    """

    __slots__ = ("__entries", "__seal", "__token")

    def __init__(
        self,
        entries: tuple[_RegisteredSchema, ...],
        *,
        _token: object,
    ) -> None:
        if _token is not _REGISTRY_CONSTRUCTION_TOKEN:
            raise TypeError("ContractSchemaRegistry is created only by build_schema_registry")
        object.__setattr__(self, "_ContractSchemaRegistry__entries", entries)
        object.__setattr__(self, "_ContractSchemaRegistry__seal", _registry_seal(entries))
        object.__setattr__(self, "_ContractSchemaRegistry__token", _token)

    def __setattr__(self, name: str, value: Any) -> Never:
        raise AttributeError("ContractSchemaRegistry is immutable")

    def __delattr__(self, name: str) -> Never:
        raise AttributeError("ContractSchemaRegistry is immutable")

    @property
    def schema_ids(self) -> tuple[str, ...]:
        entries = _registry_entries(self)
        if entries is None:
            raise ValueError("ContractSchemaRegistry failed its integrity check")
        return tuple(entry.schema_id for entry in entries)

    def __repr__(self) -> str:
        entries = _registry_entries(self)
        count = "invalid" if entries is None else str(len(entries))
        return f"ContractSchemaRegistry(<{count} schemas>)"


def build_schema_registry(
    bindings: tuple[SchemaAssetBinding, ...],
) -> ContractSchemaRegistry | tuple[Diagnostic, ...]:
    """Build one atomic offline registry or return deterministic diagnostics."""

    snapshots, input_diagnostics = _snapshot_inputs(bindings)
    if input_diagnostics:
        return _sort_diagnostics(input_diagnostics)
    assert snapshots is not None
    if not snapshots:
        return (
            _diagnostic(
                DiagnosticCode.SCHEMA_EMPTY_REGISTRY,
                "schema registry requires at least one exact schema binding",
                phase="REGISTRY_INPUT",
            ),
        )

    prepared: list[_PreparedSchema] = []
    preflight_diagnostics: list[Diagnostic] = []
    for snapshot in snapshots:
        binding_diagnostics, ref_document = _check_exact_binding(snapshot)
        if binding_diagnostics:
            preflight_diagnostics.extend(
                _attach_binding_observation(binding_diagnostics, snapshot)
            )
            continue
        assert ref_document is not None

        parsed, parse_diagnostics = _parse_schema(snapshot)
        if parse_diagnostics:
            preflight_diagnostics.extend(
                _attach_binding_observation(parse_diagnostics, snapshot)
            )
            continue
        assert parsed is not None
        document = parsed.to_python()
        assert type(document) is dict

        schema_id, analysis, meta_diagnostics = _check_schema_document(
            snapshot,
            ref_document,
            document,
        )
        if meta_diagnostics:
            declared_schema_id = document.get("$id")
            preflight_diagnostics.extend(
                _attach_binding_observation(
                    meta_diagnostics,
                    snapshot,
                    declared_schema_id=(
                        declared_schema_id
                        if _valid_schema_id(declared_schema_id)
                        else None
                    ),
                )
            )
            continue
        assert schema_id is not None and analysis is not None
        prepared.append(
            _PreparedSchema(
                snapshot,
                ref_document,
                document,
                schema_id,
                analysis,
            )
        )

    if preflight_diagnostics:
        return _sort_diagnostics(preflight_diagnostics)

    uniqueness_diagnostics = _check_unique_identities(prepared)
    if uniqueness_diagnostics:
        return _sort_diagnostics(uniqueness_diagnostics)

    closure_diagnostics = _check_reference_closure(prepared)
    if closure_diagnostics:
        return _sort_diagnostics(closure_diagnostics)

    entries = tuple(
        sorted(
            (
                _RegisteredSchema(
                    asset_id=item.snapshot.asset_id,
                    media_type=item.snapshot.media_type,
                    byte_size=len(item.snapshot.raw_bytes),
                    sha256=raw_asset_sha256(item.snapshot.raw_bytes),
                    schema_id=item.schema_id,
                    raw_bytes=item.snapshot.raw_bytes,
                    document=_freeze_json(item.document),
                )
                for item in prepared
            ),
            key=lambda entry: entry.schema_id,
        )
    )
    return ContractSchemaRegistry(entries, _token=_REGISTRY_CONSTRUCTION_TOKEN)


def _snapshot_inputs(
    bindings: object,
) -> tuple[tuple[_InputSnapshot, ...] | None, list[Diagnostic]]:
    if type(bindings) is not tuple:
        return None, [_input_type_diagnostic("bindings must have the exact tuple runtime type")]

    snapshots: list[_InputSnapshot] = []
    diagnostics: list[Diagnostic] = []
    for binding in bindings:
        if type(binding) is not SchemaAssetBinding:
            diagnostics.append(
                _input_type_diagnostic(
                    "every binding must have the exact SchemaAssetBinding runtime type"
                )
            )
            continue
        try:
            exact_ref = object.__getattribute__(binding, "exact_ref")
            supplied_asset = object.__getattribute__(binding, "supplied_asset")
        except AttributeError:
            diagnostics.append(
                _input_type_diagnostic("schema binding is missing typed fields")
            )
            continue
        if type(exact_ref) is not ParsedCanonicalValue or type(supplied_asset) is not SuppliedAsset:
            diagnostics.append(
                _input_type_diagnostic(
                    "binding fields require exact ParsedCanonicalValue and SuppliedAsset types"
                )
            )
            continue
        try:
            ref_document = exact_ref.to_python()
            asset_id = object.__getattribute__(supplied_asset, "asset_id")
            media_type = object.__getattribute__(supplied_asset, "media_type")
            raw_bytes = object.__getattribute__(supplied_asset, "raw_bytes")
            schema_uri = object.__getattribute__(supplied_asset, "schema_uri")
        except (AttributeError, CanonicalValueIntegrityError):
            diagnostics.append(
                _input_type_diagnostic(
                    "binding contains a forged or incomplete typed value"
                )
            )
            continue
        if (
            type(asset_id) is not str
            or type(media_type) is not str
            or type(raw_bytes) is not bytes
            or (schema_uri is not None and type(schema_uri) is not str)
        ):
            diagnostics.append(
                _input_type_diagnostic(
                    "supplied schema asset has invalid typed metadata"
                )
            )
            continue
        snapshots.append(
            _InputSnapshot(
                ref_document,
                asset_id,
                media_type,
                raw_bytes,
                schema_uri,
                None,
                (),
            )
        )
    if diagnostics:
        return None, diagnostics
    completed: list[_InputSnapshot] = []
    for snapshot in snapshots:
        observation = _binding_observation(snapshot)
        exact_asset_id = observation.get("exact_ref_asset_id")
        supplied_asset_id = observation.get("supplied_asset_id")
        subject = (
            exact_asset_id
            if type(exact_asset_id) is str
            else supplied_asset_id
            if type(supplied_asset_id) is str
            else observation["raw_sha256"]
        )
        assert type(subject) is str
        completed.append(
            _InputSnapshot(
                snapshot.ref_document,
                snapshot.asset_id,
                snapshot.media_type,
                snapshot.raw_bytes,
                snapshot.schema_uri,
                subject,
                tuple(sorted(observation.items())),
            )
        )
    return tuple(completed), []


def _binding_observation(snapshot: _InputSnapshot) -> dict[str, Any]:
    """Return only safe, shape-checked facts that distinguish one binding."""

    observation: dict[str, Any] = {
        "raw_byte_size": len(snapshot.raw_bytes),
        "raw_sha256": raw_asset_sha256(snapshot.raw_bytes),
    }
    if (
        3 <= len(snapshot.asset_id) <= 256
        and _NAMESPACED_ID_PATTERN.fullmatch(snapshot.asset_id) is not None
    ):
        observation["supplied_asset_id"] = snapshot.asset_id
    if (
        3 <= len(snapshot.media_type) <= 127
        and _MEDIA_TYPE_PATTERN.fullmatch(snapshot.media_type) is not None
    ):
        observation["supplied_media_type"] = snapshot.media_type
    if _valid_schema_id(snapshot.schema_uri):
        observation["supplied_schema_uri"] = snapshot.schema_uri

    document = snapshot.ref_document
    if type(document) is not dict:
        return observation
    asset_id = document.get("asset_id")
    if (
        type(asset_id) is str
        and 3 <= len(asset_id) <= 256
        and _NAMESPACED_ID_PATTERN.fullmatch(asset_id) is not None
    ):
        observation["exact_ref_asset_id"] = asset_id
    media_type = document.get("media_type")
    if (
        type(media_type) is str
        and 3 <= len(media_type) <= 127
        and _MEDIA_TYPE_PATTERN.fullmatch(media_type) is not None
    ):
        observation["exact_ref_media_type"] = media_type
    byte_size = document.get("byte_size")
    if type(byte_size) is int and 0 <= byte_size <= IJSON_MAX_INTEGER:
        observation["exact_ref_byte_size"] = byte_size
    sha256 = document.get("sha256")
    if type(sha256) is str and _DIGEST_PATTERN.fullmatch(sha256) is not None:
        observation["exact_ref_sha256"] = sha256
    schema_uri = document.get("schema_uri")
    if _valid_schema_id(schema_uri):
        observation["exact_ref_schema_uri"] = schema_uri
    return observation


def _check_exact_binding(
    snapshot: _InputSnapshot,
) -> tuple[list[Diagnostic], dict[str, Any] | None]:
    document = snapshot.ref_document
    if type(document) is not dict:
        return [
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "exact schema reference must be a canonical JSON object",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        ], None

    diagnostics: list[Diagnostic] = []
    if not _ASSET_REQUIRED <= set(document) or not set(document) <= _ASSET_ALLOWED:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.CONTRACT_MUTABLE_REF,
                "schema reference must contain only the exact asset fields",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )

    supplied_asset_id_valid = (
        3 <= len(snapshot.asset_id) <= 256
        and _NAMESPACED_ID_PATTERN.fullmatch(snapshot.asset_id) is not None
    )
    if not supplied_asset_id_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "supplied schema asset_id is not a stable namespaced identity",
                pointer="/supplied_asset/asset_id",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )
    asset_id = document.get("asset_id")
    asset_id_valid = (
        type(asset_id) is str
        and 3 <= len(asset_id) <= 256
        and _NAMESPACED_ID_PATTERN.fullmatch(asset_id) is not None
    )
    if "asset_id" in document and not asset_id_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "asset_id is not a stable namespaced identity",
                pointer="/asset_id",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )
    elif asset_id_valid and supplied_asset_id_valid and asset_id != snapshot.asset_id:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_UNRESOLVED,
                "schema binding asset_id does not name its supplied target",
                pointer="/asset_id",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )

    supplied_media_type_valid = (
        3 <= len(snapshot.media_type) <= 127
        and _MEDIA_TYPE_PATTERN.fullmatch(snapshot.media_type) is not None
    )
    if not supplied_media_type_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "supplied schema media_type is invalid",
                pointer="/supplied_asset/media_type",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )
    elif snapshot.media_type != SCHEMA_MEDIA_TYPE:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "supplied registry schema media type must be application/schema+json",
                pointer="/supplied_asset/media_type",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )
    media_type = document.get("media_type")
    media_type_valid = (
        type(media_type) is str
        and 3 <= len(media_type) <= 127
        and _MEDIA_TYPE_PATTERN.fullmatch(media_type) is not None
    )
    if "media_type" in document and not media_type_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "media_type is invalid",
                pointer="/media_type",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )
    elif media_type_valid and media_type != SCHEMA_MEDIA_TYPE:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "registry schema media type must be application/schema+json",
                pointer="/media_type",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )

    byte_size = document.get("byte_size")
    byte_size_valid = (
        type(byte_size) is int and 0 <= byte_size <= IJSON_MAX_INTEGER
    )
    if "byte_size" in document and not byte_size_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "byte_size is outside the non-negative I-JSON range",
                pointer="/byte_size",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )
    elif byte_size_valid and byte_size != len(snapshot.raw_bytes):
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_HASH_MISMATCH,
                "supplied schema byte size differs from the exact reference",
                pointer="/byte_size",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )

    digest = document.get("sha256")
    digest_valid = type(digest) is str and _DIGEST_PATTERN.fullmatch(digest) is not None
    if "sha256" in document and not digest_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.CONTRACT_MUTABLE_REF,
                "schema reference lacks an exact lowercase SHA-256 digest",
                pointer="/sha256",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )
    elif digest_valid and digest != raw_asset_sha256(snapshot.raw_bytes):
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_HASH_MISMATCH,
                "supplied raw schema bytes differ from the exact SHA-256 reference",
                pointer="/sha256",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )

    if "path_hint" in document and (
        type(document["path_hint"]) is not str
        or not 1 <= len(document["path_hint"]) <= 4096
    ):
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "path_hint must be non-empty display text",
                pointer="/path_hint",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )

    ref_schema_uri = document.get("schema_uri")
    ref_schema_uri_shape_valid = (
        type(ref_schema_uri) is str
        and len(ref_schema_uri) <= 2048
        and _SCHEMA_ID_PATTERN.fullmatch(ref_schema_uri) is not None
    )
    if "schema_uri" in document and not ref_schema_uri_shape_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.CONTRACT_MUTABLE_REF,
                "schema_uri must be an immutable versioned AgtXIv schema identity",
                pointer="/schema_uri",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
            )
        )
    ref_schema_uri_valid = ref_schema_uri_shape_valid and _valid_schema_id(ref_schema_uri)
    supplied_schema_uri_shape_valid = (
        snapshot.schema_uri is not None
        and len(snapshot.schema_uri) <= 2048
        and _SCHEMA_ID_PATTERN.fullmatch(snapshot.schema_uri) is not None
    )
    supplied_schema_uri_valid = (
        supplied_schema_uri_shape_valid and _valid_schema_id(snapshot.schema_uri)
    )
    schema_uri_details: dict[str, Any] = {
        "exact_ref_schema_uri_valid": ref_schema_uri_valid,
        "supplied_schema_uri_valid": supplied_schema_uri_valid,
    }
    if ref_schema_uri_valid:
        schema_uri_details["exact_ref_schema_uri"] = ref_schema_uri
    if supplied_schema_uri_valid:
        schema_uri_details["supplied_schema_uri"] = snapshot.schema_uri
    if not ref_schema_uri_valid and not supplied_schema_uri_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.SCHEMA_ID_MISMATCH,
                "registry binding requires one immutable versioned schema_uri",
                pointer="/schema_uri",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
                details=schema_uri_details,
            )
        )
    elif not ref_schema_uri_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.SCHEMA_ID_MISMATCH,
                "registry exact reference requires one immutable versioned schema_uri",
                pointer="/schema_uri",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
                details=schema_uri_details,
            )
        )
    elif not supplied_schema_uri_valid:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.SCHEMA_ID_MISMATCH,
                "supplied registry schema requires one immutable versioned schema_uri",
                pointer="/supplied_asset/schema_uri",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
                details=schema_uri_details,
            )
        )
    elif ref_schema_uri != snapshot.schema_uri:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.SCHEMA_ID_MISMATCH,
                "registry exact reference and supplied asset require the same schema_uri",
                pointer="/schema_uri",
                phase="REGISTRY_EXACT_BINDING",
                subject=snapshot.subject_identity,
                details=schema_uri_details,
            )
        )
    return diagnostics, document if not diagnostics else None


def _parse_schema(
    snapshot: _InputSnapshot,
) -> tuple[ParsedCanonicalValue | None, list[Diagnostic]]:
    parsed = parse_canonical_json(snapshot.raw_bytes)
    if isinstance(parsed, Diagnostic):
        return None, [
            _enrich(
                parsed,
                phase="REGISTRY_PARSE",
                subject=snapshot.subject_identity,
            )
        ]
    document = parsed.to_python()
    if type(document) is not dict:
        return None, [
            _diagnostic(
                DiagnosticCode.SCHEMA_INVALID_DOCUMENT,
                "schema asset must contain one top-level JSON object",
                phase="REGISTRY_PARSE",
                subject=snapshot.subject_identity,
            )
        ]
    return parsed, []


def _check_schema_document(
    snapshot: _InputSnapshot,
    ref_document: dict[str, Any],
    document: dict[str, Any],
) -> tuple[str | None, _SchemaAnalysis | None, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    dialect = document.get("$schema")
    if dialect != DRAFT_2020_12 or type(dialect) is not str:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.SCHEMA_DIALECT_MISMATCH,
                "schema must declare exactly Draft 2020-12",
                pointer="/$schema",
                phase="REGISTRY_SCHEMA_META",
                subject=snapshot.subject_identity,
            )
        )

    schema_id = document.get("$id")
    if (
        type(schema_id) is not str
        or not _valid_schema_id(schema_id)
        or schema_id != ref_document.get("schema_uri")
        or schema_id != snapshot.schema_uri
    ):
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.SCHEMA_ID_MISMATCH,
                "top-level $id must be one exact immutable versioned binding identity",
                pointer="/$id",
                phase="REGISTRY_SCHEMA_META",
                subject=snapshot.subject_identity,
            )
        )
    if diagnostics:
        return None, None, diagnostics
    assert type(schema_id) is str

    analysis, language_diagnostics = _analyze_schema_language(
        document,
        subject=schema_id,
    )
    if language_diagnostics:
        return None, None, language_diagnostics
    assert analysis is not None

    try:
        # An explicitly empty checker prevents process-global ``regex`` format
        # registrations from changing meta-validation.  Project regexes were
        # compiled mechanically by the closed-language walker above.
        meta_validator = Draft202012Validator(
            Draft202012Validator.META_SCHEMA,
            format_checker=FormatChecker(formats=()),
        )
        meta_errors = list(meta_validator.iter_errors(document))
    except Exception:
        return None, None, [
            _diagnostic(
                DiagnosticCode.SCHEMA_META_INVALID,
                "schema cannot be safely checked by the locked Draft 2020-12 implementation",
                phase="REGISTRY_SCHEMA_META",
                subject=schema_id,
            )
        ]
    if meta_errors:
        meta_diagnostics = [
            _diagnostic(
                DiagnosticCode.SCHEMA_META_INVALID,
                "schema does not satisfy the locked Draft 2020-12 meta-schema",
                pointer=_path_pointer(error.absolute_path),
                schema_pointer=_path_pointer(error.absolute_schema_path),
                phase="REGISTRY_SCHEMA_META",
                subject=schema_id,
                details={
                    "validator": (
                        error.validator
                        if type(error.validator) is str
                        else "unknown"
                    )
                },
            )
            for error in meta_errors
        ]
        return None, None, list(_sort_diagnostics(meta_diagnostics))
    return schema_id, analysis, []


def _analyze_schema_language(
    document: dict[str, Any],
    *,
    subject: str,
) -> tuple[_SchemaAnalysis | None, list[Diagnostic]]:
    locations: list[tuple[str, Any]] = []
    references: list[tuple[str, str, str]] = []
    containment_edges: list[tuple[str, str]] = []
    diagnostics: list[Diagnostic] = []
    stack: list[tuple[str, Any, bool]] = [("", document, True)]

    while stack:
        pointer, node, is_root = stack.pop()
        locations.append((pointer, node))
        if type(node) is bool:
            continue
        if type(node) is not dict:
            diagnostics.append(
                _meta_diagnostic(
                    subject,
                    pointer,
                    "schema-valued position must contain an object or boolean",
                )
            )
            continue

        for keyword in sorted(node):
            if keyword not in _ALLOWED_SCHEMA_KEYWORDS:
                diagnostics.append(
                    _meta_diagnostic(
                        subject,
                        _child(pointer, keyword),
                        "schema node contains a keyword outside the closed language",
                        details={"keyword": keyword},
                    )
                )
            elif not is_root and keyword == "$id":
                diagnostics.append(
                    _diagnostic(
                        DiagnosticCode.SCHEMA_ID_MISMATCH,
                        "nested $id sub-resources are forbidden in this registry version",
                        pointer=_child(pointer, keyword),
                        phase="REGISTRY_SCHEMA_META",
                        subject=subject,
                    )
                )
            elif not is_root and keyword in _ROOT_ONLY_KEYWORDS:
                diagnostics.append(
                    _meta_diagnostic(
                        subject,
                        _child(pointer, keyword),
                        "root identity keywords are forbidden at nested schema locations",
                    )
                )

        if "$ref" in node:
            reference = node["$ref"]
            if type(reference) is not str:
                diagnostics.append(
                    _meta_diagnostic(
                        subject,
                        _child(pointer, "$ref"),
                        "$ref must be a string",
                    )
                )
            else:
                references.append((pointer, _child(pointer, "$ref"), reference))

        if "format" in node and (
            type(node["format"]) is not str or node["format"] not in _ALLOWED_FORMATS
        ):
            diagnostics.append(
                _meta_diagnostic(
                    subject,
                    _child(pointer, "format"),
                    "format must be exactly uri or date-time",
                )
            )

        if "pattern" in node:
            _check_regex(
                node["pattern"],
                subject,
                _child(pointer, "pattern"),
                diagnostics,
            )

        for keyword in sorted(_SCHEMA_MAP_KEYWORDS):
            if keyword not in node:
                continue
            mapping = node[keyword]
            if type(mapping) is not dict:
                diagnostics.append(
                    _meta_diagnostic(
                        subject,
                        _child(pointer, keyword),
                        f"{keyword} must be an object mapping names to schemas",
                    )
                )
                continue
            for name in sorted(mapping, reverse=True):
                child_pointer = _child(_child(pointer, keyword), name)
                if keyword == "patternProperties":
                    _check_regex(name, subject, child_pointer, diagnostics)
                containment_edges.append((pointer, child_pointer))
                stack.append((child_pointer, mapping[name], False))

        for keyword in sorted(_SCHEMA_ARRAY_KEYWORDS):
            if keyword not in node:
                continue
            sequence = node[keyword]
            if type(sequence) is not list:
                diagnostics.append(
                    _meta_diagnostic(
                        subject,
                        _child(pointer, keyword),
                        f"{keyword} must be an array of schemas",
                    )
                )
                continue
            for index in reversed(range(len(sequence))):
                child_pointer = _child(_child(pointer, keyword), str(index))
                containment_edges.append((pointer, child_pointer))
                stack.append((child_pointer, sequence[index], False))

        for keyword in sorted(_SINGLE_SCHEMA_KEYWORDS, reverse=True):
            if keyword not in node:
                continue
            child_pointer = _child(pointer, keyword)
            containment_edges.append((pointer, child_pointer))
            stack.append((child_pointer, node[keyword], False))

    if diagnostics:
        return None, _sort_diagnostics(diagnostics)
    return (
        _SchemaAnalysis(
            tuple(sorted(locations, key=lambda item: item[0])),
            tuple(sorted(references)),
            tuple(sorted(containment_edges)),
        ),
        [],
    )


def _check_regex(
    value: Any,
    subject: str,
    pointer: str,
    diagnostics: list[Diagnostic],
) -> None:
    if type(value) is not str:
        diagnostics.append(
            _meta_diagnostic(subject, pointer, "regular expression must be a string")
        )
        return
    try:
        re.compile(value)
    except Exception:
        diagnostics.append(
            _meta_diagnostic(
                subject,
                pointer,
                "regular expression is invalid under the locked Python implementation",
            )
        )


def _check_unique_identities(prepared: list[_PreparedSchema]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for kind, pointer, identity_getter in (
        ("asset_id", "/asset_id", lambda item: item.snapshot.asset_id),
        ("schema_id", "/$id", lambda item: item.schema_id),
    ):
        groups: dict[str, list[_PreparedSchema]] = {}
        for item in prepared:
            groups.setdefault(identity_getter(item), []).append(item)
        for identity in sorted(groups):
            group = groups[identity]
            if len(group) < 2:
                continue
            observations = sorted(
                (
                    {
                        "asset_id": item.snapshot.asset_id,
                        "byte_size": len(item.snapshot.raw_bytes),
                        "schema_id": item.schema_id,
                        "sha256": raw_asset_sha256(item.snapshot.raw_bytes),
                    }
                    for item in group
                ),
                key=_canonical_machine_bytes,
            )
            diagnostics.append(
                _diagnostic(
                    DiagnosticCode.SCHEMA_DUPLICATE_ID,
                    f"registry contains more than one binding for the same {kind}",
                    pointer=pointer,
                    phase="REGISTRY_UNIQUENESS",
                    subject=identity,
                    details={
                        "binding_count": len(group),
                        "identity_kind": kind,
                        "observations": observations,
                    },
                )
            )
    return diagnostics


def _check_reference_closure(prepared: list[_PreparedSchema]) -> list[Diagnostic]:
    by_id = {item.schema_id: item for item in prepared}
    location_sets = {
        item.schema_id: frozenset(pointer for pointer, _ in item.analysis.locations)
        for item in prepared
    }
    nodes = {
        (item.schema_id, pointer)
        for item in prepared
        for pointer, _ in item.analysis.locations
    }
    edges: dict[tuple[str, str], set[tuple[str, str]]] = {
        node: set() for node in nodes
    }
    ref_edge_pointers: dict[
        tuple[tuple[str, str], tuple[str, str]],
        set[str],
    ] = {}

    for item in prepared:
        for source_pointer, child_pointer in item.analysis.containment_edges:
            edges[(item.schema_id, source_pointer)].add((item.schema_id, child_pointer))

    resolution_diagnostics: list[Diagnostic] = []
    for item in prepared:
        for source_pointer, ref_pointer, reference in item.analysis.references:
            target, code = _resolve_reference_literal(
                reference,
                current_schema_id=item.schema_id,
                known_ids=frozenset(by_id),
                location_sets=location_sets,
            )
            if code is not None:
                message = (
                    "schema reference is outside the exact supplied offline forms"
                    if code is DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN
                    else "schema reference does not resolve to an admitted schema location"
                )
                resolution_diagnostics.append(
                    _diagnostic(
                        code,
                        message,
                        pointer=ref_pointer,
                        phase="REGISTRY_REFERENCE_CLOSURE",
                        subject=item.schema_id,
                        details={"reference": reference},
                    )
                )
                continue
            assert target is not None
            source = (item.schema_id, source_pointer)
            edges[source].add(target)
            ref_edge_pointers.setdefault((source, target), set()).add(ref_pointer)

    if resolution_diagnostics:
        return resolution_diagnostics

    indegree = {node: 0 for node in nodes}
    for targets in edges.values():
        for target in targets:
            indegree[target] += 1
    ready = [node for node, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    removed: set[tuple[str, str]] = set()
    while ready:
        node = heapq.heappop(ready)
        removed.add(node)
        for target in sorted(edges[node]):
            indegree[target] -= 1
            if indegree[target] == 0:
                heapq.heappush(ready, target)

    remaining = nodes - removed
    if not remaining:
        return []
    cyclic_components = _cyclic_components(remaining, edges)
    if not cyclic_components:
        return []
    diagnostics: list[Diagnostic] = []
    for component in cyclic_components:
        component_set = frozenset(component)
        participating_ref_pointers = sorted(
            (source[0], pointer)
            for (source, target), pointers in ref_edge_pointers.items()
            if source in component_set and target in component_set
            for pointer in pointers
        )
        subject, pointer = (
            participating_ref_pointers[0]
            if participating_ref_pointers
            else min(component)
        )
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.SCHEMA_REFERENCE_CYCLE,
                "typed schema containment and reference edges contain a cycle",
                pointer=pointer,
                phase="REGISTRY_REFERENCE_CLOSURE",
                subject=subject,
                details={
                    "cycle_nodes": [
                        f"{schema_id}#{fragment}"
                        for schema_id, fragment in component
                    ]
                },
            )
        )
    return diagnostics


def _cyclic_components(
    nodes: set[tuple[str, str]],
    edges: dict[tuple[str, str], set[tuple[str, str]]],
) -> list[tuple[tuple[str, str], ...]]:
    """Return exact cyclic strongly connected components without recursion."""

    neighbors = {
        node: tuple(sorted(target for target in edges[node] if target in nodes))
        for node in nodes
    }
    visited: set[tuple[str, str]] = set()
    finish_order: list[tuple[str, str]] = []
    for start in sorted(nodes):
        if start in visited:
            continue
        stack: list[tuple[tuple[str, str], bool]] = [(start, False)]
        while stack:
            node, expanded = stack.pop()
            if expanded:
                finish_order.append(node)
                continue
            if node in visited:
                continue
            visited.add(node)
            stack.append((node, True))
            for target in reversed(neighbors[node]):
                if target not in visited:
                    stack.append((target, False))

    reverse: dict[tuple[str, str], list[tuple[str, str]]] = {
        node: [] for node in nodes
    }
    for source, targets in neighbors.items():
        for target in targets:
            reverse[target].append(source)
    for sources in reverse.values():
        sources.sort()

    assigned: set[tuple[str, str]] = set()
    cyclic: list[tuple[tuple[str, str], ...]] = []
    for start in reversed(finish_order):
        if start in assigned:
            continue
        component: list[tuple[str, str]] = []
        stack = [start]
        assigned.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for source in reversed(reverse[node]):
                if source not in assigned:
                    assigned.add(source)
                    stack.append(source)
        ordered = tuple(sorted(component))
        if len(ordered) > 1 or ordered[0] in edges[ordered[0]]:
            cyclic.append(ordered)
    return sorted(cyclic)


def _resolve_reference_literal(
    reference: str,
    *,
    current_schema_id: str,
    known_ids: frozenset[str],
    location_sets: dict[str, frozenset[str]],
) -> tuple[tuple[str, str] | None, DiagnosticCode | None]:
    if reference.startswith("#"):
        if not reference.startswith("#/") or reference.count("#") != 1:
            return None, DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN
        pointer = reference[1:]
        if not _valid_pointer_literal(pointer):
            return None, DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN
        if pointer not in location_sets[current_schema_id]:
            return None, DiagnosticCode.SCHEMA_UNRESOLVED_REF
        return (current_schema_id, pointer), None

    if reference.count("#") > 1:
        return None, DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN
    if "#" in reference:
        schema_id, fragment = reference.split("#", 1)
        if (
            not _valid_schema_id(schema_id)
            or not fragment.startswith("/")
            or not _valid_pointer_literal(fragment)
        ):
            return None, DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN
        if schema_id not in known_ids or fragment not in location_sets[schema_id]:
            return None, DiagnosticCode.SCHEMA_UNRESOLVED_REF
        return (schema_id, fragment), None

    if not _valid_schema_id(reference):
        return None, DiagnosticCode.SCHEMA_REMOTE_REF_FORBIDDEN
    if reference not in known_ids:
        return None, DiagnosticCode.SCHEMA_UNRESOLVED_REF
    return (reference, ""), None


def _registry_entries(
    registry: Any,
) -> tuple[_RegisteredSchema, ...] | None:
    if type(registry) is not ContractSchemaRegistry:
        return None
    try:
        token = object.__getattribute__(registry, "_ContractSchemaRegistry__token")
        entries = object.__getattribute__(registry, "_ContractSchemaRegistry__entries")
        seal = object.__getattribute__(registry, "_ContractSchemaRegistry__seal")
    except AttributeError:
        return None
    if token is not _REGISTRY_CONSTRUCTION_TOKEN or type(entries) is not tuple:
        return None
    if not entries or any(type(entry) is not _RegisteredSchema for entry in entries):
        return None
    for entry in entries:
        try:
            asset_id = object.__getattribute__(entry, "asset_id")
            media_type = object.__getattribute__(entry, "media_type")
            byte_size = object.__getattribute__(entry, "byte_size")
            sha256 = object.__getattribute__(entry, "sha256")
            schema_id = object.__getattribute__(entry, "schema_id")
            raw_bytes = object.__getattribute__(entry, "raw_bytes")
            document = object.__getattribute__(entry, "document")
        except AttributeError:
            return None
        if (
            type(asset_id) is not str
            or type(media_type) is not str
            or type(byte_size) is not int
            or type(sha256) is not str
            or type(schema_id) is not str
            or type(raw_bytes) is not bytes
            or type(document) is not _FrozenObject
        ):
            return None
    if type(seal) is not str or seal != _registry_seal(entries):
        return None
    previous_schema_id: str | None = None
    asset_ids: set[str] = set()
    for entry in entries:
        if (
            type(entry.asset_id) is not str
            or type(entry.media_type) is not str
            or entry.media_type != SCHEMA_MEDIA_TYPE
            or type(entry.byte_size) is not int
            or type(entry.sha256) is not str
            or type(entry.schema_id) is not str
            or not _valid_schema_id(entry.schema_id)
            or type(entry.raw_bytes) is not bytes
            or type(entry.document) is not _FrozenObject
            or entry.byte_size != len(entry.raw_bytes)
            or entry.sha256 != raw_asset_sha256(entry.raw_bytes)
            or entry.asset_id in asset_ids
            or (previous_schema_id is not None and previous_schema_id >= entry.schema_id)
        ):
            return None
        try:
            document = _thaw_json(entry.document)
        except (AttributeError, TypeError, ValueError, RecursionError, OverflowError):
            return None
        if type(document) is not dict or document.get("$id") != entry.schema_id:
            return None
        parsed = parse_canonical_json(entry.raw_bytes)
        if (
            isinstance(parsed, Diagnostic)
            or parsed.to_python() != document
            or canonical_bytes(parsed) != _canonical_bytes_from_document(document)
        ):
            return None
        asset_ids.add(entry.asset_id)
        previous_schema_id = entry.schema_id
    return entries


def _canonical_bytes_from_document(document: dict[str, Any]) -> bytes:
    """Return strict canonical bytes for an already frozen internal document."""

    # The raw document has already crossed the strict parser.  Reparse its
    # deterministic JSON spelling rather than accepting a host-created value.
    raw = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    parsed = parse_canonical_json(raw)
    if isinstance(parsed, Diagnostic):
        raise ValueError("internal frozen schema is not canonical JSON")
    return canonical_bytes(parsed)


def _registry_seal(entries: tuple[_RegisteredSchema, ...]) -> str:
    digest = hashlib.sha256()
    if type(entries) is not tuple:
        return "invalid"
    try:
        for entry in entries:
            if type(entry) is not _RegisteredSchema:
                return "invalid"
            for value in (
                entry.asset_id,
                entry.media_type,
                str(entry.byte_size),
                entry.sha256,
                entry.schema_id,
                raw_asset_sha256(entry.raw_bytes),
            ):
                encoded = value.encode("utf-8")
                digest.update(len(encoded).to_bytes(8, "big"))
                digest.update(encoded)
            frozen_bytes = _canonical_machine_bytes(_thaw_json(entry.document))
            digest.update(len(frozen_bytes).to_bytes(8, "big"))
            digest.update(frozen_bytes)
    except Exception:
        return "invalid"
    return "sha256:" + digest.hexdigest()


def _freeze_json(value: Any) -> Any:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is list:
        return tuple(_freeze_json(item) for item in value)
    if type(value) is dict:
        return _FrozenObject(
            tuple((key, _freeze_json(value[key])) for key in sorted(value))
        )
    raise TypeError("schema snapshot contains a non-JSON value")


def _thaw_json(value: Any) -> Any:
    return _thaw_json_node(value, 0, set())


def _thaw_json_node(value: Any, depth: int, active: set[int]) -> Any:
    if depth > MAX_NESTING:
        raise ValueError("frozen schema exceeds the canonical nesting limit")
    if type(value) is _FrozenObject:
        identity = id(value)
        if identity in active:
            raise ValueError("frozen schema contains an object cycle")
        active.add(identity)
        pairs = object.__getattribute__(value, "pairs")
        if type(pairs) is not tuple:
            active.remove(identity)
            raise TypeError("frozen object pairs are not a tuple")
        try:
            result: dict[str, Any] = {}
            previous: str | None = None
            for pair in pairs:
                if type(pair) is not tuple or len(pair) != 2:
                    raise TypeError("frozen object pair is malformed")
                key, child = pair
                if type(key) is not str or (previous is not None and previous >= key):
                    raise TypeError("frozen object keys are invalid")
                result[key] = _thaw_json_node(child, depth + 1, active)
                previous = key
            return result
        finally:
            active.remove(identity)
    if type(value) is tuple:
        identity = id(value)
        if identity in active:
            raise ValueError("frozen schema contains an array cycle")
        active.add(identity)
        try:
            return [_thaw_json_node(item, depth + 1, active) for item in value]
        finally:
            active.remove(identity)
    if value is None or type(value) in (bool, int, str):
        return value
    raise TypeError("frozen schema contains an invalid node")


def _diagnostic(
    code: DiagnosticCode,
    message: str,
    *,
    pointer: str = "",
    phase: str,
    subject: str | None = None,
    schema_pointer: str | None = None,
    details: Any = None,
) -> Diagnostic:
    return Diagnostic(
        code,
        message,
        pointer,
        None,
        phase,
        subject,
        schema_pointer,
        details,
    )


def _input_type_diagnostic(message: str) -> Diagnostic:
    return _diagnostic(
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
        message,
        phase="REGISTRY_INPUT",
    )


def _meta_diagnostic(
    subject: str,
    pointer: str,
    message: str,
    *,
    details: Any = None,
) -> Diagnostic:
    return _diagnostic(
        DiagnosticCode.SCHEMA_META_INVALID,
        message,
        pointer=pointer,
        phase="REGISTRY_SCHEMA_META",
        subject=subject,
        details=details,
    )


def _enrich(diagnostic: Diagnostic, *, phase: str, subject: str) -> Diagnostic:
    return Diagnostic(
        diagnostic.code,
        diagnostic.message,
        diagnostic.json_pointer,
        diagnostic.byte_offset,
        phase,
        subject,
        diagnostic.schema_pointer,
        diagnostic.details,
    )


def _attach_binding_observation(
    diagnostics: list[Diagnostic],
    snapshot: _InputSnapshot,
    *,
    declared_schema_id: str | None = None,
) -> list[Diagnostic]:
    observation = dict(snapshot.binding_observation)
    if declared_schema_id is not None:
        observation["declared_schema_id"] = declared_schema_id
    result: list[Diagnostic] = []
    for diagnostic in diagnostics:
        serialized = diagnostic.to_dict()
        existing_details = serialized.get("details")
        details = {} if existing_details is None else existing_details
        if type(details) is not dict:
            raise TypeError("internal diagnostic details must be an object")
        details["binding_observation"] = observation
        result.append(
            Diagnostic(
                diagnostic.code,
                diagnostic.message,
                diagnostic.json_pointer,
                diagnostic.byte_offset,
                diagnostic.phase,
                diagnostic.subject_identity,
                diagnostic.schema_pointer,
                details,
            )
        )
    return result


def _sort_diagnostics(diagnostics: list[Diagnostic]) -> tuple[Diagnostic, ...]:
    ordered = sorted(diagnostics, key=_diagnostic_sort_key)
    result: list[Diagnostic] = []
    previous: bytes | None = None
    for diagnostic in ordered:
        serialized = _canonical_machine_bytes(diagnostic.to_dict())
        if serialized != previous:
            result.append(diagnostic)
            previous = serialized
    return tuple(result)


def _diagnostic_sort_key(diagnostic: Diagnostic) -> tuple[Any, ...]:
    machine_fields = diagnostic.to_dict()
    message = machine_fields.pop("message")
    return (
        _PHASE_RANK.get(diagnostic.phase or "", 999),
        (diagnostic.subject_identity or "").encode("utf-8"),
        diagnostic.json_pointer.encode("utf-8"),
        (diagnostic.schema_pointer or "").encode("utf-8"),
        str(diagnostic.code).encode("ascii"),
        _canonical_machine_bytes(machine_fields),
        message.encode("utf-8"),
    )


def _canonical_machine_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _child(pointer: str, token: str) -> str:
    encoded = token.replace("~", "~0").replace("/", "~1")
    return f"{pointer}/{encoded}"


def _path_pointer(path: Any) -> str:
    pointer = ""
    try:
        parts = tuple(path)
    except TypeError:
        return ""
    for part in parts:
        pointer = _child(pointer, str(part))
    return pointer


__all__ = [
    "ContractSchemaRegistry",
    "SchemaAssetBinding",
    "build_schema_registry",
]
