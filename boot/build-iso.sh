#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "$BASH_SOURCE")/.." && pwd)"
source "$ROOT/boot/limine-toolchain.lock"

WORK_DIR="/tmp/duckos-boot-build"
TMP_ROOT="$(printenv TMPDIR || true)"
if [[ -n "$TMP_ROOT" ]]; then WORK_DIR="$TMP_ROOT/duckos-boot-build"; fi
OUTPUT="$ROOT/dist/DuckOS-Stage1-x86_64.iso"
PAYLOAD_DIR=""
VOLUME_ID="DUCKOS_STAGE1"
ESP_SIZE_MIB=64

while (($#)); do
    case "$1" in
        --work-dir)
            [[ $# -ge 2 ]] || { echo "missing value for --work-dir" >&2; exit 2; }
            WORK_DIR="$2"; shift 2 ;;
        --output)
            [[ $# -ge 2 ]] || { echo "missing value for --output" >&2; exit 2; }
            OUTPUT="$2"; shift 2 ;;
        --payload-dir)
            [[ $# -ge 2 ]] || { echo "missing value for --payload-dir" >&2; exit 2; }
            PAYLOAD_DIR="$2"; shift 2 ;;
        --volume-id)
            [[ $# -ge 2 ]] || { echo "missing value for --volume-id" >&2; exit 2; }
            VOLUME_ID="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: boot/build-iso.sh [--work-dir DIR] [--output FILE] [--payload-dir DIR] [--volume-id LABEL]"
            exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

require_tool() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "required tool not found: $1" >&2
        exit 1
    }
}
for tool in gcc ld readelf clang lld-link curl tar sha256sum xorriso find make \
            dd mkfs.vfat mmd mcopy objdump; do
    require_tool "$tool"
done

target="$(gcc -dumpmachine)"
case "$target" in
    x86_64-*|amd64-*) ;;
    *) echo "DuckOS stage-1 targets x86_64; compiler target is: $target" >&2; exit 1 ;;
esac

[[ "$VOLUME_ID" =~ ^[A-Z0-9_]{1,32}$ ]] || {
    echo "volume id must use 1-32 uppercase letters, digits or underscores" >&2
    exit 2
}
if [[ -n "$PAYLOAD_DIR" && ! -d "$PAYLOAD_DIR" ]]; then
    echo "payload directory does not exist: $PAYLOAD_DIR" >&2
    exit 2
fi

mkdir -p "$WORK_DIR/download" "$WORK_DIR/toolchain" "$WORK_DIR/objects" \
    "$WORK_DIR/uefi-objects" "$WORK_DIR/iso-root" "$(dirname -- "$OUTPUT")"
WORK_DIR="$(cd -- "$WORK_DIR" && pwd)"
OUTPUT_DIR="$(cd -- "$(dirname -- "$OUTPUT")" && pwd)"
OUTPUT="$OUTPUT_DIR/$(basename -- "$OUTPUT")"

archive="$WORK_DIR/download/limine-binary.tar.xz"
if [[ -f "$archive" ]] &&
   ! printf '%s  %s\n' "$LIMINE_BINARY_SHA256" "$archive" | sha256sum --check --status; then
    rm -f "$archive"
fi
if [[ ! -f "$archive" ]]; then
    curl --fail --location --retry 3 --output "$archive" "$LIMINE_BINARY_URL"
fi
printf '%s  %s\n' "$LIMINE_BINARY_SHA256" "$archive" | sha256sum --check

toolchain_dir="$WORK_DIR/toolchain/limine"
mkdir -p "$toolchain_dir"
tar -xf "$archive" -C "$toolchain_dir"

limine_makefile="$(find "$toolchain_dir" -type f -name Makefile -print -quit)"
[[ -n "$limine_makefile" ]] || {
    echo "pinned Limine archive is missing its host-tool Makefile" >&2
    exit 1
}
limine_source_dir="$(dirname -- "$limine_makefile")"
make -C "$limine_source_dir"

find_one() {
    local filename="$1"
    local found
    found="$(find "$toolchain_dir" -type f -name "$filename" -print -quit)"
    [[ -n "$found" ]] || {
        echo "pinned Limine archive does not contain required file: $filename" >&2
        exit 1
    }
    printf '%s\n' "$found"
}

LIMINE_BIN="$(find_one limine)"
LIMINE_BIOS_SYS="$(find_one limine-bios.sys)"
LIMINE_BIOS_CD="$(find_one limine-bios-cd.bin)"

COMMON_KERNEL_FLAGS=(
    -std=c11 -O2 -Wall -Wextra -Werror
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables
    -fomit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone -mgeneral-regs-only
)

echo "[1/6] Build the existing Limine BIOS fallback kernel"
gcc "${COMMON_KERNEL_FLAGS[@]}" \
    -I "$ROOT/foundation" -I "$ROOT/third_party/limine-protocol" \
    -c "$ROOT/kernel/boot/entry.c" -o "$WORK_DIR/objects/limine-entry.o"
gcc "${COMMON_KERNEL_FLAGS[@]}" -I "$ROOT/foundation" \
    -c "$ROOT/foundation/boot_info.c" -o "$WORK_DIR/objects/boot-info.o"
gcc "${COMMON_KERNEL_FLAGS[@]}" -I "$ROOT/foundation" \
    -c "$ROOT/foundation/frame_allocator.c" -o "$WORK_DIR/objects/frame-allocator.o"
ld -nostdlib -static -z max-page-size=0x1000 -T "$ROOT/kernel/linker.ld" \
    "$WORK_DIR/objects/limine-entry.o" \
    "$WORK_DIR/objects/boot-info.o" \
    "$WORK_DIR/objects/frame-allocator.o" \
    -o "$WORK_DIR/duckos-limine.elf"
readelf -h "$WORK_DIR/duckos-limine.elf" | grep -q 'Class:.*ELF64'
readelf -h "$WORK_DIR/duckos-limine.elf" | grep -q 'Machine:.*Advanced Micro Devices X86-64'
readelf -S "$WORK_DIR/duckos-limine.elf" | grep -q '\.limine_requests'
readelf -l "$WORK_DIR/duckos-limine.elf" | grep -q 'LOAD'

echo "[2/6] Build the DuckOS kernel for DuckBoot handoff v1"
gcc "${COMMON_KERNEL_FLAGS[@]}" -I "$ROOT/foundation" -I "$ROOT/duckboot/include" \
    -c "$ROOT/duckboot/kernel_entry.c" -o "$WORK_DIR/objects/duckboot-kernel-entry.o"
ld -nostdlib -static -z max-page-size=0x1000 -T "$ROOT/duckboot/kernel.ld" \
    "$WORK_DIR/objects/duckboot-kernel-entry.o" \
    "$WORK_DIR/objects/boot-info.o" \
    "$WORK_DIR/objects/frame-allocator.o" \
    -o "$WORK_DIR/duckos.elf"
readelf -h "$WORK_DIR/duckos.elf" | grep -q 'Class:.*ELF64'
readelf -h "$WORK_DIR/duckos.elf" | grep -q 'Machine:.*Advanced Micro Devices X86-64'
readelf -l "$WORK_DIR/duckos.elf" | grep -q 'LOAD'
if readelf -S "$WORK_DIR/duckos.elf" | grep -q '\.limine_requests'; then
    echo "DuckBoot kernel must not depend on Limine request sections" >&2
    exit 1
fi

UEFI_FLAGS=(
    --target=x86_64-pc-windows-msvc -std=c11 -O2 -Wall -Wextra -Werror
    -ffreestanding -fno-builtin -fno-stack-protector -fno-stack-check
    -fshort-wchar -mno-red-zone
    -I "$ROOT/duckboot/include" -I "$ROOT/foundation"
)

echo "[3/6] Build the native x86-64 UEFI application"
clang "${UEFI_FLAGS[@]}" -c "$ROOT/duckboot/uefi/entry.c" \
    -o "$WORK_DIR/uefi-objects/entry.obj"
clang --target=x86_64-pc-windows-msvc -c "$ROOT/duckboot/uefi/enter.S" \
    -o "$WORK_DIR/uefi-objects/enter.obj"
clang "${UEFI_FLAGS[@]}" -c "$ROOT/duckboot/core/config.c" \
    -o "$WORK_DIR/uefi-objects/config.obj"
clang "${UEFI_FLAGS[@]}" -c "$ROOT/duckboot/core/elf64.c" \
    -o "$WORK_DIR/uefi-objects/elf64.obj"
clang "${UEFI_FLAGS[@]}" -c "$ROOT/foundation/boot_info.c" \
    -o "$WORK_DIR/uefi-objects/boot-info.obj"
clang "${UEFI_FLAGS[@]}" -c "$ROOT/duckboot/uefi/runtime.c" \
    -o "$WORK_DIR/uefi-objects/runtime.obj"
lld-link /subsystem:efi_application /entry:efi_main /machine:x64 /nodefaultlib \
    /out:"$WORK_DIR/BOOTX64.EFI" \
    "$WORK_DIR/uefi-objects/entry.obj" \
    "$WORK_DIR/uefi-objects/enter.obj" \
    "$WORK_DIR/uefi-objects/config.obj" \
    "$WORK_DIR/uefi-objects/elf64.obj" \
    "$WORK_DIR/uefi-objects/boot-info.obj" \
    "$WORK_DIR/uefi-objects/runtime.obj"
objdump -f "$WORK_DIR/BOOTX64.EFI" | grep -q 'pei-x86-64'

iso_root="$WORK_DIR/iso-root"
rm -rf "$iso_root"
mkdir -p "$iso_root/boot" "$iso_root/third_party"
cp "$WORK_DIR/duckos-limine.elf" "$iso_root/boot/duckos-limine.elf"
cp "$WORK_DIR/duckos.elf" "$iso_root/boot/duckos.elf"
cp "$ROOT/boot/limine.conf" "$iso_root/limine.conf"
cp "$LIMINE_BIOS_SYS" "$iso_root/boot/limine-bios.sys"
cp "$LIMINE_BIOS_CD" "$iso_root/boot/limine-bios-cd.bin"
curl --fail --location --retry 3 --output \
    "$iso_root/third_party/Limine-COPYING.txt" "$LIMINE_COPYING_URL"

esp_image="$iso_root/boot/duckboot-esp.img"
dd if=/dev/zero of="$esp_image" bs=1M count="$ESP_SIZE_MIB" conv=fsync status=none
mkfs.vfat -F 32 -n DUCKBOOT "$esp_image" >/dev/null
mmd -i "$esp_image" ::/EFI
mmd -i "$esp_image" ::/EFI/BOOT
mmd -i "$esp_image" ::/boot
mcopy -i "$esp_image" "$WORK_DIR/BOOTX64.EFI" ::/EFI/BOOT/BOOTX64.EFI
mcopy -i "$esp_image" "$WORK_DIR/duckos.elf" ::/boot/duckos.elf
mcopy -i "$esp_image" "$ROOT/boot/duckboot.cfg" ::/boot/duckboot.cfg

if [[ -n "$PAYLOAD_DIR" ]]; then
    mkdir -p "$iso_root/duckos"
    cp -a "$PAYLOAD_DIR"/. "$iso_root/duckos/"
fi

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT"
echo "[4/6] Create hybrid ISO: Limine BIOS fallback + DuckBoot UEFI ESP"
xorriso -as mkisofs \
    -R -r -J -V "$VOLUME_ID" \
    -b boot/limine-bios-cd.bin \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    --efi-boot boot/duckboot-esp.img \
    -efi-boot-part --efi-boot-image --protective-msdos-label \
    "$iso_root" -o "$OUTPUT"
"$LIMINE_BIN" bios-install "$OUTPUT"
(cd "$OUTPUT_DIR" && sha256sum "$(basename -- "$OUTPUT")" > "$(basename -- "$OUTPUT").sha256")
echo "DuckOS hybrid ISO ready: $OUTPUT"
echo "UEFI loader: $WORK_DIR/BOOTX64.EFI"
echo "DuckBoot kernel: $WORK_DIR/duckos.elf"
echo "BIOS fallback kernel: $WORK_DIR/duckos-limine.elf"
echo "ESP image: $ESP_SIZE_MIB MiB"
cat "$OUTPUT.sha256"
