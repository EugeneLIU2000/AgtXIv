import AgtXIvVarela.ExternalPerfectGraphFoundation
import Mathlib

/-!
Finite nonnegative clique covers attain their minimum. This closes the sInf
definedness/attainment obligation independently of perfect-graph duality.
No perfectness or equality with the maximum independent-set weight is assumed.
-/

open scoped BigOperators

namespace AgtXIv.GraphFoundation

noncomputable section

def IsNonnegativeFiniteCover {ι κ : Type*} [Fintype ι]
    (R : κ → ι → Prop) (w : κ → ℝ) (x : ι → ℝ) : Prop := by
  classical
  exact (∀ i, 0 ≤ x i) ∧ ∀ v, w v ≤ ∑ i, if R v i then x i else 0

theorem exists_nonnegative_finite_cover_minimizer {ι κ : Type*} [Fintype ι]
    (R : κ → ι → Prop) (w : κ → ℝ)
    (hFeasible : ∃ x, IsNonnegativeFiniteCover R w x) :
    ∃ x, IsNonnegativeFiniteCover R w x ∧
      ∀ y, IsNonnegativeFiniteCover R w y → (∑ i, x i) ≤ ∑ i, y i := by
  classical
  obtain ⟨x₀, hx₀⟩ := hFeasible
  let cost : (ι → ℝ) → ℝ := fun x => ∑ i, x i
  have hcost : Continuous cost := by dsimp [cost]; fun_prop
  have hcover : IsClosed {x : ι → ℝ | IsNonnegativeFiniteCover R w x} := by
    simp only [IsNonnegativeFiniteCover, Set.setOf_and, Set.setOf_forall]
    apply IsClosed.inter
    · exact isClosed_iInter fun i => isClosed_le continuous_const (continuous_apply i)
    · apply isClosed_iInter
      intro v
      apply isClosed_le continuous_const
      apply continuous_finset_sum
      intro i _
      by_cases h : R v i
      · simpa only [if_pos h] using continuous_apply i
      · simp only [if_neg h]
        exact continuous_const
  let candidates : Set (ι → ℝ) :=
    {x | IsNonnegativeFiniteCover R w x ∧ cost x ≤ cost x₀}
  have hnonempty : candidates.Nonempty := ⟨x₀, hx₀, le_rfl⟩
  have hclosed : IsClosed candidates := hcover.inter (isClosed_le hcost continuous_const)
  have hnonneg : 0 ≤ cost x₀ := Finset.sum_nonneg fun i _ => hx₀.1 i
  have hbounded : Bornology.IsBounded candidates := by
    apply Metric.isBounded_closedBall.subset
    intro x hx
    rw [Metric.mem_closedBall, dist_zero_right]
    apply (pi_norm_le_iff_of_nonneg hnonneg).2
    intro i
    rw [Real.norm_eq_abs, abs_of_nonneg (hx.1.1 i)]
    exact (Finset.single_le_sum (fun j _ => hx.1.1 j) (Finset.mem_univ i)).trans hx.2
  have hcompact : IsCompact candidates :=
    Metric.isCompact_iff_isClosed_bounded.mpr ⟨hclosed, hbounded⟩
  obtain ⟨x, hx, hmin⟩ := hcompact.exists_isMinOn hnonempty hcost.continuousOn
  refine ⟨x, hx.1, ?_⟩
  intro y hy
  by_cases hcostY : cost y ≤ cost x₀
  · exact hmin ⟨hy, hcostY⟩
  · exact hx.2.trans (le_of_not_ge hcostY)

theorem singleton_mem_cliqueFinsets {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (v : V) : {v} ∈ cliqueFinsets G := by
  classical
  simp [cliqueFinsets, G.isClique_singleton v]

theorem fractionalCliqueCover_feasible {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) :
    ∃ lam, IsFractionalCliqueCover G w lam := by
  classical
  let lam : Finset V → ℝ := fun Q => ∑ v ∈ Q, w v
  have hlam : ∀ Q, 0 ≤ lam Q := fun Q => Finset.sum_nonneg fun v _ => hw v
  refine ⟨lam, (fun Q _ => hlam Q), ?_⟩
  intro v
  have hterm : (if v ∈ ({v} : Finset V) then lam {v} else 0) = w v := by simp [lam]
  rw [← hterm]
  exact Finset.single_le_sum (f := fun Q => if v ∈ Q then lam Q else 0)
    (fun Q _ => by dsimp only; split_ifs; exact hlam Q; exact le_rfl)
    (singleton_mem_cliqueFinsets G v)

theorem fractionalCliqueCover_cost_nonneg {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (lam : Finset V → ℝ)
    (hlam : IsFractionalCliqueCover G w lam) :
    0 ≤ ∑ Q ∈ cliqueFinsets G, lam Q :=
  Finset.sum_nonneg hlam.1

theorem exists_minimizing_fractionalCliqueCover {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) :
    ∃ lam, IsFractionalCliqueCover G w lam ∧
      ∀ μ, IsFractionalCliqueCover G w μ →
        (∑ Q ∈ cliqueFinsets G, lam Q) ≤ ∑ Q ∈ cliqueFinsets G, μ Q := by
  classical
  let C := cliqueFinsets G
  let R : V → C → Prop := fun v Q => v ∈ Q.val
  have hr (v : V) (z : C → ℝ) :
      (∑ Q : C, @ite ℝ (R v Q) (Classical.propDecidable (R v Q)) (z Q) 0) =
        ∑ Q : C, if v ∈ Q.val then z Q else 0 := by
    apply Finset.sum_congr rfl
    intro Q _
    by_cases h : v ∈ Q.val <;> simp [R, h]
  obtain ⟨lam₀, hlam₀⟩ := fractionalCliqueCover_feasible G w hw
  have hfeasible : ∃ x : C → ℝ, IsNonnegativeFiniteCover R w x := by
    refine ⟨fun Q => lam₀ Q.val, ?_, ?_⟩
    · exact fun Q => hlam₀.1 Q.val Q.property
    · intro v
      rw [hr]
      rw [Finset.sum_coe_sort C (fun Q => if v ∈ Q then lam₀ Q else 0)]
      exact hlam₀.2 v
  obtain ⟨x, hx, hmin⟩ := exists_nonnegative_finite_cover_minimizer R w hfeasible
  let lam : Finset V → ℝ := fun Q => if h : Q ∈ C then x ⟨Q, h⟩ else 0
  have hrestrict : ∀ Q : C, lam Q.val = x Q := by intro Q; simp [lam, Q.property]
  have hsum : (∑ Q ∈ C, lam Q) = ∑ Q : C, x Q := by
    rw [← Finset.sum_coe_sort]
    exact Finset.sum_congr rfl fun Q _ => hrestrict Q
  have hcover : IsFractionalCliqueCover G w lam := by
    constructor
    · intro Q hQ
      change 0 ≤ lam Q
      have hQC : Q ∈ C := hQ
      simpa only [lam, dif_pos hQC] using hx.1 ⟨Q, hQC⟩
    · intro v
      have hv := hx.2 v
      rw [hr] at hv
      change w v ≤ ∑ Q ∈ C, if v ∈ Q then lam Q else 0
      rw [← Finset.sum_coe_sort C (fun Q => if v ∈ Q then lam Q else 0)]
      simpa only [hrestrict] using hv
  refine ⟨lam, hcover, ?_⟩
  intro μ hμ
  have hm : IsNonnegativeFiniteCover R w (fun Q : C => μ Q.val) := by
    constructor
    · exact fun Q => hμ.1 Q.val Q.property
    · intro v
      rw [hr]
      rw [Finset.sum_coe_sort C (fun Q => if v ∈ Q then μ Q else 0)]
      exact hμ.2 v
  change (∑ Q ∈ C, lam Q) ≤ ∑ Q ∈ C, μ Q
  rw [hsum, ← Finset.sum_coe_sort C μ]
  exact hmin _ hm

theorem fractionalCliqueCoverValue_attained {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) :
    ∃ lam, IsFractionalCliqueCover G w lam ∧
      fractionalCliqueCoverValue G w = ∑ Q ∈ cliqueFinsets G, lam Q := by
  obtain ⟨lam, hlam, hmin⟩ := exists_minimizing_fractionalCliqueCover G w hw
  refine ⟨lam, hlam, ?_⟩
  have hleast : IsLeast {c : ℝ | ∃ μ, IsFractionalCliqueCover G w μ ∧
      c = ∑ Q ∈ cliqueFinsets G, μ Q} (∑ Q ∈ cliqueFinsets G, lam Q) := by
    refine ⟨⟨lam, hlam, rfl⟩, ?_⟩
    rintro c ⟨μ, hμ, rfl⟩
    exact hmin μ hμ
  exact hleast.csInf_eq

theorem fractionalCliqueCoverValue_nonneg {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) :
    0 ≤ fractionalCliqueCoverValue G w := by
  obtain ⟨lam, hlam, heq⟩ := fractionalCliqueCoverValue_attained G w hw
  rw [heq]
  exact fractionalCliqueCover_cost_nonneg G w lam hlam

end

end AgtXIv.GraphFoundation
