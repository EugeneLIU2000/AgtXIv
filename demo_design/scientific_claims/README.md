# ScientificClaim visualization demo

A dependency-free, expandable SVG graph of the two current contribution-role `ScientificClaim` records for **Graph Theoretic Approach to Quantum Nonstabilizerness** (`arxiv:2607.26154v1`) at repository revision `2d9b1b7`. The graph progressively reveals claim facets, source/calibration records, justified `FORMAL_ATOMIC` claims, and provisional navigation to deduplicated MathClaimIR or MathematicalPropositionIR targets.

## Preview

From the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8000/demo_design/scientific_claims/>. Serving from the repository root preserves the relative logo and data paths.

## Regenerate and check data

```bash
python3 tools/export_scientific_claim_demo.py
python3 tools/export_scientific_claim_demo.py --check
python3 -m unittest tests.test_scientific_claim_demo
```

The generated JSON is derived from the ScientificClaim, calibration, support-association, MathClaimIR, and MathematicalPropositionIR registries. The exporter fails on ambiguous or dangling claim, facet, occurrence, formal-claim, and mathematical-target references, and validates every typed graph endpoint. Mathematical edges are explicitly labeled `PROVISIONAL NAVIGATION`; contribution-role ScientificClaims remain outside the mathematical proof DAG.
