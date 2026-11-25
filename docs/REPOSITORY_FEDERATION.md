# DuckOS monorepo and source provenance

DuckOS is the integration host and the single monorepo checkout. The four specialist upstream repositories are vendored as ordinary tracked directory trees under `projects/`. A normal clone contains every source file; it does not require submodule initialization, a second checkout or network access to populate the source trees.

## Monorepo layout

| Workspace path | Upstream project | Source responsibility | License |
|---|---|---|---|
| `projects/reaper` | [Reaper](https://github.com/Ivan-VHS/Reaper) | Primary language, compiler/toolchain and system-policy contracts | Apache-2.0 |
| `projects/pytyliki` | [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | C11 processor, memory and diagnostics workstation | MIT |
| `projects/oplague` | [OPlague](https://github.com/Ivan-VHS/OPlague) | Read-only device, driver, signature and GPU evidence | Apache-2.0 |
| `projects/ventusample` | [VentuSample](https://github.com/Ivan-VHS/VentuSample) | C++20 procedural audio and offline DSP workstation | Apache-2.0 |

DuckOS root owns the kernel, boot, Mora desktop, system contracts, release pipeline and cross-project adapters. Each imported product keeps its own source layout: source, headers, tests, docs, schemas, tools, examples, assets, build files and project-local metadata are not flattened into one namespace.

## Source identity and provenance

Two versioned files are authoritative:

- `federation/repositories.v1.json` describes product roles, workspace paths, licenses, runtime boundaries and integration policy.
- `federation/vendor-sources.v1.json` pins the exact upstream commit SHA and root tree SHA for each copied source tree, together with file counts, content byte counts and license information.

The vendored directory is accepted only when its Git tree SHA, tracked file count, content byte count and upstream LICENSE match the source lock. The source commit signatures were verified when the current pins were selected. A content/tree match proves snapshot identity; it does not certify the project or its runtime behavior.

## First checkout

```sh
git clone https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS
bash scripts/vendor-ecosystem.sh --verify
```

No `--recurse-submodules` flag is needed. `.gitmodules` is not part of the monorepo layout.

## Import and update process

The source importer is `scripts/vendor-ecosystem.sh`. Its `--import` mode:

1. Refuses to run on a dirty worktree.
2. Removes only the four expected Git submodule entries and the obsolete `.gitmodules` file.
3. Imports each exact upstream commit with Git fetch and `git read-tree --prefix`.
4. Preserves each upstream repository's root tree below its existing `projects/<id>` path.
5. Verifies tree SHA, file count, source byte count and license file after import.

The importer never selects a floating branch head and never overwrites an already-vendored directory with a different tree. A new upstream revision requires a reviewed change to both provenance manifests and a successful import/verification run.

The source lock preserves upstream commit and tree identities. Full development history remains authoritative in the original upstream repository; the vendored snapshot and its provenance are part of DuckOS history. This keeps DuckOS's mainline history reviewable without replaying every historical upstream commit.

## Build and verification

```sh
npm test
bash scripts/vendor-ecosystem.sh --verify
bash boot/build-release-iso.sh --work-dir build/release --output dist/DuckOS-Release-x86_64.iso
```

The release pipeline builds and tests Reaper's native C17 tools, Pytyliki's C11 tools, VentuSample's C++20/Qt target and OPlague's user-space inspection/test suite, packages source and license notices, then verifies the x86_64 BIOS/UEFI Stage 1 image in QEMU. Host binaries remain host tools; they are not implicitly kernel executables.

## How projects fit together

- **Reaper** is the primary language and toolchain for DuckOS-owned system code. Its present native/host workbench and DABI64 frame validators are distinct from a freestanding kernel compiler or kernel IPC implementation.
- **Pytyliki** provides processor inventory and bounded benchmark/profile evidence. It must not change clocks, voltage, affinity, fan curves, firmware, MMIO or scheduler state.
- **OPlague** provides read-only device, package, driver-signature and GPU evidence. Device matches are candidates, not permission to install a driver.
- **VentuSample** owns audio generation and offline DSP. Its existing renderer does not automatically become a real-time audio service or kernel driver.

Preferred peer exchange remains versioned JSON/artifacts first, explicit trusted C ABI second and kernel IPC only after DuckOS has processes, capabilities, quotas, cancellation and audit.

## Reproducibility and safety

- Preserve each upstream `LICENSE`, `NOTICE`, copyright header and nested third-party notice in its original relative path.
- Do not flatten project files or silently rename public APIs during import.
- Retain upstream `.github/workflows` files inside each project as provenance and project documentation; only DuckOS root workflows execute for this monorepo.
- The OS build does not automatically launch imported apps, scripts, plugins, drivers or installers.
- Keep Reaper, Pytyliki, OPlague and VentuSample runtime boundaries explicit. Vendoring source does not grant kernel, administrator, FFI, device or microphone privileges.
- Apply changes upstream first when the product's own repository is authoritative, then update its exact DuckOS snapshot in a separate reviewed PR.

The NEXUS peer contract map is documented in [Ecosystem NEXUS integration](ECOSYSTEM_NEXUS_INTEGRATION.md).
