"""Reviewable local launch, trust and process controls for Illidia.

Executables are started with argument arrays and shell=False. This host-side
backend is not a kernel-enforced DuckOS process sandbox; see the Illidia guide.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .library import GameRecord, IllidiaError, IllidiaLibrary


class LaunchError(IllidiaError):
    """Raised when a launch cannot safely proceed."""


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def signature_report(path: str | Path, timeout: int = 12) -> dict[str, Any]:
    """Inspect Authenticode on Windows; report unknown where no verifier exists."""
    target = Path(path).resolve(strict=True)
    if os.name != "nt":
        return {
            "status": "not_checked",
            "signer": None,
            "detail": "This host does not expose a common executable-signature verifier.",
        }

    script = (
        "$s = Get-AuthenticodeSignature -LiteralPath $args[0]; "
        "$r = [ordered]@{ status = [string]$s.Status; "
        "signer = if ($s.SignerCertificate) { $s.SignerCertificate.Subject } else { $null } }; "
        "$r | ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script, str(target)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()[:500]
            return {"status": "not_checked", "signer": None, "detail": detail or "PowerShell verifier failed."}
        payload = json.loads(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        return {"status": "not_checked", "signer": None, "detail": str(error)[:500]}

    raw_status = str(payload.get("status", "Unknown")).casefold()
    mapped = {
        "valid": "signed",
        "notsigned": "unsigned",
        "hashmismatch": "invalid",
        "nottrusted": "invalid",
        "unknownerror": "not_checked",
        "nottrusted": "invalid",
    }.get(raw_status, "not_checked")
    return {
        "status": mapped,
        "signer": payload.get("signer"),
        "detail": f"Authenticode: {payload.get('status', 'Unknown')}",
    }


def _store_launch_enabled(game: GameRecord) -> bool:
    default = game.source in {"steam", "epic", "gog"} and bool(game.metadata.get("store_uri"))
    return game.launch_profile.get("launch_via_store", default) is True


def inspect_game(library: IllidiaLibrary, game: GameRecord) -> dict[str, Any]:
    if _store_launch_enabled(game):
        install_path = game.metadata.get("install_path")
        available = bool(install_path and Path(install_path).is_dir())
        return {
            "game_id": game.id,
            "name": game.name,
            "launch_mode": "store",
            "store_uri": game.metadata.get("store_uri"),
            "installed": available,
            "signature": {"status": "delegated_to_store", "signer": None, "detail": "The store client owns its update and launch chain."},
            "sha256": None,
            "previous_sha256": None,
            "hash_changed": False,
            "first_run_confirmation_required": False,
            "warnings": [],
        }

    if not game.executable_path:
        raise LaunchError("No executable is configured. Choose a binary or enable the store launch route.")
    executable = Path(game.executable_path).expanduser()
    if not executable.is_file():
        raise LaunchError(f"Executable not found: {executable}")
    if os.name != "nt" and not os.access(executable, os.X_OK):
        raise LaunchError(f"File is not executable: {executable}")

    working_directory = Path(game.working_directory or executable.parent).expanduser()
    if not working_directory.is_dir():
        raise LaunchError(f"Working directory not found: {working_directory}")

    digest = sha256_file(executable)
    signature = signature_report(executable)
    previous = library.fingerprint(game.id)
    changed = previous is not None and previous != digest
    requires_confirmation = signature["status"] in {"unsigned", "not_checked", "invalid"}
    approved = library.has_approval(game.id, digest)
    warnings = []
    if signature["status"] == "unsigned":
        warnings.append("The executable has no valid Authenticode signature.")
    elif signature["status"] == "invalid":
        warnings.append("Authenticode validation failed; review the file before running it.")
    elif signature["status"] == "not_checked":
        warnings.append("The executable signature could not be verified on this host.")
    if changed:
        warnings.append("The executable hash differs from the saved fingerprint.")
    return {
        "game_id": game.id,
        "name": game.name,
        "launch_mode": "direct",
        "executable_path": str(executable),
        "working_directory": str(working_directory),
        "installed": True,
        "signature": signature,
        "sha256": digest,
        "previous_sha256": previous,
        "hash_changed": changed,
        "first_run_confirmation_required": requires_confirmation and not approved,
        "warnings": warnings,
    }


def _runtime_command(game: GameRecord) -> list[str]:
    executable = game.executable_path
    if not executable:
        raise LaunchError("This game has no executable path.")
    if game.runtime == "native":
        return [executable, *game.arguments]
    if not game.runtime_command:
        raise LaunchError(
            f"Runtime '{game.runtime}' is selected but no runtime command is configured."
        )
    command = list(game.runtime_command)
    if game.runtime == "proton":
        return [*command, "run", executable, *game.arguments]
    return [*command, executable, *game.arguments]


def _working_directory(game: GameRecord) -> Path:
    executable = Path(game.executable_path or "").expanduser()
    cwd = Path(game.working_directory).expanduser() if game.working_directory else executable.parent
    if not cwd.is_dir():
        raise LaunchError(f"Working directory not found: {cwd}")
    return cwd.resolve()


def _environment(game: GameRecord) -> dict[str, str]:
    env = os.environ.copy()
    profile = game.launch_profile
    overrides = profile.get("environment", {})
    if not isinstance(overrides, dict):
        raise LaunchError("Launch profile environment is invalid.")
    env.update(overrides)
    if game.runtime_prefix:
        if game.runtime in {"wine", "proton", "crossover", "bottles"}:
            env.setdefault("WINEPREFIX", game.runtime_prefix)
            env.setdefault("STEAM_COMPAT_DATA_PATH", game.runtime_prefix) if game.runtime == "proton" else None
    return env


def _run_hooks(game: GameRecord, hook_name: str, cwd: Path, log_stream: Any) -> None:
    profile = game.launch_profile
    hooks = profile.get(hook_name, [])
    if not hooks:
        return
    if profile.get("allow_hooks") is not True:
        raise LaunchError(
            f"{hook_name} commands are configured but disabled. Explicitly enable allow_hooks in the profile."
        )
    for command in hooks:
        if not isinstance(command, list) or not command or any(not isinstance(arg, str) for arg in command):
            raise LaunchError(f"Invalid {hook_name} command.")
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=_environment(game),
            stdin=subprocess.DEVNULL,
            stdout=log_stream,
            stderr=subprocess.STDOUT,
            shell=False,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            raise LaunchError(f"{hook_name} command exited with code {completed.returncode}.")


def _open_store_uri(uri: str) -> tuple[int | None, list[str]]:
    parsed = urlparse(uri)
    if parsed.scheme not in {"steam", "com.epicgames.launcher", "goggalaxy"}:
        raise LaunchError("Unsupported store URI scheme.")
    if os.name == "nt":
        os.startfile(uri)  # type: ignore[attr-defined]
        return None, ["os-handler", uri]
    opener = shutil.which("open" if __import__("sys").platform == "darwin" else "xdg-open")
    if not opener:
        raise LaunchError("No desktop URI handler (xdg-open/open) was found.")
    process = subprocess.Popen(
        [opener, uri],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
        start_new_session=(os.name != "nt"),
    )
    return process.pid, [opener, uri]


def _log_directory(library: IllidiaLibrary) -> Path:
    folder = library.database.parent / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def launch_game(
    library: IllidiaLibrary,
    game_id: str,
    *,
    confirm_unverified: bool = False,
    update_fingerprint: bool = False,
    direct: bool = False,
    wait: bool = False,
) -> dict[str, Any]:
    game = library.get_game(game_id)
    review = inspect_game(library, game) if not (direct and _store_launch_enabled(game)) else inspect_game(
        library, _direct_game_view(game)
    )

    if review["launch_mode"] == "store" and not direct:
        uri = review["store_uri"]
        pid, command = _open_store_uri(uri)
        launch_id = library.record_launch(
            game.id, pid=pid, process_group=None, launch_kind="store-delegated",
            command=command, log_path=None,
        )
        return {
            "launch_id": launch_id,
            "status": "delegated_to_store",
            "pid": pid,
            "message": "The official store client received the game launch request. The store owns overlay and cloud-save behavior; Illidia cannot supervise the game's full process tree through a browser or URI handler.",
            "command": command,
        }

    if review["first_run_confirmation_required"] and not confirm_unverified:
        raise LaunchError(
            "First launch requires explicit approval because the executable is unsigned or its signature was not verified. Review the file, then repeat with --confirm-unverified."
        )

    digest = review["sha256"]
    if review["first_run_confirmation_required"] and confirm_unverified:
        library.approve(game.id, digest, "unverified")
    if library.fingerprint(game.id) is None or update_fingerprint:
        library.set_fingerprint(game.id, digest)

    command = _runtime_command(game)
    cwd = _working_directory(game)
    env = _environment(game)
    launch_id = str(uuid.uuid4())
    log_path = _log_directory(library) / f"{launch_id}.log"

    with log_path.open("a", encoding="utf-8") as log_stream:
        log_stream.write(f"Illidia launch {launch_id}\n")
        log_stream.write(f"Game: {game.name}\n")
        log_stream.write(f"Runtime: {game.runtime}\n")
        log_stream.write(f"Working directory: {cwd}\n")
        log_stream.write("Command: " + json.dumps(command, ensure_ascii=False) + "\n")
        for warning in review["warnings"]:
            log_stream.write("Warning: " + warning + "\n")
        log_stream.flush()
        _run_hooks(game, "pre_launch", cwd, log_stream)
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log_stream,
            stderr=subprocess.STDOUT,
            shell=False,
            start_new_session=(os.name != "nt"),
            creationflags=creation_flags,
        )
        try:
            process_group = os.getpgid(process.pid) if os.name != "nt" else None
        except OSError:
            process_group = None
        launch_id = library.record_launch(
            game.id, pid=process.pid, process_group=process_group,
            launch_kind="direct", command=command, log_path=str(log_path),
        )

    exit_code = None
    status = "running"
    if wait:
        exit_code = process.wait()
        status = "exited" if exit_code == 0 else "failed"
        library.update_launch(launch_id, status=status, exit_code=exit_code)
        if game.launch_profile.get("post_launch"):
            with log_path.open("a", encoding="utf-8") as log_stream:
                _run_hooks(game, "post_launch", cwd, log_stream)

    return {
        "launch_id": launch_id,
        "status": status,
        "pid": process.pid,
        "process_group": process_group,
        "exit_code": exit_code,
        "log_path": str(log_path),
        "command": command,
        "warnings": review["warnings"],
        "hash_changed": review["hash_changed"],
        "fingerprint_updated": library.fingerprint(game.id) == digest,
    }


def _direct_game_view(game: GameRecord) -> GameRecord:
    """Disable store routing for an explicitly requested direct executable launch."""
    from dataclasses import replace

    profile = dict(game.launch_profile)
    profile["launch_via_store"] = False
    return replace(game, launch_profile=profile)


def process_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def refresh_sessions(library: IllidiaLibrary) -> list[dict[str, Any]]:
    sessions = library.list_launches()
    for session in sessions:
        if session["status"] == "running" and session["pid"] and not process_is_running(session["pid"]):
            library.update_launch(session["id"], status="exited", exit_code=None)
            session["status"] = "exited"
    return sessions


def stop_launch(library: IllidiaLibrary, launch_id: str, *, force: bool = False) -> dict[str, Any]:
    session = next((item for item in library.list_launches() if item["id"] == launch_id), None)
    if session is None:
        raise LaunchError(f"Launch session not found: {launch_id}")
    if session["launch_kind"] != "direct":
        raise LaunchError(
            "This session was delegated to a store client. Stop the game through that store; the URI handler is not the game process."
        )
    pid = session["pid"]
    if not pid or not process_is_running(pid):
        library.update_launch(launch_id, status="exited", exit_code=None)
        return {"launch_id": launch_id, "status": "already_exited"}

    if os.name == "nt":
        command = ["taskkill.exe", "/PID", str(pid), "/T"]
        if force:
            command.append("/F")
        result = subprocess.run(command, capture_output=True, text=True, timeout=10, shell=False)
        if result.returncode != 0:
            raise LaunchError((result.stderr or result.stdout).strip() or "taskkill failed")
    else:
        process_group = session["process_group"] or pid
        os.killpg(process_group, signal.SIGKILL if force else signal.SIGTERM)
    library.update_launch(launch_id, status="stop_requested", exit_code=None)
    return {"launch_id": launch_id, "status": "stop_requested", "force": force}
