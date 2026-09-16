# 判定规则与正反例

本文件是 [AGENT.md](AGENT.md) 的规范性附件，与 Paper、Autoformalization 两个模块的 CONFORMANCE 同构。例子全部是人工教学材料，不是任何一次真实执行的结果。每条说明：情形、应发生什么、禁止什么、哪一层拦得住。文中「机器」只指 [check_interfaces.py](check_interfaces.py) 当前**实际执行**的规则；写「未接入」的地方就是现在没有任何机器拦截，不要读成"暂时还没写测试"。

## 1. 冲突时的固定优先级

实际观测到的执行事实 → 当次固定 request 与 Task 的绑定 → [agents.json](../agents.json) 的操作白名单 → 本目录文档的默认写法。

程序自报与真实字节冲突时以真实字节为准；文档与 agents.json 冲突时以 agents.json 为准。四层都决定不了时**停止**：`execution` 写 `null`、`outputs` 留空、把缺什么写进 `open_items`，不自选更方便的一侧，也不为了让回执"看起来完整"而补字段。

## 2. `host_mode` 的固定判定顺序

`host_mode` 是回执 schema 的两值 enum，决定这份回执能不能承载业务输出。从上往下选第一个符合者。

| 优先级 | 值 | 什么时候选 | 不表示什么 |
|---|---|---|---|
| 1 | `OFFLINE_DIAGNOSTIC` | 没有可定位的真实执行事实：命令未运行、只做了本地形状检查、只准备了请求 | 不表示已执行生产动作；不表示"轻量版通过" |
| 2 | `EXECUTED` | 受控执行边界内真实运行过，`command`、`exit_code`、起止时间与 `tool_versions` 均有依据 | 不表示结果正确、独立、可复用或已获批准 |

两者之外没有第三种。真实执行事实完全缺失时，`execution` 整块写 `null`，不得为了填必填键而造一个 `OFFLINE_DIAGNOSTIC` 的假时间戳。当前机器只检查 `host_mode == "EXECUTED"` 与 `outputs` 非空的搭配（见 E02），不检查这个值本身是否属实（见 E01）。

## 3. 最小正反例

### E01 未执行却把回执填成功

情形：程序没有真的跑，回执写 `host_mode: "EXECUTED"`、`exit_code: 0`、一段看起来合理的起止时间。

- 应发生：`execution` 写 `null`，`outputs` 留空，`open_items` 说明缺什么、下一步需要谁执行；参照 [conformance/capture-receipt-diagnostic.json](conformance/capture-receipt-diagnostic.json)。
- 禁止：为了满足必填键伪造时间、退出码或工具版本；把"我可以跑"写成"我跑过了"。
- 拦截：**未接入**。离线检查器只读 JSON，不核验任何进程。实测：`host_mode: "EXECUTED"` 配 `command: []` 与 `exit_code: null` 仍 `checks_passed: true`。防线只有受控执行边界与宿主的 `request_hash` 重算。

### E02 诊断回执夹带业务输出

情形：`execution` 为 `null` 或 `host_mode` 不是 `EXECUTED`，`outputs` 里却有一条 status-view。

- 应发生：诊断就只交诊断——`outputs` 为空，内容进 `artifacts` 或 `open_items`。
- 禁止：把诊断当交付；用"形状合法"替代"确实执行过"。
- 拦截：机器（`DIAGNOSTIC_OUTPUT`，exit 1）。正是 [conformance/project-receipt-diagnostic-output.json](conformance/project-receipt-diagnostic-output.json) 这条 fixture。

### E03 什么都不说的回执

情形：`outputs`、`artifacts`、`open_items` 三者同时为空。

- 应发生：至少交一样——业务输出、附件，或一条说明缺口的 `open_items`。`utility.persist` 的业务输出恒为空，它的交付物就是事务回执附件。
- 禁止：用一份空回执占位，让调度器以为这一步已经完成。
- 拦截：机器（`EMPTY_RECEIPT`，exit 1）。实测：`execution` 非 null 也照样报错。

### E04 请求读取不被允许的输入族

情形：`utility.capture` 的 request 把 math-claim 写进 `input_refs`；或 `utility.assemble-packet` 把 environment-check 写进 `input_refs`。

- 应发生：拒绝该请求；确实需要新输入族时按 G-02／G-03 走白名单变更，不临时放宽。
- 禁止：把不允许的记录改塞进 `input_artifacts` 绕过边界。
- 拦截：机器（`REQUEST_INPUT`，exit 1）。允许集 = 该 operation 的 `input_record_types` ∪ 三种通用上下文。即 [conformance/request-capture-rejected.json](conformance/request-capture-rejected.json)。

### E05 请求声明本操作产不出的类型

情形：`utility.persist` 的 request 在 `expected_record_types` 里写 `source-snapshot`（该操作的输出白名单是空数组）。

- 应发生：拒绝；`utility.persist` 的 `expected_record_types` 必须为空。
- 禁止：把"这次保存了什么"重新声明成"这次产出了什么"。
- 拦截：机器（`REQUEST_OUTPUT`，exit 1）。附带一条形状规则：`expected_record_types` 只收短名，写成 `agtxiv.v3.source-snapshot/0.0.0` 会先被 `SCHEMA` 拒绝。同源的冗余：request 的 `operation` enum 与 agents.json 的八个 operation 逐字相同，因此检查器里的 `REQUEST_OPERATION` 同样不可达——未注册的 operation 名先被 `SCHEMA` 拒绝。

### E06 请求的输入引用同身份不同哈希

情形：`input_refs` 里出现两条 `record_id`／`revision` 相同但 `content_hash` 不同的引用。

- 应发生：拒绝；先确定到底用哪一份字节，再重建请求。
- 禁止：让程序"自己挑一份"或按数组顺序取第一条。
- 拦截：机器（`REQUEST_REFS`，exit 1，消息 `Duplicate identity/revision, even with a different hash`）。

### E07 `utility.persist` 回执夹带业务输出

情形：persist 回执的 `outputs` 里放了一条被保存记录的副本，或一条 admission-decision。

- 应发生：`outputs: []`；事务事实进 `artifacts`。保存一条 admission-decision 不等于执行该决定。
- 禁止：把输入重新声明为本操作的新业务产出。
- 拦截：机器（`SCHEMA`，exit 1，两条错误：`is expected to be empty` 与 `Expected at most 0 items but found 1 extra`）。这条由 schema 的 `maxItems: 0, items: false` 保证，没有专用错误码。

### E08 回执交出白名单外的业务类型

情形：`utility.project` 的回执交一条 release-manifest。

- 应发生：拒绝；投影只产 status-view，发布清单属 `utility.export`。
- 禁止：借"同一个 utility 服务进程"把两个操作的输出混在一份回执里。
- 拦截：机器（`SCHEMA`，exit 1）。诚实说明：回执 schema 的 `oneOf` 分支 const 已经限死类型，而 schema 失败会提前返回，所以检查器里那条 `RECEIPT_OUTPUT` 在当前实现下**不可达**；真正生效的是 schema 分支，加上装载期把分支集合与 agents.json 比对的漂移守卫（分支与白名单不符时抛 `INPUT_ERROR: Receipt schema whitelist mismatch`，exit 2）。不要把 `RECEIPT_OUTPUT` 当成独立的第二道防线。

### E09 成功值条件门在回执层不生效（formal-check）

情形：回执交一条 `outcome: "KERNEL_CHECKED"` 的 formal-check，但 `built_declarations` 为空，或其中某项 `is_axiom: true`，或 `placeholder_findings` 非空，或 `exit_code: 7`。

- 应发生：没有真实内核结果时只能交 `FAILED`／`BLOCKED` 并保留真实日志；`logs` 在 v0.0 是 `minItems: 1`，没有日志就没有这条记录。
- 禁止：凑齐四项字段让成功值"看起来"合法；用生成器自述或日志字符串代替内核结果。
- 拦截：**未接入**。v0.0 的四重条件门写在业务 schema 的**根层 `allOf`** 上，而回执的 `payload` 只 `$ref` 到 `#/properties/payload`，根层 `allOf` 不随之生效。实测：上述四种写法在 `--kind formal-check` 下全部 `checks_passed: true`。这些门只有在宿主把回执装配成完整业务记录、用整份业务 schema 校验时才触发（实测同一 payload 交给 `SchemaBundle.validate_record` 的校验器即报 `False was expected`／`0 was expected`／`is expected to be empty`）。**这是本目录机器覆盖最弱的地方。**

### E10 其余三处成功值门同样不在回执层生效

情形与 E09 同构，机制完全相同（根层 `allOf` 不随 `#/properties/payload` 引用进来），实测均通过：

| 记录 | 被绕过的门 | 实测写法 |
|---|---|---|
| source-acquisition | `ACQUIRED` 要求 `artifacts` 非空且 `final_uri` 非 null | `outcome: "ACQUIRED"`、`artifacts: []`、`final_uri: null` |
| release-certificate | `CERTIFIED` 要求 `failed_checks` 为空 | `outcome: "CERTIFIED"` 配一条 `failed_checks` |
| archive-receipt | 契约要求"检查点缺失不得声明独立锚定"（v0.0 根本没有这条 `allOf`） | `assurance: "INDEPENDENTLY_ANCHORED"`、`checkpoint_ref: null` |

- 应发生：取得失败写 `FAILED`／`BLOCKED` 并保留真实 `reason`；认证不通过写 `REJECTED` 并逐条列出失败检查；没有独立检查点就写 `LOCAL_PERSISTENCE`。
- 禁止：用成功枚举值换取下游放行。
- 拦截：**未接入**（回执层）。宿主装配完整记录后的整份校验能拦住前两条；第三条在 v0.0 里连 `allOf` 都没有，只由 [AGENT-CONTRACTS §4.9](../AGENT-CONTRACTS.md) 与 agents.json 的 principle 约束，属人工。

### E11 本地封存冒充正式发布

情形：把一次 Git 文件快照导出写成 paper-release，或在没有对应 release-audit／release-certificate 时就交 archive-receipt。

- 应发生：普通封存只交附件；release-manifest → release-audit → release-certificate → paper-release → archive-receipt 的保留顺序见 [AGENT-CONTRACTS §3](../AGENT-CONTRACTS.md)。
- 禁止：循环引用尚不存在的证书；把候选批次（[STORAGE.md](../STORAGE.md) 的 `CANDIDATE_EXPORT`）说成 paper-release。
- 拦截：**未接入**。paper-release 与 archive-receipt 都在 `utility.export` 的输出白名单里，检查器只比对类型，不检查顺序、前置记录是否存在、证书 `outcome` 是否为 `CERTIFIED`（v0.0 的 `paper-release` 没有这条 `allOf`）。实测：一份带三个任意 `*_ref` 的 paper-release 回执 `checks_passed: true`。防线是宿主的前置输入核验与人工。

### E12 `follow_up_requests` 越界

情形：(a) `agent: "utility"` 配 `operation: "proof.expand"`；(b) 对 `review.backtranslate` 的 FollowUp 里带上 math-claim。

- 应发生：(a) 用 agents.json 里真实注册的配对；(b) 盲反译的输入隔离是它成立的前提，只能给 formal-environment。
- 禁止：借 FollowUp 把本操作读不到的记录推给别人代读；借"通用上下文许可"给 backtranslate 开口子。
- 拦截：机器（(a) `FOLLOW_UP_OPERATION`，(b) `FOLLOW_UP_INPUT`，均 exit 1）。检查器为 `review.backtranslate` 带了专门分支：允许集被收窄为 `{formal-environment}`，通用上下文许可不适用。诚实说明：检查器**不**检查目标 operation 的必需输入是否齐全，也不检查这些引用是否真实存在。

### E13 request 与 Task 不一致

情形：request 的 `task_id`、`input_refs`、`expected_record_types`、`allowed_commands` 或 `parameters.timeout_seconds` 与当前 Task 不一致；或用参数把一个 operation 转成另一个。

- 应发生：拒绝执行；重新从固定 Task 投影出新的 request。
- 禁止：把 request 当成可以再谈判的工作单。
- 拦截：**未接入**。本目录的检查器没有 `--task` 模式，因此没有 `INVISIBLE_REF`／`UNDECLARED_OUTPUT` 这类绑定检查；`request_hash` 也不会被重算。这一层完全由宿主适配器承担，对应 [PENDING_TESTS.md](../PENDING_TESTS.md) U-01。

### E14 `allowed_commands` 被当成 shell 字符串

情形：`allowed_commands` 里写 `"fetch-source; rm -rf /"`，或适配器把白名单字符串直接拼进 shell。

- 应发生：白名单里只放受控服务的命令名；实际 argv 由固定适配器生成。
- 禁止：从来源字节、论文正文或回执里读取要执行的命令。
- 拦截：**未接入**。检查器只校验字符串长度与唯一性，不解析命令语义。实测：上述写法 `checks_passed: true`。防线是受控执行边界。

### E15 同一主体既导出又认证

情形：同一个 utility 服务进程先跑 `utility.export` 交出 release-manifest，再跑 `utility.certify` 给它签认证。

- 应发生：两次调用由不同实际主体承担，认证方另需 authority-policy 与真实独立运行资格。
- 禁止：用"换一个进程名／换一份模板"当独立；用 JSON 校验通过代替认证。
- 拦截：人工 + 宿主身份核对。规则本体见 AGENT.md §1 的 I1 行与 [AGENT-CONTRACTS §6](../AGENT-CONTRACTS.md)；本模块检查器不看身份。

### E16 组包时补造前提或消除缺口

情形：`utility.assemble-packet` 发现所选 proof-plan 缺一个引理，就在 packet 里补一条 `expected_declarations`，或把 `open_obligation_ids` 清空。

- 应发生：缺什么就停，写进 `open_items` 并提 FollowUp；探索包保留未证义务，`EXPLORATORY` 不因组装完成而变成 `RELEASE_CANDIDATE`。
- 禁止：把不同路线的已通过片段拼成新证明。
- 拦截：人工。规则本体见 [AGENT-CONTRACTS §5](../AGENT-CONTRACTS.md)；检查器只比对类型白名单，看不出 packet 内容是复制还是补造。

### E17 缓存命中冒充本轮检查

情形：`utility.formal-check` 复用上一轮的构建缓存或旧环境结论，回执里照样写本轮的 `started_at`／`finished_at`。

- 应发生：环境、工具链或库版本变化时重跑受影响检查，历史结论保留原环境归属；工具链与依赖锁政策见 [Autoformalization ENVIRONMENT.md](<../Autoformalization Agent/ENVIRONMENT.md>)。
- 禁止：把旧环境的 `KERNEL_CHECKED` 迁移成新环境的通过。
- 拦截：人工 + 环境政策。检查器不知道缓存是否命中，也不核验 `tool_versions` 是否属实——这两条都写在它的 `unchecked` 里。

## 4. 一致性如何验收

三层分开报告，前一层通过不等于后一层通过。

1. **机械不变项**：request 的操作／输入族／预声明类型合法，回执形状封闭，`outputs` 类型在白名单内，诊断回执不带业务输出，FollowUp 的配对与输入族合法。这一层就是 `check_interfaces.py` 的 `checked` 列表，且只覆盖它列出的层。
2. **执行事实核验**：宿主重算 `request_hash`、在受控输出根内读取真实字节重算 `artifacts` 哈希、把回执绑定到真实 attempt、核对 `tool_versions` 与日志来源。**本目录没有任何代码做这一层**，它的缺席逐条写在检查器的 `unchecked` 与 [validation-report.json](validation-report.json) 的 `not_implemented_or_not_established` 里。
3. **内容与身份**：成功值条件门（E09／E10）、发布顺序与前置记录（E11）、认证主体独立性（E15）、组包忠实性（E16）。这一层由宿主装配完整业务记录后的整份校验、独立审阅与人工承担。

退出码 0 只表示"已执行的层里没发现问题"，不表示合规、正确或已执行。命令条数、回执字节数或 JSON 相似度都不是质量指标。

## 5. 现在可运行什么

从仓库根目录运行：

```bash
.venv/bin/python -B 'schema v0.1/Utility Agent/check_interfaces.py' --kind request --input 'schema v0.1/Utility Agent/conformance/request-capture.json'
.venv/bin/python -B 'schema v0.1/Utility Agent/check_interfaces.py' --kind request --input 'schema v0.1/Utility Agent/conformance/request-capture-rejected.json'
.venv/bin/python -B 'schema v0.1/Utility Agent/check_interfaces.py' --kind capture --input 'schema v0.1/Utility Agent/conformance/capture-receipt-diagnostic.json'
.venv/bin/python -B 'schema v0.1/Utility Agent/check_interfaces.py' --kind project --input 'schema v0.1/Utility Agent/conformance/project-receipt-diagnostic-output.json'
.venv/bin/python -B -m pytest 'schema v0.1/Utility Agent/tests' -q -p no:cacheprovider
.venv/bin/python -B 'schema v0.1/tests/run_agent_tests.py'
```

`--kind` 取 `request` 或七个操作后缀（`capture`、`register-plan`、`assemble-packet`、`formal-check`、`persist`、`export`、`project`、`certify`）。退出码：0 = 已执行的层未发现问题；1 = 检查发现问题；2 = 输入或检查器装载错误（包括回执 schema 分支与 agents.json 白名单漂移）。上面四条 fixture 命令的预期退出码依次是 0、1、0、1，四条都已接进 `schema v0.1/tests/run_agent_tests.py`。

本目录**没有**执行过任何命令、数据库事务、Git 发布或 Lean 构建；对应的待测条目见 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 U-01…U-08，其中 U-06 与 U-08 本轮明令禁止运行。2026-09-16 的真实执行记录与哈希见 [validation-report.json](validation-report.json)。
