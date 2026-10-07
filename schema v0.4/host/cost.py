"""S6 cost projection and per-call cost (spec §1.1, §11.3), from a dated PricingProfile file. No model is called.

project() is the host's plan for a run: calls, tokens, money and wall-clock time of the manifest's one S6 policy over
the planned papers. Every parameter the formulas use is listed with its label (MEASURED, OFFICIAL, POLICY for a host
choice, ESTIMATED) and source; the P0 gate refuses a projection that still uses an ESTIMATED one. call_cost() prices one
receipt's usage for the ledger's settle().

Formulas (per paper of S source bytes; β = focus_fraction, τ = tokens_per_byte, v = visible output per focus byte,
r = reasoning tokens per call, w = instruction tokens per call). A paper plan is MODELLED from S, or MEASURED by the
host's own prompt builder (focus_plan: calls n, focus bytes F, prefix bytes B, prompt bytes T summed over the calls):
  WHOLE_PAPER_FOCUS modelled  n = max(1, βS / focus_bytes); prefix = τS(1 + inventory_fraction);
                              input = n(prefix + w); cached = (n - 1) · prefix · cache_efficiency; output = βSv + nr
  WHOLE_PAPER_FOCUS measured  input = τT; cached = (n - 1) · τB · cache_efficiency; output = Fv + nr
  LOCAL_BATCH modelled        n = max(1, βS / local_batch_bytes); input = βSτ(1 + local_context_factor) + nw; cached = 0;
                              output = βSv + nr
Every total is multiplied by retry_factor.

Scaling. WHOLE_PAPER_FOCUS re-sends the whole prefix (about τS tokens) with each of its n ~ βS / focus_bytes calls, so its
input tokens grow as S², as the v0.3 layout's did. What differs is the price: every call after a paper's first can hit
the prompt cache and is billed at cache_hit (1/50 of cache_miss for mimo-v2.6-flash), so at a high cache_efficiency the
money is dominated by the terms linear in S; at a low one it grows as S² at the cache_miss price. LOCAL_BATCH grows as
S. The cache helps only if a paper's calls reach the provider back to back inside the cache lifetime, which the pages
do not state, so the dispatcher sends one paper's foci consecutively; whether Batch API requests hit the cache is not
documented beyond the batch cache_hit price. cache_efficiency is therefore ESTIMATED until pilot receipts measure it.

Wall-clock. Real time: max(calls / rpm, tokens / tpm) minutes. Batch: the provider's completion window
(batch_completion_minutes of the profile) for jobs submitted together; the pages state no job concurrency limit and the
128 MB file limit only sets how many jobs there are.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import contracts
from core import digest
from corpus import CONTRACT_VERSION, check_corpus_manifest
from delta import address

MILLION = 1_000_000
PARAMETERS = {
    "tokens_per_byte": (0.40, "MEASURED", "GPT tokenizers on v0.3 extraction prompts, 0.39-0.41 over 35 Luna and 20 Astra receipts; the MiMo tokenizer is unmeasured"),
    "focus_fraction": (0.621, "MEASURED", "73,203 focus bytes of 117,802 source bytes, arxiv:2607.26154v1 (n = 1)"),
    "visible_output_per_focus_byte": (0.887, "MEASURED", "Luna median 2,140 output minus 475 reasoning tokens per 1,877-byte scope (n = 35)"),
    "reasoning_tokens_per_call": (500.0, "ESTIMATED", "Luna median 475 reasoning tokens; MiMo thinking length is unmeasured"),
    "retry_factor": (1.2, "MEASURED", "Luna: 30 of 35 responses validated, 1/0.857 = 1.17, rounded up"),
    "cache_efficiency": (0.9, "ESTIMATED", "share of a paper's later prefixes billed as cache hits; the provider states no cache lifetime"),
    "instruction_tokens": (2000.0, "ESTIMATED", "instruction, focus block or batch framing per call"),
    "inventory_fraction": (0.05, "ESTIMATED", "alias inventory tokens relative to source tokens (focus mode)"),
    "local_context_factor": (2.0, "ESTIMATED", "local mode: referenced statements, prose and bibliography per focus byte"),
    "local_batch_bytes": (8192.0, "POLICY", "local mode: focus bytes per claim batch, a host choice"),
    "output_reserve_tokens": (32768.0, "POLICY", "context kept free for the answer when checking the largest prompt, a host choice"),
}
USED = {  # the parameters each (operation, paper plan) formula reads
    ("paper.extract_focus", "MODELLED"): ("tokens_per_byte", "focus_fraction", "visible_output_per_focus_byte", "reasoning_tokens_per_call",
                                          "retry_factor", "cache_efficiency", "instruction_tokens", "inventory_fraction", "output_reserve_tokens"),
    ("paper.extract_focus", "MEASURED"): ("tokens_per_byte", "visible_output_per_focus_byte", "reasoning_tokens_per_call", "retry_factor",
                                          "cache_efficiency", "output_reserve_tokens"),
    ("paper.extract_local", "MODELLED"): ("tokens_per_byte", "focus_fraction", "visible_output_per_focus_byte", "reasoning_tokens_per_call",
                                          "retry_factor", "instruction_tokens", "local_context_factor", "local_batch_bytes", "output_reserve_tokens"),
}
PLAN_FIELDS = ("source_bytes", "focus_bytes", "calls", "prefix_bytes", "prompt_bytes", "max_prompt_bytes")


def load_pricing(path):
    """(profile, sha256 of the file bytes) of a PricingProfile file, checked against its contract."""
    raw = Path(path).read_bytes()
    profile = json.loads(raw)
    contracts.validate("PricingProfile", profile)
    return profile, digest(raw)


def _prices(profile, model, mode):
    entry = profile["models"].get(model)
    if entry is None:
        raise ValueError("MODEL_NOT_IN_PRICING_PROFILE: " + model)
    prices = entry[mode]
    if prices is None:
        raise ValueError(f"NO_{mode.upper()}_PRICE_FOR: {model}")
    return prices, entry["limits"]


def call_cost(profile, model, usage, mode="realtime"):
    """Money for one call's usage {prompt_tokens, cached_tokens, completion_tokens} (completion includes reasoning)."""
    prices, _ = _prices(profile, model, mode)
    prompt, cached, completion = usage["prompt_tokens"], usage.get("cached_tokens") or 0, usage["completion_tokens"]
    if not 0 <= cached <= prompt or completion < 0:
        raise ValueError("USAGE_INVALID")
    return ((prompt - cached) * prices["cache_miss"] + cached * prices["cache_hit"] + completion * prices["output"]) / MILLION


def focus_plan(built, source_bytes):
    """The MEASURED plan of one paper from its extraction.build_focus_prompts output: calls, focus bytes (the FOCUS
    rows' spans), prefix bytes, and the prompt bytes summed over the calls and at most."""
    sizes = [len(p["prompt"].encode()) for p in built["prompts"]]
    focus = sum(row["byte_end"] - row["byte_start"] for p in built["prompts"] for row in p["context"]["inventory"] if row["role"] == "FOCUS")
    return {"source_bytes": source_bytes, "focus_bytes": focus, "calls": len(sizes), "prefix_bytes": built["prefix_bytes"],
            "prompt_bytes": sum(sizes), "max_prompt_bytes": max(sizes, default=0)}


def paper_tokens(size, operation, extraction, p, plan=None):
    """(calls, input, cached, output) tokens of one paper of `size` source bytes, before the retry factor; plan: its
    MEASURED focus_plan (focus mode only)."""
    v, r = p["visible_output_per_focus_byte"], p["reasoning_tokens_per_call"]
    if plan is not None:
        if operation != "paper.extract_focus":
            raise ValueError("MEASURED_PLANS_ARE_FOCUS_MODE_ONLY")
        calls, tau = plan["calls"], p["tokens_per_byte"]
        return (calls, tau * plan["prompt_bytes"], max(0, calls - 1) * tau * plan["prefix_bytes"] * p["cache_efficiency"],
                plan["focus_bytes"] * v + calls * r)
    focus, w = p["focus_fraction"] * size, p["instruction_tokens"]
    if operation == "paper.extract_focus":
        calls = max(1.0, focus / extraction["focus_bytes"])
        prefix = p["tokens_per_byte"] * size * (1 + p["inventory_fraction"])
        return calls, calls * (prefix + w), (calls - 1) * prefix * p["cache_efficiency"], focus * v + calls * r
    calls = max(1.0, focus / p["local_batch_bytes"])
    return calls, focus * p["tokens_per_byte"] * (1 + p["local_context_factor"]) + calls * w, 0.0, focus * v + calls * r


def project(manifest, pricing_path, model, mode, papers, created_at, *, sizes_label="MEASURED", overrides=None,
            other_stages=0.0, already_spent=0.0, reserve_basis="no reserve for other stages; nothing spent yet"):
    """The CostProjection of the manifest's S6 policy over the planned papers: source sizes in bytes (MODELLED plans),
    or focus_plan dicts (MEASURED plans, focus mode). The pricing file is read here, so the recorded digest is of the
    prices used. other_stages (S7, AUTO_EVAL_V1 and DISCOVERY calls) and already_spent (the ledger's spent()) are in the
    ceiling's unit; under_ceiling iff projected + other_stages + already_spent <= the ceiling."""
    check_corpus_manifest(manifest)
    profile, profile_sha256 = load_pricing(pricing_path)
    papers = list(papers)
    measured = bool(papers) and all(isinstance(x, dict) for x in papers)
    if measured:
        if any(set(x) != set(PLAN_FIELDS) or any(type(x[k]) is not int or x[k] < 0 for k in PLAN_FIELDS) or x["source_bytes"] <= 0
               for x in papers):
            raise ValueError("PAPER_PLANS_INVALID")
        sizes = [x["source_bytes"] for x in papers]
    elif papers and all(type(x) is int and x > 0 for x in papers):
        sizes = papers
    else:
        raise ValueError("PAPERS_ARE_POSITIVE_SOURCE_SIZES_OR_FOCUS_PLANS")
    if not (other_stages >= 0 and already_spent >= 0):
        raise ValueError("RESERVES_ARE_NON_NEGATIVE")
    extraction, operation = manifest["extraction"], manifest["extraction"]["operation"]
    basis = "MEASURED" if measured else "MODELLED"
    if (operation, basis) not in USED:
        raise ValueError("MEASURED_PLANS_ARE_FOCUS_MODE_ONLY")
    params = {k: {"value": float(v), "label": label, "source": source} for k, (v, label, source) in PARAMETERS.items()}
    for key, row in (overrides or {}).items():
        if key not in params or set(row) != {"value", "label", "source"}:
            raise ValueError("PARAMETER_OVERRIDE_INVALID: " + key)
        params[key] = {**row, "value": float(row["value"])}
    p = {k: row["value"] for k, row in params.items()}
    prices, limits = _prices(profile, model, mode)
    calls = inp = cached = out = 0.0
    for size, plan in zip(sizes, papers if measured else [None] * len(sizes)):
        c, i, h, o = paper_tokens(size, operation, extraction, p, plan)
        calls, inp, cached, out = calls + c, inp + i, cached + h, out + o
    k = p["retry_factor"]
    calls, inp, cached, out = calls * k, inp * k, cached * k, out * k
    money = ((inp - cached) * prices["cache_miss"] + cached * prices["cache_hit"] + out * prices["output"]) / MILLION
    if measured:
        largest = p["tokens_per_byte"] * max(x["max_prompt_bytes"] for x in papers)
    elif operation == "paper.extract_focus":
        largest = p["tokens_per_byte"] * max(sizes) * (1 + p["inventory_fraction"]) + p["instruction_tokens"]
    else:
        largest = p["tokens_per_byte"] * (1 + p["local_context_factor"]) * p["local_batch_bytes"] + p["instruction_tokens"]
    if mode == "batch":
        if "batch_completion_minutes" not in limits:
            raise ValueError("PRICING_PROFILE_STATES_NO_BATCH_COMPLETION_WINDOW: " + model)
        wallclock, wallclock_basis = float(limits["batch_completion_minutes"]), "BATCH_COMPLETION_WINDOW"
    else:
        wallclock, wallclock_basis = max(calls / limits["rpm"], (inp + out) / limits["tpm"]), "REALTIME_RATE_LIMITS"
    ceiling = manifest["budget_ceiling"]
    spend = {profile["currency"]: money, "calls": calls, "input_tokens": inp, "tokens": inp + out}
    if ceiling["unit"] in ("USD", "CNY") and (ceiling["unit"] != profile["currency"]
                                               or ceiling.get("pricing_profile_sha256") != profile_sha256):
        raise ValueError("BUDGET_CEILING_NAMES_ANOTHER_PRICING_PROFILE")
    if ceiling["unit"] not in spend:
        raise ValueError("BUDGET_CEILING_UNIT_NOT_PROJECTABLE: " + ceiling["unit"])
    projected = spend[ceiling["unit"]]
    body = {"kind": "CostProjection", "contract_version": CONTRACT_VERSION, "corpus_id": manifest["corpus_id"],
            "pricing_profile_sha256": profile_sha256, "model": model, "mode": mode, "operation": operation, "papers": len(sizes),
            "source_bytes": {"mean": sum(sizes) / len(sizes), "rms": math.sqrt(sum(s * s for s in sizes) / len(sizes)),
                             "max": max(sizes), "label": sizes_label},
            "paper_plans": basis, "parameters": {key: params[key] for key in USED[(operation, basis)]},
            "totals": {"calls": calls, "input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out, "cost": money},
            "currency": profile["currency"], "wallclock_minutes": wallclock, "wallclock_basis": wallclock_basis,
            "largest_prompt_tokens": largest, "fits_context": largest + p["output_reserve_tokens"] <= limits["context_window"],
            "ceiling": {"unit": ceiling["unit"], "value": ceiling["value"], "projected": projected, "other_stages": float(other_stages),
                        "already_spent": float(already_spent), "basis": reserve_basis},
            "under_ceiling": projected + other_stages + already_spent <= ceiling["value"]}
    row = {**body, "projection_id": address("cost", body), "created_at": created_at}
    contracts.validate("CostProjection", row)
    return row
