#!/usr/bin/env python3
"""Extract deterministic, review-required semantic-claim candidates from LaTeX.

This is deliberately a high-recall first pass.  Its outputs are provisional and
are kept separate from the authoritative MathClaimIR registries.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Stabilizerness/ProvisionalClaimRegistry"
BASELINE_COMMIT = "132b4ca17e098d37fa265b6bc42550845bc1dec5"
SCHEMA_VERSION = "agtxiv.provisional-semantic-claims/0.1.0"
STATIC_REGISTRY_FILES = (
    "README.md",
    "schema/source-claim-occurrence.schema.json",
    "schema/canonical-semantic-candidate.schema.json",
    "schema/canonical-claim-module.schema.json",
    "schema/candidate-graph.schema.json",
    "schema/paper-delta.schema.json",
)

PAPERS = (
    ("arxiv:2607.26154v1", "graph-theoretic-nonstabilizerness", "Stabilizerness/arXiv-2607.26154v1/draft.tex", "4a84425a4d56efe5b5bee4814a09c99996ab7a6bd279574d567979c248f81c1d"),
    ("arxiv:2602.18939v1", "predicting-magic-from-very-few-measurements", "Reference/Predicting magic from very few measurements/pra_version.tex", "b0631e958da1934aa7b87d60d009499b9189f435773cccc74b4e782ab985d4e5"),
    ("arxiv:1609.07488v2", "robustness-of-magic", "Reference/Application of a resource theory for magic states to fault-tolerant quantum computing/Robustness_main_appendix.tex", "48adf581a5f8353bb1125c75b8e0a075ff7ba79917f2a12d9f7e0f4ad1a8312d"),
    ("arxiv:1307.7171v1", "resource-theory-of-stabilizer-computation", "Reference/The Resource Theory of Stabilizer Computation/stab_resource_theory_021.tex", "1634926605e816b6bc0728559e2b7471750fdc849cf127f971e6ee859d277394"),
    ("arxiv:quant-ph/9705052v1", "stabilizer-codes-and-quantum-error-correction", "Reference/Stabilizer Codes and Quantum Error Correction/Thesis.tex", "79c810480bcce5635cd9507170c5327662bd33546c4638baa037c608db49db2f"),
)

SECTION_START_RE = re.compile(r"\\(part|chapter|section|subsection|subsubsection|paragraph)\*?\s*\{")
BEGIN_RE = re.compile(r"\\begin\{([^}]+)\}")
DISPLAY_ENVS = {"equation", "equation*", "align", "align*", "eqnarray", "eqnarray*", "gather", "gather*", "multline", "multline*", "displaymath"}
THEOREM_ENVS = {"theorem", "thm", "lemma", "lem", "proposition", "prop", "corollary", "cor", "lemmaCollapseRestatement", "propRelaxationRestatement", "theoremMwisRestatement", "theoremSolvableRestatement"}
DEFINITION_ENVS = {"definition", "defn"}
CONJECTURE_ENVS = {"conjecture"}
DERIVATION_CUE_RE = re.compile(r"\b(therefore|thus|hence|so|it follows|which implies|we obtain|consequently|we conclude)\b", re.IGNORECASE)
SKIP_ENVS = {"figure", "figure*", "table", "table*", "tikzpicture", "picture", "thebibliography", "acknowledgements", "acknowledgments"}
SECTION_LEVEL = {"part": 0, "chapter": 1, "section": 2, "subsection": 3, "subsubsection": 4, "paragraph": 5}


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    kind: str
    speech_act: str
    reasons: tuple[str, ...]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def source_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources(papers: Iterable[tuple[str, str, str, str]], root: Path) -> list[tuple[str, str, str, str, Path]]:
    """Verify configured, agent-recorded, and actual source identities before writes."""
    verified = []
    for paper_id, slug, artifact, expected in papers:
        manifest_path = root / f"Stabilizerness/PaperAgentRegistry/manifests/{slug}.json"
        manifest = json.loads(manifest_path.read_text())
        manifest_artifact = manifest.get("source", {}).get("canonical_artifact")
        manifest_hash = manifest.get("source", {}).get("artifact_hash")
        if manifest.get("paper_id") != paper_id:
            raise RuntimeError(f"agent manifest paper mismatch for {slug}: configured {paper_id}, manifest {manifest.get('paper_id')}")
        if manifest_artifact != artifact:
            raise RuntimeError(f"agent manifest artifact mismatch for {slug}: configured {artifact}, manifest {manifest_artifact}")
        if manifest_hash != f"sha256:{expected}":
            raise RuntimeError(f"agent manifest hash mismatch for {slug}: configured sha256:{expected}, manifest {manifest_hash}")
        path = root / artifact
        actual = source_digest(path)
        if actual != expected:
            raise RuntimeError(f"source hash mismatch for {artifact}: expected {expected}, found {actual}")
        verified.append((paper_id, slug, artifact, expected, path))
    return verified


def strip_comment(line: str) -> str:
    """Remove a TeX comment while preserving percent signs escaped by an odd slash run."""
    for index, char in enumerate(line):
        if char != "%":
            continue
        slashes = 0
        cursor = index - 1
        while cursor >= 0 and line[cursor] == "\\":
            slashes += 1
            cursor -= 1
        if slashes % 2 == 0:
            return line[:index]
    return line


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", "\n".join(strip_comment(line) for line in text.splitlines())).strip()


def readable_text(text: str) -> str:
    text = re.sub(r"\\(?:cite|ref|eqref|label|footnote|emph|textbf|textit)\*?(?:\[[^]]*\])?\{([^{}]*)\}", r" \1 ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", " ", text)
    return re.sub(r"[{}$~_^&\\]", " ", text)


def configured_environment(env: str, configured: set[str]) -> bool:
    """Match configured environment names, optionally with the controlled TeX star suffix."""
    return env.rstrip("*") in configured and env[len(env.rstrip("*")):] in {"", "*"}


def find_environment_end(clean: list[str], start: int, env: str) -> int:
    depth = 0
    begin = re.compile(r"\\begin\{" + re.escape(env) + r"\}")
    end = re.compile(r"\\end\{" + re.escape(env) + r"\}")
    for index in range(start, len(clean)):
        depth += len(begin.findall(clean[index]))
        depth -= len(end.findall(clean[index]))
        if depth <= 0:
            return index
    return len(clean) - 1


def balanced_argument(lines: list[str], start_line: int, opening: int) -> tuple[str, int]:
    """Return a balanced braced argument and its inclusive final line index."""
    depth = 0
    chunks: list[str] = []
    for line_index in range(start_line, len(lines)):
        line = lines[line_index]
        cursor = opening if line_index == start_line else 0
        while cursor < len(line):
            char = line[cursor]
            escaped = cursor > 0 and (len(line[:cursor]) - len(line[:cursor].rstrip("\\"))) % 2 == 1
            if char == "{" and not escaped:
                depth += 1
                if depth > 1:
                    chunks.append(char)
            elif char == "}" and not escaped:
                depth -= 1
                if depth == 0:
                    return "".join(chunks), line_index
                chunks.append(char)
            elif depth:
                chunks.append(char)
            cursor += 1
        if depth:
            chunks.append("\n")
    raise ValueError(f"unclosed section heading beginning on line {start_line + 1}")


def clean_section_title(title: str) -> str:
    title = re.sub(r"\\label\s*\{[^{}]*\}", "", title)
    title = re.sub(r"\\(?:emph|textbf|textit|texorpdfstring)\s*\{([^{}]*)\}", r"\1", title)
    return normalize_text(title) or "(untitled)"


def parse_section_headings(clean: list[str]) -> list[tuple[int, int, str, str]]:
    headings = []
    index = 0
    while index < len(clean):
        match = SECTION_START_RE.search(clean[index])
        if not match:
            index += 1
            continue
        title, end = balanced_argument(clean, index, match.end() - 1)
        headings.append((index, end, match.group(1), clean_section_title(title)))
        index = end + 1
    return headings


def section_paths(clean: list[str]) -> list[list[str]]:
    current: dict[int, str] = {}
    paths: list[list[str]] = [[] for _ in clean]
    headings = {start: (end, command, title) for start, end, command, title in parse_section_headings(clean)}
    index = 0
    while index < len(clean):
        heading = headings.get(index)
        if heading:
            end, command, title = heading
            level = SECTION_LEVEL[command]
            current = {key: value for key, value in current.items() if key < level}
            current[level] = title
            for line_index in range(index, end + 1):
                paths[line_index] = [current[key] for key in sorted(current)]
            index = end + 1
            continue
        paths[index] = [current[key] for key in sorted(current)]
        index += 1
    return paths


def prose_speech_act(text: str) -> tuple[str, tuple[str, ...]] | None:
    plain = readable_text(normalize_text(text)).lower()
    words = re.findall(r"[a-zA-Z]+", plain)
    if len(words) < 5 or plain.lstrip().startswith(("bibliography", "acknowledg")):
        return None
    attributed = bool(re.search(r"\b(according to|shown in|proved in|as in|it is known|has been shown)\b", plain))
    rules = (
        ("CONJECTURE", r"\b(conjecture|conjectured|we expect|we hypothesi[sz]e)\b"),
        ("ASSUMPTION", r"\b(we assume|assume that|suppose that|under the assumption|we restrict to)\b"),
        ("DERIVATION_CONCLUSION", r"\b(therefore|thus|hence|it follows|we obtain|consequently|which implies|we conclude)\b"),
        ("EXAMPLE_INSTANCE", r"\b(for example|as an example|consider the example|example:)\b"),
        ("DEFINITION", r"\b(we define|is defined (?:as|by)|are defined (?:as|by)|we call|is called)\b"),
        ("NOTATION", r"\b(we denote|denoted by|we write|notation|let [a-z])\b"),
    )
    for act, pattern in rules:
        if re.search(pattern, plain):
            return act, ("AUTOMATIC_HEURISTIC", "REVIEW_REQUIRED", "LOW_CONFIDENCE_SEMANTIC_LABEL")
    if attributed:
        return "ATTRIBUTED_ASSERTION", ("AUTOMATIC_HEURISTIC", "ATTRIBUTION_DETECTED", "REVIEW_REQUIRED", "LOW_CONFIDENCE_SEMANTIC_LABEL")
    assertion = re.search(r"\b(we show|we prove|we find|we establish|satisf(?:y|ies)|is equal to|are equal to|is bounded|upper bound|lower bound|if and only if|iff|there exists|for all|cannot|must|implies?|yields?|is monotone|are equivalent|can be written|is given by)\b", plain)
    mathematical = bool(re.search(r"[=<>]|\\(?:leq|geq|in|sum|prod|operatorname|mathbb|mathcal)|\$", normalize_text(text)))
    if assertion or (mathematical and len(words) >= 9 and re.search(r"\b(is|are|can|will|has|have)\b", plain)):
        return "MATHEMATICAL_ASSERTION", ("AUTOMATIC_HEURISTIC", "REVIEW_REQUIRED", "LOW_CONFIDENCE_SEMANTIC_LABEL")
    return None


def extract_spans(lines: list[str]) -> list[Span]:
    clean = [strip_comment(line) for line in lines]
    document_start = next((i for i, line in enumerate(clean) if "\\begin{document}" in line), 0)
    structured: list[Span] = []
    paragraph_blocked: set[int] = set(range(document_start))

    for index, line in enumerate(clean):
        for match in BEGIN_RE.finditer(line):
            env = match.group(1)
            if env in DISPLAY_ENVS:
                end = find_environment_end(clean, index, env)
                structured.append(Span(index + 1, end + 1, "DISPLAY_EQUATION", "UNRESOLVED", ("EQUATION_WITHOUT_SEMANTIC_PARSE", "REVIEW_REQUIRED")))
                paragraph_blocked.update(range(index, end + 1))
            elif configured_environment(env, DEFINITION_ENVS):
                end = find_environment_end(clean, index, env)
                structured.append(Span(index + 1, end + 1, "DEFINITION_ENVIRONMENT", "DEFINITION", ("EXPLICIT_LATEX_STRUCTURE", "REVIEW_REQUIRED")))
                paragraph_blocked.update(range(index, end + 1))
            elif configured_environment(env, THEOREM_ENVS):
                end = find_environment_end(clean, index, env)
                structured.append(Span(index + 1, end + 1, "THEOREM_LIKE_ENVIRONMENT", "MATHEMATICAL_ASSERTION", ("EXPLICIT_LATEX_STRUCTURE", "REVIEW_REQUIRED")))
                paragraph_blocked.update(range(index, end + 1))
            elif configured_environment(env, CONJECTURE_ENVS):
                end = find_environment_end(clean, index, env)
                structured.append(Span(index + 1, end + 1, "THEOREM_LIKE_ENVIRONMENT", "CONJECTURE", ("EXPLICIT_LATEX_STRUCTURE", "REVIEW_REQUIRED")))
                paragraph_blocked.update(range(index, end + 1))
            elif env in SKIP_ENVS or env.rstrip("*") in SKIP_ENVS:
                paragraph_blocked.update(range(index, find_environment_end(clean, index, env) + 1))

    # TeX display delimiters not represented as environments.
    index = document_start
    while index < len(clean):
        stripped = clean[index].strip()
        if stripped.startswith("\\[") or stripped.startswith("$$"):
            close = "\\]" if stripped.startswith("\\[") else "$$"
            end = index
            if not (close == "$$" and stripped.count("$$") >= 2):
                end += 1
                while end < len(clean) and close not in clean[end]:
                    end += 1
                end = min(end, len(clean) - 1)
            structured.append(Span(index + 1, end + 1, "DISPLAY_EQUATION", "UNRESOLVED", ("EQUATION_WITHOUT_SEMANTIC_PARSE", "REVIEW_REQUIRED")))
            paragraph_blocked.update(range(index, end + 1))
            index = end + 1
        else:
            index += 1

    paragraphs: list[Span] = []
    heading_lines = {line_index for start, end, _, _ in parse_section_headings(clean) for line_index in range(start, end + 1)}
    index = document_start
    while index < len(lines):
        if index in paragraph_blocked or not clean[index].strip() or index in heading_lines:
            index += 1
            continue
        if re.match(r"\s*\\(?:begin|end|documentclass|usepackage|newcommand|renewcommand|title|author|affiliation|date|maketitle|bibliography|bibliographystyle|caption|includegraphics)\b", clean[index]):
            index += 1
            continue
        start = index
        while index + 1 < len(lines) and index + 1 not in paragraph_blocked and index + 1 not in heading_lines:
            next_comment_only = bool(lines[index + 1].strip()) and not clean[index + 1].strip()
            if not clean[index + 1].strip() and not next_comment_only:
                break
            if re.match(r"\s*\\(?:begin|end|caption|includegraphics)\b", clean[index + 1]):
                break
            index += 1
        text = "\n".join(lines[start:index + 1])
        classified = prose_speech_act(text)
        if classified:
            act, reasons = classified
            paragraphs.append(Span(start + 1, index + 1, "PROSE_PARAGRAPH", act, reasons))
        index += 1

    spans = structured + paragraphs
    displays = sorted((span for span in structured if span.kind == "DISPLAY_EQUATION"), key=lambda span: span.start)
    for display_index, display in enumerate(displays):
        previous_end = displays[display_index - 1].end if display_index else 0
        next_start = displays[display_index + 1].start if display_index + 1 < len(displays) else len(lines) + 1
        before = max(
            (p for p in paragraphs if previous_end < p.start and p.end < display.start and display.start - p.end <= 3 and (not previous_end or display.start - p.end < p.start - previous_end)),
            key=lambda p: p.end,
            default=None,
        )
        after = min(
            (p for p in paragraphs if display.end < p.start and p.end < next_start and p.start - display.end <= 3 and (next_start > len(lines) or p.start - display.end < next_start - p.end)),
            key=lambda p: p.start,
            default=None,
        )
        if not before and not after:
            continue
        context = [span for span in (before, after) if span]
        cue_spans = [span for span in context if DERIVATION_CUE_RE.search(normalize_text("\n".join(lines[span.start - 1:span.end])))]
        if cue_spans:
            kind = "EQUATION_DISCOURSE_BUNDLE"
            speech_act = "DERIVATION_CONCLUSION"
            reasons = ("MULTI_SPAN_SYNTHESIS", "EXPLICIT_DERIVATION_CUE", "REVIEW_REQUIRED", "LOW_CONFIDENCE_SEMANTIC_LABEL")
        else:
            kind = "EQUATION_CONTEXT_BUNDLE"
            speech_act = "UNRESOLVED"
            reasons = ("MULTI_SPAN_SYNTHESIS", "REVIEW_REQUIRED", "LOW_CONFIDENCE_SEMANTIC_LABEL")
        spans.append(Span(before.start if before else display.start, after.end if after else display.end, kind, speech_act, reasons))
    return sorted(set(spans), key=lambda span: (span.start, span.end, span.kind, span.speech_act))


def occurrence_record(paper_id: str, slug: str, artifact: str, artifact_hash: str, lines: list[str], paths: list[list[str]], span: Span) -> dict[str, Any]:
    if not (1 <= span.start <= span.end <= len(lines)):
        raise ValueError(f"invalid 1-based inclusive range {span.start}-{span.end} for {artifact} ({len(lines)} lines)")
    text = "\n".join(lines[span.start - 1:span.end])
    payload = {"paper_id": paper_id, "source_artifact": artifact, "source_artifact_hash": f"sha256:{artifact_hash}", "line_start": span.start, "line_end": span.end, "verbatim_source_text": text, "section_path": paths[span.start - 1], "span_kind": span.kind, "speech_act": span.speech_act}
    content_hash = digest(payload)
    return {"schema": "agtxiv.source-claim-occurrence/0.1.0", "id": f"source-claim-occurrence:{slug}:{content_hash[7:23]}", **payload, "candidate_status": "PROVISIONAL", "reason_codes": list(span.reasons), "content_hash": content_hash}


def typed_objects(text: str) -> list[dict[str, str]]:
    objects = []
    seen: set[str] = set()
    for match in re.finditer(r"\$([^$\n]{1,80})\$", text):
        symbol = normalize_text(match.group(1))
        if symbol and symbol not in seen:
            seen.add(symbol)
            objects.append({"symbol_latex": symbol, "semantic_type": "UNRESOLVED", "scope": "claim"})
        if len(objects) == 8:
            break
    return objects


def candidate_records(slug: str, occurrences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    for occurrence in occurrences:
        relation = "UNRESOLVED" if occurrence["speech_act"] == "UNRESOLVED" else ("MULTI_SPAN_DERIVED" if occurrence["span_kind"] == "EQUATION_DISCOURSE_BUNDLE" else "INTERPRETIVE")
        key = (normalize_text(occurrence["verbatim_source_text"]), occurrence["speech_act"], relation)
        by_key[key].append(occurrence)

    records = []
    for (text, speech_act, relation), grouped in sorted(by_key.items(), key=lambda item: min(row["line_start"] for row in item[1])):
        referenced = list(grouped)
        if any(bundle["span_kind"] in {"EQUATION_DISCOURSE_BUNDLE", "EQUATION_CONTEXT_BUNDLE"} for bundle in grouped):
            for bundle in grouped:
                if bundle["span_kind"] in {"EQUATION_DISCOURSE_BUNDLE", "EQUATION_CONTEXT_BUNDLE"}:
                    referenced.extend(row for row in occurrences if row["span_kind"] in {"PROSE_PARAGRAPH", "DISPLAY_EQUATION"} and bundle["line_start"] <= row["line_start"] and row["line_end"] <= bundle["line_end"])
        refs = sorted({row["id"] for row in referenced})
        statement: dict[str, Any] = {"typed_objects": typed_objects(text), "assumptions": [], "conclusion": None, "unresolved": None}
        if speech_act == "UNRESOLVED":
            statement["unresolved"] = {"source_text": text, "issues": ["EQUATION_SEMANTICS_NOT_PARSED"]}
        else:
            if speech_act == "ASSUMPTION":
                statement["assumptions"] = [{"source_text": text, "type": "UNRESOLVED"}]
            statement["conclusion"] = {"source_text": text, "predicate_latex": None, "parse_status": "PARTIAL"}
        semantic_payload = {"speech_act": speech_act, "source_relation": relation, "statement": statement}
        semantic_hash = digest(semantic_payload)
        reasons = ["AUTOMATIC_EXTRACTION", "REVIEW_REQUIRED"] + (["LOW_CONFIDENCE_SEMANTIC_LABEL"] if relation in {"INTERPRETIVE", "MULTI_SPAN_DERIVED", "UNRESOLVED"} else [])
        if any("EXPLICIT_DERIVATION_CUE" in row["reason_codes"] for row in grouped):
            reasons.append("EXPLICIT_DERIVATION_CUE")
        records.append({"schema": "agtxiv.provisional-canonical-semantic-candidate/0.1.0", "id": f"provisional-claim:{slug}:{semantic_hash[7:23]}", "candidate_status": "PROVISIONAL", "reason_codes": reasons, "speech_act": speech_act, "source_relation": relation, "occurrence_refs": refs, "statement": statement, "canonical_content_hash": semantic_hash})
    return records


def module_records(slug: str, candidates: list[dict[str, Any]], occurrences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    occurrence_by_id = {row["id"]: row for row in occurrences}
    grouped: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for candidate in candidates:
        first = occurrence_by_id[candidate["occurrence_refs"][0]]
        section = first["section_path"][0] if first["section_path"] else "Front matter"
        grouped[section].append(candidate)
    modules = []
    for index, (section, rows) in enumerate(grouped.items(), 1):
        ids = lambda acts: [row["id"] for row in rows if row["speech_act"] in acts]
        modules.append({"schema": "agtxiv.provisional-canonical-claim-module/0.1.0", "id": f"provisional-claim-module:{slug}:{index:03d}", "candidate_status": "PROVISIONAL", "section_scope": section, "imports": [], "assumption_contracts": ids({"ASSUMPTION"}), "definitions": ids({"DEFINITION", "NOTATION"}), "core_claims": ids({"MATHEMATICAL_ASSERTION", "CONJECTURE", "ATTRIBUTED_ASSERTION"}), "derived_exports": ids({"DERIVATION_CONCLUSION", "EXAMPLE_INSTANCE"}), "unresolved_review_queue": ids({"UNRESOLVED"}), "limitations": ["Automatic first-pass grouping; boundaries and semantic roles require review.", "Physlib and PhyslibAlpha are future oracle markers only; no library alignment is claimed."], "future_oracle_markers": [{"oracle": "Physlib", "status": "FUTURE_SEARCH_ONLY"}, {"oracle": "PhyslibAlpha", "status": "FUTURE_SEARCH_ONLY"}]})
    return modules


GRAPH_STOPWORDS = {"that", "this", "with", "from", "then", "where", "which", "every", "there", "their", "have", "using", "show", "prove", "state", "claim", "result", "equation", "lemma", "theorem", "definition", "mathrm", "mathcal", "mathbf", "mathbb", "mathsf", "mathbm", "text", "label", "eqref", "begin"}
GENERIC_LATEX_COMMANDS = {"begin", "end", "mathrm", "mathcal", "mathbf", "mathbb", "mathsf", "mathbm", "bm", "text", "textrm", "operatorname", "label", "ref", "eqref", "cite", "citep", "citet", "left", "right", "big", "Big", "bigl", "bigr", "top", "dagger"}


def candidate_text(candidate: dict[str, Any]) -> str:
    conclusion = candidate["statement"].get("conclusion") or {}
    unresolved = candidate["statement"].get("unresolved") or {}
    return str(conclusion.get("source_text") or unresolved.get("source_text") or "")


def semantic_terms(candidate: dict[str, Any]) -> set[str]:
    text = normalize_text(candidate_text(candidate)).lower()
    text_without_refs = re.sub(r"\\(?:label|ref|eqref|cite|citep|citet)\s*\{[^{}]*\}", " ", text)
    words = {word for word in re.findall(r"[a-z][a-z0-9_-]{3,}", readable_text(text_without_refs)) if word not in GRAPH_STOPWORDS}
    commands = {command for command in re.findall(r"\\([a-zA-Z]{2,})", text_without_refs) if command not in GENERIC_LATEX_COMMANDS}
    return words | commands


def typed_symbol_terms(candidate: dict[str, Any]) -> set[str]:
    symbols = {latex_signature(row["symbol_latex"]) for row in candidate["statement"].get("typed_objects", [])}
    return {symbol for symbol in symbols if len(symbol) >= 3 and not re.fullmatch(r"(?:[A-Za-z]|\\[A-Za-z]+)(?:_[A-Za-z])?", symbol)}


def graph_record(slug: str, candidates: list[dict[str, Any]], occurrences: list[dict[str, Any]]) -> dict[str, Any]:
    occurrence_by_id = {row["id"]: row for row in occurrences}
    ordered = sorted(candidates, key=lambda row: min(occurrence_by_id[ref]["line_start"] for ref in row["occurrence_refs"]))
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    previous: dict[str, dict[str, Any]] = {}

    def shared_evidence(source: dict[str, Any], target: dict[str, Any]) -> tuple[set[str], set[str]]:
        return semantic_terms(source) & semantic_terms(target), typed_symbol_terms(source) & typed_symbol_terms(target)

    def add_edge(source: dict[str, Any], target: dict[str, Any], edge_type: str, reason: str, shared_words: set[str], shared_symbols: set[str]) -> None:
        key = (source["id"], target["id"], edge_type)
        evidence_refs = sorted(set(source["occurrence_refs"] + target["occurrence_refs"]))
        shared_terms = sorted(shared_words | {f"symbol:{symbol}" for symbol in shared_symbols})
        edges[key] = {"source": source["id"], "target": target["id"], "edge_type": edge_type, "evidence_occurrence_refs": evidence_refs, "shared_terms": shared_terms, "reason_codes": [reason, "REVIEW_REQUIRED"]}

    for row in ordered:
        occurrence = occurrence_by_id[row["occurrence_refs"][0]]
        section = "/".join(occurrence["section_path"])
        for key, edge_type, reason in (("definition", "DEFINITION_PREREQUISITE", "DEFINITION_TERM_OVERLAP"), ("assumption", "SCOPE_ASSUMPTION", "ASSUMPTION_SCOPE_OVERLAP")):
            prior = previous.get(f"{section}:{key}")
            if prior and prior["id"] != row["id"]:
                shared_words, shared_symbols = shared_evidence(prior, row)
                if len(shared_words) >= 3 or (shared_symbols and len(shared_words) >= 1):
                    add_edge(prior, row, edge_type, reason, shared_words, shared_symbols)
        prior_claim = previous.get(f"{section}:claim")
        source_text = candidate_text(row).lower()
        if prior_claim and prior_claim["id"] != row["id"]:
            shared_words, shared_symbols = shared_evidence(prior_claim, row)
            overlap = bool(shared_words or shared_symbols)
            if overlap and row["speech_act"] == "DERIVATION_CONCLUSION" and DERIVATION_CUE_RE.search(source_text):
                add_edge(prior_claim, row, "DERIVATION", "EXPLICIT_DERIVATION_CUE", shared_words, shared_symbols)
            elif overlap and re.search(r"\b(using|by applying|from this|from the|together with|combined with|as established)\b", source_text):
                add_edge(prior_claim, row, "CLAIM_PREMISE", "EXPLICIT_PREMISE_CUE", shared_words, shared_symbols)
            relation_cue = re.search(r"\b(this|it|the preceding|the previous|the above)\s+(?:claim|result|statement|condition|bound|identity)?\s*(?:is|are)?\s*(equivalent|a special case|a generalization)\b", source_text)
            reverse_cue = re.search(r"\b(equivalent to|special case of|generalization of)\s+(this|the preceding|the previous|the above)\b", source_text)
            if overlap and (relation_cue or reverse_cue):
                phrase = (relation_cue or reverse_cue).group(0)
                if "special case" in phrase:
                    edge_type = "SPECIALIZATION_CANDIDATE"
                elif "generalization" in phrase:
                    edge_type = "GENERALIZATION_CANDIDATE"
                else:
                    edge_type = "EQUIVALENCE_CANDIDATE"
                add_edge(prior_claim, row, edge_type, "EXPLICIT_ANAPHORIC_RELATION_CUE", shared_words, shared_symbols)
        if row["speech_act"] in {"DEFINITION", "NOTATION"}:
            previous[f"{section}:definition"] = row
        if row["speech_act"] == "ASSUMPTION":
            previous[f"{section}:assumption"] = row
        if row["speech_act"] in {"MATHEMATICAL_ASSERTION", "DERIVATION_CONCLUSION"}:
            previous[f"{section}:claim"] = row

    edge_rows = []
    for key in sorted(edges):
        payload = edges[key]
        edge_rows.append({"id": f"provisional-edge:{slug}:{digest(payload)[7:23]}", **payload, "candidate_only": True, "status": "REVIEW_REQUIRED"})
    return {"schema": "agtxiv.provisional-candidate-graph/0.1.0", "paper_slug": slug, "nodes": [row["id"] for row in candidates], "edges": edge_rows, "graph_status": "PROVISIONAL_NOT_VERIFIED_DAG", "cycle_policy": "Every edge is directed from an earlier prerequisite or supporting candidate to the later dependent candidate. Cycles and equivalence candidates require human review and, where appropriate, quotienting; this artifact does not assert a DAG."}


def git_snapshot_file(path: str, required: bool = True) -> tuple[str, str] | None:
    result = subprocess.run(["git", "show", f"{BASELINE_COMMIT}:{path}"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        if required:
            raise RuntimeError(result.stderr.strip())
        return None
    blob = subprocess.run(["git", "rev-parse", f"{BASELINE_COMMIT}:{path}"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    return result.stdout, blob


def baseline_claims_and_anchors(slug: str) -> tuple[list[dict[str, Any]], str, dict[str, dict[str, Any]], dict[str, str], dict[str, str], str]:
    claim_path = f"Stabilizerness/MathClaimIRRegistry/claims/{slug}.jsonl"
    claim_snapshot = git_snapshot_file(claim_path)
    assert claim_snapshot is not None
    raw, claim_blob = claim_snapshot
    anchors: dict[str, dict[str, Any]] = {}
    anchor_blobs: dict[str, str] = {}
    for path in (f"agents/{slug}/source/anchors.jsonl", f"Stabilizerness/MathClaimIRRegistry/source-anchors/{slug}.jsonl"):
        snapshot = git_snapshot_file(path, required=False)
        if not snapshot:
            continue
        anchor_raw, blob = snapshot
        anchor_blobs[path] = blob
        for line in anchor_raw.splitlines():
            if line.strip():
                row = json.loads(line)
                anchors[row["id"]] = row
    preprocessing_path = f"Stabilizerness/MathClaimIRRegistry/preprocessing/{slug}.json"
    preprocessing_snapshot = git_snapshot_file(preprocessing_path)
    assert preprocessing_snapshot is not None
    preprocessing_raw, preprocessing_blob = preprocessing_snapshot
    macros = json.loads(preprocessing_raw).get("macro_definitions", {})
    return [json.loads(line) for line in raw.splitlines() if line.strip()], claim_blob, anchors, anchor_blobs, macros, preprocessing_blob


def expand_project_macros(text: str, macros: dict[str, str]) -> str:
    for macro, expansion in sorted(macros.items(), key=lambda item: len(item[0]), reverse=True):
        if "#" in macro or "#" in expansion:
            continue
        text = re.sub(re.escape(macro) + r"(?![A-Za-z@])", lambda _: expansion, text)
    return text


def latex_signature(text: str, macros: dict[str, str] | None = None) -> str:
    text = expand_project_macros(text, macros or {})
    text = normalize_text(text)
    text = re.sub(r"\\(?:begin|end|label)\{[^{}]*\}", "", text)
    text = text.replace("\\left", "").replace("\\right", "")
    return re.sub(r"\s+", "", text)


COMPARISON_STOPWORDS = GRAPH_STOPWORDS | {"some", "such", "into", "only", "also", "when", "whereas", "under", "over", "given", "defined", "satisfying", "following", "associated", "corresponding"}


def comparison_terms(text: str, macros: dict[str, str]) -> set[str]:
    text = expand_project_macros(normalize_text(text), macros).lower()
    text = re.sub(r"\\(?:label|ref|eqref|cite|citep|citet)\s*\{[^{}]*\}", " ", text)
    return {word for word in re.findall(r"[a-z][a-z0-9_-]{3,}", readable_text(text)) if word not in COMPARISON_STOPWORDS}


def accepted_representations(record: dict[str, Any]) -> list[tuple[str, str]]:
    structured = record.get("structured_statement", {})
    conclusion = structured.get("conclusion", {}) if isinstance(structured, dict) else {}
    return [
        ("source_statement_expanded_latex", record.get("source", {}).get("source_statement_expanded_latex", "")),
        ("normalized_statement_expanded_latex", record.get("normalized_statement_expanded_latex", "")),
        ("structured_conclusion", conclusion.get("expression_latex", "") if isinstance(conclusion, dict) else ""),
    ]


def paper_delta(slug: str, candidates: list[dict[str, Any]], occurrences: list[dict[str, Any]]) -> dict[str, Any]:
    accepted, blob, anchors, anchor_blobs, macros, preprocessing_blob = baseline_claims_and_anchors(slug)
    occurrence_by_id = {row["id"]: row for row in occurrences}
    dispositions = []
    for candidate in candidates:
        candidate_source = candidate_text(candidate)
        candidate_signature = latex_signature(candidate_source, macros)
        candidate_terms = comparison_terms(candidate_source, macros)
        exact_matches: list[tuple[str, str]] = []
        statement_matches: list[tuple[float, str, str, list[str]]] = []
        region_matches: dict[str, tuple[list[str], list[str]]] = {}
        for record in accepted:
            best_statement_match: tuple[float, str, list[str]] | None = None
            for representation, text in accepted_representations(record):
                signature = latex_signature(text, macros)
                if len(signature) >= 12 and signature == candidate_signature:
                    exact_matches.append((record["id"], representation))
                    break
                baseline_terms = comparison_terms(text, macros)
                shared = candidate_terms & baseline_terms
                if len(shared) < 3 or not baseline_terms or not candidate_terms:
                    continue
                baseline_coverage = len(shared) / len(baseline_terms)
                candidate_coverage = len(shared) / len(candidate_terms)
                jaccard = len(shared) / len(candidate_terms | baseline_terms)
                score = (baseline_coverage + candidate_coverage + jaccard) / 3
                if baseline_coverage >= 0.75 and candidate_coverage >= 0.45 and jaccard >= 0.45:
                    match = (score, representation, sorted(shared))
                    if best_statement_match is None or match > best_statement_match:
                        best_statement_match = match
            if best_statement_match:
                score, representation, shared = best_statement_match
                statement_matches.append((score, record["id"], representation, shared))

            matched_anchor_ids = []
            matched_occurrence_ids = []
            for anchor_id in record.get("source", {}).get("statement_anchors", []):
                anchor = anchors.get(anchor_id)
                location = anchor.get("location", {}) if anchor else {}
                start, end = location.get("line_start"), location.get("line_end")
                if not isinstance(start, int) or not isinstance(end, int):
                    continue
                for occurrence_ref in candidate["occurrence_refs"]:
                    occurrence = occurrence_by_id[occurrence_ref]
                    if occurrence["line_start"] <= end and start <= occurrence["line_end"]:
                        matched_anchor_ids.append(anchor_id)
                        matched_occurrence_ids.append(occurrence_ref)
            if matched_anchor_ids:
                region_matches[record["id"]] = (sorted(set(matched_anchor_ids)), sorted(set(matched_occurrence_ids)))

        possible_regions = [{"method": "LOCATION_ONLY_SOURCE_ANCHOR_OVERLAP", "possible_baseline_ref": record_id, "anchor_refs": anchor_refs, "occurrence_refs": occurrence_refs} for record_id, (anchor_refs, occurrence_refs) in sorted(region_matches.items())]
        if exact_matches:
            refs = sorted({record_id for record_id, _ in exact_matches})
            evidence = [{"method": "EXACT_NORMALIZED_REPRESENTATION", "baseline_ref": record_id, "representation": representation, "occurrence_refs": candidate["occurrence_refs"]} for record_id, representation in sorted(set(exact_matches))]
            disposition = "reused"
            reasons = ["EXACT_BASELINE_REPRESENTATION_MATCH", "REVIEW_REQUIRED"]
        else:
            statement_matches.sort(reverse=True)
            unique_match = statement_matches and (len(statement_matches) == 1 or statement_matches[0][0] - statement_matches[1][0] >= 0.15)
            if unique_match:
                score, record_id, representation, shared = statement_matches[0]
                refs = [record_id]
                evidence = [{"method": "CONSERVATIVE_STATEMENT_MATCH", "baseline_ref": record_id, "representation": representation, "occurrence_refs": candidate["occurrence_refs"], "shared_terms": shared, "score": round(score, 6)}]
                disposition = "unresolved"
                reasons = ["PARTIAL_STATEMENT_MATCH_RELATION_UNRESOLVED", "REVIEW_REQUIRED"]
            else:
                refs = []
                evidence = [{"method": "NO_CONSERVATIVE_MATCH", "detail": "No exact or unique discriminative statement-level match was established; source-anchor overlap, if present, is retained only as a possible region hint."}]
                disposition = "unresolved"
                reasons = ["BASELINE_ABSENCE_NOT_ESTABLISHED", "REVIEW_REQUIRED"]
        dispositions.append({"candidate_ref": candidate["id"], "disposition": disposition, "baseline_record_refs": refs, "possible_baseline_region_refs": possible_regions, "comparison_evidence": evidence, "reason_codes": reasons, "status": "REVIEW_REQUIRED"})
    return {"schema": "agtxiv.provisional-paper-delta/0.1.0", "paper_slug": slug, "baseline": {"registry": "MathClaimIRRegistry", "git_commit": BASELINE_COMMIT, "claim_file_blob": blob, "source_anchor_blobs": anchor_blobs, "preprocessing_blob": preprocessing_blob}, "dispositions": dispositions, "originality_notice": "NEW_TO_REGISTRY means absent from this fixed registry snapshot; it does not assert academic originality.", "review_notice": "Source-anchor overlap is location evidence only and never populates baseline_record_refs. Equivalent, specialization, generalization, new-proof, and new-relation dispositions require explicit semantic review evidence; weak lexical similarity is never used to infer them."}


def static_registry_hashes(registry: Path = OUTPUT) -> dict[str, str]:
    hashes = {}
    for relative in STATIC_REGISTRY_FILES:
        path = registry / relative
        if not path.is_file():
            raise RuntimeError(f"missing static registry file: {relative}")
        hashes[relative] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def validate_static_registry_integrity(registry: Path = OUTPUT) -> None:
    manifest_path = registry / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("missing provisional registry manifest.json")
    recorded = json.loads(manifest_path.read_text()).get("static_file_hashes")
    actual = static_registry_hashes(registry)
    if recorded != actual:
        raise RuntimeError(f"static registry integrity mismatch: recorded={recorded} actual={actual}")


def validate_paper_artifacts(
    slug: str,
    occurrences: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    modules: list[dict[str, Any]],
    graph: dict[str, Any],
    delta: dict[str, Any],
) -> None:
    """Validate cross-artifact constraints that JSON Schema cannot express."""
    occurrence_ids = {row["id"] for row in occurrences}
    candidate_ids = {row["id"] for row in candidates}
    if len(occurrence_ids) != len(occurrences) or len(candidate_ids) != len(candidates):
        raise RuntimeError(f"duplicate occurrence or candidate ID for {slug}")
    for candidate in candidates:
        unknown = set(candidate["occurrence_refs"]) - occurrence_ids
        if unknown:
            raise RuntimeError(f"candidate occurrence refs do not exist for {slug}: {sorted(unknown)}")

    module_refs = [
        ref
        for module in modules
        for field in ("assumption_contracts", "definitions", "core_claims", "derived_exports", "unresolved_review_queue")
        for ref in module[field]
    ]
    if collections.Counter(module_refs) != collections.Counter({candidate_id: 1 for candidate_id in candidate_ids}):
        raise RuntimeError(f"module candidates are not covered exactly once for {slug}")

    if set(graph["nodes"]) != candidate_ids:
        raise RuntimeError(f"graph nodes do not match candidates for {slug}")
    for edge in graph["edges"]:
        if edge["source"] not in candidate_ids or edge["target"] not in candidate_ids:
            raise RuntimeError(f"graph edge candidate ref does not exist for {slug}")
        unknown = set(edge["evidence_occurrence_refs"]) - occurrence_ids
        if unknown:
            raise RuntimeError(f"graph edge occurrence refs do not exist for {slug}: {sorted(unknown)}")

    accepted, _, pinned_anchors, _, _, _ = baseline_claims_and_anchors(slug)
    baseline_ids = {row["id"] for row in accepted}
    anchor_ids = set(pinned_anchors)
    disposition_refs = [row["candidate_ref"] for row in delta["dispositions"]]
    if collections.Counter(disposition_refs) != collections.Counter({candidate_id: 1 for candidate_id in candidate_ids}):
        raise RuntimeError(f"delta dispositions do not cover candidates exactly once for {slug}")
    for disposition in delta["dispositions"]:
        refs = set(disposition["baseline_record_refs"])
        unknown_baselines = refs - baseline_ids
        if unknown_baselines:
            raise RuntimeError(f"baseline refs do not exist in pinned snapshot for {slug}: {sorted(unknown_baselines)}")
        if disposition["disposition"] == "new-to-registry" and refs:
            raise RuntimeError(f"new-to-registry disposition has baseline refs for {slug}")
        evidence_refs = {evidence["baseline_ref"] for evidence in disposition["comparison_evidence"] if "baseline_ref" in evidence}
        if evidence_refs != refs:
            raise RuntimeError(f"comparison evidence baseline refs disagree with baseline_record_refs for {slug}")
        for evidence in disposition["comparison_evidence"]:
            unknown = set(evidence.get("occurrence_refs", [])) - occurrence_ids
            if unknown:
                raise RuntimeError(f"comparison evidence occurrence refs do not exist for {slug}: {sorted(unknown)}")
        for region in disposition["possible_baseline_region_refs"]:
            if region["possible_baseline_ref"] not in baseline_ids:
                raise RuntimeError(f"possible-region baseline ref does not exist for {slug}")
            unknown_anchors = set(region["anchor_refs"]) - anchor_ids
            if unknown_anchors:
                raise RuntimeError(f"possible-region anchor refs do not exist for {slug}: {sorted(unknown_anchors)}")
            unknown = set(region["occurrence_refs"]) - occurrence_ids
            if unknown:
                raise RuntimeError(f"possible-region occurrence refs do not exist for {slug}: {sorted(unknown)}")


def distribution(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(collections.Counter(row[key] for row in rows).items()))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def generate(output: Path = OUTPUT) -> dict[str, Any]:
    # Verify all configured sources against PaperAgent records and bytes before writes.
    verified = verify_sources(PAPERS, ROOT)
    papers_summary = []
    for paper_id, slug, artifact, artifact_hash, path in verified:
        lines = path.read_text().splitlines()
        clean = [strip_comment(line) for line in lines]
        paths = section_paths(clean)
        occurrences = [occurrence_record(paper_id, slug, artifact, artifact_hash, lines, paths, span) for span in extract_spans(lines)]
        candidates = candidate_records(slug, occurrences)
        modules = module_records(slug, candidates, occurrences)
        graph = graph_record(slug, candidates, occurrences)
        delta = paper_delta(slug, candidates, occurrences)
        validate_paper_artifacts(slug, occurrences, candidates, modules, graph, delta)
        paper_dir = output / "papers" / slug
        paper_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(paper_dir / "occurrences.jsonl", occurrences)
        write_jsonl(paper_dir / "canonical-candidates.jsonl", candidates)
        write_json(paper_dir / "modules.json", modules)
        write_json(paper_dir / "graph.json", graph)
        write_json(paper_dir / "paper-delta.json", delta)
        review_count = sum("REVIEW_REQUIRED" in row["reason_codes"] for row in occurrences)
        unresolved_count = sum(row["speech_act"] == "UNRESOLVED" for row in occurrences)
        delta_rows = delta["dispositions"]
        baseline_refs = [ref for row in delta_rows for ref in row["baseline_record_refs"]]
        evidence_methods = collections.Counter(evidence["method"] for row in delta_rows for evidence in row["comparison_evidence"])
        papers_summary.append({"paper_id": paper_id, "slug": slug, "source_artifact": artifact, "source_artifact_hash": f"sha256:{artifact_hash}", "source_line_count": len(lines), "occurrence_count": len(occurrences), "candidate_count": len(candidates), "candidate_to_occurrence_ratio": round(len(candidates) / len(occurrences), 6) if occurrences else 1.0, "exact_repeat_merge_count": len(occurrences) - len(candidates), "module_count": len(modules), "graph_edge_count": len(graph["edges"]), "speech_act_distribution": distribution(occurrences, "speech_act"), "span_kind_distribution": distribution(occurrences, "span_kind"), "occurrence_status_distribution": distribution(occurrences, "candidate_status"), "candidate_status_distribution": distribution(candidates, "candidate_status"), "source_relation_distribution": distribution(candidates, "source_relation"), "graph_edge_type_distribution": distribution(graph["edges"], "edge_type"), "paper_delta_disposition_distribution": distribution(delta_rows, "disposition"), "paper_delta_baseline_reference_count": len(baseline_refs), "paper_delta_linked_candidate_count": sum(bool(row["baseline_record_refs"]) for row in delta_rows), "paper_delta_unique_baseline_count": len(set(baseline_refs)), "paper_delta_evidence_method_distribution": dict(sorted(evidence_methods.items())), "paper_delta_possible_region_count": sum(len(row["possible_baseline_region_refs"]) for row in delta_rows), "paper_delta_max_refs_per_candidate": max((len(row["baseline_record_refs"]) for row in delta_rows), default=0), "review_required_occurrence_count": review_count, "unresolved_occurrence_count": unresolved_count, "schema_version": SCHEMA_VERSION})
    occurrence_total = sum(paper["occurrence_count"] for paper in papers_summary)
    candidate_total = sum(paper["candidate_count"] for paper in papers_summary)
    manifest = {"schema": "agtxiv.provisional-claim-registry-manifest/0.1.0", "authority": "NON_AUTHORITATIVE_PROVISIONAL_ONLY", "generator": "tools/extract_provisional_claims.py", "baseline_commit": BASELINE_COMMIT, "static_file_hashes": static_registry_hashes(), "compression_statistics": {"occurrence_count": occurrence_total, "canonical_candidate_count": candidate_total, "exact_repeat_merge_count": occurrence_total - candidate_total, "candidate_to_occurrence_ratio": round(candidate_total / occurrence_total, 6) if occurrence_total else 1.0, "semantic_compression_performed": False}, "papers": papers_summary, "notices": ["Occurrences are never deduplicated; preliminary canonical candidates may merge exact normalized repeats while retaining every occurrence reference.", "The canonical-candidates filename denotes only the candidate layer; semantic quotienting, deduplication, and module compression have not occurred.", "All automatic semantic labels and graph edges are provisional and require review.", "Graph cycles and equivalence candidates require review or quotienting; no verified DAG is claimed.", "Physlib and PhyslibAlpha are future oracle markers only; no alignment is claimed.", "NEW_TO_REGISTRY is not a claim of academic originality."]}
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="regenerate in memory and fail if checked-in output differs")
    args = parser.parse_args()
    if args.check:
        import tempfile
        try:
            validate_static_registry_integrity()
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory) / "registry"
            generate(temporary)
            expected = {p.relative_to(OUTPUT): p.read_bytes() for p in OUTPUT.rglob("*") if p.is_file() and (p.name == "manifest.json" or "papers" in p.relative_to(OUTPUT).parts)}
            actual = {p.relative_to(temporary): p.read_bytes() for p in temporary.rglob("*") if p.is_file()}
            if expected != actual:
                missing = sorted(str(path) for path in actual.keys() - expected.keys())
                extra = sorted(str(path) for path in expected.keys() - actual.keys())
                changed = sorted(str(path) for path in actual.keys() & expected.keys() if actual[path] != expected[path])
                print(f"provisional registry differs: missing={missing} extra={extra} changed={changed}", file=sys.stderr)
                return 1
        print("provisional registry is deterministic and current")
        return 0
    manifest = generate()
    print(f"papers={len(manifest['papers'])} occurrences={sum(p['occurrence_count'] for p in manifest['papers'])} candidates={sum(p['candidate_count'] for p in manifest['papers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
