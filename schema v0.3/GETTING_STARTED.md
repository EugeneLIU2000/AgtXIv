# Getting started with schema v0.3

Schema v0.3 is a source-checkout research framework for turning paper claims into explicit, reviewable dependency graphs and attempting Lean formalization. Start by reading its contracts and workflow. Running the research controller is an optional next step; completing an accepted paper-to-proof chain is still an open goal.

The public `main` branch publishes the implementation and documentation (first published on the `schema-v0.3-framework` branch). It does **not** include the historical `schema v0.3/runs/` archive, all of its source material, or the compiled Lean environments. References to that archive in older documents describe retained local evidence, not files supplied by this checkout. A clean checkout cannot replay those historical experiments as provided.

## 1. Read the public implementation

No model account, Python environment, network request, or Lean installation is needed to read these files:

| Read | Purpose |
|---|---|
| [README.md](README.md) and [WORKFLOW.md](WORKFLOW.md) | The project boundary and the path from source acquisition to a conditional chain certificate. |
| [SEMANTIC.md](host/SEMANTIC.md) | Candidate extraction, query selection, evidence imports, and recursive matching. |
| [GRAPH.md](host/GRAPH.md) | Joint premises, alternative support routes, pruning, and blocked dependencies. |
| [PROOF_BACKEND.md](host/PROOF_BACKEND.md) | Separate model/Lean proof attempts, human review, and certificate meaning. |
| [schemas/](schemas/) | Machine-readable research contracts. |

A **candidate** is a proposed claim, support relation, or formal statement that still needs the relevant review. A **frontier** is an unresolved boundary in the current search. Neither a model response nor a graph path establishes that a paper's theorem is true.

Use the [English progress analysis](../docs/releases/schema-v0.3-progress.md) for current evidence and limits; [STATUS.md](STATUS.md) preserves the original chronological record. Historical counts and audit results belong to their recorded runs; they do not establish that the current checkout has been tested.

## 2. Prepare a source checkout

If you do not already have the repository:

```sh
git clone https://github.com/EugeneLIU2000/AgtXIv.git
cd AgtXIv
```

Run the commands below from the repository root. Paths containing `schema v0.3` must remain quoted.

The root [pyproject.toml](../pyproject.toml) requires **Python 3.12** and **uv 0.10.0**; [.python-version](../.python-version) pins Python **3.12.2**. With that uv version installed, create the Python environment from the committed lockfile:

```sh
uv sync --locked --no-default-groups --python 3.12.2
```

This installs the declared runtime dependencies, including `jsonschema` and `referencing`, into `.venv`. It may download Python and packages. It does not run tests, call a model, or build Lean. The `test` and `validation` dependency groups are separate from this setup.

The project uses `tool.uv.package = false`: these instructions run scripts from the checkout. The metadata version `2.0.0.dev0` is separate from the `research/0.3.0` contract version. This guide makes no claim that a schema-v0.3 package has been published to a package index.

The research controller uses POSIX file locking (`fcntl`); native Windows support is not established. The generated Lean proof worker currently requires macOS `/usr/bin/sandbox-exec`. Installing the Python dependencies does not prepare a usable proof environment.

## 3. Understand what execution will use

| Action | Requirements and effects |
|---|---|
| Read source, schemas, or documentation | No execution or provider quota. |
| Run `host/research.py` | Writes frozen source copies, plans, graph snapshots, and a SQLite ledger. Missing candidate evidence can trigger real Codex CLI calls. This stage does not invoke Lean. |
| Add `--network-sources` | Allows bounded arXiv source acquisition and version metadata requests. Without this flag, the controller uses registered local sources. |
| Add `--imports` | Reuses explicitly referenced evidence. Missing evidence can still trigger model calls within the remaining budget. |
| Run `host/proof_walk.py` | Requires a prepared request and audited common Lean environment; can call models and execute generated Lean terms in the required sandbox. |
| Run an `audit_*.py` script | Executes artifact validation. An integrity result does not accept mathematical content. |

**Omitting `--network-sources` does not make a research run offline.** It disables source-acquisition networking, not the model provider connection. There is no `--dry-run` option. A zero model-call budget can prevent new model dispatch, but still permits local processing and writes; with source networking enabled it can still fetch sources.

For live calls, supply an authenticated Codex CLI that supports the arguments used in [host/model.py](host/model.py), including `exec`, `--ignore-user-config`, `--ephemeral`, and `--output-schema`. The dispatcher resolves its executable in this order:

1. `AGTXIV_CODEX_BIN`, if set.
2. A Codex executable bundled in `/Applications/ChatGPT.app` or `/Applications/Codex.app`.
3. `codex` on `PATH`.

For an explicitly chosen installed CLI:

```sh
export AGTXIV_CODEX_BIN=/absolute/path/to/codex
```

Source text, and images in the PDF path, are supplied to the model provider. The host retains prompts, responses, receipts, and usage information where available. Account authentication and model access must already be available; dependency installation does not establish them.

The committed [engines.json](profiles/engines.json) requests Luna for routine extraction and failure classification, Terra for dependency matching, and Astra for proof generation. These are repository configuration values, not a guarantee of account availability. The selected model and effort are frozen into each new plan. There is no automatic model escalation, and no measured cost or quality advantage is asserted. See [MODEL_ROUTING.md](host/MODEL_ROUTING.md).

## 4. Optionally start bounded research

The following is an explicit live research request. It can acquire sources and spend account quota. It is not an installation check or a tutorial with a guaranteed successful result.

```sh
.venv/bin/python 'schema v0.3/host/research.py' \
  --paper 2607.26154v1 \
  --query-label thm:solvable \
  --output 'schema v0.3/runs/my-query-001' \
  --candidate-exploration \
  --network-sources \
  --max-papers 2 \
  --max-model-calls 4 \
  --max-match-requests 2 \
  --max-call-seconds 180 \
  --max-identity-requests 2 \
  --extract-focus-bytes 8192 \
  --max-extract-batches 4
```

Choose a fresh output directory **inside the checkout** for each new plan. The initial paper consumes one paper slot. The model-call budget is shared across extraction and matching. The time limit bounds each model call; it is not a whole-run deadline or a dollar spending cap. Sources may already be registered locally; `--network-sources` permits acquisition when they are missing.

`--query-label` is a source `\label`, not a natural-language question. It may be repeated. The host binds the selected labels to the claims actually extracted. Without it, every extracted target-paper claim becomes a query. A missing source label is refused before a model call; a present label with no extracted candidate fails with `QUERY_LABEL_UNMATCHED` and publishes no graph.

The small budgets above may leave output ranges unfinished or may not reach the selected query. `--extract-focus-bytes` controls the output scope per extraction call; each call still receives the complete frozen source context. It does not allow arbitrarily large papers to bypass the model-input ceiling. See [OUTPUT_BATCHES.md](host/OUTPUT_BATCHES.md) before planning larger work.

The default decision policy is `STRICT_CALIBRATED`. It preserves gates for unreviewed or uncalibrated judgements and may block progress. `--candidate-exploration` explicitly permits scheduling candidate work while retaining its review blockers. It never accepts source alignment or promotes a support relation. **Strict mode is not an offline or zero-cost mode.**

### Read the result before doing more work

A normally completed research invocation exits **2**, reflecting `CHAIN_INCOMPLETE`. Argument errors can also exit 2, and operational failures can stop before a summary exists. Read stderr and the run artifacts together; the exit code alone is not a success criterion.

| Artifact in your new run | Read it for |
|---|---|
| `summary.json` | Mathematical status, controller stop reason, paper and candidate counts, accepted support edges, and model calls. |
| `plan.json` | Frozen budgets, query selector, policy, model routes, imports, and runtime identity. |
| `checkpoint.json` | Current controller phase and references to the published assembly and graph. |
| `frontier.json` | Unresolved sources and scheduling boundaries. |
| `ledger.json` / `ledger.sqlite` | Calls, reservations, budgets, issues, and durable event history. |
| `graphs/`, `checkpoints/`, `results/` | Immutable snapshots produced as research progresses. |
| `papers/`, `matches/`, `runtime/` | Frozen source evidence, model work, and the implementation captured for the plan. |

Some artifacts exist only after the corresponding stage completes. No graph is evidence that all claims have been found. `research.py` does not emit a chain certificate. The older `pipeline.py` is a separate historical migration driver; its `runs/latest.json` pointer is not the latest semantic research result.

## 5. Reuse work without rewriting its history

An import manifest points to evidence that you already possess. Most committed run profiles refer to the unpublished archive and often contain paths from the original machine; they are not portable example inputs.

For a whole-paper candidate import, the supported shape is:

```json
{
  "candidates": {
    "arxiv:2607.26154v1": {
      "response": "/absolute/path/to/retained/response.json",
      "extraction": "/absolute/path/to/retained/extraction.json"
    }
  },
  "matches": []
}
```

Save a new manifest with your own paths, then add `--imports /absolute/path/to/imports.json` to a new research invocation. The referenced extraction must agree with the frozen source version and bytes. A candidate entry may also name a `provenance` file. Imported judgements retain their provenance and consume no new model-call slot; historical costs do not become costs of the new plan. Missing work may still invoke the model.

Partial extraction uses `extraction_batches` and its retained dispatch instead of a whole-paper candidate import. Preserve the original source version and focus size, and reuse successful scopes before funding missing ones. The exact format and failure boundaries are in [MODEL_ROUTING.md](host/MODEL_ROUTING.md). PDF inputs require their separate retained-source bindings; a PDF pathname is not a drop-in TeX candidate import.

`--resume` is narrower than general crash recovery. For a run with an unchanged runtime, no unexplained outstanding reservation, and a resumable checkpoint, use its existing output path:

```sh
.venv/bin/python 'schema v0.3/host/research.py' \
  --paper 2607.26154v1 \
  --output 'schema v0.3/runs/my-query-001' \
  --resume
```

Resume uses the frozen plan, including its budgets and source-networking choice. It does not replenish quota or change the query or model route. A BUSY checkpoint or unresolved reservation requires explicit recovery after establishing the former worker's status. Runtime changes require a new plan. Preserve historical receipts; do not repair a run by relabeling failed work as successful.

## 6. Treat proof work as a separate prepared stage

A fresh public checkout does not contain enough artifacts to launch the historical proof walk. Preparing it requires a compatible `physlib` checkout, the matching Lean/mathlib environment, migrated dependencies and compiled objects, and a newly audited frozen environment. The current environment constructor is the Python function `host/proof_backend.py::freeze_environment`, not a general setup CLI. It actually compiles and audits Lean, so it is an execution step of its own.

See [PROOF_BACKEND.md](host/PROOF_BACKEND.md) and [CANDIDATE_INTEGRATION.md](lean/CANDIDATE_INTEGRATION.md) for the environment and migration boundaries. The historical 60-module candidate branch was written and repaired by agents; it is not the output of an automated query-graph proof walk. Its reported compilation does not remove the need for source alignment review.

Before a proof invocation, prepare a request containing:

| Field | Required input |
|---|---|
| `paper_id`, `source_sha256` | The pinned query source identity. |
| `graph`, `environment` | References containing `path`, `sha256`, and `byte_size` for the selected graph and frozen proof environment. |
| `paper_sources` | Paper IDs mapped to frozen extraction references and source directories, or supported PDF source bindings. |
| `candidate_root_bindings` | Optional root-node to audited library-declaration mappings; these remain candidate alignments. |
| `root_audits` | Optional reference to root-search evidence for roots without such a binding. |
| `selected_group_ids` | Optional explicit selection of alternative support routes. |

Hash references use `sha256:<hex>`. Repointing old paths alone cannot reproduce an environment fingerprint: its executable, imported object bytes, search order, and trusted runtime are part of the evidence. Do not fabricate missing receipts or bypass predecessor requirements to obtain an apparently usable request.

With those inputs actually prepared, an opt-in bounded proof command is:

```sh
.venv/bin/python 'schema v0.3/host/proof_walk.py' \
  --request /absolute/path/to/prepared-proof-request.json \
  --output 'schema v0.3/runs/my-proof-001' \
  --max-model-calls 3 \
  --max-proof-attempts 2 \
  --max-node-attempts 1 \
  --max-call-seconds 180 \
  --candidate-exploration
```

The proof worker requires the macOS sandbox and does not fall back to unrestricted generated Lean execution when it is unavailable. Model calls still use the provider connection; the generated Lean subprocess has network access denied. Unresolved graph blockers can leave no node attemptable even in exploration mode.

A completed walk writes `proof-walk-result.json`, `ledger.json`, `summary.json`, and `chain-certificate.json`, with attempted work under `attempts/`. Its normal exit code is also **2**, including when its certificate state is `CHAIN_CERTIFICATE_EMITTED`. That state means a formal implication conditional on explicitly listed Lean premises, not acceptance of the paper. Review and nonvacuity gaps remain visible. The result's own `chain_state` and the separate certificate state have different scopes; read both.

## Execution policy and current limits

Under this repository's collaboration policy, setup documentation is not authorization for an agent to run tests, example replays, validators, audits, or Lean builds. Such execution requires a later explicit user request for the relevant scope. All affected execution scenarios belong in the single [PENDING_TESTS.md](../schema%20v0.1/PENDING_TESTS.md). These onboarding commands were grounded in source inspection and were not executed while preparing this guide.

The current release remains limited by unpublished historical run inputs, machine-specific proof environments, unreviewed source-to-Lean alignment, incomplete earliest-origin research, lexical library search, and the absence of a completed autonomous paper-to-proof run. PDF recovery and recursive integration code also have execution gaps. Reading the source is immediately available; successful fresh-checkout research and proof reproduction must be established by separately recorded execution evidence.
