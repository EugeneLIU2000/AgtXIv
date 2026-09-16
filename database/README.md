# AgtXIv Database

**状态：** 文件契约优先的数据库原型  
**数据格式版本：** 0.1.0  
**设计依据：** `AgtXIv.md` v0.5（2026-08-22）及提交 `095f160`  
**权威边界：** 本目录规定数据如何保存、引用、校验和索引；它本身不授予任何科学结论“正确”或“已验证”的状态。

## 1. 三十秒心智模型

AgtXIv 数据库不是“每篇论文一个大 JSON”，而是一条可追溯的生产链：

```text
冻结的论文版本
        +
问题说明书（Query）
        ↓
一次可重放的运行（Run）
        ↓
候选 scientific claim（可独立追踪的科学主张）、推理步骤、图、证明、证据、blocker、回答等产物
        ↓  独立审阅 / 校验 / 发布门
可跨 Query 复用的知识记录
        ↓
可重建的 SQLite、JSONL、图和网页索引
```

可以把它类比为实验室：冻结论文是只读原件，Query 是实验问题，Run 是一次实验日志，Artifact 是样品或测量结果，Knowledge Record 是通过发布门后放进公共货架的可复用结果，Snapshot/Release 是可重现的封存批次。

本文常用术语的直白含义是：manifest 是列全输入输出的清单文件；canonical 是有显式身份和版本的规范化表达，不等于“正确”；staging 是待校验工作区；promotion 是通过门控后晋升到公共知识层；snapshot 是某一时刻可见记录的冻结边界；receipt 是记录一次发布或查询结果的回执；policy 是状态判定规则；StatusView 是在固定证据快照和规则下计算出的状态视图；Lean kernel 是 Lean 最小可信检查核心。

最重要的分离是：

```text
Paper ≠ Query ≠ Run ≠ Artifact ≠ reusable knowledge
```

- 同一篇论文可以回答多个不同问题。
- 一个问题通常依赖多篇论文。
- 同一问题会因代码、模型、配置、知识快照变化而运行多次。
- 程序执行成功，不等于科学问题已闭合。
- 自动生成的候选产物，不会因为写入磁盘就自动成为知识事实。

## 2. 为什么项目需要这一层

`AgtXIv.md` 把系统描述为搜索引擎、包管理器和增量构建系统的组合。它要求保存冻结来源、可复用 claim、Query 相对依赖图、形式化结果、语义记录、验证证据、阻塞项、修复历史和 Query receipt，而不是维护一张全局“大 DAG”。DAG 是 directed acyclic graph（有向无环图）。

最近的 v0.5 修改又增加了两个直接影响存储的原则：

1. 先对整篇论文做粗粒度中心主张发现，再只对当前 Query 的承重主张做原子化拆解。
2. Lean 或审阅暴露错误后，系统只能发布新 revision、派生 claim、反驳证据、修复记录或 blocker；不能覆盖冻结原文和历史记录。

当前 Stabilizerness demo 已经有丰富产物，但它们散布在 `Stabilizerness/`、`agents/`、`formal/`、`graph/` 和根目录清单中。相同目标还存在多套 ID，部分形式化状态也在旧 export、coverage 和新 verification record 之间发生漂移。因此本原型先解决四件事：

- 一次 Query 到底读取和产生了哪些精确文件；
- 每个文件的版本、来源与内容指纹是什么；
- 哪些只是候选或派生视图，哪些已进入可复用知识层；
- 如何在不扫描“当前目录状态”的情况下重放和审计旧结果。

## 3. 原型选择

本阶段采用：

> Git 可审阅的不可变文件数据集作为事实来源，SQLite 仅作为可重建查询索引。

这样做有三个好处：

- JSON/JSONL、Markdown、Lean 和图文件可以直接 code review；JSONL 是 JSON Lines，即每行一条 JSON 记录。
- 每次 Run 的 manifest（清单文件）能冻结精确输入、输出与来源履历（provenance）。
- 将来迁移到 PostgreSQL、对象存储或图查询服务时，稳定 ID、schema、revision 和 hash 不需要改变。

本阶段不创建 `AgtXIv.md` 中列出的全部物理 Registry，不部署数据库服务，也不移动现有 demo。规范中的 Registry 仍作为逻辑对象归属；只有当权限、并发或生命周期真的不同，才需要拆成独立服务。

## 4. 目录结构

```text
database/
├── README.md                         # 本头文件：目标、结构、规则、案例
├── manifest.json                     # 本数据库格式与入口清单
├── .gitignore                        # 忽略可重建的本地数据库文件
├── schemas/
│   └── query-run-dataset.schema.json # 一次 Query Run 数据集的 JSON Schema
├── migrations/
│   └── 0001_core.sql                 # SQLite 派生目录的首版关系模型
├── templates/
│   ├── query-run-dataset.template.json
│   └── knowledge-record.template.json
├── sources/                          # 冻结 paper-version 清单；不覆盖旧版本
│   └── README.md
├── runs/                             # 每次 Query Run 的不可变 manifest
│   └── README.md
├── knowledge/                        # 经过发布门的可复用记录
│   └── README.md
├── derived/                          # 可从 manifest 重建的索引、图、网页
│   └── README.md
├── examples/
│   └── stabilizerness-closed-form/
│       └── manifest.json             # 当前 demo 的非权威映射案例
└── scripts/
    ├── validate_database.py          # schema、hash、引用、路径校验
    └── build_catalog.py              # 从 manifest 重建 SQLite 查询目录
```

推荐的真实数据路径是：

```text
sources/<provider>/<paper-work-key>/<version>/manifest.json
runs/<query-key>/<run-id>/manifest.json
knowledge/<record-kind>/<record-key>/r000001.json
```

目录 key 只是文件系统安全的名字，不是对象身份。例如对象 ID 可以是 `arxiv:2607.26154v1`，目录 key 可以是 `arxiv/2607.26154/v1`。

### 权威性

| 层 | 是否权威 | 允许内容 |
|---|---:|---|
| `sources/` | 是 | 冻结论文版本及其精确文件引用 |
| `runs/` | 是 | 一次执行的输入、输出、环境、结果和 manifest |
| `knowledge/` | 是 | 经独立发布门产生的 immutable record revision |
| `derived/` | 否 | SQLite、JSONL 索引、图投影、网页、搜索缓存 |
| `examples/` | 否 | 教学 fixture；不得被运行时当作生产知识 |

现有仓库文件仍保留原有地位。example manifest 使用仓库相对路径和 SHA-256 内容指纹引用它们，不复制内容，也不提升状态。SHA-256 可以理解为文件字节的“内容指纹”。

## 5. 最小数据模型

### 5.1 PaperWork 与 PaperVersion

`PaperWork` 表示论文这一作品；`PaperVersion` 表示一次冻结版本。arXiv v1 和 v2 必须是不同的 `paper_version_id`。

最小字段：

```text
work_id
paper_version_id
title
role = TARGET | DEPENDENCY | BACKGROUND
primary_source_artifact_id
source_artifact_ids[]
source_bundle_complete
```

路径不是身份。`primary_source_artifact_id` 指主文档，`source_artifact_ids` 列出 TeX、宏文件、参考文献、图和补充材料等完整 bundle；若 legacy 数据尚未枚举完整，必须设置 `source_bundle_complete=false`。论文更新时添加新版本，不覆盖旧 source。一次 Query 可以通过多对多关系关联多篇论文。

### 5.2 QuerySpec

`QuerySpec` 是问题说明书，表达科学意图而不是运行状态。

最小字段：

```text
query_id
raw_text
normalized_text
fingerprint_sha256
target_refs[]
scope_artifact_id
```

`fingerprint_sha256` 由规范化问题、目标和 scope 的 canonical JSON 计算。人类可读 slug 可以改变，fingerprint 不能悄悄改变。

### 5.3 QueryRun

`QueryRun` 表示在固定代码、配置、工具和输入快照下执行一次 Query。

最小字段：

```text
run_id
query_id
attempt
execution_state
outcome
captured_at
producer
code_commit
command[]
reproducibility_refs {configuration[], prompts[], models[], tools[], formal_environments[]}
retry_of_run_id | null
```

这里必须保留两种互不替代的状态：

- `execution_state = COMPLETED`：程序正常执行结束；
- `outcome = BLOCKED`：科学依赖仍未闭合。

当前 closed-form demo 正是这种情况。不能把它粗暴写成 `FAILED`，也不能因程序成功就写成科学 `SUCCEEDED`。

### 5.4 Artifact

Artifact 是 Run 读取或产生的实际文件。其身份使用原始字节的 SHA-256：

```text
artifact_id = artifact:sha256:<64 hex digits>
```

Artifact 本体的最小字段：

```text
artifact_id
kind
media_type
sha256
byte_size
```

同一字节可被多个 Run 复用，所以 Artifact 本身不拥有唯一 `created_by_run`、路径或输入/输出角色。Manifest 中的 `run_artifacts[]` 是 Run–Artifact 关联，内联 Artifact 核心字段，并另外保存：

```text
role = INPUT | INTERMEDIATE | OUTPUT | EVIDENCE | LOG
storage_class = SOURCE | RUN | KNOWLEDGE | DERIVED
authority
publication_state = FROZEN | STAGING | PUBLISHED | SUPERSEDED
path
schema_name / schema_version
source_refs[]
```

SQLite 中相同 hash 只存一次 Artifact，路径和 role 存在 `run_artifacts` 关联表，因此同一 bytes 可以在一个 Run 中是输出、在另一个 Run 中成为输入。`publication_state` 只描述文件是否冻结/暂存/发布/被替代，不表达科学 `BLOCKED` 或数学 `ACCEPTED`。

必须区分两种 hash：

- `artifact sha256`：文件实际字节的指纹；
- `record content_hash`：按指定 canonicalization 规则计算的语义记录指纹。

两者通常不相等。

### 5.5 SourceAnchor

`SourceAnchor` 把 claim 精确定位回冻结来源，是可追溯性的最小单位。它可先作为 Run Artifact，发布后成为 Knowledge Record。最小字段是：

```text
anchor_id
paper_version_id
source_artifact_id
source_artifact_sha256
location {line_start, line_end}       # 1-based，闭区间
label / section / page / bounding_box # 按来源类型选填
content_hash
```

Anchor 必须同时固定 source artifact ID 与 hash；只保存“第 7 页”或一个 mutable URL 不足以构成 provenance。

### 5.6 ProvenanceEdge

`ProvenanceEdge` 说明输入怎样流向输出，例如：

```text
frozen source --CONSUMED_BY--> source anchors
source anchors --CONSUMED_BY--> scientific claims
claims --CONSUMED_BY--> reasoning chain
verification evidence --EVIDENCES--> export
blocker --BLOCKS--> release
legacy statement --MIGRATED_TO--> canonical claim
```

依赖关系必须显式写入 manifest；不能靠目录扫描或文件名猜测。

### 5.7 KnowledgeRecord

Knowledge Record 是从 Run 产物中挑出并通过独立发布门的可复用对象，例如 `ScientificClaim`、`MathClaimIR`、`MathContract` 或 evidence。IR 是 intermediate representation（中间表示）。

精确引用至少包含：

```text
(object_id, revision, content_hash)
```

不得只引用浮动的 `latest`。修正内容时发布新 revision，并用下面的精确引用指向旧 revision：

```json
{
  "supersedes": {
    "object_id": "claim:...",
    "revision": 1,
    "content_hash": "<64-hex-content-hash>"
  }
}
```

`supersedes.object_id` 必须与新记录相同，旧 revision 必须更小，且不得形成自环；旧记录继续可寻址。形式化、证据或状态改变，不得反向覆盖 claim 的数学含义。

当一个 Artifact 是包含多条记录的 JSONL 时，Knowledge Record 还必须保存 `record_locator`，例如 `{"format":"JSONL","id_field":"id","id_value":"claim:..."}`；正式 `knowledge/` 推荐一对象一文件。否则只有 Artifact hash，仍无法定位文件内部的具体对象。

Knowledge Record 本体不保存一个总的 `verified=true`。数学正确性、source fidelity、formal alignment、semantic alignment、empirical support 等问题由外部证据和固定 policy 下的 StatusView 分别回答。结构校验通过不等于科学结论通过。

## 6. 生命周期与写入流程

一次新 Query 按以下顺序进入数据库：

1. **冻结来源。** 为每个实际使用的 paper version 记录 source path、字节数、media type 和 SHA-256。
2. **规范化 Query。** 保存原问题、规范化文本、目标引用、scope 和 query fingerprint。
3. **创建 Run。** 固定 git commit，并把 config、prompt、model、tool、formal environment 均作为精确 Artifact/环境引用写入 `reproducibility_refs`；未知项明确写 `null` 或空数组。
4. **写 staging 产物。** 粗粒度 discourse claim、原子 claim 候选、关系候选、图、Lean 尝试、日志都先属于这次 Run。
5. **完成 manifest。** 枚举全部实际输入与输出、hash、路径和 provenance edges；manifest 最后落盘。
6. **运行校验。** Schema、hash、路径、唯一 ID、引用完整性和 provenance 必须通过。
7. **独立 promotion。** 只有通过相应 source、relation、formal、semantic 或人工门的对象，才发布到 `knowledge/`；Run 中原候选不删除。
8. **发布 snapshot/release。** 固定本次可见知识边界与 receipt。
9. **重建派生索引。** SQLite、JSONL、图和网页都从权威 manifest/record 生成。

相同 Query、输入 snapshot、source hashes、schema、代码、配置、模型、prompt、工具和环境应产生相同 idempotency fingerprint。重复执行可以复用已完成 Run；明确重试时创建新 `run_id` 并记录 `retry_of_run_id`，不得覆写旧 Run。重试不会使旧实验日志失效；`supersedes` 只用于确实被新 revision 替代的 immutable knowledge record。

## 7. 状态与晋升规则

Artifact 的发布状态只使用：

| 状态 | 含义 |
|---|---|
| `FROZEN` | 只读输入版本已固定 |
| `STAGING` | 文件仍处于本次 Run 的待校验区 |
| `PUBLISHED` | 文件清单已发布；不表示其科学内容 accepted |
| `SUPERSEDED` | 保留但已有后继版本 |

科学 `BLOCKED` 保存在 Run outcome、BlockerRecord 或 StatusView，不能写成文件字节的生命周期。必须继续遵守：

- 自动抽取出的候选记录，其 domain state 默认 `PROVISIONAL`；即使承载它的文件已 `PUBLISHED`，内容也不会自动 accepted；
- candidate relation 与 accepted dependency 分开保存；
- `canonical-candidates` 这个旧文件名不代表记录已经 accepted；
- proof search 超时不等于 claim 为假；
- refuted source claim 仍保留原记录，反例是外部 evidence；
- 未知值写 `null`/`unknown`，不得伪装成 `PASSED` 或 `NOT_APPLICABLE`；
- 派生状态不得复制回 claim、contract、coverage、网页等多个权威位置。

## 8. ID、路径、版本与治理规范

### ID

```text
paper work:       arxiv:2607.26154
paper version:    arxiv:2607.26154v1
query:            query:<query-fingerprint-prefix>
run:              run:<UTC timestamp>:<unique suffix>
artifact:         artifact:sha256:<full digest>
knowledge record: 保留 AgtXIv 的 claim:/math-claim-ir:/contract:/... ID
```

路径可以改变，ID 不随重排改变。跨文件业务引用一律使用 ID；Run–Artifact 关联额外保存仓库相对路径以便读取。

### 时间与路径

- 时间使用 UTC ISO 8601，例如 `2026-08-23T00:00:00Z`。
- 路径统一相对仓库根目录，使用 `/`，不得包含 `..`，不得依赖用户 home path。
- 外部 URI 必须与已冻结的内容 hash 一起出现；mutable URL 不能单独作为 provenance。

### Schema 与 migration

- Schema 使用语义化版本。
- 增加 optional field 是向后兼容修改；删除字段、改语义或改必填约束需要新 major version。
- Meaning-preserving migration 可保留语义 `content_hash`，但新序列化文件有新的 artifact hash。
- Migration 追加记录，不原地改写历史 bytes。

### 安全与合法性

- 不保存 API key、cookie、访问 token 或其他秘密。
- 不保存私有模型 chain-of-thought；只保存公开可审计的 rationale、证据和工具输出。
- 记录 source license、获取时间与再分发限制；无许可的原文可只保存外部定位、hash 和允许的引用。
- 含个人、受限或敏感数据时，必须先定义访问控制和保留策略；当前原型不处理这些数据。

## 9. 当前 Stabilizerness demo 案例

机器可读案例位于：

```text
examples/stabilizerness-closed-form/manifest.json
```

它描述：

```text
target paper: arxiv:2607.26154v1
query target: statement:2607.26154v1:closed-form-equality
execution_state: COMPLETED
resolution outcome: BLOCKED
accepted release: false
```

代表性映射如下：

| 数据角色 | 当前 demo 路径 | 新数据库中的解释 |
|---|---|---|
| Query scope | `pilot-scope.json` | Query 输入，不是结果 |
| 冻结来源 | `Stabilizerness/arXiv-2607.26154v1/draft.tex` | `SOURCE/FROZEN` |
| Legacy PaperAgent | `agents/graph-theoretic-nonstabilizerness/agent.json` | Run 输入/兼容清单 |
| Source anchors | `agents/.../source/anchors.jsonl` | Legacy provenance；仍有 canonical anchor 缺口 |
| Legacy statements | `agents/.../knowledge/statements.jsonl` | Run 产物，不自动视为 canonical knowledge |
| Canonical claims | `Stabilizerness/ScientificClaimRegistry/claims/...jsonl` | 已注册不可变对象集合 |
| 数学中间表示 | `Stabilizerness/MathClaimIRRegistry/claims/...jsonl` | 已注册 `MathClaimIR` 集合 |
| ID migration | `Stabilizerness/MathClaimIRRegistry/migrations/...jsonl` | Legacy → canonical 的显式 crosswalk |
| Reasoning chain | `agents/.../reasoning/chains.jsonl` | Query-relative 推理产物 |
| Verification | `agents/.../verification/records.jsonl` | 分轴证据，不是统一 truth flag |
| Lean result | `formal/AgtXIvStabilizerness/verification-result.json` | 精确范围的 kernel evidence |
| Query graph | `graph/claim-dependencies.json` | 可重建的 Query 投影 |
| Export | `agents/.../exports/closed-form-equality.json` | Legacy blocked contract view |
| Blocker | `agents/.../blockers/perfect-graph-foundation-unchecked.json` | 显式未闭合前沿 |
| Release receipt | `release-manifest.json` | `accepted_release=false` 的 legacy release 清单 |

### 同一目标的多套 ID

当前 closed-form 目标至少出现为：

```text
claim:closed-form-rom
statement:2607.26154v1:closed-form-equality
claim:graph-theoretic-nonstabilizerness:closed-form-equality
math-claim-ir:graph-theoretic-nonstabilizerness:closed-form-equality
contract:2607.26154v1:closed-form-equality
```

这些不能靠字符串相似度合并。example 保存现有 migration/crosswalk artifact；未来应将 `migrated_to`、`normalized_as`、`packaged_by` 等关系写成有 evidence 的对象链接。

### 已发现的状态漂移

`formal/AgtXIvStabilizerness/verification-result.json` 已记录四个 target-local Lean declarations 通过 kernel 检查，formalization contract 也写为部分实现；但旧 export、coverage、release manifest 和当前工件综述仍保留“目标声明未实现/排队中”的叙述。

本目录不在本任务中修正这些旧文件。example 只忠实记录各文件的精确 hash，并把漂移列为 audit finding。这正说明：以后应保存 immutable evidence，再按固定 snapshot 和 policy 派生 StatusView，而不是在多个文件中复制汇总状态。

另一个纯文档漂移是：根 `README.md` 仍把 current specification 写成 v0.4，而 `AgtXIv.md` 已是 v0.5。本目录以 `AgtXIv.md` v0.5 为设计依据，并按任务边界不修改根 README。

### 当前 Query 仍不可重放的原因

`tools/query_agent.py` 目前通过 glob 扫描 `agents/*`，重复 ID 可能被字典覆盖；它不固定 Registry snapshot，也不持久化 request、result、dependency manifest 和 stdout。因此现有 demo 是可运行原型，但还不是严格可重放的 Query dataset。未来每次 Query 必须把这些对象写入 `runs/<query-key>/<run-id>/`。

## 10. 校验与索引命令

从仓库根目录运行：

```bash
python3 database/scripts/validate_database.py
python3 database/scripts/build_catalog.py \
  --include-examples \
  --output /tmp/agtxiv-catalog.sqlite
```

可选检查：

```bash
sqlite3 /tmp/agtxiv-catalog.sqlite \
  "SELECT run_id, execution_state, outcome FROM runs;"
```

Validator 至少检查：

- manifest 顶层结构和必填字段；
- Artifact ID、SHA-256 与实际文件字节一致；
- byte size 一致；
- 所有路径均为安全的仓库相对路径；
- paper/query/run/artifact ID 唯一；
- paper 和 scope 引用的 artifact 存在；
- paper primary source 属于其 source bundle，且未完整枚举时显式标记；
- provenance edge 的两端可解析；
- Knowledge Record 的 `record_locator` 能在 Artifact 内唯一定位对象；
- `supersedes` 使用同一 object ID、更小 revision 和精确 content hash。

`build_catalog.py` 不修改权威数据。默认拒绝覆盖已有文件；只有显式 `--replace` 且目标带有效 SQLite 文件头时才会重建，避免误覆盖普通文件。

## 11. 升级路线

推荐按以下顺序演进：

1. 用本 schema 固定当前 demo 的 artifact inventory。
2. 让下一次 v1 primary Query 原生写出 request/result/run manifest，而不是事后扫描。
3. 只迁移 v1 Query closure 内承重的 claim、relation、evidence 与 contracts。
4. 补齐 SourceAnchor、Registry snapshot、StatusView 和 release receipt 的 exact references。
5. 让 `tools/query_agent.py` 从固定 catalog/snapshot 查询。
6. 数据量、并发或权限需求出现后，再把派生 catalog 换成 PostgreSQL；文件 manifest 继续作为可复现归档。

图数据库和向量数据库只应是查询投影：图数据库加速依赖遍历，向量索引加速候选检索；两者都不能成为 claim identity、provenance 或 acceptance 的唯一事实来源。

## 12. 非目标

当前原型明确不做：

- 一次性把规范中的全部 Registry 物理化；
- 搬动或重写现有 `Reference/`、`Stabilizerness/`、`agents/`、`formal/`；
- 把所有旧数据立即迁移为 v0.5；
- 将 SQLite 二进制提交为唯一真源；
- 自动把 LLM（large language model，大语言模型）候选晋升为知识；
- 设计隐式 `latest` 解析；
- 用一个总 trust score 压平数学、语义、经验和计算证据；
- 因修复或反驳删除旧 claim。

## 13. 新 Query 的最小验收清单

- [ ] 每个实际使用的 paper version 有冻结 source artifact 与 SHA-256。
- [ ] Query 与 Run 使用不同 ID。
- [ ] Run 固定 code/config/model/tool/environment 和输入 snapshot。
- [ ] Manifest 完整枚举输入、输出、hash、byte size 与 media type。
- [ ] 所有 provenance edge 可解析，且无静默覆盖。
- [ ] 自动生成对象默认 provisional。
- [ ] Claim occurrence（原文中的一次出现）与 canonical claim（可复用语义对象）分离。
- [ ] Candidate relation 与 accepted dependency 分离。
- [ ] 修正发布新 revision，不覆盖历史。
- [ ] Evidence 和 StatusView 不写回 immutable claim。
- [ ] 派生索引可以从权威文件确定性重建。
- [ ] 结构校验结果没有被描述成科学验收结果。

如果一位没有读过 `AgtXIv.md` 的维护者能在三分钟内回答“新 Query 放哪里、原文放哪里、可复用 claim 放哪里、未验证结果能否当事实、怎样追溯到论文行号”，这个目录就达到了第一阶段目标。
