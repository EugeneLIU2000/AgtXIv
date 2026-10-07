"""S1 acquisition from a frozen metadata snapshot (spec §6.1-§6.2, §7): the sampling frame, the version rule,
versioned e-print acquisition and the outcome of every examined candidate.

The frame is read from the Kaggle arXiv metadata snapshot (here its Parquet copy, librarian-bots/arxiv-metadata-snapshot):
a paper is in the frame iff its primary category (the first token of `categories`, as arXiv lists it) is one of the
manifest's primary categories and its v1 date lies in the date window. The examined version is the latest one created
on or before the snapshot date (version_rule LATEST_ON_OR_BEFORE_SNAPSHOT). Sources come from export.arxiv.org, the
host arXiv sets aside for programmatic access, one request start per rate-token interval (the manifest's
min_request_interval_seconds); they are unpacked by the v0.3 bounded source adapter (src/agtxiv_v3/source.py, via
ingest._load_source_safety), parsed by v0.3 ingest.extract_paper, and eligibility.decide gives the outcome.

The network is touched only in fetch_source, and only through the opener a caller passes. Everything written lands
under the caller's data root inside the repository (the v0.3 reader requires that); nothing here is shared (I-13).
"""
from __future__ import annotations

import datetime as dt
import email.utils
import gzip
import hashlib
import http.client
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import ingest

import contracts
import eligibility

EPRINT = "https://export.arxiv.org/src/"
USER_AGENT = "AgtXIv-schema-research/0.4 (versioned-source-ingestion)"
TRANSIENT_HTTP = (429, 500, 502, 503, 504)
OPEN_LICENSES = ("creativecommons.org/licenses/by/", "creativecommons.org/licenses/by-sa/", "creativecommons.org/publicdomain/zero/")
UNDETERMINED = {  # fetch issue code -> SamplingRecord undetermined_class
    "SOURCE_ID_NOT_FOUND": "ID_NOT_FOUND", "SOURCE_TRANSIENT_NETWORK": "TRANSIENT_NETWORK", "SOURCE_SIZE_LIMIT": "SIZE_LIMIT",
    "SOURCE_IS_PDF": "NO_TEX_SOURCE", "SOURCE_MAIN_NOT_FOUND": "NO_TEX_SOURCE", "SOURCE_MAIN_AMBIGUOUS": "MAIN_AMBIGUOUS",
    "SOURCE_ACQUISITION_FAILED": "PARSE_FAILED"}


# ---- frame and version rule ----------------------------------------------------------------------------------------

def _date(created):
    """The UTC date of a versions[].created string ('Mon, 2 Apr 2007 19:18:42 GMT')."""
    return email.utils.parsedate_to_datetime(created).astimezone(dt.timezone.utc).date()


def snapshot_frame(parquet_glob, field):
    """{arxiv_base_id: metadata row} of the frame: primary category in field.primary_categories and v1 date inside
    field.date_window. Each row keeps title, categories, license, doi, journal_ref and versions [{version, created}]
    sorted by version number."""
    import duckdb  # the frame reader; the rest of the host does not need it

    rows = duckdb.connect().execute(
        'SELECT id, title, categories, license, doi, "journal-ref", versions FROM read_parquet(?) '
        "WHERE list_contains(?, split_part(categories, ' ', 1))", [parquet_glob, list(field["primary_categories"])]).fetchall()
    start, end = (dt.date.fromisoformat(field["date_window"][k]) for k in ("start", "end"))
    valid = contracts.validator("ArxivBaseId").is_valid
    out = {}
    for pid, title, categories, license_, doi, journal, versions in rows:
        versions = sorted(versions, key=lambda v: int(v["version"].lstrip("v")))
        if valid(pid) and versions and start <= _date(versions[0]["created"]) <= end:
            out[pid] = {"title": " ".join((title or "").split()), "categories": categories.split(), "license": license_,
                        "doi": doi, "journal_ref": journal, "versions": versions}
    return out


def snapshot_rows(parquet_glob, base_ids):
    """{arxiv_base_id: metadata row} for the given ids, whatever their category or date (EXPANSION candidates are
    outside the frame); the rows have snapshot_frame's shape, and an id the snapshot does not hold is absent."""
    import duckdb

    wanted = sorted(set(base_ids))
    rows = duckdb.connect().execute(
        'SELECT id, title, categories, license, doi, "journal-ref", versions FROM read_parquet(?) WHERE list_contains(?, id)',
        [parquet_glob, wanted]).fetchall() if wanted else []
    return {pid: {"title": " ".join((title or "").split()), "categories": categories.split(), "license": license_, "doi": doi,
                  "journal_ref": journal, "versions": sorted(versions, key=lambda v: int(v["version"].lstrip("v")))}
            for pid, title, categories, license_, doi, journal, versions in rows if versions}


def snapshot_dois(parquet_glob, dois, normalize):
    """{normalized DOI: sorted arXiv base ids whose snapshot record declares it} for the given normalized DOIs (the
    metadata the SAME_WORK basis HOST_RULE_ARXIV_METADATA_DOI rests on); normalize is works.normalize_doi. A record's doi
    field may hold several DOIs separated by spaces."""
    import duckdb

    wanted, out = set(dois), {}
    for pid, field in duckdb.connect().execute("SELECT id, doi FROM read_parquet(?) WHERE doi IS NOT NULL", [parquet_glob]).fetchall():
        for token in field.split():
            if (doi := normalize(token)) in wanted:
                out.setdefault(doi, set()).add(pid)
    return {doi: sorted(pids) for doi, pids in sorted(out.items())}


def choose_version(row, snapshot_date):
    """(version number, v1 date, version date) of the latest version created on or before snapshot_date."""
    limit = dt.date.fromisoformat(snapshot_date)
    dated = [(int(v["version"].lstrip("v")), _date(v["created"])) for v in row["versions"]]
    eligible = [(n, d) for n, d in dated if d <= limit]
    if not eligible:
        raise ValueError("NO_VERSION_ON_OR_BEFORE_SNAPSHOT")
    n, day = max(eligible)
    return n, dated[0][1], day


def redistribution(license_url):
    """OPEN only for CC BY, CC BY-SA and CC0; RESTRICTED for the arXiv default licence and NC/ND variants; UNKNOWN
    when the snapshot gives no licence (I-13: only OPEN papers' verbatim text may reach a shared projection)."""
    if not license_url:
        return "UNKNOWN"
    return "OPEN" if any(key in license_url for key in OPEN_LICENSES) else "RESTRICTED"


def paper_metadata(row, v1_date, version_date, source_sha256, snapshot_label):
    """The PaperVersion fields corpus.includes_delta takes (it adds id, arxiv_base_id, version and parser_sha256)."""
    date = lambda day, kind: {"value": day.isoformat(), "kind": kind, "precision": "DAY", "source": snapshot_label}
    out = {"primary_category": row["categories"][0], "categories": row["categories"], "redistribution": redistribution(row["license"]),
           "date_v1": date(v1_date, "ARXIV_V1"), "date_version": date(version_date, "ARXIV_VERSION"), "source_sha256": source_sha256}
    out.update({k: v for k, v in (("title", row["title"]), ("license", row["license"])) if v})
    return out


# ---- acquisition ---------------------------------------------------------------------------------------------------

class RateToken:
    """One shared token: consecutive request starts are at least `interval` seconds apart."""

    def __init__(self, interval, clock=time.monotonic, sleep=time.sleep):
        self.interval, self.clock, self.sleep, self.last = interval, clock, sleep, None

    def wait(self):
        if self.last is not None:
            self.sleep(max(0.0, self.last + self.interval - self.clock()))
        self.last = self.clock()


def _issue(code, detail, **context):
    return {"code": code, "detail": detail, **context}


def _unpack(repo, payload, source_root, limits):
    """(receipt fields, source files, main candidates, metadata_found) of an e-print payload, as v0.3 fetch_arxiv_source
    unpacks it: one gzip-compressed TeX file, or a tar through the bounded adapter."""
    single = payload
    if payload.startswith(b"\x1f\x8b"):
        with gzip.open(io.BytesIO(payload), "rb") as stream:
            single = stream.read(limits["max_file_bytes"] + 1)
    fields = {}
    if (len(single) <= limits["max_file_bytes"] and b"\x00" not in single and single.lstrip().startswith((b"%", b"\\"))
            and b"\\begin{document}" in ingest._mask_comments(single)):
        source_root.mkdir()
        (source_root / "main.tex").write_bytes(single)
        fields["source_container"] = "SINGLE_TEX_GZIP" if payload.startswith(b"\x1f\x8b") else "SINGLE_TEX"
    else:
        safety = ingest._load_source_safety(repo)
        bounds = safety.ArchiveLimits(max_archive_bytes=limits["max_archive_bytes"], max_expanded_archive_bytes=limits["max_expanded_bytes"],
                                      max_files=limits["max_files"], max_entries=limits["max_files"] * 2,
                                      max_file_bytes=limits["max_file_bytes"], max_total_bytes=limits["max_expanded_bytes"])
        tree = safety.extract_tar_atomic(payload, source_root, limits=bounds)
        fields.update({"source_container": "TAR", "source_tree_sha256": "sha256:" + tree.source_tree_sha256})
    files = sorted(path for path in source_root.rglob("*") if path.is_file())
    mains, found = [], False
    for meta in (path for path in files if path.name == "00README.json"):
        record = ingest._read_json(meta)
        for row in record.get("sources", []) if isinstance(record, dict) else []:
            if isinstance(row, dict) and row.get("usage") == "toplevel" and isinstance(row.get("filename"), str):
                found = True
                main = ingest._inside(source_root, meta.parent / row["filename"])
                if main.is_file() and main.suffix.lower() == ".tex":
                    mains.append(main)
    if not found:
        mains = [p for p in files if p.suffix.lower() == ".tex" and re.search(rb"\\begin\s*\{document\}", ingest._mask_comments(p.read_bytes()))]
    fields["main_selection_basis"] = "UPSTREAM_TOPLEVEL_METADATA" if found else "UNIQUE_LITERAL_DOCUMENT_ROOT"
    return fields, files, sorted(set(mains))


def fetch_source(repo, paper_version_id, output_dir, *, token, limits, retry_limit, opener=urllib.request.urlopen):
    """Acquire one versioned e-print into output_dir (inside repo): the result has v0.3 fetch_arxiv_source's shape
    ({paper_id, source_descriptor, source_archive, source_files, issues, receipt}) plus attempts. A 404 is
    SOURCE_ID_NOT_FOUND; 429, 5xx and network errors are retried up to retry_limit times, then
    SOURCE_TRANSIENT_NETWORK; an archive over the limit is SOURCE_SIZE_LIMIT; a PDF is SOURCE_IS_PDF."""
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    if not output_dir.is_relative_to(repo):
        raise ValueError("Acquired sources must be written inside the repository")
    version = paper_version_id.removeprefix("arxiv:")
    if not re.fullmatch(r".+v[1-9][0-9]*", version):
        raise ValueError("Source download requires an explicit arXiv version")
    output_dir.mkdir(parents=True, exist_ok=True)
    url = EPRINT + urllib.parse.quote(version, safe="/")
    receipt = {"program": "schema v0.4/host/acquire.py:fetch_source", "program_sha256": ingest._sha(Path(__file__).read_bytes()),
               "paper_id": paper_version_id, "request_url": url, "limits": limits, "started_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    result = {"paper_id": paper_version_id, "source_descriptor": None, "source_archive": None, "source_files": [], "issues": [],
              "receipt": receipt, "attempts": 0}
    payload, source_root, k = None, output_dir / "source", 0
    while source_root.exists():  # an interrupted earlier attempt keeps its tree; this one unpacks beside it
        k += 1
        source_root = output_dir / f"source-{k}"
    for attempt in range(1, retry_limit + 2):
        if attempt > 1:
            token.sleep(min(60.0, 5.0 * attempt))  # back off before a retry, on top of the shared rate token
        result["attempts"] = attempt
        token.wait()
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with opener(request, timeout=limits["timeout_seconds"]) as response:
                host = urllib.parse.urlparse(response.geturl()).hostname or ""
                if host != "arxiv.org" and not host.endswith(".arxiv.org"):
                    raise ValueError("Source response redirected outside arxiv.org")
                payload = response.read(limits["max_archive_bytes"] + 1)
                receipt.update({"response_url": response.geturl(), "http_status": response.status,
                                "content_type": response.headers.get("Content-Type")})
            break
        except urllib.error.HTTPError as error:
            receipt["http_status"] = error.code
            if error.code == 404:
                result["issues"].append(_issue("SOURCE_ID_NOT_FOUND", "export.arxiv.org has no source for this version", url=url))
                break
            if error.code not in TRANSIENT_HTTP:
                result["issues"].append(_issue("SOURCE_ACQUISITION_FAILED", f"HTTP {error.code}", url=url))
                break
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError) as error:
            receipt["last_error"] = f"{type(error).__name__}: {error}"
        except ValueError as error:
            result["issues"].append(_issue("SOURCE_ACQUISITION_FAILED", str(error), url=url))
            break
    else:
        result["issues"].append(_issue("SOURCE_TRANSIENT_NETWORK", "No response after the retry limit", attempts=result["attempts"]))
    if payload is not None:
        archive = output_dir / (hashlib.sha256(payload).hexdigest() + ".source")
        if len(payload) > limits["max_archive_bytes"]:
            result["issues"].append(_issue("SOURCE_SIZE_LIMIT", "Source download exceeds the archive-byte limit", limit=limits["max_archive_bytes"]))
        elif not payload:
            result["issues"].append(_issue("SOURCE_ACQUISITION_FAILED", "Source response is empty"))
        else:
            archive.write_bytes(payload)
            result["source_archive"] = {"path": archive.relative_to(repo).as_posix(), "sha256": ingest._sha(payload), "byte_size": len(payload)}
            if payload.startswith(b"%PDF"):
                result["issues"].append(_issue("SOURCE_IS_PDF", "The submission has no TeX source"))
            else:
                try:
                    fields, files, mains = _unpack(repo, payload, source_root, limits)
                    receipt.update(fields)
                    result["source_files"] = [{"path": p.relative_to(repo).as_posix(), "sha256": ingest._sha(p.read_bytes()),
                                               "byte_size": p.stat().st_size} for p in files]
                    if len(mains) != 1:
                        result["issues"].append(_issue("SOURCE_MAIN_AMBIGUOUS" if mains else "SOURCE_MAIN_NOT_FOUND",
                                                       "A unique TeX entry point was not established",
                                                       candidates=[p.relative_to(repo).as_posix() for p in mains]))
                    else:
                        result["source_descriptor"] = {
                            "paper_id": paper_version_id, "id": paper_version_id, "slug": version.replace("/", "-"),
                            "artifact": mains[0].relative_to(repo).as_posix(), "expected_sha256": ingest._sha(mains[0].read_bytes()),
                            "source_root": source_root.relative_to(repo).as_posix(),
                            "discovery_evidence": (output_dir / "source-acquisition.json").relative_to(repo).as_posix(),
                            "source_archive": result["source_archive"]}
                except (OSError, ValueError, EOFError, KeyError) as error:
                    result["issues"].append(_issue("SOURCE_ACQUISITION_FAILED", f"{type(error).__name__}: {error}"))
    receipt["ended_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    receipt["result"] = "SOURCE_AVAILABLE" if result["source_descriptor"] else "SOURCE_READ_PENDING"
    (output_dir / "source-acquisition.json").write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return result


def examine(repo, base_id, row, manifest, data_root, token, *, opener=urllib.request.urlopen, snapshot_label):
    """One examined candidate: {outcome (a SamplingRecord candidate's host-free fields), paper_version_id, record
    (the v0.3 extraction or None), metadata (PaperVersion fields or None), issues}. A finished acquisition is reused,
    so an interrupted run resumes without fetching again."""
    n, v1_date, version_date = choose_version(row, manifest["sampling_frame"]["snapshot_date"])
    pv = f"arxiv:{base_id}v{n}"
    home = Path(data_root) / base_id.replace("/", "_") / f"v{n}"
    receipt = home / "source-acquisition.json"
    fetched = json.loads(receipt.read_text()) if receipt.exists() else fetch_source(
        repo, pv, home, token=token, limits=manifest["size_limits"], retry_limit=manifest["transient_retry_limit"], opener=opener)
    attempts = max(1, fetched["attempts"])
    out = {"paper_version_id": pv, "record": None, "metadata": None, "issues": fetched["issues"]}
    if fetched["source_descriptor"] is None:
        code = next((i["code"] for i in fetched["issues"] if i["code"] in UNDETERMINED), "SOURCE_ACQUISITION_FAILED")
        attempts = 1 + manifest["transient_retry_limit"] if code == "SOURCE_TRANSIENT_NETWORK" else attempts
        return {**out, "outcome": {"outcome": "UNDETERMINED", "attempts": attempts, "undetermined_class": UNDETERMINED[code]}}
    try:
        record = ingest.extract_paper(repo, pv, home / "extraction", source_descriptor=fetched["source_descriptor"], source_catalog={})
    except Exception as error:  # an unreadable source is UNDETERMINED(PARSE_FAILED), never INELIGIBLE
        issue = _issue("SOURCE_PARSE_EXCEPTION", f"{type(error).__name__}: {error}")
        return {**out, "issues": [*out["issues"], issue], "outcome": {"outcome": "UNDETERMINED", "attempts": attempts, "undetermined_class": "PARSE_FAILED"}}
    decision = eligibility.decide(record, manifest["eligibility"])
    metadata = paper_metadata(row, v1_date, version_date, fetched["source_archive"]["sha256"], snapshot_label)
    return {**out, "record": record, "metadata": metadata, "decision": decision,
            "outcome": eligibility.candidate_outcome(decision, attempts, pv)}
