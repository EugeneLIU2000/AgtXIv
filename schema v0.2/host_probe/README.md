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
| Cross-object checks (SHAPE, REFERENCES) | `check_output.py` | **10 of 10 negative cases rejected.** Fixtures in `negative/`. |
| Source locator resolution | `resolve.py`, `test_resolve.py` | **3 of 3 refusal cases correct.** Two real theorem locators resolved from the target paper; a third correctly refused. |
| Blob store, ledger, atomic commit, cross-process read-back | `store.py`, `e2e.py` | Commit and read-back verified from a separate process. |
| `run.json` honesty gates | `e2e.py` | The contract refuses a faked success. See below. |
| Pinned spec index, rendered for any model | `spec_index.py` | **14 entries pinned by hash; 9 rendered into the prompt, 5 identity-only.** The whole protocol renders to 52,171 bytes — roughly 13k tokens. |
| Provider-neutral model adapter | `adapter.py`, `profiles/` | **Four providers render a real request with no credential at all.** Anthropic, Gemini, any OpenAI-compatible endpoint, and a locally run model. |

## Run it

From the repository root, with the project virtualenv:

```bash
.venv/bin/python 'schema v0.2/host_probe/registry.py'
.venv/bin/python 'schema v0.2/host_probe/spec_index.py' paper.extract
.venv/bin/python 'schema v0.2/host_probe/adapter.py'
.venv/bin/python 'schema v0.2/host_probe/test_adapter.py'
.venv/bin/python 'schema v0.2/host_probe/test_resolve.py'
.venv/bin/python 'schema v0.2/host_probe/check_output.py' 'schema v0.2/examples/paper-minimal/output.json' paper_text
.venv/bin/python 'schema v0.2/host_probe/e2e.py'
```

`e2e.py` writes `e2e.sqlite` beside itself. Delete it to start clean.

## The ten negative cases

`check_output.py` rejects each of these. A checker that only ever reports PASS establishes
nothing, so the fixtures are kept alongside the code:

unknown root field · duplicate `item.id` · dangling local reference · invisible input alias ·
`sources` pointing at the wrong item kind · item kind not allowed for the operation · a
component with neither `math_refs` nor a residual · `component_id` naming no component of its
claim · a Markdown fence in place of the contract version · operation mismatched against the Task

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
| Response path: parse, stage, commit, and the `TASK_BINDING` check layer | 2–3 |
| A `prepare` / `run` / `status` CLI over the above | 2 |
| **Minimal v0.2 slice, total** | **10–12**, of which **6–7 are done** |

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
