import AgtXIvRootMath.PauliF2Support
import AgtXIvRootMath.SemanticClifford
import Mathlib.LinearAlgebra.Matrix.Hermitian

/-!
# Signed Pauli frames and their ordered `+1` filter products

This file keeps three objects separate:

* a phase-aware ordered Pauli frame;
* the product of its signed `+1` filters `(I + P) / 2`;
* the independently defined computational projector `|0⋯0⟩⟨0⋯0|`.

The central proved result is covariance under an *already supplied*
`SemanticClifford` certificate.  No theorem here assumes that an arbitrary
independent commuting frame admits such a certificate, and the standard-frame
filter product is not definitionally identified with the computational
projector.  Those are the remaining classification and matrix-identification
obligations in the Gottesman-to-Veitch bridge.
-/

namespace AgtXIv.Stabilizer

open scoped Matrix
noncomputable section

/-- A phase-aware ordered Pauli frame with an explicit generator count. -/
structure PauliFrame (n k : Nat) where
  generators : List (Pauli n)
  length_eq : generators.length = k

namespace PauliFrame

variable {n k : Nat}

/-- The generator at a bounded frame index. -/
def get (frame : PauliFrame n k) (i : Fin k) : Pauli n :=
  frame.generators.get (Fin.cast frame.length_eq.symm i)

/-- Apply the exact signed-Pauli automorphism carried by a semantic Clifford. -/
def map (C : SemanticClifford n) (frame : PauliFrame n k) : PauliFrame n k where
  generators := frame.generators.map C.action
  length_eq := by simp [frame.length_eq]

@[simp] theorem generators_map (C : SemanticClifford n) (frame : PauliFrame n k) :
    (frame.map C).generators = frame.generators.map C.action := rfl

end PauliFrame

/-- The `+1` spectral filter associated with a signed Pauli matrix.  It is a
projector only after the relevant involutivity/Hermiticity contract is proved. -/
def pauliFilter {n : Nat} (P : Pauli n) : CMatrix (2 ^ n) (2 ^ n) :=
  (2 : ℂ)⁻¹ • (1 + P.toCMatrix)

/-- Exact covariance of one signed Pauli filter. -/
theorem conjugate_pauliFilter {n : Nat} (C : SemanticClifford n) (P : Pauli n) :
    C.conjugate (pauliFilter P) = pauliFilter (C.action P) := by
  unfold pauliFilter
  rw [SemanticClifford.conjugate_smul, SemanticClifford.conjugate_add,
    SemanticClifford.conjugate_one, SemanticClifford.conjugate_pauli]

/-- Ordered product of the `+1` filters of a frame.  For a valid commuting
signed frame this is its joint-`+1`-eigenspace projector; that semantic fact is
deliberately a theorem obligation rather than part of this definition. -/
def frameProjector {n k : Nat} (frame : PauliFrame n k) :
    CMatrix (2 ^ n) (2 ^ n) :=
  (frame.generators.map pauliFilter).prod

theorem conjugate_list_filter_product {n : Nat} (C : SemanticClifford n)
    (generators : List (Pauli n)) :
    C.conjugate ((generators.map pauliFilter).prod) =
      (((generators.map C.action).map pauliFilter).prod) := by
  induction generators with
  | nil => simp [SemanticClifford.conjugate_one]
  | cons P generators ih =>
      simp only [List.map_cons, List.prod_cons, SemanticClifford.conjugate_mul,
        conjugate_pauliFilter]
      rw [ih]

/-- Exact frame-to-projector covariance.  This theorem needs no commutativity:
both sides retain the same generator order. -/
theorem conjugate_frameProjector {n k : Nat} (C : SemanticClifford n)
    (frame : PauliFrame n k) :
    C.conjugate (frameProjector frame) = frameProjector (frame.map C) := by
  exact conjugate_list_filter_product C frame.generators

/-- Standard signed `Z` generators, recursively ordered from the most
significant qubit to the least significant qubit. -/
def standardZGenerators : (n : Nat) → List (Pauli n)
  | 0 => []
  | n + 1 => Pauli.cons true false 1 ::
      (standardZGenerators n).map (Pauli.cons false false)

@[simp] theorem standardZGenerators_length (n : Nat) :
    (standardZGenerators n).length = n := by
  induction n with
  | zero => rfl
  | succ n ih => simp [standardZGenerators, ih]

/-- The standard rank-`n` signed `Z` frame. -/
def standardZFrame (n : Nat) : PauliFrame n n where
  generators := standardZGenerators n
  length_eq := standardZGenerators_length n

/-- The computational basis vector `|0⋯0⟩`, as a coordinate function. -/
def computationalZeroKet (n : Nat) : Fin (2 ^ n) → ℂ :=
  fun i => if i = 0 then 1 else 0

/-- The rank-one matrix `|0⋯0⟩⟨0⋯0|`, independently of Pauli filters. -/
def computationalZeroProjector (n : Nat) : CMatrix (2 ^ n) (2 ^ n) :=
  fun i j => computationalZeroKet n i * star (computationalZeroKet n j)

@[simp] theorem computationalZeroProjector_apply (n : Nat) (i j : Fin (2 ^ n)) :
    computationalZeroProjector n i j = if i = 0 ∧ j = 0 then 1 else 0 := by
  by_cases hj : j = 0
  · subst j
    simp [computationalZeroProjector, computationalZeroKet]
  · simp [computationalZeroProjector, computationalZeroKet, hj]

/-- The ordered filter product associated with the standard signed `Z` frame. -/
def standardZProjector (n : Nat) : CMatrix (2 ^ n) (2 ^ n) :=
  frameProjector (standardZFrame n)

namespace StandardFrame

open scoped Kron

/-- Reindex a leading one-qubit tensor factor into the `2^(n+1)` matrix
indexing convention used by `Pauli.toCMatrix`. -/
def prependQubitEquiv (n : Nat) : Fin (2 * 2 ^ n) ≃ Fin (2 ^ (n + 1)) :=
  finCongr (by ring)

/-- Tensor a one-qubit matrix on the most-significant side and use the same
indexing convention as LeanQuantum's Pauli evaluator. -/
def prependTensor {n : Nat} (A : CMatrix 2 2) (B : CMatrix (2 ^ n) (2 ^ n)) :
    CMatrix (2 ^ (n + 1)) (2 ^ (n + 1)) :=
  Matrix.reindexAlgEquiv ℂ ℂ (prependQubitEquiv n) (Matrix.kron A B)

theorem toCMatrix_cons {n : Nat} (z x : Bool) (P : Pauli n) :
    (Pauli.cons z x P).toCMatrix =
      prependTensor (Pauli.toCMatrix.bitsToMat (z, x)) P.toCMatrix := by
  simp [prependTensor, prependQubitEquiv, Matrix.reindexAlgEquiv_apply,
    Pauli.toCMatrix_cons]

/-- Prepending an identity Pauli turns a tail filter into `I ⊗ filter`. -/
theorem filter_cons_identity {n : Nat} (P : Pauli n) :
    pauliFilter (Pauli.cons false false P) = prependTensor 1 (pauliFilter P) := by
  simp only [pauliFilter]
  rw [toCMatrix_cons]
  simp only [prependTensor, Matrix.kron_smul]
  simp only [Pauli.toCMatrix.bitsToMat]
  simp
  simp [Matrix.submatrix_add, Matrix.submatrix_smul]

/-- The leading standard generator has filter `filter(Z) ⊗ I`. -/
theorem filter_cons_Z_one {n : Nat} :
    pauliFilter (Pauli.cons true false (1 : Pauli n)) =
      prependTensor (pauliFilter Pauli.Z) 1 := by
  simp only [pauliFilter]
  rw [toCMatrix_cons]
  simp only [prependTensor, Pauli.one_toCMatrix, Matrix.smul_kron]
  rw [Pauli.Z_toCMatrix]
  simp only [Pauli.toCMatrix.bitsToMat]
  simp
  simp [Matrix.submatrix_add, Matrix.submatrix_smul]

/-- An ordered product of identity-prepended tail filters is `I` tensored with
the original ordered product. -/
theorem lifted_filter_product {n : Nat} (generators : List (Pauli n)) :
    (((generators.map (Pauli.cons false false)).map pauliFilter).prod) =
      prependTensor 1 ((generators.map pauliFilter).prod) := by
  induction generators with
  | nil =>
      simp [prependTensor, Matrix.reindexAlgEquiv_apply]
  | cons P generators ih =>
      simp only [List.map_cons, List.prod_cons]
      rw [filter_cons_identity, ih]
      unfold prependTensor
      rw [← map_mul]
      congr 1
      rw [← Matrix.mul_kron_mul]
      simp

/-- Recursive tensor law for the standard signed-`Z` filter product. -/
theorem standardZProjector_succ (n : Nat) :
    standardZProjector (n + 1) =
      prependTensor (pauliFilter Pauli.Z) (standardZProjector n) := by
  simp only [standardZProjector, frameProjector, standardZFrame, standardZGenerators,
    List.map_cons, List.prod_cons]
  rw [filter_cons_Z_one, lifted_filter_product]
  unfold prependTensor
  rw [← map_mul]
  congr 1
  rw [← Matrix.mul_kron_mul]
  simp

/-- The one-qubit positive-`Z` filter is exactly `|0⟩⟨0|`. -/
theorem pauliFilter_Z_eq_zeroProjector_one :
    pauliFilter Pauli.Z = computationalZeroProjector 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    norm_num [pauliFilter, computationalZeroProjector, computationalZeroKet,
      Pauli.Z_toCMatrix, σz]

theorem fin_div_mod_eq_zero_iff {n : Nat} (q : Fin (2 * 2 ^ n)) :
    q.divNat = 0 ∧ q.modNat = 0 ↔ q = 0 := by
  constructor
  · rintro ⟨hdiv, hmod⟩
    apply Fin.ext
    have hdiv' : q.val / 2 ^ n = 0 := congrArg Fin.val hdiv
    have hmod' : q.val % 2 ^ n = 0 := congrArg Fin.val hmod
    calc
      q.val = 2 ^ n * (q.val / 2 ^ n) + q.val % 2 ^ n :=
        (Nat.div_add_mod q.val (2 ^ n)).symm
      _ = 0 := by rw [hdiv', hmod']; simp
  · rintro rfl
    constructor <;> apply Fin.ext <;> simp [Fin.divNat, Fin.modNat]

/-- The independently defined computational zero projector obeys the same
one-qubit tensor recursion. -/
theorem computationalZeroProjector_succ (n : Nat) :
    computationalZeroProjector (n + 1) =
      prependTensor (computationalZeroProjector 1) (computationalZeroProjector n) := by
  ext i j
  simp only [prependTensor, prependQubitEquiv, Matrix.reindexAlgEquiv_apply,
    Matrix.reindex_apply, Matrix.submatrix_apply, Matrix.kron_apply,
    computationalZeroProjector_apply]
  let qi : Fin (2 * 2 ^ n) := (prependQubitEquiv n).symm i
  let qj : Fin (2 * 2 ^ n) := (prependQubitEquiv n).symm j
  have hi : qi.divNat = 0 ∧ qi.modNat = 0 ↔ i = 0 := by
    rw [fin_div_mod_eq_zero_iff]
    simp [qi, prependQubitEquiv]
  have hj : qj.divNat = 0 ∧ qj.modNat = 0 ↔ j = 0 := by
    rw [fin_div_mod_eq_zero_iff]
    simp [qj, prependQubitEquiv]
  change (if i = 0 ∧ j = 0 then (1 : ℂ) else 0) =
    (if qi.divNat = 0 ∧ qj.divNat = 0 then 1 else 0) *
      (if qi.modNat = 0 ∧ qj.modNat = 0 then 1 else 0)
  split_ifs <;> simp_all

/-- For every qubit count, the ordered filters of the standard signed `Z`
frame equal the independently defined rank-one matrix `|0⋯0⟩⟨0⋯0|`. -/
theorem standardZProjector_eq_computationalZeroProjector (n : Nat) :
    standardZProjector n = computationalZeroProjector n := by
  induction n with
  | zero =>
      ext i j
      fin_cases i
      fin_cases j
      norm_num [standardZProjector, standardZFrame, standardZGenerators,
        frameProjector, computationalZeroProjector, computationalZeroKet]
  | succ n ih =>
      rw [standardZProjector_succ, computationalZeroProjector_succ, ih,
        pauliFilter_Z_eq_zeroProjector_one]

end StandardFrame

end
end AgtXIv.Stabilizer
