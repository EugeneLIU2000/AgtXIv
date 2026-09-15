# 一条真实 claim 的交接：Paper → Dependency

## 先看结论

这里实现的是一条**可执行、可保存、可重启的候选交接**，不是完整的论文自动研究系统。

输入来自已有 Paper Agent 案例 `2608.14798v1-claude-opus-5-v1.1` 的 A07 第一个数学结论：

> 对纯态，原文声称：Mα(ψ) = 0 当且仅当 ψ 是稳定子态。

原提取结果没有明确该结论的 α 范围。这一缺口原样保留，不补猜测的范围，不把生成的数学表达认定为正确。

本轮的完整动作是：**选定已有候选 → 固定输入并建工作单 → Dependency 执行本地引用扫描 → 保存检索产物和执行回执 → 新进程读回**。

它使用 `agents.json` 已允许的 HYBRID `dependency.search` 操作，执行者是固定本地程序 `local-citations/1.0`。没有新增模型调用，没有远程检索，也没有重新运行 Paper 提取。

## 1. 实际查到了什么

扫描 claim 及定义关联的两个原文片段，在论文自带 BibTeX 中匹配到：

| 出现位置 | 本地引用键 | 引用书目记载的标题 | 可以说明什么 |
|---|---|---|---|
| SRE 定义 | `Leone/Stab_Renyi/2022` | Stabilizer Rényi Entropy | 定义所在上下文引用了此文，可作为下一步检索线索 |
| SRE 性质段落 | `Leone/Stab_Renyi_monotone/2024` | Stabilizer entropies are monotones for magic-state resource theory | 引用附在单调性叙述上；不能直接认定为本次“为零当且仅当”命题的前驱 |

这些是**引用上下文线索，不是两条已建立的数学依赖边**。没有下载或阅读两篇被引论文，没有确认其具体定理和可复用条件。BibTeX 的作者/标题是引用方提供的元数据，不是已经外部核实的归属。

每条线索保留原文 SourceSpan 精确引用、引用命令字节位置、书目文件哈希、书目条目字节位置、原始条目文本及片段哈希。可以回到原始字节检查它从何而来。

## 2. 这次补齐了哪几个接口

| 边界 | 现在实际做的事 | 明确不做的事 |
|---|---|---|
| 已有 Paper 记录 → 工作单 | 以完整 RecordRef 选目标，解析所需记录闭包；验证源文件和跨度哈希 | 不读 latest、不重写旧输出、不伪造 Paper 成功回执 |
| 工作单 → Dependency | 固定 7 条记录、3 个可见文本附件；用现有 Task 契约校验后调用 handler | 17 个源附件虽由 host 保存验证，但图片及压缩包不传给 handler |
| Dependency → host | 返回现有 `search-draft.schema.json` 格式的提案，以及实际扫描 `findings.json` | 提案不冒充实际远程检索；不凭书目制造上游 MathClaim 或 dependency-binding |
| host → 存储 | 保存 Task、真实 attempt、执行事件、Result、产物原始字节及哈希 | Task/Result 不混入业务 RecordSet，不产生科学认可 |
| 重启 → 接续 | 输入从固定 SQLite 读取；已完成直接读回；中断留失败记录后有界重试 | 不自动改输入版本，不无限递归，不重复消费已完成任务 |

**没有修改业务 schema 或其他正在搭建的 Agent 草案。** 完善点是给现有契约接上真实执行和存储边界，而不是继续增加数学字段。

原来的整篇 Paper 输出仍有 **82 个 SELF_REVIEW 错误**：作者自己制作的对应关系不能充当独立审阅。这里按精确引用自然选出的 7 条候选记录可独立通过结构/引用/字节检查，并不依赖那些对应关系记录；不是删掉失败记录让整篇变绿。`manifest.json` 同时保留整篇检查失败和本次局部检查通过的状态。

因此本任务 `acceptance=DELIVERY`，`depends_on=[]`：输入来自已保存的候选，不声称已有一个成功的 Paper 父任务。`expected_record_types=[]` 是因为本轮明确交付的是检索附件，不是业务记录。产生附件的实际执行才满足这次交付要求。

## 3. 如何自己运行

在仓库根目录，使用已有 `.venv`。初次 `prepare` 需要原 Paper 示例的 `records.json`、`acquisition.json` 和 acquisition 指向的完整源码包；之后 `run` 不再读取这些原始路径。

```bash
.venv/bin/python -B 'schema v0.1/handoff/handoff.py' prepare --run-dir /private/tmp/agtxiv-my-handoff
.venv/bin/python -B 'schema v0.1/handoff/handoff.py' run --run-dir /private/tmp/agtxiv-my-handoff
.venv/bin/python -B 'schema v0.1/handoff/handoff.py' status --run-dir /private/tmp/agtxiv-my-handoff
.venv/bin/python -B 'schema v0.1/handoff/handoff.py' export --run-dir /private/tmp/agtxiv-my-handoff
```

这四次调用是独立进程。再执行 `run` 会返回同一个 attempt 的已保存结果，不再次扫描。换另一条已有 claim 时，`prepare --example <原输出目录> --target-ref <完整RecordRef.json> --run-dir <新的目录>`；不会凭论文号或模糊文本自动挑选目标。

`prepare` 固定代码、业务 bundle 及相关接口文件的哈希。实现或接口变化后拒绝在旧 run 上继续，需建立新 run；旧结果可以保留，但不能冒充新版本执行。

`export` 只导出当前已结束尝试的结果，文件与已保存字节不同就拒绝覆盖。准备阶段不导出；若先导出了失败尝试后又重试，原导出保留，需另行归档/使用新 run，不能把新结果覆盖进旧导出。

## 4. 保存在哪里

本轮保留案例见 [example/2608.14798v1-A07](example/2608.14798v1-A07/README.md)。运行目录内容：

- `handoff.sqlite`：独立的本地候选与运行数据库，包含全部 17 个原附件。业务记录复用 `LocalStore`，运行事件复用已有 `storage/runtime.sql`。
- `task.json`：固定工作单。
- `manifest.json`：实现版本、输入身份、检查范围及旧案例未通过的事项。
- `search-draft.json`：符合 Dependency 草案契约的下一步检索建议。
- `findings.json`：实际本地扫描的线索、精确位置及未改变的目标内容。
- `result.json`、`status.json`：运行回执和事件顺序。身份是本地服务自报 `DECLARED`，不是独立认证。

产物和结束事件在同一 SQLite 事务里写入；失败回滚不留下孤立的“成功”附件。初次准备在临时库完成后再发布完整数据库。这里没有接入主业务库迁移、通用事务 outbox、Git 封存或 Neo4j 投影，也没有执行 Git commit/push。

## 5. 执行限制和测试

这不是完整 TeX/BibTeX 解释器：只扫描固定原文字节跨度中的常见字面 `cite` 命令，以及大括号包围的书目条目；不展开宏、不执行 TeX。未匹配、重复书目键、未检索范围都会保留为缺口。邻近段落引用不被提升为目标级数学依赖。

本地扫描限制：最多 256 个跨度、256 个引用、10 MiB 可见文本；单书目条目最多 128 KiB、单文件最多 10,000 个书目条目。任务最多 2 次尝试；30 秒是完成后核对的协作式耗时预算，**不是强制杀进程的沙箱**。成本单位定义为付费外部 API 调用次数，本轮是 0，不代表本地计算无成本。

单机 host 锁防止合作 worker 同时领取；中断尝试计入预算。恢复回执的结束时间是 host 发现中断的时间，真实进程何时退出未知。这里只针对进程重启做恢复；不宣称管理员隔离、分布式租约/代次隔离、断电可靠性或任意程序的资源隔离。host 和本地文件系统是信任边界。

```bash
.venv/bin/python -B -m unittest discover -s 'schema v0.1/handoff/tests' -v
```

测试使用真实保留输入作为正例，在临时目录中注入错误。覆盖精确引用、缺闭包、坏字节、不可见目标、字段漂移、输入可见范围、handler 修改输入、重复运行、进程中断、有限重试、原子提交、准备失败、只读回放和导出冲突等。

## 6. 下一步只推进哪一件事

优先把 **2022 年书目线索 → 获取原论文固定字节 → Paper 提取具体上游 claim → Review 比较定义、α 范围和用途** 接起来。确认适用条件后才保存数学依赖，再决定是否值得形式化。

Proof 分支当前还缺真实的独立范围审阅与 `FrozenScope`；不能为了演示而手填通过记录。Lamport → Lean 4、可信上游代码复用和全树预算的递归调度，均不属于这次已运行的闭环。
