import Hurwitz1898Constructions

/-!
Uncompiled bilinear packaging of the explicitly transcribed Hurwitz constructions.
The additivity and scalar laws are proof obligations, not assumptions. The final
existence statements concern these dimensions only; they do not classify all
possible dimensions, solve arbitrary quadratic forms, or establish source alignment.
-/

namespace AgtXIv.Hurwitz1898

variable {R : Type*} [CommRing R]

set_option maxHeartbeats 2000000 in
def bilinear2 : (Fin 2 → R) →ₗ[R] (Fin 2 → R) →ₗ[R] (Fin 2 → R) where
  toFun x := {
    toFun := composition2 x
    map_add' := by
      intro y z
      ext i
      fin_cases i <;>
        simp [composition2, matrix2, Fin.sum_univ_succ] <;> ring
    map_smul' := by
      intro a y
      ext i
      fin_cases i <;>
        simp [composition2, matrix2, Fin.sum_univ_succ, smul_eq_mul] <;> ring
  }
  map_add' := by
    intro x z
    refine LinearMap.ext fun y => funext fun i => ?_
    change composition2 (x + z) y i = composition2 x y i + composition2 z y i
    fin_cases i <;>
      simp [composition2, matrix2, Fin.sum_univ_succ] <;> ring
  map_smul' := by
    intro a x
    refine LinearMap.ext fun y => funext fun i => ?_
    change composition2 (a • x) y i = a • composition2 x y i
    fin_cases i <;>
      simp [composition2, matrix2, Fin.sum_univ_succ, smul_eq_mul] <;> ring

@[simp] theorem bilinear2_apply (x y : Fin 2 → R) :
    bilinear2 x y = composition2 x y := rfl

theorem bilinear2_squareSum (x y : Fin 2 → R) :
    squareSum (bilinear2 x y) = squareSum x * squareSum y := by
  exact composition2_squareSum x y

theorem exists_bilinear2_composition :
    ∃ f : (Fin 2 → R) →ₗ[R] (Fin 2 → R) →ₗ[R] (Fin 2 → R),
      ∀ x y, squareSum (f x y) = squareSum x * squareSum y :=
  ⟨bilinear2, bilinear2_squareSum⟩

set_option maxHeartbeats 2000000 in
def bilinear4 : (Fin 4 → R) →ₗ[R] (Fin 4 → R) →ₗ[R] (Fin 4 → R) where
  toFun x := {
    toFun := composition4 x
    map_add' := by
      intro y z
      ext i
      fin_cases i <;>
        simp [composition4, matrix4, Fin.sum_univ_succ] <;> ring
    map_smul' := by
      intro a y
      ext i
      fin_cases i <;>
        simp [composition4, matrix4, Fin.sum_univ_succ, smul_eq_mul] <;> ring
  }
  map_add' := by
    intro x z
    refine LinearMap.ext fun y => funext fun i => ?_
    change composition4 (x + z) y i = composition4 x y i + composition4 z y i
    fin_cases i <;>
      simp [composition4, matrix4, Fin.sum_univ_succ] <;> ring
  map_smul' := by
    intro a x
    refine LinearMap.ext fun y => funext fun i => ?_
    change composition4 (a • x) y i = a • composition4 x y i
    fin_cases i <;>
      simp [composition4, matrix4, Fin.sum_univ_succ, smul_eq_mul] <;> ring

@[simp] theorem bilinear4_apply (x y : Fin 4 → R) :
    bilinear4 x y = composition4 x y := rfl

theorem bilinear4_squareSum (x y : Fin 4 → R) :
    squareSum (bilinear4 x y) = squareSum x * squareSum y := by
  exact composition4_squareSum x y

theorem exists_bilinear4_composition :
    ∃ f : (Fin 4 → R) →ₗ[R] (Fin 4 → R) →ₗ[R] (Fin 4 → R),
      ∀ x y, squareSum (f x y) = squareSum x * squareSum y :=
  ⟨bilinear4, bilinear4_squareSum⟩

set_option maxHeartbeats 2000000 in
def bilinear8 : (Fin 8 → R) →ₗ[R] (Fin 8 → R) →ₗ[R] (Fin 8 → R) where
  toFun x := {
    toFun := composition8 x
    map_add' := by
      intro y z
      ext i
      fin_cases i <;>
        simp [composition8, matrix8, Fin.sum_univ_succ] <;> ring
    map_smul' := by
      intro a y
      ext i
      fin_cases i <;>
        simp [composition8, matrix8, Fin.sum_univ_succ, smul_eq_mul] <;> ring
  }
  map_add' := by
    intro x z
    refine LinearMap.ext fun y => funext fun i => ?_
    change composition8 (x + z) y i = composition8 x y i + composition8 z y i
    fin_cases i <;>
      simp [composition8, matrix8, Fin.sum_univ_succ] <;> ring
  map_smul' := by
    intro a x
    refine LinearMap.ext fun y => funext fun i => ?_
    change composition8 (a • x) y i = a • composition8 x y i
    fin_cases i <;>
      simp [composition8, matrix8, Fin.sum_univ_succ, smul_eq_mul] <;> ring

@[simp] theorem bilinear8_apply (x y : Fin 8 → R) :
    bilinear8 x y = composition8 x y := rfl

theorem bilinear8_squareSum (x y : Fin 8 → R) :
    squareSum (bilinear8 x y) = squareSum x * squareSum y := by
  exact composition8_squareSum x y

theorem exists_bilinear8_composition :
    ∃ f : (Fin 8 → R) →ₗ[R] (Fin 8 → R) →ₗ[R] (Fin 8 → R),
      ∀ x y, squareSum (f x y) = squareSum x * squareSum y :=
  ⟨bilinear8, bilinear8_squareSum⟩

end AgtXIv.Hurwitz1898
