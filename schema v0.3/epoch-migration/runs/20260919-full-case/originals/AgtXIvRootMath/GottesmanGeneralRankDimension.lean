import AgtXIvRootMath.GottesmanPauliGenerators
import Mathlib.RepresentationTheory.Character

/-!
# Dimension of the fixed space of a general-rank Pauli frame

For an independent phase-clean family of `r` commuting signed Pauli
generators on `n` qubits, this file derives the common fixed-space dimension
`2 ^ (n - r)`, assuming only the physically necessary rank bound `r ≤ n`.

Neither the binary group cardinality, the character profile, nor the final
dimension is an input field.  The proof derives the group cardinality from its
binary-word type and derives the nonidentity character values from the
phase-aware Pauli trace theorem.
-/

namespace AgtXIv.Stabilizer

open Representation
open scoped BigOperators

noncomputable section

namespace IndependentSignedPauliFrame

variable {n r : ℕ}

/-- The actual Pauli-matrix action of a rank-`r` frame on the `n`-qubit
Hilbert space, packaged as a finite-dimensional representation. -/
noncomputable abbrev generalRankFDRep
    (F : IndependentSignedPauliFrame n r) : FDRep ℂ (BinaryWord r) :=
  FDRep.of ((pauliMatrixRepresentation n).comp F.eval)

/-- The identity word has character equal to the `n`-qubit Hilbert-space
dimension. -/
theorem generalRankFDRep_character_one
    (F : IndependentSignedPauliFrame n r) :
    F.generalRankFDRep.character 1 = (2 ^ n : ℂ) := by
  rw [FDRep.char_one]
  simp [generalRankFDRep]

/-- Every nonidentity binary word has zero character.  This uses the concrete
phase-clean Pauli trace theorem rather than assuming a delta profile. -/
theorem generalRankFDRep_character_zero_of_ne_one
    (F : IndependentSignedPauliFrame n r) (a : BinaryWord r)
    (ha : a ≠ 1) :
    F.generalRankFDRep.character a = 0 := by
  change LinearMap.trace ℂ _ (Matrix.toLin' (F.eval a).toCMatrix) = 0
  rw [Matrix.trace_toLin'_eq]
  exact F.trace_eval_eq_zero_of_label_ne_one a ha

/-- The complete character profile of the general-rank frame. -/
theorem generalRankFDRep_character_delta
    (F : IndependentSignedPauliFrame n r) (a : BinaryWord r) :
    F.generalRankFDRep.character a =
      if a = 1 then (2 ^ n : ℂ) else 0 := by
  by_cases ha : a = 1
  · subst a
    rw [if_pos rfl]
    exact F.generalRankFDRep_character_one
  · rw [if_neg ha]
    exact F.generalRankFDRep_character_zero_of_ne_one a ha

/-- Summing the character leaves only the identity contribution. -/
theorem sum_generalRankFDRep_character
    (F : IndependentSignedPauliFrame n r) :
    ∑ a : BinaryWord r, F.generalRankFDRep.character a = (2 ^ n : ℂ) := by
  classical
  simp_rw [F.generalRankFDRep_character_delta]
  simp

/-- An independent phase-clean rank-`r` signed Pauli frame on `n` qubits has
common fixed-space dimension `2 ^ (n - r)`.  Group cardinality and the
character delta are conclusions, not hypotheses. -/
theorem finrank_commonFixed_eq_two_pow_sub
    (F : IndependentSignedPauliFrame n r) (hr : r ≤ n) :
    Module.finrank ℂ
      (AgtXIv.Gottesman.commonFixedSpace F.generalRankFDRep.ρ) =
        2 ^ (n - r) := by
  classical
  letI : Invertible (Fintype.card (BinaryWord r) : ℂ) :=
    invertibleOfNonzero (Nat.cast_ne_zero.mpr Fintype.card_ne_zero)
  have hAverage := F.generalRankFDRep.average_char_eq_finrank_invariants
  have hProductComplex :
      (Fintype.card (BinaryWord r) : ℂ) *
          (Module.finrank ℂ
            (AgtXIv.Gottesman.commonFixedSpace F.generalRankFDRep.ρ) : ℂ) =
        (2 ^ n : ℂ) := by
    calc
      (Fintype.card (BinaryWord r) : ℂ) *
          (Module.finrank ℂ
            (AgtXIv.Gottesman.commonFixedSpace F.generalRankFDRep.ρ) : ℂ) =
          (Fintype.card (BinaryWord r) : ℂ) *
            (⅟(Fintype.card (BinaryWord r) : ℂ) •
              ∑ a : BinaryWord r, F.generalRankFDRep.character a) := by
                rw [hAverage]
      _ = ∑ a : BinaryWord r, F.generalRankFDRep.character a := by
        rw [smul_eq_mul, ← mul_assoc, mul_invOf_self, one_mul]
      _ = (2 ^ n : ℂ) := F.sum_generalRankFDRep_character
  have hProductNat :
      Fintype.card (BinaryWord r) *
          Module.finrank ℂ
            (AgtXIv.Gottesman.commonFixedSpace F.generalRankFDRep.ρ) =
        2 ^ n := by
    exact_mod_cast hProductComplex
  rw [AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card r] at hProductNat
  have hPow : 2 ^ n = 2 ^ r * 2 ^ (n - r) := by
    calc
      2 ^ n = 2 ^ (r + (n - r)) := by rw [Nat.add_sub_of_le hr]
      _ = 2 ^ r * 2 ^ (n - r) := by rw [pow_add]
  apply Nat.eq_of_mul_eq_mul_left (by positivity : 0 < 2 ^ r)
  exact hProductNat.trans hPow

/-- In code-dimension notation `r = n - k`, the fixed-space dimension is
`2 ^ k`. -/
theorem finrank_commonFixed_eq_two_pow_codeDimension
    (F : IndependentSignedPauliFrame n (n - r)) (hr : r ≤ n) :
    Module.finrank ℂ
      (AgtXIv.Gottesman.commonFixedSpace F.generalRankFDRep.ρ) =
        2 ^ r := by
  simpa [Nat.sub_sub_self hr] using
    F.finrank_commonFixed_eq_two_pow_sub (Nat.sub_le n r)

end IndependentSignedPauliFrame

namespace IndependentSignedPauliGenerators

variable {n r : ℕ}

/-- Source-level commuting involutive generators inherit the general-rank
fixed-space dimension theorem through their proved binary word map. -/
theorem finrank_commonFixed_eq_two_pow_sub
    (G : IndependentSignedPauliGenerators n r) (hr : r ≤ n) :
    Module.finrank ℂ
      (AgtXIv.Gottesman.commonFixedSpace G.toFrame.generalRankFDRep.ρ) =
        2 ^ (n - r) :=
  G.toFrame.finrank_commonFixed_eq_two_pow_sub hr

/-- Source-level `n-k` generator form of the stabilizer-code dimension
formula. -/
theorem finrank_commonFixed_eq_two_pow_codeDimension
    (G : IndependentSignedPauliGenerators n (n - r)) (hr : r ≤ n) :
    Module.finrank ℂ
      (AgtXIv.Gottesman.commonFixedSpace G.toFrame.generalRankFDRep.ρ) =
        2 ^ r :=
  G.toFrame.finrank_commonFixed_eq_two_pow_codeDimension hr

end IndependentSignedPauliGenerators

end


end AgtXIv.Stabilizer
