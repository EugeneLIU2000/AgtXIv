import AgtXIvRootMath

/-!
Run with `lake env lean Audit.lean`.  The output must contain no `sorryAx` and no
undeclared project axiom.  Lean's standard logical dependencies such as
`propext`, `Classical.choice`, and `Quot.sound` are reported rather than hidden.
-/

-- Abstract convex-geometric core: normalization, attainment, and the
-- automatically constructed stochastic push-forward.
#print axioms AgtXIv.RoM.coeff_sum_eq_one
#print axioms AgtXIv.RoM.normalized_l1
#print axioms AgtXIv.RoM.exists_l1Minimizer
#print axioms AgtXIv.RoM.feasible_faithful
#print axioms AgtXIv.RoM.kernelOfAtomImages
#print axioms AgtXIv.RoM.reconstruct_push_kernelOfAtomImages
#print axioms AgtXIv.RoM.finiteRoM_mono_of_atomImages

-- Gottesman: source generator conditions, group averaging, the general
-- 2^(n-r) fixed-space dimension, and the rank-one density projector.
#print axioms AgtXIv.Gottesman.groupAverage_mem_commonFixed
#print axioms AgtXIv.Gottesman.groupAverage_eq_self_iff
#print axioms AgtXIv.Gottesman.groupAverage_idempotent
#print axioms AgtXIv.Gottesman.range_groupAverageMap
#print axioms AgtXIv.Gottesman.groupAverage_isProjection
#print axioms AgtXIv.Stabilizer.trace_eval_eq_zero_of_support_ne_zero
#print axioms AgtXIv.Stabilizer.IndependentSignedPauliFrame.finrank_commonFixed_eq_two_pow_sub
#print axioms AgtXIv.Stabilizer.IndependentSignedPauliGenerators.finrank_commonFixed_eq_two_pow_codeDimension
#print axioms AgtXIv.Stabilizer.IndependentSignedPauliGenerators.generatorsFix_iff_mem_generalRankCommonFixed
#print axioms AgtXIv.Stabilizer.toLin_stabilizerCodeProjectorMatrix
#print axioms AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_isHermitian
#print axioms AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_idempotent
#print axioms AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_posSemidef
#print axioms AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_trace
#print axioms AgtXIv.Stabilizer.stabilizerCodeProjectorMatrix_range_finrank
#print axioms AgtXIv.Stabilizer.IndependentSignedPauliGenerators.generatorsFix_iff_mem_commonFixed
#print axioms AgtXIv.Stabilizer.IndependentSignedPauliGenerators.exists_normalized_generator_fixed_vector
#print axioms AgtXIv.Stabilizer.IndependentSignedPauliGenerators.normalized_fixed_vectors_differ_by_phase
#print axioms AgtXIv.Stabilizer.stabilizerProjectorMatrix_isHermitian
#print axioms AgtXIv.Stabilizer.stabilizerProjectorMatrix_idempotent
#print axioms AgtXIv.Stabilizer.stabilizerProjectorMatrix_posSemidef
#print axioms AgtXIv.Stabilizer.stabilizerProjectorMatrix_trace_one
#print axioms AgtXIv.Stabilizer.stabilizerProjectorMatrix_range_finrank_one
#print axioms AgtXIv.Stabilizer.IndependentSignedPauliGenerators.pureStabilizerDensity

-- Gottesman-to-Veitch bridge: the Clifford witness is constructed from the
-- frame, and the two atom sets and convex hulls are then identified.
#print axioms AgtXIv.Stabilizer.IndependentSignedPauliFrame.exists_semanticClifford_map_standardIndependentZFrame
#print axioms AgtXIv.Stabilizer.pureStabilizerByFrame_iff_byCliffordOrbit
#print axioms AgtXIv.Stabilizer.range_frameAtom_eq_cliffordOrbitAtoms
#print axioms AgtXIv.Stabilizer.stabilizerPolytopeByFrames_eq_byCliffordOrbit
#print axioms AgtXIv.Stabilizer.stabilizerFreeByFrames_iff_mem_cliffordOrbitPolytope

-- Howard--Campbell: all-n feasibility, attained full robustness,
-- faithfulness, and exact deterministic atom-preserving monotonicity.
#print axioms AgtXIv.Stabilizer.traceOneHermitianAffine_le_completeFrame_affineSpan
#print axioms AgtXIv.Stabilizer.traceOne_canonicalStabilizer_feasible
#print axioms AgtXIv.Stabilizer.fullStabilizerRoM_eq_one_iff_free
#print axioms AgtXIv.Stabilizer.StabilizerAtomMap.fullStabilizerRoM_mono
#print axioms AgtXIv.Stabilizer.DensityStabilizerAtomMap.densityFullStabilizerRoM_mono
#print axioms AgtXIv.Stabilizer.densityFullStabilizerRoM_eq_one_iff_mem_cliffordOrbitPolytope
#print axioms AgtXIv.Stabilizer.one_lt_densityFullStabilizerRoM_iff_magicByCliffordOrbit
