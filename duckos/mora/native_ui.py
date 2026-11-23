"""Native Mora entry point.

The desktop runtime is PySide6. Tkinter is not used as a fallback.
"""

from __future__ import annotations


def run_native_mora() -> int:
    from .qt_ui import run_native_mora as run_qt_desktop

    return run_qt_desktop()


def main() -> int:
    return run_native_mora()


if __name__ == "__main__":
    raise SystemExit(main())
