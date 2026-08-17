# Source-alignment note

The target paper imports the exact V-representation from this source. The notation is close but not automatically identical: the root defines admissible signs by excluding negative signed Pauli products, while the target rewrites the same structure as an affine binary code with syndromes. The import therefore remains provisional until that equivalence and the signed-representative convention are checked explicitly.

The phrase “maximally independent” in the source is interpreted as inclusion-maximal independent set. It must not be confused with a maximum-cardinality independent set.

The bundle now keeps two different statements on purpose:

- `statement:2602.18939v1:reduced-polytope-vrep` records what the source explicitly claims. Its source proof remains `GAP_FOUND/FAILED`.
- `statement:2602.18939v1:reduced-polytope-vrep-normalized` is an agent-normalized special case with fixed nonidentity Hermitian representatives, distinct phase classes, phase-aware `B_S`, and the repaired coordinate convention. Its separate reconstruction has only a conditional pass.

Source fidelity must never be used to transfer the normalized reconstruction back onto the failed source proof. The export remains unaccepted until the alignment and the reconstruction's declared foundations are closed.
