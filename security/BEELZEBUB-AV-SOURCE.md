# Beelzebub AV source bundle

The Java source tree and DuckOS Python adapter are distributed as a checksummed source bundle in
`security/beelzebub-av-source.parts/`. The split Base64 chunks are reassembled and SHA-256
verified before extraction. This keeps the initial import atomic; the extracted tree is generated
locally and is not an independent source of truth.

From the repository root on Linux:

```bash
./scripts/unpack-beelzebub-av-source.sh
cd security/beelzebub-av
./scripts/self-test.sh
mvn --batch-mode clean package
```

The GitHub Actions workflow reconstructs and verifies the bundle before building the Java 21
scanner and running the DuckOS bridge/CLI regression tests.

This is a user-space scanner foundation, not a claim of kernel-level or real-time protection.
DuckOS currently has no completed native enforcement path for blocking process execution or
intercepting file opens; those capabilities remain explicitly disabled.
