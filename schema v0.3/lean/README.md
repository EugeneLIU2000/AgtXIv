# Lean evidence for the schema contract ladder v0.3

`EnvironmentAudit.lean` reads actual declarations from the imported Lean
environment. `host/lean.py:audit_projects` builds the existing three-package
case chain and generates separate audit scripts for each project. Its output
contains full types, binder types, non-instance proposition hypotheses,
proof fields carried by explicit structure arguments, axiom dependencies,
and constants occurring in elaborated declaration values.

The audit distinguishes a theorem's accepted proof term from an elaborated
definition. It does not promote either to a faithful statement of the paper.
Definitions still require totality and nondegeneracy evidence for promotion;
premise inhabitation and statement alignment remain explicit unknowns.

Composition requires a constant occurrence in the downstream elaborated term
and matching environment fingerprints. Imports and binder annotations do not
count. This is syntactic composition, not evidence that a premise is logically
necessary. Intermediate declarations not selected for the audit can prevent
the auditor from finding a transitive witness.

`formal/AgtXIvStabilizerness/.../AdmissibleSigns.lean` adds an actual bridge
from the previously formalized free-sign optimization to optimization over an
admissible set. Its `hCollapse` hypothesis says the admissible set equals the
full sign cube. Subsequent original-epoch modules now construct this domain for
actual contexts; the historical bridge's evidence remains conditional as recorded.

`ReducedRoMSemantics.lean` now defines the actual projected-frame normalized
minimum via augmented atoms `(1,a)`, proving feasibility, attainment and floor
one. `ConvexGeneratorInvariance.lean` proves minimum equality from constructed
bidirectional convex atom maps; the particular vertex maps remain missing.
`FiniteRoMDuality.lean` proves general strong duality and attainment from
mathlib Hahn–Banach and instantiates the `(μ,y)` dual for actual `reducedRoM W ρ`.
These three modules have separate successful run evidence in the original
Lean 4.30 epoch; they are also part of the common-environment build below.

`ContextSignIndependence.lean` proves support independence implies absence of
`-I` in the signed context subgroup, the complete real-sign domain, and the
maximum formula. `NoActiveDependencies.lean` proves the required independence
from genuine minimal nonempty scalar-Pauli dependencies and their absence in
commuting contexts. Its endpoints assume only `hNoActive` and `hContext`, not
`hCollapse` or linear independence. The forward direction has successful original
Lean 4.30 evidence; the reverse/parity-code characterization remains separate.

**Common-environment build (2026-09-24).** The 60-module import closure of the
query branch, including the concrete Physlib bridge, perfect-graph weighted
duality and the clique bound and saturation, compiles in one environment
(physlib, Lean v4.33.0, mathlib db584cd6, plus the migrated AgtXIv/Quantumlib
layers); 54 selected declarations (44 theorems, 10 definitions) are audited with
only `propext`, `Classical.choice`, `Quot.sound`. Evidence and the terminal
theorem `AgtXIv.ReducedRoM.perfect_window_closed_form_bound_and_attainment`
(explicit `hNoActive`, `hPerfect` and window fields) are described in
[CANDIDATE_INTEGRATION.md](CANDIDATE_INTEGRATION.md), together with the repairs
and deleted modules. These modules were written by agents, not the automated
proof worker, and source alignment is unreviewed. No generic implication over
arbitrary propositions is substituted for the theorem; `query_declaration` stays
null until a reviewed binding exists. Module header comments that say
"uncompiled" predate this build and are left unchanged so the files keep the
source hashes recorded in the compile bundle.

`LibraryIndex.lean` defines `#agtxiv_library_index`, which writes one row (name,
kind, type, module) per selected constant of a frozen environment for
`host/library.py`; retrieval over the rows is a lexical candidate search, never
a binding.

Physlib remains part of the requested scope. If a sibling `physlib` checkout
with compiled core modules exists, `audit_physlib` reads it without editing
that checkout. `PhyslibPauliFoundation.lean` proves a normalized Pauli-vector
square identity using actual Physlib `vectorMatrix_sq`. This runs in Physlib's
own Lean/mathlib environment. The old three-package chain uses a different
environment, so cross-environment composition is explicitly absent. The
2026-09-24 build above composes the migrated layers with Physlib in one
environment; this historical run did not. Local
untracked PhyslibAlpha work is not silently admitted. Cache freshness is
recorded as not rebuilt in this run; the imported environment itself is
audited.

The separately authorized `frozen/AnticommutingWitness.lean` is an exact copy
of user-authored local work, with its origin, hash, author and license in
`frozen/provenance.json`. It is not claimed as upstream Physlib. The
`host/physlib_branch.py` driver compiles those bytes in a fresh output directory
and then audits the trace-notation bridge, the graph-clique bound and a
nonvacuity instance in `AnticommutingNonvacuity.lean`. The latter constructs a
two-dimensional density matrix and a nonidentity Pauli Z observable.

The relevant paper span is `draft.tex:725–763`: the squared expectations of
an anticommuting Pauli family sum to at most one, giving an absolute-expectation
bound by Cauchy–Schwarz. The new graph theorem retains the involution and
adjacency-to-anticommutation hypotheses. Identifying the paper's Pauli window
with these library objects is now a compiled candidate (`ConcretePhyslibBridge`,
`ReducedRoMPerfectSqrtBound`); its source alignment is unreviewed, and this
branch does not by itself complete the original query chain.

`run_builds=False` does not execute Lean and produces no successful evidence.
Audit receipts and logs are written only in the caller's output directory;
historical `verification-result.json` files remain untouched.
