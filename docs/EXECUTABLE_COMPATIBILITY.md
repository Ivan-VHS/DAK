# DuckOS executable compatibility architecture

**Maintainer:** Ivan-VHS  
**Catalog:** duckos.compatibility-targets.v1  
**Current Mora capability:** header inspection in the browser shell  
**Native execution maturity:** not implemented

## Scope

Mora Compatibility Center is the user-facing place to inspect Windows PE, DOS MZ/COM, ELF and Mach-O files, understand possible execution paths, and view capabilities advertised by a future trusted native process manager.

The fifteen operating-system profiles in [the compatibility catalog](../catalogs/compatibility-targets.v1.json) are reference material. They do not mean that DuckOS contains the corresponding kernels, APIs, emulators or compatibility layers.

## Four execution models

1. **Native execution.** The host loader understands the file format and ABI. ReactOS is an example of a Windows-NT-compatible system that can natively load supported PE applications. FreeDOS runs compatible DOS MZ/COM programs, not modern Windows PE files.
2. **API translation.** Wine-like compatibility layers provide Windows API implementations while guest machine instructions execute on a compatible CPU. Graphics translation is a separate component and must be declared by the selected runtime.
3. **Binary translation.** An instruction translator converts code between CPU architectures. It does not, by itself, implement Win32, DirectX, device drivers or Windows services.
4. **Emulation / virtualization.** DOSBox is appropriate for DOS-era programs; a PC emulator or VM can provide a guest machine and, with a separately installed guest OS, a complete Windows environment.

A runtime may combine models. A PE file can require both API compatibility and CPU translation; a game can additionally need DirectX/Vulkan/Metal translation, audio, input, anti-cheat and DRM support.

## Mora browser implementation

The browser module currently reads DOS and PE headers, detects legacy NE/LE/LX, ELF and Mach-O signatures, reports PE machine type/bitness/subsystem, marks a COM file as a candidate based on extension, and shows possible execution routes and reference OS profiles.

It does **not** execute binaries, install runtimes, scan a full file for malware, validate signatures, provide a Windows API, translate instructions, emulate a PC or access arbitrary host paths. Browser file selection is local and this module does not upload the inspected bytes.

## Native bridge contract: duckos.compat.v1

A future native Mora host may expose a trusted object at globalThis.duckos.compatibility:

```js
{
  protocol: "duckos.compat.v1",
  getCapabilities(): Promise<{
    protocol: "duckos.compat.v1",
    host: { os: string, architecture: string },
    runtimes: Array<{
      id: string, name: string, ready: boolean,
      formats?: string[], architectures?: string[],
      executionModel: string
    }>
  }>,
  pickExecutable(): Promise<{
    artifactId: string, name: string, size: number,
    sha256?: string, format: string
  }>,
  launch(request: {
    artifactId: string, runtimeId: string, args: string[]
  }): Promise<{ processId: string, state: string }>
}
```

The current browser UI only calls getCapabilities() to display host and runtime information when the optional bridge is present. It does not call pickExecutable() or launch(). The latter methods describe a future native integration contract.

A future launch UI must pass an opaque artifact identifier and a runtime identifier advertised by the host. It must not pass filesystem paths, shell fragments, executable search paths or a command string. Launch must follow an explicit user action and confirmation.

This bridge is a **contract**, not a currently shipped native service. Do not add a JavaScript shim that pretends to create host processes.

## Requirements for the native process manager

Before a runtime can be advertised as ready, the host must resolve opaque artifact IDs to managed files; validate file type, architecture, manifest, entry point and requested capabilities; reject traversal, device paths and arbitrary host paths; resolve executables and libraries from registered manifests; create processes through native APIs with a structured argument vector; apply permissions and resource limits; isolate untrusted processes; and report stable process IDs and lifecycle events.

A PE header is not a security verdict. Imported files remain untrusted; signature/hash checks, malware scanning and sandbox policy belong to the native security stack.

## Runtime adapters and rollout

| Adapter family | Purpose | Prerequisite |
|---|---|---|
| Native ELF | DuckOS-native applications | DuckOS executable loader and ABI |
| DOSBox / DOSBox-X | DOS MZ/COM and supported DOS extenders | Port, graphics/audio/input integration and managed DOS image |
| Wine-compatible runtime | Windows API translation | Supported host ABI, libraries, CPU and graphics stack |
| CPU translator | Cross-architecture code execution | Verified translator build and supported host/guest pair |
| QEMU / PC virtual machine | Full guest machine and OS | Emulator port, machine model, storage and guest licensing |

Runtime discovery must be data-driven. A missing runtime is shown as unavailable, never as a clickable fake installer. Installation and updates must use the DuckOS package manager after packages have signed manifests.

## Verification status

| Capability | Status |
|---|---|
| Mora compatibility UI | Implemented in browser shell |
| Executable header inspection | Implemented in browser shell |
| Fifteen reference OS profiles | Implemented as versioned data |
| Native bridge | Not implemented |
| Native PE loader | Not implemented |
| Wine / Win32 API runtime | Not integrated |
| DOSBox runtime | Not integrated |
| CPU binary translator | Not integrated |
| QEMU / VM manager | Not integrated |
| DirectX / Vulkan graphics translation | Not integrated |
| Game launch and compatibility testing | Not implemented |

Do not change these statuses without source, build and test evidence from the native DuckOS runtime.