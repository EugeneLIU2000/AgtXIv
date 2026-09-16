# AgtXIv research website

This is the primary V3 reader and live arXiv source-analysis service. It contains
a white, responsive paper reader, a source-linked argument example, searchable
contract documentation, and the technical report. The earlier repository demos
remain historical or research surfaces with their own contracts.

Submitting a new arXiv identifier actually retrieves the exact source version,
extracts bounded claim/equation candidates and local references, and retains the
job, original bytes and result. It does **not** perform mathematical or scientific
review; all six assessment questions remain unassessed.

## Local operation

Use Node.js 26.7.0 (the tested version):

```sh
npm ci --ignore-scripts
npm run build
npm test
npm run dev
```

The service listens on `http://127.0.0.1:8787`. Local jobs and source/result bytes
are stored under `.local/`; restarting the service preserves them. The local
adapter applies committed SQL migrations. Production uses Cloudflare Workers,
D1 (`DB`) and R2 (`ARTIFACTS`) configured through `.openai/hosting.json`.

`npm ci` is needed for editing database migrations; building, running and testing
the committed application use Node's standard library without runtime npm
dependencies. Generate migrations with `npm run db:generate` after changing
`db/schema.ts`. Production never creates tables from request handlers.

## Source of truth and generated copies

In the complete AgtXIv repository, run `tools/export_web_library.py` to regenerate
the curated reader and the exact V3 schema copies. Its `--check` mode verifies
every retained copy as well as original evidence anchors.

The maintained extractor is `../src/agtxiv_web/intake.mjs`; its response contract
is `../src/agtxiv_web/analysis.schema.json`. The build copies them into this
standalone website. In a standalone website checkout, the committed copies are
the build input. `api-spec.mjs` maintains the Job schema and OpenAPI document.
The build derives `public/api/v1/*.json` and emits `dist/server/index.js` plus
the static resources and committed migration metadata. Do not edit generated
schema copies independently.

The report source is maintained at `../docs/technical-report/`; its compiled PDF
and complete source archive are copied into `public/docs/` for publication.
The build artifact includes only the selected website files. It excludes local
jobs, source archives, caches, parent-repository research inputs and credentials.

## Versioned interface

- `POST /api/v1/jobs` with `{"arxiv":"2405.08863v1"}` creates a retained attempt.
- `GET /api/v1/jobs/{id}` reads the observed state and result location.
- `GET /api/v1/jobs/{id}/result` returns the exact saved JSON after hash checking.
- `POST /api/v1/jobs/{id}/retry` with `{}` creates a new linked attempt.
- `GET /api/v1/library`, `/papers/{slug}` and `/schemas` under the same API prefix
  read the curated collection and contract catalog.
- `GET /api/v1/health` describes configuration, not an end-to-end availability probe.

The full contracts are at `public/api/v1/openapi.json`, `job.schema.json` and
`analysis.schema.json`. `COMPLETED` means extraction and result storage finished.
`INTERRUPTED` is a read-only observation of two minutes without progress; it does
not establish that the earlier worker has stopped. That worker may still finish
after a separate retry starts. No automatic queue durability or exactly-once
execution is claimed.

The service accepts at most one new attempt per 3.5 seconds and three recent
active attempts. The JSON request limit is 2 KiB. Download, expansion, file,
candidate and hash-work limits are enforced by the extractor and returned in
each result. The server's retrieval timeout is 20 seconds. Sources are treated as
data; TeX and bundled scripts are never executed. Private source bytes are not
exposed by a download endpoint. Public results contain bounded excerpts and
explicit extraction limitations, not a full-text redistribution service.

## Verification

`npm test` checks real extraction against an explicitly synthetic TeX fixture,
SQLite persistence, failed retrieval and retries, input limits, stale observation,
result integrity, and curated identities. Repository tests additionally validate
all extractor responses with JSON Schema. A deliberately live check is available
from the repository root:

```sh
.venv/bin/python tools/verify_web_http.py \
  --arxiv 2405.08863v1 --output docs/evidence/publishable-release/heplean-http
```

This command sends a new real submission and retains its HTTP evidence. It is
not an offline test and is not run implicitly by `npm test`.

The supported browser-agent tools are `submit_arxiv_paper` and
`read_analysis_job` when the browser provides WebMCP. They use the same visible
flow and HTTP routes; their absence does not disable the ordinary form.
