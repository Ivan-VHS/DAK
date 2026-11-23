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
from .desktop import DesktopService, audit_desktop
from .image_layout import plan_image
from .manifest import validate_manifest
from .module_abi import resolve_load_order
from .deployment import build_release_bundle, create_deployment_plan, verify_release_bundle
from .rights import (
    RightsAuditLog, build_transfer_manifest, validate_transfer_manifest,
    verify_content_manifest, verify_entitlement, verify_licensed_content,
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


def _trusted_key_map(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        key_id, separator, key_path = value.partition("=")
        if not separator or not key_id or not key_path:
            raise ValueError("--trusted-key must use KEY_ID=/path/to/public-key.pem")
        if key_id in result:
            raise ValueError(f"duplicate trusted key id: {key_id}")
        result[key_id] = Path(key_path).expanduser()
    return result


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

    desktop = commands.add_parser("desktop", help="audit and maintain the current user's desktop workspace")
    desktop_commands = desktop.add_subparsers(dest="desktop_command", required=True)
    desktop_audit = desktop_commands.add_parser("audit", help="read-only desktop, startup and resource report")
    desktop_audit.add_argument("--item-limit", type=int, default=10)
    desktop_commands.add_parser("gui", help="open the native Duck Desktop maintenance window")
    startup = desktop_commands.add_parser("startup", help="manage reversible per-user startup entries")
    startup_commands = startup.add_subparsers(dest="startup_command", required=True)
    startup_commands.add_parser("list", help="list current-user startup entries")
    startup_disable = startup_commands.add_parser("disable", help="disable one startup entry without deleting its data")
    startup_disable.add_argument("entry_id")
    startup_restore = startup_commands.add_parser("restore", help="restore a previously disabled startup entry")
    startup_restore.add_argument("entry_id")

    release_build = commands.add_parser(
        "build-release", help="create a deterministic, optionally signed component bundle"
    )
    release_build.add_argument("manifest", type=Path)
    release_build.add_argument("root", type=Path)
    release_build.add_argument("output", type=Path)
    release_build.add_argument("--signing-key", type=Path, help="Ed25519 private key in PEM format")

    release_verify = commands.add_parser(
        "verify-release", help="verify bundle contents, SHA-256 checksums and an optional signature"
    )
    release_verify.add_argument("archive", type=Path)
    release_verify.add_argument("--public-key", type=Path, help="Ed25519 public key in PEM format")

    deployment = commands.add_parser(
        "deployment-plan", help="prepare a non-destructive USB, PXE, HTTP or cloud deployment plan"
    )
    deployment.add_argument("manifest", type=Path)
    deployment.add_argument("root", type=Path)
    deployment.add_argument("--target", choices=("usb", "pxe", "http", "cloud"), required=True)
    deployment.add_argument("--base-url", help="HTTP(S) base URL for network boot")
    deployment.add_argument("--secure-boot", action="store_true")
    deployment.add_argument(
        "--data-size-bytes", type=int, default=2 * 1024 * 1024 * 1024,
        help="planned Duck Data partition size (default: 2 GiB)",
    )
    deployment.add_argument("--output", type=Path, help="write the JSON plan to this path")


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

    rights = commands.add_parser(
        "rights", help="verify signed content entitlements, package integrity and rights audit evidence"
    )
    rights_commands = rights.add_subparsers(dest="rights_command", required=True)

    entitlement_check = rights_commands.add_parser(
        "verify-entitlement", help="verify a local Ed25519 entitlement without contacting a store"
    )
    entitlement_check.add_argument("token", type=Path)
    entitlement_check.add_argument("--trusted-key", action="append", required=True,
                                   help="trusted publisher key as KEY_ID=/path/to/public-key.pem")
    entitlement_check.add_argument("--profile-id", help="current local profile identifier")
    entitlement_check.add_argument("--device-id", help="registered DuckOS home-device identifier")
    entitlement_check.add_argument("--region", help="current region code")
    entitlement_check.add_argument("--offline", action="store_true",
                                   help="apply the signed offline-valid-until deadline")
    entitlement_check.add_argument("--action", choices=(
        "install", "launch", "download", "backup", "transfer", "stream",
        "capture_screenshot", "capture_recording", "redistribute", "modify",
    ), help="require a particular content right")
    entitlement_check.add_argument("--audit-log", type=Path,
                                   help="append the decision to the local rights audit log")

    package_check = rights_commands.add_parser(
        "verify-package", help="verify one entitlement against its exact signed manifest and package files"
    )
    package_check.add_argument("entitlement", type=Path)
    package_check.add_argument("manifest", type=Path)
    package_check.add_argument("root", type=Path)
    package_check.add_argument("--trusted-key", action="append", required=True,
                               help="trusted publisher or store key as KEY_ID=/path/to/public-key.pem")
    package_check.add_argument("--profile-id", help="current local profile identifier")
    package_check.add_argument("--device-id", help="registered DuckOS home-device identifier")
    package_check.add_argument("--region", help="current region code")
    package_check.add_argument("--offline", action="store_true",
                               help="apply the signed offline-valid-until deadline")
    package_check.add_argument("--action", choices=(
        "install", "launch", "download", "backup", "transfer", "stream",
        "capture_screenshot", "capture_recording", "redistribute", "modify",
    ), default="launch", help="required content right (defaults to launch)")

    content_check = rights_commands.add_parser(
        "verify-content", help="verify publisher signature and the exact package file set"
    )
    content_check.add_argument("manifest", type=Path)
    content_check.add_argument("root", type=Path)
    content_check.add_argument("--trusted-key", action="append", required=True,
                               help="trusted publisher key as KEY_ID=/path/to/public-key.pem")
    content_check.add_argument("--audit-log", type=Path,
                               help="append the result to the local rights audit log")

    transfer_build = rights_commands.add_parser(
        "build-transfer", help="export content, save and signed-license metadata without changing ownership"
    )
    transfer_build.add_argument("records", type=Path,
                                help="JSON object with an items array of content manifests and entitlements")
    transfer_build.add_argument("output", type=Path,
                                help="new transfer-manifest path; existing files are never overwritten")

    transfer_check = rights_commands.add_parser(
        "validate-transfer", help="check a rights-preserving metadata export without reassigning licenses"
    )
    transfer_check.add_argument("manifest", type=Path)

    audit_check = rights_commands.add_parser(
        "audit-log", help="verify the local hash-chained rights audit journal"
    )
    audit_check.add_argument("--path", type=Path, help="journal path (defaults to ~/.duckos/rights-audit.jsonl)")

    try:
        args = parser.parse_args(argv)
        if args.command == "build-release":
            result = build_release_bundle(
                _load(args.manifest),
                args.root,
                args.output,
                signing_key=args.signing_key,
            )
        elif args.command == "verify-release":
            result = verify_release_bundle(args.archive, public_key=args.public_key)
        elif args.command == "deployment-plan":
            result = create_deployment_plan(
                _load(args.manifest),
                args.root,
                target=args.target,
                base_url=args.base_url,
                secure_boot=args.secure_boot,
                data_size_bytes=args.data_size_bytes,
            )
            if args.output:
                if args.output.is_symlink():
                    raise ValueError("deployment-plan output must not be a symlink")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )
                _print_result({
                    "schema": result["schema"],
                    "written": str(args.output.resolve()),
                    "disk_written": False,
                })
                return 0
        elif args.command == "validate-manifest":
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
        elif args.command == "desktop" and args.desktop_command == "audit":
            result = audit_desktop(item_limit=args.item_limit)
        elif args.command == "desktop" and args.desktop_command == "startup" and args.startup_command == "list":
            result = {
                "schema": "duckos.startup-list.v1",
                "scope": "current_user",
                "entries": DesktopService().startup.list_entries(),
                "machine_wide_entries_included": False,
            }
        elif args.command == "desktop" and args.desktop_command == "startup" and args.startup_command in {"disable", "restore"}:
            enabled = args.startup_command == "restore"
            result = DesktopService().startup.set_enabled(args.entry_id, enabled)
        elif args.command == "desktop" and args.desktop_command == "gui":
            from .desktop.native_ui import run_native_desktop
            return run_native_desktop()
        elif args.command == "rights" and args.rights_command == "verify-package":
            result = verify_licensed_content(
                _load(args.entitlement),
                _load(args.manifest),
                args.root,
                _trusted_key_map(args.trusted_key),
                profile_id=args.profile_id,
                home_device_id=args.device_id,
                region=args.region,
                offline=args.offline,
                required_action=args.action,
            )
            RightsAuditLog().append(
                action="licensed-content.verify",
                content_id=result.get("entitlement_decision", {}).get("content_id"),
                entitlement_id=result.get("entitlement_decision", {}).get("entitlement_id"),
                status=result.get("status", "blocked"),
                reason_code=result.get("reason_code", "verification_error"),
            )
            _print_result(result)
            return 0 if result.get("allowed") else 1
        elif args.command == "rights" and args.rights_command == "verify-entitlement":
            result = verify_entitlement(
                _load(args.token),
                _trusted_key_map(args.trusted_key),
                profile_id=args.profile_id,
                home_device_id=args.device_id,
                region=args.region,
                offline=args.offline,
                required_action=args.action,
            )
            RightsAuditLog(args.audit_log).append(
                action="entitlement.verify",
                content_id=result.get("content_id"),
                entitlement_id=result.get("entitlement_id"),
                status=result.get("status", "blocked"),
                reason_code=result.get("reason_code", "verification_error"),
            )
            _print_result(result)
            return 0 if result.get("allowed") else 1
        elif args.command == "rights" and args.rights_command == "verify-content":
            result = verify_content_manifest(
                _load(args.manifest), args.root, _trusted_key_map(args.trusted_key)
            )
            RightsAuditLog(args.audit_log).append(
                action="content.verify",
                content_id=result.get("content_id"),
                entitlement_id=None,
                status="verified" if result.get("valid") else "blocked",
                reason_code=result.get("reason_code", "verification_error"),
            )
            _print_result(result)
            return 0 if result.get("valid") else 1
        elif args.command == "rights" and args.rights_command == "build-transfer":
            records = _load(args.records)
            items = records.get("items") if isinstance(records, dict) else records
            result = build_transfer_manifest(items)
            if args.output.is_symlink() or args.output.exists():
                raise ValueError("transfer output must be a new path and must not be a symlink")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
            _print_result({
                "schema": result["schema"],
                "written": str(args.output.resolve()),
                "items": len(result["items"]),
                "authorization_granted": False,
            })
            return 0
        elif args.command == "rights" and args.rights_command == "validate-transfer":
            result = validate_transfer_manifest(_load(args.manifest))
        elif args.command == "rights" and args.rights_command == "audit-log":
            result = RightsAuditLog(args.path).verify()
            _print_result(result)
            return 0 if result.get("valid") else 1
        else:
            result = compatibility_status()
        _print_result(result)
        return 0
    except (OSError, TypeError, ValueError, RuntimeError, ImportError) as error:
        parser.exit(2, f"DuckOS check failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
