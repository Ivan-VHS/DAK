# Serein — native application manager and command console

## Purpose

Serein is DuckOS's native C++20 application manager. It gives the Mora shell a versioned, local contract for discovering and starting installed desktop applications without turning application manifests into shell commands.

The executable is named **serein**. Running it without arguments opens the interactive Serein Console. The console is a small command interpreter owned by Serein; it is deliberately **not** a general-purpose shell and does not execute arbitrary operating-system commands.

## Build

Requirements: CMake 3.20+ and a C++20 compiler (MSVC, GCC or Clang).

~~~sh
cmake -S . -B build -DBUILD_TESTING=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
~~~

The **serein** executable is produced under the native build directory. Install it with the root CMake install target or place it in a directory on the user's PATH.

## Console commands

| Command | Purpose |
|---|---|
| **serein** | Open the interactive Serein Console |
| **serein apps** | List registered applications |
| **serein register MANIFEST --root DIR** | Validate and register an installed application |
| **serein inspect APP_ID** | Inspect the registered manifest and resolved installation |
| **serein run APP_ID** | Ask for confirmation and start the application detached |
| **serein run APP_ID --foreground** | Start and wait for the application |
| **serein ps** | List live processes launched by Serein |
| **serein stop PID** | Ask for confirmation and stop a tracked process |
| **serein unregister APP_ID** | Remove only the registration record; never delete the app installation |
| **serein help** | Show the command reference |
| **serein version** | Print version and host platform |

For scripted calls, **--confirm** is an explicit confirmation switch. Without it, a terminal session prompts with a yes/no question; a non-interactive invocation is refused. Additional application arguments must follow **--**:

~~~sh
serein run ivan-vhs.reaper-studio -- --safe-mode
~~~

In the interactive console, commands are parsed as words with optional single- or double-quoted arguments. Serein does not implement command chaining, environment expansion, pipes, redirects, substitutions, glob expansion or arbitrary shell execution.

## Register the four Mora applications

Run the commands from a directory where the four repositories have been cloned. Replace the paths with the actual local clone locations:

~~~sh
serein register ../Reaper/integrations/mora/manifest.json --root ../Reaper
serein register ../Pytyliki/integrations/mora/manifest.json --root ../Pytyliki
serein register ../OPlague/integrations/mora/manifest.json --root ../OPlague
serein register ../VentuSample/integrations/mora/manifest.json --root ../VentuSample
~~~

The command asks for explicit confirmation before it stores a registration. Then use **serein apps** to list app IDs and **serein run APP_ID** to launch one. The app must already be installed/built at the entry point described in its manifest. For example, Pytyliki's GUI manifest targets its Windows Release build, and VentuSample's desktop entry points require a Qt desktop build.

The bundled Mora HTML manifest is a static entry point, not a process; Serein does not pretend that opening a static file is a native application process. The seven built-in panels continue to be owned by Mora.

## Manifest validation

Serein currently accepts application manifest schema version **1.0.0**. It checks:

- the JSON structure, duplicate keys, string types and allowed properties;
- the app ID, project identifier, platform list, entry-point map and status values;
- **launch.kind=local_process** and an available host platform;
- **confirmation_required=true** and **shell_interpolation=false**;
- integration policy and **trust_source=operator_installed_project** for external registrations;
- a real installation directory and an existing regular-file entry point;
- the working directory and selected entry point after canonical path resolution.

The manifest is copied into Serein's per-user registry along with the canonical installation root supplied by the operator. Serein re-reads and validates the stored manifest before listing, inspecting or launching the app. Registration records are not installers and do not grant elevated permissions.

### Path confinement

Manifest entry points and working directories must be relative to the explicitly registered installation root. Absolute paths, parent-directory traversal, missing paths, and symlinks that resolve outside that root are rejected. Platform-specific entry points are selected only for the current host platform.

The runtime is not an arbitrary executable field. Serein currently resolves only the allowlisted runtime names **python3**, **python** and **node** from PATH. Native applications omit runtime and are started by their resolved entry-point path. The resolved runtime path is the executable passed to the OS process API.

## Process creation and supervision

Serein does not invoke cmd.exe, PowerShell, sh, bash, system(), popen() or a shell command string.

- **Windows:** uses CreateProcessW with an explicit application path, a correctly quoted argument vector, a working directory and handle inheritance disabled.
- **Linux/macOS:** uses fork() followed by execv(); it never calls /bin/sh -c. Detached children start a new session and have standard input/output/error redirected to /dev/null.
- Runtime arguments, manifest arguments and caller-supplied arguments remain separate argv entries. Serein does not concatenate them into a command string.

Detached launches are recorded in a per-user process ledger. Each record stores the PID, application ID and process start identity. The ps command discards stale records; stop only accepts PIDs already tracked by Serein and checks the process identity to avoid acting on a recycled PID. Windows uses the process creation time; Linux uses the kernel process start time. POSIX stop sends SIGTERM; Windows uses TerminateProcess.

Serein manages the launched top-level process, not every descendant it may create. It is a per-user command-line supervisor, not yet a privileged OS daemon, service manager, compositor or automatic startup service.

## Registry and permissions

Default registry location:

- Windows: %LOCALAPPDATA%\DuckOS\Mora\registry
- Linux/macOS: $XDG_DATA_HOME/duckos/mora/registry, or ~/.local/share/duckos/mora/registry

On POSIX the registry directory is restricted to the current user (0700); manifest, root and process-ledger files are restricted to owner read/write (0600). The process ledger is protected by an exclusive OS file lock for concurrent Serein commands.

Use **serein unregister APP_ID** to remove a registration. The installed project's files are left untouched.

## Mora desktop relationship

Mora exposes Serein in its top status bar as a system utility and displays command examples. A browser page cannot invoke a native executable or control operating-system processes; launch the actual **serein** program from the system terminal. A future native Mora shell can call the same manager through a documented IPC boundary rather than evaluating commands supplied by a web view.

## Maturity and verification

| Capability | Maturity | Verification |
|---|---|---|
| Manifest parser and v1 policy checks | **implemented** | Native contract tests |
| Registration and canonical path confinement | **implemented** | Native contract tests |
| Windows process creation | **partial** | Windows CI build and smoke tests; desktop launch review remains |
| POSIX process creation | **partial** | Linux CI build and smoke tests; live process lifecycle review remains |
| Process ledger, listing and stop | **partial** | Native tests and CI; race/stress review remains |
| Native Mora-to-Serein IPC | **planned** | Not part of the browser shell |

Passing contract tests do not prove that every third-party desktop app works on every host. Runtimes, app builds, permissions and platform-specific dependencies remain the responsibility of each installed project.

## Security notes

Serein runs with the current user's permissions. It does not elevate privileges, bypass platform security, install software, change drivers, or access payment, audio or device services. The operator must install the project, register it from a trusted directory and approve every launch. Manifest validation and path confinement reduce accidental or manifest-driven command execution; they are not a sandbox against a malicious program that the operator explicitly chooses to run.

## Attribution

Project author/developer: Ivan-VHS. Preserve existing contributor credits and third-party notices.