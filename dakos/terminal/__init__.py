"""Extended DuckOS terminal with an allowlisted command registry."""

from .service import (
    CommandRegistry,
    CommandSpec,
    TerminalInputError,
    TerminalService,
    run_interactive,
)

__all__ = [
    "CommandRegistry",
    "CommandSpec",
    "TerminalInputError",
    "TerminalService",
    "run_interactive",
]
