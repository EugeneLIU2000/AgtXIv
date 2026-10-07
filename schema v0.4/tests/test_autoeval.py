"""The 2026-09-25 additions on synthetic papers: eligibility, WHOLE_PAPER_FOCUS extraction, AUTO_EVAL_V1, the automatic
gates and the cost projection. No model, network, Neo4j or Lean: judge responses and usage figures are hand-written."""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from core import canonical, digest

import anchors
import autoeval
import contracts
import corpus
import cost
import delta
import eligibility
import extraction
import gates
import ids
import invariants
import analysis
import matching
import review_sample
from reviews import leg_id
from test_builders import PV, TEX, UP, UP_TEX, acquired, claim, extract

T0 = "2026-09-25T00:00:00Z"
S = digest(b"synthetic")
RECEIPT = {"path": "receipts/judge-1.json", "sha256": S, "byte_size": 1}
DERIV = "arxiv:2102.00005v1"
DERIV_TEX = r"""\documentclass{article}
\begin{document}
\section{Model}
The Hamiltonian of the chain is
\begin{equation}\label{eq:h}
H = \sum_i Z_i Z_{i+1}.
\end{equation}
Squaring equation \eqref{eq:h} term by term gives
\begin{equation}\label{eq:h2}
H^2 = \sum_{i,j} Z_i Z_{i+1} Z_j Z_{j+1}.
\end{equation}
Taking the trace of \eqref{eq:h2} and using the orthogonality of Pauli strings \cite{Old} we obtain
\begin{equation}\label{eq:tr}
\mathrm{tr}\, H^2 = n 2^n.
\end{equation}
\begin{thebibliography}{9}
\bibitem{Old} A.~Author, \newblock Old results on Pauli strings, \newblock J. Tiny 1 (1990).
\end{thebibliography}
\end{document}
"""
NEST = "arxiv:2102.00006v1"
NEST_TEX = r"""\documentclass{article}
\begin{document}
\begin{theorem}\label{t:x}
Every widget is round. % Every widget is square.
\end{theorem}
\begin{lemma}\label{l:y}
Every round widget rolls along any flat surface without slipping, and this long sentence keeps the statement of the
lemma well beyond the focus budget, so that the host has to decide where the next focus may begin; it may begin only
once every occurrence already in the focus has ended.
\begin{equation}\label{e:z}
r = 1
\end{equation}
\end{lemma}
\begin{theorem}\label{t:w}
Every rolling widget is round.
\end{theorem}
\begin{proof}
By Lemma~\ref{l:y}.
\end{proof}
\begin{corollary}\label{c:v}
As Theorem~\ref{t:w} shows, every widget rolls.
\end{corollary}
\end{document}
"""
PRICING_PATH = Path(cost.__file__).resolve().parents[1] / "profiles" / "pricing-mimo-20260922.json"
PRICING, PRICING_SHA = cost.load_pricing(PRICING_PATH)
SELECTION = {"policy_version": "operation-routing-v2", "policy_sha256": S, "profile": "p", "reason": "synthetic judge",
             "training_cutoff": {"value": "UNKNOWN", "source": "none"}}
PRO = {**SELECTION, "operation": "leg.judge", "engine_class": "DECISION", "model": "mimo-v2.6-pro", "effort": "thinking-enabled"}
TERRA = {**SELECTION, "operation": "leg.judge", "engine_class": "DECISION", "model": "gpt-5.6-terra", "effort": "medium"}
FLASH = {**PRO, "model": "mimo-v2.6-flash"}
TEMPLATE = {"kind": "AnalysisPolicy", "contract_version": "0.4.0", "policy_id": "policy:" + "2" * 64, "status": "PRIMARY",
            "establishment_reading": {"mode": "UNION"}, "importance_methods": ["DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION", "MODEL_MATCH"],
            "work_identity": "EXPLICIT_IDS_ONLY", "citation_group_semantics": "AND", "cycle_policy": "FIXPOINT",
            "base_set": "ALL_ROOTS", "include_part_expansions": False, "traverse": "ALL_ADMITTED", "count_basis": "SAMPLE_ONLY",
            "admission_gate": None, "nomination": {"rule": "FOUNDATION_V1", "threshold": 1, "top_k": 5},
            "bootstrap": {"scheme": "PAPER_REWEIGHT_V1", "replicates": 5, "seed": "b"}, "edge_precision": None}
GATES = {"P_MINUS_1": {"min_eligible_fraction": 0.5, "max_undetermined_fraction": 0.3,
                       "claim_level": {"min_works": 1, "min_citing_papers": 3}},
         "P0": {"admission_threshold": 0.85, "fpr_inflation": 2.0, "alpha": 0.05, "max_unresolved_fraction": 0.2,
                "min_items": 100, "require_projection_under_ceiling": True}}
EXTRACT = {"method": "MODEL_EXTRACTION", "method_version": "focus-1", "role": "UNCLASSIFIED", "use_site": "UNKNOWN"}
RULES = ["SAME_PAPER_NEAR_MISS_V1", "OTHER_PAPER_DECOY_V1"]


def manifest(**changes):
    fields = {"field": {"primary_categories": ["quant-ph"], "date_window": {"start": "2015-01-01", "end": "2025-12-31"}},
              "sampling_frame": {"kind": "METADATA_SNAPSHOT", "sha256": S, "snapshot_date": "2026-09-01"},
              "eligibility": {"rule": "THEOREM_OR_DERIVATION_V1", "params": {"min_theorem_like": 1, "min_display_equations": 3},
                              "program_sha256": eligibility.program_sha256(), "parser_sha256": S},
              "size_limits": {}, "version_rule": "LATEST_ON_OR_BEFORE_SNAPSHOT", "seed": "sample-seed", "target_size": 3,
              "transient_retry_limit": 1, "coverage": "EQUAL_FULL",
              "extraction": {"operation": "paper.extract_focus", "method_version": "focus-1", "focus_bytes": 8192}, "gates": GATES,
              "primary_analysis_policy": TEMPLATE,
              "budget_ceiling": {"unit": "USD", "value": 2500, "pricing_profile_sha256": PRICING_SHA}, "created_at": T0}
    return corpus.freeze_corpus_manifest({**fields, **changes})


CORPUS = manifest()


@pytest.fixture(scope="module")
def papers(tmp_path_factory):
    return {pv: extract(pv, tex, tmp_path_factory) for pv, tex in ((PV, TEX), (UP, UP_TEX), (DERIV, DERIV_TEX), (NEST, NEST_TEX))}


# ---- eligibility --------------------------------------------------------------------------------------------------

def test_theorem_or_derivation_keeps_derivation_papers_and_unread_sources_undetermined(papers):
    rule = CORPUS["eligibility"]
    assert eligibility.counts(papers[PV]["record"]) == {"theorem_like": 4, "display_equations": 1}
    assert eligibility.counts(papers[DERIV]["record"]) == {"theorem_like": 0, "display_equations": 3}
    assert eligibility.decide(papers[DERIV]["record"], rule)["outcome"] == "ACCEPTED"  # three display equations
    strict = {**rule, "params": {"min_theorem_like": 5, "min_display_equations": 4}}
    out = eligibility.decide(papers[PV]["record"], strict)
    assert out["outcome"] == "INELIGIBLE" and "4 theorem-like < 5" in out["reason"]
    assert eligibility.candidate_outcome(out, 1, PV) == {"outcome": "INELIGIBLE", "attempts": 1, "reason": out["reason"]}
    assert eligibility.candidate_outcome(eligibility.decide(papers[PV]["record"], rule), 1, PV)["paper_version_id"] == PV
    grid = eligibility.grid([papers[p]["record"] for p in (PV, UP, DERIV)], [1, 5], [3, 10])
    assert grid == {"k=1,m=3": 1.0, "k=1,m=10": 2 / 3, "k=5,m=3": 1 / 3, "k=5,m=10": 0.0}
    assert eligibility.program_sha256() == digest(Path(eligibility.__file__).read_bytes())
    with pytest.raises(ValueError, match="UNSUPPORTED"):
        eligibility.decide(papers[PV]["record"], {**rule, "rule": "k>=1"})
    # A source that could not be read is UNDETERMINED (outside P), never INELIGIBLE (inside the denominator).
    up, issue = papers[UP]["record"], lambda code: {"code": code, "detail": "synthetic"}
    nothing = {**up, "source_files": [], "claims": []}
    out = eligibility.decide(nothing, rule)
    assert (out["outcome"], out["undetermined_class"]) == ("UNDETERMINED", "NO_TEX_SOURCE")
    assert eligibility.candidate_outcome(out, 2, UP) == {"outcome": "UNDETERMINED", "attempts": 2, "undetermined_class": "NO_TEX_SOURCE"}
    assert eligibility.decide({**up, "issues": [issue("SOURCE_MAIN_AMBIGUOUS")]}, rule)["undetermined_class"] == "MAIN_AMBIGUOUS"
    assert eligibility.decide({**up, "issues": [issue("SOURCE_ACQUISITION_FAILED")]}, rule)["undetermined_class"] == "NO_TEX_SOURCE"
    partial = {**up, "issues": [issue("SOURCE_INCLUDE_MISSING")]}
    assert eligibility.decide(partial, rule)["outcome"] == "ACCEPTED"  # what was read already meets the rule
    short = eligibility.decide(partial, strict)  # the unread include could hold what is missing
    assert (short["outcome"], short["undetermined_class"], short["issues"]) == ("UNDETERMINED", "PARSE_FAILED", ["SOURCE_INCLUDE_MISSING"])
    assert eligibility.decide(up, strict)["outcome"] == "INELIGIBLE"
    unread = eligibility.grid([papers[PV]["record"], partial, papers[DERIV]["record"], nothing], [1, 5], [3, 10])
    assert unread == {"k=1,m=3": 1.0, "k=1,m=10": 2 / 3, "k=5,m=3": 0.5, "k=5,m=10": 0.0}


# ---- WHOLE_PAPER_FOCUS --------------------------------------------------------------------------------------------

def test_foci_partition_the_occurrences_and_prompts_share_one_prefix(papers):
    p = papers[DERIV]
    foci = extraction.plan_foci(p["record"], p["sources"], focus_bytes=256)
    members = [cid for f in foci for cid in f["claim_ids"]]
    assert sorted(members) == sorted(p["P"]["claims"]) and len(members) == len(set(members)) and len(foci) > 1
    for a, b in zip(foci, foci[1:]):
        assert a["byte_end"] == b["byte_start"] and a["byte_start"] < b["byte_start"]  # disjoint, covering scopes
    assert foci[0]["byte_start"] == 0 and foci[-1]["byte_end"] == len(p["sources"][foci[-1]["path"]])
    built = extraction.build_focus_prompts(p["record"], p["sources"], focus_bytes=256)
    prefix = built["prompts"][0]["prompt"].encode()[:built["prefix_bytes"]]
    assert digest(prefix) == built["prefix_sha256"] and len(built["prompts"]) == len(foci)
    assert all(row["prompt"].encode()[:built["prefix_bytes"]] == prefix for row in built["prompts"])
    assert len({row["prompt"] for row in built["prompts"]}) == len(foci)
    assert all(len(row["prompt"].encode()) - built["prefix_bytes"] < 1024 for row in built["prompts"])  # only FOCUS differs
    assert "occ:" not in built["prompts"][0]["prompt"] and "Z_i Z_{i+1}" in prefix.decode()
    with pytest.raises(ValueError):
        extraction.plan_foci(p["record"], p["sources"], focus_bytes=100)


def focus_of(built, occ):
    return next(row for row in built["prompts"] if occ in row["context"]["aliases"].values()
                and any(r["id"] == occ and r["role"] == "ENVIRONMENT" for r in row["context"]["inventory"]))


def test_focus_response_connects_a_derivation_through_equations(papers):
    p = papers[DERIV]
    built = extraction.build_focus_prompts(p["record"], p["sources"], focus_bytes=256)
    alias = lambda occ: next(a for a, o in built["prompts"][0]["context"]["aliases"].items() if o == occ)
    h, h2, tr = (p["occ"](k) for k in ("eq:h", "eq:h2", "eq:tr"))
    later, earlier = focus_of(built, tr), focus_of(built, h2)
    assert later["focus_id"] != earlier["focus_id"]
    s6 = []
    for row, conclusion, premise, keys in ((later, tr, h2, ["Old"]), (earlier, h2, h, [])):
        response = {"claims": [claim([alias(conclusion)], "an equation of the derivation", kind="equation",
                                     internal_support_occurrence_ids=[alias(premise)], external_citation_keys=keys)],
                    "unread_or_uncertain_scope": []}
        s6.append(extraction.focus_response_to_delta(p["record"], p["sources"], row["context"], response, method_version="focus-1",
                                                     parents=[p["s3"]["delta_id"]]))
    assert all(d["issues"] == [] and d["subject"]["kind"] == "CLAIM_BATCH" for d in s6)
    claims = {row["occurrence_ids"][0]: row for d in s6 for row in d["nodes"]["Claim"]}
    (j,) = s6[0]["nodes"]["Junction"]
    premises = [leg["premise_id"] for leg in j["legs"]]
    assert premises[0] == claims[h2]["id"] and claims[h2]["occurrence_kind"] == "DISPLAY_EQUATION"  # a claim, not a placeholder
    assert premises[1].startswith("placeholder:") and j["derivation_id"] == "unlocated:MODEL_EXTRACTION:0"
    view = delta.merge([p["s1"], p["s3"], *s6])  # the equation claim both calls assert merges into one row
    assert invariants.check(view) == []
    unknown = {"claims": [claim(["o999"], "an equation", kind="equation")], "unread_or_uncertain_scope": []}
    failed = extraction.focus_response_to_delta(p["record"], p["sources"], later["context"], unknown, method_version="focus-1")
    assert failed["nodes"] == {} and {i["code"] for i in failed["issues"]} >= {"MODEL_OCCURRENCE_REFERENCE_UNKNOWN"}
    outside = {"claims": [claim([alias(h)], "an equation of another focus", kind="equation")], "unread_or_uncertain_scope": []}
    rejected = extraction.focus_response_to_delta(p["record"], p["sources"], later["context"], outside, method_version="focus-1")
    assert "MODEL_CLAIM_OUTSIDE_BATCH" in {i["code"] for i in rejected["issues"]}
    with pytest.raises(ValueError):
        extraction.focus_response_to_delta(p["record"], p["sources"], {**later["context"], "operation": "paper.extract_local"},
                                           unknown, method_version="focus-1")


def test_focus_cuts_keep_nested_occurrences_and_quotes_bind_to_their_occurrence(papers):
    p, occ = papers[NEST], papers[NEST]["occ"]
    cid = lambda key: p["record"]["labels"][key][0]["claim_ids"][0]
    foci = extraction.plan_foci(p["record"], p["sources"], focus_bytes=256)
    holder = {c: f for f in foci for c in f["claim_ids"]}
    assert holder[cid("l:y")] is holder[cid("e:z")]  # the equation inside the lemma stays with it ...
    assert holder[cid("l:y")]["byte_end"] - holder[cid("l:y")]["byte_start"] > 256  # ... though the focus then exceeds the budget
    assert foci[0]["byte_start"] == 0 and len({holder[cid(k)]["focus_id"] for k in ("t:x", "l:y", "t:w")}) == 3
    built = extraction.build_focus_prompts(p["record"], p["sources"], focus_bytes=256)
    alias = {o: a for a, o in built["prompts"][0]["context"]["aliases"].items()}
    run = lambda key, claims: extraction.focus_response_to_delta(p["record"], p["sources"], focus_of(built, occ(key))["context"],
                                                                 {"claims": claims, "unread_or_uncertain_scope": []}, method_version="focus-1")
    commented = run("t:x", [claim([alias[occ("t:x")]], "widgets are square", kind="theorem", locators=["Every widget is square."])])
    assert commented["nodes"] == {} and "MODEL_LOCATOR_IN_COMMENT" in {i["code"] for i in commented["issues"]}  # commented-out text
    assert run("t:x", [claim([alias[occ("t:x")]], "widgets are round", kind="theorem", locators=["Every widget is round."])])["issues"] == []
    # Two claims of the lemma: the quotation inside the nested equation still marks the lemma that the claim names.
    parts = run("l:y", [claim([alias[occ("l:y")]], "round widgets roll", locators=["Every round widget rolls"]),
                        claim([alias[occ("l:y")]], "the radius is one", kind="equation", locators=["r = 1"])])
    assert parts["issues"] == [] and sorted(r["part"] for r in parts["nodes"]["Claim"] if r["part"] != "whole") == ["part:0", "part:1"]
    # A claim that names no occurrence binds to the innermost one enclosing its quotation.
    inner = run("l:y", [claim([], "the radius is one", kind="equation", locators=["r = 1"])])
    assert inner["issues"] == [] and [r["occurrence_ids"] for r in inner["nodes"]["Claim"]] == [[occ("e:z")]]


def test_focus_prompts_send_body_files_byte_exact_and_other_files_as_context_only(papers):
    p = papers[NEST]
    main = next(iter(p["sources"]))
    folder = main.rsplit("/", 1)[0]
    sources = {**p["sources"], folder + "/refs.bib": b"@misc{W, title = {Widgets}}\n", folder + "/latin.tex": "caf\xe9\n".encode("latin-1"),
               folder + "/widgets.sty": b"\\def\\w{1}\n"}
    built = extraction.build_focus_prompts(p["record"], sources, focus_bytes=256)
    data = json.loads(built["prompts"][0]["prompt"].split("\nPAPER DATA:\n", 1)[1].rsplit("\nFOCUS:\n", 1)[0])
    files = {row["path"]: row for row in data["files"]}
    assert set(files) == {"main.tex", "refs.bib", "latin.tex"}  # a style file is never sent
    assert "context_only" not in files["main.tex"] and files["main.tex"]["text"].encode() == p["sources"][main]
    assert files["refs.bib"]["context_only"] and files["latin.tex"]["context_only"]  # no quotation binds there


def test_two_s2_claims_of_one_span_are_one_occurrence_named_by_the_environment():
    data = b"\\begin{theorem}x\\end{theorem}"
    span = {"path": "m.tex", "byte_start": 0, "byte_end": len(data), "span_sha256": digest(data), "sha256": digest(data)}
    row = lambda cid, kind: {"id": cid, "kind": kind, "source": span, "proof_sources": [], "text": data.decode()}
    record = {"paper": {"id": PV, "source_root": "."}, "claims": [row("a-thm", "THEOREM_LIKE_ENVIRONMENT"), row("b-eq", "DISPLAY_EQUATION")],
              "labels": {}, "anchors": [], "bibliography": [], "proof_spans": []}
    P = anchors.index(record, {"m.tex": data})
    assert P["occ"]["a-thm"] == P["occ"]["b-eq"] and P["by_occ"] == {P["occ"]["a-thm"]: "a-thm"}  # not the later id
    assert extraction._canonical(P) == ["a-thm"]


def test_a_part_claim_is_named_by_where_it_was_quoted():
    loc = lambda start: {"artifact": "main.tex", "source_sha256": S, "start_byte": start, "end_byte": start + 5, "span_sha256": S,
                         "line_start": 1, "line_end": 1}
    row = lambda part, locator: ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": PV, "occurrence_ids": ["occ:" + "a" * 64],
                                                   "part": part, "locator": locator})
    assert row("part:0", loc(0))["id"] != row("part:0", loc(10))["id"]  # two quoted parts of one occurrence are two claims
    assert row("part:0", loc(0))["id"] == row("part:0", {**loc(0), "line_start": 2, "line_end": 2})["id"]  # the place, not the lines
    assert row("whole", loc(0))["id"] == row("whole", loc(10))["id"]  # a whole claim is its occurrence


# ---- AUTO_EVAL_V1 -------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def graph(papers):
    """S1 and S3 of the theorem paper and its upstream paper, one local S6 batch of the theorem paper, and one S7 match
    of its request to \\cite{A} (the upstream paper) to the upstream theorem t:1."""
    p, up = papers[PV], papers[UP]
    ctx = extraction.build_local_prompt(p["record"], p["sources"], [p["occ"]("lem:b"), p["occ"]("thm:c")], prose_bytes=0)["context"]
    response = {"claims": [claim([p["occ"]("lem:b")], "Every nice object is tiny.", internal_support_occurrence_ids=[p["occ"]("def:a")],
                                 external_citation_keys=["Old"]),
                           claim([p["occ"]("thm:c")], "Tiny objects exist.", kind="theorem",
                                 internal_support_occurrence_ids=[p["occ"]("lem:b")])],
               "unread_or_uncertain_scope": []}
    s6 = extraction.response_to_delta(p["record"], p["sources"], ctx, response, method_version="m1", parents=[p["s3"]["delta_id"]])
    assert s6["issues"] == []
    key = {row["id"]: row["citation_key"] for row in p["s3"]["nodes"]["BibEntry"]}
    request = next(r for r in p["s3"]["nodes"]["Placeholder"] if r["kind"] == "EXTERNAL_REQUEST" and key[r["bib_entry_id"]] == "A")
    readings = {r["id"]: r for r in up["s3"]["nodes"]["ClaimReading"]}
    pairs = [(c, r) for c in up["s3"]["nodes"]["Claim"] for r in readings.values() if r["claim_id"] == c["id"]]
    theorem = next(c for c, r in pairs if r["kind"] == "theorem")
    built = matching.build_match_prompt(UP, [{"request": request, "citing": None,
                                              "candidates": matching.retrieve_candidates(request, None, pairs, 2)}])
    rows = [{"target_request_id": request["id"], "upstream_occurrence_ids": [], "upstream_claim_ids": [theorem["id"]],
             "relation": "CANDIDATE_SUPPORT", "combination": "SINGLE_CLAIM", "extra_conditions": [], "proof_issues": [],
             "source_quotes": [{"path": theorem["id"], "exact_text": "Every tiny object is small."}], "reason": "synthetic",
             "confidence": 0.9}]
    s7 = matching.match_rows_to_delta(built["context"], {"matches": rows}, method_version="match-1",
                                      parents=[p["s3"]["delta_id"], up["s3"]["delta_id"]])
    deltas = [p["s1"], p["s3"], up["s1"], up["s3"], s6, s7]
    view = delta.merge(deltas)
    dm = delta.make_manifest(CORPUS["corpus_id"], [d["delta_id"] for d in deltas], created_at=T0)
    junctions = view["nodes"]["Junction"].values()
    legs = {leg_id(j["id"], n): (j["id"], n) for j in junctions if not j["derivation_id"].startswith("source:")
            for n in range(len(j["legs"]))}
    return {"view": view, "deltas": deltas, "dm": dm, "legs": legs,
            "sources": [j["id"] for j in junctions if j["derivation_id"].startswith("source:")],
            "papers": autoeval.Papers({pv: (papers[pv]["record"], papers[pv]["sources"]) for pv in (PV, UP)}),
            "all_papers": autoeval.Papers({pv: (papers[pv]["record"], papers[pv]["sources"]) for pv in (PV, UP, DERIV)})}


def controls(per_rule=12, rules=RULES):
    return {"positive": {"rule": "ANCHOR_IN_OWNED_PROOF_V1", "count": 5},
            "negative": {"rules": rules, "count_per_rule": per_rule}, "seed": "c"}


def plan_of(graph, **changes):
    fields = {"estimands": ["LEG_PRECISION", "LEG_RECALL"], "sample": {"per_stratum": 100, "seed": "s"}, "controls": controls(),
              "panel": [{"judge_id": "mimo-pro", "route": PRO}, {"judge_id": "terra", "route": TERRA}],
              "producers": {"leg.judge": ["mimo-v2.6-flash"]}, "created_at": T0}
    return autoeval.freeze_plan(CORPUS, graph["dm"], **{**fields, **changes})


def test_plan_needs_an_independent_panel_enough_items_and_enough_decoys(graph):
    plan = plan_of(graph)
    assert plan == plan_of(graph) and plan["plan_id"] == plan_of(graph, created_at="2026-10-01T00:00:00Z")["plan_id"]
    assert [j["instruction_sha256"] for j in plan["panel"]] == [autoeval.instruction_sha256("leg.judge")] * 2
    assert plan["producers"] == {"leg.judge": ["mimo-v2.6-flash"]}
    for panel, code in (([{"judge_id": "mimo-pro", "route": PRO}], "TOO_SMALL"),
                        ([{"judge_id": "a", "route": FLASH}, {"judge_id": "b", "route": {**FLASH, "effort": "thinking-disabled"}}],
                         "NOT_INDEPENDENT_OF_PRODUCERS"),
                        ([{"judge_id": "a", "route": PRO}, {"judge_id": "b", "route": PRO}], "IDENTICAL"),
                        ([{"judge_id": "a", "route": PRO}, {"judge_id": "a", "route": TERRA}], "REPEATED"),
                        ([{"judge_id": "a", "route": PRO}, {"judge_id": "b", "route": {**TERRA, "operation": "dependency.match_retrieved"}}],
                         "NOT_A_JUDGE_OPERATION")):
        with pytest.raises(ValueError, match=code):
            plan_of(graph, panel=panel)
    with pytest.raises(ValueError, match="TOO_SMALL: match.judge"):  # MATCH_PRECISION needs its own match.judge panel
        plan_of(graph, estimands=["LEG_PRECISION", "MATCH_PRECISION"])
    # With no decoy judged positive the Wilson upper end is z²/(n + z²); twice it must stay below 0.5, so n >= 12.
    z = autoeval.z_one_sided(0.05)
    assert autoeval.min_decoys(0.05, 2.0) == 12
    assert 2 * autoeval.rate(0, 12, z)["upper"] < autoeval.MAX_INFLATED_FPR <= 2 * autoeval.rate(0, 11, z)["upper"]
    with pytest.raises(ValueError, match="TOO_FEW_DECOYS_PER_RULE: 11 < 12"):
        plan_of(graph, controls=controls(11))
    with pytest.raises(ValueError, match="PER_STRATUM_BELOW_MIN_ITEMS: 99 < 100"):
        plan_of(graph, sample={"per_stratum": 99, "seed": "s"})
    with pytest.raises(ValueError, match="PRODUCERS_MISSING_FOR: leg.judge"):
        plan_of(graph, producers={})
    with pytest.raises(ValueError, match="NON_JUDGE_OPERATION"):
        plan_of(graph, producers={"leg.judge": ["mimo-v2.6-flash"], "paper.extract_focus": ["mimo-v2.6-flash"]})


def test_cards_are_blinded_and_decoys_match_the_premise_kind(graph, papers):
    plan, view, occ, papers = plan_of(graph), graph["view"], papers[PV]["occ"], graph["papers"]
    sample = autoeval.draw_leg_sample(plan, graph["dm"], view, T0)
    assert (sample["label_source"], sample["evaluation_plan_id"], sample["labeller_count"]) == ("AUTO_PANEL", plan["plan_id"], 2)
    strata = {(i["stratum"]["method"], i["stratum"]["method_version"], i["stratum"]["use_site"]) for i in sample["items"]}
    assert strata == {("DETERMINISTIC_ANCHOR", anchors.METHOD_VERSION, "PROOF"), ("DETERMINISTIC_ANCHOR", anchors.METHOD_VERSION, "STATEMENT"),
                      ("MODEL_EXTRACTION", "m1", "UNKNOWN")}  # the S7 source junction is judged by a match card, not here
    with pytest.raises(ValueError, match="NOT_THE_PLAN_MANIFEST"):
        autoeval.draw_leg_sample(plan, {**graph["dm"], "manifest_id": "manifest:" + "0" * 64}, view, T0)
    with pytest.raises(ValueError, match="NOT_MERGED_FROM_THE_PLAN_MANIFEST"):
        autoeval.draw_leg_sample(plan, graph["dm"], {**view, "deltas": view["deltas"][1:]}, T0)
    cards = [autoeval.leg_card(papers, view, *graph["legs"][i["subject_id"]]) for i in sample["items"]]
    for card in cards:
        assert set(card) == {"card_id", "card_sha256", "question", "conclusion", "premise", "evidence"}
        text = canonical(card).decode()
        assert not any(word in text for word in ("DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION", "junction:", "reading:", "control"))
    thm_c = next(r["id"] for r in view["nodes"]["Claim"].values() if r.get("occurrence_ids") == [occ("thm:c")])
    lem_b = next(r["id"] for r in view["nodes"]["Claim"].values() if r.get("occurrence_ids") == [occ("lem:b")])
    proof = next(j for j in view["nodes"]["Junction"].values() if j["conclusion_id"] == thm_c and j["reading_method"] == "DETERMINISTIC_ANCHOR")
    card = autoeval.leg_card(papers, view, proof["id"], 0)
    assert "Lemma~\\ref{lem:b}" in card["evidence"] and card["premise"].startswith("\\begin{lemma}")
    with pytest.raises(ValueError, match="EVIDENCE_DERIVATION_NOT_FOUND"):  # a proof derivation that names no owned proof set
        autoeval.evidence(papers, view, thm_c, "proof:sha256:" + "0" * 64)
    positive = autoeval.positive_controls(plan, view)
    assert len(positive) == 3 and all(view["nodes"]["Junction"][j]["reading_method"] == "DETERMINISTIC_ANCHOR" for j, _ in positive)
    # ENVIRONMENT premise (lem:b): a later environment of the same file, unreferenced, no premise of thm:c
    assert autoeval.near_miss_decoy(plan, papers, view, proof["id"], 0).startswith("\\begin{theorem}\\label{thm:d}")
    assert autoeval.other_paper_decoy(plan, papers, view, proof["id"], 0) in {row["text"] for row in papers(UP)["claims"].values()}
    # BIB and EQUATION premises of lem:b's proof: a bibliography entry not cited there; no later unreferenced equation
    lemma = next(j for j in view["nodes"]["Junction"].values() if j["conclusion_id"] == lem_b and j["reading_method"] == "DETERMINISTIC_ANCHOR"
                 and j["derivation_id"].startswith("proof:"))
    kinds = {autoeval._kind_of(papers, view, leg["premise_id"]): n for n, leg in enumerate(lemma["legs"])}
    assert set(kinds) == {"BIB", "EQUATION"}
    bib = autoeval.near_miss_decoy(plan, papers, view, lemma["id"], kinds["BIB"])
    assert bib.startswith("Cited work: \\bibitem{") and not any(k in bib for k in ("{Old}", "{A}", "{B}"))
    assert autoeval.near_miss_decoy(plan, papers, view, lemma["id"], kinds["EQUATION"]) is None  # eq:c is the premise itself
    wide = graph["all_papers"]
    equations = {row["text"] for row in wide(DERIV)["claims"].values() if row["kind"] == "DISPLAY_EQUATION"}
    assert autoeval.other_paper_decoy(plan, wide, view, lemma["id"], kinds["EQUATION"]) in equations
    assert autoeval.other_paper_decoy(plan, wide, view, lemma["id"], kinds["BIB"]).startswith("Cited work: \\bibitem{Old}")
    # A paper the conclusion's paper cites is never the other paper of a decoy.
    cited = copy.deepcopy(view)
    work = "work:" + "7" * 64
    cited["nodes"]["Work"][work] = {"id": work}
    entry = next(b for b in cited["nodes"]["BibEntry"].values() if b["paper_version_id"] == PV and b["citation_key"] == "A")
    for kind, start in (("VERSION_OF", UP), ("RESOLVES_TO", entry["id"])):
        rel = "rel:" + digest(f"{kind}{start}".encode())[7:]
        cited["edges"][rel] = {"id": rel, "type": kind, "start_id": start, "end_id": work, "props": {"method": "HOST_RULE", "basis": "arXiv id"}}
    assert autoeval._neighbours(cited) == {PV: {UP}, UP: {PV}}
    assert autoeval.other_paper_decoy(plan, papers, cited, proof["id"], 0) is None
    negatives, by_rule, skipped = autoeval.negative_controls(plan, papers, view, list(graph["legs"].values()))
    assert set(by_rule) == set(RULES) and all(0 < len(ids_) <= 12 for ids_ in by_rule.values()) and skipped >= 1
    made = [c["card_id"] for c in negatives]  # the three BIB legs of lem:b's proof share one decoy card: made once
    assert len(made) == len(set(made))
    assert sorted(c["card_id"] for c in negatives) == sorted(i for ids_ in by_rule.values() for i in ids_)  # each card made once
    base = {(c["conclusion"], c["evidence"]) for c in (autoeval.leg_card(papers, view, *k) for k in graph["legs"].values())}
    assert all((c["conclusion"], c["evidence"]) in base for c in negatives) and not {c["card_id"] for c in negatives} & {c["card_id"] for c in cards}
    (source,) = graph["sources"]
    with pytest.raises(ValueError, match="JUDGED_BY_A_MATCH_CARD"):
        autoeval.leg_card(papers, view, source, 0)
    with pytest.raises(ValueError, match="BASE_LEG_OF_A_SOURCE_JUNCTION"):
        autoeval.negative_controls(plan, papers, view, [(source, 0)])


def test_a_decoy_never_references_the_conclusion(graph, papers):
    p = papers[NEST]
    view = delta.merge([p["s1"], p["s3"]])
    nest = autoeval.Papers({NEST: (p["record"], p["sources"])})
    t_w = next(c for c in view["nodes"]["Claim"].values() if c["occurrence_ids"] == [p["occ"]("t:w")])
    (proof,) = [j for j in view["nodes"]["Junction"].values() if j["conclusion_id"] == t_w["id"] and j["derivation_id"].startswith("proof:")]
    assert [view["nodes"]["Claim"][leg["premise_id"]]["occurrence_ids"] for leg in proof["legs"]] == [[p["occ"]("l:y")]]
    # The only environment after t:w's proof is a corollary that cites t:w: a consequence, never an unused premise.
    assert autoeval.near_miss_decoy(plan_of(graph), nest, view, proof["id"], 0) is None


def test_proof_evidence_is_one_owned_proof_or_all_of_them():
    span = lambda start: {"path": "main.tex", "byte_start": start, "byte_end": start + 10, "span_sha256": S}
    P = {"pv": PV, "root": ".", "by_occ": {"occ:1": "c1"}, "owned": {"c1": [span(40), span(0)]}}
    sets = autoeval._proof_sets(P, {"occurrence_ids": ["occ:1"]})
    one = lambda start: ids.proof_derivation([anchors.occurrence(P, span(start))])
    both = ids.proof_derivation([anchors.occurrence(P, span(0)), anchors.occurrence(P, span(40))])
    assert sets == {one(0): [span(0)], one(40): [span(40)], both: [span(0), span(40)]}  # S3 derives per proof, S6 over all


def test_match_cards_and_hard_negative_decoys(graph):
    view, papers = graph["view"], graph["papers"]
    match = [{"judge_id": "pro-m", "route": {**PRO, "operation": "match.judge"}}, {"judge_id": "terra-m", "route": {**TERRA, "operation": "match.judge"}}]
    plan = plan_of(graph, estimands=["LEG_PRECISION", "MATCH_PRECISION"],
                   panel=[{"judge_id": "mimo-pro", "route": PRO}, {"judge_id": "terra", "route": TERRA}, *match],
                   producers={"leg.judge": ["mimo-v2.6-flash"], "match.judge": ["gpt-5.6-terra"]})
    sample = autoeval.draw_match_sample(plan, graph["dm"], view, T0)
    (source,) = graph["sources"]
    assert [(i["subject_kind"], i["subject_id"], i["stratum"]) for i in sample["items"]] == [
        ("JUNCTION", source, {"method": "MODEL_MATCH", "method_version": "match-1"})]
    card = autoeval.match_card(papers, view, source)
    assert set(card) == {"card_id", "card_sha256", "question", "conclusion", "citing_passage", "premise", "evidence"}
    assert card["question"] == "MATCH" and "Every tiny object is small." in card["evidence"]
    assert card["premise"].startswith("Cited work: \\bibitem{A}") and "\\cite{A,B}" in card["citing_passage"]
    decoys, by_rule, skipped = autoeval.match_decoys(plan, papers, view, [source])
    (near,) = decoys  # the only other statement of the upstream paper; no third supplied paper outside the citation pair
    assert by_rule == {"SAME_PAPER_NEAR_MISS_V1": [near["card_id"]], "OTHER_PAPER_DECOY_V1": []} and skipped == 1
    assert near["evidence"].startswith("\\begin{definition}\\label{d:2}")
    assert {k: near[k] for k in ("conclusion", "citing_passage", "premise")} == {k: card[k] for k in ("conclusion", "citing_passage", "premise")}
    assert autoeval.build_judge_prompt(card, "match.judge")["prompt"].startswith(autoeval.INSTRUCTIONS["match.judge"])
    with pytest.raises(ValueError, match="QUESTION_IS_NOT_THE_OPERATION"):
        autoeval.build_judge_prompt(card, "leg.judge")
    with pytest.raises(ValueError, match="NEEDS_A_SOURCE_JUNCTION"):
        autoeval.match_card(papers, view, next(iter(graph["legs"].values()))[0])
    with pytest.raises(ValueError, match="UPSTREAM_SOURCES_NOT_SUPPLIED"):  # never a model reading's text
        autoeval.match_card(autoeval.Papers({PV: graph["papers"].raw[PV]}), view, source)


def test_judgements_bind_long_quotes_and_the_panel_is_unanimous(graph):
    plan, view, papers = plan_of(graph), graph["view"], graph["papers"]
    card = autoeval.leg_card(papers, view, *next(iter(graph["legs"].values())))
    judge = lambda judge_id, row, response: autoeval.judgement(plan, judge_id, row, response, RECEIPT)
    quote = card["evidence"][:40]
    ok = judge("terra", card, {"verdict": "USED", "quote": quote, "reason": "invoked"})
    assert (ok["validity"], ok["evidence"]["byte_start"], ok["evidence"]["byte_end"]) == ("VALID", 0, len(quote.encode()))
    assert ok["evidence"]["span_sha256"] == digest(quote.encode()) and ok["judgement_id"].startswith("judgement:")
    assert ok["receipt"] == RECEIPT
    twice = autoeval._card({"question": "LEG", "conclusion": "c", "premise": "p", "evidence": "alpha beta gamma. alpha beta gamma. delta"})
    extended = judge("terra", twice, {"verdict": "USED", "quote": "alpha beta gamma.", "reason": "twice"})
    # QUOTE_RULE: the shortest unique enclosing span is " alpha beta gamma." (18 bytes), around the second occurrence
    assert extended["evidence"]["extended"] and (extended["evidence"]["byte_start"], extended["evidence"]["byte_end"]) == (17, 35)
    pad, repeated = "a" * 100, "the quoted premise sentence"
    far = autoeval._card({"question": "LEG", "conclusion": "c", "premise": "p", "evidence": pad + repeated + pad + repeated + pad})
    # telling the two copies apart needs 101 more characters, beyond MAX_QUOTE_EXTENSION = 80
    assert judge("terra", far, {"verdict": "USED", "quote": repeated, "reason": "x"})["validity"] == "EVIDENCE_UNBOUND"
    assert judge("terra", card, {"verdict": "USED", "quote": card["evidence"][:11], "reason": "short"})["validity"] == "EVIDENCE_UNBOUND"
    assert judge("terra", card, {"verdict": "USED", "quote": "not in the card at all", "reason": "x"})["validity"] == "EVIDENCE_UNBOUND"
    assert judge("terra", card, {"verdict": "USED", "quote": None, "reason": "x"})["validity"] == "EVIDENCE_UNBOUND"
    assert judge("terra", card, {"verdict": "maybe"})["validity"] == "RESPONSE_INVALID"
    no = judge("mimo-pro", card, {"verdict": "NOT_USED", "quote": "anything", "reason": "unused"})
    assert (no["validity"], no["evidence"]) == ("VALID", None)
    with pytest.raises(ValueError, match="NOT_IN_PLAN"):
        judge("claude", card, {"verdict": "NOT_USED", "quote": None, "reason": "x"})
    with pytest.raises(ValueError, match="CHANGED"):
        judge("terra", {**card, "premise": "another premise"}, {"verdict": "NOT_USED", "quote": None, "reason": "x"})
    with pytest.raises(ValueError, match="QUESTION_IS_NOT_THE_JUDGE_OPERATION"):
        judge("terra", autoeval._card({**{k: card[k] for k in ("conclusion", "premise", "evidence")}, "question": "MATCH"}),
              {"verdict": "NOT_USED", "quote": None, "reason": "x"})
    with pytest.raises(ValidationError):  # every judgement names the receipt of its call
        autoeval.judgement(plan, "terra", card, {"verdict": "NOT_USED", "quote": None, "reason": "x"}, None)
    yes = judge("mimo-pro", card, {"verdict": "USED", "quote": quote, "reason": "invoked"})
    labels, unresolved = autoeval.panel_labels(plan, "leg.judge", [ok, yes])
    assert labels == {card["card_id"]: True} and unresolved == set()
    labels, unresolved = autoeval.panel_labels(plan, "leg.judge", [ok, no])
    assert labels == {card["card_id"]: False} and unresolved == {card["card_id"]}
    for rows, code in (([ok], "INCOMPLETE"), ([ok, ok, yes], "TWICE"), ([ok, {**yes, "plan_id": "eval-plan:" + "f" * 64}], "ANOTHER_PLAN")):
        with pytest.raises(ValueError, match=code):
            autoeval.panel_labels(plan, "leg.judge", rows)


def synthetic(plan, strata, n_neg=300, false_pos=3, fp_rule=0, n_pos=50, pos_hits=48, unresolved=0):
    """A LEG_PRECISION sample over strata [(stratum, items, panel positives)] with hand-set panel labels: n_neg decoys of
    every plan rule, false_pos of them judged positive, all in rule fp_rule; n_pos positive controls."""
    population, labels, cards_of = [], {}, {}
    for s, (stratum, n_items, positives) in enumerate(strata):
        for i in range(n_items):
            population.append({"subject_kind": "LEG", "subject_id": f"leg-{s}-{i}", "stratum": stratum})
            cards_of[f"leg-{s}-{i}"] = f"card-{s}-{i}"
            labels[f"card-{s}-{i}"] = i < positives
    ref = {"path": "autoeval/leg.judge.instruction.txt", "sha256": S, "byte_size": 1}
    sample = review_sample.review_sample(plan["manifest_id"], "LEG_PRECISION", "RANDOM", "s", ref, 2, population,
                                         max(n for _, n, _ in strata), T0, label_source="AUTO_PANEL", evaluation_plan_id=plan["plan_id"])
    rules = plan["controls"]["negative"]["rules"]
    negative = {rule: [f"neg-{r}-{i}" for i in range(n_neg)] for r, rule in enumerate(rules)}
    for r, rule in enumerate(rules):
        labels.update({c: r == fp_rule and i < false_pos for i, c in enumerate(negative[rule])})
    positive = [f"pos-{i}" for i in range(n_pos)]
    labels.update({c: i < pos_hits for i, c in enumerate(positive)})
    return sample, cards_of, positive, negative, labels, {f"card-0-{i}" for i in range(strata[0][1] - unresolved, strata[0][1])}


def test_precision_lower_bound_needs_no_sensitivity_and_takes_the_worst_decoy_rule(graph):
    plan, rule = plan_of(graph), CORPUS["gates"]["P0"]
    (row,) = autoeval.precision_estimates(plan, rule, *synthetic(plan, [(EXTRACT, 120, 114)]))
    # Hand computation: Wilson(114/120, z=1.96) lower 0.89519; Wilson(3/300) upper 0.02898 (the worse rule: Wilson(0/300)
    # upper is 0.01264); inflated 0.05797.
    assert row["panel_positive"]["lower"] == pytest.approx(0.89519, abs=1e-4)
    assert row["false_positive"]["upper"] == pytest.approx(0.02898, abs=1e-4)
    assert row["false_positive_by_rule"]["OTHER_PAPER_DECOY_V1"]["upper"] == pytest.approx(0.01264, abs=1e-4)
    assert row["false_positive"] == row["false_positive_by_rule"]["SAME_PAPER_NEAR_MISS_V1"] and row["stratum"] == EXTRACT
    assert row["lower_bound"] == pytest.approx((0.89519 - 0.05797) / (1 - 0.05797), abs=2e-4)
    assert row["gate"]["decision"] == "ADMIT" and row["point"] == pytest.approx((0.95 - 0.01) / (0.96 - 0.01))
    other = autoeval.precision_estimates(plan, rule, *synthetic(plan, [(EXTRACT, 120, 114)], fp_rule=1))[0]
    assert other["false_positive"] == other["false_positive_by_rule"]["OTHER_PAPER_DECOY_V1"]
    strict = autoeval.precision_estimates(plan, {**rule, "admission_threshold": 0.9}, *synthetic(plan, [(EXTRACT, 120, 114)]))
    assert strict[0]["gate"]["decision"] == "REJECT"
    for args, why in (({}, {"min_items": 200}), ({"n_neg": 0, "false_pos": 0}, {}), ({"n_neg": 20, "false_pos": 10}, {}),
                      ({"unresolved": 40}, {})):
        (bad,) = autoeval.precision_estimates(plan, {**rule, **why}, *synthetic(plan, [(EXTRACT, 120, 114)], **args))
        assert bad["gate"]["decision"] == "NOT_ESTIMABLE" and bad["lower_bound"] is None
    sample, cards_of, positive, negative, labels, unresolved = synthetic(plan, [(EXTRACT, 120, 114)])
    (empty,) = autoeval.precision_estimates(plan, rule, sample, cards_of, positive, {**negative, "OTHER_PAPER_DECOY_V1": []}, labels, unresolved)
    assert empty["gate"]["decision"] == "NOT_ESTIMABLE" and "inflated" in empty["gate"]["reason"]  # a rule with no decoy bounds nothing
    with pytest.raises(ValueError, match="NOT_IN_THE_PLAN"):
        autoeval.precision_estimates(plan, rule, sample, cards_of, positive, {"RANDOM_TEXT_V1": []}, labels, unresolved)
    rows = autoeval.precision_estimates(plan, rule, *synthetic(plan, [(EXTRACT, 120, 114), ({**EXTRACT, "method_version": "local-1"}, 120, 60)]))
    assert [(r["stratum"]["method_version"], r["gate"]["decision"]) for r in rows] == [("focus-1", "ADMIT"), ("local-1", "REJECT")]
    # recheck() recomputes a stored row from its counts and refuses one that does not recompute
    assert autoeval.recheck(row, rule) == "ADMIT"
    for forged in ({**row, "gate": {**row["gate"], "decision": "REJECT"}}, {**row, "lower_bound": 0.99},
                   {**row, "false_positive": row["false_positive_by_rule"]["OTHER_PAPER_DECOY_V1"]},
                   {**row, "panel_positive": {**row["panel_positive"], "successes": 119}}):
        with pytest.raises(ValueError, match="DOES_NOT_RECOMPUTE"):
            autoeval.recheck(forged, rule)
    with pytest.raises(ValueError, match="DOES_NOT_RECOMPUTE"):
        autoeval.recheck(row, {**rule, "alpha": 0.1})
    # The bound holds for any sensitivity: a panel with Se = 0.8, f = 0.01 on true precision q gives p = 0.8q + 0.01(1 - q).
    for q in (0.6, 0.9, 1.0):
        p = 0.8 * q + 0.01 * (1 - q)
        assert (p - 0.01) / (1 - 0.01) <= q + 1e-12


def test_recall_counts_every_examined_conclusion_and_one_premise_per_occurrence(graph):
    plan, view = plan_of(graph), graph["view"]
    anchor = autoeval.anchor_recall(view, "m1")
    assert (anchor["counts"], anchor["estimate"]) == ({"anchored": 1, "found": 1}, 1.0)  # thm:c -> lem:b, the one anchored leg
    claims = {n: "claim:" + hex(n)[2:].rjust(64, "0") for n in range(1, 10)}
    rows = {}
    for version, pairs in (("focus-1", [(1, 3), (1, 4), (2, 5), (7, 8)]), ("local-1", [(1, 3), (2, 5), (2, 6)])):
        for c in sorted({c for c, _ in pairs}):
            j = {"id": "junction:" + digest(f"{version}{c}".encode())[7:], "conclusion_id": claims[c], "derivation_id": "unlocated:MODEL_EXTRACTION:0",
                 "reading_method": "MODEL_EXTRACTION", "method_version": version,
                 "legs": [{"premise_id": claims[p], "role": "UNCLASSIFIED", "use_site": "UNKNOWN", "flags": []} for cc, p in pairs if cc == c]}
            rows[j["id"]] = j
    read = {"reading:1": {"id": "reading:1", "claim_id": claims[7], "method": "MODEL_EXTRACTION", "method_version": "local-1"}}
    tiny = {"nodes": {"Junction": rows, "ClaimReading": read, "Claim": {}, "Placeholder": {}}}
    labels = {(claims[c], claims[p]): p != 6 for c, p in [(1, 3), (1, 4), (2, 5), (2, 6), (7, 8)]}
    assert set(autoeval.union_legs(tiny, "focus-1", "local-1")) == set(labels)
    union = autoeval.union_recall(tiny, "focus-1", "local-1", labels)
    shares = {(r["basis"], r["method"]): r["estimate"] for r in union}
    assert shares[("UNION_OF_TWO_METHODS_V1", "MODEL_EXTRACTION/focus-1")] == 1.0
    # local-1 read claim 7 and proposed no premise for it: its miss of (7, 8) counts
    assert shares[("UNION_OF_TWO_METHODS_V1", "MODEL_EXTRACTION/local-1")] == pytest.approx(2 / 4)
    assert shares[("CAPTURE_RECAPTURE_CHAPMAN_V1", "MODEL_EXTRACTION/local-1")] == pytest.approx(2 / 4)  # N = 5*3/3 - 1 = 4
    assert union[0]["counts"]["conclusions"] == 3
    with pytest.raises(ValueError, match="NOT_JUDGED"):
        autoeval.union_recall(tiny, "focus-1", "local-1", {})
    # An UNRESOLVED_OCCURRENCE premise and the whole claim of the same occurrence are one premise.
    same = copy.deepcopy(tiny)
    occ, whole, holder = "occ:" + "9" * 64, claims[9], "placeholder:" + "9" * 64
    same["nodes"]["Claim"][whole] = {"id": whole, "origin": "PAPER_VERSION", "part": "whole", "occurrence_ids": [occ]}
    same["nodes"]["Placeholder"][holder] = {"id": holder, "kind": "UNRESOLVED_OCCURRENCE", "occurrence_id": occ, "created_by_claim_id": claims[1]}
    for j in same["nodes"]["Junction"].values():
        if j["conclusion_id"] == claims[1]:
            j["legs"].append({"premise_id": whole if j["method_version"] == "focus-1" else holder, "role": "UNCLASSIFIED",
                              "use_site": "UNKNOWN", "flags": []})
    assert (claims[1], whole) in autoeval._leg_keys(same, "MODEL_EXTRACTION", "local-1")
    assert (claims[1], holder) not in autoeval._leg_keys(same, "MODEL_EXTRACTION", "local-1")
    both = autoeval.union_recall(same, "focus-1", "local-1", {**labels, (claims[1], whole): True})
    assert both[0]["counts"]["confirmed_both"] == 3
    sample, cards_of, positive, negative, marks, unresolved = synthetic(plan, [(EXTRACT, 120, 114)])
    admitted = autoeval.precision_estimates(plan, CORPUS["gates"]["P0"], sample, cards_of, positive, negative, marks, unresolved)
    composition = {"LEG_PRECISION": {"positive": len(positive), "negative_by_rule": {r: len(c) for r, c in negative.items()}, "skipped": 0}}
    inputs = autoeval.report_inputs([sample], [], [], composition)
    report = autoeval.report(plan, admitted, [anchor], inputs, T0)
    assert report["independence"] == {"judge_models": {"leg.judge": ["gpt-5.6-terra", "mimo-v2.6-pro"]},
                                      "producers": {"leg.judge": ["mimo-v2.6-flash"]}, "distinct_model_present": True}
    assert report["inputs"]["samples"] == [sample["sample_id"]] and report["inputs"]["controls"] == composition
    assert "No human audit of the panel was made." in report["assumptions"]
    with pytest.raises(ValueError, match="NOT_IN_THE_INPUTS"):
        autoeval.report(plan, admitted, [], {**inputs, "samples": []}, T0)
    audit = autoeval.human_audit({"sample_id": "review-sample:" + "a" * 64}, {"x": True, "y": False}, {"x": True, "y": True})
    assert audit["agreement"]["estimate"] == 0.5
    assert "VERIFIED" not in json.dumps(report)


# ---- cost and gates ----------------------------------------------------------------------------------------------

SIZES = [53029, 86681, 88471, 117802, 120831, 160714, 264751, 333351]  # MEASURED text sources of the v0.3 papers
PILOT = {k: {"value": v, "label": "MEASURED", "source": "synthetic pilot receipts"}
         for k, (v, label, _) in cost.PARAMETERS.items() if label == "ESTIMATED"}


def test_call_cost_and_paper_tokens_follow_the_documented_formulas(papers):
    assert PRICING_SHA == digest(PRICING_PATH.read_bytes()) and PRICING["models"]["mimo-v2.6-flash"]["realtime"]["cache_miss"] == 0.14
    usage = {"prompt_tokens": 1_000_000, "cached_tokens": 900_000, "completion_tokens": 100_000}
    assert cost.call_cost(PRICING, "mimo-v2.6-flash", usage) == pytest.approx(0.014 + 0.00252 + 0.028)
    assert cost.call_cost(PRICING, "mimo-v2.6-flash", usage, "batch") == pytest.approx((0.014 + 0.00252 + 0.028) / 2)
    with pytest.raises(ValueError):
        cost.call_cost(PRICING, "mimo-v2.6-flash", {**usage, "cached_tokens": 2_000_000})
    p = {k: v for k, (v, _, _) in cost.PARAMETERS.items()}
    calls, inp, cached, out = cost.paper_tokens(100_000, "paper.extract_focus", {"focus_bytes": 8192}, p)
    n = 62_100 / 8192
    assert calls == pytest.approx(n) and inp == pytest.approx(n * (0.4 * 100_000 * 1.05 + 2000))
    assert cached == pytest.approx((n - 1) * 42_000 * 0.9) and out == pytest.approx(62_100 * 0.887 + n * 500)
    local = cost.paper_tokens(100_000, "paper.extract_local", {"prose_bytes": 0}, p)
    assert local[2] == 0 and local[1] == pytest.approx(62_100 * 0.4 * 3 + 62_100 / 8192 * 2000)
    built = extraction.build_focus_prompts(papers[DERIV]["record"], papers[DERIV]["sources"], focus_bytes=256)
    size = sum(len(b) for b in papers[DERIV]["sources"].values())
    plan = cost.focus_plan(built, size)
    assert (plan["calls"], plan["prefix_bytes"]) == (len(built["prompts"]), built["prefix_bytes"]) and plan["focus_bytes"] > 0
    assert plan["prompt_bytes"] == sum(len(r["prompt"].encode()) for r in built["prompts"])
    calls, inp, cached, out = cost.paper_tokens(size, "paper.extract_focus", {"focus_bytes": 256}, p, plan)
    assert calls == plan["calls"] and inp == pytest.approx(0.4 * plan["prompt_bytes"])
    assert cached == pytest.approx((plan["calls"] - 1) * 0.4 * plan["prefix_bytes"] * 0.9)
    assert out == pytest.approx(plan["focus_bytes"] * 0.887 + plan["calls"] * 500)
    with pytest.raises(ValueError, match="FOCUS_MODE_ONLY"):
        cost.paper_tokens(size, "paper.extract_local", {"prose_bytes": 0}, p, plan)


def test_projection_totals_reserves_ceiling_and_context(papers):
    sizes = SIZES * 1250  # 10,000 papers with the measured size mix
    real = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0)
    batch = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "batch", sizes, T0)
    assert batch["totals"]["cost"] == pytest.approx(real["totals"]["cost"] / 2)  # every batch price is half
    assert 400 < real["totals"]["cost"] < 900 and real["under_ceiling"] and real["fits_context"]
    assert real["pricing_profile_sha256"] == PRICING_SHA and real["paper_plans"] == "MODELLED"
    assert set(real["parameters"]) == set(cost.USED[("paper.extract_focus", "MODELLED")])
    assert real["parameters"]["output_reserve_tokens"]["label"] == "POLICY"
    expected = sum(cost.paper_tokens(s, "paper.extract_focus", CORPUS["extraction"], {k: v for k, (v, _, _) in cost.PARAMETERS.items()})[0]
                   for s in sizes) * 1.2
    assert real["totals"]["calls"] == pytest.approx(expected) and real["papers"] == 10_000
    assert real["wallclock_basis"] == "REALTIME_RATE_LIMITS"
    assert real["wallclock_minutes"] == pytest.approx(max(expected / 100, (real["totals"]["input_tokens"] + real["totals"]["output_tokens"]) / 1e7))
    assert (batch["wallclock_basis"], batch["wallclock_minutes"]) == ("BATCH_COMPLETION_WINDOW", 1440)
    ceiling = real["ceiling"]
    assert (ceiling["unit"], ceiling["value"], ceiling["other_stages"], ceiling["already_spent"]) == ("USD", 2500, 0, 0)
    assert ceiling["projected"] == pytest.approx(real["totals"]["cost"])
    reserved = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0, other_stages=2000, already_spent=100,
                            reserve_basis="S7, judges and discovery at pilot rates")
    assert not reserved["under_ceiling"] and reserved["ceiling"]["basis"] == "S7, judges and discovery at pilot rates"  # > 400 + 2100
    assert cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0, other_stages=100, already_spent=100)["under_ceiling"]
    tight = manifest(budget_ceiling={"unit": "USD", "value": 100, "pricing_profile_sha256": PRICING_SHA})
    assert not cost.project(tight, PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0)["under_ceiling"]
    assert not cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "realtime", [3_000_000], T0)["fits_context"]
    with pytest.raises(ValueError, match="ANOTHER_PRICING_PROFILE"):  # the digest is of the file read, not a caller's claim
        cost.project(manifest(budget_ceiling={"unit": "USD", "value": 2500, "pricing_profile_sha256": "sha256:" + "0" * 64}),
                     PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0)
    with pytest.raises(ValueError, match="NOT_PROJECTABLE"):
        cost.project(manifest(budget_ceiling={"unit": "person-hours", "value": 1}), PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0)
    with pytest.raises(ValueError, match="OVERRIDE"):
        cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0, overrides={"guess": {}})
    with pytest.raises(ValueError, match="RESERVES"):
        cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0, other_stages=-1)
    for bad in ([0], [], [100, {}]):
        with pytest.raises(ValueError, match="SOURCE_SIZES_OR_FOCUS_PLANS"):
            cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "realtime", bad, T0)
    thinking = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "realtime", sizes, T0,
                            overrides={"reasoning_tokens_per_call": {"value": 3000, "label": "ESTIMATED", "source": "long thinking"}})
    assert thinking["totals"]["cost"] > real["totals"]["cost"] and thinking["parameters"]["reasoning_tokens_per_call"]["value"] == 3000
    built = extraction.build_focus_prompts(papers[DERIV]["record"], papers[DERIV]["sources"], focus_bytes=8192)
    plan = cost.focus_plan(built, sum(len(b) for b in papers[DERIV]["sources"].values()))
    measured = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "batch", [plan] * 3, T0)
    assert measured["paper_plans"] == "MEASURED" and set(measured["parameters"]) == set(cost.USED[("paper.extract_focus", "MEASURED")])
    assert measured["totals"]["calls"] == pytest.approx(3 * plan["calls"] * 1.2)
    assert measured["largest_prompt_tokens"] == pytest.approx(0.4 * plan["max_prompt_bytes"])
    with pytest.raises(ValueError, match="PAPER_PLANS_INVALID"):
        cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "batch", [{**plan, "calls": -1}], T0)
    local = manifest(extraction={"operation": "paper.extract_local", "method_version": "local-1", "prose_bytes": 0})
    with pytest.raises(ValueError, match="FOCUS_MODE_ONLY"):
        cost.project(local, PRICING_PATH, "mimo-v2.6-flash", "batch", [plan], T0)
    assert cost.project(local, PRICING_PATH, "mimo-v2.6-flash", "batch", SIZES, T0)["parameters"]["local_batch_bytes"]["label"] == "POLICY"


def sample_view(n_papers=3, cite=3):
    """A hand-built S1-S4 view: every sample paper cites work W1 (papers 1 and 2 inside an owned proof), only paper 1
    cites W2, and paper 1 cites paper 3."""
    pvs = [f"arxiv:2201.0000{n}v1" for n in range(1, n_papers + 1)]
    view = {"deltas": [], "nodes": {label: {} for label in delta.LABELS}, "edges": {}}
    works = {w: "work:" + digest(w.encode())[7:] for w in ("W1", "W2", "W3")}
    for w, i in works.items():
        view["nodes"]["Work"][i] = {"id": i}
    def edge(kind, start, end, **props):
        i = "rel:" + digest(f"{kind}{start}{end}".encode())[7:]
        view["edges"][i] = {"id": i, "type": kind, "start_id": start, "end_id": end, "props": props}
    for n, pv in enumerate(pvs, 1):
        for w in (["W1"] if n <= cite else []) + (["W2", "W3"] if n == 1 else []):
            bib = "bib:" + digest(f"{pv}{w}".encode())[7:]
            view["nodes"]["BibEntry"][bib] = {"id": bib, "paper_version_id": pv}
            edge("RESOLVES_TO", bib, works[w], method="HOST_RULE", basis="doi")
            if w == "W1" and n <= 2:
                h = "placeholder:" + digest(bib.encode())[7:]
                view["nodes"]["Placeholder"][h] = {"id": h, "kind": "EXTERNAL_REQUEST", "paper_version_id": pv, "bib_entry_id": bib,
                                                   "methods": ["DETERMINISTIC_ANCHOR"]}
    edge("VERSION_OF", pvs[2], works["W3"])
    return pvs, view


def sample_of(man, pvs):
    """A SAMPLE round of the given papers plus one ineligible candidate that the seeded order examines first."""
    keys = {pv: corpus.order_key(man["seed"], pv.removeprefix("arxiv:")[:-2]) for pv in pvs}
    ineligible = next(b for b in (f"2201.{n:05d}" for n in range(100, 999)) if corpus.order_key(man["seed"], b) < min(keys.values()))
    frame = [pv.removeprefix("arxiv:")[:-2] for pv in pvs] + [ineligible]
    outcomes = {pv.removeprefix("arxiv:")[:-2]: {"outcome": "ACCEPTED", "attempts": 1, "paper_version_id": pv} for pv in pvs}
    outcomes[ineligible] = {"outcome": "INELIGIBLE", "attempts": 1, "reason": "no derivation"}
    return corpus.sample_record(man, frame, outcomes, T0)


def test_p_minus_1_decides_go_expand_or_stop_from_pre_registered_rules():
    pvs, view = sample_view()
    y = {"theorem_like_environments": 2, "owned_proofs": 1, "proof_owned_anchors": 3, "junction_bearing_conclusions": 1}
    s3 = [ids.make_delta("S3", "DETERMINISTIC_ANCHOR", "v", ("PAPER_VERSION", pv), measurements={"deterministic_yield": y}) for pv in pvs]
    view["deltas"] = sorted(d["delta_id"] for d in s3)
    go = gates.p_minus_1(CORPUS, sample_of(CORPUS, pvs), view, s3, T0)
    m = go["measured"]
    assert go["decision"] == "GO" and (m["eligible_fraction"], m["undetermined_fraction"]) == (0.75, 0.0)
    assert m["works_meeting_claim_level"] == 1 and m["yield_owned_proofs"] == 3 and go["admitted_methods"] == []
    assert m["works_cited_in_proofs"] == 1 and m["works_cited_in_proofs_meeting_claim_level"] == 0 and m["papers_with_anchor_delta"] == 3
    assert m["in_sample_citation_fraction"] == pytest.approx(1 / 5)  # paper 1 cites W3, which is paper 3's own work
    rule = lambda **k: {**GATES, "P_MINUS_1": {**GATES["P_MINUS_1"], **k}}
    strict = manifest(gates=rule(claim_level={"min_works": 2, "min_citing_papers": 3}))
    expand = gates.p_minus_1(strict, sample_of(strict, pvs), view, s3, T0)
    assert expand["decision"] == "GO_WITH_EXPANSION" and "EXPANSION" in expand["reasons"][0]
    picky = manifest(gates=rule(min_eligible_fraction=0.9))
    stop = gates.p_minus_1(picky, sample_of(picky, pvs), view, s3, T0)
    assert stop["decision"] == "NO_GO" and stop["reasons"] == ["eligible fraction 0.75 < 0.9"]
    assert go["gate_id"] != expand["gate_id"] and go == gates.p_minus_1(CORPUS, sample_of(CORPUS, pvs), view, s3, T0)
    with pytest.raises(ValueError, match="ANOTHER_CORPUS"):
        gates.p_minus_1(strict, sample_of(CORPUS, pvs), view, s3, T0)
    # Yields count only the anchor delta of each paper that the view includes.
    other = ids.make_delta("S3", "DETERMINISTIC_ANCHOR", "v2", ("PAPER_VERSION", pvs[0]), measurements={"deterministic_yield": y})
    assert gates.p_minus_1(CORPUS, sample_of(CORPUS, pvs), view, [*s3, other], T0) == go
    with pytest.raises(ValueError, match="TWO_ANCHOR_DELTAS_FOR"):
        gates.p_minus_1(CORPUS, sample_of(CORPUS, pvs), {**view, "deltas": sorted([*view["deltas"], other["delta_id"]])}, [*s3, other], T0)
    # In-proof citations are the anchor pass's requests, not requests a model proposed.
    proposed = copy.deepcopy(view)
    for h in proposed["nodes"]["Placeholder"].values():
        h["methods"] = ["MODEL_EXTRACTION"]
    assert gates.p_minus_1(CORPUS, sample_of(CORPUS, pvs), proposed, s3, T0)["measured"]["works_cited_in_proofs"] == 0
    grid = gates.p_minus_1(CORPUS, sample_of(CORPUS, pvs), view, s3, T0, grid={"k=1,m=3": 0.75, "k=5,m=10": None})
    assert (grid["measured"]["eligible_fraction[k=1,m=3]"], grid["measured"]["eligible_fraction[k=5,m=10]"]) == (0.75, None)


def evaluated(plan, strata, **kw):
    """(report, [sample]) of synthetic panel labels over the strata."""
    sample, cards_of, positive, negative, labels, unresolved = synthetic(plan, strata, **kw)
    rows = autoeval.precision_estimates(plan, CORPUS["gates"]["P0"], sample, cards_of, positive, negative, labels, unresolved)
    composition = {"LEG_PRECISION": {"positive": len(positive), "negative_by_rule": {r: len(c) for r, c in negative.items()}, "skipped": 0}}
    return autoeval.report(plan, rows, [], autoeval.report_inputs([sample], [], [], composition), T0), [sample]


def test_p0_gate_recomputes_the_report_ties_the_cost_to_the_run_and_derives_the_primary_policy(graph):
    plan = plan_of(graph)
    report, samples = evaluated(plan, [(EXTRACT, 120, 114), ({**EXTRACT, "method_version": "local-1"}, 120, 60)])
    projection = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "batch", SIZES, T0, overrides=PILOT)
    decision = gates.p0(CORPUS, plan, report, projection, samples, T0)
    assert decision["decision"] == "GO" and decision["admitted_methods"] == ["HUMAN", "LIBRARY", "MODEL_EXTRACTION"]
    assert decision["measured"]["extraction_strata"] == 1  # the local-1 comparison arm is REJECT and admits nothing
    assert "MODEL_MATCH is not admitted: S7 legs stay out of importance counts" in decision["reasons"]
    assert set(decision["inputs"]) == {plan["plan_id"], report["report_id"], projection["projection_id"], samples[0]["sample_id"]}
    # The projection must rest on measured inputs, cover the run and leave room in the ceiling.
    rough = gates.p0(CORPUS, plan, report, cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "batch", SIZES, T0), samples, T0)
    assert rough["decision"] == "NO_GO" and ("the projection uses ESTIMATED parameters: cache_efficiency, instruction_tokens, "
                                             "inventory_fraction, reasoning_tokens_per_call") in rough["reasons"]
    few = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "batch", SIZES[:2], T0, overrides=PILOT)
    assert "the projection covers 2 papers < target_size 3" in gates.p0(CORPUS, plan, report, few, samples, T0)["reasons"]
    guessed = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "batch", SIZES, T0, sizes_label="ESTIMATED", overrides=PILOT)
    assert "the projection uses ESTIMATED source sizes" in gates.p0(CORPUS, plan, report, guessed, samples, T0)["reasons"]
    over = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-flash", "batch", SIZES, T0, overrides=PILOT, other_stages=2500)
    stopped = gates.p0(CORPUS, plan, report, over, samples, T0)
    assert stopped["decision"] == "NO_GO" and "the cost projection exceeds the budget ceiling" in stopped["reasons"]
    # Inputs edited after they were made, or of another model, are refused.
    with pytest.raises(ValueError, match="PROJECTION_ID_IS_NOT_THE_DIGEST"):
        gates.p0(CORPUS, plan, report, {**over, "under_ceiling": True}, samples, T0)
    with pytest.raises(ValueError, match="REPORT_ID_IS_NOT_THE_DIGEST"):
        gates.p0(CORPUS, plan, {**report, "plan_id": "eval-plan:" + "0" * 64}, projection, samples, T0)
    pro = cost.project(CORPUS, PRICING_PATH, "mimo-v2.6-pro", "batch", SIZES, T0, overrides=PILOT)
    with pytest.raises(ValueError, match="NOT_JUDGED_BY_THE_PLAN"):
        gates.p0(CORPUS, plan, report, pro, samples, T0)
    # Every row is recomputed, and the rows cover every stratum of the samples exactly once.
    first, second = report["precision"]
    forged = autoeval.report(plan, [{**first, "gate": {**first["gate"], "decision": "REJECT"}}, second], [], report["inputs"], T0)
    with pytest.raises(ValueError, match="DOES_NOT_RECOMPUTE"):
        gates.p0(CORPUS, plan, forged, projection, samples, T0)
    with pytest.raises(ValueError, match="EVERY_STRATUM_ONCE"):
        gates.p0(CORPUS, plan, autoeval.report(plan, [first], [], report["inputs"], T0), projection, samples, T0)
    with pytest.raises(ValueError, match="NOT_THE_REPORT_INPUTS"):
        gates.p0(CORPUS, plan, report, projection, [], T0)
    weak, weak_samples = evaluated(plan, [(EXTRACT, 120, 100)])
    assert gates.p0(CORPUS, plan, weak, projection, weak_samples, T0)["decision"] == "NO_GO"
    policy = gates.primary_policy(CORPUS, decision)
    assert (policy["status"], policy["importance_methods"], policy["admission_gate"]) == ("PRIMARY", ["MODEL_EXTRACTION"], decision["gate_id"])
    assert policy["policy_id"] != TEMPLATE["policy_id"]
    with pytest.raises(ValueError, match="P0_GO"):
        gates.primary_policy(CORPUS, rough)
    with pytest.raises(ValueError, match="GATE_ID_IS_NOT_THE_DIGEST"):
        gates.primary_policy(CORPUS, {**decision, "admitted_methods": ["MODEL_MATCH"]})
    # Analysis honours it on a view whose MODEL_EXTRACTION rows are all of the corpus version (here: none, S1 and S3 only).
    deltas = [d for d in graph["deltas"] if d["stage"] in ("S1", "S3")]
    view, dm = delta.merge(deltas), delta.make_manifest(CORPUS["corpus_id"], [d["delta_id"] for d in deltas], created_at=T0)
    item = {"state": "DONE", "dispatchable": False}
    coverage = corpus.coverage_report(CORPUS, [sample_of(CORPUS, [PV, UP])], {PV: ["k1"], UP: ["k2"]}, {"k1": item, "k2": item})
    bound = {"admission": decision, "corpus": CORPUS, "coverage": coverage}
    out = analysis.analyze(view, dm, policy, {}, **bound)
    assert out["policy_id"] == policy["policy_id"] and all(n["count_basis"] == "SAMPLE_ONLY" for n in out["nominations"])
    with pytest.raises(ValueError, match="MIXES_EXTRACTION_VERSIONS"):  # the graph's S6 batch is method_version m1
        analysis.analyze(graph["view"], graph["dm"], policy, {}, **bound)
    with pytest.raises(ValueError, match="NOT_BOUNDED"):
        analysis.analyze(view, dm, {**policy, "importance_methods": ["DETERMINISTIC_ANCHOR"]}, {}, **bound)
    with pytest.raises(ValueError, match="EQUAL_FULL_COVERAGE_INCOMPLETE"):
        gates.require_equal_coverage({**coverage, "complete": False, "incomplete": [PV]}, CORPUS)
    with pytest.raises(ValueError, match="ANOTHER_CORPUS_OR_EXTRACTION"):
        gates.require_equal_coverage({**coverage, "corpus_id": "corpus:" + "0" * 64}, CORPUS)
