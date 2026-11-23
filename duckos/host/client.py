"""Unix-domain client for the local DuckOS native host broker."""
from __future__ import annotations

import json
from pathlib import Path
import socket
from typing import Any

from .runtime import HostError, MAX_REQUEST_BYTES


class NativeHostClient:
    """Send one bounded JSON-RPC request over a peer-credentialled socket."""

    def __init__(self, socket_path: str | Path, *, timeout: float = 5.0) -> None:
        self.socket_path = Path(socket_path)
        self.timeout = timeout

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request = {
            "id": 1,
            "method": method,
            "params": params or {},
        }
        encoded = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(encoded) > MAX_REQUEST_BYTES:
            raise HostError("native host request exceeds 64 KiB")
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection.settimeout(self.timeout)
        try:
            connection.connect(str(self.socket_path))
            connection.sendall(encoded)
            received = bytearray()
            while len(received) <= MAX_REQUEST_BYTES:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                received.extend(chunk)
                if b"\n" in chunk:
                    break
        except OSError as error:
            raise HostError(f"cannot communicate with DuckOS host socket {self.socket_path}: {error}") from error
        finally:
            connection.close()
        if len(received) > MAX_REQUEST_BYTES or b"\n" not in received:
            raise HostError("native host response is incomplete or too large")
        try:
            response = json.loads(bytes(received).split(b"\n", 1)[0].decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise HostError(f"native host returned invalid JSON: {error}") from error
        if not isinstance(response, dict):
            raise HostError("native host response must be a JSON object")
        if response.get("error"):
            error = response["error"]
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise HostError(message or "native host request was denied")
        if "result" not in response:
            raise HostError("native host response has no result")
        return response["result"]
