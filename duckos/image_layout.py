"""Dry-run image layout planner. It calculates offsets but never writes disk images."""
from __future__ import annotations

import math
import re
from typing import Any

SCHEMA = "duckos.image-layout.v1"
MAX_PARTITIONS = 64
MAX_IMAGE_BYTES = 64 * 1024 * 1024 * 1024


class LayoutError(ValueError):
    """Raised when a proposed disk image layout is invalid."""


def _positive_int(value: Any, name: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise LayoutError(f"{name} must be an integer from 1 to {maximum}")
    return value


def _align(value: int, alignment: int) -> int:
    return ((value + alignment - 1) // alignment) * alignment


def plan_image(components: list[dict[str, Any]], *, sector_size: int = 512,
               alignment_bytes: int = 1024 * 1024,
               first_usable_byte: int = 1024 * 1024) -> dict[str, Any]:
    if not isinstance(components, list) or not 1 <= len(components) <= MAX_PARTITIONS:
        raise LayoutError(f"image must contain 1..{MAX_PARTITIONS} partitions")
    sector_size = _positive_int(sector_size, "sector_size", 4096)
    alignment_bytes = _positive_int(alignment_bytes, "alignment_bytes", 16 * 1024 * 1024)
    first_usable_byte = _positive_int(first_usable_byte, "first_usable_byte", MAX_IMAGE_BYTES)
    if sector_size not in {512, 1024, 2048, 4096}:
        raise LayoutError("sector_size must be 512, 1024, 2048 or 4096")
    if alignment_bytes % sector_size or alignment_bytes & (alignment_bytes - 1):
        raise LayoutError("alignment_bytes must be a power of two and a multiple of sector_size")
    if first_usable_byte % sector_size:
        raise LayoutError("first_usable_byte must be sector aligned")

    names = set()
    cursor = _align(first_usable_byte, alignment_bytes)
    partitions = []
    for index, component in enumerate(components):
        if not isinstance(component, dict) or set(component) - {"name", "size_bytes", "type"}:
            raise LayoutError("each partition may contain only name, size_bytes and type")
        name = component.get("name")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", name):
            raise LayoutError("partition names must be lowercase identifiers")
        if name in names:
            raise LayoutError(f"duplicate partition name: {name}")
        names.add(name)
        size = _positive_int(component.get("size_bytes"), f"{name}.size_bytes", MAX_IMAGE_BYTES)
        part_type = component.get("type", "data")
        if not isinstance(part_type, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", part_type):
            raise LayoutError(f"{name}.type must be a lowercase identifier")
        start = _align(cursor, alignment_bytes)
        end = start + _align(size, sector_size)
        if end > MAX_IMAGE_BYTES:
            raise LayoutError("planned image exceeds the 64 GiB limit")
        partitions.append({
            "index": index + 1,
            "name": name,
            "type": part_type,
            "start_byte": start,
            "end_byte_exclusive": end,
            "start_sector": start // sector_size,
            "sector_count": (end - start) // sector_size,
            "size_bytes": end - start,
            "alignment_bytes": alignment_bytes,
        })
        cursor = end
    return {
        "schema": SCHEMA,
        "sector_size": sector_size,
        "alignment_bytes": alignment_bytes,
        "image_size_bytes": _align(cursor, alignment_bytes),
        "partitions": partitions,
        "write_performed": False,
        "bootability_verified": False,
    }


def validate_layout(plan: Any) -> bool:
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA:
        raise LayoutError(f"layout must use {SCHEMA}")
    parts = plan.get("partitions")
    if not isinstance(parts, list) or not 1 <= len(parts) <= MAX_PARTITIONS:
        raise LayoutError("layout partitions are malformed")
    previous_end = None
    names = set()
    for part in parts:
        if not isinstance(part, dict):
            raise LayoutError("partition record must be an object")
        name = part.get("name")
        start = part.get("start_byte")
        end = part.get("end_byte_exclusive")
        if name in names or not isinstance(name, str):
            raise LayoutError("partition names must be unique")
        names.add(name)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (start, end)):
            raise LayoutError("partition offsets must be integers")
        if start < 0 or end <= start or (previous_end is not None and start < previous_end):
            raise LayoutError("partition ranges overlap or are reversed")
        previous_end = end
    if previous_end is None or plan.get("image_size_bytes", 0) < previous_end:
        raise LayoutError("image size does not cover all partitions")
    if plan.get("write_performed") is not False:
        raise LayoutError("layout planning must not write an image")
    return True
