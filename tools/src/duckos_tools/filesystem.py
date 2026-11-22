from __future__ import annotations

import hashlib
import json
import mmap
import os
import random
import stat
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any


def _walk_files(root: Path):
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            name for name in directories
            if not (current_path / name).is_symlink()
        )
        for name in sorted(files):
            yield current_path / name
        for name in sorted(directories):
            yield current_path / name


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_tree(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in _walk_files(root):
        relative = path.relative_to(root).as_posix()
        try:
            info = path.lstat()
        except OSError:
            continue
        entry: dict[str, Any] = {
            "kind": "symlink" if stat.S_ISLNK(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "file",
            "mode": stat.S_IMODE(info.st_mode),
            "size": info.st_size,
            "mtime_ns": info.st_mtime_ns,
        }
        if entry["kind"] == "symlink":
            try:
                entry["target"] = os.readlink(path)
            except OSError:
                entry["target"] = None
        elif entry["kind"] == "file":
            entry["sha256"] = _file_hash(path)
        result[relative] = entry
    return result


def dir_tree_diff(left: str, right: str, as_json: bool = False) -> None:
    left_root = Path(left).resolve(strict=True)
    right_root = Path(right).resolve(strict=True)
    if not left_root.is_dir() or not right_root.is_dir():
        raise ValueError("оба аргумента должны быть каталогами")

    before = _snapshot_tree(left_root)
    after = _snapshot_tree(right_root)
    changes: list[dict[str, Any]] = []
    for name in sorted(before.keys() | after.keys()):
        old = before.get(name)
        new = after.get(name)
        if old is None:
            changes.append({"path": name, "status": "added", "after": new})
        elif new is None:
            changes.append({"path": name, "status": "deleted", "before": old})
        elif old != new:
            changed_fields = [
                key for key in sorted(old.keys() | new.keys())
                if old.get(key) != new.get(key)
            ]
            changes.append({
                "path": name,
                "status": "changed",
                "fields": changed_fields,
                "before": old,
                "after": new,
            })

    if as_json:
        print(json.dumps({"schema": "duckos.dir-tree-diff.v1", "changes": changes},
                         ensure_ascii=False, indent=2))
        return

    if not changes:
        print("Каталоги совпадают по содержимому и выбранным метаданным.")
        return
    for change in changes:
        marker = {"added": "+", "deleted": "-", "changed": "~"}[change["status"]]
        details = ", ".join(change.get("fields", []))
        print(f"{marker} {change['path']}" + (f" ({details})" if details else ""))
    print(f"\nИзменений: {len(changes)}")


def disk_hotspots(directory: str, limit: int = 20) -> None:
    root = Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("нужен существующий каталог")
    if limit < 1:
        raise ValueError("limit должен быть не меньше 1")

    seen_inodes: set[tuple[int, int]] = set()
    directory_bytes: dict[Path, int] = {root: 0}
    file_rows: list[tuple[int, int, Path]] = []
    logical_total = 0
    allocated_total = 0

    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            name for name in directories
            if not (current_path / name).is_symlink()
        )
        for name in directories:
            directory_bytes.setdefault(current_path / name, 0)
        for name in files:
            path = current_path / name
            try:
                info = path.stat(follow_symlinks=False)
            except OSError:
                continue
            if not stat.S_ISREG(info.st_mode):
                continue
            logical_total += info.st_size
            identity = (info.st_dev, info.st_ino)
            if identity in seen_inodes:
                continue
            seen_inodes.add(identity)
            allocated = getattr(info, "st_blocks", 0) * 512
            if not allocated:
                allocated = info.st_size
            allocated_total += allocated
            file_rows.append((allocated, info.st_size, path))
            parent = path.parent
            while True:
                directory_bytes[parent] = directory_bytes.get(parent, 0) + allocated
                if parent == root or parent.parent == parent:
                    break
                parent = parent.parent

    print(f"Каталог: {root}")
    print(f"Логический объём с учётом hard links: {logical_total:,} bytes")
    print(f"Занято на диске, hard links учтены один раз: {allocated_total:,} bytes")
    print("\nСамые тяжёлые подкаталоги:")
    subdirectories = [
        (size, path) for path, size in directory_bytes.items() if path != root
    ]
    for size, path in sorted(subdirectories, reverse=True)[:limit]:
        print(f"{size:>14,}  {path.relative_to(root)}")
    print("\nСамые тяжёлые файлы:")
    for allocated, logical, path in sorted(file_rows, reverse=True)[:limit]:
        sparse_note = " sparse" if allocated < logical else ""
        print(f"{allocated:>14,} allocated  {logical:>14,} logical  {path.relative_to(root)}{sparse_note}")


def mmap_bench(filename: str, size_mib: int = 64) -> None:
    path = Path(filename).resolve(strict=True)
    if not path.is_file():
        raise ValueError("нужен обычный файл")
    if size_mib < 1:
        raise ValueError("size-mib должен быть не меньше 1")

    file_size = path.stat().st_size
    length = min(file_size, size_mib * 1024 * 1024)
    if length == 0:
        raise ValueError("нельзя измерить пустой файл")
    page_size = getattr(os, "sysconf", lambda _name: 4096)("SC_PAGE_SIZE")
    page_count = (length + page_size - 1) // page_size
    if page_count > 250_000:
        raise ValueError("слишком много страниц для этой версии; ограничьте --size-mib до 1024")

    try:
        import resource
    except ImportError:
        resource = None

    def faults() -> tuple[int, int]:
        if resource is None:
            return 0, 0
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_minflt, usage.ru_majflt

    pages = list(range(0, length, page_size))
    random_pages = pages.copy()
    random.Random(20261122).shuffle(random_pages)

    with path.open("rb") as stream:
        with mmap.mmap(stream.fileno(), length, access=mmap.ACCESS_READ) as mapped:
            before = faults()
            start = time.perf_counter()
            checksum = 0
            for offset in pages:
                checksum ^= mapped[offset]
            sequential_time = time.perf_counter() - start
            middle = faults()
            start = time.perf_counter()
            for offset in random_pages:
                checksum ^= mapped[offset]
            random_time = time.perf_counter() - start
            after = faults()

    sequential_faults = (middle[0] - before[0], middle[1] - before[1])
    random_faults = (after[0] - middle[0], after[1] - middle[1])
    print(f"Файл: {path} ({length:,} bytes; page size {page_size})")
    print(f"Последовательно: {sequential_time * 1000:.2f} ms | "
          f"{length / max(sequential_time, 1e-9) / (1024 * 1024):.1f} MiB/s | "
          f"minor/major faults {sequential_faults[0]}/{sequential_faults[1]}")
    print(f"Случайно:        {random_time * 1000:.2f} ms | "
          f"{length / max(random_time, 1e-9) / (1024 * 1024):.1f} MiB/s | "
          f"minor/major faults {random_faults[0]}/{random_faults[1]}")
    print(f"Контрольная сумма чтения: {checksum}")
    print("Примечание: второй проход может использовать page cache; это не cold-cache benchmark.")


def atomic_write(filename: str, content: str) -> None:
    destination = Path(filename).absolute()
    parent = destination.parent
    if not parent.is_dir():
        raise ValueError(f"каталог назначения не существует: {parent}")
    if destination.is_symlink():
        raise ValueError("atomic-write отказывается заменять symlink; укажите конечный файл")
    try:
        old_mode = stat.S_IMODE(destination.stat().st_mode)
    except FileNotFoundError:
        old_mode = 0o600

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=parent,
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(content)
            stream.flush()
            os.fchmod(stream.fileno(), old_mode) if hasattr(os, "fchmod") else os.chmod(temporary_name, old_mode)
            os.fsync(stream.fileno())
        os.replace(temporary_name, destination)
        temporary_name = None
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_name:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
    print(f"Атомарно записано: {destination}")


def symlink_loop_find(directory: str) -> None:
    root = Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("нужен существующий каталог")

    findings = 0
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        names = list(directories) + list(files)
        for name in names:
            link = current_path / name
            if not link.is_symlink():
                continue
            try:
                link.resolve(strict=True)
            except RuntimeError:
                print(f"LOOP    {link.relative_to(root)}")
                findings += 1
            except FileNotFoundError:
                print(f"BROKEN  {link.relative_to(root)} -> {os.readlink(link)}")
                findings += 1
            except OSError as error:
                print(f"ERROR   {link.relative_to(root)}: {error}")
                findings += 1
    print(f"Найдено проблемных ссылок: {findings}")


def file_age_hist(directory: str) -> None:
    root = Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("нужен существующий каталог")
    now = time.time()
    buckets = (
        ("до 1 дня", 1 * 86400),
        ("1–7 дней", 7 * 86400),
        ("7–30 дней", 30 * 86400),
        ("30–90 дней", 90 * 86400),
        ("90–365 дней", 365 * 86400),
        ("старше года", float("inf")),
    )
    counts: Counter[str] = Counter()
    unreadable = 0
    for path in _walk_files(root):
        try:
            modified = path.lstat().st_mtime
        except OSError:
            unreadable += 1
            continue
        age = max(0.0, now - modified)
        for label, upper_bound in buckets:
            if age <= upper_bound:
                counts[label] += 1
                break
    print(f"Файлы и каталоги в {root}")
    for label, _upper in buckets:
        print(f"{label:16} {counts[label]:>8,}")
    if unreadable:
        print(f"Недоступно: {unreadable}")
