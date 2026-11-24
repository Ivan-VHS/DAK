"""DuckOS CLI commands for Jora."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
from .catalog import catalog_payload
from .engine import build_application, validate_package, write_package

def add_commands(commands:Any)->None:
    parser=commands.add_parser("jora",help="compose formulas and generate Jora source packages")
    actions=parser.add_subparsers(dest="jora_action",required=True)
    actions.add_parser("catalog",help="print the current Jora parameter seed registry")
    create=actions.add_parser("create",help="generate a source package from a component formula")
    create.add_argument("--formula",required=True,help="composition formula, for example: text editor + audio editor + translator")
    create.add_argument("--name",help="optional display name override")
    create.add_argument("--output",required=True,type=Path,help="new output directory or .zip archive")
    validate=actions.add_parser("validate",help="validate package paths, hashes and optional Reaper syntax")
    validate.add_argument("package",type=Path)
    validate.add_argument("--skip-reaper-check",action="store_true",help="validate package without probing Reaper")

def run_command(args:argparse.Namespace)->dict[str,Any]:
    if args.jora_action=="catalog": return catalog_payload()
    if args.jora_action=="create":
        application=build_application(args.formula,requested_name=args.name)
        result=write_package(application,args.output)
        result.update({"schema":"jora.package-creation.v1","formula":application["manifest"]["formula"]["canonical"],"languages":application["languages"],"build_status":"source_generated_not_compiled"})
        return result
    if args.jora_action=="validate": return validate_package(args.package,check_reaper=not args.skip_reaper_check)
    raise ValueError("unknown Jora action")
