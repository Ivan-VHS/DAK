#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
WORKDIR=${DUCKOS_LIVE_WORKDIR:-"$ROOT/build/live-image"}
REAPER_SOURCE=${REAPER_SOURCE_DIR:-}

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this build as root (for example: sudo tools/build-live-image.sh)." >&2
    exit 1
fi
for tool in lb rsync; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Missing build tool: $tool. Install live-build and rsync first." >&2
        exit 1
    fi
done

mkdir -p "$WORKDIR"
cd "$WORKDIR"
mkdir -p config/includes.chroot/usr/share/duckos/source
rsync -a --delete --exclude .git --exclude build --exclude .venv --exclude Reaper "$ROOT/" \
    config/includes.chroot/usr/share/duckos/source/
if [ -n "$REAPER_SOURCE" ]; then
    if [ ! -d "$REAPER_SOURCE/reaper" ] || [ ! -f "$REAPER_SOURCE/pyproject.toml" ]; then
        echo "REAPER_SOURCE_DIR must point to a Reaper checkout." >&2
        exit 1
    fi
    mkdir -p config/includes.chroot/usr/share/duckos/Reaper
    rsync -a --delete --exclude .git "$REAPER_SOURCE/" \
        config/includes.chroot/usr/share/duckos/Reaper/
fi
mkdir -p config/package-lists config/hooks/live
cp "$ROOT/packaging/live-build/duckos.list.chroot" config/package-lists/duckos.list.chroot
install -m 0755 "$ROOT/packaging/live-build/0500-install-duckos.hook.chroot" \
    config/hooks/live/0500-install-duckos.hook.chroot

lb config \
    --distribution stable \
    --architectures amd64 \
    --binary-images iso-hybrid \
    --debian-installer live \
    --archive-areas "main contrib non-free non-free-firmware" \
    --apt-recommends true \
    --bootappend-live "boot=live components hostname=duckos username=duckos"
lb build

echo "DuckOS Live ISO build completed in $WORKDIR"
