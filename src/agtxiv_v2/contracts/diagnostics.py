"""Stable diagnostics emitted by the V2 contract kernel."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
import unicodedata


_DETAIL_MAX_NESTING = 256
_DETAIL_MIN_INTEGER = -9_007_199_254_740_991
_DETAIL_MAX_INTEGER = 9_007_199_254_740_991


class DiagnosticCode(StrEnum):
    """Stable machine codes for canonical JSON validation."""

    BOM_FORBIDDEN = "AGTXIV.CANON.BOM_FORBIDDEN"
    INVALID_UTF8 = "AGTXIV.CANON.INVALID_UTF8"
    INVALID_JSON = "AGTXIV.CANON.INVALID_JSON"
    DUPLICATE_KEY = "AGTXIV.CANON.DUPLICATE_KEY"
    NORMALIZED_KEY_COLLISION = "AGTXIV.CANON.NORMALIZED_KEY_COLLISION"
    UNPAIRED_SURROGATE = "AGTXIV.CANON.UNPAIRED_SURROGATE"
    UNSUPPORTED_NUMBER = "AGTXIV.CANON.UNSUPPORTED_NUMBER"
    INTEGER_OUT_OF_RANGE = "AGTXIV.CANON.INTEGER_OUT_OF_RANGE"
    NESTING_TOO_DEEP = "AGTXIV.CANON.NESTING_TOO_DEEP"
    UNSUPPORTED_PROGRAMMATIC_TYPE = "AGTXIV.CANON.UNSUPPORTED_PROGRAMMATIC_TYPE"
    NON_STRING_OBJECT_KEY = "AGTXIV.CANON.NON_STRING_OBJECT_KEY"
    CYCLIC_PROGRAMMATIC_VALUE = "AGTXIV.CANON.CYCLIC_PROGRAMMATIC_VALUE"
    INVALID_RECORD_SHAPE = "AGTXIV.CANON.INVALID_RECORD_SHAPE"
    INVALID_INTERNAL_VALUE = "AGTXIV.CANON.INVALID_INTERNAL_VALUE"
    REF_UNRESOLVED = "AGTXIV.REF.UNRESOLVED"
    REF_HASH_MISMATCH = "AGTXIV.REF.HASH_MISMATCH"
    REF_TYPE_MISMATCH = "AGTXIV.REF.TYPE_MISMATCH"
    CONTRACT_MUTABLE_REF = "AGTXIV.CONTRACT.MUTABLE_REF"
    RECORD_INVALID_ENVELOPE = "AGTXIV.RECORD.INVALID_ENVELOPE"
    RECORD_SUPERSESSION_MISMATCH = "AGTXIV.RECORD.SUPERSESSION_MISMATCH"
    RECORD_HASH_MISMATCH = "AGTXIV.RECORD.HASH_MISMATCH"
    SCHEMA_EMPTY_REGISTRY = "AGTXIV.SCHEMA.EMPTY_REGISTRY"
    SCHEMA_INPUT_TYPE_MISMATCH = "AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH"
    SCHEMA_INVALID_DOCUMENT = "AGTXIV.SCHEMA.INVALID_DOCUMENT"
    SCHEMA_DIALECT_MISMATCH = "AGTXIV.SCHEMA.DIALECT_MISMATCH"
    SCHEMA_ID_MISMATCH = "AGTXIV.SCHEMA.ID_MISMATCH"
    SCHEMA_DUPLICATE_ID = "AGTXIV.SCHEMA.DUPLICATE_ID"
    SCHEMA_META_INVALID = "AGTXIV.SCHEMA.META_INVALID"
    SCHEMA_UNRESOLVED_REF = "AGTXIV.SCHEMA.UNRESOLVED_REF"
    SCHEMA_REFERENCE_CYCLE = "AGTXIV.SCHEMA.REFERENCE_CYCLE"
    SCHEMA_REMOTE_REF_FORBIDDEN = "AGTXIV.SCHEMA.REMOTE_REF_FORBIDDEN"
    RECORD_TYPE_SCHEMA_MISMATCH = "AGTXIV.RECORD.TYPE_SCHEMA_MISMATCH"
    RECORD_PAYLOAD_INVALID = "AGTXIV.RECORD.PAYLOAD_INVALID"
    TERMINAL_SCHEMA_MISMATCH = "AGTXIV.TERMINAL.SCHEMA_MISMATCH"
    TERMINAL_ATTEMPT_MISMATCH = "AGTXIV.TERMINAL.ATTEMPT_MISMATCH"
    TERMINAL_CONTEXT_INVALID = "AGTXIV.TERMINAL.CONTEXT_INVALID"
    TERMINAL_TARGET_INVALID = "AGTXIV.TERMINAL.TARGET_INVALID"
    TERMINAL_EVIDENCE_INVALID = "AGTXIV.TERMINAL.EVIDENCE_INVALID"
    TERMINAL_DISPOSITION_INVALID = "AGTXIV.TERMINAL.DISPOSITION_INVALID"
    TERMINAL_RESOURCE_INVALID = "AGTXIV.TERMINAL.RESOURCE_INVALID"
    ASSET_SCHEMA_MISMATCH = "AGTXIV.CONTRACT.ASSET_SCHEMA_MISMATCH"
    ASSET_INVALID = "AGTXIV.CONTRACT.ASSET_INVALID"
    REQUIREMENTS_SOURCE_BINDING_MISMATCH = "AGTXIV.REQUIREMENTS.SOURCE_BINDING_MISMATCH"
    REQUIREMENTS_ITEM_SET_MISMATCH = "AGTXIV.REQUIREMENTS.ITEM_SET_MISMATCH"
    REQUIREMENTS_ITEM_ORDER_MISMATCH = "AGTXIV.REQUIREMENTS.ITEM_ORDER_MISMATCH"
    REQUIREMENTS_MAPPING_MISMATCH = "AGTXIV.REQUIREMENTS.MAPPING_MISMATCH"
    REQUIREMENTS_SELECTION_RULE_MISMATCH = "AGTXIV.REQUIREMENTS.SELECTION_RULE_MISMATCH"
    CATALOG_REFERENCE_INVALID = "AGTXIV.CATALOG.REFERENCE_INVALID"
    CATALOG_EXACT_REF_CYCLE = "AGTXIV.CATALOG.EXACT_REF_CYCLE"
    CATALOG_DUPLICATE_FAMILY = "AGTXIV.CATALOG.DUPLICATE_FAMILY"
    CATALOG_DUPLICATE_STAGE = "AGTXIV.CATALOG.DUPLICATE_STAGE"
    CATALOG_STRUCTURE_INVALID = "AGTXIV.CATALOG.STRUCTURE_INVALID"
    CATALOG_FAMILY_BINDING_INVALID = "AGTXIV.CATALOG.FAMILY_BINDING_INVALID"
    CATALOG_SUPPORT_ASSET_ROLE_INVALID = "AGTXIV.CATALOG.SUPPORT_ASSET_ROLE_INVALID"
    CATALOG_TERMINAL_POLICY_INVALID = "AGTXIV.CATALOG.TERMINAL_POLICY_INVALID"
    PROFILE_CATALOG_MISMATCH = "AGTXIV.PROFILE.CATALOG_MISMATCH"
    PROFILE_FAMILY_SET_INVALID = "AGTXIV.PROFILE.FAMILY_SET_INVALID"
    PROFILE_REQUIREMENT_WEAKENING = "AGTXIV.PROFILE.REQUIREMENT_WEAKENING"
    PROFILE_CARDINALITY_WEAKENING = "AGTXIV.PROFILE.CARDINALITY_WEAKENING"
    PROFILE_PRODUCER_EXPANSION = "AGTXIV.PROFILE.PRODUCER_EXPANSION"
    PROFILE_TERMINAL_POLICY_MISMATCH = "AGTXIV.PROFILE.TERMINAL_POLICY_MISMATCH"
    PROFILE_OUTCOME_EXPANSION = "AGTXIV.PROFILE.OUTCOME_EXPANSION"
    PROFILE_CONTEXT_WEAKENING = "AGTXIV.PROFILE.CONTEXT_WEAKENING"
    CATALOG_CONTEXT_BINDING_MISMATCH = "AGTXIV.CATALOG.CONTEXT_BINDING_MISMATCH"
    CATALOG_UNKNOWN_FAMILY = "AGTXIV.CATALOG.UNKNOWN_FAMILY"
    CATALOG_UNKNOWN_STAGE = "AGTXIV.CATALOG.UNKNOWN_STAGE"
    CATALOG_OBLIGATION_NOT_SELECTED = "AGTXIV.CATALOG.OBLIGATION_NOT_SELECTED"
    CATALOG_TERMINAL_NOT_ALLOWED = "AGTXIV.CATALOG.TERMINAL_NOT_ALLOWED"
    CATALOG_PRODUCER_ROLE_NOT_ALLOWED = "AGTXIV.CATALOG.PRODUCER_ROLE_NOT_ALLOWED"
    CATALOG_CONTEXT_MODE_INSUFFICIENT = "AGTXIV.CATALOG.CONTEXT_MODE_INSUFFICIENT"
    CATALOG_OUTCOME_NOT_ALLOWED = "AGTXIV.CATALOG.OUTCOME_NOT_ALLOWED"


@dataclass(frozen=True, slots=True)
class _FrozenDiagnosticObject:
    pairs: tuple[tuple[str, Any], ...]


def _normalized_detail_string(value: str) -> str:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise TypeError("diagnostic detail strings cannot contain unpaired surrogates")
    return unicodedata.normalize(
        "NFC",
        value.replace("\r\n", "\n").replace("\r", "\n"),
    )


def _freeze_details(
    value: Any,
    depth: int = 0,
    active: set[int] | None = None,
) -> Any:
    if depth > _DETAIL_MAX_NESTING:
        raise TypeError("diagnostic details exceed the canonical nesting limit")
    if active is None:
        active = set()
    if value is None or value is True or value is False:
        return value
    if type(value) is str:
        return _normalized_detail_string(value)
    if type(value) is int:
        if not _DETAIL_MIN_INTEGER <= value <= _DETAIL_MAX_INTEGER:
            raise TypeError("diagnostic detail integer is outside the I-JSON range")
        return value
    if type(value) in (list, tuple):
        identity = id(value)
        if identity in active:
            raise TypeError("diagnostic details contain an array cycle")
        active.add(identity)
        try:
            return tuple(
                _freeze_details(item, depth + 1, active) for item in value
            )
        finally:
            active.remove(identity)
    if type(value) in (dict, _FrozenDiagnosticObject):
        identity = id(value)
        if identity in active:
            raise TypeError("diagnostic details contain an object cycle")
        active.add(identity)
        try:
            items = (
                value.items()
                if type(value) is dict
                else object.__getattribute__(value, "pairs")
            )
            if type(value) is _FrozenDiagnosticObject and type(items) is not tuple:
                raise TypeError("diagnostic detail object pairs are malformed")
            pairs: list[tuple[str, Any]] = []
            normalized_keys: set[str] = set()
            for pair in items:
                if type(pair) is not tuple or len(pair) != 2:
                    raise TypeError("diagnostic detail object member is malformed")
                key, child = pair
                if type(key) is not str:
                    raise TypeError("diagnostic detail object keys must be strings")
                normalized_key = _normalized_detail_string(key)
                if normalized_key in normalized_keys:
                    raise TypeError("diagnostic detail keys collide after normalization")
                normalized_keys.add(normalized_key)
                pairs.append(
                    (
                        normalized_key,
                        _freeze_details(child, depth + 1, active),
                    )
                )
            pairs.sort(key=lambda pair: pair[0])
            return _FrozenDiagnosticObject(tuple(pairs))
        finally:
            active.remove(identity)
    raise TypeError("diagnostic details must be a JSON-compatible value")


def _thaw_details(
    value: Any,
    depth: int = 0,
    active: set[int] | None = None,
) -> Any:
    if depth > _DETAIL_MAX_NESTING:
        raise TypeError("diagnostic details exceed the canonical nesting limit")
    if active is None:
        active = set()
    if type(value) is _FrozenDiagnosticObject:
        identity = id(value)
        if identity in active:
            raise TypeError("diagnostic details contain an object cycle")
        active.add(identity)
        try:
            pairs = object.__getattribute__(value, "pairs")
            if type(pairs) is not tuple:
                raise TypeError("diagnostic detail object pairs are malformed")
            result: dict[str, Any] = {}
            previous: str | None = None
            for pair in pairs:
                if type(pair) is not tuple or len(pair) != 2:
                    raise TypeError("diagnostic detail object member is malformed")
                key, child = pair
                if type(key) is not str or (previous is not None and previous >= key):
                    raise TypeError("diagnostic detail object keys are malformed")
                result[key] = _thaw_details(child, depth + 1, active)
                previous = key
            return result
        finally:
            active.remove(identity)
    if type(value) is tuple:
        identity = id(value)
        if identity in active:
            raise TypeError("diagnostic details contain an array cycle")
        active.add(identity)
        try:
            return [_thaw_details(item, depth + 1, active) for item in value]
        finally:
            active.remove(identity)
    return value


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One deterministic validation failure.

    ``byte_offset`` is present when a failure can be located in raw input.
    ``json_pointer`` is an RFC 6901-style pointer rooted at the submitted value.
    Human-readable messages may improve while ``code`` retains its meaning.
    """

    code: DiagnosticCode
    message: str
    json_pointer: str = ""
    byte_offset: int | None = None
    phase: str | None = None
    subject_identity: str | None = None
    schema_pointer: str | None = None
    details: Any = None

    def __post_init__(self) -> None:
        if self.details is not None:
            object.__setattr__(self, "details", _freeze_details(self.details))

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": str(self.code),
            "message": self.message,
            "json_pointer": self.json_pointer,
        }
        if self.byte_offset is not None:
            result["byte_offset"] = self.byte_offset
        if self.phase is not None:
            result["phase"] = self.phase
        if self.subject_identity is not None:
            result["subject_identity"] = self.subject_identity
        if self.schema_pointer is not None:
            result["schema_pointer"] = self.schema_pointer
        if self.details is not None:
            result["details"] = _thaw_details(self.details)
        return result
