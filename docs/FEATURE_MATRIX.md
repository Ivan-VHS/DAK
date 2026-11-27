# Матрица готовности

Статус отражает файлы этого релизного кандидата, а не идеи в каталоге.

| Подсистема | Статус | Что доступно сейчас |
|---|---|---|
| Desktop shell | Implemented preview | окна, dock, поиск, настройки, темы, уведомления |
| Responsive layout | Implemented | широкие и узкие экраны |
| Reduced motion | Implemented | системная настройка демо-интерфейса |
| Resource dashboard | Demo only | демонстрационные графики, явно маркированные |
| CLI package | Implemented | Python package и entry point |
| Cockos | Implemented, user space | PipeWire port discovery and explicit link connect/disconnect; requires pw-link |
| Kavun | Implemented, user space | main-stack, columns, grid and floating geometry planner; no surface control yet |
| Ka-bon | Implemented, user space | context-aware chord resolver and action allow-list; no evdev seat yet |
| Gloverty | Implemented, user space | dark/light/high-contrast palettes and contrast audit |
| Po | Implemented, user space | ranked registered-command search and confirmation gates; no shell execution |
| Illidia | Implemented, user space | atomic checksummed session snapshots with field allow-list |
| Unify | Implemented, user space | persisted profiles, in-process event bus and command registry; no IPC daemon |
| sysmon-pulse | Implemented, Linux | CPU delta, RAM, swap, interrupt rate |
| fd-watch | Implemented, Linux | FD по PID с типом file/socket/pipe |
| mmap-bench | Implemented | последовательный/случайный доступ, page fault delta |
| dir-tree-diff | Implemented | SHA-256, права, размер, время изменения |
| inotify-exec | Implemented, Linux | прямое наблюдение каталога, glob и argv без shell |
| proc-env-dump | Implemented, Linux | cmdline и environment с маскированием секретов |
| disk-hotspots | Implemented | размер логический/занятый, дедупликация hard links |
| mount-audit | Implemented, Linux | проверка noexec/nosuid/nodev |
| oom-score-map | Implemented, Linux | oom_score и oom_score_adj |
| irq-balance-check | Implemented, Linux | распределение счётчиков по CPU |
| clock-jitter | Implemented | измерение отклонений sleep/monotonic |
| entropy-gauge | Implemented, Linux | entropy_avail из procfs |
| sysinfo-snapshot | Implemented | ограниченный JSON snapshot |
| atomic-write | Implemented | temp + fsync + replace + directory fsync |
| symlink-loop-find | Implemented | broken links и циклы |
| file-age-hist | Implemented | возраст файлов по mtime |
| page-size-probe | Implemented | системная страница и hugepages |
| Kernel / bootloader | Early bring-up | Limine handoff, serial log and framebuffer; no scheduler or userspace |
| Wayland compositor | Preview bring-up | wlroots backend, output rendering and xdg-shell globals; no seat/focus policy or complete desktop shell |
| Driver installation | Out of scope | OPlague остаётся read-only |
| AI agent with host access | Not implemented | нужен отдельный permission broker и audit log |
| Native GPU telemetry | Not implemented | браузерный dashboard показывает только demo |
