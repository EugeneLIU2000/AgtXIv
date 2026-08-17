import AgtXIvRootMath.PauliDualFrame
import AgtXIvRootMath.PauliFaithful

/-!
# Exact normal form relative to a complete Pauli read/flip frame

The original frame and its constructively derived dual frame give a full
symplectic basis of binary support.  Consequently every signed Pauli has a
unique support-coordinate pair.  Its remaining information is one central
`ZMod 4` phase.  This file packages that decomposition and defines the
phase-aware transport candidate between any two complete frames.

The transport candidate already maps every original read word and every dual
flip word exactly, including their signs.  Its multiplicativity will be
certified downstream from the syndrome-basis unitary conjugation theorem,
avoiding a second large cocycle calculation.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators
noncomputable section

namespace IndependentSignedPauliFrame

variable {n : ℕ}

/-- The completed support-coordinate equivalence with all constructed
partners specialized. -/
def completedSupportEquiv (F : IndependentSignedPauliFrame n n) :
    SupportCoordinates n ≃ₗ[F2] F2Support n :=
  F.supportCompletionEquiv F.dualSupport F.dualSupport_pair F.dualSupport_isotropic

@[simp] theorem completedSupportEquiv_apply
    (F : IndependentSignedPauliFrame n n) (c : SupportCoordinates n) :
    F.completedSupportEquiv c = F.supportCompletionLinear F.dualSupport c := rfl

/-- Ordered exact word: original read block first, constructed flip block
second.  This order matches LeanQuantum's `Z`-then-`X` Pauli convention. -/
def frameWord (F : IndependentSignedPauliFrame n n)
    (c : SupportCoordinates n) : Pauli n :=
  F.eval (Multiplicative.ofAdd c.1) *
    F.dualFrame.eval (Multiplicative.ofAdd c.2)

theorem support_frameWord (F : IndependentSignedPauliFrame n n)
    (c : SupportCoordinates n) :
    F2Support.pauli (F.frameWord c) = F.completedSupportEquiv c := by
  rw [frameWord, F2Support.pauli_mul, F.support_eval,
    F.dualFrame_eval, F.support_dualWord]
  rfl

/-- Unique binary read/flip coordinates of a signed Pauli. -/
def frameCoordinates (F : IndependentSignedPauliFrame n n) (P : Pauli n) :
    SupportCoordinates n :=
  F.completedSupportEquiv.symm (F2Support.pauli P)

@[simp] theorem frameCoordinates_frameWord
    (F : IndependentSignedPauliFrame n n) (c : SupportCoordinates n) :
    F.frameCoordinates (F.frameWord c) = c := by
  rw [frameCoordinates, F.support_frameWord]
  exact F.completedSupportEquiv.symm_apply_apply c

theorem support_frameWord_frameCoordinates
    (F : IndependentSignedPauliFrame n n) (P : Pauli n) :
    F2Support.pauli (F.frameWord (F.frameCoordinates P)) = F2Support.pauli P := by
  rw [F.support_frameWord, frameCoordinates]
  exact F.completedSupportEquiv.apply_symm_apply _

/-- A central Pauli scalar `(-i)^m I`. -/
def centralPauli (n : ℕ) (m : ZMod 4) : Pauli n :=
  (1 : Pauli n).addPhase m

@[simp] theorem centralPauli_m (n : ℕ) (m : ZMod 4) :
    (centralPauli n m).m = m := by simp [centralPauli, Pauli.addPhase]

@[simp] theorem centralPauli_z (n : ℕ) (m : ZMod 4) :
    (centralPauli n m).z = 0 := by simp [centralPauli]

@[simp] theorem centralPauli_x (n : ℕ) (m : ZMod 4) :
    (centralPauli n m).x = 0 := by simp [centralPauli]

/-- Residual exact central phase after extracting the ordered read/flip word. -/
def framePhase (F : IndependentSignedPauliFrame n n) (P : Pauli n) : ZMod 4 :=
  P.m - (F.frameWord (F.frameCoordinates P)).m

/-- Exact phase-aware normal-form reconstruction. -/
theorem frameDecompose (F : IndependentSignedPauliFrame n n) (P : Pauli n) :
    centralPauli n (F.framePhase P) * F.frameWord (F.frameCoordinates P) = P := by
  apply Pauli.ext
  · simp [Pauli.mul_m, Pauli.phaseFlipsWith, framePhase]
  · have hs := F.support_frameWord_frameCoordinates P
    simpa [Pauli.mul_z, centralPauli, F2Support.pauli] using
      congrArg (fun u : F2Support n => u.1.bits) hs
  · have hs := F.support_frameWord_frameCoordinates P
    simpa [Pauli.mul_x, centralPauli, F2Support.pauli] using
      congrArg (fun u : F2Support n => u.2.bits) hs

/-- Phase-aware Pauli transport candidate from frame `A` coordinates to frame
`F` coordinates. -/
def transport (A F : IndependentSignedPauliFrame n n) (P : Pauli n) : Pauli n :=
  centralPauli n (A.framePhase P) * F.frameWord (A.frameCoordinates P)

/-- Transport is exact on every ordered frame word. -/
theorem transport_frameWord (A F : IndependentSignedPauliFrame n n)
    (c : SupportCoordinates n) :
    transport A F (A.frameWord c) = F.frameWord c := by
  unfold transport framePhase
  rw [A.frameCoordinates_frameWord]
  apply Pauli.ext
  · simp [centralPauli]
  · simp [Pauli.mul_z]
  · simp [Pauli.mul_x]

/-- In particular, transport maps every original read word exactly. -/
theorem transport_eval (A F : IndependentSignedPauliFrame n n)
    (a : BinaryWord n) :
    transport A F (A.eval a) = F.eval a := by
  have hA : A.frameWord (a.toAdd, 0) = A.eval a := by
    simp [frameWord, dualFrame_eval,
      CommutingInvolutivePauliGenerators.wordProduct_one]
  have hF : F.frameWord (a.toAdd, 0) = F.eval a := by
    simp [frameWord, dualFrame_eval,
      CommutingInvolutivePauliGenerators.wordProduct_one]
  rw [← hA, A.transport_frameWord, hF]

/-- Transport also maps every constructed flip word exactly. -/
theorem transport_dual_eval (A F : IndependentSignedPauliFrame n n)
    (a : BinaryWord n) :
    transport A F (A.dualFrame.eval a) = F.dualFrame.eval a := by
  have hA : A.frameWord (0, a.toAdd) = A.dualFrame.eval a := by
    simp [frameWord]
  have hF : F.frameWord (0, a.toAdd) = F.dualFrame.eval a := by
    simp [frameWord]
  rw [← hA, A.transport_frameWord, hF]

end IndependentSignedPauliFrame

end
end AgtXIv.Stabilizer
