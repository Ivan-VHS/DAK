"""Command-line entry point for DuckOS user-space services."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .common import ServiceError
from .gloverty import audit_palette
from .news import NewsService, serve_api
from .kavun import compute_layout
from .unify import PROFILES, DuckOSHub


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path.home() / ".local" / "state" / "duckos",
        help="directory for DuckOS session state",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("status", help="show subsystem availability")

    audio = commands.add_parser("audio", help="inspect and manage PipeWire links")
    audio_commands = audio.add_subparsers(dest="audio_command", required=True)
    ports = audio_commands.add_parser("ports")
    ports.add_argument("direction", choices=("outputs", "inputs", "links"), default="outputs", nargs="?")
    connect = audio_commands.add_parser("connect")
    connect.add_argument("output")
    connect.add_argument("input")
    disconnect = audio_commands.add_parser("disconnect")
    disconnect.add_argument("output")
    disconnect.add_argument("input")

    layout = commands.add_parser("layout", help="compute a Kavun screen layout")
    layout.add_argument("--width", type=int, required=True)
    layout.add_argument("--height", type=int, required=True)
    layout.add_argument("--mode", choices=("main-stack", "columns", "grid", "floating"), default="main-stack")
    layout.add_argument("--windows", required=True, help="JSON array of window objects")
    layout.add_argument("--ratio", type=float, default=0.62)

    theme = commands.add_parser("theme", help="inspect Gloverty palettes")
    theme.add_argument("action", choices=("audit",))
    theme.add_argument("--name", choices=("dark", "light", "high-contrast"), default="dark")

    snapshot = commands.add_parser("snapshot", help="manage Illidia session checkpoints")
    snapshot_commands = snapshot.add_subparsers(dest="snapshot_command", required=True)
    save = snapshot_commands.add_parser("save")
    save.add_argument("--label", default="CLI checkpoint")
    snapshot_commands.add_parser("list")
    restore = snapshot_commands.add_parser("restore")
    restore.add_argument("snapshot_id")

    profile = commands.add_parser("profile", help="switch coordinated workspace profiles")
    profile_commands = profile.add_subparsers(dest="profile_command", required=True)
    profile_commands.add_parser("list")
    select = profile_commands.add_parser("set")
    select.add_argument("name", choices=tuple(PROFILES))

    po = commands.add_parser("po", help="search and run registered DuckOS commands")
    po_commands = po.add_subparsers(dest="po_command", required=True)
    search = po_commands.add_parser("search")
    search.add_argument("query", nargs="?", default="")
    run = po_commands.add_parser("run")
    run.add_argument("command_id")
    run.add_argument("--arguments", default="{}", help="JSON object passed to the handler")
    run.add_argument("--confirm", action="store_true", help="confirm a destructive action")

    shortcuts = commands.add_parser("shortcuts", help="inspect and route Ka-bon shortcuts")
    shortcut_commands = shortcuts.add_subparsers(dest="shortcut_command", required=True)
    shortcut_commands.add_parser("list")
    bind = shortcut_commands.add_parser("bind")
    bind.add_argument("context")
    bind.add_argument("chord")
    bind.add_argument("action")
    dispatch = shortcut_commands.add_parser("dispatch")
    dispatch.add_argument("chord")
    dispatch.add_argument("--context", default="global")

    news = commands.add_parser("news", help="run the DuckOS live news desk")
    news_commands = news.add_subparsers(dest="news_command", required=True)
    news_commands.add_parser("status", help="show feed and cache status")
    news_commands.add_parser("refresh", help="refresh all trusted public feeds")
    serve = news_commands.add_parser("serve", help="run the loopback JSON API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "news":
            news_service = NewsService(args.state_dir)
            if args.news_command == "status":
                _print(news_service.status())
            elif args.news_command == "refresh":
                _print(news_service.refresh())
            else:
                serve_api(news_service, args.host, args.port)
            return 0

        if args.command == "theme":
            _print(audit_palette(args.name))
            return 0

        if args.command == "layout":
            windows = json.loads(args.windows)
            _print(compute_layout(
                args.width,
                args.height,
                windows,
                mode=args.mode,
                ratio=args.ratio,
            ))
            return 0

        hub = DuckOSHub(args.state_dir)

        if args.command == "status":
            _print(hub.status())
        elif args.command == "audio":
            if args.audio_command == "ports":
                _print(hub.audio.list(args.direction))
            elif args.audio_command == "connect":
                _print(hub.audio.connect(args.output, args.input))
            else:
                _print(hub.audio.disconnect(args.output, args.input))
        elif args.command == "snapshot":
            if args.snapshot_command == "save":
                _print(hub.create_snapshot(args.label))
            elif args.snapshot_command == "list":
                _print(hub.snapshots.list())
            else:
                _print(hub.restore_snapshot(args.snapshot_id))
        elif args.command == "profile":
            if args.profile_command == "list":
                _print(PROFILES)
            else:
                _print(hub.switch_profile(args.name))
        elif args.command == "po":
            if args.po_command == "search":
                _print(hub.commands.search(args.query))
            else:
                arguments = json.loads(args.arguments)
                if not isinstance(arguments, dict):
                    raise ServiceError("Po command arguments must be a JSON object")
                _print(hub.run_command(
                    args.command_id,
                    arguments,
                    confirmed=args.confirm,
                ))
        elif args.command == "shortcuts":
            if args.shortcut_command == "list":
                _print(hub.input.export())
            elif args.shortcut_command == "bind":
                hub.bind_shortcut(args.context, args.chord, args.action)
                _print(hub.input.export())
            else:
                _print(hub.dispatch_shortcut(args.chord, args.context) or {
                    "status": "unbound",
                    "chord": args.chord,
                    "context": args.context,
                })
        return 0
    except (ServiceError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"duckos-services: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
