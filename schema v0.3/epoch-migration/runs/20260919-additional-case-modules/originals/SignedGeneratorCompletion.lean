import PartialFrameExtension

/-!
Complete an actual independent commuting signed Pauli generator family by
successively adjoining the new Hermitian generators constructed by the finite
symplectic extension lemma. Original generators are retained as exact Pauli
objects, including their signs. Existence of an extension is a conclusion.
-/

namespace AgtXIv.Stabilizer

noncomputable section

namespace CommutingInvolutivePauliGenerators

variable {n r : ℕ}

def prepend (G : CommutingInvolutivePauliGenerators n r) (P : Pauli n)
    (hP : P ^ 2 = 1) (hComm : ∀ i, Commute P (G.generator i)) :
    CommutingInvolutivePauliGenerators n (r + 1) where
  generator := Fin.cons P G.generator
  involutive := Fin.cases hP G.involutive
  commute i j := by
    refine Fin.cases ?_ (fun i => ?_) i
    · exact Fin.cases (Commute.refl P) (fun j => hComm j) j
    · exact Fin.cases (hComm i).symm (fun j => G.commute i j) j

theorem prepend_support_independent
    (G : CommutingInvolutivePauliGenerators n r)
    (hg : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i)))
    (P : Pauli n) (hP : P ^ 2 = 1) (hComm : ∀ i, Commute P (G.generator i))
    (hNew : F2Support.pauli P ∉ Submodule.span F2
      (Set.range (fun i => F2Support.pauli (G.generator i)))) :
    LinearIndependent F2 (fun i => F2Support.pauli ((G.prepend P hP hComm).generator i)) := by
  convert hg.finCons hNew using 1
  funext i
  exact Fin.cases rfl (fun _ => rfl) i

theorem generator_range_subset_prepend
    (G : CommutingInvolutivePauliGenerators n r)
    (P : Pauli n) (hP : P ^ 2 = 1) (hComm : ∀ i, Commute P (G.generator i)) :
    Set.range G.generator ⊆ Set.range (G.prepend P hP hComm).generator := by
  rintro _ ⟨i, rfl⟩
  exact ⟨i.succ, rfl⟩

/-- Finite recursion adds one generator per remaining dimension. Its
inclusion witness preserves the original Pauli signs exactly. -/
theorem exists_complete_generators
    (G : CommutingInvolutivePauliGenerators n r)
    (hg : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i))) :
    ∃ H : CommutingInvolutivePauliGenerators n n,
      LinearIndependent F2 (fun i => F2Support.pauli (H.generator i)) ∧
      Set.range G.generator ⊆ Set.range H.generator := by
  have main : ∀ k r : ℕ, r + k = n →
      ∀ G : CommutingInvolutivePauliGenerators n r,
        LinearIndependent F2 (fun i => F2Support.pauli (G.generator i)) →
        ∃ H : CommutingInvolutivePauliGenerators n n,
          LinearIndependent F2 (fun i => F2Support.pauli (H.generator i)) ∧
          Set.range G.generator ⊆ Set.range H.generator := by
    intro k
    induction k with
    | zero =>
        intro r hr G hg
        have hrn : r = n := by omega
        subst r
        exact ⟨G, hg, Set.Subset.rfl⟩
    | succ k ih =>
        intro r hr G hg
        obtain ⟨P, hP, hComm, hNew⟩ := G.exists_new_generator hg (by omega)
        let G' := G.prepend P hP hComm
        have hg' : LinearIndependent F2 (fun i => F2Support.pauli (G'.generator i)) :=
          G.prepend_support_independent hg P hP hComm hNew
        obtain ⟨H, hH, hSub⟩ := ih (r + 1) (by omega) G' hg'
        exact ⟨H, hH, (G.generator_range_subset_prepend P hP hComm).trans hSub⟩
  exact main (n - r) r (Nat.add_sub_of_le (G.rank_le_of_support_independent hg)) G hg

/-- Construct an independent phase-clean frame from the generators, using
the already proved support-to-exact-word injectivity and -I exclusion. -/
def frameOfSupportIndependent (G : CommutingInvolutivePauliGenerators n r)
    (hg : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i))) :
    IndependentSignedPauliFrame n r where
  eval := G.wordProductHom
  independent := G.wordProduct_injective_of_support_independent hg
  minusOneExcluded := G.wordProduct_ne_minus_one_of_support_independent hg

/-- A complete actual signed Pauli frame containing every old generator as
an actual frame word. The word witnesses retain all signs. -/
theorem exists_complete_frame
    (G : CommutingInvolutivePauliGenerators n r)
    (hg : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i))) :
    ∃ E : IndependentSignedPauliFrame n n,
      ∀ i, ∃ a : BinaryWord n, E.eval a = G.generator i := by
  obtain ⟨H, hH, hSub⟩ := G.exists_complete_generators hg
  refine ⟨H.frameOfSupportIndependent hH, ?_⟩
  intro i
  obtain ⟨j, hj⟩ := hSub (Set.mem_range_self i)
  refine ⟨basisWord j, ?_⟩
  change H.wordProduct (basisWord j) = G.generator i
  rw [H.wordProduct_basisWord, hj]

end CommutingInvolutivePauliGenerators

namespace IndependentSignedPauliFrame

variable {n r : ℕ}

/-- Canonical source generators of an existing signed frame. -/
def basisGenerators (F : IndependentSignedPauliFrame n r) :
    CommutingInvolutivePauliGenerators n r where
  generator i := F.eval (CommutingInvolutivePauliGenerators.basisWord i)
  involutive i := F.eval_sq _
  commute i j := by
    rw [commute_iff_eq, ← map_mul, ← map_mul, mul_comm]

theorem basisGenerators_support_independent (F : IndependentSignedPauliFrame n r) :
    LinearIndependent F2 (fun i => F2Support.pauli (F.basisGenerators.generator i)) := by
  exact F.generatorSupport_linearIndependent

/-- Every actual partial frame has a complete signed extension that preserves
each of its original canonical signed generators, with no rank premise. -/
theorem exists_complete_signed_extension (F : IndependentSignedPauliFrame n r) :
    ∃ E : IndependentSignedPauliFrame n n,
      ∀ i : Fin r, ∃ a : BinaryWord n,
        E.eval a = F.eval (CommutingInvolutivePauliGenerators.basisWord i) :=
  F.basisGenerators.exists_complete_frame F.basisGenerators_support_independent

end IndependentSignedPauliFrame

end

end AgtXIv.Stabilizer
