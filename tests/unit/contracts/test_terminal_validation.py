from __future__ import annotations

import builtins
import dataclasses
import itertools
import json
import os
import random
import socket
import subprocess
import sys
import time
from copy import deepcopy
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


ROOT = _add_local_src_package()

import agtxiv_v2.contracts.registry as registry_module  # noqa: E402
import agtxiv_v2.contracts.canonical as canonical_module  # noqa: E402
from agtxiv_v2.contracts import (  # noqa: E402
    ContractSchemaRegistry,
    Diagnostic,
    DiagnosticCode,
    IJSON_MAX_INTEGER,
    MAX_NESTING,
    ParsedCanonicalValue,
    SchemaAssetBinding,
    SuppliedAsset,
    build_canonical_value,
    build_schema_registry,
    raw_asset_sha256,
    record_content_hash,
    validate_typed_terminal_result_intrinsic,
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


def _serialized(result: tuple[Diagnostic, ...]) -> bytes:
    return json.dumps(
        [item.to_dict() for item in result],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _codes(result: tuple[Diagnostic, ...]) -> tuple[DiagnosticCode, ...]:
    assert type(result) is tuple
    assert all(type(item) is Diagnostic for item in result)
    return tuple(item.code for item in result)


def _asset_ref(
    asset_id: str,
    marker: str,
    *,
    path_hint: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "asset_id": asset_id,
        "media_type": "application/json",
        "byte_size": 1,
        "sha256": "sha256:" + (marker * 64),
    }
    if path_hint is not None:
        result["path_hint"] = path_hint
    return result


def _schema_ref(
    asset_id: str,
    marker: str,
    *,
    path_hint: str | None = None,
) -> dict[str, object]:
    result = _asset_ref(asset_id, marker, path_hint=path_hint)
    result["media_type"] = "application/schema+json"
    result["schema_uri"] = (
        "https://agtxiv.org/schema/v2/contract-kernel/example/"
        "placeholder/1.0.0"
    )
    return result


def _record_ref(
    record_type: str,
    record_id: str,
    marker: str,
    *,
    path_hint: str | None = None,
) -> dict[str, object]:
    return {
        "record_type": record_type,
        "record_id": record_id,
        "record_revision": 1,
        "schema_ref": _schema_ref(
            f"schema:{record_id}", marker, path_hint=path_hint
        ),
        "content_hash": "sha256:" + (marker * 64),
    }


def _component_ref(
    record_type: str,
    record_id: str,
    marker: str,
    *,
    path_hint: str | None = None,
) -> dict[str, object]:
    return {
        **_record_ref(record_type, record_id, marker, path_hint=path_hint),
        "component_id": f"component:{record_id}",
        "json_pointer": "/payload/obligations/0",
    }


def _binding_for_path(path: Path, asset_id: str) -> SchemaAssetBinding:
    raw = path.read_bytes()
    document = json.loads(raw)
    schema_id = document["$id"]
    exact_ref = {
        "asset_id": asset_id,
        "media_type": "application/schema+json",
        "byte_size": len(raw),
        "sha256": raw_asset_sha256(raw),
        "schema_uri": schema_id,
    }
    return SchemaAssetBinding(
        _parsed(exact_ref),
        SuppliedAsset(asset_id, "application/schema+json", raw, schema_id),
    )


def _registry(
    *,
    terminal_binding: SchemaAssetBinding | None = None,
) -> tuple[ContractSchemaRegistry, SchemaAssetBinding]:
    bindings: list[SchemaAssetBinding] = []
    common_paths = sorted(
        (ROOT / "schemas" / "v2" / "contract-kernel" / "common").glob(
            "*/1.0.0.schema.json"
        )
    )
    assert len(common_paths) == 8
    for path in common_paths:
        bindings.append(
            _binding_for_path(
                path,
                f"schema:common:{path.parent.name}:1.0.0",
            )
        )
    binding = terminal_binding or _binding_for_path(
        TERMINAL_SCHEMA_PATH,
        "schema:typed-terminal-result:1.0.0",
    )
    bindings.append(binding)
    result = build_schema_registry(tuple(reversed(bindings)))
    assert type(result) is ContractSchemaRegistry, result
    return result, binding


def _base_context(mode: str) -> dict[str, object]:
    context: dict[str, object] = {
        "context_mode": mode,
        "profile_ref": _asset_ref("profile:test-1", "1"),
        "catalog_ref": _asset_ref("catalog:test-1", "2"),
    }
    if mode in {"PLAN_BOUND", "FROZEN_SCOPE_BOUND"}:
        context["plan_ref"] = _record_ref(
            "agtxiv.agentization-plan/1.0.0",
            "agentization-plan:test-1",
            "3",
            path_hint="plan-display-a.json",
        )
    if mode == "FROZEN_SCOPE_BOUND":
        context["scope_ref"] = _record_ref(
            "agtxiv.frozen-inventory-scope/1.0.0",
            "frozen-inventory-scope:test-1",
            "4",
            path_hint="scope-display-a.json",
        )
    return context


def _basis_for_context(context: dict[str, object]) -> dict[str, object]:
    mode = context["context_mode"]
    if mode == "PLAN_BOUND":
        base = deepcopy(context["plan_ref"])
        base["schema_ref"]["path_hint"] = "plan-display-b.json"
        return {
            "basis_kind": "COMPONENT",
            "component_ref": {
                **base,
                "component_id": "component:plan-obligation-1",
                "json_pointer": "/payload/obligations/0",
            },
        }
    if mode == "FROZEN_SCOPE_BOUND":
        base = deepcopy(context["scope_ref"])
        base["schema_ref"]["path_hint"] = "scope-display-b.json"
        return {
            "basis_kind": "COMPONENT",
            "component_ref": {
                **base,
                "component_id": "component:scope-obligation-1",
                "json_pointer": "/payload/obligations/0",
            },
        }
    return {
        "basis_kind": "ASSET",
        "asset_ref": _asset_ref("source:test-1", "5"),
    }


def _outcome_fields(outcome: str) -> tuple[dict[str, object], str]:
    if outcome == "UNAVAILABLE":
        return (
            {
                "retry_disposition": "NO_RETRY_IN_CURRENT_CONTEXT",
                "context_change_required": "The missing input must be supplied.",
            },
            "PROVIDE_INPUT",
        )
    if outcome == "RETRY_REQUIRED":
        return (
            {
                "retry_disposition": "RETRY_AFTER_CONDITION",
                "retry_condition": "The transient dependency becomes ready.",
            },
            "RETRY",
        )
    if outcome == "REVIEW_REQUIRED":
        return (
            {
                "retry_disposition": "REVIEW_DECIDES",
                "review_condition": "A reviewer decides how to proceed.",
            },
            "MANUAL_REVIEW",
        )
    if outcome == "BLOCKED":
        return (
            {
                "retry_disposition": "NO_RETRY_IN_CURRENT_CONTEXT",
                "context_change_required": "The dependency must be resolved.",
            },
            "RESOLVE_DEPENDENCY",
        )
    assert outcome == "FAILED"
    return (
        {
            "retry_disposition": "RETRY_AFTER_CONDITION",
            "retry_condition": "The implementation defect is fixed.",
        },
        "FIX_IMPLEMENTATION",
    )


def _payload(
    *,
    mode: str = "PROFILE_BOUND",
    outcome: str = "RETRY_REQUIRED",
    resource_case: str = "within",
) -> dict[str, object]:
    context = _base_context(mode)
    retry, action_code = _outcome_fields(outcome)
    if resource_case == "within":
        resources = {
            "limit": {"max_wall_time_ms": 100},
            "observed": {"wall_time_ms": 100},
            "unobserved_metrics": [],
            "relation": "WITHIN_OBSERVED_LIMITS",
        }
    elif resource_case == "unobserved":
        resources = {
            "limit": {"max_wall_time_ms": 100, "max_cpu_time_ms": 100},
            "observed": {"wall_time_ms": 80},
            "unobserved_metrics": ["cpu_time_ms"],
            "relation": "INDETERMINATE",
        }
    else:
        assert resource_case == "exceeded"
        resources = {
            "limit": {"max_wall_time_ms": 100},
            "observed": {"wall_time_ms": 101},
            "unobserved_metrics": [],
            "relation": "EXCEEDED_OBSERVED_LIMIT",
        }
    return {
        "terminal_for_attempt": True,
        "terminal_scope": "ATTEMPT_ONLY",
        "successful_artifact_produced": False,
        "satisfaction_claim": "NONE",
        "attempt_id": "attempt:test-1",
        "binding_context": context,
        "target_obligation": {
            "obligation_key": "obligation:test-1",
            "stage_id": "EXAMPLE_STAGE",
            "family_id": "EXAMPLE_FAMILY",
            "basis": _basis_for_context(context),
        },
        "outcome": outcome,
        "declared_reason": {
            "declared_reason_code": "AGTXIV.TERMINAL.EXAMPLE",
            "summary": "One operational attempt stopped.",
        },
        "evidence": [
            {
                "evidence_id": "evidence:test-1",
                "evidence_role": "TOOL_DIAGNOSTIC",
                "evidence_kind": "ASSET",
                "asset_ref": _asset_ref("diagnostic:test-1", "6"),
            }
        ],
        "retry": retry,
        "next_action": {
            "action_code": action_code,
            "description": "Perform the declared next action.",
            "responsible_actor": {
                "actor_kind": "AGENT",
                "actor_id": "agent:action-owner-1",
            },
            "responsible_role": "TERMINAL_ACTION_OWNER",
            "deadline": {
                "deadline_kind": "NO_DEADLINE",
                "no_deadline_reason": "The required state change controls timing.",
            },
        },
        "resources": resources,
    }


def _record(
    binding: SchemaAssetBinding,
    *,
    payload: dict[str, object] | None = None,
    envelope_changes: dict[str, object] | None = None,
    schema_path_hint: str | None = None,
) -> ParsedCanonicalValue:
    schema_ref = binding.exact_ref.to_python()
    if schema_path_hint is not None:
        schema_ref["path_hint"] = schema_path_hint
    envelope: dict[str, object] = {
        "record_type": TERMINAL_RECORD_TYPE,
        "schema_ref": schema_ref,
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
    envelope.update(envelope_changes or {})
    document: dict[str, object] = {
        "envelope": envelope,
        "payload": _payload() if payload is None else payload,
    }
    computed = record_content_hash(_parsed(document))
    assert isinstance(computed, str)
    document["content_hash"] = computed
    return _parsed(document)


def _rehashed_record(document: dict[str, object]) -> ParsedCanonicalValue:
    detached = deepcopy(document)
    detached.pop("content_hash", None)
    computed = record_content_hash(_parsed(detached))
    assert isinstance(computed, str)
    detached["content_hash"] = computed
    return _parsed(detached)


def _retry_for(disposition: str) -> dict[str, object]:
    if disposition == "RETRY_AFTER_CONDITION":
        return {
            "retry_disposition": disposition,
            "retry_condition": "The declared retry condition becomes true.",
        }
    if disposition == "NO_RETRY_IN_CURRENT_CONTEXT":
        return {
            "retry_disposition": disposition,
            "context_change_required": "The declared execution context changes.",
        }
    assert disposition == "REVIEW_DECIDES"
    return {
        "retry_disposition": disposition,
        "review_condition": "The requested review reaches a decision.",
    }


ALLOWED_OUTCOME_RETRY_ACTION = [
    *(
        ("UNAVAILABLE", disposition, action)
        for disposition in (
            "RETRY_AFTER_CONDITION",
            "NO_RETRY_IN_CURRENT_CONTEXT",
        )
        for action in ("PROVIDE_INPUT", "RESOLVE_DEPENDENCY")
    ),
    ("RETRY_REQUIRED", "RETRY_AFTER_CONDITION", "RETRY"),
    ("REVIEW_REQUIRED", "REVIEW_DECIDES", "MANUAL_REVIEW"),
    *(
        ("BLOCKED", disposition, action)
        for disposition in (
            "RETRY_AFTER_CONDITION",
            "NO_RETRY_IN_CURRENT_CONTEXT",
        )
        for action in ("RESOLVE_DEPENDENCY", "RESOLVE_POLICY", "ESCALATE")
    ),
    *(
        ("FAILED", disposition, action)
        for disposition in (
            "RETRY_AFTER_CONDITION",
            "NO_RETRY_IN_CURRENT_CONTEXT",
            "REVIEW_DECIDES",
        )
        for action in ("FIX_IMPLEMENTATION", "MANUAL_REVIEW", "ESCALATE")
    ),
]


def test_terminal_diagnostic_codes_are_locked() -> None:
    expected = {
        DiagnosticCode.TERMINAL_SCHEMA_MISMATCH: "AGTXIV.TERMINAL.SCHEMA_MISMATCH",
        DiagnosticCode.TERMINAL_ATTEMPT_MISMATCH: "AGTXIV.TERMINAL.ATTEMPT_MISMATCH",
        DiagnosticCode.TERMINAL_CONTEXT_INVALID: "AGTXIV.TERMINAL.CONTEXT_INVALID",
        DiagnosticCode.TERMINAL_TARGET_INVALID: "AGTXIV.TERMINAL.TARGET_INVALID",
        DiagnosticCode.TERMINAL_EVIDENCE_INVALID: "AGTXIV.TERMINAL.EVIDENCE_INVALID",
        DiagnosticCode.TERMINAL_DISPOSITION_INVALID: "AGTXIV.TERMINAL.DISPOSITION_INVALID",
        DiagnosticCode.TERMINAL_RESOURCE_INVALID: "AGTXIV.TERMINAL.RESOURCE_INVALID",
    }
    assert {code: str(code) for code in expected} == expected


@pytest.mark.parametrize("mode", ["PROFILE_BOUND", "PLAN_BOUND", "FROZEN_SCOPE_BOUND"])
@pytest.mark.parametrize(
    "outcome",
    ["UNAVAILABLE", "RETRY_REQUIRED", "REVIEW_REQUIRED", "BLOCKED", "FAILED"],
)
def test_valid_context_modes_and_operational_outcomes(mode: str, outcome: str) -> None:
    registry, binding = _registry()
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=_payload(mode=mode, outcome=outcome)),
        registry,
    ) == ()


@pytest.mark.parametrize(
    ("outcome", "disposition", "action"),
    ALLOWED_OUTCOME_RETRY_ACTION,
)
def test_every_allowed_outcome_retry_action_combination(
    outcome: str,
    disposition: str,
    action: str,
) -> None:
    registry, binding = _registry()
    payload = _payload(outcome=outcome)
    payload["retry"] = _retry_for(disposition)
    payload["next_action"]["action_code"] = action
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=payload),
        registry,
    ) == ()


@pytest.mark.parametrize("resource_case", ["within", "unobserved", "exceeded"])
def test_valid_resource_relations_include_equal_limit_and_exceeded_observation(
    resource_case: str,
) -> None:
    registry, binding = _registry()
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=_payload(resource_case=resource_case)),
        registry,
    ) == ()


def test_fixed_deadline_is_valid_without_reading_the_wall_clock() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["next_action"]["deadline"] = {
        "deadline_kind": "FIXED_DEADLINE",
        "deadline_at": "2027-01-01T00:00:00Z",
    }
    assert validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry) == ()


def test_context_and_basis_asset_path_hints_are_non_authoritative() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["binding_context"]["profile_ref"]["path_hint"] = "profiles/display.json"
    payload["binding_context"]["catalog_ref"]["path_hint"] = "catalogs/display.json"
    payload["target_obligation"]["basis"]["asset_ref"]["path_hint"] = "source/display.tex"
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=payload),
        registry,
    ) == ()


@pytest.mark.parametrize("basis_kind", ["RECORD", "COMPONENT"])
def test_profile_bound_context_accepts_nonterminal_record_or_component_basis(
    basis_kind: str,
) -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["target_obligation"]["basis"] = (
        {
            "basis_kind": "RECORD",
            "record_ref": _record_ref(
                "agtxiv.example-basis/1.0.0",
                "basis:record-1",
                "a",
            ),
        }
        if basis_kind == "RECORD"
        else {
            "basis_kind": "COMPONENT",
            "component_ref": _component_ref(
                "agtxiv.example-basis/1.0.0",
                "basis:component-1",
                "b",
            ),
        }
    )
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=payload),
        registry,
    ) == ()


def test_official_schema_ref_allows_only_path_hint_to_differ() -> None:
    registry, binding = _registry()
    without_hint = _record(binding)
    with_hint = _record(binding, schema_path_hint="display/terminal.schema.json")
    assert without_hint.to_python()["content_hash"] != with_hint.to_python()["content_hash"]
    assert validate_typed_terminal_result_intrinsic(without_hint, registry) == ()
    assert validate_typed_terminal_result_intrinsic(with_hint, registry) == ()
    record = _record(binding).to_python()
    record["envelope"]["schema_ref"]["byte_size"] += 1
    forged = _parsed(record)
    result = validate_typed_terminal_result_intrinsic(forged, registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_SCHEMA_MISMATCH,)


def test_gate_two_diagnostic_never_echoes_untrusted_path_hint() -> None:
    registry, binding = _registry()
    secret = "PRIVATE_HINT_" + ("界" * 1000)
    document = _record(binding, schema_path_hint=secret).to_python()
    document["envelope"]["schema_ref"]["sha256"] = "sha256:" + ("0" * 64)
    result = validate_typed_terminal_result_intrinsic(_parsed(document), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_SCHEMA_MISMATCH,)
    assert secret.encode("utf-8") not in _serialized(result)


def test_same_id_substituted_schema_hard_stops_before_payload_interpretation() -> None:
    document = json.loads(TERMINAL_SCHEMA_PATH.read_bytes())
    document["$defs"]["payload"] = True
    raw = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ref = {
        "asset_id": "schema:typed-terminal-result:1.0.0",
        "media_type": "application/schema+json",
        "byte_size": len(raw),
        "sha256": raw_asset_sha256(raw),
        "schema_uri": TERMINAL_SCHEMA_ID,
    }
    substituted = SchemaAssetBinding(
        _parsed(ref),
        SuppliedAsset(
            ref["asset_id"],
            ref["media_type"],
            raw,
            TERMINAL_SCHEMA_ID,
        ),
    )
    registry, _ = _registry(terminal_binding=substituted)
    malformed = _record(substituted, payload={})
    result = validate_typed_terminal_result_intrinsic(malformed, registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_SCHEMA_MISMATCH,)
    assert all(not item.json_pointer.startswith("/payload") for item in result)


def test_missing_producer_and_schema_mismatch_are_gate_two_only() -> None:
    registry, binding = _registry()
    record = _record(binding).to_python()
    del record["envelope"]["producer_context"]
    record["envelope"]["schema_ref"]["sha256"] = "sha256:" + ("0" * 64)
    record["payload"] = {}
    result = validate_typed_terminal_result_intrinsic(_parsed(record), registry)
    assert set(_codes(result)) == {
        DiagnosticCode.TERMINAL_SCHEMA_MISMATCH,
        DiagnosticCode.TERMINAL_ATTEMPT_MISMATCH,
    }
    assert all(not item.json_pointer.startswith("/payload") for item in result)


def test_wrong_record_type_and_other_schema_reuse_fail_before_intrinsic_meaning() -> None:
    registry, binding = _registry()
    wrong_type = _record(binding).to_python()
    wrong_type["envelope"]["record_type"] = "agtxiv.example-other/1.0.0"
    result = validate_typed_terminal_result_intrinsic(
        _rehashed_record(wrong_type),
        registry,
    )
    assert _codes(result) == (DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH,)

    other_binding = _binding_for_path(
        ROOT
        / "schemas"
        / "v2"
        / "contract-kernel"
        / "common"
        / "digest"
        / "1.0.0.schema.json",
        "schema:common:digest:1.0.0",
    )
    reused = _record(binding).to_python()
    reused["envelope"]["schema_ref"] = other_binding.exact_ref.to_python()
    result = validate_typed_terminal_result_intrinsic(_rehashed_record(reused), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_SCHEMA_MISMATCH,)


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_context_branches_cannot_launder_optional_refs(mutation: str) -> None:
    registry, binding = _registry()
    payload = _payload()
    if mutation == "missing":
        del payload["binding_context"]["catalog_ref"]
    else:
        payload["binding_context"]["plan_ref"] = _record_ref(
            "agtxiv.agentization-plan/1.0.0",
            "agentization-plan:test-extra",
            "e",
        )
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


def test_target_artifact_ref_is_not_a_target_obligation_field() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["target_obligation"]["target_artifact_ref"] = _asset_ref(
        "artifact:invented", "f"
    )
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


def test_attempt_context_mismatch_is_intrinsic() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["attempt_id"] = "attempt:other-1"
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_ATTEMPT_MISMATCH,)
    assert result[0].json_pointer == "/payload/attempt_id"


@pytest.mark.parametrize("mode", ["PLAN_BOUND", "FROZEN_SCOPE_BOUND"])
def test_basis_must_match_the_bound_plan_or_scope(mode: str) -> None:
    registry, binding = _registry()
    payload = _payload(mode=mode)
    payload["target_obligation"]["basis"]["component_ref"]["record_id"] = "wrong:test-1"
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_CONTEXT_INVALID,)


@pytest.mark.parametrize("mode", ["PLAN_BOUND", "FROZEN_SCOPE_BOUND"])
@pytest.mark.parametrize("basis_kind", ["ASSET", "RECORD"])
def test_plan_and_scope_modes_require_component_basis(
    mode: str,
    basis_kind: str,
) -> None:
    registry, binding = _registry()
    payload = _payload(mode=mode)
    payload["target_obligation"]["basis"] = (
        {
            "basis_kind": "ASSET",
            "asset_ref": _asset_ref("basis:test-asset", "a"),
        }
        if basis_kind == "ASSET"
        else {
            "basis_kind": "RECORD",
            "record_ref": _record_ref(
                "agtxiv.example-basis/1.0.0",
                "basis:test-record",
                "b",
            ),
        }
    )
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_CONTEXT_INVALID,)
    assert result[0].to_dict()["details"]["reason"] == "COMPONENT_BASIS_REQUIRED"


@pytest.mark.parametrize(
    "family_id",
    ["TYPED_STAGE_FAMILY_TERMINAL_RESULT", "TYPED_TERMINAL_RESULT"],
)
def test_terminal_target_families_are_forbidden(family_id: str) -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["target_obligation"]["family_id"] = family_id
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_TARGET_INVALID,)


def test_terminal_record_basis_is_forbidden() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["target_obligation"]["basis"] = {
        "basis_kind": "RECORD",
        "record_ref": _record_ref(
            TERMINAL_RECORD_TYPE,
            "typed-terminal-result:other-1",
            "a",
        ),
    }
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_TARGET_INVALID,)


def test_terminal_component_basis_is_forbidden() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["target_obligation"]["basis"] = {
        "basis_kind": "COMPONENT",
        "component_ref": _component_ref(
            TERMINAL_RECORD_TYPE,
            "typed-terminal-result:other-1",
            "a",
        ),
    }
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_TARGET_INVALID,)


def test_empty_evidence_is_a_generic_payload_failure() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["evidence"] = []
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


def test_duplicate_evidence_id_is_intrinsically_rejected() -> None:
    registry, binding = _registry()
    payload = _payload()
    second = deepcopy(payload["evidence"][0])
    second["asset_ref"] = _asset_ref("diagnostic:test-2", "b")
    payload["evidence"].append(second)
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_EVIDENCE_INVALID,)
    assert result[0].to_dict()["details"]["reason"] == "DUPLICATE_EVIDENCE_ID"


def test_evidence_order_id_and_authoritative_ref_uniqueness() -> None:
    registry, binding = _registry()
    payload = _payload()
    first = payload["evidence"][0]
    second = deepcopy(first)
    first["evidence_id"] = "evidence:z"
    first["asset_ref"]["path_hint"] = "first"
    second["evidence_id"] = "evidence:a"
    second["asset_ref"]["path_hint"] = "second"
    payload["evidence"] = [first, second]
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (
        DiagnosticCode.TERMINAL_EVIDENCE_INVALID,
        DiagnosticCode.TERMINAL_EVIDENCE_INVALID,
    )
    assert {item.to_dict()["details"]["reason"] for item in result} == {
        "DUPLICATE_REFERENCE",
        "EVIDENCE_ORDER",
    }


def test_nested_schema_path_hint_cannot_disguise_duplicate_record_evidence() -> None:
    registry, binding = _registry()
    payload = _payload()
    first_ref = _record_ref("agtxiv.example-evidence/1.0.0", "evidence-record:test-1", "b", path_hint="a")
    second_ref = deepcopy(first_ref)
    second_ref["schema_ref"]["path_hint"] = "b"
    payload["evidence"] = [
        {
            "evidence_id": "evidence:a",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "RECORD",
            "record_ref": first_ref,
        },
        {
            "evidence_id": "evidence:b",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "RECORD",
            "record_ref": second_ref,
        },
    ]
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_EVIDENCE_INVALID,)
    assert result[0].to_dict()["details"]["reason"] == "DUPLICATE_REFERENCE"


@pytest.mark.parametrize("evidence_kind", ["RECORD", "COMPONENT"])
def test_nonterminal_record_and_component_evidence_are_intrinsically_valid(
    evidence_kind: str,
) -> None:
    registry, binding = _registry()
    payload = _payload()
    ref = (
        _record_ref(
            "agtxiv.example-evidence/1.0.0",
            "evidence-record:test-valid",
            "b",
        )
        if evidence_kind == "RECORD"
        else _component_ref(
            "agtxiv.example-evidence/1.0.0",
            "evidence-component:test-valid",
            "c",
        )
    )
    payload["evidence"] = [
        {
            "evidence_id": "evidence:valid",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": evidence_kind,
            f"{evidence_kind.lower()}_ref": ref,
        }
    ]
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=payload),
        registry,
    ) == ()


def test_terminal_and_direct_self_evidence_are_forbidden() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["evidence"] = [
        {
            "evidence_id": "evidence:self",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "RECORD",
            "record_ref": _record_ref(
                TERMINAL_RECORD_TYPE,
                "typed-terminal-result:test-1",
                "c",
            ),
        }
    ]
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_EVIDENCE_INVALID,)
    assert result[0].to_dict()["details"]["reason"] == "SELF_REFERENCE"


def test_other_terminal_record_evidence_is_not_misreported_as_self() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["evidence"] = [
        {
            "evidence_id": "evidence:other-terminal",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "RECORD",
            "record_ref": _record_ref(
                TERMINAL_RECORD_TYPE,
                "typed-terminal-result:other-1",
                "c",
            ),
        }
    ]
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_EVIDENCE_INVALID,)
    assert result[0].to_dict()["details"]["reason"] == "TERMINAL_REFERENCE"


def test_terminal_component_evidence_is_forbidden() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["evidence"] = [
        {
            "evidence_id": "evidence:terminal-component",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "COMPONENT",
            "component_ref": _component_ref(
                TERMINAL_RECORD_TYPE,
                "typed-terminal-result:other-1",
                "c",
            ),
        }
    ]
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_EVIDENCE_INVALID,)
    assert result[0].to_dict()["details"]["reason"] == "TERMINAL_REFERENCE"


@pytest.mark.parametrize("outcome", ["NOT_APPLICABLE", "UNSUPPORTED", "REFUTED"])
def test_catalog_or_scientific_outcomes_are_excluded(outcome: str) -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["outcome"] = outcome
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize("mutation", ["satisfaction", "permanent"])
def test_satisfaction_and_permanent_claims_are_forbidden(mutation: str) -> None:
    registry, binding = _registry()
    payload = _payload()
    if mutation == "satisfaction":
        payload["satisfaction_claim"] = "SATISFIED"
    else:
        payload["permanent"] = True
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("terminal_for_attempt", False),
        ("terminal_scope", "PERMANENT"),
        ("successful_artifact_produced", True),
        ("satisfaction_claim", "SATISFIED"),
    ],
)
@pytest.mark.parametrize("missing", [False, True])
def test_all_four_non_authority_constants_are_fixed_and_required(
    field: str,
    value: object,
    missing: bool,
) -> None:
    registry, binding = _registry()
    payload = _payload()
    if missing:
        del payload[field]
    else:
        payload[field] = value
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize("mutation", ["reason", "retry", "deadline"])
def test_malformed_reason_retry_and_deadline_unions_are_schema_failures(
    mutation: str,
) -> None:
    registry, binding = _registry()
    payload = _payload()
    if mutation == "reason":
        payload["declared_reason"]["declared_reason_code"] = "agtxiv.bad"
    elif mutation == "retry":
        payload["retry"] = {"retry_disposition": "RETRY_AFTER_CONDITION"}
    else:
        payload["next_action"]["deadline"] = {
            "deadline_kind": "NO_DEADLINE",
            "no_deadline_reason": "No policy deadline.",
            "deadline_at": "2027-01-01T00:00:00Z",
        }
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize(
    "retry",
    [
        {"retry_disposition": "RETRY_AFTER_CONDITION"},
        {"retry_disposition": "NO_RETRY_IN_CURRENT_CONTEXT"},
        {"retry_disposition": "REVIEW_DECIDES"},
    ],
)
def test_each_retry_branch_requires_its_own_explanation(
    retry: dict[str, object],
) -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["retry"] = retry
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize(
    "deadline",
    [
        {"deadline_kind": "NO_DEADLINE"},
        {
            "deadline_kind": "NO_DEADLINE",
            "no_deadline_reason": "There is no policy deadline.",
            "deadline_at": "2027-01-01T00:00:00Z",
        },
        {"deadline_kind": "FIXED_DEADLINE"},
        {
            "deadline_kind": "FIXED_DEADLINE",
            "deadline_at": "2027-01-01T00:00:00Z",
            "no_deadline_reason": "Contradictory extra field.",
        },
    ],
)
def test_each_deadline_branch_requires_and_forbids_its_exact_fields(
    deadline: dict[str, object],
) -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["next_action"]["deadline"] = deadline
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize(
    ("case", "value", "valid"),
    [
        ("namespaced", "a:", False),
        ("namespaced", "a:b", True),
        ("namespaced", "a:" + ("b" * 510), True),
        ("namespaced", "a:" + ("b" * 511), False),
        ("upper", "", False),
        ("upper", "A", True),
        ("upper", "A" * 128, True),
        ("upper", "A" * 129, False),
        ("reason", "AGTXIV.A", False),
        ("reason", "AGTXIV.A.B", True),
        ("reason", "AGTXIV.A." + ("B" * 247), True),
        ("reason", "AGTXIV.A." + ("B" * 248), False),
        ("text", " ", False),
        ("text", "界", True),
        ("text", "界" * 2048, True),
        ("text", "界" * 2049, False),
    ],
)
def test_locked_lexical_boundaries_count_unicode_code_points(
    case: str,
    value: str,
    valid: bool,
) -> None:
    registry, binding = _registry()
    document = _record(binding).to_python()
    if case == "namespaced":
        document["payload"]["attempt_id"] = value
        document["envelope"]["producer_context"]["attempt_id"] = value
    elif case == "upper":
        document["payload"]["target_obligation"]["stage_id"] = value
    elif case == "reason":
        document["payload"]["declared_reason"]["declared_reason_code"] = value
    else:
        document["payload"]["declared_reason"]["summary"] = value
    result = validate_typed_terminal_result_intrinsic(_rehashed_record(document), registry)
    assert (result == ()) is valid


@pytest.mark.parametrize(
    ("timestamp", "valid"),
    [
        ("2027-01-01T00:00:00Z", True),
        ("2027-01-01T00:00:00.123456789Z", True),
        ("2027-01-01T00:00:00.1234567890Z", False),
        ("2027-02-30T00:00:00Z", False),
        ("2027-01-01t00:00:00z", False),
    ],
)
def test_fixed_deadline_lexical_and_calendar_boundaries(
    timestamp: str,
    valid: bool,
) -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["next_action"]["deadline"] = {
        "deadline_kind": "FIXED_DEADLINE",
        "deadline_at": timestamp,
    }
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert (result == ()) is valid


@pytest.mark.parametrize(
    ("case", "value"),
    [
        ("context", "UNKNOWN"),
        ("basis", "UNKNOWN"),
        ("evidence_kind", "UNKNOWN"),
        ("family", "lowercase"),
        ("evidence_role", "UNKNOWN_ROLE"),
        ("outcome", "UNKNOWN"),
        ("retry", "UNKNOWN"),
        ("action", "UNKNOWN"),
        ("deadline", "UNKNOWN"),
        ("relation", "UNKNOWN"),
    ],
)
def test_every_closed_literal_vocabulary_rejects_unknown_values(
    case: str,
    value: str,
) -> None:
    registry, binding = _registry()
    payload = _payload()
    if case == "context":
        payload["binding_context"]["context_mode"] = value
    elif case == "basis":
        payload["target_obligation"]["basis"]["basis_kind"] = value
    elif case == "evidence_kind":
        payload["evidence"][0]["evidence_kind"] = value
    elif case == "family":
        payload["target_obligation"]["family_id"] = value
    elif case == "evidence_role":
        payload["evidence"][0]["evidence_role"] = value
    elif case == "outcome":
        payload["outcome"] = value
    elif case == "retry":
        payload["retry"]["retry_disposition"] = value
    elif case == "action":
        payload["next_action"]["action_code"] = value
    elif case == "deadline":
        payload["next_action"]["deadline"]["deadline_kind"] = value
    else:
        payload["resources"]["relation"] = value
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


@pytest.mark.parametrize(
    ("outcome", "retry", "action"),
    [
        (
            "RETRY_REQUIRED",
            {"retry_disposition": "REVIEW_DECIDES", "review_condition": "Review."},
            "RETRY",
        ),
        (
            "BLOCKED",
            {
                "retry_disposition": "NO_RETRY_IN_CURRENT_CONTEXT",
                "context_change_required": "Resolve it.",
            },
            "FIX_IMPLEMENTATION",
        ),
        (
            "FAILED",
            {"retry_disposition": "REVIEW_DECIDES", "review_condition": "Review."},
            "RETRY",
        ),
    ],
)
def test_outcome_retry_action_matrix_is_closed(
    outcome: str,
    retry: dict[str, object],
    action: str,
) -> None:
    registry, binding = _registry()
    payload = _payload(outcome=outcome)
    payload["retry"] = retry
    payload["next_action"]["action_code"] = action
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert DiagnosticCode.TERMINAL_DISPOSITION_INVALID in _codes(result)


@pytest.mark.parametrize(
    ("outcome", "invalid_disposition"),
    [
        ("UNAVAILABLE", "REVIEW_DECIDES"),
        ("RETRY_REQUIRED", "REVIEW_DECIDES"),
        ("REVIEW_REQUIRED", "RETRY_AFTER_CONDITION"),
        ("BLOCKED", "REVIEW_DECIDES"),
    ],
)
def test_each_outcome_with_a_forbidden_retry_edge_is_rejected(
    outcome: str,
    invalid_disposition: str,
) -> None:
    registry, binding = _registry()
    payload = _payload(outcome=outcome)
    payload["retry"] = _retry_for(invalid_disposition)
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_DISPOSITION_INVALID,)
    assert result[0].json_pointer == "/payload/retry/retry_disposition"


@pytest.mark.parametrize(
    ("outcome", "invalid_action"),
    [
        ("UNAVAILABLE", "FIX_IMPLEMENTATION"),
        ("RETRY_REQUIRED", "PROVIDE_INPUT"),
        ("REVIEW_REQUIRED", "RETRY"),
        ("BLOCKED", "RETRY"),
        ("FAILED", "PROVIDE_INPUT"),
    ],
)
def test_each_outcome_rejects_an_action_outside_its_row(
    outcome: str,
    invalid_action: str,
) -> None:
    registry, binding = _registry()
    payload = _payload(outcome=outcome)
    payload["next_action"]["action_code"] = invalid_action
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_DISPOSITION_INVALID,)
    assert result[0].json_pointer == "/payload/next_action/action_code"


@pytest.mark.parametrize(
    "mutation",
    ["missing", "overlap", "extra", "order", "relation"],
)
def test_resource_partition_order_and_relation_are_mechanical(mutation: str) -> None:
    registry, binding = _registry()
    payload = _payload(resource_case="unobserved")
    resources = payload["resources"]
    if mutation == "missing":
        resources["unobserved_metrics"] = []
    elif mutation == "overlap":
        resources["observed"]["cpu_time_ms"] = 1
    elif mutation == "extra":
        resources["observed"]["input_bytes"] = 1
    elif mutation == "order":
        resources["limit"] = {
            "max_wall_time_ms": 100,
            "max_cpu_time_ms": 100,
            "max_input_bytes": 100,
        }
        resources["observed"] = {}
        resources["unobserved_metrics"] = [
            "input_bytes",
            "wall_time_ms",
            "cpu_time_ms",
        ]
    else:
        resources["relation"] = "WITHIN_OBSERVED_LIMITS"
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert DiagnosticCode.TERMINAL_RESOURCE_INVALID in _codes(result)


@pytest.mark.parametrize(
    ("resource_case", "wrong_relation"),
    [
        ("within", "EXCEEDED_OBSERVED_LIMIT"),
        ("within", "INDETERMINATE"),
        ("unobserved", "WITHIN_OBSERVED_LIMITS"),
        ("unobserved", "EXCEEDED_OBSERVED_LIMIT"),
        ("exceeded", "WITHIN_OBSERVED_LIMITS"),
        ("exceeded", "INDETERMINATE"),
    ],
)
def test_every_resource_truth_state_rejects_both_wrong_relations(
    resource_case: str,
    wrong_relation: str,
) -> None:
    registry, binding = _registry()
    payload = _payload(resource_case=resource_case)
    payload["resources"]["relation"] = wrong_relation
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.TERMINAL_RESOURCE_INVALID,)


def test_resource_order_and_relation_failures_are_both_reported() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["resources"] = {
        "limit": {
            "max_wall_time_ms": 100,
            "max_cpu_time_ms": 100,
        },
        "observed": {},
        "unobserved_metrics": ["cpu_time_ms", "wall_time_ms"],
        "relation": "WITHIN_OBSERVED_LIMITS",
    }
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (
        DiagnosticCode.TERMINAL_RESOURCE_INVALID,
        DiagnosticCode.TERMINAL_RESOURCE_INVALID,
    )
    assert [item.to_dict()["details"]["reason"] for item in result] == [
        "RELATION_MISMATCH",
        "DIMENSION_ORDER",
    ]


def test_bool_resource_value_is_schema_invalid_not_an_integer() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["resources"]["observed"]["wall_time_ms"] = True
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)


def test_maximum_ijson_resource_value_is_valid_and_equal_is_within() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["resources"] = {
        "limit": {"max_output_bytes": IJSON_MAX_INTEGER},
        "observed": {"output_bytes": IJSON_MAX_INTEGER},
        "unobserved_metrics": [],
        "relation": "WITHIN_OBSERVED_LIMITS",
    }
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=payload),
        registry,
    ) == ()


@pytest.mark.parametrize(
    ("limit_name", "observed_name"),
    [
        ("max_wall_time_ms", "wall_time_ms"),
        ("max_cpu_time_ms", "cpu_time_ms"),
        ("max_peak_memory_bytes", "peak_memory_bytes"),
        ("max_input_bytes", "input_bytes"),
        ("max_output_bytes", "output_bytes"),
        ("max_network_requests", "network_requests"),
    ],
)
def test_all_six_limit_to_observation_mappings_are_exact(
    limit_name: str,
    observed_name: str,
) -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["resources"] = {
        "limit": {limit_name: 10},
        "observed": {observed_name: 10},
        "unobserved_metrics": [],
        "relation": "WITHIN_OBSERVED_LIMITS",
    }
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=payload),
        registry,
    ) == ()


def test_known_exceedance_takes_precedence_over_an_unobserved_dimension() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["resources"] = {
        "limit": {"max_wall_time_ms": 100, "max_cpu_time_ms": 100},
        "observed": {"wall_time_ms": 101},
        "unobserved_metrics": ["cpu_time_ms"],
        "relation": "EXCEEDED_OBSERVED_LIMIT",
    }
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=payload),
        registry,
    ) == ()


def test_process_global_date_time_checker_pollution_is_irrelevant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(FormatChecker.checkers, "date-time", (lambda value: True, ()))
    registry, binding = _registry()
    invalid = _payload()
    invalid["next_action"]["deadline"] = {
        "deadline_kind": "FIXED_DEADLINE",
        "deadline_at": "2027-02-30T00:00:00Z",
    }
    assert _codes(
        validate_typed_terminal_result_intrinsic(
            _record(binding, payload=invalid),
            registry,
        )
    ) == (DiagnosticCode.RECORD_PAYLOAD_INVALID,)
    monkeypatch.setitem(FormatChecker.checkers, "date-time", (lambda value: False, ()))
    valid = _payload()
    valid["next_action"]["deadline"] = {
        "deadline_kind": "FIXED_DEADLINE",
        "deadline_at": "2027-01-01T00:00:00Z",
    }
    assert validate_typed_terminal_result_intrinsic(
        _record(binding, payload=valid),
        registry,
    ) == ()


def test_generic_payload_and_hash_failures_hard_stop_intrinsic_checks() -> None:
    registry, binding = _registry()
    document = _record(binding).to_python()
    document["payload"]["attempt_id"] = "wrong"
    document["content_hash"] = "sha256:" + ("0" * 64)
    result = validate_typed_terminal_result_intrinsic(_parsed(document), registry)
    assert set(_codes(result)) == {
        DiagnosticCode.RECORD_PAYLOAD_INVALID,
        DiagnosticCode.RECORD_HASH_MISMATCH,
    }
    assert all(not str(item.code).startswith("AGTXIV.TERMINAL") for item in result)


def test_wrong_types_and_forged_values_are_diagnostic_only() -> None:
    registry, binding = _registry()
    for bad_record in ({}, object(), None):
        result = validate_typed_terminal_result_intrinsic(bad_record, registry)  # type: ignore[arg-type]
        assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)
    record = _record(binding)
    object.__setattr__(record, "_ParsedCanonicalValue__node", {"host": "dict"})
    assert _codes(validate_typed_terminal_result_intrinsic(record, registry)) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )


def test_mutated_registry_is_diagnostic_only() -> None:
    registry, binding = _registry()
    object.__setattr__(registry, "_ContractSchemaRegistry__entries", ())
    assert _codes(validate_typed_terminal_result_intrinsic(_record(binding), registry)) == (
        DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,
    )


@pytest.mark.parametrize("corruption", ["cycle", "deep", "surrogate"])
def test_cyclic_deep_or_hostile_unicode_record_is_diagnostic_only(
    corruption: str,
) -> None:
    registry, binding = _registry()
    record = _record(binding)
    if corruption == "cycle":
        node = object.__new__(canonical_module._CanonicalObject)
        object.__setattr__(node, "pairs", (("x", node),))
    elif corruption == "deep":
        node = 0
        for _ in range(MAX_NESTING + 2):
            node = (node,)
    else:
        node = "\ud800"
    object.__setattr__(record, "_ParsedCanonicalValue__node", node)
    result = validate_typed_terminal_result_intrinsic(record, registry)
    assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


@pytest.mark.parametrize("corruption", ["cycle", "deep"])
def test_cyclic_or_deep_registry_is_diagnostic_only(corruption: str) -> None:
    registry, binding = _registry()
    entries = object.__getattribute__(registry, "_ContractSchemaRegistry__entries")
    if corruption == "cycle":
        frozen = object.__new__(registry_module._FrozenObject)
        object.__setattr__(frozen, "pairs", (("x", frozen),))
    else:
        frozen = 0
        for _ in range(MAX_NESTING + 2):
            frozen = registry_module._FrozenObject((("x", frozen),))
    corrupted_entry = dataclasses.replace(entries[0], document=frozen)
    object.__setattr__(
        registry,
        "_ContractSchemaRegistry__entries",
        (corrupted_entry, *entries[1:]),
    )
    result = validate_typed_terminal_result_intrinsic(_record(binding), registry)
    assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


def test_hostile_registry_field_is_never_called() -> None:
    registry, binding = _registry()
    entries = object.__getattribute__(registry, "_ContractSchemaRegistry__entries")

    class Hostile:
        def __str__(self) -> str:
            raise RuntimeError("str must not run")

        def __eq__(self, other: object) -> bool:
            raise RuntimeError("eq must not run")

        def encode(self, *args: object, **kwargs: object) -> bytes:
            raise RuntimeError("encode must not run")

    corrupted_entry = dataclasses.replace(entries[0], asset_id=Hostile())
    object.__setattr__(
        registry,
        "_ContractSchemaRegistry__entries",
        (corrupted_entry, *entries[1:]),
    )
    result = validate_typed_terminal_result_intrinsic(_record(binding), registry)
    assert _codes(result) == (DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,)


def test_terminal_diagnostics_are_permutation_and_repetition_stable() -> None:
    registry, binding = _registry()
    base = _payload()
    entries = [
        {
            "evidence_id": "evidence:z",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "ASSET",
            "asset_ref": _asset_ref("duplicate:test-1", "d"),
        },
        {
            "evidence_id": "evidence:a",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "ASSET",
            "asset_ref": _asset_ref("duplicate:test-1", "d"),
        },
    ]
    observations: set[bytes] = set()
    fixed_items = list(base.items())
    for prefix in itertools.permutations(fixed_items[:4]):
        payload = dict((*prefix, *fixed_items[4:]))
        payload["evidence"] = deepcopy(entries)
        for _ in range(3):
            observations.add(
                _serialized(
                    validate_typed_terminal_result_intrinsic(
                        _record(binding, payload=payload),
                        registry,
                    )
                )
            )
    assert len(observations) == 1


def test_cross_gate_intrinsic_diagnostics_have_fixed_phase_order() -> None:
    registry, binding = _registry()
    payload = _payload(mode="PLAN_BOUND", outcome="RETRY_REQUIRED")
    payload["attempt_id"] = "attempt:other-1"
    payload["target_obligation"]["family_id"] = "TYPED_TERMINAL_RESULT"
    payload["target_obligation"]["basis"]["component_ref"]["record_id"] = "wrong:test-1"
    payload["evidence"] = [
        {
            "evidence_id": "evidence:z",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "ASSET",
            "asset_ref": _asset_ref("evidence:z", "d"),
        },
        {
            "evidence_id": "evidence:a",
            "evidence_role": "INPUT_STATE",
            "evidence_kind": "ASSET",
            "asset_ref": _asset_ref("evidence:a", "e"),
        },
    ]
    payload["retry"] = _retry_for("REVIEW_DECIDES")
    payload["next_action"]["action_code"] = "MANUAL_REVIEW"
    payload["resources"]["relation"] = "INDETERMINATE"
    result = validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry)
    assert _codes(result) == (
        DiagnosticCode.TERMINAL_ATTEMPT_MISMATCH,
        DiagnosticCode.TERMINAL_CONTEXT_INVALID,
        DiagnosticCode.TERMINAL_TARGET_INVALID,
        DiagnosticCode.TERMINAL_EVIDENCE_INVALID,
        DiagnosticCode.TERMINAL_DISPOSITION_INVALID,
        DiagnosticCode.TERMINAL_DISPOSITION_INVALID,
        DiagnosticCode.TERMINAL_RESOURCE_INVALID,
    )
    assert [item.phase for item in result] == [
        "TERMINAL_ATTEMPT",
        "TERMINAL_CONTEXT",
        "TERMINAL_TARGET",
        "TERMINAL_EVIDENCE",
        "TERMINAL_DISPOSITION",
        "TERMINAL_DISPOSITION",
        "TERMINAL_RESOURCE",
    ]


def test_intrinsic_validation_never_uses_ambient_io_or_resolvers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, binding = _registry()
    record = _record(binding)

    def forbidden(*args: object, **kwargs: object) -> Any:
        raise AssertionError("intrinsic terminal validation attempted ambient access")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "getenv", forbidden)
    monkeypatch.setattr(random, "random", forbidden)
    monkeypatch.setattr(time, "time", forbidden)
    assert validate_typed_terminal_result_intrinsic(record, registry) == ()


def test_intrinsic_pass_does_not_resolve_future_context_or_grant_authority() -> None:
    registry, binding = _registry()
    payload = _payload()
    payload["binding_context"]["profile_ref"]["asset_id"] = "profile:does-not-exist"
    payload["binding_context"]["catalog_ref"]["asset_id"] = "catalog:does-not-exist"
    payload["evidence"][0]["asset_ref"]["asset_id"] = "evidence:does-not-exist"
    assert validate_typed_terminal_result_intrinsic(_record(binding, payload=payload), registry) == ()
