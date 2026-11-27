# DAK Desktop optimization

**Status:** partial native user-space implementation.  
**Author/developer:** Ivan-VHS.

DAK Desktop adds a native maintenance utility to the existing Mora workspace. Mora remains the visual shell; the new Python/Tk window is a host-side utility and is not a compositor, window manager or kernel subsystem.

## Commands

Install DAKOS build tools in a Python 3.10+ environment:

~~~sh
python -m pip install -e .
~~~

Run a read-only diagnostic:

~~~sh
dakos desktop audit
~~~

Open the native maintenance window:

~~~sh
dakos desktop gui
~~~

Inspect the current user's startup entries:

~~~sh
dakos desktop startup list
~~~

Disable and later restore a specific entry using its exact ID from the list:

~~~sh
dakos desktop startup disable folder:example.desktop
dakos desktop startup restore folder:example.desktop
~~~

On Windows, registry IDs use the \`registry:\` prefix; on Linux, user autostart files use \`folder:\`. Quote IDs in shells when they contain spaces or special characters.

## Implemented behavior

- Read-only inventory of Desktop/Рабочий стол files, item count, file type, basic size and common temporary naming patterns.
- A configurable clutter threshold, defaulting to ten visible items.
- Safe, explicitly confirmed movement of selected regular files into \`~/Inbox\`. Existing names are never overwritten; collisions receive a numbered suffix.
- Symbolic links and folders are excluded from the move action.
- Current-user startup folder inventory on Windows and Linux.
- Reversible enable/disable of user startup-folder entries by moving the entry into a DAKOS backup folder.
- On Windows, reversible control of \`HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\` values. Original value and registry type are written to an atomic per-user backup before the value is removed.
- A bounded process/memory snapshot. Linux reads \`/proc\`; Windows uses \`tasklist\` and \`GlobalMemoryStatusEx\`. When \`psutil\` is installed, it supplies richer CPU and process readings.
- Native Tk maintenance window with overview, file organization, startup controls, process view and explicit safety boundaries.

## Safety boundaries

The tool runs with the current user's permissions. It does not request elevation and does not change machine-wide Run keys, system services, drivers, kernel settings, process priority or process lifetime. It does not delete files, clear arbitrary caches, execute startup commands or inspect the contents of personal documents.

A startup disable operation retains a reversible copy of the entry. Restoring refuses to overwrite an entry that already exists. Moving a file to Inbox keeps its contents and chooses another destination name on collision.

The diagnostic is read-only. Moving files and changing startup state are separate operations requiring a direct user action in the GUI or an explicit CLI command.

## Native desktop boundary

This is a native user-space application, not yet a native DAKOS desktop session. The current repository does not have a production compositor, window manager, process manager, syscall ABI, capability broker or bootable distribution. Consequently:

- The utility can inspect the host user's files and selected startup mechanisms.
- It cannot create or switch OS virtual desktops.
- It does not manage arbitrary native application windows or the system tray.
- Resource profiles are observational; it does not change kernel scheduling, CPU/GPU power policy or system services.
- The HTML Mora entry is an informational launch surface. It does not pretend to perform privileged host operations.

The future compositor and shell should consume the same desktop policy while native platform services provide window, workspace, notification and process APIs. That integration must be added only when those services exist and pass their own tests.

## Verification

Python tests cover read-only audit, naming hints, collision-safe movement, path traversal rejection, symlink/folder rejection, reversible startup-folder moves and restore collision handling:

~~~sh
python -m unittest discover -s tests -v
~~~

The Reaper source file \`dakos/ui/desktop.rpr\` records the ten-item threshold and allowed action policy. Its contract tests are in \`contract_tests.rpr\`. Passing a Reaper contract verifies the policy on the Reaper reference runtime; it is not evidence of a booted compositor or kernel enforcement.
