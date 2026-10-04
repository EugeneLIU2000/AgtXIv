import ContextCodeState
import Mathlib.LinearAlgebra.BilinearForm.Orthogonal

/-!
Constructive finite-dimensional extension of independent commuting Pauli
generators. The new support is chosen from the symplectic orthogonal space
outside the old span. It is lifted to an actual Hermitian Pauli and the old
signed generators are retained exactly, not only modulo phase.

The intended endpoint is a complete signed frame and the general physicality
of maximal signed contexts on the no-active-dependency branch. Each proved
stage is independently audited in the original cached Lean 4.30.0-rc2 epoch.
-/

open scoped BigOperators

namespace AgtXIv.Stabilizer

noncomputable section

namespace F2Support

theorem finrank_eq_twice (n : ℕ) : Module.finrank F2 (F2Support n) = 2 * n := by
  calc
    _ = Module.finrank F2 ((Fin n → F2) × (Fin n → F2)) :=
      (coordinateEquiv n).finrank_eq
    _ = _ := by simp [Module.finrank_prod, two_mul]

/-- A family of fewer than n supports leaves a direction in its symplectic
orthogonal space outside its span. Neither independence of that new direction
nor its existence is an assumed extension certificate. -/
theorem exists_orthogonal_outside_span {n r : ℕ} (g : Fin r → F2Support n)
    (hg : LinearIndependent F2 g) (hr : r < n) :
    ∃ u : F2Support n, u ∉ Submodule.span F2 (Set.range g) ∧
      ∀ i, symplecticForm (g i) u = 0 := by
  classical
  let S := Submodule.span F2 (Set.range g)
  have hdim : Module.finrank F2 S = r := by
    simpa [S] using finrank_span_eq_card hg
  have horth : Module.finrank F2 (symplecticForm.orthogonal S) = 2 * n - r := by
    rw [LinearMap.BilinForm.finrank_orthogonal (symplecticForm_nondegenerate n),
      finrank_eq_twice, hdim]
  have hnot : ¬ symplecticForm.orthogonal S ≤ S := by
    intro hle
    have hmono := Submodule.finrank_mono hle
    rw [horth, hdim] at hmono
    omega
  obtain ⟨u, huorth, hunot⟩ := SetLike.not_le_iff_exists.mp hnot
  refine ⟨u, hunot, ?_⟩
  intro i
  exact huorth (g i) (Submodule.subset_span (Set.mem_range_self i))

theorem span_le_orthogonal_of_isotropic {n r : ℕ} (g : Fin r → F2Support n)
    (hIso : ∀ i j, symplecticForm (g i) (g j) = 0) :
    Submodule.span F2 (Set.range g) ≤
      symplecticForm.orthogonal (Submodule.span F2 (Set.range g)) := by
  apply Submodule.span_le.mpr
  rintro _ ⟨i, rfl⟩
  intro x hx
  change symplecticForm x (g i) = 0
  refine Submodule.span_induction ?_ ?_ ?_ ?_ hx
  · rintro _ ⟨j, rfl⟩
    exact hIso j i
  · simp
  · intro x y _ _ hx hy
    simp [hx, hy]
  · intro a x _ hx
    simp [hx]

theorem isotropic_independent_card_le {n r : ℕ} (g : Fin r → F2Support n)
    (hg : LinearIndependent F2 g)
    (hIso : ∀ i j, symplecticForm (g i) (g j) = 0) : r ≤ n := by
  have hdim : Module.finrank F2 (Submodule.span F2 (Set.range g)) = r := by
    simpa using finrank_span_eq_card hg
  have hmono := Submodule.finrank_mono (span_le_orthogonal_of_isotropic g hIso)
  rw [LinearMap.BilinForm.finrank_orthogonal (symplecticForm_nondegenerate n),
    finrank_eq_twice, hdim] at hmono
  omega

/-- The canonical Hermitian representative lifts a support without changing it. -/
def hermitianRepresentative {n : ℕ} (u : F2Support n) : Pauli n :=
  hermitianSupportPauli (u.1.bits, u.2.bits)

theorem support_hermitianRepresentative {n : ℕ} (u : F2Support n) :
    pauli (hermitianRepresentative u) = u := by
  apply Prod.ext <;> apply F2Bits.ext <;>
    simp [hermitianRepresentative, pauli]

theorem hermitianRepresentative_sq {n : ℕ} (u : F2Support n) :
    hermitianRepresentative u ^ 2 = 1 := hermitianSupportPauli_sq _

end F2Support

namespace CommutingInvolutivePauliGenerators

variable {n r : ℕ}

theorem support_isotropic (G : CommutingInvolutivePauliGenerators n r) (i j : Fin r) :
    F2Support.symplecticForm (F2Support.pauli (G.generator i))
      (F2Support.pauli (G.generator j)) = 0 := by
  exact (F2Support.pauli_commutes_iff_symplectic_eq_zero _ _).mp
    (Pauli.commutesWith_of_commute _ _ (G.commute i j))

theorem rank_le_of_support_independent (G : CommutingInvolutivePauliGenerators n r)
    (hg : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i))) : r ≤ n :=
  F2Support.isotropic_independent_card_le _ hg G.support_isotropic

/-- One actual new Hermitian involution commuting with all existing signed
generators and carrying a linearly new support. -/
theorem exists_new_generator (G : CommutingInvolutivePauliGenerators n r)
    (hg : LinearIndependent F2 (fun i => F2Support.pauli (G.generator i)))
    (hr : r < n) :
    ∃ P : Pauli n, P ^ 2 = 1 ∧ (∀ i, Commute P (G.generator i)) ∧
      F2Support.pauli P ∉ Submodule.span F2 (Set.range (fun i => F2Support.pauli (G.generator i))) := by
  obtain ⟨u, hunot, huorth⟩ := F2Support.exists_orthogonal_outside_span _ hg hr
  refine ⟨F2Support.hermitianRepresentative u, F2Support.hermitianRepresentative_sq u, ?_, ?_⟩
  · intro i
    apply (Pauli.commutesWith_iff _ _).mp
    apply (F2Support.pauli_commutes_iff_symplectic_eq_zero _ _).mpr
    rw [F2Support.support_hermitianRepresentative, F2Support.symplectic_symm]
    exact huorth i
  · simpa [F2Support.support_hermitianRepresentative] using hunot

end CommutingInvolutivePauliGenerators

end

end AgtXIv.Stabilizer
