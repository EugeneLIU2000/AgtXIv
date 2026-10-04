import Mathlib

/-!
Uncompiled candidate formalization of the three matrices displayed on Hurwitz
1898, printed page 314 (retained PDF page 7). The signed entries were manually
transcribed in reviews/hurwitz1898-construction-matrices-20260922.json.

The coefficient domain below is a proposed modern generalization to a commutative
ring, not a claim about the historical author's stated domain. This file does not
prove the exclusion/classification theorem, the normalized B-system equivalence,
or the query paper's Pauli capacity bound. No kernel evidence exists for this file.
-/

namespace AgtXIv.Hurwitz1898

open scoped BigOperators

variable {R : Type*} [CommRing R]

def squareSum {n : ℕ} (x : Fin n → R) : R := ∑ i, x i ^ 2

def matrix2 (x : Fin 2 → R) : Matrix (Fin 2) (Fin 2) R :=
  ![![x 0, -x 1],
    ![x 1, x 0]]

def matrix4 (x : Fin 4 → R) : Matrix (Fin 4) (Fin 4) R :=
  ![![x 0, -x 1, -x 2, -x 3],
    ![x 1, x 0, -x 3, x 2],
    ![x 2, x 3, x 0, -x 1],
    ![x 3, -x 2, x 1, x 0]]

def matrix8 (x : Fin 8 → R) : Matrix (Fin 8) (Fin 8) R :=
  ![![x 0, -x 1, -x 2, -x 3, -x 4, -x 5, -x 6, -x 7],
    ![x 1, x 0, -x 3, x 2, -x 5, x 4, -x 7, x 6],
    ![x 2, x 3, x 0, -x 1, -x 6, x 7, x 4, -x 5],
    ![x 3, -x 2, x 1, x 0, x 7, x 6, -x 5, -x 4],
    ![x 4, x 5, x 6, -x 7, x 0, -x 1, -x 2, x 3],
    ![x 5, -x 4, -x 7, -x 6, x 1, x 0, x 3, x 2],
    ![x 6, x 7, -x 4, x 5, x 2, -x 3, x 0, -x 1],
    ![x 7, -x 6, x 5, x 4, -x 3, -x 2, x 1, x 0]]

-- This is an ordinary transpose. No conjugation or positivity is assumed.
theorem matrix2_row_gram (x : Fin 2 → R) :
    matrix2 x * (matrix2 x).transpose = Matrix.diagonal (fun _ => squareSum x) := by
  ext i j
  rw [Matrix.mul_apply, Matrix.diagonal_apply]
  simp only [Matrix.transpose_apply]
  fin_cases i <;> fin_cases j <;>
    simp [matrix2, squareSum, Fin.sum_univ_succ] <;> ring

theorem matrix4_row_gram (x : Fin 4 → R) :
    matrix4 x * (matrix4 x).transpose = Matrix.diagonal (fun _ => squareSum x) := by
  ext i j
  rw [Matrix.mul_apply, Matrix.diagonal_apply]
  simp only [Matrix.transpose_apply]
  fin_cases i <;> fin_cases j <;>
    simp [matrix4, squareSum, Fin.sum_univ_succ] <;> ring

set_option maxHeartbeats 2000000 in
theorem matrix8_row_gram (x : Fin 8 → R) :
    matrix8 x * (matrix8 x).transpose = Matrix.diagonal (fun _ => squareSum x) := by
  ext i j
  rw [Matrix.mul_apply, Matrix.diagonal_apply]
  simp only [Matrix.transpose_apply]
  fin_cases i <;> fin_cases j <;>
    simp [matrix8, squareSum, Fin.sum_univ_succ] <;> ring

-- Column Gram identities are separate obligations: row orthogonality alone is
-- not silently substituted for the norm identity of the map y ↦ A y.
theorem matrix2_column_gram (x : Fin 2 → R) :
    (matrix2 x).transpose * matrix2 x = Matrix.diagonal (fun _ => squareSum x) := by
  ext i j
  rw [Matrix.mul_apply, Matrix.diagonal_apply]
  simp only [Matrix.transpose_apply]
  fin_cases i <;> fin_cases j <;>
    simp [matrix2, squareSum, Fin.sum_univ_succ] <;> ring

theorem matrix4_column_gram (x : Fin 4 → R) :
    (matrix4 x).transpose * matrix4 x = Matrix.diagonal (fun _ => squareSum x) := by
  ext i j
  rw [Matrix.mul_apply, Matrix.diagonal_apply]
  simp only [Matrix.transpose_apply]
  fin_cases i <;> fin_cases j <;>
    simp [matrix4, squareSum, Fin.sum_univ_succ] <;> ring

set_option maxHeartbeats 2000000 in
theorem matrix8_column_gram (x : Fin 8 → R) :
    (matrix8 x).transpose * matrix8 x = Matrix.diagonal (fun _ => squareSum x) := by
  ext i j
  rw [Matrix.mul_apply, Matrix.diagonal_apply]
  simp only [Matrix.transpose_apply]
  fin_cases i <;> fin_cases j <;>
    simp [matrix8, squareSum, Fin.sum_univ_succ] <;> ring

def composition2 (x y : Fin 2 → R) : Fin 2 → R :=
  fun i => ∑ j, matrix2 x i j * y j

def composition4 (x y : Fin 4 → R) : Fin 4 → R :=
  fun i => ∑ j, matrix4 x i j * y j

def composition8 (x y : Fin 8 → R) : Fin 8 → R :=
  fun i => ∑ j, matrix8 x i j * y j

theorem composition2_squareSum (x y : Fin 2 → R) :
    squareSum (composition2 x y) = squareSum x * squareSum y := by
  simp [squareSum, composition2, matrix2, Fin.sum_univ_succ] <;> ring

theorem composition4_squareSum (x y : Fin 4 → R) :
    squareSum (composition4 x y) = squareSum x * squareSum y := by
  simp [squareSum, composition4, matrix4, Fin.sum_univ_succ] <;> ring

set_option maxHeartbeats 2000000 in
theorem composition8_squareSum (x y : Fin 8 → R) :
    squareSum (composition8 x y) = squareSum x * squareSum y := by
  simp [squareSum, composition8, matrix8, Fin.sum_univ_succ] <;> ring

end AgtXIv.Hurwitz1898
