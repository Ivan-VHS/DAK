# DuckOS

**DuckOS — Reaper-native operating-system project.**

DuckOS starts as a set of executable system contracts written in the Reaper language. Its design draws on the supplied `new-wave.txt` specification: the 666-rule language constitution, three execution media, deterministic resource control, memory habitats, bounded data flow, capability security, a driver ABI, the DuckDriver concept and the Tri-Color Duck desktop.

This repository is the OS project. The Reaper repository is its language/toolchain dependency; DuckOS does not copy or rename the Reaper interpreter.

## Current implementation

The first implementation slice is committed in Reaper source files (`.rpr`):

- boot phase ordering and recovery decisions;
- checked memory-region arithmetic and a bounded arena allocator model;
- deterministic priority/deadline task selection;
- bounded IPC queues with explicit backpressure;
- capability checks and capability attenuation;
- versioned driver descriptors and bus/capability validation;
- bounded service restart policy;
- content-addressed graph-node and event-journal contracts;
- three-medium execution policy (CPU, accelerator, node mesh);
- the 65/25/10 DuckOS interface palette and reduced-motion policy.

The contracts are executable under both Reaper reference engines (tree-walk and VM). CI pins the Reaper toolchain commit used for those checks.

## Important boundary

**This is not yet a bootable operating system.** The current Reaper project has a Python reference runtime and a partial native C17 compiler track. It does not yet provide a complete freestanding native backend, UEFI/BIOS loader, interrupt entry, page-table management, scheduler context switch, hardware driver execution, GPU submission backend, Wayland compositor or installable image.

The Reaper code here is executable system-policy and kernel-contract code, not a claim that privileged CPU instructions or physical devices are already controlled by Reaper. Those features are staged behind explicit platform interfaces and must not be reported as implemented until a native target, hardware backend and corresponding tests exist.

## Run the contracts

Requires Python 3.10+ and a checkout of the Reaper repository at the commit pinned in `.github/workflows/reaper-contracts.yml`.

From the DuckOS repository root:

```sh
PYTHONPATH=../Reaper python -m reaper --check contract_tests.rpr
PYTHONPATH=../Reaper python -m reaper contract_tests.rpr
PYTHONPATH=../Reaper python -m reaper --engine vm contract_tests.rpr
```

The workflow checks every DuckOS `.rpr` source file and executes the contract suite with both Reaper engines.

## Repository map

```text
duckos/
  drivers/       driver descriptor and ABI policy
  kernel/        boot, memory, scheduler and bounded IPC
  security/      capability checks and attenuation
  services/      service supervision and restart budgets
  storage/       content-addressed graph and event journal
  system/        CPU / accelerator / node-mesh policy
  ui/            Tri-Color Duck design tokens and motion policy
contract_tests.rpr
docs/
.github/workflows/
```

## Engineering rules

1. Reaper source is the implementation language for DuckOS policy and system logic.
2. Privileged hardware effects are impossible without an explicit native platform binding.
3. Resource limits are explicit and bounded; overload must produce backpressure or a reported failure.
4. Unknown drivers and unverified modules are not loaded.
5. The reference runtime remains a test oracle until a native Reaper backend reaches differential parity.
6. Every feature is labelled implemented, partial, planned or blocked by a missing toolchain capability.
7. No automated process may push unreviewed changes directly to `main`.

See [Architecture](docs/ARCHITECTURE.md), [specification traceability](docs/SOURCE_TRACEABILITY.md) and [implementation status](docs/IMPLEMENTATION_STATUS.md).
