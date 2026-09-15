# 论文主张候选输出

论文：Stabilizer Statistical Mechanics（arXiv:2608.14798v1）。

本次为真实源码阅读后的候选提取；不是完整语义清点、科学审阅或形式化。
每项保留原文范围、作者结论、适用条件和缺口。MathClaim 只对已整理结构化量词的目标生成；其余公式保留在语义记录中。

## 稳定子态的 Pauli 谱计数

**ID**：stabilizer-spectrum

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：For a pure n-qubit stabilizer state the signed Pauli spectrum has d^2-d zero entries and d entries equal to plus or minus one.

**数学表达或待规范化表达**：

#{x in Spec(psi):x=0}=d^2-d; #{x in Spec(psi):|x|=1}=d.

**条件**：

- The state is a normalized pure n-qubit stabilizer state.
- d=2^n; phase-free Pauli labels are used, retaining the sign and multiplicity of each expectation.

**原文**：[L289–L335](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:289>), [L338–L365](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:338>)

**未解项（非已证伪结论）**：

- No independent proof or source-to-formal alignment performed; signed-group versus phase-free-label identification must remain explicit.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## Pauli 零谱条目与 nullity 的界

**ID**：kernel-bounds

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：The authors bound the number of vanishing Pauli expectations of a pure state using its stabilizer nullity.

**数学表达或待规范化表达**：

2^n(2^n-2^{nu(psi)}) <= |Ker_P(psi)| <= 4^n-2^n.

**条件**：

- psi is a normalized pure n-qubit state.
- nu(psi)=n-log_2|Stab(psi)|; Ker_P(psi) contains phase-free Paulis with zero expectation.

**原文**：[L289–L335](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:289>), [L374–L432](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:374>)

**未解项（非已证伪结论）**：

- The cited support/nullity comparison has not been retrieved or independently checked.

**引用线索**：Beverland/Pauli_Spectrum/2020, Leone/Stab_Renyi_monotone/2024

## 配分函数的高温与零温极限

**ID**：spf-limits

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：The stabilizer partition function tends to the number of Pauli labels as beta tends to zero and to half the stabilizer-group cardinality as beta tends to positive infinity.

**数学表达或待规范化表达**：

lim_{beta->0} Z_beta(psi)=d^2; lim_{beta->+infinity} Z_beta(psi)=|Stab(psi)|/2.

**条件**：

- psi is a fixed normalized pure n-qubit state; d=2^n.
- Z_beta(psi)=exp(-beta) sum_{x in Spec(psi)} cosh(beta x).
- beta is a mathematical parameter, not a physical inverse temperature.

**原文**：[L289–L303](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:289>), [L533–L554](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:533>)

**未解项（非已证伪结论）**：

- Limits and finite-beta estimates must not be conflated.
- The subsequent support/kernel rewrite at lines 553-555 appears to omit beta inside cosh; not silently used to redefine Z.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 配分函数的 Clifford 不变性

**ID**：clifford-invariance

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：The stabilizer partition function is invariant under Clifford conjugation of a pure state.

**数学表达或待规范化表达**：

Z_beta(C psi C^dagger)=Z_beta(psi).

**条件**：

- psi is a normalized pure n-qubit state; beta is real.
- C is an n-qubit Clifford unitary; C(psi)=C psi C^dagger.
- SPF uses cosh of signed expectations, not a labelled-spectrum identity.

**原文**：[L305–L335](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:305>), [L533–L543](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:533>), [L570–L588](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:570>)

**未解项（非已证伪结论）**：

- The proof's assertion about sorting signed spectra needs review because Clifford conjugation can flip signs; no proof repair is made here.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 稳定子参考配分函数

**ID**：stabilizer-reference

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：All pure n-qubit stabilizer states have the same SPF, with the stated closed-form core SPF.

**数学表达或待规范化表达**：

Z_beta(phi)=exp(-beta)[d^2-d+d cosh(beta)]; Z_beta^c(phi)=exp(-beta)d(cosh(beta)-1).

**条件**：

- phi is a normalized pure n-qubit stabilizer state; d=2^n; beta is real.
- Z_beta^c=Z_beta-d^2 exp(-beta).

**原文**：[L533–L567](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:533>), [L591–L605](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:591>)

**未解项（非已证伪结论）**：

- A common value on stabilizer states is not by itself an iff characterization at every beta; at beta=0 SPF is state-independent.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 配分函数与整数阶稳定子熵的展开

**ID**：renyi-expansion

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：The authors express SPF through the hierarchy of integer-index stabilizer Renyi entropies, retaining the universal zeroth and second-moment terms.

**数学表达或待规范化表达**：

Z_beta(psi)=exp(-beta)[d^2+d beta^2/2+sum_{k>=2} beta^{2k}/(2k)! * 2^{n-(k-1)M_k(psi)}].

**条件**：

- psi is a normalized pure n-qubit state; d=2^n; beta is real.
- M_k is the source's base-two stabilizer Renyi entropy; k is an integer at least two in the sum.

**原文**：[L440–L459](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:440>), [L635–L648](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:635>)

**未解项（非已证伪结论）**：

- This even-moment object does not recover the labelled signed Pauli spectrum; claims about full spectrum must respect the qualification at lines 570-573.

**引用线索**：Leone/Stab_Renyi/2022

## 配分函数的连续性界

**ID**：lipschitz

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：The SPF difference for two pure n-qubit states is bounded by an explicit coefficient times the trace norm of the projector difference.

**数学表达或待规范化表达**：

|Z_beta(psi)-Z_beta(phi)| <= exp(-beta)d beta sinh(beta) ||psi-phi||_1.

**条件**：

- psi and phi denote normalized pure-state projectors on the same n-qubit space.
- beta is real; d=2^n; ||.||_1 is the trace norm, not an independently renormalized trace distance.

**原文**：[L289–L303](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:289>), [L653–L671](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:653>)

**未解项（非已证伪结论）**：

- Supplementary proof has not been reconstructed or validated in this Paper pass.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## Bell 采样估计：固定截断不等于全参数高效

**ID**：bell-estimation

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors describe Bell-sampling access to a finite-order truncated SPF for fixed order and beta, with additive accuracy and failure probability; full normalized SPF additionally needs a truncation bound.

**数学表达或待规范化表达**：

A fixed-order moment estimator is postprocessed into a truncated SPF estimate; no uniform cost bound for arbitrary beta or the unnormalized full SPF is extracted here.

**条件**：

- Fixed truncation order k and parameter beta; repeated state copies and the cited Bell-sampling primitive are available.
- Accuracy epsilon, failure probability delta, normalization and truncation error must be tracked separately.

**原文**：[L673–L683](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:673>), [L2164–L2223](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2164>)

**未解项（非已证伪结论）**：

- This deliberately remains a residual scientific claim rather than an underspecified MathClaim.
- No sampling experiment or empirical runtime measurement was performed.

**引用线索**：Tobias/Pauli_sampling/2024

## 纯态配分函数的状态无关上下界

**ID**：state-independent-bounds

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：For pure n-qubit states the authors give stabilizer-valued upper and uniform-nonidentity-spectrum lower bounds on SPF.

**数学表达或待规范化表达**：

exp(-beta)[cosh(beta)+(d^2-1)cosh(beta/sqrt(d+1))] <= Z_beta(psi) <= exp(-beta)[d^2-d+d cosh(beta)].

**条件**：

- psi is a normalized pure n-qubit state, beta is real, d=d_n=2^n.
- Identifying the unindexed d in the source denominator with d_n is an explicit extraction convention awaiting review.

**原文**：[L289–L303](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:289>), [L688–L705](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:688>)

**未解项（非已证伪结论）**：

- The proof expansion appears to omit the exp(-beta) factor; statement is preserved, not repaired.
- Source notation d versus d_n requires alignment review.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 同一单量子比特纯态张量幂的配分函数及 T 态特例

**ID**：product-powers

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors give a multinomial expression for the stabilizer partition function of n copies of a single-qubit pure state, with a closed expression for T-state copies, and claim that T-state copies are distinguished from stabilizer states for every nonzero beta. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal Z_\beta(\psi^{\otimes n})=e^{-\beta}\sum_{w=0}^n\binom nw\sum_{n_x,n_y,n_z}\binom{w}{n_x\,n_y\,n_z}\cosh(\beta V_\psi[\vec n]),\quad V_\psi[\vec n]=\prod_{\sigma\in\{X,Y,Z\}}\langle\sigma\rangle^{n_\sigma}\). For T copies they state \(\mathcal Z_\beta(T^{\otimes n})=e^{-\beta}[(4^n-3^n)+\sum_{k=0}^n\binom nk2^k\cosh(\beta2^{-k/2})]\), \(\mathcal Z_0=4^n\), and \(\mathcal Z_\beta(T^{\otimes n})<\mathcal Z_\beta(\mathrm{STAB}_n)\) for nonzero beta.

**条件**：

- The input is n identical copies of a single-qubit pure state, not an arbitrary collection of different local states.
- For the special case, |T> = T|+> and the X and Y expectations are 1/sqrt(2).
- Beta is real under the preceding definition; the strict comparison is stated for beta != 0.

**原文**：[L748–L771](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:748>), [L788–L805](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:788>)

**未解项（非已证伪结论）**：

- The displayed multinomial sum does not explicitly give the range or the constraint n_x+n_y+n_z=w; its counting explanation suggests this constraint, but it has not been inserted into the formula.
- Line 765 says all weight-k strings after line 761 excludes strings containing Z; the qualification is implicit.
- The strict inequality does not explicitly exclude n=0.
- No independent mathematical verification was performed.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 双体乘积态配分函数的稳定子项与剩余项分解

**ID**：bipartite-decomposition

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim that a bipartite pure product state's Pauli spectrum factorizes, while its stabilizer partition function is generally nonmultiplicative and has the displayed subsystem-plus-residual decomposition. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal Z_\beta(\psi_{AB})=2^{|B|-\nu_B}\mathcal Z_\beta(\psi_A)+2^{|A|-\nu_A}\mathcal Z_\beta(\psi_B)-e^{-\beta}2^{n-\nu_A-\nu_B}\cosh\beta+\mathcal Z^{(R)}_\beta(\psi_{AB})\), with \(\mathcal Z^{(R)}_\beta=e^{-\beta}\sum_{x\in\mathrm{Spec}_R(\psi_A)\times\mathrm{Spec}_R(\psi_B)}\cosh(\beta x)\).

**条件**：

- The n-qubit pure state is psi_AB = psi_A tensor psi_B.
- nu_A and nu_B are the subsystem stabilizer nullities.
- Beta is real under the preceding definition.

**原文**：[L298–L299](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:298>), [L811–L838](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:811>)

**未解项（非已证伪结论）**：

- Line 299 defines |A| as Hilbert-space dimension, whereas the exponents in line 826 leave a qubit-count versus dimension ambiguity; the formula is retained literally.
- The read text does not supply a precise definition of Spec_R, including whether zero entries are retained.
- The sum treats an element of a Cartesian product as a scalar x; the intended multiplication and multiplicities are not explicitly specified there.
- Line 814 writes a bare inequality without conditions for possible equality.
- The statement concerns pure product states; it does not supply a formula for general separable mixed states.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 附加稳定子纯态时的配分函数与核心配分函数

**ID**：stabilizer-ancilla

**状态**：已有候选 MathClaim；等待独立审阅。

**作者主张**：The authors give an exact affine transformation of the stabilizer partition function under tensoring with a pure stabilizer state, and a multiplicative scaling for the core partition function. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal Z_\beta(\psi_A\otimes\mathrm{Stab}_B)=d_B\mathcal Z_\beta(\psi_A)+e^{-\beta}(d_B^2-d_B)d_A^2\) and \(\mathcal Z_\beta^c(\psi_A\otimes\mathrm{Stab}_B)=d_B\mathcal Z_\beta^c(\psi_A)\).

**条件**：

- psi_A is an arbitrary pure state and Stab_B is a pure stabilizer state.
- d_A and d_B are Hilbert-space dimensions.
- The core partition function is Z_beta^c = Z_beta - e^(-beta)d^2.
- Beta is real.

**原文**：[L298–L299](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:298>), [L342–L363](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:342>), [L558–L565](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:558>), [L840–L858](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:840>)

**未解项（非已证伪结论）**：

- The proof at line 854 describes d_B ones, whereas the signed spectrum convention at lines 351-363 permits plus/minus ones; both source descriptions are retained without rewriting the proof.
- No independent mathematical verification was performed.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 核心配分函数的超乘性型不等式

**ID**：core-supermultiplicativity

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors assert a normalized supermultiplicativity inequality for the core stabilizer partition function of any bipartite pure product state. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal Z_\beta^c(\psi_A\otimes\phi_B)\geq\frac{\mathcal Z_\beta^c(\psi_A)\mathcal Z_\beta^c(\phi_B)}{e^{-\beta}(\cosh\beta-1)}\).

**条件**：

- psi_AB = psi_A tensor phi_B is a bipartite n-qubit pure product state.
- Beta is real under the preceding definition; the lemma states no exclusion of beta=0.

**原文**：[L558–L565](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:558>), [L860–L880](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:860>)

**未解项（非已证伪结论）**：

- The displayed denominator vanishes at beta=0, and the source supplies neither an exclusion nor a limiting convention; no repaired domain is imposed here.
- The supplementary Chebyshev lemma referenced at line 875 was not read; body-versus-appendix consistency is unassessed.
- The expression is identifiable as a mathematical target, but its domain and proof remain unresolved.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## Haar 随机纯态的平均配分函数

**ID**：haar-mean

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors give an exact Bessel-function formula for the ensemble-average stabilizer partition function of Haar-random n-qubit pure states. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal Z_\beta(\mathrm{Haar}_n)=e^{-\beta}[\cosh\beta+(d_n^2-1)\Gamma((d_n+1)/2)(2/\beta)^{(d_n-1)/2}I_{(d_n-1)/2}(\beta)]\), with the beta-to-zero limit equal to \(d_n^2\).

**条件**：

- psi = U|0>^tensor n with U sampled from Haar measure on U(2^n).
- d_n = 2^n.
- Beta >= 0 as stated in the theorem.

**原文**：[L293–L296](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:293>), [L889–L904](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:889>)

**未解项（非已证伪结论）**：

- At beta=0 the displayed formula contains a singular factor; line 904 discusses the limit separately.
- The supplementary proof and the cited Pauli-spectrum paper were not read or verified; body-versus-appendix consistency is unassessed.
- The formula is for an ensemble mean and is not asserted here as the value of every Haar sample.

**引用线索**：Turkeshi/Pauli_spectrum/2025

## Haar 平均配分函数的大维度渐近式

**ID**：haar-asymptotics

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim that, when beta squared is little-o of the Hilbert-space dimension, the nonidentity contribution to the Haar ensemble-average partition function is asymptotically flat. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal Z_\beta(\mathrm{Haar}_n)=e^{-\beta}[\cosh\beta+(d_n^2-1)(1+o(1))]\). Their expansion is \(\Gamma(\alpha+1)(2/\beta)^\alpha I_\alpha(\beta)=1+\beta^2/[4(\alpha+1)]+O(\beta^4/\alpha^2)\).

**条件**：

- The quantity is the Haar ensemble average defined in the preceding theorem.
- d_n tends to infinity, with fixed beta or more generally beta^2=o(d_n).

**原文**：[L373–L391](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:373>), [L415–L429](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:415>), [L906–L920](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:906>)

**未解项（非已证伪结论）**：

- Line 920 moves from asymptotically small Pauli expectations to exact-looking assertions |Ker_P(Haar_n)|=d_n^2-1 and |Supp(Haar_n)|=1 almost surely. The exact-zero definitions at lines 373-391 and the kernel upper bound at lines 415-429 leave a textual tension; it is not repaired here.
- The finite-dimensional Haar moment distribution and supplementary Bessel calculation were not inspected; body-versus-appendix consistency is unassessed.
- The source provides no explicit uniform remainder constant for beta varying with dimension.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## Haar 随机态配分函数的归一化集中界

**ID**：haar-concentration

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim a tail bound for the deviation of a Haar state's partition function from its ensemble mean after normalization by L_n(beta). This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\Pr_{\psi\sim\mathrm{Haar}_n}(|\mathcal Z_\beta(\psi)-\mathcal Z_\beta(\mathrm{Haar}_n)|/L_n(\beta)\geq\epsilon)\leq4\exp[-(2/(9\pi^3))2^n\epsilon^2]\), where \(L_n(\beta)=e^{-\beta}d_n\beta\sinh\beta\).

**条件**：

- psi is a Haar-random n-qubit pure state.
- epsilon >= 0.
- L_n(beta) is taken from the preceding Lipschitz theorem; the concentration lemma does not explicitly state a beta domain.

**原文**：[L653–L668](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:653>), [L922–L940](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:922>)

**未解项（非已证伪结论）**：

- L_n(0)=0 makes the displayed normalized event undefined, and no beta=0 convention is stated.
- The preceding theorem uses trace norm on pure-state projectors; the metric conversion mentioned at line 668 is not quantified in the read text.
- The double-exponential description concerns fixed normalized deviation epsilon; no unnormalized deviation scaling is independently established here.
- The supplementary Lipschitz proof was not read; body-versus-appendix consistency is unassessed.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 以配分函数认证 Haar 态与可压缩态的操作性主张

**ID**：ensemble-certification

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors propose oracle-based tests for Haar randomness and nu-compressibility by checking a normalized residual against an asymptotic mean, and claim efficient implementation through partition-function estimation. This is an unverified author-claim candidate, not a validated certification procedure.

**数学表达或待规范化表达**：

The authors accept Haar randomness when \(\delta_H=\frac{e^\beta[\mathcal Z_\beta(\psi)-e^{-\beta}(\cosh\beta+d_n^2-1)]}{(d_n^2-1)L_n(\beta)}=o(1)\); they accept nu-compressibility when \(\delta_\nu=\frac{e^\beta[\mathcal Z_\beta(\psi)-e^{-\beta}(4^n-2^{n-\nu}+2^{n-\nu}\cosh\beta)]}{2^{n-\nu}(4^\nu-1)L_{\mathrm{Comp}_\nu}(\beta)}=o(1)\), in the respective stated beta regimes, and claim polynomial-time implementation.

**条件**：

- The Haar task promises an unknown state sampled from Haar or generated by an unspecified alternative process.
- HaarCertify receives the partition function for beta=o(sqrt(d_n)).
- nuCertify receives an integer nu<=n and oracle access for beta=o(sqrt(2^nu)).
- The implementation claim invokes an earlier estimation theorem without specifying the precision needed by these tests.

**原文**：[L942–L977](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:942>), [L1040–L1073](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1040>), [L1125–L1126](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1125>), [L1171–L1172](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1171>)

**未解项（非已证伪结论）**：

- Concentration of an ensemble alone is not an explicit acceptance/rejection guarantee against the unspecified alternative process; no such guarantee is supplied in these algorithms.
- An asymptotic o(1) predicate is not given as a finite-input decision rule.
- Normalizations are singular at beta=0; the compressible normalization also vanishes at nu=0.
- The body later says exponentially close pseudomagic and Haar curves are challenging to distinguish; the general efficient-certification wording is left unresolved.
- The referenced estimation theorem was not read in full, and no runtime-versus-required-precision verification was performed.
- Supplementary material was not read; body-versus-appendix consistency is unassessed.

**引用线索**：Gu/Magic_vs_Ent/2024

## 可压缩态系综平均配分函数及其渐近形式

**ID**：compressible-mean

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors express the average partition function of the specified nu-compressible ensemble through a nu-qubit Haar average, give the core scaling, and state a large-2^nu expansion. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors give the exact identities \(\mathcal Z_\beta(\mathrm{Comp}_\nu)=2^{n-\nu}\mathcal Z_\beta(\mathrm{Haar}_\nu)+e^{-\beta}4^\nu(4^{n-\nu}-2^{n-\nu})\) and \(\mathcal Z^c_\beta(\mathrm{Comp}_\nu)=2^{n-\nu}\mathcal Z^c_\beta(\mathrm{Haar}_\nu)\). Their asymptotic corollary is \(\mathcal Z_\beta(\mathrm{Comp}_\nu)=e^{-\beta}[4^n-2^{n-\nu}+2^{n-\nu}\cosh\beta]+e^{-\beta}2^{n-\nu}(4^\nu-1)o(1)\).

**条件**：

- States are prepared from |0>^tensor n using a nu-qubit Haar unitary followed by a uniformly sampled n-qubit Clifford.
- The sampling measure is mu_(n,nu)=mu_Cl_n * mu_Haar_nu.
- The asymptotic statement assumes fixed beta and large 2^nu, or beta^2=o(2^nu).
- The exact mean identity and the asymptotic corollary have different assertion strengths.

**原文**：[L411–L429](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:411>), [L984–L1011](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:984>), [L1024–L1039](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1024>)

**未解项（非已证伪结论）**：

- The preparation definition does not state minimality of nu, while line 991 claims equivalence to exactly nu stabilizer nullity; this distinction is unresolved.
- The measure is written mu_nu in some locations and mu_(n,nu) in others.
- Line 1038 asserts |Ker_P(Comp_nu)|=4^n-2^(n-nu), leaving tension with the earlier exact kernel bound and with interpreting small expectations as exact zeros.
- The claim of vanishing corrections at line 1039 does not specify a normalization; the displayed additive remainder includes dimension-dependent prefactors.
- No uniform-in-sample identity is inferred from the mean formula, and no supplementary or cited-source verification was performed.

**引用线索**：Gu/Magic_vs_Ent/2024

## 可压缩态的集中性质与原文 Lipschitz 下标

**ID**：compressible-concentration

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim concentration of nu-compressible-state partition functions around their ensemble mean with Lipschitz constant 2^(n-nu)L_n(beta). This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state concentration around \(\mathcal Z_\beta(\mathrm{Comp}_\nu)\) with \(L_{\mathrm{Comp}_\nu}(\beta)=2^{n-\nu}L_n(\beta)\), using \( |\mathcal Z_\beta(\psi)-\mathcal Z_\beta(\phi)|=2^{n-\nu}|\mathcal Z_\beta(U_\psi|0\rangle^{\otimes\nu})-\mathcal Z_\beta(U_\phi|0\rangle^{\otimes\nu})|\).

**条件**：

- The surrounding context samples from mu_(n,nu), although the lemma itself says only 'Given a nu-compressible state'.
- The proof compares partition functions on decoded nu-qubit pure states.
- L_n(beta) is the earlier n-qubit Lipschitz constant.

**原文**：[L653–L660](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:653>), [L993–L997](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:993>), [L1012–L1022](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1012>)

**未解项（非已证伪结论）**：

- The proof uses nu-qubit inputs while retaining the subscript n on L_n; it is not replaced by L_nu here.
- The probability measure, metric, tail exponent, and deviation normalization are not fully specified within the lemma.
- The surrounding exponentially-close and self-averaging descriptions have no explicit absolute or relative error scale here.
- Insufficient detail is supplied for extracting the full concentration statement as a complete MathClaim.
- Supplementary material was not read; body-versus-appendix consistency is unassessed.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 有限非 Clifford 门掺杂态的配分函数与门数推断主张

**ID**：doped-state-inference

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim that a state formed using at most t bounded-size non-Clifford gates is nu-compressible for some nu<=2lt, assign it the compressible-ensemble partition-function formula, and propose extracting a lower bound on t. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\nu\leq2lt\) and assign the SPF of a t-doped state to their \(\mathcal Z_\beta(\mathrm{Comp}_\nu)\) formula for some such nu. They describe a confidence interval \(t\in[t_{\min},t_{\max}]\), while tExtract explicitly ensures only \(t_{\min}\leq t\) and returns the first candidate t whose inner nu loop is accepted.

**条件**：

- The preparation starts from an n-qubit stabilizer state and uses at most t non-Clifford gates, each acting on l=O(1) qubits.
- The inference algorithm assumes access to the partition function and calls nuCertify.
- The loop uses an upper limit t_max whose origin is not specified.

**原文**：[L993–L1003](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:993>), [L1075–L1126](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1075>)

**未解项（非已证伪结论）**：

- The corollary concerns an individual t-doped state, whereas the invoked theorem concerns a particular ensemble mean; no matching distribution on t-doped states is specified.
- Line 1092 describes t as known while asking to find t.
- The preceding nuCertify prints an answer and returns Void, but tExtract expects a Boolean result.
- The loops omit nu=0 and t=0 and do not explicitly enforce nu<=n.
- No derivation of t_max or statistical confidence level accompanies the interval wording.
- The cited design and decoding results were not read, and no scientific or algorithmic verification was performed.

**引用线索**：Haferkamp/arbitrary_k_designs/2022, Leone/Clifford_decoders_PRA/2024, Oliviero/Clifford_Decoders_letter/2024

## 全支撑子集相位态的平均配分函数与伪魔性辨别限制

**ID**：pseudomagic-mean

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：For full-support subset phase states, the authors give a closed expression for the ensemble-average stabilizer partition function and state that its curves become exponentially close to Haar curves, limiting efficient discrimination. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal Z_\beta(\mathrm{SPS})=e^{-\beta}[((d_n-1)(d_n+2))/2+\cosh\beta+(d_n(d_n-1)/2)(\cosh(2\beta/d_n))^{d_n/2}]\). They also state that SPS and Haar states both have \(\nu=\mathcal O(n)\) and that the SPF curves become exponentially close, so efficient nu-extraction does not imply efficient discrimination from Haar states.

**条件**：

- The subset phase state is |psi_(f,S)> = |S|^(-1/2) sum_(x in S) (-1)^f(x)|x>.
- The theorem specializes to S={0,1}^n and |S|=2^n, with d_n=2^n.
- The source describes f as pseudorandom and the sampling as uniform over the full-support subset phase states, without specifying the function-family distribution.
- The theorem does not explicitly restrict beta beyond the preceding real-valued definition.

**原文**：[L1131–L1172](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1131>)

**未解项（非已证伪结论）**：

- The averaging law over pseudorandom functions is unspecified; uniform random Boolean functions and a pseudorandom function family are not explicitly distinguished in the theorem.
- The exact formula applies only to full support; no expression is given here for general |S|=2^k.
- The introductory computational-indistinguishability wording is accompanied by a trace-norm moment condition, without an explicit relation between the two notions or a quantified copy parameter t.
- The stated gap omega(k) versus n and the claimed low/high ordering are retained as source wording, without reconstruction of the cited result.
- The supplemental moment proof was not read; any body-versus-appendix difference in the averaging law or formula remains unassessed.
- The formula is a mathematical expression, but the unresolved sampling measure prevents a complete MathClaim for its ensemble average; the discrimination commentary also lacks a quantitative statement.
- The cited pseudomagic and pseudoentanglement papers were not read or verified.

**引用线索**：Gu/pseudomagic/2024, Aaronson/pseudoentanglement/2022

## 稳定子功的基本性质与纯态操作单调性

**ID**：work-properties

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim that stabilizer work, defined by a base-2 logarithmic ratio of core stabilizer partition functions, is faithful, Clifford invariant, subadditive, nonincreasing under discarding a factor of a pure product state, and invariant under adding stabilizer ancillas. They further use it as a monotone under deterministic pure-state stabilizer protocols. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors assert W_beta(psi) = -log_2 Z_beta^c(psi) + log_2 Z_beta^c(STAB_n), with \(\mathcal W_\beta(\psi)=0\iff\psi\in\mathrm{STAB}\), Clifford invariance, \(\mathcal W_\beta(\psi_A\otimes\chi_B)\leq\mathcal W_\beta(\psi_A)+\mathcal W_\beta(\chi_B)\), \(\mathcal W_\beta(\psi_A\otimes\chi_B)\geq\mathcal W_\beta(\psi_A)\), and equality in the latter relation exactly when the discarded factor is a stabilizer state. They assert nonincrease under their full protocol class as well.

**条件**：

- States are pure; the displayed discarding relation concerns a tensor-product input.
- The protocol class consists of Clifford unitaries, stabilizer preparation, computational-basis measurements and partial traces, with a pure resulting state.
- Logarithms in the work definition have base 2; the properties list does not state a beta domain, whereas interconversion uses beta nonzero.

**原文**：[L1180–L1222](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1180>), [L1243–L1260](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1243>), [L1435–L1463](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1435>), [L1853–L1876](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1853>)

**未解项（非已证伪结论）**：

- The displayed arguments establish or invoke the listed individual properties, but no separate computational-basis measurement monotonicity argument is supplied in the read range; the full protocol monotonicity used for interconversion remains a candidate dependency.
- The earlier core-partition-function supermultiplicativity and uniqueness results cited by internal labels were not read or verified.
- The beta=0 endpoint is not specified in the properties list; no endpoint definition is supplied here.
- The supplementary subadditivity theorem at lines 1853-1876 concerns unfiltered work, which the authors explicitly say can fail to decrease under partial trace; it must not be substituted for core-work monotonicity.
- The beta subscript is absent on the right-hand work symbol in the source Clifford-invariance formula; this notation issue is retained without adjudication.

**引用线索**：RevModPhys.91.025001, PhysRevA.97.062332, Seddon2019Jul, PhysRevA.106.042422

## 稳定子功的非负性与维数相关上界

**ID**：work-bounds

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors state a nonnegative lower bound and a state-independent upper bound on stabilizer work in terms of beta and Hilbert-space dimension. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors' bound is \(0\leq\mathcal W_\beta(\psi)\leq\log\left[\frac{d_A\cosh\beta-d_A}{\cosh\beta+(d_A^2-1)\cosh(\beta/\sqrt{d_A+1})-d_A^2}\right]\).

**条件**：

- The corollary says any real beta and any n-qubit state psi in H_A, with d_A=2^n.
- The surrounding section restricts the framework to pure states.
- Work uses base-2 logarithms.

**原文**：[L1195–L1210](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1195>), [L1262–L1270](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1262>), [L1929–L1946](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1929>)

**未解项（非已证伪结论）**：

- The declared domain includes beta=0, where the printed ratio has zero numerator and denominator; an endpoint convention is not stated in this corollary and has not been inserted.
- The cited earlier state-independent partition-function theorem is outside the read range; the supplementary core bounds were read but not scientifically verified.
- No general attainability claim for the upper bound is supplied in these anchors.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 参数两端极限及其与稳定子熵的联系

**ID**：work-limits

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim that stabilizer work converges to stabilizer nullity as beta tends to infinity and that its leading small-beta magic dependence is a function of the second stabilizer Renyi entropy. They describe a continuous monotonic interpolation, with beta resolving Pauli moments rather than physical temperature. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors assert \(\lim_{\beta\to\infty}\mathcal W_\beta(\psi)=\nu(\psi)\). At small beta they write \(\mathcal Z_\beta\simeq e^{-\beta}[4^L+\frac{\beta^2}{2}\sum_P\langle P\rangle^2+\frac{\beta^4}{24}\sum_P\langle P\rangle^4+\cdots]\), assigning the first magic-dependent term to the fourth Pauli moment and the leading work dependence to M_2.

**条件**：

- The state is a fixed pure n-qubit state; the Ising expansion uses L qubits.
- The small-beta expansion uses the purity identity sum_P <P>^2=2^L.
- Beta tends to zero or positive infinity; no simultaneous thermodynamic limit is specified.

**原文**：[L1272–L1275](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1272>), [L1530–L1530](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1530>), [L1537–L1537](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1537>), [L1558–L1568](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1558>), [L1603–L1603](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1603>), [L1733–L1745](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1733>), [L1758–L1773](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1758>)

**未解项（非已证伪结论）**：

- The discussion says the high-temperature limit recovers the second Renyi entropy, while the detailed text says a leading-order function of it and the Ising caption says work tends to zero near beta=0; these different strengths are retained.
- The main text at line 1530 writes lim Z_beta=|Stab(psi)|, whereas the supplement at line 1742 writes one half of |STAB(psi)|. The normalization discrepancy is not repaired.
- A general monotonicity-in-beta statement is asserted in prose here, without an explicit quantified theorem or supporting argument in these anchors.
- The supplementary entropy-recovery formula claims integer alpha in N while displaying 1/(1-alpha); the alpha=1 case is not separately qualified.
- Earlier definitions of nullity and the core partition function were not reread in this bounded subtask.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 稳定子功的连续性界不随量子比特数增长

**ID**：work-continuity

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors state a trace-norm Lipschitz bound for stabilizer work with a constant independent of the number of qubits, and attribute improved concentration behavior to removal of the extensive partition-function normalization. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \( |\mathcal W_\beta(\psi)-\mathcal W_\beta(\phi)|\leq K_n(\beta)\|\psi-\phi\|_1\), with \(K_n(\beta)=2\beta^{-1}\sinh\beta\). They also give the state-dependent coefficient \(d_ne^{-\beta}\beta\sinh\beta/\min\{\mathcal Z^c_\beta(\psi),\mathcal Z^c_\beta(\phi)\}\).

**条件**：

- The proof takes psi and phi to be pure states on the same n-qubit space.
- The displayed formulas require positive core partition functions and contain beta inverse; no endpoint prescription is stated.
- The definition specifies base-2 logarithms.

**原文**：[L1205–L1210](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1205>), [L1284–L1317](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1284>), [L1986–L2005](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1986>), [L2007–L2076](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2007>)

**未解项（非已证伪结论）**：

- The proof uses |log(a)-log(b)| <= |a-b|/min(a,b) without addressing the base-2 logarithm convention or a log-base conversion factor; constants are retained as printed.
- The lemma says every n-qubit state, but its proof explicitly uses two pure states; no mixed-state extension is inferred.
- The supplement first gives a partition-function coefficient (4^n-1)e^(-beta) beta sinh(beta) and later refines it to d_n e^(-beta) beta sinh(beta). The earlier sentence calling the coarser result the main-text result is not used to replace the refined expression.
- The broad assertion of stronger concentration is not supplied here with an ensemble-specific failure probability or parameter regime.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 系综功偏差界与伪魔法态分类条件

**ID**：ensemble-work-gap

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim that work for a sampled state differs from work computed from the ensemble-averaged core partition function by logarithmic polynomial corrections and an O(beta^4) term. They use a separation of ensemble work values to distinguish subset phase states from nu-compressible states. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal W_\beta(\psi)-\mathcal W_\beta(\mathcal E)\in[-\mathrm{logPoly}(n),O(\beta^4)+\mathrm{LogPoly}(n)]\) with negligible failure probability. The supplement gives each one-sided event probability at least \(1-1/\mathrm{Poly}(n)\) and \(0\leq\mathrm{Small}_\beta\leq\beta^4/576\). The main-text classification condition is \( |\mathcal W_\beta(\mathrm{SPS})-\mathcal W_\beta(\mathrm{Comp}_\nu)|>\mathrm{LogPoly}(n)\).

**条件**：

- E is an ensemble of pure n-qubit states.
- W_beta(E) is the negative logarithm of the averaged core partition function plus the stabilizer reference, not the ensemble average of work.
- The classification compares subset phase states with nu-compressible states at a selected beta.
- The read supplementary subset-phase calculation restricts support to |S|=2^n and uses a uniformly random Boolean function in its cumulant lemma.

**原文**：[L1314–L1347](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1314>), [L1878–L1982](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1878>), [L2333–L2347](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2333>), [L2405–L2430](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2405>), [L2653–L2653](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2653>)

**未解项（非已证伪结论）**：

- The main text says negligible failure probability and every state; the supplement gives probabilities for a random draw with inverse-polynomial failures. The polynomial and its degree are unspecified.
- The classification display omits the explicit O(beta^4) term, while accompanying prose requires the combined confidence correction. No beta-versus-n regime or constants are fixed.
- The supplement uses exp(+/-W) and natural-log-style identities despite the base-2 work definition; line 1895 also switches from core partition functions to an inverse unfiltered Z. These source inconsistencies are retained.
- The main text describes pseudorandom subset phase states, whereas the read supplementary derivation specializes to full support and uniformly random functions. The transfer to the general pseudorandom ensemble is not supplied in the read material.
- Earlier ensemble formulas and definitions, including nu-compressibility, were not read; the plotted numerical validation and cryptographic claims were not checked.

**引用线索**：Ptk/Kantorovich/1995, Aaronson/pseudoentanglement/2022, Gu/pseudomagic/2024

## 稳定子保真度上界与近似排除判据

**ID**：fidelity-witness

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors give a beta-dependent upper bound on stabilizer fidelity, propose optimizing it to exclude sufficiently close stabilizer approximations, and connect it to a lower bound on stabilizer extent. They report a copy-independent numerical exclusion threshold for tensor powers of T states. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(F_{\mathrm{Stab}}(\psi)\leq1-\frac12[\frac{\cosh\beta-1}{\beta\sinh\beta}2^{-\mathcal W_\beta(\psi)}\mathcal W_\beta(\psi)]^2\). They define the squared bracket divided by two as epsilon_star and their algorithm prints exclusion when \(\epsilon_\star\geq\epsilon\). The example replaces work by single-copy T work and reports exclusion for \(\epsilon\lesssim2.27\times10^{-3}\), independently of the number of copies. They invoke \(\xi(\psi)\geq F_{\mathrm{Stab}}(\psi)^{-1}\).

**条件**：

- psi is pure and F_Stab is the maximum squared overlap with a pure stabilizer state of the same size.
- The proposition says beta>=0; the tensor-power example says beta>0.
- Closeness in the task means F(psi,phi)>=1-epsilon with epsilon>=0.
- The example considers n copies of T, with single-qubit density operator (I+(X+Y)/sqrt(2))/2.

**原文**：[L1353–L1387](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1353>), [L1390–L1429](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1390>), [L1610–L1612](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1610>), [L2665–L2678](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2665>)

**未解项（非已证伪结论）**：

- The beta=0 expression is singular as printed; no endpoint convention is supplied.
- At epsilon_star=epsilon, the upper-bound equality is not explicitly excluded, although the task allows fidelity equal to 1-epsilon and the algorithm prints exclusion. The source comparison is retained.
- An upper-bound witness does not supply a positive existence decision when exclusion fails; the prose describing an answer to the task is stronger than the displayed one-sided algorithm.
- The single-copy substitution in the tensor-power example is justified only by work being nondecreasing under adding factors; no monotonicity analysis of the composite function W*2^(-W) is supplied there.
- The source defines extent using the minimum coefficient l1 norm and invokes extent/fidelity and approximate-rank relations without reconciling normalization conventions; no replacement definition is inserted.
- The discussion claims a lower bound on simulation cost, but the displayed approximate-rank relation is an upper bound in terms of extent. A direct simulation-cost lower-bound statement is not supplied.
- The underlying logarithm constants, cited external results, numerical maximization and supplementary plots were not verified.

**引用线索**：PhysRevX.6.021043, Bravyi/stab_fidelity/2019, Tobi/Stab_Fidelity/2023, Gu/pseudomagic/2024, Dutt/tolerant_stab_testing_poly/2024, Bao/tolerant_stab_testing_improved/2024

## 态转换、魔法成本与蒸馏的必要条件

**ID**：conversion-witnesses

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors use stabilizer-work monotonicity and subadditivity to give necessary bounds for exact finite-copy conversion, T-state cost and distillation, and claim that crossing work curves rule out conversion in both directions. They explicitly state that work-curve dominance is not sufficient for conversion. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors state \(\mathcal W_\beta(\phi^{\otimes m})\leq\mathcal W_\beta(\psi^{\otimes n})\leq n\mathcal W_\beta(\psi)\). Opposite strict orderings at two beta values are said to imply incomparability. For T-cost they state \(t\geq\sup_{\beta\neq0}\min\{t':\mathcal W_\beta(T^{\otimes t'})\geq\mathcal W_\beta(\phi)\}\), with weaker ratio bound \(t\geq\sup_\beta\mathcal W_\beta(\phi)/\mathcal W_\beta(T)\). For distillation they state \(\mathcal W_\beta(T^{\otimes m})\leq n\mathcal W_\beta(\psi)\).

**条件**：

- Inputs and outputs are pure states, and conversions use the deterministic pure-state stabilizer protocol class of the work section.
- n and m count input and output copies; beta is nonzero.
- T-cost is the least number of T states convertible to the target; the source does not explicitly specify the minimization domain of t'.
- Conversions in these statements have no approximation error or failure branch specified.

**原文**：[L1195–L1197](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1195>), [L1433–L1505](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1433>), [L1672–L1672](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1672>)

**未解项（非已证伪结论）**：

- Full monotonicity under the stated measurement-containing protocol class is an unverified dependency of these bounds.
- The claim at line 1465 that exact tensor-power evaluation is strictly stronger whenever neither state is stabilizer is not accompanied here by an independent strictness argument or a precise single-copy comparator.
- The ratio-bound display writes sup_beta without repeating beta!=0; the domain and any endpoint conventions are not repaired.
- The H-to-T counterexample is asserted without a conversion-impossibility argument or external citation in this subsection.
- The authors leave asymptotic and catalytic sufficiency open; the finite-copy bounds are not promoted to a complete conversion criterion.
- Commented-out tensor-power and endpoint formulas are not extracted as active author statements.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 混态与量子信道的配分函数扩展及单调性保留项

**ID**：mixed-channel-extension

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors define mixed-state partition functions by a supremum over pure-state decompositions, claim that this preserves faithfulness to the convex hull of stabilizer states, and define a channel partition function using its normalized Choi state. They explicitly leave monotonicity of the extended quantities for future work. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors define \(\mathcal Z_\beta(\rho)=\sup_{\{p_i,\phi_i\}}\sum_i p_i\mathcal Z_\beta(\phi_i)\) and claim that it attains the stabilizer value exactly for free mixed states. They define \(\mathcal Z_\beta(\mathcal N)=\mathcal Z_\beta(\widetilde J_{AB}^{\mathcal N})\), where \(\widetilde J_{AB}^{\mathcal N}=(\mathrm{id}\otimes\mathcal N)(\Phi^+_{AA'})\). Monotonicity of the resulting mixed-state and channel work is explicitly an open task.

**条件**：

- rho is a finite-dimensional mixed quantum state and the supremum ranges over its pure-state decompositions with probabilities p_i.
- Free mixed states admit decompositions into pure stabilizer states.
- N is completely positive and trace preserving; the maximally entangled state used for the Choi construction is normalized and |A|=|A'|.
- The definitions declare real beta without a separate beta=0 qualification.

**原文**：[L1187–L1192](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1187>), [L1614–L1634](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1614>), [L1669–L1669](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1669>)

**未解项（非已证伪结论）**：

- The authors call the supremum construction a convex-roof extension; that terminology is retained without replacing the supremum by an infimum.
- The all-real-beta faithfulness statement is not qualified at beta=0, while the read small-beta partition-function expression has a state-independent constant term.
- An explicit mixed-state or channel core-work formula and its reference-system convention are not provided in these extension definitions.
- The equivalence with stabilizer-preserving operations invokes an earlier uniqueness result that was not read; the cited operation classes were not externally checked.
- These definitions do not establish monotonicity under mixed-state free operations or channel superoperations, which the authors expressly defer.

**引用线索**：RevModPhys.91.025001, PhysRevA.97.062332, Seddon2019Jul, PhysRevA.106.042422

## 自由操作的泡利转移矩阵刻画主张

**ID**：free-channel-pauli

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors propose an algebraic characterization of free operations through preservation of integer-valued stabilizer Pauli spectra, and describe three possible Pauli transfer matrix forms for deterministic pure-state stabilizer protocols. This is an unverified author-claim candidate whose full equivalence is not sufficiently specified for a standalone MathClaim here.

**数学表达或待规范化表达**：

The authors require \(R_{ij}^{\mathcal O}=d_A^{-1}\operatorname{tr}[P_i^B\mathcal O(P_j^A)]\), \(\sum_jR_{ij}^{\mathcal O}p_j^\phi\in\{0,\pm1\}\), and \(\sum_i|\sum_jR_{ij}^{\mathcal O}p_j^\phi|=d_B\). They then claim that protocol matrices are signed permutations, discard-and-prepare matrices with only a stabilizer-spectrum first column, or discarding matrices with exactly one 1 in every column, and identify free operations with preservation of this rigid spectrum structure.

**条件**：

- O maps system A to B and is completely positive and trace preserving.
- The output constraints are imposed for every pure stabilizer input phi_A and every output Pauli operator.
- The transfer matrix is normalized by the input dimension d_A.

**原文**：[L1189–L1198](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1189>), [L1636–L1658](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1636>)

**未解项（非已证伪结论）**：

- The work section separates the maximal stabilizer-preserving channel class from deterministic pure-state stabilizer protocols; this discussion passes from output constraints to an exact protocol characterization without establishing the equivalence in the read text.
- The three matrix forms do not specify closure under composition, ancilla preparation, measurement or conditional corrections, although the earlier protocol description includes preparations and measurements.
- The discarding-matrix assertion says exactly one 1 per column without specifying subsystem indexing or the treatment of all other entries; it is retained as printed.
- The explicit output constraints can be isolated as mathematical expressions, but the claimed complete channel classification needs further semantic specification; math_extractable=false applies to this combined classification candidate.
- No PTM characterization or approximate-hardware assertion has been scientifically verified.

**引用线索**：本条未列外部引用线索；不表示没有历史依赖。

## 氢分子解离中的魔法特征及基组敏感性

**ID**：hydrogen-basis-effects

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors report that stabilizer work diagnoses nonstabilizerness along H2 dissociation, with low values near equilibrium and enhanced values in an intermediate correlated region. Their larger-basis calculation changes the peak position, dissociation behavior and ordering of two geometries, so they refrain from assigning intrinsic physical significance to dissociation-limit magic. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors report a magic peak along dissociation in both bases. In STO-3G the magic decreases toward dissociation and \(\mathcal W_\beta(R=0.5)>\mathcal W_\beta(R=6)\); in 6-31G appreciable large-R magic remains and this ordering reverses. They describe beta scans as resolving different Pauli moments, with work increasing and saturating for each illustrated geometry.

**条件**：

- Ground states are obtained by full diagonalization within a chosen finite one-particle basis and Jordan-Wigner encoding.
- STO-3G uses four spin-orbitals and four qubits; 6-31G uses eight spin-orbitals and eight qubits.
- The plots use beta in {0.5,2,10,50,100} and compare R=0.5 and R=6 bohr.
- Neither calculation is in the complete-basis-set limit.

**原文**：[L1516–L1532](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1516>), [L2704–L2721](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2704>)

**未解项（非已证伪结论）**：

- The supplementary reversal qualifies the main-text minimal-basis trend; it is an explicitly reported basis dependence, not a universal molecular ordering.
- Magic depends on the one-particle basis and fermion-to-qubit encoding; no intrinsic dissociation-limit molecular value is established.
- Residual configuration mixing is presented as a plausible explanation, not a demonstrated causal mechanism.
- Numerical data, Hamiltonian construction, figure files and computation code were not inspected or rerun.
- The qualitative claims do not specify quantitative peak locations, tolerances or parameter-wide inequalities sufficient for a standalone MathClaim.

**引用线索**：sarkis2025moleculesmagicalnonstabilizernessmolecular

## Ising 模型中的参数扫描与有限尺寸限定

**ID**：ising-moment-scan

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors report increasing and saturating stabilizer work with beta in the transverse-field Ising model, enhanced nonstabilizerness near the transition, and richer moment information than a single stabilizer Renyi index. The supplement qualifies the peak description by reporting a broad nearly saturated plateau at beta=100. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors describe \(\mathcal W_\beta\) as rising and saturating with beta, with size ordering suggestive of extensivity. They assign zero magic to the GHZ and plus-product endpoint states and locate an interior magic ridge near \(h/g=1\). The supplement reports ordered-side maxima at beta=0.5,2,10 and a broad nearly saturated plateau at beta=100.

**条件**：

- The model is the one-dimensional transverse-field Ising Hamiltonian H=-g sum_i sigma_i^z sigma_(i+1)^z-h sum_i sigma_i^x.
- Beta is a Pauli-moment resolving parameter rather than physical temperature.
- The main plot includes the paramagnetic point h/g approximately 1.5 and a landscape with L=8; supplementary scans use beta=0.5,2,10,100.
- The numerical claims concern finite systems and their selected ground states.

**原文**：[L1534–L1593](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1534>), [L2681–L2701](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2681>)

**未解项（非已证伪结论）**：

- The main text calls the ridge robust at large beta; the supplement reports a qualitative change to a broad plateau at beta=100. Both descriptions are retained without forcing them into a single peak claim.
- Size ordering is called evidence for extensivity, but no thermodynamic-limit scaling estimate is supplied in these passages.
- Lines 1574-1576 associate a saturation of order L-1 with a sentence about pure stabilizer states, while other read passages assign stabilizer states zero work; the intended comparison is ambiguous.
- The endpoint GHZ identification does not specify boundary conditions or a ground-state selection convention at degeneracy.
- The Hamiltonian uses g while its explanatory sentence names J; the discrepancy is not silently resolved.
- Figure files, ground-state computations and quantitative scaling were not inspected or verified; these qualitative observations are not a standalone MathClaim.

**引用线索**：sachdev2011quantum, anonquantum, kyaw2020dynamical, bastidas2018floquet, kyaw2018cluster

## 配分函数估计的归一化、截断误差与资源条件

**ID**：sampling-qualifications

**状态**：尚未生成 MathClaim；条件／量词或合并主张有残余。

**作者主张**：The authors claim that a Bell-sampling run with classical memory estimates the even-moment vector with O(kn) classical runtime, and give concentration bounds for the normalized truncated and full partition functions. These supplementary statements qualify the discussion's broad uniform-cost additive-estimation claim. This is an unverified author-claim candidate.

**数学表达或待规范化表达**：

The authors give truncated-estimator sample count \(N=O(e^{-2\beta}\cosh^2\beta\,\epsilon^{-2}\log(1/\delta))\). For \(\Delta(\beta,k)=d_ne^{-\beta}[\cosh\beta-\sum_{l=0}^k\beta^{2l}/(2l)!]\), they state \(\Pr[(\mathcal Z_\beta-\widehat{\mathcal Z}^{(k)}_\beta)/d_n\geq\epsilon]\leq2\exp[-N(\epsilon-\Delta)^2e^{2\beta}/(2\cosh^2\beta)]\), provided \(\epsilon>\Delta\).

**条件**：

- psi is a pure n-qubit state and d_n=2^n.
- The algorithm assumes preparation of both psi and its complex conjugate psi*, Bell sampling, and repeated measurement of psi in a sampled Pauli eigenbasis.
- The truncation includes even powers through 2k; the algorithm requires integer k>1.
- Samples are taken in N outer-loop runs and the full-function theorem requires epsilon>Delta(beta,k).
- Efficiency in the supplementary prose is stated for fixed k and beta.

**原文**：[L1603–L1603](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:1603>), [L2089–L2188](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2089>), [L2192–L2231](</Users/Yingjian/Documents/GitHub/AgtXIv/Reference/Stabilizer Statistical Mechanics - A Framework for Efficient Quantification and Classification of Magic States/source/Pauli_Spectrum.tex:2192>)

**未解项（非已证伪结论）**：

- The discussion describes uniform-cost additive estimation of the partition function; the supplement explicitly estimates Z_beta/d_n and retains dimension dependence in Delta. No blanket unnormalized full-function accuracy guarantee is inferred.
- The algorithm's preparation of psi* is an additional access assumption; its implementation cost is not accounted for in the stated classical runtime.
- The defined moment vector starts with normalized sum x^2, whereas the Bell-sampled algorithm stores products after two and more additional Pauli measurements. The correspondence between this indexing and the claimed unbiased vector is not explained in the read text; it is not repaired.
- The O(kn) statement describes a single run; total repeated-run time, state copies and choosing k to meet epsilon>Delta are separate resources.
- The full-function display lacks the absolute value present in the truncated-estimator bound; it is not silently upgraded to a two-sided statement.
- The earlier main-text sampling theorem and the cited Bell-sampling paper were not read or verified; no sampling experiment or TeX execution was performed.

**引用线索**：Tobias/Pauli_sampling/2024

