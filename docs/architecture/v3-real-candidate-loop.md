# Real-paper candidate loop / 真实论文候选闭环

## Purpose and evidence level

This local loop uses the byte-pinned robustness-of-magic paper to connect source capture, tentative whole-text inventory, one source-grounded proposed argument, unresolved work, immutable artifact persistence and exact historical queries. It is **not** a paper demo, scientific reproduction, scientific approval, formal scope freeze, release or knowledge admission.

The existing 64-family V3 contract is unchanged. The candidate package is a retained JSON artifact, not a new authoritative knowledge-snapshot type. Source snapshots, source spans, paper structure, proposed argument nodes, joint inference steps, dependency bindings and open frontier items use existing V3 record families. An explicitly requested local context has an **unadopted** policy, no ratification, no allowed principals and only declared producer identity. No authority context is manufactured.

Source-byte observations are `OBSERVED`; interpretation records are `RESEARCH` with explicit `ORACLE_PROPOSED / UNVERIFIED` attribution. The whole-text cue inventory and proposed obligations also remain unverified. Every query is `PROVISIONAL` and reports `scientific_assessment: NOT_PERFORMED` and `authority_checked: false`.

## Source selection and coverage

The [independent static source note](../evidence/v3-real-candidate/source-review.md) compares all five fixed papers. The selected main-and-appendix file is 56,170 bytes and 548 physical lines. Its short single-file argument made the first engineering loop tractable; the selection was not based on obtaining a favorable scientific conclusion.

The original bundle consists of six local files, including its archive and three figures. All five regular archive members match their local counterparts; see [archive correspondence](../evidence/v3-real-candidate/archive-correspondence.json). The live directory also contains eight `build/` files. These are retained as local generated/unverified artifacts, not evidence of an execution performed by this task. The captured manifest, not a hard-coded file count, determines each observation's denominator.

Every captured UTF-8 text line retains its exact original byte span. Lexical cues divide main-text lines into tentative claim cues, nonclaim cues and unknown text. Equations, tables, verbal assertions and property labels can generate false positives. Comments, macros and multi-line prose can defeat the heuristic. **Neither the number of cues nor the number of lines is a scientific claim denominator.** The semantic denominator remains unknown and a whole-text human/agent review obligation remains open.

## Representative chain and unresolved obligations

The six explicit interpretations cover the robustness definition, channel action, feasible output pseudomixture, norm contraction, the R3 trace-preserving monotonicity statement and a separate postselection extension. Exact original anchors, assumptions and reconstructed proof requirements are retained. In particular, stabilizer atoms may map to stabilizer mixtures; atom-to-atom preservation is not required. Optimality of the input decomposition is marked as a contextual reconstruction.

Declared dependency bindings let the existing potential-impact analyzer reach R3 from its proposed prerequisites. The separate postselection extension is not made a consequence of the selected trace-preserving route. None of these edges is a mathematical verification.

Proposed obligations have exact target or source-artifact references, remain `OPEN` / `DEFERRED`, contain no successful execution evidence, and explicitly say that frozen-obligation checking was **not performed**. This is candidate accounting, not a fabricated FrozenScope or a bypass of the later frozen-scope gate. Supplementary numerical matrices, datasets, solver certificates, external citations, figure contents, package/rendering environment and whole-paper scientific coverage remain unresolved.

## Repeatable offline commands

Run from the repository root. Resolve temporary paths because the no-symlink output writer deliberately rejects ancestor symlinks, including the usual macOS `/tmp` alias.

```bash
work=$(.venv/bin/python -c 'from pathlib import Path; import tempfile; print(Path(tempfile.mkdtemp(prefix="agtxiv-candidate-")).resolve())')

.venv/bin/python tools/inspect_v3_candidates.py build \
  'Reference/Application of a resource theory for magic states to fault-tolerant quantum computing' \
  --main Robustness_main_appendix.tex \
  --robustness --local-proposed-context \
  --review-note docs/evidence/v3-real-candidate/source-review.md \
  --database "$work/candidates.sqlite" \
  --output "$work/build.json"

# A separate process reopens the database in read-only mode.
.venv/bin/python tools/inspect_v3_candidates.py query \
  --database "$work/candidates.sqlite" \
  --reference "$work/build.json" \
  --output "$work/query.json"
```

All output paths must be new and outside the captured source tree. Omitting `--local-proposed-context` and `--record-context` produces an artifact-only inventory, not normative argument records. The optional `--record-context` accepts explicitly supplied caller records/bytes instead of generating local candidate context. Neither mode authenticates those records.

`--observed-at` is only for replaying a caller-known observation with `--local-proposed-context`; it is not an authenticated timestamp or a new acquisition receipt. To reproduce an exact package identity, retain the original input bytes, observation time, corpus, review-note bytes, source root and implementation version. A changed input or new observation should produce a different candidate identity. Historical query uses retained database bytes, not today's filesystem contents.

## APIs and checks

- `build_candidate_package`: binds the captured denominator, original byte segments, tentative cue inventory, explicit proposals, candidate obligations, optional V3 record references and supporting artifacts.
- `build_interpretation_records`: projects source-anchored proposals into existing V3 candidate record families without inventing reviews or acceptance.
- `persist_candidate_package`: validates/reconstructs the package and uses existing transactional storage; never updates a knowledge/admission head.
- `query_candidate_package`: reconstructs and verifies the exact historical package and returns its original spans, records and unresolved questions.
- `inspect_dependencies`: computes potential reachability over the generated explicit dependency bindings; it changes no scientific state.

Final counts, input/output hashes, actual record validation, read-only reopen/replay checks and regression results are recorded in the [real-candidate evidence directory](../evidence/v3-real-candidate/README.md). All files are locally writable engineering evidence, not independently signed checkpoints. Large retained byte artifacts/databases belong in ignored local output directories, not source-control commits.

## 中文说明

这个闭环解决的是：真实原文如何形成可核对、可保存、可按历史版本重新读取的**候选调查包**。它不解决“论文是否已被证明正确”，也不伪造正式冻结、独立身份、科学审阅或知识准入。

全文按原字节保留，并给出词法候选线索、非主张线索和未知文本。词法线索不等于科学主张：一行公式可能被误报，跨行陈述也可能漏报，因此科学主张分母仍未知。重点 R3 链具有原文定位、显式条件、联合前提和潜在依赖；后选择推广、数值结果及外部证据继续单列为未解决问题。

旧材料清单和原始文件没有改写。新增本地清点同时纳入三张已有但旧清单未单列的 PDF，以及现场的 `build/` 生成文件。生成文件只说明这些字节在捕获时存在，不代表本次运行了编译或科学程序。空数据库导入、关闭后只读重开和精确版本读取均可用上述命令重复；查询始终为 `PROVISIONAL`。

后续要进入正式科学闭环，仍需真正的全文主张/非主张审阅、符合政策的独立范围冻结、实际形式/科学核查、正式发布与逐条准入。本阶段留下可定位的缺口和原始依据，而不把缺失工作填成“成功”。
