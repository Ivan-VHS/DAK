# DuckOS Windows Compatibility

**Author / developer:** Ivan-VHS

DuckOS Windows Compatibility is the first userspace compatibility subsystem for running Windows PE applications from DuckOS. It deliberately starts with an inspectable PE front end and an external Wine execution backend instead of pretending that a new kernel can already implement the entire Win32 ABI.

## What is implemented

- Bounded PE32 / PE32+ inspection: DOS and PE signatures, machine type, bitness, subsystem, section table, entry point, relocation presence, and imported DLL names.
- Architecture checks for x86, x86_64, and ARM64 PE headers. The current Wine runner launches x86 and x86_64 applications only.
- Per-application prefix layout under the user's data directory, with a versioned `prefix.toml`, Wine prefix, log directory, and shader-cache/snapshot directories reserved for follow-up services.
- `os-run` CLI for inspection, runtime diagnostics, prefix creation, and launching a PE executable through Wine.
- Argument-safe process startup: arguments are passed directly to `execvp`; no shell is involved.
- Live stdout/stderr forwarding and a persistent session log.
- Utility, retro, and modern profiles. At this stage profiles set a small number of Wine runtime defaults; they are not compatibility fixes for individual games.
- Automated parser tests for valid PE32/PE32+, invalid signatures, and architecture/bitness mismatches.

## Build

Requirements: CMake 3.20+, a C++20 compiler, and a POSIX host for the Wine launch backend.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The `os-run` executable is produced in `build/`.

## Usage

Inspect an executable before trying to run it:

```sh
./build/os-run inspect ./setup.exe
```

Check the available host-side components:

```sh
./build/os-run doctor
```

Create a dedicated 64-bit Wine prefix:

```sh
./build/os-run prefix create my-game --arch win64 --profile modern
```

Launch an application (the prefix is created on first use when needed):

```sh
./build/os-run run ./game.exe --prefix my-game --profile modern -- -windowed
```

The default compatibility data directory is `$XDG_DATA_HOME/duckos/compat`, falling back to `~/.local/share/duckos/compat`. Use `--root PATH` to select another location.

A `win64` Wine prefix is the recommended default for mixed 32/64-bit libraries and applications. Whether 32-bit applications work depends on the installed Wine build and its WoW64/multilib configuration. A `win32` prefix cannot host a 64-bit executable.

## Important limitations

This is a working userspace foundation, **not yet a native PE loader in a DuckOS kernel**. The repository currently has no kernel, process ABI, graphics compositor, audio server, or device-input API to connect to. The current runner therefore requires Wine on a POSIX host.

- DirectX 9/10/11 translation requires a correctly installed DXVK setup. DirectX 12 generally requires VKD3D-Proton. Neither is bundled or installed automatically.
- OpenGL and Vulkan availability is host- and driver-dependent. `os-run doctor` only checks for diagnostic utilities; it does not certify a graphics path.
- Proton is not currently selected as a backend by `os-run`; Steam-managed Proton prefixes and launch options need a dedicated backend adapter.
- Prefixes separate Wine registry and Windows user-space state, but are **not a security sandbox**. Wine can expose host files and applications retain the current user's permissions. Do not run untrusted executables expecting prefix isolation to protect the host.
- Kernel-mode anti-cheat drivers are unsupported by this userspace runner. User-mode anti-cheat compatibility is title-, service-, and configuration-dependent and is not guaranteed.
- Automatic runtime installers (VC++/.NET/DirectX redistributables), launcher-specific profiles, controller remapping, fullscreen recovery, process-tree supervision, save snapshots/rollback, and shader-cache management are not implemented yet.

See [docs/WINDOWS_COMPATIBILITY.md](docs/WINDOWS_COMPATIBILITY.md) for the architecture and implementation status.
