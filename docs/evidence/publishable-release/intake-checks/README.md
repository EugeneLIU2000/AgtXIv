# Scoped local intake checks

These files were copied unchanged from the intake review's temporary outputs on 8 September 2026. They preserve their original scope; later code changes require their own evidence.

| File | Observed result | Scope |
|---|---|---|
| `concurrency-local.json` | 20 simultaneous requests: one 202, nineteen 429, one scheduled task | Real handler and local SQLite, with a synthetic TeX upstream; source hashes are in the receipt. This does not certify Cloudflare concurrency. |
| `engine-node-tests.txt` | 14 passing tests | The named engine cases in the log. |
| `engine-schema-tests.txt` | 23 passing tests | The response-contract cases in the log. |
| `handler-tests.txt` | Six passing tests | Historical handler checkpoint; a later root-MIME regression extends the handler suite and is recorded separately. |

The real network/source-acquisition evidence is the neighbouring [HepLean HTTP verification](../heplean-http/verification.json). Scientific assessment remains `NOT_PERFORMED` throughout; these operational checks do not complete a scientific review or the entire release gate.
