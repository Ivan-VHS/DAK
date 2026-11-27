# Source specification traceability

## Source record

- Library item: `new-wave.txt`
- Library file ID: `libfile_994715715f188191a8e9a9adae31ef86`
- Materialised source size: 1,780,277 bytes
- Source line count: 11,512
- SHA-256: `9d9a17d21a3d8da606d98539ff0119e09f36cb212743abb491bdbf2a64be4732`

The original remains in the user's ChatGPT Library. This repository records the source identity and implementation mapping rather than silently rewriting the original document.

## Six 111-rule domains

The language constitution in the source groups its 666 rules into six domains. The full wish-list is not treated as proof that Reaper or Dak already supports every feature. Each domain is mapped to a testable OS responsibility:

| Source domain | Dak projection | Source modules | Current evidence |
|---|---|---|---|
| 1–111: three-medium computation | CPU / accelerator / node-mesh placement and bounded worker selection | `dakos/system/three_media.rpr`, `dakos/kernel/flock.rpr` | policy tests; no GPU or network backend |
| 112–222: calm and transparency | explicit budgets, aligned arenas, bounded history and UI frame status | `dakos/kernel/memory.rpr`, `dakos/kernel/arena.rpr`, `dakos/system/telemetry.rpr`, `dakos/ui/motion.rpr` | arithmetic, sizing and threshold contracts |
| 223–333: type and data semantics | validated descriptors, graph references and deterministic register merge | `dakos/drivers/abi.rpr`, `dakos/drivers/orchestrator.rpr`, `dakos/storage/hypergraph.rpr`, `dakos/storage/crdt.rpr` | descriptor/merge tests; no full static refinement checker |
| 334–444: effects and immunity | capability attenuation, trust promotion and quarantine | `dakos/security/capabilities.rpr`, `dakos/security/trust.rpr`, `dakos/services/supervisor.rpr` | policy tests; kernel enforcement pending |
| 445–555: concurrency and flock scheduling | priority/deadline policy, worker choice, bounded IPC and byte-accounted flow control | `dakos/kernel/scheduler.rpr`, `dakos/kernel/flock.rpr`, `dakos/kernel/ipc.rpr`, `dakos/kernel/zero_copy_bus.rpr` | deterministic tests; no preemptive concurrency or shared pages |
| 556–666: freedom, self-hosting and ergonomics | source/toolchain boundary, inspectable API and Tri-Color Dak interaction policy | `dakos/ui/theme.rpr`, `dakos/ui/motion.rpr`, `docs/ARCHITECTURE.md` | design/policy tests; no self-hosted native compiler |

## Desktop and driver architecture excerpts

| Source area | Dak module or decision |
|---|---|
| Four-layer architecture and CPU/GPU/mesh substrate (around lines 1416–1494) | `docs/ARCHITECTURE.md`, `dakos/system/three_media.rpr`, `dakos/kernel/flock.rpr` |
| Semantic hypergraph, content addressing and CRDT (1436–1439; extended in the AETHER architecture chapter) | `dakos/storage/hypergraph.rpr`, `dakos/storage/crdt.rpr`; hash generation and durable graph store remain external |
| Habitats, frame arenas, FBIP and SoA (1441–1445) | `dakos/kernel/memory.rpr`, `dakos/kernel/arena.rpr`; physical allocation and compiler ownership analysis remain pending |
| Zero-copy bus and backpressure | `dakos/kernel/zero_copy_bus.rpr`; currently byte-accounting policy only, not shared memory |
| TCD-UI 65/25/10 palette and motion prototype (1496–1512; 6902 onward) | `dakos/ui/theme.rpr`, `dakos/ui/motion.rpr`; no native compositor |
| DakDriver Core and unified device topology (around lines 2661–2685) | `dakos/drivers/abi.rpr`, `dakos/drivers/orchestrator.rpr`; no hardware scan, cryptographic verifier or installer |
| Reaper R1–R14 development roadmap (5576–6197) | remains in the Reaper toolchain repository; Dak pins Reaper as a language/toolchain dependency rather than copying its IDE/DAP |
| Other proposals for Pytyliki, VentuSample and OPlague | remain owned by their respective repositories; this integration does not duplicate their source |

## Acceptance rule

A row moves from “planned” to “implemented” only when the implementation exists in Dak source, the relevant test passes under the pinned Reaper runtime, and (for hardware-facing claims) a native target or emulator test provides evidence. A source specification, catalogue entry, dashboard mock-up or green unit test alone cannot prove physical hardware functionality.
