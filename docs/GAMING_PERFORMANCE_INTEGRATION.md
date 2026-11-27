# Mora Gaming Workspace and OPlague Integration

## What is connected now

Mora has a dedicated Gaming Performance workspace in its application catalogue. It explains and links to OPlague's native gaming workbench, documentation and release page. The two projects share the same product vocabulary and a versioned capability contract.

OPlague implements the local operations: hardware and signed-driver metadata inventory, exact hardware/driver fingerprinting, atomic configuration snapshots, reversible Windows power-plan sessions, optional NVIDIA sensor readings through nvidia-smi, read-only WHEA/Display recovery-event collection, frame-time CSV analysis and operator-validated profile caching. Unsupported telemetry providers remain explicitly unavailable.

## What the browser shell cannot do

Mora currently runs as a static browser/PWA shell. A web page cannot safely enumerate arbitrary PCI/USB devices, inspect the Windows driver store, change a Windows power scheme, read raw GPU telemetry or launch an arbitrary local executable. The Gaming workspace therefore does not pretend these controls are live. Use the OPlague Windows desktop application for host operations.

## Native bridge contract

The JSON Schema at ../mora/contracts/oplague-gaming.v1.schema.json defines the request/response envelope for a future DAKOS native host service. It includes narrowly-scoped capabilities for hardware reads, snapshots, temporary power-plan sessions, benchmark comparison and manually validated profile writes.

A production bridge must be implemented by the DAKOS native service layer, not by a web page. Before enabling it, the host must:

1. Bind requests to the active local OS user and an authenticated Mora origin; never expose an unauthenticated localhost HTTP endpoint.
2. Validate the schema, request expiry, nonce/replay protection and capability-to-consent mapping.
3. Ask the user before every system-changing session start; allow read-only calls to remain separately permissioned.
4. Accept enumerated actions and opaque file handles only. Never pass web-provided strings to a shell or accept arbitrary commands, registry paths, driver package URLs or executable paths.
5. Keep security services and anti-cheat protections untouched; log the action, pre-change snapshot, result and rollback state.
6. Return a structured response with an explicit status. An unsupported capability must be reported as unsupported, not simulated as success.

## Shared operational boundary

Driver acquisition and replacement are not implemented by this gaming integration. Any future driver workflow must use verified vendor/OEM provenance, signature verification, an independently reviewed compatibility result, a restorable driver-package backup and explicit per-device confirmation. A driver update must not be inferred from a performance profile.

The benchmark contract uses measured frame-time samples. Temperature, GPU-engine utilization, VRAM pressure, WHEA events and network latency must come from real providers and carry provider, timestamp and validity metadata; missing sensor data stays unknown.
