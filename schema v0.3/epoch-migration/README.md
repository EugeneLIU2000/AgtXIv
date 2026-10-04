# Common Lean epoch experiment

This directory belongs to the schema contract ladder v0.3. It records an
isolated compatibility experiment, not an in-place package upgrade.

Run the scoped experiment in a fresh output directory:

```sh
python3 'schema v0.3/host/epoch_migration.py' --output '/absolute/path/to/new-run'
```

The driver copies the current graph foundation, free-sign lemmas and
admissible-sign bridge. The `originals` directory preserves exact source
bytes; `adapted` changes only imports to point at isolated modules and to
load the Ring tactic explicitly. Mathematical bodies are checked for byte-line
equality after removing import lines. No existing formal package or Physlib
checkout is edited, and no packages or toolchains are installed or updated.

Each module is compiled using the sibling Physlib checkout's own Lean/mathlib
environment, with generated objects kept inside the new run. A final theorem
then applies the admissible-sign result to Physlib quantum expectation values
in the same environment. Its domain-collapse premise stays explicit.

The output records source hashes, adaptations, actual compile receipts,
declaration types, premise lists and proof-term composition. The complete
original case's import closure is catalogued separately so that a successful
three-module experiment cannot be mistaken for a complete migration. In this
frozen 2026-09-19 case that closure contains 82 local modules, including 20 from Quantumlib;
the selected experiment does not compile that whole closure.

The subsequent whole-case compatibility attempt is available with
`--full-case`. It freezes the entire local import closure, preserves original
module names and package implicit-variable settings, and compiles in
dependency order. Per-module receipts are retained and `progress.json` is a
mutable checkpoint for this active run. It stops at the first compilation
failure and emits `migration-evidence.json`; it does not edit theorem bodies
or automatically repair errors. Successful compilation of all local modules
still requires a separate declaration/axiom audit before any proof evidence
can be transferred to the new environment.

The source-specific sign-collapse theorem, reduced robustness semantics,
perfect-graph duality proof and complete query composition remain distinct
mathematical tasks after toolchain compatibility is established.

The 2026-09-19 full-case attempt compiled 16 of the 82 local modules, then
stopped at `Quantumlib.Data.Gate.Pauli.Defs`. In the new mathlib version,
`MonoidAlgebra` is a structure with a `coeff` field rather than a definitional
alias for `Finsupp`; the old Pauli-map definitions and downstream coefficient
proofs therefore require a representation-aware port. This is distinct from
the successful selected-module experiment above.

The first failed checkpoint is retained as `migration-evidence.json`. An
explicit, hash-bound adaptation replaced two simplifier base cases with `rfl`
in the frozen `PowBitVec` copy, without changing theorem statements. The next
immutable checkpoint is `migration-checkpoint-18.json`, and
`query-gap-report.json` contains actual audited types for the available partial
results and the exact unresolved premises. No final-query declaration was
found in the case sources, including no theorem of the final closed form with
all missing mathematics merely exposed as premises.

`resume_full_case_migration` accepts only recorded changes to the currently
failed module and verifies source and prior object hashes before continuing.
It preserves failed receipts and writes separate retry receipts. A completed
resumed run writes `migration-completed.json`; `audit_full_case_migration`
then verifies the frozen/adapted source hash chain and current object hashes
before auditing declarations. Its target inventory is frozen with the source
closure, so later project additions cannot silently enlarge the audit scope.

A later explicit representation-port phase passed all three Pauli modules
(`Defs`, `Notation`, `Lemmas`) and reached 24 compiled modules. Patches 002–004
use `MonoidAlgebra.coeff`, its `single` constructor, and its induction principle.
The original normalization/support conclusions remain present; theorem syntax
that exposed the old definitional `Finsupp` representation is transported to
the corresponding coefficient operations. Earlier objects from `Notation`
onward were archived and recompiled before the new evidence was recorded.

`representation-audit-2/representation-evidence.json` records successful
kernel checks of the six ported theorems and three explicit coefficient-formula
identities from `RepresentationCompatibility.lean`. The first audit failed
because its generated imports were misplaced; its receipt remains in
`representation-audit-1`. Notation macros compile, but their expansions remain
unelaborated because this case's source closure does not use them. No successful
module compilation is described as checking those unused expansions.

The migration then stopped at the scalar-unitary proof in
`Quantumlib.ForMathlib.Data.Matrix.Unitary`. The active continuation uses a
recorded, statement-preserving rewrite adaptation; `progress.json` gives the
current checkpoint. The initial 16-module and later 24-module summaries are
historical checkpoints, not final full-case results.

The original 82-module closure subsequently compiled in full at Physlib's
Lean 4.33.0 / mathlib `db584cd6d46c92f209a44c0f1c829460d327499d` epoch.
`runs/20260919-full-case/migration-completed.json` preserves that result;
`full-case-audit.json` records the successful common-environment audit of
74 explicitly selected declarations: 61 theorems, 11 definitions, and two
inductive types. All audited declarations use only the allowed axioms, and
44 direct proof-term dependencies connect audited declarations. The audit
captures actual types, hypotheses, and local module companion hashes.

`completion-report.json` separates the final 82 compiled modules from all
107 preserved compilation receipts (87 successes and 20 failures). Five old
successful objects were invalidated and rebuilt after representation edits.
There are 21 recorded adaptation steps affecting 19 modules. Coefficient-form
compatibility has its separate nine-theorem audit; unused notation expansion
remains explicitly unelaborated. These counts are not paper-claim coverage.

The migration and audit retain unreviewed source alignment and do not prove
the paper's final query. Existing conditional graph-duality, V-representation,
and sign-collapse premises remain explicit in the audited types. Later
original-epoch modules and new concrete Physlib bridges belong to separate
extension scopes and are not counted in these original 82 modules.

The subsequent `runs/20260919-concrete-physlib-bridge/bridge-evidence.json`
records a successful separately counted extension. `ConcretePhyslibBridge.lean`
preserves the actual density matrix in both conversion directions, proves
trace/expectation equality, and proves that the concrete noncommutation graph
is exactly the matrix-anticommutation graph. Window involutions supply the
Hermitian/involution requirements of the frozen local Alpha theorem, so the
concrete L2/L1/clique-number bounds need only an actual clique hypothesis in
addition to the window and density matrix. A nonidentity one-qubit Z window
and an actual trace-one density matrix provide a concrete nonvacuity witness.

That extension adds 20 declarations (15 theorems and five definitions). Its
audit includes their actual dependencies: 34 declarations total, 64 direct
term-dependency witnesses, and no forbidden axioms. It compiles two extension
modules while reusing hash-verified original-case objects and the frozen
user-authored Alpha object. The first failed bridge attempt remains alongside
the successful second attempt. `source-alignment-note.json` anchors the
measurement domain, graph definition and uncertainty bound to the paper;
alignment remains unreviewed, and the RoM closed-form connection remains open.

`host/extension_migration.py` migrates later, already compiled original-epoch
case modules in separately frozen layers. It discovers their real imports,
requires a successful original receipt matching each source hash, preserves
original and adapted copies, and reuses the original 82 modules and concrete
Physlib bridge as read-only dependencies. Later layers additionally verify
the ordered predecessor layers and their object hashes. Import-only splitting
of combined audit foundations preserves every non-import source line.

The first layer, `runs/20260919-additional-case-modules`, compiled 12 modules
from reduced-RoM semantics through signed-frame completion, mutual convex
generator constructions, finite normalized duality, and clique-cover
attainment. Five recorded proof-routing adaptations preserve theorem
statements and add no assumptions. Its 17 compilation receipts include all
five failures and 12 successes. `extension-audit.json` records 210 actual
declarations (158 theorems, 49 definitions, three inductive types), 434 direct
term dependencies, and no forbidden axioms. The audit's selected scope joins
176 predecessor targets with 34 concrete Physlib bridge targets; these are
declaration counts, not paper-claim coverage. `completion-report.json` retains
selected endpoint types, explicit hypotheses and structure proof fields.

This layer constructs candidate physicality and atom refinement under the
explicit `NoActiveDependencies` hypothesis and uses actual density-matrix
semantics for the reduced robustness. Source alignment remains unreviewed.
The existing concrete single-Z-window nonvacuity theorem does not yet assert
that additional hypothesis. Subsequent graph-dual and bound modules belong
to their own appended layers and are not included in the initial 12 count.

The next layer, `runs/20260919-graph-dual-extension`, separately compiled
`WeightedCliqueCoverWeakDuality` and `ReducedRoMGraphDual`. It replaces the
latter's combined foundation import with the original four mathematical
modules, preserving every non-import line before two further recorded
proof-routing adaptations. All four compilation receipts remain: two
successes and two failures. The cumulative audit contains 232 actual
declarations (176 theorems, 53 definitions, three inductive types), 510 direct
term dependencies, and no forbidden axioms. Of the 22 newly included target
names, 21 are new declarations in these two modules and one is an existing
support definition newly included in this audit's target scope.

The actual `reducedRoM_isGreatest_graph_dual`, `reducedRoM_eq_graph_dual_sup`,
and `exists_graph_dual_optimizer` endpoints have only the explicit
`NoActiveDependencies` proposition in addition to the window and density
matrix structures. Feasibility, the convex generator correspondence,
normalized finite duality and sign elimination occur in their compiled
dependency chain. This is an attained graph-dual characterization, not yet
the paper's full closed-form query. The graph definitions used here and in
the concrete Physlib bridge have matching adjacency source; an explicit
cross-module equality theorem is outside this migration layer.

`runs/20260919-graph-bounds-perfect-replication` adds five independently
counted modules: `GraphDualBounds`, `PerfectGraphColorClass`,
`PerfectGraphTransport`, `PerfectGraphTrueTwin`, and
`PerfectGraphReplication`. All five compiled, with two failed receipts retained
before local proof-routing fixes. The bound module's combined foundation
import was split into its three already migrated mathematical modules;
the other source imports retain their original dependency order. The only
subsequent adaptations concern finite-supremum definitional unfolding and
the new `Std.Symm` graph interface. Theorem statements and hypotheses are
unchanged.

Its cumulative actual environment audit contains 302 declarations: 230
theorems, 69 definitions and three inductive types, with 662 direct term
dependencies and no forbidden axioms. The five modules themselves contribute
60 new declarations; ten older supporting declarations newly enter this
audit's selected target scope. These distinct counts are recorded with
actual endpoint types in `completion-report.json`. The reduced-RoM sandwich
retains `NoActiveDependencies`; the full hereditary `trueTwin_isPerfect`
endpoint retains `IsPerfect G`. Later clique-fibre, transversal, weak-perfect
and weighted-duality work is outside this layer. Source alignment remains
unreviewed and the complete paper query remains open.
