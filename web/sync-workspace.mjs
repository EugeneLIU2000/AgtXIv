import { cp, mkdir, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.dirname(fileURLToPath(import.meta.url));
const source = path.resolve(root, '../schema v0.2');
const target = path.join(root, 'public/workspace/data');

// Publication copies preserve source bytes. Standalone website checkouts use
// their retained copies; this is authoring, not a conformance check.
export async function syncWorkspace() {
  try { await stat(source); } catch (error) {
    if (error.code === 'ENOENT') return;
    throw error;
  }
  await mkdir(target, { recursive: true });
  for (const [from, to] of [
    ['examples/paper-minimal/output.json', 'paper-minimal.json'],
    ['examples/paper-minimal/source.txt', 'source.txt'],
    ['CONTRACT.md', 'contract.md'],
    ['HOST.md', 'host.md'],
    ['READ-INTERFACE.md', 'read-interface.md'],
    ...['common', 'task', 'items', 'output', 'run'].map(name => [`schemas/${name}.schema.json`, `${name}.schema.json`]),
  ]) await cp(path.join(source, from), path.join(target, to));
}
