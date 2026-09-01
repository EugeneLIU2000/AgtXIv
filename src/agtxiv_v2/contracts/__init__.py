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
from .catalog_validation import (
    CatalogProfileConstraints,
    RawContractAssetBinding,
    build_catalog_profile_constraints,
    validate_m1_contract_requirement_set_intrinsic,
    validate_typed_terminal_result_catalog_constraints,
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
from .registry import (
    ContractSchemaRegistry,
    SchemaAssetBinding,
    build_schema_registry,
)
from .schema_validation import validate_immutable_record_payload
from .terminal_validation import validate_typed_terminal_result_intrinsic

__all__ = [
    "CatalogProfileConstraints",
    "RawContractAssetBinding",
    "build_catalog_profile_constraints",
    "validate_m1_contract_requirement_set_intrinsic",
    "validate_typed_terminal_result_catalog_constraints",
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
    "ContractSchemaRegistry",
    "SchemaAssetBinding",
    "build_schema_registry",
    "validate_immutable_record_payload",
    "validate_typed_terminal_result_intrinsic",
]
