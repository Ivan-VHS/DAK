"""Po: a searchable, permission-aware command registry.

Po never evaluates strings as shell commands. Every executable action must be
registered by a trusted DuckOS service and destructive actions require a
separate confirmation at the call site.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from .common import ServiceError


_COMMAND_ID = re.compile(r"^[a-z][a-z0-9_.-]{1,95}$")
CommandHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class Command:
    identifier: str
    title: str
    description: str
    handler: CommandHandler
    destructive: bool = False


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(
        self,
        identifier: str,
        title: str,
        description: str,
        handler: CommandHandler,
        *,
        destructive: bool = False,
    ) -> None:
        if not isinstance(identifier, str) or not _COMMAND_ID.fullmatch(identifier):
            raise ServiceError(f"invalid command id: {identifier!r}")
        if identifier in self._commands:
            raise ServiceError(f"command is already registered: {identifier}")
        if not callable(handler):
            raise ServiceError("command handler must be callable")
        if not title.strip() or not description.strip():
            raise ServiceError("command title and description are required")

        self._commands[identifier] = Command(
            identifier=identifier,
            title=title.strip(),
            description=description.strip(),
            handler=handler,
            destructive=destructive,
        )

    def search(self, query: str = "", limit: int = 12) -> list[dict[str, str]]:
        if limit < 1 or limit > 100:
            raise ServiceError("search limit must be between 1 and 100")
        terms = query.casefold().split()
        ranked: list[tuple[int, Command]] = []

        for command in self._commands.values():
            haystack = f"{command.identifier} {command.title} {command.description}".casefold()
            if not all(term in haystack for term in terms):
                continue

            score = 0
            if command.identifier.casefold().startswith(query.casefold()):
                score += 4
            if command.title.casefold().startswith(query.casefold()):
                score += 3
            if query and query.casefold() in command.title.casefold():
                score += 2
            ranked.append((score, command))

        ranked.sort(key=lambda item: (-item[0], item[1].title.casefold()))
        return [
            {
                "id": command.identifier,
                "title": command.title,
                "description": command.description,
                "requires_confirmation": str(command.destructive).lower(),
            }
            for _, command in ranked[:limit]
        ]

    def execute(
        self,
        identifier: str,
        arguments: dict[str, Any] | None = None,
        *,
        confirmed: bool = False,
    ) -> Any:
        try:
            command = self._commands[identifier]
        except KeyError as error:
            raise ServiceError(f"unknown command: {identifier}") from error

        if command.destructive and not confirmed:
            return {
                "status": "confirmation-required",
                "command": command.identifier,
                "message": f"Confirm action: {command.title}",
            }

        payload = arguments or {}
        if not isinstance(payload, dict):
            raise ServiceError("command arguments must be an object")
        return command.handler(payload)

    def describe(self) -> list[dict[str, str]]:
        return self.search("")
