# Frozen model routing and reuse

The 2026-09-20 revision makes model choice a host decision before spending a call.
It implements the user's instruction to use smaller models for repeated source work.
It does not assert that a cheaper model has achieved equivalent extraction quality.

| Operation | Engine class | Model | Effort |
|---|---|---|---|
| `paper.extract` | LIGHT | `gpt-5.6-luna` | medium |
| `dependency.match` | DECISION | `gpt-5.6-terra` | medium |
| `autoformalization.failure_classify` | DECISION | `gpt-5.6-luna` | low |
| `autoformalization.lean` | HEAVY | `gpt-6-astra` | high |
| `autoformalization.premise` | HEAVY | `gpt-6-astra` | high |
| `autoformalization.lamport` (reserved operation) | HEAVY | `gpt-6-astra` | high |

Lamport steps currently share the Lean candidate call. Acquisition, bibliography
and ref parsing, exact byte location, exact-row deduplication, graph pruning, quotas
and Lean kernel execution are program operations and do not require an LLM router.
Library semantic search and PDF proof-context integration remain unfinished.

These model IDs are exposed by the installed Codex tooling; general model roles
were also consulted in the [official model catalog](https://developers.openai.com/api/docs/models).
Account-specific availability, actual served identity, quality and costs are not
inferred from catalog descriptions. No fallback silently inherits the account model.

New research, proof-walk and legacy-pipeline plans embed `environment.model_routing`.
The host checks its canonical digest, operation and engine class before reserving a
model slot. Changing the profile file does not change an existing plan. Plans without
a frozen route can still be read/audited, but the new dispatcher requires a new plan
before making further model calls. Old runtime snapshots and reports remain untouched.

Research defaults to `--extraction-profile LIGHT` (Luna). A new plan can explicitly
select `--extraction-profile LIGHT_TERRA` for harder source work, including only
failed ranges imported from a prior Luna dispatch. It changes only `paper.extract`;
dependency matching and proof routes keep their configured models. On resume, an
explicit profile different from the frozen one is rejected before dispatch. There
is no automatic promotion to Astra or mutation of a running plan.

Both Task and ModelReceipt record `actual_effort_requested` and `model_selection`
(policy version/hash, operation, profile, engine class, model, effort, reason).
Their values must match the frozen plan. Historical receipts are not retroactively
relabeled. `model_identity_attested_by_provider` stays false, cost stays null when
unknown, and `tier_savings_measured` stays false.

Citation/ref parsing proposes where to look. The semantic matcher receives both
frozen papers and compares the exact needed premise, assumptions and source quotes.
An unmatched implicit dependency remains unresolved. The graph retains unreviewed
support and origin boundaries; none of this is a proof certificate. The current
matcher emits one row per request, using `JOINT_SUPPORT` for multiple jointly needed
claims. More elaborate competing semantic routes remain outside that live interface.

For partial extraction continuation, add the following to an `--imports` manifest:

```json
{
  "candidates": {},
  "matches": [],
  "extraction_batches": {
    "arxiv:2607.26154v1": {"dispatch": "/absolute/prior/run/papers/arxiv-2607.26154v1/model-batches/dispatch.json"}
  }
}
```

Create a fresh output plan with the same source version and `--extract-focus-bytes`
as the prior dispatch (2048 for the existing 39-scope target run). The normal plan
constructor freezes the referenced dispatch. Complete paper candidate imports and
partial batch imports for the same paper are rejected as ambiguous. Batch reuse
requires positive focus size. `--max-extract-batches` bounds new dispatch attempts;
reused successful batches do not spend that budget or the global model-call budget.

`profiles/target-continuation-imports.json` was used by the actual
`research-luna-continuation-20260920` run: one target paper, 17 reused ranges and
22 new Luna calls, of which 20 returned admissible candidates and 2 failed exact
source-location constraints. The controller retained a 227-candidate graph and
finished with `CHAIN_INCOMPLETE`. `target-terra-continuation-imports.json` references
that new dispatch for a Terra plan restricted to its two remaining failed ranges.
That Terra plan completed both calls successfully, reused 37 successful ranges,
and retained 240 candidates in a 39,249,196-byte graph. All 39 output ranges now
have a candidate response; semantic completeness and the proof chain remain open.
Do not use a broader crawl to regenerate already completed
upstream work; import those paper artifacts separately when joining that phase.

`CANDIDATE_REUSED` carries an original result reference plus an immutable dispatch
origin. Source identity, scope ranges and successful response/receipt bytes must
match; chains are bounded to 16 dispatch levels and cycles are rejected. Reuse does
not establish semantic coverage. No BUSY worker is adopted or refunded. Failed
semantic matches in an old run still require explicit continuation planning; this
change does not implement a general recovery system for every stage.

Provider quota/auth/rate failures are typed and open a persistent SQLite-backed
plan circuit. Remaining new calls are not dispatched, while later successful old
batches may still be reused. New proof/premise reservations also stop before spending
an attempt slot; already retained identical-context proof evidence remains reusable.
There is no automatic retry, account switch, credit
redemption or expensive fallback. A human-visible provider error is not a reason to
discard successful work. Timeout and invalid candidate failures remain separate.

Graph/assembly artifacts now have a dedicated bounded 64 MiB reader with hash and
size binding; ordinary JSON evidence retains its 10 MiB bound. New graph publication
checks the bound before replacing graph pointers. The actual Luna continuation
retained and read a 35,099,488-byte graph and completed controller finalization;
the previous 10,617,299-byte graph failure was not rerun as a test.

The Luna source continuation is actual goal execution, not an independent test or
semantic acceptance. Negative paths, provider-circuit recovery and independent
artifact audits remain pending in `schema v0.1/PENDING_TESTS.md`, V03-78 onward.
Completed model ranges and Lean runs were not repeated for this revision. Cost
savings and source completeness remain unmeasured.
