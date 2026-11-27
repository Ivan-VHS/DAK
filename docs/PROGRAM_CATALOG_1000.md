# DAKOS adoption map — OS build and release tooling

The supplied 1,000-program catalogue allocates its numbered domains to Pytyliki, Reaper, OPlague and VentuSample. DAKOS is an additional OS-development repository in the Ivan-VHS family; it does not renumber those entries or claim to own their implementations.

DAKOS adopts only ideas that fit operating-system development: deterministic build plans, embedded toolchain metadata, driver-module ABI contracts, binary/container validation, supply-chain manifests and hardware-inventory evidence.

## First implementation wave

- System component manifest and SHA-256 validator.
- Dry-run image layout planner with alignment, bounds and overlap checks.
- Driver-module ABI descriptor validation with architecture/kernel-ABI matching.
- Deterministic dependency ordering with cycle detection.

## Project boundaries

- Pytyliki remains the processor benchmark and numerical-analysis project.
- OPlague remains the read-only Windows device and driver-package inspection project.
- DAKOS may later consume verified metadata and module descriptors, but it must not duplicate their implementations or execute their payloads during inspection.
- A build plan is not proof of a bootable OS. Kernel, bootloader, initramfs, rootfs, compositor and installer outputs each need independent build and emulator tests.

No third-party operating-system or driver implementation code is copied into this repository.
