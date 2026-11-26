# DAK documentation

**Documentation baseline:** 2026-11-26 · **Project state:** experimental Stage 1 foundation.

Start with the [project README](../README.md) for the verified boot boundary, Reaper policy layer, host-native desktop and current limitations. This index is a navigation aid; it does not replace source, tests, schemas or implementation records.

## Primary technical references

- [Architecture](ARCHITECTURE.md) — system decomposition and integration boundaries.
- [Implementation status](IMPLEMENTATION_STATUS.md) — delivered, partial, specified and pending capabilities.
- [Bootable Stage 1 image](BOOTABLE_IMAGE.md) — build, QEMU BIOS/UEFI evidence and the halt boundary.
- [Boot Info v1](BOOT_INFO_V1.md) — firmware handoff and validated memory-map contract.
- [Core subsystem MVP](CORE_MVP_V1.md) — Reaper reference contracts versus native enforcement.
- [DAK Desktop](DAK_DESKTOP.md) — host-native Qt application, separate from the kernel session.
- [Build contracts](BUILD_CONTRACTS.md) — reproducible build surfaces and dependencies.
- [Ecosystem integration](ECOSYSTEM_INTEGRATION.md) — independent peer repositories and versioned interchange.
- [Release edition](RELEASE_EDITION.md) — source/tool payload boundaries, not a complete installable OS.
- [Documentation control](DOCUMENTATION_CONTROL.md) — publication gates and maintenance rules.
- [Unified documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md) — canonical standards for all Ivan-VHS repositories.
- [Information architecture](INFORMATION_ARCHITECTURE.md) — complete documentation catalog.

## Browse the library

- [Project overview and cluster map](clusters/project-overview.md)
- [All documentation pages](INFORMATION_ARCHITECTURE.md)
- [Repository contribution guide](../CONTRIBUTING.md)
- [Documentation rebaseline plan](superpowers/plans/2026-11-26-documentation-rebaseline.md)

## Evidence and status

Use the maturity vocabulary defined by the unified standard. A QEMU boot check demonstrates only the exact stage and environment it exercised. Host tests of Reaper policies do not demonstrate kernel enforcement. Browser previews and host-native windows do not demonstrate a kernel compositor or user session.

## Maintainer checklist

Update the root README, affected technical contract, topic map and this index in the same pull request. Verify relative links, command syntax, supported platform claims, translation parity and any changed release or interface metadata before publication.
