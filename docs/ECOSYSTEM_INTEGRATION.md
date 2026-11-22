# Ecosystem integration

## Model

DuckOS is the OS core. Specialist repositories stay independently built and released. Their source trees are attached under `ecosystem/` as pinned Git submodules, preserving histories, licenses and CI.

| Project | Owned domain | Existing interfaces | Boundary |
|---|---|---|---|
| Pytyliki | CPU/processor inventory and bounded analysis | `pytyliki.c-abi.v1` | read-only evidence; no scheduler, clock/voltage or firmware control |
| Reaper | Language, parser, VM, IDE/LSP/DAP and toolchain | versioned language APIs; OPlague report consumer | Python reference is authoritative; C17 is partial; not a kernel compiler |
| OPlague | Device inventory, INF/ZIP/UDRV inspection and candidate graph | `oplage.device-snapshot.v1`, `udrv.v1` | no driver install/load/extract/execute; candidate match is not certification |
| VentuSample | Sample import/export, generation and offline DSP | `ventusample.pack.v1/v2` | no real-time audio device or system driver |

## Beelzebul

The 66-rule Beelzebul policy, schema, scanner, regression tests and CI workflow are copied from Pytyliki into the DuckOS root. It can independently guard changes to this repository; the Pytyliki submodule retains its own workflow and scans its own source.

The scanner is read-only. CI applies its verdict. It does not rewrite source, execute plugins, scan runtime memory or protect a running kernel.

## Interface rules

1. Every cross-project exchange requires a versioned schema or ABI.
2. Native libraries are opt-in and loaded only from an explicitly trusted path.
3. Device records and package metadata are untrusted data.
4. No project implicitly launches another project's code.
5. Privileged OS services are implemented and reviewed in DuckOS.

Pinned URLs and commit IDs are recorded in `.gitmodules` and `ecosystem/registry.v1.json`.
