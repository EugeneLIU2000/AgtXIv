"""Pure stable-code and kernel-policy validation for Checkpoint D.

Accepted values prove only candidate structural composition.  They grant no
runtime, release, merge, coverage, satisfaction, review, or admission authority.
All interpreted bytes are explicit caller inputs; exact references are identities,
never filesystem or network locators.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Never

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .canonical import ParsedCanonicalValue, build_canonical_value, canonical_bytes, parse_canonical_json
from .catalog_validation import CatalogProfileConstraints, RawContractAssetBinding, _asset_projection, _constraints_parts, validate_typed_terminal_result_catalog_constraints
from .diagnostics import Diagnostic, DiagnosticCode
from .references import SuppliedAsset, raw_asset_sha256
from .registry import ContractSchemaRegistry, DRAFT_2020_12, _diagnostic, _path_pointer, _registry_entries, _sort_diagnostics, _thaw_json
from .schema_validation import _FIXED_FORMAT_CHECKER, _validation_schema_snapshot

_OFFICIAL_SCHEMA_REFS = MappingProxyType({'catalog': {'asset_id': 'schema:stable-code-catalog:1.0.0', 'media_type': 'application/schema+json', 'byte_size': 4899, 'sha256': 'sha256:ced539ac5326b14a0e00acfcff35442960347563ed10d9dcb185947b5e085d70', 'schema_uri': 'https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.0.0'}, 'policy': {'asset_id': 'schema:kernel-validation-policy:1.0.0', 'media_type': 'application/schema+json', 'byte_size': 10329, 'sha256': 'sha256:ab7963b01ac0a4a00b7c9e2851199dc7b38bddeddb96f629b6f20d41d09647aa', 'schema_uri': 'https://agtxiv.org/schema/v2/contract-kernel/contract/kernel-validation-policy/1.0.0'}})
_CATALOG_LIMITS = MappingProxyType({"exact_code_entries":79,"maximum_code_utf8_bytes":256,"maximum_meaning_utf8_bytes":4096,"maximum_code_entry_bytes":4880,"maximum_root_metadata_bytes":16384,"maximum_catalog_root_bytes":401904})
_POLICY_LIMITS = MappingProxyType({"exact_policy_roots":2,"exact_support_assets":2,"maximum_catalog_root_bytes":401904,"maximum_exact_ref_bytes":2048,"maximum_policy_root_bytes":27072,"maximum_total_root_bytes":428976,"maximum_validator_source_bytes":1048576,"maximum_vectors":512,"maximum_vector_entry_bytes":2048,"maximum_vector_index_bytes":1064960,"maximum_total_support_bytes":2113536,"maximum_total_d_input_bytes":2542512,"exact_code_entries":79,"exact_reason_registrations":1,"exact_targets_per_registration":1,"exact_total_reason_targets":1,"maximum_emitted_diagnostics":4096})
_STABLE_DIAGNOSTICS = (('AGTXIV.CANON.BOM_FORBIDDEN', 'Input begins with a forbidden UTF-8 byte-order mark.'), ('AGTXIV.CANON.INVALID_UTF8', 'Input bytes are not valid strict UTF-8.'), ('AGTXIV.CANON.INVALID_JSON', 'UTF-8 input is not one complete syntactically valid JSON value.'), ('AGTXIV.CANON.DUPLICATE_KEY', 'A JSON object contains the same member name more than once before normalization.'), ('AGTXIV.CANON.NORMALIZED_KEY_COLLISION', 'Distinct object member names collide after required Unicode normalization.'), ('AGTXIV.CANON.UNPAIRED_SURROGATE', 'A string contains an unpaired Unicode surrogate code point.'), ('AGTXIV.CANON.UNSUPPORTED_NUMBER', 'A JSON number uses a numeric form outside the canonical profile.'), ('AGTXIV.CANON.INTEGER_OUT_OF_RANGE', 'An integer lies outside the permitted I-JSON exact-integer range.'), ('AGTXIV.CANON.NESTING_TOO_DEEP', 'A submitted value exceeds the canonical maximum nesting depth.'), ('AGTXIV.CANON.UNSUPPORTED_PROGRAMMATIC_TYPE', 'A programmatic input contains a value whose exact Python type is outside the canonical JSON model.'), ('AGTXIV.CANON.NON_STRING_OBJECT_KEY', 'A programmatic object has a member key whose exact type is not string.'), ('AGTXIV.CANON.CYCLIC_PROGRAMMATIC_VALUE', 'A programmatic array or object contains an identity cycle.'), ('AGTXIV.CANON.INVALID_RECORD_SHAPE', 'A value submitted for record hashing lacks the exact required record projection shape.'), ('AGTXIV.CANON.INVALID_INTERNAL_VALUE', 'An opaque canonical value fails its internal integrity invariant.'), ('AGTXIV.REF.UNRESOLVED', 'An exact asset, record, or component reference has no uniquely supplied target.'), ('AGTXIV.REF.HASH_MISMATCH', 'Supplied target bytes, byte size, or canonical content hash differ from the exact reference.'), ('AGTXIV.REF.TYPE_MISMATCH', 'A resolved target has the wrong declared media, schema, record, or component type for the reference.'), ('AGTXIV.CONTRACT.MUTABLE_REF', 'A contract-bound authoritative reference contains mutable or non-exact identity.'), ('AGTXIV.RECORD.INVALID_ENVELOPE', 'An immutable record envelope is absent, open, malformed, or inconsistent with its required closed shape.'), ('AGTXIV.RECORD.SUPERSESSION_MISMATCH', 'A record revision or supersession relation is inconsistent with immutable revision rules.'), ('AGTXIV.RECORD.HASH_MISMATCH', "A record's declared content hash differs from its canonical record-hash projection."), ('AGTXIV.SCHEMA.EMPTY_REGISTRY', 'Schema-registry construction received no schema bindings.'), ('AGTXIV.SCHEMA.INPUT_TYPE_MISMATCH', 'A schema or validator API received an input with an invalid exact type or failed opaque/sealed integrity.'), ('AGTXIV.SCHEMA.INVALID_DOCUMENT', 'Strict parsing succeeded, but the supplied schema is not one top-level JSON object.'), ('AGTXIV.SCHEMA.DIALECT_MISMATCH', 'A schema does not declare the required JSON Schema Draft 2020-12 dialect.'), ('AGTXIV.SCHEMA.ID_MISMATCH', "A schema's `$id`, schema URI, or exact binding identities disagree."), ('AGTXIV.SCHEMA.DUPLICATE_ID', 'More than one supplied schema claims the same authoritative schema identity.'), ('AGTXIV.SCHEMA.META_INVALID', "A schema fails the supported dialect's meta-schema or closed-keyword constraints."), ('AGTXIV.SCHEMA.UNRESOLVED_REF', 'A schema `$ref` does not resolve inside the explicit offline registry.'), ('AGTXIV.SCHEMA.REFERENCE_CYCLE', 'The admitted schema-reference graph contains a forbidden cycle.'), ('AGTXIV.SCHEMA.REMOTE_REF_FORBIDDEN', 'A schema reference would require remote or non-registry resolution.'), ('AGTXIV.RECORD.TYPE_SCHEMA_MISMATCH', "A record's declared record type differs from the exact family schema's record-type declaration."), ('AGTXIV.RECORD.PAYLOAD_INVALID', 'A record payload violates its exact family schema.'), ('AGTXIV.TERMINAL.SCHEMA_MISMATCH', 'A typed terminal record does not bind the compiled official terminal schema bytes.'), ('AGTXIV.TERMINAL.ATTEMPT_MISMATCH', 'Terminal payload attempt identity or producer context is absent or differs from the envelope attempt.'), ('AGTXIV.TERMINAL.CONTEXT_INVALID', 'A terminal binding context and its target basis have an intrinsically inconsistent shape or identity.'), ('AGTXIV.TERMINAL.TARGET_INVALID', 'A terminal target is intrinsically recursive or otherwise forbidden as a terminal obligation target.'), ('AGTXIV.TERMINAL.EVIDENCE_INVALID', 'Terminal evidence has duplicate IDs/references, noncanonical order, or a forbidden terminal/self reference.'), ('AGTXIV.TERMINAL.DISPOSITION_INVALID', 'Terminal outcome, retry disposition, or next action violates the intrinsic compatibility matrix.'), ('AGTXIV.TERMINAL.RESOURCE_INVALID', 'Declared resource dimensions, ordering, partition, or observed-limit relation is mechanically inconsistent.'), ('AGTXIV.CONTRACT.ASSET_SCHEMA_MISMATCH', "A raw contract document's official schema ref or registry schema bytes differ from the compiled ruler."), ('AGTXIV.CONTRACT.ASSET_INVALID', 'A correctly bound raw contract document is noncanonical or violates its exact official schema.'), ('AGTXIV.REQUIREMENTS.SOURCE_BINDING_MISMATCH', 'Requirement-set roadmap bytes, Git blob identity, bounded section, or exact source ref differs from the frozen source.'), ('AGTXIV.REQUIREMENTS.ITEM_SET_MISMATCH', 'Requirement item membership or uniqueness differs from the compiled 52-item floor.'), ('AGTXIV.REQUIREMENTS.ITEM_ORDER_MISMATCH', 'Requirement item order, kind, or source occurrence differs from the compiled floor.'), ('AGTXIV.REQUIREMENTS.MAPPING_MISMATCH', 'Selected roadmap rows or their reviewed requirement expansion differs from the frozen mapping.'), ('AGTXIV.REQUIREMENTS.SELECTION_RULE_MISMATCH', 'Requirement milestone selection differs from the exact M1-token rule.'), ('AGTXIV.CATALOG.REFERENCE_INVALID', 'A Catalog/Profile root or support reference is unresolved, aliased, excessive, or invalid for its declared graph role.'), ('AGTXIV.CATALOG.EXACT_REF_CYCLE', 'The recognized Catalog/Profile exact-reference graph contains a root alias or cycle.'), ('AGTXIV.CATALOG.DUPLICATE_FAMILY', 'Catalog family identity is duplicated under the v1 global-family rule.'), ('AGTXIV.CATALOG.DUPLICATE_STAGE', 'Catalog stage identity is duplicated.'), ('AGTXIV.CATALOG.STRUCTURE_INVALID', 'Catalog ordering, uniqueness, applicability, cardinality, vector, or stage-coverage structure is invalid.'), ('AGTXIV.CATALOG.FAMILY_BINDING_INVALID', 'A family successful-artifact kind, schema, or record-type binding is inconsistent.'), ('AGTXIV.CATALOG.SUPPORT_ASSET_ROLE_INVALID', 'Catalog validator or vector bytes do not resolve in the exact declared support role or target partition.'), ('AGTXIV.CATALOG.TERMINAL_POLICY_INVALID', 'Catalog terminal recursion, outcome order, context minimum, or accounting-unit terminal policy is invalid.'), ('AGTXIV.PROFILE.CATALOG_MISMATCH', 'A Profile does not exact-bind the supplied Catalog bytes.'), ('AGTXIV.PROFILE.FAMILY_SET_INVALID', 'Profile stage or family-stage keys do not exactly mirror Catalog membership and order.'), ('AGTXIV.PROFILE.REQUIREMENT_WEAKENING', 'A Profile weakens or deselects a Catalog core requirement.'), ('AGTXIV.PROFILE.CARDINALITY_WEAKENING', 'Profile cardinality weakens Catalog bounds or contradicts its selected adjustment.'), ('AGTXIV.PROFILE.PRODUCER_EXPANSION', 'Profile producer roles are reordered or expand beyond the Catalog role set.'), ('AGTXIV.PROFILE.TERMINAL_POLICY_MISMATCH', 'Profile terminal-permission mode differs from the Catalog mode.'), ('AGTXIV.PROFILE.OUTCOME_EXPANSION', 'Profile terminal outcomes are reordered or expand beyond Catalog outcomes.'), ('AGTXIV.PROFILE.CONTEXT_WEAKENING', 'Profile stage or family terminal context is weaker than the effective Catalog minimum.'), ('AGTXIV.CATALOG.CONTEXT_BINDING_MISMATCH', "A terminal context's exact Catalog/Profile refs differ from the sealed C constraints."), ('AGTXIV.CATALOG.UNKNOWN_FAMILY', 'A terminal target family is absent from the exact Catalog constraints.'), ('AGTXIV.CATALOG.UNKNOWN_STAGE', 'A terminal target stage is absent for the resolved Catalog family.'), ('AGTXIV.CATALOG.OBLIGATION_NOT_SELECTED', 'A terminal record targets a Profile branch explicitly marked `NOT_SELECTED`.'), ('AGTXIV.CATALOG.TERMINAL_NOT_ALLOWED', 'Effective Catalog/Profile policy forbids a terminal card for the target.'), ('AGTXIV.CATALOG.PRODUCER_ROLE_NOT_ALLOWED', 'Terminal producer role is outside the effective Profile role subset.'), ('AGTXIV.CATALOG.CONTEXT_MODE_INSUFFICIENT', 'Terminal context mode is weaker than the effective Profile minimum.'), ('AGTXIV.CATALOG.OUTCOME_NOT_ALLOWED', 'Terminal outcome is outside the effective Profile outcome subset.'), ('AGTXIV.CODE.CATALOG_INVALID', 'A correctly bound genesis stable-code document violates code identity, kind, order, exact version, stable meaning, or declared resource rules.'), ('AGTXIV.CODE.ENUM_PROJECTION_MISMATCH', 'The catalog `VALIDATION_DIAGNOSTIC` projection and final compiled `DiagnosticCode` enum are not equal in membership, ordinal, and declaration order.'), ('AGTXIV.CODE.POLICY_REFERENCE_INVALID', 'A policy exact reference, official schema pin, validator/vector binding, or sealed C-constraint root differs from the supplied fixed bytes.'), ('AGTXIV.CODE.POLICY_INVALID', 'A correctly bound genesis policy violates its closed gate, registration, canonical order, exact target, or declared resource rules.'), ('AGTXIV.CODE.EMITTED_DIAGNOSTIC_UNREGISTERED', "An emitted diagnostic is absent from the trusted catalog's `VALIDATION_DIAGNOSTIC` projection."), ('AGTXIV.REASON.UNREGISTERED', 'An intrinsically and structurally valid terminal record declares a code that is absent, not an active `TERMINAL_REASON`, or not registered by the exact policy.'), ('AGTXIV.REASON.CONSTRAINT_MISMATCH', 'A registered terminal reason is used outside its policy outcome, retry, context, or exact family-version-stage constraints.'))
_REASON_CODE = "AGTXIV.TERMINAL.EXAMPLE"
_REASON_MEANING = "a synthetic terminal reason used only to demonstrate contract-kernel registration and composition; it makes no domain, production, satisfaction, review, or release claim."
_GATE_ORDER = ("CODE_CATALOG_INTRINSIC","PYTHON_DIAGNOSTIC_BIJECTION","POLICY_INTRINSIC_AND_EXACT_BINDING","EMITTED_DIAGNOSTIC_REGISTRATION","TERMINAL_C_PUBLIC_INCLUDING_B_INTRINSIC","TERMINAL_D_REASON_POLICY")
_ENTRY_POINTS = MappingProxyType({"catalog_intrinsic":"agtxiv_v2.contracts.code_policy_validation.validate_stable_code_catalog_intrinsic","policy_builder":"agtxiv_v2.contracts.code_policy_validation.build_kernel_validation_policy_constraints","diagnostic_registration":"agtxiv_v2.contracts.code_policy_validation.validate_emitted_diagnostic_registration","terminal_composition":"agtxiv_v2.contracts.code_policy_validation.validate_typed_terminal_result_kernel_constraints"})
_OUTCOME_ORDER=("UNAVAILABLE","RETRY_REQUIRED","REVIEW_REQUIRED","BLOCKED","FAILED")
_RETRY_ORDER=("RETRY_AFTER_CONDITION","NO_RETRY_IN_CURRENT_CONTEXT","REVIEW_DECIDES")
_CONTEXT_ORDER=("PROFILE_BOUND","PLAN_BOUND","FROZEN_SCOPE_BOUND")
_CODE_PATTERN=re.compile(r"^AGTXIV\.[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+$")
_TOKEN=object()

@dataclass(frozen=True,slots=True)
class _Registration:
    reason_code:str
    outcomes:tuple[str,...]
    retries:tuple[str,...]
    contexts:tuple[str,...]
    targets:tuple[tuple[str,str,str],...]

class KernelValidationPolicyConstraints:
    """Detached recursively immutable non-authority composition snapshot."""
    __slots__=("__refs","__diagnostics","__reasons","__gate_order","__registrations","__seal","__token")
    def __init__(self,refs,diagnostics,reasons,gate_order,registrations,*,_token=None):
        if _token is not _TOKEN:raise TypeError("KernelValidationPolicyConstraints is created only by the policy builder")
        values=(refs,diagnostics,reasons,gate_order,registrations)
        object.__setattr__(self,"_KernelValidationPolicyConstraints__refs",refs);object.__setattr__(self,"_KernelValidationPolicyConstraints__diagnostics",diagnostics);object.__setattr__(self,"_KernelValidationPolicyConstraints__reasons",reasons);object.__setattr__(self,"_KernelValidationPolicyConstraints__gate_order",gate_order);object.__setattr__(self,"_KernelValidationPolicyConstraints__registrations",registrations);object.__setattr__(self,"_KernelValidationPolicyConstraints__seal",_seal(values));object.__setattr__(self,"_KernelValidationPolicyConstraints__token",_TOKEN)
    def __setattr__(self,n,v)->Never:raise AttributeError("KernelValidationPolicyConstraints is immutable")
    def __delattr__(self,n)->Never:raise AttributeError("KernelValidationPolicyConstraints is immutable")
    def _ref(self,n):p=_parts(self);_require(p);return p[0][n]
    @property
    def code_catalog_ref(self):return self._ref("code_catalog")
    @property
    def policy_ref(self):return self._ref("policy")
    @property
    def requirements_ref(self):return self._ref("requirements")
    @property
    def catalog_ref(self):return self._ref("catalog")
    @property
    def profile_ref(self):return self._ref("profile")
    @property
    def terminal_schema_ref(self):return self._ref("terminal_schema")
    @property
    def validation_diagnostic_codes(self):p=_parts(self);_require(p);return p[1]
    @property
    def terminal_reason_codes(self):p=_parts(self);_require(p);return p[2]
    @property
    def gate_order(self):p=_parts(self);_require(p);return p[3]
    def __repr__(self):return "KernelValidationPolicyConstraints(<sealed candidate constraints>)"

def _seal(values):
    h=hashlib.sha256()
    refs,diagnostics,reasons,gates,registrations=values
    for k in sorted(refs):
        b=canonical_bytes(refs[k]);h.update(len(b).to_bytes(8,"big"));h.update(b)
    for s in (*diagnostics,*reasons,*gates):b=s.encode();h.update(len(b).to_bytes(8,"big"));h.update(b)
    for r in registrations:
        for s in (r.reason_code,*r.outcomes,*r.retries,*r.contexts,*(x for t in r.targets for x in t)):b=s.encode();h.update(len(b).to_bytes(8,"big"));h.update(b)
    return "sha256:"+h.hexdigest()

def _parts(value):
    if type(value) is not KernelValidationPolicyConstraints:return None
    try:p=(object.__getattribute__(value,"_KernelValidationPolicyConstraints__refs"),object.__getattribute__(value,"_KernelValidationPolicyConstraints__diagnostics"),object.__getattribute__(value,"_KernelValidationPolicyConstraints__reasons"),object.__getattribute__(value,"_KernelValidationPolicyConstraints__gate_order"),object.__getattribute__(value,"_KernelValidationPolicyConstraints__registrations"));seal=object.__getattribute__(value,"_KernelValidationPolicyConstraints__seal");token=object.__getattribute__(value,"_KernelValidationPolicyConstraints__token")
    except Exception:return None
    if token is not _TOKEN or type(p[0]) is not MappingProxyType or any(type(x) is not ParsedCanonicalValue for x in p[0].values()) or any(type(x) is not tuple for x in p[1:]) or any(type(x) is not str for seq in p[1:4] for x in seq) or any(type(x) is not _Registration for x in p[4]):return None
    try:return p if type(seal) is str and seal==_seal(p) else None
    except Exception:return None

def _require(parts):
    if parts is None:raise ValueError("KernelValidationPolicyConstraints failed its integrity check")
def _diag(code,message,phase,pointer="",subject=None):return _diagnostic(code,message,pointer=pointer,phase=phase,subject=subject)
def _parsed(value):
    x=build_canonical_value(value);return x if type(x) is ParsedCanonicalValue else None
def _ref_dict(asset):
    d={"asset_id":asset.asset_id,"media_type":asset.media_type,"byte_size":len(asset.raw_bytes),"sha256":raw_asset_sha256(asset.raw_bytes)}
    if asset.schema_uri is not None:d["schema_uri"]=asset.schema_uri
    return d
def _same_ref(a,b):return _asset_projection(a)==_asset_projection(b)
def _canonical_ref(ref):
    x=_parsed(ref);return canonical_bytes(x) if x is not None else None

def _opaque_ref_fields(value):
    """Inspect a validated opaque ref without materializing a Python object."""
    try:
        node=object.__getattribute__(value,"_ParsedCanonicalValue__node")
        pairs=object.__getattribute__(node,"pairs")
    except Exception:return None
    if type(pairs) is not tuple:return None
    result={}
    for pair in pairs:
        if type(pair) is not tuple or len(pair)!=2 or type(pair[0]) is not str:return None
        if type(pair[1]) not in (str,int):return None
        result[pair[0]]=pair[1]
    return result

def _copy_raw(raw):return bytes(raw)
def _raw_hash(raw):return raw_asset_sha256(raw)
def _parse_raw(raw):return parse_canonical_json(raw)
def _materialize(value):return value.to_python()

def _root_fields(binding,phase):
    try:r=object.__getattribute__(binding,"exact_ref");a=object.__getattribute__(binding,"supplied_asset")
    except Exception:return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root binding is incomplete",phase),)
    if type(r) is not ParsedCanonicalValue or type(a) is not SuppliedAsset:return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root fields require exact opaque types",phase),)
    try:aid=object.__getattribute__(a,"asset_id");media=object.__getattribute__(a,"media_type");raw=object.__getattribute__(a,"raw_bytes");uri=object.__getattribute__(a,"schema_uri")
    except Exception:return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root asset is forged",phase),)
    if type(aid) is not str or type(media) is not str or type(raw) is not bytes or (uri is not None and type(uri) is not str):return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root metadata has wrong exact type",phase),)
    return (r,aid,media,raw,uri),()

def _support_fields(asset):
    try:row=(object.__getattribute__(asset,"asset_id"),object.__getattribute__(asset,"media_type"),object.__getattribute__(asset,"raw_bytes"),object.__getattribute__(asset,"schema_uri"))
    except Exception:return None
    return row if type(row[0]) is str and type(row[1]) is str and type(row[2]) is bytes and (row[3] is None or type(row[3]) is str) else None

def _preflight_d_inputs(code_catalog_binding,policy_binding,catalog_profile_constraints,support_assets,registry):
    # Pass one: inspect every outer/member exact type and opaque ref integrity.
    # It deliberately performs no raw length, copy, digest, parse, or registry traversal.
    if type(code_catalog_binding) is not RawContractAssetBinding or type(policy_binding) is not RawContractAssetBinding or type(catalog_profile_constraints) is not CatalogProfileConstraints or type(support_assets) is not tuple or type(registry) is not ContractSchemaRegistry:
        return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"builder requires exact immutable D, C, support, and registry types","CODE_POLICY_INPUT"),)
    if len(support_assets)!=2:return None,(_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"policy requires exactly two support assets","CODE_POLICY_INPUT"),)
    cparts=_constraints_parts(catalog_profile_constraints)
    if cparts is None:return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"C constraints failed seal integrity","CODE_POLICY_INPUT"),)
    if any(type(x) is not SuppliedAsset for x in support_assets):return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"support member requires exact SuppliedAsset type","CODE_POLICY_INPUT"),)
    cs,ds=_root_fields(code_catalog_binding,"CODE_CATALOG_INPUT")
    if ds:return None,ds
    ps,ds=_root_fields(policy_binding,"CODE_POLICY_INPUT")
    if ds:return None,ds
    supports=tuple(_support_fields(x) for x in support_assets)
    if any(x is None for x in supports):return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"support metadata has wrong exact type","CODE_POLICY_INPUT"),)
    try:
        for ref in (cs[0],ps[0]):build_canonical_value(ref)
    except Exception:return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"an opaque exact ref failed integrity","CODE_POLICY_INPUT"),)

    # Pass two: only raw lengths, role constraints, aggregate arithmetic, and
    # the closed root-ref shape are observed.
    roles=[x[1] for x in supports]
    if sorted(roles)!=["application/json","text/x-python"]:return None,(_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"supports require exactly one validator and one vector role","CODE_POLICY_INPUT"),)
    c_ref=_opaque_ref_fields(cs[0]);p_ref=_opaque_ref_fields(ps[0]);required={"asset_id","media_type","byte_size","sha256"}
    if any(type(ref) is not dict or set(ref)!=required for ref in (c_ref,p_ref)):
        return None,(_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"D root binding refs require the exact closed four-field shape","CODE_POLICY_INPUT"),)
    c_size=len(cs[3]);p_size=len(ps[3]);sizes={media:len(raw) for _,media,raw,_ in supports}
    if c_size>_POLICY_LIMITS["maximum_catalog_root_bytes"]:return None,(_diag(DiagnosticCode.CODE_CATALOG_INVALID,"catalog root exceeds its declared byte limit","CODE_CATALOG_INPUT"),)
    if p_size>_POLICY_LIMITS["maximum_policy_root_bytes"]:return None,(_diag(DiagnosticCode.CODE_POLICY_INVALID,"policy root exceeds its declared byte limit","CODE_POLICY_INPUT"),)
    if sizes["text/x-python"]>_POLICY_LIMITS["maximum_validator_source_bytes"] or sizes["application/json"]>_POLICY_LIMITS["maximum_vector_index_bytes"]:return None,(_diag(DiagnosticCode.CODE_POLICY_INVALID,"support exceeds its per-role byte limit","CODE_POLICY_INPUT"),)
    if c_size!=c_ref["byte_size"] or p_size!=p_ref["byte_size"]:return None,(_diag(DiagnosticCode.REF_HASH_MISMATCH,"root size differs from exact reference","CODE_POLICY_INPUT"),)
    support_total=sum(sizes.values());root_total=c_size+p_size
    if support_total>_POLICY_LIMITS["maximum_total_support_bytes"] or root_total>_POLICY_LIMITS["maximum_total_root_bytes"] or root_total+support_total>_POLICY_LIMITS["maximum_total_d_input_bytes"]:return None,(_diag(DiagnosticCode.CODE_POLICY_INVALID,"D-controlled inputs exceed aggregate byte limits","CODE_POLICY_INPUT"),)
    return (cs,ps,supports,cparts,c_ref,p_ref),()

def _establish_asset_namespace(preflight,entries):
    cs,ps,supports,cparts,c_ref,p_ref=preflight
    c_refs=cparts[:3]
    c_ids=[]
    for ref in c_refs:
        fields=_opaque_ref_fields(ref)
        if type(fields) is not dict or type(fields.get("asset_id")) is not str:return None
        c_ids.append(fields["asset_id"])
    identities=(c_ref["asset_id"],p_ref["asset_id"],*(x[0] for x in supports),*c_ids,*(entry.asset_id for entry in entries))
    return identities if len(identities)==len(set(identities)) else ()

def _snapshot_preflight(preflight):
    cs,ps,supports,_,_,_=preflight
    roots=[]
    for ref,aid,media,raw,uri in (cs,ps):roots.append((_materialize(ref),aid,media,_copy_raw(raw),uri))
    return roots[0],roots[1],tuple((aid,media,_copy_raw(raw),uri) for aid,media,raw,uri in supports)

def _schema_entry(entries,index,expected):
    e=index.get(expected["asset_id"])
    if e is None or len(index)!=len(entries):return None
    observed={"asset_id":e.asset_id,"media_type":e.media_type,"byte_size":e.byte_size,"sha256":e.sha256,"schema_uri":e.schema_id}
    return e if observed==expected else None

def _bound_root(snapshot,entries,index,schema_key,phase):
    ref,aid,media,raw,uri=snapshot
    if _asset_projection(ref)!={"asset_id":aid,"media_type":media,"byte_size":len(raw),"sha256":_raw_hash(raw),**({"schema_uri":uri} if "schema_uri" in ref else {})}:return None,(_diag(DiagnosticCode.REF_HASH_MISMATCH,"root differs from exact reference",phase,subject=aid),)
    parsed=_parse_raw(raw)
    if type(parsed) is Diagnostic:return None,(parsed,)
    if canonical_bytes(parsed)!=raw:return None,(_diag(DiagnosticCode.ASSET_INVALID,"root is not canonical JSON",phase,subject=aid),)
    doc=_materialize(parsed);expected=dict(_OFFICIAL_SCHEMA_REFS[schema_key]);entry=_schema_entry(entries,index,expected)
    if type(doc) is not dict:return None,(_diag(DiagnosticCode.ASSET_INVALID,"root must be an object",phase,subject=aid),)
    if _asset_projection(doc.get("document_schema_ref"))!=expected or entry is None:return None,(_diag(DiagnosticCode.ASSET_SCHEMA_MISMATCH,"root or registry differs from official schema bytes",phase,pointer="/document_schema_ref",subject=aid),)
    try:
        schema=_validation_schema_snapshot(_thaw_json(entry.document),entry.schema_id,{})
        validator=Draft202012Validator(schema,registry=Registry().with_resource(entry.schema_id,Resource.from_contents(schema)),format_checker=_FIXED_FORMAT_CHECKER)
        errors=list(validator.iter_errors(doc))
    except Exception:return None,(_diag(DiagnosticCode.ASSET_INVALID,"official schema evaluation failed",phase,subject=aid),)
    if errors:return None,_sort_diagnostics([_diag(DiagnosticCode.ASSET_INVALID,"root violates official schema",phase,_path_pointer(e.absolute_path),aid) for e in errors])
    return (parsed,doc),()

def _catalog_findings(doc):
    findings=[];codes=doc.get("codes",[])
    if doc.get("resource_limits")!=dict(_CATALOG_LIMITS):findings.append(_diag(DiagnosticCode.CODE_CATALOG_INVALID,"catalog resource limits differ from compiled map","CODE_CATALOG_INTRINSIC",pointer="/resource_limits"))
    expected=[{"code":c,"code_kind":"VALIDATION_DIAGNOSTIC","kind_ordinal":i,"meaning":m,"introduced_in_catalog_version":"1.0.0","status":"ACTIVE"} for i,(c,m) in enumerate(_STABLE_DIAGNOSTICS,1)]
    expected.append({"code":_REASON_CODE,"code_kind":"TERMINAL_REASON","kind_ordinal":1,"meaning":_REASON_MEANING,"introduced_in_catalog_version":"1.0.0","status":"ACTIVE"})
    if codes!=expected:findings.append(_diag(DiagnosticCode.CODE_CATALOG_INVALID,"catalog rows differ in code, kind, ordinal, meaning, version, status, or order","CODE_CATALOG_INTRINSIC",pointer="/codes"))
    for i,row in enumerate(codes if type(codes) is list else []):
        if type(row) is not dict:continue
        c=row.get("code");m=row.get("meaning")
        if type(c) is not str or len(c.encode("utf-8"))>256 or _CODE_PATTERN.fullmatch(c) is None:findings.append(_diag(DiagnosticCode.CODE_CATALOG_INVALID,"code grammar or byte limit is invalid","CODE_CATALOG_INTRINSIC",f"/codes/{i}/code"))
        if type(m) is not str or m!=unicodedata.normalize("NFC",m) or not m.strip() or len(m.encode("utf-8"))>4096:findings.append(_diag(DiagnosticCode.CODE_CATALOG_INVALID,"meaning is blank, non-NFC, or oversized","CODE_CATALOG_INTRINSIC",f"/codes/{i}/meaning"))
        p=_parsed(row)
        if p is None or len(canonical_bytes(p))>4880:findings.append(_diag(DiagnosticCode.CODE_CATALOG_INVALID,"code entry exceeds its canonical byte limit","CODE_CATALOG_INTRINSIC",f"/codes/{i}"))
    projected=[x.get("code") for x in codes if type(x) is dict and x.get("code_kind")=="VALIDATION_DIAGNOSTIC"]
    if projected!=[str(x) for x in DiagnosticCode]:findings.append(_diag(DiagnosticCode.CODE_ENUM_PROJECTION_MISMATCH,"catalog diagnostic projection differs from Python enum order","CODE_CATALOG_ENUM"))
    return _sort_diagnostics(findings)

def validate_stable_code_catalog_intrinsic(catalog_binding,registry):
    try:
        if type(catalog_binding) is not RawContractAssetBinding or type(registry) is not ContractSchemaRegistry:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"catalog and registry require exact types","CODE_CATALOG_INPUT"),)
        fields,ds=_root_fields(catalog_binding,"CODE_CATALOG_INPUT")
        if ds:return ds
        build_canonical_value(fields[0]);ref=_opaque_ref_fields(fields[0])
        if type(ref) is not dict or set(ref)!={"asset_id","media_type","byte_size","sha256"}:return (_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"catalog root ref requires the exact closed four-field shape","CODE_CATALOG_INPUT"),)
        if len(fields[3])>_CATALOG_LIMITS["maximum_catalog_root_bytes"]:return (_diag(DiagnosticCode.CODE_CATALOG_INVALID,"root exceeds its declared byte limit","CODE_CATALOG_INPUT"),)
        if len(fields[3])!=ref["byte_size"]:return (_diag(DiagnosticCode.REF_HASH_MISMATCH,"root size differs from exact reference","CODE_CATALOG_INPUT"),)
        entries=_registry_entries(registry)
        if entries is None:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"registry failed exact type or seal integrity","CODE_CATALOG_INPUT"),)
        index={entry.asset_id:entry for entry in entries}
        if ref["asset_id"] in index:return (_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"catalog root and registry share an asset ID","CODE_CATALOG_BINDING"),)
        snapshot=(_materialize(fields[0]),fields[1],fields[2],_copy_raw(fields[3]),fields[4])
        bound,ds=_bound_root(snapshot,entries,index,"catalog","CODE_CATALOG_SCHEMA")
        if ds:return ds
        return _catalog_findings(bound[1])
    except Exception:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"catalog validation could not safely inspect inputs","CODE_CATALOG_INPUT"),)

def _vector_index(raw):
    p=_parse_raw(raw)
    if type(p) is Diagnostic or canonical_bytes(p)!=raw:return None
    d=_materialize(p)
    if type(d) is not dict or set(d)!={"vector_set_id","vector_set_version","fixture_purpose","vectors"} or d.get("vector_set_id")!="vectors:checkpoint-d-code-policy/1.0.0" or d.get("vector_set_version")!="1.0.0" or d.get("fixture_purpose")!="CONTRACT_KERNEL_CODE_POLICY_TEST_ONLY":return None
    vectors=d.get("vectors")
    if type(vectors) is not list or not 1<=len(vectors)<=_POLICY_LIMITS["maximum_vectors"]:return None
    seen=set();allowed={str(x) for x in DiagnosticCode}
    for x in vectors:
        if type(x) is not dict:return None
        required={"vector_id","polarity","vector_kind","template_id","expected_diagnostic_codes"}
        if x.get("polarity")=="NEGATIVE":required.add("mutation_id")
        if set(x)!=required or x.get("polarity") not in {"POSITIVE","NEGATIVE"} or x.get("vector_kind") not in {"CODE_CATALOG","POLICY","DIAGNOSTIC_REGISTRATION","TERMINAL_COMPOSITION"}:return None
        if any(type(x.get(k)) is not str for k in required-{"expected_diagnostic_codes"}):return None
        codes=x.get("expected_diagnostic_codes")
        if type(codes) is not list or codes!=sorted(codes) or len(codes)!=len(set(codes)) or any(type(c) is not str or c not in allowed for c in codes) or (x["polarity"]=="POSITIVE" and codes) or (x["polarity"]=="NEGATIVE" and not codes):return None
        if x["vector_id"] in seen:return None
        seen.add(x["vector_id"])
        q=_parsed(x)
        if q is None or len(canonical_bytes(q))>_POLICY_LIMITS["maximum_vector_entry_bytes"]:return None
    return d

def _resolve(ref,supports,media):
    rawref=_asset_projection(ref)
    matches=[x for x in supports if x[0]==ref.get("asset_id")]
    if len(matches)!=1:return None
    a,m,b,u=matches[0];observed={"asset_id":a,"media_type":m,"byte_size":len(b),"sha256":_raw_hash(b),**({"schema_uri":u} if "schema_uri" in ref else {})}
    return matches[0] if m==media and rawref==observed else None

def _policy_findings(doc,catalog_doc,catalog_snapshot,policy_snapshot,cparts,supports):
    findings=[]
    refs=[doc.get("code_catalog_ref"),doc.get("terminal_schema_ref"),doc.get("validator_ref"),doc.get("conformance_vector_ref")]
    structural=doc.get("structural_constraints_ref",{});refs.extend(structural.get(k) for k in ("requirements_ref","catalog_ref","profile_ref"))
    if any(type(r) is not dict or _canonical_ref(r) is None or len(_canonical_ref(r))>_POLICY_LIMITS["maximum_exact_ref_bytes"] or "path_hint" in r for r in refs):findings.append(_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"policy contains an invalid or oversized exact reference","CODE_POLICY_GRAPH"));return findings
    if not _same_ref(doc["code_catalog_ref"],catalog_snapshot[0]) or not _same_ref(structural["requirements_ref"],cparts[0].to_python()) or not _same_ref(structural["catalog_ref"],cparts[1].to_python()) or not _same_ref(structural["profile_ref"],cparts[2].to_python()) or _asset_projection(doc["terminal_schema_ref"])!={"asset_id":"schema:typed-terminal-result:1.0.0","media_type":"application/schema+json","byte_size":16054,"sha256":"sha256:3384964d6e02bc326660ab56bb79c816ff0b6233ea8bb91aca5ba2c383a1a5e6","schema_uri":"https://agtxiv.org/schema/v2/contract-kernel/terminal/typed-terminal-result/1.0.0"}:findings.append(_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"policy roots differ from exact D, B, or C constraints","CODE_POLICY_GRAPH"))
    validator=_resolve(doc["validator_ref"],supports,"text/x-python");vectors=_resolve(doc["conformance_vector_ref"],supports,"application/json")
    if validator is None or vectors is None or validator[2] in {catalog_snapshot[3],policy_snapshot[3]} or vectors[2] in {catalog_snapshot[3],policy_snapshot[3]}:findings.append(_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"support binding is unresolved, aliased, or cyclic","CODE_POLICY_GRAPH"))
    elif _vector_index(vectors[2]) is None:findings.append(_diag(DiagnosticCode.CODE_POLICY_INVALID,"vector index is not closed canonical test metadata","CODE_POLICY_GRAPH"))
    if doc.get("validator_entry_points")!=dict(_ENTRY_POINTS) or tuple(doc.get("gate_order",()))!=_GATE_ORDER or doc.get("resource_limits")!=dict(_POLICY_LIMITS):findings.append(_diag(DiagnosticCode.CODE_POLICY_INVALID,"policy gates, entry points, or resources differ from compiled values","CODE_POLICY_INTRINSIC"))
    registrations=doc.get("terminal_reason_registrations")
    expected=[{"reason_code":_REASON_CODE,"registration_kind":"SYNTHETIC_COMPOSITION_ONLY","allowed_outcomes":["RETRY_REQUIRED","REVIEW_REQUIRED","BLOCKED","FAILED"],"allowed_retry_dispositions":list(_RETRY_ORDER),"allowed_context_modes":["FROZEN_SCOPE_BOUND"],"targets":[{"family_id":"CHECKPOINT_C_SYNTHETIC_RECORD","family_version":"1.0.0","stage_id":"SYNTHETIC_ANALYSIS"}]}]
    if registrations!=expected:findings.append(_diag(DiagnosticCode.CODE_POLICY_INVALID,"reason registration differs from the sole frozen synthetic registration","CODE_POLICY_REGISTRATION"))
    reason=[x for x in catalog_doc["codes"] if x["code"]==_REASON_CODE]
    policies=cparts[6];targets=[p for p in policies if (p.family_id,p.family_version,p.stage_id)==("CHECKPOINT_C_SYNTHETIC_RECORD","1.0.0","SYNTHETIC_ANALYSIS")]
    if len(reason)!=1 or reason[0]["code_kind"]!="TERMINAL_REASON" or reason[0]["status"]!="ACTIVE" or len(targets)!=1 or targets[0].adjustment=="NOT_SELECTED" or targets[0].terminal_mode!="STRUCTURALLY_PERMITTED" or targets[0].outcomes!=tuple(expected[0]["allowed_outcomes"]) or targets[0].minimum_context!="FROZEN_SCOPE_BOUND":findings.append(_diag(DiagnosticCode.CODE_POLICY_INVALID,"registration does not resolve to active reason and effective C target","CODE_POLICY_REGISTRATION"))
    return findings

def _make_constraints(cs,ps,cparts,terminal_ref):
    refs={"code_catalog":_parsed(cs[0]),"policy":_parsed(ps[0]),"requirements":cparts[0],"catalog":cparts[1],"profile":cparts[2],"terminal_schema":_parsed(terminal_ref)}
    registration=_Registration(_REASON_CODE,("RETRY_REQUIRED","REVIEW_REQUIRED","BLOCKED","FAILED"),_RETRY_ORDER,("FROZEN_SCOPE_BOUND",),(("CHECKPOINT_C_SYNTHETIC_RECORD","1.0.0","SYNTHETIC_ANALYSIS"),))
    return KernelValidationPolicyConstraints(MappingProxyType(refs),tuple(str(x) for x in DiagnosticCode),(_REASON_CODE,),_GATE_ORDER,(registration,),_token=_TOKEN)

def _registered_policy_findings(findings,constraints):
    ordered=_sort_diagnostics(findings)
    registration=validate_emitted_diagnostic_registration(ordered,constraints)
    return _sort_diagnostics(registration) if registration else ordered

def build_kernel_validation_policy_constraints(code_catalog_binding,policy_binding,catalog_profile_constraints,support_assets,registry):
    try:
        preflight,ds=_preflight_d_inputs(code_catalog_binding,policy_binding,catalog_profile_constraints,support_assets,registry)
        if ds:return ds
        entries=_registry_entries(registry)
        if entries is None:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"registry failed exact type or seal integrity","CODE_POLICY_INPUT"),)
        index={entry.asset_id:entry for entry in entries}
        namespace=_establish_asset_namespace(preflight,entries)
        if namespace is None:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"C refs or registry entries are malformed","CODE_POLICY_INPUT"),)
        if not namespace:return (_diag(DiagnosticCode.CODE_POLICY_REFERENCE_INVALID,"D roots, supports, C refs, and registry entries require one unique asset-ID namespace","CODE_POLICY_BINDING"),)
        # One inherited registry integrity traversal is cached before namespace
        # closure; closure then precedes every digest, parse, and materialization.
        cparts=preflight[3]
        cs,ps,supports=_snapshot_preflight(preflight)
        cb,ds=_bound_root(cs,entries,index,"catalog","CODE_CATALOG_SCHEMA")
        if ds:return ds
        findings=_catalog_findings(cb[1])
        if findings:return findings
        registration_constraints=_make_constraints(cs,ps,cparts,{"asset_id":"schema:typed-terminal-result:1.0.0","media_type":"application/schema+json","byte_size":16054,"sha256":"sha256:3384964d6e02bc326660ab56bb79c816ff0b6233ea8bb91aca5ba2c383a1a5e6","schema_uri":"https://agtxiv.org/schema/v2/contract-kernel/terminal/typed-terminal-result/1.0.0"})
        pb,ds=_bound_root(ps,entries,index,"policy","CODE_POLICY_SCHEMA")
        if ds:return _registered_policy_findings(ds,registration_constraints)
        findings=_policy_findings(pb[1],cb[1],cs,ps,cparts,supports)
        if findings:return _registered_policy_findings(findings,registration_constraints)
        result=_make_constraints(cs,ps,cparts,pb[1]["terminal_schema_ref"])
        emitted=validate_emitted_diagnostic_registration((),result)
        return emitted if emitted else result
    except Exception:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"policy builder could not safely inspect inputs","CODE_POLICY_INPUT"),)

def validate_emitted_diagnostic_registration(diagnostics,constraints):
    try:
        parts=_parts(constraints)
        if parts is None or type(diagnostics) is not tuple:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"diagnostics or constraints failed exact type/seal integrity","DIAGNOSTIC_REGISTRATION"),)
        if len(diagnostics)>_POLICY_LIMITS["maximum_emitted_diagnostics"]:return (_diag(DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED,"emitted diagnostic count exceeds policy limit","DIAGNOSTIC_REGISTRATION"),)
        allowed=set(parts[1]);findings=[]
        for i,d in enumerate(diagnostics):
            if type(d) is not Diagnostic:
                findings.append(_diag(DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED,"emitted value is not an exact Diagnostic","DIAGNOSTIC_REGISTRATION",f"/{i}"));continue
            try:code=object.__getattribute__(d,"code")
            except Exception:code=None
            if type(code) is not DiagnosticCode or str(code) not in allowed:findings.append(_diag(DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED,"emitted diagnostic is absent from validation-diagnostic catalog projection","DIAGNOSTIC_REGISTRATION",f"/{i}"))
        return _sort_diagnostics(findings)
    except Exception:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"diagnostic registration could not safely inspect inputs","DIAGNOSTIC_REGISTRATION"),)

def validate_typed_terminal_result_kernel_constraints(record,registry,catalog_profile_constraints,constraints):
    # C public owns B intrinsic and C structural validation and is called exactly once.
    c_findings=validate_typed_terminal_result_catalog_constraints(record,registry,catalog_profile_constraints)
    if c_findings:return c_findings
    parts=_parts(constraints);cparts=_constraints_parts(catalog_profile_constraints)
    if parts is None or cparts is None:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"D or C constraints failed exact type/seal integrity","REASON_POLICY_INPUT"),)
    try:
        if not _same_ref(parts[0]["requirements"].to_python(),cparts[0].to_python()) or not _same_ref(parts[0]["catalog"].to_python(),cparts[1].to_python()) or not _same_ref(parts[0]["profile"].to_python(),cparts[2].to_python()):result=(_diag(DiagnosticCode.REASON_CONSTRAINT_MISMATCH,"D policy roots differ from C constraints","REASON_POLICY"),)
        else:
            d=record.to_python();payload=d["payload"];reason=payload["declared_reason"]["declared_reason_code"];target=payload["target_obligation"];context=payload["binding_context"]["context_mode"];outcome=payload["outcome"];retry=payload["retry"]["retry_disposition"]
            registrations=[r for r in parts[4] if r.reason_code==reason]
            if reason not in parts[2] or len(registrations)!=1:result=(_diag(DiagnosticCode.REASON_UNREGISTERED,"terminal reason is not an active registered TERMINAL_REASON","REASON_POLICY",pointer="/payload/declared_reason/declared_reason_code"),)
            else:
                r=registrations[0];target_key=(target["family_id"],"1.0.0",target["stage_id"])
                if target_key not in r.targets or outcome not in r.outcomes or retry not in r.retries or context not in r.contexts:result=(_diag(DiagnosticCode.REASON_CONSTRAINT_MISMATCH,"terminal reason is outside registered target, outcome, retry, or context constraints","REASON_POLICY"),)
                else:result=()
        registration=validate_emitted_diagnostic_registration(result,constraints)
        return registration if registration else result
    except Exception:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"reason policy could not safely inspect terminal record","REASON_POLICY_INPUT"),)

__all__=["KernelValidationPolicyConstraints","validate_stable_code_catalog_intrinsic","build_kernel_validation_policy_constraints","validate_emitted_diagnostic_registration","validate_typed_terminal_result_kernel_constraints"]
