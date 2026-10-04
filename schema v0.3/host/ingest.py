"""Frozen-source adapters for the schema research ladder, version 0.3.

Claim segmentation is delegated to ``tools/extract_provisional_claims.py``.
This module adds byte identities, provenance bridges, and a *mention* inventory;
it never converts a citation, overlap, or search result into mathematical support.
No model-written state, disposition, coverage, or proof flag is consumed.
"""
from __future__ import annotations

import hashlib
import gzip
import importlib.util
import io
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ARXIV = re.compile(r"(?:\d{4}\.\d{4,5}|[a-z][a-z.-]+/\d{7})(?:v\d+)?", re.I)
REFERENCE = re.compile(rb"\\(eqref|ref|autoref|cref|Cref|pageref|cite[a-zA-Z]*)\*?(?:\s*\[[^\]]*\])*\s*\{([^{}]*)\}")
LABEL = re.compile(rb"\\label\s*\{([^{}]*)\}")
INCLUDE = re.compile(rb"\\(input|include)\s*\{([^{}]*)\}")
BIBITEM = re.compile(rb"\\bibitem\s*(?:\[(?:[^\]]|\n)*\]\s*)?\{([^{}]*)\}")


def _sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _id(prefix: str, value: Any) -> str:
    return prefix + ":" + hashlib.sha256(_canonical(value)).hexdigest()[:32]


def _issue(code: str, detail: str, **context: Any) -> dict:
    return {"code": code, "detail": detail, **context}


def normalize_paper_id(value: str) -> str:
    value = value.strip().removeprefix("arxiv:")
    value = re.sub(r"^https?://(?:export\.)?arxiv\.org/(?:abs|pdf|e-print)/", "", value)
    value = value.removesuffix(".pdf").rstrip("/")
    if not ARXIV.fullmatch(value):
        raise ValueError("Expected a syntactically valid arXiv identifier")
    return "arxiv:" + value


def _base_id(value: str) -> str:
    return re.sub(r"v\d+$", "", normalize_paper_id(value))


def _inside(repo: Path, value: str | Path) -> Path:
    path = (repo / value).resolve()
    if not path.is_relative_to(repo.resolve()):
        raise ValueError("Source paths must stay inside the repository: " + str(value))
    return path


def _load_extractor(repo: Path):
    path = repo / "tools/extract_provisional_claims.py"
    name = "agtxiv_schema_v03_extractor_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(str(path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module  # dataclass annotation resolution requires this.
        spec.loader.exec_module(module)
    return sys.modules[name]


def _load_source_safety(repo: Path):
    path = repo / "src/agtxiv_v3/source.py"
    name = "agtxiv_schema_v03_source_safety_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(str(path))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def fetch_arxiv_source(repo: Path, paper_id: str, output_dir: Path, *, timeout_seconds: int = 30,
                       max_archive_bytes: int = 64 * 1024 * 1024,
                       max_expanded_bytes: int = 256 * 1024 * 1024,
                       max_file_bytes: int = 32 * 1024 * 1024,
                       max_files: int = 5000) -> dict:
    """Acquire a versioned arXiv source under bounded, safe local extraction.

    Downloading bytes does not authorize TeX execution. Archive extraction reuses
    the repository's bounded source adapter; links, traversal and special files
    are rejected. Ambiguous main documents stay a source-reading issue.
    """
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    paper_id = normalize_paper_id(paper_id)
    if not re.search(r"v\d+$", paper_id):
        raise ValueError("Source download requires an explicit arXiv version")
    if not output_dir.is_relative_to(repo):
        raise ValueError("Acquired sources must be written inside the repository")
    if any(type(value) is not int or value < 1 for value in (timeout_seconds, max_archive_bytes, max_expanded_bytes, max_file_bytes, max_files)):
        raise ValueError("Source resource limits must be positive integers")
    output_dir.mkdir(parents=True, exist_ok=True)
    url = "https://arxiv.org/src/" + urllib.parse.quote(paper_id.removeprefix("arxiv:"), safe="/")
    receipt = {"program": "schema v0.3/host/ingest.py:fetch_arxiv_source", "paper_id": paper_id,
               "program_sha256": _sha(Path(__file__).read_bytes()),
               "request_url": url, "started_at": datetime.now(timezone.utc).isoformat(),
               "limits": {"max_archive_bytes": max_archive_bytes, "max_expanded_bytes": max_expanded_bytes,
                          "max_file_bytes": max_file_bytes, "max_files": max_files, "timeout_seconds": timeout_seconds}}
    receipt_path = output_dir / "source-acquisition.json"
    if receipt_path.exists():
        receipt_path = output_dir / ("source-acquisition-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    result = {"paper_id": paper_id, "source_descriptor": None, "source_archive": None,
              "source_files": [], "issues": [], "receipt": receipt}
    source_root = output_dir / "source"
    try:
        if source_root.exists() or source_root.is_symlink():
            raise ValueError("Source destination already exists; choose a fresh acquisition directory")
        request = urllib.request.Request(url, headers={"User-Agent": "AgtXIv-schema-research/0.3 (versioned-source-ingestion)"})
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            final_host = urllib.parse.urlparse(final_url).hostname or ""
            if final_host != "arxiv.org" and not final_host.endswith(".arxiv.org"):
                raise ValueError("Source response redirected outside arxiv.org")
            final_path = urllib.parse.unquote(urllib.parse.urlparse(final_url).path).rstrip("/")
            requested_version = paper_id.removeprefix("arxiv:")
            if final_path not in {"/src/" + requested_version, "/e-print/" + requested_version}:
                raise ValueError("Source response redirect does not preserve the requested versioned source identity")
            payload = response.read(max_archive_bytes + 1)
            receipt.update({"response_url": final_url, "http_status": response.status,
                            "content_type": response.headers.get("Content-Type")})
        if len(payload) > max_archive_bytes:
            raise ValueError("Source download exceeds archive-byte limit")
        if not payload:
            raise ValueError("Source response is empty")
        archive = output_dir / (hashlib.sha256(payload).hexdigest() + ".source")
        if archive.exists() and archive.read_bytes() != payload:
            raise ValueError("Source archive hash collision")
        if not archive.exists():
            with archive.open("xb") as stream:
                stream.write(payload)
        result["source_archive"] = {"path": archive.relative_to(repo).as_posix(), "sha256": _sha(payload), "byte_size": len(payload)}
        # Historic arXiv sources may be one gzip-compressed TeX file, not tar.
        # A bounded read identifies this case without unbounded decompression.
        single = payload
        if payload.startswith(b"\x1f\x8b"):
            with gzip.open(io.BytesIO(payload), "rb") as stream:
                single = stream.read(max_file_bytes + 1)
        looks_like_tex = (len(single) <= max_file_bytes and b"\x00" not in single
                          and single.lstrip().startswith((b"%", b"\\"))
                          and b"\\begin{document}" in _mask_comments(single))
        if looks_like_tex:
            source_root.mkdir()
            (source_root / "main.tex").write_bytes(single)
            receipt["source_container"] = "SINGLE_TEX_GZIP" if payload.startswith(b"\x1f\x8b") else "SINGLE_TEX"
        else:
            safety = _load_source_safety(repo)
            limits = safety.ArchiveLimits(max_archive_bytes=max_archive_bytes,
                                         max_expanded_archive_bytes=max_expanded_bytes,
                                         max_files=max_files, max_entries=max_files * 2,
                                         max_file_bytes=max_file_bytes, max_total_bytes=max_expanded_bytes)
            tree = safety.extract_tar_atomic(payload, source_root, limits=limits)
            receipt.update({"source_container": "TAR", "source_tree_sha256": "sha256:" + tree.source_tree_sha256,
                            "safety_adapter_sha256": _sha((repo / "src/agtxiv_v3/source.py").read_bytes())})
        files = sorted(path for path in source_root.rglob("*") if path.is_file())
        result["source_files"] = [{"path": path.relative_to(repo).as_posix(), "sha256": _sha(path.read_bytes()), "byte_size": path.stat().st_size} for path in files]
        # Respect explicit upstream top-level metadata before any lexical guess.
        main_candidates = []
        metadata_found = False
        for metadata in (path for path in files if path.name == "00README.json"):
            metadata_record = _read_json(metadata)
            if not isinstance(metadata_record, dict) or not isinstance(metadata_record.get("sources", []), list):
                raise ValueError("Upstream source metadata does not contain a sources array")
            rows = metadata_record.get("sources", [])
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("Upstream source metadata has a malformed source entry")
                if row.get("usage") != "toplevel":
                    continue
                if not isinstance(row.get("filename"), str):
                    raise ValueError("Upstream top-level filename is missing or malformed")
                metadata_found = True
                main = _inside(source_root, metadata.parent / row["filename"])
                if not main.is_file():
                    raise ValueError("Upstream top-level document is missing: " + str(row["filename"]))
                if main.suffix.lower() == ".tex":
                    main_candidates.append(main)
        if not metadata_found:
            main_candidates = [path for path in files if path.suffix.lower() == ".tex" and re.search(rb"\\begin\s*\{document\}", _mask_comments(path.read_bytes()))]
        main_candidates = sorted(set(main_candidates))
        receipt["main_selection_basis"] = "UPSTREAM_TOPLEVEL_METADATA" if metadata_found else "UNIQUE_LITERAL_DOCUMENT_ROOT"
        if len(main_candidates) != 1:
            result["issues"].append(_issue("SOURCE_MAIN_AMBIGUOUS" if main_candidates else "SOURCE_MAIN_NOT_FOUND",
                                           "A unique TeX entry point was not established", candidates=[path.relative_to(repo).as_posix() for path in main_candidates]))
        else:
            main = main_candidates[0]
            result["source_descriptor"] = {"paper_id": paper_id, "id": paper_id,
                                           "slug": paper_id.removeprefix("arxiv:").replace("/", "-"),
                                           "artifact": main.relative_to(repo).as_posix(), "expected_sha256": _sha(main.read_bytes()),
                                           "source_root": source_root.relative_to(repo).as_posix(),
                                           "discovery_evidence": receipt_path.relative_to(repo).as_posix(),
                                           "source_archive": result["source_archive"]}
    except (OSError, ValueError, KeyError, EOFError, urllib.error.URLError) as error:
        result["issues"].append(_issue("SOURCE_ACQUISITION_FAILED", str(error), paper_id=paper_id))
        receipt["error_type"] = type(error).__name__
    receipt["ended_at"] = datetime.now(timezone.utc).isoformat()
    receipt["result"] = "SOURCE_AVAILABLE" if result["source_descriptor"] is not None else "SOURCE_READ_PENDING"
    with receipt_path.open("xb") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    return result


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_sources(repo: Path) -> dict[str, dict]:
    """Discover local versioned sources from existing registries and DAG evidence.

    Additional acquired papers may be registered in ``schema v0.3/sources.json``
    as ``{"papers": [{"paper_id": ..., "artifact": ..., "artifact_hash": ...}]}``.
    Registry identity is provenance, not a claim of source authenticity.
    """
    repo = Path(repo).resolve()
    rows: dict[str, dict] = {}
    for path in sorted((repo / "Stabilizerness/PaperAgentRegistry/manifests").glob("*.json")):
        record = _read_json(path)
        source = record.get("source", {})
        if record.get("paper_id") and source.get("canonical_artifact"):
            rows[record["paper_id"]] = {
                "paper_id": record["paper_id"], "slug": path.stem,
                "artifact": source["canonical_artifact"],
                "expected_sha256": source.get("artifact_hash"),
                "discovery_evidence": path.relative_to(repo).as_posix(),
            }
    graph_path = repo / "Stabilizerness/dag/claim-dag.json"
    if graph_path.exists():
        for node in _read_json(graph_path).get("nodes", []):
            source = node.get("source", {})
            paper_id, artifact = source.get("paper_id"), source.get("artifact")
            if paper_id and artifact and paper_id.startswith("arxiv:"):
                rows.setdefault(paper_id, {
                    "paper_id": paper_id, "slug": paper_id.removeprefix("arxiv:").replace("/", "-"),
                    "artifact": artifact, "expected_sha256": source.get("artifact_hash"),
                    "discovery_evidence": graph_path.relative_to(repo).as_posix(),
                })
    acquired_path = repo / "schema v0.3/sources.json"
    if acquired_path.exists():
        for source in _read_json(acquired_path).get("papers", []):
            paper_id = normalize_paper_id(source["paper_id"])
            if not re.search(r"v\d+$", paper_id):
                raise ValueError("Acquired sources must carry an explicit version: " + paper_id)
            rows[paper_id] = {
                "paper_id": paper_id, "slug": source.get("slug", paper_id.removeprefix("arxiv:").replace("/", "-")),
                "artifact": source["artifact"], "expected_sha256": source.get("artifact_hash"),
                "discovery_evidence": acquired_path.relative_to(repo).as_posix(),
                **{key: source[key] for key in ("source_root", "source_archive", "source_acquisition", "version_evidence") if key in source},
            }
    available = {}
    for key, value in sorted(rows.items()):
        path = _inside(repo, value["artifact"])
        if not path.is_file():
            continue
        data = path.read_bytes()
        title_match = re.search(rb"\\title\s*(?:\[[^\]]*\]\s*)?\{", _mask_comments(data))
        if title_match:
            title = _balanced(data, title_match.end() - 1)
            if title:
                value["title"] = title[0].decode("utf-8", errors="replace")
                value["title_source"] = _span(value["artifact"], data, title_match.start(), title[1])
        available[key] = value
    return available


def _mask_comments(data: bytes) -> bytes:
    """Mask ordinary TeX comments without changing any byte offset."""
    output = bytearray(data)
    line_start = 0
    for line in data.splitlines(keepends=True):
        for index, byte in enumerate(line):
            if byte != 37:
                continue
            before = index
            while before and line[before - 1] == 92:
                before -= 1
            if (index - before) % 2 == 0:
                for position in range(index, len(line)):
                    if line[position] not in (10, 13):
                        output[line_start + position] = 32
                break
        line_start += len(line)
    return bytes(output)


def _span(path: str, data: bytes, start: int, end: int) -> dict:
    if not 0 <= start < end <= len(data):
        raise ValueError(f"Invalid original-byte span {path}:{start}:{end}")
    return {"path": path, "sha256": _sha(data), "byte_start": start, "byte_end": end,
            "span_sha256": _sha(data[start:end]), "offset_unit": "BYTE", "interval": "HALF_OPEN"}


def _overlap(left: dict, right: dict) -> bool:
    return left["path"] == right["path"] and max(left["byte_start"], right["byte_start"]) < min(left["byte_end"], right["byte_end"])


def _line_offsets(data: bytes) -> list[int]:
    offsets = [0]
    for line in data.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _freeze(output_dir: Path, data: bytes) -> str:
    digest = hashlib.sha256(data).hexdigest()
    path = output_dir / "sources" / digest
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Frozen source collision: " + str(path))
    else:
        with path.open("xb") as stream:
            stream.write(data)
    return "sources/" + digest


def _read_source(repo: Path, path: Path, sources: dict[str, bytes], source_root: Path) -> str:
    """Read one bounded file inside the source's permitted tree, including symlinks."""
    path = _inside(source_root, path)
    relative = path.relative_to(repo).as_posix()
    if relative not in sources:
        if path.stat().st_size > 32 * 1024 * 1024:
            raise ValueError("Source file exceeds 32 MiB: " + relative)
        with path.open("rb") as stream:
            data = stream.read(32 * 1024 * 1024 + 1)
        if len(data) > 32 * 1024 * 1024:
            raise ValueError("Source file exceeds 32 MiB: " + relative)
        if len(sources) >= 5000 or sum(map(len, sources.values())) + len(data) > 256 * 1024 * 1024:
            raise ValueError("Source inventory resource limit exceeded")
        sources[relative] = data
    return relative


def _source_tree(repo: Path, main: Path, issues: list[dict], *, source_root: Path | None = None) -> tuple[dict[str, bytes], set[str]]:
    source_root = source_root or repo
    sources: dict[str, bytes] = {}
    body_paths: set[str] = set()
    queue = [(main, True)]
    while queue:
        path, body = queue.pop(0)
        path = _inside(source_root, path)
        relative = path.relative_to(repo).as_posix()
        if body:
            body_paths.add(relative)
        if relative in sources:
            continue
        _read_source(repo, path, sources, source_root)
        data = sources[relative]
        clean = _mask_comments(data)
        document_start = clean.find(b"\\begin{document}")
        for match in INCLUDE.finditer(clean):
            name = match.group(2).decode("utf-8", errors="replace").strip()
            if "\\" in name or "#" in name:
                issues.append(_issue("DYNAMIC_INCLUDE_UNRESOLVED", "Macro-expanded input was not followed", path=relative, include=name))
                continue
            target = path.parent / name
            if not target.suffix:
                target = target.with_suffix(".tex")
            try:
                target = _inside(source_root, target)
            except ValueError:
                issues.append(_issue("INCLUDE_OUTSIDE_SOURCE_ROOT", "Input path leaves the permitted source tree", path=relative, include=name))
                continue
            if not target.is_file():
                issues.append(_issue("SOURCE_INCLUDE_MISSING", "Literal input could not be read", path=relative, include=name))
                continue
            child_body = body and (document_start < 0 or match.start() > document_start)
            queue.append((target, child_body))
        if re.search(rb"\\(?:if[A-Za-z]*|else|fi)\b", clean):
            issues.append(_issue("TEX_CONDITIONAL_ACTIVITY_UNASSESSED", "Static occurrences may include inactive TeX branches", path=relative))
    return sources, body_paths


def _balanced(data: bytes, opening: int) -> tuple[bytes, int] | None:
    if opening >= len(data) or data[opening] != 123:
        return None
    depth = 0
    for index in range(opening, len(data)):
        before = index
        while before and data[before - 1] == 92:
            before -= 1
        if (index - before) % 2:
            continue
        if data[index] == 123:
            depth += 1
        elif data[index] == 125:
            depth -= 1
            if depth == 0:
                return data[opening + 1:index], index + 1
    return None


def _bib_field(raw: bytes, field: str) -> str | None:
    match = re.search(rb"\\bibinfo\s*\{" + field.encode() + rb"\}\s*\{", raw)
    if match:
        value = _balanced(raw, match.end() - 1)
        if value:
            return re.sub(r"\s+", " ", value[0].decode("utf-8", errors="replace")).strip()
    return None


def _title_key(text: str) -> str:
    text = re.sub(r"\\[A-Za-z]+\*?", " ", text)
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _macro_inventory(sources: dict[str, bytes]) -> list[dict]:
    """Record literal macro bodies without executing TeX or asserting expansion."""
    rows = []
    pattern = re.compile(rb"\\(newcommand|renewcommand|providecommand|DeclareMathOperator)\*?\s*(?:\{\s*(\\[A-Za-z@]+)\s*\}|(\\[A-Za-z@]+))\s*((?:\[[^\]]*\]\s*)*)\{")
    for path, data in sorted(sources.items()):
        if not path.endswith(".tex"):
            continue
        clean = _mask_comments(data)
        for match in pattern.finditer(clean):
            body = _balanced(clean, match.end() - 1)
            if body:
                rows.append({"name": (match.group(2) or match.group(3)).decode(),
                             "declaration_kind": match.group(1).decode(),
                             "argument_specification": match.group(4).decode().strip(),
                             "body": body[0].decode("utf-8", errors="replace"),
                             "source": _span(path, data, match.start(), body[1]),
                             "expansion": "NOT_EXECUTED"})
        for match in re.finditer(rb"\\(?:gdef|edef|xdef|def)\s*(\\[A-Za-z@]+)([^{}]*)\{", clean):
            body = _balanced(clean, match.end() - 1)
            if body:
                rows.append({"name": match.group(1).decode(), "declaration_kind": "DEF_FAMILY",
                             "argument_specification": match.group(2).decode().strip(),
                             "body": body[0].decode("utf-8", errors="replace"),
                             "source": _span(path, data, match.start(), body[1]), "expansion": "NOT_EXECUTED"})
    return rows


def _bibliography_units(data: bytes, default: str) -> list[dict]:
    """Inventory literal bibunits and their explicit or standard generated names."""
    clean = _mask_comments(data)
    units = [{"name": default, "byte_start": 0, "byte_end": len(data)}]
    stack = []
    count = 0
    token = re.compile(rb"\\(begin|end)\s*\{bibunit\}|\\def\s*\\@bibunitname\s*\{([^{}]*)\}")
    for match in token.finditer(clean):
        if match.group(1) == b"begin":
            count += 1
            unit = {"name": "bu" + str(count), "byte_start": match.start(), "byte_end": len(data)}
            units.append(unit)
            stack.append(unit)
        elif match.group(1) == b"end":
            if stack:
                stack.pop()["byte_end"] = match.end()
        elif stack:
            stack[-1]["name"] = match.group(2).decode("utf-8", errors="replace").strip()
    return units


def _bibtex_bibliography(repo: Path, main: Path, sources: dict[str, bytes], known: dict,
                        issues: list[dict], compiled_rows: list[dict], source_root: Path) -> list[dict]:
    """Read literal BibTeX resources as data; do not expand TeX or BibTeX macros."""
    from bibtex import parse_bibtex

    command = re.compile(rb"\\(?:bibliography|addbibresource)(?:\s*\[[^\]]*\])?\s*\{([^{}]*)\}|\\putbib\s*\[([^\]]*)\]")
    resources: dict[tuple[str, str], list[dict]] = {}
    for source_path, data in list(sources.items()):
        if not source_path.endswith(".tex"):
            continue
        units = _bibliography_units(data, main.stem)
        for match in command.finditer(_mask_comments(data)):
            reference = _span(source_path, data, match.start(), match.end())
            active_units = [unit for unit in units if unit["byte_start"] <= match.start() < unit["byte_end"]]
            unit = min(active_units, key=lambda row: row["byte_end"] - row["byte_start"])["name"]
            try:
                names = (match.group(1) if match.group(1) is not None else match.group(2)).decode("utf-8").split(",")
            except UnicodeDecodeError:
                issues.append(_issue("BIBLIOGRAPHY_RESOURCE_NAME_INVALID", "Resource name is not UTF-8", source=reference))
                continue
            for raw_name in names:
                name = raw_name.strip()
                if not name or "\\" in name or "#" in name:
                    issues.append(_issue("DYNAMIC_BIBLIOGRAPHY_RESOURCE_UNRESOLVED", "Resource name requires expansion or is empty", name=name, source=reference))
                    continue
                if not name.lower().endswith(".bib"):
                    name += ".bib"
                try:
                    target = _inside(source_root, (repo / source_path).parent / name)
                    path = _read_source(repo, target, sources, source_root)
                except (OSError, ValueError) as error:
                    issues.append(_issue("BIBLIOGRAPHY_RESOURCE_UNAVAILABLE", str(error), name=name, source=reference))
                    continue
                resources.setdefault((path, unit), []).append(reference)

    compiled = {}
    for row in compiled_rows:
        compiled.setdefault((row["bibliography_unit"], row["key"]), []).append(row)
    parsed = {}
    rows = []
    for (path, unit), references in sorted(resources.items()):
        data = sources[path]
        if path not in parsed:
            parsed[path] = parse_bibtex(data)
            for issue in parsed[path]["issues"]:
                issues.append(_issue("BIBTEX_PARSE_ISSUE", "Literal BibTeX parsing retained an unresolved issue", path=path, parser_issue=issue))
        for entry in parsed[path]["entries"]:
            key = entry.get("key")
            if not key or entry["entry_type"] == "xdata":
                continue
            source = _span(path, data, entry["start"], entry["end"])
            fields = entry["fields"]
            for issue in entry.get("field_issues", []):
                issues.append(_issue("BIBTEX_FIELD_UNRESOLVED", "Field cannot be resolved by literal parsing", key=key, source=source, parser_issue=issue))
            shadowing = compiled.get((unit, key), [])
            if shadowing:
                # Compiled entries are the paper's displayed bibliography. Keep
                # the alternative bytes and mismatch obligation, not two silent
                # interchangeable identities or an unverified equivalence.
                issues.append(_issue("BIBTEX_ENTRY_SHADOWED_BY_COMPILED", "Compiled bibliography has precedence; agreement with this BibTeX entry is unassessed", key=key, source=source, bibliography_unit=unit, compiled_entry_ids=[row["id"] for row in shadowing]))
                continue
            arxiv_ids = set()
            for value in (fields.get("url"), fields.get("eprint")):
                if not isinstance(value, str):
                    continue
                for marker in re.finditer(r"arxiv(?:\.org/(?:abs|pdf))?\s*[:/]\s*([A-Za-z0-9./-]+)", value, re.I):
                    identifier = marker.group(1).removesuffix(".pdf")
                    if ARXIV.fullmatch(identifier):
                        arxiv_ids.add(normalize_paper_id(identifier))
            prefix = fields.get("archiveprefix") or fields.get("eprinttype")
            eprint = fields.get("eprint")
            if isinstance(prefix, str) and prefix.strip().lower() == "arxiv" and isinstance(eprint, str):
                identifier = eprint.strip()
                if ARXIV.fullmatch(identifier):
                    arxiv_ids.add(normalize_paper_id(identifier))
            dois = sorted({match.group(0).rstrip(".,;") for field in ("doi", "url")
                           if isinstance(fields.get(field), str)
                           for match in re.finditer(r"10\.\d{4,9}/[^\s{}<>\"\\]+", fields[field])})
            local = {paper for paper in known for found in arxiv_ids if _base_id(paper) == _base_id(found)}
            local_matches = [{"paper_id": paper, "match_basis": "EXPLICIT_ARXIV_BASE_ID"} for paper in sorted(local)]
            title = fields.get("title")
            if title and len(_title_key(title).split()) >= 4:
                for paper, descriptor in known.items():
                    if descriptor.get("title") and _title_key(title) == _title_key(descriptor["title"]):
                        local.add(paper)
                        local_matches.append({"paper_id": paper, "match_basis": "NORMALIZED_TITLE_EQUALITY_CANDIDATE", "title": descriptor["title"], "source": descriptor["title_source"]})
            rows.append({"id": _id("bibliography", {"key": key, "source": source, "unit": unit, "format": "BIBTEX_LITERAL"}),
                         "key": key, "source": source, "bibliography_unit": unit,
                         "text": data[entry["start"]:entry["end"]].decode("utf-8", errors="replace"),
                         "title": title, "year": fields.get("year"), "journal": fields.get("journal"),
                         "format": "BIBTEX_LITERAL", "entry_type": entry["entry_type"], "literal_fields": fields,
                         "field_issues": entry.get("field_issues", []), "resource_references": references,
                         "parse_issues": [issue for issue in parsed[path]["issues"] if issue.get("entry_start") == entry["start"]],
                         "identifiers": {"arxiv": sorted(arxiv_ids), "doi": dois},
                         "local_source_candidates": sorted(local), "local_match_evidence": local_matches,
                         "identifier_resolution": "EXPLICIT_IDENTIFIER" if arxiv_ids or dois else "IDENTIFIER_SEARCH_REQUIRED",
                         "terminal_kind_candidate": "ARXIV_SOURCE_AVAILABLE" if local else None,
                         "upstream_search": "FRONTIER",
                         "fallback": {"required": not arxiv_ids, "providers": ["CROSSREF", "ADS"], "search_status": "SEARCH_NOT_RUN"},
                         "support_classification": "PENDING_SEMANTIC_SUPPORT_CLASSIFICATION"})
    return rows


def _bibliography(repo: Path, main: Path, sources: dict[str, bytes], known: dict, issues: list[dict], *, source_root: Path | None = None) -> list[dict]:
    source_root = source_root or repo
    paths = {path for path, data in sources.items() if BIBITEM.search(_mask_comments(data))}
    main_bbl = main.with_suffix(".bbl")
    if main_bbl.is_file():
        try:
            paths.add(_read_source(repo, main_bbl, sources, source_root))
        except ValueError as error:
            issues.append(_issue("BIBLIOGRAPHY_RESOURCE_REJECTED", str(error), path=str(main_bbl)))
    for source_path, data in list(sources.items()):
        if not source_path.endswith(".tex"):
            continue
        for unit in _bibliography_units(data, main.stem)[1:]:
            try:
                unit_path = _inside(source_root, main.parent / (unit["name"] + ".bbl"))
            except ValueError:
                issues.append(_issue("BIBLIOGRAPHY_UNIT_PATH_INVALID", "Bibliography unit leaves the source repository", name=unit["name"]))
                continue
            if unit_path.is_file():
                paths.add(_read_source(repo, unit_path, sources, source_root))
            else:
                issues.append(_issue("BIBLIOGRAPHY_UNIT_MISSING", "Compiled bibliography unit cannot be read", name=unit["name"], path=source_path))
    rows = []
    for path in sorted(paths):
        data = sources[path]
        clean = _mask_comments(data)
        matches = list(BIBITEM.finditer(clean))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(data)
            closing = clean.find(b"\\end{thebibliography}", match.end(), end)
            if closing >= 0:
                end = closing
            raw = data[match.start():end]
            text = raw.decode("utf-8", errors="replace")
            key = match.group(1).decode("utf-8", errors="replace").strip()
            # Match only explicitly marked identifiers; bare numbers are not arXiv IDs.
            arxiv_ids = set()
            for marker in re.finditer(r"(?:arxiv(?:\.org/(?:abs|pdf))?\s*[:/]\s*|eprint\s*\}\s*\{)([A-Za-z0-9./-]+)", text, re.I):
                value = marker.group(1).removesuffix(".pdf")
                if ARXIV.fullmatch(value):
                    arxiv_ids.add("arxiv:" + value)
            dois = sorted({match.group(0).rstrip(".,;") for match in re.finditer(r"10\.\d{4,9}/[^\s{}<>\"\\]+", text)})
            local = {paper for paper in known for found in arxiv_ids if _base_id(paper) == _base_id(found)}
            local_matches = [{"paper_id": paper, "match_basis": "EXPLICIT_ARXIV_BASE_ID"} for paper in sorted(local)]
            title = _bib_field(raw, "title")
            if title is None:
                blocks = re.split(r"\\newblock\s*", text)
                if len(blocks) >= 3:
                    title = re.sub(r"\s+", " ", blocks[1]).strip().rstrip(".")
            if title and len(_title_key(title).split()) >= 4:
                for paper, descriptor in known.items():
                    if descriptor.get("title") and _title_key(title) == _title_key(descriptor["title"]):
                        local.add(paper)
                        local_matches.append({"paper_id": paper, "match_basis": "NORMALIZED_TITLE_EQUALITY_CANDIDATE", "title": descriptor["title"], "source": descriptor["title_source"]})
            source = _span(path, data, match.start(), end)
            row = {"id": _id("bibliography", {"key": key, "source": source}), "key": key, "source": source,
                   "bibliography_unit": Path(path).stem if path.endswith(".bbl") else main.stem,
                   "text": text, "title": title, "year": _bib_field(raw, "year"), "journal": _bib_field(raw, "journal"),
                   "identifiers": {"arxiv": sorted(arxiv_ids), "doi": dois},
                   "local_source_candidates": sorted(local), "local_match_evidence": local_matches,
                   "identifier_resolution": "EXPLICIT_IDENTIFIER" if arxiv_ids or dois else "IDENTIFIER_SEARCH_REQUIRED",
                   "terminal_kind_candidate": "ARXIV_SOURCE_AVAILABLE" if local else None,
                   "upstream_search": "FRONTIER",
                   "fallback": {"required": not arxiv_ids, "providers": ["CROSSREF", "ADS"], "search_status": "SEARCH_NOT_RUN"},
                   "support_classification": "PENDING_SEMANTIC_SUPPORT_CLASSIFICATION"}
            rows.append(row)
    rows.extend(_bibtex_bibliography(repo, main, sources, known, issues, rows, source_root))
    if not rows:
        issues.append(_issue("BIBLIOGRAPHY_NOT_EXTRACTED", "No readable literal bibliography resource or inline bibitems; unresolved sources remain pending"))
    return rows


def _curated(repo: Path, slug: str, paper_id: str, sources: dict[str, bytes], issues: list[dict]) -> tuple[list[dict], dict]:
    registry = repo / "Stabilizerness/MathClaimIRRegistry"
    path = registry / "claims" / (slug + ".jsonl")
    if not path.exists():
        return [], {}
    anchor_rows = {}
    for anchor_path in (repo / "agents" / slug / "source/anchors.jsonl", registry / "source-anchors" / (slug + ".jsonl")):
        if anchor_path.exists():
            for line in anchor_path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    anchor_rows[row["id"]] = row
    bound = {}
    for anchor_id, row in sorted(anchor_rows.items()):
        artifact = row.get("artifact")
        location = row.get("location", {})
        start, end = location.get("line_start"), location.get("line_end")
        data = sources.get(artifact)
        if data is None or not isinstance(start, int) or not isinstance(end, int):
            issues.append(_issue("CURATED_ANCHOR_UNBOUND", "Curated anchor lacks a source in the frozen extraction scope or line interval", anchor_id=anchor_id))
            continue
        if row.get("artifact_hash") != _sha(data):
            issues.append(_issue("CURATED_ANCHOR_HASH_MISMATCH", "Curated anchor was recorded against different source bytes", anchor_id=anchor_id))
            continue
        offsets = _line_offsets(data)
        if not 1 <= start <= end < len(offsets):
            issues.append(_issue("CURATED_ANCHOR_RANGE_INVALID", "Curated line interval is outside the source", anchor_id=anchor_id))
            continue
        bound[anchor_id] = _span(artifact, data, offsets[start - 1], offsets[end])
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("source", {}).get("occurrence_work") != paper_id:
            issues.append(_issue("CURATED_PAPER_MISMATCH", "Curated record belongs to another paper", record_id=record.get("id")))
            continue
        statement_ids = record["source"].get("statement_anchors", [])
        proof_ids = record["source"].get("proof_anchors", [])
        rows.append({"id": record["claim"]["id"], "math_claim_ir_id": record["id"], "paper_id": paper_id,
                     "kind": record["statement_kind"], "text": record["normalized_statement_expanded_latex"],
                     "statement_sources": [bound[key] for key in statement_ids if key in bound],
                     "proof_sources": [bound[key] for key in proof_ids if key in bound],
                     "unbound_anchor_ids": [key for key in statement_ids + proof_ids if key not in bound],
                     "registry_source": {"path": path.relative_to(repo).as_posix(), "sha256": _sha(path.read_bytes())},
                     "alignment": "AGENT_NORMALIZED_UNREVIEWED"})
    return rows, bound


def extract_paper(repo: Path, paper_id: str, output_dir: Path, *, source_descriptor: dict | None = None,
                  source_catalog: dict | None = None) -> dict:
    """Extract frozen candidates and mention coverage for one locally available paper.

    ``output_dir`` receives content-addressed source blobs and one JSON report.
    Counts are observations in declared scopes, never semantic completeness.
    An unknown source returns a typed frontier result without inventing claims.
    """
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    requested = normalize_paper_id(paper_id)
    # A running research plan pins bibliography identity candidates as well as
    # source bytes. An unrelated registry edit cannot silently add identities.
    known = discover_sources(repo) if source_catalog is None else {key: dict(value) for key, value in source_catalog.items()}
    if source_descriptor is not None:
        descriptor_id = normalize_paper_id(source_descriptor.get("paper_id") or source_descriptor.get("id") or requested)
        if not re.search(r"v\d+$", descriptor_id):
            raise ValueError("An explicit source descriptor must pin the arXiv version")
        if _base_id(descriptor_id) != _base_id(requested) or (re.search(r"v\d+$", requested) and descriptor_id != requested):
            raise ValueError("Source descriptor identity does not match the requested paper")
        descriptor = dict(source_descriptor)
        descriptor.update({"paper_id": descriptor_id, "slug": descriptor.get("slug") or descriptor_id.removeprefix("arxiv:").replace("/", "-"),
                           "expected_sha256": descriptor.get("expected_sha256") or descriptor.get("artifact_hash"),
                           "discovery_evidence": descriptor.get("discovery_evidence", "EXPLICIT_SOURCE_DESCRIPTOR")})
        descriptor["artifact"] = _inside(repo, descriptor["artifact"]).relative_to(repo).as_posix()
        if not _inside(repo, descriptor["artifact"]).is_file():
            raise ValueError("Source descriptor artifact is missing")
        known[descriptor_id] = descriptor
    candidates = [key for key in known if key == requested or (not re.search(r"v\d+$", requested) and _base_id(key) == requested)]
    if len(candidates) != 1:
        return {"paper": {"id": requested, "upstream_search": "FRONTIER"}, "papers": [{"id": requested}],
                "claims": [], "curated_claims": [], "anchors": [], "bibliography": [], "bridge_candidates": [],
                "coverage": [], "source_files": [], "issues": [_issue("SOURCE_UNREACHABLE" if not candidates else "SOURCE_VERSION_AMBIGUOUS", "No unique local frozen-source candidate", paper_id=requested, candidates=candidates)]}
    paper_id = candidates[0]
    descriptor = known[paper_id]
    main = _inside(repo, descriptor["artifact"])
    issues: list[dict] = []
    # Acquired TeX can only reference files from its extracted archive. The
    # fallback supports descriptors saved before source_root was introduced.
    source_root = repo
    if descriptor.get("source_root"):
        source_root = _inside(repo, descriptor["source_root"])
    elif descriptor.get("source_archive"):
        source_root = _inside(repo, Path(descriptor["source_archive"]["path"]).parent / "source")
    _inside(source_root, main)
    sources, body_paths = _source_tree(repo, main, issues, source_root=source_root)
    if descriptor.get("expected_sha256") and descriptor["expected_sha256"] != _sha(sources[descriptor["artifact"]]):
        raise ValueError("Registered source hash mismatch: " + descriptor["artifact"])
    bibliography = _bibliography(repo, main, sources, known, issues, source_root=source_root)
    extractor = _load_extractor(repo)
    claims, proof_spans = [], []
    for path in sorted(body_paths):
        if not path.endswith(".tex"):
            continue
        data = sources[path]
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(_issue("SOURCE_ENCODING_UNSUPPORTED", "Claim segmentation requires UTF-8; original bytes were frozen", path=path))
            continue
        lines = text.splitlines()
        offsets = _line_offsets(data)
        section_paths = extractor.section_paths([extractor.strip_comment(line) for line in lines])
        for span in extractor.extract_spans(lines):
            occurrence = extractor.occurrence_record(paper_id, descriptor["slug"], path, _sha(data)[7:], lines, section_paths, span)
            source = _span(path, data, offsets[span.start - 1], offsets[span.end])
            claims.append({"id": occurrence["id"], "paper_id": paper_id, "kind": span.kind,
                           "speech_act_candidate": span.speech_act, "text": data[source["byte_start"]:source["byte_end"]].decode("utf-8"),
                           "source": source, "proof_sources": [], "section_path": occurrence["section_path"],
                           "line_start": span.start, "line_end": span.end,
                           "reason_codes": occurrence["reason_codes"], "legacy_occurrence_content_hash": occurrence["content_hash"]})
        stack = []
        for match in re.finditer(rb"\\(begin|end)\s*\{proof\}", _mask_comments(data)):
            if match.group(1) == b"begin":
                stack.append(match.start())
            elif stack:
                start = stack.pop()
                proof_spans.append(_span(path, data, start, match.end()))
            else:
                issues.append(_issue("PROOF_ENVIRONMENT_UNBALANCED", "Unmatched proof end", path=path, byte_offset=match.start()))
        for start in stack:
            issues.append(_issue("PROOF_ENVIRONMENT_UNBALANCED", "Unclosed proof environment", path=path, byte_offset=start))
    # A syntactically adjacent proof is only an ownership candidate, not a proof check.
    for proof in proof_spans:
        earlier = [claim for claim in claims if claim["kind"] == "THEOREM_LIKE_ENVIRONMENT" and claim["source"]["path"] == proof["path"] and claim["source"]["byte_end"] <= proof["byte_start"]]
        if earlier:
            previous = max(earlier, key=lambda row: row["source"]["byte_end"])
            gap = _mask_comments(sources[proof["path"]])[previous["source"]["byte_end"]:proof["byte_start"]]
            if not LABEL.sub(b"", gap).strip():
                previous["proof_sources"].append(proof)
                continue
        issues.append(_issue("PROOF_OWNER_UNRESOLVED", "Proof body has no unambiguous adjacent theorem occurrence", source=proof))
    curated, curated_anchors = _curated(repo, descriptor["slug"], paper_id, sources, issues)
    bridges = []
    for claim in curated:
        for source in claim["statement_sources"]:
            matched = [occurrence for occurrence in claims if _overlap(source, occurrence["source"])]
            for occurrence in matched:
                payload = {"occurrence_id": occurrence["id"], "curated_claim_id": claim["id"], "math_claim_ir_id": claim["math_claim_ir_id"], "curated_source": source}
                bridges.append({"id": _id("occurrence-bridge", payload), **payload,
                                "relation_candidate": "SOURCE_SPAN_OVERLAP", "semantic_identity": "UNASSESSED",
                                "exclusion": "PENDING_SEMANTIC_BRIDGE_CLASSIFICATION"})
        if not any(row["curated_claim_id"] == claim["id"] for row in bridges):
            issues.append(_issue("CURATED_CLAIM_WITHOUT_OCCURRENCE_BRIDGE", "No frozen statement-span overlap with automatic candidates", claim_id=claim["id"]))
    labels = {}
    anchors = []
    for path in sorted(body_paths):
        if not path.endswith(".tex"):
            continue
        data, clean = sources[path], _mask_comments(sources[path])
        for match in LABEL.finditer(clean):
            source = _span(path, data, match.start(), match.end())
            key = match.group(1).decode("utf-8", errors="replace")
            enclosing = [claim for claim in claims if _overlap(source, claim["source"])]
            if enclosing:
                min_size = min(claim["source"]["byte_end"] - claim["source"]["byte_start"] for claim in enclosing)
                enclosing = [claim for claim in enclosing if claim["source"]["byte_end"] - claim["source"]["byte_start"] == min_size]
            labels.setdefault(key, []).append({"source": source, "claim_ids": sorted(claim["id"] for claim in enclosing)})
        bibliography_units = _bibliography_units(data, main.stem)
        for match in REFERENCE.finditer(clean):
            source = _span(path, data, match.start(), match.end())
            owners = []
            proof_owners = []
            for claim in claims:
                if _overlap(source, claim["source"]):
                    owners.append(claim["id"])
                if any(_overlap(source, span) for span in claim["proof_sources"]):
                    owners.append(claim["id"])
                    proof_owners.append(claim["id"])
            curated_owners = [claim["id"] for claim in curated if any(_overlap(source, span) for span in claim["statement_sources"] + claim["proof_sources"])]
            for key in match.group(2).decode("utf-8", errors="replace").split(","):
                key = key.strip()
                payload = {"paper_id": paper_id, "source": source, "command": match.group(1).decode(), "key": key}
                units = [unit for unit in bibliography_units if unit["byte_start"] <= match.start() < unit["byte_end"]]
                unit = min(units, key=lambda row: row["byte_end"] - row["byte_start"])
                anchors.append({"id": _id("source-reference", payload), **payload,
                                "bibliography_unit": unit["name"],
                                "owner_claim_ids": sorted(set(owners)), "proof_owner_claim_ids": sorted(set(proof_owners)),
                                "curated_owner_claim_ids": sorted(curated_owners), "candidate_target_ids": [],
                                "support_edge_ids": [], "exclusion": "PENDING_SEMANTIC_SUPPORT_CLASSIFICATION"})
    for anchor in anchors:
        if anchor["command"].startswith("cite"):
            matches = [row for row in bibliography if row["key"] == anchor["key"] and row["bibliography_unit"] == anchor["bibliography_unit"]]
            anchor["candidate_target_ids"] = [row["id"] for row in matches]
            anchor["resolution"] = "RESOLVED_BIBLIOGRAPHY_MENTION" if len(matches) == 1 else "AMBIGUOUS_BIBLIOGRAPHY_KEY" if matches else "UNRESOLVED_BIBLIOGRAPHY_KEY"
        else:
            matches = labels.get(anchor["key"], [])
            anchor["candidate_target_ids"] = sorted({target for row in matches for target in row["claim_ids"]})
            anchor["resolution"] = "AMBIGUOUS_LABEL" if len(matches) > 1 else "RESOLVED_CANDIDATE" if anchor["candidate_target_ids"] else "LABEL_WITHOUT_CLAIM" if matches else "UNRESOLVED_LABEL"
        if anchor["resolution"].startswith(("UNRESOLVED", "AMBIGUOUS", "LABEL_WITHOUT")):
            issues.append(_issue(anchor["resolution"], "Mention cannot yet identify a unique claim target", anchor_id=anchor["id"]))
    frozen = [{"path": path, "sha256": _sha(data), "byte_size": len(data), "blob_path": _freeze(output_dir, data)} for path, data in sorted(sources.items())]
    extractor_path = repo / "tools/extract_provisional_claims.py"
    paper = {"id": paper_id, "requested_id": requested, "title": descriptor.get("title"), "source": descriptor["artifact"], "source_sha256": _sha(sources[descriptor["artifact"]]),
             "source_manifest_sha256": _sha(_canonical(frozen)), "source_archive": descriptor.get("source_archive"),
             "source_root": source_root.relative_to(repo).as_posix(),
             "upstream_search": "FRONTIER", "discovery_evidence": descriptor["discovery_evidence"]}
    coverage = [
        {"scope": {"paper_id": paper_id, "unit": "THEOREM_LIKE_ENVIRONMENT", "source_paths": sorted(body_paths)}, "observed_count": sum(claim["kind"] == "THEOREM_LIKE_ENVIRONMENT" for claim in claims)},
        {"scope": {"paper_id": paper_id, "unit": "AUTOMATIC_OCCURRENCE", "source_paths": sorted(body_paths)}, "observed_count": len(claims)},
        {"scope": {"paper_id": paper_id, "unit": "CURATED_MATHCLAIMIR", "registry": f"Stabilizerness/MathClaimIRRegistry/claims/{descriptor['slug']}.jsonl"}, "observed_count": len(curated)},
        {"scope": {"paper_id": paper_id, "unit": "REFERENCE_ANCHOR", "source_paths": sorted(body_paths)}, "observed_count": len(anchors), "resolved_count": sum(row["resolution"].startswith("RESOLVED") for row in anchors), "support_classification_pending_count": len(anchors)},
        {"scope": {"paper_id": paper_id, "unit": "BIBLIOGRAPHY_ENTRY", "source_paths": sorted({row["source"]["path"] for row in bibliography})}, "observed_count": len(bibliography), "explicit_identifier_count": sum(bool(row["identifiers"]["arxiv"] or row["identifiers"]["doi"]) for row in bibliography)},
        {"scope": {"paper_id": paper_id, "unit": "BIBLIOGRAPHY_KEY", "source_paths": sorted({row["source"]["path"] for row in bibliography})}, "observed_count": len({row["key"] for row in bibliography})},
    ]
    report = {"schema": "agtxiv.research-source-extraction/0.3.0", "paper": paper, "papers": [paper], "claims": claims,
              "curated_claims": curated, "anchors": anchors, "labels": labels, "bibliography": bibliography,
              "bridge_candidates": bridges, "curated_anchors": curated_anchors, "proof_spans": proof_spans,
              "source_files": frozen, "macro_table": _macro_inventory(sources), "coverage": coverage, "issues": issues,
              "extractor": {"path": extractor_path.relative_to(repo).as_posix(), "sha256": _sha(extractor_path.read_bytes()), "entrypoint": "extract_spans"},
              "source_adapter": {"path": Path(__file__).relative_to(repo).as_posix(), "sha256": _sha(Path(__file__).read_bytes()),
                                 "bibliography_parser": {"path": "schema v0.3/host/bibtex.py", "sha256": _sha((Path(__file__).parent / "bibtex.py").read_bytes())}},
              "limitations": ["Automatic occurrences and semantic claims are distinct units; no completeness percentage is asserted.",
                              "The original deterministic extractor's fixed environment vocabulary and prose heuristics are retained.",
                              "Literal includes are followed; macro expansion, conditional activity, rendered PDF fidelity and implicit prose references remain unassessed.",
                              "Every reference is a mention with a pending typed exclusion from the support graph; no support inference is automatic.",
                              "Source overlap is a bridge candidate, not semantic identity or a promotion of a curated claim."]}
    # Detect changed source files before publishing the report; frozen blobs remain usable evidence.
    for path, data in sources.items():
        if _inside(repo, path).read_bytes() != data:
            raise ValueError("Source changed during extraction: " + path)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "extraction.json"
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    if target.exists() and target.read_bytes() != encoded:
        raise FileExistsError("Extraction output already exists with different bytes: " + str(target))
    if not target.exists():
        with target.open("xb") as stream:
            stream.write(encoded)
    return report


def resolve_external_identifiers(extraction: dict, output_dir: Path, *, enable_network: bool = False,
                                 max_requests: int = 50, timeout_seconds: int = 15,
                                 transport: Callable[[str], bytes] | None = None) -> dict:
    """Crossref title/journal fallback with immutable raw-response evidence.

    Results remain candidates: fuzzy bibliographic matching is a DECISION task.
    An unavailable provider or request budget never becomes an exhausted origin.
    ADS requires a separate authenticated adapter and is explicitly left pending.
    """
    if max_requests < 0 or timeout_seconds <= 0:
        raise ValueError("Expected nonnegative request budget and positive timeout")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records, issues = [], []
    requests = 0
    for entry in extraction.get("bibliography", []):
        if not entry["fallback"]["required"]:
            continue
        doi = next(iter(entry["identifiers"]["doi"]), None)
        if doi:
            url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
        else:
            query = " ".join(str(entry.get(field) or "") for field in ("title", "journal", "year")).strip()
            query = query or re.sub(r"\\[A-Za-z]+|[{}]", " ", entry["text"])
            url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": query[:1600], "rows": 3})
        cache_key = hashlib.sha256(url.encode()).hexdigest()
        cache = output_dir / (cache_key + ".response.json")
        record = {"bibliography_id": entry["id"], "provider": "CROSSREF", "request_url": url,
                  "upstream_search": "FRONTIER", "search_status": "SEARCH_NOT_RUN", "candidates": [],
                  "ads_search_status": "SEARCH_NOT_RUN", "ads_requirement": "AUTHENTICATED_ADAPTER_REQUIRED"}
        try:
            if cache.exists():
                raw = cache.read_bytes()
                record["transport"] = "CACHE"
            elif not enable_network:
                record["pending_reason"] = "NETWORK_NOT_ENABLED"
                records.append(record)
                continue
            elif requests >= max_requests:
                record["pending_reason"] = "IDENTIFIER_REQUEST_BUDGET"
                records.append(record)
                continue
            else:
                requests += 1
                if transport is None:
                    request = urllib.request.Request(url, headers={"User-Agent": "AgtXIv-schema-research/0.3 (bibliography-resolution)"})
                    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                        raw = response.read(4 * 1024 * 1024 + 1)
                    if len(raw) > 4 * 1024 * 1024:
                        raise ValueError("Crossref response exceeds 4 MiB")
                else:
                    raw = transport(url)
                with cache.open("xb") as stream:
                    stream.write(raw)
                record["transport"] = "NETWORK"
            result = json.loads(raw)
            message = result.get("message", {})
            matches = [message] if doi else message.get("items", [])
            record.update({"search_status": "SEARCH_PARTIAL", "response_sha256": _sha(raw), "response_path": str(cache)})
            for match in matches:
                record["candidates"].append({"doi": match.get("DOI"), "title": match.get("title", []),
                                              "type": match.get("type"), "published": match.get("published"),
                                              "url": match.get("URL"), "relation": match.get("relation", {}),
                                              "links": match.get("link", []), "alternative_ids": match.get("alternative-id", []),
                                              "match_basis": "EXPLICIT_DOI_LOOKUP" if doi else "CROSSREF_BIBLIOGRAPHIC_SEARCH",
                                              "subject_match": "UNASSESSED", "decision_required": "BIBLIOGRAPHY_IDENTITY"})
        except (OSError, ValueError, urllib.error.URLError) as error:
            record.update({"search_status": "SEARCH_PARTIAL", "error": str(error)})
            issues.append(_issue("EXTERNAL_IDENTIFIER_SEARCH_FAILED", str(error), bibliography_id=entry["id"]))
        records.append(record)
    report = {"schema": "agtxiv.external-identifier-search/0.3.0", "paper_id": extraction["paper"]["id"],
              "requests_made": requests, "records": records, "issues": issues,
              "scope": "Identifier search only; neither claim support nor earliest-source exhaustion is established"}
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    # Each invocation gets an immutable report even if network/cache provenance differs.
    target = output_dir / ("identifier-search-" + hashlib.sha256(encoded).hexdigest()[:16] + ".json")
    if not target.exists():
        with target.open("xb") as stream:
            stream.write(encoded)
    return report
