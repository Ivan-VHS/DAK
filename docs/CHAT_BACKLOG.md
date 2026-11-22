# Consolidated DuckOS backlog from available project conversations

Items below are requirements or research directions unless implementation evidence is listed in the status document.

## OS foundation

- UEFI boot chain and bootloader.
- Freestanding kernel, architecture startup, interrupt/exception handling, memory manager, scheduler, IPC and VFS.
- Initramfs, minimal userspace and service manager.
- Versioned driver ABI with capability-controlled access.
- Framebuffer, GPU backend and Wayland compositor.
- Signed package manager with content-addressed artifacts and transactional rollback.
- AI-agent process sandbox with explicit capabilities, quotas and audit logs.
- Reproducible installer/live ISO and QEMU image.

## Requested native utilities

| Utility | Intended responsibility | Owner |
|---|---|---|
| `sysmon-pulse` | CPU, RAM, swap and interrupt monitor with threshold colouring | DuckOS userspace; Pytyliki as optional read-only evidence source |
| `fd-watch` | Open file descriptors by PID, sockets and pipes | DuckOS process/filesystem tooling |
| `mmap-bench` | Bounded sequential/random mapped-file benchmark | DuckOS utility; Pytyliki optional analysis peer |

These utilities are not included in this bootstrap. Live reporting depends on OS process, memory and file APIs that do not yet exist.

## Cross-project work

- Reaper: keep language, parser, IR/VM, LSP/DAP and compiler tooling in Reaper. A freestanding backend is a separate future milestone.
- Pytyliki: processor inventory and benchmark evidence only; do not silently take over scheduling or power control.
- OPlague: use device IDs and package-integrity evidence for review; never treat a candidate as approval or install automatically.
- VentuSample: keep sound generation, DSP, WAV and sample-pack work in VentuSample.
- Beelzebul: 66-rule read-only repository policy in CI; it is not runtime sandboxing.

## Research directions

- AETHER-ANAS / Land-Water-Sky: exploratory CPU/GPU/distributed placement concept; requires measurable costs, capability negotiation and fallback. No speculative latency claims.
- Tri-Color Duck UI: desktop design direction, subordinate to accessibility and reduced-motion support.
- Recursive CI: generate candidate branches and reviewed PRs; never let an agent silently mutate protected policy or main.
- Meta-kernel/automatic feature expansion: bounded declarative registries with provenance and hard resource limits, not unbounded self-modification.

## External federation references

A supplied presentation describes a separate 13-repository Hellduck federation, including NUN, NUNLauncher, Kloz, CO and SaintSI. These sources were not available through the connected Ivan-VHS GitHub account in this session. They are recorded as research references only; no code has been cloned or merged from them.

## Completion rule

Promote an item to implemented only after code, tests, build integration and evidence are present in DuckOS.
