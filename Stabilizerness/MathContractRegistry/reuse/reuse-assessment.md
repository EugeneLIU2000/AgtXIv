# Lean declaration reuse assessment

本记录比较现有/计划的 AgtXIv 数学接口与 LeanSearch v2 返回的候选。检索日期为 2026-08-16。关键候选的固定 Mathlib 源码位置另见 `pinned-source-checks.json`。搜索命中和源码存在性都不是目标实例的类型检查、构建或科学验收。

## 可以直接复用的抽象子结论

### 有限群平均投影

现有 `formal/AgtXIvRootMath/AgtXIvRootMath/GottesmanGroupAverage.lean` 已直接使用 Mathlib：

- `Representation.averageMap_invariant`；
- `Representation.averageMap_id`；
- `Representation.isProj_averageMap`；
- module：`Mathlib.RepresentationTheory.Invariants`。

其中 `AgtXIv.Gottesman.groupAverage_isProjection` 的证明体已经只是 `ρ.isProj_averageMap`。因此不应重新证明抽象群平均投影；保留 AgtXIv wrapper 的理由只能是稳定命名、source alignment 和领域接口。

### 紧集上的最小值存在

`formal/AgtXIvRootMath/AgtXIvRootMath/FiniteAtomAttainment.lean` 已使用：

- `IsCompact.exists_isMinOn`；
- module：`Mathlib.Topology.Order.Compact`。

本地 delta 是证明候选集非空、闭、有界/紧，并把 generic minimum 转成 `IsL1Minimizer`；极值定理本身无需重证。

### 线性映射与凸包

LeanSearch v2 返回：

- `LinearMap.image_convexHull`；
- `IsLinearMap.image_convexHull`；
- module：`Mathlib.Analysis.Convex.Hull`。

它们可简化 projected stabilizer polytope 的 generic top-down 语义，但不能替代 Varela V-representation 中的 maximal-context candidate physicality、projected-atom refinement 或 extremality。

## 能显著缩小 target local delta 的候选

### Relaxed vertices 的 affine span

强候选：

- `AffineSubspace.affineSpan_eq_top_iff_vectorSpan_eq_top_of_nonempty`；
- `affineSpan_singleton_union_vadd_eq_top_of_span_eq_top`。

这意味着计划声明 `Stabilizerness.relaxed_vertices_affineSpan` 不必从 affine span 定义展开。局部证明可缩成：

1. 给出一个 relaxed vertex；
2. 对每个坐标构造两个只差该符号的 vertices；
3. 证明这些差向量生成坐标基；
4. 调用现有 affine-span API。

两个 declaration 均已在固定 Mathlib checkout 中找到。Target-local theorem `AgtXIv.Stabilizerness.affineSpan_eq_top_of_vectorSpan_eq_top` 已使用第一个 API 并通过 elaboration；它只完成 generic reduction，尚未构造 paper-specific coordinate differences，因此 `claim:relaxed-affine-span` 仍保持 `PLANNED_DELTA`。

### Free-sign 最大化

候选：

- `Finset.abs_sum_le_sum_abs`；
- module：`Mathlib.Algebra.Order.BigOperators.Group.Finset`。

它给出

\[
\left|\sum_i f_i y_i\right|\leq \sum_i |y_i|.
\]

它只直接替代上界。Target-local module `formal/AgtXIvStabilizerness/AgtXIvStabilizerness/LocalDelta.lean` 另外构造达到等号的 sign choice，并处理常数 `μ`；`AgtXIv.Stabilizerness.max_abs_signed_sum` 已通过 target build 和 axiom audit。该结果关闭 `claim:sign-alignment-identity`，但不自动关闭仍缺 LP-to-MWIS bridge 的 `claim:relaxed-mwis-dual`。

## 只有结构相似、不能直接替代

### 反对易期望值的二范数界

候选包括：

- `Orthonormal.sum_inner_products_le`；
- `CliffordAlgebra.ι_mul_ι_mul_of_isOrtho`。

前者是 Bessel inequality，后者是 Clifford algebra anticommutation。它们与目标结构相关，但仍缺少从 density operator、Hermitian involutions 和 pairwise anticommutation 到这些抽象 API 的语义桥，不能直接宣称替代 `claim:anticommuting-l2-bound`。

### Perfect-graph weighted duality

检索只返回 complement、clique 和 independent-set 的基础 API，例如：

- `SimpleGraph.isMaximumIndepSet_compl`；
- `SimpleGraph.isMaximumClique_compl`。

当前未找到 weighted stable-set/fractional clique-cover duality 或目标 antiblocker identity 的精确 Mathlib declaration。因此：

- `root:perfect-graph-weighted-duality` 仍是外部 foundation；
- `claim:perfect-graph-antiblocker` 仍是 blocker/GAP；
- 基础 graph declarations 只能减少定义工作，不能关闭承重 theorem。

### Stochastic l1 contraction

LeanSearch v2 没有返回与现有有限 row-stochastic coefficient kernel 精确匹配的 l1 contraction theorem。`Matrix.l2_opNorm_le_one_of_mem_doublyStochastic` 是 l2 且要求 doubly stochastic，不是当前接口的替代。

## 对 LeanGraph/TheoremGraph 的使用结论

TheoremGraph/LeanGraph 适合提供 declaration-level dependency 和 informal/formal matching；LeanSearch v2 适合给出 semantic candidates 和 global premise groups。当前 Registry 应把它们当作候选发现层，而不是 acceptance oracle：

```text
candidate retrieval
→ exact type check in pinned environment
→ source/assumption alignment
→ local integration
→ existing verification workflow
→ reusable contract
```

最有价值的近期提效点不是删除所有本地 wrappers，而是：

1. 将 exact Mathlib theorem 记录成 imported declaration；
2. 只保留 source-aligned wrapper 和 paper-specific bridge；
3. 对 target affine-span 与 sign-max proof 先使用已有通用 API；
4. 对 weighted perfect-graph theorem 保持明确 GAP，不用近似搜索结果冒充证明。
