"""Owner-requested run (2026-09-26): S6, EXPANSION and S7, in that order, on the 50-paper quant-ph sample of
runs/quant-ph-sample-20260926, with the current Claude model reading instead of an external model. The owner's words:
"依次做S6、EXPANSION、S7，先不调用外部模型而是用目前的模型单独一个agent". Every model reading therefore comes from one
Claude Code subagent at a time (the session's model, claude-opus-5-5), started fresh for each paper (S6) or each batch
of request pools (S7) like one independent model call; no external provider route (MiMo, GPT) is used.

Operations, prompts, response schemas and host checks are the v0.4 ones (extraction.py, matching.py). The transport
differs, and every receipt records how: the agent reads a package that renders the same prompt data as files (the
instruction verbatim, every source file, the alias inventory, the bibliography keys, the focus blocks); it answers all
foci of a paper in one context, where a provider would see each focus in its own call over a cached prefix; it may
count a quotation's occurrences in the paper's own files; the session meters it, not the call (usage UNMETERED).

    python run.py manifest        freeze the successor CorpusManifest: the first run's frame, seed and rules; the S6
                                  method_version names the transport; a ceiling in agent calls
    python run.py sample          round 0 from the first run's examined outcomes (same sources and program; no network)
    python run.py base            S1 INCLUDES, S3 anchors and restatements, S4 works of every accepted paper of every round
    python run.py s6-plan         S6 packages and ledger items for accepted papers without them
    python run.py s6-next         reserve the next paper's READY items; print its package and dispatch file
    python run.py s6-ingest PV AGENT
                                  settle them from the agent's responses; accepted responses become S6 deltas
    python run.py expand-select   metadata-DOI SAME_WORK delta, an exploratory analysis, the frozen selection (round 1)
    python run.py expand-acquire  acquire and examine the selection (export.arxiv.org, one request start per 3 s)
    python run.py s7-plan         pools of requests whose upstream paper version is in the corpus; packages, ledger items
    python run.py s7-next         reserve the next batch of pools; s7-ingest BATCH AGENT settles it
    python run.py build           delta set, invariants, analysis, coverage, projection rows, summaries
    python run.py load            load the projection into the local Neo4j

Private artifacts (packages, responses, receipts, deltas, the ledger: they hold verbatim e-print text) stay under
local-archive/ in the main checkout, which git ignores; this folder keeps records without e-print text (I-13).
"""
import collections
import datetime as dt
import json
import sys
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
import extraction  # noqa: E402
import invariants  # noqa: E402
import ledger  # noqa: E402
import matching  # noqa: E402
import projection  # noqa: E402
import reviews  # noqa: E402
import works  # noqa: E402
from delta import address  # noqa: E402

FIRST = V04 / "runs" / "quant-ph-sample-20260926"
REPO = Path("/Users/Yingjian/Documents/GitHub/AgtXIv")  # main checkout: the v0.3 reader needs sources inside the repository
SNAPSHOT = REPO / "local-archive/arxiv-metadata/2026-09-21"
PAPERS = REPO / "local-archive/corpus/quant-ph-sample-20260926/papers"  # shared paper store: sources and S2 records
DATA = REPO / "local-archive/corpus/quant-ph-claude-agent-20260926"  # this run's private artifacts
NEO4J = "http://127.0.0.1:7474"
SNAP = json.loads((SNAPSHOT / "MANIFEST.json").read_text())
SNAP_LABEL = f"arXiv metadata snapshot (Kaggle Cornell-University/arxiv v304 via {SNAP['source']}@{SNAP['commit'][:12]})"
MODEL, TRANSPORT = "claude-opus-5-5", "CLAUDE_CODE_SUBAGENT"
TRAINING_CUTOFF = {"value": "2026-06", "source": "the running model's system prompt (knowledge cutoff June 2026)"}
S6_VERSION, S7_VERSION = "focus-1/claude-opus-5-5-subagent", "match-1/claude-opus-5-5-subagent"
FOCUS_BYTES = 8192
CEILING = 1500  # agent calls, one per focus or pool attempt: a bound, not a forecast
MAX_ATTEMPTS, LEASE_SECONDS = 2, 6 * 3600
PROVIDER, ACCOUNT = "claude-code-session", "local"
EXPANSION_M = 25
EXPANSION_RULE = ("EXPANSION_REQUESTED_WORKS_V1: arXiv works (terminal_kind ARXIV_SOURCE_AVAILABLE) in the EXPLICIT_IDS_ONLY "
                  "work component of a work that an EXTERNAL_REQUEST of a SAMPLE paper resolves to, not examined in an earlier "
                  "round; ordered by the number of distinct requesting sample papers (descending), then by "
                  "order_key(<manifest seed>/expansion/1, arxiv_base_id); the first M")
S7_K = 10  # candidates retrieved per request (matching.retrieve_candidates)
PACKAGE_VERSION = "AGENT_PACKAGE_V2"  # V2 states every host check in TASK.md section 5 (V1, used for the first paper only, did not)
POOLS_PER_BATCH = 8
NOTE_CODES = {"MODEL_UNRESOLVED_DEPENDENCY", "MODEL_UNCERTAIN_SCOPE", "MODEL_SELF_SUPPORT_DROPPED"}  # issues of accepted responses
now = lambda: dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---- files ---------------------------------------------------------------------------------------------------------

def dump(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def load(name, default=None):
    path = HERE / name
    return json.loads(path.read_text()) if path.exists() else default


def log(line):
    print(line, flush=True)
    with (HERE / "run.log").open("a") as handle:
        handle.write(f"{now()} {line}\n")


def write_private(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else (value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1)).encode()
    path.write_bytes(data)
    return path


def artifact(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(REPO)), "sha256": digest(data), "byte_size": len(data)}


def short(any_id):
    return any_id.split(":")[-1][:16]


def pvdir(pv):
    return pv.removeprefix("arxiv:").replace("/", "_")


def home(pv):
    base, version = pv.removeprefix("arxiv:").rsplit("v", 1)
    return PAPERS / base.replace("/", "_") / f"v{version}"


def paper(pv):
    rec = json.loads((home(pv) / "extraction" / "extraction.json").read_text())
    return rec, {r["path"]: (REPO / r["path"]).read_bytes() for r in rec["source_files"]}


def parser_sha256():
    parts = {"schema v0.3/host/ingest.py": REPO / "schema v0.3/host/ingest.py", "schema v0.3/host/bibtex.py": REPO / "schema v0.3/host/bibtex.py",
             "tools/extract_provisional_claims.py": REPO / "tools/extract_provisional_claims.py", "src/agtxiv_v3/source.py": REPO / "src/agtxiv_v3/source.py"}
    return digest(canonical({name: ingest._sha(path.read_bytes()) for name, path in parts.items()}))


def manifest():
    return corpus.check_corpus_manifest(load("corpus-manifest.json"))


def rounds():
    return [load(f"sampling-record-round{n}.json") for n in range(2) if (HERE / f"sampling-record-round{n}.json").exists()]


def examined_rows(record):
    return json.loads((FIRST / "examined.json").read_text()) if record["round"] == 0 else load(f"examined-round{record['round']}.json")


def accepted_meta(record):
    return {row["paper_version_id"]: row["metadata"] for row in examined_rows(record) if row["outcome"]["outcome"] == "ACCEPTED"}


def open_ledger():
    return ledger.CorpusLedger(DATA / "ledger.sqlite", manifest(), max_attempts_per_item=MAX_ATTEMPTS, lease_seconds=LEASE_SECONDS)


def store():
    return delta.DeltaStore(DATA / "deltas")


def record_deltas(*deltas):
    """Store deltas and append their ids to deltas.json, the run's delta list in the order they were made."""
    listed, st = load("deltas.json", []), store()
    for d in deltas:
        st.put(d)
        if d["delta_id"] not in listed:
            listed.append(d["delta_id"])
    dump("deltas.json", listed)


def current_view():
    dm = delta.make_manifest(manifest()["corpus_id"], load("deltas.json", []), created_at=now())
    return dm, delta.check_manifest(dm, store())


def exploratory_policy():
    template = manifest()["primary_analysis_policy"]
    body = {**{k: v for k, v in template.items() if k != "policy_id"}, "status": "EXPLORATORY",
            "importance_methods": ["DETERMINISTIC_ANCHOR", "MODEL_EXTRACTION", "MODEL_MATCH"],
            "nomination": {"rule": "FOUNDATION_V1", "threshold": 2, "top_k": 25},
            "bootstrap": {"scheme": "PAPER_REWEIGHT_V1", "replicates": 100, "seed": "quant-ph-claude-agent-bootstrap"}}
    return {**body, "policy_id": address("policy", body)}


def line_of(data, byte):
    return data.count(b"\n", 0, byte) + 1


# ---- S0, round 0, deterministic tier -------------------------------------------------------------------------------

def cmd_manifest():
    if (HERE / "corpus-manifest.json").exists():
        log(f"corpus {manifest()['corpus_id']} (already frozen)")
        return
    first = corpus.check_corpus_manifest(json.loads((FIRST / "corpus-manifest.json").read_text()))
    if (first["eligibility"]["parser_sha256"], first["eligibility"]["program_sha256"]) != (parser_sha256(), eligibility.program_sha256()):
        raise SystemExit("the parser or the eligibility program changed since the first run: round 0 cannot reuse its outcomes")
    keep = {k: v for k, v in first.items() if k not in ("kind", "contract_version", "corpus_id", "extraction", "budget_ceiling", "created_at")}
    m = corpus.freeze_corpus_manifest({**keep, "extraction": {"operation": "paper.extract_focus", "method_version": S6_VERSION, "focus_bytes": FOCUS_BYTES},
                                       "budget_ceiling": {"unit": "agent_calls", "value": CEILING}, "created_at": now()})
    dump("corpus-manifest.json", m)
    log(f"corpus {m['corpus_id']} (successor of {first['corpus_id']})")


def cmd_sample():
    m = manifest()
    frame = acquire.snapshot_frame(str(SNAPSHOT / "*.parquet"), m["field"])
    outcomes = {row["arxiv_base_id"]: row["outcome"] for row in json.loads((FIRST / "examined.json").read_text())}
    record = corpus.sample_record(m, sorted(frame), outcomes, now())
    dump("sampling-record-round0.json", record)
    log(f"round 0 {record['sampling_record_id']}: {corpus.estimand_counts(record)} (frame {len(frame)}; outcomes of the first run)")


def cmd_base():
    m, base = manifest(), load("base.json", {})
    for record in rounds():
        meta = accepted_meta(record)
        s1 = corpus.includes_delta(record, m, meta)
        record_deltas(s1)
        for pv in sorted(meta):
            if pv in base:
                continue
            rec, sources = paper(pv)
            s3 = anchors.build_anchor_delta(rec, sources, parents=[s1["delta_id"]])
            restates, s4 = anchors.build_restates_delta(rec, sources, s3), works.build_work_delta(s3, rec)
            record_deltas(s3, restates, s4)
            base[pv] = {"round": record["round"], "s1": s1["delta_id"], "s3": s3["delta_id"], "restates": restates["delta_id"], "s4": s4["delta_id"]}
    dump("base.json", base)
    log(f"base: {len(base)} papers with S1/S3/S4 deltas; {len(load('deltas.json', []))} deltas listed")


# ---- S6 --------------------------------------------------------------------------------------------------------------

S6_TASK = """# S6 reading task: {pv}

You are the reading model of one operation in a research pipeline (schema v0.4, stage S6). The host records your answer
as model readings (method MODEL_EXTRACTION, method_version {version}) only after its own checks; nothing you write is
taken as true. The owner of the project asked for this run and for these readings to come from you.

## 1. The operation (verbatim)

{instruction}

## 2. The paper data

The whole paper is the files below; read all of them before answering. A file marked context_only (a bibliography or a
file that is not UTF-8) is read for context and never quoted.

| path to name in source_locators | read it at | note |
|---|---|---|
{files}

- `inventory.tsv` names every occurrence of the paper once: alias, kind, path, byte_start, byte_end, first_line,
  last_line. Byte spans are authoritative; the 1-based line numbers only help you find the text.
- `bibliography_keys.txt`: the citation keys of the paper's bibliography, one per line.
- `foci.json`: every focus of the paper: focus_id, path, byte_start, byte_end, first_line, last_line, and occurrences
  (the aliases that begin inside it).

## 3. What to write

Answer the foci that the dispatch file (named in your instructions) lists, each as its own call would be answered: one
response object per focus, valid under the JSON Schema in `response.schema.json`. The aliases (o1, o2, ...) are the ids
in source_occurrence_ids and internal_support_occurrence_ids; internal_support_claim_indexes count claims of the same
focus response. Write every response to the responses file the dispatch names, as one JSON object
{{"<focus_id>": <response>, ...}} with exactly one entry per listed focus.

## 4. How to work (transport rules; they do not change the operation)

1. Read only the files named in this package. Do not open any other file (other papers, other packages, program code,
   graph outputs, notes) and do not use the web.
2. exact_text is copied byte for byte from its file: the line-number prefix the Read tool shows is not part of the
   text, and backslashes, braces, spaces and line breaks are kept exactly. A quotation must occur exactly once in its
   file and not inside a TeX comment. You may count a quotation's occurrences in its file (grep -c -F, or a one-line
   Python count); run nothing else on the paper.
3. Write valid JSON (escape backslashes, quotes and line breaks). You may write the file with a short Python script and
   check that it parses with `python3 -m json.tool <file> > /dev/null`.
4. Answer every listed focus. A focus that states no claim gets {{"claims": [], "unread_or_uncertain_scope": ["<why>"]}}.
5. When the responses file is complete, reply with one line: the number of foci answered and of claims emitted.

## 5. What the host rejects

These are the host's checks, stated in full. One failed check rejects the whole response of that focus, and every claim
in it is lost.

1. The response does not satisfy `response.schema.json`.
2. A `source_occurrence_ids` entry is not one of the focus's own occurrences (the `occurrences` list in `foci.json`).
3. An alias that is not in `inventory.tsv`, or a citation key that is not in `bibliography_keys.txt`; a key in both
   external_citation_keys and external_mention_citation_keys; a repeated value inside one list; an empty statement or
   an empty list item; an internal_support_claim_indexes entry that is the claim itself or not a claim of this response;
   a confidence outside [0, 1].
4. A claim with neither source_occurrence_ids nor source_locators.
5. A quotation (exact_text) that is not in its file, occurs more than once in its file, lies inside a TeX comment, or
   lies outside the focus span (the focus's byte_start to byte_end).
6. Shared occurrences. A claim uses an occurrence when it names it in source_occurrence_ids, or, if it names none,
   when one of its quotations lies inside it. When two or more claims use the same occurrence, each of them must use
   only that one occurrence and quote a passage inside it, and their quotations must start at different places. A
   claim that uses several occurrences therefore shares none of them with another claim. In practice: give each claim
   the one occurrence where it is stated (a display equation for an equation, the paragraph for a prose statement);
   quote a passage inside that occurrence whenever the occurrence holds more than one claim; and put the other
   occurrences a claim relies on in internal_support_occurrence_ids.
7. A focus with no claims and no unread_or_uncertain_scope entry.
"""


def write_s6_package(pv, rec, sources, built, pkg):
    P = anchors.index(rec, sources)
    rel = {anchors.rel(P, path): path for path in sources}
    first = built["prompts"][0]["context"]
    rows, files = [], []
    for path in sorted(sources):
        if not path.lower().endswith(extraction.BODY_SUFFIXES + extraction.CONTEXT_SUFFIXES):
            continue
        try:
            sources[path].decode("utf-8")
            note = "context_only" if path.lower().endswith(extraction.CONTEXT_SUFFIXES) else ""
        except UnicodeDecodeError:
            note = "context_only (not UTF-8)"
        files.append({"path": anchors.rel(P, path), "read_at": str(REPO / path), "note": note})
    for row in first["inventory"]:
        if row["role"] in ("ENVIRONMENT", "REFERENCED"):
            data = sources[rel[row["path"]]]
            rows.append([row["alias"], row["kind"], row["path"], row["byte_start"], row["byte_end"],
                         line_of(data, row["byte_start"]), line_of(data, max(row["byte_start"], row["byte_end"] - 1))])
    rows.sort(key=lambda r: int(r[0][1:]))
    foci = []
    for prompt in built["prompts"]:
        focus = next(row for row in prompt["context"]["inventory"] if row["role"] == "FOCUS")
        data = sources[rel[focus["path"]]]
        foci.append({"focus_id": prompt["focus_id"], "path": focus["path"], "byte_start": focus["byte_start"], "byte_end": focus["byte_end"],
                     "first_line": line_of(data, focus["byte_start"]), "last_line": line_of(data, max(focus["byte_start"], focus["byte_end"] - 1)),
                     "occurrences": [row["alias"] for row in prompt["context"]["inventory"] if row["role"] == "ENVIRONMENT"]})
    keys = sorted({row["key"] for row in first["bibliography"]})
    task = S6_TASK.format(pv=pv, version=S6_VERSION, instruction="> " + extraction.FOCUS_INSTRUCTION,
                          files="\n".join(f"| {f['path']} | {f['read_at']} | {f['note']} |" for f in files))
    parts = {"TASK.md": task, "inventory.tsv": "alias\tkind\tpath\tbyte_start\tbyte_end\tfirst_line\tlast_line\n" + "".join("\t".join(map(str, r)) + "\n" for r in rows),
             "foci.json": json.dumps(foci, indent=1), "bibliography_keys.txt": "".join(k + "\n" for k in keys),
             "response.schema.json": json.dumps(extraction.RESPONSE_SCHEMA, indent=1)}
    for name, text in parts.items():
        write_private(pkg / name, text)
    write_private(pkg / "prompts.jsonl", "".join(json.dumps({"focus_id": p["focus_id"], "prompt": p["prompt"]}, ensure_ascii=False) + "\n" for p in built["prompts"]))
    return digest(canonical({"package": {name: digest(text.encode()) for name, text in parts.items()},
                             "files": {f["path"]: digest(sources[rel[f["path"]]]) for f in files}}))


def cmd_s6_plan():
    base, plan = load("base.json", {}), load("s6-plan.json", {})
    lg = open_ledger()
    try:
        for pv in sorted(base):
            if pv in plan:
                continue
            rec, sources = paper(pv)
            built = extraction.build_focus_prompts(rec, sources, focus_bytes=FOCUS_BYTES)
            pkg = DATA / "s6" / pvdir(pv)
            package_sha256 = write_s6_package(pv, rec, sources, built, pkg)
            foci = [{"focus_id": p["focus_id"], "prompt_sha256": digest(p["prompt"].encode()), "prompt_bytes": len(p["prompt"].encode()),
                     "key": lg.add("S6", "CLAIM_BATCH", p["focus_id"], "MODEL_EXTRACTION", S6_VERSION, digest(p["prompt"].encode()))}
                    for p in built["prompts"]]
            plan[pv] = {"round": base[pv]["round"], "package": str(pkg.relative_to(REPO)), "package_sha256": package_sha256,
                        "prefix_sha256": built["prefix_sha256"], "prefix_bytes": built["prefix_bytes"], "foci": foci}
    finally:
        lg.close()
    dump("s6-plan.json", plan)
    log(f"s6 plan: {len(plan)} papers, {sum(len(p['foci']) for p in plan.values())} foci")


def cmd_s6_next():
    plan = load("s6-plan.json", {})
    lg = open_ledger()
    try:
        for pv, entry in plan.items():
            ready = [f for f in entry["foci"] if (item := lg.item(f["key"]))["state"] == "READY" and item["dispatchable"]]
            if not ready:
                continue
            pkg = REPO / entry["package"]
            n = len(list(pkg.glob("dispatch-*.json"))) + 1
            reservations = {f["focus_id"]: lg.reserve(f["key"], provider=PROVIDER, account_ref=ACCOUNT, amount=1)["id"] for f in ready}
            dispatch = {"paper_version_id": pv, "dispatch": n, "reserved_at": now(), "foci": [f["focus_id"] for f in ready],
                        "reservations": reservations, "responses_file": f"responses-{n}.json"}
            write_private(pkg / f"dispatch-{n}.json", dispatch)
            print(json.dumps({"paper_version_id": pv, "package": str(pkg), "dispatch_file": str(pkg / f"dispatch-{n}.json"),
                              "responses_file": str(pkg / dispatch["responses_file"]), "foci": len(ready), "prefix_bytes": entry["prefix_bytes"]}))
            log(f"s6 dispatch {pv} #{n}: {len(ready)} foci reserved")
            return
        print("{}")
    finally:
        lg.close()


def cmd_s6_ingest(pv, agent_ref):
    plan, base, results = load("s6-plan.json"), load("base.json"), load("s6-results.json", {})
    entry = plan[pv]
    pkg = REPO / entry["package"]
    n = max(int(p.stem.split("-")[1]) for p in pkg.glob("dispatch-*.json"))
    if (pkg / f"ingested-{n}.json").exists():
        raise SystemExit(f"dispatch {n} of {pv} is already ingested")
    dispatch = json.loads((pkg / f"dispatch-{n}.json").read_text())
    try:
        responses = json.loads((pkg / dispatch["responses_file"]).read_text())
        read_error = None if isinstance(responses, dict) else "RESPONSES_NOT_AN_OBJECT"
    except (OSError, ValueError) as error:
        responses, read_error = {}, "RESPONSES_UNREADABLE: " + type(error).__name__
    rec, sources = paper(pv)
    prompts = {p["focus_id"]: p for p in extraction.build_focus_prompts(rec, sources, focus_bytes=FOCUS_BYTES)["prompts"]}
    summary = []
    lg = open_ledger()
    try:
        for fid in dispatch["foci"]:
            prompt, response = prompts[fid], (responses.get(fid) if not read_error else None)
            rfile = write_private(pkg / "responses" / f"{short(fid)}-{n}.json", canonical(response)) if response is not None else None
            receipt = {"reservation_id": dispatch["reservations"][fid], "operation": extraction.FOCUS_OPERATION, "model": MODEL,
                       "transport": TRANSPORT, "agent_ref": agent_ref, "training_cutoff": TRAINING_CUTOFF,
                       "prompt_sha256": digest(prompt["prompt"].encode()), "prefix_sha256": entry["prefix_sha256"],
                       "package_sha256": entry["package_sha256"], "response_sha256": rfile and digest(rfile.read_bytes()),
                       "dispatched_at": dispatch["reserved_at"], "settled_at": now(), "usage": "UNMETERED",
                       "rendering": PACKAGE_VERSION + ": the prompt's instruction, files, inventory, keys and focus block as files, plus the host checks; all foci of the paper in one agent context"}
            receipt_file = write_private(pkg / "receipts" / f"{short(fid)}-{n}.json", canonical(receipt))
            codes = collections.Counter()
            if response is None:
                d, failure = None, "RESPONSE_REJECTED"
                codes[read_error or "RESPONSE_MISSING"] += 1
            else:
                d = extraction.focus_response_to_delta(rec, sources, prompt["context"], response, method_version=S6_VERSION,
                                                       parents=[base[pv]["s1"]], produced_by=[artifact(receipt_file), artifact(rfile)])
                record_deltas(d)
                codes.update(i["code"] for i in d["issues"])
                failure = "RESPONSE_REJECTED" if not d["nodes"] and set(codes) - NOTE_CODES else None
            state = lg.settle(dispatch["reservations"][fid], receipt, failure=failure, cost=1)
            nodes = (d or {}).get("nodes", {})
            junctions = nodes.get("Junction", [])
            summary.append({"paper_version_id": pv, "focus_id": fid, "dispatch": n, "state": state, "accepted": failure is None,
                            "claims_emitted": len(response.get("claims", [])) if isinstance(response, dict) and isinstance(response.get("claims"), list) else None,
                            "readings": len(nodes.get("ClaimReading", [])), "junctions": len(junctions), "legs": sum(len(j["legs"]) for j in junctions),
                            "external_requests": sum(p["kind"] == "EXTERNAL_REQUEST" for p in nodes.get("Placeholder", [])),
                            "issue_codes": dict(sorted(codes.items())), "delta_id": d and d["delta_id"]})
    finally:
        lg.close()
    for row in summary:
        results[f"{row['focus_id']}#{row['dispatch']}"] = row
    dump("s6-results.json", results)
    write_private(pkg / f"ingested-{n}.json", {"ingested_at": now(), "agent_ref": agent_ref, "summary": summary})
    ok = sum(r["accepted"] for r in summary)
    log(f"s6 ingest {pv} #{n}: {ok}/{len(summary)} accepted, {sum(r['readings'] for r in summary)} readings, "
        f"{sum(r['junctions'] for r in summary)} junctions, {sum(r['external_requests'] for r in summary)} requests"
        + ("" if ok == len(summary) else f"; rejected codes {collections.Counter(c for r in summary if not r['accepted'] for c in r['issue_codes'])}"))


# ---- EXPANSION ---------------------------------------------------------------------------------------------------------

def requested_arxiv_works(view, citing_papers):
    """{arxiv base id: requesting papers} over EXTERNAL_REQUESTs of citing_papers, through RESOLVES_TO and the
    EXPLICIT_IDS_ONLY work components, keeping arXiv works with ARXIV_SOURCE_AVAILABLE."""
    edges = view["edges"].values()
    req_from = {e["start_id"]: e["end_id"] for e in edges if e["type"] == "REQUESTS_FROM"}
    resolves = {e["start_id"]: e["end_id"] for e in edges if e["type"] == "RESOLVES_TO"}
    rows, comps, out = view["nodes"]["Work"], invariants.work_components(view, "EXPLICIT_IDS_ONLY"), collections.defaultdict(set)
    for ph in view["nodes"]["Placeholder"].values():
        work = ph["kind"] == "EXTERNAL_REQUEST" and ph["paper_version_id"] in citing_papers and resolves.get(req_from.get(ph["id"]))
        for member in comps.get(work, {work}) if work else ():
            row = rows[member]
            if row["identity_basis"] == "ARXIV_BASE" and row["terminal_kind"] == "ARXIV_SOURCE_AVAILABLE":
                out[row["arxiv_base_id"]].add(ph["paper_version_id"])
    return out


def cmd_expand_select():
    m, (round0,) = manifest(), rounds()[:1]
    dm, view = current_view()
    parents = sorted({b["s4"] for b in load("base.json").values()})
    dois = sorted({w["doi"] for w in view["nodes"]["Work"].values() if w["identity_basis"] == "DOI" and not works.doi_arxiv(w["doi"])})
    index = acquire.snapshot_dois(str(SNAPSHOT / "*.parquet"), dois, works.normalize_doi)
    md = works.build_metadata_doi_delta(view["nodes"]["Work"].values(), index, "sha256:" + SNAP["manifest_sha256"], parents=parents)
    record_deltas(md)
    dm, view = current_view()
    policy = exploratory_policy()
    out = analysis.analyze(view, dm, policy, {})
    sample = {row["paper_version_id"] for row in round0["candidates"] if row["outcome"] == "ACCEPTED"}
    examined = {row["arxiv_base_id"] for record in rounds() for row in record["candidates"]}
    wanted = requested_arxiv_works(view, sample)
    seed = m["seed"] + "/expansion/1"
    order = sorted((b for b in wanted if b not in examined), key=lambda b: (-len(wanted[b]), corpus.order_key(seed, b)))
    selected = order[:EXPANSION_M]
    meta = acquire.snapshot_rows(str(SNAPSHOT / "*.parquet"), order)
    requests = [p for p in view["nodes"]["Placeholder"].values() if p["kind"] == "EXTERNAL_REQUEST" and p["paper_version_id"] in sample]
    dump("expansion-plan.json", {
        "rule": EXPANSION_RULE, "M": EXPANSION_M, "seed": seed, "created_at": now(),
        "expansion": {"source_manifest_id": dm["manifest_id"], "analysis_run": {"policy_id": policy["policy_id"], "manifest_id": dm["manifest_id"]},
                      "selection_rule": EXPANSION_RULE, "M": EXPANSION_M},
        "metadata_doi_delta": {"delta_id": md["delta_id"], "dois_checked": len(dois), "dois_found": len(index),
                               "same_work_edges": len(md["edges"]), "ambiguous": len(md["issues"])},
        "sample_requests": len(requests), "requested_arxiv_works": len(wanted), "already_examined": sorted(set(wanted) & examined),
        "candidates": [{"arxiv_base_id": b, "requesting_sample_papers": sorted(wanted[b]), "selected": b in selected,
                        "title": (meta.get(b) or {}).get("title"), "in_snapshot": b in meta} for b in order],
        "selected": selected, "analysis": {"layers": dict(sorted(collections.Counter(str(r["layer"]) for r in out["metrics"]).items())),
                                           "nominations": len(out["nominations"])}})
    log(f"expansion select: {len(requests)} sample requests; {len(wanted)} requested arXiv works; {len(order)} not yet examined; "
        f"selected {len(selected)} (M={EXPANSION_M}); metadata DOI edges {len(md['edges'])}")


def cmd_expand_acquire():
    m, plan, (round0,) = manifest(), load("expansion-plan.json"), rounds()[:1]
    rows = acquire.snapshot_rows(str(SNAPSHOT / "*.parquet"), plan["selected"])
    token = acquire.RateToken(m["size_limits"]["min_request_interval_seconds"])
    outcomes, examined = {}, load("examined-round1.json", [])
    done = {row["arxiv_base_id"]: row for row in examined}
    for base in plan["selected"]:
        if base in done:
            outcomes[base] = done[base]["outcome"]
            continue
        if base not in rows:
            res = {"outcome": {"outcome": "UNDETERMINED", "attempts": 1, "undetermined_class": "ID_NOT_FOUND"}, "paper_version_id": None,
                   "decision": None, "issues": [], "metadata": None}
        else:
            res = acquire.examine(REPO, base, rows[base], m, PAPERS, token, snapshot_label=SNAP_LABEL)
        outcomes[base] = res["outcome"]
        decision = res.get("decision") or {}
        examined.append({"n": len(examined) + 1, "arxiv_base_id": base, "paper_version_id": res["paper_version_id"],
                         "title": (rows.get(base) or {}).get("title"), "categories": (rows.get(base) or {}).get("categories"),
                         "license": (rows.get(base) or {}).get("license"), "outcome": res["outcome"], "counts": decision.get("counts"),
                         "issues": sorted({i["code"] for i in res["issues"]}), "metadata": res["metadata"]})
        dump("examined-round1.json", examined)
        log(f"expansion {len(examined):3d} {str(res['paper_version_id']):24s} {res['outcome']['outcome']:12s} "
            f"{res['outcome'].get('undetermined_class') or res['outcome'].get('reason') or decision.get('counts') or ''}")
    work_rows = [works.work_row("ARXIV_BASE", base) for base in plan["selected"]]
    record = corpus.expansion_record(m, [round0], plan["expansion"], work_rows, outcomes, now())
    dump("sampling-record-round1.json", record)
    log(f"round 1 {record['sampling_record_id']}: {collections.Counter(r['outcome'] for r in record['candidates'])}")


# ---- S7 ----------------------------------------------------------------------------------------------------------------

S7_TASK = """# S7 matching task: batch {batch}

You are the reading model of one operation in a research pipeline (schema v0.4, stage S7). The host records your answers
as model matches (method MODEL_MATCH, method_version {version}) only after its own checks; nothing you write is taken as
true. The owner of the project asked for this run and for these matches to come from you.

## 1. The operation (verbatim)

{instruction}

## 2. The data

Each pool below is one call. Its `data.json` is that call's SOURCE DATA: the upstream paper version, the external requests
of citing papers (each with the citing claim's text, the `\\cite` locator text when there is one, and the ids of the
candidates retrieved for it) and the candidate statements of the upstream paper (claim id, occurrence ids, kind, text).

{pools}

## 3. What to write

One response per pool, valid under the JSON Schema in `response.schema.json`, written to the responses file the
dispatch names as one JSON object {{"<pool_id>": <response>, ...}} with exactly one entry per listed pool. In
source_quotes, path is the candidate's claim id and exact_text is copied byte for byte from that candidate's text.

## 4. How to work (transport rules; they do not change the operation)

1. Read only the files named in this task. Do not open any other file and do not use the web.
2. Write valid JSON (escape backslashes, quotes and line breaks). You may write the file with a short Python script and
   check that it parses with `python3 -m json.tool <file> > /dev/null`; you may count a quotation's occurrences in a
   candidate text with a one-line Python count. Run nothing else.
3. When the responses file is complete, reply with one line: pools answered, CANDIDATE_SUPPORT rows, other rows.
"""


def citing_reading(readings):
    """The reading a request's citing claim shows the matcher: this run's model reading if it has text, else the
    deterministic one (environment text)."""
    ranked = sorted((r for r in readings if r.get("display_text")), key=lambda r: (r["method"] != "MODEL_EXTRACTION", r["id"]))
    return ranked[0] if ranked else None


def cmd_s7_plan():
    if load("s7-plan.json"):
        raise SystemExit("the S7 plan is frozen")
    dm, view = current_view()
    nodes, edges = view["nodes"], view["edges"].values()
    req_from = {e["start_id"]: e["end_id"] for e in edges if e["type"] == "REQUESTS_FROM"}
    resolves = {e["start_id"]: e["end_id"] for e in edges if e["type"] == "RESOLVES_TO"}
    comps, W = invariants.work_components(view, "EXPLICIT_IDS_ONLY"), nodes["Work"]
    pv_of = {row["arxiv_base_id"]: pv for pv, row in nodes["PaperVersion"].items()}
    stated, readings = collections.defaultdict(list), collections.defaultdict(list)
    for e in edges:
        if e["type"] == "STATES":
            stated[e["start_id"]].append(e["end_id"])
    for r in nodes["ClaimReading"].values():
        readings[r["claim_id"]].append(r)
    pools, outside = collections.defaultdict(list), 0
    for ph in sorted(nodes["Placeholder"].values(), key=lambda p: p["id"]):
        if ph["kind"] != "EXTERNAL_REQUEST":
            continue
        work = resolves.get(req_from.get(ph["id"]))
        ups = {pv_of[W[w]["arxiv_base_id"]] for w in (comps.get(work, {work}) if work else ())
               if W[w]["identity_basis"] == "ARXIV_BASE" and W[w]["arxiv_base_id"] in pv_of} - {ph["paper_version_id"]}
        outside += not ups
        for up in ups:
            pools[up].append(ph)
    lg, planned, empty = open_ledger(), {}, []
    try:
        for up, reqs in sorted(pools.items()):
            pairs = [(nodes["Claim"][c], r) for c in stated[up] for r in readings[c]]
            items = []
            for req in reqs:
                cite = citing_reading(readings[req["created_by_claim_id"]])
                found = matching.retrieve_candidates(req, cite, pairs, S7_K)
                (items.append({"request": req, "citing": cite, "candidates": found}) if found else empty.append(req["id"]))
            if not items:
                continue
            built = matching.build_match_prompt(up, items)
            pool = built["context"]["pool_id"]
            pkg = DATA / "s7" / short(pool)
            write_private(pkg / "data.json", built["context"])
            write_private(pkg / "prompt.txt", built["prompt"])
            planned[pool] = {"upstream_paper_version_id": up, "requests": len(items), "candidates": len(built["context"]["candidates"]),
                             "package": str(pkg.relative_to(REPO)), "prompt_sha256": digest(built["prompt"].encode()),
                             "citing_papers": sorted({it["request"]["paper_version_id"] for it in items}),
                             "key": lg.add("S7", "REQUEST_POOL", pool, "MODEL_MATCH", S7_VERSION, digest(built["prompt"].encode()))}
    finally:
        lg.close()
    order = list(planned)
    batches = [order[i:i + POOLS_PER_BATCH] for i in range(0, len(order), POOLS_PER_BATCH)]
    for n, pools_ in enumerate(batches, 1):
        listing = "\n".join(f"- pool `{p}`: {REPO / planned[p]['package'] / 'data.json'}" for p in pools_)
        task_dir = DATA / "s7" / f"batch-{n}"
        write_private(task_dir / "TASK.md", S7_TASK.format(batch=n, version=S7_VERSION, instruction="> " + matching.INSTRUCTION, pools=listing))
        write_private(task_dir / "response.schema.json", json.dumps(matching.RESPONSE_SCHEMA, indent=1))
    requests_total = sum(p["kind"] == "EXTERNAL_REQUEST" for p in nodes["Placeholder"].values())
    dump("s7-plan.json", {"source_manifest_id": dm["manifest_id"], "k": S7_K, "created_at": now(), "requests_total": requests_total,
                          "requests_without_upstream_in_corpus": outside, "requests_without_candidates": len(empty),
                          "pools": planned, "batches": batches})
    log(f"s7 plan: {requests_total} requests; {outside} without an upstream paper in the corpus; {len(empty)} without candidates; "
        f"{len(planned)} pools in {len(batches)} batches")


def cmd_s7_next():
    plan = load("s7-plan.json")
    lg = open_ledger()
    try:
        for n, pools in enumerate(plan["batches"], 1):
            ready = [p for p in pools if (item := lg.item(plan["pools"][p]["key"]))["state"] == "READY" and item["dispatchable"]]
            if not ready:
                continue
            task_dir = DATA / "s7" / f"batch-{n}"
            k = len(list(task_dir.glob("dispatch-*.json"))) + 1
            reservations = {p: lg.reserve(plan["pools"][p]["key"], provider=PROVIDER, account_ref=ACCOUNT, amount=1)["id"] for p in ready}
            dispatch = {"batch": n, "dispatch": k, "reserved_at": now(), "pools": ready, "reservations": reservations, "responses_file": f"responses-{k}.json"}
            write_private(task_dir / f"dispatch-{k}.json", dispatch)
            print(json.dumps({"batch": n, "task": str(task_dir / "TASK.md"), "dispatch_file": str(task_dir / f"dispatch-{k}.json"),
                              "responses_file": str(task_dir / dispatch["responses_file"]), "pools": len(ready)}))
            log(f"s7 dispatch batch {n} #{k}: {len(ready)} pools reserved")
            return
        print("{}")
    finally:
        lg.close()


def cmd_s7_ingest(batch, agent_ref):
    plan, base, results = load("s7-plan.json"), load("base.json"), load("s7-results.json", {})
    task_dir = DATA / "s7" / f"batch-{batch}"
    k = max(int(p.stem.split("-")[1]) for p in task_dir.glob("dispatch-*.json"))
    if (task_dir / f"ingested-{k}.json").exists():
        raise SystemExit(f"dispatch {k} of batch {batch} is already ingested")
    dispatch = json.loads((task_dir / f"dispatch-{k}.json").read_text())
    try:
        responses = json.loads((task_dir / dispatch["responses_file"]).read_text())
        read_error = None if isinstance(responses, dict) else "RESPONSES_NOT_AN_OBJECT"
    except (OSError, ValueError) as error:
        responses, read_error = {}, "RESPONSES_UNREADABLE: " + type(error).__name__
    summary = []
    lg = open_ledger()
    try:
        for pool in dispatch["pools"]:
            entry = plan["pools"][pool]
            pkg = REPO / entry["package"]
            context = json.loads((pkg / "data.json").read_text())
            response = responses.get(pool) if not read_error else None
            rfile = write_private(pkg / f"response-{k}.json", canonical(response)) if response is not None else None
            receipt = {"reservation_id": dispatch["reservations"][pool], "operation": matching.OPERATION, "model": MODEL, "transport": TRANSPORT,
                       "agent_ref": agent_ref, "training_cutoff": TRAINING_CUTOFF, "prompt_sha256": entry["prompt_sha256"],
                       "response_sha256": rfile and digest(rfile.read_bytes()), "dispatched_at": dispatch["reserved_at"], "settled_at": now(),
                       "usage": "UNMETERED", "rendering": f"AGENT_PACKAGE_V1: the prompt's SOURCE DATA as data.json; {len(dispatch['pools'])} pools in one agent context"}
            receipt_file = write_private(pkg / f"receipt-{k}.json", canonical(receipt))
            codes = collections.Counter()
            if response is None:
                d, failure = None, "RESPONSE_REJECTED"
                codes[read_error or "RESPONSE_MISSING"] += 1
            else:
                up = entry["upstream_paper_version_id"]
                d = matching.match_rows_to_delta(context, response, method_version=S7_VERSION, parents=[base[up]["s1"]] if up in base else [],
                                                 produced_by=[artifact(receipt_file), artifact(rfile)])
                record_deltas(d)
                codes.update(i["code"] for i in d["issues"])
                failure = "RESPONSE_REJECTED" if set(codes) & {"MODEL_RESPONSE_SCHEMA_INVALID", "MATCH_REQUEST_SCOPE_INVALID", "MATCH_SOURCE_ID_UNKNOWN"} else None
            state = lg.settle(dispatch["reservations"][pool], receipt, failure=failure, cost=1)
            rows = response.get("matches", []) if isinstance(response, dict) else []
            summary.append({"pool_id": pool, "batch": batch, "dispatch": k, "state": state, "accepted": failure is None,
                            "upstream_paper_version_id": entry["upstream_paper_version_id"], "requests": entry["requests"],
                            "relations": dict(collections.Counter(r.get("relation") for r in rows if isinstance(r, dict))),
                            "source_junctions": len(((d or {}).get("nodes") or {}).get("Junction", [])),
                            "issue_codes": dict(sorted(codes.items())), "delta_id": d and d["delta_id"]})
    finally:
        lg.close()
    for row in summary:
        results[f"{row['pool_id']}#{row['dispatch']}"] = row
    dump("s7-results.json", results)
    write_private(task_dir / f"ingested-{k}.json", {"ingested_at": now(), "agent_ref": agent_ref, "summary": summary})
    log(f"s7 ingest batch {batch} #{k}: {sum(r['accepted'] for r in summary)}/{len(summary)} pools accepted, "
        f"{sum(r['source_junctions'] for r in summary)} source junctions")


# ---- build and load ----------------------------------------------------------------------------------------------------

def cmd_build():
    m = manifest()
    dm, view = current_view()
    dump("delta-set-manifest.json", dm)
    findings = invariants.check(view, "EXPLICIT_IDS_ONLY")
    dump("invariants.json", {"work_identity": "EXPLICIT_IDS_ONLY", "findings": findings, "count": len(findings)})
    nodes, edges = view["nodes"], view["edges"].values()
    J = nodes["Junction"].values()
    deltas = [store().get(i) for i in dm["deltas"]]
    counts = {"nodes": {label: len(rows) for label, rows in nodes.items()}, "junction_legs": sum(len(j["legs"]) for j in J),
              "junctions_by_method": dict(collections.Counter(f"{j['reading_method']}/{j['derivation_id'].split(':')[0]}" for j in J)),
              "readings_by_method": dict(collections.Counter(r["method"] for r in nodes["ClaimReading"].values())),
              "edges": dict(sorted(collections.Counter(e["type"] for e in edges).items())),
              "placeholders": dict(collections.Counter(p["kind"] for p in nodes["Placeholder"].values())),
              "deltas": dict(collections.Counter(f"{d['stage']}/{d['method']}" for d in deltas))}
    dump("view-counts.json", counts)
    # cross-paper: source junctions resolve a request of a citing paper to claims of an upstream paper
    claims, places = nodes["Claim"], nodes["Placeholder"]
    links = collections.Counter()
    for j in J:
        if j["derivation_id"].startswith("source:"):
            citing = places[j["conclusion_id"]]["paper_version_id"]
            for leg in j["legs"]:
                links[(citing, claims[leg["premise_id"]]["paper_version_id"])] += 1
    admitted = {row["paper_version_id"]: record["admission"] for record in rounds() for row in record["candidates"] if row["outcome"] == "ACCEPTED"}
    upstream_of = collections.defaultdict(set)
    for citing, up in links:
        upstream_of[up].add(citing)
    dump("cross-paper.json", {
        "source_junctions": sum(j["derivation_id"].startswith("source:") for j in J),
        "paper_links": [{"citing": c, "upstream": u, "legs": n, "citing_admission": admitted.get(c), "upstream_admission": admitted.get(u)}
                        for (c, u), n in sorted(links.items())],
        "upstream_papers_shared_by_sample_papers": {u: sorted(c for c in cs if admitted.get(c) == "SAMPLE") for u, cs in sorted(upstream_of.items())
                                                    if sum(admitted.get(c) == "SAMPLE" for c in cs) >= 2}})
    policy = exploratory_policy()
    out = analysis.analyze(view, dm, policy, {})
    dump("analysis-summary.json", {
        "policy": policy, "metrics_rows": len(out["metrics"]),
        "layers": dict(sorted(collections.Counter(str(r["layer"]) for r in out["metrics"]).items())),
        "diagnostics": {k: len(v) for k, v in out["diagnostics"].items() if isinstance(v, list)},
        "nominations": [{k: n[k] for k in ("list", "subject_kind", "subject_id", "layer", "dependent_papers", "next_action", "blockers", "rank_interval")}
                        for n in out["nominations"]]})
    plan = load("s6-plan.json", {})
    lg = open_ledger()
    try:
        items = {f["key"]: lg.item(f["key"]) for p in plan.values() for f in p["foci"]}
        s7 = load("s7-plan.json") or {"pools": {}}
        s7_items = {p["key"]: lg.item(p["key"]) for p in s7["pools"].values()}
        spent = lg.spent()
    finally:
        lg.close()
    coverage = corpus.coverage_report(m, rounds(), {pv: [f["key"] for f in p["foci"]] for pv, p in plan.items()}, items)
    dump("coverage.json", {"s6": coverage, "s7_items_by_state": dict(collections.Counter(i["state"] for i in s7_items.values())),
                           "agent_calls_spent": spent, "ceiling": m["budget_ceiling"]})
    rows = projection.project(view, dm, {})
    dump("projection-rows.json", {"nodes": {g: len(rs) for g, rs in rows["nodes"].items()}, "rels": {t: len(rs) for t, rs in rows["rels"].items()}})
    log(f"built: {len(dm['deltas'])} deltas, invariant findings {len(findings)}, source junctions {counts['junctions_by_method']}, "
        f"coverage {coverage['by_status']}")


def cmd_load():
    dm = load("delta-set-manifest.json")
    view = delta.check_manifest(dm, store())
    rows = projection.project(view, dm, {})
    pm = projection.projection_manifest(dm, reviews.review_set_digest([]))
    client = projection.QueryClient(NEO4J, "neo4j", "neo4j", "")
    client.headers.pop("Authorization")  # the local server runs with login disabled (127.0.0.1 only)
    ready = projection.load(client, rows, pm)
    dump("projection-manifest.json", ready)
    log(f"loaded {ready['id']}: state {ready['state']}, audits {sum(ready['audit_counts'][n] for n, _ in projection.AUDITS)} rows")


if __name__ == "__main__":
    commands = {"manifest": cmd_manifest, "sample": cmd_sample, "base": cmd_base, "s6-plan": cmd_s6_plan, "s6-next": cmd_s6_next,
                "s6-ingest": cmd_s6_ingest, "expand-select": cmd_expand_select, "expand-acquire": cmd_expand_acquire,
                "s7-plan": cmd_s7_plan, "s7-next": cmd_s7_next, "s7-ingest": cmd_s7_ingest, "build": cmd_build, "load": cmd_load}
    commands[sys.argv[1]](*sys.argv[2:])
