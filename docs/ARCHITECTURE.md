# DuckOS architecture

## Current baseline

The repository was previously an empty bootstrap. This integration supplies ecosystem references, contracts, security scanning and a roadmap; it does not yet contain executable OS or boot code.

## Target layers

| Layer | Responsibility | Status |
|---|---|---|
| UEFI bootloader | Validate image metadata, load kernel/initramfs, pass memory map and firmware tables | planned |
| Kernel substrate | x86_64 entry, GDT/IDT, exceptions, physical/virtual memory, allocator, timers, interrupt controller | planned |
| Driver ABI | Versioned C ABI, capability-gated handles, bounded buffers and explicit ownership | planned |
| Initramfs | Minimal immutable root and verified bootstrap services | planned |
| Userspace | Processes, IPC, VFS, file descriptors and service supervision | planned |
| Display | Framebuffer fallback and input path | planned |
| Wayland compositor | Unprivileged surfaces, input routing and damage tracking | planned |
| GPU acceleration | Explicit backend discovery, capability negotiation, shader pipeline and software fallback | planned |
| Package manager | Signed metadata, content hashes, dependency graph and transactional rollback | planned |
| AI-agent sandbox | Separate process, syscall/capability allowlist, resource quotas and audit log | planned |
| Installer/live ISO | Reproducible image, boot menu and safe disk-target confirmation | planned |

## Kernel and ABI principles

Early boot and privileged paths must be freestanding: explicit target triple, linker script, startup objects and minimal runtime. They must not depend on Python, a hosted standard library or a managed application runtime.

Driver ABI requirements:
- version negotiation and stable integer-width types;
- caller-owned buffers and explicit lengths;
- documented object lifetime and ownership;
- explicit error codes;
- capability checks before privileged operations;
- no implicit loading of untrusted modules.

A device snapshot, INF record or package hash is evidence, not permission to load a driver.

## Graphics

Start with a QEMU-tested framebuffer console. Add input and IPC before a compositor. Hardware acceleration is an optional backend with a truthful capability report and software fallback; never assume a GPU/API is present.

## Security and package management

The package manager should verify immutable metadata and signatures, solve dependencies and activate updates transactionally. Beelzebul scans source at development time; it does not provide secure boot, memory protection, runtime isolation or driver signature enforcement.

## Integration contracts

- Pytyliki may provide opt-in processor evidence through `pytyliki.c-abi.v1`; it does not schedule kernel tasks or write processor registers.
- OPlague may provide read-only snapshots through `oplage.device-snapshot.v1`; candidate matching is not driver approval.
- Reaper can later provide build/configuration tooling, but its current Python runtime and partial C17 track are not a freestanding compiler.
- VentuSample remains an offline audio specialist, not the system audio driver.

## Boot milestones

1. Cross-toolchain and QEMU smoke image.
2. UEFI entry and serial output.
3. Exceptions, interrupt handling and physical memory map.
4. Allocator, paging and timer tests.
5. Initramfs parser and first userspace process.
6. IPC, VFS and deterministic service lifecycle.
7. Display/input, then compositor.
8. Package transactions, isolation and installer media.

Promote a milestone only after code, tests and emulator evidence exist.
