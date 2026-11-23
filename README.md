# DuckOS

## Product direction

DuckOS is specified with a seven-application default suite: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Their roles, boundaries and proposed integrations are documented in [the preinstalled application specification](docs/PREINSTALLED_APPLICATIONS.md). This is a product specification, not a claim that these apps are already implemented or included in a bootable image.

## Interactive desktop prototype

The seven-app Mora home screen is implemented as a local browser prototype in [prototype/mora-home.html](prototype/mora-home.html). It preserves the seven-app catalog and the currently supported local workflows. It is not a native DuckOS desktop or proof that the missing operating-system services are available. See [the app-suite specification](docs/PREINSTALLED_APPLICATIONS.md) for prototype capabilities and native integration boundaries.

## Unified project workspace

Mora is the common desktop entry point for the seven-app browser suite and the existing Ivan-VHS development tools. Start the local host and open the home screen at the root URL. Choose **Проекты Ivan-VHS** in the top bar to open the separate project workspace for:

- [Reaper](https://github.com/Ivan-VHS/Reaper) — language tooling and Studio IDE.
- [OPlague](https://github.com/Ivan-VHS/OPlague) — read-only device and driver-package inspection.
- [VentuSample](https://github.com/Ivan-VHS/VentuSample) — native Qt 6 sample workstation and offline DSP.
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) — processor-systems workstation and Windows GUI.

Mora does not present these four repositories as substitutes for Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia or Unify. The seven app identities and their partial prototype status remain separate from the native project integrations. Unbuilt applications are shown as unavailable instead of simulated.

## Start Mora

Place the repositories beside DuckOS or configure their local paths in the Mora workspace settings, then run:

    python mora_host.py

The local host listens only on 127.0.0.1:43860. The root page opens the seven-app Mora home screen; /projects opens the native project catalogue. Python 3.10 or newer is required for the host. Each external application retains its own build requirements and launches in a separate OS-managed window.

## Documentation

Start with the [documentation index](docs/README.md). The [Mora desktop integration guide](docs/MORA_DESKTOP.md) defines the workspace, local launch rules, theme contract and security boundaries. The [unified documentation and semantics standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md) defines the shared terminology and evidence rules used across Ivan-VHS repositories.

Implementation maturity, supported platforms and subsystem behavior must be stated from the current source, build configuration and tests. Architecture proposals and roadmap entries are not implementation evidence.
