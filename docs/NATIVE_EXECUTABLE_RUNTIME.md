# DuckOS native host executable runtime

**Maintainer:** Ivan-VHS  
**Runtime protocol:** `duckos.runtime.v1`  
**Current implementation:** host-side Python process manager  
**Native DuckOS kernel PE/Win32 support:** not implemented

## What is executable now

The optional host service creates real processes on the operating system hosting Mora:

| File/workload | Runtime | What performs the actual execution |
|---|---|---|
| Windows PE on Windows host | `native-pe` | Windows PE loader, Win32/NT subsystem and Windows process-creation API |
| Windows PE on POSIX host | `wine` | Installed Wine runtime and its Win32/NT implementation |
| DOS MZ/COM and supported legacy DOS images | `dosbox` | Installed DOSBox/DOSBox-X PC/DOS emulator |
| Existing Windows/Linux guest disk | `qemu-x86_64` | QEMU full-system virtual machine and the guest OS |

A host-native Windows process is not a process created by the unfinished DuckOS kernel. It receives the current user's Windows permissions. Wine runs on the host CPU architecture; the launcher does not currently supply a separate QEMU user-mode x86 translation layer. QEMU's system emulator can translate guest CPU instructions inside a virtual machine, but it does not implement Win32 for arbitrary host files.

## Install and start the service

From a checkout on the computer that should execute the applications:

```powershell
py -3 -m pip install -e .
duckos runtime list
duckos runtime bridge
```

The bridge binds only to `127.0.0.1` and prints a cryptographically random bearer token. Keep the agent process running and paste the token into Mora → Bridge. The token file is stored in the private DuckOS state directory with restrictive permissions; Mora keeps the token only in the open window's memory.

Serve Mora from an allowed local browser origin in another terminal:

```powershell
py -m http.server 8000
```

Then open `http://localhost:8000/mora/`. The runtime endpoint is `http://127.0.0.1:47682`. The API rejects non-loopback Host headers and non-local browser Origins; it does not expose a remote listen address.

## Import a game or application

Mora can import one `.exe`/`.com` file or a ZIP archive. For a ZIP with more than one executable, supply its relative entry point, e.g. `Game/game.exe`. The app store rejects symlinks, absolute paths, parent traversal, duplicate case-insensitive ZIP paths, encrypted ZIP entries, oversized members and excessive compression ratios.

Each imported file is recorded in a private application directory with a size and SHA-256 digest. The package has an opaque 24-hex application ID. Before launch, the manager checks every listed file, each path component, the package tree hash and the selected executable header again. Imported files remain **untrusted**; a digest protects integrity relative to the local manifest but does not authenticate the publisher or prove that an application is malware-free.

## Launch policy

- The request must carry `approved: true`; Mora shows a separate confirmation dialog.
- Applications are created from an argument array. No shell string, PowerShell, CMD, or shell interpolation is used.
- If bubblewrap is available on Linux, Wine/DOSBox may run in a restricted filesystem view; network namespace isolation is enabled unless network access was separately approved.
- If that sandbox is missing, the runtime requires the explicit `allow_unisolated` choice.
- Windows native PE and QEMU host processes are not AppContainer/bubblewrap isolated in this version and always require explicit unisolated approval.
- Windows direct launch keeps the current user's ordinary filesystem, registry, device and network permissions. The Mora Sentinel preferences do not enforce Windows process permissions.
- QEMU uses a registered disk whose SHA-256 is checked again at launch. Guest disk changes use QEMU snapshot mode by default and the virtual NIC is disabled by default. Persistent disk writes require a separate CLI action.
- Runtime environment, app arguments and imported file data are not treated as trusted metadata.

## Runtime commands

```sh
duckos runtime list
duckos runtime import "/path/to/game.exe" --name "Example Game"
duckos runtime import "/path/to/game.zip" --entrypoint "Game/game.exe"
duckos runtime apps
duckos runtime launch APP_ID --adapter auto --allow-unisolated
duckos runtime processes
duckos runtime stop PROCESS_ID
```

On Windows, `auto` selects the native Windows PE process. On POSIX, `auto` selects Wine for PE and DOSBox for DOS if installed. An unavailable runtime fails with a clear error; DuckOS does not simulate its presence.

Register an existing guest disk and launch a guest OS:

```sh
duckos runtime vm-register win11 /path/to/windows.qcow2 --memory 8192 --cpus 4
duckos runtime vm-launch win11 --allow-unisolated
```

The guest disk must already contain an operating system. Windows guest licensing and activation remain the user's responsibility. The current virtual VGA profile is for compatibility and installation, not a gaming-grade GPU path.

## DirectX and Vulkan

DXVK installation is opt-in. Supply an archive and its expected SHA-256:

```sh
duckos runtime dxvk-install APP_ID dxvk.tar.gz --sha256 YOUR_64_CHARACTER_SHA256
```

The manager validates the archive digest, extracts only the expected 32-bit and 64-bit Direct3D 9/10/11 DLL set, installs those files into the application's managed Wine prefix, and checks their integrity before each launch. DXVK does not implement Direct3D 12. A vkd3d-proton adapter is not integrated. The host must have a Vulkan loader and a working Vulkan device/driver for accelerated DXVK operation; a loader library alone is not proof of GPU compatibility.

No shader-cache optimization, GPU passthrough, anti-cheat compatibility claim or performance guarantee is made. Some games may fail due to DRM, kernel anti-cheat, unsupported APIs, CPU architecture, launchers, codecs or device features.

## Mora API

The authenticated loopback API exposes:

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/capabilities` | GET | Host and installed-runtime discovery |
| `/v1/apps` | GET | Imported application inventory |
| `/v1/apps/import` | POST | Bounded binary import |
| `/v1/launch` | POST | Explicitly approved application process creation |
| `/v1/processes` | GET | Managed process states and host PIDs |
| `/v1/processes/{id}/terminate` | POST | Stop a process created by this manager instance |
| `/v1/vms` | GET | Registered QEMU guest inventory |
| `/v1/vms/{name}/launch` | POST | Approved QEMU guest launch |

Every request requires `Authorization: Bearer <token>`. CORS accepts only loopback browser origins. Imported file bytes are uploaded only to the loopback host agent; they are not sent to a third-party service.

## What this is not

The service is not a DuckOS kernel process manager, PE image loader, Win32/NT subsystem, syscall ABI, native kernel memory mapper, Windows driver loader or enforced app sandbox. The Reaper kernel files currently validate reference contracts; they do not yet boot the hardware or schedule native DuckOS processes.

The following are still native bring-up work: bootable UEFI image; process address spaces; page tables and memory mapping; syscall ABI and context switch; kernel-enforced capabilities; PE loader; native Win32/NT implementation or integrated Wine port; CPU user-mode binary translation; graphics/audio/input compositor; GPU scheduling and passthrough; and game compatibility validation on actual supported hardware.

The host manager is a working compatibility path for the current developer desktop while those OS-level components are built.
