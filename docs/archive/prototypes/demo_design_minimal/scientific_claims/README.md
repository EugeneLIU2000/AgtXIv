# ScientificClaim visualization — minimal edition

An expandable SVG graph of the two current contribution-role `ScientificClaim` records for **Graph Theoretic Approach to Quantum Nonstabilizerness** (`arxiv:2607.26154v1`). The minimal interface preserves the graph's necessary node classification colors while reducing the surrounding chrome to warm white surfaces, fine separators, compact controls, and a single muted blue interface accent.

The canvas contains only the paper, source-faithful ScientificClaims, normalized MathClaimIR objects, and an optional gray Oracle candidate branch. Occurrences, facets, support/calibration records, anchors, identity hashes, and verification status remain in claim details.

- Circle: source-faithful/minimally normalized ScientificClaim.
- Square: reorganized MathClaimIR.
- Gray square: temporary, referenced, Oracle-proposed, or unaccepted claim.
- Color: mathematical claim type; each FORMAL_ATOMIC claim and its exact MathClaimIR identity share a color.

## Preview

From the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open <http://127.0.0.1:8000/demo_design_minimal/scientific_claims/>.

Or serve the independent copy directly:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory demo_design_minimal
```

Open <http://127.0.0.1:8000/scientific_claims/>. The exact polytope branch deep link is `#claim=claim%3Agraph-theoretic-nonstabilizerness%3Asign-relaxation-exactness&facet=facet%3Apolytope-exactness`. The facet parameter validates and filters the branch; it is not a graph node. Unrelated robustness support and the Oracle branch stay collapsed until explicitly expanded.

## Regenerate and check baseline data

The JSON in this visual copy is intentionally byte-identical to the current `demo_design/` baseline. The canonical exporter still targets that baseline:

```bash
python3 tools/export_scientific_claim_demo.py --check
python3 -m pytest -q tests/test_scientific_claim_demo.py
```

The generated JSON derives source-faithful and normalized claims from the ScientificClaim, calibration, support-association, MathClaimIR, and SourceAnchor registries. Oracle nodes and candidate edges derive from `Stabilizerness/dag/claim-dag.json`; they remain `ORACLE_PROPOSED`, unaccepted, and are connected directly to the normalized exactness target without a wrapper node.

## Local mathematics renderer

Details are rendered with the local MathJax 3.2.2 TeX-to-SVG browser bundle in `vendor/mathjax/`. `manifest.json` records the npm tarball source and SHA-256; `LICENSE` contains the Apache-2.0 license. If MathJax is unavailable, the original TeX remains visible as plaintext.


## Archive location notice — 2026-09-08

This historical prototype moved from `demo_design_minimal/` to `docs/archive/prototypes/demo_design_minimal/`. The earlier text is preserved verbatim as historical context; preview addresses above refer to the former location. The maintained V3 website and actual source-analysis service are in `web/`.

From the repository root, run `python3 -m http.server 8000 --bind 127.0.0.1` and open <http://127.0.0.1:8000/docs/archive/prototypes/demo_design_minimal/scientific_claims/>. Alternatively serve the archived prototype with `python3 -m http.server 8000 --bind 127.0.0.1 --directory docs/archive/prototypes/demo_design_minimal`. Open <http://127.0.0.1:8000/scientific_claims/> in that mode. Only this notice was appended; original file prefixes and every other asset remain byte-identical. The path mapping, hashes and recovery instructions are in `docs/audits/repository-archive-manifest.json` and `docs/audits/repository-organization.md`.
