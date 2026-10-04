import AgtXIvRootMath.FiniteAtomRoM
import Mathlib.Analysis.Convex.Combination

/-!
# Finite atom mixtures and the ordinary convex hull

`FreeByAtoms` is the coefficient form used by the robustness proofs.  This
file proves that it is exactly Mathlib's geometric convex hull of the atom
range, including the reverse direction from an arbitrary finite convex
presentation.  Thus the resource-theory word "polytope" is not merely a
comment attached to a custom predicate.
-/

namespace AgtXIv.RoM

open scoped BigOperators
noncomputable section

variable {ι V : Type*} [Fintype ι]
variable [NormedAddCommGroup V] [NormedSpace ℝ V]

/-- The explicit full-index coefficient definition is exactly membership in
the ordinary convex hull of the finite atom range. -/
theorem freeByAtoms_iff_mem_convexHull_range
    (atom : ι → V) (rho : V) :
    FreeByAtoms atom rho ↔ rho ∈ convexHull ℝ (Set.range atom) := by
  classical
  constructor
  · rintro ⟨p, hp, hsum, hrec⟩
    exact mem_convexHull_of_exists_fintype p atom hp hsum
      (fun i => ⟨i, rfl⟩) hrec
  · intro hrho
    rcases mem_convexHull_iff_exists_fintype.mp hrho with
      ⟨κ, hκ, w, z, hw, hsum, hz, hcenter⟩
    letI : Fintype κ := hκ
    choose f hf using hz
    let p : ι → ℝ := fun j => ∑ k, if f k = j then w k else 0
    refine ⟨p, ?_, ?_, ?_⟩
    · intro j
      unfold p
      exact Finset.sum_nonneg fun k _ => by
        split
        · exact hw k
        · norm_num
    · unfold p
      calc
        ∑ j, ∑ k, (if f k = j then w k else 0) =
            ∑ k, ∑ j, (if f k = j then w k else 0) := Finset.sum_comm
        _ = ∑ k, w k := by simp
        _ = 1 := hsum
    · unfold SignedDecomp reconstruct p
      calc
        ∑ j, (∑ k, if f k = j then w k else 0) • atom j =
            ∑ j, ∑ k, (if f k = j then w k else 0) • atom j := by
              apply Finset.sum_congr rfl
              intro j _
              rw [Finset.sum_smul]
        _ = ∑ k, ∑ j, (if f k = j then w k else 0) • atom j :=
          Finset.sum_comm
        _ = ∑ k, w k • atom (f k) := by simp
        _ = ∑ k, w k • z k := by
          apply Finset.sum_congr rfl
          intro k _
          rw [hf k]
        _ = rho := hcenter

end

end AgtXIv.RoM
