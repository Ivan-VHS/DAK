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
for tool in gcc ld readelf curl tar sha256sum xorriso find make; do require_tool "$tool"; done

target="$(gcc -dumpmachine)"
case "$target" in
    x86_64-*|amd64-*) ;;
    *) echo "DuckOS stage-1 targets x86_64; compiler target is: $target" >&2; exit 1 ;;
esac

[[ "$VOLUME_ID" =~ ^[A-Z0-9_]{1,32}$ ]] || { echo "volume id must use 1-32 uppercase letters, digits or underscores" >&2; exit 2; }
if [[ -n "$PAYLOAD_DIR" && ! -d "$PAYLOAD_DIR" ]]; then
    echo "payload directory does not exist: $PAYLOAD_DIR" >&2
    exit 2
fi

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

# The official binary release ships the host-side 'limine' installer as
# portable source. Upstream documents rebuilding it with make after unpacking.
limine_makefile="$(find "$toolchain_dir" -type f -name Makefile -print -quit)"
[[ -n "$limine_makefile" ]] || {
    echo "pinned Limine binary archive is missing its host-tool Makefile" >&2
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
LIMINE_UEFI_CD="$(find_one limine-uefi-cd.bin)"
LIMINE_EFI="$(find_one BOOTX64.EFI)"

gcc -std=c11 -O2 -Wall -Wextra -Werror \
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie \
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -fno-omit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone \
    -mgeneral-regs-only \
    -I "$ROOT/foundation" -I "$ROOT/kernel/arch/x86_64" -I "$ROOT/third_party/limine-protocol" \
    -c "$ROOT/kernel/boot/entry.c" -o "$WORK_DIR/objects/duckos-entry.o"

gcc -std=c11 -O2 -Wall -Wextra -Werror \
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie \
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -fno-omit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone \
    -mgeneral-regs-only \
    -I "$ROOT/foundation" \
    -c "$ROOT/foundation/boot_info.c" -o "$WORK_DIR/objects/boot-info.o"

gcc -std=c11 -O2 -Wall -Wextra -Werror \
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie \
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -fno-omit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone \
    -mgeneral-regs-only \
    -I "$ROOT/foundation" \
    -c "$ROOT/foundation/frame_allocator.c" -o "$WORK_DIR/objects/frame-allocator.o"

gcc -std=c11 -O2 -Wall -Wextra -Werror \
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie \
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -fno-omit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone \
    -mgeneral-regs-only \
    -I "$ROOT/foundation" \
    -c "$ROOT/foundation/idt.c" -o "$WORK_DIR/objects/idt.o"

gcc -std=c11 -O2 -Wall -Wextra -Werror \
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie \
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -fno-omit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone \
    -mgeneral-regs-only \
    -I "$ROOT/foundation" \
    -c "$ROOT/foundation/page_table.c" -o "$WORK_DIR/objects/page-table.o"

gcc -std=c11 -O2 -Wall -Wextra -Werror \
    -ffreestanding -fno-stack-protector -fno-pic -fno-pie \
    -fno-builtin -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -fno-omit-frame-pointer -m64 -mcmodel=kernel -mno-red-zone \
    -mgeneral-regs-only \
    -I "$ROOT/foundation" -I "$ROOT/kernel/arch/x86_64" \
    -c "$ROOT/kernel/arch/x86_64/interrupts.c" -o "$WORK_DIR/objects/interrupts.o"

gcc -m64 -mcmodel=kernel -mno-red-zone -fno-pic -fno-pie \
    -c "$ROOT/kernel/arch/x86_64/exceptions.S" -o "$WORK_DIR/objects/exceptions.o"

ld -nostdlib -static -z max-page-size=0x1000 \
    -T "$ROOT/kernel/linker.ld" \
    "$WORK_DIR/objects/duckos-entry.o" \
    "$WORK_DIR/objects/boot-info.o" \
    "$WORK_DIR/objects/frame-allocator.o" \
    "$WORK_DIR/objects/idt.o" \
    "$WORK_DIR/objects/page-table.o" \
    "$WORK_DIR/objects/interrupts.o" \
    "$WORK_DIR/objects/exceptions.o" \
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

if [[ -n "$PAYLOAD_DIR" ]]; then
    mkdir -p "$iso_root/duckos"
    cp -a "$PAYLOAD_DIR"/. "$iso_root/duckos/"
fi

rm -f "$OUTPUT"
xorriso -as mkisofs \
    -R -r -J -V "$VOLUME_ID" \
    -b boot/limine-bios-cd.bin \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    --efi-boot boot/limine-uefi-cd.bin \
    -efi-boot-part --efi-boot-image --protective-msdos-label \
    "$iso_root" -o "$OUTPUT"

"$LIMINE_BIN" bios-install "$OUTPUT"
(cd "$OUTPUT_DIR" && sha256sum "$(basename -- "$OUTPUT")" > "$(basename -- "$OUTPUT").sha256")
echo "DuckOS ISO ready ($VOLUME_ID): $OUTPUT"
echo "Kernel ELF: $WORK_DIR/duckos.elf"
cat "$OUTPUT.sha256"
