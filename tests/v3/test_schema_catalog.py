"""Whole-catalog structural checks, explicitly not scientific acceptance.

Every registered record receives a bounded, deterministic SYNTHETIC example.
References are invented structural placeholders, not a closed evidence graph.
These tests neither execute experiments nor authenticate reviewers or proofs.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import shutil
import sys

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agtxiv_v3.contracts import ContractError, SchemaBundle, content_hash  # noqa: E402

DIRECTORY = ROOT / "schema v0.0"
MANIFEST = json.loads((DIRECTORY / "manifest.json").read_text())
RECORD_ENTRIES = tuple(entry for entry in MANIFEST["schemas"] if entry["record_type"] is not None)
COMMON = json.loads((DIRECTORY / "common.schema.json").read_text())
MISSING = object()
SYNTHETIC_TEXT = "SYNTHETIC structural fixture; no scientific approval."


@pytest.fixture(scope="module")
def bundle():
    return SchemaBundle(DIRECTORY)


def walk(value, path=()):
    if isinstance(value, dict):
        yield path, value
        for key, item in value.items():
            yield from walk(item, (*path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, (*path, index))


class StructuralExample:
    """Materialize this finite schema vocabulary; fail on unsupported shapes.

    This is a test-fixture constructor, not a production schema implementation.
    Every result is checked by the independent Draft 2020-12 implementation.
    Fixed recursion and array bounds prevent silent/unbounded search for values.
    """

    def __init__(self, bundle):
        self.bundle = bundle
        self.serial = 0

    def validator(self, schema):
        return Draft202012Validator(schema, registry=self.bundle.registry, format_checker=FormatChecker())

    def valid(self, value, schema):
        return value is not MISSING and self.validator(schema).is_valid(value)

    def make(self, schema, value=MISSING, depth=0):
        assert depth < 60, "Fixture schema recursion exceeded its fixed budget"
        value = copy.deepcopy(value) if value is not MISSING else MISSING
        if not schema and value is MISSING:
            return SYNTHETIC_TEXT
        if "$ref" in schema:
            resolved = self.bundle.registry.resolver().lookup(schema["$ref"]).contents
            value = self.make(resolved, value, depth + 1)
        if "const" in schema:
            value = copy.deepcopy(schema["const"])
        elif "enum" in schema and (value is MISSING or value not in schema["enum"]):
            value = copy.deepcopy(schema["enum"][0])
        choices = schema.get("anyOf", schema.get("oneOf"))
        if choices is not None and not any(self.valid(value, branch) for branch in choices):
            # A null optional linkage is preferable to inventing a history.
            ordered = sorted(choices, key=lambda branch: branch.get("type") != "null")
            failures = []
            for branch in ordered:
                try:
                    proposed = self.make(branch, depth=depth + 1)
                    if self.valid(proposed, branch):
                        value = proposed
                        break
                except AssertionError as error:
                    failures.append(str(error))
            else:
                raise AssertionError(f"No supported branch in {choices}: {failures}")

        kind = schema.get("type")
        if kind == "object" or "properties" in schema:
            value = {} if not isinstance(value, dict) else value
            required = set(schema.get("required", []))
            for key, child in schema.get("properties", {}).items():
                if key in value or key in required:
                    value[key] = self.make(child, value.get(key, MISSING), depth + 1)
        elif kind == "array" or "contains" in schema or "minItems" in schema or "maxItems" in schema:
            value = [] if not isinstance(value, list) else value
            minimum = schema.get("minItems", 0)
            assert minimum <= 100, "Fixture array limit exceeded"
            items = schema.get("items", {})
            while len(value) < minimum:
                if schema.get("uniqueItems") and "enum" in items:
                    available = [item for item in items["enum"] if item not in value]
                    assert available, "Cannot meet uniqueItems with this enum"
                    value.append(copy.deepcopy(available[0]))
                else:
                    value.append(self.make(items, depth=depth + 1))
            if items:
                value = [self.make(items, item, depth + 1) for item in value]
            if "contains" in schema and not any(self.valid(item, schema["contains"]) for item in value):
                assert len(value) < 100, "Fixture contains limit exceeded"
                value.append(self.make(schema["contains"], depth=depth + 1))
            if "maxItems" in schema:
                value = value[:schema["maxItems"]]
        elif kind == "string" and not self.valid(value, schema):
            pattern = schema.get("pattern", "")
            if pattern == "^sha256:[0-9a-f]{64}$":
                value = "sha256:" + "0" * 64
            elif pattern.startswith("^[0-9a-f]{40}"):
                value = "0" * 40
            elif pattern.startswith("^[a-z][a-z0-9._-]*:"):
                self.serial += 1
                value = f"synthetic:item-{self.serial}"
            elif schema.get("format") == "date-time":
                value = "2026-09-07T00:00:00Z"
            elif schema.get("format") == "uri":
                value = "https://example.invalid/synthetic"
            elif pattern.startswith("^(?!/)"):
                value = "synthetic/source.tex"
            else:
                assert not pattern, f"Unsupported fixture pattern: {pattern}"
                value = SYNTHETIC_TEXT
            assert len(value) >= schema.get("minLength", 0)
            assert len(value) <= schema.get("maxLength", len(value))
        elif kind == "integer" and not self.valid(value, schema):
            value = schema.get("minimum", 0)
        elif kind == "boolean" and not self.valid(value, schema):
            value = False
        elif kind == "null":
            value = None

        for conjunct in schema.get("allOf", []):
            value = self.make(conjunct, value, depth + 1)
        if "if" in schema:
            consequence = schema.get("then") if self.valid(value, schema["if"]) else schema.get("else")
            if consequence is not None:
                value = self.make(consequence, value, depth + 1)
        assert value is not MISSING, f"Unsupported fixture shape: {schema}"
        return value

    def record(self, record_type):
        schema = self.bundle.by_type[record_type]
        record = self.make(schema)
        # Partial conditional schemas may raise an array minimum without
        # repeating its items definition. Reapply the full shape to those new
        # entries, with a fixed budget and a final independent validation.
        for _ in range(3):
            record = self.make(schema, record)
        record["data_class"] = "SYNTHETIC"
        record["schema_bundle_hash"] = self.bundle.bundle_hash
        record["record_id"] = "synthetic:" + record_type.removeprefix("agtxiv.v3.").split("/")[0]
        record["content_hash"] = content_hash(record)
        errors = list(self.validator(schema).iter_errors(record))
        assert not errors, "\n".join(f"{list(error.absolute_path)}: {error.message}" for error in errors)
        return record


@pytest.fixture(scope="module")
def examples(bundle):
    generator = StructuralExample(bundle)
    return {record_type: generator.record(record_type) for record_type in bundle.by_type}


def test_manifest_catalog_and_actual_schema_files_are_exhaustive(bundle):
    catalog = json.loads((DIRECTORY / "catalog.json").read_text())
    schemas = bundle.manifest["schemas"]
    assert bundle.manifest["record_count"] == len(bundle.by_type) == len(catalog["records"])
    assert len(bundle.by_type) >= 63, "The full V3 catalog must not shrink to a small demonstration"
    assert len({entry["path"] for entry in schemas}) == len(schemas)
    assert {entry["path"] for entry in schemas} == {path.name for path in DIRECTORY.glob("*.schema.json")}
    registered = {entry["record_type"]: entry["path"] for entry in schemas if entry["record_type"]}
    assert {entry["record_type"]: entry["schema"] for entry in catalog["records"]} == registered
    core = {"scientific-claim", "math-claim", "upstream-import", "formal-check", "axis-assessment", "release-audit", "admission-decision", "work-completion"}
    assert all(f"agtxiv.v3.{name}/0.0.0" in registered for name in core)


def test_every_schema_and_reference_is_valid_offline(bundle):
    count = 0
    for schema in bundle.schemas.values():
        Draft202012Validator.check_schema(schema)
        for _, item in walk(schema):
            if "$ref" in item:
                result = bundle.registry.resolver().lookup(item["$ref"])
                assert isinstance(result.contents, dict)
                count += 1
    assert count > 500
    union = next(schema for uri, schema in bundle.schemas.items() if uri.endswith("/record.schema.json"))
    assert {branch["$ref"] for branch in union["oneOf"]} == {schema["$id"] for schema in bundle.by_type.values()}


def test_objects_are_closed_and_all_record_discriminators_are_registered(bundle):
    allowed = set(bundle.by_type)
    common = next(schema for uri, schema in bundle.schemas.items() if uri.endswith("/common.schema.json"))
    assert set(common["$defs"]["RecordRef"]["properties"]["record_type"]["enum"]) == allowed
    for schema in bundle.schemas.values():
        for path, item in walk(schema):
            if item.get("type") == "object":
                assert item.get("additionalProperties") is False, (schema["$id"], path)
                assert set(item.get("required", [])) <= set(item.get("properties", {})), (schema["$id"], path)
                assert len(item.get("required", [])) == len(set(item.get("required", [])))
            if path and path[-1] == "record_type":
                declarations = [item["const"]] if "const" in item else item.get("enum", [])
                assert declarations and set(declarations) <= allowed, (schema["$id"], path)


def test_json_contracts_contain_no_chinese_characters():
    # Parse before searching so escaped Chinese text cannot evade this check.
    chinese = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]")
    for path in DIRECTORY.glob("*.json"):
        text = json.dumps(json.loads(path.read_text()), ensure_ascii=False)
        assert not chinese.search(text), f"Non-English JSON contract text in {path.name}"


def documented_tables(path):
    result = {}
    heading = None
    for line in path.read_text().splitlines():
        if line.startswith(("## ", "### ")):
            heading = line.lstrip("# ")
            bilingual = re.search(r"（([A-Za-z][A-Za-z0-9]*)）$", heading)
            if bilingual:
                heading = bilingual.group(1)
        elif line.startswith("| `"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            assert len(cells) == 4, (path, line)
            result.setdefault(heading, []).append(cells)
    return result


def test_english_and_chinese_tables_match_each_schema_field(bundle):
    english = documented_tables(DIRECTORY / "SCHEMA.md")
    chinese = documented_tables(DIRECTORY / "SCHEMA.zh-CN.md")
    common = next(schema for uri, schema in bundle.schemas.items() if uri.endswith("/common.schema.json"))
    expected = {name: schema for name, schema in common["$defs"].items()}
    expected.update({schema["title"]: schema["properties"]["payload"] for schema in bundle.by_type.values()})
    required_words = {"yes": "是", "no": "否"}
    for title, schema in expected.items():
        assert title in english and title in chinese, title
        en_rows, zh_rows = english[title], chinese[title]
        assert [row[0] for row in en_rows] == [row[0] for row in zh_rows], title
        assert {row[0] for row in en_rows} == {f"`{field}`" for field in schema["properties"]}, title
        for en, zh in zip(en_rows, zh_rows):
            assert en[1] == zh[1], (title, en[0], "Type or enum translation drift")
            assert required_words[en[2]] == zh[2], (title, en[0], "Required-field drift")
            assert (en[2] == "yes") == (en[0].strip("`") in schema.get("required", []))
            assert en[3] and zh[3], (title, en[0], "Missing field explanation")
    en_envelope = english["Record envelope"]
    zh_envelope = chinese["记录通用封套"]
    assert [row[:2] for row in en_envelope] == [row[:2] for row in zh_envelope]
    envelope_fields = set(next(iter(bundle.by_type.values()))["properties"])
    assert {row[0].strip("`") for row in en_envelope} == envelope_fields
    assert all(required_words[en[2]] == zh[2] for en, zh in zip(en_envelope, zh_envelope))


@pytest.mark.parametrize("name", tuple(COMMON["$defs"]))
def test_shared_values_accept_minimal_examples_and_reject_missing_or_unknown_fields(bundle, name):
    generator = StructuralExample(bundle)
    schema = bundle.registry.resolver().lookup(COMMON["$id"] + "#/$defs/" + name).contents
    value = generator.make(schema)
    for _ in range(3):
        value = generator.make(schema, value)
    validator = generator.validator(schema)
    validator.validate(value)
    unknown = {**value, "undeclared_fixture_field": "must fail"}
    assert not validator.is_valid(unknown)
    for field in schema["required"]:
        missing = {key: item for key, item in value.items() if key != field}
        assert not validator.is_valid(missing), (name, field)


@pytest.mark.parametrize("entry", RECORD_ENTRIES, ids=lambda entry: entry["path"])
def test_each_registered_type_accepts_a_synthetic_structural_example(bundle, examples, entry):
    record = examples[entry["record_type"]]
    assert record["data_class"] == "SYNTHETIC"
    assert record["record_id"].startswith("synthetic:")
    assert bundle.validate_record(record) == ()
    union = next(schema for uri, schema in bundle.schemas.items() if uri.endswith("/record.schema.json"))
    Draft202012Validator(union, registry=bundle.registry, format_checker=FormatChecker()).validate(record)


@pytest.mark.parametrize("entry", RECORD_ENTRIES, ids=lambda entry: entry["path"])
def test_every_record_rejects_unknown_fields_at_each_populated_object(bundle, examples, entry):
    original = examples[entry["record_type"]]
    for path, _ in walk(original):
        mutated = copy.deepcopy(original)
        target = mutated
        for key in path:
            target = target[key]
        target["undeclared_fixture_field"] = "must fail closed"
        mutated["content_hash"] = content_hash(mutated)
        assert any(issue.code == "SCHEMA" for issue in bundle.validate_record(mutated)), (entry["path"], path)


@pytest.mark.parametrize("entry", RECORD_ENTRIES, ids=lambda entry: entry["path"])
def test_every_record_rejects_tampered_hash_and_unknown_discriminator(bundle, examples, entry):
    original = examples[entry["record_type"]]
    tampered = copy.deepcopy(original)
    tampered["content_hash"] = "sha256:" + "f" * 64
    assert any(issue.code == "RECORD_HASH_MISMATCH" for issue in bundle.validate_record(tampered))
    mutated = copy.deepcopy(original)
    mutated["record_type"] = "agtxiv.v3.unregistered/0.0.0"
    mutated["content_hash"] = content_hash(mutated)
    assert {issue.code for issue in bundle.validate_record(mutated)} == {"UNKNOWN_RECORD_TYPE"}
    mutated = copy.deepcopy(original)
    mutated["schema_bundle_hash"] = "sha256:" + "f" * 64
    mutated["content_hash"] = content_hash(mutated)
    assert any(issue.code == "SCHEMA_BUNDLE_MISMATCH" for issue in bundle.validate_record(mutated))


@pytest.mark.parametrize("entry", RECORD_ENTRIES, ids=lambda entry: entry["path"])
def test_every_record_requires_its_envelope_payload_and_exact_discriminator(bundle, examples, entry):
    original = examples[entry["record_type"]]
    schema = bundle.by_type[entry["record_type"]]
    validator = bundle.validators[entry["record_type"]]
    for field in schema["required"]:
        missing = copy.deepcopy(original)
        del missing[field]
        assert not validator.is_valid(missing), (entry["path"], field)
    for field in schema["properties"]["payload"]["required"]:
        missing = copy.deepcopy(original)
        del missing["payload"][field]
        assert not validator.is_valid(missing), (entry["path"], "payload", field)
    wrong = copy.deepcopy(original)
    wrong["record_type"] = next(record_type for record_type in bundle.by_type if record_type != entry["record_type"])
    assert not validator.is_valid(wrong)


def variant(bundle, examples, name, updates):
    record_type = f"agtxiv.v3.{name}/0.0.0"
    value = copy.deepcopy(examples[record_type])
    value["payload"].update(updates)
    generator = StructuralExample(bundle)
    for _ in range(3):
        value = generator.make(bundle.by_type[record_type], value)
    value["content_hash"] = content_hash(value)
    assert not bundle.validate_record(value)
    return value


@pytest.mark.parametrize("locator", ["RAW_TEXT_BYTES", "TRANSFORMED_TEXT", "PDF_REGION"])
def test_source_locator_variants_cannot_mix_text_offsets_and_pdf_regions(bundle, examples, locator):
    record = variant(bundle, examples, "source-span", {"locator_kind": locator})
    payload = record["payload"]
    if locator == "PDF_REGION":
        assert payload["byte_start"] is payload["byte_end"] is payload["span_sha256"] is None
        assert payload["pdf_region"] is not None
        assert payload["artifact"]["media_type"] == "application/pdf"
        payload["byte_start"] = 0
    else:
        assert isinstance(payload["byte_start"], int)
        assert payload["pdf_region"] is None
        assert (payload["transformation_ref"] is not None) == (locator == "TRANSFORMED_TEXT")
        payload["span_sha256"] = None
    record["content_hash"] = content_hash(record)
    assert any(issue.code == "SCHEMA" for issue in bundle.validate_record(record))


def test_conditional_success_requires_the_specific_structural_evidence(bundle, examples):
    checked = variant(bundle, examples, "formal-check", {"outcome": "KERNEL_CHECKED"})
    assert checked["payload"]["built_declarations"]
    assert all(declaration["is_axiom"] is False for declaration in checked["payload"]["built_declarations"])
    for change in [{"built_declarations": []}, {"exit_code": 1}, {"placeholder_findings": ["synthetic unresolved placeholder"]}]:
        mutated = copy.deepcopy(checked)
        mutated["payload"].update(change)
        mutated["content_hash"] = content_hash(mutated)
        assert any(issue.code == "SCHEMA" for issue in bundle.validate_record(mutated))
    imported = variant(bundle, examples, "upstream-import", {"outcome": "STRUCTURALLY_IMPORTED"})
    for field in ["ledger", "graph", "identity_map", "reported_states"]:
        mutated = copy.deepcopy(imported)
        mutated["payload"][field] = None
        mutated["content_hash"] = content_hash(mutated)
        assert any(issue.code == "SCHEMA" for issue in bundle.validate_record(mutated))


def test_supported_and_counterevidence_assessments_cannot_be_deferred_or_evidence_free(bundle, examples):
    for result, evidence_field in [("SUPPORTED", "support_refs"), ("COUNTEREVIDENCE", "counterevidence_refs")]:
        record = variant(bundle, examples, "axis-assessment", {"result": result})
        assert record["payload"]["execution"] == "COMPLETED"
        assert record["payload"]["applicability"] == "APPLICABLE"
        for change in [{evidence_field: []}, {"execution": "DEFERRED"}, {"applicability": "NOT_APPLICABLE"}]:
            mutated = copy.deepcopy(record)
            mutated["payload"].update(change)
            mutated["content_hash"] = content_hash(mutated)
            assert any(issue.code == "SCHEMA" for issue in bundle.validate_record(mutated))


def test_schema_bytes_cannot_drift_under_an_unchanged_manifest(tmp_path):
    local = tmp_path / "bundle"
    shutil.copytree(DIRECTORY, local)
    target = local / RECORD_ENTRIES[0]["path"]
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ContractError, match="differ from the bundle manifest"):
        SchemaBundle(local)
