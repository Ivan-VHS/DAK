"""Read-only PCI/USB and Windows PnP inventory for DuckOS diagnostics.

The collector never installs, removes, enables, disables or updates a driver.
Device instance identifiers are represented only by per-snapshot keyed hashes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import subprocess
from typing import Any

SCHEMA = "duckos.hardware-inventory.v1"
MAX_DEVICES = 10_000
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
_HEX_ID = re.compile(r"^(?:0x)?[0-9a-f]{4}$", re.IGNORECASE)
_WINDOWS_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$rows = @(Get-PnpDevice -PresentOnly | ForEach-Object {
    $service = $null
    try {
        $property = Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName 'DEVPKEY_Device_Service' -ErrorAction Stop
        if ($property) { $service = [string]$property.Data }
    } catch { }
    [pscustomobject]@{
        Class = [string]$_.Class
        FriendlyName = [string]$_.FriendlyName
        InstanceId = [string]$_.InstanceId
        Status = [string]$_.Status
        Driver = $service
    }
})
ConvertTo-Json -InputObject $rows -Depth 3 -Compress
"""


class HardwareInventoryError(ValueError):
    """Raised when a host device inventory cannot be collected safely."""


def _clean_text(value: Any, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = "".join(char for char in value.strip() if ord(char) >= 32 and ord(char) != 127)
    return cleaned[:limit] or None


def _read_text(path: Path) -> str | None:
    try:
        return _clean_text(path.read_text(encoding="ascii", errors="strict"), 128)
    except (OSError, UnicodeError):
        return None


def _normalise_id(value: str | None) -> str | None:
    if value is None or not _HEX_ID.fullmatch(value):
        return None
    return "0x" + value.removeprefix("0x").removeprefix("0X").lower()


def _driver_name(path: Path) -> str | None:
    try:
        if not path.is_symlink():
            return None
        return _clean_text(Path(os.readlink(path)).name, 128)
    except OSError:
        return None


def _fingerprint(identifier: str, salt: bytes) -> str:
    return hmac.new(salt, identifier.encode("utf-8", errors="replace"), hashlib.sha256).hexdigest()


def _record(
    identifier: str,
    salt: bytes,
    *,
    bus: str,
    vendor_id: str | None,
    device_id: str | None,
    device_class: str | None,
    friendly_name: str | None,
    driver: str | None,
    device_problem: bool = False,
) -> dict[str, Any]:
    if device_problem:
        status = "device_problem"
    elif driver:
        status = "driver_bound"
    else:
        status = "driver_missing"
    return {
        "identity_sha256": _fingerprint(identifier, salt),
        "bus": bus,
        "vendor_id": _normalise_id(vendor_id),
        "device_id": _normalise_id(device_id),
        "device_class": _clean_text(device_class, 128) or "unknown",
        "friendly_name": _clean_text(friendly_name, 256) or f"{bus.upper()} device",
        "driver": _clean_text(driver, 128),
        "status": status,
    }


def _linux_devices(sysfs_root: Path, salt: bytes) -> list[dict[str, Any]]:
    pci_root = sysfs_root / "bus" / "pci" / "devices"
    usb_root = sysfs_root / "bus" / "usb" / "devices"
    if not pci_root.is_dir() and not usb_root.is_dir():
        raise HardwareInventoryError(f"{sysfs_root} does not expose PCI or USB sysfs devices")

    devices: list[dict[str, Any]] = []
    if pci_root.is_dir():
        try:
            entries = sorted(pci_root.iterdir(), key=lambda item: item.name)
        except OSError as error:
            raise HardwareInventoryError(f"cannot enumerate PCI sysfs devices: {error}") from error
        for entry in entries:
            if not entry.is_dir():
                continue
            devices.append(_record(
                entry.name, salt, bus="pci",
                vendor_id=_read_text(entry / "vendor"),
                device_id=_read_text(entry / "device"),
                device_class=_read_text(entry / "class"),
                friendly_name=None,
                driver=_driver_name(entry / "driver"),
            ))
            if len(devices) > MAX_DEVICES:
                raise HardwareInventoryError(f"device inventory exceeds {MAX_DEVICES} entries")

    if usb_root.is_dir():
        try:
            entries = sorted(usb_root.iterdir(), key=lambda item: item.name)
        except OSError as error:
            raise HardwareInventoryError(f"cannot enumerate USB sysfs devices: {error}") from error
        for entry in entries:
            vendor_id = _read_text(entry / "idVendor")
            device_id = _read_text(entry / "idProduct")
            if not entry.is_dir() or not vendor_id or not device_id:
                continue
            drivers = set()
            try:
                interfaces = sorted(entry.parent.iterdir(), key=lambda item: item.name)
            except OSError:
                interfaces = []
            prefix = entry.name + ":"
            for interface in interfaces:
                if interface.name.startswith(prefix):
                    name = _driver_name(interface / "driver")
                    if name:
                        drivers.add(name)
            devices.append(_record(
                entry.name, salt, bus="usb",
                vendor_id=vendor_id,
                device_id=device_id,
                device_class=_read_text(entry / "bDeviceClass"),
                friendly_name=None,
                driver=", ".join(sorted(drivers)) if drivers else None,
            ))
            if len(devices) > MAX_DEVICES:
                raise HardwareInventoryError(f"device inventory exceeds {MAX_DEVICES} entries")
    return devices


def _windows_devices(salt: bytes) -> list[dict[str, Any]]:
    executable = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if not executable:
        raise HardwareInventoryError("PowerShell is required for read-only Windows PnP inventory")
    try:
        completed = subprocess.run(
            [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", _WINDOWS_SCRIPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise HardwareInventoryError(f"Windows PnP inventory failed: {error}") from error
    if completed.returncode != 0:
        detail = _clean_text(completed.stderr, 512) or "PowerShell returned a non-zero exit code"
        raise HardwareInventoryError(detail)
    if len(completed.stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise HardwareInventoryError("Windows PnP output exceeds the 16 MiB limit")
    try:
        payload = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as error:
        raise HardwareInventoryError(f"PowerShell returned invalid PnP JSON: {error}") from error
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list) or len(payload) > MAX_DEVICES:
        raise HardwareInventoryError(f"Windows PnP result must contain at most {MAX_DEVICES} devices")

    devices = []
    for item in payload:
        if not isinstance(item, dict):
            raise HardwareInventoryError("Windows PnP result contains a non-object device")
        instance_id = _clean_text(item.get("InstanceId"), 1024)
        if not instance_id:
            continue
        status_text = _clean_text(item.get("Status"), 64)
        bus = "pci" if instance_id.upper().startswith("PCI\\") else (
            "usb" if instance_id.upper().startswith("USB\\") else "pnp"
        )
        vendor_match = re.search(r"(?:VEN|VID)_([0-9A-F]{4})", instance_id, re.IGNORECASE)
        device_match = re.search(r"(?:DEV|PID)_([0-9A-F]{4})", instance_id, re.IGNORECASE)
        driver = _clean_text(item.get("Driver"), 128)
        devices.append(_record(
            instance_id, salt, bus=bus,
            vendor_id=("0x" + vendor_match.group(1)) if vendor_match else None,
            device_id=("0x" + device_match.group(1)) if device_match else None,
            device_class=_clean_text(item.get("Class"), 128),
            friendly_name=_clean_text(item.get("FriendlyName"), 256),
            driver=driver,
            device_problem=status_text not in {"OK"},
        ))
    return devices


def _snapshot_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def collect_host_inventory(
    *,
    sysfs_root: str | Path | None = None,
    platform_name: str | None = None,
    architecture: str | None = None,
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    """Collect a bounded, read-only inventory for Linux or Windows."""
    system = (platform_name or platform.system()).strip().casefold()
    machine = _clean_text(architecture or platform.machine() or "unknown", 64) or "unknown"
    salt = secrets.token_bytes(32)
    if system == "linux":
        devices = _linux_devices(Path(sysfs_root or "/sys"), salt)
        system_name = "linux"
    elif system == "windows":
        devices = _windows_devices(salt)
        system_name = "windows"
    else:
        raise HardwareInventoryError("supported inventory platforms are Linux and Windows")

    devices.sort(key=lambda item: (
        item["bus"], item["vendor_id"] or "", item["device_id"] or "",
        item["friendly_name"], item["identity_sha256"],
    ))
    counts = {
        status: sum(item["status"] == status for item in devices)
        for status in ("driver_bound", "driver_missing", "device_problem")
    }
    moment = captured_at or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        raise HardwareInventoryError("captured_at must include a timezone")
    captured_utc = moment.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    snapshot: dict[str, Any] = {
        "schema": SCHEMA,
        "captured_utc": captured_utc,
        "source": {
            "provider": "duckos-host-inventory",
            "mode": "read_only",
            "platform": system_name,
            "architecture": machine,
        },
        "summary": {"total_devices": len(devices), **counts},
        "devices": devices,
    }
    snapshot["snapshot_sha256"] = _snapshot_digest(snapshot)
    return snapshot
