"""Bounded inspection of executable headers used by the DuckOS launcher."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class ExecutableFormatError(ValueError):
    """Raised when an executable cannot be inspected safely."""


_ARCHITECTURES = {
    0x014C: "x86",
    0x8664: "x86_64",
    0x01C0: "arm",
    0x01C4: "armv7",
    0xAA64: "aarch64",
    0xA641: "arm64ec",
    0x0200: "ia64",
    0x5032: "riscv32",
    0x5064: "riscv64",
}


def inspect_executable(path: str | Path) -> dict[str, Any]:
    """Inspect a bounded file header; never maps or executes the inspected image."""
    candidate = Path(path)
    try:
        size = candidate.stat().st_size
        with candidate.open("rb") as stream:
            prefix = stream.read(64)
    except OSError as error:
        raise ExecutableFormatError(f"cannot inspect executable: {error}") from error

    if not candidate.is_file() or candidate.is_symlink():
        raise ExecutableFormatError("executable must be a regular, non-symlink file")
    if size == 0:
        raise ExecutableFormatError("executable is empty")

    suffix = candidate.suffix.lower()
    if suffix == ".com" and size <= 0xFF00 and not prefix.startswith(b"MZ"):
        return {
            "format": "dos-com",
            "architecture": "x86",
            "bits": 16,
            "machine": None,
            "subsystem": None,
            "is_dll": False,
            "size_bytes": size,
        }

    if prefix.startswith(b"MZ"):
        if len(prefix) < 64:
            return {
                "format": "dos-mz",
                "architecture": "x86",
                "bits": 16,
                "machine": None,
                "subsystem": None,
                "is_dll": False,
                "size_bytes": size,
            }

        pe_offset = int.from_bytes(prefix[0x3C:0x40], "little")
        if 64 <= pe_offset <= size - 24:
            try:
                with candidate.open("rb") as stream:
                    stream.seek(pe_offset)
                    header = stream.read(256)
            except OSError as error:
                raise ExecutableFormatError(f"cannot read PE header: {error}") from error

            if header[:4] == b"PE\x00\x00" and len(header) >= 24:
                machine = int.from_bytes(header[4:6], "little")
                characteristics = int.from_bytes(header[22:24], "little")
                optional_size = int.from_bytes(header[20:22], "little")
                optional_magic = (
                    int.from_bytes(header[24:26], "little")
                    if optional_size >= 2 and len(header) >= 26
                    else 0
                )
                subsystem = (
                    int.from_bytes(header[24 + 68:24 + 70], "little")
                    if optional_size >= 70 and len(header) >= 94
                    else None
                )
                bits = 64 if optional_magic == 0x20B else 32 if optional_magic == 0x10B else None
                return {
                    "format": "windows-pe",
                    "architecture": _ARCHITECTURES.get(machine, "unknown"),
                    "bits": bits,
                    "machine": machine,
                    "subsystem": subsystem,
                    "is_dll": bool(characteristics & 0x2000),
                    "size_bytes": size,
                }

            legacy = header[:2]
            if legacy in {b"NE", b"LE", b"LX"}:
                return {
                    "format": "dos-legacy",
                    "architecture": "x86",
                    "bits": None,
                    "machine": None,
                    "subsystem": None,
                    "is_dll": False,
                    "legacy_signature": legacy.decode("ascii"),
                    "size_bytes": size,
                }

        return {
            "format": "dos-mz",
            "architecture": "x86",
            "bits": 16,
            "machine": None,
            "subsystem": None,
            "is_dll": False,
            "size_bytes": size,
        }

    if prefix.startswith(b"\x7fELF") and len(prefix) >= 20:
        elf_class = prefix[4]
        endian = "little" if prefix[5] == 1 else "big"
        machine = int.from_bytes(prefix[18:20], endian)
        architectures = {
            3: "x86",
            40: "arm",
            62: "x86_64",
            183: "aarch64",
            243: "riscv",
        }
        return {
            "format": "elf",
            "architecture": architectures.get(machine, "unknown"),
            "bits": 64 if elf_class == 2 else 32 if elf_class == 1 else None,
            "machine": machine,
            "subsystem": None,
            "is_dll": False,
            "size_bytes": size,
        }

    macho = {
        b"\xFE\xED\xFA\xCE": ("macho", 32, "big"),
        b"\xFE\xED\xFA\xCF": ("macho", 64, "big"),
        b"\xCE\xFA\xED\xFE": ("macho", 32, "little"),
        b"\xCF\xFA\xED\xFE": ("macho", 64, "little"),
        b"\xCA\xFE\xBA\xBE": ("macho-fat", None, "big"),
        b"\xBE\xBA\xFE\xCA": ("macho-fat", None, "little"),
    }
    if prefix[:4] in macho:
        kind, bits, _ = macho[prefix[:4]]
        return {
            "format": kind,
            "architecture": "multi" if kind == "macho-fat" else "unknown",
            "bits": bits,
            "machine": None,
            "subsystem": None,
            "is_dll": False,
            "size_bytes": size,
        }

    raise ExecutableFormatError("file is not a supported PE, DOS, ELF or Mach-O image")


def is_launchable_windows_image(info: dict[str, Any]) -> bool:
    return info.get("format") == "windows-pe" and info.get("is_dll") is False


def is_launchable_dos_image(info: dict[str, Any]) -> bool:
    return info.get("format") in {"dos-mz", "dos-com", "dos-legacy"}
