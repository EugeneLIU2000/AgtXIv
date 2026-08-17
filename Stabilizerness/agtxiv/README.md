# Stabilizerness AgtXIv canonical overlay

本目录是一个**非破坏式兼容视图**。它不复制论文科学内容，不替换 `Stabilizerness/dag/claim-dag.json`，也不移动、重命名、删除或修改历史工件。所有条目都通过工作区相对路径指向既有来源、Paper Agent、Lean 工程和验证记录。

本 overlay 没有重新运行 Lean、validator、测试、哈希检查或科学正确性审查。`PASSED`、`FAILED`、`KERNEL_CHECKED`、`BLOCKED` 等词只转述被索引文件中的现有记录。overlay 不改变任何 node、edge、verification、export 或 blocker 状态，也不把候选依赖提升为 accepted dependency。

## 1. 核心原则：只形式化 local mathematical delta

理想链条是：

```text
Root Agent Lean exports
  → Intermediate Paper Agent imports Root API + proves only its local delta
  → Target Paper Agent imports Root/Intermediate APIs + proves only its local delta
```

在当前工作区中：

- Root proof base 是 `formal/AgtXIvRootMath/`。其默认入口 `formal/AgtXIvRootMath/AgtXIvRootMath.lean` 导入 `AgtXIvRootMath.RootMathCompletion`。
- Intermediate delta 的现有实例是 `formal/AgtXIvVarela/`。`formal/AgtXIvVarela/lakefile.toml` 通过本地 package dependency 引入 `formal/AgtXIvRootMath/`；`formal/AgtXIvVarela/AgtXIvVarela/MeasurementProjection.lean` 显式导入 `AgtXIvRootMath.RootMathCompletion`。
- Target delta 目前只在 `agents/graph-theoretic-nonstabilizerness/formal/formalization-contract.json` 中排队；现有文件称 `Stabilizerness.max_abs_signed_sum` 与 `Stabilizerness.relaxed_vertices_affineSpan` 尚未实现。

下游应优先依赖稳定的 `ROOT_EXPORT`，而不是 `ROOT_INTERNAL_LEMMA`。本 overlay 的角色只是建议分类；它没有改变 Lean 源码的可见性或导入行为。

## 2. Overlay 文件

| 路径 | 作用 |
|---|---|
| `Stabilizerness/agtxiv/manifest.json` | overlay 版本、target paper、canonical DAG、agents、Lean projects 与历史入口。|
| `Stabilizerness/agtxiv/dag/claim-dag-index.json` | 为 74 个 whole-paper DAG nodes 建立保守 AgtXIv 映射；不复制节点的科学正文。|
| `Stabilizerness/agtxiv/lean/declaration-index.json` | 索引 Root 与 Varela 的源码显式 module imports、现有记录列出的 Lean declarations，以及排队中的 target declarations。|
| `Stabilizerness/agtxiv/agents/node-agent-index.json` | 逐节点记录现有 Paper Agent 或 `UNMAPPED`/`NON_MATHEMATICAL`，并给出可恢复的 Lean process。|
| `Stabilizerness/agtxiv/archive/index.json` | 按 source、reader、DAG、Paper Agent、Lean、review、computational、verification、blocker 分类历史路径。|

## 3. 对象隔离

- **Canonical dependency DAG**：`Stabilizerness/dag/claim-dag.json`。节点是 scientific claims、roots、foundations、empirical objects 和 limitations；边是 scientific、definition、scope 或 data dependency。
- **Domain-specific graph**：论文中的 Pauli frustration graph 与 Pauli product-relation structure。它们是数学对象，不是 AgtXIv dependency edge；代表性图像在 `Stabilizerness/arXiv-2607.26154v1/fig1.pdf` 和 `Stabilizerness/reader/assets/fig1.png`。
- **Reader artifacts**：`Stabilizerness/reader/`；用于阅读重构，不是 accepted proof。
- **Source artifacts**：`Stabilizerness/arXiv-2607.26154v1/` 和各 `agents/*/source/`。
- **Paper Agent artifacts**：`agents/*/knowledge`、`reasoning`、`formal`、`verification`、`exports`、`blockers` 等。
- **Lean artifacts**：`formal/AgtXIvRootMath/` 与 `formal/AgtXIvVarela/`；`.lake/` 缓存不进入 overlay 的手写源码索引。
- **Historical/auxiliary artifacts**：根目录 `graph/*.json`、`roots.json`、`pilot-scope.json`、`coverage.json`、`release-manifest.json` 及 review/computational 工件。

## 4. 映射状态

- `MAPPED`：现有文件提供直接、一对一映射。
- `PARTIAL`：可由现有 formal contract、Statement 或命名恢复语义对应，但缺少显式 `same_as` 或一对一 declaration map。
- `UNMAPPED`：当前文件未提供足够对应关系。
- `NON_MATHEMATICAL`：经验 protocol、empirical claim、limitation 或 open-problem marker；不强求 Lean declaration。
- `GAP`：预期接口已被现有合同点名，但实现或映射缺失。

本 overlay 不为 `UNMAPPED` 节点虚构 Paper Agent，也不假设一个 DAG node 必须对应一个独立代理。

## 5. 建议阅读入口

1. `Stabilizerness/CURRENT_ARTIFACTS_SYNTHESIS.md`：完整中文综合报告与增量接口检查。
2. `Stabilizerness/agtxiv/manifest.json`：机器入口。
3. `Stabilizerness/agtxiv/dag/claim-dag-index.json`：whole-paper node 映射。
4. `Stabilizerness/agtxiv/lean/declaration-index.json`：Root exports、internal lemmas、intermediate delta 与 target gaps。
5. `Stabilizerness/agtxiv/agents/node-agent-index.json`：从 node 到 agent/process 的保守追踪。
6. 原始科学图始终回到 `Stabilizerness/dag/claim-dag.json`；发布状态始终回到 `release-manifest.json`。
