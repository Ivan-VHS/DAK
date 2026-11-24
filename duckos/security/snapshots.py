"""Explicit, bounded and reversible user-space file snapshots.

The store is intentionally limited to a caller-selected managed root. It is
not a filesystem filter and cannot snapshot writes that bypass this API.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath

SNAPSHOT_DIR = Path(".duckos-security") / "snapshots"
SNAPSHOT_ID = re.compile(r"^[0-9a-f]{32}$")


class SnapshotError(ValueError):
    """Raised for unsafe paths, invalid snapshots or bounded-store failures."""


class SnapshotStore:
    def __init__(
        self,
        managed_root: str | Path,
        *,
        max_file_bytes: int = 64 * 1024 * 1024,
        max_snapshots: int = 256,
    ) -> None:
        root = Path(managed_root).expanduser()
        if root.is_symlink() or not root.is_dir():
            raise SnapshotError("managed_root must be an existing, non-symlink directory")
        self.root = root.resolve(strict=True)
        if max_file_bytes <= 0 or max_file_bytes > 512 * 1024 * 1024:
            raise SnapshotError("max_file_bytes must be between 1 and 536870912")
        if max_snapshots < 1 or max_snapshots > 4096:
            raise SnapshotError("max_snapshots must be between 1 and 4096")
        self.max_file_bytes = max_file_bytes
        self.max_snapshots = max_snapshots
        self.store = self.root / SNAPSHOT_DIR

    def _safe_relative(self, value: str) -> PurePosixPath:
        if not isinstance(value, str) or not value or len(value) > 1024 or "\x00" in value:
            raise SnapshotError("target must be a non-empty relative path")
        relative = PurePosixPath(value.replace("\\", "/"))
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise SnapshotError("target must not be absolute or contain dot segments")
        if relative.parts[0] == ".duckos-security":
            raise SnapshotError("the security snapshot store is reserved")
        return relative

    def _target(self, relative: PurePosixPath, *, allow_missing: bool = False) -> Path:
        current = self.root
        for index, part in enumerate(relative.parts):
            current = current / part
            try:
                metadata = current.lstat()
            except FileNotFoundError:
                if allow_missing and index == len(relative.parts) - 1:
                    break
                raise SnapshotError(f"managed path component does not exist: {part}")
            if stat.S_ISLNK(metadata.st_mode):
                raise SnapshotError("symbolic links are not allowed in managed snapshot paths")
            if index < len(relative.parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
                raise SnapshotError("parent path component is not a directory")
            if index == len(relative.parts) - 1 and not stat.S_ISREG(metadata.st_mode):
                raise SnapshotError("snapshot target must be a regular file or a missing file")
        resolved_parent = current.parent.resolve(strict=True)
        if self.root != resolved_parent and self.root not in resolved_parent.parents:
            raise SnapshotError("target escaped the managed root")
        return current

    def _ensure_store(self) -> None:
        security_dir = self.root / ".duckos-security"
        if security_dir.exists() and security_dir.is_symlink():
            raise SnapshotError("security store path must not be a symlink")
        security_dir.mkdir(mode=0o700, exist_ok=True)
        if security_dir.is_symlink() or not security_dir.is_dir():
            raise SnapshotError("security store path is not a safe directory")
        if self.store.exists() and self.store.is_symlink():
            raise SnapshotError("snapshot directory must not be a symlink")
        self.store.mkdir(mode=0o700, exist_ok=True)
        if self.store.is_symlink() or not self.store.is_dir():
            raise SnapshotError("snapshot directory is not a safe directory")

    @staticmethod
    def _atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
        descriptor, temporary_name = tempfile.mkstemp(prefix=".duckos-snapshot-", dir=path.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, mode & 0o777)
            os.replace(temporary, path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def create(self, target: str) -> dict[str, object]:
        relative = self._safe_relative(target)
        path = self._target(relative)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags)
        except OSError as error:
            raise SnapshotError(f"cannot safely open snapshot target: {error}") from error
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > self.max_file_bytes:
                raise SnapshotError("target is not a regular file or exceeds the snapshot size limit")
            content = stream.read(self.max_file_bytes + 1)
            after = os.fstat(stream.fileno())
        if len(content) > self.max_file_bytes:
            raise SnapshotError("target exceeds the snapshot size limit")
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise SnapshotError("target changed while the snapshot was being captured")
        self._ensure_store()
        existing = list(self.store.glob("*.json"))
        if len(existing) >= self.max_snapshots:
            raise SnapshotError("snapshot quota reached; prune old snapshots explicitly")
        snapshot_id = uuid.uuid4().hex
        digest = hashlib.sha256(content).hexdigest()
        data_path = self.store / f"{snapshot_id}.bin"
        metadata_path = self.store / f"{snapshot_id}.json"
        self._atomic_write(data_path, content)
        metadata = {
            "schema": "duckos.file-snapshot.v1",
            "snapshot_id": snapshot_id,
            "target": relative.as_posix(),
            "size_bytes": len(content),
            "sha256": digest,
            "mode": stat.S_IMODE(before.st_mode),
            "created_at_ms": int(time.time() * 1000),
        }
        self._atomic_write(metadata_path, (json.dumps(metadata, sort_keys=True) + "\n").encode("utf-8"))
        return metadata

    def restore(self, snapshot_id: str) -> dict[str, object]:
        if not isinstance(snapshot_id, str) or not SNAPSHOT_ID.fullmatch(snapshot_id):
            raise SnapshotError("invalid snapshot identifier")
        self._ensure_store()
        metadata_path = self.store / f"{snapshot_id}.json"
        data_path = self.store / f"{snapshot_id}.bin"
        try:
            metadata_stat = metadata_path.lstat()
            data_stat = data_path.lstat()
            if not stat.S_ISREG(metadata_stat.st_mode) or not stat.S_ISREG(data_stat.st_mode):
                raise SnapshotError("snapshot records must be regular files, not links or special files")
            if metadata_stat.st_size > 16 * 1024 or data_stat.st_size > self.max_file_bytes:
                raise SnapshotError("snapshot record exceeds its configured size limit")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            with os.fdopen(os.open(metadata_path, flags), "rb") as stream:
                metadata_bytes = stream.read(16 * 1024 + 1)
            if len(metadata_bytes) > 16 * 1024:
                raise SnapshotError("snapshot metadata exceeds its size limit")
            with os.fdopen(os.open(data_path, flags), "rb") as stream:
                content = stream.read(self.max_file_bytes + 1)
        except SnapshotError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise SnapshotError(f"cannot read snapshot: {error}") from error
        try:
            metadata = json.loads(metadata_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise SnapshotError(f"invalid snapshot metadata: {error}") from error
        if not isinstance(metadata, dict):
            raise SnapshotError("snapshot metadata must be a JSON object")
        if metadata.get("schema") != "duckos.file-snapshot.v1" or metadata.get("snapshot_id") != snapshot_id:
            raise SnapshotError("snapshot metadata identity mismatch")
        expected_size = metadata.get("size_bytes")
        if isinstance(expected_size, bool) or not isinstance(expected_size, int):
            raise SnapshotError("snapshot metadata has an invalid size")
        if len(content) != expected_size or len(content) > self.max_file_bytes:
            raise SnapshotError("snapshot payload size mismatch")
        mode = metadata.get("mode", 0o600)
        if isinstance(mode, bool) or not isinstance(mode, int) or mode < 0 or mode > 0o777:
            raise SnapshotError("snapshot metadata has an invalid file mode")
        digest = hashlib.sha256(content).hexdigest()
        if digest != metadata.get("sha256"):
            raise SnapshotError("snapshot payload digest mismatch")
        relative = self._safe_relative(metadata.get("target"))
        path = self._target(relative, allow_missing=True)
        self._atomic_write(path, content, mode)
        return {
            "schema": "duckos.file-restore.v1",
            "snapshot_id": snapshot_id,
            "target": relative.as_posix(),
            "restored": True,
            "sha256": digest,
        }
