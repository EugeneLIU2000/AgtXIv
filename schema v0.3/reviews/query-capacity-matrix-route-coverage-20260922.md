# 容量命题：矩阵路线的实际覆盖边界

结论：新矩阵路线的源码到达了带条件的上界，但没有完成原文整个命题，也不能替代对原文 F₂ 证明内部依赖的抽取。所有列出的 Lean 声明均为候选；本次只读来源和代码，未编译或运行校验。

## 本次读取的来源

- `Stabilizerness/arXiv-2607.26154v1/draft.tex`：第 287–289 行的正文上界；第 796–805 行的 Universal ceiling 命题；第 809–823 行的证明入口和 F₂ Gram 矩阵；第 875–884 行的唯一依赖、JW 构造及等价结论。
- `profiles/query-perfect-branch-audit.json` 已定位候选节点 `claim:candidate:e63f20587f624a1d472f6f83`，其绑定状态仍为语义未审阅。这里沿用该定位，不重新计算源摘要，也不签发新的 DeclarationBinding。
- 当前矩阵路线入口：`lean/ReducedRoMMatrixDimensionCeiling.lean`。

## 条款与候选对应

| 原文数学内容 | 当前候选位置 | 尚未满足的要求 |
| --- | --- | --- |
| n 比特 Pauli 团的大小不超过 2n+1 | PauliCliqueMatrixBound.clique_card_le_two_mul_add_one | 新链未编译；历史一般单位族来源尚未接受 |
| 可解条件下，每个态的 reducedRoM 不超过 √(2n+1) | ReducedRoM.MatrixRoute.reducedRoM_le_sqrt_dimension_ceiling | 依赖 NoActiveDependencies、IsPerfect 和旧容量桥接；不是无条件全体窗口结论 |
| 可解窗口的 witness capacity 不超过该值 | ReducedRoM.MatrixRoute.witnessCapacity_le_sqrt_dimension_ceiling | witnessCapacity 与原文 sup 的定义及定义域仍需审阅；上界不证明达到性 |
| 对所有可解窗口取最大值等于该值 | SolvableWindowCapacityMaximum.sqrt_dimension_isGreatest_solvableWindowCapacities（实际命名空间 AgtXIv.ReducedRoM） | 旧候选依赖 JW 达到性，要求 n>0；矩阵路线没有独立覆盖此条款 |
| 一个给定可解窗口容量达到上界，当且仅当其团数为 2n+1 | ReducedRoMDimensionCeiling.witnessCapacity_eq_ceiling_iff_cliqueNum（实际命名空间 AgtXIv.ReducedRoM） | 旧候选仍未编译；需容量等于 √团数及两边的实数/自然数对应 |
| 团数条件等价于存在 2n+1 个两两反对易 Pauli 成员 | CapacityAnticommutingCriterion 的两个 iff 候选 | 仍需旧反向论证及来源对齐；数值上界不能单独证明等价 |
| 最大团的唯一非平凡依赖覆盖全部成员且不活跃；JW 集合满足可解条件 | 既有 F₂/JW/唯一依赖候选链 | 这是原证明的额外数学声明，新矩阵维数界没有给出依赖唯一性，不能从覆盖清单删除 |

表中的文件名前缀用于定位，不是 Lean 声明命名空间。精确 namespace 和类型应在获准编译后的声明审计中核对，不能据此表声称七项已经证明。

## 必须保留的路线区别

原文在正文引用 Sarkar 的上界，但附录的这个证明实际从二进制辛向量和 Gram 矩阵开始推导。一般可逆反对易矩阵族的路线可以支持同一个上界结论，却不证明自己就是附录的逐步来源证明。

后续图中应把原文 F₂ 证明与新矩阵推导视为待审阅的不同路线。新路线不能覆盖或删除原文的 F₂ 秩、核、唯一依赖和 JW 构造节点；也不能因为最终数值相同，就把 Robert/Hurwitz 的引用自动当作原文每一步的直接支持。

## n=0 的范围问题

本次读取的命题句没有显式写 n>0，而现有外层最大值候选要求 n>0。MeasurementWindow 同时要求非空窗口和非零 Pauli 支持；在零比特支持空间里，不存在满足这两项要求的窗口。因此，当前形式化域下不能直接对 n=0 声称存在一个达到该最大值的窗口。

后续来源阅读补充：Background 第 114 行明确选择非恒等 Pauli（模相位）；第 763 行的容量界证明明确使用非空测量集合，从而团数至少为 1。本次对正整数、n>0 等表述的文本搜索没有找到统一的显式声明，但搜索结果不能证明全文不存在其他约定。当前证据更支持：非空和非恒等是该容量证明实际使用的域条件。

`lean/MeasurementWindowDimensionDomain.lean` 已写出未编译的 qubit_count_pos / no_zero_qubit_window 候选，从现有窗口定义推出 n>0：零比特支持空间通过 coordinateEquiv 对应空指标上的函数对，只有零元素，与已选观测量的非零支持矛盾。因此对已给定的规范化窗口，n>0 可从定义推出；对固定 n 的外层最大值存在性，仍须保证定义域非空。

这不是对原文错误的最终裁定。后续需明确空测量集合是否允许及其 reducedRoM 约定，不能静默把现有 MeasurementWindow 的非空条件扩展成论文所有声明的全局定义。对任意已给定窗口的上界与“存在达到上界的窗口”仍须分开审阅，前者在空定义域下可能真空成立，后者不行。

## 后续动作

优先取得获准的执行证据和源条款对齐，而不是继续为同一上界复制更多候选。已有 F₂ 达到性、等价和最大值代码应复用；如需要使用矩阵路线组装完整命题，只替换上界支持，并保留达到性与唯一依赖的原有未决义务。实际恢复、编译和审计权限尚未收到，不执行。
