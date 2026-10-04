"""Deterministic library index, lexical retrieval and root-search audits.

The index is Lean's own listing of the frozen proof environment's constants
under configured prefixes. Retrieval ranks them by IDF-weighted token overlap.
A ranked candidate is never a library binding, an accepted alignment or
evidence of library absence; a proof attempt still has to use it.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re

from chunks import reference
from core import digest, write_json
from recursive_graph import _verified_graph_json, _verified_json

PREFIXES = ("Mathlib.Combinatorics.SimpleGraph", "Mathlib.LinearAlgebra", "Mathlib.Analysis.Convex",
            "AgtXIv", "Physlib", "QuantumInfo", "Quantumlib")
METHOD = "LEXICAL_IDF_TOKEN_OVERLAP_V1"
PLACEHOLDER_KINDS = frozenset({"external_claim_request", "unresolved_claim_occurrence"})
WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|[0-9]+")
SYMBOLS = str.maketrans({"ℝ": " Real ", "ℂ": " Complex ", "ℕ": " Nat ", "ℤ": " Int ", "∑": " sum ", "∏": " prod "})
NOISE = frozenset("mathrm mathbb mathcal mathbf mathsf operatorname text textrm emph frac left right begin end "
                  "label ref cite eqref cdot ldots dots quad qquad the and for with that when then let all any "
                  "are its this otherwise".split())
UNKNOWN = re.compile(r"[Uu]nknown (?:identifier|constant) [`'‘]([^`'’\s]+)[`'’]")
_PREPARED = [None, None]


def _tokens(text):
    words = (word.lower() for word in WORD.findall(text.translate(SYMBOLS)))
    return {word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word
            for word in words if len(word) > 2 and word not in NOISE}


def _postings(rows):
    """token -> {row index: 2 for a declaration-name token, 1 for a type-only token}."""
    if _PREPARED[0] is not rows:
        postings = defaultdict(dict)
        for index, row in enumerate(rows):
            for token in _tokens(row["type"]):
                postings[token][index] = 1
            for token in _tokens(row["name"]):
                postings[token][index] = 2
        _PREPARED[:] = [rows, postings]
    return _PREPARED[1]


def _rank(query, rows, k, *, names_only=False):
    postings, scores = _postings(rows), Counter()
    for token in sorted(query & postings.keys()):
        idf = math.log((len(rows) + 1) / len(postings[token]))
        for index, weight in postings[token].items():
            if weight == 2 or not names_only:
                scores[index] += weight * idf
    order = sorted(scores, key=lambda index: (-round(scores[index], 9), rows[index]["name"]))
    return [rows[index] for index in order[:k]]


def retrieve(node, rows, k):
    """Rank index rows for a node's TeX text and conditions; ties break by declaration name."""
    return _rank(_tokens(" ".join([node.get("text") or "", *node.get("conditions", [])])), rows, k)


def retrieve_by_names(names, rows, k):
    """Per unresolved identifier: exact or dotted-suffix name matches first, then name-token overlap."""
    result = {}
    for name in dict.fromkeys(names):
        exact = [row for row in rows if row["name"] == name or row["name"].endswith("." + name)]
        seen = {row["name"] for row in exact}
        result[name] = (exact + [row for row in _rank(_tokens(name), rows, k, names_only=True)
                                 if row["name"] not in seen])[:k]
    return result


def unknown_identifiers(log):
    return sorted(set(UNKNOWN.findall(log)))[:10]


def _pinned(ref):
    raw = Path(ref["path"]).read_bytes()
    if digest(raw) != ref.get("sha256") or len(raw) != ref.get("byte_size"):
        raise ValueError("Library index bytes differ from the host reference")
    return raw


def load_index(ref):
    """The index manifest with its Lean-written rows, sorted by declaration name."""
    index = json.loads(_pinned(ref))
    if index.get("kind") != "LibraryIndex" or not isinstance(index.get("lean_rows"), dict):
        raise ValueError("Malformed library index")
    return {**index, "rows": sorted(map(json.loads, _pinned(index["lean_rows"]).splitlines()), key=lambda row: row["name"])}


def build_index(environment_ref, output, *, prefixes=PREFIXES, timeout=3600):
    """Run LibraryIndex.lean inside the frozen proof environment's imports and pin its rows."""
    from proof_backend import _binary_reference, _run_lean
    output = Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Keep library indexes immutable; choose a fresh output directory")
    if not prefixes or any(not isinstance(item, str) or not re.fullmatch(r"[A-Za-z0-9_.]+", item) for item in prefixes):
        raise ValueError("Index prefixes must be nonempty dotted Lean name prefixes")
    environment = _verified_json(environment_ref)
    if _binary_reference(environment["executable"]) != environment["executable_artifact"]:
        raise ValueError("Pinned Lean executable changed")
    output.mkdir(parents=True, exist_ok=True)
    body = (Path(__file__).resolve().parents[1] / "lean/LibraryIndex.lean").read_text().removeprefix("import Lean\n")
    rows_path, source = output / "compiled/library-index.jsonl", output / "LibraryIndexRun.lean"
    source.write_text("import Lean\n" + "".join("import " + name + "\n" for name in environment["imports"]) + body +
                      "\n#agtxiv_library_index " + json.dumps(str(rows_path)) + " [" +
                      ", ".join(map(json.dumps, prefixes)) + "]\n")
    receipt, log = _run_lean(environment, source, output, "lean.library_index", timeout=timeout)
    count = len(rows_path.read_bytes().splitlines()) if rows_path.is_file() else -1
    if receipt["status"] != "SUCCEEDED" or "AGTXIV_LIBRARY_INDEX_ROWS %d" % count not in log.splitlines():
        raise RuntimeError("LIBRARY_INDEX_BUILD_FAILED")
    return write_json(output / "library-index.json", {"kind": "LibraryIndex", "environment": environment_ref,
        "environment_sha256": environment["environment_sha256"], "prefixes": list(prefixes),
        "selection": "MODULE_OR_DECLARATION_NAME_PREFIX_EXCLUDING_INTERNAL_AND_GENERATED",
        "lean_source": reference(source), "lean_rows": reference(rows_path),
        "program_receipt": receipt, "row_count": count, "binding_accepted": False})


def root_audits(graph, index_ref, index, environment_sha256, *, k=8):
    """LIBRARY_SEARCHED audits for statement roots; placeholder roots keep their hard blockers."""
    if index["environment_sha256"] != environment_sha256:
        raise ValueError("Library index belongs to another proof environment")
    nodes = {node["id"]: node for node in graph["nodes"]}
    return {root["id"]: {"status": "LIBRARY_SEARCHED", "searched_revisions": [environment_sha256],
                         "candidates": [row["name"] for row in retrieve(nodes[root["id"]], index["rows"], k)],
                         "method": METHOD, "index": index_ref, "program_receipt": index["program_receipt"],
                         "binding_accepted": False}
            for root in graph["roots"] if nodes[root["id"]]["kind"] not in PLACEHOLDER_KINDS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("index", help="build the index of a frozen proof environment")
    build.add_argument("--environment", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--prefix", action="append")
    roots = commands.add_parser("roots", help="write root-audits.json for a pruned graph")
    roots.add_argument("--graph", type=Path, required=True)
    roots.add_argument("--index", type=Path, required=True)
    roots.add_argument("--environment", type=Path, required=True)
    roots.add_argument("--output", type=Path, required=True)
    roots.add_argument("--k", type=int, default=8)
    args = parser.parse_args()
    if args.command == "index":
        print(json.dumps(build_index(reference(args.environment), args.output, prefixes=tuple(args.prefix or PREFIXES))))
        return
    if args.output.exists():
        parser.error("Keep prior root audits; choose a fresh output")
    graph_ref, index_ref, environment_ref = map(reference, (args.graph, args.index, args.environment))
    graph, index = _verified_graph_json(graph_ref), load_index(index_ref)
    environment_sha256 = _verified_json(environment_ref)["environment_sha256"]
    audits = root_audits(graph, index_ref, index, environment_sha256, k=args.k)
    print(json.dumps(write_json(args.output.resolve(), {"kind": "RootLibraryAudits", "graph": graph_ref, "index": index_ref,
        "environment": environment_ref, "environment_sha256": environment_sha256, "method": METHOD, "k": args.k,
        "root_audits": audits, "skipped_placeholder_root_ids": sorted(
            {row["id"] for row in graph["roots"]} - set(audits)), "binding_accepted": False})))


if __name__ == "__main__":
    main()
