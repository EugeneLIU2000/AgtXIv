import AnticommutingParityPatterns
import JointEigenvalueFilters

/-! Uncompiled bridge from mod-two exponents to scalar eigenvalues.
The explicit hypothesis (2 : K) ≠ 0 prevents collapse of the two signs.
Actual generator products and their conjugation formula remain to be supplied.
-/

namespace AgtXIv.AnticommutingSignCharacters

open AgtXIv.AnticommutingParityPatterns

variable {K : Type*} [Field K]

def sign (a : ZMod 2) : K := if a = 0 then 1 else -1

theorem two_cases (a : ZMod 2) : a = 0 ∨ a = 1 := by
  have hlt := ZMod.val_lt a
  have hv : a.val = 0 ∨ a.val = 1 := by omega
  rcases hv with hv | hv
  · left
    rw [← ZMod.natCast_zmod_val a, hv]
    rfl
  · right
    rw [← ZMod.natCast_zmod_val a, hv]
    rfl

theorem sign_injective (htwo : (2 : K) ≠ 0) : Function.Injective (sign (K := K)) := by
  have hsign : (1 : K) ≠ -1 := by
    intro h
    apply htwo
    calc
      (2 : K) = 1 + 1 := by ring
      _ = -1 + 1 := congrArg (fun a : K => a + 1) h
      _ = 0 := neg_add_cancel 1
  intro a b hab
  rcases two_cases a with rfl | rfl <;>
    rcases two_cases b with rfl | rfl <;>
    simp_all [sign, hsign, Ne.symm hsign]

theorem sign_add (a b : ZMod 2) : sign (K := K) (a + b) = sign a * sign b := by
  rcases two_cases a with rfl | rfl <;>
    rcases two_cases b with rfl | rfl
  · simp [sign]
  · simp [sign]
  · simp [sign]
  · have h11 : (1 : ZMod 2) + 1 = 0 := by decide
    simp [sign, h11]

theorem distinct_supports_have_distinct_sign {m : ℕ} (hm : Even m)
    (htwo : (2 : K) ≠ 0) (x y : Fin m → ZMod 2) (hxy : x ≠ y) :
    ∃ i, sign (K := K) (code x i) ≠ sign (code y i) := by
  obtain ⟨i, hi⟩ := distinct_supports_have_distinct_exponent hm x y hxy
  exact ⟨i, fun h => hi (sign_injective htwo h)⟩

-- This connects the uncompiled combinatorial candidates to the general
-- separator construction. hEigen is an explicit remaining instantiation task,
-- not an assumed theorem about the historical matrices or the query's Paulis.
theorem linearIndependent_of_code_eigenvectors {m : ℕ}
    {V : Type*} [AddCommGroup V] [Module K V]
    (hm : Even m) (htwo : (2 : K) ≠ 0)
    (C : Fin m → V →ₗ[K] V) (v : (Fin m → ZMod 2) → V)
    (hne : ∀ x, v x ≠ 0)
    (hEigen : ∀ i x, C i (v x) = sign (K := K) (code x i) • v x) :
    LinearIndependent K v := by
  apply AgtXIv.JointEigenvalueFilters.linearIndependent_of_distinct_joint_eigenvalues
    C v (fun i x => sign (K := K) (code x i)) hne hEigen
  intro x y hxy
  exact distinct_supports_have_distinct_sign hm htwo x y hxy

end AgtXIv.AnticommutingSignCharacters
