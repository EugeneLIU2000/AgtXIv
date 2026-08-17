import AgtXIvRootMath.F2SymplecticNondegenerate
import AgtXIvRootMath.SymplecticCompletion
import AgtXIvRootMath.GottesmanConcretePauliFrame
import Mathlib.LinearAlgebra.StdBasis

/-!
# Constructive binary completion of an actual signed Pauli frame

An `IndependentSignedPauliFrame` is phase-aware: its binary labels evaluate
to actual LeanQuantum Paulis, and its assumptions exclude a hidden `-I`.
This file maps that exact frame into the phase-free binary support space and
proves, rather than assumes, the hypotheses of `exists_isotropic_dualPartners`:

* the support map from all binary labels is an injective linear map;
* the support vectors of the individual labels are linearly independent;
* those vectors are pairwise isotropic because the evaluated Pauli words
  commute;
* a mutually isotropic dual-partner family therefore exists by the explicit
  correction construction in `SymplecticCompletion`.

This is a constructive symplectic-completion result in the binary commutation
ledger.  It still does not lift the resulting binary coordinates to a unitary
Clifford or repair the signs of the evaluated Paulis.
-/

namespace AgtXIv.Stabilizer

noncomputable section

namespace IndependentSignedPauliFrame

variable {n r : ℕ}

/-- Binary support of the evaluated Pauli word, as a linear map from its
additive label coordinates. -/
def supportLinear (F : IndependentSignedPauliFrame n r) :
    (Fin r → F2) →ₗ[F2] F2Support n where
  toFun a := F2Support.pauli (F.eval (Multiplicative.ofAdd a))
  map_add' a b := by
    change F2Support.pauli (F.eval (Multiplicative.ofAdd (a + b))) = _
    rw [show Multiplicative.ofAdd (a + b) =
      Multiplicative.ofAdd a * Multiplicative.ofAdd b by rfl]
    rw [map_mul, F2Support.pauli_mul]
  map_smul' c a := by
    rcases F2Bits.f2_eq_zero_or_one c with rfl | rfl
    · simp [F2Support.pauli_one]
    · simp

@[simp] theorem supportLinear_apply (F : IndependentSignedPauliFrame n r)
    (a : Fin r → F2) :
    F.supportLinear a =
      F2Support.pauli (F.eval (Multiplicative.ofAdd a)) := rfl

/-- Phase-aware word independence and `-I` exclusion imply that forgetting
phase is still injective on the evaluated binary frame. -/
theorem supportLinear_injective (F : IndependentSignedPauliFrame n r) :
    Function.Injective F.supportLinear := by
  apply (injective_iff_map_eq_zero F.supportLinear.toAddMonoidHom).mpr
  intro a ha
  have hz : (F.eval (Multiplicative.ofAdd a)).z = 0 := by
    have h := congrArg (fun u : F2Support n => u.1.bits) ha
    simpa [supportLinear, F2Support.pauli] using h
  have hx : (F.eval (Multiplicative.ofAdd a)).x = 0 := by
    have h := congrArg (fun u : F2Support n => u.2.bits) ha
    simpa [supportLinear, F2Support.pauli] using h
  have hone := F.scalar_support_implies_label_one (Multiplicative.ofAdd a) hz hx
  have hadd := congrArg Multiplicative.toAdd hone
  simpa using hadd

/-- Support vector of the Pauli word selected by the `i`th standard binary
label. -/
def generatorSupport (F : IndependentSignedPauliFrame n r) (i : Fin r) :
    F2Support n :=
  F.supportLinear (Pi.basisFun F2 (Fin r) i)

/-- The individual generator supports are linearly independent.  This is a
conclusion from exact signed-frame independence, not an additional field. -/
theorem generatorSupport_linearIndependent
    (F : IndependentSignedPauliFrame n r) :
    LinearIndependent F2 F.generatorSupport := by
  have hker : LinearMap.ker F.supportLinear = ⊥ :=
    LinearMap.ker_eq_bot.mpr F.supportLinear_injective
  have h := (Pi.basisFun F2 (Fin r)).linearIndependent.map'
    F.supportLinear hker
  simpa only [generatorSupport, Function.comp_apply] using h

/-- All evaluated frame words commute because their label group is
commutative and evaluation is a homomorphism. -/
theorem eval_words_commute (F : IndependentSignedPauliFrame n r)
    (a b : Fin r → F2) :
    Commute (F.eval (Multiplicative.ofAdd a))
      (F.eval (Multiplicative.ofAdd b)) := by
  rw [commute_iff_eq]
  calc
    F.eval (Multiplicative.ofAdd a) * F.eval (Multiplicative.ofAdd b) =
        F.eval (Multiplicative.ofAdd a * Multiplicative.ofAdd b) :=
      (map_mul F.eval _ _).symm
    _ = F.eval (Multiplicative.ofAdd b * Multiplicative.ofAdd a) := by
      rw [mul_comm]
    _ = F.eval (Multiplicative.ofAdd b) * F.eval (Multiplicative.ofAdd a) :=
      map_mul F.eval _ _

/-- The exact Pauli commutation bridge makes the generator supports
pairwise isotropic. -/
theorem generatorSupport_isotropic (F : IndependentSignedPauliFrame n r)
    (i j : Fin r) :
    F2Support.symplecticForm (F.generatorSupport i)
      (F.generatorSupport j) = 0 := by
  apply (F2Support.pauli_commutes_iff_symplectic_eq_zero _ _).mp
  exact (Pauli.commutesWith_iff _ _).mpr
    (F.eval_words_commute
      (Pi.basisFun F2 (Fin r) i) (Pi.basisFun F2 (Fin r) j))

/-- Construct mutually isotropic binary partners dual to every generator
support.  The partner family is an output witness, not an input assumption. -/
theorem exists_support_dualPartners
    (F : IndependentSignedPauliFrame n r) :
    ∃ h : Fin r → F2Support n,
      (∀ i j, F2Support.symplecticForm (F.generatorSupport i) (h j) =
        if i = j then 1 else 0) ∧
      (∀ i j, F2Support.symplecticForm (h i) (h j) = 0) := by
  apply exists_isotropic_dualPartners
    F2Support.symplecticForm
    (F2Support.symplecticForm_nondegenerate n)
    ⟨F2Support.symplectic_symm⟩
    F2Support.symplectic_alternating
    F.generatorSupport
    F.generatorSupport_linearIndependent
    F.generatorSupport_isotropic

end IndependentSignedPauliFrame

end

end AgtXIv.Stabilizer
