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
CLAIMS = ROOT / "Stabilizerness/ScientificClaimRegistry/claims/contribution-role-scientific-claims.jsonl"
CALIBRATIONS = ROOT / "Stabilizerness/ExternalRecordRegistry/scientific-claim-calibrations/scientific-claim-calibrations.jsonl"
SUPPORT = ROOT / "Stabilizerness/ExternalRecordRegistry/claim-support-associations/scientific-claim-support.jsonl"
MATH_MANIFEST = ROOT / "Stabilizerness/MathClaimIRRegistry/manifest.json"
EXTERNAL_MANIFEST = ROOT / "Stabilizerness/ExternalRecordRegistry/manifest.json"
FORMAL_CLAIMS = ROOT / "Stabilizerness/ScientificClaimRegistry/claims/graph-theoretic-nonstabilizerness.jsonl"
OUTPUT = ROOT / "demo_design/scientific_claims/data/graph-theoretic-scientific-claims.json"
GRAPH_NODE_TYPES = {
    "paper", "scientific_claim_contribution", "facet", "scientific_claim_formal",
    "source_occurrence", "math_claim_ir", "mathematical_proposition_ir",
}
GRAPH_EDGE_TYPES = {"contains", "has_facet", "source_calibration", "formal_source", "provisional_navigation"}
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


def validate_graph(graph: dict[str, Any]) -> None:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ExportError("graph payload must contain node and edge arrays")
    node_by_id = unique_by(nodes, "id", "graph node")
    unique_by(edges, "id", "graph edge")
    prefixes = {
        "paper": "paper:",
        "scientific_claim_contribution": "claim:",
        "facet": "graph-facet:",
        "scientific_claim_formal": "claim:",
        "source_occurrence": "occurrence:",
        "math_claim_ir": "math-claim-ir:",
        "mathematical_proposition_ir": "math-proposition-ir:",
    }
    for node in nodes:
        node_type = node.get("type")
        if node_type not in GRAPH_NODE_TYPES:
            raise ExportError(f"graph node {node.get('id')} has unsupported type {node_type!r}")
        if not str(node["id"]).startswith(prefixes[node_type]):
            raise ExportError(f"graph node type {node_type} does not match ID {node['id']}")
        if not isinstance(node.get("label"), str) or not node["label"].strip():
            raise ExportError(f"graph node {node['id']} has no label")
        validate_markdown_detail(node.get("detail_markdown"), node["id"])
    endpoint_types = {
        "contains": ({"paper"}, {"scientific_claim_contribution"}),
        "has_facet": ({"scientific_claim_contribution"}, {"facet"}),
        "source_calibration": ({"scientific_claim_contribution"}, {"source_occurrence"}),
        "formal_source": ({"scientific_claim_contribution"}, {"scientific_claim_formal"}),
        "provisional_navigation": ({"facet"}, {"math_claim_ir", "mathematical_proposition_ir"}),
    }
    for edge in edges:
        edge_type = edge.get("type")
        if edge_type not in GRAPH_EDGE_TYPES:
            raise ExportError(f"graph edge {edge.get('id')} has unsupported type")
        if edge.get("source") not in node_by_id or edge.get("target") not in node_by_id:
            raise ExportError(f"graph edge {edge.get('id')} has a dangling endpoint")
        if edge.get("expand_from") != edge.get("source"):
            raise ExportError(f"graph edge {edge.get('id')} must expand from its source")
        source_types, target_types = endpoint_types[edge_type]
        if node_by_id[edge["source"]]["type"] not in source_types or node_by_id[edge["target"]]["type"] not in target_types:
            raise ExportError(f"graph edge {edge['id']} has endpoint types invalid for {edge_type}")
        if edge_type == "provisional_navigation":
            if not str(edge.get("label", "")).startswith("PROVISIONAL NAVIGATION · "):
                raise ExportError(f"mathematical navigation edge {edge['id']} has misleading status text")
    initial = graph.get("initial_node_ids")
    expanded = graph.get("initial_expanded_node_ids")
    expected_initial = [node["id"] for node in nodes if node["type"] in {"paper", "scientific_claim_contribution"}]
    if initial != expected_initial:
        raise ExportError("graph initial state must contain only the paper and contribution-role ScientificClaims")
    paper_ids = [node["id"] for node in nodes if node["type"] == "paper"]
    if expanded != paper_ids:
        raise ExportError("graph initial expanded state must contain only the paper root")


def build_graph(exported_claims: list[dict[str, Any]], targets: dict[tuple[str, int], dict[str, Any]], paper: dict[str, Any]) -> dict[str, Any]:
    formal_by_id = unique_by(load_jsonl(FORMAL_CLAIMS), "id", "FORMAL_ATOMIC ScientificClaim")
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    paper_node_id = f"paper:{paper['id']}"
    paper_detail = "\n\n".join([
        "## Paper",
        f"**{paper['title']}**",
        f"`{paper['id']}`",
        "### Authors\n" + "\n".join(f"- {author}" for author in paper["authors"]),
        f"### Frozen source\n`{paper['source_path']}`",
    ])
    nodes.append({
        "id": paper_node_id,
        "type": "paper",
        "label": paper["title"],
        "detail_markdown": paper_detail,
        "expandable": True,
    })

    support_contexts: dict[tuple[str, int], list[dict[str, str]]] = {}
    support_refs: dict[tuple[str, int], dict[str, Any]] = {}
    formal_sources: dict[str, dict[str, dict[str, Any]]] = {}
    facet_node_ids: dict[tuple[str, str], str] = {}

    for bundle in exported_claims:
        claim = bundle["claim"]
        calibration = bundle["calibration"]
        association = bundle["support_association"]
        claim_id = claim["id"]
        claim_detail = "\n\n".join([
            "## Contribution-role ScientificClaim",
            f"**{compact_label(claim_id)}**",
            claim["normalized_statement"],
            f"`{claim_id}` · revision `{claim['record_revision']}`",
            "### Scope\n" + "\n".join(f"- {hint}" for hint in claim["scope_hints"]),
            "### Immutable identity\n" + "\n".join([
                f"- Semantic: `{claim['semantic_content_hash']}`",
                f"- Artifact: `{claim['artifact']['artifact_hash']}`",
                f"- Content: `{claim['content_hash']}`",
            ]),
            "*Narrative/source navigation only; this ScientificClaim is not a mathematical proof-DAG node.*",
        ])
        nodes.append({
            "id": claim_id,
            "type": "scientific_claim_contribution",
            "label": compact_label(claim_id),
            "detail_markdown": claim_detail,
            "expandable": True,
        })
        edges.append({
            "id": f"edge:paper:{claim_id}",
            "source": paper_node_id,
            "target": claim_id,
            "expand_from": paper_node_id,
            "type": "contains",
            "label": "CONTRIBUTION-ROLE SCIENTIFICCLAIM",
        })

        outcomes = {outcome["facet_id"]: outcome["coverage"] for outcome in association["facet_outcomes"]}
        for facet in claim["facets"]:
            facet_id = facet["facet_id"]
            node_id = f"graph-facet:{claim_id.rsplit(':', 1)[-1]}:{facet_id.rsplit(':', 1)[-1]}"
            facet_node_ids[(claim_id, facet_id)] = node_id
            outcome = outcomes[facet_id]
            detail = "\n\n".join([
                "## Facet",
                f"**{facet['statement']}**",
                f"- Facet ID: `{facet_id}`",
                f"- Kind: `{facet['facet_kind']}`",
                f"- Provisional facet navigation: **{outcome.lower()}**",
                "*This outcome routes inspection; it is not final query coverage or verification.*",
            ])
            nodes.append({
                "id": node_id,
                "type": "facet",
                "label": compact_label(facet_id),
                "detail_markdown": detail,
                "expandable": True,
                "claim_id": claim_id,
                "facet_id": facet_id,
            })
            edges.append({
                "id": f"edge:facet:{claim_id}:{facet_id}",
                "source": claim_id,
                "target": node_id,
                "expand_from": claim_id,
                "type": "has_facet",
                "label": "HAS FACET",
            })

        for occurrence in claim["occurrences"]:
            role = occurrence["occurrence_role"]
            if role == "PRIMARY":
                relation = calibration["primary_to_normalized_relation"]
            elif role == "BODY_SUPPORT":
                relation = calibration["body_to_normalized_relation"]
            else:
                relation = None
            relation_line = f"- Calibration: `{relation}`" if relation else "- Calibration: occurrence role only; no finer relation is asserted"
            detail = "\n\n".join([
                "## Source occurrence",
                f"**{role}** · `{occurrence['source_zone']}`",
                "\n".join([
                    f"- Occurrence: `{occurrence['id']}`",
                    f"- Source: `{occurrence['source_artifact']['path']}`",
                    f"- Lines: `{occurrence['line_start']}–{occurrence['line_end']}`",
                    f"- Speech act: `{occurrence['source_characterization']['speech_act']}`",
                    f"- Formality: `{occurrence['source_characterization']['formality']}`",
                    f"- Conditionality: `{occurrence['source_characterization']['conditionality']}`",
                    relation_line,
                ]),
                "### Verbatim excerpt\n" + fenced(occurrence["source_text"], "latex"),
            ])
            nodes.append({
                "id": occurrence["id"],
                "type": "source_occurrence",
                "label": f"{role.title().replace('_', ' ')} · lines {occurrence['line_start']}–{occurrence['line_end']}",
                "detail_markdown": detail,
                "expandable": False,
                "claim_id": claim_id,
            })
            edges.append({
                "id": f"edge:occurrence:{claim_id}:{occurrence['id']}",
                "source": claim_id,
                "target": occurrence["id"],
                "expand_from": claim_id,
                "type": "source_calibration",
                "label": f"{role} · {relation or 'SOURCE OCCURRENCE'}",
                "calibration_id": calibration["id"],
                "relation_direction": calibration["relation_direction"],
            })

        for link in association["links"]:
            reference = link["target_ref"]
            key = (reference["target_id"], reference["target_revision"])
            support_refs[key] = reference
            support_contexts.setdefault(key, []).append({
                "claim_id": claim_id,
                "facet_id": link["facet_id"],
                "relationship": link["relationship"],
                "facet_coverage": link["facet_coverage"],
            })
            target = targets[key]
            formal_ref = target.get("claim") if reference["target_kind"] == "org.agtxiv.claim_ir" else None
            if isinstance(formal_ref, dict):
                formal = formal_by_id.get(formal_ref.get("id"))
                if formal is None:
                    raise ExportError(f"MathClaimIR {target['id']} has dangling FORMAL_ATOMIC ScientificClaim {formal_ref.get('id')}")
                expected = (formal["record_revision"], formal["content_hash"])
                actual = (formal_ref.get("record_revision"), formal_ref.get("content_hash"))
                if actual != expected:
                    raise ExportError(f"MathClaimIR {target['id']} has mismatched FORMAL_ATOMIC ScientificClaim identity")
                formal_sources.setdefault(claim_id, {})[formal["id"]] = formal

    for claim_id, formal_records in formal_sources.items():
        for formal in sorted(formal_records.values(), key=lambda record: record["id"]):
            detail = "\n\n".join([
                "## FORMAL_ATOMIC ScientificClaim",
                f"**{formal['text']}**",
                "\n".join([
                    f"- ID: `{formal['id']}`",
                    f"- Kind: `{formal['kind']}`",
                    f"- Origin: `{formal['origin']}`",
                    f"- Revision: `{formal['record_revision']}`",
                    f"- Content hash: `{formal['content_hash']}`",
                ]),
                "### Source anchors\n" + "\n".join(f"- `{anchor}`" for anchor in formal["source_anchors"]),
                "*Included because a displayed MathClaimIR carries this exact immutable ScientificClaim identity; no occurrence-level edge is guessed.*",
            ])
            nodes.append({
                "id": formal["id"],
                "type": "scientific_claim_formal",
                "label": compact_label(formal["id"]),
                "detail_markdown": detail,
                "expandable": False,
                "claim_id": claim_id,
            })
            edges.append({
                "id": f"edge:formal:{claim_id}:{formal['id']}",
                "source": claim_id,
                "target": formal["id"],
                "expand_from": claim_id,
                "type": "formal_source",
                "label": "FORMAL_ATOMIC SOURCE IDENTITY",
                "basis": "Exact MathClaimIR.claim immutable reference",
            })

    for key in sorted(support_contexts):
        target = targets[key]
        reference = support_refs[key]
        contexts = support_contexts[key]
        node_type = "math_claim_ir" if reference["target_kind"] == "org.agtxiv.claim_ir" else "mathematical_proposition_ir"
        statement = target.get("normalized_statement_expanded_latex") or target.get("text") or target.get("statement") or "No display statement recorded."
        detail = "\n\n".join([
            f"## {'MathClaimIR' if node_type == 'math_claim_ir' else 'MathematicalPropositionIR'}",
            f"**{compact_label(target['id'])}**",
            "\n".join([
                f"- Target ID: `{target['id']}`",
                f"- Revision: `{target['revision']}`",
                f"- Semantic hash: `{target['semantic_content_hash']}`",
                f"- Artifact hash: `{target['artifact']['artifact_hash']}`",
            ]),
            "### Mathematical statement\n" + fenced(str(statement), "latex"),
            "### Provisional navigation associations\n" + "\n".join(
                f"- `{context['facet_id']}` · `{context['relationship']}` · **{context['facet_coverage'].lower()}**"
                for context in contexts
            ),
            "### Exact artifact\n" + fenced(json.dumps(reference["target_artifact"], ensure_ascii=False, sort_keys=True, indent=2), "json"),
            "*Eligible for the mathematical proof-DAG layer; these links still do not assert final query coverage or verification.*",
        ])
        nodes.append({
            "id": target["id"],
            "type": node_type,
            "label": compact_label(target["id"]),
            "detail_markdown": detail,
            "expandable": False,
            "revision": target["revision"],
        })
        for context in contexts:
            facet_node_id = facet_node_ids[(context["claim_id"], context["facet_id"])]
            edges.append({
                "id": f"edge:support:{facet_node_id}:{target['id']}",
                "source": facet_node_id,
                "target": target["id"],
                "expand_from": facet_node_id,
                "type": "provisional_navigation",
                "label": f"PROVISIONAL NAVIGATION · {context['facet_coverage']}",
                "relationship": context["relationship"],
                "facet_id": context["facet_id"],
                "target_ref": reference,
            })

    graph = {
        "nodes": nodes,
        "edges": edges,
        "initial_node_ids": [node["id"] for node in nodes if node["type"] in {"paper", "scientific_claim_contribution"}],
        "initial_expanded_node_ids": [paper_node_id],
    }
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
                    "label": "Facets + source audit",
                    "description": "Facets route navigation to immutable occurrences, source characterization, and calibration records.",
                },
                {
                    "id": "mathematical-dag",
                    "label": "Mathematical support targets",
                    "description": "MathClaimIR and MathematicalPropositionIR records may enter the mathematical dependency DAG.",
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
        "schema": "agtxiv.scientific-claim-demo/2.0.0",
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
