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
from .terminal import TerminalService, run_interactive
from .settings import SettingsStore, network_probe
from .toolbox import (
    convert_json_xml, convert_text_encoding, convert_units, generate_secret,
    inspect_csv, list_listening_ports, read_rss, sha256_file, text_statistics, verify_tls,
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

    terminal = commands.add_parser(
        "terminal", help="open the separate DuckOS extended terminal"
    )
    terminal_actions = terminal.add_subparsers(dest="terminal_action")
    terminal_run = terminal_actions.add_parser(
        "run", help="run one quoted command through the trusted terminal registry"
    )
    terminal_run.add_argument("command_line", help="one terminal command, for example 'hardware inventory'")

    settings = commands.add_parser("settings", help="inspect and manage user-scoped Duck settings")
    settings_actions = settings.add_subparsers(dest="settings_action", required=True)
    settings_actions.add_parser("show", help="show the active settings profile")
    settings_export = settings_actions.add_parser("export", help="export validated settings to JSON")
    settings_export.add_argument("output", type=Path)
    settings_import = settings_actions.add_parser("import", help="validate and import settings from JSON")
    settings_import.add_argument("source", type=Path)
    profiles = settings_actions.add_parser("profile", help="manage configuration profiles")
    profile_actions = profiles.add_subparsers(dest="profile_action", required=True)
    profile_actions.add_parser("list", help="list saved profile names")
    profile_create = profile_actions.add_parser("create", help="create a copy of an existing profile")
    profile_create.add_argument("name")
    profile_create.add_argument("--clone-from")
    profile_activate = profile_actions.add_parser("activate", help="select the active settings profile")
    profile_activate.add_argument("name")
    network_test = settings_actions.add_parser("network-test", help="resolve a host and test a TCP endpoint")
    network_test.add_argument("host")
    network_test.add_argument("--port", type=int, default=443)

    toolbox = commands.add_parser("tools", help="run bounded, safe user-space utilities")
    toolbox_actions = toolbox.add_subparsers(dest="tool_action", required=True)
    secret = toolbox_actions.add_parser("secret", help="generate a cryptographically random secret")
    secret.add_argument("--length", type=int, default=32)
    text_stats = toolbox_actions.add_parser("text-stats", help="count words, characters, lines and paragraphs")
    text_stats.add_argument("file", type=Path)
    csv_inspect = toolbox_actions.add_parser("csv-inspect", help="inspect CSV headers, row widths and preview")
    csv_inspect.add_argument("file", type=Path)
    csv_inspect.add_argument("--delimiter", default=",")
    data_convert = toolbox_actions.add_parser("data-convert", help="convert JSON to XML or XML to JSON")
    data_convert.add_argument("file", type=Path)
    data_convert.add_argument("--to", choices=("json", "xml"), required=True)
    data_convert.add_argument("--output", type=Path)
    encoding = toolbox_actions.add_parser("encoding-convert", help="convert a text file encoding and line endings")
    encoding.add_argument("file", type=Path)
    encoding.add_argument("output", type=Path)
    encoding.add_argument("--from-encoding", dest="source_encoding", required=True)
    encoding.add_argument("--to-encoding", dest="target_encoding", required=True)
    encoding.add_argument("--line-endings", choices=("preserve", "lf", "crlf", "cr"), default="preserve")
    units = toolbox_actions.add_parser("units", help="convert common SI, time, data and temperature units")
    units.add_argument("value")
    units.add_argument("source_unit")
    units.add_argument("target_unit")
    tls = toolbox_actions.add_parser("tls-check", help="verify a remote TLS endpoint using system trust")
    tls.add_argument("host")
    tls.add_argument("--port", type=int, default=443)
    rss = toolbox_actions.add_parser("rss", help="parse a local RSS or Atom feed")
    rss.add_argument("file", type=Path)
    checksum = toolbox_actions.add_parser("sha256", help="calculate SHA-256 for a regular file")
    checksum.add_argument("file", type=Path)
    toolbox_actions.add_parser("ports", help="list listening TCP ports using a local read-only provider")

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


    reaper = commands.add_parser(
        "reaper", help="open and inspect the Reaper language workbench"
    )
    reaper.add_argument("--root", type=Path, help="explicit Reaper source checkout (defaults to projects/reaper)")
    reaper_commands = reaper.add_subparsers(dest="reaper_command", required=True)
    reaper_commands.add_parser("status", help="inspect the local Reaper checkout and integrated features")
    reaper_commands.add_parser("studio", help="open the native Reaper Studio window")
    reaper_check = reaper_commands.add_parser("check", help="parse and statically check a .rpr/.most file")
    reaper_check.add_argument("source", type=Path)
    reaper_typecheck = reaper_commands.add_parser("typecheck", help="run the focused Reaper type diagnostics")
    reaper_typecheck.add_argument("source", type=Path)

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
        elif args.command == "terminal":
            if args.terminal_action is None:
                return run_interactive(TerminalService())
            if args.terminal_action == "run":
                result = TerminalService().execute(args.command_line)
            else:
                raise ValueError("unsupported terminal action")
        elif args.command == "tools":
            if args.tool_action == "secret":
                result = {"secret": generate_secret(args.length), "length": args.length, "algorithm": "OS CSPRNG"}
            elif args.tool_action == "text-stats":
                if args.file.is_symlink() or not args.file.is_file() or args.file.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError("Text input must be a regular file no larger than 4 MiB")
                result = text_statistics(args.file.read_text(encoding="utf-8"))
            elif args.tool_action == "csv-inspect":
                if args.file.is_symlink() or not args.file.is_file() or args.file.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError("CSV input must be a regular file no larger than 4 MiB")
                result = inspect_csv(args.file.read_text(encoding="utf-8"), delimiter=args.delimiter)
            elif args.tool_action == "data-convert":
                if args.file.is_symlink() or not args.file.is_file() or args.file.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError("Data input must be a regular file no larger than 4 MiB")
                converted = convert_json_xml(args.file.read_text(encoding="utf-8"), args.to)
                if args.output:
                    if args.output.is_symlink():
                        raise ValueError("Output path cannot be a symbolic link")
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(converted + "\n", encoding="utf-8", newline="\n")
                    result = {"converted": True, "output": str(args.output), "format": args.to}
                else:
                    print(converted)
                    return 0
            elif args.tool_action == "encoding-convert":
                if args.file.is_symlink() or not args.file.is_file() or args.file.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError("Encoding input must be a regular file no larger than 4 MiB")
                if args.output.is_symlink():
                    raise ValueError("Output path cannot be a symbolic link")
                output_bytes = convert_text_encoding(args.file.read_bytes(), args.source_encoding, args.target_encoding, line_endings=args.line_endings)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_bytes(output_bytes)
                result = {"converted": True, "output": str(args.output), "size_bytes": len(output_bytes)}
            elif args.tool_action == "units":
                result = {"value": args.value, "source_unit": args.source_unit, "target_unit": args.target_unit, "result": convert_units(args.value, args.source_unit, args.target_unit)}
            elif args.tool_action == "tls-check":
                result = verify_tls(args.host, args.port)
            elif args.tool_action == "rss":
                if args.file.is_symlink() or not args.file.is_file() or args.file.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError("Feed input must be a regular file no larger than 4 MiB")
                result = read_rss(args.file.read_text(encoding="utf-8"))
            elif args.tool_action == "sha256":
                result = sha256_file(args.file)
            elif args.tool_action == "ports":
                result = list_listening_ports()
            else:
                raise ValueError("unsupported toolbox action")
        elif args.command == "settings":
            store = SettingsStore()
            if args.settings_action == "show":
                result = store.load()
            elif args.settings_action == "export":
                result = store.export_to(args.output)
            elif args.settings_action == "import":
                result = store.import_from(args.source)
            elif args.settings_action == "profile" and args.profile_action == "list":
                result = {"schema": "duckos.settings-profiles.v1", "active": store.load()["active_profile"], "profiles": store.list_profiles()}
            elif args.settings_action == "profile" and args.profile_action == "create":
                result = store.create_profile(args.name, clone_from=args.clone_from)
            elif args.settings_action == "profile" and args.profile_action == "activate":
                result = store.activate_profile(args.name)
            elif args.settings_action == "network-test":
                result = network_probe(args.host, args.port)
            else:
                raise ValueError("unsupported settings action")
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
        elif args.command == "reaper":
            from .desktop.reaper import ReaperWorkbench

            workbench = ReaperWorkbench(args.root)
            if args.reaper_command == "status":
                result = workbench.inspect()
            elif args.reaper_command == "studio":
                process = workbench.open_studio()
                result = {
                    "schema": "duckos.reaper-studio-launch.v1",
                    "started": True,
                    "pid": process.pid,
                    "repository": str(workbench.repository_root),
                    "shell": False,
                }
            elif args.reaper_command == "check":
                result = workbench.check(args.source)
                _print_result(result)
                return 0 if result["ok"] else 1
            elif args.reaper_command == "typecheck":
                result = workbench.typecheck(args.source)
                _print_result(result)
                return 0 if result["ok"] else 1
            else:
                raise ValueError("unknown Reaper workbench command")
        else:
            result = compatibility_status()
        _print_result(result)
        return 0
    except (OSError, TypeError, ValueError, RuntimeError, ImportError) as error:
        parser.exit(2, f"DuckOS check failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
