# DuckOS console navigation and content rights

## Product intent

DuckOS adds a controller-first living-room mode to the existing Mora desktop. It uses its own graphite, white and yellow design language, its own card artwork and newly generated interface cues. It does not copy another console's logos, blade artwork, iconography, distinctive sound samples or proprietary assets.

The browser surface is a console-friendly shell, not a native console compositor. Controller support is provided through the browser Gamepad API when available on a secure origin. Native USB/Bluetooth device discovery, system-wide controller routing and game input remain native-service work.

## Controller contract

When **TV mode** is enabled, the visible focus target moves through the geometry of the current UI rather than relying on DOM tab order alone.

| Input | Mora action |
|---|---|
| D-pad / left stick | Move focus to the nearest visible item in that direction |
| A / Enter | Select the focused control or game card |
| B / Escape | Close the current flyout/context menu, navigate back in Duck Files, or close the top window |
| X | Open details/context actions for the selected item; game cards open Rights Center |
| Y | Focus Duck Files search, or open the app search menu |

The standard Gamepad API mapping uses face buttons 0–3 and D-pad buttons 12–15. The left stick uses a dead-zone threshold of 0.58. Focus moves are edge-triggered; holding a direction does not repeatedly scroll the page. Arrow keys and A/B/X/Y keys provide a keyboard fallback in TV mode.

TV mode increases card sizes, type, hit areas and focus contrast. Reduced-motion preferences suppress decorative movement. It does not change native display resolution, HDMI behavior, refresh rate or system scaling.

Short synthesized tones indicate focus, selection, details and back. They are original Web Audio oscillator cues, not samples from another console. Cues can be disabled in Settings. Browser autoplay restrictions may leave the interface silent until user interaction or when Web Audio is unavailable.

## Fifteen rules and implementation state

1. **Controller-first navigation — implemented in Mora browser mode.** Focus movement, A/B/X/Y, directional pad, left stick and keyboard fallback are wired to the current interface. Native controller enumeration and routing outside Mora are not included.
2. **Responsive navigation — partial.** Mora's shell changes focus and panels immediately; expensive publisher checks are explicit CLI operations and are not run on the browser UI thread. A background native rights worker has not been connected.
3. **Living-room readability — implemented in TV mode.** Larger tiles and labels, responsive cards and a high-contrast focus ring are applied without copying a branded console layout.
4. **Tactile feedback — implemented in TV mode.** Brief generated beeps are optional and adjustable. No third-party console sounds are bundled.
5. **Cryptographic entitlement records — contract implemented.** Entitlements carry a publisher key ID, content manifest digest, scope, rights, issue/not-before/expiry times, offline validity and an optional region. Ed25519 verification uses an explicit trusted public-key map.
6. **Profile versus home-device scope — policy implemented; device provisioning pending.** A `profile` grant matches the owner profile. A `home_device` grant matches the supplied registered-device ID and is independent of the local user profile. DuckOS does not yet provision device IDs from hardware attestation or exchange account sessions with a publisher.
7. **Visible source and rights status — partially implemented.** Illidia's sample game cards explicitly say `DEMO · NO LICENSE`. Rights Center previews a selected JSON document but labels it **NOT VERIFIED**. A tile is not marked as licensed merely because a local JSON file exists.
8. **Signature and content-integrity verification — CLI contract implemented; launch gate pending.** `verify-content` checks an Ed25519 publisher signature, the exact signed file list and each SHA-256 digest. This verification is not yet wired into every native package installer or process-launch path; an unrelated launcher could still bypass it.
9. **Rights-preserving backup/transfer — metadata contract implemented.** `build-transfer` copies original signed content manifests and entitlement documents verbatim into a transfer index. It does not copy binaries, reissue tokens, change the owner or widen rights. The receiver must verify signatures and recheck profile/device scope after import.
10. **Save data separated from protected binaries — record contract implemented.** Save records are a distinct `save` content kind and are never represented as a copy of the game package. The local builder records save file digests and player-declared attribution.
11. **Creator and source attribution — partially implemented.** User records capture creator, source description, copyright notice and license ID. Such metadata is marked `self_declared_not_publisher_verified`; it does not prove identity or ownership. Publisher-signed manifests can attest to attribution when the key is trusted.
12. **Capture restrictions — policy metadata implemented; native enforcement pending.** A signed content manifest can declare allowed and denied screenshot, recording and streaming actions. The current API reports policy decisions with `native_enforcement: false`. Only a trusted compositor/capture broker can enforce a system-wide restriction.
13. **Human-readable denial reasons — implemented in rights decisions.** The verifier returns reason codes such as `wrong_profile`, `wrong_home_device`, `expired`, `offline_window_expired`, `region_restricted`, `untrusted_issuer`, `signature_invalid` and `action_not_licensed`, together with a next step.
14. **Offline entitlement checks — contract implemented.** A valid signed token can be evaluated without a network connection until `offline_valid_until). This local verifier does not refresh licenses, revoke tokens or contact a store. Once the offline deadline passes, it blocks and requests reconnection.
15. **Rights and integrity journal — local evidence implemented.** CLI decisions can be written to `~/.duckos/rights-audit.jsonl`. The journal uses sequence numbers and a SHA-256 hash chain; edits or reordering are detected. This is tamper-evident, not immutable: a local administrator who can rewrite the entire file can rebuild the chain.

## Native verification commands

The native CLI is the current verification path. It uses OpenSSL for Ed25519 signatures; no private publisher key is bundled. The caller supplies a publisher public key whose key ID matches the `issuer.key_id` or `publisher.key_id` in the signed document.

```sh
duckos rights verify-entitlement entitlement.json \
  --trusted-key studio-example=/etc/duckos/trust/studio-example.pub \
  --profile-id PROFILE_ID \
  --device-id HOME_DEVICE_ID \
  --offline \
  --action launch

duckos rights verify-content manifest.json ./content-package \
  --trusted-key studio-example=/etc/duckos/trust/studio-example.pub

duckos rights build-transfer records.json rights-transfer.json
duckos rights validate-transfer rights-transfer.json
duckos rights audit-log
```

For an online profile entitlement, omit `--offline` and supply the currently authenticated profile ID. For a home-device entitlement, supply the locally registered home-device ID and the current profile ID may be any local profile. The current CLI accepts identifiers as explicit inputs; it does not authenticate them against a hardware-backed device identity or a cloud account.

The JSON formats are defined in:

- [Entitlement v1](../schemas/entitlement.v1.schema.json)
- [Content manifest v1](../schemas/content-manifest.v1.schema.json)
- [Rights transfer v1](../schemas/rights-transfer.v1.schema.json)
- [User content record v1](../schemas/user-content-record.v1.schema.json)

## Current security boundary

The browser Rights Center only reads small JSON metadata files (up to 2 MiB) and displays them using text nodes. It never verifies or elevates their trust. The UI never grants a license.

The Python module verifies the records when a caller supplies a trusted public key. A production store still needs an issuer/account service, device registration, revocation/renewal protocol, protected key storage, authenticated IPC and a trusted native launcher that enforces the decision before execution. Global capture denial needs the native compositor. Until those components exist, the rights layer is a verifiable local contract, not a complete DRM platform.

No protection mechanism should remove or bypass a legitimate publisher's DRM. The objective is correct attribution, transparent licensing, package-integrity checks and the protection of content owners' and users' rights.
