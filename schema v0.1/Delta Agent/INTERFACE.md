# 运行接口与交付约定

本文件是 [AGENT.md](AGENT.md) 的规范性附件，规定 `delta.compare` 的输入边界、草稿形状、宿主与模型分工、分轮登记与每轮运行目录。判定顺序与编号正反例见 [CONFORMANCE.md](CONFORMANCE.md)；字段级裁决以 [delta-draft.schema.json](delta-draft.schema.json) 与 [check_interfaces.py](check_interfaces.py) 为准；实现边界见 [validation-report.json](validation-report.json)。共享不变量 I1–I6 见 [Autoformalization Agent/AGENT.md](<../Autoformalization Agent/AGENT.md>)，交接字段、独立性与交付语义见 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md)，本文件不重述其条文。

## 1. 本模块的操作

| operation | 最小输入 | 输出草稿 | 明确不负责 |
|---|---|---|---|
| `delta.compare` | `Task.input_refs` 含 `baseline-snapshot`；`Task.target_refs` 至少有一个非 `baseline-snapshot` 的当前对象；`Task.exclusions` 非空 | delta-draft（`contribution-delta`、`frontier-item`） | 检索历史与建立基准（`dependency.search`）；产出 `relation-assessment`（`review.reuse`）；检查贡献是否交代完整（`review.audit`）；产出 Result、批准或准入；给节点重要性分数 |

- 类型白名单（`input_record_types` 20 项、`output_record_types` 2 项、`capabilities` 2 项）以 [agents.json](../agents.json) 为准，本表不抄录。文档与 `agents.json` 冲突时以 `agents.json` 为准。
- 前三项最小输入由 [validate.py](../validate.py) 的 `Contracts.task()` 强制（`delta.compare` 的必需输入集合、`Delta needs a current target, not only the baseline`、`agent == "delta"` 落在 independent 集合因而 `exclusions` 必须非空）。本模块引用这三条，不重写。
- `capabilities` 只有 `records.read` 与 `delta.compare`，没有 `candidates.propose`。**不表示**本模块不产业务记录：能力串与输出白名单是两件事，`delta.compare` 确实产两类记录。
- `input_record_types` 含 `contribution-delta` 自身，用途是读旧比较记录。**不表示**可以就地修订旧记录；见 [AGENT-CONTRACTS §4.6](../AGENT-CONTRACTS.md) 的「后续新比较生成新记录」。
- 白名单里没有 `challenge`、`challenge-disposition`、`reuse-decision`、`release-*`、`admission-decision`。缺这些材料时写缺口，不推断它们的内容。
- 只使用当次 Task 提供的记录。需要尚不存在的记录（典型是 `relation-assessment`）时先提 `follow_up_requests`，等它被登记后用真实引用重开 Delta 任务，不猜未来身份。

## 2. 模型返回形状

一次调用只返回一个原始 JSON 对象：无 Markdown 围栏、无额外顶层字段、无字段别名。空列表写 `[]`。下面是**空形状示意**，不是可交付的完成示例：

```json
{
  "draft_version": "1.0",
  "baseline_ref": {
    "record_type": "agtxiv.v3.baseline-snapshot/0.0.0",
    "record_id": "", "revision": 0, "content_hash": ""
  },
  "records": [],
  "open_items": [],
  "follow_up_requests": []
}
```

| 草稿 | schema | 谁生成 | 要点 |
|---|---|---|---|
| delta-draft | [delta-draft.schema.json](delta-draft.schema.json)（`draft_version` 1.0） | `delta.compare` | 根字段五项固定：`draft_version`、`baseline_ref`、`records`、`open_items`、`follow_up_requests`；`records` 分支只有 `contribution-delta` 与 `frontier-item` |

逐字段规则：

| 字段 | 规则 | 不表示什么 |
|---|---|---|
| `baseline_ref` | 类型受限的 RecordRef，只能是 `baseline-snapshot`；根字段与每条 `contribution-delta.payload.baseline_ref` 必须是同一条精确记录 | 不表示该基准覆盖完整；覆盖范围写在 `qualifications` 与 `frontier-item` 里 |
| `records[]` | 只有 `record_type` 与 `payload` 两个键；`payload` 直接 `$ref` v0.0 业务 schema 的 `properties.payload`，不复制、不扩展其字段（字段表见[业务 schema](<../../schema v0.0/SCHEMA.md>)） | 不表示草稿是业务记录；封套归宿主 |
| `open_items` | 固定文本顺序 `target=<…>; missing=<…>; checked=<…>; next=<…>` | 空数组只表示确实没有未决项，不表示比较已穷尽 |
| `follow_up_requests[]` | 四字段 `agent`、`operation`、`input_refs`、`reason`；`reason` 固定顺序 `target=<…>; need=<…>; purpose=<…>` | 不表示被请求的任务已被接受或排期，排期见 [SCHEDULING.md](../SCHEDULING.md) |

草稿中**不得**出现的字段：`record_id`、`revision`、`created_at`、`data_class`、`schema_bundle_hash`、`producer`、`policy_ref`、`input_refs`、`content_hash`，以及任何「已检查」「已通过」性质的字段。根对象 `additionalProperties: false`，多写一个顶层键即 `SCHEMA` 失败。

草稿层比 v0.0 业务 schema 更严的两条（`SUPPORTED_WITHOUT_PRIOR`、`DRAFT_REVIEW_UNESTABLISHED`）只存在于本目录检查器。**不表示**这两条已进入业务 schema；被本检查器拒绝的记录在装配后仍可能是 schema 合法的，反之亦然。草稿合法不等于记录集合法，更不等于贡献成立。

## 3. 宿主与模型各写什么

| 内容 | 所有者 | 约束 |
|---|---|---|
| 比较内容：`current_refs`／`prior_refs` 的选取、`operation` 类型、`qualifications`、`frontier-item` 的 `statement` 与 `next_evidence` | 模型 | 只写本次实际比较过的两端；基准覆盖不足如实写进 `qualifications`（`minItems: 1`，没有「无保留贡献」这种形状） |
| `author_declaration` | 模型转录 | 归属明确的作者自述，原样放置；schema 不赋予它任何证据地位，判断写在 `operation`／`outcome`／`qualifications` 里 |
| `review.independence` | 模型只能写 `UNESTABLISHED` | 真实身份与分离是宿主的事；本模块的落地要求见 I2，条文见 [I1–I6](<../Autoformalization Agent/AGENT.md>) |
| `record_id`、`revision`、`created_at`、`content_hash`、`producer`、`policy_ref`、`input_refs`、`schema_bundle_hash` | 宿主 | 来自真实输入与真实执行；模型不得虚构 |
| 关系证据 `relation-assessment` | 独立的 `review.reuse` | Delta 无权产出它。`outcome == SUPPORTED` 因此在结构上依赖一次独立审阅 |
| 基准 `baseline-snapshot` | `dependency.search` | Delta 不建立也不扩展基准；基准不足时提 FollowUp，不改写旧基准 |
| Result、`outcome` 的最终采信、贡献是否被完整交代 | 宿主与 `review.audit` | 草稿里没有「通过」字段；`SUPPORTED` 还须宿主核对关系端点、方向、见证、独立性与基准成员资格 |

装配不得修改 `current_refs`、`prior_refs` 或 `qualifications` 来让结论更强；需要修订时保留旧记录并新建比较。

## 4. 分轮登记与引用

- 依赖顺序决定分几轮：`baseline-snapshot` 先登记，才能被 `baseline_ref` 引用；`relation-assessment` 先由 `review.reuse` 登记，才能进 `relation_refs`。引用一条尚未落库的本轮关系判断是无效引用。
- 同一草稿内的 `contribution-delta` 与 `frontier-item` 尚无正式身份，不能互相引用；`follow_up_requests` 也不能引用它们的未来身份。
- 每轮使用新的固定 Task，保留真实可见输入与预算消耗。输入新增、目标版本变化或基准更换都要新建 Task，不回写旧任务。
- 新基准、新目标修订或新审阅结论一律形成**新的**比较记录，旧判断继续保留。事后替换旧基准以迎合想要的结论是禁区（[AGENT-CONTRACTS §4.6](../AGENT-CONTRACTS.md)），本检查器看不见它（见 [CONFORMANCE.md](CONFORMANCE.md) E08）。
- 贡献记录不可省略：专门的 Delta 工作进程可以省去，但每篇调查仍须由一次符合隔离要求的 `delta.compare` 承担（[AGENT-CONTRACTS §3](../AGENT-CONTRACTS.md) 第 7 条）。[SCHEDULING.md](../SCHEDULING.md) §3 第 7 步的「按需汇总」指汇总动作，不指贡献记录可选。

## 5. 每轮文件约定

运行附件统一使用下表名称，所有路径相对于独立的运行目录。这些是附件，不新增业务类型。

| 路径 | 内容 |
|---|---|
| `task.json` | 当轮实际固定工作单；仅在确实存在时保存 |
| `draft.json` | 本轮原始模型 JSON；无效原始输出另存 `diagnostics/` |
| `records.json` | 已装配业务记录数组；不混入 Task、Result、manifest 或被拒绝的草稿 |
| `result.json` | 真实执行产生的 Result；没有足够运行事实时不造回执 |
| `validation.json` | 分层检查报告：草稿、Task 限制、引用、单条记录、完整记录集分别报告 |
| `manifest.json` | 宿主运行索引；固定字段见下 |
| `diagnostics/` | 被拒草稿、校验错误与待迁移问题；不是正式业务输出的替代通道 |

`manifest.json` 固定字段：`manifest_version`（`delta-agent/1.0`）、`run_id`、`mode`（`EXECUTED` 或 `OFFLINE_DIAGNOSTIC`）、`source_refs`、`spec_files`、`schema_bundle_hash`、`model`、`files`、`record_counts`。`spec_files` 与 `files` 写 `{path, sha256}`（`sha256:` + 64 位小写十六进制，`files` 另含 `byte_size`，不含 manifest 自身）；`model` 写 `{provider, model_id, settings}`，取不到写 null；`record_counts` 由 `records.json` 按完整 `record_type` 计算，不手填。

## 6. 兼容边界

| 项 | 现状 | 处置 |
|---|---|---|
| 草稿 `$id` 命名 | 本模块用 `…/schema/delta-agent/1.0/delta-draft.schema.json`（与 Paper Agent 同形）；[Autoformalization Agent](<../Autoformalization Agent/AGENT.md>) 用 `…/schema/autoformalization/1.0/…`（无 `-agent`） | 已知不一致，两者都不联网解析，URI 只是身份。记在 [validation-report.json](validation-report.json) |
| AGENT.md front-matter 键名 | 本模块用 `business-contract` / `orchestration-overlay` / `draft-version`，另有 `operation` 与 `execution-kind` 两行；两个既有模块用 `applies-to-business-contract` / `applies-to-orchestration-overlay` | 已知偏差，本轮不改 AGENT.md。记在 validation-report |
| `UNCOVERED_TARGET` 的覆盖边界 | 有 `contribution-delta` 时逐目标检查；一条 `contribution-delta` 都没有时该规则整条跳过 | 已知缺口，对应 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 G-07／DL-02；反例见 [CONFORMANCE.md](CONFORMANCE.md) E06 |
| `knowledge-snapshot` 在输入白名单内 | 全套 `agents.json` 中没有任何 operation 产出它 | 结构事实，不是遗漏。需要它时只能由受控集成服务提供 |
| SCHEDULING 与 AGENT-CONTRACTS 的强度差 | `delta.compare` 这个 operation 名在 [SCHEDULING.md](../SCHEDULING.md) 中从未出现 | 以 [AGENT-CONTRACTS §3](../AGENT-CONTRACTS.md) 第 7 条与 `agents.json` principle 4 为准：进程可选，记录不可省 |
| 装配器、身份隔离、真实基准检索 | 均未实现 | 本文件是实现契约，不是这些服务已存在的声明 |
