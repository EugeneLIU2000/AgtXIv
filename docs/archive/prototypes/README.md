# Historical website prototypes

These independent visual prototypes are retained for comparison and provenance. The maintained V3 reader and actual source-analysis service are in [`web/`](../../../web/README.md).

| Prototype | Preserved content | Open from a repository-root HTTP server |
|---|---|---|
| [Architecture explorer](demo_architecture/README.md) | A bilingual interactive architecture diagram with 19 nodes, 18 connections and four guided views; its data is embedded in JavaScript. | [Open explorer](demo_architecture/index.html) |
| [Minimal visual edition](demo_design_minimal/README.md) | The historical single-paper pilot replay with its own minimal HTML/CSS design, local graph data and MathJax. It does not process new papers. | [Open prototype](demo_design_minimal/index.html) · [Open graph](demo_design_minimal/scientific_claims/index.html) |

From the repository root, run `python3 -m http.server 8000 --bind 127.0.0.1`, then open <http://127.0.0.1:8000/docs/archive/prototypes/>. Each prototype can also be served independently from its own directory.

All 17 original files are preserved. Three READMEs have an appended migration notice; their original prefixes and all other assets remain byte-identical. The [organization record](../../audits/repository-organization.md) documents the consumer search and restoration procedure. The [archive manifest](../../audits/repository-archive-manifest.json) records every original/destination path and the hashes before and after the README additions.

The active historical [`demo_design/`](../../../demo_design/README.md) export/test target and [`pages/`](../../../pages/index.html) build input remain at their original locations. They have active consumers and were not included in this move.
