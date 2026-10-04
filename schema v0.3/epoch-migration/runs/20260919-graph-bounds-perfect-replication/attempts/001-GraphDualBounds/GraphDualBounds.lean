import FiniteCliqueCoverAttainment
import WeightedCliqueCoverWeakDuality
import ReducedRoMGraphDual

/-!
Unconditional graph-dual bounds and their application to actual reduced RoM.
The cover in the upper bound is on the COMPLEMENT graph: its cliques are
independent sets of the original graph. The original graph's weighted clique
maximum is a lower bound. No perfect-graph foundation, strong-duality equality,
antiblocker identity or closed formula is assumed.
Source: arXiv:2607.26154v1 draft.tex:636--653 and 696--723.
-/

open scoped BigOperators

namespace AgtXIv.GraphDual

open AgtXIv.GraphFoundation

noncomputable section

variable {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V)

/-- The source's actual finite maximum over all cliques, including the empty clique. -/
def maxWeightClique (w : V → ℝ) : ℝ := by
  classical
  have h : (cliqueFinsets G).Nonempty := ⟨∅, by simp [cliqueFinsets]⟩
  exact (cliqueFinsets G).sup' h fun Q => ∑ v ∈ Q, w v

theorem independentFinsets_complement : independentFinsets Gᶜ = cliqueFinsets G := by
  classical
  ext S
  simp [independentFinsets, cliqueFinsets]

theorem maxWeightClique_eq_complement_independent (w : V → ℝ) :
    maxWeightClique G w = maxWeightIndependent Gᶜ w := by
  classical
  unfold maxWeightClique maxWeightIndependent
  simp only [independentFinsets_complement]

theorem mem_cliqueFinsets_iff (Q : Finset V) :
    Q ∈ cliqueFinsets G ↔ G.IsClique (Q : Set V) := by
  classical
  simp [cliqueFinsets]

theorem maxWeightClique_le_iff (w : V → ℝ) (a : ℝ) :
    maxWeightClique G w ≤ a ↔
      ∀ Q : Finset V, G.IsClique (Q : Set V) → (∑ v ∈ Q, w v) ≤ a := by
  classical
  unfold maxWeightClique
  rw [Finset.sup'_le_iff]
  simp only [cliqueFinsets, Finset.mem_filter, Finset.mem_powerset,
    Finset.subset_univ, true_and]

theorem independent_weight_le_max (w : V → ℝ) (S : Finset V)
    (hS : G.IsIndepSet (S : Set V)) :
    (∑ v ∈ S, w v) ≤ maxWeightIndependent G w := by
  classical
  exact Finset.le_sup' (fun T => ∑ v ∈ T, w v)
    (show S ∈ independentFinsets G by simp [independentFinsets, hS])

theorem independent_max_nonneg (w : V → ℝ) : 0 ≤ maxWeightIndependent G w := by
  simpa using independent_weight_le_max G w ∅ (by simp)

theorem independent_max_le_iff (w : V → ℝ) (a : ℝ) :
    maxWeightIndependent G w ≤ a ↔
      ∀ S : Finset V, G.IsIndepSet (S : Set V) → (∑ v ∈ S, w v) ≤ a := by
  classical
  unfold maxWeightIndependent
  rw [Finset.sup'_le_iff]
  simp only [independentFinsets, Finset.mem_filter, Finset.mem_powerset,
    Finset.subset_univ, true_and]

theorem independent_max_zero : maxWeightIndependent G (fun _ => (0 : ℝ)) = 0 := by
  apply le_antisymm
  · exact (independent_max_le_iff G _ _).2 fun _ _ => by simp
  · exact independent_max_nonneg G _

/-- Generic objective-value set of the same graph program as the reduced RoM bridge. -/
def objectiveValues (b : V → ℝ) : Set ℝ :=
  {z | ∃ (y : V → ℝ) (μ : ℝ),
    maxWeightIndependent G (fun v => |y v|) + |μ| ≤ 1 ∧
    z = μ + ∑ v, b v * y v}

theorem one_mem_objectiveValues (b : V → ℝ) : 1 ∈ objectiveValues G b := by
  refine ⟨fun _ => 0, 1, ?_, ?_⟩
  · simp [independent_max_zero]
  · simp

/-- Choose a sign attaining each coordinate's absolute value on Q, and zero off Q. -/
def signedCliqueVector (b : V → ℝ) (Q : Finset V) : V → ℝ :=
  fun v => if v ∈ Q then if 0 ≤ b v then 1 else -1 else 0

omit [Fintype V] in
theorem abs_signedCliqueVector (b : V → ℝ) (Q : Finset V) (v : V) :
    |signedCliqueVector b Q v| = if v ∈ Q then (1 : ℝ) else 0 := by
  classical
  unfold signedCliqueVector
  split_ifs <;> norm_num

theorem signedCliqueVector_pairing (b : V → ℝ) (Q : Finset V) :
    (∑ v, b v * signedCliqueVector b Q v) = ∑ v ∈ Q, |b v| := by
  classical
  have hv (v : V) : b v * signedCliqueVector b Q v = if v ∈ Q then |b v| else 0 := by
    by_cases hQ : v ∈ Q
    · by_cases hb : 0 ≤ b v
      · simp [signedCliqueVector, hQ, hb, abs_of_nonneg hb]
      · simp [signedCliqueVector, hQ, hb, abs_of_neg (lt_of_not_ge hb)]
    · simp [signedCliqueVector, hQ]
  simp only [hv]
  simp

theorem clique_weight_mem_objectiveValues (b : V → ℝ) (Q : Finset V)
    (hQ : G.IsClique (Q : Set V)) :
    (∑ v ∈ Q, |b v|) ∈ objectiveValues G b := by
  classical
  refine ⟨signedCliqueVector b Q, 0, ?_, ?_⟩
  · simp only [abs_zero, add_zero]
    apply (independent_max_le_iff G _ _).2
    intro S hS
    simp only [abs_signedCliqueVector]
    exact clique_weight_on_independent_le G S Q 1 hS hQ (by norm_num)
  · simp only [zero_add, signedCliqueVector_pairing]

/-- Any fractional clique cover of the complement bounds the pairing with
nonnegative z by its cost times the original graph's independent-set maximum. -/
theorem pairing_le_complement_cover_cost_mul (w z : V → ℝ) (lam : Finset V → ℝ)
    (hz : ∀ v, 0 ≤ z v) (hCover : IsFractionalCliqueCover Gᶜ w lam) :
    (∑ v, w v * z v) ≤
      (∑ Q ∈ cliqueFinsets Gᶜ, lam Q) * maxWeightIndependent G z := by
  classical
  calc
    (∑ v, w v * z v) ≤
        ∑ v, (∑ Q ∈ cliqueFinsets Gᶜ, if v ∈ Q then lam Q else 0) * z v := by
      exact Finset.sum_le_sum fun v _ => mul_le_mul_of_nonneg_right (hCover.2 v) (hz v)
    _ = ∑ Q ∈ cliqueFinsets Gᶜ, lam Q * (∑ v ∈ Q, z v) := by
      simp_rw [Finset.sum_mul]
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro Q _
      simp [Finset.mul_sum, ite_mul]
    _ ≤ ∑ Q ∈ cliqueFinsets Gᶜ, lam Q * maxWeightIndependent G z := by
      apply Finset.sum_le_sum
      intro Q hQ
      have hc : Gᶜ.IsClique (Q : Set V) := (mem_cliqueFinsets_iff Gᶜ Q).mp hQ
      have hi : G.IsIndepSet (Q : Set V) := by simpa using hc
      exact mul_le_mul_of_nonneg_left (independent_weight_le_max G z Q hi) (hCover.1 Q hQ)
    _ = (∑ Q ∈ cliqueFinsets Gᶜ, lam Q) * maxWeightIndependent G z :=
      (Finset.sum_mul _ _ _).symm

/-- A companion form uses a cover of the original graph. It will support
closed-form evaluation directly from original-graph weighted duality, without
requiring complement perfectness as a separate intermediate theorem. -/
theorem pairing_le_clique_max_mul_cover_cost (w z : V → ℝ) (lam : Finset V → ℝ)
    (hz : ∀ v, 0 ≤ z v) (hCover : IsFractionalCliqueCover G w lam) :
    (∑ v, w v * z v) ≤
      (∑ Q ∈ cliqueFinsets G, lam Q) * maxWeightClique G z := by
  have h := pairing_le_complement_cover_cost_mul Gᶜ w z lam hz (by simpa using hCover)
  simpa only [compl_compl, maxWeightClique_eq_complement_independent] using h

theorem objective_le_complement_cover (b y : V → ℝ) (μ : ℝ)
    (hFeasible : maxWeightIndependent G (fun v => |y v|) + |μ| ≤ 1)
    (lam : Finset V → ℝ)
    (hCover : IsFractionalCliqueCover Gᶜ (fun v => |b v|) lam) :
    μ + ∑ v, b v * y v ≤ max 1 (∑ Q ∈ cliqueFinsets Gᶜ, lam Q) := by
  let a := maxWeightIndependent G (fun v => |y v|)
  let c := ∑ Q ∈ cliqueFinsets Gᶜ, lam Q
  have ha : 0 ≤ a := independent_max_nonneg G _
  have hPair := pairing_le_complement_cover_cost_mul G (fun v => |b v|)
    (fun v => |y v|) lam (fun v => abs_nonneg _) hCover
  have hSigned : (∑ v, b v * y v) ≤ ∑ v, |b v| * |y v| := by
    apply Finset.sum_le_sum
    intro v _
    simpa only [abs_mul] using le_abs_self (b v * y v)
  have hScale : c * a + |μ| ≤ max 1 c := by
    calc
      c * a + |μ| = c * a + 1 * |μ| := by ring
      _ ≤ max 1 c * a + max 1 c * |μ| :=
        add_le_add (mul_le_mul_of_nonneg_right (le_max_right 1 c) ha)
          (mul_le_mul_of_nonneg_right (le_max_left 1 c) (abs_nonneg μ))
      _ = max 1 c * (a + |μ|) := by ring
      _ ≤ max 1 c * 1 :=
        mul_le_mul_of_nonneg_left hFeasible ((by norm_num : (0 : ℝ) ≤ 1).trans (le_max_left _ _))
      _ = max 1 c := mul_one _
  change μ + ∑ v, b v * y v ≤ max 1 c
  have hPair' : (∑ v, |b v| * |y v|) ≤ c * a := hPair
  linarith [le_abs_self μ]

theorem objective_le_fractional_complement_cover (b y : V → ℝ) (μ : ℝ)
    (hFeasible : maxWeightIndependent G (fun v => |y v|) + |μ| ≤ 1) :
    μ + ∑ v, b v * y v ≤ max 1 (fractionalCliqueCoverValue Gᶜ (fun v => |b v|)) := by
  obtain ⟨lam, hCover, hValue⟩ := fractionalCliqueCoverValue_attained Gᶜ
    (fun v => |b v|) (fun v => abs_nonneg _)
  rw [hValue]
  exact objective_le_complement_cover G b y μ hFeasible lam hCover

end
end AgtXIv.GraphDual

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.GraphFoundation AgtXIv.GraphDual

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n))

theorem graphDualValues_eq_objectiveValues :
    graphDualValues W ρ =
      objectiveValues W.contextFrustrationGraph (W.expectationProjection ρ.toTraceOneHermitian.1) := rfl

/-- Every actual clique furnishes a feasible attaining lower-bound witness. -/
theorem maxWeightClique_le_reducedRoM (hNoActive : W.NoActiveDependencies) :
    maxWeightClique W.contextFrustrationGraph
        (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|) ≤ reducedRoM W ρ := by
  apply (maxWeightClique_le_iff _ _ _).2
  intro Q hQ
  have hGreat := reducedRoM_isGreatest_graph_dual W ρ hNoActive
  rw [graphDualValues_eq_objectiveValues] at hGreat
  exact hGreat.2 (clique_weight_mem_objectiveValues _ _ Q hQ)

/-- No perfection premise: the complement cover is a valid upper bound. -/
theorem reducedRoM_le_fractional_complement_cover (hNoActive : W.NoActiveDependencies) :
    reducedRoM W ρ ≤
      max 1 (fractionalCliqueCoverValue W.contextFrustrationGraphᶜ
        (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|)) := by
  obtain ⟨y, μ, hFeasible, hValue⟩ := exists_graph_dual_optimizer W ρ hNoActive
  rw [hValue]
  exact objective_le_fractional_complement_cover _ _ y μ hFeasible

/-- The genuine reduced primal lies between the source's clique expression
and the complement's fractional clique cover expression. Perfect-graph
integrality can identify these endpoints later; it is not assumed here. -/
theorem reducedRoM_clique_cover_sandwich (hNoActive : W.NoActiveDependencies) :
    max 1 (maxWeightClique W.contextFrustrationGraph
      (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|)) ≤ reducedRoM W ρ ∧
    reducedRoM W ρ ≤ max 1 (fractionalCliqueCoverValue W.contextFrustrationGraphᶜ
      (fun i => |W.expectationProjection ρ.toTraceOneHermitian.1 i|)) := by
  exact ⟨max_le (one_le_reducedRoM W ρ) (maxWeightClique_le_reducedRoM W ρ hNoActive),
    reducedRoM_le_fractional_complement_cover W ρ hNoActive⟩

end
end AgtXIv.ReducedRoM
