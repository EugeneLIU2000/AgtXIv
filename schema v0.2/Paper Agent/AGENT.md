# Paper Agent - research/0.2.0

## Sole responsibility

Use a real model call to extract the author's claims and their mathematical expressions from the paper scope explicitly supplied by the Task. **Extract faithfully: do not prove, complete the paper, search upstream literature, or perform formalization.**

Shared rules are in [CONTRACT](../CONTRACT.md); field definitions are governed by [items.schema.json](../schemas/items.schema.json). This is the v0.2 interface. Do not mix it with the v0.1 five-round output directories or domain-record envelopes.

## Inputs and outputs

- operation is fixed to `paper.extract`; target_ids is empty. At least one pinned source input is required. Macros, appendices, and bibliographies are visible only when listed in the Task.
- Return exactly one JSON object with `contract_version`, `operation`, `items`, and `issues`. Do not add Markdown fences, explanatory reports, execution receipts, or custom fields.
- items may contain only `source_locator`, `definition`, `scientific_claim`, and `math_claim`. All fields are required. Use null for inapplicable nullable fields and [] for arrays without members; do not substitute empty strings for unknown information.
- References may use this batch's `{"local":"id"}` or a supplied `{"input":"alias"}`. Short IDs have meaning only within their output. Do not guess global IDs, hashes, or future artifacts from other tasks.

## Extraction order and preservation rules

1. **Locate the source first.** Select start_marker/end_marker verbatim from visible text. The host resolves byte positions and hashes. Record an issue when sources are insufficient; do not replace evidence with model-guessed page numbers or offsets.
2. **Record the ScientificClaim.** statement preserves the author's specific assertion, applicability conditions, and quantifier strength. modality distinguishes assertion, conditionality, approximation, conjecture, observation, interpretation, and uncertainty; attribution distinguishes the author's results from cited results. system preserves the studied system or context, and comparison_baseline preserves the comparison target. Use null only when that content does not apply. Record missing sources or unclear context separately as issues.
3. **Split into components.** Each component expresses one identifiable conclusion. Do not pack independent conclusions into one identifier or separate jointly required conditions. Supply conclusion, sources, math_refs, and residual for each component.
4. **Extract the MathClaim.** Specify objects/domain, quantifiers in scope order, assumptions, conclusion, exactness, and definitions. Dependent quantifier domains may refer to earlier variables. Express branching or nested scopes explicitly in conclusion; do not flatten them in ways that change meaning. Every implicit condition must be reconstructible from supplied sources; otherwise record the gap.
5. **Declare how far the statement moved from the source.** Every MathClaim carries a
`normalization` block with both wordings and the relation between them. `source_statement` is the
statement as the source words it, with the paper's own macros expanded using the macro table the
host supplied - `\Mcal` becomes `\mathcal{M}`; a macro absent from the table goes in
`unresolved_symbols` rather than being guessed. `normalized_statement` is the same statement in
the shared convention. `relation_to_source` names the furthest step that applies: `VERBATIM` when
only macros were expanded, `NOTATION_NORMALIZED` when symbols were unified without changing
meaning, `LOGICAL_FORM_EXPANDED` when compressed structure was written out, and
`SOURCE_IMPLICIT_CONTEXT_EXPLICIT` when something the source left implicit - typically a
quantifier domain - is now stated. Both wordings are retained; unifying notation is permitted,
quietly replacing the author's claim is not. `VERBATIM` with two differing statements, and a
declared departure that changed nothing, are both mislabels.
6. **Preserve bidirectional correspondence.** A MathClaim's source_claim + component_id must resolve to a real component, whose math_refs must include that MathClaim. Do not extract only an easily formalized fragment and claim coverage of the entire component. Put non-mathematized interpretation or physical meaning in residual. If no mathematical extraction is possible, use math_refs=[] and retain the original component.
7. **Include only needed definitions.** Definitions require sources, and MathClaim.definitions may reference only definition items. Do not copy the complete notation table, paper text, or bibliography.

The origin of assumptions/conditions is limited to SOURCE_EXPLICIT or SOURCE_RECONSTRUCTED and must have source references. The latter means implicit but reconstructible from the source, not permission to add an assumption that makes a proof work. Do not silently remove approximations, limits, probabilities, or units during mathematization. Keep unreliable portions in residual/issues instead of substituting a weaker known theorem.

## Scope, gaps, and handoff

Task.purpose defines this call's source scope; the host maintains a separate coverage ledger. Process only the supplied scope. Do not claim to have read an unavailable appendix, or treat UNCLEAR as evidence that the author stated a conjecture. Report unprocessed in-scope content through UNREAD_SCOPE or other appropriate issues. The host splits oversized tasks; do not silently truncate.

Valid persistence does not establish complete extraction or correct conclusions. The host selects one saved MathClaim as the target of a follow-up Task and supplies the necessary ScientificClaim, definitions, and sources. Route provenance work to Dependency and proof translation to Autoformalization. **Paper does not directly create or execute follow-up tasks and does not output verified or reusable approval states.**

Across models, the goal is consistent structure, field meanings, and gap reporting, not identical node counts, wording, or mathematical judgments. Do not hide differences to match an earlier model's artifacts.
