# Duck documentation

**Documentation review:** 2026-11-27 UTC · **Project state:** experimental x86_64 Stage 1 foundation.

Start with the [project README](../README.md) in your preferred language for the verified boot boundary, Reaper policy layer, separate host-native desktop and current limitations. The repository slug remains `DAK`; the operating-system product name is **Duck**. This index is navigation and does not replace source, tests, schemas or implementation records.

## Primary technical references

- [Architecture](ARCHITECTURE.md) — system decomposition and integration boundaries.
- [Implementation status](IMPLEMENTATION_STATUS.md) — delivered, partial, specified and pending capabilities.
- [Bootable Stage 1 image](BOOTABLE_IMAGE.md) — build, QEMU BIOS/UEFI evidence and the halt boundary.
- [Boot Info v1](BOOT_INFO_V1.md) — firmware handoff and validated memory-map contract.
- [Core subsystem MVP](CORE_MVP_V1.md) — Reaper reference contracts versus native kernel enforcement.
- [Host-native desktop](DAK_DESKTOP.md) — Qt application, separate from the kernel session.
- [Build contracts](BUILD_CONTRACTS.md) — reproducible build surfaces and dependencies.
- [Ecosystem integration](ECOSYSTEM_INTEGRATION.md) — independent peer repositories and versioned interchange.
- [Release edition](RELEASE_EDITION.md) — source/tool payload boundaries, not a complete installable OS.
- [Documentation control](DOCUMENTATION_CONTROL.md) — publication gates and maintenance rules.
- [Unified documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md) — canonical standards for Ivan-VHS repositories.
- [Information architecture](INFORMATION_ARCHITECTURE.md) — complete documentation catalogue.

## Browse the library

- [Project overview and cluster map](clusters/project-overview.md)
- [All documentation pages](INFORMATION_ARCHITECTURE.md)
- [Repository contribution guide](../CONTRIBUTING.md)
- [Documentation rebaseline plan](superpowers/plans/2026-11-26-documentation-rebaseline.md)

## Evidence and status

A QEMU boot check demonstrates only the exact stage and environment it exercised. Host tests of Reaper policies do not demonstrate kernel enforcement. Browser previews and host-native windows do not demonstrate a kernel compositor or user session. A release ISO containing sources and tools is not a complete installable operating system.

## Maintainer checklist

Update the root README, affected technical contract, topic map and this index in the same pull request. Verify relative links, command syntax, supported platform claims, translation parity and changed release/interface metadata before publication.
