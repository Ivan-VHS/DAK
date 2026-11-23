# DuckOS Extended Terminal

**Author/developer:** Ivan-VHS.  
**Maturity:** partial native user-space CLI implementation.

The Extended Terminal is a separate command environment layered over the existing DuckOS Python toolchain. The base `duckos` CLI remains available unchanged; the extended interface is entered with `duckos terminal`.

## Start

Install the project in a Python 3.10+ environment:

~~~sh
python -m pip install -e .
~~~

Start the interactive terminal:

~~~sh
duckos terminal
~~~

Run one command without entering the interactive session:

~~~sh
duckos terminal run "hardware inventory"
duckos terminal run "desktop audit"
duckos terminal run "bridge runtimes"
duckos terminal run "compat status"
~~~

Commands can also be entered in the interactive prompt. Run `help` for the complete command list or `help bridge plan` for a specific command.

## Command groups

| Group | Commands | Behavior |
|---|---|---|
| General | `help`, `version`, `status`, `doctor` | Help, tool version and terminal diagnostics |
| Hardware | `hardware inventory [SYSFS_ROOT]` | Bounded read-only PCI/USB or Windows PnP inventory |
| Desktop | `desktop audit [ITEM_LIMIT]`, `desktop startup list` | Read-only current-user desktop and startup inspection |
| DuckBridge | `bridge runtimes`, `bridge inspect FILE`, `bridge plan FILE` | Runtime discovery, binary inspection and non-executing launch planning |
| Compatibility | `compat status`, `compat inspect FILE`, `compat diagnose FILE [PREFIX]`, `compat plan FILE [PREFIX]` | Existing PE and prefix diagnostics |
| Modules | `module order FILE` | Deterministic dependency-order calculation from bounded JSON input |
| Local terminal | `alias`, `unalias`, `history`, `config`, `exit` | Local aliases, bounded history and user preferences |

The terminal reuses existing DuckOS service functions. It does not fork alternative implementations of the hardware, desktop, compatibility or module tooling.

## Command and extension contract

Commands are registered as explicit `CommandSpec` entries with a word-based path, help summary, usage string and in-process handler. The registry resolves the longest matching command path and rejects duplicate or malformed registrations.

Trusted in-process DuckOS components may register an extension through `TerminalService.register_command` or the constructor's `extra_commands` argument. Extension handlers receive an argument list and must return JSON-serializable data. There is no directory scanning, implicit import, remote plugin download or automatic execution of third-party extension code.

The parser supports quoted arguments and preserves Windows path separators. It does not implement shell operators, command substitution, environment expansion, pipes, redirection, globbing or script evaluation. A line is dispatched only to a registered DuckOS command or one of the documented local terminal commands.

## Local state

The terminal stores its settings and bounded history in the current user's `~/.config/duckos/terminal` directory:

- `config.json` — prompt, history limit and user-defined aliases.
- `history.json` — recent commands, timestamps and completion state.

The directory is created with owner-only permissions on POSIX systems. Files are updated by writing a temporary file and atomically replacing the previous file. Symlink state files are rejected. History is capped at 10,000 entries and 2 MiB; command text is capped at 4,096 characters and 64 tokens. Secret-bearing options such as `--token`, `--password`, `--secret`, `--api-key` and `--authorization` are redacted in history. Aliases cannot contain those options.

Supported local commands:

~~~text
alias
alias ll desktop audit
alias ll
unalias ll
history
history clear
config show
config set prompt "duck dev"
config set history_limit 250
doctor
exit
~~~

The default history limit is 500. Set it to `0` to disable history recording.

## Security and operational boundaries

- The terminal does not invoke a host shell, `eval`, arbitrary subprocesses or user-supplied executables.
- System-facing built-ins are read-only diagnostics or non-executing plans. They do not install drivers, change startup entries, launch inspected binaries or modify the kernel.
- Local settings and history are the only built-in persistent writes. They are user-scoped and bounded.
- A registered extension is trusted application code. Register only code shipped and reviewed as part of a trusted DuckOS component.
- Errors are returned as command failures; command handlers must validate their own input and preserve the contracts of the underlying subsystem.

This is not yet a native kernel console, privileged recovery shell, PTY multiplexer, remote SSH client, job scheduler or unrestricted POSIX/PowerShell replacement. Those capabilities require separate service contracts, authentication, process isolation and platform-specific enforcement.

## Verification

Run the focused terminal tests:

~~~sh
python -m unittest tests.test_terminal -v
~~~

Run the full Python suite:

~~~sh
python -m unittest discover -s tests -v
~~~

The focused tests cover command dispatch, quoting, alias constraints, state persistence, history redaction, extension registration and CLI wiring. Passing these tests verifies the Python user-space implementation only; it does not establish kernel-console or privileged shell support.
