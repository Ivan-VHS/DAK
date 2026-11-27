# DAK application contracts

**Version:** 1  
**Language:** Reaper  
**Status:** contract layer implemented on `feat/dak-application-runtime-v1`; application backends are not claimed complete.

## Scope

This directory defines the stable application-facing contract surface for the currently registered DAK catalogue. It is deliberately separate from the kernel: an application admission result is a policy decision, not permission to execute host commands or touch hardware.

The current source catalogues reconcile to **45 unique application identities**:

- 30 entries in `mora/apps.json`;
- 28 entries in `catalogs/dak-base-applications.v1.yaml`;
- 13 product identities occur in both catalogues;
- the 20-entry preinstalled catalogue is a subset, not an additional set of 20.

The repository does not currently contain a canonical manifest listing approximately 133 applications. This implementation does not invent the missing entries. Add them to the authoritative catalogue with product scope, owner, permissions, and acceptance criteria before extending the runtime.

## Files

- `runtime.rpr` — 45 descriptors, canonical ID resolution, capability/operation admission, consent gates, bounded request metadata, lifecycle transitions and cross-app event envelope validation.
- `domain_contracts.rpr` — bounded, application-specific payload validators for every registered identity.
- `workflows.rpr` — the nine cross-application workflows already specified by the preinstalled catalogue.
- `../contract_tests.rpr` — tree-walk and VM contract tests for the three modules.

## Request envelope

The application admission contract accepts this seven-field tuple:

`[request_id, app_id, operation, capability, payload_bytes, data_scope, user_consent]`

The envelope is rejected when its size is invalid, request ID or application ID is unknown, operation or capability is not declared by that application, payload exceeds 65,536 bytes, data scope differs from the app descriptor, capability is not granted, or a consent-sensitive action lacks explicit consent.

A successful result is `admit-policy-only`. It means only that the request passed these metadata checks. It does **not** execute the operation, persist data, open a window, spawn a process, install a package, grant a kernel capability or access a device.

## Domain payload tuples

Lengths are byte counts unless the row explicitly says otherwise. These are V1 wire-contract tuples, not native storage schemas.

| Application | Payload tuple |
|---|---|
| Settings | `[key_bytes, value_bytes, scope(user/workspace), consent]` |
| Files | `[operation, path_component_count, byte_count, source_selected, consent]` |
| Calendar | `[operation, start_epoch, end_epoch, timezone_bytes, consent]` |
| Clock | `[kind(alarm/timer/stopwatch), time_value, label_bytes, consent]` |
| Notes | `[text_bytes, scope(private/workspace), consent]` |
| Tasks and Reminders | `[title_bytes, due_epoch, priority(0..5), consent]` |
| Calculator | `[expression_bytes, precision(0..100)]` |
| Web Browser | `[url_bytes, permission(ask/allow/deny), private_session, consent]` |
| Mail | `[account_ref_bytes, recipient_count(1..100), message_bytes, send_consent]` |
| Contacts | `[operation, display_name_bytes, scope(local/user-selected-export), consent]` |
| Gallery | `[media_count, total_bytes, source_selected, consent]` |
| Media Player | `[operation(play/pause/stop), source_selected, network_opt_in, stream_consent]` |
| Document Editor | `[operation, source_selected, document_bytes, export_consent]` |
| Terminal and System Monitor | `[action(inspect/logs/process-list/command-preview), argv_count, capability, privileged(false)]` |
| Software Center | `[action, package_id_bytes, version_bytes, explicit_confirmation]` |
| Cockos | `[sample_rate(8–192 kHz), channels(1–32), bit_depth(16/24/32), period_frames(16–8192), recording_consent]` |
| Kavun | `[media_id, media_bytes, visibility(private/workspace/shared-review), source_selected, optional_processing_consent]` |
| Ka-bon | `[entry_id, amount_minor_units, 3-character_currency, category, user_confirmed]` |
| Gloverty | `[rule_id, trigger, action, scope(local/user-selected), action_consent, enabled]` |
| Po | `[url_bytes, session(normal/private), site_permission(ask/allow/deny), consent]` |
| Illidia | `[game_id, title_bytes, executable_path_bytes, launch_consent, clip_share_consent]` |
| Unify | `[device_id, fingerprint_bytes, state(requested/paired/revoked), pairing_consent, sync_opt_in]` |
| Sestem | `[component, maturity_status, evidence_ref, timestamp]` |
| SetupUP | `[theme(dark/light), locale(en/uk/ru), reduced_motion, setup_complete]` |
| ORGze | `[list_id, name_bytes, item_count(0..10000), state(open/paused/done), consent]` |
| Abriganza | `[filename_bytes, archive_bytes, entry_count, max_depth(0..32), extraction_enabled(false)]` |
| Olaab | `[collection_id, name_bytes, media_count, storage_scope(local-index)]` |
| Concrete Thump | `[bpm(30..300), swing(0..100), beats_per_bar(1..32), steps(1..128)]` |
| Seu-Beu | `[recipient_confirmed, content_scope_confirmed, retention_confirmed, permissions_confirmed, approved]` |
| Love-IL | `[entry_id, text_bytes, timestamp, storage_scope(local-private)]` |
| Poi | `[capture_id, text_bytes, timestamp]` |
| Poi-2 | `[card_id, title_bytes, body_bytes, source_kind(local-reference)]` |
| Po-2 | `[route_id, stop_count(1..256), manually_ordered(true), gps_tracking(false)]` |
| GameCharager | `[game_id, title_bytes, executable_path_bytes, state(metadata-only/inspected), launch_enabled(false)]` |
| EXEdotEXE | `[format(pe/elf), file_bytes, header_bytes, sha256_hex_chars(64), read_only(true)]` |
| Red Sparrow | `[project_id, asset_count(0..10000), total_asset_bytes, local_only(true)]` |
| Mora AI | `[input_bytes, output_bytes, mode(local/network-opt-in), consent, session_policy(bounded-session)]` |
| Sentinel | `[finding_id, severity(0..4), evidence_bytes, remediation_mode(request-only)]` |
| Restore | `[snapshot_id, snapshot_bytes, hash_verified, restore_consent]` |
| Bridge | `[package_id, format(pe32/pe32+/elf), abi, isolated, execute(false)]` |
| Control | `[workspace_id, window_count(1..64), scope(local/workspace), reversible]` |
| Proof | `[algorithm(sha256/sha384/sha512), digest_hex_chars(64/96/128), source_bytes, verified]` |
| Mora Boost | `[profile_id, mode(balanced/quiet/responsive), target_fps(30..360), apply_to_hardware(false)]` |
| DAK Desktop | `[action(audit/move-selected/startup-change), target, scope(current-user), consent, reversible]` |
| Mora Commons | `[query_bytes, limit(1..100), category(all/system/productivity/multimedia)]` |

## Versioned inter-app workflows

Every workflow event uses:

`[event_id, source_app, target_app, action_id, payload_bytes, user_consent, idempotency_key, version]`

V1 is limited to 65,536 bytes of metadata per event. Large media and file transfer require a separate bounded transfer protocol; this workflow envelope is not a file-transfer implementation.

| Workflow | Route | Action |
|---|---|---|
| `automation.weekly-budget-summary.v1` | Gloverty → Ka-bon | `prepare_weekly_budget_summary` |
| `media.event-memory-assembly.v1` | Cockos → Kavun | `add_to_event_slice` |
| `continuity.browser-tabs.v1` | Po → Unify | `transfer_tabs_to_paired_device` |
| `continuity.game-clips.v1` | Illidia → Unify | `transfer_clip_to_paired_device` |
| `planning.poi-to-orriganize.v1` | Poi → ORGze | `add_capture_to_project_list` |
| `media.olaab-to-kavun.v1` | Olaab → Kavun | `open_selected_media_collection` |
| `knowledge.poi-to-poi-2.v1` | Poi → Poi-2 | `create_knowledge_card_from_selected_text` |
| `gaming.gamecharager-to-exedotexe.v1` | GameCharager → EXEdotEXE | `request_read_only_executable_inspection` |
| `audio.concrete-thump-to-cockos.v1` | Concrete Thump → Cockos | `hand_off_bpm_and_swing_metadata` |

## Application lifecycle

Allowed transitions are explicit:

- `created → ready | error`
- `ready → running | disabled | error`
- `running → ready | stopping | error`
- `stopping → stopped | error`
- `disabled → ready | stopped`
- `error → stopped`

A stopped application cannot be reopened by an implicit state transition. A package manager or supervisor must create a new lifecycle instance.

## Implementation boundary

The present code is the first contract layer. It does not yet contain 45 native application frontends or domain services. The next implementation slices must add independently testable services for local persistence, VFS access, notifications, media, scheduler, package management, pairing, and process launch—then connect each frontend through the contracts above.

Keep maturity honest: a catalogue entry, payload validator or host-native demo window is not proof of a working DAK OS application or kernel-enforced capability.
