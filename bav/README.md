# BAV context-classification module

This Java 17 module is the first limited BAV implementation increment for DuckOS. It reads the versioned local catalog at `security/defense-context.v1.tsv`, normalizes text with Unicode NFKC and returns whole-phrase context matches in three categories.

## Scope

- local, deterministic and read-only;
- UTF-8 catalog with duplicate/unknown-category validation;
- 32 KiB catalog, 128 line and 1 MiB input-character limits;
- whole-phrase boundaries to reduce substring false positives;
- returns category and matched-term metadata only;
- no network, native calls, process execution or dynamic class loading.

**This is not a complete antivirus engine.** It does not detect malware, inspect executable formats, verify signatures, sandbox processes, monitor memory or quarantine files. A context match must never be used as a malware verdict or as a reason to block/delete/quarantine content.

## Build and self-test

From the DuckOS repository root, with JDK 17 or newer:

```sh
mkdir -p build/bav-context
javac --release 17 -d build/bav-context \
  bav/java/duckos/bav/context/ContextClassifier.java \
  bav/java/duckos/bav/context/ContextClassifierSelfTest.java
java -ea -cp build/bav-context duckos.bav.context.ContextClassifierSelfTest \
  security/defense-context.v1.tsv
```

## Integration contract

The caller supplies already-bounded text from an explicitly selected local object. The classifier returns tags only; BAV's independent malware-analysis and policy layers retain ownership of threat verdicts and response actions.
