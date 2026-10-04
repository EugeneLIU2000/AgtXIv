"""Library retrieval, root audits, backend retrieval payload and the triviality probe."""
import json
import os
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from chunks import reference
from core import digest, write_json
import library
import proof_backend
from proof_backend import ModelProofBackend, statement_triviality

ENV = "sha256:" + "a" * 64
RECEIPT = {"kind": "ProgramReceipt", "contract_version": "0.3.0", "program": "agtxiv.proof-backend/0.3.0",
           "operation": "lean.library_index", "engine_class": "HOST", "call": None, "status": "SUCCEEDED",
           "outcome": "RECORDED", "exit_code": 0, "input_sha256": "sha256:" + "1" * 64,
           "output_sha256": "sha256:" + "2" * 64, "started_at": "t0", "finished_at": "t1", "elapsed_seconds": 1.0}
ROWS = sorted([
    {"name": "SimpleGraph.IsClique.card_le", "kind": "THEOREM", "module": "Mathlib.Combinatorics.SimpleGraph.Clique",
     "type": "∀ {V : Type u} (G : SimpleGraph V) (s : Finset V), G.IsClique ↑s → s.card ≤ Fintype.card V"},
    {"name": "SimpleGraph.IsIndepSet.card_le", "kind": "THEOREM", "module": "Mathlib.Combinatorics.SimpleGraph.Clique",
     "type": "∀ {V : Type u} (G : SimpleGraph V) (s : Finset V), G.IsIndepSet ↑s → s.card ≤ Fintype.card V"},
    {"name": "Matrix.det_mul", "kind": "THEOREM", "module": "Mathlib.LinearAlgebra.Matrix.Determinant.Basic",
     "type": "∀ (M N : Matrix n n R), (M * N).det = M.det * N.det"},
    {"name": "Finset.card_inter_le", "kind": "THEOREM", "module": "Mathlib.Data.Finset.Card",
     "type": "∀ (s t : Finset α), (s ∩ t).card ≤ s.card"},
    {"name": "Convex.sum_mem", "kind": "THEOREM", "module": "Mathlib.Analysis.Convex.Combination",
     "type": "Convex R s → (∀ i ∈ t, 0 ≤ w i) → ∑ i ∈ t, w i = 1 → ∑ i ∈ t, w i • z i ∈ s"},
], key=lambda row: row["name"])
NODE = {"id": "claim:root", "kind": "lemma", "text": r"Every independent set meets a clique of the graph $G$ in at most one vertex.",
        "conditions": [r"$S$ is an independent set and $Q$ is a clique of $G$."]}


def write_index(tmp_path, environment_sha256=ENV):
    """A manifest over Lean-order rows; load_index sorts them by name."""
    lean_rows = tmp_path / (environment_sha256[-8:] + ".jsonl")
    lean_rows.write_text("".join(json.dumps(row) + "\n" for row in reversed(ROWS)))
    return write_json(tmp_path / (environment_sha256[-8:] + ".json"), {"kind": "LibraryIndex", "lean_rows": reference(lean_rows),
                      "environment_sha256": environment_sha256, "program_receipt": RECEIPT})


def schema_errors(value, kind):
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas/research.schema.json").read_bytes())
    return list(Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/" + kind}).iter_errors(value))


def test_retrieval_is_deterministic_and_lexically_relevant():
    names = [row["name"] for row in library.retrieve(NODE, ROWS, 3)]
    assert names == ["SimpleGraph.IsClique.card_le", "SimpleGraph.IsIndepSet.card_le"]
    assert "Matrix.det_mul" not in names
    assert [row["name"] for row in library.retrieve(NODE, list(reversed(ROWS)), 3)] == names
    assert library.retrieve({"text": "zzz unrelated"}, ROWS, 3) == []


def test_retrieve_by_names_prefers_exact_and_suffix_matches():
    found = library.retrieve_by_names(["card_inter_le", "IsClique.card"], ROWS, 2)
    assert [row["name"] for row in found["card_inter_le"]] == ["Finset.card_inter_le", "SimpleGraph.IsClique.card_le"]
    assert found["IsClique.card"][0]["name"] == "SimpleGraph.IsClique.card_le"


def test_unknown_identifiers_parses_current_and_legacy_lean_messages():
    log = ("a.lean:3:4: error: Unknown identifier `Finset.card_inter_lt`\n"
           "b.lean:1:1: error: unknown constant 'Foo.bar'\nUnknown identifier `Finset.card_inter_lt`")
    assert library.unknown_identifiers(log) == ["Finset.card_inter_lt", "Foo.bar"]


def test_root_audits_skip_placeholders_and_match_schema():
    ref = {"path": "/tmp/index.json", "sha256": ENV, "byte_size": 1}
    graph = {"nodes": [NODE, {"id": "occ:1", "kind": "unresolved_claim_occurrence", "text": "clique"},
                       {"id": "req:1", "kind": "external_claim_request", "text": "clique"}],
             "roots": [{"id": "claim:root"}, {"id": "occ:1"}, {"id": "req:1"}]}
    index = {"environment_sha256": ENV, "rows": ROWS, "program_receipt": RECEIPT}
    audits = library.root_audits(graph, ref, index, ENV, k=2)
    assert list(audits) == ["claim:root"]
    audit = audits["claim:root"]
    assert audit["status"] == "LIBRARY_SEARCHED" and audit["binding_accepted"] is False
    assert audit["searched_revisions"] == [ENV] and audit["candidates"][0] == "SimpleGraph.IsClique.card_le"
    assert schema_errors(audit, "RootAudit") == []
    assert schema_errors({**audit, "searched_revisions": []}, "RootAudit")
    assert schema_errors({"status": "LIBRARY_BOUND", "program_receipt": RECEIPT}, "RootAudit")
    with pytest.raises(ValueError):
        library.root_audits(graph, ref, index, "sha256:" + "b" * 64)


class Ledger:
    plan = {"limits": {"max_call_seconds": 5}}

    def __init__(self, history=()):
        self.history = list(history)

    def proof_attempt_history(self, node_id, kind=None):
        return self.history


def prompt_payload(tmp_path, monkeypatch, node, *, history=(), library_index=None):
    prompts = []

    def call_model(ledger, operation, tier, prompt, schema, directory, **kwargs):
        prompts.append(prompt)
        return {"candidate": None, "receipt": {"error": "STUB"}}

    monkeypatch.setattr(proof_backend, "call_model", call_model)
    monkeypatch.setattr(ModelProofBackend, "_check_environment", lambda self: None)
    monkeypatch.setattr(ModelProofBackend, "_source_context", lambda self, node: ([], []))
    backend = ModelProofBackend.__new__(ModelProofBackend)
    backend.ledger, backend.output, backend.library, backend.paper_sources = Ledger(history), tmp_path / "out", [], {}
    backend.library_index, backend._indexes, backend.environment = library_index, {}, {"environment_sha256": ENV}
    backend.output.mkdir(exist_ok=True)
    backend._candidate(node, {}, {"id": "proof-attempt:" + str(len(list(backend.output.iterdir())))})
    text = prompts[0]
    return text, json.loads(text[text.index('{"node"'):])


def test_load_index_reads_pinned_lean_rows(tmp_path):
    index_ref = write_index(tmp_path)
    assert library.load_index(index_ref)["rows"] == ROWS
    Path(json.loads(Path(index_ref["path"]).read_bytes())["lean_rows"]["path"]).write_text("{}\n")
    with pytest.raises(ValueError):
        library.load_index(index_ref)


def test_retrieval_rows_enter_the_payload_only_when_present(tmp_path, monkeypatch):
    index_ref = write_index(tmp_path)
    text, payload = prompt_payload(tmp_path, monkeypatch, NODE)
    assert "retrieved_library_candidates" not in payload and "library_search_for_unknown_identifiers" not in payload
    assert "Retrieved library rows" not in text
    audited = {**NODE, "root_audit": library.root_audits({"nodes": [NODE], "roots": [{"id": NODE["id"]}]}, index_ref,
               {"environment_sha256": ENV, "rows": ROWS, "program_receipt": RECEIPT}, ENV, k=2)[NODE["id"]]}
    text, payload = prompt_payload(tmp_path, monkeypatch, audited)
    assert payload["retrieved_library_candidates"] == [
        {"name": row["name"], "type": row["type"]} for row in library.retrieve(NODE, ROWS, 2)]
    assert "Retrieved library rows" in text and "library_search_for_unknown_identifiers" not in payload
    log = b"x.lean:2:3: error: Unknown identifier `card_inter_le`\n"
    (tmp_path / "failed.log").write_bytes(log)
    failed = {"result": {"kernel_checked": False, "program_receipt": {
        "log": str(tmp_path / "failed.log"), "output_sha256": digest(log)}}}
    _, payload = prompt_payload(tmp_path, monkeypatch, NODE, history=[failed], library_index=index_ref)
    search = payload["library_search_for_unknown_identifiers"]
    assert search["unknown_identifiers"] == ["card_inter_le"]
    assert search["candidates"]["card_inter_le"][0] == {"name": "Finset.card_inter_le", "type": ROWS[1]["type"]}
    _, payload = prompt_payload(tmp_path, monkeypatch, NODE, history=[failed])
    assert "library_search_for_unknown_identifiers" not in payload
    with pytest.raises(ValueError, match="another proof environment"):
        prompt_payload(tmp_path, monkeypatch, NODE, history=[failed], library_index=write_index(tmp_path, "sha256:" + "b" * 64))


def test_triviality_runs_one_bounded_probe_per_tactic(tmp_path, monkeypatch):
    def run(proved, missing=0):
        def run_lean(environment, source, directory, operation, *, timeout):
            probes = [line.split()[1] for line in Path(source).read_text().splitlines() if line.startswith("theorem ")]
            rows = [{"declaration": probe, "axioms": [] if number in proved else ["sorryAx"]}
                    for number, probe in enumerate(probes[missing:], missing)]
            return {"status": "FAILED"}, "".join("AGTXIV_AUDIT_JSON " + json.dumps(row) + "\n" for row in rows)
        monkeypatch.setattr(proof_backend, "_run_lean", run_lean)
        directory = tmp_path / str(len(list(tmp_path.iterdir())))
        result = statement_triviality({"environment_sha256": ENV}, directory, "A.b", ["M"])
        return result, (directory / "Triviality.lean").read_text()
    result, source = run({3})
    assert result["statement_trivially_provable"] is True and set(result["statement_triviality"]) == {"lean_source", "program_receipt"}
    assert source.count("set_option maxHeartbeats 20000 in\ntheorem A.b_trivial_") == len(proof_backend.TRIVIALITY_TACTICS)
    assert "first" not in source and "  intros; decide\n#agtxiv_audit A.b_trivial_2\n" in source
    assert run(set())[0]["statement_trivially_provable"] is False
    assert run(set(), missing=1)[0]["statement_trivially_provable"] is None
    assert run({4}, missing=1)[0]["statement_trivially_provable"] is True



def test_audit_rebuilds_the_triviality_probe_and_rejects_a_forged_flag(tmp_path, monkeypatch):
    from audit_proof_walk import Auditor
    rows = lambda source: [{"declaration": line.split()[1], "axioms": ["sorryAx"]}  # every tactic failed
                           for line in Path(source).read_text().splitlines() if line.startswith("theorem ")]
    monkeypatch.setattr(proof_backend, "_run_lean", lambda environment, source, directory, operation, *, timeout: (
        {"operation": operation, "status": "FAILED", "cwd": str(directory), "execution_context": {"lean_path": environment["lean_path"]}},
        "".join("AGTXIV_AUDIT_JSON " + json.dumps(row) + "\n" for row in rows(source))))
    environment, module, directory = {"environment_sha256": ENV, "imports": ["M", "M"]}, "Proof_x", tmp_path.resolve() / "attempt"
    directory.mkdir()
    env = {**environment, "lean_path": "compiled:base"}
    result = {"program_receipt": {"execution_context": {"lean_path": "compiled:base"}}, **statement_triviality(
        env, directory / "triviality", "AgtXIv.Generated." + module, environment["imports"] + [module])}
    auditor = Auditor(tmp_path)  # the receipt/log hash checks are lean_receipt's; stub it with the log's audit rows
    source = directory / "triviality" / "Triviality.lean"
    monkeypatch.setattr(auditor, "lean_receipt", lambda receipt, environment: (rows(source), [], source.read_bytes(), ""))
    auditor.triviality(result, "AgtXIv.Generated." + module, module, environment, directory)
    assert result["statement_trivially_provable"] is False and auditor.issues == []
    for forged in ({**result, "statement_trivially_provable": None}, {**result, "statement_trivially_provable": True}):
        auditor.triviality(forged, "AgtXIv.Generated." + module, module, environment, directory)
    assert [issue["code"] for issue in auditor.issues] == ["TRIVIALITY_PROBE_NOT_SUPPORTED_BY_LOG"] * 2


REAL_ENVIRONMENT = Path("/Users/Yingjian/Documents/GitHub/AgtXIv/schema v0.3/runs/"
                        "proof-worker-environment-prop-v2-attempt02-20260919/environment.json")


@pytest.mark.skipif(os.environ.get("AGTXIV_LEAN_TESTS") != "1" or not REAL_ENVIRONMENT.is_file(),
                    reason="runs sandboxed Lean in the frozen proof environment; set AGTXIV_LEAN_TESTS=1")
def test_triviality_probe_in_real_environment(tmp_path):
    environment = json.loads(REAL_ENVIRONMENT.read_bytes())
    trivial = statement_triviality(environment, tmp_path / "trivial", "le_refl", environment["imports"], timeout=900)
    assert trivial["statement_trivially_provable"] is True
    hard = statement_triviality(environment, tmp_path / "hard", "AgtXIv.GraphFoundation.indep_clique_inter_card_le_one",
                                environment["imports"], timeout=900)
    assert hard["statement_trivially_provable"] is False
