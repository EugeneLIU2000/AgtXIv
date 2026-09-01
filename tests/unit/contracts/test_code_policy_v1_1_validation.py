from __future__ import annotations

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from agtxiv_v2.contracts import Diagnostic, ParsedCanonicalValue, RawContractAssetBinding, SchemaAssetBinding, SuppliedAsset, build_canonical_value, build_kernel_validation_policy_v1_1_constraints, build_schema_registry, canonical_bytes, raw_asset_sha256, validate_stable_code_catalog_v1_1_intrinsic  # noqa: E402
import agtxiv_v2.contracts.catalog_validation as catalog_validation  # noqa: E402
import agtxiv_v2.contracts.code_policy_v1_1_validation as successor  # noqa: E402
from agtxiv_v2.contracts.code_policy_v1_1_validation import CATALOG_LIMITS, POLICY_LIMITS, SCOPE_MEANING, SCOPE_REASON  # noqa: E402

OLD_SCHEMA=ROOT/"schemas/v2/contract-kernel/contract/stable-code-catalog/1.0.0.schema.json"
NEW_SCHEMA=ROOT/"schemas/v2/contract-kernel/contract/stable-code-catalog/1.1.0.schema.json"
OLD_ROOT=ROOT/"contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.0.0.json"


def _parsed(value: object)->ParsedCanonicalValue:
    result=build_canonical_value(value);assert type(result) is ParsedCanonicalValue;return result


def _asset_ref(asset: SuppliedAsset)->dict[str,object]:
    result={"asset_id":asset.asset_id,"media_type":asset.media_type,"byte_size":len(asset.raw_bytes),"sha256":raw_asset_sha256(asset.raw_bytes)}
    if asset.schema_uri is not None:result["schema_uri"]=asset.schema_uri
    return result


def _schema(path: Path,asset_id: str)->tuple[SchemaAssetBinding,dict[str,object]]:
    raw=path.read_bytes();uri=json.loads(raw)["$id"];asset=SuppliedAsset(asset_id,"application/schema+json",raw,uri);ref=_asset_ref(asset)
    return SchemaAssetBinding(_parsed(ref),asset),ref


def _root_binding(document: dict[str,object],asset_id: str)->RawContractAssetBinding:
    raw=canonical_bytes(_parsed(document));asset=SuppliedAsset(asset_id,"application/json",raw);return RawContractAssetBinding(_parsed(_asset_ref(asset)),asset)


def _fixture():
    old_schema,_=_schema(OLD_SCHEMA,"schema:stable-code-catalog:1.0.0");new_schema,new_schema_ref=_schema(NEW_SCHEMA,"schema:stable-code-catalog:1.1.0")
    common=[]
    for path in sorted((ROOT/"schemas/v2/contract-kernel/common").glob("*/*.schema.json")):
        common.append(_schema(path,"schema:common:"+path.parent.name+":1.0.0")[0])
    registry=build_schema_registry((old_schema,new_schema,*common));assert not isinstance(registry,tuple)
    old=json.loads(OLD_ROOT.read_bytes());old_binding=_root_binding(old,"codes:old")
    new=deepcopy(old);new["document_schema_ref"]=new_schema_ref;new["catalog_version"]="1.1.0";new["revision_kind"]="SUCCESSOR";new["predecessor_ref"]=old_binding.exact_ref.to_python();new["predecessor_version"]="1.0.0";new["resource_limits"]=dict(CATALOG_LIMITS);new["codes"].append({"code":SCOPE_REASON,"code_kind":"TERMINAL_REASON","kind_ordinal":2,"meaning":SCOPE_MEANING,"introduced_in_catalog_version":"1.1.0","status":"ACTIVE"})
    return old_binding,_root_binding(new,"codes:new"),registry,new


def test_successor_catalog_accepts_exact_append_only_projection() -> None:
    old,new,registry,_=_fixture()
    assert validate_stable_code_catalog_v1_1_intrinsic(old,new,registry)==()


@pytest.mark.parametrize("field",["code","code_kind","kind_ordinal","meaning","introduced_in_catalog_version","status"])
def test_every_predecessor_row_field_is_immutable(field: str) -> None:
    old,_,registry,new=_fixture();new["codes"][0][field]="MUTATED" if field!="kind_ordinal" else 999
    result=validate_stable_code_catalog_v1_1_intrinsic(old,_root_binding(new,"codes:new"),registry)
    assert result and type(result[0]) is Diagnostic


@pytest.mark.parametrize("mutation",["delete","insert","append-extra"])
def test_successor_rejects_every_non_append_only_row_set(mutation: str) -> None:
    old,_,registry,new=_fixture()
    if mutation=="delete":new["codes"].pop(0)
    elif mutation=="insert":new["codes"].insert(0,deepcopy(new["codes"][-1]))
    else:new["codes"].append(deepcopy(new["codes"][-1]))
    assert validate_stable_code_catalog_v1_1_intrinsic(old,_root_binding(new,"codes:new"),registry)


@pytest.mark.parametrize("field,value",[("catalog_version","1.0.0"),("revision_kind","GENESIS"),("predecessor_version","1.0.1"),("catalog_id","code-catalog:other")])
def test_successor_metadata_projection_is_frozen(field: str,value: str) -> None:
    old,_,registry,new=_fixture();new[field]=value
    assert validate_stable_code_catalog_v1_1_intrinsic(old,_root_binding(new,"codes:new"),registry)


def test_predecessor_reorder_and_same_id_different_bytes_fail() -> None:
    old,_,registry,new=_fixture();new["codes"][0],new["codes"][1]=new["codes"][1],new["codes"][0]
    assert validate_stable_code_catalog_v1_1_intrinsic(old,_root_binding(new,"codes:new"),registry)
    forged=RawContractAssetBinding(old.exact_ref,SuppliedAsset("codes:old","application/json",b"{}"))
    assert validate_stable_code_catalog_v1_1_intrinsic(forged,_root_binding(new,"codes:new"),registry)


@pytest.mark.parametrize("key,value",tuple(CATALOG_LIMITS.items()))
def test_every_catalog_resource_constant_is_frozen(key: str,value: int) -> None:
    old,_,registry,new=_fixture();new["resource_limits"][key]=value+1
    assert validate_stable_code_catalog_v1_1_intrinsic(old,_root_binding(new,"codes:new"),registry)


def test_successor_constants_freeze_three_support_assets_and_totals() -> None:
    assert POLICY_LIMITS["exact_support_assets"]==3
    assert POLICY_LIMITS["maximum_total_support_bytes"]==1_048_576+1_064_960+41_943_040
    assert POLICY_LIMITS["maximum_total_code_policy_input_bytes"]==44_943_536
    assert POLICY_LIMITS["exact_reason_registrations"]==2


def test_scope_reason_is_not_a_new_diagnostic_code() -> None:
    from agtxiv_v2.contracts import DiagnosticCode
    assert SCOPE_REASON not in {str(code) for code in DiagnosticCode}


def _load_helper(relative: str, name: str):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative);assert spec and spec.loader
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def _policy_fixture():
    cmod=_load_helper("tests/unit/contracts/test_catalog_profile_validation.py","_e_c_helpers")
    dmod=_load_helper("tests/unit/contracts/test_code_policy_validation.py","_e_d_helpers")
    inherited_c=cmod._build();d=dmod._build();assert not isinstance(inherited_c,tuple) and not isinstance(d,tuple)
    inherited_parts=catalog_validation._constraints_parts(inherited_c);assert inherited_parts is not None
    policies=tuple(catalog_validation._Policy(family,"1.0.0",stage,"REQUIRED",(role,),"STRUCTURALLY_PERMITTED" if family=="FROZEN_INVENTORY_SCOPE" else "FORBIDDEN",("BLOCKED",) if family=="FROZEN_INVENTORY_SCOPE" else (),"PLAN_BOUND") for family,stage,role in (("CONTRACT_BUNDLE_RELEASE","CONTRACT_BOOTSTRAP","CONTRACT_BUNDLE_BUILDER"),("PAPER_SOURCE_SNAPSHOT","SOURCE_FREEZE","SOURCE_SNAPSHOT_BUILDER"),("AGENTIZATION_PLAN","PLANNING","PLANNING_PRODUCER"),("INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","DISCOVERY_PRODUCER"),("SCOPE_FREEZE_DECISION","SCOPE_FREEZE","SCOPE_FREEZE_REVIEWER"),("FROZEN_INVENTORY_SCOPE","SCOPE_FREEZE","SCOPE_FREEZE_ISSUER")))
    c=catalog_validation.CatalogProfileConstraints(inherited_parts[0],inherited_parts[1],inherited_parts[2],inherited_parts[3],tuple(policy.family_id for policy in policies),("CONTRACT_BOOTSTRAP","SOURCE_FREEZE","PLANNING","INVENTORY_DISCOVERY","SCOPE_FREEZE"),policies,_token=catalog_validation._CONSTRUCTION_TOKEN)
    old_catalog,old_policy=dmod._roots()
    old_catalog_binding=_root_binding(json.loads(old_catalog.raw_bytes),old_catalog.asset_id)
    old_policy_binding=_root_binding(json.loads(old_policy.raw_bytes),old_policy.asset_id)
    _,new_catalog_binding,_,new_catalog=_fixture()
    new_catalog["predecessor_ref"]=_asset_ref(old_catalog)
    new_catalog_asset=SuppliedAsset("code-catalog:agtxiv-contract-kernel/1.1.0","application/json",canonical_bytes(_parsed(new_catalog)))
    new_catalog_binding=RawContractAssetBinding(_parsed(_asset_ref(new_catalog_asset)),new_catalog_asset)

    schema_paths=[*sorted((ROOT/"schemas/v2/contract-kernel/common").glob("*/*.schema.json")),
        ROOT/"schemas/v2/contract-kernel/contract/m1-contract-requirement-set/1.0.0.schema.json",
        ROOT/"schemas/v2/contract-kernel/contract/artifact-family-catalog/1.0.0.schema.json",
        ROOT/"schemas/v2/contract-kernel/contract/agentization-profile-release/1.0.0.schema.json",
        ROOT/"schemas/v2/contract-kernel/contract/stable-code-catalog/1.0.0.schema.json",
        ROOT/"schemas/v2/contract-kernel/contract/kernel-validation-policy/1.0.0.schema.json",
        ROOT/"schemas/v2/contract-kernel/contract/stable-code-catalog/1.1.0.schema.json",
        ROOT/"schemas/v2/contract-kernel/contract/kernel-validation-policy/1.1.0.schema.json",
        ROOT/"schemas/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0.schema.json",
        ROOT/"schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json",
        ROOT/"fixtures/v2-contract-kernel/catalog-profile/1.0.0/synthetic-immutable-record/1.0.0.schema.json"]
    ids={"m1-contract-requirement-set":"schema:m1-contract-requirement-set:1.0.0","artifact-family-catalog":"schema:artifact-family-catalog:1.0.0","agentization-profile-release":"schema:agentization-profile-release:1.0.0","stable-code-catalog":"schema:stable-code-catalog","kernel-validation-policy":"schema:kernel-validation-policy","discovery-obligation-policy":"schema:discovery-obligation-policy:1.0.0","typed-terminal-result":"schema:typed-terminal-result:1.0.0","synthetic-immutable-record":"schema:fixture:checkpoint-c-synthetic-record:1.0.0"}
    bindings=[];refs={}
    for path in schema_paths:
        version="1.1.0" if "/1.1.0." in str(path) else "1.0.0"
        key=path.parent.name;asset_id=(f"schema:common:{key}:1.0.0" if "common" in path.parts else f"{ids[key]}:{version}" if key in {"stable-code-catalog","kernel-validation-policy"} else ids[key])
        binding,ref=_schema(path,asset_id);bindings.append(binding);refs[(key,version)]=ref
    registry=build_schema_registry(tuple(bindings));assert not isinstance(registry,tuple)
    old=json.loads(old_policy.raw_bytes)
    validator=SuppliedAsset("validator:checkpoint-e-code-policy:1.1.0","text/x-python",b"x")
    vector_rows=[]
    for family,stage,lower in successor._E_VECTOR_TARGETS:
        target={"family_id":family,"family_version":"1.0.0","stage_id":stage,"artifact_kind":"IMMUTABLE_RECORD"};prefix=f"vector:checkpoint-e/{lower}/{stage.lower().replace('_','-')}";template=f"template:checkpoint-e/{lower}/valid-record"
        vector_rows.extend(({"vector_id":prefix+"/positive-valid","polarity":"POSITIVE","vector_kind":"FAMILY_CONFORMANCE","target":target,"template_id":template,"expected_diagnostic_codes":[]},{"vector_id":prefix+"/negative-closed-or-binding","polarity":"NEGATIVE","vector_kind":"FAMILY_CONFORMANCE","target":target,"template_id":template,"mutation_id":"mutation:closed-or-exact-binding","expected_diagnostic_codes":["AGTXIV.RECORD.PAYLOAD_INVALID"]}))
    vector_rows.sort(key=lambda row:row["vector_id"].encode());vectors_doc={"vector_set_id":"vectors:checkpoint-e-planning-families","vector_set_version":"1.0.0","fixture_purpose":"STRUCTURAL_CONFORMANCE_ONLY","vectors":vector_rows}
    vectors=SuppliedAsset("vectors:checkpoint-e-planning-families/1.0.0","application/json",canonical_bytes(_parsed(vectors_doc)))
    discovery_doc={"document_type":"AGTXIV_DISCOVERY_OBLIGATION_POLICY","document_schema_ref":refs[("discovery-obligation-policy","1.0.0")],"policy_id":"discovery-policy:checkpoint-e","policy_version":"1.0.0","policy_status":"NON_PRODUCTION_CANDIDATE","catalog_ref":c.catalog_ref.to_python(),"profile_ref":c.profile_ref.to_python(),"projection_algorithm":"AGTXIV_DISCOVERY_OBLIGATIONS_V1","applicability_vocabulary":["ALWAYS","IF_MATCHING_SOURCE_MEDIA_TYPE","IF_MATCHING_PATH_SUFFIX"],"component_matching_rules":["SOURCE_ROW_EQUALITY","REGION_SELECTOR_MATCH","COMPONENT_KIND_ALLOWED","ANCHOR_RANGE_WITHIN_SOURCE","OVERLAP_ALLOWED_ONLY_BY_MATRIX"],"resource_limits":{"maximum_discovery_obligations":256,"maximum_discovery_components":8192,"maximum_source_files":4096},"obligations":[{"obligation_id":oid,"family_id":family,"stage_id":stage,"region_selector":region,"required_component_kinds":list(kinds),"minimum_cardinality":1,"applicability_rule":{"rule":rule,"operands":list(operands)}} for oid,family,stage,region,kinds,rule,operands in (("obligation:checkpoint-e/bibliography","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","BIBLIOGRAPHY",("BIBLIOGRAPHY_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".bbl",".bib")),("obligation:checkpoint-e/opaque-binary","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","OPAQUE_BINARY",("FIGURE_BINARY","ARCHIVE_BINARY","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_SOURCE_MEDIA_TYPE",("text/x-tex","text/plain")),("obligation:checkpoint-e/source-row-accounting","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","EVERY_SOURCE_ROW",("DOCUMENT_TEXT","APPENDIX_TEXT","BIBLIOGRAPHY_TEXT","FIGURE_BINARY","ARCHIVE_BINARY","UNRESOLVED_SOURCE_REGION"),"ALWAYS",()),("obligation:checkpoint-e/tex-appendix","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","TEX_APPENDIX",("APPENDIX_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".tex",)),("obligation:checkpoint-e/tex-body","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","TEX_DOCUMENT_BODY",("DOCUMENT_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".tex",)),("obligation:checkpoint-e/frozen-inventory-scope","FROZEN_INVENTORY_SCOPE","SCOPE_FREEZE","WHOLE_SOURCE_TREE",("DOCUMENT_TEXT","APPENDIX_TEXT","BIBLIOGRAPHY_TEXT","FIGURE_BINARY","ARCHIVE_BINARY","UNRESOLVED_SOURCE_REGION"),"ALWAYS",()))]}
    discovery=SuppliedAsset("discovery-policy:checkpoint-e/1.0.0-candidate.1","application/json",canonical_bytes(_parsed(discovery_doc)))
    new=deepcopy(old);new.update({"document_schema_ref":refs[("kernel-validation-policy","1.1.0")],"policy_version":"1.1.0","revision_kind":"SUCCESSOR","predecessor_ref":old_policy_binding.exact_ref.to_python(),"predecessor_version":"1.0.0","code_catalog_ref":new_catalog_binding.exact_ref.to_python(),"inherited_registration_context_ref":old["structural_constraints_ref"],"structural_constraints_ref":{"requirements_ref":c.requirements_ref.to_python(),"catalog_ref":c.catalog_ref.to_python(),"profile_ref":c.profile_ref.to_python(),"discovery_policy_ref":_asset_ref(discovery),"constraint_source":"CHECKPOINT_E_SEALED_PLANNING_CONSTRAINTS"},"validator_ref":_asset_ref(validator),"conformance_vector_ref":_asset_ref(vectors),"validator_entry_points":{**successor.INHERITED_ENTRY_POINTS,**successor.ENTRY_POINTS},"gate_order":list(successor.INHERITED_GATE_ORDER+successor.GATE_SUFFIX),"resource_limits":dict(POLICY_LIMITS),"terminal_reason_registrations":[old["terminal_reason_registrations"][0],{"reason_code":SCOPE_REASON,"registration_kind":"PLANNING_SCOPE_BLOCK_ONLY","allowed_outcomes":["BLOCKED"],"allowed_retry_dispositions":["NO_RETRY_IN_CURRENT_CONTEXT"],"allowed_context_modes":["PLAN_BOUND"],"targets":[{"family_id":"FROZEN_INVENTORY_SCOPE","family_version":"1.0.0","stage_id":"SCOPE_FREEZE"}]}]})
    new_binding=_root_binding(new,"validation-policy:checkpoint-e/1.1.0")
    args=(old_catalog_binding,old_policy_binding,new_catalog_binding,new_binding,c,d,(validator,vectors,discovery),registry)
    return args,new


def test_successor_policy_composes_exact_predecessor_active_context_and_supports() -> None:
    args,_=_policy_fixture()
    result=build_kernel_validation_policy_v1_1_constraints(*args)
    assert not isinstance(result,tuple),result


@pytest.mark.parametrize("mutation",["gate-prefix","extra-entry","stale-active-c","support-substitution"])
def test_successor_policy_rejects_prefix_root_and_support_mutations(mutation: str) -> None:
    args,new=_policy_fixture();args=list(args)
    if mutation=="gate-prefix":new["gate_order"][0],new["gate_order"][1]=new["gate_order"][1],new["gate_order"][0]
    elif mutation=="extra-entry":new["validator_entry_points"]["extra"]="invented"
    elif mutation=="stale-active-c":new["structural_constraints_ref"]["catalog_ref"]={**new["structural_constraints_ref"]["catalog_ref"],"asset_id":"stale"}
    else:
        support=list(args[6]);support[0]=SuppliedAsset(support[0].asset_id,support[0].media_type,b"changed");args[6]=tuple(support)
    if mutation!="support-substitution":args[3]=_root_binding(new,"validation-policy:checkpoint-e/1.1.0")
    result=build_kernel_validation_policy_v1_1_constraints(*args)
    assert isinstance(result,tuple) and result


@pytest.mark.parametrize("role",["validator","vector","obligation","predecessor-catalog","predecessor-policy","successor-catalog","successor-policy"])
def test_successor_preflight_rejects_each_oversized_role_before_any_parser(monkeypatch: pytest.MonkeyPatch,role: str) -> None:
    args,_=_policy_fixture();args=list(args)
    if role in {"validator","vector","obligation"}:
        support_limits={"validator":(0,POLICY_LIMITS["maximum_validator_source_bytes"]),"vector":(1,POLICY_LIMITS["maximum_vector_index_bytes"]),"obligation":(2,POLICY_LIMITS["maximum_obligation_policy_root_bytes"])};supports=list(args[6]);index,limit=support_limits[role]
        original=supports[index];supports[index]=SuppliedAsset(original.asset_id,original.media_type,b"x"*(limit+1));args[6]=tuple(supports)
    else:
        root_limits={"predecessor-catalog":(0,401904),"predecessor-policy":(1,27072),"successor-catalog":(2,CATALOG_LIMITS["maximum_catalog_root_bytes"]),"successor-policy":(3,POLICY_LIMITS["maximum_policy_root_bytes"])};index,limit=root_limits[role]
        original=args[index];asset=original.supplied_asset;args[index]=RawContractAssetBinding(original.exact_ref,SuppliedAsset(asset.asset_id,asset.media_type,b"x"*(limit+1)))
    calls=[]
    def sentinel(*unused):calls.append(1);raise AssertionError("parser reached")
    monkeypatch.setattr(successor,"parse_canonical_json",sentinel)
    result=build_kernel_validation_policy_v1_1_constraints(*args)
    assert result and result[0].phase=="CODE_POLICY_V1_1_PREFLIGHT" and calls==[]
