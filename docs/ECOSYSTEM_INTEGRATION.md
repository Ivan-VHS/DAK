# DuckOS ecosystem integration

DuckOS is the host repository; four independently maintained peer repositories are pinned as submodules. Cloned, built, interoperable and integrated into the running kernel are different states.

## Source set

| Peer | Path | License | Runtime role |
|---|---|---|---|
| Reaper | \`projects/reaper\` | Apache-2.0 | Language/toolchain and policy contracts; user-space only |
| Pytyliki | \`projects/pytyliki\` | MIT | C11 compute/inspection ABI and read-only host evidence |
| OPlague | \`projects/oplague\` | Apache-2.0 | Read-only device, driver-package and GPU telemetry evidence |
| VentuSample | \`projects/ventusample\` | Apache-2.0 | Offline-first C++20/C11 audio and DSP |

Exact commits are recorded in \`federation/repositories.v1.json\` and mirrored in \`federation/integration-graph.v1.json\`. Keep each source history, license and notice intact; do not flatten the repositories into the kernel tree.

## Interface maturity

| Producer → consumer | Contract | Status |
|---|---|---|
| Pytyliki → Reaper | C ABI v1 | Working host interop; explicit absolute library path and ABI-version check |
| OPlague → Reaper | Device snapshot v1 | Working read-only validation/comparison |
| DuckOS → Reaper | Hardware inventory v1 | Working read-only host inventory audit |
| OPlague → Reaper | GPU telemetry v1 | Reaper validates explicit v1 snapshots in read-only user space; digest is not publisher authentication |
| OPlague → DuckOS | GPU telemetry v1 | Normalized Reaper policy adapter only; trusted native ingest and publisher/build provenance still required |
| VentuSample → Reaper | Pack manifest v1 | Implemented metadata-only Reaper consumer for v1; no WAV reads, DSP execution or real-time audio |

The Reaper user-space GPU adapter reads explicit OPlague v1 snapshot files or supplied records, validates bounded fields and the canonical digest, and preserves unknown values. SHA-256 is integrity checking, not publisher authentication. The separate DuckOS Reaper policy bridge accepts only normalized records; trusted DuckOS native ingestion, publisher/build provenance and hardware providers remain pending.

The Reaper pack-v1 consumer is metadata-only: it validates safe filenames and schema cardinality, derives 22 normalized descriptors and compares manifests. It never opens WAV data, executes DSP or starts real-time audio. Pack v2 remains a separate unsupported contract.

VentuSample pack-v1 remains \`specified_only\`: a schema and integration document do not prove a consumer implementation.

## Build and verification

\`boot/build-release-iso.sh\` and its workflow build/test the four host projects and package source, licenses/notices, host tools and checksums. Host binaries are not DuckOS kernel binaries, and the Stage 1 kernel does not launch them.

\`\`\`sh
git submodule update --init --recursive
python tools/federate_repositories.py validate --json
python tools/federate_repositories.py status --json
npm run validate:ecosystem
npm test
\`\`\`

The Node check verifies exact pin agreement, source/license paths, workbench metadata, interface evidence, schema contract IDs and release boundaries. Existing federation validation remains responsible for Git links and \`.gitmodules\`.

## Runtime and security boundary

Peer executables remain user-space programs. No automatic library loading, execution, driver installation, firmware change, clock/voltage write or device mutation is permitted. Native libraries are called only through explicitly trusted paths. VentuSample remains offline by default; real-time audio needs a separately reviewed service.

The current Stage 1 kernel still lacks the scheduler/task lifecycle, Ring 3 address spaces, syscall dispatcher, filesystem, package manager, service supervisor and complete native desktop runtime needed to start peer workbenches inside DuckOS. Those runtime gates are distinct from source federation.
