import AgtXIvRootMath.QubitStabilizerAffineComplete
import AgtXIvRootMath.StandardZProjectorBridge
import AgtXIvRootMath.PauliFrameSupportCompletion

/-!
# Explicit product stabilizer frames

This module recursively adjoins one signed one-qubit Pauli generator to a
complete frame.  The construction is phase-aware and proves independence and
exclusion of `-I`; it does not assume that a tensor product projector is a
stabilizer atom.
-/

namespace AgtXIv.Stabilizer

noncomputable section

open scoped BigOperators

/-- Put a one-qubit signed Pauli on the most-significant tensor factor. -/
def prependPauli {n : ℕ} (P : Pauli 1) (Q : Pauli n) : Pauli (n + 1) :=
  Pauli.cons P.z.msb P.x.msb (Q.addPhase P.m)

@[simp]
theorem prependPauli_z {n : ℕ} (P : Pauli 1) (Q : Pauli n) :
    (prependPauli P Q).z = BitVec.cons P.z.msb Q.z := by
  simp [prependPauli]

@[simp]
theorem prependPauli_x {n : ℕ} (P : Pauli 1) (Q : Pauli n) :
    (prependPauli P Q).x = BitVec.cons P.x.msb Q.x := by
  simp [prependPauli]

@[simp]
theorem prependPauli_m {n : ℕ} (P : Pauli 1) (Q : Pauli n) :
    (prependPauli P Q).m = Q.m + P.m := by
  simp [prependPauli, add_comm]

@[simp]
theorem prependPauli_one {n : ℕ} :
    prependPauli (1 : Pauli 1) (1 : Pauli n) = 1 := by
  apply Pauli.ext <;> simp [prependPauli]

theorem bitVec_one_dotZ₂ (x y : BitVec 1) :
    x.dotZ₂ y = (x.msb && y.msb) := by
  rw [← BitVec.cons_msb_lsbs x, ← BitVec.cons_msb_lsbs y,
    BitVec.cons_dotZ₂_cons]
  have hx : x.lsbs = (0 : BitVec 0) := Subsingleton.elim _ _
  have hy : y.lsbs = (0 : BitVec 0) := Subsingleton.elim _ _
  simp [hx, hy]

theorem bool_xor_toNat_two_zmod4 (a b : Bool) :
    (((a ^^ b).toNat : ZMod 4) * 2) =
      (a.toNat : ZMod 4) * 2 + (b.toNat : ZMod 4) * 2 := by
  cases a <;> cases b <;> decide

theorem bitVec_cons_eq_cons_head {n : ℕ} {a b : Bool} {x y : BitVec n}
    (h : BitVec.cons a x = BitVec.cons b y) : a = b := by
  have hm := congrArg BitVec.msb h
  simpa using hm

theorem bitVec_cons_eq_cons_tail {n : ℕ} {a b : Bool} {x y : BitVec n}
    (h : BitVec.cons a x = BitVec.cons b y) : x = y := by
  have ht := congrArg BitVec.lsbs h
  simpa using ht

theorem bitVec_one_eq_of_msb_eq {x y : BitVec 1} (h : x.msb = y.msb) :
    x = y := by
  calc
    x = BitVec.cons x.msb x.lsbs := (BitVec.cons_msb_lsbs x).symm
    _ = BitVec.cons y.msb y.lsbs :=
      congrArg₂ BitVec.cons h (Subsingleton.elim _ _)
    _ = y := BitVec.cons_msb_lsbs y

theorem bitVec_cons_eq_zero_head {n : ℕ} {a : Bool} {x : BitVec n}
    (h : BitVec.cons a x = 0) : a = false := by
  have hm := congrArg BitVec.msb h
  simpa using hm

theorem bitVec_cons_eq_zero_tail {n : ℕ} {a : Bool} {x : BitVec n}
    (h : BitVec.cons a x = 0) : x = 0 := by
  have ht := congrArg BitVec.lsbs h
  simpa using ht

/-- `prependPauli` respects multiplication on its two disjoint tensor
factors. -/
theorem prependPauli_mul {n : ℕ} (P R : Pauli 1) (Q S : Pauli n) :
    prependPauli (P * R) (Q * S) =
      prependPauli P Q * prependPauli R S := by
  apply Pauli.ext
  · simp only [prependPauli_m, Pauli.mul_m, Pauli.phaseFlipsWith]
    rw [bitVec_one_dotZ₂]
    simp only [prependPauli_x, prependPauli_z, BitVec.cons_dotZ₂_cons]
    rw [bool_xor_toNat_two_zmod4]
    ring
  · simp [prependPauli, Pauli.mul_z]
  · simp [prependPauli, Pauli.mul_x]

/-- Tensoring signed Paulis on disjoint factors is a monoid homomorphism. -/
def prependPauliHom (n : ℕ) : Pauli 1 × Pauli n →* Pauli (n + 1) where
  toFun p := prependPauli p.1 p.2
  map_one' := prependPauli_one
  map_mul' p q := prependPauli_mul p.1 q.1 p.2 q.2

/-- Split a rank-`n+1` binary word into the leading one-bit word and its
remaining `n`-bit word. -/
def binaryWordHeadTailHom (n : ℕ) :
    BinaryWord (n + 1) →* BinaryWord 1 × BinaryWord n where
  toFun a :=
    (Multiplicative.ofAdd (fun _ => a.toAdd (Fin.last n)),
      Multiplicative.ofAdd (Fin.init a.toAdd))
  map_one' := by
    apply Prod.ext
    · apply Multiplicative.toAdd.injective
      funext i
      change (0 : ZMod 2) = 0
      rfl
    · apply Multiplicative.toAdd.injective
      funext i
      change (0 : ZMod 2) = 0
      rfl
  map_mul' a b := by
    apply Prod.ext
    · apply Multiplicative.toAdd.injective
      funext i
      rfl
    · apply Multiplicative.toAdd.injective
      funext i
      rfl

@[simp]
theorem binaryWordHeadTailHom_fst (n : ℕ) (a : BinaryWord (n + 1)) :
    (binaryWordHeadTailHom n a).1 =
      Multiplicative.ofAdd (fun _ => a.toAdd (Fin.last n)) := rfl

@[simp]
theorem binaryWordHeadTailHom_snd (n : ℕ) (a : BinaryWord (n + 1)) :
    (binaryWordHeadTailHom n a).2 =
      Multiplicative.ofAdd (Fin.init a.toAdd) := rfl

/-- The head/tail splitting of binary labels is injective. -/
theorem binaryWordHeadTailHom_injective (n : ℕ) :
    Function.Injective (binaryWordHeadTailHom n) := by
  intro a b h
  apply Multiplicative.toAdd.injective
  have ht := congrArg (fun p => p.2.toAdd) h
  have hh := congrArg (fun p => p.1.toAdd 0) h
  funext i
  refine Fin.lastCases ?_ (fun j => ?_) i
  · simpa using hh
  · exact congrFun ht j

/-- Map a product of monoid homomorphisms coordinatewise. -/
def productMonoidHom {A B C D : Type*}
    [MulOneClass A] [MulOneClass B] [MulOneClass C] [MulOneClass D]
    (f : A →* C) (g : B →* D) : A × B →* C × D where
  toFun p := (f p.1, g p.2)
  map_one' := by simp
  map_mul' p q := by simp

/-- Binary evaluation homomorphism of the recursively adjoined frame. -/
def prependStabilizerEvalHom {n : ℕ} (a : QubitStabilizerAtom)
    (F : IndependentSignedPauliFrame n n) :
    BinaryWord (n + 1) →* Pauli (n + 1) :=
  (prependPauliHom n).comp
    ((productMonoidHom
      (binaryOnePauliHom a.signedPauli a.signedPauli_sq) F.eval).comp
      (binaryWordHeadTailHom n))

@[simp]
theorem prependStabilizerEvalHom_apply {n : ℕ} (a : QubitStabilizerAtom)
    (F : IndependentSignedPauliFrame n n) (u : BinaryWord (n + 1)) :
    prependStabilizerEvalHom a F u =
      prependPauli
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq)
          (binaryWordHeadTailHom n u).1)
        (F.eval (binaryWordHeadTailHom n u).2) := rfl

/-- Adjoin a named one-qubit stabilizer eigenstate to a complete tail frame. -/
def prependStabilizerFrame {n : ℕ} (a : QubitStabilizerAtom)
    (F : IndependentSignedPauliFrame n n) :
    IndependentSignedPauliFrame (n + 1) (n + 1) where
  eval := prependStabilizerEvalHom a F
  independent := by
    intro u v huv
    apply binaryWordHeadTailHom_injective n
    let hu := binaryWordHeadTailHom n u
    let hv := binaryWordHeadTailHom n v
    have hz := congrArg Pauli.z huv
    have hx := congrArg Pauli.x huv
    change
      (prependPauli
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hu.1)
        (F.eval hu.2)).z =
      (prependPauli
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hv.1)
        (F.eval hv.2)).z at hz
    change
      (prependPauli
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hu.1)
        (F.eval hu.2)).x =
      (prependPauli
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hv.1)
        (F.eval hv.2)).x at hx
    have hHeadSupport :
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hu.1).z =
          ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hv.1).z ∧
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hu.1).x =
          ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hv.1).x := by
      constructor
      · exact bitVec_one_eq_of_msb_eq (bitVec_cons_eq_cons_head hz)
      · exact bitVec_one_eq_of_msb_eq (bitVec_cons_eq_cons_head hx)
    have hTail : hu.2 = hv.2 := by
      apply Multiplicative.toAdd.injective
      apply F.supportLinear_injective
      apply Prod.ext <;>
        simp only [IndependentSignedPauliFrame.supportLinear_apply,
          F2Support.pauli]
      · apply F2Bits.ext
        exact bitVec_cons_eq_cons_tail hz
      · apply F2Bits.ext
        exact bitVec_cons_eq_cons_tail hx
    have hHead : hu.1 = hv.1 := by
      apply (qubitStabilizerFrame a).independent
      apply Pauli.ext
      · have hm := congrArg Pauli.m huv
        change
          (F.eval hu.2).m +
              ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hu.1).m =
            (F.eval hv.2).m +
              ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) hv.1).m at hm
        rw [hTail] at hm
        exact add_left_cancel hm
      · exact hHeadSupport.1
      · exact hHeadSupport.2
    exact Prod.ext hHead hTail
  minusOneExcluded := by
    intro u hu
    let p := binaryWordHeadTailHom n u
    have hz := congrArg Pauli.z hu
    have hx := congrArg Pauli.x hu
    change
      (prependPauli
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) p.1)
        (F.eval p.2)).z = (-(1 : Pauli (n + 1))).z at hz
    change
      (prependPauli
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) p.1)
        (F.eval p.2)).x = (-(1 : Pauli (n + 1))).x at hx
    simp only [prependPauli_z, prependPauli_x, Pauli.neg_z, Pauli.neg_x,
      Pauli.one_z, Pauli.one_x] at hz hx
    have hHeadSupport :
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) p.1).z = 0 ∧
        ((binaryOnePauliHom a.signedPauli a.signedPauli_sq) p.1).x = 0 := by
      constructor
      · exact bitVec_one_eq_of_msb_eq (bitVec_cons_eq_zero_head hz)
      · exact bitVec_one_eq_of_msb_eq (bitVec_cons_eq_zero_head hx)
    have hHead : p.1 = 1 := by
      apply (qubitStabilizerFrame a).scalar_support_implies_label_one
      · exact hHeadSupport.1
      · exact hHeadSupport.2
    have hTail : p.2 = 1 := by
      apply F.scalar_support_implies_label_one
      · exact bitVec_cons_eq_zero_tail hz
      · exact bitVec_cons_eq_zero_tail hx
    have hp : p = 1 := Prod.ext hHead hTail
    have huOne : u = 1 := (binaryWordHeadTailHom_injective n) (by simpa [p] using hp)
    subst u
    have hbad : (1 : Pauli (n + 1)) = -(1 : Pauli (n + 1)) := by
      simpa using hu
    have hm := congrArg Pauli.m hbad
    change (0 : ZMod 4) = 2 at hm
    exact (by decide : (0 : ZMod 4) ≠ 2) hm

/-- One-qubit signed Pauli followed by a tail Pauli has the expected concrete
tensor-product matrix. -/
theorem pauli_one_toCMatrix_eq_phase_smul_bits (P : Pauli 1) :
    P.toCMatrix = ((-Complex.I) ^ P.m.val) •
      Pauli.toCMatrix.bitsToMat (P.z.msb, P.x.msb) := by
  rw [Pauli.cons_msb_tail P, Pauli.toCMatrix_cons]
  obtain ⟨m, htail⟩ := Pauli.of_length_zero P.tail
  rw [htail]
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Pauli.toCMatrix, Matrix.reindex_apply, Matrix.kron_apply]

theorem prependPauli_toCMatrix {n : ℕ} (P : Pauli 1) (Q : Pauli n) :
    (prependPauli P Q).toCMatrix =
      StandardFrame.prependTensor P.toCMatrix Q.toCMatrix := by
  unfold prependPauli
  rw [StandardFrame.toCMatrix_cons, Pauli.addPhase_toCMatrix,
    pauli_one_toCMatrix_eq_phase_smul_bits]
  unfold StandardFrame.prependTensor
  rw [Matrix.kron_smul, Matrix.smul_kron]

theorem prependTensor_add_left {n : ℕ} (A B : CMatrix 2 2)
    (C : CMatrix (2 ^ n) (2 ^ n)) :
    StandardFrame.prependTensor (A + B) C =
      StandardFrame.prependTensor A C + StandardFrame.prependTensor B C := by
  unfold StandardFrame.prependTensor
  rw [Matrix.add_kron, map_add]

theorem prependTensor_add_right {n : ℕ} (A : CMatrix 2 2)
    (B C : CMatrix (2 ^ n) (2 ^ n)) :
    StandardFrame.prependTensor A (B + C) =
      StandardFrame.prependTensor A B + StandardFrame.prependTensor A C := by
  unfold StandardFrame.prependTensor
  rw [Matrix.kron_add, map_add]

theorem prependTensor_sum_right {n : ℕ} {ι : Type*}
    (A : CMatrix 2 2) (s : Finset ι)
    (B : ι → CMatrix (2 ^ n) (2 ^ n)) :
    StandardFrame.prependTensor A (∑ i ∈ s, B i) =
      ∑ i ∈ s, StandardFrame.prependTensor A (B i) := by
  classical
  induction s using Finset.induction_on with
  | empty => simp [StandardFrame.prependTensor]
  | insert i s hi ih => simp [hi, prependTensor_add_right, ih]

theorem prependTensor_smul_both {n : ℕ} (c d : ℂ)
    (A : CMatrix 2 2) (B : CMatrix (2 ^ n) (2 ^ n)) :
    StandardFrame.prependTensor (c • A) (d • B) =
      (c * d) • StandardFrame.prependTensor A B := by
  unfold StandardFrame.prependTensor
  rw [Matrix.smul_kron, Matrix.kron_smul, map_smul]
  simp [smul_smul]

theorem binaryWordHeadTailHom_snoc (n : ℕ) (b : StandardF2)
    (u : BinaryWord n) :
    binaryWordHeadTailHom n (binaryWordSnocEquiv n (b, u)) =
      (Multiplicative.ofAdd (fun _ => b), u) := by
  apply Prod.ext
  · apply Multiplicative.toAdd.injective
    funext i
    simp [binaryWordHeadTailHom, binaryWordSnocEquiv]
  · apply Multiplicative.toAdd.injective
    simp [binaryWordHeadTailHom, binaryWordSnocEquiv]

/-- The unnormalized group sum of an adjoined product frame factorizes into
the one-qubit sum and the tail-frame sum. -/
theorem sum_prependStabilizerEvalHom {n : ℕ} (a : QubitStabilizerAtom)
    (F : IndependentSignedPauliFrame n n) :
    (∑ u : BinaryWord (n + 1), (prependStabilizerEvalHom a F u).toCMatrix) =
      StandardFrame.prependTensor
        ((1 : CMatrix 2 2) + a.signedPauli.toCMatrix)
        (∑ v : BinaryWord n, (F.eval v).toCMatrix) := by
  rw [Fintype.sum_equiv (binaryWordSnocEquiv n).symm
    (fun u : BinaryWord (n + 1) =>
      (prependStabilizerEvalHom a F u).toCMatrix)
    (fun p : StandardF2 × BinaryWord n =>
      (prependStabilizerEvalHom a F (binaryWordSnocEquiv n p)).toCMatrix)]
  · rw [Fintype.sum_prod_type, sum_standardF2]
    simp only [prependStabilizerEvalHom_apply, binaryWordHeadTailHom_snoc]
    simp only [binaryOnePauliHom, MonoidHom.coe_mk, OneHom.coe_mk]
    have hzero : (fun _ : Fin 1 => (0 : StandardF2)) = 0 := rfl
    have hone : (fun _ : Fin 1 => (1 : StandardF2)) ≠ 0 := by
      intro h
      have hh := congrFun h 0
      norm_num at hh
    simp [binaryOneEval, hzero, hone, prependPauli_toCMatrix]
    rw [← prependTensor_sum_right, ← prependTensor_sum_right,
      ← prependTensor_add_left]
  · intro u
    simpa using congrArg
      (fun v => (prependStabilizerEvalHom a F v).toCMatrix)
      ((binaryWordSnocEquiv n).apply_symm_apply u).symm

/-- The normalized group-average projector of the adjoined frame is exactly
the tensor product of the corresponding one-qubit stabilizer projector and
the tail stabilizer projector. -/
theorem stabilizerProjectorMatrix_prependStabilizerFrame {n : ℕ}
    (a : QubitStabilizerAtom) (F : IndependentSignedPauliFrame n n) :
    stabilizerProjectorMatrix (prependStabilizerFrame a F) =
      StandardFrame.prependTensor (qubitPauliEigenProjector a)
        (stabilizerProjectorMatrix F) := by
  unfold stabilizerProjectorMatrix
  rw [invOf_eq_inv, invOf_eq_inv]
  rw [AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card,
    AgtXIv.Gottesman.RankPauliFrame.binaryFrameGroup_card]
  change
    (((2 ^ (n + 1) : ℕ) : ℂ))⁻¹ •
        (∑ u : BinaryWord (n + 1),
          (prependStabilizerEvalHom a F u).toCMatrix) = _
  rw [sum_prependStabilizerEvalHom,
    complex_inv_two_pow_succ]
  rw [show qubitPauliEigenProjector a =
      (2 : ℂ)⁻¹ • ((1 : CMatrix 2 2) + a.signedPauli.toCMatrix) from rfl]
  rw [prependTensor_smul_both]

/-- A finite symbolic index for the `6^n` tensor products of one-qubit
stabilizer eigenstates. -/
def ProductStabilizerAtom : ℕ → Type
  | 0 => PUnit
  | n + 1 => QubitStabilizerAtom × ProductStabilizerAtom n

noncomputable instance productStabilizerAtomFintype :
    (n : ℕ) → Fintype (ProductStabilizerAtom n)
  | 0 => inferInstanceAs (Fintype PUnit)
  | n + 1 => by
      letI := productStabilizerAtomFintype n
      exact inferInstanceAs
        (Fintype (QubitStabilizerAtom × ProductStabilizerAtom n))

noncomputable instance productStabilizerAtomDecidableEq :
    (n : ℕ) → DecidableEq (ProductStabilizerAtom n)
  | 0 => inferInstanceAs (DecidableEq PUnit)
  | n + 1 => by
      letI := productStabilizerAtomDecidableEq n
      exact inferInstanceAs
        (DecidableEq (QubitStabilizerAtom × ProductStabilizerAtom n))

/-- Every product-state label is realized by an actual complete signed Pauli
frame. -/
def productStabilizerFrame :
    (n : ℕ) → ProductStabilizerAtom n → IndependentSignedPauliFrame n n
  | 0, _ => standardIndependentZFrame 0
  | n + 1, a => prependStabilizerFrame a.1 (productStabilizerFrame n a.2)

@[simp]
theorem productStabilizerFrame_zero (a : ProductStabilizerAtom 0) :
    productStabilizerFrame 0 a = standardIndependentZFrame 0 := rfl

@[simp]
theorem productStabilizerFrame_succ (n : ℕ)
    (a : ProductStabilizerAtom (n + 1)) :
    productStabilizerFrame (n + 1) a =
      prependStabilizerFrame a.1 (productStabilizerFrame n a.2) := rfl

/-- Hermitian projector atom supplied by the explicit product frame. -/
noncomputable def productStabilizerHermitianAtom (n : ℕ) :
    ProductStabilizerAtom n → HermitianMatrixReal (2 ^ n) :=
  pureStabilizerHermitianAtom (productStabilizerFrame n)

@[simp]
theorem coe_productStabilizerHermitianAtom (n : ℕ)
    (a : ProductStabilizerAtom n) :
    (productStabilizerHermitianAtom n a : CMatrix (2 ^ n) (2 ^ n)) =
      stabilizerProjectorMatrix (productStabilizerFrame n a) := rfl

/-- Product-state atoms obey the expected projector tensor recursion. -/
theorem productStabilizerHermitianAtom_succ (n : ℕ)
    (a : ProductStabilizerAtom (n + 1)) :
    (productStabilizerHermitianAtom (n + 1) a :
        CMatrix (2 ^ (n + 1)) (2 ^ (n + 1))) =
      StandardFrame.prependTensor
        (qubitStabilizerHermitianAtom a.1 : CMatrix 2 2)
        (productStabilizerHermitianAtom n a.2 :
          CMatrix (2 ^ n) (2 ^ n)) := by
  rw [coe_productStabilizerHermitianAtom,
    productStabilizerFrame_succ,
    stabilizerProjectorMatrix_prependStabilizerFrame,
    coe_qubitStabilizerHermitianAtom,
    coe_productStabilizerHermitianAtom]

end

end AgtXIv.Stabilizer
