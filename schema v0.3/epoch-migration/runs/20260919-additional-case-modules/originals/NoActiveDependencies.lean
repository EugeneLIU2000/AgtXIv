import ContextSignIndependence

/-!
The no-active-dependency hypothesis is a statement about nonempty,
inclusion-minimal scalar Pauli products, as in arXiv:2607.26154v1
draft.tex:223--231 and 520--568. It is not defined by context independence.

We prove scalar-product relations are precisely zero binary-support sums,
independently of the order used for the product. A nontrivial F2 linear
relation contains a nonempty minimal such relation. In a commuting context
that relation is active. The absence of active dependencies therefore gives
support independence and the actual phase-admissible sign domain and maximum.

This proves the forward collapse direction. The reverse direction and the
full affine parity-code description are not established in this module.
The original cached Lean 4.30.0-rc2 epoch is used.
-/

open scoped BigOperators

namespace AgtXIv.Stabilizer

noncomputable section

/-- A Pauli proportional to identity has only its ZMod 4 phase remaining. -/
def IsScalarPauli {n : ℕ} (P : Pauli n) : Prop :=
  ∃ phase : ZMod 4, P = (1 : Pauli n).addPhase phase

theorem support_eq_zero_iff_scalar {n : ℕ} (P : Pauli n) :
    F2Support.pauli P = 0 ↔ IsScalarPauli P := by
  constructor
  · intro h
    have hz := congrArg (fun v : F2Support n => v.1.bits) h
    have hx := congrArg (fun v : F2Support n => v.2.bits) h
    change P.z = 0 at hz
    change P.x = 0 at hx
    refine ⟨P.m, ?_⟩
    apply Pauli.ext
    · simp [Pauli.addPhase]
    · simpa [Pauli.addPhase] using hz
    · simpa [Pauli.addPhase] using hx
  · rintro ⟨phase, rfl⟩
    simp

/-- The exact matrix interpretation of the phase-only identity representative. -/
theorem scalarPauli_toCMatrix {n : ℕ} (P : Pauli n) (h : IsScalarPauli P) :
    ∃ phase : ZMod 4,
      P.toCMatrix = ((-Complex.I) ^ phase.val) • (1 : Pauli n).toCMatrix := by
  obtain ⟨phase, rfl⟩ := h
  exact ⟨phase, Pauli.addPhase_toCMatrix _ _⟩

/-- No commutation is required when only the support of an ordered product is retained. -/
theorem support_list_product {ι : Type*} {n : ℕ} (p : ι → Pauli n) (l : List ι) :
    F2Support.pauli (l.map p).prod = (l.map (fun i => F2Support.pauli (p i))).sum := by
  induction l with
  | nil => simp
  | cons i l ih => simp [F2Support.pauli_mul, ih]

/-- Over F2 a nonzero coefficient is one, so a linear relation is a nonempty
zero-sum subset, with no repetitions or integer multiplicities. -/
theorem exists_nonempty_zero_sum_of_not_linearIndependent
    {ι M : Type*} [Fintype ι] [AddCommGroup M] [Module F2 M]
    (v : ι → M) (h : ¬ LinearIndependent F2 v) :
    ∃ T : Finset ι, T.Nonempty ∧ ∑ i ∈ T, v i = 0 := by
  classical
  obtain ⟨g, hsum, i, hi⟩ := Fintype.not_linearIndependent_iff.mp h
  refine ⟨Finset.univ.filter (fun i => g i ≠ 0), ?_, ?_⟩
  · exact ⟨i, by simp [hi]⟩
  · calc
      (∑ i ∈ Finset.univ.filter (fun i => g i ≠ 0), v i) =
          ∑ i, g i • v i := by
        rw [Finset.sum_filter]
        apply Finset.sum_congr rfl
        intro i _
        rcases F2Bits.f2_eq_zero_or_one (g i) with h01 | h01 <;> simp [h01]
      _ = 0 := hsum

/-- Cardinal minimization produces a genuinely inclusion-minimal relation. -/
theorem exists_minimal_nonempty_zero_sum
    {ι M : Type*} [DecidableEq ι] [AddCommMonoid M]
    (v : ι → M) (S : Finset ι) (hS : S.Nonempty) (hsum : ∑ i ∈ S, v i = 0) :
    ∃ T ⊆ S, T.Nonempty ∧ (∑ i ∈ T, v i = 0) ∧
      ∀ U : Finset ι, U ⊂ T → U.Nonempty → ∑ i ∈ U, v i ≠ 0 := by
  classical
  have hex : ∃ k : ℕ, ∃ T : Finset ι,
      T ⊆ S ∧ T.Nonempty ∧ (∑ i ∈ T, v i = 0) ∧ T.card = k :=
    ⟨S.card, S, Finset.Subset.refl S, hS, hsum, rfl⟩
  obtain ⟨T, hTS, hT, hsumT, hcard⟩ := Nat.find_spec hex
  refine ⟨T, hTS, hT, hsumT, ?_⟩
  intro U hUT hU hsumU
  have hmin : Nat.find hex ≤ U.card :=
    Nat.find_min' hex ⟨U, hUT.1.trans hTS, hU, hsumU, rfl⟩
  have hlt := Finset.card_lt_card hUT
  omega

end

end AgtXIv.Stabilizer

namespace AgtXIv.Varela.MeasurementWindow

open AgtXIv.Stabilizer AgtXIv.Stabilizerness

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

/-- An arbitrary fixed order is sufficient; scalarity is proved order independent below. -/
def subsetProduct (T : Finset (Fin m)) : Pauli n :=
  (T.toList.map W.observable).prod

theorem support_subsetProduct (T : Finset (Fin m)) :
    F2Support.pauli (W.subsetProduct T) = ∑ i ∈ T, F2Support.pauli (W.observable i) := by
  rw [subsetProduct, support_list_product, Finset.sum_map_toList]

theorem scalar_subsetProduct_iff_zero_sum (T : Finset (Fin m)) :
    IsScalarPauli (W.subsetProduct T) ↔ ∑ i ∈ T, F2Support.pauli (W.observable i) = 0 := by
  rw [← support_eq_zero_iff_scalar, W.support_subsetProduct]

/-- Every repetition-free ordering of exactly T has the same scalarity test. -/
theorem scalar_product_iff_for_any_order (T : Finset (Fin m))
    (l : List (Fin m)) (hNodup : l.Nodup) (hSet : l.toFinset = T) :
    IsScalarPauli (l.map W.observable).prod ↔ IsScalarPauli (W.subsetProduct T) := by
  rw [← support_eq_zero_iff_scalar, support_list_product,
    ← List.sum_toFinset _ hNodup, hSet, ← W.scalar_subsetProduct_iff_zero_sum]

/-- The paper's nonempty inclusion-minimal proportional-identity relation. -/
def IsPauliDependency (T : Finset (Fin m)) : Prop :=
  T.Nonempty ∧ IsScalarPauli (W.subsetProduct T) ∧
    ∀ U : Finset (Fin m), U ⊂ T → U.Nonempty → ¬ IsScalarPauli (W.subsetProduct U)

/-- The corresponding finite binary circuit, defined by support sums. -/
def IsBinaryDependency (T : Finset (Fin m)) : Prop :=
  T.Nonempty ∧ (∑ i ∈ T, F2Support.pauli (W.observable i) = 0) ∧
    ∀ U : Finset (Fin m), U ⊂ T → U.Nonempty →
      ∑ i ∈ U, F2Support.pauli (W.observable i) ≠ 0

theorem pauliDependency_iff_binaryDependency (T : Finset (Fin m)) :
    W.IsPauliDependency T ↔ W.IsBinaryDependency T := by
  simp only [IsPauliDependency, IsBinaryDependency, W.scalar_subsetProduct_iff_zero_sum]

/-- Activity adds pairwise commutation to the source-faithful minimal relation. -/
def IsActiveDependency (T : Finset (Fin m)) : Prop :=
  W.IsPauliDependency T ∧ W.IsCommutingContext T

def NoActiveDependencies : Prop :=
  ∀ T : Finset (Fin m), ¬ W.IsActiveDependency T

theorem exists_binaryDependency_subset_of_not_independent
    (S : Finset (Fin m))
    (h : ¬ LinearIndependent F2 (fun i : S => F2Support.pauli (W.observable i))) :
    ∃ T ⊆ S, W.IsBinaryDependency T := by
  classical
  obtain ⟨U, hU, hsumU⟩ := exists_nonempty_zero_sum_of_not_linearIndependent
    (fun i : S => F2Support.pauli (W.observable i)) h
  let T : Finset (Fin m) := U.image Subtype.val
  have hT : T.Nonempty := hU.image _
  have hTS : T ⊆ S := by
    intro i hi
    obtain ⟨j, _, rfl⟩ := Finset.mem_image.mp hi
    exact j.property
  have hsumT : ∑ i ∈ T, F2Support.pauli (W.observable i) = 0 := by
    rw [Finset.sum_image (fun _ _ _ _ h => Subtype.val_injective h)]
    exact hsumU
  obtain ⟨V, hVT, hV, hsumV, hminimal⟩ := exists_minimal_nonempty_zero_sum
    (fun i => F2Support.pauli (W.observable i)) T hT hsumT
  exact ⟨V, hVT.trans hTS, hV, hsumV, hminimal⟩

/-- The central forward implication: a dependent commuting context contains
an active minimal dependency, contradicting the paper's actual hypothesis. -/
theorem context_support_independent_of_noActiveDependencies
    (hNoActive : W.NoActiveDependencies) (S : Finset (Fin m))
    (hContext : W.IsCommutingContext S) :
    LinearIndependent F2 (fun i : S => F2Support.pauli (W.observable i)) := by
  classical
  by_contra h
  obtain ⟨T, hTS, hT⟩ := W.exists_binaryDependency_subset_of_not_independent S h
  apply hNoActive T
  refine ⟨(W.pauliDependency_iff_binaryDependency T).mpr hT, ?_⟩
  intro i hi j hj hij
  exact hContext (hTS hi) (hTS hj) hij

theorem isAdmissibleSign_of_noActiveDependencies
    (hNoActive : W.NoActiveDependencies) (S : Finset (Fin m))
    (hContext : W.IsCommutingContext S) (f : Fin m → Bool) :
    W.IsAdmissibleSign S f := by
  exact W.isAdmissibleSign_of_support_independent S hContext
    (W.context_support_independent_of_noActiveDependencies hNoActive S hContext) f

theorem realAdmissibleSigns_eq_full_of_noActiveDependencies
    (hNoActive : W.NoActiveDependencies) (S : Finset (Fin m))
    (hContext : W.IsCommutingContext S) :
    W.realAdmissibleSigns S = {s : S → ℝ | ∀ i, IsSign (s i)} := by
  exact W.realAdmissibleSigns_eq_full_of_support_independent S hContext
    (W.context_support_independent_of_noActiveDependencies hNoActive S hContext)

theorem max_abs_context_signed_sum_of_noActiveDependencies
    (hNoActive : W.NoActiveDependencies) (S : Finset (Fin m))
    (hContext : W.IsCommutingContext S) (y : S → ℝ) (μ : ℝ) :
    IsGreatest (admissibleSignedValues (W.realAdmissibleSigns S) y μ)
      ((∑ i, |y i|) + |μ|) := by
  exact W.max_abs_context_signed_sum_of_support_independent S hContext
    (W.context_support_independent_of_noActiveDependencies hNoActive S hContext) y μ

end

end AgtXIv.Varela.MeasurementWindow
