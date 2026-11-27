#!/usr/bin/env python3
"""Run an AI-agent command in a network-isolated Bubblewrap sandbox."""

from __future__ import annotations

import argparse
import os
import resource
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _set_limits(cpu_seconds: int, memory_mib: int, file_size_mib: int,
                process_count: int) -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_size_mib * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))

    if hasattr(resource, "RLIMIT_NPROC"):
        resource.setrlimit(resource.RLIMIT_NPROC, (process_count, process_count))

    if hasattr(resource, "RLIMIT_AS"):
        memory_bytes = memory_mib * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))


def build_command(args: argparse.Namespace, workspace: Path, home: Path) -> list[str]:
    command = [
        args.bwrap,
        "--die-with-parent",
        "--new-session",
        "--unshare-all",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--tmpfs", "/run",
        "--dir", "/home",
        "--bind", str(home), "/home/agent",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind-try", "/bin", "/bin",
        "--ro-bind-try", "/sbin", "/sbin",
        "--ro-bind-try", "/lib", "/lib",
        "--ro-bind-try", "/lib64", "/lib64",
        "--dir", "/etc",
        "--ro-bind-try", "/etc/ld.so.cache", "/etc/ld.so.cache",
        "--ro-bind-try", "/etc/nsswitch.conf", "/etc/nsswitch.conf",
        "--ro-bind-try", "/etc/passwd", "/etc/passwd",
        "--ro-bind-try", "/etc/group", "/etc/group",
    ]

    if args.read_only:
        command.extend(["--ro-bind", str(workspace), "/workspace"])
    else:
        command.extend(["--bind", str(workspace), "/workspace"])

    command.extend([
        "--chdir", "/workspace",
        "--clearenv",
        "--setenv", "PATH", "/usr/bin:/bin",
        "--setenv", "HOME", "/home/agent",
        "--setenv", "LANG", "C.UTF-8",
        "--setenv", "TERM", "xterm-256color",
        "--",
        *args.command,
    ])
    return command


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--read-only", action="store_true",
                        help="mount the workspace read-only")
    parser.add_argument("--wall-seconds", type=int, default=300)
    parser.add_argument("--cpu-seconds", type=int, default=60)
    parser.add_argument("--memory-mib", type=int, default=2048)
    parser.add_argument("--file-size-mib", type=int, default=256)
    parser.add_argument("--process-count", type=int, default=32)
    parser.add_argument("--bwrap", default="bwrap")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.command and args.command[0] == "--":
        args.command.pop(0)

    if not args.command:
        parser.error("provide a command after --")

    if sys.platform != "linux":
        print("duck-sandbox: Bubblewrap isolation is supported on Linux only", file=sys.stderr)
        return 2

    if os.geteuid() == 0:
        print("duck-sandbox: refusing to run as root; use an unprivileged account", file=sys.stderr)
        return 2

    for value, label in (
        (args.wall_seconds, "wall-seconds"),
        (args.cpu_seconds, "cpu-seconds"),
        (args.memory_mib, "memory-mib"),
        (args.file_size_mib, "file-size-mib"),
        (args.process_count, "process-count"),
    ):
        if value <= 0:
            parser.error(f"--{label} must be positive")

    bwrap = shutil.which(args.bwrap)
    if bwrap is None:
        print("duck-sandbox: bwrap is not installed; refusing an unsandboxed fallback",
              file=sys.stderr)
        return 2
    args.bwrap = bwrap

    try:
        workspace = args.workspace.resolve(strict=True)
    except OSError as error:
        print(f"duck-sandbox: cannot resolve workspace: {error}", file=sys.stderr)
        return 2

    if not workspace.is_dir():
        print("duck-sandbox: workspace must be a directory", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="duckos-agent-") as temporary_home:
        home = Path(temporary_home)
        command = build_command(args, workspace, home)

        try:
            result = subprocess.run(
                command,
                check=False,
                timeout=args.wall_seconds,
                preexec_fn=lambda: _set_limits(
                    args.cpu_seconds,
                    args.memory_mib,
                    args.file_size_mib,
                    args.process_count,
                ),
            )
        except subprocess.TimeoutExpired:
            print("duck-sandbox: wall-clock limit exceeded", file=sys.stderr)
            return 124
        except OSError as error:
            print(f"duck-sandbox: could not start sandbox: {error}", file=sys.stderr)
            return 126

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
