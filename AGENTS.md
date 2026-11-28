# DuckOS engineering agreement

DuckOS is built in small, verifiable layers. Keep the implementation understandable to the next person who has to debug a failed boot, a damaged image or an unexpected device boundary.

## Code and architecture

- Prefer plain, idiomatic C, C++ and Python that follows the surrounding module's conventions.
- Use names that communicate responsibility. Keep functions cohesive and control flow direct.
- Add an abstraction when it represents a real boundary or removes meaningful duplication, not to make the architecture look larger.
- Keep comments for invariants, hardware constraints, failure handling and decisions that are not obvious from the code.
- Preserve boot protocol details, ELF layout, driver ABI, package formats, syscall contracts and on-disk structures unless a versioned change is intended.
- Keep freestanding kernel code separate from host tooling and user-space services. Do not accidentally introduce hosted-library dependencies into kernel targets.
- Avoid broad rewrites, mass renames and bulk formatting without a tested baseline.

## Safety and resource boundaries

- Validate every external boundary: bootloader data, memory-map entries, archive headers, package manifests, paths, driver descriptors and IPC messages.
- Check integer arithmetic before computing ranges, offsets, sizes, alignment or allocation lengths.
- Bound memory use, file sizes, entry counts, recursion depth, queue length and execution time where input can be untrusted.
- Reject path traversal, unsafe archive entries, unexpected special files, malformed lengths and unsupported ABI versions.
- Keep host-side diagnostics read-only by default. Any operation that changes host devices, services, mounts, packages or system configuration needs an explicit user-selected action and a narrow scope.
- Do not load untrusted kernel modules, install drivers, alter firmware or weaken host security controls as part of ordinary tests.
- Fail visibly and preserve the original evidence; do not turn an unknown state into a successful result.

## Tests and evidence

- Add a focused regression test for each behavior change, including malformed input and boundary cases where applicable.
- Run the narrowest affected tests first, then the repository's relevant build and integration checks.
- Treat an ISO build and a QEMU boot smoke test as evidence only for the tested machine profile and boot path.
- Distinguish implemented, experimental, host-dependent, simulated and planned functionality in documentation.
- Record the exact command and result when a capability claim depends on a local or CI run.
- Keep generated images, manifests and reports reproducible where practical; verify hashes before trusting transported build inputs.

## Changes and review

- Inspect callers, tests, build scripts and versioned contracts before changing a public interface.
- Keep each change small enough to review and explain. Separate formatting-only edits from logic changes.
- Do not copy third-party code or assets without preserving their license and provenance.
- Review the complete diff for unintended file changes, permission changes, generated artifacts and unsupported claims.
- CI may build and test a proposal. It must not approve or merge its own changes or bypass branch protection.

The goal is not maximum code volume. The goal is a boot path and system whose behavior can be explained, reproduced and checked.
