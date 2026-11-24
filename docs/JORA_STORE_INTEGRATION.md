# Jora store and Reaper composition bridge

**Desktop:** Mora / DuckOS  
**Generator:** Reaper  
**Current status:** local catalogue + request composer + safe CLI bridge; generated output is a scaffold only

## User-facing model

Jora is the single product identity for the store, composer, generator and every generated application. Users pick capability modules, interface locales, a naming presentation style and graph architecture preferences. Jora itself is always named Jora; generated name options are descriptive Jora labels, not separate brands.

Example:

Text Editor + Audio Editor + Translator = Jora

Mora's browser surface performs local composition preview and exports a versioned JSON request. It does not launch host processes. This preserves the existing security boundary: browser JavaScript is not a local command runner.

## End-to-end flow

Mora / Jora composer
  -> select components, naming style, locales and graph architecture
  -> reaper.jora.request.v1 JSON file
  -> user invokes local DuckOS CLI
  -> duckos jora build request.json output-directory
  -> DuckOS ReaperWorkbench validates paths and invokes Reaper with argv and shell=False
  -> Reaper resolves dependencies and writes manifest, source scaffold and locales
  -> new Reaper project directory

The native Duck Desktop Reaper tab can select the exported JSON request, choose a destination path and start generation on a worker thread. The CLI is also available. Both use the same native bridge, which requires an existing regular .json request file, rejects symlinks and requests larger than 1 MiB, requires a new output path and delegates through Reaper's existing bounded subprocess adapter. It does not import Reaper into the DuckOS process.

## Naming and graph variability

The naming engine keeps the canonical application name fixed as **Jora**. It derives semantic descriptors from the selected component domains and offers compact, balanced, descriptive and formula-style labels such as `Jora — Documents & Languages Workspace`. No combination is published under a separate invented brand.

The graph engine can generate 1–6 alternatives for one feature formula. Its topologies include layered composition, sequential pipeline, shared orchestrator, capability mesh, event-driven and hybrid. Each topology can itself use distinct direct, domain-grouped, capability-routed, stateful, validated or extensible rewrites. Each node and edge has a type; compatible provider/consumer pairs can be connected directly or brokered. A variation budget controls optional extension and validation layers, and the seed makes the output reproducible. Users can also optimize graph selection for balanced quality, low latency, modularity, extensibility or minimal complexity. Jora scores every candidate against the chosen objective and selects the highest-ranked graph with deterministic tie-breaks.

Hard dependency edges must be acyclic. Event feedback is only allowed asynchronously through the explicit event bus. Planned extension registries and compatibility gates are labelled as planned, not implemented services.

The graph set is embedded in the application manifest and also saved to `jora.graphs.json`. Readable Mermaid diagrams are generated under `graphs/variant-*.mmd`. The lock file records the selected naming label, graph objective, winning score, graph IDs and signatures. The selected graph is the highest-scoring candidate, ranked by compatibility, reusable capability links, fewer planned nodes and then a stable signature tie-break.

## Generated artifact contract

The generator writes:

- jora.app.json — versioned application manifest and composition formula;
- jora.lock.json — component/dependency versions, naming version and graph signatures;
- jora.graphs.json — generated graph alternatives, typed nodes/edges, topology labels and compatibility metrics;
- src/main.rpr — Reaper flow entry-point scaffold;
- src/components/*.rpr — selected component contract stubs;
- locales/*.json — selected EN/RU/UK/MOST interface dictionaries;
- README.md — project structure, maturity and limits.

A successful generation means only that a new project scaffold was created. The current component records are specifications, not executable editors or translators. Jora reports installable=false, source_executed=false, and no executable capabilities.

## Supported dimensions

| Dimension | Current behavior |
|---|---|
| Feature packs | 21 canonical capability contracts across text, media, language, productivity, development, data, visual, video, documents, system, network, automation and analytics |
| Generated implementation | Reaper .rpr, flow syntax |
| UI locales | EN, RU, UK, MOST |
| Java/Kotlin/Python/TypeScript/Rust/C | Request metadata only; code-generation adapter pending |
| Installation and updates | Not connected to the operating-system package manager |
| Publication/signing | Not available yet |

MOST is a Russian-language profile. It is emitted as a separate locale package so it can later diverge in terminology or syntax without being misrepresented as another natural language.

## Commands

reaper jora catalog --json
reaper jora compose --request ./request.json --json
reaper jora build --request ./jora-request.json --output ./Jora --json
duckos jora build ./jora-request.json ./Jora

Initialize the independent Reaper checkout using the existing submodule workflow and install its Python package before invoking the bridge.

## Release gates

Jora's catalogue and scaffold builder are not a package manager. Before an application can be offered as installable, DuckOS still needs a native package lifecycle with cryptographic manifest/signature verification, dependency/license review, permission prompts and enforcement, process isolation, resource quotas, transaction-safe updates and rollback. Every selected module must have implementation, tests and reproducible provenance. A catalogue card or generated stub cannot pass those gates.


## Expanded capability catalogue and Reaper binding

Mora renders the capability list from the same canonical component IDs consumed by Reaper, rather than maintaining a three-item UI list. The selected formula supports up to 24 unique components. For formulas above 12 packs, Reaper builds domain-cluster gateways and bounds direct provider/consumer neighbours; graph node and edge counts have finite generation budgets.

DuckOS pins the Reaper submodule to the matching `feature/jora-app-factory` commit while the cross-repository Reaper pull request is under review. The native bridge continues to use argument arrays and `shell=False`; the browser composer only exports a request and never starts processes.

The DAK catalogue registers `dak.jora` and reserves `dak.app-synthesis.v1`. This DAK service is a contract reservation, not a completed native kernel/service provider. Generated projects remain statically validated source scaffolds, not installable or executable applications. Extra-language selections are generated as explicit `adapter_pending` plans until their language-specific backends are implemented.

The seed registry covers 21 canonical packs today. The 666 detailed variations are not silently represented as complete: they must be imported and verified as a separately versioned catalogue expansion.
