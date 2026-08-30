# ADR 0002: Immutable contract bundle binding

- Decision status: Accepted
- Implementation status: Planned across M1 and M6
- Milestone: M0
- Date: 2026-08-31
- Roadmap decision: D2
- Terminology: follows `docs/roadmaps/v2-end-to-end-implementation-plan.md` Section 2.1

## Context

A recorded run currently binds `docs/specifications/v1-bridge.md` by hashing the
working-tree file. The Shellworld run expected
`c9c7b46732d56c862f77b64304b5a24f312b36386e643f0c204949c426cd6b54`,
while the current file hashes to
`0c8fcd49dca17c0f6f547182cc6143c466d90a343b9703bd0aaec67690233d13`.
The scientific output did not necessarily change; the validator is correctly
showing that the run's contract input is no longer recoverable from a mutable
path alone.

The intuition is a compiler build. Recording "compiled with the current header"
is not reproducible; the build must name the exact header bytes, compiler,
options, and dependency graph. AgtXIv needs the same rule for schemas, policies,
validators, adapters, environments, and readable specifications.

## Decision

Every V2 attempt binds exactly one immutable `ContractBundleRelease`. The release
contains canonical identities and hashes for:

- JSON Schemas and canonicalization profiles;
- the selected `AgentizationProfile` and `ArtifactFamilyCatalog`;
- cross-record validators, policy code, and stable error-code catalog;
- adapters and V1-to-V2 migrations that affect interpretation;
- environment manifests, formal toolchains, and dependency locks;
- Git commit and blob identifiers plus byte hashes for human-readable
  specifications;
- the signature policy described below.

The bundle has its own version, canonical content hash, release identity, and
supersession relationship. A run records the exact bundle identity and hash; no
authoritative field may resolve to `latest` at verification time.

The bundle also pins the signature suite:

- algorithm and canonical signed payload;
- actor and key identities and their permitted roles;
- trust roots and verification implementation;
- issuance time and applicable trust-policy revision;
- key rotation, expiry, revocation, and compromise rules;
- the evidence required for offline historical validation.

Human-readable paths remain navigation aids. Their Git blob and byte hash are
part of the bundle, so a later documentation edit creates a new contract release
rather than retroactively changing an old run.

The existing Shellworld run is historical evidence and is not rewritten. M0
records the mismatch. A future repair must either recover the exact expected blob
and publish a V1 compatibility contract release, or create a new replay/superseding
run bound to a new release. It must not replace the expected hash in the old
manifest merely to make the validator green.

## Consequences

### Positive

- A validator can explain exactly which rules governed a run.
- Documentation, schema, validator, and environment drift become visible instead
  of silently reinterpreting historical output.
- An offline verifier does not depend on the current branch or network.
- Key rotation can preserve historical validity without allowing a revoked key to
  certify new releases.

### Costs and constraints

- Contract releases require a deterministic build and generated-file drift check.
- A semantically relevant edit requires a new contract release and migration
  impact statement.
- The project must preserve or make retrievable every released bundle and its
  applicable trust-policy evidence.
- Recovery of the stale V1 run may produce an explicit unresolved historical
  result if the original bytes cannot be recovered.

## Invariants

1. Every V2 run has exactly one exact `ContractBundleRelease` reference.
2. A release contains no mutable or implicit dependency, including `latest`, a
   floating Git branch, an unpinned package range, or an unversioned policy.
3. Verification resolves by identity and digest, then checks bytes; it never
   substitutes the current file at the same path.
4. Canonicalization rules are inside the contract boundary, because changing
   serialization can change every record hash.
5. A signature is valid only for the exact canonical payload, role, policy, and
   trust state that applied at issuance.
6. Revocation and compromise records are append-only and cannot erase the signed
   historical object.
7. Superseding a contract or run does not mutate or upgrade the predecessor.

## Acceptance tests

| Test | Expected result |
|---|---|
| Validate a run after changing a referenced specification at the same path | Verification reports a precise digest mismatch and does not use the new bytes. |
| Replay with the original contract bundle while the current branch differs | Replay uses the pinned bundle and produces the original canonical results. |
| Put `latest`, a branch name, or an unpinned dependency in an authoritative ref | Contract validation fails closed with a stable error code. |
| Modify a schema, validator, catalog, or canonicalization profile without rebuilding the release | Generated-drift/contract-hash checks fail. |
| Verify a signature after normal key rotation | Historical verification succeeds under the issuance-time policy; the old key cannot sign a new release. |
| Verify a release signed after the key's compromise/revocation boundary | Certification fails and records the applicable trust decision. |
| Run the current Shellworld validator | The expected `c9c7…` versus current `0c8f…` mismatch remains an intentional named M0 failure until a non-destructive supersession/replay exists. |

## Related records

- `docs/roadmaps/v2-end-to-end-implementation-plan.md`, decision D2
- ADR 0001 for the canonical replay bundle
- `docs/audits/v2-m0-baseline.md` for the observed Shellworld mismatch
- `docs/security/v2-threat-model.md` for signing-key and trust-root threats
