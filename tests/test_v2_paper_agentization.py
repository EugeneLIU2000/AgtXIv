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

    def refresh_refs(value):
        if isinstance(value, dict):
            if set(value) in ({"id", "record_revision", "content_hash"}, {"id", "record_revision", "content_hash", "component_path"}) and value["id"] in records:
                component_path = value.get("component_path")
                value.update(exact_ref(records[value["id"]]))
                if component_path is not None:
                    value["component_path"] = component_path
            else:
                for child in value.values():
                    refresh_refs(child)
        elif isinstance(value, list):
            for child in value:
                refresh_refs(child)

    for record in records.values():
        if record.get("schema") == "agtxiv.assessment-record/2.0.0":
            refresh_refs(record)
            seal(record)

    manifest = bundle["paper-agent-release-manifest.json"]
    refresh_refs(manifest)
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
    manifest["release_hash"] = canonical_release_hash(manifest)
    seal(manifest)

    audit = bundle["release-audit-record.json"]
    refresh_refs(audit)
    audit["audited_release_hash"] = manifest["release_hash"]
    seal(audit)
    certificate = bundle["release-certification-record.json"]
    refresh_refs(certificate)
    certificate["certified_release_hash"] = manifest["release_hash"] if certificate.get("decision") == "CERTIFIED" else None
    seal(certificate)
    genesis = bundle["knowledge-index-snapshot-genesis.json"]
    seal(genesis)
    knowledge = bundle["knowledge-index-snapshot.json"]
    refresh_refs(knowledge)
    seal(knowledge)
    ingestion = bundle["knowledge-ingestion-receipt.json"]
    refresh_refs(ingestion)
    seal(ingestion)
    package_query = bundle["query-resolution-package-backed.json"]
    refresh_refs(package_query)
    seal(package_query)
    provisional_query = bundle["query-resolution-provisional.json"]
    refresh_refs(provisional_query)
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
    knowledge["entries"][1]["component"]["inventory_entry_id"] = "inventory-entry:claim-main"
    knowledge["entries"][1]["admission_status"] = "ADMITTED"
    seal(knowledge)
    assert_rejected(bundle, "does not match the admitted record binding")


@pytest.mark.parametrize(
    "entry_index,family",
    [(0, "MathClaimIR/CONTRACT"), (1, "FormalizationRecord/FORMAL_ARTIFACT"), (2, "AssessmentRecord/ASSESSMENT")],
)
def test_knowledge_component_path_cannot_drift_from_record_family_boundary(bundle, entry_index, family):
    entry = bundle["knowledge-index-snapshot.json"]["entries"][entry_index]
    entry["component"]["component_path"] = f"/fabricated/{family}"
    seal(bundle["knowledge-index-snapshot.json"])
    assert_rejected(bundle, "component_path does not resolve to the record-family-specific exact component boundary")


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


def test_audit_requires_every_mandatory_stage_exactly_once(bundle):
    bundle["release-audit-record.json"]["verification_steps"].pop()
    seal(bundle["release-audit-record.json"])
    assert_rejected(bundle, "missing required audit stages")


def test_audit_rejects_duplicate_mandatory_stage(bundle):
    steps = bundle["release-audit-record.json"]["verification_steps"]
    steps[-1] = copy.deepcopy(steps[0])
    seal(bundle["release-audit-record.json"])
    assert_rejected(bundle, "duplicate")


def test_coordinator_self_audit_is_rejected(bundle):
    actor_id = bundle["paper-agent-release-manifest.json"]["coordinator"]["actor_id"]
    bundle["release-audit-record.json"]["auditor"]["actor_id"] = actor_id
    bundle["release-certification-record.json"]["root_agent"]["actor_id"] = actor_id
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
    assert_rejected(bundle, "release hash/rejection fields are inconsistent")


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
    required_chain = [
        "claims_math_ir",
        "dependencies_inferences",
        "formalization",
        "formal_verification",
        "backtranslation_alignment",
        "residual_semantics",
        "assessment_selection",
        "release_audit",
        "release_certifier",
        "paper_agent_release",
        "package_archive",
        "reusable_entry_admission",
        "knowledge_base",
        "query_resolution",
    ]
    assert all((left, right) in edges for left, right in zip(required_chain, required_chain[1:]))
    components = {component["id"]: component for component in source["components"]}
    assert components["package_archive"]["tag"] == "V2 target service"
    assert components["reusable_entry_admission"]["sublabel"] == "Atomic KnowledgeIngestionReceipt"
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


def test_v2_root_agent_role_cannot_be_coordinator_role(bundle):
    bundle["release-audit-record.json"]["auditor"]["role"] = "AGENTIZATION_COORDINATOR"
    seal(bundle["release-audit-record.json"])
    assert_rejected(bundle, "must be the V2 Root Agent")


def test_v2_root_agent_cannot_be_release_certifier(bundle):
    certifier_id = bundle["release-certification-record.json"]["certifier"]["actor_id"]
    bundle["release-audit-record.json"]["auditor"]["actor_id"] = certifier_id
    bundle["release-certification-record.json"]["root_agent"]["actor_id"] = certifier_id
    assert_rejected(bundle, "pairwise distinct")


def test_audit_rejects_out_of_order_stages(bundle):
    steps = bundle["release-audit-record.json"]["verification_steps"]
    steps[0], steps[1] = steps[1], steps[0]
    seal(bundle["release-audit-record.json"])
    assert_rejected(bundle, "out-of-order")


def test_release_recommendation_must_retain_entire_unresolved_frontier(bundle):
    bundle["release-audit-record.json"]["release_recommendation"]["retained_frontier_ids"].pop()
    seal(bundle["release-audit-record.json"])
    assert_rejected(bundle, "drops UNKNOWN/BLOCKED/REFUTED frontier")


def test_kernel_check_cannot_promote_source_or_scientific_axis_without_assessment(bundle):
    axes = bundle["knowledge-index-snapshot.json"]["entries"][1]["axes"]
    axes["formal_verification"]["status"] = "KERNEL_CHECKED"
    axes["source_assertion"]["status"] = "SOURCE_ALIGNMENT_ASSESSED"
    axes["scientific_acceptance"]["status"] = "ACCEPTED"
    seal(bundle["knowledge-index-snapshot.json"])
    assert_rejected(bundle, "lacks typed AssessmentRecord")


def test_ingestion_must_bind_exact_audit_and_after_snapshot(bundle):
    receipt = bundle["knowledge-ingestion-receipt.json"]
    receipt["root_agent_audit_ref"] = exact_ref(bundle["formalization-record.json"])
    seal(receipt)
    assert_rejected(bundle, "not bound to the exact profile/manifest/certificate/audit transaction")


def test_atomic_ingestion_rejects_partial_committed_mutation(bundle):
    receipt = bundle["knowledge-ingestion-receipt.json"]
    receipt["accepted_candidates"].pop()
    seal(receipt)
    assert_rejected(bundle, "non-atomic/partial entry mutation")


@pytest.mark.parametrize("missing", ["domain", "provenance", "scope", "axes"])
def test_knowledge_entry_requires_domain_provenance_scope_and_axes(bundle, missing):
    entry = bundle["knowledge-index-snapshot.json"]["entries"][0]
    if missing == "domain":
        entry["domain_id"] = ""
    elif missing == "provenance":
        entry["provenance"] = {}
    elif missing == "scope":
        entry["scope_assumptions"] = {}
    else:
        entry["axes"] = {}
    seal(bundle["knowledge-index-snapshot.json"])
    assert_rejected(bundle, "lacks")


def test_cross_paper_relation_requires_exact_separate_assessment(bundle):
    entries = bundle["knowledge-index-snapshot.json"]["entries"]
    bundle["knowledge-index-snapshot.json"]["cross_paper_relations"] = [{
        "relation_id": "knowledge-relation:unassessed",
        "left_entry_id": entries[0]["entry_id"],
        "right_entry_id": entries[1]["entry_id"],
        "relation": "EQUIVALENT",
        "status": "SEPARATELY_ASSESSED",
    }]
    seal(bundle["knowledge-index-snapshot.json"])
    assert_rejected(bundle, "lacks a compatible exact AssessmentRecord")


def test_domain_view_cannot_suppress_assessed_conflicts(bundle):
    bundle["knowledge-index-snapshot.json"]["view_policy"]["conflict_behavior"] = "SUPPRESS_CONFLICTS"
    seal(bundle["knowledge-index-snapshot.json"])
    assert_rejected(bundle, "suppresses conflicts")


def make_assessment(bundle, *, suffix, kind, targets, axis=None, relation=None, left=None, right=None, outcome):
    record = {
        "schema": "agtxiv.assessment-record/2.0.0",
        "id": f"assessment-record:test:{suffix}",
        "record_revision": 1,
        "source_inventory_entry_id": "inventory-entry:claim-main",
        "assessment_kind": kind,
        "target_refs": [copy.deepcopy(target) for target in targets],
        "axis": axis,
        "relation": relation,
        "left_entry_id": left,
        "right_entry_id": right,
        "outcome": outcome,
    }
    seal(record)
    bundle[f"assessment-{suffix}.json"] = record
    return record


def add_distinct_package_entry(bundle):
    profile = copy.deepcopy(bundle["agentization-profile.json"])
    profile["id"] = "agentization-profile:2608.00002v1:theory-standard"
    profile["paper_release"].update({
        "paper_id": "arxiv:2608.00002",
        "release_id": "v1",
        "source_uri": "https://arxiv.org/pdf/2608.00002v1",
    })
    profile["inventory_classes"] = ["MATH_CLAIM"]
    profile["required_artifact_classes"] = ["SOURCE_BYTES", "MATH_CLAIM_IR"]
    profile["allowed_dispositions"] = ["ADMITTED"]
    seal(profile)

    scope = copy.deepcopy(bundle["inventory-scope.json"])
    scope["id"] = "inventory-scope:2608.00002v1:theory-standard"
    scope["profile_ref"] = exact_ref(profile)
    scope["paper_release"] = copy.deepcopy(profile["paper_release"])
    scope["entries"] = [copy.deepcopy(scope["entries"][0])]
    scope["entries"][0].update({
        "entry_id": "inventory-entry:claim-second",
        "source_locator": "section:3/theorem:2",
    })
    seal(scope)

    math_ir = copy.deepcopy(bundle["math-claim-ir.json"])
    math_ir["id"] = "math-claim-ir:2608.00002v1:theorem-2"
    math_ir["scope_ref"] = exact_ref(scope)
    math_ir["source_inventory_entry_id"] = "inventory-entry:claim-second"
    seal(math_ir)

    manifest = copy.deepcopy(bundle["paper-agent-release-manifest.json"])
    manifest["id"] = "paper-agent-release-manifest:2608.00002v1:theory-standard"
    manifest["profile_ref"] = exact_ref(profile)
    manifest["scope_ref"] = exact_ref(scope)
    manifest["artifacts"] = [
        {
            "artifact_category": "BYTE",
            "artifact_id": "source-release:arxiv:2608.00002:v1",
            "artifact_class": "SOURCE_BYTES",
            "media_type": "text/plain",
            "content_hash": profile["paper_release"]["source_hash"],
            "path": profile["paper_release"]["source_path"],
        },
        {
            "artifact_category": "RECORD",
            "artifact_id": math_ir["id"],
            "record_revision": math_ir["record_revision"],
            "artifact_class": "MATH_CLAIM_IR",
            "schema_uri": "https://agtxiv.org/schema/v2/math-claim-ir/2.0.0",
            "content_hash": math_ir["content_hash"],
            "path": "math-claim-ir.json",
        },
    ]
    manifest["disposition_ledger"] = [{
        "inventory_entry_id": "inventory-entry:claim-second",
        "disposition": "ADMITTED",
        "basis_refs": [exact_ref(math_ir)],
    }]
    manifest["release_hash"] = canonical_release_hash(manifest)
    seal(manifest)

    audit = copy.deepcopy(bundle["release-audit-record.json"])
    audit["id"] = "release-audit-record:2608.00002v1:theory-standard"
    audit["manifest_ref"] = exact_ref(manifest)
    audit["profile_ref"] = exact_ref(profile)
    audit["scope_ref"] = exact_ref(scope)
    audit["audited_release_hash"] = manifest["release_hash"]
    seal(audit)

    certificate = copy.deepcopy(bundle["release-certification-record.json"])
    certificate["id"] = "release-certification-record:2608.00002v1:theory-standard"
    certificate["manifest_ref"] = exact_ref(manifest)
    certificate["root_agent_audit_ref"] = exact_ref(audit)
    certificate["certified_release_hash"] = manifest["release_hash"]
    seal(certificate)

    bundle["second-agentization-profile.json"] = profile
    bundle["second-inventory-scope.json"] = scope
    bundle["second-math-claim-ir.json"] = math_ir
    bundle["second-paper-agent-release-manifest.json"] = manifest
    bundle["second-release-audit-record.json"] = audit
    bundle["second-release-certification-record.json"] = certificate

    first = bundle["knowledge-index-snapshot.json"]["entries"][0]
    entry = copy.deepcopy(first)
    entry["entry_id"] = "knowledge-entry:2608.00002v1:theorem-2-contract"
    entry["record_ref"] = exact_ref(math_ir)
    entry["component"]["inventory_entry_id"] = "inventory-entry:claim-second"
    entry["axes"]["source_assertion"] = {"status": "NOT_ASSESSED", "assessment_refs": []}
    entry["provenance"] = {
        "manifest_ref": exact_ref(manifest),
        "certificate_ref": exact_ref(certificate),
        "root_agent_audit_ref": exact_ref(audit),
        "inventory_scope_ref": exact_ref(scope),
        "source": {
            "paper_id": "arxiv:2608.00002",
            "release_id": "v1",
            "source_uri": "https://arxiv.org/pdf/2608.00002v1",
            "source_hash": profile["paper_release"]["source_hash"],
            "source_locator": "section:3/theorem:2",
            "source_component_path": scope["entries"][0]["source_component_path"],
            "source_component_hash": scope["entries"][0]["source_hash"],
        },
    }
    knowledge = bundle["knowledge-index-snapshot.json"]
    knowledge["package_bindings"].append({
        "manifest_ref": exact_ref(manifest),
        "certificate_ref": exact_ref(certificate),
        "root_agent_audit_ref": exact_ref(audit),
    })
    knowledge["inventory_scope_refs"].append(exact_ref(scope))
    knowledge["entries"].append(entry)
    return entry


def add_assessed_relation(bundle, relation="CONFLICTING", entries=None):
    entries = entries or bundle["knowledge-index-snapshot.json"]["entries"]
    assessment = make_assessment(
        bundle,
        suffix=f"relation-{relation.lower()}",
        kind="CROSS_PAPER_RELATION",
        targets=[entry["record_ref"] for entry in entries[:2]],
        relation=relation,
        left=entries[0]["entry_id"],
        right=entries[1]["entry_id"],
        outcome="RELATION_CONFIRMED",
    )
    relation_record = {
        "relation_id": f"knowledge-relation:test:{relation.lower()}",
        "left_entry_id": entries[0]["entry_id"],
        "right_entry_id": entries[1]["entry_id"],
        "relation": relation,
        "relation_assessment_ref": exact_ref(assessment),
        "status": "SEPARATELY_ASSESSED",
    }
    bundle["knowledge-index-snapshot.json"]["cross_paper_relations"] = [relation_record]
    return relation_record


def make_ingestion_noop_from_current_snapshot(bundle):
    before = bundle["knowledge-index-snapshot-genesis.json"]
    after = bundle["knowledge-index-snapshot.json"]
    for field in (
        "view_policy",
        "package_bindings",
        "inventory_scope_refs",
        "entries",
        "cross_paper_relations",
        "environment_compatibility_receipts",
    ):
        before[field] = copy.deepcopy(after[field])
    receipt = bundle["knowledge-ingestion-receipt.json"]
    receipt["accepted_candidates"] = []
    receipt["blocked_candidates"] = [
        {**copy.deepcopy(candidate), "reason": "Candidate was already present before this no-op transaction."}
        for candidate in receipt["candidate_set"]
    ]


def test_certified_requires_root_agent_release_recommendation(bundle):
    bundle["release-audit-record.json"]["release_recommendation"]["decision"] = "DO_NOT_RELEASE"
    rechain(bundle)
    assert_rejected(bundle, "CERTIFIED requires the exact Root Agent recommendation")


def test_certified_requires_every_mechanical_check_to_pass(bundle):
    certificate = bundle["release-certification-record.json"]
    certificate["mechanical_checks"][0]["status"] = "FAILED"
    seal(certificate)
    assert_rejected(bundle, "CERTIFIED requires every mechanical check to pass")


def test_rejected_certificate_variant_is_schema_valid(bundle):
    certificate = bundle["release-certification-record.json"]
    certificate["decision"] = "REJECTED"
    certificate["mechanical_checks"][0]["status"] = "FAILED"
    certificate["certified_release_hash"] = None
    certificate["rejection_reasons"] = ["Root Agent recommended against release."]
    seal(certificate)
    schema = json.loads((SCHEMA_DIR / "release-certification-record.schema.json").read_text())
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(certificate)) == []


@pytest.mark.parametrize("invalid", ["no_failed_check", "retained_release_hash", "missing_reason"])
def test_rejected_certificate_variant_rejects_inconsistent_fields(bundle, invalid):
    certificate = bundle["release-certification-record.json"]
    certificate["decision"] = "REJECTED"
    certificate["mechanical_checks"][0]["status"] = "FAILED"
    certificate["certified_release_hash"] = None
    certificate["rejection_reasons"] = ["Mechanical rejection."]
    if invalid == "no_failed_check":
        certificate["mechanical_checks"][0]["status"] = "PASSED"
    elif invalid == "retained_release_hash":
        certificate["certified_release_hash"] = bundle["paper-agent-release-manifest.json"]["release_hash"]
    else:
        certificate["rejection_reasons"] = []
    seal(certificate)
    schema = json.loads((SCHEMA_DIR / "release-certification-record.schema.json").read_text())
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(certificate))


def test_audit_selected_assessment_ref_cannot_be_math_ir(bundle):
    step = bundle["release-audit-record.json"]["verification_steps"][3]
    step["selected_assessment_refs"] = [exact_ref(bundle["math-claim-ir.json"])]
    seal(bundle["release-audit-record.json"])
    assert_rejected(bundle, "expected ['agtxiv.assessment-record/2.0.0']")


@pytest.mark.parametrize(
    "axis_name,status,kind,axis,outcome",
    [
        ("source_assertion", "SOURCE_ALIGNMENT_ASSESSED", "SOURCE_ALIGNMENT", "SOURCE_ASSERTION", "ALIGNED"),
        ("source_assertion", "SOURCE_ALIGNMENT_REJECTED", "SOURCE_ALIGNMENT", "SOURCE_ASSERTION", "MISALIGNED"),
        ("formal_verification", "KERNEL_CHECKED", "FORMAL_VERIFICATION", "FORMAL_VERIFICATION", "KERNEL_CHECKED"),
        ("formal_verification", "KERNEL_REJECTED", "FORMAL_VERIFICATION", "FORMAL_VERIFICATION", "KERNEL_REJECTED"),
        ("scientific_acceptance", "ACCEPTED", "SCIENTIFIC_ACCEPTANCE", "SCIENTIFIC_ACCEPTANCE", "ACCEPTED"),
        ("scientific_acceptance", "REJECTED", "SCIENTIFIC_ACCEPTANCE", "SCIENTIFIC_ACCEPTANCE", "REJECTED"),
    ],
)
def test_each_assessed_axis_accepts_only_compatible_typed_assessment(bundle, axis_name, status, kind, axis, outcome):
    entry = bundle["knowledge-index-snapshot.json"]["entries"][1]
    assessment = make_assessment(
        bundle,
        suffix=f"axis-{axis_name}-{status.lower()}",
        kind=kind,
        targets=[entry["record_ref"]],
        axis=axis,
        outcome=outcome,
    )
    entry["axes"][axis_name] = {"status": status, "assessment_refs": [exact_ref(assessment)]}
    rechain(bundle)
    assert validate_bundle(bundle, DEFAULT_FIXTURES) == []


@pytest.mark.parametrize(
    "axis_name,status",
    [
        ("source_assertion", "SOURCE_ALIGNMENT_ASSESSED"),
        ("formal_verification", "KERNEL_CHECKED"),
        ("scientific_acceptance", "ACCEPTED"),
    ],
)
def test_each_axis_rejects_wrong_assessment_kind(bundle, axis_name, status):
    entry = bundle["knowledge-index-snapshot.json"]["entries"][1]
    assessment = make_assessment(
        bundle,
        suffix=f"wrong-{axis_name}",
        kind="ROOT_STAGE_ASSESSMENT",
        targets=[entry["record_ref"]],
        outcome="PASSED",
    )
    entry["axes"][axis_name] = {"status": status, "assessment_refs": [exact_ref(assessment)]}
    rechain(bundle)
    assert_rejected(bundle, f"{axis_name} uses an incompatible AssessmentRecord")


def test_relation_rejects_wrong_assessment_kind(bundle):
    entries = bundle["knowledge-index-snapshot.json"]["entries"]
    assessment = make_assessment(
        bundle,
        suffix="wrong-relation-kind",
        kind="FORMAL_VERIFICATION",
        targets=[entries[0]["record_ref"]],
        axis="FORMAL_VERIFICATION",
        outcome="KERNEL_CHECKED",
    )
    bundle["knowledge-index-snapshot.json"]["cross_paper_relations"] = [{
        "relation_id": "knowledge-relation:test:wrong-kind",
        "left_entry_id": entries[0]["entry_id"],
        "right_entry_id": entries[1]["entry_id"],
        "relation": "CONFLICTING",
        "relation_assessment_ref": exact_ref(assessment),
        "status": "SEPARATELY_ASSESSED",
    }]
    rechain(bundle)
    assert_rejected(bundle, "relation lacks a compatible exact AssessmentRecord")


def test_query_must_return_every_assessed_relation(bundle):
    add_assessed_relation(bundle)
    rechain(bundle)
    assert_rejected(bundle, "relation/conflict closure omits")


def test_conflict_query_must_retain_both_endpoint_records(bundle):
    relation = add_assessed_relation(bundle)
    bundle["query-resolution-package-backed.json"]["returned_relation_ids"] = [relation["relation_id"]]
    rechain(bundle)
    assert_rejected(bundle, "conflict-preserving closure drops a relation endpoint record")


def test_valid_cross_paper_relation_requires_two_exact_package_chains(bundle):
    second = add_distinct_package_entry(bundle)
    first = bundle["knowledge-index-snapshot.json"]["entries"][0]
    relation = add_assessed_relation(bundle, entries=[first, second])
    query = bundle["query-resolution-package-backed.json"]
    query["returned_relation_ids"] = [relation["relation_id"]]
    query["returned_record_refs"] = [first["record_ref"], second["record_ref"]]
    make_ingestion_noop_from_current_snapshot(bundle)
    rechain(bundle)
    assert validate_bundle(bundle, DEFAULT_FIXTURES) == []


def test_fabricated_entry_source_identity_cannot_create_cross_paper_relation(bundle):
    source = bundle["knowledge-index-snapshot.json"]["entries"][1]["provenance"]["source"]
    source.update({
        "paper_id": "arxiv:2608.99999",
        "release_id": "v9",
        "source_uri": "https://arxiv.org/pdf/2608.99999v9",
    })
    add_assessed_relation(bundle)
    make_ingestion_noop_from_current_snapshot(bundle)
    rechain(bundle)
    assert_rejected(bundle, "source provenance does not match its resolved exact manifest/scope chain")
    assert_rejected(bundle, "different paper releases derived from exact package provenance")


def test_preserved_genesis_entry_provenance_is_validated(bundle):
    make_ingestion_noop_from_current_snapshot(bundle)
    for snapshot_name in ("knowledge-index-snapshot-genesis.json", "knowledge-index-snapshot.json"):
        entry = bundle[snapshot_name]["entries"][0]
        entry["provenance"]["source"]["source_uri"] = "https://example.invalid/fabricated"
    rechain(bundle)
    assert_rejected(bundle, "genesis knowledge index entry 0: source provenance does not match")


def test_unresolved_entry_package_binding_is_rejected(bundle):
    entry = bundle["knowledge-index-snapshot.json"]["entries"][0]
    entry["provenance"]["manifest_ref"] = {
        "id": "paper-agent-release-manifest:missing",
        "record_revision": 1,
        "content_hash": "sha256:" + "9" * 64,
    }
    seal(bundle["knowledge-index-snapshot.json"])
    assert_rejected(bundle, "exact package reference does not resolve")


def test_query_relation_closure_does_not_collapse_duplicate_ids(bundle):
    source = bundle["knowledge-index-snapshot.json"]["entries"][1]["provenance"]["source"]
    source["paper_id"] = "arxiv:2608.00002"
    source["release_id"] = "v2"
    source["source_uri"] = "https://arxiv.org/pdf/2608.00002v2"
    relation = add_assessed_relation(bundle)
    query = bundle["query-resolution-package-backed.json"]
    query["returned_relation_ids"] = [relation["relation_id"], relation["relation_id"]]
    query["returned_record_refs"] = [entry["record_ref"] for entry in bundle["knowledge-index-snapshot.json"]["entries"]]
    make_ingestion_noop_from_current_snapshot(bundle)
    rechain(bundle)
    assert_rejected(bundle, "closure omits, duplicates, or invents")


def test_multi_target_frontier_requires_exact_target_set(bundle):
    audit = bundle["release-audit-record.json"]
    frontier = next(item for item in audit["unresolved_frontier"] if item["frontier_id"] == "frontier:alignment")
    frontier["target_refs"].pop()
    seal(audit)
    assert_rejected(bundle, "exact matching frontier entry and target set")


def test_committed_ingestion_preserves_nonempty_before_snapshot(bundle):
    before = bundle["knowledge-index-snapshot-genesis.json"]
    after = bundle["knowledge-index-snapshot.json"]
    before["package_bindings"] = copy.deepcopy(after["package_bindings"])
    before["inventory_scope_refs"] = copy.deepcopy(after["inventory_scope_refs"])
    before["entries"] = [copy.deepcopy(after["entries"][0])]
    receipt = bundle["knowledge-ingestion-receipt.json"]
    prior_entry_id = after["entries"][0]["entry_id"]
    receipt["accepted_candidates"] = [candidate for candidate in receipt["accepted_candidates"] if candidate["knowledge_entry_id"] != prior_entry_id]
    receipt["candidate_set"] = [candidate for candidate in receipt["candidate_set"] if candidate["record_ref"] != after["entries"][0]["record_ref"]]
    rechain(bundle)
    assert validate_bundle(bundle, DEFAULT_FIXTURES) == []


def test_aborted_ingestion_is_exact_no_mutation(bundle):
    receipt = bundle["knowledge-ingestion-receipt.json"]
    receipt["outcome"] = "ABORTED"
    receipt["accepted_candidates"] = []
    receipt["blocked_candidates"] = [
        {**copy.deepcopy(candidate), "reason": "Transaction aborted before candidate admission."}
        for candidate in receipt["candidate_set"]
    ]
    receipt["after_snapshot_ref"] = copy.deepcopy(receipt["before_snapshot_ref"])
    rechain(bundle)
    assert validate_bundle(bundle, DEFAULT_FIXTURES) == []


def test_aborted_ingestion_rejects_accepted_additions(bundle):
    receipt = bundle["knowledge-ingestion-receipt.json"]
    receipt["outcome"] = "ABORTED"
    receipt["after_snapshot_ref"] = copy.deepcopy(receipt["before_snapshot_ref"])
    rechain(bundle)
    assert_rejected(bundle, "ABORTED knowledge ingestion cannot contain accepted additions")


def test_candidate_ids_are_disjoint_across_accept_reject_block_lists(bundle):
    receipt = bundle["knowledge-ingestion-receipt.json"]
    accepted = receipt["accepted_candidates"][0]
    rejected = {key: value for key, value in accepted.items() if key != "knowledge_entry_id"}
    rejected["reason"] = "Rejected duplicate candidate identity."
    receipt["rejected_candidates"] = [rejected]
    seal(receipt)
    assert_rejected(bundle, "candidate IDs must be globally unique and disjoint")


def test_fixture_manifests_and_admits_typed_assessment(bundle):
    assessment = bundle["assessment-record-source-alignment.json"]
    manifest = bundle["paper-agent-release-manifest.json"]
    entry = next(entry for entry in bundle["knowledge-index-snapshot.json"]["entries"] if entry["entry_family"] == "ASSESSMENT")
    artifact = next(artifact for artifact in manifest["artifacts"] if artifact["artifact_class"] == "ASSESSMENT_RECORD")
    assert artifact["artifact_id"] == assessment["id"]
    assert artifact["content_hash"] == assessment["content_hash"]
    assert entry["record_ref"] == exact_ref(assessment)
    assert entry["component"]["inventory_entry_id"] == assessment["source_inventory_entry_id"]
    assert validate_bundle(bundle, DEFAULT_FIXTURES) == []


@pytest.mark.parametrize(
    "entry_index,entry_family",
    [(0, "FORMAL_ARTIFACT"), (1, "CONTRACT"), (2, "CONTRACT")],
)
def test_typed_records_cannot_be_relabelled_to_incompatible_entry_families(bundle, entry_index, entry_family):
    bundle["knowledge-index-snapshot.json"]["entries"][entry_index]["entry_family"] = entry_family
    rechain(bundle)
    assert_rejected(bundle, "incompatible record schema/artifact class/component/entry_family")


def test_cross_paper_relation_ids_are_unique_independent_of_object_uniqueness(bundle):
    relation = add_assessed_relation(bundle)
    duplicate = copy.deepcopy(relation)
    duplicate["relation"] = "SUPPORTS"
    bundle["knowledge-index-snapshot.json"]["cross_paper_relations"].append(duplicate)
    rechain(bundle)
    assert_rejected(bundle, "duplicate relation IDs")


def test_cross_paper_relation_rejects_self_relation(bundle):
    relation = add_assessed_relation(bundle)
    relation["right_entry_id"] = relation["left_entry_id"]
    rechain(bundle)
    assert_rejected(bundle, "endpoints must be distinct")


def test_cross_paper_relation_rejects_same_paper_release(bundle):
    add_assessed_relation(bundle)
    rechain(bundle)
    assert_rejected(bundle, "must identify different paper releases")


@pytest.mark.parametrize("case", ["omission", "extra"])
def test_candidate_dispositions_must_exactly_partition_candidate_set(bundle, case):
    receipt = bundle["knowledge-ingestion-receipt.json"]
    if case == "omission":
        receipt["accepted_candidates"].pop()
    else:
        extra = copy.deepcopy(receipt["accepted_candidates"][0])
        extra["candidate_id"] = "ingestion-candidate:fixture-1:extra"
        receipt["rejected_candidates"].append({
            **{key: value for key, value in extra.items() if key != "knowledge_entry_id"},
            "reason": "Synthetic extra disposition.",
        })
    seal(receipt)
    assert_rejected(bundle, "disjoint exhaustive partition of the exact candidate_set")
