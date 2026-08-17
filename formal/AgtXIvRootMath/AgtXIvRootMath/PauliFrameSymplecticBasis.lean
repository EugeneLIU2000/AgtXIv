import AgtXIvRootMath.PauliFrameSupportCompletion
import Mathlib.LinearAlgebra.FiniteDimensional.Lemmas

/-!
# A symplectic coordinate basis from a complete signed Pauli frame

For a rank-`n` independent signed Pauli frame on `n` qubits, the preceding
completion theorem constructs binary partners `h`.  This file proves that the
original generator supports together with those partners form a basis of the
full `2n`-coordinate support space.  More precisely, their linear-combination
map is injective, hence (by the already proved coordinate equivalence and
equal finite dimension) a linear equivalence.  The equivalence preserves the
canonical binary symplectic pairing.

No unitary operator is constructed here.  This theorem is the support-level
coordinate change that a later phase-aware Clifford-lift theorem must realize.
-/

namespace AgtXIv.Stabilizer

noncomputable section

namespace IndependentSignedPauliFrame

variable {n : ℕ}

/-- Coefficients of `n` stabilizer-like directions and `n` dual directions. -/
abbrev SupportCoordinates (n : ℕ) :=
  (Fin n → F2) × (Fin n → F2)

/-- Linear combination of a complete frame support and a chosen dual-partner
family. -/
def supportCompletionLinear (F : IndependentSignedPauliFrame n n)
    (h : Fin n → F2Support n) :
    SupportCoordinates n →ₗ[F2] F2Support n :=
  (Fintype.linearCombination F2 F.generatorSupport).coprod
    (Fintype.linearCombination F2 h)

@[simp] theorem supportCompletionLinear_apply
    (F : IndependentSignedPauliFrame n n) (h : Fin n → F2Support n)
    (a : SupportCoordinates n) :
    F.supportCompletionLinear h a =
      (∑ i, a.1 i • F.generatorSupport i) + (∑ i, a.2 i • h i) := by
  simp [supportCompletionLinear, Fintype.linearCombination_apply]

/-- The first coordinate basis is sent to the original stabilizer supports. -/
@[simp] theorem supportCompletionLinear_firstBasis
    (F : IndependentSignedPauliFrame n n) (h : Fin n → F2Support n)
    (i : Fin n) :
    F.supportCompletionLinear h (Pi.basisFun F2 (Fin n) i, 0) =
      F.generatorSupport i := by
  simp [supportCompletionLinear_apply]

/-- The second coordinate basis is sent to the constructed partner supports. -/
@[simp] theorem supportCompletionLinear_secondBasis
    (F : IndependentSignedPauliFrame n n) (h : Fin n → F2Support n)
    (i : Fin n) :
    F.supportCompletionLinear h (0, Pi.basisFun F2 (Fin n) i) = h i := by
  simp [supportCompletionLinear_apply]

/-- The Kronecker pairings force every coefficient in the kernel to vanish. -/
theorem supportCompletionLinear_injective
    (F : IndependentSignedPauliFrame n n) (h : Fin n → F2Support n)
    (hDual : ∀ i j, F2Support.symplecticForm (F.generatorSupport i) (h j) =
      if i = j then 1 else 0)
    (hIso : ∀ i j, F2Support.symplecticForm (h i) (h j) = 0) :
    Function.Injective (F.supportCompletionLinear h) := by
  apply (injective_iff_map_eq_zero (F.supportCompletionLinear h).toAddMonoidHom).mpr
  intro a ha
  have ha1 : a.1 = 0 := by
    funext j
    have hz := congrArg (fun u : F2Support n =>
      F2Support.symplecticForm u (h j)) ha
    simpa [supportCompletionLinear_apply, hDual, hIso] using hz
  have hDualRev : ∀ i j,
      F2Support.symplecticForm (h i) (F.generatorSupport j) =
        if i = j then 1 else 0 := by
    intro i j
    rw [F2Support.symplectic_symm, hDual]
    simp only [eq_comm]
  have ha2 : a.2 = 0 := by
    funext j
    have hz := congrArg (fun u : F2Support n =>
      F2Support.symplecticForm u (F.generatorSupport j)) ha
    simpa [supportCompletionLinear_apply, F.generatorSupport_isotropic,
      hDualRev] using hz
  exact Prod.ext ha1 ha2

/-- The completed `2n` coordinate family is a basis of binary Pauli support.
Surjectivity is a conclusion from injectivity and the concrete coordinate
equivalence; it is not assumed. -/
def supportCompletionEquiv
    (F : IndependentSignedPauliFrame n n) (h : Fin n → F2Support n)
    (hDual : ∀ i j, F2Support.symplecticForm (F.generatorSupport i) (h j) =
      if i = j then 1 else 0)
    (hIso : ∀ i j, F2Support.symplecticForm (h i) (h j) = 0) :
    SupportCoordinates n ≃ₗ[F2] F2Support n :=
  (F.supportCompletionLinear h).linearEquivOfInjective
    (F.supportCompletionLinear_injective h hDual hIso)
    (F2Support.coordinateEquiv n).finrank_eq.symm

@[simp] theorem supportCompletionEquiv_apply
    (F : IndependentSignedPauliFrame n n) (h : Fin n → F2Support n)
    (hDual : ∀ i j, F2Support.symplecticForm (F.generatorSupport i) (h j) =
      if i = j then 1 else 0)
    (hIso : ∀ i j, F2Support.symplecticForm (h i) (h j) = 0)
    (a : SupportCoordinates n) :
    F.supportCompletionEquiv h hDual hIso a = F.supportCompletionLinear h a := rfl

/-- Canonical symplectic form on the two blocks of coefficient coordinates. -/
def coordinateSymplectic (a b : SupportCoordinates n) : F2 :=
  (∑ i, a.2 i * b.1 i) + (∑ i, a.1 i * b.2 i)

/-- The completed coordinate map preserves the binary symplectic pairing. -/
theorem supportCompletionLinear_symplectic
    (F : IndependentSignedPauliFrame n n) (h : Fin n → F2Support n)
    (hDual : ∀ i j, F2Support.symplecticForm (F.generatorSupport i) (h j) =
      if i = j then 1 else 0)
    (hIso : ∀ i j, F2Support.symplecticForm (h i) (h j) = 0)
    (a b : SupportCoordinates n) :
    F2Support.symplecticForm (F.supportCompletionLinear h a)
      (F.supportCompletionLinear h b) = coordinateSymplectic a b := by
  have hDualRev : ∀ i j,
      F2Support.symplecticForm (h i) (F.generatorSupport j) =
        if i = j then 1 else 0 := by
    intro i j
    rw [F2Support.symplectic_symm, hDual]
    simp only [eq_comm]
  simp only [supportCompletionLinear_apply, map_add, map_sum,
    LinearMapClass.map_smul]
  simp [F.generatorSupport_isotropic, hIso, hDual, hDualRev,
    coordinateSymplectic, mul_comm]

/-- Full support-level transitivity output.  Starting only from a complete
signed Pauli frame, construct dual supports and a symplectic coordinate
equivalence that sends each standard first-block basis vector to the
corresponding generator support. -/
theorem exists_support_symplecticEquiv
    (F : IndependentSignedPauliFrame n n) :
    ∃ (h : Fin n → F2Support n)
      (e : SupportCoordinates n ≃ₗ[F2] F2Support n),
      (∀ i j, F2Support.symplecticForm (F.generatorSupport i) (h j) =
        if i = j then 1 else 0) ∧
      (∀ i j, F2Support.symplecticForm (h i) (h j) = 0) ∧
      (∀ a, e a = F.supportCompletionLinear h a) ∧
      (∀ a b, F2Support.symplecticForm (e a) (e b) =
        coordinateSymplectic a b) := by
  obtain ⟨h, hDual, hIso⟩ := F.exists_support_dualPartners
  let e := F.supportCompletionEquiv h hDual hIso
  refine ⟨h, e, hDual, hIso, ?_, ?_⟩
  · intro a
    rfl
  · intro a b
    exact F.supportCompletionLinear_symplectic h hDual hIso a b

end IndependentSignedPauliFrame

end

end AgtXIv.Stabilizer
