# ScientificClaim visualization demo

An expandable SVG graph of the two current contribution-role `ScientificClaim` records for **Graph Theoretic Approach to Quantum Nonstabilizerness** (`arxiv:2607.26154v1`). The canvas contains only the paper, source-faithful ScientificClaims, normalized MathClaimIR objects, and an optional gray Oracle candidate branch. Occurrences, facets, support/calibration records, anchors, identity hashes, and verification status remain in claim details.

- Circle: source-faithful/minimally normalized ScientificClaim.
- Square: reorganized MathClaimIR.
- Gray square: temporary, referenced, Oracle-proposed, or unaccepted claim.
- Color: mathematical claim type; each FORMAL_ATOMIC claim and its exact MathClaimIR identity share a color.

## Preview

From the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8000/demo_design/scientific_claims/>. The exact polytope branch deep link is `#claim=claim%3Agraph-theoretic-nonstabilizerness%3Asign-relaxation-exactness&facet=facet%3Apolytope-exactness`. The facet parameter validates and filters the branch; it is not a graph node. Unrelated robustness support and the Oracle branch stay collapsed until explicitly expanded.

## Regenerate and check data

```bash
python3 tools/export_scientific_claim_demo.py
python3 tools/export_scientific_claim_demo.py --check
python3 -m unittest tests.test_scientific_claim_demo
```

The generated JSON derives source-faithful and normalized claims from the ScientificClaim, calibration, support-association, MathClaimIR, and SourceAnchor registries. Oracle nodes and candidate edges derive from `Stabilizerness/dag/claim-dag.json`; they remain `ORACLE_PROPOSED`, unaccepted, and are connected directly to the normalized exactness target without a wrapper node.

## Local mathematics renderer

Details are rendered with the local MathJax 3.2.2 TeX-to-SVG browser bundle in `vendor/mathjax/`. `manifest.json` records the npm tarball source and SHA-256; `LICENSE` contains the Apache-2.0 license. Inline `$...$` and `\(...\)`, display `$$...$$` and `\[...\]`, and fenced `latex` blocks are passed to MathJax after safe DOM-only Markdown construction. Exact occurrence excerpts remain byte-faithful `tex-source` blocks; a separate source-derived preview extracts only delimited formulas and equation bodies, removes labels, deduplicates fragments, and uses the paper macros `\Mcal`, `\STAB`, `\RoM`, `\tr`, and `\clnum`. If MathJax is unavailable, the original TeX remains visible as plaintext.
