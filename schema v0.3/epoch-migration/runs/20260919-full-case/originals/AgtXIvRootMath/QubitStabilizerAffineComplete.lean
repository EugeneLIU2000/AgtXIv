import AgtXIvRootMath.HermitianAffineFeasibility
import AgtXIvRootMath.PauliF2Support

/-!
# Actual affine completeness of the six one-qubit stabilizer atoms

This is the first unconditional physical feasibility slice.  Its atoms are
the `±1` eigenstates of the three Hermitian one-qubit Paulis `X`, `Y`, and
`Z`.  Each atom is constructed through an actual independent signed Pauli
frame; no affine-completeness field is attached to the atom type.
-/

namespace AgtXIv.Stabilizer

noncomputable section

open scoped BigOperators

/-- The six pure one-qubit Pauli eigenstates.  The sign names the eigenvalue
of the unsigned Pauli; the signed frame generator always has eigenvalue `+1`.
-/
inductive QubitStabilizerAtom where
  | xPlus | xMinus | yPlus | yMinus | zPlus | zMinus
deriving DecidableEq, Fintype

/-- The signed Pauli whose common `+1` eigenspace is the named atom. -/
def QubitStabilizerAtom.signedPauli : QubitStabilizerAtom → Pauli 1
  | .xPlus => Pauli.X
  | .xMinus => -Pauli.X
  | .yPlus => Pauli.Y
  | .yMinus => -Pauli.Y
  | .zPlus => Pauli.Z
  | .zMinus => -Pauli.Z

@[simp]
theorem QubitStabilizerAtom.signedPauli_sq (a : QubitStabilizerAtom) :
    a.signedPauli ^ 2 = 1 := by
  cases a <;> decide

@[simp]
theorem QubitStabilizerAtom.signedPauli_ne_one (a : QubitStabilizerAtom) :
    a.signedPauli ≠ 1 := by
  cases a <;> decide

@[simp]
theorem QubitStabilizerAtom.signedPauli_ne_minus_one
    (a : QubitStabilizerAtom) :
    a.signedPauli ≠ -(1 : Pauli 1) := by
  cases a <;> decide

/-- The nontrivial word in the one-generator binary label group. -/
def binaryOneGenerator : BinaryWord 1 :=
  Multiplicative.ofAdd (fun _ => (1 : ZMod 2))

@[simp]
theorem binaryOneGenerator_ne_one : binaryOneGenerator ≠ (1 : BinaryWord 1) := by
  intro h
  have hc := congrArg (fun a : BinaryWord 1 => a.toAdd 0) h
  norm_num [binaryOneGenerator] at hc

/-- A one-bit word is determined by its sole coordinate. -/
theorem binaryWord_one_ext {a b : BinaryWord 1}
    (h : a.toAdd 0 = b.toAdd 0) : a = b := by
  apply Multiplicative.toAdd.injective
  funext i
  simpa [Subsingleton.elim i 0] using h

/-- The one-generator binary group has exactly the identity and its generator.
-/
theorem binaryWord_one_eq_one_or_generator (a : BinaryWord 1) :
    a = 1 ∨ a = binaryOneGenerator := by
  have hv : a.toAdd 0 = 0 ∨ a.toAdd 0 = 1 :=
    F2Bits.f2_eq_zero_or_one (a.toAdd 0)
  rcases hv with h0 | h1
  · left
    apply binaryWord_one_ext
    simpa using h0
  · right
    apply binaryWord_one_ext
    simpa [binaryOneGenerator] using h1

/-- Evaluate a one-generator binary word at an involutive Pauli. -/
def binaryOneEval (P : Pauli 1) (a : BinaryWord 1) : Pauli 1 :=
  if a = 1 then 1 else P

@[simp]
theorem binaryOneEval_one (P : Pauli 1) : binaryOneEval P 1 = 1 := by
  simp [binaryOneEval]

@[simp]
theorem binaryOneEval_generator (P : Pauli 1) :
    binaryOneEval P binaryOneGenerator = P := by
  simp [binaryOneEval, binaryOneGenerator_ne_one]

/-- The binary evaluation is a homomorphism once the chosen Pauli squares to
the identity. -/
def binaryOnePauliHom (P : Pauli 1) (hP : P ^ 2 = 1) :
    BinaryWord 1 →* Pauli 1 where
  toFun := binaryOneEval P
  map_one' := binaryOneEval_one P
  map_mul' a b := by
    rcases binaryWord_one_eq_one_or_generator a with rfl | rfl <;>
      rcases binaryWord_one_eq_one_or_generator b with rfl | rfl
    · simp
    · simp
    · simp
    · have hg : binaryOneGenerator * binaryOneGenerator = 1 := by
        simpa [pow_two] using binaryWord_sq binaryOneGenerator
      rw [hg, binaryOneEval_one, binaryOneEval_generator]
      simpa [pow_two] using hP.symm

theorem one_ne_minus_one_pauli_one : (1 : Pauli 1) ≠ -1 := by
  decide

/-- Every named one-qubit atom supplies an actual independent, phase-clean
rank-one signed Pauli frame. -/
def qubitStabilizerFrame (a : QubitStabilizerAtom) :
    IndependentSignedPauliFrame 1 1 where
  eval := binaryOnePauliHom a.signedPauli a.signedPauli_sq
  independent := by
    intro u v huv
    rcases binaryWord_one_eq_one_or_generator u with rfl | rfl <;>
      rcases binaryWord_one_eq_one_or_generator v with rfl | rfl
    · rfl
    · simp only [binaryOnePauliHom, MonoidHom.coe_mk, OneHom.coe_mk,
        binaryOneEval_one, binaryOneEval_generator] at huv
      exact (a.signedPauli_ne_one huv.symm).elim
    · simp only [binaryOnePauliHom, MonoidHom.coe_mk, OneHom.coe_mk,
        binaryOneEval_one, binaryOneEval_generator] at huv
      exact (a.signedPauli_ne_one huv).elim
    · rfl
  minusOneExcluded := by
    intro u
    rcases binaryWord_one_eq_one_or_generator u with rfl | rfl
    · exact one_ne_minus_one_pauli_one
    · exact a.signedPauli_ne_minus_one

/-- The two one-bit labels exhaust the binary frame group. -/
theorem binaryWord_one_univ :
    (Finset.univ : Finset (BinaryWord 1)) = {1, binaryOneGenerator} := by
  ext u
  simp only [Finset.mem_univ, Finset.mem_insert, Finset.mem_singleton, true_iff]
  exact binaryWord_one_eq_one_or_generator u

theorem sum_binaryWord_one {M : Type*} [AddCommMonoid M]
    (f : BinaryWord 1 → M) :
    ∑ u, f u = f 1 + f binaryOneGenerator := by
  rw [show Finset.univ = ({1, binaryOneGenerator} : Finset (BinaryWord 1)) from
    binaryWord_one_univ]
  rw [Finset.sum_insert]
  · simp
  · simpa only [Finset.mem_singleton] using
      (Ne.symm binaryOneGenerator_ne_one)

/-- Closed matrix form of the projector associated with a signed one-qubit
Pauli generator. -/
def qubitPauliEigenProjector (a : QubitStabilizerAtom) : CMatrix 2 2 :=
  (2 : ℂ)⁻¹ • (1 + a.signedPauli.toCMatrix)

/-- The abstract stabilizer group average for each six-state frame is exactly
the familiar `(I + signed Pauli) / 2` eigenprojector. -/
theorem stabilizerProjectorMatrix_qubitFrame (a : QubitStabilizerAtom) :
    stabilizerProjectorMatrix (qubitStabilizerFrame a) =
      qubitPauliEigenProjector a := by
  rw [stabilizerProjectorMatrix]
  rw [sum_binaryWord_one]
  simp only [qubitStabilizerFrame, binaryOnePauliHom,
    MonoidHom.coe_mk, OneHom.coe_mk, binaryOneEval_one,
    binaryOneEval_generator]
  have hcard : Fintype.card (BinaryWord 1) = 2 := by decide
  rw [invOf_eq_inv]
  rw [hcard]
  norm_num [qubitPauliEigenProjector]

/-- The same six physical projectors embedded in the real Hermitian carrier. -/
noncomputable def qubitStabilizerHermitianAtom :
    QubitStabilizerAtom → HermitianMatrixReal 2 :=
  pureStabilizerHermitianAtom qubitStabilizerFrame

@[simp]
theorem coe_qubitStabilizerHermitianAtom (a : QubitStabilizerAtom) :
    (qubitStabilizerHermitianAtom a : CMatrix 2 2) =
      qubitPauliEigenProjector a := by
  change stabilizerProjectorMatrix (qubitStabilizerFrame a) = _
  exact stabilizerProjectorMatrix_qubitFrame a

/-- Explicit signed affine weights for a Hermitian one-qubit matrix.  They are
not claimed to be nonnegative. -/
def qubitStabilizerAffineWeight (A : HermitianMatrixReal 2) :
    QubitStabilizerAtom → ℝ
  | .xPlus => 1 / 6 + ((A : CMatrix 2 2) 0 1).re
  | .xMinus => 1 / 6 - ((A : CMatrix 2 2) 0 1).re
  | .yPlus => 1 / 6 - ((A : CMatrix 2 2) 0 1).im
  | .yMinus => 1 / 6 + ((A : CMatrix 2 2) 0 1).im
  | .zPlus => 1 / 6 +
      (((A : CMatrix 2 2) 0 0).re - ((A : CMatrix 2 2) 1 1).re) / 2
  | .zMinus => 1 / 6 -
      (((A : CMatrix 2 2) 0 0).re - ((A : CMatrix 2 2) 1 1).re) / 2

def allQubitStabilizerAtoms : Finset QubitStabilizerAtom :=
  {.xPlus, .xMinus, .yPlus, .yMinus, .zPlus, .zMinus}

theorem qubitStabilizerAtom_univ :
    (Finset.univ : Finset QubitStabilizerAtom) = allQubitStabilizerAtoms := by
  ext a
  cases a <;> simp [allQubitStabilizerAtoms]

/-- The six signed weights are normalized for every Hermitian input. -/
theorem sum_qubitStabilizerAffineWeight (A : HermitianMatrixReal 2) :
    ∑ a, qubitStabilizerAffineWeight A a = 1 := by
  rw [show Finset.univ = allQubitStabilizerAtoms from qubitStabilizerAtom_univ]
  simp [allQubitStabilizerAtoms, qubitStabilizerAffineWeight]
  ring

@[simp]
theorem real_smul_complex_re (r : ℝ) (z : ℂ) :
    (r • z).re = r * z.re := by
  rw [Complex.real_smul]
  exact Complex.re_ofReal_mul r z

@[simp]
theorem real_smul_complex_im (r : ℝ) (z : ℂ) :
    (r • z).im = r * z.im := by
  rw [Complex.real_smul]
  exact Complex.im_ofReal_mul r z

@[simp]
theorem complex_smul_complex_re (c z : ℂ) :
    (c • z).re = c.re * z.re - c.im * z.im := by
  rw [smul_eq_mul]
  exact Complex.mul_re c z

@[simp]
theorem complex_smul_complex_im (c z : ℂ) :
    (c • z).im = c.re * z.im + c.im * z.re := by
  rw [smul_eq_mul]
  exact Complex.mul_im c z

/-- Coercing the real scalar action on a Hermitian matrix to an entry uses
ordinary multiplication by the corresponding real complex scalar.  Naming
this compatibility avoids relying on a particular definitional choice among
Mathlib's equivalent real scalar actions on `ℂ`. -/
@[simp]
theorem coe_real_smul_hermitian_apply {d : ℕ} (r : ℝ)
    (A : HermitianMatrixReal d) (i j : Fin d) :
    ((((r • A : HermitianMatrixReal d) : CMatrix d d) i j)) =
      (r : ℂ) * ((A : CMatrix d d) i j) := by
  change r • ((A : CMatrix d d) i j) = _
  rfl

set_option maxHeartbeats 800000 in
/-- The explicit Bloch-coordinate weights reconstruct every Hermitian
trace-one `2 × 2` matrix.  Positivity is not used: this is an affine
feasibility theorem, not a convex-mixture theorem. -/
theorem qubitStabilizerAffineWeight_signedDecomp
    (A : HermitianMatrixReal 2) (hTrace : A ∈ traceOneHermitianSet 2) :
    AgtXIv.RoM.SignedDecomp qubitStabilizerHermitianAtom A
      (qubitStabilizerAffineWeight A) := by
  have hHerm : Matrix.conjTranspose (A : CMatrix 2 2) = (A : CMatrix 2 2) := by
    exact A.property
  have h00 := congrArg (fun M : CMatrix 2 2 => M 0 0) hHerm
  have h01 := congrArg (fun M : CMatrix 2 2 => M 0 1) hHerm
  have h10 := congrArg (fun M : CMatrix 2 2 => M 1 0) hHerm
  have h11 := congrArg (fun M : CMatrix 2 2 => M 1 1) hHerm
  simp only [Matrix.conjTranspose_apply] at h00 h01 h10 h11
  change Matrix.trace (A : CMatrix 2 2) = 1 at hTrace
  have hTr := hTrace
  simp only [Matrix.trace, Fin.sum_univ_two] at hTr
  unfold AgtXIv.RoM.SignedDecomp AgtXIv.RoM.reconstruct
  apply Subtype.ext
  ext i j
  fin_cases i <;> fin_cases j
  all_goals
    rw [show Finset.univ = allQubitStabilizerAtoms from
      qubitStabilizerAtom_univ]
    simp [allQubitStabilizerAtoms, qubitStabilizerAffineWeight,
      coe_qubitStabilizerHermitianAtom, qubitPauliEigenProjector,
      QubitStabilizerAtom.signedPauli, Pauli.X_toCMatrix,
      Pauli.Y_toCMatrix, Pauli.Z_toCMatrix, σx, σy, σz]
  all_goals
    apply Complex.ext <;>
      simp_all [Complex.ext_iff, HSMul.hSMul, SMul.smul,
        Complex.mul_re, Complex.mul_im, ZMod.val_two_eq_two_mod, pow_two] <;>
      ring_nf <;>
      linarith [hTr.1, h00, h10, h11]

/-- Every Hermitian trace-one one-qubit matrix lies in the affine span of the
six actual stabilizer projectors.  This is the reverse inclusion that the
generic feasibility theorem deliberately leaves as an obligation. -/
theorem qubit_traceOne_le_stabilizerAffineSpan :
    traceOneHermitianAffine 2 ≤
      affineSpan ℝ (Set.range qubitStabilizerHermitianAtom) := by
  intro A hA
  let w := qubitStabilizerAffineWeight A
  have hw : ∑ a, w a = 1 := sum_qubitStabilizerAffineWeight A
  have hdecomp : AgtXIv.RoM.SignedDecomp
      qubitStabilizerHermitianAtom A w :=
    qubitStabilizerAffineWeight_signedDecomp A hA
  have hmem : Finset.univ.affineCombination ℝ
      qubitStabilizerHermitianAtom w ∈
        affineSpan ℝ (Set.range qubitStabilizerHermitianAtom) := by
    apply affineCombination_mem_affineSpan
    simpa using hw
  have hcomb : Finset.univ.affineCombination ℝ
      qubitStabilizerHermitianAtom w = A := by
    rw [Finset.affineCombination_eq_linear_combination]
    · exact hdecomp
    · simpa using hw
  rwa [hcomb] at hmem

/-- Exact affine equality for the six one-qubit stabilizer projectors. -/
theorem qubit_stabilizerAffineSpan_eq_traceOne :
    affineSpan ℝ (Set.range qubitStabilizerHermitianAtom) =
      traceOneHermitianAffine 2 := by
  apply le_antisymm
  · exact affineSpan_pureStabilizer_le_traceOne qubitStabilizerFrame
  · exact qubit_traceOne_le_stabilizerAffineSpan

/-- Unconditional Howard-style feasibility for every exact one-qubit density
matrix, with an explicit normalized real coefficient vector.  The
coefficients may be negative. -/
theorem qubit_density_exists_normalized_stabilizer_signedDecomp
    (ρ : DensityMatrix 2) :
    ∃ x : QubitStabilizerAtom → ℝ,
      (∑ a, x a = 1) ∧
      AgtXIv.RoM.SignedDecomp qubitStabilizerHermitianAtom
        ρ.toTraceOneHermitian.1 x := by
  refine ⟨qubitStabilizerAffineWeight ρ.toTraceOneHermitian.1,
    sum_qubitStabilizerAffineWeight ρ.toTraceOneHermitian.1, ?_⟩
  exact qubitStabilizerAffineWeight_signedDecomp
    ρ.toTraceOneHermitian.1 ρ.toTraceOneHermitian.2

end

end AgtXIv.Stabilizer
