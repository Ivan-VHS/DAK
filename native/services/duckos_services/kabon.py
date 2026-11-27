"""Ka-bon: context-aware keyboard chord routing with an explicit action allow-list."""

from __future__ import annotations

from collections.abc import Mapping

from .common import ServiceError


_MODIFIER_ORDER = ("Ctrl", "Alt", "Shift", "Super")
_MODIFIER_ALIASES = {
    "control": "Ctrl",
    "ctrl": "Ctrl",
    "alt": "Alt",
    "option": "Alt",
    "shift": "Shift",
    "super": "Super",
    "meta": "Super",
    "cmd": "Super",
    "command": "Super",
}
_RESERVED_CHORDS = {"Ctrl+Alt+Delete", "Alt+F4"}
_ALLOWED_ACTIONS = {
    "po.open",
    "kavun.focus.next",
    "kavun.workspace.1",
    "kavun.workspace.2",
    "illidia.snapshot.create",
    "gloverty.theme.cycle",
}


def normalize_chord(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ServiceError("keyboard chord must be non-empty text")

    parts = [part.strip() for part in value.split("+")]
    if any(not part for part in parts):
        raise ServiceError(f"invalid keyboard chord: {value!r}")

    modifiers: set[str] = set()
    key: str | None = None
    for part in parts:
        modifier = _MODIFIER_ALIASES.get(part.casefold())
        if modifier:
            modifiers.add(modifier)
        elif key is None:
            key = part.upper() if len(part) == 1 else part
        else:
            raise ServiceError("a chord may contain only one non-modifier key")

    if key is None:
        raise ServiceError("keyboard chord is missing its key")

    ordered = [name for name in _MODIFIER_ORDER if name in modifiers]
    ordered.append(key)
    return "+".join(ordered)


class InputRouter:
    """Resolve a chord in the active context, then fall back to global bindings."""

    def __init__(self, bindings: Mapping[str, Mapping[str, str]] | None = None) -> None:
        self._bindings: dict[str, dict[str, str]] = {}
        source = bindings if bindings is not None else {
            "global": {
                "Ctrl+K": "po.open",
                "Alt+Tab": "kavun.focus.next",
                "Super+1": "kavun.workspace.1",
                "Super+2": "kavun.workspace.2",
                "Ctrl+Shift+S": "illidia.snapshot.create",
                "Ctrl+Alt+T": "gloverty.theme.cycle",
            }
        }
        if not isinstance(source, Mapping):
            raise ServiceError("keyboard bindings must be an object")

        for context, context_bindings in source.items():
            if not isinstance(context_bindings, Mapping):
                raise ServiceError(f"bindings for context {context!r} must be an object")
            for chord, action in context_bindings.items():
                if not isinstance(chord, str) or not isinstance(action, str):
                    raise ServiceError("keyboard binding keys and actions must be text")
                self.bind(context, chord, action)

    def bind(self, context: str, chord: str, action: str) -> None:
        if not isinstance(context, str) or not context.strip() or len(context) > 64:
            raise ServiceError("input context must be non-empty text under 64 characters")
        normalized = normalize_chord(chord)
        if normalized in _RESERVED_CHORDS:
            raise ServiceError(f"system-reserved chord cannot be rebound: {normalized}")
        if not isinstance(action, str) or action not in _ALLOWED_ACTIONS:
            raise ServiceError(f"action is not in the Ka-bon allow-list: {action!r}")
        self._bindings.setdefault(context, {})[normalized] = action

    def unbind(self, context: str, chord: str) -> bool:
        normalized = normalize_chord(chord)
        return self._bindings.get(context, {}).pop(normalized, None) is not None

    def dispatch(self, chord: str, context: str = "global") -> str | None:
        normalized = normalize_chord(chord)
        return self._bindings.get(context, {}).get(
            normalized,
            self._bindings.get("global", {}).get(normalized),
        )

    def export(self) -> dict[str, dict[str, str]]:
        return {context: dict(bindings) for context, bindings in self._bindings.items()}
