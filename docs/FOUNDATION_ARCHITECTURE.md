# DAK Foundation Architecture

**Author / project direction:** Ivan-VHS  
**Status:** initial architecture baseline; decisions marked TBD must be resolved by an Architecture Decision Record before implementation.

## 1. Scope

DAK is intended to be an independently implemented operating system with a stable system ABI, native services, a graphical environment, package management and capability-based application isolation. This document describes boundaries and sequencing, not shipped functionality.

The first practical target should be a single documented PC architecture and an emulator-backed development environment. Keep architecture-specific code behind a hardware abstraction boundary so later targets do not leak into generic kernel code.

## 2. Dependency direction

`Boot firmware/protocol → kernel entry → memory/interrupt core → scheduler/processes → syscall ABI → initramfs/userland → services/VFS/IPC → graphics/device services → packages/apps`

Dependencies point down toward stable lower-level contracts. The graphics shell must not call private kernel internals; applications must not depend on driver implementation details.

## 3. Core boundaries

### Boot chain
Owns image layout, boot configuration, early diagnostics and the transfer of validated boot information. The boot contract must define memory map format, framebuffer information when available, command line, initramfs location and version.

### Kernel
Owns privileged execution, memory protection, interrupt handling, scheduling, timers, process isolation and the minimal syscall entry. Keep architecture-specific assembly and CPU register handling separate from policy and generic algorithms.

### Initramfs and first userland
Contains the first executable, essential configuration and recovery utilities. The first user process should start with the smallest necessary authority and report failures with stable error codes.

### System ABI
Defines fixed-width types, alignment, calling convention, version negotiation, handles, error values, ownership and capability checks. Never expose kernel pointers or compiler-private object layouts as public ABI.

### Driver interface
Defines device discovery, request queues, buffer ownership, cancellation, timeouts, DMA constraints and driver lifecycle. Begin with a mock/test driver and safe device enumeration before allowing hardware mutation.

### Graphics
Implement a simple framebuffer path first. A compositor consumes a display/input abstraction; a GPU backend is a separate provider. Hardware acceleration is an optimization layer, not a prerequisite for the first bootable UI.

### Service manager and IPC
Services communicate through versioned message contracts with bounded payloads, explicit caller identity and cancellation semantics. Service supervision includes startup dependencies, restart policy and crash logs.

### Package manager
Package metadata is validated before installation. Install, upgrade and removal are transactional: prepare, verify, stage, switch active state, commit, or rollback. A failed update must leave the previous bootable state intact.

### AI application sandbox
AI agents run as untrusted user processes. File, network, device and process privileges are explicit capabilities granted by the user/system policy. No implicit host-wide shell authority.

## 4. Reaper integration

The Reaper language is a possible first-party development path, not a dependency that may be assumed before it is proven. The integration requires a native compiler, target object generation, relocation support, stable DAK ABI, runtime support and conformance tests. The bootstrap remains buildable with a documented fallback toolchain until self-hosting is verified.

## 5. Security invariants

- Validate all sizes, offsets, counts and alignment before memory access.
- Separate user memory from kernel memory and validate every crossing.
- Check capabilities at the system-call boundary.
- Keep driver and package inputs untrusted.
- Bound queue depth, message size, memory allocation and retry loops.
- Record security-relevant events without logging secrets.
- Provide a recovery path for failed boot, service startup and package update.

## 6. Build and test contract

The first CI pipeline should:
1. pin or report compiler, linker, emulator and image-tool versions;
2. build a deterministic boot image;
3. validate image structure and required sections;
4. boot it in a headless emulator with a timeout;
5. capture serial/debug output and the exit status;
6. fail if the expected boot marker is absent;
7. retain the image checksum and log as artifacts.

As the kernel grows, add unit tests for pure algorithms, host-side tests for parsers and allocators, emulator integration tests for privileged paths, and fault-injection tests for recovery.

## 7. Initial milestones

| Milestone | Deliverable | Acceptance evidence |
|---|---|---|
| F0 | toolchain and reproducible image | clean build from documented commands |
| F1 | bootable minimal kernel | emulator prints boot marker and exits/powers off predictably |
| F2 | validated memory map and allocator | boundary tests and allocator invariants |
| F3 | exceptions, timer and scheduler skeleton | controlled fault report and tick trace |
| F4 | first user process and syscall ABI | userland hello + invalid-call rejection |
| F5 | initramfs, VFS and IPC | read-only file operation and service request |
| F6 | framebuffer and input | visible frame and input event path |
| F7 | compositor, driver ABI and package transactions | isolated tests for each interface |
| F8 | GPU backend and sandboxed apps | capability tests and fallback rendering path |

## 8. Open decisions

Create ADRs before locking down: boot protocol; initial CPU target; kernel architecture; physical allocator strategy; virtual address layout; interrupt controller; timer source; filesystem format; IPC model; display provider; package signature format; and bootstrap-to-Reaper transition.

A decision should include rejected alternatives and migration cost. Do not silently change a public ABI.

## 9. Licensing and provenance

The project may implement published standards and independently designed interfaces. It must retain notices and attribution for any adopted third-party components, respect their licenses, and avoid copying proprietary implementation code. A repository license should be selected explicitly before distributing a binary or source release.
