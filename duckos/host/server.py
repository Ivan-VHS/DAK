"""Local Unix-socket and loopback HTTP transports for the native host broker."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import hmac
import json
import os
from pathlib import Path
import socket
import socketserver
import stat
import struct
import threading
from typing import Any
from urllib.parse import urlsplit

from .runtime import HostError, MAX_REQUEST_BYTES, NativeHostBroker

MAX_HTTP_BODY = 64 * 1024


def _read_tokens(path: str | Path) -> dict[str, int]:
    token_path = Path(path)
    if token_path.is_symlink() or not token_path.is_file():
        raise HostError(f"bridge token file is missing or is a symbolic link: {token_path}")
    mode = stat.S_IMODE(token_path.stat().st_mode)
    if mode & 0o077:
        raise HostError("bridge token file must not be readable or writable by group/other")
    try:
        payload = json.loads(token_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise HostError(f"cannot read bridge token file: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema") != "duckos.bridge-tokens.v1":
        raise HostError("bridge token file has an unsupported schema")
    records = payload.get("tokens")
    if not isinstance(records, dict) or len(records) > 32:
        raise HostError("bridge token registry is malformed")
    result: dict[str, int] = {}
    for digest, uid in records.items():
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise HostError("bridge token registry contains an invalid digest")
        if isinstance(uid, bool) or not isinstance(uid, int) or uid < 0:
            raise HostError("bridge token registry contains an invalid UID")
        result[digest] = uid
    return result


def _peer_uid(connection: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise HostError("peer credential inspection is unavailable on this host")
    raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    _pid, uid, _gid = struct.unpack("3i", raw)
    return uid


class _UnixRequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            uid = _peer_uid(self.request)
            line = self.rfile.readline(MAX_REQUEST_BYTES + 1)
            if len(line) > MAX_REQUEST_BYTES or not line.endswith(b"\n"):
                raise HostError("RPC message is incomplete or too large")
            payload = json.loads(line.decode("utf-8"))
            response = self.server.broker.dispatch(uid, payload)
        except (HostError, UnicodeError, json.JSONDecodeError, OSError) as error:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": str(error)[:1024]},
            }
        try:
            encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
            self.wfile.write(encoded[:MAX_REQUEST_BYTES])
        except OSError:
            return


class UnixHostServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, socket_path: str | Path, broker: NativeHostBroker, *, mode: int = 0o660, gid: int | None = None):
        self.socket_path = Path(socket_path)
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        if self.socket_path.is_symlink():
            raise HostError("refusing to replace a symbolic-link socket path")
        if self.socket_path.exists():
            if not self.socket_path.is_socket():
                raise HostError("refusing to replace a non-socket path")
            self.socket_path.unlink()
        self.broker = broker
        super().__init__(str(self.socket_path), _UnixRequestHandler)
        os.chmod(self.socket_path, mode)
        if gid is not None:
            os.chown(self.socket_path, -1, gid)

    def server_close(self) -> None:
        try:
            super().server_close()
        finally:
            try:
                if self.socket_path.is_socket():
                    self.socket_path.unlink()
            except OSError:
                pass


class _BridgeHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, broker: NativeHostBroker, tokens: dict[str, int], origins: set[str]):
        self.broker = broker
        self.tokens = tokens
        self.origins = origins
        super().__init__(address, _BridgeRequestHandler)


class _BridgeRequestHandler(BaseHTTPRequestHandler):
    server: _BridgeHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _origin(self) -> str | None:
        origin = self.headers.get("Origin")
        return origin if origin in self.server.origins else None

    def _valid_host(self) -> bool:
        host = self.headers.get("Host", "")
        parsed = urlsplit("//" + host)
        return parsed.hostname in {"127.0.0.1", "localhost", "::1"}

    def _headers(self, status: int, *, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        origin = self._origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(self._body_length))
        self.end_headers()

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._body_length = len(body)
        self._headers(status)
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        requested_method = self.headers.get("Access-Control-Request-Method", "")
        requested_headers = {
            value.strip().lower()
            for value in self.headers.get("Access-Control-Request-Headers", "").split(",")
            if value.strip()
        }
        if (
            self.path != "/v1/rpc"
            or not self._valid_host()
            or self._origin() is None
            or requested_method != "POST"
            or not requested_headers.issubset({"authorization", "content-type"})
        ):
            self._send(403, {"error": "origin, host, path or preflight method is not allowed"})
            return
        self._body_length = 0
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self._origin())
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Max-Age", "300")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path != "/health" or not self._valid_host():
            self._send(404, {"error": "not found"})
            return
        self._send(200, {"service": "duckos-native-host", "status": "ready", "authenticated": False})

    def do_POST(self) -> None:
        if self.path != "/v1/rpc" or not self._valid_host() or self._origin() is None:
            self._send(403, {"error": "origin, host or path is not allowed"})
            return
        authorization = self.headers.get("Authorization", "")
        if not authorization.startswith("Bearer ") or len(authorization) > 256:
            self._send(401, {"error": "bearer token required"})
            return
        supplied = hashlib.sha256(authorization[7:].encode("utf-8")).hexdigest()
        uid = next((value for digest, value in self.server.tokens.items() if hmac.compare_digest(digest, supplied)), None)
        if uid is None:
            self._send(401, {"error": "invalid bridge token"})
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self._send(415, {"error": "application/json is required"})
            return
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdigit() or int(raw_length) > MAX_HTTP_BODY:
            self._send(413, {"error": "request body is missing or too large"})
            return
        try:
            payload = json.loads(self.rfile.read(int(raw_length)).decode("utf-8"))
            result = self.server.broker.dispatch(uid, payload)
        except (HostError, UnicodeError, json.JSONDecodeError, OSError) as error:
            self._send(400, {"error": str(error)[:1024]})
            return
        self._send(200, result)


def serve_native_host(
    broker: NativeHostBroker,
    *,
    socket_path: str | Path,
    http_host: str | None = None,
    http_port: int = 8765,
    token_file: str | Path | None = None,
    origins: set[str] | None = None,
    socket_mode: int = 0o660,
    socket_gid: int | None = None,
) -> None:
    """Run the local UDS broker and, optionally, the authenticated Mora bridge."""
    unix_server = UnixHostServer(socket_path, broker, mode=socket_mode, gid=socket_gid)
    http_server = None
    http_thread = None
    if http_host is not None:
        if http_host not in {"127.0.0.1", "::1"}:
            unix_server.server_close()
            raise HostError("HTTP bridge must bind to a loopback address")
        if token_file is None:
            unix_server.server_close()
            raise HostError("HTTP bridge requires a protected token file")
        try:
            tokens = _read_tokens(token_file)
            http_server = _BridgeHTTPServer(
                (http_host, http_port), broker, tokens,
                origins or {"http://127.0.0.1:8760", "http://localhost:8760"},
            )
        except Exception:
            unix_server.server_close()
            raise
        http_thread = threading.Thread(target=http_server.serve_forever, name="duckos-http-bridge", daemon=True)
        http_thread.start()
    try:
        unix_server.serve_forever()
    finally:
        unix_server.server_close()
        if http_server is not None:
            http_server.shutdown()
            http_server.server_close()
        if http_thread is not None:
            http_thread.join(timeout=2)
