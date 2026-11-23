"""DuckOS compatibility, runtime orchestration and Illidia game-launch tools."""

from .illidia import add_game, launch_game, list_games, remove_game
from .pe import PEFormatError, inspect_pe_bytes, inspect_pe_file
from .prefix import PrefixError, create_prefix, read_prefix
from .runtime import compatibility_status, diagnose_binary, plan_launch

__all__ = [
    "PEFormatError", "PrefixError", "add_game", "compatibility_status",
    "create_prefix", "diagnose_binary", "inspect_pe_bytes", "inspect_pe_file",
    "launch_game", "list_games", "plan_launch", "read_prefix", "remove_game",
]
