"""Pure offline validation of Checkpoint C requirement, Catalog, and Profile assets.

Success proves structural conformance only.  It grants no runtime, review,
release, coverage, archive, database-admission, or knowledge-admission authority.
Every interpreted byte string is supplied by the caller; path hints are display
text and are never opened or fetched.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Never

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .canonical import CanonicalValueIntegrityError, ParsedCanonicalValue, build_canonical_value, canonical_bytes, parse_canonical_json
from .diagnostics import Diagnostic, DiagnosticCode
from .references import SuppliedAsset, raw_asset_sha256
from .registry import ContractSchemaRegistry, DRAFT_2020_12, _diagnostic, _path_pointer, _registry_entries, _sort_diagnostics, _thaw_json
from .schema_validation import _FIXED_FORMAT_CHECKER, _validation_schema_snapshot
from .terminal_validation import validate_typed_terminal_result_intrinsic

_OFFICIAL_SCHEMA_REFS = MappingProxyType({'requirements': {'asset_id': 'schema:m1-contract-requirement-set:1.0.0', 'media_type': 'application/schema+json', 'byte_size': 5365, 'sha256': 'sha256:b5a78cbe8502b1155d57b5cc7882d615f9db7bfa4fd63f5e4fd70508efd6416a', 'schema_uri': 'https://agtxiv.org/schema/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0'}, 'catalog': {'asset_id': 'schema:artifact-family-catalog:1.0.0', 'media_type': 'application/schema+json', 'byte_size': 7488, 'sha256': 'sha256:0f8d0f437759bff749b9402c5d02ffdb44efaa726104590b09acea23f5a1cd13', 'schema_uri': 'https://agtxiv.org/schema/v2/contract-kernel/contract/artifact-family-catalog/1.0.0'}, 'profile': {'asset_id': 'schema:agentization-profile-release:1.0.0', 'media_type': 'application/schema+json', 'byte_size': 5312, 'sha256': 'sha256:aa31a09ff70e62b4d162f0fee2d5cd8c30bf29fc34149e4ca414532a1db7d9fb', 'schema_uri': 'https://agtxiv.org/schema/v2/contract-kernel/contract/agentization-profile-release/1.0.0'}})
_OFFICIAL_REQUIREMENTS_REF = MappingProxyType({'asset_id': 'requirements:m1-contract-requirement-set:1.0.0', 'media_type': 'application/json', 'byte_size': 12775, 'sha256': 'sha256:b8c14e570f94934b56b0a0447c856d9d37eb2db9ede6aa6c191280ff618058f9'})
_EXPECTED_SOURCE_ROWS = ({'requirement_ordinals': [1, 2, 3, 4, 5, 6, 7], 'source_group': 'Contract', 'source_required_families_cell': 'ContractBundleRelease, profile, ArtifactFamilyCatalog, canonicalization and policy refs', 'source_table_row_ordinal': 1, 'source_target_milestone_cell': 'M1'}, {'requirement_ordinals': [8, 9, 10, 11], 'source_group': 'Intake', 'source_required_families_cell': 'PaperQuery, WorkResolution, SourceAcquisitionRequest/Result', 'source_table_row_ordinal': 2, 'source_target_milestone_cell': 'M1/M1.5'}, {'requirement_ordinals': [12, 13, 14, 15], 'source_group': 'Planning', 'source_required_families_cell': 'AgentizationPlan, InventoryDiscoveryResult, ScopeFreezeDecision, FrozenInventoryScope', 'source_table_row_ordinal': 4, 'source_target_milestone_cell': 'M1'}, {'requirement_ordinals': [16, 17, 18, 19], 'source_group': 'Claims', 'source_required_families_cell': 'ScientificClaim, ClaimDecomposition, attribution and reconstruction evidence', 'source_table_row_ordinal': 6, 'source_target_milestone_cell': 'M1/M4a'}, {'requirement_ordinals': [20, 21, 22, 23, 24], 'source_group': 'Mathematics', 'source_required_families_cell': 'native MathClaimIR/2, MathClaimIRBinding/2, component index, residual semantics', 'source_table_row_ordinal': 7, 'source_target_milestone_cell': 'M1/M4b'}, {'requirement_ordinals': [25, 26, 27, 28], 'source_group': 'Reasoning', 'source_required_families_cell': 'InferenceStep, claim inference graph, mathematical dependency graph, frontier/blocker', 'source_table_row_ordinal': 8, 'source_target_milestone_cell': 'M1/M4b'}, {'requirement_ordinals': [29, 30, 31, 32], 'source_group': 'Formalization', 'source_required_families_cell': 'FormalizationRequest, generated package, build result, formal declaration graph', 'source_table_row_ordinal': 10, 'source_target_milestone_cell': 'M1/M5'}, {'requirement_ordinals': [33, 34, 35], 'source_group': 'Assessment', 'source_required_families_cell': 'assessor/method/evidence/rationale/uncertainty/attestation, ReviewDecision', 'source_table_row_ordinal': 13, 'source_target_milestone_cell': 'M1/M5/M6'}, {'requirement_ordinals': [36, 37, 38, 39, 40], 'source_group': 'Release', 'source_required_families_cell': 'release manifest, Root audit, certificate, replay bundle, ArchiveReceipt', 'source_table_row_ordinal': 14, 'source_target_milestone_cell': 'M1/M6'}, {'requirement_ordinals': [41, 42, 43, 44, 45, 46], 'source_group': 'Knowledge', 'source_required_families_cell': 'candidate entry, relation, per-entry eligibility, admission transaction, snapshot, ingestion receipt', 'source_table_row_ordinal': 15, 'source_target_milestone_cell': 'M1/M6'}, {'requirement_ordinals': [47, 48, 49], 'source_group': 'Query', 'source_required_families_cell': 'QueryResolution, exact snapshot projection, conflict preservation', 'source_table_row_ordinal': 16, 'source_target_milestone_cell': 'M1/M6'}, {'requirement_ordinals': [21, 50, 51], 'source_group': 'Compatibility', 'source_required_families_cell': 'V1 binding, migration/import receipt, reconciliation report', 'source_table_row_ordinal': 17, 'source_target_milestone_cell': 'M1/M8'}, {'requirement_ordinals': [52], 'source_group': 'Terminal', 'source_required_families_cell': 'typed stage/family result with reason, evidence, retryability, responsible actor, next action', 'source_table_row_ordinal': 18, 'source_target_milestone_cell': 'M1'})
_EXPECTED_ITEMS = ({'item_id': 'CONTRACT_BUNDLE_RELEASE', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 1, 'source_occurrences': [{'source_group': 'Contract', 'source_position': 1}]}, {'item_id': 'AGENTIZATION_PROFILE_RELEASE', 'item_kind': 'RAW_CONTRACT_ASSET', 'ordinal': 2, 'source_occurrences': [{'source_group': 'Contract', 'source_position': 2}]}, {'item_id': 'ARTIFACT_FAMILY_CATALOG', 'item_kind': 'RAW_CONTRACT_ASSET', 'ordinal': 3, 'source_occurrences': [{'source_group': 'Contract', 'source_position': 3}]}, {'item_id': 'CANONICALIZATION_PROFILE', 'item_kind': 'RAW_CONTRACT_ASSET', 'ordinal': 4, 'source_occurrences': [{'source_group': 'Contract', 'source_position': 4}]}, {'item_id': 'VALIDATION_POLICY', 'item_kind': 'RAW_CONTRACT_ASSET', 'ordinal': 5, 'source_occurrences': [{'source_group': 'Contract', 'source_position': 5}]}, {'item_id': 'SIGNATURE_POLICY', 'item_kind': 'RAW_CONTRACT_ASSET', 'ordinal': 6, 'source_occurrences': [{'source_group': 'Contract', 'source_position': 6}]}, {'item_id': 'STABLE_ERROR_CODE_CATALOG', 'item_kind': 'RAW_CONTRACT_ASSET', 'ordinal': 7, 'source_occurrences': [{'source_group': 'Contract', 'source_position': 7}]}, {'item_id': 'PAPER_QUERY', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 8, 'source_occurrences': [{'source_group': 'Intake', 'source_position': 1}]}, {'item_id': 'WORK_RESOLUTION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 9, 'source_occurrences': [{'source_group': 'Intake', 'source_position': 2}]}, {'item_id': 'SOURCE_ACQUISITION_REQUEST', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 10, 'source_occurrences': [{'source_group': 'Intake', 'source_position': 3}]}, {'item_id': 'SOURCE_ACQUISITION_RESULT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 11, 'source_occurrences': [{'source_group': 'Intake', 'source_position': 4}]}, {'item_id': 'AGENTIZATION_PLAN', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 12, 'source_occurrences': [{'source_group': 'Planning', 'source_position': 1}]}, {'item_id': 'INVENTORY_DISCOVERY_RESULT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 13, 'source_occurrences': [{'source_group': 'Planning', 'source_position': 2}]}, {'item_id': 'SCOPE_FREEZE_DECISION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 14, 'source_occurrences': [{'source_group': 'Planning', 'source_position': 3}]}, {'item_id': 'FROZEN_INVENTORY_SCOPE', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 15, 'source_occurrences': [{'source_group': 'Planning', 'source_position': 4}]}, {'item_id': 'SCIENTIFIC_CLAIM', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 16, 'source_occurrences': [{'source_group': 'Claims', 'source_position': 1}]}, {'item_id': 'CLAIM_DECOMPOSITION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 17, 'source_occurrences': [{'source_group': 'Claims', 'source_position': 2}]}, {'item_id': 'CLAIM_ATTRIBUTION_EVIDENCE', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 18, 'source_occurrences': [{'source_group': 'Claims', 'source_position': 3}]}, {'item_id': 'CLAIM_RECONSTRUCTION_EVIDENCE', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 19, 'source_occurrences': [{'source_group': 'Claims', 'source_position': 4}]}, {'item_id': 'NATIVE_MATH_CLAIM_IR', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 20, 'source_occurrences': [{'source_group': 'Mathematics', 'source_position': 1}]}, {'item_id': 'MATH_CLAIM_IR_BINDING', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 21, 'source_occurrences': [{'source_group': 'Mathematics', 'source_position': 2}, {'source_group': 'Compatibility', 'source_position': 1}]}, {'item_id': 'MATH_CLAIM_COMMON_READ_PROJECTION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 22, 'source_occurrences': [{'source_group': 'Mathematics', 'source_position': 3}]}, {'item_id': 'MATH_COMPONENT_INDEX', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 23, 'source_occurrences': [{'source_group': 'Mathematics', 'source_position': 4}]}, {'item_id': 'RESIDUAL_SEMANTICS', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 24, 'source_occurrences': [{'source_group': 'Mathematics', 'source_position': 5}]}, {'item_id': 'INFERENCE_STEP', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 25, 'source_occurrences': [{'source_group': 'Reasoning', 'source_position': 1}]}, {'item_id': 'CLAIM_INFERENCE_GRAPH', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 26, 'source_occurrences': [{'source_group': 'Reasoning', 'source_position': 2}]}, {'item_id': 'MATH_CLAIM_DEPENDENCY_GRAPH', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 27, 'source_occurrences': [{'source_group': 'Reasoning', 'source_position': 3}]}, {'item_id': 'DEPENDENCY_FRONTIER_BLOCKER', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 28, 'source_occurrences': [{'source_group': 'Reasoning', 'source_position': 4}]}, {'item_id': 'FORMALIZATION_REQUEST', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 29, 'source_occurrences': [{'source_group': 'Formalization', 'source_position': 1}]}, {'item_id': 'GENERATED_FORMAL_PACKAGE', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 30, 'source_occurrences': [{'source_group': 'Formalization', 'source_position': 2}]}, {'item_id': 'FORMAL_BUILD_RESULT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 31, 'source_occurrences': [{'source_group': 'Formalization', 'source_position': 3}]}, {'item_id': 'FORMAL_DECLARATION_GRAPH', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 32, 'source_occurrences': [{'source_group': 'Formalization', 'source_position': 4}]}, {'item_id': 'ASSESSMENT_RECORD', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 33, 'source_occurrences': [{'source_group': 'Assessment', 'source_position': 1}]}, {'item_id': 'REVIEW_DECISION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 34, 'source_occurrences': [{'source_group': 'Assessment', 'source_position': 2}]}, {'item_id': 'SIGNED_ATTESTATION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 35, 'source_occurrences': [{'source_group': 'Assessment', 'source_position': 3}]}, {'item_id': 'PAPER_AGENT_RELEASE_MANIFEST', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 36, 'source_occurrences': [{'source_group': 'Release', 'source_position': 1}]}, {'item_id': 'ROOT_AUDIT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 37, 'source_occurrences': [{'source_group': 'Release', 'source_position': 2}]}, {'item_id': 'MECHANICAL_CERTIFICATE', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 38, 'source_occurrences': [{'source_group': 'Release', 'source_position': 3}]}, {'item_id': 'REPLAY_BUNDLE', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 39, 'source_occurrences': [{'source_group': 'Release', 'source_position': 4}]}, {'item_id': 'ARCHIVE_RECEIPT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 40, 'source_occurrences': [{'source_group': 'Release', 'source_position': 5}]}, {'item_id': 'KNOWLEDGE_CANDIDATE_ENTRY', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 41, 'source_occurrences': [{'source_group': 'Knowledge', 'source_position': 1}]}, {'item_id': 'KNOWLEDGE_RELATION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 42, 'source_occurrences': [{'source_group': 'Knowledge', 'source_position': 2}]}, {'item_id': 'PER_ENTRY_ELIGIBILITY', 'item_kind': 'CROSS_RECORD_RULE', 'ordinal': 43, 'source_occurrences': [{'source_group': 'Knowledge', 'source_position': 3}]}, {'item_id': 'ADMISSION_TRANSACTION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 44, 'source_occurrences': [{'source_group': 'Knowledge', 'source_position': 4}]}, {'item_id': 'KNOWLEDGE_SNAPSHOT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 45, 'source_occurrences': [{'source_group': 'Knowledge', 'source_position': 5}]}, {'item_id': 'KNOWLEDGE_INGESTION_RECEIPT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 46, 'source_occurrences': [{'source_group': 'Knowledge', 'source_position': 6}]}, {'item_id': 'QUERY_RESOLUTION', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 47, 'source_occurrences': [{'source_group': 'Query', 'source_position': 1}]}, {'item_id': 'QUERY_EXACT_SNAPSHOT_BINDING_RULE', 'item_kind': 'CROSS_RECORD_RULE', 'ordinal': 48, 'source_occurrences': [{'source_group': 'Query', 'source_position': 2}]}, {'item_id': 'QUERY_CONFLICT_PRESERVATION_RULE', 'item_kind': 'CROSS_RECORD_RULE', 'ordinal': 49, 'source_occurrences': [{'source_group': 'Query', 'source_position': 3}]}, {'item_id': 'V1_MIGRATION_IMPORT_RECEIPT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 50, 'source_occurrences': [{'source_group': 'Compatibility', 'source_position': 2}]}, {'item_id': 'V1_RECONCILIATION_REPORT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 51, 'source_occurrences': [{'source_group': 'Compatibility', 'source_position': 3}]}, {'item_id': 'TYPED_STAGE_FAMILY_TERMINAL_RESULT', 'item_kind': 'IMMUTABLE_RECORD_FAMILY', 'ordinal': 52, 'source_occurrences': [{'source_group': 'Terminal', 'source_position': 1}]})
_EXPECTED_SELECTION = {"selection_rule_id":"agtxiv.roadmap-exact-milestone-token/1.0.0","target_milestone_token":"M1","token_separator":"/","match_mode":"EXACT_TOKEN"}
_EXPECTED_ROADMAP_REF = {"asset_id":"roadmap:v2-end-to-end-implementation-plan:2026-08-31","media_type":"text/markdown","byte_size":50302,"sha256":"sha256:7419bc340471943b1e525974b558eb508d0deaf12455d5e12949db8a7d2be2f4"}
_EXPECTED_SOURCE_FACTS = {"source_git_commit":"9d84dad47b7a92225686158f7bfc512f39332f2c","source_git_blob_object_id":"sha1:782eb493c1ee28c6f61d5a07af30449b83183e08","section_start_heading":"## 6. Required artifact families\n","section_end_heading":"## 7. Mathematical formalization chain\n","section_byte_size":3136,"section_sha256":"sha256:e50d851df655302106f3c1b5ec3f8462b9dc2dd0d12143c1b4e68bde483e4437"}
_CONTEXT_RANK = {"PROFILE_BOUND":0,"PLAN_BOUND":1,"FROZEN_SCOPE_BOUND":2}
_OUTCOME_ORDER = ("UNAVAILABLE","RETRY_REQUIRED","REVIEW_REQUIRED","BLOCKED","FAILED")
_CONSTRUCTION_TOKEN = object()
_MAX_SUPPORT_ASSET_COUNT = 1 + 2 * 256
_FIXED_VECTOR_SET_ID = "vectors:catalog-profile-linkage:checkpoint-c/1.0.0"
_VECTOR_SET_VERSION = "1.0.0"
_SEMVER_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?![\s\S])")
_SYMBOLIC_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,127}(?![\s\S])")

@dataclass(frozen=True, slots=True)
class RawContractAssetBinding:
    exact_ref: ParsedCanonicalValue
    supplied_asset: SuppliedAsset

@dataclass(frozen=True, slots=True)
class _Policy:
    family_id: str
    family_version: str
    stage_id: str
    adjustment: str
    roles: tuple[str, ...]
    terminal_mode: str
    outcomes: tuple[str, ...]
    minimum_context: str

class CatalogProfileConstraints:
    """Detached recursively immutable Catalog/Profile constraint snapshot."""
    __slots__ = ("__requirements_ref","__catalog_ref","__profile_ref","__requirement_ids","__family_ids","__stage_ids","__policies","__seal","__token")
    def __init__(self, requirements_ref: ParsedCanonicalValue, catalog_ref: ParsedCanonicalValue, profile_ref: ParsedCanonicalValue, requirement_ids: tuple[str,...], family_ids: tuple[str,...], stage_ids: tuple[str,...], policies: tuple[_Policy,...], *, _token: object=None):
        if _token is not _CONSTRUCTION_TOKEN: raise TypeError("CatalogProfileConstraints is created only by build_catalog_profile_constraints")
        object.__setattr__(self,"_CatalogProfileConstraints__requirements_ref",requirements_ref)
        object.__setattr__(self,"_CatalogProfileConstraints__catalog_ref",catalog_ref)
        object.__setattr__(self,"_CatalogProfileConstraints__profile_ref",profile_ref)
        object.__setattr__(self,"_CatalogProfileConstraints__requirement_ids",requirement_ids)
        object.__setattr__(self,"_CatalogProfileConstraints__family_ids",family_ids)
        object.__setattr__(self,"_CatalogProfileConstraints__stage_ids",stage_ids)
        object.__setattr__(self,"_CatalogProfileConstraints__policies",policies)
        object.__setattr__(self,"_CatalogProfileConstraints__seal",_constraints_seal(requirements_ref,catalog_ref,profile_ref,requirement_ids,family_ids,stage_ids,policies))
        object.__setattr__(self,"_CatalogProfileConstraints__token",_CONSTRUCTION_TOKEN)
    def __setattr__(self,name:str,value:Any)->Never: raise AttributeError("CatalogProfileConstraints is immutable")
    def __delattr__(self,name:str)->Never: raise AttributeError("CatalogProfileConstraints is immutable")
    @property
    def requirements_ref(self)->ParsedCanonicalValue: _require_constraints(self); return self.__requirements_ref
    @property
    def catalog_ref(self)->ParsedCanonicalValue: _require_constraints(self); return self.__catalog_ref
    @property
    def profile_ref(self)->ParsedCanonicalValue: _require_constraints(self); return self.__profile_ref
    @property
    def requirement_ids(self)->tuple[str,...]: _require_constraints(self); return self.__requirement_ids
    @property
    def family_ids(self)->tuple[str,...]: _require_constraints(self); return self.__family_ids
    @property
    def stage_ids(self)->tuple[str,...]: _require_constraints(self); return self.__stage_ids
    def __repr__(self)->str: return "CatalogProfileConstraints(<sealed structural constraints>)"

def _constraints_parts(value: Any):
    if type(value) is not CatalogProfileConstraints: return None
    try:
        parts=(object.__getattribute__(value,"_CatalogProfileConstraints__requirements_ref"),object.__getattribute__(value,"_CatalogProfileConstraints__catalog_ref"),object.__getattribute__(value,"_CatalogProfileConstraints__profile_ref"),object.__getattribute__(value,"_CatalogProfileConstraints__requirement_ids"),object.__getattribute__(value,"_CatalogProfileConstraints__family_ids"),object.__getattribute__(value,"_CatalogProfileConstraints__stage_ids"),object.__getattribute__(value,"_CatalogProfileConstraints__policies"))
        seal=object.__getattribute__(value,"_CatalogProfileConstraints__seal"); token=object.__getattribute__(value,"_CatalogProfileConstraints__token")
    except Exception:return None
    if token is not _CONSTRUCTION_TOKEN or type(seal) is not str:return None
    if any(type(x) is not ParsedCanonicalValue for x in parts[:3]) or any(type(x) is not tuple for x in parts[3:]):return None
    if any(type(x) is not str for seq in parts[3:6] for x in seq) or any(type(x) is not _Policy for x in parts[6]):return None
    try:
        if seal != _constraints_seal(*parts): return None
    except Exception:return None
    return parts

def _require_constraints(value):
    if _constraints_parts(value) is None: raise ValueError("CatalogProfileConstraints failed its integrity check")

def _constraints_seal(*parts)->str:
    h=hashlib.sha256()
    for value in parts[:3]:
        b=canonical_bytes(value); h.update(len(b).to_bytes(8,"big"));h.update(b)
    for seq in parts[3:6]:
        for s in seq:
            b=s.encode();h.update(len(b).to_bytes(8,"big"));h.update(b)
    for p in parts[6]:
        for s in (p.family_id,p.family_version,p.stage_id,p.adjustment,*p.roles,p.terminal_mode,*p.outcomes,p.minimum_context):
            b=s.encode();h.update(len(b).to_bytes(8,"big"));h.update(b)
    return "sha256:"+h.hexdigest()

def _diag(code,message,phase,pointer="",subject=None,details=None): return _diagnostic(code,message,pointer=pointer,phase=phase,subject=subject,details=details)
def _asset_projection(value):
    if type(value) is not dict:return None
    keys=("asset_id","media_type","byte_size","sha256")+(("schema_uri",) if "schema_uri" in value else ())
    return {k:value.get(k) for k in keys}
def _parsed(value):
    result=build_canonical_value(value)
    return result if type(result) is ParsedCanonicalValue else None

def _snapshot_inputs(bindings, support_assets, registry):
    entries = _registry_entries(registry) if type(registry) is ContractSchemaRegistry else None
    if entries is None or type(bindings) is not tuple or type(support_assets) is not tuple:
        return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"validation requires exact immutable typed inputs","CATALOG_INPUT"),)

    # First pass inspects only outer member types.  No member raw bytes are
    # copied, measured, hashed, or parsed until every member passes this pass.
    if any(type(binding) is not RawContractAssetBinding for binding in bindings):
        return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root binding requires exact RawContractAssetBinding type","CATALOG_INPUT"),)
    if any(type(asset) is not SuppliedAsset for asset in support_assets):
        return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"support asset requires exact SuppliedAsset type","CATALOG_INPUT"),)

    # Second pass checks the exact opaque field types for all roots and support
    # assets before making any raw-byte observation.
    root_fields=[]
    for binding in bindings:
        try:
            exact_ref=object.__getattribute__(binding,"exact_ref")
            asset=object.__getattribute__(binding,"supplied_asset")
        except Exception:
            return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root binding is incomplete","CATALOG_INPUT"),)
        if type(exact_ref) is not ParsedCanonicalValue or type(asset) is not SuppliedAsset:
            return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root binding fields have invalid exact types","CATALOG_INPUT"),)
        root_fields.append((exact_ref,asset))
    support_fields=[]
    for asset in support_assets:
        try:
            support_fields.append((object.__getattribute__(asset,"asset_id"),object.__getattribute__(asset,"media_type"),object.__getattribute__(asset,"raw_bytes"),object.__getattribute__(asset,"schema_uri")))
        except Exception:
            return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"support asset is incomplete","CATALOG_INPUT"),)
    roots=[]
    for exact_ref,asset in root_fields:
        try:
            ref=exact_ref.to_python();aid=object.__getattribute__(asset,"asset_id");media=object.__getattribute__(asset,"media_type");raw=object.__getattribute__(asset,"raw_bytes");uri=object.__getattribute__(asset,"schema_uri")
        except Exception:
            return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root binding contains a forged opaque value","CATALOG_INPUT"),)
        if type(ref) is not dict or type(aid) is not str or type(media) is not str or type(raw) is not bytes or (uri is not None and type(uri) is not str):
            return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"root binding metadata has invalid exact types","CATALOG_INPUT"),)
        roots.append((ref,aid,media,raw,uri))
    if any(type(aid) is not str or type(media) is not str or type(raw) is not bytes or (uri is not None and type(uri) is not str) for aid,media,raw,uri in support_fields):
        return None,(_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"support metadata has invalid exact types","CATALOG_INPUT"),)

    # Declared-size mismatches are cheaper than copying, hashing, or parsing.
    if any(type(ref.get("byte_size")) is not int or len(raw)!=ref["byte_size"] for ref,_,_,raw,_ in roots):
        return None,(_diag(DiagnosticCode.REF_HASH_MISMATCH,"raw root byte size differs from its exact reference","CATALOG_BINDING"),)
    if len(support_fields)>_MAX_SUPPORT_ASSET_COUNT:
        return None,(_diag(DiagnosticCode.CATALOG_REFERENCE_INVALID,"support asset count exceeds the schema-derived closure limit","CATALOG_INPUT"),)
    declarations=[]
    declarations.extend((item[1],item[2],item[3],"ROOT") for item in roots)
    declarations.extend((item[0],item[1],item[2],"SUPPORT") for item in support_fields)
    declarations.extend((entry.asset_id,entry.media_type,entry.raw_bytes,"SCHEMA_REGISTRY") for entry in entries)
    if len({item[0] for item in declarations})!=len(declarations):
        return None,(_diag(DiagnosticCode.CATALOG_REFERENCE_INVALID,"root, support, and schema-registry asset IDs share one global namespace","CATALOG_BINDING"),)
    root_snapshots=tuple((ref,aid,media,bytes(raw),uri) for ref,aid,media,raw,uri in roots)
    support_index=MappingProxyType({aid:(aid,media,bytes(raw),uri) for aid,media,raw,uri in support_fields})
    return (root_snapshots,support_index),()

def _bind(snapshot):
    ref,aid,media,raw,uri=snapshot
    if _asset_projection(ref)!={"asset_id":aid,"media_type":media,"byte_size":len(raw),"sha256":raw_asset_sha256(raw),**({"schema_uri":uri} if "schema_uri" in ref else {})}:
        return None,_diag(DiagnosticCode.REF_HASH_MISMATCH,"raw root differs from its exact reference","CATALOG_BINDING",subject=aid)
    parsed=parse_canonical_json(raw)
    if type(parsed) is Diagnostic:return None,parsed
    if canonical_bytes(parsed)!=raw:return None,_diag(DiagnosticCode.ASSET_INVALID,"raw contract document is not canonical JSON","CATALOG_SCHEMA",subject=aid)
    doc=parsed.to_python()
    if type(doc) is not dict:return None,_diag(DiagnosticCode.ASSET_INVALID,"raw contract document must be an object","CATALOG_SCHEMA",subject=aid)
    return (parsed,doc),None

def _schema_entry(registry, expected):
    entries=_registry_entries(registry)
    matches=[e for e in entries if e.asset_id==expected["asset_id"]]
    if len(matches)!=1:return None
    e=matches[0]
    if {"asset_id":e.asset_id,"media_type":e.media_type,"byte_size":e.byte_size,"sha256":e.sha256,"schema_uri":e.schema_id}!=expected:return None
    return e

def _validate_root(doc, registry, expected, subject):
    if _asset_projection(doc.get("document_schema_ref"))!=expected or _schema_entry(registry,expected) is None:
        return [_diag(DiagnosticCode.ASSET_SCHEMA_MISMATCH,"document or registry differs from the compiled official schema bytes","CATALOG_SCHEMA",pointer="/document_schema_ref",subject=subject)]
    try:
        entries=_registry_entries(registry); resources=[]; locations={}
        for e in entries:resources.append((e.schema_id,Resource.from_contents(_validation_schema_snapshot(_thaw_json(e.document),e.schema_id,locations))))
        validator=Draft202012Validator({"$schema":DRAFT_2020_12,"$ref":expected["schema_uri"]},registry=Registry().with_resources(resources),format_checker=_FIXED_FORMAT_CHECKER)
        errors=list(validator.iter_errors(doc))
    except Exception:return [_diag(DiagnosticCode.ASSET_INVALID,"document could not be evaluated by the exact offline schema","CATALOG_SCHEMA",subject=subject)]
    return [_diag(DiagnosticCode.ASSET_INVALID,"document violates the exact official schema","CATALOG_SCHEMA",pointer=_path_pointer(e.absolute_path),subject=subject,details={"validator":str(e.validator)}) for e in errors]

def _resolve_ref(ref,supports,*,media=None):
    if type(ref) is not dict:return None
    p=_asset_projection(ref)
    match=supports.get(ref.get("asset_id"))
    if match is None:return None
    aid,m,b,u=match
    if p is None or p.get("asset_id")!=aid or p.get("media_type")!=m or p.get("byte_size")!=len(b):return None
    if "schema_uri" in ref and p.get("schema_uri")!=u:return None
    if media is not None and m!=media:return None
    return match if p.get("sha256")==raw_asset_sha256(b) else None

def _requirements_semantics(doc,supports):
    ds=[]; sb=doc.get("source_binding",{}); roadmap=sb.get("roadmap_ref") if type(sb) is dict else None
    target=_resolve_ref(roadmap,supports,media="text/markdown")
    if _asset_projection(roadmap)!=_EXPECTED_ROADMAP_REF or target is None:
        ds.append(_diag(DiagnosticCode.REQUIREMENTS_SOURCE_BINDING_MISMATCH,"roadmap exact reference does not match the pinned source","REQUIREMENTS_SOURCE",pointer="/source_binding/roadmap_ref"));return ds
    raw=target[2]; start=_EXPECTED_SOURCE_FACTS["section_start_heading"].encode();end=_EXPECTED_SOURCE_FACTS["section_end_heading"].encode()
    try:
        if raw.count(start)!=1 or raw.count(end)!=1:raise ValueError
        a=raw.index(start);z=raw.index(end,a+len(start));section=raw[a:z]
    except ValueError:section=b""
    git_oid="sha1:"+hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    observed={k:sb.get(k) for k in _EXPECTED_SOURCE_FACTS}
    observed["source_git_blob_object_id"]=git_oid
    if observed!=_EXPECTED_SOURCE_FACTS or len(section)!=3136 or raw_asset_sha256(section)!=_EXPECTED_SOURCE_FACTS["section_sha256"]:
        ds.append(_diag(DiagnosticCode.REQUIREMENTS_SOURCE_BINDING_MISMATCH,"roadmap bytes, Git blob, or bounded section differs from the pinned source","REQUIREMENTS_SOURCE",pointer="/source_binding"))
    if doc.get("selection_rule")!=_EXPECTED_SELECTION:ds.append(_diag(DiagnosticCode.REQUIREMENTS_SELECTION_RULE_MISMATCH,"selection rule differs from exact M1-token policy","REQUIREMENTS_FLOOR",pointer="/selection_rule"))
    rows=doc.get("selected_source_rows");items=doc.get("items")
    if rows!=list(_EXPECTED_SOURCE_ROWS):ds.append(_diag(DiagnosticCode.REQUIREMENTS_MAPPING_MISMATCH,"selected roadmap rows or reviewed expansions differ","REQUIREMENTS_FLOOR",pointer="/selected_source_rows"))
    if type(items) is list:
        ids=[x.get("item_id") if type(x) is dict else None for x in items]
        expected=[x["item_id"] for x in _EXPECTED_ITEMS]
        if set(ids)!=set(expected) or len(ids)!=len(set(ids)):ds.append(_diag(DiagnosticCode.REQUIREMENTS_ITEM_SET_MISMATCH,"requirement item set differs from the compiled 52-item floor","REQUIREMENTS_FLOOR",pointer="/items"))
        elif items!=list(_EXPECTED_ITEMS):ds.append(_diag(DiagnosticCode.REQUIREMENTS_ITEM_ORDER_MISMATCH,"requirement order, kind, or occurrence differs from the compiled floor","REQUIREMENTS_FLOOR",pointer="/items"))
    else:ds.append(_diag(DiagnosticCode.REQUIREMENTS_ITEM_SET_MISMATCH,"requirements items are absent","REQUIREMENTS_FLOOR",pointer="/items"))
    return ds

def validate_m1_contract_requirement_set_intrinsic(requirements_binding, support_assets, registry):
    try:
        snapshots,ds=_snapshot_inputs((requirements_binding,),support_assets,registry)
        if ds:return ds
        roots,supports=snapshots
        if _asset_projection(roots[0][0])!=dict(_OFFICIAL_REQUIREMENTS_REF):return (_diag(DiagnosticCode.CATALOG_REFERENCE_INVALID,"requirement root differs from the compiled official bytes","CATALOG_BINDING"),)
        bound,problem=_bind(roots[0])
        if problem:return (problem,)
        parsed,doc=bound; findings=_validate_root(doc,registry,_OFFICIAL_SCHEMA_REFS["requirements"],roots[0][1])
        if findings:return _sort_diagnostics(findings)
        return _sort_diagnostics(_requirements_semantics(doc,supports))
    except Exception:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"requirement validation could not safely inspect submitted values","CATALOG_INPUT"),)

_VECTOR_ID_PATTERN=re.compile(r"^[a-z][a-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._:/-]*(?![\s\S])")

def _closed_vector_id(value):
    return type(value) is str and 3<=len(value)<=256 and _VECTOR_ID_PATTERN.fullmatch(value) is not None

def _closed_semver(value):
    return type(value) is str and _SEMVER_PATTERN.fullmatch(value) is not None

def _closed_symbolic_id(value):
    return type(value) is str and _SYMBOLIC_ID_PATTERN.fullmatch(value) is not None

def _vector_index(raw, vector_asset_id, expected_vector_set_id):
    parsed=parse_canonical_json(raw)
    if type(parsed) is Diagnostic or canonical_bytes(parsed)!=raw:return None
    doc=parsed.to_python()
    if type(doc) is not dict or set(doc)!={"vector_set_id","vector_set_version","fixture_purpose","vectors"}:return None
    if not _closed_vector_id(vector_asset_id) or vector_asset_id!=expected_vector_set_id or doc.get("vector_set_id")!=expected_vector_set_id or doc.get("vector_set_version")!=_VECTOR_SET_VERSION or doc.get("fixture_purpose")!="STRUCTURAL_CONFORMANCE_ONLY":return None
    vectors=doc.get("vectors")
    if type(vectors) is not list or not 1<=len(vectors)<=512:return None
    result={}; allowed_codes={str(code) for code in DiagnosticCode}
    for item in vectors:
        if type(item) is not dict:return None
        polarity=item.get("polarity");kind=item.get("vector_kind")
        if polarity not in {"POSITIVE","NEGATIVE"} or kind not in {"FAMILY_CONFORMANCE","CROSS_CONTRACT_TEST"}:return None
        required={"vector_id","polarity","vector_kind","template_id","expected_diagnostic_codes"}
        required.add("target" if kind=="FAMILY_CONFORMANCE" else "cross_test_kind")
        if polarity=="NEGATIVE":required.add("mutation_id")
        if set(item)!=required:return None
        if not _closed_vector_id(item.get("vector_id")) or not _closed_vector_id(item.get("template_id")):return None
        if polarity=="NEGATIVE" and not _closed_vector_id(item.get("mutation_id")):return None
        codes=item.get("expected_diagnostic_codes")
        if type(codes) is not list or len(codes)>32 or codes!=sorted(codes) or len(codes)!=len(set(codes)) or any(type(code) is not str or code not in allowed_codes for code in codes):return None
        if (polarity=="POSITIVE" and codes) or (polarity=="NEGATIVE" and not codes):return None
        if kind=="FAMILY_CONFORMANCE":
            target=item.get("target")
            if type(target) is not dict or set(target)!={"family_id","family_version","stage_id","artifact_kind"}:return None
            if not _closed_symbolic_id(target.get("family_id")) or not _closed_symbolic_id(target.get("stage_id")):return None
            if not _closed_semver(target.get("family_version")) or target.get("artifact_kind") not in {"RAW_CONTRACT_ASSET","IMMUTABLE_RECORD"}:return None
        elif item.get("cross_test_kind") not in {"CATALOG_POLICY","PROFILE_POLICY","TERMINAL_CONSTRAINT"}:return None
        vector_id=item["vector_id"]
        if vector_id in result:return None
        result[vector_id]=item
    return MappingProxyType(result)

def _catalog_semantics(doc,supports,registry,root_bytes,other_root_bytes):
    ds=[]; stages=doc["stages"];families=doc["family_policy_rows"]
    stage_ids=[s["stage_id"] for s in stages]
    if len(stage_ids)!=len(set(stage_ids)):ds.append(_diag(DiagnosticCode.CATALOG_DUPLICATE_STAGE,"Catalog stage IDs must be unique","CATALOG_COHERENCE"))
    if [s["ordinal"] for s in stages]!=list(range(1,len(stages)+1)):ds.append(_diag(DiagnosticCode.CATALOG_STRUCTURE_INVALID,"Catalog stages require contiguous ordinal order","CATALOG_COHERENCE"))
    family_ids=[f["family_id"] for f in families]
    if len(family_ids)!=len(set(family_ids)):ds.append(_diag(DiagnosticCode.CATALOG_DUPLICATE_FAMILY,"Catalog family IDs are globally unique across versions","CATALOG_COHERENCE"))
    if family_ids!=sorted(family_ids):ds.append(_diag(DiagnosticCode.CATALOG_STRUCTURE_INVALID,"Catalog family rows require strict family_id order","CATALOG_COHERENCE"))
    used=set()
    entries=_registry_entries(registry);by_schema={e.asset_id:e for e in entries}
    for fi,f in enumerate(families):
        base=f"/family_policy_rows/{fi}"; art=f["successful_artifact"];sr=art["schema_ref"];e=by_schema.get(sr["asset_id"])
        expected={"asset_id":e.asset_id,"media_type":e.media_type,"byte_size":e.byte_size,"sha256":e.sha256,"schema_uri":e.schema_id} if e else None
        if _asset_projection(sr)!=expected:ds.append(_diag(DiagnosticCode.CATALOG_FAMILY_BINDING_INVALID,"successful artifact schema does not exact-bind a registered schema", "CATALOG_COHERENCE",base+"/successful_artifact/schema_ref"))
        else:
            schema=_thaw_json(e.document);decl=((schema.get("$defs") or {}).get("recordType") or {}).get("const") if type(schema.get("$defs")) is dict else None
            if art["artifact_kind"]=="IMMUTABLE_RECORD" and decl!=art["record_type"]:ds.append(_diag(DiagnosticCode.CATALOG_FAMILY_BINDING_INVALID,"record family record_type differs from schema declaration","CATALOG_COHERENCE",base+"/successful_artifact/record_type"))
            if art["artifact_kind"]=="RAW_CONTRACT_ASSET" and type(decl) is str:ds.append(_diag(DiagnosticCode.CATALOG_FAMILY_BINDING_INVALID,"raw contract family schema declares an immutable record type","CATALOG_COHERENCE",base+"/successful_artifact"))
        if f["family_id"] in {"TYPED_STAGE_FAMILY_TERMINAL_RESULT","TYPED_TERMINAL_RESULT"} or art.get("record_type")=="agtxiv.typed-terminal-result/1.0.0":ds.append(_diag(DiagnosticCode.CATALOG_TERMINAL_POLICY_INVALID,"terminal result cannot recursively be a Catalog family","CATALOG_COHERENCE",base))
        v=_resolve_ref(f["validator_ref"],supports,media="text/x-python");vec=_resolve_ref(f["conformance_vector_ref"],supports,media="application/json")
        if v is None or vec is None:ds.append(_diag(DiagnosticCode.CATALOG_SUPPORT_ASSET_ROLE_INVALID,"validator or vector support asset does not resolve in its declared role","CATALOG_GRAPH",base))
        elif v[2] in root_bytes or vec[2] in root_bytes or v[2] in other_root_bytes or vec[2] in other_root_bytes:ds.append(_diag(DiagnosticCode.CATALOG_EXACT_REF_CYCLE,"Catalog support edge aliases a recognized root","CATALOG_GRAPH",base))
        vectors={}
        if vec:
            checked_vectors=_vector_index(vec[2],vec[0],_FIXED_VECTOR_SET_ID if doc.get("catalog_id")=="catalog:checkpoint-c-synthetic-linkage/1.0.0" else vec[0])
            if checked_vectors is None:ds.append(_diag(DiagnosticCode.CATALOG_SUPPORT_ASSET_ROLE_INVALID,"vector asset is not the closed canonical vector index","CATALOG_GRAPH",base+"/conformance_vector_ref"))
            else:vectors=checked_vectors
        positive=f["positive_vector_ids"];negative=f["negative_vector_ids"]
        if positive!=sorted(positive) or negative!=sorted(negative) or set(positive)&set(negative):ds.append(_diag(DiagnosticCode.CATALOG_STRUCTURE_INVALID,"vector IDs require disjoint lexicographic lists","CATALOG_COHERENCE",base))
        policies=f["stage_policies"]
        expected_order=[x for x in stage_ids if any(p["stage_id"]==x for p in policies)]
        if [p["stage_id"] for p in policies]!=expected_order or len(expected_order)!=len(policies):ds.append(_diag(DiagnosticCode.CATALOG_STRUCTURE_INVALID,"family stage policies must be unique in Catalog stage order","CATALOG_COHERENCE",base+"/stage_policies"))
        family_targets={
            (f["family_id"],f["family_version"],p["stage_id"],art["artifact_kind"])
            for p in policies
        }
        for polarity,ids in (("POSITIVE",positive),("NEGATIVE",negative)):
            for i in ids:
                x=vectors.get(i); target=x.get("target") if type(x) is dict else None
                target_key=(target.get("family_id"),target.get("family_version"),target.get("stage_id"),target.get("artifact_kind")) if type(target) is dict else None
                if not x or x.get("polarity")!=polarity or x.get("vector_kind")!="FAMILY_CONFORMANCE" or target_key not in family_targets:ds.append(_diag(DiagnosticCode.CATALOG_SUPPORT_ASSET_ROLE_INVALID,"listed vector has wrong polarity or family-stage target","CATALOG_COHERENCE",base,details={"vector_id":i}))
        for pi,p in enumerate(policies):
            used.add(p["stage_id"]); pb=f"{base}/stage_policies/{pi}"; c=p["cardinality"];mn=c["minimum_count"];mx=c["maximum_count"]
            if (p["applicability"],p["minimum_runtime_obligation"]) not in {("ALWAYS","CORE_REQUIRED"),("PROFILE_SELECTED","OPTIONAL_ALLOWED")}:ds.append(_diag(DiagnosticCode.CATALOG_STRUCTURE_INVALID,"applicability and minimum obligation matrix is invalid","CATALOG_COHERENCE",pb))
            if (p["minimum_runtime_obligation"]=="CORE_REQUIRED" and mn<1) or (p["minimum_runtime_obligation"]=="OPTIONAL_ALLOWED" and mn!=0) or (mx is not None and mx<mn):ds.append(_diag(DiagnosticCode.CATALOG_STRUCTURE_INVALID,"Catalog cardinality violates its minimum obligation","CATALOG_COHERENCE",pb+"/cardinality"))
            if p["allowed_producer_roles"]!=sorted(p["allowed_producer_roles"]):ds.append(_diag(DiagnosticCode.CATALOG_STRUCTURE_INVALID,"producer roles require lexicographic order","CATALOG_COHERENCE",pb+"/allowed_producer_roles"))
            tp=p["terminal_disposition_policy"]
            if p["accounting_unit"]=="CONTRACT_ASSET_INSTANCE" and tp["terminal_policy_mode"]!="FORBIDDEN":ds.append(_diag(DiagnosticCode.CATALOG_TERMINAL_POLICY_INVALID,"contract assets forbid bootstrap terminal cards","CATALOG_COHERENCE",pb))
            if tp["terminal_policy_mode"]=="STRUCTURALLY_PERMITTED":
                out=tp["structurally_permitted_outcomes"]
                if out!=[x for x in _OUTCOME_ORDER if x in out] or _CONTEXT_RANK[tp["minimum_declared_context_mode"]]<_CONTEXT_RANK[next(s["minimum_declared_context_mode"] for s in stages if s["stage_id"]==p["stage_id"])]:ds.append(_diag(DiagnosticCode.CATALOG_TERMINAL_POLICY_INVALID,"terminal outcomes or context violate Catalog policy","CATALOG_COHERENCE",pb))
            target={"family_id":f["family_id"],"family_version":f["family_version"],"stage_id":p["stage_id"],"artifact_kind":art["artifact_kind"]}
            for polarity,ids in (("POSITIVE",positive),("NEGATIVE",negative)):
                if not any(vectors.get(i,{}).get("polarity")==polarity and vectors.get(i,{}).get("target")==target for i in ids):ds.append(_diag(DiagnosticCode.CATALOG_SUPPORT_ASSET_ROLE_INVALID,"each family stage requires matching positive and negative vectors","CATALOG_COHERENCE",pb))
    if used!=set(stage_ids):ds.append(_diag(DiagnosticCode.CATALOG_STRUCTURE_INVALID,"every Catalog stage must be used by a family policy","CATALOG_COHERENCE"))
    return ds

def _profile_semantics(profile,catalog,catalog_ref):
    ds=[]
    if _asset_projection(profile["catalog_ref"])!=_asset_projection(catalog_ref):ds.append(_diag(DiagnosticCode.PROFILE_CATALOG_MISMATCH,"Profile does not exact-bind the supplied Catalog bytes","PROFILE_LINKAGE",pointer="/catalog_ref"));return ds,()
    stages=catalog["stages"]; sr=profile["stage_rules"]
    if [x["stage_id"] for x in sr]!=[x["stage_id"] for x in stages]:ds.append(_diag(DiagnosticCode.PROFILE_FAMILY_SET_INVALID,"Profile stage rules do not exactly mirror Catalog stages","PROFILE_LINKAGE",pointer="/stage_rules"))
    else:
        for i,(p,c) in enumerate(zip(sr,stages)):
            if _CONTEXT_RANK[p["minimum_declared_context_mode"]]<_CONTEXT_RANK[c["minimum_declared_context_mode"]]:ds.append(_diag(DiagnosticCode.PROFILE_CONTEXT_WEAKENING,"Profile stage context weakens Catalog context","PROFILE_MONOTONICITY",f"/stage_rules/{i}"))
    expected=[]; cmap={}
    for f in catalog["family_policy_rows"]:
        for p in f["stage_policies"]:
            k=(f["family_id"],f["family_version"],p["stage_id"]);expected.append(k);cmap[k]=p
    rules=profile["family_stage_rules"]; keys=[(r["family_id"],r["family_version"],r["stage_id"]) for r in rules]
    if keys!=expected:ds.append(_diag(DiagnosticCode.PROFILE_FAMILY_SET_INVALID,"Profile family-stage keys do not exactly mirror Catalog order","PROFILE_LINKAGE",pointer="/family_stage_rules"));return ds,()
    policies=[];stage_context={x["stage_id"]:x["minimum_declared_context_mode"] for x in sr}
    for i,(r,k) in enumerate(zip(rules,keys)):
        c=cmap[k]; adj=r["profile_requirement_adjustment"];base=f"/family_stage_rules/{i}"
        if c["minimum_runtime_obligation"]=="CORE_REQUIRED" and adj!="REQUIRED":ds.append(_diag(DiagnosticCode.PROFILE_REQUIREMENT_WEAKENING,"core Catalog obligation must remain required","PROFILE_MONOTONICITY",base))
        if adj=="NOT_SELECTED":policies.append(_Policy(*k,adj,(),"FORBIDDEN",(),stage_context[k[2]]));continue
        pc=r["cardinality"];cc=c["cardinality"]
        if pc["minimum_count"]<cc["minimum_count"] or (adj=="REQUIRED" and pc["minimum_count"]<1) or (adj=="OPTIONAL" and pc["minimum_count"]!=0) or (cc["maximum_count"] is not None and (pc["maximum_count"] is None or pc["maximum_count"]>cc["maximum_count"])) or (pc["maximum_count"] is not None and pc["maximum_count"]<pc["minimum_count"]):ds.append(_diag(DiagnosticCode.PROFILE_CARDINALITY_WEAKENING,"Profile cardinality weakens Catalog bounds","PROFILE_MONOTONICITY",base+"/cardinality"))
        roles=r["allowed_producer_roles"]
        if roles!=sorted(roles) or not set(roles)<=set(c["allowed_producer_roles"]):ds.append(_diag(DiagnosticCode.PROFILE_PRODUCER_EXPANSION,"Profile producer roles expand Catalog roles","PROFILE_MONOTONICITY",base+"/allowed_producer_roles"))
        pt=r["terminal_disposition_policy"];ct=c["terminal_disposition_policy"]
        if pt["terminal_policy_mode"]!=ct["terminal_policy_mode"]:ds.append(_diag(DiagnosticCode.PROFILE_TERMINAL_POLICY_MISMATCH,"Profile terminal mode differs from Catalog mode","PROFILE_MONOTONICITY",base))
        outcomes=tuple(pt.get("structurally_permitted_outcomes",()))
        minctx=stage_context[k[2]]
        if pt["terminal_policy_mode"]=="STRUCTURALLY_PERMITTED" and ct["terminal_policy_mode"]=="STRUCTURALLY_PERMITTED":
            if list(outcomes)!=[x for x in _OUTCOME_ORDER if x in outcomes] or not set(outcomes)<=set(ct["structurally_permitted_outcomes"]):ds.append(_diag(DiagnosticCode.PROFILE_OUTCOME_EXPANSION,"Profile outcomes expand or reorder Catalog outcomes","PROFILE_MONOTONICITY",base))
            minctx=pt["minimum_declared_context_mode"]
            if _CONTEXT_RANK[minctx]<max(_CONTEXT_RANK[stage_context[k[2]]],_CONTEXT_RANK[ct["minimum_declared_context_mode"]]):ds.append(_diag(DiagnosticCode.PROFILE_CONTEXT_WEAKENING,"Profile family context weakens effective minimum","PROFILE_MONOTONICITY",base))
        policies.append(_Policy(*k,adj,tuple(roles),pt["terminal_policy_mode"],outcomes,minctx))
    return ds,tuple(policies)

def build_catalog_profile_constraints(requirements_binding,catalog_binding,profile_binding,support_assets,registry):
    try:
        snapshots,ds=_snapshot_inputs((requirements_binding,catalog_binding,profile_binding),support_assets,registry)
        if ds:return ds
        roots,supports=snapshots; bound=[]
        expected_root=dict(_OFFICIAL_REQUIREMENTS_REF)
        if _asset_projection(roots[0][0])!=expected_root:return (_diag(DiagnosticCode.CATALOG_REFERENCE_INVALID,"requirement root differs from compiled official bytes","CATALOG_BINDING"),)
        for r in roots:
            x,p=_bind(r)
            if p:return (p,)
            bound.append(x)
        docs=[x[1] for x in bound]
        for i,key in enumerate(("requirements","catalog","profile")):
            findings=_validate_root(docs[i],registry,_OFFICIAL_SCHEMA_REFS[key],roots[i][1])
            if findings:return _sort_diagnostics(findings)
        findings=_requirements_semantics(docs[0],supports)
        if findings:return _sort_diagnostics(findings)
        root_bytes={r[3] for r in roots}; findings=_catalog_semantics(docs[1],supports,registry,root_bytes,{roots[2][3]})
        if findings:return _sort_diagnostics(findings)
        catalog_ref=roots[1][0]; findings,policies=_profile_semantics(docs[2],docs[1],catalog_ref)
        if findings:return _sort_diagnostics(findings)
        refs=[_parsed(r[0]) for r in roots]
        return CatalogProfileConstraints(refs[0],refs[1],refs[2],tuple(x["item_id"] for x in docs[0]["items"]),tuple(x["family_id"] for x in docs[1]["family_policy_rows"]),tuple(x["stage_id"] for x in docs[1]["stages"]),policies,_token=_CONSTRUCTION_TOKEN)
    except Exception:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"Catalog/Profile builder could not safely inspect submitted values","CATALOG_INPUT"),)

def _same_ref(a,b):return _asset_projection(a)==_asset_projection(b)
def validate_typed_terminal_result_catalog_constraints(record,registry,constraints):
    intrinsic=validate_typed_terminal_result_intrinsic(record,registry)
    if intrinsic:return intrinsic
    parts=_constraints_parts(constraints)
    if parts is None:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"constraints snapshot failed its exact type or seal","CATALOG_TERMINAL_INPUT"),)
    try:
        d=record.to_python();payload=d["payload"];ctx=payload["binding_context"];target=payload["target_obligation"]
        if not _same_ref(ctx["profile_ref"],parts[2].to_python()) or not _same_ref(ctx["catalog_ref"],parts[1].to_python()):return (_diag(DiagnosticCode.CATALOG_CONTEXT_BINDING_MISMATCH,"terminal context differs from exact Catalog/Profile constraints","CATALOG_TERMINAL",pointer="/payload/binding_context"),)
        fam=target["family_id"];stage=target["stage_id"]
        matches=[p for p in parts[6] if p.family_id==fam]
        if not matches:return (_diag(DiagnosticCode.CATALOG_UNKNOWN_FAMILY,"terminal targets an unknown Catalog family","CATALOG_TERMINAL",pointer="/payload/target_obligation/family_id"),)
        matches=[p for p in matches if p.stage_id==stage]
        if not matches:return (_diag(DiagnosticCode.CATALOG_UNKNOWN_STAGE,"terminal targets an unknown family stage","CATALOG_TERMINAL",pointer="/payload/target_obligation/stage_id"),)
        p=matches[0]
        if p.adjustment=="NOT_SELECTED":return (_diag(DiagnosticCode.CATALOG_OBLIGATION_NOT_SELECTED,"terminal targets an explicitly unselected Profile branch","CATALOG_TERMINAL"),)
        if p.terminal_mode=="FORBIDDEN":return (_diag(DiagnosticCode.CATALOG_TERMINAL_NOT_ALLOWED,"terminal cards are forbidden by effective policy","CATALOG_TERMINAL"),)
        role=d["envelope"]["producer_context"]["role"]
        if role not in p.roles:return (_diag(DiagnosticCode.CATALOG_PRODUCER_ROLE_NOT_ALLOWED,"terminal producer role is outside Profile subset","CATALOG_TERMINAL"),)
        if _CONTEXT_RANK[ctx["context_mode"]]<_CONTEXT_RANK[p.minimum_context]:return (_diag(DiagnosticCode.CATALOG_CONTEXT_MODE_INSUFFICIENT,"terminal declared context is weaker than Profile minimum","CATALOG_TERMINAL"),)
        if payload["outcome"] not in p.outcomes:return (_diag(DiagnosticCode.CATALOG_OUTCOME_NOT_ALLOWED,"terminal outcome is outside Profile subset","CATALOG_TERMINAL"),)
        return ()
    except Exception:return (_diag(DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,"terminal constraints could not safely inspect submitted values","CATALOG_TERMINAL_INPUT"),)

__all__=["RawContractAssetBinding","CatalogProfileConstraints","validate_m1_contract_requirement_set_intrinsic","build_catalog_profile_constraints","validate_typed_terminal_result_catalog_constraints"]
