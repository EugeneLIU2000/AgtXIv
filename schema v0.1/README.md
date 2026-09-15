# Schema v0.1：多 agent 协作与底层系统契约

状态：**实验设计与可运行的离线契约检查**。版本 `0.1.0`。日期：2026-09-12。

这次新增的是“怎样把工作交给不同 agent，并可靠地交接和保存”，不是重写数学知识的格式，也不是宣布多 agent 生产系统已经运行。

最简单的理解：**论文和 claim 是长期保存的档案；agent 是临时接工作单的研究助理；调度器负责派单；存储程序负责记账。** 换模型、结束一个 agent 或重启进程，都不应丢失研究进度。

## 先读什么

| 你关心的问题 | 入口 |
|---|---|
| 需要哪些 agent？分别做什么、不能做什么？ | [AGENT-CONTRACTS.md](AGENT-CONTRACTS.md) |
| 谁先工作？什么时候并行、等待、重试和停止？ | [SCHEDULING.md](SCHEDULING.md) |
| SQL、Neo4j、GitHub 各保存什么？怎样封存和恢复？ | [STORAGE.md](STORAGE.md) |
| 已有 64 类 schema 是否要重做？ | [COMPATIBILITY.md](COMPATIBILITY.md) |
| 现在交付了什么，下一步具体实现什么？ | [IMPLEMENTATION.md](IMPLEMENTATION.md) |
| 哪些检查真的运行过，哪些尚未执行？ | [VALIDATION.md](VALIDATION.md) |
| 数学目标怎样拆成 Lamport 证明，再交给 Lean 4？ | [Autoformalization Agent/AGENT.md](<Autoformalization Agent/AGENT.md>) |

## 本包的三个边界

1. **业务记录继续用 `../schema v0.0/`。** 原文主张、数学命题、推理步骤、检查记录等不改名、不复制、不降级。新目录只增加工作模板、任务交接和候选导出清单；不是把旧记录的版本号替换成 0.1.0。
2. **任务交付不等于科学成立。** 一次工作可以正确地交付“无法证明，缺少引理 L”。生成、格式合规、实际机器检查、含义对齐和正式准入仍分别记账。
3. **规划完成不等于服务上线。** 离线检查器能核对字段、角色输出范围、任务依赖、回执绑定和候选导出字节；它不启动模型、搜索论文、运行 Lean、调用 Docker、提交 Git 或批准科学结论。

## 最小组成

- `agents.json`：可调用工作模板及操作目录。Paper、Proof、Dependency、Formalization、Review 是核心；Delta、Reader、Planner 按需调用；Utility 执行固定程序。
- `schemas/`：五个 JSON Schema 文件，分别定义共享类型、模板目录、任务、结果和候选导出清单。
- `compatibility.lock.json`：固定当前 v0.0 契约包身份；不能静默读取另一套“最新版”。
- `examples/`：明确标记为人工教学样例的工作单、回执和文件导出；不是论文验证证据。
- `storage/`：SQL 运行表和 Neo4j/Docker 参考材料。是待接入的参考，不自动修改当前数据库。
- `validate.py`、`tests/`：离线格式与跨对象约束检查及反例测试。

## 最小调用接口

`run(task) → result`

工作单指定目标的精确记录版本、操作、预期交付、允许工具、依赖和预算。结果交代产物、缺口、后续建议和实际运行信息。平台提供真实执行归属；agent 不自行签发可信凭据。

业务产物通过原 v0.0 格式装配、校验和保存。工作单与执行回执属于新的运行层，**不能直接塞入 v0.0 的 `RecordSet` 或 `LocalStore.records`**。存储适配见 STORAGE。

## 在仓库根目录检查

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

交付标准是：工作分工和调度规则可供实现；存储权责、格式、失败恢复有明确决定；接口有可执行的正反例检查；读者能够看出哪些还未实现。生产队列、真正的多模型调用、远程获取、独立 Lean 检查和正式准入不属于本轮已经实现的能力，后续工作列在 IMPLEMENTATION 中。
