# DuckOS documentation

## Mora desktop and application content

[Mora unified desktop](../mora/index.html) is the canonical browser shell and system-control surface. It presents seven browser workspaces, six Mora system tools and four native project launch integrations in one catalogue.

- [Mora desktop and web/native integration](MORA_DESKTOP.md) explains routes, embedded web modules, local native launch readiness, themes and process boundaries.
- [Mora shell and native system integration](MORA_INTEGRATION.md) records the intent, permission, recovery and system-service maturity limits.
- [Mora Design System](../MORA_DESIGN_SYSTEM.md) is the canonical visual standard; [mora/theme.json](../mora/theme.json) contains versioned color, shape, spacing, typography and motion tokens.
- [Mora application registry](../mora/apps.json) records first-party app panels and external native project tools.
- [Mora system policy](../mora/system-policy.json) describes implemented shell behavior and future native service boundaries.

## Project catalogue and ownership

[1,000-program catalogue integration](PROGRAM_CATALOGUE_INTEGRATION.md) assigns ownership and integration boundaries across Pytyliki, Reaper, OPlague, VentuSample and DuckOS. Its machine-readable source is [ivan-vhs-program-adoption.v1.json](../manifests/ivan-vhs-program-adoption.v1.json), validated against [its schema](../schemas/ivan-vhs-program-adoption.v1.schema.json).

The ownership catalogue is an architecture/adoption contract. It does not assert that 1,000 upstream packages are copied, installed or implemented.

## Product application specification

[Preinstalled application suite](PREINSTALLED_APPLICATIONS.md) defines the seven first-party web app identities, their prototype scope, boundaries and proposed cross-app workflows. The versioned inventory is [preinstalled-applications.v1.json](../catalogs/preinstalled-applications.v1.json), validated against [its JSON Schema](../schemas/preinstalled-applications.v1.schema.json).

[Unify manual transfer format v1](UNIFY_TRANSFER_FORMAT_V1.md) specifies the bounded JSON file used for manual tab, clip and selected-setting transfer in the browser module. Its schema is [unify.transfer.v1.schema.json](../schemas/unify.transfer.v1.schema.json).

## DuckOS system contracts

The [system-manifest schema](../schemas/system-manifest.v1.schema.json), [driver-module schema](../schemas/driver-module.v1.schema.json) and [image-layout schema](../schemas/image-layout-plan.v1.schema.json) define build, module and image metadata. The browser shell does not claim to implement the kernel, driver manager, boot chain or OS image updater.

## Normative standards and validation

[Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md) defines shared maturity, evidence and writing rules. The [language quality standard](LANGUAGE_QUALITY.md) and prose diagnostics describe the repository's documentation review conventions.

Describe current behavior from source, build configuration and tests. Mark specifications and planned capabilities clearly; do not present browser controls, metadata or architecture proposals as completed native OS services.
