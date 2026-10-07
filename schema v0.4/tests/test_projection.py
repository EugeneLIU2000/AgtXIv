"""Static tests of the Neo4j projection on a synthetic delta-set view; a fake client stands in for Neo4j."""
import csv
import hashlib
import io
import json
import re
import pytest

import contracts
import ids
import projection as P
import reviews
from core import canonical, digest


def hx(*parts):
    return hashlib.sha256(repr(parts).encode()).hexdigest()


def sha(*parts):
    return "sha256:" + hx(*parts)


PV, PV2 = "arxiv:2101.00001v1", "arxiv:2002.00002v1"
CORPUS, SAMPLING = "corpus:" + hx("corpus"), "sampling:" + hx("sampling")
D1, D2 = "delta:" + hx("d1"), "delta:" + hx("d2")
A, C, U = ("claim:" + hx(x) for x in "ACU")
W, B, R = "work:" + hx("W"), "bib:" + hx("B"), "reading:" + hx("R")
ER, UO = "placeholder:" + hx("ER"), "placeholder:" + hx("UO")
J1, J2 = "junction:" + hx("J1"), "junction:" + hx("J2")
PRIM = "primitive:" + hx("P")
PROOF_D, SOURCE_D = "proof:" + sha("span"), f"source:{PV2}:" + sha("match")
SPAN = {"artifact": "main.tex", "source_sha256": sha("src"), "start_byte": 0, "end_byte": 9,
        "span_sha256": sha("span"), "line_start": 1, "line_end": 2}
DATE = {"value": "2021-01-04", "kind": "ARXIV_V1", "precision": "DAY", "source": "oai-snapshot"}


def version(pid, base, redistribution):
    return {"id": pid, "content_sha256": sha(pid), "arxiv_base_id": base, "version": 1,
            "primary_category": "quant-ph", "categories": ["quant-ph"], "redistribution": redistribution,
            "date_v1": DATE, "date_version": DATE, "source_sha256": sha("s", pid), "parser_sha256": sha("parser")}


def claim(cid, pv):
    return {"id": cid, "content_sha256": sha(cid), "origin": "PAPER_VERSION", "paper_version_id": pv,
            "occurrence_ids": ["occ:" + hx("occ", cid)], "part": "whole", "locator": SPAN,
            "occurrence_kind": "theorem"}


def leg(premise, role="PROOF_DEPENDENCY"):
    return {"premise_id": premise, "role": role, "use_site": "PROOF", "flags": []}


NODES = {
    "PaperVersion": [version(PV, "2101.00001", "RESTRICTED"), version(PV2, "2002.00002", "OPEN")],
    "Work": [{"id": W, "content_sha256": sha(W), "identity_basis": "ARXIV_BASE", "arxiv_base_id": "2002.00002",
              "work_kind": "ARTICLE", "terminal_kind": "ARXIV_SOURCE_AVAILABLE"}],
    "BibEntry": [{"id": B, "content_sha256": sha(B), "paper_version_id": PV, "citation_key": "smith20",
                  "locator": SPAN, "identifiers": {"arxiv_id": "2002.00002", "doi": None, "openalex_id": None,
                                                   "resolution_basis": "SOURCE_EXPLICIT", "evidence": ["eprint"]}}],
    "Claim": [claim(A, PV), claim(C, PV), claim(U, PV2)],
    "ClaimReading": [{"id": R, "content_sha256": sha(R), "claim_id": A, "method": "MODEL_EXTRACTION",
                      "method_version": "m1", "kind": "theorem", "statement_sha256": sha("st"),
                      "conditions_sha256": sha("co"), "display_text": "Every stabilizer state ...",
                      "display_text_class": "VERBATIM"}],
    "Junction": [
        {"id": J1, "content_sha256": sha(J1), "conclusion_id": A, "derivation_id": PROOF_D,
         "reading_method": "DETERMINISTIC_ANCHOR", "method_version": "s3-1",
         "legs": [leg(C), leg(ER, "UNCLASSIFIED")], "grouping_basis": "PROOF_SPAN", "citation_groups": ["anchor-7"]},
        {"id": J2, "content_sha256": sha(J2), "conclusion_id": ER, "derivation_id": SOURCE_D,
         "reading_method": "MODEL_MATCH", "method_version": "m1", "legs": [leg(U)], "grouping_basis": "MATCH_ROW"}],
    "Placeholder": [
        {"id": ER, "content_sha256": sha(ER), "kind": "EXTERNAL_REQUEST", "paper_version_id": PV,
         "created_by_claim_id": A, "citing_derivation_id": PROOF_D, "bib_entry_id": B,
         "citation_group": "anchor-7", "locator_text": "Theorem 3.2"},
        {"id": UO, "content_sha256": sha(UO), "kind": "UNRESOLVED_OCCURRENCE", "paper_version_id": PV,
         "created_by_claim_id": C, "citing_derivation_id": "statement", "occurrence_id": "occ:" + hx("eq"),
         "reason": "NON_ENVIRONMENT_TARGET"}],
    "PrimitiveAssertion": [{"id": PRIM, "content_sha256": sha("P"), "claim_id": C,
                            "method": "HUMAN", "basis": "AXIOM"}],
}


def edge(etype, start, end, **props):
    rid = "rel:" + hx(etype, start, end)
    return {"id": rid, "content_sha256": sha(rid), "type": etype, "start_id": start, "end_id": end, "props": props}


EDGES = [edge("STATES", PV, A), edge("STATES", PV, C), edge("STATES", PV2, U), edge("HAS_ENTRY", PV, B),
         edge("REQUESTS_FROM", ER, B), edge("RESOLVES_TO", B, W, method="HOST_RULE", basis="EPRINT_FIELD"),
         edge("VERSION_OF", PV2, W), edge("READS", R, A),
         edge("INCLUDES", CORPUS, PV, admission="SAMPLE", round=0, sampling_record_id=SAMPLING)]
MANIFEST = {"kind": "DeltaSetManifest", "manifest_id": "manifest:" + hx("m"), "corpus_id": CORPUS,
            "deltas": [D1, D2], "excluded": [], "created_at": "2026-09-25T00:00:00+00:00"}
REVIEW_SET = sha("reviews")


SIGNED = "SOURCE_FROZEN_HUMAN_SIGNED"
DISPOSITIONS = {"JUNCTION": {J1: "UNREVIEWED"}, "LEG": {reviews.leg_id(J1, 1): SIGNED},
                "PRIMITIVE_ASSERTION": {PRIM: SIGNED}, "FOUNDATION_NOMINATION": {"nomination:" + hx("n"): SIGNED}}


def view():
    """The delta.merge shape: every row carries asserted_by and methods."""
    tag = {"asserted_by": [D1], "methods": ["DETERMINISTIC_ANCHOR"]}
    return {"deltas": [D1, D2], "nodes": {label: {r["id"]: {**r, **tag} for r in rs} for label, rs in NODES.items()},
            "edges": {e["id"]: {**e, "asserted_by": [D2], "methods": ["HOST_RULE"]} for e in EDGES}}


def rows(dispositions=DISPOSITIONS):
    return P.project(view(), MANIFEST, dispositions)


class Fake:
    """Records every request; answers like an empty-then-filled Neo4j unless told to misbehave."""

    def __init__(self, stale=(), short=None, audit=None, existing=(), boom=None):
        self.calls, self.stale, self.short, self.audit, self.existing = [], set(stale), short, audit or {}, existing
        self.boom, self.audit_names = boom, {q: name for name, q in P.AUDITS}

    def run(self, statement, parameters, tx_metadata):
        self.calls.append((statement, parameters, tx_metadata))
        if statement == self.boom:
            raise RuntimeError("Query API HTTP 400: synthetic")
        if statement == P.EXISTING:
            return [{"id": i, "state": "READY"} for i in self.existing]
        if statement in self.audit_names:
            return [{"invariant": self.audit_names[statement], "id": i}
                    for i in self.audit.get(self.audit_names[statement], ())]
        if statement.endswith("RETURN row.id AS id"):
            return [{"id": r["id"]} for r in parameters["rows"] if r["id"] in self.stale]
        if statement.endswith("AS n"):
            return [{"n": len(parameters["rows"]) - (statement == self.short)}]
        return []

    def kinds(self):
        table = {P.EXISTING: "existing", P.SET_MANIFEST: "manifest", P.NODE_PREFLIGHT: "preflight",
                 **{q: "schema" for q in P.SCHEMA}, **{q: "preflight" for q in P.REL_PREFLIGHT.values()},
                 **{q: "nodes" for q in P.NODE_MERGE.values()}, **{q: "rels" for q in P.REL_MERGE.values()},
                 **{q: "audit" for q in self.audit_names}}
        out = []
        for statement, parameters, _ in self.calls:
            kind = table[statement]
            if kind == "manifest":
                kind = parameters["props"]["state"]
            if not out or out[-1] != kind:
                out.append(kind)
        return out


def strip(entry):
    return {k: v for k, v in entry.items() if k not in ("asserted_by", "methods")}


def test_fixture_and_derived_edges_are_contract_rows():
    defs = {"PaperVersion": "PaperVersionNode", "Work": "WorkNode", "BibEntry": "BibEntryNode", "Claim": "ClaimNode",
            "ClaimReading": "ClaimReadingNode", "Junction": "JunctionNode", "Placeholder": "PlaceholderNode",
            "PrimitiveAssertion": "PrimitiveAssertionNode"}
    for label, rs in NODES.items():
        for r in rs:
            contracts.validate(defs[label], r)
    for e in EDGES + [e for j in NODES["Junction"] for e in P.junction_edges(j)]:
        contracts.validate("Edge", e)
    contracts.validate("DeltaSetManifest", MANIFEST)
    first = P.junction_edges(NODES["Junction"][0])
    assert [e["type"] for e in first] == ["PREMISE_OF", "PREMISE_OF", "CONCLUDES"]
    for e in first:  # G6 and G15: the id and content digest are the identity package's
        assert e["id"] == ids.make_id("rel", ids.identity("Edge", e))
        assert e["content_sha256"] == digest(canonical(ids.identity("Edge", e)))
    assert (first[1]["start_id"], first[1]["end_id"], first[1]["props"]["position"]) == (ER, J1, 1)
    assert first[1]["props"]["flags"] == [] and first[2]["props"] == {}


def test_project_labels_properties_and_derived_rows():
    out = rows()
    assert set(out["nodes"]) == set(P.GROUPS)
    assert [r["id"] for r in out["nodes"]["ExternalRequest"]] == [ER]
    assert [r["id"] for r in out["nodes"]["UnresolvedOccurrence"]] == [UO]
    for group, rs in out["nodes"].items():
        for r in rs:
            assert set(r) == {"id", "content_sha256", "props"} and "id" not in r["props"]
            assert r["props"]["content_sha256"] == r["content_sha256"] and r["props"]["asserted_by"]
            for v in r["props"].values():
                assert isinstance(v, (str, int, float, bool)) or (
                    isinstance(v, list) and len({type(x) for x in v}) <= 1
                    and all(isinstance(x, (str, int, float, bool)) for x in v))
    claims = {r["id"]: r["props"] for r in out["nodes"]["Claim"]}
    assert "disposition" not in claims[A]
    assert out["nodes"]["PrimitiveAssertion"][0]["props"]["disposition"] == SIGNED
    assert claims[A]["locator_start_byte"] == 0 and "locator" not in claims[A]
    bib = out["nodes"]["BibEntry"][0]["props"]
    assert bib["identifiers_arxiv_id"] == "2002.00002" and "identifiers_doi" not in bib
    assert out["nodes"]["PaperVersion"][0]["props"]["date_v1_kind"] == "ARXIV_V1"
    junctions = {r["id"]: r["props"] for r in out["nodes"]["Junction"]}
    assert junctions[J1]["leg_count"] == 2 and "legs" not in junctions[J1]
    assert "display_text" not in out["nodes"]["ClaimReading"][0]["props"]  # RESTRICTED paper, VERBATIM (I-13)
    corpus = out["nodes"]["Corpus"][0]
    assert corpus["id"] == CORPUS and corpus["props"]["asserted_by"] == [D2]
    legs = {(r["start"], r["end"]): r for r in out["rels"]["PREMISE_OF"]}
    assert set(legs) == {(C, J1), (ER, J1), (U, J2)}
    expected = {"position": 1, "role": "UNCLASSIFIED", "use_site": "PROOF", "asserted_by": [D1],
                "methods": ["DETERMINISTIC_ANCHOR"], "disposition": SIGNED}
    assert {k: legs[(ER, J1)]["props"][k] for k in expected} == expected
    assert "flags" not in legs[(ER, J1)]["props"]  # an empty list is dropped, as the CSV import must
    assert out["rels"]["STATES"][0]["props"]["methods"] == ["HOST_RULE"]
    assert {(r["start"], r["end"]) for r in out["rels"]["CONCLUDES"]} == {(J1, A), (J2, ER)}
    includes = out["rels"]["INCLUDES"][0]["props"]
    assert includes["admission"] == "SAMPLE" and includes["asserted_by"] == [D2]
    assert "disposition" not in legs[(C, J1)]["props"]
    assert junctions[J1]["disposition"] == "UNREVIEWED" and "disposition" not in junctions[J2]
    assert out["params"] == {"deltas": [D1, D2], "enums": P.ENUMS, "dispositions": {
        J1: "UNREVIEWED", legs[(ER, J1)]["id"]: SIGNED, PRIM: SIGNED}}
    assert out["delta_set_digest"] == "sha256:" + hx("m") == P.delta_set_digest(dict(MANIFEST, created_at="2027"))


def test_open_paper_keeps_verbatim_display_text():
    v = view()
    v["nodes"]["PaperVersion"][PV]["redistribution"] = "OPEN"
    out = P.project(v, MANIFEST, {})
    assert out["nodes"]["ClaimReading"][0]["props"]["display_text"].startswith("Every")


def add(v, e):
    v["edges"][e["id"]] = {**e, "asserted_by": [D1], "methods": ["HOST_RULE"]}


@pytest.mark.parametrize("damage, error, match", [
    ("disposition", ValueError, r"\['disposition'\] may be set only by the host"),
    ("edge_props", ValueError, r"\['asserted_by', 'disposition', 'id'\] may be set only by the host"),
    ("logical_edge", ValueError, "derived from junctions only"),
    ("other_corpus", ValueError, "INCLUDES from a corpus other"),
    ("deltas", ValueError, "exactly the manifest's deltas"),
    ("label", KeyError, "no projection template for node label Review")])
def test_project_refuses(damage, error, match):
    v = view()
    if damage == "disposition":
        v["nodes"]["Claim"][A]["disposition"] = SIGNED
    elif damage == "edge_props":  # an open Edge.props must not overwrite host fields or the MERGE key
        add(v, edge("MENTIONS", A, B, disposition=SIGNED, asserted_by=[D1], id="rel:forged"))
    elif damage == "logical_edge":
        add(v, edge("PREMISE_OF", C, J1, position=0, role="UNCLASSIFIED", use_site="PROOF"))
    elif damage == "other_corpus":
        add(v, edge("INCLUDES", "corpus:" + hx("other"), PV2, admission="SAMPLE", round=0, sampling_record_id=SAMPLING))
    elif damage == "deltas":
        v["deltas"] = [D1]
    else:
        v["nodes"]["Review"] = {"x": {"id": "x"}}
    with pytest.raises(error, match=match):
        P.project(v, MANIFEST, {})


def test_review_set_dispositions_cover_every_reviewed_element():
    derived = reviews.derive_dispositions(view(), [])
    out = P.project(view(), MANIFEST, derived)
    flat = out["params"]["dispositions"]
    assert set(flat.values()) == {"UNREVIEWED"}
    assert {r["id"] for r in out["rels"]["PREMISE_OF"]} | {J1, J2, PRIM, out["rels"]["RESOLVES_TO"][0]["id"]} == set(flat)
    marked = {r["id"] for part in ("nodes", "rels") for rs in out[part].values() for r in rs if "disposition" in r["props"]}
    assert marked == set(flat)


def test_flat_encodes_nested_values():
    assert P._flat({"a": {"b": 1, "c": {"d": None, "e": "x"}}, "l": [1, 2], "m": [{"k": 1}], "n": [1, "a"],
                    "z": None, "e": []}) == {"a_b": 1, "a_c_e": "x", "l": [1, 2], "m_json": '[{"k":1}]',
                                             "n_json": '[1,"a"]'}
    with pytest.raises(ValueError):
        P._flat({"a_b": 1, "a": {"b": 2}})


def g5_enum_rows(out):
    """What the two $enums branches of the G5 audit return, evaluated in Python on projected rows."""
    def bad(f, v):
        if v is None:
            return f["required"]
        return any(x not in f["values"] for x in v) if f["list"] else v not in f["values"]
    return sorted({r["id"] for g, rs in out["nodes"].items() for r in rs for f in P.ENUMS["nodes"]
                   if f["label"] in {*P.GROUPS[g].split(":"), "Entity"} and bad(f, r["props"].get(f["key"]))} |
                  {r["id"] for t, rs in out["rels"].items() for r in rs for f in P.ENUMS["rels"]
                   if f["type"] == t and bad(f, r["props"].get(f["key"]))})


def test_g5_enum_table_comes_from_the_contracts_and_matches_projected_keys():
    nodes = {(f["label"], f["key"]): f for f in P.ENUMS["nodes"]}
    rels = {(f["type"], f["key"]): f for f in P.ENUMS["rels"]}
    assert {("ClaimReading", "kind"), ("ClaimReading", "display_text_class"), ("ClaimReading", "confidence_source"),
            ("Work", "work_kind"), ("Work", "terminal_kind"), ("PaperVersion", "redistribution"),
            ("PaperVersion", "date_v1_kind"), ("Placeholder", "reason"), ("PrimitiveAssertion", "basis"),
            ("Junction", "reading_method"), ("Claim", "origin"), ("Entity", "methods")} <= set(nodes)
    assert {("PREMISE_OF", "role"), ("PREMISE_OF", "flags"), ("SAME_WORK", "basis"), ("INCLUDES", "admission"),
            ("RESOLVES_TO", "method"), ("STATES", "methods")} <= set(rels)
    assert not any(k[1].startswith("legs") for k in nodes) and ("PREMISE_OF", "premise_id") not in rels
    basis = nodes["BibEntry", "identifiers_resolution_basis"]  # a union of a v0.3 enum and a v0.4 enum
    assert {"SOURCE_EXPLICIT", "OPENALEX_CANDIDATE"} <= set(basis["values"]) and basis["required"]
    assert rels["PREMISE_OF", "flags"]["list"] and not rels["PREMISE_OF", "flags"]["required"]
    assert nodes["Claim", "origin"]["required"] and not nodes["Placeholder", "reason"]["required"]
    assert not nodes["ClaimReading", "confidence_source"]["required"]  # its parent is optional
    assert g5_enum_rows(rows()) == []
    v = view()
    v["nodes"]["ClaimReading"][R]["kind"] = "Theorem"
    del v["nodes"]["Work"][W]["work_kind"]
    v["edges"][EDGES[5]["id"]]["props"]["method"] = "GUESS"
    assert g5_enum_rows(P.project(v, MANIFEST, {})) == sorted([R, W, EDGES[5]["id"]])


def test_templates_are_fixed_per_label_and_type():
    assert set(P.REL_MERGE) == set(P.REL_PREFLIGHT) == set(P.REL_TYPES) == set(
        contracts.SCHEMAS[contracts.CORPUS_ID]["$defs"]["EdgeType"]["enum"])
    for group, template in P.NODE_MERGE.items():
        assert f"MERGE (n:{P.GROUPS[group]}:Entity {{id: row.id}})" in template
    for t, template in P.REL_MERGE.items():
        assert f"-[r:{t} {{id: row.id}}]->" in template
    for template in [*P.NODE_MERGE.values(), *P.REL_MERGE.values(), *P.REL_PREFLIGHT.values(), P.NODE_PREFLIGHT]:
        assert set(re.findall(r"\$(\w+)", template)) == {"rows"} and "{row." not in template


def test_every_sent_row_carries_the_fields_its_template_reads():
    fake = Fake()
    P.load(fake, rows(), P.projection_manifest(MANIFEST, REVIEW_SET))
    checked = 0
    for statement, parameters, meta in fake.calls:
        assert meta == {"id": P.projection_manifest(MANIFEST, REVIEW_SET)["id"],
                        "delta_set_digest": "sha256:" + hx("m"), "review_set_digest": REVIEW_SET}
        assert set(re.findall(r"\$(\w+)", statement)) == set(parameters)  # audits get only what they name
        fields = set(re.findall(r"\brow\.(\w+)", statement))
        for row in parameters.get("rows", ()):
            assert fields <= set(row)
            checked += 1
    assert checked > 2 * sum(len(rs) for rs in rows()["rels"].values())


def test_schema_cypher_covers_labels_types_and_indexes():
    assert all("IF NOT EXISTS" in s for s in P.SCHEMA)
    constraints = {m for s in P.SCHEMA for m in re.findall(r"FOR \(n:(\w+)\) REQUIRE n\.id IS UNIQUE", s)}
    assert constraints == {"Entity", "Corpus", "PaperVersion", "Work", "BibEntry", "Claim", "ClaimReading",
                           "Junction", "Placeholder", "PrimitiveAssertion", "ProjectionManifest"}  # no Review, AnalysisRun, Nomination
    assert {g.split(":")[0] for g in P.GROUPS.values()} <= constraints
    rel = {m for s in P.SCHEMA for m in re.findall(r"FOR \(\)-\[r:(\w+)\]-\(\) REQUIRE r\.id IS UNIQUE", s)}
    assert rel == set(P.REL_TYPES) and not {"REVIEWS", "IN_RUN", "NOMINATES"} & rel
    indexes = {m for s in P.SCHEMA for m in re.findall(r"CREATE RANGE INDEX \w+ IF NOT EXISTS FOR \(n:(\w+)\) ON \(n\.(\w+)\)", s)}
    assert indexes == {("Work", "doi"), ("Work", "arxiv_base_id"), ("Work", "openalex_id"),
                       ("PaperVersion", "arxiv_base_id"), ("Claim", "paper_version_id"),
                       ("Junction", "conclusion_id"), ("Junction", "derivation_id"), ("Placeholder", "kind")}
    assert len(P.SCHEMA) == 1 + 10 + len(P.REL_TYPES) + 8
    names = [re.search(r"CREATE (?:CONSTRAINT|RANGE INDEX) (\w+)", s).group(1) for s in P.SCHEMA]
    assert len(set(names)) == len(names)


def balanced(text):
    text = re.sub(r"'[^']*'", "''", "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("//")))
    stack, pairs = [], {")": "(", "]": "[", "}": "{"}
    for ch in text:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs and (not stack or stack.pop() != pairs[ch]):
            return False
    return not stack


def test_audits_are_zero_row_queries_of_invariant_and_id():
    names = [name for name, _ in P.AUDITS]
    assert names == ["G1", "G2", "G3", "G4", "G5", "G7", "G8", "G9", "G10", "G11", "G12", "G13", "G14", "G15"]
    for name, query in P.AUDITS:
        assert balanced(query) and ";" not in query
        for branch in re.split(r"^UNION ALL$", query, flags=re.M):
            assert re.search(rf"^RETURN (DISTINCT )?'{name}' AS invariant, \w+(\.id)? AS id$", branch.strip(), re.M)
            assert branch.strip().splitlines()[-1].startswith("RETURN")
        assert set(re.findall(r"\$(\w+)", query)) <= set(rows()["params"])
        assert set(re.findall(r"\$enums\.(\w+)", query)) <= set(P.ENUMS)
        assert not re.search(r"VERIFIED|\bCREATE\b|\bMERGE\b|\bSET\b|\bDELETE\b", query)


def test_browse_templates_are_bounded():
    assert set(P.BROWSE) == {"premises", "dependents", "junctions", "paper_claims", "work_requests"}
    for name, query in P.BROWSE.items():
        assert balanced(query) and ";" not in query
        assert "{id: $id}" in query and re.search(r"^LIMIT \d+$", query, re.M)
        assert query.startswith("MATCH (:ProjectionManifest {state: 'READY'})")
        assert set(re.findall(r"\$(\w+)", query)) == {"id"}
        assert not re.search(r"\)-\(|\*|count\(|COUNT|\bCREATE\b|\bMERGE\b|\bSET\b|\bDELETE\b", query)
        rels = re.findall(r"(<?)-\[(\w*):([A-Z_]+)\]-(>?)", query)
        assert rels and len(rels) == query.count("-[")
        assert all(bool(left) != bool(right) for left, _, _, right in rels)
        for low, high in re.findall(r"\{(\d+),(\d+)\}", query):
            assert 1 <= int(low) <= int(high) <= 8


def test_load_protocol_order_and_ready_manifest():
    fake, manifest = Fake(), P.projection_manifest(MANIFEST, REVIEW_SET)
    contracts.validate("ProjectionManifest", manifest)
    result = P.load(fake, rows(), manifest)
    assert fake.kinds() == ["schema", "existing", "BUILDING", "preflight", "nodes", "rels", "audit", "READY"]
    contracts.validate("ProjectionManifest", result)
    assert result["state"] == "READY" and result["id"] == manifest["id"]
    assert result["audit_counts"]["G1"] == 0 and result["audit_counts"]["PREMISE_OF"] == 3
    assert result["audit_counts"]["Claim"] == 3 and "G6" not in result["audit_counts"]
    final = fake.calls[-1][1]["props"]
    assert final["id"] == manifest["id"] and final["audit_counts_G15"] == 0 and final["state"] == "READY"


def test_load_batches_at_most_batch_rows(monkeypatch):
    assert P.BATCH == 5000
    monkeypatch.setattr(P, "BATCH", 2)
    fake = Fake()
    P.load(fake, rows(), P.projection_manifest(MANIFEST, REVIEW_SET))
    sizes = [len(p["rows"]) for _, p, _ in fake.calls if "rows" in p]
    assert max(sizes) == 2 and sizes.count(1) >= 1


@pytest.mark.parametrize("stale", ["node", "relationship"])
def test_load_aborts_on_preflight_mismatch_before_writing(stale):
    out = rows()
    rid = A if stale == "node" else out["rels"]["PREMISE_OF"][0]["id"]
    fake = Fake(stale={rid})
    with pytest.raises(P.LoadError, match=f"preflight: 1 loaded ids differ in content, e.g. \\['{rid}'\\]"):
        P.load(fake, out, P.projection_manifest(MANIFEST, REVIEW_SET))
    assert fake.kinds() == ["schema", "existing", "BUILDING", "preflight", "FAILED"]
    check = P.NODE_PREFLIGHT if stale == "node" else P.REL_PREFLIGHT["PREMISE_OF"]
    assert [c[0] for c in fake.calls if rid in {r["id"] for r in c[1].get("rows", ())}] == [check]


def test_load_aborts_on_count_shortfall():
    fake = Fake(short=P.REL_MERGE["STATES"])
    with pytest.raises(P.LoadError, match="STATES"):
        P.load(fake, rows(), P.projection_manifest(MANIFEST, REVIEW_SET))
    assert fake.kinds()[-2:] == ["rels", "FAILED"] and "audit" not in fake.kinds()


def test_load_marks_failed_on_a_client_error():
    fake = Fake(boom=P.REL_MERGE["READS"])
    with pytest.raises(P.LoadError, match="RuntimeError: Query API HTTP 400") as caught:
        P.load(fake, rows(), P.projection_manifest(MANIFEST, REVIEW_SET))
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert fake.kinds()[-2:] == ["rels", "FAILED"] and fake.calls[-1][1]["props"]["audit_counts_Claim"] == 3


@pytest.mark.parametrize("step", ["schema", "existing"])
def test_load_wraps_a_client_error_before_building_without_a_manifest(step):
    fake = Fake(boom=P.SCHEMA[0] if step == "schema" else P.EXISTING)
    with pytest.raises(P.LoadError, match="RuntimeError: Query API HTTP 400") as caught:
        P.load(fake, rows(), P.projection_manifest(MANIFEST, REVIEW_SET))
    assert isinstance(caught.value.__cause__, RuntimeError) and fake.kinds()[-1] == step  # no BUILDING or FAILED written


def test_load_aborts_on_audit_rows():
    fake = Fake(audit={"G8": [ER]})
    with pytest.raises(P.LoadError, match="G8"):
        P.load(fake, rows(), P.projection_manifest(MANIFEST, REVIEW_SET))
    assert fake.kinds()[-2:] == ["audit", "FAILED"]
    assert fake.calls[-1][1]["props"]["audit_counts_G8"] == 1


def test_load_refuses_another_projection_or_mismatched_rows():
    manifest = P.projection_manifest(MANIFEST, REVIEW_SET)
    fake = Fake(existing=["projection:" + hx("old")])
    with pytest.raises(P.LoadError, match="rebuild"):
        P.load(fake, rows(), manifest)
    assert fake.kinds() == ["schema", "existing"]
    fake = Fake()
    with pytest.raises(P.LoadError, match="different delta sets"):
        P.load(fake, rows(), P.projection_manifest(dict(MANIFEST, manifest_id="manifest:" + hx("m2")), REVIEW_SET))
    assert fake.calls == []


def test_export_csv(tmp_path):
    out = rows()
    argv = P.export_csv(out, tmp_path)
    assert argv[:4] == ["neo4j-admin", "database", "import", "full"] and argv[-1] == "neo4j"
    with (tmp_path / "nodes-ExternalRequest.csv").open(encoding="utf-8") as f:
        head, first = list(csv.reader(f))
    assert head[:2] == ["id:ID", ":LABEL"] and first[1] == "Placeholder;ExternalRequest;Logical;Entity"
    assert "asserted_by:string[]" in head and first[head.index("asserted_by:string[]")] == D1
    with (tmp_path / "rels-PREMISE_OF.csv").open(encoding="utf-8") as f:
        head, *body = list(csv.reader(f))
    assert head[:4] == [":START_ID", ":END_ID", ":TYPE", "id"] and "position:long" in head and len(body) == 3
    assert "flags:string[]" not in head and all("" not in (r[3], r[head.index("role:string")]) for r in body)
    out["nodes"]["Claim"][0]["props"]["methods"] = ["A;B"]
    with pytest.raises(ValueError):
        P.export_csv(out, tmp_path)


def test_query_client_request_shape(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout):
        seen.update(url=request.full_url, method=request.get_method(), body=json.loads(request.data),
                    auth=request.get_header("Authorization"))
        return io.BytesIO(json.dumps({"data": {"fields": ["n"], "values": [[3]]}, "bookmarks": []}).encode())

    monkeypatch.setattr(P.urllib.request, "urlopen", fake_urlopen)
    client = P.QueryClient("http://localhost:7474/", "neo4j", "neo4j", "secret")
    assert client.run("RETURN 3 AS n", {"x": 1}, {"id": "p"}) == [{"n": 3}]
    assert seen == {"url": "http://localhost:7474/db/neo4j/query/v2", "method": "POST",
                    "body": {"statement": "RETURN 3 AS n", "parameters": {"x": 1}, "txMetadata": {"id": "p"}},
                    "auth": "Basic bmVvNGo6c2VjcmV0"}
