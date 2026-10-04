import MaximalContextPhysical

/-!
Actual projected complete-frame atoms have coordinates in {0,1,-1}, and their
nonzero measured support is a commuting context. These are consequences of
the exact phase-aware Pauli trace formula and the existing frame group
average, not assumptions stored in the projected atom.
-/

open scoped BigOperators

namespace AgtXIv.Stabilizer.IndependentSignedPauliFrame

noncomputable section

variable {n r : ℕ}

theorem trace_mul_eval_zero_of_support_ne
    (F : IndependentSignedPauliFrame n r) (P : Pauli n) (a : BinaryWord r)
    (hNe : F2Support.pauli P ≠ F2Support.pauli (F.eval a)) :
    Matrix.trace (P.toCMatrix * (F.eval a).toCMatrix) = 0 := by
  rw [← Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
  apply trace_eval_eq_zero_of_support_ne_zero
  by_contra h
  push Not at h
  have hs : F2Support.pauli P + F2Support.pauli (F.eval a) = 0 := by
    rw [← F2Support.pauli_mul]
    ext <;> simp [F2Support.pauli, h.1, h.2]
  exact hNe ((eq_neg_of_add_eq_zero_left hs).trans (by rfl))

theorem trace_mul_codeStateMatrix_zero_of_support_outside
    (F : IndependentSignedPauliFrame n r) (P : Pauli n)
    (hOutside : ∀ a : BinaryWord r, F2Support.pauli P ≠ F2Support.pauli (F.eval a)) :
    Matrix.trace (P.toCMatrix * F.codeStateMatrix) = 0 := by
  unfold codeStateMatrix
  rw [Matrix.mul_smul, Finset.mul_sum, Matrix.trace_smul, Matrix.trace_sum]
  simp [F.trace_mul_eval_zero_of_support_ne P _ (hOutside _)]

theorem codeStateMatrix_eq_stabilizerProjectorMatrix (F : IndependentSignedPauliFrame n n) :
    F.codeStateMatrix = stabilizerProjectorMatrix F := by
  simp only [codeStateMatrix, stabilizerProjectorMatrix,
    AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card, Nat.cast_pow, Nat.cast_ofNat,
    invOf_eq_inv]

end

end AgtXIv.Stabilizer.IndependentSignedPauliFrame

namespace AgtXIv.Varela.MeasurementWindow

open AgtXIv.Stabilizer

noncomputable section

variable {n m : ℕ} (W : MeasurementWindow n m)

theorem projectedFrameAtom_coordinate (F : IndependentSignedPauliFrame n n) (i : Fin m) :
    W.projectedFrameAtom F i =
      (Matrix.trace ((W.observable i).toCMatrix * F.codeStateMatrix)).re := by
  change (Matrix.trace ((W.observable i).toCMatrix * stabilizerProjectorMatrix F)).re = _
  rw [F.codeStateMatrix_eq_stabilizerProjectorMatrix]

/-- Exact coordinate cases, including actual signed-word witnesses in the
two nonzero cases. Support equality alone never selects the sign. -/
theorem projectedFrameAtom_coordinate_cases (F : IndependentSignedPauliFrame n n) (i : Fin m) :
    W.projectedFrameAtom F i = 0 ∨
      (W.projectedFrameAtom F i = 1 ∧ ∃ a, W.observable i = F.eval a) ∨
      (W.projectedFrameAtom F i = -1 ∧ ∃ a, W.observable i = -(F.eval a)) := by
  classical
  by_cases hMatch : ∃ a : BinaryWord n,
      F2Support.pauli (W.observable i) = F2Support.pauli (F.eval a)
  · obtain ⟨a, ha⟩ := hMatch
    have hz := congrArg (fun s : F2Support n => s.1.bits) ha
    have hx := congrArg (fun s : F2Support n => s.2.bits) ha
    change (W.observable i).z = (F.eval a).z at hz
    change (W.observable i).x = (F.eval a).x at hx
    rcases pauli_eq_or_eq_neg_of_same_support_of_sq_one (W.observable i) (F.eval a)
      hz hx (W.involutive i) (F.eval_sq a) with hPos | hNeg
    · right; left
      refine ⟨?_, a, hPos⟩
      rw [W.projectedFrameAtom_coordinate, hPos, F.eval_mul_codeStateMatrix,
        F.codeStateMatrix_trace_one]
      rfl
    · right; right
      refine ⟨?_, a, hNeg⟩
      rw [W.projectedFrameAtom_coordinate, hNeg, Pauli.toCMatrix_neg, Matrix.neg_mul,
        Matrix.trace_neg, Complex.neg_re, F.eval_mul_codeStateMatrix, F.codeStateMatrix_trace_one]
      rfl
  · left
    push Not at hMatch
    rw [W.projectedFrameAtom_coordinate,
      F.trace_mul_codeStateMatrix_zero_of_support_outside (W.observable i) hMatch]
    rfl

theorem projectedFrameAtom_ternary (F : IndependentSignedPauliFrame n n) (i : Fin m) :
    W.projectedFrameAtom F i = 0 ∨ W.projectedFrameAtom F i = 1 ∨
      W.projectedFrameAtom F i = -1 := by
  rcases W.projectedFrameAtom_coordinate_cases F i with h0 | hPos | hNeg
  · exact Or.inl h0
  · exact Or.inr (Or.inl hPos.1)
  · exact Or.inr (Or.inr hNeg.1)

theorem exists_frame_support_of_coordinate_ne_zero
    (F : IndependentSignedPauliFrame n n) (i : Fin m)
    (hi : W.projectedFrameAtom F i ≠ 0) :
    ∃ a : BinaryWord n, F2Support.pauli (W.observable i) = F2Support.pauli (F.eval a) := by
  rcases W.projectedFrameAtom_coordinate_cases F i with h0 | ⟨_, a, ha⟩ | ⟨_, a, ha⟩
  · exact (hi h0).elim
  · exact ⟨a, congrArg F2Support.pauli ha⟩
  · exact ⟨a, by simpa [Pauli.neg_eq] using congrArg F2Support.pauli ha⟩

def frameNonzeroSupport (F : IndependentSignedPauliFrame n n) : Finset (Fin m) := by
  classical
  exact Finset.univ.filter (fun i => W.projectedFrameAtom F i ≠ 0)

theorem mem_frameNonzeroSupport (F : IndependentSignedPauliFrame n n) (i : Fin m) :
    i ∈ W.frameNonzeroSupport F ↔ W.projectedFrameAtom F i ≠ 0 := by
  classical
  simp [frameNonzeroSupport]

/-- The measured support of an actual pure stabilizer atom is commuting,
although it need not be maximal in the measurement window. -/
theorem frameNonzeroSupport_commuting (F : IndependentSignedPauliFrame n n) :
    W.IsCommutingContext (W.frameNonzeroSupport F) := by
  intro i hi j hj _
  obtain ⟨a, ha⟩ := W.exists_frame_support_of_coordinate_ne_zero F i
    ((W.mem_frameNonzeroSupport F i).mp hi)
  obtain ⟨b, hb⟩ := W.exists_frame_support_of_coordinate_ne_zero F j
    ((W.mem_frameNonzeroSupport F j).mp hj)
  apply (F2Support.pauli_commutes_iff_symplectic_eq_zero _ _).mpr
  rw [ha, hb]
  apply (F2Support.pauli_commutes_iff_symplectic_eq_zero _ _).mp
  apply Pauli.commutesWith_of_commute
  rw [commute_iff_eq, ← map_mul, ← map_mul, mul_comm]

end

end AgtXIv.Varela.MeasurementWindow
