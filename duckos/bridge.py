"""Authenticated loopback API used by the Mora browser shell."""
from __future__ import annotations

import hmac
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from .runtime import AppStoreError, RuntimeErrorBase, RuntimeManager

_MAX_UPLOAD_BYTES = 8 * 1024 * 1024 * 1024
_ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


def _local_origin(value: str | None) -> bool:
    if not value:
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.hostname in _ALLOWED_HOSTS
            and parsed.username is None
            and parsed.password is None
            and parsed.port is not None
            and 1 <= parsed.port <= 65535
        )
    except ValueError:
        return False


def _load_pairing_token(manager: RuntimeManager) -> str:
    token_file = manager.store.root / "bridge.token"
    if token_file.is_symlink():
        raise RuntimeErrorBase("bridge token path must not be a symbolic link")
    if token_file.exists():
        token = token_file.read_text(encoding="ascii").strip()
        if len(token) < 40:
            raise RuntimeErrorBase("bridge token file is invalid; remove it and pair again")
        return token
    token = secrets.token_urlsafe(48)
    with token_file.open("x", encoding="ascii") as stream:
        stream.write(token + "\n")
    try:
        token_file.chmod(0o600)
    except OSError:
        pass
    return token


class _RuntimeHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, handler, manager, token):
        self.manager = manager
        self.token = token
        super().__init__(server_address, handler)


class RuntimeRequestHandler(BaseHTTPRequestHandler):
    server: _RuntimeHTTPServer
    protocol_version = "HTTP/1.1"
    server_version = "DuckOSRuntime"
    sys_version = ""

    def log_message(self, format: str, *args) -> None:
        return

    def _is_local_host(self) -> bool:
        try:
            parsed = urlsplit("//" + self.headers.get("Host", ""))
            return parsed.hostname in _ALLOWED_HOSTS
        except ValueError:
            return False

    def _origin(self) -> str | None:
        value = self.headers.get("Origin")
        if not value or not _local_origin(value):
            return None
        return value

    def _cors_headers(self) -> None:
        origin = self._origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-DuckOS-Filename, X-DuckOS-Entrypoint, X-DuckOS-Name")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.send_header("Access-Control-Max-Age", "300")

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _authorize(self) -> bool:
        if not self._is_local_host():
            self._write_json(403, {"error": "loopback host required"})
            return False
        origin = self.headers.get("Origin")
        if origin and not _local_origin(origin):
            self._write_json(403, {"error": "non-local browser origin rejected"})
            return False
        if origin and not self._origin():
            self._write_json(403, {"error": "browser origin rejected"})
            return False
        supplied = self.headers.get("Authorization", "")
        if not supplied.startswith("Bearer "):
            self._write_json(401, {"error": "pairing token required"})
            return False
        token = supplied[7:].strip()
        if not hmac.compare_digest(token, self.server.token):
            self._write_json(403, {"error": "invalid pairing token"})
            return False
        return True

    def do_OPTIONS(self) -> None:
        if not self._is_local_host() or not self._origin():
            self._write_json(403, {"error": "only loopback browser origins are allowed"})
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if not self._authorize():
            return
        if self.path == "/v1/capabilities":
            self._write_json(200, self.server.manager.capabilities())
        elif self.path == "/v1/apps":
            self._write_json(200, {"apps": self.server.manager.store.list_apps(verify=False)})
        elif self.path == "/v1/processes":
            self._write_json(200, {"processes": self.server.manager.list_processes()})
        elif self.path == "/v1/vms":
            self._write_json(200, {"vms": self.server.manager.store.list_vms()})
        else:
            self._write_json(404, {"error": "unknown endpoint"})

    def do_POST(self) -> None:
        if not self._authorize():
            return
        try:
            if self.path == "/v1/apps/import":
                self._import_app()
            elif self.path == "/v1/launch":
                self._launch_app()
            elif self.path.startswith("/v1/processes/") and self.path.endswith("/terminate"):
                self._terminate_process()
            elif self.path.startswith("/v1/vms/") and self.path.endswith("/launch"):
                self._launch_vm()
            else:
                self._write_json(404, {"error": "unknown endpoint"})
        except (AppStoreError, RuntimeErrorBase, ValueError, OSError) as error:
            self._write_json(400, {"error": str(error)})
        except Exception:
            self._write_json(500, {"error": "native runtime service failed"})

    def _read_json(self, maximum: int = 1024 * 1024) -> dict:
        length = self._content_length(maximum)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("request body must be valid UTF-8 JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def _content_length(self, maximum: int) -> int:
        value = self.headers.get("Content-Length")
        if value is None or not value.isdigit():
            raise ValueError("Content-Length is required")
        length = int(value)
        if not 0 <= length <= maximum:
            raise ValueError("request body exceeds the configured size limit")
        return length

    def _import_app(self) -> None:
        length = self._content_length(_MAX_UPLOAD_BYTES)
        raw_name = unquote(self.headers.get("X-DuckOS-Filename", ""))
        if not raw_name or len(raw_name) > 240 or "/" in raw_name or "\\" in raw_name:
            raise ValueError("X-DuckOS-Filename must be a simple filename")
        entrypoint = self.headers.get("X-DuckOS-Entrypoint")
        display_name = self.headers.get("X-DuckOS-Name")
        incoming = self.server.manager.store.root / "incoming"
        incoming.mkdir(mode=0o700, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix="upload-", suffix=Path(raw_name).suffix, dir=incoming)
        temporary = Path(temporary_name)
        try:
            remaining = length
            with os.fdopen(descriptor, "wb") as output:
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError("upload ended before Content-Length bytes were received")
                    output.write(chunk)
                    remaining -= len(chunk)
            try:
                temporary.chmod(0o600)
            except OSError:
                pass
            app = self.server.manager.import_app(
                temporary,
                entrypoint=entrypoint,
                display_name=display_name or Path(raw_name).stem,
            )
            self._write_json(201, {"app": app})
        finally:
            temporary.unlink(missing_ok=True)

    def _launch_app(self) -> None:
        payload = self._read_json()
        allowed = {"app_id", "runtime_id", "arguments", "approved", "allow_unisolated", "allow_network"}
        if set(payload) - allowed:
            raise ValueError("launch request contains unknown fields")
        if payload.get("approved") is not True:
            raise ValueError("explicit user approval is required")
        for name in ("allow_unisolated", "allow_network"):
            if name in payload and not isinstance(payload[name], bool):
                raise ValueError(f"{name} must be a boolean")
        result = self.server.manager.launch_app(
            payload.get("app_id"),
            runtime_id=payload.get("runtime_id", "auto"),
            arguments=payload.get("arguments", []),
            approved=True,
            allow_unisolated=payload.get("allow_unisolated", False),
            allow_network=payload.get("allow_network", False),
        )
        self._write_json(202, {"process": result})

    def _terminate_process(self) -> None:
        match = re.fullmatch(r"/v1/processes/([0-9a-f]{32})/terminate", self.path)
        if not match:
            self._write_json(404, {"error": "unknown process"})
            return
        self._write_json(200, self.server.manager.terminate_process(match.group(1)))

    def _launch_vm(self) -> None:
        match = re.fullmatch(r"/v1/vms/([a-z][a-z0-9-]{0,47})/launch", self.path)
        if not match:
            self._write_json(404, {"error": "unknown virtual machine"})
            return
        payload = self._read_json()
        if set(payload) - {"approved", "allow_unisolated", "allow_network", "persistent"}:
            raise ValueError("VM launch request contains unknown fields")
        if payload.get("approved") is not True or payload.get("allow_unisolated") is not True:
            raise ValueError("explicit approval for an unisolated QEMU host process is required")
        for name in ("allow_unisolated", "allow_network", "persistent"):
            if name in payload and not isinstance(payload[name], bool):
                raise ValueError(f"{name} must be a boolean")
        if payload.get("persistent", False):
            raise ValueError("persistent guest writes require the CLI and a separate local approval")
        result = self.server.manager.launch_vm(
            match.group(1),
            approved=True,
            allow_unisolated=True,
            allow_network=payload.get("allow_network", False),
        )
        self._write_json(202, {"process": result})


def serve(manager: RuntimeManager, host: str = "127.0.0.1", port: int = 47682) -> None:
    if host != "127.0.0.1":
        raise RuntimeErrorBase("the runtime bridge may bind only to 127.0.0.1")
    if not 1 <= port <= 65535:
        raise RuntimeErrorBase("bridge port must be between 1 and 65535")
    token = _load_pairing_token(manager)
    server = _RuntimeHTTPServer((host, port), RuntimeRequestHandler, manager, token)
    print("DuckOS native runtime bridge")
    print(f"Listening: http://{host}:{port}")
    print("Mora origin: http://localhost:8000 (change the local port as needed)")
    print("Pairing token (store only in the trusted local Mora session):")
    print(token)
    print("Press Ctrl+C to stop the host process manager.")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nStopping DuckOS runtime bridge.")
    finally:
        server.server_close()
