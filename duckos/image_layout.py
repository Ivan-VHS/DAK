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
    image_size = _align(cursor, alignment_bytes)
    if image_size > MAX_IMAGE_BYTES:
        raise LayoutError("aligned image size exceeds the 64 GiB limit")
    return {
        "schema": SCHEMA,
        "sector_size": sector_size,
        "alignment_bytes": alignment_bytes,
        "image_size_bytes": image_size,
        "partitions": partitions,
        "write_performed": False,
        "bootability_verified": False,
    }


def validate_layout(plan: Any) -> bool:
    """Validate every derived field so edited external plans cannot bypass planning rules."""
    top_fields = {
        "schema", "sector_size", "alignment_bytes", "image_size_bytes",
        "partitions", "write_performed", "bootability_verified",
    }
    if not isinstance(plan, dict) or set(plan) != top_fields or plan.get("schema") != SCHEMA:
        raise LayoutError(f"layout must use {SCHEMA} and its exact field set")
    sector_size = plan.get("sector_size")
    alignment = plan.get("alignment_bytes")
    image_size = plan.get("image_size_bytes")
    if isinstance(sector_size, bool) or not isinstance(sector_size, int) or sector_size not in {512, 1024, 2048, 4096}:
        raise LayoutError("layout sector_size is invalid")
    if (isinstance(alignment, bool) or not isinstance(alignment, int)
            or alignment < sector_size or alignment > 16 * 1024 * 1024
            or alignment & (alignment - 1) or alignment % sector_size):
        raise LayoutError("layout alignment_bytes must be a bounded power of two and sector multiple")
    if isinstance(image_size, bool) or not isinstance(image_size, int) or not 1 <= image_size <= MAX_IMAGE_BYTES:
        raise LayoutError("layout image_size_bytes is outside the 64 GiB limit")
    if plan.get("write_performed") is not False or plan.get("bootability_verified") is not False:
        raise LayoutError("layout validation is a dry-run contract and cannot claim writes or verified bootability")

    parts = plan.get("partitions")
    if not isinstance(parts, list) or not 1 <= len(parts) <= MAX_PARTITIONS:
        raise LayoutError("layout partitions are malformed")
    partition_fields = {
        "index", "name", "type", "start_byte", "end_byte_exclusive",
        "start_sector", "sector_count", "size_bytes", "alignment_bytes",
    }
    previous_end = None
    names: set[str] = set()
    for expected_index, part in enumerate(parts, start=1):
        if not isinstance(part, dict) or set(part) != partition_fields:
            raise LayoutError("partition record has missing or unsupported fields")
        name = part.get("name")
        part_type = part.get("type")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", name):
            raise LayoutError("partition names must be lowercase identifiers")
        if name in names:
            raise LayoutError("partition names must be unique")
        names.add(name)
        if not isinstance(part_type, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", part_type):
            raise LayoutError(f"{name}.type must be a lowercase identifier")

        integer_fields = (
            "index", "start_byte", "end_byte_exclusive", "start_sector",
            "sector_count", "size_bytes", "alignment_bytes",
        )
        if any(isinstance(part.get(field), bool) or not isinstance(part.get(field), int)
               for field in integer_fields):
            raise LayoutError(f"{name}: partition offsets and sizes must be integers")
        index = part["index"]
        start = part["start_byte"]
        end = part["end_byte_exclusive"]
        start_sector = part["start_sector"]
        sector_count = part["sector_count"]
        size = part["size_bytes"]
        part_alignment = part["alignment_bytes"]
        if index != expected_index:
            raise LayoutError("partition indices must be contiguous and ordered")
        if part_alignment != alignment:
            raise LayoutError(f"{name}: partition alignment does not match the layout")
        if start < alignment or start % alignment or end <= start or end > MAX_IMAGE_BYTES:
            raise LayoutError(f"{name}: partition range is unaligned or outside image limits")
        if previous_end is not None and start < previous_end:
            raise LayoutError("partition ranges overlap or are reversed")
        if (end - start) != size or size <= 0 or size % sector_size:
            raise LayoutError(f"{name}: partition size does not match its aligned byte range")
        if start % sector_size or start_sector != start // sector_size:
            raise LayoutError(f"{name}: start sector does not match its byte offset")
        if sector_count != size // sector_size:
            raise LayoutError(f"{name}: sector_count does not match its byte size")
        previous_end = end

    if previous_end is None:
        raise LayoutError("layout contains no partition ranges")
    expected_image_size = _align(previous_end, alignment)
    if expected_image_size > MAX_IMAGE_BYTES or image_size != expected_image_size:
        raise LayoutError("image_size_bytes must equal the aligned end of the final partition")
    return True
