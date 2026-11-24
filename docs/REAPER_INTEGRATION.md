# Native Reaper integration

**Project:** DuckOS  
**Language and toolchain:** Reaper  
**Project maintainer:** Ivan-VHS  
**Integration state:** native user-space workbench with bounded CLI bridge and stdio protocol hand-off

## Ownership and architecture

DuckOS integrates Reaper as its first-party systems-language workbench while keeping both repositories independently versioned. The upstream source remains a commit-pinned Git submodule at `projects/reaper`. DuckOS owns repository discovery, host policy, native desktop entry points, command-line routing and process supervision. Reaper owns the language grammar, Python reference runtime, type checker, compiler, Studio, LSP, DAP and language-specific tools.

The integration is deliberately process-based:

```text
Duck Desktop / duckos CLI / external IDE
                  |
                  v
       duckos.desktop.reaper
     validated source and output paths
       fixed argv, shell=False
        time and output bounds
                  |
                  v
         projects/reaper
      Python reference runtime
      static type checker / CLI
      native Studio / LSP / DAP
      experimental scalar C17 AOT
```

DuckOS does not import Reaper's interpreter, AST, compiler or Python modules into its own process. It does not translate Reaper programs into kernel modules and does not grant device, driver, administrator or kernel privileges.

## Initialize the pinned source

For a new checkout:

```sh
git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS
python -m pip install -e .
python tools/federate_repositories.py validate
```

For an existing checkout:

```sh
git submodule update --init projects/reaper
python -m pip install -e .
duckos reaper status
```

The federation registry records the exact reviewed Reaper commit. Do not use `git submodule update --remote` in reproducible builds. To choose another checkout for local development, set `DUCKOS_REAPER_ROOT` or pass `--root` before the Reaper subcommand. An explicit invalid override is an error; DuckOS does not silently fall back to another checkout.

## Available workbench operations

The native Duck Desktop **Reaper** tab and the `duckos reaper` command share the same `ReaperWorkbench` adapter.

| Operation | Entry point | Scope and maturity |
|---|---|---|
| Checkout and capability status | `duckos reaper status` | Evidence-based discovery from the selected Reaper source |
| Syntax and static checks | `duckos reaper check FILE.rpr` | Parses and analyses without running the program |
| Type diagnostics | `duckos reaper typecheck FILE.rpr` | Reaper's conservative static type checker |
| Dependency graph | `duckos reaper modules FILE.rpr` | Read-only transitive module graph |
| Program execution | `duckos reaper run FILE.rpr` | Explicit user-space execution with bounded interpreter quotas |
| C17 generation | `duckos reaper emit-c FILE.rpr --output FILE.c` | Experimental scalar AOT subset |
| Native host build | `duckos reaper native FILE.rpr --output PROGRAM` | Experimental subset; invokes an installed host C compiler |
| Toolchain inventory | `duckos reaper toolchain` | PATH lookup only; discovered tools are not executed |
| Language Server Protocol | `duckos reaper lsp` | Reaper LSP over standard input/output |
| Debug Adapter Protocol | `duckos reaper dap` | Reaper DAP over standard input/output |
| Interactive prompt | `duckos reaper repl` | Interactive terminal session |
| Native IDE | `duckos reaper studio` | Starts Reaper Studio as a separate process |

Examples:

```sh
duckos reaper status
duckos reaper check projects/reaper/examples/flow.rpr
duckos reaper typecheck projects/reaper/examples/flow.rpr
duckos reaper modules projects/reaper/examples/flow.rpr
mkdir -p build
duckos reaper run projects/reaper/examples/flow.rpr --steps 1000000 --heap-bytes 67108864
duckos reaper emit-c projects/reaper/examples/flow.rpr --output ./build/flow.c
duckos reaper native projects/reaper/examples/flow.rpr --output ./build/flow
duckos reaper toolchain
duckos reaper studio
```

On Windows, give the native output an executable suffix such as `flow.exe`. The selected output directory must already exist. The bridge rejects source symlinks, output symlinks, an output path that overwrites the source file and source inputs larger than 4 MiB.

## Execution and native build policy

Running a `.rpr` or `.most` file is always an explicit command or user action in Duck Desktop. The bridge passes fixed argument vectors with `shell=False`, disables native FFI, applies interpreter quotas and enforces a 60-second wall-clock limit. Default limits and maximum accepted overrides are:

| Limit | Default | Maximum |
|---|---:|---:|
| Interpreter steps | 1,000,000 | 10,000,000 |
| Items per collection | 100,000 | 1,000,000 |
| Text length | 1,000,000 characters | 16,000,000 characters |
| Managed heap | 64 MiB | 512 MiB |
| Open managed resources | 64 | 256 |

These are Reaper interpreter guardrails, **not an operating-system sandbox**. They do not enforce OS-level CPU scheduling, filesystem isolation, process isolation or kernel capabilities. The bridge drains stdout and stderr concurrently and retains at most 1,000,000 bytes per stream; excess output is discarded and the UI reports truncation. The non-interactive DuckOS run bridge does not provide a stdin prompt channel; use `duckos reaper repl` or Reaper directly for interactive work. Unknown source files must not be run.

The native AOT path is experimental and only accepts the subset implemented by Reaper's current compiler. The bridge can emit C17 or invoke a selected/available GCC- or Clang-compatible host compiler to create a host executable. It does not run the resulting executable, install it, load it as a driver, or place it in the DuckOS boot chain. Native compilation does not establish full language parity or a general machine-code backend.

The toolchain inventory performs filesystem PATH lookup and reports discovered tool paths. It deliberately does not invoke compilers, debuggers, formatters, package managers or WASM runtimes. Actual build actions are separate, explicit operations.

## IDE integration: LSP and DAP

Reaper exposes stdio-based language and debug services. Start them through DuckOS so the external IDE uses the pinned Reaper checkout:

```sh
duckos reaper lsp
duckos reaper dap
```

Configure the IDE's Reaper language-server command as the DuckOS executable with arguments `reaper`, `lsp`; configure its debug adapter with arguments `reaper`, `dap`. The adapter preserves stdin, stdout and stderr because LSP/DAP framing must not be mixed with UI messages or JSON status output. Reaper's LSP also provides document formatting, completion, diagnostics, hover and source navigation according to the current upstream implementation.

DAP launches trusted local programs. LSP/DAP availability is not a remote service, cloud workspace or operating-system sandbox. Editor-specific configuration keys depend on the selected IDE extension and are not invented by DuckOS.

## Native Duck Desktop interaction

Open the maintenance workspace:

```sh
duckos desktop gui
```

The **Reaper** tab provides:

- source checkout and capability status;
- Reaper Studio launch in a separate process;
- selection of a local `.rpr` or `.most` source file;
- syntax/static checks, type diagnostics and module graph inspection;
- an explicit-confirmation Run action;
- an explicit-confirmation experimental native AOT build action;
- local toolchain inventory.

Long-running checks, execution and builds run on a worker thread. Output is capped before it is displayed. The Run confirmation explains the difference between interpreter quotas and OS sandboxing. The native build confirmation states that the produced executable is not launched automatically.

LSP and DAP are intended for an external editor or terminal client. The Mora browser shell does not launch host processes; native actions are handled by Duck Desktop and the DuckOS CLI.

## Trust and process boundaries

- Reaper remains user-space software. The integration uses fixed argv arrays, `shell=False`, bounded output, command-specific timeouts and validated local source/output paths.
- Static checking and module graph inspection do not execute source programs.
- Program execution uses Reaper's interpreter limits but does not gain kernel-level containment from DuckOS.
- The DuckOS bridge never passes `--allow-native-ffi`; loading a native C ABI library remains outside the workbench's default permission surface.
- Native compilation invokes a host C compiler only after an explicit user command/confirmation. The output is not executed by the workbench.
- Toolchain inventory does not execute discovered programs.
- LSP/DAP use standard streams and the upstream protocol implementations. The debug adapter is for trusted local programs.
- No operation maps physical MMIO, enables IRQ/DMA, flashes boards, installs drivers, changes firmware or enters kernel privilege.
- The browser-based Mora shell is not a host-process launcher or security boundary.

## Capabilities that remain partial or experimental

The machine-readable status payload follows [reaper-workbench.v1.schema.json](../schemas/reaper-workbench.v1.schema.json); it reports capability maturity and explicitly records that the integration is user-space, not an OS sandbox. The workbench exposes only the capabilities actually present in the selected Reaper checkout. Experimental scalar AOT is not a general native compiler. The C17 parser/IR/lowering, QCS hardware-description frontend, embedded linker tooling and hardware Studio are limited or staged features. The Python runtime remains the broad compatibility reference.

Reaper's MMIO descriptor API validates descriptors and dispatches through a supplied host adapter; it does not map physical memory or provide a real device driver. Full native type/ownership/effect checking, general object generation, OS-backed MMIO/IRQ/DMA services, hardware execution and a complete hardware-focused Studio workspace remain upstream development work. DuckOS does not promote those plans to implemented OS capabilities.

## Verification

Run DuckOS-focused checks:

```sh
python -m compileall -q duckos tests
python -m unittest tests.test_reaper_integration tests.test_reaper_cli tests.test_repository_federation -v
python -m unittest discover -s tests -v
python tools/federate_repositories.py validate
```

Validate the upstream Reaper source separately:

```sh
python -m pip install -e projects/reaper
python -m reaper --check projects/reaper/examples/flow.rpr
python -m unittest discover -s projects/reaper/tests -v
cmake -S projects/reaper -B build/reaper -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build build/reaper --parallel
ctest --test-dir build/reaper --output-on-failure
```

The CMake/CTest commands validate Reaper's experimental native C17 track; they do not make it the DuckOS kernel compiler. Validation must run against the exact pinned Reaper commit in the PR. Studio packaging and target hardware behavior require their own platform-specific evidence.
