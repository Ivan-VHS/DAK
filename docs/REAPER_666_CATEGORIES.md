# Reaper 666 — DuckOS category integration

**Canonical registry owner:** [Ivan-VHS/Reaper](https://github.com/Ivan-VHS/Reaper)  
**Category scheme:** `duckos-reaper-architecture/v1`  
**Registry:** [`language/functions_666.json`](https://github.com/Ivan-VHS/Reaper/blob/main/language/functions_666.json)  
**Human-readable full index:** [Function categories 666](https://github.com/Ivan-VHS/Reaper/blob/main/docs/FUNCTION_CATEGORIES_666.md)

This document maps Reaper's seven architecture categories to DuckOS subsystems. It does not copy or redefine the 666 contracts. Reaper owns stable function IDs, signatures, contracts and implementation states; DuckOS owns the OS integration points and target-specific acceptance evidence.

## Category ownership

| Category ID | Functions | DuckOS ownership | Reaper ownership | Current boundary |
|---|---:|---|---|---|
| `kernel-runtime` | 121 | `duckos/kernel/`, `duckos/platform/`, `duckos/drivers/` | Systems language, runtime contracts and compiler target | Stage 1 boot and early frame allocation exist; process runtime, reusable VM, scheduler and syscall enforcement are not complete |
| `language-compiler` | 260 | `projects/reaper` integration and system build profiles | `reaper/`, `src/`, `include/reaper/`, `language/` | Python reference runtime is broad; native C17 and scalar AOT are partial, not full compiler parity |
| `desktop-ui` | 22 | `mora/`, future native desktop/compositor | Language-level UI and tooling adapters where applicable | Mora browser shell is a host application, not a kernel compositor |
| `network-distributed` | 21 | `duckos/network/`, service and transport boundaries | Protocol contracts, bounded adapters and library APIs | Network policy descriptors do not implement NIC drivers or a complete TCP/IP stack |
| `storage-data` | 121 | `duckos/storage/`, future block and filesystem services | Serialization, schema, stream and data APIs | VFS contracts do not mount filesystems or implement durable block I/O |
| `security-resilience` | 100 | `duckos/security/`, BAV policy and future kernel hooks | Capability/effect contracts, validation and audit interfaces | Reference policy and bundle schemas are not kernel-enforced MAC, endpoint scanning or a sandbox |
| `ecosystem-tooling` | 21 | `federation/`, manifests, release and integration contracts | Build profiles, diagnostics, test and profiling tools | Host tooling and metadata do not grant kernel privilege or imply target-runtime support |

**Count check:** 121 + 260 + 22 + 21 + 121 + 100 + 21 = **666**.

## Implementation order

Categories are ownership and navigation units, not a demand to implement them in numeric order. Dependencies determine execution order:

1. **Registry and ABI alignment:** pin the Reaper commit, freeze category and function IDs, version the shared ABI, and define host/freestanding runtime profiles.
2. **Kernel memory foundation:** extend the existing frame allocator to a reusable allocator, page tables, mappings, ownership, and MMIO/DMA admission.
3. **Execution foundation:** implement interrupt-safe scheduling, process/thread lifecycle, syscall entry, user-buffer validation, and capability enforcement.
4. **IPC and services:** implement bounded endpoints, cancellation, wakeups, service supervision, and audit events.
5. **Storage and networking:** select the first filesystem and block interface; then add bounded network transport and policy enforcement.
6. **Security integration:** connect BAV verification and scanning only after process isolation, IPC, persistent storage and trust roots are real.
7. **Desktop and federation:** connect the native compositor and application broker to verified system services; keep Mora browser mode as a separate host surface.

The primary implementation and CI target remains vendor-neutral x86_64 for Intel and AMD. Elbrus remains a separate compatibility/backend track and is not removed from architecture policy.

## Cross-repository integration rules

- Reaper is the sole source of truth for the 666 contracts and the seven `architecture_category` assignments.
- DuckOS references exact Reaper commits through its federation pin; it must not silently fork or renumber function IDs.
- Every cross-repository API change updates the owner-side contract first, then the consumer adapter and integration fixtures.
- Generated inventories and schemas are versioned; unknown fields and unsupported ABI versions fail closed.
- Category membership never changes maturity. A function is delivered only when target source, positive and negative tests, resource bounds, compatibility checks and required CI prove it.
- Read-only or offline boundaries stay explicit: OPlague device inspection remains read-only; VentuSample processing remains offline; Pytyliki metrics use an explicit trusted ABI path.

## Evidence and maturity references

- [DuckOS implementation status](IMPLEMENTATION_STATUS.md)
- [DuckOS native implementation roadmap](IMPLEMENTATION_ROADMAP.md)
- [DuckOS Core MVP v1](CORE_MVP_V1.md)
- [Reaper hardware-language boundary](https://github.com/Ivan-VHS/Reaper/blob/main/docs/HARDWARE_LANGUAGE.md)
- [Reaper 666 implementation registry](https://github.com/Ivan-VHS/Reaper/blob/main/docs/MOST_FUNCTIONS_666.md)

A passing Reaper reference-runtime contract test proves the policy/model behavior on that runtime only. Native DuckOS capability requires a separate target-specific implementation and test.
