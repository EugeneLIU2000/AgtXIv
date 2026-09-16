# AgtXIv minimal design prototype

A self-contained, dependency-free visual copy of the AgtXIv landing page and ScientificClaim registry. This edition keeps the full pilot workflow and data while presenting them as a restrained research-software interface: warm white surfaces, charcoal text, one muted blue accent, fine borders, compact status treatments, and minimal motion.

## Supported input and behavior

This static first-version demo only supports the committed `arXiv:2607.26154v1` pilot. Accepted equivalents include:

- `https://arxiv.org/abs/2607.26154`
- `https://arxiv.org/pdf/2607.26154`, with optional `.pdf` or `v1`
- `arXiv:2607.26154v1`
- `2607.26154`

Other valid arXiv identifiers receive an unsupported-paper message; malformed or non-arXiv input is rejected separately. The interaction replays precomputed pilot artifacts and does not claim to process arbitrary papers. Its completion report states that the pilot source identity matched and existing source-grounded records were reused; generated/candidate relations remain unverified and unaccepted, and this demo run admits no new database records.

## Preview

Serve the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open <http://127.0.0.1:8000/demo_design_minimal/>.

Alternatively, serve this copy directly:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory demo_design_minimal
```

Open <http://127.0.0.1:8000/>. In both modes, the landing page, result deep links, return navigation, local logo, generated JSON, and bundled MathJax resolve through relative paths.

The prototype uses only local HTML, CSS, JavaScript, JSON, the AgtXIv logo in `assets/`, and the MathJax bundle under `scientific_claims/vendor/`. The registry workbench is a concept preview; it does not claim that every displayed verification axis is complete in the pilot.


## Archive location notice — 2026-09-08

This historical prototype moved from `demo_design_minimal/` to `docs/archive/prototypes/demo_design_minimal/`. The earlier text is preserved verbatim as historical context; preview addresses above refer to the former location. The maintained V3 website and actual source-analysis service are in `web/`.

From the repository root, run `python3 -m http.server 8000 --bind 127.0.0.1` and open <http://127.0.0.1:8000/docs/archive/prototypes/demo_design_minimal/>. Alternatively serve the archived prototype with `python3 -m http.server 8000 --bind 127.0.0.1 --directory docs/archive/prototypes/demo_design_minimal`. Open <http://127.0.0.1:8000/> in that mode. Only this notice was appended; original file prefixes and every other asset remain byte-identical. The path mapping, hashes and recovery instructions are in `docs/audits/repository-archive-manifest.json` and `docs/audits/repository-organization.md`.
