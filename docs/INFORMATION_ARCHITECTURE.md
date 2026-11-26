# DAK documentation information architecture

[Project README](../README.md) · [Documentation index](README.md) · [Project overview](clusters/project-overview.md)

This page is the canonical map of the documentation library present on the reviewed branch. The catalog is generated from the repository tree so that a new or existing Markdown page has a direct navigation path. Technical truth remains with source, tests, schemas, build manifests and the implementation ledger.

## Entry points and authority

- **Project entry:** [README](../README.md) — product purpose, build steps, maturity boundaries and license status.
- **Documentation home:** [docs/README.md](README.md) — key references and maintenance checklist.
- **Project overview:** [Project overview](clusters/project-overview.md) — concise subsystem map.
- **Documentation policy:** [Documentation control](DOCUMENTATION_CONTROL.md) and [Unified documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md).
- **Evidence authority:** source defines behavior; tests/CI define tested behavior; schemas and ABI files define data contracts; build/release workflows define supported operations. Documentation explains those sources and must not overstate them.

## Topic hub

- [Project overview](clusters/project-overview.md) — boot state, policy layer, host desktop and integration boundaries.

## Cross-repository boundaries

- [Reaper documentation map](https://github.com/Ivan-VHS/Reaper/blob/main/docs/INFORMATION_ARCHITECTURE.md)
- [Pytyliki documentation map](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/INFORMATION_ARCHITECTURE.md)
- [OPlague documentation map](https://github.com/Ivan-VHS/OPlague/blob/main/docs/INFORMATION_ARCHITECTURE.md)
- [VentuSample documentation map](https://github.com/Ivan-VHS/VentuSample/blob/main/docs/INFORMATION_ARCHITECTURE.md)

## Complete documentation catalog

Every Markdown page currently under `docs/` is listed below. Nested directories retain their path so the links resolve without guessing. This catalog is navigation, not proof of implementation.

### A

- [ARCHITECTURE](ARCHITECTURE.md)

### B

- [BACKEND ENGINEERING STANDARD](BACKEND_ENGINEERING_STANDARD.md)
- [BAV SECURITY BUNDLE V1](BAV_SECURITY_BUNDLE_V1.md)
- [BOOTABLE IMAGE](BOOTABLE_IMAGE.md)
- [BOOT INFO V1](BOOT_INFO_V1.md)
- [BUILD CONTRACTS](BUILD_CONTRACTS.md)

### C

- [CORE MVP V1](CORE_MVP_V1.md)

### D

- [DAK DESKTOP](DAK_DESKTOP.md)
- [DEFENSIVE SECURITY DOCTRINE](DEFENSIVE_SECURITY_DOCTRINE.md)
- [DEPLOYMENT](DEPLOYMENT.md)
- [DESKTOP OPTIMIZATION](DESKTOP_OPTIMIZATION.md)
- [DOCUMENTATION CONTROL](DOCUMENTATION_CONTROL.md)
- [DUCKBRIDGE](DUCKBRIDGE.md)

### E

- [ECOSYSTEM EVOLUTION 2026](ECOSYSTEM_EVOLUTION_2026.md)
- [ECOSYSTEM INTEGRATION](ECOSYSTEM_INTEGRATION.md)
- [ENGINEERING EVOLUTION FRAMEWORK](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [ERGONOMICS AND INTERACTION STANDARD](ERGONOMICS_AND_INTERACTION_STANDARD.md)
- [EXTENDED TERMINAL](EXTENDED_TERMINAL.md)

### F

- [FOUNDATION ARCHITECTURE](FOUNDATION_ARCHITECTURE.md)

### G

- [GAMING PERFORMANCE INTEGRATION](GAMING_PERFORMANCE_INTEGRATION.md)

### I

- [IMPLEMENTATION ROADMAP](IMPLEMENTATION_ROADMAP.md)
- [IMPLEMENTATION STATUS](IMPLEMENTATION_STATUS.md)
- [IVAN VHS ENGINEERING PROFILE](IVAN_VHS_ENGINEERING_PROFILE.md)

### L

- [LANGUAGE QUALITY](LANGUAGE_QUALITY.md)

### M

- [MORA COMMONS](MORA_COMMONS.md)
- [MORA INTEGRATION](MORA_INTEGRATION.md)
- [MOTION CONSTITUTION V2026](MOTION_CONSTITUTION_V2026.md)

### P

- [PREINSTALLED APPLICATIONS](PREINSTALLED_APPLICATIONS.md)
- [PROGRAM CATALOGUE INTEGRATION](PROGRAM_CATALOGUE_INTEGRATION.md)
- [PROGRAM CATALOG 1000](PROGRAM_CATALOG_1000.md)
- [PROJECT EVOLUTION LADDER](PROJECT_EVOLUTION_LADDER.md)

### R

- [REAPER INTEGRATION](REAPER_INTEGRATION.md)
- [RELEASE EDITION](RELEASE_EDITION.md)
- [REPORT ENVELOPE](REPORT_ENVELOPE.md)
- [REPOSITORY EVOLUTION DIRECTIVES](REPOSITORY_EVOLUTION_DIRECTIVES.md)
- [REPOSITORY FEDERATION](REPOSITORY_FEDERATION.md)

### S

- [SHARED STANDARDS](SHARED_STANDARDS.md)
- [SOURCE TRACEABILITY](SOURCE_TRACEABILITY.md)
- [SYSTEM CAPABILITY PROFILE](SYSTEM_CAPABILITY_PROFILE.md)

### T

- [THIRTEEN WAVES IMPLEMENTATION](THIRTEEN_WAVES_IMPLEMENTATION.md)

### U

- [UI UX CODEX 40026](UI_UX_CODEX_40026.md)
- [UNIFIED DOCUMENTATION STANDARD](UNIFIED_DOCUMENTATION_STANDARD.md)
- [UNIFY TRANSFER FORMAT V1](UNIFY_TRANSFER_FORMAT_V1.md)

### W

- [WINDOWS COMPATIBILITY](WINDOWS_COMPATIBILITY.md)

### X

- [X86 64 EXCEPTION HANDLING](X86_64_EXCEPTION_HANDLING.md)

### Planning and governance

- [Documentation rebaseline plan](superpowers/plans/2026-11-26-documentation-rebaseline.md)
- [Contributor guide](../CONTRIBUTING.md)

## Maintenance and release gate

1. Keep every Markdown page listed in this catalog and linked from a meaningful topic hub or its adjacent contract.
2. Preserve the four README locales and keep their section order, capability maturity, commands, license status and limitations aligned.
3. Record version, tag, platform, environment and revision for release or benchmark claims; omit values that are not declared or measured.
4. Update related schemas, examples, migration guidance, tests and CI references when public contracts or build steps change.
5. Verify every relative path and command in a clean checkout before merging. Do not present a roadmap, catalogue, screenshot or policy test as proof of kernel implementation.
