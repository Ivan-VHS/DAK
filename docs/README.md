# DAK documentation

> **Psychoporter 666 documentation profile v1.0** · Reviewed 2026-11-25 (UTC)

Start with the [project README](../README.md) for the current Stage 1 boot evidence, native DAK host application and release boundary. The [documentation map](INFORMATION_ARCHITECTURE.md) links the full catalogue.

## NEXUS system architecture

[NEXUS System Components and Internal Services v1](NEXUS_SYSTEM_SERVICES_V1.md) defines component ownership, the six internal service descriptors, cross-repository boundaries and implementation gates. Its machine-readable registry is `../catalogs/nexus-system-services.v1.json` and its schema is `../schemas/nexus-system-services.v1.schema.json`.

## Desktop and application interfaces

- [DAK Desktop](DAK_DESKTOP.md) — native host shell, Reaper session policies and interactive HTML demo.

- [DAK native integration](MORA_INTEGRATION.md) — host-native Qt 6 application, top-level windows and native-service boundary.
- [DAK Commons](MORA_COMMONS.md) — local app-discovery hub and catalogue responsibilities.
- [DAK design system](../MORA_DESIGN_SYSTEM.md) — versioned interface tokens and visual language.
- [Browser reference preview](../mora/index.html) — retained browser prototype, not a native compositor.

## Native boot and kernel

- [Bootable Stage 1 image](BOOTABLE_IMAGE.md) — pinned Limine BIOS/UEFI path, image assembly and QEMU checks.
- [Implementation status](IMPLEMENTATION_STATUS.md) — delivered, partial and pending subsystems.
- [Core subsystem MVP](CORE_MVP_V1.md) — Reaper reference contracts and native-enforcement boundary.
- [x86_64 exception handling](X86_64_EXCEPTION_HANDLING.md) — current exception/interrupt progress and remaining work.

## Ecosystem and security

- [Ecosystem integration](ECOSYSTEM_INTEGRATION.md) — peer repositories, source pins and adapters.
- [Repository federation](REPOSITORY_FEDERATION.md) — repository-level integration record.
- [Ecosystem branch consolidation](ECOSYSTEM_BRANCH_CONSOLIDATION_V1.md) — five-repository inventory, PR dependency order, main rulesets and controlled merge procedure.
- [BAV security bundle](BAV_SECURITY_BUNDLE_V1.md) — declarative format and planned security services; schema validation is not scanning or signature verification.
- [Windows compatibility](WINDOWS_COMPATIBILITY.md) and [DAKBridge](DUCKBRIDGE.md) — offline inspection and dry-run plans, not target-process execution.

## Education and learning

- [Early mathematics through play](EARLY_MATH_FOR_PRESCHOOLERS.md) — parent/educator guide and the versioned local activity pack.

## Planning and evidence

- [Project evolution ladder](PROJECT_EVOLUTION_LADDER.md) — cumulative evidence gates.
- [Implementation roadmap](IMPLEMENTATION_ROADMAP.md) — staged native implementation.
- [Unified documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md) — terminology, maturity states and evidence rules.
- [Engineering evolution framework](ENGINEERING_EVOLUTION_FRAMEWORK.md) — completeness and acceptance criteria.

Describe behavior from source, build configuration, schemas, tests and CI. Mark future work as planned; never present a host prototype or a policy contract as native kernel enforcement.
