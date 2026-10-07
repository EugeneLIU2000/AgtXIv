# quant-ph test run, 2026-09-26: 50 theory papers through the deterministic tier, loaded into Neo4j

Owner's request (2026-09-26): download the Hugging Face copy of the arXiv metadata, draw 50 random quant-ph theory papers,
build the schema v0.4 dependencies, no formalisation, visualise in Neo4j. The owner then approved three downloads:
the sampled papers' arXiv sources, DuckDB 1.5.5, and a portable Java 21 JRE plus Neo4j Community 2026.09.0, all in
the git-ignored `local-archive/` of the main checkout. **No model was called**, so S6 (model extraction) and S7
(matching) did not run: every dependency here is a DETERMINISTIC_ANCHOR junction built from `\ref` and `\cite` inside
theorem-like and definition environments and their owned proofs (spec §7, S3). Times are UTC: metadata retrieved
2026-09-25T23:16Z, sample 23:23:51–23:28:37Z, build 23:30:56Z, load 23:31:15Z (01:16–01:31 local on 2026-09-26). The
build ran twice; the second run only fixed a summary count (identical deltas and ids). Worktree base commit 155e35d,
uncommitted.

## What was run

| Step | Command | Result |
|---|---|---|
| Metadata | `local-archive/arxiv-metadata/2026-09-21/fetch_snapshot.py` (copy, log and manifest in `../../snapshot/arxiv-metadata-2026-09-21/`; a pinned re-fetch script is `../../snapshot/fetch_arxiv_metadata.py`) | 10 Parquet files, 2,992,495,471 bytes, every SHA-256 equal to the one Hugging Face publishes; commit `90c265d5`, a weekly copy of Kaggle `Cornell-University/arxiv` v304 (2026-09-19). `MANIFEST.json` there. |
| Sample | `python run.py sample` | Frame: 76,946 papers with primary category quant-ph and v1 in 2015–2025. Seeded order (`order_key`, seed `agtxiv-v04-quant-ph-test-2026-09-26`), examined until 50 were ACCEPTED under THEOREM_OR_DERIVATION_V1 (≥ 1 theorem-like environment or ≥ 10 display equations): 80 examined, 50 accepted, 17 ineligible, 13 undetermined (7 MAIN_AMBIGUOUS, 3 NO_TEX_SOURCE: PDF-only, 3 PARSE_FAILED: non-UTF-8 source). 211.4 MB of e-prints from export.arxiv.org, one request start per 3 s. One arXiv API request confirmed the primary category of all 50 (`primary-category-check.json`). |
| Build | `python run.py build` | 151 deltas (S1 + 50 × S3 anchors, S3 restatements, S4 works). Host invariants G1–G15: **0 findings**. P-1 gate: **GO_WITH_EXPANSION**. |
| Load | `python run.py load` | Projection `projection:1fa9c298…` **READY** on the local Neo4j 2026.09.0; all 14 audits (G1–G5, G7–G15) returned **0 rows**. First execution of the v0.4 Cypher on a real server. |

## Findings

- **The deterministic tier is thin on quant-ph.** 36 of the 50 accepted papers qualify only through display equations and have no theorem-like environment; only 14 have one, and only 11 yield any junction. The 135 junctions (502 legs) come from those 11 papers, 50 of them from one paper (`2505.18701v1`). Of the 395 placeholders, 338 are `\eqref`s to equations (UNRESOLVED_OCCURRENCE) and 57 are citations inside proofs (EXTERNAL_REQUEST). Connecting derivation papers needs S6.
- **The papers do not connect yet.** No sample paper cites another (in-sample citation share 0). Of 2,899 cited works, 46 are cited by two sample papers and none by three, so the P-1 claim-level rule (≥ 20 works cited by ≥ 3 papers) fails: acquire the cited works (EXPANSION) or related papers (DISCOVERY) first. Work identity is strict. Of the 2,899 cited works, 1,247 are identified by DOI and 183 by arXiv id; 1,469 by BIB_DIGEST, a digest of (normalised title, year, first-author surname), which misses a work whenever one of the three differs between citing papers; and 1,182 of the 4,154 bibliography entries get no work at all because the title, year or author could not be read from the entry text.
- **Exploratory analysis** (importance from DETERMINISTIC_ANCHOR legs only): layers up to 6, no cycle, **no nomination**: no subject has dependents in two papers.
- **Acquisition.** 7 of 80 sources have several `.tex` files with `\begin{document}` and no `00README.json`, so the v0.3 main-file rule leaves them MAIN_AMBIGUOUS; 3 have a non-UTF-8 main file the v0.3 parser skips (correctly UNDETERMINED, not INELIGIBLE). Eligible fraction 0.746 (grid: 0.84 at m = 5, 0.58 at m = 20); undetermined fraction 0.1625.
- **Licences.** 13 of the 50 papers are OPEN (CC BY/BY-SA/CC0), 37 RESTRICTED; only the OPEN papers' environment text reaches Neo4j (I-13).

## Files

| File | What |
|---|---|
| `run.py` | The run script (three steps). |
| `corpus-manifest.json` | The frozen CorpusManifest (`corpus:24d8c5ea…`). |
| `frame-summary.json` | Frame size and papers per v1 year. |
| `examined.json` | Every examined candidate in order: outcome, counts, issue codes, snapshot metadata (titles only; no source text). |
| `sampling-record.json` | The SamplingRecord (`sampling:2d4be829…`). |
| `primary-category-check.json` | arXiv API primary category of the 50 accepted papers (50 of 50 quant-ph). |
| `delta-set-manifest.json` | The DeltaSetManifest of the 151 deltas (stored privately under `local-archive/corpus/quant-ph-sample-20260926/deltas`). |
| `invariants.json`, `view-counts.json`, `papers.json` | Host check result (empty), node and edge counts, per-paper yield. |
| `shared-works.json` | How many sample papers cite each work; the 46 works cited twice. |
| `analysis-summary.json` | Exploratory analysis: policy, layer distribution, diagnostics, nominations (none). |
| `p-minus-1.json` | The P-1 GateDecision. |
| `projection-rows.json`, `projection-manifest.json` | Rows sent to Neo4j and the READY ProjectionManifest with every audit count. |
| `views.cypher` | The Neo4j Browser views used for the visual check. |
| `browse_check.py`, `browse-check.json` | Every `neo4j/browse.cypher` template run once on the loaded projection: all five accepted (premises 67 paths, dependents 3, junctions 10, paper_claims 19, work_requests 1). |
| `sample.out`, `build.out`, `load.out`, `run.log` | Console output of the three steps. |

## Neo4j

- Server: `local-archive/tools/neo4j-community-2026.09.0`, Java `local-archive/tools/jdk-21.0.12.1+1-jre`, listening on
  127.0.0.1 only, login disabled (`conf/neo4j.conf`; the shipped file is kept as `neo4j.conf.orig`).
- Browser: http://127.0.0.1:7474/browser/ → Connect (no password). Queries in `views.cypher`.
- One claim in the chain-build encoding: `../../viewer/claim-view.html`, served over http (for example
  http://127.0.0.1:8765/schema%20v0.4/viewer/claim-view.html). Two examples: `#claim:9e8aab9f6d82…` (2505.18701v1,
  theorem at line 602: 29 junctions, top layer L6, no leg leaves the paper) and `#claim:b22535e113dc…`
  (2107.06411v1, theorem at line 1688: 7 junctions, 5 legs to cited works that no source junction resolves yet).
- Start / stop:

```sh
export JAVA_HOME="/Users/Yingjian/Documents/GitHub/AgtXIv/local-archive/tools/jdk-21.0.12.1+1-jre/Contents/Home"
/Users/Yingjian/Documents/GitHub/AgtXIv/local-archive/tools/neo4j-community-2026.09.0/bin/neo4j stop
```

- Remove everything this run installed: delete `local-archive/tools/`; DuckDB was added to `.venv` with `uv pip install`
  (not in `pyproject.toml` or `uv.lock`; a later `uv sync` removes it).

## Reproduce

From this folder, with the project interpreter: `PYTHONDONTWRITEBYTECODE=1 …/.venv/bin/python run.py sample`, then
`build`, then `load` (Neo4j running). A second `sample` reuses the frozen manifest and the acquired sources (no new
e-print download, one new arXiv API request for the category check) and examines the same candidates with the same
outcomes; the SamplingRecord id changes with its `created_at`. The metadata snapshot is pinned by `MANIFEST.json`.
