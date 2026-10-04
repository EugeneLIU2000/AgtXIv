# Universal ceiling: candidate scope

Source: retained arxiv:2607.26154v1 `draft.tex`, source object
`4a84425a4d56efe5b5bee4814a09c99996ab7a6bd279574d567979c248f81c1d`,
lines 797–805 (proposition), 809–889 (proof). This is a reading map,
not an accepted byte-span binding or a declaration-audit result.

The retained research assembly contains the combined proposition as
`claim:candidate:e63f20587f624a1d472f6f83`, with source byte interval
`[54243,54730)`. The audit profile now associates its outer-maximum and
clique-number clauses with this existing node. This locates the extracted
statement; it does not accept its semantic alignment. In particular, the
node also contains the maximum-anticommuting-set equivalence, which the two
selected theorem targets do not explicitly state.

| Source obligation | Candidate declaration | Remaining boundary |
| --- | --- | --- |
| Maximum over solvable measurement sets is sqrt(2n+1) | `AgtXIv.ReducedRoM.sqrt_dimension_isGreatest_solvableWindowCapacities` | Kernel-checked 2026-09-24 (`runs/candidate-compile-20260923`); domain uses finite indexed windows and n>0 |
| Capacity reaches the ceiling iff clique number is 2n+1 | `AgtXIv.ReducedRoM.witnessCapacity_eq_ceiling_iff_cliqueNum` | Kernel-checked 2026-09-24 (`runs/candidate-compile-20260923`); source RoM and window semantics require alignment |
| JW attains the ceiling | `AgtXIv.JordanWigner.window_witnessCapacity` | Kernel-checked 2026-09-24 (`runs/candidate-compile-20260923`); canonical strings use phase-clean representatives |
| A density matrix attains JW capacity | `AgtXIv.JordanWigner.window_exists_attainer` | Kernel-checked 2026-09-24; source alignment unreviewed |

The outer maximum candidate varies both the number of measurements `m` and
the window `W`. Its `IsGreatest` statement includes membership (attainment) and
the upper bound, rather than only an upper bound for a fixed window. It uses
the existing no-active-dependency and perfect-graph predicates.

Domain review remains necessary: MeasurementWindow excludes empty windows,
identity support and repeated phase classes. The JW construction requires n>0.
The proposition's displayed statement does not explicitly spell out that last
restriction. No zero-qubit extension is claimed.

Subsequent candidate work in `PauliCliqueGramFactor.lean` adds explicit targets
for the maximal clique's binary kernel, scalar product in any repetition-free
order, and unique inactive dependency. The retained extracted source node is
`claim:candidate:12649f3695466099141288ec`, at bytes `[58175,58836)`.
These are now included in the audit profile; they are kernel-checked in the
2026-09-24 build but semantically unreviewed. The extracted JW aggregate node
`claim:candidate:d2e9e22029a00ff03ea9e78e` now has an explicit kernel-checked
specialization, `AgtXIv.JordanWigner.window_unique_inactive_dependency`, using
the complete constructed window. Canonical-family and phase-convention source
alignment remains unreviewed; this does not establish the entire aggregate node.

The proof's exact even/odd Gram ranks still lack explicit candidate targets.
The candidate proofs do not discharge cited origins: `sarkar2021sets`,
`brauer1935spinors`, and `ipek2026phasespace` still require their own dependency
and source evidence. These omissions must survive any successful target audit.
