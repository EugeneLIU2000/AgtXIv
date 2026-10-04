import AgtXIvStabilizerness.LocalDelta

/-!
A domain-sensitive bridge for the target paper's sign optimization.
The paper-specific admissible sign set and the no-active-dependency lemma
are NOT proved here. The equality `hCollapse` remains an explicit premise.
This bridge must not be bound to the paper's final graph/RoM query theorem.
-/

namespace AgtXIv.Stabilizerness

open scoped BigOperators
open Set

def admissibleSignedValues {ι : Type*} [Fintype ι]
    (admissible : Set (ι → ℝ)) (y : ι → ℝ) (μ : ℝ) : Set ℝ :=
  {z | ∃ f ∈ admissible, z = |(∑ i, f i * y i) + μ|}

/-- Restricting signs retains the upper bound, but does not imply attainment. -/
theorem admissible_signed_sum_le {ι : Type*} [Fintype ι]
    (admissible : Set (ι → ℝ)) (y : ι → ℝ) (μ : ℝ)
    (hSigns : ∀ f ∈ admissible, ∀ i, IsSign (f i))
    {z : ℝ} (hz : z ∈ admissibleSignedValues admissible y μ) :
    z ≤ (∑ i, |y i|) + |μ| := by
  obtain ⟨f, hf, rfl⟩ := hz
  exact abs_signed_sum_add_le y f μ (hSigns f hf)

/-- The free-sign maximum transfers only after the domain-collapse premise. -/
theorem max_abs_admissible_signed_sum_of_sign_set_eq
    {ι : Type*} [Fintype ι]
    (admissible : Set (ι → ℝ)) (y : ι → ℝ) (μ : ℝ)
    (hCollapse : admissible = {f | ∀ i, IsSign (f i)}) :
    IsGreatest (admissibleSignedValues admissible y μ)
      ((∑ i, |y i|) + |μ|) := by
  simpa [admissibleSignedValues, hCollapse] using max_abs_signed_sum y μ

/-- A concrete inhabited instance of the domain-collapse premise. This is
not evidence that the paper's context-dependent sign sets collapse. -/
theorem full_sign_cube_collapse_instance :
    ({f : Fin 1 → ℝ | ∀ i, IsSign (f i)} : Set (Fin 1 → ℝ)) =
      {f | ∀ i, IsSign (f i)} := rfl

end AgtXIv.Stabilizerness
