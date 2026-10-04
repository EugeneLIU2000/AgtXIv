import BinaryCliqueGram
import ReducedRoMGraphDual
import AgtXIvRootMath.F2Coordinates

/-! Uncompiled candidate factors through the actual phase-free Pauli support
space. The coefficient space is indexed by the vertices of the supplied clique.
-/

open scoped BigOperators

namespace AgtXIv.PauliCliqueGram

open AgtXIv.Stabilizer AgtXIv.Varela

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m) (Q : Finset (Fin m))

def supportCombination : (Q → F2) →ₗ[F2] F2Support n where
  toFun x := ∑ i : Q, x i • F2Support.pauli (W.observable i.val)
  map_add' x y := by simp [add_smul, Finset.sum_add_distrib]
  map_smul' c x := by simp [smul_smul, Finset.smul_sum]

def pairingCoordinates : F2Support n →ₗ[F2] (Q → F2) :=
  LinearMap.pi fun i => F2Support.symplecticForm (F2Support.pauli (W.observable i.val))

theorem composed_apply (x : Q → F2) (i : Q) :
    pairingCoordinates W Q (supportCombination W Q x) i =
      ∑ j : Q, x j * F2Support.symplecticForm
        (F2Support.pauli (W.observable i.val)) (F2Support.pauli (W.observable j.val)) := by
  simp [pairingCoordinates, supportCombination, map_sum, map_smul]

/-- Off-diagonal clique pairings cannot vanish: this uses actual Pauli
commutation, not a separately supplied matrix certificate. -/
theorem pairing_ne_zero_of_distinct
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (i j : Q) (hne : i ≠ j) :
    F2Support.symplecticForm (F2Support.pauli (W.observable i.val))
      (F2Support.pauli (W.observable j.val)) ≠ 0 := by
  intro hZero
  have hDistinct : i.val ≠ j.val := fun h => hne (Subtype.ext h)
  have hAdj := hQ i.property j.property hDistinct
  exact hAdj ((F2Support.pauli_commutes_iff_symplectic_eq_zero
    (W.observable i.val) (W.observable j.val)).mpr hZero)

theorem diagonal_pairing_zero (i : Q) :
    F2Support.symplecticForm (F2Support.pauli (W.observable i.val))
      (F2Support.pauli (W.observable i.val)) = 0 :=
  F2Support.symplectic_alternating _

private theorem f2_eq_one_of_ne_zero : ∀ a : F2, a ≠ 0 → a = 1 := by decide

theorem pairing_eq_one_of_distinct
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (i j : Q) (hne : i ≠ j) :
    F2Support.symplecticForm (F2Support.pauli (W.observable i.val))
      (F2Support.pauli (W.observable j.val)) = 1 := by
  exact f2_eq_one_of_ne_zero _ (pairing_ne_zero_of_distinct W Q hQ i j hne)

theorem factors_equal_gram
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) :
    (pairingCoordinates W Q).comp (supportCombination W Q) =
      AgtXIv.BinaryCliqueGram.gramMap Q := by
  classical
  refine LinearMap.ext fun x => funext fun i => ?_
  change pairingCoordinates W Q (supportCombination W Q x) i =
    x i + ∑ j : Q, x j
  rw [composed_apply]
  have hTerm (j : Q) : x j * F2Support.symplecticForm
      (F2Support.pauli (W.observable i.val)) (F2Support.pauli (W.observable j.val)) =
      x j - (if j = i then x i else 0) := by
    by_cases h : j = i
    · subst j
      simp [diagonal_pairing_zero W Q]
    · rw [pairing_eq_one_of_distinct W Q hQ i j (Ne.symm h)]
      simp [h]
  simp_rw [hTerm]
  rw [Finset.sum_sub_distrib]
  simp only [Finset.sum_ite_eq', Finset.mem_univ, if_true]
  have hNeg : -x i = x i := ZMod.neg_eq_self_mod_two (x i)
  simp only [sub_eq_add_neg, hNeg, add_comm]

/-- The concrete binary support has two n-coordinate halves. No abstract
dimension or Gram-factorization certificate is assumed in this bound. -/
theorem clique_card_le_two_mul_add_one
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m))) :
    Q.card ≤ 2 * n + 1 := by
  classical
  let e := F2Support.coordinateEquiv n
  let f := e.toLinearMap.comp (supportCombination W Q)
  let g := (pairingCoordinates W Q).comp e.symm.toLinearMap
  have hFactor : g.comp f = AgtXIv.BinaryCliqueGram.gramMap Q := by
    rw [← factors_equal_gram W Q hQ]
    refine LinearMap.ext fun x => ?_
    simp [f, g]
  have hDim := AgtXIv.BinaryCliqueGram.card_le_factor_finrank_add_one Q f g hFactor
  simpa [two_mul] using hDim

/-- For a size-2n+1 clique, the only binary support relations are the trivial
one and the full-support relation. This remains an uncompiled candidate. -/
theorem maximum_clique_support_kernel
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1) (x : Q → F2) :
    supportCombination W Q x = 0 ↔ x = 0 ∨ x = fun _ => 1 := by
  classical
  let e := F2Support.coordinateEquiv n
  let f := e.toLinearMap.comp (supportCombination W Q)
  let g := (pairingCoordinates W Q).comp e.symm.toLinearMap
  have hFactor : g.comp f = AgtXIv.BinaryCliqueGram.gramMap Q := by
    rw [← factors_equal_gram W Q hQ]
    refine LinearMap.ext fun y => ?_
    simp [f, g]
  have hDim : Module.finrank F2 ((Fin n → F2) × (Fin n → F2)) < Fintype.card Q := by
    simpa [hCard, two_mul] using Nat.lt_succ_self (2 * n)
  have hKernel := AgtXIv.BinaryCliqueGram.factor_kernel_iff_zero_or_one_of_finrank_lt
    Q f g hFactor hDim x
  have hZero : f x = 0 ↔ supportCombination W Q x = 0 := by
    change e (supportCombination W Q x) = 0 ↔ supportCombination W Q x = 0
    constructor
    · intro h
      apply e.injective
      simpa using h
    · intro h
      simp [h]
  rw [hZero] at hKernel
  exact hKernel

theorem maximum_clique_support_sum_zero
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1) :
    (∑ i : Q, F2Support.pauli (W.observable i.val)) = 0 := by
  have h := (maximum_clique_support_kernel W Q hQ hCard (fun _ => 1)).mpr (Or.inr rfl)
  simpa [supportCombination] using h

/-- The original ordered subset product is proportional to the identity.
Scalarity deliberately leaves the phase unspecified, as in the source claim. -/
theorem maximum_clique_product_scalar
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1) :
    IsScalarPauli (W.subsetProduct Q) := by
  apply (W.scalar_subsetProduct_iff_zero_sum Q).mpr
  have h := maximum_clique_support_sum_zero W Q hQ hCard
  rw [Finset.sum_coe_sort Q (fun i => F2Support.pauli (W.observable i))] at h
  exact h

/-- Every repetition-free ordering of the same maximal clique has a scalar
product; no equality of the phases for different orders is asserted. -/
theorem maximum_clique_product_scalar_any_order
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1)
    (l : List (Fin m)) (hNodup : l.Nodup) (hSet : l.toFinset = Q) :
    IsScalarPauli (l.map W.observable).prod :=
  (W.scalar_product_iff_for_any_order Q l hNodup hSet).mpr
    (maximum_clique_product_scalar W Q hQ hCard)

/-- Scalar subproducts of a maximal clique have either empty or full support. -/
theorem maximum_clique_scalar_subset
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1)
    (U : Finset (Fin m)) (hU : U ⊆ Q)
    (hScalar : IsScalarPauli (W.subsetProduct U)) : U = ∅ ∨ U = Q := by
  classical
  let x : Q → F2 := fun i => if i.val ∈ U then 1 else 0
  have hSum : supportCombination W Q x = ∑ i ∈ U, F2Support.pauli (W.observable i) := by
    change (∑ i : Q, (if i.val ∈ U then (1 : F2) else 0) •
      F2Support.pauli (W.observable i.val)) = _
    rw [Finset.sum_coe_sort Q (fun i => (if i ∈ U then (1 : F2) else 0) •
      F2Support.pauli (W.observable i))]
    calc
      _ = ∑ i ∈ U, (if i ∈ U then (1 : F2) else 0) •
          F2Support.pauli (W.observable i) :=
        (Finset.sum_subset hU (by intro i hi hnot; simp [hnot])).symm
      _ = _ := Finset.sum_congr rfl (by intro i hi; simp [hi])
  have hx : supportCombination W Q x = 0 := by
    rw [hSum]
    exact (W.scalar_subsetProduct_iff_zero_sum U).mp hScalar
  rcases (maximum_clique_support_kernel W Q hQ hCard x).mp hx with hZero | hOne
  · left
    apply Finset.eq_empty_iff_forall_notMem.mpr
    intro i hi
    have hc := congrFun hZero ⟨i, hU hi⟩
    simpa [x, hi] using hc
  · right
    apply Finset.Subset.antisymm hU
    intro i hi
    by_contra hnot
    have hc := congrFun hOne ⟨i, hi⟩
    simpa [x, hnot] using hc

theorem maximum_clique_isPauliDependency
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1) : W.IsPauliDependency Q := by
  classical
  refine ⟨Finset.card_pos.mp (by omega), maximum_clique_product_scalar W Q hQ hCard, ?_⟩
  intro U hProper hNonempty hScalar
  rcases maximum_clique_scalar_subset W Q hQ hCard U
      hProper.subset hScalar with hEmpty | hEqual
  · exact hNonempty.ne_empty hEmpty
  · exact hProper.ne hEqual

theorem maximum_clique_dependency_unique
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1)
    (U : Finset (Fin m)) (hU : U ⊆ Q) (hDependency : W.IsPauliDependency U) :
    U = Q := by
  rcases maximum_clique_scalar_subset W Q hQ hCard U hU hDependency.2.1 with hEmpty | hFull
  · exact False.elim (hDependency.1.ne_empty hEmpty)
  · exact hFull

/-- For n>0 the full clique has more than one vertex, so its dependency
cannot be active: activity would require the same vertices to commute. -/
theorem maximum_clique_dependency_not_active
    (hn : 0 < n)
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1) : ¬ W.IsActiveDependency Q := by
  classical
  intro hActive
  obtain ⟨i, hi⟩ := hActive.1.1
  have hOnly : ∀ j ∈ Q, j = i := by
    intro j hj
    by_contra hne
    exact hQ hj hi hne (hActive.2 hj hi hne)
  have hSingleton : Q = {i} := Finset.eq_singleton_iff_unique_mem.mpr ⟨hi, hOnly⟩
  have hSize : Q.card = 1 := by simp [hSingleton]
  omega

theorem maximum_clique_unique_inactive_dependency
    (hn : 0 < n)
    (hQ : W.contextFrustrationGraph.IsClique (Q : Set (Fin m)))
    (hCard : Q.card = 2 * n + 1) :
    W.IsPauliDependency Q ∧ ¬ W.IsActiveDependency Q ∧
      ∀ U : Finset (Fin m), U ⊆ Q → W.IsPauliDependency U → U = Q :=
  ⟨maximum_clique_isPauliDependency W Q hQ hCard,
   maximum_clique_dependency_not_active W Q hn hQ hCard,
   maximum_clique_dependency_unique W Q hQ hCard⟩

end
end AgtXIv.PauliCliqueGram
