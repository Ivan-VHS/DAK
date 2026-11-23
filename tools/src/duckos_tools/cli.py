from __future__ import annotations

import argparse
import sys

from . import __version__
from . import filesystem, system


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="duckos",
        description="DuckOS — компактные пользовательские системные инструменты.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    pulse = commands.add_parser("sysmon-pulse", help="CPU, RAM, swap и скорость прерываний")
    pulse.add_argument("--interval", type=float, default=1.0)
    pulse.add_argument("--once", action="store_true")

    descriptors = commands.add_parser("fd-watch", help="отслеживать файловые дескрипторы PID")
    descriptors.add_argument("pid", type=int)
    descriptors.add_argument("--kind", choices=("all", "file", "socket", "pipe"), default="all")
    descriptors.add_argument("--interval", type=float, default=1.0)

    watcher = commands.add_parser("inotify-exec", help="выполнять команду при событиях каталога")
    watcher.add_argument("directory")
    watcher.add_argument("--pattern", default="*")
    watcher.add_argument("exec_command", nargs=argparse.REMAINDER)

    environment = commands.add_parser("proc-env-dump", help="показать cmdline и environment с маскированием")
    environment.add_argument("pid", type=int)

    commands.add_parser("mount-audit", help="проверить noexec, nosuid и nodev")
    scores = commands.add_parser("oom-score-map", help="показать oom_score активных процессов")
    scores.add_argument("--limit", type=int, default=30)
    commands.add_parser("irq-balance-check", help="сводка прерываний по CPU")

    jitter = commands.add_parser("clock-jitter", help="измерить отклонение системного таймера")
    jitter.add_argument("--samples", type=int, default=1000)
    jitter.add_argument("--period-ms", type=float, default=1.0)

    commands.add_parser("entropy-gauge", help="показать entropy_avail Linux")
    snapshot = commands.add_parser("sysinfo-snapshot", help="создать компактный JSON-снимок хоста")
    snapshot.add_argument("--output", help="путь для JSON-файла; без параметра выводится stdout")
    commands.add_parser("page-size-probe", help="показать размер страницы и hugepages")

    mapping = commands.add_parser("mmap-bench", help="сравнить последовательный и случайный доступ через mmap")
    mapping.add_argument("file")
    mapping.add_argument("--size-mib", type=int, default=64)

    comparison = commands.add_parser("dir-tree-diff", help="сравнить два дерева по SHA-256 и метаданным")
    comparison.add_argument("left")
    comparison.add_argument("right")
    comparison.add_argument("--json", action="store_true", dest="as_json")

    hotspots = commands.add_parser("disk-hotspots", help="найти самые объёмные каталоги и файлы")
    hotspots.add_argument("directory")
    hotspots.add_argument("--limit", type=int, default=20)

    atomic = commands.add_parser("atomic-write", help="атомарно записать текст в файл")
    atomic.add_argument("file")
    atomic.add_argument("text")

    links = commands.add_parser("symlink-loop-find", help="найти битые ссылки и циклы symlink")
    links.add_argument("directory")

    ages = commands.add_parser("file-age-hist", help="гистограмма возраста файлов по mtime")
    ages.add_argument("directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "sysmon-pulse":
            system.sysmon_pulse(args.interval, args.once)
        elif args.command == "fd-watch":
            system.fd_watch(args.pid, args.kind, args.interval)
        elif args.command == "inotify-exec":
            command = list(args.exec_command)
            if command and command[0] == "--":
                command.pop(0)
            system.inotify_exec(args.directory, command, args.pattern)
        elif args.command == "proc-env-dump":
            system.proc_env_dump(args.pid)
        elif args.command == "mount-audit":
            system.mount_audit()
        elif args.command == "oom-score-map":
            system.oom_score_map(args.limit)
        elif args.command == "irq-balance-check":
            system.irq_balance_check()
        elif args.command == "clock-jitter":
            system.clock_jitter(args.samples, args.period_ms)
        elif args.command == "entropy-gauge":
            system.entropy_gauge()
        elif args.command == "sysinfo-snapshot":
            system.sysinfo_snapshot(args.output)
        elif args.command == "page-size-probe":
            system.page_size_probe()
        elif args.command == "mmap-bench":
            filesystem.mmap_bench(args.file, args.size_mib)
        elif args.command == "dir-tree-diff":
            filesystem.dir_tree_diff(args.left, args.right, args.as_json)
        elif args.command == "disk-hotspots":
            filesystem.disk_hotspots(args.directory, args.limit)
        elif args.command == "atomic-write":
            filesystem.atomic_write(args.file, args.text)
        elif args.command == "symlink-loop-find":
            filesystem.symlink_loop_find(args.directory)
        elif args.command == "file-age-hist":
            filesystem.file_age_hist(args.directory)
        return 0
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError, ValueError) as error:
        print(f"duckos: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
