# NEXUS Application Catalog v1

**Status:** proposed application portfolio  
**Host:** Mora / DuckOS  
**Rule:** every entry below is a new application identity. It does not rename, remove, absorb or replace an existing application or repository.

## 1. Product compatibility

The existing Mora applications remain intact, including Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia, Unify, Sestem, SetupUP, ORGze, Abriganza, Olaab, Concrete Thump, Seu-Beu, Sentinel, Restore, Bridge, Control, Proof, Mora Boost, Duck Desktop, Mora Commons and the existing Reaper, Pytyliki, OPlague and VentuSample workbenches.

The NEXUS suite is an additional layer of specialist tools. In particular:

- **TrustVault** complements Sentinel and Proof; it does not replace either.
- **SnapshotVault** complements Restore; it does not replace it.
- **FrameForge** complements Duck Desktop; it does not replace it.
- **Nexus Hub** complements Mora Commons; it does not replace it.
- **PulseLab** complements Cockos and VentuSample; it does not turn VentuSample into a real-time audio engine.
- **VectorScope** complements the existing Pytyliki and OPlague workbenches; it does not reimplement their native measurement engines.

No proposed app should appear as an available launcher item until its executable, manifest, owner, permissions, empty/error states, tests and product documentation exist.

## 2. Application portfolio

All IDs use the reserved proposal namespace `duck.app.*`. These IDs are catalog proposals, not registered executable manifests.

| Application | Proposed ID | Purpose | Primary owner/provider | Initial maturity |
|---|---|---|---|---|
| **Nexus Hub** | `duck.app.nexus-hub` | Browse federation peers, repository pins, contract versions, provider health and compatibility status | DuckOS; reads existing federation manifests | Planned |
| **Agent Forge** | `duck.app.agent-forge` | Edit and validate service, agent and capability descriptors; inspect lifecycle and permission boundaries | DuckOS + Reaper policy contracts | Planned |
| **Worker Grid** | `duck.app.worker-grid` | Inspect task queues, concurrency budgets, priorities, affinity plans and scheduler simulations | Reaper policies; future native scheduler telemetry | Planned |
| **VectorScope** | `duck.app.vector-scope` | Unified CPU, memory, GPU, device and frametime dashboard with source/provenance per metric | Pytyliki + OPlague | Planned |
| **TrustVault** | `duck.app.trust-vault` | Review signatures, hashes, SBOM/license inventory, package provenance, trust roots and verification history | DuckOS security services + OPlague evidence | Planned |
| **RouteMatrix** | `duck.app.route-matrix` | Inspect interfaces, routes, DNS status, traffic classes and bounded QoS profiles | Future DuckOS network service | Planned |
| **PulseLab** | `duck.app.pulse-lab` | Inspect audio assets, offline DSP graphs, render parameters, peaks/RMS and pack manifests | VentuSample | Planned |
| **FrameForge** | `duck.app.frame-forge` | Author and validate window, layout, theme, motion and accessibility profiles | DuckOS desktop layer | Planned |
| **ThermalPilot** | `duck.app.thermal-pilot` | Correlate temperatures, power, utilization and workload; produce advisory profiles | OPlague telemetry + Pytyliki measurements | Planned |
| **SnapshotVault** | `duck.app.snapshot-vault` | Inspect snapshot generations, integrity, retention and recovery readiness | Future DuckOS storage/VFS services | Planned |
| **InputTrace** | `duck.app.input-trace` | Measure input-to-frame timing, queue delay, polling intervals and dropped events | Future DuckOS input/graphics telemetry | Planned |
| **DisplayMatrix** | `duck.app.display-matrix` | Inspect display topology, per-monitor mode, refresh, color/HDR capability and profile compatibility | Future DuckOS display service | Planned |
| **GlyphFoundry** | `duck.app.glyph-foundry` | Manage icon, cursor, font and design-token packs with licensing and provenance checks | DuckOS asset/design tooling | Planned |

## 3. Safe first releases

The first useful releases should be evidence viewers and profile validators, not privileged control panels.

### Wave A — Can be built from existing artifacts

1. **Nexus Hub:** read the current repository federation manifest and OCTA-8 contract; show exact pinned commits, status and missing peers.
2. **VectorScope:** display existing Pytyliki reports and OPlague device/GPU snapshots. Every value must carry provider, capture time, units and validity. Unsupported values remain unknown.
3. **PulseLab:** inspect VentuSample pack manifests and offline render metadata without loading or executing external plugins.
4. **TrustVault:** present existing hashes, Authenticode/signature evidence and SPDX data as evidence. A hash is not a signature, and a report is not a trust decision.

### Wave B — Requires native DuckOS services

- **Agent Forge** and **Worker Grid** require stable service lifecycle, scheduler and capability contracts before they may create or schedule real processes.
- **RouteMatrix** requires an implemented network service; a visual mockup must not imply active packet shaping.
- **SnapshotVault** requires a crash-consistent VFS/storage and tested restore transaction.
- **InputTrace** and **DisplayMatrix** require real input and display providers.
- **FrameForge** and **GlyphFoundry** can begin as offline profile/asset editors, but may apply profiles only through validated desktop APIs.
- **ThermalPilot** remains advisory until platform-specific controls have explicit authorization and rollback.

## 4. Shared application requirements

Every application must declare:

- stable application ID and independent display name;
- owning repository and source/version provenance;
- required host version and capability set;
- input schemas, size limits, data retention and export format;
- read-only or mutation mode, with consent scope for each mutation;
- provider identity and timestamps for externally sourced values;
- unsupported, stale, permission-denied and provider-unavailable states;
- keyboard access, localization, reduced-motion behavior and accessibility metadata;
- tests for valid input, malformed input, missing peer, version mismatch and cancellation.

Apps must be local-first and offline-capable where their domain permits. No hidden cloud, analytics, background execution or external asset fetch is introduced by this catalog.

## 5. Naming rules

Use technical names that describe the task. Do not use music-genre or track-title phrases as architecture names, package IDs, service names or diagnostics. Keep legitimate audio terms inside audio products where they are technically meaningful.

Do not recycle the names of existing products or applications for a new tool. Do not prefix all applications with `Nexus`; NEXUS is the architecture profile, while each application has its own identity.

## 6. Release gates

An entry moves from **Planned** to **Prototype** only when a buildable application shell and manifest exist. It moves to **Implemented** only when the intended provider is connected and the relevant automated tests pass. An app that only displays static examples remains a prototype and must visibly label its data as sample data.
