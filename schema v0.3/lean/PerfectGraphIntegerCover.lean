import PerfectGraphIntegerReplication

/-!
Actual optimal integer-weight clique covers of perfect graphs. Independent
copies encode multiplicities; a complement colouring separates copies in each
fibre. Projected colour classes are genuine original cliques. Their integer
multiplicities define the existing IsFractionalCliqueCover, with cost equal to
the existing maxWeightIndependent on natural weights.
-/

namespace AgtXIv.PerfectGraph

open AgtXIv.GraphFoundation
open scoped BigOperators

noncomputable section

variable {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V)

/-- Multiplicity of each clique in an explicitly indexed finite family. -/
def cliqueFamilyMultiplicity {I : Type*} [Fintype I] (Q : I → Finset V) (S : Finset V) : ℝ := by
  classical
  exact ((Finset.univ.filter fun i => Q i = S).card : ℝ)

theorem cliqueFamilyMultiplicity_nonneg {I : Type*} [Fintype I]
    (Q : I → Finset V) (S : Finset V) : 0 ≤ cliqueFamilyMultiplicity Q S := by
  unfold cliqueFamilyMultiplicity
  positivity

/-- Repeated equal cliques are counted, not discarded. -/
theorem cliqueFamilyMultiplicity_cost {I : Type*} [Fintype I]
    (Q : I → Finset V) (hQ : ∀ i, G.IsClique (Q i : Set V)) :
    (∑ S ∈ cliqueFinsets G, cliqueFamilyMultiplicity Q S) = Fintype.card I := by
  classical
  have hMaps (i : I) (_ : i ∈ (Finset.univ : Finset I)) : Q i ∈ cliqueFinsets G := by
    simp [cliqueFinsets, hQ i]
  have h := Finset.card_eq_sum_card_fiberwise hMaps
  unfold cliqueFamilyMultiplicity
  rw [← Finset.card_univ]
  exact_mod_cast h.symm

/-- The coverage contribution of a finite clique family is unchanged by grouping. -/
theorem cliqueFamilyMultiplicity_coverage {I : Type*} [Fintype I]
    (Q : I → Finset V) (hQ : ∀ i, G.IsClique (Q i : Set V)) (v : V) :
    (∑ S ∈ cliqueFinsets G, if v ∈ S then cliqueFamilyMultiplicity Q S else 0) =
      ∑ i, if v ∈ Q i then (1 : ℝ) else 0 := by
  classical
  have hMaps (i : I) (_ : i ∈ (Finset.univ : Finset I)) : Q i ∈ cliqueFinsets G := by
    simp [cliqueFinsets, hQ i]
  have h := Finset.sum_fiberwise_of_maps_to' hMaps (fun S => if v ∈ S then (1 : ℝ) else 0)
  simpa [cliqueFamilyMultiplicity, Finset.sum_const, nsmul_eq_mul, mul_ite] using h

variable (w : V → ℕ) {k : ℕ}
variable (C : (independentBlowup G w)ᶜ.Coloring (Fin k))

/-- Project an actual colour class of the complement of the copied graph. -/
def integerProjectedClique (i : Fin k) : Finset V := by
  classical
  exact Finset.univ.filter fun v => ∃ j : Fin (w v), C ⟨v, j⟩ = i

theorem integerProjectedClique_isClique (i : Fin k) :
    G.IsClique (integerProjectedClique G w C i : Set V) := by
  classical
  intro a ha b hb hne
  obtain ⟨j, hj⟩ := (Finset.mem_filter.mp ha).2
  obtain ⟨l, hl⟩ := (Finset.mem_filter.mp hb).2
  by_contra hadj
  have hCopies : (⟨a, j⟩ : Σ v, Fin (w v)) ≠ ⟨b, l⟩ := fun heq => hne (congrArg Sigma.fst heq)
  have hAdj : (independentBlowup G w)ᶜ.Adj ⟨a, j⟩ ⟨b, l⟩ := by
    exact ⟨hCopies, fun h => hadj ((independentBlowup_adj G w _ _).mp h)⟩
  exact C.valid hAdj (hj.trans hl.symm)

/-- Copies of one vertex have distinct colours in the complemented graph. -/
theorem independentCopies_colors_injective (v : V) :
    Function.Injective (fun j : Fin (w v) => C ⟨v, j⟩) := by
  intro j l hEq
  by_contra hne
  have hCopies : (⟨v, j⟩ : Σ a, Fin (w a)) ≠ ⟨v, l⟩ := by simpa using hne
  have hAdj : (independentBlowup G w)ᶜ.Adj ⟨v, j⟩ ⟨v, l⟩ := by
    refine ⟨hCopies, ?_⟩
    rw [independentBlowup_adj]
    exact G.loopless.irrefl v
  exact C.valid hAdj hEq

/-- Projection covers each original vertex exactly its prescribed multiplicity. -/
theorem integerProjectedClique_coverage (v : V) :
    (∑ i : Fin k, if v ∈ integerProjectedClique G w C i then (1 : ℝ) else 0) = w v := by
  classical
  have hSet : (Finset.univ.filter fun i => v ∈ integerProjectedClique G w C i) =
      (Finset.univ : Finset (Fin (w v))).image (fun j => C ⟨v, j⟩) := by
    ext i
    simp [integerProjectedClique]
  rw [← Finset.sum_filter, Finset.sum_const, nsmul_eq_mul, mul_one, hSet]
  rw [Finset.card_image_of_injective _ (independentCopies_colors_injective G w C v)]
  simp

/-- Integer weights attain weighted independence by a genuine integer clique
cover, expressed using the existing real-valued cover and weighted maximum. -/
theorem exists_integer_optimal_fractionalCliqueCover (hG : IsPerfect G) :
    ∃ lam : Finset V → ℝ,
      IsFractionalCliqueCover G (fun v => (w v : ℝ)) lam ∧
      (∑ Q ∈ cliqueFinsets G, lam Q) = maxWeightIndependent G (fun v => (w v : ℝ)) ∧
      ∀ Q, ∃ n : ℕ, lam Q = n := by
  classical
  let K := independentBlowup G w
  obtain ⟨C⟩ := complement_colorable_indepNum K (independentBlowup_isPerfect G w hG)
  let Q := integerProjectedClique G w C
  have hQ (i : Fin K.indepNum) : G.IsClique (Q i : Set V) := integerProjectedClique_isClique G w C i
  refine ⟨cliqueFamilyMultiplicity Q, ⟨?_, ?_⟩, ?_, ?_⟩
  · intro S _
    exact cliqueFamilyMultiplicity_nonneg Q S
  · intro v
    rw [cliqueFamilyMultiplicity_coverage G Q hQ, integerProjectedClique_coverage]
  · rw [cliqueFamilyMultiplicity_cost G Q hQ, Fintype.card_fin]
    exact independentBlowup_indepNum_eq_weightedMax G w
  · intro S
    exact ⟨(Finset.univ.filter fun i => Q i = S).card, rfl⟩

end
end AgtXIv.PerfectGraph
