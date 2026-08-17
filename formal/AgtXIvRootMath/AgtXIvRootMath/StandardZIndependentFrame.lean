import AgtXIvRootMath.GottesmanConcretePauliFrame

/-!
# The standard complete signed-Z frame

This file constructs the rank-`n` standard stabilizer frame from the binary
labels themselves.  Independence and exclusion of `-I` are proved from the
phase-aware Pauli representation; neither is stored as an extra assumption.

The construction is the common source for the Gottesman group-average
presentation and the computational-basis presentation used in the
Gottesman-to-Veitch bridge.
-/

namespace AgtXIv.Stabilizer

abbrev StandardF2 := ZMod 2

/-- Interpret a field element of `ZMod 2` as its Boolean bit. -/
def boolOfStandardF2 (a : StandardF2) : Bool := decide (a = 1)

/-- Pack an `F₂` coordinate function into LeanQuantum's little-endian bit
vector convention. -/
def bitVecOfF2Fun {n : ℕ} (a : Fin n → StandardF2) : BitVec n :=
  (BitVec.ofBoolListLE (List.ofFn (fun i => boolOfStandardF2 (a i)))).setWidth n

@[simp] theorem getLsbD_bitVecOfF2Fun {n : ℕ}
    (a : Fin n → StandardF2) (i : ℕ) :
    (bitVecOfF2Fun a).getLsbD i =
      if h : i < n then boolOfStandardF2 (a ⟨i, h⟩) else false := by
  by_cases h : i < n
  · simp only [bitVecOfF2Fun, BitVec.getLsbD_setWidth, h, decide_true,
      Bool.true_and, BitVec.getLsbD_ofBoolListLE]
    rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem (by simp [h])]
    simp [List.getElem_ofFn]
  · simp [bitVecOfF2Fun, h]

@[simp] theorem getLsb_bitVecOfF2Fun {n : ℕ}
    (a : Fin n → StandardF2) (i : Fin n) :
    (bitVecOfF2Fun a).getLsb i = boolOfStandardF2 (a i) := by
  simpa [BitVec.getLsb, BitVec.getLsbD, i.isLt] using
    getLsbD_bitVecOfF2Fun a i.val

theorem boolOfStandardF2_add (a b : StandardF2) :
    boolOfStandardF2 (a + b) =
      (boolOfStandardF2 a ^^ boolOfStandardF2 b) := by
  fin_cases a <;> fin_cases b <;> decide

theorem bitVecOfF2Fun_add {n : ℕ} (a b : Fin n → StandardF2) :
    bitVecOfF2Fun (a + b) = bitVecOfF2Fun a ^^^ bitVecOfF2Fun b := by
  apply BitVec.eq_of_getLsbD_eq
  intro i
  simp only [getLsbD_bitVecOfF2Fun, BitVec.getLsbD_xor]
  split <;> simp_all [Pi.add_apply, boolOfStandardF2_add]

@[simp] theorem bitVecOfF2Fun_zero {n : ℕ} :
    bitVecOfF2Fun (0 : Fin n → StandardF2) = 0 := by
  apply BitVec.eq_of_getLsbD_eq
  intro i
  simp [getLsbD_bitVecOfF2Fun, boolOfStandardF2]

theorem bitVecOfF2Fun_injective {n : ℕ} :
    Function.Injective (bitVecOfF2Fun (n := n)) := by
  intro a b h
  funext i
  have hi := congrArg (fun z : BitVec n => z.getLsb i) h
  simp only [getLsb_bitVecOfF2Fun] at hi
  have hInjective : Function.Injective boolOfStandardF2 := by decide
  exact hInjective hi

/-- Evaluate a binary label as the corresponding tensor product of unsigned
`Z` Paulis. -/
def standardZEval {n : ℕ} (a : BinaryWord n) : Pauli n where
  m := 0
  z := bitVecOfF2Fun a.toAdd
  x := 0

@[simp] theorem standardZEval_one {n : ℕ} :
    standardZEval (1 : BinaryWord n) = 1 := by
  apply Pauli.ext <;> simp [standardZEval]

theorem standardZEval_mul {n : ℕ} (a b : BinaryWord n) :
    standardZEval (a * b) = standardZEval a * standardZEval b := by
  apply Pauli.ext
  · simp [standardZEval, Pauli.mul_m, Pauli.phaseFlipsWith]
  · simp [standardZEval, Pauli.mul_z, bitVecOfF2Fun_add]
  · simp [standardZEval, Pauli.mul_x]

/-- The standard binary-word evaluation as an exact group homomorphism. -/
def standardZEvalHom (n : ℕ) : BinaryWord n →* Pauli n where
  toFun := standardZEval
  map_one' := standardZEval_one
  map_mul' := standardZEval_mul

theorem standardZEvalHom_injective {n : ℕ} :
    Function.Injective (standardZEvalHom n) := by
  intro a b h
  have hz := congrArg Pauli.z h
  change bitVecOfF2Fun a.toAdd = bitVecOfF2Fun b.toAdd at hz
  have hab := bitVecOfF2Fun_injective hz
  exact Multiplicative.toAdd.injective hab

theorem standardZEvalHom_ne_minus_one {n : ℕ} (a : BinaryWord n) :
    standardZEvalHom n a ≠ -(1 : Pauli n) := by
  intro h
  have hm := congrArg Pauli.m h
  change (0 : ZMod 4) = 2 at hm
  exact (by decide : (0 : ZMod 4) ≠ 2) hm

/-- The rank-`n` standard signed-`Z` frame.  Its independence and phase
cleanliness are conclusions of the explicit binary evaluation. -/
def standardIndependentZFrame (n : ℕ) :
    IndependentSignedPauliFrame n n where
  eval := standardZEvalHom n
  independent := standardZEvalHom_injective
  minusOneExcluded := standardZEvalHom_ne_minus_one

@[simp] theorem standardIndependentZFrame_eval (n : ℕ) (a : BinaryWord n) :
    (standardIndependentZFrame n).eval a = standardZEval a := rfl

end AgtXIv.Stabilizer
