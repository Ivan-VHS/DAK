#!/usr/bin/env bash
set -Eeuo pipefail

OUTPUT=""
declare -a EFI_ENTRIES=()
declare -a BIOS_TARGETS=()

usage() {
    cat <<'EOF'
Usage: boot/render-loader-menu.sh --output FILE [--efi-entry NAME]... [--bios-target DRIVE:PARTITION]...

EFI names are exact UEFI firmware boot-entry descriptions.
BIOS drive numbers are 1-based; partition 0 selects the whole disk/MBR.
The input must be an existing regular Limine configuration file.
EOF
}

while (($#)); do
    case "$1" in
        --output)
            [[ $# -ge 2 ]] || { echo "missing value for --output" >&2; exit 2; }
            OUTPUT="$2"; shift 2 ;;
        --efi-entry)
            [[ $# -ge 2 ]] || { echo "missing value for --efi-entry" >&2; exit 2; }
            EFI_ENTRIES+=("$2"); shift 2 ;;
        --bios-target)
            [[ $# -ge 2 ]] || { echo "missing value for --bios-target" >&2; exit 2; }
            BIOS_TARGETS+=("$2"); shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
done

[[ -n "$OUTPUT" ]] || { echo "--output is required" >&2; exit 2; }
[[ -f "$OUTPUT" && ! -L "$OUTPUT" ]] || {
    echo "output must be an existing regular, non-symlink file" >&2
    exit 2
}
(("${#EFI_ENTRIES[@]}" <= 16 && "${#BIOS_TARGETS[@]}" <= 16)) || {
    echo "at most 16 EFI entries and 16 BIOS targets are allowed" >&2
    exit 2
}

declare -A SEEN_EFI=()
declare -A SEEN_BIOS=()

for name in "${EFI_ENTRIES[@]}"; do
    [[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9\ _\(\)\.\+-]{0,63}$ ]] || {
        echo "invalid EFI boot-entry name: $name" >&2
        exit 2
    }
    key="$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
    [[ -z "${SEEN_EFI[$key]+x}" ]] || {
        echo "duplicate EFI boot-entry name: $name" >&2
        exit 2
    }
    SEEN_EFI["$key"]=1
done

for target in "${BIOS_TARGETS[@]}"; do
    [[ "$target" =~ ^(0|[1-9][0-9]{0,2}):(0|[1-9][0-9]{0,2})$ ]] || {
        echo "BIOS target must use DRIVE:PARTITION with decimal values" >&2
        exit 2
    }
    drive="${BASH_REMATCH[1]}"
    partition="${BASH_REMATCH[2]}"
    drive_number=$((10#$drive))
    partition_number=$((10#$partition))
    ((drive_number >= 1 && drive_number <= 255)) || {
        echo "BIOS drive must be in the range 1..255" >&2
        exit 2
    }
    ((partition_number >= 0 && partition_number <= 255)) || {
        echo "BIOS partition must be in the range 0..255" >&2
        exit 2
    }
    normalized="$drive_number:$partition_number"
    [[ -z "${SEEN_BIOS[$normalized]+x}" ]] || {
        echo "duplicate BIOS target: $target" >&2
        exit 2
    }
    SEEN_BIOS["$normalized"]=1
done

temporary="$(mktemp "${OUTPUT}.tmp.XXXXXX")"
trap 'rm -f "$temporary"' EXIT
cp -- "$OUTPUT" "$temporary"

for name in "${EFI_ENTRIES[@]}"; do
    cat >> "$temporary" <<EOF

# DuckOS external UEFI firmware entry
/UEFI: $name
    if_fw_type: UEFI
    protocol: efi_boot_entry
    entry: $name
EOF
done

for target in "${BIOS_TARGETS[@]}"; do
    drive="${target%%:*}"
    partition="${target#*:}"
    cat >> "$temporary" <<EOF

# DuckOS external BIOS chainload target
/BIOS: drive $drive partition $partition
    if_fw_type: BIOS
    protocol: bios
    drive: $drive
    partition: $partition
EOF
done

mv -- "$temporary" "$OUTPUT"
trap - EXIT
