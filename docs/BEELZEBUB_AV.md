# Beelzebub AV · DuckOS native security application

**Product:** Beelzebub AV  
**Runtime:** Java 17+ / Swing  
**Integration owner:** DuckOS user space  
**Status:** partial, implemented file-scanner foundation  
**Visual identity:** Mora black / white / duck yellow

## Architecture

~~~text
Mora browser shell
  └─ Beelzebub AV panel (status + documented native entry points)
       ├─ Duck Desktop native tab
       │    └─ BeelzebubWorkbench
       │         └─ fixed argv, shell=False, bounded build/scan timeout
       │              └─ Java 17+ process
       └─ duckos beelzebub CLI
            ├─ status
            ├─ gui
            ├─ scan <directory>
            └─ ingest
                 ├─ JSON report: beelzebub.scan-report.v1
            └─ ingest
                 └─ Loopback Go Event Bridge → redacted NDJSON → Honeypot Intel view

Java application
  ├─ ScannerEngine: bounded recursive walk, streaming SHA-256, EICAR, script heuristics
  ├─ SignatureCatalog: bundled + user-imported local SHA-256 indicators
  ├─ ScanWatcher: selected-directory WatchService
  ├─ QuarantineService: explicit move, hash-verified restore, collision refusal
  ├─ Go Event Bridge: local authenticated receiver, normalized event records, hash-only evidence
  └─ Swing UI: overview, scanner, live guard, quarantine, signatures, Honeypot Intel
~~~

The application is a separate process. DuckOS Python never embeds the JVM or Java classes. The optional Go bridge is built and launched as a second unprivileged local process; it does not share the Java scanner's file/quarantine authority. The browser shell cannot read host files or start programs; it only documents the native entry points and shares the Mora palette. No arbitrary manifest command or shell string is evaluated.

## Build and use

~~~sh
cd apps/beelzebub-av
./build.sh
java -jar build/beelzebub-av.jar
./test.sh
~~~

After installing the DuckOS Python package, use:

~~~sh
duckos beelzebub status
duckos beelzebub gui
duckos beelzebub scan "$HOME/Downloads"
duckos beelzebub ingest
~~~

The --root option is available before the subcommand when developing from a non-standard DuckOS checkout:

~~~sh
duckos beelzebub --root /path/to/DuckOS status
~~~

The Python wheel installs the Java source and resource files under the DuckOS data directory (`share/duckos/apps/beelzebub-av`); the workbench discovers both the system and per-user installation locations. The native workbench builds the app on demand using a JDK 17+ (`java`, `javac`, `jar`). Java source targets release 17. The build has no third-party runtime dependencies. Generated JAR/classes are written to the user's cache (`$XDG_CACHE_HOME/duckos/beelzebub-av`, default `~/.cache/duckos/beelzebub-av`; Windows uses `%LOCALAPPDATA%/DuckOS/Cache/BeelzebubAV`), not to the read-only application directory.

## Scan report contract

schemas/beelzebub.scan-report.v1.schema.json describes the JSON emitted by --scan. The report includes the target, counts, byte totals, skipped files, read failures, cancellation state, elapsed time and per-file findings. The Python adapter adds engine and process_exit_code.

## Implemented detection primitives

1. SHA-256 is calculated while streaming file bytes; files are not loaded wholly into memory.
2. Exact hash indicators are matched against the bundled resource and a local user-imported feed. The default resource is deliberately empty; no vendor malware corpus is bundled and feeds are not downloaded automatically.
3. The standard EICAR test string is recognized across scanner buffer boundaries.
4. Script heuristics examine a bounded sample and require multiple suspicious tokens. These are informational heuristics, not a malware verdict.
5. Directory walks do not follow symbolic links and apply limits on depth, file count and per-file size.
6. Live Guard observes only user-selected trees via WatchService. It is not an OS filesystem filter.
7. Quarantine requires an explicit user action. Restore verifies the quarantined SHA-256 and refuses to overwrite an existing path.

## Security and maturity boundaries

This is an implemented user-space scanner foundation, not a complete endpoint-protection platform or kernel antivirus. It cannot intercept every filesystem write, terminate or block processes, scan process memory, inspect network traffic, scan boot sectors, enforce system-wide policy, or provide guaranteed real-time prevention. It does not automatically delete, disinfect, or upload suspicious files. Local imported feeds are not cryptographically authenticated by this initial implementation.

### Go Beelzebub deception integration

The optional Go Event Bridge receives event JSON from a local Beelzebub honeypot runtime at `http://127.0.0.1:9777/v1/events`. Start it with `duckos beelzebub ingest` or from the Duck Desktop Beelzebub tab. It creates a 256-bit bearer token in `ingest.token`; configure the upstream Go runtime to use that token and loopback endpoint. The receiver only binds to loopback, rejects unauthenticated or oversized requests, and writes normalized NDJSON into the same BAV data directory. Only hashes and selected metadata are persisted; credentials, raw commands, cookies, request headers and request bodies are discarded. Honeypot telemetry is behavioural evidence from a decoy, not a confirmed infection, and never triggers file quarantine.

The upstream Go runtime requires a small explicit event-forwarder patch because its public plugin API does not currently expose a tracer-event sink. The patch set and application guide are stored under `apps/beelzebub-av/upstream/beelzebub-v3/`; it preserves the existing stdout, RabbitMQ or Cloud sink and adds a separate bounded local BAV forwarder. It targets upstream commit `3f20be5355c7d6f144329e39c478cdd7ff98184c` and should be applied/revalidated against the chosen Beelzebub checkout. The integration is intended for a local binary or a container sharing the host network namespace; Docker bridge networking does not automatically reach the host loopback listener.

The scanner is intended for a directory selected by the operator. WatchService may coalesce or miss events, and recursive registration is subject to host OS limits. No claim of complete system coverage or threat-free status is made. Java JDK installation is a prerequisite; DuckOS does not silently install a runtime.

## Local data

- Windows: %LOCALAPPDATA%/DuckOS/BeelzebubAV
- Linux/macOS: $XDG_DATA_HOME/duckos/beelzebub-av, default ~/.local/share/duckos/beelzebub-av

The folder contains the local signature list and quarantine objects/metadata. Quarantine permissions are restricted to the current user on POSIX filesystems where supported.

## Tests

./test.sh compiles with javac --release 17 and executes the Java self-test. It checks EICAR matching, local hash-feed import, the heuristic label, symlink rejection, quarantine/restore and collision safety. Python integration tests cover the native process adapter's path and command boundaries. CI runs the Java test suite and Python suite independently.
