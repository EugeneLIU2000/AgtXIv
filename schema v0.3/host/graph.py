"""Deterministic candidate support-graph selection, with no model-owned state.

The public boundary accepts *host-derived* nodes and support groups. A group is a
joint premise (AND); groups with the same target are alternatives (OR). Costs are
paid once per selected node/group, including shared prerequisites. This module
never promotes a claim or infers that a mathematical dependency is justified.
"""

from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import json


SUPPORT_RELATIONS = frozenset({
    "DEFINITION_DEPENDENCY", "SCIENTIFIC_CLAIM_DEPENDENCY", "SCOPE_DEPENDENCY",
    "PROOF_DEPENDENCY", "BRIDGING_DEPENDENCY",
})
# A deliberately conservative review order, not a probability or proof score.
DISPOSITIONS = (
    "SOURCE_READ_DEFECTIVE", "SOURCE_UNREACHABLE", "BLOCKED",
    "ROUTE_UNDETERMINED", "NOT_COMPOSED", "DOMAIN_WIDENED", "DOMAIN_NARROWED",
    "KERNEL_CHECKED_VACUITY_UNKNOWN", "UNREVIEWED", "CANDIDATE",
    "AGENT_NORMALIZED_UNREVIEWED", "DEFINITION_ELABORATED", "KERNEL_CHECKED",
    "SOURCE_FROZEN_HUMAN_SIGNED", "HUMAN_ACCEPTED",
)
_RANK = {value: index for index, value in enumerate(DISPOSITIONS)}
_DERIVED_KEYS = frozenset({
    "state", "included_by", "weakest_disposition_on_path", "formalization_state",
    "coverage", "selected", "derived_state", "effective_disposition",
})
MAX_SEARCH_STATES = 100_000
MAX_TIED_ROUTES = 2_048
_THEOREM_KINDS = frozenset({"theorem", "lemma", "proposition", "corollary"})
GRAPH_FORMATS = (None, "COMPACT_V1")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode()).hexdigest()


def _weakest(values):
    return min(values, key=lambda item: (_RANK[item], item), default="CANDIDATE")


def _identifier(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _money(record, key, default=None):
    value = record.get(key, default)
    if value is not None and (type(value) is not int or value < 0):
        raise ValueError(f"{record['id']}.{key} must be a nonnegative integer")
    return value


def _normalize(nodes, support_groups, query_ids):
    node_map, group_map = {}, {}
    for original in nodes:
        if not isinstance(original, dict):
            raise ValueError("nodes must be objects")
        record = dict(original)
        node_id = _identifier(record.get("id"), "node.id")
        if node_id in node_map:
            raise ValueError(f"duplicate node: {node_id}")
        if _DERIVED_KEYS.intersection(record):
            raise ValueError(f"{node_id}: graph-derived fields cannot be inputs")
        record["kind"] = _identifier(record.get("kind"), f"{node_id}.kind")
        record["disposition"] = record.get("disposition", "CANDIDATE")
        if record["disposition"] not in _RANK:
            raise ValueError(f"{node_id}: unknown disposition")
        blockers = record.get("blocked_by", [])
        if not isinstance(blockers, list) or any(not isinstance(x, str) or not x for x in blockers):
            raise ValueError(f"{node_id}.blocked_by must be an identifier array")
        record["blocked_by"] = sorted(set(blockers))
        bridges = record.get("bridging_claims", [])
        if not isinstance(bridges, list) or any(not isinstance(x, str) or not x for x in bridges):
            raise ValueError(f"{node_id}.bridging_claims must be an identifier array")
        record["bridging_claims"] = sorted(set(bridges))
        record["cost_microusd"] = _money(record, "cost_microusd")
        record["cost_error_microusd"] = _money(record, "cost_error_microusd", 0)
        if record["cost_error_microusd"] is None:
            raise ValueError(f"{node_id}.cost_error_microusd cannot be null")
        for field in ("statement_discharged", "proof_discharged"):
            if field in record and type(record[field]) is not bool:
                raise ValueError(f"{node_id}.{field} must be boolean")
        if record["kind"].lower() == "definition" and record.get("proof_discharged"):
            raise ValueError(f"{node_id}: a definition has no theorem proof discharge")
        node_map[node_id] = record
    for original in support_groups:
        if not isinstance(original, dict):
            raise ValueError("support groups must be objects")
        record = dict(original)
        group_id = _identifier(record.get("id"), "support_group.id")
        if group_id in group_map:
            raise ValueError(f"duplicate support group: {group_id}")
        if _DERIVED_KEYS.intersection(record):
            raise ValueError(f"{group_id}: graph-derived fields cannot be inputs")
        target = record.get("target")
        if target not in node_map:
            raise ValueError(f"{group_id}: target does not exist")
        members = record.get("members")
        if not isinstance(members, list) or not members:
            raise ValueError(f"{group_id}: members must be a nonempty array")
        if any(not isinstance(member, str) or member not in node_map for member in members):
            raise ValueError(f"{group_id}: every member must reference a node")
        if len(set(members)) != len(members):
            raise ValueError(f"{group_id}: duplicate joint premise")
        record["members"] = sorted(members)
        if record.get("relation") not in SUPPORT_RELATIONS:
            raise ValueError(f"{group_id}: relation is not support vocabulary; use the mention table")
        record["disposition"] = record.get("disposition", "CANDIDATE")
        if record["disposition"] not in _RANK:
            raise ValueError(f"{group_id}: unknown disposition")
        # A group defaults to no additional charge; node cost remains unknown unless supplied.
        record["cost_microusd"] = _money(record, "cost_microusd", 0)
        record["cost_error_microusd"] = _money(record, "cost_error_microusd", 0)
        if record["cost_microusd"] is None or record["cost_error_microusd"] is None:
            raise ValueError(f"{group_id}: group costs cannot be null")
        group_map[group_id] = record
    by_target = defaultdict(list)
    for group in group_map.values():
        by_target[group["target"]].append(group)
    for node_id, node in sorted(node_map.items()):
        bridges = node["bridging_claims"]
        if any(bridge not in node_map for bridge in bridges):
            raise ValueError(f"{node_id}: bridging claim does not exist")
        if not bridges:
            continue
        if not by_target[node_id]:
            group_id = "bridge:" + _digest([node_id, bridges])[:24]
            if group_id in group_map:
                raise ValueError("input identifier collides with reserved bridge group identifier")
            group = {"id": group_id, "target": node_id, "members": list(bridges),
                     "relation": "BRIDGING_DEPENDENCY", "disposition": "CANDIDATE",
                     "cost_microusd": 0, "cost_error_microusd": 0,
                     "host_derivation": "MANDATORY_DECLARED_BRIDGING_CLAIMS"}
            group_map[group_id] = group
            by_target[node_id].append(group)
        for group in by_target[node_id]:
            group["members"] = sorted(set(group["members"]) | set(bridges))
            group["mandatory_bridging_claims"] = list(bridges)
    if not isinstance(query_ids, list) or not query_ids:
        raise ValueError("query_ids must be a nonempty array")
    if any(not isinstance(query, str) or query not in node_map for query in query_ids):
        raise ValueError("every query id must reference a node")
    return node_map, group_map, sorted(set(query_ids))


def _adjacency(node_ids, groups):
    downstream = {node_id: set() for node_id in node_ids}
    upstream = {node_id: set() for node_id in node_ids}
    for group in groups.values():
        for member in group["members"]:
            downstream[member].add(group["target"])
            upstream[group["target"]].add(member)
    return downstream, upstream


def _tarjan(adjacency):
    """Iterative Tarjan: no Python recursion-depth limit on a literature chain."""
    index, low, stack, on_stack, components = {}, {}, [], set(), []
    for start in sorted(adjacency):
        if start in index:
            continue
        index[start] = low[start] = len(index)
        stack.append(start)
        on_stack.add(start)
        frames = [(start, iter(sorted(adjacency[start])), None)]
        while frames:
            node, children, parent = frames[-1]
            child = next(children, None)
            if child is not None:
                if child not in index:
                    index[child] = low[child] = len(index)
                    stack.append(child)
                    on_stack.add(child)
                    frames.append((child, iter(sorted(adjacency[child])), node))
                elif child in on_stack:
                    low[node] = min(low[node], index[child])
                continue
            frames.pop()
            if parent is not None:
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.remove(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(sorted(component))
    return sorted(components)


def _ancestors(query_ids, upstream):
    seen, pending = set(query_ids), list(query_ids)
    while pending:
        for parent in sorted(upstream[pending.pop()]):
            if parent not in seen:
                seen.add(parent)
                pending.append(parent)
    return seen


def _topological(node_ids, groups):
    downstream, upstream = _adjacency(node_ids, groups)
    degrees = {node_id: len(upstream[node_id]) for node_id in node_ids}
    ready = sorted(node_id for node_id, degree in degrees.items() if degree == 0)
    order = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for child in sorted(downstream[node_id]):
            degrees[child] -= 1
            if degrees[child] == 0:
                ready.append(child)
                ready.sort()
    if len(order) != len(node_ids):
        raise ValueError("internal error: condensation graph contains a cycle")
    return order


def _condense(node_map, groups):
    downstream, _ = _adjacency(node_map, groups)
    components, node_to_component = {}, {}
    for members in _tarjan(downstream):
        cyclic = len(members) > 1 or members[0] in downstream[members[0]]
        component_id = "scc:" + _digest(members)[:24] if cyclic else members[0]
        if cyclic and component_id in node_map:
            raise ValueError("input identifier collides with reserved SCC identifier")
        components[component_id] = {"id": component_id, "members": members, "cyclic": cyclic,
                                    "cost_microusd": 0, "cost_error_microusd": 0}
        for node_id in members:
            node_to_component[node_id] = component_id
    condensed, boundaries = {}, defaultdict(list)
    for group_id, group in sorted(groups.items()):
        target = node_to_component[group["target"]]
        members = sorted({node_to_component[x] for x in group["members"]} - {target})
        if components[target]["cyclic"]:
            boundaries[target].append(group_id)
            # Charge unresolved internal work even when the SCC has no boundary.
            components[target]["cost_microusd"] += group["cost_microusd"]
            components[target]["cost_error_microusd"] += group["cost_error_microusd"]
        else:
            condensed[group_id] = {**group, "target": target, "members": members,
                                   "source_group_ids": [group_id]}
    for target, group_ids in sorted(boundaries.items()):
        members = sorted({node_to_component[member] for group_id in group_ids
                          for member in groups[group_id]["members"]} - {target})
        # Unresolved SCC boundary is retained conservatively, never treated as an OR proof.
        if members:
            group_id = "scc-boundary:" + _digest([target, group_ids])[:24]
            if group_id in groups:
                raise ValueError("input identifier collides with reserved SCC boundary identifier")
            condensed[group_id] = {
                "id": group_id, "target": target, "members": members,
                "relation": "PROOF_DEPENDENCY",
                "disposition": _weakest(["ROUTE_UNDETERMINED"] + [groups[x]["disposition"] for x in group_ids]),
                "source_group_ids": group_ids,
                "cost_microusd": 0, "cost_error_microusd": 0,
            }
    return components, node_to_component, condensed


def _route_cost(required, chosen, components, node_map, groups):
    records = [node_map[node] for component in required
               for node in components[component]["members"]]
    records += [components[component] for component in required]
    records += [groups[group_id] for group_id in chosen.values()]
    nominal = sum(record["cost_microusd"] or 0 for record in records)
    lower = sum(max(0, (record["cost_microusd"] or 0) - record["cost_error_microusd"])
                for record in records)
    upper = sum((record["cost_microusd"] or 0) + record["cost_error_microusd"]
                for record in records)
    return {"nominal_microusd": nominal, "lower_microusd": lower, "upper_microusd": upper}


def _routes(components, node_map, groups, query_components, ancestors):
    by_target = defaultdict(list)
    for group_id, group in sorted(groups.items()):
        by_target[group["target"]].append(group_id)
    cost_complete = all(node_map[node]["cost_microusd"] is not None
                        for component in ancestors for node in components[component]["members"])
    summary = {
        "status": "EXACT", "cost_model_complete": cost_complete,
        "shared_prerequisites_charged_once": True,
        "cost_scope": "CONDENSED_CANDIDATE_STRUCTURE; NOT_A_MATHEMATICAL_PROOF_ROUTE",
        "tie_policy": "KEEP_ALL_ROUTES_WHOSE_LOWER_COST_IS_AT_MOST_THE_BEST_UPPER_COST",
        "max_search_states": MAX_SEARCH_STATES, "max_tied_routes": MAX_TIED_ROUTES,
        "explored_states": 0, "routes": [],
    }
    if not cost_complete:
        summary.update(status="UNPRICED", selection_mode="CONSERVATIVE_ANCESTORS",
                       lower_bound_microusd=0, upper_bound_microusd=None)
        return set(ancestors), set(groups), summary
    pending = [(frozenset(query_components), {})]
    candidates, best_upper = [], None
    while pending:
        if summary["explored_states"] >= MAX_SEARCH_STATES:
            summary["status"] = "BOUNDED"
            break
        required, chosen = pending.pop()
        summary["explored_states"] += 1
        costs = _route_cost(required, chosen, components, node_map, groups)
        if best_upper is not None and costs["lower_microusd"] > best_upper:
            continue
        unresolved = sorted(node for node in required if by_target[node] and node not in chosen)
        if unresolved:
            target = unresolved[0]
            for group_id in reversed(by_target[target]):
                pending.append((required | frozenset(groups[group_id]["members"]),
                                {**chosen, target: group_id}))
            continue
        route = {"component_ids": sorted(required), "condensed_group_ids": sorted(chosen.values()),
                 "cost": costs}
        best_upper = costs["upper_microusd"] if best_upper is None else min(best_upper, costs["upper_microusd"])
        candidates = [candidate for candidate in candidates
                      if candidate["cost"]["lower_microusd"] <= best_upper]
        if costs["lower_microusd"] <= best_upper:
            candidates.append(route)
        if len(candidates) > MAX_TIED_ROUTES:
            summary["status"] = "BOUNDED"
            break
    summary["routes"] = sorted(candidates, key=lambda route: (route["cost"]["nominal_microusd"],
                                                             route["condensed_group_ids"]))
    summary["upper_bound_microusd"] = best_upper
    if summary["status"] == "BOUNDED":
        summary["selection_mode"] = "CONSERVATIVE_ANCESTORS"
        summary["lower_bound_microusd"] = _route_cost(set(query_components), {}, components,
                                                      node_map, groups)["lower_microusd"]
        return set(ancestors), set(groups), summary
    summary["selection_mode"] = "UNION_OF_COST_TIED_ROUTES"
    summary["lower_bound_microusd"] = min(route["cost"]["lower_microusd"] for route in candidates)
    return ({node for route in candidates for node in route["component_ids"]},
            {group for route in candidates for group in route["condensed_group_ids"]}, summary)


def _scope(node_ids, queries, operation="PRUNED_SUPPORT_GRAPH"):
    return {"kind": operation, **queries, "node_set_sha256": _digest(sorted(node_ids))}


def _coverage(node_ids, node_map, queries, operation="PRUNED_SUPPORT_GRAPH"):
    definitions = [node for node in node_ids if node_map[node]["kind"].lower() == "definition"]
    theorems = [node for node in node_ids if node_map[node]["kind"].lower() in _THEOREM_KINDS]
    scope = _scope(node_ids, queries, operation)
    return {
        "theorems": {"scope": {**scope, "counted_kind": "THEOREM_LIKE"},
                     "eligible": len(theorems),
                     "proof_discharged": sum(bool(node_map[node].get("proof_discharged")) for node in theorems)},
        "definitions": {"scope": {**scope, "counted_kind": "DEFINITION"},
                        "eligible": len(definitions),
                        "statement_discharged": sum(bool(node_map[node].get("statement_discharged"))
                                                    for node in definitions)},
    }


def _edges(groups):
    return [{"id": "edge:" + _digest([group_id, member, group["target"]])[:24],
             "from": member, "to": group["target"], "support_group_id": group_id,
             "relation": group["relation"], "disposition": group["disposition"]}
            for group_id, group in sorted(groups.items()) for member in group["members"]]


def _witnesses(selected_ids, edges, query_ids):
    incoming = defaultdict(list)
    for edge in edges:
        incoming[edge["to"]].append(edge)
    witnesses = defaultdict(list)
    for query in query_ids:
        paths = {query: ([query], [])}
        queue = deque([query])
        while queue:
            target = queue.popleft()
            for edge in sorted(incoming[target], key=lambda item: item["id"]):
                node = edge["from"]
                if node not in paths:
                    target_nodes, target_edges = paths[target]
                    paths[node] = ([node] + target_nodes, [edge["id"]] + target_edges)
                    queue.append(node)
        for node in sorted(selected_ids):
            if node in paths:
                node_path, edge_path = paths[node]
                witnesses[node].append({"query_id": query, "node_path": node_path, "edge_path": edge_path,
                                        "kind": "QUERY" if node == query else "CANONICAL_SHORTEST_SUPPORT_PATH"})
    return witnesses


def _supported(roots, groups):
    supported = set(roots)
    while True:
        additions = {group["target"] for group in groups.values()
                     if all(member in supported for member in group["members"])} - supported
        if not additions:
            return supported
        supported.update(additions)


def _criticality(node_map, groups, query_ids, selected_ids, edges, queries):
    """Omission sensitivity is explicitly *not* a valid reduced AND premise set.

    COMPACT_V1 withdrawal lists only the queries unsupported beyond the baseline.
    """
    diagnostics = []
    original_roots = set(node_map) - {group["target"] for group in groups.values()}
    withdrawal_scope = _scope(node_map, queries, "ALL_INPUT_SUPPORT_ALTERNATIVES")
    supported_before = _supported(original_roots, groups)
    for deleted in edges:
        remaining = [edge for edge in edges if edge["id"] != deleted["id"]]
        upstream = {node: set() for node in selected_ids}
        for edge in remaining:
            upstream[edge["to"]].add(edge["from"])
        retained = _ancestors(query_ids, upstream)
        # Withdrawing an AND member invalidates its entire support group. Nodes
        # that lose every route cannot silently become newly justified roots.
        supported = _supported(original_roots, {key: value for key, value in groups.items()
                                                if key != deleted["support_group_id"]})
        unsupported = [query for query in query_ids if query not in supported]
        withdrawal = ({"unsupported_query_ids": unsupported} if "query_ids" in queries else
                      {"unsupported_query_count": len(unsupported),
                       "newly_unsupported_query_ids": [query for query in unsupported if query in supported_before]})
        diagnostics.append({
            "edge_id": deleted["id"], "from": deleted["from"], "to": deleted["to"],
            "support_group_id": deleted["support_group_id"],
            "scope": _scope(selected_ids, queries, "SINGLE_EDGE_OMISSION_IN_SELECTED_GRAPH"),
            "removed_node_ids": sorted(set(selected_ids) - retained),
            "retained_node_count": {"scope": _scope(retained, queries, "EDGE_OMISSION_REACHABILITY"),
                                    "value": len(retained)},
            "omission_is_valid_proof_route": False,
            "coverage_after_omission": _coverage(retained, node_map, queries, "EDGE_OMISSION_REACHABILITY"),
            "support_withdrawal": {
                "scope": withdrawal_scope,
                "invalidated_group_id": deleted["support_group_id"],
                "meaning": "STRUCTURAL_CANDIDATE_SUPPORT_ONLY; ROOTS_ARE_UNDISCHARGED",
                "query_route_available": not unsupported, **withdrawal,
            },
        })
    return diagnostics, {"scope": withdrawal_scope,
                         "unsupported_query_ids": [query for query in query_ids if query not in supported_before]}


def prune_graph(nodes: list[dict], support_groups: list[dict], query_ids: list[str], *, graph_format=None) -> dict:
    """Select candidate routes and derive blockers, witnesses and sensitivity.

    Missing node costs or an exhausted exact-search resource bound select the
    entire ancestor graph conservatively. This does not pretend a greedy route
    is optimal. Unknown upstream provenance remains FRONTIER. Returned state is
    entirely computed here; the caller must only pass host-derived evidence.
    graph_format COMPACT_V1 replaces nested query lists by their digest.
    """
    if graph_format not in GRAPH_FORMATS:
        raise ValueError("unknown graph_format")
    node_map, all_groups, query_ids = _normalize(nodes, support_groups, query_ids)
    queries = {"query_ids": query_ids} if graph_format is None else {"query_set_sha256": _digest(query_ids)}
    components, node_to_component, condensed = _condense(node_map, all_groups)
    query_components = sorted({node_to_component[node] for node in query_ids})
    _, upstream = _adjacency(components, condensed)
    ancestors = _ancestors(query_components, upstream)
    relevant_groups = {key: value for key, value in condensed.items() if value["target"] in ancestors}
    selected_components, selected_group_ids, route_search = _routes(
        components, node_map, relevant_groups, query_components, ancestors)
    selected_condensed = {key: value for key, value in relevant_groups.items() if key in selected_group_ids}
    selected_ids = {node for component in selected_components for node in components[component]["members"]}
    original_group_ids = {original for group in selected_condensed.values() for original in group["source_group_ids"]}
    # A closed cycle without incoming boundary still has internal support edges.
    for group_id, group in all_groups.items():
        if node_to_component[group["target"]] in selected_components and components[node_to_component[group["target"]]]["cyclic"]:
            original_group_ids.add(group_id)
    selected_groups = {key: all_groups[key] for key in sorted(original_group_ids)}
    edges = _edges(selected_groups)
    order = _topological(selected_components, selected_condensed)
    downstream, selected_upstream = _adjacency(selected_components, selected_condensed)
    blockers, weakest, effective = {}, {}, {}
    groups_at_target = defaultdict(list)
    for group in selected_condensed.values():
        groups_at_target[group["target"]].append(group)
    for component in order:
        members = components[component]["members"]
        blockers[component] = {blocker for member in members for blocker in node_map[member]["blocked_by"]}
        for member in members:
            if node_map[member]["disposition"] in {"BLOCKED", "SOURCE_READ_DEFECTIVE", "SOURCE_UNREACHABLE"}:
                blockers[component].add("node:" + member)
        if components[component]["cyclic"]:
            blockers[component].add("route:" + component)
        for parent in selected_upstream[component]:
            blockers[component].update(blockers[parent])
        # Bridge alignment is a prerequisite to the target's own disposition,
        # not merely a weaker path annotation attached to the bridge itself.
        dispositions = [node_map[member]["disposition"] for member in components[component]["members"]]
        dispositions.extend(node_map[member]["statement_alignment"] for member in components[component]["members"]
                            if node_map[member].get("statement_alignment") in _RANK)
        if any(node_map[member]["blocked_by"] for member in components[component]["members"]):
            dispositions.append("BLOCKED")
        if components[component]["cyclic"]:
            dispositions.append("ROUTE_UNDETERMINED")
            dispositions.extend(group["disposition"] for group in selected_groups.values()
                                if node_to_component[group["target"]] == component)
        for member in components[component]["members"]:
            dispositions.extend(effective[node_to_component[bridge]] for bridge in node_map[member]["bridging_claims"]
                                if node_to_component[bridge] != component)
        effective[component] = _weakest(dispositions)
    for component in reversed(order):
        dispositions = [effective[component]]
        for child in downstream[component]:
            dispositions.append(weakest[child])
            dispositions.extend(group["disposition"] for group in groups_at_target[child]
                                if component in group["members"])
        weakest[component] = _weakest(dispositions)
    witnesses = _witnesses(selected_ids, edges, query_ids)
    issues, output_nodes, roots = [], [], []
    original_targets = {group["target"] for group in all_groups.values()}
    for node_id in sorted(selected_ids):
        node, component = node_map[node_id], node_to_component[node_id]
        blocked_by = sorted(blockers[component])
        formalization_state = ("ROUTE_UNDETERMINED" if components[component]["cyclic"] else
                               "CONDITIONAL_ON_BLOCKED_ROOT" if blocked_by else "READY_FOR_ROOT_AUDIT")
        output_nodes.append({**node, "component_id": component, "blocked_by": blocked_by,
                             "included_by": witnesses[node_id],
                             "effective_disposition": effective[component],
                             "weakest_disposition_on_path": weakest[component],
                             "formalization_state": formalization_state})
        if node_id not in original_targets:
            evidence = node.get("origin_evidence")
            origin = (node.get("upstream_search") == "ORIGIN" and isinstance(evidence, dict)
                      and evidence.get("search_status") == "SEARCH_EXHAUSTED"
                      and isinstance(evidence.get("references"), list) and bool(evidence["references"])
                      and all(isinstance(ref, str) and ref for ref in evidence["references"]))
            roots.append({"id": node_id, "upstream_search": "ORIGIN" if origin else "FRONTIER",
                          "origin_evidence": evidence if origin else None,
                          "terminal_kind": node.get("terminal_kind"),
                          "library_binding": node.get("library_binding"), "blocked_by": blocked_by})
            if node.get("upstream_search") == "ORIGIN" and not origin:
                issues.append({"code": "ORIGIN_EVIDENCE_MISSING", "node_id": node_id})
        if not witnesses[node_id]:
            issues.append({"code": "ORPHAN_IN_SELECTED_GRAPH", "node_id": node_id})
    cyclic_components = [components[component] for component in order if components[component]["cyclic"]]
    if cyclic_components:
        issues.append({"code": "CYCLIC_SUPPORT_ROUTE", "component_ids": [item["id"] for item in cyclic_components]})
    if route_search["status"] != "EXACT":
        issues.append({"code": "ROUTE_OPTIMALITY_NOT_ESTABLISHED", "reason": route_search["status"]})
    for route in route_search["routes"]:
        route["node_ids"] = sorted(node for component in route["component_ids"] for node in components[component]["members"])
        route["support_group_ids"] = sorted({original for key in route["condensed_group_ids"]
                                              for original in relevant_groups[key]["source_group_ids"]})
        route["contains_unresolved_scc"] = any(components[component]["cyclic"] for component in route["component_ids"])
    criticality, baseline = _criticality(node_map, all_groups, query_ids, selected_ids, edges, queries)
    scoped_counts = {"scope": _scope(selected_ids, queries), "nodes": len(selected_ids),
                     "support_groups": len(selected_groups), "support_memberships": len(edges),
                     "blocked_nodes_including_sources": sum(bool(blockers[node_to_component[node]]) for node in selected_ids),
                     "blocked_descendant_nodes": sum(any(blockers[parent] for parent in selected_upstream[node_to_component[node]])
                                                     for node in selected_ids),
                     "node_set_sensitive_memberships": sum(bool(item["removed_node_ids"]) for item in criticality),
                     "proof_review_memberships": len(edges)}
    compact = {} if graph_format is None else {"graph_format": graph_format, **queries,
                                               "support_withdrawal_baseline": baseline}
    return {
        "schema_version": "0.3", "query_ids": query_ids, **compact,
        "scope": _scope(selected_ids, queries), "nodes": output_nodes,
        "support_groups": list(selected_groups.values()), "edges": edges,
        "selected_node_ids": sorted(selected_ids), "selected_component_ids": sorted(selected_components),
        "ancestor_node_ids": sorted(node for component in ancestors for node in components[component]["members"]),
        "roots": roots, "sccs": cyclic_components, "condensation_order": order,
        "topological_order": [component for component in order if not components[component]["cyclic"]],
        "formalization_order": [component for component in order if not components[component]["cyclic"] and not blockers[component]],
        "conditional_nodes": [{"id": node, "blocked_by": sorted(blockers[node_to_component[node]])}
                              for node in sorted(selected_ids) if blockers[node_to_component[node]]],
        "route_search": route_search,
        "coverage": _coverage(selected_ids, node_map, queries),
        "counts": scoped_counts, "edge_criticality": criticality, "issues": issues,
        "disposition_order_weakest_first": list(DISPOSITIONS),
        "blocking_policy": "UNION_OF_RETAINED_ROUTES; BLOCKING_GATES_ORDERING_NOT_SELECTION",
        "root_tag_policy": "FRONTIER_UNLESS_EXHAUSTED_SEARCH_EVIDENCE",
    }
