# AgtXIv Varela formalization

This project begins the verification of the compressed V-representation in
Varela et al., *Predicting Magic from Very Few Measurements*.

The current kernel-checked surface contains:

- a normalized finite window of fixed, nonidentity Hermitian Pauli
  representatives with no duplicate phase classes;
- the exact real-linear expectation-coordinate projection;
- the top-down projected stabilizer-polytope semantics;
- inclusion-maximal commuting contexts and phase-aware admissible signs;
- a conditional repaired convex-hull theorem whose two remaining
  Pauli/stabilizer obligations are explicit premises.
- exact finite-graph definitions for maximum weighted independent-set value,
  fractional clique-cover value, and perfectness, together with an explicit
  `WeightedPerfectGraphFoundation` parameter for downstream theorems.

It does **not** yet prove those two premises, candidate extremality, the source
paper's size bound, reduced-RoM monotonicity, or any perfect-graph theorem.
Perfect-graph duality is tracked as an external mathematical foundation.  The
Lean interface makes its statement an explicit theorem parameter; it is not
introduced as a Lean axiom or silently inherited from this project.  A theorem
proved downstream with this parameter is therefore conditional on the external
foundation until its primary-source contract is accepted.
