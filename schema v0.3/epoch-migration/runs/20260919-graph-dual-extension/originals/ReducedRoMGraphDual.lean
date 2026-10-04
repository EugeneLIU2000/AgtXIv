import RoMGraphDualFoundation
import AgtXIvVarela.ExternalPerfectGraphFoundation

/-!
Actual reduced robustness equals the attained weighted-independent-set dual
on the source's no-active-dependency branch. Both convex atom maps, normalized
finite-l1 duality and sign-domain collapse are proved upstream and instantiated
here; none is an extra premise. No perfect-graph theorem is used here.
Source: arXiv:2607.26154v1 draft.tex:223--231, 270--282, 498--568.
-/

open scoped BigOperators

namespace AgtXIv.Varela.MeasurementWindow

open AgtXIv.Stabilizer AgtXIv.Stabilizerness AgtXIv.GraphFoundation

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

/-- The actual graph on measured Pauli observables, without a Physlib import. -/
def contextFrustrationGraph : SimpleGraph (Fin m) where
  Adj i j := ¬(W.observable i).commutesWith (W.observable j)
  symm := by
    intro i j hij hji
    exact hij ((Pauli.commutesWith_iff _ _).mpr ((Pauli.commutesWith_iff _ _).mp hji).symm)
  loopless := by
    constructor
    intro i hii
    exact hii ((Pauli.commutesWith_iff _ _).mpr (Commute.refl _))

theorem independent_iff_commutingContext (S : Finset (Fin m)) :
    W.contextFrustrationGraph.IsIndepSet (S : Set (Fin m)) ↔ W.IsCommutingContext S := by
  classical
  simp only [SimpleGraph.isIndepSet_iff, contextFrustrationGraph, not_not,
    IsCommutingContext]

theorem maxWeightIndependent_le_iff_contexts (w : Fin m → ℝ) (a : ℝ) :
    maxWeightIndependent W.contextFrustrationGraph w ≤ a ↔
      ∀ S : Finset (Fin m), W.IsCommutingContext S → (∑ i ∈ S, w i) ≤ a := by
  classical
  unfold maxWeightIndependent
  rw [Finset.sup'_le_iff]
  simp only [independentFinsets, Finset.mem_filter, Finset.mem_powerset,
    Finset.subset_univ, true_and, W.independent_iff_commutingContext]

theorem context_vector_dot (c : W.MaximalSignedContext) (y : Fin m → ℝ) :
    (∑ i, MaximalSignedContext.vector W c i * y i) =
      ∑ i : c.support, (if c.sign i then (-1 : ℝ) else 1) * y i := by
  classical
  rw [Finset.sum_coe_sort c.support (fun i => (if c.sign i then (-1 : ℝ) else 1) * y i)]
  simp [MaximalSignedContext.vector, ite_mul]

/-- A normalized total encoding of any sign assignment on a maximal context. -/
def signedMaximalCandidate (hNoActive : W.NoActiveDependencies)
    (S : Finset (Fin m)) (hMax : W.IsMaximalCommutingContext S)
    (f : Fin m → Bool) : W.MaximalSignedContext where
  support := S
  sign i := if i ∈ S then f i else false
  offSupportFalse i hi := by simp [hi]
  maximal := hMax
  admissible := W.isAdmissibleSign_of_noActiveDependencies hNoActive S hMax.1 _

theorem signedMaximalCandidate_dot (hNoActive : W.NoActiveDependencies)
    (S : Finset (Fin m)) (hMax : W.IsMaximalCommutingContext S)
    (f : Fin m → Bool) (y : Fin m → ℝ) :
    (∑ i, MaximalSignedContext.vector W (W.signedMaximalCandidate hNoActive S hMax f) i * y i) =
      ∑ i : S, (if f i then (-1 : ℝ) else 1) * y i := by
  rw [W.context_vector_dot]
  apply Finset.sum_congr rfl
  intro i _
  simp [signedMaximalCandidate]

/-- Exact elimination of the actual admissible signs, using the proved
no-active implication and the attained sign maximum for each context. -/
theorem context_dual_constraint_iff_maximal_weights
    (hNoActive : W.NoActiveDependencies) (y : Fin m → ℝ) (μ : ℝ) :
    (∀ c : W.MaximalSignedContext,
      |μ + ∑ i, MaximalSignedContext.vector W c i * y i| ≤ 1) ↔
    (∀ S : Finset (Fin m), W.IsMaximalCommutingContext S →
      (∑ i ∈ S, |y i|) + |μ| ≤ 1) := by
  classical
  constructor
  · intro h S hMax
    have hGreat := W.max_abs_context_signed_sum_of_noActiveDependencies
      hNoActive S hMax.1 (fun i : S => y i) μ
    obtain ⟨s, ⟨f, hf, hs⟩, hValue⟩ := hGreat.1
    have hBound := h (W.signedMaximalCandidate hNoActive S hMax f)
    rw [W.signedMaximalCandidate_dot] at hBound
    have hSum : (∑ i : S, s i * y i) =
        ∑ i : S, (if f i then (-1 : ℝ) else 1) * y i := by
      exact Finset.sum_congr rfl fun i _ => by rw [hs i]
    rw [hSum] at hValue
    have hResult : (∑ i : S, |y i|) + |μ| ≤ 1 := by
      rw [hValue]
      simpa only [add_comm] using hBound
    rw [Finset.sum_coe_sort S (fun i => |y i|)] at hResult
    exact hResult
  · intro h c
    have hGreat := W.max_abs_context_signed_sum_of_noActiveDependencies
      hNoActive c.support c.maximal.1 (fun i : c.support => y i) μ
    have hSigns : (fun i : c.support => if c.sign i then (-1 : ℝ) else 1) ∈
        W.realAdmissibleSigns c.support := ⟨c.sign, c.admissible, fun _ => rfl⟩
    have hBound := hGreat.2 ⟨_, hSigns, rfl⟩
    rw [W.context_vector_dot, add_comm]
    have hTotal := h c.support c.maximal
    rw [← Finset.sum_coe_sort c.support (fun i => |y i|)] at hTotal
    exact hBound.trans hTotal

/-- Nonnegative weights let every context extend to a maximal one without
reducing its weight. The context itself may be empty; MeasurementWindow
retains its existing nonempty-window field. -/
theorem maximal_weights_iff_all_context_weights (y : Fin m → ℝ) (μ : ℝ) :
    (∀ S : Finset (Fin m), W.IsMaximalCommutingContext S →
      (∑ i ∈ S, |y i|) + |μ| ≤ 1) ↔
    (∀ S : Finset (Fin m), W.IsCommutingContext S →
      (∑ i ∈ S, |y i|) + |μ| ≤ 1) := by
  constructor
  · intro h S hS
    obtain ⟨T, hST, hMax⟩ := W.exists_maximal_context_containing S hS
    have hWeight : (∑ i ∈ S, |y i|) ≤ ∑ i ∈ T, |y i| :=
      Finset.sum_le_sum_of_subset_of_nonneg hST (fun i _ _ => abs_nonneg (y i))
    have hTotal := h T hMax
    linarith
  · exact fun h S hS => h S hS.1

/-- The source's alpha constraint, now obtained from actual context atoms. -/
theorem context_dual_constraint_iff_graph
    (hNoActive : W.NoActiveDependencies) (y : Fin m → ℝ) (μ : ℝ) :
    (∀ c : W.MaximalSignedContext,
      |μ + ∑ i, MaximalSignedContext.vector W c i * y i| ≤ 1) ↔
    maxWeightIndependent W.contextFrustrationGraph (fun i => |y i|) + |μ| ≤ 1 := by
  rw [W.context_dual_constraint_iff_maximal_weights hNoActive,
    W.maximal_weights_iff_all_context_weights]
  rw [← le_sub_iff_add_le, W.maxWeightIndependent_le_iff_contexts]
  exact forall_congr' fun S => imp_congr_right fun _ => le_sub_iff_add_le.symm

end
end AgtXIv.Varela.MeasurementWindow

namespace AgtXIv.ReducedRoM

open AgtXIv.Stabilizer AgtXIv.Varela AgtXIv.RoM AgtXIv.GraphFoundation

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m) (ρ : DensityMatrix (2 ^ n))

/-- Feasibility is transported from actual density-matrix frame semantics. -/
theorem augmented_context_feasible (hNoActive : W.NoActiveDependencies) :
    ∃ x : W.MaximalSignedContext → ℝ,
      SignedDecomp (augmentedAtom (MeasurementWindow.MaximalSignedContext.vector W))
        (1, W.expectationProjection ρ.toTraceOneHermitian.1) x := by
  exact augmented_feasible_of_convex_atoms W.projectedFrameAtom
    (MeasurementWindow.MaximalSignedContext.vector W)
    (W.atomRefinement_of_noActiveDependencies hNoActive)
    (W.expectationProjection ρ.toTraceOneHermitian.1) (augmented_projected_feasible W ρ)

/-- The genuine normalized finite-l1 minimum over context generators equals
the existing reduced robustness; both directions are constructed upstream. -/
theorem reducedRoM_eq_context_minimum (hNoActive : W.NoActiveDependencies) :
    reducedRoM W ρ =
      finiteRoM (augmentedAtom (MeasurementWindow.MaximalSignedContext.vector W))
        (1, W.expectationProjection ρ.toTraceOneHermitian.1)
        (augmented_context_feasible W ρ hNoActive) := by
  exact reducedRoM_eq_of_mutual_convex_generators W ρ
    (MeasurementWindow.MaximalSignedContext.vector W)
    (W.atomRefinement_of_noActiveDependencies hNoActive)
    (W.candidatePhysical_of_noActiveDependencies hNoActive)

theorem reducedRoM_isGreatest_context_dual (hNoActive : W.NoActiveDependencies) :
    IsGreatest {z : ℝ | ∃ (y : Fin m → ℝ) (μ : ℝ),
      (∀ c : W.MaximalSignedContext,
        |μ + ∑ i, MeasurementWindow.MaximalSignedContext.vector W c i * y i| ≤ 1) ∧
      z = μ + ∑ i, W.expectationProjection ρ.toTraceOneHermitian.1 i * y i}
      (reducedRoM W ρ) := by
  rw [reducedRoM_eq_context_minimum W ρ hNoActive]
  exact normalized_finiteRoM_isGreatest_dual
    (MeasurementWindow.MaximalSignedContext.vector W)
    (W.expectationProjection ρ.toTraceOneHermitian.1) (augmented_context_feasible W ρ hNoActive)

/-- Graph dual objective values; alpha is the existing finite independent-set
maximum, not a newly assumed optimization oracle. -/
def graphDualValues : Set ℝ :=
  {z : ℝ | ∃ (y : Fin m → ℝ) (μ : ℝ),
    maxWeightIndependent W.contextFrustrationGraph (fun i => |y i|) + |μ| ≤ 1 ∧
    z = μ + ∑ i, W.expectationProjection ρ.toTraceOneHermitian.1 i * y i}

/-- Actual reduced RoM is the attained graph dual optimum. Only the explicit
source no-active-dependency hypothesis remains; no VRep, strong-duality or
sign-collapse proposition is taken as an argument. -/
theorem reducedRoM_isGreatest_graph_dual (hNoActive : W.NoActiveDependencies) :
    IsGreatest (graphDualValues W ρ) (reducedRoM W ρ) := by
  have hDual := reducedRoM_isGreatest_context_dual W ρ hNoActive
  simpa only [graphDualValues, W.context_dual_constraint_iff_graph hNoActive] using hDual

theorem reducedRoM_eq_graph_dual_sup (hNoActive : W.NoActiveDependencies) :
    reducedRoM W ρ = sSup (graphDualValues W ρ) :=
  (reducedRoM_isGreatest_graph_dual W ρ hNoActive).csSup_eq.symm

theorem exists_graph_dual_optimizer (hNoActive : W.NoActiveDependencies) :
    ∃ (y : Fin m → ℝ) (μ : ℝ),
      maxWeightIndependent W.contextFrustrationGraph (fun i => |y i|) + |μ| ≤ 1 ∧
      reducedRoM W ρ = μ + ∑ i, W.expectationProjection ρ.toTraceOneHermitian.1 i * y i :=
  (reducedRoM_isGreatest_graph_dual W ρ hNoActive).1

end
end AgtXIv.ReducedRoM
