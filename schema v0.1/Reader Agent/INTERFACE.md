# 运行接口与交付约定

本文件是 [AGENT.md](AGENT.md) 的规范性附件，规定 `reader.explain` 的输入边界、草稿形状、宿主与模型分工、分轮引用规则与每轮运行目录。判定顺序与编号反例见 [CONFORMANCE.md](CONFORMANCE.md)，字段级裁决以 [explanation-draft.schema.json](explanation-draft.schema.json) 与 [check_interfaces.py](check_interfaces.py) 为准，实现边界见 [validation-report.json](validation-report.json)。

## 1. 本模块的操作

| 操作 | 最小输入 | 输出草稿 | 明确不负责 |
|---|---|---|---|
| `reader.explain` | 非空 `brief`；解释具体业务对象时，`target_refs` 取 `input_refs` 的子集并提供据以解释的记录；既有说明固定在 `input_artifacts` | explanation-draft（`records` 恒为 `[]`） | 创建或改写任何业务记录；批准科学结论或解除 EVIDENCE 门；自行判定本次解释是否独立；派单或执行下游 Task；直接查询图数据库 |

- 类型白名单以 [agents.json](../agents.json) 为准。`reader.explain` 的 `input_record_types` 是 64 项，与 [业务 schema](<../../schema v0.0/SCHEMA.md>) 的全部短名逐项相同；`output_record_types` 是**空数组**；`capabilities` 上限是 `records.read` 与 `reader.explain`。此处不抄这三张表，抄了必然漂移。
- 空的 `output_record_types` 是接口事实，不是"尚未定义"。它使 `Task.expected_record_types` 与 `Result.output_refs` 中的业务记录都必须为空；交付物只有解释附件、`open_items` 与 `follow_up_requests`。
- 64 项输入白名单不是读取许可。实际可见内容仍由当次 Task 的 `input_refs`、能力与独立性约束决定，规则见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2。
- 起步豁免：`input_refs` / `target_refs` 允许为空，由非空 `brief` 承载真实用户意图。该豁免只对 `planner` 与 `reader` 成立（`../validate.py` 的 `Contracts.task`），不是通用规则。`target_refs` 必须是 `input_refs` 的精确子集，因此 `input_refs` 为空时 `target_refs` 也必须为空。
- `reader` 与 `planner` 的输入白名单逐字相同。两者的差别全部在 `capabilities`、`principles` 与交付物形态上，不在能读什么上；不能用"planner 能读"推出"reader 该写"。
- 需要关系上下文时由 host 按 [GRAPH-INTERFACE.md](../GRAPH-INTERFACE.md) 先查询、回源核验，再把结果固定成本轮输入。Reader 只解释 Task 实际提供的记录。
- [SCHEDULING.md](../SCHEDULING.md) 没有为 `reader.explain` 规定门、顺序、预算、重试或并行度；`reader` 在其中只出现在"按需汇总 Delta 与 Reader 输出"一句里。没有被调度规则点名，不表示可以自行启动。

## 2. 模型返回形状

一次调用只返回一个原始 JSON 对象：不加 Markdown 代码围栏、不加顶层字段、不改字段名。空列表用 `[]`，只有 schema 明确允许时才用 `null`。

```json
{
  "draft_version": "1.0",
  "attribution": "",
  "explanations": [
    {"target_ref": null, "audience": "", "text": "", "basis_refs": [], "gaps": []}
  ],
  "records": [],
  "open_items": [],
  "follow_up_requests": [
    {"agent": "", "operation": "", "input_refs": [], "reason": ""}
  ]
}
```

上面是形状示意，不是可交付的示例；每个空串与空数组都必须被真实内容替换，或确实为空。

| 草稿 | schema | 谁生成 | 要点 |
|---|---|---|---|
| 解释草稿 | [explanation-draft.schema.json](explanation-draft.schema.json) | `reader.explain` | `draft_version` const `1.0`；根字段恰好六项且 `additionalProperties: false`；`records` 被收缩成 `maxItems: 0, items: false`，业务记录在结构上放不进去 |

逐字段规则：

| 字段 | 规则 | 不表示什么 |
|---|---|---|
| `attribution` | 枚举只有 `UNESTABLISHED` 与 `SELF_CHECK`。同一主体解释自己的材料写 `SELF_CHECK` | 枚举里没有任何"独立"取值；`UNESTABLISHED` 不表示已确认为独立，`SELF_CHECK` 也不表示宿主已核对过主体身份 |
| `explanations[].target_ref` | 被解释对象的精确 RecordRef；只有尚无业务目标的 brief 说明才可为 `null` | 引用精确不表示该记录真实存在；检查器不回源核对 |
| `explanations[].audience` | 写明面向什么读者、假定了哪些前置知识 | 不表示文本真的与该水平匹配——文本内容不被任何机器读取 |
| `explanations[].text` | 按 [AGENT.md](AGENT.md) §4 的顺序给出实质说明 | 不是业务记录的替代载体；把一条 payload 写成散文仍然是夹带，只是没有机器拦得住（见 [CONFORMANCE.md](CONFORMANCE.md) E05） |
| `explanations[].basis_refs` | 实际读取并据以解释的记录。允许把被解释记录本身列为依据 | 依据非空不表示解释成立；`basis_refs` 为空且 `target_ref` 为 `null` 时必须在 `gaps` 里声明无从落地 |
| `explanations[].gaps` | 该目标尚缺的依据、未检查的范围、读者据此仍无法判断的部分 | 不是 TODO 清单，是交付给读者的边界声明；写得少不表示缺口少 |
| `records` | 恒为 `[]` | 这个字段存在的唯一理由，是让业务记录有一个明确失败的地方 |
| `open_items` | 固定文本顺序 `target=…; missing=…; checked=…; next=…` | — |
| `follow_up_requests` | 四字段 `agent` / `operation` / `input_refs` / `reason`，`reason` 用固定顺序 `target=…; need=…; purpose=…` | 这是 Reader 影响系统的唯一合法通道，也是检查得最严的一处；提请求不等于获得执行 |

`follow_up_requests` 的 schema 只有那四个键且封闭，因此 Reader 在结构上就提不出 `capabilities`、`exclusions`、`limits` 或 `acceptance` 的修改；写进这些键判 `SCHEMA` 失败。

## 3. 宿主与模型各写什么

| 内容 | 所有者 | 约束 |
|---|---|---|
| 解释文本、面向读者的措辞、缺口陈述、后续请求的理由 | 模型 | 只依据本轮实际提供的记录与字节；不得补造来源 |
| `record_id`、`revision`、`created_at`、`content_hash`、`producer`、`policy_ref`、`input_refs` 等封套字段 | 宿主 | 草稿 schema 里没有这些键，模型写入即 `SCHEMA` 失败；理由见 [I1–I6](<../Autoformalization Agent/AGENT.md>) 的 I2 |
| 实际执行归属、可见性，以及"本次解释者是否不同于被解释材料的生产者" | 宿主 | 草稿只能声明 `attribution`，声明不构成事实；本模块检查器不核对（报告的 `unchecked.attribution`） |
| 审阅、异议处置与科学批准 | 独立角色 | 可读性通过不授予科学认可，也不解除任务的证据依赖，见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §2.1、§6 |
| Result 与交付结果 | 宿主 | `Result.output_refs` 的业务记录恒为空；解释以 `Result.artifacts` 交付；`acceptance` 用 `DELIVERY` |

装配不得把解释文本改写成更肯定的版本，也不得删掉 `gaps` 让交付看起来更完整。解释需要修订时保留旧版并新建一轮，不就地覆盖。

## 4. 分轮登记与引用

- 只引用本轮 Task 已固定的记录。给了 Task 时，草稿中每一个精确 RecordRef 都必须是 `Task.input_refs` 的成员，否则判 `INVISIBLE_REF`；不给 Task 时这一层不执行，检查器在 `unchecked.task` 里说明。
- 同一记录身份与修订在一次草稿里只能有一个 `content_hash`。把被解释记录同时列进 `target_ref` 与 `basis_refs` 是正常的，检查器先折叠完全相同的引用，再判 `INCONSISTENT_REF`。
- 每个 `Task.target_refs` 成员都必须是某条 explanation 的 `target_ref`，否则判 `UNEXPLAINED_TARGET`。无法解释的目标仍要绑定它，用 `text` 说明原因、用 `gaps` 列缺失依据——不能只解释容易的那个。
- 解释多于 `target_refs` 是允许的：可见输入可以被解释为上下文。允许不表示可以换目标，被指定的目标一个都不能少。
- `follow_up_requests` 不得引用尚未登记的未来身份。需要新记录时先由相应 agent 产出并登记，再由宿主新建 Task；Reader 不靠"取最新记录"消歧。
- 每轮使用新的固定 Task，保留真实可见输入与预算消耗。输入新增、读者水平变化或问题变化都要新建 Task，不回写旧任务。触发、并行与停止规则见 [SCHEDULING.md](../SCHEDULING.md)。

## 5. 每轮文件约定

运行附件统一使用下表名称，路径相对于独立的运行目录。这些是附件，不新增业务类型。

| 路径 | 内容 |
|---|---|
| `task.json` | 当轮实际固定工作单；仅在确实存在时保存 |
| `draft.json` | 本轮原始模型 JSON；无效原始输出另存 `diagnostics/` |
| `records.json` | 本模块恒为 `[]`。保留该文件只是为了让"这里本该没有记录"可被检查，不是留给以后填 |
| `result.json` | 真实执行产生的 Result；`output_refs` 中无业务记录，解释以 `artifacts` 交付；没有足够运行事实时不造回执 |
| `explanation.md` | 从同一份 `draft.json` 生成的可读说明，或与之有明确对应关系的附件；排版通过不是解释正确 |
| `validation.json` | 分层检查报告：草稿、Task 限制、引用与目标覆盖分别报告 |
| `manifest.json` | 宿主运行索引；固定字段见下 |
| `diagnostics/` | 被拒草稿与校验错误；不是正式交付的替代通道 |

`manifest.json` 固定字段：`manifest_version`（`reader-agent/1.0`）、`run_id`、`mode`（`EXECUTED` 或 `OFFLINE_DIAGNOSTIC`）、`source_refs`、`spec_files`、`schema_bundle_hash`、`model`、`files`、`record_counts`。

- `spec_files` 与 `files` 写 `{path, sha256}`（`files` 另加 `byte_size`），哈希为 `sha256:` + 64 位小写十六进制，不含 manifest 自身。
- `model` 写 `{provider, model_id, settings}`；取不到写 `null`，`settings` 只列真实使用的非敏感设置。
- `record_counts` **恒为空 map**。本模块不产业务记录，这里没有可计的东西；空 map 不表示"这轮什么都没做"。

## 6. 兼容边界

- 草稿 schema 的 `draft_version` 为 `1.0`。本文件不改变任何字段级接口，只把运行约定集中到一处。
- [AGENT.md](AGENT.md) 的 front-matter 使用 `operation` / `execution-kind` / `business-contract` / `orchestration-overlay` / `draft-version` 五行，与本包另两个模块的 `applies-to-*` 写法不同；本轮不改动它，差异记在 [validation-report.json](validation-report.json)。
- 草稿 `$id` 采用 `…/schema/reader-agent/1.0/…`，与 Paper Agent 的 `…/schema/paper-agent/1.1/…` 同形，而与 Autoformalization Agent 的 `…/schema/autoformalization/1.0/…` 不同形。这是包级已知不一致，不在本模块单方面修改。
- 未实现：共享草稿装配器、`manifest.json` 写入器、Result 生成、宿主侧身份与独立性核验，以及把解释附件真正送到读者面前的交付通道。本文件是这些实现的契约，不是它们已存在的声明。
- 跨模型可读性案例（[PENDING_TESTS.md](../PENDING_TESTS.md) 的 L-01 至 L-04）尚未执行。检查器能跑通不等于读者能读懂。
