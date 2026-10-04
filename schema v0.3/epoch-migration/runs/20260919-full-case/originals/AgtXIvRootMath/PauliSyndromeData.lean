import AgtXIvRootMath.GottesmanUniqueRay
import AgtXIvRootMath.SyndromeBasis
import AgtXIvRootMath.PauliFrameNormalForm

/-!
# Phase-aware Pauli syndrome-basis data

For every complete independent signed Pauli frame, this module instantiates
the generic syndrome-basis construction.  The read operators are the exact
signed frame words, while the flip operators are the exact Hermitian dual
words constructed by symplectic completion.  Their character is the binary
dot-product sign.

The vacuum is selected from the previously proved one-dimensional common
`+1` fixed space and normalized there; its existence is not an input field.
The resulting data still does not assume a Clifford witness.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix
noncomputable section

/-- Physical squared-norm normalization agrees with `ketInner`
normalization. -/
theorem ketInner_self_eq_one_of_qubitKetNormSq_eq_one {n : ℕ}
    (psi : AgtXIv.Gottesman.QubitHilbert n)
    (hpsi : qubitKetNormSq psi = 1) : ketInner psi psi = 1 := by
  have hcast : (↑(qubitKetNormSq psi) : ℂ) = 1 := by
    exact_mod_cast hpsi
  rw [qubitKetNormSq] at hcast
  simpa [ketInner, dotProduct, RCLike.star_def,
    ← Complex.normSq_eq_conj_mul_self] using hcast

/-- A binary coordinate distinguishes two different binary words by the
dot-product character. -/
theorem exists_binaryDot_ne {n : ℕ} {b c : BinaryWord n} (hbc : b ≠ c) :
    ∃ a : BinaryWord n,
      IndependentSignedPauliFrame.binaryDot a b ≠
        IndependentSignedPauliFrame.binaryDot a c := by
  have hfun : b.toAdd ≠ c.toAdd := by
    intro h
    apply hbc
    exact Multiplicative.toAdd.injective h
  obtain ⟨i, hi⟩ := Function.ne_iff.mp hfun
  let a : BinaryWord n := Multiplicative.ofAdd (Pi.single i 1)
  refine ⟨a, ?_⟩
  simp only [IndependentSignedPauliFrame.binaryDot]
  simp [a, Pi.single_apply, hi]

/-- Real complex character of the read/flip Weyl relation. -/
def binaryPhase {n : ℕ} (a b : BinaryWord n) : ℂ :=
  if IndependentSignedPauliFrame.binaryDot a b = 0 then 1 else -1

theorem binaryPhase_star {n : ℕ} (a b : BinaryWord n) :
    star (binaryPhase a b) = binaryPhase a b := by
  unfold binaryPhase
  split <;> simp

theorem binaryPhase_separates {n : ℕ} {b c : BinaryWord n} (hbc : b ≠ c) :
    ∃ a : BinaryWord n, binaryPhase a b ≠ binaryPhase a c := by
  obtain ⟨a, ha⟩ := exists_binaryDot_ne hbc
  refine ⟨a, ?_⟩
  rcases F2Bits.f2_eq_zero_or_one
      (IndependentSignedPauliFrame.binaryDot a b) with hb | hb <;>
    rcases F2Bits.f2_eq_zero_or_one
      (IndependentSignedPauliFrame.binaryDot a c) with hc | hc
  · exact (ha (hb.trans hc.symm)).elim
  · norm_num [binaryPhase, hb, hc]
  · norm_num [binaryPhase, hb, hc]
  · exact (ha (hb.trans hc.symm)).elim

/-- A cardinality-certified indexing of all binary syndrome words by the
computational basis.  No ordering convention beyond this equivalence is used
in the conjugation proof. -/
def binaryWordIndexEquiv (n : ℕ) : BinaryWord n ≃ Fin (2 ^ n) :=
  Fintype.equivFinOfCardEq
    (AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card n)

namespace IndependentSignedPauliFrame

variable {n : ℕ}

/-- Chosen normalized common `+1` vector, whose existence was derived from
the rank-one fixed-space theorem. -/
def syndromeVacuum (F : IndependentSignedPauliFrame n n) :
    AgtXIv.Gottesman.QubitHilbert n :=
  Classical.choose F.exists_normalized_commonFixed_vector

theorem syndromeVacuum_mem (F : IndependentSignedPauliFrame n n) :
    F.syndromeVacuum ∈ AgtXIv.Gottesman.commonFixedSpace
      F.rankPauliFrame.fdRep.ρ :=
  (Classical.choose_spec F.exists_normalized_commonFixed_vector).1

theorem syndromeVacuum_norm (F : IndependentSignedPauliFrame n n) :
    qubitKetNormSq F.syndromeVacuum = 1 :=
  (Classical.choose_spec F.exists_normalized_commonFixed_vector).2

/-- Every exact signed read word fixes the selected vacuum. -/
theorem read_syndromeVacuum (F : IndependentSignedPauliFrame n n)
    (a : BinaryWord n) :
    (F.eval a).toCMatrix *ᵥ F.syndromeVacuum = F.syndromeVacuum := by
  have h := (Representation.mem_invariants
    F.rankPauliFrame.fdRep.ρ F.syndromeVacuum).mp F.syndromeVacuum_mem a
  simpa [IndependentSignedPauliFrame.rankPauliFrame,
    AgtXIv.Gottesman.RankPauliFrame.fdRep, pauliMatrixRepresentation,
    Matrix.toLin'_apply] using h

/-- The exact Pauli Weyl relation transported to matrices.  A nonzero binary
pairing gives the literal complex scalar `-1`. -/
theorem read_mul_flip (F : IndependentSignedPauliFrame n n)
    (a b : BinaryWord n) :
    (F.eval a).toCMatrix * (F.dualFrame.eval b).toCMatrix =
      binaryPhase a b •
        ((F.dualFrame.eval b).toCMatrix * (F.eval a).toCMatrix) := by
  by_cases hd : binaryDot a b = 0
  · rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix,
      F.eval_mul_dualFrame_eval, if_pos hd]
    simp [binaryPhase, hd, Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
  · rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix,
      F.eval_mul_dualFrame_eval, if_neg hd, Pauli.toCMatrix_neg]
    simp [binaryPhase, hd, Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]

/-- Fully derived input for the generic syndrome-basis theorem. -/
def syndromeBasisData (F : IndependentSignedPauliFrame n n) :
    SyndromeBasisData (BinaryWord n) (2 ^ n) where
  basisIndex := binaryWordIndexEquiv n
  read a := (F.eval a).toCMatrix
  flip b := (F.dualFrame.eval b).toCMatrix
  vacuum := F.syndromeVacuum
  phase := binaryPhase
  read_hermitian a :=
    pauli_toCMatrix_isHermitian_of_sq_eq_one (F.eval a) (F.eval_sq a)
  flip_unitary b := pauli_toCMatrix_isUnitary (F.dualFrame.eval b)
  vacuum_normalized :=
    ketInner_self_eq_one_of_qubitKetNormSq_eq_one F.syndromeVacuum
      F.syndromeVacuum_norm
  read_vacuum := F.read_syndromeVacuum
  weyl := F.read_mul_flip
  phase_star := binaryPhase_star
  phase_separates := binaryPhase_separates

end IndependentSignedPauliFrame

end
end AgtXIv.Stabilizer
