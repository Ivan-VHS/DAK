# DuckOS initramfs

The initramfs is a deterministic `newc` CPIO archive. The generator uses only the Python standard library and refuses special files and unsafe archive paths.

The current early userspace expects a **static** BusyBox binary. Build or obtain it from a trusted distribution package, then stage it as:

- `root/bin/busybox` (executable)
- `root/bin/sh -> busybox` (relative symlink)

The `root/init` script is the kernel's first userspace process once a future kernel `exec` path is implemented. At this bring-up milestone the kernel reports the Limine module list but does not yet unpack CPIO or launch PID 1. The ISO therefore boots the kernel and carries the initramfs as a module; it does not claim to reach a functioning desktop.

Generate an archive:

```sh
python3 native/initramfs/mkinitramfs.py \
  --root native/initramfs/root \
  --output build/initramfs.cpio
```

`SOURCE_DATE_EPOCH` controls timestamps for reproducible output.
