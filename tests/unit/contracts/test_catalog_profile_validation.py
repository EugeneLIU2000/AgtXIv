from __future__ import annotations

import importlib.util
import json
import os
import random
import socket
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path

import pytest


def _add_local_src_package() -> Path:
    root = Path(__file__).resolve().parents[3]
    source = root / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    return root


ROOT = _add_local_src_package()

from agtxiv_v2.contracts import (  # noqa: E402
    CatalogProfileConstraints,
    ContractSchemaRegistry,
    Diagnostic,
    DiagnosticCode,
    ParsedCanonicalValue,
    RawContractAssetBinding,
    SchemaAssetBinding,
    SuppliedAsset,
    build_canonical_value,
    build_catalog_profile_constraints,
    build_schema_registry,
    canonical_bytes,
    parse_canonical_json,
    raw_asset_sha256,
    validate_m1_contract_requirement_set_intrinsic,
    validate_typed_terminal_result_catalog_constraints,
)

FIXTURE = ROOT / "fixtures/v2-contract-kernel/catalog-profile/1.0.0"
REQUIREMENTS = ROOT / "contracts/v2/contract-kernel/requirements/m1-contract-requirement-set/1.0.0.json"
ROADMAP = ROOT / "docs/roadmaps/v2-end-to-end-implementation-plan.md"
CATALOG = FIXTURE / "catalog.synthetic.json"
PROFILE = FIXTURE / "profile.synthetic.json"
VECTORS = FIXTURE / "family-conformance-vectors.json"
VALIDATOR = ROOT / "src/agtxiv_v2/contracts/catalog_validation.py"
GENERIC_VALIDATOR = ROOT / "src/agtxiv_v2/contracts/schema_validation.py"


def _parsed(value: object) -> ParsedCanonicalValue:
    result = build_canonical_value(value)
    assert type(result) is ParsedCanonicalValue
    return result


def _asset(asset_id: str, media_type: str, path: Path, schema_uri: str | None = None) -> SuppliedAsset:
    return SuppliedAsset(asset_id, media_type, path.read_bytes(), schema_uri)


def _ref(asset: SuppliedAsset, *, path_hint: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "asset_id": asset.asset_id,
        "media_type": asset.media_type,
        "byte_size": len(asset.raw_bytes),
        "sha256": raw_asset_sha256(asset.raw_bytes),
    }
    if asset.schema_uri is not None:
        result["schema_uri"] = asset.schema_uri
    if path_hint is not None:
        result["path_hint"] = path_hint
    return result


def _binding(asset: SuppliedAsset, *, path_hint: str | None = None) -> RawContractAssetBinding:
    return RawContractAssetBinding(_parsed(_ref(asset, path_hint=path_hint)), asset)


def _schema_binding(path: Path, asset_id: str) -> SchemaAssetBinding:
    raw = path.read_bytes()
    uri = json.loads(raw)["$id"]
    asset = SuppliedAsset(asset_id, "application/schema+json", raw, uri)
    return SchemaAssetBinding(_parsed(_ref(asset)), asset)


def _registry() -> ContractSchemaRegistry:
    bindings = []
    for path in sorted((ROOT / "schemas/v2/contract-kernel/common").glob("*/1.0.0.schema.json")):
        bindings.append(_schema_binding(path, f"schema:common:{path.parent.name}:1.0.0"))
    bindings.extend(
        [
            _schema_binding(
                ROOT / "schemas/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0.schema.json",
                "schema:m1-contract-requirement-set:1.0.0",
            ),
            _schema_binding(
                ROOT / "schemas/v2/contract-kernel/contract/artifact-family-catalog/1.0.0.schema.json",
                "schema:artifact-family-catalog:1.0.0",
            ),
            _schema_binding(
                ROOT / "schemas/v2/contract-kernel/contract/agentization-profile-release/1.0.0.schema.json",
                "schema:agentization-profile-release:1.0.0",
            ),
            _schema_binding(
                FIXTURE / "synthetic-immutable-record/1.0.0.schema.json",
                "schema:fixture:checkpoint-c-synthetic-record:1.0.0",
            ),
            _schema_binding(
                ROOT / "schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json",
                "schema:typed-terminal-result:1.0.0",
            ),
        ]
    )
    result = build_schema_registry(tuple(reversed(bindings)))
    assert type(result) is ContractSchemaRegistry, result
    return result


def _roots() -> tuple[SuppliedAsset, SuppliedAsset, SuppliedAsset]:
    return (
        _asset("requirements:m1-contract-requirement-set:1.0.0", "application/json", REQUIREMENTS),
        _asset("fixture-catalog:checkpoint-c-linkage/1.0.0", "application/json", CATALOG),
        _asset("fixture-profile:checkpoint-c-linkage/1.0.0", "application/json", PROFILE),
    )


def _support() -> tuple[SuppliedAsset, ...]:
    return (
        _asset("roadmap:v2-end-to-end-implementation-plan:2026-08-31", "text/markdown", ROADMAP),
        _asset("validator:checkpoint-c-contract-documents:1.0.0", "text/x-python", VALIDATOR),
        _asset("validator:checkpoint-a-immutable-record-payload:1.0.0", "text/x-python", GENERIC_VALIDATOR),
        _asset("vectors:catalog-profile-linkage:checkpoint-c/1.0.0", "application/json", VECTORS),
    )


def _build(
    requirements: SuppliedAsset | None = None,
    catalog: SuppliedAsset | None = None,
    profile: SuppliedAsset | None = None,
    support: tuple[SuppliedAsset, ...] | None = None,
):
    original = _roots()
    roots = (requirements or original[0], catalog or original[1], profile or original[2])
    return build_catalog_profile_constraints(
        *(_binding(asset) for asset in roots),
        _support() if support is None else support,
        _registry(),
    )


def _codes(result: tuple[Diagnostic, ...]) -> set[DiagnosticCode]:
    assert type(result) is tuple and result
    return {item.code for item in result}


def _serialized(result: tuple[Diagnostic, ...]) -> bytes:
    return json.dumps([item.to_dict() for item in result], sort_keys=True, separators=(",", ":")).encode()


def _mutated_asset(original: SuppliedAsset, document: dict[str, object]) -> SuppliedAsset:
    raw = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return SuppliedAsset(original.asset_id, original.media_type, raw, original.schema_uri)


def _linked_profile(catalog: SuppliedAsset, mutate=None) -> SuppliedAsset:
    original = _roots()[2]
    document = json.loads(original.raw_bytes)
    document["catalog_ref"] = _ref(catalog, path_hint="changed-display.json")
    if mutate is not None:
        mutate(document)
    return _mutated_asset(original, document)


def test_normative_floor_binds_exact_roadmap_and_complete_52_item_mapping() -> None:
    requirement, _, _ = _roots()
    document = json.loads(requirement.raw_bytes)
    result = validate_m1_contract_requirement_set_intrinsic(
        _binding(requirement), (_support()[0],), _registry()
    )
    assert result == ()
    assert document["item_count"] == len(document["items"]) == 52
    assert [item["ordinal"] for item in document["items"]] == list(range(1, 53))
    assert len({item["item_id"] for item in document["items"]}) == 52
    assert sum(len(item["source_occurrences"]) for item in document["items"]) == 53
    binding = next(item for item in document["items"] if item["item_id"] == "MATH_CLAIM_IR_BINDING")
    assert binding["source_occurrences"] == [
        {"source_group": "Mathematics", "source_position": 2},
        {"source_group": "Compatibility", "source_position": 1},
    ]
    assert "PAPER_SOURCE_SNAPSHOT" not in {item["item_id"] for item in document["items"]}
    source = document["source_binding"]
    raw = ROADMAP.read_bytes()
    start = source["section_start_heading"].encode()
    end = source["section_end_heading"].encode()
    assert raw.count(start) == raw.count(end) == 1
    section = raw[raw.index(start) : raw.index(end)]
    assert len(section) == source["section_byte_size"] == 3136
    assert raw_asset_sha256(section) == source["section_sha256"]


@pytest.mark.parametrize("ordinal", range(52))
def test_every_requirement_item_byte_replacement_loses_official_root_identity(ordinal: int) -> None:
    requirement, _, _ = _roots()
    document = json.loads(requirement.raw_bytes)
    document["items"][ordinal]["item_id"] += "_RENAMED"
    changed = _mutated_asset(requirement, document)
    result = validate_m1_contract_requirement_set_intrinsic(
        _binding(changed), (_support()[0],), _registry()
    )
    assert DiagnosticCode.CATALOG_REFERENCE_INVALID in _codes(result)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d["items"].pop(),
        lambda d: d["items"].append(deepcopy(d["items"][0])),
        lambda d: d["items"].reverse(),
        lambda d: d["items"][0]["source_occurrences"].append({"source_group": "Terminal", "source_position": 1}),
        lambda d: d["selection_rule"].update(target_milestone_token="M1.5"),
    ],
)
def test_requirement_remove_duplicate_reorder_regroup_and_m15_mutations_fail_closed(mutation) -> None:
    requirement, _, _ = _roots()
    document = json.loads(requirement.raw_bytes)
    mutation(document)
    result = validate_m1_contract_requirement_set_intrinsic(
        _binding(_mutated_asset(requirement, document)), (_support()[0],), _registry()
    )
    assert result


def test_builder_returns_complete_sealed_detached_non_authority_snapshot() -> None:
    result = _build()
    assert type(result) is CatalogProfileConstraints
    assert len(result.requirement_ids) == 52
    assert result.family_ids == (
        "CHECKPOINT_C_SYNTHETIC_RAW_ASSET",
        "CHECKPOINT_C_SYNTHETIC_RECORD",
    )
    assert result.stage_ids == ("CONTRACT_BOOTSTRAP", "SYNTHETIC_ANALYSIS")
    assert not any(hasattr(result, name) for name in ("approved", "released", "admitted", "contracted", "coverage", "maturity"))
    with pytest.raises(TypeError):
        CatalogProfileConstraints(None, None, None, (), (), (), ())  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        result.family_ids = ()  # type: ignore[misc]


def test_snapshot_seal_detects_accidental_tampering() -> None:
    result = _build()
    assert type(result) is CatalogProfileConstraints
    object.__setattr__(result, "_CatalogProfileConstraints__seal", "sha256:" + "0" * 64)
    with pytest.raises(ValueError):
        _ = result.family_ids


def test_support_permutation_is_deterministic_and_successful() -> None:
    support = list(_support())
    first = _build(support=tuple(support))
    random.Random(17).shuffle(support)
    second = _build(support=tuple(support))
    assert type(first) is type(second) is CatalogProfileConstraints
    assert first.family_ids == second.family_ids


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda d: d["family_policy_rows"].append(deepcopy(d["family_policy_rows"][0])), DiagnosticCode.CATALOG_DUPLICATE_FAMILY),
        (lambda d: d["stages"].reverse(), DiagnosticCode.CATALOG_STRUCTURE_INVALID),
        (lambda d: d["family_policy_rows"][0]["stage_policies"][0].update(minimum_runtime_obligation="CORE_REQUIRED"), DiagnosticCode.CATALOG_STRUCTURE_INVALID),
        (lambda d: d["family_policy_rows"][0]["stage_policies"][0]["cardinality"].update(minimum_count=1), DiagnosticCode.CATALOG_STRUCTURE_INVALID),
        (lambda d: d["family_policy_rows"][1]["successful_artifact"].update(record_type="agtxiv.other/1.0.0"), DiagnosticCode.CATALOG_FAMILY_BINDING_INVALID),
        (lambda d: d["family_policy_rows"][1].update(family_id="TYPED_TERMINAL_RESULT"), DiagnosticCode.CATALOG_TERMINAL_POLICY_INVALID),
    ],
)
def test_catalog_adversarial_structure_matrix(mutation, expected: DiagnosticCode) -> None:
    _, original, _ = _roots()
    document = json.loads(original.raw_bytes)
    mutation(document)
    changed = _mutated_asset(original, document)
    result = _build(catalog=changed, profile=_linked_profile(changed))
    assert expected in _codes(result)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda d: d["family_stage_rules"][1].update(profile_requirement_adjustment="OPTIONAL"), DiagnosticCode.PROFILE_REQUIREMENT_WEAKENING),
        (lambda d: d["family_stage_rules"][1]["cardinality"].update(maximum_count=2), DiagnosticCode.PROFILE_CARDINALITY_WEAKENING),
        (lambda d: d["family_stage_rules"][1]["allowed_producer_roles"].append("UNDECLARED_ROLE"), DiagnosticCode.PROFILE_PRODUCER_EXPANSION),
        (lambda d: d["family_stage_rules"][1]["terminal_disposition_policy"].update(structurally_permitted_outcomes=["RETRY_REQUIRED", "UNAVAILABLE"]), DiagnosticCode.PROFILE_OUTCOME_EXPANSION),
        (lambda d: d["family_stage_rules"][1]["terminal_disposition_policy"].update(minimum_declared_context_mode="PROFILE_BOUND"), DiagnosticCode.PROFILE_CONTEXT_WEAKENING),
        (lambda d: d["family_stage_rules"].reverse(), DiagnosticCode.PROFILE_FAMILY_SET_INVALID),
    ],
)
def test_profile_monotonicity_adversarial_matrix(mutation, expected: DiagnosticCode) -> None:
    requirement, catalog, profile = _roots()
    document = json.loads(profile.raw_bytes)
    mutation(document)
    result = _build(requirements=requirement, catalog=catalog, profile=_mutated_asset(profile, document))
    assert expected in _codes(result)


def test_optional_not_selected_branch_remains_explicit_and_valid() -> None:
    requirement, catalog, profile = _roots()
    document = json.loads(profile.raw_bytes)
    document["family_stage_rules"][0] = {
        "family_id": "CHECKPOINT_C_SYNTHETIC_RAW_ASSET",
        "family_version": "1.0.0",
        "stage_id": "CONTRACT_BOOTSTRAP",
        "profile_requirement_adjustment": "NOT_SELECTED",
    }
    result = _build(requirements=requirement, catalog=catalog, profile=_mutated_asset(profile, document))
    assert type(result) is CatalogProfileConstraints


def test_path_hint_only_catalog_identity_difference_is_authoritatively_equal() -> None:
    requirement, catalog, profile = _roots()
    document = json.loads(profile.raw_bytes)
    document["catalog_ref"]["path_hint"] = "another/display-only/location.json"
    result = _build(requirements=requirement, catalog=catalog, profile=_mutated_asset(profile, document))
    assert type(result) is CatalogProfileConstraints


def test_same_declared_support_id_with_different_bytes_is_distinguishable_and_deterministic() -> None:
    support = list(_support())
    source = support[-1]
    support[-1] = SuppliedAsset(source.asset_id, source.media_type, source.raw_bytes + b" ", source.schema_uri)
    first = _build(support=tuple(support))
    second = _build(support=tuple(reversed(support)))
    assert type(first) is type(second) is tuple
    assert _serialized(first) == _serialized(second)
    assert DiagnosticCode.CATALOG_SUPPORT_ASSET_ROLE_INVALID in _codes(first)


@pytest.mark.parametrize("bad", [None, [], (), object()])
def test_wrong_exact_root_binding_types_are_total(bad) -> None:
    requirement, catalog, profile = _roots()
    result = build_catalog_profile_constraints(
        bad,
        _binding(catalog),
        _binding(profile),
        _support(),
        _registry(),
    )
    assert type(result) is tuple
    assert DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH in _codes(result)


def test_noncanonical_duplicate_key_and_unpaired_surrogate_roots_fail_total() -> None:
    requirement, catalog, profile = _roots()
    for raw in (
        b'{"x":1,"x":2}',
        b'{"x":"\\ud800"}',
        b'{ "document_type": "AGTXIV_ARTIFACT_FAMILY_CATALOG" }',
    ):
        changed = SuppliedAsset(catalog.asset_id, catalog.media_type, raw)
        result = build_catalog_profile_constraints(
            _binding(requirement), _binding(changed), _binding(profile), _support(), _registry()
        )
        assert type(result) is tuple and result


def test_public_apis_do_not_consult_ambient_io(monkeypatch: pytest.MonkeyPatch) -> None:
    roots = _roots()
    bindings = tuple(_binding(asset) for asset in roots)
    support = _support()
    registry = _registry()

    def forbidden(*args, **kwargs):
        raise AssertionError("ambient capability was consulted")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(time, "time", forbidden)
    monkeypatch.setattr(os, "getenv", forbidden)
    monkeypatch.setattr(random, "random", forbidden)
    result = build_catalog_profile_constraints(
        bindings[0], bindings[1], bindings[2], support, registry
    )
    assert type(result) is CatalogProfileConstraints


def _terminal_helpers():
    path = ROOT / "tests/unit/contracts/test_terminal_validation.py"
    spec = importlib.util.spec_from_file_location("_checkpoint_c_terminal_helpers", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _terminal_record(
    constraints: CatalogProfileConstraints,
    *,
    family: str = "CHECKPOINT_C_SYNTHETIC_RECORD",
    stage: str = "SYNTHETIC_ANALYSIS",
    mode: str = "FROZEN_SCOPE_BOUND",
    outcome: str = "RETRY_REQUIRED",
    role: str = "SYNTHETIC_RECORD_PRODUCER",
    reason: str = "AGTXIV.TERMINAL.EXAMPLE",
) -> ParsedCanonicalValue:
    helpers = _terminal_helpers()
    payload = helpers._payload(mode=mode, outcome=outcome)
    catalog_ref = constraints.catalog_ref.to_python()
    profile_ref = constraints.profile_ref.to_python()
    catalog_ref["path_hint"] = "terminal-catalog-display.json"
    profile_ref["path_hint"] = "terminal-profile-display.json"
    payload["binding_context"]["catalog_ref"] = catalog_ref
    payload["binding_context"]["profile_ref"] = profile_ref
    payload["target_obligation"]["family_id"] = family
    payload["target_obligation"]["stage_id"] = stage
    payload["declared_reason"]["declared_reason_code"] = reason
    terminal_binding = _schema_binding(
        ROOT / "schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json",
        "schema:typed-terminal-result:1.0.0",
    )
    return helpers._record(
        terminal_binding,
        payload=payload,
        envelope_changes={
            "producer_context": {
                "producer": {"actor_kind": "AGENT", "actor_id": "agent:test-1"},
                "role": role,
                "attempt_id": "attempt:test-1",
                "implementation_ref": helpers._asset_ref("implementation:test-1", "8"),
                "environment_ref": helpers._asset_ref("environment:test-1", "9"),
            }
        },
    )


def test_terminal_constraints_accept_exact_selected_role_context_and_outcome() -> None:
    constraints = _build()
    assert type(constraints) is CatalogProfileConstraints
    record = _terminal_record(constraints)
    assert validate_typed_terminal_result_catalog_constraints(record, _registry(), constraints) == ()


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"family": "UNKNOWN_FAMILY"}, DiagnosticCode.CATALOG_UNKNOWN_FAMILY),
        ({"stage": "UNKNOWN_STAGE"}, DiagnosticCode.CATALOG_UNKNOWN_STAGE),
        ({"role": "OTHER_PRODUCER"}, DiagnosticCode.CATALOG_PRODUCER_ROLE_NOT_ALLOWED),
        ({"mode": "PLAN_BOUND"}, DiagnosticCode.CATALOG_CONTEXT_MODE_INSUFFICIENT),
        ({"outcome": "UNAVAILABLE"}, DiagnosticCode.CATALOG_OUTCOME_NOT_ALLOWED),
        ({"family": "CHECKPOINT_C_SYNTHETIC_RAW_ASSET", "stage": "CONTRACT_BOOTSTRAP"}, DiagnosticCode.CATALOG_TERMINAL_NOT_ALLOWED),
    ],
)
def test_terminal_constraint_adversarial_matrix(changes, expected: DiagnosticCode) -> None:
    constraints = _build()
    assert type(constraints) is CatalogProfileConstraints
    record = _terminal_record(constraints, **changes)
    result = validate_typed_terminal_result_catalog_constraints(record, _registry(), constraints)
    assert expected in _codes(result)


def test_terminal_intrinsic_failure_hard_stops_catalog_interpretation() -> None:
    constraints = _build()
    assert type(constraints) is CatalogProfileConstraints
    document = _terminal_record(constraints).to_python()
    document["content_hash"] = "sha256:" + "0" * 64
    result = validate_typed_terminal_result_catalog_constraints(
        _parsed(document), _registry(), constraints
    )
    assert DiagnosticCode.RECORD_HASH_MISMATCH in _codes(result)
    assert not any(str(code).startswith("AGTXIV.CATALOG.") for code in _codes(result))


def test_terminal_reason_registration_is_deliberately_not_inferred() -> None:
    constraints = _build()
    assert type(constraints) is CatalogProfileConstraints
    first = validate_typed_terminal_result_catalog_constraints(
        _terminal_record(constraints, reason="AGTXIV.TERMINAL.REASON_A"),
        _registry(),
        constraints,
    )
    second = validate_typed_terminal_result_catalog_constraints(
        _terminal_record(constraints, reason="AGTXIV.TERMINAL.REASON_B"),
        _registry(),
        constraints,
    )
    assert first == second == ()


def test_terminal_not_selected_profile_branch_is_rejected_explicitly() -> None:
    requirement, catalog, profile = _roots()
    document = json.loads(profile.raw_bytes)
    document["family_stage_rules"][0] = {
        "family_id": "CHECKPOINT_C_SYNTHETIC_RAW_ASSET",
        "family_version": "1.0.0",
        "stage_id": "CONTRACT_BOOTSTRAP",
        "profile_requirement_adjustment": "NOT_SELECTED",
    }
    constraints = _build(
        requirements=requirement,
        catalog=catalog,
        profile=_mutated_asset(profile, document),
    )
    assert type(constraints) is CatalogProfileConstraints
    record = _terminal_record(
        constraints,
        family="CHECKPOINT_C_SYNTHETIC_RAW_ASSET",
        stage="CONTRACT_BOOTSTRAP",
    )
    result = validate_typed_terminal_result_catalog_constraints(record, _registry(), constraints)
    assert DiagnosticCode.CATALOG_OBLIGATION_NOT_SELECTED in _codes(result)


def test_diagnostics_are_byte_identical_across_repetition() -> None:
    requirement, catalog, profile = _roots()
    document = json.loads(profile.raw_bytes)
    document["family_stage_rules"][1]["allowed_producer_roles"].append("UNDECLARED_ROLE")
    changed = _mutated_asset(profile, document)
    results = [_build(requirements=requirement, catalog=catalog, profile=changed) for _ in range(3)]
    assert all(type(result) is tuple for result in results)
    assert len({_serialized(result) for result in results}) == 1


def _registry_with_substituted_official_schema(name: str) -> ContractSchemaRegistry:
    official = {
        "requirements": (
            ROOT / "schemas/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0.schema.json",
            "schema:m1-contract-requirement-set:1.0.0",
        ),
        "catalog": (
            ROOT / "schemas/v2/contract-kernel/contract/artifact-family-catalog/1.0.0.schema.json",
            "schema:artifact-family-catalog:1.0.0",
        ),
        "profile": (
            ROOT / "schemas/v2/contract-kernel/contract/agentization-profile-release/1.0.0.schema.json",
            "schema:agentization-profile-release:1.0.0",
        ),
    }
    bindings = [
        _schema_binding(path, f"schema:common:{path.parent.name}:1.0.0")
        for path in sorted((ROOT / "schemas/v2/contract-kernel/common").glob("*/1.0.0.schema.json"))
    ]
    for key, (path, asset_id) in official.items():
        if key != name:
            bindings.append(_schema_binding(path, asset_id))
            continue
        document = json.loads(path.read_bytes())
        document["description"] += " substituted without changing $id"
        raw = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
        uri = document["$id"]
        asset = SuppliedAsset(asset_id, "application/schema+json", raw, uri)
        bindings.append(SchemaAssetBinding(_parsed(_ref(asset)), asset))
    bindings.extend(
        [
            _schema_binding(
                FIXTURE / "synthetic-immutable-record/1.0.0.schema.json",
                "schema:fixture:checkpoint-c-synthetic-record:1.0.0",
            ),
            _schema_binding(
                ROOT / "schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json",
                "schema:typed-terminal-result:1.0.0",
            ),
        ]
    )
    result = build_schema_registry(tuple(bindings))
    assert type(result) is ContractSchemaRegistry, result
    return result


@pytest.mark.parametrize("name", ["requirements", "catalog", "profile"])
def test_same_id_substituted_official_schema_fails_public_gate_before_semantics(name: str) -> None:
    registry = _registry_with_substituted_official_schema(name)
    requirement, catalog, profile = _roots()
    if name == "requirements":
        result = validate_m1_contract_requirement_set_intrinsic(
            _binding(requirement), (_support()[0],), registry
        )
    else:
        result = build_catalog_profile_constraints(
            _binding(requirement),
            _binding(catalog),
            _binding(profile),
            _support(),
            registry,
        )
    assert [diagnostic.code for diagnostic in result] == [DiagnosticCode.ASSET_SCHEMA_MISMATCH]


@pytest.mark.parametrize("position", [0, -1])
@pytest.mark.parametrize(
    ("media_type", "raw"),
    [
        ("application/json", b"different role and bytes"),
        ("application/schema+json", b"different schema bytes"),
    ],
)
def test_registry_and_support_asset_ids_share_one_fail_closed_namespace(
    position: int, media_type: str, raw: bytes
) -> None:
    collision = SuppliedAsset(
        "schema:artifact-family-catalog:1.0.0",
        media_type,
        raw,
        None,
    )
    support = list(_support())
    support.insert(position, collision)
    first = _build(support=tuple(support))
    second = _build(support=tuple(reversed(support)))
    assert type(first) is type(second) is tuple
    assert _serialized(first) == _serialized(second)
    assert [item.code for item in first] == [DiagnosticCode.CATALOG_REFERENCE_INVALID]


def _full_schema_support_closure() -> tuple[SuppliedAsset, SuppliedAsset, tuple[SuppliedAsset, ...]]:
    _, catalog, profile = _roots()
    catalog_document = json.loads(catalog.raw_bytes)
    profile_document = json.loads(profile.raw_bytes)
    family_template = catalog_document["family_policy_rows"][0]
    rule_template = profile_document["family_stage_rules"][0]
    families = []
    rules = []
    support = [_support()[0]]
    for index in range(256):
        suffix = f"{index:03d}"
        family_id = f"BOUNDARY_FAMILY_{suffix}"
        validator = SuppliedAsset(
            f"validator:boundary-{suffix}:1.0.0",
            "text/x-python",
            f"# boundary validator {suffix}\n".encode(),
        )
        vector_id = f"vectors:boundary-{suffix}:1.0.0"
        positive_id = f"vector:boundary-{suffix}-positive:1"
        negative_id = f"vector:boundary-{suffix}-negative:1"
        target = {
            "family_id": family_id,
            "family_version": "1.0.0",
            "stage_id": "CONTRACT_BOOTSTRAP",
            "artifact_kind": "RAW_CONTRACT_ASSET",
        }
        vector_document = {
            "fixture_purpose": "STRUCTURAL_CONFORMANCE_ONLY",
            "vector_set_id": vector_id,
            "vector_set_version": "1.0.0",
            "vectors": [
                {
                    "expected_diagnostic_codes": [],
                    "polarity": "POSITIVE",
                    "target": target,
                    "template_id": "template:boundary-positive:1",
                    "vector_id": positive_id,
                    "vector_kind": "FAMILY_CONFORMANCE",
                },
                {
                    "expected_diagnostic_codes": ["AGTXIV.CATALOG.REFERENCE_INVALID"],
                    "mutation_id": "mutation:boundary-negative:1",
                    "polarity": "NEGATIVE",
                    "target": target,
                    "template_id": "template:boundary-negative:1",
                    "vector_id": negative_id,
                    "vector_kind": "FAMILY_CONFORMANCE",
                },
            ],
        }
        vector = SuppliedAsset(vector_id, "application/json", _canonical_document(vector_document))
        family = deepcopy(family_template)
        family.update(
            family_id=family_id,
            validator_ref=_ref(validator),
            validator_entry_point=f"boundary.validator_{suffix}",
            conformance_vector_ref=_ref(vector),
            positive_vector_ids=[positive_id],
            negative_vector_ids=[negative_id],
        )
        rule = deepcopy(rule_template)
        rule["family_id"] = family_id
        families.append(family)
        rules.append(rule)
        support.extend((validator, vector))
    catalog_document["catalog_id"] = "catalog:support-boundary/1.0.0"
    catalog_document["stages"] = catalog_document["stages"][:1]
    catalog_document["family_policy_rows"] = families
    changed_catalog = _mutated_asset(catalog, catalog_document)
    profile_document["catalog_ref"] = _ref(changed_catalog)
    profile_document["stage_rules"] = profile_document["stage_rules"][:1]
    profile_document["family_stage_rules"] = rules
    changed_profile = _mutated_asset(profile, profile_document)
    return changed_catalog, changed_profile, tuple(support)


def test_support_asset_count_accepts_complete_schema_derived_closure() -> None:
    requirement = _roots()[0]
    catalog, profile, support = _full_schema_support_closure()
    assert len(support) == 1 + 2 * 256 == 513
    result = _build(requirements=requirement, catalog=catalog, profile=profile, support=support)
    assert type(result) is CatalogProfileConstraints, result


def test_support_asset_count_rejects_schema_derived_closure_plus_one() -> None:
    requirement = _roots()[0]
    catalog, profile, support = _full_schema_support_closure()
    overflow = SuppliedAsset("validator:closure-overflow:1.0.0", "text/x-python", b"# overflow\n")
    result = _build(requirements=requirement, catalog=catalog, profile=profile, support=support + (overflow,))
    assert [item.code for item in result] == [DiagnosticCode.CATALOG_REFERENCE_INVALID]


def test_no_unversioned_support_byte_budget_rejects_exact_graph() -> None:
    support = list(_support())
    validator = support[1]
    large = SuppliedAsset(validator.asset_id, validator.media_type, validator.raw_bytes + b"#" * 4_194_305)
    catalog = json.loads(CATALOG.read_bytes())
    catalog["family_policy_rows"][0]["validator_ref"] = _ref(large)
    changed_catalog = _mutated_asset(_roots()[1], catalog)
    changed_profile = _linked_profile(changed_catalog)
    support[1] = large
    result = _build(catalog=changed_catalog, profile=changed_profile, support=tuple(support))
    assert type(result) is CatalogProfileConstraints, result


def test_type_and_declared_size_preflight_stop_before_hash_or_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    import agtxiv_v2.contracts.catalog_validation as validation

    def forbidden(*args, **kwargs):
        raise AssertionError("hash or parse ran before preflight completed")

    monkeypatch.setattr(validation, "raw_asset_sha256", forbidden)
    monkeypatch.setattr(validation, "parse_canonical_json", forbidden)
    requirement, catalog, profile = _roots()
    ref = _ref(requirement)
    ref["byte_size"] += 1
    bad_size = RawContractAssetBinding(_parsed(ref), requirement)
    result = build_catalog_profile_constraints(
        bad_size, _binding(catalog), _binding(profile), _support(), _registry()
    )
    assert [item.code for item in result] == [DiagnosticCode.REF_HASH_MISMATCH]

    forged = _support()[-1]
    object.__setattr__(forged, "raw_bytes", bytearray(forged.raw_bytes))
    result = build_catalog_profile_constraints(
        _binding(requirement), _binding(catalog), _binding(profile), _support()[:-1] + (forged,), _registry()
    )
    assert [item.code for item in result] == [DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH]

def _canonical_document(document: object) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("vector_set_version", "2.0.0"),
        ("vector_set_version", "1.0.1"),
        ("vector_set_id", "vectors:other-valid-set:1.0.0"),
    ],
)
def test_public_builder_rejects_rehashed_wrong_fixture_vector_identity(field: str, value: str) -> None:
    requirement, catalog, _ = _roots()
    document = json.loads(VECTORS.read_bytes())
    document[field] = value
    vector_asset_id = value if field == "vector_set_id" else _support()[-1].asset_id
    changed_vector = SuppliedAsset(vector_asset_id, "application/json", _canonical_document(document))
    catalog_document = json.loads(catalog.raw_bytes)
    for family in catalog_document["family_policy_rows"]:
        family["conformance_vector_ref"] = _ref(changed_vector)
    changed_catalog = _mutated_asset(catalog, catalog_document)
    changed_profile = _linked_profile(changed_catalog)
    support = _support()[:-1] + (changed_vector,)
    result = _build(
        requirements=requirement,
        catalog=changed_catalog,
        profile=changed_profile,
        support=support,
    )
    assert _codes(result) == {DiagnosticCode.CATALOG_SUPPORT_ASSET_ROLE_INVALID}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d.pop("vector_set_id"),
        lambda d: d.update(vector_set_id=1),
        lambda d: d.update(vector_set_id="not-namespaced"),
        lambda d: d.update(vector_set_id="v:" + "x" * 255),
        lambda d: d.pop("vector_set_version"),
        lambda d: d.update(vector_set_version=1),
        lambda d: d.update(vector_set_version="1.0"),
        lambda d: d.update(vector_set_version="01.0.0"),
        lambda d: d.update(vector_set_version="1.0.1"),
        lambda d: d.update(vector_set_version="2.0.0"),
        lambda d: d.update(vector_set_id="vectors:other-valid-set:1.0.0"),
        lambda d: d.update(fixture_purpose="OTHER"),
        lambda d: d.update(extra="closed"),
        lambda d: d.update(vectors=[]),
        lambda d: d.update(vectors=d["vectors"] * 33),
        lambda d: d["vectors"][0].pop("vector_id"),
        lambda d: d["vectors"][0].update(vector_id="invalid"),
        lambda d: d["vectors"][0].update(polarity="UNKNOWN"),
        lambda d: d["vectors"][0].update(vector_kind="UNKNOWN"),
        lambda d: d["vectors"][0].update(template_id="invalid"),
        lambda d: d["vectors"][0].update(mutation_id="mutation:positive:1"),
        lambda d: d["vectors"][1].pop("mutation_id"),
        lambda d: d["vectors"][1].update(mutation_id="invalid"),
        lambda d: d["vectors"][0].update(expected_diagnostic_codes=["AGTXIV.CATALOG.UNKNOWN_STAGE"]),
        lambda d: d["vectors"][1].update(expected_diagnostic_codes=[]),
        lambda d: d["vectors"][1].update(expected_diagnostic_codes=["UNKNOWN"]),
        lambda d: d["vectors"][0]["target"].update(family_id=1),
        lambda d: d["vectors"][0]["target"].update(family_id="lowercase"),
        lambda d: d["vectors"][0]["target"].update(family_version=1),
        lambda d: d["vectors"][0]["target"].update(family_version="1.0"),
        lambda d: d["vectors"][0]["target"].update(stage_id=1),
        lambda d: d["vectors"][0]["target"].update(stage_id="lowercase"),
        lambda d: d["vectors"][0]["target"].update(artifact_kind="OPAQUE_BYTES"),
        lambda d: d["vectors"][0]["target"].update(extra="closed"),
        lambda d: d["vectors"][4].update(cross_test_kind="UNKNOWN"),
        lambda d: d["vectors"][4].update(target={}),
    ],
)
def test_closed_vector_envelope_rejects_every_field_mutation(mutation) -> None:
    from agtxiv_v2.contracts.catalog_validation import _vector_index

    document = json.loads(VECTORS.read_bytes())
    mutation(document)
    assert _vector_index(_canonical_document(document), "vectors:catalog-profile-linkage:checkpoint-c/1.0.0", "vectors:catalog-profile-linkage:checkpoint-c/1.0.0") is None


def test_catalog_family_vectors_execute_declared_validator_entrypoints_data_driven() -> None:
    import importlib

    catalog = json.loads(CATALOG.read_bytes())
    vector_document = json.loads(VECTORS.read_bytes())
    vectors = {
        vector["vector_id"]: vector
        for vector in vector_document["vectors"]
        if vector["vector_kind"] == "FAMILY_CONFORMANCE"
    }
    listed = {
        vector_id
        for row in catalog["family_policy_rows"]
        for key in ("positive_vector_ids", "negative_vector_ids")
        for vector_id in row[key]
    }
    assert listed == set(vectors)

    schema_helpers = importlib.util.spec_from_file_location(
        "_checkpoint_c_schema_helpers",
        ROOT / "tests/unit/contracts/test_catalog_profile_schemas.py",
    )
    assert schema_helpers is not None and schema_helpers.loader is not None
    module = importlib.util.module_from_spec(schema_helpers)
    schema_helpers.loader.exec_module(module)
    valid_record = module._synthetic_record(_registry())

    for row in catalog["family_policy_rows"]:
        module_name, function_name = row["validator_entry_point"].rsplit(".", 1)
        validator = getattr(importlib.import_module(module_name), function_name)
        for key in ("positive_vector_ids", "negative_vector_ids"):
            for vector_id in row[key]:
                vector = vectors[vector_id]
                assert vector["template_id"] in {
                    "template:requirements-valid:1",
                    "template:record-valid:1",
                }
                if row["successful_artifact"]["artifact_kind"] == "RAW_CONTRACT_ASSET":
                    requirement = _roots()[0]
                    if vector["polarity"] == "NEGATIVE":
                        assert vector["mutation_id"] == "mutation:remove-profile-requirement:1"
                        document = json.loads(requirement.raw_bytes)
                        document["items"] = [
                            item for item in document["items"]
                            if item["item_id"] != "AGENTIZATION_PROFILE_RELEASE"
                        ]
                        requirement = _mutated_asset(requirement, document)
                    result = validator(_binding(requirement), (_support()[0],), _registry())
                else:
                    record = valid_record
                    if vector["polarity"] == "NEGATIVE":
                        assert vector["mutation_id"] == "mutation:record-hash:1"
                        document = record.to_python()
                        document["content_hash"] = "sha256:" + "0" * 64
                        record = _parsed(document)
                    result = validator(record, _registry())
                assert [str(item.code) for item in result] == vector["expected_diagnostic_codes"]
