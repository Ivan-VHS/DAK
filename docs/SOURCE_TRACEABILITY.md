# Source specification traceability

## Source record

- Library item: `new-wave.txt`
- Library file ID: `libfile_994715715f188191a8e9a9adae31ef86`
- Materialised source size: 1,780,277 bytes
- Source line count: 11,512
- SHA-256: `9d9a17d21a3d8da606d98539ff0119e09f36cb212743abb491bdbf2a64be4732`

The original remains in the user's ChatGPT Library. This repository records the source identity and implementation mapping rather than silently rewriting the original document.

## Six 111-rule domains

The language constitution in the source groups its 666 rules into six domains. The complete wish-list is not treated as proof that the language already supports those features. Each domain is mapped to a testable OS responsibility:

| Source domain | DuckOS projection | Source modules | Current evidence |
|---|---|---|---|
| 1–111: three-medium computation | CPU / accelerator / node-mesh choice and explicit backend availability | `duckos/system/three_media.rpr` | policy tests; no GPU or network backend |
| 112–222: calm and transparency | bounded inputs, explicit resource decisions and a minimal UI token set | `duckos/kernel/memory.rpr`, `duckos/ui/theme.rpr` | range and palette contracts |
| 223–333: type and data semantics | validated descriptors and explicit data shapes | `duckos/drivers/abi.rpr`, `duckos/storage/hypergraph.rpr` | descriptor and node-shape tests; no full static refinement checker |
| 334–444: effects and immunity | capability checks, attenuation and controlled recovery | `duckos/security/capabilities.rpr`, `duckos/services/supervisor.rpr` | policy tests; kernel enforcement pending |
| 445–555: concurrency and flock scheduling | deterministic task selection and bounded message queues | `duckos/kernel/scheduler.rpr`, `duckos/kernel/ipc.rpr` | pure contract tests; no preemptive concurrency |
| 556–666: freedom, self-hosting and ergonomics | source/toolchain boundary, documented API and Duck UI tokens | `duckos/ui/theme.rpr`, `docs/ARCHITECTURE.md` | design tokens and bring-up gates; no self-hosted native compiler |

## Desktop system excerpt

| Source area | DuckOS module or decision |
|---|---|
| Four-layer architecture and CPU/GPU/mesh substrate (around lines 1416–1494) | `docs/ARCHITECTURE.md`, `duckos/system/three_media.rpr` |
| Semantic hypergraph and content addressing (1436–1439) | `duckos/storage/hypergraph.rpr`; hash generation remains an external cryptographic primitive |
| Habitats, frame arenas, FBIP and SoA (1441–1445) | `duckos/kernel/memory.rpr`; physical allocation and compiler ownership analysis remain pending |
| TCD-UI 65/25/10 palette (1496–1512) | `duckos/ui/theme.rpr` |
| Device orchestration and DuckDriver Core (around lines 2661–2685) | `duckos/drivers/abi.rpr`; hardware scan, INF parsing, signature validation and installation are not implemented |
| Reaper R1–R14 development roadmap (5576–6197) | remains in the Reaper toolchain repository; DuckOS pins Reaper as a language/toolchain dependency rather than copying its IDE/DAP |
| TCD desktop notes and motion prototype (6902 onward) | design constraints recorded here; the original browser prototype is not misrepresented as a native OS shell |

## Other repository-specific proposals in the source

The source also includes feature proposals for Pytyliki, VentuSample and OPlague. They remain owned by those repositories. DuckOS may later consume stable interfaces from those projects, but this initial commit does not duplicate their source or claim their features as DuckOS implementations.

## Acceptance rule

A row moves from “planned” to “implemented” only when the implementation exists in DuckOS source, the relevant test passes under the pinned Reaper runtime, and (for hardware-facing claims) a native target or emulator test provides evidence. A source specification, catalogue entry, dashboard mock-up or green unit test alone cannot prove physical hardware functionality.
