"""GraphDelta storage, delta-set manifests and the merged view (spec §5.3, §9.1).

A delta (ids.make_delta, re-exported here) is immutable and named by the digest of its body. A manifest
names a parent-closed set of deltas; merging it gives the view the invariants, reviews and loader read.
The view adds only asserted_by (delta ids) and methods to every asserted row; never a state or disposition.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import contracts
from core import canonical, utcnow
from ids import make_delta, make_id as address  # make_delta is re-exported: one builder, one id helper

LABELS = tuple(contracts.SCHEMAS[contracts.CORPUS_ID]["$defs"]["GraphDelta"]["properties"]["nodes"]["properties"])
PROJECTION_KEYS = ("asserted_by", "methods")


def asserted(row):
    """A view row without the projection keys: exactly what a delta asserted."""
    return {k: v for k, v in row.items() if k not in PROJECTION_KEYS}


def _body(record, id_key, *unhashed):
    return {k: v for k, v in record.items() if k not in (id_key, *unhashed)}


def _checked_delta(delta):
    contracts.validate("GraphDelta", delta)
    if delta["delta_id"] != address("delta", _body(delta, "delta_id")):
        raise ValueError(f"{delta['delta_id']}: delta_id is not the digest of its body")
    return delta


class DeltaStore:
    """<root>/<hex[:2]>/<hex>.json, canonical bytes, written once; different bytes under one id are refused."""

    def __init__(self, root):
        self.root = Path(root)

    def path(self, delta_id):
        hexpart = delta_id.removeprefix("delta:")
        return self.root / hexpart[:2] / (hexpart + ".json")

    def put(self, delta):
        raw, path = canonical(_checked_delta(delta)), self.path(delta["delta_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        tmp.write_bytes(raw)
        try:
            os.link(tmp, path)  # Atomic and never replaces an existing file.
        except FileExistsError:
            if path.read_bytes() != raw:
                raise ValueError(f"{delta['delta_id']}: different bytes already stored under this id") from None
        finally:
            tmp.unlink()
        return path

    def get(self, delta_id):
        raw = self.path(delta_id).read_bytes()
        delta = json.loads(raw)
        if canonical(delta) != raw or delta.get("delta_id") != delta_id:
            raise ValueError(f"{delta_id}: stored file is not the canonical delta of this id")
        return _checked_delta(delta)


def make_manifest(corpus_id, deltas, excluded=(), parent_manifest_id=None, created_at=None):
    """manifest_id = digest of the manifest body without manifest_id and created_at, so one delta set has one id."""
    body = {"kind": "DeltaSetManifest", "corpus_id": corpus_id, "deltas": sorted(set(deltas)),
            "excluded": sorted(excluded, key=lambda row: row["delta_id"])}
    if parent_manifest_id is not None:
        body["parent_manifest_id"] = parent_manifest_id
    manifest = {**body, "manifest_id": address("manifest", body), "created_at": created_at or utcnow()}
    contracts.validate("DeltaSetManifest", manifest)
    return manifest


def merge(deltas):
    """DeltaSetView {deltas, nodes{Label: {id: row}}, edges{id: row}}. An id asserted by several deltas must carry
    identical rows (one id with two different rows raises): method-dependent data lives only in method-scoped rows
    (readings, junctions) or in delta measurements, which the view does not merge."""
    view = {"deltas": sorted({d["delta_id"] for d in deltas}), "nodes": {label: {} for label in LABELS}, "edges": {}}
    for delta in sorted(deltas, key=lambda d: d["delta_id"]):
        tagged = [(view["nodes"][label], row) for label, rows in delta["nodes"].items() for row in rows]
        for table, row in tagged + [(view["edges"], row) for row in delta["edges"]]:
            seen = table.setdefault(row["id"], {**row, "asserted_by": [], "methods": []})
            if asserted(seen) != row:
                field = "content_sha256" if seen["content_sha256"] != row["content_sha256"] else "row"
                raise ValueError(f"{row['id']}: {field} differs between {seen['asserted_by'][0]} and {delta['delta_id']}")
            if delta["delta_id"] not in seen["asserted_by"]:
                seen["asserted_by"].append(delta["delta_id"])
            if delta["method"] not in seen["methods"]:
                seen["methods"] = sorted([*seen["methods"], delta["method"]])
    return view


def check_manifest(manifest, store):
    """The merged view of a valid manifest; otherwise ValueError listing every problem found."""
    contracts.validate("DeltaSetManifest", manifest)
    problems, included = [], set(manifest["deltas"])
    if manifest["manifest_id"] != address("manifest", _body(manifest, "manifest_id", "created_at")):
        problems.append("manifest_id is not the digest of the manifest")
    excluded = [row["delta_id"] for row in manifest["excluded"]]
    problems += [f"{i}: excluded twice" for i in sorted({i for i in excluded if excluded.count(i) > 1})]
    problems += [f"{i}: both included and excluded" for i in sorted(included & set(excluded))]
    deltas = []
    for delta_id in manifest["deltas"]:
        try:
            deltas.append(store.get(delta_id))
        except (OSError, ValueError) as error:
            problems.append(f"{delta_id}: not readable from the store ({error})")
    problems += [f"{d['delta_id']}: parent {p} not included" for d in deltas for p in d["parents"] if p not in included]
    try:
        view = merge(deltas)
    except ValueError as error:
        raise ValueError("\n".join([*problems, str(error)])) from None
    known = {i for table in view["nodes"].values() for i in table}
    refs = [(e["id"], e[end]) for e in view["edges"].values() for end in ("start_id", "end_id")
            if not (e["type"] == "INCLUDES" and end == "start_id" and e[end] == manifest["corpus_id"])]
    refs += [(j["id"], x) for j in view["nodes"]["Junction"].values()
             for x in (j["conclusion_id"], *(leg["premise_id"] for leg in j["legs"]))]
    problems += [f"{owner}: {ref} is not asserted by an included delta" for owner, ref in refs if ref not in known]
    if problems:
        raise ValueError("\n".join(problems))
    return view
