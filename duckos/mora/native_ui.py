"""Native Qt entry point for Mora.

Tkinter and browser runtimes are intentionally not used as fallbacks.
"""

from __future__ import annotations


def run_native_mora() -> int:
    try:
        from .qt_ui import run_native_mora as run_qt_desktop
    except ImportError as error:
        raise SystemExit(
            "Mora's native desktop requires PySide6. Install it with: "
            "python -m pip install 'duckos-build-tools[native-ui]'. "
            f"Qt import details: {error}"
        ) from error
    return run_qt_desktop()


def main() -> int:
    return run_native_mora()


if __name__ == "__main__":
    raise SystemExit(main())
