# Mora Hardware & Gaming Performance Suite

**Maintainer:** Ivan-VHS  
**Catalog:** `duckos.hardware-performance-suite.v1`  
**Runtime:** Mora web workspace + local Python hardware agent  
**Maturity:** partial prototype; see the per-platform limits below.

## Purpose

This suite gives Mora one coherent hardware workspace instead of fifteen unrelated utilities. It inventories the machine, captures the installed driver store, finds official driver candidates, checks package evidence, watches firmware and buses, and measures gaming frame pacing.

The suite deliberately separates three layers:

1. **Mora UI** — 15 launchable workspaces, local snapshot import/export, driver metadata review and game-profile preferences.
2. **DuckOS hardware agent** — privileged boundary for operating-system inventory and explicitly requested operations. The agent uses the Python standard library plus native OS facilities.
3. **Existing specialist engines** — OPlague for INF/PE/Authenticode inspection and exact Plug-and-Play matching; Pytyliki for CPU, sensor and benchmark analysis.

A browser tab cannot read arbitrary PCI configuration space, kernel driver objects, BIOS NVRAM, vendor fan controllers or GPU registers. Such data appears only when a native adapter supplies it. Mora labels browser-only estimates and missing evidence instead of fabricating values.

## The fifteen applications

| # | Application | Responsibility | Operation |
|---:|---|---|---|
| 1 | **Device Atlas** | PCI/USB/ACPI inventory, stable hardware IDs, classes and active drivers | Read-only |
| 2 | **Driver Capture** | Export the Windows Driver Store, hash package files and create a manifest | Export-only |
| 3 | **Driver Scout** | Search Windows Update driver offers and create precise hardware-ID catalog searches | Network read |
| 4 | **Driver Lab** | Inspect INF targets, architecture, hardware IDs, package hashes and signer evidence | Read-only |
| 5 | **Driver Graph** | Build exact-ID device-to-driver candidate edges and expose unresolved matches | Read-only |
| 6 | **Driver Restore** | Review captured packages and prepare a controlled restore path | Explicit apply |
| 7 | **Firmware Atlas** | Read BIOS/UEFI, board and firmware versions where the OS exposes them | Read-only |
| 8 | **UEFI Guard** | Report Secure Boot, TPM and boot-mode signals with evidence quality | Read-only |
| 9 | **PCIe Scope** | Inspect PCIe IDs, class, bound driver and available link properties | Read-only |
| 10 | **GPU Deck** | Inventory graphics adapters and supported GPU telemetry | Read-only |
| 11 | **CPU Lab** | CPU topology, exposed clocks/governor and processor counters | Read-only |
| 12 | **Memory Lens** | Physical/available memory, pressure and paging indicators | Read-only |
| 13 | **Storage Pulse** | Disk inventory, health counters when available and I/O measurements | Read-only |
| 14 | **Thermal Core** | Temperatures, exposed power counters, fans and throttling indicators | Read-only |
| 15 | **GameFrame** | Per-game preferences, repeatable frame-time captures and comparisons | Profile-only |

## Current implementation boundary

### Implemented in this change

- Mora opens the 15 specialist workspaces from its main launcher.
- The hardware workspace can import a local `duckos.hardware-snapshot.v1` JSON report and display its device, driver, firmware, CPU, memory, GPU, storage and sensor fields.
- The browser can report its own limited host hints (logical CPU count, optional device-memory estimate, WebGL renderer when exposed, browser storage estimate). These are explicitly marked as browser observations.
- The browser can inspect a user-selected INF as text, produce a local driver-match graph from exact identifiers, generate a Microsoft Update Catalog search for a user-entered ID, and run a short requestAnimationFrame pacing test.
- The native agent captures Windows CIM/PnP/driver metadata and Linux sysfs/procfs/DMI/UEFI/sensor data.
- On Windows, the agent can export installed third-party Driver Store packages and create a SHA-256 manifest.
- On Windows, the agent can enumerate available Microsoft Windows Update driver offers. A single update may be installed only after the user gives its exact update ID, types the confirmation phrase, the current driver store is exported, and Windows accepts a System Restore checkpoint.
- Snapshot and export operations do not install drivers or change firmware.

### Not claimed as implemented

- There is no universal driver binary that works for every device, OS, kernel and architecture.
- Windows Update does not contain every OEM release, and Linux driver availability depends on the distribution, kernel and firmware policy.
- Automatic binary patching of kernel drivers is intentionally excluded: it invalidates publisher signatures and can make the system unbootable or vulnerable.
- BIOS/UEFI/EC/GPU VBIOS flashing is not automated. Firmware flashing needs an exact board revision, vendor image, signature verification, power safeguards and a platform-specific recovery procedure.
- Generic overclocking, voltage changes, arbitrary MSR/PCI configuration writes, disabling security services and blanket background-service shutdown are not safe optimization defaults.
- The browser UI is not an OS service and cannot elevate itself. It exchanges reports through a user-selected local file until a separately packaged, authenticated IPC bridge exists.
- Live ETW/PresentMon, vendor GPU telemetry, fan curves, SMART/NVMe health and per-process priority require native platform adapters and drivers not included in the browser runtime.

## Agent commands

Run from the repository root with Python 3:

```powershell
python agent/duckos_hardware_agent.py snapshot --output hardware-snapshot.json
python agent/duckos_hardware_agent.py export-drivers --output D:\DuckOSDriverBackup
python agent/duckos_hardware_agent.py scan-driver-updates --output driver-offers.json
python agent/duckos_hardware_agent.py install-driver-update --update-id 00000000-0000-0000-0000-000000000000 --backup-dir D:\DuckOSDriverBackup
```

The final command is Windows-only and interactive. Replace the example update ID with one returned by the scanner. It aborts if the update is not found exactly once, if the driver-store export fails, if Windows cannot create the recovery checkpoint, or if the update EULA has not already been accepted by the user in Windows Update Settings. It never silently installs all offered drivers.

On Linux, the snapshot reader uses `/sys`, `/proc`, DMI and EFI variable metadata when readable. It does not run package-manager commands or unload/reload kernel modules. Run with ordinary user privileges first; unavailable metrics remain absent.

## Driver pipeline and evidence rules

1. Enumerate devices and preserve exact Hardware IDs.
2. Discover candidate packages only from Windows Update or an explicitly chosen OEM/vendor source.
3. Inspect INF model sections, architecture decorations, supported OS decorations and exact IDs.
4. Verify package provenance, catalog signature and hashes using OPlague.
5. Compare candidates with installed versions and the active OS build; a matching ID alone is not proof of compatibility.
6. Export the current Driver Store and create a recovery checkpoint.
7. Present the exact package and affected device to the user.
8. Apply only the selected, signed OS-managed update. Keep the result and reboot requirement in the audit log.
9. Re-scan and compare device status, driver version and game benchmarks. Roll back on a verified regression.

No ranking algorithm may promote a package with missing signature or OS evidence to an installable state. Unknown is not pass.

## Gaming optimization policy

GameFrame separates **measurement** from **tuning**. Each run records the same scene, resolution, graphics API, driver version, power state and duration where the native adapter can provide them. It compares median, 95th-percentile and 99th-percentile frame time, not only average FPS.

The default recommendations are reversible and per-game: use the OS Game Mode where appropriate, choose a supported GPU preference for the executable, keep a stable power plan while plugged in, avoid overlays that demonstrably add latency, and compare shader-cache behavior after a driver change. No profile silently changes voltage, clocks, thermal limits, BIOS variables or security settings.

## Snapshot contract

The local report uses `duckos.hardware-snapshot.v1`. Fields are optional when the platform does not expose them. Device and driver counts are bounded; identifiers are not uploaded anywhere. Import is a manual user action and the report remains in the page session.

## Relationship to existing projects

- [OPlague](https://github.com/Ivan-VHS/OPlague) remains the driver-evidence workbench. Its existing exact-ID graph is a candidate generator, not an install verdict; its INF, PE and Authenticode inspectors provide deeper package checks.
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) remains the processor and performance-analysis engine. Its sensor snapshot is read-only and source-labelled.
- [Mora design system](../MORA_DESIGN_SYSTEM.md) remains the shared visual contract.

## Acceptance checks

- Exactly 15 unique app IDs are present in the catalog.
- Linux snapshot tests use temporary sysfs/procfs fixtures and never read or write the host.
- Import rejects an unrelated schema or malformed report.
- Driver export runs only on Windows and invokes `pnputil /export-driver`; it does not install or remove packages.
- Windows Update install requires a unique update ID, an interactive phrase, a completed export and a successful restore checkpoint.
- No firmware-flashing, binary-patching or arbitrary-register-write code is shipped.

