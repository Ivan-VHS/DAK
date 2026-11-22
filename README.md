# DuckOS — offline operating-system build tooling

DuckOS is the OS-development integration target in the Ivan-VHS project family. This first implementation establishes build contracts and validation tools before adding executable kernel, bootloader or desktop components.

**Current status:** build tooling and test fixtures. This repository does not yet contain a bootable kernel, UEFI loader, installer ISO, initramfs image or a running operating system.

## Implemented tools

| Tool | What it does | Safety boundary |
|---|---|---|
| System manifest v1 | validates architecture, kernel ABI, boot components, paths, sizes and SHA-256 hashes | reads staged files only; does not execute components |
| Image layout planner | calculates aligned, non-overlapping partition offsets | dry-run plan; never opens a physical disk or writes an image |
| Driver-module ABI | checks architecture, kernel ABI, entry symbol, capabilities and dependencies | validates metadata; never loads kernel modules |
| Dependency resolver | returns deterministic module order and rejects cycles/missing dependencies | planning only |

The tooling uses the Python standard library and works offline.

## Quick start

From the repository root:

```sh
python -m duckos --help
python -m unittest discover -s tests -v
```

After installing the package in a local virtual environment, the `duckos` command exposes the same checks:

```sh
duckos validate-manifest system.json ./staging-root
duckos plan-image partitions.json
duckos module-order modules.json
```

Input manifests are local JSON. No command from a manifest, boot component or module descriptor is launched.

## Versioned contracts

- `duckos.system-manifest.v1` records required boot components and SHA-256 identities.
- `duckos.driver-module.v1` describes a module's target architecture, kernel ABI, entry symbol, capabilities and dependencies.
- `duckos.image-layout.v1` records aligned partition byte ranges and sector geometry.

Paths are canonical and relative. Component paths reject traversal and symbolic links. Image plans carry `write_performed: false`; module validation carries `module_loaded: false`.

## Engineering gates before a bootable release

A bootable release still needs independently tested kernel and bootloader implementations, initramfs assembly, a root filesystem, signed release metadata, emulator or virtual-machine smoke tests, and a reproducible installer image. Those components are not claimed by this first wave.
