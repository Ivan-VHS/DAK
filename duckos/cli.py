"""DuckOS offline build-contract, hardware-inventory and compatibility tools."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .compat import (
    compatibility_status, create_prefix, diagnose_binary,
    inspect_pe_file, plan_launch, read_prefix,
)
from . import compatibility as host_compatibility
from .hardware_inventory import collect_host_inventory
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

    compat = commands.add_parser(
        "compatibility", help="run installed Wine/Proton/DOS compatibility tools on a Linux host"
    )
    compat_commands = compat.add_subparsers(dest="compat_action", required=True)
    compat_commands.add_parser("status", help="detect host runtimes, launchers and graphics tools")
    compat_commands.add_parser("prefixes", help="list DuckOS-managed Wine prefixes")

    manager = compat_commands.add_parser(
        "open-manager", help="open an installed third-party compatibility manager"
    )
    manager.add_argument(
        "--name", required=True, choices=sorted(host_compatibility.MANAGER_COMMANDS)
    )

    vm_disk = compat_commands.add_parser(
        "create-reactos-disk", help="create a qcow2 virtual disk for a separate ReactOS guest"
    )
    vm_disk.add_argument("--path", type=Path, required=True)
    vm_disk.add_argument("--size-gib", type=int, default=16)

    vm = compat_commands.add_parser(
        "launch-reactos", help="boot a user-supplied ReactOS installation in QEMU"
    )
    vm.add_argument("--disk", type=Path, required=True)
    vm.add_argument("--iso", type=Path, help="optional ReactOS installation ISO")
    vm.add_argument("--memory-mib", type=int, default=2048)
    vm.add_argument("--cpus", type=int, default=2)

    create_runtime_prefix = compat_commands.add_parser(
        "create-prefix", help="initialize a real Wine prefix with wineboot"
    )
    create_runtime_prefix.add_argument("--name", required=True)
    create_runtime_prefix.add_argument("--arch", choices=("win32", "win64"), default="win64")

    component = compat_commands.add_parser(
        "install-component", help="install an allowlisted Winetricks component"
    )
    component.add_argument("--prefix", required=True)
    component.add_argument(
        "--component", required=True, choices=sorted(host_compatibility.COMPONENTS)
    )

    run = compat_commands.add_parser(
        "launch", help="launch a file through Wine, Steam Proton or DOSBox"
    )
    run.add_argument("--engine", choices=("wine", "proton", "dosbox"), default="wine")
    run.add_argument("--prefix", help="DuckOS-managed Wine prefix name")
    run.add_argument("--compat-data", type=Path, help="existing Steam compatdata directory for Proton")
    run.add_argument("executable", type=Path)
    run.add_argument("arguments", nargs=argparse.REMAINDER)

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
        elif args.command == "compatibility":
            if args.compat_action == "status":
                result = host_compatibility.compatibility_status()
            elif args.compat_action == "prefixes":
                result = host_compatibility.list_prefixes()
            elif args.compat_action == "open-manager":
                result = host_compatibility.open_manager(args.name)
            elif args.compat_action == "create-reactos-disk":
                result = host_compatibility.create_reactos_disk(args.path, args.size_gib)
            elif args.compat_action == "launch-reactos":
                result = host_compatibility.launch_reactos(
                    args.disk, iso=args.iso, memory_mib=args.memory_mib, cpus=args.cpus
                )
            elif args.compat_action == "create-prefix":
                result = host_compatibility.create_prefix(args.name, args.arch)
            elif args.compat_action == "install-component":
                result = host_compatibility.install_component(args.prefix, args.component)
            elif args.compat_action == "launch":
                arguments = list(args.arguments)
                if arguments and arguments[0] == "--":
                    arguments.pop(0)
                result = host_compatibility.launch_program(
                    args.executable,
                    engine=args.engine,
                    prefix=args.prefix,
                    compat_data=args.compat_data,
                    arguments=arguments,
                )
            else:
                raise ValueError("unknown compatibility operation")
        else:
            result = compatibility_status()
        _print_result(result)
        return 0
    except (OSError, TypeError, ValueError) as error:
        parser.exit(2, f"DuckOS check failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
