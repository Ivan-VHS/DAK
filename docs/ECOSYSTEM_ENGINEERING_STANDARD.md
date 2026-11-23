# Ecosystem Engineering Standard

**Scope:** the five current repositories in the Ivan-VHS ecosystem: Pytyliki, Reaper, OPlague, VentuSample and DuckOS.  
**Canonical home:** DuckOS superproject.  
**Status rule:** this standard defines required engineering practice; it does not certify that every capability is implemented.

This document turns the shared engineering framework into a repository-specific audit and delivery contract. Source code, tests, build files, versioned schemas and release workflows remain authoritative for actual behavior. Where this standard and a local project contract differ, preserve the narrower safety boundary and update documentation through a reviewed change.

## 1. Current repository map

| Repository | Responsibility and primary stack | Verification authority |
|---|---|---|
| Pytyliki | Portable C11 processor-systems workstation, CMake, native CLI tools, Win32 GUI on Windows, stable C ABI | CMake targets, CTest, C11 CI and Linux ASan/UBSan job |
| Reaper | Python 3.10+ language/runtime and tooling, .rpr syntax, CLI/REPL, Windows Reaper Studio, LSP/DAP, partial experimental C17 native track | Python package, unittest suite, language examples and workflow checks; native track has its own scoped CMake contract |
| OPlague | Python 3.10+ Windows device/package evidence workbench, Tkinter UI, PowerShell-backed read-only PnP inventory, INF/ZIP/PE/UDRV inspection | Python unittest suite, compile checks, engineering and visual validators, Windows packaging workflow |
| VentuSample | C++20 renderer and offline DSP, CMake, optional Qt 6 Widgets desktop, migrated bounded C11 DSP modules | CMake/CTest, Qt/core build jobs, Python contract checks, Windows MSVC desktop build |
| DuckOS | OS superproject and Mora desktop; Python 3.10+ system/packaging tools, Node.js 18+ shell tests, pinned Git submodules | Python unittest and contract validators, npm test, federation validation and native build checks when a native target exists |

The four specialist source repositories are federated by DuckOS under the pinned submodule paths documented in [Repository Federation](REPOSITORY_FEDERATION.md). DuckOS is the superproject, not a fifth submodule. Gitlink commits and the machine-readable federation registry are the source of truth for imported revisions.

### Names that are not separate current repositories

- **Reaper Studio** is the desktop IDE/workbench within Reaper; it is not a separate repository.
- **MOST** is a Reaper language/syntax and function-registry area; it is not a separate repository.
- **DuckDriver OmniCore** is not a separate repository in the current five-project federation. The adjacent current responsibilities are DuckOS read-only hardware inventory and OPlague read-only device/driver-package evidence. Neither implies driver installation or kernel-driver implementation.
- **SAMBU** is not present in the current five-repository federation map. Do not silently rename another project to SAMBU or duplicate an existing product. Add it only after a real repository, owner, scope and integration contract exist.

Requirements are applied to actual project ownership and technology rather than copied as fictitious folders, CLIs or services.

## 2. Repository-specific implementation and verification

Run only the block for the repository being changed. Keep each required command as a distinct CI step or independently reported result; a later successful command must never hide an earlier failure.

### 2.1 Pytyliki

**Engineering profile**

- Keep the core in strict C11 and preserve existing CMake target boundaries.
- Keep Win32 GUI code platform-specific; portable core and CLI targets remain buildable without the GUI.
- Preserve the versioned C ABI and explicit ownership of buffers and handles across the FFI boundary.
- Validate lengths, counts, overflow, alignment, numeric ranges and workload budgets before processing.
- Hardware discovery and source review remain read-only. Benchmark and partition output is evidence or advice, not a claim that the OS scheduler, CPU frequency or affinity was changed.
- GCC/Clang sanitizer builds and MSVC builds use their own supported compiler flags. Do not inject GCC-only flags into MSVC jobs or add -Werror without first resolving the project warning baseline.

**Release validation**

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
~~~

For the documented GCC/Clang sanitizer path:

~~~sh
cmake -S . -B build-sanitized -DBUILD_TESTING=ON -DPYTYLIKI_ENABLE_SANITIZERS=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build build-sanitized --parallel
ctest --test-dir build-sanitized --output-on-failure
~~~

The sanitizer option is not supported by MSVC. On Windows, validate the native GUI in the Windows workflow; a Linux core build does not prove Win32 behavior. Use the exact CLI smoke cases and target names in the current README and CTest configuration.

### 2.2 Reaper, MOST and Reaper Studio

**Engineering profile**

- Preserve the existing .rpr language and Python compatibility runtime while keeping native C17 work explicitly experimental and separately gated.
- Keep lexer, parser, source spans, semantic analysis, runtime, CLI, Studio, LSP and DAP behind defined module contracts.
- Preserve source locations through parsing and lowering; diagnostics must map back to the correct source file and range.
- Apply execution quotas and bounded input/resource policies. A quota system is not a security sandbox.
- Treat native libraries, FFI, external tools and process launch as explicit opt-in trust boundaries.
- MOST syntax aliases and registry entries must resolve through tested language rules; a catalog count alone is not runtime support.
- Studio diagnostics and editor features must use real parser/runtime contracts rather than a second, divergent parser.

**Python reference-runtime validation**

~~~sh
python -m compileall -q reaper tests
python tools/validate_engineering_evolution.py
python -m unittest discover -s tests -v
python -m reaper --check examples/flow.rpr
python -m reaper --check examples/device_audit.rpr
python -m reaper examples/flow.rpr
~~~

Open the Windows Studio through the documented entry point, currently python reaper_desktop.py. Run native C17 configuration only by following the current [Hardware Language](https://github.com/Ivan-VHS/Reaper/blob/main/docs/HARDWARE_LANGUAGE.md) and native compiler instructions; do not infer a build option or promise Python/native parity that the repository does not test.

### 2.3 OPlague

**Engineering profile**

- Keep device discovery, INF/ZIP/PE inspection and UDRV validation read-only.
- Treat exact hardware-ID matches as candidate evidence, not a driver compatibility verdict or publisher trust decision.
- Never execute INF directives, extract untrusted payloads, load drivers, write registry/device state or install packages as part of inspection.
- Bound package bytes, archive entries, expanded size, compression ratio, INF size, hash buffers and report output.
- Separate integrity hashes, Authenticode/signature status and compatibility evidence.
- Protect privacy in exported reports; explain pseudonymization and avoid unnecessary host identifiers.
- Windows PowerShell/CIM inventory is Windows-only. On another OS, report that live inventory is unavailable rather than substituting fixtures as live hardware.

**Validation and local launch**

~~~sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python tools/validate_engineering_evolution.py
python -m unittest discover -s tests -v
python -m oplague --verify
python oplague_app.py
~~~

The Windows packaging job remains the authority for the standalone executable and live Windows PnP behavior. Linux documentation/contract checks do not prove Windows device discovery.

### 2.4 VentuSample

**Engineering profile**

- Keep the renderer and DSP deterministic for identical parameters and fixed seeds within the documented numeric model.
- Keep rendering and DSP offline; do not introduce an audio-device callback or claim real-time playback, DAW hosting or third-party DLL/SO loading.
- Bound imported WAV bytes, frame counts, channels, sample rates, FFT sizes, MIDI input and processing allocations.
- Validate finite samples, PCM encoding, peak limits, filter constraints and manifest paths before export.
- Preserve the output non-overwrite policy, preset and pack schema compatibility, and source-sample rights confirmations.
- Keep Qt UI code separate from the portable core. A missing Qt dependency means the desktop target is blocked/not built, not that the GUI build passed.
- Compare optimized DSP paths with reference behavior and use measured performance baselines.

**Portable core validation**

~~~sh
cmake -S . -B build-core -DCMAKE_BUILD_TYPE=Release -DVENTU_BUILD_DESKTOP=OFF -DVENTU_BUILD_TESTS=ON
cmake --build build-core --parallel
ctest --test-dir build-core --output-on-failure
~~~

**Linux Qt desktop validation** (with Qt 6 Widgets and Ninja installed)

~~~sh
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DVENTU_BUILD_DESKTOP=ON -DVENTU_BUILD_TESTS=ON
cmake --build build --parallel 2
ctest --test-dir build --output-on-failure
~~~

**Windows desktop validation** uses the configured MSVC developer environment and Qt 6 toolchain:

~~~powershell
cmake -S . -B build -A x64 -DCMAKE_BUILD_TYPE=Release -DVENTU_BUILD_DESKTOP=ON -DVENTU_BUILD_TESTS=ON
cmake --build build --config Release --parallel 2
ctest --test-dir build -C Release --output-on-failure
~~~

Python contract validators are auxiliary engineering checks, not the C++ renderer build. Keep their exit statuses separate from CMake and CTest.

### 2.5 DuckOS

**Engineering profile**

- Keep the browser-local Mora shell, native DuckOS tools and future kernel/system services as distinct maturity and privilege boundaries.
- Browser preferences or UI controls must not be described as OS scheduling, driver enforcement, sandboxing, boot updates, firmware operations or kernel services.
- Keep app catalogs, hardware inventory, manifests, transfers and deployment plans versioned and schema-validated.
- Keep hardware inventory read-only unless a separately threat-modeled and explicitly approved native operation is introduced.
- Keep system actions allow-listed, previewed, consent-gated, least-privileged, bounded and auditable. No arbitrary shell execution.
- Keep the four specialist projects as pinned source submodules. Do not use floating branch heads, implicit auto-build or auto-execution; do not overwrite locally modified submodules.
- Prefer versioned JSON contracts for cross-project exchange, then a narrow C ABI where justified. IPC requires an explicit process model, capabilities, quotas, cancellation and audit.

**Python and federation validation**

~~~sh
python -m pip install --upgrade pip jsonschema pyyaml
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
python tools/validate_engineering_evolution.py
python tools/federate_repositories.py validate
python tools/federate_repositories.py status --json
~~~

**Mora shell validation** (Node.js 18 or newer; CI currently uses Node.js 22)

~~~sh
npm test
~~~

A DuckOS native build is applicable only when the current revision defines a native build target. A conditional CI notice for an absent target is not evidence that a kernel, bootable image, native driver or compositor was built.

## 3. Shared engineering requirements

Apply the following requirements to every applicable component. Mark genuinely irrelevant requirements as not applicable with a reason; do not create empty abstractions merely to satisfy a checklist.

### Architecture and completeness

- Define module ownership, dependency direction, lifecycle and failure boundaries.
- Separate domain logic from UI, platform adapters, file I/O, network/process access and persistence where those boundaries exist.
- Keep interfaces cohesive, versioned and explicit about inputs, outputs, invariants, resource limits and errors.
- Reuse one implementation of shared semantics; do not fork parser, validation or domain behavior across UI and CLI.
- Make new capabilities discoverable, configurable and replaceable through documented extension points.
- Preserve existing behavior through compatibility tests and migrations where public contracts change.
- A feature is complete only when it is implemented, connected to a real workflow, observable, tested, documented and has defined failure/cancel behavior. A button, registry entry or specification is not proof of completion.

### Data, configuration and state

- Validate external data at the boundary: type, structure, size, count, path, encoding, numeric range and cross-field constraints.
- Use versioned schemas for persistent or cross-process formats; reject unsupported versions clearly.
- Keep one authoritative owner for mutable state. Define transaction or atomic-replacement behavior for multi-step updates.
- Make retryable operations idempotent or document why they cannot be; prevent conflicting duplicate operations.
- Keep secrets out of source, logs, fixtures and exported reports. Use safe defaults and validate configuration before side effects.
- Preserve provenance, units, timestamps and source identity where they affect interpretation; use privacy minimization for identifiers.

### Runtime, resources and reliability

- Bound memory, CPU, queue depth, recursion, file/archive size, parallelism and operation duration according to the component threat and workload model.
- Define cancellation, timeout, cleanup and shutdown behavior for non-trivial operations.
- Release file handles, memory, locks, processes and native resources on success, failure and cancellation paths.
- Distinguish health, readiness, degraded operation and failure where a service lifecycle exists.
- Keep deterministic behavior where required and define numeric precision, rounding, random-seed and reproducibility expectations.
- Use structured diagnostics with stable error identifiers and actionable context; do not silently swallow failures.

### Security and compatibility

- Treat files, archives, manifests, plugin metadata, subprocess output and external input as untrusted.
- Use least privilege, explicit opt-in for powerful integrations and deny-by-default action registries.
- Separate byte integrity from authenticity, publisher trust and semantic compatibility.
- Isolate platform-specific behavior behind adapters and test each declared platform independently.
- Check schema, ABI, CLI and file-format compatibility across supported versions; provide migration or rejection behavior.
- Do not claim sandboxing, driver enforcement, hardware writes or native execution unless the corresponding privileged mechanism and tests exist.

### UI and accessibility

- Keep UI state consistent with domain state; controls must be connected to real actions and report success/failure truthfully.
- Preserve focus, selection, cursor position and keyboard operation during updates.
- Respect target-platform conventions, DPI/scaling, resize behavior, localization, contrast and reduced-motion preferences where applicable.
- Provide loading, empty, unavailable, error, cancellation and success states.
- Keep expensive I/O and processing off the UI thread and avoid needless redraw or telemetry polling.

### Performance and observability

- Record a baseline before optimizing. Profile the relevant CPU, memory, disk, GPU or UI path rather than guessing.
- Define resource and latency budgets for critical paths; test typical and bounded worst-case inputs.
- Keep queues and concurrency bounded; avoid unbounded background work and repeated polling.
- Record enough structured context to investigate failures without logging secrets or excessive personal data.
- Compare optimized output against a trusted reference implementation where numerical or semantic parity matters.

### Testing, documentation and release

- Use unit, integration, regression, boundary, failure-path and end-to-end tests in proportion to component risk.
- Test negative cases, invalid inputs, partial availability, missing permissions, cancellation and recovery.
- Run the exact build and test commands for the actual language/compiler/platform; do not let one stack's success mask another stack's failure.
- Treat missing tools as blocked and intentionally skipped tests as skipped, never as passing.
- Keep examples, CLI help, schemas, screenshots and architecture docs synchronized with the current source.
- Use reproducible dependency versions and build inputs; preserve licenses and third-party notices.
- Release only from a reviewed revision with successful applicable CI, documented limitations and a recovery/rollback path where the product has persistent state or deployment effects.

## 4. Audit sequence

1. **Inventory:** identify the repository, branch, changed files, build systems, compiler/runtime versions, platform matrix and existing local work.
2. **Model:** trace the real data/control flow, dependencies, public contracts, resource bounds, trust boundaries and failure states.
3. **Gap analysis:** compare source/tests with this standard; record specific missing behavior and classify each item as applicable, not applicable or not assessed.
4. **Implement:** change the smallest coherent vertical slice. Preserve valid existing work and avoid broad unrelated rewrites.
5. **Verify:** run each applicable formatter, static check, build, test, schema validator and platform check as an independently visible result.
6. **Integrate:** test the whole path across module boundaries and cross-project adapters, not just isolated functions.
7. **Document:** update project docs, capability maturity and exact commands. State limits and blocked checks plainly.
8. **Release:** inspect the staged diff, stage only reviewed files, and create a commit/PR only after quality checks. Commit creation is not a test or build step.

## 5. Verification status vocabulary

Use the shared identifiers consistently:

| Status | Meaning |
|---|---|
| not_assessed | No current evidence-based assessment was performed |
| specified | A contract/design exists; executable behavior is not claimed |
| planned | Accepted future work is not implemented |
| partial | A tested subset exists; missing behavior is stated |
| implemented | Behavior exists and is connected to a real workflow |
| verified | Acceptance checks passed for a named revision, platform and configuration |
| not_applicable | Requirement does not fit the project's declared scope; explain why |
| blocked | A check could not run because a prerequisite/environment is unavailable |
| skipped | A check was deliberately not run under documented conditions |
| failed | A check ran and did not meet its criteria |

Do not use a single maturity label for an entire subsystem when its features have different states. A passing unit test verifies only the behavior it exercised.

## 6. Safe Git and release procedure

~~~sh
git status --short
git branch --show-current
git log -n 10 --oneline
git diff --stat
git diff --check
~~~

Review the complete working diff and the exact paths to be staged. Stage only reviewed files; do not use an automatic all-files stage when local settings, generated assets, credentials or unrelated changes may be present. Re-run relevant checks after the final source change. Review the staged diff before committing.

~~~sh
git diff
git add <reviewed-paths>
git diff --cached --check
git diff --cached
~~~

A commit is created only after checks and staged-diff review are complete. Release and deployment remain separate from source validation. Never discard local changes or force-update a shared branch as part of an audit.

## 7. Definition of Done

A module or repository change is complete only when all applicable points are satisfied:

1. The requested behavior is implemented in the correct repository and module.
2. Ownership, dependencies and architectural boundaries remain explicit.
3. Public interfaces and data formats are validated and versioned where required.
4. Real workflows invoke the implementation; no fake controls or dead handlers remain.
5. Bounds, permissions, timeouts, cancellation and cleanup are covered.
6. Failure paths and partial availability are predictable and diagnosable.
7. Relevant unit, integration, regression and boundary tests pass.
8. The correct compiler/runtime and supported platform builds are verified.
9. Cross-project integration uses the registered contracts and pinned revisions.
10. Documentation and capability status match the current source and tests.
11. Security, compatibility and release implications are reviewed.
12. The final diff is scoped, reviewed and independently reproducible.

Unmet criteria become explicit issues or planned work. Do not conceal them behind an overall complete or production-ready claim.
