# Canvas UI source snapshot

`GridVanilla.ts` is the original vanilla component from
https://canvasui.dev/r/grid-vanilla.json, retrieved 2026-09-17.
See `../../public/workspace/vendor/NOTICE.md` and the retained license at
`../../public/workspace/vendor/canvas-ui/LICENSE.md`.

The source is retained for reproducible development; the application serves the
committed JavaScript runtime. To regenerate the runtime with Node 26:

```sh
node --input-type=module - <<'JS'
import { stripTypeScriptTypes } from 'node:module';
import { readFile, writeFile } from 'node:fs/promises';
const source = await readFile('vendor-src/canvas-ui/GridVanilla.ts', 'utf8');
const js = stripTypeScriptTypes(source).replace('"../rect-cache"', '"./rect-cache.js"');
await writeFile('public/workspace/vendor/canvas-ui/grid.js',
  '// Canvas UI Grid. Source and licensing: /workspace/vendor/NOTICE.md\n' + js);
JS
```

Run this from `web/` only when regenerating the asset. This is source
transformation; it does not typecheck, run tests, or establish browser support.
