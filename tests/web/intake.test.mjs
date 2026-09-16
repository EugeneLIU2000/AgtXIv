import test from 'node:test';
import assert from 'node:assert/strict';
import { gzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { parseArxivId, analyzeSource, fetchArxivSource, analyzeArxiv, DEFAULT_LIMITS } from '../../src/agtxiv_web/intake.mjs';

const encode = text => new TextEncoder().encode(text);
function tar(entries, { terminate = true } = {}) {
  const chunks = [];
  for (const item of entries) {
    const { name, type = '0', bytes = encode(item.text ?? '') } = item;
    const header = new Uint8Array(512);
    const put = (start, text) => header.set(encode(text), start);
    put(0, name); put(100, '0000644\0'); put(108, '0000000\0'); put(116, '0000000\0');
    put(124, bytes.length.toString(8).padStart(11, '0') + '\0'); put(136, '00000000000\0');
    put(148, '        '); put(156, type); put(257, 'ustar\0'); put(263, '00');
    const checksum = header.reduce((a, b) => a + b, 0);
    put(148, checksum.toString(8).padStart(6, '0') + '\0 ');
    chunks.push(header, bytes, new Uint8Array((512 - bytes.length % 512) % 512));
  }
  if (terminate) chunks.push(new Uint8Array(1024));
  const output = new Uint8Array(chunks.reduce((n, c) => n + c.length, 0)); let offset = 0;
  for (const chunk of chunks) { output.set(chunk, offset); offset += chunk.length; }
  return output;
}
function pax(key, value) {
  const body = `${key}=${value}\n`; let n = encode(body).length + 2;
  while (encode(`${n} ${body}`).length !== n) n = encode(`${n} ${body}`).length;
  return `${n} ${body}`;
}
const paper = String.raw`\documentclass{article}
\newtheorem{thm}{Theorem}
\title{A small {test} of $x^2$}
\author{Ada Example}
\begin{document}
\begin{abstract}We study a small exact result.\end{abstract}
\section{Results}
Unicode: α, 🙂.
\begin{definition}\label{def:x}Let $x=1$.\end{definition}
\begin{thm}\label{thm:one}Using Definition~\ref{def:x}, $x+x=2$. See \cite{example2020}.\end{thm}
\begin{equation}\label{eq:one}x+x=2.\end{equation}

Therefore the construction provides a result for every allowed input in the stated domain.

\end{document}
`;

test('strict modern, legacy and URL identifiers; versions remain explicit', () => {
  assert.equal(parseArxivId('arXiv: 2401.01234v2').canonical, '2401.01234v2');
  assert.equal(parseArxivId('https://arxiv.org/pdf/quant-ph/0601234v1.pdf').canonical, 'quant-ph/0601234v1');
  assert.equal(parseArxivId('0704.0001').version, null);
  for (const value of ['https://evil.example/abs/2401.01234', 'http://arxiv.org/abs/2401.01234', 'https://arxiv.org@evil.example/abs/2401.01234', 'https://arxiv.org/abs/2401.01234?q=a', '2413.01234', '0601.0001', '1501.0001', '1401.00001', 'blah/0601234', 'quant-ph/0712345', '2401.01234v0', '2401.01234v1000', '../../2401.01234', '2401.01234%0a'])
    assert.throws(() => parseArxivId(value), { code: 'INVALID_ARXIV_ID' }, value);
});

test('real TeX input produces readable metadata, source byte anchors, local references and six unassessed axes', async () => {
  const result = await analyzeSource(paper);
  assert.match(result.paper.title, /A small test/);
  assert.deepEqual(result.paper.authors, ['Ada Example']);
  assert.match(result.paper.abstract, /small exact result/);
  assert.deepEqual(result.candidates.map(c => c.type), ['DEFINITION', 'THEOREM', 'EQUATION', 'ASSERTION_PARAGRAPH']);
  const theorem = result.candidates.find(c => c.type === 'THEOREM');
  assert.equal(theorem.dependencies[0].targetIds[0], result.candidates[0].id);
  assert.equal(theorem.dependencies[0].relation, 'LOCAL_REFERENCE');
  assert.deepEqual(theorem.citationCues[0].keys, ['example2020']);
  const raw = encode(paper), selected = raw.subarray(theorem.anchor.startByte, theorem.anchor.endByte);
  assert.equal(new TextDecoder().decode(selected), theorem.latex);
  assert.equal(theorem.anchor.spanSha256, 'sha256:' + createHash('sha256').update(selected).digest('hex'));
  for (const claim of result.candidates) {
    assert.equal(Object.keys(claim.assessments).length, 6);
    assert.ok(Object.values(claim.assessments).every(v => v === 'NO_ASSESSMENT'));
    assert.equal(claim.interpretation, 'SOURCE_LINKED_CANDIDATE_NOT_SCIENTIFIC_APPROVAL');
  }
  assert.equal(result.provenance.sourceStored, false);
  assert.equal(result.frontier.scientificAssessment, 'NOT_PERFORMED');
  assert.ok(result.frontier.unclassifiedSpans.length > 0);
  assert.equal(JSON.parse(JSON.stringify(result)).analysisId, result.analysisId);
});

test('changed new input changes analysis and claims; repeat input is deterministic', async () => {
  const first = await analyzeSource(paper), repeated = await analyzeSource(paper);
  const changed = await analyzeSource(paper.replace('x+x=2', 'x+x=3'));
  assert.equal(first.analysisId, repeated.analysisId);
  assert.deepEqual(first, repeated);
  assert.notEqual(first.analysisId, changed.analysisId);
  assert.notEqual(first.candidates[1].id, changed.candidates[1].id);
  assert.match(changed.candidates[1].text, /x\+x=3/);
});

test('safe gzip, tar, and tar.gz intake inventory unsupported and unlinked material', async () => {
  for (const bytes of [encode(paper), gzipSync(paper), tar([{ name: 'main.tex', text: paper }]), gzipSync(tar([{ name: 'main.tex', text: paper }]))]) {
    const result = await analyzeSource(bytes);
    assert.equal(result.candidates.length, 4);
  }
  const result = await analyzeSource(tar([{ name: 'main.tex', text: paper }, { name: 'unused.tex', text: String.raw`\begin{lemma}Unused.\end{lemma}` }, { name: 'figure.png', bytes: new Uint8Array([137, 80, 78, 71]) }]));
  assert.deepEqual(result.frontier.unclassifiedFiles, ['figure.png', 'unused.tex']);
  assert.equal(result.candidates.at(-1).activity, 'UNKNOWN');
  assert.deepEqual(result.frontier.unsupportedContent.map(x => x.path), ['figure.png']);
});

test('path traversal, absolute paths, Windows paths, links, duplicates and special tar entries are rejected', async () => {
  for (const name of ['../secret.tex', '/etc/secret.tex', 'a/../secret.tex', 'C:/secret.tex', 'a\\secret.tex'])
    await assert.rejects(analyzeSource(tar([{ name, text: paper }])), { code: 'UNSAFE_ARCHIVE_PATH' }, name);
  for (const type of ['1', '2', '3', '4', '6', 'S', 'K'])
    await assert.rejects(analyzeSource(tar([{ name: 'main.tex', type, text: paper }])), { code: 'UNSAFE_ARCHIVE_ENTRY' }, type);
  await assert.rejects(analyzeSource(tar([{ name: 'main.tex', text: paper }, { name: './main.tex', text: paper }])), { code: 'DUPLICATE_PATH' });
  await assert.rejects(analyzeSource(tar([{ name: 'a', text: 'file' }, { name: 'a/main.tex', text: paper }])), { code: 'DUPLICATE_PATH' });
  await assert.rejects(analyzeSource(tar([{ name: 'a/main.tex', text: paper }, { name: 'a', text: 'file' }])), { code: 'DUPLICATE_PATH' });
});

test('checksum mismatch, incomplete tar, binary input, and decompression bombs fail closed', async () => {
  const broken = tar([{ name: 'main.tex', text: paper }]); broken[0] ^= 1;
  await assert.rejects(analyzeSource(broken), { code: 'INVALID_ARCHIVE' });
  await assert.rejects(analyzeSource(tar([{ name: 'main.tex', text: paper }], { terminate: false })), { code: 'INVALID_ARCHIVE' });
  await assert.rejects(analyzeSource(new Uint8Array([0, 1, 2])), { code: 'UNSUPPORTED_SOURCE' });
  await assert.rejects(analyzeSource('%PDF-1.5 hello'), { code: 'UNSUPPORTED_SOURCE' });
  await assert.rejects(analyzeSource(gzipSync('x'.repeat(10000)), { limits: { maxExpandedBytes: 100 } }), { code: 'BYTE_LIMIT' });
  await assert.rejects(analyzeSource(paper, { limits: { maxDownloadBytes: 20 } }), { code: 'BYTE_LIMIT' });
  await assert.rejects(analyzeSource(paper, { limits: { maxCommands: 2 } }), { code: 'COMMAND_LIMIT' });
  await assert.rejects(analyzeSource(paper, { limits: { maxFileBytes: DEFAULT_LIMITS.maxFileBytes + 1 } }), { code: 'INVALID_LIMIT' });
});

test('PAX and GNU path metadata remain bounded and safe', async () => {
  const result = await analyzeSource(tar([{ name: 'PaxHeader', type: 'x', text: pax('path', 'nested/main.tex') }, { name: 'ignored.tex', text: paper }]));
  assert.equal(result.main, 'nested/main.tex');
  await assert.rejects(analyzeSource(tar([{ name: 'PaxHeader', type: 'x', text: pax('path', '../escape.tex') }, { name: 'ignored.tex', text: paper }])), { code: 'UNSAFE_ARCHIVE_PATH' });
  await assert.rejects(analyzeSource(tar([{ name: 'PaxHeader', type: 'x', text: pax('GNU.sparse.map', '0,1') }, { name: 'main.tex', text: paper }])), { code: 'UNSUPPORTED_ARCHIVE' });
  const gnu = await analyzeSource(tar([{ name: '././@LongLink', type: 'L', text: 'nested/main.tex\0' }, { name: 'ignored.tex', text: paper }]));
  assert.equal(gnu.main, 'nested/main.tex');
});

test('includes preserve active, missing, conditional, dynamic, and ambiguous states without executing TeX', async () => {
  const main = String.raw`\documentclass{article}
\input{sections/body}
\input{missing}
\iffalse\input{inactive}\fi
\ifunknown\input{uncertain}\fi
\input{\computed}
\newcommand{\bad}{\input{macro-body}}
% \input{commented}
\begin{verbatim}\input{verbatim}\end{verbatim}
`;
  const result = await analyzeSource(tar([
    { name: 'main.tex', text: main },
    { name: 'sections/body.tex', text: String.raw`\begin{lemma}\label{a}Actual result.\end{lemma}\input{main}` },
    { name: 'inactive.tex', text: String.raw`\begin{lemma}Dormant source.\end{lemma}` },
    { name: 'uncertain.tex', text: String.raw`\begin{lemma}Maybe used.\end{lemma}` },
  ]));
  assert.equal(result.sources.find(f => f.path === 'sections/body.tex').activity, 'ACTIVE');
  assert.equal(result.sources.find(f => f.path === 'uncertain.tex').activity, 'UNKNOWN');
  assert.equal(result.includes.find(i => i.requested === 'inactive').activity, 'INACTIVE');
  assert.ok(result.frontier.issues.some(i => i.code === 'MISSING_INCLUDE'));
  assert.ok(result.frontier.issues.some(i => i.code === 'DYNAMIC_INCLUDE_UNRESOLVED'));
  assert.equal(result.frontier.macroDefinitions, 1);
  assert.ok(!result.includes.some(i => ['macro-body', 'commented', 'verbatim'].includes(i.requested)));
  const ambiguous = await analyzeSource(tar([{ name: 'paper/main.tex', text: String.raw`\documentclass{article}\input{body}` }, { name: 'paper/body.tex', text: 'Nested' }, { name: 'body.tex', text: 'Root' }]));
  assert.equal(ambiguous.includes[0].resolution, 'AMBIGUOUS_INCLUDE');
  assert.equal(ambiguous.includes[0].target, null);
});

test('comments, macro bodies, false branches, duplicate labels and excerpts cannot overstate claims', async () => {
  const source = String.raw`\documentclass{article}
% \begin{theorem}Commented.\end{theorem}
\newcommand{\claimbody}{\begin{theorem}Macro body.\end{theorem}}
\iffalse\begin{theorem}Inactive.\end{theorem}\fi
\begin{lemma}\label{dup}First result.\end{lemma}
\begin{lemma}\label{dup}Second result.\end{lemma}
\begin{theorem}From \ref{dup}, we claim something further.\end{theorem}`;
  const result = await analyzeSource(source, { limits: { maxExcerptCharacters: 30 } });
  assert.equal(result.candidates.length, 4);
  assert.equal(result.candidates[0].activity, 'INACTIVE');
  assert.equal(result.candidates.at(-1).dependencies[0].resolution, 'AMBIGUOUS_LABEL');
  assert.ok(result.candidates.at(-1).excerptTruncated);
  assert.ok(result.candidates.at(-1).anchor.endByte > result.candidates.at(-1).excerptAnchor.endByte);
  const capped = await analyzeSource(source, { limits: { maxCandidates: 1 } });
  assert.equal(capped.counts.omittedCandidates, 3);
  assert.equal(capped.frontier.omittedByFile[0].count, 3);
});

test('non-UTF-8 text keeps exact byte anchors with an explicit uncertainty', async () => {
  const bytes = encode(String.raw`\begin{theorem}Café result.\end{theorem}`);
  const latin = Uint8Array.from([...bytes].filter((_, i) => i !== [...bytes].indexOf(0xc3)));
  const result = await analyzeSource(latin), candidate = result.candidates[0];
  assert.ok(result.frontier.issues.some(i => i.code === 'ENCODING_UNCERTAIN'));
  assert.equal(candidate.anchor.endByte, latin.length);
  assert.equal(candidate.anchor.spanSha256, 'sha256:' + createHash('sha256').update(latin).digest('hex'));
});

test('UTF-8 BOM, split multibyte archive probes, author footnotes, includegraphics and newif declarations are handled conservatively', async () => {
  const source = '\uFEFF' + String.raw`\documentclass{article}
\newif\ifdraft
\author{\AND Alice\thanks{A long contribution statement {with nesting}.}\\ Institute \AND Bob\\ Another institute}
\includegraphics[width=5cm]{plot}
\begin{theorem}A source result.\end{theorem}` + 'é'.repeat(300);
  const result = await analyzeSource(source), candidate = result.candidates[0];
  assert.deepEqual(result.paper.authors, ['Alice', 'Bob']);
  assert.equal(result.includes.length, 0);
  assert.equal(candidate.activity, 'ACTIVE');
  assert.ok(!result.frontier.issues.some(i => i.code === 'UNKNOWN_CONDITIONAL'));
  assert.equal(new TextDecoder().decode(encode(source).subarray(candidate.anchor.startByte, candidate.anchor.endByte)), candidate.latex);
});

test('structural, reference, citation and label budgets fail closed', async () => {
  await assert.rejects(analyzeSource(paper, { limits: { maxStructuralSpans: 1 } }), { code: 'STRUCTURE_LIMIT' });
  await assert.rejects(analyzeSource(String.raw`\begin{theorem}\ref{a,b} result\end{theorem}`, { limits: { maxReferenceCues: 1 } }), { code: 'REFERENCE_LIMIT' });
  await assert.rejects(analyzeSource(String.raw`\begin{theorem}\cite{a,b} result\end{theorem}`, { limits: { maxCitationCues: 1 } }), { code: 'CITATION_LIMIT' });
  await assert.rejects(analyzeSource(paper, { limits: { maxLabels: 1 } }), { code: 'LABEL_LIMIT' });
});

test('unversioned IDs resolve and fetch one pinned version; real source data flows into analysis', async () => {
  const urls = [];
  const fetchImpl = async url => {
    urls.push(url);
    if (url.includes('/api/query')) return new Response('<feed><entry><id>http://arxiv.org/abs/2401.01234v3</id><title>Metadata title</title><author><name>Ada</name></author><summary>Summary</summary></entry></feed>');
    return new Response(gzipSync(paper), { headers: { 'content-type': 'application/gzip' } });
  };
  const result = await analyzeArxiv('2401.01234', { fetchImpl });
  assert.equal(urls.length, 2);
  assert.equal(urls[1], 'https://arxiv.org/src/2401.01234v3');
  assert.equal(result.paper.arxiv.version, 3);
  assert.equal(result.candidates.length, 4);
  assert.equal(result.provenance.exactVersion, 3);
  assert.match(result.provenance.fetchedAt, /^\d{4}-/);
});

test('source fetch refuses external redirects, changing versions, HTML, excessive data and response errors', async () => {
  for (const location of ['https://evil.example/src/2401.01234v1', 'https://arxiv.org/src/2401.01234v2', 'http://arxiv.org/src/2401.01234v1', 'https://arxiv.org/abs/2401.01234v1'])
    await assert.rejects(fetchArxivSource('2401.01234v1', { fetchImpl: async () => new Response(null, { status: 302, headers: { location } }) }), { code: 'UNSAFE_REDIRECT' });
  await assert.rejects(fetchArxivSource('2401.01234v1', { fetchImpl: async () => new Response('error', { headers: { 'content-type': 'text/html' } }) }), { code: 'UNSUPPORTED_SOURCE' });
  await assert.rejects(fetchArxivSource('2401.01234v1', { fetchImpl: async () => new Response('x'.repeat(100)), limits: { maxDownloadBytes: 10 } }), { code: 'BYTE_LIMIT' });
  await assert.rejects(fetchArxivSource('2401.01234v1', { fetchImpl: async () => new Response('Unavailable', { status: 503 }) }), { code: 'UPSTREAM_ERROR' });
  await assert.rejects(fetchArxivSource('2401.01234', { fetchImpl: async () => new Response('<feed/>') }), { code: 'VERSION_UNRESOLVED' });
});
