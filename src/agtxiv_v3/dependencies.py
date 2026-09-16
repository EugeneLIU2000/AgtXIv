"""Offline potential impact over declared dependencies, never scientific status."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

from agtxiv_v3.contracts import (
    ContractError, RecordSet, canonical, digest, exact_ref, kind, ref_key,
)


@dataclass(frozen=True)
class ImpactReport:
    input_refs: tuple[dict, ...]
    input_hash: str
    payload: dict
    scope: str = 'SUPPLIED_DECLARED_DEPENDENCIES'
    authority_status: str = 'ORACLE_PROPOSED'
    scientific_status: str = 'UNVERIFIED'
    limitations: tuple[str, ...] = (
        'Potential reachability is not mathematical or scientific validity or invalidity.',
        'Only supplied dependency bindings and route-local inference uses are traversed; missing declarations remain unknown.',
        'Containment, claim correspondence, provenance and display links are not dependency edges.',
        'Affected axes label dependent outputs; the schema supplies no prerequisite-axis transfer function. Transitive axes are potential, not certain.',
        'Unreached proof routes are retained only relative to these declarations, not certified independent or valid.',
        'Artifacts and identity authority are not checked by this analysis; no scientific assessment is changed.',
    )


def inspect_dependencies(store: RecordSet, trigger_refs: Iterable[dict]) -> ImpactReport:
    """Inspect a contract-valid supplied RecordSet without executing any evidence.

    Every trigger must resolve exactly; new revisions never implicitly replace
    old ones. The report binds the entire supplied universe and sorted trigger
    set. Dependency bindings carry their explicit output axes. Inference uses
    carry only potential mathematical impact within each declaring proof route.
    Reaching one route's conclusion does not invalidate other routes sharing it,
    but explicit dependency bindings can declare cross-route uses. Long reasons
    are summarized with exact provenance retained in input_refs; excess target
    counts fail closed rather than returning a partial report.
    """
    store.validate(require_artifacts=False).require_valid()
    validator = store.bundle.validators['agtxiv.v3.impact-analysis/0.0.0']
    payload_schema = validator.schema['properties']['payload']
    affected_schema = payload_schema['properties']['affected']
    target_schema = store.bundle.registry.resolver().lookup(affected_schema['items']['$ref']).contents
    reason_limit = target_schema['properties']['reason']['maxLength']
    target_limit = affected_schema['maxItems']
    records = sorted(store.records, key=lambda r: ref_key(exact_ref(r)))
    references = {ref_key(exact_ref(r)): exact_ref(r) for r in records}
    triggers = {}
    for reference in trigger_refs:
        resolved = exact_ref(store.resolve(reference))
        triggers[ref_key(resolved)] = resolved
    if not triggers:
        raise ContractError('Impact analysis requires at least one exact trigger')
    routes = {ref_key(exact_ref(r)): r for r in records if kind(r) == 'proof-plan'}
    bindings = [r for r in records if kind(r) == 'dependency-binding']
    # Edges retain declaration identity and route, not generic reference closure.
    edges = defaultdict(list)

    def edge(source, target, route, axes, declaration, label):
        edges[ref_key(source)].append((ref_key(target), route, tuple(sorted(set(axes))),
                                       ref_key(declaration), label))

    for binding in bindings:
        p = binding['payload']
        route = ref_key(p['proof_plan_ref']) if p['proof_plan_ref'] else None
        edge(p['prerequisite_ref'], p['dependent_ref'], route, p['affected_axes'],
             exact_ref(binding), 'dependency-binding:' + p['kind'])
    for route, record in routes.items():
        for reference in record['payload']['inference_refs']:
            p = store.resolve(reference)['payload']
            sources = p['premise_refs'] + p['rule_evidence_refs'] + p['discharged_context_refs']
            if p['context_ref']:
                sources.append(p['context_ref'])
            # A changed inference declaration itself also requires route review.
            for source in sources + [reference]:
                edge(source, p['conclusion_ref'], route, ['mathematical_correctness'],
                     reference, 'inference-step:' + p['rule'])
    for outgoing in edges.values():
        outgoing.sort(key=lambda e: (e[0], e[1] or (), e[2], e[3], e[4]))
    queue = deque((key, None) for key in sorted(triggers))
    seen = set(queue)
    findings = {}
    reached_routes = set(triggers) & set(routes)
    while queue:
        source, current_route = queue.popleft()
        for target, edge_route, axes, declaration, label in edges[source]:
            # Shared inference nodes alone cannot transfer a route-local impact;
            # a binding, unlike sharing, explicitly declares the cross-route use.
            if (kind(references[declaration]) == 'inference-step' and current_route is not None
                    and edge_route is not None and current_route != edge_route):
                continue
            route = edge_route if edge_route is not None else current_route
            if route is not None:
                reached_routes.add(route)
            if target in routes:
                reached_routes.add(target)
            state = (target, route)
            if state not in findings and len(findings) >= target_limit:
                raise ContractError(f'Impact affected targets exceed schema maxItems {target_limit}; no partial report returned')
            finding = findings.setdefault(state, {'axes': set(), 'reasons': set()})
            finding['axes'].update(axes)
            finding['reasons'].add(
                f'Potential reachability through {label} {declaration[1]} revision {declaration[2]} '
                f'({declaration[3]}) from {source[1]} revision {source[2]} ({source[3]}).')
            if state not in seen:
                seen.add(state)
                queue.append(state)
    affected = []
    for (target, route), finding in sorted(findings.items(), key=lambda item: (item[0][0], item[0][1] or ())):
        reasons = sorted(finding['reasons'])
        reason = ' '.join(reasons)
        if len(reason) > reason_limit:
            reason = (f'Potential reachability through {len(reasons)} declared uses. '
                      'Detailed explanations summarized to respect schema bounds; '
                      'full exact declaration provenance is retained in input_refs. '
                      f'Canonical sorted explanation list hash: {digest(canonical(reasons))}.')
        affected.append({'target_ref': references[target], 'axes': sorted(finding['axes']),
                         'proof_plan_ref': references[route] if route else None,
                         'reason': reason})
    inputs = tuple(references[key] for key in sorted(references))
    payload = {
        'trigger_refs': [triggers[key] for key in sorted(triggers)],
        'dependency_refs': [exact_ref(r) for r in bindings],
        'affected': affected,
        'unaffected_proof_plan_refs': [references[key] for key in sorted(set(routes) - reached_routes)],
        'algorithm': 'agtxiv-v3-potential-declared-impact/2',
    }
    error = next(validator.evolve(schema=payload_schema).iter_errors(payload), None)
    if error is not None:
        path = '/'.join(str(part) for part in error.absolute_path)
        raise ContractError(f'Impact payload violates schema {error.validator} at {path}; no report returned')
    binding = {'input_refs': list(inputs), 'trigger_refs': payload['trigger_refs'],
               'algorithm': payload['algorithm']}
    return ImpactReport(inputs, digest(canonical(binding)), payload)
