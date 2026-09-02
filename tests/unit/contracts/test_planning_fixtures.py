from __future__ import annotations

import builtins
import hashlib
import importlib.util
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

from agtxiv_v2.contracts import (  # noqa: E402
    Diagnostic,
    ParsedCanonicalValue,
    SchemaAssetBinding,
    build_canonical_value,
    build_schema_registry,
    canonical_bytes,
    record_content_hash,
    validate_immutable_record_payload,
)
import agtxiv_v2.contracts.planning_validation as planning  # noqa: E402

BASE = ROOT / "fixtures/v2-contract-kernel/planning-scope/1.0.0"
BUNDLE_PATH = ROOT / "contracts/v2/contract-kernel/bundles/checkpoint-e/1.0.0-candidate.1.json"
REAL_PREFIX = "Reference/The Resource Theory of Stabilizer Computation/"
REAL_PATHS = (
    "source.tar", "stab_resource_theory_021.tex", "stab_resource_theory_021.bbl",
    "Figures/4_1_2_total_mana_in_vs_expected_mana_out_standardized.png",
    "Figures/5_1_3_total_mana_in_vs_expected_mana_out_standardized.png",
    "Figures/8_1_3_total_mana_in_vs_expected_mana_out_standardized.png",
    "Figures/norrell_state_labels_no_heatmap.png",
    "Figures/slice_mana_heat_map_revised_color.png",
    "Figures/strange_state_labels_no_heatmap.png",
)
SYNTHETIC_SOURCE = {
    "main.tex": b"\\documentclass{article}\n\\begin{document}\nCheckpoint E synthetic main.\n\\end{document}\n",
    "appendix.tex": b"\\section{Appendix}\nSynthetic appendix evidence.\n",
    "binary.bin": bytes((0, 1, 2, 255, 65, 71, 84, 88, 73, 86, 0, 127)),
}
SYNTHETIC_MEDIA = {
    "main.tex": ("text/x-tex", "TEXT"), "appendix.tex": ("text/x-tex", "TEXT"),
    "binary.bin": ("application/octet-stream", "BINARY"),
}


def _canonical(value: object) -> bytes:
    parsed = build_canonical_value(value)
    assert type(parsed) is ParsedCanonicalValue
    return canonical_bytes(parsed)


def _upstream_helpers():
    spec = importlib.util.spec_from_file_location("planning_test_helpers", ROOT / "tests/unit/contracts/test_planning_validation.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _context(index, bundle, role: str, actor: str, attempt: str) -> dict[str, object]:
    return {"producer": {"actor_kind": "HUMAN" if role == "SCOPE_FREEZE_REVIEWER" else "MECHANICAL_SERVICE", "actor_id": actor}, "role": role, "attempt_id": attempt, "implementation_ref": planning._asset_ref(index["validator:checkpoint-e-planning-scope:1.0.0"]), "environment_ref": planning._asset_ref(index["canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/provenance"])}


def _record(index, bundle, rtype: str, schema_id: str, rid: str, revision: int, payload: dict[str, object], context: dict[str, object], predecessor=None):
    envelope = {"record_type": rtype, "schema_ref": planning._asset_ref(index[schema_id]), "record_id": rid, "record_revision": revision, "contract_bundle_ref": planning._record_ref(bundle), "created_at": "2026-09-01T00:00:00Z", "producer_context": context}
    if predecessor is not None:
        envelope["supersedes_ref"] = planning._record_ref(predecessor)
    document = {"envelope": envelope, "payload": payload, "content_hash": "sha256:" + "0" * 64}
    parsed = build_canonical_value(document); assert type(parsed) is ParsedCanonicalValue
    document["content_hash"] = record_content_hash(parsed)
    return _canonical(document), document


def _row(path: str, raw: bytes, media: tuple[str, str]) -> dict[str, object]:
    digest = hashlib.sha256(raw).hexdigest(); unit = "source-unit:sha256:" + digest
    return {"normalized_path": path, "source_row_id": planning._source_row_id(path, unit), "source_unit_id": unit, "sha256": "sha256:" + digest, "byte_size": len(raw), "media_type": media[0], "content_kind": media[1]}


def _build_chain(index, bundle, tag, label, sources, media, specs, branch="ACCEPT", old_scope=None, blocked=(), ancestor_tag=None):
    rows = sorted((_row(path, raw, media[path]) for path, raw in sources.items()), key=lambda row: row["normalized_path"].encode())
    root_tag = tag if ancestor_tag is None else ancestor_tag
    sp = {"snapshot_id": f"snapshot:checkpoint-e/{root_tag}", "snapshot_version": 1, "source_origin_kind": "CALLER_SUPPLIED_LOCAL_FIXTURE", "source_label": label, "source_tree_algorithm": "AGTXIV_SOURCE_TREE_V1", "source_tree_root": planning._source_root(rows, sources), "source_file_count": len(rows), "source_total_bytes": sum(map(len, sources.values())), "source_files": rows}
    sr, snapshot = _record(index, bundle, "agtxiv.paper-source-snapshot/1.0.0", "schema:paper-source-snapshot:1.0.0", sp["snapshot_id"], 1, sp, _context(index, bundle, "SOURCE_SNAPSHOT_BUILDER", f"actor:checkpoint-e/source-builder/{root_tag}", f"attempt:checkpoint-e/snapshot/{root_tag}"))
    policy = json.loads(index["discovery-policy:checkpoint-e/1.0.0-candidate.1"].raw_bytes)
    pp = {"plan_id": f"plan:checkpoint-e/{root_tag}", "plan_revision": 1, "source_snapshot_ref": planning._record_ref(snapshot), "source_tree_root": sp["source_tree_root"], "contract_bundle_ref": planning._record_ref(bundle), "artifact_family_catalog_ref": planning._asset_ref(index["catalog:checkpoint-e-planning-families/1.0.0-candidate.1"]), "agentization_profile_ref": planning._asset_ref(index["profile:checkpoint-e-planning-families/1.0.0-candidate.1"]), "stable_code_catalog_ref": planning._asset_ref(index["code-catalog:agtxiv-contract-kernel/1.1.0"]), "kernel_validation_policy_ref": planning._asset_ref(index["validation-policy:checkpoint-e-kernel-candidate/1.1.0"]), "discovery_policy_ref": planning._asset_ref(index["discovery-policy:checkpoint-e/1.0.0-candidate.1"]), "resource_policy_ref": planning._asset_ref(index["validation-policy:checkpoint-e-kernel-candidate/1.1.0"]), "expected_source_units": rows, "profile_obligations": planning._project_obligations(policy, rows), "planning_context": "QUERY_INDEPENDENT"}
    pr, plan = _record(index, bundle, "agtxiv.agentization-plan/1.0.0", "schema:agentization-plan:1.0.0", pp["plan_id"], 1, pp, _context(index, bundle, "PLANNING_PRODUCER", f"actor:checkpoint-e/planner/{root_tag}", f"attempt:checkpoint-e/plan/{root_tag}"))
    evidence = planning._asset_ref(index["canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/provenance"]); by_path = {row["normalized_path"]: row for row in rows}; components = []
    for path, kind, state, code in specs:
        row = by_path[path]; component = {"component_id": "pending", "source_row_id": row["source_row_id"], "source_unit_id": row["source_unit_id"], "normalized_path": path, "byte_start": 0, "byte_end": len(sources[path]), "component_kind": kind, "source_anchor_hash": "pending", "classification_state": state, "classification_or_issue_code": code, "evidence_refs": [evidence] if state != "CLASSIFIED" else []}
        component["component_id"], component["source_anchor_hash"] = planning._component_identity(component, row, sources[path]); components.append(component)
    key = lambda component: (component["normalized_path"].encode(), component["byte_start"], component["byte_end"], component["component_id"].encode())
    coverage = []
    for row in rows:
        selected = sorted((c for c in components if c["source_row_id"] == row["source_row_id"]), key=key); item = {k: row[k] for k in ("source_row_id", "normalized_path", "source_unit_id", "sha256", "byte_size", "media_type", "content_kind")}; item.update(component_ids=[c["component_id"] for c in selected], coverage_status="BLOCKED_WITH_EVIDENCE" if row["normalized_path"] in blocked else "COMPONENTS_RECORDED"); coverage.append(item)
    errors = [{"error_id": "error:checkpoint-e/blocked-appendix", "error_code": "AGTXIV.DISCOVERY.APPENDIX_BLOCKED", "summary": "Appendix discovery was blocked; the source region remains explicitly unresolved.", "evidence_refs": [evidence]}] if blocked else []
    row_by_id = {row["source_row_id"]: row for row in rows}; dispositions = []
    for obligation in pp["profile_obligations"]:
        relevant = sorted((c for c in components if planning._component_matches_obligation(c, obligation, row_by_id)), key=key); classified = [c for c in relevant if c["classification_state"] == "CLASSIFIED"]
        satisfied = all(sum(c["source_row_id"] == row_id for c in classified) >= obligation["minimum_cardinality"] for row_id in obligation["matched_source_row_ids"]) if obligation["region_selector"] == "EVERY_SOURCE_ROW" else len(classified) >= obligation["minimum_cardinality"]
        is_blocked = not satisfied and any(c["component_kind"] == "UNRESOLVED_SOURCE_REGION" and c["normalized_path"] in blocked for c in relevant)
        status = "BLOCKED" if is_blocked else "SATISFIED" if satisfied else "AMBIGUOUS" if any(c["classification_state"] == "AMBIGUOUS" for c in relevant) else "UNCLASSIFIED"
        dispositions.append({"obligation_id": obligation["obligation_id"], "status": status, "component_ids": [c["component_id"] for c in relevant], "finding_or_error_refs": [errors[0]["error_id"]] if is_blocked else []})
    dc = _context(index, bundle, "DISCOVERY_PRODUCER", f"actor:checkpoint-e/discoverer/{tag}", f"attempt:checkpoint-e/discovery/{tag}")
    dp = {"discovery_id": f"discovery:checkpoint-e/{tag}", "discovery_revision": 1, "plan_ref": planning._record_ref(plan), "source_snapshot_ref": planning._record_ref(snapshot), "source_tree_root": sp["source_tree_root"], "producer_context": dc, "observed_resource_limits": {"maximum_discovery_components": 8192, "maximum_discovery_obligations": 256}, "source_unit_coverage": coverage, "classified_components": sorted((c for c in components if c["classification_state"] == "CLASSIFIED"), key=key), "ambiguous_components": sorted((c for c in components if c["classification_state"] == "AMBIGUOUS"), key=key), "unclassified_components": sorted((c for c in components if c["classification_state"] == "UNCLASSIFIED"), key=key), "obligation_dispositions": dispositions, "discovery_errors": errors, "completeness_claim": "TOTAL_ACCOUNTED_PROFILE_RELATIVE"}
    dr, discovery = _record(index, bundle, "agtxiv.inventory-discovery-result/1.0.0", "schema:inventory-discovery-result:1.0.0", dp["discovery_id"], 1, dp, dc)
    reviewer = {"actor_kind": "HUMAN", "actor_id": f"actor:checkpoint-e/reviewer/{tag}"}; declarations = [{"producer_actor_id": dc["producer"]["actor_id"], "reviewer_actor_id": reviewer["actor_id"], "category": category, "disposition": "NO_CONFLICT_DECLARED"} for category in ("IDENTITY", "ORGANIZATIONAL_CONTROL", "BENEFICIAL_OWNERSHIP", "OTHER")]
    dep = {"decision_id": f"decision:checkpoint-e/{tag}", "decision_revision": 1, "plan_ref": planning._record_ref(plan), "discovery_ref": planning._record_ref(discovery), "source_snapshot_ref": planning._record_ref(snapshot), "source_tree_root": sp["source_tree_root"], "reviewer": reviewer, "reviewer_role": "SCOPE_FREEZE_REVIEWER", "producer_actor_ref": dc["producer"], "independence_declaration": "STRUCTURALLY_DISTINCT_ACTOR_IDS_DECLARED", "conflict_declarations": declarations, "review_policy_ref": pp["kernel_validation_policy_ref"], "findings": [] if branch == "ACCEPT" else [{"finding_id": "finding:checkpoint-e/blocked-appendix", "severity": "BLOCKING", "subject_kind": "DISCOVERY", "subject_id": dp["discovery_id"], "finding_code": "AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED", "summary": "The blocked appendix prevents acceptance of this exact discovery."}], "decision": branch}
    if branch == "BLOCK": dep["terminal_requirement"] = {"obligation_key": "obligation:checkpoint-e/frozen-inventory-scope", "reason_code": "AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED", "family_id": "FROZEN_INVENTORY_SCOPE", "stage_id": "SCOPE_FREEZE", "outcome": "BLOCKED", "context_mode": "PLAN_BOUND"}
    der, decision = _record(index, bundle, "agtxiv.scope-freeze-decision/1.0.0", "schema:scope-freeze-decision:1.0.0", dep["decision_id"], 1, dep, _context(index, bundle, "SCOPE_FREEZE_REVIEWER", reviewer["actor_id"], f"attempt:checkpoint-e/review/{tag}"))
    if branch == "BLOCK": return (sr, snapshot, pr, plan, dr, discovery, der, decision, None, None)
    if old_scope is None:
        seed = planning._framed(pp["plan_id"].encode()) + planning._framed(sp["snapshot_id"].encode()); scope_id = "inventory-scope:sha256:" + planning._hash(b"AGTXIV_SCOPE_ID_V1\0", seed); revision = 1; delta = {"kind": "GENESIS", "added_entry_ids": [], "removed_entry_ids": [], "classification_changed_entry_ids": [], "source_binding_changed_entry_ids": []}
    else:
        scope_id = old_scope["payload"]["scope_id"]; revision = old_scope["payload"]["scope_revision"] + 1
    entries = [planning._scope_entry(scope_id, component) for component in sorted(components, key=key)]
    if old_scope is not None: delta = {"kind": "SUCCESSOR", **planning._scope_delta(old_scope["payload"]["scope_entries"], entries)}
    scp = {"scope_id": scope_id, "scope_revision": revision, "plan_ref": planning._record_ref(plan), "discovery_ref": planning._record_ref(discovery), "accept_decision_ref": planning._record_ref(decision), "source_snapshot_ref": planning._record_ref(snapshot), "source_tree_root": sp["source_tree_root"], "revision_delta": delta, "scope_entries": entries}
    if old_scope is not None: scp["predecessor_scope_ref"] = planning._record_ref(old_scope)
    rid = f"inventory-scope-record:sha256:{scope_id.rsplit(':', 1)[-1]}/revision/{revision}"; scr, scope = _record(index, bundle, "agtxiv.frozen-inventory-scope/1.0.0", "schema:frozen-inventory-scope:1.0.0", rid, revision, scp, _context(index, bundle, "SCOPE_FREEZE_ISSUER", f"actor:checkpoint-e/issuer/{tag}", f"attempt:checkpoint-e/scope/{tag}"), old_scope)
    return sr, snapshot, pr, plan, dr, discovery, der, decision, scr, scope


def _terminal(index, bundle, plan, discovery, decision):
    plan_ref = planning._record_ref(plan); ix = next(i for i, row in enumerate(plan["payload"]["profile_obligations"]) if row["obligation_id"] == "obligation:checkpoint-e/frozen-inventory-scope"); fallback = discovery["payload"]["unclassified_components"][0]; attempt = "attempt:checkpoint-e/scope-freeze-issuer/blocked-appendix/1"
    payload = {"terminal_for_attempt": True, "terminal_scope": "ATTEMPT_ONLY", "successful_artifact_produced": False, "satisfaction_claim": "NONE", "attempt_id": attempt, "binding_context": {"context_mode": "PLAN_BOUND", "profile_ref": plan["payload"]["agentization_profile_ref"], "catalog_ref": plan["payload"]["artifact_family_catalog_ref"], "plan_ref": plan_ref}, "target_obligation": {"obligation_key": "obligation:checkpoint-e/frozen-inventory-scope", "stage_id": "SCOPE_FREEZE", "family_id": "FROZEN_INVENTORY_SCOPE", "basis": {"basis_kind": "COMPONENT", "component_ref": {**plan_ref, "component_id": "obligation:checkpoint-e/frozen-inventory-scope", "json_pointer": f"/payload/profile_obligations/{ix}"}}}, "outcome": "BLOCKED", "declared_reason": {"declared_reason_code": "AGTXIV.SCOPE.FREEZE_NOT_ACCEPTED", "summary": "Scope freeze was not accepted for the exact plan-bound discovery; no FrozenInventoryScope was issued."}, "evidence": [{"evidence_id": "evidence:scope-freeze/block-decision", "evidence_role": "POLICY_OBSERVATION", "evidence_kind": "RECORD", "record_ref": planning._record_ref(decision)}, {"evidence_id": "evidence:scope-freeze/blocked-component", "evidence_role": "TOOL_DIAGNOSTIC", "evidence_kind": "COMPONENT", "component_ref": {**planning._record_ref(discovery), "component_id": fallback["component_id"], "json_pointer": "/payload/unclassified_components/0"}}, {"evidence_id": "evidence:scope-freeze/discovery", "evidence_role": "INPUT_STATE", "evidence_kind": "RECORD", "record_ref": planning._record_ref(discovery)}], "retry": {"retry_disposition": "NO_RETRY_IN_CURRENT_CONTEXT", "context_change_required": "A new independently reviewed scope-freeze attempt is required before scope issuance."}, "next_action": {"action_code": "ESCALATE", "description": "Escalate the blocked scope-freeze decision for an independently authorized new attempt.", "responsible_actor": decision["payload"]["reviewer"], "responsible_role": "SCOPE_FREEZE_REVIEWER", "deadline": {"deadline_kind": "NO_DEADLINE", "no_deadline_reason": "No production review schedule is authorized by Checkpoint E."}}, "resources": {"limit": {"max_wall_time_ms": 60000, "max_cpu_time_ms": 60000, "max_peak_memory_bytes": 134217728, "max_input_bytes": 134217728, "max_output_bytes": 41943040, "max_network_requests": 0}, "observed": {"network_requests": 0}, "unobserved_metrics": ["wall_time_ms", "cpu_time_ms", "peak_memory_bytes", "input_bytes", "output_bytes"], "relation": "INDETERMINATE"}}
    return _record(index, bundle, "agtxiv.typed-terminal-result/1.0.0", "schema:typed-terminal-result:1.0.0", "terminal:checkpoint-e/scope-freeze-blocked-appendix/1", 1, payload, _context(index, bundle, "SCOPE_FREEZE_ISSUER", "actor:checkpoint-e/scope-freeze-issuer", attempt))


def _real_sources():
    return {path: subprocess.check_output(("git", "show", "HEAD:" + REAL_PREFIX + path), cwd=ROOT) for path in REAL_PATHS}


def _build_all():
    helpers = _upstream_helpers(); assets = helpers._exact_bundle_assets(); index = {asset.asset_id: asset for asset in assets}; bundle = json.loads(BUNDLE_PATH.read_bytes()); output = {"source/" + path: raw for path, raw in SYNTHETIC_SOURCE.items()}
    specs = [("appendix.tex", "DOCUMENT_TEXT", "CLASSIFIED", "AGTXIV.DISCOVERY.CLASSIFIED"), ("appendix.tex", "APPENDIX_TEXT", "CLASSIFIED", "AGTXIV.DISCOVERY.CLASSIFIED"), ("binary.bin", "FIGURE_BINARY", "CLASSIFIED", "AGTXIV.DISCOVERY.CLASSIFIED"), ("binary.bin", "UNRESOLVED_SOURCE_REGION", "AMBIGUOUS", "AGTXIV.DISCOVERY.AMBIGUOUS"), ("main.tex", "DOCUMENT_TEXT", "CLASSIFIED", "AGTXIV.DISCOVERY.CLASSIFIED"), ("main.tex", "UNRESOLVED_SOURCE_REGION", "UNCLASSIFIED", "AGTXIV.DISCOVERY.UNCLASSIFIED")]
    v1 = _build_chain(index, bundle, "synthetic-v1", "checkpoint-e-synthetic", SYNTHETIC_SOURCE, SYNTHETIC_MEDIA, specs); names = ("snapshot-v1.json", "plan-v1.json", "discovery-v1.json", "decision-accept-v1.json", "scope-v1.json")
    for name, raw in zip(names, v1[::2]): output["synthetic/" + name] = raw
    blocked_specs = [row for row in specs if row[0] != "appendix.tex" and row[2] == "CLASSIFIED"] + [("appendix.tex", "UNRESOLVED_SOURCE_REGION", "UNCLASSIFIED", "AGTXIV.DISCOVERY.APPENDIX_BLOCKED")]; block = _build_chain(index, bundle, "synthetic-blocked-appendix", "checkpoint-e-synthetic", SYNTHETIC_SOURCE, SYNTHETIC_MEDIA, blocked_specs, "BLOCK", blocked=("appendix.tex",), ancestor_tag="synthetic-v1"); terminal_raw, _ = _terminal(index, bundle, block[3], block[5], block[7])
    output.update({"synthetic/discovery-blocked-appendix.json": block[4], "synthetic/decision-block-appendix.json": block[6], "synthetic/terminal-block-appendix.json": terminal_raw})
    sources2 = {**SYNTHETIC_SOURCE, "notes.txt": b"Unrelated revision-two source row.\n"}; media2 = {**SYNTHETIC_MEDIA, "notes.txt": ("text/plain", "TEXT")}; specs2 = [(path, kind, "AMBIGUOUS" if path == "main.tex" and kind == "UNRESOLVED_SOURCE_REGION" else state, "AGTXIV.DISCOVERY.RECLASSIFIED" if path == "main.tex" and kind == "UNRESOLVED_SOURCE_REGION" else code) for path, kind, state, code in specs if not (path == "binary.bin" and kind == "UNRESOLVED_SOURCE_REGION")] + [("notes.txt", "DOCUMENT_TEXT", "CLASSIFIED", "AGTXIV.DISCOVERY.CLASSIFIED")]
    v2 = _build_chain(index, bundle, "synthetic-v2", "checkpoint-e-synthetic", sources2, media2, specs2, old_scope=v1[9])
    for name, raw in zip(("snapshot-v2.json", "plan-v2.json", "discovery-v2.json", "decision-accept-v2.json", "scope-v2.json"), v2[::2]): output["synthetic/" + name] = raw
    removed = next(row for row in v1[9]["payload"]["scope_entries"] if row["normalized_path"] == "binary.bin" and row["component_kind"] == "UNRESOLVED_SOURCE_REGION"); unchanged = next(row for row in v1[9]["payload"]["scope_entries"] if row["normalized_path"] == "appendix.tex" and row["component_kind"] == "APPENDIX_TEXT")
    downstream = []
    rows = (("entry", "agtxiv.checkpoint-e-entry-output/1.0.0", "schema:fixture:checkpoint-e-entry-output:1.0.0", "ENTRY_SET", [removed["scope_entry_id"]], [removed["scope_entry_id"]]), ("whole-scope", "agtxiv.checkpoint-e-whole-scope-output/1.0.0", "schema:fixture:checkpoint-e-whole-scope-output:1.0.0", "WHOLE_SCOPE", [], [unchanged["scope_entry_id"]]), ("derived", "agtxiv.checkpoint-e-derived-output/1.0.0", "schema:fixture:checkpoint-e-derived-output:1.0.0", "ENTRY_SET", [unchanged["scope_entry_id"]], []))
    for name, rtype, schema, mode, inputs, outputs in rows:
        payload = {"scope_ref": planning._record_ref(v1[9]), "coverage_mode": mode, "input_entry_ids": inputs, "output_entry_ids": outputs}; raw, doc = _record(index, bundle, rtype, schema, f"downstream:checkpoint-e/{name}-output", 1, payload, _context(index, bundle, "SCOPE_FREEZE_ISSUER", "actor:checkpoint-e/downstream-fixture", f"attempt:checkpoint-e/downstream/{name}")); output[f"synthetic/downstream-{name}-output.json"] = raw; downstream.append(doc)
    lineage = {"nodes": [{"record_id": doc["envelope"]["record_id"], "record_type": doc["envelope"]["record_type"], "scope_ref": doc["payload"]["scope_ref"], "coverage_mode": doc["payload"]["coverage_mode"], "exact_input_entry_ids": doc["payload"]["input_entry_ids"], "exact_output_entry_ids": doc["payload"]["output_entry_ids"]} for doc in downstream], "edges": [{"producer_record_id": "downstream:checkpoint-e/entry-output", "consumer_record_id": "downstream:checkpoint-e/derived-output", "relation": "DERIVED_FROM"}, {"producer_record_id": "downstream:checkpoint-e/whole-scope-output", "consumer_record_id": "downstream:checkpoint-e/derived-output", "relation": "DERIVED_FROM"}]}; output["synthetic/revision-lineage.json"] = _canonical(lineage)
    registry = _registry(assets); predecessor = planning.build_planning_scope_chain_declaration(v1[0], SYNTHETIC_SOURCE, v1[2], v1[4], v1[6], v1[8], assets, BUNDLE_PATH.read_bytes()); successor = planning.build_planning_scope_chain_declaration(v2[0], sources2, v2[2], v2[4], v2[6], v2[8], assets, BUNDLE_PATH.read_bytes()); projection = _projection(lineage); impact = planning.compute_scope_revision_impact((predecessor,), successor, tuple(output[f"synthetic/downstream-{name}-output.json"] for name in ("entry", "whole-scope", "derived")), projection, registry); assert not isinstance(impact, tuple), impact; output["synthetic/revision-impact.expected.json"] = _canonical(impact.to_python())
    real = _real_sources(); real_media = {path: ("text/x-tex", "TEXT") if path.endswith(".tex") else ("text/plain", "TEXT") if path.endswith(".bbl") else ("application/x-tar", "BINARY") if path.endswith(".tar") else ("image/png", "BINARY") for path in REAL_PATHS}; real_specs = [(path, "DOCUMENT_TEXT" if path.endswith(".tex") else "BIBLIOGRAPHY_TEXT" if path.endswith(".bbl") else "ARCHIVE_BINARY" if path.endswith(".tar") else "FIGURE_BINARY", "CLASSIFIED", "AGTXIV.DISCOVERY.CLASSIFIED") for path in REAL_PATHS]; chain = _build_chain(index, bundle, "real-paper", "tracked-resource-theory-stabilizer-computation", real, real_media, real_specs)
    for name, raw in zip(("snapshot.json", "plan.json", "discovery.json", "decision-accept.json", "scope.json"), chain[::2]): output["real-paper/" + name] = raw
    return output


def _assets(): return _upstream_helpers()._exact_bundle_assets()
def _registry(assets):
    bindings = [SchemaAssetBinding(build_canonical_value(planning._asset_ref(asset)), asset) for asset in assets if asset.schema_uri is not None]; result = build_schema_registry(tuple(bindings)); assert not isinstance(result, tuple); return result

def _projection(lineage):
    nodes = tuple((row["record_id"], row["record_type"], _canonical(row["scope_ref"]), row["coverage_mode"], tuple(row["exact_input_entry_ids"]), tuple(row["exact_output_entry_ids"])) for row in lineage["nodes"]); edges = tuple((row["producer_record_id"], row["consumer_record_id"], row["relation"]) for row in lineage["edges"]); result = planning.ScopeRevisionLineageProjection.build(nodes, edges); assert not isinstance(result, tuple); return result

def _raw(group, name): return (BASE / group / name).read_bytes()
def _json(group, name): return json.loads(_raw(group, name))
def _mutation(raw, mutate):
    document = json.loads(raw); mutate(document); document["content_hash"] = "sha256:" + "0" * 64; parsed = build_canonical_value(document); assert type(parsed) is ParsedCanonicalValue; document["content_hash"] = record_content_hash(parsed); return _canonical(document)


@pytest.fixture(scope="module")
def contract_context():
    assets = _assets(); return assets, _registry(assets), BUNDLE_PATH.read_bytes()


def test_complete_fixture_namespace_and_byte_identical_regeneration():
    generated1 = _build_all(); generated2 = _build_all(); assert generated1 == generated2
    expected = {str(path.relative_to(BASE)) for path in BASE.rglob("*") if path.is_file() and not str(path.relative_to(BASE)).startswith("downstream-schemas/") and str(path.relative_to(BASE)) != "e-family-conformance-vectors.json"}
    assert set(generated1) == expected
    assert all((BASE / path).read_bytes() == raw for path, raw in generated1.items())
    assert all(not raw.endswith(b"\n") for path, raw in generated1.items() if path.endswith(".json"))


def test_all_records_are_canonical_hash_valid_schema_valid_and_bundle_bound(contract_context):
    assets, registry, bundle_raw = contract_context; bundle = json.loads(bundle_raw); bundle_ref = planning._record_ref(bundle)
    for path in sorted(BASE.rglob("*.json")):
        if "downstream-schemas" in path.parts or path.name in {"e-family-conformance-vectors.json", "revision-lineage.json", "revision-impact.expected.json"}: continue
        raw = path.read_bytes(); parsed = planning.parse_canonical_json(raw); assert type(parsed) is ParsedCanonicalValue and canonical_bytes(parsed) == raw; assert record_content_hash(parsed) == parsed.to_python()["content_hash"]; schema_findings = validate_immutable_record_payload(parsed, registry); assert schema_findings == () or (path.name == "scope-v2.json" and len(schema_findings) == 1 and schema_findings[0].code.value == "AGTXIV.RECORD.SUPERSESSION_MISMATCH"); document = parsed.to_python(); assert document["envelope"].get("contract_bundle_ref") == bundle_ref; assert document["envelope"]["producer_context"]["environment_ref"]["asset_id"] == "canonicalization:agtxiv-record-canonical-json/2.0.0-candidate.1/provenance"


def test_synthetic_accept_block_and_successor_aggregate_branches(contract_context):
    assets, registry, bundle = contract_context; sources2 = {**SYNTHETIC_SOURCE, "notes.txt": b"Unrelated revision-two source row.\n"}
    accept = planning.validate_planning_scope_chain(_raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, _raw("synthetic", "plan-v1.json"), _raw("synthetic", "discovery-v1.json"), _raw("synthetic", "decision-accept-v1.json"), (), (_raw("synthetic", "scope-v1.json"),), (), assets, registry, bundle); assert not isinstance(accept, tuple)
    block = planning.validate_planning_scope_chain(_raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, _raw("synthetic", "plan-v1.json"), _raw("synthetic", "discovery-blocked-appendix.json"), _raw("synthetic", "decision-block-appendix.json"), (_raw("synthetic", "terminal-block-appendix.json"),), (), (), assets, registry, bundle); assert not isinstance(block, tuple)
    predecessor = planning.build_planning_scope_chain_declaration(_raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, _raw("synthetic", "plan-v1.json"), _raw("synthetic", "discovery-v1.json"), _raw("synthetic", "decision-accept-v1.json"), _raw("synthetic", "scope-v1.json"), assets, bundle); assert not isinstance(predecessor, tuple)
    successor = planning.validate_planning_scope_chain(_raw("synthetic", "snapshot-v2.json"), sources2, _raw("synthetic", "plan-v2.json"), _raw("synthetic", "discovery-v2.json"), _raw("synthetic", "decision-accept-v2.json"), (), (_raw("synthetic", "scope-v2.json"),), (predecessor,), assets, registry, bundle); assert not isinstance(successor, tuple)


def test_blocked_appendix_has_bidirectional_fallback_and_terminal_c_to_b_to_v11_composition(contract_context, monkeypatch):
    assets, registry, bundle = contract_context; discovery = _json("synthetic", "discovery-blocked-appendix.json"); appendix = next(row for row in discovery["payload"]["source_unit_coverage"] if row["normalized_path"] == "appendix.tex"); fallback = discovery["payload"]["unclassified_components"][0]; assert appendix["coverage_status"] == "BLOCKED_WITH_EVIDENCE" and fallback["component_id"] in appendix["component_ids"] and fallback["component_kind"] == "UNRESOLVED_SOURCE_REGION"; assert discovery["payload"]["discovery_errors"][0]["evidence_refs"] == fallback["evidence_refs"]
    plan_raw = _raw("synthetic", "plan-v1.json"); parsed_plan = planning.parse_canonical_json(plan_raw); constraints = planning._planning_constraints(assets, registry, parsed_plan.to_python()["payload"]); parsed_terminal = planning.parse_canonical_json(_raw("synthetic", "terminal-block-appendix.json")); calls = []
    original_c = planning.validate_typed_terminal_result_catalog_constraints; original_e = planning.validate_planning_terminal_registration_v1_1
    monkeypatch.setattr(planning, "validate_typed_terminal_result_catalog_constraints", lambda *args: (calls.append("C") or original_c(*args)))
    monkeypatch.setattr(planning, "validate_planning_terminal_registration_v1_1", lambda *args: (calls.append("1.1") or original_e(*args)))
    assert planning.validate_planning_terminal_constraints(parsed_terminal, registry, constraints[0], constraints[1], plan_raw, _raw("synthetic", "discovery-blocked-appendix.json"), _raw("synthetic", "decision-block-appendix.json"), assets, bundle) == (); assert calls == ["C", "1.1"]


def test_revision_preserves_unchanged_identities_and_exact_delta_and_impact(contract_context):
    assets, registry, bundle = contract_context; old = _json("synthetic", "scope-v1.json"); new = _json("synthetic", "scope-v2.json"); old_by_component = {row["component_id"]: row for row in old["payload"]["scope_entries"]}; new_by_component = {row["component_id"]: row for row in new["payload"]["scope_entries"]}; common = old_by_component.keys() & new_by_component.keys(); assert common and all(old_by_component[cid]["scope_entry_id"] == new_by_component[cid]["scope_entry_id"] for cid in common)
    delta = new["payload"]["revision_delta"]; assert len(delta["added_entry_ids"]) == len(delta["removed_entry_ids"]) == len(delta["classification_changed_entry_ids"]) == 1 and delta["source_binding_changed_entry_ids"] == []
    sources2 = {**SYNTHETIC_SOURCE, "notes.txt": b"Unrelated revision-two source row.\n"}; pred = planning.build_planning_scope_chain_declaration(_raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, _raw("synthetic", "plan-v1.json"), _raw("synthetic", "discovery-v1.json"), _raw("synthetic", "decision-accept-v1.json"), _raw("synthetic", "scope-v1.json"), assets, bundle); succ = planning.build_planning_scope_chain_declaration(_raw("synthetic", "snapshot-v2.json"), sources2, _raw("synthetic", "plan-v2.json"), _raw("synthetic", "discovery-v2.json"), _raw("synthetic", "decision-accept-v2.json"), _raw("synthetic", "scope-v2.json"), assets, bundle); lineage = _json("synthetic", "revision-lineage.json"); records = tuple(_raw("synthetic", f"downstream-{name}-output.json") for name in ("entry", "whole-scope", "derived")); impact = planning.compute_scope_revision_impact((pred,), succ, records, _projection(lineage), registry); assert not isinstance(impact, tuple); assert impact.to_python() == _json("synthetic", "revision-impact.expected.json"); assert impact.to_python()["directly_affected_record_ids"] == ["downstream:checkpoint-e/entry-output", "downstream:checkpoint-e/whole-scope-output"] and impact.to_python()["transitively_affected_record_ids"] == ["downstream:checkpoint-e/derived-output"]


def test_real_paper_is_exact_nine_committed_git_blobs_and_valid_local_chain(contract_context):
    assets, registry, bundle = contract_context; sources = _real_sources(); snapshot = _json("real-paper", "snapshot.json"); assert tuple(row["normalized_path"] for row in snapshot["payload"]["source_files"]) == tuple(sorted(REAL_PATHS, key=str.encode)); assert snapshot["payload"]["source_file_count"] == 9 and snapshot["payload"]["source_total_bytes"] == sum(map(len, sources.values()))
    result = planning.validate_planning_scope_chain(_raw("real-paper", "snapshot.json"), sources, _raw("real-paper", "plan.json"), _raw("real-paper", "discovery.json"), _raw("real-paper", "decision-accept.json"), (), (_raw("real-paper", "scope.json"),), (), assets, registry, bundle); assert not isinstance(result, tuple)


@pytest.mark.parametrize("field", ["query", "query_ref", "query_text", "requested_claim", "requested_theorem", "search", "filter", "include_only", "exclude", "path_subset", "family_subset", "region_subset", "dynamic_selector", "latest"])
def test_plan_rejects_every_frozen_query_or_narrowing_key(contract_context, field):
    assets, registry, bundle = contract_context; changed = _mutation(_raw("synthetic", "plan-v1.json"), lambda document: document["payload"].update({field: "hostile"})); result = planning.validate_agentization_plan(changed, _raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, assets, registry, bundle); assert isinstance(result, tuple) and result


@pytest.mark.parametrize("mutation", ["legacy", "same-id-substitution", "omitted-source", "reordered-obligation", "blocked-one-way", "aggregate-wrong-branch", "lineage-cycle"])
def test_fixture_derived_adversarial_cases_fail_closed(contract_context, mutation):
    assets, registry, bundle = contract_context
    if mutation == "legacy":
        forged = planning.SuppliedAsset(planning.LEGACY_RECORD_TYPE, "application/json", b"{}") if hasattr(planning, "SuppliedAsset") else None; result = planning.validate_agentization_plan(_raw("synthetic", "plan-v1.json"), _raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, assets + (forged,), registry, bundle)
    elif mutation == "same-id-substitution": result = planning.validate_paper_source_snapshot(_raw("synthetic", "snapshot-v1.json"), {**SYNTHETIC_SOURCE, "main.tex": b"changed"}, assets, registry, bundle)
    elif mutation == "omitted-source": result = planning.validate_paper_source_snapshot(_raw("synthetic", "snapshot-v1.json"), {k: v for k, v in SYNTHETIC_SOURCE.items() if k != "appendix.tex"}, assets, registry, bundle)
    elif mutation == "reordered-obligation":
        changed = _mutation(_raw("synthetic", "discovery-v1.json"), lambda document: document["payload"]["obligation_dispositions"].reverse()); result = planning.validate_inventory_discovery_result(changed, _raw("synthetic", "plan-v1.json"), _raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, assets, registry, bundle)
    elif mutation == "blocked-one-way":
        changed = _mutation(_raw("synthetic", "discovery-blocked-appendix.json"), lambda document: document["payload"]["unclassified_components"][0].update(evidence_refs=[])); result = planning.validate_inventory_discovery_result(changed, _raw("synthetic", "plan-v1.json"), _raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, assets, registry, bundle)
    elif mutation == "aggregate-wrong-branch": result = planning.validate_planning_scope_chain(_raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, _raw("synthetic", "plan-v1.json"), _raw("synthetic", "discovery-v1.json"), _raw("synthetic", "decision-accept-v1.json"), (_raw("synthetic", "terminal-block-appendix.json"),), (), (), assets, registry, bundle)
    else:
        lineage = _json("synthetic", "revision-lineage.json"); lineage["edges"].append({"producer_record_id": "downstream:checkpoint-e/derived-output", "consumer_record_id": "downstream:checkpoint-e/entry-output", "relation": "DERIVED_FROM"}); sources2 = {**SYNTHETIC_SOURCE, "notes.txt": b"Unrelated revision-two source row.\n"}; pred = planning.build_planning_scope_chain_declaration(_raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, _raw("synthetic", "plan-v1.json"), _raw("synthetic", "discovery-v1.json"), _raw("synthetic", "decision-accept-v1.json"), _raw("synthetic", "scope-v1.json"), assets, bundle); succ = planning.build_planning_scope_chain_declaration(_raw("synthetic", "snapshot-v2.json"), sources2, _raw("synthetic", "plan-v2.json"), _raw("synthetic", "discovery-v2.json"), _raw("synthetic", "decision-accept-v2.json"), _raw("synthetic", "scope-v2.json"), assets, bundle); result = planning.compute_scope_revision_impact((pred,), succ, tuple(_raw("synthetic", f"downstream-{name}-output.json") for name in ("entry", "whole-scope", "derived")), _projection(lineage), registry)
    assert isinstance(result, tuple) and result and all(type(item) is Diagnostic for item in result)


def test_fixture_validators_are_deterministic_and_do_not_use_ambient_io(contract_context, monkeypatch):
    assets, registry, bundle = contract_context; args = (_raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, assets, registry, bundle); first = planning.validate_paper_source_snapshot(*args); assert not isinstance(first, tuple)
    def sentinel(*args, **kwargs): raise AssertionError("ambient I/O reached")
    monkeypatch.setattr(builtins, "open", sentinel); monkeypatch.setattr(socket, "socket", sentinel); monkeypatch.setattr(subprocess, "run", sentinel)
    for _ in range(100):
        result = planning.validate_paper_source_snapshot(*args); assert not isinstance(result, tuple) and result.to_python() == first.to_python()
    invalid_args = (args[0], {**SYNTHETIC_SOURCE, "main.tex": b"wrong"}, *args[2:]); diagnostics = planning.validate_paper_source_snapshot(*invalid_args)
    for _ in range(100): assert planning.validate_paper_source_snapshot(*invalid_args) == diagnostics


@pytest.mark.parametrize("hostile", ["text", bytearray(b"{}"), memoryview(b"{}")])
def test_fixture_public_seams_reject_hostile_raw_types(contract_context, hostile):
    assets, registry, bundle = contract_context; result = planning.validate_agentization_plan(hostile, _raw("synthetic", "snapshot-v1.json"), SYNTHETIC_SOURCE, assets, registry, bundle); assert isinstance(result, tuple) and result


if __name__ == "__main__":
    generated = _build_all()
    for relative, raw in generated.items():
        path = BASE / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    print(f"wrote {len(generated)} fixture paths")
