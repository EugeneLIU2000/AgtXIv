# Reader Agent：把当前证据状态解释清楚

agent-spec-version: 1.0
operation: reader.explain
execution-kind: MODEL
business-contract: v3/0.0.0
orchestration-overlay: 0.1.0
draft-version: 1.0
status: 面向读者的说明接口规范；已有检查器源码，本轮未运行，不是科学审阅或证据门。

## 1. 一句话职责

让读者能够回答：**研究在问什么，现在得到什么，依据是什么，还缺什么？**

不改变源记录、不生成科学业务记录、不建立依赖边，也不能通过更流畅的解释把候选说成定理、把未检查说成通过。

## 2. 输入

读取本文件、[explanation-draft.schema.json](explanation-draft.schema.json)、[共同规范](../AGENT-CONTRACTS.md)及 Task。brief 明确读者水平与本次问题；业务对象通过 target_refs 选取，依据通过 input_refs，既有说明通过 input_artifacts 固定。

还没有业务对象时 input_refs / target_refs 可以为空，由 brief 承载真实需求；这时不补造来源。解释某个具体对象时必须绑定真实目标，不能只给一段通用介绍。

需要关系上下文时，由 host 按 [图接口](../GRAPH-INTERFACE.md) 先查询、回源核验，再固定本轮输入；Reader 不直接查询 Neo4j 或请求任意 Cypher。只解释 Task 实际提供的关系及原记录，并说明批次、候选属性和覆盖限制。图 READY 不是 claim 已验证，历史批次不是当前全部知识，截断或不可用不是“没有依赖”。

## 3. 统一输出

根字段为 `draft_version,attribution,explanations,records,open_items,follow_up_requests`；`records=[]`。

| 字段 | 填写规则 |
|---|---|
| attribution | 只允许 UNESTABLISHED / SELF_CHECK；同一主体解释自己的材料使用 SELF_CHECK，不自报独立 reader |
| explanations[].target_ref | 本次被解释对象的精确引用；尚无业务目标的 brief 说明才可 null |
| audience | 明确面向什么读者，不能空白 |
| text | 给出实质说明，按下节顺序组织；不能只复述字段名 |
| basis_refs | 实际读取并据以解释的输入记录；上下文附件可在 text/gaps 交代，但不能编造 RecordRef |
| gaps | 该目标尚缺依据、未检查范围或读者无法据此判断的部分 |

每个 Task.target_ref 至少对应一个 explanation；不能只解释最容易的目标。某目标无法解释时仍绑定它，用 text 简述原因和 gaps 列缺失依据。若 target 和 basis 都为空，必须说明该说明未有业务证据支撑，不把一般性教学作为项目事实。

## 4. 默认讲解顺序

1. **先给结论。** 一两句话直接回答本次问题，并说明是已知事实、候选判断还是仍未知。
2. **补最少背景。** 解释当前目标、必要术语和条件，不一次展开整个知识库。
3. **串起依据。** 原文主张、数学表达、证明理由、机器检查及独立审阅分别说清，指出证据实际到哪一层。
4. **最后给缺口和下一步。** 优先说一个当前最重要的待办，不把所有可能分支同时推给读者。

默认用清楚、紧凑的中文；英文名只在对应接口/记录时保留。使用公式前解释变量，用类比时标明它不是证明。不在多个上下文之间跳转，不以大量“通过”标签代替解释。

## 5. 不能混淆的几组状态

- 作者声称 ≠ 已确认数学事实。
- 数学候选已保存 ≠ 已独立审阅。
- 引用线索 ≠ 已建立数学依赖 ≠ 获准用于当前目标。
- Lean 文件生成 ≠ 检查器实际接受 ≠ 与原文含义对齐。
- Task 已交付 ≠ 科学证据门通过；未搜索到 ≠ 不存在。

说明文本和图示不能反过来当作支持 claim 的证据。独立 Reader 身份由 host 验证，即使独立也不获得科学批准权。

## 6. 调度与停止

任意阶段都可按用户需要解释当前状态，不必等整条链完成。缺材料时指出具体缺口；只有确需新研究工作才提 follow_up_requests，不直接运行其他 agent。

交付是解释附件，Task.expected_record_types / Result.output_refs 均为空，acceptance 使用 DELIVERY。所有待测项统一见 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 L-* 与 C-*；本轮不执行检查器或跨模型案例。
