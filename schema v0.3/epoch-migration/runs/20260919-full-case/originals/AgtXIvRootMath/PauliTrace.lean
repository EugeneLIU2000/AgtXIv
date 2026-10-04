import Quantumlib.Data.Gate.Pauli.Lemmas
import Mathlib.RepresentationTheory.Character

/-!
# Exact trace semantics for the locked LeanQuantum Pauli representation

The phase-aware `Pauli n` type is imported from the pinned local LeanQuantum
snapshot.  This file proves the matrix trace formula missing from that library.
It is important not to say merely that every nonidentity Pauli is traceless:
the nonidentity scalar phases `-I` and `±iI` are counterexamples.  Tracelessness
follows from nonzero binary support.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators

variable {n : ℕ}

/-- Matrix trace is invariant under simultaneous reindexing of rows and
columns by an equivalence. -/
theorem trace_reindex_equiv {a b : ℕ} (e : Fin a ≃ Fin b) (A : CMatrix a a) :
    Matrix.trace (Matrix.reindex e e A) = Matrix.trace A := by
  rw [Matrix.trace, Matrix.trace]
  exact Fintype.sum_equiv e.symm _ _ (fun x => by simp [Matrix.reindex_apply])

/-- The four phase-free local Pauli factors have trace two only for identity. -/
theorem trace_bitsToMat (a b : Bool) :
    Matrix.trace (Pauli.toCMatrix.bitsToMat (a, b)) =
      if a = false ∧ b = false then 2 else 0 := by
  cases a <;> cases b <;>
    simp [Pauli.toCMatrix.bitsToMat, σx, σy, σz, Matrix.trace]

@[simp] theorem bitVec_cons_false_eq_zero_iff (x : BitVec n) :
    BitVec.cons false x = 0 ↔ x = 0 := by
  constructor
  · intro h
    have := congrArg BitVec.lsbs h
    simpa using this
  · rintro rfl
    ext i
    simp

@[simp] theorem bitVec_cons_true_ne_zero (x : BitVec n) :
    BitVec.cons true x ≠ 0 := by
  intro h
  have := congrArg BitVec.msb h
  simp at this

/-- Exact trace of the full phase-aware tensor-Pauli matrix. -/
theorem pauli_trace_formula (P : Pauli n) :
    Matrix.trace P.toCMatrix =
      if P.z = 0 ∧ P.x = 0 then
        ((2 ^ n : ℕ) : ℂ) * ((-Complex.I) ^ P.m.val)
      else 0 := by
  induction n with
  | zero =>
      obtain ⟨m, rfl⟩ := Pauli.of_length_zero P
      simp [Pauli.toCMatrix, Matrix.trace, mul_comm]
  | succ n ih =>
      rw [Pauli.cons_msb_tail P, Pauli.toCMatrix_cons]
      rw [trace_reindex_equiv, Matrix.trace_kron, trace_bitsToMat, ih]
      cases hz : P.z.msb <;> cases hx : P.x.msb
      · simp only [and_self, ite_true, Pauli.cons_z, Pauli.cons_x, Pauli.cons_m]
        simp only [bitVec_cons_false_eq_zero_iff]
        split_ifs <;> simp_all [pow_succ, mul_assoc, mul_comm]
      · simp [Pauli.cons_z, Pauli.cons_x]
      · simp [Pauli.cons_z, Pauli.cons_x]
      · simp [Pauli.cons_z, Pauli.cons_x]

/-- Every Pauli with nonzero binary support is traceless, independently of its
global phase. -/
theorem trace_eval_eq_zero_of_support_ne_zero
    (P : Pauli n) (hSupport : P.z ≠ 0 ∨ P.x ≠ 0) :
    Matrix.trace P.toCMatrix = 0 := by
  rw [pauli_trace_formula]
  rw [if_neg]
  exact fun h => hSupport.elim (fun hz => hz h.1) (fun hx => hx h.2)

/-- The concrete matrix action of the LeanQuantum Pauli group. -/
noncomputable def pauliMatrixRepresentation (n : ℕ) :
    Representation ℂ (Pauli n) (Fin (2 ^ n) → ℂ) where
  toFun P := Matrix.toLin' P.toCMatrix
  map_one' := by simp [Module.End.one_eq_id]
  map_mul' P Q := by
    rw [Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix, Matrix.toLin'_mul]
    rfl

end AgtXIv.Stabilizer
