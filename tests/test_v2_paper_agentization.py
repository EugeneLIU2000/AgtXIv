from __future__ import annotations

import copy
import json
from html.parser import HTMLParser
from pathlib import Path

import jsonschema
import pytest

from tools.validate_v2_paper_agentization import (
    DEFAULT_FIXTURES,
    SCHEMA_BY_DISCRIMINATOR,
    SCHEMA_DIR,
    canonical_content_hash,
    canonical_release_hash,
    exact_ref,
    file_content_hash,
    load_bundle,
    validate_bundle,
)


@pytest.fixture
def bundle():
    return load_bundle(DEFAULT_FIXTURES)


def seal(record):
    record["content_hash"] = canonical_content_hash(record)


def rechain(bundle):
    profile = bundle["agentization-profile.json"]
    seal(profile)
    scope = bundle["inventory-scope.json"]
    scope["profile_ref"] = exact_ref(profile)
    seal(scope)
    math_ir = bundle["math-claim-ir.json"]
    math_ir["scope_ref"] = exact_ref(scope)
    seal(math_ir)
    request = bundle["formalization-request.json"]
    request["target_ref"].update(exact_ref(math_ir))
    seal(request)
    result = bundle["formalization-record.json"]
    result["request_ref"] = exact_ref(request)
    result["target_ref"] = copy.deepcopy(request["target_ref"])
    seal(result)

    records = {record["id"]: record for record in bundle.values() if "id" in record}
    manifest = bundle["paper-agent-release-manifest.json"]
    manifest["profile_ref"] = exact_ref(profile)
    manifest["scope_ref"] = exact_ref(scope)
    for artifact in manifest["artifacts"]:
        target = records.get(artifact["artifact_id"])
        if target:
            artifact["content_hash"] = target["content_hash"]
        elif artifact["artifact_class"] == "SOURCE_BYTES":
            artifact["path"] = profile["paper_release"]["source_path"]
            artifact["content_hash"] = profile["paper_release"]["source_hash"]
        elif artifact["artifact_class"] == "FORMAL_ENVIRONMENT_DESCRIPTOR":
            artifact["artifact_id"] = request["environment"]["environment_id"]
            artifact["path"] = request["environment"]["descriptor_path"]
            artifact["content_hash"] = request["environment"]["descriptor_hash"]
    for row in manifest["disposition_ledger"]:
        row["basis_refs"] = [exact_ref(records[ref["id"]]) for ref in row["basis_refs"]]
    manifest["release_hash"] = canonical_release_hash(manifest)
    seal(manifest)

    audit = bundle["release-audit-record.json"]
    audit["manifest_ref"] = exact_ref(manifest)
    audit["profile_ref"] = exact_ref(profile)
    audit["scope_ref"] = exact_ref(scope)
    audit["audited_release_hash"] = manifest["release_hash"]
    seal(audit)
    certificate = bundle["release-certification-record.json"]
    certificate["manifest_ref"] = exact_ref(manifest)
    certificate["audit_ref"] = exact_ref(audit)
    certificate["certified_release_hash"] = manifest["release_hash"]
    seal(certificate)
    knowledge = bundle["knowledge-index-snapshot.json"]
    knowledge["source_release_ref"] = exact_ref(manifest)
    knowledge["release_certificate_ref"] = exact_ref(certificate)
    for entry in knowledge["entries"]:
        entry["record_ref"] = exact_ref(records[entry["record_ref"]["id"]])
    seal(knowledge)
    package_query = bundle["query-resolution-package-backed.json"]
    package_query["release_manifest_ref"] = exact_ref(manifest)
    package_query["release_certificate_ref"] = exact_ref(certificate)
    package_query["knowledge_index_snapshot"] = exact_ref(knowledge)
    package_query["returned_record_refs"] = [exact_ref(records[ref["id"]]) for ref in package_query["returned_record_refs"]]
    seal(package_query)
    provisional_query = bundle["query-resolution-provisional.json"]
    provisional_query["agentization_trigger"]["profile_ref"] = exact_ref(profile)
    provisional_query["agentization_trigger"]["scope_ref"] = exact_ref(scope)
    seal(provisional_query)


def assert_rejected(bundle, text: str) -> None:
    errors = validate_bundle(bundle, DEFAULT_FIXTURES)
    assert errors
    assert any(text in error for error in errors), errors


def write_fixture_dir(bundle, fixture_dir: Path) -> None:
    fixture_dir.mkdir()
    for source in DEFAULT_FIXTURES.rglob("*"):
        if source.is_file() and source.suffix != ".json":
            target = fixture_dir / source.relative_to(DEFAULT_FIXTURES)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
    for name, record in bundle.items():
        (fixture_dir / name).write_text(json.dumps(record, indent=2) + "\n")


def test_positive_fixture_family(bundle):
    assert validate_bundle(bundle, DEFAULT_FIXTURES) == []
    assert {record["schema"] for record in bundle.values()} <= set(SCHEMA_BY_DISCRIMINATOR)


def test_all_v2_schemas_are_meta_valid():
    for schema_name in SCHEMA_BY_DISCRIMINATOR.values():
        schema = json.loads((SCHEMA_DIR / schema_name).read_text())
        jsonschema.Draft202012Validator.check_schema(schema)


def test_stale_record_content_hash_is_rejected(bundle):
    bundle["query-resolution-provisional.json"]["question"] += " changed"
    assert_rejected(bundle, "stale content_hash")


def test_duplicate_id_revision_is_rejected(bundle):
    bundle["duplicate.json"] = copy.deepcopy(bundle["query-resolution-provisional.json"])
    assert_rejected(bundle, "duplicate (id, revision)")


def test_stale_release_hash_is_rejected_even_with_fresh_manifest_record_hash(bundle):
    manifest = bundle["paper-agent-release-manifest.json"]
    manifest["release_hash"] = "sha256:" + "9" * 64
    seal(manifest)
    assert_rejected(bundle, "stale release_hash")


def test_unknown_discriminator_is_rejected(bundle):
    unknown = {"schema": "agtxiv.unknown/2.0.0", "id": "unknown:1", "record_revision": 1}
    seal(unknown)
    bundle["unknown.json"] = unknown
    assert_rejected(bundle, "unknown V2 schema discriminator")


@pytest.mark.parametrize("field", ["profile_ref", "scope_ref"])
def test_missing_exact_profile_or_scope_is_rejected(bundle, field):
    del bundle["paper-agent-release-manifest.json"][field]
    assert_rejected(bundle, field)


def test_scope_entry_kind_must_be_allowed_by_profile(bundle):
    bundle["inventory-scope.json"]["entries"][0]["entry_kind"] = "DEFINITION"
    rechain(bundle)
    assert_rejected(bundle, "not allowed by the profile")


def test_missing_required_manifest_artifact_class_is_rejected(bundle):
    bundle["paper-agent-release-manifest.json"]["artifacts"].pop()
    assert_rejected(bundle, "missing required artifact classes")


def test_missing_disposition_is_rejected(bundle):
    bundle["paper-agent-release-manifest.json"]["disposition_ledger"].pop()
    assert_rejected(bundle, "missing in-scope")


def test_duplicate_disposition_is_rejected(bundle):
    ledger = bundle["paper-agent-release-manifest.json"]["disposition_ledger"]
    ledger.append(copy.deepcopy(ledger[0]))
    assert_rejected(bundle, "duplicate")


def test_out_of_scope_disposition_is_rejected(bundle):
    bundle["paper-agent-release-manifest.json"]["disposition_ledger"].append(
        {"inventory_entry_id": "inventory-entry:outside", "disposition": "BLOCKED", "basis_refs": []}
    )
    assert_rejected(bundle, "out-of-scope")


def test_aggregate_verified_is_rejected(bundle):
    bundle["paper-agent-release-manifest.json"]["verified"] = True
    assert_rejected(bundle, "aggregate verified")


def first_record_artifact(bundle):
    return next(
        artifact
        for artifact in bundle["paper-agent-release-manifest.json"]["artifacts"]
        if artifact["artifact_category"] == "RECORD"
    )


def test_manifest_artifact_id_is_checked_against_resolved_record(bundle):
    first_record_artifact(bundle)["artifact_id"] = "math-claim-ir:wrong"
    assert_rejected(bundle, "record artifact identity does not resolve")


def test_manifest_artifact_hash_is_checked_against_resolved_record(bundle):
    first_record_artifact(bundle)["content_hash"] = "sha256:" + "9" * 64
    assert_rejected(bundle, "artifact content_hash mismatch")


def test_record_artifact_class_cannot_be_satisfied_by_lean_blob(bundle):
    artifact = first_record_artifact(bundle)
    artifact["path"] = "generated/Theorem1.lean"
    artifact["content_hash"] = file_content_hash(DEFAULT_FIXTURES / artifact["path"])
    assert_rejected(bundle, "RECORD artifact is not a typed JSON record")


def test_byte_artifact_cannot_claim_record_class(bundle):
    artifact = bundle["paper-agent-release-manifest.json"]["artifacts"][0]
    artifact["artifact_class"] = "MATH_CLAIM_IR"
    assert_rejected(bundle, "unsupported class")


def test_generated_artifact_hashes_match_actual_bytes(bundle):
    record = bundle["formalization-record.json"]
    for artifact in record["generated_artifacts"]:
        assert artifact["content_hash"] == file_content_hash(DEFAULT_FIXTURES / artifact["path"])


def test_stale_generated_artifact_byte_hash_is_rejected(bundle):
    result = bundle["formalization-record.json"]
    result["generated_artifacts"][0]["content_hash"] = "sha256:" + "9" * 64
    seal(result)
    assert_rejected(bundle, "stale byte hash")


def test_coordinated_resealed_source_hash_change_is_rejected(bundle):
    forged = "sha256:" + "9" * 64
    bundle["agentization-profile.json"]["paper_release"]["source_hash"] = forged
    bundle["inventory-scope.json"]["paper_release"]["source_hash"] = forged
    rechain(bundle)
    assert_rejected(bundle, "exact paper source has stale byte hash")


def test_coordinated_resealed_environment_change_is_rejected(bundle):
    forged = "sha256:" + "9" * 64
    for name in ("formalization-request.json", "formalization-record.json"):
        bundle[name]["environment"]["descriptor_hash"] = forged
    rechain(bundle)
    assert_rejected(bundle, "formal environment descriptor has stale byte hash")


def test_resealed_environment_descriptor_cannot_forge_project_manifest(bundle, tmp_path):
    fixture_dir = tmp_path / "fixture"
    write_fixture_dir(bundle, fixture_dir)
    descriptor_path = fixture_dir / "environment/lean-environment.toml"
    descriptor = descriptor_path.read_text()
    descriptor_path.write_text(
        "\n".join(
            f'project_manifest_hash = "sha256:{"9" * 64}"'
            if line.startswith("project_manifest_hash = ") else line
            for line in descriptor.splitlines()
        ) + "\n"
    )
    for name in ("formalization-request.json", "formalization-record.json"):
        bundle[name]["environment"]["descriptor_hash"] = file_content_hash(descriptor_path)
    rechain(bundle)
    for name, record in bundle.items():
        (fixture_dir / name).write_text(json.dumps(record, indent=2) + "\n")
    errors = validate_bundle(load_bundle(fixture_dir), fixture_dir)
    assert any("project manifest has stale byte hash" in error for error in errors), errors


def test_coordinated_resealed_boundary_change_is_rejected(bundle):
    forged = "sha256:" + "9" * 64
    formal_entry = next(
        entry
        for entry in bundle["inventory-scope.json"]["entries"]
        if entry["entry_id"] == "inventory-entry:formal-main"
    )
    formal_entry["source_hash"] = forged
    for name in ("formalization-request.json", "formalization-record.json"):
        bundle[name]["boundary"]["source_component_hash"] = forged
    rechain(bundle)
    assert_rejected(bundle, "scoped source component has stale byte hash")


def test_success_requires_every_requested_artifact_kind(bundle):
    result = bundle["formalization-record.json"]
    result["generated_artifacts"].pop()
    seal(result)
    assert_rejected(bundle, "exactly every requested artifact kind")


def test_valid_partial_formalization_behavior(bundle, tmp_path):
    result = bundle["formalization-record.json"]
    result["generation_outcome"] = "PARTIAL"
    result["generated_artifacts"] = result["generated_artifacts"][:1]
    result["diagnostics"] = ["Source module and build report were not generated."]
    rechain(bundle)
    fixture_dir = tmp_path / "fixture"
    write_fixture_dir(bundle, fixture_dir)
    assert validate_bundle(load_bundle(fixture_dir), fixture_dir) == []


def test_partial_requires_diagnostics_and_proper_subset(bundle):
    result = bundle["formalization-record.json"]
    result["generation_outcome"] = "PARTIAL"
    seal(result)
    assert_rejected(bundle, "partial FormalizationRecord")


def test_failed_formalization_cannot_retain_generated_artifacts(bundle):
    result = bundle["formalization-record.json"]
    result["generation_outcome"] = "FAILED"
    result["diagnostics"] = ["Generation failed."]
    seal(result)
    assert_rejected(bundle, "failed FormalizationRecord")


def test_formalization_target_component_must_exist(bundle):
    bundle["formalization-request.json"]["target_ref"]["component_path"] = "/missing"
    bundle["formalization-record.json"]["target_ref"]["component_path"] = "/missing"
    rechain(bundle)
    assert_rejected(bundle, "target/component does not resolve")


def test_knowledge_index_requires_typed_exact_certified_release(bundle):
    knowledge = bundle["knowledge-index-snapshot.json"]
    knowledge["source_release_ref"] = exact_ref(bundle["release-audit-record.json"])
    seal(knowledge)
    package_query = bundle["query-resolution-package-backed.json"]
    package_query["knowledge_index_snapshot"] = exact_ref(knowledge)
    seal(package_query)
    assert_rejected(bundle, "expected ['agtxiv.paper-agent-release-manifest/2.0.0']")


def test_knowledge_entry_must_be_exact_manifest_artifact(bundle):
    knowledge = bundle["knowledge-index-snapshot.json"]
    knowledge["entries"][0]["record_ref"] = exact_ref(bundle["formalization-request.json"])
    seal(knowledge)
    assert_rejected(bundle, "not an exact manifest artifact")


def test_knowledge_entry_cannot_be_reassigned_to_another_inventory_entry(bundle):
    knowledge = bundle["knowledge-index-snapshot.json"]
    knowledge["entries"][1]["inventory_entry_id"] = "inventory-entry:claim-main"
    knowledge["entries"][1]["admission_status"] = "ADMITTED"
    seal(knowledge)
    assert_rejected(bundle, "does not match the admitted record binding")


def test_formalization_record_binding_must_match_boundary_and_ledger(bundle):
    bundle["formalization-record.json"]["inventory_entry_id"] = "inventory-entry:claim-main"
    rechain(bundle)
    assert_rejected(bundle, "inventory entry does not match its request boundary")


def test_manifest_record_binding_uses_exact_record_identity(bundle):
    math_ir = bundle["math-claim-ir.json"]
    math_ir["source_inventory_entry_id"] = "inventory-entry:formal-main"
    rechain(bundle)
    alternate = copy.deepcopy(math_ir)
    alternate["record_revision"] = 2
    alternate["source_inventory_entry_id"] = "inventory-entry:claim-main"
    seal(alternate)
    bundle["z-alternate-math-claim-ir.json"] = alternate
    assert_rejected(bundle, "wrong inventory entry kind")


def test_manifest_rejects_duplicate_exact_record_artifact(bundle):
    manifest = bundle["paper-agent-release-manifest.json"]
    duplicate = copy.deepcopy(first_record_artifact(bundle))
    duplicate["path"] = "./" + duplicate["path"]
    manifest["artifacts"].append(duplicate)
    assert_rejected(bundle, "duplicate record artifact identity")


def test_knowledge_index_rejects_duplicate_record_admission(bundle):
    knowledge = bundle["knowledge-index-snapshot.json"]
    duplicate = copy.deepcopy(knowledge["entries"][0])
    duplicate["inventory_entry_id"] = "inventory-entry:formal-main"
    duplicate["admission_status"] = "CONDITIONAL"
    knowledge["entries"].append(duplicate)
    seal(knowledge)
    assert_rejected(bundle, "duplicate record admission")


def test_knowledge_index_rejects_duplicate_inventory_record_pair(bundle):
    knowledge = bundle["knowledge-index-snapshot.json"]
    knowledge["entries"].append(copy.deepcopy(knowledge["entries"][0]))
    seal(knowledge)
    assert_rejected(bundle, "duplicate inventory-entry/record pair")


def test_package_query_cannot_return_provisional_or_unadmitted_record(bundle):
    query = bundle["query-resolution-package-backed.json"]
    query["returned_record_refs"] = [exact_ref(bundle["query-resolution-provisional.json"])]
    seal(query)
    assert_rejected(bundle, "not admitted by the exact knowledge index")


def test_audit_requires_every_mandatory_check_exactly_once(bundle):
    bundle["release-audit-record.json"]["checks"].pop()
    seal(bundle["release-audit-record.json"])
    assert_rejected(bundle, "exactly one passing instance")


def test_audit_rejects_duplicate_mandatory_check(bundle):
    checks = bundle["release-audit-record.json"]["checks"]
    checks[-1] = copy.deepcopy(checks[0])
    seal(bundle["release-audit-record.json"])
    assert_rejected(bundle, "exactly one passing instance")


def test_coordinator_self_audit_is_rejected(bundle):
    actor_id = bundle["paper-agent-release-manifest.json"]["coordinator"]["actor_id"]
    bundle["release-audit-record.json"]["auditor"]["actor_id"] = actor_id
    bundle["release-certification-record.json"]["auditor"]["actor_id"] = actor_id
    assert_rejected(bundle, "pairwise distinct")


@pytest.mark.parametrize("overlap", ["coordinator", "auditor"])
def test_certifier_identity_overlap_is_rejected(bundle, overlap):
    if overlap == "coordinator":
        actor_id = bundle["paper-agent-release-manifest.json"]["coordinator"]["actor_id"]
    else:
        actor_id = bundle["release-audit-record.json"]["auditor"]["actor_id"]
    bundle["release-certification-record.json"]["certifier"]["actor_id"] = actor_id
    assert_rejected(bundle, "pairwise distinct")


def test_manifest_certificate_mismatch_is_rejected(bundle):
    bundle["release-certification-record.json"]["certified_release_hash"] = "sha256:" + "9" * 64
    assert_rejected(bundle, "release hashes differ")


@pytest.mark.parametrize("field", ["mutation", "publication"])
def test_package_query_mutation_or_publication_field_is_rejected(bundle, field):
    bundle["query-resolution-package-backed.json"][field] = "REQUESTED"
    assert_rejected(bundle, "not allowed")


def test_provisional_query_requires_agentization_trigger(bundle):
    query = bundle["query-resolution-provisional.json"]
    del query["agentization_trigger"]
    seal(query)
    assert_rejected(bundle, "missing its agentization trigger")


@pytest.mark.parametrize("field", ["profile_ref", "scope_ref"])
def test_provisional_trigger_requires_exact_profile_and_scope(bundle, field):
    query = bundle["query-resolution-provisional.json"]
    if field == "profile_ref":
        query["agentization_trigger"][field] = exact_ref(bundle["inventory-scope.json"])
    else:
        query["agentization_trigger"][field] = exact_ref(bundle["agentization-profile.json"])
    seal(query)
    assert_rejected(bundle, "does not bind the exact profile and scope")


def test_provisional_trigger_scope_cannot_be_query_controlled(bundle):
    query = bundle["query-resolution-provisional.json"]
    query["agentization_trigger"]["scope_control"] = "QUERY_CONTROLLED"
    seal(query)
    assert_rejected(bundle, "permits query-controlled scope")


@pytest.mark.parametrize("field", ["contract_admission", "knowledge_base_promotion"])
def test_provisional_promotion_is_rejected(bundle, field):
    bundle["query-resolution-provisional.json"]["canonical_effects"][field] = "ADMITTED"
    assert_rejected(bundle, "FORBIDDEN")


@pytest.mark.parametrize("field", ["verification_status", "alignment_status", "scientific_acceptance"])
def test_formalization_record_cannot_embed_authority_axes(bundle, field):
    bundle["formalization-record.json"][field] = "PASSED"
    assert_rejected(bundle, "FormalizationRecord cannot own")


@pytest.mark.parametrize("field", ["target_ref", "boundary", "environment"])
def test_formalization_request_result_boundary_mismatch_is_rejected(bundle, field):
    result = bundle["formalization-record.json"][field]
    leaf = next(iter(result))
    result[leaf] = "mismatch"
    assert_rejected(bundle, f"{field} mismatch")


def test_architecture_release_precedes_package_query_and_has_no_query_scoped_canonical_region():
    source = json.loads(Path("docs/architecture/agtxiv-paper-first-layered.architecture.json").read_text())
    edges = {(edge["from"], edge["to"]) for edge in source["connections"]}
    assert ("release_audit", "release_certifier") in edges
    assert ("release_certifier", "paper_agent_release") in edges
    assert ("paper_agent_release", "knowledge_base") in edges
    assert ("knowledge_base", "query_resolution") in edges
    assert all(
        not ("query" in boundary["label"].lower() and "paper_agent_release" in boundary["wraps"])
        for boundary in source.get("boundaries", [])
    )


class ArchitectureHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.node_ids = set()
        self.edges = set()
        self.guided_text = ""
        self._in_guided = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "data-node-id" in values:
            self.node_ids.add(values["data-node-id"])
        if all(key in values for key in ("data-edge-id", "data-edge-from", "data-edge-to")):
            self.edges.add((values["data-edge-id"], values["data-edge-from"], values["data-edge-to"]))
        if tag == "script" and values.get("id") == "archify-guided-views-data":
            self._in_guided = True

    def handle_endtag(self, tag):
        if tag == "script" and self._in_guided:
            self._in_guided = False

    def handle_data(self, data):
        if self._in_guided:
            self.guided_text += data


def test_architecture_json_and_compiled_html_semantics_are_synchronized():
    source = json.loads(Path("docs/architecture/agtxiv-paper-first-layered.architecture.json").read_text())
    parser = ArchitectureHTMLParser()
    parser.feed(Path("docs/architecture/agtxiv-paper-first-layered.architecture.html").read_text())
    expected_nodes = {component["id"] for component in source["components"]}
    expected_edges = {(edge["id"], edge["from"], edge["to"]) for edge in source["connections"]}
    assert parser.node_ids == expected_nodes
    assert parser.edges == expected_edges
    assert json.loads(parser.guided_text) == source["meta"]["views"]
