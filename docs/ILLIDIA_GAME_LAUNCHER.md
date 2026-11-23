# Illidia universal game library and launcher

**Feature owner:** Illidia  
**Bridge relationship:** DuckBridge runtime discovery and compatibility planning  
**Backend state:** implemented as a local Python host tool; native DuckOS service integration remains planned  
**Scope:** local game inventory, store metadata discovery, custom executable registration, explicit trust review, launch profiles, process sessions and portable library data.

Illidia owns the game library and play-session workflow. DuckBridge supplies compatibility-runtime information and, where useful, a configured Wine/Proton-style command. The launcher never treats a PE/ELF inspection result as proof that a binary can run.

## 1. What is implemented

The `duckos.illidia` package provides:

- a local SQLite database with WAL mode, indexed names and source fields;
- one game record for store and custom sources, including a stable ID, external source ID, executable path, argv, working directory, runtime command, prefix, launch profile, metadata and tags;
- read-only discovery for local Steam app manifests, Epic `.item` manifests and GOG `goggame-*.info` files;
- an explicit scan of directories selected by the user, without executing discovered files;
- manual registration for custom binaries and for entries from stores that do not yet have a tested local manifest adapter;
- search by name/path, filtering by source, installed/missing state and tags;
- per-game environment variables, working directory, arguments, runtime command and prefix;
- local SHA-256 fingerprints, a per-binary first-run approval record and signature status;
- direct process launch with argv arrays, `shell=False`, a separate process group and a local launch log;
- session listing and stop requests for directly launched process groups;
- JSON library export/import.

The command is installed as `illidia` by the DuckOS Python package. It uses only the Python standard library.

## 2. Store adapters and library records

All adapters write the same record shape. Store-specific fields are retained under `metadata` rather than leaking into the card or launch API.

| Source | Local discovery | Default launch behavior |
|---|---|---|
| Steam | `libraryfolders.vdf` and `appmanifest_*.acf` from known roots or `STEAM_DIR` / `STEAM_PATH` | Open `steam://rungameid/<appid>` so Steam owns overlay and cloud-save behavior |
| Epic Games Store | `.item` manifests from the known Windows ProgramData path or `EPIC_MANIFEST_DIR` | Open the Epic game URI from the manifest's AppName |
| GOG | `goggame-*.info` in known game roots or `GOG_GAMES_DIR` | Open `goggalaxy://openGameView/<game-id>` |
| Battle.net / EA / other launchers | Manual source identity and user-configured executable/runtime profile | Direct configured command until a tested store adapter exists |
| Custom | User-selected folder scan or manual executable path | Direct launch using the per-game profile |

The Steam adapter uses the store AppID and does not guess an executable inside the installation directory. The user can attach a binary later and choose direct launch explicitly. Epic and GOG adapters retain the local executable path when the manifest supplies a safe path inside the install directory.

Store discovery is local and read-only. It does not sign in, access account credentials, download game content, change library folders or modify store manifests. If a store changes its local manifest format, that adapter may return fewer entries; other adapters and custom records remain independent.

Battle.net and EA are accepted as explicit source identities, but automatic manifest discovery and provider-specific deep links are not claimed yet. A custom entry can still use that launcher's executable with its own arguments and runtime command. Provider-specific URI schemes must be added only after their formats and behavior are verified.

## 3. Add, scan and discover

Examples:

```sh
# Inspect local Steam, Epic and GOG manifests without changing the library
illidia discover

# Import discovered store entries into the local database
illidia discover --import-stores

# Scan only a directory the user explicitly selected; review candidates first
illidia scan "$HOME/Games"

# Add found candidates after reviewing the scan output
illidia scan "$HOME/Games" --add

# Add one local executable with explicit arguments
illidia add "Example Game" "$HOME/Games/Example/game.exe" \
  --arg=--fullscreen --working-directory "$HOME/Games/Example" \
  --runtime wine --runtime-command /usr/bin/wine \
  --prefix "$HOME/.local/share/duckos/illidia/prefixes/example" \
  --tag rpg
```

`scan` is a candidate finder, not an installer and not a launch action. It does not run discovered files. It avoids following symlinked directories and caps the result count. The user must supply the directory to scan.

## 4. Signature and hash policy

A digest and a signature answer different questions:

- SHA-256 records the bytes of the current executable.
- Authenticode validation (where available) checks a Windows executable's embedded signing status.
- A signer is trusted only when the host verifier and applicable trust policy say so.
- An absent or unavailable signature is not silently converted into a valid signature.

On Windows, Illidia queries the local Authenticode status through PowerShell. On systems without a common executable-signature verifier, the status is `not_checked`. An `unsigned`, `invalid` or `not_checked` direct executable requires explicit first-run approval for that exact SHA-256 digest:

```sh
illidia inspect GAME_ID
illidia launch GAME_ID --confirm-unverified
```

That confirmation is stored locally for the game ID and the exact file digest. A changed binary has a new digest and therefore needs its own review when its signature is not verified. The launcher does not block a file merely because its hash changed: it displays the mismatch, continues after any required first-run approval and leaves the saved fingerprint unchanged unless the user requests an update:

```sh
illidia launch GAME_ID --confirm-unverified --update-fingerprint
```

For an already approved digest, a normal launch does not ask again. The store-client route delegates execution to Steam/Epic/GOG, so the store client owns its own package verification and update flow. Use `--direct` to inspect and launch an attached local executable instead.

A local first-run approval is a user decision, not a malware verdict. It does not prove that the file is safe. Review the origin, path and digest before approving unfamiliar software.

## 5. Launch profile

Each game can define:

- the exact argument vector (not a shell command string);
- a working directory;
- a runtime name and explicit runtime command;
- a per-game compatibility prefix;
- environment variables;
- a window-mode preference;
- pre-launch and post-launch command arrays.

A profile is updated from a local JSON document:

```json
{
  "environment": {
    "DXVK_ASYNC": "1"
  },
  "window_mode": "borderless",
  "launch_via_store": false,
  "allow_hooks": false,
  "pre_launch": [],
  "post_launch": []
}
```

```sh
illidia profile GAME_ID ./profile.json
```

The window-mode field is saved as profile metadata; it is not yet applied by a native compositor. Runtime commands and environment variables are passed explicitly. For Proton, Illidia appends `run` before the executable. Other compatibility runtimes receive the executable and its arguments after the configured runtime command. DXVK or other layers must be configured in the selected runtime environment; Illidia does not download DLLs or modify a prefix automatically.

Hooks are disabled by default. To run them, the profile must contain explicit argv arrays and set `allow_hooks` to `true`. They use `shell=False`; a user who explicitly configures an interpreter such as `sh -c` is explicitly choosing that interpreter. Post-launch hooks run only when the caller uses `--wait`.

## 6. Launch, logs and process handling

```sh
illidia list --source custom --installed
illidia inspect GAME_ID
illidia launch GAME_ID
illidia sessions
illidia stop LAUNCH_ID
illidia stop LAUNCH_ID --force
```

Direct launches are started without a shell, in a separate process group on POSIX or a separate process group on Windows. stdout and stderr are written to a per-launch log under the Illidia data directory. Arguments are not interpreted by a shell.

On POSIX, stop requests signal the recorded process group so ordinary child processes that inherit that group are included. On Windows, Illidia uses `taskkill /T` and adds `/F` only when the user requests a forceful stop. Process status is refreshed from the recorded PID. This host-tool session model is best effort; the future native process manager must use authenticated process handles and stable process-generation identifiers to avoid PID-reuse races.

When a game is launched through an official store URI, the store owns the actual game process, overlay, cloud saves and provider session. Illidia records the delegation but cannot claim to supervise or terminate the full game process tree through the URI handler. Stop that game through its store client. A future native store broker can expose provider session IDs and authenticated process handles.

## 7. Offline storage, export and recovery

The default database lives under:

- Windows: `%LOCALAPPDATA%/duckos/illidia/library.sqlite3`
- Linux/macOS: `$XDG_DATA_HOME/duckos/illidia/library.sqlite3`, otherwise `~/.local/share/duckos/illidia/library.sqlite3`

Logs are stored in the adjacent `logs/` directory. The database contains local paths and launch metadata; it does not contain store passwords or authentication tokens.

```sh
illidia export ./illidia-library.json
illidia import ./illidia-library.json
illidia list --missing
```

If a volume is disconnected or a game is removed, the record and profile remain. It appears as missing until the user edits or re-adds the correct path. The remove command deletes only the library record; it never deletes game files. Back up the database and exported JSON separately from the executable files themselves.

## 8. Mora and DuckBridge integration boundary

The current Mora window is a browser shell. It cannot enumerate arbitrary host directories, launch EXE/ELF binaries, monitor process trees or access store databases without a separately installed native service. Browser file inspection is not an executable launch API.

This backend is therefore exposed as a local Python command first. The next native integration is a narrowly scoped Illidia broker over authenticated DuckOS IPC, with typed operations for library query, scan preview, add/update, inspect, approve, launch, session status, stop, export and import. The browser must never receive arbitrary process-spawn authority or raw store credentials. Its launch request must carry a selected game ID; the broker resolves the stored record, rechecks capabilities and trust state, then presents the canonical launch review.

No current implementation claims a native compositor, kernel-enforced per-game sandbox, store login, cloud-save synchronization, achievements sync, driver modification, anti-cheat bypass or compatibility guarantee. DuckBridge discovery remains a separate source of runtime availability; a configured Wine/Proton command is not proof that a specific title will run.

## 9. Validation

Run:

```sh
python -m unittest discover -s tests -v
illidia discover
illidia list
```

Tests cover the SQLite record lifecycle, filtered queries, export/import, safe directory scanning, Steam/Epic/GOG manifest parsing, Epic path traversal rejection, explicit first-run approval, hash-change behavior, literal argv handling and URI allowlisting.

The test suite validates the host-side library and launcher policy. It does not prove native DuckOS sandbox enforcement or store-provider correctness on every platform.
