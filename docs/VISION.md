# AgtXIv vision and the role of schema v0.3

AgtXIv aims to let the next paper start from an explicitly assessed knowledge
frontier, with earlier sources, assumptions, evidence and unresolved questions
still available for inspection. Each investigation should make later research
easier to understand and reuse.

This English overview explains the project direction and the narrower role of
schema v0.3. It summarizes [AgtXIv.md](../AgtXIv.md) and the proposed
[Charter](../CHARTER.md); it does not replace either document, ratify the Charter,
or change the contracts governing historical records.

## What a reader should receive

A **Paper Agent** is an auditable record of a paper: its attributable claims,
reasoning, sources, assessments, conflicts and limits. Conversation is one way
to access that record. The intended reader can answer five questions:

1. What does this exact version of the paper claim?
2. Which definitions, assumptions, earlier results and evidence support it?
3. What has been examined, and what remains uncertain or blocked?
4. What does it add or change relative to an identified knowledge baseline?
5. Which results can a later paper reuse, under which conditions?

The long-term deliverables are paper-level records with declared coverage,
individually reusable knowledge entries, contribution records relative to a
fixed baseline, and a durable account of unfinished work. Publishing software
alone does not establish any of those scientific outcomes.

## Six questions remain separate

| Assessment axis | The question it answers |
|---|---|
| Source fidelity | Does the record preserve what the identified source actually says? |
| Mathematical correctness | Does the conclusion follow from its mathematical assumptions? |
| Formal alignment | Does the formal statement preserve the intended claim? |
| Semantic applicability | Do the objects and assumptions describe the intended system or regime? |
| Empirical support | What observations support the scientific assumptions and conclusions? |
| Computational reproducibility | Can a computational result be regenerated under its recorded conditions? |

A Lean proof can supply evidence about a precisely stated mathematical
implication. It does not, by itself, answer the other questions. A reproducible
calculation can still implement an inappropriate model. A faithful source
record can preserve a claim that is later refuted. These distinctions are part
of the project purpose.

## What schema v0.3 contributes

The `research/0.3.0` framework develops the mathematical dependency and proof
path. It freezes paper sources, extracts candidate statements, follows relevant
dependencies, retains a query's upstream branch, and schedules Lean attempts
from the roots toward the query. Programs manage identities, budgets, graph
operations and evidence; models propose extraction, matching and proof
candidates. Unreviewed candidates retain their unresolved status.

This is a bounded contribution to the wider design. Selecting one theorem for
an investigation does not replace the eventual query-independent paper record.
Pruning a working graph does not establish full-paper coverage. A candidate
dependency graph is not an admitted knowledge base. The wider argument layer,
six-axis scientific assessment, contribution analysis and subsequent-paper
reuse remain separate obligations.

Read the [workflow](../schema%20v0.3/WORKFLOW.md) for the implemented stages and
the [progress analysis](releases/schema-v0.3-progress.md) for their evidence and
limits. The current recorded case remains `CHAIN_INCOMPLETE`.

## What progress should mean

Progress means fewer unexplained steps, better source alignment, explicit
conditions, inspectable evidence and demonstrable reuse. A failure can be a
useful result when it identifies a missing premise or a counterexample.
Candidate counts, graph size, model confidence and successful compilation must
not become substitutes for scientific assessment.

A future release should demonstrate an attributable path from a source claim
to a bounded conclusion, preserve every material unresolved condition, and
show what a subsequent investigation can safely reuse. Its claims must remain
limited to the evidence actually collected.

## Versions and authority

`schema v0.3` belongs to the **schema contract ladder**. It is distinct from
the older AgtXIv protocol numbers, the broader V3 design, software release
tags and paper-source versions. The Python project currently declares
`2.0.0.dev0`; that value is not a schema v0.3 release tag.

The Charter remains pending under [ADR 0007](adr/0007-adopt-project-charter.md).
Historical V1 and V2 records retain their original authority and meaning.
This release preparation neither promotes those records nor claims that the
whole project vision has been implemented.
