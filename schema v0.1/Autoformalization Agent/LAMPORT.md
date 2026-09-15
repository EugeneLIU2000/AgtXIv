# 接口 A：MathClaim → Lamport 结构化证明

本文件是规范性附件。“Lamport”指可读的命名、层级化证明风格，不表示本项目实现了 TLA+ 或 TLAPS 解析器。数学事实仍保存在原业务记录中，阅读层只提供定位。

## 1. 输入和输出

操作保持 `proof.expand`。最低输入是 MathClaim 和 frozen-scope；原文证明、实际使用的 Definition、SourceSpan、依赖与旧异议必须可解析并属于本轮输入。

输出草稿使用 proof-draft.schema.json；payload 逐类引用旧业务 schema，不能新增自拟 `LamportStep` 业务类型。允许类型来自 agents.json 的 Proof 白名单，本轮实际交付类型由 Task 预先声明。

核心产物只有五类：

| 类型 | 在证明中表达什么 | 关键字段 |
|---|---|---|
| `argument-node` | 一个明确陈述：前提、中间引理或结论 | statement、kind、origin、claim_refs、context_ref、definition_refs、source_span_refs |
| `assumption-context` | 一组局部假设的作用范围 | parent_ref、assumptions、introduction_reason、allowed_use |
| `inference-step` | 一次由全部前提共同推出结论的推理 | premise_refs、conclusion_ref、rule、justification、context_ref、discharged_context_refs、rule_evidence_refs |
| `proof-plan` | 选定的一条证明路线及未完成义务 | scope_ref、conclusion_ref、route、node_refs、inference_refs、required_obligation_ids、open_obligation_ids |
| `argument-snapshot` | 本轮供审阅的完整论证清单 | 目标、节点、推理、局部范围、路线、依赖、全部异议与 missing_items |

这是字段导读，不替代各 JSON Schema。一个步骤的引理若尚未取得，写缺口与后续请求；不得造 prerequisite_ref 或依赖批准。局部新假设不能回写 Paper 的 MathClaim.assumptions。

## 2. 一步证明至少说明六件事

1. 当前目标是什么，对应哪个精确节点和数学目标。
2. 分开说明原命题的适用条件、当前范围内的局部假设，以及可以使用的外部结果。
3. 本步实际用了哪些依据；它们合起来支持结论，全部列入同一个 premise_refs，不能拆成各自独立的蕴含。可使用的依据不等于本步实际用过的依据。
4. 用哪种规则，公开的数学理由是什么；规则适用条件在哪里说明或仍欠缺。
5. 是否引入或解除局部假设，解除后结论在什么范围成立。
6. 此内容来自原文、根据原文重建、修复还是替代路线；源文内容直接关联原文位置。

终止细化的条件：当前步骤的目标、共同前提与理由足够明确，能够交给下一层检查或标为明确缺口。不设“每个证明必须 N 步”；不能以“模型相信正确”作为叶节点已证明的依据。

## 3. Lamport 阅读动作怎样落到既有记录

| 阅读动作 | 记录方式 | 必须避免 |
|---|---|---|
| ASSUME / PROVE | 用 context 表示局部前提，node 表示要证结论；外层返回通过显式解除假设的 inference 表示 | 把局部前提自动加入最终定理，或伪造空 context |
| 断言与 BY 引用 | node 保存陈述，inference 保存所用节点、规则与理由 | 只写步骤号、不列实际前提 |
| SUFFICES：转成足够条件 | 分别保存新子目标及其足以推出旧目标的理由；最终仍回到旧目标 | 只改当前目标而漏掉“新目标 ⇒ 原目标”的桥梁 |
| PICK：取存在见证 | 先有存在性依据，再在局部范围使用该见证，说明新变量边界 | 无存在性依据凭空选对象，或把局部见证带出范围 |
| CASE / 归纳 | 使用 CASE_SPLIT／INDUCTION，保留穷尽性、基例、归纳步和适用条件证据 | 把情况标题当成已覆盖全部情况 |
| QED | 结束条目引用当前层原目标，以及真正推出它的推理 | 最后只证明了一个子结论，就宣称原目标完成 |

普通合取拆分／组合可用 `DIRECT`，具体规则写在 justification；不得往旧 rule 枚举添加 AND_INTRO 等新值。存在量词的变量限制、SUFFICES 桥梁及归纳正确性需要论证审阅与形式检查，现有字符串字段和 JSON 检查器不能完整决定它们。

context 的 parent_ref 只表示假设范围嵌套，不是数学推导关系。没有新增假设时沿用已有 context_ref，最外层可为 null；assumption-context 的 assumptions 非空，不能为凑树形结构创造空假设记录。

解除假设时使用允许的 rule、明确 discharged_context_refs 和 rule_evidence_refs，并返回该 context 的直接父范围。只填这些字段并不证明解除在数学上合法；规则证据不能循环引用结论本身。

## 4. 原文归属与证明缺口

- node.origin：SOURCE 需要直接 SourceSpan；RECONSTRUCTED 是把原文省略内容展开，不等于作者原句；REPAIRED／ALTERNATIVE 明示改造；IMPORTED 指来自外部来源的已定位内容，不等于获准复用。
- proof-plan.route 区分 ORIGINAL、RECONSTRUCTED、REPAIRED、ALTERNATIVE。若同一路线含实质修复，不得整体标 ORIGINAL。
- 原文缺证明时可以构造新路线，但必须保留来源缺失、重建归属和待审状态。研究者更换证明方法，不改变作者目标时，也不能把新方法归给作者。
- 已有冻结义务的未解项放 open_obligation_ids；新发现而未纳入范围的事项放 missing_items／frontier／follow_up_requests，申请范围修订，不编造一个已冻结 obligation ID。
- 多条替代证明分别保存，不能把甲路线前半和乙路线后半拼成没有论证的通过路径；旧失败路线和异议继续保留。

## 5. 阅读视图不是第二套证明

lamport-view.schema.json 引用一个 argument-snapshot 和其中选定的 proof-plan；entries 保存 label、parent_label、role、node_ref、inference_ref。显示时按数字路径排序（1.9 在 1.10 前）；数组的物理顺序不赋予证明意义。

- label 采用 `1`、`1.1`、`1.2`；这是定位，不是数学依赖。标签不含前导零。parent_label 必须是其数字路径的直接父级。
- 一个视图只有一个根 GOAL；有子条目的 GOAL 必须以 QED 子条目结束，QED 的 node_ref 与该层 GOAL 相同。STEP/QED 不挂子条目。
- STEP 的内容和依据从 node／inference 读取；GOAL 展示待证明的节点，并不提前把它加入可用前提。一个节点可以作为目标和对应 QED 的显示对象，不能因此变成自己的推理前提。
- GOAL 标题或明确的假设引入可以没有 inference_ref，这本身不是证明缺口。若某个需要论证的 STEP／QED 没有推理，则必须能在快照缺口中定位未完成事项；不得把 null 的 QED 显示为已完成。
- 宿主必须检查节点与推理确实属于所选路线、推理结论与显示节点对应、根目标与 proof-plan.conclusion_ref 相同。当前草稿检查器不解析这份记录集合；业务引用闭包由 RecordSet 检查，阅读视图与业务记录的对应检查仍须另行实现。
- 人类可读的 lamport.md 必须从同一批精确记录生成，或作为有对应关系的附件校对。Markdown 排版通过不是证明通过。

## 6. 保存与后续调用

记录引用形成实际依赖时分轮登记：context／node 保存后才能引用它们创建 inference；inference 保存后才能创建 plan／snapshot；存储顺序不能靠未来哈希补齐。每轮使用新的固定 Task，保留真实可见输入与预算消耗。

Proof 只提出 review.argument、review.alignment 或 dependency.search 的请求。独立审阅后，由 utility.assemble-packet 固定 MathClaim、所选路线、论证快照和环境，交给 Lean 阶段；不直接把一篇 Markdown 当作充分的形式交接包。

参考：Lamport 的 [How to Write a 21st Century Proof](https://lamport.azurewebsites.net/pubs/proof.pdf)，尤其结构化步骤与局部假设部分。本项目的 JSON 记录、命名规则及门控是本地工程约定，不是该论文规定的接口。
