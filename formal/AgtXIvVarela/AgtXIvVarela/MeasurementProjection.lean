import AgtXIvRootMath.RootMathCompletion

/-!
# Exact Pauli-coordinate projection of the stabilizer polytope

The map in this file only forgets unmeasured expectation coordinates.  It is
not a projective measurement, a partial trace, or a map to a smaller Hilbert
space.
-/

namespace AgtXIv.Varela

open scoped BigOperators ComplexOrder
open AgtXIv.Stabilizer

noncomputable section

/-- A normalized finite Pauli measurement window.  The fixed representatives
are Hermitian involutions, have nonzero binary support, and represent distinct
phase classes.  Thus identity, duplicates, and sign-duplicates are excluded. -/
structure MeasurementWindow (n m : ℕ) where
  nonempty : 0 < m
  observable : Fin m → Pauli n
  involutive : ∀ i, observable i ^ 2 = 1
  nonidentitySupport : ∀ i, F2Support.pauli (observable i) ≠ 0
  distinctPhaseClass : Function.Injective
    (fun i => F2Support.pauli (observable i))

namespace MeasurementWindow

variable {n m : ℕ}

/-- One real expectation coordinate.  Taking the real part gives an exact
real-linear map; Hermiticity of the window representatives ensures this is the
usual physical Pauli expectation on density matrices. -/
noncomputable def expectationCoordinate (W : MeasurementWindow n m)
    (i : Fin m) : HermitianMatrixReal (2 ^ n) →ₗ[ℝ] ℝ where
  toFun A :=
    (Matrix.trace ((W.observable i).toCMatrix *
      (A : CMatrix (2 ^ n) (2 ^ n)))).re
  map_add' A B := by
    simp [mul_add, Matrix.trace_add]
  map_smul' c A := by
    change
      (Matrix.trace ((W.observable i).toCMatrix *
        (c • (A : CMatrix (2 ^ n) (2 ^ n))))).re =
        c * (Matrix.trace ((W.observable i).toCMatrix *
          (A : CMatrix (2 ^ n) (2 ^ n)))).re
    rw [mul_smul_comm]
    have hTrace :=
      (Matrix.traceLinearMap (Fin (2 ^ n)) ℝ ℂ).map_smul c
        ((W.observable i).toCMatrix *
          (A : CMatrix (2 ^ n) (2 ^ n)))
    change Matrix.trace
      (c • ((W.observable i).toCMatrix *
        (A : CMatrix (2 ^ n) (2 ^ n)))) = _ at hTrace
    rw [hTrace]
    change
      (c • Matrix.trace ((W.observable i).toCMatrix *
        (A : CMatrix (2 ^ n) (2 ^ n)))).re =
        c • (Matrix.trace ((W.observable i).toCMatrix *
          (A : CMatrix (2 ^ n) (2 ^ n)))).re
    exact Complex.smul_re c _

/-- The exact coordinate projection retaining only the expectations in `W`. -/
noncomputable def expectationProjection (W : MeasurementWindow n m) :
    HermitianMatrixReal (2 ^ n) →ₗ[ℝ] (Fin m → ℝ) where
  toFun A := fun i => W.expectationCoordinate i A
  map_add' A B := by
    funext i
    exact (W.expectationCoordinate i).map_add A B
  map_smul' c A := by
    funext i
    exact (W.expectationCoordinate i).map_smul c A

/-- Projection of a pure stabilizer atom associated with a complete signed
Pauli frame. -/
noncomputable def projectedFrameAtom (W : MeasurementWindow n m)
    (F : IndependentSignedPauliFrame n n) : Fin m → ℝ :=
  W.expectationProjection (completeFrameHermitianAtom n F)

/-- The top-down projected stabilizer polytope, represented by normalized
classical mixtures of the projected pure stabilizer atoms. -/
def ProjectedStabilizerPolytope (W : MeasurementWindow n m) :
    Set (Fin m → ℝ) :=
  {b | AgtXIv.RoM.FreeByAtoms W.projectedFrameAtom b}

/-- A linear coordinate projection commutes with finite signed
reconstruction. -/
theorem expectationProjection_reconstruct
    (W : MeasurementWindow n m)
    (x : IndependentSignedPauliFrame n n → ℝ) :
    W.expectationProjection
        (AgtXIv.RoM.reconstruct (completeFrameHermitianAtom n) x) =
      AgtXIv.RoM.reconstruct W.projectedFrameAtom x := by
  unfold AgtXIv.RoM.reconstruct projectedFrameAtom
  simp

/-- Exact top-down semantics: a vector belongs to the projected stabilizer
polytope iff it is the coordinate projection of a full stabilizer-free
Hermitian matrix. -/
theorem mem_projectedStabilizerPolytope_iff
    (W : MeasurementWindow n m) (b : Fin m → ℝ) :
    b ∈ W.ProjectedStabilizerPolytope ↔
      ∃ A : HermitianMatrixReal (2 ^ n),
        AgtXIv.RoM.FreeByAtoms (completeFrameHermitianAtom n) A ∧
        W.expectationProjection A = b := by
  constructor
  · rintro ⟨p, hp, hsum, hrec⟩
    refine ⟨AgtXIv.RoM.reconstruct (completeFrameHermitianAtom n) p,
      ⟨p, hp, hsum, rfl⟩, ?_⟩
    rw [W.expectationProjection_reconstruct, hrec]
  · rintro ⟨A, ⟨p, hp, hsum, hrec⟩, hproj⟩
    refine ⟨p, hp, hsum, ?_⟩
    unfold AgtXIv.RoM.SignedDecomp at hrec ⊢
    rw [← W.expectationProjection_reconstruct, hrec, hproj]

end MeasurementWindow

end

end AgtXIv.Varela
