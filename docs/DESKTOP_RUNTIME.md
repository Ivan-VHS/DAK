# DuckOS desktop utilities and bench runtime

**Maintainer:** Ivan-VHS  
**Catalogue:** `duckos.system-applications.v1`  
**Runtime contract:** `duckos.desktop`

This layer adds fifteen system utility identities alongside the seven DuckOS first-party products. It does not replace Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia or Unify, and it does not expand the existing seven-product application catalogue.

## The 15 system applications

| # | ID | Application | Responsibility |
|---:|---|---|---|
| 01 | `sys-settings` | Настройки | Theme, permissions, isolation profile, power policy view and A/B status |
| 02 | `pkg-center` | Магазин приложений | Package catalogues, manifests, hashes, trust and install preview |
| 03 | `web-browser` | Веб-браузер | Documentation and isolated diagnostic web panels |
| 04 | `mail-client` | Почта | Mail, test reports and explicitly selected attachments |
| 05 | `contacts-dir` | Контакты | Team directory, module ownership and build responsibility |
| 06 | `file-manager` | Файловый менеджер | Files, package staging, image slots, dumps and logs |
| 07 | `quick-notes` | Заметки | Engineering notes linked to launcher slots and test sessions |
| 08 | `todo-tasks` | Задачи | Test queue, checklists and dependency tracking |
| 09 | `os-calendar` | Календарь | Releases, maintenance windows and test reservations |
| 10 | `clocks-timers` | Часы и таймеры | Clock, countdowns, cooldown and telemetry interval presets |
| 11 | `os-calc` | Калькулятор | Engineering units, voltage/current/power and number bases |
| 12 | `text-doc-view` | Текст и документы | Manifests, JSON, configs, scripts and logs |
| 13 | `media-gallery` | Галерея | Bench photos, screenshots, waveforms and diagrams |
| 14 | `av-player` | Аудио и видео | Playback, test signals and captured test sessions |
| 15 | `term-sysmon` | Терминал и монитор | Process/CPU/NPU observation, bus inventory and serial diagnostics |

The machine-readable catalogue lives at `catalogs/system-applications.v1.json`; its packaged copy is `duckos/desktop/system-applications.v1.json`. The JSON Schema is `schemas/system-applications.v1.schema.json`. Catalogue maturity remains `specified`: the Mora entry points and Python service contracts are not fifteen native GUI packages.

## Host-side runtime contracts

The `duckos.desktop` package currently provides:

- `catalog.py`: validates and loads the versioned 15-app catalogue.
- `launcher.py`: stable numbered slots, duplicate protection and structured launch requests. It never constructs shell commands or starts processes.
- `packages.py`: bounded SHA-256 inspection and exact-digest local approval for an unsigned file.
- `updates.py`: A/B state machine, signed-evidence gate, inactive-slot planning, activation through a native backend, boot confirmation and fallback selection.
- `bench.py`: board-profile validation, safe-idle/armed/running/cooling/fault state machine, telemetry freshness and rail interlocks.
- `audit.py`: append-only JSONL audit entries with a SHA-256 chain and redacted serial-line capture.
- `storage.py`: bounded JSON state with same-directory atomic replacement and restrictive file permissions.

The helpers are executable Python code for host-side contract testing and development workflows. They are not yet kernel services or native application processes.

## Numbered launcher slots

Slots are one-based and stable. Assignments do not shift when another slot is cleared. One app can occupy only one slot; replacing an occupied slot requires an explicit flag.

```sh
duckos desktop catalog
duckos desktop slots --state ~/.local/state/duckos/launcher.json list
duckos desktop slots --state ~/.local/state/duckos/launcher.json assign 1 sys-settings
duckos desktop slots --state ~/.local/state/duckos/launcher.json resolve 1
duckos desktop slots --state ~/.local/state/duckos/launcher.json unassign 1
```

A launch request is a structured object for a future privileged launcher/IPC service. `process_created` and `shell_command_created` remain false. No manifest string is passed to a shell.

## Package integrity and unsigned files

```sh
duckos desktop package-verify ./candidate.pkg --trust-store ~/.local/state/duckos/trust.json
duckos desktop package-approve ./candidate.pkg --trust-store ~/.local/state/duckos/trust.json --confirm-unsigned
duckos desktop package-verify ./candidate.pkg --trust-store ~/.local/state/duckos/trust.json
```

The package helper streams SHA-256 in bounded chunks and rejects empty, oversized and symbolic-link paths. An unsigned approval is stored against the exact 64-character SHA-256 digest, not the filename. Changing one byte creates a different identity and needs a new approval. Approval does not install or execute the file.

SHA-256 establishes byte equality, not publisher identity. Cryptographic publisher verification must be provided by a trusted signature-verifier adapter and a managed trust store. The current CLI does not claim that it verifies publisher signatures.

## A/B system image state

```sh
duckos desktop image-state --state ~/.local/state/duckos/images.json
```

A planned update must target the inactive, unconfirmed slot, match the staged file hash and carry verified signature evidence. The default manager has no native image backend, so `activate` fails closed. A hardware-specific backend must write and read back the inactive image, set the next boot target and expose boot success/failure. The old confirmed slot remains the recovery target until the new boot is confirmed.

The system-image slots A/B are different from the hardware fixture slots A/B used to identify a board or device under test.

## Hardware bench

A board profile is a separately reviewed JSON file conforming to `duckos.bench-profile.v1`; see `schemas/bench-profile.v1.schema.json`. It supplies the board identity, fixture slots, permitted serial ports, maximum telemetry age, named power rails and approved test durations.

```sh
duckos desktop bench-profile ./bench/board-rev-a.json
```

The CLI validates the profile only. A native `BenchAdapter` is required for physical connection. Before a run, the controller checks that the discovered board identity matches the profile, telemetry is recent, each configured voltage is in range, current is under its limit and temperature is below its ceiling. Faults call the adapter's emergency-disable method. A normal stop enters `cooling`; the fixture cannot return to safe idle until every rail is below its cooldown threshold.

The adapter reports configured bus link state/width/speed, GPU/NPU presence, temperature/utilization and timestamped probe measurements alongside power-rail telemetry. The controller rejects missing required devices, unhealthy bus status, out-of-profile link width/speed, NPU/GPU temperature or utilization violations, stale probes and probe values outside their calibrated range. The adapter interface deliberately has no arbitrary register-write or free-form GPIO method. A board-specific implementation must expose only approved operations for that exact revision. Do not derive power limits from a generic motherboard guess. NPU counters, PCIe lane state and probes require actual device-specific drivers and calibrated measurement sources.

## Serial log and audit

Serial lines are associated with a session ID, a configured port and fixture slot A/B. Password, token, secret, authorization and API-key values are redacted before they are appended. Each event includes UTC time, a monotonic sequence and the previous record's digest; `AuditLog.verify()` checks the chain.

Construct `SerialLogWriter` with the selected profile's `serial_ports` list so it rejects unapproved port names. The journal can be checked with `duckos desktop audit-verify ./bench-session.jsonl`. The host-side recorder accepts lines from a future native UART/USB-serial adapter; it does not open arbitrary serial ports by itself.

## Mora desktop integration

Mora exposes a single **System Apps** launcher entry with all fifteen utility identities and their API/permission declarations. The seven first-party product apps remain unchanged. The entries currently provide service descriptions and maturity boundaries; they do not pretend that unimplemented native APIs are connected.

## Verification

```sh
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
python tools/validate_system_apps.py
npm test
```

These checks validate local catalogue, state-machine and browser-shell contracts. They do not prove physical power switching, PCIe access, NPU telemetry, UART hardware access, kernel sandbox enforcement, a native compositor, a real package signature verifier or bootable A/B images.
