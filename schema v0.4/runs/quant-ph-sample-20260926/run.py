"""Owner-requested test run (2026-09-26): 50 random quant-ph theory papers through the deterministic tier of schema v0.4,
then a local Neo4j projection. No theorem is formalised and no model is called, so S6/S7 do not run: the dependencies
built here are DETERMINISTIC_ANCHOR junctions from \\ref and \\cite inside owned proofs (spec §7, S3).

    python run.py sample   # freeze the CorpusManifest, build the frame, examine candidates in seeded order until
                           # 50 are ACCEPTED (acquire, parse, THEOREM_OR_DERIVATION_V1), write the SamplingRecord
    python run.py build    # S1 INCLUDES, S3 anchors and restatements, S4 works; store, manifest, invariants,
                           # exploratory analysis, the P-1 gate, projection rows
    python run.py load     # load the projection into the local Neo4j (127.0.0.1, login disabled) and read the audits

Private data (e-print sources, v0.3 extraction records, deltas with verbatim text) stays under local-archive/ in the
main checkout, which git ignores; this folder keeps only records without verbatim e-print text (I-13).
"""
import collections
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
V04 = HERE.parents[1]
sys.path[:0] = [str(V04 / "host"), str(V04.parent / "schema v0.3" / "host")]

import ingest  # noqa: E402  (v0.3)
from core import canonical, digest  # noqa: E402

import acquire  # noqa: E402
import analysis  # noqa: E402
import anchors  # noqa: E402
import corpus  # noqa: E402
import delta  # noqa: E402
import eligibility  # noqa: E402
import gates  # noqa: E402
import invariants  # noqa: E402
import projection  # noqa: E402
import reviews  # noqa: E402
import works  # noqa: E402
from delta import address  # noqa: E402

REPO = Path("/Users/Yingjian/Documents/GitHub/AgtXIv")  # main checkout: the v0.3 reader needs sources inside the repository it is given
SNAPSHOT = REPO / "local-archive/arxiv-metadata/2026-09-21"
DATA = REPO / "local-archive/corpus/quant-ph-sample-20260926"
NEO4J = "http://127.0.0.1:7474"
SNAP = json.loads((SNAPSHOT / "MANIFEST.json").read_text())
SNAP_LABEL = f"arXiv metadata snapshot (Kaggle Cornell-University/arxiv v304 via {SNAP['source']}@{SNAP['commit'][:12]})"
TEMPLATE = {"kind": "AnalysisPolicy", "contract_version": "0.4.0", "policy_id": "policy:" + "0" * 64, "status": "PRIMARY",
            "establishment_reading": {"mode": "UNION"}, "importance_methods": ["DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION", "MODEL_MATCH"],
            "work_identity": "EXPLICIT_IDS_ONLY", "citation_group_semantics": "AND", "cycle_policy": "FIXPOINT",
            "base_set": "ALL_ROOTS", "include_part_expansions": False, "traverse": "ALL_ADMITTED", "count_basis": "SAMPLE_ONLY",
            "admission_gate": None, "nomination": {"rule": "FOUNDATION_V1", "threshold": 3, "top_k": 50},
            "bootstrap": {"scheme": "PAPER_REWEIGHT_V1", "replicates": 200, "seed": "quant-ph-sample-bootstrap"}, "edge_precision": None}
GATES = {"P_MINUS_1": {"min_eligible_fraction": 0.3, "max_undetermined_fraction": 0.2,
                       "claim_level": {"min_works": 20, "min_citing_papers": 3}},
         "P0": {"admission_threshold": 0.85, "fpr_inflation": 2.0, "alpha": 0.05, "max_unresolved_fraction": 0.2,
                "min_items": 100, "require_projection_under_ceiling": True}}
GRID = ([1, 2, 5], [5, 10, 20])
now = lambda: dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def load(name):
    return json.loads((HERE / name).read_text())


def log(line):
    print(line, flush=True)
    with (HERE / "run.log").open("a") as handle:
        handle.write(f"{now()} {line}\n")


def parser_sha256():
    parts = {"schema v0.3/host/ingest.py": REPO / "schema v0.3/host/ingest.py", "schema v0.3/host/bibtex.py": REPO / "schema v0.3/host/bibtex.py",
             "tools/extract_provisional_claims.py": REPO / "tools/extract_provisional_claims.py", "src/agtxiv_v3/source.py": REPO / "src/agtxiv_v3/source.py"}
    return digest(canonical({name: ingest._sha(path.read_bytes()) for name, path in parts.items()}))


def home(pv):
    base, version = pv.removeprefix("arxiv:").rsplit("v", 1)
    return DATA / "papers" / base.replace("/", "_") / f"v{version}"


def manifest():
    return corpus.check_corpus_manifest(load("corpus-manifest.json"))


def check_primary_categories(record, token):
    """One arXiv API request (export.arxiv.org) for the accepted papers: is the snapshot's first category arXiv's
    primary category? Answers the assumption the frame rests on."""
    pvs = [row["paper_version_id"] for row in record["candidates"] if row["outcome"] == "ACCEPTED"]
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"id_list": ",".join(pv.removeprefix("arxiv:") for pv in pvs), "max_results": len(pvs)})
    token.wait()
    request = urllib.request.Request(url, headers={"User-Agent": acquire.USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        feed = ET.fromstring(response.read())
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    primary = {}
    for entry in feed.findall("a:entry", ns):
        abs_id = entry.findtext("a:id", default="", namespaces=ns).rsplit("/abs/", 1)[-1]
        term = entry.find("x:primary_category", ns)
        primary["arxiv:" + abs_id] = term.get("term") if term is not None else None
    rows = [{"paper_version_id": pv, "api_primary_category": primary.get(pv), "snapshot_first_category": "quant-ph"} for pv in pvs]
    return {"request": url, "retrieved": now(), "papers": len(pvs), "answered": sum(r["api_primary_category"] is not None for r in rows),
            "agree": sum(r["api_primary_category"] == "quant-ph" for r in rows), "rows": rows}


def cmd_sample():
    if (HERE / "corpus-manifest.json").exists():
        m = manifest()
    else:
        m = corpus.freeze_corpus_manifest({
            "field": {"primary_categories": ["quant-ph"], "date_window": {"start": "2015-01-01", "end": "2025-12-31"}},
            "sampling_frame": {"kind": "METADATA_SNAPSHOT", "sha256": "sha256:" + SNAP["manifest_sha256"], "snapshot_date": "2026-09-19"},
            "eligibility": {"rule": "THEOREM_OR_DERIVATION_V1", "params": {"min_theorem_like": 1, "min_display_equations": 10},
                            "program_sha256": eligibility.program_sha256(), "parser_sha256": parser_sha256()},
            "size_limits": {"max_archive_bytes": 64 << 20, "max_expanded_bytes": 256 << 20, "max_file_bytes": 32 << 20, "max_files": 5000,
                            "timeout_seconds": 120, "min_request_interval_seconds": 3},
            "version_rule": "LATEST_ON_OR_BEFORE_SNAPSHOT", "seed": "agtxiv-v04-quant-ph-test-2026-09-26", "target_size": 50,
            "transient_retry_limit": 2, "coverage": "EQUAL_FULL",
            "extraction": {"operation": "paper.extract_focus", "method_version": "focus-1", "focus_bytes": 8192}, "gates": GATES,
            "primary_analysis_policy": TEMPLATE, "budget_ceiling": {"unit": "calls", "value": 0}, "created_at": now()})
        dump("corpus-manifest.json", m)
    log(f"corpus {m['corpus_id']}")
    frame = acquire.snapshot_frame(str(SNAPSHOT / "*.parquet"), m["field"])
    years = collections.Counter(acquire._date(row["versions"][0]["created"]).year for row in frame.values())
    dump("frame-summary.json", {"snapshot": SNAP_LABEL, "snapshot_files_verified": SNAP["all_verified"], "field": m["field"],
                                "papers_in_frame": len(frame), "papers_by_v1_year": dict(sorted(years.items())),
                                "rule": "primary category = first token of `categories`; v1 date in the window"})
    log(f"frame: {len(frame)} quant-ph papers with v1 in {m['field']['date_window']}")
    order = corpus.order_frame(sorted(frame), m["seed"])
    token = acquire.RateToken(m["size_limits"]["min_request_interval_seconds"])
    outcomes, examined = {}, []
    for item in order:
        if sum(o["outcome"] == "ACCEPTED" for o in outcomes.values()) == m["target_size"]:
            break
        base = item["arxiv_base_id"]
        res = acquire.examine(REPO, base, frame[base], m, DATA / "papers", token, snapshot_label=SNAP_LABEL)
        outcomes[base] = res["outcome"]
        decision = res.get("decision") or {}
        examined.append({"n": len(examined) + 1, "arxiv_base_id": base, "order_key": item["order_key"], "paper_version_id": res["paper_version_id"],
                         "title": frame[base]["title"], "categories": frame[base]["categories"], "license": frame[base]["license"],
                         "outcome": res["outcome"], "counts": decision.get("counts"), "issues": sorted({i["code"] for i in res["issues"]}),
                         "metadata": res["metadata"]})
        accepted = sum(o["outcome"] == "ACCEPTED" for o in outcomes.values())
        log(f"{len(examined):3d} {res['paper_version_id']:24s} {res['outcome']['outcome']:12s} "
            f"{res['outcome'].get('undetermined_class') or decision.get('counts') or ''}  accepted={accepted}")
        dump("examined.json", examined)
    record = corpus.sample_record(m, sorted(frame), outcomes, now())
    dump("sampling-record.json", record)
    counts = corpus.estimand_counts(record)
    log(f"sampling record {record['sampling_record_id']}: {counts}")
    dump("primary-category-check.json", check_primary_categories(record, token))


def cmd_build():
    m, record, examined = manifest(), load("sampling-record.json"), load("examined.json")
    meta = {row["paper_version_id"]: row["metadata"] for row in examined if row["outcome"]["outcome"] == "ACCEPTED"}
    s1 = corpus.includes_delta(record, m, meta)
    deltas, s3s, papers = [s1], [], []
    records = {}
    for row in examined:
        path = home(row["paper_version_id"]) / "extraction" / "extraction.json"
        if path.exists():
            records[row["paper_version_id"]] = json.loads(path.read_text())
    for pv in meta:
        rec = records[pv]
        sources = {r["path"]: (REPO / r["path"]).read_bytes() for r in rec["source_files"]}
        s3 = anchors.build_anchor_delta(rec, sources, parents=[s1["delta_id"]])
        restates, s4 = anchors.build_restates_delta(rec, sources, s3), works.build_work_delta(s3, rec)
        deltas += [s3, restates, s4]
        s3s.append(s3)
        kinds = collections.Counter(c["kind"] for c in rec["claims"])
        junctions = s3["nodes"].get("Junction", [])
        placeholders = collections.Counter(p["kind"] for p in s3["nodes"].get("Placeholder", []))
        papers.append({"paper_version_id": pv, "title": meta[pv].get("title"), "redistribution": meta[pv]["redistribution"],
                       "occurrences_by_kind": dict(sorted(kinds.items())), "proof_environments": len(rec["proof_spans"]),
                       "reference_anchors": len(rec["anchors"]), "bibliography_entries": len(rec["bibliography"]),
                       "s3_junctions": len(junctions), "s3_legs": sum(len(j["legs"]) for j in junctions),
                       "s3_proof_junctions": sum(j["derivation_id"].startswith("proof:") for j in junctions),
                       "s3_placeholders": dict(sorted(placeholders.items())), "s3_issues": len(s3["issues"]),
                       "deterministic_yield": s3.get("measurements", {}).get("deterministic_yield")})
    store = delta.DeltaStore(DATA / "deltas")
    for d in deltas:
        store.put(d)
    dm = delta.make_manifest(m["corpus_id"], [d["delta_id"] for d in deltas], created_at=now())
    view = delta.check_manifest(dm, store)
    dump("delta-set-manifest.json", dm)
    findings = invariants.check(view, "EXPLICIT_IDS_ONLY")
    dump("invariants.json", {"work_identity": "EXPLICIT_IDS_ONLY", "findings": findings, "count": len(findings)})
    legs = sum(len(j["legs"]) for j in view["nodes"]["Junction"].values())
    counts = {"nodes": {label: len(rows) for label, rows in view["nodes"].items()}, "junction_legs": legs,
              "edges": dict(sorted(collections.Counter(e["type"] for e in view["edges"].values()).items())),
              "placeholders": dict(collections.Counter(p["kind"] for p in view["nodes"]["Placeholder"].values())),
              "deltas": dict(collections.Counter(f"{d['stage']}/{d['method']}" for d in deltas))}
    dump("view-counts.json", counts)
    dump("papers.json", papers)
    body = {**{k: v for k, v in TEMPLATE.items() if k != "policy_id"}, "status": "EXPLORATORY", "importance_methods": ["DETERMINISTIC_ANCHOR"],
            "nomination": {"rule": "FOUNDATION_V1", "threshold": 2, "top_k": 25},
            "bootstrap": {"scheme": "PAPER_REWEIGHT_V1", "replicates": 100, "seed": "quant-ph-sample-bootstrap"}}
    policy = {**body, "policy_id": address("policy", body)}
    out = analysis.analyze(view, dm, policy, {})
    metrics = out["metrics"]
    dump("analysis-summary.json", {
        "policy": policy, "metrics_rows": len(metrics),
        "layers": dict(sorted(collections.Counter(str(r["layer"]) for r in metrics).items())),
        "route_status": dict(collections.Counter(r.get("route_status", "-") for r in metrics)),
        "diagnostics": {k: len(v) for k, v in out["diagnostics"].items() if isinstance(v, list)},
        "nominations": [{k: n[k] for k in ("list", "subject_kind", "subject_id", "layer", "dependent_papers", "next_action", "blockers",
                                             "rank_interval")} for n in out["nominations"]]})
    cited, in_proof = gates.works_cited(view, set(meta))
    rows_w = view["nodes"]["Work"]
    ident = lambda w: rows_w[w].get("doi") or rows_w[w].get("arxiv_base_id") or rows_w[w].get("openalex_id") or rows_w[w].get("bib_digest")
    dump("shared-works.json", {
        "identity": "EXPLICIT_IDS_ONLY host rules (arXiv id, DOI); other entries are BIB_DIGEST works, one per entry text",
        "citing_papers_histogram": dict(sorted(collections.Counter(len(ps) for ps in cited.values()).items())),
        "in_proof_citing_papers_histogram": dict(sorted(collections.Counter(len(ps) for ps in in_proof.values()).items())),
        "works_by_identity_basis": dict(collections.Counter(r["identity_basis"] for r in rows_w.values())),
        "shared": [{"work_id": w, "citing_papers": len(ps), "identity_basis": rows_w[w]["identity_basis"], "identifier": ident(w)}
                   for w, ps in sorted(cited.items(), key=lambda kv: (-len(kv[1]), kv[0])) if len(ps) >= 2]})
    grid = eligibility.grid(list(records.values()), *GRID)
    p1 = gates.p_minus_1(m, record, view, s3s, now(), grid=grid)
    dump("p-minus-1.json", p1)
    rows = projection.project(view, dm, {})
    dump("projection-rows.json", {"nodes": {g: len(rs) for g, rs in rows["nodes"].items()}, "rels": {t: len(rs) for t, rs in rows["rels"].items()}})
    log(f"built: {len(deltas)} deltas, invariant findings {len(findings)}, P-1 {p1['decision']}, view {counts['nodes']}")


def cmd_load():
    m, dm = manifest(), load("delta-set-manifest.json")
    view = delta.check_manifest(dm, delta.DeltaStore(DATA / "deltas"))
    rows = projection.project(view, dm, {})
    pm = projection.projection_manifest(dm, reviews.review_set_digest([]))
    client = projection.QueryClient(NEO4J, "neo4j", "neo4j", "")
    client.headers.pop("Authorization")  # the local test server runs with login disabled (127.0.0.1 only)
    ready = projection.load(client, rows, pm)
    dump("projection-manifest.json", ready)
    log(f"loaded {ready['id']}: state {ready['state']}, audits {sum(ready['audit_counts'][n] for n, _ in projection.AUDITS)} rows")


if __name__ == "__main__":
    {"sample": cmd_sample, "build": cmd_build, "load": cmd_load}[sys.argv[1]]()
