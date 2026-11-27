# DAK Application Build, Package and Runtime Specification

**Specification:** DAK-APP-RELEASE-001  
**Version:** 1.0.0  
**Status:** Proposed implementation contract  
**Owner:** DAK  
**Applies to:** every first-party DAK application and every federated workbench  
**Last updated:** 2026-11-28

## 1. Purpose

Define one release contract so each application can be built, versioned, packaged, installed, launched, updated, diagnosed and removed on supported desktop operating systems and DAK OS.

This document is a specification, not a claim that every application or target runtime is already implemented. A target becomes **supported** only after its build, package, install, launch, smoke-test and uninstall jobs pass on that target.

## 2. Release principles

1. One application identity and one versioned application contract across platforms.
2. Native builds use the platform ABI and native system APIs; no emulation is implied by a package being available.
3. Keep application domain logic and file formats portable. Put OS integration behind explicit platform adapters.
4. Offline-first and local-first by default. No hidden network calls, telemetry, shell execution or background privilege escalation.
5. Install and update operations are transactional where the platform supports it; preserve user data during upgrade and uninstall.
6. Use explicit capabilities and least privilege. Driver, firmware, device-register, bootloader and administrator operations are out of scope unless separately authorized and specified.
7. Reproducible builds, pinned dependencies, SBOM, checksums, provenance and signed release metadata are required for stable releases.
8. A missing native DAK ABI, service, package manager or runtime is a blocker—not something to simulate silently.

## 3. Supported target matrix

| Target | Executable | Package / installer | Release status rule |
|---|---|---|---|
| Windows 10/11 x86_64 | PE32+ `.exe`, DLL | MSI, MSIX, portable ZIP | Requires Windows CI build + install/launch/uninstall tests |
| Linux x86_64 | ELF64 | DEB, RPM, AppImage; Flatpak only with a validated manifest | Requires Linux CI build + install/launch/uninstall tests |
| macOS arm64 and x86_64 | Mach-O; universal binary only when both slices are built | APP bundle, DMG, PKG | Requires macOS CI build + signing/notarization policy + launch tests |
| DAK OS x86_64 | DAK-native executable under the published DAK ABI | DPAK (proposed), system repository package | Requires DAK loader, process/runtime, VFS, package manager and capability service integration |

A portable archive is not equivalent to an installer. An ELF binary is not automatically a DAK executable. Windows PE compatibility is not implied by PE inspection or a compatibility workbench.

## 4. Canonical application package

Every distributable application MUST provide:

- `app.json`: schema-versioned identity, display name, semantic version, publisher, entry point, target architectures, minimum OS/ABI, dependencies, permissions, data locations and update channel.
- `VERSION`: exact release version, synchronized with package metadata.
- `SPEC.md`: user-visible behavior, supported platforms, limitations and compatibility.
- `LICENSE` and third-party notices, using the project's actual license; never infer or replace a license.
- `bin/`: platform-specific executable(s), libraries and resources.
- `share/`: icons, translations, templates and static data.
- `tests/`: unit, contract, package and launch smoke tests.
- `SHA256SUMS`, SBOM and signed provenance for stable releases.
- `install`, `uninstall`, `run` entry points or equivalent native package-manager integration.

The package manifest schema is versioned independently from application versions. Breaking manifest changes require a new major schema version and a migration path.

### 4.1 Identity and versioning

Use SemVer: `MAJOR.MINOR.PATCH`. Pre-releases use `-alpha.N`, `-beta.N` or `-rc.N`. Build metadata MUST NOT be used to imply compatibility.

The canonical identity is immutable and independent of translated display names. Package IDs are lowercase reverse-DNS identifiers. Application versions may differ between applications; the DAK release train records the exact version of each component.

### 4.2 Package formats

- Windows: signed MSI/MSIX where supported; portable ZIP as a secondary artifact.
- Linux: DEB and RPM where packaging dependencies are satisfied; AppImage for self-contained portable distribution; Flatpak only with reviewed sandbox permissions.
- macOS: signed APP bundle, DMG and PKG where appropriate.
- DAK: DPAK package format is a proposed contract, not an existing supported format until parser, verifier, installer, database, rollback and repository client are implemented.

Packages MUST declare architecture, runtime/ABI, dependencies, permissions, file ownership, install hooks (if any), data migration and removal behavior. No package hook may execute arbitrary shell text from an untrusted manifest.

## 5. Build and launch contract

Each repository MUST expose equivalent commands (native scripts may differ):

- `configure`: validate toolchain, SDK and target.
- `build --target <platform>`: produce deterministic target artifacts.
- `test`: run unit and contract tests.
- `package --target <platform>`: create package and metadata.
- `verify-package`: validate schema, hashes, signatures and dependency closure.
- `install --package <file>`: install with explicit user approval.
- `run --app <id>`: resolve the installed, verified entry point without shell interpolation.
- `doctor`: report missing runtime, ABI, libraries, permissions or incompatible OS.
- `uninstall --app <id>`: remove application files while preserving user data unless the user explicitly requests data deletion.

A DAK launcher MUST resolve only verified installed paths, validate package signatures and declared capabilities, pass structured arguments, and never invoke manifest commands through a shell. Until the DAK process manager and executable loader are available, the launcher may report the application as not runnable; it MUST NOT report a successful launch.

## 6. Application inventory and current maturity

The authoritative DAK shell catalogue is `mora/apps.json`. Catalogue panels are not automatically standalone native executables. Each entry must receive its own package manifest and platform evidence before being marked distributable.

### 6.1 Built-in catalogue

| ID | Application | Current catalogue maturity / release treatment |
|---|---|---|
| cockos | Cockos | shell panel; standalone packaging not yet evidenced |
| kavun | Kavun | shell panel; standalone packaging not yet evidenced |
| kabon | Ka-bon | shell panel; standalone packaging not yet evidenced |
| gloverty | Gloverty | shell panel; standalone packaging not yet evidenced |
| po | Po | shell panel; standalone packaging not yet evidenced |
| illidia | Illidia | shell panel; native game-launch integration is separate work |
| unify | Unify | shell panel; standalone packaging not yet evidenced |
| sestem | Sestem | partial local workspace |
| setupup | SetupUP | partial local workspace |
| orriganize | ORGze | partial local workspace; preserve the display name ORGze |
| abriganza | Abriganza | partial local workspace |
| olaab | Olaab | partial local workspace |
| concrete-thump | Concrete Thump | partial local workspace |
| seu-beu | Seu-Beu | partial local workspace |
| love-il | Love-IL | partial local workspace |
| poi | Poi | partial local workspace |
| poi-2 | Poi-2 | partial local workspace |
| po-2 | Po-2 | partial local workspace |
| gamecharager | GameCharager | partial local workspace |
| exedotexe | EXEdotEXE | partial local workspace |
| red-sparrow | Red Sparrow / 赤雀 | partial local workspace; local-only user notes |
| mora-ai | Mora AI | partial local rules |
| security | Sentinel | shell policy only; not a security enforcement boundary |
| updates | Restore | shell snapshot only; not a native OS updater |
| runtime | Bridge | partial PE inspection/prefix foundation; no native PE process execution |
| workspace | Control | shell preferences |
| provenance | Proof | SHA-256 only; signature/provenance verification remains required |
| mora-boost | Mora Boost | external native workbench; package and launch contract required |
| desktop | DAK Desktop | partial native userland tool |
| mora-commons | Mora Commons | implemented local catalogue; not an application installer |

The spelling in the inventory is the stable catalogue ID; display names are user-facing. Correct any legacy display-name typo in the catalogue as a separate reviewed change rather than silently changing an ID.

### 6.2 Federated workbenches

The DAK repository pins these independent projects as submodules. Their source, licensing, build and release ownership remain in their own repositories; DAK coordinates integration and records exact commit/version references.

| Project | Repository | Current implementation boundary |
|---|---|---|
| Reaper | Ivan-VHS/Reaper | Python reference runtime and developing native C17 toolchain; Windows/Linux/macOS runtime contract; desktop support currently Windows-first |
| Pytyliki | Ivan-VHS/Pytyliki | C11 native hardware/processor tooling and C ABI; physical hardware actions remain capability-gated and read-only by default |
| VentuSample | Ivan-VHS/VentuSample | C++20, Qt 6, CMake, offline scalar DSP; desktop build is CI-gated on Qt SDK availability |
| OPlague | Ivan-VHS/OPlague | Windows-first desktop workbench with Python tooling and Rust ABI consumer; other runtime platforms do not imply desktop parity |

DAK release metadata MUST pin each submodule to an immutable commit SHA. Do not build a release from a moving `main` pointer.

## 7. Required per-project release work

### DAK

- Turn the catalogue entries into validated, versioned app manifests.
- Separate Mora shell panels from standalone native apps.
- Implement package format schema, verifier, local repository index and transactional installer.
- Implement trusted launcher, process lifecycle, logging and app health checks.
- Add Windows/Linux/macOS host builds for the native desktop shell where supported.
- Add DAK-native execution only after loader, process, VFS, ABI and capability services are ready.
- Produce bootable OS images separately from application packages.

### Reaper

- Publish versioned CLI/runtime packages for Windows, Linux and macOS based on the actual supported reference runtime.
- Package the native compiler only for targets whose native frontend, backend, linker and ABI tests pass.
- Provide `.rpr` project execution through a stable CLI contract and explicit diagnostics.
- Publish editor/desktop packages only for platforms with successful native GUI builds.
- Coordinate the canonical IR, Span/SourceMap, DABI64 and DAK ABI contracts with Pytyliki and DAK.

### Pytyliki

- Publish native libraries and CLI tools for each verified compiler/OS/architecture combination.
- Package the C ABI with headers, import libraries and shared-library artifacts; test ABI layout and symbol compatibility.
- Separate simulator/reference hardware backends from physical target adapters.
- Keep hardware inspection read-only by default; no firmware, driver or device writes through package installation.
- Coordinate every shared compiler/IR/ABI change with Reaper.

### VentuSample

- Build the C++20 core and tests independently from the optional Qt desktop target.
- Publish native desktop packages only when Qt 6 is present and smoke tests pass.
- Preserve deterministic offline rendering, bounded WAV import/export and versioned pack manifests.
- Include plugin/DSP module artifacts only where a stable module ABI and host compatibility tests exist.

### OPlague

- Publish the read-only inspection CLI/core separately from the Windows desktop workbench.
- Keep Windows PnP inventory and platform-specific telemetry behind OS adapters.
- Package the Rust/Pytyliki ABI consumer only when the target shared library and ABI checks pass.
- Never imply that inspection, candidate matching or telemetry installs, signs or modifies a driver.

## 8. CI release gates

Every repository release workflow MUST include:

1. Clean checkout including pinned submodules.
2. Toolchain and dependency lock verification.
3. Build matrix by OS, architecture and build variant.
4. Unit, integration and contract tests.
5. ABI and public-symbol compatibility checks for native libraries.
6. Package manifest/schema validation.
7. Install, launch, update and uninstall smoke tests in isolated runners or VMs.
8. Dependency and license inventory; SBOM generation.
9. Hash and signature verification.
10. Artifact upload with immutable version and provenance.
11. A release summary that distinguishes passed, skipped, unsupported and blocked targets.

A skipped job is not a pass. A package built but not installed and launched is not a supported release. Stable tags are created only after all required gates for the declared target matrix pass.

## 9. Release channels

- `nightly`: commit-pinned development artifacts; no stability promise.
- `preview`: feature-complete candidates; explicit known limitations.
- `stable`: signed artifacts with complete target evidence.
- `lts`: stable ABI and security maintenance policy; introduced only after maintenance ownership is established.

## 10. Data, update and rollback behavior

Application binaries and user data MUST have separate locations. Updates MUST validate package identity, version, signature, dependencies and migration before replacing files. Preserve the last known-good installation where atomic replacement is unavailable. A failed migration must leave user data recoverable. Uninstall removes binaries and owned integration records; user data is retained unless explicitly selected for deletion.

## 11. Compatibility declaration

Each release publishes a machine-readable compatibility record containing:

- application ID and SemVer;
- package schema version;
- OS family and minimum version;
- architecture and executable format;
- required ABI/runtime versions;
- dependencies and optional integrations;
- capabilities/permissions;
- build commit, toolchain and reproducibility metadata;
- test evidence and artifact hashes.

Compatibility is declared per artifact, not inferred from source-language portability.

## 12. Definition of done

An application is **DAK-ready** only when it has a valid manifest, DAK executable/ABI target, package verifier acceptance, installation, launch, lifecycle, permission enforcement, update/rollback, uninstall and automated DAK VM evidence.

An application is **desktop-ready** for an ordinary OS only when its native artifact builds and passes install, launch, data-preservation and uninstall tests on that OS.

An application is **release-ready** only when its declared platform matrix has no unexplained skipped or failed required gates, all artifacts are versioned and checksummed, and release provenance is published.

Until those conditions are met, report the application as `specified`, `building`, `partial`, `blocked` or `unsupported`—never `ready`.

## 13. Immediate implementation sequence

1. Validate the existing catalogue and define the app-manifest schema.
2. Generate one manifest per catalogue entry and mark shell-only panels accurately.
3. Add shared build/package/verify/run command contracts to each project.
4. Add Windows/Linux/macOS build and package CI for each project according to its native toolchain.
5. Add DAK package verifier and launcher only against implemented kernel/runtime contracts.
6. Add DAK VM integration tests and signed repository metadata.
7. Publish coordinated release manifests pinning all four submodules.

This specification is the shared baseline. Each project must implement its own repository-specific build and tests in separate reviewable changes; no project is considered complete merely because this document exists.
