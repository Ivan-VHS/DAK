# DuckOS 2026 feature and maturity matrix

This matrix consolidates modern OS design directions into concrete work in DuckOS. It describes the current repository implementation rather than treating every trend as a shipped system capability.

| Feature area | Current implementation | Maturity | Remaining work |
|---|---|---|---|
| Unified desktop | Mora launcher, windows, dock, tools and shared design tokens | Implemented at browser-shell level | Native compositor/session integration |
| Material interface | Mora Amber drapery wallpaper, dark radial workspace, walnut/graphite surfaces | Implemented in Mora shell | Contrast and high-DPI acceptance across devices |
| Local AI / agent UX | Rule-based allowlisted intent planner, human-readable plan, explicit approval | Partial | Local model runtime, NPU discovery, signed tools and native approval broker |
| Zero-trust permissions | Deny-by-default preferences and Bubblewrap host wrapper | Partial | Kernel-enforced per-process capabilities, device broker and authenticated audit |
| Application isolation | Fail-closed Bubblewrap wrapper for host-side agent experiments | Partial | Native process isolation and filesystem/network/device policy |
| Atomic system updates | Preference snapshots and local package staging | Planned for OS image updates | Signed metadata, inactive A/B slots, boot health checks and rollback |
| Provenance / integrity | SHA-256 for local files and package payload verification | Partial | Publisher signatures, C2PA parsing, signer trust and transparency |
| Adaptive workspace | Responsive windows and shell preference profiles | Partial | Native multi-monitor migration, display lifecycle and XR |
| Multimodal input | Keyboard, pointer and touch interactions | Partial | Voice, gesture, spatial input and accessibility integration |
| Resource / energy awareness | Mora saver/balanced/performance UI profiles | Partial | CPU/GPU/NPU scheduling, thermal policy, power telemetry and VRR |
| Native boot foundation | Limine x86-64 kernel, boot handoff, framebuffer/serial report, initramfs tooling | Partial | Memory allocators, IDT/APIC, interrupts, scheduler, userspace and VFS |
| Wayland / GPU | wlroots compositor and EGL/GLES shell preview on host Linux | Partial | Input seat/focus, native DRM/KMS and DuckOS GPU drivers |
| Core services | Seven Python user-space services | Implemented at user-space prototype level | Authenticated IPC and adapters to native compositor/input/device stack |
| Live information | Newsroom RSS/Atom service with loopback API and cache | Implemented at user-space level | Native service manager and offline/refresh UX polish |
| Windows compatibility | PE32/PE32+ inspector, per-app Wine prefixes, argv-based Wine launcher | Partial | Proton backend, DXVK/VKD3D setup, audio/input/compositor integration; no kernel anti-cheat |
| App ecosystem | Pytyliki, Reaper, OPlague and VentuSample federation; catalog contracts | Partial | Signed repository metadata, resolver, publisher identity and isolated app installation |

## Safety invariants

- Never execute arbitrary text or a manifest entry point through a shell.
- Inspect untrusted executable formats as data before trying to launch them.
- Require explicit approval for destructive or privileged actions.
- Keep user-space prototypes separate from kernel claims.
- Do not treat a Wine prefix as a security sandbox.
- Do not describe SHA-256 as authorship/signature verification.
- Do not use a boot-test ISO as an installer or flash it onto a physical disk.
- Mark kernel-mode anti-cheat as unsupported instead of implying compatibility or bypass.
