"""Pure Checkpoint E planning, discovery, scope, and revision validation.

All authoritative bytes are explicit arguments.  Paths in submitted records are
identifiers only: this module never opens them or consults ambient state.
Successful values are detached structural snapshots and carry no runtime,
release, review, or admission authority.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Never

from .canonical import ParsedCanonicalValue, build_canonical_value, canonical_bytes, parse_canonical_json
from .catalog_validation import CatalogProfileConstraints, RawContractAssetBinding, _constraints_parts, build_catalog_profile_constraints, validate_typed_terminal_result_catalog_constraints
from .code_policy_validation import build_kernel_validation_policy_constraints
from .code_policy_v1_1_validation import KernelValidationPolicyV11Constraints, _parts as _v11_parts, build_kernel_validation_policy_v1_1_constraints, validate_planning_terminal_registration_v1_1
from .diagnostics import Diagnostic, DiagnosticCode
from .references import SuppliedAsset, raw_asset_sha256
from .registry import ContractSchemaRegistry, _diagnostic, _registry_entries, _sort_diagnostics
from .schema_validation import validate_immutable_record_payload

MAX_SOURCE_FILES = 4096
MAX_PATH_BYTES = 1024
MAX_SOURCE_FILE_BYTES = 33_554_432
MAX_TOTAL_SOURCE_BYTES = 67_108_864
MAX_OBLIGATIONS = 256
MAX_COMPONENTS = 8192
MAX_COMPONENT_ENTRY_BYTES = 4096
MAX_FINDINGS = 4096
MAX_SCOPE_ENTRIES = 16_384
MAX_PREDECESSOR_DECLARATIONS = 256
MAX_RECORD_BYTES = 41_943_040
MAX_AGGREGATE_INPUT_BYTES = 134_217_728
MAX_EXACT_REF_BYTES = 2048
LEGACY_RECORD_TYPE = "agtxiv.inventory-scope/2.0.0"
LEGACY_SCHEMA_URI = "https://agtxiv.org/schema/v2/inventory-scope/2.0.0"
_COMPONENT_KIND_ORDER = ("DOCUMENT_TEXT", "APPENDIX_TEXT", "BIBLIOGRAPHY_TEXT", "FIGURE_BINARY", "ARCHIVE_BINARY", "UNRESOLVED_SOURCE_REGION")
_COMPONENT_KINDS = frozenset(_COMPONENT_KIND_ORDER)
_ALLOWED_OVERLAP_KIND_PAIRS = frozenset({frozenset(("DOCUMENT_TEXT","APPENDIX_TEXT")),*(frozenset(("UNRESOLVED_SOURCE_REGION",kind)) for kind in _COMPONENT_KIND_ORDER if kind!="UNRESOLVED_SOURCE_REGION")})
_FORBIDDEN_PLAN_KEYS = frozenset(("query", "query_ref", "query_text", "requested_claim", "requested_theorem", "search", "filter", "include_only", "exclude", "path_subset", "family_subset", "region_subset", "dynamic_selector", "latest"))
_DEVICE = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.I)
_EXPECTED_BUNDLE_SCHEMA_URIS = frozenset((
    *(f"https://agtxiv.org/schema/v2/contract-kernel/common/{name}/1.0.0" for name in ("actor-identity","digest","exact-asset-ref","exact-component-ref","exact-record-ref","immutable-record-envelope","producer-context","resource-budget")),
    "https://agtxiv.org/schema/v2/contract-kernel/terminal/typed-terminal-result/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/artifact-family-catalog/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/agentization-profile-release/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/fixture/checkpoint-c-synthetic-record/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/kernel-validation-policy/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.1.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/kernel-validation-policy/1.1.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/contract-bundle-release/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/source/paper-source-snapshot/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/planning/agentization-plan/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/inventory/inventory-discovery-result/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/review/scope-freeze-decision/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/inventory/frozen-inventory-scope/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/fixture/planning-scope/entry-output/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/fixture/planning-scope/whole-scope-output/1.0.0",
    "https://agtxiv.org/schema/v2/contract-kernel/fixture/planning-scope/derived-output/1.0.0",
))
_BUNDLE_SCHEMA_IDS = (
    *((f"schema:common:{name}:1.0.0", f"https://agtxiv.org/schema/v2/contract-kernel/common/{name}/1.0.0") for name in ("actor-identity","digest","exact-asset-ref","exact-component-ref","exact-record-ref","immutable-record-envelope","producer-context","resource-budget")),
    ("schema:typed-terminal-result:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/terminal/typed-terminal-result/1.0.0"),
    ("schema:m1-contract-requirement-set:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0"),
    ("schema:artifact-family-catalog:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/contract/artifact-family-catalog/1.0.0"),
    ("schema:agentization-profile-release:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/contract/agentization-profile-release/1.0.0"),
    ("schema:fixture:checkpoint-c-synthetic-record:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/fixture/checkpoint-c-synthetic-record/1.0.0"),
    ("schema:stable-code-catalog:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.0.0"),
    ("schema:kernel-validation-policy:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/contract/kernel-validation-policy/1.0.0"),
    ("schema:stable-code-catalog:1.1.0","https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.1.0"),
    ("schema:kernel-validation-policy:1.1.0","https://agtxiv.org/schema/v2/contract-kernel/contract/kernel-validation-policy/1.1.0"),
    ("schema:contract-bundle-release:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/contract/contract-bundle-release/1.0.0"),
    ("schema:paper-source-snapshot:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/source/paper-source-snapshot/1.0.0"),
    ("schema:agentization-plan:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/planning/agentization-plan/1.0.0"),
    ("schema:inventory-discovery-result:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/inventory/inventory-discovery-result/1.0.0"),
    ("schema:scope-freeze-decision:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/review/scope-freeze-decision/1.0.0"),
    ("schema:frozen-inventory-scope:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/inventory/frozen-inventory-scope/1.0.0"),
    ("schema:discovery-obligation-policy:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0"),
    ("schema:fixture:checkpoint-e-entry-output:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/fixture/planning-scope/entry-output/1.0.0"),
    ("schema:fixture:checkpoint-e-whole-scope-output:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/fixture/planning-scope/whole-scope-output/1.0.0"),
    ("schema:fixture:checkpoint-e-derived-output:1.0.0","https://agtxiv.org/schema/v2/contract-kernel/fixture/planning-scope/derived-output/1.0.0"),
)
_BUNDLE_CONTRACT_IDS = (
    "requirements:m1-contract-requirement-set:1.0.0","fixture-catalog:checkpoint-c-linkage/1.0.0","fixture-profile:checkpoint-c-linkage/1.0.0","vectors:catalog-profile-linkage:checkpoint-c/1.0.0","code-catalog:agtxiv-contract-kernel/1.0.0","validation-policy:checkpoint-d-kernel-candidate/1.0.0","vectors:checkpoint-d-code-policy/1.0.0","code-catalog:agtxiv-contract-kernel/1.1.0","catalog:checkpoint-e-planning-families/1.0.0-candidate.1","profile:checkpoint-e-planning-families/1.0.0-candidate.1","discovery-policy:checkpoint-e/1.0.0-candidate.1","validation-policy:checkpoint-e-kernel-candidate/1.1.0","vectors:checkpoint-e-planning-families/1.0.0","canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/golden-vectors","canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/provenance",
)
_BUNDLE_VALIDATOR_IDS = (
    "validator:checkpoint-e-contract-exports:1.0.0","validator:checkpoint-a-canonical-json:1.0.0","validator:checkpoint-c-contract-documents:1.0.0","validator:checkpoint-d-code-policy:1.0.0","validator:checkpoint-e-code-policy:1.1.0","validator:checkpoint-a-diagnostics:1.0.0","validator:checkpoint-e-planning-scope:1.0.0","validator:checkpoint-a-exact-references:1.0.0","validator:checkpoint-a-schema-registry:1.0.0","validator:checkpoint-a-immutable-record-payload:1.0.0","validator:checkpoint-b-typed-terminal-result:1.0.0",
)
_BUNDLE_SPEC_IDS = ("roadmap:v2-end-to-end-implementation-plan:2026-08-31","adr:0003-plan-discovery-scope-freeze","roadmap:v2-m1-contract-kernel-checkpoint-e:1.0")
BUNDLE_ASSET_ROLES = MappingProxyType({**{asset_id:("schema_assets","application/schema+json",uri) for asset_id,uri in _BUNDLE_SCHEMA_IDS},**{asset_id:("contract_assets","application/json",None) for asset_id in _BUNDLE_CONTRACT_IDS},**{asset_id:("validator_assets","text/x-python",None) for asset_id in _BUNDLE_VALIDATOR_IDS},**{asset_id:("specification_assets","text/markdown",None) for asset_id in _BUNDLE_SPEC_IDS},"canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/golden-vectors":("contract_assets","application/jsonl",None)})
_TOKEN = object()


def _diag(code: DiagnosticCode, message: str, phase: str, pointer: str = "", subject: str | None = None, details: Any = None) -> Diagnostic:
    return _diagnostic(code, message, pointer=pointer, phase=phase, subject=subject, details=details)


def _failure(message: str, phase: str = "PLANNING_INPUT", *, code: DiagnosticCode = DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH, pointer: str = "") -> tuple[Diagnostic, ...]:
    return (_diag(code, message, phase, pointer),)


def _canonical(value: Any) -> bytes:
    parsed = build_canonical_value(value)
    if type(parsed) is not ParsedCanonicalValue:
        raise ValueError("value is not canonical JSON")
    return canonical_bytes(parsed)


def _hash(prefix: bytes, *parts: bytes) -> str:
    h = hashlib.sha256(prefix)
    for part in parts:
        h.update(part)
    return h.hexdigest()


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "big")


def _framed(value: bytes) -> bytes:
    return _u64(len(value)) + value


def _record_ref(document: dict[str, Any]) -> dict[str, Any]:
    envelope = document["envelope"]
    return {"record_type": envelope["record_type"], "record_id": envelope["record_id"], "record_revision": envelope["record_revision"], "schema_ref": envelope["schema_ref"], "content_hash": document["content_hash"]}


def _asset_ref(asset: SuppliedAsset) -> dict[str, Any]:
    result = {"asset_id": asset.asset_id, "media_type": asset.media_type, "byte_size": len(asset.raw_bytes), "sha256": raw_asset_sha256(asset.raw_bytes)}
    if asset.schema_uri is not None:
        result["schema_uri"] = asset.schema_uri
    return result


def _ref_equal(left: Any, right: Any) -> bool:
    return type(left) is dict and type(right) is dict and left == right and "path_hint" not in left and len(_canonical(left)) <= MAX_EXACT_REF_BYTES


def _parse_record(raw: bytes, registry: ContractSchemaRegistry, expected_type: str, phase: str) -> tuple[tuple[ParsedCanonicalValue, dict[str, Any]] | None, tuple[Diagnostic, ...]]:
    if type(raw) is not bytes or type(registry) is not ContractSchemaRegistry:
        return None, _failure("record and registry require exact built-in types", phase)
    entries = _registry_entries(registry)
    if entries is None or any(entry.schema_id == LEGACY_SCHEMA_URI or entry.asset_id in {LEGACY_RECORD_TYPE, LEGACY_SCHEMA_URI} for entry in entries):
        return None, _failure("registry is forged or contains the rejected legacy flat InventoryScope family", phase, code=DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH)
    if len(raw) > MAX_RECORD_BYTES:
        return None, _failure("record exceeds the Checkpoint E raw-byte limit", phase, code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
    parsed = parse_canonical_json(raw)
    if type(parsed) is Diagnostic:
        return None, (parsed,)
    if canonical_bytes(parsed) != raw:
        return None, _failure("record bytes are not canonical JSON", phase, code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
    diagnostics = validate_immutable_record_payload(parsed, registry)
    if expected_type == "agtxiv.frozen-inventory-scope/1.0.0":
        diagnostics = tuple(item for item in diagnostics if not (item.code is DiagnosticCode.RECORD_SUPERSESSION_MISMATCH and item.phase == "RECORD_ENVELOPE" and item.json_pointer == "/envelope/supersedes_ref"))
    if diagnostics:
        return None, diagnostics
    document = parsed.to_python()
    if document["envelope"]["record_type"] != expected_type or expected_type in {LEGACY_RECORD_TYPE, LEGACY_SCHEMA_URI}:
        return None, _failure("record type differs from the required Checkpoint E family", phase, code=DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH)
    return (parsed, document), ()


def _bundle(raw: bytes, registry: ContractSchemaRegistry, supplied_assets: tuple[SuppliedAsset, ...]) -> tuple[dict[str, Any] | None, tuple[Diagnostic, ...]]:
    if type(supplied_assets) is not tuple or len(supplied_assets)!=56 or any(type(asset) is not SuppliedAsset for asset in supplied_assets):return None,_failure("bundle resolution requires exactly 56 exact supplied assets","BUNDLE_PREFLIGHT")
    supplied_index=_asset_index(supplied_assets)
    if supplied_index is None or set(supplied_index)!=set(BUNDLE_ASSET_ROLES):return None,_failure("supplied bundle namespace differs from the exact Section 12 closure","BUNDLE_BINDING",code=DiagnosticCode.CATALOG_REFERENCE_INVALID)
    bound, diagnostics = _parse_record(raw, registry, "agtxiv.contract-bundle-release/1.0.0", "BUNDLE_BINDING")
    if diagnostics:
        return None, diagnostics
    assert bound is not None
    document = bound[1]
    envelope, payload = document["envelope"], document["payload"]
    if any(name in envelope for name in ("contract_bundle_ref", "producer_context", "supersedes_ref")) or envelope["record_revision"] != 1 or payload["bundle_id"] != envelope["record_id"]:
        return None, _failure("bundle does not satisfy the baseEnvelope bootstrap profile", "BUNDLE_BINDING", code=DiagnosticCode.RECORD_INVALID_ENVELOPE)
    names=("schema_assets", "contract_assets", "validator_assets", "specification_assets");arrays = [payload[name] for name in names]
    refs = [ref for values in arrays for ref in values]
    identifiers = [ref.get("asset_id") for ref in refs]
    if tuple(map(len,arrays))!=(27,15,11,3) or len(refs) != 56 or len(identifiers) != len(set(identifiers)) or any(type(value) is not str for value in identifiers):
        return None, _failure("bundle must contain the exact 27/15/11/3 globally unique role cardinalities", "BUNDLE_MANIFEST", code=DiagnosticCode.CATALOG_REFERENCE_INVALID)
    for role,values in zip(names,arrays):
        expected_ids=[asset_id for asset_id,(expected_role,_,_) in BUNDLE_ASSET_ROLES.items() if expected_role==role]
        if [ref.get("asset_id") for ref in values]!=expected_ids:return None,_failure("bundle role order or exact asset identities differ from Section 12","BUNDLE_MANIFEST",code=DiagnosticCode.CATALOG_REFERENCE_INVALID)
        for ref in values:
            expected_role,media,uri=BUNDLE_ASSET_ROLES[ref["asset_id"]];asset=supplied_index[ref["asset_id"]]
            if expected_role!=role or asset.media_type!=media or asset.schema_uri!=uri or ref!=_asset_ref(asset) or "path_hint" in ref or len(_canonical(ref))>MAX_EXACT_REF_BYTES:return None,_failure("bundle ref does not resolve exact role, bytes, media, hash, or schema metadata","BUNDLE_MANIFEST",code=DiagnosticCode.REF_HASH_MISMATCH)
    registry_entries=_registry_entries(registry)
    if registry_entries is None or {entry.asset_id for entry in registry_entries}!={asset_id for asset_id,_ in _BUNDLE_SCHEMA_IDS}:return None,_failure("registry does not equal the bundle schema closure","BUNDLE_BINDING",code=DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH)
    if any(entry.raw_bytes!=supplied_index[entry.asset_id].raw_bytes for entry in registry_entries):return None,_failure("registry schema bytes differ from bundle namespace","BUNDLE_BINDING",code=DiagnosticCode.REF_HASH_MISMATCH)
    if len({asset.raw_bytes for asset in supplied_assets})!=len(supplied_assets):return None,_failure("bundle namespace aliases identical bytes under multiple IDs","BUNDLE_BINDING",code=DiagnosticCode.CATALOG_REFERENCE_INVALID)
    manifest = {name: payload[name] for name in names}
    if len(_canonical(manifest))>131072:return None,_failure("bundle manifest exceeds its exact byte ceiling","BUNDLE_MANIFEST",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
    expected = "sha256:" + hashlib.sha256(b"AGTXIV_BUNDLE_ASSET_MANIFEST_V1\x00" + _canonical(manifest)).hexdigest()
    if payload["bundle_manifest_hash"] != expected or payload["canonicalization_profile_ref"] not in payload["contract_assets"]:
        return None, _failure("bundle manifest hash or canonicalization alias is inconsistent", "BUNDLE_MANIFEST", code=DiagnosticCode.REF_HASH_MISMATCH)
    return document, ()


def _producer_matches(envelope: dict[str, Any], bundle: dict[str, Any], role: str) -> bool:
    context = envelope.get("producer_context")
    if type(context) is not dict or context.get("role") != role:
        return False
    manifest_refs = [
        ref
        for name in ("schema_assets", "contract_assets", "validator_assets", "specification_assets")
        for ref in bundle["payload"][name]
    ]
    provenance_ref = next((ref for ref in bundle["payload"]["contract_assets"] if ref.get("asset_id") == "canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/provenance"), None)
    return (
        context.get("implementation_ref") in manifest_refs
        and context.get("environment_ref") == provenance_ref
        and context["implementation_ref"].get("media_type") == "text/x-python"
    )


def _preflight(raws: tuple[Any, ...], source_map: Any = None, assets: Any = None, tuples: tuple[Any, ...] = ()) -> tuple[Diagnostic, ...]:
    if any(type(raw) is not bytes for raw in raws) or any(type(value) is not tuple for value in tuples):
        return _failure("all raw inputs and complete-set declarations require exact built-in bytes/tuple types")
    for values in tuples:
        if any(type(value) is not bytes for value in values):
            return _failure("tuple members require exact built-in bytes")
    if any(len(raw)>MAX_RECORD_BYTES for raw in raws) or any(len(raw)>MAX_RECORD_BYTES for values in tuples for raw in values):
        return _failure("a supplied record exceeds the Checkpoint E raw-byte limit",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
    total = sum(len(raw) for raw in raws) + sum(len(raw) for values in tuples for raw in values)
    if source_map is not None:
        if type(source_map) is not dict or any(type(key) is not str or type(value) is not bytes for key, value in source_map.items()):
            return _failure("source evidence requires exact dict[str, bytes]")
        if len(source_map)>MAX_SOURCE_FILES or any(len(value)>MAX_SOURCE_FILE_BYTES for value in source_map.values()) or sum(len(value) for value in source_map.values())>MAX_TOTAL_SOURCE_BYTES:
            return _failure("source evidence exceeds file-count or byte preflight limits",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        total += sum(len(value) for value in source_map.values())
    if assets is not None:
        if type(assets) is not tuple or any(type(asset) is not SuppliedAsset for asset in assets):
            return _failure("supplied assets require an exact tuple of SuppliedAsset")
        total += sum(len(asset.raw_bytes) for asset in assets)
    if total > MAX_AGGREGATE_INPUT_BYTES:
        return _failure("aggregate supplied input exceeds the Checkpoint E byte limit", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
    return ()


class _SealedView:
    __slots__ = ("__kind", "__data", "__seal", "__token")
    def __init__(self, kind: str, data: dict[str, Any], *, _token: object = None):
        if _token is not _TOKEN:
            raise TypeError("sealed planning views are validator-created")
        frozen = _canonical(data)
        object.__setattr__(self, "_SealedView__kind", kind)
        object.__setattr__(self, "_SealedView__data", frozen)
        object.__setattr__(self, "_SealedView__seal", hashlib.sha256(kind.encode() + b"\x00" + frozen).digest())
        object.__setattr__(self, "_SealedView__token", _TOKEN)
    def __setattr__(self, name: str, value: Any) -> Never: raise AttributeError("sealed planning view is immutable")
    def __delattr__(self, name: str) -> Never: raise AttributeError("sealed planning view is immutable")
    def to_python(self) -> dict[str, Any]:
        kind = object.__getattribute__(self, "_SealedView__kind"); raw = object.__getattribute__(self, "_SealedView__data")
        seal = object.__getattribute__(self, "_SealedView__seal"); token = object.__getattribute__(self, "_SealedView__token")
        if token is not _TOKEN or type(kind) is not str or type(raw) is not bytes or seal != hashlib.sha256(kind.encode() + b"\x00" + raw).digest():
            raise ValueError("sealed planning view failed integrity")
        parsed = parse_canonical_json(raw)
        if type(parsed) is not ParsedCanonicalValue: raise ValueError("sealed planning view failed parsing")
        return parsed.to_python()
    def __repr__(self) -> str: return f"{object.__getattribute__(self, '_SealedView__kind')}(<sealed>)"


PlanningScopeChain = _SealedView
ScopeRevisionImpact = _SealedView


class PlanningScopeChainDeclaration:
    __slots__=("__records","__sources","__assets","__seal","__token")
    def __init__(self,records: tuple[bytes,...],sources: tuple[tuple[str,bytes],...],assets: tuple[SuppliedAsset,...],*,_token: object=None):
        if _token is not _TOKEN:raise TypeError("use build_planning_scope_chain_declaration")
        raw=b"".join(_framed(value) for value in records)+b"".join(_framed(path.encode())+_framed(value) for path,value in sources)+b"".join(_framed(_canonical(_asset_ref(asset)))+_framed(asset.raw_bytes) for asset in assets)
        object.__setattr__(self,"_PlanningScopeChainDeclaration__records",records);object.__setattr__(self,"_PlanningScopeChainDeclaration__sources",sources);object.__setattr__(self,"_PlanningScopeChainDeclaration__assets",assets);object.__setattr__(self,"_PlanningScopeChainDeclaration__seal",hashlib.sha256(raw).digest());object.__setattr__(self,"_PlanningScopeChainDeclaration__token",_TOKEN)
    def __setattr__(self,name,value)->Never:raise AttributeError("planning chain declaration is immutable")
    def __delattr__(self,name)->Never:raise AttributeError("planning chain declaration is immutable")
    def __repr__(self)->str:return "PlanningScopeChainDeclaration(<sealed exact inputs>)"


def _declaration_fields(value: Any):
    if type(value) is not PlanningScopeChainDeclaration:return None
    try:records=object.__getattribute__(value,"_PlanningScopeChainDeclaration__records");sources=object.__getattribute__(value,"_PlanningScopeChainDeclaration__sources");assets=object.__getattribute__(value,"_PlanningScopeChainDeclaration__assets");seal=object.__getattribute__(value,"_PlanningScopeChainDeclaration__seal");token=object.__getattribute__(value,"_PlanningScopeChainDeclaration__token")
    except Exception:return None
    if token is not _TOKEN or type(records) is not tuple or len(records)!=6 or any(type(raw) is not bytes for raw in records) or type(sources) is not tuple or any(type(row) is not tuple or len(row)!=2 or type(row[0]) is not str or type(row[1]) is not bytes for row in sources) or type(assets) is not tuple or any(type(asset) is not SuppliedAsset for asset in assets) or type(seal) is not bytes:return None
    return records,sources,assets,seal


def _declaration_parts(value: Any):
    fields=_declaration_fields(value)
    if fields is None:return None
    records,sources,assets,seal=fields
    try:raw=b"".join(_framed(item) for item in records)+b"".join(_framed(path.encode())+_framed(item) for path,item in sources)+b"".join(_framed(_canonical(_asset_ref(asset)))+_framed(asset.raw_bytes) for asset in assets)
    except Exception:return None
    return (records,sources,assets) if seal==hashlib.sha256(raw).digest() else None


def build_planning_scope_chain_declaration(snapshot_raw: bytes,source_bytes_by_path: dict[str,bytes],plan_raw: bytes,discovery_raw: bytes,decision_raw: bytes,scope_raw: bytes,supplied_contract_assets: tuple[SuppliedAsset,...],bundle_raw: bytes) -> PlanningScopeChainDeclaration | tuple[Diagnostic,...]:
    try:
        diagnostics=_preflight((snapshot_raw,plan_raw,discovery_raw,decision_raw,scope_raw,bundle_raw),source_bytes_by_path,supplied_contract_assets)
        if diagnostics:return diagnostics
        if len(supplied_contract_assets)!=56:return _failure("declaration requires the complete exact bundle asset namespace","CHAIN_DECLARATION")
        sources=tuple(sorted(source_bytes_by_path.items(),key=lambda row:row[0].encode()))
        return PlanningScopeChainDeclaration((snapshot_raw,plan_raw,discovery_raw,decision_raw,scope_raw,bundle_raw),sources,supplied_contract_assets,_token=_TOKEN)
    except Exception:return _failure("planning chain declaration failed closed","CHAIN_DECLARATION")


def _valid_path(path: str) -> bool:
    if type(path) is not str or path != unicodedata.normalize("NFC", path): return False
    try: encoded = path.encode("utf-8", "strict")
    except UnicodeError: return False
    if not 1 <= len(encoded) <= MAX_PATH_BYTES or path.startswith("/") or path.endswith("/") or "\\" in path or ":" in path: return False
    if any(ord(ch) <= 0x1f or 0x7f <= ord(ch) <= 0x9f or unicodedata.category(ch) in {"Cc", "Cf", "Cs", "Zl", "Zp", "Zs"} for ch in path): return False
    parts = path.split("/")
    return all(part not in {"", ".", ".."} and not part.endswith((" ", ".")) and _DEVICE.fullmatch(part) is None for part in parts)


def _source_row_id(path: str, unit: str) -> str:
    return "source-row:sha256:" + _hash(b"AGTXIV_SOURCE_ROW_V1\x00", _framed(path.encode()), _framed(unit.encode()))


def _source_root(rows: list[dict[str, Any]], source_map: dict[str, bytes]) -> str:
    leaves = []
    for row in rows:
        path = row["normalized_path"].encode(); raw = source_map[row["normalized_path"]]; media = row["media_type"].encode()
        leaves.append(hashlib.sha256(b"AGTXIV_SOURCE_TREE_V1_LEAF\x00" + _framed(path) + _u64(len(raw)) + hashlib.sha256(raw).digest() + _framed(media)).digest())
    return "sha256:" + hashlib.sha256(b"AGTXIV_SOURCE_TREE_V1_ROOT\x00" + _u64(len(rows)) + b"".join(leaves)).hexdigest()


def validate_paper_source_snapshot(snapshot_raw: bytes, source_bytes_by_path: dict[str, bytes], supplied_contract_assets: tuple[SuppliedAsset, ...], registry: ContractSchemaRegistry, bundle_raw: bytes) -> _SealedView | tuple[Diagnostic, ...]:
    try:
        diagnostics = _preflight((snapshot_raw, bundle_raw), source_bytes_by_path, supplied_contract_assets)
        if diagnostics: return diagnostics
        bundle, diagnostics = _bundle(bundle_raw, registry, supplied_contract_assets)
        if diagnostics: return diagnostics
        bound, diagnostics = _parse_record(snapshot_raw, registry, "agtxiv.paper-source-snapshot/1.0.0", "SOURCE_SNAPSHOT")
        if diagnostics: return diagnostics
        assert bound is not None and bundle is not None
        document = bound[1]; envelope = document["envelope"]; payload = document["payload"]; rows = payload["source_files"]
        if not _ref_equal(envelope.get("contract_bundle_ref"), _record_ref(bundle)) or not _producer_matches(envelope, bundle, "SOURCE_SNAPSHOT_BUILDER") or envelope["record_revision"] != 1 or "supersedes_ref" in envelope or payload["snapshot_id"] != envelope["record_id"]:
            return _failure("snapshot envelope identity or bundle binding is inconsistent", "SOURCE_SNAPSHOT_BINDING", code=DiagnosticCode.REF_HASH_MISMATCH)
        if len(rows) > MAX_SOURCE_FILES or len(source_bytes_by_path) > MAX_SOURCE_FILES: return _failure("source-file count exceeds limit", "SOURCE_PREFLIGHT", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        paths = [row["normalized_path"] for row in rows]
        if paths != sorted(paths, key=lambda x: x.encode()) or len(paths) != len(set(paths)) or len({p.casefold() for p in paths}) != len(paths) or set(paths) != set(source_bytes_by_path) or any(not _valid_path(p) for p in paths):
            return _failure("source path table is not canonical, collision-free, and closed", "SOURCE_PATH", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        if any(len(raw) > MAX_SOURCE_FILE_BYTES for raw in source_bytes_by_path.values()) or sum(map(len, source_bytes_by_path.values())) > MAX_TOTAL_SOURCE_BYTES:
            return _failure("source byte limits are exceeded", "SOURCE_PREFLIGHT", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        expected = []
        for row in rows:
            raw = source_bytes_by_path[row["normalized_path"]]; digest = hashlib.sha256(raw).hexdigest(); unit = "source-unit:sha256:" + digest
            expected.append({**row, "source_row_id": _source_row_id(row["normalized_path"], unit), "source_unit_id": unit, "sha256": "sha256:" + digest, "byte_size": len(raw)})
        if rows != expected or payload["source_file_count"] != len(rows) or payload["source_total_bytes"] != sum(map(len, source_bytes_by_path.values())) or payload["source_tree_root"] != _source_root(rows, source_bytes_by_path):
            return _failure("snapshot rows, counts, digests, IDs, or tree root differ from supplied bytes", "SOURCE_RECONCILIATION", code=DiagnosticCode.REF_HASH_MISMATCH)
        return _SealedView("PaperSourceSnapshot", document, _token=_TOKEN)
    except Exception:
        return _failure("snapshot validation failed closed while inspecting hostile input")


def _asset_index(assets: tuple[SuppliedAsset, ...]) -> dict[str, SuppliedAsset] | None:
    ids = [asset.asset_id for asset in assets]
    return None if len(ids) != len(set(ids)) or any(asset.asset_id in {LEGACY_RECORD_TYPE, LEGACY_SCHEMA_URI} or asset.schema_uri == LEGACY_SCHEMA_URI for asset in assets) else {asset.asset_id: asset for asset in assets}


def _resolve_asset(ref: Any, index: dict[str, SuppliedAsset]) -> SuppliedAsset | None:
    if type(ref) is not dict or "path_hint" in ref: return None
    asset = index.get(ref.get("asset_id"))
    return asset if asset is not None and ref == _asset_ref(asset) and len(_canonical(ref)) <= MAX_EXACT_REF_BYTES else None


def _parse_asset(asset: SuppliedAsset) -> dict[str, Any] | None:
    parsed = parse_canonical_json(asset.raw_bytes)
    return parsed.to_python() if type(parsed) is ParsedCanonicalValue and canonical_bytes(parsed) == asset.raw_bytes and type(parsed.to_python()) is dict else None


def _raw_binding(asset: SuppliedAsset) -> RawContractAssetBinding | None:
    try:
        ref = build_canonical_value(_asset_ref(asset))
        return RawContractAssetBinding(ref, asset) if type(ref) is ParsedCanonicalValue else None
    except Exception:
        return None


def _referenced_asset_ids(value: Any) -> set[str]:
    result: set[str] = set()
    if type(value) is dict:
        if type(value.get("asset_id")) is str and {"media_type", "byte_size", "sha256"} <= value.keys():
            result.add(value["asset_id"])
        for child in value.values():
            result.update(_referenced_asset_ids(child))
    elif type(value) is list:
        for child in value:
            result.update(_referenced_asset_ids(child))
    return result


def _planning_constraints(assets: tuple[SuppliedAsset, ...], registry: ContractSchemaRegistry, plan_payload: dict[str, Any]) -> tuple[CatalogProfileConstraints, KernelValidationPolicyV11Constraints] | tuple[Diagnostic, ...]:
    """Build the inherited D and active C/1.1 constraints from supplied bytes."""
    if type(assets) is not tuple or any(type(asset) is not SuppliedAsset for asset in assets) or type(registry) is not ContractSchemaRegistry or type(plan_payload) is not dict:
        return _failure("planning roots require exact supplied assets, registry, and Plan payload", "PLAN_POLICY")
    index = _asset_index(assets)
    if index is None:
        return _failure("planning assets do not form one exact namespace", "PLAN_POLICY", code=DiagnosticCode.CATALOG_REFERENCE_INVALID)
    documents = {asset.asset_id: _parse_asset(asset) for asset in assets}

    def selected(ref: Any, kind: str) -> SuppliedAsset | None:
        asset = _resolve_asset(ref, index)
        document = documents.get(asset.asset_id) if asset is not None else None
        return asset if type(document) is dict and document.get("document_type") == kind else None

    active_catalog = selected(plan_payload.get("artifact_family_catalog_ref"), "AGTXIV_ARTIFACT_FAMILY_CATALOG")
    active_profile = selected(plan_payload.get("agentization_profile_ref"), "AGTXIV_AGENTIZATION_PROFILE_RELEASE")
    successor_catalog = selected(plan_payload.get("stable_code_catalog_ref"), "AGTXIV_STABLE_CODE_CATALOG")
    successor_policy = selected(plan_payload.get("kernel_validation_policy_ref"), "AGTXIV_KERNEL_VALIDATION_POLICY")
    if any(asset is None for asset in (active_catalog, active_profile, successor_catalog, successor_policy)):
        return _failure("Plan does not resolve the active C and 1.1 roots", "PLAN_POLICY", code=DiagnosticCode.REF_UNRESOLVED)
    assert active_catalog and active_profile and successor_catalog and successor_policy
    new_policy = documents[successor_policy.asset_id]
    if type(new_policy) is not dict or new_policy.get("policy_version") != "1.1.0":
        return _failure("Plan kernel policy is not the 1.1 successor", "PLAN_POLICY", code=DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
    structural = new_policy.get("structural_constraints_ref", {})
    requirements = selected(structural.get("requirements_ref"), "AGTXIV_M1_CONTRACT_REQUIREMENT_SET")
    predecessor_catalog = selected(new_policy.get("predecessor_ref", {}), "AGTXIV_KERNEL_VALIDATION_POLICY")
    # The policy predecessor ref names the old policy; its code-catalog ref names the old catalog.
    predecessor_policy = predecessor_catalog
    old_policy_doc = documents.get(predecessor_policy.asset_id) if predecessor_policy is not None else None
    old_catalog = selected(old_policy_doc.get("code_catalog_ref") if type(old_policy_doc) is dict else None, "AGTXIV_STABLE_CODE_CATALOG")
    if any(asset is None for asset in (requirements, predecessor_policy, old_catalog)):
        return _failure("the predecessor D and active requirement roots are incomplete", "PLAN_POLICY", code=DiagnosticCode.REF_UNRESOLVED)
    assert requirements and predecessor_policy and old_catalog and type(old_policy_doc) is dict

    registry_ids = {entry.asset_id for entry in (_registry_entries(registry) or ())}
    root_ids = {requirements.asset_id, active_catalog.asset_id, active_profile.asset_id}
    cids = set().union(*(_referenced_asset_ids(documents[asset_id]) for asset_id in root_ids)) - root_ids - registry_ids
    c = build_catalog_profile_constraints(*(_raw_binding(asset) for asset in (requirements,active_catalog,active_profile)),tuple(asset for asset in assets if asset.asset_id in cids),registry)
    if type(c) is tuple:
        return c

    inherited = new_policy.get("inherited_registration_context_ref", {})
    inherited_catalog = selected(inherited.get("catalog_ref"), "AGTXIV_ARTIFACT_FAMILY_CATALOG")
    inherited_profile = selected(inherited.get("profile_ref"), "AGTXIV_AGENTIZATION_PROFILE_RELEASE")
    inherited_requirements = selected(inherited.get("requirements_ref"), "AGTXIV_M1_CONTRACT_REQUIREMENT_SET")
    if any(asset is None for asset in (inherited_requirements, inherited_catalog, inherited_profile)):
        return _failure("the inherited C context is incomplete", "PLAN_POLICY", code=DiagnosticCode.REF_UNRESOLVED)
    assert inherited_requirements and inherited_catalog and inherited_profile
    inherited_roots = (inherited_requirements, inherited_catalog, inherited_profile)
    inherited_ids = {asset.asset_id for asset in inherited_roots}
    inherited_support_ids = set().union(*(_referenced_asset_ids(documents[asset_id]) for asset_id in inherited_ids)) - inherited_ids - registry_ids
    inherited_c = build_catalog_profile_constraints(*(_raw_binding(asset) for asset in inherited_roots), tuple(asset for asset in assets if asset.asset_id in inherited_support_ids), registry)
    if type(inherited_c) is tuple:
        return inherited_c
    old_support_ids = {old_policy_doc["validator_ref"]["asset_id"], old_policy_doc["conformance_vector_ref"]["asset_id"]}
    d = build_kernel_validation_policy_constraints(_raw_binding(old_catalog), _raw_binding(predecessor_policy), inherited_c, tuple(asset for asset in assets if asset.asset_id in old_support_ids), registry)
    if type(d) is tuple:
        return d
    new_support_ids = {new_policy.get("validator_ref", {}).get("asset_id"), new_policy.get("conformance_vector_ref", {}).get("asset_id"), structural.get("discovery_policy_ref", {}).get("asset_id")}
    e = build_kernel_validation_policy_v1_1_constraints(_raw_binding(old_catalog), _raw_binding(predecessor_policy), _raw_binding(successor_catalog), _raw_binding(successor_policy), c, d, tuple(asset for asset in assets if asset.asset_id in new_support_ids), registry)
    if type(e) is tuple:
        return e
    return c, e

def _contains_forbidden(value: Any, active: set[int] | None = None) -> bool:
    if value is None or type(value) in (bool, int, str): return False
    if type(value) not in (dict, list): return True
    active = set() if active is None else active
    if id(value) in active: return True
    active.add(id(value))
    try:
        if type(value) is dict:
            return any(type(key) is not str or key.casefold() in _FORBIDDEN_PLAN_KEYS or _contains_forbidden(child, active) for key, child in value.items())
        return any(_contains_forbidden(child, active) for child in value)
    finally: active.remove(id(value))


def _valid_discovery_policy(policy: dict[str, Any], cparts: tuple[Any, ...]) -> bool:
    expected=(
        ("obligation:checkpoint-e/bibliography","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","BIBLIOGRAPHY",frozenset(("BIBLIOGRAPHY_TEXT","UNRESOLVED_SOURCE_REGION")),1,"IF_MATCHING_PATH_SUFFIX",(".bbl",".bib")),
        ("obligation:checkpoint-e/opaque-binary","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","OPAQUE_BINARY",frozenset(("FIGURE_BINARY","ARCHIVE_BINARY","UNRESOLVED_SOURCE_REGION")),1,"IF_MATCHING_SOURCE_MEDIA_TYPE",("text/x-tex","text/plain")),
        ("obligation:checkpoint-e/source-row-accounting","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","EVERY_SOURCE_ROW",_COMPONENT_KINDS,1,"ALWAYS",()),
        ("obligation:checkpoint-e/tex-appendix","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","TEX_APPENDIX",frozenset(("APPENDIX_TEXT","UNRESOLVED_SOURCE_REGION")),1,"IF_MATCHING_PATH_SUFFIX",(".tex",)),
        ("obligation:checkpoint-e/tex-body","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","TEX_DOCUMENT_BODY",frozenset(("DOCUMENT_TEXT","UNRESOLVED_SOURCE_REGION")),1,"IF_MATCHING_PATH_SUFFIX",(".tex",)),
        ("obligation:checkpoint-e/frozen-inventory-scope","FROZEN_INVENTORY_SCOPE","SCOPE_FREEZE","WHOLE_SOURCE_TREE",_COMPONENT_KINDS,1,"ALWAYS",()),
    )
    obligations=policy.get("obligations")
    if type(obligations) is not list or len(obligations)!=len(expected) or policy.get("applicability_vocabulary")!=["ALWAYS","IF_MATCHING_SOURCE_MEDIA_TYPE","IF_MATCHING_PATH_SUFFIX"] or policy.get("component_matching_rules")!=["SOURCE_ROW_EQUALITY","REGION_SELECTOR_MATCH","COMPONENT_KIND_ALLOWED","ANCHOR_RANGE_WITHIN_SOURCE","OVERLAP_ALLOWED_ONLY_BY_MATRIX"] or policy.get("resource_limits")!={"maximum_discovery_obligations":MAX_OBLIGATIONS,"maximum_discovery_components":MAX_COMPONENTS,"maximum_source_files":MAX_SOURCE_FILES}:return False
    selected={(item.family_id,item.stage_id) for item in cparts[6] if item.adjustment!="NOT_SELECTED"}
    for row,frozen in zip(obligations,expected):
        oid,family,stage,region,kinds,minimum,rule,operands=frozen
        if (family,stage) not in selected or row.get("obligation_id")!=oid or row.get("family_id")!=family or row.get("stage_id")!=stage or row.get("region_selector")!=region or row.get("minimum_cardinality")!=minimum or row.get("required_component_kinds")!=[kind for kind in _COMPONENT_KIND_ORDER if kind in kinds] or row.get("applicability_rule")!={"rule":rule,"operands":list(operands)}:return False
    return True


def _project_obligations(policy: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for obligation in policy["obligations"]:
        rule = obligation["applicability_rule"]; matched = []
        for row in rows:
            path, media = row["normalized_path"], row["media_type"]
            applicable = rule["rule"] == "ALWAYS" or (rule["rule"] == "IF_MATCHING_SOURCE_MEDIA_TYPE" and media in rule["operands"]) or (rule["rule"] == "IF_MATCHING_PATH_SUFFIX" and any(path.casefold().endswith(x.casefold()) for x in rule["operands"]))
            if obligation["region_selector"] == "TEX_APPENDIX": applicable = applicable and "appendix" in path.rsplit("/", 1)[-1].casefold()
            if obligation["region_selector"] == "OPAQUE_BINARY": applicable = media not in {"text/x-tex", "text/plain"}
            if applicable: matched.append(row["source_row_id"])
        if rule["rule"] != "ALWAYS" and not matched: continue
        result.append({"obligation_id": obligation["obligation_id"], "family_id": obligation["family_id"], "stage_id": obligation["stage_id"], "region_selector": obligation["region_selector"], "minimum_cardinality": obligation["minimum_cardinality"], "required_component_kinds": obligation["required_component_kinds"], "applicability_result": "APPLICABLE", "matched_source_row_ids": matched})
    return result


def _component_matches_obligation(component: dict[str,Any], obligation: dict[str,Any], row_by_id: dict[str,dict[str,Any]]) -> bool:
    row=row_by_id.get(component["source_row_id"])
    if row is None or row["source_row_id"] not in obligation["matched_source_row_ids"] or component["component_kind"] not in obligation["required_component_kinds"]:return False
    path=row["normalized_path"];media=row["media_type"];region=obligation["region_selector"]
    if region=="TEX_DOCUMENT_BODY" and not path.casefold().endswith(".tex"):return False
    if region=="TEX_APPENDIX" and (not path.casefold().endswith(".tex") or "appendix" not in path.rsplit("/",1)[-1].casefold()):return False
    if region=="BIBLIOGRAPHY" and not path.casefold().endswith((".bbl",".bib")):return False
    if region=="OPAQUE_BINARY" and media in {"text/x-tex","text/plain"}:return False
    return 0<=component["byte_start"]<=component["byte_end"]<=row["byte_size"]


def validate_agentization_plan(plan_raw: bytes, snapshot_raw: bytes, source_bytes_by_path: dict[str, bytes], supplied_contract_assets: tuple[SuppliedAsset, ...], registry: ContractSchemaRegistry, bundle_raw: bytes) -> _SealedView | tuple[Diagnostic, ...]:
    try:
        diagnostics = _preflight((plan_raw, snapshot_raw, bundle_raw), source_bytes_by_path, supplied_contract_assets)
        if diagnostics: return diagnostics
        snapshot = validate_paper_source_snapshot(snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw)
        if type(snapshot) is tuple: return snapshot
        bundle, diagnostics = _bundle(bundle_raw, registry, supplied_contract_assets)
        if diagnostics: return diagnostics
        bound, diagnostics = _parse_record(plan_raw, registry, "agtxiv.agentization-plan/1.0.0", "PLAN")
        if diagnostics: return diagnostics
        index = _asset_index(supplied_contract_assets)
        if index is None: return _failure("contract assets do not form one non-legacy namespace", "PLAN_BINDING", code=DiagnosticCode.CATALOG_REFERENCE_INVALID)
        assert bound is not None and bundle is not None
        document = bound[1]; envelope, payload = document["envelope"], document["payload"]; snap = snapshot.to_python(); rows = snap["payload"]["source_files"]
        if _contains_forbidden(document): return _failure("plan contains a query or narrowing selector", "PLAN_INDEPENDENCE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        if payload["plan_id"] != envelope["record_id"] or envelope["record_revision"] != 1 or "supersedes_ref" in envelope or not _producer_matches(envelope, bundle, "PLANNING_PRODUCER") or not _ref_equal(envelope["contract_bundle_ref"], _record_ref(bundle)) or not _ref_equal(payload["contract_bundle_ref"], _record_ref(bundle)) or not _ref_equal(payload["source_snapshot_ref"], _record_ref(snap)) or payload["source_tree_root"] != snap["payload"]["source_tree_root"] or payload["expected_source_units"] != rows:
            return _failure("plan does not exact-bind its envelope, bundle, or source snapshot", "PLAN_BINDING", code=DiagnosticCode.REF_HASH_MISMATCH)
        refs = ("artifact_family_catalog_ref", "agentization_profile_ref", "stable_code_catalog_ref", "kernel_validation_policy_ref", "discovery_policy_ref")
        resolved = {name: _resolve_asset(payload[name], index) for name in refs}
        if any(asset is None for asset in resolved.values()) or payload["resource_policy_ref"] != payload["kernel_validation_policy_ref"]:
            return _failure("plan contract refs are unresolved or resource policy is not the kernel-policy alias", "PLAN_BINDING", code=DiagnosticCode.REF_UNRESOLVED)
        constraints = _planning_constraints(supplied_contract_assets, registry, payload)
        if type(constraints) is tuple and (not constraints or type(constraints[0]) is Diagnostic): return constraints
        assert type(constraints) is tuple and len(constraints) == 2
        c_constraints, e_constraints = constraints
        cparts = _constraints_parts(c_constraints); eparts = _v11_parts(e_constraints)
        if cparts is None or eparts is None or payload["artifact_family_catalog_ref"] != cparts[1].to_python() or payload["agentization_profile_ref"] != cparts[2].to_python() or payload["stable_code_catalog_ref"] != eparts[0]["catalog"].to_python() or payload["kernel_validation_policy_ref"] != eparts[0]["policy"].to_python():
            return _failure("Plan roots differ from the sealed C/1.1 composition", "PLAN_POLICY", code=DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        policy = _parse_asset(resolved["discovery_policy_ref"])
        if policy is None or policy.get("projection_algorithm") != "AGTXIV_DISCOVERY_OBLIGATIONS_V1" or policy.get("catalog_ref") != payload["artifact_family_catalog_ref"] or policy.get("profile_ref") != payload["agentization_profile_ref"] or not _valid_discovery_policy(policy,cparts):
            return _failure("discovery policy is malformed or stale", "PLAN_POLICY", code=DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        projected = _project_obligations(policy, rows)
        if payload["profile_obligations"] != projected or len(projected) > MAX_OBLIGATIONS:
            return _failure("plan obligations differ from deterministic policy projection", "PLAN_OBLIGATIONS", code=DiagnosticCode.PROFILE_REQUIREMENT_WEAKENING)
        return _SealedView("AgentizationPlan", document, _token=_TOKEN)
    except Exception:
        return _failure("plan validation failed closed while inspecting hostile input")


def _component_identity(component: dict[str, Any], row: dict[str, Any], raw: bytes) -> tuple[str, str]:
    start, end = component["byte_start"], component["byte_end"]; path = row["normalized_path"].encode(); media = row["media_type"].encode(); row_id = row["source_row_id"].encode(); source_digest = bytes.fromhex(row["sha256"][7:]); sliced = hashlib.sha256(raw[start:end]).digest(); kind = component["component_kind"].encode()
    anchor = "sha256:" + _hash(b"AGTXIV_SOURCE_ANCHOR_V1\x00", _framed(row_id), _framed(path), _framed(media), source_digest, _u64(start), _u64(end), sliced)
    identifier = "component:sha256:" + _hash(b"AGTXIV_COMPONENT_V1\x00", _framed(row_id), _framed(path), _framed(media), source_digest, _u64(start), _u64(end), _framed(kind), sliced)
    return identifier, anchor


def validate_inventory_discovery_result(discovery_raw: bytes, plan_raw: bytes, snapshot_raw: bytes, source_bytes_by_path: dict[str, bytes], supplied_contract_assets: tuple[SuppliedAsset, ...], registry: ContractSchemaRegistry, bundle_raw: bytes) -> _SealedView | tuple[Diagnostic, ...]:
    try:
        diagnostics = _preflight((discovery_raw, plan_raw, snapshot_raw, bundle_raw), source_bytes_by_path, supplied_contract_assets)
        if diagnostics: return diagnostics
        plan = validate_agentization_plan(plan_raw, snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw)
        if type(plan) is tuple: return plan
        snapshot = validate_paper_source_snapshot(snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw)
        if type(snapshot) is tuple: return snapshot
        bundle, diagnostics = _bundle(bundle_raw, registry, supplied_contract_assets)
        if diagnostics: return diagnostics
        bound, diagnostics = _parse_record(discovery_raw, registry, "agtxiv.inventory-discovery-result/1.0.0", "DISCOVERY")
        if diagnostics: return diagnostics
        assert bound is not None and bundle is not None
        asset_index=_asset_index(supplied_contract_assets)
        if asset_index is None:return _failure("discovery evidence assets do not form one exact namespace","DISCOVERY_BINDING",code=DiagnosticCode.CATALOG_REFERENCE_INVALID)
        document = bound[1]; envelope, payload = document["envelope"], document["payload"]; pd = plan.to_python(); sd = snapshot.to_python(); expected = pd["payload"]["expected_source_units"]
        if payload["discovery_id"] != envelope["record_id"] or payload["discovery_revision"] != 1 or envelope["record_revision"] != 1 or "supersedes_ref" in envelope or payload["observed_resource_limits"] != {"maximum_discovery_components":MAX_COMPONENTS,"maximum_discovery_obligations":MAX_OBLIGATIONS} or payload["producer_context"] != envelope.get("producer_context") or not _producer_matches(envelope, bundle, "DISCOVERY_PRODUCER") or not _ref_equal(envelope["contract_bundle_ref"], _record_ref(bundle)) or not _ref_equal(payload["plan_ref"], _record_ref(pd)) or not _ref_equal(payload["source_snapshot_ref"], _record_ref(sd)) or payload["source_tree_root"] != sd["payload"]["source_tree_root"]:
            return _failure("discovery envelope or ancestry binding is stale", "DISCOVERY_BINDING", code=DiagnosticCode.REF_HASH_MISMATCH)
        coverage = payload["source_unit_coverage"]
        coverage_projection = [{key: row[key] for key in ("source_row_id", "normalized_path", "source_unit_id", "sha256", "byte_size", "media_type", "content_kind")} for row in coverage]
        if coverage_projection != expected: return _failure("discovery coverage is not the complete ordered plan denominator", "DISCOVERY_CLOSURE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        partitions = (("classified_components", "CLASSIFIED"), ("ambiguous_components", "AMBIGUOUS"), ("unclassified_components", "UNCLASSIFIED")); components = []
        for name, state in partitions:
            previous = None
            for component in payload[name]:
                key = (component["normalized_path"].encode(), component["byte_start"], component["byte_end"], component["component_id"].encode())
                if previous is not None and previous >= key: return _failure("component partitions are not strictly ordered", "DISCOVERY_COMPONENT", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
                previous = key
                if component["classification_state"] != state or len(_canonical(component)) > MAX_COMPONENT_ENTRY_BYTES or not _valid_path(component["normalized_path"]): return _failure("component state, path, or canonical size is invalid", "DISCOVERY_COMPONENT", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
                components.append(component)
        if len(components) > MAX_COMPONENTS or len({c["component_id"] for c in components}) != len(components): return _failure("component count or partition disjointness is invalid", "DISCOVERY_COMPONENT", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        row_by_id = {row["source_row_id"]: row for row in expected}; ids_by_row = {key: [] for key in row_by_id}; anchors = set()
        for component in components:
            row = row_by_id.get(component["source_row_id"])
            if row is None or any(component[key] != row[key] for key in ("source_unit_id", "normalized_path")) or type(component["byte_start"]) is not int or type(component["byte_end"]) is not int or not 0 <= component["byte_start"] <= component["byte_end"] <= row["byte_size"]:
                return _failure("component source binding or offset is invalid", "DISCOVERY_COMPONENT", code=DiagnosticCode.REF_HASH_MISMATCH)
            expected_id, anchor = _component_identity(component, row, source_bytes_by_path[row["normalized_path"]])
            anchor_kind = (row["source_row_id"], component["byte_start"], component["byte_end"], component["component_kind"])
            if component["component_id"] != expected_id or component["source_anchor_hash"] != anchor or anchor_kind in anchors or any(_resolve_asset(ref,asset_index) is None for ref in component["evidence_refs"]): return _failure("component ID, anchor, evidence, or anchor-kind uniqueness is invalid", "DISCOVERY_COMPONENT", code=DiagnosticCode.REF_HASH_MISMATCH)
            anchors.add(anchor_kind); ids_by_row[row["source_row_id"]].append(component["component_id"])
        for index,left in enumerate(components):
            for right in components[index+1:]:
                overlaps=left["source_row_id"]==right["source_row_id"] and max(left["byte_start"],right["byte_start"])<min(left["byte_end"],right["byte_end"])
                if overlaps and frozenset((left["component_kind"],right["component_kind"])) not in _ALLOWED_OVERLAP_KIND_PAIRS:return _failure("component overlap is outside the frozen kind-pair matrix","DISCOVERY_COMPONENT",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        for coverage_row in coverage:
            row_components = sorted((component_by for component_by in components if component_by["source_row_id"] == coverage_row["source_row_id"]), key=lambda c:(c["normalized_path"].encode(),c["byte_start"],c["byte_end"],c["component_id"].encode()))
            expected_ids = [component["component_id"] for component in row_components]
            if coverage_row["component_ids"] != expected_ids or not expected_ids: return _failure("coverage/component reconciliation is not bidirectionally total", "DISCOVERY_CLOSURE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        obligations = pd["payload"]["profile_obligations"]; dispositions = payload["obligation_dispositions"]
        if [x["obligation_id"] for x in dispositions] != [x["obligation_id"] for x in obligations]: return _failure("obligation dispositions do not mirror the plan", "DISCOVERY_OBLIGATION", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        component_by_id = {c["component_id"]: c for c in components}; errors=payload["discovery_errors"];error_ids = [e["error_id"] for e in errors]
        if error_ids!=sorted(error_ids,key=str.encode) or len(error_ids) != len(set(error_ids)) or any(len({ref["asset_id"] for ref in error["evidence_refs"]})!=len(error["evidence_refs"]) or any(_resolve_asset(ref,asset_index) is None for ref in error["evidence_refs"]) for error in errors): return _failure("discovery errors are unordered, duplicated, or have unresolved evidence", "DISCOVERY_CLOSURE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        error_set=set(error_ids);errors_by_id={error["error_id"]:error for error in errors};referenced_errors=set();coverage_by_row={row["source_row_id"]:row for row in coverage}
        for obligation, disposition in zip(obligations, dispositions):
            matched=set(obligation["matched_source_row_ids"])
            relevant=[component for component in components if _component_matches_obligation(component,obligation,row_by_id)]
            relevant.sort(key=lambda c:(c["normalized_path"].encode(),c["byte_start"],c["byte_end"],c["component_id"].encode()))
            if disposition["component_ids"] != [component["component_id"] for component in relevant] or len(disposition["component_ids"]) != len(set(disposition["component_ids"])):
                return _failure("disposition is not the complete ordered matching component set", "DISCOVERY_OBLIGATION", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
            refs=disposition["finding_or_error_refs"]
            if len(refs)!=len(set(refs)) or any(ref not in error_set for ref in refs): return _failure("disposition evidence is duplicate or unresolved", "DISCOVERY_OBLIGATION", code=DiagnosticCode.REF_UNRESOLVED)
            referenced_errors.update(refs);status=disposition["status"]
            classified=[component for component in relevant if component["classification_state"]=="CLASSIFIED"]
            if obligation["region_selector"]=="EVERY_SOURCE_ROW":
                satisfied=all(sum(component["source_row_id"]==row_id for component in classified)>=obligation["minimum_cardinality"] for row_id in matched)
            else:satisfied=len(classified)>=obligation["minimum_cardinality"]
            if status=="SATISFIED" and (not satisfied or refs):return _failure("SATISFIED disposition does not meet exact cardinality or carries error evidence", "DISCOVERY_OBLIGATION", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
            if status=="AMBIGUOUS" and not any(component["classification_state"]=="AMBIGUOUS" for component in relevant):return _failure("AMBIGUOUS disposition lacks matching ambiguous material", "DISCOVERY_OBLIGATION", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
            if status=="UNCLASSIFIED" and not any(component["classification_state"]=="UNCLASSIFIED" for component in relevant):return _failure("UNCLASSIFIED disposition lacks matching unclassified material", "DISCOVERY_OBLIGATION", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
            if status=="BLOCKED":
                fallbacks=[component for component in relevant if component["component_kind"]=="UNRESOLVED_SOURCE_REGION" and component["classification_state"] in {"AMBIGUOUS","UNCLASSIFIED"}]
                affected_rows=[coverage_by_row[row_id] for row_id in matched if coverage_by_row[row_id]["coverage_status"]=="BLOCKED_WITH_EVIDENCE"]
                fallback_ids={component["component_id"] for component in fallbacks};affected_component_ids={component_id for row in affected_rows for component_id in row["component_ids"]}
                linked=True
                for component in fallbacks:
                    component_errors=[errors_by_id[ref] for ref in refs if errors_by_id[ref]["error_code"]==component["classification_or_issue_code"] and errors_by_id[ref]["evidence_refs"]==component["evidence_refs"]]
                    if not component["evidence_refs"] or not component_errors:linked=False
                for ref in refs:
                    error=errors_by_id[ref]
                    if not any(component["classification_or_issue_code"]==error["error_code"] and component["evidence_refs"]==error["evidence_refs"] for component in fallbacks):linked=False
                if satisfied or not refs or not fallbacks or not affected_rows or fallback_ids-set(disposition["component_ids"]) or fallback_ids-affected_component_ids or any(not fallback_ids.intersection(row["component_ids"]) for row in affected_rows) or not linked:return _failure("BLOCKED disposition lacks exact affected rows, unresolved fallbacks, or bidirectional error/evidence closure", "DISCOVERY_OBLIGATION", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        if error_set != referenced_errors: return _failure("discovery contains dangling or multiply external errors", "DISCOVERY_CLOSURE", code=DiagnosticCode.REF_UNRESOLVED)
        for coverage_row in coverage:
            if coverage_row["coverage_status"]=="BLOCKED_WITH_EVIDENCE":
                unresolved=[component_by_id[cid] for cid in coverage_row["component_ids"] if component_by_id[cid]["component_kind"]=="UNRESOLVED_SOURCE_REGION" and component_by_id[cid]["classification_state"] in {"AMBIGUOUS","UNCLASSIFIED"}]
                linked=any(disposition["finding_or_error_refs"] and any(component["component_id"] in disposition["component_ids"] for component in unresolved) for disposition in dispositions)
                if not unresolved or not linked:return _failure("blocked coverage lacks a linked unresolved fallback component", "DISCOVERY_CLOSURE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        return _SealedView("InventoryDiscoveryResult", document, _token=_TOKEN)
    except Exception:
        return _failure("discovery validation failed closed while inspecting hostile input")


def validate_scope_freeze_decision(decision_raw: bytes, discovery_raw: bytes, plan_raw: bytes, snapshot_raw: bytes, source_bytes_by_path: dict[str, bytes], supplied_contract_assets: tuple[SuppliedAsset, ...], registry: ContractSchemaRegistry, bundle_raw: bytes) -> _SealedView | tuple[Diagnostic, ...]:
    try:
        diagnostics = _preflight((decision_raw, discovery_raw, plan_raw, snapshot_raw, bundle_raw), source_bytes_by_path, supplied_contract_assets)
        if diagnostics: return diagnostics
        discovery = validate_inventory_discovery_result(discovery_raw, plan_raw, snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw)
        if type(discovery) is tuple: return discovery
        plan = validate_agentization_plan(plan_raw, snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw); snapshot = validate_paper_source_snapshot(snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw)
        if type(plan) is tuple: return plan
        if type(snapshot) is tuple: return snapshot
        bundle, diagnostics = _bundle(bundle_raw, registry, supplied_contract_assets)
        if diagnostics: return diagnostics
        bound, diagnostics = _parse_record(decision_raw, registry, "agtxiv.scope-freeze-decision/1.0.0", "SCOPE_DECISION")
        if diagnostics: return diagnostics
        assert bound is not None and bundle is not None
        document = bound[1]; envelope, payload = document["envelope"], document["payload"]; dd = discovery.to_python(); pd = plan.to_python(); sd = snapshot.to_python()
        if payload["decision_id"] != envelope["record_id"] or payload["decision_revision"] != 1 or envelope["record_revision"] != 1 or "supersedes_ref" in envelope or payload["source_tree_root"] != sd["payload"]["source_tree_root"] or payload["review_policy_ref"] != pd["payload"]["kernel_validation_policy_ref"] or payload["reviewer"] != envelope.get("producer_context", {}).get("producer") or payload["reviewer_role"] != envelope.get("producer_context", {}).get("role") or not _producer_matches(envelope, bundle, "SCOPE_FREEZE_REVIEWER") or not _ref_equal(envelope["contract_bundle_ref"], _record_ref(bundle)) or not _ref_equal(payload["plan_ref"], _record_ref(pd)) or not _ref_equal(payload["discovery_ref"], _record_ref(dd)) or not _ref_equal(payload["source_snapshot_ref"], _record_ref(sd)):
            return _failure("decision envelope, actors, or ancestry refs are inconsistent", "DECISION_BINDING", code=DiagnosticCode.REF_HASH_MISMATCH)
        producer_id = dd["payload"]["producer_context"]["producer"]["actor_id"]; reviewer_id = payload["reviewer"]["actor_id"]
        producer=dd["payload"]["producer_context"]["producer"]
        if producer_id == reviewer_id or payload["producer_actor_ref"] != producer or dd["payload"]["producer_context"]["role"] == payload["reviewer_role"] or payload["independence_declaration"] != "STRUCTURALLY_DISTINCT_ACTOR_IDS_DECLARED": return _failure("reviewer and discovery producer must have distinct exactly bound identities and roles", "DECISION_INDEPENDENCE", code=DiagnosticCode.CATALOG_PRODUCER_ROLE_NOT_ALLOWED)
        declarations = payload["conflict_declarations"];categories=[row["category"] for row in declarations];expected_categories=["IDENTITY","ORGANIZATIONAL_CONTROL","BENEFICIAL_OWNERSHIP","OTHER"]
        if categories!=expected_categories or any(row["producer_actor_id"] != producer_id or row["reviewer_actor_id"] != reviewer_id for row in declarations): return _failure("conflict declarations do not form the complete ordered actor-pair declaration", "DECISION_INDEPENDENCE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        findings=payload["findings"]
        if len(findings) > MAX_FINDINGS: return _failure("review findings exceed limit", "DECISION_PREFLIGHT", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        if [row["finding_id"] for row in findings] != sorted((row["finding_id"] for row in findings),key=str.encode) or len({row["finding_id"] for row in findings})!=len(findings):return _failure("findings are not uniquely UTF-8 ordered", "DECISION_FINDING", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        subjects={"PLAN":{pd["envelope"]["record_id"]},"DISCOVERY":{dd["envelope"]["record_id"]},"SOURCE_UNIT":{row["source_unit_id"] for row in pd["payload"]["expected_source_units"]},"COMPONENT":{component["component_id"] for name in ("classified_components","ambiguous_components","unclassified_components") for component in dd["payload"][name]},"OBLIGATION":{row["obligation_id"] for row in pd["payload"]["profile_obligations"]},"ACTOR_DECLARATION":set(expected_categories)}
        if any(row["subject_id"] not in subjects[row["subject_kind"]] for row in findings):return _failure("finding subject does not resolve in exact decision ancestry", "DECISION_FINDING", code=DiagnosticCode.REF_UNRESOLVED)
        conflicts = [row for row in declarations if row["disposition"] == "CONFLICT_DECLARED"]; blocking = [row for row in findings if row["severity"] == "BLOCKING"]
        if any(not any(finding["subject_kind"]=="ACTOR_DECLARATION" and finding["subject_id"]==conflict["category"] for finding in findings) for conflict in conflicts):return _failure("declared conflict lacks a bound finding", "DECISION_INDEPENDENCE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        expected_terminal={"obligation_key":"obligation:checkpoint-e/frozen-inventory-scope","reason_code":"AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED","family_id":"FROZEN_INVENTORY_SCOPE","stage_id":"SCOPE_FREEZE","outcome":"BLOCKED","context_mode":"PLAN_BOUND"}
        if payload["decision"] == "ACCEPT" and (conflicts or blocking or "terminal_requirement" in payload or any(row["status"]!="SATISFIED" for row in dd["payload"]["obligation_dispositions"])): return _failure("ACCEPT has conflict, blocking/incomplete discovery, or terminal requirement", "DECISION_BRANCH", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        if payload["decision"] == "BLOCK" and (not blocking or payload.get("terminal_requirement")!=expected_terminal): return _failure("BLOCK requires a blocking finding and exact typed terminal requirement", "DECISION_BRANCH", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        return _SealedView("ScopeFreezeDecision", document, _token=_TOKEN)
    except Exception:
        return _failure("decision validation failed closed while inspecting hostile input")


def _scope_entry(scope_id: str, component: dict[str, Any]) -> dict[str, Any]:
    row_id = component["source_row_id"].encode(); path = component["normalized_path"].encode(); cid = component["component_id"].encode()
    return {"scope_entry_id": "scope-entry:sha256:" + _hash(b"AGTXIV_SCOPE_ENTRY_V1\x00", _framed(scope_id.encode()), _framed(row_id), _framed(path), _framed(cid)), "component_id": component["component_id"], "source_row_id": component["source_row_id"], "source_unit_id": component["source_unit_id"], "normalized_path": component["normalized_path"], "byte_start": component["byte_start"], "byte_end": component["byte_end"], "component_kind": component["component_kind"], "scope_state": component["classification_state"], "source_anchor_hash": component["source_anchor_hash"]}


def _scope_delta(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> dict[str, list[str]]:
    before = {x["scope_entry_id"]: x for x in old}; after = {x["scope_entry_id"]: x for x in new}; common = before.keys() & after.keys()
    binding = ("component_id", "source_row_id", "source_unit_id", "normalized_path", "byte_start", "byte_end", "component_kind", "source_anchor_hash")
    return {"added_entry_ids": sorted(after.keys() - before.keys(), key=str.encode), "removed_entry_ids": sorted(before.keys() - after.keys(), key=str.encode), "classification_changed_entry_ids": sorted((x for x in common if before[x]["scope_state"] != after[x]["scope_state"]), key=str.encode), "source_binding_changed_entry_ids": sorted((x for x in common if any(before[x][k] != after[x][k] for k in binding)), key=str.encode)}


def _validate_frozen_inventory_scope_current(scope_raw: bytes, decision_raw: bytes, discovery_raw: bytes, plan_raw: bytes, snapshot_raw: bytes, source_bytes_by_path: dict[str, bytes], supplied_contract_assets: tuple[SuppliedAsset, ...], registry: ContractSchemaRegistry, bundle_raw: bytes, predecessor_scope_raw: bytes | None = None, predecessor_plan_raw: bytes | None = None, predecessor_snapshot_raw: bytes | None = None) -> _SealedView | tuple[Diagnostic, ...]:
    try:
        predecessor_raws=(predecessor_scope_raw,predecessor_plan_raw,predecessor_snapshot_raw)
        if any(raw is None for raw in predecessor_raws) and any(raw is not None for raw in predecessor_raws):return _failure("successor validation requires the complete predecessor scope/Plan/snapshot input","SCOPE_HISTORY")
        raws = (scope_raw, decision_raw, discovery_raw, plan_raw, snapshot_raw, bundle_raw) + (() if predecessor_scope_raw is None else predecessor_raws)
        diagnostics = _preflight(raws, source_bytes_by_path, supplied_contract_assets)
        if diagnostics: return diagnostics
        decision = validate_scope_freeze_decision(decision_raw, discovery_raw, plan_raw, snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw)
        if type(decision) is tuple: return decision
        if decision.to_python()["payload"]["decision"] != "ACCEPT": return _failure("a BLOCK decision cannot issue a frozen scope", "SCOPE_ISSUANCE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        discovery = validate_inventory_discovery_result(discovery_raw, plan_raw, snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw); plan = validate_agentization_plan(plan_raw, snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw); snapshot = validate_paper_source_snapshot(snapshot_raw, source_bytes_by_path, supplied_contract_assets, registry, bundle_raw); bundle, diagnostics = _bundle(bundle_raw, registry, supplied_contract_assets)
        for item in (discovery, plan, snapshot):
            if type(item) is tuple: return item
        if diagnostics: return diagnostics
        bound, diagnostics = _parse_record(scope_raw, registry, "agtxiv.frozen-inventory-scope/1.0.0", "FROZEN_SCOPE")
        if diagnostics: return diagnostics
        assert bound is not None and bundle is not None and type(discovery) is _SealedView and type(plan) is _SealedView and type(snapshot) is _SealedView
        document = bound[1]; envelope, payload = document["envelope"], document["payload"]; dd, pd, sd, dec = discovery.to_python(), plan.to_python(), snapshot.to_python(), decision.to_python()
        if not _producer_matches(envelope, bundle, "SCOPE_FREEZE_ISSUER") or payload["source_tree_root"] != sd["payload"]["source_tree_root"] or not all((_ref_equal(envelope["contract_bundle_ref"], _record_ref(bundle)), _ref_equal(payload["plan_ref"], _record_ref(pd)), _ref_equal(payload["discovery_ref"], _record_ref(dd)), _ref_equal(payload["accept_decision_ref"], _record_ref(dec)), _ref_equal(payload["source_snapshot_ref"], _record_ref(sd)))):
            return _failure("scope exact ancestry or bundle binding is stale", "SCOPE_BINDING", code=DiagnosticCode.REF_HASH_MISMATCH)
        components = sum((dd["payload"][name] for name in ("classified_components", "ambiguous_components", "unclassified_components")), [])
        expected = [_scope_entry(payload["scope_id"], component) for component in sorted(components, key=lambda c:(c["normalized_path"].encode(),c["byte_start"],c["byte_end"],c["component_id"].encode()))]
        if len(payload["scope_entries"]) > MAX_SCOPE_ENTRIES or payload["scope_entries"] != expected or any(not _valid_path(entry["normalized_path"]) for entry in payload["scope_entries"]): return _failure("scope entries do not retain every discovery component exactly once with valid paths", "SCOPE_CLOSURE", code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        if predecessor_scope_raw is None:
            seed = _framed(pd["payload"]["plan_id"].encode()) + _framed(sd["payload"]["snapshot_id"].encode()); scope_id = "inventory-scope:sha256:" + _hash(b"AGTXIV_SCOPE_ID_V1\x00", seed)
            expected_delta = {"kind":"GENESIS","added_entry_ids":[],"removed_entry_ids":[],"classification_changed_entry_ids":[],"source_binding_changed_entry_ids":[]}
            if payload["scope_revision"] != 1 or payload["scope_id"] != scope_id or "predecessor_scope_ref" in payload or "supersedes_ref" in envelope or payload["revision_delta"] != expected_delta:
                return _failure("genesis scope identity or delta is invalid", "SCOPE_REVISION", code=DiagnosticCode.RECORD_SUPERSESSION_MISMATCH)
        else:
            predecessor_bound, diagnostics = _parse_record(predecessor_scope_raw, registry, "agtxiv.frozen-inventory-scope/1.0.0", "SCOPE_PREDECESSOR")
            if diagnostics: return diagnostics
            assert predecessor_bound is not None
            predecessor = predecessor_bound[1];previous_plan_parsed=parse_canonical_json(predecessor_plan_raw);previous_snapshot_parsed=parse_canonical_json(predecessor_snapshot_raw)
            if type(previous_plan_parsed) is not ParsedCanonicalValue or type(previous_snapshot_parsed) is not ParsedCanonicalValue:return _failure("validated predecessor Plan or snapshot cannot be recovered","SCOPE_HISTORY",code=DiagnosticCode.REF_HASH_MISMATCH)
            previous_plan=previous_plan_parsed.to_python();previous_snapshot=previous_snapshot_parsed.to_python();expected_delta = {"kind":"SUCCESSOR", **_scope_delta(predecessor["payload"]["scope_entries"], expected)}
            stable_profile=pd["payload"]["agentization_profile_ref"]==previous_plan["payload"]["agentization_profile_ref"]
            stable_paper=sd["payload"]["source_origin_kind"]==previous_snapshot["payload"]["source_origin_kind"] and sd["payload"]["source_label"]==previous_snapshot["payload"]["source_label"]
            if payload["scope_id"] != predecessor["payload"]["scope_id"] or payload["scope_revision"] != predecessor["payload"]["scope_revision"] + 1 or not stable_profile or not stable_paper or envelope["contract_bundle_ref"]!=predecessor["envelope"]["contract_bundle_ref"] or not _ref_equal(payload.get("predecessor_scope_ref"), _record_ref(predecessor)) or not _ref_equal(envelope.get("supersedes_ref"), _record_ref(predecessor)) or payload["revision_delta"] != expected_delta or not any(expected_delta[key] for key in expected_delta if key != "kind") or expected_delta["source_binding_changed_entry_ids"]:
                return _failure("successor lineage or mechanical revision delta is invalid", "SCOPE_REVISION", code=DiagnosticCode.RECORD_SUPERSESSION_MISMATCH)
        expected_record_id = f"inventory-scope-record:sha256:{payload['scope_id'].rsplit(':',1)[-1]}/revision/{payload['scope_revision']}"
        if envelope["record_id"] != expected_record_id or envelope["record_revision"] != payload["scope_revision"]: return _failure("scope record ID/revision projection is invalid", "SCOPE_REVISION", code=DiagnosticCode.RECORD_SUPERSESSION_MISMATCH)
        return _SealedView("FrozenInventoryScope", document, _token=_TOKEN)
    except Exception:
        return _failure("scope validation failed closed while inspecting hostile input")


def _validated_predecessor_history(predecessor_history: tuple[PlanningScopeChainDeclaration,...],registry: ContractSchemaRegistry):
    if type(predecessor_history) is not tuple or len(predecessor_history)>MAX_PREDECESSOR_DECLARATIONS or any(type(item) is not PlanningScopeChainDeclaration for item in predecessor_history):return _failure("predecessor history requires at most 256 exact sealed declarations","SCOPE_HISTORY")
    validated=[];previous_raw=None;previous_plan_raw=None;previous_snapshot_raw=None;seen=set();baseline_assets=None;baseline_bundle=None
    for index,declaration in enumerate(predecessor_history):
        parts=_declaration_parts(declaration)
        if parts is None:return _failure("predecessor declaration failed seal integrity","SCOPE_HISTORY")
        records,source_rows,assets=parts;snapshot_raw,plan_raw,discovery_raw,decision_raw,scope_raw,bundle_raw=records;sources=dict(source_rows)
        if baseline_assets is None:baseline_assets=assets;baseline_bundle=bundle_raw
        if assets!=baseline_assets or bundle_raw!=baseline_bundle:return _failure("predecessor declarations do not share one exact bundle namespace","SCOPE_HISTORY",code=DiagnosticCode.REF_HASH_MISMATCH)
        scope=_validate_frozen_inventory_scope_current(scope_raw,decision_raw,discovery_raw,plan_raw,snapshot_raw,sources,assets,registry,bundle_raw,previous_raw,previous_plan_raw,previous_snapshot_raw)
        if type(scope) is tuple:return scope
        document=scope.to_python();identity=_canonical(_record_ref(document))
        if identity in seen or document["payload"]["scope_revision"]!=index+1:return _failure("predecessor history is duplicated, reordered, or incomplete","SCOPE_HISTORY",code=DiagnosticCode.RECORD_SUPERSESSION_MISMATCH)
        seen.add(identity);validated.append((declaration,document,records,assets));previous_raw=scope_raw;previous_plan_raw=plan_raw;previous_snapshot_raw=snapshot_raw
    return validated


def validate_frozen_inventory_scope(scope_raw: bytes, decision_raw: bytes, discovery_raw: bytes, plan_raw: bytes, snapshot_raw: bytes, source_bytes_by_path: dict[str, bytes], supplied_contract_assets: tuple[SuppliedAsset, ...], registry: ContractSchemaRegistry, bundle_raw: bytes, predecessor_history: tuple[PlanningScopeChainDeclaration,...]) -> _SealedView | tuple[Diagnostic,...]:
    try:
        if type(predecessor_history) is not tuple:return _failure("predecessor history requires an exact tuple","SCOPE_HISTORY")
        declaration_bytes=0
        for declaration in predecessor_history:
            fields=_declaration_fields(declaration)
            if fields is None:return _failure("predecessor declaration failed exact type integrity","SCOPE_HISTORY")
            records,sources,assets,_=fields;declaration_bytes+=sum(map(len,records))+sum(len(raw) for _,raw in sources)+sum(len(asset.raw_bytes) for asset in assets)
        current_bytes=sum(map(len,(scope_raw,decision_raw,discovery_raw,plan_raw,snapshot_raw,bundle_raw)))+sum(len(raw) for raw in source_bytes_by_path.values())+sum(len(asset.raw_bytes) for asset in supplied_contract_assets) if type(source_bytes_by_path) is dict and type(supplied_contract_assets) is tuple else MAX_AGGREGATE_INPUT_BYTES+1
        if declaration_bytes+current_bytes>MAX_AGGREGATE_INPUT_BYTES:return _failure("current chain plus predecessor history exceeds aggregate input limit","SCOPE_HISTORY",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        history=_validated_predecessor_history(predecessor_history,registry)
        if type(history) is tuple and (not history or type(history[0]) is Diagnostic):return history
        previous_raw=history[-1][2][4] if history else None;previous_plan_raw=history[-1][2][1] if history else None;previous_snapshot_raw=history[-1][2][0] if history else None
        if history and (history[-1][3]!=supplied_contract_assets or history[-1][2][5]!=bundle_raw):return _failure("current scope bundle namespace differs from predecessor history","SCOPE_HISTORY",code=DiagnosticCode.REF_HASH_MISMATCH)
        result=_validate_frozen_inventory_scope_current(scope_raw,decision_raw,discovery_raw,plan_raw,snapshot_raw,source_bytes_by_path,supplied_contract_assets,registry,bundle_raw,previous_raw,previous_plan_raw,previous_snapshot_raw)
        if type(result) is tuple:return result
        revision=result.to_python()["payload"]["scope_revision"]
        if len(predecessor_history)!=revision-1:return _failure("scope revision requires the complete oldest-to-immediate predecessor history","SCOPE_HISTORY",code=DiagnosticCode.RECORD_SUPERSESSION_MISMATCH)
        return result
    except Exception:return _failure("scope history validation failed closed","SCOPE_HISTORY")


@dataclass(frozen=True, slots=True)
class _LineageNode:
    record_id: str; record_type: str; scope_ref: bytes; coverage_mode: str; exact_input_entry_ids: tuple[str, ...]; exact_output_entry_ids: tuple[str, ...]
@dataclass(frozen=True, slots=True)
class _LineageEdge:
    producer_record_id: str; consumer_record_id: str; relation: str


class ScopeRevisionLineageProjection:
    __slots__ = ("__nodes", "__edges", "__seal", "__token")
    def __init__(self, nodes: tuple[tuple[Any, ...], ...], edges: tuple[tuple[Any, ...], ...], *, _token: object = None):
        if _token is not _TOKEN: raise TypeError("use ScopeRevisionLineageProjection.build")
        frozen_nodes = tuple(_LineageNode(*node) for node in nodes); frozen_edges = tuple(_LineageEdge(*edge) for edge in edges); raw = repr((frozen_nodes, frozen_edges)).encode()
        object.__setattr__(self,"_ScopeRevisionLineageProjection__nodes",frozen_nodes);object.__setattr__(self,"_ScopeRevisionLineageProjection__edges",frozen_edges);object.__setattr__(self,"_ScopeRevisionLineageProjection__seal",hashlib.sha256(raw).digest());object.__setattr__(self,"_ScopeRevisionLineageProjection__token",_TOKEN)
    @classmethod
    def build(cls, nodes: tuple[tuple[Any, ...], ...], edges: tuple[tuple[Any, ...], ...]) -> "ScopeRevisionLineageProjection" | tuple[Diagnostic, ...]:
        try:
            if type(nodes) is not tuple or type(edges) is not tuple or any(type(x) is not tuple or len(x)!=6 for x in nodes) or any(type(x) is not tuple or len(x)!=3 for x in edges): return _failure("lineage builder requires exact closed tuples", "LINEAGE_INPUT")
            if any(type(x[0]) is not str or type(x[1]) is not str or type(x[2]) is not bytes or type(x[3]) is not str or type(x[4]) is not tuple or type(x[5]) is not tuple or any(type(v) is not str for v in (*x[4],*x[5])) for x in nodes) or any(any(type(v) is not str for v in x) for x in edges): return _failure("lineage fields require exact strings, bytes, and tuples", "LINEAGE_INPUT")
            return cls(nodes, edges, _token=_TOKEN)
        except Exception:return _failure("lineage builder failed closed", "LINEAGE_INPUT")
    def __setattr__(self,n,v)->Never:raise AttributeError("lineage projection is immutable")


def _lineage_parts(value: Any):
    if type(value) is not ScopeRevisionLineageProjection:return None
    try:nodes=object.__getattribute__(value,"_ScopeRevisionLineageProjection__nodes");edges=object.__getattribute__(value,"_ScopeRevisionLineageProjection__edges");seal=object.__getattribute__(value,"_ScopeRevisionLineageProjection__seal");token=object.__getattribute__(value,"_ScopeRevisionLineageProjection__token");raw=repr((nodes,edges)).encode()
    except Exception:return None
    return (nodes,edges) if token is _TOKEN and type(nodes) is tuple and type(edges) is tuple and seal==hashlib.sha256(raw).digest() else None


def compute_scope_revision_impact(predecessor_history: tuple[PlanningScopeChainDeclaration,...], successor_declaration: PlanningScopeChainDeclaration, downstream_records: tuple[bytes, ...], lineage_projection: ScopeRevisionLineageProjection, registry: ContractSchemaRegistry) -> ScopeRevisionImpact | tuple[Diagnostic, ...]:
    try:
        if type(predecessor_history) is not tuple or not predecessor_history or len(predecessor_history)>MAX_PREDECESSOR_DECLARATIONS or type(successor_declaration) is not PlanningScopeChainDeclaration or successor_declaration in predecessor_history or type(downstream_records) is not tuple or any(type(raw) is not bytes for raw in downstream_records):return _failure("impact requires nonempty exact predecessor history, a distinct successor declaration, and exact downstream bytes","LINEAGE_INPUT")
        predecessor_fields=[_declaration_fields(item) for item in predecessor_history];successor_fields=_declaration_fields(successor_declaration)
        if any(fields is None for fields in predecessor_fields) or successor_fields is None:return _failure("impact declaration failed exact type integrity","LINEAGE_INPUT")
        records,source_rows,supplied_contract_assets,_=successor_fields;snapshot_raw,plan_raw,discovery_raw,decision_raw,successor_scope_raw,bundle_raw=records
        aggregate=sum(len(raw) for raw in downstream_records)+sum(sum(map(len,fields[0]))+sum(len(raw) for _,raw in fields[1])+sum(len(asset.raw_bytes) for asset in fields[2]) for fields in predecessor_fields)+sum(map(len,records))+sum(len(raw) for _,raw in source_rows)+sum(len(asset.raw_bytes) for asset in supplied_contract_assets)
        if aggregate>MAX_AGGREGATE_INPUT_BYTES:return _failure("impact declarations and downstream records exceed aggregate limit","LINEAGE_INPUT",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        parts=_lineage_parts(lineage_projection)
        if parts is None:return _failure("lineage projection failed exact type/seal integrity","LINEAGE_INPUT")
        history=_validated_predecessor_history(predecessor_history,registry)
        if type(history) is tuple:return history
        if _declaration_parts(successor_declaration) is None:return _failure("successor declaration failed seal integrity","LINEAGE_INPUT")
        successor=validate_frozen_inventory_scope(successor_scope_raw,decision_raw,discovery_raw,plan_raw,snapshot_raw,dict(source_rows),supplied_contract_assets,registry,bundle_raw,predecessor_history)
        if type(successor) is tuple:return successor
        old=history[-1][1];new=successor.to_python();delta=new["payload"]["revision_delta"]
        bundle,ds=_bundle(bundle_raw,registry,supplied_contract_assets)
        if ds:return ds
        assert bundle is not None
        bundle_ref=_record_ref(bundle)
        mechanical={"kind":"SUCCESSOR",**_scope_delta(old["payload"]["scope_entries"],new["payload"]["scope_entries"])}
        if new["payload"].get("predecessor_scope_ref")!=_record_ref(old) or new["envelope"].get("supersedes_ref")!=_record_ref(old) or delta!=mechanical:return _failure("scope revisions fail exact validated successor semantics","LINEAGE_SCOPE",code=DiagnosticCode.RECORD_SUPERSESSION_MISMATCH)
        allowed={"agtxiv.checkpoint-e-entry-output/1.0.0","agtxiv.checkpoint-e-whole-scope-output/1.0.0","agtxiv.checkpoint-e-derived-output/1.0.0"}; docs=[]
        for raw in downstream_records:
            parsed=parse_canonical_json(raw)
            if type(parsed) is not ParsedCanonicalValue or canonical_bytes(parsed)!=raw:return _failure("downstream record is not canonical","LINEAGE_RECORD",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
            doc=parsed.to_python();rtype=doc.get("envelope",{}).get("record_type")
            if rtype not in allowed or doc.get("envelope",{}).get("contract_bundle_ref")!=bundle_ref or validate_immutable_record_payload(parsed,registry):return _failure("downstream record type/schema or bundle binding is unsupported","LINEAGE_RECORD",code=DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH)
            docs.append(doc)
        nodes,edges=parts
        if len(nodes)!=len(docs) or len({n.record_id for n in nodes})!=len(nodes):return _failure("lineage node set is incomplete or duplicated","LINEAGE_GRAPH",code=DiagnosticCode.REF_UNRESOLVED)
        doc_by_id={d["envelope"]["record_id"]:d for d in docs};old_ref=_record_ref(old);old_ids={e["scope_entry_id"] for e in old["payload"]["scope_entries"]}
        for node in nodes:
            doc=doc_by_id.get(node.record_id)
            if doc is None:return _failure("lineage contains an invented node","LINEAGE_GRAPH",code=DiagnosticCode.REF_UNRESOLVED)
            p=doc["payload"];expected=(doc["envelope"]["record_id"],doc["envelope"]["record_type"],_canonical(p["scope_ref"]),p["coverage_mode"],tuple(p["input_entry_ids"]),tuple(p["output_entry_ids"]))
            actual=(node.record_id,node.record_type,node.scope_ref,node.coverage_mode,node.exact_input_entry_ids,node.exact_output_entry_ids)
            inputs=node.exact_input_entry_ids;outputs=node.exact_output_entry_ids
            ordered=lambda values: values==tuple(sorted(values,key=str.encode)) and len(values)==len(set(values))
            derived=node.record_type=="agtxiv.checkpoint-e-derived-output/1.0.0"
            if expected!=actual or p["scope_ref"]!=old_ref or node.coverage_mode not in {"ENTRY_SET","WHOLE_SCOPE"} or (node.coverage_mode=="WHOLE_SCOPE")!=(not inputs) or not ordered(inputs) or not ordered(outputs) or not set(inputs)<=old_ids or not set(outputs)<=old_ids or (derived and outputs) or (not derived and not outputs):return _failure("lineage projection differs from record-specific semantic extraction","LINEAGE_GRAPH",code=DiagnosticCode.REF_HASH_MISMATCH)
        ids=set(doc_by_id);adj={x:set() for x in ids};indegree={x:0 for x in ids};seen=set()
        for edge in edges:
            key=(edge.producer_record_id,edge.consumer_record_id)
            if edge.relation!="DERIVED_FROM" or key in seen or key[0]==key[1] or not set(key)<=ids:return _failure("lineage edge is duplicate, self, dangling, or mistyped","LINEAGE_GRAPH",code=DiagnosticCode.REF_UNRESOLVED)
            seen.add(key);adj[key[0]].add(key[1]);indegree[key[1]]+=1
        ready=sorted((x for x in ids if indegree[x]==0),key=str.encode);top=[]
        while ready:
            current=ready.pop(0);top.append(current)
            for child in sorted(adj[current],key=str.encode):
                indegree[child]-=1
                if indegree[child]==0:ready.append(child);ready.sort(key=str.encode)
        if len(top)!=len(ids):return _failure("lineage graph contains a directed cycle","LINEAGE_GRAPH",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
        changed=set(delta["removed_entry_ids"]+delta["classification_changed_entry_ids"]+delta["source_binding_changed_entry_ids"]);any_delta=any(delta[k] for k in ("added_entry_ids","removed_entry_ids","classification_changed_entry_ids","source_binding_changed_entry_ids"))
        direct={n.record_id for n in nodes if (n.coverage_mode=="WHOLE_SCOPE" and any_delta) or (n.coverage_mode=="ENTRY_SET" and bool(set(n.exact_input_entry_ids)&changed))};affected=set(direct)
        for current in top:
            if current in affected:affected.update(adj[current])
        result={"predecessor_scope_ref":old_ref,"successor_scope_ref":_record_ref(new),"direct_changed_entry_ids":sorted(changed|set(delta["added_entry_ids"]),key=str.encode),"directly_affected_record_ids":sorted(direct,key=str.encode),"transitively_affected_record_ids":sorted(affected-direct,key=str.encode),"affected_whole_scope_output_ids":sorted((n.record_id for n in nodes if n.coverage_mode=="WHOLE_SCOPE" and n.record_id in affected),key=str.encode),"unaffected_record_ids":sorted(ids-affected,key=str.encode),"topological_order":top}
        return _SealedView("ScopeRevisionImpact",result,_token=_TOKEN)
    except Exception:return _failure("revision impact failed closed while inspecting hostile input","LINEAGE_INPUT")


def validate_planning_terminal_constraints(record: ParsedCanonicalValue, registry: ContractSchemaRegistry, catalog_profile_constraints: CatalogProfileConstraints, kernel_policy_v1_1_constraints: KernelValidationPolicyV11Constraints, plan_raw: bytes, discovery_raw: bytes, decision_raw: bytes, supplied_contract_assets: tuple[SuppliedAsset, ...], bundle_raw: bytes) -> tuple[Diagnostic, ...]:
    """Preflight, call C/B once, call the sealed 1.1 gate once, then bind E."""
    if type(record) is not ParsedCanonicalValue or type(registry) is not ContractSchemaRegistry or type(catalog_profile_constraints) is not CatalogProfileConstraints or type(kernel_policy_v1_1_constraints) is not KernelValidationPolicyV11Constraints:
        return _failure("terminal composition requires exact record, registry, sealed C, and sealed 1.1 types","TERMINAL_E_INPUT")
    preflight=_preflight((plan_raw,discovery_raw,decision_raw,bundle_raw),assets=supplied_contract_assets)
    if preflight:return preflight
    bundle,bundle_findings=_bundle(bundle_raw,registry,supplied_contract_assets)
    if bundle_findings:return bundle_findings
    assert bundle is not None
    try:
        cparts=_constraints_parts(catalog_profile_constraints);eparts=_v11_parts(kernel_policy_v1_1_constraints)
        if cparts is None or eparts is None:return _failure("terminal constraints failed seal integrity","TERMINAL_E_INPUT",code=DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        docs=[];types=("agtxiv.agentization-plan/1.0.0","agtxiv.inventory-discovery-result/1.0.0","agtxiv.scope-freeze-decision/1.0.0")
        for raw,expected_type in zip((plan_raw,discovery_raw,decision_raw),types):
            parsed=parse_canonical_json(raw)
            if type(parsed) is not ParsedCanonicalValue or canonical_bytes(parsed)!=raw or validate_immutable_record_payload(parsed,registry):return _failure("terminal planning binding is not canonical schema-valid immutable data","TERMINAL_E_BINDING",code=DiagnosticCode.REF_HASH_MISMATCH)
            document=parsed.to_python()
            if document.get("envelope",{}).get("record_type")!=expected_type or document.get("envelope",{}).get("contract_bundle_ref")!=_record_ref(bundle):return _failure("terminal planning ancestry has a wrong family or bundle binding","TERMINAL_E_BINDING",code=DiagnosticCode.RECORD_TYPE_SCHEMA_MISMATCH)
            docs.append(document)
        plan,discovery,decision=docs;plan_payload=plan["payload"];manifest_refs=[ref for name in ("schema_assets","contract_assets","validator_assets","specification_assets") for ref in bundle["payload"][name]]
        constraint_refs=[cparts[0].to_python(),cparts[1].to_python(),cparts[2].to_python(),*(value.to_python() for value in eparts[0].values())]
        if any(ref not in manifest_refs for ref in constraint_refs) or plan_payload.get("artifact_family_catalog_ref")!=cparts[1].to_python() or plan_payload.get("agentization_profile_ref")!=cparts[2].to_python() or plan_payload.get("stable_code_catalog_ref")!=eparts[0]["catalog"].to_python() or plan_payload.get("kernel_validation_policy_ref")!=eparts[0]["policy"].to_python():return _failure("terminal constraints are not the exact bundle-bound Plan roots","TERMINAL_E_INPUT",code=DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        c_findings=validate_typed_terminal_result_catalog_constraints(record,registry,catalog_profile_constraints)
        if c_findings:return c_findings
        policy_findings=validate_planning_terminal_registration_v1_1(record,kernel_policy_v1_1_constraints)
        if policy_findings:return policy_findings
        terminal=record.to_python();envelope=terminal["envelope"];payload=terminal["payload"];target=payload["target_obligation"];plan_ref=_record_ref(plan)
        if envelope.get("contract_bundle_ref")!=_record_ref(bundle) or discovery["payload"].get("plan_ref")!=plan_ref or decision["payload"].get("plan_ref")!=plan_ref or decision["payload"].get("discovery_ref")!=_record_ref(discovery) or decision["payload"].get("source_snapshot_ref")!=discovery["payload"].get("source_snapshot_ref") or decision["payload"].get("source_tree_root")!=discovery["payload"].get("source_tree_root"):
            return _failure("terminal planning ancestry is stale or cross-plan","TERMINAL_E_BINDING",code=DiagnosticCode.REF_HASH_MISMATCH)
        obligation_index=next((index for index,row in enumerate(plan["payload"]["profile_obligations"]) if row["obligation_id"]=="obligation:checkpoint-e/frozen-inventory-scope"),None)
        if obligation_index is None:return _failure("terminal obligation is absent from the exact Plan projection","TERMINAL_E_BINDING",code=DiagnosticCode.REASON_CONSTRAINT_MISMATCH)
        expected_basis={**plan_ref,"component_id":"obligation:checkpoint-e/frozen-inventory-scope","json_pointer":f"/payload/profile_obligations/{obligation_index}"}
        expected_context={"context_mode":"PLAN_BOUND","profile_ref":plan["payload"]["agentization_profile_ref"],"catalog_ref":plan["payload"]["artifact_family_catalog_ref"],"plan_ref":plan_ref}
        expected_summary="Scope freeze was not accepted for the exact plan-bound discovery; no FrozenInventoryScope was issued."
        expected_budget={"max_wall_time_ms":60000,"max_cpu_time_ms":60000,"max_peak_memory_bytes":134217728,"max_input_bytes":134217728,"max_output_bytes":41943040,"max_network_requests":0}
        expected_unobserved=["wall_time_ms","cpu_time_ms","peak_memory_bytes","input_bytes","output_bytes"]
        reviewer=decision["payload"]["reviewer"]
        if decision["payload"]["decision"]!="BLOCK" or not _producer_matches(envelope,bundle,"SCOPE_FREEZE_ISSUER") or payload["attempt_id"]!=envelope["producer_context"]["attempt_id"] or payload["binding_context"]!=expected_context or target!={"obligation_key":"obligation:checkpoint-e/frozen-inventory-scope","stage_id":"SCOPE_FREEZE","family_id":"FROZEN_INVENTORY_SCOPE","basis":{"basis_kind":"COMPONENT","component_ref":expected_basis}} or payload["outcome"]!="BLOCKED" or payload["declared_reason"]!={"declared_reason_code":"AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED","summary":expected_summary}:
            return _failure("terminal identity, context, target, reason, or issuer attempt differs from the frozen E vector","TERMINAL_E_BINDING",code=DiagnosticCode.REASON_CONSTRAINT_MISMATCH)
        retry={"retry_disposition":"NO_RETRY_IN_CURRENT_CONTEXT","context_change_required":"A new independently reviewed scope-freeze attempt is required before scope issuance."}
        action=payload["next_action"]
        if payload["retry"]!=retry or action.get("action_code")!="ESCALATE" or action.get("description")!="Escalate the blocked scope-freeze decision for an independently authorized new attempt." or action.get("responsible_actor")!=reviewer or action.get("responsible_role")!="SCOPE_FREEZE_REVIEWER" or action.get("deadline")!={"deadline_kind":"NO_DEADLINE","no_deadline_reason":"No production review schedule is authorized by Checkpoint E."}:
            return _failure("terminal retry/action/reviewer/deadline differs from the frozen E vector","TERMINAL_E_BINDING",code=DiagnosticCode.REASON_CONSTRAINT_MISMATCH)
        resources=payload["resources"]
        if resources!={"limit":expected_budget,"observed":{"network_requests":0},"unobserved_metrics":expected_unobserved,"relation":"INDETERMINATE"}:
            return _failure("terminal resources differ from the complete six-dimension frozen budget","TERMINAL_E_BINDING",code=DiagnosticCode.TERMINAL_RESOURCE_INVALID)
        expected_evidence=[{"evidence_id":"evidence:scope-freeze/block-decision","evidence_role":"POLICY_OBSERVATION","evidence_kind":"RECORD","record_ref":_record_ref(decision)}]
        blocked=[row for row in discovery["payload"]["source_unit_coverage"] if row["coverage_status"]=="BLOCKED_WITH_EVIDENCE"]
        if blocked:
            component_ids=set(blocked[0]["component_ids"]);components=sum((discovery["payload"][name] for name in ("ambiguous_components","unclassified_components")),[]);component=next((item for item in components if item["component_id"] in component_ids and item["component_kind"]=="UNRESOLVED_SOURCE_REGION"),None)
            if component is None:return _failure("blocked discovery has no unresolved fallback component","TERMINAL_E_BINDING",code=DiagnosticCode.REASON_CONSTRAINT_MISMATCH)
            component_ref={**_record_ref(discovery),"component_id":component["component_id"],"json_pointer":next(f"/payload/{name}/{index}" for name in ("ambiguous_components","unclassified_components") for index,item in enumerate(discovery["payload"][name]) if item["component_id"]==component["component_id"])}
            expected_evidence.append({"evidence_id":"evidence:scope-freeze/blocked-component","evidence_role":"TOOL_DIAGNOSTIC","evidence_kind":"COMPONENT","component_ref":component_ref})
        expected_evidence.append({"evidence_id":"evidence:scope-freeze/discovery","evidence_role":"INPUT_STATE","evidence_kind":"RECORD","record_ref":_record_ref(discovery)})
        if payload["evidence"]!=expected_evidence:return _failure("terminal evidence roles, order, or exact projections differ from the frozen E vector","TERMINAL_E_BINDING",code=DiagnosticCode.REASON_CONSTRAINT_MISMATCH)
        return ()
    except Exception:return _failure("terminal E composition failed closed","TERMINAL_E_INPUT")


def validate_planning_scope_chain(snapshot_raw: bytes, source_bytes_by_path: dict[str, bytes], plan_raw: bytes, discovery_raw: bytes, decision_raw: bytes, terminal_records_raw: tuple[bytes, ...], scope_records_raw: tuple[bytes, ...], predecessor_history: tuple[PlanningScopeChainDeclaration,...], supplied_contract_assets: tuple[SuppliedAsset, ...], registry: ContractSchemaRegistry, bundle_raw: bytes) -> PlanningScopeChain | tuple[Diagnostic, ...]:
    try:
        diagnostics=_preflight((snapshot_raw,plan_raw,discovery_raw,decision_raw,bundle_raw),source_bytes_by_path,supplied_contract_assets,(terminal_records_raw,scope_records_raw))
        if diagnostics:return diagnostics
        if type(predecessor_history) is not tuple or any(type(item) is not PlanningScopeChainDeclaration for item in predecessor_history) or len(predecessor_history)>MAX_PREDECESSOR_DECLARATIONS:return _failure("aggregate predecessor history requires at most 256 exact declarations","CHAIN_ISSUANCE")
        decision=validate_scope_freeze_decision(decision_raw,discovery_raw,plan_raw,snapshot_raw,source_bytes_by_path,supplied_contract_assets,registry,bundle_raw)
        if type(decision) is tuple:return decision
        branch=decision.to_python()["payload"]["decision"]
        if branch=="ACCEPT":
            if terminal_records_raw or len(scope_records_raw)!=1:return _failure("ACCEPT requires zero terminals and exactly one scope","CHAIN_ISSUANCE",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
            scope=validate_frozen_inventory_scope(scope_records_raw[0],decision_raw,discovery_raw,plan_raw,snapshot_raw,source_bytes_by_path,supplied_contract_assets,registry,bundle_raw,predecessor_history)
            if type(scope) is tuple:return scope
        else:
            if predecessor_history or len(terminal_records_raw)!=1 or scope_records_raw:return _failure("BLOCK requires empty history, exactly one terminal, and zero scopes","CHAIN_ISSUANCE",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
            parsed=parse_canonical_json(terminal_records_raw[0])
            if type(parsed) is not ParsedCanonicalValue or canonical_bytes(parsed)!=terminal_records_raw[0]:return _failure("BLOCK terminal is not canonical","CHAIN_ISSUANCE",code=DiagnosticCode.RECORD_PAYLOAD_INVALID)
            parsed_plan=parse_canonical_json(plan_raw)
            if type(parsed_plan) is not ParsedCanonicalValue:return (parsed_plan,)
            constraints=_planning_constraints(supplied_contract_assets,registry,parsed_plan.to_python()["payload"])
            if type(constraints) is tuple and constraints and type(constraints[0]) is Diagnostic:return constraints
            assert type(constraints) is tuple and type(constraints[0]) is CatalogProfileConstraints
            terminal_findings=validate_planning_terminal_constraints(parsed,registry,constraints[0],constraints[1],plan_raw,discovery_raw,decision_raw,supplied_contract_assets,bundle_raw)
            if terminal_findings:return terminal_findings
        all_raw=terminal_records_raw+scope_records_raw;ids=[];refs=[]
        for raw in all_raw:
            parsed=parse_canonical_json(raw)
            if type(parsed) is not ParsedCanonicalValue:return (parsed,)
            doc=parsed.to_python();ids.append(doc["envelope"]["record_id"]);refs.append(_canonical(_record_ref(doc)))
        if len(ids)!=len(set(ids)) or len(refs)!=len(set(refs)):return _failure("complete-set members duplicate an ID or exact ref","CHAIN_ISSUANCE",code=DiagnosticCode.REF_HASH_MISMATCH)
        return _SealedView("PlanningScopeChain",{"decision":branch,"terminal_record_ids":ids if branch=="BLOCK" else [],"scope_record_ids":ids if branch=="ACCEPT" else []},_token=_TOKEN)
    except Exception:return _failure("aggregate planning chain failed closed while inspecting hostile input")


__all__=["PlanningScopeChain","PlanningScopeChainDeclaration","ScopeRevisionImpact","ScopeRevisionLineageProjection","build_planning_scope_chain_declaration","validate_paper_source_snapshot","validate_agentization_plan","validate_inventory_discovery_result","validate_scope_freeze_decision","validate_frozen_inventory_scope","validate_planning_scope_chain","compute_scope_revision_impact","validate_planning_terminal_constraints"]
