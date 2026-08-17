import AgtXIvRootMath.F2Coordinates
import Mathlib.LinearAlgebra.Basis.VectorSpace
import Mathlib.LinearAlgebra.BilinearForm.Properties

/-!
# Constructive completion of an isotropic binary frame

This file proves a basis-level theorem needed by the Clifford-transitivity
direction of the Gottesman-to-Veitch bridge.  Given a linearly independent,
pairwise-isotropic family `g` in a finite-dimensional vector space over
`ZMod 2`, equipped with a nondegenerate symmetric alternating bilinear form,
we *construct* partners `h` satisfying

`B (g i) (h j) = δᵢⱼ`, `B (h i) (h j) = 0`.

The construction extends `g` to a basis, takes its bilinear dual family, and
then performs an explicit upper-triangular correction.  Thus the partner
witness is not an input assumption.  Applying this theorem to phase-free
Pauli support still requires separate proofs that the concrete support form is
nondegenerate and that a signed Pauli frame induces the required independent
isotropic family.  Lifting the resulting binary change of coordinates to an
actual phase-aware unitary Clifford is also a later theorem.
-/

namespace AgtXIv.Stabilizer

noncomputable section

open Module

section ExtendedBasis

variable {K V : Type*} [Field K] [AddCommGroup V] [Module K V]
variable {n : Nat}

/-- Extend a linearly independent family to a basis.  The index type is kept
abstract because only the original generator indices are used downstream. -/
def extendedBasis (g : Fin n → V) (hg : LinearIndependent K g) :
    Basis (hg.linearIndepOn_id.extend (Set.subset_univ _)) K V :=
  Basis.extend hg.linearIndepOn_id

/-- Embed an original generator index into the extended-basis index. -/
def generatorIndex (g : Fin n → V) (hg : LinearIndependent K g) (i : Fin n) :
    hg.linearIndepOn_id.extend (Set.subset_univ _) :=
  ⟨g i, hg.linearIndepOn_id.subset_extend (Set.subset_univ _) (Set.mem_range_self i)⟩

@[simp] theorem extendedBasis_generatorIndex (g : Fin n → V)
    (hg : LinearIndependent K g) (i : Fin n) :
    extendedBasis g hg (generatorIndex g hg i) = g i := by
  exact Basis.extend_apply_self hg.linearIndepOn_id _

theorem generatorIndex_injective (g : Fin n → V) (hg : LinearIndependent K g) :
    Function.Injective (generatorIndex g hg) := by
  intro i j h
  apply hg.injective
  exact congrArg Subtype.val h

variable [FiniteDimensional K V]

/-- Raw bilinear-dual partner of an original generator. -/
def rawPartner (B : LinearMap.BilinForm K V) (hB : B.Nondegenerate)
    (g : Fin n → V) (hg : LinearIndependent K g) (i : Fin n) : V :=
  let b := extendedBasis g hg
  letI := FiniteDimensional.fintypeBasisIndex b
  letI := Classical.decEq (hg.linearIndepOn_id.extend (Set.subset_univ _))
  B.dualBasis hB b (generatorIndex g hg i)

/-- Raw partners have the required Kronecker pairing with the original
family.  They need not yet be mutually isotropic. -/
theorem pair_rawPartner (B : LinearMap.BilinForm K V) (hB : B.Nondegenerate)
    (hSymm : B.IsSymm) (g : Fin n → V) (hg : LinearIndependent K g)
    (i j : Fin n) :
    B (g i) (rawPartner B hB g hg j) = if i = j then 1 else 0 := by
  let b := extendedBasis g hg
  letI := FiniteDimensional.fintypeBasisIndex b
  letI := Classical.decEq (hg.linearIndepOn_id.extend (Set.subset_univ _))
  have h := B.apply_dualBasis_right hB hSymm b
    (generatorIndex g hg i) (generatorIndex g hg j)
  rw [show extendedBasis g hg (generatorIndex g hg i) = g i by simp] at h
  simpa [b, rawPartner, (generatorIndex_injective g hg).eq_iff] using h

end ExtendedBasis

section BinaryCompletion

variable {W : Type*} [AddCommGroup W] [Module F2 W]
variable [FiniteDimensional F2 W]
variable {n : Nat}

/-- Upper-triangular correction that cancels pairings among the raw dual
partners without changing their pairings with `g`. -/
def partnerCorrection (B : LinearMap.BilinForm F2 W) (hB : B.Nondegenerate)
    (g : Fin n → W) (hg : LinearIndependent F2 g) (i : Fin n) : W :=
  ∑ k : Fin n, (if i < k then B (rawPartner B hB g hg i) (rawPartner B hB g hg k)
    else 0) • g k

/-- Corrected partner family. -/
def correctedPartner (B : LinearMap.BilinForm F2 W) (hB : B.Nondegenerate)
    (g : Fin n → W) (hg : LinearIndependent F2 g) (i : Fin n) : W :=
  rawPartner B hB g hg i + partnerCorrection B hB g hg i

/-- The correction preserves the Kronecker pairing with the original
isotropic family. -/
theorem pair_correctedPartner
    (B : LinearMap.BilinForm F2 W) (hB : B.Nondegenerate) (hSymm : B.IsSymm)
    (g : Fin n → W) (hg : LinearIndependent F2 g)
    (hIso : ∀ i j, B (g i) (g j) = 0) (i j : Fin n) :
    B (g i) (correctedPartner B hB g hg j) = if i = j then 1 else 0 := by
  simp only [correctedPartner, partnerCorrection, map_add, map_sum,
    LinearMapClass.map_smul]
  rw [pair_rawPartner B hB hSymm g hg i j]
  simp [hIso]

/-- Corrected partners are pairwise isotropic. -/
theorem correctedPartner_pair
    (B : LinearMap.BilinForm F2 W) (hB : B.Nondegenerate) (hSymm : B.IsSymm)
    (hAlt : ∀ x, B x x = 0)
    (g : Fin n → W) (hg : LinearIndependent F2 g)
    (hIso : ∀ i j, B (g i) (g j) = 0) (i j : Fin n) :
    B (correctedPartner B hB g hg i) (correctedPartner B hB g hg j) = 0 := by
  have hgr (a b : Fin n) :
      B (g a) (rawPartner B hB g hg b) = if a = b then 1 else 0 :=
    pair_rawPartner B hB hSymm g hg a b
  have hrg (a b : Fin n) :
      B (rawPartner B hB g hg a) (g b) = if b = a then 1 else 0 := by
    rw [hSymm.eq]
    exact hgr b a
  have hRawCorrection (a b : Fin n) :
      B (rawPartner B hB g hg a) (partnerCorrection B hB g hg b) =
        if b < a then B (rawPartner B hB g hg b) (rawPartner B hB g hg a) else 0 := by
    unfold partnerCorrection
    rw [map_sum]
    simp only [LinearMapClass.map_smul, hrg]
    simp
  have hCorrectionRaw (a b : Fin n) :
      B (partnerCorrection B hB g hg a) (rawPartner B hB g hg b) =
        if a < b then B (rawPartner B hB g hg a) (rawPartner B hB g hg b) else 0 := by
    rw [hSymm.eq, hRawCorrection]
  have hGCorrection (a b : Fin n) :
      B (g a) (partnerCorrection B hB g hg b) = 0 := by
    unfold partnerCorrection
    rw [map_sum]
    simp only [LinearMapClass.map_smul, hIso, smul_zero, Finset.sum_const_zero]
  have hCorrectionCorrection (a b : Fin n) :
      B (partnerCorrection B hB g hg a) (partnerCorrection B hB g hg b) = 0 := by
    change B (∑ k : Fin n,
      (if a < k then B (rawPartner B hB g hg a) (rawPartner B hB g hg k) else 0) • g k)
      (partnerCorrection B hB g hg b) = 0
    change B.flip _ _ = 0
    rw [map_sum]
    simp only [LinearMapClass.map_smul, LinearMap.BilinForm.flip_apply,
      hGCorrection, smul_zero, Finset.sum_const_zero]
  simp only [correctedPartner, map_add, LinearMap.add_apply, hRawCorrection,
    hCorrectionRaw, hCorrectionCorrection, add_zero]
  have hadd (x : F2) : x + x = 0 := by
    calc
      x + x = (2 : F2) * x := (two_mul x).symm
      _ = 0 := by rw [show (2 : F2) = 0 by decide, zero_mul]
  rcases lt_trichotomy i j with hij | hij | hij
  · simp only [hij, if_true, not_lt_of_ge hij.le, if_false]
    simp only [add_zero]
    exact hadd _
  · subst j
    simp [hAlt]
  · simp only [hij, if_true, not_lt_of_ge hij.le, if_false]
    simp only [add_zero]
    rw [hSymm.eq (rawPartner B hB g hg i) (rawPartner B hB g hg j)]
    exact hadd _

/-- Constructive symplectic partner theorem.  The returned witness is the
explicit `correctedPartner`; it is not a premise. -/
theorem exists_isotropic_dualPartners
    (B : LinearMap.BilinForm F2 W) (hB : B.Nondegenerate) (hSymm : B.IsSymm)
    (hAlt : ∀ x, B x x = 0)
    (g : Fin n → W) (hg : LinearIndependent F2 g)
    (hIso : ∀ i j, B (g i) (g j) = 0) :
    ∃ h : Fin n → W,
      (∀ i j, B (g i) (h j) = if i = j then 1 else 0) ∧
      (∀ i j, B (h i) (h j) = 0) := by
  refine ⟨correctedPartner B hB g hg, ?_, ?_⟩
  · exact pair_correctedPartner B hB hSymm g hg hIso
  · exact correctedPartner_pair B hB hSymm hAlt g hg hIso

end BinaryCompletion

end
end AgtXIv.Stabilizer
