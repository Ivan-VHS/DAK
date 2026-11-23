# Katyuhen — unified project ecosystem

**Maintainer:** Ivan-VHS  
**Canonical registry:** [ecosystem/katyuhen.v1.json](../ecosystem/katyuhen.v1.json)  
**Mora entry point:** [mora/index.html](../mora/index.html)

Katyuhen connects the independent Ivan-VHS projects through one discoverable workspace, stable project identities, shared design rules and explicit, versioned integration contracts. It is a federation, not a monolithic executable that bundles every project into one process.

## Registered projects

| Project | Responsibility | Current maturity |
|---|---|---|
| DuckOS / Mora | Desktop workspace, system surface, project directory and shared visual identity | Partial: browser shell is implemented; native OS services are separate work |
| Reaper | Programming language, runtime, Studio IDE, language/debug services and native ABI | Partial: Python reference runtime is implemented; C17 parity is partial |
| OPlague | Read-only Windows device/driver inspection and evidence reports | Implemented within its documented read-only scope |
| Pytyliki | Processor inventory, bounded measurement, analysis and C ABI | Implemented within its documented local/observational scope |
| VentuSample | Procedural audio generation, offline DSP, presets and pack export | Implemented within its documented offline scope |

The **Katyuhen** tile in Mora opens the ecosystem directory and links to each project. It does not claim to install, start or control another repository's executable.

## Architecture

- **Workspace — Mora:** one starting point, window model, semantic theme and system-level navigation.
- **Product layer — specialist applications:** Reaper, OPlague, Pytyliki and VentuSample retain their own runtimes, build systems, data formats and domain-specific UI.
- **Contract layer — manifests and interfaces:** every project declares what it provides, consumes and explicitly does not do.
- **Exchange layer — JSON files and selected native ABI:** supported exchanges are versioned and opt-in. There is no implicit network bus or dynamic-library search.
- **Trust layer — validation and approvals:** external content is untrusted until validated; privileged or destructive operations are not inferred from a registry entry.

## Existing integration graph

| Source → target | Contract | Transport | State |
|---|---|---|---|
| OPlague → Reaper | Read-only device snapshot v1 | Versioned JSON file | Specified |
| Pytyliki → Reaper | Pytyliki C ABI v1 | Explicit trusted library path | Specified |
| VentuSample → Reaper | VentuSample pack v1 | Versioned JSON manifest | Implemented: metadata audit only |
| Reaper → VentuSample | Reaper C ABI v1 | Explicit local checkout at build time | Partial, optional |
| Pytyliki → VentuSample | Pytyliki C ABI v1 | Explicit trusted library path | Partial, optional |
| Pytyliki → OPlague | Pytyliki C ABI v1 | Explicit trusted library path | Specified |

A declared or specified edge is not proof that a peer is installed, currently available, ABI-compatible or safe to load. Check the cited project evidence and run the integration tests in the owning repository.

## Shared visual language

DuckOS owns `mora.theme.v1` in [mora/theme.json](../mora/theme.json). It defines semantic colors, spacing, geometry, typography and motion. Native clients may translate those semantic values into Qt or platform-specific tokens locally. They must keep readable contrast, keyboard focus and reduced-motion support, and must not fetch CSS or theme assets from a remote server at runtime.

Specialist products keep the layouts their jobs require. Katyuhen aligns identity and interaction conventions; it does not flatten an audio editor, hardware workbench and code IDE into the same UI.

## Security and data rules

1. Keep projects independently buildable and useful without their peers.
2. Validate every file exchange for schema, version, size, bounds and provenance.
3. Load native code only from an explicit trusted path after ABI and platform checks. Never execute a manifest-provided shell command.
4. Keep driver inspection separate from driver installation or device mutation. Katyuhen grants no hardware privilege.
5. Make automation typed, reviewable, auditable and explicitly approved before consequential actions.
6. Keep user data owned by the application that created it. No automatic upload, telemetry or cross-project sync is implied by registration.
7. Report implementation maturity from source, build and tests; never promote a planned service because a UI entry exists.

## Adding a project

1. Add `integrations/katyuhen/manifest.json` using [the project manifest schema](../schemas/katyuhen.project.v1.schema.json).
2. Add a project-specific `docs/KATYUHEN_INTEGRATION.md` identifying ownership, real interfaces, non-goals and validation.
3. Register the project and evidence-backed integration edges in the central registry.
4. Add a Mora directory card only when the repository and entry point are confirmed.
5. Validate IDs, manifest paths, integration endpoints and maturity labels. Keep optional dependencies optional.

## Validation

From the DuckOS repository root, run:

```sh
npm test
```

The Katyuhen contract test checks registry identity, unique project/integration IDs, valid edge endpoints, Mora's hub registration and project links. It does not certify a foreign binary, driver, native ABI or kernel service; those must be tested in their owning repository.

## Roadmap

- **Now:** unified directory, project manifests, integration graph and common visual contract.
- **Next:** small typed import/export adapters for verified JSON contracts, with size limits, schema validation and provenance reporting.
- **Later:** an optional native launcher and capability broker, only after DuckOS has trusted installation roots, process isolation, signed package metadata, approval UI and rollback.
- **Not a shortcut:** no kernel driver loading, arbitrary process execution, background network daemon or global file access is added by this registry.
