"""Frozen-obligation accounting against an explicit, finite record universe.

This is a contract/evidence check, never a scientific assessment or release
authorization. SOURCE and INVENTORY establish only source-byte and inventory
processing: neither can establish source fidelity of a scientific claim.
The caller must separately validate the complete RecordSet, including review
independence and authority. This module never calls RecordSet.validate(), so it
can also be used from its release-manifest/release-audit semantic checks.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import TYPE_CHECKING, Iterable

from .contracts import ContractError, validate_exact_ref

if TYPE_CHECKING:
    from .contracts import RecordSet


@dataclass(frozen=True)
class ObligationFinding:
    code: str
    record_id: str
    path: str
    message: str


@dataclass(frozen=True)
class ObligationReport:
    issues: tuple[ObligationFinding, ...]
    obligation_count: int
    universe_count: int
    artifact_checked: bool
    checked_artifact_count: int
    success_enforced: bool
    authority_checked: bool = False
    limitations: tuple[str, ...] = (
        'Checks only the explicitly supplied historical record universe.',
        'SOURCE/INVENTORY completion establishes processing, not scientific claim fidelity.',
        'Typed successful evidence is recorded evidence, not a new scientific assessment.',
        'Complete RecordSet semantics, independent identity and authority must be checked separately.',
        'CONTRIBUTION and RELEASE obligation stages are not implemented and fail closed.',
    )

    @property
    def valid(self) -> bool:
        return not self.issues


def _key(reference: dict) -> tuple:
    return tuple(reference[k] for k in ('record_type', 'record_id', 'revision', 'content_hash'))


def _ref(record: dict) -> dict:
    return {k: record[k] for k in ('record_type', 'record_id', 'revision', 'content_hash')}


def _kind(record: dict) -> str:
    # No catalog-size assumption or hard-coded schema version.
    return record['record_type'].split('/', 1)[0].rsplit('.', 1)[-1]


def _condition_key(condition: dict) -> str:
    # Independent conditions and their source anchors are sets. Reordering them
    # is harmless; changing an id, statement, origin, or exact anchor is not.
    value = dict(condition)
    if 'source_span_refs' in value:
        value['source_span_refs'] = sorted(value['source_span_refs'], key=_key)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def support_closure(references: Iterable[dict], get, *, accounting: bool = False) -> Iterable[dict]:
    """Resolve payload evidence edges, never envelope provenance or review history.

    Argument snapshots include their full declared node/inference/context/route,
    dependency and challenge inventories. Formal packets include the argument,
    target, environment and generation execution. Nested condition, comparison
    and rule witnesses are included. Scope/plan administration, prior revisions,
    derived-claim comparison parents and assessment frontiers are not premises.
    Completed assessed counterevidence is included; accounting also includes
    counterevidence used by nonpositive performed assessments. Merely retained
    counterevidence alongside positive support is not a support premise.
    Missing records are reported by the supplied resolver (the obligation checker
    supplies its universe-bounded get, not the global RecordSet resolver).
    """
    pending = list(references)
    seen = set()
    while pending:
        reference = pending.pop()
        record = get(reference)
        if record is None:
            continue
        key = _key(reference)
        if key in seen:
            continue
        seen.add(key)
        yield record
        excluded = {'review', 'scope_ref', 'previous_ref', 'predecessor_ref', 'frontier_refs'}
        if _kind(record) == 'derived-claim':
            excluded.add('parent_refs')
        if _kind(record) == 'work-attempt':
            excluded.add('plan_ref')
        if _kind(record) == 'axis-assessment':
            p = record['payload']
            if not (p['execution'] == 'COMPLETED' and p['method'] != 'UNASSESSED'
                    and (p['result'] == 'COUNTEREVIDENCE' or accounting
                         and p['result'] not in {'SUPPORTED', 'PARTIALLY_SUPPORTED', 'NOT_ASSESSED'})):
                excluded.add('counterevidence_refs')
        values = [v for k, v in record['payload'].items() if k not in excluded]
        while values:
            value = values.pop()
            if isinstance(value, dict):
                if set(value) == {'record_type', 'record_id', 'revision', 'content_hash'}:
                    pending.append(value)
                else:
                    values.extend(value.values())
            elif isinstance(value, list):
                values.extend(value)


class _Check:
    def __init__(self, store: RecordSet, universe_refs: Iterable[dict], require_artifacts: bool):
        self.store = store
        self.require_artifacts = require_artifacts
        self.issues: list[ObligationFinding] = []
        self.cache: dict[tuple, dict | None] = {}
        self.universe: dict[tuple, dict] = {}
        self.artifacts: set[tuple] = set()
        for reference in universe_refs:
            if not self.valid_reference(reference):
                continue
            key = _key(reference)
            if key in self.universe:
                self.fail('OBLIGATION_UNIVERSE_DUPLICATE', reference, 'universe_refs',
                          'The explicit historical universe repeats an exact record.')
            self.universe[key] = reference

    def fail(self, code: str, owner: dict, path: str, message: str) -> None:
        rid = owner.get('record_id', '') if isinstance(owner, dict) else ''
        finding = ObligationFinding(code, rid if isinstance(rid, str) else '', path, message)
        if finding not in self.issues:
            self.issues.append(finding)

    def valid_reference(self, reference: dict) -> bool:
        try:
            validate_exact_ref(reference)
        except ContractError as error:
            self.fail('OBLIGATION_EXACT_REFERENCE', reference, '', str(error))
            return False
        return True

    def get(self, reference: dict) -> dict | None:
        if not self.valid_reference(reference):
            return None
        key = _key(reference)
        if key in self.cache:
            return self.cache[key]
        if key not in self.universe:
            self.fail('OBLIGATION_OUTSIDE_UNIVERSE', reference, 'universe_refs',
                      'A required source, history, target, or evidence record is outside the explicit universe.')
            self.cache[key] = None
            return None
        try:
            record = self.store.resolve(reference)
        except (ValueError, KeyError, TypeError) as error:
            self.fail('OBLIGATION_EXACT_REFERENCE', reference, '', str(error))
            self.cache[key] = None
            return None
        shape_issues = self.store.bundle.validate_record(record)
        if shape_issues:
            self.fail('OBLIGATION_RECORD_INVALID', reference, '',
                      'Required record fails its dynamically selected schema or content hash.')
            self.cache[key] = None
            return None
        self.cache[key] = record
        if self.require_artifacts:
            self.check_artifacts(record['payload'], reference)
        return record

    def check_artifacts(self, value, owner: dict) -> None:
        if isinstance(value, dict):
            if {'artifact_id', 'sha256', 'byte_size', 'media_type'} <= value.keys():
                try:
                    self.store.artifact(value)
                    self.artifacts.add(tuple(value[k] for k in ('artifact_id', 'sha256', 'byte_size', 'media_type')))
                except (ValueError, KeyError, TypeError) as error:
                    self.fail('OBLIGATION_ARTIFACT', owner, 'payload', str(error))
            else:
                for item in value.values():
                    self.check_artifacts(item, owner)
        elif isinstance(value, list):
            for item in value:
                self.check_artifacts(item, owner)

    def target_conditions(self, target: dict, seen: set[tuple] | None = None) -> set[str]:
        seen = set() if seen is None else seen
        key = _key(_ref(target))
        if key in seen:
            return set()
        seen.add(key)
        p, name = target['payload'], _kind(target)
        result = {_condition_key(c) for field in ('conditions', 'added_conditions', 'assumptions')
                  for c in p.get(field, [])}
        # A derived claim's parents record provenance or comparison, not an
        # implicit inheritance of premises. A repair may intentionally broaden
        # an old pure-state claim to all states. Such a target must explicitly
        # retain any restriction through added_conditions if it still applies.
        parents = [p['claim_ref']] if name == 'math-claim' else []
        for reference in parents:
            parent = self.get(reference)
            if parent:
                result |= self.target_conditions(parent, seen)
        return result

    def evidence_conditions(self, evidence: dict, target_ref: dict) -> set[str]:
        p, name = evidence['payload'], _kind(evidence)
        result = {_condition_key(c) for field in ('conditions', 'assumptions') for c in p.get(field, [])}
        if name == 'formal-check':
            packet = self.get(p['packet_ref'])
            math = self.get(packet['payload']['math_ref']) if packet else None
            if math:
                result |= self.target_conditions(math)
        elif name == 'argument-review':
            snapshot = self.get(p['snapshot_ref'])
            for reference in snapshot['payload']['math_refs'] if snapshot else []:
                math = self.get(reference)
                if math and (reference == target_ref or math['payload']['claim_ref'] == target_ref):
                    result |= self.target_conditions(math)
        return result

    def no_added_conditions(self, assessment: dict, target: dict, support: list[dict]) -> bool:
        allowed = self.target_conditions(target)
        actual = self.evidence_conditions(assessment, _ref(target))
        for evidence in support:
            actual |= self.evidence_conditions(evidence, _ref(target))
        if not actual <= allowed:
            self.fail('OBLIGATION_NEW_CONDITIONS', assessment, 'payload.conditions',
                      'Success evidence adds or changes conditions absent from the exact frozen target; create and review a new target/scope.')
            return False
        return True

    def formal_matches(self, check: dict, target_ref: dict, scope_ref: dict, success: bool = True) -> bool:
        if _kind(check) != 'formal-check':
            return False
        p = check['payload']
        packet = self.get(p['packet_ref'])
        if not packet:
            return False
        q = packet['payload']
        if q['scope_ref'] != scope_ref or target_ref not in [q['math_ref'], *q['source_claim_refs'], p['packet_ref']]:
            return False
        attempt = self.get(p['attempt_ref'])
        environment = self.get(p['environment_ref'])
        if not attempt or not environment:
            return False
        if attempt['payload']['packet_ref'] != p['packet_ref'] or q['environment_ref'] != p['environment_ref']:
            return False
        if not success:
            return p['outcome'] in {'FAILED', 'KERNEL_CHECKED'}
        if p['outcome'] != 'KERNEL_CHECKED' or p['exit_code'] != 0 or p['placeholder_findings']:
            return False
        built = p['built_declarations']
        allowed = set(environment['payload']['allowed_axioms'])
        return (set(q['expected_declarations']) <= {d['name'] for d in built}
                and all(not d['is_axiom'] and set(d['axioms']) <= allowed for d in built))

    def assessment_matches(self, assessment: dict, target: dict, axis: str,
                           scope_ref: dict, success: bool, method: str | None = None) -> bool:
        if _kind(assessment) != 'axis-assessment':
            return False
        p, target_ref = assessment['payload'], _ref(target)
        counterexample_accounting = (not success and axis == 'mathematical_correctness'
                                    and p['method'] == 'COUNTEREXAMPLE_REVIEW' and p['result'] == 'COUNTEREVIDENCE')
        if (target_ref not in p['target_refs'] or p['axis'] != axis or p['execution'] != 'COMPLETED'
                or p['method'] == 'UNASSESSED' or (method is not None and p['method'] != method
                    and not (counterexample_accounting and method == 'ARGUMENT_REVIEW'))):
            return False
        if target_ref not in p['review']['reviewed_refs']:
            return False
        if success and (p['applicability'] != 'APPLICABLE' or p['result'] != 'SUPPORTED'):
            return False
        if not success and p['result'] == 'NOT_ASSESSED':
            return False
        references = p['support_refs']
        if not success and p['result'] not in {'SUPPORTED', 'PARTIALLY_SUPPORTED'}:
            references = references + p['counterevidence_refs']
        support = [record for reference in references if (record := self.get(reference))]
        method_axes = {'SOURCE_REVIEW': 'source_fidelity', 'ARGUMENT_REVIEW': 'mathematical_correctness',
                       'KERNEL_AND_ALIGNMENT': 'mathematical_correctness', 'FORMAL_ALIGNMENT': 'formal_alignment',
                       'SEMANTIC_REVIEW': 'semantic_applicability', 'EMPIRICAL_REVIEW': 'empirical_support',
                       'REPRODUCTION_REVIEW': 'computational_reproducibility',
                       'COUNTEREXAMPLE_REVIEW': 'mathematical_correctness'}
        if method_axes.get(p['method']) != axis:
            return False
        if p['method'] == 'SOURCE_REVIEW':
            matching = (_kind(target) == 'scientific-claim' and bool(target['payload']['source_span_refs'])
                        and all(any(_kind(e) == 'source-span' and _ref(e) == r for e in support)
                                for r in target['payload']['source_span_refs']))
        elif p['method'] == 'ARGUMENT_REVIEW':
            matching = False
            for evidence in support:
                if _kind(evidence) != 'argument-review':
                    continue
                q = evidence['payload']
                snapshot = self.get(q['snapshot_ref'])
                if not snapshot or snapshot['payload']['scope_ref'] != scope_ref:
                    continue
                s = snapshot['payload']
                # Conditions already present in the target are valid, although
                # genuinely conditional/incomplete evidence cannot give success.
                complete = q['outcome'] == 'SUPPORTED' and not q['open_obligation_ids'] and not q['open_challenge_refs'] and not s['missing_items']
                matching |= target_ref in s['source_claim_refs'] + s['math_refs'] and (complete or not success)
        elif p['method'] in {'KERNEL_AND_ALIGNMENT', 'FORMAL_ALIGNMENT'}:
            aligned = [e for e in support if _kind(e) == 'alignment-assessment'
                       and target_ref in e['payload']['source_refs'] + e['payload']['target_refs']
                       and (not success or (e['payload']['outcome'] == 'ALIGNED'
                            and all(c['relation'] == 'EQUIVALENT' for c in e['payload']['comparisons'])))]
            matching = bool(aligned)
            if p['method'] == 'KERNEL_AND_ALIGNMENT':
                matching = False
                for check in support:
                    if not self.formal_matches(check, target_ref, scope_ref, success):
                        continue
                    packet = self.get(check['payload']['packet_ref'])
                    expected = 'MATH_TO_FORMAL' if packet['payload']['math_ref'] == target_ref else 'SOURCE_TO_FORMAL'
                    matching |= any(a['payload']['comparison_kind'] == expected and target_ref in a['payload']['source_refs']
                                    and any(r in a['payload']['target_refs'] for r in [_ref(check), check['payload']['attempt_ref']]) for a in aligned)
        elif p['method'] == 'SEMANTIC_REVIEW':
            matching = any(_kind(e) == 'semantic-context' and (e['payload']['claim_ref'] == target_ref or _ref(e) == target_ref) for e in support)
        elif p['method'] == 'EMPIRICAL_REVIEW':
            matching = any(_kind(e) == 'empirical-evidence' and target_ref in e['payload']['target_refs'] for e in support)
        elif p['method'] == 'REPRODUCTION_REVIEW':
            matching = False
            for evidence in support:
                if _kind(evidence) != 'reproduction-record' or target_ref not in evidence['payload']['target_refs']:
                    continue
                q = evidence['payload']
                protocol = self.get(q['protocol_ref'])
                matching |= bool(protocol and protocol['payload']['scope_ref'] == scope_ref
                                 and (not success or q['outcome'] == 'REPRODUCED'))
        elif p['method'] == 'COUNTEREXAMPLE_REVIEW':
            matching = counterexample_accounting and any(
                _kind(e) == 'counterexample' and e['payload']['target_ref'] == target_ref
                for e in support)
        else:
            matching = False
        return bool(matching and (not success or self.no_added_conditions(assessment, target, support)))

    def completed(self, obligation: dict, disposition: dict, scope: dict, success: bool) -> None:
        owner, stage = _ref(disposition), obligation['stage']
        targets = [record for reference in obligation['target_refs'] if (record := self.get(reference))]
        results = [record for reference in disposition['payload']['result_refs'] if (record := self.get(reference))]
        if not targets or len(targets) != len(obligation['target_refs']):
            self.fail('OBLIGATION_TARGET_MISSING', owner, 'payload.result_refs', 'Completed work needs all exact frozen targets.')
            return
        closure = list(support_closure([_ref(r) for r in targets + results], self.get, accounting=not success))
        if (scope['data_class'] == 'OBSERVED' or disposition['data_class'] == 'OBSERVED') and any(
                record['data_class'] == 'SYNTHETIC' for record in closure):
            self.fail('OBLIGATION_SYNTHETIC_PROMOTION', owner, 'payload.result_refs',
                      'Observed obligation completion cannot be established with synthetic load-bearing target or evidence fixtures.')
        required = {'CLAIM': ('source_fidelity', 'SOURCE_REVIEW'),
                    'ARGUMENT': ('mathematical_correctness', 'ARGUMENT_REVIEW'),
                    'ALIGNMENT': ('formal_alignment', 'FORMAL_ALIGNMENT'),
                    'SEMANTICS': ('semantic_applicability', 'SEMANTIC_REVIEW'),
                    'EMPIRICAL': ('empirical_support', 'EMPIRICAL_REVIEW'),
                    'COMPUTATION': ('computational_reproducibility', 'REPRODUCTION_REVIEW')}
        axes = set(obligation['applicable_axes'])
        if stage in {'SOURCE', 'INVENTORY'}:
            plan = self.get(scope['payload']['plan_ref'])
            discovery = self.get(scope['payload']['discovery_ref'])
            decision = self.get(scope['payload']['decision_ref'])
            if not all([plan, discovery, decision]):
                return
            source = self.get(plan['payload']['source_ref'])
            structure = self.get(discovery['payload']['structure_ref'])
            accepted = (decision['payload']['decision'] == 'ACCEPT'
                        and decision['payload']['discovery_ref'] == _ref(discovery)
                        and _ref(discovery) in decision['payload']['review']['reviewed_refs']
                        and discovery['payload']['plan_ref'] == _ref(plan))
            units = set(obligation['source_unit_ids'])
            if stage == 'SOURCE':
                matching = bool(source and not source['payload']['missing_material'] and accepted
                                and all(_ref(t) == _ref(source) for t in targets)
                                and any(_ref(r) == _ref(source) for r in results)
                                and units <= set(plan['payload']['source_unit_ids'])
                                and units <= {u['unit_id'] for u in source['payload']['units']})
            else:
                matching = bool(source and structure and accepted and structure['payload']['source_ref'] == _ref(source)
                                and not structure['payload']['blockers'] and not structure['payload']['unclassified_unit_ids']
                                and not discovery['payload']['unclassified_unit_ids']
                                and all(_ref(t) in [_ref(structure), _ref(discovery)] for t in targets)
                                and any(_ref(r) == _ref(decision) for r in results)
                                and units <= set(discovery['payload']['classified_unit_ids']))
            if not matching:
                self.fail('OBLIGATION_STAGE_EVIDENCE', owner, 'payload.result_refs', f'{stage} needs exact completed source/inventory processing evidence.')
            # This process-axis exception never applies to a claim target.
            axes.discard('source_fidelity')
        elif stage == 'FORMAL':
            checks = [e for e in results if _kind(e) == 'formal-check']
            for assessment in results:
                if _kind(assessment) == 'axis-assessment':
                    checks.extend(e for r in assessment['payload']['support_refs'] if (e := self.get(r)) and _kind(e) == 'formal-check')
            for target in targets:
                matching = any(self.formal_matches(c, _ref(target), _ref(scope), success) for c in checks)
                if not matching:
                    self.fail('OBLIGATION_STAGE_EVIDENCE', owner, 'payload.result_refs', 'FORMAL completion needs an exact-target performed kernel check in this frozen scope; required success needs KERNEL_CHECKED.')
                if not any(self.assessment_matches(r, target, 'mathematical_correctness', _ref(scope), success, 'KERNEL_AND_ALIGNMENT') for r in results):
                    self.fail('OBLIGATION_AXIS_EVIDENCE', owner, 'payload.result_refs', 'FORMAL needs mathematical correctness evidence connecting the exact frozen target to the checked declaration.')
            axes.discard('mathematical_correctness')
        elif stage in required:
            axis, method = required[stage]
            axes.add(axis)
            for target in targets:
                if not any(self.assessment_matches(r, target, axis, _ref(scope), success, method) for r in results):
                    self.fail('OBLIGATION_STAGE_EVIDENCE', owner, 'payload.result_refs', f'{stage} needs a completed typed assessment for every exact target.')
            axes.discard(axis)
        else:
            self.fail('OBLIGATION_UNSUPPORTED_STAGE', owner, 'payload.result_refs', f'No implemented evidence rule for {stage}; completion fails closed.')
            return
        for axis in sorted(axes):
            for target in targets:
                if not any(self.assessment_matches(r, target, axis, _ref(scope), success) for r in results):
                    self.fail('OBLIGATION_AXIS_EVIDENCE', owner, 'payload.result_refs', f'Missing completed {axis} evidence for exact target {target["record_id"]}.')


def check_obligations(store: RecordSet, scope_ref: dict, disposition_refs: Iterable[dict], *,
                      universe_refs: Iterable[dict], enforce_success: bool = True,
                      require_artifacts: bool = True) -> ObligationReport:
    """Check one disposition head per frozen obligation within a fixed universe.

    ``universe_refs`` must be an explicit ledger cut or manifest record list. It
    must include required target/evidence records and complete previous_ref
    history. Future records in ``store`` outside this cut are never consulted.
    Forks in this cut cannot be silently selected away; they require a separately
    reviewed scope change. No currentness claim is made outside this supplied cut.

    Use ``enforce_success=False`` for a candidate manifest: a deferred required
    obligation is retainable, but claimed COMPLETED work still needs typed
    performed evidence. A positive audit uses True, which additionally requires
    every SUCCESS_REQUIRED obligation to have positive exact-target evidence.
    Ordinary ACCOUNT_FOR work can finish with inconclusive/negative assessment.

    With require_artifacts=True, raw artifacts on every inspected record are
    checked through store.artifact; False is explicitly reported as unchecked.
    Full graph validation and authority remain the caller's responsibility.
    """
    check = _Check(store, universe_refs, require_artifacts)
    scope = check.get(scope_ref)
    selected = list(disposition_refs)
    obligations = scope['payload']['obligations'] if scope and _kind(scope) == 'frozen-scope' else []
    if not scope or _kind(scope) != 'frozen-scope':
        check.fail('OBLIGATION_SCOPE', scope_ref, 'scope_ref', 'Expected an exact frozen scope in this universe.')
    frozen = {o['obligation_id']: o for o in obligations}
    chosen: dict[str, list[dict]] = {}
    known: dict[str, dict[tuple, dict]] = {oid: {} for oid in frozen}
    # Only disposition records are enumerated; unrelated future records in the
    # store cannot alter this historical universe's heads.
    for reference in check.universe.values():
        if _kind(reference) != 'obligation-disposition':
            continue
        record = check.get(reference)
        if record and record['payload']['scope_ref'] == scope_ref:
            oid = record['payload']['obligation_id']
            if oid in known:
                known[oid][_key(reference)] = record
    for reference in selected:
        record = check.get(reference)
        if not record:
            continue
        p = record['payload']
        if _kind(record) != 'obligation-disposition' or p.get('scope_ref') != scope_ref or p.get('obligation_id') not in frozen:
            check.fail('OBLIGATION_SELECTION', reference, 'disposition_refs', 'Selected disposition must belong to this exact frozen scope and obligation.')
            continue
        chosen.setdefault(p['obligation_id'], []).append(record)
    for oid, obligation in frozen.items():
        choices = chosen.get(oid, [])
        if len(choices) != 1:
            check.fail('OBLIGATION_CARDINALITY', scope_ref, 'disposition_refs', f'{oid} needs exactly one selected current disposition.')
            continue
        disposition = choices[0]
        predecessors = set()
        for record in known[oid].values():
            previous_ref = record['payload']['previous_ref']
            if previous_ref is None:
                continue
            previous = check.get(previous_ref)
            if not previous:
                continue
            if (_kind(previous) != 'obligation-disposition' or previous['payload']['scope_ref'] != scope_ref
                    or previous['payload']['obligation_id'] != oid):
                check.fail('OBLIGATION_HISTORY', _ref(record), 'payload.previous_ref', 'Disposition history cannot change its frozen scope or obligation.')
            else:
                predecessors.add(_key(previous_ref))
        heads = set(known[oid]) - predecessors
        if len(heads) != 1:
            check.fail('OBLIGATION_AMBIGUOUS_HEAD', scope_ref, 'disposition_refs', f'{oid} has {len(heads)} current branches in the explicit universe.')
        elif _key(_ref(disposition)) not in heads:
            check.fail('OBLIGATION_STALE_DISPOSITION', _ref(disposition), 'disposition_refs', f'{oid} selects a predecessor rather than its current head in this universe.')
        positive = enforce_success and obligation['requirement'] == 'SUCCESS_REQUIRED'
        if disposition['payload']['outcome'] != 'COMPLETED':
            if positive:
                check.fail('OBLIGATION_SUCCESS_REQUIRED', _ref(disposition), 'payload.outcome', f'{oid} requires successful completion before positive release audit.')
            continue
        check.completed(obligation, disposition, scope, positive)
    incomplete = {'OBLIGATION_ARTIFACT', 'OBLIGATION_EXACT_REFERENCE', 'OBLIGATION_RECORD_INVALID',
                  'OBLIGATION_OUTSIDE_UNIVERSE', 'OBLIGATION_SCOPE'}
    return ObligationReport(tuple(check.issues), len(obligations), len(check.universe),
                            require_artifacts and not any(i.code in incomplete for i in check.issues),
                            len(check.artifacts), enforce_success)
