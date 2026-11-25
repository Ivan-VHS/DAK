# DuckOS

DuckOS is the operating-system project. **Mora** is its unified desktop shell and application workspace.

[Open Mora](mora/index.html) · [Architecture](docs/ARCHITECTURE.md) · [Implementation status](docs/IMPLEMENTATION_STATUS.md) · [Native roadmap](docs/IMPLEMENTATION_ROADMAP.md) · [Shared standards](docs/SHARED_STANDARDS.md)

## What is available

- **Mora shell:** browser-local desktop UI, application catalogue, system panels, local preferences and scoped offline assets.
- **Duck Desktop:** native user-space maintenance tools, read-only audit and reversible current-user startup controls.
- **Reaper workbench:** process-isolated Studio launch and delegated static checks through the DuckOS CLI.
- **Hardware and compatibility:** bounded read-only PCI/USB or Windows PnP inventory, PE inspection and dry-run runtime discovery.
- **Deployment tooling:** verified component bundles and non-destructive disk-layout plans.

An experimental x86_64 firmware-bootable Stage 1 image adds a native 4 KiB physical-frame bootstrap allocator; BIOS/UEFI verification for this revision is running in the pull-request CI. See [Bootable image](docs/BOOTABLE_IMAGE.md). It uses pinned Limine media, a DuckOS-owned kernel entry, Boot Info v1 validation and a native monotonic 4 KiB physical-frame allocator that allocates only from validated usable RAM. The allocator is an early-boot primitive: it has no free/reclaim path or page-table manager. This is not yet a complete OS. Processes, scheduler execution, syscalls, reusable memory management, drivers, filesystem, service runtime and native Mora compositor remain unimplemented. The [implementation status](docs/IMPLEMENTATION_STATUS.md) and [roadmap](docs/IMPLEMENTATION_ROADMAP.md) separate delivered, partial and planned work.

## Workspace

Clone the repositories at the exact commits pinned by DuckOS:

```sh
git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
```

Initialize the Reaper workbench when needed:

```sh
git submodule update --init projects/reaper
duckos reaper status
duckos reaper studio
duckos reaper check ./examples/program.rpr
```

## Build the experimental boot image

On Linux x86_64, install GCC, binutils, curl, tar, xorriso and sha256sum, then run:

    boot/build-iso.sh --work-dir build/duckos-boot --output build/DuckOS-Stage1-x86_64.iso

The pinned Limine binary archive is SHA-256 checked before use. The ISO is intended for BIOS and UEFI x86_64 boot. QEMU verification with OVMF is documented in [Bootable image](docs/BOOTABLE_IMAGE.md); a successful build alone is not evidence that every physical machine is supported.

## Run and verify

Open `mora/index.html` in a modern browser. The shell has no external runtime dependencies. Run browser contract tests with Node.js 18+:

```sh
npm test
```

Collect a read-only hardware snapshot:

```sh
duckos hardware-inventory --output hardware-inventory.json
```

## Product and system specifications

- [Mora design system](MORA_DESIGN_SYSTEM.md) · [Mora integration](docs/MORA_INTEGRATION.md) · [Mora Commons](docs/MORA_COMMONS.md)
- [Preinstalled applications](docs/PREINSTALLED_APPLICATIONS.md) · [Versioned app catalogue](catalogs/preinstalled-applications.v1.json)
- [Repository federation](docs/REPOSITORY_FEDERATION.md) · [Native Reaper integration](docs/REAPER_INTEGRATION.md)
- [DuckBridge](docs/DUCKBRIDGE.md) · [Windows compatibility](docs/WINDOWS_COMPATIBILITY.md) · [Deployment](docs/DEPLOYMENT.md)

## Engineering rule

Describe behavior from current source, tests, schemas and CI. A catalogue or roadmap is not proof of implementation. Browser preferences are not kernel enforcement; PE inspection is not Windows process execution; SHA-256 is not proof of authorship.
