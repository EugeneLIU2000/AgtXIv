const pptxgen = require('pptxgenjs');
const L = require('./lib.js');
const { INK, MUTED, WHITE, OPEN, HEAD, BODY, MONO, M, W, H } = L;

const p = new pptxgen();
p.layout = 'LAYOUT_WIDE';
p.author = 'Yingjian Liu';
p.title = 'The case, as schema v0.3 leaves it';

const TOTAL = 17;
let n = 0;
function slide(title, kicker) {
  const s = p.addSlide();
  s.background = { color: WHITE };
  n += 1;
  L.titleBlock(s, n, TOTAL, title, kicker);
  return s;
}


/* A figure slide. The graph is the argument; the text only frames it. */
function figure(s, path, aspect, topY=1.70, maxH=4.30) {
  let h = maxH, w = h * aspect;
  const maxW = W - 2*M;
  if (w > maxW) { w = maxW; h = w / aspect; }
  s.addImage({ path, x:(W-w)/2, y:topY, w, h });
}

/* ---------- 1 title ---------- */
{
  const s = p.addSlide(); s.background = { color: INK };
  s.addText('The case, as v0.3 leaves it', { x:M, y:2.25, w:W-2*M, h:1.0, isTextBox:true, margin:0,
    fontFace:HEAD, fontSize:42, bold:true, color:WHITE });
  s.addText('One paper, taken from frozen bytes toward a proof — and stopped, precisely, where it stops.',
    { x:M, y:3.30, w:W-2*M-1.5, h:0.6, isTextBox:true, margin:0, fontFace:BODY, fontSize:18, color:'CADCFC' });
  s.addText('arXiv:2607.26154v1  ·  schema v0.3  ·  state of 2026-09-20', { x:M, y:4.20, w:W-2*M, h:0.4,
    isTextBox:true, margin:0, fontFace:BODY, fontSize:12, color:MUTED, charSpacing:1.4 });
  s.addNotes('Every number in this deck is read from a named file under schema v0.3/ and carries the disclaimer that file attaches to it.');
}

/* ---------- 2 the question ---------- */
{
  const s = slide('The question the case is meant to answer', 'the setup');
  L.twoCol(s, {
    head: 'the input',
    body: 'One arXiv paper as frozen bytes: draft.tex, 69,678 bytes, content-hashed.\n\n' +
          'The main theorem: for a measurement set with no active dependencies whose frustration graph is ' +
          'perfect, the reduced robustness of magic has a closed form over cliques.',
  }, {
    head: 'the question',
    body: 'What does that sentence depend on, and who has checked which part?\n\n' +
          'Not "is it true". The case is about whether the dependency and the checking can be made ' +
          'mechanical — extracted from the source, traced to origins, and carried into a kernel.',
  });
  L.caveat(s, 'The paper is the author’s own. That removes permission problems; it does not remove the risk of grading one’s own work, which is why every verdict below is a field written by a program rather than a judgement typed by a person.');
  s.addNotes('Frame the case as a measurement, not a demonstration.');
}

/* ---------- 3 freeze ---------- */
{
  const s = slide('Step one — freeze the source', 'so that every later claim has an address');
  L.statRow(s, [
    { v:'69,678', k:'bytes of draft.tex, content-hashed', s:'every span quoted later resolves to a byte range in this exact file' },
    { v:'2,093', k:'heuristic entries across the target and six selected dependencies', s:'all with exact byte positions retained' },
    { v:'180', k:'heuristic occurrences in the target paper', s:'the denominator every later coverage figure is measured against' },
  ]);
  L.caveat(s, '2,093 entries is not 2,093 independent mathematical results, and does not assert the source was read exhaustively. The 180 is labelled SUPPLIED_HEURISTIC_OCCURRENCE_IDS_NOT_ALL_MATHEMATICS — a heuristic count cannot establish "all maths claims".');
  s.addNotes('Freezing is the cheap part, and it is what makes everything after it checkable.');
}

/* ---------- 4 extract ---------- */
{
  const s = slide('Step two — extract the statements', 'runs/research-terra-continuation-20260920');
  L.statRow(s, [
    { v:'39 / 39', k:'output ranges answered, after a two-model continuation', s:'Luna 22 calls, 20 ok, 2 source-location failures; Terra re-ran those 2, both ok' },
    { v:'240', k:'candidate statements from the .tex alone', s:'154 generic claim · 38 definition · 34 equation · 5 theorem · 5 lemma · 4 proposition' },
    { v:'149 / 180', k:'heuristic occurrences referenced by a candidate', s:'unfinished_scope_count: 0' },
  ]);
  L.caveat(s, 'source_completeness_asserted: false, in the same summary.json. "Ranges answered" is a dispatch metric, not coverage of the mathematics — and the 240 is a host combination of retained reading batches with no semantic de-duplication, so it is an unreviewed candidate count, not a census of the paper’s claims.');
  s.addNotes('39 of 39 is the strongest-sounding number in the deck, which is exactly why its caveat sits under it.');
}

/* ---------- 5 the graph ---------- */
{
  const s = slide('Step three — assemble the dependency graph', 'graphs/00001-db0e3d21/graph.json');
  L.ledger(s, ['what the 613 nodes are', 'count', 'what it means'],
    [
      { cells:['candidate statements', '240', 'extracted from the frozen .tex'] },
      { cells:['external claim requests', '152', 'anchored to a .bbl byte range — paper_id null. Nobody has fetched these yet'] },
      { cells:['unresolved claim occurrences', '221', 'a location in the source that no candidate has yet claimed'] },
      { cells:['total nodes / edges', '613 / 634', 'assembled without the legacy DAG: legacy_dag_edges_used false'], open:true },
      { cells:['support groups', '213', 'AND-groups of premises'] },
      { cells:['accepted support edges', '0', 'of 634'], open:true },
    ], 1.95, [4.6, 1.7, 5.79]);
  L.caveat(s, 'all_judgements_unreviewed: true. Three hundred and seventy-three of the 613 nodes are not statements at all — they are open requests and unclaimed locations, i.e. the graph’s own record of what it has not done.');
  s.addNotes('The graph is mostly a to-do list, and says so in its own fields.');
}

/* ---------- 5b the extracted graph, drawn ---------- */
{
  const s = slide('The same graph, drawn', 'every mark is a node; every line a proposed dependency');
  figure(s, 'fig/fig-613.png', 2.078, 1.60, 4.30);
  L.caveat(s, 'Hollow throughout, because v0.3 has no accepted state to fill one with. The warm marks are the majority: 373 of 613 are external requests nobody has fetched and source locations no candidate has claimed. This is a picture of a reading list as much as of a proof.');
  s.addNotes('Let the room look at it. The point is the proportion of warm to ink.');
}

/* ---------- 6 two number lines ---------- */
{
  const s = slide('Two number lines that must not be added', 'the most important slide in the deck');
  figure(s, 'fig/fig-compare.png', 2.292, 1.58, 4.35);
  L.caveat(s, 'These are two different objects with two different node vocabularies. 613 is not "74 grown"; no completion rate can be computed between them, and v0.3’s own STATUS.md says the scopes cannot be summed. Acyclicity was an editorial achievement of the first, not a finding about the paper.');
  s.addNotes('If one slide survives from this deck, it is this one. The temptation to read 74 -> 613 as progress is exactly the over-claim the project exists to prevent.');
}

/* ---------- 7 the closure re-derived ---------- */
{
  const s = slide('The closure, re-derived a month later', 'runs/2607-full-candidate-20260919/closed-form-branch.json');
  figure(s, 'fig/fig-closure.png', 2.100, 1.58, 3.05);
  s.addText('Same 29 ids, same 11 / 6 / 4 / 2 / 6 kinds, same cones 19 14 12 7 4 2 — recomputed from frozen bytes a month later. ' +
    'Forty-six edges, not forty-five: v0.3 adds one bridging premise the authored graph never recorded.',
    { x:M, y:4.66, w:W-2*M, h:0.62, isTextBox:true, margin:0, valign:'top',
      fontFace:BODY, fontSize:13, color:INK, lineSpacingMultiple:1.25 });
  s.addShape('line', { x:M, y:5.42, w:W-2*M, h:0, line:{color:INK, width:1.25} });
  s.addText('And its coverage under v0.3: 0 of 11 definitions with the statement discharged, 0 of 12 theorem-like nodes with the proof discharged.',
    { x:M, y:5.54, w:W-2*M, h:0.42, isTextBox:true, margin:0, valign:'top',
      fontFace:HEAD, fontSize:15, italic:true, color:OPEN });
  L.caveat(s, 'A v0.3 node has no state field and no declaration field. The graph records disposition, not verification, and will not credit a Lean result to a node until the statement is aligned to its source — none of these 29 is. The three nodes the old deck showed as kernel-checked have had that credit withdrawn, not revoked as wrong.');
  s.addNotes('The counts reproducing exactly is the good news: the drawing was not wishful. The coverage rows are the price.');
}

/* ---------- 8 trace the root ---------- */
{
  const s = slide('Step four — trace the hardest root to its origin', 'root:perfect-graph-weighted-duality');
  L.ledger(s, ['what happened', 'result'],
    [
      { cells:['what the paper actually cites here', 'three separate obligations, not one theorem — weighted duality (Lovász 1972, Chvátal 1975), the antiblocker identity (Fulkerson 1971/72), the polynomial algorithm (Grötschel 1981)'], h:0.72 },
      { cells:['Lovász 1972 characterization', 'obtained. HTTP 200, 142,102 bytes, 4 of 4 pages read, hash-frozen'] },
      { cells:['Chvátal 1975, Fulkerson 1971/72', 'publisher metadata only — access failed, subscription preview, HTTP 403'], open:true },
      { cells:['Berge 1961, which Lovász’s own proof rests on', 'SOURCE_UNREACHABLE_IN_THIS_BOUNDED_SEARCH — not obtained in any form'], open:true },
      { cells:['does the source we read support the claim?', 'BRIDGE_REQUIRED_NOT_EXACT_WEIGHTED_DUALITY_STATEMENT — it gives a finite unweighted hereditary characterization; the paper needs nonnegative real weighted duality. 4 unproved bridges'], h:0.72, open:true },
    ], 1.95, [4.2, 7.89]);
  L.caveat(s, '"We read the source" and "the source supports the claim" are different sentences. earliest_origin_established is false in every file that records it; the root’s own record still reads role EXPLICIT_UNPROVED_PREMISE, outcome BINDING_CANDIDATE_UNREVIEWED.');
  s.addNotes('This is the slide that changed most since August. We went and got the paper. It proves something else.');
}

/* ---------- 9 what the kernel accepted ---------- */
{
  const s = slide('Step five — formalize upward. What the kernel accepted.', 'second Lean epoch');
  L.statRow(s, [
    { v:'82 / 82', k:'modules recompiled in a common environment', s:'lean 4.33.0 · mathlib db584cd6 · physlib 7b6e0fee' },
    { v:'302', k:'cumulative audited declarations — 230 theorems, 69 definitions, 3 inductive types', s:'662 direct term-dependency witnesses' },
    { v:'0', k:'forbidden axioms', s:'propext, Classical.choice, Quot.sound only' },
  ]);
  s.addText('Real mathematics landed here: the complement of a perfect graph is perfect; an optimal integral clique cover equals α(G); ' +
    'a two-sided bound on reduced RoM; and the Varela V-representation — both obligations — machine-proved.',
    { x:M, y:5.05, w:W-2*M, h:0.72, isTextBox:true, margin:0, fontFace:BODY, fontSize:13.5, color:INK, lineSpacingMultiple:1.25 });
  L.caveat(s, 'coverage_scope: ACTUALLY_AUDITED_SELECTED_DECLARATIONS_NOT_PAPER_CLAIM_COVERAGE. 43, 64, 74 and 302 are four nested, overlapping target lists including definitions and support declarations — they measure four different things and must never be summed. The Varela proof is of our own restatement, under a hypothesis 30 declarations assume and 0 conclude.');
  s.addNotes('Give the Lean its full credit here, because the next slide takes it all back.');
}

/* ---------- 10 and none of it counts ---------- */
{
  const s = slide('And what none of it is credited for', 'the same files, their own fields');
  L.ledger(s, ['field', 'value'],
    [
      { cells:['query_declaration', 'null'], mono:1, open:true },
      { cells:['query_chain_complete', 'false'], mono:1, open:true },
      { cells:['source_alignment', 'AGENT_NORMALIZED_UNREVIEWED'], mono:1, open:true },
      { cells:['weighted_perfect_duality_proved  (all 8 evidence files)', 'false'], mono:1, open:true },
      { cells:['declarations assuming / concluding W.NoActiveDependencies', '30  /  0'], mono:1, open:true },
      { cells:['PerfectGraphIntegerCover.lean + PerfectGraphWeightedApproximation.lean', '118 + 120 lines · never compiled by any Lean · no receipt anywhere'], mono:1, open:true },
    ], 1.95, [6.6, 5.49]);
  L.caveat(s, 'Nothing here discharges WeightedPerfectGraphFoundation — it remains an explicit unproved Prop hypothesis in the type of weighted_duality_of_foundation, in both epochs. The two uncompiled files are shown as an admission, not a result: they are source text no kernel has read.');
  s.addNotes('The kernel holds 302 declarations. The graph will not let one of them touch a node.');
}

/* ---------- 11 model to kernel ---------- */
{
  const s = slide('One step, model to kernel', 'the whole design in a single run');
  L.codeAndRead(s,
    'theorem AgtXIv.Generated.Proof_a29f133fb6\n' +
    '    {ι : Type u} [Fintype ι] (x : ι → ℝ) :\n' +
    '    (∑ i, x i) = 1 → 1 ≤ ∑ i, |x i|\n\n' +
    'axioms  propext, Classical.choice,\n' +
    '        Quot.sound\n\n' +
    'uses the audited library theorem\n' +
    '        AgtXIv.RoM.normalized_l1',
    'source            draft.tex line 608, exact byte span\n' +
    'model calls       1\n' +
    'Lean compile      exit 0, network denied\n\n' +
    'kernel_attestation_state\n' +
    '        KERNEL_CHECKED_VACUITY_UNKNOWN\n' +
    'nonvacuity_witness        NONE\n' +
    'promotion_allowed         false\n' +
    'source_alignment_accepted false\n' +
    'coverage                  proof_discharged 0 of 1');
  L.caveat(s, 'The index type may be empty, in which case the hypothesis is uninhabited and the statement vacuous — no witness is claimed. In the host’s own weakest-first ordering, KERNEL_CHECKED_VACUITY_UNKNOWN ranks below UNREVIEWED. This is one elementary step from one line of the paper.');
  s.addNotes('The kernel accepted it and the system refused to count it. That is the design working.');
}

/* ---------- 12 what changed ---------- */
{
  const s = slide('What changed since v0.2', '2026-08-16 against 2026-09-20');
  L.ledger(s, ['', 'v0.2 · August', 'v0.3 · September'],
    [
      { cells:['the extraction', '74 claim nodes, drawn by hand', '240 candidates from the .tex alone; 39 of 39 ranges answered'] },
      { cells:['nodes credited with a Lean result', '3 of 29', '0 — the graph no longer has that field'] },
      { cells:['the perfect-graph root', '"Chvátal 1975 or Fulkerson 1971/72 — candidates only"', 'three obligations; Lovász 1972 obtained and read — it states a different theorem'] },
      { cells:['Lean environment', '4.30.0-rc2, mathlib c1e30e1, "no physlib"', '+ common epoch 4.33.0, mathlib db584cd6, physlib 7b6e0fee, 82 of 82 modules'] },
      { cells:['the Varela V-representation', 'assumed', 'proved — under a hypothesis 30 declarations assume and 0 prove'] },
      { cells:['the refusal', 'phase gate: no COMMITTED run', 'exit 2 · CHAIN_INCOMPLETE · accepted_support_edges 0'] },
      { cells:['support edges anyone accepted', '0 of 45', '0 of 634'], open:true },
    ], 1.95, [3.5, 3.8, 4.79]);
  L.caveat(s, 'The word COMMITTED does not appear anywhere in v0.3’s host or schemas, and paper.extract has run many times since — so the old gate slide shows a failure the system no longer has, which is the same over-claim in reverse. The August Lean build was never re-run this round.');
  s.addNotes('The refusal moved. It did not go away - it got more specific, and it now arrives with receipts.');
}

/* ---------- 13 still not done ---------- */
{
  const s = slide('What is still not done', 'the machine’s own obligation list');
  s.addText(
    'QUERY_DECLARATION_NOT_CONSTRUCTED        SEMANTIC_EXTRACTION_NOT_COMPLETE\n' +
    'AUTOMATIC_DEPENDENCY_GATES_NOT_CALIBRATED    EARLIEST_ORIGIN_SEARCH_NOT_EXHAUSTED\n' +
    'RECURSIVE_NEW_SUPPORT_ADMISSION_NOT_IMPLEMENTED\n' +
    'ROOT_LIBRARY_COVERAGE_NOT_SOURCE_ALIGNED     UNSUPPORTED_ROOT_PREMISES_NOT_RENDERED\n' +
    'RESOLVED_ANCHOR_RECALL_AUDIT_FAILED          SUPPORT_BLOCKERS_REMAIN',
    { x:M, y:1.95, w:W-2*M, h:1.65, isTextBox:true, margin:0, fontFace:MONO, fontSize:12, color:OPEN, lineSpacingMultiple:1.35 });
  s.addText('Not on that list, and also not done', { x:M, y:3.75, w:W-2*M, h:0.3, isTextBox:true, margin:0,
    fontFace:BODY, fontSize:11, bold:true, color:MUTED, charSpacing:1.3 });
  s.addShape('line', { x:M, y:4.06, w:W-2*M, h:0, line:{color:INK, width:1.25} });
  s.addText('The two 2026-09-20 runs carry no integrity-report.json at all.   ·   No independent artifact audit, test suite or negative test was executed this round.\n' +
    'Provider circuit-breaker, batch-reuse recovery and crash recovery are implemented and have never been exercised.   ·   Every integrity report: semantic_completeness_checked false.',
    { x:M, y:4.18, w:W-2*M, h:0.95, isTextBox:true, margin:0, fontFace:BODY, fontSize:12.5, color:INK, lineSpacingMultiple:1.3 });
  L.caveat(s, 'That certificate is a snapshot taken at 00:37 on 2026-09-19 — before the common-epoch audits later the same day. Two of its obligations were discharged afterwards and it was never regenerated. Read it as dated, not current; I would rather say that than let the system look worse than it is.');
  s.addNotes('Showing a stale failure list is as dishonest as hiding one. Hence the timestamp.');
}

/* ---------- 14 the schema cannot say yes ---------- */
{
  const s = slide('The schema cannot say otherwise', 'schemas/research.schema.json · $defs.ChainCertificate');
  L.codeAndRead(s,
    '"human_accepted": {\n' +
    '    "const": false\n' +
    '},\n' +
    '"source_completeness_asserted": {\n' +
    '    "const": false\n' +
    '},\n' +
    '"premise_extraction_status": {\n' +
    '    "const": "QUERY_DECLARATION_ABSENT"\n' +
    '}',
    'These are const, not default.\n\n' +
    'A chain certificate that claimed human acceptance, or asserted the source was read completely, ' +
    'would not be a false record — it would fail validation. The document cannot be written.\n\n' +
    'This is the project’s whole thesis, reduced to nine lines of JSON Schema: the dishonest answer ' +
    'is not discouraged, it is unrepresentable.');
  L.caveat(s, 'Exit 2 is a refusal to certify, not a diagnosis. It does not say which obligation is nearest to closing — and route_search is UNPRICED with explored_states 0, so it cannot say what closing one would cost either. Nothing in this deck may be called cheap to fix.');
  s.addNotes('If the audience remembers one mechanism, it should be const: false.');
}

/* ---------- 15 the ending ---------- */
{
  const s = slide('The ending', 'in the machine’s own words');
  L.quote(s, '“CHAIN_INCOMPLETE: no composed query declaration; a conditional implication has not yet been kernel checked.”',
    'runs/2607-full-candidate-20260919/chain-certificate.json');
  s.addText('mathematical_status  CHAIN_INCOMPLETE      ·      accepted_support_edges  0      ·      proof_backend  NOT_CONNECTED\n' +
    'controller_status  FRONTIER_POLICY_OR_BUDGET_LIMIT      ·      exit code  2, raised by construction',
    { x:M, y:4.85, w:W-2*M, h:0.85, isTextBox:true, margin:0, fontFace:MONO, fontSize:12, color:OPEN, lineSpacingMultiple:1.35 });
  L.caveat(s, 'This is where the case stops today. It is not a failure report: it is the system declining to certify something it has not earned, in a vocabulary that has no word for the thing it has not earned.');
  s.addNotes('Do not dress this up. The ending is the point.');
}

/* ---------- 16 closing ---------- */
{
  const s = slide('What the case shows', 'the measurement, not the proof');
  s.addText(
    '69,678 frozen bytes went in. 240 candidate statements, 613 graph nodes and 634 edges came out.\n' +
    'Zero were accepted — accepted_support_edges 0, at 45 edges in August and at 634 now.\n' +
    'Real mathematics was proved: 302 audited declarations across 82 of 82 modules in a second toolchain, zero forbidden axioms.\n' +
    'None of it was allowed to touch a graph node, because no statement has been checked against its source.\n' +
    'We fetched the 1972 paper the bottleneck is cited to. It states a different theorem, and rests on a 1961 abstract we could not obtain.',
    { x:M, y:1.95, w:W-2*M, h:2.5, isTextBox:true, margin:0, fontFace:BODY, fontSize:14.5, color:INK, lineSpacingMultiple:1.45 });
  s.addText('What would make the next version of this deck different', { x:M, y:4.60, w:W-2*M, h:0.3,
    isTextBox:true, margin:0, fontFace:BODY, fontSize:11, bold:true, color:MUTED, charSpacing:1.3 });
  s.addShape('line', { x:M, y:4.92, w:W-2*M, h:0, line:{color:INK, width:1.25} });
  s.addText('one accepted support edge      ·      one source-aligned statement      ·      a composed Lean declaration for the query',
    { x:M, y:5.06, w:W-2*M, h:0.45, isTextBox:true, margin:0, fontFace:HEAD, fontSize:17, italic:true, color:INK });
  L.caveat(s, 'None of the five lines above is a claim about the paper’s mathematics. They are claims about what this system did, each read from a file under schema v0.3/.');
  s.addNotes('The deliverable is not a proof. It is that we can now say exactly how far this is from done.');
}

p.writeFile({ fileName: 'v03-case.pptx' }).then(f => console.log('wrote', f, '· slides:', n+1));
