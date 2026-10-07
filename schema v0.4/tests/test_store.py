"""Deltas, the delta store, manifests, the merged view, G1-G15 and review dispositions, on synthetic rows only."""
import copy
import hashlib
from pathlib import Path

import pytest
from jsonschema import ValidationError

import delta as D
import ids
import invariants
import reviews
from core import canonical, digest

HOST = Path(__file__).resolve().parents[1] / "host"


def h(name):
    return hashlib.sha256(name.encode()).hexdigest()


def i(prefix, name):
    return f"{prefix}:{h(name)}"


def s(name):
    return "sha256:" + h(name)


PVA, PVB = ids.paper_version_id("2101.00001", 1), ids.paper_version_id("2101.00002", 1)
SPAN = {"artifact": "main.tex", "source_sha256": s("src"), "start_byte": 0, "end_byte": 9, "span_sha256": s("x"),
        "line_start": 1, "line_end": 1}
DATE = {"value": "2021-01-04", "kind": "ARXIV_V1", "precision": "DAY", "source": "synthetic"}


def paper(base):
    return ids.seal("PaperVersion", {"arxiv_base_id": base, "version": 1, "primary_category": "quant-ph",
                                     "categories": ["quant-ph"], "redistribution": "RESTRICTED", "date_v1": DATE,
                                     "date_version": {**DATE, "kind": "ARXIV_VERSION"}, "source_sha256": s("src"),
                                     "parser_sha256": s("parser")})


def claim(pv, name):
    return ids.seal("Claim", {"origin": "PAPER_VERSION", "paper_version_id": pv, "occurrence_ids": [i("occ", name)],
                              "part": "whole"})


def leg(premise, use_site="PROOF"):
    return {"premise_id": premise, "role": "UNCLASSIFIED", "use_site": use_site, "flags": []}


def junction(conclusion, derivation, legs, method="DETERMINISTIC_ANCHOR"):
    return ids.seal("Junction", {"conclusion_id": conclusion, "derivation_id": derivation, "reading_method": method,
                                 "method_version": "1", "legs": legs, "grouping_basis": "SYNTHETIC"})


def reading(cid, version="1", statement="st"):
    return ids.seal("ClaimReading", {"claim_id": cid, "method": "DETERMINISTIC_ANCHOR", "method_version": version,
                                     "kind": "lemma", "statement_sha256": s(statement), "conditions_sha256": s("co"),
                                     "display_text_class": "NONE"})


def edge(kind, start, end, **props):
    return ids.edge(kind, start, end, props)


def unresolved(pv, by):
    return ids.seal("Placeholder", {"kind": "UNRESOLVED_OCCURRENCE", "paper_version_id": pv, "created_by_claim_id": by,
                                    "citing_derivation_id": PROOF, "occurrence_id": i("occ", "eq" + pv),
                                    "reason": "NON_ENVIRONMENT_TARGET"})


CA1, CA2, CB1 = claim(PVA, "a1"), claim(PVA, "a2"), claim(PVB, "b1")
A1, A2, B1 = CA1["id"], CA2["id"], CB1["id"]
WORK_B = ids.seal("Work", {"identity_basis": "ARXIV_BASE", "arxiv_base_id": "2101.00002", "work_kind": "ARTICLE",
                           "terminal_kind": "ARXIV_SOURCE_AVAILABLE"})
WORK_D = ids.seal("Work", {"identity_basis": "DOI", "doi": "10.48550/arxiv.2101.00002", "work_kind": "ARTICLE",
                           "terminal_kind": "ARXIV_SOURCE_AVAILABLE"})
WB, WD = WORK_B["id"], WORK_D["id"]
BIB_ROW = ids.seal("BibEntry", {"paper_version_id": PVA, "citation_key": "B", "locator": SPAN,
                                "identifiers": {"arxiv_id": None, "doi": "10.48550/arXiv.2101.00002", "openalex_id": None,
                                                "resolution_basis": "SOURCE_EXPLICIT", "evidence": []}})
BIB = BIB_ROW["id"]
PROOF, SOURCE = ids.proof_derivation([i("occ", "proof")]), ids.source_derivation(PVB, [B1])
REQ_ROW = ids.seal("Placeholder", {"kind": "EXTERNAL_REQUEST", "paper_version_id": PVA, "created_by_claim_id": A1,
                                   "citing_derivation_id": PROOF, "bib_entry_id": BIB, "locator_text": "Theorem 3.2"})
REQ = REQ_ROW["id"]
PRIM = ids.seal("PrimitiveAssertion", {"claim_id": A2, "method": "HUMAN", "basis": "AXIOM"})
J1 = junction(A1, PROOF, [leg(A2), leg(REQ)])
JST = junction(A1, "statement", [leg(A2, "STATEMENT")])
JS = junction(REQ, SOURCE, [leg(B1, "UNKNOWN")], "MODEL_MATCH")
RA1 = reading(A1)
CORPUS = i("corpus", "c")
SAME = edge("SAME_WORK", WD, WB, basis="HOST_RULE_ARXIV_DOI")
RESOLVES = edge("RESOLVES_TO", BIB, WD, method="HOST_RULE", basis="bib doi")
NOMINATION = {"kind": "FoundationNomination", "contract_version": "0.4.0", "nomination_id": i("nomination", "n"),
              "policy_id": i("policy", "p"), "manifest_id": i("manifest", "m"), "rule": "FOUNDATION_V1", "list": "WORKS",
              "subject_kind": "WORK", "subject_id": WB, "count_basis": "SAMPLE_ONLY", "rank_interval": {"lower": 1, "upper": 1},
              "dependent_papers": {"lower": 1, "upper": 1}, "dependent_topics": {"lower": 1, "upper": 1}, "date": DATE, "layer": 1,
              "layer_basis": ["PRIMITIVE"],
              "witness_paths": [[A1, J1["id"], REQ]], "blockers": [], "next_action": "LIBRARY_AUDIT", "match_coverage": 1,
              "bootstrap_top_k_fraction": None, "edge_precision_top_k_survival": None}


def deltas():
    d0 = D.make_delta("S1", "HOST_RULE", "1", ("MANIFEST", i("sampling", "s")),
                      {"PaperVersion": [paper("2101.00001"), paper("2101.00002")]},
                      [edge("INCLUDES", CORPUS, PVA, admission="SAMPLE", round=0, sampling_record_id=i("sampling", "s"))])
    d1 = D.make_delta("S3", "DETERMINISTIC_ANCHOR", "1", ("PAPER_VERSION", PVA),
                      {"Claim": [CA2, CA1], "BibEntry": [BIB_ROW], "ClaimReading": [RA1], "Placeholder": [REQ_ROW],
                       "Junction": [J1, JST]},
                      [edge("STATES", PVA, A1), edge("STATES", PVA, A2), edge("HAS_ENTRY", PVA, BIB),
                       edge("REQUESTS_FROM", REQ, BIB), edge("READS", RA1["id"], A1)], parents=[d0["delta_id"]])
    d2 = D.make_delta("S2", "HOST_RULE", "1", ("PAPER_VERSION", PVB), {"Claim": [CB1], "Work": [WORK_B, WORK_D]},
                      [edge("STATES", PVB, B1), edge("VERSION_OF", PVB, WB), SAME], parents=[d0["delta_id"]])
    d3 = D.make_delta("S4", "HOST_RULE", "1", ("PAPER_VERSION", PVA), {}, [RESOLVES],
                      parents=[d1["delta_id"], d2["delta_id"]])
    d4 = D.make_delta("S7", "MODEL_MATCH", "1", ("REQUEST_POOL", PVB), {"Junction": [JS], "Claim": [CB1]},
                      parents=[d3["delta_id"]])
    d5 = D.make_delta("HUMAN_ENTRY", "HUMAN", "1", ("PAPER_VERSION", PVA), {"PrimitiveAssertion": [PRIM]},
                      parents=[d1["delta_id"]])
    return [d0, d1, d2, d3, d4, d5]


def good_view():
    return D.merge(deltas())


@pytest.fixture
def store(tmp_path):
    st = D.DeltaStore(tmp_path / "deltas")
    for d in deltas():
        st.put(d)
    return st


# --- deltas and the store ---

def test_delta_id_is_the_body_digest_and_ignores_row_order():
    d1 = deltas()[1]
    body = {k: v for k, v in d1.items() if k != "delta_id"}
    assert d1["delta_id"] == "delta:" + digest(canonical(body)).removeprefix("sha256:") == D.address("delta", body)
    again = D.make_delta("S3", "DETERMINISTIC_ANCHOR", "1", ("PAPER_VERSION", PVA),
                         {k: list(reversed(v)) for k, v in d1["nodes"].items()}, list(reversed(d1["edges"])),
                         parents=d1["parents"])
    assert again["delta_id"] == d1["delta_id"]


def test_make_delta_refuses_an_asserted_logical_edge():
    with pytest.raises(ValidationError):
        D.make_delta("S3", "DETERMINISTIC_ANCHOR", "1", ("PAPER_VERSION", PVA), {},
                     [edge("PREMISE_OF", A2, J1["id"], position=0, role="UNCLASSIFIED", use_site="PROOF")])


def test_store_writes_once_at_the_content_address(store):
    d1 = deltas()[0]
    path = store.path(d1["delta_id"])
    hexpart = d1["delta_id"].removeprefix("delta:")
    assert path == store.root / hexpart[:2] / f"{hexpart}.json" and path.read_bytes() == canonical(d1)
    assert store.put(d1) == path and store.get(d1["delta_id"]) == d1
    assert not list(path.parent.glob("*.tmp"))


def test_store_refuses_different_bytes_and_tampering(store):
    d1 = deltas()[1]
    path = store.path(d1["delta_id"])
    path.write_bytes(canonical({**d1, "method_version": "2"}))
    with pytest.raises(ValueError, match="different bytes"):
        store.put(d1)
    with pytest.raises(ValueError):
        store.get(d1["delta_id"])
    with pytest.raises(ValueError, match="not the digest"):
        store.put({**d1, "stage": "S2"})


# --- manifests and the merged view ---

def test_manifest_id_ignores_created_at_and_order(store):
    ids_ = [d["delta_id"] for d in deltas()]
    m = D.make_manifest(CORPUS, ids_, created_at="2026-09-25T00:00:00Z")
    assert D.make_manifest(CORPUS, reversed(ids_), created_at="later")["manifest_id"] == m["manifest_id"]
    view = D.check_manifest(m, store)
    assert view == good_view() and view["deltas"] == sorted(ids_)


def test_merge_records_every_asserting_delta_and_method():
    ds, view = deltas(), good_view()
    b1 = view["nodes"]["Claim"][B1]
    assert b1["asserted_by"] == sorted([ds[2]["delta_id"], ds[4]["delta_id"]])
    assert b1["methods"] == ["HOST_RULE", "MODEL_MATCH"] and D.asserted(b1) == CB1
    assert view["edges"][RESOLVES["id"]]["methods"] == ["HOST_RULE"] and D.asserted(view["edges"][RESOLVES["id"]]) == RESOLVES
    assert all(e["asserted_by"] and e["methods"] for e in view["edges"].values())
    assert set(view["nodes"]) == set(D.LABELS) and len(D.LABELS) == 8


@pytest.mark.parametrize("change,field", [({"content_sha256": s("other")}, "content_sha256"),
                                          ({"part": "part:1"}, "row")])
def test_merge_refuses_one_id_with_two_rows(change, field):
    other = D.make_delta("S6", "MODEL_EXTRACTION", "1", ("CLAIM_BATCH", "b"), {"Claim": [{**CA1, **change}]})
    with pytest.raises(ValueError, match=field):
        D.merge(deltas() + [other])


def test_check_manifest_lists_every_problem(store):
    ids_ = [d["delta_id"] for d in deltas()]
    stray = D.make_delta("S6", "MODEL_EXTRACTION", "1", ("CLAIM_BATCH", "b"), {},
                         [edge("MENTIONS", A1, i("bib", "missing"))])
    store.put(stray)
    m = D.make_manifest(CORPUS, [ids_[1], ids_[3], ids_[4], stray["delta_id"], i("delta", "absent")],
                        excluded=[{"delta_id": ids_[1], "reason": "test"}, {"delta_id": ids_[2], "reason": "a"},
                                  {"delta_id": ids_[2], "reason": "b"}])
    m["manifest_id"] = i("manifest", "forged")
    with pytest.raises(ValueError) as caught:
        D.check_manifest(m, store)
    text = str(caught.value)
    for expected in ("manifest_id is not the digest", f"{ids_[1]}: both included and excluded",
                     f"{ids_[2]}: excluded twice", "not readable from the store", f"parent {ids_[2]} not included",
                     f"{i('bib', 'missing')} is not asserted", f"{WD} is not asserted"):
        assert expected in text


def test_includes_must_start_at_the_manifest_corpus(store):
    with pytest.raises(ValueError, match=CORPUS):
        D.check_manifest(D.make_manifest(i("corpus", "other"), [d["delta_id"] for d in deltas()]), store)


# --- G1-G15 ---

def found(view, keep_g6=False, **kw):
    return {(f["invariant"], f["id"]) for f in invariants.check(view, **kw) if keep_g6 or f["invariant"] != "G6"}


def test_a_consistent_view_passes_every_check_including_g6():
    assert invariants.check(good_view()) == []


def test_g6_recomputes_ids_through_the_identity_module():
    view = copy.deepcopy(good_view())
    view["nodes"]["Claim"][A1]["part"] = "part:1"  # an identity field changed, id and content_sha256 kept
    bib_digest = {"id": i("work", "bd"), "content_sha256": s("bd"), "identity_basis": "BIB_DIGEST", "bib_digest": s("x"),
                  "title": "T", "work_kind": "BOOK", "terminal_kind": "ARXIV_SOURCE_AVAILABLE"}
    view["nodes"]["Work"][bib_digest["id"]] = {**bib_digest, "asserted_by": [view["deltas"][0]], "methods": ["HOST_RULE"]}
    got = {(f["invariant"], f["id"], f["detail"].split(":")[0]) for f in invariants.check(view)}
    assert got == {("G6", A1, "identity fields give claim"), ("G6", bib_digest["id"], "identity fields give work")}


def add_edge(view, row, by=None):
    view["edges"][row["id"]] = {**row, "asserted_by": [view["deltas"][0]] if by is None else by, "methods": ["HOST_RULE"]}


def add_node(view, label, row):
    view["nodes"][label][row["id"]] = {**row, "asserted_by": [view["deltas"][0]], "methods": ["HOST_RULE"]}


def legs_of(view, row):
    return view["nodes"]["Junction"][row["id"]]["legs"]


def drop_edge(view, kind, start, end):
    del view["edges"][edge(kind, start, end)["id"]]


UNRES_B = unresolved(PVB, B1)
JU = junction(unresolved(PVA, A1)["id"], SOURCE, [leg(B1, "UNKNOWN")], "MODEL_MATCH")
LOCATOR = ids.seal("Claim", {"origin": "WORK_LOCATOR", "work_id": WB, "occurrence_ids": [], "part": "whole",
                             "work_locator_text": "Thm 1"})
RA1B, RX, RY = reading(A1, version="2"), reading(A2, statement="x"), reading(A2, statement="y")
MUTATIONS = {  # name: (mutation, the exact (invariant, id) findings apart from G6)
    "G2 premise": (lambda v: legs_of(v, J1).append(leg(i("claim", "missing"))), {("G2", J1["id"]), ("G12", J1["id"])}),
    "G2 conclusion": (lambda v: (add_node(v, "Placeholder", unresolved(PVA, A1)), add_node(v, "Junction", JU)),
                      {("G2", JU["id"]), ("G7", JU["id"])}),
    "G3": (lambda v: add_edge(v, edge("MENTIONS", A1, A2)), {("G3", edge("MENTIONS", A1, A2)["id"])}),
    "G4": (lambda v: legs_of(v, J1).append(leg(A1)), {("G4", J1["id"])}),
    "G5": (lambda v: v["nodes"]["ClaimReading"][RA1["id"]].update(kind="bogus"), {("G5", RA1["id"])}),
    "G5 carries G1": (lambda v: legs_of(v, J1).clear(), {("G5", J1["id"])}),
    "G5 carries G11": (lambda v: v["nodes"]["Junction"][J1["id"]].update(disposition=reviews.SIGNED), {("G5", J1["id"])}),
    "G5 carries G13 per junction": (lambda v: legs_of(v, J1).append(leg(A2, "STATEMENT")), {("G5", J1["id"])}),
    "G7 version": (lambda v: drop_edge(v, "VERSION_OF", PVB, WB), {("G7", JS["id"])}),
    "G7 premise": (lambda v: legs_of(v, JS).append(leg(A2, "UNKNOWN")), {("G7", JS["id"])}),
    "G8 source": (lambda v: drop_edge(v, "REQUESTS_FROM", REQ, BIB), {("G8", REQ)}),
    "G8 citing junction": (lambda v: v["nodes"]["Junction"].pop(J1["id"]), {("G8", REQ)}),
    "G9 foreign": (lambda v: v["nodes"]["Claim"][A2].update(asserted_by=[i("delta", "foreign")]), {("G9", A2)}),
    "G9 empty": (lambda v: v["edges"][SAME["id"]].update(asserted_by=[]), {("G9", SAME["id"])}),
    "G10": (lambda v: drop_edge(v, "STATES", PVA, A2), {("G10", A2)}),
    "G10 work locator": (lambda v: add_node(v, "Claim", LOCATOR), {("G10", LOCATOR["id"])}),
    "G12 claim": (lambda v: legs_of(v, J1).append(leg(B1)), {("G12", J1["id"])}),
    "G12 placeholder": (lambda v: (add_node(v, "Placeholder", UNRES_B), legs_of(v, J1).append(leg(UNRES_B["id"]))),
                        {("G12", J1["id"])}),
    "G13": (lambda v: add_node(v, "Junction", junction(A1, "statement", [leg(A2, "STATEMENT"), leg(REQ, "STATEMENT")])),
            {("G13", A1)}),  # a second statement junction of the same (conclusion, reading_method, method_version)
    "G14 superseded": (lambda v: (add_node(v, "ClaimReading", RA1B), add_edge(v, edge("SUPERSEDES", RA1B["id"], RA1["id"]))),
                       {("G14", J1["id"]), ("G14", JST["id"])}),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_each_invariant_catches_its_violation(name):
    view = copy.deepcopy(good_view())
    mutate, expected = MUTATIONS[name]
    mutate(view)
    assert found(view) == expected


def test_g13_allows_one_statement_junction_per_reading():
    view = copy.deepcopy(good_view())
    add_node(view, "Junction", junction(A1, "statement", [leg(A2, "STATEMENT")], "MODEL_EXTRACTION"))
    add_node(view, "Junction", ids.seal("Junction", {"conclusion_id": A1, "derivation_id": "statement", "legs": [leg(REQ, "STATEMENT")],
                                                     "reading_method": "MODEL_EXTRACTION", "method_version": "2", "grouping_basis": "S"}))
    assert invariants.check(view) == []


def test_g14_cycle_and_two_successors():
    view = copy.deepcopy(good_view())
    for r in (RX, RY):
        add_node(view, "ClaimReading", r)
    for start, end in ((RX, RY), (RY, RX), (RA1, RY)):
        add_edge(view, edge("SUPERSEDES", start["id"], end["id"]))
    got = [(f["id"], f["detail"]) for f in invariants.check(view) if f["invariant"] != "G6"]
    assert (RY["id"], "2 successors") in got and len(got) == 2
    assert got[1][1].startswith("SUPERSEDES cycle through") and {RX["id"], RY["id"]} <= set(got[1][1][25:].split(", "))


def test_schema_invalid_rows_are_reported_not_raised():
    view = copy.deepcopy(good_view())
    del view["nodes"]["Placeholder"][REQ]["bib_entry_id"]
    assert found(view) == {("G5", REQ)}


@pytest.mark.parametrize("target,prop", [(SAME, "basis"), (RESOLVES, "method")])
def test_g7_admits_work_identity_by_the_loading_policy(target, prop):
    view = copy.deepcopy(good_view())
    view["edges"][target["id"]]["props"][prop] = "MODEL_MATCH"
    blocked = {("G7", JS["id"])}
    assert found(view) == blocked == found(view, work_identity="PLUS_REVIEWED_SAME_WORK")
    assert found(view, work_identity="PLUS_REVIEWED_SAME_WORK", accepted=[("WORK_IDENTITY", target["id"])]) == set()
    assert found(view, work_identity="PLUS_CANDIDATE_SAME_WORK") == set()


def test_work_components_pool_admitted_same_work_only():
    view = good_view()
    assert invariants.work_components(view, "EXPLICIT_IDS_ONLY")[WD] == {WD, WB}
    view["edges"][SAME["id"]]["props"]["basis"] = "HUMAN"  # a HUMAN basis still needs its review (I-9)
    assert invariants.work_components(view, "EXPLICIT_IDS_ONLY")[WD] == {WD}
    assert invariants.work_components(view, "PLUS_REVIEWED_SAME_WORK", [("WORK_IDENTITY", SAME["id"])])[WD] == {WD, WB}


# --- reviews and dispositions ---

def review(kind, subject_id, content, decision="ACCEPT"):
    return {"kind": "HumanReview", "subject_kind": kind, "subject_id": subject_id,
            "subject_sha256": digest(canonical(content)), "decision": decision, "reviewer": "r", "basis": "read it",
            "reviewed_at": "2026-09-25"}


def test_template_lists_the_v04_subjects_with_their_digests():
    rows = reviews.template(good_view(), [NOMINATION])
    kinds = [r["subject_kind"] for r in rows]
    assert {k: kinds.count(k) for k in set(kinds)} == {"JUNCTION": 3, "LEG": 4, "WORK_IDENTITY": 2,
                                                       "PRIMITIVE_ASSERTION": 1, "FOUNDATION_NOMINATION": 1}
    assert set(reviews.KINDS) == set(kinds)
    assert all(r["decision"] is None and r["subject_sha256"] == digest(canonical(r["content"])) for r in rows)
    assert all("asserted_by" not in canonical(r["content"]).decode() for r in rows)


def test_a_leg_is_named_by_its_premise_of_id():
    premise_of = [e["id"] for e in ids.logical_edges(J1) if e["type"] == "PREMISE_OF"]
    assert [reviews.leg_id(J1["id"], k) for k in (0, 1)] == premise_of
    assert set(premise_of) <= {r["subject_id"] for r in reviews.template(good_view()) if r["subject_kind"] == "LEG"}


def test_only_an_unwithdrawn_accept_signs():
    view = good_view()
    subjects = reviews.subjects(view, [NOMINATION])
    signed = [("JUNCTION", J1["id"]), ("LEG", reviews.leg_id(J1["id"], 1)),
              ("FOUNDATION_NOMINATION", NOMINATION["nomination_id"])]
    rows = [review(*key, subjects[key]) for key in signed]
    rows += [review("JUNCTION", JS["id"], subjects["JUNCTION", JS["id"]]),
             review("JUNCTION", JS["id"], subjects["JUNCTION", JS["id"]], "REJECT"),  # REJECT withdraws
             review("PRIMITIVE_ASSERTION", PRIM["id"], subjects["PRIMITIVE_ASSERTION", PRIM["id"]], "REJECT")]
    rows += [dict(r, decision=None) for r in reviews.template(view)]  # unfilled rows are ignored
    out = reviews.derive_dispositions(view, rows, [NOMINATION])
    flat = {(k, i): d for k, table in out.items() for i, d in table.items()}
    assert {key for key, d in flat.items() if d == reviews.SIGNED} == set(signed)
    assert set(flat) == set(subjects) and set(flat.values()) == {reviews.SIGNED, reviews.UNREVIEWED}
    assert reviews.load(view, rows, [NOMINATION]) == {"accepted": sorted(signed), "rejections": []}


def test_changed_unknown_or_invalid_reviews_are_rejected_never_applied():
    view = good_view()
    content = reviews.subjects(view)["JUNCTION", J1["id"]]
    rows = [review("JUNCTION", J1["id"], {**content, "grouping_basis": "EDITED"}),
            review("JUNCTION", i("junction", "nope"), content),
            review("SUPPORT_GROUP", J1["id"], content),
            dict(review("JUNCTION", J1["id"], content), decision="MAYBE")]
    loaded = reviews.load(view, rows)
    assert [r["reason"].split(":")[0] for r in loaded["rejections"]] == [
        "SUBJECT_CHANGED_SINCE_REVIEW", "UNKNOWN_SUBJECT", "UNKNOWN_SUBJECT", "SCHEMA_INVALID"]
    assert loaded["accepted"] == [] and set(reviews.derive_dispositions(view, rows)["JUNCTION"].values()) == {reviews.UNREVIEWED}


def test_a_review_of_a_changed_row_stops_signing():
    view = good_view()
    key = ("LEG", reviews.leg_id(J1["id"], 0))
    accept = review(*key, reviews.subjects(view)[key])
    assert reviews.derive_dispositions(view, [accept])["LEG"][key[1]] == reviews.SIGNED
    legs_of(view, J1)[0]["role"] = "PROOF_DEPENDENCY"
    assert reviews.derive_dispositions(view, [accept])["LEG"][key[1]] == reviews.UNREVIEWED


def test_no_module_writes_a_verified_state():
    for name in ("delta.py", "invariants.py", "reviews.py"):
        assert "VERIFIED" not in (HOST / name).read_text()
