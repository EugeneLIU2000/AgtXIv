"""Stage 2 foundation analysis (spec §4, §8): metric vectors and nominations, never a status (I-0, I-10).

Input: a merged DeltaSetView (delta.merge), its DeltaSetManifest, one AnalysisPolicy and the dispositions
of one review set (reviews.derive_dispositions). The junction rows in scope give three graphs: E (the
policy's establishment_reading) for layers, route status and cycles; L and U (importance_methods; legs
agreed by >= 2 readings of a derivation or its only reading, and the union) for every importance bracket. The
statement junctions of a conclusion (one per reading, G13) are readings of its one statement derivation and join
the same way: E takes the union of the admitted readings' legs.
Only PREMISE_OF/CONCLUDES are traversed (I-3); layers are derived here and never read (I-5). A model-written
PrimitiveAssertion or work-identity edge counts only once signed (I-0, I-9); a CORRECTS edge blocks the source:
junctions that draw on the corrected work until the junction is signed (§3.5). The policy's traverse decides whose
claims enter the graphs (SAMPLE papers only, or also EXPANSION and DISCOVERY papers) and count_basis whose claims make
a paper dependent (I-14): under SAMPLE_ONLY the upstream chain may pass through cited or discovered papers while only
randomly sampled papers are counted, and the bootstrap resamples the counted papers only; dependents and necessary
dependents count claims of counted papers only. Two structural host rules join identities without a model (+0 layer):
an UNRESOLVED_OCCURRENCE whose occurrence has a whole Claim in scope is resolved by that claim (the same occurrence), and
a whole Claim whose parts are in scope and that has no derivation of its own is established by its parts jointly.
"""
from __future__ import annotations

import heapq
import math
import random
from collections import Counter, defaultdict, deque
from functools import reduce
from itertools import groupby
from operator import or_
from types import SimpleNamespace

import contracts
import graph
from core import canonical, digest
from corpus import CONTRACT_VERSION, order_key
from delta import address
from invariants import admitted, work_components
from ledger import MODEL_METHODS
from reviews import SIGNED, UNREVIEWED, leg_id

ALLOWED_BASIS = frozenset({"PRIMITIVE", "IN_LIBRARY", "WORK_LOCATOR"})  # §8.4
NO_SUPPORT = frozenset({"NO_SUPPORT_PROPOSED", "DEFINITION_NO_SUPPORT_PROPOSED"})
LISTS = ("DEFINITIONS", "THEOREM_LIKE", "WORKS", "LOW_LAYER_BY_OPEN_PREMISES")
BASES = ("ALL_ROOTS", "PRIMITIVE_ASSERTED")
SKETCH_K = 64  # bottom-k sketch size for the ESTIMATED dependents of non-nominated subjects
UNKNOWN_DATE = {"value": None, "kind": "UNKNOWN", "precision": "UNKNOWN", "source": "no dated record in the view"}


def _index(view, policy, dispositions):
    """What the policy and review set fix before any leg is perturbed: scope, reading kinds, examining methods,
    work identity and pools, admitted primitives, CORRECTS-blocked junctions and the resampled papers."""
    nodes, edges = view["nodes"], view["edges"].values()
    of = lambda t: [e for e in edges if e["type"] == t]
    accepted = {(k, i) for k, table in dispositions.items() for i, d in table.items() if d == SIGNED}
    admission = defaultdict(set)
    for e in of("INCLUDES"):
        admission[e["end_id"]].add(e["props"]["admission"])
    excluded = set() if policy["traverse"] == "ALL_ADMITTED" else {p for p, a in admission.items() if "SAMPLE" not in a}
    claims = {i: r for i, r in nodes["Claim"].items() if r.get("paper_version_id") not in excluded}
    holders = {i: r for i, r in nodes["Placeholder"].items() if r["paper_version_id"] not in excluded}
    superseded, kinds = {e["end_id"] for e in of("SUPERSEDES")}, defaultdict(set)
    examined = {i: set(r["methods"]) for i, r in (*claims.items(), *holders.items())}
    for r in nodes["ClaimReading"].values():
        if r["id"] not in superseded:
            kinds[r["claim_id"]].add(r["kind"])
            examined.get(r["claim_id"], set()).add(r["method"])
    for j in nodes["Junction"].values():
        examined.get(j["conclusion_id"], set()).add(j["reading_method"])
    comps = work_components(view, policy["work_identity"], accepted)
    comp = lambda w: comps.get(w, frozenset({w}))
    resolves, versions = defaultdict(set), defaultdict(set)
    for e in of("RESOLVES_TO"):
        if admitted(e, policy["work_identity"], accepted):
            resolves[e["start_id"]].add(e["end_id"])
    for e in of("VERSION_OF"):
        versions[min(comp(e["end_id"]))].add(e["start_id"])
    pool = {h: sorted({min(comp(w)) for w in resolves[r["bib_entry_id"]]})
            for h, r in holders.items() if r["kind"] == "EXTERNAL_REQUEST"}
    corrected = {min(comp(e["end_id"])) for e in of("CORRECTS")}
    stale_pvs = {p for w in corrected for p in versions.get(w, ())}
    stale = {c for c, r in claims.items()
             if r.get("paper_version_id") in stale_pvs or "work_id" in r and min(comp(r["work_id"])) in corrected}
    blocked = {j["id"] for j in nodes["Junction"].values()  # §3.5: resolutions drawing on a corrected work, unsigned
               if j["derivation_id"].startswith("source:") and ("JUNCTION", j["id"]) not in accepted
               and (corrected.intersection(pool.get(j["conclusion_id"], ()))
                    or any(l["premise_id"] in stale for l in j["legs"]))}
    papers = sorted({r["paper_version_id"] for r in claims.values() if "paper_version_id" in r} | (admission.keys() - excluded))
    pidx = {p: i for i, p in enumerate(papers)}
    # A paper with no INCLUDES edge (a hand-built view) is treated as sampled, as traversal treats it.
    counted = [pidx[p] for p in papers if policy["count_basis"] == "ALL_ADMITTED" or not admission.get(p) or "SAMPLE" in admission[p]]
    pvs = nodes["PaperVersion"]
    topics = [frozenset({pvs[p].get("primary_category"), *pvs[p].get("categories", ())} - {None}) if p in pvs else frozenset()
              for p in papers]
    whole = {r["occurrence_ids"][0]: c for c, r in claims.items()
             if r["origin"] == "PAPER_VERSION" and r["part"] == "whole" and len(r["occurrence_ids"]) == 1}
    resolved = {h: whole[r["occurrence_id"]] for h, r in holders.items() if r["kind"] == "UNRESOLVED_OCCURRENCE"
                and whole.get(r["occurrence_id"]) not in (None, r["created_by_claim_id"])}
    parts = defaultdict(set)
    for e in of("PART_OF"):
        if e["start_id"] in claims and e["end_id"] in claims:
            parts[e["end_id"]].add(e["start_id"])
    ctx = SimpleNamespace(
        view=view, policy=policy, claims=claims, holders=holders, logical=claims.keys() | holders.keys(), kinds=kinds,
        resolved=resolved, parts={w: sorted(ps) for w, ps in parts.items()},
        kind={c: next(iter(ks)) if len(ks) == 1 else "UNKNOWN" for c, ks in kinds.items()}, examined=examined,
        primitive={r["claim_id"] for i, r in nodes["PrimitiveAssertion"].items()
                   if {r["method"], *r["methods"]}.isdisjoint(MODEL_METHODS) or ("PRIMITIVE_ASSERTION", i) in accepted},
        comp=comp, pool=pool, versions=versions, blocked=blocked, papers=papers, pidx=pidx, legs=dispositions.get("LEG", {}),
        counted=counted, topics=topics)
    mask = reduce(or_, (1 << i for i in counted), 0)
    ctx.bit = lambda n: 1 << pidx[p] if (p := (claims.get(n) or holders.get(n) or {}).get("paper_version_id")) in pidx else 0
    ctx.cbit = lambda n: ctx.bit(n) & mask if n in claims else 0  # only claims of counted papers make a paper dependent (§8.2)
    return ctx


def _topics(ctx, bits):
    """Distinct arXiv categories (primary and cross-lists) of the papers in a bit set (ARXIV_CATEGORIES_V1)."""
    found = set()
    while bits:
        low = bits & -bits
        found |= ctx.topics[low.bit_length() - 1]
        bits ^= low
    return len(found)


def _root_class(ctx, n):
    if n in ctx.holders:
        h, works = ctx.holders[n], ctx.view["nodes"]["Work"]
        if h["kind"] == "UNRESOLVED_OCCURRENCE":
            return "UNRESOLVED_OCCURRENCE"
        library = any(works.get(w, {}).get("terminal_kind") == "IN_LIBRARY" for r in ctx.pool[n] for w in ctx.comp(r))
        return "IN_LIBRARY" if library else "EXTERNAL_REQUEST"
    if n in ctx.primitive:
        return "PRIMITIVE"
    if ctx.claims[n]["origin"] == "WORK_LOCATOR":
        return "WORK_LOCATOR"
    return "DEFINITION_NO_SUPPORT_PROPOSED" if ctx.kind.get(n) == "definition" else "NO_SUPPORT_PROPOSED"


def _scope(ctx, drop):
    """[(junction, [(position, leg)])] whose conclusion and premises are in scope and that no CORRECTS blocks;
    empty junctions vanish. Pure: export_v03 reuses it."""
    rows, part = [], ctx.policy["include_part_expansions"]
    for j in sorted(ctx.view["nodes"]["Junction"].values(), key=lambda j: j["id"]):
        legs = [(p, l) for p, l in enumerate(j["legs"])
                if (j["id"], p) not in drop and (part or "EXPANDED_TO_PARTS" not in l["flags"])]
        if (legs and j["id"] not in ctx.blocked and j["conclusion_id"] in ctx.logical
                and all(l["premise_id"] in ctx.logical for _, l in legs)):
            rows.append((j, legs))
    return rows


def _graph(ctx, rows, agree):
    """Productions (head, {input: junction id | None}, +layer): one per derivation of a claim (joined with its
    statement junction), one per source junction of a request, one per member of an OR citation group."""
    groups, stmt, derivs, prods = defaultdict(list), {}, defaultdict(list), []
    for j, legs in rows:
        groups[j["conclusion_id"], j["derivation_id"]].append((j["id"], {l["premise_id"] for _, l in legs}))
    for (c, d), js in sorted(groups.items()):
        count, via = Counter(p for _, ps in js for p in ps), {}
        for jid, ps in js:
            for p in sorted(ps):
                via.setdefault(p, jid)
        inputs = {p: v for p, v in via.items() if not agree or len(js) == 1 or count[p] >= 2}
        if ctx.policy["citation_group_semantics"] == "OR":
            cited = defaultdict(list)
            for p in inputs:
                if g := ctx.holders.get(p, {}).get("citation_group"):
                    cited[g].append(p)
            for g, ps in sorted(cited.items()):
                if len(ps) > 1:
                    prods += [(f"or:{c}:{d}:{g}", {p: None}, 0) for p in sorted(ps)]
                    inputs[f"or:{c}:{d}:{g}"] = min(inputs.pop(p) for p in ps)
        if inputs:
            (stmt.__setitem__(c, inputs) if d == "statement" else derivs[c].append(inputs))
    for c in sorted(stmt.keys() | derivs.keys()):
        prods += [(c, {**stmt.get(c, {}), **d}, int(c in ctx.claims)) for d in derivs.get(c) or [{}]]
    heads = {h for h, _, _ in prods}
    prods += [(h, {w: None}, 0) for h, w in sorted(ctx.resolved.items())]  # the same occurrence
    prods += [(w, dict.fromkeys(ps), 0) for w, ps in sorted(ctx.parts.items()) if w not in heads]  # a whole = its parts
    adj, by_head, uses = {n: {} for n in (*ctx.logical, *(h for h, _, _ in prods))}, defaultdict(list), defaultdict(list)
    for i, (h, inputs, _) in enumerate(prods):
        by_head[h].append(i)
        for p, jid in inputs.items():
            uses[p].append(i)
            adj[p].setdefault(h, jid)
    comps = graph._tarjan(adj)
    cycles = [c for c in comps if len(c) > 1 or c[0] in adj[c[0]]]
    cyclic = {n for c in cycles for n in c}
    return SimpleNamespace(prods=prods, adj=adj, by_head=by_head, uses=uses, comps=comps, cyclic=cyclic,
                           cycles=[m for c in cycles if (m := [n for n in c if n in ctx.logical])],
                           dead=cyclic if ctx.policy["cycle_policy"] == "CONDENSE_V03" else set(),
                           roots={n for n in ctx.logical if n not in by_head})


def _base(ctx, g, base_set):
    return g.roots if base_set == "ALL_ROOTS" else g.roots & ctx.primitive


def _layers(ctx, g, base):
    """§4.1 top-down (Knuth): roots in B at 0, a production fires on its last finalized input, a node is final
    at its smallest fired value; nodes never finalized are ∞. Returns ({node: value}, {node: root classes})."""
    value, basis, tent, left = {}, {}, {r: (0, frozenset({_root_class(ctx, r)})) for r in base}, [len(p[1]) for p in g.prods]
    heap = sorted((0, r) for r in base)
    while heap:
        v, n = heapq.heappop(heap)
        if n in value:
            continue
        value[n], basis[n] = v, tent[n][1]
        for i in g.uses[n]:
            left[i] -= 1
            h, inputs, add = g.prods[i]
            if left[i] or h in value or h in g.dead:
                continue
            best = (max(value[x] for x in inputs) + add, frozenset().union(*(basis[x] for x in inputs)))
            if h not in tent or best[0] < tent[h][0]:
                tent[h] = best
                heapq.heappush(heap, (best[0], h))
    return value, basis


def _closure(g, own, trim=None):
    """{node: OR of own[m] over nodes m reached from it by >= 1 edge}, over the SCC condensation (§8.6)."""
    cid = {n: i for i, c in enumerate(g.comps) for n in c}
    inner, succ, pred = [0] * len(g.comps), [set() for _ in g.comps], [set() for _ in g.comps]
    for n, heads in g.adj.items():
        inner[cid[n]] |= own(n)
        for h in heads:
            if cid[h] != cid[n]:
                succ[cid[n]].add(cid[h])
                pred[cid[h]].add(cid[n])
    acc, left = [0] * len(g.comps), [len(s) for s in succ]
    ready = [i for i, k in enumerate(left) if not k]
    while ready:
        i = ready.pop()
        x = reduce(or_, (inner[j] | acc[j] for j in succ[i]), inner[i] if g.comps[i][0] in g.cyclic else 0)
        acc[i] = trim(x) if trim else x
        for k in pred[i]:
            left[k] -= 1
            if not left[k]:
                ready.append(k)
    return {n: acc[cid[n]] for n in g.adj}


def _bottom(x):
    out = 0
    for _ in range(SKETCH_K):
        if not x:
            break
        out |= x & -x
        x &= x - 1
    return out


def _reach(g, sources, limit=math.inf):
    """0-1 BFS by junction count (OR-group nodes cost 0): ({node: depth}, {node: (previous, junction)})."""
    dist, parent, queue = {}, {}, deque()

    def push(m, n, d, jid):
        d += jid is not None
        if d <= limit and d < dist.get(n, math.inf):
            dist[n], parent[n] = d, (m, jid)
            (queue.append if jid else queue.appendleft)((n, d))
    for s in sorted(sources):
        for h, jid in g.adj[s].items():
            push(s, h, 0, jid)
    while queue:
        n, d = queue.popleft()
        if d == dist[n]:
            for h, jid in g.adj[n].items():
                push(n, h, d, jid)
    return dist, parent


def _date(ctx, n=None, work=None):
    """A claim or request: its stating paper's v1 date. A work (or a work-level claim's work): the earliest of its
    in-view versions' v1 dates and Work.year (§8.2)."""
    pvs, row = ctx.view["nodes"]["PaperVersion"], ctx.claims.get(n) or ctx.holders.get(n) or {}
    if "paper_version_id" in row:
        return pvs.get(row["paper_version_id"], {}).get("date_v1", UNKNOWN_DATE)
    work = work or min(ctx.comp(row["work_id"]))
    dates = [pvs[p]["date_v1"] for p in ctx.versions[work] if p in pvs]
    dates += [{"value": f"{y:04d}", "kind": "BIB_YEAR", "precision": "YEAR", "source": "Work.year"}
              for w in ctx.comp(work) if (y := ctx.view["nodes"]["Work"].get(w, {}).get("year")) is not None]
    return min(dates, key=_date_key, default=UNKNOWN_DATE)


def _date_key(d):
    """Year precision; UNKNOWN in its own bucket, after every dated subject (§8.2)."""
    return (1, 0) if d["kind"] == "UNKNOWN" else (0, int(d["value"][:4]))


def _evaluate(ctx, drop=frozenset()):
    """Graphs, layers, paper closures and candidates of one leg set; drop: the legs a perturbation removed."""
    policy, reading = ctx.policy, ctx.policy["establishment_reading"]
    establishes = lambda j: reading["mode"] == "UNION" or j["reading_method"] in reading["methods"]
    counts = lambda j: j["reading_method"] in policy["importance_methods"]
    rows = _scope(ctx, drop)
    i_rows = [r for r in rows if counts(r[0])]
    ev = SimpleNamespace(ctx=ctx, rows=rows, graphed=[r for r in rows if establishes(r[0]) or counts(r[0])],
                         E=_graph(ctx, [r for r in rows if establishes(r[0])], False),
                         L=_graph(ctx, i_rows, True), U=_graph(ctx, i_rows, False))
    ev.value, ev.basis = _layers(ctx, ev.E, _base(ctx, ev.E, policy["base_set"]))
    ev.papers = {k: _closure(getattr(ev, k), ctx.cbit) for k in "LU"}
    works = _work_cands(ev)
    ev.works = {c["subject_id"]: c for c in works}
    ev.cands = [c for c in (*(_claim_cand(ev, n) for n in sorted(ctx.claims)), *works) if c["list"]]
    return ev


def _claim_cand(ev, n):
    """A kind list needs agreeing kinds (every reading 'definition', or all theorem-like); a low claim of another or
    disputed kind goes to LOW_LAYER_BY_OPEN_PREMISES. EXTRACT only for a paper claim never model-extracted."""
    ctx, lay, basis, kinds = ev.ctx, ev.value.get(n), ev.basis.get(n, frozenset()), ev.ctx.kinds.get(n, set())
    no_support = n in ev.E.roots and _root_class(ctx, n) in NO_SUPPORT
    low = lay is not None and lay <= 1
    kind_list = ("DEFINITIONS" if kinds == {"definition"} else
                 "THEOREM_LIKE" if kinds and kinds <= graph._THEOREM_KINDS else None)
    name = (kind_list if no_support or (low and basis <= ALLOWED_BASIS) else None) or (
        "LOW_LAYER_BY_OPEN_PREMISES" if low else None)
    pending = ctx.claims[n]["origin"] == "PAPER_VERSION" and "MODEL_EXTRACTION" not in ctx.examined[n]
    action = ("EXTRACT" if pending else "MATCH_REQUESTS" if "EXTERNAL_REQUEST" in basis else
              "HUMAN_REVIEW" if no_support or basis - ALLOWED_BASIS else "LIBRARY_AUDIT")
    blockers = ({"OPEN_PREMISE:" + b for b in basis - ALLOWED_BASIS} | ({"NO_MODEL_EXTRACTION"} if pending else set())
                | ({"NO_SUPPORT_PROPOSED"} if no_support else set()) | (set() if kind_list else {"UNLISTED_KIND"}))
    return _cand(ev, name, "CLAIM", n, [n], ctx.bit(n), _date(ctx, n), "INFINITY" if lay is None else lay,
                 basis, action, blockers)


def _work_cands(ev):
    ctx, pools, out = ev.ctx, defaultdict(list), []
    for h, works in sorted(ctx.pool.items()):
        for w in works:
            pools[w].append(h)
    for w, requests in sorted(pools.items()):
        resolved = min(((ev.value[r], r) for r in requests if r in ev.E.by_head and r in ev.value), default=None)
        lay, basis = ("UNRESOLVED", frozenset()) if resolved is None else (resolved[0], ev.basis[resolved[1]])
        own = reduce(or_, (1 << ctx.pidx[p] for p in ctx.versions[w] if p in ctx.pidx), 0)
        terminal = {ctx.view["nodes"]["Work"].get(x, {}).get("terminal_kind") for x in ctx.comp(w)}
        name = "WORKS" if (lay == "UNRESOLVED" or lay <= 1) and basis <= ALLOWED_BASIS else (
            "LOW_LAYER_BY_OPEN_PREMISES" if lay != "UNRESOLVED" and lay <= 1 else None)
        action = (("MATCH_REQUESTS" if ctx.versions[w] else "ACQUIRE_SOURCE" if "ARXIV_SOURCE_AVAILABLE" in terminal
                   else "LIBRARY_AUDIT") if lay == "UNRESOLVED" else "MATCH_REQUESTS" if "EXTERNAL_REQUEST" in basis
                  else "HUMAN_REVIEW" if basis - ALLOWED_BASIS else "LIBRARY_AUDIT")
        blockers = {"OPEN_PREMISE:" + b for b in basis - ALLOWED_BASIS} | ({"WORK_UNRESOLVED"} if lay == "UNRESOLVED" else set())
        out.append(_cand(ev, name, "WORK", w, requests, own, _date(ctx, work=w), lay, basis, action, blockers))
    return out


def _cand(ev, name, kind, subject, sources, own, date, layer, basis, action, blockers):
    bits = reduce(or_, (ev.papers["L"][s] for s in sources), 0) & ~own
    return {"list": name, "subject_kind": kind, "subject_id": subject, "sources": sources, "own": own, "date": date,
            "layer": layer, "layer_basis": sorted(basis), "next_action": action, "blockers": sorted(blockers),
            "idx": [i for i in range(bits.bit_length()) if bits >> i & 1]}


def _ranked(cands, threshold, weight=None):
    """[(cand, count, position, rank lower, rank upper)] per list: dependent_papers.lower desc, date asc, layer
    asc; ties share a rank interval and are ordered by id (§8.4). weight: paper multiplicities (bootstrap)."""
    count = (lambda c: len(c["idx"])) if weight is None else (lambda c: sum(weight[i] for i in c["idx"]))
    key = lambda cc: (-cc[1], _date_key(cc[0]["date"]), (1, 0) if isinstance(cc[0]["layer"], str) else (0, cc[0]["layer"]))
    out = []
    for name in LISTS:
        scored = sorted(((c, k) for c in cands if c["list"] == name and (k := count(c)) >= threshold),
                        key=lambda cc: (key(cc), cc[0]["subject_id"]))
        for _, tie in groupby(enumerate(scored, 1), key=lambda t: key(t[1])):
            tie = list(tie)
            out += [(c, k, pos, tie[0][0], tie[-1][0]) for pos, (c, k) in tie]
    return out


def _top(ranked, k):
    return {(c["list"], c["subject_id"]) for c, _, pos, _, _ in ranked if pos <= k}


def _importance(ev, sketch, sources, own, exact):
    """(§8.2 brackets over L and U, reach). exact (a nominated subject): one unbounded traversal per graph, returned
    as {graph: (dist, parent)} for witnesses and knockouts; otherwise depth <= 3 and a bottom-k dependents estimate.
    dependents never count the subject itself, also when it reaches itself through a cycle; dependent_papers never
    count its own paper. dependent_topics (exact subjects only) counts the arXiv categories of the dependent papers."""
    ctx, reach = ev.ctx, {}
    out = {"dependent_papers": {}, "dependent_papers_by_depth": {d: {} for d in "123"}, "dependents": {}}
    for bound, k in (("lower", "L"), ("upper", "U")):
        closure = reduce(or_, (ev.papers[k][s] for s in sources), 0) & ~own
        out["dependent_papers"][bound] = closure.bit_count()
        if exact:
            out.setdefault("dependent_topics", {})[bound] = _topics(ctx, closure)
        reach[k] = _reach(getattr(ev, k), sources, math.inf if exact else 3)
        for d in "123":
            bits = reduce(or_, (ctx.cbit(m) for m, x in reach[k][0].items() if x <= int(d)), 0)
            out["dependent_papers_by_depth"][d][bound] = (bits & ~own).bit_count()
        if exact:
            out["dependents"][bound] = sum(bool(ctx.cbit(m)) and m not in sources for m in reach[k][0])
        else:  # a cyclic claim source is in its own closure (its sketch bit or the estimate): remove it
            x, cyclic = _bottom(reduce(or_, (sketch[k][s] for s in sources), 0)), getattr(ev, k).cyclic
            estimate = x.bit_count() if x.bit_count() < SKETCH_K else round((SKETCH_K - 1) * len(ctx.rank) / x.bit_length())
            out["dependents"][bound] = max(0, estimate - sum(s in ctx.rank and s in cyclic for s in sources))
    out["dependents"]["exactness"] = "EXACT" if exact else "ESTIMATED"
    return out, reach if exact else None


def _witness(ev, cand, dist, parent):
    """One shortest path in L per dependent paper: [subject, (junction, node)...] to that paper's nearest claim."""
    ctx, sources, best = ev.ctx, set(cand["sources"]), {}
    for m, d in dist.items():
        if ctx.cbit(m) and not ctx.cbit(m) & cand["own"]:
            best[ctx.cbit(m)] = min(best.get(ctx.cbit(m), (d, m)), (d, m))
    paths = []
    for _, (_, m) in sorted(best.items()):
        path, n = [m], m
        while n not in sources:
            n, jid = parent[n]
            path += [x for x in (jid, n) if x is not None and not x.startswith("or:")]
        paths.append(([cand["subject_id"]] if cand["subject_kind"] == "WORK" else []) + path[::-1])
    return paths


def _necessary(ev, key, finite, x, desc):
    """Claims finite before and ∞ after fixing x at ∞, roots fixed (§8.2), by graph._supported on x's descendants
    desc (x's reach in graph key)."""
    g = getattr(ev, key)
    if x not in finite:
        return 0
    groups = {i: {"target": g.prods[i][0], "members": list(g.prods[i][1])}
              for h in desc.keys() - {x} - g.dead for i in g.by_head[h]}
    after = graph._supported(finite - desc.keys() - {x}, groups)
    return sum(v != x and bool(ev.ctx.cbit(v)) and v in finite and v not in after for v in desc)


def _primary_bound(view, manifest, policy, admission, corpus, coverage):
    """A PRIMARY run: the policy is exactly the one gates.primary_policy derives from the corpus manifest and its P0 GO,
    coverage is complete, and every MODEL_EXTRACTION reading in the view is of the corpus extraction policy."""
    import gates  # gates imports autoeval, which imports this module's peers; import at call time
    if admission is None or corpus is None or coverage is None or policy["admission_gate"] is None:
        raise ValueError("PRIMARY_ANALYSIS_NEEDS_A_P0_ADMISSION_THE_CORPUS_AND_ITS_COVERAGE")
    if manifest["corpus_id"] != corpus["corpus_id"]:
        raise ValueError("PRIMARY_MANIFEST_OF_ANOTHER_CORPUS")
    if policy != gates.primary_policy(corpus, admission) or not set(policy["importance_methods"]) <= set(admission["admitted_methods"]):
        raise ValueError("PRIMARY_POLICY_IS_NOT_BOUNDED_BY_ITS_P0_ADMISSION")
    gates.require_equal_coverage(coverage, corpus)
    version = corpus["extraction"]["method_version"]
    rows = [*view["nodes"]["ClaimReading"].values(), *view["nodes"]["Junction"].values()]
    if any(r.get("method", r.get("reading_method")) == "MODEL_EXTRACTION" and r["method_version"] != version for r in rows):
        raise ValueError("PRIMARY_VIEW_MIXES_EXTRACTION_VERSIONS")


def analyze(view, manifest, policy, dispositions=None, *, admission=None, corpus=None, coverage=None, edge_precision=None):
    """{metrics, nominations, diagnostics, bootstrap, perturbation}, every part stamped with policy_id,
    policy_sha256 and manifest_id. edge_precision: {(method, role, premise kind): p̂} for every leg the policy's
    graphs use, loaded by the caller from policy.edge_precision.estimates (required iff that is set); premise kind =
    the agreed reading kind of a Claim premise (UNKNOWN when its readings disagree or it has none) or the kind of a
    Placeholder premise. Every statistic carries the policy's count_basis (I-14). A PRIMARY policy needs admission (the
    P0 GateDecision it names), corpus (its CorpusManifest; the policy must equal gates.primary_policy of the two) and
    coverage (corpus.coverage_report, complete), and a view whose MODEL_EXTRACTION rows are all of the corpus extraction
    policy (§11.3). match_coverage stays null until S7 attempt records exist in the ledger."""
    contracts.validate("AnalysisPolicy", policy)
    contracts.validate("DeltaSetManifest", manifest)
    if policy["status"] == "PRIMARY":
        _primary_bound(view, manifest, policy, admission, corpus, coverage)
    if sorted(manifest["deltas"]) != sorted(view["deltas"]):
        raise ValueError("the view is not the merge of this manifest's deltas")
    if (policy["edge_precision"] is None) != (edge_precision is None):
        raise ValueError("edge_precision estimates are required iff the policy enables EDGE_PRECISION_V1")
    stamp = {"policy_id": policy["policy_id"], "policy_sha256": digest(canonical(policy)),
             "manifest_id": manifest["manifest_id"]}
    head = {"contract_version": CONTRACT_VERSION, "policy_id": policy["policy_id"], "manifest_id": manifest["manifest_id"],
            "count_basis": policy["count_basis"]}
    ctx, rule, replicates = _index(view, policy, dispositions or {}), policy["nomination"], policy["bootstrap"]["replicates"]
    ev = _evaluate(ctx)
    if edge_precision is not None:
        kind = lambda n: ctx.holders[n]["kind"] if n in ctx.holders else ctx.kind.get(n, "UNKNOWN")
        legs = [(j["id"], p, (j["reading_method"], l["role"], kind(l["premise_id"]))) for j, ls in ev.graphed for p, l in ls]
        if missing := sorted({key for *_, key in legs} - edge_precision.keys()):
            raise ValueError(f"no edge precision estimate for {missing}")
    rank = ctx.rank = {c: i for i, c in enumerate(sorted((c for c in ctx.claims if ctx.cbit(c)), key=lambda c: order_key(policy["policy_id"], c)))}
    sketch = {k: _closure(getattr(ev, k), lambda n: 1 << rank[n] if n in rank else 0, _bottom) for k in "LU"}
    ranked = _ranked(ev.cands, rule["threshold"])
    chosen = {c["subject_id"] for c, *_ in ranked}
    finite = {(k, b): set(_layers(ctx, getattr(ev, k), _base(ctx, getattr(ev, k), b))[0]) for k in "LU" for b in BASES}
    uses = defaultdict(Counter)
    for j, ls in ev.rows:
        for p, l in ls:
            uses[l["premise_id"]][j["reading_method"], l["role"], ctx.legs.get(leg_id(j["id"], p), UNREVIEWED)] += 1

    metrics, reach = {}, {}
    for n in sorted(ctx.logical):
        root = n in ev.E.roots
        importance, reach[n] = _importance(ev, sketch, [n], ctx.bit(n), n in chosen)
        necessary = {b: (dict(zip(("lower", "upper"), sorted(_necessary(ev, k, finite[k, b], n, reach[n][k][0]) for k in "LU")))
                         if reach[n] else None) for b in BASES}
        metrics[n] = {"kind": "NodeMetrics", **head, "subject_kind": "CLAIM" if n in ctx.claims else "PLACEHOLDER",
                      "subject_id": n, "layer": ev.value.get(n, "INFINITY"), "layer_basis": sorted(ev.basis.get(n, ())),
                      "route_status": "FINITE" if n in ev.value else "ROUTE_UNDETERMINED", "in_cycle": n in ev.E.cyclic,
                      **importance, "necessary_dependents": necessary,
                      "direct_uses": sum(uses[n].values()), "date": _date(ctx, n),
                      "root_class": _root_class(ctx, n) if root else None,
                      "root_examined_by": sorted(ctx.examined[n]) if root else [],
                      "uncertainty": [{"method": m, "role": r, "disposition": d, "legs": k}
                                      for (m, r, d), k in sorted(uses[n].items())]}
    for w, c in ev.works.items():
        importance, reach[w] = _importance(ev, sketch, c["sources"], c["own"], w in chosen)
        metrics[w] = {"kind": "NodeMetrics", **head, "subject_kind": "WORK", "subject_id": w, "layer": c["layer"],
                      "layer_basis": c["layer_basis"], **importance, "date": c["date"],
                      "citing_claims": len({ctx.holders[r]["created_by_claim_id"] for r in c["sources"]}),
                      "citing_papers": len({ctx.holders[r]["paper_version_id"] for r in c["sources"]})}

    keys = {(c["list"], c["subject_id"]) for c, *_ in ranked}
    boot, rng = Counter(), random.Random(policy["bootstrap"]["seed"])
    for _ in range(replicates if ctx.counted else 0):
        weight = [0] * len(ctx.papers)
        for _ in ctx.counted:  # resample the counted papers only; the rest weigh nothing
            weight[ctx.counted[rng.randrange(len(ctx.counted))]] += 1
        boot.update(_top(_ranked(ev.cands, rule["threshold"], weight), rule["top_k"]) & keys)
    survival = None
    if edge_precision is not None:
        survival, rng = Counter(), random.Random(policy["bootstrap"]["seed"] + "/EDGE_PRECISION_V1")
        for _ in range(replicates):
            drop = frozenset((jid, p) for jid, p, key in legs if rng.random() >= edge_precision[key])
            survival.update(_top(_ranked(_evaluate(ctx, drop).cands, rule["threshold"]), rule["top_k"]) & keys)

    nominations = []
    for c, k, pos, lo, hi in ranked:
        key = (c["list"], c["subject_id"])
        nominations.append({
            "kind": "FoundationNomination", **{x: head[x] for x in ("contract_version", "policy_id", "manifest_id")},
            "nomination_id": address("nomination", {**stamp, "rule": rule["rule"], "list": key[0], "subject_id": key[1]}),
            "rule": rule["rule"], "list": c["list"], "subject_kind": c["subject_kind"], "subject_id": c["subject_id"],
            "count_basis": policy["count_basis"], "rank_interval": {"lower": lo, "upper": hi},
            "dependent_papers": metrics[c["subject_id"]]["dependent_papers"],
            "dependent_topics": metrics[c["subject_id"]]["dependent_topics"], "date": c["date"], "layer": c["layer"],
            "layer_basis": c["layer_basis"], "witness_paths": _witness(ev, c, *reach[c["subject_id"]]["L"]),
            "blockers": c["blockers"], "next_action": c["next_action"], "match_coverage": None,
            "bootstrap_top_k_fraction": boot[key] / replicates,
            "edge_precision_top_k_survival": None if survival is None else survival[key] / replicates})
    for row in metrics.values():
        contracts.validate("NodeMetrics", row)
    for row in nominations:
        contracts.validate("FoundationNomination", row)
    frac = lambda counts: {n["nomination_id"]: counts[n["list"], n["subject_id"]] / replicates for n in nominations}
    lower_cycles = {tuple(c) for c in ev.L.cycles}
    return {**stamp, "metrics": list(metrics.values()), "nominations": nominations,
            "diagnostics": {**stamp, "CYCLE": ev.E.cycles,
                            "READING_CONFLICT_CYCLE": [c for c in ev.U.cycles if tuple(c) not in lower_cycles],
                            "CORRECTS_BLOCKED": sorted(ctx.blocked)},
            "bootstrap": {**stamp, "scheme": "PAPER_REWEIGHT_V1", "replicates": replicates,
                          "seed": policy["bootstrap"]["seed"], "top_k": rule["top_k"], "top_k_fraction": frac(boot)},
            "perturbation": None if survival is None else {
                **stamp, "scheme": "EDGE_PRECISION_V1", "replicates": replicates, "top_k": rule["top_k"],
                "estimates": policy["edge_precision"]["estimates"], "top_k_survival": frac(survival)}}
