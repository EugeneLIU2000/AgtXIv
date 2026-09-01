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

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from agtxiv_v2.contracts import (  # noqa: E402
    ContractSchemaRegistry, Diagnostic, DiagnosticCode, KernelValidationPolicyConstraints,
    ParsedCanonicalValue, RawContractAssetBinding, SchemaAssetBinding, SuppliedAsset,
    build_canonical_value, build_kernel_validation_policy_constraints, build_schema_registry,
    canonical_bytes, raw_asset_sha256, validate_emitted_diagnostic_registration,
    validate_stable_code_catalog_intrinsic, validate_typed_terminal_result_kernel_constraints,
)

CATALOG = ROOT / "contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.0.0.json"
POLICY = ROOT / "contracts/v2/contract-kernel/code-policy/kernel-validation-policy/1.0.0.json"
VALIDATOR = ROOT / "src/agtxiv_v2/contracts/code_policy_validation.py"
VECTORS = ROOT / "fixtures/v2-contract-kernel/code-policy/1.0.0/code-policy-conformance-vectors.json"

# Reviewed literal projection of Checkpoint D Section 6; deliberately independent of messages.
EXPECTED_DIAGNOSTICS = ((1, 'AGTXIV.CANON.BOM_FORBIDDEN', 'Input begins with a forbidden UTF-8 byte-order mark.'), (2, 'AGTXIV.CANON.INVALID_UTF8', 'Input bytes are not valid strict UTF-8.'), (3, 'AGTXIV.CANON.INVALID_JSON', 'UTF-8 input is not one complete syntactically valid JSON value.'), (4, 'AGTXIV.CANON.DUPLICATE_KEY', 'A JSON object contains the same member name more than once before normalization.'), (5, 'AGTXIV.CANON.NORMALIZED_KEY_COLLISION', 'Distinct object member names collide after required Unicode normalization.'), (6, 'AGTXIV.CANON.UNPAIRED_SURROGATE', 'A string contains an unpaired Unicode surrogate code point.'), (7, 'AGTXIV.CANON.UNSUPPORTED_NUMBER', 'A JSON number uses a numeric form outside the canonical profile.'), (8, 'AGTXIV.CANON.INTEGER_OUT_OF_RANGE', 'An integer lies outside the permitted I-JSON exact-integer range.'), (9, 'AGTXIV.CANON.NESTING_TOO_DEEP', 'A submitted value exceeds the canonical maximum nesting depth.'), (10, 'AGTXIV.CANON.UNSUPPORTED_PROGRAMMATIC_TYPE', 'A programmatic input contains a value whose exact Python type is outside the canonical JSON model.'), (11, 'AGTXIV.CANON.NON_STRING_OBJECT_KEY', 'A programmatic object has a member key whose exact type is not string.'), (12, 'AGTXIV.CANON.CYCLIC_PROGRAMMATIC_VALUE', 'A programmatic array or object contains an identity cycle.'), (13, 'AGTXIV.CANON.INVALID_RECORD_SHAPE', 'A value submitted for record hashing lacks the exact required record projection shape.'), (14, 'AGTXIV.CANON.INVALID_INTERNAL_VALUE', 'An opaque canonical value fails its internal integrity invariant.'), (15, 'AGTXIV.REF.UNRESOLVED', 'An exact asset, record, or component reference has no uniquely supplied target.'), (16, 'AGTXIV.REF.HASH_MISMATCH', 'Supplied target bytes, byte size, or canonical content hash differ from the exact reference.'), (17, 'AGTXIV.REF.TYPE_MISMATCH', 'A resolved target has the wrong declared media, schema, record, or component type for the reference.'), (18, 'AGTXIV.CONTRACT.MUTABLE_REF', 'A contract-bound authoritative reference contains mutable or non-exact identity.'), (19, 'AGTXIV.RECORD.INVALID_ENVELOPE', 'An immutable record envelope is absent, open, malformed, or inconsistent with its required closed shape.'), (20, 'AGTXIV.RECORD.SUPERSESSION_MISMATCH', 'A record revision or supersession relation is inconsistent with immutable revision rules.'), (21, 'AGTXIV.RECORD.HASH_MISMATCH', "A record's declared content hash differs from its canonical record-hash projection."), (22, 'AGTXIV.SCHEMA.EMPTY_REGISTRY', 'Schema-registry construction received no schema bindings.'), (23, 'AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH', 'A schema or validator API received an input with an invalid exact type or failed opaque/sealed integrity.'), (24, 'AGTXIV.SCHEMA.INVALID_DOCUMENT', 'Strict parsing succeeded, but the supplied schema is not one top-level JSON object.'), (25, 'AGTXIV.SCHEMA.DIALECT_MISMATCH', 'A schema does not declare the required JSON Schema Draft 2020-12 dialect.'), (26, 'AGTXIV.SCHEMA.ID_MISMATCH', "A schema's `$id`, schema URI, or exact binding identities disagree."), (27, 'AGTXIV.SCHEMA.DUPLICATE_ID', 'More than one supplied schema claims the same authoritative schema identity.'), (28, 'AGTXIV.SCHEMA.META_INVALID', "A schema fails the supported dialect's meta-schema or closed-keyword constraints."), (29, 'AGTXIV.SCHEMA.UNRESOLVED_REF', 'A schema `$ref` does not resolve inside the explicit offline registry.'), (30, 'AGTXIV.SCHEMA.REFERENCE_CYCLE', 'The admitted schema-reference graph contains a forbidden cycle.'), (31, 'AGTXIV.SCHEMA.REMOTE_REF_FORBIDDEN', 'A schema reference would require remote or non-registry resolution.'), (32, 'AGTXIV.RECORD.TYPE_SCHEMA_MISMATCH', "A record's declared record type differs from the exact family schema's record-type declaration."), (33, 'AGTXIV.RECORD.PAYLOAD_INVALID', 'A record payload violates its exact family schema.'), (34, 'AGTXIV.TERMINAL.SCHEMA_MISMATCH', 'A typed terminal record does not bind the compiled official terminal schema bytes.'), (35, 'AGTXIV.TERMINAL.ATTEMPT_MISMATCH', 'Terminal payload attempt identity or producer context is absent or differs from the envelope attempt.'), (36, 'AGTXIV.TERMINAL.CONTEXT_INVALID', 'A terminal binding context and its target basis have an intrinsically inconsistent shape or identity.'), (37, 'AGTXIV.TERMINAL.TARGET_INVALID', 'A terminal target is intrinsically recursive or otherwise forbidden as a terminal obligation target.'), (38, 'AGTXIV.TERMINAL.EVIDENCE_INVALID', 'Terminal evidence has duplicate IDs/references, noncanonical order, or a forbidden terminal/self reference.'), (39, 'AGTXIV.TERMINAL.DISPOSITION_INVALID', 'Terminal outcome, retry disposition, or next action violates the intrinsic compatibility matrix.'), (40, 'AGTXIV.TERMINAL.RESOURCE_INVALID', 'Declared resource dimensions, ordering, partition, or observed-limit relation is mechanically inconsistent.'), (41, 'AGTXIV.CONTRACT.ASSET_SCHEMA_MISMATCH', "A raw contract document's official schema ref or registry schema bytes differ from the compiled ruler."), (42, 'AGTXIV.CONTRACT.ASSET_INVALID', 'A correctly bound raw contract document is noncanonical or violates its exact official schema.'), (43, 'AGTXIV.REQUIREMENTS.SOURCE_BINDING_MISMATCH', 'Requirement-set roadmap bytes, Git blob identity, bounded section, or exact source ref differs from the frozen source.'), (44, 'AGTXIV.REQUIREMENTS.ITEM_SET_MISMATCH', 'Requirement item membership or uniqueness differs from the compiled 52-item floor.'), (45, 'AGTXIV.REQUIREMENTS.ITEM_ORDER_MISMATCH', 'Requirement item order, kind, or source occurrence differs from the compiled floor.'), (46, 'AGTXIV.REQUIREMENTS.MAPPING_MISMATCH', 'Selected roadmap rows or their reviewed requirement expansion differs from the frozen mapping.'), (47, 'AGTXIV.REQUIREMENTS.SELECTION_RULE_MISMATCH', 'Requirement milestone selection differs from the exact M1-token rule.'), (48, 'AGTXIV.CATALOG.REFERENCE_INVALID', 'A Catalog/Profile root or support reference is unresolved, aliased, excessive, or invalid for its declared graph role.'), (49, 'AGTXIV.CATALOG.EXACT_REF_CYCLE', 'The recognized Catalog/Profile exact-reference graph contains a root alias or cycle.'), (50, 'AGTXIV.CATALOG.DUPLICATE_FAMILY', 'Catalog family identity is duplicated under the v1 global-family rule.'), (51, 'AGTXIV.CATALOG.DUPLICATE_STAGE', 'Catalog stage identity is duplicated.'), (52, 'AGTXIV.CATALOG.STRUCTURE_INVALID', 'Catalog ordering, uniqueness, applicability, cardinality, vector, or stage-coverage structure is invalid.'), (53, 'AGTXIV.CATALOG.FAMILY_BINDING_INVALID', 'A family successful-artifact kind, schema, or record-type binding is inconsistent.'), (54, 'AGTXIV.CATALOG.SUPPORT_ASSET_ROLE_INVALID', 'Catalog validator or vector bytes do not resolve in the exact declared support role or target partition.'), (55, 'AGTXIV.CATALOG.TERMINAL_POLICY_INVALID', 'Catalog terminal recursion, outcome order, context minimum, or accounting-unit terminal policy is invalid.'), (56, 'AGTXIV.PROFILE.CATALOG_MISMATCH', 'A Profile does not exact-bind the supplied Catalog bytes.'), (57, 'AGTXIV.PROFILE.FAMILY_SET_INVALID', 'Profile stage or family-stage keys do not exactly mirror Catalog membership and order.'), (58, 'AGTXIV.PROFILE.REQUIREMENT_WEAKENING', 'A Profile weakens or deselects a Catalog core requirement.'), (59, 'AGTXIV.PROFILE.CARDINALITY_WEAKENING', 'Profile cardinality weakens Catalog bounds or contradicts its selected adjustment.'), (60, 'AGTXIV.PROFILE.PRODUCER_EXPANSION', 'Profile producer roles are reordered or expand beyond the Catalog role set.'), (61, 'AGTXIV.PROFILE.TERMINAL_POLICY_MISMATCH', 'Profile terminal-permission mode differs from the Catalog mode.'), (62, 'AGTXIV.PROFILE.OUTCOME_EXPANSION', 'Profile terminal outcomes are reordered or expand beyond Catalog outcomes.'), (63, 'AGTXIV.PROFILE.CONTEXT_WEAKENING', 'Profile stage or family terminal context is weaker than the effective Catalog minimum.'), (64, 'AGTXIV.CATALOG.CONTEXT_BINDING_MISMATCH', "A terminal context's exact Catalog/Profile refs differ from the sealed C constraints."), (65, 'AGTXIV.CATALOG.UNKNOWN_FAMILY', 'A terminal target family is absent from the exact Catalog constraints.'), (66, 'AGTXIV.CATALOG.UNKNOWN_STAGE', 'A terminal target stage is absent for the resolved Catalog family.'), (67, 'AGTXIV.CATALOG.OBLIGATION_NOT_SELECTED', 'A terminal record targets a Profile branch explicitly marked `NOT_SELECTED`.'), (68, 'AGTXIV.CATALOG.TERMINAL_NOT_ALLOWED', 'Effective Catalog/Profile policy forbids a terminal card for the target.'), (69, 'AGTXIV.CATALOG.PRODUCER_ROLE_NOT_ALLOWED', 'Terminal producer role is outside the effective Profile role subset.'), (70, 'AGTXIV.CATALOG.CONTEXT_MODE_INSUFFICIENT', 'Terminal context mode is weaker than the effective Profile minimum.'), (71, 'AGTXIV.CATALOG.OUTCOME_NOT_ALLOWED', 'Terminal outcome is outside the effective Profile outcome subset.'), (72, 'AGTXIV.CODE.CATALOG_INVALID', 'A correctly bound genesis stable-code document violates code identity, kind, order, exact version, stable meaning, or declared resource rules.'), (73, 'AGTXIV.CODE.ENUM_PROJECTION_MISMATCH', 'The catalog `VALIDATION_DIAGNOSTIC` projection and final compiled `DiagnosticCode` enum are not equal in membership, ordinal, and declaration order.'), (74, 'AGTXIV.CODE.POLICY_REFERENCE_INVALID', 'A policy exact reference, official schema pin, validator/vector binding, or sealed C-constraint root differs from the supplied fixed bytes.'), (75, 'AGTXIV.CODE.POLICY_INVALID', 'A correctly bound genesis policy violates its closed gate, registration, canonical order, exact target, or declared resource rules.'), (76, 'AGTXIV.CODE.EMITTED_DIAGNOSTIC_UNREGISTERED', "An emitted diagnostic is absent from the trusted catalog's `VALIDATION_DIAGNOSTIC` projection."), (77, 'AGTXIV.REASON.UNREGISTERED', 'An intrinsically and structurally valid terminal record declares a code that is absent, not an active `TERMINAL_REASON`, or not registered by the exact policy.'), (78, 'AGTXIV.REASON.CONSTRAINT_MISMATCH', 'A registered terminal reason is used outside its policy outcome, retry, context, or exact family-version-stage constraints.'))


def _parsed(value: object) -> ParsedCanonicalValue:
    result = build_canonical_value(value)
    assert type(result) is ParsedCanonicalValue
    return result


def _asset(asset_id: str, media: str, path: Path, uri: str | None = None) -> SuppliedAsset:
    return SuppliedAsset(asset_id, media, path.read_bytes(), uri)


def _ref(asset: SuppliedAsset) -> dict[str, object]:
    result = {"asset_id": asset.asset_id, "media_type": asset.media_type, "byte_size": len(asset.raw_bytes), "sha256": raw_asset_sha256(asset.raw_bytes)}
    if asset.schema_uri is not None:
        result["schema_uri"] = asset.schema_uri
    return result


def _binding(asset: SuppliedAsset) -> RawContractAssetBinding:
    return RawContractAssetBinding(_parsed(_ref(asset)), asset)


def _schema_binding(path: Path, asset_id: str) -> SchemaAssetBinding:
    raw = path.read_bytes(); uri = json.loads(raw)["$id"]
    asset = SuppliedAsset(asset_id, "application/schema+json", raw, uri)
    return SchemaAssetBinding(_parsed(_ref(asset)), asset)


def _registry() -> ContractSchemaRegistry:
    bindings = []
    for path in sorted((ROOT / "schemas/v2/contract-kernel/common").glob("*/1.0.0.schema.json")):
        bindings.append(_schema_binding(path, f"schema:common:{path.parent.name}:1.0.0"))
    names = {
        "m1-contract-requirement-set": "schema:m1-contract-requirement-set:1.0.0",
        "artifact-family-catalog": "schema:artifact-family-catalog:1.0.0",
        "agentization-profile-release": "schema:agentization-profile-release:1.0.0",
        "stable-code-catalog": "schema:stable-code-catalog:1.0.0",
        "kernel-validation-policy": "schema:kernel-validation-policy:1.0.0",
        "contract-bundle-release": "schema:contract-bundle-release:1.0.0",
        "discovery-obligation-policy": "schema:discovery-obligation-policy:1.0.0",
    }
    for path in sorted((ROOT / "schemas/v2/contract-kernel/contract").glob("*/1.0.0.schema.json")):
        bindings.append(_schema_binding(path, names[path.parent.name]))
    bindings.append(_schema_binding(ROOT / "schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json", "schema:typed-terminal-result:1.0.0"))
    bindings.append(_schema_binding(ROOT / "fixtures/v2-contract-kernel/catalog-profile/1.0.0/synthetic-immutable-record/1.0.0.schema.json", "schema:fixture:checkpoint-c-synthetic-record:1.0.0"))
    result = build_schema_registry(tuple(reversed(bindings)))
    assert type(result) is ContractSchemaRegistry, result
    return result


def _c_helpers():
    spec = importlib.util.spec_from_file_location("_checkpoint_d_c_helpers", ROOT / "tests/unit/contracts/test_catalog_profile_validation.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _roots():
    return (_asset("code-catalog:agtxiv-contract-kernel/1.0.0", "application/json", CATALOG), _asset("validation-policy:checkpoint-d-kernel-candidate/1.0.0", "application/json", POLICY))


def _supports():
    return (_asset("validator:checkpoint-d-code-policy:1.0.0", "text/x-python", VALIDATOR), _asset("vectors:checkpoint-d-code-policy/1.0.0", "application/json", VECTORS))


def _build(catalog=None, policy=None, supports=None):
    roots = _roots(); c = _c_helpers()._build();
    return build_kernel_validation_policy_constraints(_binding(catalog or roots[0]), _binding(policy or roots[1]), c, _supports() if supports is None else supports, _registry())


def _mutated(original: SuppliedAsset, document: dict[str, object]) -> SuppliedAsset:
    raw = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return SuppliedAsset(original.asset_id, original.media_type, raw, original.schema_uri)


def test_final_enum_and_catalog_are_exact_ordered_bijection() -> None:
    document = json.loads(CATALOG.read_bytes()); rows = document["codes"]
    assert len(DiagnosticCode) == 78 and len(rows) == 79
    observed = tuple((row["kind_ordinal"], row["code"], row["meaning"]) for row in rows[:78])
    assert observed == EXPECTED_DIAGNOSTICS
    assert [row["code"] for row in rows[:78]] == [str(code) for code in DiagnosticCode]
    assert rows[-1]["code"] == "AGTXIV.TERMINAL.EXAMPLE"
    assert rows[-1]["code_kind"] == "TERMINAL_REASON" and rows[-1]["kind_ordinal"] == 1
    assert "AGTXIV.TERMINAL.EXAMPLE" not in {str(code) for code in DiagnosticCode}
    assert rows[23]["meaning"] == "Strict parsing succeeded, but the supplied schema is not one top-level JSON object."


def test_valid_catalog_and_policy_build_complete_sealed_constraints() -> None:
    assert validate_stable_code_catalog_intrinsic(_binding(_roots()[0]), _registry()) == ()
    result = _build()
    assert type(result) is KernelValidationPolicyConstraints, result
    assert len(result.validation_diagnostic_codes) == 78
    assert result.terminal_reason_codes == ("AGTXIV.TERMINAL.EXAMPLE",)
    assert result.gate_order[-2:] == ("TERMINAL_C_PUBLIC_INCLUDING_B_INTRINSIC", "TERMINAL_D_REASON_POLICY")
    for forbidden in ("approved", "released", "complete", "covered", "satisfied", "admitted"):
        assert not hasattr(result, forbidden)
    with pytest.raises(AttributeError):
        result.extra = True


@pytest.mark.parametrize("mutation", ["missing", "extra", "reorder", "meaning", "kind", "ordinal", "version", "status", "duplicate"])
def test_catalog_adversarial_rows_call_public_intrinsic(mutation: str) -> None:
    asset = _roots()[0]; document = json.loads(asset.raw_bytes); rows = document["codes"]
    if mutation == "missing": rows.pop(0)
    elif mutation == "extra": rows.append(deepcopy(rows[0]))
    elif mutation == "reorder": rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "meaning": rows[0]["meaning"] += " changed"
    elif mutation == "kind": rows[0]["code_kind"] = "TERMINAL_REASON"
    elif mutation == "ordinal": rows[0]["kind_ordinal"] = 2
    elif mutation == "version": rows[0]["introduced_in_catalog_version"] = "1.0.1"
    elif mutation == "status": rows[0]["status"] = "INACTIVE"
    else: rows[-1]["code"] = rows[0]["code"]
    result = validate_stable_code_catalog_intrinsic(_binding(_mutated(asset, document)), _registry())
    assert result and all(type(item) is Diagnostic for item in result)


@pytest.mark.parametrize("field", list(json.loads(POLICY.read_bytes())["resource_limits"]))
def test_every_policy_resource_literal_is_compiled_and_fail_closed(field: str) -> None:
    asset = _roots()[1]; document = json.loads(asset.raw_bytes); document["resource_limits"][field] += 1
    result = _build(policy=_mutated(asset, document))
    assert type(result) is tuple and result


@pytest.mark.parametrize("role", ["code_catalog_ref", "terminal_schema_ref", "validator_ref", "conformance_vector_ref"])
def test_policy_exact_refs_reject_path_hint_and_same_identity_substitution(role: str) -> None:
    asset = _roots()[1]; document = json.loads(asset.raw_bytes); document[role]["path_hint"] = "display-only.json"
    assert type(_build(policy=_mutated(asset, document))) is tuple
    if role in {"validator_ref", "conformance_vector_ref"}:
        supports = list(_supports()); index = 0 if role == "validator_ref" else 1
        old = supports[index]; supports[index] = SuppliedAsset(old.asset_id, old.media_type, old.raw_bytes + b"x")
        assert type(_build(supports=tuple(supports))) is tuple


@pytest.mark.parametrize("supports", [(), (_supports()[0],), _supports() + (_supports()[0],), tuple(reversed(_supports()))])
def test_support_count_roles_aliases_and_order(supports) -> None:
    result = _build(supports=supports)
    if supports == tuple(reversed(_supports())):
        assert type(result) is KernelValidationPolicyConstraints
    else:
        assert type(result) is tuple and result


def test_emitted_diagnostic_registration_is_bounded_and_rejects_reason_shadow() -> None:
    constraints = _build(); assert type(constraints) is KernelValidationPolicyConstraints
    good = Diagnostic(DiagnosticCode.CODE_POLICY_INVALID, "message is non-normative")
    assert validate_emitted_diagnostic_registration((good,), constraints) == ()
    forged = object.__new__(Diagnostic)
    object.__setattr__(forged, "code", "AGTXIV.TERMINAL.EXAMPLE")
    object.__setattr__(forged, "message", "forged")
    for name, value in (("json_pointer", ""), ("byte_offset", None), ("phase", None), ("subject_identity", None), ("schema_pointer", None), ("details", None)):
        object.__setattr__(forged, name, value)
    result = validate_emitted_diagnostic_registration((forged,), constraints)
    assert {x.code for x in result} == {DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED}
    result = validate_emitted_diagnostic_registration((good,) * 4097, constraints)
    assert result


def test_terminal_composition_accepts_registered_reason_and_rejects_unknown() -> None:
    helpers = _c_helpers(); c = helpers._build(); d = _build(); assert type(d) is KernelValidationPolicyConstraints
    record = helpers._terminal_record(c)
    assert validate_typed_terminal_result_kernel_constraints(record, helpers._registry(), c, d) == ()
    unknown = helpers._terminal_record(c, reason="AGTXIV.TERMINAL.UNKNOWN")
    result = validate_typed_terminal_result_kernel_constraints(unknown, helpers._registry(), c, d)
    assert [x.code for x in result] == [DiagnosticCode.REASON_UNREGISTERED]


def test_terminal_c_failure_hard_stops_d_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    import agtxiv_v2.contracts.code_policy_validation as module
    sentinel = (Diagnostic(DiagnosticCode.CATALOG_UNKNOWN_FAMILY, "C sentinel"),)
    calls = []
    monkeypatch.setattr(module, "validate_typed_terminal_result_catalog_constraints", lambda *args: calls.append(args) or sentinel)
    result = module.validate_typed_terminal_result_kernel_constraints(object(), object(), object(), object())
    assert result is sentinel and len(calls) == 1


def test_public_apis_are_deterministic_and_do_not_consult_ambient_io(monkeypatch: pytest.MonkeyPatch) -> None:
    catalog_binding = _binding(_roots()[0]); registry = _registry()
    expected = validate_stable_code_catalog_intrinsic(catalog_binding, registry)
    def forbidden(*args, **kwargs): raise AssertionError("ambient capability consulted")
    monkeypatch.setattr(Path, "open", forbidden); monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden); monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden); monkeypatch.setattr(time, "time", forbidden)
    monkeypatch.setattr(os, "getenv", forbidden); monkeypatch.setattr(random, "random", forbidden)
    assert validate_stable_code_catalog_intrinsic(catalog_binding, registry) == expected
    assert validate_stable_code_catalog_intrinsic(catalog_binding, registry) == expected


def test_vector_index_is_closed_bounded_and_every_branch_invokes_a_public_api() -> None:
    document = json.loads(VECTORS.read_bytes()); assert len(document["vectors"]) == 11
    constraints = _build(); assert type(constraints) is KernelValidationPolicyConstraints
    helpers = _c_helpers(); c = helpers._build(); registry = _registry()
    for vector in document["vectors"]:
        expected = vector["expected_diagnostic_codes"]
        mutation = vector.get("mutation_id", "")
        if vector["vector_kind"] == "CODE_CATALOG":
            asset = _roots()[0]
            if mutation:
                data = json.loads(asset.raw_bytes)
                if mutation.endswith("meaning-change"): data["codes"][0]["meaning"] += " changed"
                else: data["codes"][0], data["codes"][1] = data["codes"][1], data["codes"][0]
                asset = _mutated(asset, data)
            result = validate_stable_code_catalog_intrinsic(_binding(asset), registry)
        elif vector["vector_kind"] == "POLICY":
            asset = _roots()[1]
            if mutation:
                data = json.loads(asset.raw_bytes)
                if mutation.endswith("resource-limit-plus-one"): data["resource_limits"]["maximum_vectors"] += 1
                else: data["gate_order"][0], data["gate_order"][1] = data["gate_order"][1], data["gate_order"][0]
                asset = _mutated(asset, data)
            result = _build(policy=asset)
        elif vector["vector_kind"] == "DIAGNOSTIC_REGISTRATION":
            emitted = ()
            if mutation.endswith("reason-code-shadow"):
                forged = object.__new__(Diagnostic); object.__setattr__(forged, "code", "AGTXIV.TERMINAL.EXAMPLE"); emitted = (forged,)
            elif mutation.endswith("wrong-type"): emitted = (object(),)
            result = validate_emitted_diagnostic_registration(emitted, constraints)
        else:
            record = helpers._terminal_record(c, reason="AGTXIV.TERMINAL.UNKNOWN" if mutation else "AGTXIV.TERMINAL.EXAMPLE")
            result = validate_typed_terminal_result_kernel_constraints(record, helpers._registry(), c, constraints)
        observed = [] if type(result) is KernelValidationPolicyConstraints else sorted({str(item.code) for item in result})
        assert observed == expected, vector["vector_id"]


def test_non_normative_linkage_is_exact_and_grants_no_authority() -> None:
    linkage = json.loads((ROOT / "fixtures/v2-contract-kernel/code-policy/1.0.0/linkage.non-normative.json").read_bytes())
    assert set(linkage) == {"fixture_purpose", "normative_status", "runtime_authority", "coverage_claim", "requirements_ref", "catalog_ref", "profile_ref", "code_catalog_ref", "validation_policy_ref"}
    assert (linkage["normative_status"], linkage["runtime_authority"], linkage["coverage_claim"]) == ("NON_NORMATIVE", "NONE", "NONE")


def _build_with_vector_document(vector_document: dict[str, object]):
    raw = json.dumps(vector_document, sort_keys=True, separators=(",", ":")).encode()
    vector_asset = SuppliedAsset("vectors:checkpoint-d-code-policy/1.0.0", "application/json", raw)
    policy_asset = _roots()[1]
    policy = json.loads(policy_asset.raw_bytes)
    policy["conformance_vector_ref"] = _ref(vector_asset)
    return _build(policy=_mutated(policy_asset, policy), supports=(_supports()[0], vector_asset))


def test_vector_count_limit_accepts_512_and_rejects_513_through_builder() -> None:
    base = json.loads(VECTORS.read_bytes())
    template = deepcopy(base["vectors"][0])
    vectors = []
    for index in range(512):
        item = deepcopy(template); item["vector_id"] = f"d:catalog-positive-{index:03d}"; vectors.append(item)
    base["vectors"] = vectors
    assert type(_build_with_vector_document(base)) is KernelValidationPolicyConstraints
    base["vectors"].append({**deepcopy(template), "vector_id": "d:catalog-positive-512"})
    result = _build_with_vector_document(base)
    assert type(result) is tuple and {item.code for item in result} == {DiagnosticCode.CODE_POLICY_INVALID}


def test_vector_entry_limit_accepts_2048_and_rejects_2049_through_builder() -> None:
    base = json.loads(VECTORS.read_bytes()); item = deepcopy(base["vectors"][0]); base["vectors"] = [item]
    def size() -> int:
        return len(json.dumps(item, sort_keys=True, separators=(",", ":")).encode())
    item["template_id"] += "x" * (2048 - size())
    assert size() == 2048
    assert type(_build_with_vector_document(base)) is KernelValidationPolicyConstraints
    item["template_id"] += "x"; assert size() == 2049
    result = _build_with_vector_document(base)
    assert type(result) is tuple and {entry.code for entry in result} == {DiagnosticCode.CODE_POLICY_INVALID}


@pytest.mark.parametrize(
    "role,limit,code",
    [
        ("catalog", 401_904, DiagnosticCode.CODE_CATALOG_INVALID),
        ("policy", 27_072, DiagnosticCode.CODE_POLICY_INVALID),
        ("validator", 1_048_576, DiagnosticCode.CODE_POLICY_INVALID),
        ("vectors", 1_064_960, DiagnosticCode.CODE_POLICY_INVALID),
    ],
)
def test_raw_role_limit_plus_one_hard_stops_before_parse(role: str, limit: int, code: DiagnosticCode) -> None:
    if role in {"catalog", "policy"}:
        original = _roots()[0 if role == "catalog" else 1]
        oversized = SuppliedAsset(original.asset_id, original.media_type, b"x" * (limit + 1))
        if role == "catalog":
            result = validate_stable_code_catalog_intrinsic(_binding(oversized), _registry())
        else:
            result = _build(policy=oversized)
    else:
        supports = list(_supports()); index = 0 if role == "validator" else 1
        original = supports[index]; supports[index] = SuppliedAsset(original.asset_id, original.media_type, b"x" * (limit + 1))
        result = _build(supports=tuple(supports))
    assert type(result) is tuple and result[0].code == code

@pytest.mark.parametrize("root_index", [0, 1])
@pytest.mark.parametrize("extra", ["path_hint", "schema_uri", "unexpected"])
def test_d_root_binding_ref_requires_exact_closed_four_field_shape(root_index: int, extra: str) -> None:
    roots = _roots(); bindings = [_binding(roots[0]), _binding(roots[1])]
    ref = _ref(roots[root_index]); ref[extra] = "forbidden"
    bindings[root_index] = RawContractAssetBinding(_parsed(ref), roots[root_index])
    result = build_kernel_validation_policy_constraints(bindings[0], bindings[1], _c_helpers()._build(), _supports(), _registry())
    assert type(result) is tuple
    assert {item.code for item in result} == {DiagnosticCode.CODE_POLICY_REFERENCE_INVALID}


def _instrument_preflight(monkeypatch: pytest.MonkeyPatch):
    import agtxiv_v2.contracts.code_policy_validation as module
    counts = {"support_fields": 0, "materialize": 0, "copy": 0, "hash": 0, "parse": 0, "registry": 0}
    originals = {name: getattr(module, name) for name in ("_support_fields", "_materialize", "_copy_raw", "_raw_hash", "_parse_raw", "_registry_entries")}
    for name, key in (("_support_fields", "support_fields"), ("_materialize", "materialize"), ("_copy_raw", "copy"), ("_raw_hash", "hash"), ("_parse_raw", "parse"), ("_registry_entries", "registry")):
        def counted(*args, _name=name, _key=key, **kwargs):
            counts[_key] += 1
            return originals[_name](*args, **kwargs)
        monkeypatch.setattr(module, name, counted)
    return counts


@pytest.mark.parametrize("failure", ["second-root-type", "second-root-budget", "last-support-type", "last-support-budget"])
def test_complete_preflight_hard_stops_before_first_root_materialization(failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
    roots = _roots(); catalog_binding = _binding(roots[0]); policy_binding = _binding(roots[1]); supports = list(_supports())
    if failure == "second-root-type": policy_binding = object()
    elif failure == "second-root-budget":
        asset = SuppliedAsset(roots[1].asset_id, roots[1].media_type, b"x" * 27_073)
        policy_binding = _binding(asset)
    elif failure == "last-support-type": supports[1] = object()
    else: supports[1] = SuppliedAsset(supports[1].asset_id, supports[1].media_type, b"x" * 1_064_961)
    c = _c_helpers()._build(); registry = _registry(); counts = _instrument_preflight(monkeypatch)
    result = build_kernel_validation_policy_constraints(catalog_binding, policy_binding, c, tuple(supports), registry)
    assert type(result) is tuple and result
    assert counts == {"support_fields": 2 if failure.endswith("budget") else 0, "materialize": 0, "copy": 0, "hash": 0, "parse": 0, "registry": 0}


@pytest.mark.parametrize("seal", ["corrupt", "missing", "forged"])
def test_c_constraint_seal_failure_precedes_d_inputs_registry_and_namespace(seal: str, monkeypatch: pytest.MonkeyPatch) -> None:
    import agtxiv_v2.contracts.code_policy_validation as module
    constraints = _c_helpers()._build()
    name = "_CatalogProfileConstraints__seal"
    if seal == "corrupt":
        object.__setattr__(constraints, name, "sha256:" + "0" * 64)
    elif seal == "missing":
        object.__delattr__(constraints, name)
    else:
        object.__setattr__(constraints, name, object())
    counts = {key: 0 for key in ("root_fields", "support_fields", "registry", "namespace", "snapshot", "materialize", "copy", "hash", "parse")}
    for function, key in (
        ("_root_fields", "root_fields"), ("_support_fields", "support_fields"),
        ("_registry_entries", "registry"), ("_establish_asset_namespace", "namespace"),
        ("_snapshot_preflight", "snapshot"), ("_materialize", "materialize"),
        ("_copy_raw", "copy"), ("_raw_hash", "hash"), ("_parse_raw", "parse"),
    ):
        original = getattr(module, function)
        def counted(*args, _original=original, _key=key, **kwargs):
            counts[_key] += 1
            return _original(*args, **kwargs)
        monkeypatch.setattr(module, function, counted)
    result = build_kernel_validation_policy_constraints(
        _binding(_roots()[0]), _binding(_roots()[1]), constraints, _supports(), _registry(),
    )
    assert type(result) is tuple
    assert [item.code for item in result] == [DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH]
    assert counts == {key: 0 for key in counts}


def test_support_count_hard_stops_before_member_or_later_work(monkeypatch: pytest.MonkeyPatch) -> None:
    import agtxiv_v2.contracts.code_policy_validation as module
    counts = _instrument_preflight(monkeypatch)
    later = {name: 0 for name in ("root_fields", "canonical_integrity", "opaque_fields", "constraints", "namespace", "snapshot")}
    for name, key in (("_root_fields", "root_fields"), ("build_canonical_value", "canonical_integrity"), ("_opaque_ref_fields", "opaque_fields"), ("_constraints_parts", "constraints"), ("_establish_asset_namespace", "namespace"), ("_snapshot_preflight", "snapshot")):
        original = getattr(module, name)
        def counted(*args, _original=original, _key=key, **kwargs):
            later[_key] += 1
            return _original(*args, **kwargs)
        monkeypatch.setattr(module, name, counted)
    result = build_kernel_validation_policy_constraints(
        _binding(_roots()[0]), _binding(_roots()[1]), _c_helpers()._build(),
        (_supports()[0],) * 10_000, _registry(),
    )
    assert type(result) is tuple and result
    assert counts == {"support_fields": 0, "materialize": 0, "copy": 0, "hash": 0, "parse": 0, "registry": 0}
    assert later == {name: 0 for name in later}


def test_public_d_apis_traverse_sealed_registry_once(monkeypatch: pytest.MonkeyPatch) -> None:
    import agtxiv_v2.contracts.code_policy_validation as module
    assert not hasattr(module, "_unsealed_registry_asset_ids")
    original = module._registry_entries
    calls = []
    monkeypatch.setattr(module, "_registry_entries", lambda registry: calls.append(registry) or original(registry))
    registry = _registry()
    result = build_kernel_validation_policy_constraints(_binding(_roots()[0]), _binding(_roots()[1]), _c_helpers()._build(), _supports(), registry)
    assert type(result) is KernelValidationPolicyConstraints and calls == [registry]
    calls.clear()
    assert validate_stable_code_catalog_intrinsic(_binding(_roots()[0]), registry) == ()
    assert calls == [registry]


@pytest.mark.parametrize(
    "collision",
    ["d-root", "d-vs-c", "d-vs-registry", "same-bytes", "different-bytes-media"],
)
def test_complete_asset_id_namespace_rejects_every_alias_class(collision: str) -> None:
    roots = list(_roots()); supports = list(_supports())
    if collision == "d-root": roots[1] = SuppliedAsset(roots[0].asset_id, roots[1].media_type, roots[1].raw_bytes)
    elif collision == "d-vs-c": roots[0] = SuppliedAsset("requirements:m1-contract-requirement-set:1.0.0", roots[0].media_type, roots[0].raw_bytes)
    elif collision == "d-vs-registry": supports[0] = SuppliedAsset("schema:stable-code-catalog:1.0.0", supports[0].media_type, supports[0].raw_bytes)
    elif collision == "same-bytes": supports[1] = SuppliedAsset(supports[0].asset_id, supports[0].media_type, supports[0].raw_bytes)
    else: supports[1] = SuppliedAsset(supports[0].asset_id, supports[1].media_type, b"different")
    result = build_kernel_validation_policy_constraints(_binding(roots[0]), _binding(roots[1]), _c_helpers()._build(), tuple(supports), _registry())
    assert type(result) is tuple
    assert [item.code for item in result] == [DiagnosticCode.CODE_POLICY_REFERENCE_INVALID]


def test_namespace_failure_is_stable_under_support_permutation() -> None:
    roots = _roots(); supports = list(_supports())
    supports[0] = SuppliedAsset(roots[0].asset_id, supports[0].media_type, supports[0].raw_bytes)
    args = (_binding(roots[0]), _binding(roots[1]), _c_helpers()._build())
    forward = build_kernel_validation_policy_constraints(*args, tuple(supports), _registry())
    reverse = build_kernel_validation_policy_constraints(*args, tuple(reversed(supports)), _registry())
    assert forward == reverse


def test_nonempty_policy_findings_are_registered_after_catalog_trust(monkeypatch: pytest.MonkeyPatch) -> None:
    import agtxiv_v2.contracts.code_policy_validation as module
    policy = json.loads(POLICY.read_bytes()); policy["gate_order"][0], policy["gate_order"][1] = policy["gate_order"][1], policy["gate_order"][0]
    calls = []; original = module.validate_emitted_diagnostic_registration
    def monitored(findings, constraints):
        calls.append(findings)
        return original(findings, constraints)
    monkeypatch.setattr(module, "validate_emitted_diagnostic_registration", monitored)
    result = _build(policy=_mutated(_roots()[1], policy))
    assert type(result) is tuple and result
    assert len(calls) == 1 and calls[0]
    assert all(type(item) is Diagnostic for item in calls[0])
    assert result == calls[0]


def test_policy_finding_registration_failure_replaces_findings_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    import agtxiv_v2.contracts.code_policy_validation as module
    policy = json.loads(POLICY.read_bytes()); policy["gate_order"][0], policy["gate_order"][1] = policy["gate_order"][1], policy["gate_order"][0]
    sentinel = (
        Diagnostic(DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED, "z", phase="DIAGNOSTIC_REGISTRATION", json_pointer="/1"),
        Diagnostic(DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED, "a", phase="DIAGNOSTIC_REGISTRATION", json_pointer="/0"),
    )
    monkeypatch.setattr(module, "validate_emitted_diagnostic_registration", lambda findings, constraints: sentinel)
    result = _build(policy=_mutated(_roots()[1], policy))
    assert [item.json_pointer for item in result] == ["/0", "/1"]
    assert {item.code for item in result} == {DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED}


@pytest.mark.parametrize(
    "role,limit",
    [("catalog", 401_904), ("policy", 27_072), ("validator", 1_048_576), ("vectors", 1_064_960)],
)
def test_each_raw_role_exact_limit_reaches_binding_but_plus_one_stops_before_instrumentation(role: str, limit: int, monkeypatch: pytest.MonkeyPatch) -> None:
    import agtxiv_v2.contracts.code_policy_validation as module
    roots = list(_roots()); supports = list(_supports())
    if role in {"catalog", "policy"}:
        index = 0 if role == "catalog" else 1; roots[index] = SuppliedAsset(roots[index].asset_id, roots[index].media_type, b"x" * limit)
    else:
        index = 0 if role == "validator" else 1; supports[index] = SuppliedAsset(supports[index].asset_id, supports[index].media_type, b"x" * limit)
    seen = []; original = module._raw_hash
    monkeypatch.setattr(module, "_raw_hash", lambda raw: seen.append(len(raw)) or original(raw))
    result = build_kernel_validation_policy_constraints(_binding(roots[0]), _binding(roots[1]), _c_helpers()._build(), tuple(supports), _registry())
    assert type(result) is tuple and limit in seen
    seen.clear()
    if role in {"catalog", "policy"}: roots[0 if role == "catalog" else 1] = SuppliedAsset(roots[0 if role == "catalog" else 1].asset_id, "application/json", b"x" * (limit + 1))
    else: supports[0 if role == "validator" else 1] = SuppliedAsset(supports[0 if role == "validator" else 1].asset_id, supports[0 if role == "validator" else 1].media_type, b"x" * (limit + 1))
    result = build_kernel_validation_policy_constraints(_binding(roots[0]), _binding(roots[1]), _c_helpers()._build(), tuple(supports), _registry())
    assert type(result) is tuple and result and seen == []


def test_aggregate_limits_are_exactly_reachable_per_role_sums() -> None:
    limits = json.loads(POLICY.read_bytes())["resource_limits"]
    assert limits["maximum_total_root_bytes"] == limits["maximum_catalog_root_bytes"] + limits["maximum_policy_root_bytes"]
    assert limits["maximum_total_support_bytes"] == limits["maximum_validator_source_bytes"] + limits["maximum_vector_index_bytes"]
    assert limits["maximum_total_d_input_bytes"] == limits["maximum_total_root_bytes"] + limits["maximum_total_support_bytes"]
    roots = (
        SuppliedAsset(_roots()[0].asset_id, "application/json", b"c" * limits["maximum_catalog_root_bytes"]),
        SuppliedAsset(_roots()[1].asset_id, "application/json", b"p" * limits["maximum_policy_root_bytes"]),
    )
    supports = (
        SuppliedAsset(_supports()[0].asset_id, "text/x-python", b"v" * limits["maximum_validator_source_bytes"]),
        SuppliedAsset(_supports()[1].asset_id, "application/json", b"i" * limits["maximum_vector_index_bytes"]),
    )
    result = build_kernel_validation_policy_constraints(_binding(roots[0]), _binding(roots[1]), _c_helpers()._build(), supports, _registry())
    assert type(result) is tuple and result[0].code == DiagnosticCode.INVALID_JSON
