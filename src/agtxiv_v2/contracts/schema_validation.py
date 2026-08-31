"""Generic immutable-record validation over an exact offline schema registry."""

from __future__ import annotations

import re
from types import MappingProxyType
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from rfc3339_validator import validate_rfc3339
from rfc3986_validator import validate_rfc3986

from .canonical import (
    CanonicalValueIntegrityError,
    ParsedCanonicalValue,
    build_canonical_value,
    record_content_hash,
)
from .diagnostics import Diagnostic, DiagnosticCode
from .references import validate_immutable_envelope
from .registry import (
    DRAFT_2020_12,
    SCHEMA_MEDIA_TYPE,
    ContractSchemaRegistry,
    _SCHEMA_ARRAY_KEYWORDS,
    _SCHEMA_MAP_KEYWORDS,
    _SINGLE_SCHEMA_KEYWORDS,
    _child,
    _diagnostic,
    _path_pointer,
    _registry_entries,
    _sort_diagnostics,
    _thaw_json,
)

_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}(?![\s\S])")
_CONTRACT_BUNDLE_RECORD_TYPE = "agtxiv.contract-bundle-release/1.0.0"


def _has_forbidden_uri_character(value: str) -> bool:
    return any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)


def _fixed_uri(instance: object) -> bool:
    if type(instance) is not str:
        return True
    if (
        not instance
        or _has_forbidden_uri_character(instance)
        or any(ord(character) > 0x7F for character in instance)
    ):
        return False
    try:
        match = validate_rfc3986(instance, rule="URI")
        return match is not None and match.start() == 0 and match.end() == len(instance)
    except Exception:
        return False


def _fixed_date_time(instance: object) -> bool:
    if type(instance) is not str:
        return True
    if (
        not instance
        or _has_forbidden_uri_character(instance)
        or any(ord(character) > 0x7F for character in instance)
    ):
        return False
    try:
        return bool(validate_rfc3339(instance.upper()))
    except Exception:
        return False


_FIXED_FORMAT_CHECKER = FormatChecker(formats=())
_FIXED_FORMAT_CHECKER.checkers = MappingProxyType(
    {
        "date-time": (_fixed_date_time, ()),
        "uri": (_fixed_uri, ()),
    }
)


def validate_immutable_record_payload(
    record: ParsedCanonicalValue,
    registry: ContractSchemaRegistry,
) -> tuple[Diagnostic, ...]:
    """Validate envelope, exact schema/type binding, payload, and content hash.

    The empty tuple means that this isolated record conforms to its exact
    supplied family schema.  It grants no bundle, release, archive, review, or
    knowledge-admission authority.
    """

    if type(record) is not ParsedCanonicalValue or type(registry) is not ContractSchemaRegistry:
        return (
            _diagnostic(
                DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
                "record validation requires exact ParsedCanonicalValue and ContractSchemaRegistry types",
                phase="RECORD_INPUT",
            ),
        )
    entries = _registry_entries(registry)
    if entries is None:
        return (
            _diagnostic(
                DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
                "schema registry failed its frozen snapshot integrity check",
                phase="RECORD_INPUT",
            ),
        )
    try:
        document = record.to_python()
    except CanonicalValueIntegrityError:
        return (
            _diagnostic(
                DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
                "record opaque value failed its integrity check",
                phase="RECORD_INPUT",
            ),
        )

    if type(document) is not dict or set(document) != {
        "envelope",
        "payload",
        "content_hash",
    }:
        return (
            _diagnostic(
                DiagnosticCode.RECORD_INVALID_ENVELOPE,
                "immutable record must contain exactly envelope, payload, and content_hash",
                phase="RECORD_ENVELOPE",
            ),
        )

    envelope = document["envelope"]
    record_id = envelope.get("record_id") if type(envelope) is dict else None
    subject = record_id if type(record_id) is str else None
    if type(envelope) is not dict:
        envelope_diagnostic = _diagnostic(
            DiagnosticCode.RECORD_INVALID_ENVELOPE,
            "record envelope is not a canonical JSON object",
            pointer="/envelope",
            phase="RECORD_ENVELOPE",
            subject=subject,
        )
    else:
        envelope_value = build_canonical_value(envelope)
        if not isinstance(envelope_value, ParsedCanonicalValue):
            envelope_diagnostic = _diagnostic(
                DiagnosticCode.RECORD_INVALID_ENVELOPE,
                "record envelope is not a canonical JSON object",
                pointer="/envelope",
                phase="RECORD_ENVELOPE",
                subject=subject,
            )
        else:
            record_type = envelope.get("record_type")
            contract_bound = record_type != _CONTRACT_BUNDLE_RECORD_TYPE
            problem = validate_immutable_envelope(
                envelope_value,
                contract_bound=contract_bound,
            )
            envelope_diagnostic = (
                None
                if problem is None
                else _envelope_record_diagnostic(problem, subject)
            )

    hash_diagnostic = _record_hash_diagnostic(record, document, subject)
    if envelope_diagnostic is not None:
        diagnostics = [envelope_diagnostic]
        if hash_diagnostic is not None:
            diagnostics.append(hash_diagnostic)
        return _sort_diagnostics(diagnostics)

    schema_ref = envelope["schema_ref"]
    entry, binding_diagnostics = _bind_record_schema(schema_ref, entries, subject)
    if binding_diagnostics:
        if hash_diagnostic is not None:
            binding_diagnostics.append(hash_diagnostic)
        return _sort_diagnostics(binding_diagnostics)
    assert entry is not None

    schema = _thaw_json(entry.document)
    definitions = schema.get("$defs") if type(schema) is dict else None
    record_type_declaration = (
        definitions.get("recordType") if type(definitions) is dict else None
    )
    declared_record_type = (
        record_type_declaration.get("const")
        if type(record_type_declaration) is dict
        else None
    )
    if (
        type(declared_record_type) is not str
        or declared_record_type != envelope["record_type"]
    ):
        diagnostics = [
            _diagnostic(
                DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH,
                "record_type does not match the exact family schema declaration",
                pointer="/envelope/record_type",
                schema_pointer="/$defs/recordType/const",
                phase="RECORD_TYPE_BINDING",
                subject=subject,
                details={
                    "declared_record_type": (
                        declared_record_type
                        if type(declared_record_type) is str
                        else None
                    ),
                    "declaration_is_string": type(declared_record_type) is str,
                },
            )
        ]
        if hash_diagnostic is not None:
            diagnostics.append(hash_diagnostic)
        return _sort_diagnostics(diagnostics)

    payload_schema = definitions.get("payload") if type(definitions) is dict else None
    if type(payload_schema) not in (dict, bool):
        payload_diagnostics = [
            _diagnostic(
                DiagnosticCode.RECORD_PAYLOAD_INVALID,
                "family schema has no schema-valued $defs/payload entry point",
                pointer="/payload",
                schema_pointer="/$defs/payload",
                phase="RECORD_PAYLOAD",
                subject=subject,
            )
        ]
    else:
        payload_diagnostics = _validate_payload(
            document["payload"],
            entry.schema_id,
            entries,
            subject,
        )

    if hash_diagnostic is not None:
        payload_diagnostics.append(hash_diagnostic)
    return _sort_diagnostics(payload_diagnostics)


def _record_hash_diagnostic(
    record: ParsedCanonicalValue,
    document: dict[str, Any],
    subject: str | None,
) -> Diagnostic | None:
    stored = document["content_hash"]
    computed = record_content_hash(record)
    if (
        type(stored) is not str
        or _DIGEST_PATTERN.fullmatch(stored) is None
        or not isinstance(computed, str)
        or stored != computed
    ):
        return _diagnostic(
            DiagnosticCode.RECORD_HASH_MISMATCH,
            "stored record content_hash differs from the canonical record projection",
            pointer="/content_hash",
            phase="RECORD_HASH",
            subject=subject,
        )
    return None


def _envelope_record_diagnostic(
    problem: Diagnostic,
    subject: str | None,
) -> Diagnostic:
    pointer = "/envelope" + problem.json_pointer
    return Diagnostic(
        problem.code,
        problem.message,
        pointer,
        problem.byte_offset,
        "RECORD_ENVELOPE",
        subject,
        problem.schema_pointer,
        problem.details,
    )


def _bind_record_schema(
    schema_ref: dict[str, Any],
    entries: tuple[Any, ...],
    subject: str | None,
) -> tuple[Any | None, list[Diagnostic]]:
    matches = [entry for entry in entries if entry.asset_id == schema_ref["asset_id"]]
    if len(matches) != 1:
        return None, [
            _diagnostic(
                DiagnosticCode.REF_UNRESOLVED,
                "record schema_ref does not resolve to exactly one registered asset",
                pointer="/envelope/schema_ref/asset_id",
                phase="RECORD_SCHEMA_BINDING",
                subject=subject,
            )
        ]
    entry = matches[0]
    diagnostics: list[Diagnostic] = []
    if schema_ref["media_type"] != SCHEMA_MEDIA_TYPE or entry.media_type != schema_ref["media_type"]:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "record schema_ref media type differs from the exact registered schema",
                pointer="/envelope/schema_ref/media_type",
                phase="RECORD_SCHEMA_BINDING",
                subject=subject,
            )
        )
    if schema_ref.get("schema_uri") != entry.schema_id:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_TYPE_MISMATCH,
                "record schema_ref schema_uri differs from the registered schema $id",
                pointer="/envelope/schema_ref/schema_uri",
                phase="RECORD_SCHEMA_BINDING",
                subject=subject,
            )
        )
    if schema_ref["byte_size"] != entry.byte_size:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_HASH_MISMATCH,
                "record schema_ref byte size differs from the registered raw schema",
                pointer="/envelope/schema_ref/byte_size",
                phase="RECORD_SCHEMA_BINDING",
                subject=subject,
            )
        )
    if schema_ref["sha256"] != entry.sha256:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.REF_HASH_MISMATCH,
                "record schema_ref digest differs from the registered raw schema",
                pointer="/envelope/schema_ref/sha256",
                phase="RECORD_SCHEMA_BINDING",
                subject=subject,
            )
        )
    return (None, diagnostics) if diagnostics else (entry, [])


def _validate_payload(
    payload: Any,
    family_schema_id: str,
    entries: tuple[Any, ...],
    subject: str | None,
) -> list[Diagnostic]:
    try:
        node_locations: dict[int, tuple[str, str, bool | None]] = {}
        resources: list[tuple[str, Resource[Any]]] = []
        for entry in entries:
            validation_document = _validation_schema_snapshot(
                _thaw_json(entry.document),
                entry.schema_id,
                node_locations,
            )
            resources.append(
                (entry.schema_id, Resource.from_contents(validation_document))
            )
        offline_registry = Registry().with_resources(resources)
        wrapper = {
            "$schema": DRAFT_2020_12,
            "$ref": f"{family_schema_id}#/$defs/payload",
        }
        validator = Draft202012Validator(
            wrapper,
            registry=offline_registry,
            format_checker=_FIXED_FORMAT_CHECKER,
        )
        errors = list(validator.iter_errors(payload))
    except Exception:
        return [
            _diagnostic(
                DiagnosticCode.RECORD_PAYLOAD_INVALID,
                "payload could not be safely evaluated by the exact offline family schema",
                pointer="/payload",
                schema_pointer="/$defs/payload",
                phase="RECORD_PAYLOAD",
                subject=subject,
            )
        ]

    diagnostics: list[Diagnostic] = []
    expanded_dependency_groups: set[tuple[int, str, str]] = set()
    for error in errors:
        validator_name = error.validator if type(error.validator) is str else "unknown"
        if validator_name in {"required", "dependentRequired"}:
            group = (
                id(error.schema),
                _path_pointer(error.absolute_path),
                validator_name,
            )
            if group in expanded_dependency_groups:
                continue
            expanded_dependency_groups.add(group)
        location = node_locations.get(id(error.schema))
        if location is None:
            schema_id = family_schema_id
            schema_pointer = "/$defs/payload"
            location_status = "UNMAPPED_LIBRARY_SCHEMA_NODE"
        else:
            schema_id, node_pointer, boolean_schema = location
            if boolean_schema is None:
                schema_pointer = (
                    _child(node_pointer, validator_name)
                    if type(error.schema) is dict and validator_name in error.schema
                    else node_pointer
                )
                location_status = "EXACT_SCHEMA_NODE"
            else:
                schema_pointer = node_pointer
                validator_name = "false-schema" if boolean_schema is False else validator_name
                location_status = "EXACT_BOOLEAN_SCHEMA_NODE"
        diagnostics.extend(
            _payload_error_diagnostics(
                error,
                schema_id=schema_id,
                schema_pointer=schema_pointer,
                validator_name=validator_name,
                location_status=location_status,
                subject=subject,
            )
        )
    return diagnostics


def _payload_error_diagnostics(
    error: Any,
    *,
    schema_id: str,
    schema_pointer: str,
    validator_name: str,
    location_status: str,
    subject: str | None,
) -> list[Diagnostic]:
    base_instance_pointer = "/payload" + _path_pointer(error.absolute_path)
    common_details = {
        "location_status": location_status,
        "schema_id": schema_id,
        "validator": validator_name,
    }

    if (
        validator_name == "required"
        and type(error.schema) is dict
        and type(error.schema.get("required")) is list
        and type(error.instance) is dict
    ):
        missing = [
            (index, name)
            for index, name in enumerate(error.schema["required"])
            if type(name) is str and name not in error.instance
        ]
        if missing:
            return [
                _diagnostic(
                    DiagnosticCode.RECORD_PAYLOAD_INVALID,
                    "payload is missing a property required by the exact family schema",
                    pointer=_child(base_instance_pointer, name),
                    schema_pointer=_child(schema_pointer, str(index)),
                    phase="RECORD_PAYLOAD",
                    subject=subject,
                    details={**common_details, "required_property": name},
                )
                for index, name in missing
            ]

    if (
        validator_name == "dependentRequired"
        and type(error.schema) is dict
        and type(error.schema.get("dependentRequired")) is dict
        and type(error.instance) is dict
    ):
        missing_dependencies: list[tuple[str, int, str]] = []
        for trigger in sorted(error.schema["dependentRequired"]):
            dependencies = error.schema["dependentRequired"][trigger]
            if trigger not in error.instance or type(dependencies) is not list:
                continue
            for index, name in enumerate(dependencies):
                if type(name) is str and name not in error.instance:
                    missing_dependencies.append((trigger, index, name))
        if missing_dependencies:
            return [
                _diagnostic(
                    DiagnosticCode.RECORD_PAYLOAD_INVALID,
                    "payload is missing a property required by a present dependent field",
                    pointer=_child(base_instance_pointer, name),
                    schema_pointer=_child(
                        _child(schema_pointer, trigger),
                        str(index),
                    ),
                    phase="RECORD_PAYLOAD",
                    subject=subject,
                    details={
                        **common_details,
                        "required_property": name,
                        "trigger_property": trigger,
                    },
                )
                for trigger, index, name in missing_dependencies
            ]

    return [
        _diagnostic(
            DiagnosticCode.RECORD_PAYLOAD_INVALID,
            "payload does not satisfy the exact family schema",
            pointer=base_instance_pointer,
            schema_pointer=schema_pointer,
            phase="RECORD_PAYLOAD",
            subject=subject,
            details=common_details,
        )
    ]


def _validation_schema_snapshot(
    document: dict[str, Any],
    schema_id: str,
    node_locations: dict[int, tuple[str, str, bool | None]],
) -> dict[str, Any]:
    transformed = _transform_schema_node(
        document,
        "",
        schema_id,
        node_locations,
    )
    assert type(transformed) is dict
    return transformed


def _transform_schema_node(
    node: Any,
    pointer: str,
    schema_id: str,
    node_locations: dict[int, tuple[str, str, bool | None]],
) -> Any:
    if type(node) is bool:
        transformed = (
            {"$comment": f"validation-only true schema at {pointer}"}
            if node
            else {
                "$comment": f"validation-only false schema at {pointer}",
                "not": {},
            }
        )
        node_locations[id(transformed)] = (schema_id, pointer, node)
        return transformed
    if type(node) is not dict:
        raise TypeError("verified schema location is not an object or boolean")

    transformed: dict[str, Any] = dict(node)
    node_locations[id(transformed)] = (schema_id, pointer, None)
    for keyword in _SCHEMA_MAP_KEYWORDS:
        if keyword in node:
            transformed[keyword] = {
                name: _transform_schema_node(
                    child,
                    _child(_child(pointer, keyword), name),
                    schema_id,
                    node_locations,
                )
                for name, child in node[keyword].items()
            }
    for keyword in _SCHEMA_ARRAY_KEYWORDS:
        if keyword in node:
            transformed[keyword] = [
                _transform_schema_node(
                    child,
                    _child(_child(pointer, keyword), str(index)),
                    schema_id,
                    node_locations,
                )
                for index, child in enumerate(node[keyword])
            ]
    for keyword in _SINGLE_SCHEMA_KEYWORDS:
        if keyword in node:
            transformed[keyword] = _transform_schema_node(
                node[keyword],
                _child(pointer, keyword),
                schema_id,
                node_locations,
            )
    return transformed


__all__ = ["validate_immutable_record_payload"]
