## Summary

<!-- What problem does this change solve? Lead with observable behavior. -->

## Scope and exact versions

<!-- List affected software, contract, schema, database migration, paper source,
Paper Agent, producer environment, API, or knowledge-snapshot versions. Use
"none" where an axis is genuinely unaffected. -->

- Affected paths/components:
- Exact inputs or issue/ADR:
- Compatibility and supersession:

## Authority boundary

- [ ] I have not presented code merge as Paper Agent archive or Knowledge Base
      admission.
- [ ] I kept source fidelity, formal validity, and scientific applicability as
      separate states.
- [ ] I preserved blocked, unknown, failed, rejected, and conflicting evidence.
- [ ] This change does not rely on private chain-of-thought; public rationale and
      evidence are sufficient for review.

Scientific effect:

<!-- State "none", "candidate/evidence only", or identify the future independent
review required. CODEOWNERS approval is not scientific admission. -->

## Contract and persistence impact

- [ ] No persistent schema, canonicalization, hash, policy, or database change.
- [ ] Or: new exact schema/contract versions, fixtures, validators, migration,
      rollback/forward-repair, and compatibility notes are included.
- [ ] Published records and migrations were not modified in place or silently
      status-promoted.

Details:

## Generated artifacts and source rights

- [ ] No tracked generated output or external source bytes changed.
- [ ] Or: producer, exact inputs, regeneration command, no-write drift check,
      semantic diff, and output hashes are documented.
- [ ] Every external artifact has an exact source/version/hash and redistribution
      disposition; unresolved or restricted bytes are absent from public Git and
      CI artifacts.

Details and commands:

## Security and privacy

- [ ] Threat, network, sandbox, credential, signature, identity, model-use,
      rights, and data-retention impacts were considered.
- [ ] No secret, personal data, confidential review, restricted byte, or unsafe
      live endpoint was added.
- [ ] Security-sensitive details, if any, are being handled through a private
      GitHub security advisory.

Residual risks:

## Verification

Commands run and results:

```text
make check
```

<!-- Add focused, full, Lean, migration, browser, or adversarial checks as
applicable. Missing tools and known blockers must be named, not counted as pass. -->

## Review routing

- [ ] Code owner
- [ ] Contract/schema reviewer (if applicable)
- [ ] Database/migration reviewer (if applicable)
- [ ] Security/rights reviewer (if applicable)
- [ ] Independent scientific reviewer is required later for admission (if
      applicable; the production reviewer policy is currently unresolved)

## Open blockers

<!-- Name anything preventing merge, software release, package archive, or
Knowledge Base admission. The unresolved root license, copyright ownership,
DCO/CLA alternative, scientific-reviewer policy, and signature mechanism must
not be represented as completed by this template. -->
