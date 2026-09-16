# 运行接口与交付约定

本文件是 AGENT.md 的规范性附件，规定两个生产操作的输入边界、模型草稿形状、宿主装配与每轮文件约定。证明记号细则见 [LAMPORT.md](LAMPORT.md)，Lean 声明对应细则见 [LEAN4.md](LEAN4.md)，轮次与退回见 [REVIEW.md](REVIEW.md)，环境与可信库见 [ENVIRONMENT.md](ENVIRONMENT.md)。

## 1. 两个生产操作

| 操作 | 最小输入 | 输出草稿 | 明确不负责 |
|---|---|---|---|
| `proof.expand` | MathClaim 与独立形成的 frozen-scope；本轮实际使用的原文证明、定义、条件、历史依赖及异议 | proof-draft | 偷改数学目标、自己审阅自己、冻结或扩大范围 |
| `formalization.generate` | 恰好一个固定的 formalization-packet（含数学目标、所选路线、论证快照、定义、Lean 环境、预期声明与未完成义务） | lean-draft | 组装或替换交接包、自己输出独立检查结论、修改环境 |

- 类型白名单以 `agents.json` 为准：`formalization.generate` 的读取输入新增既有 `argument-node`、`inference-step`；`source-span` 未新增为直接输入。节点引用原文位置不自动授予读取原文的权限。
- 统一使用现有 Task → Result；不新增 `autoformalization.run`。Review、Dependency 和 Utility 按各自操作参与；Paper Agent 及其规范本轮不修改。
- 只使用当次 Task 提供的记录与字节。需要新记录时先保存，再创建新 Task；不猜未来引用，不隐式展开未授权输入。
- 输入不足时保存已取得材料与缺口；没有 frozen-scope 时不能启动正式 `proof.expand`，但这不要求 Paper 停止候选提取。
- 同一 Task 的输入中即使可见其他 handover 材料，也不能替换 `Task.target_refs` 指定的唯一目标 packet。

## 2. 模型返回形状

一次生产调用只返回当前阶段的一个原始 JSON 对象：不加 Markdown 代码围栏、额外顶层字段或字段别名。无内容的列表用 `[]`，仅 schema 允许为空的引用用 `null`。模型可以有不同措辞与证明路线，但不能改变接口格式、原目标或来源归属。

| 草稿 | schema | 谁生成 | 要点 |
|---|---|---|---|
| 证明草稿 | [proof-draft.schema.json](proof-draft.schema.json) | `proof.expand` | `draft_version`、`records`、`open_items`、`follow_up_requests`；记录只含类型与既有 payload，payload 直接引用 v3/0.0.0 业务 schema，不复制其字段 |
| Lamport 阅读视图 | [lamport-view.schema.json](lamport-view.schema.json) | 宿主按已登记记录导出 | 只给已登记节点和推理安排编号、层级与结束位置，不创造第二套数学事实；不是生产 operation |
| Lean 代码草稿 | [lean-draft.schema.json](lean-draft.schema.json) | `formalization.generate` | `packet_ref`、`files`、`declaration_map`、预声明的 frontier 草稿与缺口；不含执行回执，也不得编造 work-attempt、formalization-attempt 或 formal-check |

字段级必填、枚举与引用闭包以 schema 和 `check_interfaces.py` 为准；语义与来源审阅见 [Review Agent](<../Review Agent/AGENT.md>)；本流水线的轮次与退回见 REVIEW。草稿合法不等于记录集合法，也不等于数学正确。

## 3. 宿主与模型的分工

| 内容 | 所有者 | 约束 |
|---|---|---|
| 证明陈述、假设、量词、代码、`declaration_map` | 模型 | 按本目录接口细则填写；不得改变原目标 |
| 编号、修订、时间、哈希、附件引用、`producer`、`input_refs` | 宿主 | 来自真实输入与执行；模型不得虚构 |
| 运行事实：work-attempt、formalization-attempt、formal-check、Result 与 outcome | 宿主与相应独立服务 | 草稿内没有“检查通过”字段；无真实执行归属时只保存诊断 |
| 审阅、异议处置与批准 | 独立角色 | 生产者不能关闭针对自己的异议；Review 不修改被审对象 |

装配不得修改证明陈述、假设、量词或代码来使校验通过；需要修订则保留旧版、创建新尝试。旧失败路线与异议继续保留，不因新版本删除。

## 4. 分轮登记与引用

- 记录引用形成实际依赖时分轮登记：`context`／`node` 保存后才能创建引用它们的 `inference`；`inference` 保存后才能创建 `plan`／`snapshot`；存储顺序不能靠未来哈希补齐。
- 同一草稿内的记录尚无正式身份，不能互相引用；`follow_up_requests` 也不能引用其未来身份。需要新记录时，宿主按固定规则选择，不靠“取最新记录”解决歧义。
- 阅读视图在相关记录登记后再导出；一个视图只引用一个 argument-snapshot 和其中选定的 proof-plan。人类可读的 `lamport.md` 必须从同一批记录生成，或作为有对应关系的附件校对；排版通过不是证明通过。
- 每轮使用新的固定 Task，保留真实可见输入与预算消耗；输入新增、目标变化或重试规则变化要新建 Task，不回写旧任务。

## 5. 每轮文件约定

新运行统一使用下表名称；这些是运行附件，不新增业务类型。所有路径相对于独立的运行目录。旧 example 保持原样，不作为新接口的可接受别名。

| 路径 | 内容 |
|---|---|
| `task.json` | 当轮实际固定工作单；仅在确实存在时保存 |
| `draft.json` | 本轮原始模型 JSON；无效原始输出另存 `diagnostics/` |
| `records.json` | 已装配业务记录数组；不混入 Task、Result、manifest 或被拒绝的草稿 |
| `result.json` | 真实执行产生的 Result；没有足够运行事实时不造回执 |
| `lamport.md` | 从同一批精确记录生成的可读证明视图，或与记录有对应关系的附件 |
| 生成代码与 `declaration_map` | Lean 文件按运行目录内的相对路径保存；对应表属于附件，不混入业务 records |
| `validation.json` | 分层检查报告：草稿、Task 限制、引用、单条记录、完整记录集分别报告 |
| `manifest.json` | 宿主运行索引：`spec_files`（路径与哈希）、真实模型信息、`files` 哈希、`record_counts` |
| `diagnostics/` | 被拒草稿、校验错误与待迁移问题；不能作为正式业务输出的替代通道 |

Lamport 视图、生成代码、对应表与 `manifest.json` 都是附件；正式业务记录只有 `records.json` 中装配出的既有类型。

## 6. 兼容边界

- 草稿 schema 仍为 `draft_version` 1.0；本文件不改变字段级接口，只把原先散落在 AGENT、LAMPORT、LEAN4、REVIEW 中的运行约定集中到一处。
- 旧版入口规范原文保存在 [history/AGENT-1.0.md](history/AGENT-1.0.md)；整包 1.0 基线见 git commit `927bd2f`。
- 完整共享装配器、manifest 写入器、调度适配与独立审阅服务尚未实现；本文件是下一步实现的契约，不是这些服务已存在的声明。
