# DuckOS integration for Reaper multi-syntax projects

**Project author/developer:** Ivan-VHS  
**Provider:** local Reaper checkout  
**Boundary:** subprocess argument vector, no shell

DuckOS exposes Reaper's syntax registry and runtime through the Reaper workbench. It discovers the local `reaper/multisyntax.py` capability and never imports the specialist runtime into the DuckOS process.

## Commands

List installed frontends:

```sh
duckos reaper syntax --list
```

Validate source without execution:

```sh
duckos reaper syntax --check --syntax python ./examples/demo.py
duckos reaper syntax --check --polyglot ./examples/project.polyglot
```

Run a single frontend or a polyglot source:

```sh
duckos reaper syntax --syntax brainfuck ./examples/demo.bf
duckos reaper syntax --polyglot --steps 100000 ./examples/project.polyglot
```

DuckOS accepts only known source extensions, rejects symbolic-link source files, applies a bounded step count and a 30-second process timeout, captures bounded output, and launches Reaper with `shell=False`. The actual syntax validation and execution policy remains in Reaper.

The workbench capability report includes `multi_syntax_frontends`, `polyglot_runner` and `syntax_validation` only when the local Reaper checkout contains the corresponding module. Older checkouts fail clearly instead of silently pretending to support additional syntaxes.
