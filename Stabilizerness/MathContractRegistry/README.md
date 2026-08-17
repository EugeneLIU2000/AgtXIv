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
│   └── math-contract.schema.json
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
- `acceptance_effect=NONE_FROM_REGISTRY`。

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

然后打开 `http://localhost:8000/Stabilizerness/MathContractRegistry/demo/`。Demo 使用 vendored `d3-dag` 1.2.2 Sugiyama layout，在同一张 Mathematics 主图中展示全部 65 个 mathematical interfaces、13 个 query-level Agent/root nodes 和 114 条 canonical mathematical dependencies。所有 interface 始终按真实 Registry status 着色；不存在 dependency 的节点仍显示，但不会生成推测边。Agent 与 interface 的包含关系使用稳定 owner code `A01`--`A13` 编码：Agent 圆和其所有 interface dots 显示同一 code，悬停任一侧会联动强调 owner 与全部 sibling interfaces；该 membership 编码没有箭头，也不表示逻辑推导。Target Agent 和 Query Interface 下拉框可以切换查询视角，系统沿 canonical incoming edges 计算 backward ancestor closure，只加亮当前线路，其他节点保持原状态颜色并降低视觉权重。每条有向边都必须在运行时通过三项检查后才显示：edge type 属于 definition/theorem/scope dependency，方向与 target contract 的对应 import field 一致，并且有非空 reason；整个 65-node graph 还必须通过 acyclicity 检查。因此图中箭头严格解释为 prerequisite `->` dependent conclusion，而不是 Agent ownership 或经验因果。Agent 圆内只显示 `ROOT AGENT` 或 `TARGET AGENT`；外圈绿色 progress arc 按该 Agent 所有 mathematical interfaces 中 `EXISTING_PROJECT_DECLARATIONS` 的比例填充，精确百分比只在 hover/focus 时显示。绿色 interface tooltip 保证至少包含一个 Lean module source link；点击 interface 可以固定 tooltip 并打开 `.lean` 源文件。完整身份和数学内容仅在鼠标悬停或键盘聚焦时显示。顶部还可以切换 Mathematics、Computation、Physical Semantics 和 Empirical Evidence；第一版只为 Mathematics 注册真实关系，其余 profile 显示明确空状态，不生成推测边。Demo 只读展示工件，不执行 Lean，也不修改任何验收状态。
