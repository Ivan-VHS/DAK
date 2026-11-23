# DuckOS deep settings and user-space tools

**Author / developer:** Ivan-VHS.  
**Status:** partial native user-space implementation.  
**Scope:** Duck Desktop settings, validated user profiles, safe diagnostics and built-in data utilities.

This document records behavior that exists in source. It deliberately separates a saved configuration preference from an operating-system operation that would require a privileged service, kernel, driver or hardware interface.

## 1. Where to open it

Start the native maintenance workspace:

~~~sh
python -m pip install -e .
duckos desktop gui
~~~

Open the **Настройки** tab. It is hosted in the native Tk Duck Desktop utility, not in the browser-only Mora shell.

The same settings store and diagnostics can be used from the CLI:

~~~sh
duckos settings show
duckos settings profile list
duckos settings profile create "Студия" --clone-from "Работа"
duckos settings profile activate "Студия"
duckos settings export ./duck-settings.json
duckos settings import ./duck-settings.json
duckos settings network-test example.com --port 443
~~~

Run duckos --help, duckos settings --help or duckos tools --help for the registered commands. These commands use explicit argument parsers and never dispatch to a host shell.

## 2. Settings store

Implemented in duckos/settings.py:

- A single user-scoped JSON settings file. Linux and macOS use XDG_CONFIG_HOME/duckos/settings.json when set, otherwise ~/.config/duckos/settings.json; Windows uses %LOCALAPPDATA%/DuckOS/settings.json.
- A versioned duckos.settings.v1 format with four initial profiles: Дом, Работа, Игра and Дорога.
- Atomic replacement through a temporary file, flush, fsync and os.replace.
- Owner-only file permissions where the host supports POSIX permissions.
- Input size limits, symbolic-link rejection for managed settings and snapshot paths, and schema validation before a change is committed.
- A bounded history of up to 20 snapshots and 500 audit events.
- JSON export/import with validation and a snapshot of the previous state before import.
- Profile cloning and active-profile selection.
- A settings search index that returns both the matching parameter and its full breadcrumb path.

An update is a transaction against the Duck user settings document. system_changes_performed is always false: saving a profile does not silently configure a host network adapter, power controller, display driver, firmware variable or kernel service.

Unsupported schema versions are rejected without overwriting the previous file. A future migration must be implemented and tested before the version is advanced.

## 3. Settings surface

Implemented in duckos/desktop/settings_panel.py and connected from duckos/desktop/native_ui.py.

### Network profile

The editor stores DHCP or static preferences for IPv4, automatic or static IPv6, address, prefix, IPv4 netmask, gateway, DNS 1/2, DoH URL, DoT server, MTU and proxy URL.

Validation is performed before saving:

- IPv4 and IPv6 address parsing and prefix bounds;
- netmask/prefix consistency;
- same-subnet IPv4 gateway check for static profiles;
- DNS address validation;
- HTTPS requirement for DoH;
- proxy scheme and host validation;
- MTU range 576–9000.

The **Проверить узел** action runs a bounded DNS lookup and TCP connection check, reporting DNS/connect time and resolved addresses. It does not send ICMP ping packets and does not calculate jitter or packet-loss statistics.

**Not implemented:** direct changes to DHCP clients, NIC state, routing tables, interface MTU, system resolver, VPN/proxy routing, packet capture or IP conflict detection. These require a platform network service and an explicit permission boundary. A profile save therefore cannot disconnect the host.

### Power profile

The editor stores an energy preference, automatic eco threshold, whether eco is battery-only, charge limit, screen timeouts and sleep timeouts for AC/battery use.

**Not implemented:** CPU/GPU frequency changes, firmware charge caps, battery-cell health/charge-cycle collection, wake-lock ownership, thermal throttling controls or actual suspend/hibernate scheduling. A preference is not reported as an applied power policy.

### Appearance profile

The editor stores system/light/dark preference, a #RRGGBB accent, UI and icon scales, density and reduced-motion preference. The accent preview updates while editing.

**Not implemented:** a global native compositor/theme engine, automatic time-of-day switching, contrast certification or system-wide DPI changes. The stored values are ready for a future native theme service; the current panel does not claim to restyle every host window.

### Profiles, history and recovery

The profile panel creates independent copies, selects an active settings profile and summarizes the network, power and appearance preference for each profile.

The history panel displays snapshots and events, and supports JSON import/export. The store exposes SettingsStore.rollback(snapshot_id) for a validated, explicit rollback. It does not restore arbitrary host settings or files.

## 4. Built-in user-space tools

Implemented in duckos/toolbox.py and exposed through duckos tools:

| Command | Working behavior | Boundary |
|---|---|---|
| tools secret | OS-CSPRNG-backed token generation, 16–256 characters | Not a password vault or account manager |
| tools text-stats FILE | Character, non-whitespace character, word, line, paragraph and UTF-8 byte counts | Reads a bounded UTF-8 text file |
| tools csv-inspect FILE | Header, column count, row count, width errors and preview | Does not rewrite the source CSV |
| tools data-convert FILE --to json/xml | JSON ↔ XML structural conversion | YAML/TOML are not included in this first implementation |
| tools encoding-convert FILE OUTPUT | Strict encoding conversion and LF/CRLF/CR normalization | Does not guess a broken source encoding |
| tools units VALUE FROM TO | Common SI length/mass, time, data-size and temperature conversion | Rejects incompatible dimensions |
| tools tls-check HOST | TLS handshake, system trust validation, protocol, cipher and certificate dates | Requires a reachable network endpoint |
| tools rss FILE | Bounded RSS/Atom XML parsing and item preview | Reads a local feed file; no unattended background polling |
| tools sha256 FILE | Bounded SHA-256 streaming hash for a regular file | A hash is not a digital signature or author identity |
| tools ports | Read-only TCP listening-port inventory via psutil or Linux procfs | Provider permissions and platform support can limit results |

Previously implemented supporting functions remain available:

- duckos hardware-inventory — bounded read-only PCI/USB (Linux) or PnP (Windows) inventory.
- duckos desktop audit — read-only desktop, startup and resource snapshot.
- duckos desktop startup list/disable/restore — reversible current-user startup controls.
- duckos bridge — runtime discovery and non-executing compatibility launch plans.
- duckos build-release, verify-release, deployment-plan — signed component-bundle verification and non-destructive deployment plans.

## 5. Traceability to the 66 deep-settings rules

| Rule group | Working implementation | Remaining gaps |
|---|---|---|
| 1–12 Navigation | Tabbed sections, visible breadcrumb, global parameter search with result path, distinct information text, form-dirty state and exit confirmation, scrollable settings pages | Explicit multi-level back stack, dedicated settings root/overview, restored scroll offsets, full keyboard/screen-reader audit |
| 13–24 Network | DHCP/static profile fields, IPv4/IPv6 parsing, CIDR/netmask checks, gateway validation, separate DNS 1/2, DoH/DoT format checks, MTU bounds, separate proxy fields, DNS/TCP connectivity test | Host adapter discovery/grouping, actual network changes, temporary apply/auto-rollback, IP conflict detection, live route and link status, VPN integration |
| 25–36 Power | Separate AC/battery timeout fields, named power preferences, configurable eco threshold and charge limit | Battery sensor/health/charge-cycle provider, actual charge cap, wake locks, thermal controls and live power enforcement |
| 37–48 Appearance | Central profile values, theme/accent separation, live accent preview, independent UI/icon scales, density and reduced-motion values, per-profile presets | Global design-token runtime, contrast checking, time-based theme, full-window restyling and high-DPI compositor qualification |
| 49–66 State and safety | Single versioned store, draft vs saved profile, Apply/Cancel/Defaults, validation before commit, user profiles, atomic persistence, import/export, bounded event log, snapshots, rollback API, symlink-aware paths | Privileged permission broker, multi-process change arbitration, schema migration fixtures, automated deep-branch GUI/accessibility matrix |

The current test suite adds focused validation of profiles, IPv4/IPv6, DNS, MTU, export/import, snapshots, rollback, symlink rejection and user-space utilities. GUI interaction and hardware integration still require platform tests.

## 6. Relationship to application IDs 134–199

The following added catalogue functions now have real user-space building blocks:

| IDs | Capability now present |
|---|---|
| 148, 152 | DNS resolution and TCP connectivity timing (not full route/jitter monitoring) |
| 149 | TLS endpoint/certificate-chain validation against the system trust store |
| 155 | Local RSS/Atom parsing |
| 158 | Cryptographically random secret generation |
| 161 | Read-only listening TCP-port inventory where a provider is available |
| 171 | Encoding and line-ending conversion |
| 172 | CSV inspection and row validation |
| 173 | JSON ↔ XML conversion; YAML/TOML remain pending |
| 175 | Text structure and length statistics |
| 195 | Common unit conversion |
| 199 | Partial diagnostics through desktop/resource audit and settings validation |

The other proposed applications remain specified or planned until their source implementation and acceptance tests exist. In particular, EFI boot selection, environment mutation, peripheral control, filesystem repair, kernel updates, process descriptor inspection, packet capture, file sharing server, NTP/Wake-on-LAN, tunnel routing, cryptographic file encryption/signing, certificate-store mutation, vulnerability scanning, sandbox enforcement, secure free-space erasure, session locking, TOTP vault, spelling/translation, code formatter, media editing, audio generation, build-script execution and a full OS health wizard are not represented by placeholder controls.

## 7. Native OS and host-operation boundary

The repository's broader architecture documents correctly identify kernel, firmware, driver and compositor work that a user-space Python utility cannot deliver. The following remain outside this implementation:

- UEFI/BIOS bootloader, physical page allocator, interrupt controller and actual kernel scheduler;
- system-call ABI, protected process model, enforced capabilities and isolated driver loading;
- filesystem driver, disk repair and destructive disk installer;
- production compositor/window manager, device driver control and hardware power service;
- system DNS/network configuration, firewall, packet capture and privileged tunnel routing;
- kernel-enforced application sandbox and secure session manager.

Do not mark these as implemented because their settings are visible. Each needs its own platform service, permissions, source and target-specific tests.

## 8. Verification

Run from the repository root:

~~~sh
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
python tools/validate_engineering_evolution.py
npm test
~~~

The Python tests verify reference user-space behavior. They do not prove firmware boot, kernel privilege, hardware access, compositor integration or Windows/Linux system-setting enforcement.
