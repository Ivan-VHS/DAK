# DAKOS ecosystem integration

DAKOS is the host repository; four independently maintained peer repositories are pinned as submodules. Cloned, built, interoperable and integrated into the running kernel are different states.

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
| DAKOS → Reaper | Hardware inventory v1 | Working read-only host inventory audit |
| OPlague → DAKOS | GPU telemetry v1 | Reaper policy adapter only; trusted JSON ingest still required |
| VentuSample → Reaper | Pack manifest v1 | Specified metadata-only exchange; Reaper consumer not implemented |

The GPU adapter receives a normalized record only after a trusted ingest layer validates the JSON schema and canonical digest. It does not parse JSON, authenticate the publisher, probe the GPU or grant hardware rights. UTC remains provenance; the caller supplies monotonic time. Unknown sensor values remain absent.

VentuSample pack-v1 remains \`specified_only\`: a schema and integration document do not prove a consumer implementation.

## Build and verification

\`boot/build-release-iso.sh\` and its workflow build/test the four host projects and package source, licenses/notices, host tools and checksums. Host binaries are not DAKOS kernel binaries, and the Stage 1 kernel does not launch them.

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

The current Stage 1 kernel still lacks the scheduler/task lifecycle, Ring 3 address spaces, syscall dispatcher, filesystem, package manager, service supervisor and complete native desktop runtime needed to start peer workbenches inside DAKOS. Those runtime gates are distinct from source federation.
