import AgtXIvRootMath.PauliFrameSymplecticBasis
import AgtXIvRootMath.HermitianPauliBasis
import AgtXIvRootMath.GottesmanPauliGenerators

/-!
# Binary support of commuting Pauli words

This module packages phase-forgetting as a genuine homomorphism from the
signed Pauli group to the additive binary support group.  It then proves that
the support of a commuting subset product is exactly the binary linear
combination of its generator supports.  This is needed to prove independence
of the phase-aware dual Pauli words constructed during Clifford lifting.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators

/-- Forget signed Pauli phase while retaining multiplication as addition of
binary supports. -/
def pauliSupportHom (n : ℕ) :
    Pauli n →* Multiplicative (F2Support n) where
  toFun P := Multiplicative.ofAdd (F2Support.pauli P)
  map_one' := by simp
  map_mul' P Q := by
    apply Multiplicative.toAdd.injective
    exact F2Support.pauli_mul P Q

namespace CommutingInvolutivePauliGenerators

variable {n r : ℕ}

/-- The support of a commuting binary word is its coefficient-weighted sum of
generator supports.  All exact phases are retained in `wordProduct`; only this
conclusion intentionally forgets them. -/
theorem support_wordProduct
    (G : CommutingInvolutivePauliGenerators n r) (a : BinaryWord r) :
    F2Support.pauli (G.wordProduct a) =
      ∑ i : Fin r, a.toAdd i • F2Support.pauli (G.generator i) := by
  apply Multiplicative.ofAdd.injective
  change pauliSupportHom n (G.wordProduct a) = _
  unfold wordProduct
  rw [Finset.map_noncommProd]
  rw [show Finset.univ.noncommProd
      (fun i => pauliSupportHom n (G.powered a i)) _ =
      ∏ i, pauliSupportHom n (G.powered a i) by
    exact Finset.noncommProd_eq_prod _ _]
  apply Multiplicative.toAdd.injective
  change ∑ i, F2Support.pauli (G.powered a i) = _
  apply Finset.sum_congr rfl
  intro i _
  change F2Support.pauli (G.generator i ^ (a.toAdd i).val) =
    a.toAdd i • F2Support.pauli (G.generator i)
  rcases F2Bits.f2_eq_zero_or_one (a.toAdd i) with hi | hi
  · rw [hi]
    simp
  · rw [hi]
    rw [show (1 : F2).val = 1 by decide]
    simp

end CommutingInvolutivePauliGenerators

end AgtXIv.Stabilizer
