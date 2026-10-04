import AgtXIvVarela.MeasurementProjection

/-!
# Source-aligned maximal commuting contexts and admissible signs

The support records which measured observables are assigned definite values.
The sign table is admissible exactly when its signed Pauli generators do not
generate `-I`.  Inclusion-maximal means that no additional observable from the
fixed window can be added while preserving pairwise commutation; it never
means maximum cardinality.
-/

namespace AgtXIv.Varela

open AgtXIv.Stabilizer

noncomputable section

namespace MeasurementWindow

variable {n m : ℕ} (W : MeasurementWindow n m)

/-- Pairwise compatibility inside the fixed measurement window. -/
def IsCommutingContext (S : Finset (Fin m)) : Prop :=
  (↑S : Set (Fin m)).Pairwise
    (fun i j => (W.observable i).commutesWith (W.observable j))

/-- Inclusion-maximal commuting context. -/
def IsMaximalCommutingContext (S : Finset (Fin m)) : Prop :=
  W.IsCommutingContext S ∧
    ∀ T : Finset (Fin m), W.IsCommutingContext T → S ⊆ T → T = S

/-- Apply a Boolean sign to a fixed Hermitian Pauli representative. -/
def signedObservable (f : Fin m → Bool) (i : Fin m) : Pauli n :=
  if f i then -(W.observable i) else W.observable i

/-- The signed Pauli subset selected by a context. -/
def signedContextSet (S : Finset (Fin m)) (f : Fin m → Bool) :
    Set (Pauli n) :=
  {Q | ∃ i ∈ S, Q = W.signedObservable f i}

/-- A sign assignment is admissible when no product of its signed commuting
observables generates `-I`.  This is the phase-aware content omitted by the
bare anticommutation graph. -/
def IsAdmissibleSign (S : Finset (Fin m)) (f : Fin m → Bool) : Prop :=
  -(1 : Pauli n) ∉ Subgroup.closure (W.signedContextSet S f)

/-- A normalized candidate label for the compressed V-representation. -/
structure MaximalSignedContext where
  support : Finset (Fin m)
  sign : Fin m → Bool
  /-- A sign table is mathematically defined only on `support`; setting every
  unused entry to `false` gives a unique total-function encoding. -/
  offSupportFalse : ∀ i, i ∉ support → sign i = false
  maximal : W.IsMaximalCommutingContext support
  admissible : W.IsAdmissibleSign support sign

namespace MaximalSignedContext

/-- The candidate projected point: saturated `±1` on the context and zero on
all other measured coordinates.  It is called a candidate until physicality
and extremality are proved. -/
def vector (c : W.MaximalSignedContext) : Fin m → ℝ :=
  fun i => if i ∈ c.support then if c.sign i then -1 else 1 else 0

@[simp] theorem vector_of_mem (c : W.MaximalSignedContext) {i : Fin m}
    (hi : i ∈ c.support) :
    vector W c i = if c.sign i then -1 else 1 := by
  simp [vector, hi]

@[simp] theorem vector_of_not_mem (c : W.MaximalSignedContext) {i : Fin m}
    (hi : i ∉ c.support) : vector W c i = 0 := by
  simp [vector, hi]

theorem abs_vector_le_one (c : W.MaximalSignedContext) (i : Fin m) :
    |vector W c i| ≤ 1 := by
  by_cases hi : i ∈ c.support
  · cases hs : c.sign i <;> simp [vector, hi, hs]
  · simp [vector, hi]

end MaximalSignedContext

noncomputable instance maximalSignedContextFinite :
    Finite W.MaximalSignedContext := by
  let encode : W.MaximalSignedContext → Finset (Fin m) × (Fin m → Bool) :=
    fun c => (c.support, c.sign)
  apply Finite.of_injective encode
  intro a b h
  cases a with
  | mk as af aoff am aa =>
    cases b with
    | mk bs bf boff bm ba =>
      change (as, af) = (bs, bf) at h
      cases h
      rfl

noncomputable instance maximalSignedContextFintype :
    Fintype W.MaximalSignedContext := Fintype.ofFinite _

end MeasurementWindow

end

end AgtXIv.Varela
