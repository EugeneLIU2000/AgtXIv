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
]
