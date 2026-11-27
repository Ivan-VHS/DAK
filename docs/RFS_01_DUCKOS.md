# RFS-01 in Duck OS

Duck OS consumes RFS-01 through a Reaper-native policy module. Reaper owns the
language grammar, phase semantics, typed IR, and canonical runtime; Duck does
not fork the language or reinterpret its operators.

## Source and contract

- Adapter: `duckos/runtime/rfs01.rpr`
- Contract: `federation/rfs-01.duckos.v1.json`
- Reaper smoke source: `rfs01-duckos-smoke.rpr`
- Canonical specification: [Reaper RFS-01](https://github.com/Ivan-VHS/Reaper/blob/main/docs/RFS_01.md)

## Record layouts

The adapter consumes immutable positional records:

| Record | Fields |
|---|---|
| Node | `[id, layer, pressure, load_limit, integrity, noise_db, core_seed, active]` |
| Link | `[id, origin, target, channel, blocked, weight]` |
| Signal | `[sequence, origin, payload, trusted, manufactured]` |

Every function validates the expected record length and returns either a
boolean, a diagnostic tuple, or a proposed next record. It does not mutate the
input records.

## Available policy functions

- `rfs01_node_valid`, `rfs01_link_valid`, `rfs01_signal_valid`: validate the
  three record types and their bounded field domains.
- `rfs01_phase_open`: checks the pressure and integrity gate for a node.
- `rfs01_pressure_reserve`: computes the normalized diagnostic reserve.
- `rfs01_pressure_forward`: proposes a pressure transition and rejects
  blocked links or target load-limit violations.
- `rfs01_signal_forward`: accepts only trusted, non-manufactured frames and
  proposes the defined noise attenuation.
- `rfs01_restore_root` and `rfs01_restore_core`: implement distinct full-state
  and core-seed recovery.
- `rfs01_runtime_limits_valid`: enforces the shared RFS-01 resource envelope.

## System boundary

This is a validation and policy adapter, not a kernel scheduler or privileged
service. It does not create processes, switch contexts, allocate physical
memory, load drivers, write firmware, access MMIO/DMA, change CPU affinity,
alter clocks or voltage, open sockets, or run external commands. A future
privileged integration must be a separate capability-gated subsystem with
its own contracts, threat model, audit log, and tests.

## Running the smoke source

With the Reaper reference runtime installed in the workspace:

```sh
python -m reaper rfs01-duckos-smoke.rpr
```

The smoke file imports the adapter using an explicit repository-relative
source path. The C11 Duck OS foundation build remains independent of the
optional Reaper source validation step.
