"""In-process event bus shared by DuckOS user-space services."""

from __future__ import annotations

import re
import threading
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable

from .common import ServiceError, utc_now


_EVENT_NAME = re.compile(r"^[a-z][a-z0-9_.-]{0,95}$")
Subscriber = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    sequence: int
    name: str
    source: str
    payload: dict[str, Any]
    created_at: str


class EventBus:
    """A bounded, synchronous event bus with isolated subscriber failures."""

    def __init__(self, history_limit: int = 128) -> None:
        if history_limit < 1:
            raise ValueError("history_limit must be positive")
        self._history: deque[Event] = deque(maxlen=history_limit)
        self._subscribers: dict[int, tuple[str | None, Subscriber]] = {}
        self._sequence = 0
        self._next_token = 1
        self._lock = threading.RLock()
        self.last_failures: tuple[str, ...] = ()

    def subscribe(self, callback: Subscriber, event_name: str | None = None) -> int:
        if not callable(callback):
            raise TypeError("subscriber must be callable")
        if event_name is not None and not _EVENT_NAME.fullmatch(event_name):
            raise ServiceError(f"invalid event name: {event_name!r}")

        with self._lock:
            token = self._next_token
            self._next_token += 1
            self._subscribers[token] = (event_name, callback)
            return token

    def unsubscribe(self, token: int) -> bool:
        with self._lock:
            return self._subscribers.pop(token, None) is not None

    def publish(
        self,
        name: str,
        source: str,
        payload: dict[str, Any] | None = None,
    ) -> Event:
        if not isinstance(name, str) or not _EVENT_NAME.fullmatch(name):
            raise ServiceError(f"invalid event name: {name!r}")
        if not isinstance(source, str) or not source.strip():
            raise ServiceError("event source must be non-empty text")
        if payload is not None and not isinstance(payload, dict):
            raise ServiceError("event payload must be an object")

        with self._lock:
            self._sequence += 1
            event = Event(
                sequence=self._sequence,
                name=name,
                source=source.strip(),
                payload=dict(payload or {}),
                created_at=utc_now(),
            )
            self._history.append(event)
            subscribers = tuple(self._subscribers.values())

        failures: list[str] = []
        for wanted_name, callback in subscribers:
            if wanted_name is not None and wanted_name != name:
                continue
            try:
                callback(event)
            except Exception as error:  # A bad observer must not break other services.
                failures.append(f"{type(error).__name__}: {error}")

        self.last_failures = tuple(failures)
        return event

    def history(self, event_name: str | None = None) -> list[Event]:
        with self._lock:
            events = list(self._history)
        if event_name is not None:
            events = [event for event in events if event.name == event_name]
        return events
