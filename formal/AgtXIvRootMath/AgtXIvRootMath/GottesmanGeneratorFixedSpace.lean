import AgtXIvRootMath.GottesmanUniqueRay
import AgtXIvRootMath.GottesmanGeneralRankDimension
import Mathlib.Algebra.Group.Submonoid.BigOperators

/-!
# Source generators and the group common fixed space

Gottesman's joint `+1` eigenspace is stated using the individual commuting
Pauli generators.  The group-average development uses invariants of every
binary subset product.  This file proves that these are exactly the same
subspace; it does not identify them merely by terminology.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix
noncomputable section

namespace CommutingInvolutivePauliGenerators

variable {n r : ℕ}

/-- Binary label selecting exactly the `i`th source generator. -/
def basisWord (i : Fin r) : BinaryWord r :=
  Multiplicative.ofAdd (Pi.basisFun (ZMod 2) (Fin r) i)

@[simp]
theorem powered_basisWord (G : CommutingInvolutivePauliGenerators n r)
    (i j : Fin r) :
    G.powered (basisWord i) j = if j = i then G.generator j else 1 := by
  by_cases hji : j = i
  · subst j
    rw [if_pos rfl]
    unfold powered
    have hcoord : (basisWord i).toAdd i = (1 : ZMod 2) := by
      simp [basisWord, Pi.basisFun_apply]
    rw [hcoord]
    rw [show (1 : ZMod 2).val = 1 by decide]
    simp
  · simp [powered, basisWord, hji]

/-- The subset product at a standard binary label is the corresponding
source generator. -/
theorem wordProduct_basisWord
    (G : CommutingInvolutivePauliGenerators n r) (i : Fin r) :
    G.wordProduct (basisWord i) = G.generator i := by
  classical
  unfold wordProduct
  rw [← Finset.mul_noncommProd_erase Finset.univ (Finset.mem_univ i)]
  rw [powered_basisWord]
  rw [Finset.noncommProd_eq_pow_card _ _ _ (1 : Pauli n)]
  · simp
  · intro j hj
    have hji : j ≠ i := Finset.ne_of_mem_erase hj
    simp [hji]

/-- Individual-generator formulation of the exact common `+1` eigenspace. -/
def GeneratorsFix (G : CommutingInvolutivePauliGenerators n r)
    (psi : AgtXIv.Gottesman.QubitHilbert n) : Prop :=
  ∀ i, (G.generator i).toCMatrix *ᵥ psi = psi

/-- Signed Paulis fixing one vector form a multiplicative submonoid. -/
def vectorFixingPauliSubmonoid
    (psi : AgtXIv.Gottesman.QubitHilbert n) : Submonoid (Pauli n) where
  carrier := {P | P.toCMatrix *ᵥ psi = psi}
  one_mem' := by simp
  mul_mem' := by
    intro P Q hP hQ
    change (P * Q).toCMatrix *ᵥ psi = psi
    change P.toCMatrix *ᵥ psi = psi at hP
    change Q.toCMatrix *ᵥ psi = psi at hQ
    rw [Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix, ← Matrix.mulVec_mulVec,
      hQ, hP]

/-- Fixing every source generator fixes every binary subset product. -/
theorem wordProduct_mulVec_eq_of_generatorsFix
    (G : CommutingInvolutivePauliGenerators n r)
    (psi : AgtXIv.Gottesman.QubitHilbert n) (hpsi : G.GeneratorsFix psi)
    (a : BinaryWord r) :
    (G.wordProduct a).toCMatrix *ᵥ psi = psi := by
  classical
  unfold wordProduct
  apply (vectorFixingPauliSubmonoid psi).noncommProd_mem
  · intro i _
    change (G.powered a i).toCMatrix *ᵥ psi = psi
    have hv := (a.toAdd i).val_lt
    interval_cases hval : (a.toAdd i).val
    · simp [powered, hval]
    · simpa [powered, hval] using hpsi i

end CommutingInvolutivePauliGenerators

namespace IndependentSignedPauliGenerators

variable {n r : ℕ}

/-- For an arbitrary generator rank, the source generator-by-generator joint
`+1` eigenspace is exactly the invariant space of the generated binary Pauli
subgroup.  This is the set-level bridge needed to read the general-rank
character formula as Gottesman's common-eigenspace dimension theorem. -/
theorem generatorsFix_iff_mem_generalRankCommonFixed
    (G : IndependentSignedPauliGenerators n r)
    (psi : AgtXIv.Gottesman.QubitHilbert n) :
    G.toCommutingInvolutivePauliGenerators.GeneratorsFix psi ↔
      psi ∈ AgtXIv.Gottesman.commonFixedSpace
        G.toFrame.generalRankFDRep.ρ := by
  constructor
  · intro hfix a
    change (G.toFrame.eval a).toCMatrix *ᵥ psi = psi
    exact G.toCommutingInvolutivePauliGenerators
      |>.wordProduct_mulVec_eq_of_generatorsFix psi hfix a
  · intro hinv i
    have hword := hinv
      (CommutingInvolutivePauliGenerators.basisWord i)
    change
      (G.toFrame.eval
        (CommutingInvolutivePauliGenerators.basisWord i)).toCMatrix *ᵥ psi =
        psi at hword
    change
      (G.toCommutingInvolutivePauliGenerators.wordProduct
        (CommutingInvolutivePauliGenerators.basisWord i)).toCMatrix *ᵥ psi =
        psi at hword
    rw [CommutingInvolutivePauliGenerators.wordProduct_basisWord] at hword
    exact hword

/-- The source generator-by-generator joint eigenspace is exactly the
representation-theoretic fixed space used by the group average. -/
theorem generatorsFix_iff_mem_commonFixed
    (G : IndependentSignedPauliGenerators n n)
    (psi : AgtXIv.Gottesman.QubitHilbert n) :
    G.toCommutingInvolutivePauliGenerators.GeneratorsFix psi ↔
      psi ∈ AgtXIv.Gottesman.commonFixedSpace
        G.toFrame.rankPauliFrame.fdRep.ρ := by
  constructor
  · intro hfix a
    change (G.toFrame.eval a).toCMatrix *ᵥ psi = psi
    exact G.toCommutingInvolutivePauliGenerators
      |>.wordProduct_mulVec_eq_of_generatorsFix psi hfix a
  · intro hinv i
    have hword := hinv
      (CommutingInvolutivePauliGenerators.basisWord i)
    change
      (G.toFrame.eval
        (CommutingInvolutivePauliGenerators.basisWord i)).toCMatrix *ᵥ psi =
        psi at hword
    change
      (G.toCommutingInvolutivePauliGenerators.wordProduct
        (CommutingInvolutivePauliGenerators.basisWord i)).toCMatrix *ᵥ psi =
        psi at hword
    rw [CommutingInvolutivePauliGenerators.wordProduct_basisWord] at hword
    exact hword

/-- Source-form normalized joint eigenvector existence. -/
theorem exists_normalized_generator_fixed_vector
    (G : IndependentSignedPauliGenerators n n) :
    ∃ psi : AgtXIv.Gottesman.QubitHilbert n,
      G.toCommutingInvolutivePauliGenerators.GeneratorsFix psi ∧
        qubitKetNormSq psi = 1 := by
  obtain ⟨psi, hfixed, hnorm⟩ :=
    G.exists_normalized_commonFixed_vector
  exact ⟨psi, (generatorsFix_iff_mem_commonFixed G psi).2 hfixed, hnorm⟩

end IndependentSignedPauliGenerators

end

end AgtXIv.Stabilizer
