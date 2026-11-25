#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "$BASH_SOURCE")/.." && pwd)"
source "$ROOT/boot/limine-toolchain.lock"

WORK_DIR="/tmp/duckos-boot-build"
TMP_ROOT="$(printenv TMPDIR || true)"
if [[ -n "$TMP_ROOT" ]]; then WORK_DIR="$TMP_ROOT/duckos-boot-build"; fi
OUTPUT="$ROOT/dist/DuckOS-Stage0-x86_64.iso"

while (($#)); do
    case "$1" in
        --work-dir)
            [[ $# -ge 2 ]] || { echo "missing value for --work-dir" >&2; exit 2; }
            WORK_DIR="$2"; shift 2 ;;
        --output)
            [[ $# -ge 2 ]] || { echo "missing value for --output" >&2; exit 2; }
            OUTPUT="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: boot/build-iso.sh [--work-dir DIR] [--output FILE]"
            exit 0 ;;
        *)
            echo "unknown argument: $1" >&2
            exit 2 ;;
    esac
done

require_tool() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "required tool not found: $1" >&2
        exit 1
    }
}
for tool in gcc ld readelf curl tar sha256sum xorriso find; do require_tool "$tool"; done

target="$(gcc -dumpmachine)"
case "$target" in
    x86_64-*|amd64-*) ;;
    *) echo "DuckOS stage-0 targets x86_64; compiler target is: $target" >&2; exit 1 ;;
esac

mkdir -p "$WORK_DIR/download" "$WORK_DIR/toolchain" "$WORK_DIR/objects" "$WORK_DIR/iso-root"
mkdir -p "$(dirname -- "$OUTPUT")"
WORK_DIR="$(cd -- "$WORK_DIR" && pwd)"
OUTPUT_DIR="$(cd -- "$(dirname -- "$OUTPUT")" && pwd)"
OUTPUT="$OUTPUT_DIR/$(basename -- "$OUTPUT")"

archive="$WORK_DIR/download/limine-binary.tar.xz"
if [[ -f "$archive" ]]; then
    if ! printf '%s  %s\n' "$LIMINE_BINARY_SHA256" "$archive" | sha256sum --check --status; then
        rm -f "$archive"
    fi
fi
if [[ ! -f "$archive" ]]; then
    curl --fail --location --retry 3 --output "$archive" "$LIMINE_BINARY_URL"
fi
printf '%s  %s\n' "$LIMINE_BINARY_SHA256" "$archive" | sha256sum --check

toolchain_dir="$WORK_DIR/toolchain/limine"
mkdir -p "$toolchain_dir"
tar -xf "$archive" -C "$toolchain_dir"

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
LIMINE_UEFI_CD="$(find_one limine-uefi-cd.bin)"
LIMINE_EFI="$(find_one BOOTX64.EFI)"

gcc -std=c11 -O2 -Wall -Wextra -Werror \
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie \
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -fno-omit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone \
    -mgeneral-regs-only \
    -I "$ROOT/foundation" -I "$ROOT/third_party/limine-protocol" \
    -c "$ROOT/kernel/boot/entry.c" -o "$WORK_DIR/objects/duckos-entry.o"

gcc -std=c11 -O2 -Wall -Wextra -Werror \
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie \
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -fno-omit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone \
    -mgeneral-regs-only \
    -I "$ROOT/foundation" \
    -c "$ROOT/foundation/boot_info.c" -o "$WORK_DIR/objects/boot-info.o"

ld -nostdlib -static -z max-page-size=0x1000 \
    -T "$ROOT/kernel/linker.ld" \
    "$WORK_DIR/objects/duckos-entry.o" \
    "$WORK_DIR/objects/boot-info.o" \
    -o "$WORK_DIR/duckos.elf"

readelf -h "$WORK_DIR/duckos.elf" | grep -q 'Class:.*ELF64'
readelf -h "$WORK_DIR/duckos.elf" | grep -q 'Machine:.*Advanced Micro Devices X86-64'
readelf -S "$WORK_DIR/duckos.elf" | grep -q '\.limine_requests'
readelf -l "$WORK_DIR/duckos.elf" | grep -q 'LOAD'

iso_root="$WORK_DIR/iso-root"
rm -rf "$iso_root"
mkdir -p "$iso_root/boot" "$iso_root/EFI/BOOT" "$iso_root/third_party"
cp "$WORK_DIR/duckos.elf" "$iso_root/boot/duckos.elf"
cp "$ROOT/boot/limine.conf" "$iso_root/limine.conf"
cp "$LIMINE_BIOS_SYS" "$iso_root/boot/limine-bios.sys"
cp "$LIMINE_BIOS_CD" "$iso_root/boot/limine-bios-cd.bin"
cp "$LIMINE_UEFI_CD" "$iso_root/boot/limine-uefi-cd.bin"
cp "$LIMINE_EFI" "$iso_root/EFI/BOOT/BOOTX64.EFI"
curl --fail --location --retry 3 --output "$iso_root/third_party/Limine-COPYING.txt" "$LIMINE_COPYING_URL"

rm -f "$OUTPUT"
xorriso -as mkisofs \
    -R -r -J -V DUCKOS_STAGE0 \
    -b boot/limine-bios-cd.bin \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    --efi-boot boot/limine-uefi-cd.bin \
    -efi-boot-part --efi-boot-image --protective-msdos-label \
    "$iso_root" -o "$OUTPUT"

"$LIMINE_BIN" bios-install "$OUTPUT"
sha256sum "$OUTPUT" > "$OUTPUT.sha256"
echo "DuckOS stage-0 ISO ready: $OUTPUT"
echo "Kernel ELF: $WORK_DIR/duckos.elf"
cat "$OUTPUT.sha256"
