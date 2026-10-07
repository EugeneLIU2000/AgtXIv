"""Builders (ids, anchors, extraction, matching, works) on two small synthetic TeX papers (citing and upstream).

The v0.3 records come from v0.3 ``ingest.extract_paper`` itself, run on the synthetic sources below; that
reader needs a source inside the repository, so each lives in a transient directory removed at once.
No model, network, Neo4j or Lean; model responses are hand-written synthetic data.
"""
import copy
import json
import shutil
import tempfile
from pathlib import Path

import jsonschema
import pytest

from core import canonical, digest
import ingest

import anchors
import contracts
import delta
import extraction
import ids
import invariants
import matching
import works

W = Path(__file__).resolve().parents[2]
PV, UP = "arxiv:2999.99999v1", "arxiv:2101.00002v1"
TEX = r"""\documentclass{article}
\begin{document}
\section{Introduction}
We study tiny objects, following \cite{Book}.

\begin{definition}\label{def:a}
An object is nice if it is small.
\end{definition}

\begin{lemma}\label{lem:b}
Every nice object is tiny. Every tiny object is nice, by Definition~\ref{def:a}.
\end{lemma}
\begin{proof}
Use \cite[Theorem 3.2]{Old}, equation \eqref{eq:c} and \cite{A,B}.
\end{proof}

\begin{equation}\label{eq:c}
x = y
\end{equation}

\begin{theorem}[Folklore \cite{Old}]\label{thm:c}
Tiny objects exist.
\end{theorem}
\begin{proof}
Immediate from Lemma~\ref{lem:b}; compare Theorem~\ref{thm:c} and Section~\ref{sec:none}.
\end{proof}

\begin{theorem}\label{thm:d}
Big objects exist \cite{Book}.
\end{theorem}

The next proof is deferred.

\begin{proof}[Proof of Theorem~\ref{thm:d}]
By Lemma~\ref{lem:b} and Theorem~\ref{thm:c}.
\end{proof}

\begin{thebibliography}{9}
\bibitem{Old} A.~Author, \newblock Old results on tiny things, \newblock J. Tiny 1 (1990), doi:10.1000/ABC.1
\bibitem{A} B.~Author, \newblock New tiny results, \newblock arXiv:2101.00002 (2021).
\bibitem{B} \bibinfo{author}{C. Author}, \bibinfo{title}{Another tiny paper}, \bibinfo{year}{2020}, https://doi.org/10.48550/arXiv.2101.00003
\bibitem{Book} \bibinfo{author}{D. Writer}, \bibinfo{title}{A book about tiny things}, \bibinfo{year}{1985}.
\bibitem{Misc} Private communication.
\end{thebibliography}
\end{document}
"""
UP_TEX = r"""\documentclass{article}
\begin{document}
Preliminary remarks on small things.

\begin{theorem}\label{t:1}
Every tiny object is small.
\end{theorem}

\begin{definition}\label{d:2}
An object is tiny if it is nice.
\end{definition}
\end{document}
"""
DATE = {"value": "2999-01-01", "kind": "ARXIV_V1", "precision": "DAY", "source": "synthetic"}
META = {"primary_category": "quant-ph", "categories": ["quant-ph"], "redistribution": "RESTRICTED", "date_v1": DATE,
        "date_version": DATE, "source_sha256": digest(b"source"), "parser_sha256": digest(b"parser")}


def acquired(pv):
    """A stand-in S1 delta asserting the PaperVersion row, which S3 never re-asserts (corpus.includes_delta is the real one)."""
    base, version = ids.paper_version_parts(pv)
    return ids.make_delta("S1", "HOST_RULE", "v", ("PAPER_VERSION", pv),
                          {"PaperVersion": [ids.seal("PaperVersion", {**META, "arxiv_base_id": base, "version": version})]})


def extract(paper_id, tex, tmp_path_factory):
    tmp = Path(tempfile.mkdtemp(prefix=".tmp-builders-", dir=Path(__file__).parent))
    try:
        (tmp / "main.tex").write_bytes(tex.encode())
        record = ingest.extract_paper(W, paper_id, tmp_path_factory.mktemp("extraction"), source_catalog={}, source_descriptor={
            "paper_id": paper_id, "artifact": (tmp / "main.tex").relative_to(W).as_posix(), "source_root": tmp.relative_to(W).as_posix()})
        sources = {row["path"]: (W / row["path"]).read_bytes() for row in record["source_files"]}
    finally:
        shutil.rmtree(tmp)
    P, s1 = anchors.index(record, sources), acquired(paper_id)
    return {"record": record, "sources": sources, "P": P, "occ": lambda key: P["occ"][record["labels"][key][0]["claim_ids"][0]],
            "s1": s1, "s3": anchors.build_anchor_delta(record, sources, parents=[s1["delta_id"]])}


@pytest.fixture(scope="module")
def paper(tmp_path_factory):
    out = extract(PV, TEX, tmp_path_factory)
    ctx = extraction.build_local_prompt(out["record"], out["sources"], [out["occ"]("lem:b"), out["occ"]("thm:c")], prose_bytes=0)["context"]
    out["s6"] = extraction.response_to_delta(out["record"], out["sources"], ctx, split_response(out["occ"]), method_version="m1",
                                             parents=[out["s3"]["delta_id"]])
    return {**out, "up": extract(UP, UP_TEX, tmp_path_factory)}


def by(delta, label):
    return {row["id"]: row for row in delta["nodes"].get(label, [])}


def claim_of(s3, occ):
    return next(row["id"] for row in s3["nodes"]["Claim"] if row["occurrence_ids"] == [occ])


def all_node_ids(*deltas):
    return {row["id"] for delta in deltas for rows in delta["nodes"].values() for row in rows}


def assert_clean(delta):
    text = json.dumps(delta)
    assert "VERIFIED" not in text
    assert not {"state", "disposition", "layer", "coverage", "rank", "blocker"} & {
        key for rows in delta["nodes"].values() for row in rows for key in row}
    assert not {edge["type"] for edge in delta["edges"]} & {"PREMISE_OF", "CONCLUDES"}


# ids ---------------------------------------------------------------------------------------------

def test_ids_are_untruncated_digests_of_identity_fields(paper):
    claim = ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": PV, "occurrence_ids": ["occ:" + "b" * 64, "occ:" + "a" * 64], "part": "whole"})
    ident = {"origin": "PAPER_VERSION", "paper_version_id": PV, "occurrence_ids": ["occ:" + "a" * 64, "occ:" + "b" * 64], "part": "whole"}
    assert claim["id"] == "claim:" + digest(canonical(ident))[7:] and claim["content_sha256"] == digest(canonical(ident))
    assert ids.occurrence_id(PV, "main.tex", 0, 5, digest(b"x")).startswith("occ:") and len(ids.make_id("x", 1)) == 66
    assert ids.proof_derivation(["occ:2", "occ:1"]) == "proof:" + digest(canonical(["occ:1", "occ:2"]))
    assert ids.source_derivation(UP, ["claim:b", "claim:a"]) == f"source:{UP}:" + digest(canonical(["claim:a", "claim:b"]))
    body = lambda row: {k: v for k, v in row.items() if k not in ("id", "content_sha256")}
    for label, rows in [*paper["s3"]["nodes"].items(), ("Edge", paper["s3"]["edges"])]:  # G6: ids recompute from rows
        assert all(ids.seal(label, body(row)) == row for row in rows)
    assert ids.seal("Claim", {**body(paper["s3"]["nodes"]["Claim"][0]), "part": "part:0"})["id"] != paper["s3"]["nodes"]["Claim"][0]["id"]
    book = works.work_row("BIB_DIGEST", digest(b"book"))  # the digest is a row field, so G6 recomputes the id
    assert book["bib_digest"] == digest(b"book") and ids.seal("Work", body(book)) == book
    located = lambda text: ids.seal("Claim", {"origin": "WORK_LOCATOR", "work_id": "work:" + "e" * 64, "occurrence_ids": [],
                                              "part": "whole", "work_locator_text": text})["id"]
    assert located("Thm 10.1, p. 437") != located("Thm 4.2")  # two results of one book are two claims


def test_relationship_ids_and_logical_edges():
    j = "junction:" + "c" * 64
    assert ids.edge("PREMISE_OF", "claim:" + "a" * 64, j, {"position": 0, "role": "UNCLASSIFIED", "use_site": "PROOF"})["id"] == \
        ids.edge("PREMISE_OF", "claim:" + "b" * 64, j, {"position": 0, "role": "PROOF_DEPENDENCY", "use_site": "UNKNOWN"})["id"]
    assert ids.edge("SAME_WORK", "work:1", "work:2", {"basis": "HUMAN"})["id"] != ids.edge("SAME_WORK", "work:1", "work:2", {"basis": "MODEL_MATCH"})["id"]
    junction = ids.seal("Junction", {"conclusion_id": "claim:" + "d" * 64, "derivation_id": "statement", "reading_method": "HUMAN",
                                     "method_version": "v", "grouping_basis": "x", "legs": [
                                         {"premise_id": "claim:" + k * 64, "role": "UNCLASSIFIED", "use_site": "STATEMENT", "flags": []} for k in "ab"]})
    rows = ids.logical_edges(junction)
    assert [row["type"] for row in rows] == ["PREMISE_OF", "PREMISE_OF", "CONCLUDES"] and [r["props"].get("position") for r in rows] == [0, 1, None]
    for row in rows:
        contracts.validate("Edge", row)


def test_make_delta_is_content_addressed_and_closed():
    claim = ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": PV, "occurrence_ids": ["occ:" + "a" * 64], "part": "whole"})
    other = ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": PV, "occurrence_ids": ["occ:" + "b" * 64], "part": "whole"})
    make = lambda rows: ids.make_delta("S3", "HUMAN", "v", ("PAPER_VERSION", PV), {"Claim": rows})
    assert make([claim, other]) == make([other, claim, claim]) and make([claim])["delta_id"] != make([other])["delta_id"]
    with pytest.raises(ValueError):
        make([claim, {**claim, "occurrence_kind": "X"}])
    with pytest.raises(jsonschema.ValidationError):
        ids.make_delta("S3", "HUMAN", "v", ("PAPER_VERSION", PV), None, [ids.edge("CONCLUDES", "junction:" + "a" * 64, claim["id"])])


# S3 anchors ------------------------------------------------------------------------------------

def test_anchor_delta_rules(paper):
    s3, occ = paper["s3"], paper["occ"]
    contracts.validate("GraphDelta", s3)
    assert_clean(s3)
    assert s3 == anchors.build_anchor_delta(paper["record"], paper["sources"], parents=[paper["s1"]["delta_id"]])
    assert "PaperVersion" not in s3["nodes"] and s3["parents"] == [paper["s1"]["delta_id"]]  # S1 alone asserts it
    lemma, thm_c, thm_d, defn = (claim_of(s3, occ(key)) for key in ("lem:b", "thm:c", "thm:d", "def:a"))
    assert len(s3["nodes"]["Claim"]) == 4 and all(r["display_text_class"] == "VERBATIM" for r in s3["nodes"]["ClaimReading"])
    assert {r["kind"] for r in s3["nodes"]["ClaimReading"]} == {"definition", "lemma", "theorem"}
    junctions = {(row["conclusion_id"], row["derivation_id"].split(":")[0]): row for row in s3["nodes"]["Junction"]}
    assert set(junctions) == {(lemma, "statement"), (lemma, "proof"), (thm_c, "proof"), (thm_d, "proof")}
    assert [(leg["premise_id"], leg["use_site"]) for leg in junctions[lemma, "statement"]["legs"]] == [(defn, "STATEMENT")]
    assert [leg["premise_id"] for leg in junctions[thm_c, "proof"]["legs"]] == [lemma]  # self-reference dropped
    assert [leg["premise_id"] for leg in junctions[thm_d, "proof"]["legs"]] == [lemma, thm_c]  # PROOF_HEADER_OWNERSHIP
    placeholders = by(s3, "Placeholder")
    proof_legs = [placeholders[leg["premise_id"]] for leg in junctions[lemma, "proof"]["legs"]]
    assert [row["kind"] for row in proof_legs] == ["EXTERNAL_REQUEST", "UNRESOLVED_OCCURRENCE", "EXTERNAL_REQUEST", "EXTERNAL_REQUEST"]
    old, eq, a, b = proof_legs
    bib = {row["citation_key"]: row["id"] for row in s3["nodes"]["BibEntry"]}
    assert old["locator_text"] == "Theorem 3.2" and old["bib_entry_id"] == bib["Old"] and "locator_text" not in a
    assert a["citation_group"] == b["citation_group"] != old["citation_group"]
    assert junctions[lemma, "proof"]["citation_groups"] == sorted({old["citation_group"], a["citation_group"]})
    assert eq["reason"] == "NON_ENVIRONMENT_TARGET" and eq["occurrence_id"] == occ("eq:c")
    assert all(row["citing_derivation_id"] == junctions[lemma, "proof"]["derivation_id"] and row["created_by_claim_id"] == lemma for row in proof_legs)
    edges = {(e["type"], e["start_id"], e["end_id"]) for e in s3["edges"]}
    assert ("MENTIONS", thm_d, bib["Book"]) in edges and ("MENTIONS", thm_c, bib["Old"]) not in edges
    assert {e[0] for e in edges} == {"STATES", "READS", "HAS_ENTRY", "REQUESTS_FROM", "MENTIONS"}
    assert sum(e[0] == "REQUESTS_FROM" for e in edges) == 3 and sum(e[0] == "HAS_ENTRY" for e in edges) == 5
    assert {i["code"] for i in s3["issues"]} >= {"ANCHOR_SELF_REFERENCE", "UNRESOLVED_LABEL"}  # v0.3 resolution codes
    host = anchors.build_restates_delta(paper["record"], paper["sources"], s3)  # a theorem-header \cite: its own method
    assert (host["method"], host["parents"]) == ("HOST_RULE", [s3["delta_id"]]) and host["nodes"] == {}
    assert [(e["type"], e["start_id"], e["end_id"]) for e in host["edges"]] == [("RESTATES_RESULT_OF", thm_c, bib["Old"])]
    nodes = all_node_ids(paper["s1"], s3)
    assert all(e[1] in nodes and e[2] in nodes for e in edges)
    assert all(leg["premise_id"] in nodes for row in s3["nodes"]["Junction"] for leg in row["legs"])
    assert s3["measurements"]["deterministic_yield"] == {
        "theorem_like_environments": 3, "owned_proofs": 3, "proof_owned_anchors": 9, "junction_bearing_conclusions": 3}
    assert s3["nodes"]["BibEntry"][0]["locator"]["artifact"] == "main.tex"


# S6 extraction ---------------------------------------------------------------------------------

def claim(occs, statement, kind="lemma", locators=(), **fields):
    return {"source_occurrence_ids": list(occs), "source_locators": [{"path": "main.tex", "exact_text": t} for t in locators],
            "statement": statement, "kind": kind, "conditions": [], "internal_support_occurrence_ids": [],
            "internal_support_claim_indexes": [], "external_citation_keys": [], "external_mention_citation_keys": [],
            "unresolved_dependencies": [], "confidence": 0.5, **fields}


def test_local_prompt_carries_only_local_context(paper):
    occ = paper["occ"]
    built = extraction.build_local_prompt(paper["record"], paper["sources"], [occ("lem:b")], prose_bytes=40)
    ctx = built["context"]
    assert built["response_schema"] is extraction.RESPONSE_SCHEMA and built["prompt"].startswith("Operation paper.extract_local")
    assert [row["id"] for row in ctx["environments"]] == [occ("lem:b")] and len(ctx["owned_proofs"]) == 1
    assert {row["id"] for row in ctx["referenced_statements"]} == {occ("def:a"), occ("eq:c")}
    assert [row["key"] for row in ctx["bibliography"]] == sorted(["Old", "A", "B"], key=lambda k: next(
        r["id"] for r in paper["record"]["bibliography"] if r["key"] == k))
    assert all("text" not in row for row in ctx["inventory"]) and ctx["preceding_prose"] == []  # the definition ends just before
    prose = lambda n: extraction.build_local_prompt(paper["record"], paper["sources"], [occ("def:a")], prose_bytes=n)["context"]["preceding_prose"]
    start = TEX.index("\\begin{definition}")
    assert [row["text"] for row in prose(40)] == [TEX[start - 40:start]]
    assert prose(4096)[0]["text"].startswith("\\section{Introduction}") and prose(0) == []
    up = paper["up"]  # no sectioning command before the first environment: prose starts at byte 0
    first = extraction.build_local_prompt(up["record"], up["sources"], [up["occ"]("t:1")], prose_bytes=5000)["context"]["preceding_prose"]
    assert [row["text"] for row in first] == [UP_TEX[:UP_TEX.index("\\begin{theorem}")]]
    with pytest.raises(ValueError):
        extraction.build_local_prompt(paper["record"], paper["sources"], ["occ:" + "0" * 64], prose_bytes=0)


def split_response(occ):
    """Batch [lem:b, thm:c]: the lemma split in two parts, the theorem, and one claim located only in the proof."""
    return {"claims": [
        claim([occ("lem:b")], "nice implies tiny", locators=["Every nice object is tiny."], external_citation_keys=["Old"],
              external_mention_citation_keys=["A"]),
        claim([occ("lem:b")], "tiny implies nice", locators=["Every tiny object is nice"], internal_support_occurrence_ids=[occ("def:a")]),
        claim([occ("thm:c")], "tiny objects exist", kind="theorem", internal_support_occurrence_ids=[occ("lem:b"), occ("eq:c")]),
        claim([], "Theorem 3.2 of Old applies", kind="claim", locators=[r"Use \cite[Theorem 3.2]{Old}"], internal_support_claim_indexes=[0])],
        "unread_or_uncertain_scope": []}


def test_response_parts_expansion_and_requests(paper):
    occ, s3, s6 = paper["occ"], paper["s3"], paper["s6"]
    contracts.validate("GraphDelta", s6)
    assert_clean(s6)
    assert s6["stage"] == "S6" and s6["method"] == "MODEL_EXTRACTION" and s6["parents"] == [s3["delta_id"]]
    claims = by(s6, "Claim")
    lemma = claim_of(s3, occ("lem:b"))
    parts = sorted((row for row in claims.values() if row["part"] != "whole"), key=lambda r: r["part"])
    assert [row["part"] for row in parts] == ["part:0", "part:1"] and claims[lemma] == by(s3, "Claim")[lemma]
    assert parts[0]["locator"]["start_byte"] < parts[1]["locator"]["start_byte"]
    edges = {(e["type"], e["start_id"], e["end_id"]) for e in s6["edges"]}
    assert {("PART_OF", row["id"], lemma) for row in parts} <= edges
    junctions = {row["conclusion_id"]: row for row in s6["nodes"]["Junction"]}
    theorem = junctions[claim_of(s3, occ("thm:c"))]
    assert theorem["derivation_id"].startswith("proof:") and [(l["premise_id"], l["flags"], l["use_site"]) for l in theorem["legs"][:2]] == \
        [(parts[0]["id"], ["EXPANDED_TO_PARTS"], "UNKNOWN"), (parts[1]["id"], ["EXPANDED_TO_PARTS"], "UNKNOWN")]
    placeholders = by(s6, "Placeholder")
    assert placeholders[theorem["legs"][2]["premise_id"]]["reason"] == "NON_ENVIRONMENT_TARGET"
    request = placeholders[junctions[parts[0]["id"]]["legs"][0]["premise_id"]]
    assert request["kind"] == "EXTERNAL_REQUEST" and request["citing_derivation_id"] == junctions[parts[0]["id"]]["derivation_id"]
    assert request["locator_text"] == "Theorem 3.2"  # from the proof's \cite of that entry, as S3 records it
    assert ("MENTIONS", parts[0]["id"], next(r["id"] for r in s3["nodes"]["BibEntry"] if r["citation_key"] == "A")) in edges
    assert [l["premise_id"] for l in junctions[parts[1]["id"]]["legs"]] == [claim_of(s3, occ("def:a"))]
    new = next(row for row in claims.values() if row["occurrence_ids"][0] not in {occ("lem:b"), occ("thm:c"), occ("def:a")})
    assert junctions[new["id"]]["derivation_id"] == "unlocated:MODEL_EXTRACTION:0" and new["locator"]["artifact"] == "main.tex"
    readings = s6["nodes"]["ClaimReading"]
    assert len(readings) == 4 and all(r["confidence"]["source"] == "SELF_REPORTED" for r in readings)
    nodes = all_node_ids(paper["s1"], s3, s6)
    assert all(e[1] in nodes and e[2] in nodes for e in edges)
    assert all(leg["premise_id"] in nodes for row in s6["nodes"]["Junction"] for leg in row["legs"])


def test_response_rejections_are_failed_deltas(paper):
    occ = paper["occ"]
    ctx = extraction.build_local_prompt(paper["record"], paper["sources"], [occ("lem:b")], prose_bytes=0)["context"]
    run = lambda claims: extraction.response_to_delta(paper["record"], paper["sources"], ctx,
                                                      {"claims": claims, "unread_or_uncertain_scope": []}, method_version="m1")
    cases = {"AMBIGUOUS_PART": [claim([occ("lem:b")], "one"), claim([occ("lem:b")], "two", locators=["Every tiny object is nice"])],
             "MODEL_CLAIM_OUTSIDE_BATCH": [claim([occ("def:a")], "a definition", kind="definition")],
             "MODEL_OCCURRENCE_REFERENCE_UNKNOWN": [claim([occ("lem:b")], "x", internal_support_occurrence_ids=["occ:" + "0" * 64])],
             "MODEL_CITATION_KEY_UNKNOWN": [claim([occ("lem:b")], "x", external_citation_keys=["Book"])],
             "MODEL_LOCATOR_OUTSIDE_BATCH": [claim([], "x", locators=["Tiny objects exist."])]}
    for code, claims in cases.items():
        failed = run(claims)
        assert failed["nodes"] == {} and failed["edges"] == [] and code in {i["code"] for i in failed["issues"]}, code
    bad = extraction.response_to_delta(paper["record"], paper["sources"], ctx, {"claims": []}, method_version="m1")
    assert [i["code"] for i in bad["issues"]] == ["MODEL_RESPONSE_SCHEMA_INVALID"]


# S7 matching -----------------------------------------------------------------------------------

def upstream():
    rows = []
    for n, (kind, text) in enumerate([("theorem", "Every tiny object is small."),
                                      ("lemma", "Small objects are tiny objects. Small objects exist."),
                                      ("definition", "An object is tiny if it is nice.")]):
        c = ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": UP, "occurrence_ids": [ids.make_id("occ", n)], "part": "whole"})
        rows.append((c, ids.seal("ClaimReading", {"claim_id": c["id"], "method": "DETERMINISTIC_ANCHOR", "method_version": "v", "kind": kind,
                                                  "statement_sha256": digest(text.encode()), "conditions_sha256": anchors.NO_CONDITIONS,
                                                  "display_text": text, "display_text_class": "VERBATIM"})))
    return rows


def test_bind_quote_extends_to_shortest_unique_span():
    assert matching.bind_quote("ab ab c", "ab") == (2, 5, True)
    # "x ab", "ab a", "b ab" and "ab x" are the shortest unique enclosing spans: the earliest start wins (QUOTE_RULE)
    assert matching.bind_quote("x ab ab x", "ab") == (0, 4, True) and matching.bind_quote("abc", "zz") is None
    assert matching.bind_quote("abc", "b") == (1, 2, False)


def test_match_rows_to_delta(paper):
    s3 = paper["s3"]
    bib = {row["id"]: row["citation_key"] for row in s3["nodes"]["BibEntry"]}
    requests = {bib[row["bib_entry_id"]]: row for row in s3["nodes"]["Placeholder"] if row["kind"] == "EXTERNAL_REQUEST"}
    assert set(requests) == {"Old", "A", "B"}
    citing = next(r for r in s3["nodes"]["ClaimReading"] if r["claim_id"] == requests["Old"]["created_by_claim_id"])
    up = upstream()
    (t1, _), (t2, _), (d1, _) = up
    ranked = matching.retrieve_candidates(requests["Old"], citing, up, 3)
    assert [row["claim_id"] for row in ranked][0] == t1["id"] and len(matching.retrieve_candidates(requests["A"], citing, up, 2)) == 2
    built = matching.build_match_prompt(UP, [{"request": requests[k], "citing": citing, "candidates": ranked} for k in ("Old", "A", "B")])
    ctx = built["context"]
    assert built["response_schema"] is matching.RESPONSE_SCHEMA and len(ctx["candidates"]) == 3
    row = lambda key, relation, combination, claims, quotes: {
        "target_request_id": requests[key]["id"], "upstream_occurrence_ids": [], "upstream_claim_ids": claims, "relation": relation,
        "combination": combination, "source_quotes": [{"path": c, "exact_text": t} for c, t in quotes], "extra_conditions": [],
        "proof_issues": [], "reason": "synthetic", "confidence": 0.9}
    rows = [row("Old", "CANDIDATE_SUPPORT", "SINGLE_CLAIM", [t1["id"]], [(t1["id"], "Every tiny object")]),
            row("A", "CANDIDATE_SUPPORT", "JOINT_SUPPORT", [t2["id"], d1["id"]], [(t2["id"], "Small objects"), (d1["id"], "is tiny")]),
            row("B", "MISMATCH", "SINGLE_CLAIM", [], [])]
    s7 = matching.match_rows_to_delta(ctx, {"matches": rows}, method_version="m1")
    contracts.validate("GraphDelta", s7)
    assert_clean(s7)
    junctions = {row["conclusion_id"]: row for row in s7["nodes"]["Junction"]}
    assert set(junctions) == {requests["Old"]["id"], requests["A"]["id"]}
    assert junctions[requests["A"]["id"]]["derivation_id"] == ids.source_derivation(UP, [t2["id"], d1["id"]])
    assert [l["premise_id"] for l in junctions[requests["A"]["id"]]["legs"]] == sorted([t2["id"], d1["id"]])
    codes = [i["code"] for i in s7["issues"]]
    assert sorted(codes) == ["HOST_RULE_QUOTATION_EXTENDED", "MATCH_MISMATCH"]
    host = next(i for i in s7["issues"] if i["code"] == "HOST_RULE_QUOTATION_EXTENDED")["evidence"]
    assert host["claim_id"] == t2["id"] and host["byte_end"] - host["byte_start"] > len("Small objects")
    assert host["rule"] == matching.QUOTE_RULE == "SHORTEST_UNIQUE_ENCLOSING_SPAN_EARLIEST_START"
    single = copy.deepcopy(rows)
    single[0].update(upstream_claim_ids=[t1["id"], t2["id"]])
    single[1]["source_quotes"] = [{"path": t2["id"], "exact_text": "absent"}, {"path": d1["id"], "exact_text": "is tiny"}]
    partial = matching.match_rows_to_delta(ctx, {"matches": single}, method_version="m1")
    assert partial["nodes"] == {} and {"MATCH_COMBINATION_INVALID", "MATCH_QUOTATION_UNBOUND"} <= {i["code"] for i in partial["issues"]}
    unknown = copy.deepcopy(rows)
    unknown[0]["upstream_claim_ids"] = ["claim:" + "0" * 64]
    assert [i["code"] for i in matching.match_rows_to_delta(ctx, {"matches": unknown}, method_version="m1")["issues"]] == ["MATCH_SOURCE_ID_UNKNOWN"]
    assert [i["code"] for i in matching.match_rows_to_delta(ctx, {"matches": rows[:2]}, method_version="m1")["issues"]] == ["MATCH_REQUEST_SCOPE_INVALID"]
    assert [i["code"] for i in matching.match_rows_to_delta(ctx, {"matches": [{}]}, method_version="m1")["issues"]] == ["MODEL_RESPONSE_SCHEMA_INVALID"]
    with pytest.raises(ValueError):
        matching.build_match_prompt("arxiv:2101.00009v1", [{"request": requests["Old"], "citing": citing, "candidates": ranked}])


# S4 works --------------------------------------------------------------------------------------

def test_work_delta_identity_precedence(paper):
    s4 = works.build_work_delta(paper["s3"], paper["record"])
    contracts.validate("GraphDelta", s4)
    assert_clean(s4)
    assert s4["parents"] == [paper["s3"]["delta_id"]]
    key = {row["id"]: row["citation_key"] for row in paper["s3"]["nodes"]["BibEntry"]}
    work = by(s4, "Work")
    resolved = {key[e["start_id"]]: work[e["end_id"]] for e in s4["edges"] if e["type"] == "RESOLVES_TO"}
    assert {k: (w["identity_basis"], w.get("arxiv_base_id") or w.get("doi")) for k, w in resolved.items()} == {
        "Old": ("DOI", "10.1000/abc.1"), "A": ("ARXIV_BASE", "2101.00002"), "B": ("DOI", "10.48550/arxiv.2101.00003"),
        "Book": ("BIB_DIGEST", None)}
    same = [e for e in s4["edges"] if e["type"] == "SAME_WORK"]
    assert len(same) == 1 and same[0]["props"] == {"basis": "HOST_RULE_ARXIV_DOI"} and work[same[0]["end_id"]]["arxiv_base_id"] == "2101.00003"
    assert [i["code"] for i in s4["issues"]] == ["WORK_IDENTITY_INSUFFICIENT"]
    assert {k: w["terminal_kind"] for k, w in resolved.items()} == {"Old": "PREARXIV_DOI_NO_SOURCE", "A": "ARXIV_SOURCE_AVAILABLE",
                                                                     "B": "ARXIV_SOURCE_AVAILABLE", "Book": "FREE_TEXT_UNRESOLVED"}
    [own] = [e for e in s4["edges"] if e["type"] == "VERSION_OF"]
    assert own["start_id"] == PV and work[own["end_id"]]["arxiv_base_id"] == "2999.99999"
    assert all(e["start_id"] in key for e in s4["edges"] if e["type"] == "RESOLVES_TO")
    assert works.normalize_doi("https://doi.org/10.1000/ABC.") == "10.1000/abc" and works.normalize_doi("nonsense") is None
    assert works.normalize_arxiv("arXiv:math.AG/0101001v2") == works.normalize_arxiv("math.ag/0101001") == "math.AG/0101001"
    assert works.normalize_arxiv("2101.00002v3") == "2101.00002" and works.normalize_arxiv("12345") is None


# One manifest ---------------------------------------------------------------------------------

def test_deltas_merge_into_one_manifest_that_passes_the_host_checks(paper, tmp_path):
    """Citing S3 (+ its host rule), S4 and two S6 batches, S7 against the upstream paper, and the upstream's S3/S4:
    every id shared between deltas carries one row, the manifest is closed, and G7 fails exactly where it should."""
    occ, s3, rec, src, up = paper["occ"], paper["s3"], paper["record"], paper["sources"], paper["up"]
    ctx = extraction.build_local_prompt(rec, src, [occ("lem:b")], prose_bytes=0)["context"]
    whole = claim([occ("lem:b")], "nice is tiny", external_citation_keys=["Old"], internal_support_occurrence_ids=[occ("eq:c")])
    s6 = extraction.response_to_delta(rec, src, ctx, {"claims": [whole], "unread_or_uncertain_scope": []}, method_version="m1",
                                      parents=[s3["delta_id"]])
    shared = by(s3, "Placeholder").keys() & by(s6, "Placeholder").keys()  # S6 re-asserts S3's request and eq:c placeholder
    assert len(shared) == 2 and all(by(s3, "Placeholder")[i] == by(s6, "Placeholder")[i] for i in shared)
    key = {row["id"]: row["citation_key"] for row in s3["nodes"]["BibEntry"]}
    requests = {key[r["bib_entry_id"]]: r for r in s3["nodes"]["Placeholder"] if r["kind"] == "EXTERNAL_REQUEST"}
    readings = by(up["s3"], "ClaimReading")
    pairs = [(c, r) for c in up["s3"]["nodes"]["Claim"] for r in readings.values() if r["claim_id"] == c["id"]]
    theorem = next(c for c, r in pairs if r["kind"] == "theorem")
    built = matching.build_match_prompt(UP, [{"request": requests[k], "citing": None,
                                              "candidates": matching.retrieve_candidates(requests[k], None, pairs, 2)} for k in ("Old", "A")])
    rows = [{"target_request_id": requests[k]["id"], "upstream_occurrence_ids": [], "upstream_claim_ids": [theorem["id"]],
             "relation": "CANDIDATE_SUPPORT", "combination": "SINGLE_CLAIM", "extra_conditions": [], "proof_issues": [],
             "source_quotes": [{"path": theorem["id"], "exact_text": "Every tiny object is small."}], "reason": "synthetic",
             "confidence": 0.9} for k in ("Old", "A")]
    s7 = matching.match_rows_to_delta(built["context"], {"matches": rows}, method_version="m1", parents=[s3["delta_id"], up["s3"]["delta_id"]])
    deltas = [paper["s1"], s3, anchors.build_restates_delta(rec, src, s3), works.build_work_delta(s3, rec), paper["s6"], s6, s7,
              up["s1"], up["s3"], works.build_work_delta(up["s3"], up["record"])]
    store = delta.DeltaStore(tmp_path)
    for row in deltas:
        store.put(row)
    view = delta.check_manifest(delta.make_manifest("corpus:" + "0" * 64, [row["delta_id"] for row in deltas]), store)
    assert any(row["identity_basis"] == "BIB_DIGEST" for row in view["nodes"]["Work"].values())  # G6 recomputes these too
    found = {(f["invariant"], f["id"]) for f in invariants.check(view)}
    source = {j["conclusion_id"]: j["id"] for j in s7["nodes"]["Junction"]}
    assert found == {("G7", source[requests["Old"]["id"]])}  # Old resolves to a DOI work, not to the upstream's arXiv work
    same = next(e for e in view["edges"].values() if e["type"] == "SAME_WORK")
    assert invariants.work_components(view, "EXPLICIT_IDS_ONLY")[same["start_id"]] == {same["start_id"], same["end_id"]}
