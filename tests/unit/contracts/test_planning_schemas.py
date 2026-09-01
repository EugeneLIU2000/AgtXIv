from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from agtxiv_v2.contracts import Diagnostic, ParsedCanonicalValue, SchemaAssetBinding, SuppliedAsset, build_canonical_value, build_schema_registry, raw_asset_sha256  # noqa: E402

PATHS = (
    "schemas/v2/contract-kernel/contract/contract-bundle-release/1.0.0.schema.json",
    "schemas/v2/contract-kernel/contract/stable-code-catalog/1.1.0.schema.json",
    "schemas/v2/contract-kernel/contract/kernel-validation-policy/1.1.0.schema.json",
    "schemas/v2/contract-kernel/contract/discovery-obligation-policy/1.0.0.schema.json",
    "schemas/v2/contract-kernel/source/paper-source-snapshot/1.0.0.schema.json",
    "schemas/v2/contract-kernel/planning/agentization-plan/1.0.0.schema.json",
    "schemas/v2/contract-kernel/inventory/inventory-discovery-result/1.0.0.schema.json",
    "schemas/v2/contract-kernel/review/scope-freeze-decision/1.0.0.schema.json",
    "schemas/v2/contract-kernel/inventory/frozen-inventory-scope/1.0.0.schema.json",
    "fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/entry-output/1.0.0.schema.json",
    "fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/whole-scope-output/1.0.0.schema.json",
    "fixtures/v2-contract-kernel/planning-scope/1.0.0/downstream-schemas/derived-output/1.0.0.schema.json",
)


def _binding(path: Path) -> SchemaAssetBinding:
    raw = path.read_bytes(); document = json.loads(raw); schema_id = document["$id"]
    name = schema_id.removeprefix("https://agtxiv.org/schema/v2/").replace("/", ":")
    asset = SuppliedAsset(f"schema:{name}", "application/schema+json", raw, schema_id)
    ref = build_canonical_value({"asset_id":asset.asset_id,"media_type":asset.media_type,"byte_size":len(raw),"sha256":raw_asset_sha256(raw),"schema_uri":schema_id})
    assert type(ref) is ParsedCanonicalValue
    return SchemaAssetBinding(ref, asset)


@pytest.mark.parametrize("relative", PATHS)
def test_checkpoint_e_schema_is_closed_and_meta_valid(relative: str) -> None:
    schema = json.loads((ROOT / relative).read_bytes())
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].startswith("https://agtxiv.org/schema/v2/")
    if "$defs" in schema and "payload" in schema["$defs"]:
        assert schema["$defs"]["payload"]["additionalProperties"] is False


def test_all_checkpoint_e_schemas_resolve_offline_with_common_registry() -> None:
    paths = [ROOT / item for item in PATHS]
    paths.extend(sorted((ROOT / "schemas/v2/contract-kernel/common").glob("*/*.schema.json")))
    registry = build_schema_registry(tuple(_binding(path) for path in paths))
    assert not isinstance(registry, tuple), registry


def test_legacy_flat_inventory_scope_is_not_an_e_schema() -> None:
    text = "\n".join((ROOT / item).read_text() for item in PATHS)
    assert "agtxiv.inventory-scope/2.0.0" not in text
    assert "https://agtxiv.org/schema/v2/inventory-scope/2.0.0" not in text


@pytest.mark.parametrize("relative,role",[
    (PATHS[4],"SOURCE_SNAPSHOT_BUILDER"),(PATHS[5],"PLANNING_PRODUCER"),(PATHS[6],"DISCOVERY_PRODUCER"),(PATHS[7],"SCOPE_FREEZE_REVIEWER"),(PATHS[8],"SCOPE_FREEZE_ISSUER")])
def test_post_bootstrap_family_schema_requires_exact_producer_role(relative: str,role: str) -> None:
    schema=json.loads((ROOT/relative).read_bytes())
    overlay=schema["$defs"]["record"]["properties"]["envelope"]["allOf"][1]
    assert "producer_context" in overlay["required"]
    assert overlay["properties"]["producer_context"]["allOf"][1]["properties"]["role"]=={"const":role}


def test_bundle_schema_uses_base_envelope_and_planning_families_use_contract_bound() -> None:
    bundle=json.loads((ROOT/PATHS[0]).read_bytes())
    assert bundle["$defs"]["record"]["properties"]["envelope"]["allOf"][0]["$ref"].endswith("#/$defs/baseEnvelope")
    for relative in PATHS[4:9]:
        schema=json.loads((ROOT/relative).read_bytes())
        assert schema["$defs"]["record"]["properties"]["envelope"]["allOf"][0]["$ref"].endswith("#/$defs/contractBoundEnvelope")


def test_schema_maxima_freeze_checkpoint_e_admission_limits() -> None:
    snapshot = json.loads((ROOT / PATHS[4]).read_bytes())["$defs"]["payload"]
    discovery = json.loads((ROOT / PATHS[6]).read_bytes())["$defs"]["payload"]
    scope = json.loads((ROOT / PATHS[8]).read_bytes())["$defs"]["payload"]
    assert snapshot["properties"]["source_files"]["maxItems"] == 4096
    assert discovery["properties"]["classified_components"]["maxItems"] == 8192
    assert discovery["properties"]["obligation_dispositions"]["maxItems"] == 256
    assert scope["properties"]["scope_entries"]["maxItems"] == 16384
    for partition in ("classified_components","ambiguous_components","unclassified_components"):
        assert discovery["properties"][partition]["items"]["properties"]["normalized_path"]["maxLength"] == 1024
    assert scope["properties"]["scope_entries"]["items"]["properties"]["normalized_path"]["maxLength"] == 1024


def test_bundle_role_counts_and_successor_gate_prefix_are_exact() -> None:
    bundle=json.loads((ROOT/PATHS[0]).read_bytes())["$defs"]["payload"]["properties"]
    assert [(bundle[name]["minItems"],bundle[name]["maxItems"]) for name in ("schema_assets","contract_assets","validator_assets","specification_assets")]==[(27,27),(15,15),(11,11),(3,3)]
    policy=json.loads((ROOT/PATHS[2]).read_bytes())["properties"]["gate_order"]["const"]
    assert policy[-3:]==["TERMINAL_C_PUBLIC_INCLUDING_B_INTRINSIC_ONCE","TERMINAL_E_1_1_REASON_POLICY","TERMINAL_E_EXACT_PLANNING_BINDINGS"]
    assert len(policy)==9
