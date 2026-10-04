# Review_claude_v0.3_1 — schema v0.3 距离目标还有多远

**审查日期：** 2026-09-20
**审查对象：** `schema v0.3/`（3,816 个文件，732 MB；`host/` 32 模块 10,036 行 Python；`lean/` 35 文件 5,149 行 Lean；`runs/` 116 个目录、668 MB），及其与 `schema v0.1` / `schema v0.2` / `formal/` / `src/agtxiv_v3/` / `docs/superpowers/specs/2026-09-19-schema-v03-design.md` 的关系
**审查方式：** 直接读取源码与产物。本文每个数字都注明出处。未修改任何文件；未运行测试；未重跑 Lean；未发起模型调用。唯一执行过的是只读的 `host/audit_research.py`（详见 §9 R-16）。
**对照目标（用户原话）：**

> 输入一篇 arXiv 论文，提取出所有的 math claims 并且得到每个 math claim 的内部依赖以及外部依赖，同时对外部依赖的论文也进行同样的处理……直到得到最早的文献/出处；为了避免无限延伸，可以随后只关注最终能得到 query 的 arXiv math claims 的分支图，对这个分支图的最早的起点进行 mathlib、physlib package 的 Lean 4 auto-formalization，随后沿着链条一步步完成 formalization，并最后验证到 query 的 arXiv math claims。

---

## 0. 结论

### 0.1 距离目标

**v0.3 把这条流水线的前半段（取源 → 抽取 → 依赖图 → 裁剪）建成了一个质量相当高的真实系统，把后半段（Lean 形式化 → 链条验证）建成了一批质量同样高、但完全由人手驱动的独立成果。这两半从未接通过一次。**

不是"差最后一公里"。是两条半程公路各修了一段，中间那座桥连桥墩都还没打。桥墩是两件事：

1. **把非形式化的 claim 文本自动对应到 mathlib / physlib 的声明上**——目前的全部实现是 `host/roots.py` 里一个手写的 7 条字典，整个 10,036 行 host 代码中没有任何库检索。
2. **判定一个节点已经追到了最早出处**——判据写进了 `graph.py`，但**没有任何代码能生产它所需要的证据**，全项目历史上从未有过一个 `ORIGIN` 节点。

而且还有第三个、更基础的问题：**目前的递归是发散的**。四篇论文的那次运行里，敞开的外部请求从 31 涨到 148，而 148 条里只有 5 条（3.4%）最终被接上。递归每走一步，未闭合的边界增长得比闭合的快。

### 0.2 版本控制：已 `git add`，尚未 `git commit`（2026-09-20 复核）

**初版审查发现 `schema v0.3/` 完全未进入 git。此后已执行 `git add`，但尚未提交。** 复核结果：

| 检查 | 结果 |
|---|---|
| 暂存文件数 | **3,396**（2,197,468 行），其中 `schema v0.3/` 占 3,389 |
| `git rev-parse HEAD` | `39e9d03`（2026-09-17，slides 提交） |
| `git log -- "schema v0.3"` | **空——从未有任何提交触及该目录** |
| 当前分支 | `codex/agtxiv-v2`，跟踪 `origin/codex/agtxiv-v2`，无 ahead 标记 |
| 远端 | `origin` → `github.com/EugeneLIU2000/AgtXIv.git`（存在，但这批内容尚未推送） |

也就是说：`git add` 已经把全部内容写成了 `.git/objects` 里的 blob（8,469 个松散对象，228.20 MiB，0 个 packfile），索引引用它们，`git gc` 不会清理。**内容确实比之前安全了**——但没有提交就没有历史、没有 diff、没有回滚点，也没有异地副本；一次 `git reset --hard` 或索引损坏仍会丢失引用。

**暂存方案本身设计得很好，有两点值得肯定：**

1. `schema v0.3/.gitignore` 只排除可重建产物（`__pycache__/`、`*.pyc`、`*.olean*`、`*.ilean`、`*.ir`、`*.ir.sig`），不碰证据。
2. `schema v0.3/.gitattributes` 的 `* -text` 关掉了仓库级换行归一化。**这一条很关键**：项目的证据链靠 SHA256 绑定精确字节，任何 CRLF 转换都会让所有 manifest 失效。本审查实测了三个文件（`host/core.py`、`runs/research-terra-continuation-20260920/summary.json`、`lean/FiniteRoMDuality.lean`）的 `git show :<path>` 与磁盘字节的 SHA256，**三个全部逐字节一致**。证据链能安全通过版本控制。

**但复核发现两个新问题：**

**（1）225 个 Lean 编译日志被仓库根 `.gitignore:41` 的 `*.log` 规则全部排除。**

```
$ git check-ignore -v 'schema v0.3/epoch-migration/runs/.../attempts/001-ReducedRoMSemantics/compile.log'
.gitignore:41:*.log    schema v0.3/epoch-migration/runs/.../compile.log
$ git ls-files 'schema v0.3' | grep -c '\.log$'
0
```

这些 `compile.log` 是 23 次原环境编译失败和 20 次迁移编译失败的**实际 Lean 错误信息**——也就是 L-03 那条"只差 2 行补丁"的结论赖以成立的原始证据。项目最核心的纪律是"失败记录不覆盖、不删除"，而版本控制里的副本把它们全丢了，原因是一条继承自仓库根、新 `.gitignore` 没有覆盖的规则。新 `.gitignore` 的注释写着"source snapshots and receipts stay"——日志就是 receipt，意图和结果不一致。

修法是在 `schema v0.3/.gitignore` 末尾加一行否定规则。**本审查已实测过**（加上后 `git add -An` 干跑列出全部 225 个 `.log`，随后已把 `.gitignore` 还原为暂存状态）：

```gitignore
# Lean compile logs are failure receipts, not rebuildable output.
!*.log
```

**（2）一个 76.4 MB 的 blob 越过了 GitHub 的 50 MB 警告线。**

```
76.4 MB  schema v0.3/runs/semantic-gottesman-full-thesis-20260919/graph.json
```

GitHub 对单文件 50 MB 起警告、100 MB 硬拒绝。这一个还能推上去，但已经很贴边。更要紧的是它和 **R-03** 直接相连：合并深宽两线后的图预估 100–200 MB，**那就会被 GitHub 直接拒绝，根本推不上去**。所以 §10.7 那条"修掉图产物的二次膨胀"不再只是磁盘问题，它现在同时是版本控制的硬约束。

**收尾要做的三步：**

```bash
cd /Users/Yingjian/Documents/GitHub/AgtXIv
printf '\n# Lean compile logs are failure receipts, not rebuildable output.\n!*.log\n' >> "schema v0.3/.gitignore"
git add "schema v0.3/.gitignore" "schema v0.3"
git commit -m "feat(schema-v0.3): track the host, contracts, Lean corpus, docs and run evidence"
git push
```

推送前先跑一次 `git gc`——现在 8,469 个对象全是松散的、没有 packfile，而 graph.json 这类高度重复的 JSON 打包后能压掉很多。

**结论：E-01 从"阻塞（最高）"降为"部分解决"。** 剩下的是一条 `commit`、一条 `push`，和一行 `.gitignore`。**本节之外的所有评估不变**——暂存文件不改变 S1–S9 中任何一个阶段的距离。

---

## 1. 把目标拆成 9 个阶段，逐阶段打分

口径：**不是"写了多少代码"，而是"离一个可重复、对新论文也成立的能力有多远"**。

| # | 阶段 | 完成度 | 状态一句话 | 卡在哪一类问题 |
|---|---|---:|---|---|
| S1 | 论文取源与冻结 | **85%** | 指定版本下载、解包、逐字节内容寻址、SHA256 绑定全部实现并跑通；8 篇论文 + 1 篇期刊 PDF 已冻结 | 工程 |
| S2 | 抽取**所有** math claims | **40%** | 单篇 39/39 输出范围、240 候选；但"所有"无可验证定义，180 个启发式位置只覆盖 149 个，且 8 篇冻结论文中 3 篇从未做过语义抽取 | 研究开放 |
| S3 | 内部依赖 | **35%** | 634 条支持边里只有 261 条（41.2%）落到本文另一条 claim 上；另有 3 个环 | 研究开放 |
| S4 | 外部依赖 | **20%** | 152 条外部请求全部敞开；其中 113 条（74.3%）连可解析的身份都没有；112 条只有 DOI 而 DOI 从不用于解析 | 混合 |
| S5 | 递归上溯 | **15%** | 历史最深 2 跳 / 3 次 join，且那 3 次 join 用了 **0 次模型调用**（纯回放人工准备的证据）；而且递归发散 | 工程 + 研究开放 |
| S6 | 追到最早出处并终止 | **3%** | `origin_evidence` 无任何生产者；400 个 root 全是 `FRONTIER`；40.8% 的外部请求指向 1935–1988 年的文献 | 研究开放 + 资料获取 |
| S7 | 裁剪到 query 分支图 | **75%** | `graph.py` 是全项目最扎实的组件；但产物体积是 O(边×query) 的，39 MB 里 90% 是诊断冗余 | 工程 |
| S8 | 最早节点的 auto-formalization | **2%** | 唯一机制是 7 条硬编码字典，且那 9 个声明名**没有一个**在 `schema v0.3/lean/` 里 | 研究开放 |
| S9 | 沿链上行形式化 + 最终验证 | **5%** | 调度器完整且严谨，但只在一张手工搭的 1 节点图上跑过一次；那次成功的库里只有 2 条声明，其中一条就是答案 | 研究开放 |

**诚实的总体说法：** 这是一条串联链，最弱环节决定端到端能力。S6（3%）、S8（2%）决定了端到端≈0。**从未有过一次端到端运行，当前的组件配置在原理上也不可能成功。**

---

## 2. 三个结构性发现

### 2.1 前半段的输出，后半段吃不下

最新最深的一次跑（`runs/research-terra-continuation-20260920`）：

| 指标 | 数值 |
|---|---:|
| 抽取论文数 | 1（`max_papers: 1`，另有 5 条线索被 `PAPER_BUDGET_EXHAUSTED` 推迟） |
| 递归 join 次数 | **0** |
| 候选 claim | 240 |
| 图节点 / 支持组 / 支持边 | 613 / 213 / 634 |
| **已接受的支持边** | **0** |
| root 数 | 400，其中 **373（93.3%）是占位符**，只有 27 个是真内容 |
| 标为 `ORIGIN` 的 root | **0**（400/400 `FRONTIER`，400/400 `blocked_by: ['CANDIDATE_EXPLORATION_REVIEW_REQUIRED']`） |
| **`formalization_order` 长度** | **0** |
| 路线搜索 | `UNPRICED`，`explored_states: 0`，`routes: []` |
| 图中定理类节点 | 14 / 613（5 theorem + 5 lemma + 4 proposition） |
| 环 | 3 个 SCC（`CYCLIC_SUPPORT_ROUTE`），`topological_order` 只覆盖 605/613 |

**`formalization_order` 是空的。** 把这张图交给 `scheduler.bottom_up_walk`，它一个节点都不会尝试。

一个重要的对照，说明这不是引擎的毛病：**Gottesman 全文图（`runs/semantic-gottesman-full-thesis-20260919/graph.json`，618 节点）的 `formalization_order` 是 34，不是 0。** 两张图的区别在于premise 解析质量：

| | 目标论文（CLI 分批抽取） | Gottesman 全文（代理通读抽取） |
|---|---:|---:|
| 真实 premise 占比 | 261/634 = **41.2%** | 593/761 = **77.9%** |
| `unresolved_claim_occurrence` | 221 | 35 |
| `formalization_order` | **0** | **34** |

**引擎没问题，输入有问题。** 见 §6。

### 2.2 后半段唯一一次成功，是在一个只有两条声明的库里找到了答案

`runs/proof-worker-normalization-attempt02-20260919` 是全项目唯一一次"模型 → Lean → 内核检查通过"。

输入图：**1 节点、0 支持组、0 边、1 个 query**（`candidate-root-audited-graph.json`）。
冻结环境：`requested_declarations = ['AgtXIv.RoM.l1Cost', 'AgtXIv.RoM.normalized_l1']`，`imports = ['AgtXIvRootMath.FiniteAtomRoM']`——**库里一共 2 条声明**（`runs/proof-worker-environment-attempt04-20260919/environment.json`）。

产物：

```lean
"∀ {ι : Type*} [Fintype ι] (x : ι → ℝ), (∑ i, x i) = 1 → (1 : ℝ) ≤ ∑ i, |x i|"
"by intro ι inst x hNorm
    simpa only [AgtXIv.RoM.l1Cost] using (AgtXIv.RoM.normalized_l1 x hNorm).1"
```

1 次模型调用，21.4 秒，67,289 input / 532 output token。

宿主一侧的核验是真的、而且比多数同类系统严谨：沙箱隔离、公理审计（只有 `propext` / `Classical.choice` / `Quot.sound`）、证明项依赖提取、执行后重新校验输入指纹。**但模型并没有被要求"找"任何东西**——它被交给一个只含两条声明的库，其中一条 `normalized_l1` 就是答案本身。这验证了管道，没有验证 auto-formalization。

### 2.3 5,149 行手写 Lean，对流水线完全不可见

`schema v0.3/lean/` 有 29 个数学模块、4,004 行、293 条顶层声明（另有 2 个纯拼接模块 707 行、3 个工具模块）。零 `sorry`、零 `admit`、零自定义 `axiom`、零 `native_decide`。深层审计的 302 条记录全部只用三条标准公理。这是扎实的工作。

但是：**`host/roots.py` 里那 9 个声明名，没有一个在 `schema v0.3/lean/` 里**——它们全在更早的 `formal/` 工程里。结果是流水线一边把"完美图加权对偶"报告成未证明的前提，一边旁边就躺着一份接近完成的手工证明链，两者互不知晓。

同样地：23 个 `runs/*/evidence.json`（Lean 编译证据）里，**0 个包含任何模型调用标记**。这 5,149 行 Lean 全部是人（或协作代理）手写的，mtime 集中在 2026-09-19 的两个时段，约 3 小时 12 分钟。

---

## 3. S8 = 2%：auto-formalization 目前是一个 7 行字典

`host/roots.py:6-18` 的全部"根绑定"能力：

```python
CANDIDATE_BINDINGS = {
    "claim:perfect-graph-definition": ["AgtXIv.GraphFoundation.IsPerfect"],
    "claim:mwis-definition": ["AgtXIv.GraphFoundation.maxWeightIndependent"],
    "root:gottesman-stabilizer-formalism": [...],
    "root:howard-campbell-rom": [...],
    "root:veitch-stabilizer-resource-theory": [...],
    "root:varela-reduced-polytope": [...],
    "root:perfect-graph-weighted-duality": [...],
}
```

7 条，手写，专为 arXiv:2607.26154。同文件 `:45` 把 `library_search_exhausted` **硬编码为 `False`**。

更要命的是：**`roots.py` 只被 `pipeline.py:23` 引用**——那是已经被 README 明确称为"历史迁移案例、不是新语义运行器"的旧路径。**`research.py` 和 `proof_walk.py` 从不 import 它。** 也就是说，在活跃路径上，根绑定完全由人写进请求 JSON。

在整个 `host/` 约 10,000 行里：

- 检索 `loogle` / `moogle` / `library_search` / `exact?` / `apply?` / 任何语义检索：**零命中**。
- `host/model_routing.py:11-15` 的 `OPERATION_CLASSES` 定义了系统全部 **6 个**模型操作：`paper.extract`、`dependency.match`、`autoformalization.failure_classify`、`autoformalization.lean`、`autoformalization.lamport`、`autoformalization.premise`。**没有"检索库声明"，也没有"搜索最早出处"。**

目标要求系统在拿到一段自然语言 claim 时，自己去 mathlib（约 20 万条声明）和 physlib 里找对应声明。**这件事零行代码。**

---

## 4. S6 = 3%：ORIGIN 的判据存在，但没有任何东西能满足它；而且递归在发散

### 4.1 判据有，生产者没有

`host/graph.py:511-521` 与 `host/GRAPH.md` 定义得很清楚：`ORIGIN` 需要一个 `origin_evidence` 对象，含 `search_status: SEARCH_EXHAUSTED` 和非空 `references`。判据本身合理。问题是：

- 全仓库检索 `origin_evidence`：只有 `graph.py`（消费）和 `pipeline.py:83`（读取）。**没有生产者。**
- 所有生产 root 的代码都把 `upstream_search` 硬编码为 `FRONTIER`：`candidates.py:64,74`、`ingest.py:570,638,726,852,916`、`pdf_candidates.py:134,153`、`case.py:65`。
- 全仓库数据产物中 `upstream_search=ORIGIN` 的数量：**0**（13 处 grep 命中全是 `graph.py` 源码副本里的字符串字面量）。
- `host/core.py:16-19` 的 `TERMINAL_KINDS` 有 6 个值，但只有 2 个被实际产生过。`PREARXIV_DOI_NO_SOURCE` 和 `MONOGRAPH` **在任何代码和任何数据文件里都没有被赋过值**。
- `host/research.py:491` 对**每一条**线索硬写 `terminal_kind='ARXIV_SOURCE_AVAILABLE'`；而 `research.py:489` 是 `Frontier.consider` 的唯一调用者，所以 `scheduler.py:227` 里那个 `TYPED_TERMINAL; ORIGIN_NOT_IMPLIED` 分支**永远不会执行**。

### 4.2 前沿的实际构成：三分之二走不通

对最新 613 节点图里 152 条 `external_claim_request` 的逐条分析：

| 类别 | 数量 | 占比 |
|---|---:|---:|
| 可解析到已固定版本的论文 | 39 | 25.7% |
| 无法解析（109 条身份待定 + 4 条版本未固定） | 113 | **74.3%** |
| 带 arXiv 标识 | 40 | 26.3% |
| **只带 DOI**（DOI 从不用于解析） | **112** | **73.7%** |
| 引用 1935–1988 年文献（arXiv 不可能有） | **62** | **40.8%** |
| 引用专著 | 13 | 8.6% |
| 引用博士论文 | 1 | 0.7% |

而且那 39 条"可解析"的全部指向**已经在本地目录里的 5 篇论文**——**零条会触发一次新的获取**。

1935–1988 的那 62 条集中在 9 部作品上：GLS 1981（10）、Lovász 1979（9）、GLS 1988 专著（9）、Lovász 1972 normal（8）、Lovász 1972 characterization（8）、Chvátal 1975（8）、Brauer–Weyl 1935（4）、Fulkerson 1971/1972（5）。**这正是这篇论文数学主干（完美图对偶）的出处所在。** 实现的机制（只跟 arXiv 身份走）在任何预算下都到不了这些分支。

### 4.3 递归是发散的

`runs/research-four-paper-20260919` 的四个图快照：

| 快照 | 论文数 | 节点 | 支持组 | **敞开的外部请求** |
|---|---:|---:|---:|---:|
| 00001 | 1 | 109 | 66 | 31 |
| 00005 | 2 | 260 | 146 | 82 |
| 00009 | 3 | 367 | 199 | 120 |
| 00013 | 4 | 468 | 264 | **148** |

query 集全程冻结在 72。**每引入一篇上游论文，敞开的外部请求增加 30–50 条，而三次 join 总共只闭合了 5 条（3.4%）。** 第四篇论文对被选中的子图贡献为零（快照 00009 和 00013 的选中图都是 132 节点 / 84 组）。

这不是预算问题，是**结构问题**：没有相关性过滤，也没有除 `max_papers` 以外的收敛机制。"递归到最早出处"在这个结构下不会终止，会爆炸。

### 4.4 实际撞上"最早出处"时发生了什么

`runs/origin-berge-1961-followup-20260919/observations.json`：目标是 Berge 1961 发在 Halle-Wittenberg 大学学报上的德文摘要（第 114 页）。5 轮检索、4 个 URL 之后：

```json
"original_paper_read": false,
"frontier_status": "SOURCE_UNREACHABLE_IN_THIS_BOUNDED_SEARCH",
"origin_established": false,
"raw_response_bytes_retained": false,
"accepted_support_edges_added": 0
```

这次检索是**代理手工做的**，不是控制器做的——控制器的操作词汇表里没有这个操作。而且 `raw_response_bytes_retained: false`：这是全项目少数几处**不可复现**的证据，与项目其余部分的字节留痕纪律不一致。

唯一真正读完的前 arXiv 文献是 Lovász 1972（4 页 PDF，142,102 字节，全部视觉读完，产出 10 条候选、9 个 query、10 节点、7 组、1 条 Berge1961 请求，字节审计 PASS）。**但 PDF 页区域分支从未接入主图**（`host/PDF_REGIONS.md:18` 自述控制器不导入 PDF assembly）——所以这次真实的阅读对 query 图贡献了 **0 条边**，引用 Lovász 1972 的那 8 条请求至今敞开。

**判断：** "递归到最早出处"作为自动化判据**不可判定**——没有任何程序能证明"再没有更早的出处了"。这不是实现懒惰，是问题本身没良定义。必须换成可操作的替代判据（§10.4）。

---

## 5. 契约层：成功状态在 schema 里不可表示

`schemas/research.schema.json` 的 `ChainCertificate`：

```json
"source_completeness_asserted": { "const": false },
"human_accepted":              { "const": false },
"premise_extraction_status":   { "const": "QUERY_DECLARATION_ABSENT" },
"coverage": { "items": { "not": { "required": ["proof_discharged", "statement_discharged"] } } }
```

`state` 枚举里留了 `CHAIN_CERTIFICATE_EMITTED`，但一份**必须**声明"query 声明不存在"的证书永远不可能是成功证书。同时 `host/pipeline.py:152` 只有一个分支，永远输出 `CHAIN_INCOMPLETE`。

这是在**诚实地描述当下**，这一点值得肯定。但代价是：**系统没有"终点长什么样"的机器可读定义**。没有终点定义就没有验收条件，没有验收条件就没有任何一次改动能被判定为"更接近了"。116 个 run 目录全部以同一个状态结束，这个信号对进展完全不敏感。

---

## 6. 一个可以立刻改善的诊断：2048 字节的 focus 窗口正在伤害内部依赖解析

这是本次审查里**性价比最高的一条技术发现**。

`host/candidates.py:79-90` 的逻辑：模型报告 `internal_support_occurrence_ids`，宿主只在该 occurrence **唯一**对应到一条 claim 时才建真实边；否则建一个 `unresolved_claim_occurrence` 请求。

目标论文的抽取用的是 39 个 **2048 字节**的 focus 范围（`max_focus_bytes 2048`）。一个只能看到 2048 字节窗口的模型，**看不到本文其他 claim 的存在**，因此它报出的内部支持几乎必然指向"某个 occurrence"而不是"某条已抽出的 claim"。结果就是 221 条悬空边。

对照 Gottesman 全文抽取（代理一次通读全文，450 条候选）：`unresolved_claim_occurrence` 只有 35 条，真实 premise 占比 77.9%，`formalization_order` = 34。

**这说明分批窗口是当前内部依赖解析率低的主要原因，而不是模型能力。** 可验证的改法：做两阶段抽取——第一遍全文只抽"claim 清单 + ID"（输出短，不会超时），第二遍逐范围抽细节时把第一遍的完整 claim 清单一起喂进去。这样模型报内部依赖时有全局 ID 可指。

**这条建议可以被证伪**：跑一次两阶段抽取，看 `unresolved_claim_occurrence` 是否从 221 显著下降。如果不降，说明我诊断错了。

---

## 7. 真正做得好的部分（不要推翻重来）

1. **`host/graph.py`（559 行）** — 全项目最强组件。迭代式 Tarjan 缩点；AND（组内）/ OR（组间）语义；共享前提只计一次费的分支定界；成本未知时**保留全部祖先**而不偷偷选一条路；删边敏感度同时报告"遗漏敏感性"和"支持撤回"两个不同问题，并显式标注 `omission_is_valid_proof_route: false`。这套语义比"压成一张普通 DAG"正确得多。
2. **逐字节来源绑定** — 模型只能给"文件路径 + 唯一逐字引文"，字节偏移和哈希由宿主算（`host/model.py: bind_source_locators`）。引文重复即拒绝，绝不猜位置。这消灭了一整类幻觉。
3. **宿主/模型职责分离** — `core.reject_model_state` 从结构上禁止模型写状态字段；`graph.py` 拒绝 `state`、`derived_state`、`selected` 等输入。
4. **Lean 语料的质量** — 293 条声明，零 `sorry`/`admit`/自定义公理，302 条审计记录全部只用三条标准公理，662 条证明项组合见证。这是真本事。
5. **epoch migration** — 82 个模块从 Lean 4.30 整体搬到 physlib 的 Lean 4.33 / mathlib，全部编译通过；107 份回执（87 成功、20 失败）全部保留；21 步适配全部留痕。
6. **失败保留纪律** — 46 次 Lean 编译尝试里 23 次失败全部留档；28 次模型失败回执不删；连一次误执行 `git diff --check` 都明确记下"不作为功能测试结论"。这种纪律在研究代码里极罕见，是项目的核心资产。
7. **设计文档（709 行）** — 质量很高，而且已经预见了本次审查的多数结论。

---

## 8. 项目自己的设计文档已经说对了，但实现没照着做

设计文档 §10 的里程碑顺序：

```
M0  contracts      五个 schema 补充                      纯契约，零模型调用
M1  measurement    对已有 ground truth 做回放（§11）      ~$12，~1 小时
M2  Tier P         合并抽取器、宏表、locator 预扫、.bbl    零模型调用
M3  DECISION layer 25 条标注 claim 的 bake-off → 第一条校准曲线
M4  close the loop 队列+门禁走图、逐节点 Lean、人选链条
M5  index + recursion
```

并明确写着：**"M1 is placed before M2 deliberately: it is the cheapest run that converts the most unvalidated constants into measurements."**

**实际发生的是：M1 从未运行。** 它的三个目标在所有 `runs/*/proof-walk-result.json` 和 `summary.json` 里零命中：

| 目标 | 参照 Lean | 是否被尝试过 |
|---|---|---|
| `claim:perfect-graph-definition` | `AgtXIv.GraphFoundation.IsPerfect` | **否** |
| `claim:mwis-definition` | `AgtXIv.GraphFoundation.maxWeightIndependent` | **否** |
| `claim:sign-alignment-identity` | `AgtXIv.Stabilizerness.max_abs_signed_sum` | **否** |

与此同时，M2/M3/M5 方向上花掉了 **74 次模型调用**和 **668 MB 产物**。按操作分：`paper.extract` 69 次（其中 **28 次失败，40.6%**）、`dependency.match` 3 次、`paper.extract.single_statement` 1 次、**`autoformalization.lean` 1 次**。

**这是资源配置上的核心失误。** 项目把预算投在"扩大前半段的量"上，而回避了那个唯一能回答"这条路走不走得通"的实验——**模型到底能不能从 claim 文本自动写出 Lean？** 实验设计已经写好，成本约 $12、约 1 小时，至今没跑。

---

## 9. 缺口总表

编号前缀：**C**=核心链条，**L**=Lean，**R**=运行与证据，**E**=工程。

| # | 缺口 | 严重性 | 证据 |
|---|---|---|---|
| **C-01** | 前后半段无接口：目标论文图的 `formalization_order` 为空 | **阻塞** | `runs/research-terra-continuation-20260920/graphs/00001-db0e3d21/graph.json` |
| **C-02** | 无库检索；根绑定是 7 条硬编码，且只被废弃路径引用 | **阻塞** | `host/roots.py:6-18,45`；`grep 'import roots'` → 仅 `pipeline.py:23` |
| **C-03** | `origin_evidence` 无生产者；6 个 `TERMINAL_KINDS` 只有 2 个被产生过 | **阻塞** | `host/graph.py:511`；`host/core.py:16-19`；`research.py:491` |
| **C-04** | 递归发散：31→82→120→148，闭合率 3.4% | **阻塞** | `runs/research-four-paper-20260919` 图快照 00001/00005/00009/00013 |
| **C-05** | 74.3% 的前沿无可解析身份；40.8% 指向 1935–1988 文献 | **阻塞** | 152 条 `external_claim_request` 逐条分析 |
| **C-06** | 成功态在 schema 里不可表示 | **阻塞** | `schemas/research.schema.json` 四处 `const`；`host/pipeline.py:152` |
| **C-07** | 无校准曲线，`validate_policy` 强制 `quality_calibration = None`，所有自动门禁只能停在 `AWAITING_REVIEW` | **阻塞** | `host/model_routing.py:28` |
| **C-08** | 112/152 条请求只有 DOI，而 DOI 从不用于解析；Crossref 适配器只接在废弃路径上且输出被丢弃 | 重大 | `host/research.py:100`；`ingest.py:888` 仅由 `pipeline.py:232` 调用 |
| **C-09** | 深线（240 候选）与宽线（4 篇 / 72 query）**无法机械合并**：候选 ID 是 `(paper_id, sources, statement, conditions)` 的内容哈希，两套节点 ID 交集为 0，文本交集为 2（都是模板句） | 重大 | `host/candidates.py:54`；ID 集合比对 |
| **C-10** | 合并清单遗漏了 Howard（4 篇之一，54 候选），且自述从未执行 | 重大 | `profiles/upstream-evidence-imports.json` |
| **C-11** | 内部依赖解析率 41.2%，221 条边悬空；主因很可能是 2048 字节 focus 窗口（§6） | 重大 | 图统计；Gottesman 对照 77.9% |
| **C-12** | PDF 页区域分支已建好并审计，但从未接入主图；唯一读完的前 arXiv 文献贡献 0 条边 | 重大 | `host/PDF_REGIONS.md:18` |
| **C-13** | "所有 math claims" 无可验证定义；覆盖率口径是"启发式位置"而非数学陈述；8 篇冻结论文中 3 篇（649/2093 = 31% 的位置）从未语义抽取 | 重大 | `coverage.scope = "SUPPLIED_HEURISTIC_OCCURRENCE_IDS_NOT_ALL_MATHEMATICS"` |
| **C-14** | 图中 3 个环（SCC），不可能成为形式化顺序 | 中 | `graph.json: issues[0] CYCLIC_SUPPORT_ROUTE` |
| **C-15** | v0.2 的 `relation_to_source` 规范化契约被丢弃——那是唯一能机械检查"模型是否改写了定理"的机制 | 重大 | `schema v0.2/Paper Agent/AGENT.md:240-251`；v0.3 中 `relation_to_source`/`VERBATIM`/`NOTATION_NORMALIZED` 零命中 |
| **C-16** | 宏表构建了但从不发给模型 | 重大 | `ingest.py::_macro_inventory` 填充；`model.py:422-438` 的 payload 无 macro 键 |
| **L-01** | **两个 Lean 模块从未被任何 Lean 版本编译过**，而它们正是通向加权完美图对偶的最后两环 | **阻塞** | `lean/PerfectGraphIntegerCover.lean`（118 行 / 9 声明）、`lean/PerfectGraphWeightedApproximation.lean`（120 行 / 7 声明）。本审查复核：全仓库 grep `PerfectGraphIntegerCover` 只命中 `PerfectGraphWeightedApproximation.lean` 的 import 行，grep `PerfectGraphWeightedApproximation` 零命中；无 run 目录、无 receipt、无 `.olean` |
| **L-02** | 加权完美图对偶从未被证明，只作为显式未证前提存在 | **阻塞** | `formal/AgtXIvVarela/.../ExternalPerfectGraphFoundation.lean:55,65,71` |
| **L-03** | `thm:solvable` 的两半在两个 Lean 工具链里，无法组合；桥接层 `COMPATIBILITY_BLOCKED`，0/3 模块编译——而失败原因（`Std.Symm` API 变更）在别处已有 **2 行**补丁 | **阻塞** | `epoch-migration/runs/20260919-perfect-weak-extension/progress.json`；对照补丁 `.../20260919-graph-bounds-perfect-replication/adaptations/002-true-twin-Std-Symm-api.diff` |
| **L-04** | 饱和性（attainment）半边**零 Lean 内容**，连构造计划都没有 | **阻塞** | grep `eigen\|traceless\|anticommutator` 于 `lean/` → 只有注释噪声 |
| **L-05** | `thm:solvable` 的完美性假设从未在 RoM 链条中出现 | 重大 | 最深端点只有 `hNoActive` 一个命题前提 |
| **L-06** | 1 个模块编译成功但从无审计（8 条声明不在任何公理普查里） | 中 | `runs/perfect-graph-integer-replication-20260919/`：有 receipt，无 `evidence.json` |
| **L-07** | 2 个模块是纯拼接，任何"lean/ 有 N 行 / N 声明"的口径都重复计了 707 行 / 41 声明 | 中 | `RoMGraphDualFoundation.lean`、`GraphDualCoverFoundation.lean` |
| **R-01** | 承载全部头条数字（240 / 613）的三次运行**从未被独立审计过** | **阻塞** | 26 份 `integrity-report*.json` 中无一属于 terra / luna / live-full-output-batches |
| **R-02** | 图产物是 O(边×query) 的：39 MB 里 **90.0%**（35.3 MB）是 `edge_criticality`，其中 **83.5%**（32.8 MB）只是同一个 240 元 `query_ids` 列表被序列化 **3,175 次** | 重大 | 逐字段字节统计 |
| **R-03** | 合并后的图会超过本轮新设的 64 MiB 上限（预估 100–200 MB），**这是"下一步"本身的结构性阻塞** | 重大 | 613 节点 → 39 MB；618 节点 → 80 MB |
| **R-04** | `dependency.match` 只跑过 3 次、无批处理无并发；闭合 152 条请求需约 2 小时串行，且崩溃恢复从未演练 | 重大 | 两次实测 46.0 s / 49.1 s；所有审计 `concurrency_or_crash_recovery_exercised: false` |
| **R-05** | 39 个抽取范围首轮失败 22 个（56%），其中 15 个在 13 秒内失败（供应商侧拒绝或启动失败） | 重大 | `runs/research-live-full-output-batches-20260919/ledger.json` |
| **R-06** | 唯一一次 CI 检查验证的是被取代两代的产物；对当前运行器 `validate.py` 直接 FAIL | **阻塞** | `tools/validate_repo.py:363-370` → `runs/latest.json` → 2607-full-candidate；对 terra 运行返回 `{"integrity":"FAIL"}` |
| **R-07** | 约 215 MB（32%）是被取代的前缀与失败尝试，无取代索引 | 中 | 5 个 Gottesman 章节前缀 112.3 MB；4 次失败的 proof 环境 85.1 MB |
| **E-01** | ~~`schema v0.3/` 完全未进入 git~~ → **已 `git add`（3,396 文件），但尚未 `git commit`，也未推送** | 部分解决 | `git log -- "schema v0.3"` 为空；HEAD 仍是 `39e9d03`（2026-09-17）。详见 §0.2 |
| **E-01a** | 225 个 Lean `compile.log`（失败回执）被仓库根 `.gitignore:41 *.log` 排除在版本控制之外 | 重大 | `git ls-files 'schema v0.3' \| grep -c '\.log$'` → 0；修法与实测见 §0.2 |
| **E-01b** | 一个 76.4 MB 的 `graph.json` 越过 GitHub 50 MB 警告线；R-03 预估的合并图（100–200 MB）会被 GitHub 硬拒绝 | 重大 | `schema v0.3/runs/semantic-gottesman-full-thesis-20260919/graph.json` |
| **E-02** | 10,036 行 host Python **零自动化测试、零负例 fixture**（v0.2 的 `host_probe/negative/` 有 14 个） | **阻塞** | `find` 无 `test_*.py`/`conftest.py`；`host/*.py` 无 `import pytest` |
| **E-03** | **宿主自身的 bug 被记成"来源缺陷"**：`except Exception` → `failure_reason="SOURCE_READ_DEFECTIVE"`。失败分类是项目的主要工具，这一条把它污染了 | 重大 | `host/research.py:342-349` |
| **E-04** | PENDING_TESTS 的 218 个 ID 中 132 个（60%）从未执行；103 个复选框**全部未勾选**；对抗性、并发、崩溃恢复、新论文、校准、多节点组合**整块从未执行** | 重大 | `schema v0.1/PENDING_TESTS.md` |
| **E-05** | 六套互不兼容的记录模型、226 个 `.schema.json` 并存；`tests/v3` 指的是 `src/agtxiv_v3` 而非 `schema v0.3`，938 个测试覆盖的是另一条血脉 | 重大 | 见 §9.1 |
| **E-06** | 模型后端是 GUI 应用包内的硬编码路径，无版本固定、回执不记 CLI 版本、单一操作系统 | 中 | `host/model.py:223-227` |
| **E-07** | resume 会先改 SQLite 再触发代码变更守卫（顺序反了）；6 个账本事务中 1 个缺 `BEGIN IMMEDIATE`；连接从不关闭，未启 WAL | 中 | `research.py:122 vs 126-129`；`core.py:184-188` |
| **E-08** | 无运行是逐字节可复现的：4 个标识符每次随机（`uuid4`），审计也不检查可复现性 | 中 | `core.py:175,271`；`research.py:601`；`scheduler.py:117` |
| **E-09** | `runs/` 内有 282 份 host 代码副本（93,710 行）和 74 份 schema 副本，无 diff 工具 | 中 | 快照本身是对的，但目前只写不读 |
| **E-10** | `runs/latest.json` 指向落后两代的运行；9 个陈旧 `.controller.lock` 遗留 | 小 | `runs/latest.json` |
| **E-11** | 中英文分裂：README 英文（2026-09-19 口径），真实边界只在中文 STATUS/REVIEW 里；v0.2 曾为此立过英文规则 | 小 | `schema v0.2/README.md:19` |

### 9.1 仓库层面：同一套概念栈被实现了两遍，有测试的那一遍没在用

| 实现 | 位置 | 行数 | 测试 | 在主线上使用 |
|---|---|---:|---:|---|
| **A** | `src/agtxiv_v3/`（contracts / candidates / dependencies / source / storage / obligations / intake） | 4,074 | **224 个测试函数**（`tests/v3/`） | **否** |
| **B** | `schema v0.3/host/` | 10,036 | **0** | 是 |

两者概念高度重叠。A 在 AgtXIv **协议**阶梯上，B 在 schema **契约**阶梯上。结果：**经过测试的那一套没在跑，真正在跑的那一套一个测试都没有。** 全仓库 `tests/` 有 46 个文件、21,976 行、938 个测试函数，其中 **import `schema v0.3` 的：0 个**。

有意思的是 `schema v0.3/host/` 其实还在运行时反向依赖仓库根代码：`ingest.py:68` importlib 加载 `tools/extract_provisional_claims.py`（789 行），`ingest.py:81` 加载 `src/agtxiv_v3/source.py`（579 行）。所以它既不是自包含的，也没继承对方的测试。

另外，`host/` 的 32 个模块里有 **13 个（2,681 行，27%）从 `research.py` 和 `proof_walk.py` 都不可达**：`pipeline` 388、`case` 115、`roots` 63、`epoch_migration` 548、`extension_migration` 338、`concrete_physlib_bridge` 176 等。

---

## 10. 后续构建建议

排序原则：**先保住已有成果，再把"这条路走不走得通"变成可观测的数字，最后才扩大规模。**

### 10.0 第零优先级：完成提交（今天，10 分钟）

**状态更新（2026-09-20 复核）：`git add` 已完成，`git commit` 尚未执行。** 详细复核见 §0.2。剩下三步：

```bash
cd /Users/Yingjian/Documents/GitHub/AgtXIv
# 1. 把 Lean 编译日志（失败回执）从仓库根的 *.log 规则里救回来
printf '\n# Lean compile logs are failure receipts, not rebuildable output.\n!*.log\n' >> "schema v0.3/.gitignore"
git add "schema v0.3/.gitignore" "schema v0.3"
# 2. 提交
git commit -m "feat(schema-v0.3): track the host, contracts, Lean corpus, docs and run evidence"
# 3. 打包后推送（现在 8,469 个对象全是松散的，没有 packfile）
git gc
git push
```

推送时留意那个 76.4 MB 的 `semantic-gottesman-full-thesis-20260919/graph.json`——GitHub 会警告但会接受。**它与 §10.7 直接相连**：如果不先修掉图产物的二次膨胀，合并深宽两线后的图（预估 100–200 MB）会超过 GitHub 的 100 MB 硬上限，届时根本推不上去。

**为什么这件事仍排第一（从第一性原理说）：** 版本控制不是"整洁"问题，它是**唯一能回答"昨天它还能跑，今天为什么不行"的工具**。`git add` 已经把内容写进了对象库，这一步确实让数据更安全了；但没有 commit 就没有可回退的点，没有 push 就没有异地副本。现在你仍然只能靠手工比对 `runs/*/runtime/` 里那 282 份代码快照来看两天之间改了什么。

### 10.1 第一优先级：把 M1 跑掉（本周，约 $12，约 1 小时）

设计文档 §11 已经把实验设计好了，照做即可：对三个已经有人写 Lean 在盘上的节点，**只跑 Phase 9**，attempt cap 提到 30，参照 Lean 对模型隐藏、只作评分器。

| 目标 | 参照声明 | 类型 |
|---|---|---|
| `claim:perfect-graph-definition` | `AgtXIv.GraphFoundation.IsPerfect` | def，3 行 |
| `claim:mwis-definition` | `AgtXIv.GraphFoundation.maxWeightIndependent` | def，8 行 |
| `claim:sign-alignment-identity` | `AgtXIv.Stabilizerness.max_abs_signed_sum` | theorem，11 行，3 个前置声明，13 条 mathlib 引理 |

**关键的实验设计修正（相对设计文档）：** 那次唯一成功的 proof run 的环境里只有 **2 条声明**，其中一条就是答案。M1 必须避免重复这个错误——**给模型一个真实规模的库**（至少整个 `AgtXIvRootMath` 的 54 条定理 + 9 条定义，理想情况是加上相关的 mathlib 片段），否则测的还是管道而不是能力。

它产出的每一个数字都会改变后续决策：

- `attempts_to_first_compile` 与 `attempts_to_close`，**def 与 theorem 分开统计**。设计文档里"4 attempts per claim"是凭空常数，占全 claim 账单一半以上；MerLean 实测是 22.4 次。差 5.6 倍，整个成本模型作废。
- 真实 token 数，退役"4 字符 = 1 token"估计；缓存命中率，退役由 $343/$673 反推的 0.51 因子。
- **最重要的定性结论：在一个真实规模的库里，模型能不能自己找到该用的声明、并写出类型正确且语义忠实的 Lean。**

**如果三个目标在 30 次尝试内全部失败，整个 S8/S9 路线需要重新设计，而不是继续往 S1–S5 加代码。** 这就是它必须先跑的理由。

**验收：** `runs/m1-measurement-<date>/`，含三个目标各自的 attempt 曲线、token 计数、编译回执，以及一句话结论。

### 10.2 第二优先级：给"终点"一个机器可读的定义（1–2 天，零模型调用）

1. 新增 `CompletedChainCertificate` 定义：非空 `query_declarations`、非空 `premises_from_lean_environment`、每条前提带 `terminal_kind`、每条边带 `composition_witness`、每个节点带 `nonvacuity_witness`（可以是 `NONE`，但必须显式）。把现有 `ChainCertificate` 的四处 `const` 改成枚举。
2. 在 `host/pipeline.py` 加上产生它的分支。
3. **写一份最小可通过的假证书作为 fixture，让 `validate.py` 验证它**——这样"终点"就有了一个可运行的测试，而不只是一段散文。

**为什么重要：** 软件工程里一条朴素但可靠的规律——**没有验收测试的目标不会被达成**，因为没有任何改动能被判定为"更接近了"。先造一个哪怕是玩具的"通过"信号，之后所有工作才有梯度可循。

同时修掉 R-06：`tools/validate_repo.py` 当前那条 v0.3 检查指向被取代两代的产物，对真正的运行器直接 FAIL。一条指向错误目标的绿灯比没有绿灯更糟。

### 10.3 第三优先级：在一篇**故意选得很小**的论文上闭一次环（2–4 周）

不要在 arXiv:2607.26154 上尝试闭环。它需要加权完美图整性、强对偶、饱和性——那是真正的数学工作，会把工程失败和数学失败搅在一起，两边都学不到东西。

**选一篇满足：** 3–8 页；5 条以内 claim；外部依赖全部落在 mathlib 已有内容上（一篇纯组合或初等数论短文）；有 arXiv TeX 源。

目标不是证明有意思的东西，**目标是让 S1→S9 第一次全部真实依次执行一遍**，产出 §10.2 定义的完整证书。允许数学上毫无价值。

这一步会强制暴露所有接口不匹配——尤其是 C-01（`formalization_order` 为空），它在一张小图上会立刻显形且容易调试。

**验收：** 一条命令，从 `--paper <id>` 到一份 `CompletedChainCertificate`，exit 0。

### 10.4 第四优先级：换掉不可判定的终止判据（1 周设计 + 1 周实现）

把"追到最早出处"从系统目标里**删掉**，换成设计文档 §6 已经写好、但尚未实现的**分类终止**。每个 root 必须落到下面某一类：

| 终止类型 | 含义 | 算不算"已解决" |
|---|---|---|
| `LIBRARY_DISCHARGED` | 落到 mathlib/physlib 的具体声明上 | 是 |
| `PROVED_UPSTREAM` | 上游论文里已抽出并形式化的 claim | 是 |
| `TYPED_TERMINAL_PREARXIV` | 前数字化文献（如 Berge 1961） | 否，显式前提 |
| `TYPED_TERMINAL_MONOGRAPH` | 专著 / 教科书 | 否，显式前提 |
| `TYPED_TERMINAL_INACCESSIBLE` | 付费墙 / 检索失败 | 否，显式前提 |
| `BUDGET_HALT` / `DEPTH_HALT` | 预算或深度耗尽 | 否，显式前提 |

**最终报告的诚实度量是"终止类型的计数向量"，不是一个百分比**——设计文档 §7 已经说对了，实现照做。

配套三件小事，都很便宜：

- `host/core.py` 已有 6 个 `TERMINAL_KINDS`，但只有 2 个被产生过；把 `research.py:491` 那句硬编码的 `ARXIV_SOURCE_AVAILABLE` 改成按线索实际类型赋值，`scheduler.py:227` 那条死分支就活了。
- **接上 DOI 解析**。112/152 条请求只带 DOI，而 Crossref 适配器（`ingest.py:888`）只接在废弃路径上。这是闭合前沿最便宜的一根杠杆，现在完全没用。
- **接上 PDF 页区域分支**（C-12）。Lovász 1972 已经真读完了、审计 PASS、10 节点 7 组，就差接进主图，接上之后立刻闭合 8 条请求。

**同时必须解决 C-04 的发散问题。** 建议：外部请求不再无条件生成，而是**只为处在 query 可达路径上、且其下游 claim 已被判定需要该支持的引用**生成。现在的做法是每条 citation key 都造一个请求，所以前沿必然随论文数线性膨胀。

### 10.5 第五优先级：造第一座桥墩——库检索（M1 之后，4–8 周）

只有 M1 给出正面结果才做。最小可辩护实现：

1. **离线索引**（零模型调用）：扩展 `lean/EnvironmentAudit.lean`——它现在只审计**具名**声明（宿主追加 `#agtxiv_audit <name>`），改成遍历 `env.constants` 导出全部 `(name, type, module, docstring)`。约 30 行 Lean。
2. **确定性优先**：先用 Lean 自己的 `exact?` / `apply?` / `rw?` 在宿主侧试一遍。命中虽窄但完全可信，且免费。
3. **语义检索兜底**：对类型 + docstring 做向量检索，取 top-k 交给模型。在 `model_routing.py` 新增第 7 个操作 `library.search`（DECISION 类），走轻模型。
4. **立刻测量**：用 `roots.py` 那 7 条硬编码绑定当 gold set，报 recall@1 / recall@10。7 条太少，但它是现成的真实数据，先有数字再扩大。

**为什么强调"先确定性、再模型"：** 确定性工具的输出无需校准即可信任；模型输出必须先有校准曲线才能进自动门禁，而项目现在连一条都没有（C-07）。能用程序解决的不要交给模型——这也正是设计文档 §1 第二条指令的原话。

**顺带解决 C-02 的一个荒诞后果**：把 `schema v0.3/lean/` 那 293 条声明纳入索引，流水线就不会再一边把完美图对偶报成未证前提、一边旁边躺着一份接近完成的手工证明。

### 10.6 第六优先级：让后半段能消费前半段的图（与 10.3 并行）

`graph.py` 把所有带阻塞项的节点移出 `formalization_order`，而候选抽取产生的节点**全部**带 `CANDIDATE_EXPLORATION_REVIEW_REQUIRED`。

最小改动：在 `CANDIDATE_EXPLORATION` 策略下，`formalization_order` 输出一个**分层 exploratory 队列**——节点仍带全部阻塞标记并向下传播，但不被移出队列。这样 `bottom_up_walk` 能在"全程标记未审阅"的前提下真的走一遍图。不违反证据纪律：所有后代仍保留 `AWAITING_REVIEW`，`promotion_allowed` 仍为 false。

同时做 §6 的两阶段抽取实验，把 221 条悬空内部边降下来——这比改调度器更能提高队列质量。

**验收：** 把 613 节点图交给 `proof_walk.py`，它至少尝试一个节点。

### 10.7 第七优先级：修掉图产物的二次膨胀（1–2 天，纯工程）

39 MB 里 90.0% 是 `edge_criticality`，其中 83.5% 只是同一个 240 元 `query_ids` 列表被写了 3,175 遍。修法很简单：在每条 criticality 记录里存 query 集合的**哈希**（或差集），而不是整份列表；或者把 `edge_criticality` 拆成单独文件，按需生成。

**这不是优化洁癖，是 R-03**：合并深宽两线的图预计 100–200 MB，会直接撞上本轮刚设的 64 MiB 上限。也就是说，"下一步"目前被一个纯冗余问题挡住了。上次的应对是把上限从 10 MiB 抬到 64 MiB，那只买来一次翻倍。

### 10.8 其余（按需，不阻塞主线）

- **修 E-03（半小时，高价值）**：`research.py:342-349` 把任何异常都记成 `SOURCE_READ_DEFECTIVE`。这让你无法区分"论文源码有问题"和"我的代码有 bug"。28/69 次抽取失败中有多少是自己的 bug，目前无从得知。改成按异常类型分流，`SOURCE_READ_DEFECTIVE` 只保留给真正的来源问题。
- **给 `graph.py` 写单元测试**：不需要覆盖率，但这个最复杂、最正确、最值得保护的组件应该有一组小图测试——SCC、AND/OR、共享成本、删边敏感度各两三例。理由很朴素：**它将来一定会被改，而它的正确性不可能靠肉眼复查。** v0.2 的 `host_probe/negative/` 那 14 个负例 fixture 可以直接借鉴。
- **恢复 v0.2 的 `relation_to_source`（C-15）**：现在能验证"模型指向了真实文本"，但没有任何东西验证"它写的 statement 和那段文本意思一样"。v0.2 要求同时给出两种措辞加一个声明的关系，宿主拒绝"声称逐字但两串不同"和"声称改写但没变化"。这是**便宜且直接针对核心风险**的检查，丢掉可惜。
- **把宏表发给模型（C-16）**：现在算了存了但不发。模型遇到 `\Mcal` 而手上没有宏表，只能猜，而猜是不可见的。
- **arXiv 抓取合规（`ingest.py:93-175`）**：`/src` 批量下载没有节流、没有 Retry-After/429 处理、User-Agent 里没有联系邮箱、没查 robots.txt——而 Atom 元数据路径（`arxiv_metadata.py:73-87`）是有节流的。递归一旦真的放大，这是第一个会被封的地方。把 Atom 路径那套节流复用过来即可。
- **合并深宽两线要重新评估（C-09）**：这**不是**一次 import。候选 ID 是内容哈希，两套节点 ID 交集为 0，现有 9 条跨论文匹配判断对新节点集全部失效。要么接受重跑 `dependency.match`，要么放弃宽线的 72 query 结果。另外 `profiles/upstream-evidence-imports.json` 遗漏了 Howard（C-10），按现状执行会丢掉 4 篇之一。
- **产物生命周期**：约 215 MB（32%）是被取代的前缀和失败尝试。失败回执必须留（这是项目优点），但 5 份 Gottesman 章节前缀（112.3 MB）是全文图的严格前缀，可以压缩归档并留一份取代索引。
- **`runs/latest.json` 更新**，清掉 9 个陈旧 `.controller.lock`。

---

## 11. 建议停止或推迟的事

| 停止 / 推迟 | 理由 |
|---|---|
| **继续扩大单篇候选抽取的量** | 72 → 240 没有回答任何未决问题。第 241 条候选的信息增益≈0，而它继续增大那张下游消费不了的图。 |
| **在 arXiv:2607.26154 上尝试闭环** | 它的数学缺口（加权完美图整性 L-01/L-02、饱和性 L-04）是真正的研究工作，会把工程失败和数学失败混在一起。 |
| **新的"纯手工"Lean 模块** | 不是停止写 Lean，而是**改变写法**：今后每写一个新模块，先冻结 claim 文本、先让模型跑、再写人工版本作为 grader。同样的劳动同时产出形式化成果**和**一个 auto-formalization 数据点。现在的写法只产出前者——而且手工 Lean 越多，越难证明系统会自动化。 |
| **Neo4j 投影、web 界面、多 provider 路由** | 都在主线之外。 |
| **再增加 run 目录来记录 `CHAIN_INCOMPLETE`** | 116 个目录、668 MB，全部同一状态。这个信号已经饱和。 |
| **在 `src/agtxiv_v3/` 上继续投入**（除非有明确理由） | 4,074 行、224 个测试，但不在主线上。要么明确宣布它废弃并把有用的测试移植过来，要么明确写出两条血脉的分工。现在的状态是每个新读者都要重新判断一次该读哪个。 |

---

## 12. 给作者的几个问题

这些答案会显著改变上面的排序，审查者无法替你回答：

1. **这个项目的交付物是什么？** （a）一篇关于"自动化论文到证明流水线可行性"的**测量论文**；（b）一个真能用的工具；（c）arXiv:2607.26154 的完整形式化。三个目标的最优路线完全不同。若是 (a)，M1 和校准曲线就是全部重点，S6/S8 的不可判定性本身就是论文的一个结论；若是 (c)，手工 Lean 是正路，整个 `host/` 流水线其实是绕路。
2. **你愿意接受"最早出处"这个目标被替换掉吗？** §10.4 是审查者能给出的最诚实建议，但它确实削减了原始目标。
3. **有没有可能找一个 Lean/mathlib 方向的合作者？** 剩下的数学缺口（L-01 到 L-05）是有分量的形式化工作，是目前剩余工作量里最大的一块。其中 L-03 的桥接阻塞只差一个 2 行补丁，那个可以自己做。
4. **算力 / 额度预算的实际上限是多少？** 设计文档给出的 load-bearing 深度 3 估算是 $405，全 bibliography 深度 3 的实测是 $24,915。差两个数量级，而当前实现没有任何机制阻止后者——§10.4 的收敛机制正是为此。

---

## 13. 附录：本次审查核对过的关键事实与路径

| 结论 | 核对路径 / 命令 |
|---|---|
| `schema v0.3/` 已 add、未 commit（2026-09-20 复核） | `git ls-files 'schema v0.3' \| wc -l` → 3,389（暂存）；`git log -- "schema v0.3"` 为空；HEAD = `39e9d03`（2026-09-17） |
| 证据字节能安全通过 git | `.gitattributes` `* -text`；实测 3 个文件的 `git show :<path>` 与磁盘 SHA256 全部一致 |
| 225 个 Lean 编译日志被排除 | `git check-ignore -v` → 仓库根 `.gitignore:41 *.log`；`git ls-files 'schema v0.3' \| grep -c '\.log$'` → 0 |
| 最大 blob 76.4 MB（GitHub 50 MB 警告线） | `runs/semantic-gottesman-full-thesis-20260919/graph.json` |
| 对象库 8,469 个松散对象 / 228.20 MiB / 0 packfile | `git count-objects -vH` |
| `formalization_order` = 0 | `runs/research-terra-continuation-20260920/graphs/00001-db0e3d21/graph.json` |
| Gottesman 图 `formalization_order` = 34 | `runs/semantic-gottesman-full-thesis-20260919/graph.json`（618 节点） |
| 634 边 / 41.2% 解析率 | 按 `support_groups[].members` 的节点 kind 统计 |
| 613 节点构成 | 221 `unresolved_claim_occurrence` / 154 `claim` / 152 `external_claim_request` / 38 `definition` / 34 `equation` / 5 `lemma` / 5 `theorem` / 4 `proposition` |
| 400 root 全 FRONTIER，373 是占位符 | `graph.json: roots` |
| 递归发散 31→82→120→148 | `runs/research-four-paper-20260919` 图快照 00001/00005/00009/00013 |
| 152 条外部请求的身份分布 | `assembly.json` × `host/research.py:91 candidate_paper()` |
| 74 次模型调用 / 1 次 autoformalization | 全部 38 份 `ledger.json` 的 `calls` 聚合 |
| 唯一一次 auto-formalization 及其 2 声明库 | `runs/proof-worker-normalization-attempt02-20260919/`；`runs/proof-worker-environment-attempt04-20260919/environment.json` |
| 1 节点手工图 | `runs/proof-worker-normalization-attempt02-20260919/candidate-root-audited-graph.json` |
| 7 条硬编码根绑定，只被废弃路径引用 | `host/roots.py:6-18,45`；`grep 'import roots'` |
| 无库检索 | `grep -rn "loogle\|moogle\|library_search\|exact?\|apply?" host/*.py` → 零命中 |
| 6 个模型操作 | `host/model_routing.py:11-15` |
| `origin_evidence` 无生产者 | `grep -rn origin_evidence host/ schemas/` → 仅 `graph.py:511,517`、`pipeline.py:83` |
| 成功证书不可表示 | `schemas/research.schema.json` ChainCertificate 四处 `const`；`host/pipeline.py:152` |
| M1 三目标从未尝试 | `grep -rl` 三个 claim ID 于 `runs/*/proof-walk-result.json`、`runs/*/summary.json` → 零命中 |
| Berge 1961 不可达 | `runs/origin-berge-1961-followup-20260919/observations.json` |
| 深宽两线无法机械合并 | 132 个宽线节点 ID 与 613 节点图交集 0；文本交集 2（模板句） |
| 两个 Lean 模块从未编译 | `lean/PerfectGraphIntegerCover.lean`、`lean/PerfectGraphWeightedApproximation.lean`；全仓库 grep |
| 桥接层阻塞 + 2 行补丁 | `epoch-migration/runs/20260919-perfect-weak-extension/progress.json`；`.../20260919-graph-bounds-perfect-replication/adaptations/002-true-twin-Std-Symm-api.diff` |
| 82 模块 epoch 迁移 | `epoch-migration/runs/20260919-full-case/full-case-audit.json`（`leanprover/lean4:v4.33.0`，mathlib `db584cd6…`，physlib `7b6e0fee…`） |
| 零测试 / 零负例 | `find 'schema v0.3' -name 'test_*.py' -o -name 'conftest.py'` → 空 |
| 938 个仓库测试，0 个覆盖 v0.3 | `tests/`（46 文件 / 21,976 行）；`tests/v3` → `src/agtxiv_v3` |
| 宿主 bug 记成来源缺陷 | `host/research.py:342-349` |
| 图产物 90% 是诊断冗余 | `graph.json` 逐字段字节统计（本审查直接测得）：`edge_criticality` 35,321,697 B / 39,249,196 B = 90.0%；3,175 份重复的 240 元 `query_ids` = 32,769,175 B = 83.5% |
| CI 检查指向被取代产物 | `tools/validate_repo.py:363-370`；`validate.py` 对 terra 运行 → `{"integrity":"FAIL"}` |
| PENDING_TESTS 60% 未执行 | `schema v0.1/PENDING_TESTS.md`：218 个 ID，103 个复选框全未勾选 |
| 模型后端 | `host/model.py:223-227`；`MAX_MODEL_INPUT_BYTES = 1.5 MiB`（`model.py:24`） |
| 磁盘 | `schema v0.3` 732 MB，`runs/` 668 MB（91%），`epoch-migration/runs` 61 MB |

---

**本次审查未做的事：** 未运行任何测试套件；未重跑任何 Lean 构建；未发起任何模型调用；未修改仓库任何文件（本文件除外）。唯一执行过的程序是只读的 `host/audit_research.py`（对 6 个 research 运行，全部 PASS）——顺带发现它此前**从未被执行过**，STATUS.md 和 REVIEW-2026-09-20.md 中的运行完整性说法此前依据的是控制器自报，而非项目自己写的独立审计器。
