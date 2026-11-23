"""Capability-checked native host services for DuckOS and Mora."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import signal
import shutil
import subprocess
import threading
from typing import Any, Callable
import uuid

try:
    import pwd
except ImportError:  # Windows and minimal non-POSIX Python builds.
    pwd = None

SCHEMA = "duckos.native-host.v1"
MAX_REQUEST_BYTES = 64 * 1024
MAX_PROCESSES = 32
MAX_TERMINAL_OUTPUT = 16 * 1024

SUPPORTED_CAPABILITIES = {
    "host.read", "session.read", "session.spawn", "session.stop",
    "terminal.safe", "driver.inspect", "driver.load", "reaper.evaluate",
    "desktop.start", "display.manage",
}

DRIVER_MODULES = {
    "graphics": ("amdgpu", "i915", "nouveau", "nvidia"),
    "audio": ("snd_hda_intel", "snd_usb_audio", "snd_hda_codec_realtek", "snd_sof_pci_intel"),
    "network": ("iwlwifi", "iwlmvm", "ath9k", "ath10k_pci", "r8169", "e1000e", "igc"),
    "devices": ("xhci_pci", "usbhid", "nvme", "btusb"),
}

SAFE_TERMINAL_COMMANDS = {
    "system": ("uname", ("-a",)),
    "date": ("date", ("--iso-8601=seconds",)),
    "uptime": ("uptime", ()),
    "memory": ("free", ("-h",)),
    "storage": ("df", ("-h",)),
    "processes": ("ps", ("-eo", "pid,ppid,comm,stat")),
    "network": ("ip", ("-brief", "address")),
    "home": ("ls", ("-la",)),
}


class HostError(ValueError):
    """Raised when a host operation is malformed, unavailable or denied."""


def current_uid() -> int:
    """Return the local POSIX UID or a non-root process identity on other hosts."""
    return os.getuid() if hasattr(os, "getuid") else max(1, os.getpid())


def _bounded_text(value: Any, name: str, limit: int = 256) -> str:
    if not isinstance(value, str):
        raise HostError(f"{name} must be text")
    value = value.strip()
    if not value or len(value) > limit or any(ord(char) < 32 for char in value):
        raise HostError(f"{name} is empty or outside its size limit")
    return value


def _string_list(value: Any, name: str, *, limit: int = 32) -> list[str]:
    if not isinstance(value, list) or len(value) > limit:
        raise HostError(f"{name} must be a list with at most {limit} entries")
    return [_bounded_text(item, name, 512) for item in value]


def _load_json(path: Path, *, maximum: int = 256 * 1024) -> Any:
    if path.is_symlink() or not path.is_file():
        raise HostError(f"configuration file is missing or is a symbolic link: {path}")
    if path.stat().st_size > maximum:
        raise HostError(f"configuration file exceeds {maximum} bytes")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HostError(f"cannot read configuration {path}: {error}") from error


def _account_identity(uid: int) -> tuple[str, str, int, list[int]]:
    if os.name != "posix" or pwd is None or not hasattr(os, "geteuid"):
        raise HostError("native sessions currently require a POSIX process host")
    try:
        account = pwd.getpwuid(uid)
    except KeyError as error:
        raise HostError(f"requesting UID {uid} has no local account") from error
    home = account.pw_dir if account.pw_dir and Path(account.pw_dir).is_dir() else "/"
    try:
        groups = sorted(set(os.getgrouplist(account.pw_name, account.pw_gid)) - {account.pw_gid})
    except (AttributeError, OSError):
        groups = []
    return account.pw_name, home, account.pw_gid, groups


def _drop_identity(uid: int, gid: int, extra_groups: list[int]) -> dict[str, Any]:
    if os.geteuid() == 0:
        return {"user": uid, "group": gid, "extra_groups": extra_groups}
    if uid != os.getuid():
        raise HostError("an unprivileged host broker may only act for its own UID")
    return {}


class CapabilityPolicy:
    """Per-UID grants loaded from an administrator-owned JSON policy."""

    def __init__(self, grants: dict[int, set[str]] | None = None) -> None:
        self.grants = grants or {}

    @classmethod
    def load(cls, path: str | Path) -> "CapabilityPolicy":
        payload = _load_json(Path(path))
        if not isinstance(payload, dict) or payload.get("schema") != "duckos.host-policy.v1":
            raise HostError("host policy must use duckos.host-policy.v1")
        principals = payload.get("principals")
        if not isinstance(principals, dict):
            raise HostError("host policy must contain a principals object")
        grants: dict[int, set[str]] = {}
        for raw_uid, raw_grants in principals.items():
            try:
                uid = int(raw_uid)
            except (TypeError, ValueError) as error:
                raise HostError(f"invalid principal UID: {raw_uid}") from error
            if uid < 0 or not isinstance(raw_grants, list):
                raise HostError(f"invalid capability list for UID {uid}")
            selected = set(_string_list(raw_grants, f"principals.{uid}", limit=32))
            unknown = selected - SUPPORTED_CAPABILITIES
            if unknown:
                raise HostError(f"unknown capabilities for UID {uid}: {', '.join(sorted(unknown))}")
            grants[uid] = selected
        return cls(grants)

    @classmethod
    def for_current_user(cls, uid: int | None = None) -> "CapabilityPolicy":
        selected_uid = current_uid() if uid is None else uid
        return cls({selected_uid: {
            "host.read", "session.read", "session.spawn", "session.stop",
            "terminal.safe", "driver.inspect", "reaper.evaluate",
            "desktop.start", "display.manage",
        }})

    def permits(self, uid: int, capability: str) -> bool:
        return uid == 0 or capability in self.grants.get(uid, set())

    def as_json(self) -> dict[str, Any]:
        return {
            "schema": "duckos.host-policy.v1",
            "principals": {str(uid): sorted(grants) for uid, grants in sorted(self.grants.items())},
        }


@dataclass
class ProcessRecord:
    session_id: str
    application_id: str
    name: str
    pid: int
    uid: int
    started_at: str
    process: subprocess.Popen[Any]

    def snapshot(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "application_id": self.application_id,
            "name": self.name,
            "pid": self.pid,
            "uid": self.uid,
            "started_at": self.started_at,
            "status": "running" if self.process.poll() is None else "exited",
            "exit_code": self.process.poll(),
        }


class ProcessSupervisor:
    """Starts registered applications in independent POSIX process groups."""

    def __init__(
        self,
        applications: dict[str, Any] | None = None,
        *,
        popen: Callable[..., subprocess.Popen[Any]] = subprocess.Popen,
        maximum: int = MAX_PROCESSES,
    ) -> None:
        self.applications = applications if applications is not None else self._read_applications()
        self.popen = popen
        self.maximum = maximum
        self.records: dict[str, ProcessRecord] = {}
        self.lock = threading.RLock()

    @staticmethod
    def _read_applications() -> dict[str, Any]:
        path = Path(__file__).with_name("native-apps.json")
        payload = _load_json(path)
        if not isinstance(payload, dict) or payload.get("schema") != "duckos.native-applications.v1":
            raise HostError("native application catalogue has an unsupported schema")
        applications = payload.get("applications")
        if not isinstance(applications, dict):
            raise HostError("native application catalogue is malformed")
        return applications

    @staticmethod
    def _environment(home: str) -> dict[str, str]:
        allowed = {
            "DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY", "XDG_RUNTIME_DIR",
            "DBUS_SESSION_BUS_ADDRESS", "LANG", "LC_ALL",
        }
        env = {key: value for key, value in os.environ.items() if key in allowed}
        env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        env["HOME"] = home
        return env

    def start(self, application_id: str, uid: int) -> dict[str, Any]:
        application_id = _bounded_text(application_id, "application_id", 64)
        app = self.applications.get(application_id)
        if not isinstance(app, dict):
            raise HostError(f"unknown native application: {application_id}")
        argv = app.get("argv")
        if not isinstance(argv, list) or not argv or len(argv) > 16 or not all(
            isinstance(part, str) and part and len(part) <= 512 and "\x00" not in part
            for part in argv
        ):
            raise HostError(f"native application {application_id} has an invalid argv")
        executable = Path(argv[0])
        if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
            raise HostError(f"native application is not installed: {argv[0]}")
        _name, home, gid, groups = _account_identity(uid)
        identity_options = _drop_identity(uid, gid, groups)

        with self.lock:
            for session_id, record in tuple(self.records.items()):
                if record.process.poll() is not None:
                    del self.records[session_id]
            if len(self.records) >= self.maximum:
                raise HostError(f"active process limit reached ({self.maximum})")
            process = self.popen(
                list(argv),
                shell=False,
                cwd=home,
                env=self._environment(home),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
                **identity_options,
            )
            session_id = uuid.uuid4().hex
            record = ProcessRecord(
                session_id=session_id,
                application_id=application_id,
                name=str(app.get("name") or application_id),
                pid=process.pid,
                uid=uid,
                started_at=datetime.now(timezone.utc).isoformat(),
                process=process,
            )
            self.records[session_id] = record
            return record.snapshot()

    def list(self, uid: int) -> list[dict[str, Any]]:
        with self.lock:
            return [
                record.snapshot()
                for record in self.records.values()
                if uid == 0 or record.uid == uid
            ]

    def stop(self, session_id: str, uid: int, *, timeout: float = 3.0) -> dict[str, Any]:
        session_id = _bounded_text(session_id, "session_id", 64)
        with self.lock:
            record = self.records.get(session_id)
            if record is None or (uid != 0 and record.uid != uid):
                raise HostError("session was not found or is not owned by this principal")
            process = record.process
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=timeout)
            return record.snapshot()


class SafeTerminal:
    """Small diagnostic terminal whose commands are fixed argv records."""

    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        commands: dict[str, tuple[str, tuple[str, ...]]] | None = None,
    ) -> None:
        self.runner = runner
        self.commands = commands or SAFE_TERMINAL_COMMANDS

    def execute(self, command_id: str, uid: int) -> dict[str, Any]:
        command_id = _bounded_text(command_id, "command_id", 48)
        if command_id not in self.commands:
            raise HostError(f"terminal command is not allowlisted: {command_id}")
        executable_name, arguments = self.commands[command_id]
        executable = shutil.which(executable_name)
        if executable is None:
            raise HostError(f"terminal provider is not installed: {executable_name}")
        _name, home, gid, groups = _account_identity(uid)
        identity_options = _drop_identity(uid, gid, groups)
        try:
            result = self.runner(
                [executable, *arguments],
                shell=False,
                cwd=home,
                env={
                    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                    "HOME": home,
                    "LANG": os.environ.get("LANG", "C.UTF-8"),
                },
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=5,
                check=False,
                **identity_options,
            )
        except subprocess.TimeoutExpired as error:
            raise HostError(f"terminal command timed out: {command_id}") from error
        return {
            "command_id": command_id,
            "argv": [executable, *arguments],
            "exit_code": result.returncode,
            "stdout": result.stdout[:MAX_TERMINAL_OUTPUT],
            "stderr": result.stderr[:MAX_TERMINAL_OUTPUT],
            "truncated": len(result.stdout) > MAX_TERMINAL_OUTPUT or len(result.stderr) > MAX_TERMINAL_OUTPUT,
            "shell_used": False,
            "uid": uid,
        }


class DriverManager:
    """Inspects host kernel modules and loads only named, allowlisted modules."""

    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        module_root: str | Path = "/proc/modules",
        module_catalogue: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        self.runner = runner
        self.module_root = Path(module_root)
        self.module_catalogue = module_catalogue or DRIVER_MODULES

    def _loaded(self) -> set[str]:
        try:
            return {
                line.split()[0].replace("-", "_")
                for line in self.module_root.read_text(encoding="ascii").splitlines()
                if line.split()
            }
        except OSError:
            return set()

    def list(self) -> dict[str, Any]:
        if not self.module_root.exists():
            return {
                "schema": "duckos.driver-inventory.v1",
                "provider": "unsupported-host",
                "module_load_supported": False,
                "modules": [],
            }
        loaded = self._loaded()
        modinfo = shutil.which("modinfo")
        entries = []
        for category, modules in self.module_catalogue.items():
            for module in modules:
                installed = False
                if modinfo:
                    try:
                        probe = self.runner(
                            [modinfo, "-F", "filename", module],
                            shell=False, capture_output=True, text=True, timeout=3, check=False,
                        )
                        installed = probe.returncode == 0 and bool(probe.stdout.strip())
                    except (OSError, subprocess.TimeoutExpired):
                        installed = False
                entries.append({
                    "category": category,
                    "module": module,
                    "installed": installed,
                    "loaded": module.replace("-", "_") in loaded,
                })
        return {
            "schema": "duckos.driver-inventory.v1",
            "provider": "linux-kernel-modules",
            "module_load_supported": bool(shutil.which("modprobe")),
            "modules": entries,
        }

    def load(self, category: str, module: str) -> dict[str, Any]:
        category = _bounded_text(category, "category", 32)
        module = _bounded_text(module, "module", 64)
        if module not in self.module_catalogue.get(category, ()):
            raise HostError("driver module is not present in the category allowlist")
        if os.name != "posix" or not hasattr(os, "geteuid") or os.geteuid() != 0:
            raise HostError("driver.load requires the privileged DuckOS host broker")
        modprobe = shutil.which("modprobe")
        if not modprobe:
            raise HostError("modprobe is not installed on this host")
        try:
            result = self.runner(
                [modprobe, module],
                shell=False,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise HostError(f"could not load driver module {module}: {error}") from error
        if result.returncode != 0:
            raise HostError((result.stderr or f"modprobe exited with {result.returncode}")[:2048])
        return {
            "module": module,
            "category": category,
            "loaded": module.replace("-", "_") in self._loaded(),
            "load_request_succeeded": True,
            "driver_source_built_by_duckos": False,
        }


class ReaperPolicyBridge:
    """Runs fixed DuckOS .rpr policy entry points on Reaper's reference runtime."""

    CONTRACTS = {
        "capability.permits",
        "desktop.command_policy",
        "desktop.session_transition",
        "window.transition",
    }

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root).resolve() if project_root else Path(__file__).resolve().parents[2]
        self.entry_file = self.project_root / "duckos" / "host" / "reaper_entry.rpr"

    @staticmethod
    def _runtime():
        try:
            from reaper.runtime import Interpreter
        except ImportError:
            return None
        return Interpreter

    def status(self) -> dict[str, Any]:
        available = self._runtime() is not None
        return {
            "schema": "duckos.reaper-bridge.v1",
            "runtime": "reaper-python-reference" if available else "not-installed",
            "available": available,
            "entry_file": str(self.entry_file),
            "contracts": sorted(self.CONTRACTS),
        }

    @staticmethod
    def _literal(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    def evaluate(self, contract: str, arguments: dict[str, Any]) -> dict[str, Any]:
        contract = _bounded_text(contract, "contract", 64)
        if contract not in self.CONTRACTS:
            raise HostError(f"Reaper contract is not exposed by the host bridge: {contract}")
        Interpreter = self._runtime()
        if Interpreter is None:
            raise HostError("Reaper reference runtime is not installed; set PYTHONPATH to the Reaper checkout")
        if not isinstance(arguments, dict) or len(arguments) > 8:
            raise HostError("Reaper contract arguments must be a small JSON object")

        if contract == "capability.permits":
            granted = _string_list(arguments.get("granted"), "granted", limit=32)
            requested = _bounded_text(arguments.get("requested"), "requested", 64)
            source = (
                'import "../security/capabilities.rpr" as policy\n'
                f'emit policy["permits"]({self._literal(granted)}, {self._literal(requested)})\n'
            )
        elif contract == "desktop.command_policy":
            command = _string_list(arguments.get("command"), "command", limit=4)
            apps = _string_list(arguments.get("known_apps"), "known_apps", limit=128)
            workspaces = _string_list(arguments.get("known_workspaces"), "known_workspaces", limit=16)
            source = (
                'import "../ui/desktop.rpr" as desktop\n'
                f'emit desktop["command_policy"]({self._literal(command)}, {self._literal(apps)}, {self._literal(workspaces)})\n'
            )
        elif contract == "desktop.session_transition":
            current = _bounded_text(arguments.get("current"), "current", 32)
            target = _bounded_text(arguments.get("target"), "target", 32)
            source = (
                'import "../ui/desktop.rpr" as desktop\n'
                f'emit desktop["session_transition_valid"]({self._literal(current)}, {self._literal(target)})\n'
            )
        else:
            current = _bounded_text(arguments.get("current"), "current", 32)
            target = _bounded_text(arguments.get("target"), "target", 32)
            source = (
                'import "../ui/window_manager.rpr" as windows\n'
                f'emit windows["transition_valid"]({self._literal(current)}, {self._literal(target)})\n'
            )

        if not self.entry_file.is_file():
            raise HostError(f"DuckOS Reaper policy entry is missing: {self.entry_file}")
        output: list[str] = []
        interpreter = Interpreter(
            output=output.append,
            max_steps=20_000,
            max_collection_items=4_096,
            max_text_length=64 * 1024,
            max_heap_bytes=8 * 1024 * 1024,
            max_open_resources=8,
        )
        try:
            interpreter.run(source, filename=str(self.entry_file), engine="treewalk")
        except Exception as error:
            raise HostError(f"Reaper policy evaluation failed: {type(error).__name__}: {error}") from error
        if len(output) != 1:
            raise HostError("Reaper contract did not return exactly one result")
        raw = output[0]
        if raw in {"true", "True"}:
            value: Any = True
        elif raw in {"false", "False"}:
            value = False
        else:
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                value = raw
        return {
            "schema": "duckos.reaper-evaluation.v1",
            "contract": contract,
            "result": value,
            "engine": "reaper-python-reference",
            "source": str(self.entry_file),
        }


class NativeHostBroker:
    """The single dispatch point for capability-checked OS service requests."""

    def __init__(
        self,
        policy: CapabilityPolicy | None = None,
        *,
        processes: ProcessSupervisor | None = None,
        terminal: SafeTerminal | None = None,
        drivers: DriverManager | None = None,
        reaper: ReaperPolicyBridge | None = None,
    ) -> None:
        self.policy = policy or CapabilityPolicy.for_current_user()
        self.processes = processes or ProcessSupervisor()
        self.terminal = terminal or SafeTerminal()
        self.drivers = drivers or DriverManager()
        self.reaper = reaper or ReaperPolicyBridge()

    def _require(self, uid: int, capability: str) -> None:
        if not self.policy.permits(uid, capability):
            raise HostError(f"capability denied: {capability}")

    def dispatch(self, uid: int, request: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(request, dict) or set(request) - {"id", "method", "params"}:
            raise HostError("RPC request must contain only id, method and params")
        request_id = request.get("id")
        if isinstance(request_id, bool) or not isinstance(request_id, (str, int)):
            raise HostError("RPC id must be a string or integer")
        method = _bounded_text(request.get("method"), "method", 80)
        params = request.get("params", {})
        if not isinstance(params, dict) or len(params) > 16:
            raise HostError("RPC params must be a small object")

        if method == "host.status":
            self._require(uid, "host.read")
            display = "wayland" if os.environ.get("WAYLAND_DISPLAY") else "x11" if os.environ.get("DISPLAY") else "not-detected"
            result = {
                "schema": SCHEMA,
                "host": platform.system(),
                "architecture": platform.machine(),
                "uid": uid,
                "display_backend": display,
                "native_x11_compositor_installed": shutil.which("duckos-compositor") is not None,
                "process_supervisor": "posix-process-groups",
                "privileged_broker": bool(hasattr(os, "geteuid") and os.geteuid() == 0),
                "kernel_sandbox": False,
            }
        elif method == "session.list":
            self._require(uid, "session.read")
            result = {"sessions": self.processes.list(uid)}
        elif method == "session.start":
            self._require(uid, "session.spawn")
            application_id = _bounded_text(params.get("application_id"), "application_id", 64)
            application = self.processes.applications.get(application_id)
            if not isinstance(application, dict):
                raise HostError(f"unknown native application: {application_id}")
            required = _string_list(application.get("capabilities", []), "application.capabilities", limit=16)
            for capability in required:
                self._require(uid, capability)
            result = self.processes.start(application_id, uid)
        elif method == "session.stop":
            self._require(uid, "session.stop")
            result = self.processes.stop(params.get("session_id"), uid)
        elif method == "terminal.run":
            self._require(uid, "terminal.safe")
            result = self.terminal.execute(params.get("command_id"), uid)
        elif method == "driver.list":
            self._require(uid, "driver.inspect")
            result = self.drivers.list()
        elif method == "driver.inventory":
            self._require(uid, "driver.inspect")
            from ..hardware_inventory import collect_host_inventory
            result = {"modules": self.drivers.list(), "devices": collect_host_inventory()}
        elif method == "driver.load":
            self._require(uid, "driver.load")
            result = self.drivers.load(params.get("category"), params.get("module"))
        elif method == "reaper.status":
            self._require(uid, "host.read")
            result = self.reaper.status()
        elif method == "reaper.evaluate":
            self._require(uid, "reaper.evaluate")
            result = self.reaper.evaluate(params.get("contract"), params.get("arguments", {}))
        else:
            raise HostError(f"unknown host RPC method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
