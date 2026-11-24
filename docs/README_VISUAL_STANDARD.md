# README and Visual Documentation Standard

**Scope:** DuckOS README, documentation indexes, architecture diagrams and visual assets. Product behavior remains defined by source code, build contracts, schemas, tests and implementation evidence.

## Publishing principles

1. Lead with one factual sentence that identifies DuckOS as an operating-system project and describes Mora's current browser-shell role.
2. Keep the adaptive hero, current workflow badges, quick navigation and quick start near the top.
3. Distinguish browser-local Mora UI, executable Reaper reference contracts, source submodules and native OS implementation.
4. Never imply that a design, catalog entry, browser panel, manifest or test is a bootable OS capability.
5. A documentation refresh does not create a new release, kernel, installer or deployment artifact.

## README structure

Use this order: adaptive hero; factual one-line pitch; CI badges and navigation; implementation-boundary note; quick start; documentation-revival comparison; product/maturity matrix; visual overview; Mermaid architecture; source federation; native workbench; release/deployment tooling; configuration; repository map; verification and roadmap links; contribution and further reading.

## Theme-aware hero

Use `assets/readme/hero-banner-light.svg` and `assets/readme/hero-banner-dark.svg` with the same intrinsic dimensions and viewBox. Select them through `<picture>` and `prefers-color-scheme`. Keep accessible fallback alt text. SVGs must be self-contained and contain no remote resources.

## Screenshots and diagrams

- A screenshot must be an actual captured application image committed under `assets/screenshots/`.
- Never synthesize or redraw a UI mock-up and label it a screenshot.
- Label authored architecture, workflow and layer diagrams as schematics.
- Use a two-column, one-row visual layout on wide screens, with descriptive alt text and captions.
- If no verified screenshot exists, state that directly and use labelled architecture diagrams instead.
- Preserve the distinction between browser shell and native system interface in all captions.

## Technical accuracy

- Mark Reaper-backed policy behavior as reference/runtime contract behavior unless native implementation evidence exists.
- Distinguish component packaging and deployment planning from bootable ISO/USB creation and physical installation.
- Treat application catalogs as specifications, not proof that all listed apps ship or run as native services.
- Treat hashes as byte-integrity evidence, not proof of signer identity unless signature verification succeeds against a trusted public key.
- Do not invent environment variables, login credentials, cloud services or privileged command behavior.

## Navigation and acceptance

Keep the documentation index linked from the root README. Add each new technical page to the index and its owning topic hub/map. Before merge, verify local links, Mermaid syntax, SVG viewBoxes, code examples, language/terminology consistency and `git diff --check`.
