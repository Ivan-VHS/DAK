# DuckOS NEXUS ecosystem integration

**Scope:** the four specialist source trees physically vendored into the DuckOS monorepo.  
**Source of truth:** `federation/vendor-sources.v1.json` pins exact upstream commit and root-tree SHAs; `federation/nexus-peers.v1.json` describes owned contracts and permitted data flows.

## Integration model

DuckOS is the integration host. Reaper is the primary language and toolchain for DuckOS-owned system code. Pytyliki, OPlague and VentuSample remain independent specialist products with their own preserved source directories, build systems, tests and licences inside the monorepo. Their upstream repositories remain the authoritative development origins.

Use direct, versioned peer contracts rather than introducing a second message bus or a mandatory central runtime. The preferred first exchange is a bounded JSON report or immutable file artifact. Native library calls require an explicitly trusted local path, ABI/version validation and caller-owned buffers. DABI64 Desktop Host v1 is a validated wire-frame contract; it is not yet a working kernel IPC transport.

## Peer ownership and integration boundaries

| Peer | DuckOS role | Existing contract family | Current boundary |
|---|---|---|---|
| Reaper | Primary language, compiler/toolchain and deterministic policy layer | DABI64 Desktop Host v1; NEXUS federation profile | Host-native toolchain and frame validators; kernel transport and privileged service dispatch pending |
| Pytyliki | Processor, memory and diagnostics evidence | `pytyliki.c-abi.v1`; NEXUS diagnostics and service-boundary profiles | Native C11 host workbench; bounded read-only evidence, not a page allocator or scheduler |
| OPlague | Device, package, signature and GPU evidence | `oplage.device-snapshot.v1`; `oplage.gpu-telemetry.v1` | Read-only user-space inspection; no automatic driver or firmware changes |
| VentuSample | Procedural audio, sample assets and offline DSP | `ventusample.pack.v1`; preset v1; NEXUS audio profile | Native C++20 host workbench; offline processing, not AudioSubsys or a real-time driver |

The machine-readable contract inventory is `federation/nexus-peers.v1.json`, validated by `schemas/nexus-peer-registry.v1.schema.json` and `tests/mora-nexus-federation.test.mjs`.

## Build and verification path

The existing ecosystem release pipeline is the integration build gate. It checks exact vendored tree hashes, upstream commit provenance, file counts, content byte counts and preserved licenses, tests Mora, builds and tests Reaper's native C17 tools, builds and tests Pytyliki's C11 tools, builds and tests VentuSample's C++20/Qt target, validates OPlague's user-space sources and tests, packages source and licence notices, then verifies the x86_64 BIOS/UEFI Stage 1 image in QEMU.

Run it from a complete checkout:

```sh
git clone https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS
npm test
bash boot/build-release-iso.sh --work-dir build/release --output dist/DuckOS-Release-x86_64.iso
```

The release CI job repeats the build and QEMU boot checks on pull requests that change `federation/**` or `projects/**`. Passing that job will prove compatibility of the exact pinned source set for this host build and Stage 1 image—not that each project is a native DuckOS process or kernel service.

## Native integration stages

1. **Monorepo source import — implemented in the vendor workflow.** Four upstream source snapshots are copied into ordinary tracked directories using exact `git subtree --squash` imports. The upstream commit and tree SHA, file count, content bytes and licenses are locked and verified. Full historical development remains in the upstream repositories.
2. **Host workbenches — partial.** The release build compiles and tests the declared host tools. Mora discovers project metadata and build guidance; launch remains panel-only and does not execute imported commands.
3. **User-space peer adapters — next.** Implement narrow Reaper-owned adapters that validate peer schema versions, bounds, provenance, freshness and typed unavailable/error states. Keep hardware and filesystem actions read-only unless a separate reviewed capability contract exists.
4. **DABI64 transport — pending.** Implement kernel-derived sender identity, handle ownership, sequence tracking, quotas and capability checks only after the process, syscall and IPC foundations exist.
5. **Native DuckOS services — pending.** Device supervision, persistent storage, desktop/window services and AudioSubsys require their own native source, failure recovery, tests and target evidence.

## Non-negotiable boundaries

- A vendored source directory is code availability, not runtime integration.
- A successful host build is not proof of a freestanding DuckOS executable.
- Reaper policy tests are not kernel enforcement.
- Pytyliki reports cannot change clocks, voltage, affinity, firmware, MMIO or scheduling.
- OPlague evidence cannot install, enable, unload or replace drivers; a hash is not a trust verdict.
- VentuSample offline DSP cannot access devices, record audio in the background or enter a real-time callback by implication.
- A peer may be missing. Consumers must return a typed unavailable state and must not perform a partial privileged action.
- Imported code is never automatically built, loaded or executed by a normal OS boot. The explicit release build is a reviewed host-toolchain workflow.

## Completion criteria

The ecosystem is fully integrated only when every peer has: a source pin and licence record; a versioned interface owner; a tested DuckOS adapter; failure and malformed-input tests; an explicit user-space/capability boundary; a native build/packaging path; and a target-specific acceptance test. Kernel or device claims additionally require QEMU or hardware evidence for the actual native service.

The current source lock and roadmap intentionally do not claim that all native runtime integration stages are complete.

## Monorepo source structure

The four complete upstream source trees live at `projects/reaper`, `projects/pytyliki`, `projects/oplague` and `projects/ventusample`. A normal DuckOS checkout includes all files. Use `bash scripts/vendor-ecosystem.sh --verify` to confirm exact tree identity and provenance; do not clone or initialize nested Git repositories inside those directories.
