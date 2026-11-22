# Маршрутизация каталога возможностей

Большой список идей разделяется по ответственности. Это предотвращает ситуацию, когда похожие утилиты начинают независимо реализовывать одно и то же в четырёх продуктах.

| Область идей | Владелец | Правило |
|---|---|---|
| Ядро оболочки, окна, workspaces, dock, поиск, уведомления, настройки | DuckOS | пользовательская среда и её системные API |
| Процессы, файловые системы, mount points, IPC, snapshots | DuckOS | host-level utilities без изменения состояния по умолчанию |
| CPU, NUMA, RAM pressure, page faults, IRQ, таймеры и processor benchmarks | Pytyliki | измерения и процессорная диагностика принадлежат одному ядру |
| Lexer, parser, AST, CFG, SSA, IR, compiler passes, language servers | Reaper | языковые и code-intelligence функции не дублируются в DuckOS |
| USB, PCI/PCIe, NVMe, PnP, driver metadata, hardware inventory | OPlague | read-only инвентаризация, без установки или прошивки |
| WAV, PCM, MIDI, DSP, sample slicing, synth, audio analysis | VentuSample | только локальный аудио/DSP pipeline |
| Repo automation, CI, release metadata, test reports | DuckOS tooling / отдельные адаптеры | не смешивать с kernel и runtime-путями |
| Network diagnostics, cryptographic inspection, local security checks | DuckOS | read-only аудит; активные сетевые действия — отдельное подтверждение |
| UI primitives и оконная модель | DuckOS | общие компоненты принадлежат оболочке; специализированная IDE UI остаётся в Reaper |
| Text, math, generic algorithms, simulation tools | Reaper или отдельные приложения | не включать в системный daemon без реального системного сценария |

## Примеры из предложенного каталога

- sysmon-pulse, fd-watch, dir-tree-diff, inotify-exec, mount-audit, proc-env-dump, disk-hotspots, atomic-write, sysinfo-snapshot → DuckOS.
- mmap-bench, swap-pressure, cpu-affinity-pin, irq-balance-check, page-size-probe, madvise-bench, NUMA- и memory-нагрузки → Pytyliki.
- lexer-gen, pratt-expr, ast-diff, cfg-builder, ssa-pass, const-fold, dce-pass, ir-verifier, language tooling → Reaper.
- usb-tree-dump, pci-bar-info, nvme-smart-watch, driver package audit, hardware IDs → OPlague; только в пределах его read-only контракта.
- wav-header-parse, pcm-peak-rms, biquad-eq-calc, midi-step-seq, time-stretch, compressor, sample-pack-index, DSP graph → VentuSample.
- window-snap-zones, command-palette, dock-layout, accessibility checks, theme tokens → DuckOS Shell.

## Статусы

- **Implemented** — есть код и тесты в этой поставке.
- **Preview** — есть интерактивное представление, но backend или интеграция ещё отсутствуют.
- **Planned** — зафиксировано в roadmap или матрице маршрутизации.
- **Out of scope** — нарушает границы проекта или небезопасно для системного default.

Ни один пункт каталога не объявляется реализованным только из-за наличия названия в JSON или документации.
