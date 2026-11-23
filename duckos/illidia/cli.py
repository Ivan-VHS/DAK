"""Command-line tools for the Illidia local game library."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .library import (
    IllidiaError,
    IllidiaLibrary,
    discover_stores,
    import_store_discovery,
    scan_custom_directories,
)
from .launcher import (
    LaunchError,
    inspect_game,
    launch_game,
    refresh_sessions,
    stop_launch,
)


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise IllidiaError(f"cannot read JSON file {path}: {error}") from error


def _write(path: Path, payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(encoded, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="illidia",
        description="Manage a local game library and prepare controlled launches.",
    )
    parser.add_argument("--database", type=Path, help="SQLite library path")
    commands = parser.add_subparsers(dest="command", required=True)

    discover = commands.add_parser("discover", help="inspect installed Steam, Epic and GOG metadata")
    discover.add_argument("--import-stores", action="store_true", help="import discovered entries into the library")

    scan = commands.add_parser("scan", help="scan user-selected directories without running files")
    scan.add_argument("directories", nargs="+", type=Path)
    scan.add_argument("--add", action="store_true", help="add every found executable to the library")

    add = commands.add_parser("add", help="add a custom executable")
    add.add_argument("name")
    add.add_argument("executable", type=Path)
    add.add_argument("--source", choices=("steam", "epic", "gog", "battlenet", "ea", "custom"), default="custom")
    add.add_argument("--external-id")
    add.add_argument("--arg", dest="arguments", action="append", default=[])
    add.add_argument("--working-directory", type=Path)
    add.add_argument("--runtime", choices=("native", "wine", "proton", "crossover", "bottles", "qemu"), default="native")
    add.add_argument("--runtime-command", action="append", default=[])
    add.add_argument("--prefix", type=Path)
    add.add_argument("--tag", action="append", default=[])

    listing = commands.add_parser("list", help="list and filter library entries")
    listing.add_argument("--search")
    listing.add_argument("--source", choices=("steam", "epic", "gog", "battlenet", "ea", "custom"))
    listing.add_argument("--installed", action="store_true")
    listing.add_argument("--missing", action="store_true")
    listing.add_argument("--tag")

    inspect = commands.add_parser("inspect", help="inspect launch path, signature and fingerprint")
    inspect.add_argument("game_id")

    profile = commands.add_parser("profile", help="replace one game's launch profile from JSON")
    profile.add_argument("game_id")
    profile.add_argument("json_file", type=Path)

    launch = commands.add_parser("launch", help="launch through a store or a direct executable")
    launch.add_argument("game_id")
    launch.add_argument("--confirm-unverified", action="store_true",
                        help="approve this exact SHA-256 for first launch when unsigned/unverified")
    launch.add_argument("--update-fingerprint", action="store_true",
                        help="save the current SHA-256; a changed hash does not otherwise block launch")
    launch.add_argument("--direct", action="store_true",
                        help="launch the configured binary instead of the official store client")
    launch.add_argument("--wait", action="store_true",
                        help="wait for the direct process and run configured post-launch hooks")

    sessions = commands.add_parser("sessions", help="show known direct and store-delegated sessions")

    stop = commands.add_parser("stop", help="request stop for a directly launched process group")
    stop.add_argument("launch_id")
    stop.add_argument("--force", action="store_true", help="use forceful process-tree termination")

    remove = commands.add_parser("remove", help="remove a library record")
    remove.add_argument("game_id")
    remove.add_argument("--yes", action="store_true", help="confirm removal of the library record")

    export = commands.add_parser("export", help="export the library to a portable JSON file")
    export.add_argument("destination", type=Path)

    import_cmd = commands.add_parser("import", help="import a versioned Illidia library JSON file")
    import_cmd.add_argument("source", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        library = IllidiaLibrary(args.database)

        if args.command == "discover":
            discovery = discover_stores()
            if args.import_stores:
                discovery["imported"] = import_store_discovery(library, discovery)
            _print(discovery)
        elif args.command == "scan":
            candidates = scan_custom_directories(args.directories)
            if args.add:
                added = [library.add_game(**candidate).as_dict() for candidate in candidates]
                _print({"found": len(candidates), "added": len(added), "games": added})
            else:
                _print({"found": len(candidates), "candidates": candidates, "added": False})
        elif args.command == "add":
            game = library.add_game(
                name=args.name,
                source=args.source,
                external_id=args.external_id,
                executable_path=args.executable,
                arguments=args.arguments,
                working_directory=args.working_directory,
                runtime=args.runtime,
                runtime_command=args.runtime_command,
                runtime_prefix=args.prefix,
                tags=["custom", *args.tag],
                metadata={"launch_mode": "direct", "install_path": str(args.executable.expanduser().parent)},
            )
            _print(game.as_dict())
        elif args.command == "list":
            installed = True if args.installed else False if args.missing else None
            _print([game.as_dict() for game in library.list_games(
                search=args.search, source=args.source, installed=installed, tag=args.tag
            )])
        elif args.command == "inspect":
            game = library.get_game(args.game_id)
            _print(inspect_game(library, game))
        elif args.command == "profile":
            profile_data = _load(args.json_file)
            if not isinstance(profile_data, dict):
                raise IllidiaError("launch profile must be a JSON object")
            _print(library.set_launch_profile(args.game_id, profile_data).as_dict())
        elif args.command == "launch":
            _print(launch_game(
                library,
                args.game_id,
                confirm_unverified=args.confirm_unverified,
                update_fingerprint=args.update_fingerprint,
                direct=args.direct,
                wait=args.wait,
            ))
        elif args.command == "sessions":
            _print(refresh_sessions(library))
        elif args.command == "stop":
            _print(stop_launch(library, args.launch_id, force=args.force))
        elif args.command == "remove":
            if not args.yes:
                raise IllidiaError("record removal requires --yes; game files are never deleted")
            library.remove_game(args.game_id)
            _print({"removed": args.game_id, "game_files_deleted": False})
        elif args.command == "export":
            _write(args.destination, library.export_library())
            _print({"exported": len(library.list_games()), "path": str(args.destination)})
        elif args.command == "import":
            imported = library.import_library(_load(args.source))
            _print({"imported": imported})
        return 0
    except (IllidiaError, OSError, ValueError, TypeError, TimeoutError) as error:
        print(f"Illidia: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
