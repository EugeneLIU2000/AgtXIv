# Repository organization and evidence preservation

**Date:** 2026-09-08. **Scope:** first recoverable organization pass for the publishable-release goal.

The working tree already contained modified and untracked user work. This pass preserves that work and records each operation in [repository-archive-manifest.json](repository-archive-manifest.json). It changes file locations and adds a local preservation copy; it does not change scientific assessments or establish redistribution permission.

## Preserved historical candidate evidence

The complete five-file directory `tmp/v3-real-candidate/capture-g7f2mr3a/` was copied to `local-archive/v3-real-candidate/capture-g7f2mr3a/`. Both SQLite files include retained historical records and byte stores; the JSON files preserve build, query and replay outputs. All five originals matched the byte sizes and SHA-256 values in the existing [closure receipt](../evidence/v3-real-candidate/closure-verification.json) before copying. Every destination then matched its source. The originals remain in place, so existing paths and historical receipts still resolve unchanged.

The new local archive is explicitly ignored by Git and is outside the website's source selection. A second copy on the same machine protects against accidental temporary-directory cleanup; it does not provide an off-device backup or production immutable storage. Its bytes are not newly authorized for public distribution.

To check the preserved files and presentation archives from the repository root:

```bash
.venv/bin/python - <<'PY'
import hashlib
import json
from pathlib import Path

manifest = json.loads(Path('docs/audits/repository-archive-manifest.json').read_text())
for entry in manifest['entries']:
    destination = Path(entry['archive_path'])
    assert destination.stat().st_size == entry['byte_size'], destination
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == entry['sha256'], destination
    if entry['original_retained']:
        original = Path(entry['original_path'])
        assert hashlib.sha256(original.read_bytes()).hexdigest() == entry['sha256'], original
print(f"Verified {len(manifest['entries'])} archived files and retained originals.")
PY
```

If a later cleanup removes the original temporary directory, restore it from the preserved directory with `shutil.copytree`, refusing an existing destination, and rerun the verification above. Do not recreate that historical observation by recapturing the current source tree: current bytes may differ.

## Relocated historical presentations

Four untracked root-level presentation exports were moved without changing their bytes:

| Original path | New path | Reason |
|---|---|---|
| `AgtXIv_v1_overview_1to1.pptx` | `docs/archive/presentations/2026-08/AgtXIv_v1_overview_1to1.pptx` | Historical V1 presentation export |
| `AgtXIv_v1_overview_editable.pptx` | `docs/archive/presentations/2026-08/AgtXIv_v1_overview_editable.pptx` | Editable historical V1 presentation |
| `slide_demo.pdf` | `docs/archive/presentations/2026-08/slide_demo.pdf` | Historical demo PDF |
| `slide_demo.pptx` | `docs/archive/presentations/2026-08/slide_demo.pptx` | Historical demo presentation |

The new presentation [directory guide](../archive/presentations/2026-08/README.md) links the retained files. Each move is reversible using the manifest's original path after confirming that path does not already exist. Do not overwrite a newly created file while restoring.

A repository text search found references to the four original names in the historical [2026-08-31 work-in-progress reconciliation](v2-uncommitted-wip-reconciliation-2026-08-31.md), and no active navigation or build dependencies. That audit continues to describe the old observation accurately and was left unchanged. The new manifest provides the current path mapping. No ordinary active link required repair for this batch.

## Material deliberately retained

- Active scientific material in `agents/`, `Stabilizerness/`, `formal/`, `graph/`, `foundations/`, `database/`, schema packages and research reports remains at its original location.
- `Reference/` and `References/` remain in place because exact source paths and bytes are used by historical input inventories. Consolidation requires a separate reviewed mapping of those dependencies.
- Eight generated files under the robustness paper's `build/` directory are already included in a historical 14-file capture. They were not removed or reclassified as new execution evidence.
- All `formal/.lake` caches remain untouched. Their large size is not sufficient reason to remove them during release preparation.
- `slides/` contains active user presentation work and remains intact. The consumer review below distinguishes the two archived independent prototypes from the active `demo_design/` test/export target.
- Original files in `tmp/` remain present. Other temporary outputs and caches have not been broadly deleted.

## Verification and remaining organization work

The first preservation batch recorded five verified copies and four verified presentation moves, totalling 16,488,328 destination bytes. The prototype batch below adds 17 file moves and records the three append-only README changes separately. The machine-readable manifest also binds the unchanged historical closure receipt by hash. This pass is local evidence preservation, not a new Paper Agent release.

Further organization should consolidate the active website entry point, document authority and generated-output paths after their consumers have been updated. Source caches, scientific results and previous-version contracts should only move when their exact-reference dependencies and restoration paths are accounted for. The [release plan](../roadmaps/publishable-release-plan.md) keeps these tasks open under W1 and W6.

## Archived independent website prototypes

The maintained V3 website is `web/`. The following complete directories were moved after a read-only consumer review; the new [prototype index](../archive/prototypes/README.md) provides active navigation.

| Original path | Archive path | Preserved content and reason |
|---|---|---|
| `demo_architecture/` | `docs/archive/prototypes/demo_architecture/` | Four files, originally 39,154 bytes. The independent bilingual architecture explorer has 19 nodes, 18 connections and four guided views. Its diagram data is embedded in `app.js`; the external architecture JSON named in its text is a provenance reference, not a runtime fetch. No active external build/test/navigation consumer was found. |
| `demo_design_minimal/` | `docs/archive/prototypes/demo_design_minimal/` | Thirteen files, originally 2,412,664 bytes. Seven files are byte-identical to the active `demo_design/` copy: both JavaScript files, graph JSON, logo and the three MathJax files. Six HTML/CSS/README files retain the distinct minimal interface and documentation. No active external build/test/navigation consumer was found. |

All 17 files were first verified byte-for-byte after the move. Three READMEs then received only an appended migration notice and current preview commands. The manifest records each destination hash/size, each original hash/size, and each appended notice hash/size. Hashing the archived file prefix of `original_byte_size` bytes reproduces its original hash. No HTML, CSS, JavaScript, data, logo, license or vendor bundle was edited.

The [verification record](prototype-archive-verification.json) reports 26 verified manifest entries and 18,943,027 destination bytes across both organization batches. The prototype destinations contain 2,454,699 bytes, including 2,881 bytes of new README notices. All 17 original file identities, all 14 retained `demo_design/` and `pages/` file identities, the exact prototype directory membership, three HTML files, 29 local asset/navigation/anchor references, and the graph's relative JSON path passed. This is directory and static-reference verification; it does not claim a new scientific review or full browser-interaction test.

The following search was run from the repository root **before the move** and returned no matches (ripgrep exit status 1):

```bash
rg -n --hidden --max-columns 250 \
  -g '!.git/**' -g '!node_modules/**' -g '!.venv/**' \
  -g '!.claude/**' -g '!docs/audits/**' -g '!web/dist/**' \
  -g '!_site/**' -g '!baselines/**' -g '!tmp/**' \
  -g '!demo_architecture/**' -g '!demo_design/**' -g '!demo_design_minimal/**' \
  'demo_architecture|demo_design_minimal' .
```

This includes active `.github/`, `tools/`, `tests/`, `src/`, `web/` source, root documentation and non-audit documentation. It excludes Git internals, dependencies, nested worktrees, historical audit/baseline records, scratch outputs, generated websites and the three prototypes' own internal references. Ripgrep also follows the repository ignore configuration. The result is evidence about current source-text consumers, not a guarantee about unpublished bookmarks or external URLs. Searches inside the moved directories found relative local HTML assets and navigation; the architecture viewer has embedded data, while the minimal graph fetches its own `data/graph-theoretic-scientific-claims.json`.

No external active link to the two original paths required repair. Their own historical README text stays intact, followed by an explicit current-location notice; `docs/archive/README.md` and the new prototype index link to the current locations.

The following directories were deliberately retained after inspecting these concrete active consumers:

| Retained directory | Active consumers and preservation requirement |
|---|---|
| `demo_design/` | `tools/export_scientific_claim_demo.py:26` sets the generated JSON destination; `tests/test_demo_intake.py:12,72-75` and `tests/test_scientific_claim_demo.py:45` bind the original path; `docs/governance/generated-artifacts.md:56` documents that maintained output. Six files were already dirty user work: top-level `README.md`, `app.js`, `index.html`, `styles.css`, and `scientific_claims/index.html`, `scientific_claims/styles.css`. All 13 directory files were hashed before and after this operation and remained unchanged. |
| `pages/` | `tools/build_pages_site.sh:33` copies `pages/index.html`; `.github/workflows/ci.yml:81`, `.github/workflows/pages.yml:48` and `tools/validate_repo.py:496` invoke that build. The single file remained byte-identical. `web/` being the V3 entry point does not replace the existing GitHub Pages deployment workflow. |

The consumer evidence was also checked with:

```bash
rg -n --hidden --max-columns 250 \
  -g '!.git/**' -g '!node_modules/**' -g '!.venv/**' \
  -g '!.claude/**' -g '!docs/audits/**' -g '!web/dist/**' \
  -g '!_site/**' -g '!baselines/**' -g '!tmp/**' \
  -g '!demo_architecture/**' -g '!demo_design/**' -g '!demo_design_minimal/**' \
  'demo_architecture|demo_design_minimal|demo_design|pages/index.html|build_pages_site' .
```

To restore both original prototype directories with their exact original file bytes, keep the archive intact and run the following from the repository root. It refuses an existing original directory and verifies all source bytes before writing:

```python
import hashlib
import json
from pathlib import Path

manifest = json.loads(Path('docs/audits/repository-archive-manifest.json').read_text())
directories = manifest['prototype_organization']['directories']
roots = {row['original_path'] for row in directories}
assert all(not Path(name).exists() for name in roots), 'Original location already exists'
entries = [row for row in manifest['entries'] if row['original_path'].split('/')[0] in roots]
restored = []
for row in entries:
    archived = Path(row['archive_path']).read_bytes()
    assert hashlib.sha256(archived).hexdigest() == row['sha256']
    original = archived[:row['original_byte_size']]
    assert hashlib.sha256(original).hexdigest() == row['original_sha256']
    restored.append((Path(row['original_path']), original))
for path, original in restored:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(original)
    assert path.read_bytes() == original
print(f'Restored {len(restored)} original files; archive copies retained.')
```
