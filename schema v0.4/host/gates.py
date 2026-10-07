"""Automatic gates (spec §11): the rules pre-registered in CorpusManifest.gates at S0, applied to recorded
measurements. A GateDecision says what runs next; it never states anything about a claim (I-10).

P_MINUS_1 (S5, no model): sampling outcomes and the S1-S4 graph -> GO, GO_WITH_EXPANSION (the sample shares too few
cited works for claim-level analysis, so acquire the cited works first) or NO_GO (the frame yields too few eligible or
too many undetermined papers). P0 (after the pilot): an AUTO_EVAL_V1 report and a cost projection -> GO for the full
run iff the corpus extraction method version is admitted and the projection covers the run, rests on measured inputs,
fits the context window and is under the budget ceiling. The gate recomputes every precision row under the manifest's
rule rather than trusting a stored decision, and checks that each input is the unedited record its id names. The
PRIMARY analysis policy is then derived from the manifest's frozen template by keeping only admitted importance methods.
"""
from __future__ import annotations

from collections import Counter, defaultdict

import autoeval
import contracts
from corpus import CONTRACT_VERSION, check_corpus_manifest, estimand_counts
from delta import address
from invariants import admitted, work_components
from review_sample import stratum_key

YIELD_FIELDS = ("theorem_like_environments", "owned_proofs", "proof_owned_anchors", "junction_bearing_conclusions")
ANCHOR_METHOD = "DETERMINISTIC_ANCHOR"


def _addressed(row, kind, id_field):
    """Refuse a record whose id is not the digest of its content (it was edited after it was made)."""
    if row[id_field] != address(kind, {k: v for k, v in row.items() if k not in (id_field, "created_at")}):
        raise ValueError(f"{id_field.upper()}_IS_NOT_THE_DIGEST_OF_ITS_CONTENT")
    return row


def _decision(manifest, gate, inputs, measured, rule, decision, reasons, admitted_methods, created_at):
    body = {"kind": "GateDecision", "contract_version": CONTRACT_VERSION, "gate": gate, "corpus_id": manifest["corpus_id"],
            "inputs": sorted(set(inputs)), "measured": measured, "rule": rule, "decision": decision, "reasons": reasons,
            "admitted_methods": sorted(admitted_methods)}
    row = {**body, "gate_id": address("gate", body), "created_at": created_at}
    contracts.validate("GateDecision", row)
    return row


def _work(view):
    """The host-rule work identity (EXPLICIT_IDS_ONLY): a work is the least id of its SAME_WORK component."""
    comps = work_components(view, "EXPLICIT_IDS_ONLY")
    return lambda w: min(comps.get(w, {w}))


def works_cited(view, papers, work=None):
    """({work: citing papers}, {work: papers citing it inside an owned proof}) over the given paper versions. In-proof
    citations are the EXTERNAL_REQUEST rows the DETERMINISTIC_ANCHOR pass asserted (a \\cite inside an owned proof),
    not requests a model proposed."""
    work = work or _work(view)
    nodes, edges = view["nodes"], view["edges"].values()
    resolves = defaultdict(set)
    for e in edges:
        if e["type"] == "RESOLVES_TO" and admitted(e, "EXPLICIT_IDS_ONLY", ()):
            resolves[e["start_id"]].add(work(e["end_id"]))
    cited, in_proof = defaultdict(set), defaultdict(set)
    for b in nodes["BibEntry"].values():
        if b["paper_version_id"] in papers:
            for w in resolves[b["id"]]:
                cited[w].add(b["paper_version_id"])
    for h in nodes["Placeholder"].values():
        if h["kind"] == "EXTERNAL_REQUEST" and h["paper_version_id"] in papers and ANCHOR_METHOD in h.get("methods", ()):
            for w in resolves[h["bib_entry_id"]]:
                in_proof[w].add(h["paper_version_id"])
    return cited, in_proof


def p_minus_1(manifest, sample_record, view, s3_deltas, created_at, *, grid=None):
    """The P_MINUS_1 GateDecision from the SAMPLE round, the merged S1-S4 view and the S3 anchor deltas. Yields count
    only the DETERMINISTIC_ANCHOR S3 delta of each sample paper that the view includes (two for one paper raise).
    grid: an optional eligibility.grid result, reported as eligible_fraction[k=..,m=..] beside the decision."""
    check_corpus_manifest(manifest)
    contracts.validate("SamplingRecord", sample_record)
    if sample_record["corpus_id"] != manifest["corpus_id"]:
        raise ValueError("SAMPLING_RECORD_OF_ANOTHER_CORPUS")
    rule, counts = manifest["gates"]["P_MINUS_1"], estimand_counts(sample_record)
    determinable = counts["accepted"] + counts["ineligible"]
    undetermined = sum(counts["undetermined"].values())
    sample = {row["paper_version_id"] for row in sample_record["candidates"] if row["outcome"] == "ACCEPTED"}
    work = _work(view)
    cited, in_proof = works_cited(view, sample, work)
    own_works = {work(e["end_id"]) for e in view["edges"].values() if e["type"] == "VERSION_OF" and e["start_id"] in sample}
    resolved = [w for w, ps in cited.items() for _ in ps]
    need = rule["claim_level"]
    included, anchor_deltas = set(view["deltas"]), {}
    for d in s3_deltas:
        contracts.validate("GraphDelta", d)
        if d["stage"] != "S3" or d["method"] != ANCHOR_METHOD or d["delta_id"] not in included or d["subject"]["id"] not in sample:
            continue
        if d["subject"]["id"] in anchor_deltas and anchor_deltas[d["subject"]["id"]]["delta_id"] != d["delta_id"]:
            raise ValueError("TWO_ANCHOR_DELTAS_FOR: " + d["subject"]["id"])
        anchor_deltas[d["subject"]["id"]] = d
    yields = {f: sum(d.get("measurements", {}).get("deterministic_yield", {}).get(f, 0) for d in anchor_deltas.values())
              for f in YIELD_FIELDS}
    measured = {"examined": counts["examined"], "accepted": counts["accepted"], "ineligible": counts["ineligible"],
                "undetermined": undetermined,
                "eligible_fraction": counts["accepted"] / determinable if determinable else None,
                "undetermined_fraction": undetermined / counts["examined"] if counts["examined"] else None,
                "cited_works": len(cited), "works_meeting_claim_level": sum(len(ps) >= need["min_citing_papers"] for ps in cited.values()),
                "works_cited_in_proofs": len(in_proof),
                "works_cited_in_proofs_meeting_claim_level": sum(len(ps) >= need["min_citing_papers"] for ps in in_proof.values()),
                "in_sample_citation_fraction": sum(w in own_works for w in resolved) / len(resolved) if resolved else None,
                "papers_with_anchor_delta": len(anchor_deltas),
                **{"yield_" + f: v for f, v in yields.items()},
                **{f"eligible_fraction[{key}]": value for key, value in sorted((grid or {}).items())}}
    reasons = []
    if measured["eligible_fraction"] is None or measured["eligible_fraction"] < rule["min_eligible_fraction"]:
        reasons.append(f"eligible fraction {measured['eligible_fraction']} < {rule['min_eligible_fraction']}")
    if measured["undetermined_fraction"] is None or measured["undetermined_fraction"] > rule["max_undetermined_fraction"]:
        reasons.append(f"undetermined fraction {measured['undetermined_fraction']} > {rule['max_undetermined_fraction']}")
    if reasons:
        decision = "NO_GO"
    elif measured["works_meeting_claim_level"] >= need["min_works"]:
        decision, reasons = "GO", [f"{measured['works_meeting_claim_level']} works cited by >= {need['min_citing_papers']} sample papers"]
    else:
        decision = "GO_WITH_EXPANSION"
        reasons = [f"{measured['works_meeting_claim_level']} works cited by >= {need['min_citing_papers']} sample papers < "
                   f"{need['min_works']}: acquire cited works (EXPANSION) or discover related papers (DISCOVERY) before claim-level analysis"]
    return _decision(manifest, "P_MINUS_1", [sample_record["sampling_record_id"], *view["deltas"]], measured, rule, decision,
                     reasons, [], created_at)


def _precision_rows(plan, report, samples, rule):
    """The report's precision rows with their decisions recomputed under rule (autoeval.recheck), after checking that
    the samples are exactly the report's precision inputs, drawn under the plan, and that every stratum of every
    sample has exactly one row with its item count."""
    by_id = {}
    for s in samples:
        contracts.validate("ReviewSample", s)
        _addressed(s, "review-sample", "sample_id")
        if s["evaluation_plan_id"] != plan["plan_id"] or s["estimand"] not in autoeval.PRECISION_OPERATION:
            raise ValueError("P0_SAMPLE_IS_NOT_A_PRECISION_SAMPLE_OF_THE_PLAN: " + s["sample_id"])
        by_id[s["sample_id"]] = s
    if sorted(by_id) != sorted(report["inputs"]["samples"]):
        raise ValueError("P0_SAMPLES_ARE_NOT_THE_REPORT_INPUTS")
    expected = Counter((sid, stratum_key(item.get("stratum"))) for sid, s in by_id.items() for item in s["items"])
    rows = report["precision"]
    keys = [(row["sample_id"], stratum_key(row["stratum"])) for row in rows]
    if len(set(keys)) != len(keys) or set(keys) != set(expected) or any(row["items"] != expected[k] for row, k in zip(rows, keys)):
        raise ValueError("P0_PRECISION_ROWS_DO_NOT_COVER_EVERY_STRATUM_ONCE")
    if any(by_id[row["sample_id"]]["estimand"] != row["estimand"] for row in rows):
        raise ValueError("P0_PRECISION_ROW_OF_ANOTHER_ESTIMAND")
    return [(row, autoeval.recheck(row, rule)) for row in rows]


def p0(manifest, plan, report, projection, samples, created_at):
    """The P0 GateDecision from the plan, its report, the report's precision samples and a cost projection.

    Refused (ValueError) when an input is not the unedited record its id names, belongs to another corpus or plan, or
    does not recompute. GO iff: the corpus extraction method_version has MODEL_EXTRACTION strata and every one is ADMIT
    (strata of other versions, e.g. a comparison arm, admit nothing); the projection is of the corpus extraction and of
    a model whose extraction the plan judged, against the manifest's ceiling, over at least target_size papers of
    MEASURED size, with no ESTIMATED parameter, under the ceiling and inside the context window; and a judge model is
    independent of the producers. admitted_methods bound the PRIMARY importance methods."""
    check_corpus_manifest(manifest)
    for name, row, kind, key in (("EvaluationPlan", plan, "eval-plan", "plan_id"), ("EvaluationReport", report, "eval-report", "report_id"),
                                 ("CostProjection", projection, "cost", "projection_id")):
        contracts.validate(name, row)
        _addressed(row, kind, key)
    if (plan["corpus_id"] != manifest["corpus_id"] or projection["corpus_id"] != manifest["corpus_id"]
            or report["plan_id"] != plan["plan_id"] or report["manifest_id"] != plan["manifest_id"]):
        raise ValueError("P0_INPUTS_OF_ANOTHER_CORPUS_OR_PLAN")
    if projection["operation"] != manifest["extraction"]["operation"]:
        raise ValueError("PROJECTION_IS_NOT_OF_THE_CORPUS_EXTRACTION")
    if projection["model"] not in plan["producers"].get("leg.judge", ()):
        raise ValueError("PROJECTION_MODEL_WAS_NOT_JUDGED_BY_THE_PLAN: " + projection["model"])
    ceiling = manifest["budget_ceiling"]
    if ((projection["ceiling"]["unit"], projection["ceiling"]["value"]) != (ceiling["unit"], ceiling["value"])
            or ceiling.get("pricing_profile_sha256", projection["pricing_profile_sha256"]) != projection["pricing_profile_sha256"]):
        raise ValueError("PROJECTION_IS_NOT_AGAINST_THE_MANIFEST_CEILING")
    rule, version = manifest["gates"]["P0"], manifest["extraction"]["method_version"]
    rows = _precision_rows(plan, report, samples, rule)
    by_method = defaultdict(list)
    for row, decision in rows:
        s = row["stratum"]
        if s["method"] == "MODEL_EXTRACTION" and s["method_version"] != version:
            continue  # another extraction version (a comparison arm of the pilot) admits nothing
        by_method[s["method"]].append(decision)
    admitted_methods = {m for m, ds in by_method.items() if all(d == "ADMIT" for d in ds)} | set(autoeval.NON_MODEL_METHODS)
    lower = [row["lower_bound"] for row, _ in rows if row["stratum"]["method"] == "MODEL_EXTRACTION" and row["stratum"]["method_version"] == version]
    estimated = sorted(k for k, v in projection["parameters"].items() if v["label"] == "ESTIMATED")
    measured = {"extraction_admitted": "MODEL_EXTRACTION" in admitted_methods, "match_admitted": "MODEL_MATCH" in admitted_methods,
                "extraction_strata": len(lower),
                "extraction_min_lower_bound": min((x for x in lower if x is not None), default=None),
                "projected_papers": projection["papers"], "target_size": manifest["target_size"],
                "sizes_measured": projection["source_bytes"]["label"] == "MEASURED", "estimated_parameters": len(estimated),
                "projected_cost": projection["totals"]["cost"], "projected_in_ceiling_unit": projection["ceiling"]["projected"],
                "under_ceiling": projection["under_ceiling"], "fits_context": projection["fits_context"],
                "distinct_judge_model": report["independence"]["distinct_model_present"]}
    checks = ((measured["extraction_admitted"], f"MODEL_EXTRACTION {version} is not admitted by AUTO_EVAL_V1"),
              (projection["papers"] >= manifest["target_size"],
               f"the projection covers {projection['papers']} papers < target_size {manifest['target_size']}"),
              (measured["sizes_measured"], "the projection uses ESTIMATED source sizes"),
              (not estimated, "the projection uses ESTIMATED parameters: " + ", ".join(estimated)),
              (measured["under_ceiling"], "the cost projection exceeds the budget ceiling"),
              (measured["fits_context"], "the largest prompt does not fit the context window"),
              (measured["distinct_judge_model"], "no judge model is independent of the producers"))
    reasons = [text for ok, text in checks if not ok]
    decision = "NO_GO" if reasons else "GO"
    if not measured["match_admitted"]:
        reasons.append("MODEL_MATCH is not admitted: S7 legs stay out of importance counts")
    inputs = [plan["plan_id"], report["report_id"], projection["projection_id"], *report["inputs"]["samples"]]
    return _decision(manifest, "P0", inputs, measured, rule, decision, reasons or ["every P0 condition holds"],
                     admitted_methods, created_at)


def primary_policy(manifest, gate):
    """The PRIMARY AnalysisPolicy of the full run: the manifest's frozen template with importance_methods cut to the
    methods the P0 gate admitted and admission_gate naming it (a new policy_id). The gate must be an unedited P0 GO of
    this corpus under the manifest's P0 rule."""
    check_corpus_manifest(manifest)
    contracts.validate("GateDecision", gate)
    _addressed(gate, "gate", "gate_id")
    if (gate["gate"], gate["decision"], gate["corpus_id"]) != ("P0", "GO", manifest["corpus_id"]) or gate["rule"] != manifest["gates"]["P0"]:
        raise ValueError("PRIMARY_POLICY_NEEDS_A_P0_GO_OF_THIS_CORPUS")
    template = manifest["primary_analysis_policy"]
    methods = sorted(set(template["importance_methods"]) & set(gate["admitted_methods"]))
    if not methods:
        raise ValueError("NO_ADMITTED_IMPORTANCE_METHOD")
    body = {k: v for k, v in template.items() if k != "policy_id"} | {"importance_methods": methods, "admission_gate": gate["gate_id"]}
    policy = {**body, "policy_id": address("policy", body)}
    contracts.validate("AnalysisPolicy", policy)
    return policy


def require_equal_coverage(coverage, corpus):
    """Refuse a PRIMARY analysis unless the coverage report (corpus.coverage_report) is of this corpus and its
    EQUAL_FULL extraction policy and no accepted paper lacks its S6 attempts."""
    if (coverage.get("corpus_id"), coverage.get("policy"), coverage.get("extraction")) != (
            corpus["corpus_id"], corpus["coverage"], corpus["extraction"]):
        raise ValueError("COVERAGE_REPORT_OF_ANOTHER_CORPUS_OR_EXTRACTION")
    if not coverage["complete"]:
        raise ValueError(f"EQUAL_FULL_COVERAGE_INCOMPLETE: {len(coverage['incomplete'])} papers, first {coverage['incomplete'][:3]}")
    return coverage
