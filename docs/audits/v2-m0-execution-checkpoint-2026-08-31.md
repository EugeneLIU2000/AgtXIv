# AgtXIv V2 M0 execution checkpoint

- Checkpoint status: PASS WITH NAMED BLOCKERS
- PASS scope: clean Python fast aggregate only
- M0 exit status: NOT COMPLETE
- Date: 2026-08-31
- Branch: `codex/agtxiv-v2`
- Clean verification commit: `f86b98f`
- Roadmap: `docs/roadmaps/v2-end-to-end-implementation-plan.md`
- Terminology: follows the roadmap Section 2.1

## 1. Outcome

This checkpoint records the first version-managed M0 execution slice. It proves
that the committed branch can reproduce its Python environment and run one
offline aggregate validation command from a clean worktree. It also records the
remaining blockers instead of calling M0 complete prematurely.

The intuitive distinction is between a clean laboratory bench and the completed
laboratory. The bench now has a pinned tool cabinet, one inspection switchboard,
and written custody rules. The production signing keys, independent staff,
external-source rights decisions, and all later V2 machinery do not yet exist.

## 2. Versioned commits

| Commit | Boundary |
|---|---|
| `0044d1a` | Reader-approved V2 end-to-end execution roadmap and M0--M8 exit gates |
| `13b8470` | Python/Node pins, `uv.lock`, `make` entry points, aggregate validation, tests, pull-request continuous integration (CI), and CI-gated Pages workflow |
| `942d07e` | Architecture Decision Records (ADR) 0001--0006, historical repository audit, threat model, and aligned external-egress boundary |
| `f86b98f` | Contribution, security, governance, release, generated-artifact, repository-settings, CODEOWNERS, and pull-request policies |

Only the named files in these commits were staged. Pre-existing modified and
untracked user files were not stashed, cleaned, reset, reformatted, or committed.

## 3. Clean-worktree reproduction

A detached worktree was created at `f86b98f`. It contained none of the primary
worktree's uncommitted V2 schemas, fixtures, tests, database prototype, demos,
slides, references, or other user material.

Commands:

```bash
make bootstrap UV_CACHE_DIR=/tmp/agtxiv-uv-cache
make check UV_CACHE_DIR=/tmp/agtxiv-uv-cache
git status --short
```

Observed results:

- Python: CPython 3.12.2 selected by `.python-version`;
- dependency lock: uv reported 24 packages audited from `uv.lock`;
- aggregate result: `PASS`;
- named checks: 9 `PASS`, 1 `KNOWN_STALE`, 0 `FAIL`, 0 `MISSING_TOOL`;
- clean committed pytest suite: `202 passed`;
- final Git status: empty;
- validator side effects on tracked historical evidence: none.

The exact `KNOWN_STALE` result is the Shellworld V1 run's mutable specification
binding:

```text
expected v1-bridge.md sha256: c9c7b46732d56c862f77b64304b5a24f312b36386e643f0c204949c426cd6b54
current  v1-bridge.md sha256: 0c8fcd49dca17c0f6f547182cc6143c466d90a343b9703bd0aaec67690233d13
```

It is recognized only when the validator reports that sole exact failure and all
reviewed hashes match. The legacy validator runs in a bounded temporary mirror,
so it cannot rewrite the historical `check-result.json`. Any other failure or
hash becomes `FAIL`.

## 4. Why the clean count is 202 rather than 234 or 244

The initial historical audit observed `234 passed` in the primary working tree.
After adding ten aggregate-runner tests, that same augmented working tree reports
`244 passed`. Those counts include pre-existing uncommitted V2 work in progress
(WIP), including additional schemas, fixtures, validator changes, and tests.

This branch deliberately did not claim or commit that work. At the clean
versioned commit, the pre-M0 repository contributes 192 tests and M0 adds 10,
giving 202. This is not a test deletion or hidden regression; it is the honest
difference between committed branch content and the uncommitted working-tree
state. The WIP needs its own inventory, independent review, authorization,
compatibility decision, and focused V2 commit before its additional tests can
become branch evidence.

The roadmap's current M0 exit text still names the historical `234-test`
baseline. That gate is unresolved: either the relevant pre-existing tests must
be independently reviewed and committed, or the roadmap must be versioned to
replace a mutable count with an exact test inventory and commit identity. Merely
quarantining the WIP would not satisfy the gate as currently written.

## 5. Broader local validation

On the primary working tree, the `full` aggregate profile completed with:

- 15 `PASS`;
- 1 exact Shellworld `KNOWN_STALE`;
- passing static site assembly;
- passing RootMath dynamic Lean build/placeholder/axiom audit;
- passing Varela dynamic Lean build/placeholder/axiom audit.

This is useful diagnostic evidence but is not presented as clean-branch release
evidence because the primary worktree contains the user's uncommitted changes and
local ignored Lean tools/caches. A clean-checkout Lean bootstrap and the missing
Stabilizerness dynamic validator remain named work.

## 6. Controls now versioned

- Python 3.12.2, Node 24.20.0, uv 0.10.0, direct Python dependencies, validation
  dependencies, and transitive packages are pinned.
- `make bootstrap`, `make check`, `make check-full`, and `make check-nightly`
  provide one documented entry surface.
- The aggregate validator distinguishes `PASS`, `KNOWN_STALE`,
  `EXPECTED_BLOCKED`, `FAIL`, `MISSING_TOOL`, and `SKIPPED`; it uses the active
  locked interpreter and defaults declared checks to offline operation.
- Pull-request continuous integration (CI) uses immutable action commit
  identifiers, complete Git history, the pinned Python/Node/uv versions, the fast
  aggregate profile, a static-site smoke test, and one stable `ci-required`
  result.
- Pages deployment is triggered only after the same pushed `main` commit passes
  AgtXIv CI; its write and identity-token permissions are confined to deployment.
- ADRs and governance now distinguish code merge, certified package archive, and
  independently reviewed per-entry knowledge admission.
- The threat model treats paper archives, TeX/PDF, model output, generated code,
  credentials, rights, roles, storage, signatures, and queries as separate trust
  boundaries.

## 7. Remaining M0 blockers

The roadmap remains the definitive M0 gate. The following observed blockers must
be resolved and evidenced; resolving this list alone cannot override an unmet
roadmap Deliver or Exit item:

1. the actual root license, copyright holder(s), and treatment of existing
   third-party/source material;
2. the inbound contribution mechanism: Developer Certificate of Origin (DCO),
   Contributor License Agreement (CLA), or another lawful policy;
3. at least one additional qualified code owner plus the specialist review
   capacity needed to avoid branch-rule deadlock;
4. an enabled and independently verified private vulnerability reporting path;
5. the scientific reviewer identity, qualification, conflict, quorum, appeal,
   and attestation policy;
6. the production signature suite, trust roots, key custody, rotation,
   compromise, and revocation policy;
7. remote branch protection and repository security settings verified against
   `docs/governance/repository-settings.md`;
8. the required `CODE_OF_CONDUCT` and `CITATION` files and their approved
   project-specific contents;
9. the missing CI lanes for formatting, static analysis, secret scanning,
   dependency scanning, and generated-file drift;
10. clean-checkout bootstrap for the pinned Lean/LeanQuantum inputs and a dynamic
   Stabilizerness validator;
11. a non-destructive compatibility contract/replay that supersedes, rather than
   edits, the stale Shellworld run;
12. an independently reviewed, authorized focused commit for the existing V2
    WIP, or an explicit decision to supersede or quarantine each of its files;
13. reconciliation of the roadmap's fixed `234-test` exit wording with a
    versioned exact test inventory and commit identity, unless the independently
    reviewed WIP is committed and establishes the intended baseline directly.

## 8. Non-implications

This checkpoint is not a V2 Paper Agent release, software release, cryptographic
certificate, rights clearance, scientific review, or knowledge admission. It
does not prove that arbitrary arXiv intake, whole-paper discovery, mathematical
formalization, the production database, or the live V2 demo is implemented. It
establishes a reproducible and reviewable foundation on which those milestones
can now be built.
