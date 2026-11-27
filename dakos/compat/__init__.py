"""Dak Windows compatibility foundation (inspection and prefix tooling)."""

from .pe import PEFormatError, inspect_pe_bytes, inspect_pe_file
from .prefix import PrefixError, create_prefix, read_prefix
from .runtime import compatibility_status, diagnose_binary, plan_launch

__all__ = [
    "PEFormatError", "PrefixError", "compatibility_status", "create_prefix",
    "diagnose_binary", "inspect_pe_bytes", "inspect_pe_file", "plan_launch",
    "read_prefix",
]
