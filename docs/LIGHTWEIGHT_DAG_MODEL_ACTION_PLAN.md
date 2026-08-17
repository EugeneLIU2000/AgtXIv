# AgtXIv 轻量级科学依赖 DAG：首个 4--6 周 MVP 行动计划

> 计划起点：不训练现成大模型、不下载大型数据集。  
> 访问与方案基准日期：2026-08-16。  
> 目标：在 4--6 周内得到一个**可审查、可拒答、可追溯**的候选 DAG 流水线，而不是自动发布科学上已接受的 Paper Agent。

## 1. MVP 完成定义

MVP 完成时应能对一个冻结的小型论文集合执行：

1. 从 LaTeX/结构化文本产生 claim span 候选；
2. 规范化并人工确认 `Statement`；
3. 为每个目标 claim 检索 top-$k$ 候选前提；
4. 判断四类依赖、方向并定位双侧 evidence span；
5. 输出显式 `ReasoningStep` 超边和无环候选图；
6. 保留独立的 `edge_decision=UNKNOWN`、`evidence_status=BLOCKED_MISSING_*`、conflict 和 cycle；
7. 通过 schema、ID、anchor、无环与 blocker 传播检查；
8. 所有自动生成的合同保持 `accepted=false`。

MVP 不包括：下载 OpenAlex/S2ORC/unarXive 全量快照、训练全文到 DAG 模型、训练 GNN、自动科学验收、修改现有核心工件。

各“周”是时间盒，不是保证交付某个统计成绩。若 paper family 少于能形成独立 train/dev/test 的数量，或某类正边样本不足，则只报告描述性结果，不拟合该类独立阈值；建议至少保留 3 个 dev 和 3 个 test paper families。若 bootstrap 置信区间宽到无法支持 Go/No-Go 决策，则延长标注而不以点估计宣告达标。第 4 周允许回退为“候选排序器 + 人工 evidence/step 标注”。

---

## 2. 全程不变的安全规则

- 引用图、citation intent、科学依赖图分别保存；
- 跨论文正边必须有 target-use span 与 source-statement span；
- `edge_decision=UNKNOWN` 和任何 `evidence_status=BLOCKED_MISSING_*` 都不是负例；
- 边方向统一为 premise $\to$ conclusion；
- 多前提必须保留为 `ReasoningStep`，不能只保留压扁后的二元边；
- 发现环时输出冲突，不静默删除；
- 模型置信度与五路 verification status 分开；
- 任何模型或规则不得设置 `accepted=true`；
- 所有数据记录 source version、artifact hash、extractor/model/rule version；
- 开源代码、数据和模型权重分别核验许可证。

---

## 3. 第 1 周：冻结协议、Schema sidecar 与 gold seed

### 任务 1.1：建立对象映射表

**输入**

- `AgtXIv.md` 第 5--7 节；
- `Stabilizerness/AGTXIV_IMPLEMENTATION.md`；
- `Stabilizerness/DAG_AND_ROOTS.md`；
- `agents/*/knowledge/statements.jsonl`；
- `agents/*/reasoning/chains.jsonl`；
- `agents/*/source/anchors.jsonl`；
- `agents/*/exports/*.json`；
- `Stabilizerness/dag/claim-dag.json`；
- `graph/claim-dependencies.json`。

**操作**

- 列出实际 `kind`、`origin`、`operation`、status 和 edge type 枚举；
- 建立 whole-paper ID 到 Agent `Statement` ID 的显式映射；
- 标记没有对应 Agent 对象的审计节点；
- 不修改现有 JSON/JSONL，只产生 sidecar 设计。

**输出**

- 版本化的数据字典；
- whole-paper/Agent 映射清单；
- 枚举冲突清单。

**验收标准**

- 现有 50 个 statements、23 个 steps 和 7 个 contracts 均能映射到数据字典；
- 同名不同义状态被识别；
- 不使用自由文本替代应当存在的对象 ID。

### 任务 1.2：冻结标注协议

**输入**

- `docs/LIGHTWEIGHT_DAG_MODEL_RESEARCH.md` 第 8 节；
- 当前仓库中的正边、blocker、proof gap 和 counterexample。

**操作**

- 定义节点类型、四类依赖、`edge_decision=NO_EDGE/UNKNOWN` 与 `evidence_status=BLOCKED_MISSING_*`；
- 定义原子化、方向、双证据、负例和冲突规则；
- 为以下易混淆例写标注判例：citation-only、proof gap、refutation、scope mismatch、capacity/coverage、同义复述、版本变化。

**输出**

- 标注手册 v0.1；
- 至少 20 个判例和裁决理由；
- reviewer 分歧记录格式。

**验收标准**

- 两名标注者可独立区分 citation 与 dependency；
- 能分别标记“定理被反例推翻”和“来源证明有缺口但定理未被反驳”；
- 跨论文正边均要求双证据。

**阶段停止条件**

若两轮讨论后仍无法形成可操作的 dependency 定义，暂停后续模型工作，先修订协议。

### 任务 1.3：构造首批 gold seed

**输入**

- 当前仓库工件；
- 5--10 篇与 Stabilizerness 纵向链直接相关、已有冻结来源的小论文集合。

**操作**

- 对现有工件做格式统一而非改写真值；
- 额外标注 load-bearing claim、双 evidence、正边、分层负例和 unknown/blocked；
- dev/test 全双标，训练 seed 至少 20% 双标；
- 第三人裁决分歧。

**输出**

- 150--250 个 gold claim；
- 100--200 条正边；
- 约 500 条分层负例/unknown/blocked；
- canonical work family 和 split group。

**验收标准**

- 每个对象可回到冻结 anchor 和 artifact hash；
- 没有把未审查随机 pair 当成 `NO_EDGE`；
- dev/test 不包含同一论文版本或近重复 claim 的泄漏。

---

## 4. 第 2 周：Claim extraction 与结构基线

### 任务 2.1：实现高精度规则候选器

**输入**

- 冻结 LaTeX；
- theorem/lemma/definition/equation 环境；
- 章节、段落、标签和 citation marker；
- 触发短语词表。

**操作**

- 优先解析 LaTeX 结构，不先处理 PDF；
- 识别 theorem、definition、assumption、claim、limitation、counterexample 和 numerical result 候选；
- 保存 verbatim span、section path、行/字符范围和 content hash。

**输出**

- claim candidate JSONL；
- 漏检和误检报告；
- 可重复运行的规则版本号。

**验收标准**

- schema/anchor validity 为 100%；
- 对现有 load-bearing claims 的 recall 达到人工可用水平；
- 规则不生成无法回指原文的文本。

### 任务 2.2：建立小型 encoder 基线

**输入**

- 第 1 周 gold spans；
- 规则候选；
- SciBERT 与 ModernBERT-base 或 DeBERTa-v3-base。

**操作**

- 比较规则、token/span classifier、规则+classifier；
- 预测 span、kind、origin 和 atomicity；
- 暂不引入 7B 生成模型；
- 量词、否定、exactness 和 scope 作为单独错误类别。

**输出**

- 至少两个 encoder 基线结果；
- paper-held-out dev 报告；
- persisted prediction、config、seed 和 checkpoint 标识。

**验收标准**

- 神经模型必须稳定优于或补充规则基线；
- 所有预测仍保留原文 span；
- 规范化草案不能覆盖 verbatim source。

**阶段停止条件**

若 encoder 没有稳定超过规则+人工确认，MVP 保留规则基线，不扩大参数规模。

---

## 5. 第 3 周：Candidate retrieval

### 任务 3.1：建立最小索引

**输入**

- gold 与候选 `Statement`；
- 同论文上游 claims；
- 被引论文 claims；
- 已知 contracts 和 foundations；
- OpenAlex/Semantic Scholar 按 ID 获取的少量元数据。

**操作**

- 建 BM25 索引；
- 建符号/公式 token、section、citation-neighborhood 特征；
- 建 E5/BGE 类 dense 索引；
- 不下载全量外部语料。

**输出**

- BM25、dense、hybrid 三套 top-$k$；
- 每个候选的分数分解和来源版本；
- oracle candidate coverage。

**验收标准**

- 报告 Recall@5/10/20/50 与 MRR；
- Recall@20 的项目目标为至少 0.85；
- citation-only 和无 citation 的真实依赖都进入候选池；
- 候选规模可供下游 cross-encoder 运行。

### 任务 3.2：建立 hard-negative 池

**输入**

- hybrid top-$k$；
- gold 正边和当前 false positives。

**操作**

采样：citation-only、反向边、同术语不同 claim、兄弟前提、旧版本、scope mismatch、capacity/coverage 混淆。

**输出**

- 带负例类型的 hard-negative JSONL；
- unknown/blocked 隔离表。

**验收标准**

- 不把 unknown/blocked 用作负例；
- 每类关键强负例在 dev/test 中均有覆盖。

**阶段停止条件**

若 oracle candidate pool 漏掉超过 10% 的 gold premise，先修 claim extraction、版本映射和索引，不训练 edge classifier。

---

## 6. 第 4 周：Edge typing、方向与双 evidence

### 任务 4.1：训练 cross-encoder 基线

**输入**

- top-$k$ candidate pairs；
- gold/weak labels；
- target 和 source 的局部上下文；
- citation intent、symbol 和 version 特征。

**操作**

- 使用 150M--600M pair classifier；
- 联合预测 edge type、direction、target-use span、source-statement span 和 abstention；
- 比较随机负例与 hard negatives；
- 教师弱标注必须保存模型、prompt/rule hash 和原文 span。

**输出**

- edge candidate JSONL；
- 双 evidence spans；
- 正交的 `edge_decision`、`evidence_status` 和 `upstream_claim_status`；
- 模型卡草案与失败类型表。

**验收标准**

- high-confidence scientific dependency precision 目标至少 0.85；
- citation-only 子集的 dependency false-positive rate 不高于 0.10，并分别报告 `NO_EDGE` 与 `UNKNOWN` 比例；
- unknown/blocked recall 目标至少 0.80；
- 双 evidence 可由 reviewer 快速定位。

### 任务 4.2：概率校准和拒答

**输入**

- paper-held-out dev predictions。

**操作**

- temperature scaling；
- 每类边分别报告 reliability；
- 选择 $t_{\mathrm{candidate}}$ 和 $t_{\mathrm{noedge}}$；这些阈值不改变合同的 `accepted` 状态；
- evidence 不完整时强制降级。

**输出**

- calibrated scores；
- ECE、Brier 和阈值配置；
- 高置信错误清单。

**验收标准**

- ECE 项目目标不高于 0.10；
- 阈值只用 dev 选择；
- 无 evidence 的高分类分数不能进入候选 DAG 正边。

### 任务 4.3：ReasoningStep 分组与输入角色

**输入**

- 已裁决的 pairwise edges；
- gold `step_id`、input incidences、operation、active assumptions 和 derivation evidence；
- 同一 target 的候选前提集合。

**操作**

- 规则只提出可能的 step grouping，不因共享 target 自动合并；
- 人工确认每个 `step_id`、`input_role`、operation 和 active assumptions；
- `UNKNOWN` grouping 保持未合并；
- 数据足够时才比较轻量 pair-to-step grouping 模型。

**输出**

- 带 `grouping_status` 的 reasoning-step candidate JSONL；
- 已确认的 `step_id + input incidences`；
- orphan-incidence 和 grouping conflict 报告。

**验收标准**

- assembler 不从二元边自行创造联合推理；
- 报告 step exact match、input-set F1、operation macro-F1 和 orphan-incidence 数；
- 小数据阶段所有高风险 grouping 均经人工确认。

**阶段停止条件**

若模型在 evidence 不完整时仍大量输出高置信正边，则只把它作为候选排序器，不进入自动构图。若 step grouping 无法可靠确认，则第 5 周只输出 pairwise 候选和待审超边，不宣称完成 `ReasoningStep`。

---

## 7. 第 5 周：DAG assembly 与端到端回归

### 任务 5.1：实现确定性构图器

**输入**

- statement candidates；
- calibrated edge candidates；
- reasoning step 候选；
- blockers、conflicts 和人工锁定边。

**操作**

- 检查 ID、anchor、schema 和方向；
- 只物化任务 4.3 已确认的 `step_id + input incidences`，不从共同 target 猜测 `ReasoningStep`；
- 增量 cycle check；
- 传播 blocker；
- 保存约束前后结果；
- 生成候选合同但固定 `accepted=false`。

**输出**

- 候选 statement/step JSONL；
- DAG incidence 索引；
- cycle/conflict/blocker 报告；
- 人工复核队列。

**验收标准**

- dangling ID 为 0；
- schema/anchor validity 为 100%；
- 静默 cycle 为 0；
- citation 不直接升级为 dependency；
- blocked 输入不产生 accepted 输出；
- 多前提不被压扁成含义不明的独立边。

### 任务 5.2：对当前 Stabilizerness 工件回归

**输入**

- `Stabilizerness/dag/claim-dag.json`；
- `graph/claim-dependencies.json`；
- 7 个 contracts、blockers 和 source anchors。

**操作**

- leave-one-branch 或 leave-one-paper 回归；
- 专门测试 V-representation proof gap、fixed-window monotonicity counterexample 和 Fig. 2 blocker；
- 比较约束前后 typed edge、blocker 传播和 cycle。

**输出**

- 端到端回归报告；
- 误差按 claim/retrieval/edge/assembly 归因；
- 与现有 validator 的兼容性报告。

**验收标准**

- 不把 proof gap 写成 theorem false；
- 不把已判假的 monotonicity claim 作为 accepted premise；
- 不把 Fig. 2 标为 reproduced；
- load-bearing premise coverage 目标至少 0.90。

**阶段停止条件**

出现任一状态提升错误时阻断发布，先修状态传播和测试。

---

## 8. 可选第 6 周：扩充 gold、主动学习与用户测试

### 任务 6.1：主动学习扩标

**输入**

- 中间置信度样本；
- 模型分歧；
- cycle/conflict；
- high-confidence false positives。

**操作**

- 优先标注最影响 load-bearing chain 的样本；
- 保持 dev/test 冻结；
- 扩充 citation-only、blocked 和跨论文边。

**输出**

- 300--600 个 gold claims；
- 200--500 条正边；
- 1,500--3,000 条审查后的负例/unknown/blocked；
- 400--1,000 组 evidence spans。

**验收标准**

- 新论文 family 上的性能没有明显崩溃；
- gold 增量有清晰 provenance；
- 弱标签和 gold 权重、来源可区分。

### 任务 6.2：小规模 reviewer 可用性测试

**输入**

- 固定数量的自动候选与纯人工对照任务。

**操作**

- 记录每条边审核时间、每篇总时间、漏掉的关键依赖和高置信误导错误；
- 收集 reviewer 对证据展示和拒答状态的反馈。

**输出**

- 人工时间与错误分析；
- 下一版本优先级；
- 是否进入稳定版的决策记录。

**验收标准**

- 相比纯人工，复核时间有可测下降；
- 高置信错误不会诱导 reviewer 错误接受；
- reviewer 能从输出直接回到双方原文。

---

## 9. 首轮实验矩阵

只运行小规模、可解释的对照：

| 模块 | Baseline A | Baseline B | Baseline C |
|---|---|---|---|
| Claim | 结构规则 | SciBERT | ModernBERT-base |
| Retrieval | BM25 | E5/BGE dense | hybrid |
| Edge | 规则 | cross-encoder | cross-encoder + hard negatives + calibration |
| Generation | 不使用 | 受约束规范化草案 | 仅困难样本教师 |
| Graph | 无约束候选 | 硬约束 DAG | 暂不训练 GNN |

选择标准依次是：证据完整性、高置信 precision、blocked recall、校准、人工时间、资源成本。总 F1 不是唯一标准。

---

## 10. 资源与角色建议

### 最小人员

- 1 名工程/ML 负责人：解析、索引、训练和构图；
- 1 名领域标注者；
- 1 名第二标注者/裁决者，可兼职；
- 每周一次 schema 与错误复盘。

### 最小硬件

- CPU 8--16 核、RAM 32--64GB；
- 推荐一张 24GB GPU；12--16GB 也可完成 encoder 基线；
- 不需要 80GB GPU 或集群。

### 外部数据策略

- 只按论文 ID 获取最小样本；
- 不下载全量 OpenAlex、S2ORC 或 unarXive；
- 先用公开数据做辅助任务，不把其标签直接转换为 dependency gold；
- 在任何训练前记录数据、代码和模型权重的独立许可证结论。

---

## 11. 每周决策门

| 时间 | Go 条件 | No-Go / 回退 |
|---|---|---|
| 第 1 周末 | dependency 定义稳定、双证据可操作 | 回到标注协议 |
| 第 2 周末 | claim anchor 100% 合法，模型补充规则 | 保留规则+人工，不扩模型 |
| 第 3 周末 | Recall@20 接近/达到 0.85，oracle pool 完整 | 修索引和版本映射 |
| 第 4 周末 | 高置信边有双 evidence，citation-only dependency FPR 低，step grouping 可确认 | 仅作排序器和人工标注辅助，不自动构图 |
| 第 5 周末 | 无静默 cycle/状态提升，blocker 正确传播 | 阻断发布并修 validator |
| 第 6 周末 | 未见 paper family 可用且减少人工时间 | 不进入 GNN/更大模型 |

---

## 12. 6 周后的下一步，不属于本 MVP

只有 MVP 通过后才考虑：

1. 把 sidecar schema 升级为正式 `Statement`、`ReasoningStep`、`ClaimContract` schemas；
2. 建立 reviewer UI 和签名/裁决记录；
3. 扩展到多学科 paper-held-out 集；
4. 对 1.5B--3B 模型做 LoRA/QLoRA，比较是否改善原子化；
5. 达到 50--100 张独立 gold 图后再评估 GNN/graph transformer；
6. 修复 `tools/query_agent.py` 的递归 accepted-chain 判定；
7. 统一 whole-paper DAG 与 Agent DAG 的 ID 和事实源；
8. 将新的 schema validator 纳入发布门。

## 13. 最终执行结论

前 4--6 周的正确目标是建立**provenance-first、evidence-first 的候选生成器**。先把标注协议、检索召回、边证据、拒答和状态传播做对，再决定是否需要更大的语言模型。若一个组件不能减少人工时间、不能提供双侧证据，或会把 citation/blocker 错当成科学依赖，它就不应进入 AgtXIv 稳定流水线。
