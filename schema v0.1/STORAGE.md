# v0.1 存储规范与参考布局

状态：底层规划 / reference design，2026-09-12。本文件不宣称迁移、部署、调度器或科学验证已完成；不修改 v0.0 的记录身份和历史字节。任务定义、调度状态机、角色权限以同版本相应规范为准，本目录只约定存储边界；引用这些对象时必须固定其实际 schema 包与精确版本，不能臆造授权。

2026-09-15 修订：新增本地研究用 `local-seal-first / claim-graph-v1` profile，明确图查询契约，并将本地投影与远端 Git 归档解耦。见 [底层评估](SYSTEM-REVIEW.md) 与 [图接口](GRAPH-INTERFACE.md)。这是规范修改，尚未实现/测试；原 `runtime.sql` 和 Cypher 示例保留为旧 `archive-first` 参考，不自动兼容新 profile。

## 1. 三层职责与当前实现的区别

目标顺序：**SQL 运行与候选记账 → 验证并固定本地导出批次 → 分别推进 Neo4j 投影与 Git 归档**。图可从已验证的本地批次或已读回核验的 Git 批次重建；两者必须是同一 manifest 和成员字节，不直接从不断变化的 SQL 行拼图。

Git 是版本归档工具及其仓库格式；GitHub 是托管 Git 仓库的远端位置。本地封存指验证并持久固定不可变导出及回执，尚不意味着已有 Git commit 或远端副本；远端归档默认使用独立、私有的 GitHub 数据仓库。二者都不授予科学认可。

直觉：SQL 是仍在工作的实验记录本，本地导出是某一页固定的副本，Neo4j 是据此绘制的关系地图，GitHub 保存获准归档的版本。远端暂不可达时，本地研究可继续，但必须说明哪些数据尚无远端备份。

| 层 | 当前证据 / 新规范 | 权威边界 |
|---|---|---|
| 旧 `database/` | [旧 README](../database/README.md)规定 Git 文件为真源、SQLite 为派生索引 | 该旧索引可重建；不能把此属性套到 V3 候选库 |
| V3 候选 SQLite | [现有实现](../src/agtxiv_v3/storage.py)已有 records、artifacts、candidate_heads、原子 ingest 和精确历史读取 | 保存候选的实际字节；PROVISIONAL，不提供科学认可或正式准入 |
| v0.1 SQL 运行层 | 在同一个 V3 业务数据库增加任务运行、尝试、导出队列和投影检查点 | 对“提交了什么、运行了什么、待封存什么”负责；不是科学真理裁判 |
| 本地封存 / Git 归档层 | 经验证的一次固定导出及清单；本地持久化和远端读回分别记账 | 对该批次精确字节负责；不能还原从未导出的 SQL 更新 |
| Neo4j | 从固定验证批次产生的可丢弃投影；查询绑定具体批次 | 无独立修改业务含义或批准复用的权限；不是主流程启动条件 |

仓库相对证据路径：`database/README.md` 第 3 节；`database/scripts/build_catalog.py`；`src/agtxiv_v3/storage.py`；`schema v0.0/README.md` 与 `INVARIANTS.md`。另见 [v0.0 边界](../schema%20v0.0/INVARIANTS.md)。网页 `web/local-storage.mjs` 的 jobs.sqlite 又是独立的源码分析任务存储；它也不是 V3 知识库。本规范不自动合并这些现存库。

## 2. 唯一受控写入口与版本

所有 agent 只提交提案和证据给受控存储服务；不得持有 SQL 文件写权、Neo4j 写凭证或封存分支写权。服务验证 schema、精确引用、原字节哈希、调用者权限、允许的任务状态转换，再在一个 SQL 事务内写 V3 业务记录、运行事件及 outbox（待发送消息）。封存器和投影器仅执行已授权的派生写入，不成为第二个业务写入口。管理者仍可能替换本地数据库；触发器不是对抗管理员的安全隔离。

业务记录继续使用 V3 的 `(record_type, record_id, revision, content_hash)`，同身份同版本不同字节必须拒绝；修正、反驳、审阅与撤销均追加新记录，旧版本保持可寻址。工件保存原始字节及哈希，不用重新序列化后的哈希替代原字节哈希。Git 文件哈希、V3 内容哈希、工件哈希必须分别标注算法及语义。

append-only 适用于业务版本、运行事件、固定尝试输入、导出消息和历史检查点；租约、重试时间、当前指针属于可变运行状态，必须使用版本比较更新并追加事件。`candidate != scientific approval`：完成任务、SQL commit、导出校验成功、Git commit 和投影 READY 都不能产生科学认可。认可必须解析真实独立评估、正式政策和准入记录，不能从标签或保存位置推断。

现有 LocalStore.ingest 自行开启并提交事务。接入同事务 outbox 前，必须设计受控服务的事务接口并验证回滚语义；**先调用现有 ingest 再另开事务写 outbox 不满足此规范**。本次不更改该实现。

## 3. SQL、Git、图的映射

下表是逻辑映射，不要求新增同名业务 SQL 表；原 V3 records.body 是业务载体，任何索引都必须可由它和原工件重建。

| 业务对象 | SQL 存储 / 精确引用 | Git 封存 | Neo4j 建议 |
|---|---|---|---|
| records / refs | 沿用 records；引用保留类型、ID、revision、hash；不以可变名称关联 | 一版本一文件，manifest 列举引用闭包 | Record 节点保留 exact_key 与四元组，按批次隔离 |
| artifact | 沿用 artifacts；不能假定当前 LocalStore 支持大对象外置 | 当前全部真实字节随批；外置对象清单是未来扩展 | Artifact 节点，位置不等于身份 |
| source | source-snapshot、source-span 等 V3 记录及原字节 | 原版本、字节跨度、来源与许可清单 | Source/SourceSpan 标签与锚定边 |
| proofs | proof route、inference-step、形式化交接/检查等已有记录 | 路线、环境、声明和检查日志的精确引用 | ProofRoute、InferenceStep；完整前提集合与结论 |
| reviews | 独立评估/对齐/异议/准入记录；目标和政策均精确固定 | 保存审阅输入、输出和可公开身份回执 | Review 指向被评估的精确版本；不得写回 claim 的总 verified 标志 |
| dependency | dependency-binding 及关系/复用决定；类型、条件、方向和见证 | 同批次保留关系及其支撑记录 | 有类型依赖和比较节点；展示边仍可回溯来源记录 |
| runtime | 本目录 runtime.sql；任务记录引用由任务 schema 定义 | 选定截面的事件、attempt 输入及公开回执 | 可选运行履历投影，不作为数学前提 |

当前候选封存契约采用实际的 [archive-batch.schema.json](schemas/archive-batch.schema.json)，清单文件名为 **batch.json**。它的根字段严格为 `contract_version=0.1.0`、`batch_kind=CANDIDATE_EXPORT`、`batch_id`、`source_store_id`、`created_at`、`parent_batch_id`（null 或字符串）、`base_bundle_hash`、`files`。`files` 每项为 `{path, kind, sha256, size_bytes, ref}`，kind 仅为 RECORD 或 ARTIFACT，ref 是完整 v0.0 RecordRef 或 ArtifactRef；sha256 是文件原始字节哈希。path 相对批次根目录且必须安全。媒体类型沿用 ArtifactRef，不向封闭的清单结构添加自定义字段。

所有业务 records 仍按固定 v0.0 bundle 校验；`base_bundle_hash` 必须与实际固定包一致，不能只通过哈希字符串格式检查。整批包含所有被引用业务记录和附件，由离线 validator 复用 V3 RecordSet 检查闭包；不得查外部 latest。`parent_batch_id` 仅说明 lineage，不能借父批次省略任何引用。当前导出是 self-contained；文件内容寻址跨批复用是后续扩展。本次不新增 V3 业务 schema。

[Task](schemas/task.schema.json) 与 [Result](schemas/result.schema.json) 是独立运行 metadata，另存运行表/独立运行清单，**不进入旧 RecordSet，也不冒充 batch.json 的 RECORD 项**。导出校验回执、SQL 截面、投影版本和 Git commit 同样保存在批次外的运行 metadata；通过 batch ID 和 batch.json 原字节哈希绑定。CANDIDATE_EXPORT 不是 scientific release，即使其业务记录包含正向评估也不会自动升级。

联合前提必须表示为 `A → InferenceStep ← B`，再由步骤指向 C；它表达 **A 与 B 共同支持 C**。不能简化为两条看似各自足够的 `A→C`、`B→C`。保留所有 premise_refs、结论、规则、作用域、被解除假设和证据引用，空前提也必须按原记录显式处理。图导入不能因为前提节点缺失而跳过它后仍标记完整。

只对一条选定 proof route 的数学推理子图检查有向无环性（DAG）；论文关系、引用、修订、异议和替代证明组成的全图可以有环。相似、等价候选和反驳边不能都当证明依赖。不同路线的前提不得混合成一条“通过”的证明。

### 图键的确定性计算

本节是所有导入器共享的算法，不允许自行拼接四元组字符串。使用实际 [V3 canonical()](../src/agtxiv_v3/contracts.py) 返回的字节；它调用 [canonical profile 实现](../src/agtxiv_v2/contracts/canonical.py)，profile ID 为 `agtxiv.record-canonical-json/2.0.0-candidate.1`，与 [v0.0 manifest](../schema%20v0.0/manifest.json) 一致。外部 JSON 先经 V3 `parse()` 及对应 schema 校验，拒绝重复键、非法数字与无效引用，再进行以下计算：

```python
from agtxiv_v3.contracts import canonical, digest

# digest(raw_bytes) = "sha256:" + SHA256(raw_bytes).hexdigest()
# exact_ref 是完整、已验证的 v0.0 RecordRef 对象，不是 JSON 字符串。
exact_key = digest(canonical(exact_ref))
manifest_sha256 = digest(batch_json_raw_bytes)
projection_batch_id = digest(canonical({
    "archive_batch_id": archive_batch_id,
    "manifest_sha256": manifest_sha256,
    "projection_version": projection_version,
    "view": view,
}))
projection_key = digest(canonical({
    "projection_batch_id": projection_batch_id,
    "exact_ref": exact_ref,
}))
```

输出均为 `sha256:` 加 64 位小写十六进制；完整 RecordRef 包含 `record_type`、`record_id`、整数 `revision`、`content_hash`，不遗漏、增添字段或移除哈希前缀。Artifact 节点使用相同算法，但 exact_ref 换为已验证 ArtifactRef 的四个身份字段：`artifact_id`、`sha256`、`byte_size`、`media_type`。可选 `path_hint` 仅用于显示定位，必须排除在图键计算之外；换一个存放路径不能生成新的附件身份。不能只取 artifact_id。projection_version 必须固定导入映射和筛选策略，策略变化必须更换版本。Cypher 参数 `$batch_id` 及 checkpoint 表的 batch_id 接收上述 projection_batch_id；archive_batch_id 则取 batch.json 中的 batch_id。

`canonical()` 已负责键排序、Unicode/换行规范化及数值规则；直接使用其返回字节，不追加换行，不以 shell echo、CLI 显示文本的字符哈希、普通 JSON dumps 或 V2 envelope 专用 record hash 替代。batch.json 的 manifest_sha256 则始终哈希原始文件字节，不先 canonicalize。图键仅是投影内部的确定性地址，与业务记录 content_hash、附件原字节哈希和 Git 对象 ID 各有不同含义，不能互换。

导入器必须从已验证的 batch.json 与实际业务记录重算全部键，并逐一比对传入 rows 的 exact_key/projection_key、步骤引用及批次 ID；不能把 rows 自报的键视为可信。已有节点同键不同四元组或字节、批次同键不同参数一律拒绝并保留冲突。下面的 Cypher 只接收完成这些核验的参数，不实现哈希或输入可信性检查。

## 4. 导出、封存与投影协议（新本地研究 profile）

1. 在同一个 SQL 一致性读截面固定记录/工件闭包、运行事件最高序号和 schema/policy 身份；有 knowledge-snapshot 则精确绑定，没有则明确 null，不为候选导出伪造科学快照。导出任务通过同事务 outbox 创建；消息承载固定输入，禁止重试时改读最新头。
2. 导出器检查记录、引用、字节、联合前提、路线、权限及公开许可。按 archive-batch.schema.json 生成 batch.json 及批内全部业务文件；导出器版本、验证范围与运行边界另存回执。不得把结构校验报告当独立科学评估；即使父批次可访问，闭包检查也只使用本批文件。
3. batch.json 不包含自己的哈希或将来的 Git commit ID；它的原字节哈希保存在 SQL 回执中，Git commit ID 也由 SQL 回执关联。投影批次身份固定 batch.json 哈希、导出格式、视图筛选策略及投影器版本，防止同批次混入不同算法或筛选输出。投影 ID 与 archive-batch 的导出 batch_id 分开命名：参考图/运行 checkpoint 中的 batch_id 是投影 ID，回执另行绑定导出 batch_id；其中 manifest_sha256 指 batch.json 原字节哈希。封存目录的 batch-key 是独立安全路径键，不通过包含自身路径的清单哈希循环定义。路径拒绝穿越、符号链接逃逸和大小写碰撞。
4. 持久保存完整不可变本地批次及真实验证/截面回执后，记录本地封存完成，分别登记投影与归档消息。封存目录和 SQL 回执之间也没有跨系统原子性：目录已固定但回执未写时按哈希认领，回执存在但文件缺失时拒绝投影并恢复。未验证的临时目录不能被认领为完成；发布消息采用同事务记账。重试时不重选记录。
5. Neo4j 导入只读取上述已核验批次，无需等待远端 Git。每个批次逻辑隔离，先 BUILDING，按固定次序幂等导入节点再导入关系；每个导入块提交后记录 checkpoint。重试须核对消息和批次哈希。完整性核验必须比较精确节点/边集合及哈希，不能只看总数。
6. 仅在闭包、前提、路线与集合校验通过后标记 READY，再以预期旧批次做可见头切换；头按 source_store_id + projection_version + view 分区。图事务不能与 SQL/Git 跨系统原子提交；SQL checkpoint 落后于图时重放核对，不能凭 SQL 标志盲信图已完成。查询失败或批次未 READY 时返回未就绪，不偷偷选另一个快照。
7. 独立归档工作在专用工作区创建 Git commit。以预期分支头比较更新；竞争时保留本次包，重新核验后追加，不强推、不覆盖旧封存。push 后读回约定远端的精确 commit 和 manifest 字节，再记录远端归档成功。本地封存、本地 commit、图 READY 与远端持久保存是不同状态；归档失败不把已核验本地图标成失败，也不伪造 commit。

原 `archive-first` profile 把第 7 项作为第 5 项前置，仍可用于历史重建。现有参考 SQL/Cypher 仅适配该旧 profile；新本地回执与分区检查点尚需适配，不得直接把 null/占位 commit 填进旧表，见 §8。

outbox 按至少一次投递设计：目的地加幂等键去重；相同键不同内容哈希是冲突，不能忽略。失败采用有上限的指数退避和抖动，超限保留错误及待人工处置状态。租约到期可由新执行者接手，递增 fencing token（执行代次）；旧执行者的迟到提交必须被存储服务拒绝。每一条确认都绑定消息 ID、代次、完整输入哈希、结果哈希和预期状态版本。比较更新（CAS）须使用 `WHERE state_version = :expected` 并递增版本，受影响行数必须为 1；租约同时核对持有人、代次和到期时间。不得删除租约再从代次 1 开始。远端图写须由可检查代次的单一网关串行提交；仅 SQL 租约不能阻止已持有 Neo4j 凭证的旧 worker。

## 5. 查询边界与跨论文复用

公开/默认知识图选择固定的 **ADMITTED_ONLY** 视图：仅纳入独立准入决策支持的条目及明确标为支撑上下文的必要引用；上下文成员不自动成为已认可结论。没有这样的批次时返回空/未就绪，不退回候选。当前 CANDIDATE_EXPORT 只允许产生 `CANDIDATE` 投影；ADMITTED_ONLY/MIXED 是保留规划，不能凭本候选导出创建。候选可显式选择查询，默认标注 PROVISIONAL；未来混合视图必须显式选 `MIXED`，逐条保留身份和认可依据。

当前图读取的固定格式以 [GRAPH-INTERFACE](GRAPH-INTERFACE.md) 和 [机器 schema](storage/graph-contract.schema.json) 为准：请求绑定批次、类型、方向、路线和限额；实际结果返回原记录精确引用、关系见证、源 SQL 事件边界、schema 包、真实检查点、权限范围与覆盖状态。没有 knowledge-snapshot 时为 null；Git 发布回执按 manifest 另行读取，不是每次图查询的必需字段，也不能填假 commit。图查询返回导出时的 SQL 边界，不是当前数据库头。第一版不提供分页；以后游标必须绑定同一边界、查询和权限。

新增材料只在模型任务之间取得，回源核验并选择下一 operation 允许的输入后，再固定新 Task。不能借图服务绕过旧 Task 可见输入或盲反译隔离；不能从查询失败/截断推导不存在上游。需要刚保存的记录时，等待新批次或使用单独标明边界的 SQL 精确读取，不把两次视图混成一次完整图查询。当前源库 query 只是固定 knowledge-snapshot 成员读取，不等于已实现这些图查询。

跨论文检索只提供候选关联；要复用还须逐项比较定义、对象、假设、适用区间和证据，绑定现有 V3 reuse-decision。未比较、未知或冲突必须显示，不能由相似度、Neo4j 可达路径、Git 已封存或源论文有 Lean 结果直接推导 ALLOW。保留选定快照内已知的反驳、限定和冲突关系，不宣称发现了库外全部相关证据。

## 6. 单机起步、升级与恢复

单机先使用一个 V3 SQLite 文件承载业务与运行表，由受控服务串行化写事务；每连接启用 foreign_keys 和 recursive_triggers、设置合理 busy_timeout，评估 WAL 与 synchronous=FULL，避免网络共享文件系统。禁止通过 INSERT OR REPLACE 绕过不可变身份冲突；完全相同重试必须先比较字节。事务保持短小，下载、模型调用、Git 和图导入在事务外执行。当前全库 RecordSet 校验有 10,000 条记录边界，增加运行表不会消除该业务边界。

当多主机 worker、持续写锁竞争、集中权限和故障恢复需求明确后，再迁到 PostgreSQL。它提供不同的并发与运维选择，也增加服务、备份、连接管理和迁移成本；本 SQL 不是 PostgreSQL 迁移脚本。迁移需验证身份/字节一致、事务隔离、租约竞争和历史查询；冻结旧写入口、验证导入、切换单一写入口，禁止双库同时成为业务权威。

SQL 是尚未封存数据的唯一持久来源，**必须备份未导出候选、运行事件、outbox 和相关工件**。采用数据库一致性备份机制或停写后的完整备份；运行中的 SQLite 不可只复制主文件而忽略 WAL。备份与对象库应有共同恢复边界、加密、权限和恢复演练。Git 远端副本和对象备份不能替代这项备份。

恢复顺序：恢复 SQL 及工件并验证哈希/引用 → 核对本地封存与远端归档回执 → 重放未确认 outbox → 从已核验本地或 Git 批次重新构建图 → 校验后切换分区图头。仅有 Git 时只能恢复实际已归档截面，必须报告未归档区间的损失。Neo4j volume 可用于缩短恢复时间，但可重建性不代表 SQL 可丢弃。故障矩阵：SQL 已提交/导出未完成则恢复固定导出；本地批次完成/Git 不可达则继续独立重试归档并报告未远端备份；Git 已写/回执未写则按哈希认领原 commit；图部分写则保留 BUILDING 并幂等续传；图已完成/SQL checkpoint 未写则验证图后补记。备份恢复后必须提升执行代次或重新建立租约以拒绝旧 worker。

## 7. Git 与附件布局

**本版默认选择独立数据仓库。** 当前代码 repo 保存契约、代码和小型样例；真实封存批次写入独立的 GitHub 数据 repo，未确认公开许可前默认 private（私有）。只有受控 publisher（封存发布服务）持有该数据仓库的写权限，执行前述校验、预期分支头检查和远端读回；agent 不能直接提交封存。私有并不自动取得材料使用或再分发许可，仍须检查来源权限和访问范围。

远端 URL、仓库名称、分支策略和凭证属于部署配置，不新增为 schema 字段；运行回执可记录不含凭证的仓库标识与精确 commit 以定位封存。密钥由部署环境提供。本轮不创建本地或远端数据 repo，不迁移现存文件，也不配置 publisher。

备选是在代码 repo 内使用独立目录，仅适用于早期、小规模、数据与代码访问权限一致且材料许可明确的试验。选择前须接受数据历史增大 clone/备份成本、代码与数据权限难以分离的代价；出现大附件、独立访问控制或持续批量封存需求时，应采用默认的独立数据 repo。小样例不得被自动视为真实获准知识。以下是默认数据 repo 内的未来布局，不在本次创建：

```text
archive/batches/<batch-key>/batch.json
archive/batches/<batch-key>/records/<safe-key>/r000001.json
archive/batches/<batch-key>/artifacts/<sha256>.<ext>
archive/runtime/<export-batch-id>/events.jsonl
archive/runtime/<export-batch-id>/receipts.jsonl
```

Git 适合 JSON、Markdown、TeX、Lean 和小日志；不提交 SQLite/PostgreSQL 文件、WAL、Neo4j volumes、备份卷、密钥、令牌和带凭证 URL。manifest 不泄露秘密路径或访问令牌。封存前按权限选择私有仓库/私有对象库；公开封存不意味着有权分发论文全文或附件。

大附件长期可采用不可变对象存储，记录对象身份、原字节 hash、大小、媒体类型、许可、访问策略和保留策略；但当前 self-contained 批次必须把全部附件实际字节放在批内，不能仅放 URL 或外置对象清单。可选择 Git LFS 运输这些字节，但它在 Git 中提交的是指针；验证/恢复前必须完整取回对象到批次路径，再离线核对字节和闭包，指针不可替代附件。无法满足许可或大小边界时拒绝导出并保留待处理状态，不能生成虚假的完整批次。当前 archive schema 每文件上限 64 MiB，不能因使用 LFS 绕过它。GitHub 普通 Git 文件超过 50 MiB 会警告，超过 100 MiB 会阻止；浏览器上传限制 25 MiB。LFS 单文件限额随方案变化，部署前核查并预算存储/流量。[GitHub 大文件限制](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)、[Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)，查阅日：2026-09-12。

## 8. Docker / Community 参考文件

`storage/compose.example.yaml` 仅供规划。Docker command 不可用，本次未运行 Docker、Compose config 或容器；PyYAML 不可用，也未做 YAML parser 验证。部署者必须提供经过验证的 Community 精确镜像（版本标签及 sha256 digest），不能使用 latest、浮动系列或猜测 digest；记录实际架构和镜像身份。模板只要求非空值，部署预检仍须验证镜像格式、来源、许可证和兼容性。本次未选择或拉取镜像。

`/data` 和 `/logs` 使用命名卷；卷不进入 Git，也不是独立备份。认证通过 `NEO4J_AUTH_FILE` 读取仓库外 secret 文件，文件内容按官方格式为用户名/密码，由部署者创建并限制权限；模板无真实密码。端口只绑定回环地址，agent 不直接访问图写接口。Community 下不要假定 Enterprise 细粒度权限可用，读取通过受控查询服务，独立机器访问另行设计网络和认证。更改 secret 文件不能被当作已有库密码轮换的完整流程。

官方依据：[Docker Compose 与 secrets](https://neo4j.com/docs/operations-manual/current/docker/docker-compose-standalone/)、[持久卷与挂载点](https://neo4j.com/docs/operations-manual/current/docker/mounting-volumes/)，查阅日：2026-09-12。

`storage/neo4j.cypher` 只有约束 DDL；`storage/neo4j-import.example.cypher` 是分段参数化示例，**不是 one-shot 导入器**。只使用节点属性唯一约束，避免 Enterprise 专属的存在、类型和 node key 约束。唯一约束不保证属性存在或业务合法，导入器必须补齐验证。依据：[官方约束文档](https://neo4j.com/docs/cypher-manual/current/schema/constraints/create-constraints/)，查阅日：2026-09-12。示例尚未在选定 Neo4j 镜像执行，完整导入器、受控写服务和部署验收仍待实现。

`storage/runtime.sql` 是空库可执行的 SQLite 运行元数据参考 DDL，只创建 runtime_ 前缀表；不创建第二套业务 records/artifacts，不自动 migration 任何现有库。在未来集成库中必须与 V3 业务表同连接、同事务使用。它不是新的任务 schema 或完整调度器；JSON 内的精确引用、哈希、状态转换及权限由受控服务按相应 schema 验证，DDL 本身不足以保证它们。

2026-09-15 兼容边界：旧 DDL 的 `runtime_projection_checkpoints.git_commit` 为非空，`runtime_projection_heads` 以 view 为键；现有 Cypher 也采用旧归档字段。新 `local-seal-first / claim-graph-v1` 要求独立本地封存事实、可无 Git 的检查点及源库/映射/视图分区头，**不能直接复用旧字段宣称已接通**。本轮保留这些文件及已有 handoff 指纹；新 profile 的持久化适配/迁移未实现时必须拒绝启用。新 schema 放在 storage/ 而非根 schemas/；待实现与待测内容只见 [PENDING_TESTS](PENDING_TESTS.md) 的 G-10～G-13、NG-*。
