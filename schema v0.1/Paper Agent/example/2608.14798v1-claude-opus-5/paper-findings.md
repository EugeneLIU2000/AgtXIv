# 读 arXiv:2608.14798v1 时记下的问题

**这些是阅读记录，不是对论文的否定结论。** 每一条都只说"印出来的文本这样读不通"或"这一步没有给出论证"，
都对应记录集中一个 `frontier-item`（全部 `state: OPEN`），并绑定到具体的 `source-span` 字节区间。
本次没有证明或证伪任何一条，没有取回任何被引文献，没有复算任何数值结果。

正文与补充材料都读了（第 182–2723 行）。补充材料很关键：它补上了正文里看起来缺的几样东西
（`Spec_R` 的定义、低温极限的推导、小间隙引理的显式常数、SPS 密度的数值验证），也暴露了正文没有说的几个条件。

49 条开放项按轴分布：数学正确性 26、来源忠实 18、语义适用 7、可复算 4、经验支持 2。
按类型：SCOPE_AMBIGUITY 27、MODEL_ASSUMPTION 5、UNPROVED_LEMMA 5、CONFLICT 3、ALIGNMENT_GAP 3、
DATA_MISSING 3、MISSING_SOURCE 2、RESOURCE_LIMIT 1。完整列表见 [output/claims.md](output/claims.md)。

下面挑出影响面最大的九条。

## A. 摘要的强度高于正文所证（ALIGNMENT_GAP，`c23`/`c32`）

摘要说稳定子功"for every value of its parameter … is a faithful, subadditive **magic monotone**"。
第 V 节列出的五条性质是：忠实、Clifford 不变、次可加、**丢弃子系统下的单调性**、附加稳定子态不变。
**在自由操作类 $\mathcal{F}$（含计算基测量、稳定子态制备、部分迹）下的单调性，全文没有陈述也没有证明。**
这不是措辞问题：第 VI B 节的单次转化定理把第一个不等式直接称为"monotonicity of $\mathcal{W}_\beta$ under free
operations"，于是整条 $T$-代价下界与蒸馏逆定理都架在这条未证的性质上。作者自己在展望里把混合态与信道版本的
单调性列为第一个待解问题。

## B. "高效可测"的实际强度（SCOPE_AMBIGUITY，`c14`）

补充材料证到的是：对**归一化**量 $d_n^{-1}\mathcal{Z}_\beta$ 的**截断**版本，给出加性误差 $\epsilon$ 的
Hoeffding 界，样本数 $\mathcal{N}=\mathcal{O}(\cosh^2\!\beta\,e^{-2\beta}\epsilon^{-2}\log(1/\delta))$。
要谈完整 SPF，还要求 $\epsilon>\Delta(\beta,k)$，而

$$\Delta(\beta,k)=d_n e^{-\beta}\Big(\cosh\beta-\sum_{l=0}^{k}\tfrac{\beta^{2l}}{(2l)!}\Big)$$

**带一个 $d_n=2^n$ 因子**。也就是说固定 $k$ 时保证在大 $n$ 下失效，而使 $\Delta<\epsilon$ 所需的
$k(n,\beta,\epsilon)$ 论文没有给。另外每个外循环样本要消耗 $2k+2$ 份态（Bell 采样 2 份 + 内循环 $2k$ 份），
所报的 $\mathcal{O}(kn)$ 是经典后处理时间。**最关键的一步缺失是：没有任何陈述把 $\hat{\mathcal{Z}}$ 的误差
传播到 $\mathcal{W}_\beta=-\log(\hat{\mathcal{Z}}-d_n^2e^{-\beta})+\cdots$**，而摘要与讨论对这两个对象
都不加限定地说"efficiently estimable"。

## C. 可分态定理：记号冲突，但结论自洽（SCOPE_AMBIGUITY，`c16`）

`Theorem (SPF for separable states)` 用到的残余谱 `Spec_R` 在正文里没有定义，要到补充材料的
`Proposition (Canonical Splitting)` 才给出：`Spec_S` 是所有 $P\ket{\psi}=\pm\ket{\psi}$ 的项，
`Spec_R` 是其补集（含全部零项）。正文定理因此在陈述处不是自足的。

更要紧的是记号：定理里的 $2^{|B|-\nu_B}$ 只有把 $|B|$ 读作**比特数**才成立，而第 II 节明确写着
$d_A=|A|=2^n$。按第 II 节的约定，该定理量纲就是错的。

**按比特数读法，本次手工核对过它与 `Lemma (SPF for Stabilizer + Pure)` 的一致性，两边相符**：取 $B$ 为稳定子态，
$\nu_B=0$、$|{\rm Spec}_S(\psi_B)|=d_B$、$|{\rm Spec}_R(\psi_B)|=d_B^2-d_B$（全是零项），代入后四项合并正好给出
$d_B\mathcal{Z}_\beta(\psi_A)+e^{-\beta}(d_B^2-d_B)d_A^2$。所以这是一处排印／约定问题，不是数学问题——
但**这只是一次手算核对，不是对定理的证明**。

## D. 低温极限在正文两处不一致（CONFLICT，`c07`）

第 III B 节：$\lim_{\beta\to\infty}\mathcal{Z}_\beta(\psi)=|{\rm STAB}(\psi)|/2$，
补充材料由 $\hat H=\hat H_+\oplus\hat H_-$ 的分块推导也给出 $\tfrac12|{\rm STAB}(\psi)|$。
第 VI C 节（H₂ 讨论）却写成 $\lim_{\beta\to\infty}\mathcal{Z}_\beta(\psi)=|{\rm Stab}(\psi)|$，少一个因子 2。
**与推导不符的是第 VI C 节这一句。**

同节还有一处排印遗漏：支撑／核改写式写成 $\sum_{P\in{\rm Supp}}\cosh(\tr{P\psi})$，$\cosh$ 里少了 $\beta$。

## E. 引用的稳定子保真度下界按字面读不成立（CONFLICT，`c27`）

第 VI A 节引用 $\frac{\alpha-1}{2\alpha}M_\alpha(\psi)\le F_{\rm Stab}(\psi)$。
取 4 比特、$M_2=2$、$\alpha=2$，左端为 $1/2$，于是强制 $F_{\rm Stab}\ge1/2$——这与同一节自己给出的
magic 态保真度上界矛盾。按文献惯例，被引结果约束的应是 $\log(1/F_{\rm Stab})$ 而非 $F_{\rm Stab}$。
**本次按印出来的样子记录，没有代为修正，也没有去查被引文献。**

## F. 次可加性的承重步骤只有断言（SCOPE_AMBIGUITY，`c17`）

`Lemma (cSPF supermultiplicativity)` 的证明构造出 $p_k=w_ka_k/\sum_k w_ka_k$ 后，直接断言
"$p_k/p^\star_k\ge p_{k+1}/p^\star_{k+1}$"。**这一步没有给理由。** 理由其实是一行：
$p_k/p^\star_k\propto a_k=\sum_i\tr[\psi_AP_i]^{2k}$，而 $|\tr[\psi_AP_i]|\le1$ 使 $a_k$ 随 $k$ 单调不增。
补充材料对**未过滤**稳定子功的对应定理同样直接断言 $a_k/a'_k$ 单调不增。
本次把这行理由写进了记录，但没有核验论证的其余部分。补充材料里那条定理的交叉引用
`\ref{Chebyshev_lemma}` 也解析不到（引理标号是 `lem:Chebyshev_lemma`）。

## G. $\beta$ 单调性被反复使用但未证（UNPROVED_LEMMA，`c24`）

"continuous and monotonic interpolation"（第 V 节）、"grows monotonically with $\beta$"（H₂ 与 Ising 两节）
都在断言 $\beta\mapsto\mathcal{W}_\beta$ 单调。全文没有给 $\partial_\beta\mathcal{W}_\beta\ge0$ 的论证。
两个端点极限（$\beta\to\infty$ 给出 nullity、$\beta\to0$ 至领头阶给出 $M_2$ 的函数）在正文与补充材料中
**都只有断言，没有推导，也没有误差项**。

## H. 若干陈述在 $\beta=0$ 处退化，以及一个对数底问题（SCOPE_AMBIGUITY，`c23`/`c17`/`c24`/`c25`）

$\mathcal{Z}^c_0\equiv0$ 对任何态都成立，所以 $\mathcal{W}_0$ 是 $\log(0/0)$，第 V 节的性质表（含忠实性）
在 $\beta=0$ 处是空的，而性质表没有排除这一点；`Corollary (Bounds on Stabilizer Work)` 与 cSPF 超乘性不等式
在 $\beta=0$ 同样奇异。第 VI B 节的转化定理明确写了 $\beta\neq0$——**只有那一处写了**。

另有：连续性常数 $K_n(\beta)=2\beta^{-1}\sinh\beta$ 用自然对数不等式
$|\log a-\log b|\le|a-b|/\min\{a,b\}$ 推出，而 $\mathcal{W}$ 以 2 为底定义，$1/\ln 2$ 没有出现在常数里；
这个常数随后进入保真度上界命题。常数名带下标 $n$ 但值里没有 $n$。

## I. 未过滤稳定子功的反例没有给出（MISSING_SOURCE，`c35`）

补充材料说：若用 SPF 而非 cSPF 定义"未过滤稳定子功" $\mathfrak{u}_\beta$，它同样忠实、Clifford 不变、次可加，
但"does not always decrease under partial trace for all values of $\beta$"。**这正是全文选用 cSPF 的理由，
却没有给出任何一个 $\beta$、态与切分作为见证。** 读者无法从文本核实这个动机。

## J. 数值与条件（DATA_MISSING，`c29`/`c30`；SCOPE_AMBIGUITY，`c21`）

- H₂（STO-3G 与 6-31G）与横场 Ising 两节都没有给几何、积分来源、求解器、边界条件、系统尺寸表或代码。
  $\ket{T}^{\otimes n}$ 那个 $\epsilon\lesssim2.27\times10^{-3}$ 的阈值来自"straightforward numerical maximization"，
  最优 $\beta$ 与搜索过程都没有报告。这三处在记录集中记为 `COMPUTATION` 义务，状态"未复算"。
- 值得肯定的一处：补充材料对 SPS 的 Pauli 谱密度推论**做了数值验证**（$n\in\{2,4,6,8\}$，$n=2,4$ 穷尽全部布尔函数，
  $n=6,8$ 分别取 4096 与 2048 个随机函数），这是全文唯一一处检验推导而非仅作图示的数值工作；数据与代码仍未提供。
- 但该推导是对**均匀随机**布尔函数取平均（连通关联引理明写 "uniformly random function"），
  而定理陈述与整节讨论针对的是**伪随机** $f$。这一步对计算受限观测者是常规的，但定理本身没有带上这个条件。
- Ising 一节正文把耦合称作 $J$，哈密顿量与全部图里用的是 $g$。

## 记在旁边的一条

论文自带 AI 致谢：作者说用 Claude 打磨了引言与讨论，并由此了解到 Li–Haldane 的纠缠谱工作。
本记录只把它登记为 `ATTRIBUTION` 组件（`c32`/`comp:ai`），不作任何评价。
