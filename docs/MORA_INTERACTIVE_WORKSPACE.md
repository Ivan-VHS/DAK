# Mora interactive workspace

This implementation extends the existing DuckOS Mora shell instead of replacing its desktop layout.

## Desktop interaction

- The searchable start menu opens from the Mora mark and launches installed-in-shell app panels.
- Three local workspaces are selectable with the numbered pills or `Alt+1`, `Alt+2`, and `Alt+3`.
- Wi-Fi and Sound status buttons open quick controls, the power indicator opens Control, and the clock opens the locale-aware time/date panel. These controls do not switch physical radios or device settings.
- Application windows support pointer dragging, focus/z-order, minimize, maximize/restore and animated close.
- The dock restores minimized windows. Clicking the active dock icon minimizes the matching window.
- The top-right quick panel and notification panel close with Escape or an outside click.
- The application area remains the launcher surface; the right rail adds clearly labelled illustrative CPU, memory and disk bars.

## Duck Files

Duck Files uses `mora/workspace.js` to provide a validated virtual directory tree persisted in the current browser profile. It ships with sample Home, Desktop, Documents, Downloads, Pictures, Applications and System folders.

Supported operations are navigation, Back/Forward/Up, folder creation, small text-file creation/import, text preview, rename, delete, download, search, list/grid view and sorting by name/date/size/type. Sample system entries are read-only. Imported text files are capped at 2 MiB each.

**This is not the host filesystem.** It cannot enumerate or modify Windows/Linux/macOS drives, native DuckOS partitions, protected system files or real application bundles. If browser storage is disabled or full, persistence may be unavailable; the app must report that instead of implying a disk write.

## Terminal

The Mora terminal is a constrained command interpreter for the virtual workspace only. It supports `help`, `ls`, `pwd`, `cd`, `cat`, `mkdir`, `touch`, `rm`, `date`, `whoami`, `neofetch` and `clear`.

It never calls `eval`, `Function`, `child_process`, PowerShell, CMD, Bash or a native process launcher. Unsupported commands are rejected. A real terminal requires a separately permissioned native process service.

## Settings and localization

The interface supports Russian, Ukrainian and English. First launch uses the browser locale with Russian fallback; a saved explicit choice takes precedence. Date/time and item counts use locale-specific formatting and plural rules. The selected language and the application shell preferences are saved in the browser profile.

The DuckOS palette remains fixed: graphite/black surfaces, white copy and Duck yellow `#FFD400`. The quick settings panel contains interface-only indicators for network, Bluetooth, focus and volume. It does not switch physical radios or sound devices.

## Notifications and metrics

Notification read state is saved locally and items can be opened, marked read or cleared. System overview bars are deliberately labelled **DEMO**: they are simulated values, not CPU/RAM/disk telemetry. Actual readings require a trusted native diagnostics service and an explicit data contract.

## Keyboard and accessibility

- `Alt+1..3`: switch workspace.
- `Ctrl+F`: open Duck Files and focus its search field.
- `Ctrl+K`: open Mora AI.
- `Escape`: close the context menu, flyout or topmost visible window.
- Workspace and quick-panel toggles expose `aria-pressed` / `aria-expanded`; window actions have labels; reduced-motion preferences suppress decorative transitions.

## Validation

Run the Mora contract tests with:

```sh
npm test
```

The workspace and localization modules are covered by `tests/mora-workspace.test.mjs` and `tests/mora-i18n.test.mjs`.
