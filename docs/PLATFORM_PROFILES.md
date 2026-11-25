# DuckOS desktop and boot target profiles

Updated: 2026-11-25.

This integration separates the user-space desktop session from the firmware boot path. The catalogs contain the 20 requested alternatives in each area; they do not claim that every listed project is a drop-in clone or is already ported to DuckOS.

## Desktop session profiles

`catalogs/desktop-sessions.v1.json` and `duckos/ui/session_profiles.rpr` register ten desktop environments and ten window managers:

| Class | Profiles |
|---|---|
| Desktop environments | GNOME, Xfce, Cinnamon, MATE, LXQt, Budgie, Pantheon, Deepin, Unity, Enlightenment |
| Window managers | i3, Sway, AwesomeWM, Xmonad, Hyprland, Openbox, Fluxbox, JWM, IceWM, Ratpoison |

A desktop environment includes a wider session and application stack. A window manager alone does not provide a complete DE. The catalog records each profile's display protocol and its primary windowing component.

All 20 currently have `execution_state: catalog-only` and `native_supported: false`. External Linux desktops need a Linux-compatible userland, process and session managers, VFS, capability enforcement, input services and a working X11 or Wayland host. Those runtime facilities are not present in the current DuckOS Stage 1 kernel. The Reaper profile manager is an executable compatibility and readiness policy; it is not a process launcher or compositor.

`session_plan` refuses to plan a session unless its package, display backend and required services are declared available. `switch_decision` requires `desktop.session.switch` and a recovery checkpoint. The switch state machine starts a candidate session, health-checks it, commits only on success and otherwise restores the previous session or enters the safe-console fallback state. These are policy transitions until a native session manager and process runtime are implemented.

Mora is preserved as the existing shell and catalog default. It is not relabeled as a native kernel compositor or replaced by any of these profiles.

## Boot loader targets

`catalogs/boot-loaders.v1.json` and `duckos/boot/loader_profiles.rpr` classify all 20 entries from the bootloader survey. They deliberately distinguish actual boot managers from firmware stacks, helper modules, network boot and kernel handoff mechanisms.

- **UEFI firmware entries:** systemd-boot and rEFInd can be selected through an already-existing UEFI Boot#### entry.
- **BIOS chainload targets:** LILO, SYSLINUX, EXTLINUX, GRUB Legacy, BURG, Plop Boot Manager, Smart Boot Manager, XOSL and BootIt NG can only be selected when an existing compatible BIOS disk/partition target is explicitly supplied.
- **Not local loader replacements:** PXELINUX requires PXE infrastructure; MEMDISK is a helper; U-Boot and Barebox are embedded-platform loaders; Coreboot/SeaBIOS and TianoCore EDK II are firmware stacks; kexec is a running-kernel handoff mechanism; chainloading is a technique rather than a standalone product.
- **Current loader:** Limine remains the active DuckOS bootloader and the menu host.

### Add external entries to a DuckOS ISO

The ISO generator can add explicitly supplied external targets to the Limine menu:

```sh
# UEFI names must match existing firmware boot-entry descriptions.
boot/build-iso.sh --efi-entry "Windows Boot Manager" --efi-entry "rEFInd"

# BIOS disk number is 1-based. Partition 0 selects the whole disk/MBR.
boot/build-iso.sh --bios-target 1:0 --bios-target 2:1

# Both types can be added to the same hybrid image.
boot/build-iso.sh \
  --efi-entry "Windows Boot Manager" \
  --efi-entry "systemd-boot" \
  --bios-target 1:0
```

The same options are available on `boot/build-release-iso.sh`. The values are configuration supplied by the operator; DuckOS does not yet enumerate host UEFI NVRAM entries or scan physical disks automatically. On a Linux host, `efibootmgr -v` can help identify existing UEFI entry names. Check the disk/partition mapping independently before adding a BIOS target.

The renderer writes UEFI entries using Limine's `efi_boot_entry` protocol and BIOS targets using its `bios` protocol. Firmware filters hide entries that cannot apply to the current boot mode. The existing DuckOS Limine entry and `default_entry: 1` remain unchanged. Selection is performed by Limine at boot time; this does not install another loader, rewrite a disk, flash firmware or guarantee that an external target is valid.

The build-time menu renderer validates names and target ranges, rejects duplicates and symlink output, and replaces the config atomically. Its negative and positive fixtures run in `boot/test-loader-menu.sh` and the boot-image workflow.

## Security and maturity

No loader option changes firmware setup variables except the normal one-shot UEFI selection performed by Limine when the operator chooses an explicitly configured UEFI entry. The generator never installs or updates a bootloader, edits a partition table, flashes firmware, disables Secure Boot or claims Secure Boot compatibility for external entries. Secure Boot and authenticated boot-chain work remain separate release gates.

The boot selection menu is a real ISO-build feature. The DE registry and switch-state machine are native Reaper policy contracts, not yet a native desktop session runtime. Physical hardware validation remains the operator's responsibility; existing DuckOS boot verification covers the declared QEMU BIOS/OVMF UEFI Stage 1 path only.
