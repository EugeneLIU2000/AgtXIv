"""Stage 3 hand-off (§10): a claim nomination's backward closure as a v0.3 graph {nodes, support_groups}.

The closure uses the legs the nomination's own run used: analysis._index and analysis._scope apply the policy
scope (traverse, include_part_expansions), and establishment_reading picks the readings, as for
layers. One v0.3 support group per effective derivation of a conclusion: readings of one derivation are joined
(UNION, §8.1), and the statement junction's legs join every derivation of its conclusion, since §4.1 requires
both; with no derivation the statement junction stands alone. A citation group of several requests under
citation_group_semantics OR has no v0.3 AND-group form and is refused. relation = the strongest leg role, with
UNCLASSIFIED weakest and read as PROOF only when no leg has a role; every leg's position, use_site, role and flags
go into `losses`. Node ids are kept, so Stage 3 reviews map back by id and by `groups`. A claim's v0.3 kind is its
agreed reading kind (definition, theorem, ...: what v0.3 graph and certify count), else "claim". Exported nodes are
UNREVIEWED and FRONTIER, and every placeholder carries its hard blocker (v0.3 convention).

Unlike analysis, the export does not add the structural productions: an UNRESOLVED_OCCURRENCE whose occurrence has
a whole Claim stays a placeholder node (Stage 3 decides whether the two are one premise), and a whole claim is not
joined to its parts. So the exported graph can show a placeholder blocker where analysis found a finite layer.
"""
from __future__ import annotations

from collections import Counter, defaultdict

import contracts
from analysis import _index, _scope
from core import canonical, digest
from delta import address

STRENGTH = ("PROOF_DEPENDENCY", "SCIENTIFIC_CLAIM_DEPENDENCY", "DEFINITION_DEPENDENCY", "SCOPE_DEPENDENCY",
            "BRIDGING_DEPENDENCY", "UNCLASSIFIED")
V03_KINDS = {"EXTERNAL_REQUEST": "external_claim_request", "UNRESOLVED_OCCURRENCE": "unresolved_claim_occurrence"}


def _relation(roles):
    role = min(roles, key=STRENGTH.index)
    return "PROOF_DEPENDENCY" if role == "UNCLASSIFIED" else role


def _node(row, kind):
    node = {"id": row["id"], "disposition": "UNREVIEWED", "upstream_search": "FRONTIER", "cost_microusd": None}
    if row["id"].startswith("placeholder:"):
        kind = V03_KINDS[row["kind"]]
        return {**node, "kind": kind, "blocked_by": [kind.upper() + ":" + row["id"]]}
    return {**node, "kind": kind}


def export_v03(nomination, view, manifest, policy, dispositions):
    """view: the merged DeltaSetView of manifest (delta.check_manifest); policy and dispositions: the nomination
    run's AnalysisPolicy and reviews.derive_dispositions output, as analysis.analyze received them. dispositions is
    required ({} for an empty review set), so a signed closure is never silently exported as unsigned."""
    for name, row in (("FoundationNomination", nomination), ("DeltaSetManifest", manifest), ("AnalysisPolicy", policy)):
        contracts.validate(name, row)
    if nomination["subject_kind"] != "CLAIM":
        raise ValueError("EXPORT_REQUIRES_CLAIM_SUBJECT")
    if ((nomination["policy_id"], nomination["manifest_id"]) != (policy["policy_id"], manifest["manifest_id"])
            or sorted(manifest["deltas"]) != sorted(view["deltas"])):
        raise ValueError("EXPORT_INPUTS_ARE_NOT_THE_NOMINATION_RUN")
    ctx, reading = _index(view, policy, dispositions), policy["establishment_reading"]
    if nomination["subject_id"] not in ctx.claims:
        raise ValueError("EXPORT_SUBJECT_OUTSIDE_POLICY_SCOPE")
    derivations = defaultdict(lambda: defaultdict(list))
    for j, legs in _scope(ctx, frozenset()):
        if reading["mode"] == "UNION" or j["reading_method"] in reading["methods"]:
            derivations[j["conclusion_id"]][j["derivation_id"]] += [(j["id"], position, leg) for position, leg in legs]
    closure, stack = set(), [nomination["subject_id"]]
    while stack:
        node = stack.pop()
        if node not in closure:
            closure.add(node)
            stack.extend(leg["premise_id"] for legs in derivations[node].values() for _, _, leg in legs)
    groups, record_groups, losses = [], {}, []
    for target in sorted(closure):
        alternatives = dict(derivations[target])
        statement = alternatives.pop("statement", [])
        for legs in [statement + legs for _, legs in sorted(alternatives.items())] or ([statement] if statement else []):
            members = sorted({leg["premise_id"] for _, _, leg in legs})
            cited = Counter(g for p in members if (g := ctx.holders.get(p, {}).get("citation_group")))
            if policy["citation_group_semantics"] == "OR" and max(cited.values(), default=0) > 1:
                raise ValueError("EXPORT_OR_CITATION_GROUP_UNSUPPORTED: " + target)
            junction_ids = sorted({jid for jid, _, _ in legs})
            group_id = address("group", junction_ids)
            groups.append({"id": group_id, "target": target, "members": members,
                           "relation": _relation(leg["role"] for _, _, leg in legs), "disposition": "UNREVIEWED"})
            record_groups[group_id] = junction_ids
            losses.append({"group_id": group_id, "legs": [{"junction_id": jid, "position": position, **leg}
                                                          for jid, position, leg in legs]})
    rows = {**ctx.claims, **ctx.holders}
    graph = {"nodes": [_node(rows[node], ctx.kind.get(node, "claim")) for node in sorted(closure)], "support_groups": groups}
    return {"graph": graph, "record": {
        "kind": "V03Export", "nomination_id": nomination["nomination_id"], "policy_id": policy["policy_id"],
        "policy_sha256": digest(canonical(policy)), "manifest_id": manifest["manifest_id"],
        "query_ids": [nomination["subject_id"]], "groups": record_groups,
        "dropped_leg_fields": ["position", "use_site", "role", "flags"], "losses": losses,
        "graph_sha256": digest(canonical(graph))}}
