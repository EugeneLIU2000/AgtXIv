# Talk Slide Plan — 45 minutes

**Date:** 2026-09-17. For the seminar on or after 2026-09-22.
**Audience:** physics and mathematics peers.
**Design spec:** `docs/superpowers/specs/2026-09-17-schema-v0.2-talk-delivery-design.md` §8.

Thirty-one slides and four live beats. Every figure listed here exists already; nothing below
needs a number that has not been measured.

**Borrowed material.** Part I.5 leans on Tobias Osborne, *Large Language Models: A Physicist's
Perspective* (UCL, 2026, 1:27:23). Cite him on the slide. **Restate his points in your own
figures — his slides are his.** The value is not only the argument: he is a quantum information
theorist, Mike Nielsen was his PhD advisor, and the seminar host said he went looking for anyone
using these tools seriously and found Osborne wrestling with the same verification problem. With
this audience that provenance carries more than a fresh argument would.

**Three rules for the whole deck.** One example, never left: arXiv:2607.26154v1. One recurring
figure: the 29-node closure, shown empty on slide 4, filled on slide 22, and as vision backdrop
on slide 28. And no slide names a mechanism the audience has to take on faith — a physicist knows
a frozen sample and a calibration record, so use those, not "content-addressed store".

---

## Part I · Motivation — 0:00 to 7:00, six slides

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

### 3. Six questions, one word — 1:40
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

### 4. The map, empty — 3:00 · **recurring figure, first appearance**
**Job:** show the scale of the dependency question before claiming anything about it.

The 29-node closure, layers 0 to 8, branch-coloured, **all nodes neutral — no states yet**. Six
foundations at the bottom, one theorem at the top, five branches across.

Say: this is what that one sentence rests on, inside one paper. Six of these foundations come
from three different fields — quantum information, graph theory, optimization. Nobody assembled
this by reading; it was assembled from records, and we will come back to it twice.

**Do not** colour anything yet. The empty version is the honest starting state.

### 5. Related work, against this example — 4:20
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

### 6. The gap, in one line — 6:00
> **Claim-level. Byte-anchored. Verification-aware.** Nothing in the row above is all three.

Then: and the hard part is not building it, it is not lying while you build it. Which is the next
six minutes.

---

## Part I.5 · The query is the problem — 7:00 to 12:00, four slides

> This block is the evidence for Part II's thesis, so it has to come first. It leans on Tobias
> Osborne's *Large Language Models: A Physicist's Perspective* (UCL, 2026) — cite him by name on
> the slide. **Restate his points in your own figures; do not reproduce his slides**, they are his.
> He is a quantum information theorist, Mike Nielsen was his PhD advisor, and the seminar host
> noted he was wrestling with the same verification problem. For this audience that provenance
> does more work than any argument of ours.

### 7. Same input, different output — and that is the mechanism — 7:00
**Job:** establish that non-determinism is structural, not a defect to be fixed by a better model.

Three claims, all Osborne's, and all checkable by anyone in the room:

- From outside the API an LLM is a function `f : String → String`, **stateless** — nothing
  carries between calls.
- It does not output text. **It outputs a distribution over tokens**, and the text is sampled
  from it.
- One call is a single forward pass through a **frozen** network. Nothing is written back.

Then the page that lands hardest here, because it is their own subject:

$$P(\text{token}_i) = \frac{e^{l_i/T}}{\sum_j e^{l_j/T}}$$

A Boltzmann distribution over tokens, with the logits in the role of negative energy and `T` the
temperature. `T → 0` is the ground state. Osborne labels it exactly that way, for exactly this
audience.

**So "why did two calls answer differently?" is the wrong question.** Sampling is the mechanism.
The right question is what the query left undetermined — because that is what the sampling ranges
over.

### 8. ▶ "How should I understand this paper?" × three calls — 8:30
**Job:** show three defensible answers to one query, and let the room notice none is wrong.

Same frozen paper, same query, three calls — and, because the adapter is provider-neutral, ideally
three *different vendors*. Show the three answers side by side. They will differ in kind, not in
quality:

| | What it gives you | Not wrong, because |
|---|---|---|
| Call 1 | the physics narrative — magic states, why robustness matters | the query did not ask for structure |
| Call 2 | the theorem inventory — definitions, lemmas, the closed form | the query did not ask for a story |
| Call 3 | the dependency structure — what rests on what | the query did not ask for either |

**The query never said what "understand" means.** It did not say for whom, at what depth, to
what end, or what may be left out. Three samples from an underdetermined question are three
samples from an underdetermined question.

Then the line that turns this from an observation into a requirement:

> **The receipts show all three calls received byte-identical input.** So the difference is not in
> the paper, and it is not in the prompt. It is in what the question failed to fix.

**Honesty gate on this slide.** If a credential exists by the talk, this is real output with
three receipts and it is the strongest slide in Part I. If it does not, show the structure and say
plainly that it has not been run — do not stage it with invented answers. This demonstration is
also `X-07` in the pending list and the executable form of v0.2's Principle 2, so running it is a
contract obligation and not a presentational nicety.

### 9. "Please formalize this proof" — six things it did not say — 10:00
**Job:** the same defect, on an instruction that sounds completely specific.

This one is sharper, because nobody hears it as vague:

1. **Which claim?** This paper has 25.
2. **In which system, at which commit?** Lean 4 — but `mathlib` at which revision, with which
   packages, under which axioms?
3. **The statement, or the proof?** Pinning the statement formally and proving it are different
   jobs with different costs.
4. **Under whose definitions?**
5. **Assumed, or proved?** A formalization may take a lemma as a hypothesis rather than
   establishing it — and those two look identical in a file that compiles.
6. **And what counts as done?** Compiles? No `sorry`? Axioms audited? Meaning aligned with the
   source?

Point 4 is Osborne's, and quote him, because it comes from someone who did it: he handed
master's-level unpublished mathematics — not in any training set — to a coding agent, and it
formalized it in Lean essentially unattended. Asked whether he still had to check it afterwards:

> **The fragile point is the definitions, not the proof.** The proof is formally correct in Lean.
> But the semantics of the definition may be wrong. Is it proving something about matrices, or did
> it define "matrix" to be a natural number? **A human is required here.**

Say the consequence out loud: **a green build is compatible with having proved the wrong thing.**
That is not a model failure. Nothing in "please formalize this proof" asked for the definitions to
be checked.

### 10. The same six, as fields that must be filled first — 11:00
**Job:** the necessity and the novelty, in one table. This is the load-bearing slide of Part I.

Same six rows, now with what resolves each — and every one of these is a required field, so the
work order **cannot be issued** while any of them is open:

| It did not say | What fixes it |
|---|---|
| which claim | `target_ids` — exactly one committed `math_claim`, and a paper or a proof plan cannot substitute |
| which system | `module` plus a host-registered environment descriptor: toolchain, package identities, axiom policy |
| statement or proof | two operations, `autoformalization.lamport` then `autoformalization.lean`, and Lean must consume a **previously committed** Lamport artifact |
| whose definitions | `definitions` references, plus `normalization.relation_to_source` declaring how far the wording moved from the source |
| assumed or proved | `formalization_mode` — `EXPLICIT_THEOREM_PARAMETER` is the field that says "assumed, not proved" |
| what counts as done | seven check layers, each recorded once, `NOT_RUN` permitted — generation, source resolution, Lamport structure, actual build, and alignment reported **separately** |

Then the claim of novelty, which is narrower and more defensible than "we prompt better":

> **The contribution is not a better answer to an ambiguous question. It is that the question
> cannot be asked until it is unambiguous.** Six open decisions become six required fields, and a
> task with any of them missing is `NOT_STARTED` with a reason — not a plausible answer.

And the bridge into Part II, which is also Osborne's, and is the single most useful sentence in
his talk for this project:

> Being in the context window is not the same as being in effect. Context rot is a **soft
> failure** — no error, no warning. So *"I told it explicitly"* is never evidence that it complied.

Which is why the constraint cannot be an instruction. That is slide 11.

---

## Part II · The idea — 12:00 to 16:00, three slides

### 11. A prompt is a request; an interface is a refusal — 12:00
**Job:** the central intellectual claim of the talk.

If agents are going to extract, compare and formalize claims, the epistemic constraints cannot
live in the instructions. An instruction is advice. A contract that **cannot represent** the
dishonest answer is a different kind of object.

Concretely: `additionalProperties: false`. A model cannot add a field nobody agreed to. That is
not fussiness about JSON — it is the mechanism.

One concrete failure worth thirty seconds, from Osborne's own live demo. His agent probed the
machine for quantum-chemistry software. `which orca` returned `/usr/bin/orca` — which is GNOME's
**screen reader**, not the ORCA quantum-chemistry package. A `grep` in the same sweep matched
imagemagick's "quantum depth". Nothing was installed, and the name matched anyway.

**A name match is not an identity match.** Which is why a reference in this system is four parts —
record type, record id, revision, content hash — and never a path or a display name. Not because
paths are inelegant: because `/usr/bin/orca` resolved.

### 12. Three structural refusals — 13:20
Three rows, each a thing the contract makes impossible rather than discouraged:

1. **A producer cannot review its own output.** And — the sharp version, borrowed from
   Paper2Agent — *changing a role prompt inside one agent context does not create a second
   reviewer.*
2. **A backtranslator cannot see the source.** Not "should not": its context does not contain it.
3. **A fixed program has no scientific discretion.** The thing that runs Lean cannot decide what
   the result means.

### 13. Delivery is not acceptance — 14:40
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

## Part III · What we got wrong — 16:00 to 21:00, four slides

> This is the section that buys credibility for everything after it. Do not rush it and do not
> apologise through it. The finding is interesting on its own terms.

### 14. We built the nine-agent version first — 16:00
`schema v0.1`: nine task templates, 23 operations, eight agent modules, each with a role
document, an interface, conformance fixtures, a JSON Schema and an offline checker. It all
type-checks. 368 tests pass.

### 15. Then we audited it — 16:50
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

### 16. Nothing was hidden. Nothing was forbidden either — 18:40
**Job:** the actual lesson, and it is not "we were sloppy".

Every one of those boundaries is written down somewhere in the repository. The failure is
narrower and more interesting: **the contract permitted all three.** A folder assembled from a
hand-written seed satisfied the Task schema. A regex scan satisfied `dependency.search`.

A contract that documents its limits is not the same as a contract that enforces them.

### 17. So the contract changed — 19:50
`schema v0.2`: four operations, three agent modules, five schemas. Nine agents down to four
operations, and one new first principle:

> **Every executed research task calls a model. Replaying a manual seed, copying an old result,
> or scanning citations alone does not constitute a new Agent execution.**

Each of the three findings is now definitionally impossible rather than discouraged. That is the
only kind of fix that survives contact with a deadline.

---

## Part IV · v0.2 and the demonstration — 21:00 to 31:00, five slides and three live beats

### 18. The four operations — 21:00
`paper.extract` → `dependency.search` → `autoformalization.lamport` → `autoformalization.lean`.

Two things to state: the last two run on **one selected claim**, never the whole paper. And
`Task` → `Output` → `run` is the whole interface — one bounded work order, one JSON object back,
one host receipt.

### 19. Who owns what — 21:50
**Job:** the mechanical/judgement line, because everything else follows from it.

| The host, mechanically | The model, as judgement |
|---|---|
| resolve a marker to a byte range and hash it | choose which passage is the claim |
| build the paper's macro table | write the statement out with notation unified |
| run the kernel, capture the exit code | decide what to attempt formalizing |
| record who executed what, and when | — |

The model is never asked to compute a hash, and the host is never asked what a theorem means.

### 20. ▶ LIVE — a work order and a refusal — 22:40
**Beat one.** In a terminal:

- Show a `Task`: the operation, the exact inputs with hashes, the purpose, the limits.
- Run the source resolution. Two markers resolve to byte ranges in `draft.tex`:
  `[18686, 19275)` for the main theorem, `[45972, 46573)` for the lemma that blocks it.
- **Then the third one refuses**: `END_AMBIGUOUS` — `\end{theorem}` occurs more than once after
  the start marker. It will not guess.

That refusal is the demo. A system that resolves two and refuses one has told you something a
system that resolves three cannot.

**Start the Lean build now**, in a second pane, and say you are starting it. 84 seconds.

### 21. ▶ LIVE — the macro table, and the kernel — 24:30
**Beat two.** While Lean runs:

`\Mcal` means `\mathcal M` in this paper — and it is defined on line 8 of `draft.tex`, not in the
preamble it inputs. 42 macros recovered mechanically; 45 control sequences reported unresolved
rather than guessed. Worth one sentence: our first version scanned only the preamble and reported
the paper's own notation as unresolved. That is how we found the bug.

Then the build lands: exit 0, 8408 jobs, axioms within the allow-list, no `sorry`.

### 22. The map, filled — 26:00 · **recurring figure, second appearance**
**Job:** the climax. Same figure as slide 4, now with states.

- **Three rungs green** — kernel-checked in Lean. And they sit in the *mathematics* branches
  (`mwis-definition`, `perfect-graph-definition`, `sign-alignment-identity`) while feeding a
  quantum-information conclusion. Cross-field reuse, visible without being asserted.
- **The theorem at the top is not green.** It is blocked.
- **Two of the six foundations are red**, and the figure makes it obvious they are load-bearing.

### 23. What blocks it — 27:20
**Job:** the sentence the whole talk exists to deliver.

Click through to the blockers. One is another paper's proof gap. The other:

> `root:perfect-graph-weighted-duality` — Chvátal 1975.
> `source_fidelity: UNCHECKED` · `acceptance_basis: DECLARED_BACKGROUND` ·
> `formalization_mode: EXPLICIT_THEOREM_PARAMETER`

Assumed in Lean. Not proved. And the system says so rather than hiding it.

> **The bottleneck to verifying a 2026 quantum-information paper is a 1970s graph-theory theorem
> that has never been frozen from its primary source and aligned to the conventions in use.**

Pause here. This is the slide they will remember.

### 24. ▶ LIVE — the gate says no — 29:20
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

### 25. What one paper costs — 31:00
**Job:** turn the whole proposal into arithmetic.

Two scopes, kept apart, because the Lamport/Lean branch runs on one claim by design:

| Scope | Calls | Input | Output | Per paper |
|---|---|---|---|---|
| **A** — extract, dependency on all 25 claims, formalize **one** | 66 | 1.17 M | 146 k | **≈ $9.5** |
| **B** — the same, formalizing **all 25** | 210 | 3.93 M | 770 k | **≈ $39** |

The 25 is measured, not assumed. Say the two caveats out loud: token counts are a
four-characters-per-token approximation, and the rate card was looked up, not remembered.

### 26. The useful number is not the price — 32:30
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

### 27. Reuse — 34:00
Which already-verified upstream declarations extend to a new theorem. Two consequences beyond
convenience: the six-axis separation **forbids** a Lean theorem standing in for a physical
statement, so the physical content has to be written down; and the unit of formalization changes
— what a human reads is a dependency chain, with Lean declarations as evidence attached to its
rungs, not thousands of lines nobody navigates.

**They provide the terrain; this provides the map.** What those libraries lack is not tooling but
an answer to which theorem to prove next and what proving it unlocks.

**Distance:** no automated upstream search exists. Condition matching is a human judgement. The
semantic contract has no producer.

### 28. Knowledge increment — 35:30 · **recurring figure, third appearance**
The closure again, dimmed, with the inherited roots separated from this paper's new claims. What
does a new theorem actually add, against a fixed baseline, without claiming world-first?

**Distance:** the delta checker only requires the comparison set and the targets to intersect. No
comparison has been run on a real pair. "Contribution" currently means structural difference
within one frozen batch — which is not scientific significance. And this operation is not in
v0.2's startup path at all.

### 29. Knowledge discovery — 37:00
Three questions, and they are not equally far away. Which theorems matter — computable from the
graph today, out-degree gives `frustration-graph` 10 and `gottesman-stabilizer-formalism` 9. By
what route they were obtained — recoverable, because multi-premise inference is an explicit node
rather than a lost hyperedge. **Whether the pattern of connections can be learned to propose new
theorems worth proving — an open research question, not a roadmap item.**

Its precondition is the whole point: learning from candidate edges is learning from noise. Which
is why the graph stays derived and never becomes a second source of truth — **the trustworthiness
of a connection cannot exceed that of the records it connects.**

### 30. Structured transparency — 38:30
September 2026: a proof reported from roughly 10,000 agents over 88 hours on an internal model,
followed by a credit dispute. State the parties' positions as positions, not as findings.

The structural point, not a slogan: **if checking a result requires owning comparable compute,
verification becomes a function of capital.** Slide 25 is this argument in arithmetic — ten
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

### 31. What I want from you — 40:00
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

**Four live beats, and a fallback for each.** Slide 8 is the new one and the only one that needs
a credential: three calls on one query. Run it *ahead of the talk*, save the three outputs and
their receipts, and present those — the point is the byte-identical input, which a stored receipt
proves as well as a live call does, and better than a live call that fails. Then slide 20
(source resolution, ~5 s), slide 21
(macro table, instant; Lean build started at 20 and landing at 21 — 84 s, or 38 s for the audit
step alone), slide 24 (phase gate, instant). Only the Lean build has real duration, and it runs
under narration by design.

If a live step fails, show the stored receipt **and say it is stored**. The entire talk is about
that distinction; pretending otherwise on stage would undo it.

**If slide 8 has no credential by then**, show the comparison's structure and say it has not been
run. Do not invent three answers. It would be the one fabrication in a talk whose entire thesis is
that fabrications are what contracts exist to prevent — and it is the slide an audience would be
most likely to ask to see again.

**Two numbers to re-check the morning of the talk:** the rate card on slide 25, and whether a
real `COMMITTED` run exists. If one does, slide 24 becomes a pass rather than a refusal — rewrite
that slide, do not narrate around it.

## Deck mechanics

The existing beamer deck at `slides/agtxiv_mathcontract_demo.tex` already carries the palette,
the metropolis theme and the TikZ setup. Reuse it. The closure figure has a generator:
`schema v0.2/host_probe/evidence/closure.json` holds the nodes, layers, branches and states, and
`blocked-theorem.html` renders it — export the SVG from there for slides 4, 22 and 28 rather than
redrawing it three times.
