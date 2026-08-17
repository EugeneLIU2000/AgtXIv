# Fixed-window reduced RoM is not a stabilizer monotone

## Verdict

The source claim at `pra_version.tex:243-254` is false when the measurement set is held fixed. This finding is independent of the separate proof gap in the projected-polytope V-representation: it neither refutes nor repairs that theorem.

## Exact one-qubit counterexample

Let the fixed measurement window be

\[
\mathcal M=\{X,Z\}.
\]

The projection of the one-qubit stabilizer octahedron onto these two coordinates is the diamond

\[
\operatorname{conv}\{(1,0),(-1,0),(0,1),(0,-1)\}.
\]

Consequently, for a physical Bloch vector with visible coordinates \((x,z)\),

\[
\operatorname{RoM}_{\mathcal M}(\rho)=\max\{1,|x|+|z|\}.
\]

Choose the pure state whose Bloch vector is

\[
(x,y,z)=\left(2^{-1/2},2^{-1/2},0\right).
\]

Its fixed-window value is initially 1. Now apply the Clifford rotation

\[
R_X(\pi/2)=\exp(-i\pi X/4).
\]

It rotates the previously unmeasured \(y\) component into the measured \(z\) coordinate. The visible coordinates become \((2^{-1/2},2^{-1/2})\), up to the irrelevant sign convention for the second component. Therefore

\[
\operatorname{RoM}_{\mathcal M}(R_X\rho R_X^\dagger)=\sqrt 2>1
=\operatorname{RoM}_{\mathcal M}(\rho).
\]

Thus a trace-preserving stabilizer operation can increase the functional when \(\mathcal M\) remains fixed.

## Where the published proof changes the optimization domain

At `pra_version.tex:657-665`, the proof starts with a pseudomixture of the **full state** over pure stabilizer states. Its propagated coefficient norm bounds the output reduced functional, but minimizing those coefficients gives the full-state robustness, not the reduced optimum. The valid conclusion from that argument is

\[
\operatorname{RoM}_{\mathcal M}(\mathcal E(\rho))\leq \operatorname{RoM}(\rho),
\]

which does not imply fixed-window monotonicity.

## What remains valid

- Full-state robustness of magic remains a stabilizer resource monotone.
- The reduced functional remains a lower bound on the full robustness and a sound witness when it exceeds 1.
- Clifford **covariance** remains valid when the state and its measurement window are co-rotated.

Physical intuition: a fixed measurement window is like a telescope pointed in one direction. Freely rotating the object can move a previously hidden component into view, making the silhouette larger without creating a resource.
