"""Cockos: a PipeWire graph controller for system-wide audio routing.

This module controls ports and links. It does not claim to provide a kernel audio
driver, a DSP host, sample-rate conversion, or guaranteed zero-latency playback.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

from .common import ServiceError


@dataclass(frozen=True)
class AudioPort:
    name: str
    direction: str


class AudioBackendUnavailable(ServiceError):
    """PipeWire's command-line graph controller is not installed or reachable."""


class AudioBackendError(ServiceError):
    """PipeWire rejected an audio graph operation."""


class PipeWireAudioBus:
    """Safely list and connect PipeWire ports without invoking a shell."""

    _DIRECTIONS = {"outputs": "-o", "inputs": "-i", "links": "-l"}

    def __init__(
        self,
        executable: str = "pw-link",
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.executable = executable
        self._runner = runner

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def _run(self, arguments: Sequence[str]) -> str:
        try:
            result = self._runner(
                [self.executable, *arguments],
                check=False,
                capture_output=True,
                text=True,
                timeout=4,
            )
        except FileNotFoundError as error:
            raise AudioBackendUnavailable(
                f"{self.executable} is not installed; install PipeWire tools first"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise AudioBackendError("PipeWire did not answer within four seconds") from error
        except OSError as error:
            raise AudioBackendError(f"could not contact PipeWire: {error}") from error

        if result.returncode != 0:
            message = (result.stderr or result.stdout or "unknown PipeWire error").strip()
            raise AudioBackendError(message)
        return result.stdout or ""

    def list(self, direction: str) -> list[str]:
        try:
            option = self._DIRECTIONS[direction]
        except KeyError as error:
            raise ServiceError("direction must be outputs, inputs, or links") from error

        output = self._run([option])
        return [line.strip() for line in output.splitlines() if line.strip()]

    def connect(self, output_port: str, input_port: str) -> dict[str, str]:
        output_port = output_port.strip()
        input_port = input_port.strip()
        if not output_port or not input_port or "\0" in output_port + input_port:
            raise ServiceError("both audio port names must be non-empty")
        if output_port == input_port:
            raise ServiceError("an audio port cannot be linked to itself")

        outputs = self.list("outputs")
        inputs = self.list("inputs")
        if output_port not in outputs:
            raise ServiceError(f"output port does not exist: {output_port}")
        if input_port not in inputs:
            raise ServiceError(f"input port does not exist: {input_port}")

        self._run([output_port, input_port])
        return {"output": output_port, "input": input_port, "status": "linked"}

    def disconnect(self, output_port: str, input_port: str) -> dict[str, str]:
        output_port = output_port.strip()
        input_port = input_port.strip()
        if not output_port or not input_port or "\0" in output_port + input_port:
            raise ServiceError("both audio port names must be non-empty")
        self._run(["-d", output_port, input_port])
        return {"output": output_port, "input": input_port, "status": "disconnected"}
