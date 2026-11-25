#!/usr/bin/env bash
set -Eeuo pipefail

ISO=""
OUTPUT_DIR="/tmp/duckos-qemu-test"
OVMF_CODE=""
OVMF_VARS=""
TIMEOUT_SECONDS=12

while (($#)); do
    case "$1" in
        --iso) ISO="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --ovmf-code) OVMF_CODE="$2"; shift 2 ;;
        --ovmf-vars) OVMF_VARS="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: boot/test-qemu.sh --iso FILE [--output-dir DIR] [--ovmf-code FILE --ovmf-vars FILE]"
            exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

[[ -n "$ISO" && -f "$ISO" ]] || { echo "a valid --iso file is required" >&2; exit 2; }
command -v qemu-system-x86_64 >/dev/null 2>&1 || { echo "qemu-system-x86_64 is required" >&2; exit 1; }
command -v timeout >/dev/null 2>&1 || { echo "timeout is required" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd -- "$OUTPUT_DIR" && pwd)"
ISO="$(cd -- "$(dirname -- "$ISO")" && pwd)/$(basename -- "$ISO")"

run_bios() {
    local log="$OUTPUT_DIR/serial-bios.log"
    local status=0
    rm -f "$log"
    timeout "$TIMEOUT_SECONDS" qemu-system-x86_64 \
        -machine q35 -m 256M -cdrom "$ISO" -boot order=d \
        -display none -serial "file:$log" -monitor none \
        -no-reboot -no-shutdown || status=$?

    if [[ "$status" -ne 0 && "$status" -ne 124 && "$status" -ne 137 ]]; then
        echo "BIOS QEMU exited unexpectedly with status $status" >&2
        cat "$log" >&2 || true
        return "$status"
    fi
    if ! grep -Fq "exceptions=0..31 idt=loaded maskable_interrupts=disabled" "$log"; then
        echo "BIOS QEMU did not confirm CPU exception IDT installation:" >&2
        cat "$log" >&2 || true
        return 1
    fi
    if ! grep -Fq "paging=owned-cr3 root=" "$log"; then
        echo "BIOS QEMU did not confirm ownership of the active page tables:" >&2
        cat "$log" >&2 || true
        return 1
    fi
    if ! grep -Fq "vm=map-protect-unmap-verified" "$log"; then
        echo "BIOS QEMU did not pass the live virtual-memory smoke test:" >&2
        cat "$log" >&2 || true
        return 1
    fi
    if ! grep -Fq "DUCKOS_BOOT_OK stage=2" "$log"; then
        echo "BIOS QEMU did not reach the DuckOS boot handoff:" >&2
        cat "$log" >&2 || true
        return 1
    fi
    echo "BIOS boot: PASS"
    cat "$log"
}

run_uefi() {
    [[ -f "$OVMF_CODE" && -f "$OVMF_VARS" ]] || {
        echo "UEFI test needs valid --ovmf-code and --ovmf-vars files" >&2
        return 2
    }
    local log="$OUTPUT_DIR/serial-uefi.log"
    local vars_copy="$OUTPUT_DIR/OVMF_VARS.fd"
    local status=0
    cp "$OVMF_VARS" "$vars_copy"
    rm -f "$log"
    timeout "$TIMEOUT_SECONDS" qemu-system-x86_64 \
        -machine q35 -m 256M -cdrom "$ISO" -boot order=d \
        -drive "if=pflash,format=raw,unit=0,readonly=on,file=$OVMF_CODE" \
        -drive "if=pflash,format=raw,unit=1,file=$vars_copy" \
        -display none -serial "file:$log" -monitor none \
        -no-reboot -no-shutdown || status=$?

    if [[ "$status" -ne 0 && "$status" -ne 124 && "$status" -ne 137 ]]; then
        echo "UEFI QEMU exited unexpectedly with status $status" >&2
        cat "$log" >&2 || true
        return "$status"
    fi
    if ! grep -Fq "exceptions=0..31 idt=loaded maskable_interrupts=disabled" "$log"; then
        echo "UEFI QEMU did not confirm CPU exception IDT installation:" >&2
        cat "$log" >&2 || true
        return 1
    fi
    if ! grep -Fq "vm=map-protect-unmap-verified" "$log"; then
        echo "UEFI QEMU did not pass the live virtual-memory smoke test:" >&2
        cat "$log" >&2 || true
        return 1
    fi
    if ! grep -Fq "DUCKOS_BOOT_OK stage=2" "$log"; then
        echo "UEFI QEMU did not reach the DuckOS boot handoff:" >&2
        cat "$log" >&2 || true
        return 1
    fi
    echo "UEFI boot: PASS"
    cat "$log"
}

run_bios
if [[ -n "$OVMF_CODE" || -n "$OVMF_VARS" ]]; then
    run_uefi
fi
