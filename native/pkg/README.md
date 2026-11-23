# duckpkg

`duckpkg.py` is a dependency-free first package-store implementation for DuckOS. It stores immutable package versions below `/opt/duckos/packages` and records installed files in `/var/lib/duckpkg/installed.json`.

## Archive format

A package is a `tar` or `tar.gz` archive with:

- `manifest.json` at its root;
- regular files below `payload/`;
- a `files` object mapping each relative payload path to its lowercase SHA-256 digest.

Example manifest:

```json
{
  "name": "hello",
  "version": "1.0.0",
  "files": {
    "usr/bin/hello": "REPLACE_WITH_64_HEX_SHA256"
  }
}
```

The installer rejects absolute paths, traversal, duplicate entries, links, device nodes and unlisted files. It verifies every file before publishing the staged version directory. There are no package scripts, shell hooks or automatic privilege escalation.

## Commands

```sh
python3 native/pkg/duckpkg.py --root ./rootfs list
python3 native/pkg/duckpkg.py --root ./rootfs install hello.tar.gz
python3 native/pkg/duckpkg.py --root ./rootfs verify hello
python3 native/pkg/duckpkg.py --root ./rootfs remove hello 1.0.0
```

## Release limitation

SHA-256 protects against accidental corruption and detects payload/manifest mismatches. It does **not** authenticate who published an archive when an attacker can replace both the archive and its manifest. Signed repository metadata, key rotation, dependency solving, version constraints, rollback policy, service activation and atomic system upgrades are not implemented yet. Do not use this prototype as a privileged production package manager.
