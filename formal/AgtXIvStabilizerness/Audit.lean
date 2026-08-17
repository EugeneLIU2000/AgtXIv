import AgtXIvStabilizerness

/-!
# Axiom audit for the Stabilizerness target-local delta

Run this file with `lake env lean Audit.lean`. The reported dependencies must
contain no `sorryAx` or project-defined axiom. The generic affine-span theorem is
a reusable reduction only; it does not discharge the paper-specific relaxed
vertex spanning obligation.
-/

#print axioms AgtXIv.Stabilizerness.abs_signed_sum_add_le
#print axioms AgtXIv.Stabilizerness.exists_sign_attaining_abs_sum
#print axioms AgtXIv.Stabilizerness.max_abs_signed_sum
#print axioms AgtXIv.Stabilizerness.affineSpan_eq_top_of_vectorSpan_eq_top
#print axioms AgtXIv.GraphFoundation.independentFinsets
#print axioms AgtXIv.GraphFoundation.maxWeightIndependent
#print axioms AgtXIv.GraphFoundation.IsPerfect
