"""Separate Dear PyGui diagnostic utility for DuckOS.

Dear PyGui renders its own GPU-accelerated application window. It is not
embedded into Mora's Qt desktop process and does not modify system tuning.
"""

from __future__ import annotations

import platform
import sys
from typing import Any


def _snapshot() -> dict[str, Any]:
    from ..hardware_inventory import collect_host_inventory

    try:
        inventory = collect_host_inventory()
    except (OSError, RuntimeError, ValueError) as error:
        inventory = {"error": str(error)}
    return {
        "operating_system": platform.platform(),
        "python": sys.version.split()[0],
        "architecture": platform.machine(),
        "hardware_inventory": inventory,
        "execution_policy": "read_only",
        "gpu_overclocking": False,
        "driver_changes": False,
    }


def main() -> int:
    try:
        import dearpygui.dearpygui as dpg
    except ImportError as error:
        raise SystemExit(
            "The GPU diagnostic utility requires the gpu-tools extra. "
            "Install with: python -m pip install 'duckos-build-tools[gpu-tools]'. "
            f"Import details: {error}"
        ) from error

    state: dict[str, Any] = {"snapshot": _snapshot()}

    def refresh() -> None:
        state["snapshot"] = _snapshot()
        dpg.set_value("report", str(state["snapshot"]))

    dpg.create_context()
    with dpg.window(label="DuckOS · GPU diagnostics", width=980, height=680):
        dpg.add_text("Mora GPU tools", color=(255, 212, 0))
        dpg.add_text(
            "Standalone Dear PyGui window · read-only host inventory · no driver tuning"
        )
        dpg.add_button(label="Refresh inventory", callback=refresh)
        dpg.add_separator()
        dpg.add_input_text(
            tag="report",
            default_value=str(state["snapshot"]),
            multiline=True,
            readonly=True,
            width=-1,
            height=-1,
        )

    dpg.create_viewport(
        title="DuckOS GPU diagnostics",
        width=1020,
        height=740,
        min_width=720,
        min_height=480,
    )
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("Dear PyGui Demo", True) if dpg.does_item_exist("Dear PyGui Demo") else None
    dpg.start_dearpygui()
    dpg.destroy_context()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
