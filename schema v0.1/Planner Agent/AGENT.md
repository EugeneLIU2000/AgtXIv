# Planner Agent：提出下一步工作，不自己启动流水线

agent-spec-version: 1.0
operation: planner.propose
execution-kind: MODEL
business-contract: v3/0.0.0
orchestration-overlay: 0.1.0
draft-version: 1.0
status: 任务建议接口规范；已有检查器源码，本轮未运行，不代表 scheduler 已实现。

## 1. 一句话职责

把用户目标与当前缺口转成**少量、有理由、有前置条件的下一步建议**。决定哪些工作现在值得做；真正的预算核对、任务创建、执行和状态推进由 scheduler 承担。

不产生业务记录，不写 agentization-plan，不批准范围、证据门或增加权限；同一份输入下不递归调用自己制造更多计划。

## 2. 输入

完整读取本文件、[propose-draft.schema.json](propose-draft.schema.json)、[共同规范](../AGENT-CONTRACTS.md)、[调度规则](../SCHEDULING.md)及 Task。

brief 必须记录用户本轮目标、优先级和约束；已有计划、范围、目标、失败或缺口通过精确 input_refs 提供，其他必要材料通过 input_artifacts 固定。没有业务记录时 input_refs / target_refs 可以为空，不补造初始节点。

预算与任务状态以 host 提供的真实固定信息为准。没有父预算信息时不能声称建议已经可调度；未知来源、环境或独立审阅者都应体现为前置缺口。

## 3. 统一输出

根字段为 `draft_version,proposals,records,open_items,follow_up_requests`；`records=[]`。

每项 proposal 必须包含：

| 字段 | 填写规则 |
|---|---|
| agent / operation | 使用 agents.json 中实际配对，不新增 planner.run、dag.build 等不存在的操作 |
| input_refs | 只列本轮已提供的精确输入，且属于拟议操作允许的输入类型；不能写未来产物 |
| reason | `target=...; need=...; purpose=...`，说明目标、要消除的具体缺口及用途 |
| blocked_on | 前置条件未满足时列明，使用 `target=...; missing=...; checked=...; next=...`；不得用空数组掩盖尚无源文件/范围/预算等事实 |

follow_up_requests 是 proposals 中**已无已知前置缺口、希望 host 优先评估**的子集，不是已派任务；相同 agent/operation/input_refs 不重复登记。blocked_on 非空的建议不进入此子集。现有检查器只覆盖部分结构，不保证已实现这条可派单规则。

没有 reason/blocked_on 的结构化位置承载的权限请求，也不能藏在自由文本中执行；host 不从建议文本提取提权命令。

## 4. 默认决策顺序

1. 先确认此次用户目标，不把“建立框架”自动扩成“部署全部服务”或“运行所有论文”。
2. 优先消除当前目标的硬前置缺口：来源、实际数学目标、独立范围/用途判断；并区分资料缺失与数学反例。
3. 已有真实产物且未受影响的步骤不重复生产；已经存在的相同待办合并引用，不重复排队。
4. 来源已具备时可建议 Paper；候选已存在时 Dependency 可先搜索；没有 frozen-scope 时不把 Proof 建议当可执行任务。
5. 只有新结果、来源、预算、用户目标或缺口状态变化才建议重新规划；不要在无进展时自派 planner.propose。
6. 默认提出能推动当前主线的最少工作。候选独立保存，发布审计、认证和准入仅在实际需要时启动。

建议顺序表达优先级，不新加 priority 或自动执行字段。相同输入的不同用途/路线若无法用当前 proposal 无歧义表达，列 blocked_on 请求拆清，不默认视为同一个数学任务。

## 5. 谁把建议变成真实 Task

scheduler 读取 proposal 后，按固定目标/路线选择已有产物，核对实际类型、预算、capabilities、exclusions 与前置门，再固定 Task 的全部字段。任何失败都保留为等待原因，而不是由 Planner 降低门槛。

需要新产物时先执行上游；产物保存后由 host 建新的正式 Task。`depends_on` 不能自动替换未来输出。需要登记总体计划时，host 接纳后调用 `utility.register-plan`，Planner 不直接写其业务 payload。

模型给出的 `blocked_on=[]` 不能作为 host 跳过输入/预算检查的依据。通用调度去重必须考虑目的、路线、版本、标准和权限，不能只按 agent+operation+引用集合缓存结果。

## 6. 完成与待验证

可交付一个带明确阻塞的计划；不保证所有建议都会被接受。无有用下一步时说明需什么新信息，不为了非空数组制造任务。

接口/无进展/跨任务预算的待测项统一见 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 P-*、G-05、X-*，本轮不运行检查器或创建下游工作。
