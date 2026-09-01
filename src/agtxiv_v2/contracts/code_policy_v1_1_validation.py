"""Pure append-only Checkpoint E successors for Checkpoint D code policy.

The 1.0 roots remain immutable inputs.  This module accepts only a field-for-field
1.0 prefix plus the single frozen E terminal reason and validates all roots and
support bytes supplied by the caller; it performs no ambient lookup.
"""
from __future__ import annotations

import hashlib
from types import MappingProxyType
from typing import Any, Never

from .canonical import ParsedCanonicalValue, build_canonical_value, canonical_bytes, parse_canonical_json
from .catalog_validation import CatalogProfileConstraints, RawContractAssetBinding, _asset_projection, _constraints_parts
from .code_policy_validation import KernelValidationPolicyConstraints, _parts as _d_constraint_parts, validate_stable_code_catalog_intrinsic
from .diagnostics import Diagnostic, DiagnosticCode
from .references import SuppliedAsset, raw_asset_sha256
from .registry import ContractSchemaRegistry, _diagnostic, _registry_entries, _sort_diagnostics

CATALOG_LIMITS = MappingProxyType({"exact_code_entries":80,"maximum_code_utf8_bytes":256,"maximum_meaning_utf8_bytes":4096,"maximum_code_entry_bytes":4880,"maximum_root_metadata_bytes":18432,"maximum_catalog_root_bytes":408832})
POLICY_LIMITS = MappingProxyType({"exact_policy_roots":4,"exact_support_assets":3,"maximum_predecessor_total_root_bytes":428976,"maximum_catalog_root_bytes":408832,"maximum_policy_root_bytes":49152,"maximum_successor_total_root_bytes":457984,"maximum_total_root_bytes":886960,"maximum_exact_ref_bytes":2048,"maximum_validator_source_bytes":1048576,"maximum_vectors":512,"maximum_vector_entry_bytes":2048,"maximum_vector_index_bytes":1064960,"maximum_obligation_policy_root_bytes":41943040,"maximum_total_support_bytes":44056576,"maximum_total_code_policy_input_bytes":44943536,"exact_code_entries":80,"exact_reason_registrations":2,"exact_targets_per_registration":1,"exact_total_reason_targets":2,"maximum_emitted_diagnostics":4096})
SCOPE_REASON = "AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED"
SCOPE_MEANING = "Independent scope-freeze review did not accept the exact plan-bound discovery, so no FrozenInventoryScope was issued."
LEGACY = frozenset(("agtxiv.inventory-scope/2.0.0","https://agtxiv.org/schema/v2/inventory-scope/2.0.0"))
GATE_SUFFIX = ("TERMINAL_C_PUBLIC_INCLUDING_B_INTRINSIC_ONCE","TERMINAL_E_1_1_REASON_POLICY","TERMINAL_E_EXACT_PLANNING_BINDINGS")
INHERITED_GATE_ORDER = ("CODE_CATALOG_INTRINSIC","PYTHON_DIAGNOSTIC_BIJECTION","POLICY_INTRINSIC_AND_EXACT_BINDING","EMITTED_DIAGNOSTIC_REGISTRATION","TERMINAL_C_PUBLIC_INCLUDING_B_INTRINSIC","TERMINAL_D_REASON_POLICY")
INHERITED_ENTRY_POINTS = MappingProxyType({"catalog_intrinsic":"agtxiv_v2.contracts.code_policy_validation.validate_stable_code_catalog_intrinsic","policy_builder":"agtxiv_v2.contracts.code_policy_validation.build_kernel_validation_policy_constraints","diagnostic_registration":"agtxiv_v2.contracts.code_policy_validation.validate_emitted_diagnostic_registration","terminal_composition":"agtxiv_v2.contracts.code_policy_validation.validate_typed_terminal_result_kernel_constraints"})
ENTRY_POINTS = MappingProxyType({"paper_source_snapshot":"agtxiv_v2.contracts.planning_validation.validate_paper_source_snapshot","agentization_plan":"agtxiv_v2.contracts.planning_validation.validate_agentization_plan","inventory_discovery_result":"agtxiv_v2.contracts.planning_validation.validate_inventory_discovery_result","scope_freeze_decision":"agtxiv_v2.contracts.planning_validation.validate_scope_freeze_decision","frozen_inventory_scope":"agtxiv_v2.contracts.planning_validation.validate_frozen_inventory_scope","planning_scope_chain":"agtxiv_v2.contracts.planning_validation.validate_planning_scope_chain","scope_revision_impact":"agtxiv_v2.contracts.planning_validation.compute_scope_revision_impact","planning_terminal_constraints":"agtxiv_v2.contracts.planning_validation.validate_planning_terminal_constraints"})
_E_VECTOR_ASSET_ID="vectors:checkpoint-e-planning-families/1.0.0"
_E_VECTOR_SET_ID="vectors:checkpoint-e-planning-families"
_E_VECTOR_TARGETS=(("CONTRACT_BUNDLE_RELEASE","CONTRACT_BOOTSTRAP","contract-bundle-release"),("PAPER_SOURCE_SNAPSHOT","SOURCE_FREEZE","paper-source-snapshot"),("AGENTIZATION_PLAN","PLANNING","agentization-plan"),("INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","inventory-discovery-result"),("SCOPE_FREEZE_DECISION","SCOPE_FREEZE","scope-freeze-decision"),("FROZEN_INVENTORY_SCOPE","SCOPE_FREEZE","frozen-inventory-scope"))
_TOKEN=object()


def _diag(code,message,phase,pointer="",subject=None):return _diagnostic(code,message,pointer=pointer,phase=phase,subject=subject)
def _fail(message,phase="CODE_POLICY_V1_1_INPUT",code=DiagnosticCode.SCHEMA_INPUT_TYPE_MISMATCH,pointer=""):return (_diag(code,message,phase,pointer),)
def _parsed(value):
    result=build_canonical_value(value);return result if type(result) is ParsedCanonicalValue else None
def _ref(asset):
    value={"asset_id":asset.asset_id,"media_type":asset.media_type,"byte_size":len(asset.raw_bytes),"sha256":raw_asset_sha256(asset.raw_bytes)}
    if asset.schema_uri is not None:value["schema_uri"]=asset.schema_uri
    return value

def _binding(binding):
    if type(binding) is not RawContractAssetBinding:return None
    try:exact=object.__getattribute__(binding,"exact_ref");asset=object.__getattribute__(binding,"supplied_asset")
    except Exception:return None
    if type(exact) is not ParsedCanonicalValue or type(asset) is not SuppliedAsset:return None
    try:value=exact.to_python()
    except Exception:return None
    return (value,asset) if value==_ref(asset) and "path_hint" not in value else None

def _document(binding):
    fields=_binding(binding)
    if fields is None:return None
    parsed=parse_canonical_json(fields[1].raw_bytes)
    if type(parsed) is not ParsedCanonicalValue or canonical_bytes(parsed)!=fields[1].raw_bytes:return None
    value=parsed.to_python();return (value,fields[0],fields[1]) if type(value) is dict else None

def _document_from_asset(asset):
    if type(asset) is not SuppliedAsset:return None
    parsed=parse_canonical_json(asset.raw_bytes)
    if type(parsed) is not ParsedCanonicalValue or canonical_bytes(parsed)!=asset.raw_bytes:return None
    value=parsed.to_python();return value if type(value) is dict else None

def _schema_bound(document,registry,uri):
    entries=_registry_entries(registry)
    if entries is None:return False
    ref=document.get("document_schema_ref")
    if type(ref) is not dict or ref.get("schema_uri")!=uri:return False
    matches=[entry for entry in entries if entry.asset_id==ref.get("asset_id")]
    return len(matches)==1 and ref=={"asset_id":matches[0].asset_id,"media_type":matches[0].media_type,"byte_size":matches[0].byte_size,"sha256":matches[0].sha256,"schema_uri":matches[0].schema_id}


class KernelValidationPolicyV11Constraints:
    __slots__=("__refs","__reasons","__seal","__token")
    def __init__(self,refs,reasons,*,_token=None):
        if _token is not _TOKEN:raise TypeError("constraints are builder-created")
        raw=b"".join(canonical_bytes(x) for x in refs.values())+b"\x00".join(x.encode() for x in reasons)
        object.__setattr__(self,"_KernelValidationPolicyV11Constraints__refs",refs);object.__setattr__(self,"_KernelValidationPolicyV11Constraints__reasons",reasons);object.__setattr__(self,"_KernelValidationPolicyV11Constraints__seal",hashlib.sha256(raw).digest());object.__setattr__(self,"_KernelValidationPolicyV11Constraints__token",_TOKEN)
    def __setattr__(self,n,v)->Never:raise AttributeError("constraints are immutable")
    @property
    def terminal_reason_codes(self):
        parts=_parts(self)
        if parts is None:raise ValueError("constraints failed integrity")
        return parts[1]
    def __repr__(self):return "KernelValidationPolicyV11Constraints(<sealed candidate constraints>)"
def _parts(value):
    if type(value) is not KernelValidationPolicyV11Constraints:return None
    try:refs=object.__getattribute__(value,"_KernelValidationPolicyV11Constraints__refs");reasons=object.__getattribute__(value,"_KernelValidationPolicyV11Constraints__reasons");seal=object.__getattribute__(value,"_KernelValidationPolicyV11Constraints__seal");token=object.__getattribute__(value,"_KernelValidationPolicyV11Constraints__token");raw=b"".join(canonical_bytes(x) for x in refs.values())+b"\x00".join(x.encode() for x in reasons)
    except Exception:return None
    return (refs,reasons) if token is _TOKEN and type(refs) is MappingProxyType and type(reasons) is tuple and seal==hashlib.sha256(raw).digest() else None


def validate_stable_code_catalog_v1_1_intrinsic(predecessor_catalog_binding: RawContractAssetBinding, successor_catalog_binding: RawContractAssetBinding, registry: ContractSchemaRegistry) -> tuple[Diagnostic,...]:
    try:
        if type(registry) is not ContractSchemaRegistry or type(predecessor_catalog_binding) is not RawContractAssetBinding or type(successor_catalog_binding) is not RawContractAssetBinding:return _fail("catalog roots and registry require exact opaque types")
        try:
            old_asset=object.__getattribute__(predecessor_catalog_binding,"supplied_asset");new_asset=object.__getattribute__(successor_catalog_binding,"supplied_asset");old_raw=object.__getattribute__(old_asset,"raw_bytes");new_raw=object.__getattribute__(new_asset,"raw_bytes")
        except Exception:return _fail("catalog binding preflight failed")
        if type(old_asset) is not SuppliedAsset or type(new_asset) is not SuppliedAsset or type(old_raw) is not bytes or type(new_raw) is not bytes:return _fail("catalog root fields require exact opaque types")
        if len(new_raw)>CATALOG_LIMITS["maximum_catalog_root_bytes"]:return _fail("successor catalog exceeds root limit","CODE_CATALOG_V1_1_PREFLIGHT",DiagnosticCode.CODE_CATALOG_INVALID)
        predecessor=_document(predecessor_catalog_binding);successor=_document(successor_catalog_binding)
        if predecessor is None or successor is None:return _fail("catalog bindings are forged, noncanonical, or inexact")
        if len(successor[2].raw_bytes)>CATALOG_LIMITS["maximum_catalog_root_bytes"]:return _fail("successor catalog exceeds root limit","CODE_CATALOG_V1_1_PREFLIGHT",DiagnosticCode.CODE_CATALOG_INVALID)
        inherited=validate_stable_code_catalog_intrinsic(predecessor_catalog_binding,registry)
        if inherited:return inherited
        old,old_ref,_=predecessor;new,_,_=successor
        if not _schema_bound(new,registry,"https://agtxiv.org/schema/v2/contract-kernel/contract/stable-code-catalog/1.1.0"):return _fail("successor schema ref is not exact","CODE_CATALOG_V1_1_SCHEMA",DiagnosticCode.ASSET_SCHEMA_MISMATCH)
        fixed=("document_type","catalog_id","catalog_kind","compatibility_rules")
        expected_keys={"document_type","document_schema_ref","catalog_id","catalog_version","catalog_kind","revision_kind","predecessor_ref","predecessor_version","compatibility_rules","resource_limits","codes"}
        if set(new)!=expected_keys or any(new.get(k)!=old.get(k) for k in fixed) or new.get("catalog_version")!="1.1.0" or new.get("revision_kind")!="SUCCESSOR" or new.get("predecessor_ref")!=old_ref or new.get("predecessor_version")!="1.0.0":return _fail("successor metadata or predecessor projection differs from frozen compatibility","CODE_CATALOG_V1_1_COMPAT",DiagnosticCode.CODE_CATALOG_INVALID)
        expected={"code":SCOPE_REASON,"code_kind":"TERMINAL_REASON","kind_ordinal":2,"meaning":SCOPE_MEANING,"introduced_in_catalog_version":"1.1.0","status":"ACTIVE"}
        if new.get("codes",[])[:-1]!=old.get("codes") or new.get("codes",[])[-1:]!=[expected] or new.get("resource_limits")!=dict(CATALOG_LIMITS):return _fail("successor is not the exact immutable 79-row prefix plus sole E reason","CODE_CATALOG_V1_1_COMPAT",DiagnosticCode.CODE_CATALOG_INVALID)
        return ()
    except Exception:return _fail("catalog successor validation failed closed")


def _preflight_builder_inputs(bindings, catalog_profile_constraints, predecessor_constraints, support_assets, registry):
    if any(type(binding) is not RawContractAssetBinding for binding in bindings) or type(catalog_profile_constraints) is not CatalogProfileConstraints or type(predecessor_constraints) is not KernelValidationPolicyConstraints or type(support_assets) is not tuple or type(registry) is not ContractSchemaRegistry:
        return _fail("successor builder requires exact root, C/D constraint, support, and registry types")
    if len(support_assets)!=3 or any(type(asset) is not SuppliedAsset for asset in support_assets):
        return _fail("successor policy requires exactly three exact SuppliedAsset values",code=DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
    roots=[]
    for binding in bindings:
        try:ref=object.__getattribute__(binding,"exact_ref");asset=object.__getattribute__(binding,"supplied_asset");raw=object.__getattribute__(asset,"raw_bytes")
        except Exception:return _fail("root binding is forged")
        if type(ref) is not ParsedCanonicalValue or type(asset) is not SuppliedAsset or type(raw) is not bytes:return _fail("root binding fields require exact opaque types")
        roots.append(raw)
    try:support_fields=[(object.__getattribute__(asset,"asset_id"),object.__getattribute__(asset,"media_type"),object.__getattribute__(asset,"raw_bytes")) for asset in support_assets]
    except Exception:return _fail("support binding is forged")
    if any(type(asset_id) is not str or type(media) is not str or type(raw) is not bytes for asset_id,media,raw in support_fields):return _fail("support metadata/raw values require exact built-in types")
    expected_support={"validator:checkpoint-e-code-policy:1.1.0":("text/x-python",POLICY_LIMITS["maximum_validator_source_bytes"]),_E_VECTOR_ASSET_ID:("application/json",POLICY_LIMITS["maximum_vector_index_bytes"]),"discovery-policy:checkpoint-e/1.0.0-candidate.1":("application/json",POLICY_LIMITS["maximum_obligation_policy_root_bytes"])}
    if {asset_id for asset_id,_,_ in support_fields}!=set(expected_support) or any(media!=expected_support[asset_id][0] or len(raw)>expected_support[asset_id][1] for asset_id,media,raw in support_fields):return _fail("support role identity, media, or individual preflight limit differs from policy","CODE_POLICY_V1_1_PREFLIGHT",DiagnosticCode.CODE_POLICY_INVALID)
    support_raw=[raw for _,_,raw in support_fields]
    if len(set(roots+support_raw))!=len(roots)+len(support_raw):return _fail("root/support bytes alias or form a cycle",code=DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
    predecessor_total=len(roots[0])+len(roots[1]);successor_total=len(roots[2])+len(roots[3]);root_total=predecessor_total+successor_total
    if len(roots[0])>401904 or len(roots[1])>27072 or len(roots[2])>CATALOG_LIMITS["maximum_catalog_root_bytes"] or len(roots[3])>POLICY_LIMITS["maximum_policy_root_bytes"] or sum(map(len,support_raw))>POLICY_LIMITS["maximum_total_support_bytes"] or predecessor_total>POLICY_LIMITS["maximum_predecessor_total_root_bytes"] or successor_total>POLICY_LIMITS["maximum_successor_total_root_bytes"] or root_total>POLICY_LIMITS["maximum_total_root_bytes"]:return _fail("predecessor, successor, or aggregate roots exceed preflight limits","CODE_POLICY_V1_1_PREFLIGHT",DiagnosticCode.CODE_POLICY_INVALID)
    if root_total+sum(map(len,support_raw))>POLICY_LIMITS["maximum_total_code_policy_input_bytes"]:return _fail("aggregate successor inputs exceed preflight limit","CODE_POLICY_V1_1_PREFLIGHT",DiagnosticCode.CODE_POLICY_INVALID)
    return ()


def _exact_discovery_policy(document,cparts):
    kinds=("DOCUMENT_TEXT","APPENDIX_TEXT","BIBLIOGRAPHY_TEXT","FIGURE_BINARY","ARCHIVE_BINARY","UNRESOLVED_SOURCE_REGION")
    expected=(
      ("obligation:checkpoint-e/bibliography","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","BIBLIOGRAPHY",("BIBLIOGRAPHY_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".bbl",".bib")),
      ("obligation:checkpoint-e/opaque-binary","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","OPAQUE_BINARY",("FIGURE_BINARY","ARCHIVE_BINARY","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_SOURCE_MEDIA_TYPE",("text/x-tex","text/plain")),
      ("obligation:checkpoint-e/source-row-accounting","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","EVERY_SOURCE_ROW",kinds,"ALWAYS",()),
      ("obligation:checkpoint-e/tex-appendix","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","TEX_APPENDIX",("APPENDIX_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".tex",)),
      ("obligation:checkpoint-e/tex-body","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","TEX_DOCUMENT_BODY",("DOCUMENT_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".tex",)),
      ("obligation:checkpoint-e/frozen-inventory-scope","FROZEN_INVENTORY_SCOPE","SCOPE_FREEZE","WHOLE_SOURCE_TREE",kinds,"ALWAYS",()),)
    rows=[]
    for oid,family,stage,region,allowed,rule,operands in expected:rows.append({"obligation_id":oid,"family_id":family,"stage_id":stage,"region_selector":region,"required_component_kinds":list(allowed),"minimum_cardinality":1,"applicability_rule":{"rule":rule,"operands":list(operands)}})
    selected={(p.family_id,p.stage_id) for p in cparts[6] if p.adjustment!="NOT_SELECTED"}
    return document.get("applicability_vocabulary")==["ALWAYS","IF_MATCHING_SOURCE_MEDIA_TYPE","IF_MATCHING_PATH_SUFFIX"] and document.get("component_matching_rules")==["SOURCE_ROW_EQUALITY","REGION_SELECTOR_MATCH","COMPONENT_KIND_ALLOWED","ANCHOR_RANGE_WITHIN_SOURCE","OVERLAP_ALLOWED_ONLY_BY_MATRIX"] and document.get("resource_limits")=={"maximum_discovery_obligations":256,"maximum_discovery_components":8192,"maximum_source_files":4096} and document.get("obligations")==rows and {(row["family_id"],row["stage_id"]) for row in rows}<=selected


def _exact_e_vectors(document,asset_id):
    if asset_id!=_E_VECTOR_ASSET_ID or type(document) is not dict or set(document)!={"vector_set_id","vector_set_version","fixture_purpose","vectors"} or document.get("vector_set_id")!=_E_VECTOR_SET_ID or document.get("vector_set_version")!="1.0.0" or document.get("fixture_purpose")!="STRUCTURAL_CONFORMANCE_ONLY":return False
    expected=[]
    for family,stage,lower in _E_VECTOR_TARGETS:
        target={"family_id":family,"family_version":"1.0.0","stage_id":stage,"artifact_kind":"IMMUTABLE_RECORD"};template=f"template:checkpoint-e/{lower}/valid-record";prefix=f"vector:checkpoint-e/{lower}/{stage.lower().replace('_','-')}"
        expected.append({"vector_id":prefix+"/positive-valid","polarity":"POSITIVE","vector_kind":"FAMILY_CONFORMANCE","target":target,"template_id":template,"expected_diagnostic_codes":[]})
        expected.append({"vector_id":prefix+"/negative-closed-or-binding","polarity":"NEGATIVE","vector_kind":"FAMILY_CONFORMANCE","target":target,"template_id":template,"mutation_id":"mutation:closed-or-exact-binding","expected_diagnostic_codes":["AGTXIV.RECORD.PAYLOAD_INVALID"]})
    expected.sort(key=lambda row:row["vector_id"].encode())
    return document.get("vectors")==expected


def _supports(support_assets):
    if type(support_assets) is not tuple or len(support_assets)!=3 or any(type(x) is not SuppliedAsset for x in support_assets):return None
    ids=[x.asset_id for x in support_assets]
    if len(ids)!=len(set(ids)):return None
    media=sorted(x.media_type for x in support_assets)
    if media!=["application/json","application/json","text/x-python"]:return None
    sizes={"text/x-python":0,"vector":0,"obligation":0}
    for asset in support_assets:
        if asset.media_type=="text/x-python":sizes["text/x-python"]=len(asset.raw_bytes)
        else:
            parsed=parse_canonical_json(asset.raw_bytes)
            if type(parsed) is not ParsedCanonicalValue or canonical_bytes(parsed)!=asset.raw_bytes:return None
            doc=parsed.to_python()
            sizes["obligation" if doc.get("document_type")=="AGTXIV_DISCOVERY_OBLIGATION_POLICY" else "vector"]=len(asset.raw_bytes)
    if sizes["text/x-python"]>POLICY_LIMITS["maximum_validator_source_bytes"] or sizes["vector"]>POLICY_LIMITS["maximum_vector_index_bytes"] or sizes["obligation"]>POLICY_LIMITS["maximum_obligation_policy_root_bytes"] or sum(sizes.values())>POLICY_LIMITS["maximum_total_support_bytes"]:return None
    return support_assets


def build_kernel_validation_policy_v1_1_constraints(predecessor_catalog_binding: RawContractAssetBinding, predecessor_policy_binding: RawContractAssetBinding, successor_catalog_binding: RawContractAssetBinding, successor_policy_binding: RawContractAssetBinding, catalog_profile_constraints: CatalogProfileConstraints, predecessor_constraints: KernelValidationPolicyConstraints, support_assets: tuple[SuppliedAsset,...], registry: ContractSchemaRegistry) -> KernelValidationPolicyV11Constraints | tuple[Diagnostic,...]:
    try:
        preflight=_preflight_builder_inputs((predecessor_catalog_binding,predecessor_policy_binding,successor_catalog_binding,successor_policy_binding),catalog_profile_constraints,predecessor_constraints,support_assets,registry)
        if preflight:return preflight
        cparts=_constraints_parts(catalog_profile_constraints);dparts=_d_constraint_parts(predecessor_constraints)
        if cparts is None or dparts is None:return _fail("C/D constraints failed seal integrity")
        findings=validate_stable_code_catalog_v1_1_intrinsic(predecessor_catalog_binding,successor_catalog_binding,registry)
        if findings:return findings
        oldp=_document(predecessor_policy_binding);newp=_document(successor_policy_binding);newc=_document(successor_catalog_binding)
        supports=_supports(support_assets)
        if oldp is None or newp is None or newc is None or supports is None:return _fail("policy roots/support tuple is forged, noncanonical, or exceeds limits",code=DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        old,old_ref,_=oldp;new,_,asset=newp;oldc=_document(predecessor_catalog_binding)
        if oldc is None:return _fail("predecessor catalog binding is invalid")
        drefs=dparts[0]
        if drefs["code_catalog"].to_python()!=oldc[1] or drefs["policy"].to_python()!=old_ref:return _fail("predecessor D constraints do not bind supplied predecessor roots","CODE_POLICY_V1_1_COMPAT",DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        total=len(asset.raw_bytes)+len(newc[2].raw_bytes)+len(oldp[2].raw_bytes)+len(oldc[2].raw_bytes)+sum(len(x.raw_bytes) for x in supports)
        if len(asset.raw_bytes)>POLICY_LIMITS["maximum_policy_root_bytes"] or total>POLICY_LIMITS["maximum_total_code_policy_input_bytes"]:return _fail("policy input exceeds successor limits","CODE_POLICY_V1_1_PREFLIGHT",DiagnosticCode.CODE_POLICY_INVALID)
        if not _schema_bound(new,registry,"https://agtxiv.org/schema/v2/contract-kernel/contract/kernel-validation-policy/1.1.0"):return _fail("successor policy schema ref is not exact","CODE_POLICY_V1_1_SCHEMA",DiagnosticCode.ASSET_SCHEMA_MISMATCH)
        stable_fields=("document_type","policy_id","policy_kind","policy_status","terminal_schema_ref")
        if any(new.get(key)!=old.get(key) for key in stable_fields) or new.get("policy_version")!="1.1.0" or new.get("revision_kind")!="SUCCESSOR" or new.get("predecessor_ref")!=old_ref or new.get("predecessor_version")!="1.0.0" or new.get("inherited_registration_context_ref")!=old.get("structural_constraints_ref") or new.get("resource_limits")!=dict(POLICY_LIMITS):return _fail("policy predecessor, stable metadata, inherited context, or resource map differs from frozen values","CODE_POLICY_V1_1_COMPAT",DiagnosticCode.CODE_POLICY_INVALID)
        if new.get("code_catalog_ref")!=newc[1]:return _fail("policy does not exact-bind successor catalog","CODE_POLICY_V1_1_GRAPH",DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        structural=new.get("structural_constraints_ref",{})
        if set(structural)!={"requirements_ref","catalog_ref","profile_ref","discovery_policy_ref","constraint_source"} or structural.get("requirements_ref")!=cparts[0].to_python() or structural.get("catalog_ref")!=cparts[1].to_python() or structural.get("profile_ref")!=cparts[2].to_python() or structural.get("constraint_source")!="CHECKPOINT_E_SEALED_PLANNING_CONSTRAINTS":return _fail("active policy structural refs differ from sealed C constraints","CODE_POLICY_V1_1_GRAPH",DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        support_index={item.asset_id:item for item in supports}
        validator=support_index.get(new.get("validator_ref",{}).get("asset_id"));vectors=support_index.get(new.get("conformance_vector_ref",{}).get("asset_id"));obligation=support_index.get(structural.get("discovery_policy_ref",{}).get("asset_id"))
        if any(item is None for item in (validator,vectors,obligation)) or new["validator_ref"]!=_ref(validator) or new["conformance_vector_ref"]!=_ref(vectors) or structural["discovery_policy_ref"]!=_ref(obligation):return _fail("successor support refs do not resolve exact validator, vector, and discovery-policy bytes","CODE_POLICY_V1_1_GRAPH",DiagnosticCode.CODE_POLICY_REFERENCE_INVALID)
        obligation_doc=_document_from_asset(obligation);vector_doc=_document_from_asset(vectors)
        vector_rows=vector_doc.get("vectors") if type(vector_doc) is dict else None
        obligation_keys={"document_type","document_schema_ref","policy_id","policy_version","policy_status","catalog_ref","profile_ref","projection_algorithm","applicability_vocabulary","component_matching_rules","resource_limits","obligations"}
        if obligation_doc is None or set(obligation_doc)!=obligation_keys or obligation_doc.get("document_type")!="AGTXIV_DISCOVERY_OBLIGATION_POLICY" or obligation_doc.get("policy_version")!="1.0.0" or obligation_doc.get("policy_status")!="NON_PRODUCTION_CANDIDATE" or obligation_doc.get("projection_algorithm")!="AGTXIV_DISCOVERY_OBLIGATIONS_V1" or obligation_doc.get("catalog_ref")!=cparts[1].to_python() or obligation_doc.get("profile_ref")!=cparts[2].to_python() or not _exact_discovery_policy(obligation_doc,cparts) or not _schema_bound(obligation_doc,registry,"https://agtxiv.org/schema/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0") or vector_doc is None or set(vector_doc)!={"vector_set_id","vector_set_version","fixture_purpose","vectors"} or not _exact_e_vectors(vector_doc,vectors.asset_id) or type(vector_rows) is not list or not 1<=len(vector_rows)<=POLICY_LIMITS["maximum_vectors"] or len({row.get("vector_id") for row in vector_rows if type(row) is dict})!=len(vector_rows) or any(type(row) is not dict or type(row.get("vector_id")) is not str or _parsed(row) is None or len(canonical_bytes(_parsed(row)))>POLICY_LIMITS["maximum_vector_entry_bytes"] for row in vector_rows):return _fail("successor support documents are not canonical closed policy/vector metadata","CODE_POLICY_V1_1_GRAPH",DiagnosticCode.CODE_POLICY_INVALID)
        expected_keys={"document_type","document_schema_ref","policy_id","policy_version","policy_kind","policy_status","revision_kind","code_catalog_ref","structural_constraints_ref","terminal_schema_ref","validator_ref","conformance_vector_ref","validator_entry_points","gate_order","resource_limits","terminal_reason_registrations","predecessor_ref","predecessor_version","inherited_registration_context_ref"}
        if set(new)!=expected_keys or new.get("gate_order")!=list(INHERITED_GATE_ORDER+GATE_SUFFIX):return _fail("policy root or gate order differs from the exact inherited prefix plus E suffix","CODE_POLICY_V1_1_COMPAT",DiagnosticCode.CODE_POLICY_INVALID)
        entries=new.get("validator_entry_points",{});expected_entries={**INHERITED_ENTRY_POINTS,**ENTRY_POINTS}
        if entries!=expected_entries:return _fail("policy entry points differ from the exact inherited and planning set","CODE_POLICY_V1_1_COMPAT",DiagnosticCode.CODE_POLICY_INVALID)
        expected={"reason_code":SCOPE_REASON,"registration_kind":"PLANNING_SCOPE_BLOCK_ONLY","allowed_outcomes":["BLOCKED"],"allowed_retry_dispositions":["NO_RETRY_IN_CURRENT_CONTEXT"],"allowed_context_modes":["PLAN_BOUND"],"targets":[{"family_id":"FROZEN_INVENTORY_SCOPE","family_version":"1.0.0","stage_id":"SCOPE_FREEZE"}]}
        registrations=new.get("terminal_reason_registrations",[])
        if len(registrations)!=2 or registrations[0]!=old.get("terminal_reason_registrations",[None])[0] or registrations[-1]!=expected:return _fail("policy does not contain the exact inherited registration followed by E registration","CODE_POLICY_V1_1_REGISTRATION",DiagnosticCode.CODE_POLICY_INVALID)
        refs={"catalog":_parsed(newc[1]),"policy":_parsed(newp[1]),"predecessor_catalog":_parsed(_document(predecessor_catalog_binding)[1]),"predecessor_policy":_parsed(old_ref)}
        if any(x is None for x in refs.values()):return _fail("constraint refs cannot be sealed")
        return KernelValidationPolicyV11Constraints(MappingProxyType(refs),(registrations[0]["reason_code"],SCOPE_REASON),_token=_TOKEN)
    except Exception:return _fail("policy successor builder failed closed")


def validate_emitted_diagnostic_registration_v1_1(diagnostics: tuple[Diagnostic,...], constraints: KernelValidationPolicyV11Constraints) -> tuple[Diagnostic,...]:
    try:
        if _parts(constraints) is None or type(diagnostics) is not tuple:return _fail("diagnostics/constraints failed exact type or seal integrity","DIAGNOSTIC_REGISTRATION")
        if len(diagnostics)>POLICY_LIMITS["maximum_emitted_diagnostics"]:return _fail("diagnostic count exceeds policy limit","DIAGNOSTIC_REGISTRATION",DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED)
        bad=[_diag(DiagnosticCode.CODE_EMITTED_DIAGNOSTIC_UNREGISTERED,"emitted value is not a registered Diagnostic","DIAGNOSTIC_REGISTRATION",f"/{i}") for i,x in enumerate(diagnostics) if type(x) is not Diagnostic or type(x.code) is not DiagnosticCode]
        return _sort_diagnostics(bad)
    except Exception:return _fail("diagnostic registration failed closed","DIAGNOSTIC_REGISTRATION")


__all__=["CATALOG_LIMITS","POLICY_LIMITS","SCOPE_REASON","KernelValidationPolicyV11Constraints","validate_stable_code_catalog_v1_1_intrinsic","build_kernel_validation_policy_v1_1_constraints","validate_emitted_diagnostic_registration_v1_1"]
