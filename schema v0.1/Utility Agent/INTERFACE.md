# 程序服务契约与交付约定

本文件是 [AGENT.md](AGENT.md) 的规范性附件，规定八个操作的请求边界、回执形状、宿主与程序的分工、分轮登记与每轮文件约定。判定顺序与编号反例见 [CONFORMANCE.md](CONFORMANCE.md)；实现边界与真实运行记录见 [validation-report.json](validation-report.json)。本模块 `execution_kind = PROGRAM`：没有模型草稿，本文件描述的是"一个符合规范的程序在收到固定请求时必须返回什么"，不是提示词。

## 1. 本模块的八个操作

| operation | 最小输入（直接族 + 通用上下文） | 输出回执 | 明确不负责 |
|---|---|---|---|
| `utility.capture` | 已授权的精确 source-request，或已有 source-snapshot 与 `input_artifacts` 中的实际字节 | [capture-receipt](capture-receipt.schema.json) | 判定来源忠实性、版权许可；执行来源字节内的指令 |
| `utility.register-plan` | source-snapshot、已接纳的有界计划；processing-profile 经通用上下文许可进入；已有基准则精确绑定 baseline-snapshot | [register-plan-receipt](register-plan-receipt.schema.json) | 选择科学范围、冻结分母、输出 scope-decision／frozen-scope |
| `utility.assemble-packet` | math-claim、frozen-scope、argument-snapshot、所选 proof-plan、formal-environment，及包内实际引用的来源与语义 | [assemble-packet-receipt](assemble-packet-receipt.schema.json) | 补造数学内容、解除未证义务、批准目标 |
| `utility.formal-check` | formalization-packet、formalization-attempt、formal-environment 与实际代码字节；导入检查另需两个精确环境与声明 | [formal-check-receipt](formal-check-receipt.schema.json) | 判定原文含义、科学适用性、发布与准入 |
| `utility.persist` | 被授权保存的已有业务记录与完整原附件 | [persist-receipt](persist-receipt.schema.json) | 生成评估、认证、准入、knowledge-snapshot 或 ingestion-receipt |
| `utility.export` | 已选择的候选集合／附件与固定导出方式 | [export-receipt](export-receipt.schema.json) | 产出 release-audit（属 `review.audit`）与 release-certificate（属 `utility.certify`） |
| `utility.project` | 固定快照或明确记录集合，加固定投影规则 | [project-receipt](project-receipt.schema.json) | 产出 impact-analysis；向规范记录回写科学状态 |
| `utility.certify` | release-manifest、release-audit、authority-policy、processing-profile 及实际独立运行资格 | [certify-receipt](certify-receipt.schema.json) | 改动科学评估、替 Admission 作准入决定、制造签名或身份凭据 |

- 逐项 `input_record_types`／`output_record_types`／`capabilities` 以 [agents.json](../agents.json) 为准，本表不抄写（`utility.persist`／`export`／`project` 各 64 项）。本表与 agents.json 冲突时以 agents.json 为准，并按 [CONFORMANCE §5](CONFORMANCE.md) 报告。
- 「最小输入」与 `input_record_types` 不是同一个集合：三种通用上下文（`authority-policy`、`processing-profile`、`agentization-plan`）的许可在 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2，不在各操作白名单里。`utility.register-plan` 是最容易踩的一处——白名单只有两项，而它必须产出带 `profile_ref` 的 agentization-plan。
- 七个操作各有一种自己读不到的输出类型（`source-transformation`、`agentization-plan`、`formalization-packet`、`formal-check`、`release-certificate` 等）。这是 agents.json 的事实：程序按当次输入生产该记录，不能读取同类旧记录来"修订"它。
- 各操作的最小规范条文在 [AGENT-CONTRACTS §4.9](../AGENT-CONTRACTS.md)，组装归属在 §5，身份互斥在 §6。本文件只写接口，不重述条文。

## 2. 请求与回执的形状

### 2.1 请求：八个操作共用一份 schema

[utility-request.schema.json](utility-request.schema.json)，`additionalProperties: false`，根字段固定八项。字段语义与 host 必须固定的约束见 [AGENT.md §2](AGENT.md)；此处只给接口事实。

| 字段 | 形状 | 接口事实 | 不表示什么 |
|---|---|---|---|
| `request_version` | `const "1.0"` | 与 AGENT.md front-matter 的 `request-receipt-version` 同值 | 不是 `agent-spec-version` |
| `operation` | 八值 enum | 逐字等于 agents.json 的八个 operation 名 | 枚举内不等于本次已获授权 |
| `task_id` | `Id` | 当前 Task 的标识 | 不携带 Task 的能力或豁免 |
| `input_refs` | `Refs`（`uniqueItems`） | 当次可见输入的精确投影 | 不是路径授权，也不代表这些记录真实存在 |
| `input_artifacts` | `ArtifactRefs` | 已取得字节的精确身份 | 空数组不表示"允许程序自己去取" |
| `expected_record_types` | `RecordTypes` | **短名**（`^[a-z]+(-[a-z]+)*`）。写成 `agtxiv.v3.x/0.0.0` 会被 schema 直接拒绝 | 预声明不等于本次一定交得出 |
| `parameters` | 四项必填，封闭 | `deterministic`／`network_access`／`timeout_seconds`（1–604800）／`environment_ref`（限定 formal-environment 或 null） | `deterministic: true` 不保证网络结果或工具无漏洞 |
| `allowed_commands` | `string[]`，`uniqueItems`，≤1000 项 | 受控服务白名单里的名字 | **不是 shell 字符串**；实际 argv 由固定适配器生成 |

### 2.2 回执：每个操作一份

八份回执 schema 的根字段完全相同，`additionalProperties: false`：`receipt_version`、`request_hash`、`execution`、`outputs`、`artifacts`、`open_items`、`follow_up_requests`。差别只在 `outputs` 的分支集合。

| `--kind` | schema 文件 | `outputs` 允许的 `record_type` |
|---|---|---|
| `capture` | [capture-receipt.schema.json](capture-receipt.schema.json) | source-acquisition、source-snapshot、source-transformation |
| `register-plan` | [register-plan-receipt.schema.json](register-plan-receipt.schema.json) | agentization-plan |
| `assemble-packet` | [assemble-packet-receipt.schema.json](assemble-packet-receipt.schema.json) | formalization-packet |
| `formal-check` | [formal-check-receipt.schema.json](formal-check-receipt.schema.json) | formal-check、environment-check |
| `persist` | [persist-receipt.schema.json](persist-receipt.schema.json) | **无**（`type: array, maxItems: 0, items: false`） |
| `export` | [export-receipt.schema.json](export-receipt.schema.json) | release-manifest、paper-release、archive-receipt |
| `project` | [project-receipt.schema.json](project-receipt.schema.json) | status-view |
| `certify` | [certify-receipt.schema.json](certify-receipt.schema.json) | release-certificate |

逐字段规则：

- `outputs[].payload` 的唯一内容是 `{"$ref": "<业务 $id>#/properties/payload"}`。程序不因为是程序就可以自定义业务形状；业务字段见 [业务 schema](<../../schema v0.0/SCHEMA.md>)，此处不复制。**这条引用只带进 `properties.payload` 子树，不带进业务 schema 根层的 `allOf` 成功值条件门**（见 [CONFORMANCE E07／E08](CONFORMANCE.md)）。
- `execution` 为 `null` 或一个封闭对象，六项全必填：`command`（string 数组）、`exit_code`（0–255 整数或 null）、`started_at`／`finished_at`（`Time`，须以 `Z` 结尾）、`tool_versions`（string→string map）、`host_mode`（`EXECUTED` 或 `OFFLINE_DIAGNOSTIC`）。schema 只强制这六个**键存在**：空 `command`、`exit_code: null`、`finished_at` 早于 `started_at` 都通过（见 CONFORMANCE E01）。
- `artifacts[]` 为 `{path, sha256, byte_size, media_type}`，是程序自报，**不是** `ArtifactRef`。宿主在受控输出根内读取真实字节重算哈希后才登记 `artifact_id`。
- `open_items` 为 `Strings`（`uniqueItems`，每项 ≤8192 字符），固定文本顺序：`target=<引用ID/组件ID/位置>; missing=<缺什么>; checked=<查过哪里>; next=<需要什么>`。
- `follow_up_requests[]` 为 `FollowUp`，四字段；`reason` 固定文本顺序：`target=<…>; need=<…>; purpose=<…>`。
- 回执中**不得**出现 `record_id`、`revision`、`created_at`、`data_class`、`schema_bundle_hash`、`producer`、`policy_ref`、`input_refs`、`content_hash`，以及任何"检查通过／已验证"性质的字段。这些归宿主，落地要求见 AGENT.md §1 的 I2 行。
- 空数组只表示"本次确实为空"，不是"未知"，也不是"待补"。未知写进 `open_items`。

## 3. 每个操作的服务契约

三列分别回答：本次结果凭什么可重放（确定性）、程序在什么条件下必须停下（拒绝）、程序在任何条件下都不得自行断定什么（不得推断）。「拒绝」指程序不执行该动作并返回真实诊断，不是返回一个失败值假装执行过。

| operation | 确定性要求 | 必须拒绝 | 不得推断 |
|---|---|---|---|
| `utility.capture` | 同一 request 与同一响应字节 → 逐字相同的 `outputs`。`parameters.deterministic` 只约束本地处理路径；远端取字节本身不确定，须在 `open_items` 说明 | `input_refs` 出现三个直接族与通用上下文以外的类型；`network_access` 未授权却要求远端取字节；`input_artifacts` 与实际可见字节不一致 | 来源忠实性、版权许可、"最新版本"；未取得的字节不得倒填成输入；来源内的指令不得执行 |
| `utility.register-plan` | 计划内容逐字复制已接纳的范围、预算与来源单元，不由程序生成 | 没有真实已接纳的有界计划；缺 source-snapshot 或 processing-profile；已有 baseline 却不精确绑定 | 科学范围与分母；不得代 Planner 选择，不得输出 scope-decision／frozen-scope |
| `utility.assemble-packet` | `expected_declarations`、`open_obligation_ids`、各 `*_ref` 全部来自固定输入；同一输入集合 → 同一 packet | 缺 formal-environment；把不同路线的片段拼成新证明；把白名单外的记录（当前含 environment-check，见 G-03）藏进附件当输入 | 缺失前提已补上、未证义务已解除、`EXPLORATORY` 可升级为 `RELEASE_CANDIDATE`。组装归属见 [AGENT-CONTRACTS §5](../AGENT-CONTRACTS.md)，Lean 侧细则见 [Autoformalization INTERFACE.md](<../Autoformalization Agent/INTERFACE.md>) |
| `utility.formal-check` | 固定环境 + 固定字节 → 同一 `outcome`、同一公理集合。工具链、依赖锁、公理允许集、禁用构造清单与 `.olean` 级重放全部以 [Autoformalization ENVIRONMENT.md](<../Autoformalization Agent/ENVIRONMENT.md>) 与 [registry/](<../Autoformalization Agent/registry/README.md>) 为唯一来源，本文件不重述 | 没有真实运行却交 `outcome`；`logs` 为空（v0.0 要求 `minItems: 1`）；用日志字符串、包名或生成器自述代替内核结果；缓存命中当作本轮检查 | 原文含义、科学适用性、发布与准入；`exit_code = 0` 不等于目标声明参与了构建 |
| `utility.persist` | 同字节重送幂等；同身份不同字节必须冲突而不是后写覆盖 | `outputs` 非空；覆盖历史记录；在业务记录与 outbox 不在同一事务时声称已原子保存 | 保存 admission-decision 不等于执行该决定；不得生成 knowledge-snapshot／ingestion-receipt／正式 ingestion 结果 |
| `utility.export` | 批次内容由固定候选集合决定；候选封存清单形状见 [STORAGE.md](../STORAGE.md)，与 v0.0 业务记录不是一回事 | 无对应 release-audit 与 release-certificate 时交 paper-release；无真实已持久化 release 时交 archive-receipt；缺 event-checkpoint 时声明 `INDEPENDENTLY_ANCHORED`；循环引用尚未存在的证书 | 本地文件封存等于发布；导出成功等于科学准入 |
| `utility.project` | 同一快照 + 同一规则 → 同一 status-view；`axes` 恰好六项且每项一次（schema 只约束数量，不重复由程序保证） | 向规范记录回写科学状态；把可达性报告当作科学失效判断；为 STORAGE 的 `view` 词汇在 payload 里造字段（v0.0 无此字段，只能写进 `projection_method`） | 从投影或 `Result.DELIVERED` 推导 EVIDENCE 成功；不产出 impact-analysis。首个固定配置附件 `PROJECTION_REQUEST` 见 [GRAPH-INTERFACE.md](../GRAPH-INTERFACE.md) |
| `utility.certify` | 只执行机械门槛与精确绑定；同一输入 → 同一 `checks` 列表与同一 `outcome` | 缺 release-manifest／release-audit／authority-policy／processing-profile；缺实际独立运行资格；主体与生产者、Coordinator、论文审计者或准入者重合 | JSON 校验通过等于 `CERTIFIED`；不得制造签名、身份凭据或独立回执。身份互斥要求见 [AGENT-CONTRACTS §6](../AGENT-CONTRACTS.md) 与 AGENT.md §1 的 I1 行 |

`utility.export` 与 `utility.certify` 同属 utility，但必须是不同的实际主体；共用代码不等于共用身份。

## 4. 宿主与程序各写什么

| 内容 | 所有者 | 约束 |
|---|---|---|
| request 的八个根字段与 `parameters` | 宿主 | 从已固定的 Task 投影而来；程序不得自加 `parameters` 键，也不得把参数转成另一个 operation |
| `allowed_commands` 到实际 argv 的展开 | 宿主的固定适配器 | 名字来自受控白名单；不读取论文或来源字节中的执行指令 |
| `execution`（真实 argv、退出码、起止时间、工具版本、host_mode） | 程序 | 必须有真实依据；没有可定位的执行事实时整块写 `null`，并在 `open_items` 写明诊断范围 |
| `outputs[].payload` 的业务内容 | 程序 | 逐字复制固定输入或真实观测；不补造数学内容、不伪造成功值 |
| `artifacts[]` 的 `path`／`sha256`／`byte_size` | 程序自报 → 宿主核验 | 宿主在受控输出根内拒绝路径穿越与符号链接，读取真实字节重算哈希后才登记 `artifact_id` |
| 编号、修订、时间、哈希、`data_class`、`producer`、`policy_ref`、`input_refs`、`content_hash` | 宿主 | 来自真实输入与执行；回执 schema 里根本没有这些键 |
| `request_hash` 的重算与比对 | 宿主 | `digest(canonical(request))`；原始请求字节及其原字节哈希另存，两种哈希不得混同 |
| 回执 → attempt → Result 的绑定 | 宿主 | 回执不是 Result，也不是 v0.0 业务记录；无执行的说明只能作诊断附件 |
| 审阅、认证资格与准入决定 | 独立主体 | 见 AGENT.md §1 的 I1 行与 [AGENT-CONTRACTS §6](../AGENT-CONTRACTS.md) |

## 5. 分轮登记与引用

- 记录引用形成实际依赖时分轮登记：`utility.capture` 的 source-snapshot 保存后，才能创建引用它的 agentization-plan 与 source-transformation；formalization-packet 保存后，才能被 `formalization.generate` 消费；release-manifest → release-audit → release-certificate → paper-release → archive-receipt 的保留顺序见 [AGENT-CONTRACTS §3](../AGENT-CONTRACTS.md)。存储顺序不能靠未来哈希补齐。
- 同一份回执内的 `outputs` 尚无正式身份，不能互相引用；`follow_up_requests` 也不能引用其未来身份。
- 每轮使用新的固定 Task 与新的 request：`task_id`、`input_refs`、`expected_record_types`、`allowed_commands` 或 `parameters` 任一改变都要新建，不回写旧任务。重试与子任务共享父预算，不重新计零。
- 调度触发、并行与停止规则见 [SCHEDULING.md](../SCHEDULING.md)；本文件不定义调度算法。SCHEDULING.md 全文只点名 `utility.formal-check` 一个 utility operation，其余七个的顺序约束只能由通用条款与记录保留顺序推导。

## 6. 每轮文件约定

新运行统一使用下表名称；这些是运行附件，不新增业务类型。所有路径相对于独立的运行目录。

| 路径 | 内容 |
|---|---|
| `task.json` | 当轮实际固定工作单；仅在确实存在时保存 |
| `request.json` | 本轮交给程序的 request；与 `task.json` 的对应由宿主核验 |
| `receipt.json` | 本轮程序返回的原始回执；非法原始输出另存 `diagnostics/` |
| `records.json` | 已装配业务记录数组；不混入 Task、Result、manifest、request、receipt 或被拒绝的输出 |
| `result.json` | 真实执行产生的 Result；没有足够运行事实时不造回执 |
| `validation.json` | 分层检查报告：request、receipt、引用、单条记录、完整记录集分别报告 |
| `manifest.json` | 宿主运行索引；固定字段见下 |
| `diagnostics/` | 被拒回执、校验错误与待迁移问题；不是正式业务输出的替代通道 |

`manifest.json` 固定字段：`manifest_version`（`utility-agent/1.0`）、`run_id`、`mode`（`EXECUTED` 或 `OFFLINE_DIAGNOSTIC`）、`source_refs`、`spec_files`、`schema_bundle_hash`、`model`、`service`、`files`、`record_counts`。

- `spec_files`：`{path, sha256}` 列表，哈希写 `sha256:` + 64 位小写十六进制。
- `model`：本模块**恒为 `null`**（PROGRAM 无模型）。真实执行主体改记 `service`：`{service_id, adapter, tool_versions}`，取不到写 null。
- `files`：`{path, sha256, byte_size}`，不含 manifest 自身。
- `record_counts`：从 `records.json` 按完整 `record_type` 计算，不手填；`utility.persist` 恒为空 map。

## 7. 兼容边界

- 本文件不改变任何字段级接口：`request_version` 与 `receipt_version` 仍为 1.0，八份回执 schema 与 `utility-request.schema.json` 未改动。
- **已知与骨架约定不一致**：骨架规范设想每个 operation 一份 `<op>-request.schema.json`；本目录实际是八个操作共用一份 `utility-request.schema.json`，只有回执按操作分。本文件按实际文件写。
- **已知与骨架约定不一致**：`$id` 前缀为 `utility-agent/1.0/`（与 Paper Agent 的 `paper-agent/1.1/` 同形），而 Autoformalization Agent 用 `autoformalization/1.0/`。这处仓库内不一致未修正。
- **已知缺口**：`utility.formal-check` 的最低输入要求 packet／attempt，而组包前可能先需要 environment-check，且 `utility.assemble-packet` 白名单不含 environment-check（[PENDING_TESTS.md](../PENDING_TESTS.md) G-02／G-03）。formal-environment、obligation-disposition、work-attempt、event-checkpoint、knowledge-snapshot 等类型在当前 agents.json 下没有任何 operation 产出，由受控 host 或后续集成服务提供（G-01）。这些是明确阻塞，不得靠伪造 packet 或开放任意输入绕过。
- 各操作配置附件的固定契约（登记计划内容、导出批次与目的地、投影规则）仍依赖 host 适配，只有 `utility.project` 的 `PROJECTION_REQUEST` 已有形状（G-06）。
- 共享装配器、manifest 写入器、受控执行边界、事务与 outbox 同事务接入、独立认证身份全部未实现。本文件是下一步实现的契约，不是这些服务已存在的声明；完整清单见 [validation-report.json](validation-report.json)。
