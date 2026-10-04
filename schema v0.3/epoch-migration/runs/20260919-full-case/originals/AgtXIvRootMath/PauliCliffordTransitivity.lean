import AgtXIvRootMath.PauliSyndromeIntertwiner
import AgtXIvRootMath.SemanticCliffordFrames
import AgtXIvRootMath.StandardZIndependentFrame

/-!
# Clifford transitivity on complete signed Pauli frames

This module closes the phase-aware stabilizer-frame transitivity theorem.
The syndrome change-of-basis unitary has already been constructed without a
normalizer witness and proved to conjugate both exact signed read words and
their exact signed dual flip words.  Here those generator identities are
extended to every phase-aware Pauli via the proved read/flip/central normal
form.  Faithfulness of the concrete matrix representation then turns the
transport into an actual Pauli-group automorphism and hence a
`SemanticClifford` certificate.

The final theorem constructs, for every complete independent signed Pauli
frame, a semantic Clifford mapping the standard signed-`Z` frame to it.  No
Clifford-surjectivity or orbit witness is assumed.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators Matrix
noncomputable section
set_option maxHeartbeats 1000000

namespace IndependentSignedPauliFrame

variable {n : ℕ}

/-- Matrix conjugation by the syndrome change-of-basis unitary. -/
def frameConjugate (A F : IndependentSignedPauliFrame n n)
    (M : CMatrix (2 ^ n) (2 ^ n)) : CMatrix (2 ^ n) (2 ^ n) :=
  frameChangeMatrix A F * M * (frameChangeMatrix A F)ᴴ

theorem frameConjugate_one (A F : IndependentSignedPauliFrame n n) :
    frameConjugate A F 1 = 1 := by
  have hright : frameChangeMatrix A F * (frameChangeMatrix A F)ᴴ = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff] using
      frameChangeMatrix_unitary A F
  simpa [frameConjugate] using hright

theorem frameConjugate_mul (A F : IndependentSignedPauliFrame n n)
    (M N : CMatrix (2 ^ n) (2 ^ n)) :
    frameConjugate A F (M * N) =
      frameConjugate A F M * frameConjugate A F N := by
  have hleft : (frameChangeMatrix A F)ᴴ * frameChangeMatrix A F = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff'] using
      frameChangeMatrix_unitary A F
  unfold frameConjugate
  calc
    frameChangeMatrix A F * (M * N) * (frameChangeMatrix A F)ᴴ =
      frameChangeMatrix A F * M * N * (frameChangeMatrix A F)ᴴ := by
        noncomm_ring
    _ = frameChangeMatrix A F * M *
        ((frameChangeMatrix A F)ᴴ * frameChangeMatrix A F) * N *
          (frameChangeMatrix A F)ᴴ := by rw [hleft]; noncomm_ring
    _ = (frameChangeMatrix A F * M * (frameChangeMatrix A F)ᴴ) *
        (frameChangeMatrix A F * N * (frameChangeMatrix A F)ᴴ) := by
          noncomm_ring

/-- Scalar Pauli phases are fixed by unitary conjugation. -/
theorem frameConjugate_central (A F : IndependentSignedPauliFrame n n)
    (m : ZMod 4) :
    frameConjugate A F (centralPauli n m).toCMatrix =
      (centralPauli n m).toCMatrix := by
  rw [centralPauli, Pauli.addPhase_toCMatrix]
  unfold frameConjugate
  have hright : frameChangeMatrix A F * (frameChangeMatrix A F)ᴴ = 1 := by
    simpa [Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff] using
      frameChangeMatrix_unitary A F
  calc
    frameChangeMatrix A F *
        (((-Complex.I) ^ m.val) • (1 : Pauli n).toCMatrix) *
          (frameChangeMatrix A F)ᴴ =
      ((-Complex.I) ^ m.val) •
        (frameChangeMatrix A F * (frameChangeMatrix A F)ᴴ) := by
          rw [Pauli.one_toCMatrix, Matrix.mul_smul, Matrix.smul_mul]
          simp
    _ = ((-Complex.I) ^ m.val) •
        (1 : CMatrix (2 ^ n) (2 ^ n)) := by rw [hright]
    _ = ((-Complex.I) ^ m.val) • (1 : Pauli n).toCMatrix := by
      rw [Pauli.one_toCMatrix]

/-- Read and dual-flip conjugation determines every ordered frame word. -/
theorem frameConjugate_frameWord (A F : IndependentSignedPauliFrame n n)
    (c : SupportCoordinates n) :
    frameConjugate A F (A.frameWord c).toCMatrix =
      (F.frameWord c).toCMatrix := by
  rw [frameWord, frameWord, Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix,
    Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
  rw [frameConjugate_mul]
  unfold frameConjugate
  rw [frameChangeMatrix_read_conjugates, frameChangeMatrix_flip_conjugates]

/-- Conjugation by the constructed unitary implements the exact
phase-preserving Pauli transport candidate on every signed Pauli. -/
theorem frameConjugates_transport (A F : IndependentSignedPauliFrame n n)
    (P : Pauli n) :
    frameConjugate A F P.toCMatrix = (transport A F P).toCMatrix := by
  calc
    frameConjugate A F P.toCMatrix =
      frameConjugate A F
        (centralPauli n (A.framePhase P) *
          A.frameWord (A.frameCoordinates P)).toCMatrix := by
            rw [A.frameDecompose]
    _ = frameConjugate A F
        ((centralPauli n (A.framePhase P)).toCMatrix *
          (A.frameWord (A.frameCoordinates P)).toCMatrix) := by
            rw [Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
    _ = frameConjugate A F (centralPauli n (A.framePhase P)).toCMatrix *
        frameConjugate A F (A.frameWord (A.frameCoordinates P)).toCMatrix :=
          frameConjugate_mul A F _ _
    _ = (centralPauli n (A.framePhase P)).toCMatrix *
        (F.frameWord (A.frameCoordinates P)).toCMatrix := by
          rw [frameConjugate_central, frameConjugate_frameWord]
    _ = (transport A F P).toCMatrix := by
          rw [transport, Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]

/-- Exact Pauli transport as a monoid homomorphism, with multiplicativity
proved from unitary conjugation and matrix faithfulness rather than assumed. -/
def frameTransportHom (A F : IndependentSignedPauliFrame n n) :
    Pauli n →* Pauli n where
  toFun := transport A F
  map_one' := by
    apply pauli_toCMatrix_injective
    change (transport A F 1).toCMatrix = (1 : Pauli n).toCMatrix
    rw [← frameConjugates_transport]
    simpa [Pauli.one_toCMatrix] using frameConjugate_one A F
  map_mul' P Q := by
    apply pauli_toCMatrix_injective
    change (transport A F (P * Q)).toCMatrix =
      (transport A F P * transport A F Q).toCMatrix
    rw [← frameConjugates_transport]
    rw [Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]
    rw [frameConjugate_mul]
    rw [frameConjugates_transport, frameConjugates_transport]
    rw [Pauli.mul_toCMatrix_eq_toCMatrix_mul_toCMatrix]

theorem frameTransport_injective (A F : IndependentSignedPauliFrame n n) :
    Function.Injective (transport A F) := by
  intro P Q h
  apply pauli_toCMatrix_injective
  have hconj : frameConjugate A F P.toCMatrix =
      frameConjugate A F Q.toCMatrix := by
    rw [frameConjugates_transport, frameConjugates_transport, h]
  let U := frameChangeMatrix A F
  have hleft : Uᴴ * U = 1 := by
    simpa [U, Matrix.IsUnitary, Matrix.mem_unitaryGroup_iff'] using
      frameChangeMatrix_unitary A F
  have hrecover (M : CMatrix (2 ^ n) (2 ^ n)) :
      Uᴴ * frameConjugate A F M * U = M := by
    unfold frameConjugate
    change Uᴴ * (U * M * Uᴴ) * U = M
    calc
      Uᴴ * (U * M * Uᴴ) * U =
          (Uᴴ * U) * M * (Uᴴ * U) := by
        noncomm_ring
      _ = M := by rw [hleft]; simp
  calc
    P.toCMatrix = Uᴴ * frameConjugate A F P.toCMatrix * U :=
      (hrecover _).symm
    _ = Uᴴ * frameConjugate A F Q.toCMatrix * U := by rw [hconj]
    _ = Q.toCMatrix := hrecover _

theorem frameTransport_bijective (A F : IndependentSignedPauliFrame n n) :
    Function.Bijective (frameTransportHom A F) := by
  apply (Fintype.bijective_iff_injective_and_card _).2
  exact ⟨frameTransport_injective A F, rfl⟩

/-- Exact signed-Pauli automorphism implemented by the constructed unitary. -/
def frameTransportEquiv (A F : IndependentSignedPauliFrame n n) :
    Pauli n ≃* Pauli n :=
  MulEquiv.ofBijective (frameTransportHom A F) (frameTransport_bijective A F)

/-- Constructed semantic Clifford carrying frame `A` to frame `F`. -/
def frameChangeClifford (A F : IndependentSignedPauliFrame n n) :
    SemanticClifford n where
  matrix := frameChangeMatrix A F
  isUnitary := frameChangeMatrix_unitary A F
  action := frameTransportEquiv A F
  conjugates := frameConjugates_transport A F

/-- Two frame structures with the same exact evaluation homomorphism are
equal; their remaining fields are proofs. -/
theorem ext_eval {A F : IndependentSignedPauliFrame n n}
    (h : A.eval = F.eval) : A = F := by
  cases A
  cases F
  cases h
  rfl

/-- The constructed Clifford carries its source frame to its target frame
exactly, including all signed word evaluations. -/
theorem frameChangeClifford_mapFrame
    (A F : IndependentSignedPauliFrame n n) :
    (frameChangeClifford A F).mapFrame A = F := by
  apply ext_eval
  apply MonoidHom.ext
  intro a
  change transport A F (A.eval a) = F.eval a
  exact A.transport_eval F a

/-- Unconditional phase-aware Clifford transitivity from the standard
signed-`Z` frame to every complete independent signed Pauli frame. -/
theorem exists_semanticClifford_map_standardIndependentZFrame
    (F : IndependentSignedPauliFrame n n) :
    ∃ C : SemanticClifford n,
      C.mapFrame (standardIndependentZFrame n) = F := by
  exact ⟨frameChangeClifford (standardIndependentZFrame n) F,
    frameChangeClifford_mapFrame _ F⟩

end IndependentSignedPauliFrame

end
end AgtXIv.Stabilizer
