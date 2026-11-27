# DuckOS native core integrity contracts v1

**Status:** Reaper policy contracts added; privileged native enforcement and a qualified freestanding Reaper backend remain pending.  
**Language:** Reaper  
**Primary target:** x86_64  
**Contract suite:** `system_platform_tests.rpr`

## Purpose

This layer establishes one consistent admission model for the DuckOS primary kernel, verification rules, installation preflight, mandatory operation completion and application storage layout. It extends the existing boot and subsystem contracts without claiming that reference-runtime policy code can perform privileged operations.

The contracts are deny-by-default. A rejected or uncertain condition stops installation or activation; a failed required operation selects recovery rather than silently treating the transaction as complete.

## Primary-kernel admission

`duckos/kernel/core.rpr` defines the primary-kernel profile:

`[architecture, syscall_abi, execution_mode, privilege, reaper_codegen, hosted_fallback]`

The accepted profile currently requires:

- `x86_64` and `DABI64-v1`;
- `freestanding` execution in `ring0`;
- a separately qualified Reaper native code-generation backend;
- hosted fallback disabled.

This is an admission rule, not a claim that all those capabilities are already present. The machine-readable platform manifest still records `hardware_execution: false` and `native_freestanding_codegen: not-yet-qualified`. Therefore the current repository state must reject primary-kernel activation through this gate until native code generation and the privileged ABI are actually qualified.

The gate also checks the established startup order:

`reset → firmware → memory → interrupts → scheduler → ipc → drivers → services → desktop`

A shortened or reordered phase list is not considered complete startup.

## Immutable verification model

`duckos/kernel/verification.rpr` represents a verification model as:

`[model_id, version, revision, digest, state, epoch]`

The state lifecycle is:

`draft → frozen → installing → installed`

A model is frozen before installation. The install operation accepts only the frozen model and its expected epoch. While frozen or installing, mutation is denied. Commit succeeds only when the candidate snapshot exactly matches the model's identifier, version, revision, digest and epoch.

Installed snapshots are not edited in place. A change starts a separate draft with a higher revision and epoch. An interrupted installation returns to draft only after the caller supplies a matching snapshot, a later epoch and evidence that native rollback has been verified.

The digest field is an opaque identity supplied by a trusted verifier. These Reaper contracts do not calculate cryptographic hashes, verify signatures or prove provenance.

**Native enforcement requirement:** a Reaper value-state contract is not a mutex or a privileged storage lock. The future kernel backend must atomically serialize model transitions, retain the frozen snapshot in protected memory/storage, reject stale epochs at every mutation boundary and make the lock survive all installation workers. No installer or application receives permission to rewrite the authoritative verification model.

## Predictive condition checks

`duckos/kernel/predictor.rpr` stores a bounded condition prediction:

`[condition_id, ruleset_revision, install_epoch, expires_at_tick, expected_value]`

A prediction is usable only for the same frozen/installing rules revision and epoch, and only before its expiry tick. A changed observation invalidates the prediction.

A predictor can reduce repeated preflight work, but it cannot authorize a commit. `commit_guard` requires a fresh authoritative check and an unchanged observed value. Missing, stale or contradictory evidence fails closed.

The native implementation must read live authoritative state again at the protected operation boundary. It must not trust a cached prediction as a security verdict, signature result, capability grant or permission to write storage.

## Mandatory execution barrier

`duckos/kernel/execution.rpr` treats the required operation list as an exact set. It rejects empty or duplicate step names, omitted steps, unexpected duplicates and failed operations.

The installation barrier accepts the transaction only when:

1. the verification model is in `installing`;
2. the frozen candidate snapshot is unchanged;
3. the failed-operation list is empty;
4. every required operation appears exactly once in the completed set.

An incomplete set is denied; a failed step selects recovery. This makes "all required work" an explicit, testable condition instead of a best-effort checklist.

The required operation list itself must come from a trusted, immutable install plan. The native transaction manager must execute each operation, persist its result and reconcile the final completion set. The Reaper contract validates evidence; it does not execute disk writes, firmware changes, process creation or driver installation.

## Unified code, byte, memory and sector model

`duckos/storage/sectorization.rpr` uses one application identity and one ruleset revision/digest across the executable code record, memory region, disk extent and application manifest.

### Code record

`[application_id, code_id, encoding, byte_length, ruleset_revision, ruleset_digest, bytes]`

The canonical byte representation is `u8le-v1`: every code byte is an integer in the inclusive range 0–255, and the declared length must equal the byte-array length.

### Memory region

`[application_id, physical_base, byte_length, permissions, ruleset_revision, ruleset_digest]`

The current contract requires page-aligned base and length (4096 bytes), rejects address overflow and rejects writable-plus-executable mappings. The allowed permission labels are read-only, read/write or read/execute.

### Disk extent

`[application_id, start_sector, sector_count, logical_sector_bytes, payload_bytes, ruleset_revision, ruleset_digest]`

Only 512-byte and 4096-byte logical sectors are accepted. The extent must fit within the supplied disk-sector limit, multiplication must not overflow and payload bytes must fit inside the extent. A sector map rejects overlaps between distinct applications and duplicate extents for one application.

### Application manifest

`[application_id, app_version, ruleset_revision, ruleset_digest, abi, entry_code_id]`

The consistency check binds the manifest, byte record, memory region and disk extent to the same application and exact ruleset revision/digest. The entry code identifier and payload length must also agree.

These are validation and layout contracts. They do not yet allocate physical pages, map page tables, hash executable bytes, write a partition table, implement a filesystem, mount a volume or install an application. Disk geometry, sector limits, block-device identity and trusted manifest provenance must come from the native storage layer.

## Verification

The new assertions are part of `system_platform_tests.rpr`. The existing Reaper system-platform workflow checks every `.rpr` file under `duckos/` and runs the contract suite with both the reference tree-walk engine and the Reaper VM.

This verifies the policy model when those CI jobs pass. It does not prove privileged enforcement, native code generation, hardware execution, atomicity under SMP, durable installation or a bootable user session.

## Native work still required

- Qualify Reaper freestanding x86_64 code generation and the DABI64-v1 kernel calling convention.
- Implement atomic verification-model locking, protected snapshot storage and monotonic epochs in the native kernel.
- Connect live predictor revalidation to trusted memory, device and package state.
- Execute the complete install plan through a transaction manager with durable step records and verified rollback.
- Implement physical page allocation, page tables, W^X enforcement and memory teardown.
- Implement a block-device/VFS path that maps application extents to real storage and validates all geometry before writes.
- Run QEMU and hardware tests for interrupted installs, stale predictors, concurrent mutation attempts, sector overlap and rollback.

Until these gates pass, this layer is a versioned and testable Reaper policy foundation for the primary native kernel, not a completed or production-qualified DuckOS kernel.
