# Веельзевул / Beelzebul

DuckOS includes the Beelzebul 1.0.0 repository scanner and its machine-readable 66-rule policy.

Run:

```sh
python3 tools/beelzebul.py --help
python3 tools/beelzebul.py --json
python3 -m unittest discover -s tests -p "test_beelzebul.py" -v
```

Contract:
- `beelzebul.security.v1`, exactly 66 ordered unique rules in five groups (15+15+15+15+6).
- Read-only scanning; no source rewriting or external code loading.
- Secret values are not copied into findings.
- File count, individual file size, total bytes and line length are bounded.
- Critical findings can block CI; review findings stay visible.

Beelzebul is a development-time repository scanner, not an antivirus, kernel monitor, secure-boot implementation or process sandbox.
