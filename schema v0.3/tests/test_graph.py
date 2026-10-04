"""prune_graph selection semantics and the COMPACT_V1 diagnostic format."""
import json
from pathlib import Path

import pytest

from candidates import select_candidate_graph
from graph import prune_graph

# Golden: b9f6432's (pre-COMPACT_V1) graph.prune_graph(*cyclic_fixture()), stored as JSON.
LEGACY = Path(__file__).resolve().parent / "fixtures" / "legacy_graph_b9f6432.json"


def node(node_id, cost=0, **extra):
    return {"id": node_id, "kind": "theorem", "cost_microusd": cost, **extra}


def group(target, *members):
    return {"id": "g:" + target + ":" + "+".join(members), "target": target,
            "members": list(members), "relation": "PROOF_DEPENDENCY"}


def cyclic_fixture():
    # q1 has two OR routes, q3 one; q2 rests on the rootless cycle m <-> n.
    nodes = [node("q1"), node("q2"), node("q3"), node("x", 1), node("y", 4), node("m", 1), node("n", 1)]
    groups = [group("q1", "x"), group("q1", "y"), group("q3", "x"), group("q2", "m"), group("m", "n"), group("n", "m")]
    return nodes, groups, ["q1", "q2", "q3"]


def test_and_or_charges_shared_prerequisite_once():
    nodes = [node("q1"), node("q2"), node("x", 1), node("s", 5), node("y", 4)]
    groups = [group("q1", "s", "x"), group("q1", "y"), group("q2", "s")]
    alone = prune_graph(nodes, groups, ["q1"])
    assert alone["selected_node_ids"] == ["q1", "y"]  # 4 < 1 + 5
    both = prune_graph(nodes, groups, ["q1", "q2"])
    # s is paid once for q2, so x + s (6) beats y + s (9).
    assert both["selected_node_ids"] == ["q1", "q2", "s", "x"]
    assert both["route_search"]["status"] == "EXACT"
    assert both["route_search"]["upper_bound_microusd"] == 6


def test_scc_is_condensed_and_kept_out_of_formalization_order():
    graph = prune_graph(*cyclic_fixture())
    [scc] = graph["sccs"]
    assert scc["members"] == ["m", "n"] and scc["cyclic"]
    states = {row["id"]: row["formalization_state"] for row in graph["nodes"]}
    assert states["m"] == states["n"] == "ROUTE_UNDETERMINED"
    assert states["q2"] == "CONDITIONAL_ON_BLOCKED_ROOT"
    assert scc["id"] not in graph["formalization_order"] and "q2" not in graph["formalization_order"]
    assert {"code": "CYCLIC_SUPPORT_ROUTE", "component_ids": [scc["id"]]} in graph["issues"]


def test_unpriced_selects_all_ancestors():
    nodes = [node("q"), node("a", None), node("b", 1)]
    graph = prune_graph(nodes, [group("q", "a"), group("q", "b")], ["q"])
    assert graph["route_search"]["status"] == "UNPRICED"
    assert graph["route_search"]["selection_mode"] == "CONSERVATIVE_ANCESTORS"
    assert graph["selected_node_ids"] == ["a", "b", "q"]
    assert {row["upstream_search"] for row in graph["roots"]} == {"FRONTIER"}


def test_blocking_gates_ordering_not_selection():
    nodes = [node("q"), node("cheap", 1, blocked_by=["GAP"]), node("pricey", 9)]
    graph = prune_graph(nodes, [group("q", "cheap"), group("q", "pricey")], ["q"])
    assert graph["selected_node_ids"] == ["cheap", "q"]
    assert graph["formalization_order"] == []
    assert [row["id"] for row in graph["conditional_nodes"]] == ["cheap", "q"]


def _keys(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield path + (key,)
            yield from _keys(item, path + (key,))
    elif isinstance(value, list):
        for item in value:
            yield from _keys(item, path)


def test_legacy_output_is_unchanged_and_compact_is_lossless():
    legacy = prune_graph(*cyclic_fixture())
    assert json.loads(json.dumps(legacy)) == json.loads(LEGACY.read_bytes())
    compact = prune_graph(*cyclic_fixture(), graph_format="COMPACT_V1")
    assert [path for path in _keys(compact) if path[-1] == "query_ids"] == [("query_ids",)]
    assert compact["query_ids"] == legacy["query_ids"]
    baseline = compact["support_withdrawal_baseline"]["unsupported_query_ids"]
    assert baseline == ["q2"]
    for old, new in zip(legacy["edge_criticality"], compact["edge_criticality"], strict=True):
        old_w, new_w = old["support_withdrawal"], new["support_withdrawal"]
        assert set(old_w["unsupported_query_ids"]) == set(baseline) | set(new_w["newly_unsupported_query_ids"])
        assert new_w["unsupported_query_count"] == len(old_w["unsupported_query_ids"])
        assert not set(baseline) & set(new_w["newly_unsupported_query_ids"])
        assert new["scope"]["query_set_sha256"] == compact["query_set_sha256"]
    newly = [row["support_withdrawal"]["newly_unsupported_query_ids"] for row in compact["edge_criticality"]]
    assert ["q3"] in newly and not any("q1" in row for row in newly)  # q1 keeps its OR alternative
    strip = lambda graph: {key: value for key, value in graph.items()
                           if key not in {"scope", "coverage", "counts", "edge_criticality", "graph_format",
                                          "query_set_sha256", "support_withdrawal_baseline"}}
    assert strip(compact) == strip(legacy)


def test_graph_format_travels_with_the_assembly():
    nodes, groups, queries = cyclic_fixture()
    assembly = {"nodes": nodes, "support_groups": groups, "query_ids": queries}
    assert "graph_format" not in select_candidate_graph(assembly)
    assert select_candidate_graph({**assembly, "graph_format": "COMPACT_V1"})["graph_format"] == "COMPACT_V1"
    with pytest.raises(ValueError):
        prune_graph(nodes, groups, queries, graph_format="COMPACT_V2")
