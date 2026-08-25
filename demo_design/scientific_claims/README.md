# ScientificClaim visualization demo

A dependency-free, expandable SVG graph of the two current contribution-role `ScientificClaim` records for **Graph Theoretic Approach to Quantum Nonstabilizerness** (`arxiv:2607.26154v1`) at repository revision `2d9b1b7`. The graph separates claim-level source provenance, normalized MathClaimIR identities, and an optional unverified Oracle candidate proof skeleton. Registry navigation remains distinct from proof dependencies.

## Preview

From the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open <http://127.0.0.1:8000/demo_design/scientific_claims/>. The exactness branch deep link is `#claim=claim%3Agraph-theoretic-nonstabilizerness%3Asign-relaxation-exactness&facet=facet%3Apolytope-exactness`. Serving from the repository root preserves the relative logo and data paths.

## Regenerate and check data

```bash
python3 tools/export_scientific_claim_demo.py
python3 tools/export_scientific_claim_demo.py --check
python3 -m unittest tests.test_scientific_claim_demo
```

The generated JSON is derived from the ScientificClaim, calibration, support-association, MathClaimIR, MathematicalPropositionIR, SourceAnchor registries, and the frozen Oracle candidate DAG. The exporter fails on ambiguous or dangling claim, facet, occurrence, formal-claim, and mathematical-target references, and validates every typed graph endpoint. Mathematical edges are explicitly labeled `PROVISIONAL NAVIGATION`; contribution-role ScientificClaims remain outside the mathematical proof DAG.
