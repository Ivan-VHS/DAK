"""DuckOS Windows compatibility foundation (inspection and prefix tooling)."""

from .pe import PEFormatError, inspect_pe_bytes, inspect_pe_file
from .prefix import PrefixError, create_prefix, read_prefix
from .runtime import compatibility_status, diagnose_binary, plan_launch
from .upstream import (
    RuntimeError as UpstreamRuntimeError,
    build_launch_plan,
    create_runtime_environment,
    detect_runtimes,
    launch_application,
    recommend_runtime,
    runtime_status,
)

__all__ = [
    "PEFormatError", "PrefixError", "compatibility_status", "create_prefix",
    "diagnose_binary", "inspect_pe_bytes", "inspect_pe_file", "plan_launch",
    "read_prefix", "UpstreamRuntimeError", "build_launch_plan",
    "create_runtime_environment", "detect_runtimes", "launch_application",
    "recommend_runtime", "runtime_status",
]
