# Native Reaper integration

**Project:** DuckOS  
**Specialist runtime:** Reaper  
**Maintainer:** Ivan-VHS  
**Status:** implemented user-space launcher, static-check bridge, native AOT build command and boot-contract parity gate

## Architecture

DuckOS keeps Reaper as an independently versioned language and toolchain source at `projects/reaper`. The native Duck Desktop and CLI integrations invoke Reaper through an explicit process boundary:

```text
Duck Desktop / duckos CLI
          |
          v
  ReaperWorkbench
          |
  fixed argument vector
  shell=False, bounded timeout
          |
          v
  projects/reaper
  ├── reference runtime and static checker
  ├── experimental scalar C17 AOT backend
  └── DuckOS boot-info v1 source target
```

DuckOS does not import Reaper's interpreter, AST or Python modules into the OS process. Reaper owns its grammar, reference semantics and compiler diagnostics. DuckOS owns the native launch surface, the bounded process bridge and the boot ABI implementation.

## Initialize the source checkout

```sh
git submodule update --init projects/reaper
python -m pip install -e .
```

The Reaper submodule is pinned to an exact reviewed commit in `federation/repositories.v1.json`. A source checkout is not automatically built, trusted as a kernel module, or launched.

## Native shell entry points

```sh
duckos reaper status
duckos reaper studio
duckos reaper check ./examples/program.rpr
duckos reaper typecheck ./examples/program.rpr
duckos reaper build ./examples/native_program.rpr --output ./build/native_program
duckos reaper target-check
```

- `check` invokes the static parser/type-check path; it does not execute the selected program.
- `typecheck` invokes the focused type diagnostics when the pinned checkout supports them.
- `build` asks Reaper's experimental AOT subset to produce a host executable. It does not run that executable, and it does not claim to generate a DuckOS kernel image.
- `target-check` runs the fixed, repository-owned boot-contract conformance program in the Reaper reference runtime and AOT backend, then checks both outputs against the expected fixture stream. It never accepts an arbitrary source path.

The native Duck Desktop Reaper panel continues to use the same process boundary. The browser Mora shell does not launch host processes.

## Reaper boot-info v1 target

The Reaper repository contains `targets/duckos/boot_contract_v1.rpr`. It models split-u64 range arithmetic, individual memory-region validation, ordering, framebuffer extent calculation and the current C handoff status codes for a two-region conformance matrix.

The DuckOS native CMake test adds a small C fixture runner linked to `duckos_boot_contract`. CTest compares the exact status stream from:

1. the Reaper reference runtime;
2. Reaper's experimental native AOT executable;
3. the current DuckOS C implementation.

Run the complete native contract check after initializing the Reaper submodule:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Or run the bridge directly after building the conformance harness:

```sh
python tools/check_reaper_boot_contract.py \
  --reaper-root projects/reaper \
  --c-harness build/duckos_boot_info_conformance
```

## Process and trust boundaries

- Every Reaper process is started with a fixed argument vector and `shell=False`.
- Commands have bounded execution time and captured output; source paths must be existing regular `.rpr` or `.most` files.
- Native AOT builds write only to the explicit output path and do not execute the result.
- The fixed boot-contract conformance program uses only scalar arithmetic and standard output; it has no file, network, FFI, process or hardware effects.
- DuckOS does not grant Reaper kernel access, device access, administrator rights, driver installation or ambient FFI.
- The C boot-info contract remains the kernel-facing implementation.

## Current migration boundary

The current Reaper AOT backend emits hosted C17 for a limited scalar language subset. It does not yet emit freestanding object files, define a bootloader calling convention, link a kernel image, provide records or general collections, implement complete unsigned integer types, or cover arbitrary memory-map arrays in the source-level fixture validator. The Reaper model currently covers two memory regions; DuckOS C remains authoritative for maps of up to 256 entries.

A genuine kernel migration must not begin until typed records and bounded collections, complete u64/u32 semantics, a versioned target ABI, a freestanding backend, object/ELF generation, linker and entry-point contracts, startup/runtime support, target emulator tests and hardware validation are implemented. The current parity gate is the first measurable migration slice, not a claim that a bootable Reaper kernel exists.
