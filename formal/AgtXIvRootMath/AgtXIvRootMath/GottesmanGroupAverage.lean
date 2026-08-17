module

public import Mathlib.RepresentationTheory.Invariants
public import Mathlib.Data.Complex.Basic

/-!
# Finite-group averaging and the common fixed space

This file isolates an exact algebraic component of the stabilizer fixed-space
construction.  It is deliberately stated for an arbitrary finite group
representation.  The later Pauli-specific bridge must still prove that the
chosen stabilizer subgroup and its action satisfy these hypotheses, and must
separately establish the dimension of the fixed space.
-/

@[expose] public section

namespace AgtXIv.Gottesman

open Representation

variable {G V : Type*} [Group G] [Fintype G]
variable [AddCommGroup V] [Module ℂ V]
variable [Invertible (Fintype.card G : ℂ)]

/-- The abstract common fixed space of a finite group representation. -/
noncomputable abbrev commonFixedSpace (ρ : Representation ℂ G V) : Submodule ℂ V :=
  Representation.invariants ρ

/-- The normalized average of the finite group action. -/
noncomputable abbrev groupAverageMap (ρ : Representation ℂ G V) : V →ₗ[ℂ] V :=
  Representation.averageMap ρ

/-- Averaging any vector produces a vector fixed by every group element. -/
theorem groupAverage_mem_commonFixed (ρ : Representation ℂ G V) (v : V) :
    groupAverageMap ρ v ∈ commonFixedSpace ρ :=
  ρ.averageMap_invariant v

/-- The group average fixes exactly the vectors in the common fixed space. -/
theorem groupAverage_eq_self_iff (ρ : Representation ℂ G V) (v : V) :
    groupAverageMap ρ v = v ↔ v ∈ commonFixedSpace ρ := by
  constructor
  · intro h
    rw [← h]
    exact groupAverage_mem_commonFixed ρ v
  · exact ρ.averageMap_id v

/-- Applying the group average twice is the same as applying it once. -/
theorem groupAverage_idempotent (ρ : Representation ℂ G V) (v : V) :
    groupAverageMap ρ (groupAverageMap ρ v) = groupAverageMap ρ v :=
  ρ.averageMap_id _ (groupAverage_mem_commonFixed ρ v)

/-- The range of the averaging map is exactly the common fixed space. -/
theorem range_groupAverageMap (ρ : Representation ℂ G V) :
    LinearMap.range (groupAverageMap ρ) = commonFixedSpace ρ := by
  apply le_antisymm
  · rintro _ ⟨v, rfl⟩
    exact groupAverage_mem_commonFixed ρ v
  · intro v hv
    exact ⟨v, (groupAverage_eq_self_iff ρ v).2 hv⟩

/-- The averaging map is a projection onto the common fixed space. -/
theorem groupAverage_isProjection (ρ : Representation ℂ G V) :
    LinearMap.IsProj (commonFixedSpace ρ) (groupAverageMap ρ) :=
  ρ.isProj_averageMap

end AgtXIv.Gottesman
