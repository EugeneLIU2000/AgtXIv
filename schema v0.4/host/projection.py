"""Neo4j projection of one delta-set view plus one review set (spec §9, §3.7, I-12).

Neo4j is a rebuildable projection, never the authority: nothing is read back into the store and no
state here says VERIFIED. Labels and relationship types live only in the fixed templates below,
built from constants; data selects a template by key and never reaches Cypher text. Review, AnalysisRun and
Nomination are not projected in v0.4: reviews act through derived dispositions and nominations stay immutable
artifacts. Loading always rebuilds from empty; incremental loading is deferred (§9.4).
"""
from __future__ import annotations

import base64
import contextlib
import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import contracts
from core import canonical, digest
from ids import logical_edges, make_id

NEO4J = Path(__file__).resolve().parents[1] / "neo4j"
LOADER_VERSION = "projection-0.4.0"
BATCH = 5000
_DEFS = contracts.SCHEMAS[contracts.CORPUS_ID]["$defs"]
REL_TYPES = tuple(_DEFS["EdgeType"]["enum"])
DERIVED = ("PREMISE_OF", "CONCLUDES")
HOST_FIELDS = ("id", "content_sha256", "asserted_by", "methods", "disposition")


def _fields(schema, key="", required=True, resolver=contracts.REGISTRY.resolver(contracts.CORPUS_ID)):
    """[{key, values, list, required}] for the enumerated values under a contract schema, keyed as _flat
    keys them; a nullable union or a list is never required (_flat drops None and empty lists)."""
    while "$ref" in schema:
        found = resolver.lookup(schema["$ref"])
        schema, resolver = found.contents, found.resolver
    if "enum" in schema:
        return [{"key": key, "values": schema["enum"], "list": False, "required": required}]
    if "anyOf" in schema:
        branches = [b for b in schema["anyOf"] if b.get("type") != "null"]
        parts = [_fields(b, key, required, resolver) for b in branches]
        if not parts or not all(len(p) == 1 and not p[0]["list"] for p in parts):
            return []
        return [{"key": key, "values": [v for p in parts for v in p[0]["values"]], "list": False,
                 "required": required and len(branches) == len(schema["anyOf"])}]
    if schema.get("type") == "array":  # a list of maps is JSON-encoded, so only scalar items are checked
        return [dict(f, list=True, required=False) for f in _fields(schema.get("items", {}), key, False, resolver)
                if f["key"] == key and not f["list"]]
    need = set(schema.get("required", ()))
    return [f for k, s in schema.get("properties", {}).items()
            for f in _fields(s, f"{key}_{k}" if key else k, required and k in need, resolver)]


_METHODS = {"key": "methods", "values": _DEFS["Method"]["enum"], "list": True, "required": False}
_REL_PROPS = {**{b["if"]["properties"]["type"]["const"]: b["then"]["properties"].get("props", {})
                 for b in _DEFS["Edge"]["allOf"]},
              "PREMISE_OF": _DEFS["JunctionNode"]["properties"]["legs"]["items"]}  # its props are the leg's
# The G5 audit's $enums: every enumerated contract field of each label and type, plus the view's methods.
ENUMS = {"nodes": [{"label": "Entity", **_METHODS}] + [
             {"label": label, **f} for label, s in _DEFS["GraphDelta"]["properties"]["nodes"]["properties"].items()
             for f in _fields(s["items"])],
         "rels": [{"type": t, **f} for t in REL_TYPES for f in [_METHODS, *_fields(_REL_PROPS.get(t, {}))]]}
GROUPS = {"Corpus": "Corpus", "PaperVersion": "PaperVersion", "Work": "Work", "BibEntry": "BibEntry",
          "Claim": "Claim:Logical", "ClaimReading": "ClaimReading", "Junction": "Junction",
          "ExternalRequest": "Placeholder:ExternalRequest:Logical",
          "UnresolvedOccurrence": "Placeholder:UnresolvedOccurrence:Logical",
          "PrimitiveAssertion": "PrimitiveAssertion"}
_PLACEHOLDER = {"EXTERNAL_REQUEST": "ExternalRequest", "UNRESOLVED_OCCURRENCE": "UnresolvedOccurrence"}

NODE_MERGE = {g: f"UNWIND $rows AS row MERGE (n:{labels}:Entity {{id: row.id}}) "
                 "ON CREATE SET n += row.props RETURN count(n) AS n" for g, labels in GROUPS.items()}
REL_MERGE = {t: "UNWIND $rows AS row MATCH (a:Entity {id: row.start}) MATCH (b:Entity {id: row.end}) "
                f"MERGE (a)-[r:{t} {{id: row.id}}]->(b) ON CREATE SET r += row.props RETURN count(r) AS n"
             for t in REL_TYPES}
NODE_PREFLIGHT = ("UNWIND $rows AS row MATCH (n:Entity {id: row.id}) "
                  "WHERE coalesce(n.content_sha256, '') <> row.content_sha256 RETURN row.id AS id")
REL_PREFLIGHT = {t: f"UNWIND $rows AS row MATCH ()-[r:{t} {{id: row.id}}]->() "
                    "WHERE coalesce(r.content_sha256, '') <> row.content_sha256 RETURN row.id AS id"
                 for t in REL_TYPES}
EXISTING = "MATCH (m:ProjectionManifest) RETURN m.id AS id, m.state AS state"
SET_MANIFEST = "MERGE (m:ProjectionManifest:Entity {id: $id}) SET m = $props RETURN m.state AS state"


def _code(text):
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//")).strip()


def _blocks(name, tag):
    """Statements of a .cypher file headed by "// @<tag> <name>" lines, with comment lines removed."""
    parts = re.split(rf"^// @{tag} (\S+)[ \t]*$", (NEO4J / name).read_text(encoding="utf-8"), flags=re.M)
    return tuple((key, _code(body)) for key, body in zip(parts[1::2], parts[2::2]))


SCHEMA = tuple(s.strip() for s in _code((NEO4J / "schema.cypher").read_text(encoding="utf-8")).split(";")
               if s.strip())
AUDITS = _blocks("audits.cypher", "audit")
BROWSE = dict(_blocks("browse.cypher", "browse"))


class LoadError(RuntimeError):
    """The §9.4 protocol stopped; the ProjectionManifest is left FAILED (or untouched before step 3, BUILDING)."""


def _flat(entry):
    """Neo4j properties: nested maps flatten to a_b keys, lists of maps or mixed lists become a_json;
    None and empty lists are dropped (neither Neo4j nor the CSV import stores them)."""
    out = {}

    def put(key, value):
        if isinstance(value, dict):
            for k, v in value.items():
                put(f"{key}_{k}", v)
            return
        if isinstance(value, list) and (len({type(v) for v in value}) > 1 or any(
                isinstance(v, (dict, list)) or v is None for v in value)):
            key, value = key + "_json", canonical(value).decode()[:-1]
        if value is None or value == []:
            return
        if key in out:
            raise ValueError("property collision: " + key)
        out[key] = value

    for k, v in entry.items():
        put(k, v)
    return out


def junction_edges(junction):
    """ids.logical_edges (PREMISE_OF per leg, then CONCLUDES; ids per §5.2 and G15) plus each leg's flags."""
    edges = logical_edges(junction)
    for edge, leg in zip(edges, junction["legs"]):
        edge["props"]["flags"] = leg["flags"]
    return edges


def delta_set_digest(manifest):
    """manifest_id as a sha256: delta.make_manifest digests everything but created_at (one set, one id)."""
    return "sha256:" + manifest["manifest_id"].removeprefix("manifest:")


def project(view, manifest, dispositions):
    """Projection rows for one delta.merge view under its DeltaSetManifest and the
    reviews.derive_dispositions output {subject_kind: {subject_id: disposition}} of one review set."""
    if sorted(view["deltas"]) != sorted(manifest["deltas"]):
        raise ValueError("the view was not merged from exactly the manifest's deltas (I-12)")
    nodes, edges = view["nodes"], view["edges"]
    derived = [dict(e, asserted_by=j["asserted_by"], methods=j["methods"])
               for j in nodes.get("Junction", {}).values() for e in junction_edges(j)]
    # A LEG subject id is its PREMISE_OF relationship id (reviews.leg_id); nominations are not projected (I-10).
    dispositions = {i: value for kind, table in dispositions.items() if kind != "FOUNDATION_NOMINATION"
                    for i, value in table.items()}
    out_nodes, out_rels = {}, {}

    def element(entry, drop=(), **extra):
        clash = sorted({*extra} & {*entry, *HOST_FIELDS} | {"disposition"} & {*entry})
        if clash:  # asserted_by and methods come from the view, disposition from the review set (G9, G11)
            raise ValueError(f"{entry['id']}: {clash} may be set only by the host")
        props = _flat({**{k: v for k, v in entry.items() if k not in ("id", *drop)}, **extra})
        if entry["id"] in dispositions:
            props["disposition"] = dispositions[entry["id"]]
        return props

    claims, versions = nodes.get("Claim", {}), nodes.get("PaperVersion", {})
    for label, rows in nodes.items():
        for row in rows.values():
            drop, extra = (), {}
            if label == "Junction":
                drop, extra = ("legs",), {"leg_count": len(row["legs"])}
            if label == "ClaimReading" and row["display_text_class"] == "VERBATIM":
                version = versions.get(claims.get(row["claim_id"], {}).get("paper_version_id"), {})
                drop = () if version.get("redistribution") == "OPEN" else ("display_text",)  # I-13
            group = _PLACEHOLDER[row["kind"]] if label == "Placeholder" else label
            if group not in GROUPS or group == "Corpus":
                raise KeyError("no projection template for node label " + label)
            out_nodes.setdefault(group, []).append(
                {"id": row["id"], "content_sha256": row["content_sha256"], "props": element(row, drop, **extra)})
    corpus = set()
    for edge in edges.values():
        if edge["type"] in DERIVED:
            raise ValueError(edge["id"] + ": PREMISE_OF and CONCLUDES are derived from junctions only")
        if edge["type"] == "INCLUDES":
            if edge["start_id"] != manifest["corpus_id"]:
                raise ValueError(edge["id"] + ": INCLUDES from a corpus other than the manifest's")
            corpus.update(edge["asserted_by"])
    for edge in (*edges.values(), *derived):
        props = element({k: v for k, v in edge.items() if k not in ("type", "start_id", "end_id", "props")},
                        **edge["props"])
        out_rels.setdefault(edge["type"], []).append({"id": edge["id"], "content_sha256": edge["content_sha256"],
                                                      "start": edge["start_id"], "end": edge["end_id"],
                                                      "props": props})
    if corpus:
        cid = manifest["corpus_id"]
        entry = {"id": cid, "content_sha256": digest(canonical({"corpus_id": cid})), "asserted_by": sorted(corpus)}
        out_nodes["Corpus"] = [{"id": entry["id"], "content_sha256": entry["content_sha256"], "props": element(entry)}]
    return {"nodes": {g: sorted(rs, key=lambda r: r["id"]) for g, rs in sorted(out_nodes.items())},
            "rels": {t: sorted(rs, key=lambda r: r["id"]) for t, rs in sorted(out_rels.items())},
            "delta_set_digest": delta_set_digest(manifest),
            "params": {"deltas": list(manifest["deltas"]), "dispositions": dict(dispositions), "enums": ENUMS}}


def projection_manifest(manifest, review_set_digest):
    """The BUILDING ProjectionManifest row for one DeltaSetManifest plus one review-set digest."""
    identity = {"delta_set_digest": delta_set_digest(manifest), "review_set_digest": review_set_digest,
                "loader_version": LOADER_VERSION}
    return {"id": make_id("projection", identity), "content_sha256": digest(canonical(identity)), **identity,
            "state": "BUILDING", "audit_counts": {}}


def _chunks(rows):
    return (rows[i:i + BATCH] for i in range(0, len(rows), BATCH))


def load(client, rows, manifest):
    """§9.4: schema, BUILDING, preflight, node then relationship batches, audits, READY.

    client.run(statement, parameters, tx_metadata) -> [row dict]. Returns the READY manifest row;
    raises LoadError (manifest FAILED once it was written) on any mismatch, shortfall, audit row or
    client error, chained to the client's exception. A database holding another projection is refused:
    v0.4 always rebuilds from empty.
    """
    if rows["delta_set_digest"] != manifest["delta_set_digest"]:
        raise LoadError("rows and ProjectionManifest name different delta sets")
    meta = {k: manifest[k] for k in ("id", "delta_set_digest", "review_set_digest")}

    def run(statement, parameters=None):
        return client.run(statement, parameters or {}, meta)

    def mark(state, counts):
        row = dict(manifest, state=state, audit_counts=counts)
        run(SET_MANIFEST, {"id": row["id"], "props": _flat(row)})
        return row

    try:  # steps 1-2 write no manifest, so a client error here leaves nothing to mark FAILED
        for statement in SCHEMA:
            run(statement)
        others = sorted(r["id"] for r in run(EXISTING) if r["id"] != manifest["id"])
    except Exception as error:
        raise LoadError(f"{type(error).__name__}: {error}") from error
    if others:
        raise LoadError(f"database holds another projection {others}; rebuild from empty (§9.4)")
    plan = [(g, NODE_PREFLIGHT, NODE_MERGE[g], rs) for g, rs in rows["nodes"].items()] + \
           [(t, REL_PREFLIGHT[t], REL_MERGE[t], rs) for t, rs in rows["rels"].items()]
    counts = {}
    try:
        mark("BUILDING", {})
        stale = [r["id"] for _, check, _, rs in plan for batch in _chunks(rs) for r in run(
            check, {"rows": [{"id": x["id"], "content_sha256": x["content_sha256"]} for x in batch]})]
        if stale:
            raise LoadError(f"preflight: {len(stale)} loaded ids differ in content, e.g. {stale[:5]}")
        for key, _, merge, rs in plan:
            for batch in _chunks(rs):
                written = run(merge, {"rows": batch})
                if not written or written[0]["n"] != len(batch):
                    raise LoadError(f"{key}: a batch of {len(batch)} rows returned {written}")
            counts[key] = len(rs)
        found = {name: [r["id"] for r in run(query, {k: rows["params"][k] for k in re.findall(r"\$(\w+)", query)})]
                 for name, query in AUDITS}  # only the parameters it names: G11 alone needs the dispositions
        counts.update({name: len(ids) for name, ids in found.items()})
        failed = {name: ids[:5] for name, ids in found.items() if ids}
        if failed:
            raise LoadError(f"audits returned rows: {failed}")
    except Exception as error:  # any abort after BUILDING, a client or server error included, ends FAILED
        with contextlib.suppress(Exception):  # a dead server must not mask the original error
            mark("FAILED", counts)
        if isinstance(error, LoadError):
            raise
        raise LoadError(f"{type(error).__name__}: {error}") from error
    return mark("READY", counts)


class QueryClient:
    """Neo4j Query API (POST /db/{db}/query/v2): one auto-commit request per call, single writer."""

    def __init__(self, base_url, database, user, password):
        self.url = f"{base_url.rstrip('/')}/db/{urllib.parse.quote(database)}/query/v2"
        self.headers = {"Content-Type": "application/json", "Accept": "application/json",
                        "Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}

    def run(self, statement, parameters, tx_metadata):
        body = json.dumps({"statement": statement, "parameters": parameters, "txMetadata": tx_metadata})
        request = urllib.request.Request(self.url, body.encode(), self.headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                out = json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Query API HTTP {error.code}: {error.read()[:2000]!r}") from None
        if out.get("errors"):
            raise RuntimeError(f"Query API errors: {out['errors']}")
        data = out["data"]
        return [dict(zip(data["fields"], values)) for values in data["values"]]


_CSV_TYPES = {bool: "boolean", int: "long", float: "double", str: "string"}


def _csv_cell(value):
    if isinstance(value, list):
        if any(";" in str(v) for v in value):
            raise ValueError("array element contains the array delimiter ';'")
        return ";".join(_csv_cell(v) for v in value)
    return str(value).lower() if isinstance(value, bool) else str(value)


def _write_csv(path, head, leads, props):
    types = {}
    for p in props:
        for k, v in p.items():
            kind = _CSV_TYPES[type(v[0])] + "[]" if isinstance(v, list) else _CSV_TYPES[type(v)]
            if types.setdefault(k, kind) != kind:
                raise ValueError(f"{path.name}: {k} mixes {types[k]} and {kind}")
    keys = sorted(types)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([*head, *(f"{k}:{types[k]}" for k in keys)])
        w.writerows([*lead, *("" if p.get(k) is None else _csv_cell(p[k]) for k in keys)]
                    for lead, p in zip(leads, props))


def export_csv(rows, directory):
    """Write neo4j-admin 'database import full' inputs and return its argv (outside the contract:
    run load() afterwards, which preflights, merges as no-ops, audits and sets READY)."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    argv = ["neo4j-admin", "database", "import", "full", "--multiline-fields=true"]
    for g, rs in rows["nodes"].items():
        path = directory / f"nodes-{g}.csv"
        labels = ";".join([*GROUPS[g].split(":"), "Entity"])
        _write_csv(path, ["id:ID", ":LABEL"], [[r["id"], labels] for r in rs], [r["props"] for r in rs])
        argv.append(f"--nodes={path}")
    for t, rs in rows["rels"].items():
        path = directory / f"rels-{t}.csv"
        _write_csv(path, [":START_ID", ":END_ID", ":TYPE", "id"], [[r["start"], r["end"], t, r["id"]] for r in rs],
                   [r["props"] for r in rs])
        argv.append(f"--relationships={path}")
    return [*argv, "neo4j"]
