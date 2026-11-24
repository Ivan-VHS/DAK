# DuckOS documentation

The root [README](../README.md) is the first-stop guide for the current project boundary, Mora browser preview, clone/test/build commands, application catalogue and maturity. This index links to the maintained architecture and integration contracts.

## Desktop and application interfaces

- [Mora unified desktop](../mora/index.html) — current browser shell source and local preview entry point.
- [Mora Commons](MORA_COMMONS.md) — neutral application discovery and catalogue experience.
- [Mora shell and native integration](MORA_INTEGRATION.md) — browser-local behavior versus native host capabilities.
- [Mora Design System](../MORA_DESIGN_SYSTEM.md) — canonical black/white/yellow palette and interaction tokens.
- [Mora Boost and OPlague gaming integration](GAMING_PERFORMANCE_INTEGRATION.md) — hardware evidence, reversible Windows sessions and future bridge scope.
- [Preinstalled application suite](PREINSTALLED_APPLICATIONS.md) — product roles and declared capability boundaries.
- [Earlier Mora prototype](../prototype/mora-home.html) — retained reference implementation; not a native desktop compositor.

## Native platform and developer tools

- [Architecture](ARCHITECTURE.md) — implemented Reaper-first system contracts and pending native backends.
- [Native Reaper integration](REAPER_INTEGRATION.md) — process-isolated Studio launch and delegated CLI checks.
- [Repository federation](REPOSITORY_FEDERATION.md) — pinned Pytyliki, Reaper, OPlague and VentuSample submodules.
- [DuckOS Extended Terminal](EXTENDED_TERMINAL.md) — allowlisted user-space command environment and trust boundaries.
- [Duck Desktop optimization](DESKTOP_OPTIMIZATION.md) — native user-space maintenance and current compositor boundary.
- [Windows compatibility foundation](WINDOWS_COMPATIBILITY.md) — PE inspection, profiles and diagnostic tools.
- [DuckBridge](DUCKBRIDGE.md) — runtime discovery and structured dry-run launch plans; no target launch is claimed.

## Versioned contracts and utilities

- [Unify transfer format v1](UNIFY_TRANSFER_FORMAT_V1.md) — bounded JSON transfer contract for supported settings and content.
- [Hardware inventory schema](../schemas/hardware-inventory.v1.schema.json) — bounded local device-inventory records.
- [Preinstalled applications schema](../schemas/preinstalled-applications.v1.schema.json) — versioned application catalogue structure.
- [Base application catalogue](../catalogs/dak-base-applications.v1.yaml) — proposed package catalogue, not a boot-image manifest.
- [Engineering evolution framework](ENGINEERING_EVOLUTION_FRAMEWORK.md) — maturity states, architecture evolution and measurable completion criteria.
- [Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md) — capability maturity, runtime states, evidence and documentation terminology.

## Build and verification

~~~sh
npm test
python -m pip install -e .
python -m pip install jsonschema pyyaml
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
python tools/validate_engineering_evolution.py
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

CI currently runs Python 3.10/3.11/3.12, Mora Node tests on Node 22, and the native C build when a CMake target is present. The native build in this repository produces the C11 boot-contract library; it is not a complete OS image or kernel.

## Documentation rules

Describe implemented behavior separately from designs and roadmaps. A browser panel is not a native service; a catalogue item is not a packaged application; a process launch is not kernel integration; a device snapshot is not driver installation; and a boot contract is not a bootable image.

This repository currently has no root LICENSE file or captured Mora desktop screenshot. Do not add license or screenshot badges until those artifacts exist.
