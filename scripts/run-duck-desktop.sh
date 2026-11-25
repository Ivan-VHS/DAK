#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
APP="$ROOT/release/bin/duckos-desktop"

if [[ ! -x "$APP" ]]; then
    echo "Native DuckOS desktop is not built. Run the release build or build desktop-native first." >&2
    exit 1
fi

exec "$APP" --root "$ROOT" "$@"
