#!/usr/bin/env python3
"""Export the graph-theoretic paper's contribution-role ScientificClaims."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PAPER_ID = "arxiv:2607.26154v1"
POLYTOPE_CLAIM_ID = "claim:graph-theoretic-nonstabilizerness:sign-relaxation-exactness"
POLYTOPE_FACET_ID = "facet:polytope-exactness"
EXACT_POLYTOPE_MATH_ID = "math-claim-ir:graph-theoretic-nonstabilizerness:relaxation-polytope-exactness"
ORACLE_SKELETON_ID = "oracle-skeleton:polytope-exactness"
CLAIMS = ROOT / "Stabilizerness/ScientificClaimRegistry/claims/contribution-role-scientific-claims.jsonl"
CALIBRATIONS = ROOT / "Stabilizerness/ExternalRecordRegistry/scientific-claim-calibrations/scientific-claim-calibrations.jsonl"
SUPPORT = ROOT / "Stabilizerness/ExternalRecordRegistry/claim-support-associations/scientific-claim-support.jsonl"
MATH_MANIFEST = ROOT / "Stabilizerness/MathClaimIRRegistry/manifest.json"
EXTERNAL_MANIFEST = ROOT / "Stabilizerness/ExternalRecordRegistry/manifest.json"
FORMAL_CLAIMS = ROOT / "Stabilizerness/ScientificClaimRegistry/claims/graph-theoretic-nonstabilizerness.jsonl"
SOURCE_ANCHORS = ROOT / "Stabilizerness/MathClaimIRRegistry/source-anchors/graph-theoretic-nonstabilizerness.jsonl"
CANDIDATE_DAG = ROOT / "Stabilizerness/dag/claim-dag.json"
OUTPUT = ROOT / "demo_design/scientific_claims/data/graph-theoretic-scientific-claims.json"
GRAPH_NODE_TYPES = {
    "paper", "scientific_claim_contribution", "facet", "scientific_claim_formal",
    "source_occurrence", "math_claim_ir", "mathematical_proposition_ir",
    "oracle_skeleton", "oracle_candidate",
}
GRAPH_EDGE_TYPES = {
    "contains", "has_facet", "source_calibration", "normalizes_identity",
    "provisional_navigation", "oracle_overlay", "oracle_contains", "oracle_candidate_dependency",
}
ORACLE_NODE_IDS = {
    "root:gottesman-stabilizer-formalism", "root:varela-reduced-polytope",
    "claim:reduced-stabilizer-polytope", "claim:frustration-graph",
    "claim:exact-reduced-vrep", "claim:sign-syndrome-linear-consistent",
    "claim:dependency-affine-code", "claim:pauli-active-dependency",
    "claim:no-active-free-signs", "claim:relaxation-exactness",
}
ORACLE_EVIDENCE = {
    "oracle_status": "ORACLE_PROPOSED",
    "source_alignment": "UNREVIEWED_AT_EDGE_LEVEL",
    "lean_support": "NOT_EXTRACTED",
    "disposition": "CANDIDATE",
}
SUPPORTED_TARGETS = {
    "org.agtxiv.claim_ir": "math-claim-ir:",
    "org.agtxiv.mathematical_proposition_ir": "math-proposition-ir:",
}
TARGET_SCHEMAS = {
    "org.agtxiv.scientific_claim": ROOT / "Stabilizerness/ScientificClaimRegistry/schema/scientific-claim.schema.json",
    "org.agtxiv.claim_ir": ROOT / "Stabilizerness/MathClaimIRRegistry/schema/math-claim-ir.schema.json",
    "org.agtxiv.mathematical_proposition_ir": ROOT / "Stabilizerness/ExternalRecordRegistry/schema/mathematical-proposition-ir.schema.json",
}


class ExportError(ValueError):
    """Raised when registry data cannot be exported without ambiguity."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExportError(f"cannot read JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise ExportError(f"expected a JSON object in {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ExportError(f"cannot read {path}: {error}") from error
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ExportError(f"invalid JSON in {path}:{line_number}: {error}") from error
        if not isinstance(record, dict):
            raise ExportError(f"expected a JSON object in {path}:{line_number}")
        records.append(record)
    return records


def file_hash(path: Path) -> str:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ExportError(f"cannot hash {path}: {error}") from error


def unique_by(records: list[dict[str, Any]], key: str, label: str) -> dict[Any, dict[str, Any]]:
    indexed: dict[Any, dict[str, Any]] = {}
    for record in records:
        value = record.get(key)
        if value is None:
            raise ExportError(f"{label} has no {key}")
        if value in indexed:
            raise ExportError(f"duplicate {label} {key}: {value}")
        indexed[value] = record
    return indexed


def assert_claim_ref(reference: Any, claim: dict[str, Any], label: str, component_path: str | None = None) -> None:
    if not isinstance(reference, dict):
        raise ExportError(f"{label} has no scientific_claim_ref object")
    expected = {
        "target_kind": "org.agtxiv.scientific_claim",
        "target_id": claim["id"],
        "target_revision": claim["record_revision"],
        "target_content_hash": claim["content_hash"],
        "component_path": component_path,
        "claim_ir": None,
        "claim_ir_members": [],
    }
    for key, value in expected.items():
        if reference.get(key) != value:
            raise ExportError(f"{label} {key} does not match {claim['id']}")
    expected_artifact = None if component_path else claim["artifact"]
    if reference.get("target_artifact") != expected_artifact:
        raise ExportError(f"{label} target_artifact does not match {claim['id']}")
    expected_type_schema = {
        "uri": claim["artifact"]["schema_uri"],
        "content_hash": file_hash(TARGET_SCHEMAS["org.agtxiv.scientific_claim"]),
    }
    if reference.get("type_schema") != expected_type_schema:
        raise ExportError(f"{label} type schema does not match {claim['id']}")


def validate_occurrences(claims: list[dict[str, Any]]) -> None:
    occurrence_ids: set[str] = set()
    for claim in claims:
        occurrences = claim.get("occurrences")
        if not isinstance(occurrences, list) or not occurrences:
            raise ExportError(f"{claim['id']} has no source occurrences")
        for occurrence in occurrences:
            identifier = occurrence.get("id") if isinstance(occurrence, dict) else None
            if not isinstance(identifier, str) or identifier in occurrence_ids:
                raise ExportError(f"missing or duplicate source occurrence ID: {identifier!r}")
            occurrence_ids.add(identifier)
            artifact = occurrence.get("source_artifact")
            if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
                raise ExportError(f"{identifier} has no source artifact path")
            source_path = ROOT / artifact["path"]
            if artifact.get("sha256") != file_hash(source_path):
                raise ExportError(f"{identifier} source artifact hash mismatch")
            start, end = occurrence.get("line_start"), occurrence.get("line_end")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
                raise ExportError(f"{identifier} has an invalid source line range")
            try:
                source_lines = source_path.read_text(encoding="utf-8").splitlines()
            except OSError as error:
                raise ExportError(f"cannot read source for {identifier}: {error}") from error
            if end > len(source_lines):
                raise ExportError(f"{identifier} source line range exceeds {artifact['path']}")
            if occurrence.get("source_text") != "\n".join(source_lines[start - 1:end]):
                raise ExportError(f"{identifier} verbatim source text mismatch")


def load_support_targets() -> dict[tuple[str, int], dict[str, Any]]:
    math_manifest = load_json(MATH_MANIFEST)
    external_manifest = load_json(EXTERNAL_MANIFEST)
    relative_paths = math_manifest.get("claim_files", []) + external_manifest.get("proposition_files", [])
    if not relative_paths or not all(isinstance(path, str) for path in relative_paths):
        raise ExportError("support target manifests contain no usable target files")

    targets: dict[tuple[str, int], dict[str, Any]] = {}
    for relative_path in relative_paths:
        path = ROOT / relative_path
        for target in load_jsonl(path):
            identifier = target.get("id")
            revision = target.get("revision")
            if not isinstance(identifier, str) or not identifier.startswith(tuple(SUPPORTED_TARGETS.values())):
                continue
            key = (identifier, revision)
            if key in targets:
                raise ExportError(f"duplicate support target: {identifier} revision {revision}")
            targets[key] = target
    return targets


def assert_support_ref(reference: Any, targets: dict[tuple[str, int], dict[str, Any]], label: str) -> None:
    if not isinstance(reference, dict):
        raise ExportError(f"{label} has no target_ref object")
    kind = reference.get("target_kind")
    identifier = reference.get("target_id")
    revision = reference.get("target_revision")
    prefix = SUPPORTED_TARGETS.get(kind)
    if prefix is None:
        raise ExportError(f"{label} has unsupported target kind {kind!r}")
    if not isinstance(identifier, str) or not identifier.startswith(prefix):
        raise ExportError(f"{label} target kind does not match target ID {identifier!r}")
    target = targets.get((identifier, revision))
    if target is None:
        raise ExportError(f"{label} has dangling target {identifier} revision {revision}")
    if reference.get("target_content_hash") != target.get("semantic_content_hash"):
        raise ExportError(f"{label} target hash does not match {identifier}")
    if reference.get("target_artifact") != target.get("artifact"):
        raise ExportError(f"{label} target artifact does not match {identifier}")
    expected_type_schema = {
        "uri": target["artifact"]["schema_uri"],
        "content_hash": file_hash(TARGET_SCHEMAS[kind]),
    }
    if reference.get("type_schema") != expected_type_schema:
        raise ExportError(f"{label} target type schema does not match {identifier}")
    if reference.get("component_path") is not None or reference.get("claim_ir_members") != []:
        raise ExportError(f"{label} has an unexpected component path or member list")
    claim_ir = reference.get("claim_ir")
    if kind == "org.agtxiv.claim_ir":
        expected = {
            "id": identifier,
            "revision": revision,
            "semantic_content_hash": target["semantic_content_hash"],
        }
        if claim_ir != expected:
            raise ExportError(f"{label} ClaimIR identity does not match {identifier}")
    elif claim_ir is not None:
        raise ExportError(f"{label} MathematicalPropositionIR must not contain claim_ir")


def compact_label(identifier: str) -> str:
    return identifier.rsplit(":", 1)[-1].replace("-", " ").title()


def fenced(text: str, language: str = "") -> str:
    if "```" in text:
        raise ExportError("graph Markdown code content contains an unsupported fence")
    return f"```{language}\n{text}\n```"


def validate_markdown_detail(detail: Any, node_id: str) -> None:
    if not isinstance(detail, str) or not detail.strip().startswith("## "):
        raise ExportError(f"graph node {node_id} has missing or malformed Markdown detail")
    lowered = detail.lower()
    unsafe = ("<script", "javascript:", "data:text/html", "onerror=", "onload=", "\x00")
    if any(token in lowered for token in unsafe):
        raise ExportError(f"graph node {node_id} has unsafe Markdown detail")
    if detail.count("```") % 2:
        raise ExportError(f"graph node {node_id} has an unclosed Markdown fence")


def load_oracle_subgraph() -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    dag = load_json(CANDIDATE_DAG)
    if dag.get("graph_view") != "ORACLE_CANDIDATE":
        raise ExportError("candidate DAG is not an ORACLE_CANDIDATE graph view")
    dag_nodes = unique_by(dag.get("nodes", []), "id", "candidate DAG node")
    missing = ORACLE_NODE_IDS - dag_nodes.keys()
    if missing:
        raise ExportError(f"candidate DAG is missing required nodes: {sorted(missing)}")
    selected_nodes = {candidate_id: dag_nodes[candidate_id] for candidate_id in ORACLE_NODE_IDS}
    for candidate_id, record in selected_nodes.items():
        issues = record.get("issue_badges", [])
        if not isinstance(issues, list):
            raise ExportError(f"candidate DAG node {candidate_id} has malformed issue badges")
        for issue in issues:
            if not isinstance(issue, dict) or set(issue) != {"object", "status", "badges", "interpretation"}:
                raise ExportError(f"candidate DAG node {candidate_id} has malformed structured issue metadata")
            if not isinstance(issue["badges"], list) or not issue["badges"]:
                raise ExportError(f"candidate DAG node {candidate_id} has an issue without badges")
    selected_edges = [
        edge for edge in dag.get("edges", [])
        if edge.get("from") in selected_nodes and edge.get("to") in selected_nodes
    ]
    if not selected_edges:
        raise ExportError("candidate DAG contains no selected dependency edges")
    for edge in selected_edges:
        if edge.get("evidence") != ORACLE_EVIDENCE:
            raise ExportError(f"candidate DAG edge {edge.get('from')} -> {edge.get('to')} has unexpected evidence")
        if edge.get("type") not in dag.get("edge_types", {}):
            raise ExportError(f"candidate DAG edge has undeclared type {edge.get('type')}")
        if not isinstance(edge.get("reason"), str) or not edge["reason"].strip():
            raise ExportError(f"candidate DAG edge {edge.get('from')} -> {edge.get('to')} has no reason")
    return dag, selected_nodes, selected_edges


def oracle_layout_levels(selected_nodes: dict[str, dict[str, Any]], selected_edges: list[dict[str, Any]]) -> dict[str, int]:
    predecessors = {candidate_id: set() for candidate_id in selected_nodes}
    successors = {candidate_id: set() for candidate_id in selected_nodes}
    for edge in selected_edges:
        predecessors[edge["to"]].add(edge["from"])
        successors[edge["from"]].add(edge["to"])
    ready = sorted(candidate_id for candidate_id, incoming in predecessors.items() if not incoming)
    levels = {candidate_id: 5 for candidate_id in ready}
    remaining = {candidate_id: set(incoming) for candidate_id, incoming in predecessors.items()}
    visited = 0
    while ready:
        candidate_id = ready.pop(0)
        visited += 1
        for target in sorted(successors[candidate_id]):
            levels[target] = max(levels.get(target, 5), levels[candidate_id] + 1)
            remaining[target].discard(candidate_id)
            if not remaining[target]:
                ready.append(target)
                ready.sort()
    if visited != len(selected_nodes):
        raise ExportError("selected Oracle candidate subgraph contains a cycle")
    return levels


def expected_polytope_navigation() -> list[dict[str, Any]]:
    associations = [
        record for record in load_jsonl(SUPPORT)
        if record.get("scientific_claim_ref", {}).get("target_id") == POLYTOPE_CLAIM_ID
    ]
    if len(associations) != 1:
        raise ExportError("expected exactly one support association for the polytope contribution claim")
    links = [link for link in associations[0].get("links", []) if link.get("facet_id") == POLYTOPE_FACET_ID]
    required = {
        (EXACT_POLYTOPE_MATH_ID, "DIRECT_ATOMIC_SUPPORT", "COMPLETE"),
        ("math-claim-ir:graph-theoretic-nonstabilizerness:sign-set-collapse", "FRAMEWORK_SUPPORT", "PARTIAL"),
    }
    actual = {
        (link.get("target_ref", {}).get("target_id"), link.get("relationship"), link.get("facet_coverage"))
        for link in links
    }
    if actual != required:
        raise ExportError("polytope facet Registry association does not contain the required exact navigation pair")
    return links


def validate_graph(graph: dict[str, Any]) -> None:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ExportError("graph payload must contain node and edge arrays")
    node_by_id = unique_by(nodes, "id", "graph node")
    unique_by(edges, "id", "graph edge")
    prefixes = {
        "paper": ("paper:",),
        "scientific_claim_contribution": ("claim:",),
        "facet": ("graph-facet:",),
        "scientific_claim_formal": ("claim:",),
        "source_occurrence": ("occurrence:",),
        "math_claim_ir": ("math-claim-ir:",),
        "mathematical_proposition_ir": ("math-proposition-ir:",),
        "oracle_skeleton": ("oracle-skeleton:",),
        "oracle_candidate": ("oracle-candidate:",),
    }
    for node in nodes:
        node_type = node.get("type")
        if node_type not in GRAPH_NODE_TYPES:
            raise ExportError(f"graph node {node.get('id')} has unsupported type {node_type!r}")
        if not str(node["id"]).startswith(prefixes[node_type]):
            raise ExportError(f"graph node type {node_type} does not match ID {node['id']}")
        if not isinstance(node.get("label"), str) or not node["label"].strip():
            raise ExportError(f"graph node {node['id']} has no label")
        if node_type == "oracle_candidate" and not isinstance(node.get("layout_level"), int):
            raise ExportError(f"Oracle candidate {node['id']} has no DAG-derived layout level")
        validate_markdown_detail(node.get("detail_markdown"), node["id"])
    endpoint_types = {
        "contains": ({"paper"}, {"scientific_claim_contribution"}),
        "has_facet": ({"scientific_claim_contribution"}, {"facet"}),
        "source_calibration": ({"scientific_claim_contribution"}, {"source_occurrence"}),
        "normalizes_identity": ({"math_claim_ir"}, {"scientific_claim_formal"}),
        "provisional_navigation": ({"facet"}, {"math_claim_ir", "mathematical_proposition_ir"}),
        "oracle_overlay": ({"math_claim_ir"}, {"oracle_skeleton"}),
        "oracle_contains": ({"oracle_skeleton"}, {"oracle_candidate"}),
        "oracle_candidate_dependency": ({"oracle_candidate"}, {"oracle_candidate"}),
    }
    for edge in edges:
        edge_type = edge.get("type")
        if edge_type not in GRAPH_EDGE_TYPES:
            raise ExportError(f"graph edge {edge.get('id')} has unsupported type")
        if edge.get("source") not in node_by_id or edge.get("target") not in node_by_id:
            raise ExportError(f"graph edge {edge.get('id')} has a dangling endpoint")
        source_types, target_types = endpoint_types[edge_type]
        if node_by_id[edge["source"]]["type"] not in source_types or node_by_id[edge["target"]]["type"] not in target_types:
            raise ExportError(f"graph edge {edge['id']} has endpoint types invalid for {edge_type}")
        expand_from = edge.get("expand_from")
        if expand_from not in node_by_id:
            raise ExportError(f"graph edge {edge['id']} has an invalid expansion owner")
        if edge_type != "oracle_candidate_dependency" and expand_from != edge["source"]:
            raise ExportError(f"graph edge {edge['id']} must expand from its source")
        if edge_type == "oracle_candidate_dependency" and node_by_id[expand_from]["type"] != "oracle_skeleton":
            raise ExportError(f"Oracle edge {edge['id']} must be owned by its skeleton")
        if edge_type == "provisional_navigation":
            if not str(edge.get("label", "")).startswith("PROVISIONAL NAVIGATION · "):
                raise ExportError(f"mathematical navigation edge {edge['id']} has misleading status text")
        if edge_type == "normalizes_identity" and edge.get("basis") != "Exact MathClaimIR.claim immutable reference":
            raise ExportError(f"identity edge {edge['id']} has no exact normalization basis")
        if edge_type == "oracle_candidate_dependency" and edge.get("evidence") != ORACLE_EVIDENCE:
            raise ExportError(f"Oracle edge {edge['id']} does not preserve exact candidate evidence")

    facet_nodes = [
        node for node in nodes
        if node.get("type") == "facet"
        and node.get("claim_id") == POLYTOPE_CLAIM_ID
        and node.get("facet_id") == POLYTOPE_FACET_ID
    ]
    if len(facet_nodes) != 1:
        raise ExportError("graph must contain exactly one selected polytope facet")
    expected_navigation = expected_polytope_navigation()
    expected_navigation_records = sorted(
        (
            link["target_ref"]["target_id"], link["relationship"], link["facet_coverage"],
            link["facet_id"], json.dumps(link["target_ref"], sort_keys=True),
        )
        for link in expected_navigation
    )
    actual_navigation_records = sorted(
        (
            edge["target"], edge.get("relationship"), edge.get("facet_coverage"),
            edge.get("facet_id"), json.dumps(edge.get("target_ref"), sort_keys=True),
        )
        for edge in edges
        if edge.get("type") == "provisional_navigation" and edge.get("source") == facet_nodes[0]["id"]
    )
    if actual_navigation_records != expected_navigation_records:
        raise ExportError("selected polytope facet navigation does not exactly match its Registry association")

    _, source_candidates, source_oracle_edges = load_oracle_subgraph()
    graph_candidates = {
        node.get("candidate_id"): node for node in nodes if node.get("type") == "oracle_candidate"
    }
    if set(graph_candidates) != set(source_candidates):
        raise ExportError("graph Oracle candidate node set does not match the selected source-DAG subgraph")
    expected_levels = oracle_layout_levels(source_candidates, source_oracle_edges)
    for candidate_id, source_record in source_candidates.items():
        graph_node = graph_candidates[candidate_id]
        if graph_node.get("candidate_record") != source_record:
            raise ExportError(f"Oracle candidate {candidate_id} does not preserve its source DAG record")
        if graph_node.get("source_status") != source_record.get("status"):
            raise ExportError(f"Oracle candidate {candidate_id} does not preserve source status")
        if graph_node.get("issue_badges") != source_record.get("issue_badges", []):
            raise ExportError(f"Oracle candidate {candidate_id} does not preserve structured issue badges")
        detail = graph_node["detail_markdown"]
        for issue in source_record.get("issue_badges", []):
            required_detail = [
                f"Object: **{issue['object']}**", f"Status: `{issue['status']}`",
                issue["interpretation"], *(f"`{badge}`" for badge in issue["badges"]),
            ]
            if any(value not in detail for value in required_detail):
                raise ExportError(f"Oracle candidate {candidate_id} does not render its structured issue metadata")
        if graph_node.get("layout_level") != expected_levels[candidate_id]:
            raise ExportError(f"Oracle candidate {candidate_id} does not preserve the source-derived topological layout")
    expected_oracle_edges = sorted(
        (
            edge["from"], edge["to"], edge["type"], edge["reason"], json.dumps(edge["evidence"], sort_keys=True),
        )
        for edge in source_oracle_edges
    )
    actual_oracle_edges = sorted(
        (
            edge["source"].removeprefix("oracle-candidate:"),
            edge["target"].removeprefix("oracle-candidate:"),
            edge.get("candidate_edge_type"), edge.get("reason"), json.dumps(edge.get("evidence"), sort_keys=True),
        )
        for edge in edges if edge.get("type") == "oracle_candidate_dependency"
    )
    if actual_oracle_edges != expected_oracle_edges:
        raise ExportError("Oracle candidate dependency edges do not exactly match the induced source-DAG subgraph")
    contained_candidates = {
        edge["target"].removeprefix("oracle-candidate:")
        for edge in edges if edge.get("type") == "oracle_contains" and edge.get("source") == ORACLE_SKELETON_ID
    }
    if contained_candidates != set(source_candidates):
        raise ExportError("Oracle skeleton containment does not exactly cover the selected candidate nodes")
    overlay_edges = [edge for edge in edges if edge.get("type") == "oracle_overlay"]
    if len(overlay_edges) != 1 or (overlay_edges[0]["source"], overlay_edges[0]["target"]) != (EXACT_POLYTOPE_MATH_ID, ORACLE_SKELETON_ID):
        raise ExportError("Oracle overlay is not attached exactly beneath the polytope-exactness MathClaimIR")

    initial = graph.get("initial_node_ids")
    expanded = graph.get("initial_expanded_node_ids")
    expected_initial = [node["id"] for node in nodes if node["type"] in {"paper", "scientific_claim_contribution"}]
    if initial != expected_initial:
        raise ExportError("graph initial state must contain only the paper and contribution-role ScientificClaims")
    paper_ids = [node["id"] for node in nodes if node["type"] == "paper"]
    if expanded != paper_ids:
        raise ExportError("graph initial expanded state must contain only the paper root")


def anchor_lines(formal: dict[str, Any], anchors: dict[str, dict[str, Any]]) -> list[str]:
    lines = []
    for anchor_id in formal["source_anchors"]:
        anchor = anchors.get(anchor_id)
        if anchor is None:
            lines.append(f"- `{anchor_id}` — **referenced anchor / Registry record missing**")
        else:
            location = anchor["location"]
            lines.append(f"- `{anchor_id}` — resolved SourceAnchor, lines `{location['line_start']}–{location['line_end']}`")
    return lines


def build_oracle_overlay(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], exact_math_id: str) -> None:
    _, dag_nodes, selected_edges = load_oracle_subgraph()
    skeleton_id = ORACLE_SKELETON_ID
    nodes.append({
        "id": skeleton_id,
        "type": "oracle_skeleton",
        "label": "ORACLE CANDIDATE PROOF SKELETON",
        "detail_markdown": "\n\n".join([
            "## ORACLE CANDIDATE PROOF SKELETON",
            "**UNVERIFIED overlay from the prototype claim DAG**",
            "- Source status: `ORACLE_PROPOSED`",
            "- Edge review: `UNREVIEWED_AT_EDGE_LEVEL`",
            "- Lean support: `NOT_EXTRACTED`",
            "- Disposition: `CANDIDATE`",
            "- SCIENTIFIC ACCEPTANCE: **UNKNOWN**",
            "- PROOF-DAG EDGE: **NOT ASSERTED AS ACCEPTED**",
            f"- Frozen DAG: `{CANDIDATE_DAG.relative_to(ROOT)}`",
            f"- File hash: `{file_hash(CANDIDATE_DAG)}`",
            "*Expanding this overlay shows an Oracle-proposed candidate chain, not accepted MathClaimIR dependencies.*",
        ]),
        "expandable": True,
        "unverified": True,
    })
    edges.append({
        "id": f"edge:oracle-overlay:{exact_math_id}",
        "source": exact_math_id,
        "target": skeleton_id,
        "expand_from": exact_math_id,
        "type": "oracle_overlay",
        "label": "OPTIONAL · UNVERIFIED ORACLE OVERLAY",
    })
    candidate_levels = oracle_layout_levels(dag_nodes, selected_edges)
    for candidate_id in sorted(ORACLE_NODE_IDS):
        record = dag_nodes[candidate_id]
        display_id = f"oracle-candidate:{candidate_id}"
        source = record.get("source") or {"anchor": record.get("anchor")}
        blockers = [record["status"]] if record.get("status") in {
            "BLOCKED_BY_ROOT_CONTRACT", "BLOCKED_BY_VREP_PROOF_GAP", "AGENT_EXPLICITATION_REQUIRES_PROOF_AUDIT",
            "LOCAL_DERIVATION_BLOCKED_BY_VREP_IMPORT",
        } else []
        issues = record.get("issue_badges", [])
        detail_parts = [
            "## Oracle candidate node",
            f"**{record['contract']}**",
            f"- Candidate ID: `{candidate_id}`",
            f"- Kind: `{record['kind']}`",
            f"- Source status: `{record['status']}`",
            "- Oracle status: `ORACLE_PROPOSED`",
            "- SCIENTIFIC ACCEPTANCE: **UNKNOWN**",
            "- PROOF-DAG EDGE: **NOT ASSERTED AS ACCEPTED**",
            "### Preserved source\n" + fenced(json.dumps(source, ensure_ascii=False, sort_keys=True, indent=2), "json"),
        ]
        if blockers:
            detail_parts.append("### Node blockers / audit status\n" + "\n".join(f"- `{blocker}`" for blocker in blockers))
        for issue in issues:
            detail_parts.append("\n".join([
                f"### Structured issue: {issue['object']}",
                f"- Object: **{issue['object']}**",
                f"- Status: `{issue['status']}`",
                "- Badges: " + ", ".join(f"`{badge}`" for badge in issue["badges"]),
                f"- Interpretation: {issue['interpretation']}",
            ]))
        nodes.append({
            "id": display_id,
            "candidate_id": candidate_id,
            "type": "oracle_candidate",
            "label": compact_label(candidate_id),
            "detail_markdown": "\n\n".join(detail_parts),
            "expandable": False,
            "source_status": record["status"],
            "issue_badges": issues,
            "candidate_record": record,
            "layout_level": candidate_levels[candidate_id],
            "unverified": True,
        })
        edges.append({
            "id": f"edge:oracle-contains:{candidate_id}",
            "source": skeleton_id,
            "target": display_id,
            "expand_from": skeleton_id,
            "type": "oracle_contains",
            "label": "UNVERIFIED CANDIDATE NODE",
        })
    for index, record in enumerate(selected_edges):
        edges.append({
            "id": f"edge:oracle-dependency:{index:02d}:{record['from']}:{record['to']}",
            "source": f"oracle-candidate:{record['from']}",
            "target": f"oracle-candidate:{record['to']}",
            "expand_from": skeleton_id,
            "type": "oracle_candidate_dependency",
            "label": f"CANDIDATE · {record['type']}",
            "candidate_edge_type": record["type"],
            "reason": record["reason"],
            "evidence": record["evidence"],
        })


def build_graph(exported_claims: list[dict[str, Any]], targets: dict[tuple[str, int], dict[str, Any]], paper: dict[str, Any]) -> dict[str, Any]:
    formal_by_id = unique_by(load_jsonl(FORMAL_CLAIMS), "id", "FORMAL_ATOMIC ScientificClaim")
    anchor_records = load_jsonl(SOURCE_ANCHORS)
    anchors = unique_by(anchor_records, "id", "SourceAnchor")
    for anchor in anchor_records:
        artifact = ROOT / anchor["artifact"]
        if anchor.get("artifact_hash") != file_hash(artifact):
            raise ExportError(f"SourceAnchor {anchor['id']} artifact hash mismatch")
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    paper_node_id = f"paper:{paper['id']}"
    nodes.append({
        "id": paper_node_id, "type": "paper", "label": paper["title"], "expandable": True,
        "detail_markdown": "\n\n".join(["## Paper", f"**{paper['title']}**", f"`{paper['id']}`", "### Authors\n" + "\n".join(f"- {a}" for a in paper["authors"]), f"### Frozen source\n`{paper['source_path']}`"]),
    })

    support_contexts: dict[tuple[str, int], list[dict[str, str]]] = {}
    support_refs: dict[tuple[str, int], dict[str, Any]] = {}
    facet_node_ids: dict[tuple[str, str], str] = {}
    for bundle in exported_claims:
        claim, calibration, association = bundle["claim"], bundle["calibration"], bundle["support_association"]
        claim_id = claim["id"]
        nodes.append({
            "id": claim_id, "type": "scientific_claim_contribution", "label": compact_label(claim_id), "expandable": True,
            "detail_markdown": "\n\n".join([
                "## Contribution-role ScientificClaim", f"**{compact_label(claim_id)}**", claim["normalized_statement"],
                f"`{claim_id}` · revision `{claim['record_revision']}`", "### Scope\n" + "\n".join(f"- {hint}" for hint in claim["scope_hints"]),
                "*Narrative root and claim-level source provenance only; this ScientificClaim is not a proof-DAG node.*",
            ]),
        })
        edges.append({"id": f"edge:paper:{claim_id}", "source": paper_node_id, "target": claim_id, "expand_from": paper_node_id, "type": "contains", "label": "CONTRIBUTION-ROLE SCIENTIFICCLAIM"})
        outcomes = {item["facet_id"]: item["coverage"] for item in association["facet_outcomes"]}
        for facet in claim["facets"]:
            facet_id = facet["facet_id"]
            node_id = f"graph-facet:{claim_id.rsplit(':', 1)[-1]}:{facet_id.rsplit(':', 1)[-1]}"
            facet_node_ids[(claim_id, facet_id)] = node_id
            coverage = outcomes[facet_id]
            nodes.append({
                "id": node_id, "type": "facet", "label": compact_label(facet_id), "expandable": True,
                "claim_id": claim_id, "facet_id": facet_id,
                "detail_markdown": "\n\n".join([
                    "## Facet", f"**{facet['statement']}**", f"- Facet ID: `{facet_id}`", f"- Kind: `{facet['facet_kind']}`",
                    f"- NAVIGATION COVERAGE: **{coverage}**", "- SCIENTIFIC ACCEPTANCE: **UNKNOWN**", "- PROOF-DAG EDGE: **NOT ASSERTED**",
                    "*Navigation coverage routes Registry inspection. It is not proof completeness or scientific verification.*",
                ]),
            })
            edges.append({"id": f"edge:facet:{claim_id}:{facet_id}", "source": claim_id, "target": node_id, "expand_from": claim_id, "type": "has_facet", "label": "HAS FACET"})
        for occurrence in claim["occurrences"]:
            role = occurrence["occurrence_role"]
            relation = calibration.get("primary_to_normalized_relation") if role == "PRIMARY" else calibration.get("body_to_normalized_relation") if role == "BODY_SUPPORT" else None
            nodes.append({
                "id": occurrence["id"], "type": "source_occurrence", "label": f"{role.title().replace('_', ' ')} · lines {occurrence['line_start']}–{occurrence['line_end']}", "expandable": False, "claim_id": claim_id,
                "detail_markdown": "\n\n".join([
                    "## Claim-level source occurrence", f"**{role}** · `{occurrence['source_zone']}`",
                    "\n".join([f"- Occurrence: `{occurrence['id']}`", f"- Source: `{occurrence['source_artifact']['path']}`", f"- Lines: `{occurrence['line_start']}–{occurrence['line_end']}`", f"- Calibration: `{relation or 'SOURCE OCCURRENCE'}`"]),
                    "- PROOF-DAG EDGE: **NOT ASSERTED**", "### Verbatim excerpt\n" + fenced(occurrence["source_text"], "latex"),
                ]),
            })
            edges.append({"id": f"edge:occurrence:{claim_id}:{occurrence['id']}", "source": claim_id, "target": occurrence["id"], "expand_from": claim_id, "type": "source_calibration", "label": f"{role} · {relation or 'SOURCE OCCURRENCE'}", "calibration_id": calibration["id"], "relation_direction": calibration["relation_direction"]})
        for link in association["links"]:
            reference = link["target_ref"]
            key = (reference["target_id"], reference["target_revision"])
            support_refs[key] = reference
            support_contexts.setdefault(key, []).append({"claim_id": claim_id, "facet_id": link["facet_id"], "relationship": link["relationship"], "facet_coverage": link["facet_coverage"]})

    formal_added: set[str] = set()
    exact_math_id = EXACT_POLYTOPE_MATH_ID
    for key in sorted(support_contexts):
        target, reference, contexts = targets[key], support_refs[key], support_contexts[key]
        node_type = "math_claim_ir" if reference["target_kind"] == "org.agtxiv.claim_ir" else "mathematical_proposition_ir"
        statement = target.get("normalized_statement_expanded_latex") or target.get("text") or target.get("statement") or "No display statement recorded."
        node_detail = [
            f"## {'MathClaimIR' if node_type == 'math_claim_ir' else 'MathematicalPropositionIR'}", f"**{compact_label(target['id'])}**",
            f"- Target ID: `{target['id']}`", f"- Revision: `{target['revision']}`", "- SCIENTIFIC ACCEPTANCE: **UNKNOWN**", "- PROOF-DAG EDGE: **NOT ASSERTED**",
            "### Mathematical statement\n" + fenced(str(statement), "latex"),
            "### Registry navigation\n" + "\n".join(f"- `{c['facet_id']}` · `{c['relationship']}` · NAVIGATION COVERAGE: **{c['facet_coverage']}**" for c in contexts),
            "### Exact artifact\n" + fenced(json.dumps(reference["target_artifact"], ensure_ascii=False, sort_keys=True, indent=2), "json"),
            "*This normalized object is proof-DAG eligible, but these Registry links assert navigation only.*",
        ]
        nodes.append({"id": target["id"], "type": node_type, "label": compact_label(target["id"]), "detail_markdown": "\n\n".join(node_detail), "expandable": node_type == "math_claim_ir", "revision": target["revision"]})
        for context in contexts:
            facet_node_id = facet_node_ids[(context["claim_id"], context["facet_id"])]
            edges.append({"id": f"edge:support:{facet_node_id}:{target['id']}", "source": facet_node_id, "target": target["id"], "expand_from": facet_node_id, "type": "provisional_navigation", "label": f"PROVISIONAL NAVIGATION · {context['facet_coverage']}", "relationship": context["relationship"], "facet_coverage": context["facet_coverage"], "facet_id": context["facet_id"], "target_ref": reference})
        if node_type == "math_claim_ir":
            formal_ref = target.get("claim")
            formal = formal_by_id.get(formal_ref.get("id") if isinstance(formal_ref, dict) else None)
            if formal is None or (formal_ref.get("record_revision"), formal_ref.get("content_hash")) != (formal["record_revision"], formal["content_hash"]):
                raise ExportError(f"MathClaimIR {target['id']} has invalid FORMAL_ATOMIC ScientificClaim identity")
            if formal["id"] not in formal_added:
                formal_added.add(formal["id"])
                nodes.append({
                    "id": formal["id"], "type": "scientific_claim_formal", "label": compact_label(formal["id"]), "expandable": False,
                    "detail_markdown": "\n\n".join([
                        "## Immutable FORMAL_ATOMIC ScientificClaim identity", f"**{formal['text']}**", f"- ID: `{formal['id']}`", f"- Revision: `{formal['record_revision']}`", f"- Content hash: `{formal['content_hash']}`",
                        "### Source-anchor resolution\n" + "\n".join(anchor_lines(formal, anchors)),
                        "- SCIENTIFIC ACCEPTANCE: **UNKNOWN**", "- PROOF-DAG EDGE: **NOT ASSERTED**",
                        "*This is the exact identity normalized by its MathClaimIR, not a proof dependency or contribution-source edge.*",
                    ]),
                })
            edges.append({"id": f"edge:identity:{target['id']}:{formal['id']}", "source": target["id"], "target": formal["id"], "expand_from": target["id"], "type": "normalizes_identity", "label": "NORMALIZES IMMUTABLE IDENTITY", "basis": "Exact MathClaimIR.claim immutable reference"})

    if exact_math_id not in {node["id"] for node in nodes}:
        raise ExportError("polytope exactness MathClaimIR is missing from Registry navigation")
    build_oracle_overlay(nodes, edges, exact_math_id)
    graph = {"nodes": nodes, "edges": edges, "initial_node_ids": [n["id"] for n in nodes if n["type"] in {"paper", "scientific_claim_contribution"}], "initial_expanded_node_ids": [paper_node_id]}
    validate_graph(graph)
    return graph

def build_demo_data() -> dict[str, Any]:
    all_claims = load_jsonl(CLAIMS)
    unique_by(all_claims, "id", "ScientificClaim")
    claims = [record for record in all_claims if record.get("paper_id") == PAPER_ID]
    if len(claims) != 2:
        raise ExportError(f"expected exactly two contribution-role ScientificClaims for {PAPER_ID}, found {len(claims)}")
    if any(record.get("claim_role") != "CONTRIBUTION" for record in claims):
        raise ExportError(f"all selected ScientificClaims must have claim_role CONTRIBUTION")
    claims.sort(key=lambda record: record["id"])
    validate_occurrences(claims)

    calibrations = load_jsonl(CALIBRATIONS)
    support_records = load_jsonl(SUPPORT)
    unique_by(calibrations, "id", "calibration")
    unique_by(support_records, "id", "support association")
    selected_ids = {claim["id"] for claim in claims}
    calibration_by_claim: dict[str, dict[str, Any]] = {}
    support_by_claim: dict[str, dict[str, Any]] = {}

    for label, records, indexed in (
        ("calibration", calibrations, calibration_by_claim),
        ("support association", support_records, support_by_claim),
    ):
        for record in records:
            reference = record.get("scientific_claim_ref")
            claim_id = reference.get("target_id") if isinstance(reference, dict) else None
            if claim_id not in selected_ids:
                continue
            if claim_id in indexed:
                raise ExportError(f"duplicate {label} for {claim_id}")
            indexed[claim_id] = record

    targets = load_support_targets()
    exported_claims: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = claim["id"]
        calibration = calibration_by_claim.get(claim_id)
        association = support_by_claim.get(claim_id)
        if calibration is None or association is None:
            raise ExportError(f"missing calibration or support association for {claim_id}")
        assert_claim_ref(calibration.get("scientific_claim_ref"), claim, calibration["id"])
        assert_claim_ref(association.get("scientific_claim_ref"), claim, association["id"])
        assert_claim_ref(association.get("navigation_basis_ref"), claim, association["id"], "/facets")
        if calibration.get("record_revision") != claim["record_revision"]:
            raise ExportError(f"calibration revision does not match {claim_id}")
        if calibration.get("relation_direction") != "SOURCE_RELATIVE_TO_NORMALIZED_CLAIM":
            raise ExportError(f"calibration direction does not match {claim_id}")
        if association.get("record_revision") != claim["record_revision"]:
            raise ExportError(f"support revision does not match {claim_id}")

        facets = claim.get("facets")
        if not isinstance(facets, list) or not facets:
            raise ExportError(f"{claim_id} has no facets")
        facet_ids = [facet.get("facet_id") for facet in facets if isinstance(facet, dict)]
        if len(facet_ids) != len(facets) or len(set(facet_ids)) != len(facet_ids):
            raise ExportError(f"{claim_id} has missing or duplicate facet IDs")
        outcomes = association.get("facet_outcomes")
        if not isinstance(outcomes, list):
            raise ExportError(f"{association['id']} has no facet outcomes")
        outcome_ids = [outcome.get("facet_id") for outcome in outcomes if isinstance(outcome, dict)]
        if len(outcome_ids) != len(outcomes) or sorted(outcome_ids) != sorted(facet_ids):
            raise ExportError(f"{association['id']} does not map every facet exactly once")

        linked_facets: set[str] = set()
        links = association.get("links")
        if not isinstance(links, list) or not links:
            raise ExportError(f"{association['id']} has no support links")
        for index, link in enumerate(links):
            if not isinstance(link, dict) or link.get("facet_id") not in facet_ids:
                raise ExportError(f"{association['id']} link {index} has a dangling facet")
            linked_facets.add(link["facet_id"])
            assert_support_ref(link.get("target_ref"), targets, f"{association['id']} link {index}")
        if linked_facets != set(facet_ids):
            raise ExportError(f"{association['id']} has a facet without a support link")

        exported_claims.append({
            "calibration": calibration,
            "claim": claim,
            "support_association": association,
        })

    paper = {
        "authors": ["Yingjian Liu", "Albert Gasull", "Mengyao Hu", "Ruiyun Zhang", "Flavio Baccari", "Jordi Tura"],
        "id": PAPER_ID,
        "source_path": "Stabilizerness/arXiv-2607.26154v1/draft.tex",
        "title": "Graph Theoretic Approach to Quantum Nonstabilizerness",
    }
    graph = build_graph(exported_claims, targets, paper)
    return {
        "architecture": {
            "calibration_direction": {
                "code": "SOURCE_RELATIVE_TO_NORMALIZED_CLAIM",
                "explanation": "Each relation describes the source occurrence relative to the normalized ScientificClaim: BROADER_THAN means the source says more; CONSERVATIVE_PARAPHRASE means the normalized claim stays within the source; PARTIAL_OVERLAP means only part aligns.",
            },
            "layers": [
                {
                    "id": "scientific-claim",
                    "label": "ScientificClaim",
                    "description": "CONTRIBUTION-role narrative and navigation identity; it is not a node in the mathematical proof DAG.",
                },
                {
                    "id": "facet-evidence",
                    "label": "Claim-level source provenance",
                    "description": "Facets route navigation to immutable occurrences, source characterization, and calibration records.",
                },
                {
                    "id": "mathematical-dag",
                    "label": "Mathematical support targets",
                    "description": "Normalized MathClaimIR and MathematicalPropositionIR objects are proof-DAG eligible; Registry links do not assert dependencies.",
                },
            ],
            "verification_boundary": {
                "available": "Provisional facet coverage is immutable navigation support from the current source audit.",
                "pending": [
                    "Query-specific PaperTheoryDelta construction",
                    "Final QueryResolution coverage",
                    "Viewer integration",
                ],
            },
        },
        "claims": exported_claims,
        "graph": graph,
        "paper": paper,
        "schema": "agtxiv.scientific-claim-demo/3.0.0",
        "source_revision": "2d9b1b7",
    }


def serialize(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT, help="output JSON path")
    parser.add_argument("--check", action="store_true", help="fail if the output differs instead of writing")
    args = parser.parse_args()
    content = serialize(build_demo_data())
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check:
        try:
            current = output.read_text(encoding="utf-8")
        except OSError as error:
            raise SystemExit(f"cannot check {output}: {error}") from error
        if current != content:
            raise SystemExit(f"generated output differs: run {Path(__file__).relative_to(ROOT)}")
        print(f"ScientificClaim demo data is current: {output.relative_to(ROOT)}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Exported 2 ScientificClaims to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
