# Host Probe: What of v0.2 Already Runs, and What It Costs

Date: 2026-09-17. Status: **a probe, not a host.** These scripts were written to measure the
real cost of `HOST.md` section 6 item 1 — "independent v0.2 schema registration, cross-object
checks, source resolution, and a minimal blob/index write entry point". They are not a v0.2
runtime, they make **no model call**, and nothing here produces a v0.2 Agent execution.

Everything below was executed. Nothing is estimated.

## What was measured

| Component | File | Result |
|---|---|---|
| Offline schema registry | `registry.py` | **109 `$ref`s walked, 0 unresolved.** Registers the five v0.2 schemas separately; it does not touch the v0.1 root loader, which hard-asserts exactly five files. |
| Cross-object checks (SHAPE, REFERENCES) | `check_output.py` | **13 of 13 negative cases rejected.** Fixtures in `negative/`. |
| Source locator resolution | `resolve.py`, `test_resolve.py` | **3 of 3 refusal cases correct.** Two real theorem locators resolved from the target paper; a third correctly refused. |
| Blob store, ledger, atomic commit, cross-process read-back | `store.py`, `e2e.py` | Commit and read-back verified from a separate process. |
| `run.json` honesty gates | `e2e.py` | The contract refuses a faked success. See below. |
| Pinned spec index, rendered for any model | `spec_index.py` | **16 entries pinned by hash; 9 rendered into the prompt, 7 identity-only.** The whole protocol renders to 58,155 bytes — roughly 14.5k tokens. |
| Provider-neutral model adapter | `adapter.py`, `profiles/` | **Four providers render a real request with no credential at all.** Anthropic, Gemini, any OpenAI-compatible endpoint, and a locally run model. |
| Lineage checks | `lineage.py`, `test_lineage.py` | **8 of 8 lineage failures rejected**, including a receipt that names a different producer than the ledger does. |
| Phase gate | `verify_phase.py` | Re-hashes every blob and traces every consumed item to its producing run; **correctly refuses to call the extract phase reached**, because no model has been called. |
| Per-paper cost model | `cost.py` | **≈$9.5 per paper** to extract and depend on all 25 claims and formalize one; **≈$39** to formalize all. **82% of all input is the same 14.5k-token spec prefix**, sent 66 times. |
| Macro table extraction | `expand.py` | **42 of the paper's own macros recovered**, `\Mcal` to `\mathcal M` among them. 45 control sequences reported unresolved rather than guessed. |

## Run it

From the repository root, with the project virtualenv:

```bash
.venv/bin/python 'schema v0.2/host_probe/registry.py'
.venv/bin/python 'schema v0.2/host_probe/spec_index.py' paper.extract
.venv/bin/python 'schema v0.2/host_probe/adapter.py'
.venv/bin/python 'schema v0.2/host_probe/test_adapter.py'
.venv/bin/python 'schema v0.2/host_probe/test_resolve.py'
.venv/bin/python 'schema v0.2/host_probe/check_output.py' 'schema v0.2/examples/paper-minimal/output.json' paper_text
.venv/bin/python 'schema v0.2/host_probe/test_lineage.py'
.venv/bin/python 'schema v0.2/host_probe/expand.py'
.venv/bin/python 'schema v0.2/host_probe/cost.py'
.venv/bin/python 'schema v0.2/host_probe/e2e.py'
```

`e2e.py` writes `e2e.sqlite` beside itself. Delete it to start clean. Then gate it:

```bash
.venv/bin/python 'schema v0.2/host_probe/verify_phase.py' --store 'schema v0.2/host_probe/e2e.sqlite' --through extract
```

It exits non-zero with `PHASE_NOT_REACHED`, which is the right answer: the store is internally
sound but holds no `COMMITTED` `paper.extract` run, because no model has been called.

## The ten negative cases

`check_output.py` rejects each of these. A checker that only ever reports PASS establishes
nothing, so the fixtures are kept alongside the code:

unknown root field · duplicate `item.id` · dangling local reference · invisible input alias ·
`sources` pointing at the wrong item kind · item kind not allowed for the operation · a
component with neither `math_refs` nor a residual · `component_id` naming no component of its
claim · a Markdown fence in place of the contract version · operation mismatched against the
Task · a missing `normalization` block · `VERBATIM` with two differing wordings · a declared
departure that changed nothing

## The `run.json` gates have teeth

Deliberate attempts to record a success that did not happen, and what the contract did:

| Attempt | Outcome |
|---|---|
| `NOT_STARTED`, `call: null`, reason given | **accepted** — the honest state when no model was called |
| `COMMITTED` with `call: null` | **refused** |
| `COMMITTED` with a call but `SOURCES: NOT_RUN` | **refused** |
| `NOT_STARTED` carrying `source_bindings` | **refused** |
| fewer than seven check layers | **refused** |

One further constraint surfaced only by running it: `report: null` is admissible **only** with
status `NOT_RUN`. Every `PASS` or `FAIL` must point at an actual check-report blob — a layer
cannot be marked passing without evidence behind it.

## Lineage, and why seven check layers are not a chain

v0.2 states two lineage requirements and nothing previously enforced either. CONTRACT section 3:
the next Task "verifies a real COMMITTED run binding that Task/output pair." HOST section 4:
Lean's lamport "must reference a **previously committed** lamport_proof" and "a string authored
in the current call is not a pinned intermediate layer."

A run can satisfy all seven of its own check layers and still stand on a predecessor that never
committed. So `run.consumes` now records every committed item an attempt read together with the
run that produced it, `run.call.principal` records who the **host** attributed the execution to,
and `Task.excluded_principals` returns from v0.1. `lineage.py` rejects:

| Failure | Code |
|---|---|
| lean consumed no committed lamport at all | `NO_COMMITTED_LAMPORT` |
| an attempt cites itself as its own producer | `SELF_CONSUME` |
| the cited producing run is `STAGED`, not `COMMITTED` | `CONSUMED_UNCOMMITTED` |
| the cited item was never produced by anything | `DANGLING_CONSUME` |
| the receipt names a producer the ledger disagrees with | `PRINCIPAL_MISMATCH` |
| the principal is one the Task excluded | `EXCLUDED_PRINCIPAL` |
| `NOT_STARTED` yet claims to have read items | `NOT_STARTED_CONSUMES` |
| the host attributed no principal at all | `NO_PRINCIPAL` |

`PRINCIPAL_MISMATCH` is the one worth naming: **the ledger wins over the receipt's assertion.**
Paper2Agent states the underlying rule most sharply — "do not substitute a changed role prompt in
the same agent context for independent verification" — and a principal a model reports about
itself is not a principal.

Say the boundary plainly: **v0.2 has no review operation, so this is lineage and not independent
review.** It is what a review operation will stand on when one exists.

`verify_phase.py` is the gate across runs, adapted from Paper2Agent's `verify_workflow.py`. It
re-hashes every stored blob — "never refresh hashes alone to make stale evidence current" — traces
every consumed item to its producing run, and requires a `COMMITTED` run for each phase up to the
one requested. It decides nothing scientific, and its passing message says so.

## Macros: mechanical, and the host's job

`\Mcal` means `\mathcal M` in this paper, and the model should not have to guess that. `expand.py`
reads every `\newcommand` / `\renewcommand` / `\providecommand` / `\def` out of the supplied
sources and publishes a table as a context input.

**It scans the main file as well as the preamble.** This paper defines `\Mcal` on line 8 of
`draft.tex`, not in the `head.tex` it inputs; scanning only the preamble reported the paper's own
notation as unresolved, which is how the bug was found. Result: 42 macros recovered, outcome
`PARTIALLY_EXPANDED`, and 45 remaining control sequences reported — all standard LaTeX or TikZ
(`\draw`, `\foreach`, `\hbar`). `STOCK` in that file is a curated allowlist, not a complete
inventory of LaTeX, so an entry in `unresolved_macros` is a prompt to look rather than proof of
a defect.

**Expansion supplies a table; it does not rewrite the source.** Byte offsets stay offsets into
the original bytes and locator markers are still verbatim from the text the model saw. The model
then declares, per MathClaim, how far its wording moved from the source — `VERBATIM`,
`NOTATION_NORMALIZED`, `LOGICAL_FORM_EXPANDED`, or `SOURCE_IMPLICIT_CONTEXT_EXPLICIT` — and both
wordings are retained. The checker verifies that declaration is self-consistent; whether it is
the *right* step is a reading judgement and belongs to review.

For contrast, the earlier V1 mechanism at
`Stabilizerness/MathClaimIRRegistry/` recorded the same discipline and produced 25 MathClaimIR
records for this paper with **zero** marked `VERBATIM`: 8 `SOURCE_IMPLICIT_CONTEXT_EXPLICIT`,
11 `LOGICAL_FORM_EXPANDED`, 6 `NOTATION_NORMALIZED`, no unresolved symbols. Its sibling
`normalization/` directory, however, is empty — the notation layer was given a home and never
populated, which is why it went missing from v0.2 until it was put back.

## Real source resolution

Against `Stabilizerness/arXiv-2607.26154v1/draft.tex` (69,678 bytes,
`sha256:4a84425a4d56efe5…`). The model supplies only verbatim markers; the host computes the range.

| Locator | Byte range | Length | What it is |
|---|---|---|---|
| `loc-closed-form` | `[18686, 19275)` | 589 | the paper's main closed-form theorem |
| `loc-perfect-collapse` | `[45972, 46573)` | 601 | the Chvatal perfect-graph lemma that blocks it |
| `loc-mwis-thm` | — | — | **refused**, `END_AMBIGUOUS`: `\end{theorem}` occurs more than once at or after the start marker |

The third row is the point. The convention refuses rather than guessing, on real input.

## Measured cost

| Work | Hours |
|---|---|
| Everything in the table above, including its tests | **4–5** (done) |
| Pinned spec index and the provider-neutral adapter, four profiles, render verified | **2** (done) |
| Macro table extraction and the normalization self-consistency checks | **1** (done) |
| Lineage checks, the phase gate, and per-stage retry bounds | **1** (done) |
| Response path: parse, stage, commit, and the `TASK_BINDING` check layer | 2–3 |
| A `prepare` / `run` / `status` CLI over the above | 2 |
| **Minimal v0.2 slice, total** | **11–13**, of which **8–9 are done** |

For comparison, the v0.1 route priced in the framework gap-analysis record came to roughly
23 hours, and what it delivered would not satisfy v0.2's first principle: its five "rounds"
replay one hand-authored seed, and its dependency stage is a regular-expression scan over bytes.

## Providers: the protocol does not pick one

`CONTRACT.md` treats `model_profile` as a pinned descriptor, and `run.schema.json`'s `call`
block names `provider` and `model` as data with a nullable `provider_request_id`. The receipt
shape was already provider-neutral; `adapter.py` is the mechanism, not a change to the contract.

| Profile | Provider | Credential read from |
|---|---|---|
| `profiles/anthropic.json` | Anthropic Messages API | `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` |
| `profiles/gemini.json` | Google Generative Language | `GEMINI_API_KEY`, `GOOGLE_API_KEY` |
| `profiles/openai-compatible.json` | any Chat Completions endpoint — OpenAI, OpenRouter, Together, DeepSeek, vLLM | `OPENAI_API_KEY` |
| `profiles/local-ollama.json` | a model the reader runs themselves | `OLLAMA_API_KEY`, `LOCAL_LLM_KEY` |

A profile is a small JSON file: provider, model, endpoint, how the credential is carried, and
generation parameters. Adding a vendor means adding a file, plus a shim in `_body` and
`_normalize` if its request shape is new. Changing the model is editing one string — no model id
here is assumed to exist, and none is validated against a list.

`render()` needs **no credential**: it assembles the request, pins the profile bytes, and records
the hash of the exact content that would be sent, which is what `HOST.md` section 3 requires.
`send()` needs one, and when none is present it raises a message written to go straight into a
`NOT_STARTED` receipt's `reason`:

> No credential for provider 'gemini': none of ['GEMINI_API_KEY', 'GOOGLE_API_KEY'] is set in
> the environment. No model call was attempted.

Two consequences worth stating plainly. First, this is the executable form of Principle 2 — the
format is shared, the content may differ — so "which model" becomes a measurable question rather
than an architectural commitment, and the same Task can be replayed across vendors with every
original response retained. Second, the `local-ollama` profile makes one claim testable: at
roughly 13k tokens of protocol plus the source, the reader does not need anyone's hosted model
to produce a checkable record.

Raw HTTP over the standard library is deliberate. No single vendor SDK spans these providers,
`HOST.md` states this delivery installs no dependencies and selects no provider, and the
repository has no runtime package dependencies. If you only ever target Anthropic, that vendor's
official SDK is the better choice than this file.

**Nothing has been sent.** No credential is configured on this machine, so `send()` has never
executed against any provider. The render path is verified; the response path is not.

## What a paper costs

`cost.py` prints the model behind the talk's cost slide. Two scopes, kept apart because v0.2's
Lamport/Lean branch runs on one selected MathClaim by design:

| Scope | Calls | Input | Output | Cost |
|---|---|---|---|---|
| A — extract, dependency on all 25 claims, formalize **one** | 66 | 1.17 M | 146 k | **≈ $9.5** |
| B — the same, formalizing **all 25** | 210 | 3.93 M | 770 k | **≈ $39** |

The claim count is measured from `Stabilizerness/MathClaimIRRegistry/`, not assumed. The token
counts are a four-characters-per-token approximation and the rate card is quoted from a cached
table — both are to be replaced with receipts, and the script says so in its own output.

The number that matters is not the price: **82% of scope A's input is the same 14.5k-token
specification prefix, sent 66 times.** The largest lever is therefore free, and it comes before
any effort-tiering decision. The adapter already renders in cache-friendly order — instruction,
specification, then the varying brief and sources — but declares no cache breakpoints, so that
82% is currently paid in full. Fixing that is the first cost item.

Effort then goes where the difficulty is: `low`/`medium` for extraction, `medium` for dependency
comparison, `high` for structuring a proof, `xhigh`/`max` for writing Lean that must compile. In
scope B that last operation alone is over half the bill, and its **iteration count** — not its
per-call price — decides the total. That is the first quantity to measure.

## `evidence/`

Derived material, produced from repository data by the scripts above and by the DAG in
`Stabilizerness/dag/claim-dag.json`:

- `closure.json` — the 29-node upstream closure of `claim:closed-form-rom`, with each node's
  state and any attached Lean declaration or open blocker.
- `projection.cypher` — a Neo4j projection of that closure: 29 nodes, 45 edges, deterministic
  projection keys per `STORAGE.md`. Neo4j is not installed here; the file is import-ready.
  Every edge carries `disposition: 'ORACLE_CANDIDATE'`.
- `source_bindings.json` — the resolved byte ranges above.
- `blocked-theorem.html` — a reader for the closure: select a node to trace its edges and see
  its record, its Lean declaration, or its blocker.

Three of the twenty-nine claims carry a kernel-checked declaration from
`formal/AgtXIvStabilizerness`; two of the six foundations are blocked; the closed-form theorem
itself remains unproved. A path in the projection is not a proof.
