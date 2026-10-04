"""Budgeted recursive source research with real model calls or explicit evidence reuse.

This controller does not issue a successful mathematical certificate. It binds
the query after extraction, re-prunes after each join, and leaves unresolved
boundaries visible. The bottom-up Lean walk is a separate stage (proof_walk.py).
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import fcntl
import json
import pathlib
import re
import uuid
from collections import Counter, defaultdict

from candidates import CLAIM_REFERENCE_POLICY, assemble_candidates, select_candidate_graph
from core import PlanLedger, VERSION, canonical, digest, utcnow, write_json
from graph import prune_graph
from ingest import discover_sources, extract_paper, fetch_arxiv_source, normalize_paper_id
from model import SourcePayloadError, _frozen_source_payload, extract_candidates, match_source_candidates
from recursive_graph import MAX_GRAPH_BYTES, _verified_graph_json, _verified_json, join_candidate_paper
from scheduler import Frontier
from arxiv_metadata import parse_version, resolve_version
from extract_batches import extract_candidate_batches
from review_blocks import apply_review_blocks
from source_availability import apply_source_availability, apply_dependency_gaps
from source_corrections import apply_source_corrections
from model_routing import freeze_model_routing
from pdf_match_run import run_pdf_match
from pdf_proof_context import pdf_source_binding


@contextlib.contextmanager
def controller_lock(output):
    """One host process owns a run, including initialization and cached matching."""
    output = pathlib.Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent / ("." + output.name + ".controller.lock")).open("a+") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("RESEARCH_CONTROLLER_ALREADY_RUNNING") from None
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def reference(path):
    path = pathlib.Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "byte_size": len(raw)}


def base_id(paper_id):
    return re.sub(r"v[1-9]\d*$", "", normalize_paper_id(paper_id))


def pinned(paper_id):
    return bool(re.search(r"v[1-9]\d*$", paper_id))


def freeze_imports(path):
    """Freeze explicit evidence reuse; no imported judgement becomes a paid call."""
    if path is None:
        return {"candidates": {}, "matches": [], "extraction_batches": {}}
    data = json.loads(path.read_bytes())
    candidates = {}
    for pid, item in data.get("candidates", {}).items():
        pid = normalize_paper_id(pid)
        if not pinned(pid) or pid in candidates:
            raise ValueError("Imported candidate identities must be distinct and versioned")
        candidates[pid] = {key: reference(item[key]) for key in ("response", "extraction")}
        if item.get("provenance"):
            candidates[pid]["provenance"] = reference(item["provenance"])
    matches, pairs = [], set()
    for item in data.get("matches", []):
        pair = tuple(normalize_paper_id(item[key]) for key in ("downstream_paper_id", "upstream_paper_id"))
        if not all(map(pinned, pair)) or pair in pairs:
            raise ValueError("Imported match pairs must be distinct and versioned")
        pairs.add(pair)
        matches.append({"downstream_paper_id": pair[0], "upstream_paper_id": pair[1],
                        "response": reference(item["path"])})
    batches = {}
    for pid, item in data.get("extraction_batches", {}).items():
        pid = normalize_paper_id(pid)
        if not pinned(pid) or pid in batches or pid in candidates:
            raise ValueError("Batch imports require distinct versioned papers without whole-paper candidate imports")
        batches[pid] = reference(item["dispatch"])
    scopes = {}
    for pid, item in data.get("extraction_scopes", {}).items():
        pid = normalize_paper_id(pid)
        if not pinned(pid) or pid in scopes or pid in candidates:
            raise ValueError("Explicit scopes need a distinct versioned paper without whole-paper candidate import")
        scopes[pid] = reference(item["manifest"])
    return {"manifest": reference(path), "candidates": candidates, "matches": matches,
            "extraction_batches": batches, "extraction_scopes": scopes,
            "review_blocks": [reference(item["path"]) for item in data.get("review_blocks", [])],
            "source_availability": [reference(item["path"]) for item in data.get("source_availability", [])],
            "dependency_gaps": [reference(item["path"]) for item in data.get("dependency_gaps", [])],
            "source_corrections": [reference(item["path"]) for item in data.get("source_corrections", [])],
            "pdf_sources": [reference(item["path"]) for item in data.get("pdf_sources", [])]}


def candidate_paper(request, catalog):
    """Resolve only explicit arXiv IDs or an unambiguous local title candidate.

    A DOI alone does not establish an arXiv identity. Identity remains reviewable
    even when a locally registered version is selected for candidate exploration.
    """
    ids, local = set(), set()
    for entry in request.get("bibliography", []):
        ids.update(normalize_paper_id(pid) for pid in (entry.get("identifiers") or {}).get("arxiv", []))
        local.update(normalize_paper_id(row["paper_id"]) for row in entry.get("local_match_evidence", [])
                     if row.get("match_basis") in {"EXPLICIT_ARXIV_BASE_ID", "NORMALIZED_TITLE_EQUALITY_CANDIDATE"})
    if ids:
        if len({base_id(pid) for pid in ids}) != 1 or len({pid for pid in ids if pinned(pid)}) > 1:
            return None, "CONFLICTING_BIBLIOGRAPHY_IDENTITIES"
        versions = {pid for pid in ids if pinned(pid)}
        if not versions:
            versions = {pid for pid in catalog if base_id(pid) == base_id(next(iter(ids)))}
        if len(versions) != 1:
            return None, "PAPER_VERSION_NOT_PINNED"
        return next(iter(versions)), "EXPLICIT_ARXIV_ID_VERSION_FROM_CITATION_OR_LOCAL_CATALOG"
    local.intersection_update(catalog)
    if len(local) == 1:
        return next(iter(local)), "UNREVIEWED_LOCAL_TITLE_IDENTITY"
    return None, "AMBIGUOUS_LOCAL_IDENTITIES" if local else "EXTERNAL_IDENTITY_RESOLUTION_REQUIRED"


def bind_query(selector, paper, assembly):
    """Bind a frozen selector to extracted query-paper claims; any unmatched label fails."""
    if selector["kind"] == "ALL_EXTRACTED_MATH_CLAIMS":
        return assembly["query_ids"]
    if selector["kind"] != "SOURCE_LABELS":
        raise ValueError("QUERY_SELECTOR_UNSUPPORTED")
    claims = [row for row in assembly["nodes"] if row["id"] in set(assembly["query_ids"])]

    def match(rows):
        # The label's smallest enclosing occurrence decides; its byte position is only a fallback.
        occurrences = {oid for row in rows for oid in row["claim_ids"]}
        return {node["id"] for node in claims if occurrences & set(node["source_occurrence_ids"])} or {
            node["id"] for node in claims if any(span["path"] == row["source"]["path"] and
            span["byte_start"] <= row["source"]["byte_start"] < span["byte_end"] for row in rows for span in node["source_spans"])}
    matches = {label: match(paper["labels"].get(label, [])) for label in selector["labels"]}
    unmatched = [label for label, ids in matches.items() if not ids]
    if unmatched:
        raise ValueError("QUERY_LABEL_UNMATCHED: " + ", ".join(unmatched))
    return [qid for qid in assembly["query_ids"] if any(qid in ids for ids in matches.values())]


def terminal_kind(request, bibliography):
    """Deterministic frontier type from bibliography fields; not an identity or support judgement."""
    entries = [bibliography.get(row.get("id"), row) for row in request.get("bibliography", [])]
    identifiers = lambda kind: any((row.get("identifiers") or {}).get(kind) for row in entries)
    if identifiers("arxiv"):
        return "ARXIV_SOURCE_AVAILABLE"
    if any(row.get("entry_type") in {"book", "monograph"} for row in entries):
        return "MONOGRAPH"
    return "PREARXIV_DOI_NO_SOURCE" if identifiers("doi") else "FREE_TEXT_UNRESOLVED"


def accepted_support_edges(graph):
    return sum(row["disposition"] == "SOURCE_FROZEN_HUMAN_SIGNED" for row in graph["support_groups"]) if graph else 0


def extraction_failure(receipts, error):
    """A payload refused at preflight by every dispatched call never reached a model: a source defect."""
    detail = "MODEL_EXTRACTION_FAILED: " + str(error)
    if receipts and all(row.get("operation") == "paper.extract.preflight" for row in receipts):
        return SourcePayloadError(receipts[0]["error"], detail)
    return ValueError(detail)


class ResearchController:
    def __init__(self, repo, output, ledger):
        self.repo, self.output, self.ledger = pathlib.Path(repo).resolve(), pathlib.Path(output).resolve(), ledger
        self.plan = ledger._frozen_plan()
        self.frontier = Frontier(ledger)
        self.imports = self.plan["environment"]["evidence_imports"]
        self.catalog = _verified_json(self.plan["environment"]["source_catalog"])
        self.version_catalog = dict(self.catalog)
        for item in self.plan["environment"]["runtime_sources"]:
            path = self.repo / item["repository_path"]
            if digest(path.read_bytes()) != item["sha256"]:
                raise ValueError("RUNTIME_CHANGED_REQUIRES_A_NEW_PLAN: " + str(path))
        checkpoint = self.output / "checkpoint.json"
        self.state = json.loads(checkpoint.read_bytes()) if checkpoint.exists() else {
            "plan_id": self.plan["plan_id"], "phase": "READY", "sequence": 0, "papers": {},
            "failed_papers": [], "attempted_matches": [], "assembly": None, "graph": None,
            "query_binding": None, "controller_status": "RUNNING"}
        self.state.setdefault("version_resolutions", {})
        # Older checkpoints record attempts only; do not infer successful work.
        self.state.setdefault("match_outcomes", [])
        self.pdf_catalog, self.pdf_requests = {}, {}
        for ref in self.imports.get("pdf_sources", []):
            binding = _verified_json(ref)
            if (set(binding) != {"kind", "paper_id", "pdf_run", "requests"}
                    or binding["kind"] != "RetainedPDFSourceBinding"
                    or not isinstance(binding["requests"], list) or not binding["requests"]):
                raise ValueError("PDF_SOURCE_BINDING_INVALID")
            pid = binding["paper_id"]
            if not isinstance(pid, str) or not pid.strip():
                raise ValueError("PDF_SOURCE_BINDING_ID_REQUIRED")
            summary = _verified_json(binding["pdf_run"])
            if summary.get("paper_id") != pid:
                raise ValueError("PDF_SOURCE_BINDING_PAPER_MISMATCH")
            entry = {"pdf_run": binding["pdf_run"]}
            if pid in self.pdf_catalog and self.pdf_catalog[pid] != entry:
                raise ValueError("PDF_SOURCE_BINDING_CONFLICT")
            self.pdf_catalog[pid] = entry
            for request in binding["requests"]:
                if (not isinstance(request, dict) or not isinstance(request.get("id"), str)
                        or not request["id"] or not isinstance(request.get("downstream_node_id"), str)
                        or not request["downstream_node_id"]
                        or request.get("request_kind", request.get("kind")) != "external_claim_request"):
                    raise ValueError("PDF_SOURCE_EXTERNAL_REQUEST_REQUIRED")
                if request["id"] in self.pdf_requests:
                    raise ValueError("PDF_SOURCE_REQUEST_BINDING_DUPLICATE")
                self.pdf_requests[request["id"]] = {"request": request, "paper_id": pid, "binding": ref}
        if self.pdf_catalog:
            self.state.setdefault("pdf_sources", {})
            self.state.setdefault("pdf_match_attempts", [])
        for pid, entry in self.state.get("pdf_sources", {}).items():
            if self.pdf_catalog.get(pid) != entry:
                raise ValueError("PDF_CHECKPOINT_SOURCE_DIFFERS_FROM_PLAN")
            pdf_source_binding(pid, entry)
            admitted = ledger.db.execute("SELECT admitted,admission_json FROM frontier WHERE plan_id=? AND paper_id=?",
                                         (self.plan["plan_id"], pid)).fetchone()
            if (not admitted or admitted[0] != 1 or not admitted[1]
                    or json.loads(admitted[1]).get("pdf_run") != entry["pdf_run"]):
                raise ValueError("PDF_CHECKPOINT_SOURCE_NOT_COUNTED_IN_BUDGET")
        if self.state["plan_id"] != self.plan["plan_id"]:
            raise ValueError("Checkpoint belongs to another plan")
        if self.state["phase"] == "BUSY":
            # Never steal an outstanding worker token or refund an interrupted
            # model call. Recovery needs process-liveness evidence, not a timer.
            raise RuntimeError("IN_FLIGHT_WORK_REQUIRES_HOST_RECOVERY; inspect checkpoint and ledger")
        outstanding_calls = ledger.db.execute("SELECT COUNT(*) FROM calls WHERE plan_id=? AND state='RESERVED'", (self.plan["plan_id"],)).fetchone()[0]
        outstanding_proofs = ledger.db.execute("SELECT COUNT(*) FROM proof_attempts WHERE plan_id=? AND state='RESERVED'", (self.plan["plan_id"],)).fetchone()[0]
        if outstanding_calls or outstanding_proofs or any(row["has_active_claim"] for row in self.frontier.snapshot()["papers"]):
            raise RuntimeError("OUTSTANDING_WORK_REQUIRES_HOST_RECOVERY; no reservation was reused or refunded")
        for item in self.state["papers"].values():
            _verified_json(item["extraction"])
            assembly = _verified_graph_json(item["assembly"])
            _verified_json(assembly["response_reference"])
            _verified_json(item["provenance"])
        for item in self.imports["candidates"].values():
            for ref in item.values():
                _verified_json(ref)
        for item in self.imports["matches"]:
            _verified_json(item["response"])
        for ref in self.imports.get("extraction_batches", {}).values():
            _verified_json(ref)
        for ref in self.imports.get("extraction_scopes", {}).values():
            _verified_json(ref)
        if self.imports.get("extraction_scopes") and not self.plan["environment"].get("extract_focus_bytes"):
            raise ValueError("EXPLICIT_SCOPES_REQUIRE_BATCH_EXTRACTION_MODE")
        if self.imports.get("extraction_batches") and not self.plan["environment"].get("extract_focus_bytes"):
            raise ValueError("BATCH_REUSE_REQUIRES_BATCH_EXTRACTION_MODE")
        if self.state["assembly"]:
            _verified_graph_json(self.state["assembly"])
            _verified_graph_json(self.state["graph"])
            self.validate_query_binding()
        for requested, ref in self.state["version_resolutions"].items():
            self.adopt_version_receipt(requested, ref)
        initial_version = self.plan["environment"].get("initial_version_resolution")
        if initial_version:
            result = _verified_json(initial_version)
            self.adopt_version_receipt(result["requested_id"], initial_version)
            if (result.get("resolved") or {}).get("paper_id") != self.plan["paper_id"]:
                raise ValueError("QUERY_VERSION_METADATA_DIFFERS_FROM_PLAN")

    def adopt_version_receipt(self, requested, ref):
        result = _verified_json(ref)
        if result["requested_id"] != requested:
            raise ValueError("VERSION_RECEIPT_REQUEST_MISMATCH")
        if result.get("resolved"):
            response = result["response"]
            raw = pathlib.Path(response["path"]).read_bytes()
            if digest(raw) != response["sha256"] or len(raw) != response["byte_size"]:
                raise ValueError("VERSION_METADATA_RESPONSE_CHANGED")
            if parse_version(raw, requested) != result["resolved"]:
                raise ValueError("VERSION_RECEIPT_PARSE_MISMATCH")
            resolved_id = result["resolved"]["paper_id"]
            self.version_catalog = {pid: item for pid, item in self.version_catalog.items() if base_id(pid) != base_id(resolved_id)}
            self.version_catalog[resolved_id] = {"version_metadata": ref}

    def resolve_request_version(self, request):
        ids = {normalize_paper_id(pid) for entry in request.get("bibliography", [])
               for pid in (entry.get("identifiers") or {}).get("arxiv", [])}
        if len({base_id(pid) for pid in ids}) != 1 or any(map(pinned, ids)):
            return False
        requested = base_id(next(iter(ids)))
        if requested in self.state["version_resolutions"]:
            return False
        count = self.ledger.db.execute("SELECT COUNT(*) FROM events WHERE plan_id=? AND kind='ArxivVersionResolutionRequested'", (self.plan["plan_id"],)).fetchone()[0]
        count += int(self.plan["environment"].get("initial_version_resolution") is not None)
        if count >= self.plan["environment"].get("max_identity_requests", 0):
            self.issue("VERSION_METADATA_REQUEST_BUDGET", request["id"], "Version resolution budget exhausted; identity remains a frontier")
            return False
        self.save("BUSY", inflight={"operation": "arxiv.version.resolve", "requested_id": requested})
        request_id = "version-request:" + uuid.uuid4().hex
        # Reservation is durable before network I/O and never refunded on failure.
        self.ledger.event("ArxivVersionResolutionRequested", {"id": request_id, "requested_id": requested, "lead_id": request["id"]})
        directory = self.output / "version-metadata" / request_id.split(":")[1]
        result = resolve_version(self.repo, requested, directory)
        ref = reference(directory / "version-resolution.json")
        self.ledger.event("ArxivVersionResolutionFinished", {"id": request_id, "requested_id": requested, "receipt": ref})
        self.state["version_resolutions"][requested] = ref
        self.adopt_version_receipt(requested, ref)
        self.save(inflight=None)
        if not result.get("resolved"):
            self.issue("PAPER_VERSION_NOT_PINNED", request["id"], "Official version metadata did not establish a pinned identity", ref)
        return True

    def validate_query_binding(self):
        binding = self.state["query_binding"]
        events = self.ledger.db.execute("SELECT payload FROM events WHERE plan_id=? AND kind='QuerySelectorBound'", (self.plan["plan_id"],)).fetchall()
        if len(events) != 1 or json.loads(events[0][0]) != binding:
            raise ValueError("QUERY_BINDING_DIFFERS_FROM_UNIQUE_LEDGER_EVENT")
        selector = self.plan["environment"]["query_selector"]
        if selector.get("paper_id") != self.plan["paper_id"] or binding["selector"] != selector:
            raise ValueError("QUERY_SELECTOR_DIFFERS_FROM_FROZEN_PLAN")
        entry = self.state["papers"][self.plan["paper_id"]]
        raw = _verified_graph_json(entry["assembly"])
        paper = _verified_json(entry["extraction"])
        if (binding["source_assembly"] != entry["assembly"] or binding["query_ids"] != bind_query(selector, paper, raw) or
                raw["paper_id"] != self.plan["paper_id"] or paper["paper"]["source_sha256"] != self.plan["source_sha256"]):
            raise ValueError("QUERY_BINDING_DIFFERS_FROM_FROZEN_SOURCE_ASSEMBLY")

    def save(self, phase="READY", **updates):
        self.ledger._frozen_plan()
        self.state.update(updates, phase=phase)
        self.state["sequence"] += 1
        self.state["updated_at"] = utcnow()
        # History is immutable. checkpoint.json is explicitly the latest pointer.
        write_json(self.output / "checkpoints" / f'{self.state["sequence"]:05d}.json', self.state)
        write_json(self.output / "checkpoint.json", self.state)
        write_json(self.output / "ledger.json", self.ledger.snapshot())
        write_json(self.output / "frontier.json", self.frontier.snapshot())

    def issue(self, code, subject, detail, evidence=None):
        return self.ledger.issue(code, subject, detail, evidence)

    def paper_directory(self, pid):
        return self.output / "papers" / pid.replace(":", "-").replace("/", "-")

    def read_paper(self, pid):
        directory = self.paper_directory(pid)
        extraction = directory / "extraction.json"
        if extraction.exists():
            paper = json.loads(extraction.read_bytes())
        else:
            descriptor = self.catalog.get(pid)
            if descriptor is None and self.plan["environment"]["network_sources"]:
                acquired = fetch_arxiv_source(self.repo, pid, directory / "acquired", timeout_seconds=30)
                descriptor = acquired["source_descriptor"]
                for problem in acquired["issues"]:
                    self.issue(problem["code"], pid, problem["detail"], acquired["receipt"])
            if descriptor is None:
                raise ValueError("SOURCE_UNREACHABLE: no registered source or successful acquisition")
            paper = extract_paper(self.repo, pid, directory, source_descriptor=descriptor, source_catalog=self.catalog)
        if paper.get("paper", {}).get("id") != pid or not paper.get("source_files"):
            raise ValueError("SOURCE_READ_DEFECTIVE: absent frozen versioned source")
        sources = _frozen_source_payload(paper, directory, source_directory=directory)
        return paper, sources, directory

    def process_paper(self, work):
        pid = work["paper_id"]
        self.save("BUSY", inflight={"operation": "paper.extract", "work": work})
        settled, source_read = False, False
        try:
            with self.ledger.stage("research.paper", {"paper_id": pid, "work": work}) as receipt:
                paper, sources, directory = self.read_paper(pid)
                source_read = True
                imported = self.imports["candidates"].get(pid)
                if imported:
                    old = _verified_json(imported["extraction"])
                    signatures = lambda value: sorted((row["path"], row["sha256"], row["byte_size"]) for row in value["source_files"])
                    if old["paper"]["id"] != pid or signatures(old) != signatures(paper):
                        raise ValueError("IMPORTED_CANDIDATE_SOURCE_SNAPSHOT_MISMATCH")
                    response = _verified_json(imported["response"])
                    candidate = response.get("candidate", response)
                    response_ref = imported["response"]
                    provenance = {"kind": "PRIOR_CANDIDATE_EVIDENCE_REUSED", "input_references": imported,
                                  "new_model_call": False, "source_alignment_accepted": False}
                    self.ledger.event("CandidateEvidenceReused", {"paper_id": pid, **provenance})
                elif self.plan["environment"].get("extract_focus_bytes", 0):
                    result = extract_candidate_batches(self.ledger, paper, directory / "model-batches",
                        source_directory=directory, max_focus_bytes=self.plan["environment"]["extract_focus_bytes"],
                        max_batches=self.plan["environment"]["max_extract_batches"],
                        reuse_dispatch=self.imports.get("extraction_batches", {}).get(pid),
                        scope_manifest=self.imports.get("extraction_scopes", {}).get(pid))
                    write_json(directory / "model-batch-result.json", result)
                    if result["candidate"] is None:
                        raise extraction_failure([_verified_json(row["result"])["receipt"] for row in
                                                  _verified_json(result["dispatch"])["scopes"] if "result" in row], result["error"])
                    candidate, response_ref = result["candidate"], result["response_reference"]
                    provenance = {"kind": "LIVE_MODEL_OUTPUT_BATCHES", "dispatch": result["dispatch"],
                                  "combination": result["combination"],
                                  "complete_output_scope_responses": result["complete_output_scope_responses"],
                                  "unfinished_scope_count": result["unfinished_scope_count"],
                                  "source_completeness_asserted": False}
                    if result["unfinished_scope_count"]:
                        self.issue("PARTIAL_BATCH_EXTRACTION", pid,
                            "Some output ranges lack a successful response; extracted candidates cover only the retained subset.", result["dispatch"])
                else:
                    result = extract_candidates(self.ledger, paper, directory / "model", source_directory=directory)
                    write_json(directory / "model-result.json", result)
                    if result["candidate"] is None:
                        raise extraction_failure([result["receipt"]], result["receipt"].get("error"))
                    candidate = result["candidate"]
                    response_ref = reference(pathlib.Path(result["receipt"]["directory"]) / "response.json")
                    provenance = {"kind": "LIVE_MODEL_CANDIDATE", "receipt": result["receipt"]}
                assembly = assemble_candidates(paper, candidate, sources, response_reference=response_ref,
                    claim_reference_policy=self.plan["environment"].get("claim_reference_policy"))
                if not assembly["query_ids"]:
                    raise ValueError("NO_MATH_CANDIDATE_EXTRACTED")
                entry = {"extraction": reference(directory / "extraction.json"),
                         "assembly": write_json(directory / "assembly.json", assembly),
                         "provenance": write_json(directory / "candidate-provenance.json", provenance),
                         "scope": {"candidate_claims": len(assembly["query_ids"]),
                                   "available_heuristic_occurrences": len(paper["claims"]),
                                   "candidate_referenced_occurrences": assembly["coverage"]["candidate_covered_occurrences"],
                                   "new_exact_locators": assembly["coverage"]["new_exact_locator_count"],
                                   "uncertain_scope_reference": "assembly.unread_or_uncertain_scope",
                                   "output_batch_dispatch": provenance.get("dispatch"),
                                   "complete_output_scope_responses": provenance.get("complete_output_scope_responses"),
                                   "unfinished_scope_count": provenance.get("unfinished_scope_count"),
                                   "source_completeness_asserted": False},
                         "directory": str(directory)}
                receipt["artifacts"] = entry
                if self.state["assembly"] is None:
                    if pid != self.plan["paper_id"]:
                        raise ValueError("The first extracted paper must be the frozen query paper")
                    queries = bind_query(self.plan["environment"]["query_selector"], paper, assembly)
                self.state["papers"][pid] = entry
                if self.state["assembly"] is None:
                    self.state["query_binding"] = {"selector": self.plan["environment"]["query_selector"],
                        "query_ids": queries, "source_assembly": entry["assembly"]}
                    self.ledger.event("QuerySelectorBound", self.state["query_binding"])
                    self.publish_graph({**assembly, "query_ids": queries})
                self.frontier.record(work, len(assembly["query_ids"]), True)
                settled = True
            self.save(inflight=None)
            return True
        except Exception as error:
            if settled:
                # Publication failed after the worker token was consumed. Keep
                # BUSY and the original error; never settle that token twice.
                raise
            # Only source bytes/payload defects are source failures; model, candidate,
            # query-binding and programming errors are host processing failures.
            reason = ("SOURCE_UNREACHABLE" if str(error).startswith("SOURCE_UNREACHABLE") else "SOURCE_READ_DEFECTIVE"
                      if isinstance(error, SourcePayloadError) or not source_read and isinstance(error, (ValueError, OSError))
                      else "HOST_PROCESSING_FAILED")
            self.issue("RESEARCH_PAPER_FAILED", pid, str(error), {"failure_reason": reason, "exception_type": type(error).__name__})
            self.frontier.record(work, 0, False, failure_reason=reason)
            self.state["failed_papers"] = sorted(set(self.state["failed_papers"]) | {pid})
            self.save(inflight=None)
            return False

    def publish_graph(self, assembly):
        self.validate_query_binding()
        assembly = copy.deepcopy(assembly)
        apply_review_blocks(assembly, self.imports.get("review_blocks", []))
        apply_source_availability(assembly, self.imports.get("source_availability", []))
        apply_dependency_gaps(assembly, self.imports.get("dependency_gaps", []))
        apply_source_corrections(assembly, self.imports.get("source_corrections", []))
        if self.plan["decision_policy"] == "CANDIDATE_EXPLORATION":
            for node in assembly["nodes"]:
                node["blocked_by"] = sorted(set(node.get("blocked_by", [])) | {"CANDIDATE_EXPLORATION_REVIEW_REQUIRED"})
        queries = self.state["query_binding"]["query_ids"]
        if assembly["query_ids"] != queries:
            raise ValueError("QUERY_SCOPE_CHANGED")
        graph = select_candidate_graph(assembly, queries)
        if max(len(canonical(assembly)), len(canonical(graph))) > MAX_GRAPH_BYTES:
            raise ValueError("GRAPH_ARTIFACT_LIMIT_EXCEEDED: 64 MiB; prior graph retained")
        directory = self.output / "graphs" / f'{self.state["sequence"]:05d}-{uuid.uuid4().hex[:8]}'
        self.state["assembly"] = write_json(directory / "assembly.json", assembly)
        self.state["graph"] = write_json(directory / "graph.json", graph)

    def pending_requests(self):
        assembly = _verified_graph_json(self.state["assembly"])
        graph = _verified_graph_json(self.state["graph"])
        selected, attempted = set(graph["selected_node_ids"]), set(map(tuple, self.state["attempted_matches"]))
        batches = defaultdict(list)
        unresolved = []
        for request in assembly["dependency_requests"]:
            if request["id"] not in selected or request["request_kind"] != "external_claim_request":
                continue
            pdf_binding = self.pdf_requests.get(request["id"])
            if pdf_binding:
                if pdf_binding["request"] != request:
                    raise ValueError("PDF_SOURCE_REQUEST_SNAPSHOT_CHANGED")
                pid, reason = pdf_binding["paper_id"], "RETAINED_PDF_IDENTITY_CANDIDATE"
            else:
                pid, reason = candidate_paper(request, self.version_catalog)
            if pid is None:
                available = assembly.get("source_availability", {}).get(request["id"])
                if available:
                    gap = assembly.get("dependency_gaps", {}).get(request["id"])
                    if gap:
                        self.issue("SOURCE_BRIDGE_REQUIRED", request["id"],
                                   "Attributed missing obligations: " + "; ".join(
                                       item["kind"] + ": " + item["description"]
                                       for item in gap["missing_obligations"]), gap["review"])
                    else:
                        self.issue("PDF_SOURCE_AVAILABLE_SUPPORT_JOIN_REQUIRED", request["id"],
                                   "Retained DOI source exists; PDF support alignment remains unresolved", available["binding"])
                    continue
                if reason == "PAPER_VERSION_NOT_PINNED":
                    unresolved.append(request)
                self.issue(reason, request["id"], "No unique pinned candidate paper could be resolved from supplied bibliography evidence")
                continue
            if (request["id"], pid) in attempted or pid in self.state["failed_papers"]:
                continue
            batches[(request["from_paper_id"], pid)].append(request)
        # Read known/reused sources first. Resolve at most one new identity per
        # pass, and do not consume metadata calls after source budget exhaustion.
        if (not batches and self.plan["environment"]["network_sources"]
                and self.frontier.snapshot()["admitted_papers"] < self.plan["limits"]["max_papers"]):
            for request in unresolved:
                if self.resolve_request_version(request):
                    return self.pending_requests()
        return assembly, graph, batches

    def match_pdf_batch(self, downstream_id, upstream_id, requests):
        directory = self.output / "pdf-matches" / uuid.uuid4().hex
        published = False
        self.save("BUSY", inflight={"operation": "dependency.match.pdf",
                  "downstream_paper_id": downstream_id, "upstream_paper_id": upstream_id,
                  "request_ids": [row["id"] for row in requests], "directory": str(directory)})
        try:
            source = self.state.get("pdf_sources", {}).get(downstream_id)
            if source is None:
                entry = self.state["papers"][downstream_id]
                source = {key: entry[key] for key in ("extraction", "directory")}
            summary = run_pdf_match(self.ledger, self.state["assembly"], [row["id"] for row in requests],
                                    source, upstream_id, self.pdf_catalog[upstream_id]["pdf_run"], directory)
            if summary["status"] == "CANDIDATE_JOIN_RECORDED":
                self.publish_graph(_verified_graph_json(summary["assembly"]))
                published = True
        except Exception as error:
            self.issue("PDF_RESEARCH_MATCH_FAILED", upstream_id, str(error))
        # Interruptions bypass this block and leave BUSY for explicit recovery.
        # Normal failures remain attempted, so continuation does not repay a call.
        if (directory / "summary.json").is_file():
            ref = reference(directory / "summary.json")
            summary = _verified_json(ref)
            self.state["pdf_match_attempts"].append(ref)
            outcomes = _verified_json(summary["outcomes"])
            self.state["match_outcomes"].extend({**row, "pdf_attempt": ref,
                "research_graph_published": published and row.get("relation") == "CANDIDATE_SUPPORT"}
                for row in outcomes)
        else:
            self.state["match_outcomes"].extend({"request_id": row["id"], "upstream_paper_id": upstream_id,
                "status": "PDF_DISPATCH_FAILED_BEFORE_SUMMARY", "mathematically_resolved": False,
                "automatic_retry": False} for row in requests)
        self.state["attempted_matches"].extend([row["id"], upstream_id] for row in requests)
        self.save(inflight=None)

    def match_batch(self, downstream_id, upstream_id, requests):
        directory = self.output / "matches" / uuid.uuid4().hex
        directory.mkdir(parents=True)
        outcomes = {row["id"]: {"request_id": row["id"], "upstream_paper_id": upstream_id,
                    "status": "DISPATCH_FAILED", "mathematically_resolved": False,
                    "automatic_retry": False, "attempt_directory": str(directory)} for row in requests}
        self.save("BUSY", inflight={"operation": "dependency.match", "downstream_paper_id": downstream_id,
                                   "upstream_paper_id": upstream_id, "request_ids": [row["id"] for row in requests]})
        try:
            downstream, _, down_dir = self.read_paper(downstream_id)
            upstream, sources, up_dir = self.read_paper(upstream_id)
            up_assembly = _verified_graph_json(self.state["papers"][upstream_id]["assembly"])
            base = _verified_graph_json(self.state["assembly"])
            wanted = {row["id"] for row in requests}
            imported = next((row for row in self.imports["matches"] if
                             (row["downstream_paper_id"], row["upstream_paper_id"]) == (downstream_id, upstream_id)), None)
            rows, used, origins = [], set(), []
            if imported:
                raw = _verified_json(imported["response"])
                for row in raw["matches"]:
                    if row["target_request_id"] in wanted:
                        rows.append(row)
                        used.add(row["target_request_id"])
                origins.append({"kind": "PRIOR_MATCH_EVIDENCE_REUSED", "reference": imported["response"],
                                "new_model_call": False, "selected_request_ids": sorted(used)})
                self.ledger.event("MatchEvidenceReused", origins[-1])
            remaining = [row for row in requests if row["id"] not in used]
            if remaining:
                try:
                    result = match_source_candidates(self.ledger, remaining, downstream, down_dir, upstream, up_dir,
                        up_assembly, directory / "model", downstream_assembly=base)
                    write_json(directory / "model-result.json", result)
                    for request in remaining:
                        outcomes[request["id"]].update(status="MODEL_RESPONSE_UNAVAILABLE",
                            model_result=reference(directory / "model-result.json"))
                    if result["candidate"] is not None:
                        rows.extend(result["candidate"]["matches"])
                        origins.append({"kind": "LIVE_MODEL_MATCH", "receipt": result["receipt"]})
                    else:
                        self.issue("SOURCE_MATCH_MODEL_FAILED", upstream_id, str(result["receipt"].get("error")))
                        if result.get("partial_candidate"):
                            rows.extend(result["partial_candidate"]["matches"])
                            origins.append({"kind": "PARTIAL_MODEL_MATCH_ROWS", "receipt": result["receipt"],
                                            "reference": result["partial_selection"]})
                except Exception as error:
                    self.issue("SOURCE_MATCH_DISPATCH_FAILED", upstream_id, str(error))
            if rows:
                matches = {"matches": rows}
                match_ref = write_json(directory / "selected-matches.json", matches)
                for row in rows:
                    if row["target_request_id"] in outcomes:
                        outcomes[row["target_request_id"]].update(status="JOIN_NOT_PUBLISHED", matches=match_ref)
                input_refs = {"base": self.state["assembly"], "upstream": self.state["papers"][upstream_id]["assembly"],
                              "matches": match_ref, "upstream_extraction": self.state["papers"][upstream_id]["extraction"]}
                with self.ledger.stage("research.join", input_refs) as receipt:
                    joined = join_candidate_paper(base, up_assembly, matches, sources, matches_reference=match_ref,
                        resolve_explicit_occurrences=self.plan["environment"].get("source_join_policy") ==
                        "EXPLICIT_CLAIM_IDS_DISAMBIGUATE_OCCURRENCES_V1")
                    self.publish_graph(joined["assembly"])
                    receipt["assembly"] = self.state["assembly"]
                    receipt["graph"] = self.state["graph"]
                    receipt["provenance"] = write_json(directory / "provenance.json", {"inputs": input_refs, "origins": origins})
                    for request_id, outcome in outcomes.items():
                        records = [row for row in joined["assembly"].get("match_records", [])
                                   if row["target_request_id"] == request_id and row["matches_reference"] == match_ref]
                        if records:
                            outcome.update(status=("JOIN_REJECTED" if any(row["status"] == "UNRESOLVED" for row in records)
                                                   else "JUDGEMENT_RECORDED_UNREVIEWED"),
                                judgement_statuses=sorted({row["status"] for row in records}),
                                provenance=receipt["provenance"])
            for request in requests:
                self.state["attempted_matches"].append([request["id"], upstream_id])
            self.state["match_outcomes"].extend(outcomes.values())
            self.save(inflight=None)
        except Exception as error:
            self.issue("RESEARCH_MATCH_FAILED", upstream_id, str(error))
            for request in requests:
                self.state["attempted_matches"].append([request["id"], upstream_id])
            self.state["match_outcomes"].extend(outcomes.values())
            self.save(inflight=None)

    def run(self):
        if self.state["assembly"] is None:
            work = self.frontier.seed(self.plan["paper_id"])
            if not work or work.get("state") != "RUNNING" or not work.get("claim_token"):
                raise RuntimeError("QUERY_WORK_NOT_AVAILABLE")
            if not self.process_paper(work):
                if self.ledger.provider_failure() is not None:
                    self.issue("MODEL_PROVIDER_CIRCUIT_OPEN", self.plan["plan_id"],
                               "Initial query extraction stopped on a provider failure.", self.ledger.provider_failure())
                    return self.finish("MODEL_PROVIDER_CIRCUIT_OPEN")
                return self.finish("QUERY_EXTRACTION_FAILED")
        while True:
            if self.ledger.provider_failure() is not None:
                self.issue("MODEL_PROVIDER_CIRCUIT_OPEN", self.plan["plan_id"],
                           "Provider failure retained; no further model dispatch in this plan.",
                           self.ledger.provider_failure())
                return self.finish("MODEL_PROVIDER_CIRCUIT_OPEN")
            assembly, graph, batches = self.pending_requests()
            if not batches:
                return self.finish("NO_FURTHER_RESOLVED_SOURCE_WORK")
            # Process already read sources first, then evidence that can be reused
            # without another extraction call. Ordering is frozen in the plan.
            order = lambda pair: (pair[1] not in self.state["papers"],
                                  pair[1] not in self.imports["candidates"], pair[1], pair[0])
            progressed = False
            for (downstream, upstream), requests in sorted(batches.items(), key=lambda item: order(item[0])):
                requests = requests[:self.plan["environment"].get("max_match_requests", len(requests))]
                if upstream in self.pdf_catalog:
                    if self.plan["decision_policy"] != "CANDIDATE_EXPLORATION":
                        self.issue("UNCALIBRATED_PDF_SOURCE_MATCH", upstream, "PDF identity and support remain unreviewed")
                        continue
                    request = requests[0]
                    admission = self.frontier.admit_retained_pdf(upstream, self.pdf_catalog[upstream]["pdf_run"],
                        {"lead_id": request["id"], "upstream_node_id": request["id"],
                         "downstream_node_id": request["downstream_node_id"]}, graph)
                    if not admission["admitted"]:
                        self.issue(admission["reason"], upstream, "Retained PDF still consumes a paper slot")
                        continue
                    self.state["pdf_sources"][upstream] = self.pdf_catalog[upstream]
                    self.match_pdf_batch(downstream, upstream, requests)
                    progressed = True
                    break
                if downstream in self.state.get("pdf_sources", {}):
                    self.issue("PDF_TO_TEX_MATCH_NOT_IMPLEMENTED", downstream,
                               "Do not send an opaque PDF identity to the arXiv source reader")
                    continue
                if upstream in self.state["papers"]:
                    if self.plan["decision_policy"] != "CANDIDATE_EXPLORATION":
                        # Cached evidence does not bypass the same source-support
                        # gate that applies to a newly admitted paper.
                        self.issue("UNCALIBRATED_CACHED_SOURCE_MATCH", upstream, "Strict policy requires source support and identity review before matching")
                        continue
                    self.match_batch(downstream, upstream, requests)
                    progressed = True
                    break
                request = requests[0]
                node = next(row for row in assembly["nodes"] if row["id"] == request["downstream_node_id"])
                decision = self.frontier.consider({"paper_id": upstream, "lead_id": request["id"],
                    "upstream_node_id": request["id"], "downstream_node_id": request["downstream_node_id"],
                    "terminal_kind": "ARXIV_SOURCE_AVAILABLE", "confidence": node.get("confidence"),
                    "identity_confidence": {"source": "SELF_REPORTED", "value": 0, "calibration_ref": None}},
                    graph, calibration_registry={})
                if decision["state"] != "QUEUED":
                    continue
                work = self.frontier.take(graph, calibration_registry={})
                if work is None:
                    continue
                self.process_paper(work)
                progressed = True
                break
            if not progressed:
                return self.finish("FRONTIER_POLICY_OR_BUDGET_LIMIT")

    def finish(self, status):
        self.save(controller_status=status, inflight=None)
        graph = _verified_graph_json(self.state["graph"]) if self.state["graph"] else None
        kinds = Counter()
        if graph:
            bibliography = {row["id"]: row for entry in self.state["papers"].values()
                            for row in _verified_json(entry["extraction"])["bibliography"]}
            # Unresolved: selected and not the target of an accepted group (an unreviewed match resolves nothing).
            open_ids = set(graph["selected_node_ids"]) - {row["target"] for row in graph["support_groups"]
                                                          if row["disposition"] == "SOURCE_FROZEN_HUMAN_SIGNED"}
            kinds.update(terminal_kind(row, bibliography) for row in _verified_graph_json(self.state["assembly"])["dependency_requests"]
                         if row["request_kind"] == "external_claim_request" and row["id"] in open_ids)
        summary = {"kind": "RecursiveResearchResult", "plan_id": self.plan["plan_id"], "controller_status": status,
                   "mathematical_status": "CHAIN_INCOMPLETE", "papers_extracted": len(self.state["papers"]),
                   "query_candidates": len(self.state["query_binding"]["query_ids"]) if self.state["query_binding"] else 0,
                   "nodes": len(graph["nodes"]) if graph else 0,
                   "support_groups": len(graph["support_groups"]) if graph else 0,
                   "model_calls_in_this_plan": len(self.ledger.snapshot()["calls"]),
                   "match_outcome_counts": {status: sum(row["status"] == status for row in self.state["match_outcomes"])
                       for status in sorted({row["status"] for row in self.state["match_outcomes"]})},
                   "attempted_matches_are_not_resolved_dependencies": True,
                   "legacy_attempts_without_outcome": len(set(map(tuple, self.state["attempted_matches"])) -
                       {(row["request_id"], row["upstream_paper_id"]) for row in self.state["match_outcomes"]}),
                   "version_metadata_requests_in_this_plan": self.ledger.db.execute("SELECT COUNT(*) FROM events WHERE plan_id=? AND kind='ArxivVersionResolutionRequested'", (self.plan["plan_id"],)).fetchone()[0] + int(self.plan["environment"].get("initial_version_resolution") is not None),
                   "paper_scopes": {pid: entry.get("scope", {"source_completeness_asserted": False})
                                    for pid, entry in self.state["papers"].items()},
                   "all_judgements_unreviewed": True, "source_completeness_asserted": False,
                   "accepted_support_edges": accepted_support_edges(graph), "proof_backend": "SEPARATE_STAGE_PROOF_WALK",
                   "frontier_terminal_kinds": dict(sorted(kinds.items())),
                   "legacy_dag_edges_used": False,
                   "checkpoint": reference(self.output / "checkpoints" / f'{self.state["sequence"]:05d}.json')}
        if self.state.get("pdf_sources"):
            summary["retained_pdf_sources"] = self.state["pdf_sources"]
            summary["retained_pdf_paper_count"] = len(self.state["pdf_sources"])
            summary["pdf_match_attempt_count"] = len(self.state["pdf_match_attempts"])
            summary["pdf_recursive_reconstruction_audit"] = "NOT_EXECUTED"
        write_json(self.output / "results" / f'{self.state["sequence"]:05d}.json', summary)
        write_json(self.output / "summary.json", summary)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", required=True)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--imports", type=pathlib.Path)
    parser.add_argument("--extraction-profile", choices=("LIGHT", "LIGHT_TERRA"),
                        help="New-plan extraction model: LIGHT uses Luna (default), LIGHT_TERRA uses Terra; resume cannot change a frozen route")
    parser.add_argument("--max-papers", type=int, default=5)
    parser.add_argument("--max-model-calls", type=int, default=12)
    parser.add_argument("--max-match-requests", type=int, default=4,
                        help="Maximum external requests in one semantic matching call")
    parser.add_argument("--max-call-seconds", type=int, default=300)
    parser.add_argument("--extract-focus-bytes", type=int, default=8192,
                        help="Bytes per output scope with complete source context; 0 selects a single whole-paper output")
    parser.add_argument("--max-extract-batches", type=int, default=128)
    parser.add_argument("--network-sources", action="store_true")
    parser.add_argument("--max-identity-requests", type=int, default=8)
    parser.add_argument("--candidate-exploration", action="store_true")
    parser.add_argument("--query-label", action="append", dest="query_labels",
                        help="Repeatable source \\label of the query paper; new plans query only the claims it locates")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    with controller_lock(args.output):
        return execute(args, parser)


def execute(args, parser):
    repo = pathlib.Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if not output.is_relative_to(repo):
        parser.error("The research run must live inside the repository")
    if args.max_papers < 1 or args.max_model_calls < 0 or args.max_call_seconds < 1 or not 0 <= args.max_identity_requests <= 64:
        parser.error("Invalid resource limit")
    if args.extract_focus_bytes != 0 and not 1024 <= args.extract_focus_bytes <= 131072:
        parser.error("Output focus must be 0 or 1024–131072 bytes")
    if not 1 <= args.max_extract_batches <= 512:
        parser.error("Output batch limit must be 1–512")
    if args.resume:
        plan = json.loads((output / "plan.json").read_bytes())
        frozen_profile = plan.get("environment", {}).get("model_routing", {}).get("operations", {}).get("paper.extract", {}).get("profile")
        if args.extraction_profile is not None and args.extraction_profile != frozen_profile:
            parser.error("Resume cannot change a frozen extraction route; create a new plan and import existing successes")
        if base_id(args.paper) != base_id(plan["paper_id"]) or (pinned(normalize_paper_id(args.paper)) and normalize_paper_id(args.paper) != plan["paper_id"]):
            parser.error("Resume paper differs from the frozen plan")
        if args.query_labels and plan["environment"]["query_selector"].get("labels") != sorted(set(args.query_labels)):
            parser.error("Resume cannot change a frozen query selector")
    else:
        if not 1 <= args.max_match_requests <= 64:
            parser.error("Matching request batch size must be 1–64")
        if output.exists() and any(output.iterdir()):
            parser.error("Use a fresh run directory, or --resume with its frozen plan")
        requested = normalize_paper_id(args.paper)
        catalog = discover_sources(repo)
        versions = [pid for pid in catalog if base_id(pid) == base_id(requested)]
        pid = requested if pinned(requested) else versions[0] if len(versions) == 1 else None
        version_ref = None
        if pid is None and args.network_sources and args.max_identity_requests > 0:
            resolution = resolve_version(repo, requested, output / "initial-version-metadata")
            version_ref = reference(output / "initial-version-metadata/version-resolution.json")
            if resolution.get("resolved"):
                pid = resolution["resolved"]["paper_id"]
        if pid is None:
            parser.error("Version unresolved: no explicit/local/official metadata version was established; any metadata receipt is retained")
        output.mkdir(parents=True, exist_ok=True)
        initial_dir = output / "papers" / pid.replace(":", "-").replace("/", "-")
        descriptor = catalog.get(pid)
        if descriptor is None and args.network_sources:
            acquired = fetch_arxiv_source(repo, pid, initial_dir / "acquired")
            descriptor = acquired["source_descriptor"]
        if descriptor is None:
            write_json(output / "source-frontier.json", {"paper_id": pid, "status": "SOURCE_UNREACHABLE", "origin_established": False})
            parser.error("Query source unavailable; source-frontier.json records this boundary")
        paper = extract_paper(repo, pid, initial_dir, source_descriptor=descriptor, source_catalog=catalog)
        _frozen_source_payload(paper, initial_dir, source_directory=initial_dir)
        missing = sorted(set(args.query_labels or []) - set(paper["labels"]))
        if missing:
            parser.error("Query labels absent from the frozen source: " + ", ".join(missing))
        catalog[pid] = descriptor
        runtime = []
        files = sorted(pathlib.Path(__file__).parent.glob("*.py")) + [repo / "tools/extract_provisional_claims.py"]
        for path in files:
            raw = path.read_bytes()
            destination = output / "runtime" / path.relative_to(repo)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
            runtime.append({"repository_path": path.relative_to(repo).as_posix(), "sha256": digest(raw), "snapshot": str(destination)})
        plan = {"contract_version": VERSION, "plan_id": "plan:" + uuid.uuid4().hex, "paper_id": pid,
                "query_ids": [], "created_at": utcnow(), "cost_mode": "ACCOUNT_QUOTA",
                "decision_policy": "CANDIDATE_EXPLORATION" if args.candidate_exploration else "STRICT_CALIBRATED",
                "limits": {"max_papers": args.max_papers, "max_model_calls": args.max_model_calls,
                           "max_call_seconds": args.max_call_seconds, "max_cost_microusd": 0,
                           "no_progress_limit": 1, "max_node_attempts": 1},
                "source_sha256": paper["paper"]["source_sha256"],
                "environment": {"mode": "RECURSIVE_RESEARCH", "model_routing": freeze_model_routing(args.extraction_profile or "LIGHT"),
                    "query_selector": {"kind": "SOURCE_LABELS", "paper_id": pid, "labels": sorted(set(args.query_labels))}
                        if args.query_labels else {"kind": "ALL_EXTRACTED_MATH_CLAIMS", "paper_id": pid},
                    "query_binding_policy": "HOST_BINDS_EXACT_EXTRACTED_IDS_ONCE_WITH_LEDGER_EVENT",
                    "paper_version_basis": "OFFICIAL_ATOM_METADATA" if version_ref else "EXPLICIT_INPUT" if pinned(requested) else "UNIQUE_LOCAL_REGISTERED_VERSION_NOT_LATEST_ASSERTION",
                    "initial_version_resolution": version_ref, "max_identity_requests": args.max_identity_requests,
                    "extract_focus_bytes": args.extract_focus_bytes, "max_extract_batches": args.max_extract_batches,
                    "max_match_requests": args.max_match_requests,
                    "source_join_policy": "EXPLICIT_CLAIM_IDS_DISAMBIGUATE_OCCURRENCES_V1",
                    "claim_reference_policy": CLAIM_REFERENCE_POLICY,
                    "network_sources": args.network_sources, "evidence_imports": freeze_imports(args.imports),
                    "source_catalog": write_json(output / "source-catalog.json", catalog), "runtime_sources": runtime,
                    "scheduling_order": "READ_PAPERS_THEN_IMPORTED_CANDIDATES_THEN_PINNED_ID",
                    "proof_backend": "SEPARATE_STAGE_PROOF_WALK"}}
        write_json(output / "plan.json", plan)
    ledger = PlanLedger(output, plan)
    summary = ResearchController(repo, output, ledger).run()
    print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(2)  # honest incomplete mathematical result, even when crawl operations succeed


if __name__ == "__main__":
    main()
