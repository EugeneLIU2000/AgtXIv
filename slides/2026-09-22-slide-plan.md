# Talk Slide Plan — 45 minutes

**Date:** 2026-09-17. For the seminar on or after 2026-09-22.
**Audience:** physics and mathematics peers.
**Design spec:** `docs/superpowers/specs/2026-09-17-schema-v0.2-talk-delivery-design.md` §8.

Twenty-five slides and three live beats. Every figure listed here exists already; nothing below
needs a number that has not been measured.

**Three rules for the whole deck.** One example, never left: arXiv:2607.26154v1. One recurring
figure: the 29-node closure, shown empty on slide 4, filled on slide 18, and as vision backdrop
on slide 24. And no slide names a mechanism the audience has to take on faith — a physicist knows
a frozen sample and a calibration record, so use those, not "content-addressed store".

---

## Part I · Motivation — 0:00 to 9:00, six slides

### 1. Title — 0:00
Title, you, the institute, the date. One line under it, which is the whole talk:

> *A paper states what it proves. It does not state what it depends on, or who checked which part.*

Say nothing else. Ten seconds.

### 2. The paragraph — 0:30
**Job:** put the audience inside one concrete result before any abstraction.

A screenshot of the actual theorem environment from `draft.tex`, rendered. This is the paper's
main closed-form theorem: for a measurement set with no active dependencies and a perfect
frustration graph, the reduced robustness of magic has a closed form over cliques.

Ask the room two questions and do not answer them:

- What does this sentence depend on?
- Who has checked which part of it?

**Do not** say "AI" yet. Do not say "verification". Let the questions sit.

### 3. Six questions, one word — 2:00
**Job:** name the actual problem.

Six rows, each a distinct question about the same sentence:

| | |
|---|---|
| Source fidelity | Is this what the paper says? |
| Mathematical correctness | Does the conclusion follow from the stated assumptions? |
| Formal alignment | Does the formal statement mean the paper's statement? |
| Semantic applicability | Does the formal object represent the physical system? |
| Empirical support | What supports the modelled regime? |
| Computational reproducibility | Can the load-bearing numerics be regenerated? |

Then the point: **every one of these collapses into the single word "verified"** — in a referee
report, in a citation, and most of all in anything a language model says about the paper. They
are not degrees of the same thing. They have different evidence, different checkers, and
different people who are competent to sign them.

### 4. The map, empty — 3:30 · **recurring figure, first appearance**
**Job:** show the scale of the dependency question before claiming anything about it.

The 29-node closure, layers 0 to 8, branch-coloured, **all nodes neutral — no states yet**. Six
foundations at the bottom, one theorem at the top, five branches across.

Say: this is what that one sentence rests on, inside one paper. Six of these foundations come
from three different fields — quantum information, graph theory, optimization. Nobody assembled
this by reading; it was assembled from records, and we will come back to it twice.

**Do not** colour anything yet. The empty version is the honest starting state.

### 5. Related work, against this example — 5:00
**Job:** position without dismissing, using the example as the ruler.

Four rows, each answering "what would this project do with slide 2's sentence?":

| | Would do | Cannot |
|---|---|---|
| **mathlib, physlib / HepLean, Lean-QIT** | state the theorem formally, and check it | someone must hand-write it, and nothing ties it to these bytes |
| **ResearchRabbit, Connected Papers** | show this paper's neighbours | say what the theorem depends on |
| **Paper2Agent** | wrap the paper's methods as tested, callable tools — the best engineering reference here | **needs a paper with a public codebase; this paper has none** |
| **Agentic Publication Protocol** | package the release for agents | no verification semantics |

Be generous about Paper2Agent — it is genuinely good and this deck borrows from it. The
differentiator is theirs, not ours: they say they need a codebase. A theory paper's main theorem
has none. Their unit is an executable method; ours is a claim with its conditions.

### 6. The gap, in one line — 7:30
> **Claim-level. Byte-anchored. Verification-aware.** Nothing in the row above is all three.

Then: and the hard part is not building it, it is not lying while you build it. Which is the next
six minutes.

---

## Part II · The idea — 9:00 to 14:00, three slides

### 7. A prompt is a request; an interface is a refusal — 9:00
**Job:** the central intellectual claim of the talk.

If agents are going to extract, compare and formalize claims, the epistemic constraints cannot
live in the instructions. An instruction is advice. A contract that **cannot represent** the
dishonest answer is a different kind of object.

Concretely: `additionalProperties: false`. A model cannot add a field nobody agreed to. That is
not fussiness about JSON — it is the mechanism.

### 8. Three structural refusals — 10:30
Three rows, each a thing the contract makes impossible rather than discouraged:

1. **A producer cannot review its own output.** And — the sharp version, borrowed from
   Paper2Agent — *changing a role prompt inside one agent context does not create a second
   reviewer.*
2. **A backtranslator cannot see the source.** Not "should not": its context does not contain it.
3. **A fixed program has no scientific discretion.** The thing that runs Lean cannot decide what
   the result means.

### 9. Delivery is not acceptance — 12:30
**Job:** the distinction the whole system turns on.

A task can *correctly* deliver "cannot prove this; lemma L is missing." So the outcome vocabulary
has no `SUCCESS`:

`DELIVERED` · `BLOCKED` · `FAILED` · `DEFERRED`

And the run states: `NOT_STARTED` · `FAILED` · `CANCELLED` · `OUTPUT_REJECTED` · `STAGED` ·
`COMMITTED` · `UNKNOWN`. `COMMITTED` means a candidate transaction completed. It is not a claim
about truth.

Quote, because it says it better than a paragraph: *a marker that work ended is not a record that
it passed.*

---

## Part III · What we got wrong — 14:00 to 20:00, four slides

> This is the section that buys credibility for everything after it. Do not rush it and do not
> apologise through it. The finding is interesting on its own terms.

### 10. We built the nine-agent version first — 14:00
`schema v0.1`: nine task templates, 23 operations, eight agent modules, each with a role
document, an interface, conformance fixtures, a JSON Schema and an offline checker. It all
type-checks. 368 tests pass.

### 11. Then we audited it — 15:00
**Job:** the three findings, plainly.

Six surveyor agents read the repository and ran against it; five skeptics tried to refute them.

1. **The five-round pipeline was five Python functions.** A model read the paper once,
   interactively, and hand-wrote a 440 KB seed file. A script then sliced that seed into five
   "rounds". Re-run into a scratch directory it reproduced every round file **byte-identically in
   18.2 seconds** — no model, no network.
2. **The dependency stage was a regular expression.** Its own manifest asserts
   `external_model_calls: 0`.
3. **The third operation could not legally be issued at all.** Formalization requires a packet;
   the packet's only producer requires four record families, one of which has no producing
   operation anywhere.

### 12. Nothing was hidden. Nothing was forbidden either — 17:00
**Job:** the actual lesson, and it is not "we were sloppy".

Every one of those boundaries is written down somewhere in the repository. The failure is
narrower and more interesting: **the contract permitted all three.** A folder assembled from a
hand-written seed satisfied the Task schema. A regex scan satisfied `dependency.search`.

A contract that documents its limits is not the same as a contract that enforces them.

### 13. So the contract changed — 18:30
`schema v0.2`: four operations, three agent modules, five schemas. Nine agents down to four
operations, and one new first principle:

> **Every executed research task calls a model. Replaying a manual seed, copying an old result,
> or scanning citations alone does not constitute a new Agent execution.**

Each of the three findings is now definitionally impossible rather than discouraged. That is the
only kind of fix that survives contact with a deadline.

---

## Part IV · v0.2 and the demonstration — 20:00 to 31:00, five slides and three live beats

### 14. The four operations — 20:00
`paper.extract` → `dependency.search` → `autoformalization.lamport` → `autoformalization.lean`.

Two things to state: the last two run on **one selected claim**, never the whole paper. And
`Task` → `Output` → `run` is the whole interface — one bounded work order, one JSON object back,
one host receipt.

### 15. Who owns what — 21:00
**Job:** the mechanical/judgement line, because everything else follows from it.

| The host, mechanically | The model, as judgement |
|---|---|
| resolve a marker to a byte range and hash it | choose which passage is the claim |
| build the paper's macro table | write the statement out with notation unified |
| run the kernel, capture the exit code | decide what to attempt formalizing |
| record who executed what, and when | — |

The model is never asked to compute a hash, and the host is never asked what a theorem means.

### 16. ▶ LIVE — a work order and a refusal — 22:00
**Beat one.** In a terminal:

- Show a `Task`: the operation, the exact inputs with hashes, the purpose, the limits.
- Run the source resolution. Two markers resolve to byte ranges in `draft.tex`:
  `[18686, 19275)` for the main theorem, `[45972, 46573)` for the lemma that blocks it.
- **Then the third one refuses**: `END_AMBIGUOUS` — `\end{theorem}` occurs more than once after
  the start marker. It will not guess.

That refusal is the demo. A system that resolves two and refuses one has told you something a
system that resolves three cannot.

**Start the Lean build now**, in a second pane, and say you are starting it. 84 seconds.

### 17. ▶ LIVE — the macro table, and the kernel — 24:00
**Beat two.** While Lean runs:

`\Mcal` means `\mathcal M` in this paper — and it is defined on line 8 of `draft.tex`, not in the
preamble it inputs. 42 macros recovered mechanically; 45 control sequences reported unresolved
rather than guessed. Worth one sentence: our first version scanned only the preamble and reported
the paper's own notation as unresolved. That is how we found the bug.

Then the build lands: exit 0, 8408 jobs, axioms within the allow-list, no `sorry`.

### 18. The map, filled — 25:30 · **recurring figure, second appearance**
**Job:** the climax. Same figure as slide 4, now with states.

- **Three rungs green** — kernel-checked in Lean. And they sit in the *mathematics* branches
  (`mwis-definition`, `perfect-graph-definition`, `sign-alignment-identity`) while feeding a
  quantum-information conclusion. Cross-field reuse, visible without being asserted.
- **The theorem at the top is not green.** It is blocked.
- **Two of the six foundations are red**, and the figure makes it obvious they are load-bearing.

### 19. What blocks it — 27:00
**Job:** the sentence the whole talk exists to deliver.

Click through to the blockers. One is another paper's proof gap. The other:

> `root:perfect-graph-weighted-duality` — Chvátal 1975.
> `source_fidelity: UNCHECKED` · `acceptance_basis: DECLARED_BACKGROUND` ·
> `formalization_mode: EXPLICIT_THEOREM_PARAMETER`

Assumed in Lean. Not proved. And the system says so rather than hiding it.

> **The bottleneck to verifying a 2026 quantum-information paper is a 1970s graph-theory theorem
> that has never been frozen from its primary source and aligned to the conventions in use.**

Pause here. This is the slide they will remember.

### 20. ▶ LIVE — the gate says no — 29:00
**Beat three.** Run the phase gate. It exits non-zero:

```
GATE FAILED — 1 problem(s):
  [PHASE_NOT_REACHED] extract: no COMMITTED run for paper.extract
```

Explain why this is the right answer: the ledger is internally sound — every blob re-hashed,
every consumed item traced to its producing run — and it still refuses to call the phase reached,
because the thing that would reach it has not happened. Seven per-run check layers do not compose
into a chain: a run can pass all seven and stand on a predecessor that never committed.

Then, briefly: lineage rejects eight ways of lying about provenance, and the one worth naming is
that **the ledger wins over the receipt** — a receipt claiming a different producer than the
ledger records is rejected, not believed.

---

## Part V · Cost — 31:00 to 34:00, two slides

### 21. What one paper costs — 31:00
**Job:** turn the whole proposal into arithmetic.

Two scopes, kept apart, because the Lamport/Lean branch runs on one claim by design:

| Scope | Calls | Input | Output | Per paper |
|---|---|---|---|---|
| **A** — extract, dependency on all 25 claims, formalize **one** | 66 | 1.17 M | 146 k | **≈ $9.5** |
| **B** — the same, formalizing **all 25** | 210 | 3.93 M | 770 k | **≈ $39** |

The 25 is measured, not assumed. Say the two caveats out loud: token counts are a
four-characters-per-token approximation, and the rate card was looked up, not remembered.

### 22. The useful number is not the price — 32:30
**82% of scope A's input is the same 14.5k-token specification prefix, sent 66 times.** The
largest lever is therefore free — cache it, nothing traded. That comes *before* any decision
about where to spend reasoning effort.

Then effort where the difficulty is: low for extraction, medium for dependency comparison, high
for structuring a proof, **highest for writing Lean that must compile** — which in scope B is
over half the bill, and whose *iteration count*, not per-call price, decides the total.

And the honest half: **an effort allocation is a claim about where the difficulty lies, and it is
testable.** If low effort on extraction holds quality, the task was easier than the architecture
assumed — and that is a result, not a saving.

---

## Part VI · Vision — 34:00 to 40:00, four slides

> One standing line, on every slide in this part: *the distance is large, none of this is a
> roadmap item with a date, and each needs a community rather than a project.* Say it once
> properly and let the footer carry it after that.

### 23. Reuse — 34:00
Which already-verified upstream declarations extend to a new theorem. Two consequences beyond
convenience: the six-axis separation **forbids** a Lean theorem standing in for a physical
statement, so the physical content has to be written down; and the unit of formalization changes
— what a human reads is a dependency chain, with Lean declarations as evidence attached to its
rungs, not thousands of lines nobody navigates.

**They provide the terrain; this provides the map.** What those libraries lack is not tooling but
an answer to which theorem to prove next and what proving it unlocks.

**Distance:** no automated upstream search exists. Condition matching is a human judgement. The
semantic contract has no producer.

### 24. Knowledge increment — 35:30 · **recurring figure, third appearance**
The closure again, dimmed, with the inherited roots separated from this paper's new claims. What
does a new theorem actually add, against a fixed baseline, without claiming world-first?

**Distance:** the delta checker only requires the comparison set and the targets to intersect. No
comparison has been run on a real pair. "Contribution" currently means structural difference
within one frozen batch — which is not scientific significance. And this operation is not in
v0.2's startup path at all.

### 25. Knowledge discovery — 37:00
Three questions, and they are not equally far away. Which theorems matter — computable from the
graph today, out-degree gives `frustration-graph` 10 and `gottesman-stabilizer-formalism` 9. By
what route they were obtained — recoverable, because multi-premise inference is an explicit node
rather than a lost hyperedge. **Whether the pattern of connections can be learned to propose new
theorems worth proving — an open research question, not a roadmap item.**

Its precondition is the whole point: learning from candidate edges is learning from noise. Which
is why the graph stays derived and never becomes a second source of truth — **the trustworthiness
of a connection cannot exceed that of the records it connects.**

### 26. Structured transparency — 38:30
September 2026: a proof reported from roughly 10,000 agents over 88 hours on an internal model,
followed by a credit dispute. State the parties' positions as positions, not as findings.

The structural point, not a slogan: **if checking a result requires owning comparable compute,
verification becomes a function of capital.** Slide 21 is this argument in arithmetic — ten
dollars a paper against ten thousand agents for eighty-eight hours.

And what makes it concrete rather than rhetorical: the whole protocol is 14.5k tokens, so any
model with an ordinary context window can receive it and be held to it by the same checker. Four
providers render a real request today, one of them a model on a laptop. **A student with a local
model produces a record checkable by exactly the same rules.** Whether it is as good is then an
empirical question — and the contract requires that any difference be visible rather than
concealed.

**Distance:** no model has run under these contracts yet. And nothing here constrains anyone who
declines to adopt them; that is a norms problem, not a technical one.

---

## Part VII · Discussion — 40:00 to 45:00, one slide

### 27. What I want from you — 40:00
Six questions, and mean them:

1. For the blocked Chvátal foundation — what would you accept as "frozen from the primary source
   and aligned to these conventions"? Who may sign that?
2. Is formal alignment a judgement one named expert can sign, or does it need two?
3. What is the right baseline for a contribution delta in your subfield?
4. Which classical results in your area are, like this one, universally used as background and
   never checked against their source?
5. If the same frozen task gives materially different extractions under two models, which
   difference is a defect and which is legitimate research judgement — and who decides?
6. Would you attach a chain like this to a submission? What would have to be true first?

---

## Staging

**Three live beats, and a fallback for each.** Slide 16 (source resolution, ~5 s), slide 17
(macro table, instant; Lean build started at 16 and landing at 17 — 84 s, or 38 s for the audit
step alone), slide 20 (phase gate, instant). Only the Lean build has real duration, and it runs
under narration by design.

If a live step fails, show the stored receipt **and say it is stored**. The entire talk is about
that distinction; pretending otherwise on stage would undo it.

**Two numbers to re-check the morning of the talk:** the rate card on slide 21, and whether a
real `COMMITTED` run exists. If one does, slide 20 becomes a pass rather than a refusal — rewrite
that slide, do not narrate around it.

## Deck mechanics

The existing beamer deck at `slides/agtxiv_mathcontract_demo.tex` already carries the palette,
the metropolis theme and the TikZ setup. Reuse it. The closure figure has a generator:
`schema v0.2/host_probe/evidence/closure.json` holds the nodes, layers, branches and states, and
`blocked-theorem.html` renders it — export the SVG from there for slides 4, 18 and 24 rather than
redrawing it three times.
