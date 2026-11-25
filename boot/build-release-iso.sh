#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$ROOT/build/release"
OUTPUT="$ROOT/dist/DAK-Release-x86_64.iso"

while (($#)); do
    case "$1" in
        --work-dir) [[ $# -ge 2 ]] || { echo "missing --work-dir value" >&2; exit 2; }; WORK_DIR="$2"; shift 2 ;;
        --output) [[ $# -ge 2 ]] || { echo "missing --output value" >&2; exit 2; }; OUTPUT="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: boot/build-release-iso.sh [--work-dir DIR] [--output FILE]"
            exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

require_tool() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "required release tool is missing: $1" >&2
        exit 1
    }
}
for tool in git python3 cmake ctest gcc g++ node npm tar sha256sum install find readelf; do
    require_tool "$tool"
done

mkdir -p "$WORK_DIR/build" "$WORK_DIR/payload" "$(dirname -- "$OUTPUT")"
WORK_DIR="$(cd -- "$WORK_DIR" && pwd)"
OUTPUT_DIR="$(cd -- "$(dirname -- "$OUTPUT")" && pwd)"
OUTPUT="$OUTPUT_DIR/$(basename -- "$OUTPUT")"
BUILD_DIR="$WORK_DIR/build"
PAYLOAD="$WORK_DIR/payload"

echo "[1/8] Synchronize and validate exact source pins"
git -C "$ROOT" submodule sync --recursive
git -C "$ROOT" submodule update --init --recursive
python3 "$ROOT/tools/federate_repositories.py" validate --json
python3 "$ROOT/tools/federate_repositories.py" status --json

for project in pytyliki reaper oplague ventusample; do
    [[ -f "$ROOT/projects/$project/LICENSE" ]] || {
        echo "source or license missing for $project" >&2
        exit 1
    }
done

echo "[2/8] Verify Mora shell contracts"
(cd "$ROOT" && npm test)

echo "[3/8] Build and test Reaper native C17 tools"
cmake -S "$ROOT/projects/reaper" -B "$BUILD_DIR/reaper" \
    -DCMAKE_BUILD_TYPE=Release -DREAPER_BUILD_TESTS=ON
cmake --build "$BUILD_DIR/reaper" --parallel 2
ctest --test-dir "$BUILD_DIR/reaper" --output-on-failure

echo "[4/8] Build and test Pytyliki C11 tools"
cmake -S "$ROOT/projects/pytyliki" -B "$BUILD_DIR/pytyliki" \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build "$BUILD_DIR/pytyliki" --parallel 2
ctest --test-dir "$BUILD_DIR/pytyliki" --output-on-failure

echo "[5/8] Build and test VentuSample C++20 / Qt desktop"
cmake -S "$ROOT/projects/ventusample" -B "$BUILD_DIR/ventusample" \
    -DCMAKE_BUILD_TYPE=Release -DVENTU_BUILD_DESKTOP=ON -DVENTU_BUILD_TESTS=ON \
    -DREAPER_SOURCE_DIR="$ROOT/projects/reaper"
cmake --build "$BUILD_DIR/ventusample" --parallel 2
QT_QPA_PLATFORM=offscreen ctest --test-dir "$BUILD_DIR/ventusample" --output-on-failure

echo "[6/8] Verify OPlague read-only user-space workbench"
(
    cd "$ROOT/projects/oplague"
    python3 -m compileall -q oplague_app.py oplage_app.py oplague tests tools
    python3 -m unittest discover -s tests -v
)

echo "[7/8] Assemble offline source, licenses, host tools and Mora"
rm -rf "$PAYLOAD"
mkdir -p "$PAYLOAD/dak/release/bin" "$PAYLOAD/dak/release/lib" "$PAYLOAD/dak/release/evidence"

# Keep full source and notices; exclude Git metadata and generated build caches.
tar -C "$ROOT" \
    --exclude='./.git' --exclude='*/.git' \
    --exclude='./build' --exclude='./dist' \
    --exclude='*/build' --exclude='*/dist' \
    --exclude='*/node_modules' --exclude='*/__pycache__' \
    --exclude='*/.pytest_cache' --exclude='*/.mypy_cache' \
    --exclude='*/.venv' --exclude='*/CMakeFiles' \
    -cf - . | tar -C "$PAYLOAD/dak" -xf -

copy_binary() {
    local source="$1" destination="$2"
    if [[ -f "$source" ]]; then
        install -m 0755 "$source" "$PAYLOAD/dak/release/bin/$destination"
        echo "included host tool: $destination"
    fi
}
for required in \
    "$BUILD_DIR/reaper/reaper-c" \
    "$BUILD_DIR/pytyliki/pytyliki" \
    "$BUILD_DIR/pytyliki/pytyliki-apsia" \
    "$BUILD_DIR/pytyliki/pytyliki-metrics" \
    "$BUILD_DIR/pytyliki/pytyliki-benchstats" \
    "$BUILD_DIR/pytyliki/pytyliki-qcs" \
    "$BUILD_DIR/ventusample/VentuSample"; do
    [[ -x "$required" ]] || {
        echo "expected host build output is missing: $required" >&2
        exit 1
    }
done
copy_binary "$BUILD_DIR/reaper/reaper-c" "reaper-c"
copy_binary "$BUILD_DIR/pytyliki/pytyliki" "pytyliki"
copy_binary "$BUILD_DIR/pytyliki/pytyliki-apsia" "pytyliki-apsia"
copy_binary "$BUILD_DIR/pytyliki/pytyliki-metrics" "pytyliki-metrics"
copy_binary "$BUILD_DIR/pytyliki/pytyliki-benchstats" "pytyliki-benchstats"
copy_binary "$BUILD_DIR/pytyliki/pytyliki-qcs" "pytyliki-qcs"
copy_binary "$BUILD_DIR/ventusample/VentuSample" "VentuSample"

copy_library() {
    local source="$1" destination="$2"
    if [[ -f "$source" ]]; then
        install -m 0644 "$source" "$PAYLOAD/dak/release/lib/$destination"
    fi
}
copy_library "$BUILD_DIR/reaper/libreaper_core.a" "libreaper_core.a"
copy_library "$BUILD_DIR/reaper/libreaper_ffi.a" "libreaper_ffi.a"
copy_library "$BUILD_DIR/pytyliki/libpytyliki_core.a" "libpytyliki_core.a"
copy_library "$BUILD_DIR/pytyliki/libpytyliki_ffi.a" "libpytyliki_ffi.a"
copy_library "$BUILD_DIR/ventusample/libventusample_core.a" "libventusample_core.a"
copy_library "$BUILD_DIR/ventusample/libventusample_pytyliki_dsp.a" "libventusample_pytyliki_dsp.a"

cat > "$PAYLOAD/dak/release/BUILD-INFO.txt" <<EOF
DAK Ecosystem Release Edition
Build date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)
DAK source revision: $(git -C "$ROOT" rev-parse HEAD)
Reaper: $(git -C "$ROOT/projects/reaper" rev-parse HEAD)
Pytyliki: $(git -C "$ROOT/projects/pytyliki" rev-parse HEAD)
OPlague: $(git -C "$ROOT/projects/oplague" rev-parse HEAD)
VentuSample: $(git -C "$ROOT/projects/ventusample" rev-parse HEAD)

Mora: offline browser desktop shell with local application state.
Host tools: Linux x86_64 builds, not DAK kernel executables.
Kernel: experimental Stage 1; validates Boot Info v1, allocates and clears one early physical frame, prints DAK_BOOT_OK and halts.
External application execution: disabled by default.
EOF

(
    cd "$PAYLOAD/dak"
    find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS
    sha256sum --check SHA256SUMS >/dev/null
)

echo "[8/8] Build hybrid BIOS/UEFI release ISO"
bash "$ROOT/boot/build-iso.sh" \
    --work-dir "$BUILD_DIR/boot" \
    --payload-dir "$PAYLOAD/dak" \
    --volume-id DAK_RELEASE \
    --output "$OUTPUT"

ISO_BYTES="$(wc -c < "$OUTPUT" | tr -d ' ')"
echo "DAK Release ISO ready: $OUTPUT"
echo "ISO size: $ISO_BYTES bytes (content-sized; no artificial 4 GiB padding)"
echo "SHA-256: $(sha256sum "$OUTPUT" | awk '{print $1}')"
echo "Payload checksums: $PAYLOAD/dak/SHA256SUMS"
