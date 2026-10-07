"""P0 labelling samples (spec §11): seeded stratified draws that record inclusion probabilities, the Wilson
score interval, and the inverse-inclusion-weighted (Hájek) precision estimate. No label is made here: labels come
from an AUTO_PANEL (autoeval.py, the default) or from humans (an optional audit of the panel)."""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict

import contracts
from corpus import CONTRACT_VERSION, order_key
from delta import address

Z95 = 1.959963984540054
RELABEL_GAP = dt.timedelta(days=7)


def stratum_key(stratum):
    """The full stratum (method, method_version and, for a leg, role and use_site) as a sortable key; () for none."""
    return () if stratum is None else tuple(sorted(stratum.items()))


def draw(population, per_stratum, seed):
    """Per stratum (every field of it: method, method_version and, for legs, role and use_site; one stratum for items
    without one) the first n in the §6.2 seeded order (corpus.order_key), without replacement; each drawn item records
    π = n / N of its stratum."""
    strata = defaultdict(list)
    for item in population:
        strata[stratum_key(item.get("stratum"))].append(item)
    out = []
    for _, items in sorted(strata.items()):
        items, n = sorted(items, key=lambda i: order_key(seed, i["subject_id"])), min(per_stratum, len(items))
        out += [{**i, "inclusion_probability": n / len(items)} for i in items[:n]]
    return out


def _sample(**fields):
    body = {"kind": "ReviewSample", "contract_version": CONTRACT_VERSION, **fields}
    row = {**body, "sample_id": address("review-sample", {k: v for k, v in body.items() if k != "created_at"})}
    contracts.validate("ReviewSample", row)
    return row


def review_sample(manifest_id, estimand, arm, seed, labelling_guide, labeller_count, population, per_stratum,
                  created_at, *, label_source="HUMAN", evaluation_plan_id=None):
    """label_source AUTO_PANEL names the EvaluationPlan whose judges label it (labeller_count = panel size >= 2)."""
    return _sample(manifest_id=manifest_id, estimand=estimand, arm=arm, seed=seed, label_source=label_source,
                   evaluation_plan_id=evaluation_plan_id, labelling_guide=labelling_guide, labeller_count=labeller_count,
                   relabel_of=None, items=draw(population, per_stratum, seed), created_at=created_at)


def relabel(sample, seed, created_at):
    """The seeded 10% re-label, ceil(n / 10) items drawn >= 7 days after the sample (§11): a human labeller's
    self-consistency check. Its seed must differ from the sample's: that order would take the items each stratum drew
    first, not a uniform subset, and π · m / n would be wrong."""
    if seed == sample["seed"]:
        raise ValueError("a re-label needs a seed other than its sample's")
    if dt.datetime.fromisoformat(created_at) - dt.datetime.fromisoformat(sample["created_at"]) < RELABEL_GAP:
        raise ValueError("a re-label is drawn at least 7 days after its sample")
    items = sorted(sample["items"], key=lambda i: order_key(seed, i["subject_id"]))
    m = math.ceil(len(items) / 10)
    return _sample(**{k: sample[k] for k in ("manifest_id", "estimand", "arm", "label_source", "evaluation_plan_id",
                                             "labelling_guide", "labeller_count")},
                   seed=seed, relabel_of=sample["sample_id"], created_at=created_at,
                   items=[{**i, "inclusion_probability": i["inclusion_probability"] * m / len(items)} for i in items[:m]])


def wilson(successes, n):
    """Wilson score 95% interval for successes out of n (n may be an effective, non-integer size)."""
    if n <= 0:
        raise ValueError("the Wilson interval needs n > 0")
    p, z2 = successes / n, Z95 * Z95
    centre, half = p + z2 / (2 * n), Z95 * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return {"lower": max(0.0, (centre - half) / (1 + z2 / n)), "upper": min(1.0, (centre + half) / (1 + z2 / n))}


def precision(sample, labels):
    """Σ(y/π) / Σ(1/π) over the labelled items ({subject_id: bool}); Wilson 95% at Kish n_eff = (Σw)² / Σw²."""
    pairs = [(1 / i["inclusion_probability"], labels[i["subject_id"]]) for i in sample["items"] if i["subject_id"] in labels]
    if not pairs:
        raise ValueError("no labelled item")
    total = sum(w for w, _ in pairs)
    estimate, n_eff = sum(w for w, y in pairs if y) / total, total * total / sum(w * w for w, _ in pairs)
    return {"estimate": estimate, "labelled": len(pairs), "items": len(sample["items"]), "n_effective": n_eff,
            "wilson_95": wilson(estimate * n_eff, n_eff)}
