# quant-ph run 2: S6, EXPANSION and S7 with the current Claude model reading (paused after the first paper)

Owner's request (2026-09-26): "依次做S6、EXPANSION、S7，先不调用外部模型而是用目前的模型单独一个agent" — run S6,
EXPANSION and S7 in order on the 50-paper sample of [run 1](../quant-ph-sample-20260926/INDEX.md), with the session's own
model (claude-opus-5-5) as a separate agent instead of an external model API. **Status: paused by the owner after the
first paper** ("先中断一下，我觉得我需要再优化一下流程"). No external model was called; no network was used in this run.

## What was run

| Step | Result |
|---|---|
| `manifest` | Successor CorpusManifest `corpus:8db77fb1…` of run 1's `corpus:24d8c5ea…`: same field, frame, eligibility program and parser, seed, target and gates; the S6 `method_version` is `focus-1/claude-opus-5-5-subagent`; the budget ceiling is 1,500 agent calls instead of 0. |
| `sample` | Round 0 `sampling:ca8800b8…` from run 1's examined outcomes (same sources and program): 80 examined, 50 accepted, as in run 1. |
| `base` | S1, S3, restatement and S4 deltas of the 50 papers: 151 deltas. |
| `s6-plan` | 50 agent packages and 511 ledger items (one per focus of 8,192 bytes); 8,874 occurrences in the inventories: 4,190 prose paragraphs, 3,013 display equations, 1,087 equation context bundles, 397 equation discourse bundles, 171 theorem-like and 16 definition environments. |
| S6, paper 1 | `arxiv:1501.02403v1` (3 foci): one fresh Claude Code subagent read the package and answered all three foci in one context, 32 minutes, about 184,000 subagent tokens, 18 tool uses; 47 claims emitted, 81 quotations each unique in the file. The host accepted 1 focus (9 readings, 9 junctions, 27 legs, 5 external requests) and rejected 2 foci for `AMBIGUOUS_PART`. |

## Finding: the focus-1 instruction states only half of the shared-occurrence rule

The instruction says that several claims of one occurrence each need a quotation inside it. The host also requires that
every claim sharing an occurrence uses only that occurrence (`extraction.response_to_delta`). The agent tied a claim to
a paragraph and the display equation it introduces, while another claim used the same paragraph; six such conflicts
rejected two whole foci. An external model given the same instruction would meet the same rule.

The owner chose to state every host check in the agent's task and restart (answer: "写清规则并重新开始"). `run.py` now
writes packages `AGENT_PACKAGE_V2`, whose `TASK.md` section 5 lists all rejection rules. The 50 packages on disk are
still V1: the restart must freeze a new manifest (a new S6 `method_version`), regenerate the packages and redo paper 1.

## Scale measured on paper 1

At paper 1's pace (about 11 minutes per focus, 0.7 minutes per occurrence), S6 on the 50 papers takes about 90–110
hours with one agent at a time, before EXPANSION (up to 25 more papers) and S7. This is why the owner paused.

## State left behind

- Ledger (`local-archive/…/quant-ph-claude-agent-20260926/ledger.sqlite`): paper 1 has 1 focus DONE and 2 READY (the
  rejected ones, one attempt left); the other 508 items are READY and were never dispatched. 3 agent calls spent.
- Deltas: 151 base deltas and 3 S6 deltas (one accepted, two failed, issues only) in `deltas.json`.
- Neo4j still holds run 1's projection; nothing was loaded in this run.

## Files

| File | What |
|---|---|
| `run.py` | The run script (all steps, including the not-yet-run EXPANSION, S7, build and load). |
| `corpus-manifest.json`, `sampling-record-round0.json` | The successor manifest and round 0. |
| `base.json`, `deltas.json` | Base delta ids per paper; the run's delta list. |
| `s6-plan.json`, `s6-results.json` | Foci, prompt digests and ledger keys per paper; per-focus results of paper 1 (counts and issue codes, no text). |
| `run.log` | Console log. |
