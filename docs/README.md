# DuckOS documentation

## Application interfaces

[Unify manual transfer format v1](UNIFY_TRANSFER_FORMAT_V1.md) specifies the bounded JSON file used for manual tab, clip and selected-setting transfer in the browser prototype. Its schema is [unify.transfer.v1.schema.json](../schemas/unify.transfer.v1.schema.json).

## Runnable prototype

[prototype/mora-home.html](../prototype/mora-home.html) is the seven-app Mora home screen and browser prototype. Its prototype limits and native integration gaps are recorded in [PREINSTALLED_APPLICATIONS.md](PREINSTALLED_APPLICATIONS.md).

## Unified desktop workspace

[Mora desktop integration](MORA_DESKTOP.md) documents the common local desktop, seven-app home screen, linked native project catalogue, theme contract and allowlisted launcher. Start Mora from the DuckOS repository with python mora_host.py.

## Product specification

[Preinstalled application suite](PREINSTALLED_APPLICATIONS.md) defines the seven default DuckOS application roles, their initial capability scope, boundaries and proposed cross-app workflows. The versioned inventory is available as [JSON](../catalogs/preinstalled-applications.v1.json) and validated against its [JSON Schema](../schemas/preinstalled-applications.v1.schema.json).

## Normative standard

[Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md) defines the shared Ivan-VHS terminology, capability maturity, runtime states, verification outcomes, evidence rules and documentation acceptance criteria. It applies to new and materially revised documentation in this repository.

## Documentation rules

Describe current behavior from the source, build configuration and tests. Mark designs and future work as specified or planned; do not present them as implemented. Keep kernel, boot, driver, runtime, graphics and desktop claims tied to concrete source paths and reproducible verification evidence.

This index is a documentation entry point. It does not itself assert that any particular subsystem is implemented or absent.
