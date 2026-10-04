/-
Copyright (c) 2026 Yingjian Liu. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Yingjian Liu
-/
module

public import QuantumInfo.States.Mixed.MState
public import Mathlib.Algebra.Order.Chebyshev
public import Mathlib.Analysis.Real.Sqrt

/-!
# Witness bounds from anticommuting observables

A family of pairwise anticommuting Hermitian involutions behaves like orthogonal axes of a
generalized Bloch ball. For any mixed state, the squared expectation values along these axes sum
to at most one. Cauchy--Schwarz then bounds the sum of their absolute expectations by the square
root of the family size.

This is the quantum uncertainty estimate used for the clique bound in the graph-theoretic
approach to nonstabilizerness. The graph application still has to identify each clique with such a
family of observables.

## A. Nonnegative variance

## B. Squaring an anticommuting sum

## C. Mixed-state witness bounds

## References

- Y. Liu et al., *Graph Theoretic Approach to Quantum Nonstabilizerness*, arXiv:2607.26154.
- S. Sarkar and A. van den Berg, *On Sets of Commuting and Anticommuting Paulis*,
  arXiv:1909.08123.
-/

@[expose] public section

noncomputable section

open BigOperators
open scoped Matrix

/-!

## A. Nonnegative variance

-/

namespace MState

variable {d : Type*} [Fintype d] [DecidableEq d]

/-- The expectation of a squared Hermitian observable dominates the square of its expectation. -/
lemma sq_exp_val_le_exp_val_sq (ρ : MState d) (A : HermitianMat d ℂ) :
    (ρ.exp_val A) ^ 2 ≤ ρ.exp_val (A ^ 2) := by
  let μ : ℝ := ρ.exp_val A
  have hcentered :
      (A - μ • (1 : HermitianMat d ℂ)) ^ 2 =
        A ^ 2 - (2 * μ) • A + (μ ^ 2) • (1 : HermitianMat d ℂ) := by
    apply HermitianMat.ext
    change (A.mat - μ • (1 : Matrix d d ℂ)) ^ 2 =
      A.mat ^ 2 - (2 * μ) • A.mat + (μ ^ 2) • (1 : Matrix d d ℂ)
    simp only [pow_two, sub_mul, mul_sub, Matrix.smul_mul, Matrix.mul_smul,
      one_mul, mul_one, smul_smul]
    module
  have hnonneg : 0 ≤ ρ.exp_val ((A - μ • (1 : HermitianMat d ℂ)) ^ 2) :=
    ρ.exp_val_nonneg (A - μ • (1 : HermitianMat d ℂ)).sq_nonneg
  rw [hcentered, ρ.exp_val_add, ρ.exp_val_sub, ρ.exp_val_smul,
    ρ.exp_val_smul, ρ.exp_val_one] at hnonneg
  dsimp [μ] at hnonneg
  nlinarith

end MState

/-!

## B. Squaring an anticommuting sum

-/

namespace Matrix

variable {d ι : Type*} [Fintype d] [DecidableEq d] [DecidableEq ι]

/-- Squaring a real-weighted sum of pairwise anticommuting involutions removes every mixed term. -/
lemma weighted_sum_sq_of_pairwise_anticommute (s : Finset ι) (A : ι → Matrix d d ℂ)
    (c : ι → ℝ) (hinv : ∀ i ∈ s, A i * A i = 1)
    (hanti : ∀ i ∈ s, ∀ j ∈ s, i ≠ j → A i * A j = -(A j * A i)) :
    (∑ i ∈ s, c i • A i) ^ 2 = (∑ i ∈ s, c i ^ 2) • (1 : Matrix d d ℂ) := by
  induction s using Finset.induction_on with
  | empty => simp
  | @insert a s ha ih =>
      let X : Matrix d d ℂ := c a • A a
      let Y : Matrix d d ℂ := ∑ i ∈ s, c i • A i
      have hcross : X * Y + Y * X = 0 := by
        dsimp [X, Y]
        rw [Matrix.mul_sum, Matrix.sum_mul, ← Finset.sum_add_distrib]
        apply Finset.sum_eq_zero
        intro i hi
        simp only [Matrix.smul_mul, Matrix.mul_smul, smul_smul]
        rw [hanti a (Finset.mem_insert_self a s) i (Finset.mem_insert_of_mem hi)
          (by exact fun h => ha (h ▸ hi))]
        simp [mul_comm]
      have hXsq : X ^ 2 = c a ^ 2 • (1 : Matrix d d ℂ) := by
        dsimp [X]
        simp [pow_two, hinv a (Finset.mem_insert_self a s), smul_smul]
      have ih' := ih
        (fun i hi => hinv i (Finset.mem_insert_of_mem hi))
        (fun i hi j hj hij => hanti i (Finset.mem_insert_of_mem hi) j
          (Finset.mem_insert_of_mem hj) hij)
      rw [Finset.sum_insert ha, Finset.sum_insert ha]
      change (X + Y) ^ 2 = (c a ^ 2 + ∑ i ∈ s, c i ^ 2) • (1 : Matrix d d ℂ)
      calc
        (X + Y) ^ 2 = X ^ 2 + (X * Y + Y * X) + Y ^ 2 := by
          simp only [pow_two]
          noncomm_ring
        _ = (c a ^ 2 + ∑ i ∈ s, c i ^ 2) • (1 : Matrix d d ℂ) := by
          rw [hcross, hXsq, ih']
          simp [add_smul]

end Matrix

/-!

## C. Mixed-state witness bounds

-/

namespace MState

variable {d ι : Type*} [Fintype d] [DecidableEq d] [DecidableEq ι]

/-- Expectation is additive over a finite sum of Hermitian observables. -/
lemma exp_val_finset_sum (ρ : MState d) (s : Finset ι) (A : ι → HermitianMat d ℂ) :
    ρ.exp_val (∑ i ∈ s, A i) = ∑ i ∈ s, ρ.exp_val (A i) := by
  induction s using Finset.induction_on with
  | empty => simp
  | @insert a s ha ih => simp [ha, ρ.exp_val_add, ih]

/-- Squared expectations of pairwise anticommuting Hermitian involutions sum to at most one. -/
lemma sum_sq_exp_val_finset_le_one_of_pairwise_anticommute (ρ : MState d) (s : Finset ι)
    (A : ι → HermitianMat d ℂ) (hinv : ∀ i ∈ s, A i ^ 2 = 1)
    (hanti : ∀ i ∈ s, ∀ j ∈ s,
      i ≠ j → (A i).mat * (A j).mat = -((A j).mat * (A i).mat)) :
    ∑ i ∈ s, (ρ.exp_val (A i)) ^ 2 ≤ 1 := by
  let r : ι → ℝ := fun i => ρ.exp_val (A i)
  let S : ℝ := ∑ i ∈ s, r i ^ 2
  let B : HermitianMat d ℂ := ∑ i ∈ s, r i • A i
  have hBsq : B ^ 2 = S • (1 : HermitianMat d ℂ) := by
    apply HermitianMat.ext
    simpa [B, S] using Matrix.weighted_sum_sq_of_pairwise_anticommute s
      (fun i => (A i).mat) r (fun i hi => by
        simpa [pow_two] using congrArg HermitianMat.mat (hinv i hi)) hanti
  have hBexp : ρ.exp_val B = S := by
    dsimp [B, S, r]
    rw [ρ.exp_val_finset_sum]
    simp only [ρ.exp_val_smul]
    simp [pow_two]
  have hvariance := ρ.sq_exp_val_le_exp_val_sq B
  rw [hBexp, hBsq, ρ.exp_val_smul, ρ.exp_val_one] at hvariance
  have hSnonneg : 0 ≤ S := by
    dsimp [S]
    exact Finset.sum_nonneg fun i _ => sq_nonneg (r i)
  dsimp [S, r] at hvariance hSnonneg ⊢
  nlinarith

/-- Absolute expectations of pairwise anticommuting Hermitian involutions are clique-bounded. -/
lemma sum_abs_exp_val_finset_le_sqrt_card_of_pairwise_anticommute (ρ : MState d)
    (s : Finset ι)
    (A : ι → HermitianMat d ℂ) (hinv : ∀ i ∈ s, A i ^ 2 = 1)
    (hanti : ∀ i ∈ s, ∀ j ∈ s,
      i ≠ j → (A i).mat * (A j).mat = -((A j).mat * (A i).mat)) :
    ∑ i ∈ s, |ρ.exp_val (A i)| ≤ √(s.card : ℝ) := by
  have hl2 := ρ.sum_sq_exp_val_finset_le_one_of_pairwise_anticommute s A hinv hanti
  have hcs :
      (∑ i ∈ s, |ρ.exp_val (A i)|) ^ 2 ≤
        (s.card : ℝ) * ∑ i ∈ s, |ρ.exp_val (A i)| ^ 2 := by
    exact sq_sum_le_card_mul_sum_sq
  have habs :
      (∑ i ∈ s, |ρ.exp_val (A i)| ^ 2) =
        ∑ i ∈ s, (ρ.exp_val (A i)) ^ 2 := by
    simp
  rw [habs] at hcs
  have hsq : (∑ i ∈ s, |ρ.exp_val (A i)|) ^ 2 ≤ (s.card : ℝ) :=
    hcs.trans <| by
      simpa using mul_le_mul_of_nonneg_left hl2 (Nat.cast_nonneg s.card)
  exact Real.le_sqrt_of_sq_le hsq

/-- Type-indexed squared-expectation bound for an entire finite anticommuting family. -/
lemma sum_sq_exp_val_le_one_of_pairwise_anticommute [Fintype ι] (ρ : MState d)
    (A : ι → HermitianMat d ℂ) (hinv : ∀ i, A i ^ 2 = 1)
    (hanti : ∀ i j, i ≠ j → (A i).mat * (A j).mat = -((A j).mat * (A i).mat)) :
    ∑ i, (ρ.exp_val (A i)) ^ 2 ≤ 1 := by
  simpa using ρ.sum_sq_exp_val_finset_le_one_of_pairwise_anticommute Finset.univ A
    (fun i _ => hinv i) (fun i _ j _ hij => hanti i j hij)

/-- Type-indexed absolute-expectation bound for an entire finite anticommuting family. -/
lemma sum_abs_exp_val_le_sqrt_card_of_pairwise_anticommute [Fintype ι] (ρ : MState d)
    (A : ι → HermitianMat d ℂ) (hinv : ∀ i, A i ^ 2 = 1)
    (hanti : ∀ i j, i ≠ j → (A i).mat * (A j).mat = -((A j).mat * (A i).mat)) :
    ∑ i, |ρ.exp_val (A i)| ≤ √(Fintype.card ι : ℝ) := by
  simpa using
    ρ.sum_abs_exp_val_finset_le_sqrt_card_of_pairwise_anticommute Finset.univ A
      (fun i _ => hinv i) (fun i _ j _ hij => hanti i j hij)

end MState
