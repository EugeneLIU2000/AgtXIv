"""Pure intrinsic validation for ``TypedTerminalResult/1.0.0``.

The compiled schema reference below pins the exact family-schema ruler used by
this implementation.  An intrinsic pass checks only one submitted immutable
record.  It does not resolve context or evidence, satisfy an obligation, or
grant merge, release, archive, certification, or knowledge-admission authority.
"""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any

from .canonical import (
    CanonicalValueIntegrityError,
    ParsedCanonicalValue,
    build_canonical_value,
    canonical_bytes,
)
from .diagnostics import Diagnostic, DiagnosticCode
from .registry import ContractSchemaRegistry, _registry_entries
from .schema_validation import validate_immutable_record_payload


_TERMINAL_SCHEMA_ID = (
    "https://agtxiv.org/schema/v2/contract-kernel/terminal/"
    "typed-terminal-result/1.0.0"
)
_TERMINAL_RECORD_TYPE = "agtxiv.typed-terminal-result/1.0.0"
_TERMINAL_SCHEMA_ASSET_ID = "schema:typed-terminal-result:1.0.0"
_TERMINAL_SCHEMA_MEDIA_TYPE = "application/schema+json"
_TERMINAL_SCHEMA_BYTE_SIZE = 16_054
_TERMINAL_SCHEMA_SHA256 = (
    "sha256:3384964d6e02bc326660ab56bb79c816ff0b6233ea8bb91aca5ba2c383a1a5e6"
)
_TERMINAL_SCHEMA_EXACT_REF = MappingProxyType(
    {
        "asset_id": _TERMINAL_SCHEMA_ASSET_ID,
        "media_type": _TERMINAL_SCHEMA_MEDIA_TYPE,
        "byte_size": _TERMINAL_SCHEMA_BYTE_SIZE,
        "sha256": _TERMINAL_SCHEMA_SHA256,
        "schema_uri": _TERMINAL_SCHEMA_ID,
    }
)

_ASSET_REQUIRED_FIELDS = ("asset_id", "media_type", "byte_size", "sha256")
_ASSET_IDENTITY_FIELDS = (*_ASSET_REQUIRED_FIELDS, "schema_uri")
_ASSET_ALLOWED_FIELDS = frozenset((*_ASSET_IDENTITY_FIELDS, "path_hint"))
_RECORD_FIELDS = (
    "record_type",
    "record_id",
    "record_revision",
    "schema_ref",
    "content_hash",
)
_COMPONENT_FIELDS = (*_RECORD_FIELDS, "component_id", "json_pointer")

_RESERVED_TERMINAL_FAMILIES = frozenset(
    {"TYPED_STAGE_FAMILY_TERMINAL_RESULT", "TYPED_TERMINAL_RESULT"}
)
_RESOURCE_FIELDS = (
    ("max_wall_time_ms", "wall_time_ms"),
    ("max_cpu_time_ms", "cpu_time_ms"),
    ("max_peak_memory_bytes", "peak_memory_bytes"),
    ("max_input_bytes", "input_bytes"),
    ("max_output_bytes", "output_bytes"),
    ("max_network_requests", "network_requests"),
)
_RESOURCE_ORDER = {name: index for index, (_, name) in enumerate(_RESOURCE_FIELDS)}

_OUTCOME_RETRY = {
    "UNAVAILABLE": frozenset(
        {"RETRY_AFTER_CONDITION", "NO_RETRY_IN_CURRENT_CONTEXT"}
    ),
    "RETRY_REQUIRED": frozenset({"RETRY_AFTER_CONDITION"}),
    "REVIEW_REQUIRED": frozenset({"REVIEW_DECIDES"}),
    "BLOCKED": frozenset(
        {"RETRY_AFTER_CONDITION", "NO_RETRY_IN_CURRENT_CONTEXT"}
    ),
    "FAILED": frozenset(
        {
            "RETRY_AFTER_CONDITION",
            "NO_RETRY_IN_CURRENT_CONTEXT",
            "REVIEW_DECIDES",
        }
    ),
}
_OUTCOME_ACTION = {
    "UNAVAILABLE": frozenset({"PROVIDE_INPUT", "RESOLVE_DEPENDENCY"}),
    "RETRY_REQUIRED": frozenset({"RETRY"}),
    "REVIEW_REQUIRED": frozenset({"MANUAL_REVIEW"}),
    "BLOCKED": frozenset(
        {"RESOLVE_DEPENDENCY", "RESOLVE_POLICY", "ESCALATE"}
    ),
    "FAILED": frozenset({"FIX_IMPLEMENTATION", "MANUAL_REVIEW", "ESCALATE"}),
}

_PHASE_RANK = {
    "TERMINAL_INPUT": 1,
    "TERMINAL_SCHEMA_BINDING": 2,
    "TERMINAL_ATTEMPT": 3,
    "TERMINAL_CONTEXT": 4,
    "TERMINAL_TARGET": 5,
    "TERMINAL_EVIDENCE": 6,
    "TERMINAL_DISPOSITION": 7,
    "TERMINAL_RESOURCE": 8,
}


def validate_typed_terminal_result_intrinsic(
    record: ParsedCanonicalValue,
    registry: ContractSchemaRegistry,
) -> tuple[Diagnostic, ...]:
    """Validate one terminal record without resolving referenced targets.

    An empty result proves intrinsic conformance only.  It does not prove that
    an obligation was satisfied, a review passed, or knowledge may be admitted.
    """

    try:
        return _validate_typed_terminal_result_intrinsic(record, registry)
    except Exception:
        return (
            _diagnostic(
                DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
                "terminal validation could not safely inspect the submitted typed values",
                phase="TERMINAL_INPUT",
            ),
        )


def _validate_typed_terminal_result_intrinsic(
    record: ParsedCanonicalValue,
    registry: ContractSchemaRegistry,
) -> tuple[Diagnostic, ...]:
    if type(record) is not ParsedCanonicalValue or type(registry) is not ContractSchemaRegistry:
        return (
            _diagnostic(
                DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
                "terminal validation requires exact ParsedCanonicalValue and ContractSchemaRegistry types",
                phase="TERMINAL_INPUT",
            ),
        )
    if _registry_entries(registry) is None:
        return (
            _diagnostic(
                DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
                "schema registry failed its frozen snapshot integrity check",
                phase="TERMINAL_INPUT",
            ),
        )
    try:
        document = record.to_python()
    except CanonicalValueIntegrityError:
        return (
            _diagnostic(
                DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
                "record opaque value failed its integrity check",
                phase="TERMINAL_INPUT",
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
    if type(envelope) is not dict:
        return (
            _diagnostic(
                DiagnosticCode.RECORD_INVALID_ENVELOPE,
                "record envelope is not a canonical JSON object",
                pointer="/envelope",
                phase="RECORD_ENVELOPE",
            ),
        )
    schema_ref = envelope.get("schema_ref")
    if type(schema_ref) is not dict:
        return (
            _diagnostic(
                DiagnosticCode.RECORD_INVALID_ENVELOPE,
                "schema_ref must be an exact schema asset reference",
                pointer="/envelope/schema_ref",
                phase="RECORD_ENVELOPE",
            ),
        )

    gate_two: list[Diagnostic] = []
    official_projection = _asset_projection(schema_ref, require_schema_uri=True)
    if official_projection != dict(_TERMINAL_SCHEMA_EXACT_REF):
        gate_two.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_SCHEMA_MISMATCH,
                "envelope schema_ref does not name the compiled official terminal schema bytes",
                pointer="/envelope/schema_ref",
                phase="TERMINAL_SCHEMA_BINDING",
                details={"expected_schema_version": "1.0.0"},
            )
        )
    if "producer_context" not in envelope:
        gate_two.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_ATTEMPT_MISMATCH,
                "typed terminal result requires envelope producer_context",
                pointer="/envelope/producer_context",
                phase="TERMINAL_ATTEMPT",
                details={"reason": "MISSING_PRODUCER_CONTEXT"},
            )
        )
    if gate_two:
        return _sort_diagnostics(gate_two)

    generic = validate_immutable_record_payload(record, registry)
    if generic:
        return generic

    payload = document["payload"]
    producer_context = envelope["producer_context"]
    subject = envelope["record_id"]
    diagnostics: list[Diagnostic] = []

    if payload["attempt_id"] != producer_context["attempt_id"]:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_ATTEMPT_MISMATCH,
                "payload attempt_id differs from the envelope producer attempt",
                pointer="/payload/attempt_id",
                phase="TERMINAL_ATTEMPT",
                subject=subject,
                details={"reason": "ATTEMPT_ID_DIFFERENCE"},
            )
        )

    diagnostics.extend(_context_diagnostics(payload, subject))
    diagnostics.extend(_target_diagnostics(payload, subject))
    diagnostics.extend(_evidence_diagnostics(document, subject))
    diagnostics.extend(_disposition_diagnostics(payload, subject))
    diagnostics.extend(_resource_diagnostics(payload, subject))
    return _sort_diagnostics(diagnostics)


def _context_diagnostics(payload: dict[str, Any], subject: str) -> list[Diagnostic]:
    context = payload["binding_context"]
    mode = context["context_mode"]
    if mode == "PROFILE_BOUND":
        return []
    basis = payload["target_obligation"]["basis"]
    if basis["basis_kind"] != "COMPONENT":
        return [
            _diagnostic(
                DiagnosticCode.TERMINAL_CONTEXT_INVALID,
                "plan- and scope-bound obligations require a component basis",
                pointer="/payload/target_obligation/basis",
                phase="TERMINAL_CONTEXT",
                subject=subject,
                details={"context_mode": mode, "reason": "COMPONENT_BASIS_REQUIRED"},
            )
        ]
    expected = context["plan_ref"] if mode == "PLAN_BOUND" else context["scope_ref"]
    actual = _record_projection(basis["component_ref"])
    if actual != _record_projection(expected):
        return [
            _diagnostic(
                DiagnosticCode.TERMINAL_CONTEXT_INVALID,
                "basis component record differs from the bound plan or frozen scope",
                pointer="/payload/target_obligation/basis/component_ref",
                phase="TERMINAL_CONTEXT",
                subject=subject,
                details={"context_mode": mode, "reason": "BASIS_RECORD_DIFFERENCE"},
            )
        ]
    return []


def _target_diagnostics(payload: dict[str, Any], subject: str) -> list[Diagnostic]:
    target = payload["target_obligation"]
    diagnostics: list[Diagnostic] = []
    if target["family_id"] in _RESERVED_TERMINAL_FAMILIES:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_TARGET_INVALID,
                "terminal result cannot be its own artifact-family obligation",
                pointer="/payload/target_obligation/family_id",
                phase="TERMINAL_TARGET",
                subject=subject,
                details={"reason": "TERMINAL_FAMILY"},
            )
        )
    basis = target["basis"]
    if basis["basis_kind"] in {"RECORD", "COMPONENT"}:
        field = "record_ref" if basis["basis_kind"] == "RECORD" else "component_ref"
        if basis[field]["record_type"] == _TERMINAL_RECORD_TYPE:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCode.TERMINAL_TARGET_INVALID,
                    "terminal record cannot be the basis of another terminal obligation",
                    pointer=f"/payload/target_obligation/basis/{field}/record_type",
                    phase="TERMINAL_TARGET",
                    subject=subject,
                    details={"reason": "TERMINAL_RECORD_BASIS"},
                )
            )
    return diagnostics


def _evidence_diagnostics(
    document: dict[str, Any],
    subject: str,
) -> list[Diagnostic]:
    evidence = document["payload"]["evidence"]
    envelope = document["envelope"]
    diagnostics: list[Diagnostic] = []
    seen_ids: set[str] = set()
    seen_refs: set[bytes] = set()
    previous_id: bytes | None = None
    for index, item in enumerate(evidence):
        base = f"/payload/evidence/{index}"
        evidence_id = item["evidence_id"]
        encoded_id = evidence_id.encode("utf-8")
        if evidence_id in seen_ids:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCode.TERMINAL_EVIDENCE_INVALID,
                    "evidence_id is duplicated",
                    pointer=f"{base}/evidence_id",
                    phase="TERMINAL_EVIDENCE",
                    subject=subject,
                    details={"reason": "DUPLICATE_EVIDENCE_ID"},
                )
            )
        seen_ids.add(evidence_id)
        if previous_id is not None and previous_id > encoded_id:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCode.TERMINAL_EVIDENCE_INVALID,
                    "evidence entries are not in strict UTF-8 evidence_id order",
                    pointer=f"{base}/evidence_id",
                    phase="TERMINAL_EVIDENCE",
                    subject=subject,
                    details={"reason": "EVIDENCE_ORDER"},
                )
            )
        previous_id = encoded_id

        ref, ref_field = _evidence_reference(item)
        projection = _reference_projection(item["evidence_kind"], ref)
        serialized = _projection_bytes(projection)
        if serialized in seen_refs:
            diagnostics.append(
                _diagnostic(
                    DiagnosticCode.TERMINAL_EVIDENCE_INVALID,
                    "underlying authoritative evidence reference is duplicated",
                    pointer=f"{base}/{ref_field}",
                    phase="TERMINAL_EVIDENCE",
                    subject=subject,
                    details={"reason": "DUPLICATE_REFERENCE"},
                )
            )
        seen_refs.add(serialized)

        if item["evidence_kind"] in {"RECORD", "COMPONENT"}:
            if ref["record_type"] == _TERMINAL_RECORD_TYPE:
                reason = (
                    "SELF_REFERENCE"
                    if _same_record_identity(ref, envelope)
                    else "TERMINAL_REFERENCE"
                )
                diagnostics.append(
                    _diagnostic(
                        DiagnosticCode.TERMINAL_EVIDENCE_INVALID,
                        "terminal record or component cannot be terminal evidence",
                        pointer=f"{base}/{ref_field}/record_type",
                        phase="TERMINAL_EVIDENCE",
                        subject=subject,
                        details={"reason": reason},
                    )
                )
    return diagnostics


def _disposition_diagnostics(
    payload: dict[str, Any],
    subject: str,
) -> list[Diagnostic]:
    outcome = payload["outcome"]
    retry = payload["retry"]["retry_disposition"]
    action = payload["next_action"]["action_code"]
    diagnostics: list[Diagnostic] = []
    if retry not in _OUTCOME_RETRY[outcome]:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_DISPOSITION_INVALID,
                "retry disposition is incompatible with the operational outcome",
                pointer="/payload/retry/retry_disposition",
                phase="TERMINAL_DISPOSITION",
                subject=subject,
                details={"reason": "OUTCOME_RETRY_MISMATCH"},
            )
        )
    if action not in _OUTCOME_ACTION[outcome]:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_DISPOSITION_INVALID,
                "next action is incompatible with the operational outcome",
                pointer="/payload/next_action/action_code",
                phase="TERMINAL_DISPOSITION",
                subject=subject,
                details={"reason": "OUTCOME_ACTION_MISMATCH"},
            )
        )
    return diagnostics


def _resource_diagnostics(payload: dict[str, Any], subject: str) -> list[Diagnostic]:
    resources = payload["resources"]
    limit = resources["limit"]
    observed = resources["observed"]
    unobserved = resources["unobserved_metrics"]
    expected = {
        observed_name
        for limit_name, observed_name in _RESOURCE_FIELDS
        if limit_name in limit
    }
    observed_names = set(observed)
    unobserved_names = set(unobserved)
    diagnostics: list[Diagnostic] = []
    relation_blocked = False
    if observed_names & unobserved_names:
        relation_blocked = True
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_RESOURCE_INVALID,
                "observed and unobserved resource dimensions overlap",
                pointer="/payload/resources/unobserved_metrics",
                phase="TERMINAL_RESOURCE",
                subject=subject,
                details={"reason": "OVERLAPPING_DIMENSIONS"},
            )
        )
    if observed_names | unobserved_names != expected:
        relation_blocked = True
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_RESOURCE_INVALID,
                "resource dimensions do not exactly partition the declared limit",
                pointer="/payload/resources",
                phase="TERMINAL_RESOURCE",
                subject=subject,
                details={"reason": "DIMENSION_PARTITION"},
            )
        )
    ordered_unobserved = sorted(unobserved, key=_RESOURCE_ORDER.__getitem__)
    if unobserved != ordered_unobserved:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_RESOURCE_INVALID,
                "unobserved resource dimensions are not in fixed metric order",
                pointer="/payload/resources/unobserved_metrics",
                phase="TERMINAL_RESOURCE",
                subject=subject,
                details={"reason": "DIMENSION_ORDER"},
            )
        )
    if relation_blocked:
        return diagnostics

    exceeded = any(
        observed_name in observed and observed[observed_name] > limit[limit_name]
        for limit_name, observed_name in _RESOURCE_FIELDS
        if limit_name in limit
    )
    expected_relation = (
        "EXCEEDED_OBSERVED_LIMIT"
        if exceeded
        else "INDETERMINATE"
        if unobserved
        else "WITHIN_OBSERVED_LIMITS"
    )
    if resources["relation"] != expected_relation:
        diagnostics.append(
            _diagnostic(
                DiagnosticCode.TERMINAL_RESOURCE_INVALID,
                "declared resource relation differs from the mechanical comparison",
                pointer="/payload/resources/relation",
                phase="TERMINAL_RESOURCE",
                subject=subject,
                details={
                    "declared_relation": resources["relation"],
                    "expected_relation": expected_relation,
                    "reason": "RELATION_MISMATCH",
                },
            )
        )
    return diagnostics


def _asset_projection(
    value: Any,
    *,
    require_schema_uri: bool = False,
) -> dict[str, Any] | None:
    if type(value) is not dict:
        return None
    keys = set(value)
    required = set(_ASSET_REQUIRED_FIELDS)
    if require_schema_uri:
        required.add("schema_uri")
    if not required <= keys or not keys <= _ASSET_ALLOWED_FIELDS:
        return None
    return {field: value[field] for field in _ASSET_IDENTITY_FIELDS if field in value}


def _record_projection(value: Any) -> dict[str, Any] | None:
    if type(value) is not dict or not set(_RECORD_FIELDS) <= set(value):
        return None
    schema_projection = _asset_projection(value.get("schema_ref"))
    if schema_projection is None:
        return None
    return {
        "record_type": value["record_type"],
        "record_id": value["record_id"],
        "record_revision": value["record_revision"],
        "schema_ref": schema_projection,
        "content_hash": value["content_hash"],
    }


def _component_projection(value: Any) -> dict[str, Any] | None:
    record = _record_projection(value)
    if record is None or type(value) is not dict or not set(_COMPONENT_FIELDS) <= set(value):
        return None
    return {
        **record,
        "component_id": value["component_id"],
        "json_pointer": value["json_pointer"],
    }


def _reference_projection(kind: str, value: dict[str, Any]) -> dict[str, Any]:
    if kind == "ASSET":
        projection = _asset_projection(value)
    elif kind == "RECORD":
        projection = _record_projection(value)
    else:
        projection = _component_projection(value)
    if projection is None:
        raise ValueError("schema-validated exact reference has no projection")
    return projection


def _evidence_reference(item: dict[str, Any]) -> tuple[dict[str, Any], str]:
    field = {
        "ASSET": "asset_ref",
        "RECORD": "record_ref",
        "COMPONENT": "component_ref",
    }[item["evidence_kind"]]
    return item[field], field


def _projection_bytes(value: dict[str, Any]) -> bytes:
    parsed = build_canonical_value(value)
    if not isinstance(parsed, ParsedCanonicalValue):
        raise ValueError("authoritative exact-reference projection is not canonical")
    return canonical_bytes(parsed)


def _same_record_identity(reference: dict[str, Any], envelope: dict[str, Any]) -> bool:
    return all(
        reference[field] == envelope[field]
        for field in ("record_type", "record_id", "record_revision")
    )


def _diagnostic(
    code: DiagnosticCode,
    message: str,
    *,
    pointer: str = "",
    phase: str,
    subject: str | None = None,
    details: Any = None,
) -> Diagnostic:
    return Diagnostic(
        code,
        message,
        pointer,
        None,
        phase,
        subject,
        None,
        details,
    )


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


__all__ = ["validate_typed_terminal_result_intrinsic"]
