import AgtXIvRootMath.PauliAdjoint
import AgtXIvRootMath.GottesmanRankPauliFrame

/-!
# From independent signed Pauli generators to a one-dimensional fixed space

This file closes the concrete bridge omitted by the abstract binary-frame
module.  Its primitive input is the subset-product homomorphism of a commuting,
involutive signed Pauli generator family.  Injectivity is generator
independence; exclusion of `-I` is the stabilizer phase condition.  Cardinality,
absence of all nontrivial scalar phases, the delta character, and fixed-space
dimension one are conclusions rather than fields.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators

/-- Binary subset labels, written multiplicatively so that they can act as the
domain of a Pauli word homomorphism. -/
abbrev BinaryWord (r : ℕ) := AgtXIv.Gottesman.BinaryFrameGroup r

/-- Every binary word is an involution. -/
theorem binaryWord_sq {r : ℕ} (a : BinaryWord r) : a ^ 2 = 1 := by
  rw [pow_two]
  apply Multiplicative.toAdd.injective
  ext i
  change a.toAdd i + a.toAdd i = 0
  rw [← two_mul]
  have hTwo : (2 : ZMod 2) = 0 := by decide
  rw [hTwo, zero_mul]

/-- A phase-aware signed Pauli frame encoded by its binary subset-product map.
The homomorphism property packages involutivity and pairwise commutation;
injectivity packages generator independence. -/
structure IndependentSignedPauliFrame (n r : ℕ) where
  eval : BinaryWord r →* Pauli n
  independent : Function.Injective eval
  minusOneExcluded : ∀ a, eval a ≠ -(1 : Pauli n)

namespace IndependentSignedPauliFrame

variable {n r : ℕ}

/-- Every evaluated binary word remains an involution. -/
theorem eval_sq {n r : ℕ} (F : IndependentSignedPauliFrame n r)
    (a : BinaryWord r) : F.eval a ^ 2 = 1 := by
  rw [← map_pow, binaryWord_sq, map_one]

/-- If an evaluated word has zero binary Pauli support, then it is the identity
word.  The proof first uses involutivity to reduce the possible scalar phases
to `+I` and `-I`, then uses the stabilizer exclusion of `-I`. -/
theorem scalar_support_implies_label_one {n r : ℕ}
    (F : IndependentSignedPauliFrame n r) (a : BinaryWord r)
    (hz : (F.eval a).z = 0) (hx : (F.eval a).x = 0) : a = 1 := by
  have hs := F.eval_sq a
  have hm : 2 * (F.eval a).m = 0 := by
    have h := congrArg Pauli.m hs
    simp [Pauli.pow_two, Pauli.phaseFlipsWith, hz, hx, Pauli.addPhase] at h
    exact h
  have hmCases : (F.eval a).m = 0 ∨ (F.eval a).m = 2 := by
    have hv := (F.eval a).m.val_lt
    interval_cases hv0 : (F.eval a).m.val
    · exact Or.inl ((ZMod.val_eq_zero (F.eval a).m).mp hv0)
    · have hm1 : (F.eval a).m = 1 :=
        (ZMod.val_eq_one (by norm_num) (F.eval a).m).mp hv0
      rw [hm1] at hm
      have hNe : (2 : ZMod 4) ≠ 0 := by decide
      exact (hNe hm).elim
    · right
      apply ZMod.val_injective
      simpa using hv0
    · have hm3 : (F.eval a).m = 3 := by
        apply ZMod.val_injective
        simpa using hv0
      rw [hm3] at hm
      have hNe : (6 : ZMod 4) ≠ 0 := by decide
      exact (hNe hm).elim
  apply F.independent
  rcases hmCases with hm0 | hm2
  · apply Pauli.ext <;> simp [hm0, hz, hx]
  · exfalso
    apply F.minusOneExcluded a
    apply Pauli.ext <;> simp [hm2, hz, hx]

/-- A nonidentity frame label evaluates to a Pauli with nonzero binary support. -/
theorem support_ne_zero_of_label_ne_one {n r : ℕ}
    (F : IndependentSignedPauliFrame n r) (a : BinaryWord r)
    (ha : a ≠ 1) : (F.eval a).z ≠ 0 ∨ (F.eval a).x ≠ 0 := by
  by_cases hz : (F.eval a).z = 0
  · exact Or.inr (fun hx => ha (F.scalar_support_implies_label_one a hz hx))
  · exact Or.inl hz

/-- Consequently every nonidentity frame word is traceless in the locked
matrix representation. -/
theorem trace_eval_eq_zero_of_label_ne_one {n r : ℕ}
    (F : IndependentSignedPauliFrame n r) (a : BinaryWord r)
    (ha : a ≠ 1) : Matrix.trace (F.eval a).toCMatrix = 0 :=
  trace_eval_eq_zero_of_support_ne_zero (F.eval a)
    (F.support_ne_zero_of_label_ne_one a ha)

/-- Construct the abstract rank-`n` binary frame from an actual independent
signed Pauli frame.  Its character hypotheses are proved from the concrete
trace theorem, not supplied by the caller. -/
noncomputable def rankPauliFrame (F : IndependentSignedPauliFrame n n) :
    AgtXIv.Gottesman.RankPauliFrame n (BinaryWord n) where
  word := MonoidHom.id (BinaryWord n)
  word_injective := Function.injective_id
  word_surjective := Function.surjective_id
  action := (pauliMatrixRepresentation n).comp F.eval
  nonidentity_traceless a ha := by
    change LinearMap.trace ℂ _ (Matrix.toLin' (F.eval a).toCMatrix) = 0
    rw [Matrix.trace_toLin'_eq]
    exact F.trace_eval_eq_zero_of_label_ne_one a ha

/-- The common `+1` fixed space of an independent rank-`n` signed Pauli frame
is one-dimensional.  Neither cardinality nor dimension is an input field. -/
theorem finrank_commonFixed_eq_one (F : IndependentSignedPauliFrame n n) :
    Module.finrank ℂ
      (AgtXIv.Gottesman.commonFixedSpace F.rankPauliFrame.fdRep.ρ) = 1 :=
  F.rankPauliFrame.finrank_commonFixed_eq_one

end IndependentSignedPauliFrame

end AgtXIv.Stabilizer
