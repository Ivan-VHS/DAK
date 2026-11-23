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
from .compat.bridge import (
    build_launch_plan as bridge_launch_plan,
    detect_runtimes as detect_bridge_runtimes,
    inspect_binary as inspect_bridge_binary,
)
from .hardware_inventory import collect_host_inventory
from .image_layout import plan_image
from .manifest import validate_manifest
from .module_abi import resolve_load_order
from .desktop import (
    ABUpdateManager, AuditLog, LauncherRegistry, PackageTrustStore,
    load_bench_profile, load_system_catalog, system_app_ids,
)


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
    bridge_plan.add_argument(
        "--arg", dest="arguments", action="append", default=[],
        help="append one target argument; repeat to add more than one",
    )

    desktop = commands.add_parser("desktop", help="DuckOS desktop application and bench contracts")
    desktop_commands = desktop.add_subparsers(dest="desktop_command", required=True)
    desktop_commands.add_parser("catalog", help="show the fifteen system utility applications")

    slots = desktop_commands.add_parser("slots", help="manage persistent numbered launcher slots")
    slots.add_argument("--state", type=Path, required=True, help="launcher state JSON path")
    slot_commands = slots.add_subparsers(dest="slot_action", required=True)
    slot_commands.add_parser("list", help="list all numbered slots")
    assign_slot = slot_commands.add_parser("assign", help="assign an application to a slot")
    assign_slot.add_argument("slot", type=int)
    assign_slot.add_argument("app_id")
    assign_slot.add_argument("--replace", action="store_true", help="explicitly replace an occupied slot")
    assign_slot.add_argument("--unpin", action="store_true", help="assign without pinning")
    unassign_slot = slot_commands.add_parser("unassign", help="clear a slot without shifting other slots")
    unassign_slot.add_argument("slot", type=int)
    resolve_slot = slot_commands.add_parser("resolve", help="resolve a slot to its application identity")
    resolve_slot.add_argument("slot", type=int)

    package_verify = desktop_commands.add_parser("package-verify", help="calculate SHA-256 and evaluate local package trust")
    package_verify.add_argument("file", type=Path)
    package_verify.add_argument("--trust-store", type=Path, required=True)
    package_approve = desktop_commands.add_parser("package-approve", help="approve one unsigned file by exact SHA-256")
    package_approve.add_argument("file", type=Path)
    package_approve.add_argument("--trust-store", type=Path, required=True)
    package_approve.add_argument("--confirm-unsigned", action="store_true", help="confirm this exact unsigned file")

    image_state = desktop_commands.add_parser("image-state", help="show the local A/B image-slot state")
    image_state.add_argument("--state", type=Path, required=True)

    bench_profile = desktop_commands.add_parser("bench-profile", help="validate a board-specific hardware bench profile")
    bench_profile.add_argument("file", type=Path)

    audit_verify = desktop_commands.add_parser("audit-verify", help="verify an audit/serial journal hash chain")
    audit_verify.add_argument("file", type=Path)

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
                arguments=args.arguments,
            )
        elif args.command == "desktop":
            if args.desktop_command == "catalog":
                result = load_system_catalog()
            elif args.desktop_command == "slots":
                registry = LauncherRegistry(args.state, app_ids=system_app_ids())
                if args.slot_action == "list":
                    result = {"schema": "duckos.launcher-slots.v1", "slots": registry.list_slots()}
                elif args.slot_action == "assign":
                    result = registry.assign(
                        args.slot, args.app_id, pinned=not args.unpin, replace=args.replace
                    )
                elif args.slot_action == "unassign":
                    result = {
                        "slot": args.slot,
                        "removed": registry.unassign(args.slot),
                        "other_slots_shifted": False,
                    }
                else:
                    app_id = registry.resolve(args.slot)
                    result = {
                        "slot": args.slot,
                        "app_id": app_id,
                        "launch_request": registry.prepare_launch_request(args.slot) if app_id else None,
                    }
            elif args.desktop_command == "package-verify":
                result = PackageTrustStore(args.trust_store).verify(args.file)
            elif args.desktop_command == "package-approve":
                result = PackageTrustStore(args.trust_store).approve_unsigned(
                    args.file, confirmed=args.confirm_unsigned
                )
            elif args.desktop_command == "image-state":
                result = ABUpdateManager(args.state).status()
            elif args.desktop_command == "bench-profile":
                result = {
                    "profile": load_bench_profile(args.file),
                    "hardware_access_enabled": False,
                    "native_adapter_required": True,
                }
            elif args.desktop_command == "audit-verify":
                result = AuditLog(args.file).verify()
            else:
                raise ValueError("unsupported DuckOS desktop command")
        else:
            result = compatibility_status()
        _print_result(result)
        return 0
    except (OSError, TypeError, ValueError) as error:
        parser.exit(2, f"DuckOS check failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
