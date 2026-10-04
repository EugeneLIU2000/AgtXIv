"""Pin arXiv versions from bounded, retained official Atom metadata responses."""
from __future__ import annotations

import argparse
import fcntl
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from core import digest, utcnow, write_json
from ingest import normalize_paper_id

ATOM = "{http://www.w3.org/2005/Atom}"
MAX_BYTES = 2 * 1024 * 1024


def parse_version(raw: bytes, requested: str) -> dict:
    """Accept one explicit version for this identity, never infer v1 from dates."""
    requested = normalize_paper_id(requested)
    if len(raw) > MAX_BYTES:
        raise ValueError("Metadata response exceeded its byte limit")
    text = raw.decode("utf-8", errors="strict")
    if "\x00" in text or re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
        raise ValueError("Metadata is oversized or contains an unsupported XML declaration")
    root = ET.fromstring(text)
    if root.tag != ATOM + "feed":
        raise ValueError("Expected an official Atom feed")
    entries = root.findall(ATOM + "entry")
    if len(entries) != 1:
        raise ValueError("Expected exactly one matching metadata entry")
    entry = entries[0]
    identifier = (entry.findtext(ATOM + "id") or "").strip()
    url = urllib.parse.urlsplit(identifier)
    if (url.scheme not in {"http", "https"} or url.netloc != "arxiv.org"
            or url.query or url.fragment or not url.path.startswith("/abs/")):
        raise ValueError("Entry ID is not an arxiv.org abstract identity URL")
    pid = normalize_paper_id(url.path.removeprefix("/abs/"))
    if not re.search(r"v[1-9]\d*$", pid):
        raise ValueError("API metadata omitted the version; version remains unresolved")
    base = lambda value: re.sub(r"v[1-9]\d*$", "", value)
    if base(pid) != base(requested) or (re.search(r"v[1-9]\d*$", requested) and requested != pid):
        raise ValueError("Metadata identity/version differs from the requested paper")
    return {"paper_id": pid, "entry_id": identifier,
            "title": " ".join((entry.findtext(ATOM + "title") or "").split()),
            "published": entry.findtext(ATOM + "published"), "updated": entry.findtext(ATOM + "updated"),
            "version_basis": "EXPLICIT_VERSION_IN_OFFICIAL_ATOM_ENTRY_ID",
            "citation_version_alignment": "UNASSESSED"}


def resolve_version(repo: Path, requested: str, output: Path, *, timeout_seconds: int = 30) -> dict:
    repo, output = repo.resolve(), output.resolve()
    requested = normalize_paper_id(requested)
    if not output.is_relative_to(repo) or timeout_seconds <= 0:
        raise ValueError("Expected a repository output directory and positive timeout")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Preserve the previous metadata receipt; choose a fresh directory")
    output.mkdir(parents=True, exist_ok=True)
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": requested.removeprefix("arxiv:"), "max_results": 1})
    receipt = {"kind": "ArxivVersionResolution", "requested_id": requested, "request_url": url,
               "started_at": utcnow(), "program_sha256": digest(Path(__file__).read_bytes()),
               "status": "PAPER_VERSION_NOT_PINNED", "resolved": None, "response": None,
               "max_response_bytes": MAX_BYTES, "timeout_seconds": timeout_seconds,
               "timeout_scope": "SOCKET_OPERATION_TIMEOUT_NOT_WHOLE_REQUEST_DEADLINE",
               "semantic_support_accepted": False, "origin_established": False}
    try:
        # A host-wide file lock serializes this adapter's API calls and spaces
        # their starts by at least three seconds, including after a restart.
        throttle = repo / "schema v0.3/runs/.arxiv-api-throttle"
        throttle.parent.mkdir(parents=True, exist_ok=True)
        with throttle.open("a+") as state:
            fcntl.flock(state.fileno(), fcntl.LOCK_EX)
            state.seek(0)
            previous = state.read().strip()
            if previous:
                delay = max(0.0, 3.0 - (time.time() - float(previous)))
                if delay > 3.0:
                    raise ValueError("Clock moved backwards; API throttle requires host attention")
                time.sleep(delay)
            state.seek(0)
            state.truncate()
            state.write(str(time.time()))
            state.flush()
            request = urllib.request.Request(url, headers={"User-Agent": "AgtXIv-schema-research/0.3 (version-metadata)", "Accept": "application/atom+xml"})
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                final = urllib.parse.urlsplit(response.geturl())
                if final.scheme != "https" or final.netloc not in {"export.arxiv.org", "arxiv.org"} or final.path != "/api/query":
                    raise ValueError("Unexpected metadata redirect")
                receipt.update({"response_url": response.geturl(), "http_status": response.status,
                                "content_type": response.headers.get("Content-Type")})
                raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Metadata response exceeded the byte limit; not parsed")
        target = output / "response.atom"
        with target.open("xb") as stream:
            stream.write(raw)
        receipt["response"] = {"path": str(target), "sha256": digest(raw), "byte_size": len(raw)}
        receipt["resolved"] = parse_version(raw, requested)
        receipt["status"] = "VERSION_PINNED_FROM_METADATA"
    except (OSError, ValueError, ET.ParseError, urllib.error.URLError) as error:
        receipt["error"] = {"type": type(error).__name__, "detail": str(error)}
    receipt["ended_at"] = utcnow()
    write_json(output / "version-resolution.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = resolve_version(Path(__file__).resolve().parents[2], args.paper, args.output)
    print(json.dumps({key: result.get(key) for key in ("status", "resolved", "error")}, ensure_ascii=False))
    raise SystemExit(0 if result["resolved"] else 2)


if __name__ == "__main__":
    main()
