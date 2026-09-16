# 运行接口与交付约定

本文件是 [AGENT.md](AGENT.md) 的规范性附件，规定 `planner.propose` 的输入边界、草稿形状、宿主与模型的分工、分轮引用与每轮文件约定。判定顺序与编号正反例见 [CONFORMANCE.md](CONFORMANCE.md)，真实执行记录与未实现清单见 [validation-report.json](validation-report.json)。共享不变量 I1–I6 见 [Autoformalization Agent/AGENT.md](<../Autoformalization Agent/AGENT.md>) 第 1 节，交接字段、独立性与交付语义见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md)，本文件不重述这两处的条文。

## 1. 本模块的操作

| 操作 | 最小输入 | 输出草稿 | 明确不负责 |
|---|---|---|---|
| `planner.propose` | 非空 brief，记录本轮真实用户目标、优先级与约束；已有来源／计划／范围／处置以精确 `input_refs` 提供，实际目标取其精确子集 `target_refs`；其他材料固定在 `input_artifacts`。尚无业务记录时 `input_refs`／`target_refs` 可为空 | [propose-draft.schema.json](propose-draft.schema.json)（`records` 恒为空数组） | 创建、排期或执行 Task；产出 `agentization-plan` 或任何业务记录；授予 capabilities、移除 exclusions、提高预算、关闭 EVIDENCE 门；判定科学结论是否成立 |

- 类型白名单、capabilities 与 principles 以 [agents.json](../agents.json) 为准。实测：`planner.propose` 的 `input_record_types` 是 64 个业务短名的**全集**，`output_record_types` 为 `[]`，capabilities 上限为 `records.read`、`planner.propose` 两项。白名单表示"可接受类型"，不表示每类都必填，也不表示已获得读取这些记录内容的许可。
- 空的 `output_record_types` 是接口事实，不是尚未决定：`Task.expected_record_types` 与 `Result.output_refs` 必须为空，本模块的交付物是建议与附件。
- 三类通用上下文（`authority-policy`、`processing-profile`、`agentization-plan`）与 `review.backtranslate` 的输入隔离特例由 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2 规定。[check_interfaces.py](check_interfaces.py) 对每一条 proposal 与 follow_up_request 按**被建议的那个 operation** 重算允许输入族，含该特例。
- 计划的正式登记由 `utility.register-plan` 承担，它是 `agentization-plan` 在 agents.json 中的唯一生产者。Planner 可以建议调用它，不代写它的业务 payload。

## 2. 模型返回形状

一次调用只返回一个原始 JSON 对象：不加 Markdown 代码围栏、不加额外顶层字段、不改字段名。空列表写 `[]`；`records` 的空不表示"这次没找到记录"，而表示本操作没有业务输出通道。

```json
{
  "draft_version": "1.0",
  "proposals": [],
  "records": [],
  "open_items": [],
  "follow_up_requests": []
}
```

| 草稿 | schema | 谁生成 | 要点 |
|---|---|---|---|
| 任务建议草稿 | [propose-draft.schema.json](propose-draft.schema.json) | `planner.propose` | 五个根字段全部必填；`additionalProperties: false`；`proposals` 与 `follow_up_requests` 上限各 1000 项 |

逐字段规则：

| 字段 | 形状 | 填写规则 | 不表示什么 |
|---|---|---|---|
| `draft_version` | `const "1.0"` | 与 AGENT.md 的 `draft-version` 行逐字相同 | 不是 `agent-spec-version` 的别名 |
| `proposals[]` | 五项必填 `agent`、`operation`、`input_refs`、`reason`、`blocked_on`；对象封闭 | `agent`+`operation` 必须是 agents.json 中的实际配对；`input_refs` 只列本轮已提供的精确引用，且属于被建议 operation 的允许输入族 | 不是 Task，不是排期，不是已获批准的工作 |
| `reason` | 单个字符串，1–8192 字符 | 固定顺序 `target=...; need=...; purpose=...`，写明目标、要消除的具体缺口、用途 | 格式正确不表示理由成立；检查器只比对文本顺序 |
| `blocked_on` | 字符串数组，唯一 | 固定顺序 `target=...; missing=...; checked=...; next=...`；`checked` 只列实际已读或已执行的事项 | 空数组不表示宿主可以跳过输入、预算与门槛核对（[SCHEDULING.md](../SCHEDULING.md) §3.3） |
| `records` | `{"type":"array","maxItems":0,"items":false}` | 恒为 `[]` | 不是"本轮无记录可交"，是本操作永远无业务输出 |
| `open_items` | 字符串数组，唯一 | 与 `blocked_on` 同一固定顺序，用于不挂在单条建议上的缺口 | 不是待办清单，也不是免责声明 |
| `follow_up_requests[]` | `FollowUp` 四字段 `agent`、`operation`、`input_refs`、`reason`；无 `blocked_on` | 必须是 `proposals` 中**已无已知前置缺口**那部分的子集；同一 `agent`／`operation`／`input_refs` 集合不重复登记 | 不是已派任务，不携带未来 task_id、预算或权限 |

草稿中**没有** `capabilities`、`exclusions`、`limits`、`acceptance`、`expected_record_types`、`priority`、`depends_on` 这些键。提权与排期不是被禁止的写法，而是**无处可写**：对象封闭，写了就是 schema 失败。同一请求改写成 `reason`／`blocked_on`／`open_items` 里的散文时，schema 与检查器都不会拦截（见 [CONFORMANCE.md](CONFORMANCE.md) E08），宿主也不从建议文本提取提权命令。

字段级必填、引用形状与错误码以 [propose-draft.schema.json](propose-draft.schema.json) 和 [check_interfaces.py](check_interfaces.py) 为最终裁决。草稿通过检查不等于建议值得做，也不等于宿主会接受它。

## 3. 宿主与模型各写什么

| 内容 | 所有者 | 约束 |
|---|---|---|
| 建议做什么工作、为什么、缺什么 | 模型 | 只能使用本轮 Task 提供的记录与字节；理由与缺口采用上表的固定文本顺序 |
| 编号、修订、时间、哈希、`producer`、`policy_ref`、业务 `input_refs`、`content_hash` | 宿主 | 本模块不产业务记录，本行对 planner 的唯一落点是：草稿里的每个 RecordRef 必须指向真实已登记记录，且是本轮可见输入（见 I2） |
| Task 的全部字段：`limits`、`capabilities`、`exclusions`、`acceptance`、`depends_on`、`expected_record_types`、`brief` | 宿主 scheduler | 建议不含这些键；scheduler 核对实际类型、预算、能力、回避与前置门后才固定 Task |
| 预算预留、成本、尝试次数、时间与无进展计数 | 宿主 | 子任务消耗父计划的预留额度（[SCHEDULING.md](../SCHEDULING.md) §5 第 5 条）；**提出子任务不产生新额度**。检查器看不到父计划剩余额度，无法区分有界分解与耗尽全树预算的分解（报告键 `budget_and_no_progress`） |
| 派单去重键（真实 brief、用途、路线、政策、权限与回避名单） | 宿主 | 检查器只按 `agent`+`operation`+`input_refs` 集合判重；这比宿主的去重键粗，不能当作安全去重（[PENDING_TESTS.md](../PENDING_TESTS.md) G-05） |
| 运行事实、Result 与 outcome | 宿主 | 草稿无执行回执字段，也不得编造 `work-attempt` 或其他运行记录（见 I2） |
| 计划的正式登记 | `utility.register-plan` | Planner 建议调用它，不代写 `agentization-plan` 的 payload |
| 审阅、范围冻结、批准与 EVIDENCE 放行 | 各自独立操作 | 见 I1 与 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §6；Planner 不因为"看见了输入"而取得这些判断权 |

## 4. 分轮登记与引用

- 建议中出现的每个 RecordRef 必须是 `Task.input_refs` 的精确成员。给了 `--task` 时由 `INVISIBLE_REF` 强制；没给 Task 时这一层在报告的 `unchecked.task` 中明确记为未检查，**不是默认通过**。
- 不得引用未来身份。需要先有 A 才能建议引用 A 的 B 时，本轮只描述所需内容并写 `blocked_on`；A 被真实保存后，由宿主以真实引用新建下一轮 Task。`depends_on` 不能自动替换未来输出。
- 同一份草稿里，`agent`+`operation`+`input_refs` 集合相同的建议只能出现一次（`DUPLICATE_PROPOSAL`）。用途或路线不同但输入相同时，当前草稿**没有字段**可以区分，必须写 `blocked_on` 请求拆清，不能靠 `reason` 文本让宿主去猜。
- `blocked_on` 非空的建议不得进入 `follow_up_requests`；`follow_up_requests` 的每一项也必须在 `proposals` 中出现，因为 `proposals` 是宿主审阅的完整附件。
- 每轮使用新的固定 Task，不回写旧任务。只有真实的新记录、新来源、新预算或用户目标变化才触发重规划；无进展时不自派 `planner.propose`（`SELF_REDISPATCH`）。
- 图检索只能作为建议提出，实际检索与回源核验由宿主在任务之间完成，见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2.3 与 [GRAPH-INTERFACE.md](../GRAPH-INTERFACE.md)。

## 5. 每轮文件约定

运行附件统一使用下表名称，所有路径相对于独立的运行目录。这些是附件，不新增业务类型。

| 路径 | 内容 |
|---|---|
| `task.json` | 当轮实际固定工作单；仅在确实存在时保存 |
| `draft.json` | 本轮原始模型 JSON；无效原始输出另存 `diagnostics/` |
| `records.json` | 本模块恒为空数组；本操作没有业务输出通道 |
| `result.json` | 真实执行产生的 Result；没有足够运行事实时不造回执 |
| `validation.json` | 分层检查报告：草稿、建议配对与输入族、Task 限制、引用可见性分别报告 |
| `manifest.json` | 宿主运行索引；固定字段见下 |
| `diagnostics/` | 被拒草稿、校验错误与待迁移问题；不是正式交付的替代通道 |

`manifest.json` 固定字段：`manifest_version`（`planner-agent/1.0`）、`run_id`、`mode`（`EXECUTED` 或 `OFFLINE_DIAGNOSTIC`）、`source_refs`、`spec_files`、`schema_bundle_hash`、`model`、`files`、`record_counts`。`spec_files` 与 `files` 写 `{path, sha256}`（`files` 另含 `byte_size`），哈希为 `sha256:` 加 64 位小写十六进制；`model` 为 `{provider, model_id, settings}`，取不到写 `null`；`record_counts` 对本模块**恒为空 map**，不是"尚未统计"。

## 6. 兼容边界

- 草稿 schema 的 `draft_version` 为 `1.0`，`$id` 采用 `planner-agent/1.0/` 形式。[Autoformalization Agent](<../Autoformalization Agent/AGENT.md>) 的草稿 `$id` 使用 `autoformalization/1.0/`（无 `-agent`）；这处命名不一致是已知的，本轮不改任何一侧。
- [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2 写"Reader/Planner 与通用存储操作的**有限**类型全集仅列在机器目录中"。按 agents.json 实测，`planner.propose` 的 `input_record_types` 与 64 类目录逐项相同，是全集而非真子集。以 agents.json 为准；真正的限制来自任务能力与独立性检查，不是类型筛选。
- [SCHEDULING.md](../SCHEDULING.md) 全文没有出现 `planner.propose` 这个 operation 名。本模块的调度约束只能引用其通用条款（§4 状态机与两道门、§5 并发／复用／重试／预算），不得声称 SCHEDULING.md 为本操作规定了专门顺序。
- SCHEDULING.md §3 第 1 步的"Planner 对接 `AgentizationPlan`、`ProcessingProfile`"指读取与提议，不是产出权；与 agents.json 的空输出白名单不矛盾。
- agents.json 的 principle 2 要求建议带"预算边界和停止条件"。草稿 schema 故意没有 `limits` 键，因此预算边界**只能**写成 `reason`／`blocked_on` 里的散文，没有任何机器检查它；停止条件的可检查部分只有 `blocked_on` 的文本顺序。这一处规范意图与可执行接口的落差记在 [validation-report.json](validation-report.json)。
- [AGENT.md](AGENT.md) 的 status 行与 §3 末句仍写"本轮未运行检查器""不保证已实现这条可派单规则"。检查器现已实现 `FOLLOW_UP_BLOCKED` 并已接入 `tests/run_agent_tests.py`；该文字与当前代码的差异记在 validation-report.json，本轮不改 AGENT.md。
- 尚未实现：scheduler 本身、宿主 `WorkBinding` 的用途／路线模板与接纳服务、预算账本、真实记录登记与身份核验。本文件是这些实现的契约，不是它们已存在的声明。
