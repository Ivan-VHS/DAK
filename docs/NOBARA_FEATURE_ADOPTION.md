# Nobara-inspired DuckOS experience adoption

**Review date:** 2026-11-25  
**Target:** DuckOS / Mora  
**Method:** clean-room implementation of general product and interaction concepts

## Review scope

The review covered the Nobara Project home page and downloads page, its new-user guide and FAQ, plus the wiki topics most relevant to an operating-system experience: package and kernel modifications, update behavior, HTPC/handheld sessions, Flatpak sources, controller support, GPU support, creator tools, Secure Boot and troubleshooting.

Primary sources:
- [Nobara home page](https://nobaraproject.org/index.html#hero)
- [Downloads and editions](https://nobaraproject.org/download.html)
- [New-user guide](https://wiki.nobaraproject.org/en/new-user-guide-general-guidelines)
- [FAQ](https://wiki.nobaraproject.org/en/FAQ/FAQ)
- [System updates](https://wiki.nobaraproject.org/en/general-usage/troubleshooting/update-system)
- [Package modifications](https://wiki.nobaraproject.org/en/modifications/packages)
- [Kernel modifications](https://wiki.nobaraproject.org/en/modifications/kernel)
- [HTPC and Gamescope sessions](https://wiki.nobaraproject.org/en/general-usage/troubleshooting/convert-htpc)
- [Flatpak source policy](https://wiki.nobaraproject.org/en/general-usage/flatpaks/nobara-flatpak)
- [Xbox controller support](https://wiki.nobaraproject.org/en/gaming/controllers/xbox)
- [Nintendo controller support](https://wiki.nobaraproject.org/en/gaming/controllers/nintendo-controller-support)
- [OBS Studio](https://wiki.nobaraproject.org/en/general-usage/additional-software/obs-studio)
- [GPU Screen Recorder](https://wiki.nobaraproject.org/en/general-usage/additional-software/GPU-Screen-Recorder)
- [MangoJuice / MangoHUD setup](https://wiki.nobaraproject.org/en/general-usage/additional-software/MangoJuice)
- [Nobara Secure Boot guide](https://wiki.nobaraproject.org/en/secureboot)
- [Nobara update transaction notes](https://updates.nobaraproject.org/updates.txt)
- [Updating troubleshooting](https://wiki.nobaraproject.org/en/general-usage/troubleshooting/updating-troubleshooting)
- [Kernel fallback versions](https://wiki.nobaraproject.org/en/general-usage/troubleshooting/why-3-versions)
- [DaVinci Resolve wizard guidance](https://wiki.nobaraproject.org/en/general-usage/additional-software/davinci-resolve)

This is a feature and documentation review, not a claim that every Wiki.js article, historical post or external package was independently audited.

## Feature transfer map

| Nobara product idea | DuckOS adaptation | Current maturity |
|---|---|---|
| First-boot welcome and setup suggestions | SetupUP presents named Mora experience profiles; saves selected profile in current-user QSettings | Partial, host shell only |
| Separate desktop/HTPC/handheld editions | One Duck identity with Workstation, Creator, Living-room and Handheld presentation profiles; no copied themes or ISO images | Partial, local UI preference |
| Integrated update manager | Sestem System Center explains the intended staged transaction and clearly shows that the native updater is not connected | UI boundary plus Reaper reference contract |
| Ordered updates and per-group recovery | Reaper validates Kernel → Graphics → System core → Desktop → Optional sequencing and safe rollback preconditions | Reference policy only |
| Package repositories and app stores | Mora Commons and federated workbenches remain metadata/discovery surfaces with explicit source boundaries | Partial catalogue; installation unavailable |
| Driver manager and GPU support | Unify shows device-service maturity and the read-only ecosystem boundary; no live hardware or driver actions are exposed as working | Planned native service |
| Gaming-ready desktop | Mora Boost stores a user-local gaming preference (Balanced / Low latency / Image quality) | Partial local preference |
| Gamescope/Steam living-room and handheld paths | UI profiles prepare larger catalogue tiles and controller-first presentation preferences | Partial presentation only; no Gamescope/session/input runtime |
| OBS, capture, audio and creator tools | Preserve Reaper, VentuSample and OPlague as independently licensed ecosystem workbenches; future creator profile is presentation only | Existing integrations remain separate user-space tools |
| GPU overlay and screen capture | Future GPU service must report provider, codec, permission and capture scope; no screen recorder or instant-replay service is connected | Planned |
| OBS and professional media applications | Treat hardware encode/decode and plug-in compatibility as target-specific; third-party apps stay separately licensed and user-installed | No bundled creator packages |
| Controller, GPU and codec compatibility guides | Add a future device compatibility matrix with exact device/driver/runtime evidence; support claims expire when upstream driver support changes | Planned |
| Troubleshooting, first steps and FAQ | Documented maturity, safe next steps, repository/GPG/disk-space diagnosis, fallback-boot policy and visible unavailable states | Documentation and host UI |

## Native work delivered in this change

- Adds `mora/experience.v1.json` and a JSON Schema for the four Duck-owned presentation profiles.
- Adds a SetupUP native Mora panel that persists only a user-local shell preference.
- Adds a Sestem system-center panel that states the updater and package service are not connected; update controls remain disabled.
- Adds a Unify hardware-center panel that states live device enumeration and driver install/update are not connected.
- Adds a Mora Boost local gaming preference panel; it does not change device power, clocks, voltage, drivers or scheduling.
- Adapts Mora's application catalogue density to the selected shell profile.
- Adds Reaper reference contracts for workload-profile scope, staged update order/rollback gates and software-source admission.
- Extends native smoke-test assertions for the new host-shell panels.

The Qt executable still runs on the host operating system. The Stage 1 DuckOS kernel does not launch these windows.

## Explicitly not implemented

This adoption does **not** add:
- a disk installer, user-session manager, package manager or atomic image updater;
- PCI/USB/ACPI hardware discovery, kernel driver loading, driver signing or driver installation;
- a real rollback engine, snapshots or a boot-success/A-B slot service;
- Gamescope, SteamOS-like session, process launching, power/TDP/clock controls or controller remapping;
- OBS, DaVinci Resolve, codecs, Steam/Proton/Wine, proprietary GPU packages or any third-party application payload;
- Secure Boot keys, EAC kernel, vendor kernel patches, TPM enrollment or verified-boot claims;
- GPU telemetry providers, sensor readers, live benchmarking or frame-time capture inside Mora.
- OBS, GPU Screen Recorder, MangoHUD/MangoJuice, DaVinci Resolve or other third-party creator software bundles or installers.

The Reaper modules are executable policy examples on the reference runtime. Passing their checks does not prove kernel enforcement, package installation, hardware access or rollback.

## Copyright, licenses and attribution

This work was written independently for DuckOS. It adopts general operating-system usability ideas—first-run setup, named usage profiles, explicit system centers, staged update policy and distinct gaming/creator workflows—not Nobara's implementation.

No Nobara source code, logo, screenshots, visual assets, wallpapers, theme, distinctive violet palette, font files, page copy, package binaries or kernel patches are copied into DuckOS. Nobara's name is used only to identify the research source. The DuckOS black/white/yellow design tokens and Mora application names remain Duck-owned.

Upstream projects and tools retain their own authorship and license terms. A source pin or catalogue entry does not grant permission to redistribute a binary or to relicense its source. The DAK repository root currently has no root `LICENSE` declaration; this change does not assume MIT, Apache-2.0 or any other license for DuckOS itself. Choose and approve the DAK license separately before redistribution.

## Verification boundary

The source and tests added in this change are checked by the existing Reaper contract and Mora native CI workflows. Host Qt CI can verify the native shell and widget wiring; Reaper CI exercises reference policy. Neither workflow turns the Stage 1 kernel into a desktop operating system.
