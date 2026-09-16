# 运行接口与交付约定

本文件是 [AGENT.md](AGENT.md) 的规范性附件，规定 `dependency.search` 的输入边界、模型草稿形状、宿主与模型分工、分轮登记与每轮运行目录约定。判定优先级与编号正反例见 [CONFORMANCE.md](CONFORMANCE.md)；共同交接字段、通用上下文许可与独立性最低线见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md)；共享不变量 I1–I6 见 [Autoformalization Agent/AGENT.md](<../Autoformalization Agent/AGENT.md>)；调度触发、并行与预算见 [SCHEDULING.md](../SCHEDULING.md)。

## 1. 本模块的操作

| operation | execution_kind | 最小输入 | 输出草稿 | 明确不负责 |
|---|---|---|---|---|
| `dependency.search` | HYBRID | `input_refs` 至少含 `source-snapshot` / `scientific-claim` / `math-claim` 之一（由 `validate.py` 的 Task 检查强制）；复用检索另需精确目标用途及其条件；本次 Task 的 brief 须交代搜索范围与停止规则 | [search-draft.schema.json](search-draft.schema.json) | 取字节、批准复用、产出 `reuse-decision` / `relation-assessment`、维护数据库或图的权威边、判定全球首次、把引用书目直接变成 MathClaim |

- 类型白名单以 [agents.json](../agents.json) 为准：`input_record_types` 25 项、`output_record_types` 三项（`baseline-snapshot`、`dependency-binding`、`frontier-item`）、`capabilities` 三项（`records.read`、`dependency.search`、`candidates.propose`）。本表不抄写这三份列表。
- 白名单是**直接输入**白名单。`authority-policy`、`processing-profile`、`agentization-plan` 三种通用上下文另由 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2 许可进入，不出现在 `input_record_types` 里，也不因此成为必需输入。
- `execution_kind = HYBRID` 只表达预期执行方式，不是网络访问授权，也不表示部署已存在。`capabilities` 中没有任何取字节能力；实际检索由受限服务执行，模型不继承服务账户或凭据（[AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §1）。
- `impact-analysis` 在输入白名单内，但当前 agents.json 中没有任何 operation 产出它。把它写成必需输入等于永久阻塞任务；实现边界见 [validation-report.json](validation-report.json)。
- `dependency` 不在 `validate.py` 的独立身份集合内，Task 的 `exclusions` 因此可以为空数组。这只说明本操作不是独立审阅岗位，不表示本模块可以审阅或批准自己的候选（I1）。

## 2. 模型返回形状

一次调用只返回一个原始 JSON 对象：不加 Markdown 代码围栏、额外顶层字段或字段别名。无内容的列表用 `[]`，仅 schema 允许为空的引用用 `null`。空形状：

```json
{"draft_version": "1.0", "search_requests": [], "records": [], "open_items": [], "follow_up_requests": []}
```

| 草稿 | schema | draft_version | 谁生成 | 要点 |
|---|---|---|---|---|
| 检索草稿 | [search-draft.schema.json](search-draft.schema.json) | `1.0` | `dependency.search` | 五个根字段固定；`records` 项只含 `record_type` 与 `payload`，payload 直接 `$ref` 对应 v0.0 业务 schema 的 `#/properties/payload`，不复制其字段 |

逐字段规则：

| 字段 | 规则 | 不表示什么 |
|---|---|---|
| `search_requests[].target_ref` | 针对已有 claim 的检索必须绑定所选目标；仅来源级检索时才可 `null` 并在 `open_items` 说明理由 | `null` 不表示"对全部目标有效" |
| `search_requests[].query` | 非空字符串；同一 `(target_ref, query.strip())` 只能出现一次 | 不是检索回执，不表示该查询执行过 |
| `search_requests[].sources` | 本次允许的来源范围，字符串数组 | 不是已访问来源列表 |
| `records` | 只允许三类输出，且必须属于本 Task 的 `expected_record_types` | 通过 schema 不表示候选数学有效 |
| `baseline-snapshot.limitations` | v0.0 强制 `minItems: 1`；`knowledge_ref` 可为 `null` | `null` 只表示"没有可用的既有知识快照"，不表示检索已完整 |
| `dependency-binding.comparison` | v0.0 强制 `minItems: 1`；两端引用必须是已存在记录 | 声明了比较不表示比较成立 |
| `dependency-binding.reuse_decision_ref` | 生产时通常为 `null`；填非 `null` 需要一条已存在的 `reuse-decision` | `null` 不表示已获准复用，非 `null` 也不由本模块判定适用（授权归 `review.reuse`） |
| `dependency-binding.proof_plan_ref` | 只在证明路线已存在时填写 | 不编造路线；候选不因此成为已支持的数学前提 |
| `frontier-item` | `state` 为 `RESOLVED` / `SUPERSEDED` 时 `resolution_refs` 非空 | 记录缺口不等于缺口已被处理 |
| `open_items` | 固定文本顺序 `target=…; missing=…; checked=…; next=…`（[AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2.2 第 6 条）；`checked` 只列实际已读或已执行的事项 | 空数组只表示确实没有缺口 |
| `follow_up_requests` | 四字段 `agent, operation, input_refs, reason`；`reason` 用 `target=…; need=…; purpose=…` | 提出建议不是获得授权，不含 task_id、预算或 capabilities |

草稿中不得出现 `record_id`、`revision`、`created_at`、`data_class`、`schema_bundle_hash`、`producer`、`policy_ref`、`input_refs`、`content_hash`，也不得新增 `retrieval_success`、`executed_at` 一类执行回执字段；schema 的 `additionalProperties: false` 会直接拒绝。

`records` 为空是合法交付：只提检索建议或只报缺口时使用。`search_requests`、`records` 与非空白 `open_items` 三者全空则不是交付。

## 3. 宿主与模型各写什么

| 内容 | 所有者 | 约束 |
|---|---|---|
| 检索目标、查询串、来源范围、比较维度、缺口陈述 | 模型 | 按本文件与 CONFORMANCE 填写；不得为匹配上游而修改目标 |
| 编号、修订、时间、哈希、`data_class`、`schema_bundle_hash`、`producer`、`policy_ref`、`input_refs`、`content_hash` | 宿主 | 来自真实输入与执行；模型不得虚构（I2） |
| 实际检索执行：查询时间、来源返回内容、URL、失败与原始字节 | 受限检索服务 + 宿主 | 另存运行附件；草稿内没有"已检索"字段 |
| 知识库与图的读写、批次与回执 | 宿主受控服务 | 见 [GRAPH-INTERFACE.md](../GRAPH-INTERFACE.md)；模型不持有 Cypher 或数据库凭据 |
| 复用许可、关系评估、用途判定 | `review.reuse` | 本模块只提候选（I1）；候选绑定的 `reuse_decision_ref` 为 `null` 时就是候选 |
| Result、`outcome`、`output_refs` | 宿主 | 草稿不是 Result；交付齐全不等于科学成立（[AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2.1） |

装配不得修改 `comparison`、`limitations` 或缺口陈述来使校验通过；需要修订时保留旧版本、创建新记录版本。

## 4. 分轮登记与引用

- 草稿中的每个 RecordRef 必须是本次 `Task.input_refs` 的精确成员；同一草稿内的记录尚无正式身份，不能互相引用，`follow_up_requests` 也不能引用其未来身份。
- `dependency-binding` 两端都必须已存在。上游尚未取得时只写 `open_items` 与 `frontier-item`，不造替身引用：先 `utility.capture` 取得来源、再 `paper.extract` 得到上游 MathClaim，宿主保存后以真实引用创建下一轮 Task。
- 用途决定要绑定到依赖时，创建新的 Dependency 任务与新的记录版本，不回写旧候选。
- 库内关系检索按 [GRAPH-INTERFACE.md](../GRAPH-INTERFACE.md)：模型先提需求，host 在任务之间执行固定批次查询并回源核验，再以真实引用创建下一轮 Task；新结果不塞进当前运行任务。
- 每轮使用新的固定 Task，保留真实可见输入与预算消耗。检索深度、文献数与范围由父计划固定，子任务不重新获得额度（[SCHEDULING.md](../SCHEDULING.md) §5）。

## 5. 每轮文件约定

新运行统一使用下表名称；这些是运行附件，不新增业务类型。所有路径相对于独立的运行目录。

| 路径 | 内容 |
|---|---|
| `task.json` | 当轮实际固定工作单；仅在确实存在时保存 |
| `draft.json` | 本轮原始模型 JSON；无效原始输出另存 `diagnostics/` |
| `records.json` | 已装配业务记录数组；不混入 Task、Result、manifest 或被拒绝的草稿 |
| `result.json` | 真实执行产生的 Result；没有足够运行事实时不造回执 |
| `retrieval/` | 受限检索服务的真实执行附件：查询、时间、返回内容、URL 与失败；属于附件，不是业务记录 |
| `validation.json` | 分层检查报告：草稿、Task 限制、引用、单条记录、完整记录集分别报告 |
| `manifest.json` | 宿主运行索引；固定字段见下 |
| `diagnostics/` | 被拒草稿、校验错误与待迁移问题；不是正式业务输出的替代通道 |

`manifest.json` 固定字段：`manifest_version`（`dependency-agent/1.0`）、`run_id`、`mode`（`EXECUTED` 或 `OFFLINE_DIAGNOSTIC`）、`source_refs`、`spec_files`（`{path, sha256}`）、`schema_bundle_hash`、`model`（`{provider, model_id, settings}`，取不到写 `null`）、`files`（`{path, sha256, byte_size}`，不含自身）、`record_counts`（从 `records.json` 按完整 `record_type` 计算，不手填）。

## 6. 兼容边界

- 草稿 schema 的 `draft_version` 为 `1.0`，与 AGENT.md 的 `draft-version` 一致；本文件不改变字段级接口，只把运行约定集中到一处。
- 已知不一致：本目录 `$id` 使用 `dependency-agent/1.0/`（与 Paper Agent 同形），`Autoformalization Agent` 的草稿 `$id` 使用 `autoformalization/1.0/`（无 `-agent`）。URI 只是身份，不联网解析。
- `check_interfaces.py` 的 `--fail-on-warning` 目前不可能改变退出码：本检查器从不向 `warnings` 追加内容。
- 检索适配器、共享装配器、manifest 写入器、图查询批次执行与独立 `review.reuse` 服务尚未实现；本文件是实现契约，不是这些服务已存在的声明。逐条边界见 [validation-report.json](validation-report.json)，后续待测项登记在 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 D-* 与 X-* 项。
- 形式依赖另有一道准入边界：进入 release-candidate 交付物的形式依赖必须出现在 [Autoformalization Agent/registry/trusted-packages.json](<../Autoformalization Agent/registry/trusted-packages.json>) 中。该注册表的条目、状态与政策由该目录拥有，本文件不复述其内容，也不在本模块检查器中执行。

现有 Task/Result 与权限规范、调度规则、业务 schema 继续有效；本文件不改变它们的字段或信任门槛，冲突必须报告。
