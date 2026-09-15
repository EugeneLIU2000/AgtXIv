#!/usr/bin/env python3
"""Interface checks for this run: what the contracts accept, and exactly where they stop.

Every result here is produced by running the repository's own validators over
records or tasks built in this file. Nothing is asserted that the validators
were not asked. Probe records are labelled as probes and are NOT part of the
delivered record set.
"""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE.parents[2]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'src'))
from agtxiv_v3.contracts import SchemaBundle, RecordSet, SuppliedArtifact, digest, exact_ref  # noqa: E402

spec = importlib.util.spec_from_file_location('validate_v01', SPEC / 'validate.py')
V01 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V01)

RUN = 'opus5-2608.14798v1'
PRINCIPAL = f'session:{RUN}'
OTHER = f'session:{RUN}-hypothetical-second-principal'
RUN_AT = '2026-09-13T00:00:00Z'
BUNDLE = SchemaBundle(REPO / 'schema v0.0')


def producer(role, principal=PRINCIPAL, execution='exec:probe', visible=()):
    return {'principal_id': principal, 'role': role, 'actor_kind': 'AGENT',
            'identity_assurance': 'DECLARED', 'execution_id': execution,
            'model': 'claude-opus-5', 'visible_input_refs': list(visible), 'identity_evidence': []}


def codes(records, artifacts=()):
    report = RecordSet(BUNDLE, records, list(artifacts)).validate(require_artifacts=bool(artifacts))
    return sorted({i.code for i in report.issues}), [f'{i.code} {i.record_id}{i.path}: {i.message}' for i in report.issues]


def probe_codes(delivered, probe):
    """Validate one probe record inside the real reference closure, then report only its own issues.

    Byte artifacts are not supplied here: these probes are about review boundaries,
    not about source bytes, which the full record-set check already covers.
    """
    report = RecordSet(BUNDLE, list(delivered) + [probe]).validate(require_artifacts=False)
    mine = [i for i in report.issues if i.record_id == probe['record_id']]
    return sorted({i.code for i in mine}), [f'{i.code}{i.path}: {i.message}' for i in mine]


def plan_compatibility(out, records):
    """AGENT.md section 3 fixes a 12-field plan. The pinned v0.0 schema does not accept it."""
    plan = next(r for r in records if r['record_type'].startswith('agtxiv.v3.agentization-plan'))
    slim = json.loads(json.dumps(plan))
    slim['record_id'] = f'plan:{RUN}/as-agent-md-specifies'
    for dropped in ('created_at', 'data_class'):
        slim.pop(dropped, None)
    for dropped in ('max_seconds', 'max_cost_units'):
        slim['payload'].pop(dropped, None)
    slim['payload']['trigger_note'] = (
        'Plan carrying exactly the fields AGENT.md section 3 declares finalized. Kept as an '
        'unsigned, unadopted compatibility sample; it is NOT the plan this run used.')
    slim.pop('content_hash', None)
    issues = BUNDLE.validate_record(slim)
    (out / 'plan-as-agent-md-specifies.INVALID.json').write_text(
        json.dumps(slim, ensure_ascii=False, indent=1) + '\n')
    return {
        'question': 'Does a plan carrying exactly the 12 fields AGENT.md section 3 finalizes validate against the pinned v0.0 agentization-plan schema?',
        'answer': 'No.',
        'validator': 'agtxiv_v3.contracts.SchemaBundle.validate_record over schema v0.0',
        'issues': [f'{i.code} {i.path}: {i.message}' for i in issues],
        'note': ('AGENT.md defers created_at to an event log, data_class to a producer tag, and drops '
                 'max_seconds/max_cost_units as redundant with max_steps. The v0.0 schema requires all '
                 'four. The plan actually used in this run therefore carries declared placeholders in '
                 'the two budget fields, stated as such in its trigger_note.'),
    }


def review_gate_probes(records):  # noqa: C901
    """Where the AGENT.md working stages stop for a single-principal execution."""
    claim = next(r for r in records if r['record_type'].startswith('agtxiv.v3.scientific-claim'))
    discovery = next(r for r in records if r['record_type'].startswith('agtxiv.v3.inventory-discovery'))
    claim_ref, discovery_ref = exact_ref(claim), exact_ref(discovery)
    policy_ref = claim['policy_ref']
    probes = []

    def map_probe(principal, label):
        record = BUNDLE.make_record('claim-component-map', f'probe:{RUN}/map-{label}', {
            'claim_ref': claim_ref,
            'mappings': [{'component_id': component['component_id'],
                          'math_refs': [], 'semantic_refs': [], 'evidence_refs': [],
                          'disposition': 'RESIDUAL', 'residual': 'Probe record. Not an extraction result.'}
                         for component in claim['payload']['components']],
            'review': {'reviewed_refs': [claim_ref], 'producer_principal_ids': [PRINCIPAL],
                       'independence': 'UNESTABLISHED',
                       'conflicts': ['Probe record built only to locate the contract boundary.'],
                       'method': 'Probe.', 'evidence_refs': []},
            'coverage': 'PARTIAL',
        }, producer=producer('CLAIM_PRODUCER', principal, visible=[claim_ref]),
            policy_ref=policy_ref, input_refs=[claim_ref], created_at=RUN_AT)
        return probe_codes(records, record)

    same, same_detail = map_probe(PRINCIPAL, 'same-principal')
    other, other_detail = map_probe(OTHER, 'distinct-principal')
    probes.append({
        'probe': 'claim-component-map review boundary',
        'agent_md_requirement': 'S3: at least one scientific-claim per obligation, each with a claim-component-map.',
        'schema_fact': 'claim-component-map.payload.review is required and ReviewContext requires at least one reviewed_ref and one producer_principal_id.',
        'same_principal_as_claim': {'issue_codes': same, 'issues': same_detail},
        'distinct_principal': {'issue_codes': other, 'issues': other_detail},
        'conclusion': ('A correspondence map is rejected as SELF_REVIEW whenever its producer is the '
                       'principal that produced the claim, and accepted as soon as the principal differs. '
                       'There is no third option: the review block cannot be omitted or nulled. A Paper '
                       'Agent run carried out by a single principal therefore cannot deliver a valid '
                       'record set, and this run did not manufacture a second principal to avoid that.'),
    })

    def scope_probe(principal, independence, decision, label):
        try:
            record = BUNDLE.make_record('scope-decision', f'probe:{RUN}/scope-{label}', {
                'discovery_ref': discovery_ref,
                'review': {'reviewed_refs': [discovery_ref], 'producer_principal_ids': [PRINCIPAL],
                           'independence': independence,
                           'conflicts': ['Probe record built only to locate the contract boundary.'],
                           'method': 'Probe.', 'evidence_refs': []},
                'decision': decision,
                'reason': 'Probe record. Not a scope decision of this run.',
            }, producer=producer('SCOPE_REVIEWER', principal, visible=[discovery_ref]),
                policy_ref=policy_ref, input_refs=[discovery_ref], created_at=RUN_AT)
        except Exception as error:  # shape rejection
            return ['SHAPE_REJECTED'], [str(error)]
        return probe_codes(records, record)

    variants = {
        'same-principal-accept-unestablished': scope_probe(PRINCIPAL, 'UNESTABLISHED', 'ACCEPT', 'a'),
        'same-principal-block-unestablished': scope_probe(PRINCIPAL, 'UNESTABLISHED', 'BLOCK', 'b'),
        'distinct-principal-accept-unestablished': scope_probe(OTHER, 'UNESTABLISHED', 'ACCEPT', 'c'),
        'distinct-principal-accept-role-separated': scope_probe(OTHER, 'ROLE_SEPARATED', 'ACCEPT', 'd'),
    }
    probes.append({
        'probe': 'scope-decision and the reachability of frozen-scope',
        'agent_md_requirement': 'S2: the discoverer proposes the obligation count; an independent reviewer signs it; the count is locked as frozen-scope.',
        'schema_fact': ('frozen-scope requires an accepting scope-decision; a scope-decision carries a required '
                        'review block; a positive outcome with independence UNESTABLISHED is rejected.'),
        'variants': {k: {'issue_codes': v[0], 'issues': v[1]} for k, v in variants.items()},
        'conclusion': ('An ACCEPT is reachable only from a principal other than the discoverer AND with an '
                       'independence stronger than UNESTABLISHED. This run had neither, so it produced no '
                       'scope-decision and no frozen-scope, and the obligation denominator stays proposed.'),
    })
    return probes


def handoff(records, out):
    """AGENT.md S4 pairs a to-proof and a to-dependency Task. Only one of them can be built here."""
    contracts = V01.Contracts(SPEC)
    by_type = {}
    for record in records:
        by_type.setdefault(record['record_type'], []).append(record)

    def ref(rtype, index=0):
        return exact_ref(by_type['agtxiv.v3.' + rtype + '/0.0.0'][index])

    limits = {'max_attempts': 4, 'max_seconds': 3600, 'max_cost_units': 0, 'no_progress_limit': 2}
    math_refs = [exact_ref(r) for r in by_type['agtxiv.v3.math-claim/0.0.0'][:3]]
    claim_refs = [exact_ref(r) for r in by_type['agtxiv.v3.scientific-claim/0.0.0'][:3]]
    common_inputs = [ref('source-snapshot'), ref('processing-profile'), ref('authority-policy')]

    dependency_task = {
        'contract_version': '0.1.0', 'task_id': f'task.{RUN}.dependency-search',
        'agent': 'dependency', 'operation': 'dependency.search',
        'brief': ('Retrieve and bind the citation leads recorded for this paper: the imported stabilizer '
                  'Renyi entropy and nullity definitions, the nu-compressible equivalence, the Haar '
                  'Pauli-spectrum density, the Bell-sampling moment primitive, and the stabilizer-fidelity '
                  'lower bound whose printed form this run recorded as inconsistent. Citation or topical '
                  'similarity is not mathematical dependence; bind only what the exact conditions support.'),
        'target_refs': claim_refs, 'input_refs': common_inputs + claim_refs + math_refs,
        'input_artifacts': [], 'depends_on': [],
        'expected_record_types': ['dependency-binding', 'frontier-item'],
        'limits': limits, 'acceptance': 'DELIVERY',
        'exclusions': [], 'capabilities': ['records.read', 'dependency.search', 'candidates.propose'],
    }
    proof_task = {
        'contract_version': '0.1.0', 'task_id': f'task.{RUN}.proof-expand',
        'agent': 'proof', 'operation': 'proof.expand',
        'brief': ('Expand the mathematical targets extracted from this paper. Cannot be dispatched: the '
                  'operation requires a frozen-scope, which this run could not produce.'),
        'target_refs': math_refs, 'input_refs': common_inputs + math_refs + claim_refs,
        'input_artifacts': [], 'depends_on': [],
        'expected_record_types': ['argument-node', 'inference-step', 'proof-plan', 'frontier-item'],
        'limits': limits, 'acceptance': 'DELIVERY',
        'exclusions': [], 'capabilities': ['records.read', 'argument.expand', 'candidates.propose'],
    }
    results = {}
    for name, task in (('dependency-search', dependency_task), ('proof-expand', proof_task)):
        try:
            contracts.task(task)
            results[name] = {'accepted': True, 'error': None}
        except Exception as error:
            results[name] = {'accepted': False, 'error': str(error)}
    (out / 'handoff' / 'task-dependency-search.json').write_text(
        json.dumps(dependency_task, ensure_ascii=False, indent=1) + '\n')
    (out / 'handoff' / 'task-proof-expand.BLOCKED.json').write_text(
        json.dumps(proof_task, ensure_ascii=False, indent=1) + '\n')
    return {
        'validator': "schema v0.1/validate.py Contracts.task()",
        'results': results,
        'same_hash_rule': ('AGENT.md section 6 requires the to-proof and to-dependency Tasks to reference the '
                           'identical claim revision, math-target revision and frozen-scope hash. There is no '
                           'frozen-scope hash in this run, so the pair cannot be formed even though one half '
                           'of it validates on its own.'),
        'dispatched': False,
        'note': 'Both Task documents are drafts. Neither was scheduled, and no Result receipt exists.',
    }


def main():
    out = HERE / 'output'
    (out / 'handoff').mkdir(parents=True, exist_ok=True)
    records = json.loads((out / 'records.json').read_text())
    acq = json.loads((HERE / 'acquisition.json').read_text())
    source = REPO / acq['source_directory']
    snapshot = next(r for r in records if r['record_type'].startswith('agtxiv.v3.source-snapshot'))
    artifacts = []
    for unit in snapshot['payload']['units']:
        artifacts.append(SuppliedArtifact(unit['artifact']['artifact_id'], unit['artifact']['media_type'],
                                          (source / unit['relative_path']).read_bytes()))
    archive = snapshot['payload']['archive']
    artifacts.append(SuppliedArtifact(archive['artifact_id'], archive['media_type'],
                                      (REPO / acq['archive_path']).read_bytes()))

    full_codes, full_issues = codes(records, artifacts)
    without_maps = [r for r in records if not r['record_type'].startswith('agtxiv.v3.claim-component-map')]
    subset_codes, subset_issues = codes(without_maps, artifacts)
    (out / 'records-without-maps.json').write_text(
        json.dumps(without_maps, ensure_ascii=False, indent=1) + '\n')

    report = {
        'run': RUN,
        'scope': 'CONTRACT_AND_INTERFACE_CHECKS_ONLY',
        'full_record_set': {'records': len(records), 'valid': not full_codes,
                            'issue_codes': full_codes, 'issue_count': len(full_issues)},
        'diagnostic_subset_without_correspondence_maps': {
            'records': len(without_maps), 'valid': not subset_codes, 'issue_codes': subset_codes,
            'meaning': ('Everything except the producer-authored correspondence maps closes: every exact '
                        'reference resolves, every source span re-hashes against the real paper bytes, and '
                        'every record shape is accepted. This subset is a diagnostic, not a Paper Agent '
                        'deliverable, because AGENT.md S3 requires a correspondence map per obligation.')},
        'plan_compatibility': plan_compatibility(out, records),
        'review_gate_probes': review_gate_probes(records),
        'handoff': handoff(records, out),
        'not_established': [
            'No claim of the paper was checked for truth.',
            'No mathematical target was proved, disproved or formalized.',
            'No numerical result of the paper was reproduced; nothing was executed against the physics.',
            'No cited work was retrieved, so every attribution is to the citing text only.',
            'No identity was authenticated; identity_assurance is DECLARED on every record.',
        ],
    }
    (out / 'interface-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({
        'full_record_set_valid': report['full_record_set']['valid'],
        'full_issue_codes': report['full_record_set']['issue_codes'],
        'full_issue_count': report['full_record_set']['issue_count'],
        'subset_valid': report['diagnostic_subset_without_correspondence_maps']['valid'],
        'agent_md_plan_accepted_by_v0_0_schema': not report['plan_compatibility']['issues'],
        'handoff': {k: v['accepted'] for k, v in report['handoff']['results'].items()},
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
