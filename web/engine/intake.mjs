/**
 * Bounded, source-linked arXiv intake. Web-platform APIs only: this module runs
 * unchanged in Node >= 22 and Cloudflare Workers. It never executes TeX or code.
 * Its output is an intake report, NOT a V3 scientific-claim or assessment record.
 */
export const ENGINE_VERSION = 'agtxiv.web-source-intake/1.0.0';
export const DEFAULT_LIMITS = Object.freeze({
  maxDownloadBytes: 8 * 1024 * 1024,
  maxExpandedBytes: 16 * 1024 * 1024,
  maxFileBytes: 2 * 1024 * 1024,
  maxTexBytes: 4 * 1024 * 1024,
  maxEntries: 1024,
  maxFiles: 512,
  maxPathBytes: 512,
  maxCandidates: 240,
  maxExcerptCharacters: 1800,
  maxIncludes: 512,
  maxCommands: 50000,
  maxStructuralSpans: 4096,
  maxReferenceCues: 1024,
  maxCitationCues: 1024,
  maxLabels: 1024,
  maxIssues: 256,
  maxAnchoredBytes: 32 * 1024 * 1024,
  timeoutMs: 30000,
  maxRedirects: 3,
});
export const ASSESSMENT_AXES = Object.freeze([
  'source_fidelity', 'mathematical_correctness', 'formal_alignment',
  'semantic_applicability', 'empirical_support', 'computational_reproducibility',
]);
export class IntakeError extends Error {
  constructor(code, message) { super(message); this.name = 'IntakeError'; this.code = code; }
}
const fail = (code, message) => { throw new IntakeError(code, message); };
const enc = new TextEncoder();
const utf8 = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
const legacyArchives = new Set(('acc-phys adap-org alg-geom ao-sci astro-ph atom-ph bayes-an chao-dyn chem-ph cmp-lg comp-gas cond-mat cs dg-ga funct-an gr-qc hep-ex hep-lat hep-ph hep-th math math-ph mtrl-th nlin nucl-ex nucl-th patt-sol physics plasm-ph q-alg q-bio quant-ph solv-int supr-con').split(' '));
function limitsFor(overrides = {}) {
  const value = { ...DEFAULT_LIMITS };
  for (const [key, n] of Object.entries(overrides)) {
    if (!Object.hasOwn(DEFAULT_LIMITS, key) || !Number.isSafeInteger(n) || n < (key === 'maxRedirects' ? 0 : 1) || n > DEFAULT_LIMITS[key])
      fail('INVALID_LIMIT', `Limit ${key} must be a positive integer no larger than the engine default.`);
    value[key] = n;
  }
  return value;
}
const bytesOf = value => typeof value === 'string' ? enc.encode(value) : value instanceof Uint8Array ? value : value instanceof ArrayBuffer ? new Uint8Array(value) : fail('INVALID_SOURCE', 'Source must be text, an ArrayBuffer, or a Uint8Array.');
async function sha256(bytes) {
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return 'sha256:' + Array.from(new Uint8Array(hash), n => n.toString(16).padStart(2, '0')).join('');
}

/** Accept a bare ID, arXiv:ID, or an HTTPS arxiv.org abs/pdf/src URL. */
export function parseArxivId(input) {
  if (typeof input !== 'string' || input.length > 256) fail('INVALID_ARXIV_ID', 'Enter one arXiv identifier or an arxiv.org paper URL.');
  let value = input.trim().replace(/^arxiv\s*:\s*/i, '');
  if (/^https?:\/\//i.test(value)) {
    let url;
    try { url = new URL(value); } catch { fail('INVALID_ARXIV_ID', 'The arXiv URL is invalid.'); }
    if (url.protocol !== 'https:' || !['arxiv.org', 'www.arxiv.org', 'export.arxiv.org'].includes(url.hostname) || url.port || url.username || url.password || url.search || url.hash)
      fail('INVALID_ARXIV_ID', 'Only HTTPS arxiv.org paper URLs without credentials, query strings, or fragments are accepted.');
    const match = url.pathname.match(/^\/(?:abs|pdf|src|e-print)\/(.+?)(?:\.pdf)?$/);
    if (!match) fail('INVALID_ARXIV_ID', 'Use an arXiv abstract, PDF, or source URL.');
    value = match[1];
  }
  const match = value.match(/^((?:\d{4}\.\d{4,5})|(?:[a-z][a-z-]*\/\d{7}))(?:v([1-9]\d{0,2}))?$/);
  if (!match) fail('INVALID_ARXIV_ID', 'Expected an arXiv ID such as 2401.01234v2 or quant-ph/0601234v1.');
  const id = match[1];
  const modern = id.includes('.');
  const digits = modern ? id.slice(0, 4) : id.split('/')[1].slice(0, 4);
  const ym = Number(digits), month = Number(digits.slice(2));
  if (month < 1 || month > 12 || (modern && (ym < 704 || id.split('.')[1].length !== (ym >= 1501 ? 5 : 4))) ||
      (!modern && (!legacyArchives.has(id.split('/')[0]) || !(ym >= 9108 || ym <= 703))))
    fail('INVALID_ARXIV_ID', 'The arXiv date, archive name, or identifier length is invalid.');
  const version = match[2] ? Number(match[2]) : null;
  const canonical = id + (version ? 'v' + version : '');
  return { id, version, canonical, sourceUrl: `https://arxiv.org/src/${canonical}`, abstractUrl: `https://arxiv.org/abs/${canonical}` };
}

function safeRemoteUrl(value, purpose, arxiv) {
  let url;
  try { url = new URL(value); } catch { fail('UNSAFE_REDIRECT', 'Source redirected to an invalid URL.'); }
  if (url.protocol !== 'https:' || !['arxiv.org', 'export.arxiv.org'].includes(url.hostname) || url.port || url.username || url.password || url.hash)
    fail('UNSAFE_REDIRECT', 'Only HTTPS arxiv.org and export.arxiv.org are allowed.');
  if (purpose === 'source') {
    if (![ `/src/${arxiv.canonical}`, `/e-print/${arxiv.canonical}` ].includes(url.pathname) || url.search)
      fail('UNSAFE_REDIRECT', 'A source redirect changed the exact paper version or source endpoint.');
  } else if (url.pathname !== '/api/query' || url.searchParams.get('id_list') !== arxiv.id || [...url.searchParams.keys()].some(k => !['id_list', 'max_results'].includes(k))) {
    fail('UNSAFE_REDIRECT', 'A metadata redirect changed the requested paper.');
  }
  return url.href;
}
async function readBounded(stream, max, deadline, controller) {
  if (!stream) fail('EMPTY_RESPONSE', 'The source response has no body.');
  const reader = stream.getReader();
  const chunks = []; let length = 0;
  try {
    for (;;) {
      const remaining = deadline - Date.now();
      if (remaining <= 0) fail('TIMEOUT', 'The source request exceeded its time limit.');
      let timer;
      const part = await Promise.race([
        reader.read(),
        new Promise((_, reject) => { timer = setTimeout(() => { controller?.abort(); reject(new IntakeError('TIMEOUT', 'The source request exceeded its time limit.')); }, remaining); }),
      ]).finally(() => clearTimeout(timer));
      if (part.done) break;
      length += part.value.byteLength;
      if (length > max) fail('BYTE_LIMIT', 'The source exceeds the byte limit.');
      chunks.push(part.value);
    }
  } catch (error) { controller?.abort(); await reader.cancel().catch(() => {}); throw error; }
  finally { reader.releaseLock(); }
  const bytes = new Uint8Array(length); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return bytes;
}
async function getRemote(url, purpose, arxiv, options, limits, deadline) {
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (options.signal?.aborted) fail('CANCELLED', 'The analysis was cancelled.');
  options.signal?.addEventListener('abort', abort, { once: true });
  const timer = setTimeout(abort, Math.max(1, deadline - Date.now()));
  try {
    for (let redirects = 0; ; redirects++) {
      url = safeRemoteUrl(url, purpose, arxiv);
      const response = await (options.fetchImpl ?? fetch)(url, { redirect: 'manual', signal: controller.signal, headers: { Accept: purpose === 'source' ? 'application/x-eprint-tar, application/gzip, application/x-tar, text/plain' : 'application/atom+xml' } });
      if ([301, 302, 303, 307, 308].includes(response.status)) {
        await response.body?.cancel();
        if (redirects >= limits.maxRedirects) fail('REDIRECT_LIMIT', 'Too many arXiv redirects.');
        const location = response.headers.get('location');
        if (!location) fail('UNSAFE_REDIRECT', 'The source redirect has no destination.');
        url = new URL(location, url).href; continue;
      }
      if (!response.ok) { await response.body?.cancel(); fail('UPSTREAM_ERROR', `arXiv returned HTTP ${response.status}. Try again later or supply an exact version.`); }
      const max = purpose === 'source' ? limits.maxDownloadBytes : Math.min(limits.maxDownloadBytes, 256 * 1024);
      const declared = response.headers.get('content-length');
      if (declared && (!/^\d+$/.test(declared) || Number(declared) > max)) { await response.body?.cancel(); fail('BYTE_LIMIT', 'The response declares too many bytes.'); }
      const bytes = await readBounded(response.body, max, deadline, controller);
      return { bytes, url, contentType: response.headers.get('content-type') ?? 'application/octet-stream' };
    }
  } catch (error) {
    if (options.signal?.aborted) fail('CANCELLED', 'The analysis was cancelled.');
    if (error.name === 'AbortError') fail('TIMEOUT', 'The source request exceeded its time limit.');
    throw error;
  } finally { clearTimeout(timer); options.signal?.removeEventListener('abort', abort); }
}
const xmlText = value => value.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();
export async function fetchArxivSource(input, options = {}) {
  const limits = limitsFor(options.limits); let arxiv = parseArxivId(input);
  const requested = arxiv.canonical, deadline = Date.now() + limits.timeoutMs;
  let metadata = null;
  if (!arxiv.version) {
    const response = await getRemote(`https://export.arxiv.org/api/query?id_list=${encodeURIComponent(arxiv.id)}&max_results=1`, 'metadata', arxiv, options, limits, deadline);
    let atom;
    try { atom = utf8.decode(response.bytes); } catch { fail('INVALID_METADATA', 'arXiv returned invalid metadata encoding.'); }
    const entry = atom.match(/<entry(?:\s[^>]*)?>([\s\S]*?)<\/entry>/)?.[1];
    const resolved = entry?.match(/<id>\s*https?:\/\/arxiv\.org\/abs\/([^<\s]+)\s*<\/id>/)?.[1];
    if (!resolved) fail('VERSION_UNRESOLVED', 'Could not resolve an exact arXiv version. Enter an identifier ending in v1, v2, etc.');
    const exact = parseArxivId(resolved);
    if (exact.id !== arxiv.id || !exact.version) fail('VERSION_UNRESOLVED', 'The arXiv response did not identify the requested exact version.');
    arxiv = exact;
    metadata = {
      title: xmlText(entry.match(/<title>([\s\S]*?)<\/title>/)?.[1] ?? ''),
      authors: [...entry.matchAll(/<author>\s*<name>([\s\S]*?)<\/name>/g)].map(m => xmlText(m[1])),
      abstract: xmlText(entry.match(/<summary>([\s\S]*?)<\/summary>/)?.[1] ?? ''),
      basis: 'ARXIV_ATOM_METADATA',
    };
  }
  const source = await getRemote(arxiv.sourceUrl, 'source', arxiv, options, limits, deadline);
  if (/text\/html|application\/pdf/i.test(source.contentType)) fail('UNSUPPORTED_SOURCE', 'arXiv returned HTML or a PDF rather than a TeX source archive.');
  return { ...source, arxiv, requested, metadata, fetchedAt: new Date().toISOString() };
}

function safePath(value, limits) {
  if (typeof value !== 'string' || !value || enc.encode(value).length > limits.maxPathBytes || /[\\\x00-\x1f\x7f]/.test(value) || value.startsWith('/') || /^[A-Za-z]:/.test(value))
    fail('UNSAFE_ARCHIVE_PATH', 'Source paths must be bounded relative POSIX paths.');
  const parts = value.split('/');
  if (parts.includes('..')) fail('UNSAFE_ARCHIVE_PATH', 'Parent traversal is forbidden in source paths.');
  const normalized = parts.filter(p => p && p !== '.').join('/');
  if (!normalized) fail('UNSAFE_ARCHIVE_PATH', 'The source path is empty.');
  return normalized;
}
function field(bytes) {
  const zero = bytes.indexOf(0); const used = zero >= 0 ? bytes.subarray(0, zero) : bytes;
  try { return utf8.decode(used); } catch { fail('UNSUPPORTED_ARCHIVE', 'Archive names and headers must use UTF-8.'); }
}
function octal(bytes, label) {
  if (bytes[0] & 128) fail('UNSUPPORTED_ARCHIVE', 'Binary tar numeric fields are not supported.');
  const value = field(bytes).trim();
  if (!/^[0-7]*$/.test(value)) fail('INVALID_ARCHIVE', `Invalid tar ${label}.`);
  const parsed = value ? parseInt(value, 8) : 0;
  if (!Number.isSafeInteger(parsed)) fail('INVALID_ARCHIVE', 'Tar numeric field exceeds the supported range.');
  return parsed;
}
function checkHeader(header) {
  const expected = octal(header.subarray(148, 156), 'checksum');
  let total = 0;
  for (let i = 0; i < 512; i++) total += i >= 148 && i < 156 ? 32 : header[i];
  if (expected !== total) fail('INVALID_ARCHIVE', 'Tar header checksum does not match.');
}
function paxFields(bytes) {
  let offset = 0; const values = {};
  while (offset < bytes.length) {
    let space = offset;
    while (space < bytes.length && bytes[space] !== 32 && space - offset < 12) space++;
    const lengthText = field(bytes.subarray(offset, space));
    if (!/^\d+$/.test(lengthText)) fail('INVALID_ARCHIVE', 'Invalid PAX record length.');
    const length = Number(lengthText), end = offset + length;
    if (!length || end > bytes.length || end <= space + 2 || bytes[end - 1] !== 10) fail('INVALID_ARCHIVE', 'Truncated PAX metadata.');
    const record = field(bytes.subarray(space + 1, end - 1));
    const equal = record.indexOf('=');
    if (equal <= 0) fail('INVALID_ARCHIVE', 'Invalid PAX metadata.');
    const key = record.slice(0, equal), value = record.slice(equal + 1);
    if (key.startsWith('GNU.sparse') || key === 'linkpath') fail('UNSUPPORTED_ARCHIVE', 'Sparse and linked source entries are forbidden.');
    if (Object.hasOwn(values, key)) fail('INVALID_ARCHIVE', 'Duplicate PAX metadata key.');
    values[key] = value; offset = end;
  }
  return values;
}
function parseTar(bytes, limits) {
  const files = new Map(), paths = new Set(); let offset = 0, entries = 0, total = 0;
  let pending = {}, global = {}, ended = false;
  while (offset + 512 <= bytes.length) {
    const header = bytes.subarray(offset, offset + 512); offset += 512;
    if (header.every(n => n === 0)) {
      if (bytes.length - offset < 512 || !bytes.subarray(offset).every(n => n === 0)) fail('INVALID_ARCHIVE', 'Tar must end with two zero blocks and no trailing data.');
      ended = true; break;
    }
    if (++entries > limits.maxEntries) fail('ENTRY_LIMIT', 'The archive has too many entries.');
    checkHeader(header);
    const type = String.fromCharCode(header[156] || 48);
    if (!['0', '5', 'x', 'g', 'L'].includes(type)) fail('UNSAFE_ARCHIVE_ENTRY', 'Only regular files, directories, and bounded path metadata are accepted; links and special files are forbidden.');
    let size = octal(header.subarray(124, 136), 'file size');
    if (!['x', 'g', 'L'].includes(type) && (pending.size ?? global.size) !== undefined) {
      const raw = pending.size ?? global.size;
      if (!/^\d+$/.test(raw) || !Number.isSafeInteger(Number(raw))) fail('INVALID_ARCHIVE', 'Invalid PAX file size.');
      size = Number(raw);
    }
    if (size > limits.maxFileBytes || offset + size > bytes.length) fail('BYTE_LIMIT', 'A tar entry is too large or truncated.');
    const data = bytes.subarray(offset, offset + size); offset += Math.ceil(size / 512) * 512;
    if (offset > bytes.length) fail('INVALID_ARCHIVE', 'Tar entry padding is truncated.');
    if (type === 'x' || type === 'g') {
      const values = paxFields(data);
      if (type === 'g') {
        if ('path' in values || 'size' in values) fail('UNSUPPORTED_ARCHIVE', 'Global PAX paths or sizes are not supported.');
        global = { ...global, ...values };
      } else pending = { ...pending, ...values };
      continue;
    }
    if (type === 'L') { pending.path = field(data).replace(/\n$/, ''); continue; }
    let name = field(header.subarray(0, 100));
    const prefix = field(header.subarray(345, 500));
    if (prefix) name = prefix + '/' + name;
    name = pending.path ?? global.path ?? name; pending = {};
    if (type === '5' && /^\.?\/$|^\.$/.test(name)) { if (size) fail('INVALID_ARCHIVE', 'Directories must not contain file bytes.'); continue; }
    const path = safePath(name, limits);
    if (paths.has(path)) fail('DUPLICATE_PATH', 'The archive repeats a normalized path.');
    for (const parent of path.split('/').slice(0, -1).map((_, i) => path.split('/').slice(0, i + 1).join('/'))) {
      if (files.has(parent)) fail('DUPLICATE_PATH', 'A source file is also used as a directory.');
    }
    if (type === '0' && [...paths].some(p => p.startsWith(path + '/'))) fail('DUPLICATE_PATH', 'A source file is also used as a directory.');
    paths.add(path);
    if (type === '5') { if (size) fail('INVALID_ARCHIVE', 'Directories must not contain file bytes.'); continue; }
    total += size;
    if (total > limits.maxExpandedBytes || files.size >= limits.maxFiles) fail('BYTE_LIMIT', 'The archive exceeds the total file or byte limit.');
    files.set(path, data);
  }
  if (!ended || Object.keys(pending).length) fail('INVALID_ARCHIVE', 'Tar is missing its terminator or contains unused path metadata.');
  return files;
}
async function unpack(input, limits) {
  const raw = bytesOf(input);
  if (!raw.length) fail('EMPTY_SOURCE', 'The source is empty.');
  if (raw.length > limits.maxDownloadBytes) fail('BYTE_LIMIT', 'The source archive exceeds the download byte limit.');
  let bytes = raw, format = 'TEX';
  if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
    try {
      bytes = await readBounded(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')), limits.maxExpandedBytes, Date.now() + limits.timeoutMs);
    } catch (error) { if (error instanceof IntakeError) throw error; fail('INVALID_GZIP', 'The gzip source could not be decoded.'); }
    format = 'GZIP_TEX';
  }
  if (bytes.length > limits.maxExpandedBytes) fail('BYTE_LIMIT', 'The expanded source exceeds the byte limit.');
  if (bytes.length >= 512 && (String.fromCharCode(...bytes.subarray(257, 263)).startsWith('ustar') || /^[0-7 ]+\x00? *$/.test(String.fromCharCode(...bytes.subarray(148, 156))))) {
    return { files: parseTar(bytes, limits), format: format === 'GZIP_TEX' ? 'TAR_GZIP' : 'TAR', raw };
  }
  if (bytes.length > limits.maxFileBytes) fail('BYTE_LIMIT', 'The TeX source exceeds the per-file byte limit.');
  if (bytes.subarray(0, 5).every((v, i) => v === [37, 80, 68, 70, 45][i]) || bytes.includes(0)) fail('UNSUPPORTED_SOURCE', 'The source is a PDF or binary format; TeX source is required.');
  return { files: new Map([['main.tex', bytes]]), format, raw };
}

function sourceText(bytes) {
  try { return { text: utf8.decode(bytes), encoding: 'UTF-8', uncertain: false }; }
  catch {
    let text = '';
    for (let i = 0; i < bytes.length; i += 8192) text += String.fromCharCode(...bytes.subarray(i, i + 8192));
    return { text, encoding: 'BYTE_PRESERVING_LATIN1_FALLBACK', uncertain: true };
  }
}
const blank = value => value.replace(/[^\r\n]/g, ' ');
function commentsMasked(text) {
  let result = '', start = 0;
  for (let i = 0; i < text.length; i++) {
    if (text[i] !== '%') continue;
    let slashes = 0; for (let j = i - 1; j >= 0 && text[j] === '\\'; j--) slashes++;
    if (slashes % 2) continue;
    let end = text.indexOf('\n', i); if (end < 0) end = text.length;
    result += text.slice(start, i) + blank(text.slice(i, end)); start = end; i = end;
  }
  return result + text.slice(start);
}
function groupAt(text, start, open = '{', close = '}') {
  let pos = start; while (/\s/.test(text[pos] ?? '') && pos < text.length) pos++;
  if (text[pos] !== open) return null;
  const begin = pos++; let depth = 1;
  while (pos < text.length) {
    if (text[pos] === '\\') { pos += 2; continue; }
    if (text[pos] === open) depth++;
    if (text[pos] === close && --depth === 0) return { value: text.slice(begin + 1, pos), start: begin, end: pos + 1 };
    // The decrement above must only happen for a closing delimiter.
    pos++;
  }
  return null;
}
function maskRanges(text, ranges) {
  const chunks = []; let cursor = 0;
  for (const { start, end } of [...ranges].sort((a, b) => a.start - b.start || b.end - a.end)) {
    if (end <= cursor) continue;
    if (start > cursor) chunks.push(text.slice(cursor, start));
    chunks.push(blank(text.slice(Math.max(start, cursor), end))); cursor = end;
  }
  chunks.push(text.slice(cursor)); return chunks.join('');
}
function staticSyntax(text, limits) {
  let masked = commentsMasked(text); const issues = [], opaque = [];
  let commandCount = 0;
  for (const command of masked.matchAll(/\\(?:[A-Za-z@]+|.)/g)) {
    if (++commandCount > limits.maxCommands) fail('COMMAND_LIMIT', 'The TeX source contains too many commands.');
    if (command[0].length > 201) fail('COMMAND_LIMIT', 'A TeX command name exceeds the 200-character limit.');
  }
  const opaqueRE = /\\begin\s*\{(verbatim\*?|Verbatim|lstlisting|minted|comment)\}/g;
  let previousEnd = 0;
  for (const m of masked.matchAll(opaqueRE)) {
    if (m.index < previousEnd) continue;
    const close = new RegExp('\\\\end\\s*\\{' + m[1].replace('*', '\\*') + '\\}', 'g'); close.lastIndex = m.index + m[0].length;
    const ending = close.exec(masked), end = ending ? ending.index + ending[0].length : masked.length;
    opaque.push({ start: m.index, end, kind: 'OPAQUE_ENVIRONMENT' }); previousEnd = end;
    if (!ending) issues.push({ code: 'UNCLOSED_OPAQUE_ENVIRONMENT', offset: m.index, detail: m[1] });
  }
  masked = maskRanges(masked, opaque);
  const verbRE = /\\verb\*?([^\sA-Za-z])/g;
  const verbs = []; previousEnd = 0;
  for (const m of masked.matchAll(verbRE)) {
    if (m.index < previousEnd) continue;
    const endIndex = masked.indexOf(m[1], m.index + m[0].length), lineEnd = masked.indexOf('\n', m.index);
    const end = endIndex >= 0 && (lineEnd < 0 || endIndex < lineEnd) ? endIndex + 1 : (lineEnd < 0 ? masked.length : lineEnd);
    verbs.push({ start: m.index, end, kind: 'OPAQUE_VERBATIM' }); previousEnd = end;
  }
  opaque.push(...verbs); masked = maskRanges(masked, verbs);
  const conditionalDeclarations = [...masked.matchAll(/\\newif\s*\\if[A-Za-z@]+/g)].map(m => ({ start: m.index, end: m.index + m[0].length, kind: 'MACRO_DEFINITION' }));
  opaque.push(...conditionalDeclarations); masked = maskRanges(masked, conditionalDeclarations);
  const macroRE = /\\(?:newcommand|renewcommand|providecommand|DeclareRobustCommand|newenvironment|renewenvironment)\*?|\\(?:gdef|edef|xdef|def)\b/g;
  const macros = []; previousEnd = 0;
  for (const m of masked.matchAll(macroRE)) {
    if (m.index < previousEnd) continue;
    let cursor = m.index + m[0].length;
    const name = groupAt(masked, cursor);
    if (name) cursor = name.end;
    else { const command = masked.slice(cursor).match(/^\s*\\[A-Za-z@]+/); if (command) cursor += command[0].length; }
    for (let count = 0; count < 2; count++) { const opt = groupAt(masked, cursor, '[', ']'); if (opt) cursor = opt.end; }
    if (/\\(?:gdef|edef|xdef|def)$/.test(m[0])) { const open = masked.indexOf('{', cursor); if (open >= 0 && open - cursor < 100) cursor = open; }
    const body = groupAt(masked, cursor);
    if (body) {
      cursor = body.end;
      if (/environment/.test(m[0])) { const second = groupAt(masked, cursor); if (second) cursor = second.end; }
      macros.push({ start: m.index, end: cursor, kind: 'MACRO_DEFINITION' }); previousEnd = cursor;
    } else {
      issues.push({ code: 'UNRESOLVED_MACRO_DEFINITION', offset: m.index, detail: 'Definition was not safely delimited; the remaining file is opaque.' });
      macros.push({ start: m.index, end: masked.length, kind: 'UNDELIMITED_MACRO_REMAINDER' }); break;
    }
  }
  opaque.push(...macros); masked = maskRanges(masked, macros);
  const states = [], stack = []; let state = 'ACTIVE', count = 0;
  const commandRE = /\\([A-Za-z@]+|.)/g;
  for (const m of masked.matchAll(commandRE)) {
    if (++count > limits.maxCommands) fail('COMMAND_LIMIT', 'The TeX source contains too many commands.');
    const name = m[1];
    if (name === 'fi') {
      if (!stack.length) issues.push({ code: 'UNBALANCED_CONDITIONAL', offset: m.index, detail: 'Unmatched \\fi.' });
      else { state = stack.pop().outer; states.push({ offset: m.index + m[0].length, state }); }
    } else if (name === 'else') {
      const current = stack.at(-1);
      if (!current || current.other) issues.push({ code: 'UNBALANCED_CONDITIONAL', offset: m.index, detail: 'Unmatched or repeated \\else.' });
      else { current.other = true; state = current.outer === 'INACTIVE' ? 'INACTIVE' : current.condition === null ? 'UNKNOWN' : current.condition ? 'INACTIVE' : current.outer; states.push({ offset: m.index + m[0].length, state }); }
    } else if (name.startsWith('if') && name !== 'ifthenelse') {
      const condition = name === 'iftrue' ? true : name === 'iffalse' ? false : null;
      stack.push({ outer: state, condition, other: false });
      if (stack.length > 128) fail('CONDITIONAL_LIMIT', 'The conditional nesting exceeds the limit.');
      state = state === 'INACTIVE' ? 'INACTIVE' : condition === false ? 'INACTIVE' : condition === null ? 'UNKNOWN' : state;
      states.push({ offset: m.index + m[0].length, state });
      if (condition === null) issues.push({ code: 'UNKNOWN_CONDITIONAL', offset: m.index, detail: `\\${name} was not evaluated.` });
    }
  }
  if (stack.length) issues.push({ code: 'UNBALANCED_CONDITIONAL', offset: text.length, detail: 'One or more conditionals were not closed.' });
  if (issues.length > limits.maxIssues) fail('ISSUE_LIMIT', 'The source has too many unresolved syntax issues.');
  const activityAt = offset => { let state = 'ACTIVE'; for (const point of states) { if (point.offset > offset) break; state = point.state; } return state; };
  return { masked, issues, opaque, activityAt, commandCount };
}

/** Text is a reading aid only. Original bounded TeX and byte anchors remain authoritative. */
export function readableTex(value) {
  return commentsMasked(value)
    .replace(/\\(?:label|index|bibliographystyle)\s*\{[^}]*\}/g, '')
    .replace(/\\(?:begin|end)\s*\{[^}]*\}(?:\[[^\]]*\])?/g, '')
    .replace(/\\(?:cite[a-zA-Z]*|ref|eqref|autoref|cref|Cref)\*?(?:\[[^\]]*\])*\s*\{([^}]*)\}/g, ' [$1] ')
    .replace(/\\(?:title|author|textbf|textit|emph|textrm|mathrm|mathbf|mathit|operatorname|text|thanks)\*?\s*\{([^{}]*)\}/g, '$1')
    .replace(/\\(?:quad|qquad|,|;|!| |newline|par)\b/g, ' ')
    .replace(/\\(?:maketitle|centering|noindent)\b/g, '')
    .replace(/\\([%&#_{}])/g, '$1').replace(/\\\\/g, ' ')
    .replace(/[{}]/g, '').replace(/\$+/g, '').replace(/\s+/g, ' ').trim();
}
function collectCommand(text, name, max = 20, raw = false) {
  const values = [];
  for (const match of text.matchAll(new RegExp('\\\\' + name + '\\s*', 'g'))) {
    const group = groupAt(text, match.index + match[0].length);
    if (group) values.push(raw ? group.value : readableTex(group.value));
    if (values.length >= max) break;
  }
  return values;
}
function authorNames(text) {
  return collectCommand(text, 'author', 30, true).flatMap(value => {
    const ranges = [];
    for (const m of value.matchAll(/\\(?:thanks|footnote|textsuperscript|affiliation|email)(?![A-Za-z@])\s*/g)) {
      const group = groupAt(value, m.index + m[0].length);
      if (group) ranges.push({ start: m.index, end: group.end });
    }
    value = maskRanges(value, ranges).replace(/\\footnotemark(?:\[[^\]]*\])?/g, '');
    return value.split(/\\(?:and|And|AND)(?![A-Za-z@])/).map(part => readableTex(part.split(/\\\\|\r?\n\s*\\(?:texttt|email|affiliation)/)[0])).filter(Boolean);
  });
}
const typeMap = new Map(Object.entries({ theorem: 'THEOREM', thm: 'THEOREM', lemma: 'LEMMA', lem: 'LEMMA', proposition: 'PROPOSITION', prop: 'PROPOSITION', corollary: 'COROLLARY', cor: 'COROLLARY', definition: 'DEFINITION', defn: 'DEFINITION', def: 'DEFINITION', conjecture: 'CONJECTURE', conject: 'CONJECTURE', claim: 'CLAIM', assumption: 'ASSUMPTION', remark: 'REMARK', observation: 'OBSERVATION', example: 'EXAMPLE', equation: 'EQUATION', align: 'EQUATION', alignat: 'EQUATION', gather: 'EQUATION', multline: 'EQUATION', eqnarray: 'EQUATION', displaymath: 'EQUATION' }));
function byteMap(text, encoding) {
  const map = new Uint32Array(text.length + 1); let byte = 0;
  for (let i = 0; i < text.length; i++) {
    map[i] = byte;
    if (encoding !== 'UTF-8') { byte++; continue; }
    const cp = text.codePointAt(i);
    if (cp > 0xffff) { map[++i] = byte; byte += 4; }
    else byte += cp < 0x80 ? 1 : cp < 0x800 ? 2 : 3;
  }
  map[text.length] = byte; return map;
}
function lineCheckpoints(text) {
  const map = new Uint32Array(Math.floor(text.length / 1024) + 1); let line = 1;
  for (let i = 0; i < text.length; i++) { if (i % 1024 === 0) map[i / 1024] = line; if (text[i] === '\n') line++; }
  if (text.length % 1024 === 0) map[text.length / 1024] = line;
  return map;
}
function lineAt(file, offset) {
  const checkpoint = Math.floor(offset / 1024);
  return file.lineCheckpoints[checkpoint] + (file.text.slice(checkpoint * 1024, offset).match(/\n/g)?.length ?? 0);
}
const boundedExcerpt = (text, limit) => { let end = Math.min(text.length, limit); if (end && /[\uD800-\uDBFF]/.test(text[end - 1])) end--; return text.slice(0, end); };
function candidateSpans(file, declaredTypes, limits) {
  const { masked } = file.syntax, spans = [], stack = [];
  for (const m of masked.matchAll(/\\(begin|end)\s*\{([^}]+)\}/g)) {
    const env = m[2].replace(/\*$/, ''), type = declaredTypes.get(env) ?? typeMap.get(env.toLowerCase());
    if (m[2].length > 100) fail('ENVIRONMENT_LIMIT', 'An environment name exceeds the 100-character limit.');
    if (m[1] === 'begin') { stack.push({ name: m[2], start: m.index, type, env }); if (stack.length > 128) fail('ENVIRONMENT_LIMIT', 'The environment nesting exceeds the limit.'); continue; }
    const index = stack.findLastIndex(item => item.name === m[2]);
    if (index < 0) { file.syntax.issues.push({ code: 'UNMATCHED_ENVIRONMENT_END', offset: m.index, detail: m[2] }); continue; }
    if (index !== stack.length - 1) file.syntax.issues.push({ code: 'CROSSED_ENVIRONMENTS', offset: m.index, detail: m[2] });
    const opened = stack[index]; stack.splice(index);
    if (type && opened.type) spans.push({ start: opened.start, end: m.index + m[0].length, type, environment: env });
    if (spans.length > limits.maxStructuralSpans) fail('STRUCTURE_LIMIT', 'The source contains too many structural candidates.');
  }
  for (const item of stack) file.syntax.issues.push({ code: 'UNCLOSED_ENVIRONMENT', offset: item.start, detail: item.name });
  for (const m of masked.matchAll(/\\\[([\s\S]*?)\\\]|\$\$([\s\S]*?)\$\$/g)) { spans.push({ start: m.index, end: m.index + m[0].length, type: 'EQUATION', environment: 'display-delimiter' }); if (spans.length > limits.maxStructuralSpans) fail('STRUCTURE_LIMIT', 'The source contains too many structural candidates.'); }
  const envelopes = [...spans].sort((a, b) => a.start - b.start); let position = 0;
  for (const m of masked.matchAll(/[^\r\n](?:[^\r\n]|\r?\n(?!\s*\r?\n))*/g)) {
    while (position < envelopes.length && envelopes[position].end <= m.index) position++;
    if (position < envelopes.length && m.index + m[0].length > envelopes[position].start) continue;
    const plain = readableTex(m[0]);
    if (plain.length >= 40 && /\b(?:we (?:show|prove|establish|demonstrate|find|propose|define|conclude)|our (?:result|theorem)|it follows|therefore|thus)\b/i.test(plain))
      spans.push({ start: m.index, end: m.index + m[0].length, type: 'ASSERTION_PARAGRAPH', environment: null });
    if (spans.length > limits.maxStructuralSpans) fail('STRUCTURE_LIMIT', 'The source contains too many structural candidates.');
  }
  return spans.sort((a, b) => a.start - b.start || a.end - b.end || a.type.localeCompare(b.type));
}

export async function analyzeSource(input, options = {}) {
  const limits = limitsFor(options.limits), unpacked = await unpack(input, limits);
  const archiveSha256 = await sha256(unpacked.raw), files = [], parsed = new Map(); let texTotal = 0, totalCommands = 0;
  for (const [path, bytes] of [...unpacked.files].sort(([a], [b]) => a.localeCompare(b, 'en'))) {
    const isTex = /\.(?:tex|ltx)$/i.test(path), hash = await sha256(bytes);
    const inventory = { path, sha256: hash, sizeBytes: bytes.length, role: isTex ? 'TEX' : /\.(bib|bbl)$/i.test(path) ? 'BIBLIOGRAPHY' : 'UNSUPPORTED_RESOURCE', activity: 'UNCLASSIFIED', publishedRenderingActivity: 'UNASSESSED', analysis: isTex ? 'BOUNDED_STATIC_TEX' : 'HASHED_ONLY' };
    files.push(inventory);
    if (!isTex) continue;
    texTotal += bytes.length;
    if (texTotal > limits.maxTexBytes) fail('TEX_BYTE_LIMIT', 'The TeX sources exceed the analysis byte limit.');
    if (bytes.includes(0)) { inventory.analysis = 'BINARY_TEX_UNSUPPORTED'; continue; }
    const decoded = sourceText(bytes);
    const syntax = staticSyntax(decoded.text, limits); totalCommands += syntax.commandCount;
    if (totalCommands > limits.maxCommands) fail('COMMAND_LIMIT', 'The TeX source set contains too many commands.');
    parsed.set(path, { path, bytes, hash, ...decoded, syntax, inventory });
  }
  if (!parsed.size) fail('NO_TEX_SOURCE', 'No readable .tex or .ltx source was found in the archive.');
  const roots = [...parsed.values()].filter(f => /\\documentclass(?:\[[^\]]*\])?\s*\{|\\documentstyle(?:\[[^\]]*\])?\s*\{/.test(f.syntax.masked));
  roots.sort((a, b) => Number(/(?:^|\/)main\.tex$/i.test(b.path)) - Number(/(?:^|\/)main\.tex$/i.test(a.path)) || a.path.split('/').length - b.path.split('/').length || a.path.localeCompare(b.path));
  const main = options.main ? safePath(options.main, limits) : roots[0]?.path ?? [...parsed.keys()][0];
  if (!parsed.has(main)) fail('MISSING_MAIN', 'The selected main TeX source is missing.');
  const declaredTypes = new Map(typeMap), issues = [], includes = [], reach = new Map([[main, 'ACTIVE']]);
  if (roots.length !== 1 && !options.main) issues.push({ code: roots.length ? 'AMBIGUOUS_MAIN' : 'MAIN_HEURISTIC', path: main, detail: roots.length ? 'Multiple document roots exist; main.tex and then shortest path were preferred.' : 'No document class found; the first TeX path was selected.' });
  for (const file of parsed.values()) {
    for (const m of file.syntax.masked.matchAll(/\\newtheorem\*?\s*\{([^}]+)\}(?:\[[^\]]*\])?\s*\{([^}]+)\}/g)) {
      const inferred = typeMap.get(readableTex(m[2]).toLowerCase());
      if (inferred) declaredTypes.set(m[1], inferred);
    }
    for (const m of file.syntax.masked.matchAll(/\\(?:input|include|subfile)(?![A-Za-z@])\s*(?:\{([^}]+)\}|([^\s{}%]+))/g)) {
      if (includes.length >= limits.maxIncludes) fail('INCLUDE_LIMIT', 'The source contains too many include directives.');
      const rawTarget = (m[1] ?? m[2]).trim(), localActivity = file.syntax.activityAt(m.index);
      if (enc.encode(rawTarget).length > limits.maxPathBytes) fail('INCLUDE_LIMIT', 'An include target exceeds the path-byte limit.');
      const edge = { source: file.path, requested: rawTarget, target: null, activity: localActivity, offset: m.index, end: m.index + m[0].length, resolution: 'UNRESOLVED' };
      if (/[\\#$~]/.test(rawTarget)) edge.resolution = 'DYNAMIC_INCLUDE_UNRESOLVED';
      else {
        let safe;
        try { safe = safePath(rawTarget, limits); } catch { edge.resolution = 'UNSAFE_INCLUDE_REJECTED'; }
        if (safe) {
          const variants = /\.[^/]+$/.test(safe) ? [safe] : [safe + '.tex', safe];
          const mainDir = main.includes('/') ? main.slice(0, main.lastIndexOf('/') + 1) : '';
          const fileDir = file.path.includes('/') ? file.path.slice(0, file.path.lastIndexOf('/') + 1) : '';
          const matches = [...new Set([mainDir, '', fileDir].flatMap(prefix => variants.map(name => prefix + name)).filter(name => parsed.has(name)))];
          if (matches.length === 1) { edge.target = matches[0]; edge.resolution = 'STATIC_PATH_MATCH'; }
          else edge.resolution = matches.length ? 'AMBIGUOUS_INCLUDE' : 'MISSING_INCLUDE';
        }
      }
      includes.push(edge);
    }
  }
  for (let pass = 0; pass < parsed.size; pass++) {
    let changed = false;
    for (const edge of includes) {
      if (!edge.target || !reach.has(edge.source) || edge.activity === 'INACTIVE') continue;
      const activity = reach.get(edge.source) === 'ACTIVE' && edge.activity === 'ACTIVE' ? 'ACTIVE' : 'UNKNOWN';
      if (!reach.has(edge.target) || (reach.get(edge.target) === 'UNKNOWN' && activity === 'ACTIVE')) { reach.set(edge.target, activity); changed = true; }
    }
    if (!changed) break;
  }
  const fileAnchors = new Map();
  for (const file of parsed.values()) {
    file.inventory.activity = reach.get(file.path) ?? 'UNCLASSIFIED'; file.inventory.encoding = file.encoding;
    if (file.uncertain) issues.push({ code: 'ENCODING_UNCERTAIN', path: file.path, detail: 'Non-UTF-8 bytes are shown with a byte-preserving Latin-1 fallback.' });
    fileAnchors.set(file.path, byteMap(file.text, file.encoding));
    file.lineCheckpoints = lineCheckpoints(file.text);
  }
  let totalAnchoredBytes = 0;
  async function anchor(file, start, end) {
    const map = fileAnchors.get(file.path), startByte = map[start], endByte = map[end];
    totalAnchoredBytes += endByte - startByte;
    if (totalAnchoredBytes > limits.maxAnchoredBytes) fail('ANCHOR_BYTE_LIMIT', 'Overlapping source spans exceed the total hashing byte limit.');
    return { path: file.path, sourceSha256: file.hash, startByte, endByte, startLine: lineAt(file, start), endLine: lineAt(file, end), spanSha256: await sha256(file.bytes.subarray(startByte, endByte)) };
  }
  for (const edge of includes) {
    edge.anchor = await anchor(parsed.get(edge.source), edge.offset, edge.end); delete edge.offset; delete edge.end;
    if (edge.resolution !== 'STATIC_PATH_MATCH') issues.push({ code: edge.resolution, path: edge.source, detail: edge.requested, anchor: edge.anchor });
    if (!reach.has(edge.source)) edge.activity = 'UNKNOWN';
    else if (reach.get(edge.source) === 'UNKNOWN' && edge.activity === 'ACTIVE') edge.activity = 'UNKNOWN';
  }
  const ordered = [...parsed.values()].sort((a, b) => (a.path === main ? -1 : b.path === main ? 1 : 0) || a.path.localeCompare(b.path));
  const candidates = [], omittedByFile = [], unclassifiedSpans = [];
  const candidateInternals = new Map(); let discovered = 0, totalLabels = 0;
  for (const file of ordered) {
    const spans = candidateSpans(file, declaredTypes, limits); discovered += spans.length;
    if (discovered > limits.maxStructuralSpans) fail('STRUCTURE_LIMIT', 'The source set contains too many structural candidates.');
    let omitted = 0;
    for (const span of spans) {
      if (candidates.length >= limits.maxCandidates) { omitted++; continue; }
      const raw = file.text.slice(span.start, span.end), latex = boundedExcerpt(raw, limits.maxExcerptCharacters);
      const location = await anchor(file, span.start, span.end), id = 'candidate:' + (await sha256(enc.encode(`${ENGINE_VERSION}\n${file.path}\n${file.hash}\n${location.startByte}:${location.endByte}\n${span.type}`))).slice(7, 31);
      const localActivity = file.syntax.activityAt(span.start), activity = localActivity === 'INACTIVE' ? 'INACTIVE' : reach.get(file.path) === 'ACTIVE' && localActivity === 'ACTIVE' ? 'ACTIVE' : 'UNKNOWN';
      const maskedSpan = file.syntax.masked.slice(span.start, span.end);
      const labels = [...new Set([...maskedSpan.matchAll(/\\label\s*\{([^}]+)\}/g)].map(m => m[1].trim()))];
      totalLabels += labels.length;
      if (totalLabels > limits.maxLabels || labels.some(label => label.length > 200)) fail('LABEL_LIMIT', 'The source contains too many or excessively long labels.');
      const candidate = { id, type: span.type, environment: span.environment, text: readableTex(latex), latex, excerptTruncated: latex.length < raw.length, anchor: location, excerptAnchor: await anchor(file, span.start, span.start + latex.length), labels, activity, interpretation: 'SOURCE_LINKED_CANDIDATE_NOT_SCIENTIFIC_APPROVAL', dependencies: [], citationCues: [], assessments: Object.fromEntries(ASSESSMENT_AXES.map(axis => [axis, 'NO_ASSESSMENT'])) };
      candidateInternals.set(id, { file, span, maskedSpan }); candidates.push(candidate);
    }
    if (omitted) omittedByFile.push({ path: file.path, count: omitted });
    // Exact byte ranges outside selected candidate envelopes remain explicitly unclassified.
    const selected = candidates.filter(c => c.anchor.path === file.path).map(c => [c.anchor.startByte, c.anchor.endByte]).sort((a, b) => a[0] - b[0]);
    let cursor = 0;
    for (const [start, end] of selected) { if (start > cursor) unclassifiedSpans.push({ path: file.path, startByte: cursor, endByte: start }); cursor = Math.max(cursor, end); }
    if (cursor < file.bytes.length) unclassifiedSpans.push({ path: file.path, startByte: cursor, endByte: file.bytes.length });
    for (const issue of file.syntax.issues) issues.push({ ...issue, path: file.path, byteOffset: fileAnchors.get(file.path)[issue.offset], offset: undefined });
    if (issues.length > limits.maxIssues) fail('ISSUE_LIMIT', 'The source set has too many unresolved syntax issues.');
  }
  const byLabel = new Map();
  for (const candidate of candidates) for (const label of candidate.labels) {
    if (!byLabel.has(label)) byLabel.set(label, []);
    byLabel.get(label).push(candidate);
  }
  let totalReferences = 0, totalCitations = 0;
  for (const candidate of candidates) {
    const { file, span, maskedSpan } = candidateInternals.get(candidate.id);
    for (const m of maskedSpan.matchAll(/\\(ref|eqref|autoref|[cC]ref|[vV]ref)\*?\s*\{([^}]+)\}/g)) {
      const evidence = await anchor(file, span.start + m.index, span.start + m.index + m[0].length);
      for (const label of m[2].split(',').map(s => s.trim()).filter(Boolean)) {
        if (++totalReferences > limits.maxReferenceCues || label.length > 200) fail('REFERENCE_LIMIT', 'The source contains too many or excessively long reference cues.');
        let targets = byLabel.get(label) ?? [];
        // A nested equation's label also lies in its enclosing theorem. Prefer
        // the narrowest envelope only when all alternatives actually nest.
        if (targets.length > 1) {
          const narrow = [...targets].sort((a, b) => a.anchor.endByte - a.anchor.startByte - (b.anchor.endByte - b.anchor.startByte))[0];
          if (targets.every(t => t.anchor.path === narrow.anchor.path && t.anchor.startByte <= narrow.anchor.startByte && t.anchor.endByte >= narrow.anchor.endByte)) targets = [narrow];
        }
        candidate.dependencies.push({ relation: 'LOCAL_REFERENCE', label, command: m[1], targetIds: targets.map(c => c.id), resolution: targets.length === 1 ? 'RESOLVED_CANDIDATE' : targets.length ? 'AMBIGUOUS_LABEL' : 'UNRESOLVED_LABEL', evidence, meaning: 'A textual reference was observed; logical support has not been assessed.' });
      }
    }
    for (const m of maskedSpan.matchAll(/\\(cite[A-Za-z]*)\*?(?:\[[^\]]*\])*\s*\{([^}]+)\}/g)) {
      const keys = m[2].split(',').map(s => s.trim()).filter(Boolean); totalCitations += keys.length;
      if (totalCitations > limits.maxCitationCues || keys.some(key => key.length > 200)) fail('CITATION_LIMIT', 'The source contains too many or excessively long citation cues.');
      candidate.citationCues.push({ keys, command: m[1], evidence: await anchor(file, span.start + m.index, span.start + m.index + m[0].length), status: 'BIBLIOGRAPHIC_CUE_UNASSESSED' });
    }
  }
  const mainFile = parsed.get(main), title = collectCommand(mainFile.syntax.masked, 'title', 1)[0] ?? options.metadata?.title ?? 'Untitled source submission';
  const authors = authorNames(mainFile.syntax.masked);
  const abstractMatch = mainFile.syntax.masked.match(/\\begin\s*\{abstract\}([\s\S]*?)\\end\s*\{abstract\}/);
  const abstract = abstractMatch ? readableTex(boundedExcerpt(abstractMatch[1], 3000)) : (collectCommand(mainFile.syntax.masked, 'abstract', 1)[0] ?? options.metadata?.abstract ?? '');
  const metadataAnchors = { title: [], authors: [], abstract: [] };
  for (const [key, command] of [['title', 'title'], ['authors', 'author'], ['abstract', 'abstract']]) {
    for (const m of mainFile.syntax.masked.matchAll(new RegExp('\\\\' + command + '(?![A-Za-z@])\\s*', 'g'))) {
      const group = groupAt(mainFile.syntax.masked, m.index + m[0].length);
      if (group) metadataAnchors[key].push(await anchor(mainFile, m.index, group.end));
      if (metadataAnchors[key].length >= (key === 'authors' ? 30 : 1)) break;
    }
  }
  if (abstractMatch) metadataAnchors.abstract = [await anchor(mainFile, abstractMatch.index, abstractMatch.index + abstractMatch[0].length)];
  const manifestSha256 = await sha256(enc.encode(files.map(f => `${f.path}\0${f.sha256}\0${f.sizeBytes}`).join('\n')));
  const analysisId = 'analysis:' + (await sha256(enc.encode(JSON.stringify({ engine: ENGINE_VERSION, manifestSha256, main, limits })))).slice(7, 39);
  const arxiv = options.arxiv ? parseArxivId(typeof options.arxiv === 'string' ? options.arxiv : options.arxiv.canonical) : null;
  const macroDefinitions = [...parsed.values()].reduce((n, file) => n + file.syntax.opaque.filter(item => item.kind === 'MACRO_DEFINITION').length, 0);
  return {
    schemaVersion: ENGINE_VERSION, analysisId, status: 'SOURCE_LINKED_CANDIDATES',
    paper: { title: boundedExcerpt(title, 500), authors: (authors.length ? authors : options.metadata?.authors ?? []).map(a => boundedExcerpt(a, 500)).slice(0, 30), abstract: boundedExcerpt(abstract, 3000), arxiv, metadataBasis: 'STATIC_TEX_WITH_OPTIONAL_ARXIV_METADATA_FALLBACK', metadataAnchors },
    main, candidates, sources: files, includes,
    counts: { sources: files.length, texFiles: parsed.size, discoveredCandidates: discovered, returnedCandidates: candidates.length, omittedCandidates: discovered - candidates.length, localReferences: candidates.reduce((n, c) => n + c.dependencies.length, 0) },
    frontier: {
      issues, omittedByFile, unclassifiedSpans,
      unclassifiedFiles: files.filter(f => f.activity === 'UNCLASSIFIED').map(f => f.path),
      unsupportedContent: files.filter(f => f.analysis !== 'BOUNDED_STATIC_TEX').map(f => ({ path: f.path, analysis: f.analysis })),
      inactiveCandidates: candidates.filter(c => c.activity === 'INACTIVE').map(c => c.id),
      uncertainCandidates: candidates.filter(c => c.activity === 'UNKNOWN').map(c => c.id),
      macroDefinitions, macroSemantics: 'NOT_EXECUTED_OR_EXPANDED',
      sourceCompleteness: 'ARCHIVE_INVENTORIED_EXTERNAL_AND_PUBLICATION_COMPLETENESS_UNASSESSED',
      scientificAssessment: 'NOT_PERFORMED',
      limitations: [
        'Static TeX syntax discovers candidate envelopes and reference cues; it does not prove their scientific meaning or correctness.',
        'TeX, macros, packages, source code, external commands, and PDFs were not executed or rendered.',
        'Displayed prose is a lossy reading aid. Byte anchors and hashes refer to original file bytes; excerpts may be truncated.',
        'Static include reachability is not proof that content appeared in the published paper. Unknown conditions and unused files remain visible.',
        'Citations are keys observed in TeX, not verified bibliographic identities. Local references are not established proof dependencies.',
        'No scientific claims have been admitted to a knowledge base and all six assessment axes remain NO_ASSESSMENT.',
        'The result stores hashes, source ranges, and bounded excerpts; it does not retain the archive. Re-fetch the exact version to verify bytes.',
      ],
    },
    provenance: { engine: ENGINE_VERSION, method: 'BOUNDED_STATIC_TEX_STRUCTURE', archiveSha256, manifestSha256, archiveFormat: unpacked.format, archiveBytes: unpacked.raw.length, sourceUrl: options.sourceUrl ?? null, fetchedAt: options.fetchedAt ?? null, exactVersion: arxiv?.version ?? null, sourceStored: false, anchorConvention: 'Zero-based byte offsets, half-open [startByte,endByte); line numbers are one-based.' },
    limits,
  };
}

export async function analyzeArxiv(input, options = {}) {
  const fetched = await fetchArxivSource(input, options);
  return analyzeSource(fetched.bytes, { ...options, arxiv: fetched.arxiv, metadata: fetched.metadata, sourceUrl: fetched.url, fetchedAt: fetched.fetchedAt });
}
