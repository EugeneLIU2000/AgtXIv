# ScientificClaim visualization demo

A dependency-free, facet-first view of the two current contribution-role `ScientificClaim` records for **Graph Theoretic Approach to Quantum Nonstabilizerness** (`arxiv:2607.26154v1`) at repository revision `97445bc`.

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

The generated JSON is derived from the ScientificClaim, calibration, support-association, MathClaimIR, and MathematicalPropositionIR registries. The exporter fails on ambiguous or dangling claim, facet, and mathematical-target references.
