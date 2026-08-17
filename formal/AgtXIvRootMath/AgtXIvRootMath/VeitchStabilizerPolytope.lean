import AgtXIvRootMath.GottesmanPauliGenerators
import AgtXIvRootMath.FiniteAtomTotalRoM

/-!
# Finite pure stabilizer atoms and their convex hull

The pure atoms in this module are the rank-one projectors derived from complete
signed Pauli frames.  A later bridge proves that this same atom set is the
Clifford orbit used in Veitch's operational presentation; the two predicates
are deliberately not identified by definition.

Classical random mixing is represented by nonnegative real coefficients that
sum to one.  It is therefore distinct from coherent superposition.
-/

namespace AgtXIv.Stabilizer

open scoped BigOperators ComplexOrder

variable {d n r : ℕ}

/-- Complete signed Pauli frames form a finite type because both the binary
label group and the signed Pauli group are finite. -/
noncomputable instance frameFinite (n r : ℕ) :
    Finite (IndependentSignedPauliFrame n r) :=
  Finite.of_injective
    (fun F : IndependentSignedPauliFrame n r =>
      (F.eval : BinaryWord r → Pauli n)) (by
        intro F G h
        cases F with
        | mk f hf hm =>
          cases G with
          | mk g hg hn =>
            have hfg : f = g := MonoidHom.ext fun a => congrFun h a
            subst g
            rfl)

noncomputable instance frameFintype (n r : ℕ) :
    Fintype (IndependentSignedPauliFrame n r) := Fintype.ofFinite _

/-- Real part of the matrix trace as a real-linear normalization functional. -/
noncomputable def traceReLinear (d : ℕ) : CMatrix d d →ₗ[ℝ] ℝ :=
  Complex.reLm.comp (Matrix.traceLinearMap (Fin d) ℝ ℂ)

@[simp] theorem traceReLinear_apply (A : CMatrix d d) :
    traceReLinear d A = (Matrix.trace A).re := rfl

/-- The finite atom family indexed by all complete independent signed Pauli
frames.  Different frames may index the same projector; duplicates do not add
new convex-hull points. -/
noncomputable def frameAtom (n : ℕ) :
    IndependentSignedPauliFrame n n → CMatrix (2 ^ n) (2 ^ n) :=
  fun F => stabilizerProjectorMatrix F

theorem traceReLinear_frameAtom (n : ℕ)
    (F : IndependentSignedPauliFrame n n) :
    traceReLinear (2 ^ n) (frameAtom n F) = 1 := by
  simp [frameAtom, stabilizerProjectorMatrix_trace_one]

/-- Pure stabilizer membership in the common-eigenspace presentation. -/
def PureStabilizerByFrame (n : ℕ) (ρ : CMatrix (2 ^ n) (2 ^ n)) : Prop :=
  ∃ F : IndependentSignedPauliFrame n n, ρ = frameAtom n F

/-- The frame-presented candidate free set, written as the ordinary finite
convex hull of the pure frame projectors.  It becomes Veitch's `STAB` only
after the separate frame/common-eigenspace-to-Clifford-orbit theorem is proved. -/
def StabilizerFreeByFrames (n : ℕ) (ρ : CMatrix (2 ^ n) (2 ^ n)) : Prop :=
  AgtXIv.RoM.FreeByAtoms (frameAtom n) ρ

/-- A classical convex mixture of stabilizer atoms has trace one. -/
theorem stabilizerFreeByFrames_trace_one (n : ℕ)
    (ρ : CMatrix (2 ^ n) (2 ^ n))
    (hρ : StabilizerFreeByFrames n ρ) : Matrix.trace ρ = 1 := by
  obtain ⟨p, hp, hsum, hrec⟩ := hρ
  rw [← hrec]
  simp only [AgtXIv.RoM.reconstruct, Matrix.trace_sum, Matrix.trace_smul,
    frameAtom, stabilizerProjectorMatrix_trace_one]
  calc
    ∑ x, p x • (1 : ℂ) = ∑ x, (p x : ℂ) := by
      apply Finset.sum_congr rfl
      intro i _
      simp [Complex.real_smul]
    _ = ((∑ x, p x : ℝ) : ℂ) := by norm_cast
    _ = 1 := by rw [hsum]; norm_num

/-- A classical convex mixture of stabilizer atoms remains positive
semidefinite. -/
theorem stabilizerFreeByFrames_posSemidef (n : ℕ)
    (ρ : CMatrix (2 ^ n) (2 ^ n))
    (hρ : StabilizerFreeByFrames n ρ) : ρ.PosSemidef := by
  obtain ⟨p, hp, hsum, hrec⟩ := hρ
  rw [← hrec]
  unfold AgtXIv.RoM.reconstruct
  apply Matrix.posSemidef_sum
  intro i hi
  change ((p i : ℂ) • stabilizerProjectorMatrix i).PosSemidef
  exact (stabilizerProjectorMatrix_posSemidef i).smul
    (RCLike.ofReal_nonneg.mpr (hp i))

/-- Package a free convex mixture as an exact density matrix. -/
noncomputable def densityOfStabilizerFree (n : ℕ)
    (ρ : CMatrix (2 ^ n) (2 ^ n))
    (hρ : StabilizerFreeByFrames n ρ) : DensityMatrix (2 ^ n) where
  val := ρ
  posSemidef := stabilizerFreeByFrames_posSemidef n ρ hρ
  trace_one := stabilizerFreeByFrames_trace_one n ρ hρ

end AgtXIv.Stabilizer
