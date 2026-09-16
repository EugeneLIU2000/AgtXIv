# 判定规则与正反例

本文件是 [AGENT.md](AGENT.md) 的规范性附件，与 Paper、Autoformalization 两个模块的 CONFORMANCE 同构。例子是人工教学材料，不是审阅结果。每条说明：情形、应发生什么、禁止什么、**哪一层能拦住**。文中"机器"只指 [check_interfaces.py](check_interfaces.py) 当前实际执行的规则（含它委托给 `../validate.py` 的 Task 契约）；写"人工"或"未接入"的地方就是现在没有任何检查器覆盖，不要读成保障。

## 1. 冲突时的固定优先级

被审对象的原始断言与字节 → 本次 Task 绑定的精确目标与范围 → 实际可见证据 → 独立条件 → 结论枚举。

先确认目标、比较方向、范围、实际可见证据与独立条件，再逐项核对，最后才选枚举值；不先猜"应该通过"再找理由。上一项没定下来时，不用下一项的方便取值代替：范围不清就交 `open_items` 与 `frontier-item`，不选一个"看起来最合适"的结论。四类状态必须分开，不能互相冒充：

| 状态 | 含义 | 不表示 |
|---|---|---|
| 已经反对 | 本次检查发现了实际冲突或反例 | 对象在别的轴上也不成立 |
| 证据不足 | 检查已做，材料不够下结论 | 对象为假 |
| 未检查 | 本次根本没看这一部分 | 通过，也不是"证据不足" |
| 不适用 | 该轴对该对象无意义 | 该轴通过 |

## 2. 两个枚举的固定判定顺序

### 2.1 `ReviewContext.independence`

| 优先级 | 值 | 什么时候选 | 不表示什么 |
|---|---|---|---|
| 1 | `UNESTABLISHED` | 模型草稿阶段一律选此值；宿主尚未核定真实主体与生产参与者 | 审阅者有利益冲突 |
| 2 | `ROLE_SEPARATED` | 宿主已核对实际主体不在被审对象的生产参与者集合内 | 结论正确，或已有外部见证 |
| 3 | `INDEPENDENTLY_ATTESTED` | 另有独立提供的身份证据支持上一项 | 科学上成立 |

后两值只能由宿主按真实执行事实装配；换模型名、换昵称或换进程都不构成独立（见 [I1–I6](<../Autoformalization Agent/AGENT.md>) 的 I1 与 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §6）。

### 2.2 `axis-assessment.result`

先定 `applicability`，再定 `execution`，最后才定 `result`。

| 优先级 | 值 | 什么时候选 | 不表示什么 |
|---|---|---|---|
| 1 | `NOT_ASSESSED` | `applicability = NOT_APPLICABLE`，或本轴这次根本没做 | 该轴通过 |
| 2 | `INCONCLUSIVE` | 做了检查但材料不足以下判断 | 对象有问题 |
| 3 | `COUNTEREVIDENCE` | 找到了实际反证，`counterevidence_refs` 非空 | 整个目标为假 |
| 4 | `PARTIALLY_SUPPORTED` | 部分成立，剩余条件写进 `conditions` | 条件可以在下游省略 |
| 5 | `SUPPORTED` | 本轴证据完整，`support_refs` 非空且 `execution = COMPLETED` | 其它五轴也成立；更不等于科学结论成立（见 AGENT-CONTRACTS §2.1） |

六轴分别交代。形式检查通过不能推出模型、单位、近似或经验结论成立；缺失资料与不适用不能混用。

## 3. 最小正反例

### E01 反译首轮看见原文或预期答案

情形：给 `review.backtranslate` 的 Task 里，`input_refs` 除 `formal-environment` 外还放了 `math-claim`（预期答案）、`source-snapshot` 或既有 `alignment-assessment`。

- 应发生：拒绝该 Task；业务输入恰为 `{formal-environment}`，必要定义只以固定形式代码字节经 `input_artifacts` 进入。
- 禁止：用"通用上下文许可"或"反正都要读"把 policy、profile、plan、packet 或原文塞进首轮。
- 拦截：**机器**（`TASK_CONTRACT`，消息 `Disallowed input family`；若换成 `BLIND_FORBIDDEN` 集合内的类型则是 `Source-blind work has forbidden visible input`）。反例 fixture：[conformance/task-backtranslate-leak.json](conformance/task-backtranslate-leak.json)，正例 [conformance/task-backtranslate.json](conformance/task-backtranslate.json)。

### E02 反译草稿自带业务记录或身份字段

情形：模型在 backtranslate 草稿里直接交一条 `backtranslation` 记录，或自填 `packet_ref`、`source_blind`、`visibility_evidence`。

- 应发生：模型只交 `interpretation` 与 `conditions`；宿主在解释冻结后按真实工作链装配正式记录。
- 禁止：模型自报独立性或自报读过哪个包。
- 拦截：**机器**（`SCHEMA`：`backtranslate-draft` 的 `records` 为 `maxItems: 0` 且 `items: false`，顶层 `additionalProperties: false`，自加字段一并被拒）。

### E03 删掉注释就称严格盲审

情形：形式代码的注释或文件名泄漏了原文答案，宿主直接删注释后交给首轮，不保留原始字节与转换规则。

- 应发生：提供**经过记录的中性输入版本**，保留原始字节、转换规则、新附件身份与可见性记录；转换是否保持形式含义另行核对。
- 禁止：静默修改数学声明；把"删了注释"等同于隔离成立。
- 拦截：**未接入**。检查器只检查 `input_artifacts` 非空且 `artifact_id` 不重复，不读字节，也不比较转换前后的形式含义。中性化转换当前没有任何实现。

### E04 草稿自称独立

情形：草稿里 `ReviewContext.independence` 写成 `ROLE_SEPARATED` 或 `INDEPENDENTLY_ATTESTED`，`producer_principal_ids` 填一个换了名字的同一主体。

- 应发生：草稿一律写 `UNESTABLISHED`，由宿主按执行事实核定后改写。
- 禁止：把换模型名当独立证据；把"我没看见原文"当可见性证明。
- 拦截：**未接入**。已实测：这样的草稿通过 `check_interfaces.py`。机器目前只拦一件相关的事——`review` 是 `validate.py` 的 independent 集合成员，Task 的 `exclusions` 为空会被 `TASK_CONTRACT`（`Independent work requires declared producer exclusions`）拒绝。**非空 `exclusions` 是格式下限，不是独立性证据**；真正的比对在 Result 层（`principal_id` 不得落在 `exclusions` 内），本目录的检查器不检查 Result。

### E05 比较类操作只给一个端点

情形：`review.reuse` 或 `review.alignment` 的 Task 只在 `target_refs` 里放了一个对象，另一端"在输入里能看到"。

- 应发生：两端都写进 `target_refs`，并明确比较方向。
- 禁止：把可见输入当成已绑定的比较端点。
- 拦截：**机器**（`TASK_CONTRACT`，消息 `Comparison requires both exact target endpoints`）。

### E06 形式对齐没有冻结反译

情形：`review.alignment` 比较 `formalization-attempt` 与数学目标，`input_refs` 里没有 `backtranslation`；或者只比较 packet 与原目标，根本没定位实际生成的代码。

- 应发生：形式对齐必须取得已冻结的 `backtranslation` 与实际形式附件；源→数学／论证、数学→形式、源→形式分别检查，不以传递性代替实际核对。
- 禁止：复制前两项冒充第三项；把 packet 与原目标的一致当成形式对齐完成。
- 拦截：**机器部分覆盖**（`TASK_CONTRACT`，消息 `Formal alignment requires frozen backtranslation`），但只在 `Task.target_refs` 命中 `formalization-packet`／`formalization-attempt`／`formal-check` 时触发。草稿里写 `comparison_kind: MATH_TO_FORMAL` 而 Task 目标不是这三类时，**没有机器拦截**；`backtranslation_refs` 也没有 `minItems`。

### E07 关系支持当成复用许可

情形：拿到一条 `relation-assessment`，直接对新目标输出 `reuse-decision: ALLOW`；或把 `CONDITIONAL` 的剩余条件在传到目标时丢掉。

- 应发生：关系评估与复用决定分轮保存；复用决定绑定具体目标用途与 `processing-profile`，形式复用另需适用的 `environment-check`。`CONDITIONAL` 的剩余条件必须传递到目标，不能满足原目标的无条件成功要求。
- 禁止：把候选关系、弱证据或不兼容环境升级为 `ALLOW`；把复用决定当成新的定理证明。
- 拦截：**机器部分覆盖**（`TASK_CONTRACT`，消息 `Reuse decision requires a processing profile`）。条件是否真的传递到目标、环境是否兼容——**未接入**；`reuse-decision` 没有任何顶层 if/then 门，`ALLOW` 在 schema 层是自由值。

### E08 声称 SUPPORTED 却没有支持证据

情形：`axis-assessment` 填 `result: SUPPORTED`、`applicability: APPLICABLE`、`execution: COMPLETED`，而 `support_refs` 是空数组。同类：`relation-assessment` 填 `outcome: ACCEPTED` 而 `witness_refs` 为空。

- 应发生：v0.0 业务 schema 的顶层 `allOf` 正是为此设的门——`SUPPORTED`／`PARTIALLY_SUPPORTED` 要求 `support_refs` 非空，`ACCEPTED` 要求 `witness_refs` 非空。
- 禁止：交"没做但看起来通过"的评估。
- 拦截：**未接入**。已实测：这两种草稿都通过 `check_interfaces.py`。原因是草稿只 `$ref` 业务 schema 的 `#/properties/payload`，**业务根层的 if/then 门不被继承**；检查器只重新实现了 `frontier-item` 那一条（见 E09），其余没有。检查器输出的 `unchecked.record_conditionals` 明说了这一点。宿主装配成正式记录时，整条业务 schema 才会生效。

### E09 未决项被标成已解决

情形：`frontier-item` 置为 `RESOLVED` 或 `SUPERSEDED`，`resolution_refs` 留空。

- 应发生：给出精确的解决证据引用；缺口不能靠改状态消除。
- 禁止：用"后续会补"当作已解决。
- 拦截：**机器**（`FRONTIER_RESOLUTION`）。这是检查器唯一重新实现的业务级条件门。

### E10 交付 Task 没有预声明的类型

情形：`review.admission` 顺手附一条 `challenge`；或 Task 的 `expected_record_types` 只有 `challenge`，草稿却交了 `frontier-item`。

- 应发生：输出只限事先声明的部分；`review.admission` 的输出白名单只有 `admission-decision`，异议走 `follow_up_requests` 与 `open_items`。
- 禁止：把"这类型在 agents.json 的白名单里"当成本次可以交。
- 拦截：**机器**（草稿层 `UNDECLARED_OUTPUT`；Task 层 `TASK_CONTRACT`，消息 `Disallowed output family`）。

### E11 引用 Task 没给的对象

情形：草稿里的 `reviewed_refs`、`target_ref` 或 `evidence_refs` 指向一个本次 `Task.input_refs` 里没有的引用，或同一身份换了一个 `content_hash`。

- 应发生：只引用实际提供的对象；需要新材料就交 `follow_up_requests`。
- 禁止：引用"应该存在"的记录；用同 ID 不同哈希制造两个版本。
- 拦截：**机器**（`INVISIBLE_REF`；`follow_up_requests` 内的同身份不同哈希由 `FOLLOW_UP_INPUT` 拦下）。但**引用合法不等于真的读过、真的核对过**：检查器不解析被引用记录，`unchecked.assessment_meaning` 明说了这一点。

### E12 空交付

情形：草稿的 `records` 为空，`open_items` 也为空或只有空白字符串。

- 应发生：要么交评估记录，要么写明为什么交不出——缺什么材料、被什么阻塞、哪一层需要先动。
- 禁止：用空数组表示"没问题"。
- 拦截：**机器**（`EMPTY_DELIVERY`）。backtranslate 草稿不适用此条，它交的是 `interpretation`。

### E13 生产者关闭针对自己的异议

情形：产生被审对象的同一主体，在下一轮交出针对该 `challenge` 的 `challenge-disposition: RESOLVED`。

- 应发生：Reviewer 提出、生产者响应并产生新修订、独立 Reviewer 决定处置，三步分轮保存。规则本体见 I1 与 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §6。
- 禁止：把"我改好了"当成异议已被独立处置。
- 拦截：**未接入**（本目录）。草稿层完全看不到主体身份。Task 层只能拦 `exclusions` 为空；真正的比对在 Result 层由 `../validate.py` 的 `Declared producer self-review/conflict` 完成，而本模块的检查器不检查 Result。

### E14 目标或输入变了仍沿用旧结论

情形：被审对象出了新修订或换了环境，旧的 `argument-review: SUPPORTED` 被当成对新版本的结论继续使用。

- 应发生：创建新任务重审；旧审阅仍属于旧版本，不因内容相似而复用结论（见 [INTERFACE.md](INTERFACE.md) §6）。
- 禁止：把旧批准覆盖成"针对最新版本"。
- 拦截：**未接入**。检查器一次只看一个草稿加一个 Task，没有跨版本的历史比较；证据复用规则尚未实现。

## 4. 一致性如何验收

三层分开，前一层通过不等于后一层通过：

1. **机械不变项**：草稿形状、类型白名单、Task 绑定、引用可见性、跟进请求的输入族。由 `check_interfaces.py` 判定，退出码 0／1／2。
2. **内容覆盖**：本次是否真的核对了绑定的目标、方向与范围，未检查部分是否如实写进 `open_items`。由人工或后续独立审阅判定，当前无机器覆盖。
3. **差异处置**：不同审阅者结论不同时，保留双方结论与各自范围，走 `challenge`／`challenge-disposition`，不取平均也不取多数。

不用相似度、记录条数或字符长度当质量指标。八份草稿都通过检查器，只说明八份草稿形状合法。

## 5. 现在可运行什么

以下命令在 `/Users/Yingjian/Documents/GitHub/AgtXIv` 下运行，是本轮实际跑过的；当日退出码与结果见 [validation-report.json](validation-report.json)。

```
.venv/bin/python -B "schema v0.1/Review Agent/check_interfaces.py" --kind backtranslate \
  --input "schema v0.1/Review Agent/conformance/backtranslate-draft.json" \
  --task  "schema v0.1/Review Agent/conformance/task-backtranslate.json"

.venv/bin/python -B "schema v0.1/Review Agent/check_interfaces.py" --kind backtranslate \
  --input "schema v0.1/Review Agent/conformance/backtranslate-draft.json" \
  --task  "schema v0.1/Review Agent/conformance/task-backtranslate-leak.json"

.venv/bin/python -B -m pytest "schema v0.1/Review Agent/tests" -q -p no:cacheprovider

.venv/bin/python -B "schema v0.1/tests/run_agent_tests.py"
```

退出码含义：`0` 本次检查的各层都通过；`1` 至少一条规则被违反，`errors` 给出错误码与路径；`2` 输入或检查器装载失败，检查**未完成**。退出码 0 只表示上面第 1 层通过，不表示审阅成立，也不表示被审对象正确。

`--require-task` 把"没有固定 Task"从 `unchecked` 升级为 `TASK_REQUIRED` 错误。每次输出都带 `unchecked` 映射，逐项写明本次没有检查什么；把它连同错误一起读。
