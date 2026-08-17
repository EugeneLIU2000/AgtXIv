import AgtXIvRootMath.PauliSupportWord

/-!
# Exact dual Pauli frame from constructive symplectic completion

For every complete signed Pauli frame `F`, the binary completion theorem has
already constructed mutually commuting dual supports.  This module lifts each
dual support to the canonical Hermitian Pauli representative, proves the
resulting subset-product map is independent and excludes `-I`, and packages it
as another exact signed frame.

The central result is an exact Weyl relation for arbitrary binary words: an
`F` word and a dual-frame word commute or anticommute according to their
binary dot product.  Thus the phase/sign information needed by the later
syndrome-basis Clifford construction is proved here, not inferred from the
phase-free support map.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators
noncomputable section

namespace IndependentSignedPauliFrame

variable {n : ℕ}

/-- Constructively chosen dual supports from `exists_support_dualPartners`. -/
def dualSupport (F : IndependentSignedPauliFrame n n) :
    Fin n → F2Support n :=
  Classical.choose F.exists_support_dualPartners

/-- Original and dual supports have the exact Kronecker pairing. -/
theorem dualSupport_pair (F : IndependentSignedPauliFrame n n) (i j : Fin n) :
    F2Support.symplecticForm (F.generatorSupport i) (F.dualSupport j) =
      if i = j then 1 else 0 :=
  (Classical.choose_spec F.exists_support_dualPartners).1 i j

/-- The constructed dual supports are mutually isotropic. -/
theorem dualSupport_isotropic (F : IndependentSignedPauliFrame n n) (i j : Fin n) :
    F2Support.symplecticForm (F.dualSupport i) (F.dualSupport j) = 0 :=
  (Classical.choose_spec F.exists_support_dualPartners).2 i j

/-- Phase-aware Hermitian involution realizing a constructed dual support. -/
def dualPauli (F : IndependentSignedPauliFrame n n) (i : Fin n) : Pauli n :=
  hermitianSupportPauli ((F.dualSupport i).1.bits, (F.dualSupport i).2.bits)

@[simp] theorem dualPauli_support
    (F : IndependentSignedPauliFrame n n) (i : Fin n) :
    F2Support.pauli (F.dualPauli i) = F.dualSupport i := by
  apply Prod.ext <;> apply F2Bits.ext <;>
    simp [dualPauli, F2Support.pauli]

@[simp] theorem dualPauli_sq
    (F : IndependentSignedPauliFrame n n) (i : Fin n) :
    F.dualPauli i ^ 2 = 1 := by
  exact hermitianSupportPauli_sq _

/-- Mutual support isotropy lifts to exact commutation of the signed Hermitian
representatives. -/
theorem dualPauli_commute
    (F : IndependentSignedPauliFrame n n) (i j : Fin n) :
    Commute (F.dualPauli i) (F.dualPauli j) := by
  apply (Pauli.commutesWith_iff _ _).mp
  apply (F2Support.pauli_commutes_iff_symplectic_eq_zero _ _).mpr
  simpa using F.dualSupport_isotropic i j

/-- Source-level commuting involutive generators for the dual directions. -/
def dualGenerators (F : IndependentSignedPauliFrame n n) :
    CommutingInvolutivePauliGenerators n n where
  generator := F.dualPauli
  involutive := F.dualPauli_sq
  commute := F.dualPauli_commute

@[simp] theorem support_dualWord
    (F : IndependentSignedPauliFrame n n) (a : BinaryWord n) :
    F2Support.pauli (F.dualGenerators.wordProduct a) =
      ∑ i : Fin n, a.toAdd i • F.dualSupport i := by
  rw [F.dualGenerators.support_wordProduct]
  apply Finset.sum_congr rfl
  intro i _
  change a.toAdd i • F2Support.pauli (F.dualPauli i) =
    a.toAdd i • F.dualSupport i
  rw [F.dualPauli_support]

/-- The support map is reconstructed from its values on the standard binary
basis. -/
theorem supportLinear_eq_sum_generatorSupport
    (F : IndependentSignedPauliFrame n n) (a : Fin n → F2) :
    F.supportLinear a = ∑ i, a i • F.generatorSupport i := by
  have hrepr : ∑ i, a i • Pi.basisFun F2 (Fin n) i = a := by
    simpa using (Pi.basisFun F2 (Fin n)).sum_repr a
  calc
    F.supportLinear a =
        F.supportLinear (∑ i, a i • Pi.basisFun F2 (Fin n) i) :=
      congrArg F.supportLinear hrepr.symm
    _ = ∑ i, a i • F.generatorSupport i := by
      rw [map_sum]
      simp [generatorSupport]

/-- The dual word map is itself a complete independent signed Pauli frame.
Injectivity and `-I` exclusion are derived via the completed support-basis
equivalence rather than stored in the dual construction. -/
def dualFrame (F : IndependentSignedPauliFrame n n) :
    IndependentSignedPauliFrame n n where
  eval := F.dualGenerators.wordProductHom
  independent := by
    intro a b hab
    change F.dualGenerators.wordProduct a = F.dualGenerators.wordProduct b at hab
    have hs := congrArg F2Support.pauli hab
    rw [F.support_dualWord, F.support_dualWord] at hs
    have hmap : F.supportCompletionLinear F.dualSupport (0, a.toAdd) =
        F.supportCompletionLinear F.dualSupport (0, b.toAdd) := by
      simpa [supportCompletionLinear_apply] using hs
    have hab' := F.supportCompletionLinear_injective F.dualSupport
      F.dualSupport_pair F.dualSupport_isotropic hmap
    apply Multiplicative.toAdd.injective
    exact congrArg Prod.snd hab'
  minusOneExcluded := by
    intro a ha
    change F.dualGenerators.wordProduct a = -(1 : Pauli n) at ha
    have hs := congrArg F2Support.pauli ha
    have hs0 : ∑ i : Fin n, a.toAdd i • F.dualSupport i = 0 := by
      simpa [F.support_dualWord] using hs
    have hmap : F.supportCompletionLinear F.dualSupport (0, a.toAdd) =
        F.supportCompletionLinear F.dualSupport (0, 0) := by
      simpa [supportCompletionLinear_apply] using hs0
    have ha0 := F.supportCompletionLinear_injective F.dualSupport
      F.dualSupport_pair F.dualSupport_isotropic hmap
    have ha1 : a = 1 := by
      apply Multiplicative.toAdd.injective
      simpa using congrArg Prod.snd ha0
    subst a
    have hm := congrArg Pauli.m ha
    simp [CommutingInvolutivePauliGenerators.wordProduct_one,
      Pauli.addPhase] at hm
    exact (by decide : (0 : ZMod 4) ≠ 2) hm

@[simp] theorem dualFrame_eval
    (F : IndependentSignedPauliFrame n n) (a : BinaryWord n) :
    F.dualFrame.eval a = F.dualGenerators.wordProduct a := rfl

/-- Binary dot product controlling the read/flip commutation sign. -/
def binaryDot (a b : BinaryWord n) : F2 :=
  ∑ i, a.toAdd i * b.toAdd i

@[simp] theorem support_eval
    (F : IndependentSignedPauliFrame n n) (a : BinaryWord n) :
    F2Support.pauli (F.eval a) =
      ∑ i : Fin n, a.toAdd i • F.generatorSupport i := by
  rw [← F.supportLinear_eq_sum_generatorSupport]
  rfl

/-- Arbitrary original and dual words pair by their binary coefficient dot
product. -/
theorem eval_dualFrame_symplectic
    (F : IndependentSignedPauliFrame n n) (a b : BinaryWord n) :
    F2Support.symplecticForm (F2Support.pauli (F.eval a))
      (F2Support.pauli (F.dualFrame.eval b)) = binaryDot a b := by
  have hfirst :
      F.supportCompletionLinear F.dualSupport (a.toAdd, 0) =
        F2Support.pauli (F.eval a) := by
    rw [supportCompletionLinear_apply, F.support_eval]
    simp
  have hsecond :
      F.supportCompletionLinear F.dualSupport (0, b.toAdd) =
        F2Support.pauli (F.dualFrame.eval b) := by
    rw [supportCompletionLinear_apply, F.dualFrame_eval, F.support_dualWord]
    simp
  rw [← hfirst, ← hsecond]
  rw [F.supportCompletionLinear_symplectic F.dualSupport
    F.dualSupport_pair F.dualSupport_isotropic]
  simp [coordinateSymplectic, binaryDot]

theorem eval_dualFrame_commutes_iff
    (F : IndependentSignedPauliFrame n n) (a b : BinaryWord n) :
    (F.eval a).commutesWith (F.dualFrame.eval b) = true ↔
      binaryDot a b = 0 := by
  rw [F2Support.pauli_commutes_iff_symplectic_eq_zero]
  rw [F.eval_dualFrame_symplectic]

/-- Exact phase-aware Weyl relation.  A nonzero binary dot product is exactly
one in `ZMod 2`, hence gives a literal Pauli-group minus sign. -/
theorem eval_mul_dualFrame_eval
    (F : IndependentSignedPauliFrame n n) (a b : BinaryWord n) :
    F.eval a * F.dualFrame.eval b =
      if binaryDot a b = 0 then
        F.dualFrame.eval b * F.eval a
      else -(F.dualFrame.eval b * F.eval a) := by
  by_cases hd : binaryDot a b = 0
  · rw [if_pos hd]
    exact ((Pauli.commutesWith_iff _ _).mp
      ((F.eval_dualFrame_commutes_iff a b).mpr hd)).eq
  · rw [if_neg hd]
    apply Pauli.mul_anticomm_of_not_commutesWith
    intro hc
    exact hd ((F.eval_dualFrame_commutes_iff a b).mp hc)

end IndependentSignedPauliFrame

end
end AgtXIv.Stabilizer
