# DuckOS native platform

This tree is the native-OS bring-up track. It is separate from the existing browser shell and the Python/Linux host utilities. The first target is x86-64 PC hardware using the Limine boot protocol.

## Build targets

From this directory:

    make kernel
    make initramfs
    make test
    make services-test
    make shell
    make compositor
    LIMINE_DIR=/path/to/limine/share make iso

The kernel build needs Clang/LLD. The compositor build needs Meson, Wayland server headers and wlroots 0.19 development files. The native EGL shell client needs Wayland client/wayland-egl, wayland-protocols, EGL and GLESv2 development files. ISO creation additionally needs xorriso, the Limine host tool and the Limine BIOS/UEFI assets. BUSYBOX_STATIC may point to a trusted static BusyBox binary to populate the early userspace.

Build output is written to ../build/native, outside this source tree.

## Subsystems and truthful status

| Subsystem | Current state | What exists now |
|---|---|---|
| Kernel | Early bring-up | Freestanding x86-64 ELF, Limine base revision 6 requests, COM1 logging, memory-map summary and framebuffer test pattern |
| Bootloader | Integrated external project | Limine config and ISO staging; Limine itself is not forked or modified |
| initramfs | Builder implemented | Deterministic newc CPIO generator and an early init script; kernel does not yet unpack it or launch PID 1 |
| Wayland compositor | Preview bring-up | wlroots backend, renderer, output frame path, compositor and xdg-shell globals; input seat/focus and desktop policy remain unfinished |
| Package manager | Local prototype | SHA-256 verified, traversal-safe, staged package store with list/verify/remove |
| Driver ABI | Contract only | Versioned C header; no kernel module loader or device model exists yet |
| GPU acceleration | Host integration only | wlroots/Mesa EGL-GLES renderer path; no GPU driver or DRM subsystem in the DuckOS kernel |
| AI sandbox | Linux host wrapper | Bubblewrap namespaces, network isolation, reduced filesystem view and resource limits; not a kernel security boundary |
| Installer image | Builder integrated | Hybrid BIOS/UEFI ISO staging; it currently boots the bring-up kernel, not a complete desktop installation |
| Core services | User-space prototype | Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify; see ../docs/CORE_SERVICES.md |

## Core services

The Python package in services/duckos_services provides the Cockos PipeWire graph adapter, Kavun layout planner, Ka-bon shortcut router, Gloverty palette audit, Po command registry, Illidia session snapshot store and Unify profile/event hub. It uses only the Python standard library. PipeWire routing additionally needs pw-link on the host. Run make services-test to execute its unit tests.

These services run in host user space. Kavun does not yet control compositor surfaces, Ka-bon does not capture system-wide input, and Unify's event bus is in-process rather than an authenticated IPC transport.

## Kernel handoff

The current kernel is intentionally small. It validates the Limine base revision, initializes a serial console, reports bootloader information, the HHDM offset, usable RAM and boot modules, and paints the provided 32-bit RGB framebuffer. It then halts safely.

Not implemented: GDT/IDT ownership, APIC and interrupt routing, physical/virtual page allocators, SMP startup, scheduler, syscall boundary, process loader, VFS, filesystem drivers, PCI enumeration, USB, storage, networking, power management, module loader, IOMMU and firmware services. These are explicit future milestones, not hidden behind placeholder APIs.

## Security and release rules

- No package archive is executed during installation.
- Archive paths are validated; symlinks, hard links and device nodes are rejected.
- A digest inside an unsigned package is an integrity check, not publisher authentication.
- The agent wrapper refuses an unsandboxed fallback and refuses root execution.
- The native kernel is not yet suitable as a daily-driver OS or for handling untrusted workloads.
- Never flash the generated ISO to a physical disk as an installer. The ISO is a boot test image only until partitioning, installation, recovery, rollback and hardware detection are implemented.

## Next engineering gates

1. Add physical page allocation and reclaim Limine memory only after all boot references are copied or no longer needed.
2. Build GDT, IDT, exception handlers, APIC timer and keyboard/serial interrupt paths.
3. Add a scheduler, userspace ABI, ELF loader, process isolation and initramfs unpacking.
4. Add VFS, block layer, PCI bus enumeration and a small set of well-reviewed device drivers.
5. Finish Wayland seats, output lifecycle, input focus, session management and shell client.
6. Sign package metadata, add dependency solving and transactional OS updates.
7. Implement a boot-tested installer with partition checks, confirmation, rollback and recovery media.
