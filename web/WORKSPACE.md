# Schema v0.2 reading workspace

Implemented 2026-09-17/18. This is a front-end redesign, not a v0.2 execution host.
No tests, app build, browser validation, source replays or model calls were run
for this change. Pending work is maintained only in
[`schema v0.1/PENDING_TESTS.md`](../schema%20v0.1/PENDING_TESTS.md), section 11.

## Design

The interface keeps one material and one selected object in view. The sidebar
holds the collection; the center shows a source-to-claim map or a sequential
list; the inspector retains the selected object's conditions and provenance.
The title uses a quiet serif, with white surfaces, fine warm-gray rules,
desaturated green, and native system typography. No external font requests.
All interface copy is English, including navigation, descriptions, dialogs,
errors, form hints, accessible labels, and live announcements. The page declares
`lang="en"`. Source records retain their original bytes and identities.

Repository references: the graph/detail arrangement in
`demo_design/scientific_claims`, the source-linked reading and real extraction
in the previous `web/public/index.html`, and the deliberate separation between
source-faithful ScientificClaims and mathematical interpretation. The original
demos are not overwritten.

External references requested by the user:

- [OpenAI Product Design](https://openai.com/zh-Hans-CN/business/plugins/product-design/):
  concept, interaction flow and prototype organization. No Product Design tool
  is available in this session; the plugin was not invoked or installed.
- [GSAP](https://gsap.com/docs/v3/GSAP/gsap.matchMedia()/): short entrance and
  selection transitions; reduced-motion support and cleanup.
- [Canvas UI](https://canvasui.dev/docs/installation): actual vanilla Grid source,
  used as a low-strength background, not as the sole renderer of content.
  The component license and source details are in
  `public/workspace/vendor/NOTICE.md`.

## Reading behavior and data boundaries

| Surface | Material and behavior |
| --- | --- |
| `/` | New v0.2-oriented workspace. Defaults to the hand-authored teaching Output. |
| Claim map | Selectable native buttons, source/correspondence links for the v0.2 example; candidate dependency links for the old robustness argument. No universal DAG assumption. |
| Sequential reading | Same objects and selected inspector, presented as a list. |
| Original record / export | Exact fields from the selected teaching Output or historical paper object. No v0.2 relabeling of historical records. |
| Source | Teaching source text and literal markers, without invented byte bindings. The historical example displays retained anchor metadata and links to its original reader. |
| Normalization | Source statement, normalized statement, declared relation, and unresolved symbols from the teaching MathClaim. |
| Formalization | Explains a single fixed MathClaim → committed Lamport artifact → Lean draft path, with missing prerequisites explicit. Does not submit anything. |
| Library | Search by title, English description and arXiv ID; explicit no-match state. |
| Schema guide | Four operations, three reading layers, seven host check layers, and exact specification downloads. No simulated check outcomes. |
| Open paper | Validate an arXiv link/ID for navigation, then prefill `/reader.html`. The user must separately submit the legacy extraction form. |

The only retained preference is the motion toggle. Navigable state lives in the
URL (`page`, `dataset`, `node`, `view`), including browser back/forward. There is
no account, fake upload queue, simulated agent progress, model selector, or
invented proof result. Fetch failures have a retry action and clear the stale
inspector. Loaded source/record strings are escaped before HTML insertion.

The teaching fixture has no persistent task/output/run identity. It is not a
real read-service response under `READ-INTERFACE.md`; the UI says so in provenance.
The historical dataset keeps its V3 `record_ref`, anchors and unassessed status.

## Motion and browser fallback

GSAP is optional: content starts visible in normal HTML. Canvas UI is dynamically
loaded for fine pointers only; it is behind the interactive DOM, has no idle
wave loop, and is destroyed on view change, reduced-motion selection, context
loss, tab hiding or page exit. Resize and intersection handling come from the
component. The ordinary dotted background remains if enhancement is unavailable.

Keyboard tabs support arrows/Home/End. Native buttons handle node selection;
dialogs have labels, Escape behavior and return focus to their trigger. On narrow
screens the inspector moves beneath the graph, navigation becomes a compact
top row, and the map scrolls horizontally to keep text readable. Sequential
reading is also available. These behaviors are implemented, not browser-verified.

## Files and maintenance

- `public/index.html`: workspace shell and dialogs.
- `public/workspace/app.js`: URL state, views, selection, source/context dialogs.
- `public/workspace/data.js`: read-only projections for the two retained examples.
- `public/workspace/motion.js`: GSAP and Canvas UI lifecycle.
- `public/workspace/styles.css`: responsive visual system.
- `sync-workspace.mjs`: exact source copies, called by the publication build.
- `public/reader.html`, `public/app.js`, `public/styles.css`: retained legacy reader.
- `vendor-src/canvas-ui`: original TypeScript and regeneration instructions.

No framework migration or runtime package installation is required. The existing
same-origin CSP remains intact. The existing HTTP test's expected root marker and
asset inventory were updated, without execution. Serving uses `npm run dev` from
`web/`; building and verification are separate actions under project policy.
