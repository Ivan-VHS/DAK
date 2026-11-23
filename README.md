# DuckOS

## Product direction

DuckOS is specified with a seven-application default suite: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Their roles, boundaries and proposed integrations are documented in [the preinstalled application specification](docs/PREINSTALLED_APPLICATIONS.md). This is a product specification, not a claim that the apps are native system services or included in a bootable image.

## Mora — one desktop for web and native tools

Mora is the common desktop for both the seven web applications and the connected native project tools. The main screen in [prototype/mora-home.html](prototype/mora-home.html) shows both groups together:

- **Web apps:** Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Their current local browser workflows, app windows and local data stay in the seven-app prototype.
- **Native tools:** Reaper Studio, OPlague, VentuSample and Pytyliki. Mora checks their real repository and build state, then launches an available application as a separate native OS window.

The native tools are additions to the workspace, not replacements for the seven-app suite. A missing repository or unbuilt executable is shown as unavailable; Mora does not imitate a running native app with an HTML placeholder.

## Start Mora

Place DuckOS, Reaper, OPlague, VentuSample and Pytyliki beside one another or configure their paths in the local workspace settings. From the DuckOS directory, run:

    python mora_host.py

The local host listens only on 127.0.0.1:43860. The root page opens the combined web/native desktop. The **Каталог проектов** link opens the detailed native project page at /projects. Python 3.10 or newer is required for the host; each external application retains its own build prerequisites.

## Shared desktop behavior

- One home screen and one visual language for both application groups.
- One saved dark/light Mora theme, passed to new native processes as MORA_THEME_MODE.
- Web apps retain their browser-based local data and capability boundaries.
- Native apps retain their own executable processes, tools and data, with startup theme inherited from Mora.
- Existing application theme controls remain available; currently running native windows are not remotely repainted.

## Documentation

Start with the [documentation index](docs/README.md). The [Mora desktop integration guide](docs/MORA_DESKTOP.md) defines the unified home screen, local launch rules, theme contract and security boundaries. The [preinstalled app specification](docs/PREINSTALLED_APPLICATIONS.md) continues to define the seven web app identities and their maturity boundaries. The [unified documentation and semantics standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md) defines shared terminology and evidence rules.

Implementation maturity, supported platforms and subsystem behavior must be stated from the current source, build configuration and tests. Architecture proposals and roadmap entries are not implementation evidence.
