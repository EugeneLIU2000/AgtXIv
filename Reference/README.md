# Reference source corpus

This directory contains upstream material used to design, test, and audit AgtXIv. Paper directories preserve searchable TeX/BibTeX sources and source-supplied figures; Lean repositories are retained as package/API references and are excluded from ordinary repository tracking where indicated by `.gitignore`.

## Source policy

- Keep upstream filenames and directory structure intact so source anchors remain reproducible.
- `00README.json`, when present, records the upstream top-level TeX entry point and compiler.
- `source.tar`, when present, is the frozen upstream download bundle. The expanded files are the searchable working copy. Both are retained when provenance requires the exact downloaded bundle; neither should be treated as a local build artifact.
- Source-supplied PDF/PNG figures are part of the upstream source bundle, not generated AgtXIv output.
- Local compilation products should not be added to paper source directories.

## Newly catalogued design and formalization references

| Directory | Relevance to AgtXIv |
|---|---|
| `Agentic Publication Protocol An Attempt to Modernize Scientific Publication/` | Agentic publication protocols, repository structure, and publication workflow |
| `Can Theoretical Physics Research Benefit from Language Agents/` | Language-agent workflows for theoretical-physics research |
| `End-to-End Formalization of Quantum Error Correction/` | End-to-end formalization workflow in a quantum-information domain |
| `Multi-agent Autoformalization of Tensor Network Theory/` | Multi-agent Lean formalization, blueprints, prompts, alignment, and cost telemetry |
| `Paper2Agent Reimagining Research Papers As Interactive and Reliable AI Agents/` | Paper-to-agent interfaces and reliability-oriented research packaging |

The remaining paper directories support the Stabilizerness and quantum-information pilot. `References/` is a legacy source location used by an existing artifact and has not been renamed in this organizational pass to avoid breaking paths; new general source additions should use `Reference/` until a dedicated migration updates all consumers atomically.
