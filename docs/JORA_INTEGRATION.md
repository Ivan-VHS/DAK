# Jora — DuckOS integration and implementation boundary

**Application:** Jora  
**Host:** DuckOS / Mora  
**Runtime:** DuckOS user space; Reaper reference-runtime static checks  
**Status:** partial implementation  
**Contract:** duckos.jora.app-package.v1

## 1. Product boundary

Jora is a standalone DuckOS application factory and local application catalogue. It is exposed through two complementary entry points:

- **Mora Formula Studio** previews formulas, component composition, graph topology and language choices; it stores formula drafts in the current browser profile.
- **Native DuckOS CLI** creates source-first Jora packages, verifies their file inventory and asks the existing Reaper workbench to statically check the generated Reaper source.

Jora is not part of the DuckOS kernel, is not the operating-system package manager and does not run generated programs automatically. The browser interface cannot launch host processes. A package's local catalogue record is not a public listing or a system installation.

## 2. Runtime structure

    Mora Desktop
      └─ Jora Formula Studio
           ├─ Formula preview and identity
           ├─ Bounded component graph
           ├─ Language-plan preview
           └─ Current-browser-profile drafts

    Native DuckOS CLI
      └─ duckos jora
           ├─ registry.py       25 canonical base components and aliases
           ├─ engine.py         parser, validation, graph and language selector
           ├─ packages.py       source package, manifest and integrity checks
           └─ ReaperWorkbench   bounded subprocess bridge to pinned Reaper CLI

    Current-user local catalogue
      └─ ~/.local/share/duckos/jora/catalog.v1.json

The Reaper process boundary remains the one documented by Native Reaper Integration. DuckOS supplies a fixed argument vector, no shell interpretation, a timeout and bounded output; Reaper owns its grammar and runtime.

## 3. Formula contract

The native engine accepts Russian and English aliases separated by plus, comma, semicolon, and/or conjunctions. Each term can optionally use a role and weight:

    основной: текстовый редактор + фоновый: заметки x2
    optional: subtitle export

Roles are primary, standard, background and optional; weights are bounded from 1 to 16. The canonical formula stores component ID, role, weight and input position. Duplicate canonical components and hard conflicts are rejected with a diagnostic instead of generating ambiguous code.

The initial registry contains 25 canonical component capabilities. It includes text, audio, translation, subtitles, STT/TTS, glossaries, notes, tasks, calendar, tables, charts, code editing, debugging, build pipelines, file management, search, version control, image/video editing, presentations, cloud sync/streaming, offline mode and automation rules.

The 666-variation proposal (222 variants for each of the three original families) is not represented as 666 implemented registry entries yet. It is a future catalogue-import and curation task; the current registry is the executable base taxonomy.

## 4. Graph composition

Every formula creates a Reaper coordinator node, one node per canonical component, registration edges and a bounded set of typed synergy edges. Rolling indexes keep only a finite number of candidate neighbours per type/domain. Thus graph construction does not compare every newly-added node against the entire previous component list.

The graph has linear-size storage under the configured bound. The number of candidate lookups per insertion depends on the bounded number of contract types carried by a component. A hard 256-component cap and package/resource limits make each generation finite. N → ∞ is an extensibility objective, not a promise to materialize or execute an infinite graph.

## 5. Polyglot selection and Reaper source

Reaper is always selected as the generated core language. Optional helper languages are selected only when the local toolchain is detectable:

- Python for text, glossary, translation-adapter and content helpers.
- Rust or C for a narrow audio-frame helper when rustc or a C compiler is present.
- The Mora web UI remains JavaScript; TypeScript is optional for future web build profiles.

The generated main source is a .rpr file. The native verification command invokes the existing Reaper --check --json path when the pinned Reaper checkout is available. Helper syntax checks are bounded and do not execute generated code.

The toolchain selector does not assume that Reaper's partial native compiler is a production compiler. A successful Reaper check proves a reference-runtime parse/static-check result, not native AOT compilation, process isolation, device access or end-to-end application execution.

## 6. Package structure

A generated package is a new directory with a .jora suffix:

- jora.manifest.json — versioned identity, formula hash, graph summary, language plan, permissions, dependencies, inventory and verification state.
- source/main.rpr — Reaper-first source entry point.
- helpers/ — optional Python, C or Rust source helpers selected for available tools.
- architecture/ — canonical formula, full bounded graph and language-plan report.
- content/demo-project.json — coherent synthetic content and linked segment metadata.
- content/audio/demo.wav — deterministic short PCM silence asset when an audio/STT/TTS component is present.
- store/listing.json — store metadata draft. Screenshot list remains empty until a real app UI is available and captured.
- README.md — package contents and trust/runtime boundaries.

Every packaged file except the manifest itself has a SHA-256 digest and byte length in the manifest. Package creation uses a staging directory and an atomic rename to a new target. Existing output directories are never overwritten. Symlinks, traversal paths and oversized packages are rejected.

## 7. CLI

    duckos jora status
    duckos jora formula "текстовый редактор + аудиоредактор + переводчик"
    duckos jora create --formula "текстовый редактор + аудиоредактор + переводчик" --output ./slovovolna.jora
    duckos jora verify ./slovovolna.jora
    duckos jora publish ./slovovolna.jora --channel experimental
    duckos jora catalog

The formula command prints normalized composition, identity, graph and language report. The create command writes the source-first package. The verify command validates path safety, sizes, hashes, helper syntax and the Reaper source check when available. The publish command records a package path in the current user's local catalogue.

Only experimental and verified_preview are accepted by the local publisher. verified_preview requires the successful Reaper static check. No stable/public channel is enabled.

## 8. Security and privacy

- Formula text is size-limited, parsed against a fixed registry and never treated as executable input.
- Generated source is written as data and is not executed during package creation or verification.
- Reaper static checking uses the existing bounded workbench process bridge.
- Python helpers are syntax-compiled in memory; C/Rust helpers are passed to syntax/metadata compiler modes only when a compiler is available.
- No generated helper is run, no external translator is contacted, and no network or device permissions are automatically granted.
- Package paths are validated; symlinks and path traversal are rejected; output is not overwritten.
- Browser drafts remain in the active Mora browser profile. Native package catalogue records remain in the current user's local data directory.

## 9. Implemented versus deferred

Implemented in this change:

- formula parser and alias registry;
- duplicate/conflict validation;
- deterministic identity proposals;
- bounded component graph and language-plan selection;
- Reaper .rpr source generation;
- synthetic demo data and generated silence WAV;
- package manifest and SHA-256 inventory;
- helper syntax checks and Reaper static-check integration;
- per-user experimental/verified-preview catalogue;
- Mora Formula Studio and local formula drafts;
- Python/JavaScript contract tests and package schema.

Not implemented by this change:

- all 666 variation records and large domain-specific component packs;
- a hosted public catalogue, user accounts, remote workers, ratings or community moderation;
- production native compiler support and execution of generated programs;
- application installer, dependency resolver or kernel-enforced app sandbox;
- automatic screenshot capture from a running generated app;
- signed public releases, stable update channels and rollback across installed apps;
- native system package manager or boot-image integration.

A feature may advance to a stronger maturity state only after source, tests, CI, target-platform evidence and documentation demonstrate that exact scope.
