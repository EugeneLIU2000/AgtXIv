# 判定规则与正反例

本文件是 [AGENT.md](AGENT.md) 的规范性附件，与 Paper、Autoformalization 两个模块的 CONFORMANCE 同构。例子是人工教学材料，不是调度验证结果。文中"机器"只指 [check_interfaces.py](check_interfaces.py) **当前实际执行**的规则；写"人工"或"未接入"的地方，今天没有任何程序会拦住它。接口形状见 [INTERFACE.md](INTERFACE.md)。

## 1. 冲突时的固定优先级

本轮用户目标的硬前置缺口 → 已有真实产物能否直接复用 → 当前主线最少的一步 → 候选与审计等可延后的工作。

先确认此次用户目标，不把"建立框架"自动扩成"部署全部服务"；再区分资料缺失与数学反例，两者的下一步不同；已有真实产物且未受影响的步骤不重复生产。四项都决定不了时，交一份**带明确阻塞**的计划，或说明需要什么新信息，不为了让 `proposals` 非空而制造任务。建议的数组顺序表达优先级，不新增 `priority` 或自动执行字段。

## 2. 一条判断放进哪个位置的固定顺序

草稿只有四个位置可以承载一条判断。下表是位置选择顺序，**不是 JSON 字段的枚举值**：草稿里没有任何键取这些名字。

| 优先级 | 位置 | 什么时候选 | 不表示什么 |
|---|---|---|---|
| 1 | `proposals` + `follow_up_requests` | 该建议的已知前置缺口为空，且希望宿主优先评估 | 不表示已派任务，也不表示宿主核对可以跳过 |
| 2 | 仅 `proposals`，`blocked_on` 为空 | 无已知前置缺口，但不必抢先评估 | 空的 `blocked_on` 不表示前置条件已经被验证过 |
| 3 | 仅 `proposals`，`blocked_on` 非空 | 工作方向已经明确，但缺来源、范围、预算或上游产物 | 不表示该工作被否决；也不得进入 `follow_up_requests` |
| 4 | `open_items` | 缺口不挂在任何一条具体建议上（例如父预算未知） | 不是免责声明，也不是待办清单 |

选不到 1–3 时不要退而求其次造一条模糊建议。`follow_up_requests` 是 `proposals` 的子集，不是第二份清单。

## 3. 最小正反例

`--task` 指 `check_interfaces.py` 的 `--task <task.json>` 参数。凡标"需 `--task`"的规则，不给 Task 时报告会在 `unchecked.task` 明确记为未检查，**不是默认通过**。

### E01 无进展时自派下一轮规划

情形：草稿里出现 `{"agent":"planner","operation":"planner.propose", ...}`，理由是"再规划一次以细化拆分"，输入与本轮完全相同。

- 应发生：说明需要什么新信息，写进 `open_items`；重规划由宿主在真实新记录、新来源、新预算或用户目标变化后触发。
- 禁止：用更多文字刷新无进展计数；用自派单代替"当前没有有用下一步"这句话。
- 拦截：给了 Task 时机器（`SELF_REDISPATCH`，错误）；未给 Task 时机器只发**告警**，因为可见性无从核对。fixture：[conformance/propose-draft-rejected.json](conformance/propose-draft-rejected.json) 的 `/proposals/3`。

### E02 带阻塞的建议被登记为可派单

情形：某 proposal 的 `blocked_on` 写明"缺冻结基准"，同一条却出现在 `follow_up_requests` 里。

- 应发生：保留该 proposal 与它的 `blocked_on`；`follow_up_requests` 只收无已知前置缺口的那部分。
- 禁止：为了让它被优先评估而清空 `blocked_on`；也不得把"宿主反正还会检查"当作可以先登记的理由。
- 拦截：机器（`FOLLOW_UP_BLOCKED`）。fixture：[conformance/propose-draft-blocked-follow-up.json](conformance/propose-draft-blocked-follow-up.json)，整份草稿退出码 1。

### E03 建议一个不存在的 operation

情形：建议 `planner.run`、`dag.build`、`scheduler.dispatch` 之类听起来合理但不在 agents.json 中的操作。

- 应发生：只使用 [agents.json](../agents.json) 中已注册的 `agent`／`operation` 配对。
- 禁止：为表达"希望宿主做某事"而发明操作名；也不得把宿主内部动作写成 operation。
- 拦截：机器（`PROPOSAL_OPERATION`，follow_up 侧为 `FOLLOW_UP_OPERATION`）。该条失败后本条建议的后续检查跳过，同一份草稿的其他建议继续检查。

### E04 agent 与 operation 错配

情形：`{"agent":"review","operation":"dependency.search"}`——两个名字各自都存在，配对不存在。

- 应发生：按 agents.json 的实际归属填写；操作名的前缀必须等于它的 `agent_id`。
- 禁止：用 agent 字段表达"希望谁来审"；承担者由 agents.json 决定，回避名单由宿主决定。
- 拦截：机器（`PROPOSAL_OPERATION` / `FOLLOW_UP_OPERATION`，消息为 `Agent/operation mismatch`）。

### E05 给被建议的操作喂越界输入

情形：建议 `review.backtranslate`，`input_refs` 里放了 `scientific-claim`。

- 应发生：`review.backtranslate` 的首轮业务输入只允许 `formal-environment`；其余操作允许各自白名单加三类通用上下文，规则本体见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2。
- 禁止：以"这些记录本轮反正可见"为由扩大被建议操作的输入；可见不等于可传递。
- 拦截：机器（`PROPOSAL_INPUT` / `FOLLOW_UP_INPUT`，消息为 `Disallowed proposed input family`）。检查器对每条建议按**被建议的那个 operation** 重算允许集，并带有 backtranslate 特例分支。fixture：[conformance/propose-draft-rejected.json](conformance/propose-draft-rejected.json) 的 `/proposals/2`。

### E06 同一身份两个不同哈希

情形：同一条建议的 `input_refs` 里，同一 `record_id` 与 `revision` 出现两次，`content_hash` 不同。

- 应发生：一个身份加修订对应唯一字节；引用不同版本时写成不同的建议，或在 `blocked_on` 里说明需要宿主固定哪一版。
- 禁止：用"最新版"语义混用引用。
- 拦截：机器（`PROPOSAL_INPUT` / `FOLLOW_UP_INPUT`，消息为 `Duplicate identity/revision, even with a different hash`）。

### E07 引用本轮没给的记录，或引用未来产物

情形：建议里引用 `scientific-claim:two`，而 Task 只给了 `scientific-claim:one`；或引用一条"下一步会生成"的记录身份。

- 应发生：只引用 `Task.input_refs` 的精确成员；需要新产物时先写 `blocked_on` 描述所需内容，宿主保存后再新建 Task。
- 禁止：用 local placeholder 冒充正式引用；用 `depends_on` 之类的说法替代未来输出。
- 拦截：机器（`INVISIBLE_REF`，需 `--task`）。不给 Task 时**没有机器拦截**，报告在 `unchecked.task` 中写明这一层未执行。

### E08 提权：结构化被拦，散文不被拦

情形（a）：proposal 里加 `"capabilities": ["records.write"]`、`"limits": {...}`、`"exclusions": []` 或 `"acceptance": "DELIVERY"`。
情形（b）：同一请求写成 `reason` 里的一句话——"需要 records.write 与更高预算，请去掉回避名单"。

- 应发生：权限、预算、回避与验收门都由宿主固定；建议只描述要做的工作与缺什么。
- 禁止：把提权请求塞进任何自由文本并期望宿主执行；宿主不从建议文本提取提权命令。
- 拦截：（a）机器（`SCHEMA`——草稿对象封闭，根本没有这些键）；（b）**未接入**，检查器实测让它通过，报告键 `escalation_in_prose` 原文说明了这一点。这一条是本模块机器覆盖最弱的地方，实际防线是宿主固定 Task 字段与人工阅读。

### E09 夹带业务记录

情形：把一条 `agentization-plan` 或 `scientific-claim` 的 `{record_type, payload}` 放进 `records`，或塞进建议对象的额外键里。

- 应发生：`records` 恒为 `[]`；`planner.propose` 的 `output_record_types` 是空数组，业务记录由相应生产操作产出。
- 禁止：用附件通道绕过类型检查；用"先放着等宿主装配"当理由。
- 拦截：机器（`SCHEMA`：`records` 为 `maxItems: 0, items: false`，实测报两条错误）。检查器另有一条 `SMUGGLED_RECORD` 反夹带扫描，它在当前 schema 下**不可能触发**——草稿所有对象都封闭，`RecordRef` 的键集合恰好等于四个引用键，任何夹带在扫描之前就已被 schema 拦下并提前返回。它是 schema 被放宽时的第二道闸，不是今天正在工作的检查，不要把它当作现有保障。

### E10 同一 agent、operation 与输入集合提两次

情形：同一份草稿里两条建议的 `agent`、`operation` 与 `input_refs` 集合完全相同，只有 `reason` 不同（例如"检索前提"与"检索基准"两个真实不同的用途）。

- 应发生：已经存在的相同待办合并引用，不重复排队；用途或路线确实不同且无法用当前 proposal 无歧义表达时，写 `blocked_on` 请求拆清。
- 禁止：靠 `reason` 的措辞差异让宿主去猜是不是同一件事。
- 拦截：机器（`DUPLICATE_PROPOSAL`）。注意方向：机器按 `agent`+`operation`+`input_refs` 集合判重，因此**两个真实不同的用途也会被判为重复**；草稿没有表达用途或路线的字段。这是已登记的接口缺口 G-05（[PENDING_TESTS.md](../PENDING_TESTS.md)），宿主侧的去重键另含 brief、用途、政策与回避名单，不能用检查器的判重当作安全去重。

### E11 用提出子任务换取新的预算额度

情形：本轮已经接近 `max_attempts` 或 `no_progress_limit`，于是把同一件事拆成三条子建议，期望每条各自获得完整额度。

- 应发生：子任务消耗父计划的预留额度（[SCHEDULING.md](../SCHEDULING.md) §5 第 5 条）；父预算未知时写进 `open_items`，不声称建议已经可调度。
- 禁止：把"分解"当成刷新额度的手段；把重写答案当作有进展。
- 拦截：**未接入**。检查器看不到父计划剩余额度，无法区分有界分解与耗尽全树预算的分解；报告键 `budget_and_no_progress` 原文说明了这一点。实际防线是宿主的预算账本，而它尚未实现（见 [validation-report.json](validation-report.json)）。

### E12 空的 blocked_on 被当成前置条件已满足

情形：一条建议的 `blocked_on` 为 `[]`，宿主据此直接固定 Task，不再核对源文件、范围、预算与门槛。

- 应发生：`blocked_on` 为空只表示**模型没有发现**已知缺口；宿主仍按固定规则核对实际类型、预算、capabilities、exclusions 与前置门（[SCHEDULING.md](../SCHEDULING.md) §3.3）。
- 禁止：把模型的空数组当作宿主检查的替代；把检查器退出码 0 读成"这条建议可以派单"。
- 拦截：**人工与宿主**。检查器不检查被建议操作的必需输入是否齐全，也不检查被引用记录是否真实存在（报告键 `required_inputs_of_proposed_operation`）。

### E13 建议的质量本身

情形：建议格式全对、配对全对、引用全可见，但它没有回答用户这一轮的目标，或把"建立框架"扩成了部署全部服务。

- 应发生：先确认此次用户目标，提出能推动当前主线的最少工作。
- 禁止：把"通过了接口检查"读成"这是一份好计划"。
- 拦截：**未接入**。报告键 `plan_quality` 原文写明：是否有依据、是否有界、是否非冗余、是否拆到有用的深度、是否回答了用户的实际目标，都不检查；只检查配对、输入族与引用可见性。

### E14 声明业务输出

情形：宿主给出的 `Task.expected_record_types` 非空，例如 `["agentization-plan"]`。

- 应发生：`planner.propose` 的输出白名单为空，这样的 Task 不可调度；需要登记计划时建立 `utility.register-plan` 的 Task。
- 禁止：为了让 Planner"顺便产出计划"而放宽任务声明。
- 拦截：机器（`NONEMPTY_EXPECTED_TYPES`，需 `--task`；共享 Task 契约另以 `TASK_CONTRACT` 重复拦下，消息不如前者具体）。

## 4. 一致性如何验收

三层分开报告，前一层通过不等于后一层通过：

1. **机械不变项**：草稿封闭形状、`records` 为空、`agent`/`operation` 配对存在、输入族在被建议操作的允许集内、引用无重身份冲突、`follow_up_requests` 是无阻塞 proposals 的子集；给了 Task 时另加声明输出为空、Task 契约与引用可见性。检查器只覆盖它在 `checked` 中列出的层。
2. **内容覆盖**：逐条核对建议是否对应用户本轮目标、缺口是否写在正确的位置、`checked` 里列的是不是真读过的东西、阻塞是否真实存在。这一层今天没有机器。
3. **差异处置**：措辞不同但指向同一件工作应合并；用途不同、路线不同、版本不同必须分开表达，表达不了就写 `blocked_on`。建议条数、文本长度与相似度都不能当质量指标。

## 5. 现在可运行什么

从仓库根目录运行（2026-09-16 实测，退出码为实际观测值）：

```bash
.venv/bin/python -B 'schema v0.1/Planner Agent/check_interfaces.py' --kind propose \
  --input 'schema v0.1/Planner Agent/conformance/propose-draft.json'
.venv/bin/python -B 'schema v0.1/Planner Agent/check_interfaces.py' --kind propose \
  --input 'schema v0.1/Planner Agent/conformance/propose-draft.json' \
  --task 'schema v0.1/Planner Agent/conformance/task.json'
.venv/bin/python -B 'schema v0.1/Planner Agent/check_interfaces.py' --kind propose \
  --input 'schema v0.1/Planner Agent/conformance/propose-draft-rejected.json'
.venv/bin/python -B 'schema v0.1/Planner Agent/check_interfaces.py' --kind propose \
  --input 'schema v0.1/Planner Agent/conformance/propose-draft-blocked-follow-up.json'
.venv/bin/python -B -m pytest 'schema v0.1/Planner Agent/tests' -q -p no:cacheprovider
.venv/bin/python -B 'schema v0.1/tests/run_agent_tests.py'
```

前四条依次得到 0、0、1、1。加 `--task` 时 `checked` 从 8 层增至 11 层（多出 `task_declared_outputs`、`task_contract`、`task_exact_refs`），`unchecked.task` 随之消失。`--require-task` 在缺 Task 时报 `TASK_REQUIRED`（退出码 1）；`--fail-on-warning` 把 `REASON_FORMAT`／`OPEN_ITEM_FORMAT` 告警升为退出码 1。

退出码含义：0 表示**已执行的层**未发现问题，不是"合规"、不是"这条建议可以派单"；1 表示检查发现问题；2 表示输入不可读、参数错误，或草稿 schema 与 [agents.json](../agents.json) 漂移（例如 `planner.propose` 不再是空输出白名单，或 `records` 不再是 `maxItems: 0, items: false`），此时报告只有一条 `INPUT_ERROR`。

当日完整执行记录、通过的测试数与未实现清单见 [validation-report.json](validation-report.json)。
