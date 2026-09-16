#!/usr/bin/env python3
"""Extract a closed, pinned vibefeld JSON profile without executing Go code.

The generated schemas are runtime artifacts: consumers do not need Reference/.
Regeneration and --check require the pinned source checkout.  --check performs
no writes.  JSON Schema checks structure, not event causality, source fidelity,
identity, evidence execution, or mathematical correctness.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys


COMMIT = "392b2da3bee5766cca1a201f28e0255056baaba4"
PROFILE = "agtxiv.vibefeld-offline/392b2da3.1"
SCHEMA_URI = "https://agtxiv.org/schema/v3/0.0.0/upstream/vibefeld-392b2da3/"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "Reference" / f"vibefeld-{COMMIT}" / f"vibefeld-{COMMIT}"
DEFAULT_OUTPUT = ROOT / "schema v0.0" / "upstream" / "vibefeld-392b2da3"

# These are source-byte pins, not values refreshed from the current checkout.
# A changed file requires a reviewed profile revision, never a silent update.
SOURCE_PINS = {
    "internal/ledger/event.go": "d74b276292e9708db88c2cbc304c39b9b5f022ca2f7855cea6a2f8e4dee9d98f",
    "internal/ledger/read.go": "5cfb0e722ba9d6a017c0018fc74a082c4dbead37df0cc226a0fceb3cee61b038",
    "internal/ledger/filename.go": "48297faf7b19921e1d793d1583261b5e1b43e4870d1823776004efd2a9155dbd",
    "internal/state/replay.go": "a0463dec715a801d101d0614d2eadc6c31aa1fc3222a28eada4213bf31db7ea8",
    "internal/state/apply.go": "fc5440844798c8d2b25e67461b78febb74f76effe93d946034f6fd23582a7265",
    "internal/state/state.go": "16cd6ccd2746ca3b6948a5584dff1241932223fe9aa9b24421cd732fc1b12c53",
    "internal/node/node.go": "5842f034525c8bd8c0aa2a714bf741ef335311ffb6b6e5b96aefe2b94c4352bb",
    "internal/node/definition.go": "d17f53b66f5e7093fcc690ec6894b8fb4445eb84d904054d12413d539e03f435",
    "internal/node/assumption.go": "4988b47f8355d68d7efedfefcfca24c97d9b5c8c095996431140cf34900c8e9f",
    "internal/node/external.go": "319d7e17c12b2d9bf9e8cad917443a56316bce3a20575758cbd95acde10c2f5f",
    "internal/node/lemma.go": "11780f6a9b994b60cba0ef69235556e27bcae2b22a4508bb2b43fd9f3f4c65dc",
    "internal/node/pending_def.go": "0adfe610b0b0f83f839b52565e7e0b6d66eb9e8e65aacd6e8c7ea8082900ce76",
    "internal/node/challenge.go": "95c4834eed90a06cc7fda5ad58a306fc4d827de7dd9e0c45603023d1b5659dfa",
    "internal/node/context_validate.go": "5ddc729c73512ecd0fbd5e793f3de3fed46201f2f87c45920d94108576d330fb",
    "internal/config/config.go": "0fe0954e5cc024dbf1e4b29d08763dc16a28a5f0a278c27d27049d9f43cdf5c9",
    "internal/export/graph.go": "7eba12688e5fe74feb4956246b282aab77a44088c5cb2b7fb763795a42ef005b",
    "internal/export/graph_closure.go": "f73e56280323312adf185213349f8daccfd307380103de50130cf3886649a2e9",
    "internal/export/export.go": "af6831189f18c841549dfa2f5118a159313ec95d1f830cf2f8a2df093e866b62",
    "internal/schema/nodetype.go": "1435ff2ec9a45720e5ad4ef7f17b73205fe7024b1929a000f05035a3e456c2b3",
    "internal/schema/workflow.go": "e181630ea2ca1f7d8761d11a511fd95e9c37dcd9dcacfbc35f1e3aaa465c2e7b",
    "internal/schema/epistemic.go": "44cb434830b52308782c6edbaff7db4538baf17b4900aa55aeca214bed34f44c",
    "internal/schema/severity.go": "59d1ae7d8be72dc4ea32d1e23531e42bf56cdeeb389b65627928c2e1dc7f5081",
    "internal/schema/category.go": "f93dc83a37649d2ca63210ea68003c2df125c66c93850fce327d2b1dd9aaaac0",
    "internal/types/time.go": "ae7accb23b4325cccf29b368fa722489c4c17aa41004614f543ba39e0b9e41f2",
    "internal/types/id.go": "8a1b20ba5cafe726736043ecfa2ce1f81499cd47067557fa29337ce7b1f73785",
    "internal/jobs/prover.go": "33c291633c4f9dc8915e1a5a6b0e7964b979eb0aa2b93b9e65f5ed0c7739632f",
    "internal/jobs/verifier.go": "211f77e10a774a25665b8122bc36e771c459c44dc6d89cdee995087ddfa6922c",
    "internal/taint/propagate.go": "62530f9290d808ad3d6dc7a95ed4ba119e924144d6facd11d20010626a7669ce",
    "internal/scope/scope.go": "82a72c3fe927509a0097e851a36ffd0a75a1d416fe7ea6c496d9041fb08e8ea9",
    "internal/scope/tracker.go": "a65990f7a18248bea9cd743c679769e01eaf552c65a792a5a085d4d90ab58d8b",
    "internal/service/proof.go": "d02edd4579d4d1a55a25943d8929d36072e4d43a0f863d0d07bfa64a6c934548",
    "internal/fs/init.go": "f635f0d78f77df9eab1c6a99287a499b6d2986659870c9f5591acf3b7a537b30",
    "internal/fs/paths.go": "49ad6903ecec2eb08ccc4050912f5afc8d86047faffa27196cb06bc734642cad",
    "internal/fs/schema_io.go": "9d974f6a3a9f0c39b03d8baa11313dce22dba3ee477d98413304c778bcf918ac",
    "internal/fs/pending_def_io.go": "49ef5ed7d2ee00576fbc419e3b9f727e6039e8d06b08277f6889b7d8dfe129c3",
}

STRUCT_RE = re.compile(r"^type (\w+) struct \{(.*?)^\}", re.M | re.S)
FIELD_RE = re.compile(r'(\w+)\s+(\S+)\s+`json:"([^"`]+)"`')
EVENT_RE = re.compile(r'\bEvent(\w+)\s+EventType\s*=\s*"([^"\n]+)"')
TIMESTAMP_PATTERN = (
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]{1,9})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])$"
)


def serialized(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2) + "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read_sources(source: Path) -> dict[str, str]:
    """Require regular, non-symlink pinned files before parsing any source."""
    if source.is_symlink() or not source.is_dir():
        raise ValueError(f"Source must be an existing non-symlink directory: {source}")
    result = {}
    for name, expected in SOURCE_PINS.items():
        path = source
        for part in Path(name).parts:
            path = path / part
            if path.is_symlink():
                raise ValueError(f"Pinned source path contains a symlink: {name}")
        if not path.is_file():
            raise ValueError(f"Missing pinned source file: {name}")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"Pinned source hash mismatch: {name}")
        result[name] = raw.decode("utf-8")
    return result


def enum_values(sources: dict[str, str], path: str, go_type: str) -> list[str]:
    values = re.findall(r'\b\w+\s+' + re.escape(go_type) + r'\s*=\s*"([^"\n]*)"', sources[path])
    if not values or len(values) != len(set(values)):
        raise ValueError(f"Missing or duplicate {go_type} constants in {path}")
    return values


def extract_struct(sources: dict[str, str], path: str, name: str) -> dict:
    matches = [m for m in STRUCT_RE.finditer(sources[path]) if m[1] == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one Go struct {name} in {path}")
    match = matches[0]
    fields = []
    embedded = []
    for raw in match[2].splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line == "BaseEvent":
            embedded.append(line)
            continue
        field = FIELD_RE.fullmatch(line)
        if not field:
            raise ValueError(f"Unsupported pinned Go field in {name}: {line}")
        go_name, go_type, tag = field.groups()
        parts = tag.split(",")
        if len(parts) > 2 or (len(parts) == 2 and parts[1] != "omitempty"):
            raise ValueError(f"Unsupported Go JSON tag: {tag}")
        fields.append({"go_field": go_name, "go_type": go_type, "json_field": parts[0], "omitempty": len(parts) == 2})
    names = [field["json_field"] for field in fields]
    if len(set(names)) != len(names):
        raise ValueError(f"Duplicate JSON fields in {name}")
    return {"source_path": path, "go_struct": name, "source_line": sources[path].count("\n", 0, match.start()) + 1, "embedded": embedded, "fields": fields}


def ref(name: str) -> dict:
    return {"$ref": f"#/$defs/{name}"}


def primitive_defs(sources: dict[str, str], events: dict[str, str]) -> dict:
    enums = {
        "EventType": list(events.values()),
        "NodeType": enum_values(sources, "internal/schema/nodetype.go", "NodeType"),
        "WorkflowState": enum_values(sources, "internal/schema/workflow.go", "WorkflowState"),
        "EpistemicState": enum_values(sources, "internal/schema/epistemic.go", "EpistemicState"),
        "TaintState": enum_values(sources, "internal/node/node.go", "TaintState"),
        "PendingDefStatus": enum_values(sources, "internal/node/pending_def.go", "PendingDefStatus"),
    }
    result = {name: {"type": "string", "enum": values} for name, values in enums.items()}
    result.update({
        "NodeID": {"type": "string", "pattern": r"^1(?:\.[1-9][0-9]*)*$", "description": "Canonical hierarchical ID; numeric aliases accepted by Go are deliberately rejected by this import profile."},
        "TimestampString": {"type": "string", "format": "date-time", "pattern": TIMESTAMP_PATTERN, "description": "RFC3339 timestamp with at most nine fractional digits. Preserve original bytes and nanosecond precision; calendar validity requires format checking."},
        "Timestamp": {"anyOf": [ref("TimestampString"), {"type": "null"}], "description": "The pinned Go timestamp decoder also accepts null as its zero value; null is never evidence of a recorded time."},
        "ContentHash": {"type": "string", "pattern": r"^[0-9a-f]{64}$", "description": "Upstream lowercase SHA256 text without a prefix. Structure alone does not verify its content preimage."},
        "NonnegativeInteger": {"type": "integer", "minimum": 0, "maximum": 9223372036854775807},
    })
    return result


def type_schema(go_type: str, known_structs: set[str]) -> dict:
    if go_type.startswith("[]"):
        return {"type": ["array", "null"], "items": type_schema(go_type[2:], known_structs)}
    if go_type == "map[string]int":
        return {"type": "object", "additionalProperties": ref("NonnegativeInteger")}
    aliases = {
        "types.NodeID": "NodeID", "types.Timestamp": "Timestamp", "time.Time": "Timestamp",
        "schema.NodeType": "NodeType", "schema.WorkflowState": "WorkflowState",
        "schema.EpistemicState": "EpistemicState", "node.TaintState": "TaintState",
        "TaintState": "TaintState", "PendingDefStatus": "PendingDefStatus", "EventType": "EventType",
    }
    if go_type in aliases:
        return ref(aliases[go_type])
    if go_type in {"string", "schema.InferenceType"}:
        return {"type": "string"}
    if go_type == "bool":
        return {"type": "boolean"}
    if go_type in {"int", "time.Duration"}:
        return {"type": "integer", "minimum": -9223372036854775808, "maximum": 9223372036854775807}
    if go_type == "float64":
        return {"type": "number"}
    name = go_type.removeprefix("node.")
    if name in known_structs:
        return ref(name)
    raise ValueError(f"Unsupported pinned Go type: {go_type}")


def object_schema(spec: dict, specs: dict, events: dict[str, str]) -> dict:
    fields = []
    for embedded in spec["embedded"]:
        fields.extend(specs[embedded]["fields"])
    fields.extend(spec["fields"])
    names = [field["json_field"] for field in fields]
    if len(names) != len(set(names)):
        raise ValueError(f"Embedded field collision in {spec['go_struct']}")
    properties = {field["json_field"]: type_schema(field["go_type"], set(specs)) for field in fields}
    if spec["go_struct"] in events:
        properties["type"] = {"const": events[spec["go_struct"]]}
    if "content_hash" in properties:
        properties["content_hash"] = ref("ContentHash")
    return {
        "type": "object", "additionalProperties": False,
        "properties": properties,
        "required": [field["json_field"] for field in fields if not field["omitempty"]],
        "description": f"Pinned {spec['go_struct']} from {spec['source_path']}; only non-omitempty JSON fields are required.",
    }


def document(filename: str, defs: dict, root_schema: dict) -> dict:
    return {
        "$schema": DRAFT, "$id": SCHEMA_URI + filename,
        "title": f"AgtXIv pinned vibefeld {filename.removesuffix('.schema.json')} import profile",
        "description": "Closed structural profile for one pinned upstream commit. This is neither a scientific validity certificate nor an upstream-issued JSON Schema.",
        "x-upstream-commit": COMMIT, "x-import-profile": PROFILE,
        **root_schema, "$defs": defs,
    }


def generate_artifacts(source: Path) -> dict[str, bytes]:
    sources = read_sources(source)
    events = dict(EVENT_RE.findall(sources["internal/ledger/event.go"]))
    if len(events) != 35 or len(set(events.values())) != 35:
        raise ValueError("Expected exactly 35 distinct pinned event discriminators")
    event_path = "internal/ledger/event.go"
    event_specs = {name: extract_struct(sources, event_path, name) for name in ["BaseEvent", "Definition", "Lemma", "OutlineStage", *events]}
    # Check the entire source event-struct surface, including helper payloads.
    if set(event_specs) != {m[1] for m in STRUCT_RE.finditer(sources[event_path])}:
        raise ValueError("Unrepresented Go event struct in pinned source")
    node_spec = extract_struct(sources, "internal/node/node.go", "Node")
    event_specs["Node"] = node_spec
    graph_specs = {name: extract_struct(sources, "internal/export/graph.go", name) for name in ["GraphWorkspace", "GraphNode", "GraphValidation", "GraphExport"]}
    sidecar_specs = {name: extract_struct(sources, f"internal/node/{file}.go", name) for name, file in [("Definition", "definition"), ("Assumption", "assumption"), ("External", "external"), ("Lemma", "lemma"), ("PendingDef", "pending_def")]}
    sidecar_specs["Config"] = extract_struct(sources, "internal/config/config.go", "Config")
    sidecar_specs["Node"] = node_spec
    primitive = primitive_defs(sources, events)
    event_defs = {**copy.deepcopy(primitive), **{name: object_schema(spec, event_specs, events) for name, spec in event_specs.items()}}
    sidecar_defs = {**copy.deepcopy(primitive), **{name: object_schema(spec, sidecar_specs, events) for name, spec in sidecar_specs.items()}}
    graph_defs = {**copy.deepcopy(primitive), **{name: object_schema(spec, graph_specs, events) for name, spec in graph_specs.items()}}

    version_match = re.search(r'const GraphSchemaVersion = "([^"\n]+)"', sources["internal/export/graph.go"])
    if not version_match or version_match[1] != "1":
        raise ValueError("Unsupported graph schema version")
    feature_source = sources["internal/export/graph_closure.go"]
    feature_constants = dict(re.findall(r'\b(Feature\w+)\s*=\s*"([^"\n]+)"', feature_source))
    feature_block = re.search(r"var GraphFeatures = \[\]string\{(.*?)\}", feature_source, re.S)
    if not feature_block:
        raise ValueError("Missing GraphFeatures initializer")
    feature_names = re.findall(r"\bFeature\w+\b", feature_block[1])
    features = [feature_constants[name] for name in feature_names]
    if features != ["readiness-flags", "closure-flag", "node-dependencies", "proof-author"]:
        raise ValueError("Unsupported graph feature profile")
    export_properties = graph_defs["GraphExport"]["properties"]
    export_properties["schema_version"] = {"const": "1"}
    export_properties["features"] = {"type": "array", "const": features, "description": "Exact ordered capability list emitted by this fixed commit; missing, added, or changed tokens reject this profile."}
    # BuildGraphExport initializes nodes and count maps, even for nil state.
    export_properties["nodes"]["type"] = "array"
    graph_node = graph_defs["GraphNode"]["properties"]
    for field, name in {"id": "NodeID", "type": "NodeType", "parent_id": "NodeID", "workflow_state": "WorkflowState", "epistemic_state": "EpistemicState", "taint_state": "TaintState", "created": "TimestampString"}.items():
        graph_node[field] = ref(name)
    for field in ["child_ids", "dependencies"]:
        graph_node[field]["items"] = ref("NodeID")
    counts = graph_defs["GraphValidation"]["properties"]
    for field in ["total_nodes", "total_challenges"]:
        counts[field] = ref("NonnegativeInteger")
    for field, values in {
        "epistemic_counts": primitive["EpistemicState"]["enum"],
        "taint_counts": primitive["TaintState"]["enum"],
        "challenge_status_counts": ["open", "resolved", "withdrawn", "superseded"],
    }.items():
        counts[field] = {"type": "object", "additionalProperties": False, "properties": {value: ref("NonnegativeInteger") for value in values}}
    sidecar_defs["Config"]["properties"]["version"] = {"const": "1.0"}

    schemas = {
        "event.schema.json": document("event.schema.json", event_defs, {"oneOf": [ref(name) for name in events]}),
        "graph.schema.json": document("graph.schema.json", graph_defs, ref("GraphExport")),
        "sidecar.schema.json": document("sidecar.schema.json", sidecar_defs, {"oneOf": [ref(name) for name in sidecar_specs]}),
    }
    artifacts = {name: serialized(schema) for name, schema in schemas.items()}
    manifest = {
        "profile": PROFILE, "status": "EXPERIMENTAL_PINNED_STRUCTURAL_PROFILE",
        "upstream_repository": "https://github.com/tobiasosborne/vibefeld", "upstream_commit": COMMIT,
        "graph_schema_version": "1", "graph_features": features, "event_count": len(events),
        "unknown_field_policy": "REJECT_ACTIVE_IMPORT_AND_PRESERVE_ORIGINAL_BYTES_OUTSIDE_THIS_PROFILE",
        "unknown_event_policy": "REJECT_REPLAY_AND_PRESERVE_ORIGINAL_BYTES_OUTSIDE_THIS_PROFILE",
        "historical_missing_field_policy": "Only omitempty fields are optional; a missing non-omitempty field is outside this pinned emission profile, even if Go could decode a zero value.",
        "array_policy": "Go slices accept null and empty arrays; omitempty controls required fields. Graph features and nodes are always initialized by the pinned exporter.",
        "normalization_policy": "Preserve upstream raw bytes; do not apply AgtXIv record normalization to source text, nanosecond timestamps, floats, or upstream content hashes.",
        "proof_limitations": [
            "Schemas check structural compatibility only; replay and graph agreement require separate code.",
            "Driver-supplied author and reviewer labels are not authenticated identities.",
            "Upstream validated, closed, and passed fields are not Lean kernel checks or mathematical correctness certificates.",
            "Graph exports omit context, scope, validation_deps, challenge bodies, and evidence histories; a graph alone is not a full snapshot.",
            "Replay scope timestamps use runtime Now and discard discharge_node_id; original scope events must remain available.",
            "Missing historical identity, challenge response text, or definition history must remain unknown rather than invented.",
        ],
        "schemas": [{"path": name, "uri": schemas[name]["$id"], "sha256": sha256(raw), "byte_size": len(raw)} for name, raw in artifacts.items()],
        "source_files": [{"path": name, "sha256": "sha256:" + digest, "byte_size": len(sources[name].encode("utf-8"))} for name, digest in SOURCE_PINS.items()],
        "events": [{"event_type": value, "go_struct": name, "schema_ref": "event.schema.json#/$defs/" + name, "source_path": event_path, "source_line": event_specs[name]["source_line"]} for name, value in events.items()],
        "structs": [{"schema_file": filename, "schema_def": name, **spec} for filename, specs in [("event.schema.json", event_specs), ("graph.schema.json", graph_specs), ("sidecar.schema.json", sidecar_specs)] for name, spec in specs.items()],
    }
    artifacts["manifest.json"] = serialized(manifest)
    return artifacts


def synthetic_fixture(schema: dict, root: dict) -> object:
    """A deterministic structural witness, never a scientific fixture."""
    if "$ref" in schema:
        prefix = "#/$defs/"
        if not schema["$ref"].startswith(prefix):
            raise ValueError("Self-check encountered a nonlocal reference")
        return synthetic_fixture(root["$defs"][schema["$ref"][len(prefix):]], root)
    if "const" in schema:
        return copy.deepcopy(schema["const"])
    if "enum" in schema:
        return copy.deepcopy(schema["enum"][0])
    if "anyOf" in schema or "oneOf" in schema:
        return synthetic_fixture(schema.get("anyOf", schema.get("oneOf"))[0], root)
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = kind[0]
    if kind == "object":
        return {name: synthetic_fixture(schema["properties"][name], root) for name in schema.get("required", [])}
    if kind == "array":
        return []
    if kind == "boolean":
        return False
    if kind in {"integer", "number"}:
        return max(0, schema.get("minimum", 0))
    if kind == "null":
        return None
    if kind == "string":
        if schema.get("format") == "date-time":
            return "2026-01-01T00:00:00.123456789Z"
        pattern = schema.get("pattern", "")
        if "[0-9a-f]{64}" in pattern:
            return "0" * 64
        if pattern.startswith("^1(?:"):
            return "1"
        return "SYNTHETIC"
    raise ValueError(f"Unsupported fixture schema: {schema}")


def check_structural_artifacts(artifacts: dict[str, bytes]) -> dict[str, int]:
    """Check schemas, all local references, and positive/negative witnesses."""
    from jsonschema import Draft202012Validator, FormatChecker

    positive = negative = 0
    for filename, raw in artifacts.items():
        if not filename.endswith(".schema.json"):
            continue
        schema = json.loads(raw)
        Draft202012Validator.check_schema(schema)
        def check_refs(value: object) -> None:
            if isinstance(value, dict):
                if "$ref" in value:
                    uri = value["$ref"]
                    if not uri.startswith("#/$defs/") or uri.removeprefix("#/$defs/") not in schema["$defs"]:
                        raise ValueError(f"Unresolved or nonlocal schema reference: {filename} {uri}")
                for item in value.values():
                    check_refs(item)
            elif isinstance(value, list):
                for item in value:
                    check_refs(item)
        check_refs(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        # Validate every extracted nested struct, not only the root branches.
        # These witnesses intentionally contain no real paper or proof data.
        for name, definition in schema["$defs"].items():
            if definition.get("type") != "object" or "properties" not in definition:
                continue
            scoped = Draft202012Validator(
                {"$defs": schema["$defs"], **ref(name)},
                format_checker=FormatChecker(),
            )
            fixture = synthetic_fixture(definition, schema)
            scoped.validate(fixture)
            positive += 1
            if scoped.is_valid({**fixture, "unknown_synthetic_field": True}):
                raise ValueError(f"Nested unknown-field check failed: {filename} {name}")
            negative += 1
            for field in definition.get("required", []):
                if scoped.is_valid({key: value for key, value in fixture.items() if key != field}):
                    raise ValueError(f"Nested required-field check failed: {filename} {name} {field}")
                negative += 1
            for field, field_schema in definition["properties"].items():
                if field_schema.get("type") == ["array", "null"]:
                    scoped.validate({**fixture, field: None})
                    scoped.validate({**fixture, field: []})
                    positive += 2
            if "content_hash" in definition["properties"]:
                if scoped.is_valid({**fixture, "content_hash": "not-a-sha256"}):
                    raise ValueError(f"Nested hash-format check failed: {filename} {name}")
                negative += 1
                # Changing a well-formed digest is deliberately not a schema
                # error: actual content-hash agreement belongs to replay.
                scoped.validate({**fixture, "content_hash": "1" * 64})
                positive += 1
        branches = schema.get("oneOf", [{"$ref": "#/$defs/GraphExport"}])
        for branch in branches:
            fixture = synthetic_fixture(branch, schema)
            validator.validate(fixture)
            positive += 1
            tampered = {**fixture, "unknown_synthetic_field": True}
            if validator.is_valid(tampered):
                raise ValueError(f"Unknown-field negative check failed: {filename}")
            negative += 1
            if filename == "event.schema.json":
                tampered = {**fixture, "type": "unknown_synthetic_event"}
                if validator.is_valid(tampered):
                    raise ValueError("Unknown-event negative check failed")
                negative += 1
                for field in ["type", "timestamp"]:
                    tampered = {key: value for key, value in fixture.items() if key != field}
                    if validator.is_valid(tampered):
                        raise ValueError(f"Required event field negative check failed: {field}")
                    negative += 1
                definition = schema["$defs"][branch["$ref"].split("/")[-1]]
                for field, field_schema in definition["properties"].items():
                    if field_schema.get("type") == ["array", "null"]:
                        validator.validate({**fixture, field: None})
                        positive += 1
        if filename == "graph.schema.json":
            fixture = synthetic_fixture(ref("GraphExport"), schema)
            for field, value in [("schema_version", "2"), ("features", []), ("features", fixture["features"] + ["unknown-feature"])]:
                if validator.is_valid({**fixture, field: value}):
                    raise ValueError(f"Pinned graph protocol negative check failed: {field}")
                negative += 1
    return {"schema_documents": 3, "positive_structural_checks": positive, "negative_structural_checks": negative}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE, help="Pinned source directory, read only")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Verify source pins, schema checks, and exact generated bytes without writing")
    args = parser.parse_args(argv)
    try:
        artifacts = generate_artifacts(args.source_root)
        checks = check_structural_artifacts(artifacts)
        if args.check:
            for name, expected in artifacts.items():
                path = args.output_dir / name
                if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
                    raise ValueError(f"Generated artifact mismatch: {path}")
        else:
            if args.output_dir.is_symlink():
                raise ValueError("Output directory cannot be a symlink")
            args.output_dir.mkdir(parents=True, exist_ok=True)
            for name, raw in artifacts.items():
                target = args.output_dir / name
                if target.is_symlink():
                    raise ValueError(f"Output artifact cannot be a symlink: {target}")
                target.write_bytes(raw)
        print(json.dumps({"status": "MATCH" if args.check else "GENERATED", "profile": PROFILE, "event_count": 35, "source_files_checked": len(SOURCE_PINS), "executed_upstream_code": False, **checks}))
        return 0
    except (OSError, ValueError, ImportError) as exc:
        print(f"vibefeld protocol generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
