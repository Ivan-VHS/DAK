# DuckOS — Reaper Edition

A small, executable operating-environment foundation written in **Reaper** source files.

> **Honest scope:** this is a Reaper-hosted user-space OS foundation and simulator, not a bootable
> bare-metal kernel. Process scheduling, memory accounting, virtual-path policy, device inventory,
> service state and capability checks are implemented as executable Reaper code. They do not
> replace OS syscalls, hardware drivers, physical memory management or real process creation.

## Run it

Install the Reaper reference runtime, then launch DuckOS:

~~~sh
git clone https://github.com/Ivan-VHS/Reaper.git
python -m pip install -e ./Reaper

git clone -b reaper/duckos-kernel-foundation https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS

python -m reaper --check duckos.rpr
python -m reaper duckos.rpr
python -m reaper tests/smoke.rpr
python -m unittest discover -s tests -v
~~~

The boot path writes a JSON report to var/boot-report.json.

## Implemented Reaper modules

| Module | Responsibilities |
|---|---|
| kernel/system.rpr | OS identity, version and boot metadata |
| kernel/process.rpr | Process records, validation, state filtering, priority ordering and memory totals |
| kernel/memory.rpr | Bounded memory-pool accounting, allocation/release checks and pressure levels |
| kernel/security.rpr | Explicit capability checks, missing-grant reports and deny-by-default policy |
| kernel/vfs.rpr | POSIX-style path validation, normalization, joining, extension and root-containment checks |
| kernel/devices.rpr | Device inventory records, validation and online-device discovery |
| kernel/monitor.rpr | CPU/memory/disk threshold classification and health snapshots |
| kernel/services.rpr | Service lifecycle metadata and event-queue records |
| kernel/catalog.rpr | Versioned function-catalogue contract |

The modules are Reaper source. Python is used only for the registry generator and automated
catalogue checks. The Reaper runtime's host file API is used explicitly for the boot report.

## The 87,965-entry function registry

The requested total is represented by a deterministic, paginated registry in tools/catalog.py.
It scans exported Reaper functions and marks those entries **implemented**. All remaining records
are explicitly labelled **reserved**; they are not empty function bodies and are not described as
working OS functionality.

~~~sh
# Show the summary and first page
python tools/catalog.py

# Inspect the final ten reserved records
python tools/catalog.py --offset 87955 --limit 10

# Export a selected page as JSON
python tools/catalog.py --offset 0 --limit 100 --json
~~~

The registry has exactly **87,965 records**. The implemented count is derived from the Reaper
source files, so it increases automatically as new exported craft functions are added.

## Validation

GitHub Actions installs the Reaper reference runtime, syntax-checks both entry points, executes
the boot path and Reaper smoke suite, and verifies catalogue size and pagination.

~~~sh
python -m reaper --check duckos.rpr
python -m reaper --check tests/smoke.rpr
python -m reaper duckos.rpr
python -m reaper tests/smoke.rpr
python -m unittest discover -s tests -v
~~~

## Next engineering stages

1. Replace the current process and memory models with explicit host adapters behind the same Reaper interfaces.
2. Add persistent filesystem metadata and a permission-aware VFS mount table.
3. Add a scheduler service with time slices, queues and measured telemetry.
4. Add device-driver adapters only where the host platform exposes a real supported interface.
5. Promote reserved catalogue slots to implemented functions only alongside source, tests and documented runtime boundaries.

## Repository layout

~~~text
duckos.rpr             Reaper boot entry point
kernel/                Reaper kernel and service modules
tests/smoke.rpr        Executable Reaper contract checks
tests/test_catalog.py  Registry tests
tools/catalog.py       Deterministic 87,965-entry registry generator
.github/workflows/     Reaper-aware CI
var/                   Generated boot reports
~~~

The initial implementation is original project code. No third-party operating-system or driver
source has been copied into this repository.
