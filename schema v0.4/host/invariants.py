"""Host checks of the strict invariants G1-G15 (spec §3.7) on a merged DeltaSetView, before any load.

check(view) returns [{invariant, id, detail}]; an empty list means every check passed. G5 re-validates
every row against its contract first, and a view with a G5 finding gets only those (the other checks
read required fields). The contracts carry G1 (legs minItems 1; CONCLUDES is derived), G11 (no row
admits a disposition), and the per-row halves of G7 (source: iff the conclusion is a placeholder id) and
G13 (STATEMENT legs only in a statement junction); the host adds at most one statement junction per
(conclusion, reading_method, method_version). G14: a junction's reading basis is every ClaimReading of its
conclusion with its (reading_method, method_version); it is flagged if any of them is superseded. G15 holds by
construction: delta.merge refuses two rows under one id and PREMISE_OF rows come only from ids.logical_edges.
Dependency cycles are not violations (an analysis diagnostic, §4.1).
"""
from __future__ import annotations

from collections import Counter, defaultdict

from jsonschema.exceptions import best_match

import contracts
from delta import asserted
from graph import _tarjan
from ids import seal

# §3.6 endpoint labels of every type a delta may assert; logical→logical is PART_OF only (G3).
ENDPOINTS = {"STATES": ("PaperVersion", "Claim"), "STATED_BY": ("Claim", "Work"), "READS": ("ClaimReading", "Claim"),
             "PART_OF": ("Claim", "Claim"), "HAS_ENTRY": ("PaperVersion", "BibEntry"), "RESOLVES_TO": ("BibEntry", "Work"),
             "REQUESTS_FROM": ("Placeholder", "BibEntry"), "MENTIONS": ("Claim", "BibEntry"),
             "RESTATES_RESULT_OF": ("Claim", "BibEntry"), "VERSION_OF": ("PaperVersion", "Work"),
             "SAME_WORK": ("Work", "Work"), "CORRECTS": ("Work", "Work"),
             "SUPERSEDES": ("ClaimReading", "ClaimReading"), "ASSERTS_PRIMITIVE": ("PrimitiveAssertion", "Claim"),
             "INCLUDES": ("Corpus", "PaperVersion")}
HOST_RULE_SAME_WORK = frozenset({"HOST_RULE_ARXIV_DOI", "HOST_RULE_ARXIV_METADATA_DOI"})


def admitted(edge, work_identity, accepted):
    """Whether the policy admits a SAME_WORK or RESOLVES_TO edge as work identity (§3.5, I-9): a host rule
    always; an accepted ('WORK_IDENTITY', edge id) under PLUS_REVIEWED_SAME_WORK; any under PLUS_CANDIDATE."""
    host = (edge["props"]["basis"] in HOST_RULE_SAME_WORK if edge["type"] == "SAME_WORK"
            else edge["props"]["method"] == "HOST_RULE")
    return host or work_identity == "PLUS_CANDIDATE_SAME_WORK" or (
        work_identity == "PLUS_REVIEWED_SAME_WORK" and ("WORK_IDENTITY", edge["id"]) in accepted)


def work_components(view, work_identity, accepted=()):
    """{work id: frozenset of works} joined by the SAME_WORK edges the policy admits."""
    accepted, parent = set(accepted), {w: w for w in view["nodes"]["Work"]}

    def find(w):
        while parent.setdefault(w, w) != w:
            parent[w] = parent[parent[w]]
            w = parent[w]
        return w
    for e in view["edges"].values():
        if e["type"] == "SAME_WORK" and admitted(e, work_identity, accepted):
            parent[find(e["start_id"])] = find(e["end_id"])
    members = defaultdict(set)
    for w in list(parent):
        members[find(w)].add(w)
    return {w: frozenset(members[find(w)]) for w in parent}


def check(view, work_identity="EXPLICIT_IDS_ONLY", accepted=()):
    """Every violation on the view; G7 uses the loading policy's work identity and accepted (kind, id) reviews."""
    tables = [(label + "Node", table) for label, table in view["nodes"].items()] + [("Edge", view["edges"])]
    found = [("G5", rid, error.message) for name, table in tables for rid, row in table.items()
             if (error := best_match(contracts.validator(name).iter_errors(asserted(row))))]
    if not found:
        found = _graph(view, tables, work_identity, set(accepted)) + _g6(tables)
    return [{"invariant": g, "id": i, "detail": d} for g, i, d in found]


def _g6(tables):
    out = []
    for name, table in tables:
        for rid, row in table.items():
            expected = seal(name.removesuffix("Node"), {k: v for k, v in asserted(row).items() if k not in ("id", "content_sha256")})
            if (expected["id"], expected["content_sha256"]) != (rid, row["content_sha256"]):
                out.append(("G6", rid, f"identity fields give {expected['id']} / {expected['content_sha256']}"))
    return out


def _graph(view, tables, work_identity, accepted):
    nodes, edges = view["nodes"], view["edges"]
    label = {i: lab for lab, table in nodes.items() for i in table}
    junctions, claims, holders = nodes["Junction"], nodes["Claim"], nodes["Placeholder"]
    out_edges, in_edges = defaultdict(list), defaultdict(list)
    for e in edges.values():
        out_edges[e["type"], e["start_id"]].append(e)
        in_edges[e["type"], e["end_id"]].append(e)
    premise_of = defaultdict(list)
    for j in junctions.values():
        for leg in j["legs"]:
            premise_of[leg["premise_id"]].append(j)
    pv_of = lambda i: (claims.get(i) or {}).get("paper_version_id")
    found, loaded = [], set(view["deltas"])

    for _, table in tables:  # G9
        for rid, row in table.items():
            if not (row.get("asserted_by") and row.get("methods")):
                found.append(("G9", rid, "asserted_by or methods empty"))
            elif not set(row["asserted_by"]) <= loaded:
                found.append(("G9", rid, "asserted by a delta outside the manifest"))
    for e in edges.values():  # G3
        want = ENDPOINTS.get(e["type"])
        have = (label.get(e["start_id"], "Corpus" if e["start_id"].startswith("corpus:") else None), label.get(e["end_id"]))
        if want != have:
            found.append(("G3", e["id"], f"{e['type']} joins {have[0] or 'missing'}→{have[1] or 'missing'}; "
                                        + ("allowed {}→{}".format(*want) if want else "not assertable in a delta")))

    components = work_components(view, work_identity, accepted)
    for j in junctions.values():
        jid, conclusion, derivation = j["id"], j["conclusion_id"], j["derivation_id"]
        premises = [leg["premise_id"] for leg in j["legs"]]
        found += [("G2", jid, f"premise {p} is {label.get(p) or 'missing'}") for p in premises
                  if label.get(p) not in ("Claim", "Placeholder")]
        target = holders.get(conclusion)
        if not (label.get(conclusion) == "Claim" or (target and target["kind"] == "EXTERNAL_REQUEST")):
            found.append(("G2", jid, f"conclusion {conclusion} is not conclusion-capable"))
        if conclusion in premises:
            found.append(("G4", jid, "the conclusion is one of its premises"))
        if derivation.startswith("source:") and target:  # G7
            pv = derivation.removeprefix("source:").rsplit(":sha256:", 1)[0]
            works = {e["end_id"] for e in out_edges["RESOLVES_TO", target.get("bib_entry_id")]
                     if admitted(e, work_identity, accepted)}
            cls = frozenset().union(*(components.get(w, {w}) for w in works))
            if not cls & {e["end_id"] for e in out_edges["VERSION_OF", pv]}:
                found.append(("G7", jid, f"{pv}'s work is not in the request's work-identity class"))
            for p in premises:
                c = claims.get(p)
                if c and c.get("paper_version_id") != pv and c.get("work_id") not in cls:
                    found.append(("G7", jid, f"premise {p} is neither stated by {pv} nor by a work of the class"))
        if derivation.startswith(("proof:", "unlocated:")):  # G12
            pv = pv_of(conclusion)
            for p in premises:
                ok = pv is not None and (pv_of(p) == pv if p in claims else
                                         p in holders and holders[p]["paper_version_id"] == pv == pv_of(holders[p]["created_by_claim_id"]))
                if not ok:
                    found.append(("G12", jid, f"premise {p} is not of the conclusion's paper version {pv}"))
    statements = Counter((j["conclusion_id"], j["reading_method"], j["method_version"])
                         for j in junctions.values() if j["derivation_id"] == "statement")
    found += [("G13", c, f"{n} statement junctions of {m} {v}") for (c, m, v), n in sorted(statements.items()) if n > 1]

    for r in holders.values():  # G8
        if r["kind"] != "EXTERNAL_REQUEST":
            continue
        sources = out_edges["REQUESTS_FROM", r["id"]]
        if [e["end_id"] for e in sources] != [r["bib_entry_id"]]:
            found.append(("G8", r["id"], f"{len(sources)} REQUESTS_FROM; exactly one to {r['bib_entry_id']} required"))
        if not any(j["conclusion_id"] == r["created_by_claim_id"] and j["derivation_id"] == r["citing_derivation_id"]
                   for j in premise_of[r["id"]]):
            found.append(("G8", r["id"], "not a premise of the junction named by its identity"))

    for c in claims.values():  # G10
        states, stated_by = in_edges["STATES", c["id"]], out_edges["STATED_BY", c["id"]]
        want = ([c.get("paper_version_id")], []) if c["origin"] == "PAPER_VERSION" else ([], [c.get("work_id")])
        if ([e["start_id"] for e in states], [e["end_id"] for e in stated_by]) != want:
            found.append(("G10", c["id"], f"{len(states)} STATES and {len(stated_by)} STATED_BY for origin {c['origin']}"))

    supersedes = [e for e in edges.values() if e["type"] == "SUPERSEDES"]  # G14
    successors = Counter(e["end_id"] for e in supersedes)
    found += [("G14", r, f"{n} successors") for r, n in sorted(successors.items()) if n > 1]
    adjacency = {r: set() for r in nodes["ClaimReading"]}
    for e in supersedes:
        adjacency.setdefault(e["start_id"], set()).add(e["end_id"])
        adjacency.setdefault(e["end_id"], set())
    cyclic = [c for c in _tarjan(adjacency) if len(c) > 1] + [[e["start_id"]] for e in supersedes if e["start_id"] == e["end_id"]]
    found += [("G14", c[0], "SUPERSEDES cycle through " + ", ".join(c)) for c in cyclic]
    superseded = {(r["claim_id"], r["method"], r["method_version"]) for r in nodes["ClaimReading"].values() if r["id"] in successors}
    found += [("G14", j["id"], "uses a superseded reading") for j in junctions.values()
              if (j["conclusion_id"], j["reading_method"], j["method_version"]) in superseded]
    return found
