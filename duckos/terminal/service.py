"""Interactive, non-shell terminal for trusted DuckOS commands."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import os
from pathlib import Path
import platform
import re
import shlex
import tempfile
from typing import Any, Callable, Iterable

from ..compat import compatibility_status, diagnose_binary, inspect_pe_file, plan_launch
from ..compat.bridge import (
    build_launch_plan,
    detect_runtimes,
    inspect_binary,
)
from ..desktop import DesktopService, audit_desktop
from ..hardware_inventory import collect_host_inventory
from ..module_abi import resolve_load_order


CONFIG_SCHEMA = "duckos.terminal-config.v1"
RESULT_SCHEMA = "duckos.terminal-result.v1"
MAX_COMMAND_LENGTH = 4096
MAX_ARGUMENTS = 64
MAX_CONFIG_BYTES = 64 * 1024
MAX_HISTORY_BYTES = 2 * 1024 * 1024
MAX_HISTORY_ENTRIES = 10_000
MAX_INPUT_JSON_BYTES = 4 * 1024 * 1024
_ALIAS_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_SECRET_OPTIONS = {"--token", "--password", "--secret", "--api-key", "--authorization"}


class TerminalInputError(ValueError):
    """Raised when terminal input or its local configuration is invalid."""


@dataclass(frozen=True)
class CommandSpec:
    """One trusted command exposed through the DuckOS terminal registry."""

    path: tuple[str, ...]
    summary: str
    usage: str
    handler: Callable[[list[str]], Any]


class CommandRegistry:
    """Longest-prefix command registry with explicit, duplicate-safe registration."""

    def __init__(self) -> None:
        self._commands: dict[tuple[str, ...], CommandSpec] = {}

    def register(self, command: CommandSpec) -> None:
        if not command.path or len(command.path) > 3:
            raise ValueError("command paths must contain between one and three words")
        if any(not re.fullmatch(r"[a-z][a-z0-9-]*", part) for part in command.path):
            raise ValueError("command names must use lowercase ASCII letters, digits and hyphens")
        if command.path in self._commands:
            raise ValueError("command is already registered: " + " ".join(command.path))
        self._commands[command.path] = command

    def resolve(self, tokens: list[str]) -> tuple[CommandSpec, list[str]] | None:
        for size in range(min(3, len(tokens)), 0, -1):
            spec = self._commands.get(tuple(tokens[:size]))
            if spec is not None:
                return spec, tokens[size:]
        return None

    def commands(self) -> list[CommandSpec]:
        return sorted(self._commands.values(), key=lambda item: item.path)

    def roots(self) -> set[str]:
        return {path[0] for path in self._commands}


def _tokenize(line: str) -> list[str]:
    if not isinstance(line, str):
        raise TerminalInputError("command must be text")
    if len(line) > MAX_COMMAND_LENGTH:
        raise TerminalInputError("command exceeds the 4096-character limit")
    if any(ord(char) < 32 and char not in "\t" for char in line) or "\x7f" in line:
        raise TerminalInputError("command contains unsupported control characters")
    lexer = shlex.shlex(line, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.escape = ""
    try:
        tokens = list(lexer)
    except ValueError as error:
        raise TerminalInputError("invalid quoting: " + str(error)) from error
    if len(tokens) > MAX_ARGUMENTS:
        raise TerminalInputError("command exceeds the 64-token limit")
    return tokens


def _redact_history(tokens: list[str]) -> str:
    safe: list[str] = []
    hide_next = False
    for token in tokens:
        if hide_next:
            safe.append("[redacted]")
            hide_next = False
            continue
        lower = token.casefold()
        if lower in _SECRET_OPTIONS:
            safe.append(token)
            hide_next = True
        elif any(lower.startswith(option + "=") for option in _SECRET_OPTIONS):
            safe.append(token.split("=", 1)[0] + "=[redacted]")
        else:
            safe.append(token)
    return " ".join(shlex.quote(token) for token in safe)


class TerminalService:
    """Dispatch allowlisted commands without invoking a host shell."""

    def __init__(
        self,
        state_dir: str | Path | None = None,
        extra_commands: Iterable[CommandSpec] = (),
    ) -> None:
        self.state_dir = Path(state_dir) if state_dir is not None else (
            Path.home() / ".config" / "duckos" / "terminal"
        )
        self.config_path = self.state_dir / "config.json"
        self.history_path = self.state_dir / "history.json"
        self.config = self._load_config()
        self.registry = CommandRegistry()
        self._register_builtin_commands()
        for command in extra_commands:
            self.registry.register(command)
        self._reserved_aliases = self.registry.roots() | {
            "alias", "unalias", "history", "config", "doctor", "exit", "quit"
        }
        for name in self.config["aliases"]:
            if name in self._reserved_aliases:
                raise TerminalInputError("terminal config contains a reserved alias: " + name)
            expanded = self._expand_alias([name])
            if self.registry.resolve(expanded) is None:
                raise TerminalInputError("terminal alias does not resolve to a registered command: " + name)

    @property
    def prompt(self) -> str:
        return str(self.config["prompt"])

    def register_command(self, command: CommandSpec) -> None:
        """Register a command from a trusted in-process DuckOS extension."""
        self.registry.register(command)
        self._reserved_aliases.add(command.path[0])

    def _ensure_state_dir(self) -> None:
        if self.state_dir.is_symlink():
            raise TerminalInputError("terminal state directory must not be a symlink")
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.state_dir.is_symlink() or not self.state_dir.is_dir():
            raise TerminalInputError("terminal state path is not a regular directory")
        if os.name == "posix":
            try:
                self.state_dir.chmod(0o700)
            except OSError:
                pass

    def _read_json(self, path: Path, max_bytes: int, default: Any) -> Any:
        if path.is_symlink():
            raise TerminalInputError("terminal state files must not be symlinks: " + path.name)
        try:
            size = path.stat().st_size
            if size > max_bytes:
                raise TerminalInputError(path.name + " exceeds its size limit")
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default
        except json.JSONDecodeError as error:
            raise TerminalInputError("invalid JSON in " + path.name + ": " + str(error)) from error
        except OSError as error:
            raise TerminalInputError("cannot read " + path.name + ": " + str(error)) from error

    def _atomic_write(self, path: Path, payload: str) -> None:
        self._ensure_state_dir()
        if path.is_symlink():
            raise TerminalInputError("refusing to replace a symlink: " + path.name)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix="." + path.name + ".",
                suffix=".tmp",
                dir=self.state_dir,
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            if os.name == "posix":
                temporary_path.chmod(0o600)
            os.replace(temporary_path, path)
        except OSError as error:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise TerminalInputError("cannot update " + path.name + ": " + str(error)) from error

    def _load_config(self) -> dict[str, Any]:
        default = {
            "schema": CONFIG_SCHEMA,
            "prompt": "duckos",
            "history_limit": 500,
            "aliases": {},
        }
        payload = self._read_json(self.config_path, MAX_CONFIG_BYTES, default)
        if not isinstance(payload, dict) or payload.get("schema") != CONFIG_SCHEMA:
            raise TerminalInputError("terminal config has an unsupported schema")
        if set(payload) != set(default):
            raise TerminalInputError("terminal config contains missing or unknown fields")
        prompt = payload.get("prompt")
        limit = payload.get("history_limit")
        aliases = payload.get("aliases")
        if (
            not isinstance(prompt, str)
            or not prompt
            or len(prompt) > 40
            or any(ord(char) < 32 or ord(char) == 127 for char in prompt)
        ):
            raise TerminalInputError("terminal prompt must be 1-40 printable characters")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 0 <= limit <= MAX_HISTORY_ENTRIES:
            raise TerminalInputError("history_limit must be between 0 and 10000")
        if not isinstance(aliases, dict) or len(aliases) > 128:
            raise TerminalInputError("aliases must be an object with at most 128 entries")
        for name, target in aliases.items():
            if not isinstance(name, str) or not _ALIAS_NAME.fullmatch(name):
                raise TerminalInputError("terminal config contains an invalid alias name")
            if name in {
                "help", "version", "status", "hardware", "desktop", "bridge",
                "compat", "module", "alias", "unalias", "history", "config",
                "doctor", "exit", "quit",
            }:
                raise TerminalInputError("terminal config contains a reserved alias")
            if (
                not isinstance(target, list)
                or not target
                or len(target) > MAX_ARGUMENTS
                or any(
                    not isinstance(item, str)
                    or not item
                    or len(item) > 1024
                    or any(ord(char) < 32 or ord(char) == 127 for char in item)
                    for item in target
                )
                or any(
                    item.casefold() in _SECRET_OPTIONS
                    or any(item.casefold().startswith(flag + "=") for flag in _SECRET_OPTIONS)
                    for item in target
                )
            ):
                raise TerminalInputError("terminal config contains an invalid alias target")
        return {"schema": CONFIG_SCHEMA, "prompt": prompt, "history_limit": limit, "aliases": aliases}

    def _save_config(self) -> None:
        encoded = json.dumps(
            self.config, ensure_ascii=False, indent=2, allow_nan=False
        ) + "\n"
        if len(encoded.encode("utf-8")) > MAX_CONFIG_BYTES:
            raise TerminalInputError("terminal config exceeds its size limit")
        self._atomic_write(self.config_path, encoded)

    def _read_history(self) -> list[dict[str, Any]]:
        payload = self._read_json(self.history_path, MAX_HISTORY_BYTES, [])
        if not isinstance(payload, list):
            raise TerminalInputError("terminal history must be a JSON array")
        entries = []
        for item in payload[-MAX_HISTORY_ENTRIES:]:
            if (
                isinstance(item, dict)
                and isinstance(item.get("timestamp"), str)
                and isinstance(item.get("command"), str)
                and isinstance(item.get("result"), str)
            ):
                entries.append(item)
        return entries[-self.config["history_limit"]:] if self.config["history_limit"] else []

    def _write_history(self, entries: list[dict[str, Any]]) -> None:
        if not self.config["history_limit"]:
            return
        bounded = entries[-self.config["history_limit"]:]
        encoded = json.dumps(bounded, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if len(encoded.encode("utf-8")) > MAX_HISTORY_BYTES:
            raise TerminalInputError("terminal history exceeds its size limit")
        self._atomic_write(self.history_path, encoded)

    def _record_history(self, tokens: list[str], result: str) -> None:
        if not self.config["history_limit"]:
            return
        entries = self._read_history()
        entries.append({
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "command": _redact_history(tokens),
            "result": result,
        })
        self._write_history(entries)

    def _expand_alias(self, tokens: list[str]) -> list[str]:
        expanded = list(tokens)
        seen: set[str] = set()
        for _ in range(8):
            if not expanded or expanded[0] not in self.config["aliases"]:
                return expanded
            name = expanded[0]
            if name in seen:
                raise TerminalInputError("alias cycle detected at " + name)
            seen.add(name)
            expanded = list(self.config["aliases"][name]) + expanded[1:]
            if len(expanded) > MAX_ARGUMENTS:
                raise TerminalInputError("alias expansion exceeds the 64-token limit")
        if expanded and expanded[0] in self.config["aliases"]:
            raise TerminalInputError("alias expansion exceeds eight levels")
        return expanded

    def completion_candidates(self, prefix: str, current_word: str = "") -> list[str]:
        """Return safe next-word suggestions for a readline-style completer."""
        try:
            parent = _tokenize(prefix)
        except TerminalInputError:
            return []
        candidates: set[str] = set()
        if not parent:
            candidates.update(self.registry.roots())
            candidates.update({
                "alias", "unalias", "history", "config", "doctor", "exit", "quit"
            })
            candidates.update(self.config["aliases"])
        else:
            parent_path = tuple(parent)
            for command in self.registry.commands():
                if len(command.path) > len(parent_path) and command.path[:len(parent_path)] == parent_path:
                    candidates.add(command.path[len(parent_path)])
            if parent_path == ("history",):
                candidates.update({"show", "clear"})
            elif parent_path == ("config",):
                candidates.update({"show", "set"})
            elif parent_path == ("config", "set"):
                candidates.update({"prompt", "history_limit"})
            elif parent_path == ("alias",):
                candidates.update(self.config["aliases"])
            elif parent_path == ("unalias",):
                candidates.update(self.config["aliases"])
        return sorted(item for item in candidates if item.startswith(current_word))

    def _register_builtin_commands(self) -> None:
        register = self.registry.register
        register(CommandSpec(("help",), "List commands or explain one command.", "help [command]", self._help))
        register(CommandSpec(("version",), "Show the installed DuckOS tools version.", "version", self._version))
        register(CommandSpec(("status",), "Show the terminal runtime and execution policy.", "status", self._status))
        register(CommandSpec(("hardware", "inventory"), "Collect a read-only host device inventory.", "hardware inventory [SYSFS_ROOT]", self._hardware_inventory))
        register(CommandSpec(("desktop", "audit"), "Audit the current user's desktop without changing files.", "desktop audit [ITEM_LIMIT]", self._desktop_audit))
        register(CommandSpec(("desktop", "startup", "list"), "List current-user startup entries.", "desktop startup list", self._startup_list))
        register(CommandSpec(("bridge", "runtimes"), "Discover installed compatibility runtimes.", "bridge runtimes", self._bridge_runtimes))
        register(CommandSpec(("bridge", "inspect"), "Inspect a PE or ELF file without executing it.", "bridge inspect FILE", self._bridge_inspect))
        register(CommandSpec(("bridge", "plan"), "Prepare a non-executing compatibility launch plan.", "bridge plan FILE", self._bridge_plan))
        register(CommandSpec(("compat", "status"), "Show implemented and pending compatibility components.", "compat status", self._compat_status))
        register(CommandSpec(("compat", "inspect"), "Inspect a PE32/PE32+ file without executing it.", "compat inspect FILE", self._compat_inspect))
        register(CommandSpec(("compat", "diagnose"), "Inspect binary imports and an optional prefix.", "compat diagnose FILE [PREFIX]", self._compat_diagnose))
        register(CommandSpec(("compat", "plan"), "Show launch blockers without starting a process.", "compat plan FILE [PREFIX]", self._compat_plan))
        register(CommandSpec(("module", "order"), "Resolve module dependencies from a JSON file.", "module order FILE", self._module_order))

    def _help(self, arguments: list[str]) -> Any:
        commands = self.registry.commands()
        if arguments:
            requested = tuple(arguments)
            match = next((item for item in commands if item.path == requested), None)
            if match is None:
                raise TerminalInputError("unknown command: " + " ".join(arguments))
            return {"usage": match.usage, "description": match.summary}
        return {
            "commands": [
                {"usage": item.usage, "description": item.summary}
                for item in commands
            ],
            "local_commands": [
                "alias [NAME [COMMAND...]]",
                "unalias NAME",
                "history [show|clear]",
                "config show",
                "config set prompt VALUE",
                "config set history_limit VALUE",
                "doctor",
                "exit",
            ],
            "execution_model": "allowlisted in-process commands; no host shell",
        }

    def _version(self, arguments: list[str]) -> Any:
        self._require_no_arguments("version", arguments)
        try:
            installed = package_version("duckos-build-tools")
        except PackageNotFoundError:
            installed = "source-checkout"
        return {"project": "DuckOS", "tools_package": "duckos-build-tools", "version": installed}

    def _status(self, arguments: list[str]) -> Any:
        self._require_no_arguments("status", arguments)
        return {
            "schema": "duckos.terminal-status.v1",
            "runtime_state": "ready",
            "maturity_status": "partial",
            "command_count": len(self.registry.commands()),
            "execution_policy": {
                "host_shell": False,
                "arbitrary_process_launch": False,
                "shell_expansion": False,
                "external_plugin_autoload": False,
                "read_only_system_commands": True,
                "local_preferences_write": True,
                "history_secrets_redacted": True,
            },
        }

    @staticmethod
    def _require_no_arguments(command: str, arguments: list[str]) -> None:
        if arguments:
            raise TerminalInputError(command + " does not accept arguments")

    @staticmethod
    def _require_path(command: str, arguments: list[str], max_args: int = 1) -> Path:
        if not 1 <= len(arguments) <= max_args:
            raise TerminalInputError("usage: " + command)
        return Path(arguments[0])

    def _hardware_inventory(self, arguments: list[str]) -> Any:
        if len(arguments) > 1:
            raise TerminalInputError("usage: hardware inventory [SYSFS_ROOT]")
        return collect_host_inventory(sysfs_root=Path(arguments[0]) if arguments else None)

    def _desktop_audit(self, arguments: list[str]) -> Any:
        if len(arguments) > 1:
            raise TerminalInputError("usage: desktop audit [ITEM_LIMIT]")
        try:
            limit = int(arguments[0]) if arguments else 10
        except ValueError as error:
            raise TerminalInputError("ITEM_LIMIT must be an integer") from error
        if not 1 <= limit <= 100:
            raise TerminalInputError("ITEM_LIMIT must be between 1 and 100")
        return audit_desktop(item_limit=limit)

    def _startup_list(self, arguments: list[str]) -> Any:
        self._require_no_arguments("desktop startup list", arguments)
        return {
            "schema": "duckos.startup-list.v1",
            "scope": "current_user",
            "entries": DesktopService().startup.list_entries(),
            "machine_wide_entries_included": False,
        }

    def _bridge_runtimes(self, arguments: list[str]) -> Any:
        self._require_no_arguments("bridge runtimes", arguments)
        return detect_runtimes()

    def _bridge_inspect(self, arguments: list[str]) -> Any:
        file_path = self._require_path("bridge inspect FILE", arguments)
        return inspect_binary(file_path)

    def _bridge_plan(self, arguments: list[str]) -> Any:
        file_path = self._require_path("bridge plan FILE", arguments)
        return build_launch_plan(file_path, purpose="application", backend="auto")

    def _compat_status(self, arguments: list[str]) -> Any:
        self._require_no_arguments("compat status", arguments)
        return compatibility_status()

    def _compat_inspect(self, arguments: list[str]) -> Any:
        file_path = self._require_path("compat inspect FILE", arguments)
        return inspect_pe_file(file_path)

    def _compat_diagnose(self, arguments: list[str]) -> Any:
        if not 1 <= len(arguments) <= 2:
            raise TerminalInputError("usage: compat diagnose FILE [PREFIX]")
        return diagnose_binary(Path(arguments[0]), Path(arguments[1]) if len(arguments) == 2 else None)

    def _compat_plan(self, arguments: list[str]) -> Any:
        if not 1 <= len(arguments) <= 2:
            raise TerminalInputError("usage: compat plan FILE [PREFIX]")
        return plan_launch(Path(arguments[0]), Path(arguments[1]) if len(arguments) == 2 else None)

    def _module_order(self, arguments: list[str]) -> Any:
        file_path = self._require_path("module order FILE", arguments)
        if file_path.is_symlink():
            raise TerminalInputError("module input must not be a symlink")
        try:
            if file_path.stat().st_size > MAX_INPUT_JSON_BYTES:
                raise TerminalInputError("module input exceeds the 4 MiB limit")
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise TerminalInputError("module input does not exist: " + str(file_path)) from error
        except json.JSONDecodeError as error:
            raise TerminalInputError("invalid module JSON: " + str(error)) from error
        except OSError as error:
            raise TerminalInputError("cannot read module input: " + str(error)) from error
        items = payload.get("modules") if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise TerminalInputError("module input must be a list or an object with a modules list")
        return {
            "schema": "duckos.module-order.v1",
            "load_order": resolve_load_order(items),
            "modules_loaded": False,
        }

    def _doctor(self, arguments: list[str]) -> Any:
        self._require_no_arguments("doctor", arguments)
        return {
            "schema": "duckos.terminal-doctor.v1",
            "python": platform.python_version(),
            "platform": platform.system().lower(),
            "state_directory": "available" if self.state_dir.exists() else "not_created",
            "history_enabled": self.config["history_limit"] > 0,
            "registered_commands": len(self.registry.commands()),
            "host_shell_enabled": False,
        }

    def _local_command(self, tokens: list[str]) -> Any | None:
        command = tokens[0]
        arguments = tokens[1:]
        if command in {"exit", "quit"}:
            self._require_no_arguments(command, arguments)
            return {"exit": True, "message": "DuckOS Extended Terminal closed."}
        if command == "doctor":
            return self._doctor(arguments)
        if command == "history":
            if not arguments or arguments == ["show"]:
                return {"entries": self._read_history()}
            if arguments == ["clear"]:
                self._write_history([])
                return {"cleared": True}
            raise TerminalInputError("usage: history [show|clear]")
        if command == "alias":
            if not arguments:
                return {"aliases": self.config["aliases"]}
            name = arguments[0]
            if not _ALIAS_NAME.fullmatch(name):
                raise TerminalInputError("alias name must match " + _ALIAS_NAME.pattern)
            if name in self._reserved_aliases:
                raise TerminalInputError("alias name is reserved: " + name)
            if len(arguments) == 1:
                target = self.config["aliases"].get(name)
                if target is None:
                    raise TerminalInputError("unknown alias: " + name)
                return {"name": name, "command": target}
            target = arguments[1:]
            if any(token in _SECRET_OPTIONS or any(token.casefold().startswith(flag + "=") for flag in _SECRET_OPTIONS) for token in target):
                raise TerminalInputError("aliases cannot store secret-bearing options")
            previous = self.config["aliases"].get(name)
            self.config["aliases"][name] = target
            try:
                expanded = self._expand_alias([name])
                if self.registry.resolve(expanded) is None:
                    raise TerminalInputError("alias target must resolve to a registered DuckOS command")
            except Exception:
                if previous is None:
                    self.config["aliases"].pop(name, None)
                else:
                    self.config["aliases"][name] = previous
                raise
            self._save_config()
            return {"name": name, "command": target, "saved": True}
        if command == "unalias":
            if len(arguments) != 1:
                raise TerminalInputError("usage: unalias NAME")
            name = arguments[0]
            if name not in self.config["aliases"]:
                raise TerminalInputError("unknown alias: " + name)
            del self.config["aliases"][name]
            self._save_config()
            return {"name": name, "removed": True}
        if command == "config":
            if arguments == ["show"] or not arguments:
                return {
                    "schema": self.config["schema"],
                    "prompt": self.config["prompt"],
                    "history_limit": self.config["history_limit"],
                    "aliases": len(self.config["aliases"]),
                }
            if len(arguments) != 3 or arguments[0] != "set":
                raise TerminalInputError("usage: config set prompt VALUE | config set history_limit VALUE")
            key, value = arguments[1], arguments[2]
            if key == "prompt":
                if not 1 <= len(value) <= 40 or any(ord(char) < 32 or ord(char) == 127 for char in value):
                    raise TerminalInputError("prompt must be 1-40 printable characters")
                self.config["prompt"] = value
            elif key == "history_limit":
                try:
                    limit = int(value)
                except ValueError as error:
                    raise TerminalInputError("history_limit must be an integer") from error
                if not 0 <= limit <= MAX_HISTORY_ENTRIES:
                    raise TerminalInputError("history_limit must be between 0 and 10000")
                self.config["history_limit"] = limit
            else:
                raise TerminalInputError("unknown config key: " + key)
            self._save_config()
            return {"updated": key, "value": self.config[key]}
        return None

    def execute(self, line: str, *, record_history: bool = True) -> dict[str, Any]:
        original_tokens = _tokenize(line)
        if not original_tokens:
            return {"schema": RESULT_SCHEMA, "empty": True}
        tokens = self._expand_alias(original_tokens)
        try:
            local_result = self._local_command(tokens)
            if local_result is not None:
                result = local_result
                command_path = [tokens[0]]
            else:
                resolved = self.registry.resolve(tokens)
                if resolved is None:
                    raise TerminalInputError(
                        "unknown command: " + tokens[0] + ". Run help to list supported commands."
                    )
                command, arguments = resolved
                command_path = list(command.path)
                result = command.handler(arguments)
        except Exception:
            if record_history:
                self._record_history(original_tokens, "failed")
            raise
        if record_history and tokens != ["history", "clear"]:
            self._record_history(original_tokens, "completed")
        return {
            "schema": RESULT_SCHEMA,
            "command": command_path,
            "result": result,
        }


def run_interactive(service: TerminalService | None = None) -> int:
    """Run the line-oriented terminal until exit, EOF or an interrupt."""
    terminal = service or TerminalService()
    try:
        import readline

        def complete(text: str, state: int) -> str | None:
            line = readline.get_line_buffer()
            start = readline.get_begidx()
            matches = terminal.completion_candidates(line[:start], text)
            return matches[state] if state < len(matches) else None

        readline.set_completer(complete)
        readline.parse_and_bind("tab: complete")
    except (ImportError, AttributeError):
        pass
    print("DuckOS Extended Terminal — trusted commands only. Run help for commands.")
    while True:
        try:
            line = input(terminal.prompt + "> ")
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            return 130
        if not line.strip():
            continue
        try:
            response = terminal.execute(line)
        except (OSError, RuntimeError, TypeError, ValueError, ImportError) as error:
            print("error: " + str(error))
            continue
        payload = response.get("result")
        if isinstance(payload, dict) and payload.get("exit") is True:
            print(payload.get("message", "Goodbye."))
            return 0
        if payload is not None:
            print(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False))
