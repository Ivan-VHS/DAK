#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "$BASH_SOURCE")/.." && pwd)"
RENDER="$ROOT/boot/render-loader-menu.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

BASE="$WORK/limine.conf"
cat > "$BASE" <<'EOF'
timeout: 4
default_entry: 1

/DuckOS Native x86_64
    protocol: limine
    path: boot():/boot/duckos.elf
EOF
cp "$BASE" "$WORK/expected.conf"

bash "$RENDER" --output "$BASE" \
    --efi-entry "Windows Boot Manager" \
    --efi-entry "rEFInd" \
    --bios-target "1:0" \
    --bios-target "2:1"

grep -Fq 'default_entry: 1' "$BASE"
grep -Fq 'protocol: efi_boot_entry' "$BASE"
grep -Fq 'entry: Windows Boot Manager' "$BASE"
grep -Fq 'if_fw_type: UEFI' "$BASE"
grep -Fq 'protocol: bios' "$BASE"
grep -Fq 'drive: 1' "$BASE"
grep -Fq 'partition: 0' "$BASE"
grep -Fq 'drive: 2' "$BASE"
grep -Fq 'partition: 1' "$BASE"

cp "$WORK/expected.conf" "$BASE"
if bash "$RENDER" --output "$BASE" --efi-entry $'bad\nentry'; then
    echo "renderer accepted an injected newline" >&2
    exit 1
fi
cmp -s "$BASE" "$WORK/expected.conf"

if bash "$RENDER" --output "$BASE" --efi-entry "rEFInd" --efi-entry "rEFInd"; then
    echo "renderer accepted a duplicate EFI entry" >&2
    exit 1
fi
cmp -s "$BASE" "$WORK/expected.conf"

if bash "$RENDER" --output "$BASE" --bios-target "0:0"; then
    echo "renderer accepted BIOS drive zero" >&2
    exit 1
fi
if bash "$RENDER" --output "$BASE" --bios-target "256:0"; then
    echo "renderer accepted an out-of-range BIOS drive" >&2
    exit 1
fi
if bash "$RENDER" --output "$BASE" --bios-target "1:256"; then
    echo "renderer accepted an out-of-range BIOS partition" >&2
    exit 1
fi
if bash "$RENDER" --output "$BASE" --bios-target "1"; then
    echo "renderer accepted a malformed BIOS target" >&2
    exit 1
fi

cp "$BASE" "$WORK/real.conf"
ln -s "$WORK/real.conf" "$WORK/link.conf"
if bash "$RENDER" --output "$WORK/link.conf" --efi-entry "rEFInd"; then
    echo "renderer accepted a symlink output" >&2
    exit 1
fi

echo "DuckOS Limine external-entry renderer tests passed."
