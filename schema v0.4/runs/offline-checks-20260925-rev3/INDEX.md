# Offline checks, 2026-09-25, Revision 3

Authorized scope: the owner's "允许离线检查" for building the v0.4 framework — offline checks on synthetic fixtures
only (no real paper, model, network, Neo4j or Lean). Timestamps in the files are UTC (2026-09-25T22:16Z = 2026-09-26
00:16 local). Worktree base commit 155e35d; the v0.4 files are uncommitted. Interpreter:
/Users/Yingjian/Documents/GitHub/AgtXIv/.venv/bin/python.

The v0.3 regression was run twice: once after the Revision 3 changes (`pytest-v03-regression.txt`, kept unchanged)
and again after the fixes that two independent static reviews asked for (`pytest-v03-regression-after-review.txt`).
The v0.4 suite was run after those fixes (`pytest-v04-suite.txt`, 306 passed) and again after tests were added for
ten fixes that had no direct test yet — seven new test functions and one new check in an existing test
(`pytest-v04-suite-final.txt`, 313 passed; only test files changed between the two runs, so the static checks, run
once, still apply).

| File | What |
|---|---|
| `pytest-v04-suite.txt` | `pytest 'schema v0.4/tests' -v -p no:cacheprovider` after the Revision 3 changes and the review fixes, 2026-09-25T22:16Z: 306 passed, exit 0. |
| `pytest-v04-suite-final.txt` | The same command, 2026-09-25T22:25Z, after adding tests for comment quotations, context-only files, nested focus cuts, occurrence binding, the canonical occurrence claim, part identity, the two structural rules, counted dependents, decoys that cite the conclusion and decoy de-duplication: 313 passed, exit 0. This is the current result. |
| `pytest-v03-regression.txt` | `pytest 'schema v0.3/tests' 'schema v0.3/host/test_clause_evidence.py' -q`, 2026-09-25T21:22Z, before the review fixes: 77 passed, 1 skipped, exit 0; `git status` shows no change under `schema v0.3/`. |
| `pytest-v03-regression-after-review.txt` | The same command, 2026-09-25T22:16Z, after the review fixes: 77 passed, 1 skipped, exit 0; no change under `schema v0.3/`. |
| `static-checks.txt` | Output of `static_checks.py`: 20 JSON files parse, 17 schemas pass the Draft 2020-12 metaschema, 102 Cypher statements have balanced brackets and quotes and use only loader-sent fields and parameters. This is not a Neo4j parse. |
| `static_checks.py` | The same script as in `../offline-checks-20260925/`. |

The framework deck `slides/chain-build/schema_v0.4_framework.html` was checked in the app's built-in browser through a
local static server: every frame draws without console errors, every clickable mark opens a record, and the
precision-bound calculator and the count-basis toggle give the numbers the unit tests assert (details in
`schema v0.1/PENDING_TESTS.md` V04-29).
