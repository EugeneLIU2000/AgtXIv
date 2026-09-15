# Paper Agent 1.1 重跑：arXiv 2608.14798v1

论文：[Stabilizer Statistical Mechanics: A Framework for Efficient Quantification and Classification of Magic States](https://arxiv.org/abs/2608.14798v1)。
运行日期：2026-09-14。模型：`claude-opus-5`，单次交互执行。

**按 AGENT.md 1.1 的草稿接口与 R1–R8 重新提取；规范自带的离线检查器在 5 份草稿和 433 条记录上全部 0 错误。**
**仍然有一个阻塞：82 条自生成对应表被判 `SELF_REVIEW`。这是 R8 明确要求保留的状态，没有伪造审阅者。**

`mode` 为 `OFFLINE_DIAGNOSTIC`：本目录没有 `result.json`。没有调度器、没有运行身份、没有回执事实，就不造回执。

1.0 那次运行保留在 [../2608.14798v1-claude-opus-5](../2608.14798v1-claude-opus-5)，**未改写**，其校验脚本对当前 AGENT.md 的哈希比对会有意失败。

## 先看这三个文件

1. [主张阅读版](claims.md)：82 条作者主张，逐条列出条件、组件去向、数学目标、残余与开放项。
2. [机器记录](records.json)：433 条已装配 v0.0 记录。候选，不可当作已准入知识。
3. [校验报告](validation.json)：草稿层、装配层、完整记录集、源字节分层报告，含规范检查器的原始判定。

## 产物

| 产物 | 数量 | 说明 |
|---|---:|---|
| 作者主张 ScientificClaim | 82 | 按 R2 拆分：44 条有编号断言（命题 11、定理 14、引理 12、推论 5、算法 2），38 段无编号叙述单元 |
| 组件 Component | 175 | CONCLUSION 114、EVIDENCE 19、MODEL 14、LIMITATION 13、DEFINITION 6、ATTRIBUTION 4、ASSUMPTION 4、APPROXIMATION 1 |
| 数学目标 MathClaim | 84 | 每个可完整表达的 CONCLUSION 组件一个；EXACT 75、ASYMPTOTIC 8、APPROXIMATE 1；对象 186 个，从目标自身变量提取 |
| 定义 Definition | 16 | 含补充材料的 `Spec_S / Spec_R` 正则拆分 |
| 语义背景 SemanticContext | 2 | 仅 H₂ 与 Ising 两处数值应用需要 |
| 原文定位 SourceSpan | 97 | 全部按真实 TeX 字节区间与摘要绑定 |
| 对应关系 ClaimComponentMap | 82 | MAPPED 87、RESIDUAL 56、UNRESOLVED 28、NON_CLAIM 4；COMPLETE 25、PARTIAL 57 |
| 开放项 FrontierItem | 64 | 范围歧义 30、未证引理 7、模型假设 6、缺来源 6、冲突 5、对齐缺口 5、缺数据 4、资源限制 1 |
| 发现清单 InventoryDiscovery | 1 | 提出 109 项义务；**未冻结** |
| 宿主上下文 | 4 | 政策、标准、快照、计划 |

条件与假设共 **353** 条，**全部**带直接原文定位。

## 真实校验结果

```bash
.venv/bin/python -B 'schema v0.1/Paper Agent/check_output.py' \
  --draft 'schema v0.1/Paper Agent/example/2608.14798v1-claude-opus-5-v1.1/rounds/round-2-claims/draft.json' \
  --task  'schema v0.1/Paper Agent/example/2608.14798v1-claude-opus-5-v1.1/rounds/round-2-claims/task.json'
```

- **规范检查器**：5 份草稿逐份 0 错误，`missing_expected_record_types` 均为空；433 条完整记录 0 错误。1.0 那次的 67 处 `CONDITION_SOURCE_REQUIRED` 与 3 处 `CONCLUSION_REQUIRED` 已在源头消除。
- **装配不改 payload**：433 条记录逐条比对装配前后 payload 的规范化 JSON，全部相等。
- **源字节**：16 个来源文件重新读取并重算摘要，97 条 span 的字节区间摘要逐条重算。
- **完整记录集未通过**：82 条对应表触发 `SELF_REVIEW`。生产者与 claim 生产者是同一主体，`review` 又是必填字段，单主体运行无法两全。
- **诊断子集通过**：移除对应表后的 **351** 条通过引用闭包、字节与形状检查。它不是 Paper Agent 交付物，因为 R8 要求每个组件都有对应行。

读回检查：

```bash
.venv/bin/python 'schema v0.1/Paper Agent/example/2608.14798v1-claude-opus-5-v1.1/host/verify.py'
```

14 项全通过。它把规范哈希变更作为 *findings* 报告而不是首条 assert，因此版本升级不会再遮住后面的检查——这是 1.0 那次的教训。

## 相对 1.0 那次运行的实质变化

| | 1.0 运行 | 1.1 重跑 |
|---|---|---|
| 模型返回形状 | 直接写完整记录（含 `producer`） | 只返回 `extraction-draft` 草稿，身份与哈希由宿主填 |
| 轮次 | 单轮 | 5 轮，顺序由真实引用依赖决定（span → claim → semantics → math → map） |
| 主张数 | 36 | 82（R2：有编号断言不合并） |
| 数学目标 | 30，挂在 claim 上 | 84，挂在 CONCLUSION 组件上（R6） |
| MathClaim 的 objects | 从定义表批量复制 | 从目标自身变量与载体提取（R6 明确禁止前者） |
| 条件来源定位 | 仅 claim 条件有 | 353 条全部有（R4） |
| 检查器错误 | 70 | 0 |
| Plan | 精简 12 字段试样 + 兼容性失败记录 | 只用 v0.0 完整字段（INTERFACE §5 已废除精简 Plan） |
| 组件角色 | 把解释性结论降级为 `MODEL`，导致 3 条主张缺 CONCLUSION | 解释性结论按 R3 归入 `CONCLUSION`，modality 走 CONFORMANCE 阶梯 |

## 本轮更正了 1.0 的两处结论

读补充材料后，1.0 那次有两条记录是错的，这里更正：

1. **`Spec_R` 有定义。** 1.0 记为"全文从未定义"。实际上补充材料的 Proposition (Canonical Splitting) 定义了 `Spec_S / Spec_R`。真正的问题是：主文的可分态定理在使用该符号处没有前向引用。定理右端因此可以写出数学目标，1.0 那条 `MISSING_SOURCE` 降级为 `SCOPE_AMBIGUITY`。
2. **低温极限有定论。** 1.0 记为"两处印数不同且全文未调和"。实际上补充材料从 `Ĥ` 的奇偶分解推出 `Z_β → ½|STAB(ψ)|`，与 §III B 一致，因此 **§VI C 少写的因子 ½ 才是笔误**。这条从"待作者澄清"变成"可直接勘误"。

同时补充材料还给出了主文缺的一句关键依据：可分态定理证明里把 `2^{|A|-ν_A}` 注解为 `Spec_S(ψ_A)` 的基数，这**确认** `|A|` 在该定理中是比特数，与 §II 的 `d_A=|A|=2^n` 约定冲突。该项从"需澄清"升为 `CONFLICT`（可勘误）。

## 这篇论文暴露出的边界（64 项开放项中的主要几类）

以下是记录下来的待审阅事项，不是已经证伪的结论：

- **摘要强于正文的四处**：①"对每个参数值都是 magic monotone"——§V 只证了忠实性、Clifford 不变性、次可加性、丢弃子系统单调性、稳定子附加不变性，对声明的自由操作类 `𝔉`（含计算基测量）的单调性全文无证明，而单次互转定理的第一个不等式正是它；②"可由 Bell 采样高效估计"——实际保证是对**归一化截断** SPF 的可加误差，且截断底 `Δ(β,k)` 带 `2^n` 因子，论文没给出使其非平凡的 `k(n,β,ε)`，也没有把误差传播到 `W_β`；③"完整温度剖面携带严格更多信息"——"更多信息"未定义；④两个极限无推导、无误差项。
- **次可加性的支撑步骤未证**：cSPF 超可乘性依赖 `p_k/p⋆_k` 单调不增，论文断言未证；补充材料的支撑定理用同一未证步骤。
- **未过滤稳定子功不随偏迹下降**——这是选用 core SPF 的实质理由，但没有给反例或 β 范围。
- **算法 1–3 分支在渐近谓词上**（`δ=o(1)`）且假设精确 oracle；§IV D 说可用估计器替代，但没把归一化与截断条件带过去。
- **SPS 闭式只覆盖 `|S|=2^n`**，而伪魔法构造的密码学要害区间是 `log n ≤ k ≤ n`；SPS 的矩计算又是对**均匀随机**函数做的，而 SPS 用的是伪随机函数。
- **引用的稳定子保真度下界按印刷形式与 `F_Stab ≤ 1` 矛盾**（四比特 `M₂=2` 会逼出 `F_Stab ≥ 1/2`）。本轮未取引用文献，只记录冲突。
- **数值结果均不可复现**：H₂ 两组基、Ising、SPS 数值验证都没有数据、代码、几何或容差；`2.27×10⁻³` 阈值没给最优 β 与数值过程。

## 输入与执行证据

- [下载记录](acquisition.json)：固定 `2608.14798v1`，源压缩包与 16 个文件的 SHA-256。
- 原始压缩包与 TeX 在仓库 `Reference/Stabilizer Statistical Mechanics - .../`；源文件没有编译或执行。
- [提取种子](extraction/seed.json)：本次真实阅读的产物，`records` 由它装配而来。
- [各轮工作单与草稿](rounds/)：`task.json` 是本次固定的工作单，**不是调度器签发的**；`draft.json` 是该轮模型返回形状；`records.json` 是宿主装配结果；`validation.json` 是规范检查器对该轮的原始判定。
- 全部 5 轮由同一主体、同一会话完成。`identity_assurance` 一律 `DECLARED`；没有身份认证、没有外部模型计费测量、没有预算调度。Plan 的 `max_seconds=86400` 与 `max_cost_units=0` 是声明上限，从未强制也未测量，**0 不表示本次零成本**。

## 没有做什么

没有证明或否证任何数学目标；没有形式化；没有复现任何数值；没有取任何被引文献；没有冻结范围；没有生成 `scope-decision`、`frozen-scope`、`obligation-disposition` 或任何 Proof/Formalization 记录；没有写 Result 回执。跨模型一致性**未测量**——1.0 与 1.1 两次运行的主张数不同是拆分规则不同，不是一致性指标。
