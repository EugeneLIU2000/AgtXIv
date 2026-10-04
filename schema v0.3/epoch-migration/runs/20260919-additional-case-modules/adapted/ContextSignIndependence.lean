import AgtXIvStabilizerness.AdmissibleSigns
import AgtXIvRootMath.PauliSupportWord
import AgtXIvRootMath.GottesmanGeneratorFixedSpace

/-!
Independent binary Pauli supports imply unrestricted signs in a commuting
measurement context. The conclusion uses the existing phase-aware definition:
the generated signed Pauli subgroup excludes -I. No sign-domain collapse is
assumed. The real sign functions are defined only on the context subtype.

Source: arXiv:2607.26154v1 draft.tex:134--155 (contexts and admissible signs),
223--231 (active-dependency condition), and 615--625 (sign optimization).
Relating the paper's minimal-active-dependency definition to the explicit
binary linear-independence premise remains a separate source-alignment proof.
This independent module uses the original cached Lean 4.30.0-rc2 epoch.
-/

namespace AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators

open scoped BigOperators

variable {n r : ℕ}

/-- Independent support columns distinguish all binary Pauli words, including
their phases, since equality of Paulis implies equality of their supports. -/
theorem wordProduct_injective_of_support_independent
    (G : CommutingInvolutivePauliGenerators n r)
    (hIndependent : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i))) :
    Function.Injective G.wordProduct := by
  intro a b hab
  have hs := congrArg F2Support.pauli hab
  rw [G.support_wordProduct, G.support_wordProduct] at hs
  apply Multiplicative.toAdd.injective
  exact funext ((Fintype.linearIndependent_iffₛ.mp hIndependent) a.toAdd b.toAdd hs)

/-- Zero binary support forces the empty word; its actual phase is +I, not -I. -/
theorem wordProduct_ne_minus_one_of_support_independent
    (G : CommutingInvolutivePauliGenerators n r)
    (hIndependent : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i)))
    (a : BinaryWord r) : G.wordProduct a ≠ -(1 : Pauli n) := by
  intro ha
  have hs := congrArg F2Support.pauli ha
  have hs0 : (∑ i : Fin r, a.toAdd i • F2Support.pauli (G.generator i)) =
      ∑ i : Fin r, (0 : Fin r → F2) i • F2Support.pauli (G.generator i) := by
    simpa [G.support_wordProduct, Pauli.neg_eq] using hs
  have ha0 : a.toAdd = 0 :=
    funext ((Fintype.linearIndependent_iffₛ.mp hIndependent) a.toAdd 0 hs0)
  have ha1 : a = 1 := Multiplicative.toAdd.injective ha0
  subst a
  have hm := congrArg Pauli.m ha
  simp [G.wordProduct_one, Pauli.addPhase] at hm
  exact (by decide : (0 : ZMod 4) ≠ 2) hm

/-- Each generator is a basis word, so its generated subgroup is contained in
the range of the actual word homomorphism. -/
theorem closure_generators_le_wordProduct_range
    (G : CommutingInvolutivePauliGenerators n r) :
    Subgroup.closure (Set.range G.generator) ≤ G.wordProductHom.range := by
  apply (Subgroup.closure_le _).2
  rintro P ⟨i, rfl⟩
  exact ⟨basisWord i, G.wordProduct_basisWord i⟩

theorem minus_one_not_mem_closure_of_support_independent
    (G : CommutingInvolutivePauliGenerators n r)
    (hIndependent : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i))) :
    -(1 : Pauli n) ∉ Subgroup.closure (Set.range G.generator) := by
  intro hm
  obtain ⟨a, ha⟩ := G.closure_generators_le_wordProduct_range hm
  exact G.wordProduct_ne_minus_one_of_support_independent hIndependent a ha

end AgtXIv.Stabilizer.CommutingInvolutivePauliGenerators

namespace AgtXIv.Varela.MeasurementWindow

open scoped BigOperators
open AgtXIv.Stabilizer AgtXIv.Stabilizerness

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

theorem support_signedObservable (f : Fin m → Bool) (i : Fin m) :
    F2Support.pauli (W.signedObservable f i) = F2Support.pauli (W.observable i) := by
  cases hf : f i <;> simp [signedObservable, hf, Pauli.neg_eq]

theorem signedObservable_involutive (f : Fin m → Bool) (i : Fin m) :
    W.signedObservable f i ^ 2 = 1 := by
  cases hf : f i
  · simpa [signedObservable, hf] using W.involutive i
  · simpa [signedObservable, hf, Pauli.neg_eq, pow_two,
      show (2 : ZMod 4) + 2 = 0 by decide] using W.involutive i

theorem signedObservable_commutesWith (f : Fin m → Bool) (i j : Fin m) :
    (W.signedObservable f i).commutesWith (W.signedObservable f j) =
      (W.observable i).commutesWith (W.observable j) := by
  cases hi : f i <;> cases hj : f j <;>
    simp [signedObservable, hi, hj, Pauli.commutesWith, Pauli.phaseFlipsWith]

theorem commute_signedObservable_of_context (S : Finset (Fin m))
    (hContext : W.IsCommutingContext S) (f : Fin m → Bool)
    {i j : Fin m} (hi : i ∈ S) (hj : j ∈ S) :
    Commute (W.signedObservable f i) (W.signedObservable f j) := by
  by_cases hij : i = j
  · subst j
    exact Commute.refl _
  · apply Pauli.commute_of_commutesWith
    rw [W.signedObservable_commutesWith]
    exact hContext hi hj hij

/-- Enumerate precisely the selected context, with no maximality assumption. -/
def contextEnumeration (S : Finset (Fin m)) : Fin S.card ≃ S :=
  (Fintype.equivFinOfCardEq (show Fintype.card S = S.card by simp)).symm

/-- A commuting context with any Boolean sign table gives actual involutive
Pauli generators; support independence is not needed for this construction. -/
def signedContextGenerators (S : Finset (Fin m)) (hContext : W.IsCommutingContext S)
    (f : Fin m → Bool) : CommutingInvolutivePauliGenerators n S.card where
  generator i := W.signedObservable f (contextEnumeration S i)
  involutive i := W.signedObservable_involutive f _
  commute i j := W.commute_signedObservable_of_context S hContext f
    (contextEnumeration S i).property (contextEnumeration S j).property

theorem signedContextGenerators_support_independent
    (S : Finset (Fin m)) (hContext : W.IsCommutingContext S)
    (hIndependent : LinearIndependent F2 (fun i : S => F2Support.pauli (W.observable i)))
    (f : Fin m → Bool) :
    LinearIndependent F2
      (fun i => F2Support.pauli ((W.signedContextGenerators S hContext f).generator i)) := by
  simpa [signedContextGenerators, W.support_signedObservable, Function.comp_def] using
    hIndependent.comp (contextEnumeration S) (contextEnumeration S).injective

theorem signedContextSet_eq_generator_range
    (S : Finset (Fin m)) (hContext : W.IsCommutingContext S) (f : Fin m → Bool) :
    W.signedContextSet S f = Set.range (W.signedContextGenerators S hContext f).generator := by
  ext Q
  constructor
  · rintro ⟨i, hi, hQ⟩
    refine ⟨(contextEnumeration S).symm ⟨i, hi⟩, ?_⟩
    simpa [signedContextGenerators] using hQ.symm
  · rintro ⟨j, rfl⟩
    exact ⟨contextEnumeration S j, (contextEnumeration S j).property, rfl⟩

/-- Binary support independence is a concrete sufficient condition for every
Boolean sign assignment to satisfy the existing phase-aware admissibility. -/
theorem isAdmissibleSign_of_support_independent
    (S : Finset (Fin m)) (hContext : W.IsCommutingContext S)
    (hIndependent : LinearIndependent F2 (fun i : S => F2Support.pauli (W.observable i)))
    (f : Fin m → Bool) : W.IsAdmissibleSign S f := by
  unfold IsAdmissibleSign
  rw [W.signedContextSet_eq_generator_range S hContext f]
  exact (W.signedContextGenerators S hContext f).minus_one_not_mem_closure_of_support_independent
    (W.signedContextGenerators_support_independent S hContext hIndependent f)

/-- Real deterministic signs restricted to the context, with a phase-admissible
Boolean extension to the measurement window. Off-context coordinates are not
optimization variables. -/
def realAdmissibleSigns (S : Finset (Fin m)) : Set (S → ℝ) :=
  {s | ∃ f : Fin m → Bool, W.IsAdmissibleSign S f ∧
    ∀ i : S, s i = if f i then -1 else 1}

/-- The real sign domain is derived from support independence; no domain
equality or no-active-dependency assertion is used as a premise. -/
theorem realAdmissibleSigns_eq_full_of_support_independent
    (S : Finset (Fin m)) (hContext : W.IsCommutingContext S)
    (hIndependent : LinearIndependent F2 (fun i : S => F2Support.pauli (W.observable i))) :
    W.realAdmissibleSigns S = {s : S → ℝ | ∀ i, IsSign (s i)} := by
  classical
  ext s
  constructor
  · rintro ⟨f, _, hValues⟩ i
    rw [hValues i]
    cases f i <;> simp [IsSign]
  · intro hs
    let f : Fin m → Bool := fun i =>
      if hi : i ∈ S then if s ⟨i, hi⟩ = -1 then true else false else false
    refine ⟨f, W.isAdmissibleSign_of_support_independent S hContext hIndependent f, ?_⟩
    intro i
    rcases hs i with hPos | hNeg
    · simp [f, i.property, hPos]
    · simp [f, i.property, hNeg]

/-- The paper's absolute signed-sum maximum follows for an actual commuting
context with independent binary supports, over precisely its admissible signs. -/
theorem max_abs_context_signed_sum_of_support_independent
    (S : Finset (Fin m)) (hContext : W.IsCommutingContext S)
    (hIndependent : LinearIndependent F2 (fun i : S => F2Support.pauli (W.observable i)))
    (y : S → ℝ) (μ : ℝ) :
    IsGreatest (admissibleSignedValues (W.realAdmissibleSigns S) y μ)
      ((∑ i, |y i|) + |μ|) := by
  exact max_abs_admissible_signed_sum_of_sign_set_eq (W.realAdmissibleSigns S) y μ
    (W.realAdmissibleSigns_eq_full_of_support_independent S hContext hIndependent)

end

end AgtXIv.Varela.MeasurementWindow
