# Jora application synthesis in DuckOS

**Product:** DuckOS / Mora / Jora  
**Initial implementation:** 0.1.0  
**Maturity:** partial user-space formula studio and source-package generator

## Product placement

Jora is a distinct application in the Mora desktop and a proposed DAK application package (dak.jora). It complements, rather than replaces, Mora Commons. Mora Commons is the curated local catalogue; Jora is the formula studio and source-package generator.

## Formula and seed registry

A formula is a bounded composition such as: text editor + audio editor + translator. The seed registry assigns canonical parameter IDs, Russian/English aliases, domains, capabilities, conflicts and variants. It currently includes text editor, audio editor, translator, subtitles, notes, task board, calendar, offline mode and cloud translation. The full 666-variant source taxonomy is not represented as already implemented in this initial seed.

The parser rejects empty, unknown, duplicate and conflicting components. The limit is 64 components and 2,048 characters.

## Graph and growth

The initial three-component example includes a Reaper coordinator, unified project-data hub, three component nodes and all three pairwise synergy edges. Larger formulas use domain cluster gateways and bounded local adjacency rather than a full pairwise mesh. Graph metadata records topology and growth policy.

This is a planning artifact. It does not imply that OS processes, shared memory, network channels or kernel services have started.

## Polyglot selection and Reaper boundary

Reaper is always the selected core language. Python is selected for text/translation work. Audio work selects Rust only when rustc is detected by the host CLI; otherwise the plan records a Python non-real-time fallback. A generated source package includes a small Reaper entry point.

DuckOS uses the existing ReaperWorkbench process boundary. Package validation may invoke Reaper's static checker when the checkout is available. It never executes the generated program. Reaper native C17 compilation remains a partial scalar AOT path, not a general compiler for every generated component.

## Package contract

A generated directory or deterministic ZIP contains jora.manifest.json, formula.graph.json, source/main.rpr, polyglot/languages.json, content/demo-project.json and README.md. The manifest includes formula identity, selected languages, graph metadata, build maturity and a SHA-256 inventory.

Audio is represented by placeholder metadata in the seed scenario; no audio binary is fabricated. Validation checks canonical relative paths, duplicate ZIP entries, symlinks, file-count and expanded-size limits, required files and SHA-256 integrity.

## Commands

    duckos jora catalog
    duckos jora create --formula "текстовый редактор + аудиоредактор + переводчик" --output ./Slovovolna.zip
    duckos jora validate ./Slovovolna.zip
    duckos jora validate ./Slovovolna.zip --skip-reaper-check

The output path must not already exist. Create writes a directory or ZIP; it does not install or launch the application.

## Security and maturity

- Formula input and package size are bounded.
- Generated paths are canonical relative paths; symbolic links and path traversal are rejected.
- Generated packages are source artifacts, not executed by the generator.
- Reaper static checking is a diagnostic pass, not program execution.
- The browser panel stores local drafts and downloads user-selected files.
- No remote store, payments, signing authority, app sandbox, native package installer or kernel capability provider is connected.
- dak.app-synthesis.v1 is a proposed DAK service identifier; its native provider remains design-only.

## Verification

    python -m unittest tests.test_jora -v
    npm test
