import SignedGeneratorCompletion

/-!
General physicality of maximal signed context candidates on the source's
no-active-dependency branch. A complete signed frame is constructed, retaining
every selected signed observable. Its projected atom is exactly the candidate,
so a singleton convex combination discharges candidatePhysical.

There is no full-rank condition on the measured context and no supplied
extension, convex-decomposition, or VRepRepairObligations certificate.
The reverse atom-refinement direction remains a separate obligation.
Source: arXiv:2607.26154v1 draft.tex:134--155, 223--231, 498--509.
-/

namespace AgtXIv.Varela.MeasurementWindow

open AgtXIv.Stabilizer

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

/-- Construct a complete frame containing each actual selected signed Pauli,
including phases. Its extension is a proved output, not a hypothesis. -/
theorem exists_completeFrame_realizing_maximalContext
    (hNoActive : W.NoActiveDependencies) (c : W.MaximalSignedContext) :
    ∃ E : IndependentSignedPauliFrame n n,
      ∀ i ∈ c.support, ∃ a : BinaryWord n, E.eval a = W.signedObservable c.sign i := by
  let G := W.signedContextGenerators c.support c.maximal.1 c.sign
  have hg : LinearIndependent F2 (fun j => F2Support.pauli (G.generator j)) :=
    W.signedContextGenerators_support_independent c.support c.maximal.1
      (W.context_support_independent_of_noActiveDependencies hNoActive c.support c.maximal.1) c.sign
  obtain ⟨E, hE⟩ := G.exists_complete_frame hg
  refine ⟨E, ?_⟩
  intro i hi
  obtain ⟨a, ha⟩ := hE ((contextEnumeration c.support).symm ⟨i, hi⟩)
  exact ⟨a, by simpa [G, signedContextGenerators] using ha⟩

/-- Exact observable-level containment in a signed frame determines the
projection of its normalized code state for a maximal measured context. -/
theorem codeState_projection_eq_maximalContext {r : ℕ}
    (c : W.MaximalSignedContext) (E : IndependentSignedPauliFrame n r)
    (hContains : ∀ i ∈ c.support, ∃ a : BinaryWord r,
      E.eval a = W.signedObservable c.sign i) :
    W.expectationProjection E.codeState.toTraceOneHermitian.1 =
      MaximalSignedContext.vector W c := by
  classical
  funext i
  change (Matrix.trace ((W.observable i).toCMatrix * E.codeStateMatrix)).re = _
  by_cases hi : i ∈ c.support
  · obtain ⟨a, ha⟩ := hContains i hi
    have he := E.eval_mul_codeStateMatrix a
    rw [ha] at he
    have ht := congrArg (fun A => (Matrix.trace A).re) he
    rw [E.codeStateMatrix_trace_one] at ht
    rw [MaximalSignedContext.vector_of_mem W c hi]
    cases hs : c.sign i
    · simpa [signedObservable, hs] using ht
    · simp only [signedObservable, hs, ite_true, Pauli.toCMatrix_neg,
        Matrix.neg_mul, Matrix.trace_neg, Complex.neg_re, Complex.one_re] at ht
      change _ = (-1 : ℝ)
      linarith
  · obtain ⟨j, hj, hnot⟩ := W.exists_not_commutes_of_not_mem_maximal c i hi
    obtain ⟨a, ha⟩ := hContains j hj
    have hnot' : ¬ (W.observable i).commutesWith (E.eval a) := by
      rw [ha]
      cases hs : c.sign j <;>
        simpa [signedObservable, hs, Pauli.commutesWith, Pauli.phaseFlipsWith] using hnot
    rw [E.trace_mul_codeStateMatrix_zero_of_not_commutes (W.observable i) a hnot',
      MaximalSignedContext.vector_of_not_mem W c hi]
    rfl

/-- The maximal-context candidate is exactly one actual projected pure
stabilizer atom, even if its measured context has fewer than n elements. -/
theorem exists_projectedFrameAtom_eq_maximalContext
    (hNoActive : W.NoActiveDependencies) (c : W.MaximalSignedContext) :
    ∃ E : IndependentSignedPauliFrame n n,
      W.projectedFrameAtom E = MaximalSignedContext.vector W c := by
  obtain ⟨E, hContains⟩ := W.exists_completeFrame_realizing_maximalContext hNoActive c
  obtain ⟨E', hAtom⟩ := E.codeState_eq_completeFrameAtom_of_rank_eq rfl
  refine ⟨E', ?_⟩
  unfold projectedFrameAtom
  rw [← hAtom]
  exact W.codeState_projection_eq_maximalContext c E hContains

/-- General candidate physicality on the no-active-dependency branch,
with actual singleton nonnegative coefficients from the constructed frame. -/
theorem candidatePhysical_of_noActiveDependencies
    (hNoActive : W.NoActiveDependencies) (c : W.MaximalSignedContext) :
    AgtXIv.RoM.FreeByAtoms W.projectedFrameAtom (MaximalSignedContext.vector W c) := by
  obtain ⟨E, hE⟩ := W.exists_projectedFrameAtom_eq_maximalContext hNoActive c
  rw [← hE]
  exact CanonicalAtomAux.atom_mem_freeByAtoms W.projectedFrameAtom E

end

end AgtXIv.Varela.MeasurementWindow
