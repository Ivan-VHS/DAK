"""DuckOS local build, ABI and compatibility command line."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import compatibility
from .image_layout import plan_image
from .manifest import validate_manifest
from .module_abi import resolve_load_order


def _load(path: Path) -> Any:
    try:
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("input JSON exceeds 4 MiB")
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error


def _compatibility_command(args: argparse.Namespace) -> dict[str, Any]:
    if args.compat_action == "status":
        return compatibility.compatibility_status()
    if args.compat_action == "prefixes":
        return compatibility.list_prefixes()
    if args.compat_action == "create-prefix":
        return compatibility.create_prefix(args.name, args.arch)
    if args.compat_action == "install-component":
        return compatibility.install_component(args.prefix, args.component)
    if args.compat_action == "launch":
        arguments = list(args.arguments)
        if arguments and arguments[0] == "--":
            arguments.pop(0)
        return compatibility.launch_program(
            args.executable,
            engine=args.engine,
            prefix=args.prefix,
            compat_data=args.compat_data,
            arguments=arguments,
        )
    raise ValueError("unknown compatibility operation")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="duckos",
        description="DuckOS local image, module and compatibility tools.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser(
        "validate-manifest", help="verify a system manifest and component hashes"
    )
    validate.add_argument("manifest", type=Path)
    validate.add_argument("root", type=Path)
    validate.add_argument("--metadata-only", action="store_true")

    layout = commands.add_parser(
        "plan-image", help="calculate a dry-run image partition layout"
    )
    layout.add_argument("components", type=Path)
    layout.add_argument("--alignment", type=int, default=1024 * 1024)

    modules = commands.add_parser(
        "module-order", help="resolve static driver module dependencies"
    )
    modules.add_argument("modules", type=Path)

    compat = commands.add_parser(
        "compatibility", help="inspect and operate installed Windows/DOS compatibility runtimes"
    )
    compat_commands = compat.add_subparsers(dest="compat_action", required=True)
    compat_commands.add_parser("status", help="detect host runtimes, launchers and graphics tools")
    compat_commands.add_parser("prefixes", help="list managed Wine prefixes")

    create = compat_commands.add_parser("create-prefix", help="initialize a managed Wine prefix")
    create.add_argument("--name", required=True)
    create.add_argument("--arch", choices=("win32", "win64"), default="win64")

    component = compat_commands.add_parser(
        "install-component", help="install an allowlisted Winetricks component"
    )
    component.add_argument("--prefix", required=True)
    component.add_argument(
        "--component",
        required=True,
        choices=sorted(compatibility.COMPONENTS),
    )

    launch = compat_commands.add_parser(
        "launch", help="start an executable through Wine, Proton or DOSBox"
    )
    launch.add_argument("--engine", choices=("wine", "proton", "dosbox"), default="wine")
    launch.add_argument("--prefix", help="managed Wine prefix name")
    launch.add_argument("--compat-data", type=Path, help="existing Steam compatdata directory for Proton")
    launch.add_argument("executable", type=Path)
    launch.add_argument("arguments", nargs=argparse.REMAINDER)

    try:
        args = parser.parse_args(argv)
        if args.command == "validate-manifest":
            result = validate_manifest(
                _load(args.manifest), args.root, verify_files=not args.metadata_only
            )
        elif args.command == "plan-image":
            payload = _load(args.components)
            items = payload.get("components") if isinstance(payload, dict) else payload
            result = plan_image(items, alignment_bytes=args.alignment)
        elif args.command == "module-order":
            payload = _load(args.modules)
            items = payload.get("modules") if isinstance(payload, dict) else payload
            result = {
                "schema": "duckos.module-order.v1",
                "load_order": resolve_load_order(items),
                "modules_loaded": False,
            }
        else:
            result = _compatibility_command(args)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, TypeError, ValueError) as error:
        parser.exit(2, f"DuckOS check failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
