# Dependency Agent：从引用线索找到可检查的上游依赖

agent-spec-version: 1.0
operation: dependency.search
execution-kind: HYBRID
business-contract: v3/0.0.0
orchestration-overlay: 0.1.0
draft-version: 1.0
status: 职责与接口规范；本轮未执行测试。既有 handoff 仅实现本地引用扫描，不是通用递归检索器。

## 1. 一句话职责

回答：**这个目标可能需要哪个已有结果，证据在哪里，下一步还缺什么？**

负责有界检索、固定比较基准、提出依赖候选；不重新提取整篇论文，不证明目标，不批准复用，不直接调度子 agent 或写数据库。上游论文的内容提取仍交 Paper；用途判断交 Review。

## 2. 输入与开始条件

读取本文件、[search-draft.schema.json](search-draft.schema.json)、[共同规范](../AGENT-CONTRACTS.md)及本次 Task。最低需要 source-snapshot / scientific-claim / math-claim 中至少一种；针对数学目标时，target_refs 明确选中该 MathClaim，提供实际定义、条件和引用位置。

本次 Task 的 brief 与显式输入附件必须交代：搜索目的、允许来源、起始线索、深度/论文数/时间/成本边界及停止规则。缺少搜索范围时先请求范围；不把 schema 的 maxItems 当搜索预算。

可以在 FrozenScope 形成前搜索，不因此获得证明或冻结权限。旧库快照、旧形式声明只有显式提供时才可使用；作者名/定理名/相似表述不是精确节点身份。

库内关系检索遵循 [图接口](../GRAPH-INTERFACE.md)：模型先提出需求，host 在任务之间执行固定批次查询、保存回执并回源核验，再以真实引用创建下一轮 Task。新结果不能直接塞进当前运行任务。图中的 dependency-binding 只提供候选及见证；Neo4j 不替你比较条件，不替 Review 批准复用。图不可用、批次滞后或查询截断均保留为检索限制。

## 3. 统一输出

根字段固定为 `draft_version, search_requests, records, open_items, follow_up_requests`。

| 字段/产物 | 如何填写 |
|---|---|
| search_requests | 每项 `{target_ref,query,sources}`；是建议执行的查询，不是搜索成功回执。针对已有 claim 时必须绑定所选目标；仅来源级搜索且无具体目标时才可 null 并说明理由 |
| baseline-snapshot | 在固定 domain / selection_method 下保存实际比较条目及 search_coverage / limitations；空结果也须如实说明覆盖，不制造旧知识节点 |
| dependency-binding | dependent_ref 是需要该结果的对象，prerequisite_ref 是实际候选上游；两端均须已存在。kind、affected_axes、comparison、proof_plan_ref、reuse_decision_ref 均按业务 schema 填写 |
| frontier-item | 需要长期追踪、且已有足够真实引用的缺口；缺必要引用时只写 open_items，不强造记录 |
| open_items / follow_up_requests | 用共同规范的固定文本顺序说明目标、已查内容、缺失材料和下一步；不填写未来 RecordRef |

`records` 仅允许 baseline-snapshot、dependency-binding、frontier-item，且必须属于本 Task 预声明类型。只有检索建议或诊断时可以 `records=[]`，不能用附件偷偷交付未声明的业务记录。

实际查询时间、来源返回内容、URL、失败和原始字节由 host/检索服务另存执行附件；草稿 schema 不新增 retrieval_success 等字段。不同模型的候选可以不同，但必须能够回溯其输入和实际检索证据。

## 4. 默认工作顺序

1. 明确目标的对象、定义、量词和条件，保留未知范围；不为匹配上游而修改目标。
2. 先查显式提供的精确库条目，再查原文明确引用，最后在任务授权的范围内扩展搜索。参考文献条目和邻近引用只产生线索。
3. 只有书目/链接时，提出取得来源的请求；已有上游源码时，请求 Paper 提取相关内容。host 获得真实输入后才创建正式任务。
4. 上游 MathClaim 已存在后，逐项说明对象/定义/假设/结论的对应与差异。原文位置相似、标题相近或发表更早都不足以建立数学依赖。
5. 有足够依据时提出 candidate binding，再请求 `review.reuse`。尚无用途决定时 reuse_decision_ref 为 null；这不代表获准复用。证明路线未存在时不编造 proof_plan_ref，也不将候选作为已经支持的数学前提。
6. Review 的实际结果保存后，若需把用途决定绑定到依赖，创建新的 Dependency 任务/记录版本；不回写旧候选。

## 5. 调度与停止

- 缺被引论文：建议 Utility 获取；缺 source-request 的真实登记入口时报告该前置缺口，不擅自产出 source-request。
- 缺上游 claim：建议 Paper；不能直接从书目制造 MathClaim。
- 两端具备、用途清楚：建议 `review.reuse`；不能自己产生 relation-assessment 或 reuse-decision。
- 有新前提影响证明：反馈 Proof；有新目标/条件影响范围：反馈 Planner / `review.scope`。
- 父计划限制耗尽、重复节点无新证据、来源不可达或身份不清：保留可恢复缺口。全树去重和预算由 scheduler 负责，子任务不得重新获得无限额度。

原文引用图可能有环；仅所选证明路线的数学推理需满足 DAG 约束。不要把引用、定义依赖、相似关系和已批准证明前提合并成一种边。

## 6. 交付门与当前边界

一次有界检索可以交付“未找到可用前驱”，但必须说明查过哪里，不能推出“没有前驱”或“全球首次”。条件差异未解决时，不满足目标的无条件成功门。

现有[本地交接](../handoff/README.md)只证明某个执行路径曾读到引用；不替代本规范的语义检索、递归获取和用途审阅。后续待测内容只登记在 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 D-* 与 X-* 项，不在本目录另建清单或自动运行案例。
