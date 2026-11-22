# DuckOS

**DuckOS — Reaper-native operating-system project.**

DuckOS is developed as a system whose policy and service logic are written in the Reaper language. Its architecture is traced to the supplied `new-wave.txt` specification: the six 111-rule language domains, three execution media, bounded memory habitats, flow control, semantic storage, capability security, DuckDriver Core and Tri-Color Duck UI.

This repository is the OS project. The Reaper repository is its language/toolchain dependency; DuckOS does not copy or rename the Reaper interpreter.

## Current implementation

The first executable contract kernel is written in `.rpr` and checked by the pinned Reaper toolchain:

- ordered boot phases, transition validation and recovery decisions;
- checked signed-address arithmetic, aligned arenas, frame reset and SoA layout;
- deterministic priority/deadline task selection and least-loaded worker choice;
- bounded FIFO IPC and byte-accounted zero-copy bus backpressure;
- explicit capabilities, non-amplifying grants and trust/taint transitions;
- driver ABI/package metadata checks and resource-conflict detection;
- finite service restart policy;
- content-addressed graph reference checks, monotonic event journal and deterministic LWW register merge;
- CPU / accelerator / node-mesh placement policy;
- bounded telemetry history and warning/critical thresholds;
- Tri-Color Duck palette, reduced-motion and frame-budget policy.

## Important boundary

**This is not yet a bootable operating system.** Reaper currently has a Python reference runtime and a partial native C17 compiler track. It does not yet provide a complete freestanding native backend, UEFI/BIOS loader, interrupt entry, page-table management, context switching, real driver loading, GPU submission, Wayland compositor or installable image.

The current modules are executable Reaper policy contracts. For example, the UDB bus accounts bounded bytes but does not map shared pages; DuckDriver validates supplied metadata but does not enumerate devices, cryptographically verify package signatures or install drivers; the telemetry module validates supplied samples but does not read sensors; the graph module validates references but does not implement BLAKE3 or a persistent hypergraph database.

These boundaries are intentional. A passing reference-runtime test does not prove privileged hardware access, zero-copy performance, hard real-time behavior or bootability. Each such capability needs a native Reaper backend, a platform binding and hardware/emulator evidence.

## Run the contracts

Requires Python 3.10+ and a checkout of Reaper at the commit pinned in `.github/workflows/reaper-contracts.yml`.

From the DuckOS repository root:

```sh
PYTHONPATH=../Reaper python -m reaper --check contract_tests.rpr
PYTHONPATH=../Reaper python -m reaper contract_tests.rpr
PYTHONPATH=../Reaper python -m reaper --engine vm contract_tests.rpr
```

CI checks every DuckOS `.rpr` source file and executes the contract suite with both Reaper engines.

## Repository map

```text
duckos/
  drivers/       ABI, device-resource and package policy
  kernel/        boot, memory, arenas, scheduler, flock and IPC
  security/      capabilities and trust boundaries
  services/      service supervision and restart budgets
  storage/       hypergraph references, journal and CRDT register
  system/        CPU / accelerator / mesh and telemetry policy
  ui/            Tri-Color Duck theme and motion policy
contract_tests.rpr
docs/
.github/workflows/
```

## Engineering rules

1. Reaper source is the implementation language for DuckOS policy and system logic.
2. Privileged hardware effects require explicit, auditable native platform bindings.
3. Memory, queues, retries and telemetry history are bounded; overload is visible.
4. Unknown devices, unsigned packages and ungranted capabilities are rejected by policy.
5. The reference runtime remains a test oracle until a native Reaper backend reaches differential parity.
6. A feature is labelled implemented, partial, planned or blocked by a missing toolchain capability.
7. No automated process may push unreviewed changes directly to `main`.

See [Architecture](docs/ARCHITECTURE.md), [specification traceability](docs/SOURCE_TRACEABILITY.md) and [implementation status](docs/IMPLEMENTATION_STATUS.md).
