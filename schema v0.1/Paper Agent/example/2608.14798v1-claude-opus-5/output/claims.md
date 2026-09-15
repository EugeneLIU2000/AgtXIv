# Author claims extracted from arXiv:2608.14798v1

Reading view of `records.json`. The JSON records are authoritative; this file is an attachment.
Every quoted condition, component and residual is a reading of the source text, not a judgement
about whether the paper is right. Nothing here was proved, checked or reproduced.

Claims: 36. Definitions: 15. MathClaims: 32. SemanticContexts: 2. Open frontier items: 49.

| # | Section | Claim | Modality | Components | Coverage | Open items |
|---|---|---|---|---|---|---|
| c01 | Sec. II B | Signed Pauli spectrum convention | ASSERTED | 4 | PARTIAL | 1 |
| c02 | Sec. II B | Pauli spectrum of pure stabilizer states | ASSERTED | 1 | COMPLETE | 0 |
| c03 | Sec. II B | Pauli spectrum is not Clifford invariant | ASSERTED | 3 | PARTIAL | 1 |
| c04 | Sec. II B, II C 1 | Support/kernel splitting and kernel bounds | ASSERTED | 3 | PARTIAL | 1 |
| c05 | Sec. II C 2, Sec. I | Renyi hierarchy and coarseness of existing measures | ASSERTED | 4 | PARTIAL | 1 |
| c06 | Sec. III A | Pauli gas construction | INTERPRETIVE | 5 | PARTIAL | 2 |
| c07 | Sec. III B | SPF definition and moment-generating reading | ASSERTED | 5 | PARTIAL | 2 |
| c08 | Sec. III B, Sec. V | Core SPF removes the leading constant | ASSERTED | 3 | PARTIAL | 0 |
| c09 | Sec. III C 1 | SPF is Clifford invariant and uniquely valued on stabilizer states | ASSERTED | 4 | PARTIAL | 1 |
| c10 | Sec. III C 2 | Clifford-orbit and stabilizer-Renyi representations | ASSERTED | 5 | PARTIAL | 1 |
| c11 | Sec. III C 3 | Lipschitz robustness of the SPF | ASSERTED | 3 | PARTIAL | 1 |
| c12 | Sec. III C 5 | SPF state-independent bounds | ASSERTED | 3 | PARTIAL | 1 |
| c13 | Sec. III C 5 | SPF state-dependent bounds in terms of M2 | ASSERTED | 3 | PARTIAL | 1 |
| c14 | Sec. III C 4, Supplemental Material | SPF is estimable by Bell sampling | CONDITIONAL | 6 | PARTIAL | 3 |
| c15 | Sec. IV A | SPF of tensor powers of single-qubit states | ASSERTED | 3 | PARTIAL | 1 |
| c16 | Sec. IV B | SPF of separable bipartite states and its stabilizer special case | ASSERTED | 4 | PARTIAL | 2 |
| c17 | Sec. IV B | cSPF supermultiplicativity | ASSERTED | 3 | PARTIAL | 2 |
| c18 | Sec. IV C | Exact ensemble-averaged SPF for Haar-random states | ASSERTED | 4 | PARTIAL | 1 |
| c19 | Sec. IV C | Concentration of the SPF for Haar states, and Haar certification | ASSERTED | 4 | PARTIAL | 2 |
| c20 | Sec. IV D | Exact ensemble SPF for nu-compressible and t-doped states | ASSERTED | 6 | PARTIAL | 2 |
| c21 | Sec. IV E | Exact ensemble SPF for pseudomagic subset phase states | ASSERTED | 6 | PARTIAL | 2 |
| c22 | Sec. V, Sec. VII | Free states and free operations of the resource theory | ASSERTED | 4 | PARTIAL | 1 |
| c23 | Sec. V, abstract | Stabilizer work is a faithful subadditive magic monotone | ASSERTED | 5 | PARTIAL | 2 |
| c24 | Sec. V | Bounds, limits and the interpolation claim for stabilizer work | ASSERTED | 4 | PARTIAL | 2 |
| c25 | Sec. V A | Continuity of stabilizer work and its dimension-free constant | ASSERTED | 3 | PARTIAL | 1 |
| c26 | Sec. V A | Ensemble averages of stabilizer work and the small-gap lemma | APPROXIMATE | 4 | PARTIAL | 1 |
| c27 | Sec. VI A | Stabilizer fidelity upper bound from stabilizer work | ASSERTED | 4 | PARTIAL | 2 |
| c28 | Sec. VI B | Interconversion bounds, magic cost and distillation converse | CONDITIONAL | 6 | PARTIAL | 2 |
| c29 | Sec. VI C and Supplemental Material | H2 dissociation: stabilizer work as a chemistry diagnostic | OBSERVED | 4 | COMPLETE | 2 |
| c30 | Sec. VI D and Supplemental Material | Transverse-field Ising: extensivity and a nonstabilizerness ridge | OBSERVED | 4 | COMPLETE | 2 |
| c31 | Sec. VII | Extensions to mixed states and channels | ASSERTED | 4 | PARTIAL | 1 |
| c32 | Abstract, Sec. VII | Framing claims of the abstract and discussion | ASSERTED | 6 | PARTIAL | 1 |
| c33 | Sec. III C | What the SPF discards | ASSERTED | 2 | PARTIAL | 1 |
| c34 | Supplemental Material | Integer SREs recoverable from the SPF by differentiation | ASSERTED | 3 | PARTIAL | 1 |
| c35 | Supplemental Material | Unfiltered stabilizer work and why the core SPF is used | ASSERTED | 3 | PARTIAL | 1 |
| c36 | Supplemental Material | Variational lower bound on the SPF | ASSERTED | 2 | PARTIAL | 1 |

---

## c01 — Signed Pauli spectrum convention

*Sec. II B · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The paper defines the Pauli spectrum with the sign retained, ${\rm Spec}(\psi)=\{\tr(\psi P)\}_{P\in\mathcal{P}_n}$, rather than the absolute-value convention of Beverland et al., stating that the signed convention is the natural one for the typical-set analysis developed later and that the absolute-value version can be recovered whenever needed.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the $|\tr(\psi P)|$ convention of Beverland et al. (2020)

**Stated conditions.**

- (SOURCE_EXPLICIT) $\ket{\psi}$ is an $n$-qubit pure state
- (SOURCE_EXPLICIT) Pauli operators are taken modulo phase; global phases irrelevant

**Components and their accounting.**

- `comp:def` [DEFINITION / MAPPED] ${\rm Spec}(\psi):=\{\tr(\psi P)\ \text{for}\ P\in\mathcal{P}_n\}$, $4^n$ real entries.
- `comp:multiset` [DEFINITION / RESIDUAL] Spec should be read as a multiset because multiplicities matter (stated in a footnote, not in the displayed definition).
  - residual: The multiset reading is given only in a footnote; the displayed definition uses set braces. Which of the two the later theorems rely on is not fixed in the source.
- `comp:recover` [ASSUMPTION / RESIDUAL] The absolute-value convention 'can be recovered whenever needed'.
  - residual: No recovery map from the signed to the absolute-value convention is given, and no statement of which later results are convention-dependent.
- `comp:witness` [CONCLUSION / RESIDUAL] The Pauli spectrum separates stabilizer structure from nonstabilizer behaviour and is therefore a magic witness.
  - residual: 'Magic witness' is used informally here; no witness soundness/completeness statement is attached at this point in the text.

**Math target `m01`** (EXACT), covering `comp:def`.

- conclusion: ${\rm Spec}(\psi)$ is the multiset $\{\tr(\psi P)\}_{P\in\mathcal{P}_n}$ of cardinality $4^n$, with $\tr(\psi\mathbb{I})=1$ always present.
- quantifier: FORALL n in positive integers
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_EXPLICIT): $\psi=\ket{\psi}\bra{\psi}$ is a rank-one projector on $\mathcal{H}_n$
- normalization: entries lie in $[-1,1]$; $\sum_{P\in\mathcal{P}_n}\tr(\psi P)^2=d_n$ for pure states (used implicitly elsewhere in the paper, not stated here)

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity] Set-versus-multiset reading of ${\rm Spec}(\psi)$ is fixed only in a footnote while the displayed definition uses set notation.
  - what could settle it: An author clarification, or a check of which downstream sums (SPF, SRE) require multiplicity, would settle this.

Records: `claim:opus5-2608.14798v1/c01`, `map:opus5-2608.14798v1/c01`, `math:opus5-2608.14798v1/m01`.

## c02 — Pauli spectrum of pure stabilizer states

*Sec. II B · modality ASSERTED · coverage COMPLETE*

**What the authors said.** Proposition (Stabilizer Pauli Spectrum): the Pauli spectrum of a pure $n$-qubit stabilizer state of a system $A$ consists of $d_A^2-d_A$ zeros and $d_A$ entries equal to $\pm1$.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** general pure states, whose spectra contain non-integer entries

**Stated conditions.**

- (SOURCE_EXPLICIT) $\ket{\psi}$ is a pure $n$-qubit stabilizer state
- (SOURCE_EXPLICIT) $d_A=|A|=2^{n}$ is the dimension of system $A$

**Components and their accounting.**

- `comp:count` [CONCLUSION / MAPPED] Exactly $d_A$ spectrum entries equal $\pm1$ and the remaining $d_A^2-d_A$ entries vanish.

**Math target `m02`** (EXACT), covering `comp:count`.

- conclusion: $|\{x\in{\rm Spec}(\psi):|x|=1\}|=d_A$ and $|\{x\in{\rm Spec}(\psi):x=0\}|=d_A^2-d_A$.
- quantifier: FORALL n in positive integers
- quantifier: FORALL \psi in pure stabilizer states of an $n$-qubit system $A$, $d_A=2^n$
- assumption (SOURCE_EXPLICIT): $\ket{\psi}\in{\rm Stab}_n$, i.e. the unique common $+1$ eigenstate of an abelian subgroup of $\widetilde{\mathcal{P}}_n$ generated by $n$ independent commuting Paulis
- normalization: $d_A=2^n$ denotes the Hilbert-space dimension of $A$ (Sec. II convention $d_A=|A|=2^n$)

Records: `claim:opus5-2608.14798v1/c02`, `map:opus5-2608.14798v1/c02`, `math:opus5-2608.14798v1/m02`.

## c03 — Pauli spectrum is not Clifford invariant

*Sec. II B · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The Pauli spectrum is not invariant under general Clifford unitaries: Clifford conjugation may permute spectrum entries and flip their signs. For stabilizer states this permutes and sign-changes the $\pm1$ entries while leaving the stabilizer-group size unchanged, so $|{\rm Stab}(\psi)|$ can be read off by counting entries with $|x|=1$.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** Clifford-invariant functionals such as $M_\alpha$ and (later) the SPF

**Stated conditions.**

- (SOURCE_EXPLICIT) $\mathcal{C}\in\mathcal{C}l_n$ acts by conjugation

**Components and their accounting.**

- `comp:noninv` [CONCLUSION / RESIDUAL] ${\rm Spec}(\psi)\neq{\rm Spec}(\mathcal{C}(\psi))$ in general.
  - residual: The source says 'not invariant ... for any arbitrary Clifford', which literally reads as 'for every Clifford'; the intended reading is 'not invariant in general'.
- `comp:action` [MODEL / MAPPED] The action is by permutation and/or sign flip of spectrum entries.
- `comp:readoff` [CONCLUSION / MAPPED] The stabilizer-group size is invariant and readable from the count of $|x|=1$ entries.

**Math target `m03`** (EXACT), covering `comp:action`, `comp:readoff`.

- conclusion: For every $\mathcal{C}\in\mathcal{C}l_n$ there is a permutation $\pi$ of $\mathcal{P}_n$ and signs $s_P\in\{\pm1\}$ with $\tr(\mathcal{C}(\psi)P)=s_P\tr(\psi\,\pi(P))$; consequently $|\{x\in{\rm Spec}(\psi):|x|=1\}|$ is Clifford invariant.
- quantifier: FORALL \mathcal{C} in $\mathcal{C}l_n$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_EXPLICIT): $\mathcal{C}l_n=\{U\in U(2^n):U\mathcal{P}_nU^\dagger=\mathcal{P}_n\}$, i.e. Cliffords map Paulis to Paulis up to phase
- normalization: phase-free Pauli labels; the sign is carried by the spectrum entry, not by the label

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity] Quantifier wording 'for any arbitrary Clifford unitary' is ambiguous between 'for some' and 'for every'.
  - what could settle it: Author clarification; the surrounding argument only needs 'not invariant in general'.

Records: `claim:opus5-2608.14798v1/c03`, `map:opus5-2608.14798v1/c03`, `math:opus5-2608.14798v1/m03`.

## c04 — Support/kernel splitting and kernel bounds

*Sec. II B, II C 1 · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Every pure state induces a disjoint decomposition $\mathcal{P}_n={\rm Supp}(\psi)\cup{\rm Ker}_\mathcal{P}(\psi)$ with $|{\rm Supp}|+|{\rm Ker}_\mathcal{P}|=d_n^2$, ${\rm Stab}(\psi)\subseteq{\rm Supp}(\psi)$ with equality for stabilizer states, and the kernel obeys $2^n(2^n-2^{\nu(\psi)})\leq|{\rm Ker}_\mathcal{P}(\psi)|\leq 4^n-2^n$.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the trivial bound |Ker| <= 4^n - |Stab(psi)|

**Stated conditions.**

- (SOURCE_EXPLICIT) $\psi$ is pure
- (SOURCE_EXPLICIT) The lower bound uses $|{\rm Supp}(\psi)|=d\,2^{M_0(\psi)}\leq d\,2^{\nu(\psi)}$, attributed to Leone et al. (2024), with $M_0$ the zero-order stabilizer Renyi entropy

**Components and their accounting.**

- `comp:split` [CONCLUSION / RESIDUAL] Disjoint decomposition of $\mathcal{P}_n$ into support and Pauli kernel.
- `comp:bounds` [CONCLUSION / MAPPED] $2^n(2^n-2^{\nu})\leq|{\rm Ker}_\mathcal{P}(\psi)|\leq 4^n-2^n$.
- `comp:tighter` [EVIDENCE / UNRESOLVED] The proof first derives the nullity-dependent upper bound $4^n-2^{n-\nu(\psi)}$ and then replaces it by the state-independent $4^n-2^n$, described as 'tighter more fundamental'.
  - residual: For $\nu>0$ the displayed 'tighter' bound $4^n-2^n$ is weaker than $4^n-2^{n-\nu}$; the source calls it tighter and attributes tightness to the stabilizer case $\nu=0$, where the two coincide. The intended comparison is not stated.

**Math target `m04`** (EXACT), covering `comp:bounds`.

- conclusion: $2^{n}(2^{n}-2^{\nu(\psi)})\ \leq\ |{\rm Ker}_{\mathcal{P}}(\psi)|\ \leq\ 4^{n}-2^{n}$.
- quantifier: FORALL n in positive integers
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$ with stabilizer nullity $\nu(\psi)$
- assumption (SOURCE_EXPLICIT): $|{\rm Supp}(\psi)|=d_n 2^{M_0(\psi)}$ and $M_0(\psi)\leq\nu(\psi)$ (imported)
- assumption (SOURCE_EXPLICIT): $|{\rm Supp}(\psi)|+|{\rm Ker}_{\mathcal{P}}(\psi)|=d_n^2$
- normalization: $d_n=2^n$; counts are over phase-free Pauli labels

**Open items recorded against this claim.**

- [CONFLICT · source_fidelity, mathematical_correctness] The proof of the kernel bound describes $|{\rm Ker}|\leq 4^n-2^n$ as 'tighter' than $4^n-2^{n-\nu(\psi)}$, but for $\nu>0$ the latter is the stronger statement.
  - what could settle it: Author clarification, or a decision on which bound downstream results use; nothing later in the paper appears to depend on the distinction.

Records: `claim:opus5-2608.14798v1/c04`, `map:opus5-2608.14798v1/c04`, `math:opus5-2608.14798v1/m04`.

## c05 — Renyi hierarchy and coarseness of existing measures

*Sec. II C 2, Sec. I · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The stabilizer Renyi entropies are faithful, Clifford-stable and additive, and are magic monotones for $\alpha\geq2$; they satisfy $M_\alpha(\psi)\leq M_0=\log(|{\rm Supp}(\psi)|/d_n)\leq\nu(\psi)$, and $M_\alpha(\psi)\leq 2\log{\rm RoM}(\psi)$ and $M_\alpha(\psi)\leq T(\psi)$ for $\alpha\geq\frac12$. The paper's framing claim is that computable measures carry structural caveats (monotonicity unresolved for $\alpha<2$; estimation cost grows exactly where the measure is largest; nullity cannot separate states with trivial stabilizer group) while operationally strong measures are not evaluable at scale.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** robustness of magic, stabilizer extent/rank, relative entropies of magic, T-count

**Stated conditions.**

- (SOURCE_EXPLICIT) Monotonicity of $M_\alpha$ under stabilizer protocols is stated only for $\alpha\geq2$ and described as unresolved for $\alpha<2$
- (SOURCE_EXPLICIT) Bell-sampling measurability is stated for integer $\alpha\geq2$

**Components and their accounting.**

- `comp:props` [EVIDENCE / RESIDUAL] $M_\alpha$ is faithful, Clifford-stable, additive, and a monotone for $\alpha\geq2$.
- `comp:hier` [CONCLUSION / MAPPED] $M_\alpha\leq M_0=\log(|{\rm Supp}|/d_n)\leq\nu$.
  - residual: The index range of $\alpha$ in the hierarchy is not stated at this point in the text.
- `comp:rom` [CONCLUSION / RESIDUAL] $M_\alpha\leq2\log{\rm RoM}$ and $M_\alpha\leq T$-count for $\alpha\geq\frac12$.
  - residual: The admissible index range '$\alpha\geq\frac12$' for the RoM and T-count bounds is asserted without proof or citation at this point.
- `comp:tradeoff` [LIMITATION / RESIDUAL] Framing claim: no existing measure is simultaneously resource-theoretically clean, computable/measurable and fine-grained.
  - residual: A survey-level framing judgement about the literature; not a mathematical statement and not checkable from this paper alone.

**Math target `m05`** (EXACT), covering `comp:hier`.

- conclusion: $M_\alpha(\psi)\leq M_0(\psi)=\log(|{\rm Supp}(\psi)|/d_n)\leq\nu(\psi)$.
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- quantifier: FORALL \alpha in the index range over which the Renyi hierarchy is claimed; the source does not state it at this point
- assumption (SOURCE_EXPLICIT): $M_\alpha$ is the stabilizer Renyi entropy of the distribution $\Xi(\psi)$
- normalization: $\log$ base 2; $M_0=\log(|{\rm Supp}|/d_n)$ uses the support cardinality, not the Renyi limit computed from $\Xi$

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity] The Renyi-hierarchy inequality is stated without its admissible range of $\alpha$.
  - what could settle it: Author clarification or an independent check against Leone et al. (2024); not attempted in this round.

Records: `claim:opus5-2608.14798v1/c05`, `map:opus5-2608.14798v1/c05`, `math:opus5-2608.14798v1/m05`.

## c06 — Pauli gas construction

*Sec. III A · modality INTERPRETIVE · coverage PARTIAL*

**What the authors said.** The Pauli spectrum is reinterpreted as the energy spectrum of a fictitious many-body system. In Perspective 1 the stabilizer Hamiltonian $\hat H(\psi)$ on $\mathcal{H}_n^{\otimes2}\otimes\mathbb{C}^2$ has a $|{\rm Stab}(\psi)|$-fold degenerate ground level and is block diagonal in the parity sectors; in Perspective 2 each Pauli labels a two-level particle with energies $1\pm\tr[\psi_A P]$, giving $d^2$ particles in the band $[0,2]$, with the identity Pauli pinning the band edges. The dictionary asserted is: stabilizer states give a maximally rigid gas with only integer levels $\{0,1,2\}$ and ground-level degeneracy $d$; magic populates fractional interior levels and depletes the degenerate ground level.

**System.** fictitious many-body ensemble of $d^2=4^n$ two-level particles derived from an $n$-qubit pure state

**Comparison baseline.** a pure stabilizer state, for which the gas has only the integer levels $\{0,1,2\}$

**Stated conditions.**

- (SOURCE_EXPLICIT) $\psi_A$ pure
- (SOURCE_EXPLICIT) Perspective 1 is set up from the POVM $\{\Pi_P^\pm=\frac{1}{2d_n^2}(\mathbb{I}\pm P)\}$ and the large-shot empirical distribution

**Components and their accounting.**

- `comp:ham` [MODEL / RESIDUAL] $\hat H(\psi)=\sum_{P,s}(1-s\tr(\psi P))|P,s)(P,s|$ with $|{\rm Stab}(\psi)|$-degenerate ground level.
  - residual: The block-diagonal decomposition $\hat H=\hat H_+\oplus\hat H_-$ and the parity operator $\hat n$ are stated with details deferred to the supplement.
- `comp:gas` [MODEL / RESIDUAL] $d^2$ two-level particles with energies $E_{P,\pm}=1\pm\tr[\psi_AP]$ in the band $[0,2]$.
  - residual: The two perspectives are not shown to be equivalent; Perspective 1 lives on $\mathcal{H}_n^{\otimes2}\otimes\mathbb{C}^2$ while Perspective 2 is a bookkeeping device over $\mathcal{P}_n$.
- `comp:physical` [MODEL / RESIDUAL] For every non-identity Pauli, $E_{P,\pm}$ is claimed to be 'the energy of a genuine physical state $(I\pm P)/d$'.
  - residual: '$E_{P,\pm}$ is the energy of a genuine physical state $(I\pm P)/d$' is not an equation in the source: no Hamiltonian is given for which $(I\pm P)/d$ is an eigenstate with that eigenvalue. Read as interpretive, not as an established identity.
- `comp:dictionary` [CONCLUSION / RESIDUAL] Rigid integer levels for stabilizer states; magic populates fractional levels and depletes ground degeneracy.
- `comp:thermo` [MODEL / RESIDUAL] Nonstabilizerness is recast as a macroscopic spectral property of a thermodynamically large ensemble, and the zero-temperature limit is presented as a third-law statement.
  - residual: Thermodynamic vocabulary (temperature, third law, thermodynamically large) is used by analogy; the source states explicitly that $\beta$ has no connection to a physical temperature.

**Math target.** None. This claim was not forced into a MathClaim; its meaning is retained in the claim record and, where applicable, in a SemanticContext.

**Open items recorded against this claim.**

- [MODEL_ASSUMPTION · semantic_applicability] The two Pauli-gas constructions are introduced as complementary but never reconciled; the SPF definition uses Perspective 1's $\hat H(\psi)$ while all later reasoning uses Perspective 2's band picture.
  - what could settle it: An explicit isomorphism between the two constructions, or a statement that only one is load-bearing.
- [MODEL_ASSUMPTION · semantic_applicability] The claim that $E_{P,\pm}$ is the energy of a 'genuine physical state' is not supported by an equation in the text.
  - what could settle it: Identification of the operator whose spectrum this is, or restatement as an analogy.

Records: `claim:opus5-2608.14798v1/c06`, `map:opus5-2608.14798v1/c06`.

## c07 — SPF definition and moment-generating reading

*Sec. III B · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The stabilizer partition function is defined as $\mathcal{Z}_\beta(\psi)=\frac12\tr[e^{-\beta\hat H(\psi)}]=e^{-\beta}\sum_{x\in{\rm Spec}(\psi)}\cosh(\beta x)$ and is described as a moment-generating function that captures the full statistical properties of the Pauli spectrum rather than a single moment. Its limits are $\lim_{\beta\to0}\mathcal{Z}_\beta(\psi)=d_n^2$ and $\lim_{\beta\to\infty}\mathcal{Z}_\beta(\psi)=|{\rm STAB}(\psi)|/2$.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** a single stabilizer Renyi entropy $M_\alpha$ at fixed $\alpha$, which fixes one moment

**Stated conditions.**

- (SOURCE_EXPLICIT) $\beta\in\mathbb{R}$

**Components and their accounting.**

- `comp:def` [DEFINITION / MAPPED] $\mathcal{Z}_\beta(\psi)=\frac12\tr[e^{-\beta\hat H(\psi)}]=e^{-\beta}\sum_{x\in{\rm Spec}(\psi)}\cosh(\beta x)$.
- `comp:mgf` [MODEL / RESIDUAL] The SPF is a moment-generating function capturing the full statistics of the Pauli spectrum.
  - residual: 'Moment-generating function' is used for $\sum_x\cosh(\beta x)$, which generates even moments only; odd moments are not accessible. The source does not state this restriction here.
- `comp:hi-t` [CONCLUSION / MAPPED] $\lim_{\beta\to0}\mathcal{Z}_\beta(\psi)=d_n^2$ for every state.
- `comp:lo-t` [CONCLUSION / RESIDUAL] $\lim_{\beta\to\infty}\mathcal{Z}_\beta(\psi)=|{\rm STAB}(\psi)|/2$.
  - residual: The supplemental material derives this limit from the block decomposition $\hat H=\hat H_+\oplus\hat H_-$ and obtains $\tfrac12|{\rm STAB}(\psi)|$, so the Sec. III B value is the supported one. Sec. VI C states the same limit without the factor $1/2$; the two cannot both be right.
- `comp:rewrite` [CONCLUSION / UNRESOLVED] For every $\beta$, $\mathcal{Z}_\beta(\psi)=e^{-\beta}(|{\rm Ker}(\psi)|+\sum_{P\in{\rm Supp}(\psi)}\cosh(\tr{P\psi}))$.
  - residual: As printed, the rewrite has $\cosh(\tr{P\psi})$ without the factor $\beta$ inside the hyperbolic cosine, which is inconsistent with the definition and with the $e^{-\beta}|{\rm Ker}|$ term. Read as a typographical omission; not repaired here.

**Math target `m07`** (EXACT), covering `comp:def`, `comp:hi-t`.

- conclusion: $\mathcal{Z}_\beta(\psi)=e^{-\beta}\sum_{x\in{\rm Spec}(\psi)}\cosh(\beta x)$ and $\mathcal{Z}_0(\psi)=d_n^2$.
- quantifier: FORALL \beta in $\mathbb{R}$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_RECONSTRUCTED): the sum runs over the full multiset ${\rm Spec}(\psi)$ of $4^n$ entries, identity included
- normalization: $\mathcal{Z}_0=d_n^2$ fixes the normalization; the SPF is not normalized to 1

**Open items recorded against this claim.**

- [CONFLICT · source_fidelity] The low-temperature limit is stated as $|{\rm STAB}(\psi)|/2$ in Sec. III B and, in the supplemental material, derived as $\tfrac12|{\rm STAB}(\psi)|$; Sec. VI C states it as $|{\rm Stab}(\psi)|$ without the factor. The Sec. VI C form is the one that disagrees with the derivation.
  - what could settle it: Errata on the Sec. VI C sentence. Nothing in the numerical discussion appears to depend on the factor, but the two statements as printed are incompatible.
- [SCOPE_AMBIGUITY · source_fidelity] The support/kernel rewrite of the SPF omits $\beta$ inside $\cosh$.
  - what could settle it: Errata or author confirmation that the intended expression is $\cosh(\beta\tr[P\psi])$.

Records: `claim:opus5-2608.14798v1/c07`, `map:opus5-2608.14798v1/c07`, `math:opus5-2608.14798v1/m07`.

## c08 — Core SPF removes the leading constant

*Sec. III B, Sec. V · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The core SPF is defined by dropping the leading-order constant of the SPF, $\mathcal{Z}^c_\beta(\psi)=e^{-\beta}\sum_x(\cosh(\beta x)-1)=\mathcal{Z}_\beta(\psi)-d^2e^{-\beta}$; for stabilizer states it takes the simpler form $\mathcal{Z}^c_\beta({\rm STAB}_n)=e^{-\beta}d_n(\cosh\beta-1)$. The stated reason for using the cSPF to build the monotone is that the SPF's leading term scales with the number of Pauli operators and does not combine multiplicatively under tensor products in a manner consistent with the higher-moment structure.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the unfiltered SPF $\mathcal{Z}_\beta$

**Stated conditions.**

- (SOURCE_EXPLICIT) $\beta\in\mathbb{R}$

**Components and their accounting.**

- `comp:def` [DEFINITION / MAPPED] $\mathcal{Z}^c_\beta(\psi)=\mathcal{Z}_\beta(\psi)-d^2e^{-\beta}$.
  - residual: Subscript on $d$ is dropped in the displayed equation.
- `comp:stab` [CONCLUSION / MAPPED] $\mathcal{Z}^c_\beta({\rm STAB}_n)=e^{-\beta}d_n(\cosh\beta-1)$.
- `comp:why` [ASSUMPTION / RESIDUAL] Motivation: the removed term is the Pauli count and spoils multiplicative composition.
  - residual: 'Does not combine multiplicatively ... in a manner consistent with the higher-order moment structure' is a motivation, not a proved statement; no counterexample or inequality is given at this point.

**Math target `m08`** (EXACT), covering `comp:def`, `comp:stab`.

- conclusion: $\mathcal{Z}^c_\beta(\psi)=e^{-\beta}\sum_{x\in{\rm Spec}(\psi)}(\cosh(\beta x)-1)=\mathcal{Z}_\beta(\psi)-d_n^2e^{-\beta}$, and $\mathcal{Z}^c_\beta(\phi)=e^{-\beta}d_n(\cosh\beta-1)$ for every $\phi\in{\rm Stab}_n$.
- quantifier: FORALL \beta in $\mathbb{R}$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_RECONSTRUCTED): $|{\rm Spec}(\psi)|=d_n^2$ counted with multiplicity
- normalization: $d$ appears without a subscript in the displayed cSPF definition; read as $d_n=2^n$

Records: `claim:opus5-2608.14798v1/c08`, `map:opus5-2608.14798v1/c08`, `math:opus5-2608.14798v1/m08`.

## c09 — SPF is Clifford invariant and uniquely valued on stabilizer states

*Sec. III C 1 · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Proposition (Invariance): $\mathcal{Z}_\beta(\mathcal{C}(\psi))=\mathcal{Z}_\beta(\psi)$ for all $\mathcal{C}\in\mathcal{C}l_n$. Proposition (Uniqueness): for any $\ket{\phi}\in{\rm Stab}_n$, $\mathcal{Z}_\beta(\phi)=\mathcal{Z}_\beta({\rm STAB}_n)=e^{-\beta}[(d_n^2-d_n)+d_n\cosh\beta]$. The paper reads uniqueness as faithfulness of the SPF under free operations.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the non-invariant Pauli spectrum itself

**Stated conditions.**

- (SOURCE_EXPLICIT) $\mathcal{C}\in\mathcal{C}l_n$
- (SOURCE_EXPLICIT) the uniqueness statement is for pure stabilizer states

**Components and their accounting.**

- `comp:inv` [CONCLUSION / MAPPED] $\mathcal{Z}_\beta$ is invariant under Clifford unitaries.
  - residual: The proof asserts Cliffords act transitively on Paulis; transitivity on non-identity Paulis is what the argument needs, and the identity is not in the orbit.
- `comp:uniq` [CONCLUSION / MAPPED] $\mathcal{Z}_\beta(\phi)=e^{-\beta}[(d_n^2-d_n)+d_n\cosh\beta]$ for every pure stabilizer state.
- `comp:faithful` [MODEL / RESIDUAL] Uniqueness is read as the SPF being 'faithful under free operations (Clifford unitaries)'.
  - residual: 'Faithful' is used here for constancy on the free set; faithfulness as a resource-theoretic property (zero iff free) is only established later for the stabilizer work, not for the SPF.
- `comp:cspf-ext` [CONCLUSION / RESIDUAL] Both properties extend to the core SPF, with $\mathcal{Z}^c_\beta({\rm STAB}_n)=e^{-\beta}d_n(\cosh\beta-1)$.

**Math target `m09`** (EXACT), covering `comp:inv`, `comp:uniq`.

- conclusion: $\forall\mathcal{C}\in\mathcal{C}l_n:\ \mathcal{Z}_\beta(\mathcal{C}(\psi))=\mathcal{Z}_\beta(\psi)$; and $\forall\phi\in{\rm Stab}_n:\ \mathcal{Z}_\beta(\phi)=e^{-\beta}[(d_n^2-d_n)+d_n\cosh\beta]$, $d_n=2^n$.
- quantifier: FORALL \beta in $\mathbb{R}$
- quantifier: FORALL n in positive integers
- quantifier: FORALL \mathcal{C} in $\mathcal{C}l_n$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_EXPLICIT): $\cosh$ is even, absorbing Clifford-induced sign flips
- assumption (SOURCE_EXPLICIT): Clifford conjugation permutes the Pauli spectrum, so the sorted spectra agree
- assumption (SOURCE_EXPLICIT): Proposition (Stabilizer Pauli Spectrum) supplies the stabilizer spectrum $d_n$ entries $\pm1$ and $d_n^2-d_n$ zeros
- normalization: $\mathcal{Z}_\beta({\rm STAB}_n)$ denotes the common value on all pure $n$-qubit stabilizer states

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity] The invariance proof says Cliffords 'act transitively on Paulis', which is false for the identity Pauli; the intended statement is transitivity on non-identity Paulis.
  - what could settle it: Errata or author confirmation; the conclusion is unaffected.

Records: `claim:opus5-2608.14798v1/c09`, `map:opus5-2608.14798v1/c09`, `math:opus5-2608.14798v1/m09`.

## c10 — Clifford-orbit and stabilizer-Renyi representations

*Sec. III C 2 · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Two equivalent representations are given. The Clifford-orbit representation rewrites the SPF as $e^{-\beta}[\cosh\beta+\frac{d_n^2-1}{|\mathcal{C}l_n|}\sum_{C}\cosh(\beta\tr[\psi P_C])]$ and, after expanding $\cosh$, in terms of Clifford $2k$-fold twirling channels acting on $2k$ copies. The stabilizer-Renyi representation is $\mathcal{Z}_\beta(\psi)=e^{-\beta}[d_n^2+\frac{d_n}{2}\beta^2+\sum_{k\geq2}\frac{\beta^{2k}}{(2k)!}2^{n-(k-1)M_k(\psi)}]$, exhibiting the SPF as a generating function for the moment hierarchy probed by the integer SREs.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the direct Pauli-spectrum sum in Definition (SPF)

**Stated conditions.**

- (SOURCE_EXPLICIT) $P\neq\mathbb{I}$ is an arbitrary non-identity Pauli, e.g. $Z^{\otimes n}$
- (SOURCE_EXPLICIT) the Renyi representation uses integer-index stabilizer entropies $M_k$

**Components and their accounting.**

- `comp:orbit` [CONCLUSION / RESIDUAL] Clifford-orbit representation via the orbit-stabilizer theorem.
- `comp:twirl` [CONCLUSION / RESIDUAL] Expansion in Clifford $2k$-fold channels $\Phi^{2k}_{\mathcal{C}l_n}$ on $2k$ copies.
  - residual: The displayed Clifford-channel expansion is written with $\frac{\beta^{2k}}{2k!}$ in one equation and $\frac{\beta^{2k}}{(2k)!}$ in the next; the intended coefficient is $1/(2k)!$.
- `comp:design` [EVIDENCE / RESIDUAL] Because Cliffords form a 2-design, the first genuinely state-dependent contribution appears beyond the second-moment sector.
  - residual: 'Beyond the universal second-moment sector' is stated without the explicit design-order bookkeeping.
- `comp:renyi` [CONCLUSION / MAPPED] $\mathcal{Z}_\beta(\psi)=e^{-\beta}[d_n^2+\frac{d_n}{2}\beta^2+\sum_{k\geq2}\frac{\beta^{2k}}{(2k)!}2^{n-(k-1)M_k(\psi)}]$.
- `comp:sampling` [MODEL / RESIDUAL] The orbit representation is presented as the natural starting point for sampling-based access to the SPF.
  - residual: Interpretive bridge to Sec. III C 4; no complexity statement is made here.

**Math target `m10`** (EXACT), covering `comp:renyi`.

- conclusion: $\mathcal{Z}_{\beta}(\psi)=e^{-\beta}\left[d_{n}^{2}+\frac{d_{n}}{2}\beta^{2}+\sum_{k\geq 2}\frac{\beta^{2k}}{(2k)!}2^{\,n-(k-1)M_{k}(\psi)}\right]$.
- quantifier: FORALL \beta in $\mathbb{R}$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- quantifier: FORALL k in integers $\geq2$ in the summation index
- assumption (SOURCE_RECONSTRUCTED): $\sum_{x\in{\rm Spec}(\psi)}x^{2k}=2^{\,n-(k-1)M_k(\psi)}$ for integer $k\geq2$, i.e. the definition of $M_k$ rearranged
- assumption (SOURCE_RECONSTRUCTED): $\sum_{x\in{\rm Spec}(\psi)}x^{2}=d_n$ for pure states, giving the $\beta^2$ term
- normalization: the $k=0$ term is the Pauli count $d_n^2$ and the $k=1$ term is purity-fixed; neither carries magic

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity] Coefficient printed as $\beta^{2k}/2k!$ in the Clifford-representation equation, inconsistent with $\beta^{2k}/(2k)!$ used elsewhere.
  - what could settle it: Errata; the surrounding equations fix the intended value.

Records: `claim:opus5-2608.14798v1/c10`, `map:opus5-2608.14798v1/c10`, `math:opus5-2608.14798v1/m10`.

## c11 — Lipschitz robustness of the SPF

*Sec. III C 3 · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Theorem (Lipschitz property): for two $n$-qubit pure states, $|\mathcal{Z}_\beta(\psi)-\mathcal{Z}_\beta(\phi)|\leq L_n(\beta)\|\psi-\phi\|_1$ with $L_n(\beta)=e^{-\beta}d_n\beta\sinh\beta$. The paper reads this as guaranteeing that the SPF, and hence the magic monotone built from it, is robust under small perturbations.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** discontinuous or unstable magic measures

**Stated conditions.**

- (SOURCE_EXPLICIT) $\ket{\phi},\ket{\psi}$ are $n$-qubit pure states
- (SOURCE_EXPLICIT) the proof is deferred to the supplemental material and is based on the Clifford-orbit representation

**Components and their accounting.**

- `comp:bound` [CONCLUSION / MAPPED] $|\mathcal{Z}_\beta(\psi)-\mathcal{Z}_\beta(\phi)|\leq e^{-\beta}d_n\beta\sinh\beta\,\|\psi-\phi\|_1$.
- `comp:symmetry` [EVIDENCE / RESIDUAL] $\beta\sinh\beta$ carries the $\mathbb{Z}_2$ symmetry $\beta\to-\beta$ while the prefactor reflects the energy shift in the definition.
  - residual: The remark asserts a $\mathbb{Z}_2$ symmetry of $\beta\sinh\beta$ while the stated constant $L_n(\beta)=e^{-\beta}d_n\beta\sinh\beta$ is not $\beta\to-\beta$ symmetric; the admissible $\beta$ range of the theorem is not given.
- `comp:robust` [MODEL / RESIDUAL] Robustness is presented as a physical requirement, not merely a convenient bound.
  - residual: Physical reading; no operational error model is attached.

**Math target `m11`** (EXACT), covering `comp:bound`.

- conclusion: $|\mathcal{Z}_{\beta}(\psi)-\mathcal{Z}_{\beta}(\phi)|\leq L_{n}(\beta)\,\|\psi-\phi\|_{1}$ with $L_{n}(\beta)=e^{-\beta}d_{n}\beta\sinh\beta$.
- quantifier: FORALL \beta in the range of $\beta$ is not stated in the theorem; the prefactor $e^{-\beta}$ is not symmetric under $\beta\to-\beta$
- quantifier: FORALL \psi,\phi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_RECONSTRUCTED): $\|\cdot\|_1$ is the trace norm on the difference of the two rank-one projectors
- normalization: $L_n(\beta)$ grows like $d_n=2^n$, so the bound is extensive in Hilbert-space dimension

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity, mathematical_correctness] Theorem (Lipschitz property) does not state the admissible range of $\beta$, while the accompanying remark appeals to a $\beta\to-\beta$ symmetry that the stated constant does not have.
  - what could settle it: Author clarification, or restriction of the theorem to $\beta\geq0$ as used throughout the applications.

Records: `claim:opus5-2608.14798v1/c11`, `map:opus5-2608.14798v1/c11`, `math:opus5-2608.14798v1/m11`.

## c12 — SPF state-independent bounds

*Sec. III C 5 · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Theorem (SPF state-independent bounds): for $\beta\in\mathbb{R}$ and any $n$-qubit pure state, $e^{-\beta}[(d_n^2-d_n)+d_n\cosh\beta]\geq\mathcal{Z}_\beta(\psi)\geq e^{-\beta}[\cosh\beta+(d_n^2-1)\cosh(\beta/\sqrt{d+1})]$, the upper bound being the stabilizer value and the lower bound obtained from a spectrum uniform over all non-trivial Paulis.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the stabilizer value $\mathcal{Z}_\beta({\rm STAB}_n)$

**Stated conditions.**

- (SOURCE_EXPLICIT) $\beta\in\mathbb{R}$
- (SOURCE_EXPLICIT) $\ket{\psi}$ pure

**Components and their accounting.**

- `comp:upper` [CONCLUSION / MAPPED] Upper bound is the stabilizer SPF, so stabilizer states maximize the SPF.
- `comp:lower` [CONCLUSION / MAPPED] Lower bound $e^{-\beta}[\cosh\beta+(d_n^2-1)\cosh(\beta/\sqrt{d+1})]$.
  - residual: Subscript on $d$ omitted in the displayed lower bound.
- `comp:extremal` [MODEL / RESIDUAL] The lower bound is attained by a hypothetical spectrum uniform over all non-identity Paulis.
  - residual: The extremal configuration is not shown to be realized by an actual quantum state; the bound is a bound over admissible moment sequences, which the source does not state explicitly.

**Math target `m12`** (EXACT), covering `comp:upper`, `comp:lower`.

- conclusion: $e^{-\beta}[(d_{n}^{2}-d_{n})+d_{n}\cosh\beta]\ \geq\ \mathcal{Z}_{\beta}(\psi)\ \geq\ e^{-\beta}[\cosh\beta+(d_{n}^{2}-1)\cosh(\beta/\sqrt{d_{n}+1})]$.
- quantifier: FORALL \beta in $\mathbb{R}$ as stated; the argument uses the even-moment expansion, which is symmetric in $\beta$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_RECONSTRUCTED): $\sum_{P\in\mathcal{P}_n}\tr[\psi P]^{2}=d_n$ for pure states
- assumption (SOURCE_RECONSTRUCTED): the extremal lower configuration assigns every non-identity Pauli the value $\pm1/\sqrt{d_n+1}$
- normalization: the source writes $\sqrt{d+1}$ without a subscript; read as $d_n=2^n$

**Open items recorded against this claim.**

- [MODEL_ASSUMPTION · mathematical_correctness] The lower bound is derived from an extremal Pauli-spectrum profile whose realizability by a pure state is not established in the source.
  - what could settle it: Either an explicit state achieving the profile, or a restatement of the result as a bound over moment sequences rather than over states.

Records: `claim:opus5-2608.14798v1/c12`, `map:opus5-2608.14798v1/c12`, `math:opus5-2608.14798v1/m12`.

## c13 — SPF state-dependent bounds in terms of M2

*Sec. III C 5 · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Theorem (SPF state-dependent bounds): $e^{-\beta}[(d_n^2-d_n)+d_n\cosh\beta]\geq\mathcal{Z}_\beta(\psi)\geq e^{-\beta}[d_n(d_n-2^{M_2(\psi)})+d_n2^{M_2(\psi)}\cosh(\beta2^{-M_2(\psi)/2})]$, with the lower bound attained by a spectrum of $d_n^2-d_n2^{M_2}$ zeros and $d_n2^{M_2}$ entries $\pm2^{-M_2/2}$.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the state-independent bounds of the preceding theorem

**Stated conditions.**

- (SOURCE_EXPLICIT) $\beta\in\mathbb{R}$
- (SOURCE_EXPLICIT) the proof uses $M_2(\psi)\geq M_{k>2}(\psi)\geq M_\infty(\psi)=0$

**Components and their accounting.**

- `comp:bound` [CONCLUSION / MAPPED] State-dependent lower bound in terms of $M_2(\psi)$.
- `comp:extremal` [MODEL / RESIDUAL] Identification of the two extremal spectra realizing the two bounds.
  - residual: Realizability of the extremal spectra by actual pure states is asserted, not shown.
- `comp:variational` [EVIDENCE / RESIDUAL] A variational refinement of the lower bound is deferred to the supplemental material.
  - residual: The refinement is not reproduced in the main text; its statement and its relation to the displayed bound are not given here.

**Math target `m13`** (EXACT), covering `comp:bound`.

- conclusion: $\mathcal{Z}_{\beta}(\psi)\ \geq\ e^{-\beta}\left[d_{n}(d_{n}-2^{M_{2}(\psi)})+d_{n}2^{M_{2}(\psi)}\cosh(\beta\,2^{-M_{2}(\psi)/2})\right]$.
- quantifier: FORALL \beta in $\mathbb{R}$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$ with order-2 stabilizer Renyi entropy $M_2(\psi)$
- assumption (SOURCE_EXPLICIT): $M_{2}(\psi)\geq M_{k}(\psi)$ for $k>2$ and $M_\infty(\psi)=0$
- assumption (SOURCE_EXPLICIT): the stabilizer-Renyi representation of the SPF
- normalization: $\log$ base 2 throughout, so $2^{M_2}$ is the inverse stabilizer purity

**Open items recorded against this claim.**

- [UNPROVED_LEMMA · mathematical_correctness] The claim $M_\infty(\psi)=0$ used in the proof is stated without qualification; for a general pure state $M_\infty$ need not vanish.
  - what could settle it: Author clarification of the convention for $M_\infty$, or a corrected chain of inequalities.

Records: `claim:opus5-2608.14798v1/c13`, `map:opus5-2608.14798v1/c13`, `math:opus5-2608.14798v1/m13`.

## c14 — SPF is estimable by Bell sampling

*Sec. III C 4, Supplemental Material · modality CONDITIONAL · coverage PARTIAL*

**What the authors said.** Theorem (SPF complexity, informal): for fixed $k$ and $\beta$, the truncated SPF $\mathcal{Z}^{(k)}_\beta(\psi)$ can be estimated to additive error $\epsilon$ and failure probability $\delta$ using the Bell-sampling primitive that estimates Pauli-spectrum moments; approximating the normalized full SPF further requires choosing $k$ so the truncation remainder is below the target accuracy. The supplement gives $\mathcal{N}=\mathcal{O}(\cosh^2\beta\,e^{-2\beta}\epsilon^{-2}\log(1/\delta))$ samples for the normalized truncation, and $\mathcal{N}=\mathcal{O}(\cosh^2\beta\,e^{-2\beta}(\epsilon-\Delta(\beta,k))^{-2}\log(1/\delta))$ for the full normalized SPF, valid only for $\epsilon>\Delta(\beta,k)$.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** direct estimation of a single stabilizer Renyi entropy by Bell sampling, and the $\mathcal{O}(k^2n)$ runtime of running the moment estimator once per moment

**Stated conditions.**

- (SOURCE_EXPLICIT) the guarantee is an additive-error guarantee on the NORMALIZED quantity $d_n^{-1}\mathcal{Z}_\beta(\psi)$, not on $\mathcal{Z}_\beta(\psi)$ itself
- (SOURCE_EXPLICIT) the full-SPF statement requires $\epsilon>\Delta(\beta,k)$ with $\Delta(\beta,k)=d_ne^{-\beta}(\cosh\beta-\sum_{l=0}^{k}\beta^{2l}/(2l)!)$
- (SOURCE_RECONSTRUCTED) each outer sample consumes two copies for Bell sampling plus $2k$ further copies of $\ket{\psi}$ for the inner moment loop
- (SOURCE_EXPLICIT) $k$ and $\beta$ are held fixed in the informal statement

**Components and their accounting.**

- `comp:informal` [CONCLUSION / RESIDUAL] Truncated SPF is estimable with the Bell-sampling primitive at additive error $\epsilon$, failure probability $\delta$.
  - residual: The main-text theorem is labelled 'informal' and carries no explicit sample count; it is not a formal statement.
- `comp:onepass` [CONCLUSION / RESIDUAL] A single run with extra classical memory yields all even moments up to order $2k$, reducing classical runtime from $\mathcal{O}(k^2n)$ to $\mathcal{O}(kn)$.
  - residual: The runtime claim $\mathcal{O}(kn)$ versus $\mathcal{O}(k^2n)$ is classical post-processing only; the quantum copy cost per outer sample ($2k+2$ copies) is not counted in the stated complexity.
- `comp:beta-free` [CONCLUSION / RESIDUAL] The sampling primitive is independent of $\beta$; $\beta$ enters only in classical post-processing, while accuracy and sample complexity depend on $\beta,\epsilon,\delta$ and the truncation error.
  - residual: 'Independent of $\beta$' applies to the sampling primitive; the required truncation order $k$ does depend on $\beta$ through $\Delta(\beta,k)$.
- `comp:samples` [CONCLUSION / MAPPED] $\mathcal{N}=\mathcal{O}(\cosh^2\beta\,e^{-2\beta}\epsilon^{-2}\log(1/\delta))$ for the normalized truncation (Hoeffding on $|X_\alpha|\leq\cosh\beta$).
- `comp:full` [APPROXIMATION / MAPPED] Full normalized SPF at additive $\epsilon$ requires $\epsilon>\Delta(\beta,k)$ and costs $\mathcal{O}(\cosh^2\beta\,e^{-2\beta}(\epsilon-\Delta(\beta,k))^{-2}\log(1/\delta))$.
- `comp:abstract` [LIMITATION / RESIDUAL] The abstract and discussion state without qualification that the SPF and stabilizer work are 'efficiently estimable via Bell sampling'.
  - residual: The abstract's unqualified 'efficiently estimable' does not carry the normalization ($d_n^{-1}\mathcal{Z}$), the truncation floor $\Delta(\beta,k)$, or the required scaling of $k$ with $n$. No statement in the paper transfers the estimator guarantee to $\mathcal{W}_\beta$, which is a logarithm of a difference of the estimated quantity.

**Math target `m14`** (APPROXIMATE), covering `comp:samples`, `comp:full`.

- conclusion: ${\rm Pr}\left(\left|\hat{\mathcal{Z}}^{(k)}_{\beta}(\psi)-\mathcal{Z}^{(k)}_{\beta}(\psi)\right|/d_{n}\geq\epsilon\right)\leq2\exp\left(-\mathcal{N}\epsilon^{2}e^{2\beta}/(2\cosh^{2}\beta)\right)$, and for $\epsilon>\Delta(\beta,k)$ the same bound with $\epsilon\mapsto\epsilon-\Delta(\beta,k)$ controls $(\mathcal{Z}_{\beta}(\psi)-\hat{\mathcal{Z}}^{(k)}_{\beta}(\psi))/d_{n}$.
- quantifier: FORALL \epsilon in reals with $\epsilon>\Delta(\beta,k)$ for the full-SPF statement, $\epsilon>0$ for the truncation statement
- quantifier: FORALL \delta in $(0,1)$
- quantifier: FORALL k in positive integers, held fixed
- quantifier: FORALL \beta in $\mathbb{R}$, held fixed
- assumption (SOURCE_EXPLICIT): each entry of the accumulated sign vector $\mathbf{B}_k$ is $\pm1$, giving $|X_\alpha|\leq\cosh\beta$ for Hoeffding
- assumption (SOURCE_EXPLICIT): Bell sampling draws $P$ with probability $|\langle P|\eta\rangle|^2$ and repeated eigenbasis measurements of that $P$ give unbiased even moments
- assumption (SOURCE_EXPLICIT): the error is additive on $d_n^{-1}\mathcal{Z}$, and $\Delta(\beta,k)$ itself carries a factor $d_n=2^n$
- normalization: all guarantees are for $d_n^{-1}\mathcal{Z}$; since $\mathcal{Z}_\beta\sim d_n^2$, a constant additive error on $d_n^{-1}\mathcal{Z}$ is a relative error of order $2^{-n}$ on $\mathcal{Z}$ but does NOT bound $\mathcal{W}_\beta$ without further argument
- approximation error: truncation floor $\Delta(\beta,k)=d_ne^{-\beta}(\cosh\beta-\sum_{l=0}^{k}\beta^{2l}/(2l)!)$, which scales with $d_n=2^n$; the stated guarantee is vacuous unless $k$ is chosen large enough that $\Delta(\beta,k)<\epsilon$, and the source does not give the resulting $k(n,\beta,\epsilon)$

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · mathematical_correctness, empirical_support] The efficiency claim is proved for an additive error on the normalized truncated SPF, whereas the abstract and discussion state it for the SPF and for the stabilizer work without qualification.
  - what could settle it: An explicit statement of $k(n,\beta,\epsilon)$ making $\Delta(\beta,k)<\epsilon$, and an error-propagation argument from $\hat{\mathcal{Z}}$ to $\mathcal{W}_\beta=-\log(\hat{\mathcal{Z}}-d_n^2e^{-\beta})+\ldots$.
- [SCOPE_AMBIGUITY · source_fidelity] Index convention of the moment vector $\mathbf{m}_k$ versus the accumulator $\mathbf{B}_k$ in Algorithm 4: the first stored entry appears to estimate $d_n^{-1}\sum x^4$ while $\mathbf{m}_k$ is defined to start at $d_n^{-1}\sum x^2$.
  - what could settle it: Author clarification of the off-by-one; the state-independent $k=1$ moment is purity-fixed so the discrepancy may be immaterial.
- [RESOURCE_LIMIT · computational_reproducibility] No code, seed, or measured sample count is supplied for any estimator claim; nothing was executed in this round.
  - what could settle it: Author-supplied implementation, or an independent reproduction with declared parameters.

Records: `claim:opus5-2608.14798v1/c14`, `map:opus5-2608.14798v1/c14`, `math:opus5-2608.14798v1/m14`.

## c15 — SPF of tensor powers of single-qubit states

*Sec. IV A · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Proposition: $\mathcal{Z}_\beta(\ket{T}^{\otimes n})=e^{-\beta}[(4^n-3^n)+\sum_{k=0}^{n}\binom{n}{k}2^k\cosh(\beta2^{-k/2})]$. Theorem ($n$-copy SPF) generalizes this to $n$ copies of an arbitrary single-qubit pure state via $V_\psi[\vec n]=\prod_{\sigma}\braket{\sigma}^{n_\sigma}$. At $\beta=0$ the SPF is insensitive to magic ($\mathcal{Z}_0=4^n$), while for every $\beta\neq0$ it separates $\ket{T}^{\otimes n}$ from stabilizer states.

**System.** product states $\bigotimes_{l=1}^{n}\ket{\psi_l}$ of single-qubit pure states; magic without entanglement across any cut

**Comparison baseline.** $\mathcal{Z}_\beta({\rm STAB}_n)$

**Stated conditions.**

- (SOURCE_EXPLICIT) the state is a tensor power of a single-qubit pure state
- (SOURCE_EXPLICIT) $\braket{T|X|T}=\braket{T|Y|T}=1/\sqrt2$ and $\braket{T|Z|T}=0$

**Components and their accounting.**

- `comp:t` [CONCLUSION / MAPPED] Closed form for $\mathcal{Z}_\beta(\ket{T}^{\otimes n})$.
- `comp:general` [CONCLUSION / RESIDUAL] Closed form for $\mathcal{Z}_\beta(\ket{\psi}^{\otimes n})$, arbitrary single-qubit $\ket{\psi}$.
  - residual: The multi-index sum $\sum_{n_x,n_y,n_z}$ in the $n$-copy theorem is written without its constraint; the intended constraint $n_x+n_y+n_z=w$ is left implicit.
- `comp:sep` [CONCLUSION / RESIDUAL] $\mathcal{Z}_\beta(\ket{T}^{\otimes n})<\mathcal{Z}_\beta({\rm STAB}_n)$ for every $\beta\neq0$; equality only at $\beta=0$.

**Math target `m15`** (EXACT), covering `comp:t`.

- conclusion: $\mathcal{Z}_{\beta}(\ket{T}^{\otimes n})=e^{-\beta}\left[(4^{n}-3^{n})+\sum_{k=0}^{n}\binom{n}{k}2^{k}\cosh(\beta\,2^{-k/2})\right]$.
- quantifier: FORALL n in positive integers
- quantifier: FORALL \beta in $\mathbb{R}$
- assumption (SOURCE_EXPLICIT): the Pauli spectrum factorizes over tensor factors
- assumption (SOURCE_EXPLICIT): $4^n-3^n$ Pauli strings contain at least one $Z$ and contribute zero
- assumption (SOURCE_EXPLICIT): there are $\binom{n}{k}2^k$ weight-$k$ strings built from $\{X,Y\}$, each contributing $2^{-k/2}$
- normalization: $\ket{T}=T\ket{+}$; $\mathcal{Z}_0=4^n$ fixes the normalization

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity] Theorem ($n$-copy SPF) omits the summation constraint $n_x+n_y+n_z=w$ on the multinomial index.
  - what could settle it: Errata; the $\ket{T}^{\otimes n}$ special case fixes the intended reading.

Records: `claim:opus5-2608.14798v1/c15`, `map:opus5-2608.14798v1/c15`, `math:opus5-2608.14798v1/m15`.

## c16 — SPF of separable bipartite states and its stabilizer special case

*Sec. IV B · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The Pauli spectrum factorizes under tensor products but the SPF is not multiplicative. Theorem (SPF for separable states) gives $\mathcal{Z}_\beta(\psi_{AB})=2^{|B|-\nu_B}\mathcal{Z}_\beta(\psi_A)+2^{|A|-\nu_A}\mathcal{Z}_\beta(\psi_B)-e^{-\beta}2^{n-\nu_A-\nu_B}\cosh\beta+\mathcal{Z}^{(R)}_\beta(\psi_{AB})$ with a residual term built from the Cartesian product of the residual Pauli spectra. Lemma (SPF for Stabilizer + Pure) gives the simpler $\mathcal{Z}_\beta(\psi_A\otimes{\rm Stab}_B)=d_B\mathcal{Z}_\beta(\psi_A)+e^{-\beta}(d_B^2-d_B)d_A^2$, and for the core SPF $\mathcal{Z}^c_\beta(\psi_A\otimes{\rm Stab}_B)=d_B\mathcal{Z}^c_\beta(\psi_A)$.

**System.** bipartite separable pure states $\ket{\psi_A}\otimes\ket{\psi_B}$ across an $A|B$ cut

**Comparison baseline.** multiplicativity $\mathcal{Z}_\beta(\psi_A\otimes\phi_B)=\mathcal{Z}_\beta(\psi_A)\mathcal{Z}_\beta(\phi_B)$, which is explicitly denied

**Stated conditions.**

- (SOURCE_EXPLICIT) $\ket{\psi_{AB}}=\ket{\psi_A}\otimes\ket{\psi_B}$
- (SOURCE_EXPLICIT) $\nu_{A(B)}$ is the stabilizer nullity of the corresponding subsystem state

**Components and their accounting.**

- `comp:nonmult` [CONCLUSION / RESIDUAL] $\mathcal{Z}_\beta(\psi_A\otimes\phi_B)\neq\mathcal{Z}_\beta(\psi_A)\mathcal{Z}_\beta(\phi_B)$; the failure is structured.
  - residual: No quantitative statement of how far multiplicativity fails is given here; the quantitative version appears later as cSPF supermultiplicativity.
- `comp:decomp` [CONCLUSION / RESIDUAL] Four-term decomposition with residual $\mathcal{Z}^{(R)}_\beta$.
  - residual: The exponents $2^{|B|-\nu_B}$ and $2^{|A|-\nu_A}$ require $|A|,|B|$ to be QUBIT COUNTS, which contradicts the Sec. II convention $d_A=|A|=2^{n}$; under the Sec. II reading the theorem is dimensionally wrong. Under the qubit-count reading the supplemental proof identifies $2^{|A|-\nu_A}=|{\rm Spec}_S(\psi_A)|$ and the decomposition does reduce to Lemma (SPF for Stabilizer + Pure).
- `comp:residual` [DEFINITION / RESIDUAL] $\mathcal{Z}^{(R)}_\beta(\psi_{AB})=e^{-\beta}\sum_{x\in{\rm Spec}_R(\psi_A)\times{\rm Spec}_R(\psi_B)}\cosh(\beta x)$ from the Cartesian product of residual spectra, with ${\rm Spec}_R$ fixed by the supplemental Canonical Splitting proposition as the complement of the $\pm1$ entries, i.e. every Pauli with $|\tr(P\psi)|<1$ including the zeros.
  - residual: ${\rm Spec}_R$ is used in the main-text theorem but defined only in the supplemental material, so the theorem has no evaluable right-hand side at the point where it is stated.
- `comp:stabpure` [CONCLUSION / MAPPED] Stabilizer+pure special case, plus the clean core-SPF form $d_B\mathcal{Z}^c_\beta(\psi_A)$.

**Math target `m16`** (EXACT), covering `comp:stabpure`.

- conclusion: $\mathcal{Z}_{\beta}(\psi_{A}\otimes{\rm Stab}_{B})=d_{B}\mathcal{Z}_{\beta}(\psi_{A})+e^{-\beta}(d_{B}^{2}-d_{B})d_{A}^{2}$, and $\mathcal{Z}^{c}_{\beta}(\psi_{A}\otimes{\rm Stab}_{B})=d_{B}\mathcal{Z}^{c}_{\beta}(\psi_{A})$.
- quantifier: FORALL \beta in $\mathbb{R}$
- quantifier: FORALL \psi_A in pure states of subsystem $A$
- quantifier: FORALL {\rm Stab}_B in pure stabilizer states of subsystem $B$
- assumption (SOURCE_EXPLICIT): the Pauli spectrum of a stabilizer state on $B$ is $d_B$ ones and $d_B^2-d_B$ zeros
- assumption (SOURCE_EXPLICIT): multiplicativity of the Pauli spectrum under tensor products
- normalization: $d_A,d_B$ are Hilbert-space dimensions $2^{n_A},2^{n_B}$

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity, mathematical_correctness] The symbol $|A|$ is fixed in Sec. II as $d_A=2^n$ but is used as a qubit count in Theorem (SPF for separable states); the two readings give different statements and only the qubit-count one is consistent with the supplemental proof.
  - what could settle it: Errata fixing the notation. With $|A|$ read as the qubit count, this run checked the theorem against Lemma (SPF for Stabilizer + Pure) by hand and the two agree; that hand check is not a proof of the theorem.
- [SCOPE_AMBIGUITY · source_fidelity] ${\rm Spec}_R$ appears in the main-text theorem but is defined only in the supplemental Canonical Splitting proposition, so the main-text statement is not self-contained.
  - what could settle it: A forward reference, or restating the definition where the theorem appears.

Records: `claim:opus5-2608.14798v1/c16`, `map:opus5-2608.14798v1/c16`, `math:opus5-2608.14798v1/m16`.

## c17 — cSPF supermultiplicativity

*Sec. IV B · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Lemma (cSPF supermultiplicativity): for any bipartite separable pure state, $\mathcal{Z}^c_\beta(\psi_A\otimes\phi_B)\geq\frac{\mathcal{Z}^c_\beta(\psi_A)\mathcal{Z}^c_\beta(\phi_B)}{e^{-\beta}(\cosh\beta-1)}$. The proof reduces to a reweighting inequality proved as a Chebyshev-type monotone reweighting lemma in the supplement.

**System.** bipartite separable pure states

**Comparison baseline.** exact multiplicativity

**Stated conditions.**

- (SOURCE_EXPLICIT) $\ket{\psi_{AB}}=\ket{\psi_A}\otimes\ket{\phi_B}$
- (SOURCE_EXPLICIT) the proof asserts $p_k/p^\star_k\geq p_{k+1}/p^\star_{k+1}$ for the constructed distributions
- (SOURCE_RECONSTRUCTED) the admissible range of $\beta$ is not stated; the denominator $\cosh\beta-1$ vanishes at $\beta=0$

**Components and their accounting.**

- `comp:ineq` [CONCLUSION / MAPPED] Supermultiplicativity of the core SPF with the stated stabilizer-value denominator.
  - residual: No range of $\beta$ is stated, and the inequality is singular at $\beta=0$.
- `comp:lemma` [EVIDENCE / RESIDUAL] Monotone reweighting (Chebyshev-type) lemma supplies the key step.
- `comp:pstar` [ASSUMPTION / RESIDUAL] $p^\star_k=w_k/\sum_k w_k$ is said to be derivable from a stabilizer state in system $A$.
  - residual: The monotonicity hypothesis $p_k/p^\star_k$ non-increasing is asserted without justification. It is in fact immediate, since $p_k/p^\star_k\propto a_k=\sum_i\tr[\psi_AP_i]^{2k}$ and $|\tr[\psi_AP_i]|\leq1$ makes $a_k$ non-increasing in $k$; this run supplies that one-line reason, which the source does not. The supplemental material proves the analogous reweighting step for the UNFILTERED work with the comparison vector $a^{\prime}=(d_A^2,d_A,d_A,\dots)$, again asserting the monotonicity of $a_k/a^{\prime}_k$.

**Math target `m17`** (EXACT), covering `comp:ineq`.

- conclusion: $\mathcal{Z}_{\beta}^{c}(\psi_A\otimes\phi_B)\ \geq\ \dfrac{\mathcal{Z}_{\beta}^{c}(\psi_A)\,\mathcal{Z}_{\beta}^{c}(\phi_B)}{e^{-\beta}(\cosh\beta-1)}$, i.e. division by $\mathcal{Z}^c_\beta$ of a single-qubit-normalized stabilizer reference.
- quantifier: FORALL \psi_A,\phi_B in pure states of the two subsystems
- quantifier: FORALL \beta in $\beta\neq0$; at $\beta=0$ both sides degenerate and the quotient is $0/0$
- assumption (SOURCE_EXPLICIT): $w_k=\beta^{2k}/(2k)!$, $a_k=\sum_i\tr[\psi_AP_i^A]^{2k}$, $b_k=\sum_j\tr[\phi_BP_j^B]^{2k}$
- assumption (SOURCE_EXPLICIT): $p_k=w_ka_k/\sum_k w_ka_k$ is a probability distribution and $p_k/p^\star_k$ is non-increasing in $k$
- assumption (SOURCE_EXPLICIT): $\sum_{k\geq1}w_k=\cosh\beta-1$
- normalization: the denominator equals $\mathcal{Z}^c_\beta$ of a one-qubit stabilizer state ($d=1$ in $e^{-\beta}d(\cosh\beta-1)$); the source does not label it as such

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · mathematical_correctness] The reweighting hypothesis $p_k/p^\star_k$ non-increasing is asserted with no reason given, in both the main-text lemma and the supplemental supporting theorem.
  - what could settle it: One added sentence: $a_k$ is non-increasing because every Pauli expectation has modulus at most one. This run states that reason but did not verify the rest of the argument.
- [SCOPE_AMBIGUITY · mathematical_correctness] The supplemental supporting theorem cites the reweighting lemma as \\ref{Chebyshev_lemma} while the lemma is labelled lem:Chebyshev_lemma; the cross-reference does not resolve.
  - what could settle it: Errata.

Records: `claim:opus5-2608.14798v1/c17`, `map:opus5-2608.14798v1/c17`, `math:opus5-2608.14798v1/m17`.

## c18 — Exact ensemble-averaged SPF for Haar-random states

*Sec. IV C · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Theorem (SPF for Haar-random states): for $\beta\geq0$, $\mathcal{Z}_\beta({\rm Haar}_n)=e^{-\beta}[\cosh\beta+(d_n^2-1)\Gamma(\frac{d_n+1}{2})(2/\beta)^{\frac{d_n-1}{2}}I_{\frac{d_n-1}{2}}(\beta)]$. Lemma: for fixed $\beta$ and large $d_n$, more generally whenever $\beta^2=o(d_n)$, $\mathcal{Z}_\beta({\rm Haar}_n)=e^{-\beta}[\cosh\beta+(d_n^2-1)(1+o(1))]$. The proof is deferred to the supplement and is based on the Haar Pauli-spectrum density of Turkeshi et al.

**System.** $\ket{\psi}=U\ket{0}^{\otimes n}$ with $U$ Haar-distributed on $U(2^n)$; maximal magic and volume-law entanglement

**Comparison baseline.** $\mathcal{Z}_\beta({\rm STAB}_n)$ and the $\nu$-compressible family

**Stated conditions.**

- (SOURCE_EXPLICIT) $\beta\geq0$ is stated in the theorem
- (SOURCE_EXPLICIT) the quantity is the ENSEMBLE AVERAGE $\mathbb{E}_{\psi\sim{\rm Haar}}[\mathcal{Z}_\beta(\psi)]$, not the SPF of any single state
- (SOURCE_EXPLICIT) the asymptotic form requires $\beta^2=o(d_n)$

**Components and their accounting.**

- `comp:exact` [CONCLUSION / MAPPED] Closed form in terms of a modified Bessel function of the first kind.
- `comp:check` [EVIDENCE / RESIDUAL] Consistency check: the $\beta\to0$ limit recovers $\mathcal{Z}_0=d_n^2$ via the small-argument Bessel expansion.
  - residual: The $\beta\to0$ check is stated via a footnote expansion; the exchange of limit and ensemble average is not discussed.
- `comp:asym` [APPROXIMATION / RESIDUAL] Asymptotic flat form $e^{-\beta}[\cosh\beta+(d_n^2-1)(1+o(1))]$ for $\beta^2=o(d_n)$.
  - residual: $o(1)$ is not quantified; no explicit rate in $n$ or $\beta$ is given.
- `comp:picture` [MODEL / RESIDUAL] Reading: Haar spectra narrow to $d_n^2-1$ zeros plus a single one, with $|{\rm Stab}|=|{\rm Supp}|=1$ almost surely.
  - residual: '$|{\rm Stab}({\rm Haar}_n)|=|{\rm Supp}({\rm Haar}_n)|=1$ almost surely' is an almost-sure statement about individual states, used to motivate an ensemble-average formula.

**Math target `m18`** (EXACT), covering `comp:exact`.

- conclusion: $\mathcal{Z}_{\beta}({\rm Haar}_{n})=e^{-\beta}\left[\cosh\beta+(d_{n}^{2}-1)\Gamma\!\left(\tfrac{d_{n}+1}{2}\right)\left(\tfrac{2}{\beta}\right)^{\frac{d_{n}-1}{2}}I_{\frac{d_{n}-1}{2}}(\beta)\right]$.
- quantifier: FORALL n in positive integers, $d_n=2^n$
- quantifier: FORALL \beta in $[0,\infty)$
- assumption (SOURCE_EXPLICIT): $U$ is Haar-distributed on $U(2^n)$ and $\ket{\psi}=U\ket{0}^{\otimes n}$
- assumption (SOURCE_EXPLICIT): the averaged Pauli-spectrum density of Haar states is the imported Proposition attributed to Turkeshi et al. (2025)
- normalization: $I_\nu$ is the modified Bessel function of the first kind; the expression is the ensemble mean of $\mathcal{Z}_\beta$, and by Jensen's inequality it is NOT the exponential of the mean free energy

**Open items recorded against this claim.**

- [MODEL_ASSUMPTION · mathematical_correctness] The theorem is an ensemble average, but it is used throughout as if it characterized individual Haar states; the bridge is the concentration lemma, whose normalization is separately unclear.
  - what could settle it: Explicit statement of which downstream uses need the average and which need per-state concentration.

Records: `claim:opus5-2608.14798v1/c18`, `map:opus5-2608.14798v1/c18`, `math:opus5-2608.14798v1/m18`.

## c19 — Concentration of the SPF for Haar states, and Haar certification

*Sec. IV C · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Lemma (Levy's Lemma for the SPF): ${\rm Prob}(|\mathcal{Z}_\beta(\psi)-\mathcal{Z}_\beta({\rm Haar}_n)|/L_n(\beta)\geq\epsilon)\leq4\exp(-\frac{2}{9\pi^3}2^n\epsilon^2)$, so deviations are doubly exponentially suppressed in the qubit number and almost all Haar states share essentially the same SPF. Algorithm 1 uses a single oracle call to the SPF at small $\beta$ to certify Haar randomness. The paper argues the SPF is a better Haar witness than a fixed-$\alpha$ SRE because high-order designs reproduce individual SRE values.

**System.** Haar-random $n$-qubit pure states

**Comparison baseline.** fixed-$\alpha$ stabilizer Renyi entropies and $k$-designs

**Stated conditions.**

- (SOURCE_EXPLICIT) the lemma is stated for the 'properly normalized' SPF, with the deviation divided by the Lipschitz constant $L_n(\beta)$
- (SOURCE_EXPLICIT) Algorithm 1 requires $\beta=o(\sqrt{d_n})$
- (SOURCE_EXPLICIT) Algorithm 1 assumes oracle access to $\mathcal{Z}_\beta(\psi)$

**Components and their accounting.**

- `comp:levy` [CONCLUSION / MAPPED] Doubly exponential concentration with the explicit constant $\frac{2}{9\pi^3}$.
- `comp:selfavg` [MODEL / RESIDUAL] Reading: the SPF is self-averaging, so almost all Haar states share the same SPF and stabilizer work.
  - residual: 'Almost all Haar states share essentially the same SPF and therefore the same stabilizer work' transfers a concentration statement about $\mathcal{Z}$ to $\mathcal{W}=-\log\mathcal{Z}^c+\ldots$; the paper itself later flags the Jensen gap for ensemble averages.
- `comp:alg` [MODEL / RESIDUAL] Algorithm 1 (HaarCertify): compute $\delta_\beta$, normalize, and decide by whether $\delta_\beta=o(1)$.
  - residual: The decision rule tests an asymptotic predicate ('$\delta_\beta(\psi)=o(1)$') on a single numerical value of a single state; no finite-$n$ threshold, tolerance, or failure probability is specified, so the algorithm is not executable as written.
- `comp:design` [CONCLUSION / RESIDUAL] A fixed $\alpha$-SRE cannot distinguish a $k$-design from Haar once moments agree, typically requiring $k<2\alpha$ for discrimination; the SPF, being a series in all $\alpha$, is sensitive to true Haar randomness.
  - residual: 'typically requiring $k<2\alpha$ for discrimination' is stated without proof or citation.

**Math target `m19`** (EXACT), covering `comp:levy`.

- conclusion: ${\rm Prob}_{\psi\sim{\rm Haar}_n}\left(|\mathcal{Z}_{\beta}(\psi)-\mathcal{Z}_{\beta}({\rm Haar}_{n})|/L_{n}(\beta)\geq\epsilon\right)\leq4\exp\left(-\tfrac{2}{9\pi^{3}}2^{n}\epsilon^{2}\right)$.
- quantifier: FORALL \epsilon in $[0,\infty)$
- quantifier: FORALL n in positive integers
- quantifier: FORALL \beta in range not stated; $L_n(\beta)$ is the Lipschitz constant of Theorem (Lipschitz property)
- assumption (SOURCE_RECONSTRUCTED): Levy concentration for Lipschitz functions on the unit sphere of $\mathbb{C}^{2^n}$
- assumption (SOURCE_EXPLICIT): $L_n(\beta)=e^{-\beta}d_n\beta\sinh\beta$ from Theorem (Lipschitz property)
- normalization: the deviation is measured in units of $L_n(\beta)$, which itself grows like $2^n$; an $\epsilon$-level statement in these units is NOT an $\epsilon$-level statement on $\mathcal{Z}_\beta$ or on $d_n^{-1}\mathcal{Z}_\beta$

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · mathematical_correctness] The concentration lemma normalizes deviations by $L_n(\beta)\sim2^n$, so the 'doubly exponential suppression' is measured against an exponentially large yardstick.
  - what could settle it: Restatement of the deviation in absolute or $d_n^{-1}$-normalized units, which would fix what the concentration actually certifies.
- [SCOPE_AMBIGUITY · semantic_applicability] Algorithms 1-3 branch on asymptotic predicates ($\delta=o(1)$) evaluated on a single instance and assume exact oracle access to $\mathcal{Z}_\beta$.
  - what could settle it: A finite-sample version with explicit thresholds and failure probabilities, built on the estimator of Theorem (Estimator Concentration).

Records: `claim:opus5-2608.14798v1/c19`, `map:opus5-2608.14798v1/c19`, `math:opus5-2608.14798v1/m19`.

## c20 — Exact ensemble SPF for nu-compressible and t-doped states

*Sec. IV D · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Theorem: for $\ket{\psi}$ sampled uniformly from $\mu_{n,\nu}$, $\mathcal{Z}_\beta({\rm Comp}_\nu)=2^{n-\nu}\mathcal{Z}_\beta({\rm Haar}_\nu)+e^{-\beta}4^\nu(4^{n-\nu}-2^{n-\nu})$, with $\mathcal{Z}^c_\beta({\rm Comp}_\nu)=2^{n-\nu}\mathcal{Z}^c_\beta({\rm Haar}_\nu)$; the family concentrates with Lipschitz constant $2^{n-\nu}L_n(\beta)$; asymptotically $\mathcal{Z}_\beta({\rm Comp}_\nu)=e^{-\beta}[4^n-2^{n-\nu}+2^{n-\nu}\cosh\beta]+e^{-\beta}2^{n-\nu}(4^\nu-1)o(1)$ for $\beta^2=o(2^\nu)$, so the SPF depends only on the size of the stabilizer sector up to vanishing corrections. $t$-doped states are $\nu$-compressible with $\nu\leq2lt$, and Algorithms 2-3 certify $\nu$ and extract a lower bound on $t$ given oracle access.

**System.** $\nu$-compressible states, i.e. states of stabilizer nullity $\nu$; and $t$-doped states obtained from a stabilizer state by at most $t$ non-Clifford gates of size $l=O(1)$

**Comparison baseline.** Haar-random states ($\nu\to n$) and stabilizer states ($\nu\to0$)

**Stated conditions.**

- (SOURCE_EXPLICIT) states are sampled from $\mu_{n,\nu}=\mu_{\mathcal{C}l_n}\ast\mu_{{\rm Haar}_\nu}$
- (SOURCE_EXPLICIT) the formula is an ensemble average $\mathbb{E}_{\psi\sim\mu_\nu}[\mathcal{Z}_\beta(\psi)]$
- (SOURCE_EXPLICIT) the asymptotic form requires $\beta^2=o(2^\nu)$
- (SOURCE_EXPLICIT) $t$-doped states use non-Clifford gates of constant size $l$, giving $\nu\leq2lt$

**Components and their accounting.**

- `comp:thm` [CONCLUSION / MAPPED] Exact ensemble SPF for $\nu$-compressible states.
- `comp:limits` [EVIDENCE / RESIDUAL] Consistency in the limits $\nu\to n$ (Haar) and $\nu\to0$ (stabilizer), and the clean cSPF form $2^{n-\nu}\mathcal{Z}^c_\beta({\rm Haar}_\nu)$.
  - residual: The consistency-check sentence cites Theorem (SPF for Haar-random states) where it means the $\nu$-compressible theorem itself; a cross-reference slip.
- `comp:conc` [CONCLUSION / RESIDUAL] Concentration with Lipschitz constant $L_{{\rm Comp}_\nu}(\beta)=2^{n-\nu}L_n(\beta)$.
- `comp:asym` [APPROXIMATION / RESIDUAL] Asymptotic dependence only on the stabilizer-sector size.
  - residual: $o(1)$ unquantified; the correction term is multiplied by $2^{n-\nu}(4^\nu-1)$, which is exponentially large, so the residual is only vanishing relative to that prefactor.
- `comp:tdoped` [CONCLUSION / RESIDUAL] $t$-doped states inherit the result with $\nu\leq2lt$.
- `comp:alg` [MODEL / RESIDUAL] Algorithms 2 and 3 certify $\nu$-compressibility and return $t_{\min}$, at the cost of oracle access; the paper notes oracle access can be replaced by the estimator of Theorem (SPF complexity).
  - residual: Algorithm 3 ($t$-extraction) is declared to ensure a lower bound $t_{\min}\leq t$ but its loop returns on the first successful $\nu$-certification, and its stated requirement is the SPF of a state promised to be $t$-doped 'with known $t$' while the task is to find $t$.

**Math target `m20`** (EXACT), covering `comp:thm`.

- conclusion: $\mathcal{Z}_{\beta}({\rm Comp}_{\nu})=2^{n-\nu}\mathcal{Z}_{\beta}({\rm Haar}_{\nu})+e^{-\beta}4^{\nu}(4^{n-\nu}-2^{n-\nu})$, equivalently $\mathcal{Z}^{c}_{\beta}({\rm Comp}_{\nu})=2^{n-\nu}\mathcal{Z}^{c}_{\beta}({\rm Haar}_{\nu})$.
- quantifier: FORALL n,\nu in integers with $0\leq\nu\leq n$
- quantifier: FORALL \beta in $[0,\infty)$, inherited from the Haar theorem
- assumption (SOURCE_EXPLICIT): Clifford invariance of the SPF brings every $\nu$-compressible state to the product form $U\ket{0}^{\otimes\nu}\otimes\ket{0}^{\otimes(n-\nu)}$
- assumption (SOURCE_EXPLICIT): Lemma (SPF for Stabilizer + Pure) and Theorem (SPF for Haar-random states) are applied to that product form
- normalization: ${\rm Haar}_\nu$ is the $\nu$-qubit Haar ensemble, $d_\nu=2^\nu$; the ensemble average is over $\mu_{n,\nu}$

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · source_fidelity] Task statement for $t$-extraction says the state is 'promised to be $t$-doped with known $t$' while the task is to find $t$.
  - what could settle it: Errata or author clarification.
- [SCOPE_AMBIGUITY · mathematical_correctness] Cross-reference in the $\nu$-compressible consistency check points to the Haar theorem instead of the $\nu$-compressible theorem.
  - what could settle it: Errata; the intended check is unambiguous from context.

Records: `claim:opus5-2608.14798v1/c20`, `map:opus5-2608.14798v1/c20`, `math:opus5-2608.14798v1/m20`.

## c21 — Exact ensemble SPF for pseudomagic subset phase states

*Sec. IV E · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Theorem (SPF for pseudomagic states): for an $n$-qubit SPS sampled uniformly with $|S|=2^n$, $\mathcal{Z}_\beta({\rm SPS})=e^{-\beta}[\frac{(d_n-1)(d_n+2)}{2}+\cosh\beta+\frac{d_n(d_n-1)}{2}(\cosh(2\beta/d_n))^{d_n/2}]$. The paper adds that stabilizer nullity cannot quantify pseudomagic, since SPS and Haar states both have $\nu=\mathcal{O}(n)$, and that the SPF curves of the two families become exponentially close so that distinguishing them is challenging, as it must be for a cryptographic construction.

**System.** subset phase states $\ket{\psi_{f,S}}$ with pseudorandom $f$ and $S=\{0,1\}^n$

**Comparison baseline.** Haar-random states and $
u$-compressible states

**Stated conditions.**

- (SOURCE_EXPLICIT) the theorem is restricted to $|S|=2^n$, the single-subset case, where only the average over pseudorandom $f$ remains
- (SOURCE_EXPLICIT) the result is an ensemble average over the SPS family

**Components and their accounting.**

- `comp:thm` [CONCLUSION / MAPPED] Closed-form ensemble SPF for SPS at $|S|=2^n$.
  - residual: The general case $\log n\leq k<n$ (i.e. $|S|=2^k$) is excluded 'by simplicity', so the pseudomagic regime of primary cryptographic interest is not covered by the closed form.
- `comp:nullity` [CONCLUSION / RESIDUAL] Nullity does not separate SPS from Haar states; both have $\nu=\mathcal{O}(n)$.
- `comp:crypto` [LIMITATION / RESIDUAL] Efficient $\nu$-extraction must not translate into efficiently distinguishing SPS from Haar, else the pseudomagic definition would be contradicted.
  - residual: The tension between efficient $\nu$-extraction and computational indistinguishability is raised but not resolved; no quantitative gap statement is given.
- `comp:tunable` [CONCLUSION / RESIDUAL] Applying Cliffords tunes the entanglement of SPS while keeping magic content unchanged.
  - residual: 'keeping the magic content of the SPS unchanged' follows from Clifford invariance of the SPF but is asserted for 'magic content' generally.
- `comp:randomf` [ASSUMPTION / RESIDUAL] The supplemental derivation averages over a UNIFORMLY RANDOM Boolean function $f$ (the cumulant lemma says so explicitly), not over a pseudorandom one.
  - residual: The gap between the uniform-random-function average actually computed and the pseudorandom-function ensemble the section is about is not discussed. Closing it is routine for computationally bounded observers, but the theorem statement does not carry the condition.
- `comp:density` [EVIDENCE / RESIDUAL] A corollary gives the exact average SPS Pauli-spectrum density, a sum of delta peaks that does not smooth out under ensemble averaging, unlike the Haar case; it is checked numerically against exact Pauli expectations for $n\in\{2,4,6,8\}$, exhaustively over Boolean functions for $n=2,4$ and over 4096 and 2048 random functions for $n=6,8$.
  - residual: This is the only numerical validation in the paper that checks a derived formula rather than illustrating one; its data and code are still not supplied.

**Math target `m21`** (EXACT), covering `comp:thm`.

- conclusion: $\mathcal{Z}_{\beta}({\rm SPS})=e^{-\beta}\left[\tfrac{(d_{n}-1)(d_{n}+2)}{2}+\cosh\beta+\tfrac{d_{n}(d_{n}-1)}{2}\left(\cosh\!\left(\tfrac{2\beta}{d_{n}}\right)\right)^{d_{n}/2}\right]$.
- quantifier: FORALL n in positive integers with $d_n=2^n$
- quantifier: FORALL \beta in range not stated in the theorem
- assumption (SOURCE_EXPLICIT): $|S|=2^n$, so $S=\{0,1\}^n$ and the average is over the pseudorandom function $f$ only
- assumption (SOURCE_EXPLICIT): the proof rests on exact evaluation of the Pauli-spectrum moments of SPS, deferred to the supplement
- normalization: ensemble average; the $\beta\to0$ value should recover $d_n^2$, which the source does not verify here

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · semantic_applicability] The SPS closed form covers only $|S|=2^n$, whereas the pseudomagic gap construction is stated for $\log n\leq k\leq n$.
  - what could settle it: Extension of the moment computation to general $|S|=2^k$, or an explicit statement of what the $|S|=2^n$ case does and does not establish about pseudomagic.
- [SCOPE_AMBIGUITY · mathematical_correctness] Theorem (SPF for pseudomagic states) is stated for subset phase states built from a pseudorandom $f$, but the supplemental proof averages over a uniformly random $f$.
  - what could settle it: An explicit condition on the theorem, or the standard indistinguishability argument transferring the uniform-average result to the pseudorandom ensemble.

Records: `claim:opus5-2608.14798v1/c21`, `map:opus5-2608.14798v1/c21`, `math:opus5-2608.14798v1/m21`.

## c22 — Free states and free operations of the resource theory

*Sec. V, Sec. VII · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Free states are pure stabilizer states (convex hull for the mixed case). $\mathcal{F}_{\rm all}(A\to B)$ is defined as the channels preserving the stabilizer SPF value, which the paper equates with stabilizer-preserving operations (SPO) and notes contains stabilizer operations and CSPO. The pure-state development uses the smaller class $\mathcal{F}$ of deterministic pure-state stabilizer protocols: Clifford unitaries, stabilizer-state preparation, computational-basis measurement and partial trace, provided the output stays pure. Sec. VII characterizes $\mathcal{F}$ by Pauli-transfer-matrix conditions and states that the PTM of such a protocol is a signed permutation matrix, a discard-and-prepare matrix, or a matrix with exactly one 1 per column.

**System.** quantum channels between multi-qubit systems

**Comparison baseline.** stabilizer operations and completely stabilizer-preserving operations (CSPO)

**Stated conditions.**

- (SOURCE_EXPLICIT) the monotone statements of Sec. V are restricted to pure-state transformations
- (SOURCE_EXPLICIT) $\mathcal{F}$ consists of DETERMINISTIC protocols whose output remains pure

**Components and their accounting.**

- `comp:fall` [DEFINITION / RESIDUAL] $\mathcal{F}_{\rm all}$ = channels with $\mathcal{Z}_\beta(\mathcal{O}(\phi_A))=\mathcal{Z}_\beta({\rm STAB}_B)$ for all stabilizer inputs, identified with SPO.
  - residual: $\mathcal{F}_{\rm all}$ is defined for all $\beta$ simultaneously; whether a single $\beta$ suffices is not discussed.
- `comp:f` [DEFINITION / RESIDUAL] $\mathcal{F}$ = deterministic pure-state stabilizer protocols.
- `comp:ptm` [CONCLUSION / MAPPED] PTM characterization: signed permutation (Clifford), discard-and-prepare, or one 1 per column (subsystem discard).
  - residual: The claim that the PTM 'takes one of three forms' is stated as a classification without proof; it is asserted to follow from the two displayed conditions.
- `comp:relax` [MODEL / RESIDUAL] Approximate ($\epsilon$-close) PTM conditions are proposed as a route to bounding magic injected by imperfect Clifford hardware, tied to gate-set tomography.
  - residual: Proposed direction, not a result; no $\epsilon$-robustness bound is derived.

**Math target `m22`** (EXACT), covering `comp:ptm`.

- conclusion: For $\mathcal{O}\in\mathcal{F}$ and all $\phi\in{\rm STAB}_A$ with $p^{\phi}_j=\tr[\phi P_j]$: $\sum_j(R^{\mathcal{O}}_{AB})_{i,j}p^{\phi}_j\in\{0,\pm1\}$ and $\sum_i|\sum_j(R^{\mathcal{O}}_{AB})_{i,j}p^{\phi}_j|=d_B$, where $(R^{\mathcal{O}}_{AB})_{i,j}=\frac{1}{d_A}\tr[P^B_i\mathcal{O}(P^A_j)]$.
- quantifier: FORALL \mathcal{O} in $\mathcal{F}$
- quantifier: FORALL \phi in ${\rm STAB}_A$
- quantifier: FORALL i,j in Pauli indices of $\mathcal{P}_B$ and $\mathcal{P}_A$
- assumption (SOURCE_EXPLICIT): $\mathcal{O}\in{\rm CPTP}(A\to B)$
- assumption (SOURCE_RECONSTRUCTED): the output of $\mathcal{O}$ on a stabilizer input is again a pure stabilizer state
- normalization: PTM normalized by $1/d_A$; the conditions are stated on stabilizer inputs only

**Open items recorded against this claim.**

- [UNPROVED_LEMMA · mathematical_correctness] The three-form PTM classification of $\mathcal{F}$ is asserted without proof.
  - what could settle it: A proof, or a restriction of the claim to the examples exhibited.

Records: `claim:opus5-2608.14798v1/c22`, `map:opus5-2608.14798v1/c22`, `math:opus5-2608.14798v1/m22`.

## c23 — Stabilizer work is a faithful subadditive magic monotone

*Sec. V, abstract · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The stabilizer work $\mathcal{W}_\beta(\psi)=-\log\mathcal{Z}^c_\beta(\psi)+\log\mathcal{Z}^c_\beta({\rm STAB}_n)$ is claimed to be (1) faithful, (2) Clifford invariant, (3) subadditive, (4) monotone under discarding subsystems, (5) invariant under appending a stabilizer state. The abstract states more strongly that for every value of its parameter the stabilizer work is a faithful, subadditive MAGIC MONOTONE.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** $M_\alpha$ at fixed $\alpha$ (monotone only for $\alpha\geq2$) and the stabilizer nullity

**Stated conditions.**

- (SOURCE_EXPLICIT) restricted to pure states and to the class $\mathcal{F}$ of deterministic pure-state stabilizer protocols
- (SOURCE_RECONSTRUCTED) 'for every value of its parameter' in the abstract; the properties list does not state a $\beta$ range and $\mathcal{W}_0\equiv0$ by construction

**Components and their accounting.**

- `comp:faithful` [CONCLUSION / MAPPED] $\mathcal{W}_\beta(\psi_A)=0\iff\psi_A\in{\rm STAB}_A$, from uniqueness of the cSPF on stabilizer states.
  - residual: The $\beta=0$ case is degenerate: $\mathcal{Z}^c_0\equiv0$ for every state, so $\mathcal{W}_0$ is a $\log$ of $0/0$ and faithfulness is empty there; the source does not exclude $\beta=0$ in the properties list.
- `comp:clifford` [CONCLUSION / RESIDUAL] Clifford invariance, from invariance of the SPF.
- `comp:subadd` [CONCLUSION / MAPPED] $\mathcal{W}_\beta(\psi_A\otimes\chi_B)\leq\mathcal{W}_\beta(\psi_A)+\mathcal{W}_\beta(\chi_B)$, from cSPF supermultiplicativity.
  - residual: Subadditivity inherits the unproved reweighting hypothesis of Lemma (cSPF supermultiplicativity).
- `comp:discard` [CONCLUSION / MAPPED] $\mathcal{W}_\beta(\psi_A\otimes\chi_B)\geq\mathcal{W}_\beta(\psi_A)$, with equality iff the discarded subsystem is a stabilizer state, established from $b_k\leq d_B$.
- `comp:monotone` [LIMITATION / RESIDUAL] The abstract, the introduction and the discussion call $\mathcal{W}_\beta$ a magic monotone at every temperature.
  - residual: The five listed properties do not include monotonicity under the free class $\mathcal{F}$. Property 4 is monotonicity under DISCARDING SUBSYSTEMS only; no statement or proof covers computational-basis measurement, stabilizer-state preparation, or general $\mathcal{F}$ protocols. The abstract's unqualified 'magic monotone' is therefore stronger than what Sec. V establishes, and the discussion's own open-problem list asks for monotonicity to be established for the mixed-state and channel extensions.

**Math target `m23`** (EXACT), covering `comp:faithful`, `comp:subadd`, `comp:discard`.

- conclusion: $\mathcal{W}_{\beta}(\psi)=0\iff\psi\in{\rm STAB}$; $\mathcal{W}_{\beta}(\psi_A\otimes\chi_B)\leq\mathcal{W}_{\beta}(\psi_A)+\mathcal{W}_{\beta}(\chi_B)$; $\mathcal{W}_{\beta}(\psi_A\otimes\chi_B)\geq\mathcal{W}_{\beta}(\psi_A)$ with equality iff $\chi_B\in{\rm STAB}_B$.
- quantifier: FORALL \beta in $\beta\neq0$; at $\beta=0$ the stabilizer work vanishes identically and faithfulness is vacuous
- quantifier: FORALL \psi_A,\chi_B in pure states of the respective subsystems
- assumption (SOURCE_EXPLICIT): Lemma (cSPF supermultiplicativity)
- assumption (SOURCE_EXPLICIT): uniqueness of the cSPF on pure stabilizer states
- assumption (SOURCE_EXPLICIT): $b_k\leq d_B$ in the notation of the supermultiplicativity proof
- normalization: $\log$ base 2; $\mathcal{W}_\beta\geq0$ with equality exactly on the free set

**Open items recorded against this claim.**

- [ALIGNMENT_GAP · mathematical_correctness, source_fidelity] The abstract asserts that the stabilizer work is a magic monotone for every $\beta$, while Sec. V proves only faithfulness, Clifford invariance, subadditivity, monotonicity under discarding subsystems, and stabilizer-ancilla invariance. Monotonicity under the declared free class $\mathcal{F}$ (which includes computational-basis measurement) is not proved anywhere in the paper.
  - what could settle it: A proof of monotonicity under every element of $\mathcal{F}$, or a weakening of the abstract's claim to the five established properties. Theorem (One-shot interconversion bound) explicitly invokes the unproved monotonicity as its first inequality.
- [SCOPE_AMBIGUITY · mathematical_correctness] $\beta=0$ is not excluded from the properties list although $\mathcal{Z}^c_0\equiv0$ makes $\mathcal{W}_0$ ill-defined.
  - what could settle it: Explicit restriction to $\beta\neq0$, as done in Sec. VI B for the interconversion family.

Records: `claim:opus5-2608.14798v1/c23`, `map:opus5-2608.14798v1/c23`, `math:opus5-2608.14798v1/m23`.

## c24 — Bounds, limits and the interpolation claim for stabilizer work

*Sec. V · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Corollary (Bounds on Stabilizer Work): $0\leq\mathcal{W}_\beta(\psi)\leq\log\frac{d_A\cosh\beta-d_A}{\cosh\beta+(d_A^2-1)\cosh(\beta/\sqrt{d_A+1})-d_A^2}$. In the limit $\beta\to\infty$ the stabilizer work converges to the stabilizer nullity; for $\beta\to0$ it reduces, at leading order, to a function of the second-order stabilizer Renyi entropy alone. The paper concludes that stabilizer work provides a continuous and monotonic interpolation between two previously independent measures.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the stabilizer nullity $\nu$ and the 2-stabilizer Renyi entropy $M_2$

**Stated conditions.**

- (SOURCE_EXPLICIT) $\beta\in\mathbb{R}$ in the corollary; the limit statements concern $\beta\to0$ and $\beta\to\infty$

**Components and their accounting.**

- `comp:bounds` [CONCLUSION / MAPPED] Explicit two-sided bound following from the state-independent SPF bounds.
  - residual: Displayed as $d^2_A$ in one place and $d_A^2$ elsewhere; singular at $\beta=0$.
- `comp:lowT` [CONCLUSION / RESIDUAL] $\beta\to\infty$: stabilizer work converges to stabilizer nullity.
  - residual: No rate or error term is given for the $\beta\to\infty$ convergence to $\nu$, and no proof is given in the main text.
- `comp:hiT` [APPROXIMATION / RESIDUAL] $\beta\to0$: at leading order a function of $M_2$ alone.
  - residual: 'Reduces, at leading order, to a function of $M_2$' is not made explicit: the function, the expansion order, and the error term are not stated.
- `comp:interp` [CONCLUSION / RESIDUAL] Continuous and monotonic interpolation between $M_2$ and $\nu$.
  - residual: 'Continuous and monotonic interpolation' asserts monotonicity of $\beta\mapsto\mathcal{W}_\beta$, which is nowhere proved; the numerical figures are consistent with it but no argument is supplied.

**Math target `m24`** (EXACT), covering `comp:bounds`.

- conclusion: $0\leq\mathcal{W}_{\beta}(\psi)\leq\log\!\left(\dfrac{d_{A}\cosh\beta-d_{A}}{\cosh\beta+(d_{A}^{2}-1)\cosh\!\left(\beta/\sqrt{d_{A}+1}\right)-d_{A}^{2}}\right)$.
- quantifier: FORALL \beta in $\mathbb{R}$ as stated; the expression is singular at $\beta=0$
- quantifier: FORALL \psi in pure states of an $n$-qubit system $A$, $d_A=2^n$
- assumption (SOURCE_EXPLICIT): Theorem (SPF state-independent bounds) applied to $\mathcal{Z}^c_\beta=\mathcal{Z}_\beta-d_A^2e^{-\beta}$
- normalization: $\log$ base 2; numerator and denominator are $e^{\beta}\mathcal{Z}^c_\beta$ of the stabilizer reference and of the extremal lower configuration respectively

**Open items recorded against this claim.**

- [UNPROVED_LEMMA · mathematical_correctness] Monotonicity of $\beta\mapsto\mathcal{W}_\beta(\psi)$ is used verbally ('continuous and monotonic interpolation', 'grows monotonically with $\beta$' in the applications) but never proved.
  - what could settle it: A proof that $\partial_\beta\mathcal{W}_\beta\geq0$, or a restriction of the interpolation claim to the two endpoint limits.
- [UNPROVED_LEMMA · mathematical_correctness] The two limiting statements ($\beta\to\infty$ gives $\nu$; $\beta\to0$ gives a function of $M_2$) are asserted in the main text with no derivation and no error terms.
  - what could settle it: Explicit expansions with remainder, or supplementary proofs; none appear in the supplemental material.

Records: `claim:opus5-2608.14798v1/c24`, `map:opus5-2608.14798v1/c24`, `math:opus5-2608.14798v1/m24`.

## c25 — Continuity of stabilizer work and its dimension-free constant

*Sec. V A · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Lemma (Continuity of the Stabilizer Work): $|\mathcal{W}_\beta(\psi)-\mathcal{W}_\beta(\phi)|\leq K_n(\beta)\|\psi-\phi\|_1$ with $K_n(\beta)=2\beta^{-1}\sinh\beta$. The paper stresses that, unlike $L_n(\beta)$, this constant does not grow exponentially with the qubit number, so concentration statements for the stabilizer work are stronger than those for the SPF.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the SPF Lipschitz constant $L_n(\beta)=e^{-\beta}d_n\beta\sinh\beta$

**Stated conditions.**

- (SOURCE_EXPLICIT) $\psi,\phi$ pure $n$-qubit states
- (SOURCE_EXPLICIT) the proof uses $|\log a-\log b|\leq|a-b|/\min\{a,b\}$, the SPF Lipschitz property, and $\cosh x-1\geq x^2/2$ in the state-independent lower bound

**Components and their accounting.**

- `comp:bound` [CONCLUSION / MAPPED] $|\mathcal{W}_\beta(\psi)-\mathcal{W}_\beta(\phi)|\leq2\beta^{-1}\sinh\beta\,\|\psi-\phi\|_1$.
  - residual: Base of the logarithm in $\mathcal{W}$ versus the $\log$ used in the inequality $|\log a-\log b|\leq|a-b|/\min\{a,b\}$ is not reconciled; a factor $1/\ln2$ is unaccounted for.
- `comp:tighter` [EVIDENCE / RESIDUAL] A tighter intermediate bound $d_ne^{-\beta}\beta\sinh\beta/\min\{\mathcal{Z}^c_\beta(\psi),\mathcal{Z}^c_\beta(\phi)\}$ is displayed and reused later for the fidelity bound.
- `comp:dimfree` [CONCLUSION / RESIDUAL] $K_n(\beta)$ carries no $d_n$, which the paper attributes to the logarithmic ratio structure.
  - residual: The constant is written $K_n(\beta)$ with an $n$ subscript although the stated value $2\beta^{-1}\sinh\beta$ carries no $n$ dependence.

**Math target `m25`** (EXACT), covering `comp:bound`.

- conclusion: $|\mathcal{W}_{\beta}(\psi)-\mathcal{W}_{\beta}(\phi)|\leq K_{n}(\beta)\|\psi-\phi\|_{1}$ with $K_{n}(\beta)=2\beta^{-1}\sinh\beta$, independent of $n$ despite the subscript.
- quantifier: FORALL \beta in $\beta>0$ is required for $\beta^{-1}$ to be defined; the lemma does not say so
- quantifier: FORALL \psi,\phi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_EXPLICIT): $|\log a-\log b|\leq|a-b|/\min\{a,b\}$ for positive $a,b$
- assumption (SOURCE_EXPLICIT): Theorem (Lipschitz property) for the SPF
- assumption (SOURCE_EXPLICIT): $\cosh x-1\geq x^2/2$ applied inside the state-independent SPF lower bound
- normalization: the natural versus base-2 logarithm is not made explicit in the constant, although $\mathcal{W}$ is defined with $\log_2$

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · mathematical_correctness] The continuity constant is derived using an inequality for the natural logarithm while $\mathcal{W}_\beta$ is defined with $\log_2$; the resulting factor $1/\ln2$ is not visible in $K_n(\beta)=2\beta^{-1}\sinh\beta$.
  - what could settle it: Recomputation of the constant with an explicit logarithm base, which would also fix the constant used in Proposition (Stabilizer fidelity upper bounds).

Records: `claim:opus5-2608.14798v1/c25`, `map:opus5-2608.14798v1/c25`, `math:opus5-2608.14798v1/m25`.

## c26 — Ensemble averages of stabilizer work and the small-gap lemma

*Sec. V A · modality APPROXIMATE · coverage PARTIAL*

**What the authors said.** Because $-\log$ is convex, the ensemble average of the stabilizer work is not the stabilizer work of the ensemble-averaged cSPF, so ensemble averages require separate analysis. Lemma (Small gap): for an ensemble $\mathcal{E}$, with negligible failure probability every $\psi\in\mathcal{E}$ satisfies $\mathcal{W}_\beta(\psi)-\mathcal{W}_\beta(\mathcal{E})\in[-{\rm logPoly}(n),\mathcal{O}(\beta^4)+{\rm LogPoly}(n)]$. Applied to SPS versus $\nu$-compressible states, the two ensembles are separated whenever $|\mathcal{W}_\beta({\rm SPS})-\mathcal{W}_\beta({\rm Comp}_\nu)|>{\rm LogPoly}(n)$.

**System.** ensembles of $n$-qubit pure states

**Comparison baseline.** the ensemble-averaged SPF, for which exact closed forms are available

**Stated conditions.**

- (SOURCE_EXPLICIT) 'with negligible failure probability' is not quantified
- (SOURCE_EXPLICIT) the proof is stated to control tails with Markov's inequality, details deferred to the supplement

**Components and their accounting.**

- `comp:jensen` [CONCLUSION / RESIDUAL] $\mathbb{E}_\psi[\mathcal{W}_\beta(\psi)]\neq\log\mathbb{E}_\psi[\mathcal{Z}^c_\beta(\psi)]$; ensemble means of work need independent analysis.
  - residual: Stated as an inequality of expectations; the direction implied by convexity is not used explicitly.
- `comp:gap` [APPROXIMATION / MAPPED] Two-sided confidence interval with asymmetric width, the upper side carrying an $n$-independent $\mathcal{O}(\beta^4)$ term.
  - residual: ${\rm logPoly}(n)$ and ${\rm LogPoly}(n)$ appear with different capitalization in the same displayed formula and are never defined; the supplemental proof fixes the failure probability as $1/{\rm Poly}(n)$ with ${\rm Poly}$ still free, chosen by the reader through the Markov threshold.
- `comp:sps` [CONCLUSION / RESIDUAL] Disjoint confidence intervals give a threshold classifier separating SPS from $\nu$-compressible ensembles.
  - residual: The separation criterion is stated in terms of an unquantified ${\rm LogPoly}(n)$, so it cannot be evaluated for any concrete $n$, $\nu$ or $\beta$ from the paper alone.
- `comp:proof` [EVIDENCE / RESIDUAL] The supplemental proof uses Markov's inequality on $e^{\mp\mathcal{W}_\beta}$ plus the Kantorovich inequality to bound the reciprocal average, and derives the explicit constant ${\rm Small}_\beta=2\log({\rm AM/GM})\leq\beta^4/576$ from the state-independent SPF bounds; the two events are then combined by a union bound.
  - residual: The $\mathcal{O}(\beta^4)$ half of the interval is genuinely derived, with the explicit constant $1/576$. The $n$-dependent half is not: it is whatever polynomial the reader picks in the Markov step, so the lemma cannot be instantiated at a fixed $n$ without that choice.

**Math target `m26`** (ASYMPTOTIC), covering `comp:gap`.

- conclusion: $\mathcal{W}_{\beta}(\psi)-\mathcal{W}_{\beta}(\mathcal{E})\in[-{\rm logPoly}(n),\ \mathcal{O}(\beta^{4})+{\rm LogPoly}(n)]$ for every $\psi\in\mathcal{E}$ outside a negligible-probability set.
- quantifier: FORALL \mathcal{E} in ensembles of $n$-qubit pure states; no structural restriction is imposed
- quantifier: FORALL \psi in $\mathcal{E}$, outside a set of negligible probability
- assumption (SOURCE_EXPLICIT): $\mathcal{W}_\beta(\mathcal{E}):=-\log\mathcal{Z}^c_\beta(\mathcal{E})+\log\mathcal{Z}^c_\beta({\rm Stab}_n)$ with $\mathcal{Z}_\beta(\mathcal{E})$ the ensemble-averaged SPF
- assumption (SOURCE_EXPLICIT): Markov-type tail control, deferred to the supplement
- normalization: the statement mixes ${\rm logPoly}(n)$ and ${\rm LogPoly}(n)$ notations without defining either; neither the polynomial degree nor the implied constants are given
- approximation error: ${\rm logPoly}(n)$ on the lower side and $\mathcal{O}(\beta^{4})+{\rm LogPoly}(n)$ on the upper side, with unspecified constants; 'negligible failure probability' is not quantified

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · mathematical_correctness, semantic_applicability] Lemma (Small gap) and the SPS-versus-compressible separation criterion are stated with undefined ${\rm logPoly}(n)$/${\rm LogPoly}(n)$ terms and an unquantified 'negligible failure probability'. The supplemental proof supplies the $\beta$-dependent constant ($\beta^4/576$) but leaves the polynomial free.
  - what could settle it: A worked instance at fixed $n,\nu,\beta$ fixing the polynomial, which is what the SPS-versus-compressible classifier would need to be usable.

Records: `claim:opus5-2608.14798v1/c26`, `map:opus5-2608.14798v1/c26`, `math:opus5-2608.14798v1/m26`.

## c27 — Stabilizer fidelity upper bound from stabilizer work

*Sec. VI A · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Proposition (Stabilizer fidelity upper bounds): $F_{\rm Stab}(\psi)\leq1-\frac12\left(\frac{\cosh\beta-1}{\beta\sinh\beta}2^{-\mathcal{W}_\beta(\psi)}\mathcal{W}_\beta(\psi)\right)^2$ for all $\beta\geq0$, tightest after optimizing over $\beta$. This upper-bounds the stabilizer fidelity and thereby lower-bounds the stabilizer extent and the approximate stabilizer rank. The paper also quotes a complementary lower bound $\frac{\alpha-1}{2\alpha}M_\alpha(\psi)\leq F_{\rm Stab}(\psi)$, and gives the worked consequence that no pure stabilizer state is $\epsilon$-close in fidelity to $\ket{T}^{\otimes n}$ for $\epsilon\lesssim2.27\times10^{-3}$, independently of the number of copies.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** stabilizer extent $\xi$ and approximate stabilizer rank $\chi_\delta$, via $\xi\geq F_{\rm Stab}^{-1}$ and $\chi_\delta\leq1+\delta^{-2}\xi$

**Stated conditions.**

- (SOURCE_EXPLICIT) $\beta\geq0$
- (SOURCE_EXPLICIT) the $\ket{T}^{\otimes n}$ consequence uses $\mathcal{W}_\beta(\ket{T}^{\otimes n})\geq\mathcal{W}_\beta(\ket{T})$, i.e. the discarding property

**Components and their accounting.**

- `comp:ub` [CONCLUSION / MAPPED] Family of stabilizer-fidelity upper bounds parameterized by $\beta$.
- `comp:chain` [CONCLUSION / RESIDUAL] Upper bound on $F_{\rm Stab}$ lower-bounds $\xi$ and hence constrains $\chi_\delta$.
  - residual: The chain to $\chi_\delta$ is quoted from prior work; no new bound on the stabilizer rank is derived here.
- `comp:lb` [ATTRIBUTION / UNRESOLVED] Quoted complementary bound $\frac{\alpha-1}{2\alpha}M_\alpha(\psi)\leq F_{\rm Stab}(\psi)$, attributed to prior work.
  - residual: As printed, $\frac{\alpha-1}{2\alpha}M_\alpha(\psi)\leq F_{\rm Stab}(\psi)$ is inconsistent with $F_{\rm Stab}\leq1$: for a 4-qubit state with $M_2=2$ it would force $F_{\rm Stab}\geq1/2$, which contradicts the paper's own upper bound for magic states. The intended form is presumably a bound on $\log(1/F_{\rm Stab})$. Recorded as printed; not repaired.
- `comp:example` [EVIDENCE / RESIDUAL] Numerical consequence: no stabilizer state is $\epsilon$-close to $\ket{T}^{\otimes n}$ for $\epsilon\lesssim2.27\times10^{-3}$, uniformly in $n$.
  - residual: The number $2.27\times10^{-3}$ comes from 'straightforward numerical maximization' with no code, grid, or optimizing $\beta$ reported, so it is not reproducible from the paper.

**Math target `m27`** (EXACT), covering `comp:ub`.

- conclusion: $F_{\rm Stab}(\psi)\leq1-\tfrac12\left(\dfrac{\cosh\beta-1}{\beta\sinh\beta}\,2^{-\mathcal{W}_{\beta}(\psi)}\mathcal{W}_{\beta}(\psi)\right)^{2}$ for every $\beta\geq0$.
- quantifier: FORALL \beta in $[0,\infty)$ as stated; the expression is $0/0$ at $\beta=0$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_EXPLICIT): faithfulness of $\mathcal{W}_\beta$ plus the tighter continuity estimate of Lemma (Continuity of the Stabilizer Work)
- assumption (SOURCE_EXPLICIT): the right-hand side is independent of which stabilizer state is used, so maximizing over ${\rm STAB}$ is legitimate
- assumption (SOURCE_RECONSTRUCTED): $\|\psi-\phi\|_1=2\sqrt{1-|\braket{\phi|\psi}|^2}$ for pure states
- normalization: $\log$ base 2 in $\mathcal{W}$ and the factor $2^{-\mathcal{W}_\beta}$; the same base-of-logarithm question flagged for the continuity constant propagates here

**Open items recorded against this claim.**

- [CONFLICT · source_fidelity, mathematical_correctness] The quoted stabilizer-fidelity lower bound $\frac{\alpha-1}{2\alpha}M_\alpha(\psi)\leq F_{\rm Stab}(\psi)$ is dimensionally inconsistent with $F_{\rm Stab}\leq1$ for states with appreciable $M_\alpha$.
  - what could settle it: Check against the cited sources (Haug-Piroli; Gu et al.), which state a bound on $\log(1/F_{\rm Stab})$; this round records the conflict without consulting those papers.
- [DATA_MISSING · computational_reproducibility] The threshold $\epsilon\lesssim2.27\times10^{-3}$ for $\ket{T}^{\otimes n}$ is reported without the optimizing $\beta$, the numerical procedure, or code.
  - what could settle it: Author-supplied script or the optimizing $\beta$ value; recomputation was not attempted in this round.

Records: `claim:opus5-2608.14798v1/c27`, `map:opus5-2608.14798v1/c27`, `math:opus5-2608.14798v1/m27`.

## c28 — Interconversion bounds, magic cost and distillation converse

*Sec. VI B · modality CONDITIONAL · coverage PARTIAL*

**What the authors said.** Theorem (One-shot interconversion bound): if $n$ copies of $\psi$ convert to $m$ copies of $\phi$ by free operations, then for every $\beta\neq0$, $\mathcal{W}_\beta(\phi^{\otimes m})\leq\mathcal{W}_\beta(\psi^{\otimes n})\leq n\mathcal{W}_\beta(\psi)$. Corollaries give a $T$-cost lower bound and a distillation converse. Because each $\beta$ is an independent witness, crossing curves certify two-directional incomparability; the paper notes the conditions are necessary but not sufficient, exhibiting $\ket{H}\to\ket{T}$ as a case where the bound does not obstruct a conversion that no deterministic stabilizer protocol realizes.

**System.** pure-state resource interconversion under the class $\mathcal{F}$

**Comparison baseline.** single-monotone obstructions and single-copy ratio bounds

**Stated conditions.**

- (SOURCE_EXPLICIT) conversion is by operations in $\mathcal{F}$, the class under which $\mathcal{W}_\beta$ is claimed to be a monotone
- (SOURCE_EXPLICIT) $\beta\neq0$
- (SOURCE_RECONSTRUCTED) the first inequality IS monotonicity of $\mathcal{W}_\beta$ under $\mathcal{F}$, which is asserted but not proved in the paper

**Components and their accounting.**

- `comp:bound` [CONCLUSION / MAPPED] $\mathcal{W}_\beta(\phi^{\otimes m})\leq\mathcal{W}_\beta(\psi^{\otimes n})\leq n\mathcal{W}_\beta(\psi)$.
  - residual: The load-bearing first inequality is exactly the monotonicity property that Sec. V lists but does not prove for $\mathcal{F}$.
- `comp:strictness` [CONCLUSION / RESIDUAL] The tensor-power form is strictly stronger than single-copy bounds whenever subadditivity is strict, i.e. whenever neither state is a stabilizer state.
  - residual: 'Strictly stronger ... whenever subadditivity is strict' presumes strictness for all non-stabilizer states, which is not established.
- `comp:incomp` [CONCLUSION / RESIDUAL] Crossing $\beta$-curves certify incomparability in both directions.
- `comp:notsuff` [LIMITATION / RESIDUAL] $\ket{H}$ dominates $\ket{T}$ at every $\beta$ yet no deterministic stabilizer protocol converts $\ket{H}\to\ket{T}$; the condition is necessary, not sufficient.
  - residual: The assertion that no deterministic stabilizer protocol realizes $\ket{H}\to\ket{T}$ is stated without proof or citation.
- `comp:tcost` [CONCLUSION / MAPPED] $T$-cost lower bound $t\geq\sup_{\beta\neq0}\min\{t':\mathcal{W}_\beta(T^{\otimes t'})\geq\mathcal{W}_\beta(\phi)\}$, weakening to $t\geq\sup_\beta\mathcal{W}_\beta(\phi)/\mathcal{W}_\beta(T)$.
  - residual: The commented-out closed form for $\mathcal{W}_\beta(\chi^{\otimes r})$ and the endpoint bounds ($\beta\to0$ giving $t\geq M_2(\phi)/\ln\frac43$, $\beta\to\infty$ giving $t\geq\nu(\phi)$) are present in the source only as LaTeX comments, i.e. they are not claims of the published text.
- `comp:distill` [CONCLUSION / RESIDUAL] Distillation converse $\mathcal{W}_\beta(T^{\otimes m})\leq n\mathcal{W}_\beta(\psi)$.

**Math target `m28`** (EXACT), covering `comp:bound`, `comp:tcost`.

- conclusion: If $\psi^{\otimes n}\to\phi^{\otimes m}$ under $\mathcal{F}$ then $\forall\beta\neq0$: $\mathcal{W}_{\beta}(\phi^{\otimes m})\leq\mathcal{W}_{\beta}(\psi^{\otimes n})\leq n\,\mathcal{W}_{\beta}(\psi)$; consequently $t\geq\sup_{\beta\neq0}\min\{t':\mathcal{W}_{\beta}(T^{\otimes t'})\geq\mathcal{W}_{\beta}(\phi)\}$.
- quantifier: FORALL \beta in $\mathbb{R}\setminus\{0\}$
- quantifier: EXISTS \Lambda in an operation in $\mathcal{F}$ with $\Lambda(\psi^{\otimes n})=\phi^{\otimes m}$ (the hypothesis of the theorem)
- quantifier: FORALL n,m in positive integers
- assumption (SOURCE_RECONSTRUCTED): $\mathcal{W}_\beta$ is monotone under $\mathcal{F}$ (asserted in Sec. V; no proof in the paper)
- assumption (SOURCE_EXPLICIT): subadditivity of $\mathcal{W}_\beta$ (Theorem, resting on Lemma (cSPF supermultiplicativity))
- normalization: conversion is exact and deterministic; no error tolerance, catalysis or asymptotic rate is involved

**Open items recorded against this claim.**

- [ALIGNMENT_GAP · mathematical_correctness] Theorem (One-shot interconversion bound) uses monotonicity of $\mathcal{W}_\beta$ under $\mathcal{F}$ as its first inequality, but that monotonicity is not established anywhere in the paper.
  - what could settle it: Same resolution as the monotonicity gap recorded for the stabilizer-work property list.
- [MISSING_SOURCE · mathematical_correctness] The claim that no deterministic stabilizer protocol converts $\ket{H}$ into $\ket{T}$ has no proof or citation in the text.
  - what could settle it: A citation or an argument; this round did not attempt to verify it.

Records: `claim:opus5-2608.14798v1/c28`, `map:opus5-2608.14798v1/c28`, `math:opus5-2608.14798v1/m28`.

## c29 — H2 dissociation: stabilizer work as a chemistry diagnostic

*Sec. VI C and Supplemental Material · modality OBSERVED · coverage COMPLETE*

**What the authors said.** For $\mathrm{H}_2$ in the minimal STO-3G basis (four spin-orbitals, four qubits, Jordan-Wigner, exact diagonalization) the stabilizer work and $M_2$ are small near equilibrium, peak in the strongly correlated intermediate region and decrease toward dissociation; increasing $\beta$ sharpens the features and at large $\beta$ tracks the shape of $M_2$. The paper states explicitly that nonstabilizerness of a molecular ground state is not basis-independent, and the 6-31G repetition (eight qubits) shows the peak displaced, appreciable magic retained at large $R$, and the ordering between $R=0.5$ and $R=6$ bohr reversed.

**System.** electronic ground state of $\mathrm{H}_2$ along the dissociation coordinate, Jordan-Wigner qubit Hamiltonian, full CI within the chosen basis

**Comparison baseline.** $M_{\alpha=2}$ along the same curve, and the STO-3G versus 6-31G comparison

**Stated conditions.**

- (SOURCE_EXPLICIT) results are basis-set and fermion-to-qubit-encoding dependent; neither basis approaches the complete-basis-set limit
- (SOURCE_EXPLICIT) ground states obtained by exact diagonalization (full CI within basis) of the Jordan-Wigner Hamiltonian
- (SOURCE_EXPLICIT) $\beta\in\{0.5,2,10,50,100\}$ are shown

**Components and their accounting.**

- `comp:peak` [EVIDENCE / MAPPED] Pronounced magic peak in the strongly correlated region in both bases.
  - residual: Figure-level reading; no tabulated values are given, so the peak position and height cannot be extracted from the text.
- `comp:beta` [EVIDENCE / MAPPED] $\beta$ acts as a resolution knob: small $\beta$ coarse and smooth, large $\beta$ sharp and tracking $M_2$.
  - residual: 'Tracks the overall shape of $M_2$' is qualitative; no correlation measure is reported.
- `comp:caveat` [LIMITATION / MAPPED] Explicit refusal to draw physical conclusions; dissociation-limit decay is a minimal-basis artifact.
- `comp:reversal` [EVIDENCE / MAPPED] In 6-31G the geometry ordering between $R=0.5$ and $R=6$ bohr reverses relative to STO-3G.
  - residual: Reported from figures only; the underlying statevectors and $\mathcal{W}_\beta$ values are not published.

**Math target.** None. This claim was not forced into a MathClaim; its meaning is retained in the claim record and, where applicable, in a SemanticContext.

**Semantic context `sc29`.** molecular hydrogen along the H-H dissociation coordinate, mapped to 4 qubits (STO-3G) or 8 qubits (6-31G) by Jordan-Wigner

- approximation regime: finite one-particle basis (STO-3G, 6-31G); the paper states neither approaches the complete-basis-set limit
- error bound: none reported; no error bars, convergence study, or basis extrapolation
- limitation: Nonstabilizerness here is a property of an encoding, not of the molecule; the paper says so explicitly and declines physical conclusions.
- limitation: Peak position, dissociation-limit magic and the ordering between two fixed geometries are all shown to be basis-set sensitive.
- limitation: No data, code, geometries, or numerical tolerances are provided, so none of the curves is reproducible from the paper alone.

**Open items recorded against this claim.**

- [DATA_MISSING · computational_reproducibility, empirical_support] No geometries, integrals, statevectors, code, or numerical values are supplied for the $\mathrm{H}_2$ curves in either basis.
  - what could settle it: Author-supplied data or code; an independent recomputation would need the bond-length grid and the integral source. Not attempted in this round.
- [MODEL_ASSUMPTION · semantic_applicability] The mapping from 'stabilizer work of the encoded statevector' to 'nonstabilizerness of the molecule' is disclaimed by the authors but is still used as the section's framing.
  - what could settle it: Encoding-invariance study, or restriction of the claim to the encoded state.

Records: `claim:opus5-2608.14798v1/c29`, `map:opus5-2608.14798v1/c29`, `semantics:opus5-2608.14798v1/sc29`.

## c30 — Transverse-field Ising: extensivity and a nonstabilizerness ridge

*Sec. VI D and Supplemental Material · modality OBSERVED · coverage COMPLETE*

**What the authors said.** For the 1D transverse-field Ising model $H=-g\sum_i\sigma^z_i\sigma^z_{i+1}-h\sum_i\sigma^x_i$, the stabilizer work in the paramagnetic phase rises monotonically in $\beta$ and saturates, with a clean ordering in system size indicating extensivity; the apparent increment is close to 1 per site, which the paper links to a stabilizer state having $2^L$ unit-weight Paulis and hence a saturation of order $L-1$. Over the full $(h/g,\beta)$ landscape the two field extremes are exactly solvable stabilizer points (GHZ at $h/g\to0$, $\ket{+}^{\otimes L}$ at $h/g\to\infty$) so the surface approaches its stabilizer floor there, and the ridge of nonstabilizerness lies in the interior near the critical point $h/g=1$.

**System.** ground states of the 1D transverse-field quantum Ising chain of $L$ spins

**Comparison baseline.** $M_\alpha$ for $\alpha=2,5,10$ across the same transition

**Stated conditions.**

- (SOURCE_EXPLICIT) one-dimensional chain; critical point at $h=g$
- (SOURCE_EXPLICIT) finite $L$; panel (b) uses $L=8$
- (SOURCE_EXPLICIT) the extensivity observation is made in the paramagnetic phase at $h/g\approx1.5$

**Components and their accounting.**

- `comp:expansion` [EVIDENCE / MAPPED] Small-$\beta$ expansion: the $O(\beta^2)$ term is purity-fixed ($\sum_P\langle P\rangle^2=2^L$) and carries no magic; the first nonstabilizer information enters at $O(\beta^4)$ via $\sum_P\langle P\rangle^4$, the participation behind $M_2$.
- `comp:extensive` [EVIDENCE / MAPPED] Clean size ordering in the paramagnetic phase, increment close to 1 per site, saturation of order $L-1$.
  - residual: 'The apparent increment is close to 1 per site, which is suggestive' is explicitly hedged; the saturation value $L-1$ is a heuristic, not a derived result.
- `comp:ridge` [EVIDENCE / MAPPED] Stabilizer floors at both field extremes and an interior ridge near $h/g=1$; the pattern persists along $\beta$.
  - residual: The claim that the surface 'should decrease again as $h/g$ grows beyond the window shown' is an expectation about data outside the plotted range.
- `comp:notation` [LIMITATION / MAPPED] The text introduces the coupling as $J$ while the Hamiltonian and all plots use $g$.
  - residual: Coupling named $J$ in prose and $g$ in the Hamiltonian; only $g$ is used thereafter.

**Math target.** None. This claim was not forced into a MathClaim; its meaning is retained in the claim record and, where applicable, in a SemanticContext.

**Semantic context `sc30`.** 1D transverse-field Ising chain, $H=-g\sum_i\sigma^z_i\sigma^z_{i+1}-h\sum_i\sigma^x_i$, finite $L$, ground state

- approximation regime: finite-size chains at selected $\beta$; no finite-size scaling analysis is performed
- error bound: none reported
- limitation: 'Suggestive' extensivity at increment 1 per site is read off plots at small $L$ with no scaling collapse or fit.
- limitation: The claimed stabilizer floor at $h/g\to0$ and $h/g\to\infty$ is argued from exact endpoints, not measured at those endpoints in the shown window.
- limitation: No code, chain lengths beyond the figures, boundary conditions, or numerical tolerances are given.

**Open items recorded against this claim.**

- [DATA_MISSING · computational_reproducibility] No solver, boundary conditions, system sizes beyond the figures, or numerical data are given for the Ising results.
  - what could settle it: Author-supplied code or data tables; recomputation was not attempted in this round.
- [SCOPE_AMBIGUITY · source_fidelity] The Ising coupling is introduced as $J$ in the prose but written $g$ in the Hamiltonian and figures.
  - what could settle it: Errata; unambiguous from context.

Records: `claim:opus5-2608.14798v1/c30`, `map:opus5-2608.14798v1/c30`, `semantics:opus5-2608.14798v1/sc30`.

## c31 — Extensions to mixed states and channels

*Sec. VII · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The SPF is extended to mixed states by a convex-roof supremum over pure-state decompositions, argued to preserve faithfulness because the SPF is maximized on stabilizer states, and to channels through the normalized Choi matrix. The paper states explicitly that establishing monotonicity of the corresponding stabilizer work for these extensions is left for future work, and lists it as the first of three open problems.

**System.** mixed states $\rho\in\mathcal{D}(\mathcal{H}_A)$ and CPTP maps $\mathcal{N}\in{\rm CPTP}(A\to B)$

**Comparison baseline.** the pure-state framework of Secs. III-VI

**Stated conditions.**

- (SOURCE_EXPLICIT) the extension uses a SUPREMUM, justified by the SPF being maximized by stabilizer states
- (SOURCE_EXPLICIT) the channel definition uses the NORMALIZED Choi matrix with $|A|=|A'|$
- (SOURCE_EXPLICIT) monotonicity for both extensions is explicitly left open

**Components and their accounting.**

- `comp:mixed` [DEFINITION / MAPPED] $\mathcal{Z}_\beta(\rho)=\sup\sum_ip_i\mathcal{Z}_\beta(\phi_i)$.
- `comp:faithful` [CONCLUSION / MAPPED] The roof extension attains the stabilizer value iff $\rho$ decomposes into pure stabilizer states, i.e. iff $\rho$ is free.
  - residual: The iff argument uses maximality of the SPF on stabilizer states at a single $\beta$; whether the argument is uniform in $\beta$, and whether the supremum is attained, is not discussed.
- `comp:channel` [DEFINITION / RESIDUAL] $\mathcal{Z}_\beta(\mathcal{N})=\mathcal{Z}_\beta(\tilde J^{\mathcal{N}}_{AB})$.
  - residual: No properties of the channel SPF (invariance, faithfulness, composition) are established.
- `comp:open` [LIMITATION / RESIDUAL] Monotonicity of the extended stabilizer work is left for future work.
  - residual: Explicit deferral; no partial result is offered.

**Math target `m31`** (EXACT), covering `comp:mixed`, `comp:faithful`.

- conclusion: $\mathcal{Z}_{\beta}(\rho):=\sup_{\{p_i,\phi_i\}}\sum_{i\in[m]}p_i\,\mathcal{Z}_{\beta}(\phi_i)$, and $\mathcal{Z}_{\beta}(\rho)=\mathcal{Z}_{\beta}({\rm STAB})$ iff $\rho$ admits a decomposition into pure stabilizer states.
- quantifier: FORALL \rho in $\mathcal{D}(\mathcal{H}_A)$
- quantifier: FORALL \beta in range not stated
- quantifier: EXISTS \{p_i,\phi_i\} in pure-state decompositions of $\rho$ attaining the supremum (attainment is not discussed)
- assumption (SOURCE_EXPLICIT): $\mathcal{Z}_\beta$ on pure states is maximized exactly on ${\rm STAB}$ (Theorem, state-independent bounds)
- normalization: the Choi matrix is normalized, i.e. $\tilde J=({\rm id}\otimes\mathcal{N})(\Phi^+)$ with $\Phi^+$ normalized

**Open items recorded against this claim.**

- [UNPROVED_LEMMA · mathematical_correctness] Monotonicity of the mixed-state and channel stabilizer work is stated as an open problem by the authors themselves.
  - what could settle it: Future work identified in the source; the PTM characterization is proposed there as a starting point.

Records: `claim:opus5-2608.14798v1/c31`, `map:opus5-2608.14798v1/c31`, `math:opus5-2608.14798v1/m31`.

## c32 — Framing claims of the abstract and discussion

*Abstract, Sec. VII · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The abstract and discussion assert as a package: the stabilizer work is a faithful, subadditive magic monotone at every temperature; both the SPF and the stabilizer work are efficiently estimable via Bell sampling; the zero-temperature limit is a third-law statement recovering the stabilizer nullity and the high-temperature limit recovers the 2-stabilizer Renyi entropy; the full temperature profile is a magic spectrum carrying strictly more information than either endpoint; and the ensemble catalogue (Haar, $\nu$-compressible, pseudomagic) with concentration guarantees makes the SPF a classifier of magic classes. The paper also discloses that Claude was used to refine the Introduction and Discussion.

**System.** the framework as a whole

**Comparison baseline.** existing magic measures (SREs, nullity, RoM, extent, T-count)

**Stated conditions.**

- (SOURCE_EXPLICIT) the whole development is for pure states unless otherwise stated

**Components and their accounting.**

- `comp:monotone` [CONCLUSION / RESIDUAL] 'a faithful, subadditive magic monotone at every temperature'.
  - residual: Not established for the declared free class; see the recorded monotonicity gap.
- `comp:efficient` [CONCLUSION / RESIDUAL] 'efficiently estimable via Bell sampling', stated for both objects without qualification.
  - residual: Established only for an additive error on the normalized truncated SPF, above a truncation floor that scales as $2^n$; no error-propagation statement reaches $\mathcal{W}_\beta$.
- `comp:limits` [CONCLUSION / RESIDUAL] Third-law reading of the $\beta\to\infty$ limit and $M_2$ recovery at $\beta\to0$.
  - residual: The two limits are asserted without derivation or error terms anywhere in the paper, and the $\beta\to\infty$ SPF limit itself is stated inconsistently in two places.
- `comp:strictly-more` [CONCLUSION / RESIDUAL] 'the full temperature profile ... carrying strictly more information than either endpoint'.
  - residual: 'Strictly more information' is not defined; no information measure, sufficiency statement, or separating example is given.
- `comp:classifier` [CONCLUSION / RESIDUAL] Exact ensemble formulas plus concentration make the SPF a classifier of magic classes.
  - residual: 'Classifier' summarizes the ensemble formulas plus concentration; the executable content is Algorithms 1-3, which branch on asymptotic predicates and assume oracle access.
- `comp:ai` [ATTRIBUTION / NON_CLAIM] Disclosure that Claude was used to refine the Introduction and Discussion, including surfacing the Li-Haldane entanglement-spectrum connection.
  - residual: Scope of the AI assistance ('refine and sharpen') is described qualitatively; no statement about mathematical content is made or excluded.

**Math target.** None. This claim was not forced into a MathClaim; its meaning is retained in the claim record and, where applicable, in a SemanticContext.

**Open items recorded against this claim.**

- [ALIGNMENT_GAP · source_fidelity] Three abstract-level assertions (magic monotone at every temperature; efficiently estimable; strictly more information) are stronger than the corresponding in-text results.
  - what could settle it: Either proofs closing the three gaps, or restatement of the abstract; each gap is recorded separately against the section where it arises.

Records: `claim:opus5-2608.14798v1/c32`, `map:opus5-2608.14798v1/c32`.

## c33 — What the SPF discards

*Sec. III C · modality ASSERTED · coverage PARTIAL*

**What the authors said.** The SPF does not retain the full labelled Pauli spectrum; instead it packages the spectrum's Clifford-invariant EVEN statistics into an analytic object, thereby capturing the stabilizer-relevant information accessible through Pauli moments.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the full signed, labelled Pauli spectrum ${\rm Spec}(\psi)$ of Definition (Pauli Spectrum)

**Stated conditions.**

- (SOURCE_RECONSTRUCTED) only even moments enter, since $\cosh$ is an even function of $\beta x$

**Components and their accounting.**

- `comp:lossy` [LIMITATION / MAPPED] The map $\psi\mapsto\mathcal{Z}_\bullet(\psi)$ is explicitly lossy: labels, signs and odd statistics are not recoverable.
- `comp:sufficient` [ASSUMPTION / RESIDUAL] What survives is asserted to be 'the stabilizer-relevant information accessible through Pauli moments'.
  - residual: 'Stabilizer-relevant information' is not defined, and no statement identifies what magic-relevant content, if any, is lost with the discarded labels and signs. This matters for the abstract's 'strictly more information' claim, which compares the SPF profile with its two endpoint measures rather than with the spectrum itself.

**Math target `m33`** (EXACT), covering `comp:lossy`.

- conclusion: $\mathcal{Z}_{\beta}(\psi)$ depends on ${\rm Spec}(\psi)$ only through the even moments $\{\sum_{x}x^{2k}\}_{k\geq0}$; in particular any two states whose Pauli spectra agree as multisets up to sign and relabelling have identical SPF at every $\beta$.
- quantifier: FORALL \beta in $\mathbb{R}$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_RECONSTRUCTED): $\cosh$ is even, so $\mathcal{Z}_\beta$ is invariant under independent sign flips of spectrum entries
- assumption (SOURCE_RECONSTRUCTED): the sum over ${\rm Spec}$ is symmetric, so it is invariant under relabelling
- normalization: the converse (that the even moments determine the SPF) is immediate; the paper does not state whether the even moments determine the magic-relevant content

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · semantic_applicability] The SPF is stated to be a lossy compression of the Pauli spectrum, but no characterization is given of the equivalence classes it induces or of what magic-relevant content is lost.
  - what could settle it: An explicit statement of which pairs of states the SPF profile identifies; this also bears on the 'magic spectrum carries strictly more information' claim.

Records: `claim:opus5-2608.14798v1/c33`, `map:opus5-2608.14798v1/c33`, `math:opus5-2608.14798v1/m33`.

## c34 — Integer SREs recoverable from the SPF by differentiation

*Supplemental Material · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Proposition (Stab Renyi from SPF): for integer $\alpha$, $M_\alpha(\psi)=\lim_{\beta\to0}\frac{1}{1-\alpha}\log\left(\frac{1}{d_n}\frac{\partial^{2\alpha}}{\partial\beta^{2\alpha}}e^{\beta}\mathcal{Z}_\beta(\psi)\right)$, because $\sum_{x}x^{2m}=\partial^{2m}_\beta\,e^{\beta}\mathcal{Z}_\beta(\psi)|_{\beta\to0}$; the exchange of limits is justified by positivity of the SPF derivatives.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the direct definition of $M_\alpha$ from the Pauli-spectrum distribution $\Xi(\psi)$

**Stated conditions.**

- (SOURCE_EXPLICIT) $\alpha\in\mathbb{N}$
- (SOURCE_RECONSTRUCTED) $\alpha=1$ is excluded by the prefactor $1/(1-\alpha)$; the source does not say so

**Components and their accounting.**

- `comp:formula` [CONCLUSION / MAPPED] Differentiation formula recovering integer-index SREs from the SPF.
  - residual: The admissible integer range is not stated; $\alpha=1$ makes the prefactor singular.
- `comp:moments` [EVIDENCE / RESIDUAL] $\sum_x x^{2m}=\partial^{2m}_\beta e^{\beta}\mathcal{Z}_\beta|_{\beta\to0}$, i.e. $e^{\beta}\mathcal{Z}_\beta$ is the moment generating object.
- `comp:limits` [ASSUMPTION / RESIDUAL] 'The exchange of the limits comes because the positivity of the SPF derivatives.'
  - residual: Positivity of derivatives is not by itself a justification for exchanging a limit with differentiation; the actual justification (the series is entire) is not given.

**Math target `m34`** (EXACT), covering `comp:formula`.

- conclusion: $M_{\alpha}(\psi)=\lim_{\beta\to0}\frac{1}{1-\alpha}\log\left(\frac{1}{d_{n}}\frac{\partial^{2\alpha}}{\partial\beta^{2\alpha}}e^{\beta}\mathcal{Z}_{\beta}(\psi)\right)$ for $\alpha\in\mathbb{N}$.
- quantifier: FORALL \alpha in $\mathbb{N}$ as stated; $\alpha=1$ is singular and $\alpha=0$ is not covered by the displayed prefactor
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_RECONSTRUCTED): $e^{\beta}\mathcal{Z}_\beta(\psi)=\sum_{x\in{\rm Spec}(\psi)}\cosh(\beta x)$ is entire in $\beta$, so term-by-term differentiation is legitimate
- assumption (SOURCE_EXPLICIT): the SPF derivatives are positive, which the source offers as the justification for exchanging limit and differentiation
- normalization: $\log$ base 2 as elsewhere; the $1/d_n$ inside the logarithm matches the normalization in the definition of $M_\alpha$

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · mathematical_correctness] The limit-exchange justification offered for Proposition (Stab Renyi from SPF) is positivity of derivatives, which does not establish the exchange.
  - what could settle it: Replace with the analyticity argument, or state the interchange theorem being used.

Records: `claim:opus5-2608.14798v1/c34`, `map:opus5-2608.14798v1/c34`, `math:opus5-2608.14798v1/m34`.

## c35 — Unfiltered stabilizer work and why the core SPF is used

*Supplemental Material · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Defining a stabilizer-work-like function from the unfiltered SPF instead of the core SPF gives the 'unfiltered stabilizer work' $\mathfrak{u}_\beta$, which shares faithfulness, Clifford invariance and sub-additivity, but which 'does not always decrease under partial trace for all values of $\beta$'. Sub-additivity of $\mathfrak{u}_\beta$ is proved through a supporting theorem: for non-increasing vectors $a,b$ with $a_0=d_A^2$, $b_0=d_B^2$, $a_1=d_A$, $b_1=d_B$, $a_{k>1}\leq a_1$, $b_{k>1}\leq b_1$ and $w_k=x^{2k}/(2k)!$ summing to $c=\cosh x$, $\frac{\sum_kw_ka_kb_k}{(\sum_kw_ka_k)(\sum_kw_kb_k)}\geq\frac{d_Ad_B+c-1}{(d_A+c-1)(d_B+c-1)}$.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the stabilizer work $\mathcal{W}_\beta$ built from the core SPF

**Stated conditions.**

- (SOURCE_EXPLICIT) the sub-additivity statement is for separable pure states across an $A|B$ cut
- (SOURCE_EXPLICIT) the supporting theorem assumes $a,b$ non-increasing with the stated first two entries

**Components and their accounting.**

- `comp:shared` [CONCLUSION / RESIDUAL] $\mathfrak{u}_\beta$ is faithful, Clifford invariant and sub-additive.
  - residual: Faithfulness and Clifford invariance are called straightforward and not proved.
- `comp:fails` [LIMITATION / RESIDUAL] $\mathfrak{u}_\beta$ does not always decrease under partial trace for all $\beta$; this is the stated reason for filtering.
  - residual: The failure of monotonicity under partial trace is asserted without an explicit $\beta$ and state for which it fails, so the motivation for the core SPF rests on a statement the reader cannot check from the text.
- `comp:theorem` [EVIDENCE / MAPPED] Supporting inequality on reweighted moment vectors, proved via the monotone reweighting lemma applied twice.

**Math target `m35`** (EXACT), covering `comp:theorem`.

- conclusion: Under the stated hypotheses, $\dfrac{\sum_k w_k a_k b_k}{(\sum_k w_k a_k)(\sum_k w_k b_k)}\ \geq\ \dfrac{d_Ad_B+c-1}{(d_A+c-1)(d_B+c-1)}$ with $c=\cosh x$.
- quantifier: FORALL x in $\mathbb{R}$
- quantifier: FORALL a,b in non-increasing non-negative sequences with $a_0=d_A^2$, $a_1=d_A$, $a_{k>1}\leq a_1$ and the analogous conditions on $b$
- assumption (SOURCE_EXPLICIT): the monotone reweighting lemma, applied with the comparison vectors $a'=(d_A^2,d_A,d_A,\dots)$ and $b'=(d_B^2,d_B,d_B,\dots)$
- assumption (SOURCE_EXPLICIT): $a_k/a'_k$ is non-increasing in $k$, asserted without reason in the source
- normalization: the right-hand side is the same ratio evaluated on the stabilizer vectors $a',b'$, i.e. the free-state reference

**Open items recorded against this claim.**

- [MISSING_SOURCE · mathematical_correctness] The claim that the unfiltered stabilizer work can increase under partial trace, which is the stated justification for using the core SPF throughout, is given without a witness.
  - what could settle it: An explicit $\beta$, state and cut exhibiting the failure. This run did not search for one.

Records: `claim:opus5-2608.14798v1/c35`, `map:opus5-2608.14798v1/c35`, `math:opus5-2608.14798v1/m35`.

## c36 — Variational lower bound on the SPF

*Supplemental Material · modality ASSERTED · coverage PARTIAL*

**What the authors said.** Lemma (variational SPF lower bound): for $\beta\geq0$ and a control parameter $\epsilon\in[0,1)$, $\mathcal{Z}_\beta(\psi)\geq e^{-\beta}d_n^2[\cosh(|\beta|\epsilon)(1-f_\epsilon(\psi))+f_\epsilon(\psi)]$ with $f_\epsilon(\psi)=\frac{1-2^{-M_2(\psi)-n}}{1-\epsilon^4}$, the tightest bound following by optimizing over $\epsilon$. The supplement also records that the ensemble-averaged stabilizer Hamiltonian for any 1-design is $\mathbb{I}^{\otimes2}-s\ket{\Phi^+}\bra{\Phi^+}$ and warns explicitly that $\mathcal{Z}_\beta({\rm Haar}_n)\neq\tr\,e^{-\beta\mathbb{E}[\hat H]}$.

**System.** $n$-qubit pure states, $\mathcal{H}_n\cong(\mathbb{C}^2)^{\otimes n}$, $d_n=2^n$, finite $n$

**Comparison baseline.** the non-variational state-dependent lower bound of Theorem (SPF state-dependent bounds)

**Stated conditions.**

- (SOURCE_EXPLICIT) $\beta\geq0$
- (SOURCE_EXPLICIT) $\epsilon\in[0,1)$
- (SOURCE_EXPLICIT) the proof uses $\mathbb{E}_{x\sim d\mu_\psi}[x^4]=2^{-M_2(\psi)-n}$

**Components and their accounting.**

- `comp:bound` [CONCLUSION / MAPPED] Family of lower bounds indexed by $\epsilon$, obtained by splitting the Pauli-spectrum density at $|x|=\epsilon$ and applying Markov's inequality.
  - residual: No range of $\epsilon$ is excluded even though $f_\epsilon\to\infty$ as $\epsilon\to1$, and the bound is stated with $\cosh(|\beta|\epsilon)$ while the theorem is restricted to $\beta\geq0$.
- `comp:nojensen` [LIMITATION / RESIDUAL] The ensemble-averaged SPF is not the partition function of the ensemble-averaged Hamiltonian; the supplement states this explicitly and says the latter gives only coarse-grained features.
  - residual: The warning is recorded but never reconnected to the main-text use of ensemble-averaged SPFs as if they characterized individual states.

**Math target `m36`** (EXACT), covering `comp:bound`.

- conclusion: $\mathcal{Z}_{\beta}(\psi)\geq\sup_{\epsilon\in[0,1)}e^{-\beta}d_n^{2}\left[\cosh(|\beta|\epsilon)(1-f_{\epsilon}(\psi))+f_{\epsilon}(\psi)\right]$, $f_{\epsilon}(\psi)=\dfrac{1-2^{-M_{2}(\psi)-n}}{1-\epsilon^{4}}$.
- quantifier: FORALL \beta in $[0,\infty)$
- quantifier: FORALL \epsilon in $[0,1)$
- quantifier: FORALL \psi in pure states in $\mathcal{H}_n$
- assumption (SOURCE_EXPLICIT): $\mathcal{Z}_\beta(\psi)=e^{-\beta}d_n^2\,\mathbb{E}_{x\sim d\mu_\psi}[\cosh(\beta x)]$, the Pauli-density form of the SPF
- assumption (SOURCE_EXPLICIT): Markov's inequality applied to $1-x^4$ under $d\mu_\psi$
- assumption (SOURCE_EXPLICIT): $p\mapsto\cosh(\beta\epsilon)(1-p)+p$ is decreasing in $p$, so replacing $p_\epsilon$ by its upper bound preserves the lower bound
- normalization: the bound is on the unnormalized SPF; $f_\epsilon$ can exceed 1 for $\epsilon$ close to 1, in which case the bracket is weaker than the trivial bound and the source does not restrict $\epsilon$ to exclude this

**Open items recorded against this claim.**

- [SCOPE_AMBIGUITY · mathematical_correctness] The variational lower bound does not restrict $\epsilon$ away from the region where $f_\epsilon(\psi)>1$ and the bracket stops being informative.
  - what could settle it: An explicit admissible range for $\epsilon$, or a statement that the supremum is attained inside the useful region.

Records: `claim:opus5-2608.14798v1/c36`, `map:opus5-2608.14798v1/c36`, `math:opus5-2608.14798v1/m36`.

