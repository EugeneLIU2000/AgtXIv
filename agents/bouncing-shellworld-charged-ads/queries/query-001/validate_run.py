#!/usr/bin/env python3
"""Validate the query-local V1 claim--mathematics bridge demonstration."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
Q = Path(__file__).resolve().parent
TARGET_SCHEMA = REPO / "schemas/target-ref.schema.json"
CLAIM_SCHEMA = REPO / "Stabilizerness/ScientificClaimRegistry/schema/scientific-claim.schema.json"
MATH_SCHEMA = REPO / "Stabilizerness/MathClaimIRRegistry/schema/math-claim-ir.schema.json"
BRIDGE_SCHEMA = REPO / "Stabilizerness/ExternalRecordRegistry/schema/claim-math-bridge.schema.json"
ASSESSMENT_SCHEMA = REPO / "Stabilizerness/ExternalRecordRegistry/schema/bridge-assessment.schema.json"
FIXTURE_BRIDGE = REPO / "Stabilizerness/ExternalRecordRegistry/bridges/predicting-magic-from-very-few-measurements.jsonl"
FIXTURE_ASSESSMENT = REPO / "Stabilizerness/ExternalRecordRegistry/bridge-assessments/predicting-magic-from-very-few-measurements.jsonl"


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    if isinstance(value, dict):
        return {canonicalize(k): canonicalize(v) for k, v in sorted(value.items())}
    raise ValueError(f"unsupported canonical value: {type(value).__name__}")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def content_hash(record: dict[str, Any]) -> str:
    return canonical_hash({k: v for k, v in record.items() if k != "content_hash"})


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            row = json.loads(line)
            if not row.get("id"):
                raise ValueError(f"{path}:{number}: record missing id")
            rows.append(row)
    return rows


def resolve_pointer(document: Any, pointer: Any) -> tuple[Any, list[str]]:
    if not isinstance(pointer, str) or not pointer.startswith("/") or not pointer:
        raise ValueError("component_path must be a nonempty RFC 6901 JSON Pointer")
    tokens = []
    current = document
    for raw in pointer.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if "~" in token and "~" not in raw:
            raise ValueError(f"malformed pointer escape: {pointer}")
        tokens.append(token)
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and str(int(token)) == token and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ValueError(f"unresolved component_path: {pointer}")
    return current, tokens


def expected_math_ref(math: dict[str, Any], path: str) -> dict[str, Any]:
    return {
        "target_kind": "org.agtxiv.claim_ir",
        "type_schema": {"uri": "https://agtxiv.org/schema/math-claimir/1.0.0", "content_hash": file_hash(MATH_SCHEMA)},
        "target_id": math["id"], "target_revision": math["revision"], "target_content_hash": math["semantic_content_hash"],
        "target_artifact": math["artifact"], "component_path": path,
        "claim_ir": {"id": math["id"], "revision": math["revision"], "semantic_content_hash": math["semantic_content_hash"]},
        "claim_ir_members": [],
    }


def validate() -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, Any] = {}
    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError as exc:
        return {"outcome": "BLOCKED", "blocker": f"standard local JSON Schema validator unavailable: {exc}", "errors": []}

    target_schema = load_json(TARGET_SCHEMA)
    registry = Registry().with_resource(target_schema["$id"], Resource.from_contents(target_schema))
    format_checker = jsonschema.FormatChecker()

    def schema_check(record: dict[str, Any], schema_path: Path, label: str) -> None:
        schema = load_json(schema_path)
        found = sorted(jsonschema.Draft202012Validator(schema, registry=registry, format_checker=format_checker).iter_errors(record), key=lambda e: list(e.path))
        errors.extend(f"{label} schema: {'/'.join(map(str, e.path))}: {e.message}" for e in found)

    # Validate the repository's declared conforming fixture first. An inconsistency is a blocker, not a reason to weaken validation.
    fixture_bridge = json.loads(FIXTURE_BRIDGE.read_text().splitlines()[0])
    fixture_assessment = json.loads(FIXTURE_ASSESSMENT.read_text().splitlines()[0])
    before_fixture = len(errors)
    schema_check(fixture_bridge, BRIDGE_SCHEMA, "conforming fixture bridge")
    schema_check(fixture_assessment, ASSESSMENT_SCHEMA, "conforming fixture assessment")
    if len(errors) != before_fixture:
        return {"outcome": "BLOCKED", "blocker": "repository normative schemas are inconsistent with the declared conforming fixture", "errors": errors}
    checks["normative_schema_fixture_consistency"] = "PASSED"

    claim = load_json(Q / "scientific-claim.json")
    math = load_json(Q / "math-claim-ir.json")
    bridge = load_json(Q / "claim-math-bridge.json")
    assessment = load_json(Q / "bridge-assessment.json")
    for record, schema, label in ((claim, CLAIM_SCHEMA, "ScientificClaim"), (math, MATH_SCHEMA, "MathClaimIR"), (bridge, BRIDGE_SCHEMA, "ClaimMathBridge"), (assessment, ASSESSMENT_SCHEMA, "BridgeAssessment")):
        schema_check(record, schema, label)
    checks["normative_and_target_schema_validation"] = "PASSED" if not errors else "FAILED"

    if claim.get("content_hash") != content_hash(claim): errors.append("ScientificClaim canonical content_hash mismatch")
    if bridge.get("content_hash") != content_hash(bridge): errors.append("ClaimMathBridge canonical content_hash mismatch")
    if assessment.get("content_hash") != content_hash(assessment): errors.append("BridgeAssessment canonical content_hash mismatch")
    semantic = {"id": math["id"], "revision": math["revision"], "claim_id": math["claim"]["id"], "source": math["source"], "statement_kind": math["statement_kind"], "normalized_statement_expanded_latex": math["normalized_statement_expanded_latex"], "structured_statement": math["structured_statement"], "normalization": math["normalization"]}
    if math.get("semantic_content_hash") != canonical_hash(semantic): errors.append("MathClaimIR semantic_content_hash mismatch")
    artifact_payload = copy.deepcopy(math); artifact_payload["artifact"]["artifact_hash"] = None
    if math.get("artifact", {}).get("artifact_hash") != canonical_hash(artifact_payload): errors.append("MathClaimIR artifact_hash mismatch")

    expected_claim_ref = {"target_kind":"org.agtxiv.scientific_claim","type_schema":{"uri":"https://agtxiv.org/schema/scientific-claim/1.1.0","content_hash":file_hash(CLAIM_SCHEMA)},"target_id":claim["id"],"target_revision":claim["record_revision"],"target_content_hash":claim["content_hash"],"target_artifact":None,"component_path":None,"claim_ir":None,"claim_ir_members":[]}
    if bridge.get("scientific_claim_ref") != expected_claim_ref: errors.append("bridge ScientificClaim reference is not exact and canonical")
    if bridge.get("source_anchors") != claim.get("source_anchors"): errors.append("bridge does not preserve exact ScientificClaim anchors")
    frozen_anchors = {row["id"]: row for row in load_jsonl(REPO / "agents/bouncing-shellworld-charged-ads/source/anchors.jsonl")}
    for aid in bridge.get("source_anchors", []):
        if aid not in frozen_anchors: errors.append(f"unknown frozen source anchor: {aid}")
    for component in bridge.get("source_components", []):
        if not set(component.get("source_anchors", [])) <= set(bridge.get("source_anchors", [])): errors.append(f"{component.get('component_id')}: anchor outside pinned claim")
        for mapped in component.get("mapped_targets", []):
            ref = mapped["target_ref"]; path = ref.get("component_path")
            if ref != expected_math_ref(math, path): errors.append(f"{component['component_id']}: target reference is not exact and canonical")
            try: _, tokens = resolve_pointer(math, path)
            except ValueError as exc: errors.append(f"{component['component_id']}: {exc}"); continue
            role = mapped["role"]
            conclusion = path == "/structured_statement/conclusion" or path.startswith("/structured_statement/conclusion/")
            assumption = (tokens[:2] == ["structured_statement", "assumptions"] and len(tokens) >= 4) or (tokens[:2] == ["structured_statement", "quantifiers"] and len(tokens) >= 3) or (tokens[:2] == ["structured_statement", "mathematical_mode"] and len(tokens) >= 3)
            if role == "CONCLUSION" and not conclusion: errors.append(f"{component['component_id']}: CONCLUSION role mismatch")
            if role == "ASSUMPTION" and not assumption: errors.append(f"{component['component_id']}: ASSUMPTION role mismatch")
    checks["exact_refs_anchors_and_rfc6901_targets"] = "PASSED" if not errors else "FAILED"

    required_components = {"component:thin-brane-constant-tension","component:ads-radius-order","component:mass-charge-order","component:positive-scale-factor-domain","component:no-string-zero-lambda-regime","component:reduced-friedmann-equation","component:exact-conformal-time-solution","component:literal-rho-condition","component:literal-nonsingular-cyclic-bounce","component:minimum-at-integer-pi","component:intrinsic-turning-polynomial","component:model-reduction-approximation-status"}
    ids = [c.get("component_id") for c in bridge.get("source_components", [])]
    if set(ids) != required_components or len(ids) != len(required_components): errors.append("source component list is incomplete or duplicated")
    forbidden = {"status","truth_status","verification","verification_status","evidence","evidence_refs","blocker","blocker_refs","acceptance","scientific_acceptance","coverage","aggregate_coverage","navigation_coverage"}
    def walk(v: Any, path: str = "") -> None:
        if isinstance(v, dict):
            for k, child in v.items():
                if k.lower() in forbidden: errors.append(f"bridge forbidden field: {path + '.' if path else ''}{k}")
                walk(child, f"{path}.{k}" if path else k)
        elif isinstance(v, list):
            for i, child in enumerate(v): walk(child, f"{path}[{i}]")
    walk(bridge)
    checks["component_completeness_and_bridge_purity"] = "PASSED" if not errors else "FAILED"

    records = load_jsonl(Q / "verification/evidence-records.jsonl")
    record_by_id = {r["id"]: r for r in records}
    if len(record_by_id) != len(records): errors.append("duplicate evidence/blocker record id")
    for row in records:
        if row.get("content_hash") != content_hash(row): errors.append(f"{row['id']}: canonical content_hash mismatch")
    for field in ("evidence_refs", "blocker_refs"):
        for ref in assessment.get(field, []):
            row = record_by_id.get(ref.get("id"))
            if row is None or ref != {"id":row["id"],"record_revision":row["record_revision"],"content_hash":row["content_hash"]}: errors.append(f"unknown or inexact {field} reference: {ref.get('id')}")
    expected_bridge_ref={"target_kind":"org.agtxiv.claim_math_bridge","type_schema":{"uri":"https://agtxiv.org/schema/claim-math-bridge/1.0.0","content_hash":file_hash(BRIDGE_SCHEMA)},"target_id":bridge["id"],"target_revision":bridge["record_revision"],"target_content_hash":bridge["content_hash"],"target_artifact":None,"component_path":None,"claim_ir":None,"claim_ir_members":[]}
    if assessment.get("bridge_ref") != expected_bridge_ref: errors.append("assessment bridge reference is not exact and canonical")
    outcomes=assessment.get("component_outcomes",[])
    if [o.get("source_component_id") for o in outcomes] != ids: errors.append("assessment components are not one-to-one in bridge order")
    known_basis={r["id"] for r in assessment.get("evidence_refs",[])+assessment.get("blocker_refs",[])}
    component_by={c["component_id"]:c for c in bridge["source_components"]}
    for out in outcomes:
        if not set(out.get("basis_refs",[])) <= known_basis: errors.append(f"{out['source_component_id']}: unknown basis ref")
        comp=component_by[out["source_component_id"]]; roles={m["role"] for m in comp["mapped_targets"]}
        expected_kind="RESIDUAL_REVIEW" if comp["disposition"]=="RESIDUAL" else "APPLICABILITY_MATCH" if roles and roles <= {"ASSUMPTION","DEFINITION"} else "MATHEMATICAL_DISPOSITION"
        if out.get("assessment_kind") != expected_kind: errors.append(f"{out['source_component_id']}: assessment kind mismatch")
        if out.get("status") in {"VERIFIED","REFUTED"} and not any(x.startswith("evidence:") for x in out.get("basis_refs",[])): errors.append(f"{out['source_component_id']}: dispositive outcome lacks evidence")
    checks["evidence_blocker_refs_and_one_to_one_assessment"] = "PASSED" if not errors else "FAILED"

    out_by={o["source_component_id"]:o for o in outcomes}
    if assessment.get("scientific_acceptance") != "NOT_REVIEWED": errors.append("scientific_acceptance must be NOT_REVIEWED")
    if assessment.get("assumption_object_match",{}).get("status") != "PARTIAL": errors.append("assumption/object match must be PARTIAL")
    if assessment.get("root_agent_conclusion",{}).get("outcome") not in {"UNKNOWN","NOT_CHECKED"}: errors.append("literal scientific conclusion was promoted")
    if out_by.get("component:literal-nonsingular-cyclic-bounce",{}).get("status") not in {"UNKNOWN","NOT_CHECKED"}: errors.append("literal source bounce component was promoted")
    if out_by.get("component:literal-rho-condition",{}).get("status") not in {"UNKNOWN","NOT_CHECKED"}: errors.append("literal rho<=1 component was promoted")
    result=load_json(Q/"verification/check-result.json")
    if result.get("conditional_mathematical_outcome") != "VERIFIED_WITH_ENDPOINT_QUALIFICATION" or not result.get("aggregate_passed"): errors.append("conditional mathematical result not closed by all checks")
    if result.get("literal_scientific_claim_outcome") not in {"UNKNOWN","NOT_CHECKED"}: errors.append("check-result promotes literal scientific claim")
    checks["non_promotion_and_status_separation"] = "PASSED" if not errors else "FAILED"

    manifest=load_json(Q/"run-manifest.json")
    for section in ("consumed_artifacts","produced_artifacts"):
        for item in manifest.get(section,[]):
            path=REPO/item["path"]
            if not path.is_file() or file_hash(path).removeprefix("sha256:") != item.get("sha256"): errors.append(f"manifest hash mismatch: {item.get('path')}")
    payload=copy.deepcopy(manifest); expected=payload.get("self_artifact",{}).pop("sha256",None)
    actual=canonical_hash(payload).removeprefix("sha256:")
    if actual != expected: errors.append("run-manifest self-payload hash mismatch")
    checks["run_manifest_hashes_and_self_hash"] = "PASSED" if not errors else "FAILED"

    before=file_hash(Q/"verification/check-result.json")
    proc=subprocess.run([sys.executable,str(Q/"verification/derive_and_check.py")],cwd=REPO,capture_output=True,text=True)
    after=file_hash(Q/"verification/check-result.json")
    if proc.returncode != 0 or before != after: errors.append(f"verification rerun is not deterministic: exit={proc.returncode}, before={before}, after={after}, stderr={proc.stderr.strip()}")
    checks["rerun_result_determinism"] = "PASSED" if proc.returncode == 0 and before == after else "FAILED"

    return {"schema":"agtxiv.query-v1-validation-result/1.0.0","validator":"validate_run.py","outcome":"PASSED" if not errors else "FAILED","checks":checks,"counts":{"bridge_components":len(ids),"component_outcomes":len(outcomes),"external_records":len(records),"errors":len(errors)},"verification_result_sha256":after,"errors":errors,"legacy_validator_scope_note":"tools/validate_pilot.py supplies repository-level legacy parse and structural checks only; it is not V1 bridge validation."}


if __name__ == "__main__":
    result=validate()
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result.get("outcome")=="PASSED" else 1)
