# DAK Native System Services v1

**Status:** Reaper reference-runtime contracts implemented; native privileged providers pending.  
**Language:** Reaper (`.rpr`) for all four system services and their shared audit policy.  
**Primary platform:** Intel/AMD x86-64. Elbrus remains a preserved compatibility track.  
**Scope:** Installer, driver runtime, package manager, update system and shared audit journal.

## 1. Architecture

The service modules are independent Reaper policy services. Each validates bounded input, returns a deterministic decision and exposes an explicit transaction or lifecycle state machine.

| Subsystem | Reaper module | Owns |
|---|---|---|
| Installer | `dak/system/installer.rpr` | Target admission, A/B + recovery layout validation, explicit consent and installation transaction policy |
| Driver runtime | `dak/drivers/runtime.rpr` | Driver metadata admission, publisher/signature state, device/ABI/architecture matching, least-authority lifecycle and safe-unload gates |
| Package manager | `dak/packages/manager.rpr` | Package manifest, version/ABI/architecture, dependency and payload-path validation, capability admission, removal policy |
| Update system | `dak/system/updates.rpr` | Signed-manifest state, version and sequence anti-rollback, inactive-slot choice, boot confirmation and rollback policy |
| Audit journal | `dak/system/audit.rpr` | Bounded, strictly sequenced append-only event-record and journal policy |

The modules reuse existing Reaper contracts for memory-range validation, architecture policy, capabilities, device descriptors and virtual-filesystem path components. They do not duplicate the kernel or storage implementation.

## 2. Common trust and effect boundary

- An external manifest or payload starts untrusted.
- The string state `verified` is an input from a future trusted signature-verification provider; the Reaper policy module does not verify cryptography itself.
- Installer source, driver and package descriptors carry publisher identity and a content digest in addition to signature state. A trusted provider must authenticate the attestation that sets `verified`.
- A digest proves byte identity only. Publisher authenticity requires a signature verified against an explicitly trusted key.
- `revoked` is a hard rejection state. Missing, malformed or unknown trust states fail closed.
- The current modules return `*-plan-only` decisions. They never write disks, extract archives, execute packages, map driver payloads, enable IRQs, touch MMIO/DMA, edit firmware or switch boot slots.
- No operation has ambient authority. A future provider must authenticate the caller and enforce narrow capabilities again at the privileged boundary; a Reaper policy result alone is not authorization.
- Destructive installation needs explicit consent, a verified source and a ready recovery path. Commit additionally requires a verified boot result.

## 3. Installer contract

### Input records

Target: `[disk_id, architecture, disk_bytes, logical_sector_bytes, firmware_mode, consent]`.

Source evidence: `[publisher, digest, signature_state]`.

Partition: `[partition_id, kind, start_byte, length_bytes]`, where kind is `efi`, `bios_boot`, `system`, `recovery` or `userdata`.

A valid layout is sorted by start byte, starts after the first 1 MiB of disk metadata, contains two system partitions (A/B), exactly one recovery partition and at most one user-data partition. UEFI requires exactly one EFI partition and no BIOS boot partition; BIOS requires exactly one BIOS boot partition and no EFI partition. Every partition is 4 KiB aligned, in bounds and non-overlapping.

### API

- `target_valid(target) -> bool`
- `source_record_valid(source) -> bool`
- `admission(target, source, recovery_state) -> decision`
- `partition_valid(partition, disk_bytes) -> bool`
- `layout_valid(partitions, disk_bytes, firmware_mode) -> bool`
- `transition_valid(current, next) -> bool`
- `commit_policy(state, consent, source, recovery_state, boot_state) -> decision`

Transaction path: `planned → validated → staged → ready_to_commit → committed`. Failure and rollback are explicit; skipping a phase is rejected.

## 4. Driver runtime contract

Driver descriptor: `[id, abi, bus, architecture, capabilities, publisher, digest, signature_state, payload_bytes]`. Device descriptors reuse the existing six-field DuckDriver resource record. Resource admission rejects conflicts with already registered device ranges or exclusive IRQ ownership.

Admission requires a verified, non-revoked signature state, a non-empty publisher, matching architecture and bus, a supported ABI and a capability set contained by the grants. Payload size is bounded to 256 MiB.

Lifecycle path: `candidate → verified → admitted → mapped → initialized → running`. The current module models these states only. It does not map memory or start a module.

Unload requires a running/stopping driver and affirmative evidence that IRQs are quiesced, DMA is stopped and the device is quiesced.

### API

- `descriptor_valid(driver) -> bool`
- `admission(driver, device, target_arch, expected_abi, supported_buses, grants) -> decision`
- `resource_admission(device, registered_devices) -> decision`
- `transition_valid(current, next) -> bool`
- `unload_policy(state, irqs_quiesced, dma_stopped, device_quiesced) -> decision`

## 5. Package manager contract

Package record: `[id, major, minor, patch, architecture, abi, kind, dependencies, requested_capabilities, digest, publisher, signature_state, payload_bytes]`.

Supported kinds are application, system, driver and library. Payloads are bounded to 2 GiB. Every payload path is passed as normalized path components, and traversal components are rejected by the shared VFS contract. All dependencies must be present before staging; requested capabilities must be a subset of the package manager's explicit grants.

Transaction path: `planned → verified → resolved → staged → committed`, with rollback from verified/resolved/staged states. Protected system packages and packages with dependents cannot be removed by the plan.

### API

- `package_valid(package) -> bool`
- `dependencies_satisfied(required, installed_ids) -> bool`
- `paths_valid(paths) -> bool`
- `admission(package, target_arch, expected_abi, installed_ids, grants) -> decision`
- `transition_valid(current, next) -> bool`
- `remove_policy(state, dependent_count, protected) -> decision`

## 6. Audit journal contract

Audit record: `[sequence, request_id, actor, action, resource, outcome, reason, previous_digest, digest]`. Records are strictly sequenced from 1, link each event to the prior digest (the first record links to `genesis`), and are bounded by the caller's configured maximum. Append intent is rejected for gaps, malformed entries, invalid prior history, broken digest links or capacity exhaustion.

### API

- `record_valid(record) -> bool`
- `chain_valid(records) -> bool`
- `append_policy(records, record, max_records) -> decision`

This Reaper module validates append intent only. Durable append-only storage, tamper-evident hashing/signing, access control and retention policy belong to the trusted storage/security provider.
## 7. Update system contract

Update manifest: `[channel, major, minor, patch, architecture, sequence, payload_bytes, digest, publisher, signature_state]`.

Admission requires a verified non-revoked signature state, valid digest and publisher fields, matching architecture, a sequence strictly above the installed sequence, and a semantic version strictly newer than the installed version. The target slot is always the inactive member of A/B.

Transaction path: `idle → verified → staged → armed → boot_pending → confirmed`. Failed boot confirmation may enter `rolling_back → rolled_back`. Healthy boot evidence is required before confirmation; pending health never commits.

### API

- `manifest_valid(manifest) -> bool`
- `version_newer(candidate, current) -> bool`
- `admission(manifest, target_arch, current_version, current_sequence) -> decision`
- `inactive_slot(active_slot) -> slot`
- `transition_valid(current, next) -> bool`
- `boot_result_policy(health, attempts, max_attempts) -> decision`

## 8. Verification matrix

The DAK Reaper contract workflow must validate every `.rpr` file under `dak/`, then execute `contract_tests.rpr` under both the tree-walk engine and VM.

Audit coverage includes malformed request identities, non-consecutive sequences, corrupted prior journals and append-capacity exhaustion. Required negative coverage includes: missing consent, unverified/revoked provenance, missing recovery, malformed and overlapping partitions, driver bus/architecture/ABI/capability mismatch, active DMA/IRQ during unload, missing dependencies, path traversal, protected package removal, version and sequence rollback, invalid A/B slot, skipped state transitions and unhealthy boot confirmation.

## 9. Native implementation gates

These Reaper contracts are not a disk installer, package extractor, driver loader or updater. A privileged implementation must not be marked delivered until the following independent gates exist and pass:

1. Cryptographic verifier with trusted-key provisioning, revocation and authenticated provenance results.
2. Kernel-enforced DABI64 syscall provider and per-operation capability checks.
3. Reusable memory manager, address spaces, process isolation, interrupt and DMA/IOMMU ownership.
4. Native storage/filesystem implementation with crash-safe writes, fsync/barrier semantics and atomic transaction metadata.
5. Installer image verification, safe disk discovery, explicit device identity confirmation, write ordering, interruption recovery and tested rollback.
6. Driver discovery and compatibility database, signed module format, isolated mapping, IRQ/DMA lifetime and safe unload.
7. Package archive parser with bounded extraction, canonical path checks, dependency solver, atomic database and uninstall ownership.
8. A/B update boot integration with boot-success confirmation, anti-rollback persistence, recovery image and power-loss testing.
9. QEMU BIOS/UEFI tests, hardware qualification on supported Intel/AMD x86-64 systems, and separate Elbrus build/boot evidence.
10. Bounded audit-journal storage with tamper-evident event authentication, retention and recovery tests.
11. Full tree-walk/VM/native conformance, resource-limit, malformed-input, corruption, power-loss and rollback tests.

Until then, the four system-service modules and shared audit policy remain policy-only and return plan-only decisions. This boundary is intentional and security-critical.
