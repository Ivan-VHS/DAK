# Product Stage Naming Standard

**Status:** shared naming convention for public roadmap, architecture and product-facing documentation across DuckOS and its connected repositories.

## Purpose

Use meaningful, sequential stage labels instead of arbitrary numerological branding. A stage communicates the maturity gate or delivery phase of a body of work; it is not a decorative count and does not certify that the associated work is complete.

## Canonical stage ladder

| Label | Name | Intended scope |
|---|---|---|
| Stage 0.1 | Foundation | Product intent, engineering principles, user needs and baseline constraints |
| Stage 0.2 | Architecture & Contracts | System boundaries, data models, API/ABI contracts and component ownership |
| Stage 0.3 | Core Implementation | First integrated implementation of the agreed contracts |
| Stage 0.4 | Developer Experience | Compiler/toolchain, editor, diagnostics, build and debugging workflows |
| Stage 0.5 | Product Experience | User interaction, accessibility, visual system and product-specific workflows |
| Stage 0.6 | Ecosystem Integration | Cross-repository interfaces, packaging, migration and interoperability |
| Stage 0.7 | Verification | Conformance, tests, benchmarks and reproducible evidence |
| Stage 0.8 | Hardening | Security, resilience, performance, recovery and operational limits |
| Stage 0.9 | Release Candidate | Release packaging, documentation, compatibility review and qualification |
| Stage 1.0 | Stable Release | A supported release whose published acceptance gates have passed |
| Stage 1.1+ | Evolution | Compatible feature growth, optimization and subsequent maintenance |
| Stage 2.0 | Next Generation | A deliberately versioned architectural generation with migration guidance |

## Naming format

Use:

`<Product> — Stage 0.1: <short deliverable name>`

Examples:

- `Reaper Psychoporter — Stage 0.1: Engineering Doctrine`
- `MOST Function Atlas — Stage 0.2: Contract Registry`
- `Reaper Studio — Stage 0.4: Developer Tooling Contract`
- `Shared UI/UX Foundation — Stage 0.1`
- `Product UI/UX Profile — Stage 0.5`

Use the stage in document titles, roadmap entries, milestone names and public progress summaries. Prefer semantic filenames such as `STAGE_NAMING_STANDARD.md` or `UI_UX_PROFILE_STAGE_0_5.md`; do not encode arbitrary totals into filenames.

## Advancement gates

A stage may be marked complete only when its acceptance criteria are documented and supported by repository evidence:

1. Source implementation or an explicitly scoped specification exists.
2. Positive, negative and boundary tests cover the relevant contracts.
3. Integration and compatibility effects are reviewed.
4. CI or reproducible local verification is recorded.
5. Documentation states limitations and remaining work.
6. The stage does not imply that planned functionality is already shipped.

A document may carry a stage label as its roadmap position without claiming that the whole stage has passed.

## Numbers that must remain unchanged

This standard applies to branding, not to technical identity or measurement. Preserve:

- stable requirement, diagnostic, issue and symbol IDs;
- API, ABI, file-format and schema versions;
- exact registry sizes, array bounds, ordinals and dataset counts where they are part of a contract;
- memory sizes, timing budgets, frequencies, benchmark values and hardware identifiers;
- dates, release versions and migration identifiers.

Do not renumber a stable contract merely to make a heading look cleaner. Replace only arbitrary marketing numerology; retain historical identifiers wherever tasks, tests, code or compatibility depend on them.

## Migration policy

When replacing a numeric brand:

1. Give the document or program a semantic name and a stage label.
2. Update every incoming relative and cross-repository link in the same change.
3. Update workflow labels, test descriptions and validator messages that expose the old brand.
4. Keep technical IDs and machine-readable counts intact.
5. Record a migration note when a public path changes.
6. Merge each repository's change through its own reviewed pull request.

**Principle:** the stage tells readers where the work is in its lifecycle; evidence tells them what actually works.
