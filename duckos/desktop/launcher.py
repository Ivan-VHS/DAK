"""Persistent number slots and shell-free launch request creation."""
from __future__ import annotations

from datetime import datetime, timezone
import re
from pathlib import Path
from typing import Iterable
import uuid

from .storage import read_json_state, write_json_state

SCHEMA = "duckos.launcher-slots.v1"
REQUEST_SCHEMA = "duckos.launch-request.v1"
_APP_ID = re.compile(r"^[a-z][a-z0-9-]{1,63}$")


class LauncherError(ValueError):
    """Raised when a launcher slot or application assignment is invalid."""


class LauncherRegistry:
    def __init__(
        self,
        state_file: str | Path,
        *,
        app_ids: Iterable[str],
        slot_count: int = 15,
    ) -> None:
        if isinstance(slot_count, bool) or not isinstance(slot_count, int) or not 1 <= slot_count <= 128:
            raise LauncherError("slot_count must be an integer from 1 to 128")
        known_ids = set(app_ids)
        if not known_ids or any(not isinstance(item, str) or not _APP_ID.fullmatch(item) for item in known_ids):
            raise LauncherError("app_ids must contain valid application identifiers")
        self.state_file = Path(state_file).expanduser()
        self.app_ids = known_ids
        self.slot_count = slot_count
        self._default = {"schema": SCHEMA, "version": 1, "slot_count": slot_count, "slots": {}}
        self._read()

    def _read(self) -> dict:
        state = read_json_state(self.state_file, self._default)
        if (
            state.get("schema") != SCHEMA
            or state.get("version") != 1
            or state.get("slot_count") != self.slot_count
            or not isinstance(state.get("slots"), dict)
        ):
            raise LauncherError("launcher state has an unsupported schema or slot count")
        for key, item in state["slots"].items():
            if not isinstance(key, str) or not key.isdigit() or not 1 <= int(key) <= self.slot_count:
                raise LauncherError(f"invalid launcher slot key: {key}")
            if (
                not isinstance(item, dict)
                or set(item) != {"app_id", "pinned", "shortcut"}
                or not isinstance(item.get("app_id"), str)
                or item["app_id"] not in self.app_ids
                or not isinstance(item["pinned"], bool)
                or not isinstance(item["shortcut"], str)
            ):
                raise LauncherError(f"invalid launcher assignment in slot {key}")
        assigned = [item["app_id"] for item in state["slots"].values()]
        if len(assigned) != len(set(assigned)):
            raise LauncherError("one application cannot occupy multiple numbered slots")
        return state

    def list_slots(self) -> list[dict]:
        state = self._read()
        return [
            {
                "slot": slot,
                "app_id": state["slots"].get(str(slot), {}).get("app_id"),
                "pinned": state["slots"].get(str(slot), {}).get("pinned", False),
                "shortcut": state["slots"].get(str(slot), {}).get("shortcut"),
            }
            for slot in range(1, self.slot_count + 1)
        ]

    def assign(self, slot: int, app_id: str, *, pinned: bool = True, replace: bool = False) -> dict:
        if isinstance(slot, bool) or not isinstance(slot, int) or not 1 <= slot <= self.slot_count:
            raise LauncherError(f"slot must be an integer from 1 to {self.slot_count}")
        if app_id not in self.app_ids:
            raise LauncherError(f"unknown system application: {app_id}")
        if not isinstance(pinned, bool) or not isinstance(replace, bool):
            raise LauncherError("pinned and replace must be booleans")

        state = self._read()
        key = str(slot)
        current = state["slots"].get(key)
        if current and current["app_id"] != app_id and not replace:
            raise LauncherError(f"slot {slot} is already assigned; use replace=True explicitly")
        for other_key, assignment in state["slots"].items():
            if other_key != key and assignment["app_id"] == app_id:
                raise LauncherError(f"{app_id} is already assigned to slot {other_key}")

        record = {
            "app_id": app_id,
            "pinned": pinned,
            "shortcut": f"Super+{slot}",
        }
        state["slots"][key] = record
        write_json_state(self.state_file, state)
        return {"slot": slot, **record}

    def unassign(self, slot: int) -> bool:
        if isinstance(slot, bool) or not isinstance(slot, int) or not 1 <= slot <= self.slot_count:
            raise LauncherError(f"slot must be an integer from 1 to {self.slot_count}")
        state = self._read()
        removed = state["slots"].pop(str(slot), None) is not None
        if removed:
            write_json_state(self.state_file, state)
        return removed

    def resolve(self, slot: int) -> str | None:
        if isinstance(slot, bool) or not isinstance(slot, int) or not 1 <= slot <= self.slot_count:
            raise LauncherError(f"slot must be an integer from 1 to {self.slot_count}")
        return self._read()["slots"].get(str(slot), {}).get("app_id")

    def prepare_launch_request(self, slot: int) -> dict:
        app_id = self.resolve(slot)
        if app_id is None:
            raise LauncherError(f"slot {slot} is empty")
        return {
            "schema": REQUEST_SCHEMA,
            "request_id": uuid.uuid4().hex,
            "slot": slot,
            "app_id": app_id,
            "requested_at_utc": datetime.now(timezone.utc).isoformat(),
            "dispatch": "native-launcher-service-required",
            "process_created": False,
            "shell_command_created": False,
        }
