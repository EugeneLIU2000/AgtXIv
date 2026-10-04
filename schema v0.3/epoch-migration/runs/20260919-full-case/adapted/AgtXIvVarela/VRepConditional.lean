import AgtXIvVarela.ContextReconstruction

/-!
# Conditional public surface for the projected-polytope V-representation

The exact top-down projection and the normalized maximal signed contexts are
formalized.  The repaired convex-hull equality is kernel-checked conditional
on the two explicit Pauli/stabilizer obligations.  Closing those obligations,
and then proving candidate extremality, are the next mathematical tasks.
-/

namespace AgtXIv.Varela

noncomputable section

variable {n m : ℕ}

/-- Public conditional theorem matching the normalized Varela statement at
the convex-hull level. -/
theorem reducedStabilizerPolytope_vrep_conditional
    (W : MeasurementWindow n m) (H : VRepRepairObligations W) :
    W.ProjectedStabilizerPolytope =
      VRepRepairObligations.contextPolytope W :=
  H.projected_eq_contextPolytope W

end

end AgtXIv.Varela
