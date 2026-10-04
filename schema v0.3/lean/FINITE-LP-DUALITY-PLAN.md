# Finite normalized ℓ₁ strong duality: local construction plan

**Conclusion.** The missing strong-duality bridge can be proved from the current finite-atom minimum and mathlib's Hahn–Banach theorem. It need not be assumed. The shortest route identified in this static review is the **norm on the coefficient space modulo the reconstruction kernel**, followed by a norming linear functional. This supplies an attained dual maximum, including degenerate atom families, without assuming the target clique formula or that the atoms span the ambient space.

This document is a construction plan, not an implemented or compiled theorem. No Lean execution, tests, network lookup, or modification of published modules was performed for this review.

## Scope and pinned sources

The inspected local mathlib is `formal/AgtXIvRootMath/.lake/packages/mathlib`, observed Git revision `c1e30e172c8fda21e6776bf1f10351e882ee31b9`; its toolchain file specifies `leanprover/lean4:v4.30.0-rc2`. `formal/AgtXIvVarela/lake-manifest.json` uses that same package directory and revision. These observations locate source declarations; they do not attest that a new importing module will compile against the cached objects.

The paper's primal is `Stabilizerness/arXiv-2607.26154v1/draft.tex:122–130`. Its exact dual is at lines 150–155. The relaxed version invokes strong LP duality at lines 608–625; the final query is at lines 270–282. The general result below provides the optimization theorem used at that step. It does not prove the paper's proposed stabilizer/context correspondence, sign-domain collapse, or perfect-graph argument.

Local searches found Hahn–Banach and geometric Farkas declarations, but no ready-made finite LP strong-duality interface. In particular, `Mathlib/Analysis/Convex/Cone/Basic.lean:30–36` still lists defining primal/dual cone programs and proving their strong duality as future work. This is a scoped local finding, not a claim about every Lean library.

## Proposed general theorem

For finite `ι`, a real normed vector space `V`, atoms `a : ι → V`, target `b : V`, and only the existing feasibility premise

```text
hFeasible : ∃ x : ι → ℝ, AgtXIv.RoM.SignedDecomp a b x,
```

prove the following contract (proposed declaration name, not an existing declaration):

```text
finiteRoM_isGreatest_dual :
  IsGreatest
    {z : ℝ | ∃ ℓ : V →ₗ[ℝ] ℝ,
      (∀ i, |ℓ (a i)| ≤ 1) ∧ z = ℓ b}
    (AgtXIv.RoM.finiteRoM a b hFeasible)
```

`IsGreatest` asserts both attainment and the upper-bound property. It is stronger than a statement about equal suprema. The functional is algebraically linear on `V`; continuity on the whole ambient space is unnecessary for this finite optimization. The application has `V = ℝ × (Fin m → ℝ)`, where coordinate functionals are continuous anyway.

Neither linear independence nor surjectivity of reconstruction is required. An empty atom type is allowed when feasible, which forces `b = 0`. The proof below also handles zero targets without dividing by the optimum.

## Recommended proof route

1. **Expose the coefficient norm and reconstruction map.** Use `X := PiLp 1 (fun _ : ι => ℝ)`, and define a linear map `T : X →ₗ[ℝ] V` by `T x = reconstruct a (WithLp.ofLp x)`. Linearity is the finite-sum identity. Prove `‖WithLp.toLp 1 x‖ = l1Cost x` using `PiLp.norm_eq_of_L1` and `Real.norm_eq_abs`. The ordinary function space `ι → ℝ` has the supremum norm in mathlib: using that norm directly would prove the wrong optimization theorem.

2. **Identify the quotient norm with the attained minimum.** Set `K := LinearMap.ker T`, `Q := X ⧸ K`, take the existing `x* := optimalCoeffs a b hFeasible`, and let `q := Submodule.Quotient.mk (WithLp.toLp 1 x*)`. Equality of quotient representatives is exactly equality of their reconstruction; use `Submodule.Quotient.eq` and linearity of `T`.

   Let `r := finiteRoM a b hFeasible`. `Submodule.Quotient.norm_mk_le` immediately gives `‖q‖ ≤ r`. For every `ε > 0`, `Submodule.Quotient.norm_mk_lt q hε` supplies a representative `u` with `‖u‖ < ‖q‖ + ε`. It reconstructs `b`, so existing minimizer optimality gives `r ≤ ‖u‖`. Consequently `r ≤ ‖q‖` by the positive-ε argument, and `‖q‖ = r`.

   This avoids a new proof of primal attainment, unfolding a conditional infimum, or assuming dual attainment. The quotient has the existing seminormed-group and normed-space instances; the chosen Hahn–Banach lemma works for a seminormed space, so no additional closed-kernel proof is needed for this route.

3. **Construct an attaining dual functional.** Apply `exists_dual_vector'' ℝ q` to obtain `g : StrongDual ℝ Q`, `‖g‖ ≤ 1`, and `g q = ‖q‖`. Compose its underlying linear map with `(T.quotKerEquivRange).symm` to get a linear functional on `LinearMap.range T`. Extend it to `ℓ : V →ₗ[ℝ] ℝ` using `LinearMap.exists_extend`. The extension agrees on the entire range, so it preserves both the target value and every atom value.

   For `e_i := PiLp.single 1 i (1 : ℝ)`, prove `T e_i = a i`. Then

   ```text
   |ℓ (a i)| = |g (mk e_i)|
              ≤ ‖g‖ * ‖mk e_i‖
              ≤ ‖e_i‖ = 1.
   ℓ b = g q = ‖q‖ = r.
   ```

   The bound uses `ContinuousLinearMap.le_opNorm`, the quotient norm bound, and `PiLp.norm_single`. In particular, the construction does not require an invertible atom matrix. `exists_dual_vector''` handles `q = 0` itself.

4. **Prove weak duality and assemble `IsGreatest`.** For any feasible coefficients `x` and any functional satisfying the atom bounds, linearity and the triangle inequality give

   ```text
   ℓ b = ∑ i, x i * ℓ (a i)
       ≤ ∑ i, |x i| * |ℓ (a i)|
       ≤ ∑ i, |x i| = l1Cost x.
   ```

   Apply this to `optimalCoeffs` for the upper-bound half. The functional from step 3 gives membership of `r` in the set of dual objective values. These are the two components of `IsGreatest`.

The main new proof obligations are therefore the `PiLp` reconstruction wrapper, quotient feasibility/norm equality, the norming-functional transport, and the finite-sum weak-duality estimate. None is the desired closed-form equality in disguise.

## Exact reusable declarations

The mathlib paths in this table are relative to the pinned package root above. Names and signatures were read from source, not checked with Lean in this review.

| Existing declaration | Source | Role |
| --- | --- | --- |
| `AgtXIv.RoM.exists_l1Minimizer` | `formal/AgtXIvRootMath/AgtXIvRootMath/FiniteAtomAttainment.lean:36` | Existing primal attainment under feasibility. |
| `AgtXIv.RoM.optimalCoeffs_isL1Minimizer` | `formal/AgtXIvRootMath/AgtXIvRootMath/FiniteAtomTotalRoM.lean:30` | Feasibility and cost comparison for the chosen minimizer. |
| `AgtXIv.RoM.finiteRoM` | `formal/AgtXIvRootMath/AgtXIvRootMath/FiniteAtomTotalRoM.lean:39` | Existing value; do not redefine it. |
| `WithLp.linearEquiv`, `WithLp.ofLp_toLp`, `WithLp.toLp_ofLp` | `Mathlib/Analysis/Normed/Lp/WithLp.lean:237,101,102` | Preserve the coefficient functions while changing their norm. |
| `PiLp.norm_eq_of_L1` | `Mathlib/Analysis/Normed/Lp/PiLp.lean:753` | `‖x‖ = ∑ i, ‖x i‖` for `PiLp 1`. |
| `PiLp.single`, `PiLp.ofLp_single`, `PiLp.norm_single` | Same file, lines 149,152,1043 | Unit coefficient vectors and norm one. |
| `Submodule.Quotient.eq` | `Mathlib/LinearAlgebra/Quotient/Defs.lean:82` | `mk x = mk y ↔ x - y ∈ K`. |
| `Submodule.Quotient.norm_mk_le` | `Mathlib/Analysis/Normed/Group/Quotient.lean:442` | `‖mk x‖ ≤ ‖x‖`. |
| `Submodule.Quotient.norm_mk_lt` | Same file, line 438 | For `ε > 0`, a representative within `ε` of the quotient norm. |
| `exists_dual_vector''` | `Mathlib/Analysis/Normed/Module/HahnBanach.lean:166` | `∃ g : StrongDual ℝ Q, ‖g‖ ≤ 1 ∧ g q = ‖q‖`; works for seminormed `Q`. |
| `ContinuousLinearMap.le_opNorm` | `Mathlib/Analysis/Normed/Operator/Basic.lean:239` | `‖g q‖ ≤ ‖g‖ * ‖q‖`. |
| `LinearMap.quotKerEquivRange`, `LinearMap.quotKerEquivRange_apply_mk`, `LinearMap.quotKerEquivRange_symm_apply_image` | `Mathlib/LinearAlgebra/Isomorphisms.lean:39,50,60` | Move from the quotient to the reconstruction range. |
| `LinearMap.exists_extend` | `Mathlib/LinearAlgebra/Basis/VectorSpace.lean:288` | For `f : p →ₗ[ℝ] ℝ`, obtain `ℓ` with `ℓ.comp p.subtype = f`. |

Use the current import `Mathlib.Analysis.Normed.Module.HahnBanach`. The old `Mathlib.Analysis.NormedSpace.HahnBanach.Extension` path is a deprecated compatibility module in this checkout; its source is not the theorem implementation.

## Normalized application and boundary of the result

Apply the general theorem to `AgtXIv.ReducedRoM.augmentedAtom a` and `(1,b)`. For any ambient linear functional, set

```text
μ := ℓ (1, 0)
y i := ℓ (0, Pi.single i (1 : ℝ)).
```

Finite coordinate expansion proves `ℓ (t,v) = t * μ + ∑ i, v i * y i`. Conversely that formula defines a linear functional for every `(μ,y)`. Thus the general theorem becomes precisely

```text
IsGreatest
  {z | ∃ (y : Fin m → ℝ) (μ : ℝ),
    (∀ j, |μ + ∑ i, a j i * y i| ≤ 1) ∧
    z = μ + ∑ i, b i * y i}
  (finiteRoM (augmentedAtom a) (1,b) hFeasible).
```

For the actual query input, `augmented_projected_feasible W ρ` already supplies feasibility and `reducedRoM` is definitionally this primal. This gives an unconditional dual representation over actual projected frame atoms. To replace them by a different finite generator family, use the already released `normalized_minimum_eq_of_mutual_convex_atoms` or `reducedRoM_eq_of_mutual_convex_generators`. The bidirectional probability maps must still be supplied for the particular context/vertex family.

After that bridge, the remaining work is still substantial: source-aligned context generators; phase-aware sign admissibility and no-active-dependency collapse; evaluation of the graph-constrained dual using perfectness; then the clique bound and saturation. This theorem would discharge **general LP strong duality**, not any of those independent obligations or final-query source acceptance.

## Alternatives inspected

`exists_extension_of_le_sublinear` (`Mathlib/Analysis/Convex/Cone/Extension.lean:159`) directly extends a partial linear functional dominated by a positively homogeneous, subadditive function. Together with `LinearPMap.mkSpanSingleton` and `LinearMap.exists_extend`, it yields another valid route: define the finite minimum on the reconstruction range, prove its zero/negation/homogeneity/subadditivity properties, and support it at the target. This replaces quotient/norm wrappers with several fresh properties of the minimum and a zero-target case; the quotient route reuses more existing infrastructure.

`gauge_add_le`, `gauge_smul_of_nonneg`, `gauge_neg`, and `gaugeSeminorm` in `Mathlib/Analysis/Convex/Gauge.lean` support a symmetric atomic-body approach. It additionally requires proving absorbency on the reconstruction span and identifying the gauge with the existing minimum. The ambient atom hull need not be absorbent, so that hypothesis cannot be silently supplied on all of `V`.

`ProperCone.hyperplane_separation_point` (`Mathlib/Analysis/Convex/Cone/Dual.lean:132`) is geometric Farkas, and `geometric_hahn_banach_closed_point` (`Mathlib/Analysis/LocallyConvex/Separation.lean:230`) gives strict separation of a point outside a closed convex set. Either supports a longer epigraph/polyhedral route. A minimizing boundary point is not outside the closed feasible epigraph, so directly applying strict separation there is invalid; an attainment or supporting-functional argument remains necessary. The quotient norming theorem already supplies that argument.
