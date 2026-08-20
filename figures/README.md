# AgtXIv figures

Six vector figures for `AgtXIv.md`, drawn to the `paper-figure` style spec from
[paper-craft-skills](https://github.com/zsyggg/paper-craft-skills)
(white ground, dark-grey dominant, two accent colours used for meaning rather than decoration,
short label-style annotations, no 3-D and no decorative fill).

| file | what it shows | current specification topics |
|---|---|---|
| `fig1_overview` | query → backward archaeology → forward build → QueryResolution receipt | “Two opposite directions”; “QueryResolution cache” |
| `fig2_axes` | independent verification axes and the limited scope of Lean evidence | “Trusted Verification Layers”; “Verification axes” |
| `fig3_contract` | claim-level vs paper-level binding; MathContract anatomy | “Graph model”; “MathContract”; “QueryResolution cache” |
| `fig4_incremental` | offline vs online path; what a query pays for; invalidation | “Search, registry, and incremental build”; “Versioning and invalidation” |
| `fig5_lean` | MathClaimIR → kernel → source-blind backtranslation → alignment audit | “Formal-alignment layer”; “Automated Lean 4 Reconstruction Procedure” |
| `fig6_failure` | lifecycle states, failure classification, and distinct blocked/refuted outcomes | “Failure classes and graph repair”; “Overall lifecycle status” |

The topic names above are used instead of hard-coded section numbers so this index remains stable when the specification is reorganized.

Each figure ships as:

- `*.svg` — vector master, editable
- `*.pdf` — vector, for LaTeX (`\includegraphics{figures/fig1_overview.pdf}`)
- `*@2x.png` — 2× raster, for README / slides

## Rebuilding

```bash
cd figures
python3 src/fig1_overview.py     # writes figures/fig1_overview.svg
```

The Python programs are the maintainable source for the SVG masters. PDF exports are retained for publication use. High-resolution PNG exports and the presentation-specific backends are local derivatives and are not part of the canonical figure set.

`figlib.py` holds the palette and the shared primitives; every figure imports it,
so changing a colour there restyles the whole set.

Two accents carry all the meaning:

- **blue `#2563EB`** — verified / accepted / reusable
- **red `#DC2626`** — gap, blocked, frontier, refuted

Everything else is greyscale on purpose.
