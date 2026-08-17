# Physical-semantic review

Status: `AGENT_REVIEWED`; no human sign-off is recorded.

## Physical picture

The reduced stabilizer polytope is the shadow of the full stabilizer polytope seen through a finite window of Pauli expectation values. A measured vector outside this shadow certifies nonstabilizerness; a value at or below the boundary may simply mean the window missed the resource.

The frustration graph is only the compatibility skeleton. An edge means two Pauli observables anticommute and cannot both have sharp values. An independent set is therefore a jointly measurable commuting context. Pauli multiplication adds a second layer: even inside one commuting context, joint eigenvalue signs may obey parity checks. A **Pauli-active dependency** is exactly a product relation that lies wholly inside such a context and removes otherwise plausible sign corners.

The set `{XX, ZZ, YY}` makes the distinction visible. The observables commute, but `XX·ZZ·YY=-I`, so only four of eight sign triples are physically admissible. The sign-relaxed cube contains four pseudo-vertices that are not states. Because it is an outer relaxation, its reduced robustness is less than or equal to the exact one.

When all Pauli-active dependencies are absent, each commuting support admits every sign, so the graph skeleton suffices. In the dual, freely choosing signs aligns them with the witness coefficients; the worst context is a maximum-weight independent set. Perfect-graph duality then turns that feasible region into mixtures of clique indicators, leaving only sums over pairwise anticommuting sets.

For a clique `Q`, the anticommuting observables behave like orthogonal Bloch-sphere axes. If `A=sum a_P P` and `sum a_P^2=1`, cross terms cancel and `A^2=I`. Thus the expectation vector on the clique lies in a Euclidean unit ball. The witness uses its l1 norm, whose maximum on that ball is `sqrt(|Q|)`.

Clifford conjugation rotates the measurement window; it does not make one window's ruler longer. Capacity is unchanged, while multiple inequivalent rotations may increase empirical coverage. Capacity, coverage, and the magic of an individual state are distinct quantities.

## Scope cautions

- The target equality requires both a perfect frustration graph and no Pauli-active dependency.
- Perfect means `chi=omega` for every induced subgraph, not only for the full graph.
- Signed Hermitian Pauli representatives are required for expectations and Clifford covariance; phase-free binary vectors alone are insufficient.
- Polynomial-time graph optimization is a rational/finite-precision complexity claim, separate from the exact real-arithmetic identity.
- Figure 2 is empirical coverage evidence, not a measurement of witness capacity or a proof that circuit magic decreases with depth.
