# Query-stage V1 result

## Part A: whole-paper baseline

Use the frozen whole-paper overview at [`understanding/overview.md`](../../understanding/overview.md), snapshot `paper-understanding:2608.22855v1:whole-paper-baseline`. It is not rewritten here.

## Part B: bounded query assessment

**Target and lineage.** The V1 package pins `scientific-claim.json`, its four frozen source anchors, normative `math-claim-ir.json`, and the revision/hash-pinned bridge and assessment. It follows executions `b1767b8c5f28` and `f145cc7cd887` and addresses independent review `39b13632357a`.

**Bounded chain.** Source assumptions and imported charged-AdS/junction formalism $\rightarrow$ unresolved junction-to-Friedmann reduction $\rightarrow$ displayed reduced equation as a conditional input $\rightarrow$ exact $\Lambda_4=0$ solution $\rightarrow$ intrinsic turning polynomial and endpoint analysis. The intrinsic turning polynomial is included; side-specific horizon roots and horizon ordering remain excluded.

**Separated outcomes.** All exact symbolic assertions pass, including the first-integral identity, turning roots, second-derivative signs, $x_{\min}>0$ for $0<\beta<1$, nonconstancy for $\beta>0$, the singular $\rho=0$ endpoint, and the static $\rho=1$ endpoint. The conditional reduced-equation proposition is `VERIFIED_WITH_ENDPOINT_QUALIFICATION`: under the additional Agent-side conditions $D>0$, $E>0$, and $0<\rho<1$, it gives a positive nonconstant periodic bounce. The literal source proposition uses $\rho\leq1$ and remains `UNKNOWN`/`NOT_CHECKED`; it is not silently replaced by the Agent-derived proposition. Scientific acceptance is exactly `NOT_REVIEWED`.

**Applicability and evidence.** Assumption/object matching is `PARTIAL` because the junction-to-Friedmann reduction, its approximation regime, and the relation between source orderings and $D,E>0$ are unresolved. Evidence completeness is `PARTIAL`. Formal proof-kernel alignment is `NOT_CHECKED`.

**First unresolved frontier and blockers.** `blocker:2608.22855v1:junction-reduction-approximation-unresolved` blocks unconditional source-level projection. `blocker:2608.22855v1:phase-scan-code-absent` blocks reproduction of the excluded outside-horizon region.

**Validation scope.** `validate_run.py` performs the V1 schema, exact-reference, RFC 6901 pointer, canonical-hash, completeness, one-to-one assessment, non-promotion, manifest, and determinism checks. `tools/validate_pilot.py` supplies legacy repository-level parse and structural checks only; it is not V1 bridge validation.

**Non-implications.** The result does not verify the physical model reduction, horizon avoidance, the phase diagram, perturbative or nonlinear stability, a full five-dimensional solution, nonzero-$\Lambda_4$ regimes, the string-cloud extension, or scientific acceptance.
