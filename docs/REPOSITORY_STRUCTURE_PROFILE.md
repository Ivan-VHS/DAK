# Repository Structure Profile — DAK

**Normative reference:** [Ivan-VHS Repository Structure Standard](REPOSITORY_STRUCTURE_STANDARD.md).

This profile maps the shared logical structure to DAK's Reaper-native operating-system and desktop architecture. It is an architectural map, not a claim that every planned subsystem has shipped.

## Canonical layout

| Concern | Existing canonical location | Responsibility |
|---|---|---|
| Project entry and policy | `README*.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE` | Product scope, supported targets, release boundaries and governance |
| Architecture and status | `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/FOUNDATION_ARCHITECTURE.md`, `docs/IMPLEMENTATION_STATUS.md` | Layer ownership, implementation maturity and navigation |
| Reaper-native OS contracts | `duckos/` — especially `kernel/`, `drivers/`, `runtime/`, `graphics/`, `network/`, `security/` | Canonical DAK subsystem and hardware-facing Reaper source |
| Kernel and boot | `kernel/`, `boot/`, `foundation/` | Boot/runtime primitives, native core and system foundations |
| Desktop and applications | `desktop/`, `projects/`, `catalogs/`, `manifests/` | Native host, application ownership, catalogues and release manifests |
| Verification | `tests/`, `contract_tests.rpr`, `core_mvp_tests.rpr`, `system_platform_tests.rpr` | Native contracts, platform checks and host-side integration tests |
| Machine contracts | `schemas/`, `catalogs/`, `manifests/`, `federation/` | Versioned system, device, application, deployment and federation formats |
| Reproducible tooling | `scripts/`, `tools/`, `CMakeLists.txt`, `package.json` | Build, validation, packaging and host-side automation |
| CI | `.github/workflows/` | Boot image, native builds, system contracts, desktop and release gates |
| Supporting material | `assets/`, `examples/`, `artifacts/` | Licensed media, examples and generated evidence with provenance |

## DAK-specific boundaries

- Reaper `.rpr` sources in the DAK subsystem tree are the native language lane for OS/kernel contracts. Kernel behavior must not be replaced with a Python implementation merely to satisfy a generic directory convention.
- Existing host-side utilities and compatibility adapters retain their own boundaries; they are not automatically kernel code.
- Bootable-image, QEMU, platform and native-host evidence must be described separately. A host test or source contract is not proof of a booted target.
- Drivers, firmware flashing and device mutation remain out of scope for a structure-only validation job.
- Product/catalogue/manifest data is not executable capability by itself.

## Formal evidence

DAK uses Reaper contract tests, native build checks, boot-image validation and platform-specific evidence. A separate theorem-prover directory is not a requirement for an operating-system repository. Keep formal language contracts distinct from mathematical proof claims.

## Change rule

A path migration must update Reaper module/source references, build targets, boot/image assembly, manifests, schemas, test registration, package tooling and cross-repository DAK integrations in the same reviewed change.
