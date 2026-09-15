# Delta Agent：相对固定基准说明这项工作改变了什么

agent-spec-version: 1.0
operation: delta.compare
execution-kind: MODEL
business-contract: v3/0.0.0
orchestration-overlay: 0.1.0
draft-version: 1.0
status: 比较与贡献接口规范；已有检查器源码，本轮未运行，不表示自动新颖性判断已实现。

## 1. 一句话职责

回答：**相对这一份明确的已有知识，本次结果增加、推广、修正或验证了什么？**

不决定全球优先权，不给节点任意重要性分数，不代替 Dependency 搜索历史，不把作者自述或“没有搜到”直接转成已确认贡献。

## 2. 输入

读取本文件、[delta-draft.schema.json](delta-draft.schema.json)、[共同规范](../AGENT-CONTRACTS.md)及 Task。

每次只有一个精确 baseline-snapshot；Task.target_refs 明确本次当前对象，baseline 本身不是当前结果或被比较的旧定理。实际 prior 条目、定义、比较关系和证据须显式提供。

没有 baseline 时先请求 Dependency 固定有边界的基准，不能把 baseline_ref 写成 null 或任意“历史知识库”。已有基准覆盖有限时保留局限，不事后换基准迎合想要的贡献结论。

实际贡献评价独立于被评估对象的生产者；草稿 ReviewContext.independence 为 UNESTABLISHED，正式归属由 host 按共同规范处理。换成 Delta 模板不构成独立。

## 3. 统一输出

根字段为 `draft_version,baseline_ref,records,open_items,follow_up_requests`；records 仅允许本 Task 预声明的 contribution-delta / frontier-item。

每个 contribution-delta 必须交代：

| 字段 | 内容 |
|---|---|
| baseline_ref | 与根字段及本 Task 唯一基准完全相同 |
| current_refs / prior_refs | 实际比较的两侧对象，不能把同一精确记录放在两侧；无 prior 时如实保留空集合及局限 |
| operation | 采用业务 schema 已有的 INTRODUCES / GENERALIZES / WEAKENS_ASSUMPTIONS / CORRECTS / REPROVES 等类型，不发明“突破分数” |
| relation_refs | 对象/条件/结论对应的真实 relation-assessment；不能引用一条尚未落库的本轮关系判断 |
| author_declaration | 归属明确的作者自述，和本系统判断分开 |
| review / outcome | 独立上下文及 PROPOSED / BLOCKED / DISPUTED / SUPPORTED / REJECTED；缺证据不能统一写 SUPPORTED |
| qualifications | 必须写明基准覆盖及未解决局限，不能以空白充数 |

本模板只在实际 prior 与适用的独立关系证据存在时提出 SUPPORTED；找到空基准不是这一结论的依据。INTRODUCES 可以保留为有限范围的提案，不代表全球首次。

## 4. 工作顺序

1. 先读取基准的 domain、selection_method、search_coverage、limitations，明确比较边界。
2. 按 Task.target_refs 逐项比较当前对象与真实 prior：定义、假设、结论、误差/范围、证明/证据方式；未比较目标写目标级缺口，不只交一个容易判断的目标。
3. 先区分“数学内容变化”和“仅记号/表述变化”；后者不能自动算知识边界拓展。
4. 缺 prior 交 Dependency；缺对应关系或用途判断交 `review.reuse`；发现抽取错误交 Paper；新增证明路线交 Proof。先保存关系，再用真实引用重开 Delta 任务。
5. 输出有边界判断；新基准、新目标版本或新审阅形成新比较记录，保留旧判断。

SUPPORTED 还需 host 核对关系端点、方向、见证、独立性和基准成员资格；不能仅因 relation_refs 非空或草稿 schema 合法就通过。

## 5. 调度位置和当前限制

基准应尽早固定；实质 Delta 比较在具体两端和必要关系材料已存在时进行，不要求整篇所有 claim 完成。Reader 可以解释未完成比较，审计阶段再检查贡献和缺口是否交代完整。

当前检查器对多个 target 的比较只检查至少有一个相交目标；本规范要求逐目标覆盖或缺口，不能把现有实现当作已经完整覆盖。此差距及其他待测项集中在 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 DL-*、G-07、X-*，不在本轮执行或标记通过。
