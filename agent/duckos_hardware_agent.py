"""DuckOS read-only hardware inventory and guarded Windows driver workflow.

The snapshot path never writes to the host. Driver export copies packages from the
Windows Driver Store. Driver installation is a separate, interactive operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

SNAPSHOT_SCHEMA = "duckos.hardware-snapshot.v1"
CAPTURE_SCHEMA = "duckos.driver-capture.v1"
MAX_DEVICES = 10_000
MAX_DRIVERS = 10_000
MAX_SENSORS = 2_048
MAX_FILES = 20_000
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
POWERSHELL_TIMEOUT = 90

IS_WINDOWS = platform.system() == "Windows"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_text(path: Path, maximum: int = 4096) -> str | None:
    try:
        if path.is_symlink() or not path.is_file():
            return None
        if path.stat().st_size > maximum:
            return None
        value = path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    return value or None


def _read_integer(path: Path) -> int | None:
    value = _read_text(path, 128)
    if value is None:
        return None
    try:
        return int(value, 10)
    except ValueError:
        return None


def _link_name(path: Path) -> str | None:
    try:
        if not path.is_symlink():
            return None
        value = os.readlink(path)
    except OSError:
        return None
    return Path(value).name or None


def _read_secure_boot(sys_root: Path) -> bool | None:
    efi_root = sys_root / "firmware/efi/efivars"
    try:
        candidates = sorted(efi_root.glob("SecureBoot-*"))[:4]
    except OSError:
        return None
    for path in candidates:
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 32:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) >= 5:
            return data[4] == 1
    return None


def _linux_snapshot(sys_root: Path = Path("/sys"), proc_root: Path = Path("/proc")) -> dict[str, Any]:
    """Collect facts exposed by Linux sysfs/procfs. Unreadable values stay absent."""
    report: dict[str, Any] = {
        "schema": SNAPSHOT_SCHEMA,
        "collected_at": _now(),
        "platform": "Linux",
        "host": {
            "os": platform.platform(),
            "release": platform.release(),
            "architecture": platform.machine(),
        },
        "firmware": {},
        "cpu": {},
        "memory": {},
        "devices": [],
        "drivers": [],
        "gpu": [],
        "storage": [],
        "sensors": [],
        "notes": [],
    }

    dmi = sys_root / "class/dmi/id"
    firmware = {
        "vendor": _read_text(dmi / "bios_vendor"),
        "version": _read_text(dmi / "bios_version"),
        "release_date": _read_text(dmi / "bios_date"),
        "board_vendor": _read_text(dmi / "board_vendor"),
        "board_name": _read_text(dmi / "board_name"),
        "system_vendor": _read_text(dmi / "sys_vendor"),
        "system_product": _read_text(dmi / "product_name"),
        "uefi_mode": (sys_root / "firmware/efi").is_dir(),
        "secure_boot": _read_secure_boot(sys_root),
    }
    report["firmware"] = {key: value for key, value in firmware.items() if value is not None}

    cpuinfo = _read_text(proc_root / "cpuinfo", 2 * 1024 * 1024)
    cpu_model = None
    if cpuinfo:
        for line in cpuinfo.splitlines():
            key, separator, value = line.partition(":")
            if separator and key.strip().lower() in {"model name", "hardware", "processor"}:
                cpu_model = value.strip()
                if cpu_model:
                    break
    max_clock_khz = _read_integer(sys_root / "devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
    current_clock_khz = _read_integer(sys_root / "devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    cpu = {
        "name": cpu_model,
        "logical_processors": os.cpu_count(),
        "max_clock_mhz": round(max_clock_khz / 1000, 2) if max_clock_khz is not None else None,
        "current_clock_mhz": round(current_clock_khz / 1000, 2) if current_clock_khz is not None else None,
        "governor": _read_text(sys_root / "devices/system/cpu/cpu0/cpufreq/scaling_governor"),
    }
    report["cpu"] = {key: value for key, value in cpu.items() if value is not None}

    meminfo = _read_text(proc_root / "meminfo", 128 * 1024)
    if meminfo:
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                match = re.search(r"(\d+)\s+kB", line)
                if match:
                    report["memory"]["total_bytes"] = int(match.group(1)) * 1024
            elif line.startswith("MemAvailable:"):
                match = re.search(r"(\d+)\s+kB", line)
                if match:
                    report["memory"]["available_bytes"] = int(match.group(1)) * 1024
            elif line.startswith("SwapTotal:"):
                match = re.search(r"(\d+)\s+kB", line)
                if match:
                    report["memory"]["swap_total_bytes"] = int(match.group(1)) * 1024

    pci_root = sys_root / "bus/pci/devices"
    try:
        pci_paths = sorted(p for p in pci_root.iterdir() if p.is_dir() and not p.is_symlink())[:MAX_DEVICES]
    except OSError:
        pci_paths = []

    for path in pci_paths:
        vendor = (_read_text(path / "vendor", 32) or "").removeprefix("0x").upper()
        device = (_read_text(path / "device", 32) or "").removeprefix("0x").upper()
        class_code = (_read_text(path / "class", 32) or "").removeprefix("0x").upper()
        driver_name = _link_name(path / "driver")
        module_name = _link_name(path / "driver/module")
        hardware_ids = []
        if re.fullmatch(r"[0-9A-F]{4}", vendor) and re.fullmatch(r"[0-9A-F]{4}", device):
            hardware_ids.append("PCI\\VEN_" + vendor + "&DEV_" + device)
        item = {
            "device_id": path.name,
            "name": _read_text(path / "label", 256) or ("PCI device " + path.name),
            "bus": "PCI",
            "class_code": ("0x" + class_code) if class_code else None,
            "vendor_id": vendor or None,
            "device_code": device or None,
            "hardware_ids": hardware_ids,
            "driver": driver_name,
            "driver_module": module_name,
        }
        item = {key: value for key, value in item.items() if value not in (None, [], {})}
        report["devices"].append(item)
        if class_code.startswith("03"):
            report["gpu"].append(item)
        if driver_name:
            report["drivers"].append({
                "device_id": path.name,
                "name": driver_name,
                "module": module_name,
                "source": "Linux sysfs driver binding",
                "evidence": "observed",
            })

    usb_root = sys_root / "bus/usb/devices"
    try:
        usb_paths = sorted(p for p in usb_root.iterdir() if p.is_dir() and not p.is_symlink())[:MAX_DEVICES]
    except OSError:
        usb_paths = []
    for path in usb_paths:
        vendor = (_read_text(path / "idVendor", 32) or "").upper()
        product_id = (_read_text(path / "idProduct", 32) or "").upper()
        if not vendor or not product_id:
            continue
        report["devices"].append({
            "device_id": path.name,
            "name": _read_text(path / "product", 256) or ("USB device " + vendor + ":" + product_id),
            "bus": "USB",
            "vendor_id": vendor,
            "device_code": product_id,
            "hardware_ids": ["USB\\VID_" + vendor + "&PID_" + product_id],
            "manufacturer": _read_text(path / "manufacturer", 256),
        })

    block_root = sys_root / "block"
    try:
        block_paths = sorted(p for p in block_root.iterdir() if p.is_dir() and not p.is_symlink())[:256]
    except OSError:
        block_paths = []
    for path in block_paths:
        sectors = _read_integer(path / "size")
        report["storage"].append({
            "name": _read_text(path / "device/model", 256) or path.name,
            "device": path.name,
            "size_bytes": sectors * 512 if sectors is not None else None,
            "removable": _read_integer(path / "removable") == 1,
            "source": "Linux sysfs",
        })

    thermal_root = sys_root / "class/thermal"
    try:
        zones = sorted(p for p in thermal_root.glob("thermal_zone*") if p.is_dir() and not p.is_symlink())[:MAX_SENSORS]
    except OSError:
        zones = []
    for zone in zones:
        temperature = _read_integer(zone / "temp")
        if temperature is not None:
            report["sensors"].append({
                "name": _read_text(zone / "type", 128) or zone.name,
                "value": round(temperature / 1000, 3),
                "unit": "°C",
                "source": str((zone / "temp").relative_to(sys_root)),
                "quality": "observed",
            })

    hwmon_root = sys_root / "class/hwmon"
    try:
        hwmon_paths = sorted(p for p in hwmon_root.glob("hwmon*") if p.is_dir() and not p.is_symlink())[:64]
    except OSError:
        hwmon_paths = []
    for hwmon in hwmon_paths:
        label = _read_text(hwmon / "name", 128) or hwmon.name
        for input_path in sorted(hwmon.glob("temp*_input"))[:64]:
            value = _read_integer(input_path)
            if value is None:
                continue
            index = input_path.name.removesuffix("_input")
            sensor_label = _read_text(hwmon / (index + "_label"), 128) or index
            report["sensors"].append({
                "name": label + " " + sensor_label,
                "value": round(value / 1000, 3),
                "unit": "°C",
                "source": str(input_path.relative_to(sys_root)),
                "quality": "observed",
            })
            if len(report["sensors"]) >= MAX_SENSORS:
                break

    module_root = sys_root / "module"
    try:
        modules = sorted(p.name for p in module_root.iterdir() if p.is_dir() and not p.is_symlink())[:MAX_DRIVERS]
    except OSError:
        modules = []
    report["kernel_modules"] = modules
    if not report["devices"]:
        report["notes"].append("No PCI or USB devices were readable from this sysfs view.")
    if not report["sensors"]:
        report["notes"].append("No thermal sensors were exposed by sysfs.")
    if report["firmware"].get("secure_boot") is None:
        report["notes"].append("Secure Boot state was not readable; unknown is not the same as disabled.")
    return report


WINDOWS_SNAPSHOT_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$system = Get-CimInstance Win32_ComputerSystem
$bios = Get-CimInstance Win32_BIOS
$cpu = Get-CimInstance Win32_Processor
$memory = @(Get-CimInstance Win32_PhysicalMemory)
$devices = @(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
  Select-Object -First 10000 @{Name='device_id';Expression={$_.PNPDeviceID}},
  @{Name='name';Expression={$_.Name}}, @{Name='class';Expression={$_.PNPClass}},
  @{Name='status';Expression={$_.Status}},
  @{Name='problem_code';Expression={$_.ConfigManagerErrorCode}},
  @{Name='hardware_ids';Expression={$_.HardwareID}},
  @{Name='compatible_ids';Expression={$_.CompatibleID}})
$drivers = @(Get-CimInstance Win32_PnPSignedDriver -ErrorAction SilentlyContinue |
  Select-Object -First 10000 @{Name='device_name';Expression={$_.DeviceName}},
  @{Name='device_id';Expression={$_.DeviceID}},
  @{Name='provider';Expression={$_.DriverProviderName}},
  @{Name='version';Expression={$_.DriverVersion}},
  @{Name='date';Expression={[string]$_.DriverDate}},
  @{Name='inf';Expression={$_.InfName}},
  @{Name='is_signed';Expression={$_.IsSigned}},
  @{Name='signer';Expression={$_.Signer}})
$gpus = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue |
  Select-Object Name,DriverVersion,VideoProcessor,AdapterRAM,PNPDeviceID,Status)
$disks = @(Get-CimInstance Win32_DiskDrive -ErrorAction SilentlyContinue |
  Select-Object Model,InterfaceType,MediaType,Size,Status,PNPDeviceID)
$secureBoot = $null
try { $secureBoot = [bool](Confirm-SecureBootUEFI -ErrorAction Stop) } catch {}
$tpmPresent = $null
try { $tpmPresent = [bool](Get-Tpm -ErrorAction Stop).TpmPresent } catch {}
$payload = [pscustomobject]@{
  schema = 'duckos.hardware-snapshot.v1'
  collected_at = [DateTime]::UtcNow.ToString('o')
  platform = 'Windows'
  host = [pscustomobject]@{
    os = [string]$os.Caption
    release = [string]$os.Version
    build = [string]$os.BuildNumber
    architecture = [string]$os.OSArchitecture
    manufacturer = [string]$system.Manufacturer
    model = [string]$system.Model
  }
  firmware = [pscustomobject]@{
    vendor = [string]$bios.Manufacturer
    version = [string]$bios.SMBIOSBIOSVersion
    release_date = [string]$bios.ReleaseDate
    serial_number_present = [bool]([string]$bios.SerialNumber)
    secure_boot = $secureBoot
    tpm_present = $tpmPresent
  }
  cpu = @($cpu | ForEach-Object {
    [pscustomobject]@{
      name = [string]$_.Name
      cores = [int]$_.NumberOfCores
      logical_processors = [int]$_.NumberOfLogicalProcessors
      max_clock_mhz = [int]$_.MaxClockSpeed
    }
  })
  memory = [pscustomobject]@{
    total_bytes = [int64](($memory | Measure-Object -Property Capacity -Sum).Sum)
    modules = @($memory | ForEach-Object {
      [pscustomobject]@{
        capacity_bytes = [int64]$_.Capacity
        speed_mhz = [int]$_.Speed
        manufacturer = [string]$_.Manufacturer
        part_number = [string]$_.PartNumber
      }
    })
  }
  devices = $devices
  drivers = $drivers
  gpu = $gpus
  storage = $disks
  sensors = @()
  notes = @('Temperature and fan telemetry require a supported vendor or kernel sensor adapter.')
}
$payload | ConvertTo-Json -Depth 8 -Compress
"""


WINDOWS_DRIVER_SCAN_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()
$result = $searcher.Search("IsInstalled=0 and Type='Driver' and IsHidden=0")
$updates = @()
for ($i = 0; $i -lt $result.Updates.Count; $i++) {
  $item = $result.Updates.Item($i)
  $driver = $item.Driver
  $updates += [pscustomobject]@{
    update_id = [string]$item.Identity.UpdateID
    revision = [int]$item.Identity.RevisionNumber
    title = [string]$item.Title
    description = [string]$item.Description
    driver_manufacturer = [string]$driver.Manufacturer
    driver_model = [string]$driver.Model
    driver_class = [string]$driver.DriverClass
    driver_hardware_id = [string]$driver.DriverHardwareID
    reboot_required = [bool]$item.RebootRequired
    max_download_bytes = [int64]$item.MaxDownloadSize
  }
}
[pscustomobject]@{
  schema = 'duckos.windows-update-driver-offers.v1'
  scanned_at = [DateTime]::UtcNow.ToString('o')
  count = $updates.Count
  updates = $updates
} | ConvertTo-Json -Depth 6 -Compress
"""


WINDOWS_CHECKPOINT_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$description = 'DuckOS driver update ' + $env:DUCKOS_UPDATE_ID
Checkpoint-Computer -Description $description -RestorePointType MODIFY_SETTINGS -ErrorAction Stop
[pscustomobject]@{ checkpoint = 'created'; description = $description } | ConvertTo-Json -Compress
"""


WINDOWS_INSTALL_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$target = $env:DUCKOS_UPDATE_ID
$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()
$result = $searcher.Search("IsInstalled=0 and Type='Driver' and IsHidden=0")
$matches = @()
for ($i = 0; $i -lt $result.Updates.Count; $i++) {
  $item = $result.Updates.Item($i)
  if ([string]$item.Identity.UpdateID -eq $target) { $matches += $item }
}
if ($matches.Count -ne 1) { throw 'The exact driver update ID was not found exactly once.' }
$update = $matches[0]
if (-not $update.EulaAccepted) { throw 'The update EULA has not been accepted. Review and accept it through Windows Update Settings, then run this command again.' }
$collection = New-Object -ComObject Microsoft.Update.UpdateColl
[void]$collection.Add($update)
$downloader = $session.CreateUpdateDownloader()
$downloader.Updates = $collection
$download = $downloader.Download()
if ($download.ResultCode -notin @(2,3)) { throw ('Download failed with result code ' + $download.ResultCode) }
$installer = $session.CreateUpdateInstaller()
$installer.Updates = $collection
$install = $installer.Install()
[pscustomobject]@{
  update_id = $target
  title = [string]$update.Title
  result_code = [int]$install.ResultCode
  reboot_required = [bool]$install.RebootRequired
  hresult = [string]$install.HResult
} | ConvertTo-Json -Compress
"""


def _run_powershell(script: str, *, extra_env: Mapping[str, str] | None = None) -> str:
    if not IS_WINDOWS:
        raise RuntimeError("This operation is available only on Windows.")
    executable = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if not executable:
        raise RuntimeError("PowerShell was not found.")
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=POWERSHELL_TIMEOUT,
        env=env,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "PowerShell command failed."
        raise RuntimeError(detail[-4000:])
    return completed.stdout.strip()


def _windows_snapshot() -> dict[str, Any]:
    raw = _run_powershell(WINDOWS_SNAPSHOT_SCRIPT)
    try:
        report = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("PowerShell returned an invalid hardware snapshot.") from error
    if not isinstance(report, dict) or report.get("schema") != SNAPSHOT_SCHEMA:
        raise RuntimeError("PowerShell returned an unexpected snapshot schema.")
    return report


def collect_snapshot(*, sys_root: str | Path = "/sys", proc_root: str | Path = "/proc",
                     system: str | None = None) -> dict[str, Any]:
    """Collect a platform snapshot. No installation or firmware write is performed."""
    target = system or platform.system()
    if target == "Windows":
        return _windows_snapshot()
    if target == "Linux":
        return _linux_snapshot(Path(sys_root), Path(proc_root))
    return {
        "schema": SNAPSHOT_SCHEMA,
        "collected_at": _now(),
        "platform": target,
        "host": {"os": platform.platform(), "release": platform.release(), "architecture": platform.machine()},
        "firmware": {},
        "cpu": {},
        "memory": {},
        "devices": [],
        "drivers": [],
        "gpu": [],
        "storage": [],
        "sensors": [],
        "notes": ["Detailed native inventory is not implemented for this platform yet."],
    }


def _write_json(value: Any, output: Path | None) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if output is None:
        sys.stdout.write(content)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8", newline="\n")


def export_windows_driver_store(destination: str | Path) -> dict[str, Any]:
    """Export installed third-party driver packages; never installs or removes one."""
    if not IS_WINDOWS:
        raise RuntimeError("Driver Store export is available only on Windows.")
    target = Path(destination).expanduser()
    if not target.is_absolute():
        raise ValueError("Use an absolute destination path for a driver backup.")
    target.mkdir(parents=True, exist_ok=True)
    if any(target.iterdir()):
        raise ValueError("The backup destination must be empty; existing files are never overwritten.")
    pnputil = shutil.which("pnputil.exe") or shutil.which("pnputil")
    if not pnputil:
        raise RuntimeError("pnputil was not found.")
    completed = subprocess.run(
        [pnputil, "/export-driver", "*", str(target)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "pnputil export failed."
        raise RuntimeError(detail[-4000:])

    files: list[dict[str, Any]] = []
    total_bytes = 0
    for path in sorted(target.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise RuntimeError("A driver package file exceeds the 2 GiB inspection limit.")
        total_bytes += size
        if len(files) >= MAX_FILES or total_bytes > 32 * 1024 * 1024 * 1024:
            raise RuntimeError("The exported driver store exceeds the inspection limits.")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        files.append({
            "path": path.relative_to(target).as_posix(),
            "size_bytes": size,
            "sha256": digest.hexdigest(),
            "extension": path.suffix.lower(),
        })

    manifest = {
        "schema": CAPTURE_SCHEMA,
        "captured_at": _now(),
        "platform": "Windows",
        "method": "pnputil /export-driver",
        "install_attempted": False,
        "system_modified": False,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "files": files,
    }
    _write_json(manifest, target / "duckos-driver-capture.manifest.json")
    return manifest


def scan_windows_driver_updates() -> dict[str, Any]:
    """List offered driver updates from the configured Windows Update service."""
    raw = _run_powershell(WINDOWS_DRIVER_SCAN_SCRIPT)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("Windows Update returned invalid JSON.") from error
    if not isinstance(result, dict) or result.get("schema") != "duckos.windows-update-driver-offers.v1":
        raise RuntimeError("Windows Update returned an unexpected response.")
    updates = result.get("updates")
    if not isinstance(updates, list):
        raise RuntimeError("Windows Update response has no valid update list.")
    result["updates"] = updates[:MAX_DRIVERS]
    result["count"] = len(result["updates"])
    return result


def install_windows_driver_update(update_id: str, backup_dir: str | Path,
                                  *, input_fn: Callable[[str], str] = input) -> dict[str, Any]:
    """Install one exact Windows Update driver after backup and interactive approval."""
    try:
        target_id = str(uuid.UUID(update_id.strip()))
    except (ValueError, AttributeError) as error:
        raise ValueError("update_id must be a valid Windows Update GUID.") from error

    scan = scan_windows_driver_updates()
    matches = [
        item for item in scan["updates"]
        if isinstance(item, dict) and str(item.get("update_id", "")).lower() == target_id.lower()
    ]
    if len(matches) != 1:
        raise RuntimeError("The exact update ID is not present exactly once in the current Windows Update results.")
    offer = matches[0]
    title = str(offer.get("title") or "Unnamed driver update")
    phrase = "INSTALL " + target_id
    print("Selected driver update: " + title)
    print("A Driver Store backup and Windows System Restore checkpoint are required.")
    if input_fn("Type '" + phrase + "' to continue: ").strip() != phrase:
        raise RuntimeError("Installation cancelled; no driver was installed.")

    backup = export_windows_driver_store(backup_dir)
    _run_powershell(WINDOWS_CHECKPOINT_SCRIPT, extra_env={"DUCKOS_UPDATE_ID": target_id})
    raw = _run_powershell(WINDOWS_INSTALL_SCRIPT, extra_env={"DUCKOS_UPDATE_ID": target_id})
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("Windows Update install returned invalid JSON.") from error
    if not isinstance(result, dict) or result.get("update_id", "").lower() != target_id.lower():
        raise RuntimeError("Windows Update install response did not match the selected update.")
    result["backup_manifest"] = str(Path(backup_dir) / "duckos-driver-capture.manifest.json")
    result["backup_file_count"] = backup["file_count"]
    result["checkpoint_created_before_install"] = True
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DuckOS hardware inventory and guarded driver workflow.")
    commands = parser.add_subparsers(dest="command", required=True)

    snapshot = commands.add_parser("snapshot", help="Collect a read-only hardware snapshot.")
    snapshot.add_argument("--output", type=Path)

    capture = commands.add_parser("export-drivers", help="Export the Windows Driver Store to an empty folder.")
    capture.add_argument("--output", type=Path, required=True)

    scan = commands.add_parser("scan-driver-updates", help="List Windows Update driver offers without installing.")
    scan.add_argument("--output", type=Path)

    install = commands.add_parser("install-driver-update", help="Install one explicitly selected Windows Update driver.")
    install.add_argument("--update-id", required=True)
    install.add_argument("--backup-dir", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            _write_json(collect_snapshot(), args.output)
        elif args.command == "export-drivers":
            _write_json(export_windows_driver_store(args.output), None)
        elif args.command == "scan-driver-updates":
            _write_json(scan_windows_driver_updates(), args.output)
        elif args.command == "install-driver-update":
            _write_json(install_windows_driver_update(args.update_id, args.backup_dir), None)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print("duckos-hardware-agent: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
