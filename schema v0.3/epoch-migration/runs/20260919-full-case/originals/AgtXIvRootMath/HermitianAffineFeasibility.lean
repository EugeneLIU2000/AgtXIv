import AgtXIvRootMath.FiniteAtomRoM
import AgtXIvRootMath.GottesmanRankNProjector
import Mathlib.Algebra.Star.Module
import Mathlib.LinearAlgebra.AffineSpace.Combination

/-!
# Affine-span feasibility on the Hermitian trace-one slice

This module closes the abstract finite-atom feasibility step without storing
feasibility in a target or atom structure.  Membership in the affine span is
converted into an explicit normalized signed decomposition.

For quantum states, the real ambient vector space is the self-adjoint part of
the complex matrix space.  Trace-one matrices form an affine slice of that real
space; they are deliberately not treated as a vector subspace.
-/

namespace AgtXIv.RoM

open scoped BigOperators

variable {ι V : Type*} [Fintype ι]
variable [AddCommGroup V] [Module ℝ V]

/-- Affine-span membership supplies explicit normalized real coefficients and
a signed reconstruction.  This is the missing feasibility bridge used by the
finite-atom robustness development. -/
theorem exists_normalized_signedDecomp_of_mem_affineSpan
    (atom : ι → V) (ρ : V)
    (hρ : ρ ∈ affineSpan ℝ (Set.range atom)) :
    ∃ x : ι → ℝ, (∑ i, x i = 1) ∧ SignedDecomp atom ρ x := by
  obtain ⟨x, hxSum, hxAffine⟩ :=
    eq_affineCombination_of_mem_affineSpan_of_fintype hρ
  refine ⟨x, hxSum, ?_⟩
  unfold SignedDecomp reconstruct
  rw [← Finset.univ.affineCombination_eq_linear_combination atom x hxSum]
  exact hxAffine.symm

/-- A proved inclusion of a target set in the atoms' affine span gives
feasibility for every target in that set.  The inclusion is an explicit proof
obligation, not a field hidden in the target carrier. -/
theorem exists_normalized_signedDecomp_of_subset_affineSpan
    (atom : ι → V) (targets : Set V)
    (hcomplete : targets ⊆ affineSpan ℝ (Set.range atom))
    {ρ : V} (hρ : ρ ∈ targets) :
    ∃ x : ι → ℝ, (∑ i, x i = 1) ∧ SignedDecomp atom ρ x :=
  exists_normalized_signedDecomp_of_mem_affineSpan atom ρ (hcomplete hρ)

end AgtXIv.RoM

namespace AgtXIv.Stabilizer

noncomputable section

/-- Hermitian complex matrices, regarded as a real vector space. -/
abbrev HermitianMatrixReal (d : ℕ) := selfAdjoint (CMatrix d d)

/-- Real trace normalization functional on the Hermitian real vector space.
Taking the real part gives the scalar type required by the real coefficient
optimization.  On a trace-one matrix it is exactly one. -/
def hermitianToMatrixReal (d : ℕ) :
    HermitianMatrixReal d →ₗ[ℝ] CMatrix d d where
  toFun A := A
  map_add' _ _ := rfl
  map_smul' _ _ := rfl

def hermitianTraceReal (d : ℕ) : HermitianMatrixReal d →ₗ[ℝ] ℝ :=
  Complex.reLm.comp
    ((Matrix.traceLinearMap (Fin d) ℝ ℂ).comp (hermitianToMatrixReal d))

@[simp]
theorem hermitianTraceReal_apply {d : ℕ} (A : HermitianMatrixReal d) :
    hermitianTraceReal d A = (Matrix.trace (A : CMatrix d d)).re := rfl

/-- The trace-one affine slice of the real Hermitian matrix space, represented
as a set because it is not closed under vector addition or real scaling. -/
def traceOneHermitianSet (d : ℕ) : Set (HermitianMatrixReal d) :=
  {A | Matrix.trace (A : CMatrix d d) = 1}

/-- The trace-one condition is genuinely affine: real affine combinations of
trace-one Hermitian matrices remain trace one. -/
def traceOneHermitianAffine (d : ℕ) :
    AffineSubspace ℝ (HermitianMatrixReal d) where
  carrier := traceOneHermitianSet d
  smul_vsub_vadd_mem c p₁ p₂ p₃ hp₁ hp₂ hp₃ := by
    change Matrix.trace
      (((c • (p₁ - p₂) + p₃ : HermitianMatrixReal d) : CMatrix d d)) = 1
    change Matrix.trace
      ((c : ℂ) • ((p₁ : CMatrix d d) - (p₂ : CMatrix d d)) +
        (p₃ : CMatrix d d)) = 1
    simp only [Matrix.trace_add, Matrix.trace_smul, Matrix.trace_sub]
    change Matrix.trace (p₁ : CMatrix d d) = 1 at hp₁
    change Matrix.trace (p₂ : CMatrix d d) = 1 at hp₂
    change Matrix.trace (p₃ : CMatrix d d) = 1 at hp₃
    rw [hp₁, hp₂, hp₃]
    simp

/-- A carrier for points of the Hermitian trace-one affine slice.  Linear
combinations are performed in `HermitianMatrixReal`; affine normalization is
tracked by this subtype. -/
def TraceOneHermitianMatrix (d : ℕ) :=
  {A : HermitianMatrixReal d // A ∈ traceOneHermitianSet d}

/-- Every exact density matrix determines a point in the real Hermitian
trace-one slice. -/
def DensityMatrix.toTraceOneHermitian {d : ℕ} (ρ : DensityMatrix d) :
    TraceOneHermitianMatrix d :=
  ⟨⟨ρ.val, by
      change Matrix.conjTranspose ρ.val = ρ.val
      exact ρ.posSemidef.1.eq⟩,
    ρ.trace_one⟩

@[simp]
theorem DensityMatrix.hermitianTraceReal_toTraceOneHermitian {d : ℕ}
    (ρ : DensityMatrix d) :
    hermitianTraceReal d ρ.toTraceOneHermitian.1 = 1 := by
  change (Matrix.trace ρ.val).re = 1
  rw [ρ.trace_one]
  norm_num

@[simp]
theorem DensityMatrix.coe_toTraceOneHermitian {d : ℕ} (ρ : DensityMatrix d) :
    (((ρ.toTraceOneHermitian : TraceOneHermitianMatrix d).1 :
      HermitianMatrixReal d) : CMatrix d d) = ρ.val := rfl

/-- Pure stabilizer projectors supplied by a complete independent signed Pauli
frame, embedded in the same Hermitian trace-one carrier used by robustness. -/
noncomputable def pureStabilizerTraceOneHermitian {n : ℕ}
    (F : IndependentSignedPauliFrame n n) :
    TraceOneHermitianMatrix (2 ^ n) :=
  (pureStabilizerDensity F).toDensityMatrix.toTraceOneHermitian

@[simp]
theorem coe_pureStabilizerTraceOneHermitian {n : ℕ}
    (F : IndependentSignedPauliFrame n n) :
    (((pureStabilizerTraceOneHermitian F : TraceOneHermitianMatrix (2 ^ n)).1 :
      HermitianMatrixReal (2 ^ n)) : CMatrix (2 ^ n) (2 ^ n)) =
      stabilizerProjectorMatrix F := rfl

/-- The Hermitian-vector representative of a finite family of pure stabilizer
projectors.  The finite index is intentional: finiteness of the complete atom
set must eventually be proved by an enumeration theorem, not assumed by the
density carrier. -/
noncomputable def pureStabilizerHermitianAtom {ι : Type*} {n : ℕ}
    (frame : ι → IndependentSignedPauliFrame n n) (i : ι) :
    HermitianMatrixReal (2 ^ n) :=
  (pureStabilizerTraceOneHermitian (frame i)).1

theorem pureStabilizerHermitianAtom_mem_traceOne {ι : Type*} {n : ℕ}
    (frame : ι → IndependentSignedPauliFrame n n) (i : ι) :
    pureStabilizerHermitianAtom frame i ∈ traceOneHermitianAffine (2 ^ n) :=
  (pureStabilizerTraceOneHermitian (frame i)).2

@[simp]
theorem hermitianTraceReal_pureStabilizerHermitianAtom
    {ι : Type*} {n : ℕ}
    (frame : ι → IndependentSignedPauliFrame n n) (i : ι) :
    hermitianTraceReal (2 ^ n) (pureStabilizerHermitianAtom frame i) = 1 := by
  exact DensityMatrix.hermitianTraceReal_toTraceOneHermitian
    (pureStabilizerDensity (frame i)).toDensityMatrix

/-- One direction of affine completeness is automatic: normalized pure
stabilizer projectors cannot leave the trace-one affine slice. -/
theorem affineSpan_pureStabilizer_le_traceOne {ι : Type*} {n : ℕ}
    (frame : ι → IndependentSignedPauliFrame n n) :
    affineSpan ℝ (Set.range (pureStabilizerHermitianAtom frame)) ≤
      traceOneHermitianAffine (2 ^ n) := by
  rw [affineSpan_le]
  rintro A ⟨i, rfl⟩
  exact pureStabilizerHermitianAtom_mem_traceOne frame i

/-- Exact Howard feasibility for a density target follows once a finite family
of pure stabilizer projectors has been proved to span the entire Hermitian
trace-one affine slice.  The reverse inclusion is the substantive atom
completeness obligation; it is exposed here as a theorem premise rather than a
field of `DensityMatrix`, `IndependentSignedPauliFrame`, or the atom family.

A later physical completion should discharge `hcomplete` by proving a finite
enumeration of all maximal signed stabilizer frames and showing, via a
Hermitian Pauli basis, that the trace-one slice lies in their affine span. -/
theorem density_exists_normalized_stabilizer_signedDecomp_of_affine_complete
    {ι : Type*} [Fintype ι] {n : ℕ}
    (frame : ι → IndependentSignedPauliFrame n n)
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (pureStabilizerHermitianAtom frame)))
    (ρ : DensityMatrix (2 ^ n)) :
    ∃ x : ι → ℝ,
      (∑ i, x i = 1) ∧
      AgtXIv.RoM.SignedDecomp (pureStabilizerHermitianAtom frame)
        ρ.toTraceOneHermitian.1 x := by
  apply AgtXIv.RoM.exists_normalized_signedDecomp_of_mem_affineSpan
  exact hcomplete ρ.toTraceOneHermitian.2

/-- The same result in the exact feasibility shape consumed by the attained
finite-atom robustness definition. -/
theorem density_stabilizer_feasible_of_affine_complete
    {ι : Type*} [Fintype ι] {n : ℕ}
    (frame : ι → IndependentSignedPauliFrame n n)
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (pureStabilizerHermitianAtom frame)))
    (ρ : DensityMatrix (2 ^ n)) :
    ∃ x : ι → ℝ,
      AgtXIv.RoM.SignedDecomp (pureStabilizerHermitianAtom frame)
        ρ.toTraceOneHermitian.1 x := by
  obtain ⟨x, _hxSum, hx⟩ :=
    density_exists_normalized_stabilizer_signedDecomp_of_affine_complete
      frame hcomplete ρ
  exact ⟨x, hx⟩

/-- The two inclusions package the exact affine-completeness statement once
the substantive reverse inclusion has been proved. -/
theorem affineSpan_pureStabilizer_eq_traceOne_of_complete
    {ι : Type*} {n : ℕ}
    (frame : ι → IndependentSignedPauliFrame n n)
    (hcomplete : traceOneHermitianAffine (2 ^ n) ≤
      affineSpan ℝ (Set.range (pureStabilizerHermitianAtom frame))) :
    affineSpan ℝ (Set.range (pureStabilizerHermitianAtom frame)) =
      traceOneHermitianAffine (2 ^ n) :=
  le_antisymm (affineSpan_pureStabilizer_le_traceOne frame) hcomplete

end

end AgtXIv.Stabilizer
