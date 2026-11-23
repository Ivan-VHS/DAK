"""DuckOS build, runtime discovery and host process-management commands."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .image_layout import plan_image
from .manifest import validate_manifest
from .module_abi import resolve_load_order
from .runtime import RuntimeManager, RuntimeErrorBase
from .bridge import serve as serve_runtime_bridge


def _load(path: Path) -> Any:
    try:
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("input JSON exceeds 4 MiB")
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _confirm(message: str) -> bool:
    try:
        return input(message + " Type RUN to continue: ").strip() == "RUN"
    except (EOFError, KeyboardInterrupt):
        return False


def _add_runtime_commands(commands: argparse._SubParsersAction) -> None:
    runtime = commands.add_parser("runtime", help="discover runtimes and launch imported PE/DOS applications")
    actions = runtime.add_subparsers(dest="runtime_command", required=True)

    actions.add_parser("list", help="show native PE, Wine, DOSBox, QEMU and sandbox availability")

    import_app = actions.add_parser("import", help="import a PE/DOS executable, ZIP game package or directory")
    import_app.add_argument("source", type=Path)
    import_app.add_argument("--entrypoint", help="relative executable path when a package contains multiple programs")
    import_app.add_argument("--name", help="display name shown in Mora")

    actions.add_parser("apps", help="list imported application packages and trust state")

    launch = actions.add_parser("launch", help="create a native host process for an imported application")
    launch.add_argument("app_id")
    launch.add_argument("--adapter", default="auto", choices=["auto", "native-pe", "wine", "dosbox"])
    launch.add_argument("--allow-unisolated", action="store_true", help="explicitly permit a host process without an OS sandbox")
    launch.add_argument("--allow-network", action="store_true", help="permit network access where the sandbox can enforce it")
    launch.add_argument("--yes", action="store_true", help="confirm this launch without an interactive prompt")
    launch.add_argument("arguments", nargs=argparse.REMAINDER, help="application arguments after --")

    actions.add_parser("processes", help="list processes created by this manager instance")

    stop = actions.add_parser("stop", help="terminate a process created by this manager instance")
    stop.add_argument("process_id")

    bridge = actions.add_parser("bridge", help="start an authenticated loopback API for Mora")
    bridge.add_argument("--port", type=int, default=47682)

    dxvk = actions.add_parser("dxvk-install", help="install a verified DXVK archive into one app's managed Wine prefix")
    dxvk.add_argument("app_id")
    dxvk.add_argument("archive", type=Path)
    dxvk.add_argument("--sha256", required=True, help="expected SHA-256 digest of the downloaded archive")

    vm_register = actions.add_parser("vm-register", help="register an existing QEMU guest disk image")
    vm_register.add_argument("name")
    vm_register.add_argument("disk", type=Path)
    vm_register.add_argument("--memory", type=int, default=4096, help="guest RAM in MiB (1024..65536)")
    vm_register.add_argument("--cpus", type=int, default=4, help="guest vCPU count")

    actions.add_parser("vms", help="list registered guest machines")

    vm_launch = actions.add_parser("vm-launch", help="boot an existing QEMU guest image")
    vm_launch.add_argument("name")
    vm_launch.add_argument("--allow-unisolated", action="store_true", help="explicitly permit the QEMU host process without a host sandbox")
    vm_launch.add_argument("--allow-network", action="store_true", help="attach QEMU user-mode NAT")
    vm_launch.add_argument("--persistent", action="store_true", help="write changes to the original VM disk instead of a disposable snapshot")
    vm_launch.add_argument("--yes", action="store_true", help="confirm this launch without an interactive prompt")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="duckos",
        description="DuckOS build contracts and host-side executable runtime manager.",
    )
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

    _add_runtime_commands(commands)

    try:
        args = parser.parse_args(argv)
        if args.command == "validate-manifest":
            result = validate_manifest(_load(args.manifest), args.root, verify_files=not args.metadata_only)
            _print(result)
            return 0
        if args.command == "plan-image":
            payload = _load(args.components)
            items = payload.get("components") if isinstance(payload, dict) else payload
            _print(plan_image(items, alignment_bytes=args.alignment))
            return 0
        if args.command == "module-order":
            payload = _load(args.modules)
            items = payload.get("modules") if isinstance(payload, dict) else payload
            _print({
                "schema": "duckos.module-order.v1",
                "load_order": resolve_load_order(items),
                "modules_loaded": False,
            })
            return 0

        manager = RuntimeManager()
        action = args.runtime_command
        if action == "list":
            _print(manager.capabilities())
            return 0
        if action == "import":
            _print(manager.import_app(args.source, entrypoint=args.entrypoint, display_name=args.name))
            return 0
        if action == "apps":
            _print({"apps": manager.store.list_apps()})
            return 0
        if action == "launch":
            arguments = list(args.arguments)
            if arguments and arguments[0] == "--":
                arguments.pop(0)
            approved = args.yes or _confirm(
                "Launch the untrusted imported application through the selected host runtime?"
            )
            if not approved:
                print("Launch cancelled.")
                return 1
            result = manager.launch_app(
                args.app_id,
                runtime_id=args.adapter,
                arguments=arguments,
                approved=True,
                allow_unisolated=args.allow_unisolated,
                allow_network=args.allow_network,
            )
            _print(result)
            return 0
        if action == "processes":
            _print({"processes": manager.list_processes()})
            return 0
        if action == "stop":
            _print(manager.terminate_process(args.process_id))
            return 0
        if action == "bridge":
            serve_runtime_bridge(manager, port=args.port)
            return 0
        if action == "dxvk-install":
            _print(manager.install_dxvk(args.app_id, args.archive, args.sha256))
            return 0
        if action == "vm-register":
            _print(manager.store.register_vm(
                args.name, args.disk, memory_mb=args.memory, cpus=args.cpus
            ))
            return 0
        if action == "vms":
            _print({"vms": manager.store.list_vms()})
            return 0
        if action == "vm-launch":
            approved = args.yes or _confirm(
                "Boot the registered guest machine using the selected disk and network policy?"
            )
            if not approved:
                print("VM launch cancelled.")
                return 1
            persistent_approved = False
            if args.persistent:
                persistent_approved = args.yes or _confirm(
                    "Write guest changes permanently to the original virtual disk? This cannot be undone by QEMU snapshot mode."
                )
                if not persistent_approved:
                    print("Persistent guest write cancelled.")
                    return 1
            _print(manager.launch_vm(
                args.name,
                approved=True,
                allow_unisolated=args.allow_unisolated,
                allow_network=args.allow_network,
                persistent=args.persistent,
                allow_persistent=persistent_approved,
            ))
            return 0
        raise RuntimeErrorBase(f"unknown runtime action: {action}")
    except (OSError, TypeError, ValueError, RuntimeErrorBase) as error:
        parser.exit(2, f"DuckOS operation failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
