# Windows application compatibility in DuckOS

**Owner:** Ivan-VHS  
**Subsystem:** `duckos::compat`  
**Status:** userspace foundation, version 0.1.0

## Design

The compatibility subsystem is split into four boundaries:

1. **PE inspection** (`pe_image`) reads untrusted files as data, validates bounds before every read, and reports architecture and loader-relevant metadata. It does not map executable sections into the DuckOS address space.
2. **Prefix management** (`prefix_manager`) creates one Wine prefix per application, stores its architecture and launch profile in `prefix.toml`, and reserves private log/cache/snapshot locations.
3. **Execution backend** (`runner`) starts Wine with an explicit `WINEPREFIX`. Process arguments are passed as an argv array rather than interpolated into a shell command. The current backend is POSIX-only.
4. **CLI and diagnostics** (`os-run`) expose inspect, doctor, prefix-create, and run operations.

The long-term native integration point is an `ExecutionBackend` interface with Wine/Proton adapters for development hosts and a native Win32 compatibility service for a future DuckOS kernel. That native service requires a process ABI, virtual-memory manager, scheduler, handles, synchronization primitives, filesystem semantics, registry service, and windowing/input APIs; none of those kernel contracts are present in this repository yet.

## Current support matrix

| Area | Current state | Notes |
|---|---|---|
| PE32 / PE32+ inspection | Implemented | Header, section, subsystem, relocation and import metadata |
| x86 / x86_64 identification | Implemented | x86 and x86_64 are accepted by the Wine runner |
| ARM64 identification | Implemented | Inspection only; launch is rejected by the current backend |
| 32/64-bit execution | Delegated to Wine | Depends on Wine WoW64/multilib support and prefix architecture |
| Prefix creation | Implemented | Per-app Wine prefix layout and TOML metadata |
| Win32 API | Delegated to Wine | No native DuckOS Win32 syscall layer exists |
| DirectX 9/10/11 | External dependency | DXVK setup required; not bundled |
| DirectX 12 | External dependency | VKD3D-Proton setup required; not bundled |
| OpenGL / Vulkan | Host-dependent | Driver and Wine configuration required |
| Audio / input / fullscreen | Wine and host-dependent | No DuckOS audio/input bridge exists yet |
| Kernel-mode anti-cheat | Unsupported | Requires Windows-compatible kernel driver semantics |
| User-mode anti-cheat | Untested / title-dependent | No blanket compatibility claim |
| Launch logging | Implemented | Wine output and exit code are written to `logs/session.log` |
| Process-tree cleanup | Not implemented | Wine child processes may outlive the initial launcher |
| Save snapshots / rollback | Not implemented | Snapshot directory is reserved only |
| Shader cache | Not implemented | Cache directory is reserved only |
| Security sandbox | Not implemented | Wine prefix isolation is not a host security boundary |

## Prefix layout

```text
<XDG_DATA_HOME>/duckos/compat/
└── prefixes/
    └── <application-id>/
        ├── prefix.toml
        ├── wine/             # Wine-managed C: drive, registry and user profile
        ├── cache/
        │   └── shaders/      # reserved for a future graphics cache service
        ├── logs/
        │   ├── wineboot.log
        │   └── session.log
        └── snapshots/        # reserved for a future save/config snapshot service
```

Prefix IDs are restricted to letters, digits, `-` and `_`, and the directory tree is created with owner-only permissions on POSIX hosts. This reduces accidental cross-application state sharing; it does not prevent the Windows process from using Wine's host filesystem mappings.

## Launch profiles

- `utility`: quiet Wine diagnostics and conservative synchronization defaults.
- `retro`: verbose Wine errors and esync disabled, which can help isolate timing-sensitive failures but does not emulate historical CPUs or timers.
- `modern`: Wine errors enabled and esync requested for lower synchronization overhead.

Profiles are stored when a prefix is created. Existing prefixes keep their stored profile; `--profile` and `--arch` on `os-run run` only set values for a newly created prefix. Advanced title-specific settings should be represented as explicit per-game overrides once a profile schema is introduced.

## Mapping the 15 design rules to implementation

| Rule | Implementation status |
|---|---|
| Detect format and architecture before launch | PE32/PE32+ parser implemented; installers and script wrappers are not classified yet |
| Isolated per-app prefix | Wine prefix directory and metadata implemented; not a security boundary |
| Versioned runtime dependencies | Not implemented; winetricks/manual runtime provisioning remains external |
| DirectX/OpenGL/Vulkan translation | External DXVK/VKD3D/Wine components; not bundled |
| Unified low-latency audio | Not implemented in DuckOS |
| Keyboard, mouse and controller mapping | Delegated to Wine/host; DuckOS mapping UI not implemented |
| Utility/retro/modern profiles | Initial profile storage and Wine defaults implemented |
| 32/64-bit and timer compatibility | Architecture detection and prefix checks implemented; timer emulation delegated to Wine |
| Safe fullscreen / resolution switching | Delegated to Wine and the host compositor |
| Least privilege and sandboxing | No elevation requested, but no kernel sandbox exists |
| Launcher and anti-cheat reporting | General Wine failure diagnostics only; no per-title anti-cheat database |
| Snapshots and rollback | Not implemented |
| Crash logs and missing-module diagnostics | Wine output and exit code are persisted; structured crash analysis is future work |
| Shader cache | Directory reserved; cache lifecycle not implemented |
| Child process tracking and clean shutdown | Direct Wine process is waited on; process-tree tracking is not implemented |

## Security notes

PE files are treated as untrusted input. The parser caps file size, bounds-checks offsets, limits section count and import traversal, and rejects inconsistent machine/optional-header bitness. The launcher does not invoke a shell. These controls protect the inspector and command construction; they do not make the executed program safe. A future sandbox must be enforced by the OS kernel with namespaces/capabilities or an equivalent isolation model, not by a Wine prefix convention.

## Next engineering milestones

1. Add parser fuzzing and a corpus of real PE samples (including malformed and packed images).
2. Add a prefix schema/version migration path and transactional profile updates.
3. Add a backend interface and a separately tested Proton adapter.
4. Add explicit dependency manifests for VC runtimes, .NET, DXVK and VKD3D, with checksum and rollback support.
5. Integrate native DuckOS window, audio, input, process and filesystem APIs when their contracts exist.
6. Implement kernel-enforced sandboxing and process-tree lifecycle supervision before treating third-party game execution as isolated.
