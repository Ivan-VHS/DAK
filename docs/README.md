# DuckOS documentation

## Mora desktop

[Mora desktop integration](MORA_DESKTOP.md) describes the canonical PWA shell, its seven browser workspaces, six system tools and four external native project launches. The shell runs from /mora/ when started with python mora_host.py.

## Design system

[Mora Design System](../MORA_DESIGN_SYSTEM.md) and the [versioned theme tokens](../mora/theme.json) define the shared palette, surfaces, typography, motion and accessibility roles used by the desktop and native adapters.

## Application and system contracts

[Application registry](../mora/apps.json) contains the 13 first-party web/system panels and four external native project tools. [System policy](../mora/system-policy.json) records maturity boundaries and safety principles.

The [seven-app product specification](PREINSTALLED_APPLICATIONS.md) defines the first-party web identities, prototype scope and consent boundaries. Its machine-readable catalog is available at [preinstalled-applications.v1.json](../catalogs/preinstalled-applications.v1.json).

[Unify manual transfer format v1](UNIFY_TRANSFER_FORMAT_V1.md) describes the bounded JSON file used by the web module for manual tab, clip and selected-setting transfer. Its schema is [unify.transfer.v1.schema.json](../schemas/unify.transfer.v1.schema.json).

## Other documentation

The [unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md) defines shared maturity, evidence and writing rules. Describe actual behavior from source, build configuration and tests; do not present browser controls or architecture proposals as completed native OS services.
