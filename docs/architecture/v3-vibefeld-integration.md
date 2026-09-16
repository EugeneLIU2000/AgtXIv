# V3 数学论证中间层：vibefeld 接入设计与依据

**状态：** 设计提案、静态阅读记录；不是集成实现或安全认证。

**日期：** 2026-09-05。

**主文：** [AgtXIv V3](../../AgtXIv.md)，[实施清单](../roadmaps/v3-implementation-plan.md)。

**上游：** [tobiasosborne/vibefeld](https://github.com/tobiasosborne/vibefeld)。

**本次固定提交：** [`392b2da3bee5766cca1a201f28e0255056baaba4`](https://github.com/tobiasosborne/vibefeld/commit/392b2da3bee5766cca1a201f28e0255056baaba4)，2026-09-02。后续接入必须重新确认所选版本的能力，不能依赖浮动 main。

## 1. 采用的部分与 AgtXIv 的责任

vibefeld 提供自然语言数学论证的工作环境：拆解步骤、提出质疑、回应异议、管理局部假设、记录历史。它填补原文“因此可得”与形式系统所需明确步骤之间的空白。[上游 README](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/README.md)。

AgtXIv 保留对原始科学主张、完整跨论文依赖、六轴评估、复用条件及知识准入的解释权。Lean 对固定的形式声明提供内核检查。三个系统没有一个可代替其余两者的全部责任。

采用的是一个**受控的论证工作引擎加适配层**。首版不修改上游状态语义，不把 graph export 当知识数据库，不等待上游实现 Lean exporter。工作区自身报告的状态保留在 `upstream_report`，V3 评估由独立记录表达。

## 2. 固定版本能力核实

以下均来自静态文档/源码阅读；本次未运行上游命令、示例或测试。仓库入口通过网页读取，固定提交及源码通过 GitHub 连接器读取；未克隆、安装或执行上游。若文档与实现不一致，以被固定的具体实现路径为接入审计依据，同时保留差异。

| 项目 | 观察到的上游能力与限制 | 对 V3 的直接影响 |
|---|---|---|
| 论证与异议 | 节点、层级结构、异议、回应与接受流程已有实现 | 可用于候选论证及公开审阅证据的生产 |
| `validated` / `closed` | 前者是审阅接受；后者是上游树内流程状态，允许某些 admitted/archived 状态 | 只导入其原始报告，不直接赋予 V3 数学支持或发布资格 |
| 不确定性传播 | 树范围传播已有实现；引用依赖、外部引用不等同于树路径 | V3 对完整依赖重新计算影响，不沿用 `clean` 作为闭合证明 |
| 普通接受命令 | 普通 acceptance 路径不因作者与 verifier 相同而自动拒绝 | 受控调度及导入校验必须核查实际生产者/审阅者 |
| 批量 verdict | 有作者与 reviewer 比较及 `expect_hash` 检查；身份来自输入，缺失时限制仍在 | 不能说上游毫无身份检查，也不能把字段比较当认证身份 |
| 事件记录 | 可重放，按追加方式记录操作；未形成独立锚定的防篡改历史 | V3 需独立保管事件收据、快照与发布检查点 |
| 局部作用域 | 有假设、解除假设、scope 数据结构和校验模块 | 尚不能推断普通 acceptance 必然执行所有 scope 校验；适配层显式检查 |
| graph JSON | 有版本/能力信息、引用边、部分身份与工作状态 | 缺少 context、scope、validation dependencies 及完整异议正文，不能单独用于完整交接 |
| 节点内容哈希 | 源码实际包含 `validation_deps`；不覆盖所有范围、身份、状态等上下文 | 必须对完整快照另做 V3 哈希；不能凭节点 hash 判定整个审阅仍有效 |
| 形式导出 | Markdown、LaTeX 和 JSON graph 已有；Lean 导出在 roadmap | AgtXIv→Lean 交接是 V3 新工作，不能计入现有功能 |

能力边界的直接来源：

- 树风险和已知绕过方式：[trust-model.md](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/docs/trust-model.md)。
- 接受流程：[internal/service/proof.go](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/internal/service/proof.go#L830)；批量检查：[verdicts_apply.go](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/internal/service/verdicts_apply.go)。
- 导出字段：[export-graph-v1.md](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/docs/export-graph-v1.md)、[internal/export/graph.go](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/internal/export/graph.go)。
- 实际哈希覆盖：[internal/node/node.go](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/internal/node/node.go#L220)。文档对该覆盖的描述存在滞后，尤其不能写成 `validation_deps` 未参与哈希。
- 作用域校验：[internal/scope/validate.go](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/internal/scope/validate.go)、[scope_acceptance_test.go](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/e2e/scope_acceptance_test.go)。该测试中的手动 scope 检查不能证明普通接受路径自动执行相同检查。
- 导出格式：[cmd/af/export.go](https://github.com/tobiasosborne/vibefeld/blob/392b2da3bee5766cca1a201f28e0255056baaba4/cmd/af/export.go)。

## 3. 完整快照的输入输出契约

### 3.1 调度输入

每个工作项固定以下信息：

```text
任务身份和实际执行者
精确 ScientificClaim 与来源组件引用
处理标准、处理范围和资源预算
候选 MathClaimIR 及科学语义引用
已允许使用的定义、引理和外部知识版本
vibefeld 提交、适配器版本、命令/导出能力
Prover/Verifier 可见输入与权限
```

调用命令的请求、实际 actor、输入摘要及输出回执由工作区外的调度记录保存。论证 agent 不持有正式评估、发布或知识入库的写权限。若允许直接修改工作区文件，导入必须检查这种变化并标出无法归因的历史，不把它伪装成命令产生的已审阅事件。

### 3.2 冻结输出

`ArgumentSnapshot` 至少同时绑定：

1. 上游事件 ledger 及封存的事件范围；
2. graph JSON 及其版本/能力声明；
3. 定义、局部假设、解除假设、context、外部引用、普通与 validation dependencies；
4. 完整异议正文、目标版本、回应、撤回/解决/替代记录；
5. 节点的 author、proof_author、validated_by 与实际执行身份对应；
6. AgtXIv 稳定节点身份到上游 workspace/node 的映射；
7. 每个承重步骤的来源、科学主张组件和证明方案归属；
8. 上游原始状态、V3 导入结果、缺失项和独立审阅记录；
9. 所有被绑定文件与记录的内容指纹、类型和大小。

上游 workspace 的绝对目录不能作为可复用科学身份。移动目录不改变命题，变更主张条件却必须改变相应版本。数据缺失时停止相应的支持评估，保留可读的历史材料；不能猜测 scope 或审阅者。

### 3.3 导入时的检查顺序

```text
确认版本和导出能力
→ 保存原始字节及取得履历
→ 解析记录并核对内容、事件和引用一致性
→ 重建完整 scope、共同前提、引用与证明方案
→ 核对实际身份与审阅范围
→ 保留 reported_verifier_acceptance 等原始事件
→ 独立评估是否可作为 V3 ArgumentReview 证据
```

上游 `validated` 最初只对应“上游报告审阅接受”。即使独立导入校验通过，也只使它成为可追溯的审阅证据；数学轴结果还需要针对目标、假设和其他证据作出评估。

## 4. 最容易出错的四个接口

### 4.1 归档不是解除证明义务

固定本次论证需要交代的义务集合。某步被归档，需独立记录它被什么替代，或者为什么不再被结论使用。没有这种记录，原依赖仍待处置。

上游 graph 的 `closed` 对部分阻塞异议有额外检查，所以不能简单说“归档必然让 closed 通过”。但无论其返回什么，都不能证明必要数学步骤没有被删除。V3 检查的是冻结的义务和实际推理关系。

### 4.2 前提、占位和物理假设有不同含义

- 正确形式化的“假设 H 则 C”可以是条件定理；H 需要清楚显示。
- 以未证引理代替原本必须证明的步骤，会留下证明义务。
- 模型假设缺经验支持，会限制面向实际系统的科学推断，但不自动否定其条件数学推论。
- 存在互相矛盾的数学前提时，形式系统仍可能推导结论；内核通过不能替代前提相容性与适用性审查。不能确定时记录未知。

因此影响传播按依赖种类、证明方案及评估轴进行。V3 不把所有问题压成一个 `tainted`。

### 4.3 探索性 Lean 与可发布证据分开

尚未审阅完的论证也可交给 Lean 尝试，发现缺定义、缺假设或错误量词。探索结果仍是候选。要作为发布支持，必须固定精确交接包并满足独立对齐、声明/公理政策、论文审计与准入条件。

允许 alternative proof：原文推导有缺口，但另一条严格证明支持同一结论。分别保存原文、重建、修补与替代证明的归属；若贡献是新证明方法，还须单独评价该方法。

### 4.4 修改之后哪些审阅过期

节点陈述、局部假设、定义、引用依赖、异议状态或审阅可见上下文改变，都可能影响判断。`expect_hash` 或节点内容 hash 没变，不能单独说明审阅仍适用。V3 审阅绑定完整上下文快照，局部变化计算受影响目标，再生成新审阅版本。

纯显示变化无需重做科学核查；这要求语义记录与网页输出分开。

## 5. 接入验收设计

以下是后续实现的验收要求，未在本次执行：

| 编号 | 输入情形 | 必须观察到的行为 |
|---|---|---|
| VF-01 | 同一快照在不同绝对路径读取 | V3 对象身份稳定，上游原始目录作为履历保留 |
| VF-02 | graph.json 有节点但缺少 scope/context | 不生成伪完整交接包；给出精确缺失项 |
| VF-03 | 引用一个不在树路径上的未证引理 | 该依赖影响相应方案，不能因上游 clean 漏掉 |
| VF-04 | 同一 actor 用不同 owner/reviewer 名称 | 拒绝作为独立审阅；保留原始事件 |
| VF-05 | author 与 proof_author 不同 | 对实际参与待审证明生产的 actor 检查冲突 |
| VF-06 | 归档难以证明的必要步骤 | 义务保留，除非有独立认可的替代/移除理由 |
| VF-07 | 修改 scope，节点内容 hash 不变 | 旧范围审阅不满足新快照的认可条件 |
| VF-08 | 修改 validation_deps | 核对实际源码的哈希覆盖及隐藏字段；不依赖过时文档 |
| VF-09 | ledger 与导出互相不一致 | 导入失败并保留差异；不能任选一个当真 |
| VF-10 | 工作区过去历史被改写 | 与独立收据/检查点不符时拒绝；无独立证据时只报告所获快照，不能证明历史未改 |
| VF-11 | 本地假设尚未解除但结论脱离该范围 | 阻止无条件导出，或明确输出条件命题 |
| VF-12 | 同一结论两个方案仅一个受影响 | 只使相关支持待复核，不删除独立方案 |
| VF-13 | 上游升级增加未知事件或改变状态语义 | 能力协商失败或明确降为不支持，不能静默忽略 |

## 6. 实施决策

首版采用固定提交的适配器、完整快照和 V3 自有审阅/依赖规则。先实现“能准确解释一次带缺口的调查”，再实现自动循环调度；先确保不能错误升级，再考虑提升审阅通过率。

只有后续实验证明有必要，才考虑维护上游 fork 或把部分能力贡献回上游。升级需重新检查导出、scope、身份、事件和 taint 语义，并重跑对应兼容性验收；旧快照永远按旧版本解释。
