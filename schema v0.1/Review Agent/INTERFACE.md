# 运行接口与交付约定

本文件是 [AGENT.md](AGENT.md) 的规范性附件，规定八个 `review.*` 操作的调用边界、草稿形状、宿主与模型的分工、分轮登记与返工通道。职责与开始条件见 AGENT.md §3，不在此重复；判定顺序与正反例见 [CONFORMANCE.md](CONFORMANCE.md)；Paper → Proof → Lean 这条流水线的轮次编号与退回层见 [REVIEW.md](<../Autoformalization Agent/REVIEW.md>)。

## 1. 本模块的八个操作

operation 名、输入／输出白名单与 capabilities 以 [agents.json](../agents.json) 为准；触发条件、禁区与身份底线以 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §4.5 为准。下表只写这两处没有的两件事：**代码当前已强制的最小输入**，以及**本次调用明确不产出什么**。

| operation | 草稿 schema | `validate.py` 已强制的最小输入与前置 | 本次调用不产出 |
|---|---|---|---|
| `review.scope` | [scope-draft](scope-draft.schema.json) | `inventory-discovery`、`source-snapshot`、`paper-structure`、`agentization-plan`、`processing-profile` 五项同时可见 | Result、obligation-disposition、上游记录的修订 |
| `review.argument` | [argument-draft](argument-draft.schema.json) | `argument-snapshot`、`frozen-scope` | formal-check、alignment-assessment、被审快照的新版本 |
| `review.reuse` | [reuse-draft](reuse-draft.schema.json) | `target_refs` 至少两项；`expected_record_types` 含 `reuse-decision` 时另需 `processing-profile` | environment-check、新定理、目标级 EVIDENCE 通过结论 |
| `review.backtranslate` | [backtranslate-draft](backtranslate-draft.schema.json) | 业务输入恰为 `{formal-environment}`；`input_artifacts` 非空；`acceptance` 恒为 `DELIVERY` | 任何业务记录（草稿 `records` 上限 0 项）、`packet_ref`、`source_blind`、`visibility_evidence` |
| `review.alignment` | [alignment-draft](alignment-draft.schema.json) | `target_refs` 至少两项；`target_refs` 命中 `formalization-packet`／`formalization-attempt`／`formal-check` 时另需可见 `backtranslation` | formal-check、被比较两端的任何修订 |
| `review.scientific` | [scientific-draft](scientific-draft.schema.json) | 无专门的代码级下限；按 AGENT-CONTRACTS §4.5 绑定精确目标与对应轴的证据 | empirical-evidence、reproduction-record、alignment-assessment |
| `review.audit` | [audit-draft](audit-draft.schema.json) | `release-manifest`、`processing-profile` | release-certificate、paper-release、被审计证据的补齐 |
| `review.admission` | [admission-draft](admission-draft.schema.json) | `paper-release`、`knowledge-snapshot`、`authority-policy`、`processing-profile` | challenge、frontier-item（不在其输出白名单内）、knowledge-snapshot、ingestion-receipt、任何数据库事务 |

- `review.audit` 与 `review.admission` 的 `input_record_types` 各为全部 64 类。这表示**可读**，不表示必须全读：本次实际审阅对象仍由 `Task.target_refs` 逐项绑定；未读到的部分只能进 `open_items`，不能按"输入白名单里有"推定已核对。
- `review.scope` 的输入白名单不含 `agentization-plan`，`review.reuse` 的输入白名单不含 `processing-profile`；两者都靠 `authority-policy`／`processing-profile`／`agentization-plan` 这组通用上下文许可进入。`review.backtranslate` 是唯一**不适用**该许可的操作。
- `review.argument` 输出 `axis-assessment`，但 `axis-assessment` 不在它的输入白名单里：它写得出这类记录，读不到既有的同类记录。要读旧轴评估须另起 `review.scientific` 或 `review.alignment` 任务。
- 输出只限 `Task.expected_record_types` 事先声明的部分。白名单里的其它类型也不能临时附带；未预声明的异议只能走 `follow_up_requests` 与 `open_items`。
- 只使用当次 Task 提供的记录与字节。需要新记录时先保存，再创建新 Task；不猜未来引用，不隐式展开未授权输入。

## 2. 模型返回形状与审阅意见的最低内容

一次调用只返回一个原始 JSON 对象：不加 Markdown 代码围栏、额外顶层字段或字段别名。无内容的列表用 `[]`，且 `[]` 只表示"确实没有"，不表示"没检查"——没检查的部分写进 `open_items`。

| 草稿 | 根字段 | 要点 |
|---|---|---|
| 七个评估类草稿（scope、argument、reuse、alignment、scientific、audit、admission） | `draft_version`、`records`、`open_items`、`follow_up_requests` | `records` 项只有 `record_type` 与 `payload` 两个键；`payload` 直接 `$ref` v3/0.0.0 业务 schema 的 `properties/payload`，不复制其字段 |
| [backtranslate-draft](backtranslate-draft.schema.json) | 另加 `interpretation`、`conditions`，且 `records` 恒为 `[]` | 模型只交解释与条件；正式 `backtranslation` 由宿主在解释冻结后装配 |

每条审阅意见——无论落在 `challenge.statement`、`argument-review.conditions`、`axis-assessment.rationale` 还是 `release-audit.findings`——至少说明五项：

1. 精确对象：哪一条记录、哪一步推理、哪一个声明；
2. 违反了哪一条要求；
3. 原文或代码依据；
4. 影响哪一个目标；
5. 需要哪一层处理。

复用既有业务类型承载意见，不创造第二套 review 类型。业务 schema 没有对应字段时，使用现有说明字段与诊断附件，**不临时扩字段**。不得要求生产者公开隐藏思考；需要的是可核对的数学理由与执行证据——"请说明你当时是怎么想的"不是可执行意见，"第 3 步的量词顺序与 MathClaim 不一致，依据是 span X"才是。

否定、未知与不适用都要明确对象、依据与未检查范围，并使用业务类型已有的枚举（`INCONCLUSIVE`、`UNKNOWN`、`NOT_APPLICABLE`、`BLOCK` 等），不发明统一的 `verified`。业务 payload 的必要证据或身份字段还不能真实填写时，交 `open_items` 说明缺口，不用 placeholder 满足形状。

## 3. 宿主与模型各写什么

| 内容 | 所有者 | 约束 |
|---|---|---|
| 审阅判断本身：结论枚举、理由、条件、比较项、异议陈述 | 模型 | 按本文件与 CONFORMANCE.md 填写；每一判断绑定其范围 |
| 编号、修订、时间、哈希、附件引用、`producer`、`policy_ref`、`input_refs`、`content_hash` | 宿主 | 来自真实输入与执行事实（[I1–I6](<../Autoformalization Agent/AGENT.md>) 的 I2）；模型不得虚构 |
| `ReviewContext` 的 `independence`、`producer_principal_ids`、`conflicts` | 宿主核定；模型只能写 `UNESTABLISHED` | 独立性按实际主体与参与生产的主体集合判断，底线见 I1 与 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §6 |
| `backtranslation` 的 `packet_ref`、`source_blind`、`visibility_evidence` | 宿主 | 先冻结模型解释，再按已记录的 `depends_on` 工作链固定逻辑归属；取不到真实可见性材料就不交付声称独立的 backtranslation |
| `backtranslation.formal_artifacts` | 宿主，按**实际可见**附件填写 | 不得用隐藏包的逻辑归属冒充"反译者读过这个包"：`packet_ref` 是归属，不是读取许可 |
| 盲输入的中性化 | 宿主 | 见下段 |
| Result、outcome、批准与证据门 | 宿主与相应独立角色 | 草稿里没有"审阅通过"字段；本模块不产出 Result |

**盲输入的中性化：** 代码注释、文件名或附加说明若泄漏原文答案，宿主应提供**经过记录的中性输入版本**，同时保留原始字节、转换规则、新附件身份与可见性记录，不静默修改数学声明。转换是否保持形式含义要**另外核对**——删掉注释不等于严格盲审。该转换目前没有任何实现，也没有任何检查器覆盖，见 [validation-report.json](validation-report.json)。

装配不得修改审阅结论、条件或比较项来使校验通过。需要修订则保留旧版、创建新审阅；旧的反对意见与未决异议继续保留，不因新版本删除。

## 4. 分轮登记、引用与返工通道

- 记录引用形成实际依赖时分轮登记：`scope-decision` 保存并取得精确引用后，才能以该引用形成 `frozen-scope`；`relation-assessment` 保存后，才能对固定用途形成引用它的 `reuse-decision`。同一草稿内的记录尚无正式身份，不能互相引用。
- 异议的三步分轮保存：Reviewer 提出 `challenge` → 生产者响应并产生新修订 → 独立 Reviewer 形成 `challenge-disposition`。三步不在同一次交付里预造身份。
- `follow_up_requests` 只描述缺什么，不能引用其未来身份；字段形状见 [common.schema.json](../schemas/common.schema.json) 的 `FollowUp`。保存后由调度程序选择实际产物创建新 Task，不靠"取最新记录"解决歧义。
- 返工通道：通过允许的 `challenge`／`frontier-item` 明确指出问题，必要的原始错误日志作为固定附件；**不得把完整业务检查记录藏进附件绕过输入白名单**。下游生产操作读不到某类正式记录时，正确做法是把问题缩减成可执行意见，不是换一个容器把同一份记录递过去。
- 所有未解决的问题保留在新快照与相应处置中；`frontier-item` 置为 `RESOLVED` 或 `SUPERSEDED` 必须给出精确的 `resolution_refs`。
- 每轮使用新的固定 Task，保留真实可见输入与预算消耗；输入新增、目标变化或重试规则变化要新建 Task，不回写旧任务。预算、无进展与停止规则见 [SCHEDULING.md](../SCHEDULING.md)。

## 5. 每轮文件约定

新运行统一使用下表名称；这些是运行附件，不新增业务类型。所有路径相对于独立的运行目录。

| 路径 | 内容 |
|---|---|
| `task.json` | 当轮实际固定工作单；仅在确实存在时保存 |
| `draft.json` | 本轮原始模型 JSON；无效原始输出另存 `diagnostics/` |
| `records.json` | 已装配业务记录数组；不混入 Task、Result、manifest 或被拒绝的草稿 |
| `result.json` | 真实执行产生的 Result；没有足够运行事实时不造回执 |
| `validation.json` | 分层检查报告：草稿、Task 限制、引用、单条记录、完整记录集分别报告 |
| `manifest.json` | 宿主运行索引；固定字段见下 |
| `diagnostics/` | 被拒草稿、校验错误与待迁移问题；不是正式业务输出的替代通道 |

`manifest.json` 固定字段：`manifest_version`（`review-agent/1.0`）、`run_id`、`mode`（`EXECUTED` 或 `OFFLINE_DIAGNOSTIC`）、`source_refs`、`spec_files`、`schema_bundle_hash`、`model`、`files`、`record_counts`。`spec_files` 与 `files` 用 `{path, sha256}`，哈希写 `sha256:` 加 64 位小写十六进制；`record_counts` 从 `records.json` 按完整 `record_type` 计算，不手填。

盲反译轮另存本轮实际提供的形式字节及其身份；若使用了中性化版本，原始字节、转换规则与新附件身份一并保存在同一运行目录，否则该轮不具备可核对的隔离记录。

## 6. 兼容边界与结论失效

- 审阅结论绑定**精确引用与字节**。输入的版本、环境或适用政策一变，结论不自动跟随；旧批准不得覆盖成"针对最新版本"（见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §5）。没有已实现的证据复用规则时，不自行跳过重审。各流水线的具体重做清单由各自模块给出，例如 [REVIEW.md](<../Autoformalization Agent/REVIEW.md>) §4。
- 草稿 schema 为 `draft_version` 1.0，八份按 operation 分开。本文件不改变字段级接口，也不新增业务类型：v0.0 是 64 类闭合集合，草稿只 `$ref` 其 `properties/payload`。
- [check_interfaces.py](check_interfaces.py) 只做只读的草稿层与 Task 层检查。它不解析审阅含义、不认定独立性、不展开 RecordSet、不产生 Result。草稿合法不等于审阅成立，更不等于被审对象正确；每次输出的 `unchecked` 映射逐项自报盲点。
- 与 `agents.json` 的已知张力：`review.admission` 的必需输入 `knowledge-snapshot` 在当前 `agents.json` 下**没有任何 operation 产出**，而 `admission-decision.before_ref` 又必填该类型。该任务目前无法由本包内的 agent 自足地满足输入，记在 [validation-report.json](validation-report.json)。
- 完整宿主装配器、身份认证、审阅者资格认证与各证据门实现尚不存在。本文件是实现契约，不是这些服务已存在的声明。待验证与前置缺口统一见 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 R-\*、G-\*、X-\*。
