"""End to end on a synthetic mini-corpus of three fake arXiv papers; no real paper, model, network, Neo4j or Lean.

The TeX sources below are hand-written; their v0.3-shaped extraction records come from v0.3 ``ingest.extract_paper``
itself (it needs a source inside the repository, so each lives in a transient directory removed at once). The model
responses are hand-written synthetic data. A (upstream) has a definition and a theorem; B cites A's theorem in a
lemma proof and has a two-proof theorem X in a cycle with lemma Y; C cites A (by its arXiv DOI), B and a book.
Pipeline: S1 acquisition (PaperVersion + INCLUDES), S3 anchors (+ host rule), S4 works, S6 extraction, S7 matching,
store, manifest, invariants, reviews and dispositions, projection rows loaded through a fake Neo4j client, analysis,
export_v03, v0.3 prune_graph; then a HUMAN_ENTRY PrimitiveAssertion in a corrected manifest.
"""
import re
import shutil
import tempfile
from pathlib import Path

import pytest

from core import canonical, digest
import graph as v03_graph
import ingest

import analysis
import anchors
import contracts
import corpus
import delta
import export_v03
import extraction
import ids
import invariants
import matching
import projection
import reviews
import works

W = Path(__file__).resolve().parents[2]
A, B, C = "arxiv:2401.00001v1", "arxiv:2402.00002v1", "arxiv:2403.00003v1"
TEX = {A: r"""\documentclass{article}
\begin{document}
\section{Basics}
\begin{definition}\label{def:tiny}
An object is tiny if it fits in a box.
\end{definition}

\begin{theorem}\label{thm:small}
Every tiny object (Definition~\ref{def:tiny}) is small.
\end{theorem}
\begin{proof}
Immediate from Definition~\ref{def:tiny}.
\end{proof}
\end{document}
""", B: r"""\documentclass{article}
\begin{document}
\section{Results}
We build on earlier work.

\begin{definition}\label{def:nice}
An object is nice if it is tiny and round.
\end{definition}

\begin{lemma}\label{lem:round}
Every nice object is small.
\end{lemma}
\begin{proof}
By \cite[Theorem 1]{Aup} and Definition~\ref{def:nice}.
\end{proof}

\begin{theorem}\label{thm:x}
Nice objects are stable.
\end{theorem}
\begin{proof}
Apply Lemma~\ref{lem:y}.
\end{proof}

\begin{lemma}\label{lem:y}
Stable objects are nice.
\end{lemma}
\begin{proof}
This follows from Theorem~\ref{thm:x}.
\end{proof}

\begin{proof}[Second proof of Theorem~\ref{thm:x}]
Immediate from Definition~\ref{def:nice}.
\end{proof}

\begin{thebibliography}{9}
\bibitem{Aup} A.~Author, \newblock Tiny objects, \newblock arXiv:2401.00001 (2024).
\end{thebibliography}
\end{document}
""", C: r"""\documentclass{article}
\begin{document}
\section{Applications}
\begin{theorem}[see \cite{Book}]\label{thm:app}
Every tiny object is useful.
\end{theorem}
\begin{proof}
Combine \cite{Aup2}, \cite[Theorem 2]{Bx} and \cite{Book}.
\end{proof}

\begin{thebibliography}{9}
\bibitem{Aup2} \bibinfo{author}{A. Author}, \bibinfo{title}{Tiny objects}, \bibinfo{year}{2024}, https://doi.org/10.48550/arXiv.2401.00001
\bibitem{Bx} B.~Author, \newblock Nice objects, \newblock arXiv:2402.00002 (2024).
\bibitem{Book} \bibinfo{author}{D. Writer}, \bibinfo{title}{A book about tiny things}, \bibinfo{year}{1985}.
\end{thebibliography}
\end{document}
"""}
S = digest(b"synthetic")
T0 = "2026-09-25T00:00:00Z"
TEMPLATE = {"kind": "AnalysisPolicy", "contract_version": "0.4.0", "policy_id": "policy:" + "1" * 64, "status": "PRIMARY",
            "establishment_reading": {"mode": "UNION"},
            "importance_methods": ["DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION", "MODEL_MATCH"],
            "work_identity": "EXPLICIT_IDS_ONLY", "citation_group_semantics": "AND", "cycle_policy": "FIXPOINT",
            "base_set": "ALL_ROOTS", "include_part_expansions": False, "traverse": "SAMPLE_ONLY", "count_basis": "SAMPLE_ONLY",
            "admission_gate": None, "nomination": {"rule": "FOUNDATION_V1", "threshold": 1, "top_k": 10},
            "bootstrap": {"scheme": "PAPER_REWEIGHT_V1", "replicates": 20, "seed": "boot"}, "edge_precision": None}
POLICY = {**TEMPLATE, "status": "EXPLORATORY"}  # a PRIMARY run needs a P0 admission (test_autoeval covers that path)
CORPUS = corpus.freeze_corpus_manifest({
    "field": {"primary_categories": ["quant-ph"], "date_window": {"start": "2024-01-01", "end": "2024-12-31"}},
    "sampling_frame": {"kind": "METADATA_SNAPSHOT", "sha256": S, "snapshot_date": "2026-09-01"},
    "eligibility": {"rule": "THEOREM_OR_DERIVATION_V1", "params": {"min_theorem_like": 1, "min_display_equations": 10},
                    "program_sha256": S, "parser_sha256": S}, "size_limits": {},
    "version_rule": "LATEST_ON_OR_BEFORE_SNAPSHOT", "seed": "sample-seed", "target_size": 3, "transient_retry_limit": 1,
    "coverage": "EQUAL_FULL", "extraction": {"operation": "paper.extract_local", "method_version": "m1", "prose_bytes": 0},
    "gates": {"P_MINUS_1": {"min_eligible_fraction": 0.3, "max_undetermined_fraction": 0.2,
                            "claim_level": {"min_works": 1, "min_citing_papers": 2}},
              "P0": {"admission_threshold": 0.85, "fpr_inflation": 2.0, "alpha": 0.05, "max_unresolved_fraction": 0.2,
                     "min_items": 100, "require_projection_under_ceiling": True}},
    "primary_analysis_policy": TEMPLATE, "budget_ceiling": {"unit": "calls", "value": 10}, "created_at": T0})


def meta(pv, month, redistribution):
    date = {"value": f"2024-{month:02d}-01", "kind": "ARXIV_V1", "precision": "DAY", "source": "synthetic snapshot"}
    return {"primary_category": "quant-ph", "categories": ["quant-ph"], "redistribution": redistribution, "date_v1": date,
            "date_version": date, "source_sha256": digest(TEX[pv].encode())}


def paper(pv, s1, tmp_path_factory):
    tmp = Path(tempfile.mkdtemp(prefix=".tmp-e2e-", dir=Path(__file__).parent))
    try:
        (tmp / "main.tex").write_bytes(TEX[pv].encode())
        record = ingest.extract_paper(W, pv, tmp_path_factory.mktemp("extraction"), source_catalog={}, source_descriptor={
            "paper_id": pv, "artifact": (tmp / "main.tex").relative_to(W).as_posix(), "source_root": tmp.relative_to(W).as_posix()})
        sources = {row["path"]: (W / row["path"]).read_bytes() for row in record["source_files"]}
    finally:
        shutil.rmtree(tmp)
    P, s3 = anchors.index(record, sources), anchors.build_anchor_delta(record, sources, parents=[s1["delta_id"]])
    occ = lambda label: P["occ"][record["labels"][label][0]["claim_ids"][0]]
    claim = lambda label: next(row["id"] for row in s3["nodes"]["Claim"] if row["occurrence_ids"] == [occ(label)])
    return {"record": record, "sources": sources, "s3": s3, "occ": occ, "claim": claim,
            "s4": works.build_work_delta(s3, record), "restates": anchors.build_restates_delta(record, sources, s3)}


def requests_of(s3):
    keys = {row["id"]: row["citation_key"] for row in s3["nodes"]["BibEntry"]}
    return {keys[row["bib_entry_id"]]: row for row in s3["nodes"]["Placeholder"] if row["kind"] == "EXTERNAL_REQUEST"}


def match(upstream, pairs, *, parents):
    """S7 for one pool: every request (key, citing paper) → the claim whose reading contains its quotation."""
    items = []
    for s3, key, quote in pairs:
        request = requests_of(s3)[key]
        citing = next(r for r in s3["nodes"]["ClaimReading"] if r["claim_id"] == request["created_by_claim_id"])
        upstream_pairs = [(c, r) for c in upstream["nodes"]["Claim"] for r in upstream["nodes"]["ClaimReading"] if r["claim_id"] == c["id"]]
        items.append(({"request": request, "citing": citing,
                       "candidates": matching.retrieve_candidates(request, citing, upstream_pairs, 2)}, quote))
    context = matching.build_match_prompt(upstream["subject"]["id"], [item for item, _ in items])["context"]
    rows = []
    for item, quote in items:
        target = next(row for row in item["candidates"] if quote in row["text"])
        rows.append({"target_request_id": item["request"]["id"], "upstream_occurrence_ids": [], "upstream_claim_ids": [target["claim_id"]],
                     "relation": "CANDIDATE_SUPPORT", "combination": "SINGLE_CLAIM", "extra_conditions": [], "proof_issues": [],
                     "source_quotes": [{"path": target["claim_id"], "exact_text": quote}], "reason": "synthetic", "confidence": 0.9})
    return matching.match_rows_to_delta(context, {"matches": rows}, method_version="match-1", parents=parents)


class Neo4jFake:
    """Answers like an empty-then-filled Neo4j; checks every template reads only row fields and parameters it is sent."""

    def __init__(self):
        self.calls, self.audits = [], {query for _, query in projection.AUDITS}

    def run(self, statement, parameters, tx_metadata):
        self.calls.append(statement)
        assert set(re.findall(r"\$(\w+)", statement)) <= set(parameters), statement
        fields = set(re.findall(r"\brow\.(\w+)", statement))
        assert all(fields <= set(row) for row in parameters.get("rows", ())), statement
        if statement.endswith("AS n"):
            return [{"n": len(parameters["rows"])}]
        return []


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    metadata = {A: meta(A, 1, "OPEN"), B: meta(B, 2, "RESTRICTED"), C: meta(C, 3, "RESTRICTED")}
    sample = corpus.sample_record(CORPUS, [pv.removeprefix("arxiv:")[:-2] for pv in metadata],
                                  {pv.removeprefix("arxiv:")[:-2]: {"outcome": "ACCEPTED", "attempts": 1, "paper_version_id": pv}
                                   for pv in metadata}, T0)
    s1 = corpus.includes_delta(sample, CORPUS, metadata)  # the only delta asserting PaperVersion rows
    papers = {pv: paper(pv, s1, tmp_path_factory) for pv in metadata}
    pa, pb, pc = papers[A], papers[B], papers[C]
    # S6: a synthetic model reading of B's lemma that proposes the \cite but omits the definition (a bracket).
    batch = extraction.build_local_prompt(pb["record"], pb["sources"], [pb["occ"]("lem:round")], prose_bytes=200)["context"]
    response = {"claims": [{"source_occurrence_ids": [pb["occ"]("lem:round")], "source_locators": [], "kind": "lemma",
                            "statement": "Every nice object is small.", "conditions": [], "internal_support_occurrence_ids": [],
                            "internal_support_claim_indexes": [], "external_citation_keys": ["Aup"],
                            "external_mention_citation_keys": [], "unresolved_dependencies": [], "confidence": 0.7}],
                "unread_or_uncertain_scope": []}
    s6 = extraction.response_to_delta(pb["record"], pb["sources"], batch, response, method_version="extract-1",
                                      parents=[pb["s3"]["delta_id"]])
    s7a = match(pa["s3"], [(pb["s3"], "Aup", "Every tiny object"), (pc["s3"], "Aup2", "Every tiny object")],
                parents=[pa["s3"]["delta_id"], pb["s3"]["delta_id"], pc["s3"]["delta_id"]])
    s7b = match(pb["s3"], [(pc["s3"], "Bx", "Nice objects are stable.")], parents=[pb["s3"]["delta_id"], pc["s3"]["delta_id"]])
    deltas = [s1, s6, s7a, s7b, *(p[k] for p in papers.values() for k in ("s3", "restates", "s4"))]
    # HUMAN_ENTRY: a person asserts A's definition as a standard notion; kept out of the first manifest.
    def_tiny = pa["claim"]("def:tiny")
    primitive = ids.seal("PrimitiveAssertion", {"claim_id": def_tiny, "method": "HUMAN", "basis": "STANDARD_NOTION"})
    human = ids.make_delta("HUMAN_ENTRY", "HUMAN", "entry-1", ("PAPER_VERSION", A), {"PrimitiveAssertion": [primitive]},
                           [ids.edge("ASSERTS_PRIMITIVE", primitive["id"], def_tiny)], parents=[pa["s3"]["delta_id"]])
    store = delta.DeltaStore(tmp_path_factory.mktemp("store"))
    for row in [*deltas, human]:
        store.put(row)
    manifest = delta.make_manifest(CORPUS["corpus_id"], [row["delta_id"] for row in deltas], created_at=T0)
    view = delta.check_manifest(manifest, store)
    ids_ = {"def_tiny": pa["claim"]("def:tiny"), "thm_small": pa["claim"]("thm:small"), "def_nice": pb["claim"]("def:nice"),
            "lem_round": pb["claim"]("lem:round"), "thm_x": pb["claim"]("thm:x"), "lem_y": pb["claim"]("lem:y"),
            "thm_app": pc["claim"]("thm:app"), "R_B": requests_of(pb["s3"])["Aup"]["id"], "R_C": requests_of(pc["s3"])["Aup2"]["id"],
            "R_C2": requests_of(pc["s3"])["Bx"]["id"], "R_Book": requests_of(pc["s3"])["Book"]["id"]}
    return {"papers": papers, "s1": s1, "s6": s6, "s7a": s7a, "s7b": s7b, "human": human, "sample": sample, "deltas": deltas,
            "manifest": manifest, "view": view, "store": store, "id": ids_}


def named(run):
    """id -> short name, junctions as 'J>' + the name of their conclusion."""
    names = {v: k for k, v in run["id"].items()}
    names.update({j: "J>" + names[row["conclusion_id"]] for j, row in run["view"]["nodes"]["Junction"].items()})
    return names


def signed_reviews(view, run):
    """ACCEPT the S7 junction resolving R_B and the S3 leg lem:round -> R_B; one review of since-changed content."""
    s3_lemma = next(j for j in view["nodes"]["Junction"].values()
                    if j["conclusion_id"] == run["id"]["lem_round"] and j["reading_method"] == "DETERMINISTIC_ANCHOR")
    source = next(j for j in run["s7a"]["nodes"]["Junction"] if j["conclusion_id"] == run["id"]["R_B"])
    wanted = {("JUNCTION", source["id"]), ("LEG", reviews.leg_id(s3_lemma["id"], 0)), ("JUNCTION", s3_lemma["id"])}
    out = [{**row, "decision": "ACCEPT", "reviewer": "synthetic reviewer", "basis": "synthetic", "reviewed_at": T0,
            **({"subject_sha256": S} if row["subject_id"] == s3_lemma["id"] else {})}  # this one reviewed other content
           for row in reviews.template(view) if (row["subject_kind"], row["subject_id"]) in wanted]
    return out, source["id"], reviews.leg_id(s3_lemma["id"], 0), s3_lemma


def test_stage1_deltas_merge_into_one_closed_manifest_with_zero_violations(run):
    view, i = run["view"], run["id"]
    assert {label: len(rows) for label, rows in view["nodes"].items()} == {
        "PaperVersion": 3, "Work": 5, "BibEntry": 4, "Claim": 7, "ClaimReading": 8, "Junction": 11, "Placeholder": 4,
        "PrimitiveAssertion": 0}
    assert invariants.check(view, POLICY["work_identity"]) == []  # G1-G15, G6 on every id (BIB_DIGEST work included)
    assert view["nodes"]["Placeholder"][i["R_B"]]["methods"] == ["DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION"]  # S3 = S6 row
    assert len(view["nodes"]["Placeholder"][i["R_B"]]["asserted_by"]) == 2
    assert {w["identity_basis"] for w in view["nodes"]["Work"].values()} == {"ARXIV_BASE", "DOI", "BIB_DIGEST"}
    includes = [e for e in view["edges"].values() if e["type"] == "INCLUDES"]
    assert sorted(e["end_id"] for e in includes) == [A, B, C] and {e["start_id"] for e in includes} == {CORPUS["corpus_id"]}
    restates = [e for e in view["edges"].values() if e["type"] == "RESTATES_RESULT_OF"]
    assert [e["start_id"] for e in restates] == [i["thm_app"]]
    assert {r["kind"] for r in view["nodes"]["Placeholder"].values()} == {"EXTERNAL_REQUEST"}
    store = run["store"]
    assert all(store.get(row["delta_id"]) == row for row in run["deltas"])
    b3 = run["papers"][B]["s3"]["delta_id"]  # dropping B's S3 leaves S6/S7 parents and B's endpoints dangling
    partial = delta.make_manifest(CORPUS["corpus_id"], [d["delta_id"] for d in run["deltas"] if d["delta_id"] != b3])
    with pytest.raises(ValueError, match=f"parent {b3} not included"):
        delta.check_manifest(partial, store)
    s1 = run["s1"]  # S1 alone: every accepted paper keeps its PaperVersion row, so no INCLUDES edge dangles
    assert (s1["stage"], s1["method"]) == ("S1", "HOST_RULE") and all("PaperVersion" not in p["s3"]["nodes"] for p in run["papers"].values())
    alone = delta.check_manifest(delta.make_manifest(CORPUS["corpus_id"], [s1["delta_id"]]), store)
    assert sorted(alone["nodes"]["PaperVersion"]) == [A, B, C] and invariants.check(alone) == []
    assert {row["parser_sha256"] for row in alone["nodes"]["PaperVersion"].values()} == {CORPUS["eligibility"]["parser_sha256"]}
    assert run["papers"][A]["s3"]["measurements"]["deterministic_yield"]["theorem_like_environments"] == 1


def test_reviews_dispositions_projection_and_load(run):
    view, i = run["view"], run["id"]
    filled, source, leg, s3_lemma = signed_reviews(view, run)
    loaded = reviews.load(view, filled)
    assert sorted(loaded["accepted"]) == sorted([("JUNCTION", source), ("LEG", leg)])
    assert [r["reason"] for r in loaded["rejections"]] == ["SUBJECT_CHANGED_SINCE_REVIEW"]
    assert invariants.check(view, POLICY["work_identity"], loaded["accepted"]) == []
    dispositions = reviews.derive_dispositions(view, filled)
    assert {k: len(v) for k, v in dispositions.items() if v} == {"JUNCTION": 11, "LEG": 14, "WORK_IDENTITY": 5}
    rows = projection.project(view, run["manifest"], dispositions)
    assert {g: len(rs) for g, rs in rows["nodes"].items()} == {
        "BibEntry": 4, "Claim": 7, "ClaimReading": 8, "Corpus": 1, "ExternalRequest": 4, "Junction": 11, "PaperVersion": 3, "Work": 5}
    assert {t: len(rs) for t, rs in rows["rels"].items()} == {
        "CONCLUDES": 11, "HAS_ENTRY": 4, "INCLUDES": 3, "PREMISE_OF": 14, "READS": 8, "REQUESTS_FROM": 4,
        "RESOLVES_TO": 4, "RESTATES_RESULT_OF": 1, "SAME_WORK": 1, "STATES": 7, "VERSION_OF": 3}
    signed = {r["id"] for rs in (*rows["nodes"].values(), *rows["rels"].values()) for r in rs
              if r["props"].get("disposition") == reviews.SIGNED}
    assert signed == {source, leg}
    claims = view["nodes"]["Claim"]
    shown = {claims[r["props"]["claim_id"]]["paper_version_id"] for r in rows["nodes"]["ClaimReading"] if "display_text" in r["props"]}
    assert shown == {A}  # I-13: only the OPEN paper's verbatim text reaches the projection
    legs = [r for r in rows["rels"]["PREMISE_OF"] if r["end"] == s3_lemma["id"]]
    assert [(r["start"], r["props"]["position"]) for r in legs] == [(i["R_B"], 0), (i["def_nice"], 1)]
    manifest = projection.projection_manifest(run["manifest"], reviews.review_set_digest(filled))
    fake = Neo4jFake()
    ready = projection.load(fake, rows, manifest)
    contracts.validate("ProjectionManifest", ready)
    assert ready["state"] == "READY" and ready["review_set_digest"] == reviews.review_set_digest(list(reversed(filled)))
    assert {name: ready["audit_counts"][name] for name, _ in projection.AUDITS} == {name: 0 for name, _ in projection.AUDITS}
    assert ready["audit_counts"]["PREMISE_OF"] == 14 and ready["audit_counts"]["Corpus"] == 1
    assert fake.calls[-1] == projection.SET_MANIFEST and len(fake.audits & set(fake.calls)) == len(projection.AUDITS)


def test_analysis_layers_brackets_and_nominations(run):
    view, i, name = run["view"], run["id"], named(run)
    filled, _, leg, _ = signed_reviews(view, run)
    out = analysis.analyze(view, run["manifest"], POLICY, reviews.derive_dispositions(view, filled))
    metrics = {m["subject_id"]: m for m in out["metrics"]}
    assert {name[n]: metrics[n]["layer"] for n in i.values()} == {
        "def_tiny": 0, "thm_small": 1, "R_B": 1, "R_C": 1, "def_nice": 0, "lem_round": 2, "thm_x": 1, "lem_y": 2,
        "R_C2": 1, "R_Book": 0, "thm_app": 2}  # §4.1: X is finite through its second proof although X <-> Y is a cycle
    assert {name[n] for n in i.values() if metrics[n]["in_cycle"]} == {"thm_x", "lem_y"}
    assert all(metrics[n]["route_status"] == "FINITE" for n in i.values())
    assert metrics[i["thm_app"]]["layer_basis"] == ["DEFINITION_NO_SUPPORT_PROPOSED", "EXTERNAL_REQUEST"]
    nice, tiny = metrics[i["def_nice"]], metrics[i["def_tiny"]]
    # The model reading of lem:round omits def:nice, so that leg is only in the union: a bracket.
    assert nice["dependents"] == {"lower": 3, "upper": 4, "exactness": "EXACT"} and nice["dependent_papers"] == {"lower": 1, "upper": 1}
    assert nice["necessary_dependents"] == {"ALL_ROOTS": {"lower": 3, "upper": 4}, "PRIMITIVE_ASSERTED": {"lower": 0, "upper": 0}}
    assert tiny["dependents"] == {"lower": 3, "upper": 3, "exactness": "EXACT"} and tiny["dependent_papers"] == {"lower": 2, "upper": 2}
    assert tiny["dependent_papers_by_depth"] == {"1": {"lower": 0, "upper": 0}, "2": {"lower": 0, "upper": 0}, "3": {"lower": 2, "upper": 2}}
    assert metrics[i["R_B"]]["uncertainty"] == [
        {"method": "DETERMINISTIC_ANCHOR", "role": "UNCLASSIFIED", "disposition": reviews.SIGNED, "legs": 1},
        {"method": "MODEL_EXTRACTION", "role": "UNCLASSIFIED", "disposition": reviews.UNREVIEWED, "legs": 1}]
    assert out["diagnostics"]["CYCLE"] == [sorted([i["thm_x"], i["lem_y"]])] and out["diagnostics"]["READING_CONFLICT_CYCLE"] == []
    arxiv_a, doi_a = (works.work_row(*k)["id"] for k in (("ARXIV_BASE", "2401.00001"), ("DOI", "10.48550/arxiv.2401.00001")))
    work_a, work_b = min(arxiv_a, doi_a), works.work_row("ARXIV_BASE", "2402.00002")["id"]
    book = next(w for w, row in view["nodes"]["Work"].items() if row["identity_basis"] == "BIB_DIGEST")
    name.update({work_a: "W_A", work_b: "W_B", book: "W_Book"})
    got = [(n["list"], name[n["subject_id"]], n["rank_interval"]["lower"], n["rank_interval"]["upper"], n["dependent_papers"]["lower"],
            n["layer"], n["next_action"]) for n in out["nominations"]]
    assert got == [("DEFINITIONS", "def_tiny", 1, 1, 2, 0, "EXTRACT"), ("DEFINITIONS", "def_nice", 2, 2, 1, 0, "EXTRACT"),
                   ("WORKS", "W_Book", 1, 1, 1, "UNRESOLVED", "LIBRARY_AUDIT"),
                   ("LOW_LAYER_BY_OPEN_PREMISES", "thm_small", 1, 2, 2, 1, "EXTRACT"),
                   ("LOW_LAYER_BY_OPEN_PREMISES", "W_A", 1, 2, 2, 1, "HUMAN_REVIEW"),
                   ("LOW_LAYER_BY_OPEN_PREMISES", "thm_x", 3, 4, 1, 1, "EXTRACT"),
                   ("LOW_LAYER_BY_OPEN_PREMISES", "W_B", 3, 4, 1, 1, "HUMAN_REVIEW")]
    nominated = {name[n["subject_id"]]: n for n in out["nominations"]}
    assert [[name[x] for x in path] for path in nominated["def_tiny"]["witness_paths"]] == [
        ["def_tiny", "J>thm_small", "thm_small", "J>R_B", "R_B", "J>lem_round", "lem_round"],
        ["def_tiny", "J>thm_small", "thm_small", "J>R_C", "R_C", "J>thm_app", "thm_app"]]
    assert nominated["W_Book"]["blockers"] == ["WORK_UNRESOLVED"] and nominated["def_nice"]["blockers"] == [
        "NO_MODEL_EXTRACTION", "NO_SUPPORT_PROPOSED", "OPEN_PREMISE:DEFINITION_NO_SUPPORT_PROPOSED"]
    fraction = {k: n["bootstrap_top_k_fraction"] for k, n in nominated.items()}  # equal dependent-paper sets resample alike
    assert fraction["def_tiny"] == fraction["thm_small"] == fraction["W_A"] >= fraction["def_nice"] == fraction["thm_x"] == \
        fraction["W_B"] == fraction["W_Book"] > 0
    assert "VERIFIED" not in repr(out) and out["perturbation"] is None


def test_export_v03_of_nominations_is_accepted_by_v03_prune_graph(run):
    view, i, name = run["view"], run["id"], named(run)
    dispositions = reviews.derive_dispositions(view, signed_reviews(view, run)[0])
    out = analysis.analyze(view, run["manifest"], POLICY, dispositions)
    nominated = {n["subject_id"]: n for n in out["nominations"]}
    cyclic = export_v03.export_v03(nominated[i["thm_x"]], view, run["manifest"], POLICY, dispositions)
    graph, record = cyclic["graph"], cyclic["record"]
    assert {name[n["id"]]: n["kind"] for n in graph["nodes"]} == {"thm_x": "theorem", "lem_y": "lemma", "def_nice": "definition"}
    assert sorted((name[g["target"]], tuple(name[m] for m in g["members"]), g["relation"]) for g in graph["support_groups"]) == [
        ("lem_y", ("thm_x",), "PROOF_DEPENDENCY"), ("thm_x", ("def_nice",), "PROOF_DEPENDENCY"), ("thm_x", ("lem_y",), "PROOF_DEPENDENCY")]
    assert record["graph_sha256"] == digest(canonical(graph)) and record["manifest_id"] == run["manifest"]["manifest_id"]
    pruned = v03_graph.prune_graph(graph["nodes"], graph["support_groups"], record["query_ids"])
    assert any(set(scc["members"]) == {i["thm_x"], i["lem_y"]} for scc in pruned["sccs"])
    assert i["thm_x"] in pruned["selected_node_ids"] and "VERIFIED" not in repr(pruned)
    plain = export_v03.export_v03(nominated[i["thm_small"]], view, run["manifest"], POLICY, dispositions)
    assert [(name[g["target"]], [name[m] for m in g["members"]]) for g in plain["graph"]["support_groups"]] == [
        ("thm_small", ["def_tiny"])]  # its statement and proof junctions join into one v0.3 group
    assert sum(len(loss["legs"]) for loss in plain["record"]["losses"]) == 2
    pruned = v03_graph.prune_graph(plain["graph"]["nodes"], plain["graph"]["support_groups"], plain["record"]["query_ids"])
    assert set(pruned["selected_node_ids"]) == {i["thm_small"], i["def_tiny"]}


def test_human_entry_primitive_assertion_gives_a_primitive_basis_theorem_like_nomination(run):
    """D3: a HUMAN_ENTRY delta joins a corrected manifest; def:tiny becomes a PRIMITIVE root, so thm:small (layer 1)
    rests only on allowed roots and moves from LOW_LAYER_BY_OPEN_PREMISES to THEOREM_LIKE."""
    i, human = run["id"], run["human"]
    assert (human["stage"], human["method"], human["parents"]) == ("HUMAN_ENTRY", "HUMAN", [run["papers"][A]["s3"]["delta_id"]])
    manifest = delta.make_manifest(CORPUS["corpus_id"], [*run["manifest"]["deltas"], human["delta_id"]],
                                   parent_manifest_id=run["manifest"]["manifest_id"], created_at=T0)
    view = delta.check_manifest(manifest, run["store"])
    assert invariants.check(view, POLICY["work_identity"]) == []
    out = analysis.analyze(view, manifest, POLICY, reviews.derive_dispositions(view, []))
    metrics = {m["subject_id"]: m for m in out["metrics"]}
    assert metrics[i["def_tiny"]]["root_class"] == "PRIMITIVE" and metrics[i["thm_small"]]["layer_basis"] == ["PRIMITIVE"]
    theorem = next(n for n in out["nominations"] if n["subject_id"] == i["thm_small"])
    assert (theorem["list"], theorem["layer"], theorem["dependent_papers"]["lower"], theorem["next_action"], theorem["blockers"]) == (
        "THEOREM_LIKE", 1, 2, "EXTRACT", ["NO_MODEL_EXTRACTION"])
    before = analysis.analyze(run["view"], run["manifest"], POLICY, reviews.derive_dispositions(run["view"], []))
    assert [n["list"] for n in before["nominations"] if n["subject_id"] == i["thm_small"]] == ["LOW_LAYER_BY_OPEN_PREMISES"]
