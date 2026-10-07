"""analysis.py and review_sample.py on small hand-built views with known answers (synthetic, offline)."""
import hashlib
import json

import pytest

import analysis
import review_sample
from delta import LABELS, make_manifest

DELTA = "delta:" + "d" * 64
MANIFEST = make_manifest("corpus:" + "c" * 64, [DELTA], created_at="2026-09-25T00:00:00+00:00")
POLICY = {"kind": "AnalysisPolicy", "contract_version": "0.4.0", "policy_id": "policy:" + "e" * 64, "status": "EXPLORATORY",
          "establishment_reading": {"mode": "UNION"},
          "importance_methods": ["DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION", "MODEL_MATCH", "HUMAN"],
          "work_identity": "EXPLICIT_IDS_ONLY", "citation_group_semantics": "AND", "cycle_policy": "FIXPOINT",
          "base_set": "ALL_ROOTS", "include_part_expansions": True, "traverse": "SAMPLE_ONLY", "count_basis": "SAMPLE_ONLY",
          "admission_gate": None,
          "nomination": {"rule": "FOUNDATION_V1", "threshold": 1, "top_k": 2},
          "bootstrap": {"scheme": "PAPER_REWEIGHT_V1", "replicates": 25, "seed": "seed-1"}, "edge_precision": None}
REF = {"path": "artifacts/p.json", "sha256": "sha256:" + "f" * 64, "byte_size": 1}
hx = lambda name: hashlib.sha256(name.encode()).hexdigest()
pv = lambda n: f"arxiv:2101.0000{n}v1"
proof = lambda name: "proof:sha256:" + hx(name)


class V:
    """A merged DeltaSetView built by name: v.id['a'] is the claim, request or work called 'a'."""

    def __init__(self):
        self.nodes, self.edges, self.id = {label: {} for label in LABELS}, {}, {}

    def _put(self, label, prefix, name, methods=("DETERMINISTIC_ANCHOR",), **row):
        i = self.id[name] = row.pop("id", None) or f"{prefix}:{hx(name)}"
        self.nodes[label][i] = {"id": i, **row, "asserted_by": [DELTA], "methods": list(methods)}
        return i

    def paper(self, n, year=2021):
        date = {"value": f"{year}-01-01", "kind": "ARXIV_V1", "precision": "DAY", "source": "synthetic"}
        self._put("PaperVersion", "", f"pv{n}", id=pv(n), date_v1=date)

    def claim(self, name, paper=1, kind="theorem", primitive=False, methods=("DETERMINISTIC_ANCHOR",)):
        """kind: one kind for every reading, or one per method."""
        if pv(paper) not in self.nodes["PaperVersion"]:
            self.paper(paper, 2020 + paper)
        c = self._put("Claim", "claim", name, methods, origin="PAPER_VERSION", paper_version_id=pv(paper),
                      occurrence_ids=["occ:" + hx(name)], part="whole")
        for m, k in zip(methods, [kind] * len(methods) if isinstance(kind, str) else kind):
            self._put("ClaimReading", "reading", name + m, claim_id=c, method=m, kind=k)
        if primitive:
            self._put("PrimitiveAssertion", "primitive", name + "!", ["HUMAN"], claim_id=c, method="HUMAN", basis="AXIOM")
        return c

    def request(self, name, citing, work=None, group=None):
        c = self.nodes["Claim"][self.id[citing]]
        bib = "bib:" + hx(name)
        extra = {"citation_group": group} if group else {}
        r = self._put("Placeholder", "placeholder", name, kind="EXTERNAL_REQUEST", paper_version_id=c["paper_version_id"],
                      created_by_claim_id=c["id"], citing_derivation_id=proof(citing), bib_entry_id=bib, **extra)
        if work:
            self.edge("RESOLVES_TO", bib, self.id[work], method="HOST_RULE", basis="arxiv id")
        return r

    def work(self, name, terminal="ARXIV_SOURCE_AVAILABLE", year=None):
        return self._put("Work", "work", name, ["HOST_RULE"], identity_basis="BIB_DIGEST", work_kind="ARTICLE",
                         terminal_kind=terminal, **({"year": year} if year else {}))

    def junction(self, conclusion, premises, derivation=None, method="DETERMINISTIC_ANCHOR", flags=()):
        c = self.id[conclusion]
        if derivation is None:
            derivation = (f"source:{pv(1)}:sha256:{hx(conclusion)}" if c.startswith("placeholder:") else proof(conclusion))
        site = "STATEMENT" if derivation == "statement" else "PROOF"
        legs = [{"premise_id": self.id[p], "role": "UNCLASSIFIED", "use_site": site, "flags": list(flags)} for p in premises]
        return self._put("Junction", "junction", f"{conclusion}|{derivation}|{method}|{premises}", [method],
                         conclusion_id=c, derivation_id=derivation, reading_method=method, method_version="1", legs=legs,
                         grouping_basis="synthetic")

    def edge(self, type_, start, end, **props):
        i = "rel:" + hx(f"{type_}{start}{end}")
        self.edges[i] = {"id": i, "type": type_, "start_id": start, "end_id": end, "props": props, "asserted_by": [DELTA]}
        return i

    def run(self, dispositions=None, estimates=None, **policy):
        view = {"deltas": [DELTA], "nodes": self.nodes, "edges": self.edges}
        self.result = analysis.analyze(view, MANIFEST, {**POLICY, **policy}, dispositions, edge_precision=estimates)
        self.m = {r["subject_id"]: r for r in self.result["metrics"]}
        return self.result

    def layer(self, name):
        return self.m[self.id[name]]["layer"]

    def nominated(self, name):
        return [n for n in self.result["nominations"] if n["subject_id"] == self.id[name]]


def test_and_takes_max_or_takes_min():
    v = V()
    for name in ("r1", "r2", "a", "b", "c", "d"):
        v.claim(name)
    v.junction("a", ["r1"])
    v.junction("b", ["a", "r1"])  # AND: 1 + max(1, 0)
    v.junction("c", ["b"])  # OR over two derivations: 1 + min(2, 0)
    v.junction("c", ["r2"], derivation=proof("c-alt"))
    v.junction("d", ["b"])
    v.run()
    assert [v.layer(n) for n in ("r1", "a", "b", "c", "d")] == [0, 1, 2, 1, 3]
    assert v.m[v.id["a"]]["layer_basis"] == ["NO_SUPPORT_PROPOSED"] and v.m[v.id["r1"]]["root_class"] == "NO_SUPPORT_PROPOSED"
    assert v.m[v.id["a"]]["root_class"] is None and v.m[v.id["b"]]["route_status"] == "FINITE"
    assert v.m[v.id["r1"]]["direct_uses"] == 2 and v.m[v.id["r1"]]["uncertainty"] == [
        {"method": "DETERMINISTIC_ANCHOR", "role": "UNCLASSIFIED", "disposition": "UNREVIEWED", "legs": 2}]
    v.run(base_set="PRIMITIVE_ASSERTED")  # no PrimitiveAssertion: every root is outside B
    assert all(v.layer(n) == "INFINITY" for n in ("r1", "a", "b", "c", "d"))


def test_statement_junction_joins_every_derivation():
    v = V()
    for name in ("x0", "x1", "x2", "c", "c2", "c3"):
        v.claim(name)
    v.junction("x1", ["x0"])
    v.junction("x2", ["x1"])
    v.junction("c", ["x2"], derivation="statement")
    v.junction("c", ["x0"])  # 1 + max(statement 2, derivation 0)
    v.junction("c2", ["x0"], derivation="statement")  # statement alone
    v.junction("c3", ["x0"], derivation="statement", method="MODEL_EXTRACTION")
    v.junction("c3", ["x2"])  # 1 + max(0, 2)
    v.run()
    assert (v.layer("c"), v.layer("c2"), v.layer("c3")) == (3, 1, 3)


def test_statement_junctions_of_two_readings_combine_by_the_establishment_reading():
    v = V()
    for name in ("x", "y", "y1", "y0", "c"):
        v.claim(name)
    v.junction("y1", ["y0"])
    v.junction("y", ["y1"])
    v.junction("c", ["x"], derivation="statement")
    v.junction("c", ["y"], derivation="statement", method="MODEL_EXTRACTION")
    v.run()
    assert v.layer("c") == 1 + v.layer("y") == 3  # UNION: both readings' statement legs
    v.run(establishment_reading={"mode": "ONLY", "methods": ["DETERMINISTIC_ANCHOR"]})
    assert v.layer("c") == 1 + v.layer("x") == 1  # ONLY: the admitted reading's legs


def test_pure_two_cycle_is_infinite_and_poisons_downstream_only():
    v = V()
    for name in ("a", "b", "d", "r", "e"):
        v.claim(name)
    v.junction("a", ["b"])
    v.junction("b", ["a"])
    v.junction("d", ["a"])
    v.junction("e", ["a"], derivation=proof("e1"))
    v.junction("e", ["r"], derivation=proof("e2"))  # an OR exit around the dead cycle
    v.run()
    a, d = v.m[v.id["a"]], v.m[v.id["d"]]
    assert (a["layer"], a["route_status"], a["in_cycle"]) == ("INFINITY", "ROUTE_UNDETERMINED", True)
    assert (d["layer"], d["in_cycle"], v.layer("e")) == ("INFINITY", False, 1)
    assert v.result["diagnostics"]["CYCLE"] == [sorted([v.id["a"], v.id["b"]])]


def test_cycle_with_exit_is_finite_under_fixpoint_and_dead_under_condense():
    v = V()
    for name in ("a", "b", "r", "e"):
        v.claim(name)
    v.junction("a", ["b"], derivation=proof("a1"))
    v.junction("a", ["r"], derivation=proof("a2"))
    v.junction("b", ["a"])
    v.junction("e", ["b"])
    v.run()
    assert (v.layer("a"), v.layer("b"), v.layer("e")) == (1, 2, 3)
    assert v.m[v.id["b"]]["in_cycle"] and v.m[v.id["b"]]["route_status"] == "FINITE"
    v.run(cycle_policy="CONDENSE_V03")
    assert (v.layer("a"), v.layer("b"), v.layer("e")) == ("INFINITY",) * 3


def two_papers(v):
    """Paper 1: primitive definition p0 <- lemma p1. Paper 2: q uses request R, which MODEL_MATCH resolves to p1."""
    v.claim("p0", 1, "definition", primitive=True)
    v.claim("p1", 1, "lemma", methods=("DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION"))
    v.junction("p1", ["p0"])
    v.claim("q", 2, "theorem")
    v.request("R", "q")
    v.junction("q", ["R"])
    return v


def test_request_is_transparent_across_papers():
    v = two_papers(V())
    v.junction("R", ["p1"], method="MODEL_MATCH")
    v.run()
    assert (v.layer("p1"), v.layer("R"), v.layer("q")) == (1, 1, 2)
    assert v.m[v.id["q"]]["layer_basis"] == ["PRIMITIVE"]
    assert v.m[v.id["p0"]]["dependent_papers"] == {"lower": 1, "upper": 1}
    assert v.m[v.id["p0"]]["dependent_papers_by_depth"] == {"1": {"lower": 0, "upper": 0}, "2": {"lower": 0, "upper": 0},
                                                            "3": {"lower": 1, "upper": 1}}
    u = two_papers(V())  # unresolved: a request root is in ALL_ROOTS, outside PRIMITIVE_ASSERTED
    u.run()
    assert (u.layer("R"), u.layer("q"), u.m[u.id["R"]]["root_class"]) == (0, 1, "EXTERNAL_REQUEST")
    u.run(base_set="PRIMITIVE_ASSERTED")
    assert (u.layer("p1"), u.layer("q")) == (1, "INFINITY")


def test_citation_group_and_or():
    v = two_papers(V())
    del v.nodes["Placeholder"][v.id["R"]]
    v.nodes["Junction"].clear()
    v.junction("p1", ["p0"])
    v.request("R1", "q", group="anchor-1")
    v.request("R2", "q", group="anchor-1")
    v.junction("q", ["R1", "R2"])
    v.junction("R1", ["p1"], method="MODEL_MATCH")
    v.run(base_set="PRIMITIVE_ASSERTED")
    assert v.layer("q") == "INFINITY"  # AND: the unresolved R2 is required
    v.run(base_set="PRIMITIVE_ASSERTED", citation_group_semantics="OR")
    assert v.layer("q") == 2 and not any(r["subject_id"].startswith("or:") for r in v.result["metrics"])


def test_importance_bracket_lower_needs_agreement_upper_is_union():
    v = V()
    for name in ("a", "b", "c"):
        v.claim(name, 2)
    v.junction("c", ["a", "b"], derivation=proof("c"))
    v.junction("c", ["a"], derivation=proof("c"), method="MODEL_EXTRACTION")
    v.claim("d", 3)
    v.request("R", "d")
    v.junction("d", ["R"])
    v.junction("R", ["c"], method="MODEL_MATCH")
    v.run()
    a, b = v.m[v.id["a"]], v.m[v.id["b"]]
    assert (a["dependents"]["lower"], a["dependents"]["upper"], b["dependents"]["lower"], b["dependents"]["upper"]) == (2, 2, 0, 2)
    assert (a["dependent_papers"], b["dependent_papers"]) == ({"lower": 1, "upper": 1}, {"lower": 0, "upper": 1})
    assert v.layer("c") == 1 and b["direct_uses"] == 1  # UNION establishment keeps b as a premise
    v.run(importance_methods=["DETERMINISTIC_ANCHOR", "MODEL_MATCH"])  # one admitted reading: its legs are the lower bound
    assert v.m[v.id["b"]]["dependent_papers"] == {"lower": 1, "upper": 1}


def test_reading_conflict_cycle_is_diagnosed_not_propagated_to_lower_bound():
    v = V()
    for name in ("a", "b", "r"):
        v.claim(name)
    v.junction("a", ["b"], derivation=proof("a"))
    v.junction("a", ["r"], derivation=proof("a"), method="MODEL_EXTRACTION")
    v.junction("b", ["a"])
    v.run()
    pair = sorted([v.id["a"], v.id["b"]])
    assert v.result["diagnostics"]["READING_CONFLICT_CYCLE"] == [pair] == v.result["diagnostics"]["CYCLE"]
    assert v.layer("a") == "INFINITY"  # the UNION establishment reading needs b and r jointly
    v.run(establishment_reading={"mode": "ONLY", "methods": ["MODEL_EXTRACTION"]})
    assert (v.layer("a"), v.result["diagnostics"]["CYCLE"]) == (1, [])


def knockout_view():
    v = V()
    v.claim("r", 1, "definition", primitive=True)
    v.claim("a", 1, "lemma", methods=("DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION"))
    v.junction("a", ["r"])
    v.claim("q1", 2)
    v.claim("q2", 2)
    v.claim("s", 2, "definition", primitive=True)
    v.request("R1", "q1")
    v.request("R2", "q2")
    v.junction("q1", ["R1"])
    v.junction("q2", ["R2"], derivation=proof("q2a"))
    v.junction("q2", ["s"], derivation=proof("q2b"))  # q2 survives r's knockout through s
    v.junction("R1", ["a"], method="MODEL_MATCH")
    v.junction("R2", ["a"], method="MODEL_MATCH")
    return v


def test_knockout_counts_necessary_dependents_with_roots_fixed():
    v = knockout_view()
    v.run()
    r, a = v.m[v.id["r"]], v.m[v.id["a"]]
    assert r["necessary_dependents"] == {"ALL_ROOTS": {"lower": 2, "upper": 2}, "PRIMITIVE_ASSERTED": {"lower": 2, "upper": 2}}
    assert a["necessary_dependents"]["ALL_ROOTS"] == {"lower": 1, "upper": 1}
    assert r["dependents"] == {"lower": 3, "upper": 3, "exactness": "EXACT"}
    assert v.m[v.id["q1"]]["necessary_dependents"] == {"ALL_ROOTS": None, "PRIMITIVE_ASSERTED": None}
    assert v.m[v.id["q1"]]["dependents"]["exactness"] == "ESTIMATED"


def test_foundation_v1_lists_ranks_actions_and_witnesses():
    v = knockout_view()
    v.claim("t", 1, "theorem")  # no support proposed, never model-extracted, used from paper 2
    v.claim("r2", 1, "definition", primitive=True)  # ties with r on every ranking key
    for request, target in (("R3", "t"), ("R4", "r2")):
        v.request(request, "q1")
        v.junction("q1", [request], derivation=proof(request))
        v.junction(request, [target], method="MODEL_MATCH")
    v.run()
    r, r2, a, t = (v.nominated(n)[0] for n in ("r", "r2", "a", "t"))
    assert (r["list"], r["layer"], r["layer_basis"], r["next_action"]) == ("DEFINITIONS", 0, ["PRIMITIVE"], "EXTRACT")
    assert r["rank_interval"] == r2["rank_interval"] == {"lower": 1, "upper": 2}  # tie, ordered by id inside
    assert (a["list"], a["next_action"], a["blockers"], a["rank_interval"]) == ("THEOREM_LIKE", "LIBRARY_AUDIT", [], {"lower": 2, "upper": 2})
    assert (t["list"], t["next_action"], t["rank_interval"]) == ("THEOREM_LIKE", "EXTRACT", {"lower": 1, "upper": 1})
    assert {"NO_MODEL_EXTRACTION", "NO_SUPPORT_PROPOSED"} <= set(t["blockers"])
    path = r["witness_paths"][0]
    assert len(r["witness_paths"]) == 1 and len(path) == 7 and path[:3:2] == [v.id["r"], v.id["a"]]
    assert path[-1] in (v.id["q1"], v.id["q2"]) and path[1].startswith("junction:")
    assert all(0 <= n["bootstrap_top_k_fraction"] <= 1 for n in v.result["nominations"])
    assert not v.nominated("s") and not v.nominated("q1")  # no dependent paper


def test_kind_lists_need_agreeing_kinds_and_other_kinds_are_listed_low():
    v = V()
    v.claim("r", 1, "definition", primitive=True)
    v.claim("a", 1, ("lemma", "theorem"), methods=("DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION"))
    v.claim("e", 1, "equation")
    v.claim("q", 2)
    for name in ("a", "e"):
        v.junction(name, ["r"])
        v.request("R" + name, "q")
        v.junction("q", ["R" + name], derivation=proof("q" + name))
        v.junction("R" + name, [name], method="MODEL_MATCH")
    v.run()
    (a,), (e,) = v.nominated("a"), v.nominated("e")
    assert (a["list"], a["layer_basis"], a["next_action"], a["blockers"]) == ("THEOREM_LIKE", ["PRIMITIVE"], "LIBRARY_AUDIT", [])
    assert (e["list"], e["layer_basis"], e["next_action"], e["blockers"]) == (
        "LOW_LAYER_BY_OPEN_PREMISES", ["PRIMITIVE"], "EXTRACT", ["NO_MODEL_EXTRACTION", "UNLISTED_KIND"])


def test_work_locator_claim_is_never_sent_to_extraction():
    v = V()
    w = v.work("NC", terminal="PREARXIV_DOI_NO_SOURCE", year=2000)
    c = v._put("Claim", "claim", "nc", ["HUMAN"], origin="WORK_LOCATOR", work_id=w, occurrence_ids=[], part="whole",
               work_locator_text="Thm 10.1, p. 437")
    v._put("ClaimReading", "reading", "nc-reading", ["HUMAN"], claim_id=c, method="HUMAN", kind="theorem")
    for n in (2, 3):
        v.claim(f"q{n}", n)
        v.request(f"R{n}", f"q{n}")
        v.junction(f"q{n}", [f"R{n}"])
        v.junction(f"R{n}", ["nc"], method="HUMAN")
    v.run()
    (n,) = v.nominated("nc")
    assert (n["list"], n["layer_basis"], n["next_action"], n["blockers"]) == ("THEOREM_LIKE", ["WORK_LOCATOR"], "LIBRARY_AUDIT", [])
    assert n["dependent_papers"] == {"lower": 2, "upper": 2} and n["date"]["kind"] == "BIB_YEAR"


def test_model_primitive_assertion_counts_only_once_signed():
    v = V()
    v.claim("p")
    pa = v._put("PrimitiveAssertion", "primitive", "p!", ["MODEL_EXTRACTION"], claim_id=v.id["p"],
                method="MODEL_EXTRACTION", basis="STANDARD_NOTION")
    v.claim("q")
    v.junction("q", ["p"])
    v.run(base_set="PRIMITIVE_ASSERTED")
    assert (v.layer("p"), v.layer("q"), v.m[v.id["p"]]["root_class"]) == ("INFINITY", "INFINITY", "NO_SUPPORT_PROPOSED")
    v.run({"PRIMITIVE_ASSERTION": {pa: "SOURCE_FROZEN_HUMAN_SIGNED"}}, base_set="PRIMITIVE_ASSERTED")
    assert (v.layer("p"), v.layer("q"), v.m[v.id["p"]]["root_class"]) == (0, 1, "PRIMITIVE")


def test_corrects_blocks_resolutions_from_the_corrected_work_until_signed():
    v = two_papers(V())
    j = v.junction("R", ["p1"], method="MODEL_MATCH")
    w = v.work("W")
    v.edge("VERSION_OF", pv(1), w)
    v.edge("CORRECTS", v.work("W-erratum"), w)
    v.run()
    assert (v.layer("R"), v.layer("q"), v.m[v.id["q"]]["layer_basis"]) == (0, 1, ["EXTERNAL_REQUEST"])
    assert v.result["diagnostics"]["CORRECTS_BLOCKED"] == [j] and v.m[v.id["p0"]]["dependent_papers"]["upper"] == 0
    v.run({"JUNCTION": {j: "SOURCE_FROZEN_HUMAN_SIGNED"}})
    assert (v.layer("R"), v.layer("q"), v.m[v.id["p0"]]["dependent_papers"]["upper"]) == (1, 2, 1)


def test_model_resolution_pools_a_request_only_when_the_policy_admits_it():
    v = V()
    v.work("W")
    v.claim("q", 2)
    v.request("R", "q")
    v.junction("q", ["R"])
    v.edge("RESOLVES_TO", "bib:" + hx("R"), v.id["W"], method="MODEL_MATCH", basis="title match")
    works = lambda: [r["subject_id"] for r in v.result["metrics"] if r["subject_kind"] == "WORK"]
    v.run()
    assert works() == []
    v.run(work_identity="PLUS_CANDIDATE_SAME_WORK")
    assert works() == [v.id["W"]]


def test_bootstrap_resamples_every_accepted_paper_even_without_claims():
    v = knockout_view()
    for n in (1, 2, 9):  # paper 9 was accepted and yielded no claim (§6.2: it stays in every denominator)
        v.edge("INCLUDES", "corpus:" + "c" * 64, pv(n), admission="SAMPLE", round=0, sampling_record_id="sampling:" + "a" * 64)
    view = {"deltas": [DELTA], "nodes": v.nodes, "edges": v.edges}
    assert analysis._index(view, POLICY, {}).papers == [pv(1), pv(2), pv(9)]


def test_low_layer_by_open_premises_and_work_pooling():
    v = V()
    v.work("W1", year=1995)
    v.work("W2", terminal="PREARXIV_DOI_NO_SOURCE")
    for n in (2, 3):
        v.claim(f"q{n}", n, "lemma", methods=("MODEL_EXTRACTION",))
        v.request(f"R{n}", f"q{n}", work="W1" if n == 2 else "W2")
        v.junction(f"q{n}", [f"R{n}"], method="MODEL_EXTRACTION")
    v.claim("z", 4)
    v.request("Rz", "z")
    v.junction("z", ["Rz"])
    v.junction("Rz", ["q2"], method="MODEL_MATCH", derivation=f"source:{pv(2)}:sha256:{hx('z')}")
    same = v.edge("SAME_WORK", v.id["W1"], v.id["W2"], basis="MODEL_MATCH")
    v.run()
    works = [r for r in v.result["metrics"] if r["subject_kind"] == "WORK"]
    assert len(works) == 2 and all(w["layer"] == "UNRESOLVED" and w["citing_claims"] == 1 for w in works)
    low = v.nominated("q2")[0]
    assert (low["list"], low["next_action"], low["blockers"]) == (
        "LOW_LAYER_BY_OPEN_PREMISES", "MATCH_REQUESTS", ["OPEN_PREMISE:EXTERNAL_REQUEST"])
    for kw in ({"work_identity": "PLUS_CANDIDATE_SAME_WORK"},
               {"work_identity": "PLUS_REVIEWED_SAME_WORK", "dispositions": {"WORK_IDENTITY": {same: "SOURCE_FROZEN_HUMAN_SIGNED"}}}):
        v.run(**kw)
        (w,) = [r for r in v.result["metrics"] if r["subject_kind"] == "WORK"]
        assert (w["subject_id"], w["citing_claims"], w["citing_papers"]) == (min(v.id["W1"], v.id["W2"]), 2, 2)
        assert w["dependent_papers"]["lower"] == 3 and w["date"]["kind"] == "BIB_YEAR"
        (n,) = [n for n in v.result["nominations"] if n["list"] == "WORKS"]
        assert (n["next_action"], n["blockers"], n["witness_paths"][0][0]) == ("ACQUIRE_SOURCE", ["WORK_UNRESOLVED"], w["subject_id"])
    v.run(work_identity="PLUS_REVIEWED_SAME_WORK")  # unreviewed candidate edge is not admitted
    assert len([r for r in v.result["metrics"] if r["subject_kind"] == "WORK"]) == 2


def test_expansion_papers_and_part_expansions_follow_the_policy():
    v = V()
    v.claim("a", 1)
    v.claim("x", 5)
    v.claim("b", 1)
    v.junction("b", ["a"], flags=["EXPANDED_TO_PARTS"])
    v.edge("INCLUDES", "corpus:" + "c" * 64, pv(5), admission="EXPANSION", round=1, sampling_record_id="sampling:" + "a" * 64)
    v.run()
    assert v.id["x"] not in v.m and v.layer("b") == 1
    v.run(traverse="ALL_ADMITTED", count_basis="ALL_ADMITTED", include_part_expansions=False)
    assert v.id["x"] in v.m and v.layer("b") == 0


def test_output_is_deterministic_stamped_and_never_a_status():
    first, second = knockout_view().run(), knockout_view().run()
    assert first == second
    assert first["policy_sha256"].startswith("sha256:") and first["bootstrap"]["manifest_id"] == MANIFEST["manifest_id"]
    assert set(first["bootstrap"]["top_k_fraction"]) == {n["nomination_id"] for n in first["nominations"]}
    assert "VERIFIED" not in json.dumps(first)


def test_edge_precision_perturbation():
    kinds = [(m, "UNCLASSIFIED", k) for m in ("DETERMINISTIC_ANCHOR", "MODEL_MATCH")
             for k in ("definition", "lemma", "theorem", "EXTERNAL_REQUEST")]
    v = knockout_view()
    v.claim("x", 5)
    v.claim("y", 5)
    v.junction("y", ["x"], method="MODEL_EXTRACTION")  # an out-of-scope expansion paper's legs need no estimate
    v.edge("INCLUDES", "corpus:" + "c" * 64, pv(5), admission="EXPANSION", round=1, sampling_record_id="sampling:" + "a" * 64)
    with pytest.raises(ValueError):
        v.run(estimates={k: 1.0 for k in kinds})  # the policy does not enable it
    policy = {"edge_precision": {"scheme": "EDGE_PRECISION_V1", "estimates": REF}}
    with pytest.raises(ValueError):
        v.run(estimates={}, **policy)
    keep = v.run(estimates={k: 1.0 for k in kinds}, **policy)
    assert all(n["edge_precision_top_k_survival"] == 1.0 for n in keep["nominations"])
    lost = v.run(estimates={k: 0.0 for k in kinds}, **policy)
    assert all(n["edge_precision_top_k_survival"] == 0.0 for n in lost["nominations"])
    assert set(lost["perturbation"]["top_k_survival"].values()) == {0.0}


def test_edge_precision_key_uses_the_agreed_premise_kind():
    """p̂(method, role, premise kind): a Claim premise's agreed reading kind, UNKNOWN when its readings disagree, or the
    Placeholder kind."""
    v = V()
    v.claim("agreed", kind="definition")
    v.claim("split", kind=("theorem", "lemma"), methods=("DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION"))
    v.claim("q")
    v.request("R", "q")
    v.junction("q", ["agreed", "split", "R"])
    with pytest.raises(ValueError) as caught:
        v.run(estimates={}, edge_precision={"scheme": "EDGE_PRECISION_V1", "estimates": REF})
    expected = sorted(("DETERMINISTIC_ANCHOR", "UNCLASSIFIED", k) for k in ("definition", "UNKNOWN", "EXTERNAL_REQUEST"))
    assert str(caught.value) == f"no edge precision estimate for {expected}"


def test_dependents_never_count_the_subject_inside_a_cycle():
    """a <-> b with an exit through r: a reaches itself, but it is not its own dependent (u != v), exact or estimated."""
    for paper_b, exactness in ((1, "ESTIMATED"), (2, "EXACT")):  # with b in another paper, a is nominated: exact count
        v = V()
        for name, paper in (("r", 1), ("a", 1), ("b", paper_b)):
            v.claim(name, paper)
        v.junction("a", ["b"], derivation=proof("a1"))
        v.junction("a", ["r"], derivation=proof("a2"))
        v.junction("b", ["a"])
        v.run()
        a, b = v.m[v.id["a"]], v.m[v.id["b"]]
        assert a["in_cycle"] and a["dependents"] == {"lower": 1, "upper": 1, "exactness": exactness}
        assert b["dependents"]["lower"] == b["dependents"]["upper"] == 1  # only a
        assert a["dependent_papers"]["lower"] == paper_b - 1 and bool(v.nominated("a")) == (exactness == "EXACT")


def test_view_must_be_the_manifest_merge():
    v = knockout_view()
    with pytest.raises(ValueError):
        analysis.analyze({"deltas": [], "nodes": v.nodes, "edges": v.edges}, MANIFEST, POLICY)


POPULATION = [{"subject_kind": "LEG", "subject_id": f"junction:{hx(str(i))}#0",
               "stratum": {"method": "MODEL_EXTRACTION" if i % 3 else "DETERMINISTIC_ANCHOR", "method_version": "1",
                           "role": "UNCLASSIFIED", "use_site": "PROOF"}} for i in range(30)]


def test_review_sample_is_seeded_stratified_and_relabels_after_seven_days():
    args = ("manifest:" + "a" * 64, "LEG_PRECISION", "RANDOM", "s1", REF, 1, POPULATION, 5, "2026-09-25T00:00:00+00:00")
    sample = review_sample.review_sample(*args)
    assert sample == review_sample.review_sample(*args) and len(sample["items"]) == 10
    probs = sorted({(i["stratum"]["method"], i["inclusion_probability"]) for i in sample["items"]})
    assert probs == [("DETERMINISTIC_ANCHOR", 0.5), ("MODEL_EXTRACTION", 0.25)]
    assert review_sample.review_sample(*args[:3], "s2", *args[4:])["items"] != sample["items"]
    with pytest.raises(ValueError):
        review_sample.relabel(sample, "r", "2026-09-30T00:00:00+00:00")
    with pytest.raises(ValueError):  # the sample's own seed would favour the strata it drew first
        review_sample.relabel(sample, "s1", "2026-10-02T00:00:00+00:00")
    again = review_sample.relabel(sample, "r", "2026-10-02T00:00:00+00:00")
    assert again["relabel_of"] == sample["sample_id"] and len(again["items"]) == 1
    assert again["items"][0]["inclusion_probability"] in (0.05, 0.025)
    versions = [{**i, "stratum": {**i["stratum"], "method_version": "2" if n % 2 else "1"}} for n, i in enumerate(POPULATION)]
    split = review_sample.review_sample(*args[:6], versions, 5, args[8])
    assert len({review_sample.stratum_key(i["stratum"]) for i in split["items"]}) == 4  # a method version is its own stratum


def test_wilson_and_inverse_inclusion_weighted_precision():
    w = review_sample.wilson(50, 100)
    assert w["lower"] == pytest.approx(0.40383, abs=1e-5) and w["upper"] == pytest.approx(0.59617, abs=1e-5)
    assert review_sample.wilson(0, 10)["lower"] == 0.0
    items = [{"subject_id": "a", "inclusion_probability": 1.0}, {"subject_id": "b", "inclusion_probability": 0.25}]
    out = review_sample.precision({"items": items}, {"a": True, "b": False})
    assert out["estimate"] == pytest.approx(1 / 5) and out["n_effective"] == pytest.approx(25 / 17)
    assert out["wilson_95"]["lower"] < 0.2 < out["wilson_95"]["upper"]
    with pytest.raises(ValueError):
        review_sample.precision({"items": items}, {})


def test_dependents_of_a_non_nominated_hub_are_a_bottom_k_estimate():
    v = V()
    v.claim("hub")
    for i in range(200):
        v.claim(f"c{i}")
        v.junction(f"c{i}", ["hub"])
    v.run()
    hub = v.m[v.id["hub"]]["dependents"]
    assert hub["exactness"] == "ESTIMATED" and hub["lower"] == hub["upper"] and 100 <= hub["lower"] <= 400


def admitted_view():
    """f (paper 5, EXPANSION) is used by e (paper 5), which a and b (papers 1, 2, SAMPLE) use; g (paper 6, DISCOVERY)
    uses f directly. Paper categories: 1 quant-ph, 2 cond-mat.str-el (cross-listed quant-ph), 5 math-ph, 6 hep-th."""
    v = V()
    for name, paper in (("f", 5), ("e", 5), ("a", 1), ("b", 2), ("g", 6)):
        v.claim(name, paper)
    v.junction("e", ["f"])
    v.junction("a", ["e"])
    v.junction("b", ["e"])
    v.junction("g", ["f"])
    for n, admission, cats in ((1, "SAMPLE", ["quant-ph"]), (2, "SAMPLE", ["cond-mat.str-el", "quant-ph"]),
                               (5, "EXPANSION", ["math-ph"]), (6, "DISCOVERY", ["hep-th"])):
        v.edge("INCLUDES", "corpus:" + "c" * 64, pv(n), admission=admission, round=0 if admission == "SAMPLE" else 1,
               sampling_record_id="sampling:" + "a" * 64)
        v.nodes["PaperVersion"][pv(n)].update(primary_category=cats[0], categories=cats)
    return v


def test_count_basis_counts_sample_papers_while_traversing_cited_and_discovered_ones():
    v = admitted_view()
    v.run(traverse="ALL_ADMITTED", count_basis="SAMPLE_ONLY")
    f = v.m[v.id["f"]]
    assert f["count_basis"] == "SAMPLE_ONLY" and f["dependent_papers"] == {"lower": 2, "upper": 2}  # papers 1, 2; not 6
    (nom,) = v.nominated("f")
    assert nom["count_basis"] == "SAMPLE_ONLY" and nom["dependent_topics"] == {"lower": 2, "upper": 2}  # quant-ph, cond-mat
    assert all(len(path) >= 3 for path in nom["witness_paths"])  # f -> e -> a and f -> e -> b; no path to g's paper
    v.run(traverse="ALL_ADMITTED", count_basis="ALL_ADMITTED")
    assert v.m[v.id["f"]]["dependent_papers"]["lower"] == 3 and v.nominated("f")[0]["dependent_topics"]["lower"] == 3
    v.run()  # traverse SAMPLE_ONLY: the expansion and discovery papers are outside the graph
    assert v.id["f"] not in v.m and v.id["g"] not in v.m and v.m[v.id["a"]]["dependent_papers"]["lower"] == 0
    with pytest.raises(Exception):
        v.run(traverse="SAMPLE_ONLY", count_basis="ALL_ADMITTED")  # the contract refuses counting what is not traversed


def test_dependents_and_knockouts_count_only_claims_of_counted_papers():
    v = admitted_view()
    v.run(traverse="ALL_ADMITTED", count_basis="SAMPLE_ONLY")
    f = v.m[v.id["f"]]
    assert (f["dependents"]["lower"], f["dependents"]["upper"]) == (2, 2)  # a and b; not e (EXPANSION) or g (DISCOVERY)
    assert f["necessary_dependents"]["ALL_ROOTS"] == {"lower": 2, "upper": 2}
    v.run(traverse="ALL_ADMITTED", count_basis="ALL_ADMITTED")
    f = v.m[v.id["f"]]
    assert (f["dependents"]["lower"], f["necessary_dependents"]["ALL_ROOTS"]["lower"]) == (4, 4)  # e, a, b and g


def test_structural_rules_resolve_an_occurrence_placeholder_and_join_a_whole_to_its_parts():
    v = V()
    for name in ("r", "w", "c", "p0", "p1", "q", "s"):
        v.claim(name)
    v.junction("w", ["r"])
    w = v.nodes["Claim"][v.id["w"]]
    v._put("Placeholder", "placeholder", "u", kind="UNRESOLVED_OCCURRENCE", paper_version_id=pv(1), created_by_claim_id=v.id["c"],
           citing_derivation_id=proof("c"), occurrence_id=w["occurrence_ids"][0], reason="NON_ENVIRONMENT_TARGET")
    v.junction("c", ["u"])  # c rests on the placeholder of w's own occurrence
    v.junction("p1", ["r"])
    for part in ("p0", "p1"):
        v.edge("PART_OF", v.id[part], v.id["q"])
    v.junction("s", ["q"])  # s uses the whole q, which has no derivation of its own
    v.run()
    assert v.layer("c") == 2  # c <- u = w <- r: the placeholder takes w's value, it is not a root at 0
    assert (v.layer("q"), v.layer("s")) == (1, 2)  # q = max(p0, p1) without a layer of its own
    assert v.m[v.id["w"]]["dependents"]["lower"] == 1  # c depends on w through the placeholder


def test_bootstrap_resamples_only_the_counted_papers():
    v = admitted_view()
    view = {"deltas": [DELTA], "nodes": v.nodes, "edges": v.edges}
    ctx = analysis._index(view, {**POLICY, "traverse": "ALL_ADMITTED"}, {})
    assert [ctx.papers[i] for i in ctx.counted] == [pv(1), pv(2)]
    ctx = analysis._index(view, {**POLICY, "traverse": "ALL_ADMITTED", "count_basis": "ALL_ADMITTED"}, {})
    assert [ctx.papers[i] for i in ctx.counted] == [pv(1), pv(2), pv(5), pv(6)]


def test_a_primary_run_needs_its_p0_go_the_corpus_and_complete_coverage():
    import corpus
    import gates
    v = knockout_view()
    reading = next(r for r in v.nodes["ClaimReading"].values() if r["method"] == "MODEL_EXTRACTION")
    reading["method_version"] = "focus-1"
    rule = {"admission_threshold": 0.85, "fpr_inflation": 2.0, "alpha": 0.05, "max_unresolved_fraction": 0.2, "min_items": 100,
            "require_projection_under_ceiling": True}
    cm = corpus.freeze_corpus_manifest({
        "field": {"primary_categories": ["quant-ph"], "date_window": {"start": "2020-01-01", "end": "2025-12-31"}},
        "sampling_frame": {"kind": "METADATA_SNAPSHOT", "sha256": "sha256:" + "a" * 64, "snapshot_date": "2026-09-01"},
        "eligibility": {"rule": "THEOREM_OR_DERIVATION_V1", "params": {"min_theorem_like": 1, "min_display_equations": 3},
                        "program_sha256": "sha256:" + "a" * 64, "parser_sha256": "sha256:" + "a" * 64},
        "size_limits": {}, "version_rule": "LATEST_ON_OR_BEFORE_SNAPSHOT", "seed": "s", "target_size": 2,
        "transient_retry_limit": 1, "coverage": "EQUAL_FULL",
        "extraction": {"operation": "paper.extract_focus", "method_version": "focus-1", "focus_bytes": 8192},
        "gates": {"P_MINUS_1": {"min_eligible_fraction": 0.3, "max_undetermined_fraction": 0.2,
                                "claim_level": {"min_works": 1, "min_citing_papers": 2}}, "P0": rule},
        "primary_analysis_policy": {**POLICY, "status": "PRIMARY"}, "budget_ceiling": {"unit": "calls", "value": 10},
        "created_at": "2026-09-25T00:00:00Z"})
    everything = ["DETERMINISTIC_ANCHOR", "HUMAN", "LIBRARY", "MODEL_EXTRACTION", "MODEL_MATCH"]
    decide = lambda decision, methods=everything: gates._decision(cm, "P0", ["eval-report:" + "a" * 64], {}, rule, decision,
                                                                 ["synthetic"], methods, "2026-09-25T00:00:00Z")
    go = decide("GO")
    primary = gates.primary_policy(cm, go)
    dm = make_manifest(cm["corpus_id"], [DELTA], created_at="2026-09-25T00:00:00+00:00")
    coverage = {"corpus_id": cm["corpus_id"], "policy": "EQUAL_FULL", "extraction": cm["extraction"], "complete": True, "incomplete": []}
    view = {"deltas": [DELTA], "nodes": v.nodes, "edges": v.edges}
    ok = {"admission": go, "corpus": cm, "coverage": coverage}
    out = analysis.analyze(view, dm, primary, **ok)
    assert out["nominations"] and out["policy_id"] == primary["policy_id"] and primary["admission_gate"] == go["gate_id"]
    for missing in ok:
        with pytest.raises(ValueError, match="NEEDS_A_P0_ADMISSION"):
            analysis.analyze(view, dm, primary, **{**ok, missing: None})
    with pytest.raises(ValueError, match="MANIFEST_OF_ANOTHER_CORPUS"):
        analysis.analyze(view, MANIFEST, primary, **ok)
    with pytest.raises(ValueError, match="NOT_BOUNDED"):  # not the policy gates.primary_policy derives
        analysis.analyze(view, dm, {**primary, "importance_methods": ["HUMAN"]}, **ok)
    with pytest.raises(ValueError, match="NOT_BOUNDED"):
        analysis.analyze(view, dm, gates.primary_policy(cm, decide("GO", ["HUMAN", "MODEL_EXTRACTION"])), **ok)
    with pytest.raises(ValueError, match="P0_GO"):
        analysis.analyze(view, dm, primary, **{**ok, "admission": decide("NO_GO")})
    with pytest.raises(ValueError, match="GATE_ID_IS_NOT_THE_DIGEST"):  # an admission edited after the gate made it
        analysis.analyze(view, dm, primary, **{**ok, "admission": {**go, "admitted_methods": ["HUMAN", "LIBRARY"]}})
    with pytest.raises(ValueError, match="COVERAGE_INCOMPLETE"):
        analysis.analyze(view, dm, primary, **{**ok, "coverage": {**coverage, "complete": False, "incomplete": [pv(1)]}})
    with pytest.raises(ValueError, match="ANOTHER_CORPUS_OR_EXTRACTION"):
        analysis.analyze(view, dm, primary, **{**ok, "coverage": {**coverage, "extraction": {**cm["extraction"], "method_version": "local-1"}}})
    reading["method_version"] = "local-1"
    with pytest.raises(ValueError, match="MIXES_EXTRACTION_VERSIONS"):
        analysis.analyze(view, dm, primary, **ok)
