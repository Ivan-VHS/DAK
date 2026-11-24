# Jora store and Reaper composition bridge

**Desktop:** Mora / DuckOS  
**Generator:** Reaper  
**Current status:** local catalogue + request composer + safe CLI bridge; generated output is a scaffold only

## User-facing model

Jora is the one application-store entry point in Mora. It combines a curated catalogue with a formula builder. Users can pick capability modules, choose interface locales and a primary locale, and receive a product-name suggestion and a formula.

Example:

Text Editor + Audio Editor + Translator = LexiTone 3D

Mora's browser surface performs local composition preview and exports a versioned JSON request. It does not launch host processes. This preserves the existing security boundary: browser JavaScript is not a local command runner.

## End-to-end flow

Mora / Jora composer
  -> select components and locales
  -> reaper.jora.request.v1 JSON file
  -> user invokes local DuckOS CLI
  -> duckos jora build request.json output-directory
  -> DuckOS ReaperWorkbench validates paths and invokes Reaper with argv and shell=False
  -> Reaper resolves dependencies and writes manifest, source scaffold and locales
  -> new Reaper project directory

The native bridge requires an existing regular .json request file, rejects symlinks and requests larger than 1 MiB, requires a new output path and delegates through Reaper's existing bounded subprocess adapter. It does not import Reaper into the DuckOS process.

## Generated artifact contract

The generator writes:

- jora.app.json — versioned application manifest and composition formula;
- jora.lock.json — component and dependency versions and resolution order;
- src/main.rpr — Reaper flow entry-point scaffold;
- src/components/*.rpr — selected component contract stubs;
- locales/*.json — selected EN/RU/UK/MOST interface dictionaries;
- README.md — project structure, maturity and limits.

A successful generation means only that a new project scaffold was created. The current component records are specifications, not executable editors or translators. Jora reports installable=false, source_executed=false, and no executable capabilities.

## Supported dimensions

| Dimension | Current behavior |
|---|---|
| Feature packs | Text editor, audio editor, translator |
| Generated implementation | Reaper .rpr, flow syntax |
| UI locales | EN, RU, UK, MOST |
| Java/Kotlin/Python/TypeScript/Rust/C | Request metadata only; code-generation adapter pending |
| Installation and updates | Not connected to the operating-system package manager |
| Publication/signing | Not available yet |

MOST is a Russian-language profile. It is emitted as a separate locale package so it can later diverge in terminology or syntax without being misrepresented as another natural language.

## Commands

reaper jora catalog --json
reaper jora compose --request ./request.json --json
reaper jora build --request ./request.json --output ./LexiTone --json
duckos jora build ./request.json ./LexiTone

Initialize the independent Reaper checkout using the existing submodule workflow and install its Python package before invoking the bridge.

## Release gates

Jora's catalogue and scaffold builder are not a package manager. Before an application can be offered as installable, DuckOS still needs a native package lifecycle with cryptographic manifest/signature verification, dependency/license review, permission prompts and enforcement, process isolation, resource quotas, transaction-safe updates and rollback. Every selected module must have implementation, tests and reproducible provenance. A catalogue card or generated stub cannot pass those gates.
