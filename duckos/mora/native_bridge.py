"""Small, explicitly scoped native desktop adapters.

The module reports available bridges without loading arbitrary DLLs or
performing privileged actions. Windows window inspection validates handles
and returns metadata only.
"""

from __future__ import annotations

import ctypes
import importlib.util
import os
import platform
from typing import Any


def native_bridge_status() -> dict[str, Any]:
    windows = os.name == "nt"
    return {
        "platform": platform.system(),
        "ctypes": True,
        "pywin32_available": (
            importlib.util.find_spec("win32gui") is not None if windows else False
        ),
        "cffi_available": importlib.util.find_spec("cffi") is not None,
        "pyobjc_available": (
            importlib.util.find_spec("AppKit") is not None
            if platform.system() == "Darwin" else False
        ),
        "window_inspection": "windows_only_read_only" if windows else "not_available",
        "arbitrary_library_loading": False,
        "shell_execution": False,
    }


def inspect_windows_window(handle: int) -> dict[str, Any]:
    """Read a Windows window's title and class; never sends messages or changes it."""
    if os.name != "nt":
        raise OSError("Native window inspection is available only on Windows.")
    if not isinstance(handle, int) or handle <= 0:
        raise ValueError("A positive native window handle is required.")

    try:
        import win32gui
    except ImportError:
        win32gui = None

    if win32gui is not None:
        if not win32gui.IsWindow(handle):
            raise ValueError("The selected window handle is not valid.")
        return {
            "handle": handle,
            "title": win32gui.GetWindowText(handle),
            "class_name": win32gui.GetClassName(handle),
            "read_only": True,
        }

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    is_window = user32.IsWindow
    is_window.argtypes = [ctypes.c_void_p]
    is_window.restype = ctypes.c_int
    if not is_window(ctypes.c_void_p(handle)):
        raise ValueError("The selected window handle is not valid.")

    get_title_length = user32.GetWindowTextLengthW
    get_title_length.argtypes = [ctypes.c_void_p]
    get_title_length.restype = ctypes.c_int
    get_title = user32.GetWindowTextW
    get_title.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    get_title.restype = ctypes.c_int
    get_class = user32.GetClassNameW
    get_class.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    get_class.restype = ctypes.c_int

    hwnd = ctypes.c_void_p(handle)
    title_buffer = ctypes.create_unicode_buffer(min(get_title_length(hwnd) + 1, 2049))
    class_buffer = ctypes.create_unicode_buffer(257)
    get_title(hwnd, title_buffer, len(title_buffer))
    get_class(hwnd, class_buffer, len(class_buffer))
    return {
        "handle": handle,
        "title": title_buffer.value,
        "class_name": class_buffer.value,
        "read_only": True,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(native_bridge_status(), ensure_ascii=False, indent=2))
