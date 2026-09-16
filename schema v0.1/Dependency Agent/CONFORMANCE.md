# 判定规则与正反例

本文件是 [AGENT.md](AGENT.md) 的规范性附件，与 Paper、Autoformalization 两个目录的 CONFORMANCE 同构。例子是人工教学材料，不是检索结果，也不是论文验证结果。文中"机器"只指 [check_interfaces.py](check_interfaces.py) 当前实际执行的规则；它读 JSON、比较引用身份与已声明形状，从不执行检索、不解析记录内容、不判断数学含义。

## 1. 冲突时的固定优先级

目标对象的精确身份与条件作用范围 → 两端记录是否真实已存在 → 条件差异是否可逐项核对 → 本次授权的检索范围与预算 → 候选的排序与数量。

上一项不满足时不得用下一项补齐：候选再多不替代精确身份，覆盖再广不替代条件比较。四项都决定不了时，保留 `open_items` 与 `frontier-item` 说明歧义，不自选一个更方便的上游。

## 2. `dependency-binding.kind` 的固定判定顺序

枚举值取自 v0.0 [业务 schema](<../../schema v0.0/SCHEMA.md>)，不新造。从上到下选第一个符合者；一次绑定只承载一种依赖，混合情形拆成多条绑定，不合并成"一条边"。

| 优先级 | 值 | 什么时候选 | 不表示什么 |
|---|---|---|---|
| 1 | `MATHEMATICAL` | 目标的证明实际使用该上游结论作为前提 | 不表示该前提已获准复用 |
| 2 | `DEFINITION` | 目标直接沿用上游的定义或记号约定 | 不表示两处定义已核对等价 |
| 3 | `SCOPE` | 依赖来自范围、适用域或冻结边界的继承 | 不表示范围已被 `review.scope` 冻结 |
| 4 | `FORMAL_ENVIRONMENT` | 依赖对象是形式环境、工具链或库条目 | 不表示该库已在信任注册表内 |
| 5 | `SEMANTIC` | 依赖是物理解释、语义适用性或模型假设的承接 | 不表示语义对齐已审阅 |
| 6 | `EMPIRICAL` | 依赖是实验或观测证据 | 不表示证据强度已评估 |
| 7 | `COMPUTATIONAL` | 依赖是数值、代码或可复现计算结果 | 不表示复现已执行 |
| 8 | `VALIDATION` | 依赖是某次检查、审阅或验证结论本身 | 不表示该结论对本目标适用 |

`ParameterComparison.relation` 是**评估结论，不是文本相似度**：措辞接近填 `EQUIVALENT` 是误用。上游更强填 `SOURCE_STRONGER`，目标更强填 `TARGET_STRONGER`，两者不可比填 `INCOMPARABLE`，尚未核对填 `UNKNOWN`。`UNKNOWN` 是诚实的默认值，不是待补占位符。

`frontier-item.kind` 与 `state` 同样取自 v0.0 枚举：上游来源取不到用 `MISSING_SOURCE`，上游结论存在但未证明用 `UNPROVED_LEMMA`，预算耗尽用 `RESOURCE_LIMIT`。`RESOLVED` / `SUPERSEDED` 需要精确 `resolution_refs`（见 E09）。

## 3. 最小正反例

### E01 把检索提案当成检索回执

情形：草稿的 `search_requests[0].query` 写成"已检索全部索引，确认不存在前驱结果"，或在 `sources` 里列出"已访问"的 URL。

- 应发生：`search_requests` 只描述**建议执行**的查询与允许来源；真实查询时间、返回内容、URL 与失败由受限检索服务另存运行附件（[INTERFACE.md](INTERFACE.md) §5 的 `retrieval/`）。
- 禁止：在草稿里表达执行事实；新增 `retrieval_success`、`executed_at` 等字段（schema 直接拒绝）。
- 拦截：**没有机器拦截这段文字**。检查器分不清一条被执行过的查询和一条只是被提出的查询，自报于 `unchecked.retrieval_not_run` 与 `unchecked.absence`。新增字段由机器拦截（`SCHEMA`）。实际防线是宿主的执行附件归属与人工核对。

### E02 同一目标同一查询提两次

情形：两条 `search_requests` 的 `target_ref` 与 `query` 完全相同，只是 `sources` 写法不同（见 [conformance/search-draft-duplicate.json](conformance/search-draft-duplicate.json)）。

- 应发生：一条查询一条动作；要换来源范围就换 `query` 或明确说明这是两个不同目标。
- 禁止：靠重复条目表示"重点检索"或凑数量；宿主无法区分这两个动作。
- 拦截：机器（`DUPLICATE_SEARCH`，路径 `/search_requests/1`）。比较键是 `(ref_key(target_ref), query.strip())`，因此首尾空白不能绕过；`target_ref` 不同则不算重复。

### E03 把记录绑定到它自己

情形：`dependency-binding` 的 `dependent_ref` 与 `prerequisite_ref` 是同一条精确记录（见 [conformance/search-draft-self-binding.json](conformance/search-draft-self-binding.json)）。

- 应发生：找到一条**不同的**已存在记录作为前提；找不到就写 `open_items` 与 `frontier-item`。
- 禁止：用自绑定占位表示"依赖自身定义"或"暂时没有上游"。
- 拦截：机器（`DEPENDENT_IS_PREREQUISITE`，路径 `/records/<i>/payload`）。

### E04 缓存命中或名字相近当成可复用

情形：检索返回一条同名引理，或某个候选之前被查过并命中缓存，于是直接产出 `dependency-binding`，`comparison` 里填一条 `relation: EQUIVALENT`。

- 应发生：逐项写出对象、定义、量词、假设、结论的对应与差异；证据不足时用 `UNKNOWN` 并保留缺口，再请求 `review.reuse`。
- 禁止：把作者名、定理名、相似表述、缓存命中或发表更早当作节点身份或可复用证据；把候选当作已支持的数学前提。
- 拦截：机器只能拦住两件事——`comparison` 为空数组（`SCHEMA`，v0.0 强制 `minItems: 1`）与编造的引用（给 `--task` 时 `INVISIBLE_REF`）。**比较内容是否成立没有机器拦截**，自报于 `unchecked.binding_semantics`。实际防线是独立的 `review.reuse`。

### E05 有界基准写成穷尽调研

情形：`baseline-snapshot` 的 `selection_method` 写"本领域完整调研"，`search_coverage` 写"已审阅全部相关工作"，`limitations` 写 `["None known."]`，实际只跑了一条查询。

- 应发生：`domain` 与 `selection_method` 如实写出这次固定的比较域和挑选办法；`search_coverage` 写实际来源、查询与覆盖；`limitations` 写已知缺失与其影响。空结果也要如实说明覆盖。
- 禁止：用无缺口的措辞掩盖有界检索；`knowledge_ref: null` 时暗示"检索已完整"——`null` 只表示没有可用的既有知识快照。
- 拦截：机器只拦 `limitations` 为空数组（`SCHEMA`，v0.0 强制 `minItems: 1`）。**`"None known."` 这类文字没有机器拦截**：检查器从不解析 baseline payload，自报于 `unchecked.baseline_content`。该缺口在 [tests/test_dependency_interfaces.py](tests/test_dependency_interfaces.py) 中被固化为断言。

### E06 本次未找到当成不存在或全球首次

情形：在允许范围内检索一轮，没有命中，于是写"该结果此前不存在"或"本文为首次"。

- 应发生：交付"在本次固定范围内未找到可用前驱"，同时说明查过哪里、用了什么来源、范围边界在哪；需要长期追踪时写 `frontier-item`。
- 禁止：从空结果推出无前驱；把"未找到"当成新颖性证据。新颖性判断不属于本操作的输出白名单。
- 拦截：**没有机器拦截**，自报于 `unchecked.absence`。机器只能确认这份草稿是一次合法交付（`EMPTY_DELIVERY` 要求至少有检索建议、记录或非空白缺口）。实际防线是人工与后续 `delta.compare` 的独立比较。

### E07 自己批准自己的复用候选

情形：草稿里直接放一条 `reuse-decision` 记录，或把 `reuse_decision_ref` 指向一条本轮"打算创建"的决定，或指向一条真实存在但针对**另一个用途**的 `reuse-decision`。

- 应发生：`reuse_decision_ref` 保持 `null`，用 `follow_up_requests` 请求 `review.reuse`；用途决定保存后创建新的 Dependency 任务与新记录版本，不回写旧候选。
- 禁止：本模块产出 `reuse-decision` 或 `relation-assessment`；把候选绑定读成已获准复用。授权归属见 I1（[Autoformalization Agent/AGENT.md](<../Autoformalization Agent/AGENT.md>) §1）与 [AGENT-CONTRACTS.md](../AGENT-CONTRACTS.md) §4.3。
- 拦截：机器拦住类型越界（`records` 里出现 `reuse-decision` → `SCHEMA`；给 `--task` 时另有 `UNDECLARED_OUTPUT`）与错误类型的引用（`reuse_decision_ref` 不是 `reuse-decision` → `SCHEMA`），给 `--task` 时编造的引用被 `INVISIBLE_REF` 拦住。**一条真实存在但不适用于本用途的 `reuse-decision` 会通过**，自报于 `unchecked.authorization`。

### E08 同一 lineage 不同修订之间的自依赖

情形：`dependent_ref` 是 `math-claim:one` 修订 2，`prerequisite_ref` 是同一 `record_id` 的修订 1。

- 应发生：把它当作版本关系处理，不作为数学依赖边；所选证明路线上的数学推理需满足 DAG 约束。
- 禁止：把引用关系、定义依赖、相似关系、版本关系和已批准的证明前提合并成同一种边。
- 拦截：**没有机器拦截**。`DEPENDENT_IS_PREREQUISITE` 比较完整的 `ref_key`（含 `revision` 与 `content_hash`），两条不同修订因此不构成自绑定。实际防线是 `review.reuse` 与证明路线的 DAG 检查。该缺口在 [tests/test_dependency_interfaces.py](tests/test_dependency_interfaces.py) 中被固化为断言。

### E09 前沿项声称已解决但不给证据

情形：`frontier-item.state` 写 `RESOLVED` 或 `SUPERSEDED`，`resolution_refs` 是空数组。

- 应发生：解决或被取代时给出精确的 `resolution_refs`；尚未解决时用 `OPEN` / `BLOCKED` / `DEFERRED`，并在 `next_evidence` 写清楚什么能收窄它。
- 禁止：用状态字段表达进度感；把预算耗尽写成 `RESOLVED`（应为 `DEFERRED` 加 `kind: RESOURCE_LIMIT`）。
- 拦截：机器（`FRONTIER_RESOLUTION`，路径 `/records/<i>/payload/resolution_refs`）。注意这条是检查器**重新实现**的：草稿只 `$ref` 了 v0.0 的 `#/properties/payload`，没有继承业务 schema 根层的 if/then 门，因此在本检查器之外装配的记录不被它覆盖（自报于 `unchecked.record_conditionals`）。

### E10 上游范围更窄，靠给目标加假设来匹配

情形：上游引理只覆盖纯态或某个 α 区间，当前目标覆盖混态或全区间；为了让绑定成立，在目标一侧悄悄加上"设为纯态"。

- 应发生：如实记录差异（`dimension: ASSUMPTION` 或 `REGIME`，`relation: SOURCE_STRONGER`），交 `review.reuse` 判断用途，交 Proof 决定是否改路线；范围变化反馈 Planner 或 `review.scope`。
- 禁止：为匹配上游而修改目标——那是新命题、新范围（I4）；也不得把差异藏进自由文本了事。
- 拦截：**没有机器拦截**。检查器不读 `math-claim` 内容，也不比较条件，自报于 `unchecked.meaning` 与 `unchecked.binding_semantics`。实际防线是 `review.reuse` 与 Proof；后续待测项为 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 D-05。

### E11 引用未出现在本次 Task，或记录类型未预声明

情形：`dependency-binding` 指向一条本轮不可见的上游记录；或草稿交出 `frontier-item`，而 Task 的 `expected_record_types` 只写了 `baseline-snapshot`。

- 应发生：每个 RecordRef 都是 `Task.input_refs` 的精确成员；需要新记录时先保存，再以真实引用创建下一轮 Task；本轮要交的类型在创建任务时就固定。
- 禁止：用 local placeholder 冒充正式引用；把未声明的业务记录塞进附件绕过类型检查。
- 拦截：机器，但**只在提供 `--task` 时**（`INVISIBLE_REF` / `UNDECLARED_OUTPUT`）。不给 Task 时这两层明确记为未执行（`unchecked.task`），不是默认通过；需要强制时用 `--require-task`（`TASK_REQUIRED`）。Task 本身的白名单、必需输入与能力不提权由 `contracts.task()` 检查，失败报 `TASK_CONTRACT`。

### E12 形式依赖不在可信库注册表内

情形：某条 `kind: FORMAL_ENVIRONMENT` 的候选绑定指向一个外部 Lean 库，而该库不在 [Autoformalization Agent/registry/trusted-packages.json](<../Autoformalization Agent/registry/trusted-packages.json>) 中，或条目状态不允许本次使用。

- 应发生：候选可以提出，但不得进入 release-candidate 交付物；准入条件、状态与撤销规则以该注册表及 [Autoformalization Agent/ENVIRONMENT.md](<../Autoformalization Agent/ENVIRONMENT.md>) 为唯一来源，本文件不复述。
- 禁止：把"import 成功"或"搜到同名引理"当成准入；在本目录另建一份平行库清单。
- 拦截：**未接入**。本目录检查器不读该注册表，也不扫描 import；该注册表自身声明其 `enforcement` 尚未由任何检查器执行。实际防线是人工与该模块的环境政策。

## 4. 一致性如何验收

三层分开报告，前一层通过不等于后一层通过：

1. **机械不变项**：固定草稿字段、合法业务 payload、输出类型属于 `agents.json` 白名单与本 Task 预声明集合、引用是本次 Task 的精确成员、检索动作可区分、前沿状态与证据一致。检查器只覆盖它在 `checked` 中列出的层，`unchecked` 是发布给读者的边界声明。
2. **检索覆盖**：按目标逐项比较——查了哪些来源、用了什么查询、命中什么、漏了什么、范围边界在哪。范围内未配对的目标必须列出，不被候选总数平均掉。
3. **用途与差异处置**：条件差异由独立 `review.reuse` 判断；措辞不同但原意相同可接受，缺条件、量词不同、无依据修复或遗漏必须报告。多个模型给出同一候选也可能一起错，最终对照原文与实际记录，不以多数票代替证据。

候选数量、命中率、缓存命中次数或查询串相似度都不能单独作为质量指标。

## 5. 现在可运行什么

从仓库根目录运行（2026-09-16 实际执行，退出码为实测值）：

```bash
.venv/bin/python -B 'schema v0.1/Dependency Agent/check_interfaces.py' --kind search \
  --input 'schema v0.1/Dependency Agent/conformance/search-draft.json'                       # exit 0
.venv/bin/python -B 'schema v0.1/Dependency Agent/check_interfaces.py' --kind search \
  --input 'schema v0.1/Dependency Agent/conformance/search-draft-duplicate.json'             # exit 1
.venv/bin/python -B 'schema v0.1/Dependency Agent/check_interfaces.py' --kind search \
  --input 'schema v0.1/Dependency Agent/conformance/search-draft-self-binding.json'          # exit 1
.venv/bin/python -B -m pytest 'schema v0.1/Dependency Agent/tests' -q -p no:cacheprovider    # exit 0
.venv/bin/python -B 'schema v0.1/tests/run_agent_tests.py'                                   # exit 0
```

真实 Task 可用 `--task <task.json>` 增加 `task_contract` 与 `task_exact_refs_and_declared_outputs` 两层；未提供 Task 时这两层明确记为未执行。`--require-task` 在缺 Task 时报 `TASK_REQUIRED`。`--fail-on-warning` 当前不可能改变退出码，因为本检查器从不产生 warning。

退出码 0 仅表示**已执行的层**未发现问题；1 表示检查发现问题；2 表示输入或检查器装载错误（含草稿 schema 与 `agents.json` 白名单漂移，报 `INPUT_ERROR`）。exit 0 不等于合规，不等于候选可复用，也不等于检索已完整。

2026-09-16 的实测结果见 [validation-report.json](validation-report.json)；后续待测项登记在 [PENDING_TESTS.md](../PENDING_TESTS.md) 的 D-* 与 X-* 项，本目录不另建清单。
