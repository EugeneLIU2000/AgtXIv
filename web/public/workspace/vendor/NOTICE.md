# Third-party components in the AgtXIv workspace

These files are application dependencies, served locally. No CDN is contacted
when a reader opens the workspace. Retrieved 2026-09-17/18.

## GSAP 3.15.0

- Author: GreenSock / Jack Doyle; copyright notice retained in `gsap/gsap.min.js`.
- Distribution: https://registry.npmjs.org/gsap/-/gsap-3.15.0.tgz
- File: `package/dist/gsap.min.js`, copied without modification.
- License: https://gsap.com/standard-license/ (GSAP Standard License, not MIT).
- Used for restrained entrance and selection transitions. Missing GSAP leaves
  the ordinary HTML interface operational.

## Canvas UI Grid (vanilla WebGL)

- Author: David Haz, copyright 2026.
- Official registry: https://canvasui.dev/r/grid-vanilla.json
- Component: https://canvasui.dev/docs/components/grid
- Upstream project: https://github.com/DavidHDev/canvas-ui
- License: `canvas-ui/LICENSE.md`, retrieved from the official repository.
- Original source retained at `web/vendor-src/canvas-ui/GridVanilla.ts`.
- Runtime `canvas-ui/grid.js` is generated with Node's
  `stripTypeScriptTypes`, then changes only the helper import path to
  `./rect-cache.js`. The public header points to this notice.
- The retrieved registry contained a `../rect-cache` import but no helper file
  or registry dependency. `canvas-ui/rect-cache.js` is an AgtXIv-authored local
  adapter, not an upstream file.
- Included as part of this application. It is not a standalone component
  redistribution, component marketplace, or resold component bundle.

The Grid sits behind the semantic HTML graph, at low opacity, with idle ripples
disabled. It is skipped on coarse pointers or reduced-motion settings. A failed
WebGL context leaves the static dotted background and all reading controls.
The application does not require the experimental HTML-in-Canvas browser flag.
