# Offline checks, 2026-09-25

Authorized scope: offline checks on synthetic fixtures only (no real paper, model, network, Neo4j or Lean).
Timestamps in the files are UTC (2026-09-24T23:55Z = 2026-09-25 01:55 local). Worktree base commit 155e35d;
the v0.4 files were uncommitted at the time.
Interpreter: /Users/Yingjian/Documents/GitHub/AgtXIv/.venv/bin/python (see the pytest header).
Re-run 2026-09-25T00:24Z after the owner's gap decisions D1-D13 were applied (the first run had 241 passed and
114 Cypher statements; that re-run had 248 passed and 102). Re-run again 2026-09-25T00:34Z after the review
fixes (only S1 may assert PaperVersion; one more analysis test); all three output files are from this run.

| File | What |
|---|---|
| `pytest-v04-suite.txt` | `pytest 'schema v0.4/tests' -v`: 249 passed, exit 0. |
| `pytest-v03-regression.txt` | `pytest 'schema v0.3/tests' 'schema v0.3/host/test_clause_evidence.py' -q`: 77 passed, 1 skipped, exit 0; `git status` shows no change under `schema v0.3/`. |
| `static-checks.txt` | Output of `static_checks.py`: 12 JSON files parse, 11 schemas pass the Draft 2020-12 metaschema, 102 Cypher statements have balanced brackets and quotes and use only loader-sent fields and parameters. This is not a Neo4j parse. |
| `static_checks.py` | The script, copied from the integration stage's scratch space. |
