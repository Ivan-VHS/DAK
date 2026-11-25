#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${DUCKOS_MORA_PORT:-8765}"
URL="http://127.0.0.1:${{PORT}/mora/"

command -v python3 >/dev/null 2>&1 || {
    echo "Python 3 is required only as a local static-file server." >&2
    exit 1
}
if python3 -c 'import urllib.request, sys; urllib.request.urlopen(sys.argv[1], timeout=1).read(1)' "$URL" >/dev/null 2>&1; then
    echo "Mora is already responding at $URL"
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true; fi
    exit 0
fi

python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$ROOT" &
SERVER_PID=$!
cleanup() { kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

ready=0
for _ in $(seq 1 40); do
    if python3 -c 'import urllib.request, sys; urllib.request.urlopen(sys.argv[1], timeout=1).read(1)' "$URL" >/dev/null 2>&1; then ready=1; break; fi
    sleep 0.25
done
if [[ "$ready" -ne 1 ]]; then
    echo "Mora did not become available at $URL" >&2
    exit 1
fi

echo "Mora is ready at $URL"
echo "Keep this terminal open; press Ctrl+C to stop the local server."
if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true; fi
wait "$SERVER_PID"
