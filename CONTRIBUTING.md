# Contributing to DAK

DAK is a Reaper-first operating-system project. Keep its native boot path, Reaper policy layer, and Mora host application as separate implementation tracks. A passing host-side policy test is not evidence of a native kernel capability.

## Engineering boundaries

- Use Reaper for OS policy, service contracts, and system-level logic. Keep C11 limited to the narrow freestanding boot and architecture boundary that requires it.
- Mora is a local host application, not a kernel-launched desktop, native compositor, or privileged system shell.
- Prefer local-first, offline-capable behavior. Do not add hidden network access, remote telemetry, external CDNs, cloud dependencies, or background data transfer.
- Keep device, firmware, process, memory-mapping, and driver operations read-only or simulated until a reviewed native implementation and authorization path exist.
- Version cross-repository contracts with an owner, schema version, limits, provenance, failure states, and maturity.
- A catalog entry or policy validator is not proof of runtime implementation.

## Local checks

Native C11 boot-contract tests:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Mora host-shell tests (Node.js 22+):

```sh
npm test
```

These checks do not qualify physical hardware, a native process model, a kernel service, or a production desktop. BIOS/UEFI and ISO claims require the repository's QEMU boot and release workflows.

## Pull request expectations

1. Keep each PR focused on one subsystem or contract.
2. Describe before/after behavior, affected repositories, compatibility impact, resource bounds, and failure behavior.
3. Add or update Reaper tests, CTest cases, Mora tests, schemas, and documentation for the changed surface.
4. Update `docs/IMPLEMENTATION_STATUS.md` when maturity changes; distinguish specified, host-tested, QEMU-tested, and hardware-qualified behavior.
5. Include exact checks and results. Never claim native enforcement from a reference-runtime test.
6. Use Conventional Commit messages and avoid unrelated formatting churn.

Required CI entry points: `.github/workflows/ci.yml` and `.github/workflows/completeness-check.yml`.
