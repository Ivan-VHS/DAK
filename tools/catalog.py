#!/usr/bin/env python3
"""Generate a paginated view of DuckOS's 87,965 API slots.

Implemented entries are discovered from exported Reaper crafts. The remaining
records are explicitly marked reserved, never presented as working code.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TARGET_COUNT = 87_965
DOMAINS = (
    "kernel", "process", "memory", "scheduler", "filesystem",
    "devices", "drivers", "security", "services", "network",
    "display", "input", "shell", "diagnostics", "package",
    "storage", "power", "users", "permissions", "developer",
)
CRAFT_PATTERN = re.compile(
    r"^\s*export\s+craft\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    re.MULTILINE,
)


def implemented_functions(root: Path) -> list[dict[str, str]]:
    """Read the public Reaper API directly from source declarations."""
    entries: list[dict[str, str]] = []
    for source in sorted((root / "kernel").glob("*.rpr")):
        module = source.stem
        source_text = source.read_text(encoding="utf-8")
        for function_name in CRAFT_PATTERN.findall(source_text):
            entries.append({
                "name": f"{module}.{function_name}",
                "domain": module,
                "language": "Reaper",
                "status": "implemented",
                "source": source.relative_to(root).as_posix(),
            })
    return entries


def catalog_summary(root: Path) -> dict[str, int]:
    implemented_count = len(implemented_functions(root))
    if implemented_count > TARGET_COUNT:
        raise RuntimeError("implemented API count exceeds the catalogue target")
    return {
        "target_count": TARGET_COUNT,
        "implemented_count": implemented_count,
        "reserved_count": TARGET_COUNT - implemented_count,
    }


def catalog_page(root: Path, offset: int = 0, limit: int = 25) -> dict[str, Any]:
    if offset < 0:
        raise ValueError("offset must be zero or greater")
    if limit < 1:
        raise ValueError("limit must be at least one")

    implemented = implemented_functions(root)
    summary = catalog_summary(root)
    page_end = min(TARGET_COUNT, offset + limit)
    items: list[dict[str, Any]] = []

    for index in range(offset, page_end):
        function_id = f"DUCK-{index + 1:05d}"
        if index < len(implemented):
            item: dict[str, Any] = dict(implemented[index])
        else:
            reserved_index = index - len(implemented) + 1
            domain = DOMAINS[(reserved_index - 1) % len(DOMAINS)]
            item = {
                "name": f"{domain}.reserved_{reserved_index:05d}",
                "domain": domain,
                "language": "Reaper",
                "status": "reserved",
                "source": None,
            }
        item["id"] = function_id
        items.append(item)

    return {
        "schema": "duckos.function-registry.v1",
        **summary,
        "offset": offset,
        "returned": len(items),
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offset", type=int, default=0, help="zero-based catalogue offset")
    parser.add_argument("--limit", type=int, default=25, help="number of records to show")
    parser.add_argument("--json", action="store_true", help="print the selected page as JSON")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    page = catalog_page(root, args.offset, args.limit)

    if args.json:
        print(json.dumps(page, ensure_ascii=False, indent=2))
        return 0

    summary = page
    print("DuckOS Function Registry")
    print(f"Target:      {summary['target_count']:,}")
    print(f"Implemented: {summary['implemented_count']:,}")
    print(f"Reserved:    {summary['reserved_count']:,}")
    print(f"Page:        {summary['offset']:,} .. {summary['offset'] + summary['returned'] - 1:,}")
    for item in page["items"]:
        print(f"{item['id']}  {item['status']:<11} {item['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
