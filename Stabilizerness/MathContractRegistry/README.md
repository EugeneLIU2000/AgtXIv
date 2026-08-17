# Stabilizerness MathContractRegistry

`MathContractRegistry` 是 AgtXIv 的 math-first 接口层。它把 `Stabilizerness/dag/claim-dag.json` 中的每个节点登记成统一合同，但不声称每个节点都是数学定理，也不为缺失证明制造 Lean 占位符。

## 设计边界

- 原始 whole-paper DAG 仍是 `Stabilizerness/dag/claim-dag.json`。
- 已有 Paper Agent、source、verification、export 和 blocker 文件保持原位。
- 已有 Lean 代码仍位于 `formal/AgtXIvRootMath/` 与 `formal/AgtXIvVarela/`。
- 本目录集中保存数学接口、DAG imports、Lean bindings、复用检索候选和 Demo。
- Registry 不改变任何 `accepted`、verification 或 blocker 状态。

## 目录

```text
MathContractRegistry/
├── README.md
├── manifest.json
├── schema/
│   ├── math-contract.schema.json
│   └── dependency-edge-evidence.schema.json
├── contracts/
│   └── contracts.json
├── mappings/
│   └── claim-to-lean.json
├── reuse/
│   ├── leansearch-v2-results.json
│   ├── pinned-source-checks.json
│   └── reuse-assessment.md
└── demo/
    ├── data/
    │   └── claim-dag.en.json
    ├── vendor/
    │   ├── d3-dag-1.2.2.iife.min.js
    │   ├── d3-dag-LICENSE.txt
    │   └── manifest.json
    ├── index.html
    ├── styles.css
    └── app.js
```

## 每个节点的统一接口

每条合同都包含：

- whole-paper DAG node ID、kind、status 和 branch；
- normalized mathematical statement，或对非数学节点明确记为 `null`；
- source reference、Paper Agent、Statement 和 ReasoningStep；
- assumption、definition、theorem 和 data imports；
- downstream nodes；
- 现有 Lean declarations、源码模块、计划声明、LeanSearch v2 候选和 verification references；
- exports、blockers、mapping status；
- query-relative external resolution state；
- `acceptance_effect=NONE_FROM_REGISTRY`。

## Unresolved External Mathematical Source

`external_resolution.status` 只能取：

- `NOT_APPLICABLE`；
- `SOURCE_FOUND_AND_VERIFIED`；
- `INDEPENDENT_LEAN_PROOF_COMPLETED`；
- `BLOCKING_UNRESOLVED_CLAIM`。

当前 8 个 unmapped external mathematical interfaces 均保守标为 `BLOCKING_UNRESOLVED_CLAIM`。它们仍是 claim-level interfaces，不会自动生成虚拟 Root Agent。只有当该节点进入选定 query 的 backward closure 时，才进入该 query 的 $U(q)$ 并阻断 `DAGComplete`。

每条 DAG edge 还包含 `evidence`，分别记录 Oracle、source alignment、Lean support 和 disposition。当前 whole-paper edge set 全部保持 `ORACLE_PROPOSED`、`UNREVIEWED_AT_EDGE_LEVEL`、`NOT_EXTRACTED` 和 `CANDIDATE`；这批字段使 Demo 可以明确展示尚未完成 edge-level verification，而不是把结构化边误作 accepted dependencies。

## Lean 状态

- `EXISTING_PROJECT_DECLARATIONS`：已有工程和记录提供 declaration 映射；不是重新验证。
- `PLANNED_DELTA`：现有 formalization contract 点名了计划声明，但源码尚未实现。
- `EXTERNAL_OR_UNMAPPED`：外部 root/foundation 尚无本地 Lean 绑定。
- `GAP`：数学节点存在，但当前文件没有 Lean declaration。
- `NOT_APPLICABLE`：empirical protocol、empirical claim、limitation 或 open problem；不伪装成 Lean theorem。

## 与旧工件的关系

本 Registry 保留并集中引用以下 math-only 工件，而不移动或复制其证明源码：

- `Stabilizerness/agtxiv/lean/declaration-index.json`；
- `Stabilizerness/agtxiv/dag/claim-dag-index.json`；
- `agents/*/knowledge/statements.jsonl`；
- `agents/*/reasoning/chains.jsonl`；
- `agents/*/formal/*.json`；
- `agents/*/exports/*.json`；
- `formal/AgtXIvRootMath/`；
- `formal/AgtXIvVarela/`。

以后可逐步把稳定数学合同提升到共享的跨论文 Registry；Root 不是永久层级，而是某次 query 反向搜索的停止点。

## 复用检索边界

`reuse/leansearch-v2-results.json` 保存公共 LeanSearch v2 标准模式返回的候选，`reuse/pinned-source-checks.json` 记录其中关键 declaration 在固定 Mathlib checkout 中的源码位置。源码存在性检查不是 elaboration 或 kernel verification；这些对象仍只是候选：

1. 必须核对 exact Lean type；
2. 必须核对 pinned Mathlib 版本中是否存在；
3. 必须核对 source mathematics 与 candidate semantics；
4. 只有在工程中实际 import 并完成现有审计流程后，才能替代本地证明。

本轮没有把远程候选直接写入现有 Lean 工程，也没有把搜索命中标成 `KERNEL_CHECKED`。

## 运行只读 Demo

从仓库根目录启动任意静态文件服务器，例如：

```sh
python3 -m http.server 8000
```

然后打开 `http://localhost:8000/Stabilizerness/MathContractRegistry/demo/`。Demo 使用 vendored `d3-dag` 1.2.2 Sugiyama layout，展示 65 个 mathematical interfaces、5 个 mapped Paper Agents 和 114 条 typed Oracle candidate dependencies。8 个 unresolved external mathematical interfaces 保持 claim 节点，不再伪装成 query-level Root Agents，也不进入 Target Agent 下拉框。

Target Agent 和 Query Interface 下拉框沿 candidate incoming edges 计算 backward closure。query status panel 显示 closure size、candidate edges、Lean-linked nodes、GAP、PLANNED_DELTA、visible blockers、$U(q)$、`DAGComplete` 和 `VerificationClosed`。`DAGComplete` 仅在 unresolved frontier 非空时安全地显示 `FALSE`；如果 frontier 为空但 edge review 仍处于 Oracle candidate 阶段，则显示 `NOT EVALUABLE`，不会提前宣称完成。

Agent 外圈表示 `Lean-linked coverage`，只统计 `EXISTING_PROJECT_DECLARATIONS`，不再命名为 verified coverage。interface tooltip 显示 DAG、mapping、Lean 和 external resolution states，并公开 blockers、verification references、Mathlib/project reuse candidates 与 Lean source links。每条 edge 在运行时检查 type、方向、reason 和 evidence state；图中高亮只改变视觉权重，仍保留 claim/theorem、definition 和 scope 三种语义。Demo 是只读的 Oracle-candidate Registry projection，不执行 Lean、不做 proof-guided pruning，也不修改 acceptance status。
