"""Bounded, read-only PE32/PE32+ inspection for DuckOS compatibility tooling.

This module parses file metadata only. It does not map executable images into
memory, resolve imports, or execute untrusted code.
"""
from __future__ import annotations

import hashlib
import os
import stat
import struct
from pathlib import Path
from typing import Any

SCHEMA = "duckos.pe-inspection.v1"
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_SECTIONS = 96
MAX_IMPORTS = 4096
MAX_IMPORT_NAME_BYTES = 512

MACHINES = {
    0x014C: ("x86", "x86 · 32-bit"),
    0x8664: ("x86_64", "x86-64 · 64-bit"),
    0xAA64: ("aarch64", "ARM64"),
    0x01C4: ("arm", "ARM · 32-bit"),
}
SUBSYSTEMS = {
    1: "native",
    2: "windows_gui",
    3: "windows_console",
    5: "os2_console",
    7: "posix_console",
    9: "windows_ce_gui",
    10: "efi_application",
    11: "efi_boot_service_driver",
    12: "efi_runtime_driver",
    13: "efi_rom",
    14: "xbox",
    16: "windows_boot_application",
}


class PEFormatError(ValueError):
    """Raised when a PE image is malformed or exceeds inspection limits."""


def _unpack(fmt: str, data: bytes, offset: int, label: str) -> tuple[Any, ...]:
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(data):
        raise PEFormatError(f"{label} extends beyond the file")
    return struct.unpack_from(fmt, data, offset)


def _read_c_string(data: bytes, offset: int, *, limit: int = MAX_IMPORT_NAME_BYTES) -> str:
    if offset < 0 or offset >= len(data):
        raise PEFormatError("import name points outside the file")
    end = data.find(b"\0", offset, min(len(data), offset + limit + 1))
    if end < 0:
        raise PEFormatError("import name is not terminated within the size limit")
    try:
        return data[offset:end].decode("ascii")
    except UnicodeDecodeError as error:
        raise PEFormatError("import name is not valid ASCII") from error


def inspect_pe_bytes(data: bytes, *, file_name: str = "") -> dict[str, Any]:
    """Inspect PE headers and the import DLL table without executing the file."""
    if not isinstance(data, bytes):
        raise TypeError("PE data must be bytes")
    if len(data) > MAX_FILE_BYTES:
        raise PEFormatError(f"file exceeds the {MAX_FILE_BYTES}-byte inspection limit")
    if len(data) < 64 or data[:2] != b"MZ":
        raise PEFormatError("DOS MZ header is missing or incomplete")

    pe_offset, = _unpack("<I", data, 0x3C, "DOS PE offset")
    if pe_offset < 64:
        raise PEFormatError("PE header overlaps the DOS header")
    if data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise PEFormatError("PE signature was not found at e_lfanew")

    machine, section_count, timestamp, _symbol_table, _symbol_count, optional_size, characteristics = _unpack(
        "<HHIIIHH", data, pe_offset + 4, "COFF file header"
    )
    if not 1 <= section_count <= MAX_SECTIONS:
        raise PEFormatError(f"section count must be between 1 and {MAX_SECTIONS}")

    optional_offset = pe_offset + 24
    optional_end = optional_offset + optional_size
    if optional_end > len(data) or optional_size < 2:
        raise PEFormatError("optional header is truncated")
    magic, = _unpack("<H", data, optional_offset, "optional-header magic")
    if magic == 0x10B:
        pe_kind = "PE32"
        directory_count_offset = 92
        directory_table_offset = 96
        image_base, = _unpack("<I", data, optional_offset + 28, "PE32 image base")
    elif magic == 0x20B:
        pe_kind = "PE32+"
        directory_count_offset = 108
        directory_table_offset = 112
        image_base, = _unpack("<Q", data, optional_offset + 24, "PE32+ image base")
    else:
        raise PEFormatError(f"unsupported optional-header magic 0x{magic:04x}")

    if optional_size < directory_count_offset + 4:
        raise PEFormatError("optional header does not contain a data-directory count")
    entry_point, = _unpack("<I", data, optional_offset + 16, "entry point")
    size_of_image, = _unpack("<I", data, optional_offset + 56, "image size")
    size_of_headers, = _unpack("<I", data, optional_offset + 60, "header size")
    subsystem, = _unpack("<H", data, optional_offset + 68, "subsystem")
    dll_characteristics, = _unpack("<H", data, optional_offset + 70, "DLL characteristics")
    directory_count, = _unpack("<I", data, optional_offset + directory_count_offset, "data-directory count")
    available_directories = max(0, (optional_size - directory_table_offset) // 8)
    directory_count = min(directory_count, available_directories, 32)

    section_table = optional_end
    section_table_end = section_table + section_count * 40
    if section_table_end > len(data):
        raise PEFormatError("section table is truncated")

    sections: list[dict[str, int | str]] = []
    for index in range(section_count):
        offset = section_table + index * 40
        raw_name = data[offset:offset + 8].split(b"\0", 1)[0]
        try:
            name = raw_name.decode("ascii")
        except UnicodeDecodeError:
            name = raw_name.hex()
        virtual_size, virtual_address, raw_size, raw_pointer = _unpack(
            "<IIII", data, offset + 8, f"section {index + 1} layout"
        )
        section_flags, = _unpack("<I", data, offset + 36, f"section {index + 1} flags")
        if raw_size and raw_pointer + raw_size > len(data):
            raise PEFormatError(f"section {name!r} raw data extends beyond the file")
        sections.append({
            "name": name,
            "virtual_address": virtual_address,
            "virtual_size": virtual_size,
            "raw_offset": raw_pointer,
            "raw_size": raw_size,
            "characteristics": section_flags,
        })

    # Raw section ranges must be disjoint: overlapping file-backed bytes make
    # RVA-to-file mapping ambiguous and can hide contradictory section content.
    raw_ranges = sorted(
        (int(section["raw_offset"]),
         int(section["raw_offset"]) + int(section["raw_size"]),
         str(section["name"]))
        for section in sections
        if int(section["raw_size"]) > 0
    )
    for previous, current in zip(raw_ranges, raw_ranges[1:]):
        if current[0] < previous[1]:
            raise PEFormatError(
                f"sections {previous[2]!r} and {current[2]!r} have overlapping raw data"
            )

    def rva_to_offset(rva: int, label: str) -> int:
        if rva < 0:
            raise PEFormatError(f"{label} has a negative RVA")
        if rva < size_of_headers and rva < len(data):
            return rva
        for section in sections:
            start = int(section["virtual_address"])
            raw_size = int(section["raw_size"])
            delta = rva - start
            if 0 <= delta < raw_size:
                result = int(section["raw_offset"]) + delta
                if result < len(data):
                    return result
                break
        raise PEFormatError(f"{label} RVA 0x{rva:x} does not map to file-backed data")

    imports: list[str] = []
    import_rva = import_size = 0
    if directory_count > 1:
        import_rva, import_size = _unpack(
            "<II", data, optional_offset + directory_table_offset + 8,
            "import data directory"
        )
    if import_rva or import_size:
        if not import_rva or import_size < 20:
            raise PEFormatError("import directory has an invalid RVA or size")
        descriptor_offset = rva_to_offset(import_rva, "import directory")
        descriptor_limit = min(MAX_IMPORTS, import_size // 20)
        terminated = False
        for index in range(descriptor_limit):
            offset = descriptor_offset + index * 20
            original_thunk, _date, _chain, name_rva, first_thunk = _unpack(
                "<IIIII", data, offset, "import descriptor"
            )
            if not any((original_thunk, name_rva, first_thunk, _date, _chain)):
                terminated = True
                break
            if not name_rva:
                raise PEFormatError("import descriptor has no DLL name RVA")
            name_offset = rva_to_offset(name_rva, "import DLL name")
            name = _read_c_string(data, name_offset).strip()
            if not name or "/" in name or "\\" in name:
                raise PEFormatError("import descriptor contains an invalid DLL name")
            imports.append(name)
        if not terminated:
            raise PEFormatError("import directory has no terminating descriptor within its declared size")

    architecture, architecture_label = MACHINES.get(
        machine, ("unknown", f"Unknown machine (0x{machine:04x})")
    )
    normalized_imports = {
        item.casefold(): item for item in imports
    }
    imports = sorted(normalized_imports.values(), key=str.casefold)
    return {
        "schema": SCHEMA,
        "valid": True,
        "file_name": file_name,
        "format": pe_kind,
        "machine": f"0x{machine:04x}",
        "architecture": architecture,
        "architecture_label": architecture_label,
        "is_dll": bool(characteristics & 0x2000),
        "subsystem": SUBSYSTEMS.get(subsystem, f"unknown_{subsystem}"),
        "entry_point_rva": entry_point,
        "image_base": image_base,
        "size_of_image": size_of_image,
        "size_of_headers": size_of_headers,
        "timestamp": timestamp,
        "aslr_enabled": bool(dll_characteristics & 0x0040),
        "nx_compatible": bool(dll_characteristics & 0x0100),
        "high_entropy_va": bool(dll_characteristics & 0x0020),
        "section_count": section_count,
        "sections": sections,
        "imports": imports,
        "import_count": len(imports),
        "inspection_only": True,
        "memory_mapped": False,
        "execution_performed": False,
    }


def inspect_pe_file(path: str | Path) -> dict[str, Any]:
    """Read a regular file through a bounded descriptor without following symlinks."""
    candidate = Path(path)
    descriptor: int | None = None
    try:
        if candidate.is_symlink():
            raise PEFormatError("input must be a regular file, not a symbolic link")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(candidate, flags)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise PEFormatError("input must be a regular file, not a device, pipe or directory")
        if metadata.st_size > MAX_FILE_BYTES:
            raise PEFormatError(f"file exceeds the {MAX_FILE_BYTES}-byte inspection limit")
        # Bound the read itself as well as the preliminary stat: a file may grow
        # between fstat() and read(), so never trust the original size alone.
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            payload = stream.read(MAX_FILE_BYTES + 1)
        if len(payload) > MAX_FILE_BYTES:
            raise PEFormatError(f"file exceeds the {MAX_FILE_BYTES}-byte inspection limit")
    except FileNotFoundError as error:
        raise PEFormatError("input file does not exist") from error
    except OSError as error:
        raise PEFormatError(f"cannot safely read input file: {error}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)

    report = inspect_pe_bytes(payload, file_name=candidate.name)
    report["file_size_bytes"] = len(payload)
    report["sha256"] = hashlib.sha256(payload).hexdigest()
    return report
