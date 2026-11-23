"""Kavun: deterministic window geometry for the DuckOS session/compositor."""

from __future__ import annotations

import math
from typing import Any

from .common import ServiceError


_LAYOUTS = {"main-stack", "columns", "grid", "floating"}


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ServiceError(f"{label} must be a positive integer")
    return value


def compute_layout(
    width: int,
    height: int,
    windows: list[dict[str, Any]],
    *,
    mode: str = "main-stack",
    gap: int = 12,
    margin: int = 16,
    ratio: float = 0.62,
) -> list[dict[str, Any]]:
    """Return a non-overlapping layout in output-local logical pixels.

    The result is a geometry plan for a compositor adapter; this function does
    not move real Wayland surfaces by itself.
    """
    width = _positive_int(width, "width")
    height = _positive_int(height, "height")
    if mode not in _LAYOUTS:
        raise ServiceError(f"mode must be one of: {', '.join(sorted(_LAYOUTS))}")
    if not isinstance(windows, list) or len(windows) > 16:
        raise ServiceError("windows must be a list containing at most 16 entries")
    if not windows:
        return []
    if not 0.0 < ratio < 1.0:
        raise ServiceError("ratio must be greater than 0 and less than 1")
    if isinstance(gap, bool) or not isinstance(gap, int) or gap < 0:
        raise ServiceError("gap must be a non-negative integer")
    if isinstance(margin, bool) or not isinstance(margin, int) or margin < 0:
        raise ServiceError("margin must be a non-negative integer")

    usable_width = width - margin * 2
    usable_height = height - margin * 2
    if usable_width <= 0 or usable_height <= 0:
        raise ServiceError("margins leave no usable screen area")

    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in windows:
        if not isinstance(item, dict):
            raise ServiceError("each window must be an object")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 128:
            raise ServiceError("every window needs a short, non-empty id")
        if identifier in seen:
            raise ServiceError(f"duplicate window id: {identifier}")
        seen.add(identifier)
        cleaned.append(item)

    rectangles: list[tuple[int, int, int, int]]
    count = len(cleaned)

    if mode == "floating":
        rectangles = []
        offset = max(0, gap)
        for index, item in enumerate(cleaned):
            preferred = item.get("geometry", {})
            if not isinstance(preferred, dict):
                preferred = {}
            x = preferred.get("x", margin + index * 24)
            y = preferred.get("y", margin + index * 24)
            w = preferred.get("width", int(usable_width * 0.72))
            h = preferred.get("height", int(usable_height * 0.72))
            if any(isinstance(value, bool) or not isinstance(value, int) for value in (x, y, w, h)):
                raise ServiceError(f"invalid floating geometry for window {item['id']}")
            w = min(max(160, w), usable_width)
            h = min(max(120, h), usable_height)
            x = min(max(margin, x), width - margin - w)
            y = min(max(margin, y), height - margin - h)
            rectangles.append((x, y, w, h))
        return [_geometry(item, rect) for item, rect in zip(cleaned, rectangles)]

    if mode == "main-stack" and count > 1:
        main_width = int((usable_width - gap) * ratio)
        side_width = usable_width - gap - main_width
        row_height = (usable_height - gap * (count - 2)) // (count - 1)
        rectangles = [(margin, margin, main_width, usable_height)]
        for index in range(count - 1):
            y = margin + index * (row_height + gap)
            h = usable_height - (row_height + gap) * index if index == count - 2 else row_height
            rectangles.append((margin + main_width + gap, y, side_width, h))
    elif mode == "columns":
        column_width = (usable_width - gap * (count - 1)) // count
        rectangles = []
        for index in range(count):
            x = margin + index * (column_width + gap)
            w = usable_width - (column_width + gap) * index if index == count - 1 else column_width
            rectangles.append((x, margin, w, usable_height))
    else:
        columns = math.ceil(math.sqrt(count))
        rows = math.ceil(count / columns)
        cell_width = (usable_width - gap * (columns - 1)) // columns
        cell_height = (usable_height - gap * (rows - 1)) // rows
        rectangles = []
        for index in range(count):
            row, column = divmod(index, columns)
            x = margin + column * (cell_width + gap)
            y = margin + row * (cell_height + gap)
            w = usable_width - (cell_width + gap) * column if column == columns - 1 else cell_width
            h = usable_height - (cell_height + gap) * row if row == rows - 1 else cell_height
            rectangles.append((x, y, w, h))

    return [_geometry(item, rect) for item, rect in zip(cleaned, rectangles)]


def _geometry(item: dict[str, Any], rectangle: tuple[int, int, int, int]) -> dict[str, Any]:
    x, y, width, height = rectangle
    return {
        "id": item["id"],
        "role": item.get("role", "window"),
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }
