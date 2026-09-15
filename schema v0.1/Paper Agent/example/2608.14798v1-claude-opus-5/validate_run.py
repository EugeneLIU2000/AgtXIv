#!/usr/bin/env python3
"""Read-back check for the saved run. Exit 0 means the recorded successes AND the
recorded blockers both reproduce; it does NOT mean AGENT.md S0-S5 completed."""
from __future__ import annotations
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'src'))
from agtxiv_v3.contracts import SchemaBundle, RecordSet, SuppliedArtifact, digest, exact_ref  # noqa: E402

FORBIDDEN = {'scope-decision', 'frozen-scope', 'obligation-disposition', 'argument-node',
             'inference-step', 'proof-plan', 'argument-snapshot', 'formalization-packet',
             'formalization-attempt', 'formal-check', 'axis-assessment', 'release-manifest'}


def main():
    out = HERE / 'output'
    bundle = SchemaBundle(REPO / 'schema v0.0')
    manifest = json.loads((out / 'manifest.json').read_text())
    checks = json.loads((out / 'interface-checks.json').read_text())
    records = json.loads((out / 'records.json').read_text())
    acq = json.loads((HERE / 'acquisition.json').read_text())

    assert manifest['agent_spec_sha256'] == digest((HERE.parents[1] / 'AGENT.md').read_bytes()), \
        'AGENT.md changed after this run; the run is no longer a run of the saved spec'
    assert manifest['schema_bundle_hash'] == bundle.bundle_hash, 'schema v0.0 bundle changed'
    assert manifest['record_total'] == len(records) == len(manifest['records'])

    for item, record in zip(manifest['records'], records):
        raw = (out / item['path']).read_bytes()
        assert digest(raw) == item['sha256'], item['path']
        assert json.loads(raw) == record and exact_ref(record) == item['ref'], item['path']
    assert all(not bundle.validate_record(r) for r in records), 'a record no longer matches its schema'

    source = REPO / acq['source_directory']
    snapshot = next(r for r in records if r['record_type'].startswith('agtxiv.v3.source-snapshot'))
    artifacts = []
    for unit in snapshot['payload']['units']:
        data = (source / unit['relative_path']).read_bytes()
        assert digest(data) == unit['artifact']['sha256'], unit['relative_path']
        artifacts.append(SuppliedArtifact(unit['artifact']['artifact_id'], unit['artifact']['media_type'], data))
    archive = snapshot['payload']['archive']
    archive_bytes = (REPO / acq['archive_path']).read_bytes()
    assert digest(archive_bytes) == archive['sha256']
    artifacts.append(SuppliedArtifact(archive['artifact_id'], archive['media_type'], archive_bytes))

    full = RecordSet(bundle, records, artifacts).validate(require_artifacts=True)
    assert not full.valid, 'the recorded blocker did not reproduce'
    assert {i.code for i in full.issues} == {'SELF_REVIEW'}, sorted({i.code for i in full.issues})
    maps = [r for r in records if r['record_type'].startswith('agtxiv.v3.claim-component-map')]
    assert len(full.issues) == len(maps), 'blocker count no longer equals the correspondence-map count'

    subset = json.loads((out / 'records-without-maps.json').read_text())
    assert subset == [r for r in records if not r['record_type'].startswith('agtxiv.v3.claim-component-map')]
    diagnostic = RecordSet(bundle, subset, artifacts).validate(require_artifacts=True)
    assert diagnostic.valid, [f'{i.code} {i.record_id}{i.path}' for i in diagnostic.issues]

    present = {r['record_type'].removeprefix('agtxiv.v3.').removesuffix('/0.0.0') for r in records}
    assert not present & FORBIDDEN, sorted(present & FORBIDDEN)
    assert manifest['scope_frozen'] is False and manifest['formal_tasks_created'] is False
    assert checks['handoff']['results']['proof-expand']['accepted'] is False
    assert checks['handoff']['results']['dependency-search']['accepted'] is True
    assert checks['plan_compatibility']['issues'], 'the plan incompatibility no longer reproduces'
    gate = checks['review_gate_probes'][0]
    assert gate['same_principal_as_claim']['issue_codes'] == ['SELF_REVIEW']
    assert gate['distinct_principal']['issue_codes'] == []

    obligations = next(r for r in records if r['record_type'].startswith('agtxiv.v3.inventory-discovery'))['payload']['obligations']
    ids = [o['obligation_id'] for o in obligations]
    assert len(ids) == len(set(ids))

    print(json.dumps({
        'readback_checks_passed': True,
        'records': len(records),
        'source_files_rehashed': len(snapshot['payload']['units']),
        'source_spans_rehashed': sum(1 for r in records if r['record_type'].startswith('agtxiv.v3.source-span')),
        'full_record_set_valid': full.valid,
        'expected_blocker': f'{len(full.issues)} producer-authored correspondence maps rejected as SELF_REVIEW',
        'diagnostic_subset_valid': diagnostic.valid,
        'diagnostic_subset_records': len(subset),
        'proposed_obligations': len(ids),
        'scope_frozen': False,
        'proof_handoff_accepted': False,
        'dependency_handoff_accepted': True,
        'numerics_reproduced': False,
        'scientific_acceptance_checked': False,
        'interpretation': ('Exit 0 means the saved successes and the saved blockers both reproduce. '
                           'It does not mean AGENT.md S0-S5 completed, and it says nothing about whether '
                           'any claim of the paper is true.'),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
