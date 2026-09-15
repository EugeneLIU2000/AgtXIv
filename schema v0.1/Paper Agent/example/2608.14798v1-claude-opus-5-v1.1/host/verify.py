#!/usr/bin/env python3
"""Read-back checks for this retained run. Expected blockers stay failures.

Every check runs and is reported. A specification-version change is reported as
a finding rather than as an assertion that aborts the run: the 1.0 example's
pinned-spec assert fired first and hid its remaining checks, which is the one
thing this script is written not to repeat.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
SPECDIR = RUN_DIR.parents[1]
REPO = RUN_DIR.parents[3]
sys.path.insert(0, str(REPO / 'src'))
from agtxiv_v3.contracts import SchemaBundle, RecordSet, SuppliedArtifact, digest, exact_ref  # noqa: E402

SPEC_FILES = ['AGENT.md', 'INTERFACE.md', 'CONFORMANCE.md', 'extraction-draft.schema.json']


def main():
    findings, checks = [], {}
    manifest = json.loads((RUN_DIR / 'manifest.json').read_text())
    validation = json.loads((RUN_DIR / 'validation.json').read_text())
    records = json.loads((RUN_DIR / 'records.json').read_text())
    acquisition = json.loads((RUN_DIR / 'acquisition.json').read_text())
    bundle = SchemaBundle(REPO / 'schema v0.0')

    # 1. the specification this run was executed against
    drift = []
    for entry in manifest['spec_files']:
        name = Path(entry['path']).name
        current = digest((SPECDIR / name).read_bytes())
        if current != entry['sha256']:
            drift.append({'file': name, 'run': entry['sha256'], 'current': current})
    checks['spec_files_unchanged'] = not drift
    if drift:
        findings.append('Specification files changed after this run; the records are a run of the pinned '
                        'hashes in manifest.spec_files, not of the current files: '
                        + ', '.join(d['file'] for d in drift))

    # 2. schema bundle
    checks['schema_bundle_matches'] = manifest['schema_bundle_hash'] == bundle.bundle_hash
    if not checks['schema_bundle_matches']:
        findings.append('Pinned v0.0 schema bundle differs from the current one.')

    # 3. retained files
    bad_files = [f['path'] for f in manifest['files']
                 if not (RUN_DIR / f['path']).is_file()
                 or digest((RUN_DIR / f['path']).read_bytes()) != f['sha256']]
    checks['manifest_files_intact'] = not bad_files
    if bad_files:
        findings.append('Retained files changed or are missing: ' + ', '.join(bad_files[:5]))

    # 4. source bytes and every span digest
    source = REPO / acquisition['source_directory']
    artifacts, snapshot = [], next(r for r in records if r['record_type'].startswith('agtxiv.v3.source-snapshot'))
    for unit in snapshot['payload']['units']:
        raw = (source / unit['relative_path']).read_bytes()
        assert digest(raw) == unit['artifact']['sha256'], unit['relative_path']
        artifacts.append(SuppliedArtifact(unit['artifact']['artifact_id'], unit['artifact']['media_type'], raw))
    archive = snapshot['payload']['archive']
    artifacts.append(SuppliedArtifact(archive['artifact_id'], archive['media_type'],
                                      (REPO / acquisition['archive_path']).read_bytes()))
    tex = (source / 'Pauli_Spectrum.tex').read_bytes()
    spans = [r for r in records if r['record_type'].startswith('agtxiv.v3.source-span')]
    bad_spans = [r['record_id'] for r in spans
                 if digest(tex[r['payload']['byte_start']:r['payload']['byte_end']]) != r['payload']['span_sha256']]
    checks['source_bytes_and_spans_rehash'] = not bad_spans
    if bad_spans:
        findings.append('Span digests no longer match the source bytes: ' + ', '.join(bad_spans[:5]))

    # 5. record shapes, then the full set and the diagnostic subset
    checks['single_record_shapes_valid'] = all(not bundle.validate_record(r) for r in records)
    full = RecordSet(bundle, records, artifacts).validate(require_artifacts=True)
    subset_records = [r for r in records if not r['record_type'].startswith('agtxiv.v3.claim-component-map')]
    subset = RecordSet(bundle, subset_records, artifacts).validate(require_artifacts=True)
    codes = sorted({i.code for i in full.issues})
    expected_blocker = (not full.valid and codes == ['SELF_REVIEW']
                        and len(full.issues) == sum(1 for r in records
                                                    if r['record_type'].startswith('agtxiv.v3.claim-component-map')))
    checks['expected_self_review_blocker_reproduced'] = expected_blocker
    checks['diagnostic_subset_valid'] = subset.valid
    if not expected_blocker:
        findings.append(f'The recorded blocker did not reproduce exactly: codes={codes}, count={len(full.issues)}.')

    # 6. nothing was fabricated downstream of Paper
    forbidden = {'scope-decision', 'frozen-scope', 'obligation-disposition', 'argument-node',
                 'inference-step', 'proof-plan', 'formalization-packet', 'formalization-attempt',
                 'formal-check', 'release-manifest', 'paper-release'}
    present = {r['record_type'].removeprefix('agtxiv.v3.').removesuffix('/0.0.0') for r in records}
    checks['no_downstream_records_fabricated'] = not (present & forbidden)
    checks['no_result_receipt_written'] = not list(RUN_DIR.rglob('result.json'))
    checks['mode_is_offline_diagnostic'] = manifest['mode'] == 'OFFLINE_DIAGNOSTIC'

    # 7. the filling rules that the 1.0 run failed
    every_claim_has_conclusion = all(
        any(c['role'] == 'CONCLUSION' for c in r['payload']['components'])
        for r in records if r['record_type'].startswith('agtxiv.v3.scientific-claim'))
    sourced = [cond for r in records for field in ('conditions', 'assumptions')
               for cond in r['payload'].get(field, [])
               if cond['origin'] in {'SOURCE_EXPLICIT', 'SOURCE_RECONSTRUCTED'}]
    checks['every_claim_has_a_conclusion_component'] = every_claim_has_conclusion
    checks['every_source_condition_cites_a_span'] = all(c['source_span_refs'] for c in sourced)
    checks['no_agent_added_or_imported_premise'] = not [
        cond for r in records for field in ('conditions', 'assumptions')
        for cond in r['payload'].get(field, [])
        if cond['origin'] in {'AGENT_ADDED', 'IMPORTED'}]
    checks['drafts_declare_unestablished_only'] = all(
        r['payload']['review']['independence'] == 'UNESTABLISHED'
        for r in records if r['record_type'].startswith('agtxiv.v3.claim-component-map'))

    result = {
        'readback_version': 'paper-agent/1.1',
        'run': manifest['run_id'],
        'checks': checks,
        'findings': findings,
        'counts': {'records': len(records), 'spans_rehashed': len(spans),
                   'source_conditions_checked': len(sourced),
                   'full_set_issue_codes': codes, 'full_set_issue_count': len(full.issues),
                   'diagnostic_subset_records': len(subset_records)},
        'expected_blocker': '82 producer-authored correspondence maps rejected as SELF_REVIEW; AGENT.md 1.1 R8 requires keeping them and staying blocked',
        'interpretation': ('Exit 0 means every read-back check passed and the recorded success and failure '
                           'boundaries reproduced. It does NOT mean the extraction is faithful, that any '
                           'claim of the paper holds, or that a Paper Agent delivery was accepted.'),
        'not_established': validation['not_established'],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
