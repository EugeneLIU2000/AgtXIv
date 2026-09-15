# 图服务接口：固定批次，返回精确引用

graph-contract-version: 1.0
projection-version: claim-graph-v1
状态：2026-09-15 新增接口设计，**未接通运行器、未执行测试**。机器形状见 [graph-contract.schema.json](storage/graph-contract.schema.json)；业务记录仍为 v3/0.0.0，外层 Task / Result 不变。

## 1. 谁调用，解决什么问题

图服务是 host 的固定程序，不是新的 Agent。`utility.project` 负责已授权的投影工作；查询是 host 在模型任务之间使用的受控读取接口，不新增模型可调用的任意 Cypher 操作，也不扩大 `agents.json` 的能力白名单。

| 使用者 | 图可以帮忙 | 后续仍需谁判断 |
|---|---|---|
| Dependency | 找到指定批次内真实存在的上游候选和绑定记录 | Dependency 比较条件；Review 判断具体用途 |
| Proof / Formalization 的输入装配 | 找到选定 proof-plan 的完整推理步骤及其引用 | 原业务记录、组包规则和独立检查；不能直接导入图上的代码名称 |
| Reader / Planner / Delta 的输入装配 | 取得有边界的关系上下文或潜在影响线索 | Reader 解释限制；Planner 只提建议；Delta 固定基准 |
| review.backtranslate | **禁止访问图服务及其派生的源目标上下文** | host 保持首轮代码盲输入隔离 |

没有图服务时，可继续保存、直接按已知引用读取及处理任务。若问题确需邻域查询，返回 UNAVAILABLE 或等待建图，不把“未提供查询能力”说成“没有相关节点”。

## 2. 三类消息与宿主边界

机器文件定义 `PROJECTION_REQUEST`、`QUERY_REQUEST`、`QUERY_RESULT`；所有对象封闭，根字段必填，null 与空数组按 schema 使用。它们都是**运行 metadata / 附件，不是业务 RecordSet 成员，也不冒充 v0.0 query-receipt 或 archive-receipt**。

### 2.1 投影请求：PROJECTION_REQUEST

由 host 生成，固定 `task_id, projection_ref, source, manifest_artifact_ref`。

- `task_id` 指当前合法的 `utility.project` Task。请求文件本身及 manifest、封存验证材料须作为真实附件进入 Task.input_artifacts；批内成员授权由 host 对全部 manifest 成员核对，不因藏在附件里就绕过输入类型/权限限制。
- 请求中的 source 是固定导出边界：`source_store_id, source_event_seq, knowledge_snapshot_ref, base_bundle_hash`。没有科学 knowledge-snapshot 时明确为 null；不能用一个候选导出伪造它。event_seq 是源库已提交事件的边界，不是时间戳或本次图写次数。
- 同一个 manifest / projection_ref 只能绑定一份已封存的 source 描述；重试自报不同事件边界或 snapshot 必须拒绝。即使业务成员没有变化，改用新的源截面也要生成新的导出批次，不能改写旧批次的来源说明。
- `manifest_artifact_ref` 标识 batch.json 的原字节；其 sha256 必须等于 projection_ref.manifest_sha256。manifest 中的 batch_id/source_store_id/base_bundle_hash 分别与请求对应。该附件登记在运行层，不把 batch.json 列入自己的 files。
- 请求不是验证成功回执。执行者必须解析并核验批内真实字节、闭包、权限、固定 schema 与 source 截面证据，才可投影；缺失回执/材料则拒绝执行。
- 请求随已有 Utility request/receipt 使用：不增加 utility-request.parameters 字段；原始请求哈希、实际执行归属、检查点及集合核验报告进入程序回执附件。`Result=DELIVERED` 仍需 host 核实真实交付。

本地封存的含义是：一致性导出、真实验证、持久保存不可变 batch.json 与全部成员及运行回执。仅在内存生成 JSON 或建立空目录不算封存。路径和对象写入需防替换；读取时仍核对哈希。远端 Git 已发布不是本地投影的前置条件。

### 2.2 查询请求：QUERY_REQUEST

host 在授权后的服务调用上下文中生成：`query_id, projection_ref, query, limits`。用户/模型不能靠填写 query_id 或版本号取得权限；实际调用主体、授权范围、父预算和查询实现版本由 host 保存并绑定请求哈希。请求里没有数据库地址、账号、Cypher、可执行表达式或任意排序脚本。

`projection_ref` 必须完整：`projection_batch_id, archive_batch_id, manifest_sha256, projection_version, view`。当前 view **只能显式为 CANDIDATE**；这是私有研究查询，所有结果为 PROVISIONAL。公开/准入视图仍按 STORAGE 拒绝回退。`archive_batch_id` 是旧字段名，指不可变导出批次，不意味着已上传 Git。

图键继续严格采用 [STORAGE 的 canonical 算法](STORAGE.md)：投影身份由导出 ID、manifest 原字节哈希、映射版本、视图计算，**不包含 Git commit**。相同输入不同图后端应得到同一逻辑集合；后端与实际检查点另行记账，不参与业务身份。

| query.kind | 明确的范围与方向 | 路线规则 |
|---|---|---|
| DEPENDENCY_NEIGHBORS | 只沿真实 dependency-binding；UPSTREAM 从 dependent 找 prerequisite，DOWNSTREAM 反向；binding_kinds 显式选业务依赖类型 | proof_plan_ref 为 null 表示不按路线过滤；非 null 只保留精确绑定该路线的记录，null 路线绑定不混入 |
| INFERENCE_STEPS | seed_refs 仅为所选路线的 argument-node；UPSTREAM 找结论为当前节点的步骤，DOWNSTREAM 找含当前节点的步骤 | 必须提供精确 proof-plan；仅沿该计划 inference_refs 中的步骤；返回完整共同前提，不解释为每个前提单独充分 |
| RECORD_CONTEXT | 按固定业务 schema 中实际 RecordRef 字段查邻域；OUTGOING 从 owner 指向字段引用，INCOMING 查引用该对象的记录 | 不沿引用字符串、作者名或向量相似度造边；普通引用不是数学推导 |

DEP / INFERENCE 的一个 depth 单位是一条完整绑定/推理步骤；CONTEXT 是一个精确字段引用。返回原始关系方向不随查询方向倒置。深度限制定义问题的范围，不宣称范围之外为空。遍历采用最小距离的广度优先分层，层内节点按 exact_key、候选关系按 owner 的 exact_key 与字段路径排序；去重键包含查询种类、精确对象与路线。环通过 visited 集合终止，不据此否定整张知识图。为说明关系附带的 owner、路线、上下文/证据不会自动成为下一层的遍历起点，只有该查询定义的邻接端点进入前沿。

INFERENCE 查询中，联合前提作为一个不可拆的结果单元：上游完整加入该步所有前提；下游即使只命中其中一个前提，也返回整组并明确这只是可能受影响，非推理已可执行；向下遍历只将结论加入下一层，不把其他共同前提也当作已受影响。零前提步骤按原记录保留。数组保持源顺序及重复项，底层边需保留字段位置，不能因节点去重改写原 premise_refs。路线之外的替代证明不自动并入。

limits 必须给出深度、返回记录数、关系数、展开次数、毫秒时限、响应字节数。schema 给的是硬上限，host 还需按剩余父预算降低；无无限递归、无无限重试。一次展开计一个被考察的候选关系/步骤，含随后被过滤的项；仅有结果 LIMIT 不能约束实际扫描。无法在后台落实扫描/时间预算时，不开放对应查询。max_response_bytes 包括完整响应的实际 UTF-8 字节，不只计关系数组；预留最小诊断空间。请求的种子/必要路线本身已超记录或响应限额时，返回空数据的 LIMIT_REACHED，不悄悄丢弃部分种子。

### 2.3 查询结果：QUERY_RESULT

固定 `query_id, request_hash, outcome, projection_ref, provenance, record_refs, relations, coverage, open_items`。request_hash 是 `digest(canonical(QUERY_REQUEST))`；原请求字节哈希另存。结果为服务实际执行记录，不由模型编造。

| outcome | 返回内容 | 可以据此说什么 |
|---|---|---|
| READY | 指定 READY 批次内、请求范围完整的精确引用和关系；provenance 必有值 | 只说“这个指定范围内的查询已完成”，不是科学成立或全库无遗漏 |
| LIMIT_REACHED | 仅已回源核验的完整关系单元；允许结果数组为空；coverage=TRUNCATED | 明确预算/输出大小导致截断，不将局部结果当全部 |
| NOT_READY | 数组空、provenance=null、coverage=NOT_EVALUATED | 批次未完成或未与检查点核对，不切换其他批次 |
| NOT_FOUND | 同上；仅在授权的批次目录确认该批次不存在，或核验完整批次后确认种子/路线不存在时使用 | 不等于全库/历史文献中不存在对象 |
| UNAVAILABLE / DENIED / FAILED | 同上；给安全的错误原因，不泄露库外标识或凭证 | 服务缺失、权限不足、执行/一致性失败分别记账，不能当成空搜索 |

对合法已授权请求，结果回显同一 projection_ref；对非法或未授权请求，授权层可在进入本接口前直接拒绝，不返回私有对象是否存在的信息。READY 但没有邻居时仍返回种子引用，relations 为空；record_refs 空不能冒充种子存在且查询完成。

provenance 固定 `source, backend, checkpoint_artifact_ref, query_service_hash, authorization_scope_hash`。checkpoint 附件是 host 保存的实际就绪证据，须绑定本 projection_ref、映射/实现身份、完整节点与关系集合哈希、真实写入/核验回执；不能由一个 READY 字符串代替。authorization_scope_hash 绑定实际服务主体和访问政策，不是模型自报身份。归档成功若需展示，以该 manifest 关联的真实发布回执另读；本查询不要求或编造 Git commit。

## 3. 返回什么关系，怎样回到真正的记录

所有关系必须有 `owner_ref`（原记录见证），不能只给一条无来源的线：

- **DEPENDENCY_BINDING**：保留 prerequisite_ref → dependent_ref、binding_kind、proof_plan_ref、reuse_decision_ref。复用决定为空或有值均不由图判断 ALLOW；内容和适用性回源读取、独立判断。
- **INFERENCE_STEP**：保留精确 proof_plan_ref、premise_refs 全数组、conclusion_ref、context_ref、discharged_context_refs、rule_evidence_refs；规则与论证正文仍取 owner_ref 的原记录。步骤本身没有 proof_plan_ref 字段，路线归属必须来自所选 proof-plan.inference_refs，不凭空给步骤指定归属。
- **RECORD_REFERENCE**：保留 owner_ref、字段 JSON Pointer、target_ref。引用抽取依据固定 schema 类型，不能仅看一个字典“长得像引用”；指向 ArtifactRef 的关系不混作 RecordRef。附件通过回源读取 owner 的真实 ArtifactRef 取得，本版不提供附件节点遍历接口。

成功返回数据时，record_refs 是全部种子、请求指定的非空路线、关系 owner、所有端点及列出的上下文/证据引用的去重并集；不能只返回图中两端却丢失见证。LIMIT_REACHED 可以不返回任何数据；一旦返回某关系，必须包含其完整引用集合。host 从 SQL 的**精确版本**或同批次验证文件读取原记录，复算身份、核对 membership 与字段。返回关系的所有字段必须与原记录及路线一致；缺一个前提不能跳过后报完整。完整单元超过限额则整项不交付并报告 LIMIT_REACHED；源库/图集合不一致则 FAILED，不用 TRUNCATED 掩盖损坏。

返回的外层 record_refs 按 exact_key 排序；relations 按 `digest(canonical(relation))` 排序并按完整关系去重，关系内部的原数组不排序。响应限额不是合法业务图的容量限制：原记录若含超过响应上限的前提，仍须完整投影，查询时整步标为无法在本次限额返回，不能截短源记录后生成另一条推理。图就绪检查点的完整集合编码和回执格式仍需 G-11 完成，不用查询的有界结果子集替代全图核验。

候选全集节点保留记录身份；数学关系使用见证节点实现，不在 MathClaim 上写一个可变 verified=true。通用字段引用可保留用于追溯，但查询 DEP/INFERENCE 时不得把它们混成证明边。所有匹配都限定同一 projection_batch_id，不能靠全局 record_id 连上别批次的“最新版”。

## 4. 图结果如何进入下一轮 Agent

1. 当前模型任务交付搜索建议/缺口，host 保存原草稿；此 Task 的可见输入不变。
2. host 按批准模板和剩余预算执行图查询，保存原请求、实际回执及所选批次。返回内容是检索材料，不是科学证据。
3. host 核验来源、权限、记录和附件，并按下一 operation 白名单选择可见上下文；需要的对象未获授权则不交付，不通过完整图回执附件泄露它们。
4. 对允许输入创建新的 Task，显式 input_refs/input_artifacts 固定实际材料。若为权限/预算只展示子集，保存单独的可见性清单，明确子集，不修改原始查询回执。私有原回执不默认给模型。
5. Dependency / Review / Reader 等只对该轮真实可见内容处理；新线索继续通过同样过程扩展。找到了记录不代表通过依赖门；不能在旧 Task 上追加隐藏输入后仍声称 execution.visible_refs 与原输入相同。

只有授权覆盖**整个投影批次**的 host 服务可执行本版邻域遍历；否则 DENIED 或先按独立授权范围重新构建完整批次。此版不提供“过滤掉部分前提却继续算完整”的逐节点 ACL 查询。提供给下一模型的资料可以更窄，但必须重新满足该任务证据与完整性要求。

选批次是显式行为：需要新写入的记录时，先导出/投影新批次或继续用 SQL 精确读取，不把新 SQL 记录混到旧图结果里。旧图可解释历史，但不能解除依赖“当前知识状态”的门；只有宿主确认所需最新已提交边界已被覆盖，才能用于该门的后续评估。影响查询只提供可能受影响集合，重新调度仍须核对具体使用关系和原任务版本。

## 5. 本地封存、远端归档与故障恢复

SQL 业务/运行事务 → 固定一致性导出 → 验证并持久保存本地批次。之后分别安排本地投影与 Git 归档；二者共享原字节，不共享一个“全部成功”标志。

- SQL 状态：候选已提交。导出状态：尚未固定 / 已固定且验证 / 失败。图状态：BUILDING / READY / FAILED。归档状态：待归档 / 本地 commit / 已远端读回 / 失败。各自属于运行 metadata，不向 batch.json 加状态字段。
- 只有图全部节点、关系及闭包核验后才产生 READY 检查点。头指针按 **source_store_id + projection_version + view** 分区，并比较预期旧版本更新；不能用全局 CANDIDATE 头混合多个源库或映射版本。查询依然指定批次，不直接读可变头。
- 投影和 Git 工作可分别重试。至少一次投递、幂等键、租约代次与单一图写网关仍按 STORAGE；Neo4j 和 SQL 不存在本规范提供的跨库原子事务。
- 本地封存不是远端备份。归档失败时必须显示未受远端保护的导出/SQL 边界；SQL、附件、本地封存回执仍需真实备份。恢复可从已核验本地批次或已读回 Git 批次重建，不从混杂目录猜一个完整快照。

**兼容性：** `storage/runtime.sql` 及现有 Cypher 示例仍是旧 `archive-first` 参考：checkpoint 的 git_commit 非空、头按 view 建立。它们不能直接执行本接口的 `local-seal-first / claim-graph-v1` profile。本轮不修改或迁移旧表，不影响 handoff 的代码指纹。新检查点/本地封存/分区头的持久化适配，以及旧表数据迁移需另行实现；未实现时拒绝启用新 profile，绝不填假 commit 或强塞旧表。

## 6. Neo4j 适配器的安全与实现边界

固定参数化模板、显式数据库名、请求前授权、服务器超时与取消、遍历扩展上限、结果字节上限缺一不可。不要接受模型生成的 Cypher / APOC / 子查询 / 动态标签。agent 无图凭证；查询和写入入口分离。Neo4j driver 的 read routing 只是路由选择，**不是禁止写入的安全保证**，不能代替网关/凭证和部署隔离。[官方事务说明](https://neo4j.com/docs/python-manual/current/transactions/)

driver 的托管事务函数可能重试，因此只做可幂等的图事务，不在回调内再次启动模型、扣款或提交 Git。结果行 LIMIT 也不是安全权限边界，同一 query part 中的写入不因 LIMIT 自动撤销。[官方 LIMIT 说明](https://neo4j.com/docs/cypher-manual/current/clauses/limit/)

约束只采用部署版本确实支持的功能。唯一约束不能确保属性存在；存在、类型和 key 约束涉及 Enterprise 能力，不能把它们当作当前 Community 已有保障。业务身份、哈希、路线和完整性仍由导入器核对。[官方约束说明](https://neo4j.com/docs/cypher-manual/current/schema/constraints/)

本 schema 只描述形状、枚举和静态限额；请求/结果绑定、哈希、预算、授权、业务映射及实际数据库行为需要独立语义检查器。文件在 `storage/`，尚未注册进根 validate.py 的五文件加载器；URI 仅作身份，未来采用固定离线注册表，缺失即失败，不联网补 schema。全部待实现/待测试项集中见 [PENDING_TESTS](PENDING_TESTS.md) 的 G-10～G-13、NG-*。
