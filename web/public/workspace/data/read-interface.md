# Read Interface: What a Tool May Expose, and What It Must Return With It

Applies to research/0.2.0. The four research operations write candidates; this document governs
**reading** them back — from a coding agent, another program, or a person. It has no
implementation yet; `host_probe/` holds a reference query backend and nothing else.

The shape here is adapted from [Paper2Agent](https://github.com/jmiao24/Paper2Agent), which
packages a paper's methods as MCP tools. Section 4 states what does **not** carry over, because
that project's unit is an executable method and ours is a claim with its conditions.

## 1. There is no "run the theorem"

Paper2Agent can wrap `scanpy.clustering()` because it is a function over data. A theorem is not.
For a theoretical paper the exposable surface is not the paper's methods but **its records, plus
the fixed checkers that act on them**:

| Read operation | Answers | Backed by |
|---|---|---|
| `claim.get` | this claim's statement, conditions, quantifiers, and how far its wording moved from the source | a committed `math_claim` item and its `normalization` block |
| `claim.dependencies` | within one sealed batch, what this claim load-bearingly depends on and each dependency's state | a bounded `DependencyQuery` against a projection |
| `source.span` | the exact bytes behind an anchor | a `source_binding` from the producing run |
| `formal.check` | whether a declaration passes the kernel in a pinned environment, and on which axioms | a `formal-check` receipt from a real build |

Only `formal.check` executes anything, and it is a fixed program with no scientific discretion.
The other three are reads. None of them returns a verdict on a claim, because no read operation
is entitled to one.

## 2. Every read returns three things, never one

Adopted directly. A tool returns a JSON object carrying **`message`**, **`reference`**, and
**`artifacts`**, plus compact summary fields — and never a bare answer:

- **`message`** — what was found, in a sentence a reader can act on.
- **`reference`** — the exact identity this came from. Paper2Agent pins a repository URL to a
  commit; here it is the persistent candidate identity: producing-task hash, output hash, and
  `item_id`, or for a span the source hash plus byte range. A path or a display name is not a
  reference.
- **`artifacts`** — `[{"description", "path"}]`, absolute paths, a fresh directory per call.

Compact summary fields (counts, resolved settings, coverage) are welcome; **full arrays are not**.
This is STORAGE section 4's size discipline applied to the read side: a response that inlines a
whole record set has copied the store rather than referenced it.

The rule behind the triple is the one this project already holds elsewhere: an answer is never
separable from what it is grounded in. A read interface that returns only `message` is a summary
generator, and summaries are what this project exists to avoid.

## 3. Four further rules taken as written

1. **A description on every parameter, and it *is* the documentation.** Paper2Agent requires
   `Annotated[type, "one sentence"]` on each one. Every field in a v0.2 read request carries a
   one-sentence description in its schema; a field whose meaning lives only in prose elsewhere is
   incomplete.
2. **Closed choices are closed.** Enumerate the admissible values rather than accepting free
   text, and map caller-facing values onto internal ones inside the implementation. v0.2's write
   side already does this throughout — `relation_to_source`, `outcome`, `state`, `exactness` —
   and the read side inherits it.
3. **A failure is a typed error, not a successful-looking empty answer.** Paper2Agent: "expected
   failures must be MCP tool errors." Here: an unimplemented query kind returns an explicit
   unsupported outcome, a query exceeding its `Limits` says so in `coverage`, and neither is
   allowed to look like a query that ran and found nothing. **An empty result must never stand in
   for an unimplemented one.**
4. **Expose no parameter the backing thing cannot honour.** Paper2Agent: "add `seed` only when
   the bound upstream code is actually seedable." So a kernel check takes no tolerance argument,
   because the kernel has none; a query against a backend without transitive expansion does not
   accept a depth it will silently ignore.

And one about delivery, which this repository currently fails: **checking in-process is not
checking as delivered.** Paper2Agent requires real stdio packaging checks at integration and
states that importing a server is not equivalent. `host_probe/` scripts pass under this
repository's own virtualenv; that is not evidence they work for a reader who installs them. A
packaging check belongs in the pending list, not in a claim.

## 4. What does not carry over, and why

Paper2Agent's own limits say it needs a paper with a public codebase; it does not extract
algorithms that exist only in prose. That boundary lands exactly on the discipline difference.

**The tutorial-extraction pipeline does not apply.** Its scanner → executor → extractor →
verifier chain runs over notebooks and example scripts. arXiv:2607.26154v1 ships `draft.tex`,
`head.tex`, two `.bbl` files and two PDFs. There is no notebook, and the one numerical result in
the paper is already blocked for exactly that reason — `figure2-code-unavailable` records that
the bundle contains the rendered figure but not the code, samples, seeds, sampling law, angle
distribution, precision, tolerance, or error bars.

**Reference-value comparison does not apply to a claim.** Paper2Agent verifies a tool by calling
the paper's own code and comparing against its output, with justified floating-point tolerances
and explicit nonfinite handling. For a theorem there is no upstream execution to compare with:
the kernel returns a proof or a failure, not a reference value within a tolerance. Importing that
machinery into the claim layer would invent a comparison that has no referent.

Where it does apply is narrower than it first appears, and worth stating precisely: **a
theoretical paper's numerical appendix**. This paper has one, it is load-bearing for one claim,
and it is correctly blocked. When that layer is eventually built, Paper2Agent's rules are the
right starting point — expected values from real execution, exact integer and identifier checks,
justified tolerances, no comparison against truncated output, and no relaxing an assertion to
obtain a pass. Until then the honest position is that v0.2 has four operations and none of them
is a reproduction operation.

## 5. Status

Specification only. The reference query backend in `host_probe/` answers one bounded dependency
query and returns provenance; it does not implement this document's return triple, its typed
failures, or any packaging check. Pending work is recorded centrally as `V02-19`.
