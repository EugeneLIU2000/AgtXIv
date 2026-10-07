"""corpus, ledger, routing and export_v03 on synthetic ids only; no paper, model, network, Neo4j or Lean."""
import copy
import hashlib

import pytest

import contracts
import corpus
import export_v03
import graph as v03_graph
import model_routing as v03_routing
import routing
from core import canonical, digest
from delta import LABELS, make_manifest
from ledger import CorpusLedger

S = "sha256:" + "a" * 64
T0 = "2026-09-25T00:00:00Z"


def hexid(prefix, n):
    return f"{prefix}:{n:064x}"


POLICY = {"kind": "AnalysisPolicy", "contract_version": "0.4.0", "policy_id": hexid("policy", 1), "status": "PRIMARY",
          "establishment_reading": {"mode": "UNION"}, "importance_methods": ["DETERMINISTIC_ANCHOR"],
          "work_identity": "EXPLICIT_IDS_ONLY", "citation_group_semantics": "AND", "cycle_policy": "FIXPOINT",
          "base_set": "ALL_ROOTS", "include_part_expansions": False, "traverse": "SAMPLE_ONLY", "count_basis": "SAMPLE_ONLY",
          "admission_gate": None, "nomination": {"rule": "FOUNDATION_V1", "threshold": 3, "top_k": 50},
          "bootstrap": {"scheme": "PAPER_REWEIGHT_V1", "replicates": 10, "seed": "b"}, "edge_precision": None}
GATES = {"P_MINUS_1": {"min_eligible_fraction": 0.3, "max_undetermined_fraction": 0.2,
                       "claim_level": {"min_works": 20, "min_citing_papers": 3}},
         "P0": {"admission_threshold": 0.85, "fpr_inflation": 2.0, "alpha": 0.05, "max_unresolved_fraction": 0.2,
                "min_items": 100, "require_projection_under_ceiling": True}}
FIELDS = {"field": {"primary_categories": ["quant-ph"], "date_window": {"start": "2015-01-01", "end": "2025-12-31"}},
          "sampling_frame": {"kind": "METADATA_SNAPSHOT", "sha256": S, "snapshot_date": "2026-09-01"},
          "eligibility": {"rule": "THEOREM_OR_DERIVATION_V1", "params": {"min_theorem_like": 1, "min_display_equations": 10},
                          "program_sha256": S, "parser_sha256": S}, "size_limits": {},
          "version_rule": "LATEST_ON_OR_BEFORE_SNAPSHOT", "seed": "sample-seed", "target_size": 60,
          "transient_retry_limit": 2, "coverage": "EQUAL_FULL",
          "extraction": {"operation": "paper.extract_focus", "method_version": "focus-1", "focus_bytes": 8192}, "gates": GATES,
          "primary_analysis_policy": POLICY, "budget_ceiling": {"unit": "calls", "value": 3}, "created_at": T0}
MANIFEST = corpus.freeze_corpus_manifest(FIELDS)
FRAME = [f"2101.{n:05d}" for n in range(200)]


def outcomes_until(manifest, frame, accept=lambda i: i % 4 != 1):
    """Examine in seeded order; every 4th candidate (offset 1) is ineligible, every 8th (offset 3) undetermined."""
    result, accepted = {}, 0
    for i, item in enumerate(corpus.order_frame(frame, manifest["seed"])):
        if accepted == manifest["target_size"]:
            break
        base = item["arxiv_base_id"]
        if i % 8 == 3:
            result[base] = {"outcome": "UNDETERMINED", "attempts": 3, "undetermined_class": "TRANSIENT_NETWORK"}
        elif not accept(i):
            result[base] = {"outcome": "INELIGIBLE", "attempts": 1, "reason": "no theorem-like environment"}
        else:
            result[base] = {"outcome": "ACCEPTED", "attempts": 1, "paper_version_id": f"arxiv:{base}v1"}
            accepted += 1
    return result


# ---- corpus.py ----

def test_manifest_is_content_addressed_and_host_fields_are_refused():
    assert MANIFEST["corpus_id"] == corpus.freeze_corpus_manifest(copy.deepcopy(FIELDS))["corpus_id"]
    assert MANIFEST["corpus_id"] != corpus.freeze_corpus_manifest({**FIELDS, "seed": "other"})["corpus_id"]
    with pytest.raises(ValueError, match="HOST_FIELD"):
        corpus.freeze_corpus_manifest({**FIELDS, "corpus_id": hexid("corpus", 9)})
    with pytest.raises(Exception):  # no prioritized arm: equal full coverage is the only coverage (§6.4)
        corpus.freeze_corpus_manifest({**FIELDS, "coverage": "PRIORITIZED"})
    with pytest.raises(Exception):
        corpus.freeze_corpus_manifest({**FIELDS, "audit_arm": {"min_fraction": 0.1, "min_papers": 50, "seed": "a"}})
    with pytest.raises(ValueError, match="CORPUS_ID_IS_NOT_THE_MANIFEST_DIGEST"):  # edited after freezing
        corpus.sample_record({**MANIFEST, "target_size": 5}, FRAME, {}, T0)


def test_order_key_is_the_spec_byte_rule_and_order_ignores_input_order():
    assert corpus.order_key("s", "2101.00001") == hashlib.sha256(b"s\x002101.00001").hexdigest()
    ordered = corpus.order_frame(FRAME, "s")
    assert ordered == corpus.order_frame(list(reversed(FRAME)), "s")
    assert [x["order_key"] for x in ordered] == sorted(x["order_key"] for x in ordered)
    assert ordered != corpus.order_frame(FRAME, "t")
    with pytest.raises(ValueError, match="DUPLICATE"):
        corpus.order_frame(FRAME + FRAME[:1], "s")
    with pytest.raises(ValueError, match="NOT_ARXIV"):
        corpus.order_frame(["arxiv:2101.00001v1"], "s")


def test_sample_record_stops_at_target_and_keeps_every_outcome():
    outcomes = outcomes_until(MANIFEST, FRAME)
    record = corpus.sample_record(MANIFEST, FRAME, outcomes, T0)
    contracts.validate("SamplingRecord", record)
    assert record == corpus.sample_record(MANIFEST, list(reversed(FRAME)), outcomes, T0)
    assert [row["arxiv_base_id"] for row in record["candidates"]] == \
        [row["arxiv_base_id"] for row in corpus.order_frame(FRAME, "sample-seed")][:len(outcomes)]
    counts = corpus.estimand_counts(record)
    assert counts["accepted"] == 60 and counts["examined"] == len(outcomes)
    assert counts["examined"] == counts["accepted"] + counts["ineligible"] + sum(counts["undetermined"].values())
    assert set(counts["undetermined"]) == {"TRANSIENT_NETWORK"}
    assert "audit_arm" not in record  # every accepted paper receives the same extraction (EQUAL_FULL)
    body = {k: v for k, v in record.items() if k != "sampling_record_id"}
    assert record["sampling_record_id"] == "sampling:" + digest(canonical(body))[7:]


def test_sample_record_refuses_gaps_extras_and_bad_attempts():
    outcomes = outcomes_until(MANIFEST, FRAME)
    ordered = [x["arxiv_base_id"] for x in corpus.order_frame(FRAME, "sample-seed")]
    gap = {k: v for k, v in outcomes.items() if k != ordered[0]}
    with pytest.raises(ValueError, match="NOT_EXAMINED_IN_ORDER"):
        corpus.sample_record(MANIFEST, FRAME, gap, T0)
    extra = {**outcomes, ordered[len(outcomes)]: {"outcome": "INELIGIBLE", "attempts": 1, "reason": "r"}}
    with pytest.raises(ValueError, match="OUTSIDE_EXAMINED_PREFIX"):
        corpus.sample_record(MANIFEST, FRAME, extra, T0)
    first = ordered[0]
    for bad, code in (({"outcome": "UNDETERMINED", "attempts": 2, "undetermined_class": "TRANSIENT_NETWORK"}, "NOT_EXHAUSTED"),
                      ({"outcome": "INELIGIBLE", "attempts": 4, "reason": "r"}, "RETRY_LIMIT"),
                      ({"outcome": "ACCEPTED", "attempts": 1, "paper_version_id": "arxiv:2101.99999v1"}, "ANOTHER_BASE"),
                      ({"outcome": "INELIGIBLE", "attempts": 1, "reason": "r", "order_key": "0" * 64}, "FIELDS_INVALID"),
                      ({"outcome": "ACCEPTED", "attempts": 1, "paper_version_id": f"arxiv:{first}v1", "reason": "r"},
                       "FIELDS_INVALID")):
        with pytest.raises(ValueError, match=code):
            corpus.sample_record(MANIFEST, FRAME, {**outcomes, first: bad}, T0)
    with pytest.raises(Exception):  # the contract: an ACCEPTED candidate needs its paper version
        corpus.sample_record(MANIFEST, FRAME, {**outcomes, first: {"outcome": "ACCEPTED", "attempts": 1}}, T0)


def work(n, base=None, terminal="ARXIV_SOURCE_AVAILABLE"):
    row = {"id": hexid("work", n), "content_sha256": S, "work_kind": "ARTICLE", "terminal_kind": terminal}
    return {**row, "identity_basis": "ARXIV_BASE", "arxiv_base_id": base} if base else {**row, "identity_basis": "BIB_DIGEST", "bib_digest": S}


EXPANSION = {"source_manifest_id": hexid("manifest", 1), "selection_rule": "WORKS list top M",
             "analysis_run": {"policy_id": hexid("policy", 1), "manifest_id": hexid("manifest", 1)}, "M": 2}


def test_expansion_round_is_bounded_and_never_repeats_a_candidate():
    sample = corpus.sample_record(MANIFEST, FRAME, outcomes_until(MANIFEST, FRAME), T0)
    outcomes = {"2201.00001": {"outcome": "ACCEPTED", "attempts": 1, "paper_version_id": "arxiv:2201.00001v3"},
                "2201.00002": {"outcome": "UNDETERMINED", "attempts": 1, "undetermined_class": "NO_TEX_SOURCE"}}
    works = [work(1, "2201.00001"), work(2, "2201.00002")]
    record = corpus.expansion_record(MANIFEST, [sample], EXPANSION, works, outcomes, T0)
    contracts.validate("SamplingRecord", record)
    assert (record["round"], record["admission"], "audit_arm" in record) == (1, "EXPANSION", False)
    assert all("order_key" not in row for row in record["candidates"])
    second = corpus.expansion_record(MANIFEST, [record, sample], EXPANSION, [work(3, "2201.00003")],
                                     {"2201.00003": {"outcome": "INELIGIBLE", "attempts": 1, "reason": "k=0"}}, T0)
    assert second["round"] == 2
    with pytest.raises(ValueError, match="EXCEEDS_M"):
        corpus.expansion_record(MANIFEST, [sample], EXPANSION, works + [work(3, "2201.00003")], outcomes, T0)
    with pytest.raises(ValueError, match="NOT_EXPANDABLE"):
        corpus.expansion_record(MANIFEST, [sample], EXPANSION, [work(4, terminal="MONOGRAPH")], {}, T0)
    sampled = sample["candidates"][0]["arxiv_base_id"]
    with pytest.raises(ValueError, match="REPEATED"):
        corpus.expansion_record(MANIFEST, [sample], EXPANSION, [work(5, sampled)],
                                {sampled: {"outcome": "INELIGIBLE", "attempts": 1, "reason": "r"}}, T0)
    with pytest.raises(ValueError, match="FIELDS_INVALID"):  # expansion candidates have no seeded draw position
        corpus.expansion_record(MANIFEST, [sample], EXPANSION, works[:1],
                                {"2201.00001": {**outcomes["2201.00001"], "order_key": "0" * 64}}, T0)
    for prior in ([], [record]):
        with pytest.raises(ValueError, match="PRIOR_ROUNDS"):
            corpus.expansion_record(MANIFEST, prior, EXPANSION, works, outcomes, T0)
    with pytest.raises(ValueError, match="OUTSIDE_P"):
        corpus.estimand_counts(record)


def test_includes_delta_asserts_every_accepted_paper_version_from_frozen_metadata():
    sample = corpus.sample_record(MANIFEST, FRAME, outcomes_until(MANIFEST, FRAME), T0)
    accepted = [row["paper_version_id"] for row in sample["candidates"] if row["outcome"] == "ACCEPTED"]
    date = {"value": "2021-01-01", "kind": "ARXIV_V1", "precision": "DAY", "source": "snapshot"}
    meta = {pv: {"primary_category": "quant-ph", "categories": ["quant-ph"], "redistribution": "UNKNOWN", "date_v1": date,
                 "date_version": date, "source_sha256": "sha256:" + "b" * 64} for pv in accepted}
    s1 = corpus.includes_delta(sample, MANIFEST, meta)
    rows = s1["nodes"]["PaperVersion"]
    assert (s1["stage"], s1["method"], s1["subject"]) == ("S1", "HOST_RULE", {"kind": "MANIFEST", "id": sample["sampling_record_id"]})
    assert sorted(r["id"] for r in rows) == sorted(accepted) and {r["parser_sha256"] for r in rows} == {S}  # eligibility.parser_sha256
    assert sorted(e["end_id"] for e in s1["edges"] if e["type"] == "INCLUDES") == sorted(accepted)
    for bad, code in ((dict(list(meta.items())[1:]), "NOT_THE_ACCEPTED_PAPERS"),
                      ({**meta, accepted[0]: {**meta[accepted[0]], "parser_sha256": S}}, "HOST_FIELD")):
        with pytest.raises(ValueError, match=code):
            corpus.includes_delta(sample, MANIFEST, bad)
    with pytest.raises(ValueError, match="ANOTHER_CORPUS"):
        corpus.includes_delta(sample, corpus.freeze_corpus_manifest({**FIELDS, "seed": "other"}), meta)


# ---- routing.py ----

def rehash(policy):
    policy = {k: v for k, v in policy.items() if k != "sha256"}
    return {**policy, "sha256": digest(canonical(policy))}


V04_OPERATIONS = {"paper.extract_local", "paper.extract_focus", "dependency.match_retrieved", "leg.judge", "match.judge",
                  "corpus.discover"}


def test_routing_v2_adds_the_v04_operations_with_unknown_cutoffs():
    policy = routing.freeze_model_routing_v2()
    assert policy["version"] == "operation-routing-v2" and v03_routing.POLICY_VERSION == "operation-routing-v1"
    assert set(policy["operations"]) == set(v03_routing.OPERATION_CLASSES) | V04_OPERATIONS
    assert {op: policy["operations"][op]["engine_class"] for op in ("paper.extract_focus", "leg.judge", "match.judge",
                                                                    "corpus.discover")} == {
        "paper.extract_focus": "LIGHT", "leg.judge": "DECISION", "match.judge": "DECISION", "corpus.discover": "LIGHT"}
    assert policy["operations"]["paper.extract_local"]["engine_class"] == "LIGHT"
    assert policy["operations"]["dependency.match_retrieved"]["engine_class"] == "DECISION"
    assert all(r["training_cutoff"]["value"] == "UNKNOWN" for r in policy["operations"].values())
    selection = routing.select_model_route(policy, "dependency.match_retrieved", "DECISION")
    contracts.validate("ModelSelectionV4", selection)
    assert selection["policy_sha256"] == policy["sha256"]
    with pytest.raises(ValueError, match="FORBIDDEN"):
        routing.select_model_route(policy, "paper.extract_local", "HEAVY")


def test_routing_v2_refuses_tampered_policies():
    policy = routing.freeze_model_routing_v2()
    dated = copy.deepcopy(policy)
    dated["operations"]["paper.extract_local"]["training_cutoff"] = {"value": "2025-06", "source": "provider model card"}
    routing.validate_policy(rehash(dated))
    cases = []
    for path, value in ((("paper.extract_local", "model"), "gpt-6-astra"),
                        (("dependency.match_retrieved", "engine_class"), "LIGHT"),
                        (("paper.extract_local", "training_cutoff"), {"value": "June 2025", "source": "x"}),
                        (("paper.extract", "training_cutoff"), None), (("paper.extract", "reason"), "  ")):
        bad = copy.deepcopy(policy)
        bad["operations"][path[0]][path[1]] = value
        cases.append((rehash(bad), "ROUTE_INVALID"))
    borrowed = copy.deepcopy(policy)  # a route may not carry its own operation to borrow another operation's rules
    borrowed["operations"]["autoformalization.lean"] = {**policy["operations"]["paper.extract"], "operation": "paper.extract"}
    moved = copy.deepcopy(policy)
    moved["operations"]["autoformalization.failure_classify"]["engine_class"] = "LIGHT"
    cases += [(rehash(borrowed), "ROUTE_INVALID"), (rehash(moved), "ROUTE_INVALID")]
    missing = copy.deepcopy(policy)
    del missing["operations"]["dependency.match_retrieved"]
    cases += [(rehash(missing), "OPERATION_SET"), ({**policy, "automatic_escalation": True}, "HASH_MISMATCH"),
              (rehash({**policy, "quality_calibration": {}}), "AUTHORITY"),
              (rehash({**policy, "version": "operation-routing-v1"}), "UNSUPPORTED")]
    for bad, code in cases:
        with pytest.raises(ValueError, match=code):
            routing.validate_policy(bad)


# ---- ledger.py ----

KEY = ("S6", "CLAIM_BATCH", "batch-1", "MODEL_EXTRACTION", "v1", S)
CALL = {"provider": "codex", "account_ref": "acct", "amount": 1}  # a model dispatch spends one call of the ceiling


def open_ledger(tmp_path, **limits):
    return CorpusLedger(tmp_path / "ledger.sqlite", MANIFEST, **{"max_attempts_per_item": 3, "lease_seconds": 10, **limits})


def test_ledger_single_writer_frozen_config_and_idempotent_keys(tmp_path):
    with pytest.raises(ValueError, match="CORPUS_ID_IS_NOT"):
        CorpusLedger(tmp_path / "x.sqlite", {**MANIFEST, "budget_ceiling": {"unit": "calls", "value": 99}},
                     max_attempts_per_item=3, lease_seconds=10)
    ledger = open_ledger(tmp_path)
    key = ledger.add(*KEY)
    assert key == ledger.add(*KEY) and ledger.item(key)["state"] == "READY"
    assert key != ledger.add(*KEY[:-1], "sha256:" + "b" * 64)
    for bad in (("S0", *KEY[1:]), (KEY[0], "PAPER", *KEY[2:]), (*KEY[:-1], "abc")):
        with pytest.raises(ValueError, match="KEY_INVALID"):
            ledger.add(*bad)
    with pytest.raises(RuntimeError, match="ANOTHER_WRITER"):
        open_ledger(tmp_path)
    ledger.close()
    with pytest.raises(ValueError, match="CONFIG_FROZEN"):
        open_ledger(tmp_path, max_attempts_per_item=4)
    reopened = open_ledger(tmp_path)
    assert reopened.item(key)["state"] == "READY"


def test_ledger_reserve_settle_and_failure_classes(tmp_path):
    ledger = open_ledger(tmp_path)
    key, other = ledger.add(*KEY), ledger.add("S2", "PAPER_VERSION", "arxiv:2101.00001v1", "HOST_RULE", "v1", S)
    for item, bad in ((key, {}), (key, {**CALL, "amount": 0}), (key, {"provider": "codex", "amount": 1}), (other, CALL)):
        with pytest.raises(ValueError, match="ARGUMENTS_INVALID"):  # model items name a window and spend; host items do not
            ledger.reserve(item, 0, **bad)
    res = ledger.reserve(key, 0, **CALL)
    assert ledger.item(key)["state"] == "RUNNING" and ledger.item(key)["method"] == "MODEL_EXTRACTION"
    with pytest.raises(RuntimeError, match="NOT_DISPATCHABLE"):
        ledger.reserve(key, 1, **CALL)
    with pytest.raises(ValueError, match="BIND"):
        ledger.settle(res["id"], {"reservation_id": "sha256:" + "0" * 64}, 1)
    with pytest.raises(ValueError, match="CLASSIFICATION"):  # a non-provider error is never settled DONE
        ledger.settle(res["id"], {"reservation_id": res["id"], "error": "MODEL_OUTPUT_SCHEMA_INVALID"}, 1)
    assert ledger.settle(res["id"], {"reservation_id": res["id"]}, 1, cost=0.5) == "DONE"
    with pytest.raises(ValueError, match="NOT_LIVE"):
        ledger.settle(res["id"], {"reservation_id": res["id"]}, 2)
    host = ledger.reserve(other, 2)
    with pytest.raises(ValueError, match="CLASSIFICATION"):
        ledger.settle(host["id"], {"reservation_id": host["id"]}, 3, failure="MODEL_WAS_WRONG")
    with pytest.raises(ValueError, match="CLASSIFICATION"):  # a host item has no provider window to close
        ledger.settle(host["id"], {"reservation_id": host["id"], "error": "MODEL_PROVIDER_QUOTA_EXHAUSTED"}, 3)
    assert ledger.settle(host["id"], {"reservation_id": host["id"]}, 3, failure="SOURCE_READ_DEFECTIVE") == "FAILED"
    assert ledger.item(other)["detail"] == "SOURCE_READ_DEFECTIVE" and ledger.spent() == 0.5
    wrong = ledger.add(*KEY[:2], "batch-2", *KEY[3:])
    res = ledger.reserve(wrong, 4, **CALL)
    assert ledger.settle(res["id"], {"reservation_id": res["id"], "error": "MODEL_OUTPUT_SCHEMA_INVALID"}, 5,
                         failure="HOST_PROCESSING_FAILED") == "FAILED" and ledger.spent() == 1.5
    third = ledger.add("S7", "REQUEST_POOL", "pool-1", "MODEL_MATCH", "v1", S)
    ledger.skip(third, "NO_REQUESTS")
    assert ledger.items("SKIPPED") == [third]


def test_ledger_expired_lease_abandons_and_stays_spent(tmp_path):
    ledger = open_ledger(tmp_path)
    key = ledger.add(*KEY)
    res = ledger.reserve(key, 100, **{**CALL, "amount": 2})
    assert ledger.expire_leases(109) == [] and ledger.expire_leases(110) == [key]
    assert ledger.item(key) == {"key": key, "method": "MODEL_EXTRACTION", "state": "ABANDONED", "detail": "LEASE_EXPIRED",
                                "requeued": False, "attempts": 1, "dispatchable": False}
    assert ledger.spent() == 2
    with pytest.raises(ValueError, match="NOT_LIVE"):
        ledger.settle(res["id"], {"reservation_id": res["id"]}, 111)
    with pytest.raises(RuntimeError, match="NOT_DISPATCHABLE"):
        ledger.reserve(key, 111, **CALL)
    late = ledger.add(*KEY[:-1], "sha256:" + "c" * 64)
    with pytest.raises(RuntimeError, match="BUDGET"):
        ledger.reserve(late, 112, **{**CALL, "amount": 1.5})


def test_ledger_quota_closes_window_and_allows_one_reattempt(tmp_path):
    ledger = open_ledger(tmp_path)
    key, other = ledger.add(*KEY), ledger.add(*KEY[:2], "batch-2", *KEY[3:])
    quota = lambda r: {"reservation_id": r["id"], "error": "MODEL_PROVIDER_QUOTA_EXHAUSTED"}
    first = ledger.reserve(key, 0, **CALL)
    assert ledger.settle(first["id"], quota(first), 1, closed_until=50) == "QUOTA_WAIT"
    assert ledger.window("codex", "acct", 49) == "CLOSED_UNTIL" and ledger.window("codex", "acct", 50) == "OPEN"
    for item in (key, other):
        with pytest.raises(RuntimeError, match="WINDOW_CLOSED"):
            ledger.reserve(item, 10, **CALL)
    with pytest.raises(RuntimeError, match="ANOTHER_WINDOW"):
        ledger.reserve(key, 60, **{**CALL, "account_ref": "other-acct"})
    second = ledger.reserve(key, 60, **CALL)
    assert second["attempt"] == 2 and second["id"] != first["id"] and ledger.item(key)["requeued"]
    assert ledger.settle(second["id"], quota(second), 61) == "QUOTA_WAIT"
    assert not ledger.item(key)["dispatchable"] and ledger.item(other)["dispatchable"]  # the one re-attempt is used
    assert ledger.window("codex", "acct", 10 ** 9) == "CLOSED_UNKNOWN"
    ledger.open_window("codex", "acct")
    with pytest.raises(RuntimeError, match="REATTEMPT_USED"):
        ledger.reserve(key, 70, **CALL)
    ledger.reserve(other, 70, **CALL)


def test_ledger_quota_reattempt_counts_against_max_attempts(tmp_path):
    ledger = open_ledger(tmp_path, max_attempts_per_item=1)
    key = ledger.add(*KEY)
    first = ledger.reserve(key, 0, **CALL)
    ledger.settle(first["id"], {"reservation_id": first["id"], "error": "MODEL_PROVIDER_RATE_LIMITED"}, 1, closed_until=2)
    assert ledger.item(key)["state"] == "QUOTA_WAIT" and not ledger.item(key)["dispatchable"]
    with pytest.raises(RuntimeError, match="MAX_ATTEMPTS"):
        ledger.reserve(key, 3, **CALL)


def test_ledger_retries_a_rejected_response_while_attempts_remain(tmp_path):
    ledger = open_ledger(tmp_path)  # three attempts per item, a ceiling of three calls
    key, host = ledger.add(*KEY), ledger.add("S2", "PAPER_VERSION", "arxiv:2101.00001v1", "HOST_RULE", "v1", S)
    for n, expected in ((1, "READY"), (2, "READY"), (3, "FAILED")):
        res = ledger.reserve(key, 10 * n, **CALL)
        assert res["attempt"] == n
        assert ledger.settle(res["id"], {"reservation_id": res["id"]}, 10 * n + 1, failure="RESPONSE_REJECTED") == expected
        assert ledger.item(key)["detail"] == "RESPONSE_REJECTED" and ledger.item(key)["dispatchable"] == (expected == "READY")
    assert ledger.spent() == 3
    res = ledger.reserve(host, 40)
    with pytest.raises(ValueError, match="CLASSIFICATION"):  # only a model response can be rejected
        ledger.settle(res["id"], {"reservation_id": res["id"]}, 41, failure="RESPONSE_REJECTED")


# ---- export_v03.py ----

PV, PV_UP = "arxiv:2101.00001v1", "arxiv:2102.00001v1"
DELTA = "delta:" + "d" * 64
RUN = make_manifest(MANIFEST["corpus_id"], [DELTA], created_at=T0)


def claim(n, pv=PV, kind="theorem"):
    return {"id": hexid("claim", n), "content_sha256": S, "origin": "PAPER_VERSION", "paper_version_id": pv,
            "occurrence_ids": [hexid("occ", n)], "part": "whole", "occurrence_kind": kind}


def junction(n, conclusion, derivation, legs, method="DETERMINISTIC_ANCHOR"):
    return {"id": hexid("junction", n), "content_sha256": S, "conclusion_id": conclusion, "derivation_id": derivation,
            "reading_method": method, "method_version": "v1", "grouping_basis": "SYNTHETIC",
            "legs": [{"premise_id": p, "role": role, "use_site": site, "flags": list(flags)} for p, role, site, *flags in legs]}


A, B, C, D, E, F, Z = (hexid("claim", n) for n in (1, 2, 3, 4, 5, 6, 9))
R, R2 = hexid("placeholder", 1), hexid("placeholder", 2)
REQUEST = {"id": R, "content_sha256": S, "kind": "EXTERNAL_REQUEST", "paper_version_id": PV, "created_by_claim_id": A,
           "citing_derivation_id": "unlocated:MODEL_EXTRACTION:0", "bib_entry_id": hexid("bib", 1)}
PROOF, UNLOCATED = "proof:" + S, "unlocated:MODEL_EXTRACTION:0"
NODES = [claim(1), claim(2), claim(3), claim(4, kind="definition"), claim(5, PV_UP), claim(6), claim(9), REQUEST]
JUNCTIONS = [
    junction(1, A, "statement", [(D, "DEFINITION_DEPENDENCY", "STATEMENT")]),
    junction(2, A, PROOF, [(B, "UNCLASSIFIED", "PROOF")]),
    junction(3, A, PROOF, [(C, "SCOPE_DEPENDENCY", "PROOF")], method="MODEL_EXTRACTION"),
    junction(4, A, UNLOCATED, [(R, "SCIENTIFIC_CLAIM_DEPENDENCY", "UNKNOWN")], method="MODEL_EXTRACTION"),
    junction(5, R, f"source:{PV_UP}:{S}", [(E, "SCIENTIFIC_CLAIM_DEPENDENCY", "UNKNOWN")], method="MODEL_MATCH"),
    junction(6, Z, PROOF, [(A, "PROOF_DEPENDENCY", "PROOF")]),
    junction(7, A, PROOF, [(F, "PROOF_DEPENDENCY", "PROOF", "EXPANDED_TO_PARTS")]),
]
NOMINATION = {"kind": "FoundationNomination", "contract_version": "0.4.0", "nomination_id": hexid("nomination", 1),
              "policy_id": POLICY["policy_id"], "manifest_id": RUN["manifest_id"], "rule": "FOUNDATION_V1",
              "list": "THEOREM_LIKE", "subject_kind": "CLAIM", "subject_id": A, "count_basis": "SAMPLE_ONLY",
              "rank_interval": {"lower": 1, "upper": 1}, "dependent_papers": {"lower": 3, "upper": 4},
              "dependent_topics": {"lower": 1, "upper": 1},
              "date": {"value": "2021", "kind": "ARXIV_V1", "precision": "YEAR", "source": "synthetic"},
              "layer": 1, "layer_basis": ["PRIMITIVE"], "witness_paths": [[A]], "blockers": [], "next_action": "LIBRARY_AUDIT",
              "match_coverage": None, "bootstrap_top_k_fraction": None,
              "edge_precision_top_k_survival": None}
INCLUDES = [{"id": hexid("rel", n), "content_sha256": S, "type": "INCLUDES", "start_id": MANIFEST["corpus_id"], "end_id": pv,
             "props": {"admission": admission, "round": n, "sampling_record_id": hexid("sampling", n)}}
            for n, pv, admission in ((0, PV, "SAMPLE"), (1, PV_UP, "EXPANSION"))]


def export(nomination=NOMINATION, nodes=NODES, junctions=JUNCTIONS, run=RUN, **policy):
    """export_v03 on a merged DeltaSetView of one synthetic delta."""
    view = {"deltas": [DELTA], "nodes": {label: {} for label in LABELS}, "edges": {e["id"]: e for e in INCLUDES}}
    for row in nodes + junctions:
        label = {"junction": "Junction", "placeholder": "Placeholder"}.get(row["id"].split(":")[0], "Claim")
        view["nodes"][label][row["id"]] = {**row, "asserted_by": [DELTA],
                                           "methods": [row.get("reading_method", "DETERMINISTIC_ANCHOR")]}
    return export_v03.export_v03(nomination, view, run, {**POLICY, **policy}, {})


def summary(out):
    return {(g["target"], tuple(g["members"])): g["relation"] for g in out["graph"]["support_groups"]}


def test_export_joins_readings_and_statement_and_v03_prune_accepts_it():
    out = export(traverse="ALL_ADMITTED", count_basis="ALL_ADMITTED")
    graph, record = out["graph"], out["record"]
    assert [n["id"] for n in graph["nodes"]] == sorted({A, B, C, D, E, R})
    assert summary(out) == {(A, tuple(sorted({B, C, D}))): "DEFINITION_DEPENDENCY",  # UNCLASSIFIED ranks last (§10)
                            (A, tuple(sorted({D, R}))): "SCIENTIFIC_CLAIM_DEPENDENCY", (R, (E,)): "SCIENTIFIC_CLAIM_DEPENDENCY"}
    assert export_v03._relation(["UNCLASSIFIED"]) == "PROOF_DEPENDENCY"
    assert sorted(map(sorted, record["groups"].values())) == sorted(
        [sorted(hexid("junction", n) for n in (1, 2, 3)), sorted(hexid("junction", n) for n in (1, 4)), [hexid("junction", 5)]])
    assert sum(len(loss["legs"]) for loss in record["losses"]) == 6
    assert {(leg["premise_id"], leg["position"], leg["use_site"]) for loss in record["losses"] for leg in loss["legs"]} >= {
        (D, 0, "STATEMENT"), (B, 0, "PROOF")}
    assert (record["policy_sha256"], record["manifest_id"]) == (digest(canonical({**POLICY, "traverse": "ALL_ADMITTED",
                                                                                   "count_basis": "ALL_ADMITTED"})),
                                                                RUN["manifest_id"])
    request = next(n for n in graph["nodes"] if n["id"] == R)
    assert request["kind"] == "external_claim_request" and request["blocked_by"] == ["EXTERNAL_CLAIM_REQUEST:" + R]
    assert record["graph_sha256"] == digest(canonical(graph))
    pruned = v03_graph.prune_graph(graph["nodes"], graph["support_groups"], record["query_ids"])
    assert set(pruned["selected_node_ids"]) <= {A, B, C, D, E, R} and A in pruned["selected_node_ids"]
    assert all(root["upstream_search"] == "FRONTIER" for root in pruned["roots"])


def test_export_follows_the_nomination_policy():
    assert E not in {n["id"] for n in export()["graph"]["nodes"]}  # traverse SAMPLE_ONLY: PV_UP is EXPANSION-only
    parts = export(traverse="ALL_ADMITTED", count_basis="ALL_ADMITTED", include_part_expansions=True)
    assert summary(parts)[A, tuple(sorted({B, C, D, F}))] == "PROOF_DEPENDENCY"
    assert summary(export(establishment_reading={"mode": "ONLY", "methods": ["DETERMINISTIC_ANCHOR"]})) == {
        (A, tuple(sorted({B, D}))): "DEFINITION_DEPENDENCY"}
    grouped = [n for n in NODES if n["id"] != R] + [{**REQUEST, "citation_group": "anchor:1"},
                                                     {**REQUEST, "id": R2, "bib_entry_id": hexid("bib", 2), "citation_group": "anchor:1"}]
    cited = JUNCTIONS[:3] + [junction(4, A, UNLOCATED, [(R, "SCIENTIFIC_CLAIM_DEPENDENCY", "UNKNOWN"),
                                                        (R2, "SCIENTIFIC_CLAIM_DEPENDENCY", "UNKNOWN")], method="MODEL_EXTRACTION")]
    assert (A, tuple(sorted({D, R, R2}))) in summary(export(nodes=grouped, junctions=cited))
    with pytest.raises(ValueError, match="OR_CITATION_GROUP_UNSUPPORTED"):
        export(nodes=grouped, junctions=cited, citation_group_semantics="OR")


OTHER = make_manifest(MANIFEST["corpus_id"], ["delta:" + "e" * 64], created_at=T0)


def test_export_keeps_cycles_for_v03_and_refuses_works_and_other_runs():
    out = export(junctions=JUNCTIONS + [junction(8, B, PROOF, [(C, "PROOF_DEPENDENCY", "PROOF")]),
                                        junction(9, C, PROOF, [(B, "PROOF_DEPENDENCY", "PROOF")])])
    pruned = v03_graph.prune_graph(out["graph"]["nodes"], out["graph"]["support_groups"], out["record"]["query_ids"])
    assert any({B, C} <= set(scc["members"]) for scc in pruned["sccs"])
    for kwargs, code in (({"nomination": {**NOMINATION, "list": "WORKS", "subject_kind": "WORK", "subject_id": hexid("work", 1)}},
                          "CLAIM_SUBJECT"),
                         ({"nomination": {**NOMINATION, "subject_id": E}}, "OUTSIDE_POLICY_SCOPE"),
                         ({"policy_id": hexid("policy", 2)}, "NOT_THE_NOMINATION_RUN"),
                         ({"run": OTHER, "nomination": {**NOMINATION, "manifest_id": OTHER["manifest_id"]}},
                          "NOT_THE_NOMINATION_RUN")):  # the view is not the merge of that manifest's deltas
        with pytest.raises(ValueError, match=code):
            export(**kwargs)
    with pytest.raises(TypeError):  # dispositions are required: a signed closure is never exported as unsigned
        export_v03.export_v03(NOMINATION, {}, RUN, POLICY)


def test_mimo_profile_routes_the_v04_operations_and_keeps_v03_ones_on_their_models():
    policy = routing.freeze_model_routing_v2(routing.MIMO_PROFILE)
    ops = policy["operations"]
    assert set(ops) == set(v03_routing.OPERATION_CLASSES) | V04_OPERATIONS
    assert (ops["paper.extract_focus"]["model"], ops["paper.extract_focus"]["effort"]) == ("mimo-v2.6-flash", "thinking-enabled")
    assert ops["leg.judge"]["model"] == "mimo-v2.6-pro" and ops["paper.extract"]["model"] == "gpt-5.6-luna"
    assert ops["paper.extract_focus"]["training_cutoff"]["value"] == "UNKNOWN" and "mimo.mi.com" in ops["paper.extract_focus"]["training_cutoff"]["source"]
    assert policy["profile_source_sha256"] != routing.freeze_model_routing_v2()["profile_source_sha256"]
    for op in V04_OPERATIONS:
        contracts.validate("ModelSelectionV4", routing.select_model_route(policy, op, ops[op]["engine_class"]))
    bad = copy.deepcopy(policy)
    bad["operations"]["paper.extract_focus"]["effort"] = "medium"  # a MiMo route names a thinking mode, not an effort
    with pytest.raises(ValueError, match="ROUTE_INVALID"):
        routing.validate_policy(rehash(bad))


def test_ledger_schedules_judge_and_discovery_calls_as_model_items(tmp_path):
    ledger = open_ledger(tmp_path)
    judge = ledger.add("EVAL", "JUDGE_CARD", "card:" + "a" * 64, "MODEL_JUDGE", "leg.judge/v1", S)
    search = ledger.add("S1", "DISCOVERY_QUERY", "query-1", "MODEL_SEARCH", "corpus.discover/v1", S)
    with pytest.raises(ValueError, match="ARGUMENTS_INVALID"):  # a model item names its provider window
        ledger.reserve(judge, 0)
    res = ledger.reserve(judge, 0, **CALL)
    assert ledger.settle(res["id"], {"reservation_id": res["id"]}, 1, cost=0.25) == "DONE"
    assert ledger.item(search)["method"] == "MODEL_SEARCH" and ledger.spent() == 0.25
    with pytest.raises(ValueError, match="KEY_INVALID"):
        ledger.add("EVAL", "JUDGE_CARD", "card:x", "MODEL_GUESS", "v1", S)


def test_discovery_round_examines_model_proposals_in_seeded_order():
    sample = corpus.sample_record(MANIFEST, FRAME, outcomes_until(MANIFEST, FRAME), T0)
    seen = sample["candidates"][0]["arxiv_base_id"]
    proposed = ["2301.00005", "2301.00001", "not-an-id", 17, "2301.00001", seen, "2301.00003", "2301.00002"]
    discovery = {"operation": "corpus.discover", "queries_sha256": S, "receipts": [], "M": 3}
    selected, counts = corpus.discovery_selection(MANIFEST, [sample], proposed, discovery)
    seed = corpus.discovery_seed(MANIFEST, 1)
    assert seed == "sample-seed/discovery/1"
    assert counts == {"proposed": 8, "dropped_invalid": 2, "duplicates": 1, "dropped_seen": 1, "not_selected": 1, "seed": seed}
    assert sum(counts[k] for k in ("dropped_invalid", "duplicates", "dropped_seen", "not_selected")) + len(selected) == 8
    fresh = ["2301.00001", "2301.00002", "2301.00003", "2301.00005"]
    assert [x["arxiv_base_id"] for x in selected] == [x["arxiv_base_id"] for x in corpus.order_frame(fresh, seed)][:3]
    with pytest.raises(ValueError, match="HOST_DERIVED"):  # a seed chosen after seeing the proposals would choose the papers
        corpus.discovery_record(MANIFEST, [sample], {**discovery, "seed": "chosen"}, proposed, {}, T0)
    outcomes = {x["arxiv_base_id"]: {"outcome": "ACCEPTED", "attempts": 1, "paper_version_id": f"arxiv:{x['arxiv_base_id']}v1"}
                for x in selected}
    first = selected[0]["arxiv_base_id"]
    outcomes[first] = {"outcome": "UNDETERMINED", "attempts": 1, "undetermined_class": "ID_NOT_FOUND"}
    record = corpus.discovery_record(MANIFEST, [sample], discovery, proposed, outcomes, T0)
    assert (record["round"], record["admission"], record["discovery"]["proposed"]) == (1, "DISCOVERY", 8)
    assert record["discovery"]["seed"] == seed and record["discovery"]["duplicates"] == 1
    assert all(row["order_key"] == corpus.order_key(seed, row["arxiv_base_id"]) for row in record["candidates"])
    with pytest.raises(ValueError, match="NOT_THE_SELECTION"):
        corpus.discovery_record(MANIFEST, [sample], discovery, proposed, {first: outcomes[first]}, T0)
    with pytest.raises(ValueError, match="OUTSIDE_P"):
        corpus.estimand_counts(record)
    date = {"value": "2023-01-01", "kind": "ARXIV_V1", "precision": "DAY", "source": "snapshot"}
    meta = {row["paper_version_id"]: {"primary_category": "hep-th", "categories": ["hep-th"], "redistribution": "UNKNOWN",
                                      "date_v1": date, "date_version": date, "source_sha256": S}
            for row in record["candidates"] if row["outcome"] == "ACCEPTED"}
    s1 = corpus.includes_delta(record, MANIFEST, meta)
    assert {e["props"]["admission"] for e in s1["edges"] if e["type"] == "INCLUDES"} == {"DISCOVERY"}
    again = corpus.expansion_record(MANIFEST, [sample, record], EXPANSION, [work(9, "2401.00001")],
                                    {"2401.00001": {"outcome": "INELIGIBLE", "attempts": 1, "reason": "no derivation"}}, T0)
    assert again["round"] == 2  # rounds are numbered across expansion and discovery


def test_coverage_report_accounts_every_accepted_paper_of_every_round():
    sample = corpus.sample_record(MANIFEST, FRAME, outcomes_until(MANIFEST, FRAME), T0)
    accepted = [row["paper_version_id"] for row in sample["candidates"] if row["outcome"] == "ACCEPTED"]
    plan = {pv: [f"{pv}#0", f"{pv}#1"] for pv in accepted[:-1]}  # the last accepted paper has no planned item
    item = lambda state, dispatchable=False: {"state": state, "dispatchable": dispatchable}
    items = {key: item("DONE") for keys in plan.values() for key in keys}
    items[plan[accepted[0]][1]] = item("FAILED")
    items[plan[accepted[1]][0]] = item("QUOTA_WAIT", True)  # may still get its one re-attempt
    items[plan[accepted[2]][0]] = item("QUOTA_WAIT")  # its re-attempt is used: terminal
    items[plan[accepted[3]][0]] = item("ABANDONED")  # an expired lease: terminal
    items[plan[accepted[4]][0]] = item("SKIPPED")  # one item skipped, one done: the paper is done
    items[plan[accepted[5]][0]] = item("RUNNING")
    report = corpus.coverage_report(MANIFEST, [sample], plan, items)
    assert report["by_status"] == {"DONE": 54, "FAILED": 3, "INCOMPLETE": 2, "MISSING": 1} and not report["complete"]
    assert report["failed"] == sorted(accepted[i] for i in (0, 2, 3))
    assert report["incomplete"] == sorted([accepted[1], accepted[5], accepted[-1]])
    assert report["by_admission"] == {"SAMPLE": 60} and report["extraction"] == MANIFEST["extraction"]
    assert report["corpus_id"] == MANIFEST["corpus_id"] and report["policy"] == "EQUAL_FULL"
    plan[accepted[-1]] = ["last#0"]
    items.update({"last#0": item("DONE"), plan[accepted[1]][0]: item("DONE"), plan[accepted[5]][0]: item("FAILED")})
    done = corpus.coverage_report(MANIFEST, [sample], plan, items)
    assert done["complete"] and done["by_status"]["FAILED"] == 4  # a failed paper stays in the denominators
    with pytest.raises(ValueError, match="NOT_ACCEPTED"):
        corpus.coverage_report(MANIFEST, [sample], {**plan, "arxiv:2999.00001v1": ["x"]}, {**items, "x": item("DONE")})
    with pytest.raises(ValueError, match="PRIOR_ROUNDS_INCOMPLETE"):  # every round of the corpus, starting with SAMPLE
        corpus.coverage_report(MANIFEST, [], {}, {})
