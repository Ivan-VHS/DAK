"""Transactional state machine for signed A/B image updates.

Physical image writes and boot-target changes are delegated to a native backend.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, Any

from .packages import SignatureEvidence, sha256_file
from .storage import read_json_state, write_json_state

SCHEMA = "duckos.image-slots.v1"


class ABUpdateError(ValueError):
    """Raised when an A/B update transition is invalid or cannot be completed."""


class ImageSlotBackend(Protocol):
    def write_slot(self, slot: str, image_path: Path, expected_sha256: str) -> None: ...
    def verify_slot(self, slot: str, expected_sha256: str) -> bool | str: ...
    def set_next_boot(self, slot: str) -> None: ...


def _empty_state() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "version": 1,
        "active_slot": "A",
        "confirmed_slot": "A",
        "pending_slot": None,
        "slots": {
            "A": {"state": "confirmed", "image_version": None, "sha256": None},
            "B": {"state": "empty", "image_version": None, "sha256": None},
        },
    }


class ABUpdateManager:
    def __init__(self, state_file: str | Path, backend: ImageSlotBackend | None = None) -> None:
        self.state_file = Path(state_file).expanduser()
        self.backend = backend
        self._read()

    def _read(self) -> dict[str, Any]:
        state = read_json_state(self.state_file, _empty_state())
        if (
            state.get("schema") != SCHEMA
            or state.get("version") != 1
            or state.get("active_slot") not in {"A", "B"}
            or state.get("confirmed_slot") not in {"A", "B"}
            or state.get("pending_slot") not in (None, "A", "B")
            or not isinstance(state.get("slots"), dict)
            or set(state["slots"]) != {"A", "B"}
        ):
            raise ABUpdateError("A/B image state has an unsupported schema")
        for slot, record in state["slots"].items():
            if (
                not isinstance(record, dict)
                or record.get("state") not in {"confirmed", "empty", "pending", "rollback", "failed"}
                or record.get("image_version") is not None and not isinstance(record.get("image_version"), str)
                or record.get("sha256") is not None and (
                    not isinstance(record.get("sha256"), str)
                    or len(record["sha256"]) != 64
                    or any(char not in "0123456789abcdef" for char in record["sha256"])
                )
            ):
                raise ABUpdateError(f"invalid image metadata for slot {slot}")
        if state["pending_slot"] is not None and state["slots"][state["pending_slot"]]["state"] != "pending":
            raise ABUpdateError("pending_slot must point to a pending image record")
        return state

    def status(self) -> dict[str, Any]:
        return self._read()

    def plan_update(
        self,
        image_path: str | Path,
        *,
        target_slot: str,
        image_version: str,
        expected_sha256: str,
        signature: SignatureEvidence | None,
    ) -> dict[str, Any]:
        state = self._read()
        if target_slot not in {"A", "B"}:
            raise ABUpdateError("target_slot must be A or B")
        if target_slot == state["active_slot"] or target_slot == state["confirmed_slot"]:
            raise ABUpdateError("updates may only target the inactive, unconfirmed slot")
        if state["pending_slot"] is not None:
            raise ABUpdateError("another image update is already pending")
        if not isinstance(image_version, str) or not image_version.strip() or len(image_version) > 128:
            raise ABUpdateError("image_version must contain 1..128 characters")
        if signature is None or not signature.verified:
            raise ABUpdateError("A/B image activation requires verified signature evidence")
        size, actual = sha256_file(image_path)
        if actual != expected_sha256:
            raise ABUpdateError("staged image SHA-256 does not match the expected digest")
        return {
            "schema": "duckos.image-update-plan.v1",
            "target_slot": target_slot,
            "image_version": image_version,
            "sha256": actual,
            "size_bytes": size,
            "signer_key_id": signature.key_id,
            "write_required": True,
            "boot_target_change_required": True,
            "write_performed": False,
            "boot_target_changed": False,
        }

    def activate(
        self,
        image_path: str | Path,
        *,
        target_slot: str,
        image_version: str,
        expected_sha256: str,
        signature: SignatureEvidence | None,
    ) -> dict[str, Any]:
        plan = self.plan_update(
            image_path,
            target_slot=target_slot,
            image_version=image_version,
            expected_sha256=expected_sha256,
            signature=signature,
        )
        if self.backend is None:
            raise ABUpdateError("no native image-slot backend is configured; only dry-run planning is available")

        previous = self._read()
        source = Path(image_path).expanduser().resolve(strict=True)
        self.backend.write_slot(target_slot, source, expected_sha256)
        verified = self.backend.verify_slot(target_slot, expected_sha256)
        if verified is not True and verified != expected_sha256:
            raise ABUpdateError("native backend did not verify the written image slot")

        updated = self._read()
        updated["slots"][target_slot] = {
            "state": "pending",
            "image_version": image_version,
            "sha256": expected_sha256,
        }
        updated["pending_slot"] = target_slot
        write_json_state(self.state_file, updated)
        try:
            self.backend.set_next_boot(target_slot)
        except Exception as error:
            write_json_state(self.state_file, previous)
            try:
                self.backend.set_next_boot(previous["confirmed_slot"])
            except Exception:
                pass
            raise ABUpdateError(f"could not set the next boot slot; state was rolled back: {error}") from error

        return {
            **plan,
            "write_performed": True,
            "boot_target_changed": True,
            "pending_slot": target_slot,
        }

    def confirm_boot(self, slot: str) -> dict[str, Any]:
        state = self._read()
        if slot not in {"A", "B"} or state["pending_slot"] != slot:
            raise ABUpdateError("only the pending slot can be confirmed")
        state["active_slot"] = slot
        state["confirmed_slot"] = slot
        state["pending_slot"] = None
        state["slots"][slot]["state"] = "confirmed"
        other = "B" if slot == "A" else "A"
        if state["slots"][other]["state"] == "confirmed":
            state["slots"][other]["state"] = "rollback"
        write_json_state(self.state_file, state)
        return state

    def record_boot_failure(self, slot: str) -> dict[str, Any]:
        state = self._read()
        if state["pending_slot"] != slot or slot not in {"A", "B"}:
            raise ABUpdateError("boot failure does not match the pending image slot")
        if self.backend is None:
            raise ABUpdateError("native boot backend is required to restore the confirmed slot")
        fallback = state["confirmed_slot"]
        self.backend.set_next_boot(fallback)
        state["slots"][slot]["state"] = "failed"
        state["pending_slot"] = None
        state["active_slot"] = fallback
        write_json_state(self.state_file, state)
        return state
