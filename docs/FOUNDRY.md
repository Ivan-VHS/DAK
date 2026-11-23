# Duck Foundry — industrial operations workbench

**Project:** DuckOS  
**Application:** Foundry  
**Maintainer:** Ivan-VHS  
**Status:** implemented native user-space diagnostic and operator-planning workbench

## Purpose

Foundry translates an industrial control-room metaphor into a general-purpose DuckOS systems console. Its subject is the operating system and its software subsystems, not music production and not control of physical factory equipment.

The workbench brings together existing bounded diagnostic sources:

- host resource and process snapshot from Duck Desktop;
- workspace and current-user startup audit;
- PCI/USB device inventory on Linux and Plug-and-Play inventory on Windows;
- DuckBridge discovery of installed compatibility runtimes;
- explicit maturity markers for recovery and security services that remain architectural specifications.

Foundry correlates those sources. It does not replace their owners or create a competing implementation.

## Native entry points

~~~sh
duckos foundry gui
duckos foundry audit
duckos foundry audit --skip-devices --skip-runtimes
duckos foundry plan --profile routine
duckos foundry plan --profile preventive
duckos foundry plan --profile incident
duckos foundry plan --profile commissioning
duckos foundry audit --output ./foundry-report.json
~~~

The graphical workbench is a native Tk user-space application. The CLI produces versioned JSON, and an optional export creates a new private report file. Existing report files are never overwritten.

## Operational model

A report has four layers:

1. **Signals:** current, bounded measurements and inventory summaries.
2. **Subsystems:** source-backed availability or explicitly specified maturity.
3. **Findings:** threshold-based observations with severity and a suggested next check.
4. **Runbooks:** reviewable operator checklists for routine checks, preventive maintenance, incident review and commissioning.

Runbooks are checklists, not executable automation. The operator can use them to organize work and record decisions in a separate maintenance process. Foundry does not perform those changes.

## Data collection

- Desktop resources and processes come from DesktopService.audit().
- Device information comes from collect_host_inventory(). Raw device instance IDs are not included; the inventory provider emits a per-snapshot keyed identity hash.
- Compatibility runtimes are discovered by DuckBridge without launching them or contacting the network.
- Unsupported or unavailable collectors are represented as unavailable and recorded in collection_errors; one unsupported source does not discard successful diagnostics.
- The report records the capture time, data sources, execution boundaries and privacy properties.

## Safety boundary

Foundry is read-only and local. It does not terminate or reprioritize processes, install or remove drivers, change power plans, edit the registry, modify services, mount disks, change firmware, alter boot settings, install packages or run arbitrary shell commands. It does not control PLCs, industrial machinery or physical actuators.

The recovery and security sections are marked specified, not available: DuckOS still requires a native A/B updater, boot verification, recovery implementation, capability broker and process isolation before those can be represented as enforced services.

## Verification

Run the focused checks:

~~~sh
python -m unittest tests.test_foundry tests.test_foundry_cli -v
npm test
~~~

The Python tests exercise threshold evaluation, optional collector failures, read-only policy, manual-only runbooks, export safety and CLI integration. They do not certify kernel scheduling, driver installation, machine-wide policy enforcement or boot-image readiness.
