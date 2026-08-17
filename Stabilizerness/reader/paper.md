# Graph Theoretic Approach to Quantum Nonstabilizerness

> Yingjian Liu, Albert Gasull, Mengyao Hu, Ruiyun Zhang, Flavio Baccari, Jordi Tura · arXiv:2607.26154v1 · 首轮中英对照阅读稿

本阅读稿服务于 AgtXIv 首个实现切片：完整覆盖摘要、问题设定、核心定义、主定理、Clifford 协变、数值结论和展望；附录只纳入闭式公式依赖链的关键证明段。未纳入的附录分支在 `translation_notes.md` 中显式列出，不能把本稿误称为全文翻译完成版。

## 阅读导航

1. [一句话物理图像](#一句话物理图像)
2. [术语表](#术语表)
3. [摘要](#b001-摘要)
4. [有限测量窗口与投影多面体](#b002-有限测量窗口与投影多面体)
5. [图骨架与符号细节](#b003-图骨架与符号细节)
6. [符号松弛和 Pauli-active dependency](#b004-符号松弛和-pauli-active-dependency)
7. [从自由符号到最大权独立集](#b005-从自由符号到最大权独立集)
8. [Perfect graph 闭式公式](#b006-perfect-graph-闭式公式)
9. [Clifford 旋转与覆盖率](#b007-clifford-旋转与覆盖率)
10. [数值图与测量族](#b008-数值图与测量族)
11. [证明链的关键局部段](#b009-证明链的关键局部段)
12. [展望](#b010-展望)

## 一句话物理图像

只测有限个 Pauli 方向，相当于从一个有限窗口看完整稳定子多面体的影子；反对易图给出“哪些方向不能同时确定”的骨架，Pauli 乘积关系再决定共同测量语境里哪些正负角点真正物理允许。

## 术语表

| English | 中文 | 本文中的直觉 |
|---|---|---|
| stabilizer state | 稳定子态 | 纯稳定子态由一个 maximal commuting Pauli 群的本征值刻画；稳定子多面体再取所有纯稳定子态的凸包 |
| nonstabilizerness / magic | 非稳定子性 / magic | 超出稳定子凸包、支持通用量子计算的资源 |
| robustness of magic | magic 稳健性 | 把目标写成稳定子态带符号仿射组合时所需的一范数 |
| reduced stabilizer polytope | 投影稳定子多面体 | 完整稳定子多面体在有限 Pauli 坐标窗口中的影子 |
| V-representation | 顶点表示 | 显式给出一个多面体作为候选顶点集合的 convex hull |
| frustration graph | 反对易图 | 节点是 Pauli，边表示反对易 |
| commuting context | 共同测量语境 | 一组两两对易、可联合测量的 Pauli |
| maximal independent set | 极大独立集 | 再加任何节点都会破坏独立性；不等于基数最大的 maximum independent set |
| maximum-weight independent set | 最大权独立集 | 在可共同测量集合中选择总权重最大的一个 |
| clique / clique number | clique / 最大 clique 大小 | 两两反对易集合 / 其中最大集合的大小 |
| perfect graph | perfect graph | 每个诱导子图都满足着色数等于最大 clique 大小 |
| outer relaxation | 外松弛 | 加入伪角点而扩大可行多面体，因此给出的 RoM 只会更小 |
| witness capacity | witness 容量 | 固定测量窗口后，对所有状态的 reduced RoM 取上确界 |
| detection coverage | 检测覆盖率 | 在指定状态样本、旋转策略与阈值下被检出的比例 |
| Pauli-active dependency | Pauli-active 乘积依赖 | 完全位于共同测量语境内、会限制联合本征值正负号的最小乘积关系 |
| Clifford covariance | Clifford 协变 | 旋转测量窗口但保留反对易、乘积关系和容量 |

## B001 摘要

**Original · `draft.tex:68–75`**

> Detecting nonstabilizerness requires full tomography and an optimization over exponentially many stabilizer states. A limited Pauli measurement set promises resource-efficient magic certification, yet the resulting reduced stabilizer polytope is generally difficult to characterize. We trace this difficulty into two coupled obstructions: the simultaneous measurability of measurements captured by their frustration graph structure, and the consistency of sign dependencies from stabilizer formalism. We show that the sign dependencies can be discarded exactly whenever active dependencies are absent, and that perfect frustration graphs then make this reduced polytope efficiently solvable. This solvable regime derives a closed form bounded by the clique number of the frustration graph, revealing a tradeoff between witness capacity and simultaneous measurability. Clifford covariance allows rotated measurement sets to enlarge the detectable state space without raising the capacity. Graph structure therefore emerges as both a certificate of tractability and a design principle for scalable magic resource detection.

**中文**

> 检测非稳定子性通常需要完整层析，并在指数多个稳定子态上优化。只测有限个 Pauli 算符有望以更少资源认证 magic，但所得投影稳定子多面体一般仍难刻画。作者把困难分成两个耦合障碍：反对易图所描述的同时可测性，以及稳定子形式带来的符号一致性。若不存在 Pauli-active 乘积依赖，符号限制可以被精确删除；若反对易图同时还是 perfect graph，投影多面体便进入可高效求解的区域。此时 reduced RoM 有一个由最大 clique 大小控制的闭式表达，揭示 witness 容量与共同测量能力的权衡。Clifford 协变可以旋转测量窗口、扩大被检测状态的覆盖范围，却不提高单个窗口的容量。

## B002 有限测量窗口与投影多面体

**Original · `draft.tex:113–131`**

> Instead, one can fix a measurement set \(\mathcal M=\{P_1,\dots,P_m\}\) of nonidentity Pauli operators modulo phase, so that the experiment reports only the accessible expectation vector \(\mathbf b_{\mathcal M(\rho)}=(\operatorname{tr}(P_1\rho),\dots,\operatorname{tr}(P_m\rho))\in[-1,1]^m\). Seen through this window, stabilizer states are projected into the reduced stabilizer polytope
>
> \[
> \operatorname{STAB}(\mathcal M)=\operatorname{conv}\{\mathbf b_{\mathcal M(\sigma)}:\sigma\in\operatorname{STAB}_n\}\subset\mathbb R^m,
> \]
>
> and the reduced robustness of magic is the induced monotone
>
> \[
> \operatorname{RoM}_{\mathcal M}(\rho)=\min_{\mathbf x}\{\|\mathbf x\|_1:\sum_vx_v\mathbf v=\mathbf b_{\mathcal M(\rho)},\ \sum_vx_v=1\}.
> \]
>
> The projection gives \(\operatorname{RoM}_{\mathcal M}(\rho)\le\operatorname{RoM}(\rho)\), hence \(\operatorname{RoM}_{\mathcal M}(\rho)>1\) certifies nonstabilizerness.

**中文**

> 选定有限测量集合 \(\mathcal M\) 后，实验只返回这些 Pauli 的期望值向量。完整稳定子多面体沿未测坐标被压扁，形成 \(m\) 维的投影多面体。Reduced RoM 寻找一个系数和为 1 的带符号仿射分解，并最小化系数绝对值之和。由于投影会丢失区分能力，reduced RoM 不超过完整 RoM；所以大于 1 能可靠认证 magic，而不大于 1 可能只是窗口漏检。

> 这里的 projection 只是“保留若干期望值坐标、忘掉其余坐标”的线性映射；它不是对量子态执行投影测量，不是偏迹，也不是把状态送进更小的 Hilbert 空间。

> AgtXIv 纠错：原文在这里称它为 monotone，但固定 \(\mathcal M\) 时这不是对任意稳定子自由操作都单调的资源量；一个自由 Clifford 可以把原先未测的分量旋进窗口，使读数增大。它应被理解为**依赖测量窗口的函数/见证量**。完整 RoM 的单调性、\(\operatorname{RoM}_{\mathcal M}>1\) 的认证意义、它对完整 RoM 的下界关系，以及状态与窗口一起旋转时的协变性仍成立。

## B003 图骨架与符号细节

**Original · `draft.tex:134–149`**

> The frustration graph \(G_{\mathcal M}\) has node set \(\mathcal M\) and an edge for anticommuting pairs. An independent set therefore corresponds to a pairwise commuting context. These signs are constrained by Pauli product relations: if \(\prod_{P\in T}P=\eta_T I\), then \(\prod_{P\in T}f(P)=\eta_T\). Accordingly, the sign assignments satisfying all such relations form the admissible sign set \(B_S\). The reduced stabilizer polytope then has the exact V-representation
>
> \[
> \operatorname{STAB}(\mathcal M)=\operatorname{conv}\{\mathbf v_{S,f}:S\in\mathcal I_{\max}(G_{\mathcal M}),\ f\in B_S\}.
> \]

**中文**

> 反对易图决定支持集合：独立集是可共同测量的 Pauli 语境。乘积关系决定该支持上的细粒度正负号：若一组 Pauli 乘起来是 \(\eta_T I\)，其联合本征值也必须乘成 \(\eta_T\)。因此图只给多面体的骨架，允许符号集合 \(B_S\) 才给出物理角点。

> AgtXIv 审计提醒：这条 V 表示来自外部论文，statement 与这里对齐，但源证明中的一个中间 bijection 不成立；这不是 V-representation 结论的反例。详见实现说明。

![图1：反对易图、active/inactive 依赖与精确/松弛多面体](/Users/Yingjian/Documents/GitHub/AgtXIv/Stabilizerness/reader/assets/fig1.png)

**图 1 中文解读**

上半部分：橙色 active 关系完全落在一个独立集里，会删除某些符号角；绿色 inactive 关系含反对易对，不会限制任何共同测量语境。下半部分：删除符号校验得到更大的外松弛，多出来的橙色扇区并非物理稳定子投影。对同一个状态，外松弛距离更短，所以 \(\widetilde{\operatorname{RoM}}\le\operatorname{RoM}\)。

## B004 符号松弛和 Pauli-active dependency

**Original · `draft.tex:198–244`**

> We therefore relax the sign dependencies by retaining all deterministic sign assignments for a sign-relaxed stabilizer polytope. This construction is an outer relaxation satisfying \(\operatorname{STAB}(\mathcal M)\subseteq\widetilde{\operatorname{STAB}}(\mathcal M)\). A dependency is a nonempty inclusion-minimal subset \(T\subseteq\mathcal M\) satisfying \(\prod_{P\in T}P\propto I\). It is active if its Pauli operators pairwise commute. The equality \(\operatorname{STAB}(\mathcal M)=\widetilde{\operatorname{STAB}}(\mathcal M)\) holds if and only if \(\mathcal M\) has no active dependencies.

**中文**

> 符号松弛保留每个极大共同测量语境上的所有形式正负赋值，因此扩大了多面体。Pauli-active dependency 是一个最小 Pauli 乘积关系，并且其中所有 Pauli 两两对易。论文声称：精确多面体与松弛多面体相等，当且仅当不存在这种 active 关系。

关键玩具例 \(\{X_1X_2,Z_1Z_2,Y_1Y_2\}\) 的三项乘积为 \(-I\)。它们彼此对易，因此八个正负模式只有满足乘积为 −1 的四个可实现。放开校验就从四面体变成了立方体。

## B005 从自由符号到最大权独立集

**Original · `draft.tex:245–264`**

> For nonnegative node weights \(\mathbf w\), the maximum-weight independent-set value is
>
> \[
> \alpha_{\mathbf w}(G_{\mathcal M})=\max_{I\in\mathcal I(G_{\mathcal M})}\sum_{P_i\in I}w_i.
> \]
>
> For any Pauli measurement set and state,
>
> \[
> \widetilde{\operatorname{RoM}}_{\mathcal M}(\rho)=
> \max_{\mathbf y,\mu}\{\mathbf b^T\mathbf y+\mu:\alpha_{|\mathbf y|}(G_{\mathcal M})+|\mu|\le1\}.
> \]

**中文**

> 对固定对偶系数 \(y\)，松弛后的正负号可以逐项与 \(y_i\) 对齐；在某个共同测量语境 \(S\) 上，最坏值于是成为 \(\sum_{i\in S}|y_i|+|\mu|\)。再对所有独立集最大化，正好得到最大权独立集。这是最大权独立集自然出现的原因。

## B006 Perfect graph 闭式公式

**Original · `draft.tex:265–287`**

> A graph \(G\) is perfect if \(\chi(G')=\omega(G')\) for every induced subgraph \(G'\subseteq G\). If \(\mathcal M\) has no active dependencies and \(G_{\mathcal M}\) is perfect, then for any state \(\rho\),
>
> \[
> \operatorname{RoM}_{\mathcal M}(\rho)=
> \max\!\left(1,\max_Q\sum_{P\in Q}|\operatorname{tr}(P\rho)|\right)
> \le\sqrt{\omega(G_{\mathcal M})}.
> \]
>
> The bound is attained by any state supported on the \(+1\) eigenspace of \(|Q|^{-1/2}\sum_{P\in Q}P\) for a maximum clique \(Q\).

**中文**

> Perfect graph 的要求作用在所有诱导子图上，而不是只检查整图一次。在“无 Pauli-active dependency”与“图 perfect”两个门同时打开时，reduced RoM 只需查看每个反对易 clique 上的绝对期望值之和。反对易集合像高维 Bloch 球的正交轴，因此期望向量的二范数不超过 1；一范数再给出 \(\sqrt{|Q|}\) 上界。等幅的 \(+1\) 本征方向可以达到该上界。

> AgtXIv 依赖提醒：这里用到的“perfect graph 上最大权稳定集与分数 clique-cover 对偶”目前登记为 Chvátal 图论外部基础，primary source 的逐陈述对齐仍待完成。本轮 Lean 没有证明该图论定理；后续 Lean 只允许把它作为显式参数使用。因此闭式公式合同仍同时受 V-representation 修补和图论 import 阻塞。

## B007 Clifford 旋转与覆盖率

**Original · `draft.tex:302–326`**

> Let \(C\) be a Clifford unitary. Then
>
> \[
> \operatorname{RoM}_{C\mathcal MC^\dagger}(\rho)=\operatorname{RoM}_{\mathcal M}(C^\dagger\rho C).
> \]
>
> Clifford conjugation also preserves commuting, anticommuting, and Pauli product relations, hence both \(G_{\mathcal M}\) and the active status of every dependency. Thus any ensemble witness from rotated copies obeys the same witness-capacity bound.

**中文**

> Clifford 共轭把稳定子态双射到稳定子态，并保持反对易关系与 Pauli 乘积关系。物理上它是在旋转测量窗口，不是在把同一个窗口的“尺子”变长：每个副本的容量不变，但多个不等价窗口取并集可以覆盖更多状态。

## B008 数值图与测量族

![图2：八比特检测率](/Users/Yingjian/Documents/GitHub/AgtXIv/Stabilizerness/reader/assets/fig2.png)

**Original · `draft.tex:332–334,455–459`**

> Eight-qubit magic-detection rates are compared for Local, Ising, Majorana-tree, and Jordan–Wigner measurement sets. Panel (a) uses 10,000 Haar-random states and cumulative global Clifford rotations. Panel (b) uses 400 hardware-efficient variational states at each circuit depth. Coverage gain is clearest for the Jordan–Wigner and Majorana-tree sets.

**中文**

> 图 2a 显示累计加入 Clifford 旋转后，检测覆盖率上升，Jordan–Wigner 集合最显著。图 2b 中深电路检测率下降，更谨慎的物理解释是 Pauli 信号分散到更多方向，有限窗口更容易漏掉；它不证明状态的 magic 本身下降。

复现状态：源码包只有渲染后的图，没有代码、原始样本、随机种子、Clifford 采样律、旋转角分布和数值容差，所以这里只能读图，不能标记为 reproduced。

![图3：四种可解测量集合的反对易图](/Users/Yingjian/Documents/GitHub/AgtXIv/Stabilizerness/reader/assets/fig3.png)

![表1：四种测量集合及其 witness capacity](/Users/Yingjian/Documents/GitHub/AgtXIv/Stabilizerness/reader/assets/table1.png)

局域 XYZ、Ising path、Majorana tree 和 Jordan–Wigner 是四个可解族。表中的 capacity 分别为 \(\sqrt3,\sqrt2,\sqrt{\lfloor3n/2\rfloor},\sqrt{2n+1}\)。这些是理想期望值下的 witness 容量；实验成本还要考虑 Pauli weight、Clifford 深度、shots 和噪声。

## B009 证明链的关键局部段

**Original · `draft.tex:607–625`**

> The relaxed primal is feasible for every \(\mathbf b\) because the relaxed vertices affinely span \(\mathbb R^m\), and it is bounded below. Strong linear-program duality gives the vertex-form dual. For a fixed context,
>
> \[
> \max_f\left|\sum_{P_i\in S}f(P_i)y_i+\mu\right|
> =\sum_{P_i\in S}|y_i|+|\mu|.
> \]

**中文**

> 原文在这里压缩了一个必要的仿射张成 lemma：任一 Pauli 节点都能扩展到极大共同测量语境；在松弛顶点中只翻转该坐标的符号，两顶点之差就是 \(2e_i\)。因此所有坐标方向都在仿射包中，primal 对任意 \(b\) 可行。完成这一步后，有限维线性规划强对偶才能合法应用。

**Original · `draft.tex:700–723`**

> Perfect-graph antiblocker structure bounds every feasible dual objective by a convex combination of 1 and clique sums. Conversely, \((\mathbf y,\mu)=(0,1)\) attains 1, while a sign-aligned vector supported on any clique attains that clique's absolute expectation sum. The upper and lower bounds coincide.

**中文**

> 这里的 antiblocker 可以直观理解为“由所有独立集不等式切出的非负区域的对偶轮廓”；perfect graph 让这条轮廓恰好由 clique 指示向量的凸组合生成。证明闭合分两面：先用该结构证明任何 witness 都不能超过闭式表达；再给出两个显式 witness，分别达到常数分支 1 和任意 clique 分支。两者缺一都不能得到等式。

> 验证边界：上面的 antiblocker 结构是目标论文在 Chvátal 加权对偶基础上的本地合成；它目前是“条件于外部图论基础”的推导，不得由 Root 数学证书或 Varela 投影几何自动继承为已验收结论。

## B010 展望

**Original · `draft.tex:464–466`**

> When \(G_{\mathcal M}\) is perfect but active dependencies are present, maximum-weight independent set remains tractable while admissible signs require coset decoding of the dependency code. For imperfect graphs without active dependencies, replacing the independent-set value by a weighted Lovász bound gives a sound polynomial-time lower bound. Determining tight regimes is open.

**中文**

> 论文把不可解区域分成两条正交方向：图仍 perfect、但符号码有 active 约束时，图优化容易，而 coset decoding——在带奇偶校验的允许符号类中寻找最优符号——仍可能困难；没有 active 约束、但图不 perfect 时，符号层已消失，而图层需要 Lovász 型半定规划松弛。这个二维划分很适合 AgtXIv 后续拆成两个独立 branch。

## 本轮阅读结论

论文最重要的观念不是“magic 等于一个图不变量”，而是：在两个精确门控条件下，有限 Pauli 窗口的线性 witness 才能从“图骨架 + 符号细节”塌缩成纯 clique 公式。容量、检测覆盖率和某个状态的完整 magic 是三件不同的事。
