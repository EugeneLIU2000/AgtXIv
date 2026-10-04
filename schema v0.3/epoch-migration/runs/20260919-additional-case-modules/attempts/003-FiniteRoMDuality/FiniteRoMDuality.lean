import ReducedRoMSemantics
import Mathlib.Analysis.Normed.Lp.PiLp
import Mathlib.Analysis.Normed.Group.Quotient
import Mathlib.Analysis.Normed.Module.HahnBanach
import Mathlib.LinearAlgebra.Isomorphisms
import Mathlib.LinearAlgebra.Basis.VectorSpace

/-!
Strong duality for the actual attained finite-atom l1 minimum. The coefficient
space has its l1 norm and is quotiented by the reconstruction kernel. A norming
Hahn--Banach functional gives an attained dual optimizer. Normalized reduced
RoM uses the previously defined augmented atoms, not a desired closed formula.

Source use: arXiv:2607.26154v1 draft.tex:122--130 (normalized primal), 150--155
(exact LP dual), and 608--625 (relaxed LP dual). Context/vertex identification,
Pauli sign admissibility, perfect-graph evaluation, and saturation are separate
obligations. This module uses the original cached Lean 4.30.0-rc2 epoch.
-/

namespace AgtXIv.RoM

open scoped BigOperators

noncomputable section

variable {ι V : Type*} [Fintype ι]
variable [NormedAddCommGroup V] [NormedSpace ℝ V]

abbrev L1Coeffs (ι : Type*) := PiLp 1 (fun _ : ι => ℝ)

/-- Reconstruction on coefficients equipped with the correct l1 norm. -/
def reconstructL1 (atom : ι → V) : L1Coeffs ι →ₗ[ℝ] V where
  toFun x := reconstruct atom (WithLp.ofLp x)
  map_add' x y := by simp [reconstruct, add_smul, Finset.sum_add_distrib]
  map_smul' c x := by simp [reconstruct, smul_smul, Finset.smul_sum]

theorem reconstructL1_toLp (atom : ι → V) (x : ι → ℝ) :
    reconstructL1 atom (WithLp.toLp 1 x) = reconstruct atom x := rfl

theorem norm_toLp_eq_l1Cost (x : ι → ℝ) :
    ‖WithLp.toLp 1 x‖ = l1Cost x := by
  simp [PiLp.norm_eq_of_L1, l1Cost, Real.norm_eq_abs]

theorem reconstructL1_single [DecidableEq ι] (atom : ι → V) (i : ι) :
    reconstructL1 atom (PiLp.single 1 i (1 : ℝ)) = atom i := by
  classical
  simp [reconstructL1, reconstruct]

theorem quotient_eq_iff_reconstructL1 (atom : ι → V) (x y : L1Coeffs ι) :
    (Submodule.Quotient.mk x : L1Coeffs ι ⧸ LinearMap.ker (reconstructL1 atom)) =
      Submodule.Quotient.mk y ↔ reconstructL1 atom x = reconstructL1 atom y := by
  rw [Submodule.Quotient.eq]
  change reconstructL1 atom (x - y) = 0 ↔ _
  rw [map_sub, sub_eq_zero]

/-- Every representative of a feasible reconstruction class has quotient norm
equal to the existing attained finite robustness minimum. -/
theorem quotient_norm_eq_finiteRoM (atom : ι → V) (b : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom b x)
    (x : ι → ℝ) (hx : SignedDecomp atom b x) :
    ‖(Submodule.Quotient.mk (WithLp.toLp 1 x) :
      L1Coeffs ι ⧸ LinearMap.ker (reconstructL1 atom))‖ = finiteRoM atom b hFeasible := by
  let q : L1Coeffs ι ⧸ LinearMap.ker (reconstructL1 atom) :=
    Submodule.Quotient.mk (WithLp.toLp 1 x)
  have hMin := optimalCoeffs_isL1Minimizer atom b hFeasible
  have hEq : q = Submodule.Quotient.mk (WithLp.toLp 1 (optimalCoeffs atom b hFeasible)) := by
    apply (quotient_eq_iff_reconstructL1 atom _ _).2
    exact hx.trans hMin.1.symm
  apply le_antisymm
  · change ‖q‖ ≤ _
    rw [hEq]
    exact (Submodule.Quotient.norm_mk_le _ _).trans_eq
      (norm_toLp_eq_l1Cost (optimalCoeffs atom b hFeasible))
  · change finiteRoM atom b hFeasible ≤ ‖q‖
    apply le_of_forall_pos_le_add
    intro ε hε
    obtain ⟨u, hu, hnorm⟩ := Submodule.Quotient.norm_mk_lt q hε
    have huDecomp : SignedDecomp atom b (WithLp.ofLp u) := by
      have hTu := (quotient_eq_iff_reconstructL1 atom u (WithLp.toLp 1 x)).1 hu
      exact hTu.trans hx
    have hCost := hMin.2 (WithLp.ofLp u) huDecomp
    have hn : l1Cost (WithLp.ofLp u) = ‖u‖ := by
      simpa using (norm_toLp_eq_l1Cost (WithLp.ofLp u)).symm
    exact (hCost.trans_eq hn).trans hnorm.le

/-- Weak duality for any given feasible coefficients. -/
theorem dual_le_l1Cost (atom : ι → V) (b : V) (x : ι → ℝ)
    (hx : SignedDecomp atom b x) (ℓ : V →ₗ[ℝ] ℝ)
    (hAtom : ∀ i, |ℓ (atom i)| ≤ 1) : ℓ b ≤ l1Cost x := by
  calc
    ℓ b = ∑ i, x i * ℓ (atom i) := by rw [← hx]; simp [reconstruct]
    _ ≤ ∑ i, |x i| := by
      apply Finset.sum_le_sum
      intro i _
      calc
        x i * ℓ (atom i) ≤ |x i * ℓ (atom i)| := le_abs_self _
        _ = |x i| * |ℓ (atom i)| := abs_mul _ _
        _ ≤ |x i| * 1 := mul_le_mul_of_nonneg_left (hAtom i) (abs_nonneg _)
        _ = |x i| := mul_one _
    _ = l1Cost x := rfl

/-- Hahn--Banach supplies a genuine dual optimizer; no duality or final-value
hypothesis is assumed, and the atom family need not span the ambient space. -/
theorem exists_finiteRoM_dual_optimizer (atom : ι → V) (b : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom b x) :
    ∃ ℓ : V →ₗ[ℝ] ℝ, (∀ i, |ℓ (atom i)| ≤ 1) ∧
      ℓ b = finiteRoM atom b hFeasible := by
  classical
  let T := reconstructL1 atom
  let x := optimalCoeffs atom b hFeasible
  have hx : SignedDecomp atom b x := (optimalCoeffs_isL1Minimizer atom b hFeasible).1
  let q : L1Coeffs ι ⧸ LinearMap.ker T := Submodule.Quotient.mk (WithLp.toLp 1 x)
  obtain ⟨g, hgNorm, hgValue⟩ := exists_dual_vector'' ℝ q
  let f : LinearMap.range T →ₗ[ℝ] ℝ :=
    g.toLinearMap.comp T.quotKerEquivRange.symm.toLinearMap
  obtain ⟨ℓ, hExtend⟩ := LinearMap.exists_extend f
  have hTransport (u : L1Coeffs ι) : ℓ (T u) = g (Submodule.Quotient.mk u) := by
    have he := LinearMap.congr_fun hExtend ⟨T u, LinearMap.mem_range_self T u⟩
    simpa [f, LinearMap.quotKerEquivRange_symm_apply_image] using he
  refine ⟨ℓ, ?_, ?_⟩
  · intro i
    have he : T (PiLp.single 1 i (1 : ℝ)) = atom i := reconstructL1_single atom i
    rw [← he, hTransport]
    change ‖g (Submodule.Quotient.mk (PiLp.single 1 i (1 : ℝ)))‖ ≤ 1
    calc
      _ ≤ ‖g‖ * ‖(Submodule.Quotient.mk (PiLp.single 1 i (1 : ℝ)) :
          L1Coeffs ι ⧸ LinearMap.ker T)‖ := g.le_opNorm _
      _ ≤ 1 * ‖(Submodule.Quotient.mk (PiLp.single 1 i (1 : ℝ)) :
          L1Coeffs ι ⧸ LinearMap.ker T)‖ := mul_le_mul_of_nonneg_right hgNorm (norm_nonneg _)
      _ ≤ 1 * ‖(PiLp.single 1 i (1 : ℝ) : L1Coeffs ι)‖ :=
        mul_le_mul_of_nonneg_left (Submodule.Quotient.norm_mk_le (LinearMap.ker T) _) zero_le_one
      _ = 1 := by simp [PiLp.norm_single]
  · have ht : T (WithLp.toLp 1 x) = b := hx
    calc
      ℓ b = ℓ (T (WithLp.toLp 1 x)) := congrArg ℓ ht.symm
      _ = g q := hTransport _
      _ = finiteRoM atom b hFeasible :=
        hgValue.trans (quotient_norm_eq_finiteRoM atom b hFeasible x hx)

/-- The actual finite-atom primal minimum equals an attained dual maximum. -/
theorem finiteRoM_isGreatest_dual (atom : ι → V) (b : V)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp atom b x) :
    IsGreatest {z : ℝ | ∃ ℓ : V →ₗ[ℝ] ℝ,
      (∀ i, |ℓ (atom i)| ≤ 1) ∧ z = ℓ b} (finiteRoM atom b hFeasible) := by
  obtain ⟨ℓ, hAtom, hValue⟩ := exists_finiteRoM_dual_optimizer atom b hFeasible
  refine ⟨⟨ℓ, hAtom, hValue.symm⟩, ?_⟩
  rintro z ⟨g, hg, rfl⟩
  exact dual_le_l1Cost atom b (optimalCoeffs atom b hFeasible)
    (optimalCoeffs_isL1Minimizer atom b hFeasible).1 g hg

end

end AgtXIv.RoM

namespace AgtXIv.ReducedRoM

open scoped BigOperators
open AgtXIv.RoM AgtXIv.Stabilizer AgtXIv.Varela

noncomputable section

variable {ι : Type*} [Fintype ι] {n m : ℕ}

/-- Coordinates of a dual functional on the augmented expectation space. -/
def augmented_dualCoordinates (y : Fin m → ℝ) (μ : ℝ) :
    (ℝ × (Fin m → ℝ)) →ₗ[ℝ] ℝ where
  toFun p := μ * p.1 + ∑ i, p.2 i * y i
  map_add' p q := by
    simp only [Prod.fst_add, Prod.snd_add, Pi.add_apply, add_mul, mul_add,
      Finset.sum_add_distrib]
    ring
  map_smul' c p := by
    change μ * (c * p.1) + ∑ i, (c * p.2 i) * y i =
      c * (μ * p.1 + ∑ i, p.2 i * y i)
    simp only [mul_assoc, ← Finset.mul_sum, mul_add]
    ring

theorem augmented_dualCoordinates_apply (y : Fin m → ℝ) (μ t : ℝ) (v : Fin m → ℝ) :
    augmented_dualCoordinates y μ (t, v) = μ * t + ∑ i, v i * y i := rfl

/-- Every linear functional has the paper's scalar-and-vector coordinates. -/
theorem linearFunctional_eq_augmented_dualCoordinates
    (ℓ : (ℝ × (Fin m → ℝ)) →ₗ[ℝ] ℝ) :
    ℓ = augmented_dualCoordinates (fun i => ℓ (0, Pi.single i (1 : ℝ))) (ℓ (1, 0)) := by
  classical
  apply LinearMap.ext
  intro p
  have hFirst : (p.1, (0 : Fin m → ℝ)) = p.1 • (1, (0 : Fin m → ℝ)) := by simp
  have hSecond : ((0 : ℝ), p.2) =
      ∑ i, p.2 i • ((0 : ℝ), (Pi.single i (1 : ℝ) : Fin m → ℝ)) := by
    apply Prod.ext
    · simp [Prod.fst_sum]
    · funext j
      simp [Prod.snd_sum, Finset.sum_apply, Pi.single_apply]
  calc
    ℓ p = ℓ (p.1, 0) + ℓ (0, p.2) := by rw [← map_add]; simp
    _ = p.1 * ℓ (1, 0) + ∑ i, p.2 i * ℓ (0, Pi.single i (1 : ℝ)) := by
      rw [hFirst, hSecond]
      simp only [map_smul, map_sum, smul_eq_mul]
    _ = augmented_dualCoordinates (fun i => ℓ (0, Pi.single i (1 : ℝ))) (ℓ (1, 0)) p := by
      simp [augmented_dualCoordinates, mul_comm]

/-- The normalized primal equals the attained scalar/vector dual, with both
source constraints represented by the actual augmented reconstruction. -/
theorem normalized_finiteRoM_isGreatest_dual (atom : ι → (Fin m → ℝ)) (b : Fin m → ℝ)
    (hFeasible : ∃ x : ι → ℝ, SignedDecomp (augmentedAtom atom) (1, b) x) :
    IsGreatest {z : ℝ | ∃ (y : Fin m → ℝ) (μ : ℝ),
      (∀ j, |μ + ∑ i, atom j i * y i| ≤ 1) ∧ z = μ + ∑ i, b i * y i}
      (finiteRoM (augmentedAtom atom) (1, b) hFeasible) := by
  have hDual := finiteRoM_isGreatest_dual (augmentedAtom atom) (1, b) hFeasible
  obtain ⟨ℓ, hAtom, hValue⟩ := hDual.1
  let y : Fin m → ℝ := fun i => ℓ (0, Pi.single i (1 : ℝ))
  let μ : ℝ := ℓ (1, 0)
  have he : ℓ = augmented_dualCoordinates y μ := linearFunctional_eq_augmented_dualCoordinates ℓ
  refine ⟨⟨y, μ, ?_, ?_⟩, ?_⟩
  · intro j
    simpa [he, augmented_dualCoordinates, augmentedAtom] using hAtom j
  · simpa [he, augmented_dualCoordinates] using hValue
  · rintro z ⟨v, c, hAtoms, rfl⟩
    apply hDual.2
    refine ⟨augmented_dualCoordinates v c, ?_, ?_⟩
    · intro j
      simpa [augmented_dualCoordinates, augmentedAtom] using hAtoms j
    · simp [augmented_dualCoordinates]

/-- An attained dual for the actual projected-frame reduced robustness. This
does not assert the context/vertex representation or the final clique formula. -/
theorem reducedRoM_isGreatest_dual (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n)) :
    IsGreatest {z : ℝ | ∃ (y : Fin m → ℝ) (μ : ℝ),
      (∀ F, |μ + ∑ i, W.projectedFrameAtom F i * y i| ≤ 1) ∧
      z = μ + ∑ i, W.expectationProjection ρ.toTraceOneHermitian.1 i * y i}
      (reducedRoM W ρ) := by
  exact normalized_finiteRoM_isGreatest_dual W.projectedFrameAtom
    (W.expectationProjection ρ.toTraceOneHermitian.1) (augmented_projected_feasible W ρ)

end

end AgtXIv.ReducedRoM
