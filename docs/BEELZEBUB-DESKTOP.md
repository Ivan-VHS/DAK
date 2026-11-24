# Beelzebub AV in Duck Desktop

Duck Desktop exposes Beelzebub AV (BAV) through a native maintenance tab and the
`duckos beelzebub` CLI. The tab is a user-space client of the versioned
Python-to-Java process bridge; it does not implement a second scanner.

## Build and run

```bash
./scripts/unpack-beelzebub-av-source.sh
cd security/beelzebub-av
mvn --batch-mode clean package
cd ../..
python -m duckos.cli beelzebub status
python -m duckos.cli desktop gui
```

The native tab reports actual runtime/JAR availability, accepts a user-selected
file, optional signed SHA-256 feed material (database, detached signature and
pinned public key), a loopback ClamAV port, and optional YARA-X executable/rules.
Scanning occurs in a bounded background process, never through a shell.

## Verdict semantics

- `CLEAN` applies only to the current immutable snapshot after every required
  configured check succeeds. It is not a guarantee or execution authorization.
- `MALICIOUS` reflects a configured engine detection.
- `INDETERMINATE` covers missing, invalid, expired or rolled-back trust data,
  unavailable required engines, timeouts, malformed output and audit failures.

Quarantine remains a separate explicit CLI option; the panel never moves or
deletes the scanned original.

## Enforcement boundary

This integration provides on-demand scans. It does not intercept file opens,
scan continuously, prevent process creation, block execution or enforce a
kernel policy. A future VFS/process-manager integration must bind a fresh verdict
to immutable file identity and hash, then enforce it through a native broker.
