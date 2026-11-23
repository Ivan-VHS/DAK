"""DuckOS offline build-contract, hardware-inventory and compatibility tools."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Any

from .compat import (
    compatibility_status, create_prefix, diagnose_binary,
    inspect_pe_file, plan_launch, read_prefix,
)
from .compat.bridge import (
    build_launch_plan as bridge_launch_plan,
    detect_runtimes as detect_bridge_runtimes,
    inspect_binary as inspect_bridge_binary,
)
from .compat.illidia import (
    add_game as illidia_add_game,
    list_games as illidia_list_games,
    launch_game as illidia_launch_game,
    remove_game as illidia_remove_game,
)
from .hardware_inventory import collect_host_inventory
from .image_layout import plan_image
from .manifest import validate_manifest
from .module_abi import resolve_load_order
from .shell import host_status as shell_host_status, read_app_catalog, readiness_report
from .host import CapabilityPolicy, NativeHostBroker, NativeHostClient
from .host.runtime import HostError, current_uid
from .host.server import serve_native_host


def _load(path: Path) -> Any:
    try:
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("input JSON exceeds 4 MiB")
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error


def _print_result(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="duckos", description="DuckOS build, ABI, hardware-inventory and compatibility tools.")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-manifest", help="verify a system manifest and component hashes")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("root", type=Path)
    validate.add_argument("--metadata-only", action="store_true")

    layout = commands.add_parser("plan-image", help="calculate a dry-run image partition layout")
    layout.add_argument("components", type=Path)
    layout.add_argument("--alignment", type=int, default=1024 * 1024)

    modules = commands.add_parser("module-order", help="resolve static driver module dependencies")
    modules.add_argument("modules", type=Path)

    inventory = commands.add_parser(
        "hardware-inventory", help="collect a read-only PCI/USB (Linux) or PnP (Windows) inventory"
    )
    inventory.add_argument("--output", type=Path, help="write the versioned JSON snapshot to this path")
    inventory.add_argument("--sysfs-root", type=Path, help="Linux sysfs root (defaults to /sys; useful for tests)")

    inspect = commands.add_parser("inspect-pe", help="inspect a PE32/PE32+ file without executing it")
    inspect.add_argument("file", type=Path)

    create = commands.add_parser("prefix-create", help="create an isolated Windows-prefix directory skeleton")
    create.add_argument("store", type=Path, help="directory that will contain application prefixes")
    create.add_argument("name", help="new prefix name")
    create.add_argument("--architecture", choices=("x86", "x86_64", "aarch64"), default="x86_64")

    info = commands.add_parser("prefix-info", help="validate and describe an existing compatibility prefix")
    info.add_argument("prefix", type=Path)

    diagnose = commands.add_parser("compat-diagnose", help="inspect PE imports and prefix DLL search paths")
    diagnose.add_argument("file", type=Path)
    diagnose.add_argument("--prefix", type=Path)

    launch = commands.add_parser("compat-plan", help="show launch blockers; never starts the executable")
    launch.add_argument("file", type=Path)
    launch.add_argument("--prefix", type=Path)

    commands.add_parser("compat-status", help="show implemented and pending Windows-runtime components")


    bridge = commands.add_parser(
        "bridge", help="discover compatibility runtimes and prepare non-executing launch plans"
    )
    bridge_commands = bridge.add_subparsers(dest="bridge_command", required=True)
    bridge_commands.add_parser(
        "runtimes", help="list detected Wine, Proton, CrossOver, Bottles and CPU translators"
    )
    bridge_inspect = bridge_commands.add_parser(
        "inspect", help="inspect a local PE or ELF executable without running it"
    )
    bridge_inspect.add_argument("file", type=Path)
    bridge_plan = bridge_commands.add_parser(
        "plan", help="prepare a JSON launch plan without creating a process"
    )
    bridge_plan.add_argument("file", type=Path)
    bridge_plan.add_argument("--purpose", choices=("application", "game"), default="application")
    bridge_plan.add_argument(
        "--backend", choices=("auto", "wine", "proton", "crossover", "bottles"), default="auto"
    )
    bridge_plan.add_argument("--bottle", help="name of an existing CrossOver or Bottles bottle")
    bridge_plan.add_argument("--compat-data", type=Path, help="Proton compatibility-data directory")
    bridge_plan.add_argument("--wine-prefix", type=Path, help="existing or new per-application Wine prefix")
    bridge_plan.add_argument(
        "--arg", dest="arguments", action="append", default=[],
        help="append one target argument; repeat to add more than one",
    )

    illidia = commands.add_parser(
        "illidia", help="manage and launch games through DuckBridge"
    )
    illidia_commands = illidia.add_subparsers(dest="illidia_command", required=True)

    illidia_list = illidia_commands.add_parser("list", help="list registered local games")
    illidia_list.add_argument("--library", type=Path, help="alternate library JSON path")

    illidia_add = illidia_commands.add_parser("add", help="register an existing PE or ELF game executable")
    illidia_add.add_argument("file", type=Path)
    illidia_add.add_argument("--name", help="display name for the game")
    illidia_add.add_argument("--id", dest="game_id", help="stable lowercase game identifier")
    illidia_add.add_argument(
        "--backend", choices=("auto", "wine", "proton", "crossover", "bottles"), default="auto"
    )
    illidia_add.add_argument("--bottle", help="existing CrossOver or Bottles bottle name")
    illidia_add.add_argument("--library", type=Path, help="alternate library JSON path")
    illidia_add.add_argument(
        "--arg", dest="arguments", action="append", default=[],
        help="save one target argument; repeat to add more than one",
    )

    illidia_remove = illidia_commands.add_parser("remove", help="remove a game from the library")
    illidia_remove.add_argument("game_id")
    illidia_remove.add_argument("--library", type=Path, help="alternate library JSON path")

    illidia_launch = illidia_commands.add_parser("launch", help="start a registered game")
    illidia_launch.add_argument("game_id")
    illidia_launch.add_argument(
        "--backend", choices=("auto", "wine", "proton", "crossover", "bottles"),
        help="override the saved compatibility backend",
    )
    illidia_launch.add_argument("--bottle", help="override the saved CrossOver or Bottles bottle")
    illidia_launch.add_argument("--library", type=Path, help="alternate library JSON path")
    illidia_launch.add_argument("--compatibility-root", type=Path, help="per-game Wine/Proton data directory")
    illidia_launch.add_argument(
        "--arg", dest="arguments", action="append", default=[],
        help="append one target argument; repeat to add more than one",
    )
    illidia_launch.add_argument("--gamemode", action="store_true", help="wrap the launch with GameMode")
    illidia_launch.add_argument("--mangohud", action="store_true", help="show MangoHud telemetry")
    illidia_launch.add_argument("--wined3d", action="store_true", help="use Proton's WineD3D fallback instead of DXVK/VKD3D")
    illidia_launch.add_argument("--no-esync", action="store_true", help="disable Proton esync")
    illidia_launch.add_argument("--no-fsync", action="store_true", help="disable Proton fsync")
    illidia_launch.add_argument("--wait", action="store_true", help="wait for the game and return its exit code")

    shell = commands.add_parser(
        "shell", help="inspect the Mora desktop shell and current host without changing the system"
    )
    shell_commands = shell.add_subparsers(dest="shell_command", required=True)
    shell_commands.add_parser("status", help="show real host information and native desktop boundaries")
    shell_commands.add_parser("apps", help="list the local Mora application catalogue")
    shell_verify = shell_commands.add_parser("verify", help="check shell source wiring and Reaper runtime availability")
    shell_verify.add_argument("--root", type=Path, help="DuckOS project root")
    shell_verify.add_argument("--catalogue", type=Path, help="alternate Mora app catalogue JSON")

    host = commands.add_parser("host", help="native host broker, sessions, safe terminal, drivers and Reaper bridge")
    host_commands = host.add_subparsers(dest="host_command", required=True)
    host_status = host_commands.add_parser("status", help="show native host and Reaper runtime availability")
    host_status.add_argument("--socket", type=Path, help="query a running broker over its Unix socket")

    host_sessions = host_commands.add_parser("sessions", help="list processes managed by the running host broker")
    host_sessions.add_argument("--socket", type=Path, default=Path("/run/duckos/host.sock"))

    host_start = host_commands.add_parser("session-start", help="start an allowlisted native application")
    host_start.add_argument("application_id")
    host_start.add_argument("--socket", type=Path, default=Path("/run/duckos/host.sock"))

    host_stop = host_commands.add_parser("session-stop", help="stop a session owned by the caller")
    host_stop.add_argument("session_id")
    host_stop.add_argument("--socket", type=Path, default=Path("/run/duckos/host.sock"))

    host_serve = host_commands.add_parser("serve", help="serve native host requests over a Unix socket")
    host_serve.add_argument("--socket", type=Path, default=Path("/run/duckos/host.sock"))
    host_serve.add_argument("--policy", type=Path, default=Path("/etc/duckos/host-policy.json"))
    host_serve.add_argument("--http-host", choices=("127.0.0.1", "::1"))
    host_serve.add_argument("--http-port", type=int, default=8765)
    host_serve.add_argument("--token-file", type=Path)
    host_serve.add_argument("--origin", action="append", default=[])
    host_serve.add_argument("--socket-mode", type=lambda value: int(value, 8), default=0o660)
    host_serve.add_argument("--socket-gid", type=int)

    host_policy = host_commands.add_parser("policy-init", help="create an initial UID capability policy")
    host_policy.add_argument("--path", type=Path, default=Path("host-policy.json"))
    host_policy.add_argument("--uid", type=int, default=current_uid())
    host_policy.add_argument("--grant", action="append", default=[
        "host.read", "session.read", "session.spawn", "session.stop",
        "terminal.safe", "driver.inspect", "reaper.evaluate",
    ])

    host_token = host_commands.add_parser("token-create", help="create a Mora bridge token; raw token is shown once")
    host_token.add_argument("--path", type=Path, default=Path("bridge-tokens.json"))
    host_token.add_argument("--uid", type=int, default=current_uid())

    host_terminal = host_commands.add_parser("terminal", help="execute one fixed diagnostic command")
    host_terminal.add_argument("command_id", choices=("system", "date", "uptime", "memory", "storage", "processes", "network", "home"))
    host_terminal.add_argument("--socket", type=Path, help="run through a privileged host broker")

    host_driver = host_commands.add_parser("drivers", help="inspect safe Linux driver availability")
    host_driver.add_argument("--load", nargs=2, metavar=("CATEGORY", "MODULE"))
    host_driver.add_argument("--socket", type=Path, help="run through a privileged host broker")

    host_reaper = host_commands.add_parser("reaper", help="inspect or evaluate an allowlisted Reaper contract")
    host_reaper.add_argument("--contract", choices=(
        "capability.permits", "desktop.command_policy",
        "desktop.session_transition", "window.transition",
    ))
    host_reaper.add_argument("--arguments", type=Path, help="JSON object with contract arguments")
    host_reaper.add_argument("--socket", type=Path, help="run through a native host broker")


    try:
        args = parser.parse_args(argv)
        if args.command == "validate-manifest":
            result = validate_manifest(_load(args.manifest), args.root, verify_files=not args.metadata_only)
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
        elif args.command == "hardware-inventory":
            result = collect_host_inventory(sysfs_root=args.sysfs_root)
            encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            if args.output:
                args.output.write_text(encoded, encoding="utf-8", newline="\n")
            else:
                print(encoded, end="")
            return 0
        elif args.command == "inspect-pe":
            result = inspect_pe_file(args.file)
        elif args.command == "prefix-create":
            result = create_prefix(args.store, args.name, architecture=args.architecture)
        elif args.command == "prefix-info":
            result = read_prefix(args.prefix)
        elif args.command == "compat-diagnose":
            result = diagnose_binary(args.file, args.prefix)
        elif args.command == "compat-plan":
            result = plan_launch(args.file, args.prefix)
        elif args.command == "bridge" and args.bridge_command == "runtimes":
            result = detect_bridge_runtimes()
        elif args.command == "bridge" and args.bridge_command == "inspect":
            result = inspect_bridge_binary(args.file)
        elif args.command == "bridge" and args.bridge_command == "plan":
            result = bridge_launch_plan(
                args.file,
                purpose=args.purpose,
                backend=args.backend,
                bottle=args.bottle,
                compat_data=args.compat_data,
                wine_prefix=args.wine_prefix,
                arguments=args.arguments,
            )
        elif args.command == "illidia" and args.illidia_command == "list":
            result = illidia_list_games(library_path=args.library)
        elif args.command == "illidia" and args.illidia_command == "add":
            result = illidia_add_game(
                args.file, name=args.name, game_id=args.game_id,
                backend=args.backend, bottle=args.bottle,
                arguments=args.arguments, library_path=args.library,
            )
        elif args.command == "illidia" and args.illidia_command == "remove":
            result = illidia_remove_game(args.game_id, library_path=args.library)
        elif args.command == "illidia" and args.illidia_command == "launch":
            result = illidia_launch_game(
                args.game_id, backend=args.backend, bottle=args.bottle,
                arguments=args.arguments, library_path=args.library,
                compatibility_root=args.compatibility_root,
                use_gamemode=args.gamemode, use_mangohud=args.mangohud,
                use_wined3d=args.wined3d, disable_esync=args.no_esync,
                disable_fsync=args.no_fsync, wait=args.wait,
            )
        elif args.command == "shell" and args.shell_command == "status":
            result = shell_host_status()
        elif args.command == "shell" and args.shell_command == "apps":
            result = read_app_catalog()
        elif args.command == "host" and args.host_command == "status":
            if args.socket:
                result = NativeHostClient(args.socket).call("host.status")
            else:
                broker = NativeHostBroker()
                result = {
                    "schema": "duckos.host-status.v1",
                    "host": broker.dispatch(current_uid(), {"id": "status", "method": "host.status"})["result"],
                    "drivers": broker.dispatch(current_uid(), {"id": "drivers", "method": "driver.list"})["result"],
                    "reaper": broker.reaper.status(),
                }
        elif args.command == "host" and args.host_command == "sessions":
            result = NativeHostClient(args.socket).call("session.list")
        elif args.command == "host" and args.host_command == "session-start":
            result = NativeHostClient(args.socket).call("session.start", {"application_id": args.application_id})
        elif args.command == "host" and args.host_command == "session-stop":
            result = NativeHostClient(args.socket).call("session.stop", {"session_id": args.session_id})
        elif args.command == "host" and args.host_command == "policy-init":
            from .host.config import write_policy
            result = write_policy(args.path, args.uid, args.grant)
        elif args.command == "host" and args.host_command == "token-create":
            from .host.config import create_bridge_token
            result = create_bridge_token(args.path, args.uid)
        elif args.command == "host" and args.host_command == "terminal":
            if args.socket:
                result = NativeHostClient(args.socket).call("terminal.run", {"command_id": args.command_id})
            else:
                broker = NativeHostBroker()
                result = broker.dispatch(current_uid(), {
                    "id": "terminal", "method": "terminal.run",
                    "params": {"command_id": args.command_id},
                })["result"]
        elif args.command == "host" and args.host_command == "drivers":
            method = "driver.load" if args.load else "driver.inventory"
            params = {"category": args.load[0], "module": args.load[1]} if args.load else {}
            if args.socket:
                result = NativeHostClient(args.socket).call(method, params)
            else:
                broker = NativeHostBroker()
                result = broker.dispatch(current_uid(), {
                    "id": "drivers", "method": method, "params": params,
                })["result"]
        elif args.command == "host" and args.host_command == "reaper":
            if not args.contract:
                if args.socket:
                    result = NativeHostClient(args.socket).call("reaper.status")
                else:
                    result = NativeHostBroker().reaper.status()
            else:
                arguments = _load(args.arguments) if args.arguments else {}
                params = {"contract": args.contract, "arguments": arguments}
                if args.socket:
                    result = NativeHostClient(args.socket).call("reaper.evaluate", params)
                else:
                    broker = NativeHostBroker()
                    result = broker.dispatch(current_uid(), {
                        "id": "reaper", "method": "reaper.evaluate", "params": params,
                    })["result"]
        elif args.command == "host" and args.host_command == "serve":
            policy = CapabilityPolicy.load(args.policy) if args.policy.exists() else CapabilityPolicy.for_current_user()
            broker = NativeHostBroker(policy)
            serve_native_host(
                broker,
                socket_path=args.socket,
                http_host=args.http_host,
                http_port=args.http_port,
                token_file=args.token_file,
                origins=set(args.origin) if args.origin else None,
                socket_mode=args.socket_mode,
                socket_gid=args.socket_gid,
            )
            return 0
        else:
            result = compatibility_status()
        _print_result(result)
        return 0
    except (OSError, TypeError, ValueError) as error:
        parser.exit(2, f"DuckOS check failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
