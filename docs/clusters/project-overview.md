# DuckOS project overview

[Project README](../../README.md) · [Documentation home](../README.md) · [Information architecture](../INFORMATION_ARCHITECTURE.md)

## Product role

DuckOS is the operating-system project. Mora is its unified desktop and system-control shell. The product catalogue defines twenty first-party application concepts: the original seven identities (Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify) plus thirteen additions. Several newer panels remain partial browser-local tools rather than native system services. Mora also provides a set of local system-tool panels, whose current scope and boundaries are described in the [Mora integration guide](../MORA_INTEGRATION.md).

The browser shell is a usable interface and local contract prototype. It is not evidence that DuckOS already boots as a complete native operating system.

## Current implementation boundary

- Mora provides the desktop layout, application panels, window interactions, local preference storage, an approval-gated allowlisted intent planner, PE/ELF header inspection and local SHA-256 calculation.
- Sentinel stores shell preference choices; native per-process capability enforcement and sandboxing still require a privileged service.
- Restore snapshots Mora preferences; it does not roll back an OS image or user data.
- Bridge inspects executable headers; it does not run Windows programs.
- Proof calculates a digest; it does not authenticate an author's identity or verify C2PA provenance.
- Local AI/NPU inference, kernel resource scheduling, native compositor, immutable updates, full Windows compatibility and XR services require native implementations and their own test evidence.

The [Mora system policy](../../mora/system-policy.json) is the machine-readable source for capability maturity. The [Mora integration guide](../MORA_INTEGRATION.md) records the service and security boundaries.

## Primary documentation

| Subject | Canonical reference |
|---|---|
| Product applications | [Preinstalled application suite](../PREINSTALLED_APPLICATIONS.md) |
| Desktop design | [Mora Design System](../../MORA_DESIGN_SYSTEM.md) |
| Desktop integration | [Mora shell integration](../MORA_INTEGRATION.md) |
| Language and runtime semantics | [Unified documentation standard](../UNIFIED_DOCUMENTATION_STANDARD.md) |
| Editorial quality | [Language quality](../LANGUAGE_QUALITY.md) |
| Navigation and maintenance | [Documentation control](../DOCUMENTATION_CONTROL.md) |

## Engineering principle

A capability is complete only at the layer where it is implemented and verified. Keep product intent, browser prototype, host integration, native userspace and privileged kernel behavior explicitly separated in source, documentation and release notes.
