# Output Shape Only: A Hand-Authored Teaching Example

**This is not a paper execution result or a model call, and no validation has been run.** source.txt contains a manually written mathematical statement; output.json is only for understanding fields. No Task hashes, provider calls, passing checks, or run.json have been fabricated.

If a future real Task supplies [source.txt](source.txt) under the input alias paper_text, [output.json](output.json) illustrates three items:

1. loc1: The model identifies source boundary text; the host subsequently computes the actual byte range.
2. sc1: The original assertion and its component c1 are faithfully represented.
3. mc1: The real-number domain and universal quantifier are explicit. It references sc1/c1, which also references mc1.

This bidirectional correspondence is not a circular proof. It contains no proof steps and implies neither confirmed dependencies nor a successful Lean check.

Only after real execution can the host save actual output bytes and assign persistent identity. A subsequent Task may supply mc1 under a new input alias, target, to Dependency for dependency search or Autoformalization for Lamport generation. The short string mc1 is not a cross-paper global ID.

issues=[] means only that this hand-authored example lists no gaps; it does not establish complete extraction from a real paper. Real Task/run call evidence, source binding, and checking still require implementation. Pending acceptance work is recorded centrally under V02-* in PENDING_TESTS.
