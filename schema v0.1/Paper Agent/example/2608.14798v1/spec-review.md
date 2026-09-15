# AGENT.md 执行前检查

检查对象：`../../AGENT.md` 的 agent-spec-version 1.0；输入文件没有被修改。实际字节指纹记录于输出 manifest。

结论：可以进行真实取源、分段阅读和候选提取，但不能声称严格完成 S0–S5。本文不代替用户批准接口迁移。

## 阻止严格执行的冲突

| 位置 | 冲突 | 本次处置 |
|---|---|---|
| 第 3 节，原文件第 28 行 | “12 fields”列出 7 个 envelope 项、7 个 payload 项，还另保留 input_refs，计数规则不明确 | 不将此计数当作可执行 schema |
| 同上 | 删除 created_at、data_class、schema_bundle_hash、max_seconds、max_cost_units 和 Producer 中若干字段，但现有 v0.0 schema 仍要求它们 | 保留一份明确标为兼容性试样的完整旧格式 Plan；另输出精简 Plan 的失败校验。不悄悄修改规范或旧 schema |
| 第 3 节 source_unit_ids | 文件称可以是 snapshot 单元的子集；现有 RecordSet 校验要求计划涵盖整个 supplied source inventory | 本次全部 16 个来源文件留在候选清单中；未检查图像等仍明确开放 |
| S0 | Coordinator “signs”没有当前可用的签名机制和授权政策 | 不生成签名、不声称受信任执行；本地候选政策为 PROPOSED，无准入权限 |
| S2/S3 | S2 在 Claims 前冻结，但当前 discovery 已可引用 claims；S3 又要求每个 obligation 都有 ScientificClaim。然而来源缺失、图像阅读等义务不等于作者主张 | 不为凑分母制造 claim；只生成未冻结的候选发现记录 |
| S4 / 第 6 节 | 要求始终创建 Proof 与 Dependency 两个任务，且绑定同一 MathClaim/FrozenScope；同时允许冻结前检索，也允许非数学主张没有 MathClaim | 只保存带真实已存在引用的后续请求，不伪造 frozen-scope 或正式配对 Tasks |
| S5 | 严格清单需已冻结义务与正式回执，而本次 S0/S2 未完成 | 本次 manifest 是候选产物与开放义务清单，不是正式 release-manifest 或通过审计的论文产物 |
| 第 4 节与现有 RecordSet | Paper 可以输出 claim-component-map，但其中的 review 即使写 UNESTABLISHED，校验器也对同一生产者触发 SELF_REVIEW | 实际完整包保留 33 个拒绝，不伪造另一个审阅者。去掉这些 map 的诊断子集通过，但不能充当完整输出 |

Dependency 输入白名单已经允许 frozen-scope，不把它误报为缺少白名单。

## 本次执行方式

1. 实际下载 `https://arxiv.org/src/2608.14798v1`，保存压缩包、解压文件及逐文件指纹。
2. 主执行者阅读前部正文，两个分段 agent 分别阅读系综部分、稳定子功与应用及附录部分，形成 3 份候选种子文件。
3. 固定程序将候选装配为现有 v0.0 记录，并校验 JSON、精确引用及源文字节。程序不会调用模型，不把重放当作重新阅读。
4. 另一个 agent 独立检查接口冲突和面向读者的状态表述。这不是对数学内容的正式独立审阅，也不签发冻结范围。

候选输出在 S2 阻塞后作为旁路研究材料保留；它不代表按新 AGENT.md 顺序完成了 S3。原文件本身允许保存候选、不得以假记录满足交付。

## 建议的最小修订（尚未实施）

- 明确精简 Plan 是新版本协议，还是现有协议的阅读摘要；前者需要迁移 JSON schema 和消费者。
- 把“每个义务至少一条 claim”改成“每个义务都有处置；真正发现主张时才生成 claim”。
- 同版本规则只约束冻结后、面向同一数学目标的配对交接；预检索和非数学残余项单独调度。
- 将“签名”区分为普通执行归属记录、独立审阅和真正的认证签名。

这里不把格式校验、结构审阅、原文忠实性、数学正确性混为一个通过状态。
