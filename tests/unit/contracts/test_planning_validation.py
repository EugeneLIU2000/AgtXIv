from __future__ import annotations

import builtins
import hashlib
import json
import socket
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from agtxiv_v2.contracts import CatalogProfileConstraints, Diagnostic, ParsedCanonicalValue, SchemaAssetBinding, SuppliedAsset, build_canonical_value, build_schema_registry, canonical_bytes, record_content_hash, raw_asset_sha256, validate_paper_source_snapshot  # noqa: E402
import agtxiv_v2.contracts.catalog_validation as catalog_validation  # noqa: E402
import agtxiv_v2.contracts.code_policy_v1_1_validation as successor  # noqa: E402
import agtxiv_v2.contracts.planning_validation as planning  # noqa: E402
from agtxiv_v2.contracts.planning_validation import MAX_PATH_BYTES, ScopeRevisionLineageProjection, _source_root, _source_row_id  # noqa: E402

COMMON = sorted((ROOT / "schemas/v2/contract-kernel/common").glob("*/*.schema.json"))
BUNDLE_SCHEMA = ROOT / "schemas/v2/contract-kernel/contract/contract-bundle-release/1.0.0.schema.json"
SNAPSHOT_SCHEMA = ROOT / "schemas/v2/contract-kernel/source/paper-source-snapshot/1.0.0.schema.json"
DISCOVERY_SCHEMA = ROOT / "schemas/v2/contract-kernel/inventory/inventory-discovery-result/1.0.0.schema.json"
DECISION_SCHEMA = ROOT / "schemas/v2/contract-kernel/review/scope-freeze-decision/1.0.0.schema.json"
TERMINAL_SCHEMA = ROOT / "schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json"


def _canonical(value: object) -> bytes:
    parsed = build_canonical_value(value); assert type(parsed) is ParsedCanonicalValue
    return canonical_bytes(parsed)


def _schema_binding(path: Path) -> tuple[SchemaAssetBinding, dict[str, object]]:
    raw=path.read_bytes(); uri=json.loads(raw)["$id"]; asset=SuppliedAsset("schema:"+uri.rsplit("/schema/v2/",1)[-1].replace("/",":"),"application/schema+json",raw,uri)
    ref={"asset_id":asset.asset_id,"media_type":asset.media_type,"byte_size":len(raw),"sha256":raw_asset_sha256(raw),"schema_uri":uri}; parsed=build_canonical_value(ref);assert type(parsed) is ParsedCanonicalValue
    return SchemaAssetBinding(parsed,asset),ref


def _record(envelope: dict[str, object], payload: dict[str, object]) -> tuple[bytes,dict[str,object]]:
    document={"envelope":envelope,"payload":payload,"content_hash":"sha256:"+"0"*64}; parsed=build_canonical_value(document);assert type(parsed) is ParsedCanonicalValue
    digest=record_content_hash(parsed);assert type(digest) is str;document["content_hash"]=digest
    return _canonical(document),document


def _provenance_ref(bundle: dict[str, object]) -> dict[str, object]:
    return next(ref for ref in bundle["payload"]["contract_assets"] if ref["asset_id"]=="canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/provenance")


def _e_vector_document():
    rows=[]
    for family,stage,lower in successor_vector_targets():
        target={"family_id":family,"family_version":"1.0.0","stage_id":stage,"artifact_kind":"IMMUTABLE_RECORD"};prefix=f"vector:checkpoint-e/{lower}/{stage.lower().replace('_','-')}";template=f"template:checkpoint-e/{lower}/valid-record"
        rows.extend(({"vector_id":prefix+"/positive-valid","polarity":"POSITIVE","vector_kind":"FAMILY_CONFORMANCE","target":target,"template_id":template,"expected_diagnostic_codes":[]},{"vector_id":prefix+"/negative-closed-or-binding","polarity":"NEGATIVE","vector_kind":"FAMILY_CONFORMANCE","target":target,"template_id":template,"mutation_id":"mutation:closed-or-exact-binding","expected_diagnostic_codes":["AGTXIV.RECORD.PAYLOAD_INVALID"]}))
    rows.sort(key=lambda row:row["vector_id"].encode())
    return {"vector_set_id":"vectors:checkpoint-e-planning-families/1.0.0","vector_set_version":"1.0.0","fixture_purpose":"STRUCTURAL_CONFORMANCE_ONLY","vectors":rows}


def successor_vector_targets():
    return (("CONTRACT_BUNDLE_RELEASE","CONTRACT_BOOTSTRAP","contract-bundle-release"),("PAPER_SOURCE_SNAPSHOT","SOURCE_FREEZE","paper-source-snapshot"),("AGENTIZATION_PLAN","PLANNING","agentization-plan"),("INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","inventory-discovery-result"),("SCOPE_FREEZE_DECISION","SCOPE_FREEZE","scope-freeze-decision"),("FROZEN_INVENTORY_SCOPE","SCOPE_FREEZE","frozen-inventory-scope"))


def _exact_bundle_assets():
    schema_paths=[*sorted((ROOT/"schemas/v2/contract-kernel/common").glob("*/*.schema.json")),ROOT/"schemas/v2/contract-kernel/terminal/typed-terminal-result/1.0.0.schema.json",*sorted((ROOT/"schemas/v2/contract-kernel/contract").glob("*/1.0.0.schema.json")),ROOT/"schemas/v2/contract-kernel/contract/stable-code-catalog/1.1.0.schema.json",ROOT/"schemas/v2/contract-kernel/contract/kernel-validation-policy/1.1.0.schema.json",ROOT/"schemas/v2/contract-kernel/source/paper-source-snapshot/1.0.0.schema.json",ROOT/"schemas/v2/contract-kernel/planning/agentization-plan/1.0.0.schema.json",ROOT/"schemas/v2/contract-kernel/inventory/inventory-discovery-result/1.0.0.schema.json",ROOT/"schemas/v2/contract-kernel/review/scope-freeze-decision/1.0.0.schema.json",ROOT/"schemas/v2/contract-kernel/inventory/frozen-inventory-scope/1.0.0.schema.json",ROOT/"fixtures/v2-contract-kernel/catalog-profile/1.0.0/synthetic-immutable-record/1.0.0.schema.json",*sorted((ROOT/"fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas").glob("*/1.0.0.schema.json"))]
    by_uri={json.loads(path.read_bytes())["$id"]:path for path in schema_paths};assets=[]
    for asset_id,(role,media,uri) in planning.BUNDLE_ASSET_ROLES.items():
        if role=="schema_assets":assets.append(SuppliedAsset(asset_id,media,by_uri[uri].read_bytes(),uri))
    validator_files=("__init__.py","canonical.py","catalog_validation.py","code_policy_validation.py","code_policy_v1_1_validation.py","diagnostics.py","planning_validation.py","references.py","registry.py","schema_validation.py","terminal_validation.py")
    for asset_id,name in zip(planning._BUNDLE_VALIDATOR_IDS,validator_files):assets.append(SuppliedAsset(asset_id,"text/x-python",(ROOT/"src/agtxiv_v2/contracts"/name).read_bytes()))
    spec_paths=(ROOT/"docs/roadmaps/v2-end-to-end-implementation-plan.md",ROOT/"docs/adr/0003-plan-discovery-scope-freeze.md",ROOT/"docs/roadmaps/v2-m1-contract-kernel-checkpoint-e.md")
    for asset_id,path in zip(planning._BUNDLE_SPEC_IDS,spec_paths):assets.append(SuppliedAsset(asset_id,"text/markdown",path.read_bytes()))
    contract_paths={
      "requirements:m1-contract-requirement-set:1.0.0":ROOT/"contracts/v2/contract-kernel/requirements/m1-contract-requirement-set/1.0.0.json",
      "fixture-catalog:checkpoint-c-linkage/1.0.0":ROOT/"fixtures/v2-contract-kernel/catalog-profile/1.0.0/catalog.synthetic.json",
      "fixture-profile:checkpoint-c-linkage/1.0.0":ROOT/"fixtures/v2-contract-kernel/catalog-profile/1.0.0/profile.synthetic.json",
      "vectors:catalog-profile-linkage:checkpoint-c/1.0.0":ROOT/"fixtures/v2-contract-kernel/catalog-profile/1.0.0/family-conformance-vectors.json",
      "code-catalog:agtxiv-contract-kernel/1.0.0":ROOT/"contracts/v2/contract-kernel/code-policy/stable-code-catalog/1.0.0.json",
      "validation-policy:checkpoint-d-kernel-candidate/1.0.0":ROOT/"contracts/v2/contract-kernel/code-policy/kernel-validation-policy/1.0.0.json",
      "vectors:checkpoint-d-code-policy/1.0.0":ROOT/"fixtures/v2-contract-kernel/code-policy/1.0.0/code-policy-conformance-vectors.json",
      "canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/golden-vectors":ROOT/"fixtures/v2-contract-kernel/canonicalization-profile/2.0.0-candidate.1/golden-vectors.jsonl",
      "canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/provenance":ROOT/"fixtures/v2-contract-kernel/canonicalization-profile/2.0.0-candidate.1/provenance.json"}
    for asset_id,path in contract_paths.items():assets.append(SuppliedAsset(asset_id,planning.BUNDLE_ASSET_ROLES[asset_id][1],path.read_bytes()))
    vectors=SuppliedAsset("vectors:checkpoint-e-planning-families/1.0.0","application/json",_canonical(_e_vector_document()));assets.append(vectors)
    index={asset.asset_id:asset for asset in assets};schema_ref=lambda asset_id:planning._asset_ref(index[asset_id])
    stages=(("CONTRACT_BOOTSTRAP","PROFILE_BOUND"),("SOURCE_FREEZE","PROFILE_BOUND"),("PLANNING","PLAN_BOUND"),("INVENTORY_DISCOVERY","PLAN_BOUND"),("SCOPE_FREEZE","PLAN_BOUND"))
    families=(("CONTRACT_BUNDLE_RELEASE","CONTRACT","CONTRACT_BOOTSTRAP","CONTRACT_ASSET_INSTANCE","CONTRACT_BUNDLE_BUILDER","contract-bundle-release","agtxiv.contract-bundle-release/1.0.0","schema:contract-bundle-release:1.0.0"),("PAPER_SOURCE_SNAPSHOT","SOURCE","SOURCE_FREEZE","PAPER_ATTEMPT","SOURCE_SNAPSHOT_BUILDER","paper-source-snapshot","agtxiv.paper-source-snapshot/1.0.0","schema:paper-source-snapshot:1.0.0"),("AGENTIZATION_PLAN","PLANNING","PLANNING","PAPER_ATTEMPT","PLANNING_PRODUCER","agentization-plan","agtxiv.agentization-plan/1.0.0","schema:agentization-plan:1.0.0"),("INVENTORY_DISCOVERY_RESULT","INVENTORY","INVENTORY_DISCOVERY","PAPER_ATTEMPT","DISCOVERY_PRODUCER","inventory-discovery-result","agtxiv.inventory-discovery-result/1.0.0","schema:inventory-discovery-result:1.0.0"),("SCOPE_FREEZE_DECISION","REVIEW","SCOPE_FREEZE","PAPER_ATTEMPT","SCOPE_FREEZE_REVIEWER","scope-freeze-decision","agtxiv.scope-freeze-decision/1.0.0","schema:scope-freeze-decision:1.0.0"),("FROZEN_INVENTORY_SCOPE","INVENTORY","SCOPE_FREEZE","PAPER_ATTEMPT","SCOPE_FREEZE_ISSUER","frozen-inventory-scope","agtxiv.frozen-inventory-scope/1.0.0","schema:frozen-inventory-scope:1.0.0"))
    forbidden={"terminal_policy_mode":"FORBIDDEN"};scope_terminal={"terminal_policy_mode":"STRUCTURALLY_PERMITTED","structurally_permitted_outcomes":["BLOCKED"],"minimum_declared_context_mode":"PLAN_BOUND","declared_reason_policy":"DEFERRED_TO_EXACT_ERROR_CATALOG"}
    rows=[]
    for family,group,stage,unit,role,lower,rtype,schema_id in families:
        prefix=f"vector:checkpoint-e/{lower}/{stage.lower().replace('_','-')}";terminal=scope_terminal if family=="FROZEN_INVENTORY_SCOPE" else forbidden;validator_id="validator:checkpoint-a-immutable-record-payload:1.0.0" if family=="CONTRACT_BUNDLE_RELEASE" else "validator:checkpoint-e-planning-scope:1.0.0";entry="agtxiv_v2.contracts.schema_validation.validate_immutable_record_payload" if family=="CONTRACT_BUNDLE_RELEASE" else "agtxiv_v2.contracts.planning_validation."+{"PAPER_SOURCE_SNAPSHOT":"validate_paper_source_snapshot","AGENTIZATION_PLAN":"validate_agentization_plan","INVENTORY_DISCOVERY_RESULT":"validate_inventory_discovery_result","SCOPE_FREEZE_DECISION":"validate_scope_freeze_decision","FROZEN_INVENTORY_SCOPE":"validate_frozen_inventory_scope"}[family]
        rows.append({"family_id":family,"family_version":"1.0.0","family_group":group,"successful_artifact":{"artifact_kind":"IMMUTABLE_RECORD","schema_ref":schema_ref(schema_id),"record_type":rtype},"stage_policies":[{"stage_id":stage,"applicability":"ALWAYS","minimum_runtime_obligation":"CORE_REQUIRED","accounting_unit":unit,"cardinality":{"minimum_count":1,"maximum_count":1},"allowed_producer_roles":[role],"terminal_disposition_policy":terminal}],"validator_ref":planning._asset_ref(index[validator_id]),"validator_entry_point":entry,"conformance_vector_ref":planning._asset_ref(vectors),"positive_vector_ids":[prefix+"/positive-valid"],"negative_vector_ids":[prefix+"/negative-closed-or-binding"]})
    rows.sort(key=lambda row:row["family_id"])
    catalog_doc={"document_type":"AGTXIV_ARTIFACT_FAMILY_CATALOG","document_schema_ref":schema_ref("schema:artifact-family-catalog:1.0.0"),"catalog_id":"catalog:checkpoint-e-planning-families/1.0.0-candidate.1","catalog_version":"1.0.0","stages":[{"stage_id":stage,"ordinal":ordinal,"minimum_declared_context_mode":mode} for ordinal,(stage,mode) in enumerate(stages,1)],"family_policy_rows":rows}
    catalog=SuppliedAsset("catalog:checkpoint-e-planning-families/1.0.0-candidate.1","application/json",_canonical(catalog_doc));assets.append(catalog)
    profile_doc={"document_type":"AGTXIV_AGENTIZATION_PROFILE_RELEASE","document_schema_ref":schema_ref("schema:agentization-profile-release:1.0.0"),"profile_id":"profile:checkpoint-e-planning-families/1.0.0-candidate.1","profile_version":"1.0.0","profile_kind":"REUSABLE_OBLIGATION_POLICY","catalog_ref":planning._asset_ref(catalog),"stage_rules":[{"stage_id":stage,"minimum_declared_context_mode":mode} for stage,mode in stages],"family_stage_rules":[{"family_id":family,"family_version":"1.0.0","stage_id":stage,"profile_requirement_adjustment":"REQUIRED","cardinality":{"minimum_count":1,"maximum_count":1},"allowed_producer_roles":[role],"terminal_disposition_policy":scope_terminal if family=="FROZEN_INVENTORY_SCOPE" else forbidden} for family,_,stage,_,role,_,_,_ in sorted(families)]}
    profile=SuppliedAsset("profile:checkpoint-e-planning-families/1.0.0-candidate.1","application/json",_canonical(profile_doc));assets.append(profile)
    kinds=("DOCUMENT_TEXT","APPENDIX_TEXT","BIBLIOGRAPHY_TEXT","FIGURE_BINARY","ARCHIVE_BINARY","UNRESOLVED_SOURCE_REGION")
    obligation_rows=(("obligation:checkpoint-e/bibliography","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","BIBLIOGRAPHY",("BIBLIOGRAPHY_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".bbl",".bib")),("obligation:checkpoint-e/opaque-binary","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","OPAQUE_BINARY",("FIGURE_BINARY","ARCHIVE_BINARY","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_SOURCE_MEDIA_TYPE",("text/x-tex","text/plain")),("obligation:checkpoint-e/source-row-accounting","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","EVERY_SOURCE_ROW",kinds,"ALWAYS",()),("obligation:checkpoint-e/tex-appendix","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","TEX_APPENDIX",("APPENDIX_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".tex",)),("obligation:checkpoint-e/tex-body","INVENTORY_DISCOVERY_RESULT","INVENTORY_DISCOVERY","TEX_DOCUMENT_BODY",("DOCUMENT_TEXT","UNRESOLVED_SOURCE_REGION"),"IF_MATCHING_PATH_SUFFIX",(".tex",)),("obligation:checkpoint-e/frozen-inventory-scope","FROZEN_INVENTORY_SCOPE","SCOPE_FREEZE","WHOLE_SOURCE_TREE",kinds,"ALWAYS",()))
    discovery_doc={"document_type":"AGTXIV_DISCOVERY_OBLIGATION_POLICY","document_schema_ref":schema_ref("schema:discovery-obligation-policy:1.0.0"),"policy_id":"discovery-policy:checkpoint-e","policy_version":"1.0.0","policy_status":"NON_PRODUCTION_CANDIDATE","catalog_ref":planning._asset_ref(catalog),"profile_ref":planning._asset_ref(profile),"projection_algorithm":"AGTXIV_DISCOVERY_OBLIGATIONS_V1","applicability_vocabulary":["ALWAYS","IF_MATCHING_SOURCE_MEDIA_TYPE","IF_MATCHING_PATH_SUFFIX"],"component_matching_rules":["SOURCE_ROW_EQUALITY","REGION_SELECTOR_MATCH","COMPONENT_KIND_ALLOWED","ANCHOR_RANGE_WITHIN_SOURCE","OVERLAP_ALLOWED_ONLY_BY_MATRIX"],"resource_limits":{"maximum_discovery_obligations":256,"maximum_discovery_components":8192,"maximum_source_files":4096},"obligations":[{"obligation_id":oid,"family_id":family,"stage_id":stage,"region_selector":region,"required_component_kinds":list(allowed),"minimum_cardinality":1,"applicability_rule":{"rule":rule,"operands":list(operands)}} for oid,family,stage,region,allowed,rule,operands in obligation_rows]}
    discovery=SuppliedAsset("discovery-policy:checkpoint-e/1.0.0-candidate.1","application/json",_canonical(discovery_doc));assets.append(discovery)
    old_catalog=index["code-catalog:agtxiv-contract-kernel/1.0.0"];new_catalog_doc=json.loads(old_catalog.raw_bytes);new_catalog_doc.update({"document_schema_ref":schema_ref("schema:stable-code-catalog:1.1.0"),"catalog_version":"1.1.0","revision_kind":"SUCCESSOR","predecessor_ref":planning._asset_ref(old_catalog),"predecessor_version":"1.0.0","resource_limits":dict(successor.CATALOG_LIMITS)});new_catalog_doc["codes"].append({"code":successor.SCOPE_REASON,"code_kind":"TERMINAL_REASON","kind_ordinal":2,"meaning":successor.SCOPE_MEANING,"introduced_in_catalog_version":"1.1.0","status":"ACTIVE"})
    new_catalog=SuppliedAsset("code-catalog:agtxiv-contract-kernel/1.1.0","application/json",_canonical(new_catalog_doc));assets.append(new_catalog)
    old_policy=index["validation-policy:checkpoint-d-kernel-candidate/1.0.0"];new_policy_doc=json.loads(old_policy.raw_bytes);new_policy_doc.update({"document_schema_ref":schema_ref("schema:kernel-validation-policy:1.1.0"),"policy_version":"1.1.0","revision_kind":"SUCCESSOR","predecessor_ref":planning._asset_ref(old_policy),"predecessor_version":"1.0.0","code_catalog_ref":planning._asset_ref(new_catalog),"inherited_registration_context_ref":new_policy_doc["structural_constraints_ref"],"structural_constraints_ref":{"requirements_ref":planning._asset_ref(index["requirements:m1-contract-requirement-set:1.0.0"]),"catalog_ref":planning._asset_ref(catalog),"profile_ref":planning._asset_ref(profile),"discovery_policy_ref":planning._asset_ref(discovery),"constraint_source":"CHECKPOINT_E_SEALED_PLANNING_CONSTRAINTS"},"validator_ref":planning._asset_ref(index["validator:checkpoint-e-code-policy:1.1.0"]),"conformance_vector_ref":planning._asset_ref(vectors),"validator_entry_points":{**successor.INHERITED_ENTRY_POINTS,**successor.ENTRY_POINTS},"gate_order":list(successor.INHERITED_GATE_ORDER+successor.GATE_SUFFIX),"resource_limits":dict(successor.POLICY_LIMITS),"terminal_reason_registrations":[new_policy_doc["terminal_reason_registrations"][0],{"reason_code":successor.SCOPE_REASON,"registration_kind":"PLANNING_SCOPE_BLOCK_ONLY","allowed_outcomes":["BLOCKED"],"allowed_retry_dispositions":["NO_RETRY_IN_CURRENT_CONTEXT"],"allowed_context_modes":["PLAN_BOUND"],"targets":[{"family_id":"FROZEN_INVENTORY_SCOPE","family_version":"1.0.0","stage_id":"SCOPE_FREEZE"}]}]})
    assets.append(SuppliedAsset("validation-policy:checkpoint-e-kernel-candidate/1.1.0","application/json",_canonical(new_policy_doc)))
    index={asset.asset_id:asset for asset in assets};return tuple(index[asset_id] for asset_id in planning.BUNDLE_ASSET_ROLES)


def _fixture(path: str="main.tex", raw: bytes=b"abc"):
    assets=_exact_bundle_assets();bindings=[];refs={}
    for asset in assets:
        if asset.schema_uri is None:continue
        ref=planning._asset_ref(asset);binding=SchemaAssetBinding(build_canonical_value(ref),asset);bindings.append(binding);refs[asset.schema_uri]=ref
    registry=build_schema_registry(tuple(bindings));assert not isinstance(registry,tuple)
    index={asset.asset_id:asset for asset in assets};profile=planning._asset_ref(index["canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/golden-vectors"]);implementation=planning._asset_ref(index["validator:checkpoint-e-planning-scope:1.0.0"])
    manifest={role:[planning._asset_ref(index[asset_id]) for asset_id,(expected_role,_,_) in planning.BUNDLE_ASSET_ROLES.items() if expected_role==role] for role in ("schema_assets","contract_assets","validator_assets","specification_assets")}
    bundle_payload={"bundle_id":"contract-bundle:test/1","bundle_version":"1.0.0-candidate.1","bundle_status":"NON_PRODUCTION_CANDIDATE","canonicalization_profile_ref":profile,**manifest,"bundle_manifest_hash":"sha256:"+hashlib.sha256(b"AGTXIV_BUNDLE_ASSET_MANIFEST_V1\0"+_canonical(manifest)).hexdigest()}
    bundle_uri="https://agtxiv.org/schema/v2/contract-kernel/contract/contract-bundle-release/1.0.0";bundle_envelope={"record_type":"agtxiv.contract-bundle-release/1.0.0","schema_ref":refs[bundle_uri],"record_id":bundle_payload["bundle_id"],"record_revision":1,"created_at":"2026-09-01T00:00:00Z"}
    bundle_raw,bundle=_record(bundle_envelope,bundle_payload)
    digest=hashlib.sha256(raw).hexdigest();unit="source-unit:sha256:"+digest;row={"normalized_path":path,"source_row_id":_source_row_id(path,unit),"source_unit_id":unit,"sha256":"sha256:"+digest,"byte_size":len(raw),"media_type":"text/x-tex","content_kind":"TEXT"}
    sources={path:raw};snapshot_payload={"snapshot_id":"snapshot:test/1","snapshot_version":1,"source_origin_kind":"CALLER_SUPPLIED_LOCAL_FIXTURE","source_label":"synthetic","source_tree_algorithm":"AGTXIV_SOURCE_TREE_V1","source_tree_root":_source_root([row],sources),"source_file_count":1,"source_total_bytes":len(raw),"source_files":[row]}
    producer_context={"producer":{"actor_kind":"MECHANICAL_SERVICE","actor_id":"actor:snapshot-builder"},"role":"SOURCE_SNAPSHOT_BUILDER","attempt_id":"attempt:snapshot/1","implementation_ref":implementation,"environment_ref":_provenance_ref(bundle)}
    snapshot_uri="https://agtxiv.org/schema/v2/contract-kernel/source/paper-source-snapshot/1.0.0";snapshot_envelope={"record_type":"agtxiv.paper-source-snapshot/1.0.0","schema_ref":refs[snapshot_uri],"record_id":snapshot_payload["snapshot_id"],"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":producer_context}
    snapshot_raw,snapshot=_record(snapshot_envelope,snapshot_payload)
    return snapshot_raw,sources,assets,registry,bundle_raw,snapshot


def _plan_fixture():
    snapshot_raw,sources,assets,registry,bundle_raw,snapshot=_fixture();index={asset.asset_id:asset for asset in assets};bundle=json.loads(bundle_raw)
    discovery_policy=json.loads(index["discovery-policy:checkpoint-e/1.0.0-candidate.1"].raw_bytes);rows=snapshot["payload"]["source_files"]
    payload={"plan_id":"plan:test/1","plan_revision":1,"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot["payload"]["source_tree_root"],"contract_bundle_ref":planning._record_ref(bundle),"artifact_family_catalog_ref":planning._asset_ref(index["catalog:checkpoint-e-planning-families/1.0.0-candidate.1"]),"agentization_profile_ref":planning._asset_ref(index["profile:checkpoint-e-planning-families/1.0.0-candidate.1"]),"stable_code_catalog_ref":planning._asset_ref(index["code-catalog:agtxiv-contract-kernel/1.1.0"]),"kernel_validation_policy_ref":planning._asset_ref(index["validation-policy:checkpoint-e-kernel-candidate/1.1.0"]),"discovery_policy_ref":planning._asset_ref(index["discovery-policy:checkpoint-e/1.0.0-candidate.1"]),"resource_policy_ref":planning._asset_ref(index["validation-policy:checkpoint-e-kernel-candidate/1.1.0"]),"expected_source_units":rows,"profile_obligations":planning._project_obligations(discovery_policy,rows),"planning_context":"QUERY_INDEPENDENT"}
    context={"producer":{"actor_kind":"MECHANICAL_SERVICE","actor_id":"actor:planner"},"role":"PLANNING_PRODUCER","attempt_id":"attempt:plan/1","implementation_ref":planning._asset_ref(index["validator:checkpoint-e-planning-scope:1.0.0"]),"environment_ref":_provenance_ref(bundle)}
    schema_ref=planning._asset_ref(index["schema:agentization-plan:1.0.0"]);raw,document=_record({"record_type":"agtxiv.agentization-plan/1.0.0","schema_ref":schema_ref,"record_id":payload["plan_id"],"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":context},payload)
    return raw,snapshot_raw,sources,assets,registry,bundle_raw,document


def _full_chain_fixture(branch: str):
    plan_raw,snapshot_raw,sources,assets,registry,bundle_raw,plan=_plan_fixture();index={asset.asset_id:asset for asset in assets};bundle=json.loads(bundle_raw);snapshot=json.loads(snapshot_raw);row=snapshot["payload"]["source_files"][0]
    component={"component_id":"pending","source_row_id":row["source_row_id"],"source_unit_id":row["source_unit_id"],"normalized_path":row["normalized_path"],"byte_start":0,"byte_end":row["byte_size"],"component_kind":"DOCUMENT_TEXT","source_anchor_hash":"pending","classification_state":"CLASSIFIED","classification_or_issue_code":"AGTXIV.TEST.CLASSIFIED","evidence_refs":[]};component["component_id"],component["source_anchor_hash"]=planning._component_identity(component,row,sources[row["normalized_path"]])
    context=lambda role,actor,attempt:{"producer":{"actor_kind":"MECHANICAL_SERVICE" if role!="SCOPE_FREEZE_REVIEWER" else "HUMAN","actor_id":actor},"role":role,"attempt_id":attempt,"implementation_ref":planning._asset_ref(index["validator:checkpoint-e-planning-scope:1.0.0"]),"environment_ref":_provenance_ref(bundle)}
    coverage={key:row[key] for key in ("source_row_id","normalized_path","source_unit_id","sha256","byte_size","media_type","content_kind")};coverage.update({"component_ids":[component["component_id"]],"coverage_status":"COMPONENTS_RECORDED"})
    dispositions=[{"obligation_id":obligation["obligation_id"],"status":"SATISFIED","component_ids":[component["component_id"]],"finding_or_error_refs":[]} for obligation in plan["payload"]["profile_obligations"]]
    discovery_context=context("DISCOVERY_PRODUCER","actor:discoverer","attempt:discovery/1");discovery_payload={"discovery_id":"discovery:test/1","discovery_revision":1,"plan_ref":planning._record_ref(plan),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot["payload"]["source_tree_root"],"producer_context":discovery_context,"observed_resource_limits":{"maximum_discovery_components":8192,"maximum_discovery_obligations":256},"source_unit_coverage":[coverage],"classified_components":[component],"ambiguous_components":[],"unclassified_components":[],"obligation_dispositions":dispositions,"discovery_errors":[],"completeness_claim":"TOTAL_ACCOUNTED_PROFILE_RELATIVE"}
    discovery_raw,discovery=_record({"record_type":"agtxiv.inventory-discovery-result/1.0.0","schema_ref":planning._asset_ref(index["schema:inventory-discovery-result:1.0.0"]),"record_id":discovery_payload["discovery_id"],"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":discovery_context},discovery_payload)
    reviewer={"actor_kind":"HUMAN","actor_id":"actor:reviewer"};decision_context=context("SCOPE_FREEZE_REVIEWER",reviewer["actor_id"],"attempt:review/1");declarations=[{"producer_actor_id":"actor:discoverer","reviewer_actor_id":reviewer["actor_id"],"category":category,"disposition":"NO_CONFLICT_DECLARED"} for category in ("IDENTITY","ORGANIZATIONAL_CONTROL","BENEFICIAL_OWNERSHIP","OTHER")]
    findings=[] if branch=="ACCEPT" else [{"finding_id":"finding:block","severity":"BLOCKING","subject_kind":"PLAN","subject_id":plan["envelope"]["record_id"],"finding_code":"AGTXIV.TEST.BLOCK","summary":"Independent review did not accept scope issuance."}]
    decision_payload={"decision_id":f"decision:test/{branch.lower()}","decision_revision":1,"plan_ref":planning._record_ref(plan),"discovery_ref":planning._record_ref(discovery),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot["payload"]["source_tree_root"],"reviewer":reviewer,"reviewer_role":"SCOPE_FREEZE_REVIEWER","producer_actor_ref":discovery_context["producer"],"independence_declaration":"STRUCTURALLY_DISTINCT_ACTOR_IDS_DECLARED","conflict_declarations":declarations,"review_policy_ref":plan["payload"]["kernel_validation_policy_ref"],"findings":findings,"decision":branch}
    if branch=="BLOCK":decision_payload["terminal_requirement"]={"obligation_key":"obligation:checkpoint-e/frozen-inventory-scope","reason_code":"AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED","family_id":"FROZEN_INVENTORY_SCOPE","stage_id":"SCOPE_FREEZE","outcome":"BLOCKED","context_mode":"PLAN_BOUND"}
    decision_raw,decision=_record({"record_type":"agtxiv.scope-freeze-decision/1.0.0","schema_ref":planning._asset_ref(index["schema:scope-freeze-decision:1.0.0"]),"record_id":decision_payload["decision_id"],"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":decision_context},decision_payload)
    if branch=="ACCEPT":
        seed=planning._framed(plan["payload"]["plan_id"].encode())+planning._framed(snapshot["payload"]["snapshot_id"].encode());scope_id="inventory-scope:sha256:"+planning._hash(b"AGTXIV_SCOPE_ID_V1\0",seed);entries=[planning._scope_entry(scope_id,component)];scope_payload={"scope_id":scope_id,"scope_revision":1,"plan_ref":planning._record_ref(plan),"discovery_ref":planning._record_ref(discovery),"accept_decision_ref":planning._record_ref(decision),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot["payload"]["source_tree_root"],"revision_delta":{"kind":"GENESIS","added_entry_ids":[],"removed_entry_ids":[],"classification_changed_entry_ids":[],"source_binding_changed_entry_ids":[]},"scope_entries":entries};scope_context=context("SCOPE_FREEZE_ISSUER","actor:issuer","attempt:scope/1");record_id=f"inventory-scope-record:sha256:{scope_id.rsplit(':',1)[-1]}/revision/1";scope_raw,_=_record({"record_type":"agtxiv.frozen-inventory-scope/1.0.0","schema_ref":planning._asset_ref(index["schema:frozen-inventory-scope:1.0.0"]),"record_id":record_id,"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":scope_context},scope_payload);terminals=();scopes=(scope_raw,)
    else:
        scope_context=context("SCOPE_FREEZE_ISSUER","actor:issuer","attempt:scope-block/1");frozen_index=next(i for i,row_value in enumerate(plan["payload"]["profile_obligations"]) if row_value["obligation_id"]=="obligation:checkpoint-e/frozen-inventory-scope");plan_ref=planning._record_ref(plan);terminal_payload={"terminal_for_attempt":True,"terminal_scope":"ATTEMPT_ONLY","successful_artifact_produced":False,"satisfaction_claim":"NONE","attempt_id":scope_context["attempt_id"],"binding_context":{"context_mode":"PLAN_BOUND","profile_ref":plan["payload"]["agentization_profile_ref"],"catalog_ref":plan["payload"]["artifact_family_catalog_ref"],"plan_ref":plan_ref},"target_obligation":{"obligation_key":"obligation:checkpoint-e/frozen-inventory-scope","stage_id":"SCOPE_FREEZE","family_id":"FROZEN_INVENTORY_SCOPE","basis":{"basis_kind":"COMPONENT","component_ref":{**plan_ref,"component_id":"obligation:checkpoint-e/frozen-inventory-scope","json_pointer":f"/payload/profile_obligations/{frozen_index}"}}},"outcome":"BLOCKED","declared_reason":{"declared_reason_code":"AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED","summary":"Scope freeze was not accepted for the exact plan-bound discovery; no FrozenInventoryScope was issued."},"evidence":[{"evidence_id":"evidence:scope-freeze/block-decision","evidence_role":"POLICY_OBSERVATION","evidence_kind":"RECORD","record_ref":planning._record_ref(decision)},{"evidence_id":"evidence:scope-freeze/discovery","evidence_role":"INPUT_STATE","evidence_kind":"RECORD","record_ref":planning._record_ref(discovery)}],"retry":{"retry_disposition":"NO_RETRY_IN_CURRENT_CONTEXT","context_change_required":"A new independently reviewed scope-freeze attempt is required before scope issuance."},"next_action":{"action_code":"ESCALATE","description":"Escalate the blocked scope-freeze decision for an independently authorized new attempt.","responsible_actor":reviewer,"responsible_role":"SCOPE_FREEZE_REVIEWER","deadline":{"deadline_kind":"NO_DEADLINE","no_deadline_reason":"No production review schedule is authorized by Checkpoint E."}},"resources":{"limit":{"max_wall_time_ms":60000,"max_cpu_time_ms":60000,"max_peak_memory_bytes":134217728,"max_input_bytes":134217728,"max_output_bytes":41943040,"max_network_requests":0},"observed":{"network_requests":0},"unobserved_metrics":["wall_time_ms","cpu_time_ms","peak_memory_bytes","input_bytes","output_bytes"],"relation":"INDETERMINATE"}}
        terminal_raw,_=_record({"record_type":"agtxiv.typed-terminal-result/1.0.0","schema_ref":planning._asset_ref(index["schema:typed-terminal-result:1.0.0"]),"record_id":"terminal:test/block/1","record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":scope_context},terminal_payload);terminals=(terminal_raw,);scopes=()
    return (snapshot_raw,sources,plan_raw,discovery_raw,decision_raw,terminals,scopes,(),assets,registry,bundle_raw)


def _successor_chain_fixture(*, source_label: str="synthetic"):
    genesis_args=_full_chain_fixture("ACCEPT");old_snapshot_raw,old_sources,old_plan_raw,old_discovery_raw,old_decision_raw,_,genesis_scopes,_,assets,registry,bundle_raw=genesis_args;old_scope_raw=genesis_scopes[0];old_snapshot=json.loads(old_snapshot_raw);old_plan=json.loads(old_plan_raw);old_discovery=json.loads(old_discovery_raw);old_scope=json.loads(old_scope_raw);bundle=json.loads(bundle_raw);index={asset.asset_id:asset for asset in assets}
    sources={**old_sources,"notes.txt":b"unrelated"};digest=hashlib.sha256(sources["notes.txt"]).hexdigest();unit="source-unit:sha256:"+digest;new_row={"normalized_path":"notes.txt","source_row_id":_source_row_id("notes.txt",unit),"source_unit_id":unit,"sha256":"sha256:"+digest,"byte_size":len(sources["notes.txt"]),"media_type":"text/plain","content_kind":"TEXT"};rows=sorted([old_snapshot["payload"]["source_files"][0],new_row],key=lambda row:row["normalized_path"].encode())
    snapshot_payload=deepcopy(old_snapshot["payload"]);snapshot_payload.update({"snapshot_id":"snapshot:test/2","source_label":source_label,"source_tree_root":_source_root(rows,sources),"source_file_count":2,"source_total_bytes":sum(map(len,sources.values())),"source_files":rows});snapshot_envelope=deepcopy(old_snapshot["envelope"]);snapshot_envelope["record_id"]=snapshot_payload["snapshot_id"];snapshot_raw,snapshot=_record(snapshot_envelope,snapshot_payload)
    discovery_policy=json.loads(index["discovery-policy:checkpoint-e/1.0.0-candidate.1"].raw_bytes);plan_payload=deepcopy(old_plan["payload"]);plan_payload.update({"plan_id":"plan:test/2","source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot_payload["source_tree_root"],"expected_source_units":rows,"profile_obligations":planning._project_obligations(discovery_policy,rows)});plan_envelope=deepcopy(old_plan["envelope"]);plan_envelope["record_id"]=plan_payload["plan_id"];plan_raw,plan=_record(plan_envelope,plan_payload)
    old_component=old_discovery["payload"]["classified_components"][0];new_component={"component_id":"pending","source_row_id":new_row["source_row_id"],"source_unit_id":new_row["source_unit_id"],"normalized_path":new_row["normalized_path"],"byte_start":0,"byte_end":new_row["byte_size"],"component_kind":"DOCUMENT_TEXT","source_anchor_hash":"pending","classification_state":"CLASSIFIED","classification_or_issue_code":"AGTXIV.TEST.CLASSIFIED","evidence_refs":[]};new_component["component_id"],new_component["source_anchor_hash"]=planning._component_identity(new_component,new_row,sources[new_row["normalized_path"]]);components=sorted([old_component,new_component],key=lambda item:(item["normalized_path"].encode(),item["byte_start"],item["byte_end"],item["component_id"].encode()));row_by_id={row["source_row_id"]:row for row in rows};coverage=[]
    for row in rows:
        item={key:row[key] for key in ("source_row_id","normalized_path","source_unit_id","sha256","byte_size","media_type","content_kind")};item.update({"component_ids":[component["component_id"] for component in components if component["source_row_id"]==row["source_row_id"]],"coverage_status":"COMPONENTS_RECORDED"});coverage.append(item)
    dispositions=[]
    for obligation in plan_payload["profile_obligations"]:dispositions.append({"obligation_id":obligation["obligation_id"],"status":"SATISFIED","component_ids":[component["component_id"] for component in components if planning._component_matches_obligation(component,obligation,row_by_id)],"finding_or_error_refs":[]})
    discovery=deepcopy(old_discovery);discovery["payload"].update({"discovery_id":"discovery:test/2","plan_ref":planning._record_ref(plan),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot_payload["source_tree_root"],"source_unit_coverage":coverage,"classified_components":components,"obligation_dispositions":dispositions});discovery["envelope"]["record_id"]=discovery["payload"]["discovery_id"];discovery_raw,discovery=_record(discovery["envelope"],discovery["payload"])
    decision=json.loads(old_decision_raw);decision["payload"].update({"decision_id":"decision:test/2","plan_ref":planning._record_ref(plan),"discovery_ref":planning._record_ref(discovery),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot_payload["source_tree_root"]});decision["envelope"]["record_id"]=decision["payload"]["decision_id"];decision_raw,decision=_record(decision["envelope"],decision["payload"])
    entries=[planning._scope_entry(old_scope["payload"]["scope_id"],component) for component in components];new_payload=deepcopy(old_scope["payload"]);new_payload.update({"scope_revision":2,"plan_ref":planning._record_ref(plan),"discovery_ref":planning._record_ref(discovery),"accept_decision_ref":planning._record_ref(decision),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot_payload["source_tree_root"],"predecessor_scope_ref":planning._record_ref(old_scope),"revision_delta":{"kind":"SUCCESSOR",**planning._scope_delta(old_scope["payload"]["scope_entries"],entries)},"scope_entries":entries});new_envelope=deepcopy(old_scope["envelope"]);new_envelope.update({"record_id":new_envelope["record_id"].rsplit("/",1)[0]+"/2","record_revision":2,"supersedes_ref":planning._record_ref(old_scope)});new_scope_raw,new_scope=_record(new_envelope,new_payload)
    predecessor=planning.build_planning_scope_chain_declaration(old_snapshot_raw,old_sources,old_plan_raw,old_discovery_raw,old_decision_raw,old_scope_raw,assets,bundle_raw);assert not isinstance(predecessor,tuple);successor=planning.build_planning_scope_chain_declaration(snapshot_raw,sources,plan_raw,discovery_raw,decision_raw,new_scope_raw,assets,bundle_raw);assert not isinstance(successor,tuple);chain_args=(snapshot_raw,sources,plan_raw,discovery_raw,decision_raw,(),(new_scope_raw,),(predecessor,),assets,registry,bundle_raw)
    return chain_args,predecessor,successor,old_scope,new_scope


def test_in_memory_snapshot_validates_with_exact_provenance_environment() -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,snapshot=_fixture();bundle=json.loads(bundle_raw)
    assert snapshot["envelope"]["producer_context"]["environment_ref"]==_provenance_ref(bundle)
    assert snapshot["envelope"]["producer_context"]["environment_ref"]!=bundle["payload"]["canonicalization_profile_ref"]
    result=validate_paper_source_snapshot(snapshot_raw,sources,assets,registry,bundle_raw)
    assert not isinstance(result,tuple),result


@pytest.mark.parametrize("mutation",["golden-vectors","same-id-substitution"])
def test_snapshot_rejects_non_provenance_environment(mutation: str) -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,_=_fixture();snapshot=json.loads(snapshot_raw);bundle=json.loads(bundle_raw)
    if mutation=="golden-vectors":environment=bundle["payload"]["canonicalization_profile_ref"]
    else:environment=deepcopy(_provenance_ref(bundle));environment["sha256"]="sha256:"+"0"*64
    snapshot["envelope"]["producer_context"]["environment_ref"]=environment;changed_raw,_=_record(snapshot["envelope"],snapshot["payload"])
    result=validate_paper_source_snapshot(changed_raw,sources,assets,registry,bundle_raw)
    assert isinstance(result,tuple) and result and result[0].phase=="SOURCE_SNAPSHOT_BINDING"


def test_complete_exact_root_suite_validates_unpatched_positive_plan() -> None:
    plan_raw,snapshot_raw,sources,assets,registry,bundle_raw,_=_plan_fixture()
    result=planning.validate_agentization_plan(plan_raw,snapshot_raw,sources,assets,registry,bundle_raw)
    assert not isinstance(result,tuple),result


def test_authoritative_e_roots_pass_c_directly_and_unversioned_vector_set_fails() -> None:
    _,_,assets,registry,_,_=_fixture();index={asset.asset_id:asset for asset in assets};root_ids=("requirements:m1-contract-requirement-set:1.0.0","catalog:checkpoint-e-planning-families/1.0.0-candidate.1","profile:checkpoint-e-planning-families/1.0.0-candidate.1");registry_ids={entry.asset_id for entry in planning._registry_entries(registry)};support_ids=set().union(*(planning._referenced_asset_ids(json.loads(index[asset_id].raw_bytes)) for asset_id in root_ids))-set(root_ids)-registry_ids;supports=tuple(asset for asset in assets if asset.asset_id in support_ids);result=catalog_validation.build_catalog_profile_constraints(*(planning._raw_binding(index[asset_id]) for asset_id in root_ids),supports,registry)
    assert type(result) is CatalogProfileConstraints
    vector=index["vectors:checkpoint-e-planning-families/1.0.0"];vector_doc=json.loads(vector.raw_bytes);vector_doc["vector_set_id"]="vectors:checkpoint-e-planning-families";changed_vector=SuppliedAsset(vector.asset_id,vector.media_type,_canonical(vector_doc));catalog_doc=json.loads(index[root_ids[1]].raw_bytes)
    for row in catalog_doc["family_policy_rows"]:row["conformance_vector_ref"]=planning._asset_ref(changed_vector)
    changed_catalog=SuppliedAsset(index[root_ids[1]].asset_id,"application/json",_canonical(catalog_doc));profile_doc=json.loads(index[root_ids[2]].raw_bytes);profile_doc["catalog_ref"]=planning._asset_ref(changed_catalog);changed_profile=SuppliedAsset(index[root_ids[2]].asset_id,"application/json",_canonical(profile_doc));changed_supports=tuple(changed_vector if asset.asset_id==vector.asset_id else asset for asset in supports)
    assert isinstance(catalog_validation.build_catalog_profile_constraints(planning._raw_binding(index[root_ids[0]]),planning._raw_binding(changed_catalog),planning._raw_binding(changed_profile),changed_supports,registry),tuple)


@pytest.mark.parametrize("branch",["ACCEPT","BLOCK"])
def test_public_full_chain_validates_without_upstream_monkeypatches(branch: str) -> None:
    args=_full_chain_fixture(branch);bundle=json.loads(args[10]);provenance=_provenance_ref(bundle)
    for raw in (args[0],args[2],args[3],args[4],*args[5],*args[6]):assert json.loads(raw)["envelope"]["producer_context"]["environment_ref"]==provenance
    result=planning.validate_planning_scope_chain(*args)
    assert not isinstance(result,tuple),result
    assert result.to_python()["decision"]==branch


@pytest.mark.parametrize("mutation",["golden-vectors","same-id-substitution"])
def test_full_block_chain_rejects_non_provenance_terminal_environment(mutation: str) -> None:
    args=list(_full_chain_fixture("BLOCK"));bundle=json.loads(args[10]);terminal=json.loads(args[5][0])
    if mutation=="golden-vectors":environment=bundle["payload"]["canonicalization_profile_ref"]
    else:environment=deepcopy(_provenance_ref(bundle));environment["sha256"]="sha256:"+"0"*64
    terminal["envelope"]["producer_context"]["environment_ref"]=environment;changed_raw,_=_record(terminal["envelope"],terminal["payload"]);args[5]=(changed_raw,)
    result=planning.validate_planning_scope_chain(*args)
    assert isinstance(result,tuple) and result and result[0].phase=="TERMINAL_E_BINDING"


def test_public_successor_chain_validates_complete_oldest_to_immediate_history() -> None:
    args,_,_,old_scope,new_scope=_successor_chain_fixture();result=planning.validate_planning_scope_chain(*args)
    assert not isinstance(result,tuple),result
    old_entry=old_scope["payload"]["scope_entries"][0];unchanged=next(entry for entry in new_scope["payload"]["scope_entries"] if entry["normalized_path"]==old_entry["normalized_path"])
    assert unchanged==old_entry
    assert new_scope["payload"]["plan_ref"]!=old_scope["payload"]["plan_ref"]
    assert new_scope["payload"]["source_snapshot_ref"]!=old_scope["payload"]["source_snapshot_ref"]
    assert new_scope["payload"]["revision_delta"]=={"kind":"SUCCESSOR","added_entry_ids":[next(entry["scope_entry_id"] for entry in new_scope["payload"]["scope_entries"] if entry["normalized_path"]=="notes.txt")],"removed_entry_ids":[],"classification_changed_entry_ids":[],"source_binding_changed_entry_ids":[]}


def test_successor_rejects_cross_paper_source_label_lineage() -> None:
    args,_,_,_,_=_successor_chain_fixture(source_label="different-paper")
    result=planning.validate_planning_scope_chain(*args)
    assert isinstance(result,tuple) and result
    assert result[0].phase=="SCOPE_REVISION"


def test_genesis_rejects_nonempty_history_and_successor_rejects_truncated_history() -> None:
    genesis=list(_full_chain_fixture("ACCEPT"));declaration=planning.build_planning_scope_chain_declaration(genesis[0],genesis[1],genesis[2],genesis[3],genesis[4],genesis[6][0],genesis[8],genesis[10]);assert not isinstance(declaration,tuple);genesis[7]=(declaration,)
    assert isinstance(planning.validate_planning_scope_chain(*genesis),tuple)
    successor_args,_,_,_,_=_successor_chain_fixture();truncated=(*successor_args[:7],(),*successor_args[8:])
    assert isinstance(planning.validate_planning_scope_chain(*truncated),tuple)


@pytest.mark.parametrize("replacement",["text",bytearray(b"x"),memoryview(b"x")])
def test_snapshot_rejects_non_exact_raw_type(replacement: object) -> None:
    _,sources,assets,registry,bundle_raw,_=_fixture()
    result=validate_paper_source_snapshot(replacement,sources,assets,registry,bundle_raw)  # type: ignore[arg-type]
    assert isinstance(result,tuple) and result and type(result[0]) is Diagnostic


def test_snapshot_rejects_same_id_different_source_bytes() -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,_=_fixture()
    sources["main.tex"]=b"abd"
    assert isinstance(validate_paper_source_snapshot(snapshot_raw,sources,assets,registry,bundle_raw),tuple)


def test_path_limit_and_limit_plus_one_are_deterministic() -> None:
    for path in ("a"*MAX_PATH_BYTES,"é"*(MAX_PATH_BYTES//2)):
        args=_fixture(path)
        assert not isinstance(validate_paper_source_snapshot(args[0],args[1],args[2],args[3],args[4]),tuple)
    for path in ("a"*(MAX_PATH_BYTES+1),"é"*(MAX_PATH_BYTES//2+1)):
        args=_fixture(path)
        first=validate_paper_source_snapshot(args[0],args[1],args[2],args[3],args[4]);second=validate_paper_source_snapshot(args[0],args[1],args[2],args[3],args[4])
        assert isinstance(first,tuple) and [x.to_dict() for x in first]==[x.to_dict() for x in second]


@pytest.mark.parametrize("path",["/absolute.tex","../escape.tex","a/../b.tex","a\\b.tex","C:drive.tex","trailing. ","CON.tex","e\u0301.tex"])
def test_snapshot_rejects_noncanonical_or_unsafe_paths(path: str) -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,_=_fixture(path)
    result=validate_paper_source_snapshot(snapshot_raw,sources,assets,registry,bundle_raw)
    assert isinstance(result,tuple) and result


def test_bundle_manifest_cardinality_is_exactly_56() -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,_=_fixture()
    bundle=json.loads(bundle_raw)
    for delta in (-1,1):
        mutated=deepcopy(bundle)
        if delta<0:
            mutated["payload"]["schema_assets"].pop()
        else:
            row=deepcopy(mutated["payload"]["schema_assets"][-1]);row["asset_id"]="schema:filler:extra";mutated["payload"]["schema_assets"].append(row)
        manifest={key:mutated["payload"][key] for key in ("schema_assets","contract_assets","validator_assets","specification_assets")}
        mutated["payload"]["bundle_manifest_hash"]="sha256:"+hashlib.sha256(b"AGTXIV_BUNDLE_ASSET_MANIFEST_V1\0"+_canonical(manifest)).hexdigest()
        changed_raw,_=_record(mutated["envelope"],mutated["payload"])
        assert isinstance(validate_paper_source_snapshot(snapshot_raw,sources,assets,registry,changed_raw),tuple)


def test_bundle_rejects_role_preserving_schema_substitution() -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,_=_fixture();document=json.loads(bundle_raw)
    document["payload"]["schema_assets"][0]["schema_uri"]="https://agtxiv.org/schema/v2/contract-kernel/fixture/invented/1.0.0"
    manifest={key:document["payload"][key] for key in ("schema_assets","contract_assets","validator_assets","specification_assets")}
    document["payload"]["bundle_manifest_hash"]="sha256:"+hashlib.sha256(b"AGTXIV_BUNDLE_ASSET_MANIFEST_V1\0"+_canonical(manifest)).hexdigest()
    changed_raw,_=_record(document["envelope"],document["payload"])
    assert isinstance(validate_paper_source_snapshot(snapshot_raw,sources,assets,registry,changed_raw),tuple)


def test_record_size_preflight_precedes_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    _,sources,assets,registry,bundle_raw,_=_fixture()
    def sentinel(*args,**kwargs):raise AssertionError("parser reached before preflight")
    monkeypatch.setattr(planning,"parse_canonical_json",sentinel)
    result=validate_paper_source_snapshot(b"x"*(planning.MAX_RECORD_BYTES+1),sources,assets,registry,bundle_raw)
    assert isinstance(result,tuple) and result


def test_snapshot_rejects_wrong_or_missing_producer_role() -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,_=_fixture()
    original=json.loads(snapshot_raw)
    for mutation in ("wrong","missing"):
        document=deepcopy(original)
        if mutation=="wrong":document["envelope"]["producer_context"]["role"]="PLANNING_PRODUCER"
        else:document["envelope"].pop("producer_context")
        changed_raw,_=_record(document["envelope"],document["payload"])
        assert isinstance(validate_paper_source_snapshot(changed_raw,sources,assets,registry,bundle_raw),tuple)


def test_source_row_identity_is_path_sensitive_but_unit_identity_is_not() -> None:
    raw=b"same";digest=hashlib.sha256(raw).hexdigest();unit="source-unit:sha256:"+digest
    assert _source_row_id("a.tex",unit)!=_source_row_id("b.tex",unit)


def test_lineage_builder_rejects_list_substitution_and_cycles_in_programmatic_shape() -> None:
    assert isinstance(ScopeRevisionLineageProjection.build([],()),tuple)  # type: ignore[arg-type]
    projection=ScopeRevisionLineageProjection.build((("r:a","agtxiv.checkpoint-e-entry-output/1.0.0",b"{}","ENTRY_SET",("e:a",),()),),())
    assert not isinstance(projection,tuple)


def test_every_public_planning_seam_fails_closed_on_exact_type_substitution() -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,_=_fixture()
    assets=()
    calls=(
        lambda:planning.validate_paper_source_snapshot("bad",sources,(),registry,bundle_raw),
        lambda:planning.validate_agentization_plan("bad",snapshot_raw,sources,assets,registry,bundle_raw),
        lambda:planning.validate_inventory_discovery_result("bad",b"bad",snapshot_raw,sources,assets,registry,bundle_raw),
        lambda:planning.validate_scope_freeze_decision("bad",b"bad",b"bad",snapshot_raw,sources,assets,registry,bundle_raw),
        lambda:planning.validate_frozen_inventory_scope("bad",b"bad",b"bad",b"bad",snapshot_raw,sources,assets,registry,bundle_raw,()),
        lambda:planning.build_planning_scope_chain_declaration("bad",sources,b"bad",b"bad",b"bad",b"bad",assets,bundle_raw),
        lambda:planning.validate_planning_scope_chain(snapshot_raw,sources,b"bad",b"bad",b"bad",[],(),(),assets,registry,bundle_raw),
        lambda:planning.compute_scope_revision_impact((),object(),[],object(),registry),
        lambda:planning.validate_planning_terminal_constraints(object(),registry,object(),object(),b"bad",b"bad",b"bad",(),b"bad"),
    )
    for call in calls:
        result=call()
        assert isinstance(result,tuple) and result and all(type(item) is Diagnostic for item in result)


def test_valid_and_invalid_snapshot_use_no_ambient_io(monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot_raw,sources,assets,registry,bundle_raw,_=_fixture()
    def sentinel(*args,**kwargs):raise AssertionError("ambient I/O")
    monkeypatch.setattr(builtins,"open",sentinel);monkeypatch.setattr(socket,"socket",sentinel);monkeypatch.setattr(subprocess,"run",sentinel)
    assert not isinstance(validate_paper_source_snapshot(snapshot_raw,sources,assets,registry,bundle_raw),tuple)
    assert isinstance(validate_paper_source_snapshot(snapshot_raw,{"main.tex":b"wrong"},assets,registry,bundle_raw),tuple)


def _local_discovery_fixture(monkeypatch: pytest.MonkeyPatch):
    snapshot_raw,sources,assets,registry,bundle_raw,snapshot=_fixture();bundle=json.loads(bundle_raw)
    refs={path:planning._asset_ref(next(asset for asset in assets if asset.schema_uri==json.loads(path.read_bytes())["$id"])) for path in (DISCOVERY_SCHEMA,)}
    row=snapshot["payload"]["source_files"][0]
    plan={"envelope":{"record_type":"agtxiv.agentization-plan/1.0.0","schema_ref":{"asset_id":"schema:plan","media_type":"application/schema+json","byte_size":0,"sha256":"sha256:"+"0"*64,"schema_uri":"https://agtxiv.org/schema/v2/contract-kernel/planning/agentization-plan/1.0.0"},"record_id":"plan:test/1","record_revision":1},"payload":{"expected_source_units":[row],"profile_obligations":[{"obligation_id":"obligation:test","family_id":"INVENTORY_DISCOVERY_RESULT","stage_id":"INVENTORY_DISCOVERY","region_selector":"WHOLE_SOURCE_TREE","minimum_cardinality":1,"required_component_kinds":["DOCUMENT_TEXT"],"applicability_result":"APPLICABLE","matched_source_row_ids":[row["source_row_id"]]}]},"content_hash":"sha256:"+"1"*64}
    component={"component_id":"pending","source_row_id":row["source_row_id"],"source_unit_id":row["source_unit_id"],"normalized_path":row["normalized_path"],"byte_start":0,"byte_end":row["byte_size"],"component_kind":"DOCUMENT_TEXT","source_anchor_hash":"pending","classification_state":"CLASSIFIED","classification_or_issue_code":"AGTXIV.TEST.CLASSIFIED","evidence_refs":[]}
    component["component_id"],component["source_anchor_hash"]=planning._component_identity(component,row,sources[row["normalized_path"]])
    producer={"producer":{"actor_kind":"MECHANICAL_SERVICE","actor_id":"actor:discovery"},"role":"DISCOVERY_PRODUCER","attempt_id":"attempt:discovery/1","implementation_ref":bundle["payload"]["validator_assets"][0],"environment_ref":_provenance_ref(bundle)}
    payload={"discovery_id":"discovery:test/1","discovery_revision":1,"plan_ref":planning._record_ref(plan),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot["payload"]["source_tree_root"],"producer_context":producer,"observed_resource_limits":{"maximum_discovery_components":8192,"maximum_discovery_obligations":256},"source_unit_coverage":[{**row,"component_ids":[component["component_id"]],"coverage_status":"COMPONENTS_RECORDED"}],"classified_components":[component],"ambiguous_components":[],"unclassified_components":[],"obligation_dispositions":[{"obligation_id":"obligation:test","status":"SATISFIED","component_ids":[component["component_id"]],"finding_or_error_refs":[]}],"discovery_errors":[],"completeness_claim":"TOTAL_ACCOUNTED_PROFILE_RELATIVE"}
    envelope={"record_type":"agtxiv.inventory-discovery-result/1.0.0","schema_ref":refs[DISCOVERY_SCHEMA],"record_id":payload["discovery_id"],"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":producer}
    raw,document=_record(envelope,payload)
    monkeypatch.setattr(planning,"validate_agentization_plan",lambda *args:planning._SealedView("AgentizationPlan",plan,_token=planning._TOKEN))
    monkeypatch.setattr(planning,"validate_paper_source_snapshot",lambda *args:planning._SealedView("PaperSourceSnapshot",snapshot,_token=planning._TOKEN))
    args=(raw,b"plan",snapshot_raw,sources,assets,registry,bundle_raw)
    return args,document


def _blocked_discovery_fixture():
    plan_raw,snapshot_raw,sources,assets,registry,bundle_raw,plan=_plan_fixture();snapshot=json.loads(snapshot_raw);bundle=json.loads(bundle_raw);index={asset.asset_id:asset for asset in assets};row=snapshot["payload"]["source_files"][0];evidence=[planning._asset_ref(index["canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/provenance"])]
    component={"component_id":"pending","source_row_id":row["source_row_id"],"source_unit_id":row["source_unit_id"],"normalized_path":row["normalized_path"],"byte_start":0,"byte_end":row["byte_size"],"component_kind":"UNRESOLVED_SOURCE_REGION","source_anchor_hash":"pending","classification_state":"UNCLASSIFIED","classification_or_issue_code":"AGTXIV.TEST.DISCOVERY_BLOCKED","evidence_refs":evidence};component["component_id"],component["source_anchor_hash"]=planning._component_identity(component,row,sources[row["normalized_path"]]);error={"error_id":"error:discovery/blocked","error_code":component["classification_or_issue_code"],"summary":"Discovery could not classify the supplied source region.","evidence_refs":evidence};context={"producer":{"actor_kind":"MECHANICAL_SERVICE","actor_id":"actor:discoverer"},"role":"DISCOVERY_PRODUCER","attempt_id":"attempt:discovery/blocked","implementation_ref":planning._asset_ref(index["validator:checkpoint-e-planning-scope:1.0.0"]),"environment_ref":_provenance_ref(bundle)};coverage={key:row[key] for key in ("source_row_id","normalized_path","source_unit_id","sha256","byte_size","media_type","content_kind")};coverage.update({"component_ids":[component["component_id"]],"coverage_status":"BLOCKED_WITH_EVIDENCE"});dispositions=[{"obligation_id":obligation["obligation_id"],"status":"BLOCKED","component_ids":[component["component_id"]],"finding_or_error_refs":[error["error_id"]]} for obligation in plan["payload"]["profile_obligations"]];payload={"discovery_id":"discovery:test/blocked","discovery_revision":1,"plan_ref":planning._record_ref(plan),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot["payload"]["source_tree_root"],"producer_context":context,"observed_resource_limits":{"maximum_discovery_components":8192,"maximum_discovery_obligations":256},"source_unit_coverage":[coverage],"classified_components":[],"ambiguous_components":[],"unclassified_components":[component],"obligation_dispositions":dispositions,"discovery_errors":[error],"completeness_claim":"TOTAL_ACCOUNTED_PROFILE_RELATIVE"};envelope={"record_type":"agtxiv.inventory-discovery-result/1.0.0","schema_ref":planning._asset_ref(index["schema:inventory-discovery-result:1.0.0"]),"record_id":payload["discovery_id"],"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":context};raw,document=_record(envelope,payload)
    return (raw,plan_raw,snapshot_raw,sources,assets,registry,bundle_raw),document


def test_discovery_blocked_requires_bidirectional_affected_row_fallback_and_error_closure() -> None:
    args,_=_blocked_discovery_fixture();result=planning.validate_inventory_discovery_result(*args)
    assert not isinstance(result,tuple),result


@pytest.mark.parametrize("mutation",["zero-affected-rows","zero-relevant-components","classified-fallback","one-way-evidence"])
def test_discovery_blocked_reviewer_reproductions_fail(mutation: str) -> None:
    args,document=_blocked_discovery_fixture();payload=document["payload"]
    if mutation=="zero-affected-rows":payload["source_unit_coverage"][0]["coverage_status"]="COMPONENTS_RECORDED"
    elif mutation=="zero-relevant-components":payload["obligation_dispositions"][0]["component_ids"]=[]
    elif mutation=="classified-fallback":component=payload["unclassified_components"].pop();component["classification_state"]="CLASSIFIED";payload["classified_components"]=[component]
    else:payload["unclassified_components"][0]["evidence_refs"]=[planning._asset_ref(args[4][0])]
    changed,_=_record(document["envelope"],payload);assert isinstance(planning.validate_inventory_discovery_result(changed,*args[1:]),tuple)


def test_discovery_local_closure_accepts_complete_matching_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    args,_=_local_discovery_fixture(monkeypatch)
    assert not isinstance(planning.validate_inventory_discovery_result(*args),tuple)


@pytest.mark.parametrize("mutation",["missing-coverage","duplicate-component","partial-disposition","boolean-offset","oversized-path"])
def test_discovery_local_closure_rejects_adversarial_mutations(monkeypatch: pytest.MonkeyPatch,mutation: str) -> None:
    args,document=_local_discovery_fixture(monkeypatch);payload=document["payload"]
    if mutation=="missing-coverage":payload["source_unit_coverage"]=[]
    elif mutation=="duplicate-component":payload["ambiguous_components"]=[{**payload["classified_components"][0],"classification_state":"AMBIGUOUS"}]
    elif mutation=="partial-disposition":payload["obligation_dispositions"][0]["component_ids"]=[]
    elif mutation=="boolean-offset":payload["classified_components"][0]["byte_start"]=False
    else:payload["classified_components"][0]["normalized_path"]="é"*513
    changed,_=_record(document["envelope"],payload);changed_args=(changed,*args[1:])
    assert isinstance(planning.validate_inventory_discovery_result(*changed_args),tuple)


def test_component_matcher_rejects_wrong_region_and_out_of_range() -> None:
    row={"source_row_id":"row:1","normalized_path":"main.tex","media_type":"text/x-tex","byte_size":3};rows={row["source_row_id"]:row}
    obligation={"matched_source_row_ids":[row["source_row_id"]],"required_component_kinds":["APPENDIX_TEXT"],"region_selector":"TEX_APPENDIX"};component={"source_row_id":row["source_row_id"],"component_kind":"APPENDIX_TEXT","byte_start":0,"byte_end":3}
    assert not planning._component_matches_obligation(component,obligation,rows)
    obligation["region_selector"]="TEX_DOCUMENT_BODY";obligation["required_component_kinds"]=["DOCUMENT_TEXT"];component["component_kind"]="DOCUMENT_TEXT";component["byte_end"]=4
    assert not planning._component_matches_obligation(component,obligation,rows)


@pytest.mark.parametrize("kind,accepted",[("APPENDIX_TEXT",True),("BIBLIOGRAPHY_TEXT",False)])
def test_discovery_overlap_matrix_allows_only_frozen_kind_pairs(monkeypatch: pytest.MonkeyPatch,kind: str,accepted: bool) -> None:
    args,document=_local_discovery_fixture(monkeypatch);payload=document["payload"];row={key:payload["source_unit_coverage"][0][key] for key in ("source_row_id","source_unit_id","normalized_path","sha256","byte_size","media_type","content_kind")};component={**payload["classified_components"][0],"component_kind":kind,"component_id":"pending","source_anchor_hash":"pending"};component["component_id"],component["source_anchor_hash"]=planning._component_identity(component,row,args[3][row["normalized_path"]]);payload["classified_components"].append(component);payload["classified_components"].sort(key=lambda item:(item["normalized_path"].encode(),item["byte_start"],item["byte_end"],item["component_id"].encode()));payload["source_unit_coverage"][0]["component_ids"]=[item["component_id"] for item in payload["classified_components"]]
    changed,_=_record(document["envelope"],payload);result=planning.validate_inventory_discovery_result(changed,*args[1:])
    assert (not isinstance(result,tuple)) is accepted


def _document_from_ref(ref: dict[str,object],payload: dict[str,object]) -> dict[str,object]:
    return {"envelope":{key:ref[key] for key in ("record_type","record_id","record_revision","schema_ref")},"payload":payload,"content_hash":ref["content_hash"]}


def _local_decision_fixture(monkeypatch: pytest.MonkeyPatch):
    discovery_args,discovery=_local_discovery_fixture(monkeypatch);_,_,snapshot_raw,sources,assets,_,bundle_raw=discovery_args;bundle=json.loads(bundle_raw)
    registry=discovery_args[5];refs={DECISION_SCHEMA:planning._asset_ref(next(asset for asset in assets if asset.schema_uri==json.loads(DECISION_SCHEMA.read_bytes())["$id"]))}
    row={key:discovery["payload"]["source_unit_coverage"][0][key] for key in ("normalized_path","source_row_id","source_unit_id","sha256","byte_size","media_type","content_kind")}
    plan_ref=discovery["payload"]["plan_ref"];snapshot_ref=discovery["payload"]["source_snapshot_ref"]
    plan=_document_from_ref(plan_ref,{"plan_id":plan_ref["record_id"],"expected_source_units":[row],"profile_obligations":[{"obligation_id":"obligation:test"}],"kernel_validation_policy_ref":{"asset_id":"policy:test","media_type":"application/json","byte_size":0,"sha256":"sha256:"+"0"*64}})
    snapshot=_document_from_ref(snapshot_ref,{"snapshot_id":snapshot_ref["record_id"],"source_tree_root":discovery["payload"]["source_tree_root"]})
    bundle_ref=planning._record_ref(bundle)
    for document_value in (plan,discovery):document_value["envelope"]["contract_bundle_ref"]=bundle_ref
    reviewer={"actor_kind":"HUMAN","actor_id":"actor:reviewer"};producer=discovery["payload"]["producer_context"]["producer"]
    context={"producer":reviewer,"role":"SCOPE_FREEZE_REVIEWER","attempt_id":"attempt:review/1","implementation_ref":bundle["payload"]["validator_assets"][0],"environment_ref":_provenance_ref(bundle)}
    declarations=[{"producer_actor_id":producer["actor_id"],"reviewer_actor_id":reviewer["actor_id"],"category":category,"disposition":"NO_CONFLICT_DECLARED"} for category in ("IDENTITY","ORGANIZATIONAL_CONTROL","BENEFICIAL_OWNERSHIP","OTHER")]
    payload={"decision_id":"decision:test/1","decision_revision":1,"plan_ref":plan_ref,"discovery_ref":planning._record_ref(discovery),"source_snapshot_ref":snapshot_ref,"source_tree_root":discovery["payload"]["source_tree_root"],"reviewer":reviewer,"reviewer_role":"SCOPE_FREEZE_REVIEWER","producer_actor_ref":producer,"independence_declaration":"STRUCTURALLY_DISTINCT_ACTOR_IDS_DECLARED","conflict_declarations":declarations,"review_policy_ref":plan["payload"]["kernel_validation_policy_ref"],"findings":[],"decision":"ACCEPT"}
    envelope={"record_type":"agtxiv.scope-freeze-decision/1.0.0","schema_ref":refs[DECISION_SCHEMA],"record_id":payload["decision_id"],"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":context}
    raw,document=_record(envelope,payload)
    monkeypatch.setattr(planning,"validate_inventory_discovery_result",lambda *args:planning._SealedView("InventoryDiscoveryResult",discovery,_token=planning._TOKEN))
    monkeypatch.setattr(planning,"validate_agentization_plan",lambda *args:planning._SealedView("AgentizationPlan",plan,_token=planning._TOKEN))
    monkeypatch.setattr(planning,"validate_paper_source_snapshot",lambda *args:planning._SealedView("PaperSourceSnapshot",snapshot,_token=planning._TOKEN))
    args=(raw,b"discovery",b"plan",snapshot_raw,sources,assets,registry,bundle_raw)
    return args,document,(discovery,plan,snapshot)


def test_decision_local_semantics_accept_complete_independent_review(monkeypatch: pytest.MonkeyPatch) -> None:
    args,_,_=_local_decision_fixture(monkeypatch)
    assert not isinstance(planning.validate_scope_freeze_decision(*args),tuple)


@pytest.mark.parametrize("mutation",["same-actor","missing-declaration","conflict-without-finding","stale-policy","blocking-accept"])
def test_decision_local_semantics_reject_adversarial_mutations(monkeypatch: pytest.MonkeyPatch,mutation: str) -> None:
    args,document,_=_local_decision_fixture(monkeypatch);payload=document["payload"]
    if mutation=="same-actor":payload["reviewer"]["actor_id"]=payload["producer_actor_ref"]["actor_id"];document["envelope"]["producer_context"]["producer"]=payload["reviewer"]
    elif mutation=="missing-declaration":payload["conflict_declarations"].pop()
    elif mutation=="conflict-without-finding":payload["conflict_declarations"][0]["disposition"]="CONFLICT_DECLARED"
    elif mutation=="stale-policy":payload["review_policy_ref"]={**payload["review_policy_ref"],"asset_id":"policy:stale"}
    else:payload["findings"]=[{"finding_id":"finding:block","severity":"BLOCKING","subject_kind":"PLAN","subject_id":payload["plan_ref"]["record_id"],"finding_code":"AGTXIV.TEST.BLOCK","summary":"blocked"}]
    changed,_=_record(document["envelope"],payload);changed_args=(changed,*args[1:])
    assert isinstance(planning.validate_scope_freeze_decision(*changed_args),tuple)


def _local_scope_fixture(monkeypatch: pytest.MonkeyPatch):
    decision_args,decision,chain=_local_decision_fixture(monkeypatch);discovery,plan,snapshot=chain
    _,_,_,snapshot_raw,sources,assets,_,bundle_raw=decision_args;bundle=json.loads(bundle_raw)
    scope_schema=ROOT/"schemas/v2/contract-kernel/inventory/frozen-inventory-scope/1.0.0.schema.json"
    registry=decision_args[6];refs={scope_schema:planning._asset_ref(next(asset for asset in assets if asset.schema_uri==json.loads(scope_schema.read_bytes())["$id"]))}
    seed=planning._framed(plan["envelope"]["record_id"].encode())+planning._framed(snapshot["payload"]["snapshot_id"].encode())
    scope_id="inventory-scope:sha256:"+planning._hash(b"AGTXIV_SCOPE_ID_V1\0",seed)
    components=sum((discovery["payload"][name] for name in ("classified_components","ambiguous_components","unclassified_components")),[])
    entries=[planning._scope_entry(scope_id,component) for component in components]
    payload={"scope_id":scope_id,"scope_revision":1,"plan_ref":planning._record_ref(plan),"discovery_ref":planning._record_ref(discovery),"accept_decision_ref":planning._record_ref(decision),"source_snapshot_ref":planning._record_ref(snapshot),"source_tree_root":snapshot["payload"]["source_tree_root"],"revision_delta":{"kind":"GENESIS","added_entry_ids":[],"removed_entry_ids":[],"classification_changed_entry_ids":[],"source_binding_changed_entry_ids":[]},"scope_entries":entries}
    context={"producer":{"actor_kind":"MECHANICAL_SERVICE","actor_id":"actor:issuer"},"role":"SCOPE_FREEZE_ISSUER","attempt_id":"attempt:issuer/1","implementation_ref":bundle["payload"]["validator_assets"][0],"environment_ref":_provenance_ref(bundle)}
    envelope={"record_type":"agtxiv.frozen-inventory-scope/1.0.0","schema_ref":refs[scope_schema],"record_id":f"inventory-scope-record:sha256:{scope_id.rsplit(':',1)[-1]}/revision/1","record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":context}
    raw,document=_record(envelope,payload)
    monkeypatch.setattr(planning,"validate_scope_freeze_decision",lambda *args:planning._SealedView("ScopeFreezeDecision",decision,_token=planning._TOKEN))
    monkeypatch.setattr(planning,"validate_inventory_discovery_result",lambda *args:planning._SealedView("InventoryDiscoveryResult",discovery,_token=planning._TOKEN))
    monkeypatch.setattr(planning,"validate_agentization_plan",lambda *args:planning._SealedView("AgentizationPlan",plan,_token=planning._TOKEN))
    monkeypatch.setattr(planning,"validate_paper_source_snapshot",lambda *args:planning._SealedView("PaperSourceSnapshot",snapshot,_token=planning._TOKEN))
    args=(raw,b"decision",b"discovery",b"plan",snapshot_raw,sources,assets,registry,bundle_raw,())
    return args,document


def test_scope_genesis_accepts_exact_discovery_closure(monkeypatch: pytest.MonkeyPatch) -> None:
    args,_=_local_scope_fixture(monkeypatch)
    assert not isinstance(planning.validate_frozen_inventory_scope(*args),tuple)


@pytest.mark.parametrize("mutation",["wrong-id","wrong-delta","omitted-entry","changed-binding"])
def test_scope_genesis_rejects_identity_delta_and_closure_mutations(monkeypatch: pytest.MonkeyPatch,mutation: str) -> None:
    args,document=_local_scope_fixture(monkeypatch);payload=document["payload"]
    if mutation=="wrong-id":payload["scope_id"]="inventory-scope:sha256:"+"0"*64
    elif mutation=="wrong-delta":payload["revision_delta"]["added_entry_ids"]=[payload["scope_entries"][0]["scope_entry_id"]]
    elif mutation=="omitted-entry":payload["scope_entries"]=[]
    else:payload["scope_entries"][0]["normalized_path"]="changed.tex"
    changed,_=_record(document["envelope"],payload);changed_args=(changed,*args[1:])
    assert isinstance(planning.validate_frozen_inventory_scope(*changed_args),tuple)


def _impact_fixture(monkeypatch: pytest.MonkeyPatch):
    chain_args,predecessor,successor,old,new=_successor_chain_fixture();assets=chain_args[8];registry=chain_args[9];bundle=json.loads(chain_args[10]);downstream_paths=[ROOT/f"fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/{name}/1.0.0.schema.json" for name in ("entry-output","whole-scope-output","derived-output")];refs={path:planning._asset_ref(next(asset for asset in assets if asset.schema_uri==json.loads(path.read_bytes())["$id"])) for path in downstream_paths};entry_id=old["payload"]["scope_entries"][0]["scope_entry_id"]
    records=[];nodes=[];kinds=(("entry-output","agtxiv.checkpoint-e-entry-output/1.0.0","ENTRY_SET",[entry_id],[entry_id]),("whole-scope-output","agtxiv.checkpoint-e-whole-scope-output/1.0.0","WHOLE_SCOPE",[],[entry_id]),("derived-output","agtxiv.checkpoint-e-derived-output/1.0.0","ENTRY_SET",[entry_id],[]))
    for index,(name,rtype,mode,inputs,outputs) in enumerate(kinds):
        context=old["envelope"]["producer_context"];rid=f"downstream:{name}/{index}";envelope={"record_type":rtype,"schema_ref":refs[downstream_paths[index]],"record_id":rid,"record_revision":1,"contract_bundle_ref":planning._record_ref(bundle),"created_at":"2026-09-01T00:00:00Z","producer_context":context};payload={"scope_ref":planning._record_ref(old),"coverage_mode":mode,"input_entry_ids":inputs,"output_entry_ids":outputs};raw,_=_record(envelope,payload);records.append(raw);nodes.append((rid,rtype,_canonical(payload["scope_ref"]),mode,tuple(inputs),tuple(outputs)))
    projection=ScopeRevisionLineageProjection.build(tuple(nodes),((nodes[0][0],nodes[2][0],"DERIVED_FROM"),));assert not isinstance(projection,tuple)
    return ((predecessor,),successor,tuple(records),projection,registry),records,nodes


def test_revision_impact_validates_semantic_scopes_and_record_specific_lineage(monkeypatch: pytest.MonkeyPatch) -> None:
    args,_,_=_impact_fixture(monkeypatch);result=planning.compute_scope_revision_impact(*args)
    assert not isinstance(result,tuple),result
    impact=result.to_python();assert impact["affected_whole_scope_output_ids"]==["downstream:whole-scope-output/1"]


@pytest.mark.parametrize("mutation",["derived-output","unknown-input","cycle","stale-scope"])
def test_revision_impact_rejects_record_specific_and_graph_mutations(monkeypatch: pytest.MonkeyPatch,mutation: str) -> None:
    args,records,nodes=_impact_fixture(monkeypatch);history,successor,_,projection,registry=args
    if mutation in {"derived-output","unknown-input","stale-scope"}:
        index=2 if mutation=="derived-output" else 0;document=json.loads(records[index])
        if mutation=="derived-output":document["payload"]["output_entry_ids"]=[nodes[0][4][0]]
        elif mutation=="unknown-input":document["payload"]["input_entry_ids"]=["scope-entry:unknown"]
        else:document["payload"]["scope_ref"]={**document["payload"]["scope_ref"],"content_hash":"sha256:"+"0"*64}
        records[index],_=_record(document["envelope"],document["payload"])
    else:
        projection=ScopeRevisionLineageProjection.build(tuple(nodes),((nodes[0][0],nodes[2][0],"DERIVED_FROM"),(nodes[2][0],nodes[0][0],"DERIVED_FROM")));assert not isinstance(projection,tuple)
    result=planning.compute_scope_revision_impact(history,successor,tuple(records),projection,registry)
    assert isinstance(result,tuple) and result


def test_revision_impact_rejects_intrinsic_predecessor_with_forged_plan_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    args,_,_=_impact_fixture(monkeypatch);history,successor,records,projection,registry=args;parts=planning._declaration_parts(history[0]);assert parts is not None;raws,sources,assets=parts;snapshot_raw,plan_raw,discovery_raw,decision_raw,scope_raw,bundle_raw=raws;scope=json.loads(scope_raw);scope["payload"]["plan_ref"]={**scope["payload"]["plan_ref"],"content_hash":"sha256:"+"0"*64};scope_raw,_=_record(scope["envelope"],scope["payload"]);forged=planning.build_planning_scope_chain_declaration(snapshot_raw,dict(sources),plan_raw,discovery_raw,decision_raw,scope_raw,assets,bundle_raw);assert not isinstance(forged,tuple)
    assert isinstance(planning.compute_scope_revision_impact((forged,),successor,records,projection,registry),tuple)


def _terminal_fixture(monkeypatch: pytest.MonkeyPatch):
    chain_args=_full_chain_fixture("BLOCK");snapshot_raw,sources,plan_raw,discovery_raw,decision_raw,terminals,_,_,assets,registry,bundle_raw=chain_args;terminal_raw=terminals[0]
    parsed=planning.parse_canonical_json(terminal_raw);parsed_plan=planning.parse_canonical_json(plan_raw);assert type(parsed) is ParsedCanonicalValue and type(parsed_plan) is ParsedCanonicalValue
    constraints=planning._planning_constraints(assets,registry,parsed_plan.to_python()["payload"]);assert type(constraints) is tuple and len(constraints)==2 and type(constraints[0]) is CatalogProfileConstraints
    return parsed,terminal_raw,parsed.to_python(),assets,registry,bundle_raw,constraints[0],constraints[1],plan_raw,discovery_raw,decision_raw,chain_args


def test_terminal_composition_calls_c_once_and_freezes_complete_e_vector(monkeypatch: pytest.MonkeyPatch) -> None:
    parsed,_,_,assets,registry,bundle_raw,c_constraints,e_constraints,plan_raw,discovery_raw,decision_raw,_=_terminal_fixture(monkeypatch)
    original_c=planning.validate_typed_terminal_result_catalog_constraints;original_e=planning.validate_planning_terminal_registration_v1_1;c_calls=[];e_calls=[]
    def counted_c(*args):c_calls.append(1);return original_c(*args)
    def counted_e(*args):e_calls.append(1);return original_e(*args)
    monkeypatch.setattr(planning,"validate_typed_terminal_result_catalog_constraints",counted_c);monkeypatch.setattr(planning,"validate_planning_terminal_registration_v1_1",counted_e)
    assert planning.validate_planning_terminal_constraints(parsed,registry,c_constraints,e_constraints,plan_raw,discovery_raw,decision_raw,assets,bundle_raw)==()
    assert c_calls==[1] and e_calls==[1]


def test_terminal_rejects_forged_constraints_and_corrupt_bundle_policy_before_c(monkeypatch: pytest.MonkeyPatch) -> None:
    parsed,_,_,assets,registry,bundle_raw,c_constraints,e_constraints,plan_raw,discovery_raw,decision_raw,_=_terminal_fixture(monkeypatch);calls=[]
    original=planning.validate_typed_terminal_result_catalog_constraints
    def counted(*args):calls.append(1);return original(*args)
    monkeypatch.setattr(planning,"validate_typed_terminal_result_catalog_constraints",counted);object.__setattr__(e_constraints,"_KernelValidationPolicyV11Constraints__registrations",(b"{}",))
    assert planning.validate_planning_terminal_constraints(parsed,registry,c_constraints,e_constraints,plan_raw,discovery_raw,decision_raw,assets,bundle_raw) and calls==[]
    fresh=_terminal_fixture(monkeypatch);parsed,_,_,assets,registry,bundle_raw,c_constraints,e_constraints,plan_raw,discovery_raw,decision_raw,_=fresh;changed=list(assets);index=next(i for i,asset in enumerate(changed) if asset.asset_id=="validation-policy:checkpoint-e-kernel-candidate/1.1.0");asset=changed[index];changed[index]=SuppliedAsset(asset.asset_id,asset.media_type,asset.raw_bytes+b" ")
    assert planning.validate_planning_terminal_constraints(parsed,registry,c_constraints,e_constraints,plan_raw,discovery_raw,decision_raw,tuple(changed),bundle_raw)


@pytest.mark.parametrize("mutation",["basis","evidence-order","resource","attempt","action"])
def test_terminal_composition_rejects_each_frozen_binding_dimension(monkeypatch: pytest.MonkeyPatch,mutation: str) -> None:
    _,_,document,assets,registry,bundle_raw,c_constraints,e_constraints,plan_raw,discovery_raw,decision_raw,_=_terminal_fixture(monkeypatch);payload=document["payload"]
    if mutation=="basis":payload["target_obligation"]["basis"]["component_ref"]["record_id"]="plan:stale"
    elif mutation=="evidence-order":payload["evidence"].reverse()
    elif mutation=="resource":payload["resources"]["limit"]["max_network_requests"]=1
    elif mutation=="attempt":payload["attempt_id"]="attempt:stale"
    else:payload["next_action"]["responsible_role"]="DISCOVERY_PRODUCER"
    raw,_=_record(document["envelope"],payload);parsed=planning.parse_canonical_json(raw);assert type(parsed) is ParsedCanonicalValue
    assert planning.validate_planning_terminal_constraints(parsed,registry,c_constraints,e_constraints,plan_raw,discovery_raw,decision_raw,assets,bundle_raw)


def test_aggregate_block_invokes_terminal_composition_and_rejects_canonical_garbage(monkeypatch: pytest.MonkeyPatch) -> None:
    args=_full_chain_fixture("BLOCK")
    assert not isinstance(planning.validate_planning_scope_chain(*args),tuple)
    garbage_args=(*args[:5],(b"{}",),*args[6:])
    assert isinstance(planning.validate_planning_scope_chain(*garbage_args),tuple)
