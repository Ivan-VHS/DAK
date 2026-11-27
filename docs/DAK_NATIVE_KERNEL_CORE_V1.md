# DAK Native Kernel Integrity Core v1

**Status:** experimental bootstrap integration; native C11 modules are compiled into the x86-64 Stage 1 image.  
**Primary target:** x86_64.  
**Policy language:** Reaper.  
**Wire format:** DAKS v1.

This document records the implementation boundary for the native rule-epoch registry, predictive guard, canonical application-sector descriptor, and their Reaper policy contracts.

## What is now in the kernel image

The Stage 1 entry path initializes an empty rule registry and an empty bounded predictor after the existing Limine handoff and early-frame validation. The ISO build compiles these units with freestanding x86-64 flags and links them into the kernel ELF:

- `foundation/rule_epoch.c`
- `foundation/predictive_guard.c`
- `foundation/app_sector.c`

No model is trusted or active at cold boot. Installation must remain unavailable until a real verifier publishes a verified model through the native registry.

The CMake host test target is `dak_kernel_core`. Its three CTest suites cover model epochs, predictive guard decisions, and DAKS sector serialization and range validation.

## Immutable verification epochs

An installation transaction pins a model lease containing its slot and generation. Model payload bytes are copied into a private staging slot before verification. A candidate is verified away from caller-owned mutable memory, and publication occurs only after successful verification.

Publication is rejected while the active model has any live installation lease. A failed verifier leaves the previous active generation untouched. Unpinning must identify the exact slot and generation originally pinned; a stale lease cannot release a newer model.

The registry currently uses bounded C11 `atomic_flag` metadata locks. This bootstrap use occurs with interrupts disabled and before scheduler/SMP activation. Before concurrent runtime use, replace or adapt this lock boundary to a kernel-owned IRQ/preemption/SMP-aware primitive. Do not treat the current spin lock as a completed general-purpose kernel synchronization facility.

## Predictive guard

The predictor maintains bounded history keyed by a request fingerprint and the pinned model generation. Repeated complete denials can trigger a conservative early risk result.

The predictor has no allow authority. A valid authorization request always executes the complete authoritative verifier callback, even after a repeated-denial prediction. The callback must report either complete allow or complete deny; incomplete or invalid outcomes fail closed. Prediction may add a deny, but cannot skip rules or manufacture an allow.

The request fingerprint must be computed at a trusted ingress boundary over canonical request bytes. A caller-supplied or untrusted digest is not an identity proof. A production implementation must also use a real cryptographic digest and bind the fingerprint to principal, target, operation, relevant arguments and model epoch.

## DAKS v1 application sectors

DAKS v1 is a 96-byte canonical little-endian record. It is encoded field-by-field; a compiler-dependent packed structure is not the wire format. The record carries application ID, sector ID and kind, byte offset and length, alignment, permissions, a 32-byte digest and generation. Reserved bytes must be zero.

Application image sectors are not the same thing as physical disk sectors or the filesystem's block geometry. DAKS describes independently validated regions within an application image.

The permission model is strict:

| Sector kind | Permissions |
|---|---|
| Manifest, read-only data, resource, policy | R |
| Code | RX |
| Writable data, journal | RW |

W+X is rejected. Tables reject invalid ranges, overlap, duplicate sector IDs, wrong application ownership, missing verification/seal state, more than 64 entries, anything other than exactly one manifest, and absence of a code sector.

The current native codec and validator do not themselves hash content, verify a signature, map pages, create page tables or install permissions in hardware. Those are separate trusted verifier, VM and package-service responsibilities.

## Reaper policy surface

The policy modules are:

- `dak/kernel/rule_epoch.rpr`
- `dak/security/predictive_guard.rpr`
- `dak/system/application_sectors.rpr`
- `dak/system/secure_install.rpr`

`kernel_integrity_tests.rpr` checks immutable leases, blocked generation changes, exact-once completion of required plan steps, predictive non-authority, DAKS permissions and range validation, and the final native readback/commit gate.

The workflow checks and executes this Reaper contract through both the tree-walk and VM engines. A workflow definition is not the same as a passing GitHub Actions run; inspect the PR checks for the current CI result.

## Mandatory install sequence

An install must bind one immutable rule-model epoch for its whole lifetime. The transaction's required steps are an explicit finite set; missing, duplicated, extra, or failed work prevents commit. At minimum the transaction includes model pinning, manifest and sector validation, target and capability checks, staging, durable write, independent readback, and boot-record staging. The final policy result is only eligibility for the native atomic-commit adapter.

A failure before mutation aborts without writes. A failure after mutation restores a verified backup and old boot selection only when the recovery journal is consistent; otherwise the service stops writes, preserves evidence and enters recovery.

## Current limits — do not overclaim

This change does not yet provide:

- production cryptographic signature or digest verification and a protected trust store;
- a disk/filesystem write backend, durable journal or boot-slot switch;
- VM page mapping or hardware-enforced RX/RW permissions for application sectors;
- process isolation, syscall-based app launch, driver runtime or service supervisor;
- an IRQ/preemption/SMP-safe registry lock adapter;
- a direct Reaper freestanding ELF backend;
- full Stage 1 ISO build and QEMU BIOS/UEFI qualification for this branch or physical-hardware qualification.

The current entry path initializes an empty registry and predictor only. It does not mount applications or execute an installation. The host C test suite and individual freestanding object-link check are separate evidence from a full boot test.

## Local verification

Host tests:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Expected CTest names:

- `dak-rule_epoch`
- `dak-predictive_guard`
- `dak-app_sector`

The ISO build compiles the same three native source units with the existing freestanding toolchain flags and links them into the Stage 1 ELF. BIOS/UEFI boot evidence must be recorded by the dedicated QEMU workflow before this milestone can be described as boot-qualified.
