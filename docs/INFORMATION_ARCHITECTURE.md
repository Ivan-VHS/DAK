# DuckOS documentation information architecture

[Project README](../README.md) · [Documentation index](README.md) · [Project overview](clusters/project-overview.md)

This map is the canonical navigation graph for DuckOS. It describes the documentation currently present in the repository and keeps browser prototypes, product specifications and native OS work at separate maturity levels.

## Entry points

- **Project entry:** [README.md](../README.md) — product direction, current Mora shell, maturity boundaries and validation commands.
- **Documentation home:** [docs/README.md](README.md) — subject clusters and normative standards.
- **Project overview:** [clusters/project-overview.md](clusters/project-overview.md) — concise description and links to current subsystems.
- **Documentation control:** [DOCUMENTATION_CONTROL.md](DOCUMENTATION_CONTROL.md) — evidence, navigation, ownership and maintenance rules.

## Topic clusters

### 1. Mora desktop and visual system

**Hub:** [Mora shell integration](MORA_INTEGRATION.md)

- [Mora Design System](../MORA_DESIGN_SYSTEM.md) — semantic palette, composition, geometry, motion and accessibility.
- [Mora theme tokens](../mora/theme.json) — versioned machine-readable palettes and interaction tokens.
- [Mora system policy](../mora/system-policy.json) — maturity and implementation boundaries.
- [Mora application registry](../mora/apps.json) — first-party panels and shell-level system tools.
- [Mora desktop entry point](../mora/index.html) — current unified browser shell.

### 2. Product applications

**Hub:** [Preinstalled application suite](PREINSTALLED_APPLICATIONS.md)

- [Versioned application catalog](../catalogs/preinstalled-applications.v1.json)
- [Application catalog schema](../schemas/preinstalled-applications.v1.schema.json)
- [Unify transfer format v1](UNIFY_TRANSFER_FORMAT_V1.md)
- [Unify transfer schema](../schemas/unify.transfer.v1.schema.json)

### 3. Native settings and operational tools

**Hub:** [Deep settings and user-space tools](DEEP_SETTINGS_AND_USERLAND_TOOLS.md)

- [Duck settings service](../duckos/settings.py) — versioned user profiles, validation, snapshots, import/export and audit journal.
- [Native settings panel](../duckos/desktop/settings_panel.py) — searchable settings pages and validation-driven profile editing.
- [User-space toolbox](../duckos/toolbox.py) — bounded text/data, TLS, RSS, hashing, port and unit utilities.

### 4. Engineering and language standards

- [Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md) — maturity, runtime state, evidence and terminology.
- [Language quality standard](LANGUAGE_QUALITY.md) — editorial conventions and diagnostic scope.

### 5. Runnable prototypes and evidence

- [Current Mora shell](../mora/index.html) — unified 13-entry desktop, local settings and guarded system-tool panels.
- [Earlier seven-app prototype](../prototype/mora-home.html) — historical/reference implementation.
- [Application catalog validator](../tools/validate_app_catalog.py) and [catalog tests](../tests/test_app_catalog.py).
- [Mora contract tests](../tests/mora-contract.test.mjs) and [core tests](../tests/mora-core.test.mjs).

## Dependency and cross-repository boundaries

DuckOS may link to specialist repositories, but a link is not evidence of shared source, ABI compatibility, native launchability or feature parity. Cross-repository integration must name the interface, version and verification evidence.

## Growth rules

Every new specification must have one primary topic owner, a stable path, a versioned schema where machine-readable data is exchanged, a parent hub and at least two useful incoming links. Important pages should remain within three to four clicks of the root README. Update the root README, documentation index and any affected topic hub in the same change.
