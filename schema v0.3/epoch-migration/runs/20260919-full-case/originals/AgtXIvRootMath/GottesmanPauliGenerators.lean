import AgtXIvRootMath.GottesmanRankNProjector
import Mathlib.Data.Finset.NoncommProd

/-!
# Source-level Pauli generators and their binary word map

`IndependentSignedPauliFrame` uses a binary word homomorphism because that is
the convenient downstream representation-theoretic interface.  Gottesman's
source conditions are stated instead as `n` commuting involutive signed Pauli
generators, their independence, and exclusion of `-I`.  This file proves the
bridge: the subset product is a homomorphism.  Thus commutation and
involutivity are not silently assumed again at the frame layer.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Function

/-- A concrete family of pairwise commuting, involutive signed Pauli
generators. -/
structure CommutingInvolutivePauliGenerators (n r : ℕ) where
  generator : Fin r → Pauli n
  involutive : ∀ i, generator i ^ 2 = 1
  commute : ∀ i j, Commute (generator i) (generator j)

namespace CommutingInvolutivePauliGenerators

variable {n r : ℕ}

/-- The `i`th generator, selected by the corresponding binary exponent. -/
def powered (G : CommutingInvolutivePauliGenerators n r)
    (a : BinaryWord r) (i : Fin r) : Pauli n :=
  G.generator i ^ (a.toAdd i).val

theorem powered_commute (G : CommutingInvolutivePauliGenerators n r)
    (a : BinaryWord r) :
    (↑(Finset.univ : Finset (Fin r)) : Set (Fin r)).Pairwise
      (Commute on G.powered a) := by
  intro i _ j _ _
  exact (G.commute i j).pow_pow _ _

/-- Product of the selected generators.  `Finset.noncommProd` makes the use of
pairwise commutation explicit even though the ambient Pauli group is not
commutative. -/
def wordProduct (G : CommutingInvolutivePauliGenerators n r)
    (a : BinaryWord r) : Pauli n :=
  Finset.univ.noncommProd (G.powered a) (G.powered_commute a)

theorem generator_pow_val_add (G : CommutingInvolutivePauliGenerators n r)
    (i : Fin r) (a b : ZMod 2) :
    G.generator i ^ (a + b).val =
      G.generator i ^ a.val * G.generator i ^ b.val := by
  fin_cases a <;> fin_cases b
  · change G.generator i ^ 0 = G.generator i ^ 0 * G.generator i ^ 0
    simp
  · change G.generator i ^ 1 = G.generator i ^ 0 * G.generator i ^ 1
    simp
  · change G.generator i ^ 1 = G.generator i ^ 1 * G.generator i ^ 0
    simp
  · change G.generator i ^ 0 = G.generator i ^ 1 * G.generator i ^ 1
    simpa [pow_two] using (G.involutive i).symm

theorem wordProduct_one (G : CommutingInvolutivePauliGenerators n r) :
    G.wordProduct 1 = 1 := by
  unfold wordProduct powered
  rw [Finset.noncommProd_eq_pow_card (Finset.univ) _ _ 1]
  · simp
  · intro i _
    simp

/-- Multiplying binary labels multiplies their Pauli subset products. -/
theorem wordProduct_mul (G : CommutingInvolutivePauliGenerators n r)
    (a b : BinaryWord r) :
    G.wordProduct (a * b) = G.wordProduct a * G.wordProduct b := by
  let f : Fin r → Pauli n := G.powered a
  let g : Fin r → Pauli n := G.powered b
  have hff : (↑(Finset.univ : Finset (Fin r)) : Set (Fin r)).Pairwise
      (Commute on f) := G.powered_commute a
  have hgg : (↑(Finset.univ : Finset (Fin r)) : Set (Fin r)).Pairwise
      (Commute on g) := G.powered_commute b
  have hgf : (↑(Finset.univ : Finset (Fin r)) : Set (Fin r)).Pairwise
      (fun i j => Commute (g i) (f j)) := by
    intro i _ j _ _
    exact (G.commute i j).pow_pow _ _
  calc
    G.wordProduct (a * b) =
        Finset.univ.noncommProd (f * g)
          (Finset.noncommProd_mul_distrib_aux hff hgg hgf) := by
      apply Finset.noncommProd_congr rfl
      intro i _
      change G.generator i ^ ((a * b).toAdd i).val =
        G.generator i ^ (a.toAdd i).val * G.generator i ^ (b.toAdd i).val
      exact G.generator_pow_val_add i (a.toAdd i) (b.toAdd i)
    _ = G.wordProduct a * G.wordProduct b := by
      exact Finset.noncommProd_mul_distrib f g hff hgg hgf

/-- The source-level subset product is therefore a genuine binary-group
homomorphism into the signed Pauli group. -/
def wordProductHom (G : CommutingInvolutivePauliGenerators n r) :
    BinaryWord r →* Pauli n where
  toFun := G.wordProduct
  map_one' := G.wordProduct_one
  map_mul' := G.wordProduct_mul

end CommutingInvolutivePauliGenerators

/-- Gottesman's complete phase-aware generator assumptions.  Independence and
`-I` exclusion are stated on the subset products and are not replaced by
cardinality or a one-dimensionality conclusion. -/
structure IndependentSignedPauliGenerators (n r : ℕ)
    extends CommutingInvolutivePauliGenerators n r where
  independent : Function.Injective toCommutingInvolutivePauliGenerators.wordProduct
  minusOneExcluded : ∀ a,
    toCommutingInvolutivePauliGenerators.wordProduct a ≠ -(1 : Pauli n)

namespace IndependentSignedPauliGenerators

variable {n r : ℕ}

/-- Construct the downstream exact frame from the source-level generators. -/
def toFrame (G : IndependentSignedPauliGenerators n r) :
    IndependentSignedPauliFrame n r where
  eval := G.toCommutingInvolutivePauliGenerators.wordProductHom
  independent := G.independent
  minusOneExcluded := G.minusOneExcluded

/-- A complete family of `n` source-level generators has a one-dimensional
common fixed space. -/
theorem finrank_commonFixed_eq_one (G : IndependentSignedPauliGenerators n n) :
    Module.finrank ℂ
      (AgtXIv.Gottesman.commonFixedSpace G.toFrame.rankPauliFrame.fdRep.ρ) = 1 :=
  G.toFrame.finrank_commonFixed_eq_one

/-- The complete source-level generator family determines a pure density
projector. -/
noncomputable def pureStabilizerDensity (G : IndependentSignedPauliGenerators n n) :
    PureDensityMatrix (2 ^ n) :=
  AgtXIv.Stabilizer.pureStabilizerDensity G.toFrame

end IndependentSignedPauliGenerators

end AgtXIv.Stabilizer
