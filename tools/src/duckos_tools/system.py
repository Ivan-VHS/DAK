from __future__ import annotations

import ctypes
import errno
import fnmatch
import json
import os
import re
import selectors
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SECRET_NAME = re.compile(
    r"(?:PASS(?:WORD|WD)?|TOKEN|SECRET|API[_-]?KEY|PRIVATE[_-]?KEY|CREDENTIAL|AUTH)",
    re.IGNORECASE,
)


def _proc_file(name: str) -> str:
    path = Path("/proc") / name
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        raise RuntimeError(f"не удалось прочитать {path}: {error}") from error


def _cpu_ticks() -> tuple[int, int]:
    first = _proc_file("stat").splitlines()[0].split()
    if not first or first[0] != "cpu":
        raise RuntimeError("/proc/stat не содержит общей строки cpu")
    values = [int(value) for value in first[1:]]
    total = sum(values)
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return total, idle


def _memory_values() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in _proc_file("meminfo").splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        match = re.search(r"\d+", raw)
        if match:
            values[key] = int(match.group()) * 1024
    return values


def _interrupt_total() -> int:
    for line in _proc_file("stat").splitlines():
        if line.startswith("intr "):
            fields = line.split()
            return int(fields[1])
    raise RuntimeError("/proc/stat не содержит счётчик intr")


def _format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if amount < 1024 or unit == "TiB":
            return f"{amount:,.1f} {unit}"
        amount /= 1024
    return f"{amount:,.1f} TiB"


def _paint(value: str, level: float, warning: float = 70.0, danger: float = 90.0) -> str:
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return value
    color = "32" if level < warning else "33" if level < danger else "31"
    return f"\033[{color}m{value}\033[0m"


def sysmon_pulse(interval: float = 1.0, once: bool = False) -> None:
    if interval <= 0:
        raise ValueError("интервал должен быть больше нуля")
    previous_cpu = _cpu_ticks()
    previous_interrupts = _interrupt_total()
    while True:
        time.sleep(interval)
        current_cpu = _cpu_ticks()
        current_interrupts = _interrupt_total()
        total_delta = current_cpu[0] - previous_cpu[0]
        idle_delta = current_cpu[1] - previous_cpu[1]
        cpu = 0.0 if total_delta <= 0 else 100.0 * (total_delta - idle_delta) / total_delta

        memory = _memory_values()
        total_memory = memory.get("MemTotal", 0)
        available = memory.get("MemAvailable", memory.get("MemFree", 0))
        used_memory = max(0, total_memory - available)
        total_swap = memory.get("SwapTotal", 0)
        free_swap = memory.get("SwapFree", 0)
        used_swap = max(0, total_swap - free_swap)
        irq_rate = max(0, current_interrupts - previous_interrupts) / interval

        ram_percent = 0 if not total_memory else 100 * used_memory / total_memory
        swap_percent = 0 if not total_swap else 100 * used_swap / total_swap
        print(
            f"CPU {_paint(f'{cpu:5.1f}%', cpu)}  "
            f"RAM {_paint(f'{_format_bytes(used_memory)} / {_format_bytes(total_memory)}', ram_percent)}  "
            f"SWAP {_paint(f'{_format_bytes(used_swap)} / {_format_bytes(total_swap)}', swap_percent)}  "
            f"IRQ {irq_rate:,.0f}/s"
        )
        previous_cpu = current_cpu
        previous_interrupts = current_interrupts
        if once:
            return


def fd_watch(pid: int, kind: str = "all", interval: float = 1.0) -> None:
    if pid <= 0:
        raise ValueError("PID должен быть положительным")
    if interval <= 0:
        raise ValueError("интервал должен быть больше нуля")
    fd_dir = Path("/proc") / str(pid) / "fd"
    if not fd_dir.is_dir():
        raise RuntimeError(f"процесс {pid} не найден или недоступен")

    previous: dict[str, str] = {}
    print(f"Наблюдение за {fd_dir}; Ctrl+C для остановки")
    while True:
        current: dict[str, str] = {}
        try:
            entries = list(fd_dir.iterdir())
        except OSError as error:
            raise RuntimeError(f"процесс завершился или FD недоступны: {error}") from error
        for entry in entries:
            try:
                target = os.readlink(entry)
            except OSError:
                continue
            category = (
                "socket" if target.startswith("socket:[")
                else "pipe" if target.startswith("pipe:[")
                else "file"
            )
            if kind == "all" or category == kind:
                current[entry.name] = f"{category:6} {target}"
        for descriptor in sorted(current.keys() - previous.keys(), key=int):
            print(f"+ fd {descriptor}: {current[descriptor]}")
        for descriptor in sorted(previous.keys() - current.keys(), key=int):
            print(f"- fd {descriptor}: {previous[descriptor]}")
        previous = current
        time.sleep(interval)


def _redact_arguments(arguments: list[str]) -> list[str]:
    result: list[str] = []
    hide_next = False
    for argument in arguments:
        if hide_next:
            result.append("[REDACTED]")
            hide_next = False
            continue
        if argument.startswith("-") and "=" in argument:
            name, _value = argument.split("=", 1)
            if _SECRET_NAME.search(name):
                result.append(f"{name}=[REDACTED]")
                continue
        if argument.startswith("-") and _SECRET_NAME.search(argument):
            result.append(argument)
            hide_next = True
        else:
            result.append(argument)
    return result


def proc_env_dump(pid: int) -> None:
    if pid <= 0:
        raise ValueError("PID должен быть положительным")
    root = Path("/proc") / str(pid)
    try:
        raw_cmdline = (root / "cmdline").read_bytes()
        raw_environment = (root / "environ").read_bytes()
    except OSError as error:
        raise RuntimeError(f"процесс {pid} недоступен: {error}") from error

    arguments = [part.decode("utf-8", "replace") for part in raw_cmdline.split(b"\0") if part]
    environment: dict[str, str] = {}
    for entry in raw_environment.split(b"\0"):
        if not entry or b"=" not in entry:
            continue
        key_raw, value_raw = entry.split(b"=", 1)
        key = key_raw.decode("utf-8", "replace")
        value = value_raw.decode("utf-8", "replace")
        environment[key] = "[REDACTED]" if _SECRET_NAME.search(key) else value

    payload = {
        "pid": pid,
        "cmdline": _redact_arguments(arguments),
        "environment": dict(sorted(environment.items())),
        "redaction": "heuristic; review before sharing",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def mount_audit() -> None:
    lines = _proc_file("self/mountinfo").splitlines()
    print(f"{'ТОЧКА МОНТИРОВАНИЯ':44} {'FS':12} {'NOEXEC':8} {'NOSUID':8} {'NODEV':8}")
    findings = 0
    for line in lines:
        fields = line.split()
        if len(fields) < 10 or "-" not in fields:
            continue
        separator = fields.index("-")
        mount_point = fields[4].replace(r"\040", " ")
        options = set(fields[5].split(","))
        if separator + 3 < len(fields):
            options.update(fields[separator + 3].split(","))
        fs_type = fields[separator + 1]
        flags = [flag in options for flag in ("noexec", "nosuid", "nodev")]
        findings += 1
        print(
            f"{mount_point[:44]:44} {fs_type[:12]:12} "
            + " ".join(f"{'yes' if flag else 'no':8}" for flag in flags)
        )
    if not findings:
        print("Точки монтирования не найдены.")


def oom_score_map(limit: int = 30) -> None:
    if limit < 1:
        raise ValueError("limit должен быть не меньше 1")
    rows: list[tuple[int, int, int, str]] = []
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            score = int((process / "oom_score").read_text().strip())
            adjustment = int((process / "oom_score_adj").read_text().strip())
            status = (process / "comm").read_text(encoding="utf-8", errors="replace").strip()
        except (OSError, ValueError):
            continue
        rows.append((score, adjustment, int(process.name), status))
    print(f"{'PID':>8} {'SCORE':>7} {'ADJ':>6}  PROCESS")
    for score, adjustment, pid, name in sorted(rows, reverse=True)[:limit]:
        print(f"{pid:8d} {score:7d} {adjustment:6d}  {name}")


def irq_balance_check() -> None:
    lines = _proc_file("interrupts").splitlines()
    if not lines:
        raise RuntimeError("/proc/interrupts пуст")
    cpu_columns = re.findall(r"CPU\d+", lines[0])
    totals = [0] * len(cpu_columns)
    irq_rows = 0
    for line in lines[1:]:
        if not re.match(r"^\s*\d+:", line):
            continue
        fields = line.split()
        counts: list[int] = []
        for value in fields[1:1 + len(cpu_columns)]:
            try:
                counts.append(int(value))
            except ValueError:
                break
        if len(counts) != len(cpu_columns):
            continue
        totals = [old + new for old, new in zip(totals, counts)]
        irq_rows += 1
    total = sum(totals)
    print(f"Строк IRQ: {irq_rows}; всего зарегистрировано: {total:,}")
    if not totals:
        print("Счётчики CPU не распознаны.")
        return
    for name, count in zip(cpu_columns, totals):
        share = 0 if not total else 100 * count / total
        print(f"{name:>6}: {count:>14,}  ({share:5.1f}%)")


def clock_jitter(samples: int = 1000, period_ms: float = 1.0) -> None:
    if samples < 10:
        raise ValueError("для полезной оценки нужно не менее 10 samples")
    if period_ms <= 0:
        raise ValueError("period-ms должен быть больше нуля")
    period = period_ms / 1000.0
    deviations: list[float] = []
    previous = time.monotonic()
    for _ in range(samples):
        time.sleep(period)
        current = time.monotonic()
        deviations.append(max(0.0, current - previous - period) * 1000.0)
        previous = current
    ordered = sorted(deviations)

    def percentile(value: float) -> float:
        index = min(len(ordered) - 1, round((len(ordered) - 1) * value))
        return ordered[index]

    print(f"Период: {period_ms:g} ms; samples: {samples}")
    print(f"Jitter: p50 {percentile(0.50):.3f} ms | p95 {percentile(0.95):.3f} ms | "
          f"p99 {percentile(0.99):.3f} ms | max {max(ordered):.3f} ms")


def entropy_gauge() -> None:
    try:
        available = int(Path("/proc/sys/kernel/random/entropy_avail").read_text().strip())
    except (OSError, ValueError) as error:
        raise RuntimeError(f"источник entropy_avail недоступен: {error}") from error
    print(f"Доступная оценка энтропии ядра: {available} bits")
    print("Это моментальный показатель пула, а не доказательство криптографической стойкости приложения.")


def page_size_probe() -> None:
    page_size = os.sysconf("SC_PAGE_SIZE")
    print(f"Размер страницы: {page_size} bytes")
    try:
        memory = _memory_values()
    except RuntimeError:
        memory = {}
    for key in ("HugePages_Total", "HugePages_Free", "Hugepagesize"):
        if key in memory:
            value = memory[key]
            if key == "Hugepagesize":
                print(f"{key}: {value // 1024} KiB")
            else:
                print(f"{key}: {value}")
    if not any(key.startswith("HugePages_") for key in memory):
        print("HugePages: сведения отсутствуют в /proc/meminfo")


def sysinfo_snapshot(output: str | None = None) -> None:
    memory: dict[str, int] = {}
    try:
        memory = _memory_values()
    except RuntimeError:
        pass
    snapshot: dict[str, Any] = {
        "schema": "duckos.sysinfo.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "host": {
            "hostname": os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME", "unknown"),
            "platform": sys.platform,
            "release": os.uname().release if hasattr(os, "uname") else "unknown",
            "machine": os.uname().machine if hasattr(os, "uname") else "unknown",
        },
        "cpu": {"logical_count": os.cpu_count()},
        "memory": {
            "total_bytes": memory.get("MemTotal"),
            "available_bytes": memory.get("MemAvailable"),
            "swap_total_bytes": memory.get("SwapTotal"),
            "swap_free_bytes": memory.get("SwapFree"),
        },
        "page_size": os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else None,
    }
    rendered = json.dumps(snapshot, ensure_ascii=False, indent=2)
    if output:
        destination = Path(output)
        destination.write_text(rendered + "\n", encoding="utf-8")
        print(f"Snapshot сохранён: {destination}")
    else:
        print(rendered)


def inotify_exec(directory: str, command: list[str], pattern: str = "*") -> None:
    if not sys.platform.startswith("linux"):
        raise RuntimeError("inotify-exec поддерживается только на Linux")
    if not command:
        raise ValueError("после -- укажите исполняемую команду")
    watch_path = Path(directory).resolve(strict=True)
    if not watch_path.is_dir():
        raise ValueError("нужно указать существующий каталог")

    libc = ctypes.CDLL(None, use_errno=True)
    init = libc.inotify_init1
    init.argtypes = [ctypes.c_int]
    init.restype = ctypes.c_int
    add_watch = libc.inotify_add_watch
    add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    add_watch.restype = ctypes.c_int

    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    non_blocking = getattr(os, "O_NONBLOCK", 0)
    fd = init(non_blocking | close_on_exec)
    if fd < 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))

    mask = 0x00000100 | 0x00000200 | 0x00000002 | 0x00000008 | 0x00000040 | 0x00000080 | 0x00000004
    watch = add_watch(fd, os.fsencode(watch_path), mask)
    if watch < 0:
        code = ctypes.get_errno()
        os.close(fd)
        raise OSError(code, os.strerror(code))

    event_names = (
        (0x00000100, "created"),
        (0x00000200, "deleted"),
        (0x00000002, "modified"),
        (0x00000008, "written"),
        (0x00000040, "moved-from"),
        (0x00000080, "moved-to"),
        (0x00000004, "metadata"),
    )
    print(f"inotify: {watch_path} (pattern={pattern}); Ctrl+C для остановки")
    selector = selectors.DefaultSelector()
    selector.register(fd, selectors.EVENT_READ)
    try:
        while True:
            for _key, _events in selector.select(timeout=1.0):
                try:
                    data = os.read(fd, 65536)
                except BlockingIOError:
                    continue
                offset = 0
                while offset + 16 <= len(data):
                    watch_descriptor, event_mask, _cookie, name_length = struct.unpack_from("iIII", data, offset)
                    offset += 16
                    raw_name = data[offset:offset + name_length]
                    offset += name_length
                    name = raw_name.split(b"\0", 1)[0].decode("utf-8", "replace")
                    if watch_descriptor != watch or not name:
                        continue
                    target = watch_path / name
                    if not fnmatch.fnmatch(name, pattern):
                        continue
                    for bit, event_name in event_names:
                        if event_mask & bit:
                            print(f"{event_name:10} {target}")
                            argv = [
                                part.replace("{path}", str(target)).replace("{event}", event_name)
                                for part in command
                            ]
                            if not any("{path}" in part or "{event}" in part for part in command):
                                argv.append(str(target))
                            try:
                                completed = subprocess.run(argv, check=False)
                                if completed.returncode:
                                    print(f"Команда завершилась с кодом {completed.returncode}")
                            except OSError as error:
                                print(f"Не удалось запустить команду: {error}", file=sys.stderr)
                            break
    finally:
        selector.close()
        os.close(fd)
