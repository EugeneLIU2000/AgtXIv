module

public import AgtXIvRootMath.GottesmanGroupAverage
public import Mathlib.RepresentationTheory.Character

/-!
# Character criterion for a one-dimensional common fixed space

This file proves the exact representation-theoretic step behind the rank-one
stabilizer specialization.  It deliberately does not assume the desired fixed
space dimension.  Instead it derives that dimension from a delta-shaped
character profile: the identity has trace equal to the group cardinality and
every nonidentity element has trace zero.

The later Pauli module must prove that an actual phase-clean rank-`n` Pauli
stabilizer representation has this character profile and has cardinality equal
to the Hilbert-space dimension.
-/

@[expose] public section

namespace AgtXIv.Gottesman

open Representation
open scoped BigOperators

variable {G : Type} [Group G] [Fintype G] [DecidableEq G]
variable [Invertible (Fintype.card G : ℂ)]

/-- A finite-dimensional complex representation whose character is the group
cardinality at the identity and zero away from the identity has a
one-dimensional invariant subspace. -/
theorem finrank_commonFixed_eq_one_of_character_delta
    (V : FDRep ℂ G)
    (hCharacter : ∀ g : G,
      V.character g = if g = 1 then (Fintype.card G : ℂ) else 0) :
    Module.finrank ℂ (commonFixedSpace V.ρ) = 1 := by
  classical
  have hCast :
      (Module.finrank ℂ (commonFixedSpace V.ρ) : ℂ) = 1 := by
    rw [← V.average_char_eq_finrank_invariants]
    simp_rw [hCharacter]
    simp
  exact_mod_cast hCast

end AgtXIv.Gottesman
