#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PARTS="$ROOT/security/beelzebub-av-source.parts"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

if [[ ! -d "$PARTS" ]]; then
  echo "Beelzebub source bundle parts are missing: $PARTS" >&2
  exit 2
fi

shopt -s nullglob
parts=("$PARTS"/part-*.b64)
if [[ ${#parts[@]} -ne 6 ]]; then
  echo "Expected 6 Beelzebub source parts; found ${#parts[@]}" >&2
  exit 2
fi

cat "${parts[@]}" | base64 --decode > "$TMP"
printf '%s  %s\n' "4c952a00165b2ed25c7adcd3f878bcdac20135902f05ea0daf5a8f23df68bacc" "$TMP" | sha256sum --check --status || {
  echo "Beelzebub source bundle checksum mismatch; extraction refused" >&2
  exit 3
}

if tar -tzf "$TMP" | grep -Ev '^(security/beelzebub-av/?|security/beelzebub-av/|duckos/security/|tests/)' | grep -q .; then
  echo "Unexpected path in Beelzebub source archive; extraction refused" >&2
  exit 3
fi

tar -xzf "$TMP" -C "$ROOT"
test -f "$ROOT/security/beelzebub-av/pom.xml"
test -f "$ROOT/duckos/security/beelzebub.py"
echo "Verified and reconstructed Beelzebub AV source bundle."
