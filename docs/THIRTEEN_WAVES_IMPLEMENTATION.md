# Thirteen-wave implementation record — 23 November 2026

**Project direction:** Ivan-VHS  
**Scope:** implementation changes prepared across Pytyliki, Reaper, OPlague, VentuSample and Dak.  
**Delivery rule:** changes are isolated in repository branches and reviewed through pull requests; they are not described as merged until GitHub reports a merge.

| Wave | Repository | Delivered change | Verification added |
|---:|---|---|---|
| 1 | Pytyliki | Numerically scaled benchmark statistics to avoid overflow on valid finite values near the floating-point limit; result structure is published only on success. | Extreme-value, finite-result and unchanged-output regression cases. |
| 2 | Reaper | Bounded lexer source length and token count to control parser input work. | Source and token limit tests; normal Unicode tokenization check. |
| 3 | Reaper | Expanded Canonical IR verification for jump targets, call/list arity, definitions, iterator exits, functions, imports and operator operands. | Malformed-IR rejection tests. |
| 4 | Reaper | Added a reference-runtime/VM semantic parity suite for pipelines, loops, conditions and lexical scope. | Shared-source conformance tests for tree-walk and VM engines. |
| 5 | OPlague | Reject oversized standalone INF files before loading their bytes into memory. | Sparse oversized-file regression test. |
| 6 | OPlague | Hardened ZIP inspection against non-canonical paths, duplicate paths, symlinks, special files and encrypted entries; bounded INF decompression. | Malicious archive fixtures and existing traversal checks. |
| 7 | OPlague | Added regression coverage for duplicate names, symlink entries, dot-segment paths and oversized standalone INF files. | Python unittest cases in the existing inspector suite. |
| 8 | VentuSample | Added deterministic 16-tap Blackman-windowed sinc conversion with an anti-alias cutoff for offline downsampling; retained linear interpolation for previews. | New C API and C11 implementation in the existing DSP target. |
| 9 | VentuSample | Added tests for above-Nyquist attenuation, passband retention, stereo separation and invalid-output behavior; updated user-facing capability documentation. | Existing CTest resampler target now covers both algorithms. |
| 10 | Dak | Defined a fixed-width, versioned v1 boot handoff structure and typed memory-map entries. | Public header and explicit version/size contract. |
| 11 | Dak | Implemented validation for kernel/initramfs ranges, overlap, framebuffer extent and sorted non-overlapping memory-map entries. | C11 validator with stable status codes. |
| 12 | Dak | Added host-side tests for valid records, malformed ranges, framebuffer bounds, map ordering, overlap, types and version negotiation. | CTest executable `dakos_boot_info_tests`. |
| 13 | Dak | Added a CMake foundation build, sanitizer option, CI workflow and build/test instructions. | `cmake --build`, `ctest`, AddressSanitizer and UndefinedBehaviorSanitizer in CI. |

## Scope boundaries

- Pytyliki still provides advisory processor measurements; this change does not alter CPU scheduling or hardware configuration.
- Reaper still uses its current reference runtime and VM; this change strengthens input and IR validation but does not add native object generation or a completed Dak ABI.
- OPlague remains read-only; it does not install, load or execute driver payloads.
- VentuSample remains an offline processor; sinc resampling is not a real-time device path or a replacement claim for specialist resampling libraries.
- Dak now has a host-testable boot handoff contract, not a bootloader, kernel, initramfs, compositor or bootable image.

## Review state

This record is committed with [Dak PR #13](https://github.com/Ivan-VHS/Dak/pull/13). The corresponding implementation PRs are [Pytyliki #198](https://github.com/Ivan-VHS/Pytyliki/pull/198), [Reaper #227](https://github.com/Ivan-VHS/Reaper/pull/227), [OPlague #147](https://github.com/Ivan-VHS/OPlague/pull/147) and [VentuSample #111](https://github.com/Ivan-VHS/VentuSample/pull/111). CI status is determined by the checks attached to those pull requests; adding a workflow is not itself evidence that it passed.
