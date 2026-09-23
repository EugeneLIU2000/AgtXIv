// These are reading projections, not a v0.2 producer or an admission adapter.
// A historical V3 argument keeps its identity and is never exported as v0.2.
const base = '/workspace/data';
export const catalog = [
  { id: 'minimal', title: 'A nonnegative square', category: 'SCHEMA 0.2 · TEACHING EXAMPLE', description: 'Explore how source locators, scientific claims, and mathematical claims connect through one simple statement. Hand-authored, with no model execution.', searchable: 'square real nonnegative teaching v0.2 example', number: '01' },
  { id: 'robustness', title: 'Robustness of magic', category: 'RESEARCH PAPER · HISTORICAL CANDIDATES', description: 'Follow the argument for robustness monotonicity, from signed decompositions and free operations to weight contraction. Six historical candidate interpretations.', searchable: 'quantum robustness magic 1609.07488 stabilizer', number: '02' },
];

async function readJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Could not load the material (HTTP ${response.status}).`);
  return response.json();
}

export async function loadDataset(id) {
  if (id === 'minimal') {
    const [raw, sourceResponse] = await Promise.all([
      readJSON(`${base}/paper-minimal.json`), fetch(`${base}/source.txt`),
    ]);
    if (!sourceResponse.ok) throw new Error('The teaching example source text is unavailable.');
    const source = await sourceResponse.text();
    const titles = { loc1: 'Source statement', sc1: 'Nonnegative squares', mc1: 'Real squares are nonnegative' };
    const labels = { loc1: 'SOURCE LOCATOR', sc1: 'SCIENTIFIC CLAIM', mc1: 'MATH CLAIM' };
    return {
      id, title: 'A nonnegative square', category: 'TEACHING EXAMPLE · RESEARCH / 0.2.0',
      subtitle: 'One source statement, connected scientific and mathematical claims.',
      notice: 'Hand-authored example · No model call, proof, or review receipt.',
      defaultNode: 'mc1', raw, source, download: `${base}/paper-minimal.json`,
      nodes: raw.items.map(item => ({
        id: item.id, kind: item.kind, title: titles[item.id] || item.id,
        label: labels[item.id] || item.kind, raw: item,
      })),
      // These are source/correspondence references, not proof dependencies.
      edges: [{ from: 'loc1', to: 'sc1', kind: 'correspondence' }, { from: 'sc1', to: 'mc1', kind: 'correspondence' }],
      origin: 'schema v0.2/examples/paper-minimal/output.json',
      sourceOrigin: 'schema v0.2/examples/paper-minimal/source.txt',
      identityNote: 'These local IDs apply only within the hand-authored Output. There is no producing Task, COMMITTED run, or persistent candidate identity.',
    };
  }
  if (id === 'robustness') {
    const library = await readJSON('/data/library.json');
    const paper = library.papers.find(paper => paper.slug === 'robustness-of-magic');
    if (!paper) throw new Error('The historical robustness example was not found in the library.');
    return {
      id, title: 'Robustness of magic', category: 'ARXIV:1609.07488v2 · HISTORICAL V3 READING',
      subtitle: paper.title, notice: 'Historical V3 candidates · Not migrated to v0.2 or scientifically reviewed.',
      defaultNode: 'R3', raw: paper, source: null, download: '/api/v1/papers/robustness-of-magic',
      nodes: paper.claims.map(claim => ({ id: claim.id, kind: 'historical', title: claim.title, label: 'HISTORICAL ARGUMENT', raw: claim })),
      edges: paper.claims.flatMap(claim => claim.dependencies.map(from => ({ from, to: claim.id, kind: 'historical' }))),
      origin: 'web/public/data/library.json → robustness-of-magic', sourceOrigin: paper.source_url,
      identityNote: 'Original record_ref values, source anchors, and unassessed states are retained. The links represent historical candidate arguments, not proven dependencies.',
    };
  }
  throw new Error('This material is not available.');
}

export const kindNames = {
  source_locator: 'Source locator', scientific_claim: 'Scientific claim candidate', math_claim: 'Mathematical claim candidate', historical: 'Historical argument candidate',
};
export const operations = [
  ['paper.extract', 'Extract candidates from a paper', 'Extract source locators, definitions, scientific claims, and mathematical claims. Preserve conditions, quantifiers, and unresolved issues.'],
  ['dependency.search', 'Find historical dependencies', 'Propose searches for one MathClaim, compare supplied upstream material, and save candidate relationships. The host retrieves sources between tasks.'],
  ['autoformalization.lamport', 'Structure a proof draft', 'Pin one MathClaim version and produce a Lamport proof draft with explicit joint premises, proof routes, and scopes.'],
  ['autoformalization.lean', 'Generate a Lean draft', 'Use a previously saved Lamport artifact and a fixed environment for the same MathClaim to generate Lean source drafts. Actual build results require separate receipts.'],
];
export const layers = ['SHAPE', 'TASK_BINDING', 'REFERENCES', 'SOURCES', 'LAMPORT_STRUCTURE', 'FORMAL_BUILD', 'ALIGNMENT'];
