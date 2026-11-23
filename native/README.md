# DuckOS native platform

The native tree is an early x86-64 bring-up track. It runs alongside Mora, host user-space services and the C++ Windows compatibility utility.

## Build targets

From the repository root:

```sh
make -C native kernel initramfs test services-test
make -C native compat-test
```

The kernel needs Clang/LLD. The Windows compatibility tool needs CMake 3.20+ and a C++20 compiler. The Wine runner requires a POSIX host and a separately installed Wine build. The Wayland compositor requires wlroots 0.19 and Wayland development headers. ISO staging additionally requires the Limine BIOS/UEFI assets and xorriso.

## Current status

| Subsystem | State | Boundary |
|---|---|---|
| Kernel | Early bring-up | Reports boot information, memory map and framebuffer state, then halts |
| Boot/initramfs | Builder and validator | The kernel does not yet unpack the archive and launch PID 1 |
| Wayland | Compositor/EGL preview | Uses host Linux drivers; input seat and focus remain incomplete |
| Package store | Local staged package prototype | No signed publisher metadata or full OS updater |
| Security | Bubblewrap host wrapper | Not a DuckOS kernel security boundary |
| Core services | Seven Python service prototypes plus Newsroom | User-space only; not kernel modules |
| Windows compatibility | PE inspector and Wine-backed launcher | Not native Win32 execution and not a sandbox |

## Compatibility CLI

The C++20 tool lives under `native/compat`:

```sh
make -C native compat-test
build/compat/os-run doctor
build/compat/os-run inspect ./application.exe
build/compat/os-run prefix create application --arch win64 --profile modern
build/compat/os-run run ./application.exe --prefix application --profile modern
```

The command uses an argv vector and does not invoke a shell. Wine, graphics translation libraries and 32-bit support are external host dependencies. Kernel-mode anti-cheat is unsupported.

## Security and release rules

- No package archive is executed during installation.
- Archive paths are validated; links and device nodes are rejected by the current package/initramfs tools.
- A digest in an unsigned package checks integrity, not publisher identity.
- The Wine prefix separates app configuration but does not restrict host filesystem access.
- The browser desktop's Sentinel settings do not grant or revoke native process permissions.
- The boot-test image is not an installer and must not be written to a physical disk as one.

The kernel still needs memory management, interrupt routing, a scheduler, process/syscall support, VFS, device enumeration/drivers, native graphics and a full session lifecycle before it can be called a daily-driver OS.
