"""Public contract-kernel primitives."""

from .canonical import (
    IJSON_MAX_INTEGER,
    IJSON_MIN_INTEGER,
    MAX_NESTING,
    PROFILE_ID,
    CanonicalValueIntegrityError,
    ParsedCanonicalValue,
    build_canonical_value,
    canonical_bytes,
    canonical_sha256,
    parse_canonical_json,
    record_content_hash,
    record_hash_projection_bytes,
)
from .diagnostics import Diagnostic, DiagnosticCode
from .references import (
    SuppliedAsset,
    raw_asset_sha256,
    resolve_exact_asset_ref,
    resolve_exact_component_ref,
    resolve_exact_record_ref,
    validate_immutable_envelope,
    validate_immutable_record,
)

__all__ = [
    "Diagnostic",
    "DiagnosticCode",
    "IJSON_MAX_INTEGER",
    "IJSON_MIN_INTEGER",
    "MAX_NESTING",
    "PROFILE_ID",
    "CanonicalValueIntegrityError",
    "ParsedCanonicalValue",
    "build_canonical_value",
    "canonical_bytes",
    "canonical_sha256",
    "parse_canonical_json",
    "record_content_hash",
    "record_hash_projection_bytes",
    "SuppliedAsset",
    "raw_asset_sha256",
    "resolve_exact_asset_ref",
    "resolve_exact_component_ref",
    "resolve_exact_record_ref",
    "validate_immutable_envelope",
    "validate_immutable_record",
]
