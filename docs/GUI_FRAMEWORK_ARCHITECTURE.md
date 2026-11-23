# Mora GUI and native runtime architecture

**Primary desktop runtime:** PySide6 / Qt 6 Widgets  
**Terminal runtime:** Textual + Rich (optional extra)  
**GPU utility runtime:** Dear PyGui (separate optional process)  
**Qt plotting:** PyQtGraph (optional extra)  
**Native bridge:** Python standard-library `ctypes`, with platform-scoped PyWin32 / PyObjC / CFFI adapters  
**HTML / WebView:** forbidden in Mora

## Why one primary toolkit

The 66-item review is recorded in [gui-toolkits.json](../duckos/mora/data/gui-toolkits.json). It is a compatibility and architecture registry, not a list of 66 runtime dependencies.

Mora uses one primary widget system: **PySide6 with Qt Widgets**. This provides a single event loop, signal/slot model, accessibility surface, native file dialogs, keyboard focus model, layout engine and cross-platform window backend. PyQt6, wxPython, Kivy, Toga, GTK, FLTK and IUP remain alternative desktop stacks; mixing them into one window tree would add incompatible event loops, styles and native dependencies.

Qt Quick / QML is reserved for separate declarative scenes where it provides a concrete benefit. It is not required by the desktop launcher. Qt's official Python bindings are PySide6; the package is available under LGPLv3/GPLv3 or commercial licensing, so distribution must retain the selected Qt license notices and meet the relevant LGPL obligations. See the [Qt for Python project](https://doc.qt.io/qtforpython-6/) and [commercial use guidance](https://doc.qt.io/qtforpython-6/commercial/index.html).

## Runtime layers

| Layer | Selected implementation | Scope |
|---|---|---|
| Main desktop | PySide6 Qt Widgets | Mora launcher, app windows, system panels, dialogs, accessibility and input |
| Declarative scenes | Qt Quick / QML, optional (`duckos mora scene`) | Standalone animated native scene; no HTML canvas |
| Charts | PyQtGraph, optional | Native Qt plots and numeric visualizations |
| GPU diagnostics | Dear PyGui, separate process | GPU-accelerated engineering/diagnostic utility; not the desktop shell |
| TUI | Textual, optional | Terminal-based recovery and remote administration |
| Terminal rendering | Rich, optional | Tables, logs, progress and structured output |
| Interactive command input | Prompt Toolkit, optional | Completion and multiline terminal interaction |
| Windows bridge | ctypes + optional PyWin32 | Read-only HWND title/class inspection behind a platform adapter |
| Native ABI plugins | CFFI, optional | Availability detection and foundation for explicitly registered compiled adapters; arbitrary library loading is disabled |

PyObjC is currently detected as an optional AppKit bridge on macOS; app enumeration/window control is not yet exposed by Mora. CFFI is an optional ABI foundation, not an arbitrary dynamic loader.

The CPU/GPU rendering frameworks (Pygame, Arcade, Panda3D, Ursina, Pyglet, ModernGL, Vispy and Manim) are application or scene engines. They do not replace the desktop window manager or Qt controls.

Web-first stacks (PyWebView, Eel, NiceGUI, Streamlit, Dash, Reflex, Gradio, Solara, Remi, JustPy, HTML-backed FastAPI/Flask frontends, cefpython and Tauri/Electron frontends) are excluded from the Mora system shell. A local API may exist as a separate service only when it has a documented native client and does not introduce browser rendering into Mora.

Tkinter wrappers and themes are retired because the primary shell no longer uses Tk. Qt equivalents provide drag/drop, date controls, menus, tooltips and dialogs without maintaining a second widget family.

## Dependency profiles

- `native-ui`: PySide6 for the primary desktop.
- `plots`: PyQtGraph for optional numeric plotting.
- `gpu-tools`: Dear PyGui in a separate diagnostic process.
- `terminal-ui`: Textual, Rich and Prompt Toolkit for terminal surfaces.
- `windows-native`: PyWin32 on Windows only.
- `native-ffi`: CFFI for explicitly built native ABI adapters.
- `macos-native`: PyObjC/AppKit adapter on macOS only.
- `native-ui` also provides a standalone Qt Quick scene preview through `duckos mora scene`.

Do not install every alternative framework. The base install remains lightweight; desktop, charts, GPU and TUI capabilities are installed only when requested. The app launcher does not import optional modules until their command or feature is selected.

## Licensing and trust boundaries

PySide6 Community Edition is distributed under LGPLv3/GPLv3 terms, or under a Qt commercial license. Review the selected distribution model before shipping binaries. Qt Graphs includes GPLv3-only modules in the open-source Qt distribution; Mora therefore prefers the separately packaged PyQtGraph adapter for optional plots. See [Qt licensing](https://doc.qt.io/qt-6/licensing.html).

Python `ctypes` can execute native code and bypass Python memory safety. It is reserved for reviewed declarations with fixed signatures, validated handles and platform guards. PyWin32/CFFI/PyObjC adapters must not expose arbitrary library loading, raw shell invocation or generic privileged calls to UI code.

## Maturity

A framework marked `supported-extra` is an optional integration surface, not proof that it is installed on a target system. A catalogue item marked `alternative`, `domain-tool`, `forbidden` or `unverified` must not be described as part of the shipped Mora runtime.
