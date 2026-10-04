import AgtXIvRootMath.GottesmanPauliGenerators
import Mathlib.Analysis.Complex.Norm
import Mathlib.LinearAlgebra.FiniteDimensional.Basic

/-!
# Uniqueness of the normalized stabilizer ray

The rank-`n` Pauli argument already proves that the common `+1` fixed space is
one-dimensional.  This file spells out the source's final ray statement: two
vectors in that fixed space with physical squared norm one differ by a scalar
of unit complex modulus.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators
noncomputable section

/-- The physical squared Hilbert norm on the computational amplitudes. -/
def qubitKetNormSq {n : ℕ} (psi : AgtXIv.Gottesman.QubitHilbert n) : ℝ :=
  ∑ i, Complex.normSq (psi i)

@[simp]
theorem qubitKetNormSq_zero {n : ℕ} :
    qubitKetNormSq (0 : AgtXIv.Gottesman.QubitHilbert n) = 0 := by
  simp [qubitKetNormSq]

theorem qubitKetNormSq_smul {n : ℕ} (c : ℂ)
    (psi : AgtXIv.Gottesman.QubitHilbert n) :
    qubitKetNormSq (c • psi) = Complex.normSq c * qubitKetNormSq psi := by
  simp only [qubitKetNormSq, Pi.smul_apply, smul_eq_mul,
    Complex.normSq_mul, Finset.mul_sum]

/-- A nonzero computational-amplitude vector has strictly positive physical
squared norm.  This elementary lemma lets the one-dimensional fixed-space
result produce a normalized vector without assuming one as extra input. -/
theorem qubitKetNormSq_pos_of_ne_zero {n : ℕ}
    (psi : AgtXIv.Gottesman.QubitHilbert n) (hpsi : psi ≠ 0) :
    0 < qubitKetNormSq psi := by
  rw [qubitKetNormSq]
  apply Finset.sum_pos'
  · intro i _
    exact Complex.normSq_nonneg (psi i)
  · obtain ⟨i, hi⟩ := Function.ne_iff.mp hpsi
    refine ⟨i, Finset.mem_univ i, ?_⟩
    exact Complex.normSq_pos.mpr (by simpa using hi)

/-- The complete independent signed Pauli frame has a physically normalized
common `+1` vector.  Existence is derived from the already proved
one-dimensional fixed space and finite-dimensional normalization; it is not a
field of the frame structure. -/
theorem IndependentSignedPauliFrame.exists_normalized_commonFixed_vector
    {n : ℕ} (F : IndependentSignedPauliFrame n n) :
    ∃ psi : AgtXIv.Gottesman.QubitHilbert n,
      psi ∈ AgtXIv.Gottesman.commonFixedSpace F.rankPauliFrame.fdRep.ρ ∧
        qubitKetNormSq psi = 1 := by
  let U := AgtXIv.Gottesman.commonFixedSpace F.rankPauliFrame.fdRep.ρ
  have hfinrank : 0 < Module.finrank ℂ U := by
    rw [F.finrank_commonFixed_eq_one]
    norm_num
  letI : Nontrivial U := Module.finrank_pos_iff.mp hfinrank
  obtain ⟨u, hu⟩ := exists_ne (0 : U)
  have huCoe : (u : AgtXIv.Gottesman.QubitHilbert n) ≠ 0 := by
    intro hzero
    apply hu
    apply Subtype.ext
    exact hzero
  let q := qubitKetNormSq (u : AgtXIv.Gottesman.QubitHilbert n)
  have hq : 0 < q := qubitKetNormSq_pos_of_ne_zero _ huCoe
  let c : ℂ := ((Real.sqrt q : ℝ) : ℂ)⁻¹
  refine ⟨c • (u : AgtXIv.Gottesman.QubitHilbert n), ?_, ?_⟩
  · exact U.smul_mem c u.property
  · rw [qubitKetNormSq_smul]
    simp only [c, Complex.normSq_inv, Complex.normSq_ofReal]
    rw [← pow_two, Real.sq_sqrt hq.le]
    exact inv_mul_cancel₀ hq.ne'

/-- Two physically normalized vectors in the one-dimensional common fixed
space of a complete frame differ by a unit-modulus global phase. -/
theorem IndependentSignedPauliFrame.normalized_fixed_vectors_differ_by_phase
    {n : ℕ} (F : IndependentSignedPauliFrame n n)
    (psi phi : AgtXIv.Gottesman.QubitHilbert n)
    (hpsi : psi ∈ AgtXIv.Gottesman.commonFixedSpace
      F.rankPauliFrame.fdRep.ρ)
    (hphi : phi ∈ AgtXIv.Gottesman.commonFixedSpace
      F.rankPauliFrame.fdRep.ρ)
    (hpsiNorm : qubitKetNormSq psi = 1)
    (hphiNorm : qubitKetNormSq phi = 1) :
    ∃ c : ℂ, ‖c‖ = 1 ∧ phi = c • psi := by
  let U := AgtXIv.Gottesman.commonFixedSpace F.rankPauliFrame.fdRep.ρ
  let psiU : U := ⟨psi, hpsi⟩
  let phiU : U := ⟨phi, hphi⟩
  have hpsiU_ne : psiU ≠ 0 := by
    intro hzero
    have hzeroCoe : psi = 0 := congrArg Subtype.val hzero
    have hnormZero : qubitKetNormSq psi = 0 := by
      rw [hzeroCoe]
      exact qubitKetNormSq_zero
    linarith
  obtain ⟨c, hc⟩ := exists_smul_eq_of_finrank_eq_one
    F.finrank_commonFixed_eq_one hpsiU_ne phiU
  have hcCoe : c • psi = phi := congrArg Subtype.val hc
  have hnormEq := congrArg qubitKetNormSq hcCoe
  rw [qubitKetNormSq_smul, hpsiNorm, hphiNorm, mul_one] at hnormEq
  refine ⟨c, ?_, hcCoe.symm⟩
  rw [Complex.norm_def, hnormEq]
  norm_num

/-- Source-level generator-family version of normalized-ray uniqueness. -/
theorem IndependentSignedPauliGenerators.normalized_fixed_vectors_differ_by_phase
    {n : ℕ} (G : IndependentSignedPauliGenerators n n)
    (psi phi : AgtXIv.Gottesman.QubitHilbert n)
    (hpsi : psi ∈ AgtXIv.Gottesman.commonFixedSpace
      G.toFrame.rankPauliFrame.fdRep.ρ)
    (hphi : phi ∈ AgtXIv.Gottesman.commonFixedSpace
      G.toFrame.rankPauliFrame.fdRep.ρ)
    (hpsiNorm : qubitKetNormSq psi = 1)
    (hphiNorm : qubitKetNormSq phi = 1) :
    ∃ c : ℂ, ‖c‖ = 1 ∧ phi = c • psi :=
  G.toFrame.normalized_fixed_vectors_differ_by_phase
    psi phi hpsi hphi hpsiNorm hphiNorm

/-- Source-level generator-family version of normalized-vector existence. -/
theorem IndependentSignedPauliGenerators.exists_normalized_commonFixed_vector
    {n : ℕ} (G : IndependentSignedPauliGenerators n n) :
    ∃ psi : AgtXIv.Gottesman.QubitHilbert n,
      psi ∈ AgtXIv.Gottesman.commonFixedSpace
        G.toFrame.rankPauliFrame.fdRep.ρ ∧
        qubitKetNormSq psi = 1 :=
  G.toFrame.exists_normalized_commonFixed_vector

end

end AgtXIv.Stabilizer
