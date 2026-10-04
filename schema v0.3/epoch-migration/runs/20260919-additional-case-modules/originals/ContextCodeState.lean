import NoActiveDependencies

/-!
An actual density-matrix bridge for maximal signed measurement contexts.
We construct the phase-aware context frame, normalize its group-average
projector by Hilbert-space dimension, and derive every projected coordinate.
Positivity comes from the existing code-projector theorem, not affine-span
feasibility. No complete-frame convex decomposition is assumed or asserted.

Source: arXiv:2607.26154v1 draft.tex:134--155, 223--231, 498--509.
The remaining general physicality step is extension of this partial frame to
a complete signed Pauli frame (or an explicit positive decomposition into
complete-frame atoms). Affine completeness alone does not supply that step.
-/

open scoped BigOperators ComplexOrder

namespace AgtXIv.Stabilizer.IndependentSignedPauliFrame

noncomputable section

variable {n r : ℕ}

/-- Trace-normalized code state, with normalization independent of code rank. -/
def codeStateMatrix (F : IndependentSignedPauliFrame n r) : CMatrix (2 ^ n) (2 ^ n) :=
  (2 ^ n : ℂ)⁻¹ • ∑ a : BinaryWord r, (F.eval a).toCMatrix

theorem codeStateMatrix_eq_scaled_projector (F : IndependentSignedPauliFrame n r) :
    F.codeStateMatrix =
      ((Fintype.card (BinaryWord r) : ℂ) / (2 ^ n : ℂ)) • stabilizerCodeProjectorMatrix F := by
  unfold codeStateMatrix stabilizerCodeProjectorMatrix
  rw [smul_smul]
  congr 1
  rw [invOf_eq_inv]
  have hc : (Fintype.card (BinaryWord r) : ℂ) ≠ 0 :=
    Nat.cast_ne_zero.mpr Fintype.card_ne_zero
  field_simp

theorem codeStateMatrix_posSemidef (F : IndependentSignedPauliFrame n r) :
    F.codeStateMatrix.PosSemidef := by
  rw [F.codeStateMatrix_eq_scaled_projector]
  apply (stabilizerCodeProjectorMatrix_posSemidef F).smul
  have hpos : (0 : ℂ) ≤ (((Fintype.card (BinaryWord r) : ℝ) / (2 ^ n : ℝ) : ℝ) : ℂ) := by
    refine ⟨?_, rfl⟩
    change (0 : ℝ) ≤ (Fintype.card (BinaryWord r) : ℝ) / (2 ^ n : ℝ)
    positivity
  simpa using hpos

theorem codeStateMatrix_trace_one (F : IndependentSignedPauliFrame n r) :
    Matrix.trace F.codeStateMatrix = 1 := by
  classical
  have hsum : ∑ a : BinaryWord r, Matrix.trace (F.eval a).toCMatrix = (2 ^ n : ℂ) := by
    calc
      _ = ∑ a : BinaryWord r, if a = 1 then (2 ^ n : ℂ) else 0 := by
        apply Finset.sum_congr rfl
        intro a _
        by_cases ha : a = 1
        · subst a
          simp
        · simp [ha, F.trace_eval_eq_zero_of_label_ne_one a ha]
      _ = _ := by simp
  rw [codeStateMatrix, Matrix.trace_smul, Matrix.trace_sum, hsum, smul_eq_mul]
  exact inv_mul_cancel₀ (by positivity)

/-- The code state is a positive trace-one density matrix for every actual frame. -/
def codeState (F : IndependentSignedPauliFrame n r) : DensityMatrix (2 ^ n) where
  val := F.codeStateMatrix
  posSemidef := F.codeStateMatrix_posSemidef
  trace_one := F.codeStateMatrix_trace_one

/-- Each signed frame element fixes the normalized code state on the left. -/
theorem eval_mul_codeStateMatrix (F : IndependentSignedPauliFrame n r) (a : BinaryWord r) :
    (F.eval a).toCMatrix * F.codeStateMatrix = F.codeStateMatrix := by
  unfold codeStateMatrix
  rw [Matrix.mul_smul, Finset.mul_sum]
  congr 1
  calc
    (∑ b : BinaryWord r, (F.eval a).toCMatrix * (F.eval b).toCMatrix) =
        ∑ b : BinaryWord r, (F.eval (a * b)).toCMatrix := by
      apply Finset.sum_congr rfl
      intro b _
      rw [map_mul, Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
    _ = _ := (Equiv.mulLeft a).bijective.sum_comp (fun b => (F.eval b).toCMatrix)

/-- An observable incompatible with one frame element has no trace overlap
with any frame word. This retains the actual Pauli phase and uses binary
support only to rule out scalar products. -/
theorem trace_mul_eval_zero_of_not_commutes
    (F : IndependentSignedPauliFrame n r) (P : Pauli n) (b : BinaryWord r)
    (hNot : ¬ P.commutesWith (F.eval b)) (a : BinaryWord r) :
    Matrix.trace (P.toCMatrix * (F.eval a).toCMatrix) = 0 := by
  rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
  apply trace_eval_eq_zero_of_support_ne_zero
  by_contra h
  push Not at h
  have hs : F2Support.pauli P + F2Support.pauli (F.eval a) = 0 := by
    rw [← F2Support.pauli_mul]
    ext <;> simp [F2Support.pauli, h.1, h.2]
  have heq : F2Support.pauli P = F2Support.pauli (F.eval a) := by
    exact (eq_neg_of_add_eq_zero_left hs).trans (by rfl)
  have hc : Commute (F.eval a) (F.eval b) := by
    rw [commute_iff_eq, ← map_mul, ← map_mul, mul_comm]
  have hz := (F2Support.pauli_commutes_iff_symplectic_eq_zero _ _).mp
    (Pauli.commutesWith_of_commute _ _ hc)
  apply hNot
  apply (F2Support.pauli_commutes_iff_symplectic_eq_zero _ _).mpr
  rw [heq]
  exact hz

theorem trace_mul_codeStateMatrix_zero_of_not_commutes
    (F : IndependentSignedPauliFrame n r) (P : Pauli n) (b : BinaryWord r)
    (hNot : ¬ P.commutesWith (F.eval b)) :
    Matrix.trace (P.toCMatrix * F.codeStateMatrix) = 0 := by
  unfold codeStateMatrix
  rw [Matrix.mul_smul, Finset.mul_sum, Matrix.trace_smul, Matrix.trace_sum]
  simp [F.trace_mul_eval_zero_of_not_commutes P b hNot]

/-- At full rank the constructed density is exactly the existing pure frame
atom, so no convex-decomposition obligation remains in this subcase. -/
theorem codeState_eq_completeFrameAtom_of_rank_eq
    (F : IndependentSignedPauliFrame n r) (hr : r = n) :
    ∃ E : IndependentSignedPauliFrame n n,
      F.codeState.toTraceOneHermitian.1 = completeFrameHermitianAtom n E := by
  subst r
  refine ⟨F, ?_⟩
  apply Subtype.ext
  change F.codeStateMatrix = stabilizerProjectorMatrix F
  simp only [codeStateMatrix, stabilizerProjectorMatrix,
    AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card, Nat.cast_pow, Nat.cast_ofNat,
    invOf_eq_inv]

end

end AgtXIv.Stabilizer.IndependentSignedPauliFrame

namespace AgtXIv.Varela.MeasurementWindow

open AgtXIv.Stabilizer

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

/-- The concrete signed context becomes an actual independent frame under
the source no-active-dependency hypothesis. -/
def maximalContextFrame (hNoActive : W.NoActiveDependencies) (c : W.MaximalSignedContext) :
    IndependentSignedPauliFrame n c.support.card where
  eval := (W.signedContextGenerators c.support c.maximal.1 c.sign).wordProductHom
  independent :=
    (W.signedContextGenerators c.support c.maximal.1 c.sign).wordProduct_injective_of_support_independent
      (W.signedContextGenerators_support_independent c.support c.maximal.1
        (W.context_support_independent_of_noActiveDependencies hNoActive c.support c.maximal.1) c.sign)
  minusOneExcluded :=
    (W.signedContextGenerators c.support c.maximal.1 c.sign).wordProduct_ne_minus_one_of_support_independent
      (W.signedContextGenerators_support_independent c.support c.maximal.1
        (W.context_support_independent_of_noActiveDependencies hNoActive c.support c.maximal.1) c.sign)

theorem signedObservable_mem_contextFrame (hNoActive : W.NoActiveDependencies)
    (c : W.MaximalSignedContext) (i : Fin m) (hi : i ∈ c.support) :
    ∃ a, (W.maximalContextFrame hNoActive c).eval a = W.signedObservable c.sign i := by
  refine ⟨CommutingInvolutivePauliGenerators.basisWord ((contextEnumeration c.support).symm ⟨i, hi⟩), ?_⟩
  change (W.signedContextGenerators c.support c.maximal.1 c.sign).wordProduct
    (CommutingInvolutivePauliGenerators.basisWord ((contextEnumeration c.support).symm ⟨i, hi⟩)) =
      W.signedObservable c.sign i
  rw [CommutingInvolutivePauliGenerators.wordProduct_basisWord]
  simp [signedContextGenerators]

/-- Maximality is by inclusion in the measured window: every omitted
observable is incompatible with at least one included observable. -/
theorem exists_not_commutes_of_not_mem_maximal (c : W.MaximalSignedContext)
    (i : Fin m) (hi : i ∉ c.support) :
    ∃ j ∈ c.support, ¬ (W.observable i).commutesWith (W.observable j) := by
  classical
  by_contra h
  push Not at h
  have hins : W.IsCommutingContext (insert i c.support) := by
    intro a ha b hb hab
    rcases Finset.mem_insert.mp ha with hai | haS
    · subst a
      rcases Finset.mem_insert.mp hb with hbi | hbS
      · exact (hab hbi.symm).elim
      · exact h b hbS
    · rcases Finset.mem_insert.mp hb with hbi | hbS
      · subst b
        rw [Pauli.commutesWith_comm]
        exact h a haS
      · exact c.maximal.1 haS hbS hab
  have heq := c.maximal.2 (insert i c.support) hins (Finset.subset_insert _ _)
  apply hi
  rw [← heq]
  exact Finset.mem_insert_self _ _

theorem contextCodeState_expectation (hNoActive : W.NoActiveDependencies)
    (c : W.MaximalSignedContext) (i : Fin m) :
    (Matrix.trace ((W.observable i).toCMatrix *
      (W.maximalContextFrame hNoActive c).codeStateMatrix)).re =
      MaximalSignedContext.vector W c i := by
  classical
  by_cases hi : i ∈ c.support
  · obtain ⟨a, ha⟩ := W.signedObservable_mem_contextFrame hNoActive c i hi
    have he := (W.maximalContextFrame hNoActive c).eval_mul_codeStateMatrix a
    rw [ha] at he
    have ht := congrArg (fun A => (Matrix.trace A).re) he
    dsimp only at ht
    rw [(W.maximalContextFrame hNoActive c).codeStateMatrix_trace_one] at ht
    rw [MaximalSignedContext.vector_of_mem W c hi]
    cases hs : c.sign i
    · simpa [signedObservable, hs] using ht
    · simp only [signedObservable, hs, ite_true,
        Pauli.toCMatrix_neg, Matrix.neg_mul, Matrix.trace_neg, Complex.neg_re, Complex.one_re] at ht
      change _ = (-1 : ℝ)
      linarith
  · obtain ⟨j, hj, hnot⟩ := W.exists_not_commutes_of_not_mem_maximal c i hi
    obtain ⟨a, ha⟩ := W.signedObservable_mem_contextFrame hNoActive c j hj
    have hnot' : ¬ (W.observable i).commutesWith
        ((W.maximalContextFrame hNoActive c).eval a) := by
      rw [ha]
      cases hs : c.sign j <;>
        simpa [signedObservable, hs, Pauli.commutesWith, Pauli.phaseFlipsWith] using hnot
    rw [(W.maximalContextFrame hNoActive c).trace_mul_codeStateMatrix_zero_of_not_commutes
      (W.observable i) a hnot', MaximalSignedContext.vector_of_not_mem W c hi]
    rfl

/-- A genuine positive trace-one matrix projects exactly to the candidate.
This is not yet a proof of membership in the stabilizer convex hull. -/
theorem exists_density_projecting_to_maximalContext
    (hNoActive : W.NoActiveDependencies) (c : W.MaximalSignedContext) :
    ∃ ρ : DensityMatrix (2 ^ n),
      W.expectationProjection ρ.toTraceOneHermitian.1 = MaximalSignedContext.vector W c := by
  refine ⟨(W.maximalContextFrame hNoActive c).codeState, ?_⟩
  funext i
  exact W.contextCodeState_expectation hNoActive c i

/-- An actual singleton convex combination for a full-rank maximal context.
The extra cardinality hypothesis is explicit; this is not general physicality. -/
theorem candidatePhysical_of_full_rank_context
    (hNoActive : W.NoActiveDependencies) (c : W.MaximalSignedContext)
    (hRank : c.support.card = n) :
    AgtXIv.RoM.FreeByAtoms W.projectedFrameAtom (MaximalSignedContext.vector W c) := by
  obtain ⟨E, hE⟩ := (W.maximalContextFrame hNoActive c).codeState_eq_completeFrameAtom_of_rank_eq hRank
  have hp : W.projectedFrameAtom E = MaximalSignedContext.vector W c := by
    unfold projectedFrameAtom
    rw [← hE]
    funext i
    exact W.contextCodeState_expectation hNoActive c i
  rw [← hp]
  exact CanonicalAtomAux.atom_mem_freeByAtoms W.projectedFrameAtom E

end

end AgtXIv.Varela.MeasurementWindow
