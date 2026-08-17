#!/usr/bin/env python3
"""Validate the claim-level DAG for the Stabilizerness paper."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from pathlib import Path


DEFAULT_DAG = Path("Stabilizerness/dag/claim-dag.json")


def validate(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    errors: list[str] = []

    if data.get("graph_view") != "ORACLE_CANDIDATE":
        errors.append("graph_view must explicitly remain ORACLE_CANDIDATE")

    ids = [node.get("id") for node in nodes]
    duplicate_ids = sorted(key for key, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"duplicate node ids: {duplicate_ids}")

    node_by_id = {node.get("id"): node for node in nodes}
    allowed_kinds = set(data.get("node_kinds", []))
    allowed_edges = set(data.get("edge_types", {}))
    for node in nodes:
        node_id = node.get("id")
        for field in ("id", "layer", "branch", "kind", "label_zh", "contract", "status"):
            if field not in node:
                errors.append(f"{node_id}: missing field {field}")
        if node.get("kind") not in allowed_kinds:
            errors.append(f"{node_id}: unknown kind {node.get('kind')}")

    adjacency: dict[str, list[str]] = defaultdict(list)
    indegree = {node_id: 0 for node_id in node_by_id}
    edge_keys: Counter[tuple[str, str, str]] = Counter()
    for index, edge in enumerate(edges):
        source = edge.get("from")
        target = edge.get("to")
        edge_type = edge.get("type")
        if source not in node_by_id:
            errors.append(f"edge {index}: unknown source {source}")
            continue
        if target not in node_by_id:
            errors.append(f"edge {index}: unknown target {target}")
            continue
        if edge_type not in allowed_edges:
            errors.append(f"edge {index}: unknown type {edge_type}")
        evidence = edge.get("evidence")
        if not evidence:
            errors.append(f"edge {index}: missing evidence state")
        else:
            if evidence.get("oracle_status") != "ORACLE_PROPOSED":
                errors.append(f"edge {index}: Oracle provenance was not preserved")
            if evidence.get("disposition") not in {
                "CANDIDATE",
                "ACCEPTED",
                "CONDITIONAL",
                "REJECTED",
                "REDUNDANT_IN_QUERY_VIEW",
                "BLOCKED",
                "DISPUTED",
            }:
                errors.append(f"edge {index}: invalid evidence disposition")
            if not evidence.get("source_alignment") or not evidence.get("lean_support"):
                errors.append(f"edge {index}: incomplete evidence axes")
        if source == target:
            errors.append(f"edge {index}: self-loop at {source}")
        edge_keys[(source, target, edge_type)] += 1
        adjacency[source].append(target)
        indegree[target] += 1

    duplicate_edges = sorted(key for key, count in edge_keys.items() if count > 1)
    if duplicate_edges:
        errors.append(f"duplicate typed edges: {duplicate_edges}")

    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    order: list[str] = []
    work_indegree = dict(indegree)
    while queue:
        node_id = queue.popleft()
        order.append(node_id)
        for target in adjacency[node_id]:
            work_indegree[target] -= 1
            if work_indegree[target] == 0:
                queue.append(target)
    if len(order) != len(nodes):
        cycle_nodes = sorted(node_id for node_id, degree in work_indegree.items() if degree > 0)
        errors.append(f"cycle detected among: {cycle_nodes}")

    roots = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    scientific_roots = [
        node_id
        for node_id in roots
        if node_by_id[node_id].get("kind") in {"external_contract", "standard_foundation"}
    ]
    data_inputs = [
        node_id for node_id in roots if node_by_id[node_id].get("kind") == "empirical_protocol"
    ]
    branches = Counter(node.get("branch") for node in nodes)
    statuses = Counter(node.get("status") for node in nodes)

    return {
        "ok": not errors,
        "path": str(path),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "branch_counts": dict(sorted(branches.items())),
        "scientific_roots": scientific_roots,
        "data_input_roots": data_inputs,
        "false_or_blocked_nodes": sorted(
            node_id
            for node_id, node in node_by_id.items()
            if "FALSE" in str(node.get("status")) or "BLOCK" in str(node.get("status"))
        ),
        "status_counts": dict(sorted(statuses.items())),
        "topological_order": order,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_DAG)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = validate(args.path)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"claim DAG: {'PASS' if result['ok'] else 'FAIL'}")
        print(f"nodes={result['node_count']} edges={result['edge_count']}")
        print("scientific roots:")
        for root in result["scientific_roots"]:
            print(f"  - {root}")
        if result["data_input_roots"]:
            print("unfrozen data-input roots:")
            for root in result["data_input_roots"]:
                print(f"  - {root}")
        if result["false_or_blocked_nodes"]:
            print("false/blocked nodes:")
            for node in result["false_or_blocked_nodes"]:
                print(f"  - {node}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
