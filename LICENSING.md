# Licensing

AgtXIv's own work is licensed in two parts. Material written by other people keeps its own terms.

| What | Licence |
|---|---|
| **Code**: Python, JavaScript and TypeScript, Lean, shell, build and CI files, JSON Schemas and other machine-readable contracts | MIT ([LICENSE](LICENSE)) |
| **Documentation, figures, slides and data**: Markdown and HTML documents and decks, PowerPoint, PDF and image files, the technical report, and run records and other data files the project writes | CC BY 4.0 ([LICENSE-docs](LICENSE-docs)) |
| **Third-party material** (below) | Its own terms; neither licence covers it |

## Third-party material

- **Vendored web components** in `web/public/workspace/vendor/` and `web/vendor-src/`: GSAP under the GSAP Standard
  License (not MIT) and Canvas UI Grid under its own licence. See
  [web/public/workspace/vendor/NOTICE.md](web/public/workspace/vendor/NOTICE.md).
- **Excerpts of other people's papers** kept as source evidence, for example the `verbatim_source_text` fields under
  `Stabilizerness/ProvisionalClaimRegistry/`, and quotations in reviews and records. Paper titles and arXiv metadata
  (the metadata is CC0) are facts about the papers, not part of AgtXIv's work.
- **Papers the project studies.** They are not distributed here; [docs/REFERENCES.md](docs/REFERENCES.md) lists them
  with their own licences.
- **Dependencies fetched at build or run time** (for example mathlib and physlib for Lean, and Python and Node
  packages), under their own licences.

## Copyright and contributions

The copyright holder of AgtXIv's own work is the repository owner, **EugeneLIU2000**. Commits authored by the
`texra-ai` account were made by the owner with the TeXRA tool, and commits co-authored with Claude or Codex were
made at the owner's direction.

Contributions are accepted under the same licences (inbound = outbound) and need a Developer Certificate of Origin
sign-off on every commit. [CONTRIBUTING.md](CONTRIBUTING.md#licensing-of-contributions) explains how.

The repository owner decided these terms on 2026-10-07; [GOVERNANCE.md](GOVERNANCE.md#resolved-governance-decisions)
records the decision.
