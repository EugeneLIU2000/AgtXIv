import Quantumlib.Data.Gate.Pauli.Lemmas
import Mathlib.LinearAlgebra.BilinearForm.Basic

/-!
# Binary support and the Pauli commutation form

This file is a phase-explicit bridge from LeanQuantum's signed Pauli group to a
vector space over `ZMod 2`.  The map `F2Support.pauli` deliberately forgets the
`ZMod 4` phase and retains only the `Z` and `X` support bits.  It is therefore
appropriate for commutation and symplectic linear algebra, but it must not be
used to identify signed stabilizer generators or their `+1` eigenspaces.

The main closed results are:

* binary support turns Pauli multiplication into vector addition;
* the support pairing is an alternating bilinear form over `ZMod 2`;
* two signed Paulis commute exactly when their support pairing vanishes.

No Clifford-orbit or stabilizer-state equivalence is assumed here.
-/

namespace AgtXIv.Stabilizer

abbrev F2 := ZMod 2

/-- A bit vector regarded as a vector space over the field with two elements.
Addition is bitwise XOR. -/
@[ext]
structure F2Bits (n : Nat) where
  bits : BitVec n
deriving DecidableEq, Fintype

namespace F2Bits

variable {n : Nat}

instance : Zero (F2Bits n) := ⟨⟨0⟩⟩
instance : Add (F2Bits n) := ⟨fun a b => ⟨a.bits ^^^ b.bits⟩⟩
instance : Neg (F2Bits n) := ⟨fun a => a⟩

@[simp] theorem bits_zero : (0 : F2Bits n).bits = 0 := rfl
@[simp] theorem bits_add (a b : F2Bits n) : (a + b).bits = a.bits ^^^ b.bits := rfl
@[simp] theorem bits_neg (a : F2Bits n) : (-a).bits = a.bits := rfl

instance : AddCommGroup (F2Bits n) :=
  { AddGroup.ofLeftAxioms
      (fun a b c => by
        apply F2Bits.ext
        exact BitVec.xor_assoc _ _ _)
      (fun a => by
        apply F2Bits.ext
        exact BitVec.zero_xor)
      (fun a => by
        apply F2Bits.ext
        exact BitVec.xor_self) with
    add_comm := fun a b => by
      apply F2Bits.ext
      exact BitVec.xor_comm _ _ }

/-- Scalar multiplication by `ZMod 2`: zero erases a bit vector and one keeps it. -/
def f2smul (c : F2) (a : F2Bits n) : F2Bits n :=
  if c = 0 then 0 else a

instance : SMul F2 (F2Bits n) := ⟨f2smul⟩

@[simp] theorem zero_smul' (a : F2Bits n) : (0 : F2) • a = 0 := by
  simp [HSMul.hSMul, SMul.smul, f2smul]

@[simp] theorem one_smul' (a : F2Bits n) : (1 : F2) • a = a := by
  simp [HSMul.hSMul, SMul.smul, f2smul]

theorem f2_eq_zero_or_one (c : F2) : c = 0 ∨ c = 1 := by
  fin_cases c
  · exact Or.inl rfl
  · exact Or.inr rfl

instance : Module F2 (F2Bits n) := Module.ofMinimalAxioms
  (fun c a b => by
    rcases f2_eq_zero_or_one c with rfl | rfl <;> simp)
  (fun c d a => by
    rcases f2_eq_zero_or_one c with rfl | rfl <;>
      rcases f2_eq_zero_or_one d with rfl | rfl
    all_goals try simp
    case inr.inr =>
      rw [show (1 : F2) + 1 = 0 by decide, zero_smul']
      apply F2Bits.ext
      exact BitVec.xor_self.symm)
  (fun c d a => by
    rcases f2_eq_zero_or_one c with rfl | rfl <;>
      rcases f2_eq_zero_or_one d with rfl | rfl <;> simp)
  one_smul'

/-- The canonical embedding of a Boolean bit into `ZMod 2`. -/
def ofBool (b : Bool) : F2 := b.toNat

@[simp] theorem ofBool_false : ofBool false = 0 := rfl
@[simp] theorem ofBool_true : ofBool true = 1 := rfl

theorem ofBool_xor (a b : Bool) : ofBool (a ^^ b) = ofBool a + ofBool b := by
  cases a <;> cases b <;> decide

/-- The parity-valued dot product already used by LeanQuantum, reinterpreted in `ZMod 2`. -/
def dot (a b : F2Bits n) : F2 := ofBool (a.bits.dotZ₂ b.bits)

@[simp] theorem dot_zero_left (a : F2Bits n) : dot 0 a = 0 := by
  simp [dot]

@[simp] theorem dot_zero_right (a : F2Bits n) : dot a 0 = 0 := by
  simp [dot]

theorem dot_add_left (a b c : F2Bits n) : dot (a + b) c = dot a c + dot b c := by
  simp only [dot, bits_add, BitVec.dotZ₂_xor_distrib_right, ofBool_xor]

theorem dot_add_right (a b c : F2Bits n) : dot a (b + c) = dot a b + dot a c := by
  simp only [dot, bits_add, BitVec.dotZ₂_xor_distrib_left, ofBool_xor]

theorem dot_smul_left (r : F2) (a b : F2Bits n) : dot (r • a) b = r • dot a b := by
  rcases f2_eq_zero_or_one r with rfl | rfl <;> simp

theorem dot_smul_right (r : F2) (a b : F2Bits n) : dot a (r • b) = r • dot a b := by
  rcases f2_eq_zero_or_one r with rfl | rfl <;> simp

theorem dot_comm (a b : F2Bits n) : dot a b = dot b a := by
  simp [dot, BitVec.dotZ₂_comm]

noncomputable def dotForm : LinearMap.BilinForm F2 (F2Bits n) :=
  LinearMap.mk₂ F2 dot dot_add_left dot_smul_left dot_add_right dot_smul_right

@[simp] theorem dotForm_apply (a b : F2Bits n) : dotForm a b = dot a b := rfl

end F2Bits

/-- Phase-free `Z/X` support of an `n`-qubit Pauli. -/
abbrev F2Support (n : Nat) := F2Bits n × F2Bits n

namespace F2Support

variable {n : Nat}

/-- Forget the `ZMod 4` phase of a signed Pauli and retain its `Z/X` support. -/
def pauli (P : Pauli n) : F2Support n := ⟨⟨P.z⟩, ⟨P.x⟩⟩

@[simp] theorem pauli_one : pauli (1 : Pauli n) = 0 := by
  ext <;> simp [pauli]

/-- Changing only the Pauli phase does not change binary support.  This lemma
also marks the precise information lost by `pauli`. -/
@[simp] theorem pauli_addPhase (P : Pauli n) (m : ZMod 4) :
    pauli (P.addPhase m) = pauli P := by
  ext <;> simp [pauli]

/-- Pauli multiplication becomes addition of phase-free supports. -/
theorem pauli_mul (P Q : Pauli n) : pauli (P * Q) = pauli P + pauli Q := by
  ext <;> simp [pauli, Pauli.mul_z, Pauli.mul_x]

/-- The standard binary Pauli pairing `x·z' + z·x'`. -/
def symplecticValue (u v : F2Support n) : F2 :=
  F2Bits.dot u.2 v.1 + F2Bits.dot u.1 v.2

theorem symplectic_add_left (u v w : F2Support n) :
    symplecticValue (u + v) w = symplecticValue u w + symplecticValue v w := by
  simp only [symplecticValue, Prod.fst_add, Prod.snd_add, F2Bits.dot_add_left]
  abel

theorem symplectic_add_right (u v w : F2Support n) :
    symplecticValue u (v + w) = symplecticValue u v + symplecticValue u w := by
  simp only [symplecticValue, Prod.fst_add, Prod.snd_add, F2Bits.dot_add_right]
  abel

theorem symplectic_smul_left (r : F2) (u v : F2Support n) :
    symplecticValue (r • u) v = r • symplecticValue u v := by
  change F2Bits.dot (r • u.2) v.1 + F2Bits.dot (r • u.1) v.2 =
    r • (F2Bits.dot u.2 v.1 + F2Bits.dot u.1 v.2)
  rw [F2Bits.dot_smul_left, F2Bits.dot_smul_left, smul_add]

theorem symplectic_smul_right (r : F2) (u v : F2Support n) :
    symplecticValue u (r • v) = r • symplecticValue u v := by
  change F2Bits.dot u.2 (r • v.1) + F2Bits.dot u.1 (r • v.2) =
    r • (F2Bits.dot u.2 v.1 + F2Bits.dot u.1 v.2)
  rw [F2Bits.dot_smul_right, F2Bits.dot_smul_right, smul_add]

/-- The alternating bilinear form controlling Pauli commutation. -/
noncomputable def symplecticForm : LinearMap.BilinForm F2 (F2Support n) :=
  LinearMap.mk₂ F2 symplecticValue symplectic_add_left symplectic_smul_left
    symplectic_add_right symplectic_smul_right

@[simp] theorem symplecticForm_apply (u v : F2Support n) :
    symplecticForm u v = symplecticValue u v := rfl

theorem symplectic_alternating (u : F2Support n) : symplecticForm u u = 0 := by
  rw [symplecticForm_apply, symplecticValue, F2Bits.dot_comm u.2 u.1]
  generalize F2Bits.dot u.1 u.2 = a
  fin_cases a <;> rfl

theorem symplectic_symm (u v : F2Support n) :
    symplecticForm u v = symplecticForm v u := by
  simp only [symplecticForm_apply, symplecticValue]
  rw [F2Bits.dot_comm u.2 v.1, F2Bits.dot_comm u.1 v.2]
  exact add_comm _ _

theorem bool_beq_iff_f2_sum_zero (a b : Bool) :
    (a == b) = true ↔ F2Bits.ofBool a + F2Bits.ofBool b = 0 := by
  cases a <;> cases b <;> decide

/-- Exact bridge from LeanQuantum's Boolean commutation test to the binary bilinear form. -/
theorem pauli_commutes_iff_symplectic_eq_zero (P Q : Pauli n) :
    P.commutesWith Q = true ↔ symplecticForm (pauli P) (pauli Q) = 0 := by
  simpa [Pauli.commutesWith, Pauli.phaseFlipsWith, symplecticValue, pauli, F2Bits.dot,
    BitVec.dotZ₂_comm P.z Q.x] using
    bool_beq_iff_f2_sum_zero (P.x.dotZ₂ Q.z) (Q.x.dotZ₂ P.z)

end F2Support

end AgtXIv.Stabilizer
