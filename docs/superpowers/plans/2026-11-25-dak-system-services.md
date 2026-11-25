# DAK Native System Services Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first Reaper-native policy layer for the DAK installer, driver runtime, package manager, update system and shared audit journal.

**Architecture:** Five focused `.rpr` policy modules (four system services plus an audit journal) reuse existing Reaper memory, architecture, capability, driver-descriptor and VFS contracts. A single Reaper contract suite exercises their public APIs under both the tree-walk engine and VM; all decisions remain plan-only until privileged DAK providers exist.

**Tech Stack:** Reaper `.rpr`, existing DAK Reaper reference runtime, GitHub Actions contract workflow, Markdown architecture documentation.

**Spec:** `docs/DAK_SYSTEM_SERVICES_V1.md`.

## Global Constraints

- All four subsystem policies and the shared audit journal are implemented in Reaper source, not Python.
- x86-64 is the primary Intel/AMD target; Elbrus remains a compatibility-preserved target.
- Fail closed on missing trust, identity, signature, capability, bounds or recovery evidence.
- Never conflate hash integrity with publisher authentication.
- No disk writes, archive extraction, package execution, driver loading, MMIO/DMA, firmware mutation or boot-slot switch in policy modules.
- Keep `main` protected; stack this work on the coordinated DAK #190 / Reaper #344 naming migration.

## Review Focus

- Signature-state spoofing or revoked publisher state — require a trusted future verifier and document that Reaper only consumes its authenticated result.
- Integer overflow and unaligned/out-of-disk partition boundaries — use the existing overflow-safe `region_fits` contract.
- Path traversal and malformed package paths — test each payload path as normalized components against the shared VFS rules.
- Resource and privilege lifetime on driver unload — reject while IRQ, DMA or device ownership remains active.
- Downgrade and interrupted update — enforce both semantic-version and monotonic-sequence ordering; confirm only after healthy boot evidence.

---

### Task 1: Installer

**Files:**
- Create: `dak/system/installer.rpr`
- Modify: `contract_tests.rpr`

**Interfaces:**
- Consumes: `dak/kernel/memory.rpr::region_fits`, `dak/platform/targets.rpr::architecture_known`.
- Produces: `target_valid`, `admission`, `partition_valid`, `layout_valid`, `transition_valid`, `commit_policy`.

- [x] Write tests for explicit consent, publisher/digest/signature evidence, recovery readiness, canonical A/B slot IDs, BIOS/UEFI layout, partition overlap, skipped states and unverified boot.
- [x] Implement policy module; all results are plan-only and never write storage.
- [ ] Verify tree-walk and VM contract results in GitHub Actions.

### Task 2: Driver Runtime

**Files:**
- Create: `dak/drivers/runtime.rpr`
- Modify: `contract_tests.rpr`

**Interfaces:**
- Consumes: `dak/drivers/abi.rpr`, `dak/drivers/orchestrator.rpr`, `dak/platform/targets.rpr`.
- Produces: `descriptor_valid`, `admission`, `resource_admission`, `transition_valid`, `unload_policy`.

- [x] Test publisher, digest and signature state; typed descriptor validation; device-bus and architecture gates; resource conflicts; lifecycle skips and active DMA.
- [x] Implement admission and safe-unload decision policy; no driver is loaded or mapped.
- [ ] Verify tree-walk and VM contract results in GitHub Actions.

### Task 3: Package Manager

**Files:**
- Create: `dak/packages/manager.rpr`
- Modify: `contract_tests.rpr`

**Interfaces:**
- Consumes: `dak/platform/targets.rpr`, `dak/security/capabilities.rpr`, `dak/storage/vfs.rpr`.
- Produces: `package_valid`, `dependencies_satisfied`, `paths_valid`, `admission`, `transition_valid`, `remove_policy`.

- [x] Test malformed manifests and field types, publisher/digest fields, dependency absence, dot traversal, embedded POSIX/Windows separators, capability denial and protected/dependent removal.
- [x] Implement bounded manifest and transaction policy; no payload is extracted or executed.
- [ ] Verify tree-walk and VM contract results in GitHub Actions.

### Task 4: Update System

**Files:**
- Create: `dak/system/updates.rpr`
- Modify: `contract_tests.rpr`

**Interfaces:**
- Consumes: `dak/platform/targets.rpr`.
- Produces: `manifest_valid`, `version_newer`, `admission`, `inactive_slot`, `activation_policy`, `transition_valid`, `boot_result_policy`.

- [x] Test signature state, architecture, version/sequence rollback, inactive-slot arming, boot-entry validation, malformed manifests and skipped states.
- [x] Implement A/B update and boot-confirmation policy; no slot is written or switched.
- [ ] Verify tree-walk and VM contract results in GitHub Actions.

### Task 5: Append-only audit journal

**Files:**
- Create: `dak/system/audit.rpr`
- Modify: `contract_tests.rpr`

**Interfaces:**
- Produces: `record_valid`, `chain_valid`, `append_policy`.

- [x] Test valid hash-linked events, malformed records, missing request identity, sequence gaps, broken digest links, bounded capacity and append-only ordering.
- [x] Implement append-intent validation; durable storage and tamper-evident signing remain provider responsibilities.
- [ ] Verify tree-walk and VM contract results in GitHub Actions.

### Task 6: Documentation and cross-repository integration

**Files:**
- Create: `docs/DAK_SYSTEM_SERVICES_V1.md`
- Create: `docs/superpowers/plans/2026-11-25-dak-system-services.md`
- Modify: `README.md`, `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_ROADMAP.md`.

- [x] Record the exact API, transaction states, return decisions and security boundaries.
- [x] State the native prerequisites for moving beyond Reaper policy contracts.
- [ ] Reconcile the DAK #190 and Reaper #344 naming migrations before merging the dependency stack.
- [ ] Require successful Reaper tree-walk and VM workflows on the final PR head.
- [ ] Promote implementation status only when native providers and target evidence exist.
