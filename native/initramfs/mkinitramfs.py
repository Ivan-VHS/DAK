#!/usr/bin/env python3
"""Build a deterministic, path-safe newc initramfs using only Python's stdlib."""

from __future__ import annotations

import argparse
import os
import stat
import tempfile
from pathlib import Path


def _align4(stream) -> None:
    padding = (-stream.tell()) % 4
    if padding:
        stream.write(b"\0" * padding)


def _safe_archive_name(path: Path, root: Path) -> str:
    name = path.relative_to(root).as_posix()
    if not name or name == ".":
        raise ValueError("the initramfs root itself is not an archive entry")
    if name.startswith("/") or "\\" in name:
        raise ValueError(f"unsafe archive path: {name!r}")
    if any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError(f"unsafe archive path: {name!r}")
    return name


def _entries(root: Path):
    items: list[Path] = []

    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        directory_names.sort()
        file_names.sort()

        for name in list(directory_names):
            path = current_path / name
            if path.is_symlink():
                items.append(path)
                directory_names.remove(name)
            else:
                items.append(path)

        items.extend(current_path / name for name in file_names)

    return sorted(items, key=lambda item: item.relative_to(root).as_posix())


def _entry_data(path: Path) -> tuple[int, bytes, int]:
    info = path.lstat()
    mode = info.st_mode

    if stat.S_ISDIR(mode):
        return stat.S_IFDIR | stat.S_IMODE(mode), b"", 2

    if stat.S_ISREG(mode):
        return stat.S_IFREG | stat.S_IMODE(mode), path.read_bytes(), 1

    if stat.S_ISLNK(mode):
        target = os.readlink(path)
        if os.path.isabs(target) or "\\" in target:
            raise ValueError(f"unsafe symlink target at {path}: {target!r}")
        if any(part == ".." for part in Path(target).parts):
            raise ValueError(f"symlink leaves the initramfs tree: {path} -> {target}")
        return stat.S_IFLNK | 0o777, os.fsencode(target), 1

    raise ValueError(f"unsupported special file in initramfs: {path}")


def _write_entry(stream, inode: int, name: str, mode: int, data: bytes,
                 nlink: int, mtime: int) -> None:
    encoded_name = os.fsencode(name) + b"\0"
    fields = (
        inode, mode, 0, 0, nlink, mtime, len(data),
        0, 0, 0, 0, len(encoded_name), 0,
    )
    header = b"070701" + b"".join(f"{value:08x}".encode("ascii") for value in fields)

    if len(header) != 110:
        raise AssertionError("newc header must be exactly 110 bytes")

    stream.write(header)
    stream.write(encoded_name)
    _align4(stream)
    stream.write(data)
    _align4(stream)


def build_archive(root: Path, output: Path, epoch: int | None = None) -> None:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"initramfs root is not a directory: {root}")

    if epoch is None:
        epoch_text = os.environ.get("SOURCE_DATE_EPOCH")
        epoch = int(epoch_text) if epoch_text is not None else 0

    if epoch < 0 or epoch > 0xFFFFFFFF:
        raise ValueError("SOURCE_DATE_EPOCH must fit the newc 32-bit timestamp field")

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{output.name}.", suffix=".tmp",
            dir=output.parent, delete=False
        ) as stream:
            temporary_path = Path(stream.name)

            for inode, path in enumerate(_entries(root), start=1):
                name = _safe_archive_name(path, root)
                mode, data, nlink = _entry_data(path)
                _write_entry(stream, inode, name, mode, data, nlink, epoch)

            _write_entry(stream, inode + 1 if "inode" in locals() else 1,
                         "TRAILER!!!", 0, b"", 1, epoch)
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epoch", type=int, default=None)
    args = parser.parse_args()

    try:
        build_archive(args.root, args.output, args.epoch)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(f"created {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
