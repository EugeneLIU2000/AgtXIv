# Translation and reading notes

## Status

This is a `FOCUSED_DRAFT`, not a complete full-paper translation. It is
complete for the first AgtXIv vertical slice: abstract, definitions, exactness
gate, graph dual, closed-form theorem, Clifford covariance, numerical claim,
outlook, and the load-bearing appendix steps.

## Terminology decisions

- Keep `magic` in English because it is the standard resource-theory term;
  use “非稳定子性” when the formal property is emphasized.
- Translate `frustration graph` descriptively as “反对易图” on first use;
  the edges encode Pauli anticommutation, not ordinary energetic frustration.
- Preserve `perfect graph` in English after its definition to avoid confusing
  it with the informal phrase “a flawless graph”.
- Use “极大独立集” for `maximal independent set` and “最大独立集” for
  `maximum independent set`; they are not interchangeable.
- Write `Pauli-active dependency` throughout. AgtXIv also has scientific claim
  dependencies, and using the bare word “dependency” for both is hazardous.
- Expand `maximum-weight independent set` once in the reader and avoid the
  acronym in explanatory prose when it is not needed.
- `witness capacity` is kept bilingual because “见证容量” is not yet a stable
  Chinese convention in this draft.

## Source-normalization notes

- Displayed formulas were converted from TeX macros to standard MathJax names;
  mathematical content was not changed.
- The target source initially describes Pauli operators modulo phase. For any
  implementation, expectation coordinates still need signed Hermitian
  representatives; this is an implementation normalization, not a verbatim
  source statement.
- The introduction's broad phrase that detection “requires full tomography” is
  read narrowly as evaluation of general standard monotones/universal
  membership, because the paper itself constructs incomplete-measurement
  witnesses.

## Scientific cautions

- The imported V-representation statement is aligned with the target, but its
  cited arXiv proof contains a gap in an intermediate maximality claim. The
  counterexample does not refute the convex-hull theorem. The AgtXIv prototype
  keeps the claim blocked pending an independently reviewed repair.
- `perfect` requires `chi = omega` on every induced subgraph.
- The sign-relaxed vertices are pseudo expectation assignments, not quantum
  states.
- Outer relaxation makes the relaxed robustness no larger than the exact one.
- Capacity, empirical detection coverage, and a state's full magic are distinct.
- Figure 2 cannot be marked reproduced from the available source bundle.

## Pending full-reader work

The universal `2n+1` ceiling proof, all squared-profile/stabilizer-Renyi-entropy
material, complete citations, and paragraph-by-paragraph translation of the
remaining appendix are intentionally pending. The source map lists these gaps
so downstream tools cannot mistake this draft for full coverage.
