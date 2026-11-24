# DuckOS documentation

## Desktop and application interfaces

[Mora unified desktop](../mora/index.html) is the current browser shell and system-control surface. Its neutral application discovery hub, **Mora Commons**, is documented in [Mora Commons](MORA_COMMONS.md). Its application and native-service boundaries are described in [Mora shell and native integration](MORA_INTEGRATION.md). The [Mora Boost and OPlague gaming integration](GAMING_PERFORMANCE_INTEGRATION.md) describes measured telemetry, reversible Windows sessions and the future native bridge contract.

[Unify manual transfer format v1](UNIFY_TRANSFER_FORMAT_V1.md) specifies the bounded JSON file used for manual tab, clip and selected-setting transfer in the earlier browser prototype. Its schema is [unify.transfer.v1.schema.json](../schemas/unify.transfer.v1.schema.json).

## Visual design

[Mora Design System](../MORA_DESIGN_SYSTEM.md) is the canonical interface standard; [mora/theme.json](../mora/theme.json) contains the versioned color, shape, spacing, typography and motion tokens.

## Runnable prototypes

[The current Mora shell](../mora/index.html) — unified home screen, seven first-party app identities and eight system tools, including Mora Commons, with local intent, preference, recovery, file-inspection and Mora Boost/OPlague entry points.

[The earlier seven-app Mora prototype](../prototype/mora-home.html) — retained as a reference while the unified shell evolves. Neither browser prototype is a native compositor or proof that kernel and hardware services are available.

## Command-line tools

[DuckOS Extended Terminal](EXTENDED_TERMINAL.md) documents the separate allowlisted user-space command environment, command registry, local configuration, bounded history, extension contract and security boundaries.

## Native workbench

[Native Reaper integration](REAPER_INTEGRATION.md) documents the process-isolated Reaper Studio launcher, static-check bridge and Duck Desktop panel.
[Reaper migration roadmap](REAPER_MIGRATION.md) records the exact source inventory, compiler gaps, target decisions and bootable-kernel acceptance gates. The machine-readable status is [reaper-migration.v1.json](../duckos/reaper-migration.v1.json), validated by tools/validate_reaper_target.py.

## Desktop optimization

[Duck Desktop optimization](DESKTOP_OPTIMIZATION.md) documents the native user-space maintenance window, read-only audit, safe file organization, reversible per-user startup controls and the current compositor boundary.

## Product specification

[Preinstalled application suite](PREINSTALLED_APPLICATIONS.md) defines the seven default DuckOS application roles, their initial capability scope, boundaries and proposed cross-app workflows. The versioned inventory is available as [JSON](../catalogs/preinstalled-applications.v1.json) and validated against its [JSON Schema](../schemas/preinstalled-applications.v1.schema.json).

## Normative standard

[Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md) defines the shared Ivan-VHS terminology, capability maturity, runtime states, verification outcomes, evidence rules and documentation acceptance criteria. It applies to new and materially revised documentation in this repository.

## Documentation rules

Describe current behavior from the source, build configuration and tests. Mark designs and future work as specified or planned; do not present them as implemented. Keep kernel, boot, driver, runtime, graphics and desktop claims tied to concrete source paths and reproducible verification evidence.

This index is a documentation entry point. It does not itself assert that any particular subsystem is implemented or absent.

## Windows application compatibility

[Windows compatibility foundation](WINDOWS_COMPATIBILITY.md) documents PE inspection, isolated prefix profiles, CLI diagnostics and implementation status against the 66-point specification. [DuckBridge](DUCKBRIDGE.md) adds local runtime inventory and structured dry-run plans for compatible backends; neither layer starts a target process.


## Capability completeness standard

[Engineering Evolution and Capability Completeness Standard](ENGINEERING_EVOLUTION_FRAMEWORK.md) — canonical vocabulary, maturity states, measurable acceptance gates, architecture and extension rules, compatibility and release criteria.
