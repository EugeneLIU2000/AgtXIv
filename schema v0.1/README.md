# Schema v0.1：多 agent 协作与底层系统契约

状态：**实验设计与可运行的离线契约检查**。版本 `0.1.0`。日期：2026-09-12。

这次新增的是“怎样把工作交给不同 agent，并可靠地交接和保存”，不是重写数学知识的格式，也不是宣布多 agent 生产系统已经运行。

最简单的理解：**论文和 claim 是长期保存的档案；agent 是临时接工作单的研究助理；调度器负责派单；存储程序负责记账。** 换模型、结束一个 agent 或重启进程，都不应丢失研究进度。

当前开发约定（2026-09-15）：先完善 Agent 框架，**不自动执行测试**。所有新增/受影响的待测试项及接口前置缺口统一放在 [PENDING_TESTS.md](PENDING_TESTS.md)，供用户检查；后续明确要求时才执行指定范围。历史报告不代表本次修改已验证。

## 先读什么

| 你关心的问题 | 入口 |
|---|---|
| 需要哪些 agent？分别做什么、不能做什么？ | [AGENT-CONTRACTS.md](AGENT-CONTRACTS.md) |
| 谁先工作？什么时候并行、等待、重试和停止？ | [SCHEDULING.md](SCHEDULING.md) |
| SQL、Neo4j、GitHub 各保存什么？怎样封存和恢复？ | [STORAGE.md](STORAGE.md) |
| 底层架构现在最该补什么，为什么保留 Neo4j？ | [SYSTEM-REVIEW.md](SYSTEM-REVIEW.md)（先读结论） |
| 图查询具体接收/返回什么，怎样交给下一 Agent？ | [GRAPH-INTERFACE.md](GRAPH-INTERFACE.md) |
| 已有 64 类 schema 是否要重做？ | [COMPATIBILITY.md](COMPATIBILITY.md) |
| 现在交付了什么，下一步具体实现什么？ | [IMPLEMENTATION.md](IMPLEMENTATION.md) |
| 宿主如何用固定程序调度、用 Pydantic AI 调用模型？ | [宿主参考版](host_reference/README.md)（控制流与端口；未运行） |
| 以前运行过哪些检查？ | [VALIDATION.md](VALIDATION.md)（历史范围） |
| 当前还有什么需要我检查、以后再测试？ | [PENDING_TESTS.md](PENDING_TESTS.md)（唯一待测入口） |
| 数学目标怎样拆成 Lamport 证明，再交给 Lean 4？ | [Autoformalization Agent/AGENT.md](<Autoformalization Agent/AGENT.md>) |
| 一条真实 claim 能否实际交接、保存并重启接续？ | [Paper → Dependency 本地交接](handoff/README.md) |

2026-09-15 增补：`handoff/` 已实现一条从已有 Paper 候选到 Dependency 本地引用扫描的有界执行路径。它不调用新模型、不远程检索、不建立已认可的数学依赖；本包其余调度/存储规划不能因此视为已经实现。

2026-09-15 底层审阅修订：图服务被定位为 host 的可替换查询模块，不新增 Agent。新增 [graph-contract.schema.json](storage/graph-contract.schema.json)，规范投影请求、三类有界查询和带来源的结果；本地验证批次可分别进入图投影和 Git 归档，不再把 Git push 当成本地研究前置。**新图 schema 尚未接入检查器，旧 SQL/Cypher 仍是归档优先参考；未部署图服务或迁移。**

同日后续进展：复核已有执行日志，统一 runner 的 21 步均符合预期退出码；这不代表科学验证或新宿主已通过。新增 `host_reference/` 的确定性控制流与 Pydantic AI 调用适配，实际运行库、身份/证据门及固定程序端口尚未接通；本轮没有运行新测试。当前证据与待测范围见 [PENDING_TESTS §8–9](PENDING_TESTS.md)。

## 其他六个 Agent：从哪里开始读

先前规范轮补齐以下六个 `AGENT.md`，按职责、输入、输出、工作顺序、停止与交接组织。后续图接口和宿主参考版继续沿用它们的业务草稿格式，不重写科学含义；其他轮次的历史执行记录见中央清单。

| 入口 | 只负责什么 |
|---|---|
| [Dependency Agent](<Dependency Agent/AGENT.md>) | 找真实上游候选及证据，不批准复用 |
| [Review Agent](<Review Agent/AGENT.md>) | 分角色独立审阅范围、推理、用途与对齐，不改被审对象 |
| [Utility Agent](<Utility Agent/AGENT.md>) | 执行固定程序并保存真实回执，不作科学选择 |
| [Planner Agent](<Planner Agent/AGENT.md>) | 提议有前置条件的下一步，不直接派单 |
| [Delta Agent](<Delta Agent/AGENT.md>) | 相对固定基准比较改变，不宣称全球首次 |
| [Reader Agent](<Reader Agent/AGENT.md>) | 解释当前结果、依据与缺口，不授予科学认可 |

建议先读 Dependency → Review → Utility，理解主链；再读 Planner 如何提议顺序，以及 Delta / Reader 如何消费已有结果。共同草稿约束在 [AGENT-CONTRACTS §2.2](AGENT-CONTRACTS.md)，具体交接条件在 [SCHEDULING §3.1](SCHEDULING.md)。

## 本包的三个边界

1. **业务记录继续用 `../schema v0.0/`。** 原文主张、数学命题、推理步骤、检查记录等不改名、不复制、不降级。新目录只增加工作模板、任务交接和候选导出清单；不是把旧记录的版本号替换成 0.1.0。
2. **任务交付不等于科学成立。** 一次工作可以正确地交付“无法证明，缺少引理 L”。生成、格式合规、实际机器检查、含义对齐和正式准入仍分别记账。
3. **规划完成不等于服务上线。** 离线检查器能核对字段、角色输出范围、任务依赖、回执绑定和候选导出字节；它不启动模型、搜索论文、运行 Lean、调用 Docker、提交 Git 或批准科学结论。

## 最小组成

- `agents.json`：可调用工作模板及操作目录。Paper、Proof、Dependency、Formalization、Review 是核心；Delta、Reader、Planner 按需调用；Utility 执行固定程序。
- `schemas/`：五个 JSON Schema 文件，分别定义共享类型、模板目录、任务、结果和候选导出清单。
- `compatibility.lock.json`：固定当前 v0.0 契约包身份；不能静默读取另一套“最新版”。
- `examples/`：明确标记为人工教学样例的工作单、回执和文件导出；不是论文验证证据。
- `storage/`：SQL 运行表和 Neo4j/Docker 参考材料，以及独立的 graph-service/1.0 消息 schema；图 schema 尚未注册到根检查器，不自动修改当前数据库。旧 SQL/Cypher 不直接支持新本地封存 profile。
- `validate.py`、`tests/`：离线格式与跨对象约束检查及反例测试。
- `host_reference/`：固定程序宿主与 Pydantic AI 模型适配的未执行参考；强制后端端口仍需实现，不是已部署服务。

## 最小调用接口

`run(task) → result`

工作单指定目标的精确记录版本、操作、预期交付、允许工具、依赖和预算。结果交代产物、缺口、后续建议和实际运行信息。平台提供真实执行归属；agent 不自行签发可信凭据。

业务产物通过原 v0.0 格式装配、校验和保存。工作单与执行回执属于新的运行层，**不能直接塞入 v0.0 的 `RecordSet` 或 `LocalStore.records`**。存储适配见 STORAGE。

## 按需检查（仅在用户明确要求执行时）

```bash
.venv/bin/python 'schema v0.1/validate.py' --check
.venv/bin/python -m unittest discover -s 'schema v0.1/tests' -v
```

检查自己的交接单：

```bash
.venv/bin/python 'schema v0.1/validate.py' --task /absolute/task.json
.venv/bin/python 'schema v0.1/validate.py' --task /absolute/task.json --result /absolute/result.json
.venv/bin/python 'schema v0.1/validate.py' --archive /absolute/batch/batch.json
```

URI 只作 schema 身份，所有引用在本地解析，缺失即失败，绝不联网下载。单份输入文件最多 64 MiB；导出成员合计最多 256 MiB；这里只是有界本地参考，不是海量系统容量承诺。

任务与结果检查**不解析所引用业务记录的真实字节，不验证执行真实性或科学成功门**。候选导出检查会另行读取所列业务记录和附件，使用 v0.0 检查器检查该批次内的完整引用集合；仍不认证身份或科学真伪。每次输出均报告这些边界。

## 本轮完成边界

交付标准是：工作分工和调度规则可供实现；存储权责、格式、失败恢复有明确决定；读者能够区分接口、实现与实际运行证据。原有根契约具备离线检查入口；新增图接口只有规范与机器 schema，尚无语义检查器或运行适配。生产队列、真正的多模型调用、通用远程获取、独立 Lean 检查和正式准入不能由这些文件推定完成，后续工作列在 IMPLEMENTATION 中。
