# Non-normative archive

This directory preserves superseded documents and visual drafts for provenance. Nothing here defines current AgtXIv behavior.

- `specifications/`: historical snapshots replaced by the canonical root [`AgtXIv.md`](../../AgtXIv.md).
- `diagram-drafts/`: unreferenced or superseded visual drafts retained for comparison.
- [`presentations/2026-08/`](presentations/2026-08/README.md): historical root-level V1 overview and demo exports, relocated without changing their bytes.
- [`prototypes/`](prototypes/README.md): independent architecture and minimal-design website prototypes, with original assets preserved and append-only README migration notices.

The [repository organization audit](../audits/repository-organization.md) and [archive manifest](../audits/repository-archive-manifest.json) record current recoverable relocations. They also document a separate ignored `local-archive/` preservation copy of the complete V3 candidate evidence previously retained only under `tmp/`. That local copy is outside this public document archive; existing historical records and original evidence files remain unchanged.

Exact duplicate drafts are not archived: Git history and the archive manifest are sufficient. In particular, the former root files `AgtXIv_v1.md` and `AgtXIv_v2.md` were byte-identical (SHA-256 `4d41d1035bcf4749b6895e61dd1f52891460a17084b7667ab3e441e3f6b51c9d`); their consolidated design subsequently evolved in the root `AgtXIv.md`.

The [v0.6 pre-V3 reading archive](specifications/AgtXIv-v0.6-pre-v3-2026-09-05.md) preserves the design before its 2026-09-05 V3 rewrite. Its original root-file SHA-256 is `ecd256bd070fbd4b909364e12257864cf901ddc3ec8eb0c778377dcffc44b336`, at repository HEAD `4bc41cbd32a0bb6b5fa1ea2a0b69c972525b28bd`. The reading copy adds a provenance notice and relocates relative Markdown links; original bytes remain in Git history. The current root document is the V3 design proposal, while V1 and V2 specifications retain their own version-specific authority.
