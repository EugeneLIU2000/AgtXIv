import Mathlib

/-! Uncompiled finite-filter candidates for the joint-eigenvalue independence
argument. A single operator's distinct-eigenvalue theorem is insufficient when
each conjugation has only two eigenvalues. These filters compose in a fixed order;
no commutation of the operators on the ambient space is assumed.
-/

namespace AgtXIv.JointEigenvalueFilters

variable {K V ι : Type*} [Field K] [AddCommGroup V] [Module K V]

def filter (C : V →ₗ[K] V) (a : K) : V →ₗ[K] V := C - a • LinearMap.id

theorem filter_eigenvector (C : V →ₗ[K] V) (v : V) (a b : K)
    (h : C v = b • v) : filter C a v = (b - a) • v := by
  simp [filter, h, sub_smul]

def word (C : ι → V →ₗ[K] V) (a : ι → K) : List ι → V →ₗ[K] V
  | [] => LinearMap.id
  | i :: rest => (filter (C i) (a i)).comp (word C a rest)

theorem word_eigenvector (C : ι → V →ₗ[K] V) (a b : ι → K)
    (v : V) (h : ∀ i, C i v = b i • v) (indices : List ι) :
    word C a indices v =
      (indices.map (fun i => b i - a i)).prod • v := by
  induction indices with
  | nil => simp [word]
  | cons i rest ih =>
      simp only [word, LinearMap.comp_apply, ih, map_smul,
        List.map_cons, List.prod_cons]
      rw [filter_eigenvector (C i) v (a i) (b i) (h i), smul_smul]
      rw [mul_comm]

-- An explicitly separating family suffices to read every coefficient of a
-- finite relation. The finite construction from differing joint eigenvalues
-- appears below; this helper alone does not supply it.
theorem linearIndependent_of_separators (v : ι → V)
    (P : ι → V →ₗ[K] V) (hne : ∀ i, v i ≠ 0)
    (hself : ∀ i, P i (v i) = v i)
    (hother : ∀ i j, j ≠ i → P i (v j) = 0) : LinearIndependent K v := by
  classical
  apply linearIndependent_iff'.mpr
  intro s c hrel i hi
  have hmap := congrArg (P i) hrel
  have hterm : ∀ j ∈ s, P i (c j • v j) = if j = i then c i • v i else 0 := by
    intro j hj
    by_cases hji : j = i
    · subst j
      simp [hself]
    · simp [hji, hother i j hji]
  have hcoeff : c i • v i = 0 := by
    simpa only [map_sum, map_zero, Finset.sum_congr rfl hterm,
      Finset.sum_ite_eq', if_pos hi] using hmap
  exact (smul_eq_zero.mp hcoeff).resolve_right (hne i)

-- Finite induction builds a separator without assuming a globally commuting
-- operator family or choosing one operator with an injective eigenvalue map.
theorem exists_finite_separator {J : Type*} (C : ι → V →ₗ[K] V)
    (v : J → V) (μ : ι → J → K)
    (heigen : ∀ i j, C i (v j) = μ i j • v j)
    (hdistinct : ∀ s t, s ≠ t → ∃ i, μ i s ≠ μ i t)
    (s : J) (targets : Finset J) :
    ∃ P : V →ₗ[K] V, P (v s) = v s ∧
      ∀ t ∈ targets, t ≠ s → P (v t) = 0 := by
  classical
  induction targets using Finset.induction_on with
  | empty =>
      exact ⟨LinearMap.id, rfl, by simp⟩
  | @insert t targets ht ih =>
      obtain ⟨P, hself, hkill⟩ := ih
      by_cases hts : t = s
      · refine ⟨P, hself, ?_⟩
        intro u hu hus
        rcases Finset.mem_insert.mp hu with hut | hu
        · exact (hus (hut.trans hts)).elim
        · exact hkill u hu hus
      · obtain ⟨i, hμ⟩ := hdistinct s t (Ne.symm hts)
        let δ : K := μ i s - μ i t
        have hδ : δ ≠ 0 := sub_ne_zero.mpr hμ
        let D : V →ₗ[K] V := δ⁻¹ • filter (C i) (μ i t)
        have hD (u : J) : D (v u) = (δ⁻¹ * (μ i u - μ i t)) • v u := by
          change δ⁻¹ • filter (C i) (μ i t) (v u) = _
          rw [filter_eigenvector (C i) (v u) (μ i t) (μ i u) (heigen i u),
            smul_smul]
        have hDs : D (v s) = v s := by
          rw [hD]
          change (δ⁻¹ * δ) • v s = v s
          simp [hδ]
        have hDt : D (v t) = 0 := by simp [hD]
        refine ⟨P.comp D, ?_, ?_⟩
        · simpa only [LinearMap.comp_apply, hDs] using hself
        · intro u hu hus
          rcases Finset.mem_insert.mp hu with hut | hu
          · subst u
            simp [LinearMap.comp_apply, hDt]
          · simp only [LinearMap.comp_apply, hD, map_smul, hkill u hu hus, smul_zero]

theorem linearIndependent_of_distinct_joint_eigenvalues {J : Type*} [Fintype J]
    (C : ι → V →ₗ[K] V) (v : J → V) (μ : ι → J → K)
    (hne : ∀ j, v j ≠ 0)
    (heigen : ∀ i j, C i (v j) = μ i j • v j)
    (hdistinct : ∀ s t, s ≠ t → ∃ i, μ i s ≠ μ i t) :
    LinearIndependent K v := by
  classical
  have hsep (s : J) := exists_finite_separator C v μ heigen hdistinct s Finset.univ
  choose P hself hkill using hsep
  exact linearIndependent_of_separators v P hne hself
    (fun s t hts => hkill s t (Finset.mem_univ t) hts)

end AgtXIv.JointEigenvalueFilters
