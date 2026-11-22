#!/usr/bin/env bash
set -euo pipefail

NATIVE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$NATIVE_ROOT/.." && pwd)"
BUILD_ROOT="$REPO_ROOT/build/native"
STAGING="$BUILD_ROOT/iso-root"
WORK_ROOT="$(mktemp -d /tmp/duckos-iso.XXXXXX)"
trap 'rm -rf "$WORK_ROOT"' EXIT

if [[ -z "$LIMINE_DIR" ]]; then
    echo "build-iso: set LIMINE_DIR to the directory containing Limine boot assets" >&2
    exit 1
fi

for tool in make python3 xorriso; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "build-iso: missing required tool: $tool" >&2
        exit 1
    }
done

LIMINE_TOOL="$(command -v limine || true)"
if [[ -z "$LIMINE_TOOL" && -x "$LIMINE_DIR/../bin/limine" ]]; then
    LIMINE_TOOL="$LIMINE_DIR/../bin/limine"
fi
if [[ -z "$LIMINE_TOOL" || ! -x "$LIMINE_TOOL" ]]; then
    echo "build-iso: install the Limine host utility or set LIMINE_TOOL" >&2
    exit 1
fi

EFI_BINARY="$LIMINE_DIR/BOOTX64.EFI"
if [[ ! -f "$EFI_BINARY" ]]; then
    EFI_BINARY="$LIMINE_DIR/EFI/BOOT/BOOTX64.EFI"
fi

for asset in \
    "$LIMINE_DIR/limine-bios.sys" \
    "$LIMINE_DIR/limine-bios-cd.bin" \
    "$LIMINE_DIR/limine-uefi-cd.bin" \
    "$EFI_BINARY"; do
    [[ -f "$asset" ]] || {
        echo "build-iso: missing Limine asset: $asset" >&2
        exit 1
    }
done

make -C "$NATIVE_ROOT/kernel" CC=clang LD=ld.lld

mkdir -p "$BUILD_ROOT" "$STAGING/boot/EFI/BOOT"
cp "$NATIVE_ROOT/kernel/build/kernel.elf" "$STAGING/boot/kernel.elf"
cp "$LIMINE_DIR/limine-bios.sys" "$STAGING/boot/limine-bios.sys"
cp "$LIMINE_DIR/limine-bios-cd.bin" "$STAGING/boot/limine-bios-cd.bin"
cp "$LIMINE_DIR/limine-uefi-cd.bin" "$STAGING/boot/limine-uefi-cd.bin"
cp "$EFI_BINARY" "$STAGING/boot/EFI/BOOT/BOOTX64.EFI"
cp "$NATIVE_ROOT/boot/limine.conf" "$STAGING/limine.conf"

INITRAMFS_ROOT="$WORK_ROOT/initramfs"
mkdir -p "$INITRAMFS_ROOT"
cp -a "$NATIVE_ROOT/initramfs/root/." "$INITRAMFS_ROOT/"

if [[ -n "$BUSYBOX_STATIC" ]]; then
    [[ -f "$BUSYBOX_STATIC" ]] || {
        echo "build-iso: BUSYBOX_STATIC does not name a file" >&2
        exit 1
    }
    mkdir -p "$INITRAMFS_ROOT/bin"
    install -m 0755 "$BUSYBOX_STATIC" "$INITRAMFS_ROOT/bin/busybox"
    ln -sfn busybox "$INITRAMFS_ROOT/bin/sh"
fi

python3 "$NATIVE_ROOT/initramfs/mkinitramfs.py" \
    --root "$INITRAMFS_ROOT" \
    --output "$STAGING/boot/initramfs.cpio"

ISO_PATH="$BUILD_ROOT/DuckOS-x86_64.iso"
mkdir -p "$(dirname "$ISO_PATH")"

xorriso -as mkisofs \
    -R -r -J -hfsplus -apm-block-size 2048 \
    -b boot/limine-bios-cd.bin \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
    --efi-boot boot/limine-uefi-cd.bin \
    -efi-boot-part --efi-boot-image --protective-msdos-label \
    "$STAGING" -o "$ISO_PATH"

"$LIMINE_TOOL" bios-install "$ISO_PATH"
echo "created $ISO_PATH"
