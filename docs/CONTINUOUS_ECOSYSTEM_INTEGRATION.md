# Continuous ecosystem integration into DAKOS

## Goal

DAKOS becomes the continuously improving integration host for all accumulated code, modules, tools and applications. Every useful implementation is inventoried, assigned an owner and destination, connected through a versioned contract, implemented in the correct runtime layer, tested and tracked until verified.

This is not a source-code dump. Reaper, Pytyliki, OPlague and VentuSample retain their own repositories, histories, languages, release cadence and licenses. DAKOS owns the adapters, native services, app manifests, capability boundaries and boot integration.

## Existing authorities

Reuse rather than duplicate:
- federation/repositories.v1.json — source URLs, exact pins, licenses and runtime boundaries.
- catalogs/preinstalled-applications.v1.json — app catalogue.
- manifests/ivan-vhs-program-adoption.v1.json — existing adoption/allocation manifest.
- .architecture/system-capabilities.v1.json — system capability boundaries.
- Existing federation, adoption, Reaper-contract and completeness workflows.
- docs/IMPLEMENTATION_ROADMAP.md — native OS implementation sequence.

## Delivery waves

1. **Reaper + DAKOS foundation:** canonical typed IR, Span/SourceMap, DABI64, boot-info, HIR/MIR/LIR, deterministic diagnostics and native system contracts. Reaper is the primary language for new DAKOS-owned native code.
2. **BAV + Kontexa + Mora:** least-privilege security/capability service, audit and recovery, offline-first document/knowledge service, typed service APIs and preserved Mora/Red Sparrow app surfaces.
3. **Pytyliki + OPlague:** versioned C ABI, normalized diagnostic records, device evidence adapters, bounded inputs and read-only-by-default behavior.
4. **VentuSample + Reaper:** preserve C++20 DSP ownership, define stable ABI/ownership/format contracts, integrate offline render jobs; real-time device access remains a separate native service.
5. **Jora + application platform:** stable app IDs, manifests, capabilities, package verification, sandboxing, install/update/remove, atomic deployment and rollback.
6. **Remaining applications and tools:** ORGze, DAKBridge, DAKDriver OmniCore, Reaper Studio, SAMBU, MOST, ToolNG, SaintSI and every remaining catalogue entry. Preserve product identities and reconcile localization, accessibility, offline behavior and dependencies.

## Discovery and inventory

Continuously reconcile all repositories, branches, apps, libraries, modules, prototypes, specifications and existing work. Record stable ID, owner, source, license, maturity, build system, dependencies, target runtime, ABI/schema, tests, evidence and next action. Unknown work stays in an explicit discovery queue. Never delete, rename or overwrite a project automatically.

The repository registry, application catalogue and adoption manifest remain the authorities for their respective domains. The integration plan only connects them.

## Continuous automation

The ecosystem-continuous-review workflow runs on relevant changes, manual dispatch and a recurring schedule. It checks out pinned source revisions, validates the plan and repository registry, verifies submodule state and reports upstream default-branch drift in the Actions summary.

It never advances pins, builds imported code, executes imported binaries, installs drivers or merges changes automatically. Existing focused workflows continue to validate federation, app adoption, Reaper contracts, completeness and CI. A drift report is a review queue, not permission to import code.

## Native DAK integration service

GitHub Actions is development-time automation, not an in-OS daemon. The eventual resident counterpart belongs in DAK's user-space service layer and must be implemented in Reaper after process isolation, IPC, capability enforcement, durable state and service supervision exist.

Required subsystems: source/app inventory; dependency and contract graph; maturity/evidence ledger; integration queue and priority planner; resource-budgeted build/test scheduler; sandboxed workers; ABI/schema compatibility gate; explicit approval broker; signed provenance; A/B deployment and rollback; audit log; cancellation and crash recovery.

It must be offline-first, deterministic where possible and read-only by default. Source-pin changes, package installation, driver loading and system mutation require explicit policy and approval.

## State machine and acceptance

discovered → classified → designed → implementation → tested → reviewed → staged → verified

Failed work becomes blocked with evidence and a next action. Documentation or catalogue entries never promote maturity.

Every integration requires an actual source change in its owning repository or DAKOS adapter, versioned contracts, tests, security/resource review, supported-target CI, provenance/license review and rollback or an explicit non-mutating scope. Keep PRs separate and reviewable; protect main and merge in dependency order.

## Success metrics

Track discovered, implemented and verified items; verified integration edges; passing contracts; blockers; upstream drift; regressions; build/test duration; and runtime resource budgets. Report evidence-backed progress, not document or roadmap-bullet counts.
