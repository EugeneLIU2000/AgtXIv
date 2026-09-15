# Paper Agent 运行实例：arXiv 2608.14798v1（claude-opus-5）

论文：[Stabilizer Statistical Mechanics: A Framework for Efficient Quantification and Classification of Magic States](https://arxiv.org/abs/2608.14798v1)。
规范：`schema v0.1/Paper Agent/AGENT.md`（未修改）。业务记录：`schema v0.0`（未修改）。运行日期：2026-09-13。

这是**同一篇论文的第二次独立运行**，与同目录下 `2608.14798v1/`（另一模型）并列存放，便于比较。本次由 claude-opus-5 单次执行完成：真实读完 `Pauli_Spectrum.tex` 的全部正文与补充材料（第 182–2723 行，即 `\begin{document}` 之后的全部内容；1–181 行是宏包与自定义命令，只做结构性确认），自行抽取主张，自行装配记录。**没有**参考另一模型的抽取结果。

**结论先说：S0、S1、S3 交付；S2 冻结、S4 配对交接、S5 清单对账在本次运行中不可达，原因不是工作量，而是接口本身要求第二个主体。** 下面每一条都有可复运行的校验输出支撑。

## 先看这三个文件

1. [主张阅读版](output/claims.md)：36 条作者主张，逐条列出条件、组件、数学目标、残留与开放问题。
2. [接口检查](output/interface-checks.json)：本次真正跑出来的校验结果，包括四个把边界钉死的探针。
3. [接口边界结论](interface-findings.md)：AGENT.md 与 v0.0 schema 在本次运行中相撞的三处，以及它们各自卡在哪一行。

论文本身读出来的问题单独放在 [paper-findings.md](paper-findings.md)。

## 产出了什么

| 记录类型 | 数量 | 说明 |
|---|---:|---|
| `source-snapshot` / `paper-structure` | 1 / 1 | 16 个源文件全部登记并按字节核过 SHA-256 |
| `agentization-plan` / `processing-profile` / `authority-policy` | 1 / 1 / 1 | S0 上下文 |
| `source-span` | 97 | 每条都对 `Pauli_Spectrum.tex` 的真实字节区间，逐条重算摘要 |
| `scientific-claim` | 36 | 覆盖正文与补充材料；模态 ASSERTED 30 / CONDITIONAL 2 / OBSERVED 2 / APPROXIMATE 1 / INTERPRETIVE 1 |
| `definition` | 15 | 含 SPF、cSPF、稳定子功、Pauli 气、截断 SPF、Pauli 谱密度等 |
| `math-claim` | 32 | 带量词、假设、归一化说明；EXACT 30 / APPROXIMATE 1 / ASYMPTOTIC 1 |
| `semantic-context` | 2 | H₂ 解离与横场 Ising 两个数值应用的物理读法 |
| `claim-component-map` | 36 | 140 个组件全部有处置：MAPPED 50、RESIDUAL 86、UNRESOLVED 3、NON_CLAIM 1 |
| `frontier-item` | 49 | 全部 OPEN；按轴分布：数学正确性 26、来源忠实 18、语义适用 7、可复算 4、经验支持 2 |
| 合计 | **273** | — |

主张覆盖度：3 条 COMPLETE（组件全部有数学目标），33 条 PARTIAL。**PARTIAL 是诚实状态，不是失败。** 论文中大量内容（物理类比、动机、算法散文、图读数）不应被硬塞进 MathClaim，这些组件保留为 RESIDUAL，原文含义原样留存。

未被冻结的义务分母共 **57 项**：16 项源单元、1 项结构、36 项主张、2 项语义、2 项数值复算。

## 实际校验结果（本次真跑出来的）

```
完整记录集      → 不通过：36 个 SELF_REVIEW，且只有这一类错误
诊断子集(237)   → 通过：去掉 36 条对应关系后，引用闭包、字节重算、记录形状全部通过
AGENT.md 精简 Plan → v0.0 schema 拒绝（缺 max_seconds / max_cost_units / created_at / data_class）
proof.expand 交接  → 被拒：Missing required operation input: frozen-scope
dependency.search 交接 → 通过
```

三点需要讲清楚：

- **36 个 SELF_REVIEW 是结构性的，不是疏忽。** `claim-component-map` 的 `review` 是必填且不可为空，而 `ReviewContext` 至少要一个被审对象和一个生产者主体；只要对应关系的生产者就是主张的生产者，校验器一定拒绝。本次没有编造第二个主体来消除它。[探针](output/interface-checks.json)同时给出同主体与不同主体两种情形的实测结果：前者 `['SELF_REVIEW']`，后者 `[]`——差别只有 `principal_id` 一个字段。
- **S2 冻结不可达，因此 S4／S5 也不可达。** 四个 `scope-decision` 探针把条件钉死了：同主体 + ACCEPT + UNESTABLISHED → `SELF_REVIEW` + `INDEPENDENCE_UNESTABLISHED`；同主体 + BLOCK → 仍是 `SELF_REVIEW`（连"阻塞"都签不了）；不同主体 + ACCEPT + UNESTABLISHED → `INDEPENDENCE_UNESTABLISHED`；不同主体 + ACCEPT + ROLE_SEPARATED → 通过。`frozen-scope` 要求一个 ACCEPT 的 `scope-decision`，`proof.expand` 要求 `frozen-scope`，`obligation-disposition` 要求 `frozen-scope`——**一条单主体的 Paper Agent 运行链，在 S2 处必然断开。**
- **精简 Plan 与旧 schema 不兼容。** AGENT.md 第 3 节把 `max_seconds`／`max_cost_units` 判为冗余并删除，把 `created_at`／`data_class` 移出记录；v0.0 `agentization-plan` 这四项全是必填。本次采用的 Plan 在这两个预算字段上填了声明性占位值，并在 `trigger_note` 中写明"从未度量、从未生效，0 不代表零成本"。AGENT.md 形状的 Plan 连同校验错误保存在 [plan-as-agent-md-specifies.INVALID.json](output/plan-as-agent-md-specifies.INVALID.json)。

## 本次**没有**建立什么

- 没有判断论文任何一条主张的真假。`paper-findings.md` 里记的是**读到的文本不一致**，不是"论文错了"。
- 没有证明、证伪或形式化任何数学目标；没有生成 Lean 代码。
- 没有复算任何数值结果。H₂ 与 Ising 的曲线只被记录为"未复算"，两项 COMPUTATION 义务保持开放。
- 没有取回任何被引文献。所有 `IMPORTED` 归属只到"本文这样引用"为止；`draft_ref.bib` 只登记了字节。
- 没有打开任何图像文件。12 个图形文件只有哈希，**论文中一切依赖看图得出的陈述在这里都未被核实**。
- 没有任何身份认证。所有记录 `identity_assurance` 均为 `DECLARED`；运行中没有可信执行度量、没有独立审阅者、没有计费度量。
- 没有编译 LaTeX。文档结构边是从源文本读出来的，不是构建日志。

## 怎样复运行

在仓库根目录：

```bash
.venv/bin/python 'schema v0.1/Paper Agent/example/2608.14798v1-claude-opus-5/validate_run.py'
```

退出 0 表示**已记录的成功项和已记录的阻塞项都复现了**，不表示 S0–S5 走通，更不表示论文成立。它会重算 16 个源文件和 97 条 span 的摘要、比对 `AGENT.md` 与 schema bundle 的哈希，并要求完整集恰好出现 36 个 `SELF_REVIEW`。

重新装配（不覆盖已保存结果）：

```bash
.venv/bin/python 'schema v0.1/Paper Agent/example/2608.14798v1-claude-opus-5/build_run.py' \
  --output '/tmp/opus5-replay'
.venv/bin/python 'schema v0.1/Paper Agent/example/2608.14798v1-claude-opus-5/checks_run.py'
```

`build_run.py` 预期退出 2（完整集不通过）。**它不调用模型**：它把已完成的一次抽取（`extraction/seed.json`）重放成记录，并从真实论文字节重新计算每个 span 的偏移与摘要。要换一篇论文，需要重新做一次真实阅读，这个脚本做不到。

## 文件说明

```
acquisition.json                     16 个源文件 + 压缩包的真实哈希与字节数
extraction/seed.json                 本次阅读的抽取结果（模型直接写出，非派生）：97 个锚点、15 个定义、36 条主张
build_run.py                         seed → 273 条 v0.0 记录 + claims.md
checks_run.py                        接口检查与四个边界探针；产出 interface-checks.json
validate_run.py                      回读检查，退出 0 表示成功项与阻塞项都复现
output/records.json                  273 条记录（权威）
output/records/                      每条记录单独一个文件，manifest 中登记字节摘要
output/records-without-maps.json     237 条诊断子集（去掉未审阅的对应关系）
output/claims.md                     主张阅读版
output/manifest.json                 记录清单、计数、校验结论、AGENT.md 与 schema bundle 哈希
output/interface-checks.json         接口检查全文，含探针实测输出
output/plan-as-agent-md-specifies.INVALID.json  AGENT.md 形状的 Plan 样本（未签署、未采用）
output/handoff/                      两份 Task 草稿：dependency.search 通过，proof.expand 被拒
interface-findings.md                接口边界结论
paper-findings.md                    论文文本层面读出的问题
```

## 与同目录另一次运行的关系

两次运行读的是同一份字节（压缩包 SHA-256 `3e3c04d8…`，16 个文件）。两次都**独立**得出同一个核心阻塞：对应关系的自审无法通过，义务分母无法冻结。这一点相互印证，不是互相抄来的。

差别在于：本次把边界**做成了可执行的探针和 Task 校验**，因此能给出比"若干 SELF_REVIEW"更强的结论——单主体运行在 S2 处必然断链，而这一点连带决定了 S4 与 S5。主张集合是独立抽取的，两边的条数、切分和残留判断都不同，不应互相当作对照真值。
