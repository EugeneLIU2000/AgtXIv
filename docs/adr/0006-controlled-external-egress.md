# ADR 0006: Controlled external Internet egress

- Decision status: Accepted
- Implementation status: Planned across M1.5, M2, and M3
- Milestone: M0
- Date: 2026-08-31
- Roadmap decision: D9
- Terminology: follows `docs/roadmaps/v2-end-to-end-implementation-plan.md` Section 2.1

## Context

AgtXIv must retrieve papers and may use a hosted model, but paper text, archives,
generated code, and model output are untrusted. Giving every worker general
Internet access would let hostile content fetch executable dependencies, contact
private infrastructure, leak credentials or restricted bytes, and bypass the
recorded acquisition and model-use policies. Saying that all network traffic is
forbidden would be equally incorrect because production databases, object stores,
queues, and authenticated internal services communicate over controlled networks.

The physical picture is a clean laboratory with two guarded exterior hatches.
One receiving hatch accepts packages from approved paper sources. One service
hatch sends an approved minimum payload to an optional hosted model. Internal
pipes connect laboratory rooms, but their valves are identity-bound and paper
content cannot redirect them. The build and release workshop has a separate
supply-chain loading dock governed by its own policy.

## Decision

Only two components in the paper-processing plane may initiate external Internet
egress:

1. **Acquisition worker.** It receives a normalized identifier, constructs a URL
   from an exact allowlisted endpoint policy, validates every address and redirect,
   applies byte/time/rate limits, and writes only quarantine records and objects.
   It has no signing, certification, review, archive, or knowledge-admission
   credential.
2. **Policy-enabled model gateway.** It may call one configured hosted provider
   only when the exact profile, rights disposition, retention policy, payload
   class, provider, and model permit the call. It sends the minimum approved
   payload and records request/response digests, provider/model revision, policy,
   retention setting, resource use, and attempt identity. It has no general CAS
   browsing, signing, review, or knowledge-admission authority.

A local-model adapter implements the same model contract without external egress.
Extraction, TeX/PDF handling, general analysis, generated-code execution, and
formal builds run offline. Paper or model content cannot choose a host, scheme,
port, redirect, provider, model, tool, internal service target, or credential.

Authenticated database, object-store, queue, and service traffic is internal
control-plane traffic. It uses workload identity, least-privilege service roles,
network allowlists, exact request targets, and audit records. CI and release
automation may access locked dependency and release endpoints under a separate
supply-chain egress policy; untrusted paper content is never an input to that
network authority.

## Consequences

### Positive

- Source retrieval and hosted-model use remain possible without granting paper
  content general network authority.
- Rights-restricted bytes cannot be sent to a provider merely because a model
  stage exists.
- Offline workers and formal builds are reproducible and cannot fetch floating
  dependencies during an attempt.
- Internal production communication is not confused with public Internet access.

### Costs and constraints

- Acquisition, hosted-model, internal-service, and CI/release policies need
  separate identities, allowlists, logs, tests, and incident response.
- DNS, redirect, private-address, proxy, and provider-retention controls must be
  enforced below the application layer as well as in code.
- A model call rejected by rights or egress policy produces a typed terminal
  result; it cannot silently fall back to an unrecorded provider.
- Online smoke tests remain separate from deterministic offline core validation.

## Invariants

1. Paper-processing components other than acquisition and the policy-enabled
   model gateway have no external Internet route.
2. The acquisition worker cannot fetch a caller-authored arbitrary URL and cannot
   write outside quarantine.
3. The model gateway cannot send a payload whose exact rights, profile, retention,
   provider, model, and data-use policy are not approved.
4. Paper and model content cannot expand external or internal allowlists or select
   a credential, tool, service endpoint, or dependency source.
5. Formal and generated-code builds are offline and use exact pre-frozen
   dependencies.
6. Internal-service calls bind authenticated workload identity, target, intent,
   policy, and idempotency information and are independently audited.
7. CI/release egress is governed separately and cannot be reached through a paper
   attempt.

## Acceptance tests

| Test | Expected result |
|---|---|
| Submit a caller URL pointing to loopback, private, link-local, metadata, alternate-port, or redirect target | Acquisition makes no disallowed connection and emits a stable evidence-bearing rejection. |
| Put a network command or dependency URL in TeX, PDF metadata, model output, or generated formal code | Offline worker cannot connect; the attempt records the policy/resource result. |
| Ask the hosted model stage to send a rights-forbidden source payload | Gateway rejects before transmission and records the exact policy reason. |
| Paper text asks to switch provider/model or call an internal database/object endpoint | Request is treated as untrusted content and cannot alter gateway or service routing. |
| Acquisition identity attempts release signing or admission | Authorization fails and is audited. |
| Internal worker calls its permitted object/database endpoint with a wrong workload identity or target | Service policy rejects the call; this does not open an external egress path. |
| Reproduce an offline fixture while live arXiv or the hosted provider is unavailable | Core validation and replay remain deterministic; only the separate online smoke lane is affected. |

## Related records

- `docs/roadmaps/v2-end-to-end-implementation-plan.md`, decision D9
- `docs/security/v2-threat-model.md`
- ADR 0001 for storage authority and quarantine promotion
- ADR 0002 for exact dependency and policy binding
- ADR 0004 for role and admission separation
