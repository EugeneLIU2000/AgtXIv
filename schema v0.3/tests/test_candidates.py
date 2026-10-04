"""Claim-reference policy CLAIM_REFERENCE_V1, the mention table and batch index rebinding."""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from candidates import CLAIM_REFERENCE_POLICY, assemble_candidates, select_candidate_graph
from chunks import bundle
from core import canonical, digest
from model import CLAIM_RESPONSE_COMPAT_SCHEMA, CLAIM_RESPONSE_SCHEMA

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def claim(statement, sources, support=(), cites=(), **new):
    return {"source_occurrence_ids": list(sources), "source_locators": [], "statement": statement,
            "kind": "theorem", "conditions": [], "internal_support_occurrence_ids": list(support),
            "external_citation_keys": list(cites), "unresolved_dependencies": [], "confidence": 0.5, **new}


def paper(occurrences=("o1", "o2", "o3", "o4")):
    return {"paper": {"id": "arxiv:0000.00001v1", "source_manifest_sha256": "sha256:" + "0" * 64},
            "claims": [{"id": oid, "source": {"path": "main.tex", "byte_start": index}}
                       for index, oid in enumerate(occurrences)],
            "bibliography": [{"key": key, "id": "bib:" + key, "source": {"path": "main.bib"}} for key in ("k1", "k2")]}


def respond(tmp_path, candidate, name="response.json"):
    path = tmp_path / name
    path.write_bytes(canonical(candidate))
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}


def assemble(tmp_path, claims, **policy):
    candidate = {"claims": claims, "unread_or_uncertain_scope": []}
    return assemble_candidates(paper(), candidate, [], response_reference=respond(tmp_path, candidate), **policy)


# o1: A alone; o2: B1 and B2; o3: never extracted; o4: C and C2.
LEGACY_CLAIMS = [claim("A", ["o1"], ["o1", "o2", "o3"], ["k1"]), claim("B1", ["o2"]), claim("B2", ["o2"]),
                 claim("C", ["o4"], ["o4"]), claim("C2", ["o4"])]


def test_legacy_response_assembles_identically_to_before(tmp_path, monkeypatch):
    # Golden assembly and graph digest from b9f6432's graph.py, candidates.py, model.py on this input, cwd-relative response.json.
    monkeypatch.chdir(tmp_path)
    candidate = {"claims": LEGACY_CLAIMS, "unread_or_uncertain_scope": []}
    now = assemble_candidates(paper(), candidate, [], response_reference=respond(Path(), candidate))
    assert "claim_reference_policy" not in now and "mentions" not in now
    assert json.loads((FIXTURES / "legacy_candidates_b9f6432.json").read_bytes()) == json.loads(json.dumps(now))
    assert digest(canonical(select_candidate_graph(now))) == "sha256:2cd8c944caad0c4f84d5cd9b6c99f5cd941369830f0dd3823e687c5dbea480e4"


def test_claim_reference_v1_rules(tmp_path):
    legacy = assemble(tmp_path, LEGACY_CLAIMS)
    v1 = assemble(tmp_path, LEGACY_CLAIMS, claim_reference_policy=CLAIM_REFERENCE_POLICY)
    ids = dict(zip("A B1 B2 C C2".split(), v1["query_ids"]))
    assert v1["query_ids"] == legacy["query_ids"]
    groups = {row["target"]: row for row in v1["support_groups"]}
    requests = {row["id"]: row for row in v1["dependency_requests"]}
    issues = {(row["code"], row.get("occurrence_id")): row for row in v1["issues"]}
    members = groups[ids["A"]]["members"]
    # own occurrence, no sibling: dropped, not a blocker
    assert ("SELF_OCCURRENCE_REFERENCE", "o1") in issues
    assert not any(requests.get(m, {}).get("occurrence_id") == "o1" for m in members)
    # another occurrence with two claims: both joint members
    assert {ids["B1"], ids["B2"]} <= set(members)
    assert issues[("MULTI_CLAIM_OCCURRENCE_EXPANDED", "o2")]["member_ids"] == sorted([ids["B1"], ids["B2"]])
    assert groups[ids["A"]]["grouping_basis"].endswith("MULTI_CLAIM_OCCURRENCES_EXPANDED_JOINTLY")
    # not yet extracted, and own occurrence with a sibling: placeholders remain
    reasons = {row["occurrence_id"]: row["reason"] for row in v1["dependency_requests"]
               if row["request_kind"] == "unresolved_claim_occurrence"}
    assert reasons == {"o3": "NOT_YET_EXTRACTED", "o4": "AMBIGUOUS_OR_SELF_CLAIM"}
    assert {requests[m]["request_kind"] for m in groups[ids["C"]]["members"]} == {"unresolved_claim_occurrence"}
    assert v1["graph_format"] == "COMPACT_V1" and v1["mentions"] == []
    # the policy travels with the assembly, so reconstruction from a legacy-shaped response reproduces it
    assert assemble(tmp_path, LEGACY_CLAIMS, claim_reference_policy=v1.get("claim_reference_policy")) == v1
    legacy_reasons = sorted(row["occurrence_id"] for row in legacy["dependency_requests"]
                            if row["request_kind"] == "unresolved_claim_occurrence")
    assert legacy_reasons == ["o1", "o2", "o3", "o4"]


def test_expansion_closing_a_cycle_reverts_to_a_placeholder(tmp_path):
    # A cites o2 (B1, B2); B1 cites o1 (A alone): expanding into B1 closes A <-> B1, B2 does not. C <-> D is direct.
    claims = [claim("A", ["o1"], ["o2"]), claim("B1", ["o2"], ["o1"]), claim("B2", ["o2"]),
              claim("C", ["o3"], ["o4"]), claim("D", ["o4"], ["o3"])]
    v1 = assemble(tmp_path, claims, claim_reference_policy=CLAIM_REFERENCE_POLICY)
    ids = dict(zip("A B1 B2 C D".split(), v1["query_ids"]))
    groups = {row["target"]: row["members"] for row in v1["support_groups"]}
    [placeholder] = [row for row in v1["dependency_requests"] if row["request_kind"] == "unresolved_claim_occurrence"]
    assert groups[ids["A"]] == sorted([ids["B2"], placeholder["id"]]) and groups[ids["B1"]] == [ids["A"]]
    assert placeholder["reason"] == "SHARED_OCCURRENCE_EXPANSION_CYCLIC" and placeholder["candidate_claim_ids"] == [ids["B1"]]
    assert [(row["subject"], row["placeholder_id"]) for row in v1["issues"]
            if row["code"] == "SHARED_OCCURRENCE_EXPANSION_CYCLIC"] == [(ids["A"], placeholder["id"])]
    assert [scc["members"] for scc in select_candidate_graph(v1)["sccs"]] == [sorted([ids["C"], ids["D"]])]
    reversed_v1 = assemble(tmp_path, claims[::-1], claim_reference_policy=CLAIM_REFERENCE_POLICY)
    assert [row["reason"] for row in reversed_v1["dependency_requests"]] == [placeholder["reason"]]
    # A direct reference to B1 already closes A <-> B1: the expansion is kept whole, with no placeholder.
    direct = assemble(tmp_path, [{**claims[0], "internal_support_claim_indexes": [1]}, *claims[1:]])
    assert direct["dependency_requests"] == [] and direct["support_groups"][0]["members"] == sorted([ids["B1"], ids["B2"]])


def test_new_fields_enable_the_policy_and_mentions_never_support(tmp_path):
    claims = [claim("A", ["o1"], [], ["k1"], internal_support_claim_indexes=[1], external_mention_citation_keys=["k2"]),
              claim("B", ["o2"], [], [], internal_support_claim_indexes=[], external_mention_citation_keys=[])]
    assembly = assemble(tmp_path, claims)
    a, b = assembly["query_ids"]
    assert assembly["claim_reference_policy"] == CLAIM_REFERENCE_POLICY
    [group] = assembly["support_groups"]
    assert group["target"] == a and b in group["members"]
    assert assembly["mentions"] == [{"claim_id": a, "citation_key": "k2", "relation": "MENTION_NOT_SUPPORT",
                                     "bibliography_ids": ["bib:k2"]}]
    assert [row["citation_key"] for row in assembly["dependency_requests"]] == ["k1"]
    assert select_candidate_graph(assembly)["graph_format"] == "COMPACT_V1"


@pytest.mark.parametrize("indexes,mentions,code", [
    ([0], [], "MODEL_CLAIM_INDEX_INVALID"), ([5], [], "MODEL_CLAIM_INDEX_INVALID"), ([1.0], [], "MODEL_CLAIM_INDEX_INVALID"),
    ([], ["k1"], "MODEL_CITATION_ROLE_CONFLICT"), ([], ["zz"], "MODEL_CITATION_KEY_UNKNOWN"),
    ([1, 1], [], "MODEL_DUPLICATE_REFERENCE")])
def test_invalid_new_references_are_rejected(tmp_path, indexes, mentions, code):
    claims = [claim("A", ["o1"], [], ["k1"], internal_support_claim_indexes=indexes, external_mention_citation_keys=mentions),
              claim("B", ["o2"])]
    with pytest.raises(ValueError) as error:
        assemble(tmp_path, claims)
    assert code in {row["code"] for row in error.value.args[0]["issues"]}


def test_model_schema_requires_new_fields_and_compat_schema_does_not():
    legacy = {"claims": [claim("A", ["o1"])], "unread_or_uncertain_scope": []}
    assert list(Draft202012Validator(CLAIM_RESPONSE_SCHEMA).iter_errors(legacy))
    assert not list(Draft202012Validator(CLAIM_RESPONSE_COMPAT_SCHEMA).iter_errors(legacy))
    negative = {"claims": [claim("A", ["o1"], internal_support_claim_indexes=[-1], external_mention_citation_keys=[])],
                "unread_or_uncertain_scope": []}
    assert list(Draft202012Validator(CLAIM_RESPONSE_SCHEMA).iter_errors(negative))


def test_bundle_rebinds_batch_local_claim_indexes(tmp_path):
    source = b"\\begin{theorem}x\\end{theorem}\n"
    blob = tmp_path / "sources" / digest(source).removeprefix("sha256:")
    blob.parent.mkdir()
    blob.write_bytes(source)
    files = [{"path": "main.tex", "sha256": digest(source), "byte_size": len(source),
              "blob_path": "sources/" + blob.name}]
    span = lambda i: {"path": "main.tex", "byte_start": i, "byte_end": i + 1, "sha256": digest(source),
                      "span_sha256": digest(source[i:i + 1])}
    frozen = paper(("o1", "o2", "o3", "o4", "o5"))
    for index, row in enumerate(frozen["claims"] + frozen["bibliography"]):
        row["source"] = span(index)
    extraction = tmp_path / "extraction.json"
    extraction.write_bytes(canonical({**frozen, "source_files": files}))
    new = lambda text, oid, support=(), confidence=0.5: {
        **claim(text, [oid], internal_support_claim_indexes=list(support), external_mention_citation_keys=[]),
        "confidence": confidence}
    batches = [[new("A", "o1"), new("B", "o2", [0]), new("C", "o3", confidence=0.4)],
               [new("D", "o4", [1, 2]), new("C", "o3"), new("E", "o5")]]  # C conflicts across batches
    chunks = []
    for index, claims in enumerate(batches):
        response = respond(tmp_path, {"claims": claims, "unread_or_uncertain_scope": []}, f"r{index}.json")
        provenance = tmp_path / f"p{index}.json"
        provenance.write_bytes(canonical({"paper_id": "arxiv:0000.00001v1", "source_files": files}))
        chunks.append({"id": f"c{index}", "response": response["path"], "provenance": str(provenance), "read_spans": []})
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(canonical({"paper_id": "arxiv:0000.00001v1", "extraction": str(extraction), "chunks": chunks}))
    bundle(manifest, tmp_path / "combined")
    combined = json.loads((tmp_path / "combined" / "response.json").read_bytes())["claims"]
    rows = {row["statement"]: row for row in combined}
    assert [row["statement"] for row in combined] == ["A", "B", "D", "E"]
    assert rows["B"]["internal_support_claim_indexes"] == [0]
    assert rows["D"]["internal_support_claim_indexes"] == [3]
    assert len(rows["D"]["unresolved_dependencies"]) == 1  # C was excluded pending reconciliation
