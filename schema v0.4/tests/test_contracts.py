"""v0.4 contracts: metaschema, offline v0.3 $ref resolution, one valid and one invalid synthetic row per $def."""
import copy
import json

import pytest
from jsonschema import Draft202012Validator, ValidationError

import contracts

H, S = "a" * 64, "sha256:" + "a" * 64
PV_ID = "arxiv:2101.00001v2"


def ident(prefix):
    return f"{prefix}:{H}"


def edit(base, *drop, **changes):
    row = copy.deepcopy(base)
    for key in drop:
        row.pop(key)
    return {**row, **changes}


def deep(base, path, value):
    row = copy.deepcopy(base)
    target = row
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return row


SPAN = {"artifact": "src/main.tex", "source_sha256": S, "start_byte": 0, "end_byte": 9, "span_sha256": S,
        "line_start": 1, "line_end": 1}
REF = {"path": "artifacts/x.json", "sha256": S, "byte_size": 3}
DATE = {"value": "2021-01-04", "kind": "ARXIV_V1", "precision": "DAY", "source": "oai-pmh snapshot"}
EXT = {"arxiv_id": None, "doi": "10.1103/PhysRevA.1", "openalex_id": None, "resolution_basis": "HOST_RULE_ARXIV_DOI",
       "evidence": []}
SELECTION = {"policy_version": "operation-routing-v2", "policy_sha256": S, "operation": "paper.extract_local",
             "profile": "light", "engine_class": "LIGHT", "model": "gpt-5.6-luna", "effort": "low", "reason": "local batch",
             "training_cutoff": {"value": "UNKNOWN", "source": "provider page not frozen"}}
PAPER = {"id": PV_ID, "content_sha256": S, "arxiv_base_id": "2101.00001", "version": 2, "primary_category": "quant-ph",
         "categories": ["quant-ph"], "redistribution": "RESTRICTED", "date_v1": DATE,
         "date_version": {**DATE, "kind": "ARXIV_VERSION"}, "source_sha256": S, "parser_sha256": S}
YIELD = {"theorem_like_environments": 3, "owned_proofs": 2, "proof_owned_anchors": 4, "junction_bearing_conclusions": 2}
WORK = {"id": ident("work"), "content_sha256": S, "identity_basis": "DOI", "doi": "10.1103/physreva.1",
        "work_kind": "ARTICLE", "terminal_kind": "PREARXIV_DOI_NO_SOURCE"}
BIB = {"id": ident("bib"), "content_sha256": S, "paper_version_id": PV_ID, "citation_key": "NC00", "locator": SPAN,
       "identifiers": EXT}
CLAIM = {"id": ident("claim"), "content_sha256": S, "origin": "PAPER_VERSION", "paper_version_id": PV_ID,
         "occurrence_ids": [ident("occ")], "part": "whole", "locator": SPAN}
WORK_CLAIM = {"id": ident("claim"), "content_sha256": S, "origin": "WORK_LOCATOR", "work_id": ident("work"),
              "occurrence_ids": [], "part": "whole", "work_locator_text": "Nielsen-Chuang Thm 10.1, p. 437"}
READING = {"id": ident("reading"), "content_sha256": S, "claim_id": ident("claim"), "method": "MODEL_EXTRACTION",
           "method_version": "1", "kind": "lemma", "statement_sha256": S, "conditions_sha256": S,
           "display_text_class": "NONE", "confidence": {"value": 0.5, "source": "SELF_REPORTED", "calibration_ref": None}}
LEG = {"premise_id": ident("placeholder"), "role": "UNCLASSIFIED", "use_site": "PROOF", "flags": []}
JUNCTION = {"id": ident("junction"), "content_sha256": S, "conclusion_id": ident("claim"),
            "derivation_id": "proof:" + S, "reading_method": "DETERMINISTIC_ANCHOR", "method_version": "1",
            "legs": [LEG], "grouping_basis": "PROOF_SPAN"}
REQUEST = {"id": ident("placeholder"), "content_sha256": S, "kind": "EXTERNAL_REQUEST", "paper_version_id": PV_ID,
           "created_by_claim_id": ident("claim"), "citing_derivation_id": "proof:" + S, "bib_entry_id": ident("bib"),
           "citation_group": "anchor-1", "locator_text": "Theorem 3.2"}
UNRESOLVED = {"id": ident("placeholder"), "content_sha256": S, "kind": "UNRESOLVED_OCCURRENCE", "paper_version_id": PV_ID,
              "created_by_claim_id": ident("claim"), "citing_derivation_id": "statement", "occurrence_id": ident("occ"),
              "reason": "NON_ENVIRONMENT_TARGET"}
PRIMITIVE = {"id": ident("primitive"), "content_sha256": S, "claim_id": ident("claim"), "method": "HUMAN", "basis": "AXIOM"}
EDGE = {"id": ident("rel"), "content_sha256": S, "type": "INCLUDES", "start_id": ident("corpus"), "end_id": PV_ID,
        "props": {"admission": "SAMPLE", "round": 0, "sampling_record_id": ident("sampling")}}
DELTA = {"kind": "GraphDelta", "contract_version": "0.4.0", "delta_id": ident("delta"), "stage": "S3",
         "method": "DETERMINISTIC_ANCHOR", "method_version": "1", "subject": {"kind": "PAPER_VERSION", "id": PV_ID},
         "parents": [], "produced_by": [REF],
         "nodes": {"Claim": [CLAIM], "Junction": [JUNCTION], "Placeholder": [REQUEST]},
         "edges": [{**EDGE, "type": "STATES", "start_id": PV_ID, "end_id": ident("claim"), "props": {}}],
         "issues": [{"id": "i1", "code": "AMBIGUOUS_PART", "subject": ident("claim"), "detail": "two claims, one locator"}]}
MANIFEST = {"kind": "DeltaSetManifest", "manifest_id": ident("manifest"), "corpus_id": ident("corpus"),
            "deltas": [ident("delta")], "excluded": [], "created_at": "2026-09-25T00:00:00Z"}
PROJECTION = {"id": ident("projection"), "content_sha256": S, "delta_set_digest": S, "review_set_digest": S,
              "state": "READY", "loader_version": "0.4.0", "audit_counts": {"G1": 0}}
POLICY = {"kind": "AnalysisPolicy", "contract_version": "0.4.0", "policy_id": ident("policy"), "status": "PRIMARY",
          "establishment_reading": {"mode": "UNION"}, "importance_methods": ["DETERMINISTIC_ANCHOR"],
          "work_identity": "EXPLICIT_IDS_ONLY", "citation_group_semantics": "AND", "cycle_policy": "FIXPOINT",
          "base_set": "ALL_ROOTS", "include_part_expansions": False, "traverse": "ALL_ADMITTED", "count_basis": "SAMPLE_ONLY",
          "admission_gate": None, "nomination": {"rule": "FOUNDATION_V1", "threshold": 3, "top_k": 50},
          "bootstrap": {"scheme": "PAPER_REWEIGHT_V1", "replicates": 200, "seed": "s"}, "edge_precision": None}
GATES = {"P_MINUS_1": {"min_eligible_fraction": 0.3, "max_undetermined_fraction": 0.2,
                       "claim_level": {"min_works": 20, "min_citing_papers": 3}},
         "P0": {"admission_threshold": 0.85, "fpr_inflation": 2.0, "alpha": 0.05, "max_unresolved_fraction": 0.2,
                "min_items": 100, "require_projection_under_ceiling": True}}
CORPUS = {"kind": "CorpusManifest", "contract_version": "0.4.0", "corpus_id": ident("corpus"),
          "field": {"primary_categories": ["quant-ph"], "date_window": {"start": "2015-01-01", "end": "2025-12-31"}},
          "sampling_frame": {"kind": "OAI_PMH_ARXIVRAW", "sha256": S, "snapshot_date": "2026-09-01"},
          "eligibility": {"rule": "THEOREM_OR_DERIVATION_V1", "params": {"min_theorem_like": 1, "min_display_equations": 10},
                          "program_sha256": S, "parser_sha256": S},
          "size_limits": {"max_bytes": 1}, "version_rule": "LATEST_ON_OR_BEFORE_SNAPSHOT", "seed": "seed",
          "target_size": 1000, "transient_retry_limit": 3, "coverage": "EQUAL_FULL",
          "extraction": {"operation": "paper.extract_focus", "method_version": "focus-1", "focus_bytes": 8192}, "gates": GATES,
          "primary_analysis_policy": POLICY, "budget_ceiling": {"unit": "USD", "value": 2500, "pricing_profile_sha256": S},
          "created_at": "2026-09-25T00:00:00Z"}
SAMPLING = {"kind": "SamplingRecord", "contract_version": "0.4.0", "sampling_record_id": ident("sampling"),
            "corpus_id": ident("corpus"), "round": 0, "admission": "SAMPLE",
            "candidates": [{"arxiv_base_id": "2101.00001", "order_key": H, "outcome": "ACCEPTED", "attempts": 1,
                            "paper_version_id": PV_ID},
                           {"arxiv_base_id": "quant-ph/9705052", "order_key": H, "outcome": "UNDETERMINED", "attempts": 3,
                            "undetermined_class": "TRANSIENT_NETWORK"}],
            "created_at": "2026-09-25T00:00:00Z"}
EXPANSION = edit(SAMPLING, round=1, admission="EXPANSION",
                 candidates=[{"arxiv_base_id": "2101.00002", "outcome": "INELIGIBLE", "attempts": 1, "reason": "k=0"}],
                 expansion={"source_manifest_id": ident("manifest"), "selection_rule": "top-M works",
                            "analysis_run": {"policy_id": ident("policy"), "manifest_id": ident("manifest")}, "M": 5})
DISCOVERY = edit(SAMPLING, round=2, admission="DISCOVERY",
                 candidates=[{"arxiv_base_id": "2101.00003", "order_key": H, "outcome": "UNDETERMINED", "attempts": 1,
                              "undetermined_class": "ID_NOT_FOUND"}],
                 discovery={"operation": "corpus.discover", "queries_sha256": S, "receipts": [REF], "proposed": 5,
                            "dropped_invalid": 1, "duplicates": 1, "dropped_seen": 2, "not_selected": 0, "M": 10,
                            "seed": "seed/discovery/2"})
BRACKET = {"lower": 1, "upper": 2}
METRICS = {"kind": "NodeMetrics", "contract_version": "0.4.0", "policy_id": ident("policy"), "manifest_id": ident("manifest"),
           "subject_kind": "CLAIM", "subject_id": ident("claim"), "count_basis": "SAMPLE_ONLY", "layer": 1,
           "layer_basis": ["PRIMITIVE"], "route_status": "FINITE", "in_cycle": False, "dependent_papers": BRACKET,
           "dependent_papers_by_depth": {"1": BRACKET, "2": BRACKET, "3": BRACKET},
           "dependents": {"lower": 3, "upper": 4, "exactness": "ESTIMATED"},
           "necessary_dependents": {"ALL_ROOTS": BRACKET, "PRIMITIVE_ASSERTED": None}, "direct_uses": 2, "date": DATE,
           "root_class": None, "root_examined_by": [],
           "uncertainty": [{"method": "DETERMINISTIC_ANCHOR", "role": "UNCLASSIFIED", "disposition": "CANDIDATE", "legs": 2}]}
WORK_METRICS = {"kind": "NodeMetrics", "contract_version": "0.4.0", "policy_id": ident("policy"),
                "manifest_id": ident("manifest"), "subject_kind": "WORK", "subject_id": ident("work"),
                "count_basis": "ALL_ADMITTED", "layer": "UNRESOLVED", "layer_basis": [], "dependent_papers": BRACKET,
                "dependent_topics": BRACKET,
                "dependent_papers_by_depth": {"1": BRACKET, "2": BRACKET, "3": BRACKET},
                "dependents": {"lower": 3, "upper": 4, "exactness": "EXACT"}, "date": DATE, "citing_claims": 4,
                "citing_papers": 3}
NOMINATION = {"kind": "FoundationNomination", "contract_version": "0.4.0", "nomination_id": ident("nomination"),
              "policy_id": ident("policy"), "manifest_id": ident("manifest"), "rule": "FOUNDATION_V1", "list": "WORKS",
              "subject_kind": "WORK", "subject_id": ident("work"), "count_basis": "SAMPLE_ONLY",
              "rank_interval": {"lower": 1, "upper": 2}, "dependent_papers": BRACKET, "dependent_topics": BRACKET, "date": DATE,
              "layer": "UNRESOLVED",
              "layer_basis": [], "witness_paths": [[ident("claim"), ident("junction"), ident("placeholder")]],
              "blockers": ["EXTERNAL_REQUEST_UNRESOLVED"], "next_action": "LIBRARY_AUDIT", "match_coverage": 0.5,
              "bootstrap_top_k_fraction": None, "edge_precision_top_k_survival": None}
REVIEW_SAMPLE = {"kind": "ReviewSample", "contract_version": "0.4.0", "sample_id": ident("review-sample"),
                 "manifest_id": ident("manifest"), "estimand": "LEG_PRECISION", "arm": "RANDOM", "seed": "s",
                 "label_source": "AUTO_PANEL", "evaluation_plan_id": ident("eval-plan"),
                 "labelling_guide": REF, "labeller_count": 2, "relabel_of": None,
                 "items": [{"subject_kind": "LEG", "subject_id": ident("rel"), "inclusion_probability": 0.25,
                            "stratum": {"method": "MODEL_EXTRACTION", "method_version": "focus-1", "role": "PROOF_DEPENDENCY",
                                        "use_site": "PROOF"}}],
                 "created_at": "2026-09-25T00:00:00Z"}
REVIEW = {"kind": "HumanReview", "subject_kind": "JUNCTION", "subject_id": ident("junction"), "subject_sha256": S,
          "decision": "ACCEPT", "reviewer": "reviewer", "basis": "read the proof", "reviewed_at": "2026-09-25"}
RATE = {"successes": 3, "n": 100, "estimate": 0.03, "lower": 0.01, "upper": 0.085, "z": 1.96}
STRATUM = {"method": "MODEL_EXTRACTION", "method_version": "focus-1", "role": "UNCLASSIFIED", "use_site": "UNKNOWN"}
MATCH_STRATUM = {"method": "MODEL_MATCH", "method_version": "match-1"}
ROUTE_A = {**SELECTION, "operation": "leg.judge", "engine_class": "DECISION", "model": "mimo-v2.6-pro", "effort": "thinking-enabled"}
ROUTE_B = {**SELECTION, "operation": "leg.judge", "engine_class": "DECISION", "model": "gpt-5.6-terra", "effort": "medium"}
PLAN = {"kind": "EvaluationPlan", "contract_version": "0.4.0", "plan_id": ident("eval-plan"), "corpus_id": ident("corpus"),
        "manifest_id": ident("manifest"), "scheme": "AUTO_EVAL_V1", "estimands": ["LEG_PRECISION"],
        "sample": {"per_stratum": 100, "seed": "s"},
        "controls": {"positive": {"rule": "ANCHOR_IN_OWNED_PROOF_V1", "count": 100},
                     "negative": {"rules": ["SAME_PAPER_NEAR_MISS_V1", "OTHER_PAPER_DECOY_V1"], "count_per_rule": 150}, "seed": "c"},
        "panel": [{"judge_id": "mimo-pro", "route": ROUTE_A, "instruction_sha256": S},
                  {"judge_id": "terra", "route": ROUTE_B, "instruction_sha256": S}],
        "decision_rule": "UNANIMOUS_VALID_USED", "blinding": "METHOD_AND_CONTROL_HIDDEN", "producers": {"leg.judge": ["mimo-v2.6-flash"]},
        "created_at": "2026-09-25T00:00:00Z"}
JUDGEMENT = {"kind": "Judgement", "contract_version": "0.4.0", "judgement_id": ident("judgement"), "plan_id": ident("eval-plan"),
             "judge_id": "terra", "card_id": ident("card"), "card_sha256": S, "verdict": "USED", "validity": "VALID",
             "evidence": {"byte_start": 3, "byte_end": 9, "span_sha256": S, "extended": False}, "receipt": REF}
ESTIMATE = {"estimand": "LEG_PRECISION", "sample_id": ident("review-sample"),
            "stratum": STRATUM, "items": 100, "unresolved": 4,
            "panel_positive": {**RATE, "successes": 92, "estimate": 0.92, "lower": 0.85, "upper": 0.96}, "false_positive": RATE,
            "false_positive_by_rule": {"SAME_PAPER_NEAR_MISS_V1": RATE, "OTHER_PAPER_DECOY_V1": {**RATE, "successes": 1, "upper": 0.05}},
            "sensitivity": None, "fpr_inflation": 2.0, "lower_bound": 0.7, "point": None,
            "gate": {"threshold": 0.85, "decision": "REJECT", "reason": "lower bound 0.700 vs threshold 0.85"}}
RECALL = {"estimand": "LEG_RECALL", "basis": "ANCHOR_REFERENCED_V1", "method": "MODEL_EXTRACTION/focus-1",
          "versus": "DETERMINISTIC_ANCHOR", "rate": RATE, "estimate": 0.03, "counts": {"anchored": 100, "found": 3},
          "assumption": "premises referenced by label only"}
REPORT = {"kind": "EvaluationReport", "contract_version": "0.4.0", "report_id": ident("eval-report"), "plan_id": ident("eval-plan"),
          "manifest_id": ident("manifest"), "label_source": "AUTO_PANEL",
          "independence": {"judge_models": {"leg.judge": ["gpt-5.6-terra", "mimo-v2.6-pro"]}, "producers": {"leg.judge": ["mimo-v2.6-flash"]},
                           "distinct_model_present": True},
          "inputs": {"samples": [ident("review-sample")], "cards_sha256": S, "judgements_sha256": S,
                     "controls": {"LEG_PRECISION": {"positive": 100, "negative_by_rule": {"SAME_PAPER_NEAR_MISS_V1": 150,
                                                                                         "OTHER_PAPER_DECOY_V1": 150}, "skipped": 3}}},
          "precision": [ESTIMATE], "recall": [RECALL], "assumptions": ["decoys are unused"], "human_audit": None,
          "created_at": "2026-09-25T00:00:00Z"}
GATE = {"kind": "GateDecision", "contract_version": "0.4.0", "gate_id": ident("gate"), "gate": "P0", "corpus_id": ident("corpus"),
        "inputs": [ident("eval-report")], "measured": {"extraction_admitted": True, "projected_cost": 612.5, "extraction_min_lower_bound": None},
        "rule": GATES["P0"], "decision": "GO", "reasons": ["every P0 condition holds"], "admitted_methods": ["HUMAN", "MODEL_EXTRACTION"],
        "created_at": "2026-09-25T00:00:00Z"}
PRICES = {"cache_hit": 0.0028, "cache_miss": 0.14, "output": 0.28}
PRICING = {"kind": "PricingProfile", "provider": "MiMo", "source_url": "https://mimo.mi.com/docs/en-US/price/pay-as-you-go",
           "page_updated": "2026-09-22", "retrieved": "2026-09-25", "currency": "USD", "unit": "PER_MILLION_TOKENS",
           "models": {"mimo-v2.6-flash": {"realtime": PRICES, "batch": {"cache_hit": 0.0014, "cache_miss": 0.07, "output": 0.14},
                                          "limits": {"rpm": 100, "tpm": 10000000, "context_window": 1000000, "max_output": 131072,
                                                     "batch_completion_minutes": 1440}}},
           "notes": []}
COST = {"kind": "CostProjection", "contract_version": "0.4.0", "projection_id": ident("cost"), "corpus_id": ident("corpus"),
        "pricing_profile_sha256": S, "model": "mimo-v2.6-flash", "mode": "batch", "operation": "paper.extract_focus", "papers": 10000,
        "source_bytes": {"mean": 153000.0, "rms": 178000.0, "max": 333351, "label": "ESTIMATED"},
        "paper_plans": "MODELLED",
        "parameters": {"tokens_per_byte": {"value": 0.4, "label": "MEASURED", "source": "receipts"},
                       "output_reserve_tokens": {"value": 32768, "label": "POLICY", "source": "host choice"}},
        "totals": {"calls": 139000.0, "input_tokens": 1.2e10, "cached_input_tokens": 1.0e10, "output_tokens": 1.1e9, "cost": 322.0},
        "currency": "USD", "wallclock_minutes": 1440.0, "wallclock_basis": "BATCH_COMPLETION_WINDOW", "largest_prompt_tokens": 142000.0,
        "fits_context": True,
        "ceiling": {"unit": "USD", "value": 2500, "projected": 322.0, "other_stages": 500.0, "already_spent": 12.5,
                    "basis": "S7 and judge calls from the pilot, times the corpus size"},
        "under_ceiling": True, "created_at": "2026-09-25T00:00:00Z"}

ID_DEFS = {"WorkId": "work", "BibEntryId": "bib", "OccurrenceId": "occ", "ClaimId": "claim", "ReadingId": "reading",
           "JunctionId": "junction", "PlaceholderId": "placeholder", "PrimitiveId": "primitive", "RelId": "rel",
           "DeltaId": "delta", "ManifestId": "manifest", "CorpusId": "corpus", "ProjectionId": "projection",
           "PolicyId": "policy", "SamplingRecordId": "sampling", "NominationId": "nomination",
           "ReviewSampleId": "review-sample", "EvaluationPlanId": "eval-plan", "JudgementId": "judgement", "CardId": "card",
           "EvaluationReportId": "eval-report", "GateId": "gate", "CostProjectionId": "cost"}
VALID = {
    "Stratum": [STRATUM, MATCH_STRATUM],
    **{name: [ident(prefix)] for name, prefix in ID_DEFS.items()},
    "Sha256": [S], "HexKey": [H], "IsoDate": ["2026-09-25"], "PartialDate": ["2026", "2026-09", "2026-09-25"],
    "ArxivBaseId": ["2101.00001", "quant-ph/9705052", "math.AG/0101001"],
    "PaperVersionId": [PV_ID, "arxiv:quant-ph/9705052v1"], "LogicalId": [ident("claim"), ident("placeholder")],
    "DerivationId": ["statement", "proof:" + S, "unlocated:MODEL_EXTRACTION:0", f"source:{PV_ID}:{S}"],
    "Method": ["HUMAN"], "LegRole": ["UNCLASSIFIED"], "UseSite": ["STATEMENT"], "Admission": ["SAMPLE", "DISCOVERY"],
    "CountBasis": ["SAMPLE_ONLY", "ALL_ADMITTED"], "Rate": [RATE, {"successes": 0, "n": 0, "estimate": None, "lower": 0, "upper": 1, "z": 1.96}],
    "TokenPrices": [PRICES],
    "RootClass": ["WORK_LOCATOR"], "Layer": [0, "INFINITY", "UNRESOLVED"], "Bracket": [BRACKET], "EdgeType": ["INCLUDES"],
    "DateValue": [DATE, {"value": None, "kind": "UNKNOWN", "precision": "UNKNOWN", "source": "none"},
                  {"value": "1995", "kind": "BIB_YEAR", "precision": "YEAR", "source": "bib"}],
    "ExternalIdentifierV4": [EXT, {**EXT, "resolution_basis": "UNRESOLVED", "doi": None}],
    "ModelSelectionV4": [SELECTION, {**SELECTION, "operation": "dependency.match_retrieved", "engine_class": "DECISION",
                                     "model": "gpt-5.6-terra", "training_cutoff": {"value": "2025-06", "source": "card"}},
                         {**SELECTION, "operation": "paper.extract_focus", "model": "mimo-v2.6-flash", "effort": "thinking-enabled"},
                         {**SELECTION, "operation": "corpus.discover", "model": "mimo-v2.6-flash", "effort": "thinking-disabled"},
                         ROUTE_A, ROUTE_B, {**ROUTE_A, "operation": "match.judge"}],
    "PaperVersionNode": [PAPER, {**PAPER, "title": "T", "license": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/"}],
    "WorkNode": [WORK, edit(WORK, "doi", identity_basis="BIB_DIGEST", bib_digest=S, work_kind="BOOK", terminal_kind="MONOGRAPH")],
    "BibEntryNode": [BIB], "ClaimNode": [CLAIM, WORK_CLAIM],
    "ClaimReadingNode": [READING, {**READING, "display_text_class": "PARAPHRASE", "display_text": "every x has y"}],
    "JunctionNode": [JUNCTION,
                     {**JUNCTION, "derivation_id": "statement", "legs": [{**LEG, "use_site": "STATEMENT"}]},
                     {**JUNCTION, "conclusion_id": ident("placeholder"), "derivation_id": f"source:{PV_ID}:{S}",
                      "legs": [{**LEG, "premise_id": ident("claim"), "flags": ["EXPANDED_TO_PARTS"]}]}],
    "PlaceholderNode": [REQUEST, UNRESOLVED], "PrimitiveAssertionNode": [PRIMITIVE],
    "Edge": [EDGE, {**EDGE, "type": "PREMISE_OF", "start_id": ident("claim"), "end_id": ident("junction"),
                    "props": {"position": 0, "role": "UNCLASSIFIED", "use_site": "PROOF"}},
             {**EDGE, "type": "SAME_WORK", "start_id": ident("work"), "end_id": ident("work"), "props": {"basis": "HUMAN"}}],
    "GraphDelta": [DELTA, {**DELTA, "measurements": {"deterministic_yield": YIELD}},
                   {**DELTA, "stage": "HUMAN_ENTRY", "method": "HUMAN", "nodes": {"PrimitiveAssertion": [PRIMITIVE]}, "edges": []},
                   {**DELTA, "stage": "LIBRARY_AUDIT", "method": "LIBRARY", "nodes": {"Claim": [WORK_CLAIM]}, "edges": []}],
    "DeltaSetManifest": [MANIFEST, {**MANIFEST, "parent_manifest_id": ident("manifest"),
                                                          "excluded": [{"delta_id": ident("delta"), "reason": "superseded"}]}],
    "ProjectionManifest": [PROJECTION], "AnalysisPolicy": [POLICY, {**POLICY, "status": "EXPLORATORY",
                                                                   "establishment_reading": {"mode": "ONLY", "methods": ["HUMAN"]},
                                                                   "edge_precision": {"scheme": "EDGE_PRECISION_V1", "estimates": REF}},
                                                          {**POLICY, "admission_gate": ident("gate"), "traverse": "SAMPLE_ONLY"}],
    "CorpusManifest": [CORPUS, {**CORPUS, "extraction": {"operation": "paper.extract_local", "method_version": "local-1", "prose_bytes": 2048},
                                "budget_ceiling": {"unit": "calls", "value": 5}}],
    "SamplingRecord": [SAMPLING, EXPANSION, DISCOVERY], "NodeMetrics": [METRICS, WORK_METRICS],
    "FoundationNomination": [NOMINATION, {**NOMINATION, "list": "DEFINITIONS", "subject_kind": "CLAIM",
                                          "subject_id": ident("claim"), "layer": 0, "next_action": "EXTRACT"}],
    "ReviewSample": [REVIEW_SAMPLE, {**REVIEW_SAMPLE, "label_source": "HUMAN", "evaluation_plan_id": None, "labeller_count": 1},
                     {**REVIEW_SAMPLE, "estimand": "MATCH_PRECISION",
                      "items": [{"subject_kind": "JUNCTION", "subject_id": ident("junction"), "inclusion_probability": 1, "stratum": MATCH_STRATUM}]}],
    "HumanReviewV4": [REVIEW, {**REVIEW, "subject_kind": "SUPPORT_GROUP"}],
    "EvaluationPlan": [PLAN, {**PLAN, "estimands": ["LEG_PRECISION", "MATCH_PRECISION"], "controls": deep(PLAN, ["controls", "positive", "count"], 0)["controls"],
                              "producers": {"leg.judge": ["mimo-v2.6-flash"], "match.judge": ["gpt-5.6-terra"]}}],
    "Judgement": [JUDGEMENT, {**JUDGEMENT, "verdict": "NOT_USED", "evidence": None},
                  {**JUDGEMENT, "validity": "EVIDENCE_UNBOUND", "evidence": None},
                  {**JUDGEMENT, "validity": "RESPONSE_INVALID", "verdict": "CANNOT_TELL", "evidence": None}],
    "PrecisionEstimate": [ESTIMATE, {**ESTIMATE, "estimand": "MATCH_PRECISION", "stratum": MATCH_STRATUM, "lower_bound": None,
                                     "gate": {"threshold": 0.85, "decision": "NOT_ESTIMABLE", "reason": "no negative control"}}],
    "RecallEstimate": [RECALL, {**RECALL, "estimand": "LOCAL_VS_WHOLE_RECALL", "basis": "CAPTURE_RECAPTURE_CHAPMAN_V1", "rate": None,
                                "versus": "MODEL_EXTRACTION/local-1", "estimate": None}],
    "EvaluationReport": [REPORT, {**REPORT, "human_audit": {"sample_id": ident("review-sample"), "agreement": RATE}}],
    "GateDecision": [GATE, {**GATE, "gate": "P_MINUS_1", "decision": "GO_WITH_EXPANSION", "admitted_methods": [], "rule": GATES["P_MINUS_1"]}],
    "PricingProfile": [PRICING, deep(PRICING, ["models", "mimo-v2.6-flash", "batch"], None),
                       deep(PRICING, ["models", "mimo-v2.6-flash", "limits"], edit(PRICING["models"]["mimo-v2.6-flash"]["limits"], "batch_completion_minutes"))],
    "CostProjection": [COST, {**COST, "ceiling": {**COST["ceiling"], "unit": "calls", "value": 10, "projected": 139000.0}, "under_ceiling": False},
                       {**COST, "mode": "realtime", "wallclock_basis": "REALTIME_RATE_LIMITS", "paper_plans": "MEASURED"}],
}
INVALID = {
    **{name: [ident(prefix)[:-1], "x:" + H, ident(prefix).upper()] for name, prefix in ID_DEFS.items()},
    "Stratum": [edit(STRATUM, "method_version"), edit(STRATUM, "use_site"), {**MATCH_STRATUM, "arm": "RANDOM"},
                {**MATCH_STRATUM, "method_version": ""}],
    "Sha256": [H, "sha256:" + H[:-1]], "HexKey": [S], "IsoDate": ["2026-09"], "PartialDate": ["26-09"],
    "ArxivBaseId": ["2101.00001v1", "arxiv:2101.00001"], "PaperVersionId": ["arxiv:2101.00001", "2101.00001v1", "arxiv:2101.00001v0"],
    "LogicalId": [ident("work")],
    "DerivationId": ["proof:" + H, "unlocated:GUESS:0", f"source:{PV_ID}:{H}", "statement:x"],
    "Method": ["MODEL"], "LegRole": ["PROOF"], "UseSite": ["BOTH"], "Admission": ["AUDIT_ARM"], "CountBasis": ["UNIFORM_COVERAGE"],
    "Rate": [edit(RATE, "z"), {**RATE, "lower": 1.5}], "TokenPrices": [{**PRICES, "output": -1}], "RootClass": ["ORIGIN"],
    "Layer": [-1, "INF"], "Bracket": [{"lower": 1}, {**BRACKET, "exact": True}], "EdgeType": ["CITES", "NOMINATES", "REVIEWS"],
    "DateValue": [{**DATE, "value": None}, {**DATE, "kind": "UNKNOWN"}, {**DATE, "kind": "BIB_YEAR"}],
    "ExternalIdentifierV4": [edit(EXT, "openalex_id"), {**EXT, "resolution_basis": "GUESS"}],
    "ModelSelectionV4": [{**SELECTION, "engine_class": "HEAVY"}, {**SELECTION, "policy_version": "operation-routing-v1"},
                         {**SELECTION, "operation": "dependency.match", "engine_class": "LIGHT"}, edit(SELECTION, "training_cutoff"),
                         {**SELECTION, "model": "mimo-v2.6-flash"}, {**ROUTE_A, "effort": "high"}, {**SELECTION, "operation": "leg.judge"},
                         {**SELECTION, "model": "gpt-6-astra"}, {**SELECTION, "operation": "paper.extract", "model": "mimo-v2.6-flash",
                                                                 "effort": "thinking-enabled"}],
    "PaperVersionNode": [edit(PAPER, "content_sha256"), {**PAPER, "redistribution": "CC-BY"}, {**PAPER, "id": "arxiv:2101.00001"},
                         {**PAPER, "asserted_by": []}, {**PAPER, "deterministic_yield": YIELD}],
    "WorkNode": [edit(WORK, "doi"), {**WORK, "doi": "10.1103/PhysRevA.1"}, {**WORK, "terminal_kind": "UNKNOWN"},
                 edit(WORK, "doi", identity_basis="BIB_DIGEST")],
    "BibEntryNode": [edit(BIB, "locator"), {**BIB, "identifiers": {"doi": None}}],
    "ClaimNode": [{**CLAIM, "occurrence_ids": []}, {**CLAIM, "work_id": ident("work")}, {**WORK_CLAIM, "paper_version_id": PV_ID},
                  {**CLAIM, "part": "part:a"}, {**CLAIM, "statement": "method-written text"}],
    "ClaimReadingNode": [{**READING, "display_text": "x"}, {**READING, "display_text_class": "VERBATIM"},
                         {**READING, "state": "VERIFIED"}, {**READING, "kind": "axiom"}],
    "JunctionNode": [{**JUNCTION, "legs": []}, {**JUNCTION, "legs": [{**LEG, "use_site": "STATEMENT"}]},
                     {**JUNCTION, "derivation_id": "statement"}, {**JUNCTION, "derivation_id": f"source:{PV_ID}:{S}"},
                     {**JUNCTION, "legs": [{**LEG, "position": 0}]}, {**JUNCTION, "legs": [edit(LEG, "flags")]}],
    "PlaceholderNode": [edit(REQUEST, "bib_entry_id"), {**REQUEST, "reason": "NOT_YET_EXTRACTED"}, edit(UNRESOLVED, "reason"),
                        {**UNRESOLVED, "reason": "AMBIGUOUS"}, {**UNRESOLVED, "bib_entry_id": ident("bib")}],
    "PrimitiveAssertionNode": [{**PRIMITIVE, "basis": "MODEL"}],
    "Edge": [{**EDGE, "props": {"admission": "SAMPLE", "round": 0}}, {**EDGE, "type": "CITES"},
             {**EDGE, "type": "PREMISE_OF", "end_id": ident("claim"), "props": {"position": 0, "role": "UNCLASSIFIED", "use_site": "PROOF"}},
             {**EDGE, "type": "SAME_WORK", "props": {"basis": "TITLE_MATCH"}}, edit(EDGE, "props")],
    "GraphDelta": [deep(DELTA, ["nodes", "Review"], []), deep(DELTA, ["edges", 0, "type"], "PREMISE_OF"),
                   {**DELTA, "stage": "S10"}, deep(DELTA, ["subject", "kind"], "PAPER"), edit(DELTA, "issues"),
                   deep(DELTA, ["nodes", "Junction", 0, "legs"], []), {**DELTA, "stage": "HUMAN_ENTRY"},
                   {**DELTA, "stage": "LIBRARY_AUDIT", "method": "HUMAN"}, {**DELTA, "measurements": {"layer": 1}},
                   {**DELTA, "measurements": {"deterministic_yield": edit(YIELD, "owned_proofs")}},
                   deep(DELTA, ["nodes", "PaperVersion"], [PAPER])],  # only S1 asserts PaperVersion
    "DeltaSetManifest": [{**MANIFEST, "deltas": [ident("delta")] * 2}, {**MANIFEST, "excluded": [{"delta_id": ident("delta")}]}],
    "ProjectionManifest": [{**PROJECTION, "state": "VERIFIED"}, {**PROJECTION, "audit_counts": {"G1": -1}}],
    "AnalysisPolicy": [{**POLICY, "establishment_reading": {"mode": "ONLY", "methods": []}},
                       {**POLICY, "establishment_reading": {"mode": "UNION", "methods": ["HUMAN"]}},
                       {**POLICY, "cycle_policy": "CONDENSE"}, edit(POLICY, "edge_precision"), {**POLICY, "base_set": "B"},
                       {**POLICY, "traverse": "SAMPLE_ONLY", "count_basis": "ALL_ADMITTED"}, edit(POLICY, "admission_gate"),
                       {**edit(POLICY, "traverse"), "traverse_expansions": True}],
    "CorpusManifest": [deep(CORPUS, ["primary_analysis_policy", "status"], "EXPLORATORY"),
                       deep(CORPUS, ["eligibility", "rule"], "k>=1"), deep(CORPUS, ["eligibility", "params", "min_theorem_like"], 0),
                       {**CORPUS, "extraction": {"operation": "paper.extract_focus", "method_version": "x"}},
                       {**CORPUS, "extraction": {"operation": "paper.extract_local", "method_version": "x", "focus_bytes": 4096}},
                       {**CORPUS, "coverage": "PRIORITIZED"}, edit(CORPUS, "gates"), edit(CORPUS, "coverage"),
                       {**CORPUS, "budget_ceiling": {"unit": "USD", "value": 1}},
                       deep(CORPUS, ["primary_analysis_policy", "admission_gate"], ident("gate")),
                       {**CORPUS, "audit_arm": {"min_fraction": 0.1, "min_papers": 50, "seed": "a"}},
                       deep(CORPUS, ["gates", "P0", "require_projection_under_ceiling"], False),
                       {**CORPUS, "version_rule": "EARLIEST"}],
    "SamplingRecord": [deep(SAMPLING, ["candidates", 0, "outcome"], "REPLACED"),
                       deep(SAMPLING, ["candidates", 1, "undetermined_class"], "TIMEOUT"),
                       deep(SAMPLING, ["candidates", 0], edit(SAMPLING["candidates"][0], "paper_version_id")),
                       deep(SAMPLING, ["candidates", 0], edit(SAMPLING["candidates"][0], "order_key")),
                       deep(SAMPLING, ["candidates", 0, "reason"], "accepted anyway"),
                       deep(SAMPLING, ["candidates", 1, "paper_version_id"], PV_ID),
                       deep(EXPANSION, ["candidates", 0, "order_key"], H),
                       edit(EXPANSION, "expansion"), {**EXPANSION, "discovery": DISCOVERY["discovery"]},
                       {**SAMPLING, "expansion": EXPANSION["expansion"]}, {**SAMPLING, "discovery": DISCOVERY["discovery"]},
                       edit(DISCOVERY, "discovery"), deep(DISCOVERY, ["candidates", 0], edit(DISCOVERY["candidates"][0], "order_key")),
                       {**SAMPLING, "round": 1}, {**EXPANSION, "round": 0},
                       {**SAMPLING, "audit_arm": {"arxiv_base_ids": ["2101.00001"], "sha256": S}}],
    "NodeMetrics": [{**METRICS, "layer": "INFINITY"}, {**METRICS, "route_status": "ROUTE_UNDETERMINED"},
                    {**METRICS, "layer": "UNRESOLVED", "route_status": "ROUTE_UNDETERMINED"}, edit(WORK_METRICS, "citing_papers"),
                    {**WORK_METRICS, "layer": "INFINITY"}, edit(METRICS, "uncertainty"), {**METRICS, "score": 1.0},
                    {**METRICS, "subject_id": ident("work")}, {**METRICS, "coverage": "UNIFORM_COVERAGE"}, edit(METRICS, "count_basis")],
    "FoundationNomination": [{**NOMINATION, "subject_kind": "CLAIM"}, {**NOMINATION, "next_action": "VERIFY"},
                             {**NOMINATION, "status": "FOUNDATION"}, {**NOMINATION, "match_coverage": 1.5},
                             {**NOMINATION, "rank_interval": {"lower": 0, "upper": 1}}, edit(NOMINATION, "dependent_topics"),
                             {**NOMINATION, "missed_nomination_rate": None}],
    "ReviewSample": [deep(REVIEW_SAMPLE, ["items", 0, "inclusion_probability"], 0),
                     deep(REVIEW_SAMPLE, ["items", 0], edit(REVIEW_SAMPLE["items"][0], "stratum")),
                     {**REVIEW_SAMPLE, "items": []}, {**REVIEW_SAMPLE, "estimand": "F1"},
                     {**REVIEW_SAMPLE, "evaluation_plan_id": None}, {**REVIEW_SAMPLE, "labeller_count": 1},
                     {**REVIEW_SAMPLE, "label_source": "HUMAN"}, edit(REVIEW_SAMPLE, "label_source"),
                     deep(REVIEW_SAMPLE, ["items", 0, "stratum"], MATCH_STRATUM),  # a leg stratum names its role and use site
                     deep(REVIEW_SAMPLE, ["items", 0, "stratum"], edit(REVIEW_SAMPLE["items"][0]["stratum"], "method_version"))],
    "HumanReviewV4": [{**REVIEW, "subject_kind": "CLAIM"}, {**REVIEW, "decision": "MAYBE"}, {**REVIEW, "subject_sha256": H},
                      edit(REVIEW, "reviewer")],
    "EvaluationPlan": [{**PLAN, "panel": PLAN["panel"][:1]}, {**PLAN, "decision_rule": "MAJORITY"}, {**PLAN, "scheme": "AUTO_EVAL_V2"},
                       deep(PLAN, ["controls", "negative", "count_per_rule"], 0), {**PLAN, "blinding": "NONE"}, {**PLAN, "estimands": []},
                       deep(PLAN, ["panel", 0, "judge_id"], "Mimo Pro"), {**PLAN, "producers": {}},
                       {**PLAN, "producers": {"paper.extract_focus": ["mimo-v2.6-flash"]}}, edit(PLAN, "producers"),
                       {**edit(PLAN, "producers"), "extraction_models": ["mimo-v2.6-flash"]},
                       deep(PLAN, ["controls", "negative"], {"rules": ["SAME_PAPER_NEAR_MISS_V1"], "count": 12})],
    "Judgement": [{**JUDGEMENT, "evidence": None}, {**JUDGEMENT, "validity": "RESPONSE_INVALID"}, {**JUDGEMENT, "verdict": "NOT_USED"},
                  {**JUDGEMENT, "validity": "EVIDENCE_UNBOUND"}, {**JUDGEMENT, "state": "SIGNED"}, edit(JUDGEMENT, "receipt"),
                  {**JUDGEMENT, "receipt": None}],
    "PrecisionEstimate": [{**ESTIMATE, "lower_bound": None}, {**ESTIMATE, "fpr_inflation": 0.5}, deep(ESTIMATE, ["gate", "decision"], "PASS"),
                          {**ESTIMATE, "gate": {"threshold": 0.85, "decision": "NOT_ESTIMABLE", "reason": "x"}},
                          {**ESTIMATE, "stratum": None}, {**ESTIMATE, "false_positive_by_rule": {}}, edit(ESTIMATE, "false_positive_by_rule"),
                          {**ESTIMATE, "false_positive_by_rule": {"RANDOM_TEXT_V1": RATE}}],
    "RecallEstimate": [{**RECALL, "basis": "GOLD_PROOFS"}, edit(RECALL, "assumption"), {**RECALL, "estimate": 1.5}],
    "EvaluationReport": [{**REPORT, "label_source": "HUMAN"}, {**REPORT, "assumptions": []}, edit(REPORT, "independence"),
                         edit(REPORT, "inputs"), deep(REPORT, ["independence", "judge_models"], ["gpt-5.6-terra"]),
                         deep(REPORT, ["inputs", "controls", "LEG_PRECISION"], {"positive": 1, "negative_by_rule": {}})],
    "GateDecision": [{**GATE, "decision": "GO_WITH_EXPANSION"}, {**GATE, "gate": "P_MINUS_1"}, {**GATE, "measured": {"x": "text"}},
                     {**GATE, "gate": "P1"}],
    "PricingProfile": [{**PRICING, "source_url": "http://mimo.mi.com"}, {**PRICING, "unit": "PER_TOKEN"},
                       deep(PRICING, ["models", "mimo-v2.6-flash", "limits", "rpm"], 0), {**PRICING, "models": {}},
                       deep(PRICING, ["models", "mimo-v2.6-flash", "limits", "batch_completion_minutes"], 0)],
    "CostProjection": [edit(COST, "parameters"), deep(COST, ["parameters", "tokens_per_byte", "label"], "GUESS"),
                       {**COST, "operation": "paper.extract"}, deep(COST, ["totals", "cost"], -1), edit(COST, "paper_plans"),
                       {**COST, "wallclock_basis": "GUESS"}, {**COST, "ceiling": {"unit": "USD", "value": 2500}},
                       deep(COST, ["ceiling", "other_stages"], -1)],
}
CASES = sorted(VALID.items())
BAD = sorted(INVALID.items())


def test_every_def_has_valid_and_invalid_examples():
    assert set(VALID) == set(contracts.DEFS) == set(INVALID)


def test_v04_schema_files_pass_metaschema_and_wrappers_reference_top_level_records():
    wrappers = {}
    for path in contracts.SCHEMA_FILES:
        schema = json.loads(path.read_bytes())
        Draft202012Validator.check_schema(schema)
        if path.parent == contracts.ROOT / "schemas" and path.name != "corpus.schema.json":
            assert schema["$id"] == "https://agtxiv.org/schema/research/0.4.0/" + path.name
            wrappers[schema["$ref"].rsplit("/", 1)[1]] = schema
    assert set(wrappers) == {"GraphDelta", "DeltaSetManifest", "ProjectionManifest", "CorpusManifest", "SamplingRecord",
                             "AnalysisPolicy", "NodeMetrics", "FoundationNomination", "ReviewSample", "HumanReviewV4",
                             "EvaluationPlan", "Judgement", "EvaluationReport", "GateDecision", "PricingProfile", "CostProjection"}
    for name, schema in wrappers.items():
        checker = Draft202012Validator(schema, registry=contracts.REGISTRY)
        assert all(checker.is_valid(row) for row in VALID[name]) and not checker.is_valid(INVALID[name][0])


def test_every_ref_resolves_offline_including_v03_defs():
    resolver = contracts.REGISTRY.resolver(base_uri=contracts.CORPUS_ID)
    refs = []

    def walk(node):
        if isinstance(node, dict):
            refs.extend([node["$ref"]] if "$ref" in node else [])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(contracts.SCHEMAS[contracts.CORPUS_ID])
    v03 = [ref for ref in refs if ref.startswith("../0.3.0/")]
    assert v03
    for ref in refs:
        assert resolver.lookup(ref).contents is not None


@pytest.mark.parametrize("name,rows", CASES)
def test_valid_examples(name, rows):
    for row in rows:
        contracts.validate(name, row)


@pytest.mark.parametrize("name,rows", BAD)
def test_invalid_examples(name, rows):
    for row in rows:
        with pytest.raises(ValidationError):
            contracts.validate(name, row)


def test_unknown_def_is_refused():
    with pytest.raises(KeyError):
        contracts.validator("SupportGroup")


def enum(*path):
    node = contracts.SCHEMAS[contracts.CORPUS_ID]["$defs"]
    for key in path:
        node = node[key]
    return set(node["enum"])


def test_enums_match_the_spec():
    assert enum("Method") == {"DETERMINISTIC_ANCHOR", "HOST_RULE", "MODEL_EXTRACTION", "MODEL_MATCH", "HUMAN", "LIBRARY"}
    assert enum("LegRole") == {"DEFINITION_DEPENDENCY", "SCIENTIFIC_CLAIM_DEPENDENCY", "SCOPE_DEPENDENCY",
                               "PROOF_DEPENDENCY", "BRIDGING_DEPENDENCY", "UNCLASSIFIED"}
    assert enum("UseSite") == {"STATEMENT", "PROOF", "UNKNOWN"}
    assert enum("CountBasis") == {"SAMPLE_ONLY", "ALL_ADMITTED"}
    assert enum("Admission") == {"SAMPLE", "EXPANSION", "DISCOVERY"}
    assert enum("AnalysisPolicy", "properties", "traverse") == {"SAMPLE_ONLY", "ALL_ADMITTED"}
    assert enum("Judgement", "properties", "verdict") == {"USED", "NOT_USED", "CANNOT_TELL"}
    assert enum("GateDecision", "properties", "decision") == {"GO", "GO_WITH_EXPANSION", "NO_GO"}
    assert enum("CorpusManifest", "properties", "extraction", "properties", "operation") == {"paper.extract_focus", "paper.extract_local"}
    assert enum("EdgeType") == {"STATES", "STATED_BY", "READS", "PART_OF", "HAS_ENTRY", "RESOLVES_TO", "REQUESTS_FROM",
                                "MENTIONS", "RESTATES_RESULT_OF", "VERSION_OF", "SAME_WORK", "CORRECTS", "SUPERSEDES",
                                "ASSERTS_PRIMITIVE", "INCLUDES", "PREMISE_OF", "CONCLUDES"}  # REVIEWS, IN_RUN, NOMINATES: not in v0.4
    assert enum("GraphDelta", "properties", "stage") == {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "HUMAN_ENTRY",
                                                         "LIBRARY_AUDIT"}
    assert enum("DateValue", "properties", "kind") == {"ARXIV_V1", "ARXIV_VERSION", "JOURNAL_PUBLISHED", "BIB_YEAR", "UNKNOWN"}
    assert enum("PaperVersionNode", "properties", "redistribution") == {"OPEN", "RESTRICTED", "UNKNOWN"}
    assert enum("WorkNode", "properties", "identity_basis") == {"ARXIV_BASE", "DOI", "OPENALEX", "BIB_DIGEST"}
    assert enum("WorkNode", "properties", "work_kind") == {"ARTICLE", "BOOK", "THESIS", "PROCEEDINGS", "UNKNOWN"}
    assert enum("ClaimNode", "properties", "origin") == {"PAPER_VERSION", "WORK_LOCATOR"}
    assert enum("ClaimReadingNode", "properties", "kind") == {"definition", "theorem", "lemma", "proposition", "corollary",
                                                              "equation", "claim", "remark", "UNKNOWN"}
    assert enum("ClaimReadingNode", "properties", "display_text_class") == {"VERBATIM", "PARAPHRASE", "NONE"}
    assert enum("PlaceholderNode", "properties", "kind") == {"EXTERNAL_REQUEST", "UNRESOLVED_OCCURRENCE"}
    assert enum("PlaceholderNode", "properties", "reason") == {"AMBIGUOUS_OR_SELF_CLAIM", "NOT_YET_EXTRACTED",
                                                               "SHARED_OCCURRENCE_EXPANSION_CYCLIC", "NON_ENVIRONMENT_TARGET"}
    assert enum("PrimitiveAssertionNode", "properties", "basis") == {"AXIOM", "ASSUMPTION", "STANDARD_NOTION", "HUMAN"}
    assert enum("GraphDelta", "properties", "subject", "properties", "kind") == {"PAPER_VERSION", "CLAIM_BATCH",
                                                                                 "REQUEST_POOL", "MANIFEST"}
    assert enum("ProjectionManifest", "properties", "state") == {"BUILDING", "READY", "FAILED"}
    assert enum("AnalysisPolicy", "properties", "work_identity") == {"EXPLICIT_IDS_ONLY", "PLUS_REVIEWED_SAME_WORK",
                                                                     "PLUS_CANDIDATE_SAME_WORK"}
    assert enum("AnalysisPolicy", "properties", "citation_group_semantics") == {"AND", "OR"}
    assert enum("AnalysisPolicy", "properties", "cycle_policy") == {"FIXPOINT", "CONDENSE_V03"}
    assert enum("AnalysisPolicy", "properties", "base_set") == {"ALL_ROOTS", "PRIMITIVE_ASSERTED"}
    assert enum("AnalysisPolicy", "properties", "status") == {"PRIMARY", "EXPLORATORY"}
    assert enum("SamplingRecord", "properties", "candidates", "items", "properties", "undetermined_class") == {
        "TRANSIENT_NETWORK", "NO_TEX_SOURCE", "SIZE_LIMIT", "MAIN_AMBIGUOUS", "WITHDRAWN", "PARSE_FAILED", "ID_NOT_FOUND"}
    assert enum("FoundationNomination", "properties", "next_action") == {"ACQUIRE_SOURCE", "EXTRACT", "MATCH_REQUESTS",
                                                                         "LIBRARY_AUDIT", "HUMAN_REVIEW", "FORMALIZE"}
    assert enum("Edge", "allOf", 3, "then", "properties", "props", "properties", "basis") == {
        "HOST_RULE_ARXIV_DOI", "HOST_RULE_ARXIV_METADATA_DOI", "MODEL_MATCH", "HUMAN"}
    for value in ("SOURCE_EXPLICIT", "CROSSREF_CANDIDATE", "ADS_CANDIDATE", "UNRESOLVED", "OPENALEX_CANDIDATE",
                  "HOST_RULE_ARXIV_DOI"):
        contracts.validate("ExternalIdentifierV4", {**EXT, "resolution_basis": value})
    for value in ("SUPPORT_GROUP", "STATEMENT_ALIGNMENT", "PREMISE_ALIGNMENT", "FAILURE_CLASSIFICATION", "JUNCTION", "LEG",
                  "WORK_IDENTITY", "PRIMITIVE_ASSERTION", "FOUNDATION_NOMINATION"):
        contracts.validate("HumanReviewV4", {**REVIEW, "subject_kind": value})


def test_no_contract_can_carry_a_verified_value():
    assert "VERIFIED" not in (contracts.ROOT / "schemas" / "corpus.schema.json").read_text()
