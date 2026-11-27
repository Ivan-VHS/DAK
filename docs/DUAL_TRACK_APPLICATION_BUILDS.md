# Dual-track application builds

DuckOS application delivery has two deliberately separate target tracks.

## Track A — host-native workbench builds

The GitHub Actions workflow `.github/workflows/application-build-matrix.yml` builds the currently federated upstream workbenches for Linux x86_64 and Windows x64:

- Reaper: native host compiler/toolchain targets and tests.
- Pytyliki: native host tools and tests.
- VentuSample: DSP/core tests on both hosts; Qt desktop target on Linux when Qt 6 is available.
- OPlague: read-only user-space workbench validation and source payload.
- Mora: catalogue and shell contract tests on Linux.

Each workbench receives a separate host/architecture-labelled archive (Reaper, Pytyliki, VentuSample and the OPlague source snapshot). These are reproducible CI build bundles, not end-user installers and not Duck-native executables. The existing `release-iso.yml` remains the Linux x86_64 source-pinned ecosystem ISO build and QEMU BIOS/UEFI boot-validation pipeline.

## Track B — Duck-native application builds

This track is intentionally not advertised as producing binaries yet. The current Stage 1 kernel validates boot information, establishes early CPU tables and allocates an initial physical frame, then halts. It does not yet provide the user-mode execution foundation required by applications.

The native track can be enabled only after the following contracts are implemented and tested together:

1. Stable executable format, loader and relocation rules.
2. Ring-3 entry/return and a versioned syscall ABI.
3. Process lifecycle, address spaces, memory protection and scheduling.
4. Filesystem, package format, installation and atomic update contracts.
5. Kernel-enforced capabilities, service supervision and IPC.
6. Native windowing, input, compositor and application runtime APIs.
7. Cross-target toolchain, linker, SDK, reproducible packaging and ABI conformance tests.

Until then, native-target readiness is reported as blocked in CI. No host executable may be renamed or presented as a Duck-native binary.

## Repository and safety boundaries

Upstream projects remain independent Git repositories pinned to exact commits in the DuckOS superproject. Builds consume those pins; they do not advance submodules. OPlague and Pytyliki hardware inspection stays read-only. VentuSample processing remains offline by default. Reaper extensions remain user-space and capability-bounded. The pipeline does not install drivers, write firmware, or execute imported application manifests.

## Current scope

The build matrix covers the four projects presently declared in `federation/repositories.v1.json`, plus Mora's own shell/catalogue tests. It does not claim that every app identity in `mora/apps.json` is an independently implemented native application. Each catalogue entry must receive an explicit implementation/build recipe and maturity state before it can be counted as a shippable application.
