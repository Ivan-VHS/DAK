# Dak 2026 ecosystem evolution

**Scope:** Dak/Mora and the four specialist repositories federated by Dak.  
**Review baseline:** 2026-11-24.  
**Normative rule:** a roadmap, catalogue entry, UI preference, repository pin or mock-up is not evidence that a native capability has shipped.

## 1. Architecture map

Dak is the operating-system superproject. Mora is its shared desktop environment. It owns the browser workspace, launch catalogue, app windows, local presentation preferences and entry points into native tools. Mora is not the kernel, native compositor or privileged process broker.

| Project | Owned domain | Integration boundary |
|---|---|---|
| Dak / Mora | Desktop, first-party apps, system policy, native integration | Shell and bounded user-space orchestration |
| Reaper | Language, compiler, runtime, Studio and developer toolchain | Primary/native language for new Dak-owned system code; user-space toolchain |
| Pytyliki | C11 processor/system inspection and bounded measurement | Read-only inventory and evidence reports |
| OPlague | Device/driver evidence and Windows gaming workbench | Read-only package inspection and reversible user sessions |
| VentuSample | C++20 procedural audio and offline DSP | Offline render jobs and versioned manifests |

The four specialist projects remain independently versioned submodules at exact commits. Preserve source history, licences, release cadence and established implementation domains. Do not copy their source into Dak or silently advance their pins.

## 2. 2026 engineering principles

### 2.1 Local-first, offline-first and data ownership
- Local reads and edits should complete without a network round trip.
- Use versioned data contracts, bounded payloads, deterministic migrations, export/import and explicit recovery.
- Use IndexedDB for browser-shell documents where it fits. Use SQLite or DakDB in native product domains when the data model and workload justify them.
- Add CRDT replication only for a verified multi-writer or multi-device requirement. Define conflict resolution, tombstones, causal metadata, retention and idempotency before sync is enabled.
- A cache or local database is not a sync engine. No background or cloud sync is implied by this plan.

### 2.2 Reaper-first Dak-native development
- New Dak-owned native services, examples and system-facing code should use Reaper as the primary language, with contracts and compiler tests alongside implementation.
- Specialist projects remain in their own technical domains: Pytyliki C11, VentuSample C++20 and OPlague's existing Python/C++ boundaries are not rewritten simply for cosmetic uniformity.
- Preserve canonical typed IR, Span/SourceMap, deterministic diagnostics, explicit ABI, bounded allocation and clear user/kernel boundaries.
- MMIO, DMA, IRQ contexts, memory management, device access, process scheduling and loader behavior require native verification and a distinct privileged-service review.

### 2.3 AI-assisted workflows with explicit authority
- An assistant or local planner returns a typed, inspectable action plan; it never returns arbitrary shell text for execution.
- Each mutating action requires a target identity, capability, precondition, impact summary, explicit approval, audit event and rollback semantics.
- Local model inference and NPU scheduling are separate capabilities. They remain planned until an actual runtime, hardware discovery and resource policy are connected and tested.
- Never let agent automation install drivers, alter firmware, mutate system files or change device state without a separately reviewed native capability broker.

### 2.4 Adaptive, accessible desktop
- Preserve keyboard operation, visible focus, semantic controls, readable scaling, responsive reflow, reduced motion and appropriately sized hit targets.
- Test keyboard-only, touch, narrow-window, high-contrast and assistive-technology workflows; do not encode meaning in color alone.
- Keep app-specific visual identity scoped to each app. Mora's shared shell identity remains black/white/yellow.
- Treat spatial/XR, speech, gesture and advanced multimodal input as separate native services, not CSS-only claims.

### 2.5 Security, supply chain and provenance
- Apply least privilege, deny-by-default capability policy, input bounds, strict path handling, dependency inventory, reproducible builds and verifiable provenance.
- Treat archives, manifests, packages, plugins, model files and user imports as untrusted.
- Keep device and driver workflows read-only until a signed package lifecycle, privileged broker, rollback and recovery path are implemented and reviewed.
- Use OWASP Top 10:2025 as an awareness baseline, plus repository-specific threat models and code review; it is not a compliance certificate.

### 2.6 Performance, energy and predictable interaction
- Measure cold start, idle CPU, memory, rendering cost, data size and build/test time before optimizing.
- Prefer event-driven updates, bounded work queues, incremental DOM changes, cancellation and cached immutable metadata over perpetual polling.
- Eco and Reduced Motion profiles must suppress decorative work. Do not render expensive effects while a workspace is idle.
- Preserve semantics when caching, quantizing or vectorizing. Document units, precision, error bounds and fallback behavior.

### 2.7 Compatibility and modular integration
- Register every app and system tool with a stable identifier, owner, maturity, data policy and versioned manifest.
- Use adapters with explicit schemas/ABIs and failure semantics. No implicit FFI or dynamic loading.
- Keep the four specialist projects as opt-in or contract-driven tools; repository presence is not evidence that a native service is installed or launched.
- Maintain reversible migration paths for display labels and names. ORGze is the product-facing name; the existing `orriganize` identifier remains stable for compatibility.

## 3. Implemented vertical in this branch

| Capability | Status | Evidence target |
|---|---|---|
| Red Sparrow / 赤雀 Mora app | partial | app catalogue, launcher, window and local note editor |
| Separate `ru-RU` / `zh-CN` locale preference | partial | Control selector, local preference key and localized shell labels/date/time |
| Mandarin Red Sparrow workspace | partial | Chinese panel content under `zh-CN` |
| Local-first note store | partial | IndexedDB-first module, bounded payload and localStorage fallback |
| Full translation of legacy app panels | planned | Translate and review each panel, including validation/error states |
| CRDT or multi-device sync | planned | Requires user-approved sync scope and conflict contract |
| Native capability broker and OS updater | planned | Requires native service implementations and platform tests |

A partial maturity status is deliberate: this patch does not claim full system localization, cloud sync, native app sandboxing, OS-image rollback or kernel enforcement.

## 4. Cross-project contracts

- **Reaper → Dak:** versioned user-space CLI, compiler/runtime and subprocess contracts; no implicit kernel privilege.
- **Pytyliki → Dak/OPlague:** bounded processor inventory and measurement evidence through versioned reports; no hardware mutation.
- **OPlague → Dak:** read-only device, driver-package and performance evidence; no automatic installation or payload execution.
- **VentuSample → Dak:** offline render jobs, audio manifests and bounded DSP contracts; no real-time device access by default.
- **Mora → native tools:** catalogue entries and explicit workbench links; the browser shell never impersonates a native service.
- **Red Sparrow → Mora:** creative panel and local notes only; no privilege escalation or external executable content.

Every cross-project edge must name provider, consumer, owner, schema/ABI version, direction, maturity, error behavior and verification evidence.

## 5. Evidence-led delivery sequence

1. Inventory source, tests, build systems, contracts and licences.
2. Record a reproducible baseline before changing behavior.
3. Implement one bounded vertical slice per repository on a reviewable branch.
4. Run each repository's own native build, unit tests, static checks and CI.
5. Validate schemas and cross-project fixtures against pinned partner commits.
6. Review security, migration, performance, localization and accessibility.
7. Open separate PRs. Protect `main`; merge sequentially only after review and passing checks.
8. Update submodule pins only after the upstream changes are reviewed and validated.

## 6. Acceptance checklist

- No project identity, licence notice, source history or established implementation domain is overwritten.
- No capability is called implemented without code and reproducible verification.
- No registry relationship is called a runtime integration without an exercised adapter.
- Local data has a schema, size limit, failure behavior and export/recovery strategy.
- Chinese selection survives reload and does not alter repository names, source language or compiler contracts.
- User text is inserted as text, never interpreted as executable HTML.
- Keyboard, focus, Reduced Motion and responsive behavior remain intact.
- No hidden network requests, telemetry export, arbitrary shell execution or automatic driver/firmware changes are introduced.

## 7. References

- Web Platform Baseline: https://web.dev/baseline/
- W3C WCAG 2.2: https://www.w3.org/TR/WCAG22/
- WAI-ARIA keyboard interaction guidance: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- OWASP Top 10:2025: https://owasp.org/Top10/
- Microsoft Windows app best practices: https://learn.microsoft.com/windows/apps/get-started/best-practices

These references inform design and verification; they do not certify Dak compliance by themselves.
