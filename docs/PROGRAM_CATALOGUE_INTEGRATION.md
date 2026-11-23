# 1,000-program catalogue: DuckOS integration contract

**Owner:** Ivan-VHS  
**Version:** 1.0.0  
**Status:** architecture contract; no bootable OS implementation is asserted

## 1. Purpose

The 1,000 entries describe ideas and capability patterns drawn from existing software. They are not a request to bundle 1,000 upstream applications, copy their source code or turn every idea into a kernel feature.

The four specialist repositories remain the owners of their domains. DuckOS is the future integration host for selected user-space services and OS-facing adapters.

The authoritative machine-readable allocation is `manifests/ivan-vhs-program-adoption.v1.json`.

## 2. Catalogue ownership

| Repository | IDs | Count | Primary responsibility |
|---|---:|---:|---|
| Pytyliki | 1–120, 171–250 | 200 | CPU and host inventory, bounded benchmark/profile evidence, static analysis, embedded references and classical simulation |
| Reaper | 251–500 | 250 | Language/runtime, compiler infrastructure, IDE services, build/test tooling, parsers and documentation |
| OPlague | 501–700 | 200 | Device and driver inspection, package/binary parsing, signatures, hashes, SBOM and provenance |
| VentuSample | 121–170, 701–1000 | 350 | DSP/audio analysis, DAW-inspired workflows, synthesis, sampling, effects, music metadata and notation |
| DuckOS | no catalogue IDs | 0 | Operating-system integration, core services, IPC and packaging |

The ranges form a non-overlapping partition of IDs 1–1000. IDs 121–170 are assigned to VentuSample even though they appear in the Pytyliki section of the original list; this is an explicit ownership transfer to keep all audio code in one project.

## 3. Service boundaries

### Pytyliki → system inspection

Expose hardware inventory and benchmark evidence through a versioned C ABI or a versioned JSON report. The OS adapter must not change CPU frequency, voltage, affinity, firmware, fan curves or device configuration. Missing sensors remain unknown rather than being estimated.

### Reaper → user-space language and tooling

Treat Reaper as a user-space programming environment and automation tool. Apply explicit permissions, filesystem scopes, CPU/memory/time quotas and audit records. The interpreter must not run inside the kernel. Native compiler or JIT work remains separate from the boot-critical path.

### OPlague → read-only device and package evidence

Use OPlague to parse metadata, hashes, signatures and package structure. Never load a driver, install a package, flash firmware or execute an inspected payload as a side effect of inspection. A signature result or hardware-ID match is evidence, not an automatic safety verdict.

### VentuSample → offline audio

Use VentuSample as the owner of audio processing, sample generation, MIDI/WAV handling and offline rendering. Do not move DSP back into Pytyliki or add an audio-device callback to the kernel. A future real-time audio service must specify scheduling, buffer ownership, device permissions, latency targets and failure recovery independently.

## 4. Cross-project interface rules

Every integrated capability must define:

- stable capability ID and interface version;
- request/response schema and compatibility policy;
- data provenance and source-quality labels;
- execution mode: pure, read-only, offline render or privileged;
- permission set and resource quotas;
- cancellation, timeout and error behavior;
- test fixtures and an acceptance test.

Preferred integration order:

1. **JSON** for manifests, inventory, package metadata and offline job descriptions.
2. **Versioned C ABI** for narrow native library calls with explicit ownership and lifetime rules.
3. **IPC** for long-running user-space services after DuckOS has a defined process and permission model.

Do not expose raw pointers across a process boundary. Do not let one project silently load arbitrary plugins or libraries discovered by another project.

## 5. OS architecture sequence

| Stage | Deliverable | Exit condition |
|---|---|---|
| 0 | Service contracts, capability registry and package metadata | Schemas validate; ownership and permissions are explicit |
| 1 | Bootable emulator target, minimal kernel and initramfs | Repeatable boot and shutdown tests; no specialist project required to boot |
| 2 | User-space process model, IPC and service supervisor | Crash isolation, timeouts and resource ceilings are tested |
| 3 | Read-only hardware/device adapters | No hardware writes; unknown data is preserved as unknown |
| 4 | Sandboxed Reaper tools and OPlague inspection service | Permission-denial and quota tests pass |
| 5 | VentuSample offline audio/render service | Deterministic fixtures and bounded memory use pass |
| 6 | Compositor, settings UI, package manager and installer | End-to-end install/update/rollback tests and signed metadata checks pass |

These are planned stages. No stage is marked complete by the existence of this document.

## 6. Security and licensing

- Adopt ideas and documented formats, not third-party implementation code.
- Record the upstream license and required notices before adding a dependency.
- Do not treat MIT, Apache-2.0, GPL or proprietary licenses as automatically interchangeable.
- Keep untrusted parsers bounded by input size, recursion depth, archive expansion, memory and execution time.
- Treat downloaded packages, firmware and plugins as untrusted data until a separate verification policy is implemented.
- Network lookup, telemetry upload and remote generation must be opt-in and visible.
- Privileged operations require a separate design, explicit user/admin consent, audit record and rollback plan.

## 7. Capability status vocabulary

| Status | Meaning |
|---|---|
| `proposed` | Idea only; no implementation evidence |
| `specified` | Contract or schema exists |
| `in_development` | Source exists but acceptance gates are incomplete |
| `implemented` | Source, build, tests and limits are verified |
| `deferred` | Intentionally postponed |
| `rejected` | Incompatible with project scope, security or licensing |

A catalogue count, feature registry entry, README statement or roadmap item does not by itself qualify as implementation evidence.

## 8. Current baseline

The four specialist repositories already publish their own `docs/PROGRAM_CATALOG_1000.md` adoption maps and feature matrices. Their first implementation waves include bounded profiling and sensor evidence, Reaper language services and toolchain inventory, OPlague PE/SPDX inspection, and VentuSample offline FFT/resampling/MIDI inspection.

DuckOS now checks out the four specialist repositories as commit-pinned Git submodules under `projects/`, preserving their individual histories and licences. `federation/repositories.v1.json` is the source registry and `tools/federate_repositories.py` validates and synchronizes the exact pins. This makes upstream source available in the workspace; it does not automatically build or execute those projects, nor does it complete their user-space service adapters. DuckOS still does not provide a bootable kernel, bootloader, initramfs, compositor, enforced process sandbox, package manager or installer. The next engineering task remains interface verification and native OS foundation work—not bulk-copying project code into the kernel.
