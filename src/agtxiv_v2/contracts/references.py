"""Pure exact-reference resolution and immutable-envelope checks.

All targets are supplied explicitly as immutable in-memory values.  A path hint
is display text only: this module has no filesystem, URL, Git, registry, clock,
or process adapter and never substitutes a target found at a similar locator.
``schema_uri`` is a one-way assertion: when a ref includes it the supplied
target must agree; omission makes no URI assertion, and a URI is never fetched.

Record resolution checks only the direct record target and its explicitly
supplied schema bytes.  It deliberately does not inspect the schema ``$id``,
validate the payload against that schema, resolve embedded references, or walk
a transitive contract/bundle closure; those belong to later registry and bundle
validators.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .canonical import (
    IJSON_MAX_INTEGER,
    CanonicalValueIntegrityError,
    ParsedCanonicalValue,
    build_canonical_value,
    record_content_hash,
)
from .diagnostics import Diagnostic, DiagnosticCode

_DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}(?![\s\S])")
_NAMESPACED_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._:/-]*(?![\s\S])"
)
_RECORD_TYPE_PATTERN = re.compile(
    r"^agtxiv\.[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)*/"
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)(?![\s\S])"
)
_MEDIA_TYPE_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/"
    r"[a-z0-9][a-z0-9!#$&^_.+-]*(?![\s\S])"
)
_SCHEMA_URI_PATTERN = re.compile(
    r"^https://agtxiv\.org/schema/v2/contract-kernel/"
    r"[a-z0-9-]+(?:/[a-z0-9-]+)+/"
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*)(?![\s\S])"
)
_JSON_POINTER_PATTERN = re.compile(
    r"^(?:/(?:[^~/\r\n]|~[01])*)+(?![\s\S])"
)
_ROLE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*(?![\s\S])")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,9})?Z(?![\s\S])"
)

_ASSET_REQUIRED = frozenset({"asset_id", "media_type", "byte_size", "sha256"})
_ASSET_ALLOWED = _ASSET_REQUIRED | {"path_hint", "schema_uri"}
_RECORD_REF_KEYS = frozenset(
    {"record_type", "record_id", "record_revision", "schema_ref", "content_hash"}
)
_COMPONENT_REF_KEYS = _RECORD_REF_KEYS | {"component_id", "json_pointer"}
_ENVELOPE_REQUIRED = frozenset(
    {"record_type", "schema_ref", "record_id", "record_revision", "created_at"}
)
_ENVELOPE_ALLOWED = _ENVELOPE_REQUIRED | {
    "contract_bundle_ref",
    "producer_context",
    "supersedes_ref",
}
_CONTRACT_BUNDLE_RECORD_TYPE = "agtxiv.contract-bundle-release/1.0.0"


@dataclass(frozen=True, slots=True)
class SuppliedAsset:
    """One explicitly supplied raw-byte target; it intentionally has no path.

    ``schema_uri`` is optional target metadata.  A ref that supplies the field
    asserts equality; a ref that omits it still resolves by ID, media type,
    byte size, and digest.
    """

    asset_id: str
    media_type: str
    raw_bytes: bytes
    schema_uri: str | None = None


def raw_asset_sha256(raw_bytes: bytes) -> str:
    """Return the raw-byte asset digest, without canonical JSON normalization."""

    if type(raw_bytes) is not bytes:
        raise TypeError("raw_asset_sha256 requires bytes")
    return "sha256:" + hashlib.sha256(raw_bytes).hexdigest()


def resolve_exact_asset_ref(
    ref: ParsedCanonicalValue,
    supplied_assets: tuple[SuppliedAsset, ...],
) -> SuppliedAsset | Diagnostic:
    """Resolve one exact asset only from the explicitly supplied byte tuple.

    Every tuple member is validated before matching, and asset IDs must be
    globally unique.  ``path_hint`` and ``schema_uri`` are never locators.
    """

    ref_object, problem = _parsed_object(ref, "")
    if problem is not None:
        return problem
    assert ref_object is not None
    problem = _validate_asset_ref_object(ref_object, "")
    if problem is not None:
        return problem
    return _resolve_asset_ref_object(ref_object, supplied_assets)


def _resolve_asset_ref_object(
    ref_object: dict[str, Any],
    supplied_assets: tuple[SuppliedAsset, ...],
) -> SuppliedAsset | Diagnostic:
    if type(supplied_assets) is not tuple:
        return _type_mismatch("supplied asset index must be an immutable tuple")

    snapshots: list[tuple[SuppliedAsset, str, str, bytes, str | None]] = []
    seen_asset_ids: set[str] = set()
    for index, asset in enumerate(supplied_assets):
        snapshot, problem = _supplied_asset_snapshot(asset, index)
        if problem is not None:
            return problem
        assert snapshot is not None
        if snapshot[1] in seen_asset_ids:
            return Diagnostic(
                DiagnosticCode.REF_UNRESOLVED,
                "supplied asset index contains a duplicate asset_id",
                f"/supplied_assets/{index}/asset_id",
            )
        seen_asset_ids.add(snapshot[1])
        snapshots.append(snapshot)

    matches = [snapshot for snapshot in snapshots if snapshot[1] == ref_object["asset_id"]]
    if len(matches) != 1:
        return Diagnostic(
            DiagnosticCode.REF_UNRESOLVED,
            "exact asset reference must resolve to exactly one supplied target",
            "/asset_id",
        )
    target, _, media_type, raw_bytes, schema_uri = matches[0]
    if media_type != ref_object["media_type"]:
        return _type_mismatch("supplied asset media type differs from the exact reference", "/media_type")
    if "schema_uri" in ref_object and schema_uri != ref_object["schema_uri"]:
        return _type_mismatch("supplied schema identity differs from the exact reference", "/schema_uri")
    if len(raw_bytes) != ref_object["byte_size"]:
        return Diagnostic(
            DiagnosticCode.REF_HASH_MISMATCH,
            "supplied asset byte size differs from the exact reference",
            "/byte_size",
        )
    if raw_asset_sha256(raw_bytes) != ref_object["sha256"]:
        return Diagnostic(
            DiagnosticCode.REF_HASH_MISMATCH,
            "supplied raw asset bytes differ from the exact SHA-256 reference",
            "/sha256",
        )
    return target


def resolve_exact_record_ref(
    ref: ParsedCanonicalValue,
    supplied_records: tuple[ParsedCanonicalValue, ...],
    supplied_schema_assets: tuple[SuppliedAsset, ...],
) -> ParsedCanonicalValue | Diagnostic:
    """Check a direct record target and its supplied schema bytes.

    This is intentionally not schema ``$id`` checking, payload validation,
    embedded-ref resolution, or transitive contract-closure validation.
    """

    ref_object, problem = _parsed_object(ref, "")
    if problem is not None:
        return problem
    assert ref_object is not None
    problem = _validate_record_ref_object(ref_object, "")
    if problem is not None:
        return problem
    return _resolve_record_ref_object(
        ref_object,
        supplied_records,
        supplied_schema_assets,
    )


def resolve_exact_component_ref(
    ref: ParsedCanonicalValue,
    supplied_records: tuple[ParsedCanonicalValue, ...],
    supplied_schema_assets: tuple[SuppliedAsset, ...],
) -> ParsedCanonicalValue | Diagnostic:
    """Resolve an exact record and then its identity-checked JSON Pointer target."""

    ref_object, problem = _parsed_object(ref, "")
    if problem is not None:
        return problem
    assert ref_object is not None
    problem = _validate_component_ref_object(ref_object, "")
    if problem is not None:
        return problem

    record_ref = {key: ref_object[key] for key in _RECORD_REF_KEYS}
    record = _resolve_record_ref_object(
        record_ref,
        supplied_records,
        supplied_schema_assets,
    )
    if isinstance(record, Diagnostic):
        return record
    document = record.to_python()
    component, found = _resolve_json_pointer(document, ref_object["json_pointer"])
    if not found:
        return Diagnostic(
            DiagnosticCode.REF_UNRESOLVED,
            "component JSON Pointer does not resolve in the exact record",
            "/json_pointer",
        )
    if type(component) is not dict or component.get("component_id") != ref_object["component_id"]:
        return _type_mismatch(
            "resolved component identity differs from the exact component reference",
            "/component_id",
        )
    built = build_canonical_value(component)
    if isinstance(built, Diagnostic):
        return _type_mismatch("resolved component is not a canonical JSON value", "/json_pointer")
    return built


def validate_immutable_envelope(
    envelope: ParsedCanonicalValue,
    *,
    contract_bound: bool,
) -> Diagnostic | None:
    """Check envelope shape plus revision/supersession and contract-binding rules."""

    envelope_object, problem = _parsed_object(
        envelope,
        "",
        code=DiagnosticCode.RECORD_INVALID_ENVELOPE,
    )
    if problem is not None:
        return problem
    assert envelope_object is not None
    return _validate_envelope_object(envelope_object, contract_bound=contract_bound)


def validate_immutable_record(
    record: ParsedCanonicalValue,
    *,
    contract_bound: bool,
) -> Diagnostic | None:
    """Check the immutable envelope and stored canonical record content hash."""

    document, problem = _record_document(record)
    if problem is not None:
        return problem
    assert document is not None
    problem = _validate_envelope_object(
        document["envelope"],
        contract_bound=contract_bound,
    )
    if problem is not None:
        return problem
    stored_hash = document["content_hash"]
    if type(stored_hash) is not str or _DIGEST_PATTERN.fullmatch(stored_hash) is None:
        return Diagnostic(
            DiagnosticCode.RECORD_HASH_MISMATCH,
            "record content_hash is not an exact lowercase SHA-256 digest",
            "/content_hash",
        )
    computed_hash = record_content_hash(record)
    if isinstance(computed_hash, Diagnostic) or computed_hash != stored_hash:
        return Diagnostic(
            DiagnosticCode.RECORD_HASH_MISMATCH,
            "stored record content_hash differs from the canonical record projection",
            "/content_hash",
        )
    return None


def _parsed_object(
    value: ParsedCanonicalValue,
    pointer: str,
    *,
    code: DiagnosticCode = DiagnosticCode.REF_TYPE_MISMATCH,
) -> tuple[dict[str, Any] | None, Diagnostic | None]:
    if type(value) is not ParsedCanonicalValue:
        return None, Diagnostic(code, "value must be a validated canonical JSON object", pointer)
    try:
        detached = value.to_python()
    except CanonicalValueIntegrityError:
        return None, Diagnostic(code, "opaque canonical value failed integrity validation", pointer)
    if type(detached) is not dict:
        return None, Diagnostic(code, "value must be a JSON object", pointer)
    return detached, None


def _validate_asset_ref_object(ref: dict[str, Any], pointer: str) -> Diagnostic | None:
    keys = set(ref)
    if not _ASSET_REQUIRED <= keys or not keys <= _ASSET_ALLOWED:
        return Diagnostic(
            DiagnosticCode.CONTRACT_MUTABLE_REF,
            "asset reference must contain only exact fields; paths, URLs, branches, latest aliases, and digest-free refs are forbidden",
            pointer,
        )
    if (
        type(ref["asset_id"]) is not str
        or not 3 <= len(ref["asset_id"]) <= 256
        or _NAMESPACED_ID_PATTERN.fullmatch(ref["asset_id"]) is None
    ):
        return _type_mismatch("asset_id is not a stable namespaced identity", _child(pointer, "asset_id"))
    if (
        type(ref["media_type"]) is not str
        or not 3 <= len(ref["media_type"]) <= 127
        or _MEDIA_TYPE_PATTERN.fullmatch(ref["media_type"]) is None
    ):
        return _type_mismatch("media_type is invalid", _child(pointer, "media_type"))
    if (
        type(ref["byte_size"]) is not int
        or ref["byte_size"] < 0
        or ref["byte_size"] > IJSON_MAX_INTEGER
    ):
        return _type_mismatch("byte_size is outside the non-negative I-JSON range", _child(pointer, "byte_size"))
    if type(ref["sha256"]) is not str or _DIGEST_PATTERN.fullmatch(ref["sha256"]) is None:
        return Diagnostic(
            DiagnosticCode.CONTRACT_MUTABLE_REF,
            "asset reference lacks an exact lowercase SHA-256 digest",
            _child(pointer, "sha256"),
        )
    if "path_hint" in ref and (
        type(ref["path_hint"]) is not str or not 1 <= len(ref["path_hint"]) <= 4096
    ):
        return _type_mismatch("path_hint must be non-empty display text", _child(pointer, "path_hint"))
    if "schema_uri" in ref and (
        type(ref["schema_uri"]) is not str
        or len(ref["schema_uri"]) > 2048
        or _SCHEMA_URI_PATTERN.fullmatch(ref["schema_uri"]) is None
    ):
        return Diagnostic(
            DiagnosticCode.CONTRACT_MUTABLE_REF,
            "schema_uri must be an immutable versioned AgtXIv schema identity",
            _child(pointer, "schema_uri"),
        )
    return None


def _validate_record_ref_object(ref: dict[str, Any], pointer: str) -> Diagnostic | None:
    if set(ref) != _RECORD_REF_KEYS:
        return Diagnostic(
            DiagnosticCode.CONTRACT_MUTABLE_REF,
            "record reference must contain exactly type, identity, revision, schema asset, and content hash",
            pointer,
        )
    if (
        type(ref["record_type"]) is not str
        or not 15 <= len(ref["record_type"]) <= 256
        or _RECORD_TYPE_PATTERN.fullmatch(ref["record_type"]) is None
    ):
        return _type_mismatch("record_type is not an immutable family version", _child(pointer, "record_type"))
    if (
        type(ref["record_id"]) is not str
        or not 3 <= len(ref["record_id"]) <= 512
        or _NAMESPACED_ID_PATTERN.fullmatch(ref["record_id"]) is None
    ):
        return _type_mismatch("record_id is not a stable namespaced identity", _child(pointer, "record_id"))
    if (
        type(ref["record_revision"]) is not int
        or not 1 <= ref["record_revision"] <= IJSON_MAX_INTEGER
    ):
        return _type_mismatch("record_revision must be a positive I-JSON integer", _child(pointer, "record_revision"))
    if type(ref["schema_ref"]) is not dict:
        return _type_mismatch("schema_ref must be an exact asset reference", _child(pointer, "schema_ref"))
    problem = _validate_asset_ref_object(ref["schema_ref"], _child(pointer, "schema_ref"))
    if problem is not None:
        return problem
    if ref["schema_ref"]["media_type"] != "application/schema+json":
        return _type_mismatch(
            "schema_ref media type must be application/schema+json",
            _child(_child(pointer, "schema_ref"), "media_type"),
        )
    if type(ref["content_hash"]) is not str or _DIGEST_PATTERN.fullmatch(ref["content_hash"]) is None:
        return Diagnostic(
            DiagnosticCode.CONTRACT_MUTABLE_REF,
            "record reference lacks an exact lowercase canonical content hash",
            _child(pointer, "content_hash"),
        )
    return None


def _validate_component_ref_object(ref: dict[str, Any], pointer: str) -> Diagnostic | None:
    if set(ref) != _COMPONENT_REF_KEYS:
        return Diagnostic(
            DiagnosticCode.CONTRACT_MUTABLE_REF,
            "component reference must contain exactly the record and component exact fields",
            pointer,
        )
    record_problem = _validate_record_ref_object(
        {key: ref[key] for key in _RECORD_REF_KEYS},
        pointer,
    )
    if record_problem is not None:
        return record_problem
    if (
        type(ref["component_id"]) is not str
        or not 3 <= len(ref["component_id"]) <= 512
        or _NAMESPACED_ID_PATTERN.fullmatch(ref["component_id"]) is None
    ):
        return _type_mismatch("component_id is not a stable namespaced identity", _child(pointer, "component_id"))
    if (
        type(ref["json_pointer"]) is not str
        or not 1 <= len(ref["json_pointer"]) <= 4096
        or _JSON_POINTER_PATTERN.fullmatch(ref["json_pointer"]) is None
    ):
        return _type_mismatch("json_pointer must be a non-root RFC 6901 pointer", _child(pointer, "json_pointer"))
    return None


def _supplied_asset_snapshot(
    asset: Any,
    index: int,
) -> tuple[
    tuple[SuppliedAsset, str, str, bytes, str | None] | None,
    Diagnostic | None,
]:
    pointer = f"/supplied_assets/{index}"
    if type(asset) is not SuppliedAsset:
        return None, _type_mismatch(
            "every supplied asset must have the exact SuppliedAsset runtime type",
            pointer,
        )
    try:
        asset_id = object.__getattribute__(asset, "asset_id")
        media_type = object.__getattribute__(asset, "media_type")
        raw_bytes = object.__getattribute__(asset, "raw_bytes")
        schema_uri = object.__getattribute__(asset, "schema_uri")
    except AttributeError:
        return None, _type_mismatch(
            "supplied asset is missing required typed fields",
            pointer,
        )
    if (
        type(asset_id) is not str
        or not 3 <= len(asset_id) <= 256
        or _NAMESPACED_ID_PATTERN.fullmatch(asset_id) is None
        or type(media_type) is not str
        or not 3 <= len(media_type) <= 127
        or _MEDIA_TYPE_PATTERN.fullmatch(media_type) is None
        or type(raw_bytes) is not bytes
        or (
            schema_uri is not None
            and (
                type(schema_uri) is not str
                or len(schema_uri) > 2048
                or _SCHEMA_URI_PATTERN.fullmatch(schema_uri) is None
            )
        )
    ):
        return None, _type_mismatch(
            "supplied asset target has invalid typed metadata",
            pointer,
        )
    return (asset, asset_id, media_type, raw_bytes, schema_uri), None


def _resolve_record_ref_object(
    ref: dict[str, Any],
    supplied_records: tuple[ParsedCanonicalValue, ...],
    supplied_schema_assets: tuple[SuppliedAsset, ...],
) -> ParsedCanonicalValue | Diagnostic:
    if type(supplied_records) is not tuple:
        return _type_mismatch("supplied record index must be an immutable tuple")
    candidates: list[tuple[ParsedCanonicalValue, dict[str, Any]]] = []
    for record in supplied_records:
        document, problem = _record_document(record)
        if problem is not None:
            return problem
        assert document is not None
        envelope = document["envelope"]
        if (
            envelope.get("record_id") == ref["record_id"]
            and envelope.get("record_revision") == ref["record_revision"]
        ):
            candidates.append((record, document))
    if len(candidates) != 1:
        return Diagnostic(
            DiagnosticCode.REF_UNRESOLVED,
            "exact record reference must resolve to exactly one supplied identity and revision",
            "/record_id",
        )

    record, document = candidates[0]
    envelope = document["envelope"]
    contract_bound = envelope.get("record_type") != _CONTRACT_BUNDLE_RECORD_TYPE
    envelope_problem = _validate_envelope_object(envelope, contract_bound=contract_bound)
    if envelope_problem is not None:
        return envelope_problem
    if envelope["record_type"] != ref["record_type"]:
        return _type_mismatch("resolved record type differs from the exact reference", "/record_type")
    if not _same_asset_identity(envelope["schema_ref"], ref["schema_ref"]):
        return _type_mismatch("resolved record schema asset differs from the exact reference", "/schema_ref")
    schema_asset = _resolve_asset_ref_object(
        envelope["schema_ref"],
        supplied_schema_assets,
    )
    if isinstance(schema_asset, Diagnostic):
        return schema_asset

    computed_hash = record_content_hash(record)
    if (
        isinstance(computed_hash, Diagnostic)
        or type(document["content_hash"]) is not str
        or document["content_hash"] != computed_hash
        or ref["content_hash"] != computed_hash
    ):
        return Diagnostic(
            DiagnosticCode.REF_HASH_MISMATCH,
            "resolved record bytes differ from the stored or referenced canonical content hash",
            "/content_hash",
        )
    return record


def _record_document(
    record: ParsedCanonicalValue,
) -> tuple[dict[str, Any] | None, Diagnostic | None]:
    document, problem = _parsed_object(
        record,
        "",
        code=DiagnosticCode.RECORD_INVALID_ENVELOPE,
    )
    if problem is not None:
        return None, problem
    assert document is not None
    if set(document) != {"envelope", "payload", "content_hash"}:
        return None, Diagnostic(
            DiagnosticCode.RECORD_INVALID_ENVELOPE,
            "immutable record must contain exactly envelope, payload, and content_hash",
        )
    if type(document["envelope"]) is not dict:
        return None, Diagnostic(
            DiagnosticCode.RECORD_INVALID_ENVELOPE,
            "record envelope must be an object",
            "/envelope",
        )
    return document, None


def _validate_envelope_object(
    envelope: dict[str, Any],
    *,
    contract_bound: bool,
) -> Diagnostic | None:
    keys = set(envelope)
    if not _ENVELOPE_REQUIRED <= keys or not keys <= _ENVELOPE_ALLOWED:
        return Diagnostic(
            DiagnosticCode.RECORD_INVALID_ENVELOPE,
            "envelope has missing or unrecognized fields",
        )
    if (
        type(envelope["record_type"]) is not str
        or not 15 <= len(envelope["record_type"]) <= 256
        or _RECORD_TYPE_PATTERN.fullmatch(envelope["record_type"]) is None
    ):
        return _invalid_envelope("record_type is not an immutable family version", "/record_type")
    is_contract_bundle = envelope["record_type"] == _CONTRACT_BUNDLE_RECORD_TYPE
    if is_contract_bundle == contract_bound:
        return _invalid_envelope(
            "only ContractBundleRelease uses the base envelope; every other record is contract-bound",
            "/record_type",
        )
    if (
        type(envelope["record_id"]) is not str
        or not 3 <= len(envelope["record_id"]) <= 512
        or _NAMESPACED_ID_PATTERN.fullmatch(envelope["record_id"]) is None
    ):
        return _invalid_envelope("record_id is not a stable namespaced identity", "/record_id")
    revision = envelope["record_revision"]
    if type(revision) is not int or not 1 <= revision <= IJSON_MAX_INTEGER:
        return _invalid_envelope("record_revision must be a positive I-JSON integer", "/record_revision")
    if type(envelope["schema_ref"]) is not dict:
        return _invalid_envelope("schema_ref must be an exact schema asset reference", "/schema_ref")
    schema_problem = _validate_asset_ref_object(envelope["schema_ref"], "/schema_ref")
    if schema_problem is not None:
        return schema_problem
    if envelope["schema_ref"]["media_type"] != "application/schema+json":
        return _invalid_envelope("schema_ref media type must be application/schema+json", "/schema_ref/media_type")
    timestamp = envelope["created_at"]
    if type(timestamp) is not str or _UTC_TIMESTAMP_PATTERN.fullmatch(timestamp) is None:
        return _invalid_envelope("created_at must be an exact UTC RFC 3339 timestamp", "/created_at")
    try:
        datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError:
        return _invalid_envelope("created_at is not a valid calendar timestamp", "/created_at")

    if "producer_context" in envelope:
        producer_problem = _validate_producer_context(envelope["producer_context"], "/producer_context")
        if producer_problem is not None:
            return producer_problem

    has_contract = "contract_bundle_ref" in envelope
    if has_contract != contract_bound:
        expectation = "requires" if contract_bound else "forbids"
        return _invalid_envelope(
            f"this envelope mode {expectation} contract_bundle_ref",
            "/contract_bundle_ref",
        )
    if has_contract:
        contract_ref = envelope["contract_bundle_ref"]
        if type(contract_ref) is not dict:
            return _invalid_envelope("contract_bundle_ref must be an exact record reference", "/contract_bundle_ref")
        contract_problem = _validate_record_ref_object(contract_ref, "/contract_bundle_ref")
        if contract_problem is not None:
            return contract_problem
        if contract_ref["record_type"] != _CONTRACT_BUNDLE_RECORD_TYPE:
            return _invalid_envelope(
                "contract_bundle_ref has the wrong record type",
                "/contract_bundle_ref/record_type",
            )

    supersedes = envelope.get("supersedes_ref")
    if revision == 1 and supersedes is not None:
        return Diagnostic(
            DiagnosticCode.RECORD_SUPERSESSION_MISMATCH,
            "first revision cannot supersede an earlier revision",
            "/supersedes_ref",
        )
    if revision > 1 and supersedes is None:
        return Diagnostic(
            DiagnosticCode.RECORD_SUPERSESSION_MISMATCH,
            "a later revision must exact-reference its immediate predecessor",
            "/supersedes_ref",
        )
    if supersedes is not None:
        if type(supersedes) is not dict:
            return _invalid_envelope("supersedes_ref must be an exact record reference", "/supersedes_ref")
        supersedes_problem = _validate_record_ref_object(supersedes, "/supersedes_ref")
        if supersedes_problem is not None:
            return supersedes_problem
        if (
            supersedes["record_type"] != envelope["record_type"]
            or supersedes["record_id"] != envelope["record_id"]
            or supersedes["record_revision"] != revision - 1
        ):
            return Diagnostic(
                DiagnosticCode.RECORD_SUPERSESSION_MISMATCH,
                "supersedes_ref must name the same record at the immediately preceding revision",
                "/supersedes_ref",
            )
    return None


def _validate_producer_context(value: Any, pointer: str) -> Diagnostic | None:
    required = {"producer", "role", "attempt_id", "implementation_ref", "environment_ref"}
    if type(value) is not dict or set(value) != required:
        return _invalid_envelope("producer_context has an invalid exact shape", pointer)
    producer = value["producer"]
    if type(producer) is not dict or set(producer) != {"actor_kind", "actor_id"}:
        return _invalid_envelope("producer identity has an invalid exact shape", _child(pointer, "producer"))
    if (
        type(producer["actor_kind"]) is not str
        or producer["actor_kind"] not in {"HUMAN", "AGENT", "MECHANICAL_SERVICE"}
    ):
        return _invalid_envelope(
            "producer actor_kind is invalid",
            _child(_child(pointer, "producer"), "actor_kind"),
        )
    if (
        type(producer["actor_id"]) is not str
        or not 3 <= len(producer["actor_id"]) <= 512
        or _NAMESPACED_ID_PATTERN.fullmatch(producer["actor_id"]) is None
    ):
        return _invalid_envelope(
            "producer actor_id is invalid",
            _child(_child(pointer, "producer"), "actor_id"),
        )
    if (
        type(value["role"]) is not str
        or not 1 <= len(value["role"]) <= 128
        or _ROLE_PATTERN.fullmatch(value["role"]) is None
    ):
        return _invalid_envelope("producer role is invalid", _child(pointer, "role"))
    if (
        type(value["attempt_id"]) is not str
        or not 3 <= len(value["attempt_id"]) <= 512
        or _NAMESPACED_ID_PATTERN.fullmatch(value["attempt_id"]) is None
    ):
        return _invalid_envelope("producer attempt_id is invalid", _child(pointer, "attempt_id"))
    for field in ("implementation_ref", "environment_ref"):
        if type(value[field]) is not dict:
            return _invalid_envelope(f"{field} must be an exact asset reference", _child(pointer, field))
        problem = _validate_asset_ref_object(value[field], _child(pointer, field))
        if problem is not None:
            return problem
    return None


def _resolve_json_pointer(document: Any, pointer: str) -> tuple[Any, bool]:
    current = document
    for encoded_token in pointer.split("/")[1:]:
        token = encoded_token.replace("~1", "/").replace("~0", "~")
        if type(current) is dict:
            if token not in current:
                return None, False
            current = current[token]
        elif type(current) is list:
            if token == "-" or not token.isascii() or not token.isdigit():
                return None, False
            if len(token) > 1 and token.startswith("0"):
                return None, False
            if not current:
                return None, False
            maximum_index = str(len(current) - 1)
            if len(token) > len(maximum_index) or (
                len(token) == len(maximum_index) and token > maximum_index
            ):
                return None, False
            index = int(token)
            current = current[index]
        else:
            return None, False
    return current, True


def _same_asset_identity(left: Any, right: Any) -> bool:
    if type(left) is not dict or type(right) is not dict:
        return False
    required_equal = all(left.get(field) == right.get(field) for field in _ASSET_REQUIRED)
    if not required_equal:
        return False
    return "schema_uri" not in right or left.get("schema_uri") == right["schema_uri"]


def _type_mismatch(message: str, pointer: str = "") -> Diagnostic:
    return Diagnostic(DiagnosticCode.REF_TYPE_MISMATCH, message, pointer)


def _invalid_envelope(message: str, pointer: str = "") -> Diagnostic:
    return Diagnostic(DiagnosticCode.RECORD_INVALID_ENVELOPE, message, pointer)


def _child(pointer: str, token: str) -> str:
    encoded = token.replace("~", "~0").replace("/", "~1")
    return f"{pointer}/{encoded}"
