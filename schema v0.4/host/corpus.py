"""Corpus manifest, seeded sampling order, candidate outcomes, expansion and discovery rounds, and the EQUAL_FULL
coverage account (§6).

Everything is a pure function of its arguments; records are content-addressed and checked against the contracts.
There is no prioritized arm (§6.4): every accepted paper of every round receives the manifest's one S6 policy.
"""
from __future__ import annotations

import hashlib
from collections import Counter

import contracts
import ids
from delta import address

CONTRACT_VERSION = "0.4.0"
_HOST_FIELDS = {"kind", "contract_version", "corpus_id"}
_OUTCOME_FIELD = {"ACCEPTED": "paper_version_id", "INELIGIBLE": "reason", "UNDETERMINED": "undetermined_class"}


def freeze_corpus_manifest(fields):
    """S0: fields are every CorpusManifest field except the host-set kind, contract_version and corpus_id."""
    if _HOST_FIELDS & set(fields):
        raise ValueError("CORPUS_MANIFEST_HOST_FIELD_SUPPLIED")
    body = {"kind": "CorpusManifest", "contract_version": CONTRACT_VERSION, **fields}
    return check_corpus_manifest({**body, "corpus_id": address("corpus", body)})


def check_corpus_manifest(manifest):
    """A frozen manifest: valid under the contract and still named by the digest of everything else in it."""
    contracts.validate("CorpusManifest", manifest)
    if manifest["corpus_id"] != address("corpus", {k: v for k, v in manifest.items() if k != "corpus_id"}):
        raise ValueError("CORPUS_ID_IS_NOT_THE_MANIFEST_DIGEST")
    return manifest


def order_key(seed, arxiv_base_id):
    """§6.2: sha256(seed_utf8 || 0x00 || arxiv_base_id), hex."""
    return hashlib.sha256(seed.encode() + b"\x00" + arxiv_base_id.encode()).hexdigest()


def order_frame(frame_ids, seed):
    """The frame in examination order, drawn without replacement: [{arxiv_base_id, order_key}]."""
    frame_ids = list(frame_ids)
    if len(set(frame_ids)) != len(frame_ids):
        raise ValueError("FRAME_HAS_DUPLICATE_IDS")
    if not all(contracts.validator("ArxivBaseId").is_valid(item) for item in frame_ids):
        raise ValueError("FRAME_ID_NOT_ARXIV_BASE_ID")
    return sorted(({"arxiv_base_id": item, "order_key": order_key(seed, item)} for item in frame_ids),
                  key=lambda item: (item["order_key"], item["arxiv_base_id"]))


def _candidate(manifest, base, result, **host):
    """One outcome per examined candidate; attempts beyond the first are TRANSIENT_NETWORK retries only.

    result carries outcome, attempts and only its outcome's own field; arxiv_base_id and order_key are host-set."""
    if not isinstance(result, dict) or set(result) - {"outcome", "attempts", _OUTCOME_FIELD.get(result.get("outcome"))}:
        raise ValueError("OUTCOME_FIELDS_INVALID: " + base)
    row, limit = {**result, "arxiv_base_id": base, **host}, manifest["transient_retry_limit"]
    attempts, version = row.get("attempts"), row.get("paper_version_id")
    if type(attempts) is not int or not 1 <= attempts <= 1 + limit:
        raise ValueError("ATTEMPTS_OUTSIDE_RETRY_LIMIT: " + base)
    if row.get("undetermined_class") == "TRANSIENT_NETWORK" and attempts != 1 + limit:
        raise ValueError("TRANSIENT_RETRIES_NOT_EXHAUSTED: " + base)
    if version is not None and not (isinstance(version, str) and version.startswith(f"arxiv:{base}v")):
        raise ValueError("PAPER_VERSION_OF_ANOTHER_BASE_ID: " + base)
    return row


def _record(manifest, body):
    body = {"kind": "SamplingRecord", "contract_version": CONTRACT_VERSION, "corpus_id": manifest["corpus_id"], **body}
    record = {**body, "sampling_record_id": address("sampling", body)}
    contracts.validate("SamplingRecord", record)
    return record


def sample_record(manifest, frame_ids, outcomes, created_at):
    """Round 0: examine the ordered frame until target_size are ACCEPTED; accepted papers are never replaced.

    outcomes maps each examined base id to {outcome, attempts, paper_version_id? reason? undetermined_class?}.
    """
    check_corpus_manifest(manifest)
    candidates, accepted = [], []
    for item in order_frame(frame_ids, manifest["seed"]):
        if len(accepted) == manifest["target_size"]:
            break
        base = item["arxiv_base_id"]
        if base not in outcomes:
            raise ValueError("CANDIDATE_NOT_EXAMINED_IN_ORDER: " + base)
        candidates.append(_candidate(manifest, base, outcomes[base], order_key=item["order_key"]))
        if candidates[-1]["outcome"] == "ACCEPTED":
            accepted.append(base)
    if set(outcomes) - {row["arxiv_base_id"] for row in candidates}:
        raise ValueError("OUTCOME_OUTSIDE_EXAMINED_PREFIX")
    return _record(manifest, {"round": 0, "admission": "SAMPLE", "candidates": candidates, "created_at": created_at})


def _prior(manifest, prior):
    """(next round number, every base id examined so far) of a complete prior-round list starting with SAMPLE."""
    check_corpus_manifest(manifest)
    for record in prior:
        contracts.validate("SamplingRecord", record)
    rounds = sorted((record["round"], record["admission"]) for record in prior)
    if (any(record["corpus_id"] != manifest["corpus_id"] for record in prior) or not rounds
            or [r for r, _ in rounds] != list(range(len(rounds))) or rounds[0][1] != "SAMPLE"):
        raise ValueError("PRIOR_ROUNDS_INCOMPLETE")
    return len(rounds), {row["arxiv_base_id"] for record in prior for row in record["candidates"]}


def expansion_record(manifest, prior, expansion, works, outcomes, created_at):
    """§6.3: one bounded round over at most expansion.M nominated works that have an arXiv source.

    prior: every earlier SamplingRecord of this corpus; works: Work rows in selection-rule order.
    """
    next_round, seen = _prior(manifest, prior)
    if len(works) > expansion["M"]:
        raise ValueError("EXPANSION_EXCEEDS_M")
    candidates = []
    for work in works:
        contracts.validate("WorkNode", work)
        base = work.get("arxiv_base_id")
        if work["terminal_kind"] != "ARXIV_SOURCE_AVAILABLE" or base is None:
            raise ValueError("WORK_NOT_EXPANDABLE_NEEDS_LIBRARY_AUDIT_OR_HUMAN_REVIEW: " + work["id"])
        if base in seen or base not in outcomes:
            raise ValueError("EXPANSION_CANDIDATE_REPEATED_OR_UNEXAMINED: " + base)
        seen.add(base)
        candidates.append(_candidate(manifest, base, outcomes[base]))
    if set(outcomes) - {row["arxiv_base_id"] for row in candidates}:
        raise ValueError("OUTCOME_FOR_UNSELECTED_WORK")
    return _record(manifest, {"round": next_round, "admission": "EXPANSION", "expansion": expansion,
                              "candidates": candidates, "created_at": created_at})


def discovery_seed(manifest, round_number):
    """The seed of a DISCOVERY round, derived by the host so it cannot be chosen after the proposals are seen."""
    return f"{manifest['seed']}/discovery/{round_number}"


def discovery_selection(manifest, prior, proposed_ids, discovery):
    """§6.3 DISCOVERY: the ids a model search proposed, as the host examines them. Malformed ids, repeats and ids of
    earlier rounds are dropped; the rest are ordered by order_key(discovery_seed, id) and cut to M. Returns (selected
    [{arxiv_base_id, order_key}], counts {proposed, dropped_invalid, duplicates, dropped_seen, not_selected, seed}), with
    proposed = dropped_invalid + duplicates + dropped_seen + not_selected + len(selected). Nothing is admitted here:
    every selected id is still acquired and checked for eligibility like a sampled one (I-0)."""
    next_round, seen = _prior(manifest, prior)
    valid = contracts.validator("ArxivBaseId").is_valid
    proposed = list(proposed_ids)
    well_formed = [item for item in proposed if isinstance(item, str) and valid(item)]
    unique = sorted(set(well_formed))
    fresh = [item for item in unique if item not in seen]
    seed = discovery_seed(manifest, next_round)
    selected = order_frame(fresh, seed)[:discovery["M"]]
    counts = {"proposed": len(proposed), "dropped_invalid": len(proposed) - len(well_formed),
              "duplicates": len(well_formed) - len(unique), "dropped_seen": len(unique) - len(fresh),
              "not_selected": len(fresh) - len(selected), "seed": seed}
    return selected, counts


def discovery_record(manifest, prior, discovery, proposed_ids, outcomes, created_at):
    """One DISCOVERY round (§6.3): discovery = {operation, queries_sha256, receipts, M}; the host adds the counts and the
    derived seed. outcomes maps every selected base id to its examined outcome. Discovery papers are never in P."""
    if "seed" in discovery:
        raise ValueError("DISCOVERY_SEED_IS_HOST_DERIVED")
    next_round, _ = _prior(manifest, prior)
    selected, counts = discovery_selection(manifest, prior, proposed_ids, discovery)
    if set(outcomes) != {item["arxiv_base_id"] for item in selected}:
        raise ValueError("DISCOVERY_OUTCOMES_ARE_NOT_THE_SELECTION")
    candidates = [_candidate(manifest, item["arxiv_base_id"], outcomes[item["arxiv_base_id"]], order_key=item["order_key"])
                  for item in selected]
    return _record(manifest, {"round": next_round, "admission": "DISCOVERY", "discovery": {**discovery, **counts},
                              "candidates": candidates, "created_at": created_at})


def includes_delta(record, manifest, metadata, *, produced_by=()):
    """S1 acquisition (HOST_RULE) delta of one SamplingRecord: the PaperVersion row and INCLUDES (Corpus →
    PaperVersion) {admission, round, sampling_record_id} of every ACCEPTED candidate. metadata maps each accepted
    paper version id to its frozen PaperVersion fields except id, content_sha256, arxiv_base_id, version and
    parser_sha256 (= the manifest's eligibility.parser_sha256). S3 and later deltas take this one as a parent and
    never re-assert PaperVersion, so an accepted paper that fails S3 keeps its row and INCLUDES endpoint."""
    contracts.validate("SamplingRecord", record)
    if check_corpus_manifest(manifest)["corpus_id"] != record["corpus_id"]:
        raise ValueError("SAMPLING_RECORD_OF_ANOTHER_CORPUS")
    accepted = [row["paper_version_id"] for row in record["candidates"] if row["outcome"] == "ACCEPTED"]
    if set(metadata) != set(accepted):
        raise ValueError("METADATA_IS_NOT_THE_ACCEPTED_PAPERS")
    if any({"id", "content_sha256", "arxiv_base_id", "version", "parser_sha256"} & set(metadata[pv]) for pv in accepted):
        raise ValueError("METADATA_HOST_FIELD_SUPPLIED")
    parser = manifest["eligibility"]["parser_sha256"]
    rows = [ids.seal("PaperVersion", {**metadata[pv], **dict(zip(("arxiv_base_id", "version"), ids.paper_version_parts(pv))),
                                      "parser_sha256": parser}) for pv in accepted]
    props = {"admission": record["admission"], "round": record["round"], "sampling_record_id": record["sampling_record_id"]}
    edges = [ids.edge("INCLUDES", record["corpus_id"], pv, props) for pv in accepted]
    return ids.make_delta("S1", "HOST_RULE", "corpus-" + CONTRACT_VERSION, ("MANIFEST", record["sampling_record_id"]),
                          {"PaperVersion": rows}, edges, produced_by=produced_by)


def estimand_counts(record):
    """§6.2: counts every statistic over P = frame ∩ determinable ∩ eligible reports; SAMPLE rounds only."""
    if record["admission"] != "SAMPLE":
        raise ValueError("EXPANSION_AND_DISCOVERY_ARE_OUTSIDE_P")
    rows = record["candidates"]
    outcomes = Counter(row["outcome"] for row in rows)
    return {"examined": len(rows), "accepted": outcomes["ACCEPTED"], "ineligible": outcomes["INELIGIBLE"],
            "undetermined": dict(sorted(Counter(row["undetermined_class"] for row in rows
                                                if row["outcome"] == "UNDETERMINED").items()))}


def _terminal(item):
    """A ledger item that can receive no further attempt: DONE, FAILED, SKIPPED, ABANDONED (an expired lease), or a
    READY or QUOTA_WAIT item that reserve() would refuse (its one quota re-attempt or its attempts are used up);
    ledger.CorpusLedger.item gives state and dispatchable. RUNNING and unregistered items are not terminal."""
    state = (item or {}).get("state")
    return state in ("DONE", "FAILED", "SKIPPED", "ABANDONED") or (state in ("READY", "QUOTA_WAIT") and not item["dispatchable"])


def coverage_report(manifest, records, plan, items):
    """§6.4 EQUAL_FULL account of S6: every ACCEPTED paper of every round against its planned S6 work items (S7 is
    accounted per nomination as match_coverage).

    records: every SamplingRecord of the corpus (a complete round list starting with SAMPLE); plan maps each paper
    version id to the ledger keys of its S6 items under the manifest's extraction policy (one per focus or claim
    batch); items maps each key to its ledger item ({state, dispatchable}; a key without one has not been registered).
    A paper is DONE when every item is DONE or SKIPPED and one is DONE; FAILED when every item is terminal and one is
    not DONE or SKIPPED (the paper stays in every denominator with missing data); INCOMPLETE otherwise; MISSING with no
    planned item. complete is true iff nothing is INCOMPLETE or MISSING."""
    _prior(manifest, list(records))
    accepted = {}
    for record in records:
        for row in record["candidates"]:
            if row["outcome"] == "ACCEPTED":
                accepted[row["paper_version_id"]] = record["admission"]
    if set(plan) - accepted.keys():
        raise ValueError("PLAN_NAMES_A_PAPER_THAT_WAS_NOT_ACCEPTED")
    papers = {}
    for pv in sorted(accepted):
        seen = [items.get(key) for key in plan.get(pv, [])]
        states = [(item or {}).get("state") for item in seen]
        papers[pv] = ("MISSING" if not seen else "INCOMPLETE" if not all(_terminal(item) for item in seen) else
                      "DONE" if set(states) <= {"DONE", "SKIPPED"} and "DONE" in states else "FAILED")
    by = Counter(papers.values())
    return {"corpus_id": manifest["corpus_id"], "policy": manifest["coverage"], "extraction": manifest["extraction"], "papers": len(papers),
            "by_status": {k: by[k] for k in ("DONE", "FAILED", "INCOMPLETE", "MISSING")},
            "by_admission": dict(sorted(Counter(accepted.values()).items())),
            "failed": sorted(p for p, s in papers.items() if s == "FAILED"),
            "incomplete": sorted(p for p, s in papers.items() if s in ("INCOMPLETE", "MISSING")),
            "complete": not (by["INCOMPLETE"] or by["MISSING"])}
