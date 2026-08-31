from __future__ import annotations

import base64
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _add_local_src_package() -> Path:
    """Import the uninstalled slice without changing project-wide configuration."""

    repository_root = Path(__file__).resolve().parents[3]
    source_root = repository_root / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    return repository_root


ROOT = _add_local_src_package()

from agtxiv_v2.contracts import (  # noqa: E402
    MAX_NESTING,
    PROFILE_ID,
    CanonicalValueIntegrityError,
    Diagnostic,
    DiagnosticCode,
    ParsedCanonicalValue,
    build_canonical_value,
    canonical_bytes,
    canonical_sha256,
    parse_canonical_json,
    record_content_hash,
    record_hash_projection_bytes,
)
import agtxiv_v2.contracts.canonical as canonical_module  # noqa: E402


FIXTURE_DIR = (
    ROOT
    / "fixtures"
    / "v2-contract-kernel"
    / "canonicalization-profile"
    / "2.0.0-candidate.1"
)


HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ALLOWED_ORIGINS = {"CLEAN_MINIMAL_SUBSET", "INDEPENDENT_PROFILE_EDGE"}
POSITIVE_CANONICAL_KEYS = {
    "id",
    "kind",
    "operation",
    "origin",
    "input_utf8_base64",
    "expected_canonical_utf8_base64",
    "expected_sha256",
}
POSITIVE_RECORD_HASH_KEYS = {
    "id",
    "kind",
    "operation",
    "origin",
    "input_utf8_base64",
    "expected_projection_utf8_base64",
    "expected_content_hash",
}
NEGATIVE_KEYS = {
    "id",
    "kind",
    "operation",
    "origin",
    "input_utf8_base64",
    "expected_error_code",
}
EXPECTED_REFERENCE_COMMIT = "f86b98f4c98c4b5a356d6cd3ef067d402ff17cab"
EXPECTED_CLEAN_SOURCES = {
    "schemas/record-canonical-json-v1.profile.json": {
        "git_blob_id": "a180dcdd25d31bd112f82d347f96935543d06689",
        "sha256": "sha256:6445ca1b595f1894b4f5e52dd70cf6b2b2c9b4a7be02ee573754b8a7ee073b6e",
        "use": (
            "Primitive null, boolean, integer, ordered-array, object-order, UTF-8, "
            "newline, NFC, and SHA-256 behavior was used only to select a minimal "
            "compatibility subset."
        ),
    },
    "tools/validate_v2_paper_agentization.py": {
        "git_blob_id": "8bd0bcd7e9eb634f12c15c4318093f17acf6f84a",
        "sha256": "sha256:d6f297fc0cd13caf27a14a1d5cfc979196c291fdf7d257e1ae8009e0f6976566",
        "use": (
            "The clean committed integer-only canonicalization implementation was "
            "inspected only to identify shared primitive cases; no current "
            "working-tree bytes were read into a vector."
        ),
    },
}


def _strict_fixture_object(raw: bytes, label: str) -> dict[str, object]:
    parsed = parse_canonical_json(raw)
    if isinstance(parsed, Diagnostic):
        raise AssertionError(f"{label}: {parsed.code}: {parsed.message}")
    value = parsed.to_python()
    if type(value) is not dict:
        raise AssertionError(f"{label}: expected one JSON object")
    return value


def _validate_vector_row(row: dict[str, object], label: str) -> None:
    kind = row.get("kind")
    operation = row.get("operation")
    if kind == "positive" and operation == "canonicalize":
        expected_keys = POSITIVE_CANONICAL_KEYS
    elif kind == "positive" and operation == "record_content_hash":
        expected_keys = POSITIVE_RECORD_HASH_KEYS
    elif kind == "negative" and operation == "parse":
        expected_keys = NEGATIVE_KEYS
    else:
        raise AssertionError(f"{label}: invalid kind/operation pair: {kind!r}/{operation!r}")
    if set(row) != expected_keys:
        raise AssertionError(
            f"{label}: row keys differ; expected {sorted(expected_keys)}, got {sorted(row)}"
        )
    if row["origin"] not in ALLOWED_ORIGINS:
        raise AssertionError(f"{label}: invalid origin {row['origin']!r}")
    required_string_fields = expected_keys - {"kind", "operation"}
    if any(type(row[field]) is not str for field in required_string_fields):
        raise AssertionError(f"{label}: every vector field must be a JSON string")
    if type(kind) is not str or type(operation) is not str:
        raise AssertionError(f"{label}: kind and operation must be JSON strings")
    if not str(row["id"]).startswith(f"{kind}-"):
        raise AssertionError(f"{label}: id must start with {kind}-")
    base64.b64decode(row["input_utf8_base64"], validate=True)  # type: ignore[arg-type]
    if operation == "canonicalize":
        base64.b64decode(  # type: ignore[arg-type]
            row["expected_canonical_utf8_base64"], validate=True
        )
        if not HASH_PATTERN.fullmatch(row["expected_sha256"]):  # type: ignore[arg-type]
            raise AssertionError(f"{label}: invalid expected SHA-256")
    elif operation == "record_content_hash":
        base64.b64decode(  # type: ignore[arg-type]
            row["expected_projection_utf8_base64"], validate=True
        )
        if not HASH_PATTERN.fullmatch(row["expected_content_hash"]):  # type: ignore[arg-type]
            raise AssertionError(f"{label}: invalid expected content hash")
    elif row["expected_error_code"] not in {str(code) for code in DiagnosticCode}:
        raise AssertionError(f"{label}: unknown expected error code")


def _load_vectors() -> list[dict[str, object]]:
    raw_lines = (FIXTURE_DIR / "golden-vectors.jsonl").read_bytes().splitlines()
    if not raw_lines or any(not line for line in raw_lines):
        raise AssertionError("golden-vectors.jsonl must contain non-empty JSONL rows")
    rows: list[dict[str, object]] = []
    for index, raw_line in enumerate(raw_lines, start=1):
        label = f"golden-vectors.jsonl:{index}"
        row = _strict_fixture_object(raw_line, label)
        _validate_vector_row(row, label)
        rows.append(row)
    assert len({row["id"] for row in rows}) == len(rows)
    return rows


def _validate_provenance(provenance: dict[str, object], label: str) -> None:
    expected_keys = {
        "schema",
        "profile_id",
        "reference_commit",
        "clean_sources",
        "clean_minimal_subset_vector_ids",
        "independent_edge_vector_policy",
        "non_adoption",
    }
    if set(provenance) != expected_keys:
        raise AssertionError(f"{label}: unexpected top-level shape")
    scalar_string_keys = {
        "schema",
        "profile_id",
        "reference_commit",
        "independent_edge_vector_policy",
    }
    if any(type(provenance[key]) is not str for key in scalar_string_keys):
        raise AssertionError(f"{label}: scalar provenance fields must be JSON strings")
    if type(provenance["clean_sources"]) is not list:
        raise AssertionError(f"{label}: clean_sources must be an array")
    if type(provenance["clean_minimal_subset_vector_ids"]) is not list or any(
        type(item) is not str
        for item in provenance["clean_minimal_subset_vector_ids"]  # type: ignore[union-attr]
    ):
        raise AssertionError(f"{label}: clean vector ids must be a string array")
    clean_vector_ids = provenance["clean_minimal_subset_vector_ids"]
    if len(clean_vector_ids) != len(set(clean_vector_ids)):  # type: ignore[arg-type]
        raise AssertionError(f"{label}: clean vector ids must be unique")
    if type(provenance["non_adoption"]) is not list or any(
        type(item) is not str for item in provenance["non_adoption"]  # type: ignore[union-attr]
    ):
        raise AssertionError(f"{label}: non_adoption must be a string array")
    source_keys = {"path", "git_blob_id", "sha256", "use"}
    clean_source_paths: set[str] = set()
    for source in provenance["clean_sources"]:  # type: ignore[union-attr]
        if (
            type(source) is not dict
            or set(source) != source_keys
            or any(type(source[key]) is not str for key in source_keys)
        ):
            raise AssertionError(f"{label}: clean source has an unexpected shape")
        if source["path"] in clean_source_paths:
            raise AssertionError(f"{label}: clean source paths must be unique")
        clean_source_paths.add(source["path"])


def _load_provenance() -> dict[str, object]:
    provenance = _strict_fixture_object(
        (FIXTURE_DIR / "provenance.json").read_bytes(),
        "provenance.json",
    )
    _validate_provenance(provenance, "provenance.json")
    return provenance


VECTORS = _load_vectors()
POSITIVE_VECTORS = [row for row in VECTORS if row["kind"] == "positive"]
NEGATIVE_VECTORS = [row for row in VECTORS if row["kind"] == "negative"]
PROVENANCE = _load_provenance()


def _raw(row: dict[str, object]) -> bytes:
    return base64.b64decode(str(row["input_utf8_base64"]), validate=True)


@pytest.mark.parametrize("row", POSITIVE_VECTORS, ids=lambda row: str(row["id"]))
def test_positive_golden_vectors(row: dict[str, object]) -> None:
    parsed = parse_canonical_json(_raw(row))
    assert isinstance(parsed, ParsedCanonicalValue), parsed

    if row["operation"] == "canonicalize":
        expected = base64.b64decode(
            str(row["expected_canonical_utf8_base64"]), validate=True
        )
        assert canonical_bytes(parsed) == expected
        assert canonical_sha256(parsed) == row["expected_sha256"]
    else:
        assert row["operation"] == "record_content_hash"
        expected_projection = base64.b64decode(
            str(row["expected_projection_utf8_base64"]), validate=True
        )
        assert record_hash_projection_bytes(parsed) == expected_projection
        assert record_content_hash(parsed) == row["expected_content_hash"]


@pytest.mark.parametrize("row", NEGATIVE_VECTORS, ids=lambda row: str(row["id"]))
def test_negative_golden_vectors_have_stable_codes(row: dict[str, object]) -> None:
    result = parse_canonical_json(_raw(row))
    assert isinstance(result, Diagnostic)
    assert str(result.code) == row["expected_error_code"]


def test_mandatory_vector_classes_are_explicit() -> None:
    required_ids = {
        "positive-empty-array",
        "positive-empty-object",
        "positive-null",
        "positive-boolean-true",
        "positive-boolean-false",
        "positive-integer-min",
        "positive-integer-max",
        "positive-integer-negative",
        "positive-integer-zero",
        "positive-integer-multidigit",
        "positive-ordered-array",
        "positive-scalar-key-order",
        "positive-exact-escaping",
        "positive-raw-nonascii",
        "positive-newline-normalization",
        "positive-nfc-normalization",
        "positive-record-hash-projection",
        "negative-bom",
        "negative-malformed-utf8",
        "negative-trailing-data",
        "negative-duplicate-decoded-key",
        "negative-post-nfc-key-collision",
        "negative-unpaired-high-surrogate",
        "negative-minus-zero",
        "negative-leading-zero",
        "negative-decimal",
        "negative-exponent",
        "negative-integer-below-range",
        "negative-integer-above-range",
    }
    assert required_ids <= {str(row["id"]) for row in VECTORS}


def test_every_vector_is_deterministic_across_repeated_runs() -> None:
    for row in VECTORS:
        observations: list[object] = []
        for _ in range(10):
            result = parse_canonical_json(_raw(row))
            if isinstance(result, Diagnostic):
                observations.append(result.to_dict())
            elif row["operation"] == "record_content_hash":
                observations.append(
                    (record_hash_projection_bytes(result), record_content_hash(result))
                )
            else:
                observations.append((canonical_bytes(result), canonical_sha256(result)))
        assert all(observation == observations[0] for observation in observations), row["id"]


def test_raw_parser_is_required_at_untrusted_json_boundary() -> None:
    host_value = json.loads('{"a": 1, "a": 2}')
    assert host_value == {"a": 2}

    with pytest.raises(TypeError, match="ParsedCanonicalValue"):
        canonical_bytes(host_value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ParsedCanonicalValue"):
        record_content_hash(host_value)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="raw bytes"):
        parse_canonical_json('{"a": 1}')  # type: ignore[arg-type]

    raw_result = parse_canonical_json(b'{"a": 1, "a": 2}')
    assert isinstance(raw_result, Diagnostic)
    assert raw_result.code is DiagnosticCode.DUPLICATE_KEY


def test_programmatic_builder_is_an_explicit_separate_boundary() -> None:
    built = build_canonical_value({"z": [1, True, None], "e\u0301": "a\r\nb\rc"})
    assert isinstance(built, ParsedCanonicalValue)
    assert canonical_bytes(built) == '{"z":[1,true,null],"é":"a\\nb\\nc"}'.encode()

    host_float = build_canonical_value({"value": 1.0})
    assert isinstance(host_float, Diagnostic)
    assert host_float.code is DiagnosticCode.UNSUPPORTED_PROGRAMMATIC_TYPE

    normalized_collision = build_canonical_value({"é": 1, "e\u0301": 2})
    assert isinstance(normalized_collision, Diagnostic)
    assert normalized_collision.code is DiagnosticCode.NORMALIZED_KEY_COLLISION


def test_programmatic_builder_rejects_non_json_keys_cycles_and_unsafe_integers() -> None:
    non_string_key = build_canonical_value({1: "value"})
    assert isinstance(non_string_key, Diagnostic)
    assert non_string_key.code is DiagnosticCode.NON_STRING_OBJECT_KEY

    cyclic: list[object] = []
    cyclic.append(cyclic)
    cycle_result = build_canonical_value(cyclic)
    assert isinstance(cycle_result, Diagnostic)
    assert cycle_result.code is DiagnosticCode.CYCLIC_PROGRAMMATIC_VALUE

    too_large = build_canonical_value(9_007_199_254_740_992)
    assert isinstance(too_large, Diagnostic)
    assert too_large.code is DiagnosticCode.INTEGER_OUT_OF_RANGE


@pytest.mark.parametrize("sign", [b"", b"-"])
def test_arbitrarily_long_integer_is_rejected_before_host_integer_conversion(
    sign: bytes,
) -> None:
    result = parse_canonical_json(sign + (b"9" * 10_000))
    assert isinstance(result, Diagnostic)
    assert result.code is DiagnosticCode.INTEGER_OUT_OF_RANGE


def test_parser_and_programmatic_builder_share_the_same_nesting_limit() -> None:
    accepted_raw = (b"[" * MAX_NESTING) + b"0" + (b"]" * MAX_NESTING)
    accepted_programmatic: object = 0
    for _ in range(MAX_NESTING):
        accepted_programmatic = [accepted_programmatic]
    assert isinstance(parse_canonical_json(accepted_raw), ParsedCanonicalValue)
    assert isinstance(build_canonical_value(accepted_programmatic), ParsedCanonicalValue)

    rejected_raw = (b"[" * (MAX_NESTING + 1)) + b"0" + (
        b"]" * (MAX_NESTING + 1)
    )
    rejected_programmatic: object = 0
    for _ in range(MAX_NESTING + 1):
        rejected_programmatic = [rejected_programmatic]
    for result in (
        parse_canonical_json(rejected_raw),
        build_canonical_value(rejected_programmatic),
    ):
        assert isinstance(result, Diagnostic)
        assert result.code is DiagnosticCode.NESTING_TOO_DEEP


def test_parsed_value_cannot_be_constructed_directly() -> None:
    with pytest.raises(TypeError, match="created only"):
        ParsedCanonicalValue({}, _token=object())


def test_parsed_value_blocks_ordinary_assignment_and_deletion() -> None:
    parsed = parse_canonical_json(b'{"value":1}')
    assert isinstance(parsed, ParsedCanonicalValue)
    with pytest.raises(AttributeError, match="immutable"):
        parsed._ParsedCanonicalValue__node = 2  # type: ignore[attr-defined]
    with pytest.raises(AttributeError, match="immutable"):
        del parsed._ParsedCanonicalValue__node  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "invalid_node",
    [
        {"host": "dict"},
        9_007_199_254_740_992,
        "e\u0301",
        canonical_module._CanonicalObject((("z", 1), ("a", 2))),
        canonical_module._CanonicalObject((("a", 1), ("a", 2))),
    ],
    ids=["type", "integer-range", "normalization", "key-order", "duplicate-key"],
)
def test_private_constructor_token_does_not_bypass_recursive_integrity_validation(
    invalid_node: object,
) -> None:
    with pytest.raises(CanonicalValueIntegrityError) as raised:
        ParsedCanonicalValue(
            invalid_node,
            _token=canonical_module._CONSTRUCTION_TOKEN,
        )
    assert raised.value.diagnostic.code is DiagnosticCode.INVALID_INTERNAL_VALUE


def test_private_constructor_token_cannot_bypass_internal_nesting_limit() -> None:
    invalid_node: object = 0
    for _ in range(MAX_NESTING + 1):
        invalid_node = (invalid_node,)
    with pytest.raises(CanonicalValueIntegrityError) as raised:
        ParsedCanonicalValue(
            invalid_node,
            _token=canonical_module._CONSTRUCTION_TOKEN,
        )
    assert raised.value.diagnostic.code is DiagnosticCode.INVALID_INTERNAL_VALUE


def test_every_consumer_revalidates_an_object_setattr_mutation_fail_closed() -> None:
    parsed = parse_canonical_json(b'{"value":1}')
    assert isinstance(parsed, ParsedCanonicalValue)

    object.__setattr__(
        parsed,
        "_ParsedCanonicalValue__node",
        canonical_module._CanonicalObject((("value", 9_007_199_254_740_992),)),
    )
    consumers = (
        lambda: canonical_bytes(parsed),
        lambda: parsed.to_python(),
        lambda: build_canonical_value(parsed),
    )
    for consume in consumers:
        with pytest.raises(CanonicalValueIntegrityError) as raised:
            consume()
        assert raised.value.diagnostic.code is DiagnosticCode.INVALID_INTERNAL_VALUE


def test_to_python_returns_a_detached_value() -> None:
    parsed = parse_canonical_json(b'{"items":[1,2]}')
    assert isinstance(parsed, ParsedCanonicalValue)
    detached = parsed.to_python()
    detached["items"].append(3)
    assert canonical_bytes(parsed) == b'{"items":[1,2]}'


@pytest.mark.parametrize(
    ("raw", "expected_code"),
    [
        (b"+1", DiagnosticCode.UNSUPPORTED_NUMBER),
        (b"NaN", DiagnosticCode.UNSUPPORTED_NUMBER),
        (b"Infinity", DiagnosticCode.UNSUPPORTED_NUMBER),
        ("-٢".encode("utf-8"), DiagnosticCode.UNSUPPORTED_NUMBER),
        (b'"\\uD800x"', DiagnosticCode.UNPAIRED_SURROGATE),
        (b'{"a":1,}', DiagnosticCode.INVALID_JSON),
        (b"[1,]", DiagnosticCode.INVALID_JSON),
    ],
)
def test_additional_parser_edges(raw: bytes, expected_code: DiagnosticCode) -> None:
    result = parse_canonical_json(raw)
    assert isinstance(result, Diagnostic)
    assert result.code is expected_code


def test_record_hash_excludes_only_outer_content_hash() -> None:
    first = parse_canonical_json(
        b'{"envelope":{},"payload":{"content_hash":"nested-a"},"content_hash":"outer-a"}'
    )
    second = parse_canonical_json(
        b'{"envelope":{},"payload":{"content_hash":"nested-a"},"content_hash":"outer-b"}'
    )
    changed_nested = parse_canonical_json(
        b'{"envelope":{},"payload":{"content_hash":"nested-b"},"content_hash":"outer-a"}'
    )
    assert all(
        isinstance(value, ParsedCanonicalValue) for value in (first, second, changed_nested)
    )
    assert record_content_hash(first) == record_content_hash(second)  # type: ignore[arg-type]
    assert record_content_hash(first) != record_content_hash(changed_nested)  # type: ignore[arg-type]


def test_record_hash_rejects_uncommitted_outer_metadata() -> None:
    record = parse_canonical_json(b'{"envelope":{},"payload":{},"extra":"not-hashed"}')
    assert isinstance(record, ParsedCanonicalValue)
    result = record_content_hash(record)
    assert isinstance(result, Diagnostic)
    assert result.code is DiagnosticCode.INVALID_RECORD_SHAPE


def test_profile_identity_is_single_and_does_not_reuse_the_clean_v1_path() -> None:
    assert PROFILE_ID == "agtxiv.record-canonical-json/2.0.0-candidate.1"
    assert PROVENANCE["profile_id"] == PROFILE_ID
    assert FIXTURE_DIR.name == "2.0.0-candidate.1"
    legacy_fixture_dir = (
        ROOT
        / "fixtures"
        / "v2-contract-kernel"
        / "canonicalization-profile"
        / "1.0.0"
    )
    assert not legacy_fixture_dir.exists() or not any(legacy_fixture_dir.iterdir())


def test_fixture_loader_rejects_duplicates_extra_fields_and_invalid_origin() -> None:
    with pytest.raises(AssertionError, match="DUPLICATE_KEY"):
        _strict_fixture_object(b'{"id":"first","id":"second"}', "duplicate")

    valid_row = dict(VECTORS[0])
    with_extra = {**valid_row, "unexpected": "field"}
    with pytest.raises(AssertionError, match="row keys differ"):
        _validate_vector_row(with_extra, "extra-field")

    invalid_origin = {**valid_row, "origin": "DIRTY_WIP"}
    with pytest.raises(AssertionError, match="invalid origin"):
        _validate_vector_row(invalid_origin, "invalid-origin")

    invalid_operation = {**valid_row, "operation": "unknown"}
    with pytest.raises(AssertionError, match="invalid kind/operation"):
        _validate_vector_row(invalid_operation, "invalid-operation")


def test_provenance_loader_rejects_duplicate_and_non_exact_shapes() -> None:
    with pytest.raises(AssertionError, match="DUPLICATE_KEY"):
        _strict_fixture_object(b'{"schema":"one","schema":"two"}', "duplicate")

    with_extra = {**PROVENANCE, "unexpected": "field"}
    with pytest.raises(AssertionError, match="top-level shape"):
        _validate_provenance(with_extra, "extra-field")

    malformed_source = dict(PROVENANCE)
    malformed_source["clean_sources"] = [
        {"path": "source", "git_blob_id": "blob", "sha256": "hash"}
    ]
    with pytest.raises(AssertionError, match="clean source"):
        _validate_provenance(malformed_source, "malformed-source")

    duplicate_source = dict(PROVENANCE)
    duplicate_source["clean_sources"] = [
        *PROVENANCE["clean_sources"],  # type: ignore[union-attr]
        PROVENANCE["clean_sources"][0],  # type: ignore[index]
    ]
    with pytest.raises(AssertionError, match="source paths must be unique"):
        _validate_provenance(duplicate_source, "duplicate-source")

    duplicate_vector_id = dict(PROVENANCE)
    duplicate_vector_id["clean_minimal_subset_vector_ids"] = [
        *PROVENANCE["clean_minimal_subset_vector_ids"],  # type: ignore[union-attr]
        PROVENANCE["clean_minimal_subset_vector_ids"][0],  # type: ignore[index]
    ]
    with pytest.raises(AssertionError, match="vector ids must be unique"):
        _validate_provenance(duplicate_vector_id, "duplicate-vector-id")


def test_golden_provenance_is_exact_clean_minimal_and_disjoint() -> None:
    assert PROVENANCE["schema"] == "agtxiv.canonical-golden-provenance/1.0.0"
    assert PROVENANCE["reference_commit"] == EXPECTED_REFERENCE_COMMIT
    assert "dirty" in " ".join(PROVENANCE["non_adoption"]).lower()  # type: ignore[arg-type]

    clean_ids = set(PROVENANCE["clean_minimal_subset_vector_ids"])  # type: ignore[arg-type]
    vector_clean_ids = {
        row["id"] for row in VECTORS if row["origin"] == "CLEAN_MINIMAL_SUBSET"
    }
    assert clean_ids == vector_clean_ids
    assert clean_ids.isdisjoint(
        {row["id"] for row in VECTORS if row["origin"] == "INDEPENDENT_PROFILE_EDGE"}
    )

    actual_sources = {
        source["path"]: {
            "git_blob_id": source["git_blob_id"],
            "sha256": source["sha256"],
            "use": source["use"],
        }
        for source in PROVENANCE["clean_sources"]  # type: ignore[union-attr]
    }
    assert actual_sources == EXPECTED_CLEAN_SOURCES


def test_provenance_clean_bindings_recompute_from_git_when_available() -> None:
    if not (ROOT / ".git").exists() or shutil.which("git") is None:
        pytest.skip("Git checkout is unavailable; exact static bindings remain tested")

    for path, expected in EXPECTED_CLEAN_SOURCES.items():
        revision = f"{EXPECTED_REFERENCE_COMMIT}:{path}"
        blob_id = subprocess.check_output(
            ["git", "rev-parse", revision], cwd=ROOT, text=True
        ).strip()
        source_bytes = subprocess.check_output(["git", "show", revision], cwd=ROOT)
        assert blob_id == expected["git_blob_id"]
        assert "sha256:" + hashlib.sha256(source_bytes).hexdigest() == expected["sha256"]
