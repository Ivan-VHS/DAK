"""Local game-library storage and read-only store discovery for Illidia.

This module does not authenticate to store accounts or download game content.
Store adapters inspect local installation metadata and produce ordinary library
records. Launch authorization and process handling live in launcher.py.
"""
from __future__ import annotations

import json
import os
import platform
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "duckos.illidia-library.v1"
SOURCES = {"steam", "epic", "gog", "battlenet", "ea", "custom"}
RUNTIMES = {"native", "wine", "proton", "crossover", "bottles", "qemu"}
MAX_SCAN_RESULTS = 10_000
_EXECUTABLE_SUFFIXES = {".exe", ".com", ".appimage", ".bin"}


class IllidiaError(ValueError):
    """Raised when a library record or local game manifest is invalid."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_database_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "duckos" / "illidia" / "library.sqlite3"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _string_list(value: Any, field: str, limit: int = 128) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > limit:
        raise IllidiaError(f"{field} must be a list with at most {limit} entries")
    result = []
    for item in value:
        if not isinstance(item, str) or "\x00" in item or len(item) > 4096:
            raise IllidiaError(f"{field} entries must be strings without NUL bytes")
        result.append(item)
    return result


def _absolute_path(value: str | Path | None) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    raw = Path(value).expanduser()
    try:
        return str(raw.resolve(strict=False))
    except OSError:
        return str(raw.absolute())


def _safe_child(root: Path, relative: str) -> Path | None:
    """Resolve a manifest-relative path and reject traversal outside its root."""
    if not isinstance(relative, str) or not relative.strip() or "\x00" in relative:
        return None
    candidate = (root / relative).resolve(strict=False)
    base = root.resolve(strict=False)
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate


@dataclass(frozen=True)
class GameRecord:
    id: str
    name: str
    source: str
    external_id: str | None
    executable_path: str | None
    arguments: list[str]
    working_directory: str | None
    runtime: str
    runtime_command: list[str]
    runtime_prefix: str | None
    launch_profile: dict[str, Any]
    metadata: dict[str, Any]
    tags: list[str]
    added_at: str
    updated_at: str
    last_played_at: str | None

    @property
    def installed(self) -> bool:
        install_path = self.metadata.get("install_path")
        if self.executable_path:
            return Path(self.executable_path).is_file()
        return bool(install_path and Path(install_path).is_dir())

    def as_dict(self) -> dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "external_id": self.external_id,
            "executable_path": self.executable_path,
            "arguments": list(self.arguments),
            "working_directory": self.working_directory,
            "runtime": self.runtime,
            "runtime_command": list(self.runtime_command),
            "runtime_prefix": self.runtime_prefix,
            "launch_profile": dict(self.launch_profile),
            "metadata": dict(self.metadata),
            "tags": list(self.tags),
            "added_at": self.added_at,
            "updated_at": self.updated_at,
            "last_played_at": self.last_played_at,
            "installed": self.installed,
        }
        return result


class IllidiaLibrary:
    """SQLite-backed local library with bounded, versioned records."""

    def __init__(self, database: str | Path | None = None):
        self.database = Path(database or default_database_path()).expanduser()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS games (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    external_id TEXT,
                    executable_path TEXT,
                    arguments_json TEXT NOT NULL,
                    working_directory TEXT,
                    runtime TEXT NOT NULL,
                    runtime_command_json TEXT NOT NULL,
                    runtime_prefix TEXT,
                    launch_profile_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_played_at TEXT,
                    UNIQUE(source, external_id)
                );
                CREATE INDEX IF NOT EXISTS games_name_idx ON games(name COLLATE NOCASE);
                CREATE INDEX IF NOT EXISTS games_source_idx ON games(source);
                CREATE TABLE IF NOT EXISTS approvals (
                    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                    digest TEXT NOT NULL,
                    approval_kind TEXT NOT NULL,
                    approved_at TEXT NOT NULL,
                    PRIMARY KEY(game_id, digest, approval_kind)
                );
                CREATE TABLE IF NOT EXISTS fingerprints (
                    game_id TEXT PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,
                    digest TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS launches (
                    id TEXT PRIMARY KEY,
                    game_id TEXT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                    pid INTEGER,
                    process_group INTEGER,
                    launch_kind TEXT NOT NULL,
                    command_json TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    exit_code INTEGER,
                    log_path TEXT
                );
                CREATE INDEX IF NOT EXISTS launches_game_idx ON launches(game_id, started_at);
                """
            )
            connection.execute("PRAGMA user_version = 1")

    @staticmethod
    def _row_to_game(row: sqlite3.Row) -> GameRecord:
        return GameRecord(
            id=row["id"],
            name=row["name"],
            source=row["source"],
            external_id=row["external_id"],
            executable_path=row["executable_path"],
            arguments=json.loads(row["arguments_json"]),
            working_directory=row["working_directory"],
            runtime=row["runtime"],
            runtime_command=json.loads(row["runtime_command_json"]),
            runtime_prefix=row["runtime_prefix"],
            launch_profile=json.loads(row["launch_profile_json"]),
            metadata=json.loads(row["metadata_json"]),
            tags=json.loads(row["tags_json"]),
            added_at=row["added_at"],
            updated_at=row["updated_at"],
            last_played_at=row["last_played_at"],
        )

    def add_game(
        self,
        *,
        name: str,
        source: str,
        executable_path: str | Path | None = None,
        external_id: str | None = None,
        arguments: Iterable[str] = (),
        working_directory: str | Path | None = None,
        runtime: str = "native",
        runtime_command: Iterable[str] = (),
        runtime_prefix: str | Path | None = None,
        launch_profile: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: Iterable[str] = (),
    ) -> GameRecord:
        if source not in SOURCES:
            raise IllidiaError(f"unsupported source: {source}")
        if runtime not in RUNTIMES:
            raise IllidiaError(f"unsupported runtime: {runtime}")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 240:
            raise IllidiaError("name must contain 1..240 characters")
        args = _string_list(list(arguments), "arguments")
        runtime_args = _string_list(list(runtime_command), "runtime_command", 64)
        tag_values = _string_list(list(tags), "tags", 64)
        if any(len(tag) > 64 for tag in tag_values):
            raise IllidiaError("tags must be at most 64 characters")
        if metadata is not None and not isinstance(metadata, dict):
            raise IllidiaError("metadata must be an object")
        if launch_profile is not None and not isinstance(launch_profile, dict):
            raise IllidiaError("launch_profile must be an object")

        profile = dict(launch_profile or {})
        allowed_profile_keys = {
            "environment", "window_mode", "launch_via_store",
            "pre_launch", "post_launch", "allow_hooks",
        }
        if set(profile) - allowed_profile_keys:
            raise IllidiaError("launch_profile contains unsupported keys")
        environment = profile.get("environment", {})
        if not isinstance(environment, dict) or len(environment) > 128:
            raise IllidiaError("launch_profile.environment must be a small object")
        for key, value in environment.items():
            if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                raise IllidiaError("environment variable names must be valid identifiers")
            if not isinstance(value, str) or "\x00" in value or len(value) > 8192:
                raise IllidiaError("environment values must be bounded strings")
        for hook_name in ("pre_launch", "post_launch"):
            hooks = profile.get(hook_name, [])
            if not isinstance(hooks, list) or len(hooks) > 8:
                raise IllidiaError(f"{hook_name} must contain at most 8 commands")
            for command in hooks:
                _string_list(command, hook_name, 32)
                if not command:
                    raise IllidiaError(f"{hook_name} commands cannot be empty")
        if "allow_hooks" in profile and not isinstance(profile["allow_hooks"], bool):
            raise IllidiaError("allow_hooks must be boolean")
        window_mode = profile.get("window_mode", "default")
        if window_mode not in {"default", "windowed", "borderless", "fullscreen"}:
            raise IllidiaError("window_mode must be default, windowed, borderless or fullscreen")
        if "launch_via_store" in profile and not isinstance(profile["launch_via_store"], bool):
            raise IllidiaError("launch_via_store must be boolean")

        now = _utc_now()
        game_id = str(uuid.uuid4())
        path = _absolute_path(executable_path)
        cwd = _absolute_path(working_directory)
        prefix = _absolute_path(runtime_prefix)
        meta = dict(metadata or {})
        if external_id is not None and (not isinstance(external_id, str) or len(external_id) > 256):
            raise IllidiaError("external_id must be at most 256 characters")
        ext_id = external_id or (f"custom:{game_id}" if source == "custom" else None)

        with self._connect() as connection:
            if ext_id:
                existing = connection.execute(
                    "SELECT id FROM games WHERE source=? AND external_id=?",
                    (source, ext_id),
                ).fetchone()
            else:
                existing = None
            if existing:
                game_id = existing["id"]
                connection.execute(
                    """
                    UPDATE games SET name=?, executable_path=?, arguments_json=?,
                        working_directory=?, runtime=?, runtime_command_json=?,
                        runtime_prefix=?, launch_profile_json=?, metadata_json=?,
                        tags_json=?, updated_at=? WHERE id=?
                    """,
                    (
                        name.strip(), path, _json(args), cwd, runtime, _json(runtime_args),
                        prefix, _json(profile), _json(meta), _json(tag_values), now, game_id,
                    ),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO games (
                        id, name, source, external_id, executable_path, arguments_json,
                        working_directory, runtime, runtime_command_json, runtime_prefix,
                        launch_profile_json, metadata_json, tags_json, added_at,
                        updated_at, last_played_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        game_id, name.strip(), source, ext_id, path, _json(args), cwd,
                        runtime, _json(runtime_args), prefix, _json(profile), _json(meta),
                        _json(tag_values), now, now,
                    ),
                )
            row = connection.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
        return self._row_to_game(row)

    def get_game(self, game_id: str) -> GameRecord:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone()
        if row is None:
            raise IllidiaError(f"game not found: {game_id}")
        return self._row_to_game(row)

    def list_games(
        self,
        *,
        search: str | None = None,
        source: str | None = None,
        installed: bool | None = None,
        tag: str | None = None,
    ) -> list[GameRecord]:
        if source is not None and source not in SOURCES:
            raise IllidiaError(f"unsupported source: {source}")
        clauses = []
        values: list[Any] = []
        if source:
            clauses.append("source=?")
            values.append(source)
        if search:
            clauses.append("(name LIKE ? COLLATE NOCASE OR executable_path LIKE ? COLLATE NOCASE)")
            values.extend((f"%{search}%", f"%{search}%"))
        query = "SELECT * FROM games"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY name COLLATE NOCASE, source"
        with self._connect() as connection:
            rows = connection.execute(query, values).fetchall()
        records = [self._row_to_game(row) for row in rows]
        if installed is not None:
            records = [record for record in records if record.installed is installed]
        if tag:
            records = [record for record in records if tag in record.tags]
        return records

    def set_launch_profile(self, game_id: str, profile: dict[str, Any]) -> GameRecord:
        current = self.get_game(game_id)
        updated = self.add_game(
            name=current.name,
            source=current.source,
            executable_path=current.executable_path,
            external_id=current.external_id,
            arguments=current.arguments,
            working_directory=current.working_directory,
            runtime=current.runtime,
            runtime_command=current.runtime_command,
            runtime_prefix=current.runtime_prefix,
            launch_profile=profile,
            metadata=current.metadata,
            tags=current.tags,
        )
        return updated

    def remove_game(self, game_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM games WHERE id=?", (game_id,))
            if cursor.rowcount == 0:
                raise IllidiaError(f"game not found: {game_id}")

    def has_approval(self, game_id: str, digest: str, kind: str = "unverified") -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM approvals WHERE game_id=? AND digest=? AND approval_kind=?",
                (game_id, digest, kind),
            ).fetchone()
        return row is not None

    def approve(self, game_id: str, digest: str, kind: str = "unverified") -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO approvals VALUES (?, ?, ?, ?)",
                (game_id, digest, kind, _utc_now()),
            )

    def fingerprint(self, game_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT digest FROM fingerprints WHERE game_id=?", (game_id,)
            ).fetchone()
        return row["digest"] if row else None

    def set_fingerprint(self, game_id: str, digest: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO fingerprints VALUES (?, ?, ?)",
                (game_id, digest, _utc_now()),
            )

    def record_launch(
        self,
        game_id: str,
        *,
        pid: int | None,
        process_group: int | None,
        launch_kind: str,
        command: list[str],
        log_path: str | None,
        launch_id: str | None = None,
    ) -> str:
        launch_id = launch_id or str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO launches (
                    id, game_id, pid, process_group, launch_kind, command_json,
                    started_at, status, exit_code, log_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    launch_id, game_id, pid, process_group, launch_kind,
                    _json(command), _utc_now(), "running" if pid else "delegated",
                    log_path,
                ),
            )
            connection.execute(
                "UPDATE games SET last_played_at=?, updated_at=? WHERE id=?",
                (_utc_now(), _utc_now(), game_id),
            )
        return launch_id

    def update_launch(self, launch_id: str, *, status: str, exit_code: int | None = None) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE launches SET status=?, exit_code=? WHERE id=?",
                (status, exit_code, launch_id),
            )

    def list_launches(self, game_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM launches"
        values: tuple[Any, ...] = ()
        if game_id:
            query += " WHERE game_id=?"
            values = (game_id,)
        query += " ORDER BY started_at DESC"
        with self._connect() as connection:
            rows = connection.execute(query, values).fetchall()
        return [
            {
                "id": row["id"], "game_id": row["game_id"], "pid": row["pid"],
                "process_group": row["process_group"], "launch_kind": row["launch_kind"],
                "command": json.loads(row["command_json"]), "started_at": row["started_at"],
                "status": row["status"], "exit_code": row["exit_code"],
                "log_path": row["log_path"],
            }
            for row in rows
        ]

    def export_library(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "exported_at": _utc_now(),
            "games": [record.as_dict() for record in self.list_games()],
        }

    def import_library(self, payload: Any) -> int:
        if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
            raise IllidiaError(f"import must use schema {SCHEMA}")
        records = payload.get("games")
        if not isinstance(records, list) or len(records) > 50_000:
            raise IllidiaError("games must be a list with at most 50000 entries")
        imported = 0
        for item in records:
            if not isinstance(item, dict):
                raise IllidiaError("each imported game must be an object")
            self.add_game(
                name=item.get("name"),
                source=item.get("source"),
                executable_path=item.get("executable_path"),
                external_id=item.get("external_id"),
                arguments=item.get("arguments", []),
                working_directory=item.get("working_directory"),
                runtime=item.get("runtime", "native"),
                runtime_command=item.get("runtime_command", []),
                runtime_prefix=item.get("runtime_prefix"),
                launch_profile=item.get("launch_profile", {}),
                metadata=item.get("metadata", {}),
                tags=item.get("tags", []),
            )
            imported += 1
        return imported


def _key_value(text: str, key: str) -> str | None:
    match = re.search(r'"' + re.escape(key) + r'"\s*"((?:\\.|[^"])*)"', text, re.IGNORECASE)
    return match.group(1).replace("\\\\", "\\") if match else None


def _steam_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    candidates = []
    for value in (os.environ.get("STEAM_DIR"), os.environ.get("STEAM_PATH")):
        if value:
            candidates.append(Path(value).expanduser())
    if os.name == "nt":
        for env in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
            if os.environ.get(env):
                candidates.append(Path(os.environ[env]) / "Steam")
    candidates.extend([
        home / ".steam/steam",
        home / ".local/share/Steam",
        home / "Library/Application Support/Steam",
    ])
    unique = []
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve(strict=False)
        if resolved not in seen and resolved.is_dir():
            seen.add(resolved)
            unique.append(resolved)
    return unique


class SteamAdapter:
    source = "steam"

    def discover(self) -> list[dict[str, Any]]:
        records = []
        for steam_root in _steam_roots():
            library_roots = {steam_root}
            vdf = steam_root / "steamapps/libraryfolders.vdf"
            if vdf.is_file():
                try:
                    text = vdf.read_text(encoding="utf-8", errors="replace")
                    for raw_path in re.findall(r'"path"\s*"((?:\\.|[^"])*)"', text):
                        library_roots.add(Path(raw_path.replace("\\\\", "\\")).expanduser())
                except OSError:
                    continue
            for library_root in library_roots:
                apps = library_root / "steamapps"
                if not apps.is_dir():
                    continue
                for manifest in apps.glob("appmanifest_*.acf"):
                    try:
                        data = manifest.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    app_id = _key_value(data, "appid")
                    name = _key_value(data, "name")
                    install_dir = _key_value(data, "installdir")
                    if not app_id or not name or not install_dir:
                        continue
                    install_path = (apps / "common" / install_dir).resolve(strict=False)
                    records.append({
                        "name": name,
                        "source": "steam",
                        "external_id": app_id,
                        "executable_path": None,
                        "working_directory": str(install_path),
                        "metadata": {
                            "steam_app_id": app_id,
                            "install_path": str(install_path),
                            "store_uri": f"steam://rungameid/{app_id}",
                            "launch_mode": "store",
                        },
                        "tags": ["store", "steam"],
                    })
        return records


def _epic_manifest_dirs() -> list[Path]:
    candidates = []
    if os.environ.get("EPIC_MANIFEST_DIR"):
        candidates.append(Path(os.environ["EPIC_MANIFEST_DIR"]).expanduser())
    if os.name == "nt":
        program_data = Path(os.environ.get("PROGRAMDATA", r"C:\\ProgramData"))
        candidates.append(program_data / "Epic/EpicGamesLauncher/Data/Manifests")
    candidates.extend([
        Path.home() / ".config/Epic/Manifests",
        Path.home() / ".local/share/Epic/Manifests",
    ])
    return [item for item in candidates if item.is_dir()]


class EpicAdapter:
    source = "epic"

    def discover(self) -> list[dict[str, Any]]:
        records = []
        for folder in _epic_manifest_dirs():
            for manifest in folder.glob("*.item"):
                try:
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                app_name = data.get("AppName")
                display_name = data.get("DisplayName") or app_name
                install_value = data.get("InstallLocation")
                if not isinstance(app_name, str) or not isinstance(display_name, str):
                    continue
                install_path = Path(install_value).expanduser() if isinstance(install_value, str) else None
                executable = data.get("LaunchExecutable")
                executable_path = _safe_child(install_path, executable) if install_path and isinstance(executable, str) else None
                uri = f"com.epicgames.launcher://apps/{app_name}?action=launch&silent=true"
                records.append({
                    "name": display_name,
                    "source": "epic",
                    "external_id": app_name,
                    "executable_path": str(executable_path) if executable_path else None,
                    "working_directory": str(install_path) if install_path else None,
                    "arguments": [],
                    "metadata": {
                        "epic_app_name": app_name,
                        "install_path": str(install_path) if install_path else None,
                        "launch_uri": uri,
                        "store_uri": uri,
                        "launch_mode": "store",
                        "manifest": str(manifest),
                        "launch_command": data.get("LaunchCommand"),
                    },
                    "tags": ["store", "epic"],
                })
        return records


def _gog_roots() -> list[Path]:
    candidates = []
    if os.environ.get("GOG_GAMES_DIR"):
        candidates.append(Path(os.environ["GOG_GAMES_DIR"]).expanduser())
    candidates.extend([
        Path.home() / "GOG Games",
        Path.home() / "Games",
    ])
    if os.name == "nt":
        for env in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
            if os.environ.get(env):
                candidates.append(Path(os.environ[env]) / "GOG Galaxy/Games")
    return [item for item in candidates if item.is_dir()]


class GogAdapter:
    source = "gog"

    def discover(self) -> list[dict[str, Any]]:
        records = []
        seen = set()
        for root in _gog_roots():
            for manifest in root.rglob("goggame-*.info"):
                if len(records) >= MAX_SCAN_RESULTS:
                    return records
                try:
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                game_id = str(data.get("gameId") or manifest.stem.removeprefix("goggame-"))
                name = data.get("name") or data.get("title") or manifest.parent.name
                if not game_id or game_id in seen or not isinstance(name, str):
                    continue
                seen.add(game_id)
                install_path = manifest.parent
                tasks = data.get("playTasks") if isinstance(data.get("playTasks"), list) else []
                primary = next((task for task in tasks if isinstance(task, dict) and task.get("isPrimary")), None)
                task = primary or next((item for item in tasks if isinstance(item, dict)), {})
                executable_value = task.get("path") if isinstance(task, dict) else None
                executable = _safe_child(install_path, executable_value) if isinstance(executable_value, str) else None
                uri = f"goggalaxy://openGameView/{game_id}"
                records.append({
                    "name": name,
                    "source": "gog",
                    "external_id": game_id,
                    "executable_path": str(executable) if executable else None,
                    "arguments": _string_list(task.get("arguments", []), "GOG arguments") if isinstance(task, dict) else [],
                    "working_directory": str(install_path),
                    "metadata": {
                        "gog_game_id": game_id,
                        "install_path": str(install_path),
                        "store_uri": uri,
                        "launch_mode": "store",
                        "manifest": str(manifest),
                    },
                    "tags": ["store", "gog"],
                })
        return records


def discover_stores() -> dict[str, Any]:
    adapters = (SteamAdapter(), EpicAdapter(), GogAdapter())
    results: dict[str, Any] = {"schema": "duckos.illidia-discovery.v1", "stores": {}, "total": 0}
    for adapter in adapters:
        try:
            records = adapter.discover()
            results["stores"][adapter.source] = {
                "available": bool(records),
                "count": len(records),
                "games": records,
                "error": None,
            }
            results["total"] += len(records)
        except OSError as error:
            results["stores"][adapter.source] = {
                "available": False, "count": 0, "games": [], "error": str(error),
            }
    return results


def import_store_discovery(library: IllidiaLibrary, discovery: dict[str, Any]) -> int:
    imported = 0
    for store in discovery.get("stores", {}).values():
        for record in store.get("games", []):
            library.add_game(**record)
            imported += 1
    return imported


def scan_custom_directories(directories: Iterable[str | Path]) -> list[dict[str, Any]]:
    """Find likely executables in user-selected directories without launching them."""
    results = []
    seen = set()
    for supplied in directories:
        root = Path(supplied).expanduser()
        if not root.exists() or not root.is_dir():
            continue
        for current, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [name for name in dirs if not (Path(current) / name).is_symlink()]
            for filename in files:
                candidate = Path(current) / filename
                suffix = candidate.suffix.casefold()
                executable = suffix in _EXECUTABLE_SUFFIXES
                if os.name != "nt" and not executable:
                    try:
                        executable = os.access(candidate, os.X_OK) and candidate.is_file()
                    except OSError:
                        executable = False
                if not executable:
                    continue
                try:
                    resolved = candidate.resolve(strict=True)
                except OSError:
                    continue
                if resolved in seen or not resolved.is_file():
                    continue
                seen.add(resolved)
                results.append({
                    "name": candidate.stem,
                    "source": "custom",
                    "executable_path": str(resolved),
                    "working_directory": str(resolved.parent),
                    "metadata": {"install_path": str(resolved.parent), "launch_mode": "direct"},
                    "tags": ["custom"],
                })
                if len(results) >= MAX_SCAN_RESULTS:
                    return results
    return results
