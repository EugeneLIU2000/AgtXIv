# AgtXIv design prototype

A self-contained, dependency-free visual prototype for an AgtXIv landing page and registry interface. Its primary interaction accepts an arXiv URL or identifier, shows a short staged source/normalization/DAG/report run, and opens the existing normalized ScientificClaim graph.

## Supported input

This static first-version demo only supports the committed `arXiv:2607.26154v1` pilot. Accepted equivalents include:

- `https://arxiv.org/abs/2607.26154`
- `https://arxiv.org/pdf/2607.26154`, with optional `.pdf` or `v1`
- `arXiv:2607.26154v1`
- `2607.26154`

Other valid arXiv identifiers receive an unsupported-paper message; malformed or non-arXiv input is rejected separately. The interaction replays precomputed pilot artifacts and does not claim to process arbitrary papers. Its completion report states that the pilot source identity matched and existing source-grounded records were reused; generated/candidate relations remain unverified and unaccepted, and this demo run admits no new database records.

## Preview

From the repository root, either serve the repository:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

and open <http://127.0.0.1:8000/demo_design/>, or serve the demo directory directly:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory demo_design
```

and open <http://127.0.0.1:8000/>.

The prototype uses only local HTML, CSS, JavaScript, and the AgtXIv logo in `assets/`. The registry workbench is a concept preview; it does not claim that every displayed verification axis is complete in the pilot.
