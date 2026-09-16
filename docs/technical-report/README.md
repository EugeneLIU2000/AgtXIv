# AgtXIv technical report / 技术报告与中文伴读

This directory contains the English technical report, a generated field appendix, and the Chinese reading guide below. The report is an implementation-oriented working document; it does not ratify the Charter or claim that the V3 scientific lifecycle is complete.

## Build

From the repository root:

```bash
.venv/bin/python docs/technical-report/generate_appendix.py
.venv/bin/python docs/technical-report/generate_appendix.py --check
bash docs/technical-report/build.sh
```

The output is `docs/technical-report/build/main.pdf`. The source uses pdfLaTeX, standard Latin Modern fonts, BibTeX and TikZ. The English PDF avoids requiring a particular Chinese system font; this README provides the Chinese companion. Build intermediates are ignored locally.

The portable [complete TeX source archive](agtxiv-technical-report-source.zip) includes the main file, every section, BibTeX source, generated appendix, generator and build script; it excludes PDF/rendering caches and compilation intermediates. After extraction, enter `agtxiv-technical-report/` and run `bash build.sh --frozen-appendix`. This compiles the included appendix without checking absent repository schemas. For schema changes, work in the repository, regenerate the appendix, and use the default build command above. The archive includes a SHA-256 file manifest. [Report validation](../evidence/publishable-release/report-validation.json) binds the source archive, PDF, compilation logs and reviewed pages.

`generate_appendix.py` reads the V3 catalog, schema manifest, common structures and every family schema. It writes only three files in this report's `generated/` directory, with exact source digests. The complete field reference is derived, not manually maintained. Long discriminator enumerations and exact regular expressions remain authoritative in the original schemas. The appendix includes their existence and points to the source rather than printing an unreadable identifier wall.

## 中文伴读：先理解这份报告在讲什么

这份报告围绕一个问题展开：**读到一个科学结论时，怎样知道它来自哪里、依赖什么、检查到了哪一步，以及自己是否能在当前条件下使用它？**

可以把 AgtXIv 看成“科学主张卡片 + 实验记录本”。论文原文是原件；主张卡片保留一句话背后的条件和出处；论证图说明几张卡片怎样一起支撑下一步；核查记录说明谁用什么方法检查了哪个对象。网页帮助人阅读，API 帮助其他程序读取，schema 规定记录格式。三者应指向同一份有版本的证据。

| 阅读顺序 | 核心直觉 | 英文正文 |
|---|---|---|
| 1 | 文件存在、程序跑完、科学结论成立，是三个不同问题。 | Purpose and reading model |
| 2 | 文件的内容指纹固定“看的是哪份原件”；原文位置固定“这句话在哪里”。它们不能判断这句话是否正确。 | Identity, sources and reconstruction |
| 3 | 多个前提通常必须一起使用；在局部假设下证明的结论不能被拿到外面当无条件结论。 | Arguments and six assessment questions |
| 4 | 64 类记录覆盖从取论文到复用知识的计划生命周期，不代表 64 个服务都已完成。 | Record families across the lifecycle |
| 5 | 魔性鲁棒性的例子解释为什么最优分解、迹保持和后选择必须单独记账。 | Worked robustness example |
| 6 | 新 arXiv 必须真的下载和处理；进度来自后台任务，结果依然是有边界的候选。 | Web/API architecture |
| 7 | 清理前先保全唯一材料；发布前核对实际构建、链接和运行证据。 | Evidence, maintenance and release |

## R3 的物理图像

把量子态写成稳定子态的线性组合时，系数可以为负。魔性鲁棒性取的是所有合法分解中“系数绝对值总和”的最小值。自由的迹保持操作把每个稳定子态分散成新的稳定子态概率混合，分配比例非负且总和为一。这种重新分配不会增加带符号权重的绝对值总量，正负抵消还可能让它减小。

证明最后必须用到**输入分解是最优的**。任意一个合法分解只能给上界，不能直接等同鲁棒性的最小值。原文前后语境中的这一要求在候选论证中被显式重构，不把它伪装成原文逐字写出的新前提。

**后选择是另一件事。** 选中一个测量结果后，还要除以成功概率得到归一化量子态。因此，“整个操作保持迹”的推导不能直接说明“每一个条件分支都不增加鲁棒性”。平均量与单个分支是不同目标，报告和记录均保留这一区别。

## 六个检查问题

1. **原文忠实性：** 有没有把作者的话、条件或归属改掉？
2. **数学正确性：** 在写明的前提下，结论是否成立？
3. **形式对齐：** 形式化代码证明的，是否正是想证明的数学命题？
4. **科学适用性：** 数学对象、近似和边界条件是否适用于当前物理问题？
5. **经验支持：** 数据和观测是否支持这个科学结论？
6. **计算可复现性：** 在说明的输入和环境下能否重做该计算？

例如 Lean 检查通过，并不自动回答第 1、3、4、5 个问题。程序正常结束也不说明上述问题已经得到支持。报告按“问题是否适用、证据得出什么结论、工作实际执行到哪一步”分别保存状态。

## Terminology ledger / 术语表

| Canonical term | 中文解释 | 使用规则 |
|---|---|---|
| Candidate | 待审阅的候选内容 | 不等于科学认可 |
| ScientificClaim | 保留原文条件与归属的科学主张 | 不与形式化定理混用 |
| MathClaimIR | 数学主张的中间表示 | IR 只在必要时使用并解释 |
| Assessment | 针对精确对象的一次有方法、有依据的核查 | 与命题内容分开 |
| Snapshot | 一份明确的历史版本范围 | 不以“latest”代替证据身份 |
| FrontierItem | 尚未解决的具体问题 | 写清下一步需要什么证据 |
| Compare-and-swap | 仅当前状态仍等于预期旧状态时才更新 | 避免并发任务互相覆盖；不写成科学认证 |
| D1 / R2 | 当前网页方案中的任务数据库 / 字节对象存储 | 这是运行架构，不自动成为正式科学知识库 |

## Evidence and known pending inputs

- Scientific case: the original retained Howard--Campbell TeX, the independent static source note and the historical candidate closure receipt.
- Contract description: the V3 schemas, invariant ledger and local mechanism guide. Field input digests are in [generated/schema-inputs.json](generated/schema-inputs.json).
- Repository organization: [organization audit](../audits/repository-organization.md) and [archive manifest](../audits/repository-archive-manifest.json).
- The current local HTTP path is recorded in [final HepLean verification](../evidence/publishable-release/heplean-http-final/verification.json) and its [complete result](../evidence/publishable-release/heplean-http-final/result.json): actual submission and source acquisition of `2405.08863v1`, three inventoried sources, 15 returned candidates, exact-version/schema checks, identical repeated reads and a nonempty entity tag matching the result digest. Both acquisition and analysis use the configured 20-second timeout, reported as `limits.timeoutMs=20000`. Earlier HTTP/browser results preserve their original 30-second engine field as historical checkpoints. All six axes remain `NO_ASSESSMENT` and scientific acceptance remains false.
- The retained [local admission check](../evidence/publishable-release/intake-checks/concurrency-local.json) observed one accepted request and nineteen rate-limited responses for 20 concurrent submissions. It used the real handler with a synthetic upstream and local SQLite; it is not a production concurrency certification. The neighbouring logs retain 14 engine, 23 response-schema and six handler test passes.
- The report reflects the current OpenAPI, atomic conditional admission and prefixed source digest. `INTERRUPTED` is a read-time stale projection after 120 seconds without an update; it does not prove the previous worker stopped. An earlier attempt can still complete while its separately retained retry runs. The three-task admission bound counts recent active records, not every potentially surviving worker.
- [Browser verification](../evidence/publishable-release/browser-verification.json) records the fixed root MIME response; actual form submission of HepLean; WebMCP task reading and new submission of `1706.03762` resolved to v7; invalid URL rejection; refresh recovery; keyboard slider operation; schema search/field expansion; and a narrow viewport with no page-wide overflow. These are scoped local checks, not a complete accessibility or public-deployment audit. Report-download resources and public deployment remain separate checks.
- The aggregate repository gate encountered a pre-existing dirty frozen-baseline mismatch against `HEAD`. The current full test run is being checked separately; neither this report nor the historical 710-test receipt claims the entire release gate passed.
- No benchmark advantage, independent scientific acceptance, Charter ratification or completion of all 58 V3 tasks is asserted.

Independent review checked all 64 lifecycle family names, the 11-field envelope, root-only record-hash exclusion, caller-held authority boundary and six-axis separation. The text distinguishes a recorded execution claim from an independently supported actual execution, and the local `project_axes` behaviour from completeness guarantees that a serialized `StatusView` does not provide. Reader feedback removed the phrase “first scientific output” from intake results and identified the signed-weight interaction as algebraic intuition, not a calculation for a specified quantum state or channel. The new HTTP evidence is synchronized in section 6; final deployment and complete release evidence remain separate.

The report follows the reader's path from purpose to object identity, scientific reasoning, interfaces, evidence and maintenance. Technical identifiers move to the generated appendix so the main argument remains readable. Targeted corrections should update the affected section and the supporting evidence map, preserving the rest of the report.
