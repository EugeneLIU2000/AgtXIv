import Mathlib.Combinatorics.SimpleGraph.Clique
import Mathlib.Combinatorics.SimpleGraph.Coloring.VertexColoring
import Mathlib.Data.Real.Archimedean

/-!
# Explicit interface for the external perfect-graph foundation

This file does not assert Chvátal's theorem as a Lean axiom.  It fixes the
finite weighted stable-set and fractional clique-cover quantities used by the
paper and packages the weighted duality theorem as an explicit proposition.
Every downstream result must receive a proof of that proposition as an input.
-/

namespace AgtXIv.GraphFoundation

open scoped BigOperators

noncomputable def independentFinsets {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) : Finset (Finset V) := by
  classical
  exact Finset.univ.powerset.filter fun S => G.IsIndepSet (S : Set V)

noncomputable def maxWeightIndependent {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) : ℝ := by
  classical
  let family := independentFinsets G
  have hfamily : family.Nonempty := by
    refine ⟨∅, ?_⟩
    simp [family, independentFinsets]
  exact family.sup' hfamily fun S => ∑ v ∈ S, w v

noncomputable def cliqueFinsets {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) : Finset (Finset V) := by
  classical
  exact Finset.univ.powerset.filter fun Q => G.IsClique (Q : Set V)

noncomputable def IsFractionalCliqueCover {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (w : V → ℝ) (lambda : Finset V → ℝ) : Prop :=
  (∀ Q ∈ cliqueFinsets G, 0 ≤ lambda Q) ∧
    ∀ v, w v ≤ ∑ Q ∈ cliqueFinsets G, if v ∈ Q then lambda Q else 0

noncomputable def fractionalCliqueCoverValue {V : Type*} [Fintype V]
    [DecidableEq V] (G : SimpleGraph V) (w : V → ℝ) : ℝ :=
  sInf {c : ℝ | ∃ lambda : Finset V → ℝ,
    IsFractionalCliqueCover G w lambda ∧
      c = ∑ Q ∈ cliqueFinsets G, lambda Q}

/-- A finite graph is perfect when every induced subgraph has matching
chromatic and clique numbers. -/
def IsPerfect {V : Type*} (G : SimpleGraph V) : Prop :=
  ∀ S : Set V,
    (G.induce S).chromaticNumber = (G.induce S).cliqueNum

/-- The exact weighted duality certificate needed downstream for one graph. -/
def WeightedPerfectDualityCertificate {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) : Prop :=
  ∀ w : V → ℝ, (∀ v, 0 ≤ w v) →
    maxWeightIndependent G w = fractionalCliqueCoverValue G w

universe u

/-- External-foundation interface: every finite perfect graph satisfies the
weighted stable-set/fractional-clique-cover duality.  This is a proposition to
be supplied by an accepted external foundation, not an axiom declared here. -/
def WeightedPerfectGraphFoundation : Prop :=
  ∀ (V : Type u) [Fintype V] [DecidableEq V] (G : SimpleGraph V),
    IsPerfect G → WeightedPerfectDualityCertificate G

/-- Kernel-checked use of the external theorem.  The theorem itself remains an
explicit premise named `foundation`. -/
theorem weighted_duality_of_foundation
    (foundation : WeightedPerfectGraphFoundation.{u})
    {V : Type u} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) (hPerfect : IsPerfect G)
    (w : V → ℝ) (hw : ∀ v, 0 ≤ w v) :
    maxWeightIndependent G w = fractionalCliqueCoverValue G w :=
  foundation V G hPerfect w hw

end AgtXIv.GraphFoundation
